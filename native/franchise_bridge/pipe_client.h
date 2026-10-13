#pragma once
#include <windows.h>
#include "contract_response.h"
#include <chrono>
#include <future>
#include <stdexcept>
#include <string>
#include <thread>

namespace franchise {
enum class ServiceMode { OfflineFixture, VertexRuntime };
// Quote one Windows command-line argument, including embedded quotes/backslashes.
inline std::wstring quote(const std::wstring& value) {
    std::wstring result = L"\"";
    size_t slashes = 0;
    for (wchar_t c : value) {
        if (c == L'\\') { ++slashes; continue; }
        result.append(c == L'"' ? slashes * 2 + 1 : slashes, L'\\');
        slashes = 0;
        result += c;
    }
    result.append(slashes * 2, L'\\');
    return result + L"\"";
}

class PipeClient {
    HANDLE input_ = nullptr, output_ = nullptr, process_ = nullptr, job_ = nullptr;
    std::future<std::string> pending_;
    std::string request_id_;
    nlohmann::json request_;
    void close() noexcept {
        if (input_) { CloseHandle(input_); input_ = nullptr; }
        if (process_) {
            if (WaitForSingleObject(process_, 1000) == WAIT_TIMEOUT) {
                TerminateProcess(process_, 1);
                WaitForSingleObject(process_, 1000);
            }
            CloseHandle(process_); process_ = nullptr;
        }
        if (job_) { CloseHandle(job_); job_ = nullptr; }
        if (output_) { CloseHandle(output_); output_ = nullptr; }
    }
public:
    PipeClient(const std::wstring& python, const std::wstring& database, ServiceMode mode) {
        if (mode != ServiceMode::OfflineFixture && mode != ServiceMode::VertexRuntime)
            throw std::runtime_error("Explicit supported service mode required");
        SECURITY_ATTRIBUTES attributes{sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE};
        HANDLE child_input = nullptr, child_output = nullptr;
        if (!CreatePipe(&child_input, &input_, &attributes, 0) ||
            !CreatePipe(&output_, &child_output, &attributes, 0)) {
            if (child_input) CloseHandle(child_input);
            if (child_output) CloseHandle(child_output);
            close(); throw std::runtime_error("Pipe creation failed");
        }
        if (!SetHandleInformation(input_, HANDLE_FLAG_INHERIT, 0) ||
            !SetHandleInformation(output_, HANDLE_FLAG_INHERIT, 0)) {
            CloseHandle(child_input); CloseHandle(child_output); close();
            throw std::runtime_error("Pipe inheritance configuration failed");
        }
        job_ = CreateJobObjectW(nullptr, nullptr);
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        SIZE_T attribute_size = 0;
        InitializeProcThreadAttributeList(nullptr, 1, 0, &attribute_size);
        auto attributes_list = static_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(
            HeapAlloc(GetProcessHeap(), 0, attribute_size));
        bool initialized = attributes_list && InitializeProcThreadAttributeList(attributes_list, 1, 0, &attribute_size);
        bool configured = initialized && job_ &&
            SetInformationJobObject(job_, JobObjectExtendedLimitInformation, &limits, sizeof(limits)) &&
            UpdateProcThreadAttribute(attributes_list, 0, PROC_THREAD_ATTRIBUTE_JOB_LIST,
                                      &job_, sizeof(job_), nullptr, nullptr);
        if (!configured) {
            if (initialized) DeleteProcThreadAttributeList(attributes_list);
            if (attributes_list) HeapFree(GetProcessHeap(), 0, attributes_list);
            CloseHandle(child_input); CloseHandle(child_output); close();
            throw std::runtime_error("Sidecar ownership setup failed");
        }
        STARTUPINFOEXW startup{}; startup.StartupInfo.cb = sizeof(startup);
        startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
        startup.StartupInfo.hStdInput = child_input; startup.StartupInfo.hStdOutput = child_output;
        startup.StartupInfo.hStdError = GetStdHandle(STD_ERROR_HANDLE);
        startup.lpAttributeList = attributes_list;
        PROCESS_INFORMATION info{};
        // Mode is fixed before launch; runtime never falls back to a fixture.
        std::wstring command = quote(python) + L" -m franchise.sidecar --database " + quote(database) +
            (mode == ServiceMode::OfflineFixture ? L" --provider offline-fixture" :
             L" --provider vertex --impersonate-runtime");
        BOOL started = CreateProcessW(python.c_str(), command.data(), nullptr, nullptr,
                                      TRUE, CREATE_NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT,
                                      nullptr, nullptr, &startup.StartupInfo, &info);
        DeleteProcThreadAttributeList(attributes_list);
        HeapFree(GetProcessHeap(), 0, attributes_list);
        CloseHandle(child_input); CloseHandle(child_output);
        if (!started) { close(); throw std::runtime_error("Sidecar launch failed"); }
        process_ = info.hProcess; CloseHandle(info.hThread);
    }
    PipeClient(const PipeClient&) = delete;
    PipeClient& operator=(const PipeClient&) = delete;
    ~PipeClient() {
        // Worker polling has a bounded deadline; never close its handles concurrently.
        if (pending_.valid()) pending_.wait();
        close();
    }
    DWORD process_id() const { return GetProcessId(process_); }
    void submit(std::string json) {
        if (!process_) throw std::runtime_error("Client is disconnected");
        if (pending_.valid()) throw std::runtime_error("Client request already pending");
        if (json.size() > 4095 || json.find_first_of("\r\n") != std::string::npos)
            throw std::runtime_error("Invalid client frame");
        auto request = parse_frame(json);
        if (!request.is_object() || !request.contains("request_id") || !request["request_id"].is_string())
            throw std::runtime_error("Request ID required");
        request_ = request;
        request_id_ = request["request_id"].get<std::string>();
        if (request_id_.empty()) throw std::runtime_error("Request ID required");
        pending_ = std::async(std::launch::async, [this, json = std::move(json)] {
            std::string frame = json + "\n", response;
            DWORD written = 0;
            if (!WriteFile(input_, frame.data(), static_cast<DWORD>(frame.size()), &written, nullptr) || written != frame.size())
                throw std::runtime_error("Sidecar write failed");
            auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
            while (std::chrono::steady_clock::now() < deadline) {
                DWORD available = 0;
                if (!PeekNamedPipe(output_, nullptr, 0, nullptr, &available, nullptr))
                    throw std::runtime_error("Sidecar disconnected");
                if (!available) { std::this_thread::sleep_for(std::chrono::milliseconds(2)); continue; }
                char c; DWORD count = 0;
                if (!ReadFile(output_, &c, 1, &count, nullptr) || count != 1)
                    throw std::runtime_error("Sidecar read failed");
                if (c == '\n') return response;
                if (c == '\r') continue;  // Windows text-mode CRLF framing.
                if (response.size() >= 65536) throw std::runtime_error("Sidecar response too large");
                response += c;
            }
            throw std::runtime_error("Sidecar response timeout");
        });
    }
    bool ready() {
        return pending_.valid() && pending_.wait_for(std::chrono::seconds(0)) == std::future_status::ready;
    }
    std::string take() {
        if (!ready()) throw std::runtime_error("Response not ready");
        try {
            auto response = pending_.get();
            validate_result(decode_response(response, request_id_), request_);
            return response;
        }
        catch (...) { close(); throw; }
    }
};
}
