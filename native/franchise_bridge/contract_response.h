#pragma once
#include "protocol.h"
#include <charconv>
#include <limits>
#include <numeric>
#include <set>
#include <algorithm>
#include <map>
#include <cmath>

namespace franchise {
inline const nlohmann::json& validate_amendment_history(const nlohmann::json&,const std::string&,const std::string&,bool allow_empty_prior=false);
inline void promise_goals(const nlohmann::json& goals) {
    if (!goals.is_array()) throw std::runtime_error("Invalid promise terms");
    std::set<std::string> ids;
    const std::set<std::string> metrics = {"touches", "starts", "receiving_yards", "rushing_yards", "passing_yards", "team_wins"};
    for (const auto& goal : goals) {
        if (!goal.is_object() || goal.size() != 6) throw std::runtime_error("Invalid promise goal");
        for (const auto* field : {"goal_id", "metric", "window", "source"}) {
            if (!goal.at(field).is_string() || goal.at(field).get<std::string>().find_first_not_of(" \t\r\n") == std::string::npos)
                throw std::runtime_error("Missing promise identity or source");
        }
        if (!ids.insert(goal.at("goal_id").get<std::string>()).second || !metrics.count(goal.at("metric").get<std::string>()) ||
            !goal.at("target").is_number_integer() || goal.at("target") <= 0 ||
            !goal.at("importance").is_number_integer() || goal.at("importance") < 1 || goal.at("importance") > 100)
            throw std::runtime_error("Invalid promise metric or weight");
    }
}
inline void integer_money(const nlohmann::json& value) {
    if (!value.is_number_integer() || value < 0 ||
        (value.is_number_unsigned() && value.get<uint64_t>() > static_cast<uint64_t>(std::numeric_limits<int64_t>::max())))
        throw std::runtime_error("Invalid integer money");
}
inline void promise_circumstances(const nlohmann::json& history, const nlohmann::json& request) {
    if (!history.contains("circumstances")) return;
    const auto& records=history.at("circumstances");
    const auto nonblank=[](const nlohmann::json& value) {
        return value.is_string() && value.get<std::string>().find_first_not_of(" \t\r\n")!=std::string::npos;
    };
    if (!request.contains("team_id") || !nonblank(request.at("team_id")) ||
        history.at("player_id")!=request.at("player_id") || !records.is_array() || records.empty() ||
        !history.at("score").at("goals").is_array()) throw std::runtime_error("Invalid circumstance identity or coverage");
    std::set<std::string> windows,seen;
    for (const auto& goal:history.at("score").at("goals")) {
        if (!nonblank(goal.at("window"))) throw std::runtime_error("Missing scored promise window");
        windows.insert(goal.at("window").get<std::string>());
    }
    for (const auto& row:records) {
        if (!row.is_object() || row.size()!=12) throw std::runtime_error("Invalid circumstance shape");
        for (const auto* field:{"player_id","team_id","window","mode","source","coverage"})
            if (!nonblank(row.at(field))) throw std::runtime_error("Missing circumstance provenance");
        const auto window=row.at("window").get<std::string>();
        const auto mode=row.at("mode").get<std::string>();
        if (row.at("player_id")!=request.at("player_id") || row.at("team_id")!=request.at("team_id") ||
            !windows.count(window) || !seen.insert(window).second ||
            (mode!="played" && mode!="cpu_played" && mode!="fast_sim") || !row.at("complete_window").is_boolean())
            throw std::runtime_error("Foreign or invalid circumstance scope");
        bool unknown=false;
        for (const auto* field:{"total_games","available_games","injury_unavailable_games","coaching_dnp_games"}) {
            if (row.at(field).is_null()) unknown=true;
            else integer_money(row.at(field));
        }
        if (unknown ? !nonblank(row.at("unavailable_reason")) : !row.at("unavailable_reason").is_null())
            throw std::runtime_error("Invalid unknown circumstance reason");
        const auto& total=row.at("total_games"); const auto& available=row.at("available_games");
        const auto& injury=row.at("injury_unavailable_games"); const auto& coaching=row.at("coaching_dnp_games");
        if (!total.is_null()) {
            const auto limit=total.get<int64_t>();
            for (const auto* field:{"available_games","injury_unavailable_games","coaching_dnp_games"})
                if (!row.at(field).is_null() && row.at(field).get<int64_t>()>limit)
                    throw std::runtime_error("Circumstance exceeds total games");
            // Subtraction avoids overflow while checking disjoint nonnegative counts.
            for (const auto* first:{"available_games","coaching_dnp_games"})
                if (!row.at(first).is_null() && !injury.is_null() &&
                    row.at(first).get<int64_t>()>limit-injury.get<int64_t>())
                    throw std::runtime_error("Disjoint circumstances exceed total games");
        }
        if (!available.is_null() && !coaching.is_null() && coaching.get<int64_t>()>available.get<int64_t>())
            throw std::runtime_error("Coaching DNP exceeds available games");
    }
}
inline void exact_money(const nlohmann::json& value) {
    if (value.is_number_integer()) { integer_money(value); return; }
    if (!value.is_string()) throw std::runtime_error("Inexact response money");
    auto text = value.get<std::string>();
    auto slash = text.find('/');
    if (slash == std::string::npos) throw std::runtime_error("Invalid exact money");
    uint64_t numerator = 0, denominator = 0;
    auto first = std::from_chars(text.data(), text.data() + slash, numerator);
    auto second = std::from_chars(text.data() + slash + 1, text.data() + text.size(), denominator);
    if (first.ec != std::errc{} || second.ec != std::errc{} || first.ptr != text.data() + slash ||
        second.ptr != text.data() + text.size() || numerator == 0 || denominator <= 1 ||
        std::gcd(numerator, denominator) != 1 ||
        text != std::to_string(numerator) + "/" + std::to_string(denominator))
        throw std::runtime_error("Noncanonical exact money");
}
inline nlohmann::json canonical_offer(const nlohmann::json& offer) {
    if (!offer.is_object() || !(offer.size() == 3 || offer.size() == 4) ||
        !offer.contains("player_id") || !offer.contains("salaries") || !offer.contains("signing_bonus") ||
        (offer.size() == 4 && !offer.contains("guaranteed_salaries")) ||
        !offer["player_id"].is_string() || offer["player_id"].get<std::string>().empty() ||
        !offer["salaries"].is_array() || offer["salaries"].empty())
        throw std::runtime_error("Invalid response contract");
    for (const auto& salary : offer["salaries"]) integer_money(salary);
    integer_money(offer["signing_bonus"]);
    auto guarantees = offer.value("guaranteed_salaries", nlohmann::json::array());
    if (!guarantees.is_array()) throw std::runtime_error("Invalid guarantee terms");
    if (guarantees.empty()) for (size_t i = 0; i < offer["salaries"].size(); ++i) guarantees.push_back(0);
    if (guarantees.size() != offer["salaries"].size()) throw std::runtime_error("Guarantee term mismatch");
    for (size_t i = 0; i < guarantees.size(); ++i) {
        integer_money(guarantees[i]);
        if (guarantees[i] > offer["salaries"][i]) throw std::runtime_error("Guarantee exceeds base");
    }
    auto result = offer; result["guaranteed_salaries"] = guarantees; return result;
}
inline int64_t checked_money_sum(int64_t total, const nlohmann::json& value) {
    integer_money(value);
    const auto amount=value.get<int64_t>();
    if (amount>std::numeric_limits<int64_t>::max()-total) throw std::runtime_error("Money total overflow");
    return total+amount;
}
inline void restructure_cash_record(const nlohmann::json& cash) {
    if (!cash.is_object() || cash.size()!=6) throw std::runtime_error("Invalid allocated amendment cash");
    for (const auto* field : {"obligation_id","player_id","source"})
        if (!cash.at(field).is_string() || cash.at(field).get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
            throw std::runtime_error("Missing amendment cash identity");
    integer_money(cash.at("amount")); integer_money(cash.at("paid"));
    if (cash.at("paid")>cash.at("amount") || !cash.at("paid_components").is_array())
        throw std::runtime_error("Invalid amendment cash allocation");
    std::set<std::string> names;
    int64_t paid=0;
    for (const auto& row : cash.at("paid_components")) {
        if (!row.is_array() || row.size()!=2 || !row[0].is_string() || row[0].get<std::string>().empty() ||
            !names.insert(row[0].get<std::string>()).second) throw std::runtime_error("Invalid amendment payment component");
        paid=checked_money_sum(paid,row[1]);
    }
    if (paid!=cash.at("paid").get<int64_t>()) throw std::runtime_error("Amendment payments disagree");
}
inline bool target_receipt_mode(const nlohmann::json& result, const nlohmann::json& request) {
    if (!request.contains("receipt_format")) {
        if (result.contains("receipt_format")) throw std::runtime_error("Unexpected compact receipt mode");
        return false;
    }
    if (request.at("receipt_format")!="target_v1" || !result.contains("receipt_format") ||
        result.at("receipt_format")!="target_v1") throw std::runtime_error("Compact receipt mode mismatch");
    return true;
}
inline void target_financial(const nlohmann::json& financial, const char* lifecycle, const std::string& player) {
    if (!financial.is_object() || financial.size()!=4 || !financial.contains("revision") ||
        !financial.contains("charges") || !financial.contains("signed_players") ||
        !financial.at(lifecycle).is_object() || financial.at(lifecycle).size()!=1 || !financial.at(lifecycle).contains(player))
        throw std::runtime_error("Compact receipt has unrelated financial archives");
}
inline void target_cash(const nlohmann::json& cash, const nlohmann::json& target) {
    if (!cash.is_object() || cash.size()!=6 || !cash.at("obligations").is_array() || cash.at("obligations").size()!=1)
        throw std::runtime_error("Invalid compact cash coverage");
    restructure_cash_record(target);
    if (cash.at("obligations")[0].dump()!=target.dump()) throw std::runtime_error("Compact cash differs from target archive");
    integer_money(cash.at("revision"));
    for (const auto* field : {"nominal_total","paid_total","unpaid_total"}) integer_money(cash.at(field));
    const auto& other=cash.at("other_obligations");
    if (!other.is_object() || other.size()!=4) throw std::runtime_error("Invalid other-obligation summary");
    for (const auto* field : {"count","nominal_total","paid_total","unpaid_total"}) integer_money(other.at(field));
    if (other.at("paid_total")>other.at("nominal_total") || other.at("unpaid_total").get<int64_t>()!=
            other.at("nominal_total").get<int64_t>()-other.at("paid_total").get<int64_t>() ||
        (other.at("count")==0 && (other.at("nominal_total")!=0 || other.at("paid_total")!=0 || other.at("unpaid_total")!=0)))
        throw std::runtime_error("Other-obligation summary does not reconcile");
    const auto nominal=checked_money_sum(target.at("amount").get<int64_t>(),other.at("nominal_total"));
    const auto paid=checked_money_sum(target.at("paid").get<int64_t>(),other.at("paid_total"));
    const auto unpaid=checked_money_sum(target.at("amount").get<int64_t>()-target.at("paid").get<int64_t>(),other.at("unpaid_total"));
    if (cash.at("nominal_total")!=nominal || cash.at("paid_total")!=paid || cash.at("unpaid_total")!=unpaid)
        throw std::runtime_error("Compact target and other cash do not reconcile");
}
inline std::string generation_cash_identity(const nlohmann::json& value, const std::string& player) {
    if (!value.is_string()) throw std::runtime_error("Invalid saved agreement identity");
    const auto identity=value.get<std::string>();
    const std::string prefix=identity.rfind("contract-gen:",0)==0 ? "contract-gen:" : "legacy-contract:";
    if (identity.size()!=prefix.size()+64 || identity.compare(0,prefix.size(),prefix)!=0 ||
        identity.find_first_not_of("0123456789abcdef",prefix.size())!=std::string::npos)
        throw std::runtime_error("Invalid saved agreement identity");
    return prefix=="contract-gen:" ? identity : "contract:"+player;
}
inline void compact_release_cash(const nlohmann::json& archive, const std::string& player) {
    const auto& original=archive.at("original_cash");
    const auto& settled=archive.at("cash_obligation");
    restructure_cash_record(original); restructure_cash_record(settled);
    const auto identity=original.at("obligation_id").get<std::string>();
    if (identity!="contract:"+player) {
        if (identity.rfind("contract-gen:",0)!=0) throw std::runtime_error("Invalid released cash identity");
        generation_cash_identity(original.at("obligation_id"),player);
    }
    if (original.at("player_id")!=player || settled.at("player_id")!=player ||
        settled.at("obligation_id")!=original.at("obligation_id") || settled.at("amount")>original.at("amount") ||
        settled.at("paid")!=original.at("paid") || settled.at("paid_components").dump()!=original.at("paid_components").dump())
        throw std::runtime_error("Release changed original cash identity or payments");
}
inline void trade_cash_records(const nlohmann::json& archive, const std::string& player,
                               const std::string& source, const std::string& destination) {
    const auto& original=archive.at("original_cash");
    const auto& seller=archive.at("seller_cash");
    const auto& buyer=archive.at("buyer_cash");
    for (const auto* record : {&original,&seller,&buyer}) {
        restructure_cash_record(*record);
        if (record->at("player_id")!=player) throw std::runtime_error("Trade cash belongs to another player");
    }
    if (original.at("obligation_id")!=source || seller.at("obligation_id")!=source || buyer.at("obligation_id")!=destination ||
        checked_money_sum(seller.at("amount").get<int64_t>(),buyer.at("amount"))!=original.at("amount").get<int64_t>() ||
        seller.at("amount")!=seller.at("paid") || seller.at("paid")!=original.at("paid") ||
        seller.at("paid_components").dump()!=original.at("paid_components").dump() || buyer.at("paid")!=0)
        throw std::runtime_error("Trade changed cash identity, conservation or payment history");
}
inline void validate_contract_accounting(const nlohmann::json& accounting, const std::string& player) {
    if (accounting.is_null()) return; // Explicitly unavailable, never a zero balance.
    if (!accounting.is_object() || !(accounting.size()==6 ||
        (accounting.size()==7 && accounting.contains("generation_id")))) throw std::runtime_error("Invalid saved player accounting");
    const auto expected_cash=accounting.contains("generation_id") ?
        generation_cash_identity(accounting.at("generation_id"),player) : "contract:"+player;
    const auto status=accounting.at("status").get<std::string>();
    if ((status!="active" && status!="released" && status!="assigned") ||
        accounting.at("charge_scope")!=(status=="active" ? "active_contract" : "retained_obligations"))
        throw std::runtime_error("Invalid saved accounting lifecycle");
    const auto& contract=accounting.at("contract");
    if (!contract.is_object() || !(contract.size()==4 || (contract.size()==5 && contract.contains("bonus_layers"))) ||
        !contract.at("source").is_string() || contract.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
        throw std::runtime_error("Invalid saved contract source");
    const auto offer=canonical_offer(contract.at("offer"));
    if (offer.at("player_id")!=player) throw std::runtime_error("Foreign saved contract");
    integer_money(contract.at("elapsed_years")); integer_money(contract.at("bonus_years"));
    const auto elapsed=contract.at("elapsed_years").get<int64_t>();
    const auto term=offer.at("salaries").size();
    if (elapsed>=static_cast<int64_t>(term) || contract.at("bonus_years")<1 || contract.at("bonus_years")>5)
        throw std::runtime_error("Invalid saved contract allocation");
    const auto& charges=accounting.at("annual_charges");
    if (!charges.is_array() || charges.empty() || (status=="active" && charges.size()!=term-static_cast<size_t>(elapsed)))
        throw std::runtime_error("Invalid saved charge coverage");
    for (const auto& value : charges) exact_money(value);
    std::map<std::string,int64_t> ceilings{{"signing_bonus",offer.at("signing_bonus").get<int64_t>()}}, layers;
    for (size_t i=0;i<term;++i) ceilings["base:"+std::to_string(i)]=offer.at("salaries")[i].get<int64_t>();
    int64_t total_bonus=offer.at("signing_bonus").get<int64_t>();
    if (contract.contains("bonus_layers")) {
        if (!contract.at("bonus_layers").is_array()) throw std::runtime_error("Invalid saved bonus layers");
        for (const auto& layer : contract.at("bonus_layers")) {
            if (!layer.is_object() || layer.size()!=5 || !layer.at("record_id").is_string() ||
                layer.at("record_id").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos ||
                !layer.at("source").is_string() || layer.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
                throw std::runtime_error("Invalid saved bonus identity");
            integer_money(layer.at("amount")); integer_money(layer.at("original_start_index")); integer_money(layer.at("allocation_years"));
            const auto start=layer.at("original_start_index").get<int64_t>(), years=layer.at("allocation_years").get<int64_t>();
            if (layer.at("amount")==0 || start>=static_cast<int64_t>(term) || years<1 || years>5 ||
                years>static_cast<int64_t>(term)-start ||
                !layers.emplace("bonus:"+layer.at("record_id").get<std::string>(),layer.at("amount").get<int64_t>()).second)
                throw std::runtime_error("Invalid saved bonus allocation");
            total_bonus=checked_money_sum(total_bonus,layer.at("amount"));
        }
    }
    ceilings.insert(layers.begin(),layers.end());
    const auto& cash=accounting.at("cash_obligation");
    if (!cash.is_null()) {
        if (!cash.is_object() || !(cash.size()==5 || (cash.size()==6 && cash.contains("paid_components"))) ||
            cash.at("player_id")!=player || cash.at("obligation_id")!=expected_cash ||
            !cash.at("source").is_string() || cash.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
            throw std::runtime_error("Invalid saved cash identity");
        integer_money(cash.at("amount")); integer_money(cash.at("paid"));
        if (cash.at("paid")>cash.at("amount")) throw std::runtime_error("Saved cash overpayment");
        if (status=="active") {
            int64_t nominal=total_bonus;
            for (const auto& salary : offer.at("salaries")) nominal=checked_money_sum(nominal,salary);
            if (cash.at("amount")!=nominal) throw std::runtime_error("Active cash disagrees with compensation");
        } else if (status=="assigned" && cash.at("amount")!=cash.at("paid"))
            throw std::runtime_error("Assigned cash remains payable");
        if (cash.contains("paid_components")) {
            restructure_cash_record(cash);
            for (const auto& row : cash.at("paid_components")) {
                const auto found=ceilings.find(row[0].get<std::string>());
                if (found==ceilings.end() || row[1]>found->second) throw std::runtime_error("Saved payment exceeds compensation");
            }
        }
    }
    const auto& guarantees=accounting.at("guarantees");
    if (guarantees.is_null()) return; // Historical payment allocation may be unknown.
    if (!guarantees.is_object()) throw std::runtime_error("Invalid saved guarantees");
    const std::set<std::string> fields={"unpaid_guaranteed_base_by_original_year","unpaid_signing_bonus",
        "obligation_source","unpaid_bonus_layers","unpaid_original_signing_bonus"};
    for (auto field=guarantees.begin();field!=guarantees.end();++field)
        if (!fields.count(field.key())) throw std::runtime_error("Unknown saved guarantee field");
    const auto& bases=guarantees.at("unpaid_guaranteed_base_by_original_year");
    if (!bases.is_array() || bases.size()!=term) throw std::runtime_error("Invalid saved guarantee coverage");
    for (size_t i=0;i<term;++i) {
        integer_money(bases[i]);
        if (bases[i]>offer.at("guaranteed_salaries")[i] || (status=="assigned" && bases[i]!=0))
            throw std::runtime_error("Saved guarantee exceeds original protection");
    }
    integer_money(guarantees.at("unpaid_signing_bonus"));
    if (guarantees.at("unpaid_signing_bonus")>total_bonus || (status=="assigned" && guarantees.at("unpaid_signing_bonus")!=0))
        throw std::runtime_error("Invalid saved unpaid bonus");
    if (guarantees.contains("obligation_source") && (!guarantees.at("obligation_source").is_string() ||
        guarantees.at("obligation_source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos))
        throw std::runtime_error("Missing guarantee provenance");
    // Assigned archives may intentionally expose only settled aggregate debt.
    if (status=="assigned" && guarantees.size()==2) return;
    if (layers.empty()) {
        if (guarantees.contains("unpaid_bonus_layers") || guarantees.contains("unpaid_original_signing_bonus"))
            throw std::runtime_error("Unrelated saved bonus guarantees");
    } else {
        integer_money(guarantees.at("unpaid_original_signing_bonus"));
        int64_t unpaid=guarantees.at("unpaid_original_signing_bonus").get<int64_t>();
        const auto& unpaid_layers=guarantees.at("unpaid_bonus_layers");
        if (unpaid>offer.at("signing_bonus").get<int64_t>() || !unpaid_layers.is_object() || unpaid_layers.size()!=layers.size())
            throw std::runtime_error("Invalid saved unpaid bonus coverage");
        for (const auto& layer : layers) {
            const auto& amount=unpaid_layers.at(layer.first);
            integer_money(amount);
            if (amount>layer.second) throw std::runtime_error("Unpaid bonus exceeds original layer");
            unpaid=checked_money_sum(unpaid,amount);
        }
        if (unpaid!=guarantees.at("unpaid_signing_bonus")) throw std::runtime_error("Saved unpaid bonus total disagrees");
    }
}
inline void validate_assigned_calendar_cash(const nlohmann::json& archive, int64_t cursor) {
    const auto& contract=archive.at("contract");
    const auto offer=canonical_offer(contract.at("offer"));
    const auto term=static_cast<int64_t>(offer.at("salaries").size());
    if(cursor<contract.at("elapsed_years").get<int64_t>() || cursor>=term)
        throw std::runtime_error("Invalid assigned calendar cursor");
    std::map<std::string,int64_t> ceilings{{"signing_bonus",offer.at("signing_bonus").get<int64_t>()}};
    for(int64_t i=0;i<term;++i) ceilings["base:"+std::to_string(i)]=i<cursor ? offer.at("salaries")[i].get<int64_t>() : 0;
    if(contract.contains("bonus_layers"))
        for(const auto& layer:contract.at("bonus_layers"))
            ceilings["bonus:"+layer.at("record_id").get<std::string>()]=layer.at("amount").get<int64_t>();
    int64_t nominal=0;
    for(const auto& component:ceilings) nominal=checked_money_sum(nominal,component.second);
    const auto& cash=archive.at("cash_obligation");
    if(!cash.is_object() || !cash.contains("paid_components") || !cash.at("paid_components").is_array() ||
        cash.at("amount")!=nominal || cash.at("paid")!=nominal)
        throw std::runtime_error("Assigned calendar cash lacks settled compensation");
    std::map<std::string,int64_t> paid;
    for(const auto& row:cash.at("paid_components")) {
        const auto key=row[0].get<std::string>();
        const auto found=ceilings.find(key);
        if(found==ceilings.end() || row[1]>found->second)
            throw std::runtime_error("Assigned calendar payment exceeds retained compensation");
        paid[key]=row[1].get<int64_t>();
    }
    for(const auto& component:ceilings)
        if(paid[component.first]!=component.second)
            throw std::runtime_error("Assigned calendar compensation is unpaid");
    const auto& guarantees=archive.at("guarantees");
    if(!guarantees.is_object() || guarantees.at("unpaid_signing_bonus")!=0)
        throw std::runtime_error("Assigned calendar guarantees remain payable");
    for(const auto& amount:guarantees.at("unpaid_guaranteed_base_by_original_year"))
        if(amount!=0) throw std::runtime_error("Assigned base guarantee remains payable");
    if(guarantees.contains("unpaid_original_signing_bonus") && guarantees.at("unpaid_original_signing_bonus")!=0)
        throw std::runtime_error("Assigned original bonus remains payable");
    if(guarantees.contains("unpaid_bonus_layers"))
        for(const auto& amount:guarantees.at("unpaid_bonus_layers"))
            if(amount!=0) throw std::runtime_error("Assigned layer bonus remains payable");
}
inline void validate_calendar_contract_context(const nlohmann::json& result, const nlohmann::json& request,
                                              int64_t assigned_cursor=-1) {
    if(request.at("context_format")=="calendar_v4") {
        if(!result.is_object() || result.size()!=11 || !result.at("format").is_number_integer() || result.at("format")!=5)
            throw std::runtime_error("Invalid immutable contract calendar context");
        auto normalized=result;normalized.erase("original_contract");normalized.erase("amendment_history");normalized["format"]=4;
        auto expected=request;expected["context_format"]="calendar_v3";
        validate_calendar_contract_context(normalized,expected);
        const auto& archive=result.at("economic_archive");const auto& birth=result.at("original_contract");
        const auto& history=result.at("amendment_history");
        if(history.is_null()) {
            if(birth.dump()!=archive.at("contract").dump()) throw std::runtime_error("Missing economic amendment history");
        } else {
            const auto player=archive.at("contract").at("offer").at("player_id").get<std::string>();
            const auto& cash=archive.at("cash_obligation");
            if(cash.is_null()) throw std::runtime_error("Amendment cash provenance unavailable");
            const auto& latest=validate_amendment_history(history,player,cash.at("obligation_id").get<std::string>(),true);
            const auto& first=history.at("prior_restructures").empty()?latest:history.at("prior_restructures").at(0);
            auto original=birth;
            integer_money(original.at("elapsed_years"));
            if(first.at("original_contract").at("elapsed_years")<original.at("elapsed_years")) throw std::runtime_error("Amendment predates economic birth");
            original["elapsed_years"]=first.at("original_contract").at("elapsed_years");
            if(original.dump()!=first.at("original_contract").dump() || latest.at("contract").dump()!=archive.at("contract").dump())
                throw std::runtime_error("Immutable birth or effective amendment changed");
            const auto amendment_year=latest.at("scope").at("league_year").get<int64_t>();
            if(amendment_year>result.at("league_year").get<int64_t>() ||
                (archive.at("status")=="active" && result.at("calendar_accounting").at("anchor_year")!=amendment_year))
                throw std::runtime_error("Economic amendment calendar anchor changed");
            const auto& prior=latest.at("cash_obligation");
            std::map<std::string,int64_t> paid;
            for(const auto& row:cash.at("paid_components")) paid[row.at(0).get<std::string>()]=row.at(1).get<int64_t>();
            for(const auto& row:prior.at("paid_components")) if(paid[row.at(0).get<std::string>()]<row.at(1).get<int64_t>())
                throw std::runtime_error("Archived amendment payment disappeared");
            if(archive.at("status")=="active") {
                if(cash.at("amount")!=prior.at("amount") || cash.at("source")!=prior.at("source"))
                    throw std::runtime_error("Active amendment cash provenance changed");
            }
        }
        return;
    }
    if(request.at("context_format")=="calendar_v3") {
        if(!result.is_object() || result.size()!=9 || !result.at("format").is_number_integer() || result.at("format")!=4)
            throw std::runtime_error("Invalid assignment calendar context format");
        const auto& trade=result.at("trade_calendar");
        int64_t cursor=-1;
        if(!trade.is_null()) {
            const auto& archive=result.at("economic_archive");
            const auto& view=result.at("calendar_accounting");
            if(!trade.is_object() || trade.size()!=3 || archive.at("status")!="assigned" || view.at("status")!="assigned" ||
                !trade.at("source").is_string() || trade.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
                throw std::runtime_error("Invalid sourced assignment calendar");
            integer_money(trade.at("league_year"));integer_money(trade.at("elapsed_years"));
            cursor=trade.at("elapsed_years").get<int64_t>();
            if(trade.at("league_year")!=view.at("anchor_year") || trade.at("league_year")>result.at("league_year"))
                throw std::runtime_error("Assignment calendar year disagrees with cursor");
        }
        auto normalized=result;normalized.erase("trade_calendar");normalized["format"]=3;
        auto expected=request;expected["context_format"]="calendar_v2";
        validate_calendar_contract_context(normalized,expected,cursor);
        return;
    }
    if (request.at("context_format")=="calendar_v2") {
        if (!result.is_object() || result.size()!=8 || !result.at("format").is_number_integer() || result.at("format")!=3)
            throw std::runtime_error("Invalid release calendar context format");
        auto normalized=result; normalized.erase("release_calendar"); normalized["format"]=2;
        auto legacy_request=request; legacy_request["context_format"]="calendar_v1";
        validate_calendar_contract_context(normalized,legacy_request);
        const auto& release=result.at("release_calendar");
        const auto& archive=result.at("economic_archive");
        const auto& view=result.at("calendar_accounting");
        if(archive.at("status")=="assigned")
            validate_assigned_calendar_cash(archive,assigned_cursor<0 ?
                archive.at("contract").at("elapsed_years").get<int64_t>() : assigned_cursor);
        if (release.is_null() && archive.at("status")!="released") return;
        if (!release.is_null() && (!release.is_object() || release.size()!=3 || archive.at("status")!="released" ||
            view.at("status")!="released" || !release.at("source").is_string() ||
            release.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos))
            throw std::runtime_error("Invalid sourced release calendar");
        if (!release.is_null()) {
            integer_money(release.at("league_year")); integer_money(release.at("elapsed_years"));
        }
        const auto& contract=archive.at("contract");
        const auto offer=canonical_offer(contract.at("offer"));
        const auto cursor=(release.is_null() ? contract.at("elapsed_years") : release.at("elapsed_years")).get<int64_t>();
        const auto term=static_cast<int64_t>(offer.at("salaries").size());
        if (!release.is_null() && (release.at("league_year")!=view.at("anchor_year") ||
            release.at("league_year")>result.at("league_year") ||
            cursor<contract.at("elapsed_years").get<int64_t>() || cursor>=term))
            throw std::runtime_error("Release calendar disagrees with preserved contract");
        std::map<std::string,int64_t> ceilings{{"signing_bonus",offer.at("signing_bonus").get<int64_t>()}};
        for(int64_t i=0;i<term;++i)
            ceilings["base:"+std::to_string(i)]=(i<cursor ? offer.at("salaries")[i] : offer.at("guaranteed_salaries")[i]).get<int64_t>();
        if(contract.contains("bonus_layers"))
            for(const auto& layer:contract.at("bonus_layers"))
                ceilings["bonus:"+layer.at("record_id").get<std::string>()]=layer.at("amount").get<int64_t>();
        int64_t nominal=0;
        for(const auto& component:ceilings) nominal=checked_money_sum(nominal,component.second);
        const auto& cash=archive.at("cash_obligation");
        if(!cash.is_object() || !cash.contains("paid_components") || !cash.at("paid_components").is_array() || cash.at("amount")!=nominal)
            throw std::runtime_error("Release calendar cash disagrees with preserved liabilities");
        std::map<std::string,int64_t> paid;
        for(const auto& row:cash.at("paid_components")) {
            const auto key=row[0].get<std::string>();
            const auto found=ceilings.find(key);
            if(found==ceilings.end() || row[1]>found->second)
                throw std::runtime_error("Released payment exceeds calendar liability");
            paid[key]=row[1].get<int64_t>();
        }
        for(int64_t i=0;i<cursor;++i)
            if(paid["base:"+std::to_string(i)]!=ceilings.at("base:"+std::to_string(i)))
                throw std::runtime_error("Released calendar has unpaid prior base");
        const auto& guarantees=archive.at("guarantees");
        if(!guarantees.is_object()) throw std::runtime_error("Missing allocated release guarantees");
        for(int64_t i=0;i<term;++i) {
            auto remaining=std::max<int64_t>(0,offer.at("guaranteed_salaries")[i].get<int64_t>()-paid["base:"+std::to_string(i)]);
            if(guarantees.at("unpaid_guaranteed_base_by_original_year")[i]!=remaining)
                throw std::runtime_error("Release base guarantee disagrees with payments");
        }
        const auto original_unpaid=ceilings.at("signing_bonus")-paid["signing_bonus"];
        int64_t unpaid_bonus=original_unpaid;
        if(contract.contains("bonus_layers") && !contract.at("bonus_layers").empty()) {
            if(guarantees.at("unpaid_original_signing_bonus")!=original_unpaid)
                throw std::runtime_error("Release original bonus disagrees with payments");
            for(const auto& layer:contract.at("bonus_layers")) {
                auto key="bonus:"+layer.at("record_id").get<std::string>();
                auto remaining=ceilings.at(key)-paid[key];
                if(guarantees.at("unpaid_bonus_layers").at(key)!=remaining)
                    throw std::runtime_error("Release layer bonus disagrees with payments");
                unpaid_bonus=checked_money_sum(unpaid_bonus,remaining);
            }
        }
        if(guarantees.at("unpaid_signing_bonus")!=unpaid_bonus)
            throw std::runtime_error("Release bonus total disagrees with payments");
        return;
    }
    if (!request.at("context_format").is_string() || request.at("context_format")!="calendar_v1" ||
        !result.is_object() || result.size()!=7 || !result.at("format").is_number_integer() || result.at("format")!=2 ||
        result.at("team_id")!=request.at("team_id") || !result.at("team_id").is_string() ||
        result.at("generation_id")!=request.at("generation_id") || !result.at("generation_id").is_string())
        throw std::runtime_error("Invalid calendar agreement identity or format");
    integer_money(result.at("financial_revision")); integer_money(result.at("league_year"));
    const auto& archive=result.at("economic_archive");
    if (!archive.is_object() || archive.size()!=7 || archive.at("generation_id")!=result.at("generation_id"))
        throw std::runtime_error("Missing calendar economic archive");
    const auto player=archive.at("contract").at("offer").at("player_id").get<std::string>();
    validate_contract_accounting(archive,player);
    const auto& view=result.at("calendar_accounting");
    if (!view.is_object() || view.size()!=6 || !view.at("ownership_current").is_boolean())
        throw std::runtime_error("Invalid current calendar accounting");
    integer_money(view.at("anchor_year"));
    const auto anchor=view.at("anchor_year").get<int64_t>(), year=result.at("league_year").get<int64_t>();
    if (anchor<2020 || anchor>year || year>2030) throw std::runtime_error("Invalid calendar year cursor");
    const auto delta=static_cast<size_t>(year-anchor);
    const auto& charges=view.at("annual_charges");
    if (!charges.is_array()) throw std::runtime_error("Invalid current calendar charges");
    auto expected_charges=nlohmann::json::array();
    const auto& original_charges=archive.at("annual_charges");
    for (size_t i=delta;i<original_charges.size();++i) expected_charges.push_back(original_charges[i]);
    if (charges.dump()!=expected_charges.dump()) throw std::runtime_error("Calendar charges changed preserved schedule");
    const auto old_status=archive.at("status").get<std::string>(), status=view.at("status").get<std::string>();
    const auto& original=archive.at("contract");
    const auto elapsed=original.at("elapsed_years").get<int64_t>()+static_cast<int64_t>(delta);
    const auto term=static_cast<int64_t>(original.at("offer").at("salaries").size());
    if (old_status!="active") {
        if (status!=old_status || view.at("ownership_current")!=false ||
            !view.at("current_contract").is_null() || !view.at("expiry_source").is_null())
            throw std::runtime_error("Closed agreement gained calendar ownership or expiry");
    } else if (status=="active") {
        auto expected=original; expected["elapsed_years"]=elapsed;
        if (elapsed>=term || view.at("ownership_current")!=true || !view.at("expiry_source").is_null() ||
            view.at("current_contract").dump()!=expected.dump())
            throw std::runtime_error("Current contract disagrees with economic calendar cursor");
    } else if (status=="expired") {
        const auto& cash=archive.at("cash_obligation");
        if (elapsed<term || view.at("ownership_current")!=false || !view.at("current_contract").is_null() ||
            !view.at("expiry_source").is_string() ||
            view.at("expiry_source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos ||
            !cash.is_object() || !cash.contains("paid_components") || !cash.at("paid_components").is_array() ||
            cash.at("paid")!=cash.at("amount"))
            throw std::runtime_error("Expiry lacks exhausted term and allocated settlement");
        // Archive validation proves every allocation is bounded by its original
        // component; fully paid nominal compensation therefore settles them all.
        restructure_cash_record(cash);
    } else throw std::runtime_error("Invalid current calendar lifecycle");
}
inline void validate_amendment_history_plan(const nlohmann::json& plan,const std::string& player,const std::string& cash_id) {
    if(!plan.is_object() || plan.size()!=8) throw std::runtime_error("Invalid amendment history plan");
    const auto& scope=plan.at("scope");
    if(!scope.is_object() || scope.size()!=10) throw std::runtime_error("Invalid amendment history scope");
    integer_money(scope.at("league_year"));integer_money(scope.at("current_year_earned_base"));
    if(scope.at("league_year")<2020 || scope.at("league_year")>2030 || scope.at("current_year_earned_base")!=0)
        throw std::runtime_error("Invalid amendment history calendar or earnings");
    for(const auto* key:{"healthy","consent","renegotiation_eligible"})
        if(!scope.at(key).is_boolean() || scope.at(key)!=true) throw std::runtime_error("Missing amendment history eligibility");
    for(const auto* key:{"source","minimum_source"})
        if(!scope.at(key).is_string() || scope.at(key).get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
            throw std::runtime_error("Missing amendment history source");
    auto date_valid=[&](const nlohmann::json& value) {
        if(!value.is_string()) return false;
        const auto text=value.get<std::string>();
        if(text.size()!=10 || text[4]!='-' || text[7]!='-') return false;
        for(size_t i=0;i<text.size();++i) if(i!=4 && i!=7 && (text[i]<'0' || text[i]>'9')) return false;
        const int year=std::stoi(text.substr(0,4)),month=std::stoi(text.substr(5,2)),day=std::stoi(text.substr(8,2));
        const int days[]={0,31,28,31,30,31,30,31,31,30,31,30,31};
        return year==scope.at("league_year") && month>=1 && month<=12 && day>=1 &&
            day<=days[month]+(month==2 && year%4==0 && (year%100!=0 || year%400==0));
    };
    if(!date_valid(scope.at("amended_on")) || !date_valid(scope.at("first_regular_season_game")) ||
        scope.at("amended_on").get<std::string>()>=scope.at("first_regular_season_game").get<std::string>())
        throw std::runtime_error("Invalid amendment history dates");
    const std::set<std::string> required={"rookie_rules","salary_benefits","other_compensation","guarantee_offsets",
        "guarantee_voids","conditional_guarantees","extension","void_years","unpaid_old_bonus","deferred_new_bonus","injury_liability","grievance"};
    std::set<std::string> excluded;
    if(!scope.at("exclusions").is_array()) throw std::runtime_error("Missing amendment history exclusions");
    for(const auto& value:scope.at("exclusions"))
        if(!value.is_string() || !excluded.insert(value.get<std::string>()).second) throw std::runtime_error("Duplicate amendment history exclusion");
    if(excluded!=required) throw std::runtime_error("Incomplete amendment history exclusions");
    const auto& original=plan.at("original_contract");const auto& amended=plan.at("contract");
    if(!original.is_object() || !(original.size()==4 || (original.size()==5 && original.contains("bonus_layers"))) ||
        !amended.is_object() || amended.size()!=5) throw std::runtime_error("Invalid amendment history contract");
    for(const auto* contract:{&original,&amended}) {
        integer_money(contract->at("elapsed_years"));integer_money(contract->at("bonus_years"));
        if(contract->at("bonus_years")<1 || contract->at("bonus_years")>5 || !contract->at("source").is_string() ||
            contract->at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
            throw std::runtime_error("Invalid amendment history contract source or allocation");
    }
    auto before=canonical_offer(original.at("offer")),after=canonical_offer(amended.at("offer"));
    const auto cursor=original.at("elapsed_years").get<int64_t>();
    const auto term=before.at("salaries").size();
    integer_money(plan.at("converted_base"));const auto converted=plan.at("converted_base").get<int64_t>();
    if(before.at("player_id")!=player || after.at("player_id")!=player || cursor>=static_cast<int64_t>(term) || converted==0 ||
        scope.at("league_year").get<int64_t>()+static_cast<int64_t>(term)-cursor-1>2030)
        throw std::runtime_error("Invalid amendment history player, cursor or amount");
    const auto base=before.at("salaries")[cursor].get<int64_t>();
    if(before.at("guaranteed_salaries")[cursor]!=base || converted>base) throw std::runtime_error("Unprotected amendment history base");
    before["salaries"][cursor]=base-converted;before["guaranteed_salaries"][cursor]=base-converted;
    if(before.dump()!=after.dump()) throw std::runtime_error("Changed unrelated amendment history economics");
    const auto& layer=plan.at("bonus_layer");
    if(!layer.is_object() || layer.size()!=5 || !layer.at("record_id").is_string() ||
        layer.at("record_id").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos || layer.at("source")!=scope.at("source"))
        throw std::runtime_error("Invalid amendment history bonus source");
    for(const auto* key:{"amount","original_start_index","allocation_years"}) integer_money(layer.at(key));
    if(layer.at("amount")!=converted || layer.at("original_start_index")!=cursor ||
        layer.at("allocation_years")!=std::min<size_t>(term-static_cast<size_t>(cursor),5))
        throw std::runtime_error("Invalid amendment history bonus allocation");
    auto old_layers=original.contains("bonus_layers") ? original.at("bonus_layers") : nlohmann::json::array();
    if(!old_layers.is_array() || !amended.at("bonus_layers").is_array()) throw std::runtime_error("Invalid history layer arrays");
    std::map<std::string,int64_t> ceilings{{"signing_bonus",original.at("offer").at("signing_bonus").get<int64_t>()}};
    for(size_t i=0;i<term;++i) ceilings["base:"+std::to_string(i)]=original.at("offer").at("salaries")[i].get<int64_t>();
    std::set<std::string> layer_ids;
    for(const auto& old:old_layers) {
        if(!old.is_object() || old.size()!=5 || !old.at("record_id").is_string() ||
            !layer_ids.insert(old.at("record_id").get<std::string>()).second) throw std::runtime_error("Invalid prior history bonus identity");
        integer_money(old.at("amount"));integer_money(old.at("original_start_index"));integer_money(old.at("allocation_years"));
        if(old.at("amount")==0 || old.at("original_start_index")>cursor || old.at("allocation_years")<1 || old.at("allocation_years")>5 ||
            old.at("original_start_index").get<int64_t>()+old.at("allocation_years").get<int64_t>()>static_cast<int64_t>(term) ||
            !old.at("source").is_string() || old.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
            throw std::runtime_error("Invalid prior history bonus allocation");
        ceilings["bonus:"+old.at("record_id").get<std::string>()]=old.at("amount").get<int64_t>();
    }
    if(layer_ids.count(layer.at("record_id").get<std::string>())) throw std::runtime_error("Replaced existing history bonus");
    old_layers.push_back(layer);
    auto expected_contract=original;expected_contract["offer"]=after;expected_contract["bonus_layers"]=old_layers;
    expected_contract["source"]=original.at("source").get<std::string>()+"; base conversion: "+scope.at("source").get<std::string>();
    if(expected_contract.dump()!=amended.dump()) throw std::runtime_error("Changed history contract or prior bonus prefix");
    const auto& minimums=plan.at("annual_minimums");
    if(!minimums.is_array() || minimums.size()!=term-static_cast<size_t>(cursor)) throw std::runtime_error("Missing history salary floors");
    for(size_t i=0;i<minimums.size();++i) {
        integer_money(minimums[i]);if(minimums[i]==0 || after.at("salaries")[cursor+i]<minimums[i]) throw std::runtime_error("History salary below floor");
    }
    const auto& cash=plan.at("original_cash");const auto& settled=plan.at("cash_obligation");
    restructure_cash_record(cash);restructure_cash_record(settled);
    int64_t nominal=0;for(const auto& ceiling:ceilings) nominal=checked_money_sum(nominal,ceiling.second);
    if(cash.at("player_id")!=player || cash.at("obligation_id")!=cash_id || cash.at("amount")!=nominal)
        throw std::runtime_error("History cash disagrees with original compensation");
    auto expected_cash=cash;expected_cash["source"]=cash.at("source").get<std::string>()+"; base conversion: "+scope.at("source").get<std::string>();
    if(expected_cash.dump()!=settled.dump()) throw std::runtime_error("History conversion changed cash or paid allocations");
    std::map<std::string,int64_t> paid;
    for(const auto& row:cash.at("paid_components")) {
        const auto key=row[0].get<std::string>();
        if(!ceilings.count(key) || row[1]>ceilings.at(key)) throw std::runtime_error("History payment exceeds component");
        paid[key]=row[1].get<int64_t>();
    }
    for(const auto& ceiling:ceilings) {
        const auto& key=ceiling.first;
        if(key.rfind("base:",0)!=0 || std::stoull(key.substr(5))<static_cast<uint64_t>(cursor)) {
            if(paid[key]!=ceiling.second) throw std::runtime_error("History prior base or bonus unpaid");
        } else if(paid[key]!=0) throw std::runtime_error("History remaining base already paid");
    }
}

inline const nlohmann::json& validate_amendment_history(const nlohmann::json& history,const std::string& player,const std::string& cash_id,bool allow_empty_prior) {
    if(!history.is_object() || history.size()!=3 || !history.at("format").is_number_integer() || history.at("format")!=1 ||
        !history.at("prior_restructures").is_array() || (!allow_empty_prior && history.at("prior_restructures").empty()))
        throw std::runtime_error("Missing immutable prior amendment history");
    auto plans=history.at("prior_restructures");plans.push_back(history.at("latest_restructure"));
    std::set<std::string> ids;const nlohmann::json* previous=nullptr;
    for(const auto& plan:plans) {
        validate_amendment_history_plan(plan,player,cash_id);
        if(!ids.insert(plan.at("bonus_layer").at("record_id").get<std::string>()).second) throw std::runtime_error("Duplicate amendment history identity");
        if(!previous) {
            if(plan.at("original_contract").contains("bonus_layers") && !plan.at("original_contract").at("bonus_layers").empty())
                throw std::runtime_error("Incomplete original amendment history");
        } else {
            const auto delta=plan.at("scope").at("league_year").get<int64_t>()-previous->at("scope").at("league_year").get<int64_t>();
            auto original=previous->at("contract");
            original["elapsed_years"]=original.at("elapsed_years").get<int64_t>()+delta;
            if(delta<=0 || original.dump()!=plan.at("original_contract").dump()) throw std::runtime_error("History year/cursor or economics changed");
            const auto& before=previous->at("cash_obligation");const auto& after=plan.at("original_cash");
            if(before.at("amount")!=after.at("amount") || before.at("source")!=after.at("source")) throw std::runtime_error("History nominal cash/source changed");
            std::map<std::string,int64_t> paid;for(const auto& row:after.at("paid_components")) paid[row[0].get<std::string>()]=row[1].get<int64_t>();
            for(const auto& row:before.at("paid_components")) if(paid[row[0].get<std::string>()]<row[1].get<int64_t>()) throw std::runtime_error("History prior payment dropped");
        }
        previous=&plan;
    }
    return history.at("latest_restructure");
}

inline void validate_layered_calendar_restructure(const nlohmann::json& result,const nlohmann::json& request) {
    const bool compact=target_receipt_mode(result,request);
    const auto& receipt=result.at("restructure");
    if(!result.is_object() || result.size()!=(compact?6:5) || !receipt.is_object() || receipt.size()!=6 ||
        !receipt.at("format").is_number_integer() || receipt.at("format")!=3 ||
        result.at("team_id")!=request.at("team_id") || result.at("player_id")!=request.at("player_id") ||
        result.at("decision_mode")!="manual" || request.at("decision_mode")!="manual" ||
        result.at("generation_id")!=request.at("generation_id") || receipt.at("generation_id")!=request.at("generation_id"))
        throw std::runtime_error("Invalid repeated calendar amendment receipt");
    const auto player=request.at("player_id").get<std::string>();
    for(const auto* key:{"player_id","team_id","request_id"})
        if(!request.at(key).is_string() || request.at(key).get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
            throw std::runtime_error("Missing repeated amendment request identity");
    const auto cash_id=generation_cash_identity(request.at("generation_id"),player);
    integer_money(receipt.at("league_year"));integer_money(request.at("scope").at("league_year"));
    if(receipt.at("league_year")!=request.at("scope").at("league_year")) throw std::runtime_error("Repeated amendment year mismatch");
    const auto& financial=receipt.at("financial");const auto& cash=receipt.at("cash");
    integer_money(request.at("expected_revision"));integer_money(financial.at("revision"));
    const auto revision=request.at("expected_revision").get<int64_t>();
    if(revision==std::numeric_limits<int64_t>::max() || financial.at("revision")!=revision+1 ||
        !financial.at("signed_players").is_array() || !financial.at("charges").is_array() || financial.at("charges").empty())
        throw std::runtime_error("Invalid repeated amendment financial revision");
    std::set<std::string> owners;
    for(const auto& owner:financial.at("signed_players"))
        if(!owner.is_string() || !owners.insert(owner.get<std::string>()).second) throw std::runtime_error("Invalid repeated amendment ownership");
    if(!owners.count(player)) throw std::runtime_error("Repeated amendment removed ownership");
    for(const auto& charge:financial.at("charges")) exact_money(charge);
    if(compact) target_financial(financial,"restructures",player);
    else if(cash.contains("other_obligations")) throw std::runtime_error("Unmarked compact repeated cash");
    const auto& history=receipt.at("amendment_history");
    const auto& latest=validate_amendment_history(history,player,cash_id);
    auto scope=request.at("scope");std::sort(scope.at("exclusions").begin(),scope.at("exclusions").end());
    if(latest.dump()!=financial.at("restructures").at(player).dump() || latest.at("scope").dump()!=scope.dump() ||
        latest.at("converted_base")!=request.at("converted_base") ||
        latest.at("bonus_layer").at("record_id")!="calendar-layered-restructure:"+request.at("request_id").get<std::string>())
        throw std::runtime_error("Repeated amendment changed requested plan or history binding");
    integer_money(request.at("converted_base"));
    const auto& obligation=latest.at("cash_obligation");
    if(compact) {target_cash(cash,obligation);return;}
    if(!cash.is_object() || cash.size()!=6 || !cash.at("source").is_string() ||
        cash.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
        throw std::runtime_error("Invalid repeated full cash snapshot");
    integer_money(cash.at("revision"));integer_money(cash.at("nominal_total"));integer_money(cash.at("paid_total"));integer_money(cash.at("unpaid_total"));
    if(!cash.at("obligations").is_array() || cash.at("paid_total")>cash.at("nominal_total") ||
        cash.at("unpaid_total").get<int64_t>()!=cash.at("nominal_total").get<int64_t>()-cash.at("paid_total").get<int64_t>())
        throw std::runtime_error("Invalid repeated amendment cash totals");
    int64_t nominal=0,paid=0;size_t matched=0;std::set<std::string> cash_ids;
    for(const auto& record:cash.at("obligations")) {
        if(!record.is_object() || !(record.size()==5 || (record.size()==6 && record.contains("paid_components"))))
            throw std::runtime_error("Invalid repeated cash obligation shape");
        for(const auto* key:{"obligation_id","player_id","source"})
            if(!record.at(key).is_string() || record.at(key).get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
                throw std::runtime_error("Missing repeated cash obligation identity");
        if(record.contains("paid_components") && !record.at("paid_components").is_null()) restructure_cash_record(record);
        if(!cash_ids.insert(record.at("obligation_id").get<std::string>()).second) throw std::runtime_error("Duplicate repeated amendment cash");
        nominal=checked_money_sum(nominal,record.at("amount"));paid=checked_money_sum(paid,record.at("paid"));
        if(record.at("paid")>record.at("amount")) throw std::runtime_error("Repeated cash overpayment");
        if(record.at("obligation_id")==cash_id) {if(record.dump()!=obligation.dump()) throw std::runtime_error("Repeated cash archive mismatch");++matched;}
    }
    if(matched!=1 || nominal!=cash.at("nominal_total") || paid!=cash.at("paid_total")) throw std::runtime_error("Repeated cash reconciliation failed");
}

inline void validate_restructure(const nlohmann::json& result, const nlohmann::json& request) {
    if(request.contains("calendar_format") && request.at("calendar_format")=="calendar_v2") {
        validate_layered_calendar_restructure(result,request);return;
    }
    const bool compact=target_receipt_mode(result,request);
    const bool calendar=request.contains("calendar_format");
    const auto& receipt=result.at("restructure");
    if(calendar) {
        if(request.at("calendar_format")!="calendar_v1" || !request.contains("generation_id") ||
            !result.is_object() || result.size()!=(compact ? 6 : 5) || !receipt.is_object() || receipt.size()!=5 ||
            !receipt.at("format").is_number_integer() || receipt.at("format")!=2 ||
            receipt.at("generation_id")!=request.at("generation_id"))
            throw std::runtime_error("Invalid calendar amendment receipt format");
        integer_money(receipt.at("league_year"));integer_money(request.at("scope").at("league_year"));
        if(receipt.at("league_year")!=request.at("scope").at("league_year") || receipt.at("league_year")<2020 || receipt.at("league_year")>2030)
            throw std::runtime_error("Calendar amendment year mismatch");
    } else if(!receipt.is_object() || receipt.size()!=2 || result.contains("calendar_format"))
        throw std::runtime_error("Unexpected calendar amendment receipt");
    const auto player=request.at("player_id").get<std::string>();
    if (player.empty() || !request.at("team_id").is_string() || request.at("team_id").get<std::string>().empty() ||
        !request.at("request_id").is_string() || request.at("request_id").get<std::string>().empty() ||
        request.at("decision_mode")!="manual" || result.at("decision_mode")!="manual" ||
        result.at("team_id")!=request.at("team_id") || result.at("player_id")!=player)
        throw std::runtime_error("Invalid manual amendment identity");
    auto expected_cash="contract:"+player;
    if (request.contains("generation_id")) {
        expected_cash=generation_cash_identity(request.at("generation_id"),player);
        if (!result.contains("generation_id") || result.at("generation_id")!=request.at("generation_id"))
            throw std::runtime_error("Amendment changed agreement identity");
    } else if (result.contains("generation_id")) throw std::runtime_error("Unexpected amendment generation");
    const auto& financial=result.at("restructure").at("financial");
    const auto& cash=result.at("restructure").at("cash");
    integer_money(request.at("expected_revision")); integer_money(financial.at("revision"));
    const auto revision=request.at("expected_revision").get<int64_t>();
    if (revision==std::numeric_limits<int64_t>::max() || financial.at("revision")!=revision+1 ||
        !financial.at("charges").is_array() || financial.at("charges").empty() || !financial.at("signed_players").is_array())
        throw std::runtime_error("Invalid amendment posting");
    std::set<std::string> owners;
    for (const auto& owner : financial.at("signed_players"))
        if (!owner.is_string() || !owners.insert(owner.get<std::string>()).second) throw std::runtime_error("Invalid amendment ownership");
    if (!owners.count(player)) throw std::runtime_error("Amendment removed player ownership");
    for (const auto& charge : financial.at("charges")) exact_money(charge);
    const auto& archive=financial.at("restructures").at(player);
    if (compact) target_financial(financial,"restructures",player);
    else if (cash.contains("other_obligations")) throw std::runtime_error("Unmarked compact cash summary");
    if (!archive.is_object() || archive.size()!=8) throw std::runtime_error("Incomplete amendment archive");
    auto scope=request.at("scope");
    auto& exclusions=scope.at("exclusions");
    if (!exclusions.is_array() || !scope.at("source").is_string() ||
        scope.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
        throw std::runtime_error("Invalid amendment exclusions or source");
    std::set<std::string> excluded;
    for (const auto& item : exclusions)
        if (!item.is_string() || item.get<std::string>().empty() || !excluded.insert(item.get<std::string>()).second)
            throw std::runtime_error("Invalid amendment exclusion identity");
    std::sort(exclusions.begin(),exclusions.end());
    integer_money(request.at("converted_base")); integer_money(archive.at("converted_base"));
    const auto converted=request.at("converted_base").get<int64_t>();
    if (converted==0 || archive.at("converted_base")!=converted || archive.at("scope")!=scope)
        throw std::runtime_error("Response changed amendment inputs");
    const auto& original=archive.at("original_contract");
    const auto& amended=archive.at("contract");
    if (!original.is_object() || !(original.size()==4 || (original.size()==5 && original.contains("bonus_layers"))) ||
        !amended.is_object() || amended.size()!=5 ||
        (original.contains("bonus_layers") && (!original.at("bonus_layers").is_array() || !original.at("bonus_layers").empty())) ||
        !amended.at("bonus_layers").is_array() || amended.at("bonus_layers").size()!=1)
        throw std::runtime_error("Invalid original or amended bonus layers");
    for (const auto* contract : {&original,&amended}) {
        if (!contract->at("source").is_string() || contract->at("source").get<std::string>().empty())
            throw std::runtime_error("Missing amendment contract source");
        integer_money(contract->at("elapsed_years")); integer_money(contract->at("bonus_years"));
        if (contract->at("bonus_years")<1 || contract->at("bonus_years")>5) throw std::runtime_error("Invalid original bonus term");
    }
    auto before=canonical_offer(original.at("offer")), after=canonical_offer(amended.at("offer"));
    const auto elapsed=original.at("elapsed_years").get<int64_t>();
    if (before.at("player_id")!=player || after.at("player_id")!=player ||
        elapsed>=static_cast<int64_t>(before.at("salaries").size()) ||
        original.at("elapsed_years")!=amended.at("elapsed_years") || original.at("bonus_years")!=amended.at("bonus_years") ||
        before.at("salaries").size()!=after.at("salaries").size() || before.at("signing_bonus")!=after.at("signing_bonus"))
        throw std::runtime_error("Response changed original contract term");
    const auto index=static_cast<size_t>(elapsed), remaining=before.at("salaries").size()-index;
    const auto base=before.at("salaries")[index].get<int64_t>();
    if (before.at("guaranteed_salaries")[index]!=base || converted>base)
        throw std::runtime_error("Conversion exceeds protected original base");
    before["salaries"][index]=base-converted;
    before["guaranteed_salaries"][index]=base-converted;
    if (before!=after) throw std::runtime_error("Response changed unconverted salary or guarantee");
    const auto& layer=archive.at("bonus_layer");
    if (!layer.is_object() || layer.size()!=5 || amended.at("bonus_layers")[0]!=layer ||
        layer.at("record_id")!=(calendar ? "calendar-restructure:" : "restructure:")+request.at("request_id").get<std::string>() ||
        layer.at("source")!=scope.at("source")) throw std::runtime_error("Invalid converted bonus identity");
    integer_money(layer.at("amount")); integer_money(layer.at("original_start_index")); integer_money(layer.at("allocation_years"));
    if (layer.at("amount")!=converted || layer.at("original_start_index")!=elapsed ||
        layer.at("allocation_years")!=std::min<size_t>(remaining,5)) throw std::runtime_error("Invalid converted bonus allocation");
    const auto& minimums=archive.at("annual_minimums");
    if (!minimums.is_array() || minimums.size()!=remaining) throw std::runtime_error("Missing annual amendment floors");
    for (size_t i=0;i<remaining;++i) {
        integer_money(minimums[i]);
        if (minimums[i]==0 || after.at("salaries")[index+i]<minimums[i]) throw std::runtime_error("Amendment under annual floor");
    }
    const auto& original_cash=archive.at("original_cash");
    const auto& amended_cash=archive.at("cash_obligation");
    restructure_cash_record(original_cash); restructure_cash_record(amended_cash);
    if (original_cash.at("player_id")!=player || original_cash.at("obligation_id")!=expected_cash ||
        amended_cash.at("player_id")!=player || amended_cash.at("obligation_id")!=original_cash.at("obligation_id") ||
        amended_cash.at("amount")!=original_cash.at("amount") || amended_cash.at("paid")!=original_cash.at("paid") ||
        amended_cash.at("paid_components")!=original_cash.at("paid_components"))
        throw std::runtime_error("Amendment changed nominal cash or payments");
    auto original_offer=canonical_offer(original.at("offer"));
    int64_t nominal=original_offer.at("signing_bonus").get<int64_t>();
    for (const auto& salary : original_offer.at("salaries")) nominal=checked_money_sum(nominal,salary);
    if (original_cash.at("amount")!=nominal) throw std::runtime_error("Original nominal cash disagrees");
    for (const auto& row : original_cash.at("paid_components")) {
        const auto name=row[0].get<std::string>();
        int64_t ceiling=0;
        if (name=="signing_bonus") ceiling=original_offer.at("signing_bonus").get<int64_t>();
        else {
            if (name.rfind("base:",0)!=0) throw std::runtime_error("Unknown original payment component");
            uint64_t year=0; const auto number=name.substr(5);
            const auto parsed=std::from_chars(number.data(),number.data()+number.size(),year);
            if (parsed.ec!=std::errc{} || parsed.ptr!=number.data()+number.size() || number!=std::to_string(year) || year>=original_offer.at("salaries").size())
                throw std::runtime_error("Invalid original base payment index");
            ceiling=original_offer.at("salaries")[year].get<int64_t>();
            if (year>=index && row[1]!=0) throw std::runtime_error("Conversion includes paid remaining base");
        }
        if (row[1]>ceiling) throw std::runtime_error("Original payment exceeds compensation");
    }
    // Every past base and the old signing bonus must be settled before conversion.
    for (size_t i=0;i<=index;++i) {
        const auto name=i==index ? std::string("signing_bonus") : "base:"+std::to_string(i);
        const auto amount=i==index ? original_offer.at("signing_bonus") : original_offer.at("salaries")[i];
        nlohmann::json paid=0;
        for (const auto& row : original_cash.at("paid_components")) if (row[0]==name) paid=row[1];
        if (paid!=amount) throw std::runtime_error("Original bonus or past base remains unpaid");
    }
    integer_money(cash.at("revision")); integer_money(cash.at("nominal_total")); integer_money(cash.at("paid_total")); integer_money(cash.at("unpaid_total"));
    if (compact) { target_cash(cash,amended_cash); return; }
    if (!cash.at("obligations").is_array() || cash.at("paid_total")>cash.at("nominal_total") ||
        cash.at("unpaid_total").get<int64_t>()!=cash.at("nominal_total").get<int64_t>()-cash.at("paid_total").get<int64_t>())
        throw std::runtime_error("Invalid amendment cash totals");
    int64_t total=0,total_paid=0; size_t matched=0; std::set<std::string> obligations;
    for (const auto& record : cash.at("obligations")) {
        if (!record.is_object() || !record.at("obligation_id").is_string() || !obligations.insert(record.at("obligation_id").get<std::string>()).second)
            throw std::runtime_error("Duplicate amendment cash obligation");
        total=checked_money_sum(total,record.at("amount")); total_paid=checked_money_sum(total_paid,record.at("paid"));
        if (record.at("paid")>record.at("amount")) throw std::runtime_error("Cash payment exceeds obligation");
        if (record.at("obligation_id")==amended_cash.at("obligation_id")) {
            if (record!=amended_cash) throw std::runtime_error("Amended obligation differs from archive");
            ++matched;
        }
    }
    if (matched!=1 || total!=cash.at("nominal_total") || total_paid!=cash.at("paid_total"))
        throw std::runtime_error("Amendment cash posting disagrees with obligations");
}
/* Match observed original float32 stores and truncation, retaining every base
 * salary. Reject unsupported modern allocation rather than repair the bonus. */
inline int64_t guest_money_scale(const std::string& format) {
    if(format=="original_fxg_v1") return 1;
    if(format=="softdrink_fxg_v1") return 4;
    throw std::runtime_error("Unsupported guest contract format");
}
inline nlohmann::json exact_guest_offer(const nlohmann::json& raw,const std::string& player,
                                       const std::string& format="original_fxg_v1") {
    const auto scale=guest_money_scale(format);
    integer_money(raw.at("amount_word")); integer_money(raw.at("flags_word"));
    if(raw.at("amount_word")<1 || raw.at("amount_word")>65535 || raw.at("flags_word")>4294967295ULL)
        throw std::runtime_error("Unsupported guest offer words");
    const auto amount=raw.at("amount_word").get<int64_t>();
    const auto flags=raw.at("flags_word").get<uint32_t>();
    const unsigned years=(flags>>16)&15u, bonus=flags&15u, shape=(flags>>29)&7u;
    if(!years || bonus>10 || (bonus && years>5) || (amount*bonus)%years)
        throw std::runtime_error("Unsupported modern guest bonus allocation");
    const int64_t average=static_cast<int64_t>(static_cast<float>(static_cast<double>(amount)*10/years));
    const int64_t base=average-amount*bonus/years;
    nlohmann::json salaries=nlohmann::json::array(),guarantees=nlohmann::json::array();
    for(unsigned i=0;i<years;++i) {
        int64_t salary=base;
        const double position=i+0.5, midpoint=years*0.5;
        if(shape==0 || shape==7) {
            int factor=position<midpoint?12:position>midpoint?8:10;
            if(shape==7) factor=20-factor;
            salary=base*factor/10;
        } else if(shape==1 || shape==6) {
            const float fraction=static_cast<float>(2*(position/years)-1);
            const int direction=shape==1?-1:1;
            salary=static_cast<int64_t>(static_cast<float>(base+direction*static_cast<double>(base/2)*fraction));
        } else if((shape==3 || shape==4) && years>1) {
            const double offset=position<=midpoint?position:position-midpoint;
            const float fraction=static_cast<float>(2*offset/midpoint-1);
            int direction=position<=midpoint?1:-1;
            if(shape==4) direction=-direction;
            salary=static_cast<int64_t>(static_cast<float>(base+direction*static_cast<double>(base/2)*fraction));
        } else if(shape==5 && years>1) salary=base*(i%2==0?12:8)/10;
        salaries.push_back(salary*1000*scale); guarantees.push_back(0);
    }
    return {{"player_id",player},{"salaries",salaries},{"signing_bonus",amount*bonus*1000*scale},{"guaranteed_salaries",guarantees}};
}
inline void validate_result(const nlohmann::json& response, const nlohmann::json& request) {
    if (!response["error"].is_null()) return;
    const auto& result = response["result"];
    auto operation = request.at("operation").get<std::string>();
    if(operation=="guest_signing_status" || operation=="guest_signing_confirm") {
        auto hex=[](const nlohmann::json& value,size_t size) {
            if(!value.is_string()) return false;
            const auto text=value.get<std::string>();
            return text.size()==size && text.find_first_not_of("0123456789abcdef")==std::string::npos;
        };
        const bool live=operation=="guest_signing_status" &&
            (request.contains("live_finance_sha256") || request.contains("live_identity_sha256"));
        if(!result.is_object() || result.size()!=(live?8u:7u) || result.at("request_id")!=request.at("journal_request_id") ||
           result.at("write_authorized")!=false) throw std::runtime_error("Invalid saved-signing identity or authority");
        if(live && (!hex(request.at("live_finance_sha256"),64) || !hex(request.at("live_identity_sha256"),64) ||
                    !result.at("live_application_matches").is_boolean()))
            throw std::runtime_error("Invalid live application observation");
        if(operation=="guest_signing_confirm") {
            if(result.at("state")!="settled" || !hex(result.at("player_id"),32) ||
               !hex(result.at("after_payload_sha256"),64) || result.at("after_payload_sha256")!=request.at("expected_after_sha256") ||
               !result.at("charges").is_array() || result.at("charges").empty() || result.at("charges").size()>15)
                throw std::runtime_error("Invalid saved-signing confirmation");
            integer_money(result.at("financial_revision"));
            if(result.at("financial_revision")==0) throw std::runtime_error("Missing signing revision");
            for(const auto& charge:result.at("charges")) exact_money(charge);
            return;
        }
        const auto state=result.at("state").get<std::string>();
        const auto position=result.at("save_position").get<std::string>();
        const auto& current=result.at("current_payload_sha256");
        const auto& before=result.at("before_payload_sha256");
        const auto& after=result.at("after_payload_sha256");
        if(!hex(current,64) || !hex(before,64) ||
           (state!="prepared" && state!="settled" && state!="cancelled") ||
           (state=="settled" ? !hex(after,64) || after==before : !after.is_null()) ||
           (position!="before" && position!="candidate_after" && position!="confirmed_after" && position!="unrecognized") ||
           ((position=="before")!=(current==before)) ||
           (position=="candidate_after" && state!="prepared") ||
           (position=="confirmed_after" && (state!="settled" || current!=after)) ||
           (state=="settled" && current==after && position!="confirmed_after"))
            throw std::runtime_error("Invalid saved-signing recovery state or hashes");
        return;
    }
    if(operation=="guest_signing_prepare") {
        if(!result.is_object() || result.size()!=4 || result.at("request_id")!=request.at("request_id") ||
           result.at("state")!="prepared" || result.at("write_authorized")!=false ||
           result.at("before_payload_sha256")!=request.at("expected_before_sha256"))
            throw std::runtime_error("Invalid saved-signing preparation receipt");
        const auto hash=result.at("before_payload_sha256").get<std::string>();
        if(hash.size()!=64 || hash.find_first_not_of("0123456789abcdef")!=std::string::npos)
            throw std::runtime_error("Invalid saved-signing payload hash");
        return;
    }
    if(operation=="negotiate_proposal" && request.contains("observation")) {
        auto checkpoint_request=request;
        checkpoint_request["operation"]="signing_context";
        checkpoint_request["performance_format"]="saved_history_v1";
        checkpoint_request.erase("promise_goals");
        auto checkpoint_reply=response;
        checkpoint_reply["result"]=result.at("signing_checkpoint");
        validate_result(checkpoint_reply,checkpoint_request);
        const auto& checkpoint=checkpoint_reply.at("result");
        const auto& inspected=checkpoint.at("offer_context");
        if(inspected.at("outcome")!="eligible_preview" ||
            result.at("evidence").at("personality")!=checkpoint.at("player_context").at("personality") ||
            result.at("evidence").at("relationships")!=checkpoint.at("player_context").at("relationships") ||
            result.at("evidence").at("performance")!=checkpoint.at("performance_context"))
            throw std::runtime_error("Captured proposal source or eligibility mismatch");
        auto normalized=request;
        normalized.erase("observation");normalized.erase("guest_offer");
        normalized["team_id"]=checkpoint.at("team_id");
        normalized["offer"]=inspected.at("offer");
        normalized["contract_format"]=inspected.value("contract_format",std::string("original_fxg_v1"));
        auto proposal_reply=response;
        proposal_reply["result"].erase("signing_checkpoint");
        validate_result(proposal_reply,normalized);
        return;
    }
    if(result.contains("signing_checkpoint")) throw std::runtime_error("Unexpected captured signing checkpoint");
    if ((request.contains("receipt_format") || result.contains("receipt_format")) &&
        operation!="manual_restructure" && operation!="manual_trade" && operation!="manual_release")
        throw std::runtime_error("Unsupported compact receipt operation");
    if (operation == "manual_restructure") { validate_restructure(result,request); return; }
    if (operation == "manual_trade") {
        const bool compact=target_receipt_mode(result,request);
        const auto seller=request.at("seller").get<std::string>(), buyer=request.at("buyer").get<std::string>();
        const bool calendar=request.contains("calendar_format");
        const bool layered=calendar && request.at("calendar_format")=="calendar_v2";
        if(calendar) {
            if((!layered && request.at("calendar_format")!="calendar_v1") || !request.contains("seller_generation_id") ||
                !request.contains("buyer_previous_generation_id") || !result.is_object() || result.size()!=(layered ? (compact ? 13 : 12) : (compact ? 12 : 11)) ||
                result.at("calendar_format")!=request.at("calendar_format") || !result.at("format").is_number_integer() || result.at("format")!=(layered?3:2))
                throw std::runtime_error("Invalid calendar assignment receipt format");
            integer_money(result.at("league_year"));integer_money(request.at("scope").at("league_year"));
            if(result.at("league_year")!=request.at("scope").at("league_year") || result.at("league_year")<2020 || result.at("league_year")>2030)
                throw std::runtime_error("Calendar assignment year mismatch");
        } else if(result.contains("calendar_format") || result.contains("format") || result.contains("league_year"))
            throw std::runtime_error("Unexpected calendar assignment receipt");
        if (seller.empty() || buyer.empty() || seller == buyer || result.at("decision_mode") != "manual" ||
            result.at("seller") != seller || result.at("buyer") != buyer || result.at("player_id") != request.at("player_id"))
            throw std::runtime_error("Invalid manual assignment identity");
        if (request.contains("seller_generation_id")) {
            const auto source_cash=generation_cash_identity(request.at("seller_generation_id"),request.at("player_id").get<std::string>());
            if (!request.at("buyer_previous_generation_id").is_null())
                generation_cash_identity(request.at("buyer_previous_generation_id"),request.at("player_id").get<std::string>());
            if (!result.contains("seller_generation_id") || result.at("seller_generation_id")!=request.at("seller_generation_id") ||
                !result.contains("buyer_previous_generation_id") || result.at("buyer_previous_generation_id").dump()!=request.at("buyer_previous_generation_id").dump())
                throw std::runtime_error("Trade changed agreement participants");
            const auto destination_cash=generation_cash_identity(result.at("buyer_generation_id"),request.at("player_id").get<std::string>());
            if (result.at("buyer_generation_id").get<std::string>().rfind("contract-gen:",0)!=0)
                throw std::runtime_error("Trade failed to create destination agreement");
            const auto& outgoing=result.at("trade").at(seller).at("financial").at("outgoing_trades").at(request.at("player_id").get<std::string>());
            const auto& incoming=result.at("trade").at(buyer).at("financial").at("incoming_trades").at(request.at("player_id").get<std::string>());
            trade_cash_records(outgoing,request.at("player_id").get<std::string>(),source_cash,destination_cash);
            if (outgoing.dump()!=incoming.dump() || outgoing.at("original_cash").at("obligation_id")!=source_cash ||
                outgoing.at("seller_cash").at("obligation_id")!=source_cash || outgoing.at("buyer_cash").at("obligation_id")!=destination_cash)
                throw std::runtime_error("Trade changed agreement cash identity");
        } else if (result.contains("seller_generation_id") || result.contains("buyer_generation_id") || result.contains("buyer_previous_generation_id"))
            throw std::runtime_error("Unexpected versioned trade mode");
        const auto& postings=result.at("trade");
        if (!postings.is_object() || postings.size()!=2) throw std::runtime_error("Invalid paired assignment postings");
        auto scope=request.at("scope");
        auto& exclusions=scope.at("exclusions");
        if (!exclusions.is_array()) throw std::runtime_error("Invalid assignment exclusions");
        for (const auto& item : exclusions) if (!item.is_string()) throw std::runtime_error("Invalid assignment exclusion identity");
        std::sort(exclusions.begin(),exclusions.end());
        for (const auto& team : {seller,buyer}) {
            const auto& financial=postings.at(team).at("financial");
            const auto& cash=postings.at(team).at("cash");
            if(layered && financial.at("charges").empty()) throw std::runtime_error("Layered assignment omitted current cap obligations");
            const auto& expected_json=request.at(team==seller ? "seller_revision" : "buyer_revision");
            integer_money(expected_json); integer_money(financial.at("revision"));
            const auto expected=expected_json.get<int64_t>();
            if (expected==std::numeric_limits<int64_t>::max() || financial.at("revision")!=expected+1 ||
                !financial.at("charges").is_array() || !financial.at("signed_players").is_array())
                throw std::runtime_error("Invalid assignment revision or charges");
            size_t owner_count=0;
            for (const auto& player : financial.at("signed_players")) {
                if (!player.is_string()) throw std::runtime_error("Invalid assignment player list");
                if (player==request.at("player_id")) ++owner_count;
            }
            if (owner_count!=(team==buyer ? 1 : 0)) throw std::runtime_error("Invalid assigned player ownership");
            for (const auto& charge : financial.at("charges")) exact_money(charge);
            integer_money(cash.at("nominal_total")); integer_money(cash.at("paid_total")); integer_money(cash.at("unpaid_total"));
            if (cash.at("paid_total")>cash.at("nominal_total") || cash.at("unpaid_total").get<int64_t>() !=
                cash.at("nominal_total").get<int64_t>()-cash.at("paid_total").get<int64_t>())
                throw std::runtime_error("Invalid assigned cash totals");
            const auto& archive=financial.at(team==seller ? "outgoing_trades" : "incoming_trades").at(request.at("player_id").get<std::string>());
            if (compact) {
                target_financial(financial,team==seller ? "outgoing_trades" : "incoming_trades",request.at("player_id").get<std::string>());
                if (!request.contains("seller_generation_id"))
                    trade_cash_records(archive,request.at("player_id").get<std::string>(),
                        "contract:"+request.at("player_id").get<std::string>(),"contract:"+request.at("player_id").get<std::string>());
                const auto& target=archive.at(team==seller ? "seller_cash" : "buyer_cash");
                if (target.at("player_id")!=request.at("player_id")) throw std::runtime_error("Compact trade cash belongs to another player");
                target_cash(cash,target);
            } else if (cash.contains("other_obligations")) throw std::runtime_error("Unmarked compact cash summary");
            if(calendar && !compact) {
                const auto& target=archive.at(team==seller ? "seller_cash" : "buyer_cash");
                if(!cash.is_object() || cash.size()!=6 || !cash.at("source").is_string() || cash.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos) throw std::runtime_error("Invalid calendar assignment cash posting shape");
                integer_money(cash.at("revision"));
                if(!cash.at("obligations").is_array()) throw std::runtime_error("Missing calendar assignment cash inventory");
                std::set<std::string> ids;int64_t nominal=0,paid=0;size_t matched=0;
                for(const auto& record:cash.at("obligations")) {
                    restructure_cash_record(record);
                    const auto id=record.at("obligation_id").get<std::string>();
                    if(!ids.insert(id).second) throw std::runtime_error("Duplicate calendar assignment obligation");
                    nominal=checked_money_sum(nominal,record.at("amount"));paid=checked_money_sum(paid,record.at("paid"));
                    if(id==target.at("obligation_id")) {
                        if(record.dump()!=target.dump()) throw std::runtime_error("Calendar assignment target cash differs from archive");
                        ++matched;
                    }
                }
                if(matched!=1 || cash.at("nominal_total")!=nominal || cash.at("paid_total")!=paid)
                    throw std::runtime_error("Calendar assignment cash inventory disagrees");
            }
            if (archive.at("scope")!=scope || canonical_offer(archive.at("original_contract").at("offer")).at("player_id")!=request.at("player_id"))
                throw std::runtime_error("Response changed assignment source facts");
        }
        const auto player=request.at("player_id").get<std::string>();
        if (postings.at(seller).at("financial").at("outgoing_trades").at(player) !=
            postings.at(buyer).at("financial").at("incoming_trades").at(player))
            throw std::runtime_error("Paired assignment archives disagree");
        if(calendar) {
            const auto& archive=postings.at(seller).at("financial").at("outgoing_trades").at(player);
            const auto& original=archive.at("original_contract");
            if(layered) {
                const auto cash_id=generation_cash_identity(request.at("seller_generation_id"),player);
                const auto& latest=validate_amendment_history(result.at("amendment_history"),player,cash_id);
                const auto delta=result.at("league_year").get<int64_t>()-latest.at("scope").at("league_year").get<int64_t>();
                auto expected=latest.at("contract");
                expected["elapsed_years"]=expected.at("elapsed_years").get<int64_t>()+delta;
                if(delta<0 || expected.dump()!=original.dump()) throw std::runtime_error("Layered assignment changed source economic terms or cursor");
                if(!scope.at("traded_on").is_string() || (delta==0 && scope.at("traded_on").get<std::string>()<
                    latest.at("scope").at("amended_on").get<std::string>())) throw std::runtime_error("Layered assignment precedes latest amendment");
                const auto& previous_cash=latest.at("cash_obligation");const auto& current_cash=archive.at("original_cash");
                if(current_cash.at("player_id")!=player || current_cash.at("obligation_id")!=cash_id ||
                    current_cash.at("amount")!=previous_cash.at("amount") || current_cash.at("source")!=previous_cash.at("source"))
                    throw std::runtime_error("Layered assignment changed original nominal cash/source");
                std::map<std::string,int64_t> paid;
                for(const auto& row:current_cash.at("paid_components")) paid[row[0].get<std::string>()]=row[1].get<int64_t>();
                for(const auto& row:previous_cash.at("paid_components"))
                    if(paid[row[0].get<std::string>()]<row[1].get<int64_t>()) throw std::runtime_error("Layered assignment dropped prior payments");
                const auto& retained=archive.at("retained_bonus");
                const auto id="calendar-layered-trade:"+request.at("request_id").get<std::string>()+":seller-bonus";
                if(!retained.is_object() || retained.size()!=3 || retained.at("record_id")!=id ||
                    !retained.at("source").is_string() || retained.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
                    throw std::runtime_error("Layered assignment retained identity differs from request");
                if(request.at("request_id").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos ||
                    player.find_first_not_of(" \t\r\n")==std::string::npos)
                    throw std::runtime_error("Missing layered assignment identity");
            }
            auto offer=canonical_offer(original.at("offer"));
            integer_money(original.at("elapsed_years"));
            const auto cursor=original.at("elapsed_years").get<int64_t>();
            const auto term=static_cast<int64_t>(offer.at("salaries").size());
            if(cursor>=term) throw std::runtime_error("Calendar assignment exhausted source contract");
            auto bases=nlohmann::json::array(),guaranteed=nlohmann::json::array(),zeros=nlohmann::json::array();
            int64_t assigned=0;
            for(int64_t i=0;i<term;++i) {
                zeros.push_back(0);
                if(i>=cursor) {
                    bases.push_back(offer.at("salaries")[i]);guaranteed.push_back(offer.at("guaranteed_salaries")[i]);
                    assigned=checked_money_sum(assigned,offer.at("salaries")[i]);
                }
            }
            auto expected=offer;expected["salaries"]=bases;expected["guaranteed_salaries"]=guaranteed;expected["signing_bonus"]=0;
            const auto& incoming=archive.at("buyer_contract");
            integer_money(incoming.at("elapsed_years"));integer_money(incoming.at("bonus_years"));integer_money(archive.at("assigned_base"));
            if(!incoming.is_object() || !(incoming.size()==4 || (incoming.size()==5 && incoming.contains("bonus_layers"))) ||
                !incoming.at("source").is_string() || incoming.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
                throw std::runtime_error("Invalid calendar assignment receiving contract");
            if(canonical_offer(incoming.at("offer")).dump()!=expected.dump() || incoming.at("elapsed_years")!=0 ||
                incoming.at("bonus_years").dump()!=original.at("bonus_years").dump() ||
                (incoming.contains("bonus_layers") && (!incoming.at("bonus_layers").is_array() || !incoming.at("bonus_layers").empty())) ||
                archive.at("buyer_cash").at("amount")!=assigned || archive.at("assigned_base")!=assigned)
                throw std::runtime_error("Calendar assignment changed transferred compensation");
            auto accounting=nlohmann::json{{"generation_id",request.at("seller_generation_id")},{"status","assigned"},
                {"charge_scope","retained_obligations"},{"contract",original},
                {"annual_charges",archive.at("retained_bonus").at("annual_charges")},
                {"cash_obligation",archive.at("seller_cash")},
                {"guarantees",{{"unpaid_guaranteed_base_by_original_year",zeros},{"unpaid_signing_bonus",0}}}};
            validate_contract_accounting(accounting,player);
            validate_assigned_calendar_cash(accounting,cursor);
        }
        return;
    }
    if (operation == "manual_release") {
        const bool compact=target_receipt_mode(result,request);
        const auto& receipt=result.at("release");
        const bool calendar=request.contains("calendar_format");
        const bool layered=calendar && request.at("calendar_format")=="calendar_v2";
        if (calendar) {
            if ((!layered && request.at("calendar_format")!="calendar_v1") || !receipt.is_object() || receipt.size()!=(layered?6:5) ||
                !receipt.at("format").is_number_integer() || receipt.at("format")!=(layered?3:2) ||
                receipt.at("generation_id")!=request.at("generation_id") ||
                receipt.at("league_year")!=request.at("scope").at("league_year"))
                throw std::runtime_error("Invalid calendar release receipt identity");
            integer_money(receipt.at("league_year"));
            if (receipt.at("league_year")<2020 || receipt.at("league_year")>2030)
                throw std::runtime_error("Invalid calendar release year");
        } else if (receipt.contains("format") || receipt.contains("generation_id") || receipt.contains("league_year"))
            throw std::runtime_error("Unrequested calendar release receipt");
        if (result.at("decision_mode") != "manual" || result.at("player_id") != request.at("player_id"))
            throw std::runtime_error("Invalid manual release identity");
        const auto& financial=result.at("release").at("financial");
        const auto& cash=result.at("release").at("cash");
        integer_money(financial.at("revision"));
        integer_money(request.at("expected_revision"));
        const auto expected=request.at("expected_revision").get<int64_t>();
        if (expected == std::numeric_limits<int64_t>::max() || financial.at("revision") != expected+1 ||
            !financial.at("signed_players").is_array() || !financial.at("charges").is_array())
            throw std::runtime_error("Invalid release posting");
        for (const auto& player : financial.at("signed_players"))
            if (!player.is_string() || player == request.at("player_id")) throw std::runtime_error("Released player remains owned");
        for (const auto& charge : financial.at("charges")) exact_money(charge);
        const auto& archive=financial.at("released_contracts").at(request.at("player_id").get<std::string>());
        if(layered) {
            const auto player=request.at("player_id").get<std::string>();
            const auto identity=generation_cash_identity(request.at("generation_id"),player);
            // Release responses use the existing decision/player/receipt shape;
            // the exact generation is bound inside the versioned receipt.
            if(!result.is_object() || result.size()!=(compact?4:3)) throw std::runtime_error("Invalid layered release target identity");
            if(financial.at("charges").empty()) throw std::runtime_error("Layered release omitted current cap obligations");
            for(const auto* key:{"player_id","team_id","request_id"})
                if(!request.at(key).is_string() || request.at(key).get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
                    throw std::runtime_error("Missing layered release request identity");
            const auto& latest=validate_amendment_history(receipt.at("amendment_history"),player,identity);
            const auto year=receipt.at("league_year").get<int64_t>();
            const auto delta=year-latest.at("scope").at("league_year").get<int64_t>();
            if(!request.at("scope").at("removed_on").is_string() ||
                (delta==0 && request.at("scope").at("removed_on").get<std::string>()<
                    latest.at("scope").at("amended_on").get<std::string>()))
                throw std::runtime_error("Layered release precedes latest amendment");
            auto contract=latest.at("contract");
            contract["elapsed_years"]=contract.at("elapsed_years").get<int64_t>()+delta;
            if(delta<0 || contract.dump()!=archive.at("original_contract").dump())
                throw std::runtime_error("Layered release changed amendment economics or calendar cursor");
            const auto& old_cash=latest.at("cash_obligation");const auto& original_cash=archive.at("original_cash");
            restructure_cash_record(original_cash);
            if(original_cash.at("obligation_id")!=identity || original_cash.at("player_id")!=player ||
                original_cash.at("amount")!=old_cash.at("amount") || original_cash.at("source")!=old_cash.at("source"))
                throw std::runtime_error("Layered release changed inherited nominal cash or source");
            std::map<std::string,int64_t> paid;
            for(const auto& row:original_cash.at("paid_components")) paid[row[0].get<std::string>()]=row[1].get<int64_t>();
            for(const auto& row:old_cash.at("paid_components"))
                if(paid[row[0].get<std::string>()]<row[1].get<int64_t>()) throw std::runtime_error("Layered release dropped prior payments");
            const auto offer=canonical_offer(contract.at("offer"));const auto cursor=contract.at("elapsed_years").get<int64_t>();
            if(cursor>=static_cast<int64_t>(offer.at("salaries").size())) throw std::runtime_error("Layered release exhausted contract");
            std::map<std::string,int64_t> ceilings{{"signing_bonus",offer.at("signing_bonus").get<int64_t>()}};
            int64_t cancelled=0;
            for(size_t i=0;i<offer.at("salaries").size();++i) {
                const auto key="base:"+std::to_string(i);
                const auto& salary=offer.at("salaries")[i];
                ceilings[key]=salary.get<int64_t>();
                if(paid[key]!=(static_cast<int64_t>(i)<cursor ? salary.get<int64_t>() : 0))
                    throw std::runtime_error("Layered release past/current base payment mismatch");
                if(static_cast<int64_t>(i)>=cursor)
                    cancelled=checked_money_sum(cancelled,salary.get<int64_t>()-offer.at("guaranteed_salaries")[i].get<int64_t>());
            }
            integer_money(archive.at("cancelled_unearned_base"));
            if(archive.at("cancelled_unearned_base")!=cancelled) throw std::runtime_error("Layered release cancellation changed guaranteed liabilities");
            for(const auto& layer:contract.at("bonus_layers")) ceilings["bonus:"+layer.at("record_id").get<std::string>()]=layer.at("amount").get<int64_t>();
            for(const auto& row:original_cash.at("paid_components")) {
                const auto key=row[0].get<std::string>();
                if(!ceilings.count(key) || row[1]>ceilings.at(key)) throw std::runtime_error("Layered release payment exceeds source compensation");
            }
            const auto& retained=archive.at("retained");
            const auto prefix="calendar-layered-release:"+request.at("request_id").get<std::string>();
            if(!retained.is_array() || retained.size()!=2 || retained[0].at("record_id")!=prefix+":bonus" || retained[1].at("record_id")!=prefix+":base")
                throw std::runtime_error("Layered release retained identity differs from request");
            for(const auto& record:retained) {
                if(!record.is_object() || record.size()!=3 || !record.at("source").is_string() ||
                    record.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos ||
                    !record.at("annual_charges").is_array() || record.at("annual_charges").empty())
                    throw std::runtime_error("Invalid layered retained charge record");
                for(const auto& charge:record.at("annual_charges")) exact_money(charge);
            }
        }
        if (calendar) {
            const auto player=request.at("player_id").get<std::string>();
            const auto identity=generation_cash_identity(request.at("generation_id"),player);
            compact_release_cash(archive,player);
            if (archive.at("cash_obligation").at("obligation_id")!=identity)
                throw std::runtime_error("Calendar release belongs to another agreement");
            const auto& original=archive.at("original_contract");
            const auto offer=canonical_offer(original.at("offer"));
            integer_money(original.at("elapsed_years"));
            const auto cursor=original.at("elapsed_years").get<int64_t>();
            if (cursor>=static_cast<int64_t>(offer.at("salaries").size())) throw std::runtime_error("Invalid calendar release salary cursor");
            std::map<std::string,int64_t> ceilings{{"signing_bonus",offer.at("signing_bonus").get<int64_t>()}};
            for(size_t i=0;i<offer.at("salaries").size();++i)
                ceilings["base:"+std::to_string(i)]=(static_cast<int64_t>(i)<cursor ? offer.at("salaries")[i] : offer.at("guaranteed_salaries")[i]).get<int64_t>();
            if(original.contains("bonus_layers")) for(const auto& layer:original.at("bonus_layers")) {
                const auto key="bonus:"+layer.at("record_id").get<std::string>();
                integer_money(layer.at("amount"));
                if(!ceilings.emplace(key,layer.at("amount").get<int64_t>()).second) throw std::runtime_error("Duplicate calendar release bonus");
            }
            int64_t nominal=0;for(const auto& component:ceilings) nominal=checked_money_sum(nominal,component.second);
            const auto& target=archive.at("cash_obligation");
            if(target.at("amount")!=nominal) throw std::runtime_error("Calendar release changed retained nominal cash");
            std::map<std::string,int64_t> allocated;
            for(const auto& row:target.at("paid_components")) {
                const auto key=row[0].get<std::string>();auto found=ceilings.find(key);
                if(found==ceilings.end() || row[1]>found->second) throw std::runtime_error("Calendar release payment exceeds liability");
                allocated[key]=row[1].get<int64_t>();
            }
            for(int64_t i=0;i<cursor;++i) if(allocated["base:"+std::to_string(i)]!=ceilings.at("base:"+std::to_string(i)))
                throw std::runtime_error("Calendar release has unpaid prior salary");
            if (!compact) {
                if (!cash.is_object() || cash.size()!=6 || !cash.at("source").is_string() || cash.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos) throw std::runtime_error("Invalid calendar release cash posting shape");
                integer_money(cash.at("revision"));
                if (!cash.at("obligations").is_array()) throw std::runtime_error("Missing calendar release cash records");
                std::set<std::string> identities;int64_t nominal=0,paid=0;bool found=false;
                for (const auto& row:cash.at("obligations")) {
                    restructure_cash_record(row);
                    const auto key=row.at("obligation_id").get<std::string>();
                    if (!identities.insert(key).second) throw std::runtime_error("Duplicate calendar release cash record");
                    nominal=checked_money_sum(nominal,row.at("amount"));paid=checked_money_sum(paid,row.at("paid"));
                    if (key==identity) {
                        if (row.dump()!=archive.at("cash_obligation").dump()) throw std::runtime_error("Calendar release cash differs from archive");
                        found=true;
                    }
                }
                if (!found || cash.at("nominal_total")!=nominal || cash.at("paid_total")!=paid)
                    throw std::runtime_error("Calendar release cash coverage mismatch");
            }
        }
        if (compact) {
            target_financial(financial,"released_contracts",request.at("player_id").get<std::string>());
            compact_release_cash(archive,request.at("player_id").get<std::string>());
            if (archive.at("cash_obligation").at("player_id")!=request.at("player_id")) throw std::runtime_error("Compact release cash belongs to another player");
            target_cash(cash,archive.at("cash_obligation"));
        } else if (cash.contains("other_obligations")) throw std::runtime_error("Unmarked compact cash summary");
        if (canonical_offer(archive.at("original_contract").at("offer")).at("player_id") != request.at("player_id"))
            throw std::runtime_error("Release archive identity mismatch");
        auto scope=request.at("scope");
        auto& exclusions=scope.at("exclusions");
        if (!exclusions.is_array()) throw std::runtime_error("Invalid release exclusions");
        for (const auto& item : exclusions)
            if (!item.is_string()) throw std::runtime_error("Invalid release exclusion identity");
        std::sort(exclusions.begin(),exclusions.end());
        if (archive.at("scope") != scope || archive.at("discount") != request.at("discount") ||
            archive.at("payment_year_offsets") != request.at("payment_year_offsets"))
            throw std::runtime_error("Response changed release facts or valuation inputs");
        integer_money(cash.at("nominal_total")); integer_money(cash.at("paid_total")); integer_money(cash.at("unpaid_total"));
        if (cash.at("paid_total") > cash.at("nominal_total") || cash.at("unpaid_total").get<int64_t>() !=
            cash.at("nominal_total").get<int64_t>()-cash.at("paid_total").get<int64_t>())
            throw std::runtime_error("Invalid retained cash posting");
        return;
    }
    if (operation == "contract_context") {
        if (request.contains("context_format")) {
            validate_calendar_contract_context(result,request);
            return;
        }
        if (!result.is_object() || result.size()!=4 || result.at("team_id")!=request.at("team_id") ||
            !result.at("team_id").is_string() || result.at("generation_id")!=request.at("generation_id") ||
            !result.at("generation_id").is_string()) throw std::runtime_error("Agreement context identity mismatch");
        integer_money(result.at("financial_revision"));
        const auto& accounting=result.at("accounting");
        if (!accounting.is_object() || accounting.at("generation_id")!=result.at("generation_id"))
            throw std::runtime_error("Missing requested agreement accounting");
        const auto player=accounting.at("contract").at("offer").at("player_id").get<std::string>();
        validate_contract_accounting(accounting,player);
        return;
    }
    if (operation == "signing_context") {
        const bool performance=request.contains("performance_format");
        const bool guest_offer=request.contains("guest_offer");
        if (performance && request.at("performance_format")!="saved_history_v1")
            throw std::runtime_error("Unsupported saved performance format");
        if (!result.is_object() || result.size()!=9+performance+guest_offer || result.at("write_authorized")!=false ||
            result.at("ai_authorized")!=false ||
            result.at("scope")!="matching saved legacy checkpoint; active franchise selection, cash/rookie obligations and write authorization remain unverified")
            throw std::runtime_error("Invalid signing checkpoint scope or authority");
        integer_money(request.at("expected_revision"));
        integer_money(result.at("financial_revision"));
        integer_money(result.at("source_slot"));
        if (result.at("financial_revision")!=request.at("expected_revision") ||
            result.at("source_slot")!=request.at("observation").at("biography").at("source_slot"))
            throw std::runtime_error("Signing checkpoint locator or revision mismatch");
        auto canonical_hex=[](const nlohmann::json& value,size_t size) {
            if (!value.is_string()) return false;
            const auto text=value.get<std::string>();
            return text.size()==size && text.find_first_not_of("0123456789abcdef")==std::string::npos;
        };
        if (!canonical_hex(result.at("player_id"),32) || !canonical_hex(result.at("saved_payload_sha256"),64))
            throw std::runtime_error("Invalid signing checkpoint identity or source");
        static const char* teams[]={"49ers","Bears","Bengals","Bills","Broncos","Browns","Buccaneers","Cardinals",
            "Chargers","Chiefs","Colts","Cowboys","Dolphins","Eagles","Falcons","Giants","Jaguars","Jets",
            "Lions","Packers","Panthers","Patriots","Raiders","Rams","Ravens","Redskins","Saints","Seahawks",
            "Steelers","Texans","Titans","Vikings"};
        const auto& observed=request.at("observation").at("team");
        integer_money(observed.at("table_index"));
        if (observed.at("table_mode")!=2 || observed.at("table_index")>=32 ||
            result.at("team_id")!=teams[observed.at("table_index").get<size_t>()])
            throw std::runtime_error("Signing checkpoint team mismatch");
        const auto& context=result.at("player_context");
        if (context.at("initialized")!=true || context.at("financial_revision")!=result.at("financial_revision"))
            throw std::runtime_error("Signing checkpoint context revision or initialization mismatch");
        auto nested_reply=response; nested_reply["result"]=context;
        nlohmann::json nested_request={{"operation","player_context"},{"player_id",result.at("player_id")},
                                      {"team_id",result.at("team_id")}};
        validate_result(nested_reply,nested_request);
        if (guest_offer) {
            const auto& raw=request.at("guest_offer");
            if (!raw.is_object() || raw.size()!=2) throw std::runtime_error("Invalid raw guest offer");
            integer_money(raw.at("amount_word")); integer_money(raw.at("flags_word"));
            if (raw.at("amount_word")>65535 || raw.at("flags_word")>4294967295ULL)
                throw std::runtime_error("Guest offer words out of range");
            const auto& terms=result.at("offer_context");
            const auto format=terms.value("contract_format",std::string("original_fxg_v1"));
            const auto scale=guest_money_scale(format);
            if (!terms.is_object() || terms.size()!=6+terms.contains("contract_format") || terms.at("amount_word")!=raw.at("amount_word") ||
                terms.at("flags_word")!=raw.at("flags_word")) throw std::runtime_error("Guest offer preview changed raw terms");
            const auto outcome=terms.at("outcome").get<std::string>();
            if (outcome=="format_rejected") {
                bool compatible=false;
                try{exact_guest_offer(raw,result.at("player_id").get<std::string>(),format);compatible=true;}catch(const std::exception&){}
                if(compatible) throw std::runtime_error("Compatible guest terms mislabeled as format rejection");
                if (!terms.at("offer").is_null() || !terms.at("preview").is_null())
                    throw std::runtime_error("Rejected guest format cannot expose an eligible offer");
            } else {
                const auto offer=canonical_offer(terms.at("offer"));
                if(offer!=exact_guest_offer(raw,result.at("player_id").get<std::string>(),format))
                    throw std::runtime_error("Guest salary schedule differs from raw terms");
                const auto flags=raw.at("flags_word").get<uint32_t>();
                const auto years=(flags>>16)&15u, bonus=flags&15u;
                if (offer.at("player_id")!=result.at("player_id") || !years || bonus>10 ||
                    (bonus && years>5) || offer.at("salaries").size()!=years ||
                    offer.at("signing_bonus")!=raw.at("amount_word").get<int64_t>()*bonus*1000*scale)
                    throw std::runtime_error("Decoded guest offer identity, term or bonus mismatch");
                for(const auto& guarantee:offer.at("guaranteed_salaries"))
                    if(guarantee!=0) throw std::runtime_error("Guest format cannot encode base guarantees");
                if(outcome=="eligible_preview") {
                    if(!terms.at("reason").is_null()) throw std::runtime_error("Eligible guest preview carries rejection");
                    nlohmann::json preview_request={{"operation","preview"},{"offer",offer},{"expected_revision",result.at("financial_revision")}};
                    nlohmann::json preview_reply={{"error",nullptr},{"result",terms.at("preview")}};
                    validate_result(preview_reply,preview_request);
                    const auto allocated=offer.at("signing_bonus").get<int64_t>()/years;
                    for(size_t i=0;i<years;++i)
                        if(terms.at("preview").at("contract_charges").at(i)!=offer.at("salaries").at(i).get<int64_t>()+allocated)
                            throw std::runtime_error("Guest preview charges differ from exact modern allocation");
                } else if(outcome!="accounting_rejected" || !terms.at("preview").is_null())
                    throw std::runtime_error("Unknown guest offer preview outcome");
            }
            if(outcome!="eligible_preview" && (!terms.at("reason").is_string() ||
                terms.at("reason").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos))
                throw std::runtime_error("Rejected guest offer needs a reason");
        } else if(result.contains("offer_context")) throw std::runtime_error("Unrequested guest offer preview");
        if (performance) {
            const auto& evidence=result.at("performance_context");
            integer_money(evidence.at("saved_display_year"));
            const std::string source="original-fxg:"+result.at("saved_payload_sha256").get<std::string>()+
                ":slot:"+std::to_string(result.at("source_slot").get<int64_t>());
            if (!evidence.is_object() || evidence.size()!=9 || evidence.at("player_id")!=result.at("player_id") ||
                evidence.at("source")!=source || evidence.at("saved_display_year")!=request.at("observation").at("calendar").at("display_year") ||
                evidence.at("scope")!="Saved historical counters only; calendar years are candidates. Raw modes are not played/CPU/fast-sim coverage. Entries are not summed and missing metrics are not zero. No current-week, salary-credit or promise-goal attribution." ||
                !evidence.at("history_present").is_boolean() ||
                evidence.at("unmapped_requested_metrics")!=nlohmann::json::array({"tackles","targets","pressures","qb_hits"}))
                throw std::runtime_error("Saved performance identity, source or scope mismatch");
            const std::map<std::string,std::string> units={{"games","count"},{"rush_attempts","count"},
                {"rushing_yards","yards"},{"rushing_touchdowns","count"},{"pass_attempts","count"},
                {"completions","count"},{"passing_yards","yards"},{"passing_touchdowns","count"},
                {"interceptions_thrown","count"},{"sacks","sacks"}};
            const auto& rows=evidence.at("saved_history");
            if (!rows.is_array() || (!evidence.at("history_present").get<bool>() && !rows.empty()))
                throw std::runtime_error("Invalid saved history presence");
            std::set<std::string> present,sources,missing;
            for (const auto& row:rows) {
                const auto metric=row.at("metric").get<std::string>();
                const auto unit=units.find(metric);
                if (unit==units.end() || !row.is_object() || row.size()!=(metric=="sacks"?9:7) || row.at("unit")!=unit->second)
                    throw std::runtime_error("Unsupported saved performance metric or fields");
                integer_money(row.at("period_code_raw")); integer_money(row.at("mode_code_raw"));
                if (row.at("period_code_raw")>31 || row.at("mode_code_raw")>1)
                    throw std::runtime_error("Invalid raw history filter");
                const auto& year=row.at("candidate_calendar_year");
                if (!year.is_null()) {
                    integer_money(year);
                    const auto saved=evidence.at("saved_display_year").get<int64_t>();
                    if (year.get<int64_t>()>saved || year.get<int64_t>()<saved-31 || row.at("period_code_raw")==0)
                        throw std::runtime_error("Invalid historical calendar candidate");
                }
                const auto entry_source=row.at("source").get<std::string>(), prefix=source+":entry:";
                const auto suffix=entry_source.size()>prefix.size()?entry_source.substr(prefix.size()):"";
                if (entry_source.compare(0,prefix.size(),prefix) || suffix.empty() ||
                    suffix.find_first_not_of("0123456789")!=std::string::npos || !sources.insert(entry_source).second)
                    throw std::runtime_error("Invalid or duplicated saved history source");
                const auto& value=row.at("value");
                if (metric=="sacks") {
                    integer_money(row.at("raw_half_sack_units"));
                    if (row.at("raw_half_sack_units")>32767 || !value.is_number() ||
                        !std::isfinite(value.get<double>()) || value.get<double>()!=row.at("raw_half_sack_units").get<double>()/2 ||
                        row.at("mapping_scope")!="historical sack mapping inferred from descriptor and Gildon NFL corroboration; live updates/coverage unverified")
                        throw std::runtime_error("Invalid inferred half-sack history");
                } else {
                    if (!value.is_number_integer() || value < (unit->second=="yards"?-32768:0) || value>32767)
                        throw std::runtime_error("Invalid historical counter value");
                }
                present.insert(metric);
            }
            if (!evidence.at("missing_named_metrics").is_array()) throw std::runtime_error("Missing historical coverage metadata");
            for (const auto& metric:evidence.at("missing_named_metrics"))
                if (!metric.is_string() || !units.count(metric.get<std::string>()) || !missing.insert(metric.get<std::string>()).second)
                    throw std::runtime_error("Invalid missing history metric");
            for (const auto& metric:units)
                if (missing.count(metric.first)==present.count(metric.first)) throw std::runtime_error("Historical missing/present contradiction");
            const auto& excluded=evidence.at("excluded_entries");
            if (!excluded.is_object() || excluded.size()!=4) throw std::runtime_error("Invalid excluded history metadata");
            for (const auto* field:{"deleted","unknown_bit30","unmapped_code","negative_count"}) integer_money(excluded.at(field));
        } else if (result.contains("performance_context")) throw std::runtime_error("Unrequested saved performance");
        return;
    }
    if (operation == "player_context") {
        if (result.at("player_id") != request.at("player_id") || !result.at("player_id").is_string())
            throw std::runtime_error("Player context identity mismatch");
        integer_money(result.at("financial_revision"));
        if (result.contains("classification_pending") || result.contains("observed_player_source")) {
            if (!result.contains("classification_pending") || result.at("classification_pending")!=true ||
                !result.contains("observed_player_source") || !result.at("observed_player_source").is_string() ||
                result.at("observed_player_source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos ||
                !result.at("contract_accounting").is_null() || result.contains("legacy_contract") ||
                (result.contains("calendar_contract_context") && !result.at("calendar_contract_context").is_null()))
                throw std::runtime_error("Invalid pending player classification context");
        }
        if (result.contains("legacy_contract") || result.contains("legacy_liability_scope")) {
            if (!result.contains("legacy_contract") || !result.contains("legacy_liability_scope") ||
                result.at("legacy_liability_scope")!="original cap schedule; cash/protections/lifecycle unverified" ||
                !result.at("contract_accounting").is_null())
                throw std::runtime_error("Invalid legacy liability context");
            const auto& legacy=result.at("legacy_contract");
            if (!legacy.is_object() || legacy.size()!=7+legacy.contains("game_dollar_scale") || legacy.at("player_id")!=request.at("player_id") ||
                !legacy.at("source").is_string() ||
                legacy.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos)
                throw std::runtime_error("Invalid legacy identity or source");
            if(legacy.contains("game_dollar_scale")) {
                integer_money(legacy.at("game_dollar_scale"));
                if(legacy.at("game_dollar_scale")!=4) throw std::runtime_error("Unsupported legacy scale");
            }
            for (const auto* field:{"amount_word","bonus_code","shape_code","original_years","remaining_years"})
                integer_money(legacy.at(field));
            if (legacy.at("amount_word")<1 || legacy.at("amount_word")>65535 ||
                legacy.at("bonus_code")>10 || legacy.at("shape_code")>7 ||
                legacy.at("original_years")<1 || legacy.at("original_years")>15 ||
                legacy.at("remaining_years")<1 || legacy.at("remaining_years")>legacy.at("original_years") ||
                (result.contains("calendar_contract_context") && !result.at("calendar_contract_context").is_null()))
                throw std::runtime_error("Unsupported legacy terms or calendar conversion");
        }
        if (request.contains("context_format")) {
            if (!request.at("context_format").is_string() ||
                (request.at("context_format")!="calendar_v1" && request.at("context_format")!="calendar_v2" &&
                 request.at("context_format")!="calendar_v3" && request.at("context_format")!="calendar_v4") ||
                result.at("context_format")!=request.at("context_format") ||
                !result.at("contract_accounting").is_null())
                throw std::runtime_error("Invalid calendar player context format");
            const auto& calendar=result.at("calendar_contract_context");
            if (!calendar.is_null()) {
                auto expected=nlohmann::json{{"context_format",request.at("context_format")},
                    {"team_id",request.at("team_id")},{"generation_id",calendar.at("generation_id")}};
                validate_calendar_contract_context(calendar,expected);
                if (calendar.at("financial_revision")!=result.at("financial_revision") ||
                    calendar.at("economic_archive").at("contract").at("offer").at("player_id")!=request.at("player_id"))
                    throw std::runtime_error("Calendar player snapshot identity mismatch");
            }
        } else if (result.contains("context_format") || result.contains("calendar_contract_context")) {
            throw std::runtime_error("Unrequested calendar player context");
        }
        if (result.contains("contract_accounting"))
            validate_contract_accounting(result.at("contract_accounting"),request.at("player_id").get<std::string>());
        if (!result.at("initialized").is_boolean() || !result.at("agreed_promises").is_array() ||
            !result.at("promise_history").is_array()) throw std::runtime_error("Invalid player context");
        const bool initialized = result.at("initialized").get<bool>();
        for (const auto* field : {"personality", "relationships"}) {
            if (initialized ? !result.at(field).is_object() : !result.at(field).is_null())
                throw std::runtime_error("Invalid player initialization context");
        }
        for (const auto& agreement : result.at("agreed_promises")) {
            if (!agreement.is_object() || !agreement.at("agreement_request_id").is_string() ||
                agreement.at("agreement_request_id").get<std::string>().empty() || !agreement.at("goals").is_array())
                throw std::runtime_error("Invalid promise agreement context");
            promise_goals(agreement.at("goals"));
        }
        for (const auto& history : result.at("promise_history")) {
            if (!history.is_object()) throw std::runtime_error("Invalid promise history context");
            promise_circumstances(history,request);
        }
        if (result.contains("negotiation_history")) {
            if (!result.at("negotiation_history").is_array()) throw std::runtime_error("Invalid negotiation history context");
            if (result.contains("negotiation_history_total")) {
                integer_money(result.at("negotiation_history_total"));
                if (result.at("negotiation_history_total") < result.at("negotiation_history").size() ||
                    !result.at("negotiation_history_has_more").is_boolean() ||
                    result.at("negotiation_history_has_more") != (result.at("negotiation_history_total") > result.at("negotiation_history").size()))
                    throw std::runtime_error("Inconsistent negotiation history coverage");
            }
            for (const auto& event : result.at("negotiation_history"))
                if (!event.is_object() || canonical_offer(event.at("offer")).at("player_id") != request.at("player_id"))
                    throw std::runtime_error("Foreign player negotiation context");
        }
        return;
    }
    if (operation == "hello" || operation == "bind_runtime") {
        const bool observation=operation=="bind_runtime";
        if(observation && (result.size()!=3 || result.at("operations")!=nlohmann::json::array({"signing_context"}) || !request.contains("loaded_image_sha256")))
            throw std::runtime_error("Invalid observation binding capabilities");
        if (!result.contains("ai_enabled") || !result["ai_enabled"].is_boolean() || result["ai_enabled"] != !observation ||
            !result.contains("operations") || !result["operations"].is_array()) throw std::runtime_error("Invalid handshake result");
        for (const auto& item : result["operations"]) if (!item.is_string()) throw std::runtime_error("Invalid operation list");
        if(request.contains("loaded_image_sha256")) {
            auto hex=[](const nlohmann::json& value,size_t size) {
                if(!value.is_string()) return false;
                const auto text=value.get<std::string>();
                return text.size()==size && text.find_first_not_of("0123456789abcdef")==std::string::npos;
            };
            const auto& binding=result.at("runtime_binding");
            if(!hex(request.at("loaded_image_sha256"),64) || !binding.is_object() || binding.size()!=4 ||
               binding.at("loaded_image_sha256")!=request.at("loaded_image_sha256") ||
               !hex(binding.at("franchise_id"),32) || !hex(binding.at("bindings_sha256"),64) ||
               !hex(binding.at("snapshot_payload_sha256"),64))
                throw std::runtime_error("Runtime handshake identity mismatch");
        } else if(result.contains("runtime_binding")) throw std::runtime_error("Unrequested runtime binding");
        return;
    }
    if (operation == "preview" || operation == "negotiate" || operation == "negotiate_proposal" || operation == "manual_sign") {
        if (request.contains("return_scope")) {
            const auto& scope=request.at("return_scope");
            if (!scope.is_object() || scope.size()!=6 || !scope.at("league_year").is_number_integer() ||
                scope.at("league_year")<2020 || scope.at("league_year")>2030 ||
                !scope.at("healthy").is_boolean() || scope.at("healthy")!=true ||
                !scope.at("signed_on").is_string() || !scope.at("first_regular_season_game").is_string() ||
                !scope.at("source").is_string() || scope.at("source").get<std::string>().find_first_not_of(" \t\r\n")==std::string::npos ||
                scope.at("exclusions")!=nlohmann::json::array({"extensions","guarantee_offsets","league_year_rollover","rookie_contracts"}) ||
                !result.contains("return_scope") || result.at("return_scope").dump()!=scope.dump())
                throw std::runtime_error("Response changed sourced return scope");
        } else if (result.contains("return_scope")) throw std::runtime_error("Unexpected return signing mode");
    }
    if (operation == "preview") {
        if (!result.contains("revision") || !result["revision"].is_number_integer() || result["revision"] != request.at("expected_revision"))
            throw std::runtime_error("Preview revision mismatch");
        exact_money(result.at("room_after"));
        const auto& charges = result.at("contract_charges");
        if (!charges.is_array() || charges.size() != request.at("offer").at("salaries").size()) throw std::runtime_error("Preview charges mismatch");
        for (const auto& charge : charges) exact_money(charge);
        return;
    }
    if (operation != "manual_sign" && operation != "negotiate" && operation != "negotiate_proposal")
        throw std::runtime_error("Unsupported result operation");
    if (canonical_offer(result.at("offer")) != canonical_offer(request.at("offer")) || result.at("request_id") != request.at("request_id"))
        throw std::runtime_error("Response changed submitted contract");
    if(request.contains("contract_format")) {
        const auto format=request.at("contract_format").get<std::string>();
        guest_money_scale(format);
        if(operation!="negotiate_proposal" ||
            result.at("contract_format")!=request.at("contract_format"))
            throw std::runtime_error("Guest proposal contract format mismatch");
        auto check_encoding=[&format](const nlohmann::json& raw,const nlohmann::json& offer) {
            if(!raw.is_object() || raw.size()!=2 ||
                exact_guest_offer(raw,offer.at("player_id").get<std::string>(),format)!=canonical_offer(offer) ||
                (raw.at("flags_word").get<uint32_t>() & ~0xE00F000Fu))
                throw std::runtime_error("Guest proposal encoding differs from exact offer");
        };
        auto check_preview=[&request](const nlohmann::json& preview,const nlohmann::json& offer) {
            const auto exact=canonical_offer(offer);
            const auto& salaries=exact.at("salaries");
            const auto& charges=preview.at("contract_charges");
            if(preview.at("revision")!=request.at("expected_revision") || !charges.is_array() || charges.size()!=salaries.size())
                throw std::runtime_error("Guest proposal preview revision or term mismatch");
            for(size_t i=0;i<charges.size();++i) {
                integer_money(charges.at(i));
                if(charges.at(i).get<int64_t>()!=salaries.at(i).get<int64_t>()+exact.at("signing_bonus").get<int64_t>()/salaries.size())
                    throw std::runtime_error("Guest proposal preview charge mismatch");
            }
        };
        check_encoding(result.at("guest_offer"),request.at("offer"));
        if(result.at("outcome")=="accepted_proposal") check_preview(result.at("proposal_preview"),request.at("offer"));
        if(result.at("counter").is_null()) {
            if(!result.at("guest_counter").is_null()) throw std::runtime_error("Unexpected guest counter encoding");
        } else if(result.at("guest_counter").is_null()) {
            if(result.at("counter_validation").at("status")!="ineligible")
                throw std::runtime_error("Unencoded guest counter cannot be eligible");
        } else {
            check_encoding(result.at("guest_counter"),result.at("counter"));
            if(result.at("counter_validation").at("status")=="eligible")
                check_preview(result.at("counter_validation").at("preview"),result.at("counter"));
            else if(result.at("counter_validation").at("status")!="ineligible")
                throw std::runtime_error("Invalid guest counter eligibility");
        }
    } else if(result.contains("contract_format") || result.contains("guest_offer") || result.contains("guest_counter"))
        throw std::runtime_error("Unexpected guest proposal contract format");
    auto outcome = result.at("outcome").get<std::string>();
    auto action = result.at("action").get<std::string>();
    if (operation == "negotiate" || operation == "negotiate_proposal") {
        const auto proposed = request.value("promise_goals", nlohmann::json::array());
        const auto echoed = result.value("promise_goals", nlohmann::json::array());
        promise_goals(proposed); promise_goals(echoed);
        if (proposed != echoed) throw std::runtime_error("Response changed submitted promises");
        if (result.contains("promise_goals")) {
            if (action == "counter") promise_goals(result.at("counter_promises"));
            else if (!result.at("counter_promises").is_null()) throw std::runtime_error("Unexpected counter promises");
        } else if (result.contains("counter_promises")) throw std::runtime_error("Missing submitted promise context");
    }
    if (operation == "negotiate_proposal" &&
        (result.at("decision_mode") != "proposal" || result.contains("charges") || outcome == "signed"))
        throw std::runtime_error("Proposal cannot report a signing");
    if (outcome == "accepted_proposal") {
        if (operation != "negotiate_proposal" || action != "accept" || !result.at("counter").is_null() ||
            !request.at("expected_revision").is_number_integer() || request.at("expected_revision")<0 ||
            result.at("evidence").at("financial_revision") != request.at("expected_revision"))
            throw std::runtime_error("Invalid noncommitting acceptance");
        auto preview_request = request; preview_request["operation"] = "preview";
        nlohmann::json preview_response={{"error",nullptr},{"result",result.at("proposal_preview")}};
        validate_result(preview_response,preview_request);
    } else if (outcome == "signed") {
        if (action != "accept" || !result.at("counter").is_null()) throw std::runtime_error("Invalid signed decision");
        if (operation == "manual_sign" && result.at("decision_mode") != "manual") throw std::runtime_error("Manual decision mode missing");
        const auto& charges = result.at("charges");
        if (!charges.is_array() || charges.size() != request.at("offer").at("salaries").size()) throw std::runtime_error("Signed charges mismatch");
        for (const auto& charge : charges) exact_money(charge);
    } else if (outcome == "counteroffer") {
        if (action != "counter" || canonical_offer(result.at("counter"))["player_id"] != request.at("offer")["player_id"])
            throw std::runtime_error("Invalid counter decision");
    } else if (outcome == "player_rejected" || outcome == "accounting_rejected") {
        if (action != (outcome == "player_rejected" ? "reject" : "accept") || !result.at("counter").is_null())
            throw std::runtime_error("Invalid rejection decision");
    } else throw std::runtime_error("Unknown decision outcome");
    if (operation == "manual_sign" && outcome != "signed") throw std::runtime_error("Manual result is not a signing");
}
}
