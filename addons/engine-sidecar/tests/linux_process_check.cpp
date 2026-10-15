#include <engine_sidecar/pipe_client.h>
#include <fstream>
#include <iostream>
#include <sys/stat.h>

using engine_sidecar::PipeClient;
static void require(bool ok,const char* detail) { if(!ok) throw std::runtime_error(detail); }
static void wait_ready(PipeClient& client) {
    auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(7);
    while(!client.ready() && std::chrono::steady_clock::now()<deadline)
        std::this_thread::sleep_for(std::chrono::milliseconds(2));
    require(client.ready(),"Worker did not complete");
}
static bool running(pid_t pid) {
    std::ifstream input("/proc/"+std::to_string(pid)+"/stat");
    std::string line;std::getline(input,line);
    auto end=line.rfind(')');
    return end!=std::string::npos && end+2<line.size() && line[end+2]!='Z' && line[end+2]!='X';
}
static void require_reaped(pid_t pid) {
    int status=0;errno=0;
    require(waitpid(pid,&status,WNOHANG)==-1 && errno==ECHILD,"Owned peer was not reaped");
}
int main(int argc,char** argv) {
    if(argc!=3) return 1;
    try {
        std::string python=argv[1],peer=argv[2];
        // Only the test adopts orphaned descendants so it can reap every peer
        // used to prove process-group and abrupt-parent teardown.
        require(prctl(PR_SET_CHILD_SUBREAPER,1)==0,"Test subreaper unavailable");
        signal(SIGPIPE,SIG_DFL);
        const std::string request=R"({"protocol":1,"request_id":"linux-1","operation":"echo","payload":"native Linux"})";
        struct sigaction original_pipe{};sigaction(SIGPIPE,nullptr,&original_pipe);
        for(const std::string mode:{"echo","crlf"}) {
            pid_t pid;
            {
                PipeClient client(python,{peer,mode,"space arg","literal $() ;", "quote\"slash\\", ""});pid=client.process_id();
                client.submit(request);
                bool refused=false;try { client.submit(request); } catch(...) { refused=true; }
                require(refused,"Concurrent submit was accepted");
                wait_ready(client);
                auto response=engine_sidecar::decode_response(client.take(),"linux-1");
                require(response["result"]["echo"]=="native Linux","Echo payload changed");
                require(response["result"]["argv"]==nlohmann::json({"space arg","literal $() ;","quote\"slash\\",""}),"Launch argument changed");
                client.submit(request);wait_ready(client);client.take();
            }
            require_reaped(pid);
        }
        for(const std::string mode:{"mismatch","oversize","invalid","exit"}) {
            PipeClient client(python,{peer,mode});pid_t pid=client.process_id();
            client.submit(request);wait_ready(client);
            bool refused=false;try { client.take(); } catch(...) { refused=true; }
            require(refused,"Invalid peer response was accepted");
            require(client.process_id()<0,"Failed transport remained connected");require_reaped(pid);
            refused=false;try { client.submit(request); } catch(...) { refused=true; }
            require(refused,"Disconnected client was reused");
        }
        {
            PipeClient client(python,{peer,"stalled"});pid_t pid=client.process_id();
            client.submit(request);
            auto started=std::chrono::steady_clock::now();client.abort();
            require(std::chrono::steady_clock::now()-started<std::chrono::seconds(3),"Stalled shutdown exceeded bound");
            require_reaped(pid);
        }
        {
            PipeClient client(python,{peer,"stalled"});pid_t pid=client.process_id();
            client.submit(request);wait_ready(client);
            bool refused=false;try { client.take(); } catch(...) { refused=true; }
            require(refused,"Missing response did not time out");require_reaped(pid);
        }
        {
            int fd=open("/dev/null",O_RDONLY);struct stat info{};
            require(fd>=0 && fstat(fd,&info)==0,"Sentinel descriptor unavailable");
            PipeClient client(python,{peer,"inherited",std::to_string(fd),std::to_string(info.st_ino)});
            client.submit(request);wait_ready(client);
            auto response=engine_sidecar::decode_response(client.take(),"linux-1");
            ::close(fd);require(response["result"]["leaked"]==false,"Unrelated parent descriptor leaked");
        }
        pid_t descendant=0;
        {
            PipeClient client(python,{peer,"descendant"});client.submit(request);wait_ready(client);
            auto response=engine_sidecar::decode_response(client.take(),"linux-1");
            descendant=response["result"]["child_pid"].get<pid_t>();
            require(running(descendant),"Descendant never started");
        }
        auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(running(descendant) && std::chrono::steady_clock::now()<deadline)
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
        require(!running(descendant),"Descendant survived process-group teardown");
        int descendant_status=0;require(waitpid(descendant,&descendant_status,0)==descendant,"Descendant was not reaped");
        {
            int report[2];require(pipe(report)==0,"Parent-death test pipe failed");
            pid_t owner=fork();require(owner>=0,"Parent-death test fork failed");
            if(owner==0) {
                ::close(report[0]);
                try {
                    PipeClient client(python,{peer,"stalled"});pid_t child=client.process_id();
                    if(::write(report[1],&child,sizeof(child))!=sizeof(child)) _exit(2);
                    _exit(0); // Deliberately bypass all client destructors.
                } catch(...) { _exit(3); }
            }
            ::close(report[1]);pid_t orphan=0;
            require(::read(report[0],&orphan,sizeof(orphan))==sizeof(orphan),"Missing parent-death peer PID");
            ::close(report[0]);int status=0;
            require(waitpid(owner,&status,0)==owner && WIFEXITED(status) && WEXITSTATUS(status)==0,"Parent-death helper failed");
            auto killed_by=std::chrono::steady_clock::now()+std::chrono::seconds(2);
            while(running(orphan) && std::chrono::steady_clock::now()<killed_by)
                std::this_thread::sleep_for(std::chrono::milliseconds(2));
            require(!running(orphan),"Direct peer survived abrupt parent exit");
            require(waitpid(orphan,&status,0)==orphan,"Parent-death peer was not reaped");
        }
        bool refused=false;
        try { PipeClient client("python3",{peer,"echo"}); } catch(...) { refused=true; }
        require(refused,"Relative executable was accepted");
        refused=false;try { PipeClient client("/no/such/engine-sidecar-executable",{}); } catch(...) { refused=true; }
        require(refused,"Missing executable was accepted");
        struct sigaction after_pipe{};sigaction(SIGPIPE,nullptr,&after_pipe);
        require(after_pipe.sa_handler==original_pipe.sa_handler,"Host SIGPIPE handler changed");
        std::cout<<"Native Linux argv/framing/dead-peer/timeout/abort/inheritance/group cleanup/parent-death checks passed\n";
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 2; }
}
