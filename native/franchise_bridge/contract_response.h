#pragma once
#include "protocol.h"
#include <charconv>
#include <limits>
#include <numeric>
#include <set>
#include <algorithm>

namespace franchise {
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
inline void validate_result(const nlohmann::json& response, const nlohmann::json& request) {
    if (!response["error"].is_null()) return;
    const auto& result = response["result"];
    auto operation = request.at("operation").get<std::string>();
    if (operation == "manual_trade") {
        const auto seller=request.at("seller").get<std::string>(), buyer=request.at("buyer").get<std::string>();
        if (seller.empty() || buyer.empty() || seller == buyer || result.at("decision_mode") != "manual" ||
            result.at("seller") != seller || result.at("buyer") != buyer || result.at("player_id") != request.at("player_id"))
            throw std::runtime_error("Invalid manual assignment identity");
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
            if (archive.at("scope")!=scope || canonical_offer(archive.at("original_contract").at("offer")).at("player_id")!=request.at("player_id"))
                throw std::runtime_error("Response changed assignment source facts");
        }
        const auto player=request.at("player_id").get<std::string>();
        if (postings.at(seller).at("financial").at("outgoing_trades").at(player) !=
            postings.at(buyer).at("financial").at("incoming_trades").at(player))
            throw std::runtime_error("Paired assignment archives disagree");
        return;
    }
    if (operation == "manual_release") {
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
    if (operation == "player_context") {
        if (result.at("player_id") != request.at("player_id") || !result.at("player_id").is_string())
            throw std::runtime_error("Player context identity mismatch");
        integer_money(result.at("financial_revision"));
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
        for (const auto& history : result.at("promise_history"))
            if (!history.is_object()) throw std::runtime_error("Invalid promise history context");
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
    if (operation == "hello") {
        if (!result.contains("ai_enabled") || !result["ai_enabled"].is_boolean() || result["ai_enabled"] != true ||
            !result.contains("operations") || !result["operations"].is_array()) throw std::runtime_error("Invalid handshake result");
        for (const auto& item : result["operations"]) if (!item.is_string()) throw std::runtime_error("Invalid operation list");
        return;
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
    if (operation != "manual_sign" && operation != "negotiate") throw std::runtime_error("Unsupported result operation");
    if (canonical_offer(result.at("offer")) != canonical_offer(request.at("offer")) || result.at("request_id") != request.at("request_id"))
        throw std::runtime_error("Response changed submitted contract");
    auto outcome = result.at("outcome").get<std::string>();
    auto action = result.at("action").get<std::string>();
    if (operation == "negotiate") {
        const auto proposed = request.value("promise_goals", nlohmann::json::array());
        const auto echoed = result.value("promise_goals", nlohmann::json::array());
        promise_goals(proposed); promise_goals(echoed);
        if (proposed != echoed) throw std::runtime_error("Response changed submitted promises");
        if (result.contains("promise_goals")) {
            if (action == "counter") promise_goals(result.at("counter_promises"));
            else if (!result.at("counter_promises").is_null()) throw std::runtime_error("Unexpected counter promises");
        } else if (result.contains("counter_promises")) throw std::runtime_error("Missing submitted promise context");
    }
    if (outcome == "signed") {
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
