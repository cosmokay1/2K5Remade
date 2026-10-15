/* Authored memory file only, using the production capture implementation. */
#include "finance_state.h"
#include "identity_state.h"
#include "franchise_addon.h"
#include "../../src/nfl2k5_franchise_host.h"
#include <stdio.h>
#include <stdlib.h>
static FILE *memory;
static long extent;
extern const NFL2K5AddonAPI *nfl2k5_addon_query(uint32_t abi);
/* No process, model, grant or submission in this read-only boundary fixture. */
int nfl2k5_franchise_start(void){return 1;}
void nfl2k5_franchise_stop(void){}
void nfl2k5_franchise_on_fsm(uint32_t d,int p){(void)d;(void)p;}
void nfl2k5_franchise_poll(void){}
int nfl2k5_franchise_context_enabled(void){return 0;}
void nfl2k5_franchise_signing_context(const FranchiseSigningObservation *o){(void)o;}
int nfl2k5_franchise_display(FranchiseSigningDisplay *out){(void)out;return 0;}
unsigned long long nfl2k5_franchise_submission_epoch(void){return 0;}
int nfl2k5_franchise_submit_held(const FranchiseSigningObservation *o,unsigned long long epoch){(void)o;(void)epoch;return 0;}
static int range(uint32_t address,size_t size) {
    return (uint64_t)address+size<=(uint64_t)extent;
}
static int read_memory(uint32_t address,void *out,size_t size) {
    return range(address,size) && fseek(memory,(long)address,SEEK_SET)==0 && fread(out,1,size,memory)==size;
}
int main(int argc,char **argv) {
    const int identity=argc==4 && !strcmp(argv[3],"identity");
    const int capture=argc==4 && !strcmp(argv[3],"capture");
    if((argc!=3 && !identity && !capture) || !(memory=fopen(argv[1],"rb"))) return 2;
    if(fseek(memory,0,SEEK_END) || (extent=ftell(memory))<0) {fclose(memory);return 2;}
    NFL2K5AddonHost host={sizeof(host),range,read_memory};
    size_t capacity=identity?sizeof(FranchiseIdentitySnapshot):sizeof(FranchiseFinanceSnapshot);
    void *state=malloc(capacity);
    if(!state) {fclose(memory);return 2;}
    const NFL2K5AddonAPI *api=nfl2k5_addon_query(NFL2K5_ADDON_ABI);
    if(!api || !api->start(&host)) {free(state);fclose(memory);return 2;}
    if(capture) {
#ifdef _WIN32
        if(_putenv_s("NFL2K5_FRANCHISE_CAPTURE",argv[2])) return 2;
#else
        if(setenv("NFL2K5_FRANCHISE_CAPTURE",argv[2],1)) return 2;
#endif
        const FranchiseFSMEvent event={0,0x00557B2Cu,1};
        api->event(FRANCHISE_FSM_EVENT,&event,sizeof(event));
        api->event(FRANCHISE_FSM_EVENT,&event,sizeof(event));
        api->stop();free(state);fclose(memory);
        FILE *result=fopen(argv[2],"rb");
        if(!result) return 1;
        fclose(result);return 0;
    }
    int captured=api->snapshot(identity?FRANCHISE_IDENTITY_SNAPSHOT:FRANCHISE_FINANCE_SNAPSHOT,state,capacity);
    api->stop();
    fclose(memory);
    if(!captured) {free(state);return 1;}
    FILE *output=fopen(argv[2],"wb");
    if(!output) {free(state);return 2;}
    uint32_t size=identity?((FranchiseIdentitySnapshot*)state)->size:((FranchiseFinanceSnapshot*)state)->size;
    unsigned char *bytes=identity?((FranchiseIdentitySnapshot*)state)->bytes:((FranchiseFinanceSnapshot*)state)->bytes;
    int good=fwrite(bytes,1,size,output)==size;
    if(fclose(output)) good=0;
    free(state);return good?0:2;
}
