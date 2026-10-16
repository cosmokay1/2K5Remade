/* Authored memory, actual private guard and addon dispatcher. No game assets. */
#include "pending_signing.h"
#include "franchise_addon.h"
#include "../../src/nfl2k5_franchise_host.h"
#include <stdio.h>
#include <stdlib.h>
static unsigned char *memory;
static unsigned calls,fail_call;
static uint32_t mutate;
static unsigned submissions;
static int range(uint32_t a,size_t n){return (uint64_t)a+n<=0x1000000u;}
static int read_memory(uint32_t a,void *out,size_t n) {
    if(++calls==fail_call || !range(a,n)) return 0;
    memcpy(out,memory+a,n);
    if(a==mutate){memory[a+n-1]^=1;mutate=0;}
    return 1;
}
int nfl2k5_franchise_start(void){return 1;}
void nfl2k5_franchise_stop(void){}
void nfl2k5_franchise_on_fsm(uint32_t d,int p){(void)d;(void)p;}
void nfl2k5_franchise_poll(void){}
int nfl2k5_franchise_context_enabled(void){return 0;}
void nfl2k5_franchise_signing_context(const FranchiseSigningObservation *o){(void)o;}
int nfl2k5_franchise_negotiation_view(FranchiseNegotiationView *out){(void)out;return 0;}
int nfl2k5_franchise_display(FranchiseSigningDisplay *out){(void)out;return 0;}
unsigned long long nfl2k5_franchise_submission_epoch(void){return 0;}
int nfl2k5_franchise_completed(void){return 0;}
int nfl2k5_franchise_application_at(unsigned s,uint32_t c){(void)s;(void)c;return 0;}
int nfl2k5_franchise_application_terms(uint32_t *a,uint32_t *f){(void)a;(void)f;return 0;}
int nfl2k5_franchise_application_selected(const FranchiseSigningObservation *o,int a){(void)o;(void)a;return 0;}
int nfl2k5_franchise_submit_held(const FranchiseSigningObservation *o,unsigned long long e){(void)o;(void)e;++submissions;return 1;}
extern const NFL2K5AddonAPI *nfl2k5_addon_query(uint32_t abi);
static void put(uint32_t a,uint32_t v){finance_put32(memory+a,v);}
static int expect(const NFL2K5AddonHost *host,const NFL2K5AddonAPI *api,int clear) {
    const FranchiseSignGateEvent event={FRANCHISE_SIGN_JUDGMENT,0x11000};
    if(franchise_pending_signing_clear(host,event.context)!=clear) return 0;
    /* Even a clear result is NOT an application authorization. */
    return api->event(FRANCHISE_SIGN_APPLICATION_EVENT,&event,sizeof(event))==1;
}
int main(void) {
    memory=calloc(1,0x1000000u);if(!memory)return 1;
    NFL2K5AddonHost host={sizeof(host),range,read_memory};
    const NFL2K5AddonAPI *api=nfl2k5_addon_query(NFL2K5_ADDON_ABI);
    if(!api || !api->start(&host)) return 2;
    put(0xB72918,0x10000);put(0x10000,3);put(0x10004,0x200000);put(0x11000,0x200054);
    if(!expect(&host,api,1)) return 3;
    for(unsigned i=0;i<15;++i) for(unsigned j=0;j<6;++j) {
        const uint32_t row=0xE3C27C+i*0x3C;
        const uint32_t participant=row+(j<3?0xC+4*j:0x24+4*(j-3));
        put(participant,0x200054);if(!expect(&host,api,1)) return 4;
        put(row,1);if(!expect(&host,api,0)) return 5;
        put(participant,0x2000A8);if(!expect(&host,api,1)) return 6;
        memset(memory+row,0,0x3C);
    }
    for(unsigned i=0;i<100;++i) {
        const uint32_t row=0xE3C600+i*0x10;put(row,0x200054);
        memory[row+0xB]=0xFC;if(!expect(&host,api,1)) return 7;
        for(unsigned state=1;state<=3;++state) {
            memory[row+0xB]=(unsigned char)(0xFC|state);if(!expect(&host,api,0)) return 8;
        }
        put(row,0x2000A8);if(!expect(&host,api,1)) return 9;
        memset(memory+row,0,0x10);
    }
    for(unsigned i=1;i<=10;++i) {
        calls=0;fail_call=i;if(franchise_pending_signing_clear(&host,0x11000)) return 10;
    }
    fail_call=0;
    const uint32_t changes[]={0x11000,0xB72918,0x10000,0xE3C27C,0xE3C600};
    const unsigned sizes[]={16,4,8,15*0x3C,100*0x10};
    for(unsigned i=0;i<5;++i) {
        mutate=changes[i];
        if(franchise_pending_signing_clear(&host,0x11000)) return 11;
        memory[changes[i]+sizes[i]-1]^=1;
    }
    put(0x10004,0x300000);put(0x11000,0x300054);if(!expect(&host,api,1)) return 12;
    put(0x11000,0x300055);if(!expect(&host,api,0)) return 13;
    put(0x11000,0x300000+3*0x54);if(!expect(&host,api,0)) return 14;
    put(0x11000,0x300054);put(0x10000,FRANCHISE_FINANCE_MAX_PLAYERS+1);if(!expect(&host,api,0)) return 15;
    put(0x10000,3);
    if(franchise_pending_signing_clear(&host,0) || franchise_pending_signing_clear(&host,UINT32_MAX-1)) return 16;
    if(submissions) return 17;
    api->stop();free(memory);
    puts("Pending native signing queues hold before application; clear queues grant nothing");return 0;
}
