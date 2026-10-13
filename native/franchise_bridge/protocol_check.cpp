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
        auto restructure_request=franchise::parse_frame(R"({"operation":"manual_restructure","request_id":"conversion","team_id":"a","player_id":"v","expected_revision":1,"converted_base":8,"decision_mode":"manual","scope":{"source":"synthetic amendment","exclusions":["void_years","extension"]}})");
        auto restructure_reply=franchise::parse_frame(R"({"error":null,"result":{"decision_mode":"manual","team_id":"a","player_id":"v","restructure":{"financial":{"revision":2,"charges":[19,37],"signed_players":["v"],"restructures":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[10,20,30],"signing_bonus":9,"guaranteed_salaries":[10,20,10]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":69,"paid":19,"source":"synthetic paid history","paid_components":[["signing_bonus",9],["base:0",10]]},"scope":{"source":"synthetic amendment","exclusions":["extension","void_years"]},"annual_minimums":[1,1],"converted_base":8,"bonus_layer":{"record_id":"restructure:conversion","amount":8,"original_start_index":1,"allocation_years":2,"source":"synthetic amendment"},"contract":{"offer":{"player_id":"v","salaries":[10,12,30],"signing_bonus":9,"guaranteed_salaries":[10,12,10]},"source":"synthetic original; base conversion: synthetic amendment","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"restructure:conversion","amount":8,"original_start_index":1,"allocation_years":2,"source":"synthetic amendment"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":69,"paid":19,"source":"synthetic paid history; base conversion: synthetic amendment","paid_components":[["signing_bonus",9],["base:0",10]]}}}},"cash":{"revision":2,"nominal_total":69,"paid_total":19,"unpaid_total":50,"obligations":[]}}}})");
        auto& restructure_archive=restructure_reply["result"]["restructure"]["financial"]["restructures"]["v"];
        restructure_reply["result"]["restructure"]["cash"]["obligations"].push_back(restructure_archive["cash_obligation"]);
        franchise::validate_result(restructure_reply,restructure_request);
        for (int scenario=0;scenario<31;++scenario) {
            auto bad=restructure_reply, bad_request=restructure_request;
            auto& financial=bad["result"]["restructure"]["financial"];
            auto& cash=bad["result"]["restructure"]["cash"];
            auto& archive=financial["restructures"]["v"];
            if (scenario==0) bad["result"]["team_id"]="other";
            if (scenario==1) financial["revision"]=3;
            if (scenario==2) financial["signed_players"]=nlohmann::json::array();
            if (scenario==3) financial["signed_players"]={"v","v"};
            if (scenario==4) financial["charges"]={19.5,37};
            if (scenario==5) archive["scope"]["source"]="other";
            if (scenario==6) archive["converted_base"]=7;
            if (scenario==7) archive["bonus_layer"]["record_id"]="restructure:other";
            if (scenario==8) archive["contract"]["offer"]["salaries"][0]=9;
            if (scenario==9) archive["contract"]["offer"]["guaranteed_salaries"][1]=11;
            if (scenario==10) archive["contract"]["offer"]["signing_bonus"]=0;
            if (scenario==11) archive["contract"]["elapsed_years"]=0;
            if (scenario==12) archive["original_contract"]["bonus_layers"]={archive["bonus_layer"]};
            if (scenario==13) archive["contract"]["bonus_layers"].push_back(archive["bonus_layer"]);
            if (scenario==14) archive["bonus_layer"]["amount"]=true;
            if (scenario==15) archive["annual_minimums"]={13,1};
            if (scenario==16) archive["cash_obligation"]["amount"]=61;
            if (scenario==17) archive["cash_obligation"]["paid"]=20;
            if (scenario==18) archive["original_cash"]["paid_components"]={{"base:1",19}};
            if (scenario==19) cash["unpaid_total"]=49;
            if (scenario==20) cash["obligations"].push_back(archive["cash_obligation"]);
            if (scenario==21) cash["obligations"][0]["source"]="changed";
            if (scenario==22) bad_request["expected_revision"]=std::numeric_limits<int64_t>::max();
            if (scenario==23) bad_request["scope"]["exclusions"]={"void_years","void_years"};
            if (scenario==24) {
                archive["original_contract"]["offer"]["salaries"][2]=std::numeric_limits<int64_t>::max();
                archive["contract"]["offer"]["salaries"][2]=std::numeric_limits<int64_t>::max();
            }
            if (scenario==25) archive["bonus_layer"]["allocation_years"]=1;
            if (scenario==26) archive["cash_obligation"]["paid_components"].push_back({"bonus:restructure:conversion",0});
            if (scenario==27) archive["original_contract"]["unknown"]=0;
            if (scenario==28) bad_request["decision_mode"]="automatic";
            if (scenario==29) bad["result"]["decision_mode"]="automatic";
            if (scenario==30) cash["nominal_total"]=std::numeric_limits<uint64_t>::max();
            bool rejected=false;
            try { franchise::validate_result(bad,bad_request); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Invalid amendment response accepted: "+std::to_string(scenario));
        }
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
        auto release_request=franchise::parse_frame(R"({"operation":"manual_release","player_id":"v","expected_revision":1})");
        auto release_reply=franchise::parse_frame(R"({"error":null,"result":{"decision_mode":"manual","player_id":"v","release":{"financial":{"revision":2,"signed_players":[],"charges":[39],"released_contracts":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[10,20,30],"signing_bonus":9}}}}},"cash":{"nominal_total":39,"paid_total":9,"unpaid_total":30}}}})");
        release_request["scope"]={{"source","fixture"},{"exclusions",{"b","a"}}};
        release_request["discount"]={{"league_year",2026},{"annual_rate",0},{"rate_source","synthetic"}};
        release_request["payment_year_offsets"]={0,1,2};
        auto& release_archive=release_reply["result"]["release"]["financial"]["released_contracts"]["v"];
        release_archive["scope"]=release_request["scope"];
        release_archive["scope"]["exclusions"]={"a","b"};
        release_archive["discount"]=release_request["discount"];
        release_archive["payment_year_offsets"]=release_request["payment_year_offsets"];
        franchise::validate_result(release_reply,release_request);
        auto trade_request=franchise::parse_frame(R"({"operation":"manual_trade","seller":"a","buyer":"b","player_id":"v","seller_revision":1,"buyer_revision":1,"scope":{"source":"fixture","exclusions":[]}})");
        auto trade_reply=franchise::parse_frame(R"({"error":null,"result":{"decision_mode":"manual","seller":"a","buyer":"b","player_id":"v","trade":{"a":{"financial":{"revision":2,"charges":[9],"signed_players":[]},"cash":{"nominal_total":9,"paid_total":9,"unpaid_total":0}},"b":{"financial":{"revision":2,"charges":[10,20,30],"signed_players":["v"]},"cash":{"nominal_total":60,"paid_total":0,"unpaid_total":60}}}}})");
        auto assignment_archive=nlohmann::json{{"scope",trade_request["scope"]},{"original_contract",release_archive["original_contract"]}};
        trade_reply["result"]["trade"]["a"]["financial"]["outgoing_trades"]={{"v",assignment_archive}};
        trade_reply["result"]["trade"]["b"]["financial"]["incoming_trades"]={{"v",assignment_archive}};
        franchise::validate_result(trade_reply,trade_request);
        for (int scenario=0;scenario<6;++scenario) {
            auto bad=trade_reply;
            if (scenario==0) bad["result"]["trade"]["a"]["financial"]["signed_players"]={"v"};
            if (scenario==1) bad["result"]["trade"]["b"]["financial"]["signed_players"]=nlohmann::json::array();
            if (scenario==2) bad["result"]["trade"]["b"]["financial"]["revision"]=3;
            if (scenario==3) bad["result"]["trade"]["b"]["financial"]["incoming_trades"]["v"]["scope"]["source"]="other";
            if (scenario==4) bad["result"]["trade"]["b"]["cash"]["unpaid_total"]=55;
            if (scenario==5) bad["result"]["trade"]["b"]["financial"]["incoming_trades"]["v"]["assigned_base"]=60;
            bool rejected=false;
            try { franchise::validate_result(bad,trade_request); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Invalid paired assignment accepted");
        }
        for (int scenario=0;scenario<7;++scenario) {
            auto bad=release_reply;
            if (scenario==0) bad["result"]["release"]["financial"]["signed_players"]={"v"};
            if (scenario==1) bad["result"]["release"]["financial"]["charges"]={39.5};
            if (scenario==2) bad["result"]["release"]["cash"]["unpaid_total"]=0;
            if (scenario==3) bad["result"]["release"]["financial"]["revision"]=3;
            auto& bad_archive=bad["result"]["release"]["financial"]["released_contracts"]["v"];
            if (scenario==4) bad_archive["scope"]["source"]="other";
            if (scenario==5) bad_archive["discount"]["annual_rate"]=1;
            if (scenario==6) bad_archive["payment_year_offsets"]={0,0,0};
            bool rejected=false;
            try { franchise::validate_result(bad,release_request); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Invalid release response accepted");
        }
        auto promised_request = request;
        promised_request["operation"] = "negotiate";
        auto goals = franchise::parse_frame(R"([{"goal_id":"starts","metric":"starts","target":12,"importance":80,"window":"2026","source":"offer"}])");
        promised_request["promise_goals"] = goals;
        auto promised_reply = reply;
        promised_reply["result"]["promise_goals"] = goals;
        promised_reply["result"]["counter_promises"] = nullptr;
        franchise::validate_result(promised_reply, promised_request);
        auto counter_reply = promised_reply;
        counter_reply["result"]["action"] = "counter";
        counter_reply["result"]["outcome"] = "counteroffer";
        counter_reply["result"]["counter"] = request["offer"];
        counter_reply["result"]["counter_promises"] = goals;
        counter_reply["result"]["counter_promises"][0]["target"] = 8;
        franchise::validate_result(counter_reply, promised_request);
        counter_reply["result"]["counter_promises"] = nlohmann::json::array();
        franchise::validate_result(counter_reply, promised_request); // Explicit withdrawal.
        for (int scenario = 0; scenario < 5; ++scenario) {
            auto bad = counter_reply;
            bad["result"]["counter_promises"] = goals;
            if (scenario == 0) bad["result"]["counter_promises"] = nullptr;
            if (scenario == 1) bad["result"]["counter_promises"].push_back(goals[0]);
            if (scenario == 2) bad["result"]["counter_promises"][0]["metric"] = "overall_rating";
            if (scenario == 3) bad["result"]["counter_promises"][0]["source"] = " ";
            if (scenario == 4) bad["result"]["counter_promises"][0]["target"] = 8.5;
            bool rejected = false;
            try { franchise::validate_result(bad, promised_request); } catch (const std::exception&) { rejected = true; }
            if (!rejected) throw std::runtime_error("Invalid counter promises accepted");
        }
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
        player_reply["result"]["contract_accounting"]=nullptr;
        franchise::validate_result(player_reply,player_request);
        auto accounting=nlohmann::json{{"status","active"},{"charge_scope","active_contract"},
            {"annual_charges",{19,37}},{"contract",restructure_archive["contract"]},
            {"cash_obligation",restructure_archive["cash_obligation"]},
            {"guarantees",{{"unpaid_guaranteed_base_by_original_year",{0,12,10}},
                {"unpaid_signing_bonus",8},{"unpaid_original_signing_bonus",0},
                {"unpaid_bonus_layers",{{"bonus:restructure:conversion",8}}},{"obligation_source","synthetic paid history"}}}};
        player_reply["result"]["contract_accounting"]=accounting;
        franchise::validate_result(player_reply,player_request);
        auto unknown=accounting;
        unknown["cash_obligation"].erase("paid_components"); unknown["guarantees"]=nullptr;
        player_reply["result"]["contract_accounting"]=unknown;
        franchise::validate_result(player_reply,player_request);
        unknown["cash_obligation"]=nullptr;
        player_reply["result"]["contract_accounting"]=unknown;
        franchise::validate_result(player_reply,player_request);
        auto retained=accounting;
        retained["status"]="released"; retained["charge_scope"]="retained_obligations"; retained["annual_charges"]={36};
        retained["cash_obligation"]["amount"]=49;
        player_reply["result"]["contract_accounting"]=retained;
        franchise::validate_result(player_reply,player_request);
        retained["status"]="assigned";
        retained["cash_obligation"]=nullptr;
        retained["guarantees"]={{"unpaid_guaranteed_base_by_original_year",{0,0,0}},
            {"unpaid_signing_bonus",0},{"unpaid_original_signing_bonus",0},
            {"unpaid_bonus_layers",{{"bonus:restructure:conversion",0}}}};
        player_reply["result"]["contract_accounting"]=retained;
        franchise::validate_result(player_reply,player_request);
        retained["cash_obligation"]=accounting["cash_obligation"];
        retained["cash_obligation"]["amount"]=27; retained["cash_obligation"]["paid"]=27;
        retained["cash_obligation"]["paid_components"].push_back({"bonus:restructure:conversion",8});
        retained["guarantees"]={{"unpaid_guaranteed_base_by_original_year",{0,0,0}},{"unpaid_signing_bonus",0}};
        player_reply["result"]["contract_accounting"]=retained;
        franchise::validate_result(player_reply,player_request);
        player_reply["result"]["contract_accounting"]=accounting;
        for (int scenario=0;scenario<20;++scenario) {
            auto bad=player_reply;
            auto& saved=bad["result"]["contract_accounting"];
            if (scenario==0) saved["extra"]=true;
            if (scenario==1) saved["status"]="unsigned";
            if (scenario==2) saved["charge_scope"]="retained_obligations";
            if (scenario==3) saved["annual_charges"]={19};
            if (scenario==4) saved["annual_charges"]={"2/4",37};
            if (scenario==5) saved["contract"]["offer"]["player_id"]="other";
            if (scenario==6) saved["contract"]["elapsed_years"]=true;
            if (scenario==7) saved["contract"]["bonus_layers"].push_back(saved["contract"]["bonus_layers"][0]);
            if (scenario==8) saved["contract"]["bonus_layers"][0]["original_start_index"]=std::numeric_limits<int64_t>::max();
            if (scenario==9) saved["cash_obligation"]["player_id"]="other";
            if (scenario==10) saved["cash_obligation"]["amount"]=18;
            if (scenario==11) saved["cash_obligation"]["paid_components"][0][1]=8;
            if (scenario==12) saved["guarantees"]["unpaid_guaranteed_base_by_original_year"]={12};
            if (scenario==13) saved["guarantees"]["unpaid_guaranteed_base_by_original_year"][1]=13;
            if (scenario==14) saved["guarantees"]["unpaid_signing_bonus"]=7;
            if (scenario==15) saved["guarantees"]["unpaid_bonus_layers"]={{"bonus:other",8}};
            if (scenario==16) saved["guarantees"]["unpaid_original_signing_bonus"]=true;
            if (scenario==17) saved["guarantees"]["ability_rating"]=99;
            if (scenario==18) {saved["status"]="assigned";saved["charge_scope"]="retained_obligations";}
            if (scenario==19) saved["contract"]["source"]=" ";
            bool rejected=false;
            try { franchise::validate_result(bad,player_request); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Invalid saved player accounting accepted: "+std::to_string(scenario));
        }
        player_reply["result"]["agreed_promises"] = {{{"agreement_request_id", "one"}, {"goals", goals}}};
        franchise::validate_result(player_reply, player_request);
        for (int scenario = 0; scenario < 7; ++scenario) {
            auto bad = player_reply;
            if (scenario == 0) bad["result"]["player_id"] = "other";
            if (scenario == 1) bad["result"]["financial_revision"] = true;
            if (scenario == 2) bad["result"]["personality"] = nullptr;
            if (scenario == 3) bad["result"]["promise_history"] = {1};
            if (scenario == 4) bad["result"]["agreed_promises"] = {{{"agreement_request_id", ""}, {"goals", nlohmann::json::array()}}};
            if (scenario == 5) bad["result"]["agreed_promises"][0]["goals"][0]["metric"] = "catching_rating";
            if (scenario == 6) bad["result"]["negotiation_history"] = {{{"offer", {{"player_id", "other"}, {"salaries", {10}}, {"signing_bonus", 0}}}}};
            bool rejected = false;
            try { franchise::validate_result(bad, player_request); } catch (const std::exception&) { rejected = true; }
            if (!rejected) throw std::runtime_error("Invalid player context accepted");
        }
        std::cout << "Protocol envelope and contract validation passed" << std::endl;
        return 0;
    } catch (const std::exception& error) { std::cerr << error.what() << std::endl; return 1; }
}
