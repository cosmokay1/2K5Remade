#pragma once
#include "negotiation_screen.h"
inline nlohmann::json negotiation_screen_fixture() {
    return {{"protocol",1},{"request_id","authored-preview"},{"error",nullptr},{"result",{
        {"write_authorized",false},{"ai_authorized",false},{"player_id","authored-player"},
        {"player_context",{{"initialized",true},{"personality",{{"negotiation_style","competitive"},{"money",0.45},{"security",0.65},{"playing_time",0.8},{"winning",0.9},{"loyalty",0.5}}},
            {"relationships",{{"trust",0.5},{"respect",0.5},{"team_connection",0.5}}},
            {"legacy_contract",{{"amount_word",348},{"bonus_code",5},{"shape_code",6},{"original_years",3},{"remaining_years",3},{"game_dollar_scale",4}}}}},
        {"offer_context",{{"amount_word",422u},{"flags_word",0x20020004u},{"contract_format","softdrink_fxg_v1"},{"offer",{{"salaries",{6328000,3796000}},{"signing_bonus",6752000},
            {"guaranteed_salaries",{0,0}}}},{"preview",{{"contract_charges",{9704000,7172000}},{"room_after",79512000}}}}},
        {"performance_context",{{"saved_display_year",2004},{"franchise_season_year",2026},{"player_profile",{{"height_inches",72},{"weight_pounds",200},{"age_years",23},{"injury_tendency",nullptr}}},{"saved_history",{
            {{"metric","completions"},{"value",478},{"unit","count"},{"period_code_raw",1},{"mode_code_raw",0},{"candidate_calendar_year",2002}},
            {{"metric","sacks"},{"value",2.5},{"unit","sacks"},{"period_code_raw",2},{"mode_code_raw",1},{"candidate_calendar_year",2003}}}},
            {"missing_named_metrics",{"games","rushing_yards"}},
            {"unmapped_requested_metrics",{"targets","pressures","qb_hits"}}}}
    }}};
}
