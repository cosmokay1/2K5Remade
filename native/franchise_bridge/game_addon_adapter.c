/* Existing game call sites speak franchise; the module loader does not. */
#include "../../src/nfl2k5_sidecar_adapter.h"
#include <stdlib.h>
#include <string.h>
/* The shared signing routine returns retail failure for a deferred offer.
 * Its interactive caller must distinguish that from an actual rejection.
 * This token survives only until that synchronous caller consumes it. */
#ifdef _MSC_VER
__declspec(thread) static uint32_t held_signing_context;
__declspec(thread) static uint32_t accepted_signing_context;
__declspec(thread) static uint32_t applying_signing_context;
#else
static _Thread_local uint32_t held_signing_context;
static _Thread_local uint32_t accepted_signing_context;
static _Thread_local uint32_t applying_signing_context;
#endif
int nfl2k5_franchise_signing_was_held(uint32_t context) {
    int held=context && held_signing_context==context;
    held_signing_context=0;
    accepted_signing_context=0;
    applying_signing_context=0;
    return held;
}
static int signing_hold_result(uint32_t context,int held) {
    held_signing_context=held ? context : 0;
    return held;
}
static int screen_preview_requested(void) {
    const char *mode=getenv("NFL2K5_FRANCHISE_SCREEN_PREVIEW");
    return mode && !strcmp(mode,"1");
}
static int controlled_signing_requested(void) {
    const char *mode=getenv("NFL2K5_FRANCHISE_NEGOTIATION");
    return screen_preview_requested() || (mode && !strcmp(mode,"1"));
}
static int application_requested(void) {
    const char *mode=getenv("NFL2K5_FRANCHISE_GUEST_SIGNING");
    return !screen_preview_requested() && controlled_signing_requested() && mode && !strcmp(mode,"1");
}
#ifdef NFL2K5_FRANCHISE_CLIENT
#include "../game_addon/loader.h"
#include "franchise_addon.h"
/* A runtime serial is never reused after releasing the global guest lock.
 * Pin both application checks to one ownership span; this does not extend
 * ownership across subsequent original-game writes. */
extern uint64_t xbox_ggl_current_serial(void);
#ifdef _MSC_VER
__declspec(thread) static uint64_t accepted_guest_serial;
#else
static _Thread_local uint64_t accepted_guest_serial;
#endif
int nfl2k5_franchise_start(void) { held_signing_context=accepted_signing_context=applying_signing_context=0; return nfl2k5_addon_start(); }
void nfl2k5_franchise_stop(void) { held_signing_context=accepted_signing_context=applying_signing_context=0; nfl2k5_addon_stop(); }
void nfl2k5_franchise_guest_poll(void) { nfl2k5_addon_poll(); }
int nfl2k5_franchise_negotiation_view(FranchiseNegotiationView *out) {
    if(!out) return 0;
    /* Older addons and unavailable snapshots must never leave stale UI data. */
    memset(out,0,sizeof(*out));
    if(nfl2k5_addon_snapshot(FRANCHISE_NEGOTIATION_VIEW_SNAPSHOT,out,sizeof(*out))) return 1;
    memset(out,0,sizeof(*out));return 0;
}
int nfl2k5_franchise_display(FranchiseSigningDisplay *out) {
    return nfl2k5_addon_snapshot(FRANCHISE_DISPLAY_SNAPSHOT,out,sizeof(*out));
}
#endif
void nfl2k5_franchise_load_boundary(uint32_t stage,uint32_t buffer,uint32_t offset,uint32_t table_offset,uint32_t stack) {
#ifdef NFL2K5_FRANCHISE_CLIENT
    const FranchiseLoadEvent event={stage,buffer,offset,table_offset,stack};
    nfl2k5_addon_event(FRANCHISE_LOAD_EVENT,&event,sizeof(event));
#else
    (void)stage;(void)buffer;(void)offset;(void)table_offset;(void)stack;
#endif
}
void nfl2k5_diag_fsm(uint32_t object,uint32_t descriptor,int push) {
#ifdef NFL2K5_FRANCHISE_CLIENT
    const FranchiseFSMEvent event={object,descriptor,push!=0};
    nfl2k5_addon_event(FRANCHISE_FSM_EVENT,&event,sizeof(event));
#else
    (void)object;(void)descriptor;(void)push;
#endif
}
void nfl2k5_diag_signing(uint32_t stage,uint32_t context,uint32_t result,uint32_t code,uint32_t stack) {
    if(stage==0) held_signing_context=accepted_signing_context=applying_signing_context=0;
#ifdef NFL2K5_FRANCHISE_CLIENT
    const FranchiseSigningEvent event={stage,context,result,code,stack};
    nfl2k5_addon_event(FRANCHISE_SIGNING_EVENT,&event,sizeof(event));
#else
    (void)stage;(void)context;(void)result;(void)code;(void)stack;
#endif
}

