/* Existing game call sites speak franchise; the module loader does not. */
#include "../../src/nfl2k5_sidecar_adapter.h"
#include <stdlib.h>
#include <string.h>
/* The shared signing routine returns retail failure for a deferred offer.
 * Its interactive caller must distinguish that from an actual rejection.
 * This token survives only until that synchronous caller consumes it. */
#ifdef _MSC_VER
__declspec(thread) static uint32_t held_signing_context;
#else
static _Thread_local uint32_t held_signing_context;
#endif
int nfl2k5_franchise_signing_was_held(uint32_t context) {
    int held=context && held_signing_context==context;
    held_signing_context=0;
    return held;
}
static int signing_hold_result(uint32_t context,int held) {
    held_signing_context=held ? context : 0;
    return held;
}
static int controlled_signing_requested(void) {
    const char *mode=getenv("NFL2K5_FRANCHISE_NEGOTIATION");
    return mode && !strcmp(mode,"1");
}
#ifdef NFL2K5_FRANCHISE_CLIENT
#include "../game_addon/loader.h"
#include "franchise_addon.h"
int nfl2k5_franchise_start(void) { held_signing_context=0; return nfl2k5_addon_start(); }
void nfl2k5_franchise_stop(void) { held_signing_context=0; nfl2k5_addon_stop(); }
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
    if(stage==0) held_signing_context=0;
#ifdef NFL2K5_FRANCHISE_CLIENT
    const FranchiseSigningEvent event={stage,context,result,code,stack};
    nfl2k5_addon_event(FRANCHISE_SIGNING_EVENT,&event,sizeof(event));
#else
    (void)stage;(void)context;(void)result;(void)code;(void)stack;
#endif
}

int nfl2k5_franchise_hold_signing(uint32_t context) {
#ifdef NFL2K5_FRANCHISE_CLIENT
    return signing_hold_result(context,nfl2k5_addon_event(FRANCHISE_SIGN_SUBMIT_EVENT,&context,sizeof(context))!=0 || controlled_signing_requested());
#else
    return signing_hold_result(context,controlled_signing_requested());
#endif
}

int nfl2k5_franchise_hold_signing_at(uint32_t stage,uint32_t context) {
    if(stage!=1u && stage!=2u) return signing_hold_result(context,1);
#ifdef NFL2K5_FRANCHISE_CLIENT
    const FranchiseSignGateEvent event={stage,context};
    if(nfl2k5_addon_event(FRANCHISE_SIGN_GATE_EVENT,&event,sizeof(event))) return signing_hold_result(context,1);
    /* Older ABI2 addons only know v1. An unknown v2 event must not release
     * a transaction that the legacy addon would have held. */
    return nfl2k5_franchise_hold_signing(context);
#else
    return nfl2k5_franchise_hold_signing(context);
#endif
}
