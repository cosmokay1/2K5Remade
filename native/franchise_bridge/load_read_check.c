#include "load_read.h"
#include <stdlib.h>
static void require(int ok){if(!ok)abort();}
static FranchiseLoadEvent event={FRANCHISE_LOAD_BEGIN,0x100000,0,24,0x400000};
static NFL2K5AddonFileReadV2 read_event;
static FranchiseSaveRead source;
static void begin(FranchiseLoadRead *s){memset(s,0,sizeof(*s));event.stage=FRANCHISE_LOAD_BEGIN;event.offset=0;franchise_load_begin(s,&event,7,FRANCHISE_SAVE_BYTES,9);require(s->phase==FRANCHISE_LOAD_READING);}
static void input(FranchiseLoadRead *s){event.stage=FRANCHISE_LOAD_INPUT;event.offset=0;franchise_load_input(s,&event,7,source.payload_sha256);}
int main(void) {
    FranchiseLoadRead state;read_event.guest_mapped=1;read_event.guest_address=event.buffer;
    read_event.read.bytes="borrowed";read_event.read.completed=read_event.read.requested=FRANCHISE_SAVE_BYTES;
    source.sequence=5;source.guest_mapped=1;source.guest_address=event.buffer;source.file_size=FRANCHISE_SAVE_BYTES;
    memset(source.payload_sha256,'a',64);
    begin(&state);require(franchise_load_read_begin(&state,&read_event)==1);
    franchise_load_read_finish(&state,1,&source);input(&state);require(state.phase==FRANCHISE_LOAD_INPUT_MATCHED);
    event.stage=FRANCHISE_LOAD_DECODED;event.offset=FRANCHISE_SAVE_BYTES;franchise_load_decoded(&state,&event,7);
    require(state.phase==FRANCHISE_LOAD_DECODED_SEEN && state.source.sequence==5);
    /* A new load cannot inherit a matching read from a prior load. */
    event.stage=FRANCHISE_LOAD_BEGIN;event.offset=0;franchise_load_begin(&state,&event,7,FRANCHISE_SAVE_BYTES,9);
    require(state.epoch==2 && !state.source.sequence);franchise_load_read_finish(&state,1,&source);input(&state);require(state.phase==FRANCHISE_LOAD_INVALID);
    begin(&state);require(franchise_load_read_begin(&state,&read_event)==1);
    require(!franchise_load_read_begin(&state,&read_event) && state.phase==FRANCHISE_LOAD_INVALID);
    begin(&state);--read_event.read.completed;require(!franchise_load_read_begin(&state,&read_event) && state.phase==FRANCHISE_LOAD_INVALID);++read_event.read.completed;
    begin(&state);read_event.guest_address=0x300000;require(!franchise_load_read_begin(&state,&read_event) && state.phase==FRANCHISE_LOAD_READING);read_event.guest_address=event.buffer;
    begin(&state);read_event.guest_mapped=0;require(!franchise_load_read_begin(&state,&read_event));input(&state);require(state.phase==FRANCHISE_LOAD_INVALID);read_event.guest_mapped=1;
    begin(&state);franchise_load_read_begin(&state,&read_event);franchise_load_read_finish(&state,1,&source);
    event.stage=FRANCHISE_LOAD_INPUT;char changed[65];memcpy(changed,source.payload_sha256,65);changed[0]='b';franchise_load_input(&state,&event,7,changed);require(state.phase==FRANCHISE_LOAD_INVALID);
    begin(&state);franchise_load_read_begin(&state,&read_event);franchise_load_read_finish(&state,1,&source);
    event.stage=FRANCHISE_LOAD_INPUT;franchise_load_input(&state,&event,8,source.payload_sha256);require(state.phase==FRANCHISE_LOAD_INVALID);
    begin(&state);franchise_load_read_begin(&state,&read_event);franchise_load_read_finish(&state,1,&source);input(&state);
    require(!franchise_load_read_begin(&state,&read_event) && state.phase==FRANCHISE_LOAD_INVALID);
    begin(&state);franchise_load_read_begin(&state,&read_event);franchise_load_read_finish(&state,1,NULL);require(state.phase==FRANCHISE_LOAD_INVALID);
    begin(&state);event.stage=FRANCHISE_LOAD_BEGIN;franchise_load_begin(&state,&event,7,FRANCHISE_SAVE_BYTES,9);require(state.phase==FRANCHISE_LOAD_INVALID);
    begin(&state);event.stage=FRANCHISE_LOAD_DECODED;event.offset=FRANCHISE_SAVE_BYTES;franchise_load_decoded(&state,&event,7);require(state.phase==FRANCHISE_LOAD_INVALID);
    begin(&state);state.epoch=UINT64_MAX;event.stage=FRANCHISE_LOAD_BEGIN;event.offset=0;franchise_load_begin(&state,&event,7,FRANCHISE_SAVE_BYTES,9);require(state.phase==FRANCHISE_LOAD_INVALID && state.epoch==UINT64_MAX);
    return 0;
}
