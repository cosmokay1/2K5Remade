#ifndef NFL2K5_NEGOTIATION_SCREEN_H
#define NFL2K5_NEGOTIATION_SCREEN_H
#include "protocol.h"
#include "../game_addon/ui.h"
#include <array>
#include <algorithm>
#include <string>
#include <sstream>
#include <limits>
namespace franchise {
inline std::string screen_label(std::string value) {
    for(auto& c:value) if(c=='_') c=' ';
    return value;
}
inline std::string screen_metric(const std::string& value) {
    static const std::set<std::string> allowed={"games","rush_attempts","rushing_yards","rushing_touchdowns",
        "pass_attempts","completions","passing_yards","passing_touchdowns","interceptions_thrown","sacks",
        "tackles","targets","pressures","qb_hits"};
    if(!allowed.count(value)) throw std::runtime_error("Unsupported performance metric");
    return screen_label(value);
}
inline std::string screen_number(const nlohmann::json& value) {
    if(value.is_string()) return value.get<std::string>(); // exact dollar fractions
    if(value.is_number()) return value.dump();
    throw std::runtime_error("Unavailable display amount");
}
inline std::string screen_money(const nlohmann::json& value) {
    auto number=screen_number(value);
    if(number.find_first_not_of("-0123456789")!=std::string::npos) return "$"+number+" (exact dollars)";
    const int first=!number.empty() && number[0]=='-'?1:0;
    for(int i=static_cast<int>(number.size())-3;i>first;i-=3) number.insert(static_cast<size_t>(i),",");
    return "$"+number;
}
inline void screen_terms(std::ostringstream& text,const nlohmann::json& offer) {
    const auto& salaries=offer.at("salaries");
    int64_t total=offer.at("signing_bonus").get<int64_t>();
    if(total<0) throw std::runtime_error("Invalid displayed compensation");
    for(const auto& value:salaries) {
        const auto salary=value.get<int64_t>();
        if(salary<0 || total>std::numeric_limits<int64_t>::max()-salary) throw std::runtime_error("Invalid displayed compensation");
        total+=salary;
    }
    text<<"Term: "<<salaries.size()<<" years\nTotal compensation: "<<screen_money(total)<<"\n\n";
    for(size_t i=0;i<salaries.size();++i) {
        text<<"Contract year "<<i+1<<" base salary: "<<screen_money(salaries[i])<<"\n";
        if(offer.contains("guaranteed_salaries"))
            text<<"    Protected base: "<<screen_money(offer.at("guaranteed_salaries").at(i))<<"\n";
    }
    text<<"Signing bonus (total): "<<screen_money(offer.at("signing_bonus"))<<"\n";
}
inline std::array<std::string,3> negotiation_pages(const nlohmann::json& reply) {
    if(!reply.at("error").is_null()) throw std::runtime_error("No negotiation view");
    const auto& result=reply.at("result");
    const auto& checkpoint=result.contains("signing_checkpoint")?result.at("signing_checkpoint"):result;
    if(checkpoint.at("write_authorized")!=false || checkpoint.at("ai_authorized")!=false)
        throw std::runtime_error("Screen evidence is not an authorization");
    std::ostringstream contract,performance,agent;
    if(checkpoint.contains("offer_context")) {
        const auto& context=checkpoint.at("offer_context");
        if(!context.at("offer").is_null()) screen_terms(contract,context.at("offer"));
        else contract<<"These native terms cannot use the supported contract format.\n";
        if(context.contains("preview") && !context.at("preview").is_null()) {
            const auto& preview=context.at("preview");
            contract<<"\nCap charges (supported ledger scope)\n";
            const auto& charges=preview.at("contract_charges");
            for(size_t i=0;i<charges.size();++i)
                contract<<"Contract year "<<i+1<<": "<<screen_money(charges[i])<<"\n";
            contract<<"Cap room after offer: "<<screen_money(preview.at("room_after"))<<"\n";
        }
        if(context.contains("reason") && context.at("reason").is_string())
            contract<<"\nOffer unavailable: "<<context.at("reason").get<std::string>()<<"\n";
    } else contract<<"Contract preview unavailable.\n";
    contract<<"\nThis preview does not sign or reserve a contract.\n"
        <<"Cash compensation and cap charges are different amounts.\n"
        <<"Opening liabilities are not fully verified.\n";
    if(checkpoint.contains("performance_context")) {
        const auto& evidence=checkpoint.at("performance_context");
        const auto& rows=evidence.at("saved_history");
        if(rows.empty()) performance<<"No mapped performance records are available for this player.\n";
        else {
            performance<<"Saved history: season and game coverage unverified.\n"
                <<"Each row is separate; these are not current-season totals.\n\n";
            size_t record=0;
            for(const auto& row:rows)
                performance<<"Record "<<++record<<": "<<screen_metric(row.at("metric").get<std::string>())<<": "
                    <<screen_number(row.at("value"))<<" "<<row.at("unit").get<std::string>()<<"\n";
        }
        if(evidence.contains("missing_named_metrics") && !evidence.at("missing_named_metrics").empty()) {
            performance<<"\nNot available in this history:\n";
            for(const auto& metric:evidence.at("missing_named_metrics"))
                performance<<screen_metric(metric.get<std::string>())<<"\n";
        }
        if(evidence.contains("unmapped_requested_metrics") && !evidence.at("unmapped_requested_metrics").empty()) {
            performance<<"\nNot mapped from this save:\n";
            for(const auto& metric:evidence.at("unmapped_requested_metrics"))
                performance<<screen_metric(metric.get<std::string>())<<"\n";
        }
    } else performance<<"Performance evidence unavailable.\n";
    performance<<"\nMissing observations are unknown, not zero.\n"
        <<"Saved history does not establish promise fulfillment.\n";
    if(result.contains("signing_checkpoint")) {
        agent<<result.at("reason").get<std::string>()<<"\n";
        if(result.contains("counter") && !result.at("counter").is_null()) {
            agent<<"\nCounteroffer (not signed)\n";screen_terms(agent,result.at("counter"));
            if(result.contains("counter_validation")) {
                const auto& validation=result.at("counter_validation");
                agent<<"\nCounter eligibility: "<<validation.at("status").get<std::string>()<<"\n";
                if(validation.contains("reason")) agent<<validation.at("reason").get<std::string>()<<"\n";
            }
        }
        const auto& goals=result.contains("counter_promises") && !result.at("counter_promises").is_null()?result.at("counter_promises"):
            result.value("promise_goals",nlohmann::json::array());
        if(goals.is_array() && !goals.empty()) {
            agent<<"\nProposed promises (not committed)\n";
            for(const auto& goal:goals) agent<<screen_label(goal.at("metric").get<std::string>())
                <<": "<<screen_number(goal.at("target"))<<"; window: "<<goal.at("window").get<std::string>()<<"\n";
        }
    } else agent<<"No player response has been requested.\n";
    agent<<"\nOffer editing and submission are not enabled in this read-only preview.\n";
    return {contract.str(),performance.str(),agent.str()};
}
/* Local navigation only. No transport, model, game clock or financial changes. */
struct NegotiationNavigation {
    unsigned page=0;
    std::array<int,3> scroll{};
    bool armed=false;
    uint16_t previous_buttons=0;
    std::array<uint8_t,8> previous_analog{};
    std::array<int,2> vertical{};
    void reset(){*this={};}
    int input(const NFL2K5AddonInput& input) {
        bool neutral=!input.buttons;
        for(auto value:input.analog) if(value>30) neutral=false;
        for(auto value:input.axes) if(value>8000 || value<-8000) neutral=false;
        if(!armed) {armed=neutral;return NFL2K5_ADDON_UI_CONSUMED;}
        const auto pressed=input.buttons&~previous_buttons;
        auto down=[&](size_t i){return input.analog[i]>30 && previous_analog[i]<=30;};
        const bool back=down(1);
        auto stick=[&](size_t index,int16_t value) {
            const int before=vertical[index];
            if(value>16000) vertical[index]=1;
            else if(value<-16000) vertical[index]=-1;
            else if(value>=-8000 && value<=8000) vertical[index]=0;
            return vertical[index]!=before ? vertical[index] : 0;
        };
        const int section=stick(0,input.axes[1]),scrolling=stick(1,input.axes[3]);
        if((pressed&2) || section<0 || down(7)) page=(page+1)%3;
        if((pressed&1) || section>0 || down(6)) page=(page+2)%3;
        if(scrolling>0) scroll[page]=std::max(0,scroll[page]-90);
        if(scrolling<0) scroll[page]=std::min(100000,scroll[page]+90);
        previous_buttons=input.buttons;
        std::copy(std::begin(input.analog),std::end(input.analog),previous_analog.begin());
        return back?NFL2K5_ADDON_UI_BACK:NFL2K5_ADDON_UI_CONSUMED;
    }
};
}
#endif
