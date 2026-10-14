#ifndef NFL2K5_FRANCHISE_HOST_H
#define NFL2K5_FRANCHISE_HOST_H
/* Host entry thread only; no guest state access or automatic AI grant. */
int nfl2k5_franchise_start(void);
void nfl2k5_franchise_stop(void);
#endif
