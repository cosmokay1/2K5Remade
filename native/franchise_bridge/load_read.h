/* Correlate one supported load's read/input/decoded checkpoints. No grant. */
#ifndef FRANCHISE_LOAD_READ_H
#define FRANCHISE_LOAD_READ_H
#include "save_read.h"
#include "../game_addon/file_read.h"
#define FRANCHISE_LOAD_EVENT "franchise.load-boundary.v1"
#define FRANCHISE_LOAD_READ_SNAPSHOT "franchise.load-read.v1"
#define FRANCHISE_LOAD_BEGIN 1u
#define FRANCHISE_LOAD_FAILED 2u
#define FRANCHISE_LOAD_INPUT 3u
#define FRANCHISE_LOAD_DECODED 4u
#define FRANCHISE_LOAD_ATTEMPT 5u
#define FRANCHISE_LOAD_READING 1u
#define FRANCHISE_LOAD_INPUT_MATCHED 2u
#define FRANCHISE_LOAD_DECODED_SEEN 3u
#define FRANCHISE_LOAD_INVALID 4u
typedef struct FranchiseLoadEvent {uint32_t stage,buffer,offset,table_offset,stack;} FranchiseLoadEvent;
typedef struct FranchiseLoadRead {
    uint64_t epoch;
    uint32_t phase,owner,buffer,table_offset,stack,read_seen;
    uint32_t raw_size,raw_kind,last_stage,last_offset;
    FranchiseSaveRead source;
} FranchiseLoadRead;
static inline void franchise_load_invalid(FranchiseLoadRead *state){state->phase=FRANCHISE_LOAD_INVALID;}
/* The router can return before it allocates a read buffer. Revoke the prior
 * checkpoint at entry, without reading a table or relying on later callbacks. */
static inline void franchise_load_attempt(FranchiseLoadRead *state) {
    uint64_t epoch=state->epoch;
    memset(state,0,sizeof(*state));state->epoch=epoch==UINT64_MAX?epoch:epoch+1;
    state->phase=FRANCHISE_LOAD_INVALID;state->last_stage=FRANCHISE_LOAD_ATTEMPT;
}
static inline void franchise_load_begin(FranchiseLoadRead *state,const FranchiseLoadEvent *event,
        uint32_t owner,uint32_t size,uint32_t kind) {
    uint64_t epoch=state->epoch;uint32_t previous=state->phase;
    memset(state,0,sizeof(*state));state->epoch=epoch==UINT64_MAX?epoch:epoch+1;
    state->phase=FRANCHISE_LOAD_INVALID;
    state->owner=owner;state->buffer=event->buffer;state->table_offset=event->table_offset;state->stack=event->stack;
    state->raw_size=size;state->raw_kind=kind;state->last_stage=event->stage;state->last_offset=event->offset;
    if(epoch==UINT64_MAX || previous==FRANCHISE_LOAD_READING || previous==FRANCHISE_LOAD_INPUT_MATCHED ||
       !owner || event->stage!=FRANCHISE_LOAD_BEGIN || !event->buffer || !event->stack || event->offset ||
       size!=FRANCHISE_SAVE_BYTES || kind!=9 || (uint64_t)event->buffer+size>UINT64_C(0x100000000))return;
    state->phase=FRANCHISE_LOAD_READING;
}
/* Sample the epoch before hashing native bytes; an old in-flight callback must
 * not be attached to a newer load. Partial/duplicate overlapping deliveries fail. */
static inline uint64_t franchise_load_read_begin(FranchiseLoadRead *state,const NFL2K5AddonFileReadV2 *event) {
    if((state->phase!=FRANCHISE_LOAD_READING && state->phase!=FRANCHISE_LOAD_INPUT_MATCHED) || event->guest_mapped!=1 || !event->read.completed)return 0;
    uint64_t begin=event->guest_address,end=begin+event->read.completed;
    if(end<begin || end>UINT64_C(0x100000000)) {franchise_load_invalid(state);return 0;}
    if(end<=state->buffer || begin>=(uint64_t)state->buffer+FRANCHISE_SAVE_BYTES)return 0;
    if(state->phase!=FRANCHISE_LOAD_READING || state->read_seen || begin!=state->buffer || event->read.completed!=FRANCHISE_SAVE_BYTES ||
       event->read.completed>event->read.requested || event->read.status || !event->read.bytes) {
        franchise_load_invalid(state);return 0;
    }
    state->read_seen=1;return state->epoch;
}
static inline void franchise_load_read_finish(FranchiseLoadRead *state,uint64_t epoch,const FranchiseSaveRead *source) {
    if(!epoch || epoch!=state->epoch || state->phase!=FRANCHISE_LOAD_READING)return;
    if(!source || !source->sequence || source->guest_mapped!=1 || source->guest_address!=state->buffer ||
       source->file_size!=FRANCHISE_SAVE_BYTES){franchise_load_invalid(state);return;}
    state->source=*source;
}
static inline int franchise_load_same(const FranchiseLoadRead *state,const FranchiseLoadEvent *event,uint32_t owner) {
    return owner && state->owner==owner && state->buffer==event->buffer && state->table_offset==event->table_offset && state->stack==event->stack;
}
static inline void franchise_load_input(FranchiseLoadRead *state,const FranchiseLoadEvent *event,uint32_t owner,const char *digest) {
    state->last_stage=event->stage;state->last_offset=event->offset;
    if(state->phase!=FRANCHISE_LOAD_READING || event->stage!=FRANCHISE_LOAD_INPUT || event->offset ||
       !franchise_load_same(state,event,owner) || !state->read_seen || !state->source.sequence ||
       !digest || memcmp(state->source.payload_sha256,digest,65)) {franchise_load_invalid(state);return;}
    state->phase=FRANCHISE_LOAD_INPUT_MATCHED;
}
static inline void franchise_load_decoded(FranchiseLoadRead *state,const FranchiseLoadEvent *event,uint32_t owner) {
    state->last_stage=event->stage;state->last_offset=event->offset;
    if(state->phase!=FRANCHISE_LOAD_INPUT_MATCHED || event->stage!=FRANCHISE_LOAD_DECODED ||
       event->offset!=FRANCHISE_SAVE_BYTES || !franchise_load_same(state,event,owner)){franchise_load_invalid(state);return;}
    state->phase=FRANCHISE_LOAD_DECODED_SEEN;
}
#endif
