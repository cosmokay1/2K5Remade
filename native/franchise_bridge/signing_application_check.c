/* Actual host shim with authored grants; production addon grants none. */
#include "../../src/nfl2k5_sidecar_adapter.h"
#include "franchise_addon.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern void nfl2k5_franchise_stop(void);
static int judgment,commit;
static unsigned applications,completions;
static uint32_t completed_context;
static int mode(const char *key,const char *value) {
#ifdef _WIN32
    return _putenv_s(key,value);
#else
    return setenv(key,value,1);
#endif
}
int nfl2k5_addon_start(void){return 1;}
void nfl2k5_addon_stop(void){}
void nfl2k5_addon_poll(void){}
int nfl2k5_addon_snapshot(const char *n,void *o,size_t c){(void)n;(void)o;(void)c;return 0;}
int nfl2k5_addon_event(const char *name,const void *data,size_t size) {
    if(!strcmp(name,FRANCHISE_SIGN_COMPLETED_EVENT)) {
        if(size!=sizeof(uint32_t)) abort();
        completed_context=*(const uint32_t *)data;++completions;
        nfl2k5_franchise_signing_completed(completed_context); /* Reentrant retry is consumed. */
        return 2;
    }
    if(strcmp(name,FRANCHISE_SIGN_APPLICATION_EVENT) || size!=sizeof(FranchiseSignGateEvent)) return 0;
    const FranchiseSignGateEvent *event=data;
    ++applications;
    return event->stage==1 ? judgment : commit;
}
int main(void) {
    if(mode("NFL2K5_FRANCHISE_NEGOTIATION","1") || mode("NFL2K5_FRANCHISE_GUEST_SIGNING","1")) return 1;
    nfl2k5_franchise_signing_completed(0x1234);
    if(completions) return 27;
    judgment=commit=FRANCHISE_SIGN_APPLICATION_AUTHORIZED;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2 ||
       nfl2k5_franchise_hold_signing_at(2,0x1234) || applications!=2 ||
       completions) return 2;
    nfl2k5_franchise_signing_completed(0x1234);
    nfl2k5_franchise_signing_completed(0x1234);
    if(completions!=1 || completed_context!=0x1234 || nfl2k5_franchise_signing_was_held(0x1234)) return 19;
    /* Repeating precommit, bypassing judgment, CPU or other contexts cannot use it. */
    if(!nfl2k5_franchise_hold_signing_at(2,0x1234) || applications!=2) return 3;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2 ||
       !nfl2k5_franchise_hold_signing_at(2,0x5678) ||
       !nfl2k5_franchise_hold_signing_at(2,0x1234)) return 4;
    if(nfl2k5_franchise_judge_signing(0)!=1 || !nfl2k5_franchise_hold_signing_at(2,0)) return 5;
    for(int rejected=-1;rejected<=3;++rejected) {
        if(rejected==2) continue;
        judgment=rejected;
        if(nfl2k5_franchise_judge_signing(0x1234)!=1 || !nfl2k5_franchise_signing_was_held(0x1234)) return 6;
        judgment=2;commit=rejected;
        if(nfl2k5_franchise_judge_signing(0x1234)!=2 || !nfl2k5_franchise_hold_signing_at(2,0x1234) ||
           !nfl2k5_franchise_signing_was_held(0x1234)) return 7;
        nfl2k5_franchise_signing_completed(0x1234);
        if(completions!=1) return 28;
    }
    judgment=commit=2;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2) return 8;
    nfl2k5_diag_signing(0,0,0,0,0);
    if(!nfl2k5_franchise_hold_signing_at(2,0x1234)) return 9;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2) return 10;
    nfl2k5_franchise_signing_was_held(0);
    if(!nfl2k5_franchise_hold_signing_at(2,0x1234)) return 11;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2) return 12;
    nfl2k5_franchise_stop();
    if(!nfl2k5_franchise_hold_signing_at(2,0x1234)) return 13;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2 || !nfl2k5_franchise_hold_signing(0x5678) ||
       !nfl2k5_franchise_hold_signing_at(2,0x1234)) return 18;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2 || mode("NFL2K5_FRANCHISE_GUEST_SIGNING","0") ||
       !nfl2k5_franchise_hold_signing_at(2,0x1234)) return 14;
    if(mode("NFL2K5_FRANCHISE_GUEST_SIGNING","1") || nfl2k5_franchise_judge_signing(0x1234)!=2 ||
       mode("NFL2K5_FRANCHISE_NEGOTIATION","0") || !nfl2k5_franchise_hold_signing_at(2,0x1234)) return 15;
    applications=0;
    if(nfl2k5_franchise_judge_signing(0x1234) || applications) return 16; /* Retail unchanged. */
    if(mode("NFL2K5_FRANCHISE_NEGOTIATION","1") || mode("NFL2K5_FRANCHISE_GUEST_SIGNING","0") ||
       nfl2k5_franchise_judge_signing(0x1234)!=1 || applications) return 17;
    /* Completion persists through control disable, but never grants another commit. */
    mode("NFL2K5_FRANCHISE_GUEST_SIGNING","1");
    if(nfl2k5_franchise_judge_signing(0x1234)!=2 || nfl2k5_franchise_hold_signing_at(2,0x1234)) return 20;
    mode("NFL2K5_FRANCHISE_NEGOTIATION","0");
    nfl2k5_franchise_signing_completed(0x1234);
    if(completions!=2) return 21;
    mode("NFL2K5_FRANCHISE_NEGOTIATION","1");
    if(!nfl2k5_franchise_hold_signing_at(2,0x1234)) return 22;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2 || nfl2k5_franchise_hold_signing_at(2,0x1234)) return 23;
    nfl2k5_franchise_signing_completed(0x5678);
    nfl2k5_franchise_signing_completed(0x1234);
    if(completions!=2) return 24;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2 || nfl2k5_franchise_hold_signing_at(2,0x1234)) return 25;
    nfl2k5_diag_signing(0,0,0,0,0);
    nfl2k5_franchise_signing_completed(0x1234);
    if(completions!=2) return 26;
    if(nfl2k5_franchise_judge_signing(0x1234)!=2 || nfl2k5_franchise_hold_signing_at(2,0x1234)) return 29;
    nfl2k5_franchise_stop();
    nfl2k5_franchise_signing_completed(0x1234);
    if(completions!=2) return 30;
    puts("Two-stage same-context application boundary passed with authored grants only");
    return 0;
}
