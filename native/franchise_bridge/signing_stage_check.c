/* Actual host shim, authored addon replies; no game memory or process launch. */
#include "../../src/nfl2k5_sidecar_adapter.h"
#include "../game_addon/loader.h"
#include "franchise_addon.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int gate_reply,legacy_reply;
static unsigned gates,legacy;
static uint32_t last_stage,last_context;
static int mode(const char* value){
#ifdef _WIN32
    return _putenv_s("NFL2K5_FRANCHISE_NEGOTIATION",value);
#else
    return setenv("NFL2K5_FRANCHISE_NEGOTIATION",value,1);
#endif
}
int nfl2k5_addon_start(void){return 1;}
void nfl2k5_addon_stop(void){}
void nfl2k5_addon_poll(void){}
int nfl2k5_addon_snapshot(const char* name,void* out,size_t capacity){(void)name;(void)out;(void)capacity;return 0;}
int nfl2k5_addon_event(const char* name,const void* data,size_t size){
    if(!strcmp(name,FRANCHISE_SIGN_GATE_EVENT) && size==sizeof(FranchiseSignGateEvent)){
        FranchiseSignGateEvent event;memcpy(&event,data,sizeof(event));++gates;
        last_stage=event.stage;last_context=event.context;return gate_reply;
    }
    if(!strcmp(name,FRANCHISE_SIGN_SUBMIT_EVENT) && size==sizeof(uint32_t)){
        memcpy(&last_context,data,sizeof(last_context));++legacy;return legacy_reply;
    }
    return 0;
}
int main(void){
    if(mode("0")) return 6;
    for(uint32_t stage=FRANCHISE_SIGN_JUDGMENT;stage<=FRANCHISE_SIGN_PRECOMMIT;++stage){
        gates=legacy=0;gate_reply=1;legacy_reply=0;
        if(!nfl2k5_franchise_hold_signing_at(stage,0x12345678u) || gates!=1 || legacy ||
           last_stage!=stage || last_context!=0x12345678u) return 1;
        // An older addon does not know v2, but its hold must still be honored.
        gates=legacy=0;gate_reply=0;legacy_reply=1;
        if(!nfl2k5_franchise_hold_signing_at(stage,0x22345678u) || gates!=1 || legacy!=1 || last_context!=0x22345678u) return 2;
        gate_reply=legacy_reply=0;
        if(nfl2k5_franchise_hold_signing_at(stage,0)) return 3; // Disabled/absent addon preserves retail behavior.
        gate_reply=2;legacy=0;
        if(!nfl2k5_franchise_hold_signing_at(stage,0) || legacy) return 4; // A nonboolean result never grants writes.
    }
    gates=legacy=0;
    if(!nfl2k5_franchise_hold_signing_at(0,0) || !nfl2k5_franchise_hold_signing_at(3,0) || gates || legacy) return 5;
    // Explicit controlled mode cannot silently become retail when a module is
    // missing, disabled, fails startup, or does not handle these messages.
    gate_reply=legacy_reply=0;
    if(mode("1") || !nfl2k5_franchise_hold_signing_at(FRANCHISE_SIGN_JUDGMENT,0) ||
       !nfl2k5_franchise_hold_signing_at(FRANCHISE_SIGN_PRECOMMIT,0) || !nfl2k5_franchise_hold_signing(0)) return 7;
    if(mode("0") || nfl2k5_franchise_hold_signing_at(FRANCHISE_SIGN_JUDGMENT,0) ||
       nfl2k5_franchise_hold_signing_at(FRANCHISE_SIGN_PRECOMMIT,0)) return 8;
    puts("Stage-aware signing shim, legacy hold fallback and no-write behavior passed");return 0;
}
