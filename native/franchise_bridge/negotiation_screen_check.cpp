#include "negotiation_screen_fixture.h"
#include <cstdio>
#include <stdexcept>
static void require(bool ok){if(!ok) throw std::runtime_error("Negotiation screen model failed");}
int main() {
    try {
        auto fixture=negotiation_screen_fixture();auto pages=franchise::negotiation_pages(fixture);
        for(const auto* term:{"$6328000","$3796000","$6752000","$9704000","$7172000","$79512000"}) require(pages[0].find(term)!=std::string::npos);
        require(pages[1].find("completions: 478 count  (saved period 1, mode 0)")!=std::string::npos);
        require(pages[1].find("sacks: 2.5 sacks  (saved period 2, mode 1)")!=std::string::npos);
        require(pages[1].find("unknown, not zero")!=std::string::npos && pages[1].find("qb hits")!=std::string::npos);
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
        require(pages[2].find("$3796000")!=std::string::npos);
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
        input={};nav.input(input);input.buttons=2;nav.input(input);require(nav.scroll[2]==90);
        nav.input(input);require(nav.scroll[2]==90);
        input={};nav.input(input);input.buttons=1;nav.input(input);require(nav.scroll[2]==0);
        input={};nav.input(input);input.analog[1]=255;require(nav.input(input)==2);
        nav.reset();require(!nav.armed && !nav.page && !nav.scroll[2]);
        std::puts("Exact terms, separate saved records, full responses/counters/promises and navigation passed");return 0;
    } catch(const std::exception& error){std::fprintf(stderr,"%s\n",error.what());return 1;}
}
