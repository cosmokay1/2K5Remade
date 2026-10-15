/* Compile the actual game shim without sidecar support. No addon stubs. */
#include "../../src/nfl2k5_sidecar_adapter.h"
#include <stdlib.h>
#include <stdio.h>
static int mode(const char *value) {
#ifdef _WIN32
    return _putenv_s("NFL2K5_FRANCHISE_NEGOTIATION",value);
#else
    return setenv("NFL2K5_FRANCHISE_NEGOTIATION",value,1);
#endif
}
int main(void) {
    if(mode("1")) return 1;
    for(uint32_t stage=1;stage<=2;++stage) {
        if(!nfl2k5_franchise_hold_signing_at(stage,0x1234) ||
           !nfl2k5_franchise_signing_was_held(0x1234) ||
           nfl2k5_franchise_signing_was_held(0x1234)) return 2;
        /* CPU passes have no interactive context but must also stay held. */
        if(!nfl2k5_franchise_hold_signing_at(stage,0) ||
           nfl2k5_franchise_signing_was_held(0)) return 3;
    }
    nfl2k5_franchise_hold_signing_at(1,0x1234);
    if(nfl2k5_franchise_signing_was_held(0x5678) ||
       nfl2k5_franchise_signing_was_held(0x1234)) return 4;
    nfl2k5_franchise_hold_signing_at(2,0x1234);
    nfl2k5_diag_signing(0,0x1234,0,0,0);
    if(nfl2k5_franchise_signing_was_held(0x1234)) return 5;
    const char *disabled[]={"0","","true","01"};
    for(unsigned i=0;i<sizeof(disabled)/sizeof(disabled[0]);++i) {
        if(mode(disabled[i])) return 6;
        for(uint32_t stage=1;stage<=2;++stage)
            if(nfl2k5_franchise_hold_signing_at(stage,0x1234) ||
               nfl2k5_franchise_signing_was_held(0x1234)) return 7;
    }
    if(!nfl2k5_franchise_hold_signing_at(0,0x1234) ||
       !nfl2k5_franchise_hold_signing_at(3,0x1234)) return 8;
    puts("Controlled signing stays held without compiled sidecar support");
    return 0;
}
