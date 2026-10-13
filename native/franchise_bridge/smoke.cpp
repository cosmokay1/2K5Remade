#include "pipe_client.h"
#include <iostream>

int wmain(int argc, wchar_t** argv) {
    if (argc != 3) return 2;
    try {
        franchise::PipeClient client(argv[1], argv[2]);
        const char* requests[] = {
            R"({"protocol":1,"request_id":"hello","operation":"hello"})",
            R"({"protocol":1,"request_id":"preview","operation":"preview","team_id":"a","offer":{"player_id":"v","salaries":[10],"signing_bonus":0},"expected_revision":0,"timeout_ms":1000})",
            R"({"protocol":1,"request_id":"dialogue","operation":"negotiate","team_id":"a","offer":{"player_id":"v","salaries":[10],"signing_bonus":0},"expected_revision":0,"timeout_ms":1000,"personality":{},"performance":{},"relationships":{}})"
        };
        for (const char* request : requests) {
            client.submit(request);
            while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
            std::cout << client.take() << std::endl;
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << std::endl;
        return 1;
    }
}
