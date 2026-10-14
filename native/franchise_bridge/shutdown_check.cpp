#include "pipe_client.h"
#include <iostream>
#include <memory>

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) return 1;
    try {
        auto client = std::make_unique<franchise::PipeClient>(argv[1], L"unused", franchise::ServiceMode::OfflineFixture);
        HANDLE child = OpenProcess(SYNCHRONIZE, FALSE, client->process_id());
        if (!child) throw std::runtime_error("Cannot observe owned child");
        std::string request = R"({"protocol":1,"request_id":"stall","operation":"hello"})";
        request.append(4095 - request.size(), ' ');
        client->submit(request);
        auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
        while (!client->ready() && std::chrono::steady_clock::now() < deadline)
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
        client->take();
        // The first frame fills stdin. This second write cannot finish until
        // destruction terminates the peer and closes its inherited read end.
        client->submit(request);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        if (client->ready()) throw std::runtime_error("Expected a stalled write");
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
