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
        "receptions","receiving_yards","receiving_touchdowns","tackles","targets","pressures","qb_hits"};
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
struct ScreenStatRow {std::string label;std::vector<std::string> values;};
struct ScreenTable {std::string title;std::vector<std::string> columns;std::vector<ScreenStatRow> rows;};
inline std::string screen_profile(const nlohmann::json& evidence) {
    if(!evidence.contains("player_profile")) return "Contract negotiation";
    const auto& profile=evidence.at("player_profile");std::vector<std::string> parts;
    if(!profile.at("height_inches").is_null()) {const int height=profile.at("height_inches").get<int>();parts.push_back(std::to_string(height/12)+"'"+std::to_string(height%12)+"\"");}
    if(!profile.at("weight_pounds").is_null()) parts.push_back(std::to_string(profile.at("weight_pounds").get<int>())+" lb");
    if(!profile.at("age_years").is_null()) parts.push_back("Age "+std::to_string(profile.at("age_years").get<int>())+" at season start");
    std::string label;for(const auto& part:parts){if(!label.empty()) label+="  /  ";label+=part;}
    return label.empty()?"Physical profile unavailable":label;
}
inline std::string performance_year(const nlohmann::json& evidence,const nlohmann::json& entry) {
    if(!evidence.contains("franchise_season_year") || !evidence.contains("saved_display_year") ||
       !entry.contains("candidate_calendar_year") || entry.at("candidate_calendar_year").is_null()) return u8"\u2014";
    return std::to_string(evidence.at("franchise_season_year").get<int>()-
        evidence.at("saved_display_year").get<int>()+entry.at("candidate_calendar_year").get<int>());
}
inline std::vector<ScreenTable> performance_tables(const nlohmann::json& evidence) {
    std::vector<ScreenTable> tables;
    if(!evidence.contains("saved_history")) return tables;
    const auto& history=evidence.at("saved_history");
    for(const auto& row:history) screen_metric(row.at("metric").get<std::string>());
    for(const auto* field:{"missing_named_metrics","unmapped_requested_metrics"})
        if(evidence.contains(field)) for(const auto& metric:evidence.at(field)) screen_metric(metric.get<std::string>());
    struct Category {const char *title;std::vector<std::pair<std::string,std::string>> columns;};
    const Category categories[]={
        {"Receiving",{{"games","G"},{"receptions","REC"},{"receiving_yards","YDS"},{"receiving_touchdowns","TD"}}},
        {"Passing",{{"games","G"},{"completions","CMP"},{"pass_attempts","ATT"},{"passing_yards","YDS"},{"passing_touchdowns","TD"},{"interceptions_thrown","INT"}}},
        {"Rushing",{{"games","G"},{"rush_attempts","ATT"},{"rushing_yards","YDS"},{"rushing_touchdowns","TD"}}},
        {"Defense",{{"games","G"},{"sacks","SCK"}}}};
    for(const auto& category:categories) {
        bool present=false;
        for(const auto& entry:history) for(size_t col=1;col<category.columns.size();++col)
            if(entry.at("metric")==category.columns[col].first) present=true;
        if(!present) continue;
        ScreenTable table{category.title,{"YEAR"},{}};
        for(const auto& col:category.columns) table.columns.push_back(col.second);
        // Join only identical saved period/mode keys. Repeated metric entries get
        // their own row; never sum them or guess a different season/calendar.
        std::vector<std::pair<int,int>> keys;
        std::vector<std::vector<bool>> occupied;
        for(const auto& entry:history) {
            size_t col=0;
            while(col<category.columns.size() && entry.at("metric")!=category.columns[col].first) ++col;
            if(col==category.columns.size()) continue;
            const auto key=std::make_pair(entry.at("period_code_raw").get<int>(),entry.at("mode_code_raw").get<int>());
            size_t row=0;
            while(row<keys.size() && (keys[row]!=key || occupied[row][col])) ++row;
            if(row==keys.size()) {
                keys.push_back(key);occupied.push_back(std::vector<bool>(category.columns.size()));
                table.rows.push_back({performance_year(evidence,entry),std::vector<std::string>(category.columns.size(),u8"\u2014")});
            }
            occupied[row][col]=true;
            table.rows[row].values[col]=screen_number(entry.at("value"));
        }
        // A games-only period does not create a misleading empty category row.
        for(size_t row=table.rows.size();row-->0;) {
            bool has_stat=false;for(size_t col=1;col<occupied[row].size();++col) has_stat|=occupied[row][col];
            if(!has_stat) table.rows.erase(table.rows.begin()+row);
        }
        tables.push_back(std::move(table));
    }
    if(tables.empty()) {
        ScreenTable games{"Games played",{"YEAR","G"},{}};
        for(const auto& entry:history) if(entry.at("metric")=="games")
            games.rows.push_back({performance_year(evidence,entry),{screen_number(entry.at("value"))}});
        if(!games.rows.empty()) tables.push_back(std::move(games));
    }
    return tables;
}
inline ScreenTable contract_table(const nlohmann::json& context) {
    ScreenTable table{"Annual breakdown",{"YEAR","BASE SALARY","GUAR. BASE","BONUS CAP","CAP HIT"},{}};
    if(!context.contains("offer") || context.at("offer").is_null()) return table;
    const auto& offer=context.at("offer");const auto& salaries=offer.at("salaries");
    const bool preview=context.contains("preview") && !context.at("preview").is_null();
    for(size_t year=0;year<salaries.size();++year) {
        std::string bonus=u8"\u2014",charge=u8"\u2014";
        if(preview) {
            const auto& amount=context.at("preview").at("contract_charges").at(year);
            charge=amount.is_string()?"$"+amount.get<std::string>():screen_money(amount);
            // Only display a derived bonus charge when the authoritative preview
            // uses exact integer amounts; retain unknown for fractional charges.
            if(amount.is_number_integer() && salaries[year].is_number_integer())
                bonus=screen_money(amount.get<int64_t>()-salaries[year].get<int64_t>());
        }
        table.rows.push_back({"Year "+std::to_string(year+1),{screen_money(salaries[year]),
            offer.contains("guaranteed_salaries")?screen_money(offer.at("guaranteed_salaries").at(year)):u8"\u2014",bonus,charge}});
    }
    return table;
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
        const auto tables=performance_tables(checkpoint.at("performance_context"));
        if(tables.empty()) performance<<"No saved stats available for this player.\n";
        for(const auto& table:tables) {
            performance<<table.title<<"\nYEAR";
            for(size_t col=1;col<table.columns.size();++col) performance<<"  "<<table.columns[col];
            performance<<"\n";
            for(const auto& row:table.rows) {performance<<row.label;for(const auto& value:row.values) performance<<"  "<<value;performance<<"\n";}
            performance<<"\n";
        }
    } else performance<<"No saved stats available for this player.\n";
    performance<<u8"Saved history. \u2014 means not recorded.\n";
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
