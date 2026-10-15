#ifndef NFL2K5_FRANCHISE_HOST_CLIENT_H
#define NFL2K5_FRANCHISE_HOST_CLIENT_H
#include <stddef.h>
#include <wchar.h>
#ifdef __cplusplus
extern "C" {
#endif

/* One owner thread per handle. No guest memory, roster or money hooks.
 * Paths and mode are explicit; runtime never falls back to the fixture.
 * Destroy an existing handle before creating a replacement. */
typedef struct FranchiseHostClient FranchiseHostClient;
typedef enum FranchiseHostMode {
    FRANCHISE_HOST_OFFLINE_FIXTURE = 1,
    FRANCHISE_HOST_VERTEX_RUNTIME = 2
} FranchiseHostMode;
typedef enum FranchiseHostStatus {
    FRANCHISE_HOST_OK = 0,
    FRANCHISE_HOST_BUSY,
    FRANCHISE_HOST_NOT_READY,
    FRANCHISE_HOST_BUFFER_TOO_SMALL,
    FRANCHISE_HOST_INVALID_ARGUMENT,
    FRANCHISE_HOST_SERVICE_FAILURE
} FranchiseHostStatus;
typedef struct FranchiseSigningDisplay {
    char title[310], priorities[160], offer[256], history[160];
} FranchiseSigningDisplay;
/* Format an already transport-validated read-only context; no I/O or grant. */
FranchiseHostStatus franchise_host_signing_display(const char *response, FranchiseSigningDisplay *out);

FranchiseHostStatus franchise_host_create(const wchar_t* python, const wchar_t* database,
    FranchiseHostMode mode, FranchiseHostClient** out_client);
/* Vertex runtime only. Explicit persisted budget; no automatic credit or scope.
 * This request-only API and original create API start runtime AI disabled:
 * live Python policy also requires the explicit cumulative token ceiling. */
FranchiseHostStatus franchise_host_create_with_budget(const wchar_t* python, const wchar_t* database,
    FranchiseHostMode mode, const wchar_t* budget_database, const wchar_t* budget_scope,
    unsigned long long request_limit, FranchiseHostClient** out_client);
/* Adds an explicit cumulative token ceiling; both limits are positive and
 * bounded by INT64_MAX. Request-only creation never supplies a token policy. */
FranchiseHostStatus franchise_host_create_with_token_budget(const wchar_t* python, const wchar_t* database,
    FranchiseHostMode mode, const wchar_t* budget_database, const wchar_t* budget_scope,
    unsigned long long request_limit, unsigned long long token_limit, FranchiseHostClient** out_client);
/* Explicit UTF-8 JSON bytes, excluding terminator; max 4095, no NUL/CR/LF.
 * A pending or unread cached reply rejects the next submission as BUSY.
 * AI negotiation and journal writes require a validated successful hello grant;
 * journal writes additionally require advertised journal operations. Server access is
 * checked again per request; ai_disabled/failedhello clears the local grant.
 * Manual and read operations remain available without an AI grant. */
FranchiseHostStatus franchise_host_submit(FranchiseHostClient* client, const char* bytes, size_t length);
/* Queue preparation only for the last consumed, validated captured acceptance.
 * Requires hello AI grant and advertised journal support. NOT_READY means no
 * accepted proposal. Supply used bytes of the fresh addon financial and identity
 * snapshots; the service checks both SHA256s against the server-owned save.
 * This is neither an atomic live read nor a guest write grant. */
FranchiseHostStatus franchise_host_prepare_accepted(FranchiseHostClient* client,
    const void* finance_state, size_t finance_size, const void* identity_state, size_t identity_size);
/* Owner only; copy/hash completed live snapshots for the existing journal.
 * No transport wait or guest writes. May record while a status request is busy;
 * the next idle check must compare these hashes before any saved confirmation.
 * Repeating identical data is allowed; changing it requires explicit recovery. */
FranchiseHostStatus franchise_host_observe_completed(FranchiseHostClient* client,
    const void* finance_state, size_t finance_size, const void* identity_state, size_t identity_size);
/* Queue a read-only saved-state check for the prepared journal. Only a validated
 * candidate after-save plus the existing hello grant can queue confirmation;
 * the server rechecks current authority and bytes. NOT_READY means no journal or
 * terminal confirmed/cancelled state. Never authorizes guest writes or inference. */
FranchiseHostStatus franchise_host_check_saved(FranchiseHostClient* client);
/* Nonblocking; reports 1 for an unread cached reply or completed transport task. */
FranchiseHostStatus franchise_host_ready(FranchiseHostClient* client, int* ready_out);
/* required_size includes the NUL terminator. NULL+0 queries a ready reply's
 * size. BUFFER_TOO_SMALL caches it; only a successful copy permits submission.
 * NOT_READY never waits for the sidecar. Failed calls return static statuses. */
FranchiseHostStatus franchise_host_take(FranchiseHostClient* client, char* buffer,
    size_t capacity, size_t* required_size);
/* NULL-safe; stops the owned child before joining the transport worker.
 * Not a render callback: destruction waits for process/worker cleanup. */
void franchise_host_destroy(FranchiseHostClient* client);

#ifdef __cplusplus
}
#endif
#endif
