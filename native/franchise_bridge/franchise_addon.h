/* Private application protocol, shared by franchise host wrapper and DLL. */
#ifndef NFL2K5_FRANCHISE_ADDON_H
#define NFL2K5_FRANCHISE_ADDON_H
#include <stdint.h>
#include "host_client.h"
#include "load_read.h"
#define FRANCHISE_FSM_EVENT "franchise.fsm.v1"
#define FRANCHISE_SIGN_SUBMIT_EVENT "franchise.sign-submit.v1"
#define FRANCHISE_SIGN_GATE_EVENT "franchise.sign-gate.v2"
/* Separate from legacy hold replies. Current production addon issues no grant.
 * Stage1 validates a prepared application; stage2 consumes its authorization.
 * Both require exact context, current control and an uninterrupted commit plan. */
#define FRANCHISE_SIGN_APPLICATION_EVENT "franchise.sign-application.v1"
#define FRANCHISE_SIGN_APPLICATION_AUTHORIZED 2
/* One-use notification after an authorized native success; payload uint32_t
 * context. Reply is ignored. This is neither saved proof nor a grant. */
#define FRANCHISE_SIGN_COMPLETED_EVENT "franchise.sign-completed.v1"
#define FRANCHISE_SIGN_JUDGMENT 1u
#define FRANCHISE_SIGN_PRECOMMIT 2u
#define FRANCHISE_SIGNING_EVENT "franchise.signing.v1"
#define FRANCHISE_DISPLAY_SNAPSHOT "franchise.signing-display.v1"
#define FRANCHISE_NEGOTIATION_VIEW_SNAPSHOT "franchise.negotiation-view.v1"
typedef struct FranchiseFSMEvent { uint32_t object, descriptor, push; } FranchiseFSMEvent;
typedef struct FranchiseSignGateEvent { uint32_t stage, context; } FranchiseSignGateEvent;
typedef struct FranchiseSigningEvent { uint32_t stage, context, result, code, stack; } FranchiseSigningEvent;
#endif
