#ifndef NFL2K5_SIDECAR_ADAPTER_H
#define NFL2K5_SIDECAR_ADAPTER_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Existing generated-code callbacks. Read-only game observations; never a
 * transaction, remote-control grant or proof of mod-pack compatibility. */
void nfl2k5_diag_fsm(uint32_t object, uint32_t descriptor, int push);
/* Nonzero defers the original transaction before any contract writes. */
int nfl2k5_franchise_hold_signing(uint32_t context);
void nfl2k5_diag_signing(uint32_t stage, uint32_t context, uint32_t result,
                       uint32_t return_code, uint32_t stack);
#ifdef NFL2K5_FRANCHISE_CLIENT
/* Called from the existing input owner; no blocking transport or guest writes. */
void nfl2k5_franchise_guest_poll(void);
#endif
#ifdef __cplusplus
}
#endif
#endif
