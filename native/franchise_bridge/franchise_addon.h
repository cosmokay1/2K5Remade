/* Private application protocol, shared by franchise host wrapper and DLL. */
#ifndef NFL2K5_FRANCHISE_ADDON_H
#define NFL2K5_FRANCHISE_ADDON_H
#include <stdint.h>
#include "host_client.h"
#define FRANCHISE_FSM_EVENT "franchise.fsm.v1"
#define FRANCHISE_SIGNING_EVENT "franchise.signing.v1"
#define FRANCHISE_DISPLAY_SNAPSHOT "franchise.signing-display.v1"
typedef struct FranchiseFSMEvent { uint32_t object, descriptor, push; } FranchiseFSMEvent;
typedef struct FranchiseSigningEvent { uint32_t stage, context, result, code, stack; } FranchiseSigningEvent;
#endif
