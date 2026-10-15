#pragma once
#include "protocol.h"
#include <atomic>
#include <cerrno>
#include <chrono>
#include <climits>
#include <csignal>
#include <fcntl.h>
#include <future>
#include <poll.h>
#include <stdexcept>
#include <string>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <thread>
#include <unistd.h>

extern char **environ;
namespace engine_sidecar {

// Linux owns a process group for normal teardown and applies a parent-death
// signal to the direct peer. Arbitrary descendants need cooperative cleanup;
// this is not a cgroup sandbox or a Windows job-object equivalent.
class PipeClient {
    int input_=-1, output_=-1;
    pid_t process_=-1;
    std::future<std::string> pending_;
    std::string request_id_;
    std::atomic<bool> stopping_{false};
    using Clock=std::chrono::steady_clock;
    static void close_fd(int& fd) noexcept { if(fd>=0) { ::close(fd);fd=-1; } }
    static void private_fd(int& fd) {
        if(fd>=3) return;
        int copy=fcntl(fd,F_DUPFD_CLOEXEC,3);
        if(copy<0) throw std::runtime_error("Sidecar descriptor setup failed");
        close_fd(fd);fd=copy;
    }
    [[noreturn]] static void child_failure(int fd) noexcept {
        int error=errno;
        // One atomic, bounded startup-status write. No allocation/CRT cleanup
        // between fork and exec in the multithreaded native application.
        ssize_t result;
        do { result=::write(fd,&error,sizeof(error)); } while(result<0 && errno==EINTR);
        _exit(127);
    }
    void wait_fd(int fd,short events,Clock::time_point deadline) const {
        while(!stopping_.load()) {
            if(Clock::now()>=deadline) throw std::runtime_error("Sidecar request timeout");
            pollfd item{fd,events,0};
            int result=::poll(&item,1,20);
            if(result<0 && errno==EINTR) continue;
            if(result<0 || (result && (item.revents&POLLNVAL)))
                throw std::runtime_error("Sidecar poll failed");
            if(result && (item.revents&(events|POLLHUP|POLLERR))) return;
        }
        throw std::runtime_error("Sidecar request cancelled");
    }
    void close() noexcept {
        stopping_.store(true);
        // Workers only use nonblocking I/O and short polls. Keep their fds alive
        // until they stop; closing/reusing one underneath a worker is unsafe.
        if(pending_.valid()) pending_.wait();
        close_fd(input_);
        if(process_>0) {
            bool owned=true;
            auto deadline=Clock::now()+std::chrono::milliseconds(500);
            while(Clock::now()<deadline) {
                siginfo_t info{};
                if(waitid(P_PID,process_,&info,WEXITED|WNOHANG|WNOWAIT)<0) {
                    if(errno==ECHILD) owned=false;
                    if(errno==EINTR) continue;
                    break;
                }
                if(info.si_pid) break;
                std::this_thread::sleep_for(std::chrono::milliseconds(2));
            }
            if(owned) {
                // Keep the group leader unreaped until signalling its group:
                // its PID cannot be recycled into an unrelated process group.
                bool group=::kill(-process_,SIGTERM)==0;
                ::kill(process_,SIGTERM);
                if(group) std::this_thread::sleep_for(std::chrono::milliseconds(100));
                ::kill(-process_,SIGKILL);::kill(process_,SIGKILL);
                deadline=Clock::now()+std::chrono::seconds(1);
                while(Clock::now()<deadline) {
                    int status=0;
                    pid_t result=waitpid(process_,&status,WNOHANG);
                    if(result==process_ || (result<0 && errno==ECHILD)) break;
                    if(result<0 && errno!=EINTR) break;
                    std::this_thread::sleep_for(std::chrono::milliseconds(2));
                }
            }
            process_=-1;
        }
        close_fd(output_);
    }
public:
    PipeClient(const std::string& executable,const std::vector<std::string>& arguments) {
        if(executable.empty() || executable[0]!='/' || executable.find('\0')!=std::string::npos)
            throw std::invalid_argument("Explicit absolute executable required");
        for(const auto& value:arguments)
            if(value.find('\0')!=std::string::npos) throw std::invalid_argument("NUL in launch argument");
        struct sigaction reaper{};
        if(sigaction(SIGCHLD,nullptr,&reaper)<0 || reaper.sa_handler!=SIG_DFL || (reaper.sa_flags&SA_NOCLDWAIT))
            throw std::invalid_argument("Sidecar requires ownership of child reaping");
        // Materialize argv before fork; execve receives exact arguments, never
        // a shell command. The peer inherits the parent's current environment.
        std::vector<char*> argv;argv.reserve(arguments.size()+2);
        argv.push_back(const_cast<char*>(executable.c_str()));
        for(const auto& value:arguments) argv.push_back(const_cast<char*>(value.c_str()));
        argv.push_back(nullptr);
        int input[2]={-1,-1}, output[2]={-1,-1}, startup[2]={-1,-1}, error=-1;
        try {
            // Socket sends use MSG_NOSIGNAL: a dead peer must never deliver
            // SIGPIPE to the game, and the game-wide signal disposition stays intact.
            if(socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,input) ||
               socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,output) || pipe2(startup,O_CLOEXEC))
                throw std::runtime_error("Sidecar channel creation failed");
            for(int* fd:{&input[0],&input[1],&output[0],&output[1],&startup[0],&startup[1]}) private_fd(*fd);
            error=fcntl(STDERR_FILENO,F_DUPFD_CLOEXEC,3);
            if(error<0) error=::open("/dev/null",O_WRONLY|O_CLOEXEC);
            if(error<0) throw std::runtime_error("Sidecar stderr setup failed");
            private_fd(error);
            for(int fd:{input[0],output[0],startup[0]})
                if(fcntl(fd,F_SETFL,fcntl(fd,F_GETFL)|O_NONBLOCK)<0)
                    throw std::runtime_error("Sidecar nonblocking setup failed");
            rlimit limit{};
            if(getrlimit(RLIMIT_NOFILE,&limit)<0) throw std::runtime_error("Sidecar descriptor limit unavailable");
            unsigned long descriptor_limit=limit.rlim_cur>INT_MAX ? INT_MAX : limit.rlim_cur;
            const pid_t parent=getpid();
            process_=fork();
            if(process_<0) throw std::runtime_error("Sidecar fork failed");
            if(process_==0) {
                if(setpgid(0,0)<0 || syscall(SYS_prctl,PR_SET_PDEATHSIG,SIGKILL)<0 || getppid()!=parent)
                    child_failure(startup[1]);
                if(dup2(input[1],STDIN_FILENO)<0 || dup2(output[1],STDOUT_FILENO)<0 ||
                   dup2(error,STDERR_FILENO)<0 || dup2(startup[1],3)<0 || fcntl(3,F_SETFD,FD_CLOEXEC)<0)
                    child_failure(startup[1]);
#ifdef SYS_close_range
                if(syscall(SYS_close_range,4u,~0u,0u)<0)
#endif
                    for(unsigned long fd=4;fd<descriptor_limit;++fd) ::close(static_cast<int>(fd));
                execve(executable.c_str(),argv.data(),::environ);
                child_failure(3);
            }
            // Child also establishes this group before exec; this closes the
            // constructor-failure cleanup race before the child is scheduled.
            setpgid(process_,process_);
            close_fd(input[1]);close_fd(output[1]);close_fd(startup[1]);close_fd(error);
            input_=input[0];input[0]=-1;output_=output[0];output[0]=-1;
            auto deadline=Clock::now()+std::chrono::seconds(5);
            while(true) {
                wait_fd(startup[0],POLLIN,deadline);
                int launch_error=0;
                ssize_t count=::read(startup[0],&launch_error,sizeof(launch_error));
                if(count==0) break; // CLOEXEC status channel closed: exec succeeded.
                if(count<0 && (errno==EINTR || errno==EAGAIN)) continue;
                throw std::runtime_error("Sidecar exec failed");
            }
            close_fd(startup[0]);
        } catch(...) {
            for(int* fd:{&input[0],&input[1],&output[0],&output[1],&startup[0],&startup[1],&error}) close_fd(*fd);
            close();throw;
        }
    }
    PipeClient(const PipeClient&)=delete;
    PipeClient& operator=(const PipeClient&)=delete;
    ~PipeClient() { close(); }
    void abort() noexcept { close(); }
    pid_t process_id() const { return process_; }
    void submit(std::string json) {
        if(process_<=0 || stopping_.load()) throw std::runtime_error("Client is disconnected");
        if(pending_.valid()) throw std::runtime_error("Client request already pending");
        if(json.size()>4095 || json.find_first_of("\r\n")!=std::string::npos || json.find('\0')!=std::string::npos)
            throw std::runtime_error("Invalid client frame");
        auto request=parse_frame(json);
        if(!request.is_object() || !request.contains("request_id") || !request["request_id"].is_string())
            throw std::runtime_error("Request ID required");
        request_id_=request["request_id"].get<std::string>();
        if(request_id_.empty()) throw std::runtime_error("Request ID required");
        pending_=std::async(std::launch::async,[this,json=std::move(json)] {
            auto deadline=Clock::now()+std::chrono::seconds(5);
            std::string frame=json+"\n",response;
            size_t sent=0;
            while(sent<frame.size()) {
                wait_fd(input_,POLLOUT,deadline);
                ssize_t count=::send(input_,frame.data()+sent,frame.size()-sent,MSG_NOSIGNAL);
                if(count<0 && (errno==EINTR || errno==EAGAIN)) continue;
                if(count<=0) throw std::runtime_error("Sidecar write failed");
                sent+=static_cast<size_t>(count);
            }
            while(true) {
                wait_fd(output_,POLLIN,deadline);
                char buffer[4096];ssize_t count=::recv(output_,buffer,sizeof(buffer),0);
                if(count<0 && (errno==EINTR || errno==EAGAIN)) continue;
                if(count<=0) throw std::runtime_error("Sidecar disconnected");
                for(ssize_t i=0;i<count;++i) {
                    if(buffer[i]=='\n') {
                        if(i+1!=count) throw std::runtime_error("Unexpected extra response data");
                        return response;
                    }
                    if(buffer[i]=='\r') continue;
                    if(response.size()>=65536) throw std::runtime_error("Sidecar response too large");
                    response+=buffer[i];
                }
            }
        });
    }
    bool ready() { return pending_.valid() && pending_.wait_for(std::chrono::seconds(0))==std::future_status::ready; }
    std::string take() {
        if(!ready()) throw std::runtime_error("Response not ready");
        try { auto response=pending_.get();decode_response(response,request_id_);return response; }
        catch(...) { close();throw; }
    }
};
}
