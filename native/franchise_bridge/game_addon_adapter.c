/* Existing game call sites speak franchise; the module loader does not. */
#include "../../src/nfl2k5_sidecar_adapter.h"
#ifdef NFL2K5_FRANCHISE_CLIENT
#include "../game_addon/loader.h"
#include "franchise_addon.h"
int nfl2k5_franchise_start(void) { return nfl2k5_addon_start(); }
void nfl2k5_franchise_stop(void) { nfl2k5_addon_stop(); }
void nfl2k5_franchise_guest_poll(void) { nfl2k5_addon_poll(); }
int nfl2k5_franchise_display(FranchiseSigningDisplay *out) {
    return nfl2k5_addon_snapshot(FRANCHISE_DISPLAY_SNAPSHOT,out,sizeof(*out));
}
#endif
void nfl2k5_diag_fsm(uint32_t object,uint32_t descriptor,int push) {
#ifdef NFL2K5_FRANCHISE_CLIENT
    const FranchiseFSMEvent event={object,descriptor,push!=0};
    nfl2k5_addon_event(FRANCHISE_FSM_EVENT,&event,sizeof(event));
#else
    (void)object;(void)descriptor;(void)push;
#endif
}
void nfl2k5_diag_signing(uint32_t stage,uint32_t context,uint32_t result,uint32_t code,uint32_t stack) {
#ifdef NFL2K5_FRANCHISE_CLIENT
    const FranchiseSigningEvent event={stage,context,result,code,stack};
    nfl2k5_addon_event(FRANCHISE_SIGNING_EVENT,&event,sizeof(event));
#else
    (void)stage;(void)context;(void)result;(void)code;(void)stack;
#endif
}

int nfl2k5_franchise_hold_signing(uint32_t context) {
#ifdef NFL2K5_FRANCHISE_CLIENT
    return nfl2k5_addon_event(FRANCHISE_SIGN_SUBMIT_EVENT,&context,sizeof(context))!=0;
#else
    (void)context;return 0;
#endif
}
