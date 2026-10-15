/* Loaded-file origin evidence only; never an active-session or write grant. */
#ifndef FRANCHISE_SOURCE_BINDING_H
#define FRANCHISE_SOURCE_BINDING_H
#include "load_read.h"
#define FRANCHISE_SOURCE_MATCH_SNAPSHOT "franchise.loaded-source.v1"
typedef struct FranchiseSourceMatch {
    uint64_t epoch;
    uint32_t configured,matched;
    FranchiseSaveRead source;
} FranchiseSourceMatch;
#endif
