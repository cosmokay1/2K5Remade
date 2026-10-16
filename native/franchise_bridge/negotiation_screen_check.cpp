#include "negotiation_screen_fixture.h"
#include <cstdio>
#include <stdexcept>
static void require(bool ok){if(!ok) throw std::runtime_error("Negotiation screen model failed");}
int main() {
    try {
        require(franchise::screen_money(-12345)=="$-12,345");
        require(franchise::screen_money("3316000/3")=="$3316000/3 (exact dollars)");
        auto fixture=negotiation_screen_fixture();auto pages=franchise::negotiation_pages(fixture);
        for(const auto* term:{"$6,328,000","$3,796,000","$6,752,000","$9,704,000","$7,172,000","$79,512,000","$16,876,000"}) require(pages[0].find(term)!=std::string::npos);
        require(pages[1].find("Record 1: completions: 478 count")!=std::string::npos);
        require(pages[1].find("Record 2: sacks: 2.5 sacks")!=std::string::npos);
        require(pages[1].find("unknown, not zero")!=std::string::npos && pages[1].find("qb hits")!=std::string::npos);
        auto receiving=fixture;
        receiving["result"]["performance_context"]["saved_history"]={
            {{"metric","receptions"},{"value",70},{"unit","count"}},
            {{"metric","receiving_yards"},{"value",900},{"unit","yards"}},
            {{"metric","receiving_touchdowns"},{"value",4},{"unit","count"}}};
        const auto receiving_page=franchise::negotiation_pages(receiving)[1];
        require(receiving_page.find("receptions: 70 count")!=std::string::npos);
        require(receiving_page.find("receiving yards: 900 yards")!=std::string::npos);
        require(receiving_page.find("receiving touchdowns: 4 count")!=std::string::npos);
        auto missing=fixture;missing["result"]["performance_context"]["saved_history"]=nlohmann::json::array();
        require(franchise::negotiation_pages(missing)[1].find("No mapped performance records")!=std::string::npos);
        auto proposal=fixture;proposal["result"]={{"signing_checkpoint",fixture["result"]},
            {"reason",std::string(1800,'r')+" END OF FULL RESPONSE"},{"counter",fixture["result"]["offer_context"]["offer"]},
            {"counter_validation",{{"status","ineligible"},{"reason","Insufficient supported cap room"}}},
            {"counter_promises",{{{"metric","starts"},{"target",12},{"window","regular season"}}}}};
        pages=franchise::negotiation_pages(proposal);
        require(pages[2].find(proposal["result"]["reason"].get<std::string>())!=std::string::npos);
        require(pages[2].find("Counter eligibility: ineligible")!=std::string::npos);
        require(pages[2].find("starts: 12; window: regular season")!=std::string::npos);
        require(pages[2].find("$3,796,000")!=std::string::npos);
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
        input={};nav.input(input);input.buttons=2;nav.input(input);require(nav.page==0); // down selects next vertical section
        nav.input(input);require(nav.page==0);
        input={};nav.input(input);input.buttons=1;nav.input(input);require(nav.page==2);
        input={};nav.input(input);input.buttons=4;nav.input(input);require(nav.page==2); // horizontal d-pad is not vertical navigation
        input={};nav.input(input);input.buttons=8;nav.input(input);require(nav.page==2);
        input={};nav.input(input);input.axes[1]=-20000;nav.input(input);require(nav.page==0);
        nav.input(input);require(nav.page==0);input.axes[1]=-12000;nav.input(input);require(nav.page==0);
        input.axes[1]=0;nav.input(input);input.axes[1]=20000;nav.input(input);require(nav.page==2);
        input={};nav.input(input);input.axes[3]=-20000;nav.input(input);require(nav.scroll[2]==90);
        nav.input(input);require(nav.scroll[2]==90);
        input={};nav.input(input);input.axes[3]=20000;nav.input(input);require(nav.scroll[2]==0);
        nav.reset();input={};input.axes[1]=-20000;nav.input(input);require(!nav.armed && nav.page==0);
        input.axes[1]=-9000;nav.input(input);require(!nav.armed);
        input={};nav.input(input);require(nav.armed);
        input={};nav.input(input);input.analog[1]=255;require(nav.input(input)==2);
        nav.reset();require(!nav.armed && !nav.page && !nav.scroll[2]);
        std::puts("Exact terms, separate saved records, full responses/counters/promises and navigation passed");return 0;
    } catch(const std::exception& error){std::fprintf(stderr,"%s\n",error.what());return 1;}
}
