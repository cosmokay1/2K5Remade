/* Host-owned synchronous read scope; no lock acquisition or write authority. */
#ifndef NFL2K5_ADDON_READ_SCOPE_H
#define NFL2K5_ADDON_READ_SCOPE_H
#include <stdint.h>
#include <limits.h>
typedef struct NFL2K5AddonReadScope { uint64_t serial; unsigned depth; } NFL2K5AddonReadScope;
static void addon_read_begin(NFL2K5AddonReadScope *scope,uint64_t serial) {
    if(scope->depth==UINT_MAX) {scope->serial=0;return;}
    if(scope->depth++==0) scope->serial=serial;
}
static void addon_read_end(NFL2K5AddonReadScope *scope) {
    if(scope->depth && --scope->depth==0) scope->serial=0;
}
static int addon_read_allowed(const NFL2K5AddonReadScope *scope,uint64_t serial) {
    return scope->depth && scope->serial && scope->serial==serial;
}
#endif
