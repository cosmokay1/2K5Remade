#include "pipe_client.h"
#include <iostream>

int wmain(int argc, wchar_t** argv) {
    if (argc != 3 && argc != 4) return 2;
    const bool replay = argc == 4 && std::wstring(argv[3]) == L"--replay";
    const bool abrupt = argc == 4 && std::wstring(argv[3]) == L"--abrupt";
    const bool release = argc == 4 && std::wstring(argv[3]) == L"--release";
    if (argc == 4 && !replay && !abrupt && !release) return 2;
    try {
        franchise::PipeClient client(argv[1], argv[2], franchise::ServiceMode::OfflineFixture);
        if (abrupt) {
            std::cout << client.process_id() << std::endl;
            std::cin.get();
            ExitProcess(0);  // Deliberately bypass all client destructors.
        }
        if (release) {
            const char* release_requests[] = {
                R"({"protocol":1,"request_id":"release","operation":"manual_release","team_id":"a","player_id":"v","expected_revision":1,"timeout_ms":1000,"decision_mode":"manual","scope":{"league_year":2026,"removed_on":"2026-06-01","first_regular_season_game":"2026-09-10","exclusions":["additional_termination_pay","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","waiver_transfer"],"covered_guarantees":true,"healthy":true,"current_year_earned_base":0,"source":"synthetic Windows fixture"},"discount":{"league_year":2026,"annual_rate":0,"rate_source":"synthetic zero rate"},"payment_year_offsets":[0,1,2]})",
                R"({"protocol":1,"request_id":"release-player","operation":"player_context","team_id":"a","player_id":"v","timeout_ms":1000})"
            };
            for (const auto* request : release_requests) {
                client.submit(request);
                while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
                std::cout << client.take() << std::endl;
            }
            return 0;
        }
        const char* requests[] = {
            R"({"protocol":1,"request_id":"hello","operation":"hello"})",
            R"({"protocol":1,"request_id":"preview","operation":"preview","team_id":"a","offer":{"player_id":"v","salaries":[10],"signing_bonus":0},"expected_revision":0,"timeout_ms":1000})",
            R"({"protocol":1,"request_id":"dialogue","operation":"negotiate","team_id":"a","offer":{"player_id":"v","salaries":[10],"signing_bonus":0},"expected_revision":0,"timeout_ms":1000,"personality":{},"performance":{},"relationships":{}})",
            R"({"protocol":1,"request_id":"too-large","operation":"manual_sign","team_id":"a","offer":{"player_id":"v","salaries":[101],"signing_bonus":0},"expected_revision":0,"timeout_ms":1000,"decision_mode":"manual"})",
            R"({"protocol":1,"request_id":"agreement","operation":"manual_sign","team_id":"a","offer":{"player_id":"v","salaries":[10],"signing_bonus":0,"guaranteed_salaries":[10]},"expected_revision":0,"timeout_ms":1000,"decision_mode":"manual"})",
            R"({"protocol":1,"request_id":"player","operation":"player_context","team_id":"a","player_id":"v","timeout_ms":1000})"
        };
        for (size_t i = 0; i < sizeof(requests) / sizeof(requests[0]); ++i) {
            if (replay && i != 0 && i != 4 && i != 5) continue;
            client.submit(requests[i]);
            while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
            std::cout << client.take() << std::endl;
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << std::endl;
        return 1;
    }
}
