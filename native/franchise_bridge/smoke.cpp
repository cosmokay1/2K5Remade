#include "pipe_client.h"
#include <iostream>

int wmain(int argc, wchar_t** argv) {
    if (argc != 3 && argc != 4) return 2;
    const bool promise_context = argc == 4 && std::wstring(argv[3]) == L"--promise-context";
    const bool calendar_context = argc == 4 && std::wstring(argv[3]) == L"--calendar-context";
    const bool calendar_release_context = argc == 4 && std::wstring(argv[3]) == L"--calendar-release-context";
    const bool calendar_release = argc == 4 && std::wstring(argv[3]) == L"--calendar-release";
    const bool replay = argc == 4 && std::wstring(argv[3]) == L"--replay";
    const bool abrupt = argc == 4 && std::wstring(argv[3]) == L"--abrupt";
    const bool compact_release = argc == 4 && std::wstring(argv[3]) == L"--compact-release";
    const bool capacity = argc == 4 && std::wstring(argv[3]) == L"--receipt-capacity";
    const bool release = argc == 4 && std::wstring(argv[3]) == L"--release";
    const bool assignment = argc == 4 && std::wstring(argv[3]) == L"--trade";
    const bool restructure = argc == 4 && std::wstring(argv[3]) == L"--restructure";
    const bool returning = argc == 4 && (std::wstring(argv[3]) == L"--return" || std::wstring(argv[3]) == L"--return-replay");
    const bool return_replay = argc == 4 && std::wstring(argv[3]) == L"--return-replay";
    const bool returned_amendment = argc == 4 && std::wstring(argv[3]) == L"--returned-restructure";
    const bool generation_trade = argc == 4 && std::wstring(argv[3]) == L"--generation-trade";
    if (argc == 4 && !calendar_context && !calendar_release_context && !calendar_release && !promise_context && !compact_release && !capacity && !generation_trade && !returned_amendment && !replay && !abrupt && !release && !assignment && !restructure && !returning) return 2;
    try {
        franchise::PipeClient client(argv[1], argv[2], franchise::ServiceMode::OfflineFixture);
        if (calendar_context || calendar_release_context || calendar_release) {
            if (calendar_release) {
                client.submit(R"({"protocol":1,"request_id":"calendar-release","operation":"manual_release","team_id":"a","player_id":"a","expected_revision":3,"timeout_ms":5000,"decision_mode":"manual","calendar_format":"calendar_v1","generation_id":"legacy-contract:6a82e497f58043c0c18152df7d39335462babd6c6f98b619af8d6f03f0f77ec2","scope":{"league_year":2027,"removed_on":"2027-07-01","first_regular_season_game":"2027-09-10","exclusions":["additional_termination_pay","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","waiver_transfer"],"covered_guarantees":true,"healthy":true,"current_year_earned_base":0,"source":"synthetic Windows calendar release"},"discount":{"league_year":2027,"annual_rate":0,"rate_source":"synthetic discount"},"payment_year_offsets":[0,1]})");
                while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
                std::cout << client.take() << std::endl;
            }
            const char* requests[] = {
                R"({"protocol":1,"request_id":"calendar-current","operation":"contract_context","team_id":"a","generation_id":"legacy-contract:6a82e497f58043c0c18152df7d39335462babd6c6f98b619af8d6f03f0f77ec2","timeout_ms":5000,"context_format":"calendar_v1"})",
                R"({"protocol":1,"request_id":"calendar-expired","operation":"contract_context","team_id":"b","generation_id":"legacy-contract:66c0244076e7869a68431355e9e1f6bedced76f2ae8afb3d1907b327a65a252b","timeout_ms":5000,"context_format":"calendar_v1"})",
                R"({"protocol":1,"request_id":"calendar-player-current","operation":"player_context","team_id":"a","player_id":"a","timeout_ms":5000,"context_format":"calendar_v1"})",
                R"({"protocol":1,"request_id":"calendar-player-expired","operation":"player_context","team_id":"b","player_id":"b","timeout_ms":5000,"context_format":"calendar_v1"})"
            };
            for (const auto* request : requests) {
                auto parsed=nlohmann::json::parse(request);
                if (calendar_release_context || calendar_release) parsed["context_format"]="calendar_v2";
                client.submit(parsed.dump());
                while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
                std::cout << client.take() << std::endl;
            }
            return 0;
        }
        if (abrupt) {
            std::cout << client.process_id() << std::endl;
            std::cin.get();
            ExitProcess(0);  // Deliberately bypass all client destructors.
        }
        if (promise_context) {
            client.submit(R"({"protocol":1,"request_id":"promise-context","operation":"player_context","team_id":"a","player_id":"p","timeout_ms":5000})");
            while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
            std::cout << client.take() << std::endl;
            return 0;
        }
        if (generation_trade) {
            const char* requests[] = {
                R"({"protocol":1,"request_id":"native-generation-assignment","operation":"manual_trade","seller":"a","buyer":"b","player_id":"v","seller_revision":6,"buyer_revision":1,"seller_generation_id":"contract-gen:b1b0159b144a9d2dc7ba7aac3130c7c6a15318dbf98792c08a728f646158bdc2","buyer_previous_generation_id":null,"timeout_ms":5000,"decision_mode":"manual","scope":{"league_year":2026,"traded_on":"2026-06-01","seller_first_regular_season_game":"2026-09-10","buyer_first_regular_season_game":"2026-09-10","exclusions":["conditional_consideration","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","seller_retained_guarantees","unpaid_or_deferred_bonus","waiver_transfer"],"healthy":true,"current_year_earned_base":0,"assignment_consent":true,"transaction_eligible":true,"source":"synthetic Windows generation assignment"}})",
                R"({"protocol":1,"request_id":"generation-buyer","operation":"player_context","team_id":"b","player_id":"v","timeout_ms":5000})"
            };
            for (const auto* request : requests) {
                client.submit(request);
                while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
                std::cout << client.take() << std::endl;
            }
            return 0;
        }
        if (returned_amendment) {
            const char* requests[] = {
                R"({"protocol":1,"request_id":"return-conversion","operation":"manual_restructure","team_id":"a","player_id":"v","generation_id":"contract-gen:b1b0159b144a9d2dc7ba7aac3130c7c6a15318dbf98792c08a728f646158bdc2","expected_revision":4,"timeout_ms":5000,"decision_mode":"manual","converted_base":4,"scope":{"league_year":2026,"amended_on":"2026-06-01","first_regular_season_game":"2026-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"synthetic annual floors","source":"synthetic Windows returned amendment"}})",
                R"({"protocol":1,"request_id":"returned-amended-player","operation":"player_context","team_id":"a","player_id":"v","timeout_ms":5000})"
            };
            for (const auto* request : requests) {
                client.submit(request);
                while (!client.ready()) std::this_thread::sleep_for(std::chrono::milliseconds(2));
                std::cout << client.take() << std::endl;
            }
            return 0;
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
        if (release || capacity || compact_release) {
            const char* release_requests[] = {
                R"({"protocol":1,"request_id":"release","operation":"manual_release","team_id":"a","player_id":"v","expected_revision":1,"timeout_ms":1000,"decision_mode":"manual","scope":{"league_year":2026,"removed_on":"2026-06-01","first_regular_season_game":"2026-09-10","exclusions":["additional_termination_pay","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","waiver_transfer"],"covered_guarantees":true,"healthy":true,"current_year_earned_base":0,"source":"synthetic Windows fixture"},"discount":{"league_year":2026,"annual_rate":0,"rate_source":"synthetic zero rate"},"payment_year_offsets":[0,1,2]})",
                R"({"protocol":1,"request_id":"release-player","operation":"player_context","team_id":"a","player_id":"v","timeout_ms":1000})"
            };
            for (size_t index=0;index<((capacity || compact_release) ? 1 : 2);++index) {
                auto request=franchise::parse_frame(release_requests[index]);
                if (compact_release) {
                    request["receipt_format"]="target_v1";
                    request["request_id"]="compact-release";
                    request["expected_revision"]=31;
                    request["timeout_ms"]=5000;
                }
                client.submit(request.dump());
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
