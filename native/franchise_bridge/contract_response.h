#pragma once
#include "protocol.h"
#include <charconv>
#include <limits>
#include <numeric>

namespace franchise {
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
