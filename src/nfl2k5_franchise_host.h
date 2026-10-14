#ifndef NFL2K5_FRANCHISE_HOST_H
#define NFL2K5_FRANCHISE_HOST_H
#include <stdint.h>
/* Host entry thread only; no guest state access or automatic AI grant. */
int nfl2k5_franchise_start(void);
void nfl2k5_franchise_stop(void);
/* Nonblocking on the transport owner. A signing-screen push requests hello;
 * later FSM events consume it. The native client enforces the resulting grant. */
void nfl2k5_franchise_on_fsm(uint32_t descriptor, int push);
#endif
