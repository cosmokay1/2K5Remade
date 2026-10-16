#include "negotiation_screen_fixture.h"
#include "contract_draft.h"
#include <cstdio>
#include <stdexcept>
static void require(bool ok){if(!ok) throw std::runtime_error("Negotiation screen model failed");}
int main() {
    try {
        require(franchise::screen_money(-12345)=="$-12,345");
        require(franchise::screen_money("3316000/3")=="$3316000/3 (exact dollars)");
        auto fixture=negotiation_screen_fixture();auto pages=franchise::negotiation_pages(fixture);
        franchise::ContractDraft draft;
        require(draft.begin(fixture["result"]["offer_context"],1));
        require(draft.amount==422 && draft.years()==2 && draft.bonus()==4 && draft.schedule()=="Descending");
        require(draft.table().rows[0].values[0]=="$16,880,000");
        NFL2K5AddonInput edit{};edit.buttons=8;
        draft.input(edit);require(draft.amount==422); // Entry quarantines held controls.
        edit={};draft.input(edit);edit.buttons=8;draft.input(edit);require(draft.amount==423);
        draft.input(edit);require(draft.amount==423); // No repeated edits from a held key.
        edit={};draft.input(edit);edit.axes[0]=-24000;draft.input(edit);require(draft.amount==422);
        edit={};draft.input(edit);edit.buttons=2;draft.input(edit);require(draft.field==1);
        edit={};draft.input(edit);edit.axes[0]=24000;draft.input(edit);require(draft.years()==3);
        edit={};draft.input(edit);edit.buttons=2;draft.input(edit);
        edit={};draft.input(edit);edit.buttons=4;draft.input(edit);require(draft.bonus()==3);
        edit={};draft.input(edit);edit.buttons=2;draft.input(edit);
        const auto retained=draft.flags&0x1fffffffu;
        edit={};draft.input(edit);edit.buttons=8;draft.input(edit);
        require(draft.schedule()=="Balanced" && (draft.flags&0x1fffffffu)==retained);
        edit={};draft.input(edit);edit.analog[2]=255;require(draft.input(edit)==2);
        draft.waiting=true;edit={};draft.input(edit);edit.analog[2]=255;require(draft.input(edit)==0);
        edit={};draft.input(edit);edit.analog[1]=255;require(draft.input(edit)==1);
        draft.reset();require(!draft.active && !draft.waiting && !draft.epoch);
        auto malformed=fixture["result"]["offer_context"];
        malformed["amount_word"]=uint64_t(65536);require(!draft.begin(malformed,1));
        malformed["amount_word"]=uint64_t(1);malformed["contract_format"]="unknown";require(!draft.begin(malformed,1));
        require(!draft.begin(fixture["result"]["offer_context"],0));
        auto original=fixture["result"]["offer_context"];original.erase("contract_format");
        require(draft.begin(original,1) && draft.scale==1 && draft.table().rows[0].values[0]=="$4,220,000");
        original["offer"]=nullptr;original["preview"]=nullptr;original["outcome"]="format_rejected";
        require(draft.begin(original,1)); // Rejected drafts remain editable.
        require(draft.begin(fixture["result"]["offer_context"],1));
        draft.amount=65535;edit={};draft.input(edit);edit.buttons=8;draft.input(edit);require(draft.amount==65535);
        draft.amount=1;edit={};draft.input(edit);edit.buttons=4;draft.input(edit);require(draft.amount==1);
        edit={};draft.input(edit);edit.buttons=8;edit.analog[7]=255;draft.input(edit);require(draft.amount==26);
        draft.review();require(!draft.active && draft.present && draft.dirty() && draft.amount==26);
        draft.resume();require(draft.active && draft.amount==26 && !draft.armed);
        edit={};draft.input(edit,1000);edit.buttons=8;draft.input(edit,1010);require(draft.amount==27);
        draft.input(edit,1359);require(draft.amount==27);
        draft.input(edit,1360);require(draft.amount==28);
        draft.input(edit,1450);require(draft.amount==29);
        edit={};draft.input(edit,1500);draft.input(edit,2000);require(draft.amount==29);
        auto current=franchise::current_contract_table(fixture["result"]);
        require(current.rows.size()==3 && current.rows[0].label=="2026");
        require(current.rows[0].values==std::vector<std::string>({"$1,544,000","$2,320,000","$3,864,000"}));
        auto aged=fixture["result"];aged["player_context"]["legacy_contract"]["remaining_years"]=2;
        current=franchise::current_contract_table(aged);
        require(current.rows.size()==2 && current.rows[0].values[2]=="$4,640,000");
        aged["player_context"].erase("legacy_contract");require(franchise::current_contract_table(aged).rows.empty());
        aged["player_context"]["contract_accounting"]={{"status","active"},{"charge_scope","active_contract"},
            {"contract",{{"elapsed_years",1},{"offer",{{"salaries",{1000000,2000000,3000000}}}}}},
            {"annual_charges",{2500000,3500000}}};
        current=franchise::current_contract_table(aged);
        require(current.rows.size()==2 && current.rows[0].values==std::vector<std::string>({"$2,000,000","$500,000","$2,500,000"}));
        aged["player_context"]["contract_accounting"]["status"]="released";
        require(franchise::current_contract_table(aged).rows.empty());
        for(const auto* term:{"$6,328,000","$3,796,000","$6,752,000","$9,704,000","$7,172,000","$79,512,000","$16,876,000"}) require(pages[0].find(term)!=std::string::npos);
        require(pages[1].find("Record ")==std::string::npos);
        require(franchise::screen_profile(fixture["result"]["performance_context"])=="6'0\"  /  200 lb  /  Age 23 at season start");
        auto tables=franchise::performance_tables(fixture["result"]["performance_context"]);
        require(tables.size()==2 && tables[0].title=="Passing" && tables[1].title=="Defense");
        require(tables[0].rows[0].values[1]=="478" && tables[1].rows[0].values[1]=="2.5");
        require(pages[2].find("Priorities:")==std::string::npos);
        require(pages[2].find("Fictional")==std::string::npos);
        require(pages[2].find("Winning\nValues the chance to compete and win.")!=std::string::npos);
        require(pages[3].find("Winning")==std::string::npos);
        const auto traits=franchise::screen_personalities(fixture["result"]);
        require(traits.size()==2 && traits[0].label=="Winning" && traits[1].label=="Playing time");
        auto relationship=fixture;
        relationship["result"]["player_context"]["relationships"]={{"trust",0},{"respect",1}};
        const auto rows=franchise::screen_relationships(relationship["result"]);
        require(rows[0].known && rows[0].value==0 && rows[1].known && rows[1].value==1 && !rows[2].known);
        auto absent_personality=fixture;absent_personality["result"].erase("player_context");
        require(franchise::screen_personalities(absent_personality["result"]).empty());
        relationship["result"]["player_context"]["relationships"]["trust"]=2;
        bool bad_relationship=false;try{franchise::negotiation_pages(relationship);}catch(...){bad_relationship=true;}require(bad_relationship);
        for(const auto* key:{"money","security","playing_time","winning","loyalty"}) {
            auto priorities=fixture["result"];
            priorities["player_context"]["personality"][key]=1;
            require(!franchise::screen_personalities(priorities)[0].key.empty());
        }
        auto receiving=fixture;
        receiving["result"]["performance_context"]["saved_history"]={
            {{"metric","receptions"},{"value",70},{"unit","count"},{"period_code_raw",1},{"mode_code_raw",0}},
            {{"metric","receiving_yards"},{"value",900},{"unit","yards"},{"period_code_raw",1},{"mode_code_raw",0}},
            {{"metric","receiving_touchdowns"},{"value",4},{"unit","count"},{"period_code_raw",1},{"mode_code_raw",0}},
            {{"metric","receptions"},{"value",18},{"unit","count"},{"period_code_raw",2},{"mode_code_raw",0}},
            {{"metric","receiving_yards"},{"value",-4},{"unit","yards"},{"period_code_raw",2},{"mode_code_raw",0}}};
        auto stats=franchise::performance_tables(receiving["result"]["performance_context"]);
        require(stats.size()==1 && stats[0].title=="Receiving" && stats[0].rows.size()==2);
        require(stats[0].columns==std::vector<std::string>({"YEAR","G","REC","YDS","TD"}));
        require(stats[0].rows[0].values==std::vector<std::string>({u8"\u2014","70","900","4"}));
        require(stats[0].rows[1].values==std::vector<std::string>({u8"\u2014","18","-4",u8"\u2014"}));
        auto& history=receiving["result"]["performance_context"]["saved_history"];
        auto duplicate=history[0];duplicate["value"]=9;history.push_back(duplicate);
        duplicate["mode_code_raw"]=1;history.push_back(duplicate);
        stats=franchise::performance_tables(receiving["result"]["performance_context"]);
        require(stats[0].rows.size()==4 && stats[0].rows[2].values[1]=="9" && stats[0].rows[3].values[1]=="9");
        auto games_only=fixture["result"]["performance_context"];
        games_only["saved_history"]={{{"metric","games"},{"value",0},{"period_code_raw",3},{"mode_code_raw",0}}};
        const auto appearances=franchise::performance_tables(games_only);
        require(appearances.size()==1 && appearances[0].rows[0].values[0]=="0");
        require(tables[1].columns==std::vector<std::string>({"YEAR","G","SCK"}));
        require(tables[0].rows[0].label=="2024" && tables[1].rows[0].label=="2025");
        auto unknown_year=fixture["result"]["performance_context"];unknown_year.erase("franchise_season_year");
        require(franchise::performance_tables(unknown_year)[0].rows[0].label==u8"\u2014");
        auto annual=franchise::contract_table(fixture["result"]["offer_context"]);
        require(annual.rows.size()==2 && annual.rows[0].values[2]=="$3,376,000" && annual.rows[1].values[3]=="$7,172,000");
        auto unpreviewed=fixture["result"]["offer_context"];unpreviewed["preview"]=nullptr;
        annual=franchise::contract_table(unpreviewed);
        require(annual.rows.size()==2 && annual.rows[0].values[0]=="$6,328,000" && annual.rows[0].values[2]=="$3,376,000" && annual.rows[0].values[3]==u8"\u2014");
        auto dart=unpreviewed;dart["offer"]["salaries"]={4708000,7060000,9412000};dart["offer"]["signing_bonus"]=21180000;dart["offer"]["guaranteed_salaries"]={0,0,0};
        annual=franchise::contract_table(dart);
        require(annual.rows.size()==3 && annual.rows[0].values[2]=="$7,060,000" && annual.rows[2].values[2]=="$7,060,000");
        dart["offer"]["signing_bonus"]=0;require(franchise::contract_table(dart).rows[0].values[2]=="$0");
        dart["offer"]["signing_bonus"]=1;require(franchise::contract_table(dart).rows[0].values[2]=="$1/3 (exact dollars)");
        dart["offer"]["signing_bonus"]=21180000;
        dart["amendment"]={{"current_charges",{3864000,4640000,5412000}},
            {"carried_bonus_charges",{2320000,2320000,2320000}},
            {"combined_player_charges",{14088000,16440000,18792000}}};
        auto compared=franchise::amendment_table(dart,fixture["result"]["performance_context"]);
        require(compared.rows[0].label=="2026" && compared.rows[0].values==std::vector<std::string>({
            "$3,864,000","$4,708,000","$2,320,000","$7,060,000","$14,088,000"}));
        dart["offer"]["salaries"]={1000000};dart["offer"]["signing_bonus"]=0;dart["offer"]["guaranteed_salaries"]={0};
        dart["amendment"]["combined_player_charges"]={3320000,2320000,2320000};
        compared=franchise::amendment_table(dart,fixture["result"]["performance_context"]);
        require(compared.rows[2].values==std::vector<std::string>({"$5,412,000","$0","$2,320,000","$0","$2,320,000"}));
        auto display_comparison=fixture;
        display_comparison["result"]["offer_context"]["outcome"]="amendment_comparison";
        require(franchise::signing_display(display_comparison).offer=="Contract comparison only. Player agreement and settlement remain pending.");
        dart["amendment"]["room_before"]=89216000;dart["amendment"]["room_after"]=78992000;
        require(franchise::cap_room_comparison(dart,false)==std::array<std::string,3>{"$89,216,000","$78,992,000","-$10,224,000"});
        require(franchise::cap_room_comparison(dart,true)==std::array<std::string,3>{"$89,216,000","Check draft",u8"\u2014"});
        dart["amendment"]["room_after"]=90000000;
        require(franchise::cap_room_comparison(dart,false)[2]=="+$784,000");
        dart["amendment"]["room_after"]=89216000;
        require(franchise::cap_room_comparison(dart,false)[2]=="$0");
        auto missing=fixture;missing["result"]["performance_context"]["saved_history"]=nlohmann::json::array();
        require(franchise::negotiation_pages(missing)[1].find("No saved stats available")!=std::string::npos);
        auto proposal=fixture;proposal["result"]={{"signing_checkpoint",fixture["result"]},
            {"reason",std::string(1800,'r')+" END OF FULL RESPONSE"},{"counter",fixture["result"]["offer_context"]["offer"]},
            {"counter_validation",{{"status","ineligible"},{"reason","Insufficient supported cap room"}}},
            {"counter_promises",{{{"metric","starts"},{"target",12},{"window","regular season"}}}}};
        pages=franchise::negotiation_pages(proposal);
        require(pages[3].find(proposal["result"]["reason"].get<std::string>())!=std::string::npos);
        require(pages[3].find("Counter eligibility: ineligible")!=std::string::npos);
        require(pages[3].find("starts: 12; window: regular season")!=std::string::npos);
        require(pages[3].find("$3,796,000")!=std::string::npos);
        require(franchise::screen_conversation(fixture,pages[3]).empty());
        proposal["result"]["offer"]=fixture["result"]["offer_context"]["offer"];
        const auto conversation=franchise::screen_conversation(proposal,pages[3]);
        require(conversation.size()==2 && conversation[0].outgoing && !conversation[1].outgoing);
        require(conversation[0].body.find("$16,876,000")!=std::string::npos);
        require(conversation[1].body.find("END OF FULL RESPONSE")!=std::string::npos);
        require(conversation[1].body.find("starts: 12")!=std::string::npos);
        auto hidden=fixture;hidden["result"]["performance_context"]["saved_history"][0]["metric"]="overall_rating";
        bool hidden_refused=false;try{franchise::negotiation_pages(hidden);}catch(...){hidden_refused=true;}
        require(hidden_refused);
        fixture["result"]["write_authorized"]=true;bool refused=false;
        try{franchise::negotiation_pages(fixture);}catch(...){refused=true;}require(refused);
        franchise::NegotiationNavigation nav;NFL2K5AddonInput input{};
        input.analog[7]=255;require(nav.input(input)==1 && nav.page==0); // entering with RT held
        input={};nav.input(input);input.analog[7]=255;nav.input(input);require(nav.page==1);
        nav.input(input);require(nav.page==1); // held trigger is not repeated
        input={};nav.input(input);input.analog[7]=255;nav.input(input);require(nav.page==2);
        input={};nav.input(input);input.buttons=2;nav.input(input);require(nav.page==3); // down selects next vertical section
        nav.input(input);require(nav.page==3);
        input={};nav.input(input);input.buttons=1;nav.input(input);require(nav.page==2);
        input={};nav.input(input);input.buttons=4;nav.input(input);require(nav.page==2); // horizontal d-pad is not vertical navigation
        input={};nav.input(input);input.buttons=8;nav.input(input);require(nav.page==2);
        input={};nav.input(input);input.axes[1]=-20000;nav.input(input);require(nav.page==3);
        nav.input(input);require(nav.page==3);input.axes[1]=-12000;nav.input(input);require(nav.page==3);
        input.axes[1]=0;nav.input(input);input.axes[1]=20000;nav.input(input);require(nav.page==2);
        input={};nav.input(input);input.axes[3]=-20000;nav.input(input);require(nav.scroll[2]==90);
        nav.input(input);require(nav.scroll[2]==90);
        input={};nav.input(input);input.axes[3]=20000;nav.input(input);require(nav.scroll[2]==0);
        nav.reset();input={};input.axes[1]=-20000;nav.input(input);require(!nav.armed && nav.page==0);
        input.axes[1]=-9000;nav.input(input);require(!nav.armed);
        input={};nav.input(input);require(nav.armed);
        input={};nav.input(input);input.analog[1]=255;require(nav.input(input)==2);
        nav.reset();require(!nav.armed && !nav.page && !nav.scroll[2]);
        input={};nav.input(input);input.buttons=1;nav.input(input);require(nav.page==3);
        input={};nav.input(input);input.buttons=2;nav.input(input);require(nav.page==0);

        std::puts("Exact terms, separate saved records, full responses/counters/promises and navigation passed");return 0;
    } catch(const std::exception& error){std::fprintf(stderr,"%s\n",error.what());return 1;}
}
