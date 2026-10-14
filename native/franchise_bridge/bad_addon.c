/* Deliberately incompatible fixture: loader must reject before callbacks. */
#include "game_addon.h"
__declspec(dllexport) const NFL2K5AddonAPI *nfl2k5_addon_query(uint32_t abi) {
    static const NFL2K5AddonAPI bad={0};
    (void)abi;return &bad;
}
