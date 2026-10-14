/* Actual game-host lifecycle against an owned inert peer; no model requests. */
#include "../../src/nfl2k5_franchise_host.h"
#include <stdlib.h>

int wmain(int argc, wchar_t **argv)
{
    if (argc != 2) return 1;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_DATABASE",L"") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE",L"") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT",L"") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT",L"") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER", L"vertex") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_PYTHON", argv[1]) ||
        _wputenv_s(L"NFL2K5_FRANCHISE_DATABASE", L"0")) return 2;
    if (!nfl2k5_franchise_start()) return 3;
    /* Re-entry must not replace the live child or leak its ownership. */
    if (nfl2k5_franchise_start()) return 4;
    nfl2k5_franchise_stop();
    nfl2k5_franchise_stop();
    if (!nfl2k5_franchise_start()) return 5;
    nfl2k5_franchise_stop();
    /* Invalid/partial policy must fail before an owned child is launched. */
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_DATABASE",L"usage with spaces.sqlite") ||
        nfl2k5_franchise_start()) return 6;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE",L"franchise 2026") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT",L"+250") || nfl2k5_franchise_start()) return 7;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT",L"9223372036854775808") || nfl2k5_franchise_start()) return 8;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT",L"0") || nfl2k5_franchise_start()) return 9;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT",L"250") || !nfl2k5_franchise_start()) return 10;
    nfl2k5_franchise_stop();
    /* Token policy needs the complete request policy; never launch a partial one. */
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_DATABASE",L"") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE",L"") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT",L"") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT",L"1000000") || nfl2k5_franchise_start()) return 11;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_DATABASE",L"usage with spaces.sqlite") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE",L"franchise 2026") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT",L"250")) return 12;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT",L"+0") || nfl2k5_franchise_start()) return 13;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT",L"0") || nfl2k5_franchise_start()) return 14;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT",L"9223372036854775808") || nfl2k5_franchise_start()) return 15;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT",L" 10") || nfl2k5_franchise_start()) return 16;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT",L"\x0661") || nfl2k5_franchise_start()) return 17;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT",L"1000000") || !nfl2k5_franchise_start()) return 18;
    if (nfl2k5_franchise_start()) return 19;
    nfl2k5_franchise_stop();
    nfl2k5_franchise_stop();
    return 0;
}
