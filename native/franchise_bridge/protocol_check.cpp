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
        auto return_scope=franchise::parse_frame(R"({"league_year":2026,"signed_on":"2026-06-01","first_regular_season_game":"2026-09-10","healthy":true,"exclusions":["extensions","guarantee_offsets","league_year_rollover","rookie_contracts"],"source":"synthetic return"})");
        auto return_request=request;
        return_request["return_scope"]=return_scope;
        auto return_reply=reply;
        return_reply["result"]["return_scope"]=return_scope;
        franchise::validate_result(return_reply,return_request);
        for (int scenario=0;scenario<6;++scenario) {
            auto bad=return_reply;
            if (scenario==0) bad["result"].erase("return_scope");
            if (scenario==1) bad["result"]["return_scope"]["healthy"]=1;
            if (scenario==2) bad["result"]["return_scope"]["source"]="changed";
            if (scenario==3) bad["result"]["return_scope"]["signed_on"]="2026-06-02";
            if (scenario==4) bad["result"]["return_scope"]["league_year"]=2026.0;
            bool rejected=false;
            try { franchise::validate_result(bad,scenario==5 ? request : return_request); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Return mode/source substitution accepted");
        }
        auto restructure_request=franchise::parse_frame(R"({"operation":"manual_restructure","request_id":"conversion","team_id":"a","player_id":"v","expected_revision":1,"converted_base":8,"decision_mode":"manual","scope":{"source":"synthetic amendment","exclusions":["void_years","extension"]}})");
        auto restructure_reply=franchise::parse_frame(R"({"error":null,"result":{"decision_mode":"manual","team_id":"a","player_id":"v","restructure":{"financial":{"revision":2,"charges":[19,37],"signed_players":["v"],"restructures":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[10,20,30],"signing_bonus":9,"guaranteed_salaries":[10,20,10]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":69,"paid":19,"source":"synthetic paid history","paid_components":[["signing_bonus",9],["base:0",10]]},"scope":{"source":"synthetic amendment","exclusions":["extension","void_years"]},"annual_minimums":[1,1],"converted_base":8,"bonus_layer":{"record_id":"restructure:conversion","amount":8,"original_start_index":1,"allocation_years":2,"source":"synthetic amendment"},"contract":{"offer":{"player_id":"v","salaries":[10,12,30],"signing_bonus":9,"guaranteed_salaries":[10,12,10]},"source":"synthetic original; base conversion: synthetic amendment","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"restructure:conversion","amount":8,"original_start_index":1,"allocation_years":2,"source":"synthetic amendment"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":69,"paid":19,"source":"synthetic paid history; base conversion: synthetic amendment","paid_components":[["signing_bonus",9],["base:0",10]]}}}},"cash":{"revision":2,"nominal_total":69,"paid_total":19,"unpaid_total":50,"obligations":[]}}}})");
        auto& restructure_archive=restructure_reply["result"]["restructure"]["financial"]["restructures"]["v"];
        restructure_reply["result"]["restructure"]["cash"]["obligations"].push_back(restructure_archive["cash_obligation"]);
        franchise::validate_result(restructure_reply,restructure_request);
        auto generation_request=restructure_request, generation_reply=restructure_reply;
        const auto generation_id="contract-gen:"+std::string(64,'c');
        generation_request["generation_id"]=generation_id;
        generation_reply["result"]["generation_id"]=generation_id;
        auto& generation_archive=generation_reply["result"]["restructure"]["financial"]["restructures"]["v"];
        generation_archive["original_cash"]["obligation_id"]=generation_id;
        generation_archive["cash_obligation"]["obligation_id"]=generation_id;
        generation_reply["result"]["restructure"]["cash"]["obligations"][0]["obligation_id"]=generation_id;
        franchise::validate_result(generation_reply,generation_request);
        for (int scenario=0;scenario<5;++scenario) {
            auto bad=generation_reply, input=generation_request;
            if (scenario==0) bad["result"].erase("generation_id");
            if (scenario==1) bad["result"]["generation_id"]="contract-gen:"+std::string(64,'d');
            if (scenario==2) input["generation_id"]=true;
            if (scenario==3) bad["result"]["restructure"]["financial"]["restructures"]["v"]["original_cash"]["obligation_id"]="contract:v";
            if (scenario==4) input.erase("generation_id");
            bool rejected=false;
            try { franchise::validate_result(bad,input); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Amendment agreement substitution accepted");
        }
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
        auto released_cash=franchise::parse_frame(R"({"obligation_id":"contract:v","player_id":"v","amount":39,"paid":9,"source":"synthetic release settlement","paid_components":[["signing_bonus",9]]})");
        auto seller_cash=franchise::parse_frame(R"({"obligation_id":"contract:v","player_id":"v","amount":9,"paid":9,"source":"synthetic assigned paid history","paid_components":[["signing_bonus",9]]})");
        auto buyer_cash=franchise::parse_frame(R"({"obligation_id":"contract:v","player_id":"v","amount":60,"paid":0,"source":"synthetic assigned bases","paid_components":[]})");
        auto compact_release=release_reply,compact_trade=trade_reply,compact_restructure=restructure_reply;
        compact_release["result"]["release"]["financial"]["released_contracts"]["v"]["cash_obligation"]=released_cash;
        auto original_cash=released_cash;original_cash["amount"]=69;original_cash["source"]="synthetic original cash";
        compact_release["result"]["release"]["financial"]["released_contracts"]["v"]["original_cash"]=original_cash;
        for (const auto& team : {std::string("a"),std::string("b")}) {
            auto& archive=compact_trade["result"]["trade"][team]["financial"][team=="a" ? "outgoing_trades" : "incoming_trades"]["v"];
            archive["seller_cash"]=seller_cash;archive["buyer_cash"]=buyer_cash;
            archive["original_cash"]=original_cash;
        }
        auto summarize=[](nlohmann::json& cash,const nlohmann::json& target) {
            const auto nominal=target.at("amount").get<int64_t>(),paid=target.at("paid").get<int64_t>();
            cash={{"revision",1},{"nominal_total",nominal+11},{"paid_total",paid+3},{"unpaid_total",nominal-paid+8},
                {"obligations",nlohmann::json::array({target})},
                {"other_obligations",{{"count",1},{"nominal_total",11},{"paid_total",3},{"unpaid_total",8}}}};
        };
        summarize(compact_release["result"]["release"]["cash"],released_cash);
        summarize(compact_trade["result"]["trade"]["a"]["cash"],seller_cash);
        summarize(compact_trade["result"]["trade"]["b"]["cash"],buyer_cash);
        summarize(compact_restructure["result"]["restructure"]["cash"],restructure_archive["cash_obligation"]);
        for (const auto& operation : {std::string("manual_release"),std::string("manual_trade"),std::string("manual_restructure")}) {
            auto compact=operation=="manual_release" ? compact_release : operation=="manual_trade" ? compact_trade : compact_restructure;
            auto submitted=operation=="manual_release" ? release_request : operation=="manual_trade" ? trade_request : restructure_request;
            submitted["receipt_format"]="target_v1";compact["result"]["receipt_format"]="target_v1";
            franchise::validate_result(compact,submitted);
            for (int scenario=0;scenario<16;++scenario) {
                auto bad=compact,bad_request=submitted;
                auto& posted=operation=="manual_release" ? bad["result"]["release"] :
                    operation=="manual_trade" ? bad["result"]["trade"]["a"] : bad["result"]["restructure"];
                auto& cash=posted["cash"];
                auto& financial=posted["financial"];
                const auto map=operation=="manual_release" ? "released_contracts" : operation=="manual_trade" ? "outgoing_trades" : "restructures";
                if (scenario==0) bad["result"].erase("receipt_format");
                if (scenario==1) bad_request.erase("receipt_format");
                if (scenario==2) bad["result"]["receipt_format"]="target_v2";
                if (scenario==3) cash["other_obligations"].erase("count");
                if (scenario==4) cash["other_obligations"]["count"]=true;
                if (scenario==5) cash["other_obligations"]["count"]=0;
                if (scenario==6) cash["other_obligations"]["unpaid_total"]=7;
                if (scenario==7) cash["nominal_total"]=0;
                if (scenario==8) cash["obligations"][0]["source"]="changed from archive";
                if (scenario==9) cash["obligations"].push_back(cash["obligations"][0]);
                if (scenario==10) financial[map]["other-player"]=financial[map]["v"];
                if (scenario==11) financial["cap"]=100;
                if (scenario==12) {
                    cash["other_obligations"]={{"count",1},{"nominal_total",std::numeric_limits<int64_t>::max()},
                        {"paid_total",0},{"unpaid_total",std::numeric_limits<int64_t>::max()}};
                    cash["nominal_total"]=std::numeric_limits<int64_t>::max();
                    cash["paid_total"]=cash["obligations"][0]["paid"];
                    cash["unpaid_total"]=std::numeric_limits<int64_t>::max()-cash["paid_total"].get<int64_t>();
                }
                if (scenario==13) {bad_request.erase("receipt_format");bad["result"].erase("receipt_format");}
                if (scenario==14) cash["other_obligations"]["count"]=std::numeric_limits<uint64_t>::max();
                if (scenario==15) cash["revision"]=true;
                bool rejected=false;
                try { franchise::validate_result(bad,bad_request); } catch (const std::exception&) { rejected=true; }
                if (!rejected) throw std::runtime_error("Invalid compact receipt accepted: "+operation+"/"+std::to_string(scenario));
            }
        }
        auto returned_release=compact_release, returned_request=release_request;
        returned_release["result"]["receipt_format"]="target_v1";returned_request["receipt_format"]="target_v1";
        auto& returned_archive=returned_release["result"]["release"]["financial"]["released_contracts"]["v"];
        const auto returned_cash_id="contract-gen:"+std::string(64,'d');
        returned_archive["original_cash"]["obligation_id"]=returned_cash_id;
        returned_archive["cash_obligation"]["obligation_id"]=returned_cash_id;
        returned_release["result"]["release"]["cash"]["obligations"][0]["obligation_id"]=returned_cash_id;
        franchise::validate_result(returned_release,returned_request);
        for (const auto& operation : {std::string("manual_release"),std::string("manual_trade")}) {
            auto base=operation=="manual_release" ? compact_release : compact_trade;
            auto input=operation=="manual_release" ? release_request : trade_request;
            input["receipt_format"]="target_v1";base["result"]["receipt_format"]="target_v1";
            for (int scenario=0;scenario<8;++scenario) {
                auto bad=base;
                if (operation=="manual_release") {
                    auto& archive=bad["result"]["release"]["financial"]["released_contracts"]["v"];
                    auto& target=archive["cash_obligation"];
                    if (scenario==0) {target["obligation_id"]="foreign";archive["original_cash"]["obligation_id"]="foreign";}
                    if (scenario==1) target["obligation_id"]=returned_cash_id;
                    if (scenario==2) archive["original_cash"]["player_id"]="other";
                    if (scenario==3) {target["paid"]=8;target["paid_components"]={{"signing_bonus",8}};}
                    if (scenario==4) target["paid_components"]={{"base:0",9}};
                    if (scenario==5) {archive["original_cash"]["paid"]=8;archive["original_cash"]["paid_components"]={{"signing_bonus",8}};}
                    if (scenario==6) target["amount"]=70;
                    if (scenario==7) archive["original_cash"].erase("paid_components");
                    summarize(bad["result"]["release"]["cash"],target);
                } else {
                    auto archive=bad["result"]["trade"]["a"]["financial"]["outgoing_trades"]["v"];
                    if (scenario==0) for (const auto* key : {"original_cash","seller_cash","buyer_cash"}) archive[key]["obligation_id"]="foreign";
                    if (scenario==1) archive["original_cash"]["obligation_id"]=returned_cash_id;
                    if (scenario==2) archive["buyer_cash"]["amount"]=61;
                    if (scenario==3) {
                        archive["seller_cash"]["amount"]=8;archive["seller_cash"]["paid"]=8;
                        archive["seller_cash"]["paid_components"]={{"signing_bonus",8}};archive["buyer_cash"]["amount"]=61;
                    }
                    if (scenario==4) archive["seller_cash"]["paid_components"]={{"base:0",9}};
                    if (scenario==5) {archive["original_cash"]["paid"]=8;archive["original_cash"]["paid_components"]={{"signing_bonus",8}};}
                    if (scenario==6) {archive["buyer_cash"]["paid"]=1;archive["buyer_cash"]["paid_components"]={{"base:0",1}};}
                    if (scenario==7) archive["original_cash"].erase("paid_components");
                    for (const auto& team : {std::string("a"),std::string("b")}) {
                        bad["result"]["trade"][team]["financial"][team=="a" ? "outgoing_trades" : "incoming_trades"]["v"]=archive;
                        summarize(bad["result"]["trade"][team]["cash"],archive[team=="a" ? "seller_cash" : "buyer_cash"]);
                    }
                }
                bool rejected=false;
                try { franchise::validate_result(bad,input); } catch (const std::exception&) { rejected=true; }
                if (!rejected) throw std::runtime_error("Invalid compact cash provenance accepted: "+operation+"/"+std::to_string(scenario));
            }
        }
        auto generational_trade_request=trade_request, generational_trade_reply=trade_reply;
        const auto from_id="contract-gen:"+std::string(64,'e'), to_id="contract-gen:"+std::string(64,'f');
        generational_trade_request["seller_generation_id"]=from_id;
        generational_trade_request["buyer_previous_generation_id"]=nullptr;
        generational_trade_reply["result"]["seller_generation_id"]=from_id;
        generational_trade_reply["result"]["buyer_previous_generation_id"]=nullptr;
        generational_trade_reply["result"]["buyer_generation_id"]=to_id;
        auto linked_archive=assignment_archive;
        linked_archive["original_cash"]={{"obligation_id",from_id},{"player_id","v"},{"amount",69},{"paid",9},{"source","fixture"},{"paid_components",nlohmann::json::array({nlohmann::json::array({"signing_bonus",9})})}};
        linked_archive["seller_cash"]=linked_archive["original_cash"];linked_archive["seller_cash"]["amount"]=9;
        linked_archive["buyer_cash"]={{"obligation_id",to_id},{"player_id","v"},{"amount",60},{"paid",0},{"source","fixture"},{"paid_components",nlohmann::json::array()}};
        generational_trade_reply["result"]["trade"]["a"]["financial"]["outgoing_trades"]["v"]=linked_archive;
        generational_trade_reply["result"]["trade"]["b"]["financial"]["incoming_trades"]["v"]=linked_archive;
        franchise::validate_result(generational_trade_reply,generational_trade_request);
        auto calendar_trade_write_request=generational_trade_request,calendar_trade_write_reply=generational_trade_reply;
        calendar_trade_write_request["calendar_format"]="calendar_v1";
        calendar_trade_write_request["scope"]["league_year"]=2027;
        auto& calendar_trade_result=calendar_trade_write_reply["result"];
        calendar_trade_result["calendar_format"]="calendar_v1";calendar_trade_result["format"]=2;
        calendar_trade_result["league_year"]=2027;
        auto calendar_trade_archive=linked_archive;
        calendar_trade_archive["scope"]=calendar_trade_write_request["scope"];
        calendar_trade_archive["original_contract"]["source"]="synthetic original";
        calendar_trade_archive["original_contract"]["elapsed_years"]=0;
        calendar_trade_archive["original_contract"]["bonus_years"]=3;
        auto transferred_offer=calendar_trade_archive["original_contract"]["offer"];
        transferred_offer["signing_bonus"]=0;
        calendar_trade_archive["buyer_contract"]={{"offer",transferred_offer},{"source","synthetic transferred"},
            {"elapsed_years",0},{"bonus_years",3}};
        calendar_trade_archive["assigned_base"]=60;
        calendar_trade_archive["retained_bonus"]={{"record_id","synthetic:seller-bonus"},{"annual_charges",{9}},
            {"source","synthetic acceleration"}};
        calendar_trade_result["trade"]["a"]["financial"]["outgoing_trades"]["v"]=calendar_trade_archive;
        calendar_trade_result["trade"]["b"]["financial"]["incoming_trades"]["v"]=calendar_trade_archive;
        calendar_trade_result["trade"]["a"]["cash"]["revision"]=1;
        calendar_trade_result["trade"]["a"]["cash"]["source"]="synthetic cash coverage";
        calendar_trade_result["trade"]["b"]["cash"]["revision"]=1;
        calendar_trade_result["trade"]["b"]["cash"]["source"]="synthetic cash coverage";
        calendar_trade_result["trade"]["a"]["cash"]["obligations"]=nlohmann::json::array({calendar_trade_archive["seller_cash"]});
        calendar_trade_result["trade"]["b"]["cash"]["obligations"]=nlohmann::json::array({calendar_trade_archive["buyer_cash"]});
        franchise::validate_result(calendar_trade_write_reply,calendar_trade_write_request);
        auto calendar_trade_compact=calendar_trade_write_reply,calendar_trade_compact_request=calendar_trade_write_request;
        calendar_trade_compact_request["receipt_format"]="target_v1";
        calendar_trade_compact["result"]["receipt_format"]="target_v1";
        for(const auto& club:{"a","b"}) calendar_trade_compact["result"]["trade"][club]["cash"]["other_obligations"]=
            {{"count",0},{"nominal_total",0},{"paid_total",0},{"unpaid_total",0}};
        for(const auto& club:{"a","b"}) calendar_trade_compact["result"]["trade"][club]["cash"].erase("source");
        franchise::validate_result(calendar_trade_compact,calendar_trade_compact_request);
        for(int scenario=0;scenario<8;++scenario) {
            auto bad=calendar_trade_write_reply;auto& result=bad["result"];
            if(scenario==0) result["format"]=true;
            if(scenario==1) result["league_year"]=2026;
            if(scenario==2) result["trade"]["b"]["cash"]["obligations"]=nlohmann::json::array();
            if(scenario==3) result["trade"]["b"]["cash"]["obligations"][0]["source"]="changed";
            if(scenario==4) {
                result["trade"]["a"]["financial"]["outgoing_trades"]["v"]["buyer_contract"]["elapsed_years"]=1;
                result["trade"]["b"]["financial"]["incoming_trades"]["v"]["buyer_contract"]["elapsed_years"]=1;
            }
            if(scenario==5) result.erase("calendar_format");
            if(scenario==6) result["unexpected"]=0;
            if(scenario==7) result["trade"]["b"]["cash"]["revision"]=true;
            bool rejected=false;
            try{franchise::validate_result(bad,calendar_trade_write_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt calendar trade write receipt accepted");
        }
        for (int scenario=0;scenario<7;++scenario) {
            auto bad=generational_trade_reply,input=generational_trade_request;
            if (scenario==0) bad["result"]["seller_generation_id"]=to_id;
            if (scenario==1) bad["result"]["buyer_previous_generation_id"]=true;
            if (scenario==2) bad["result"]["buyer_generation_id"]=nullptr;
            if (scenario==3) bad["result"]["trade"]["b"]["financial"]["incoming_trades"]["v"]["buyer_cash"]["obligation_id"]=from_id;
            if (scenario==4) input.erase("seller_generation_id");
            if (scenario==5) bad["result"]["trade"]["a"]["financial"]["outgoing_trades"]["v"]["original_cash"]["paid"]=true;
            if (scenario==6) input["seller_generation_id"]=nullptr;
            bool rejected=false;
            try { franchise::validate_result(bad,input); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Versioned trade agreement substitution accepted");
        }
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
        auto circumstance_request=player_request; circumstance_request["team_id"]="a";
        auto circumstance_reply=player_reply;
        auto circumstances=franchise::parse_frame(R"({"player_id":"v","team_id":"a","window":"season","mode":"cpu_played","total_games":16,"available_games":12,"injury_unavailable_games":4,"coaching_dnp_games":2,"source":"synthetic report","coverage":"full season","complete_window":true,"unavailable_reason":null})");
        circumstance_reply["result"]["promise_history"]={{{"player_id","v"},{"score",{{"goals",{{{"window","season"}}}}}},{"circumstances",{circumstances}}}};
        franchise::validate_result(circumstance_reply,circumstance_request);
        auto unknown_circumstance=circumstance_reply;
        unknown_circumstance["result"]["promise_history"][0]["circumstances"][0]["available_games"]=nullptr;
        unknown_circumstance["result"]["promise_history"][0]["circumstances"][0]["unavailable_reason"]="Collector unavailable";
        franchise::validate_result(unknown_circumstance,circumstance_request);
        for (int scenario=0;scenario<18;++scenario) {
            auto bad=circumstance_reply; auto req=circumstance_request;
            auto& history=bad["result"]["promise_history"][0]; auto& row=history["circumstances"][0];
            if (scenario==0) row["player_id"]="other";
            if (scenario==1) row["team_id"]="other";
            if (scenario==2) row["window"]="other";
            if (scenario==3) row["mode"]="invented";
            if (scenario==4) row["total_games"]=true;
            if (scenario==5) row["available_games"]=-1;
            if (scenario==6) row["available_games"]=17;
            if (scenario==7) row["injury_unavailable_games"]=5;
            if (scenario==8) row["coaching_dnp_games"]=13;
            if (scenario==9) row["available_games"]=nullptr;
            if (scenario==10) row["unavailable_reason"]="unexpected";
            if (scenario==11) row["source"]=" ";
            if (scenario==12) row["complete_window"]=1;
            if (scenario==13) history["circumstances"].push_back(row);
            if (scenario==14) row["unexpected"]=0;
            if (scenario==15) req.erase("team_id");
            if (scenario==16) history["player_id"]="other";
            if (scenario==17) { row["total_games"]=INT64_MAX;row["available_games"]=INT64_MAX;row["injury_unavailable_games"]=1; }
            bool rejected=false;
            try { franchise::validate_result(bad,req); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Corrupt promise circumstances accepted");
        }
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
        auto identified=accounting;
        identified["generation_id"]="legacy-contract:"+std::string(64,'a');
        player_reply["result"]["contract_accounting"]=identified;
        franchise::validate_result(player_reply,player_request);
        for (const auto& identity : nlohmann::json::array({nullptr,true,4,"","legacy-contract:abc",
                "legacy-contract:"+std::string(64,'A'),"legacy-contract:"+std::string(64,'g')})) {
            auto bad=player_reply;
            bad["result"]["contract_accounting"]["generation_id"]=identity;
            bool rejected=false;
            try { franchise::validate_result(bad,player_request); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Invalid agreement identity accepted");
        }
        auto returned=identified;
        returned["generation_id"]="contract-gen:"+std::string(64,'b');
        returned["cash_obligation"]["obligation_id"]=returned["generation_id"];
        player_reply["result"]["contract_accounting"]=returned;
        franchise::validate_result(player_reply,player_request);
        auto mismatched=player_reply;
        mismatched["result"]["contract_accounting"]["cash_obligation"]["obligation_id"]="contract:v";
        bool mismatch_rejected=false;
        try { franchise::validate_result(mismatched,player_request); } catch (const std::exception&) { mismatch_rejected=true; }
        if (!mismatch_rejected) throw std::runtime_error("Return agreement used legacy cash identity");
        auto agreement_request=nlohmann::json{{"operation","contract_context"},{"team_id","a"},
            {"generation_id",identified["generation_id"]}};
        auto agreement_reply=nlohmann::json{{"error",nullptr},{"result",{{"team_id","a"},
            {"generation_id",identified["generation_id"]},{"financial_revision",3},{"accounting",identified}}}};
        franchise::validate_result(agreement_reply,agreement_request);
        for (int scenario=0;scenario<7;++scenario) {
            auto bad=agreement_reply;
            if (scenario==0) bad["result"]["team_id"]="other";
            if (scenario==1) bad["result"]["generation_id"]="legacy-contract:"+std::string(64,'b');
            if (scenario==2) bad["result"]["accounting"]=nullptr;
            if (scenario==3) bad["result"]["financial_revision"]=true;
            if (scenario==4) bad["result"]["accounting"]["generation_id"]="legacy-contract:"+std::string(64,'b');
            if (scenario==5) bad["result"]["extra"]=1;
            if (scenario==6) bad["result"]["accounting"].erase("generation_id");
            bool rejected=false;
            try { franchise::validate_result(bad,agreement_request); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Invalid requested agreement context accepted");
        }
        auto calendar_request=agreement_request; calendar_request["context_format"]="calendar_v1";
        auto current_contract=identified["contract"]; current_contract["elapsed_years"]=2;
        auto calendar_reply=nlohmann::json{{"error",nullptr},{"result",{{"format",2},{"team_id","a"},
            {"generation_id",identified["generation_id"]},{"financial_revision",4},{"league_year",2027},
            {"economic_archive",identified},{"calendar_accounting",{{"status","active"},
                {"current_contract",current_contract},{"annual_charges",{37}},
                {"ownership_current",true},{"expiry_source",nullptr},{"anchor_year",2026}}}}}};
        franchise::validate_result(calendar_reply,calendar_request);
        auto calendar_release_request=calendar_request;calendar_release_request["context_format"]="calendar_v2";
        auto calendar_release_reply=calendar_reply;
        auto& release_context=calendar_release_reply["result"];
        release_context["format"]=3;
        release_context["release_calendar"]={{"league_year",2027},{"elapsed_years",1},{"source","synthetic release"}};
        auto& released_archive=release_context["economic_archive"];
        released_archive["status"]="released";released_archive["charge_scope"]="retained_obligations";
        released_archive["contract"]={{"offer",{{"player_id","v"},{"salaries",{10,20,30}},
            {"signing_bonus",9},{"guaranteed_salaries",{0,0,5}}}},
            {"source","synthetic"},{"elapsed_years",0},{"bonus_years",3}};
        released_archive["annual_charges"]={3,8};
        released_archive["cash_obligation"]={{"obligation_id","contract:v"},{"player_id","v"},
            {"amount",24},{"paid",19},{"source","synthetic allocated"},
            {"paid_components",nlohmann::json::array({nlohmann::json::array({"signing_bonus",9}),
                nlohmann::json::array({"base:0",10})})}};
        released_archive["guarantees"]={{"unpaid_guaranteed_base_by_original_year",{0,0,5}},
            {"unpaid_signing_bonus",0},{"obligation_source","synthetic"}};
        release_context["calendar_accounting"]={{"status","released"},{"anchor_year",2027},
            {"current_contract",nullptr},{"annual_charges",{3,8}},
            {"ownership_current",false},{"expiry_source",nullptr}};
        franchise::validate_result(calendar_release_reply,calendar_release_request);
        auto calendar_write_request=release_request;
        calendar_write_request["calendar_format"]="calendar_v1";
        calendar_write_request["generation_id"]=identified["generation_id"];
        calendar_write_request["scope"]["league_year"]=2027;
        auto calendar_write_reply=release_reply;
        auto& write_receipt=calendar_write_reply["result"]["release"];
        write_receipt["format"]=2;write_receipt["generation_id"]=identified["generation_id"];
        write_receipt["league_year"]=2027;
        auto& write_archive=write_receipt["financial"]["released_contracts"]["v"];
        write_archive["original_contract"]=released_archive["contract"];
        write_archive["original_contract"]["elapsed_years"]=1;
        write_archive["scope"]=calendar_write_request["scope"];
        std::sort(write_archive["scope"]["exclusions"].begin(),write_archive["scope"]["exclusions"].end());
        write_archive["cash_obligation"]=released_archive["cash_obligation"];
        write_archive["original_cash"]=released_archive["cash_obligation"];
        write_archive["original_cash"]["amount"]=69;
        write_receipt["cash"]={{"revision",1},{"source","synthetic cash coverage"},{"nominal_total",24},{"paid_total",19},{"unpaid_total",5},
            {"obligations",nlohmann::json::array({write_archive["cash_obligation"]})}};
        franchise::validate_result(calendar_write_reply,calendar_write_request);
        auto calendar_compact_request=calendar_write_request,calendar_compact_reply=calendar_write_reply;
        calendar_compact_request["receipt_format"]="target_v1";
        calendar_compact_reply["result"]["receipt_format"]="target_v1";
        calendar_compact_reply["result"]["release"]["cash"].erase("source");
        calendar_compact_reply["result"]["release"]["cash"]["other_obligations"]=
            {{"count",0},{"nominal_total",0},{"paid_total",0},{"unpaid_total",0}};
        franchise::validate_result(calendar_compact_reply,calendar_compact_request);
        for(int scenario=0;scenario<8;++scenario) {
            auto bad=calendar_write_reply;auto& receipt=bad["result"]["release"];
            if(scenario==0) receipt["format"]=true;
            if(scenario==1) receipt["generation_id"]="legacy-contract:"+std::string(64,'b');
            if(scenario==2) receipt["league_year"]=2026;
            if(scenario==3) receipt["cash"]["obligations"]=nlohmann::json::array();
            if(scenario==4) receipt["cash"]["obligations"][0]["source"]="changed";
            if(scenario==5) receipt["financial"]["released_contracts"]["v"]["original_contract"]["elapsed_years"]=0;
            if(scenario==6) receipt.erase("format");
            if(scenario==7) receipt["financial"]["released_contracts"]["v"]["cash_obligation"]["amount"]=25;
            bool rejected=false;
            try{franchise::validate_result(bad,calendar_write_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt calendar release write receipt accepted");
        }
        auto legacy_release=calendar_release_reply;
        legacy_release["result"]["release_calendar"]=nullptr;
        legacy_release["result"]["economic_archive"]["contract"]["elapsed_years"]=1;
        franchise::validate_result(legacy_release,calendar_release_request);
        auto active_v2=calendar_reply;active_v2["result"]["format"]=3;
        active_v2["result"]["release_calendar"]=nullptr;
        franchise::validate_result(active_v2,calendar_release_request);
        auto trade_context_request=calendar_release_request;trade_context_request["context_format"]="calendar_v3";
        auto trade_context_reply=calendar_release_reply;
        auto& trade_context=trade_context_reply["result"];
        trade_context["format"]=4;trade_context["release_calendar"]=nullptr;
        trade_context["trade_calendar"]={{"league_year",2027},{"elapsed_years",1},{"source","synthetic calendar trade"}};
        trade_context["economic_archive"]["status"]="assigned";
        trade_context["calendar_accounting"]["status"]="assigned";
        trade_context["economic_archive"]["annual_charges"]={3,3};
        trade_context["calendar_accounting"]["annual_charges"]={3,3};
        trade_context["economic_archive"]["cash_obligation"]["amount"]=19;
        trade_context["economic_archive"]["guarantees"]["unpaid_guaranteed_base_by_original_year"]={0,0,0};
        franchise::validate_result(trade_context_reply,trade_context_request);
        auto active_v3=active_v2;active_v3["result"]["format"]=4;active_v3["result"]["trade_calendar"]=nullptr;
        franchise::validate_result(active_v3,trade_context_request);
        for(int scenario=0;scenario<8;++scenario) {
            auto bad=trade_context_reply;auto& context=bad["result"];
            if(scenario==0) context["trade_calendar"]=nullptr;
            if(scenario==1) context["trade_calendar"]["elapsed_years"]=true;
            if(scenario==2) context["trade_calendar"]["league_year"]=2026;
            if(scenario==3) context["trade_calendar"]["source"]=" ";
            if(scenario==4) context["economic_archive"]["cash_obligation"]["amount"]=20;
            if(scenario==5) context["economic_archive"]["guarantees"]["unpaid_guaranteed_base_by_original_year"][2]=5;
            if(scenario==6) context["calendar_accounting"]["ownership_current"]=true;
            if(scenario==7) context["trade_calendar"].erase("elapsed_years");
            bool rejected=false;
            try{franchise::validate_result(bad,trade_context_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt calendar trade context accepted");
        }
        for(int scenario=0;scenario<11;++scenario) {
            auto bad=calendar_release_reply;auto& context=bad["result"];
            if(scenario==0) context["release_calendar"]=nullptr;
            if(scenario==1) context["release_calendar"]["elapsed_years"]=true;
            if(scenario==2) context["release_calendar"]["league_year"]=2026;
            if(scenario==3) context["release_calendar"]["source"]=" ";
            if(scenario==4) context["economic_archive"]["cash_obligation"]["amount"]=25;
            if(scenario==5) {
                context["economic_archive"]["cash_obligation"]["paid_components"][1][1]=9;
                context["economic_archive"]["cash_obligation"]["paid"]=18;
            }
            if(scenario==6) context["economic_archive"]["guarantees"]["unpaid_guaranteed_base_by_original_year"][2]=4;
            if(scenario==7) context["calendar_accounting"]["ownership_current"]=true;
            if(scenario==8) context["format"]=2;
            if(scenario==9) context["release_calendar"].erase("elapsed_years");
            if(scenario==10) context["calendar_accounting"]["annual_charges"]={8};
            bool rejected=false;
            try {franchise::validate_result(bad,calendar_release_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt calendar release context accepted");
        }
        bool release_downgrade=false;
        try {franchise::validate_result(calendar_release_reply,calendar_request);}catch(const std::exception&){release_downgrade=true;}
        if(!release_downgrade) throw std::runtime_error("Release format accepted for legacy request");
        auto calendar_player_request=player_request;
        calendar_player_request["context_format"]="calendar_v1";
        calendar_player_request["team_id"]="a";
        auto calendar_player_reply=player_reply;
        auto& profile=calendar_player_reply["result"];
        profile["context_format"]="calendar_v1";
        profile["contract_accounting"]=nullptr;
        profile["financial_revision"]=calendar_reply["result"]["financial_revision"];
        profile["calendar_contract_context"]=calendar_reply["result"];
        franchise::validate_result(calendar_player_reply,calendar_player_request);
        auto released_player_request=calendar_player_request;
        released_player_request["context_format"]="calendar_v2";
        auto released_player_reply=calendar_player_reply;
        released_player_reply["result"]["context_format"]="calendar_v2";
        released_player_reply["result"]["calendar_contract_context"]=release_context;
        franchise::validate_result(released_player_reply,released_player_request);
        auto trade_player_request=released_player_request;trade_player_request["context_format"]="calendar_v3";
        auto trade_player_reply=released_player_reply;trade_player_reply["result"]["context_format"]="calendar_v3";
        trade_player_reply["result"]["calendar_contract_context"]=trade_context;
        franchise::validate_result(trade_player_reply,trade_player_request);
        for (int scenario=0;scenario<8;++scenario) {
            auto bad=calendar_player_reply;
            if (scenario==0) bad["result"]["context_format"]="unknown";
            if (scenario==1) bad["result"]["contract_accounting"]=accounting;
            if (scenario==2) bad["result"]["calendar_contract_context"]["team_id"]="other";
            if (scenario==3) bad["result"]["financial_revision"]=99;
            if (scenario==4) bad["result"]["player_id"]="other";
            if (scenario==5) bad["result"]["calendar_contract_context"]["calendar_accounting"]["ownership_current"]=false;
            if (scenario==6) bad["result"].erase("calendar_contract_context");
            if (scenario==7) bad["result"]["calendar_contract_context"]["league_year"]=2031;
            bool rejected=false;
            try {franchise::validate_result(bad,calendar_player_request);}catch(const std::exception&){rejected=true;}
            if (!rejected) throw std::runtime_error("Corrupt calendar player context accepted");
        }
        profile["calendar_contract_context"]=nullptr;
        franchise::validate_result(calendar_player_reply,calendar_player_request);
        bool unrequested=false;
        try {franchise::validate_result(calendar_player_reply,player_request);}catch(const std::exception&){unrequested=true;}
        if (!unrequested) throw std::runtime_error("Unrequested calendar player format accepted");
        for (int scenario=0;scenario<15;++scenario) {
            auto bad=calendar_reply; auto req=calendar_request;auto& view=bad["result"]["calendar_accounting"];
            if (scenario==0) bad["result"]["format"]=true;
            if (scenario==1) bad["result"]["league_year"]=2025;
            if (scenario==2) view["anchor_year"]=true;
            if (scenario==3) view["current_contract"]["elapsed_years"]=1;
            if (scenario==4) view["current_contract"]["offer"]["salaries"][2]=99;
            if (scenario==5) view["ownership_current"]=false;
            if (scenario==6) view["annual_charges"]={19,37};
            if (scenario==7) view["expiry_source"]="invented";
            if (scenario==8) view["unexpected"]=0;
            if (scenario==9) req["context_format"]="invented";
            if (scenario==10) bad["result"]["economic_archive"]["generation_id"]="legacy-contract:"+std::string(64,'b');
            if (scenario==11) view["current_contract"]["source"]="changed";
            if (scenario==12) view["current_contract"]["bonus_layers"][0]["amount"]=9;
            if (scenario==13) view["current_contract"]=nullptr;
            if (scenario==14) bad["result"]["league_year"]=2031;
            bool rejected=false;
            try { franchise::validate_result(bad,req); } catch (const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Corrupt current calendar agreement accepted");
        }
        auto expired_reply=calendar_reply;auto& expired=expired_reply["result"];
        expired["league_year"]=2028;expired["calendar_accounting"]={{"status","expired"},
            {"current_contract",nullptr},{"annual_charges",nlohmann::json::array()},
            {"ownership_current",false},{"expiry_source","synthetic verified eligible close"},{"anchor_year",2026}};
        auto& paid_cash=expired["economic_archive"]["cash_obligation"];
        const auto& original_offer=expired["economic_archive"]["contract"]["offer"];
        auto components=nlohmann::json::array();
        components.push_back({"signing_bonus",original_offer["signing_bonus"]});
        for(size_t i=0;i<original_offer["salaries"].size();++i)
            components.push_back({"base:"+std::to_string(i),original_offer["salaries"][i]});
        for(const auto& layer:expired["economic_archive"]["contract"]["bonus_layers"])
            components.push_back({"bonus:"+layer["record_id"].get<std::string>(),layer["amount"]});
        paid_cash["paid_components"]=components;paid_cash["paid"]=paid_cash["amount"];
        expired["economic_archive"]["guarantees"]={{"unpaid_guaranteed_base_by_original_year",{0,0,0}},
            {"unpaid_signing_bonus",0},{"unpaid_original_signing_bonus",0},
            {"unpaid_bonus_layers",{{"bonus:restructure:conversion",0}}}};
        franchise::validate_result(expired_reply,calendar_request);
        for(int scenario=0;scenario<7;++scenario) {
            auto bad=expired_reply;auto& view=bad["result"]["calendar_accounting"];
            if(scenario==0) view["expiry_source"]=nullptr;
            if(scenario==1) view["expiry_source"]=" ";
            if(scenario==2) view["ownership_current"]=true;
            if(scenario==3) bad["result"]["league_year"]=2027;
            if(scenario==4) bad["result"]["economic_archive"]["cash_obligation"]["paid_components"]=nullptr;
            if(scenario==5) bad["result"]["economic_archive"]["cash_obligation"]=nullptr;
            if(scenario==6) view["current_contract"]=current_contract;
            bool rejected=false;
            try {franchise::validate_result(bad,calendar_request);} catch(const std::exception&) {rejected=true;}
            if(!rejected) throw std::runtime_error("Unsettled or corrupt calendar expiry accepted");
        }
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
        auto closed_calendar=calendar_reply;
        auto closed_archive=retained;closed_archive["generation_id"]=identified["generation_id"];
        closed_calendar["result"]["economic_archive"]=closed_archive;
        closed_calendar["result"]["calendar_accounting"]={{"status","released"},{"current_contract",nullptr},
            {"annual_charges",nlohmann::json::array()},{"ownership_current",false},
            {"expiry_source",nullptr},{"anchor_year",2026}};
        franchise::validate_result(closed_calendar,calendar_request);
        auto invalid_closed=closed_calendar;invalid_closed["result"]["calendar_accounting"]["status"]="expired";
        bool closed_rejected=false;
        try {franchise::validate_result(invalid_closed,calendar_request);}catch(const std::exception&){closed_rejected=true;}
        if(!closed_rejected) throw std::runtime_error("Released generation gained calendar expiry");
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
