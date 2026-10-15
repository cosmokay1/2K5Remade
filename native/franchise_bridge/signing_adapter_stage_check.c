/* Exercise the real DLL adapter with inert host callbacks, not retail memory. */
#include "game_addon.h"
#include "franchise_addon.h"
#include "finance_state.h"
#include "../../src/nfl2k5_franchise_host.h"
#include <stdio.h>
#include <string.h>
extern const NFL2K5AddonAPI* nfl2k5_addon_query(uint32_t abi);
static int enabled=1;
static unsigned reads,epochs,submits;
static unsigned long long submitted_epoch;
static const FranchiseSigningObservation* submitted_observation;
static int range(uint32_t a,size_t n){(void)a;(void)n;return 0;}
static int read_memory(uint32_t a,void* out,size_t n){(void)a;(void)out;(void)n;++reads;return 0;}
int nfl2k5_franchise_start(void){return 1;}
void nfl2k5_franchise_stop(void){}
void nfl2k5_franchise_on_fsm(uint32_t d,int p){(void)d;(void)p;}
void nfl2k5_franchise_poll(void){}
int nfl2k5_franchise_context_enabled(void){return 0;}
void nfl2k5_franchise_signing_context(const FranchiseSigningObservation* o){(void)o;}
int nfl2k5_franchise_display(FranchiseSigningDisplay* out){memset(out,0,sizeof(*out));return 0;}
unsigned long long nfl2k5_franchise_submission_epoch(void){++epochs;return enabled?7:0;}
int nfl2k5_franchise_submit_held(const FranchiseSigningObservation* o,unsigned long long epoch){
    ++submits;submitted_observation=o;submitted_epoch=epoch;return enabled;
}
int main(void){
    const NFL2K5AddonAPI* api=nfl2k5_addon_query(NFL2K5_ADDON_ABI);
    NFL2K5AddonHost host={sizeof(host),range,read_memory};
    if(!api || !api->start(&host)) return 1;
    FranchiseSignGateEvent event={FRANCHISE_SIGN_PRECOMMIT,0x12345678u};
    if(!api->event(FRANCHISE_SIGN_GATE_EVENT,&event,sizeof(event)) || reads || epochs || submits!=1 ||
       submitted_observation || submitted_epoch) return 2;
    event.stage=FRANCHISE_SIGN_JUDGMENT;
    if(!api->event(FRANCHISE_SIGN_GATE_EVENT,&event,sizeof(event)) || reads!=1 || epochs!=1 || submits!=2 ||
       submitted_observation || submitted_epoch!=7) return 3;
    event.stage=3;
    if(api->event(FRANCHISE_SIGN_GATE_EVENT,&event,sizeof(event)) ||
       api->event(FRANCHISE_SIGN_GATE_EVENT,&event,sizeof(uint32_t)) || submits!=2) return 4;
    enabled=0;reads=epochs=submits=0;
    event.stage=FRANCHISE_SIGN_PRECOMMIT;
    if(api->event(FRANCHISE_SIGN_GATE_EVENT,&event,sizeof(event)) || reads || epochs || submits!=1) return 5;
    event.stage=FRANCHISE_SIGN_JUDGMENT;
    if(api->event(FRANCHISE_SIGN_GATE_EVENT,&event,sizeof(event)) || reads || epochs!=1 || submits!=2) return 6;
    FranchiseFinanceSnapshot state;
    memset(&state,0xFF,sizeof(state));
    if(api->snapshot(FRANCHISE_FINANCE_SNAPSHOT,&state,sizeof(state)-1) ||
       api->snapshot(FRANCHISE_FINANCE_SNAPSHOT,&state,sizeof(state)) || state.size) return 7;
    api->stop();
    puts("Actual adapter distinguishes judgment from precommit without extra sampling or offer intent");return 0;
}
