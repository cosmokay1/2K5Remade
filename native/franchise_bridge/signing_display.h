#ifndef NFL2K5_SIGNING_DISPLAY_H
#define NFL2K5_SIGNING_DISPLAY_H
#include "protocol.h"
#include <algorithm>
#include <array>
#include <string>
#include <iomanip>
#include <sstream>
namespace franchise {
inline std::array<std::pair<double,std::string>,5> personality_priority_values(const nlohmann::json& personality) {
    std::array<std::pair<double,std::string>,5> priorities;
    const char* keys[]={"money","security","playing_time","winning","loyalty"};
    const char* labels[]={"pay","security","playing time","winning","loyalty"};
    for(size_t i=0;i<priorities.size();++i) {
        const auto& value=personality.at(keys[i]);
        if(!value.is_number() || value<0 || value>1) throw std::runtime_error("Invalid fictional priority");
        priorities[i]={value.get<double>(),labels[i]};
    }
    std::stable_sort(priorities.begin(),priorities.end(),[](const auto& a,const auto& b){return a.first>b.first;});
    return priorities;
}
inline std::string personality_priorities(const nlohmann::json& personality) {
    const auto priorities=personality_priority_values(personality);
    return "Priorities: "+priorities[0].second+" and "+priorities[1].second;
}
struct SigningDisplayText { std::string priorities,offer,history; };
inline SigningDisplayText signing_display(const nlohmann::json& response) {
    if(!response.at("error").is_null()) throw std::runtime_error("No valid signing context");
    const auto& result=response.at("result");
    if(result.contains("save_position") && result.at("write_authorized")==false) {
        if(result.at("state")=="cancelled") return {"","Journal signing was cancelled.","Original signing remains held."};
        const auto position=result.at("save_position").get<std::string>();
        if(position=="before") return {"","Waiting for the accepted contract to be saved.","Original signing remains held."};
        if(position=="candidate_after") return {"","Saved contract matches the proposal; settlement pending.","Original signing remains held."};
        if(position=="confirmed_after") return {"","Saved contract and ledger agree.","Game reload remains unverified. Signing remains held."};
        return {"","Save differs from the accepted signing. Recovery required.","Original signing remains held."};
    }
    if(result.contains("state") && result.at("state")=="settled" && result.at("write_authorized")==false)
        return {"","Saved contract reconciled with the ledger.","Game reload remains unverified. Signing remains held."};
    if(result.contains("state") && result.at("state")=="prepared" && result.at("write_authorized")==false)
        return {"","Accepted terms reserved. Signing remains held.","Game application and recovery are pending."};
    if(result.contains("signing_checkpoint")) {
        auto checkpoint=response;checkpoint["result"]=result.at("signing_checkpoint");
        auto text=signing_display(checkpoint);
        const auto outcome=result.at("outcome").get<std::string>();
        if(outcome=="accepted_proposal") text.offer="Player accepts the proposal. Signing remains held.";
        else if(outcome=="counteroffer") {
            const auto& counter=result.at("counter");
            long double total=counter.at("signing_bonus").get<int64_t>();
            for(const auto& salary:counter.at("salaries")) total+=salary.get<int64_t>();
            std::ostringstream label;
            label<<"Counter: "<<counter.at("salaries").size()<<" years, $"<<std::fixed<<std::setprecision(3)
                 <<total/1000000<<"M total. Signing remains held.";
            text.offer=label.str();
        }
        else if(outcome=="player_rejected") text.offer="Player rejected the offer. Signing remains held.";
        else if(outcome=="accounting_rejected") text.offer="Offer failed accounting checks. Signing remains held.";
        else throw std::runtime_error("Unsupported held negotiation outcome");
        const auto reason=result.at("reason").get<std::string>();
        size_t count=std::min<size_t>(reason.size(),140);
        while(count && count<reason.size() && (static_cast<unsigned char>(reason[count])&0xC0)==0x80) --count;
        text.history="Reason: "+reason.substr(0,count);
        for(auto& c:text.history) if(static_cast<unsigned char>(c)<32) c=' ';
        return text;
    }

    if(result.at("write_authorized")!=false || result.at("ai_authorized")!=false)
        throw std::runtime_error("Display cannot grant negotiation authority");
    const auto& personality=result.at("player_context").at("personality");
    SigningDisplayText text;
    text.priorities=personality_priorities(personality);
    text.offer="Offer preview unavailable.";
    if(result.contains("offer_context")) {
        const auto& offer=result.at("offer_context");
        const auto outcome=offer.at("outcome").get<std::string>();
        if(outcome=="eligible_preview") text.offer="Offer fits the supported cap and contract rules.";
        else if(outcome=="format_rejected") text.offer="Offer cannot use the supported modern contract rules.";
        else if(outcome=="accounting_rejected") text.offer="Offer is not eligible: "+offer.at("reason").get<std::string>();
        else throw std::runtime_error("Invalid offer preview");
    }
    text.history="Performance history unavailable.";
    if(result.contains("performance_context")) {
        const auto& history=result.at("performance_context").at("saved_history");
        if(!history.is_array()) throw std::runtime_error("Invalid saved history");
        if(!history.empty()) text.history="Saved performance records available; season attribution unverified.";
    }
    return text;
}
}
#endif
