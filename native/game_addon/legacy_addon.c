/* ABI1-only fixture: an ABI2 host must reject without reading its old table. */
#include <stdint.h>
__declspec(dllexport) const void *nfl2k5_addon_query(uint32_t abi) {
    static const uint32_t old_table=4;
    return abi==1?&old_table:0;
}
