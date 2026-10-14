#include "pipe_client.h"
#include <iostream>

int wmain(int argc, wchar_t** argv) {
    if (argc != 3 && argc != 4) return 2;
    const bool replay = argc == 4 && std::wstring(argv[3]) == L"--replay";
    const bool abrupt = argc == 4 && std::wstring(argv[3]) == L"--abrupt";
    const bool release = argc == 4 && std::wstring(argv[3]) == L"--release";
    const bool assignment = argc == 4 && std::wstring(argv[3]) == L"--trade";
    const bool restructure = argc == 4 && std::wstring(argv[3]) == L"--restructure";
    const bool returning = argc == 4 && (std::wstring(argv[3]) == L"--return" || std::wstring(argv[3]) == L"--return-replay");
    const bool return_replay = argc == 4 && std::wstring(argv[3]) == L"--return-replay";
    if (argc == 4 && !replay && !abrupt && !release && !assignment && !restructure && !returning) return 2;
    try {
        franchise::PipeClient client(argv[1], argv[2], franchise::ServiceMode::OfflineFixture);
        if (abrupt) {
            std::cout << client.process_id() << std::endl;
            std::cin.get();
            ExitProcess(0);  // Deliberately bypass all client destructors.
        }
        if (returning) {
            const char* requests[] = {
                R"({"protocol":1,"team_id":"a","offer":{"player_id":"v","salaries":[5,5,5],"signing_bonus":3,"guaranteed_salaries":[5,0,0]},"expected_revision":2,"timeout_ms":5000,"return_scope":{"league_year":2026,"signed_on":"2026-06-01","first_regular_season_game":"2026-09-10","healthy":true,"exclusions":["extensions","guarantee_offsets","league_year_rollover","rookie_contracts"],"source":"synthetic Windows return"},"request_id":"return-preview","operation":"preview"})",
                R"({"protocol":1,"team_id":"a","offer":{"player_id":"v","salaries":[5,5,5],"signing_bonus":3,"guaranteed_salaries":[5,0,0]},"expected_revision":2,"timeout_ms":5000,"return_scope":{"league_year":2026,"signed_on":"2026-06-01","first_regular_season_game":"2026-09-10","healthy":true,"exclusions":["extensions","guarantee_offsets","league_year_rollover","rookie_contracts"],"source":"synthetic Windows return"},"request_id":"return-agreement","operation":"manual_sign","decision_mode":"manual"})",
                R"({"protocol":1,"request_id":"returned-player","operation":"player_context","team_id":"a","player_id":"v","timeout_ms":5000})"
            };
            for (size_t i=return_replay ? 1 : 0;i<3;++i) {
                client.submit(requests[i]);
                while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
                std::cout << client.take() << std::endl;
            }
            return 0;
        }
        if (restructure) {
            const char* requests[] = {
                R"({"protocol":1,"request_id":"conversion","operation":"manual_restructure","team_id":"a","player_id":"v","expected_revision":1,"timeout_ms":1000,"decision_mode":"manual","converted_base":8,"scope":{"league_year":2026,"amended_on":"2026-06-01","first_regular_season_game":"2026-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"synthetic annual floors","source":"synthetic Windows amendment"}})",
                R"({"protocol":1,"request_id":"amended-player","operation":"player_context","team_id":"a","player_id":"v","timeout_ms":1000})"
            };
            for (const auto* request : requests) {
                client.submit(request);
                while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
                std::cout << client.take() << std::endl;
            }
            return 0;
        }
        if (assignment) {
            const char* requests[] = {
                R"({"protocol":1,"request_id":"assignment","operation":"manual_trade","seller":"a","buyer":"b","player_id":"v","seller_revision":1,"buyer_revision":1,"timeout_ms":1000,"decision_mode":"manual","scope":{"league_year":2026,"traded_on":"2026-06-01","seller_first_regular_season_game":"2026-09-10","buyer_first_regular_season_game":"2026-09-11","exclusions":["conditional_consideration","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","seller_retained_guarantees","unpaid_or_deferred_bonus","waiver_transfer"],"healthy":true,"current_year_earned_base":0,"assignment_consent":true,"transaction_eligible":true,"source":"synthetic Windows assignment"}})",
                R"({"protocol":1,"request_id":"assigned-player","operation":"player_context","team_id":"b","player_id":"v","timeout_ms":1000})"
            };
            for (const auto* request : requests) {
                client.submit(request);
                while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
                std::cout << client.take() << std::endl;
            }
            return 0;
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