int nfl2k5_franchise_hold_signing(uint32_t context) {
    accepted_signing_context=0;
    applying_signing_context=0;
#ifdef NFL2K5_FRANCHISE_CLIENT
    return signing_hold_result(context,nfl2k5_addon_event(FRANCHISE_SIGN_SUBMIT_EVENT,&context,sizeof(context))!=0 || controlled_signing_requested());
#else
    return signing_hold_result(context,controlled_signing_requested());
#endif
}

int nfl2k5_franchise_hold_signing_at(uint32_t stage,uint32_t context) {
    const uint32_t accepted=accepted_signing_context;
    accepted_signing_context=0; /* Consume before invoking possibly reentrant addon code. */
    applying_signing_context=0;
    if(accepted) {
        if(stage!=2u || context!=accepted || !application_requested()) return signing_hold_result(context,1);
#ifdef NFL2K5_FRANCHISE_CLIENT
        const uint64_t serial=accepted_guest_serial;
        accepted_guest_serial=0;
        if(!serial || xbox_ggl_current_serial()!=serial) return signing_hold_result(context,1);
        const FranchiseSignGateEvent event={stage,context};
        const int decision=nfl2k5_addon_event(FRANCHISE_SIGN_APPLICATION_EVENT,&event,sizeof(event));
        accepted_signing_context=0;
        applying_signing_context=0;
        if(application_requested() && decision==FRANCHISE_SIGN_APPLICATION_AUTHORIZED &&
           xbox_ggl_current_serial()==serial) {
            applying_signing_context=context;
            return signing_hold_result(context,0);
        }
#endif
        return signing_hold_result(context,1);
    }
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

int nfl2k5_franchise_judge_signing(uint32_t context) {
    accepted_signing_context=0;
    applying_signing_context=0;
#ifdef NFL2K5_FRANCHISE_CLIENT
    if(context && application_requested()) {
        const uint64_t serial=xbox_ggl_current_serial();
        accepted_guest_serial=0;
        if(!serial) return signing_hold_result(context,1);
        const FranchiseSignGateEvent event={1u,context};
        const int decision=nfl2k5_addon_event(FRANCHISE_SIGN_APPLICATION_EVENT,&event,sizeof(event));
        accepted_signing_context=0;
        applying_signing_context=0;
        if(application_requested() && decision==FRANCHISE_SIGN_APPLICATION_AUTHORIZED &&
           xbox_ggl_current_serial()==serial) {
            accepted_guest_serial=serial;
            accepted_signing_context=context;
            signing_hold_result(context,0);
            return 2;
        }
        if(decision) { signing_hold_result(context,1); return 1; }
    }
#endif
    return nfl2k5_franchise_hold_signing_at(1u,context) ? 1 : 0;
}

/* Called only at the original success epilogue, after roster/payroll/history.
 * Notification is recovery evidence, not a further authorization or save proof.
 * Record completion even if AI was disabled after the committed writes. */
void nfl2k5_franchise_signing_completed(uint32_t context) {
    const uint32_t applying=applying_signing_context;
    applying_signing_context=0;
#ifdef NFL2K5_FRANCHISE_CLIENT
    if(context && context==applying)
        nfl2k5_addon_event(FRANCHISE_SIGN_COMPLETED_EVENT,&context,sizeof(context));
#else
    (void)context;(void)applying;
#endif
}
