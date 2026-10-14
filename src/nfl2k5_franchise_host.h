#ifndef NFL2K5_FRANCHISE_HOST_H
#define NFL2K5_FRANCHISE_HOST_H
#include <stdint.h>
/* Host entry thread only; no guest state access or automatic AI grant. */
int nfl2k5_franchise_start(void);
void nfl2k5_franchise_stop(void);
/* Nonblocking on the transport owner. A signing-screen push requests hello;
 * later FSM events consume it. The native client enforces the resulting grant. */
void nfl2k5_franchise_on_fsm(uint32_t descriptor, int push);
typedef struct {
    uint32_t slot, team_index, payroll, cap, team_flag, accumulator;
    uint32_t calendar[7]; /* phase1, phase2, team count, step4, step5, season, counter */
    char first_name[151], last_name[151], photo[9], dob[7];
} FranchiseSigningObservation;
/* Optional pinned-snapshot inspection only; never a transaction or AI grant. */
int nfl2k5_franchise_context_enabled(void);
void nfl2k5_franchise_signing_context(const FranchiseSigningObservation *observation);
#endif
