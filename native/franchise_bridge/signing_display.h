#ifndef NFL2K5_SIGNING_DISPLAY_H
#define NFL2K5_SIGNING_DISPLAY_H
#include "protocol.h"
#include <algorithm>
#include <array>
#include <string>
namespace franchise {
struct SigningDisplayText { std::string priorities,offer,history; };
inline SigningDisplayText signing_display(const nlohmann::json& response) {
    if(!response.at("error").is_null()) throw std::runtime_error("No valid signing context");
    const auto& result=response.at("result");
    if(result.at("write_authorized")!=false || result.at("ai_authorized")!=false)
        throw std::runtime_error("Display cannot grant negotiation authority");
    const auto& personality=result.at("player_context").at("personality");
    std::array<std::pair<double,std::string>,5> priorities;
    const char* keys[]={"money","security","playing_time","winning","loyalty"};
    const char* labels[]={"pay","security","playing time","winning","loyalty"};
    for(size_t i=0;i<priorities.size();++i) {
        const auto& value=personality.at(keys[i]);
        if(!value.is_number() || value<0 || value>1) throw std::runtime_error("Invalid fictional priority");
        priorities[i]={value.get<double>(),labels[i]};
    }
    std::stable_sort(priorities.begin(),priorities.end(),[](const auto& a,const auto& b){return a.first>b.first;});
    SigningDisplayText text;
    text.priorities="Priorities: "+priorities[0].second+" and "+priorities[1].second;
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
