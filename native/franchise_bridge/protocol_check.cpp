#include "contract_response.h"
#include "launch_options.h"
#include "signing_display.h"
#include "saved_signing.h"
#include <iostream>

int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string(argv[1])=="--guest-terms") {
            std::string line; size_t count=0;
            while(std::getline(std::cin,line)) {
                const auto sample=franchise::parse_frame(line);
                nlohmann::json actual=nullptr;
                try{actual=franchise::exact_guest_offer(sample.at("raw"),sample.at("player_id").get<std::string>(),
                    sample.value("contract_format",std::string("original_fxg_v1")));}
                catch(const std::exception&){}
                const auto& expected=sample.at("offer");
                if(expected.is_null()!=actual.is_null() || (!expected.is_null() && actual!=franchise::canonical_offer(expected)))
                    throw std::runtime_error("Native/Python guest salary schedule mismatch at case "+std::to_string(count));
                ++count;
            }
            if(!count) throw std::runtime_error("Empty guest terms corpus");
            std::cout<<"Native/Python guest terms matched "<<count<<" cases\n";
            return 0;
        }
        if(argc!=1) throw std::runtime_error("Unsupported protocol-check arguments");
        // A load-image hello must receive an exact bound echo before a local AI grant.
        nlohmann::json hello_request={{"operation","hello"},{"loaded_image_sha256",std::string(64,'a')}};
        nlohmann::json hello_reply={{"error",nullptr},{"result",{
            {"ai_enabled",true},{"operations",{"negotiate_proposal"}},
            {"runtime_binding",{{"loaded_image_sha256",std::string(64,'a')},{"franchise_id",std::string(32,'b')},
                {"bindings_sha256",std::string(64,'c')},{"snapshot_payload_sha256",std::string(64,'d')}}}}}};
        franchise::validate_result(hello_reply,hello_request);
        for(int scenario=0;scenario<7;++scenario) {
            auto bad=hello_reply;auto req=hello_request;
            if(scenario==0) bad["result"].erase("runtime_binding");
            if(scenario==1) bad["result"]["runtime_binding"]["loaded_image_sha256"]=std::string(64,'e');
            if(scenario==2) bad["result"]["runtime_binding"]["franchise_id"]="invalid";
            if(scenario==3) bad["result"]["runtime_binding"]["bindings_sha256"]=std::string(64,'G');
            if(scenario==4) bad["result"]["runtime_binding"]["snapshot_payload_sha256"]=false;
            if(scenario==5) bad["result"]["runtime_binding"]["write_authorized"]=true;
            if(scenario==6) req.erase("loaded_image_sha256");
            bool rejected=false;try{franchise::validate_result(bad,req);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Unbound runtime hello accepted");
        }
        auto binding_request=hello_request;binding_request["operation"]="bind_runtime";
        auto binding_reply=hello_reply;binding_reply["result"]["ai_enabled"]=false;
        binding_reply["result"]["operations"]=nlohmann::json::array({"signing_context"});
        franchise::validate_result(binding_reply,binding_request);
        for(int scenario=0;scenario<5;++scenario){
            auto bad=binding_reply;auto request=binding_request;
            if(scenario==0)bad["result"]["ai_enabled"]=true;
            if(scenario==1)bad["result"]["operations"].push_back("negotiate_proposal");
            if(scenario==2)bad["result"].erase("runtime_binding");
            if(scenario==3)bad["result"]["write_authorized"]=true;
            if(scenario==4)request.erase("loaded_image_sha256");
            bool rejected=false;try{franchise::validate_result(bad,request);}catch(const std::exception&){rejected=true;}
            if(!rejected)throw std::runtime_error("Observation binding granted excess authority");
        }
        const franchise::BudgetLaunch launch_budget{LR"(C:\budget path\ledger.sqlite)",L"scope \"quoted\" --provider offline-fixture",17};
        const auto budget_command=franchise::launch_command(L"python path",L"database path",franchise::ServiceMode::VertexRuntime,launch_budget);
        const auto expected_budget=franchise::quote(L"python path")+L" \"-m\" \"franchise.sidecar\" \"--database\" "+franchise::quote(L"database path")+
            L" \"--provider\" \"vertex\" \"--impersonate-runtime\" \"--ai-budget-database\" "+franchise::quote(launch_budget.database)+
            L" \"--ai-budget-scope\" "+franchise::quote(launch_budget.scope)+L" \"--ai-request-limit\" \"17\"";
        if(budget_command!=expected_budget || franchise::quote(L"a\"b\\")!=L"\"a\\\"b\\\\\"") throw std::runtime_error("Launch quoting changed");
        for(auto mode:{franchise::ServiceMode::OfflineFixture,franchise::ServiceMode::VertexRuntime})
            if(franchise::launch_command(L"python",L"db",mode).find(L"--ai-budget")!=std::wstring::npos)
                throw std::runtime_error("Implicit launch budget added");
        auto token_budget=launch_budget;token_budget.token_limit=110;
        if(franchise::launch_command(L"python path",L"database path",franchise::ServiceMode::VertexRuntime,token_budget)!=
            expected_budget+L" \"--ai-token-limit\" \"110\"" || budget_command.find(L"--ai-token-limit")!=std::wstring::npos)
            throw std::runtime_error("Token policy launch forwarding changed");
        for(auto value:{0ULL,~0ULL}) {
            token_budget.token_limit=value;bool rejected=false;
            try{franchise::launch_command(L"python",L"db",franchise::ServiceMode::VertexRuntime,token_budget);}
            catch(const std::invalid_argument&){rejected=true;}
            if(!rejected) throw std::runtime_error("Invalid cumulative token launch accepted");
        }
        token_budget.token_limit=static_cast<unsigned long long>(std::numeric_limits<long long>::max());
        if(franchise::launch_command(L"python",L"db",franchise::ServiceMode::VertexRuntime,token_budget).find(
            L" \"--ai-token-limit\" \"9223372036854775807\"")==std::wstring::npos)
            throw std::runtime_error("Maximum token policy was truncated");
        for(int scenario=0;scenario<7;++scenario) {
            auto budget=launch_budget;auto mode=franchise::ServiceMode::VertexRuntime;
            if(scenario==0) mode=franchise::ServiceMode::OfflineFixture;
            if(scenario==1) budget.database=L" ";
            if(scenario==2) budget.scope=L"";
            if(scenario==3) budget.request_limit=0;
            if(scenario==4) budget.request_limit=~0ULL;
            if(scenario==5) budget.scope=std::wstring(L"a\0b",3);
            if(scenario==6) budget.database=std::wstring(L"a\0b",3);
            bool rejected=false;try{franchise::launch_command(L"python",L"db",mode,budget);}catch(const std::invalid_argument&){rejected=true;}
            if(!rejected) throw std::runtime_error("Invalid runtime budget launch accepted");
        }
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
        auto proposal_request=request;
        proposal_request["operation"]="negotiate_proposal";
        proposal_request["expected_revision"]=0;
        auto proposal_reply=reply;
        proposal_reply["result"]["decision_mode"]="proposal";
        proposal_reply["result"]["outcome"]="accepted_proposal";
        proposal_reply["result"].erase("charges");
        proposal_reply["result"]["evidence"]={{"financial_revision",0}};
        proposal_reply["result"]["proposal_preview"]={{"revision",0},{"contract_charges",{10}},{"room_after",90}};
        franchise::validate_result(proposal_reply,proposal_request);
        for(const auto& guest_format:{"original_fxg_v1","softdrink_fxg_v1"}) {
        const auto scale=franchise::guest_money_scale(guest_format);
        auto guest_request=proposal_request,guest_reply=proposal_reply;
        guest_request["contract_format"]=guest_format;
        auto encoding=nlohmann::json{{"amount_word",829},{"flags_word",(1u<<29)|(2u<<16)|4u}};
        guest_request["offer"]=franchise::exact_guest_offer(encoding,"v",guest_format);
        guest_reply["result"]["offer"]=guest_request["offer"];
        guest_reply["result"]["contract_format"]=guest_format;
        guest_reply["result"]["guest_offer"]=encoding;
        guest_reply["result"]["guest_counter"]=nullptr;
        guest_reply["result"]["proposal_preview"]["contract_charges"]={4766000*scale,3523000*scale};
        franchise::validate_result(guest_reply,guest_request);
        auto counter_reply=guest_reply;
        counter_reply["result"]["action"]="counter";
        counter_reply["result"]["outcome"]="counteroffer";
        counter_reply["result"]["counter"]=guest_request["offer"];
        counter_reply["result"]["guest_counter"]=encoding;
        counter_reply["result"]["counter_validation"]={{"status","eligible"},{"preview",guest_reply["result"]["proposal_preview"]}};
        counter_reply["result"].erase("proposal_preview");
        franchise::validate_result(counter_reply,guest_request);
        auto unencoded=counter_reply;
        unencoded["result"]["guest_counter"]=nullptr;
        bool unencoded_rejected=false;
        try{franchise::validate_result(unencoded,guest_request);}catch(const std::exception&){unencoded_rejected=true;}
        if(!unencoded_rejected) throw std::runtime_error("Unencoded eligible guest counter accepted");
        unencoded["result"]["counter_validation"]={{"status","ineligible"},{"reason","Demand cannot encode"},{"revision",0}};
        franchise::validate_result(unencoded,guest_request);
        for(int scenario=0;scenario<6;++scenario) {
            auto bad=guest_reply;auto bad_request=guest_request;
            if(scenario==0) bad["result"]["guest_offer"]["amount_word"]=830;
            if(scenario==1) bad["result"]["guest_offer"]["flags_word"]=encoding["flags_word"].get<uint32_t>()|0x10u;
            if(scenario==2) bad["result"]["contract_format"]="other";
            if(scenario==3) bad["result"]["guest_counter"]=encoding;
            if(scenario==4) bad_request.erase("contract_format");
            if(scenario==5) bad["result"]["proposal_preview"]["contract_charges"]={4766001,3523000};
            bool rejected=false;
            try{franchise::validate_result(bad,bad_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Guest proposal encoding substitution accepted");
        }
        }
        for(int scenario=0;scenario<7;++scenario) {
            auto bad=proposal_reply;auto bad_request=proposal_request;
            if(scenario==0) bad["result"]["outcome"]="signed";
            if(scenario==1) bad["result"]["charges"]={10};
            if(scenario==2) bad["result"]["decision_mode"]="manual";
            if(scenario==3) bad["result"]["proposal_preview"]["revision"]=1;
            if(scenario==4) bad["result"]["evidence"]["financial_revision"]=1;
            if(scenario==5) bad["result"]["proposal_preview"]["contract_charges"]={10.5};
            if(scenario==6) bad_request["operation"]="negotiate";
            bool rejected=false;
            try{franchise::validate_result(bad,bad_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Proposal signing/mode/revision substitution accepted");
        }
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
        auto calendar_amendment_request=restructure_request,calendar_amendment_reply=restructure_reply;
        const auto opening_id="legacy-contract:"+std::string(64,'a');
        calendar_amendment_request["calendar_format"]="calendar_v1";
        calendar_amendment_request["generation_id"]=opening_id;
        calendar_amendment_request["scope"]["league_year"]=2027;
        calendar_amendment_reply["result"]["generation_id"]=opening_id;
        auto& calendar_amendment=calendar_amendment_reply["result"]["restructure"];
        calendar_amendment["format"]=2;calendar_amendment["generation_id"]=opening_id;calendar_amendment["league_year"]=2027;
        auto& calendar_amendment_archive=calendar_amendment["financial"]["restructures"]["v"];
        calendar_amendment_archive["scope"]["league_year"]=2027;
        calendar_amendment_archive["bonus_layer"]["record_id"]="calendar-restructure:conversion";
        calendar_amendment_archive["contract"]["bonus_layers"][0]["record_id"]="calendar-restructure:conversion";
        franchise::validate_result(calendar_amendment_reply,calendar_amendment_request);
        auto compact_calendar_request=calendar_amendment_request,compact_calendar_reply=calendar_amendment_reply;
        compact_calendar_request["receipt_format"]="target_v1";
        compact_calendar_reply["result"]["receipt_format"]="target_v1";
        compact_calendar_reply["result"]["restructure"]["cash"]["other_obligations"]=
            {{"count",0},{"nominal_total",0},{"paid_total",0},{"unpaid_total",0}};
        franchise::validate_result(compact_calendar_reply,compact_calendar_request);
        for(int scenario=0;scenario<11;++scenario) {
            auto bad=calendar_amendment_reply,input=calendar_amendment_request;
            auto& saved=bad["result"]["restructure"];
            if(scenario==0) input["calendar_format"]="invented";
            if(scenario==1) input.erase("generation_id");
            if(scenario==2) saved["format"]=true;
            if(scenario==3) saved["league_year"]=2026;
            if(scenario==4) saved["league_year"]=true;
            if(scenario==5) saved["generation_id"]="contract-gen:"+std::string(64,'b');
            if(scenario==6) saved["unexpected"]=0;
            if(scenario==7) input.erase("calendar_format");
            if(scenario==8) saved["financial"]["restructures"]["v"]["bonus_layer"]["record_id"]="restructure:conversion";
            if(scenario==9) saved["financial"]["restructures"]["v"]["scope"]["league_year"]=2026;
            if(scenario==10) input["scope"]["league_year"]=2031;
            bool rejected=false;
            try { franchise::validate_result(bad,input); } catch(const std::exception&) { rejected=true; }
            if(!rejected) throw std::runtime_error("Corrupt calendar amendment accepted");
        }
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
        // Captured from the actual two-year Python Store/Bridge fixture.
        // Values are synthetic fixture money, with first 2027 and second 2028.
        auto repeated_request=franchise::parse_frame(R"golden({"protocol":1,"request_id":"second-2028","operation":"manual_restructure","team_id":"a","player_id":"v","expected_revision":8,"timeout_ms":5000,"decision_mode":"manual","calendar_format":"calendar_v2","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"converted_base":200000})golden");
        auto repeated_history=franchise::parse_frame(R"golden({"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}})golden");
        auto repeated_financial=franchise::parse_frame(R"golden({"revision":9,"cap":20000000,"roster_reserve":0,"charges":[3050000],"signed_players":["v"],"rookie_year_one_remaining":"0","rookie_total_remaining":0,"rookie_tenders":{}})golden");
        repeated_financial["restructures"]={{"v",repeated_history["latest_restructure"]}};
        auto repeated_cash=franchise::parse_frame(R"golden({"revision":5,"source":"synthetic complete allocated cash","nominal_total":9000000,"paid_total":7000000,"unpaid_total":2000000})golden");
        repeated_cash["obligations"]=nlohmann::json::array({repeated_history["latest_restructure"]["cash_obligation"]});
        auto repeated_reply=nlohmann::json{{"error",nullptr},{"result",{{"team_id","a"},{"player_id","v"},
            {"decision_mode","manual"},{"generation_id",repeated_request["generation_id"]},
            {"restructure",{{"format",3},{"generation_id",repeated_request["generation_id"]},{"league_year",2028},
                {"financial",repeated_financial},{"cash",repeated_cash},{"amendment_history",repeated_history}}}}}};
        franchise::validate_result(repeated_reply,repeated_request);
        auto repeated_compact_request=repeated_request;repeated_compact_request["receipt_format"]="target_v1";
        auto repeated_compact_reply=repeated_reply;repeated_compact_reply["result"]["receipt_format"]="target_v1";
        repeated_compact_reply["result"]["restructure"]["financial"]=franchise::parse_frame(R"golden({"revision":9,"charges":[3050000],"signed_players":["v"]})golden");
        repeated_compact_reply["result"]["restructure"]["financial"]["restructures"]={{"v",repeated_history["latest_restructure"]}};
        repeated_compact_reply["result"]["restructure"]["cash"]=franchise::parse_frame(R"golden({"revision":5,"nominal_total":9000000,"paid_total":7000000,"unpaid_total":2000000,"other_obligations":{"count":0,"nominal_total":0,"paid_total":0,"unpaid_total":0}})golden");
        repeated_compact_reply["result"]["restructure"]["cash"]["obligations"]=nlohmann::json::array({repeated_history["latest_restructure"]["cash_obligation"]});
        franchise::validate_result(repeated_compact_reply,repeated_compact_request);
        for(int scenario=0;scenario<29;++scenario) {
            auto bad=repeated_reply;auto req=repeated_request;
            auto& receipt=bad["result"]["restructure"];auto& history=receipt["amendment_history"];
            auto& latest=history["latest_restructure"];auto& first=history["prior_restructures"][0];
            if(scenario==0) receipt["format"]=2;
            if(scenario==1) history["format"]=true;
            if(scenario==2) history["prior_restructures"]=nlohmann::json::array();
            if(scenario==3) first["scope"]["league_year"]=2028;
            if(scenario==4) latest["original_contract"]["elapsed_years"]=1;
            if(scenario==5) latest["contract"]["bonus_layers"].erase(0);
            if(scenario==6) latest["original_cash"]["amount"]=8000000;
            if(scenario==7) latest["original_cash"]["paid_components"][0][1]=0;
            if(scenario==8) latest["original_cash"]["source"]="forged predecessor";
            if(scenario==9) latest["cash_obligation"]["paid"]=0;
            if(scenario==10) latest["scope"]["exclusions"].erase(0);
            if(scenario==11) latest["scope"]["current_year_earned_base"]=false;
            if(scenario==12) latest["scope"]["healthy"]=1;
            if(scenario==13) latest["scope"]["amended_on"]="2028-02-30";
            if(scenario==14) latest["annual_minimums"]={2000000};
            if(scenario==15) latest["contract"]["offer"]["guaranteed_salaries"][0]=1;
            if(scenario==16) first["contract"]["source"]="changed first source";
            if(scenario==17) latest["bonus_layer"]["record_id"]=first["bonus_layer"]["record_id"];
            if(scenario==18) latest["bonus_layer"]["allocation_years"]=2;
            if(scenario==19) receipt["generation_id"]="legacy-contract:"+std::string(64,'f');
            if(scenario==20) receipt["league_year"]=2027;
            if(scenario==21) receipt["cash"]["nominal_total"]=9000000.0;
            if(scenario==22) receipt["cash"]["obligations"].push_back(receipt["cash"]["obligations"][0]);
            if(scenario==23) receipt["cash"]["obligations"][0]["extra"]=0;
            if(scenario==24) history["extra"]=0;
            if(scenario==25) req["calendar_format"]="calendar_v1";
            if(scenario==26) req["converted_base"]=199999;
            if(scenario==27) req["request_id"]="different";
            if(scenario==28) receipt["financial"]["signed_players"]=nlohmann::json::array();
            receipt["financial"]["restructures"]["v"]=latest;
            bool rejected=false;
            try {franchise::validate_result(bad,req);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt repeated calendar amendment accepted");
        }
        auto mismatched_history=repeated_reply;
        mismatched_history["result"]["restructure"]["amendment_history"]["latest_restructure"]["converted_base"]=1;
        bool history_rejected=false;
        try {franchise::validate_result(mismatched_history,repeated_request);}catch(const std::exception&){history_rejected=true;}
        if(!history_rejected) throw std::runtime_error("Repeated latest history did not bind archive");
        auto compact_bad=repeated_compact_reply;
        compact_bad["result"]["restructure"]["cash"]["other_obligations"]["paid_total"]=1;
        bool compact_rejected=false;
        try {franchise::validate_result(compact_bad,repeated_compact_request);}catch(const std::exception&){compact_rejected=true;}
        if(!compact_rejected) throw std::runtime_error("Repeated compact cash failed to reconcile");
        // Actual Python sidecar fixture: newest $200k bonus remains unpaid.
        auto layered_release_capture=franchise::parse_frame(R"releasegolden({"request":{"protocol":1,"request_id":"layered-release","operation":"manual_release","team_id":"a","player_id":"v","expected_revision":9,"timeout_ms":5000,"decision_mode":"manual","calendar_format":"calendar_v2","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","scope":{"league_year":2028,"removed_on":"2028-06-01","first_regular_season_game":"2028-09-10","exclusions":["additional_termination_pay","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","waiver_transfer"],"covered_guarantees":true,"healthy":true,"current_year_earned_base":0,"source":"synthetic healthy layered release"},"discount":{"league_year":2028,"annual_rate":0,"rate_source":"synthetic discount"},"payment_year_offsets":[0]},"reply":{"protocol":1,"request_id":"layered-release","result":{"decision_mode":"manual","player_id":"v","release":{"financial":{"revision":10,"cap":20000000,"roster_reserve":0,"charges":[3050000],"signed_players":[],"rookie_year_one_remaining":"0","rookie_total_remaining":0,"rookie_tenders":{},"released_contracts":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"removed_on":"2028-06-01","first_regular_season_game":"2028-09-10","exclusions":["additional_termination_pay","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","waiver_transfer"],"covered_guarantees":true,"healthy":true,"current_year_earned_base":0,"source":"synthetic healthy layered release"},"discount":{"league_year":2028,"annual_rate":0,"rate_source":"synthetic discount"},"payment_year_offsets":[0],"retained":[{"record_id":"calendar-layered-release:layered-release:bonus","annual_charges":[1250000],"source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf#article-13-section-6-b-ii; 2020-cba-article13-6bii-bonus-acceleration"},{"record_id":"calendar-layered-release:layered-release:base","annual_charges":[1800000],"source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf#article-13-section-6-d-iv; 2020-cba-article13-6div-covered-base-present-value"}],"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"cancelled_unearned_base":0}},"restructures":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}}},"cash":{"revision":6,"source":"synthetic complete allocated cash","obligations":[{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}],"nominal_total":9000000,"paid_total":7000000,"unpaid_total":2000000},"format":3,"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","league_year":2028,"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}}}},"error":null,"detail":null}})releasegolden");
        auto layered_release_request=layered_release_capture["request"];
        auto layered_release_reply=layered_release_capture["reply"];
        franchise::validate_result(layered_release_reply,layered_release_request);
        auto compact_release_request=layered_release_request;compact_release_request["receipt_format"]="target_v1";
        auto compact_release_reply=layered_release_reply;compact_release_reply["result"]["receipt_format"]="target_v1";
        compact_release_reply["result"]["release"]["financial"]=franchise::parse_frame(R"releasegolden({"revision":10,"charges":[3050000],"signed_players":[],"released_contracts":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"removed_on":"2028-06-01","first_regular_season_game":"2028-09-10","exclusions":["additional_termination_pay","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","waiver_transfer"],"covered_guarantees":true,"healthy":true,"current_year_earned_base":0,"source":"synthetic healthy layered release"},"discount":{"league_year":2028,"annual_rate":0,"rate_source":"synthetic discount"},"payment_year_offsets":[0],"retained":[{"record_id":"calendar-layered-release:layered-release:bonus","annual_charges":[1250000],"source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf#article-13-section-6-b-ii; 2020-cba-article13-6bii-bonus-acceleration"},{"record_id":"calendar-layered-release:layered-release:base","annual_charges":[1800000],"source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf#article-13-section-6-d-iv; 2020-cba-article13-6div-covered-base-present-value"}],"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"cancelled_unearned_base":0}}})releasegolden");
        compact_release_reply["result"]["release"]["cash"]=franchise::parse_frame(R"releasegolden({"revision":6,"nominal_total":9000000,"paid_total":7000000,"unpaid_total":2000000,"obligations":[{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}],"other_obligations":{"count":0,"nominal_total":0,"paid_total":0,"unpaid_total":0}})releasegolden");
        franchise::validate_result(compact_release_reply,compact_release_request);
        for(int scenario=0;scenario<24;++scenario) {
            auto bad=layered_release_reply;auto req=layered_release_request;
            auto& receipt=bad["result"]["release"];auto& history=receipt["amendment_history"];
            auto& archive=receipt["financial"]["released_contracts"]["v"];
            if(scenario==0) receipt["format"]=2;
            if(scenario==1) receipt["amendment_history"]=nullptr;
            if(scenario==2) history["prior_restructures"]=nlohmann::json::array();
            if(scenario==3) history["latest_restructure"]["contract"]["source"]="forged";
            if(scenario==4) archive["original_contract"]["elapsed_years"]=1;
            if(scenario==5) archive["original_contract"]["bonus_layers"].erase(0);
            if(scenario==6) archive["original_cash"]["amount"]=8000000;
            if(scenario==7) archive["original_cash"]["source"]="forged source";
            if(scenario==8) archive["original_cash"]["paid_components"][0][1]=0;
            if(scenario==9) archive["cash_obligation"]["paid_components"].push_back({"bonus:calendar-layered-restructure:second-2028",200000});
            if(scenario==10) archive["cash_obligation"]["amount"]=8800000;
            if(scenario==11) archive["retained"][0]["record_id"]="calendar-release:layered-release:bonus";
            if(scenario==12) archive["retained"][1]["record_id"]="foreign:base";
            if(scenario==13) archive["cancelled_unearned_base"]=1;
            if(scenario==14) req["calendar_format"]="calendar_v1";
            if(scenario==15) receipt["generation_id"]="legacy-contract:"+std::string(64,'f');
            if(scenario==16) receipt["league_year"]=2029;
            if(scenario==17) receipt["financial"]["signed_players"]=nlohmann::json::array({"v"});
            if(scenario==18) receipt["financial"]["charges"]=nlohmann::json::array();
            if(scenario==19) archive["retained"][0]["annual_charges"]=nlohmann::json::array();
            if(scenario==20) archive["retained"][0]["source"]=" ";
            if(scenario==21) history["prior_restructures"][0]["scope"]["league_year"]=2028;
            if(scenario==22) req["request_id"]="different-release";
            if(scenario==23) req["scope"]["removed_on"]="2028-05-01";
            bool rejected=false;
            try {franchise::validate_result(bad,req);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt layered calendar release accepted");
        }
        auto corrupt_compact_release=compact_release_reply;
        corrupt_compact_release["result"]["release"]["cash"]["other_obligations"]["paid_total"]=1;
        bool compact_release_rejected=false;
        try {franchise::validate_result(corrupt_compact_release,compact_release_request);}catch(const std::exception&){compact_release_rejected=true;}
        if(!compact_release_rejected) throw std::runtime_error("Layered release compact totals did not reconcile");
        // Actual Python Bridge: all seller bonuses paid, buyer receives bases
        // only. Runtime string chunks stay below MSVC literal-token limits.
        auto layered_trade_capture=franchise::parse_frame(std::string(R"tradegolden({"request":{"protocol":1,"request_id":"assignment","operation":"manual_trade","seller":"a","buyer":"b","player_id":"v","decision_mode":"manual","calendar_format":"calendar_v2","seller_generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","buyer_previous_generation_id":null,"seller_revision":10,"buyer_revision":4,"timeout_ms":5000,"scope":{"league_year":2028,"traded_on":"2028-07-01","seller_first_regular_season_game":"2028-09-10","buyer_first_regular_season_game":"2028-09-10","exclusions":["conditional_consideration","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","seller_retained_guarantees","unpaid_or_deferred_bonus","waiver_transfer"],"healthy":true,"current_year_earned_base":0,"assignment_consent":true,"transaction_eligible":true,"source":"synthetic layered assignment"}},"reply":{"protocol":1,"request_id":"assignment","result":{"decision_mode":"manual","player_id":"v","seller":"a","buyer":"b","trade":{"a":{"financial":{"revision":11,"cap":20000000,"roster_reserve":0,"charges":["2650000/3","2650000/3"],"signed_players":[],"rookie_year_one_remaining":"0","rookie_total_remaining":0,"rookie_tenders":{},"outgoing_trades":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"traded_on":"2028-07-01","seller_first_regular_season_game":"2028-09-10","buyer_first_regular_season_game":"2028-09-10","exclusions":["conditional_consideration","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","seller_retained_guarantees","unpaid_or_deferred_bonus","waiver_transfer"],"healthy":true,"current_year_earned_base":0,"assignment_consent":true,"transaction_eligible":true,"source":"synthetic layered assignment"},"retained_bonus":{"record_id":"calendar-layered-trade:assignment:seller-bonus","annual_charges":["2650000/3","2650000/3"],"source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf#article-13-section-6-b-ii; 2020-cba-article13-6bii-bonus-acceleration"},"seller_cash":{"obligation_id":"contract:v","player_id":"v","amount":7200000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"buyer_contract":{"offer":{"player_id":"v","salaries":[1800000,2000000],"signing_bonus":0,"guaranteed_salaries":[1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; original signing bonus remains with assigning club","elapsed_years":0,"bonus_years":5},"buyer_cash":{"obligation_id":)tradegolden")+R"tradegolden("contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","player_id":"v","amount":3800000,"paid":0,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; assigned remaining base","paid_components":[]},"assigned_base":3800000}},"restructures":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000,1435000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]}}}},"cash":{"revision":7,"source":"synthetic complete allocated cash","obligations":[{"obligation_id":"contract:v","player_id":"v","amount":7200000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]}],"nominal_total":7200000,"paid_total":7200000,"unpaid_total":0}},"b":{"financial":{"revision":5,"cap":20000000,"roster_reserve":0,"charges":[1800000,2000000],"signed_players":["v"],"rookie_year_one_remaining":"0","rookie_total_remaining":0,"rookie_tenders":{},"incoming_trades":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic )tradegolden"+R"tradegolden(second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"traded_on":"2028-07-01","seller_first_regular_season_game":"2028-09-10","buyer_first_regular_season_game":"2028-09-10","exclusions":["conditional_consideration","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","seller_retained_guarantees","unpaid_or_deferred_bonus","waiver_transfer"],"healthy":true,"current_year_earned_base":0,"assignment_consent":true,"transaction_eligible":true,"source":"synthetic layered assignment"},"retained_bonus":{"record_id":"calendar-layered-trade:assignment:seller-bonus","annual_charges":["2650000/3","2650000/3"],"source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf#article-13-section-6-b-ii; 2020-cba-article13-6bii-bonus-acceleration"},"seller_cash":{"obligation_id":"contract:v","player_id":"v","amount":7200000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"buyer_contract":{"offer":{"player_id":"v","salaries":[1800000,2000000],"signing_bonus":0,"guaranteed_salaries":[1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; original signing bonus remains with assigning club","elapsed_years":0,"bonus_years":5},"buyer_cash":{"obligation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","player_id":"v","amount":3800000,"paid":0,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; assigned remaining base","paid_components":[]},"assigned_base":3800000}}},"cash":{"revision":1,"source":"synthetic complete allocated cash","obligations":[{"obligation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","player_id":"v","amount":3800000,"paid":0,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; assigned remaining base","paid_components":[]}],"nominal_total":3800000,"paid_total":0,"unpaid_total":3800000}}},"seller_generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","buyer_generation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","buyer_previous_generation_id":null,"calendar_format":"calendar_v2","format":3,"league_year":2028,"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000,0]},"source":"synthetic original")tradegolden"+R"tradegolden(,"elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000,1435000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000,1435000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; b)tradegolden"+R"tradegolden(ase conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]}}}},"error":null,"detail":null}})tradegolden");
        auto layered_trade_request=layered_trade_capture["request"];
        auto layered_trade_reply=layered_trade_capture["reply"];
        franchise::validate_result(layered_trade_reply,layered_trade_request);
        auto layered_trade_compact_capture=franchise::parse_frame(std::string(R"tradegolden({"request":{"protocol":1,"request_id":"assignment","operation":"manual_trade","seller":"a","buyer":"b","player_id":"v","decision_mode":"manual","calendar_format":"calendar_v2","seller_generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","buyer_previous_generation_id":null,"seller_revision":10,"buyer_revision":4,"timeout_ms":5000,"scope":{"league_year":2028,"traded_on":"2028-07-01","seller_first_regular_season_game":"2028-09-10","buyer_first_regular_season_game":"2028-09-10","exclusions":["conditional_consideration","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","seller_retained_guarantees","unpaid_or_deferred_bonus","waiver_transfer"],"healthy":true,"current_year_earned_base":0,"assignment_consent":true,"transaction_eligible":true,"source":"synthetic layered assignment"},"receipt_format":"target_v1"},"reply":{"protocol":1,"request_id":"assignment","result":{"decision_mode":"manual","player_id":"v","seller":"a","buyer":"b","trade":{"a":{"financial":{"revision":11,"charges":["2650000/3","2650000/3"],"signed_players":[],"outgoing_trades":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"traded_on":"2028-07-01","seller_first_regular_season_game":"2028-09-10","buyer_first_regular_season_game":"2028-09-10","exclusions":["conditional_consideration","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","seller_retained_guarantees","unpaid_or_deferred_bonus","waiver_transfer"],"healthy":true,"current_year_earned_base":0,"assignment_consent":true,"transaction_eligible":true,"source":"synthetic layered assignment"},"retained_bonus":{"record_id":"calendar-layered-trade:assignment:seller-bonus","annual_charges":["2650000/3","2650000/3"],"source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf#article-13-section-6-b-ii; 2020-cba-article13-6bii-bonus-acceleration"},"seller_cash":{"obligation_id":"contract:v","player_id":"v","amount":7200000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"buyer_contract":{"offer":{"player_id":"v","salaries":[1800000,2000000],"signing_bonus":0,"guaranteed_salaries":[1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; original signing bonus remains with assigning club","elapsed_years":0,"bonus_years":5},"buyer_cash":{"obligation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","pla)tradegolden")+R"tradegolden(yer_id":"v","amount":3800000,"paid":0,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; assigned remaining base","paid_components":[]},"assigned_base":3800000}}},"cash":{"revision":7,"nominal_total":7200000,"paid_total":7200000,"unpaid_total":0,"obligations":[{"obligation_id":"contract:v","player_id":"v","amount":7200000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]}],"other_obligations":{"count":0,"nominal_total":0,"paid_total":0,"unpaid_total":0}}},"b":{"financial":{"revision":5,"charges":[1800000,2000000],"signed_players":["v"],"incoming_trades":{"v":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"traded_on":"2028-07-01","seller_first_regular_season_game":"2028-09-10","buyer_first_regular_season_game":"2028-09-10","exclusions":["conditional_consideration","early_june1_designation","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","seller_retained_guarantees","unpaid_or_deferred_bonus","waiver_transfer"],"healthy":true,"current_year_earned_base":0,"assignment_consent":true,"transaction_eligible":true,"source":"synthetic layered assignment"},"retained_bonus":{"record_id":"calendar-layered-trade:assignment:seller-bonus","annual_charges":["2650000/3","2650000/3"],"source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf#article-13-section-6-b-ii; 2020-cba-article13-6bii-bonus-acceleration"},"seller_cash":{"obligation_id":"contract:v","player_id":"v","amount":7200000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"buyer_contract":{"offer":{"player_id":"v","salaries":[1800000,2000000],"signing_bonus":0,"guaranteed_salaries":[1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; original signing bonus remains with assigning club","elapsed_years":0,"bonus_years":5},"buyer_cash":{"obligation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","player_id":"v","amount":3800000,"paid":0,"source":"synthetic paid original )tradegolden"+R"tradegolden(bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; assigned remaining base","paid_components":[]},"assigned_base":3800000}}},"cash":{"revision":1,"nominal_total":3800000,"paid_total":0,"unpaid_total":3800000,"obligations":[{"obligation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","player_id":"v","amount":3800000,"paid":0,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; assigned remaining base","paid_components":[]}],"other_obligations":{"count":0,"nominal_total":0,"paid_total":0,"unpaid_total":0}}}},"seller_generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","buyer_generation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","buyer_previous_generation_id":null,"calendar_format":"calendar_v2","format":3,"league_year":2028,"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000,0]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000,1435000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions)tradegolden"+R"tradegolden(":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000,1435000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]}}},"receipt_format":"target_v1"},"error":null,"detail":null}})tradegolden");
        franchise::validate_result(layered_trade_compact_capture["reply"],layered_trade_compact_capture["request"]);
        for(int scenario=0;scenario<26;++scenario) {
            auto bad=layered_trade_reply;auto req=layered_trade_request;
            auto& result=bad["result"];auto& history=result["amendment_history"];
            auto& archive=result["trade"]["a"]["financial"]["outgoing_trades"]["v"];
            if(scenario==0) result["format"]=2;
            if(scenario==1) history=nullptr;
            if(scenario==2) history["prior_restructures"]=nlohmann::json::array();
            if(scenario==3) history["latest_restructure"]["contract"]["source"]="forged";
            if(scenario==4) archive["original_contract"]["elapsed_years"]=1;
            if(scenario==5) archive["original_contract"]["bonus_layers"].erase(0);
            if(scenario==6) archive["original_cash"]["source"]="forged predecessor";
            if(scenario==7) archive["original_cash"]["amount"]=10999999;
            if(scenario==8) archive["seller_cash"]["amount"]=7000000;
            if(scenario==9) archive["original_cash"]["paid_components"].erase(archive["original_cash"]["paid_components"].size()-1);
            if(scenario==10) archive["retained_bonus"]["record_id"]="calendar-trade:assignment:seller-bonus";
            if(scenario==11) archive["retained_bonus"]["source"]=" ";
            if(scenario==12) archive["buyer_contract"]["bonus_layers"]=archive["original_contract"]["bonus_layers"];
            if(scenario==13) archive["buyer_contract"]["offer"]["signing_bonus"]=1;
            if(scenario==14) archive["buyer_contract"]["offer"]["guaranteed_salaries"][0]=0;
            if(scenario==15) archive["buyer_cash"]["obligation_id"]=result["seller_generation_id"];
            if(scenario==16) req["calendar_format"]="calendar_v1";
            if(scenario==17) result["calendar_format"]="calendar_v1";
            if(scenario==18) result["buyer_previous_generation_id"]=false;
            if(scenario==19) result["seller_generation_id"]="legacy-contract:"+std::string(64,'f');
            if(scenario==20) history["prior_restructures"][0]["scope"]["league_year"]=2028;
            if(scenario==21) result["trade"]["b"]["financial"]["signed_players"]=nlohmann::json::array();
            if(scenario==22) result["trade"]["a"]["financial"]["signed_players"]=nlohmann::json::array({"v"});
            if(scenario==23) req["request_id"]="different";
            if(scenario==24) {
                req["scope"]["traded_on"]="2028-05-01";archive["scope"]["traded_on"]="2028-05-01";
            }
            if(scenario==25) result["amendment_history"]["latest_restructure"]["cash_obligation"]["source"]="forged latest";
            result["trade"]["b"]["financial"]["incoming_trades"]["v"]=archive;
            bool rejected=false;
            try {franchise::validate_result(bad,req);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt history-aware calendar assignment accepted");
        }
        auto compact_trade_bad=layered_trade_compact_capture;
        compact_trade_bad["reply"]["result"]["trade"]["a"]["cash"]["other_obligations"]["paid_total"]=1;
        bool trade_compact_rejected=false;
        try {franchise::validate_result(compact_trade_bad["reply"],compact_trade_bad["request"]);}catch(const std::exception&){trade_compact_rejected=true;}
        if(!trade_compact_rejected) throw std::runtime_error("Layered assignment compact cash did not reconcile");
        auto player_request = franchise::parse_frame(R"({"operation":"player_context","player_id":"v"})");
        auto player_reply = franchise::parse_frame(R"({"error":null,"result":{"player_id":"v","financial_revision":0,"initialized":true,"personality":{},"relationships":{},"agreed_promises":[],"promise_history":[]}})");
        franchise::validate_result(player_reply, player_request);
        auto signing_request=franchise::parse_frame(R"({"operation":"signing_context","expected_revision":0,"observation":{"biography":{"source_slot":1},"team":{"table_mode":2,"table_index":0}}})");
        auto signing_player=player_reply["result"]; signing_player["player_id"]=std::string(32,'a');
        nlohmann::json signing_reply={{"error",nullptr},{"result",{{"player_id",std::string(32,'a')},
            {"team_id","49ers"},{"financial_revision",0},{"source_slot",1},{"saved_payload_sha256",std::string(64,'b')},
            {"player_context",signing_player},{"write_authorized",false},{"ai_authorized",false},
            {"scope","matching saved legacy checkpoint; active franchise selection, cash/rookie obligations and write authorization remain unverified"}}}};
        franchise::validate_result(signing_reply,signing_request);
        for (int scenario=0;scenario<9;++scenario) {
            auto bad=signing_reply;
            if (scenario==0) bad["result"]["write_authorized"]=true;
            if (scenario==1) bad["result"]["ai_authorized"]=true;
            if (scenario==2) bad["result"]["financial_revision"]=1;
            if (scenario==3) bad["result"]["source_slot"]=0;
            if (scenario==4) bad["result"]["player_context"]["player_id"]=std::string(32,'c');
            if (scenario==5) bad["result"]["team_id"]="Giants";
            if (scenario==6) bad["result"]["saved_payload_sha256"]="unknown";
            if (scenario==7) bad["result"]["player_context"]["initialized"]=false;
            if (scenario==8) bad["result"]["charges"]={10};
            bool rejected=false;
            try {franchise::validate_result(bad,signing_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt signing checkpoint accepted");
        }
        auto guest_request=signing_request;
        guest_request["guest_offer"]={{"amount_word",829},{"flags_word",0x20020004}};
        auto guest_reply=signing_reply;
        guest_reply["result"]["offer_context"]={{"amount_word",829},{"flags_word",0x20020004},
            {"outcome","eligible_preview"},{"reason",nullptr},
            {"offer",{{"player_id",std::string(32,'a')},{"salaries",{3108000,1865000}},{"signing_bonus",3316000}}},
            {"preview",{{"revision",0},{"contract_charges",{4766000,3523000}},{"room_after",5234000}}}};
        franchise::validate_result(guest_reply,guest_request);
        auto amendment_request=guest_request;
        amendment_request["observation"]["team"]["payroll_raw"]=4766;
        amendment_request["observation"]["team"]["league_cap_raw"]=10000;
        auto amendment_reply=guest_reply;
        const nlohmann::json legacy={{"player_id",std::string(32,'a')},{"amount_word",829},{"bonus_code",4},
            {"shape_code",1},{"original_years",2},{"remaining_years",2},{"source","authored imported schedule"}};
        auto& amendment_player=amendment_reply["result"]["player_context"];
        amendment_player["legacy_contract"]=legacy;amendment_player["contract_accounting"]=nullptr;
        amendment_player["legacy_liability_scope"]="original cap schedule; cash/protections/lifecycle unverified";
        auto& amended_terms=amendment_reply["result"]["offer_context"];
        amended_terms["outcome"]="amendment_comparison";amended_terms["preview"]=nullptr;
        amended_terms["amendment"]={{"revision",0},{"rule","legacy_bonus_carry_v1"},{"original_contract",legacy},
            {"cap",10000000},{"reserved_cap",0},{"annual_team_charges_before",{4766000,3523000}},
            {"current_charges",{4766000,3523000}},{"carried_bonus_charges",{1658000,1658000}},
            {"new_contract_charges",{4766000,3523000}},{"combined_player_charges",{6424000,5181000}},
            {"annual_team_charges_after",{6424000,5181000}},{"room_before",5234000},{"room_after",3576000},
            {"within_modeled_cap",true},{"requires_player_agreement",true},{"settlement_authorized",false}};
        franchise::validate_result(amendment_reply,amendment_request);
        for(int scenario=0;scenario<12;++scenario) {
            auto bad=amendment_reply;auto& terms=bad["result"]["offer_context"];auto& a=terms["amendment"];
            if(scenario==0)a["carried_bonus_charges"][0]=0;
            if(scenario==1)a["combined_player_charges"][0]=4766000;
            if(scenario==2)a["annual_team_charges_after"][0]=4766000;
            if(scenario==3)a["settlement_authorized"]=true;
            if(scenario==4)a["requires_player_agreement"]=false;
            if(scenario==5)a["original_contract"]["remaining_years"]=1;
            if(scenario==6)a["room_after"]=5234000;
            if(scenario==7)a["cap"]=20000000;
            if(scenario==8)a["within_modeled_cap"]=false;
            if(scenario==9)terms["outcome"]="eligible_preview";
            if(scenario==10)a["new_contract_charges"][0]=4765000;
            if(scenario==11)a["annual_team_charges_before"][0]=0;
            bool rejected=false;try{franchise::validate_result(bad,amendment_request);}catch(const std::exception&){rejected=true;}
            if(!rejected)throw std::runtime_error("Corrupt amendment comparison accepted");
        }
        auto rejected_guest=guest_reply;
        rejected_guest["result"]["offer_context"]["outcome"]="accounting_rejected";
        rejected_guest["result"]["offer_context"]["preview"]=nullptr;
        rejected_guest["result"]["offer_context"]["reason"]="Minimum classification missing";
        franchise::validate_result(rejected_guest,guest_request);
        rejected_guest["result"]["offer_context"]["outcome"]="format_rejected";
        rejected_guest["result"]["offer_context"]["offer"]=nullptr;
        auto unsupported_guest_request=guest_request;
        unsupported_guest_request["guest_offer"]={{"amount_word",1949},{"flags_word",0x4D060004}};
        rejected_guest["result"]["offer_context"]["amount_word"]=1949;
        rejected_guest["result"]["offer_context"]["flags_word"]=0x4D060004;
        franchise::validate_result(rejected_guest,unsupported_guest_request);
        for(int scenario=0;scenario<10;++scenario) {
            auto bad=guest_reply;
            auto& terms=bad["result"]["offer_context"];
            if(scenario==0) terms["outcome"]="signed";
            if(scenario==1) terms["amount_word"]=828;
            if(scenario==2) terms["offer"]["player_id"]=std::string(32,'c');
            if(scenario==3) terms["offer"]["signing_bonus"]=3315000;
            if(scenario==4) terms["offer"]["guaranteed_salaries"]={1,0};
            if(scenario==5) terms["preview"]["revision"]=1;
            if(scenario==6) terms["outcome"]="format_rejected";
            if(scenario==7) terms["offer"]["salaries"][0]=3107000;
            if(scenario==8) terms["preview"]["contract_charges"][0]=4765000;
            if(scenario==9) {terms["outcome"]="format_rejected";terms["offer"]=nullptr;terms["preview"]=nullptr;terms["reason"]="False format rejection";}
            bool rejected=false;
            try{franchise::validate_result(bad,guest_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt guest offer preview accepted");
        }
        auto performance_request=signing_request;
        performance_request["performance_format"]="saved_history_v1";
        performance_request["observation"]["calendar"]["display_year"]=2004;
        auto performance_reply=signing_reply;
        const auto history_source="original-fxg:"+std::string(64,'b')+":slot:1";
        auto history=franchise::parse_frame(R"({"metric":"completions","unit":"count","value":478,"period_code_raw":1,"mode_code_raw":0,"candidate_calendar_year":2003})");
        history["source"]=history_source+":entry:0";
        auto sacks=history;
        sacks["metric"]="sacks"; sacks["unit"]="sacks"; sacks["value"]=2.5;
        sacks["raw_half_sack_units"]=5; sacks["source"]=history_source+":entry:1";
        sacks["mapping_scope"]="historical sack mapping inferred from descriptor and Gildon NFL corroboration; live updates/coverage unverified";
        performance_reply["result"]["performance_context"]={{"player_id",std::string(32,'a')},{"source",history_source},
            {"saved_display_year",2004},{"history_present",true},{"saved_history",{history,sacks}},
            {"excluded_entries",{{"deleted",0},{"unknown_bit30",0},{"unmapped_code",0},{"negative_count",0}}},
            {"missing_named_metrics",{"games","rush_attempts","rushing_yards","rushing_touchdowns","pass_attempts","passing_yards","passing_touchdowns","interceptions_thrown","receptions","receiving_yards","receiving_touchdowns"}},
            {"unmapped_requested_metrics",{"tackles","targets","pressures","qb_hits"}},
            {"scope","Saved historical counters only; calendar years are candidates. Raw modes are not played/CPU/fast-sim coverage. Entries are not summed and missing metrics are not zero. No current-week, salary-credit or promise-goal attribution."}};
        franchise::validate_result(performance_reply,performance_request);
        // The service includes every supported metric in either present rows or
        // missing coverage. Validate receiving support at the transport boundary,
        // including players with no saved history, before rendering the screen.
        auto no_history_reply=performance_reply;
        auto& no_history=no_history_reply["result"]["performance_context"];
        no_history["history_present"]=false;
        no_history["saved_history"]=nlohmann::json::array();
        no_history["missing_named_metrics"].push_back("completions");
        no_history["missing_named_metrics"].push_back("sacks");
        franchise::validate_result(no_history_reply,performance_request);
        auto receiving_reply=performance_reply;
        auto& receiving=receiving_reply["result"]["performance_context"];
        receiving["saved_history"]=nlohmann::json::array();
        receiving["missing_named_metrics"]=no_history["missing_named_metrics"];
        for (const auto& metric:{"receptions","receiving_yards","receiving_touchdowns"}) {
            auto row=history;
            row["metric"]=metric;
            row["unit"]=std::string(metric)=="receiving_yards"?"yards":"count";
            row["value"]=std::string(metric)=="receiving_yards"?-4:2;
            row["source"]=history_source+":entry:"+std::to_string(receiving["saved_history"].size());
            receiving["saved_history"].push_back(row);
            auto& missing=receiving["missing_named_metrics"];
            for (auto it=missing.begin();it!=missing.end();++it) if(*it==metric) {missing.erase(it);break;}
        }
        franchise::validate_result(receiving_reply,performance_request);
        auto invalid_receiving=receiving_reply;
        invalid_receiving["result"]["performance_context"]["saved_history"][0]["unit"]="yards";
        bool invalid_receiving_rejected=false;
        try {franchise::validate_result(invalid_receiving,performance_request);}
        catch(const std::exception&) {invalid_receiving_rejected=true;}
        if(!invalid_receiving_rejected) throw std::runtime_error("Receiving count with yards unit accepted");
        auto dated_performance=performance_reply;
        dated_performance["result"]["performance_context"]["franchise_season_year"]=2026;
        franchise::validate_result(dated_performance,performance_request);
        dated_performance["result"]["performance_context"]["player_profile"]={{"height_inches",74},{"weight_pounds",225},{"age_years",23},{"injury_tendency",nullptr}};
        franchise::validate_result(dated_performance,performance_request);
        auto invalid_profile=dated_performance;
        invalid_profile["result"]["performance_context"]["player_profile"]["injury_tendency"]="injury prone";
        bool invented_injury_rejected=false;
        try{franchise::validate_result(invalid_profile,performance_request);}catch(const std::exception&){invented_injury_rejected=true;}
        if(!invented_injury_rejected) throw std::runtime_error("Unsourced injury assessment accepted");
        for(const nlohmann::json invalid:{nlohmann::json(true),nlohmann::json(1999),nlohmann::json(2256)}) {
            dated_performance["result"]["performance_context"]["franchise_season_year"]=invalid;
            bool rejected=false;try{franchise::validate_result(dated_performance,performance_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Invalid displayed franchise year accepted");
        }
        auto captured_request=guest_request;
        captured_request["operation"]="negotiate_proposal";
        captured_request["request_id"]="captured-proposal";
        captured_request["observation"]["calendar"]=performance_request["observation"]["calendar"];
        auto checkpoint=performance_reply["result"];
        checkpoint["offer_context"]=guest_reply["result"]["offer_context"];
        auto captured_reply=proposal_reply;
        auto& captured_event=captured_reply["result"];
        captured_event["request_id"]="captured-proposal";
        captured_event["offer"]=checkpoint["offer_context"]["offer"];
        captured_event["proposal_preview"]=checkpoint["offer_context"]["preview"];
        captured_event["contract_format"]="original_fxg_v1";
        captured_event["guest_offer"]=captured_request["guest_offer"];
        captured_event["guest_counter"]=nullptr;
        captured_event["signing_checkpoint"]=checkpoint;
        captured_event["evidence"]={{"financial_revision",0},{"personality",checkpoint["player_context"]["personality"]},
            {"relationships",checkpoint["player_context"]["relationships"]},{"performance",checkpoint["performance_context"]}};
        franchise::validate_result(captured_reply,captured_request);
        const auto preparation=franchise::saved_signing_prepare(captured_request,captured_reply);
        if(preparation!=nlohmann::json{{"protocol",1},{"request_id","captured-proposal-guest"},
            {"operation","guest_signing_prepare"},{"timeout_ms",10000},{"team_id",checkpoint["team_id"]},
            {"proposal_request_id","captured-proposal"},{"guest_offer",captured_request["guest_offer"]},
            {"expected_revision",0},{"expected_before_sha256",checkpoint["saved_payload_sha256"]}})
            throw std::runtime_error("Captured journal preparation changed accepted source");
        nlohmann::json prepared={{"error",nullptr},{"result",{{"request_id",preparation["request_id"]},
            {"state","prepared"},{"before_payload_sha256",checkpoint["saved_payload_sha256"]},{"write_authorized",false}}}};
        franchise::validate_result(prepared,preparation);
        auto journal=franchise::SavedSigningJournal::capture(captured_request,captured_reply);
        journal.consume(preparation,prepared);
        auto completion=journal;
        completion.observe_completed(std::string(64,'a'),std::string(64,'b'));
        completion.observe_completed(std::string(64,'a'),std::string(64,'b'));
        bool changed_completion=false;
        try{completion.observe_completed(std::string(64,'c'),std::string(64,'b'));}catch(...){changed_completion=true;}
        if(!changed_completion) throw std::runtime_error("Changed completion was not held");
        const auto status_request=journal.next(false);
        if(status_request.at("operation")!="guest_signing_status") throw std::runtime_error("Recovery read requires AI");
        auto saved_status=nlohmann::json{{"error",nullptr},{"result",{{"request_id",preparation["request_id"]},
            {"state","prepared"},{"save_position","before"},{"write_authorized",false},
            {"current_payload_sha256",checkpoint["saved_payload_sha256"]},
            {"before_payload_sha256",checkpoint["saved_payload_sha256"]},{"after_payload_sha256",nullptr}}}};
        journal.consume(status_request,saved_status);
        auto pending_candidate=saved_status;
        pending_candidate["result"]["save_position"]="candidate_after";
        pending_candidate["result"]["current_payload_sha256"]=std::string(64,'d');
        completion.consume(status_request,pending_candidate); // A pending pre-completion reply.
        const auto compare_request=completion.next(true);
        if(compare_request.at("operation")!="guest_signing_status" || compare_request.at("live_finance_sha256")!=std::string(64,'a'))
            throw std::runtime_error("Uncompared completion allowed saved settlement");
        auto compared=pending_candidate;compared["result"]["live_application_matches"]=true;
        completion.consume(compare_request,compared);
        if(completion.next(true).at("operation")!="guest_signing_confirm" ||
           completion.next(false).at("operation")!="guest_signing_status")
            throw std::runtime_error("Live comparison lost saved proof or control requirement");
        compared["result"]["live_application_matches"]=false;
        completion.consume(compare_request,compared);
        if(!completion.next(true).is_null() || !completion.next(false).is_null())
            throw std::runtime_error("Mismatched completion continued automatically");
        auto live_request=status_request;
        live_request["live_finance_sha256"]=std::string(64,'a');
        live_request["live_identity_sha256"]=std::string(64,'b');
        auto live_status=saved_status;
        for(bool matches:{false,true}) {
            live_status["result"]["live_application_matches"]=matches;
            franchise::validate_result(live_status,live_request);
        }
        for(int scenario=0;scenario<5;++scenario) {
            auto request=live_request;auto response=live_status;
            if(scenario==0) response["result"].erase("live_application_matches");
            if(scenario==1) response["result"]["live_application_matches"]=1;
            if(scenario==2) request.erase("live_identity_sha256");
            if(scenario==3) request["live_finance_sha256"]=std::string(64,'A');
            if(scenario==4) request=status_request;
            bool rejected=false;
            try{franchise::validate_result(response,request);}catch(...){rejected=true;}
            if(!rejected) throw std::runtime_error("Invalid live completion status accepted");
        }
        if(journal.next(true).at("operation")!="guest_signing_status") throw std::runtime_error("Unchanged save queued settlement");
        saved_status["result"]["save_position"]="candidate_after";
        saved_status["result"]["current_payload_sha256"]=std::string(64,'d');
        journal.consume(status_request,saved_status);
        if(journal.next(false).at("operation")!="guest_signing_status") throw std::runtime_error("AI-off recovery queued settlement");
        const auto confirm_request=journal.next(true);
        if(confirm_request.at("operation")!="guest_signing_confirm" || confirm_request.at("expected_after_sha256")!=std::string(64,'d'))
            throw std::runtime_error("Confirmation lost verified candidate hash");
        auto confirmed=nlohmann::json{{"error",nullptr},{"result",{{"request_id",preparation["request_id"]},
            {"state","settled"},{"player_id",checkpoint["player_id"]},{"financial_revision",1},
            {"charges",captured_event["proposal_preview"]["contract_charges"]},
            {"after_payload_sha256",std::string(64,'d')},{"write_authorized",false}}}};
        for(int scenario=0;scenario<7;++scenario) {
            auto bad=confirmed;auto copy=journal;
            if(scenario==0) bad["result"]["player_id"]=std::string(32,'f');
            if(scenario==1) bad["result"]["financial_revision"]=2;
            if(scenario==2) bad["result"]["charges"][0]=1;
            if(scenario==3) bad["result"]["after_payload_sha256"]=std::string(64,'e');
            if(scenario==4) bad["result"]["write_authorized"]=true;
            if(scenario==5) bad["result"]["extra"]=false;
            if(scenario==6) copy.preparation["expected_revision"]=std::numeric_limits<int64_t>::max();
            bool rejected=false;
            try{copy.consume(confirm_request,bad);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Contradictory native journal settlement accepted");
        }
        auto refused=journal;refused.consume(confirm_request,nlohmann::json{{"error","ai_disabled"}});
        if(refused.next(false).at("operation")!="guest_signing_status") throw std::runtime_error("Refusal skipped fresh recovery read");
        journal.consume(confirm_request,confirmed);
        if(journal.next(false).at("operation")!="guest_signing_status") throw std::runtime_error("Confirmation skipped saved-state read");
        auto settled_status=saved_status;
        settled_status["result"]["state"]="settled";settled_status["result"]["save_position"]="confirmed_after";
        settled_status["result"]["after_payload_sha256"]=std::string(64,'d');
        journal.consume(status_request,settled_status);
        if(!journal.next(true).is_null()) throw std::runtime_error("Confirmed journal kept polling or settling");
        for(int scenario=0;scenario<8;++scenario) {
            auto bad=saved_status;
            if(scenario==0) bad["result"]["state"]="other";
            if(scenario==1) bad["result"]["save_position"]="confirmed_after";
            if(scenario==2) bad["result"]["save_position"]="before";
            if(scenario==3) bad["result"]["before_payload_sha256"]=std::string(64,'e');
            if(scenario==4) bad["result"]["current_payload_sha256"]=std::string(64,'D');
            if(scenario==5) bad["result"]["after_payload_sha256"]=std::string(64,'d');
            if(scenario==6) bad["result"]["request_id"]="another";
            if(scenario==7) bad["result"]["state"]="cancelled";
            bool rejected=false;
            try{auto copy=journal;copy.consume(status_request,bad);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Invalid recovery state/hash accepted");
        }
        if(franchise::signing_display(prepared).offer.find("Signing remains held.")==std::string::npos)
            throw std::runtime_error("Preparation display implied a signing");
        for(int scenario=0;scenario<5;++scenario) {
            auto bad=prepared;
            if(scenario==0) bad["result"]["write_authorized"]=true;
            if(scenario==1) bad["result"]["request_id"]="other";
            if(scenario==2) bad["result"]["state"]="settled";
            if(scenario==3) bad["result"]["before_payload_sha256"]=std::string(64,'c');
            if(scenario==4) bad["result"]["extra"]=false;
            bool rejected=false;
            try{franchise::validate_result(bad,preparation);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Invalid journal preparation receipt accepted");
        }
        auto declined=captured_reply;
        declined["result"]["action"]="reject";declined["result"]["outcome"]="player_rejected";
        declined["result"].erase("proposal_preview");
        auto offended=declined;
        offended["result"]["signing_checkpoint"]["player_context"]["relationships"]["respect"]=0.5;
        offended["result"]["evidence"]["relationships"]["respect"]=0.5;
        offended["result"]["reaction"]="offended";
        offended["result"]["reaction_effect"]={{"policy","offer-reaction-v1"},{"relationship","respect"},{"before",0.5},{"after",0.45}};
        franchise::validate_result(offended,captured_request);
        auto recalled_offense=offended;
        recalled_offense["result"]["signing_checkpoint"]["player_context"]["relationships"]["respect"]=0.45;
        franchise::validate_result(recalled_offense,captured_request);
        auto stale_acceptance=captured_reply;
        stale_acceptance["result"]["signing_checkpoint"]["player_context"]["relationships"]["respect"]=0.45;
        stale_acceptance["result"]["evidence"]["relationships"]["respect"]=0.5;
        bool stale_acceptance_rejected=false;
        try{franchise::validate_result(stale_acceptance,captured_request);}catch(const std::exception&){stale_acceptance_rejected=true;}
        if(!stale_acceptance_rejected) throw std::runtime_error("Changed opinion reused a captured acceptance");
        if(!franchise::saved_signing_prepare(captured_request,offended).is_null())
            throw std::runtime_error("Opinion consequence authorized signing");
        for(int scenario=0;scenario<7;++scenario) {
            auto bad=offended;
            if(scenario==0) bad["result"]["reaction_effect"]["after"]=0.1;
            if(scenario==1) bad["result"]["reaction_effect"]["before"]=0.6;
            if(scenario==2) bad["result"]["reaction_effect"]["relationship"]="trust";
            if(scenario==3) bad["result"]["reaction"]="none";
            if(scenario==4) bad["result"].erase("reaction");
            if(scenario==5) bad["result"]["reaction_effect"]["policy"]="invented";
            if(scenario==6) bad["result"]["reaction_effect"]["extra"]=true;
            bool rejected=false;
            try{franchise::validate_result(bad,captured_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Contradictory negotiation opinion effect accepted");
        }
        if(!franchise::saved_signing_prepare(captured_request,declined).is_null() ||
           !franchise::saved_signing_prepare(captured_request,nlohmann::json{{"error","ai_disabled"}}).is_null() ||
           !franchise::saved_signing_prepare(proposal_request,proposal_reply).is_null())
            throw std::runtime_error("Unaccepted or uncaptured offer prepared a journal");
        for(int scenario=0;scenario<3;++scenario) {
            auto bad=captured_reply;
            if(scenario==0) bad["result"]["guest_offer"]["amount_word"]=830;
            if(scenario==1) bad["result"]["signing_checkpoint"]["financial_revision"]=1;
            if(scenario==2) bad["result"]["signing_checkpoint"]["write_authorized"]=true;
            bool rejected=false;
            try{franchise::saved_signing_prepare(captured_request,bad);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Altered captured acceptance prepared a journal");
        }
        auto held_display_reply=captured_reply;
        held_display_reply["result"]["signing_checkpoint"]["player_context"]["personality"]={
            {"money",0.5},{"security",0.2},{"playing_time",0.9},{"winning",0.8},{"loyalty",0.1}};
        held_display_reply["result"]["counter"]=held_display_reply["result"]["offer"];
        held_display_reply["result"]["reason"]="I want a larger role on this team.";
        for(const auto& outcome:{"accepted_proposal","counteroffer","player_rejected","accounting_rejected"}) {
            held_display_reply["result"]["outcome"]=outcome;
            const auto text=franchise::signing_display(held_display_reply);
            if(text.offer.find("Signing remains held.")==std::string::npos ||
               text.history!="Reason: I want a larger role on this team.")
                throw std::runtime_error("Held proposal display lost response or implied a signing");
        }
        auto scaled_captured=captured_reply;
        auto& scaled_event=scaled_captured["result"];
        auto& scaled_terms=scaled_event["signing_checkpoint"]["offer_context"];
        scaled_terms["contract_format"]="softdrink_fxg_v1";
        scaled_terms["offer"]=franchise::exact_guest_offer(captured_request["guest_offer"],std::string(32,'a'),"softdrink_fxg_v1");
        scaled_terms["preview"]["contract_charges"]={19064000,14092000};
        scaled_terms["preview"]["room_after"]=80936000;
        scaled_event["offer"]=scaled_terms["offer"];
        scaled_event["proposal_preview"]=scaled_terms["preview"];
        scaled_event["contract_format"]="softdrink_fxg_v1";
        franchise::validate_result(scaled_captured,captured_request);
        scaled_event["contract_format"]="original_fxg_v1";
        bool scale_mismatch_rejected=false;
        try{franchise::validate_result(scaled_captured,captured_request);}catch(const std::exception&){scale_mismatch_rejected=true;}
        if(!scale_mismatch_rejected) throw std::runtime_error("Captured proposal scale substitution accepted");
        nlohmann::json display_reply={{"error",nullptr},{"result",checkpoint}};
        display_reply["result"]["player_context"]["personality"]={{"money",0.5},{"security",0.2},
            {"playing_time",0.9},{"winning",0.8},{"loyalty",0.1}};
        const auto display_text=franchise::signing_display(display_reply);
        if(display_text.priorities!="Priorities: playing time and winning" ||
            display_text.offer!="Offer fits the supported cap and contract rules.")
            throw std::runtime_error("Signing display priorities or eligibility mismatch");
        display_reply["result"]["player_context"]["personality"]["money"]=2;
        bool bad_display=false;
        try{franchise::signing_display(display_reply);}catch(const std::exception&){bad_display=true;}
        if(!bad_display) throw std::runtime_error("Invalid display priority accepted");
        for(int scenario=0;scenario<6;++scenario) {
            auto bad=captured_reply;
            if(scenario==0) bad["result"]["evidence"]["personality"]={{"money",0.99}};
            if(scenario==1) bad["result"]["evidence"]["relationships"]={{"trust",0.1}};
            if(scenario==2) bad["result"]["evidence"]["performance"]["player_id"]=std::string(32,'c');
            if(scenario==3) bad["result"]["signing_checkpoint"]["write_authorized"]=true;
            if(scenario==4) bad["result"]["signing_checkpoint"]["offer_context"]["outcome"]="accounting_rejected";
            if(scenario==5) bad["result"]["signing_checkpoint"]["saved_payload_sha256"]=std::string(64,'c');
            bool rejected=false;
            try{franchise::validate_result(bad,captured_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Captured proposal source substitution accepted");
        }
        for(int scenario=0;scenario<11;++scenario) {
            auto bad=performance_reply;
            auto& evidence=bad["result"]["performance_context"];
            if(scenario==0) evidence["player_id"]=std::string(32,'c');
            if(scenario==1) evidence["source"]="another snapshot";
            if(scenario==2) evidence["saved_history"][0]["metric"]="overall_rating";
            if(scenario==3) evidence["saved_history"][0]["value"]=1.5;
            if(scenario==4) evidence["saved_history"][1]["raw_half_sack_units"]=4;
            if(scenario==5) evidence["missing_named_metrics"].push_back("completions");
            if(scenario==6) evidence["history_present"]=false;
            if(scenario==7) evidence["saved_history"][0]["candidate_calendar_year"]=2005;
            if(scenario==8) evidence["saved_history"][0]["source"]="unbound record";
            if(scenario==9) evidence["unmapped_requested_metrics"]=nlohmann::json::array();
            if(scenario==10) evidence["ratings"]={{"catching",90}};
            bool rejected=false;
            try{franchise::validate_result(bad,performance_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt saved performance accepted");
        }
        bool unsolicited_performance=false;
        try{franchise::validate_result(performance_reply,signing_request);}catch(const std::exception&){unsolicited_performance=true;}
        if(!unsolicited_performance) throw std::runtime_error("Unrequested performance accepted");
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
        auto history_context_goldens=nlohmann::json::parse(std::string(R"ctxgolden([{"request":{"operation":"contract_context","team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","context_format":"calendar_v4"},"reply":{"error":null,"result":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":4,"league_year":2027,"calendar_accounting":{"status":"active","anchor_year":2026,"current_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":1,"bonus_years":5},"annual_charges":[3000000,3000000],"ownership_current":true,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"active","contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":0,"bonus_years":5},"annual_charges":[3000000,3000000,3000000],"charge_scope":"active_contract","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,2000000,0],"unpaid_signing_bonus":0,"obligation_source":"synthetic paid original bonus"}},"release_calendar":null,"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":0,"bonus_years":5},"amendment_history":null}}},{"request":{"operation":"contract_context","team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","context_format":"calendar_v4"},"reply":{"error":null,"result":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":5,"league_year":2027,"calendar_accounting":{"status":"active","anchor_year":2027,"current_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,0]},"source":"synthetic immutable original; base conversion: synthetic guaranteed calendar conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:convert-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic guaranteed calendar conversion"}]},"annual_charges":[2950000,3050000],"ownership_current":true,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"active","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,0]},"source":"synthetic immutable original; base conversion: synthetic guaranteed calendar conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:convert-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic guaranteed calendar conversion"}]},"annual_charges":[2950000,3050000],"charge_scope":"active_contract","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic guaranteed calendar conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,1900000,0],"unpaid_signing_bonus":100000,"unpaid_bonus_layers":{"bonus:calendar-restructure:convert-2027":100000},"unpaid_original_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic guaranteed calendar conversion"}},"release_calendar":null,"trade_calendar":null,"original_co)ctxgolden")
            + R"ctxgolden(ntract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic guaranteed calendar conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:convert-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic guaranteed calendar conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,0]},"source":"synthetic immutable original; base conversion: synthetic guaranteed calendar conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:convert-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic guaranteed calendar conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic guaranteed calendar conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}}}}},{"request":{"operation":"contract_context","team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","context_format":"calendar_v4"},"reply":{"error":null,"result":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":9,"league_year":2028,"calendar_accounting":{"status":"active","anchor_year":2028,"current_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"annual_charges":[3050000],"ownership_current":true,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"active","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000)ctxgolden"
            + R"ctxgolden(,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"annual_charges":[3050000],"charge_scope":"active_contract","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,1800000],"unpaid_signing_bonus":200000,"unpaid_bonus_layers":{"bonus:calendar-restructure:first-2027":0,"bonus:calendar-layered-restructure:second-2028":200000},"unpaid_original_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion"}},"release_calendar":null,"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":)ctxgolden"
            + R"ctxgolden(["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}}}}},{"request":{"operation":"contract_context","team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","context_format":"calendar_v4"},"reply":{"error":null,"result":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":10,"league_year":2028,"calendar_accounting":{"status":"released","anchor_year":2028,"current_contract":null,"annual_charges":[3050000],"ownership_current":false,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"released","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"annual_charges":[3050000],"charge_scope":"retained_obligations","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,1800000],"unpaid_signing_bonus":200000,"unpaid_bonus_layers":{"bonus:calendar-restructure:first-2027":0,"bonus:calendar-layered-restructure:second-2028":200000},"unpaid_original_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release"}},"release_calendar":{"league_year":2028,"elapsed_years":2,"source":"synthetic healthy layered release"},"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,)ctxgolden"
            + R"ctxgolden("guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":")ctxgolden"
            + R"ctxgolden(synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}}}}},{"request":{"operation":"contract_context","team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","context_format":"calendar_v4"},"reply":{"error":null,"result":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":11,"league_year":2028,"calendar_accounting":{"status":"assigned","anchor_year":2028,"current_contract":null,"annual_charges":["2650000/3","2650000/3"],"ownership_current":false,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"assigned","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"annual_charges":["2650000/3","2650000/3"],"charge_scope":"retained_obligations","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":7200000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,0,0],"unpaid_signing_bonus":0,"unpaid_original_signing_bonus":0,"unpaid_bonus_layers":{"bonus:calendar-restructure:first":0,"bonus:calendar-layered-restructure:second":0}}},"release_calendar":null,"trade_calendar":{"league_year":2028,"elapsed_years":2,"source":"synthetic layered assignment"},"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000,0]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000,0]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"s)ctxgolden"
            + R"ctxgolden(ynthetic first conversion"},"annual_minimums":[1345000,1390000,1435000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000,1435000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]}}}}}},{"request":{"operation":"contract_context","team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","context_format":"calendar_v4"},"reply":{"error":null,"result":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":12,"league_year":2029,"calendar_accounting":{"status":"expired","anchor_year":2028,"current_contract":null,"annual_charges":[],"ownership_current":false,"expiry_source":"synthetic complete closing"},"economic_archive":{"generat)ctxgolden"
            + R"ctxgolden(ion_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"active","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"annual_charges":[3050000],"charge_scope":"active_contract","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":9000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["base:2",1800000],["bonus:calendar-layered-restructure:second-2028",200000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,0],"unpaid_signing_bonus":0,"unpaid_bonus_layers":{"bonus:calendar-restructure:first-2027":0,"bonus:calendar-layered-restructure:second-2028":0},"unpaid_original_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion"}},"release_calendar":null,"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_y)ctxgolden"
            + R"ctxgolden(ears":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}}}}},{"request":{"protocol":1,"request_id":"plain-player","operation":"player_context","team_id":"a","player_id":"v","context_format":"calendar_v4","timeout_ms":5000},"reply":{"protocol":1,"request_id":"plain-player","result":{"player_id":"v","financial_revision":4,"initialized":true,"contract_accounting":null,"personality":{"money":0.8},"relationships":{"trust":0.6},"agreed_promises":[],"promise_history":[],"negotiation_history":[],"negotiation_history_total":0,"negotiation_history_has_more":false,"context_format":"calendar_v4","calendar_contract_context":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":4,"league_year":2027,"calendar_accounting":{"status":"active","anchor_year":2026,"current_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":1,"bonus_years":5},"annual_charges":[3000000,3000000],"ownership_current":true,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"active","contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":0,"bonus_years":5},"annual_charges":[3000000,3000000,3000000],"charge_scope":"active_contract","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,2000)ctxgolden"
            + R"ctxgolden(000,0],"unpaid_signing_bonus":0,"obligation_source":"synthetic paid original bonus"}},"release_calendar":null,"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":0,"bonus_years":5},"amendment_history":null}},"error":null,"detail":null}},{"request":{"protocol":1,"request_id":"first-player","operation":"player_context","team_id":"a","player_id":"v","context_format":"calendar_v4","timeout_ms":5000},"reply":{"protocol":1,"request_id":"first-player","result":{"player_id":"v","financial_revision":5,"initialized":true,"contract_accounting":null,"personality":{"money":0.8},"relationships":{"trust":0.6},"agreed_promises":[],"promise_history":[],"negotiation_history":[],"negotiation_history_total":0,"negotiation_history_has_more":false,"context_format":"calendar_v4","calendar_contract_context":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":5,"league_year":2027,"calendar_accounting":{"status":"active","anchor_year":2027,"current_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,0]},"source":"synthetic immutable original; base conversion: synthetic guaranteed calendar conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:convert-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic guaranteed calendar conversion"}]},"annual_charges":[2950000,3050000],"ownership_current":true,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"active","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,0]},"source":"synthetic immutable original; base conversion: synthetic guaranteed calendar conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:convert-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic guaranteed calendar conversion"}]},"annual_charges":[2950000,3050000],"charge_scope":"active_contract","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic guaranteed calendar conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,1900000,0],"unpaid_signing_bonus":100000,"unpaid_bonus_layers":{"bonus:calendar-restructure:convert-2027":100000},"unpaid_original_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic guaranteed calendar conversion"}},"release_calendar":null,"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,0]},"source":"synthetic immutable original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","sa)ctxgolden"
            + R"ctxgolden(lary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic guaranteed calendar conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:convert-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic guaranteed calendar conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,0]},"source":"synthetic immutable original; base conversion: synthetic guaranteed calendar conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:convert-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic guaranteed calendar conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic guaranteed calendar conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}}}},"error":null,"detail":null}},{"request":{"protocol":1,"request_id":"repeated-player","operation":"player_context","team_id":"a","player_id":"v","context_format":"calendar_v4","timeout_ms":5000},"reply":{"protocol":1,"request_id":"repeated-player","result":{"player_id":"v","financial_revision":9,"initialized":true,"contract_accounting":null,"personality":{"money":0.8},"relationships":{"trust":0.6},"agreed_promises":[],"promise_history":[],"negotiation_history":[],"negotiation_history_total":0,"negotiation_history_has_more":false,"context_format":"calendar_v4","calendar_contract_context":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":9,"league_year":2028,"calendar_accounting":{"status":"active","anchor_year":2028,"current_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"annual_charges":[3050000],"ownership_current":true,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"active","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"annual_charges":[3050000],"charge_scope":"active_contract","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,1800000],"unpaid_signing_bonus":200000,"unpaid_bonus_layers":{"bonus:calendar-restructure:first-2027":0,"bonus:calendar-laye)ctxgolden"
            + R"ctxgolden(red-restructure:second-2028":200000},"unpaid_original_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion"}},"release_calendar":null,"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,19000)ctxgolden"
            + R"ctxgolden(00,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}}}},"error":null,"detail":null}},{"request":{"protocol":1,"request_id":"expired-player","operation":"player_context","team_id":"a","player_id":"v","context_format":"calendar_v4","timeout_ms":5000},"reply":{"protocol":1,"request_id":"expired-player","result":{"player_id":"v","financial_revision":12,"initialized":true,"contract_accounting":null,"personality":{"money":0.8},"relationships":{"trust":0.6},"agreed_promises":[],"promise_history":[],"negotiation_history":[],"negotiation_history_total":0,"negotiation_history_has_more":false,"context_format":"calendar_v4","calendar_contract_context":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":12,"league_year":2029,"calendar_accounting":{"status":"expired","anchor_year":2028,"current_contract":null,"annual_charges":[],"ownership_current":false,"expiry_source":"synthetic complete closing"},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"active","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"annual_charges":[3050000],"charge_scope":"active_contract","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":9000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["base:2",1800000],["bonus:calendar-layered-restructure:second-2028",200000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,0],"unpaid_signing_bonus":0,"unpaid_bonus_layers":{"bonus:calendar-restructure:first-2027":0,"bonus:calendar-layered-restructure:second-2028":0},"unpaid_original_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion"}},"release_calendar":null,"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v",")ctxgolden"
            + R"ctxgolden(amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["bas)ctxgolden"
            + R"ctxgolden(e:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}}}},"error":null,"detail":null}},{"request":{"protocol":1,"request_id":"released-player","operation":"player_context","team_id":"a","player_id":"v","context_format":"calendar_v4","timeout_ms":5000},"reply":{"protocol":1,"request_id":"released-player","result":{"player_id":"v","financial_revision":10,"initialized":true,"contract_accounting":null,"personality":{"money":0.8},"relationships":{"trust":0.6},"agreed_promises":[],"promise_history":[],"negotiation_history":[],"negotiation_history_total":0,"negotiation_history_has_more":false,"context_format":"calendar_v4","calendar_contract_context":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":10,"league_year":2028,"calendar_accounting":{"status":"released","anchor_year":2028,"current_contract":null,"annual_charges":[3050000],"ownership_current":false,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"released","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"annual_charges":[3050000],"charge_scope":"retained_obligations","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,1800000],"unpaid_signing_bonus":200000,"unpaid_bonus_layers":{"bonus:calendar-restructure:first-2027":0,"bonus:calendar-layered-restructure:second-2028":200000},"unpaid_original_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release"}},"release_calendar":{"league_year":2028,"elapsed_years":2,"source":"synthetic healthy layered release"},"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Execu)ctxgolden"
            + R"ctxgolden(ted-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}}}},"error":null,"detail":null}},{"request":{"protocol":1,"request_id":"released-next-player","operation":"player_context","team_id":"a","player_id":"v","context_format":"calendar_v4","timeout_ms":5000},"reply":{"protocol":1,"request_id":"released-next-player","result":{"player_id":"v","financial_revision":11,"initialized":true,"contract_accounting":null,"personality":{"money":0.8},"relationships":{"trust":0.6},"agreed_promises":[],"promise_history":[],"negotiation_history":[],"negotiation_history_total":0,"negotiation_history_has_more":false,"context_format":"calendar_v4",")ctxgolden"
            + R"ctxgolden(calendar_contract_context":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":11,"league_year":2029,"calendar_accounting":{"status":"released","anchor_year":2028,"current_contract":null,"annual_charges":[],"ownership_current":false,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"released","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"annual_charges":[3050000],"charge_scope":"retained_obligations","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,1800000],"unpaid_signing_bonus":200000,"unpaid_bonus_layers":{"bonus:calendar-restructure:first-2027":0,"bonus:calendar-layered-restructure:second-2028":200000},"unpaid_original_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason release: synthetic healthy layered release"}},"release_calendar":{"league_year":2028,"elapsed_years":2,"source":"synthetic healthy layered release"},"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"})ctxgolden"
            + R"ctxgolden(]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first-2027","amount":100000,"original_start_index":1,"allocation_years":2,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second-2028","amount":200000,"original_start_index":2,"allocation_years":1,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":9000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first-2027",100000],["signing_bonus",3000000]]}}}}},"error":null,"detail":null}},{"request":{"protocol":1,"request_id":"assigned-player","operation":"player_context","team_id":"a","player_id":"v","context_format":"calendar_v4","timeout_ms":5000},"reply":{"protocol":1,"request_id":"assigned-player","result":{"player_id":"v","financial_revision":11,"initialized":true,"contract_accounting":null,"personality":{"money":0.8},"relationships":{"trust":0.6},"agreed_promises":[],"promise_history":[],"negotiation_history":[],"negotiation_history_total":0,"negotiation_history_has_more":false,"context_format":"calendar_v4","calendar_contract_context":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":11,"league_year":2028,"calendar_accounting":{"status":"assigned","anchor_year":2028,"current_contract":null,"annual_charges":["2650000/3","2650000/3"],"ownership_current":false,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"assigned","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base c)ctxgolden"
            + R"ctxgolden(onversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"annual_charges":["2650000/3","2650000/3"],"charge_scope":"retained_obligations","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":7200000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,0,0],"unpaid_signing_bonus":0,"unpaid_original_signing_bonus":0,"unpaid_bonus_layers":{"bonus:calendar-restructure:first":0,"bonus:calendar-layered-restructure:second":0}}},"release_calendar":null,"trade_calendar":{"league_year":2028,"elapsed_years":2,"source":"synthetic layered assignment"},"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000,0]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000,0]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000,1435000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount)ctxgolden"
            + R"ctxgolden(":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000,1435000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]}}}}},"error":null,"detail":null}},{"request":{"protocol":1,"request_id":"buyer-player","operation":"player_context","team_id":"b","player_id":"v","context_format":"calendar_v4","timeout_ms":5000},"reply":{"protocol":1,"request_id":"buyer-player","result":{"player_id":"v","financial_revision":5,"initialized":true,"contract_accounting":null,"personality":{"money":0.8},"relationships":{"trust":0.6},"agreed_promises":[],"promise_history":[],"negotiation_history":[],"negotiation_history_total":0,"negotiation_history_has_more":false,"context_format":"calendar_v4","calendar_contract_context":{"format":5,"team_id":"b","generation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","financial_revision":5,"league_year":2028,"calendar_accounting":{"status":"active","anchor_year":2028,"current_contract":{"offer":{"player_id":"v","salaries":[1800000,2000000],"signing_bonus":0,"guaranteed_salaries":[1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; original signing bonus remains with assigning club","elapsed_years":0,"bonus_years":5},"annual_charges":[1800000,2000000],"ownership_current":true,"expiry_source":null},"economic_archive":{"generation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4fb32a","status":"active","contract":{"offer":{"player_id":"v","salaries":[1800000,2000000],"signing_bonus":0,"guaranteed_salaries":[1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; original signing bonus remains with assigning club","elapsed_years":0,"bonus_years":5},"annual_charges":[1800000,2000000],"charge_scope":"active_contract","cash_obligation":{"obligation_id":"contract-gen:f28c707ee5b02e5f8a76e667169b25e0f99165a9e62bf4d6656ba65b6b4)ctxgolden"
            + R"ctxgolden(fb32a","player_id":"v","amount":3800000,"paid":0,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; assigned remaining base","paid_components":[]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[1800000,0],"unpaid_signing_bonus":0,"obligation_source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; assigned remaining base"}},"release_calendar":null,"trade_calendar":null,"original_contract":{"offer":{"player_id":"v","salaries":[1800000,2000000],"signing_bonus":0,"guaranteed_salaries":[1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment; original signing bonus remains with assigning club","elapsed_years":0,"bonus_years":5},"amendment_history":null}},"error":null,"detail":null}},{"request":{"protocol":1,"request_id":"assigned-next-player","operation":"player_context","team_id":"a","player_id":"v","context_format":"calendar_v4","timeout_ms":5000},"reply":{"protocol":1,"request_id":"assigned-next-player","result":{"player_id":"v","financial_revision":12,"initialized":true,"contract_accounting":null,"personality":{"money":0.8},"relationships":{"trust":0.6},"agreed_promises":[],"promise_history":[],"negotiation_history":[],"negotiation_history_total":0,"negotiation_history_has_more":false,"context_format":"calendar_v4","calendar_contract_context":{"format":5,"team_id":"a","generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","financial_revision":12,"league_year":2029,"calendar_accounting":{"status":"assigned","anchor_year":2028,"current_contract":null,"annual_charges":["2650000/3"],"ownership_current":false,"expiry_source":null},"economic_archive":{"generation_id":"legacy-contract:be70191536cfa0fe2ecf746e944b3a7f17b5e761ecc8e57714e7c0003ca97c0a","status":"assigned","contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"}]},"annual_charges":["2650000/3","2650000/3"],"charge_scope":"retained_obligations","cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":7200000,"paid":7200000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion; preseason assignment: synthetic layered assignment; calendar-layered-trade:assignment","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-layered-restructure:second",200000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"guarantees":{"unpaid_guaranteed_base_by_original_year":[0,0,0,0],"unpaid_signing_bonus":0,"unpaid_original_signing_bonus":0,"unpaid_bonus_layers":{"bonus:calendar-restructure:first":0,"bonus:calendar-layered-restructure:second":0}}},"release_calendar":null,"trade_calendar":{"league_year":2028,"elapsed_years":2,"source":"synthetic layered assignment"},"original_contract":{"offer":{"player_id":"v","salaries":[2000000,2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000,0]},"source":"synthetic original","elapsed_years":0,"bonus_years":5},"amendment_history":{"format":1,"prior_restructures":[{"original_contract":{"offer)ctxgolden"
            + R"ctxgolden(":{"player_id":"v","salaries":[2000000,2000000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,2000000,2000000,0]},"source":"synthetic original","elapsed_years":1,"bonus_years":5},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus","paid_components":[["base:0",2000000],["signing_bonus",3000000]]},"scope":{"league_year":2027,"amended_on":"2027-06-01","first_regular_season_game":"2027-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic first conversion"},"annual_minimums":[1345000,1390000,1435000],"converted_base":100000,"bonus_layer":{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":1,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":5000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["signing_bonus",3000000]]}}],"latest_restructure":{"original_contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,2000000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,2000000,0]},"source":"synthetic original; base conversion: synthetic first conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"}]},"original_cash":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]},"scope":{"league_year":2028,"amended_on":"2028-06-01","first_regular_season_game":"2028-09-10","current_year_earned_base":0,"healthy":true,"consent":true,"renegotiation_eligible":true,"exclusions":["conditional_guarantees","deferred_new_bonus","extension","grievance","guarantee_offsets","guarantee_voids","injury_liability","other_compensation","rookie_rules","salary_benefits","unpaid_old_bonus","void_years"],"minimum_source":"https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf","source":"synthetic second conversion"},"annual_minimums":[1390000,1435000],"converted_base":200000,"bonus_layer":{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic second conversion"},"contract":{"offer":{"player_id":"v","salaries":[2000000,1900000,1800000,2000000],"signing_bonus":3000000,"guaranteed_salaries":[0,1900000,1800000,0]},"source":"synthetic original; base conversion: synthetic first conversion; base conversion: synthetic second conversion","elapsed_years":2,"bonus_years":5,"bonus_layers":[{"record_id":"calendar-restructure:first","amount":100000,"original_start_index":1,"allocation_years":3,"source":"synthetic first conversion"},{"record_id":"calendar-layered-restructure:second","amount":200000,"original_start_index":2,"allocation_years":2,"source":"synthetic)ctxgolden"
            + R"ctxgolden( second conversion"}]},"cash_obligation":{"obligation_id":"contract:v","player_id":"v","amount":11000000,"paid":7000000,"source":"synthetic paid original bonus; base conversion: synthetic first conversion; base conversion: synthetic second conversion","paid_components":[["base:0",2000000],["base:1",1900000],["bonus:calendar-restructure:first",100000],["signing_bonus",3000000]]}}}}},"error":null,"detail":null}}])ctxgolden");
        for(const auto& row:history_context_goldens) franchise::validate_result(row.at("reply"),row.at("request"));
        for(int scenario=0;scenario<14;++scenario) {
            auto row=history_context_goldens.at(2);auto& value=row["reply"]["result"];
            if(scenario==0) value["amendment_history"]=nullptr;
            if(scenario==1) value["original_contract"]["source"]="forged";
            if(scenario==2) value["original_contract"]["offer"]["signing_bonus"]=1;
            if(scenario==3) value["original_contract"]["elapsed_years"]=2;
            if(scenario==4) value["amendment_history"]["prior_restructures"]=nlohmann::json::array();
            if(scenario==5) value["amendment_history"]["latest_restructure"]["scope"]["league_year"]=2027;
            if(scenario==6) value["amendment_history"]["latest_restructure"]["contract"]["bonus_layers"].erase(0);
            if(scenario==7) value["amendment_history"]["prior_restructures"][0]["scope"]["source"]="forged";
            if(scenario==8) value["economic_archive"]["cash_obligation"]["source"]="forged";
            if(scenario==9) value["amendment_history"]["format"]=true;
            if(scenario==10) value["original_contract"]["bonus_layers"]=nlohmann::json::array();
            if(scenario==11) value["amendment_history"]["latest_restructure"]["original_cash"]["paid"]=0;
            if(scenario==12) value["calendar_accounting"]["anchor_year"]=2027;
            if(scenario==13) value["league_year"]=2027;
            bool rejected=false;try{franchise::validate_result(row.at("reply"),row.at("request"));}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt immutable economic history accepted");
        }
        auto birth_request=calendar_request;birth_request["context_format"]="calendar_v4";
        auto birth_reply=active_v2;
        birth_reply["result"]["format"]=5;birth_reply["result"]["trade_calendar"]=nullptr;
        birth_reply["result"]["original_contract"]=birth_reply["result"]["economic_archive"]["contract"];
        birth_reply["result"]["amendment_history"]=nullptr;
        franchise::validate_result(birth_reply,birth_request);
        auto birth_player_request=calendar_player_request;birth_player_request["context_format"]="calendar_v4";
        auto birth_player_reply=calendar_player_reply;birth_player_reply["result"]["context_format"]="calendar_v4";
        birth_player_reply["result"]["calendar_contract_context"]=birth_reply["result"];
        franchise::validate_result(birth_player_reply,birth_player_request);
        for(int scenario=0;scenario<8;++scenario) {
            auto bad=birth_reply;
            if(scenario==0) bad["result"]["format"]=4;
            if(scenario==1) bad["result"].erase("original_contract");
            if(scenario==2) bad["result"]["original_contract"]["source"]="forged birth";
            if(scenario==3) bad["result"]["original_contract"]["elapsed_years"]=true;
            if(scenario==4) bad["result"]["original_contract"]["offer"]["salaries"][0]=999;
            if(scenario==5) bad["result"]["amendment_history"]={{"format",1},{"prior_restructures",nlohmann::json::array()},{"latest_restructure",nullptr}};
            if(scenario==6) bad["result"]["extra"]=nullptr;
            if(scenario==7) bad["result"]["original_contract"]=nullptr;
            bool rejected=false;try{franchise::validate_result(bad,birth_request);}catch(const std::exception&){rejected=true;}
            if(!rejected) throw std::runtime_error("Corrupt immutable calendar birth accepted");
        }
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
        auto legacy_reply=player_reply;
        legacy_reply["result"]["contract_accounting"]=nullptr;
        legacy_reply["result"]["legacy_contract"]={{"player_id","v"},{"amount_word",900},
            {"bonus_code",4},{"shape_code",2},{"original_years",8},{"remaining_years",7},{"source","authored original terms"}};
        legacy_reply["result"]["legacy_liability_scope"]="original cap schedule; cash/protections/lifecycle unverified";
        franchise::validate_result(legacy_reply,player_request);
        auto scaled_legacy=legacy_reply;
        scaled_legacy["result"]["legacy_contract"]["game_dollar_scale"]=4;
        franchise::validate_result(scaled_legacy,player_request);
        scaled_legacy["result"]["legacy_contract"]["game_dollar_scale"]=2;
        bool legacy_scale_rejected=false;
        try{franchise::validate_result(scaled_legacy,player_request);}catch(const std::exception&){legacy_scale_rejected=true;}
        if(!legacy_scale_rejected) throw std::runtime_error("Unsupported legacy scale accepted");

        for (int scenario=0;scenario<10;++scenario) {
            auto bad=legacy_reply;
            auto& legacy=bad["result"]["legacy_contract"];
            if (scenario==0) legacy["player_id"]="other";
            if (scenario==1) legacy["amount_word"]=true;
            if (scenario==2) legacy["amount_word"]=65536;
            if (scenario==3) legacy["bonus_code"]=11;
            if (scenario==4) legacy["shape_code"]=8;
            if (scenario==5) legacy["remaining_years"]=9;
            if (scenario==6) legacy["paid_cash"]=0;
            if (scenario==7) legacy["source"]=" ";
            if (scenario==8) bad["result"].erase("legacy_liability_scope");
            if (scenario==9) bad["result"]["legacy_liability_scope"]="modern guarantees verified";
            bool rejected=false;
            try { franchise::validate_result(bad,player_request); } catch(const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Invalid legacy context accepted");
        }
        auto pending_reply=player_reply;
        pending_reply["result"]["contract_accounting"]=nullptr;
        pending_reply["result"]["classification_pending"]=true;
        pending_reply["result"]["observed_player_source"]="authored pinned roster";
        franchise::validate_result(pending_reply,player_request);
        for (int scenario=0;scenario<4;++scenario) {
            auto bad=pending_reply;
            if (scenario==0) bad["result"]["classification_pending"]=false;
            if (scenario==1) bad["result"].erase("classification_pending");
            if (scenario==2) bad["result"]["observed_player_source"]=" ";
            if (scenario==3) bad["result"]["contract_accounting"]=player_reply["result"]["contract_accounting"];
            bool rejected=false;
            try { franchise::validate_result(bad,player_request); } catch(const std::exception&) { rejected=true; }
            if (!rejected) throw std::runtime_error("Invalid pending classification accepted");
        }
        std::cout << "Protocol envelope and contract validation passed" << std::endl;
        return 0;
    } catch (const std::exception& error) { std::cerr << error.what() << std::endl; return 1; }
}
