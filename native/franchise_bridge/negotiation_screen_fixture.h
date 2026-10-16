#pragma once
#include "negotiation_screen.h"
inline nlohmann::json negotiation_screen_fixture() {
    return {{"protocol",1},{"request_id","authored-preview"},{"error",nullptr},{"result",{
        {"write_authorized",false},{"ai_authorized",false},
        {"offer_context",{{"offer",{{"salaries",{6328000,3796000}},{"signing_bonus",6752000},
            {"guaranteed_salaries",{0,0}}}},{"preview",{{"contract_charges",{9704000,7172000}},{"room_after",79512000}}}}},
        {"performance_context",{{"saved_display_year",2004},{"franchise_season_year",2026},{"player_profile",{{"height_inches",72},{"weight_pounds",200},{"age_years",23},{"injury_tendency",nullptr}}},{"saved_history",{
            {{"metric","completions"},{"value",478},{"unit","count"},{"period_code_raw",1},{"mode_code_raw",0},{"candidate_calendar_year",2002}},
            {{"metric","sacks"},{"value",2.5},{"unit","sacks"},{"period_code_raw",2},{"mode_code_raw",1},{"candidate_calendar_year",2003}}}},
            {"missing_named_metrics",{"games","rushing_yards"}},
            {"unmapped_requested_metrics",{"targets","pressures","qb_hits"}}}}
    }}};
}
