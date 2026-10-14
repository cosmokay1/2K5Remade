#include "pipe_client.h"
#include <iostream>
#include <memory>
#include <cstdint>

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) return 1;
    try {
        SECURITY_ATTRIBUTES attributes{sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE};
        std::unique_ptr<void, decltype(&CloseHandle)> unrelated(
            CreateEventW(&attributes, TRUE, FALSE, nullptr), &CloseHandle);
        if (!unrelated) throw std::runtime_error("Cannot create inheritance sentinel");
        // Positive control: unrestricted inheritance must signal the same event.
        std::wstring command = franchise::quote(argv[1]) + L" --inheritance-control " +
            std::to_wstring(reinterpret_cast<uintptr_t>(unrelated.get()));
        STARTUPINFOW startup{}; startup.cb = sizeof(startup);
        PROCESS_INFORMATION control{};
        if (!CreateProcessW(argv[1], command.data(), nullptr, nullptr, TRUE,
                            CREATE_NO_WINDOW, nullptr, nullptr, &startup, &control))
            throw std::runtime_error("Cannot launch inheritance control");
        CloseHandle(control.hThread);
        std::unique_ptr<void, decltype(&CloseHandle)> control_process(control.hProcess, &CloseHandle);
        if (WaitForSingleObject(control_process.get(), 5000) != WAIT_OBJECT_0) {
            TerminateProcess(control_process.get(), 1);
            WaitForSingleObject(control_process.get(), 1000);
            throw std::runtime_error("Inheritance control did not exit");
        }
        DWORD code = 1;
        if (!GetExitCodeProcess(control_process.get(), &code) || code != 0 ||
            WaitForSingleObject(unrelated.get(), 0) != WAIT_OBJECT_0 || !ResetEvent(unrelated.get()))
            throw std::runtime_error("Inheritance control did not signal parent event");
        auto client = std::make_unique<franchise::PipeClient>(argv[1],
            std::to_wstring(reinterpret_cast<uintptr_t>(unrelated.get())), franchise::ServiceMode::OfflineFixture);
        HANDLE child = OpenProcess(SYNCHRONIZE, FALSE, client->process_id());
        if (!child) throw std::runtime_error("Cannot observe owned child");
        std::string request = R"({"protocol":1,"request_id":"stall","operation":"hello"})";
        request.append(4095 - request.size(), ' ');
        bool stalled = false;
        // Pipe capacity is advisory. Drain prequeued acknowledgements until
        // stdin fills, rather than assuming the requested capacity was used.
        for (int i = 0; i < 64; ++i) {
            client->submit(request);
            auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(100);
            while (!client->ready() && std::chrono::steady_clock::now() < deadline)
                std::this_thread::sleep_for(std::chrono::milliseconds(2));
            if (!client->ready()) {
                // A completed write with a missing reply would hit its five
                // second response deadline. Still pending proves write stall.
                std::this_thread::sleep_for(std::chrono::seconds(6));
                if (!client->ready()) { stalled = true; break; }
            }
            client->take();
            if (WaitForSingleObject(unrelated.get(), 0) != WAIT_TIMEOUT)
                throw std::runtime_error("Unrelated event inherited by sidecar");
        }
        if (!stalled) throw std::runtime_error("Failed to establish a blocked pipe write");
        if (WaitForSingleObject(unrelated.get(), 0) != WAIT_TIMEOUT)
            throw std::runtime_error("Unrelated event inherited by sidecar");
        client.reset();
        DWORD stopped = WaitForSingleObject(child, 5000);
        CloseHandle(child);
        if (stopped != WAIT_OBJECT_0) throw std::runtime_error("Owned child survived shutdown");
        std::cout << "Stalled peer shutdown verified\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
