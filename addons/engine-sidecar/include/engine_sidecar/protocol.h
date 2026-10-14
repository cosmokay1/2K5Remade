#pragma once
#include <nlohmann/json.hpp>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace engine_sidecar {
inline nlohmann::json parse_frame(const std::string& text) {
    if (text.size() > 65536) throw std::runtime_error("Protocol frame too large");
    std::vector<std::set<std::string>> objects;
    auto callback = [&](int depth, nlohmann::json::parse_event_t event, nlohmann::json& value) {
        if (depth > 32) throw std::runtime_error("Protocol nesting exceeded");
        if (event == nlohmann::json::parse_event_t::object_start) objects.emplace_back();
        if (event == nlohmann::json::parse_event_t::key && !objects.back().insert(value.get<std::string>()).second)
            throw std::runtime_error("Duplicate protocol field");
        if (event == nlohmann::json::parse_event_t::object_end) objects.pop_back();
        return true;
    };
    try { return nlohmann::json::parse(text, callback); }
    catch (...) { throw std::runtime_error("Invalid protocol JSON"); }
}

inline nlohmann::json decode_response(const std::string& text, const std::string& expected_id) {
    auto data = parse_frame(text);
    const std::set<std::string> fields{"protocol", "request_id", "result", "error", "detail"};
    if (!data.is_object() || data.size() != fields.size()) throw std::runtime_error("Invalid response fields");
    for (const auto& field : fields) if (!data.contains(field)) throw std::runtime_error("Missing response field");
    if (!data["protocol"].is_number_integer() || data["protocol"] != 1)
        throw std::runtime_error("Response protocol mismatch");
    if (expected_id.empty() || !data["request_id"].is_string() || data["request_id"] != expected_id)
        throw std::runtime_error("Response request mismatch");
    if (!(data["detail"].is_null() || data["detail"].is_string())) throw std::runtime_error("Invalid response detail");
    if (data["error"].is_null()) {
        if (!data["result"].is_object() || !data["detail"].is_null()) throw std::runtime_error("Invalid success response");
    } else {
        if (!data["error"].is_string() || data["error"].get<std::string>().empty() || !data["result"].is_null())
            throw std::runtime_error("Invalid failure response");
    }
    return data;
}
}
