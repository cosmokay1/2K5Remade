#include "contract_response.h"
#include <iostream>

int main() {
    try {
        const std::string valid = R"({"protocol":1,"request_id":"one","result":{},"error":null,"detail":null})";
        franchise::decode_response(valid, "one");
        for (const std::string& bad : {
            std::string(R"({"protocol":true,"request_id":"one","result":{},"error":null,"detail":null})"),
            std::string(R"({"protocol":1,"protocol":2,"request_id":"one","result":{},"error":null,"detail":null})"),
            std::string(R"({"protocol":1,"request_id":"other","result":{},"error":null,"detail":null})"),
            std::string(R"({"protocol":1,"request_id":"one","result":{},"error":"busy","detail":null})"),
            std::string(R"({"protocol":1,"request_id":"one","result":null,"error":null,"detail":null})"),
            std::string("not JSON")}) {
            bool rejected = false;
            try { franchise::decode_response(bad, "one"); }
            catch (const std::exception&) { rejected = true; }
            if (!rejected) throw std::runtime_error("Malformed response accepted");
        }
        franchise::decode_response(R"({"protocol":1,"request_id":"one","result":null,"error":"busy","detail":null})", "one");
        auto request = franchise::parse_frame(R"({"operation":"manual_sign","request_id":"one","offer":{"player_id":"v","salaries":[10],"signing_bonus":0,"guaranteed_salaries":[8]}})");
        auto reply = franchise::parse_frame(R"({"error":null,"result":{"request_id":"one","offer":{"player_id":"v","salaries":[10],"signing_bonus":0,"guaranteed_salaries":[8]},"action":"accept","outcome":"signed","counter":null,"decision_mode":"manual","charges":[10]}})");
        franchise::validate_result(reply, request);
        for (int scenario = 0; scenario < 4; ++scenario) {
            auto bad = reply;
            if (scenario == 0) bad["result"]["offer"]["guaranteed_salaries"] = {0};
            if (scenario == 1) bad["result"]["charges"] = {10.5};
            if (scenario == 2) bad["result"]["charges"] = {"2/4"};
            if (scenario == 3) bad["result"]["decision_mode"] = "automatic";
            bool rejected = false;
            try { franchise::validate_result(bad, request); } catch (const std::exception&) { rejected = true; }
            if (!rejected) throw std::runtime_error("Invalid contract result accepted");
        }
        franchise::exact_money("1/2");
        auto promised_request = request;
        promised_request["operation"] = "negotiate";
        auto goals = franchise::parse_frame(R"([{"goal_id":"starts","metric":"starts","target":12,"importance":80,"window":"2026","source":"offer"}])");
        promised_request["promise_goals"] = goals;
        auto promised_reply = reply;
        promised_reply["result"]["promise_goals"] = goals;
        promised_reply["result"]["counter_promises"] = nullptr;
        franchise::validate_result(promised_reply, promised_request);
        for (int scenario = 0; scenario < 4; ++scenario) {
            auto bad = promised_reply;
            if (scenario == 0) bad["result"]["promise_goals"][0]["target"] = 13;
            if (scenario == 1) bad["result"].erase("promise_goals");
            if (scenario == 2) bad["result"]["counter_promises"] = goals;
            if (scenario == 3) bad["result"]["promise_goals"][0]["importance"] = true;
            bool rejected = false;
            try { franchise::validate_result(bad, promised_request); } catch (const std::exception&) { rejected = true; }
            if (!rejected) throw std::runtime_error("Changed promise result accepted");
        }
        auto player_request = franchise::parse_frame(R"({"operation":"player_context","player_id":"v"})");
        auto player_reply = franchise::parse_frame(R"({"error":null,"result":{"player_id":"v","financial_revision":0,"initialized":true,"personality":{},"relationships":{},"agreed_promises":[],"promise_history":[]}})");
        franchise::validate_result(player_reply, player_request);
        for (int scenario = 0; scenario < 5; ++scenario) {
            auto bad = player_reply;
            if (scenario == 0) bad["result"]["player_id"] = "other";
            if (scenario == 1) bad["result"]["financial_revision"] = true;
            if (scenario == 2) bad["result"]["personality"] = nullptr;
            if (scenario == 3) bad["result"]["promise_history"] = {1};
            if (scenario == 4) bad["result"]["agreed_promises"] = {{{"agreement_request_id", ""}, {"goals", nlohmann::json::array()}}};
            bool rejected = false;
            try { franchise::validate_result(bad, player_request); } catch (const std::exception&) { rejected = true; }
            if (!rejected) throw std::runtime_error("Invalid player context accepted");
        }
        std::cout << "Protocol envelope and contract validation passed" << std::endl;
        return 0;
    } catch (const std::exception& error) { std::cerr << error.what() << std::endl; return 1; }
}
