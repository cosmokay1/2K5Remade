/* Actual game-host lifecycle against an owned inert peer; no model requests. */
#include "../../src/nfl2k5_franchise_host.h"
#include <stdlib.h>

int wmain(int argc, wchar_t **argv)
{
    if (argc != 2) return 1;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER", L"vertex") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_PYTHON", argv[1]) ||
        _wputenv_s(L"NFL2K5_FRANCHISE_DATABASE", L"0")) return 2;
    if (!nfl2k5_franchise_start()) return 3;
    /* Re-entry must not replace the live child or leak its ownership. */
    if (nfl2k5_franchise_start()) return 4;
    nfl2k5_franchise_stop();
    nfl2k5_franchise_stop();
    if (!nfl2k5_franchise_start()) return 5;
    nfl2k5_franchise_stop();
    return 0;
}
