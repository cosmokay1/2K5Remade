#include "nfl2k5_franchise_host.h"
#include "host_client.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include <string.h>

static FranchiseHostClient *franchise_client;
static volatile LONG franchise_owner_thread;
static volatile LONG franchise_foreign_sign_logged;
static int hello_pending, hello_failed;
static int context_enabled, hello_consumed, context_pending;
static unsigned long long context_revision;
static unsigned context_sequence, context_logged;
static int positive_limit(const wchar_t *text, unsigned long long *value)
{
    unsigned long long limit=0;
    if (!text || !*text) return 0;
    for (;*text;++text) {
        if (*text<L'0' || *text>L'9' || limit>(9223372036854775807ULL-(*text-L'0'))/10) return 0;
        limit=limit*10+(*text-L'0');
    }
    if (!limit) return 0;
    *value=limit;
    return 1;
}
void nfl2k5_franchise_stop(void)
{
    InterlockedExchange(&franchise_owner_thread, 0);
    InterlockedExchange(&franchise_foreign_sign_logged, 0);
    hello_pending = hello_failed = 0;
    context_enabled = hello_consumed = context_pending = 0;
    context_sequence = context_logged = 0;
    franchise_host_destroy(franchise_client);
    franchise_client = NULL;
}
void nfl2k5_franchise_on_fsm(uint32_t descriptor, int push)
{
    /* Guest callbacks may run on another host thread. Do not hand a single-owner
     * client to it, block the callback, or move ownership implicitly. */
    DWORD owner = (DWORD)InterlockedCompareExchange(&franchise_owner_thread, 0, 0);
    DWORD caller = GetCurrentThreadId();
    if (owner != caller) {
        if (owner && push && descriptor == 0x00557B2Cu &&
            !InterlockedCompareExchange(&franchise_foreign_sign_logged, 1, 0))
            fprintf(stderr, "[FRANCHISE] Signing callback on foreign thread: owner=%lu caller=%lu; transport not accessed.\n",
                (unsigned long)owner, (unsigned long)caller);
        return;
    }
    if (!franchise_client || hello_failed) return;
    if (hello_pending || context_pending) {
        int ready = 0;
        static char response[65536];
        size_t required = 0;
        if (franchise_host_ready(franchise_client, &ready) != FRANCHISE_HOST_OK)
            goto failed;
        if (!ready) return;
        if (franchise_host_take(franchise_client, response, sizeof(response), &required) != FRANCHISE_HOST_OK)
            goto failed;
        if (context_pending) {
            context_pending = 0;
            if (context_logged++ < 16)
                fprintf(stderr, "[FRANCHISE] Read-only signing context reply: %s\n", response);
        } else {
            hello_pending = 0;
            hello_consumed = 1;
        /* Receipt is not authorization. Native submit still rejects AI without
         * a validated hello grant; the service rechecks remote control per call. */
        fprintf(stderr, "[FRANCHISE] Control handshake reply consumed.\n");
        }
    }
    if (push && descriptor == 0x00557B2Cu && (!context_enabled || !hello_consumed)) {
        static const char request[] = "{\"protocol\":1,\"request_id\":\"game-sign-hello\",\"operation\":\"hello\"}";
        if (franchise_host_submit(franchise_client, request, sizeof(request) - 1) != FRANCHISE_HOST_OK)
            goto failed;
        hello_pending = 1;
    }
    return;
failed:
    hello_failed = 1;
    fprintf(stderr, "[FRANCHISE] Control handshake transport unavailable; no AI request submitted.\n");
}
int nfl2k5_franchise_context_enabled(void)
{
    return (DWORD)InterlockedCompareExchange(&franchise_owner_thread, 0, 0) == GetCurrentThreadId()
        && context_enabled && !hello_failed;
}
static int safe_name(const char *text, size_t capacity)
{
    const char *end = memchr(text, 0, capacity);
    if (!end || end == text) return 0;
    for (;text < end; ++text)
        if ((unsigned char)*text < 32 || *text == '"' || *text == '\\') return 0;
    return 1;
}
static int safe_hex(const char *text, size_t digits)
{
    if (text[digits]) return 0;
    for (size_t i=0; i<digits; ++i)
        if (!text[i] || !strchr("0123456789abcdef", text[i])) return 0;
    return 1;
}
void nfl2k5_franchise_signing_context(const FranchiseSigningObservation *o)
{
    if (!nfl2k5_franchise_context_enabled() || !franchise_client || !hello_consumed ||
        hello_pending || context_pending || !o || o->team_index >= 32 || o->calendar[5] > 255 ||
        !safe_name(o->first_name,sizeof(o->first_name)) || !safe_name(o->last_name,sizeof(o->last_name)) ||
        !safe_hex(o->photo,8) || !safe_hex(o->dob,6)) return;
    char request[4096];
    int length = snprintf(request,sizeof(request),
        "{\"protocol\":1,\"request_id\":\"game-sign-context-%u\",\"operation\":\"signing_context\","
        "\"expected_revision\":%llu,\"timeout_ms\":10000,\"observation\":{"
        "\"biography\":{\"source_slot\":%u,\"first_name\":\"%s\",\"last_name\":\"%s\","
        "\"pbp_photo_raw\":\"%s\",\"dob_region_raw\":\"%s\"},"
        "\"team\":{\"table_index\":%u,\"table_mode\":2,\"payroll_raw\":%u,\"league_cap_raw\":%u,"
        "\"team_flag_raw\":%u,\"first_year_accumulator_raw\":%u},"
        "\"calendar\":{\"season_index\":%u,\"display_year\":%u,\"phase_01_raw\":%u,\"phase_02_raw\":%u,"
        "\"step_04_raw\":%u,\"step_05_raw\":%u,\"counter_08_raw\":%u}}}",
        ++context_sequence,context_revision,o->slot,o->first_name,o->last_name,o->photo,o->dob,
        o->team_index,o->payroll,o->cap,o->team_flag,o->accumulator,o->calendar[5],2004u+o->calendar[5],
        o->calendar[0],o->calendar[1],o->calendar[3],o->calendar[4],o->calendar[6]);
    if (length <= 0 || (size_t)length >= sizeof(request) ||
        franchise_host_submit(franchise_client,request,(size_t)length) != FRANCHISE_HOST_OK) {
        hello_failed = 1;
        fprintf(stderr,"[FRANCHISE] Signing context transport unavailable; no transaction submitted.\n");
        return;
    }
    context_pending = 1;
}
int nfl2k5_franchise_start(void)
{
    if (franchise_client) return 0; /* Never replace an owned live service. */
    const wchar_t *mode = _wgetenv(L"NFL2K5_FRANCHISE_PROVIDER");
    const wchar_t *python = _wgetenv(L"NFL2K5_FRANCHISE_PYTHON");
    const wchar_t *database = _wgetenv(L"NFL2K5_FRANCHISE_DATABASE");
    if (!mode) return 1; /* Compiling transport does not enable AI. */
    if (wcscmp(mode, L"vertex") || !python || !*python || !database || !*database) {
        fprintf(stderr, "[FRANCHISE] Explicit vertex provider, Python and database paths required.\n");
        return 0;
    }
    const wchar_t *guest_save = _wgetenv(L"NFL2K5_FRANCHISE_GUEST_SAVE");
    const wchar_t *guest_bindings = _wgetenv(L"NFL2K5_FRANCHISE_GUEST_BINDINGS");
    const wchar_t *guest_revision = _wgetenv(L"NFL2K5_FRANCHISE_GUEST_REVISION");
    int inspect_context = guest_save && *guest_save;
    if ((guest_bindings && *guest_bindings) || (guest_revision && *guest_revision)) inspect_context = 1;
    unsigned long long revision = 0;
    if (inspect_context && (!guest_save || !*guest_save || !guest_bindings || !*guest_bindings ||
        !guest_revision || !*guest_revision ||
        (wcscmp(guest_revision,L"0") && !positive_limit(guest_revision,&revision)))) return 0;
    const wchar_t *budget_database = _wgetenv(L"NFL2K5_FRANCHISE_AI_BUDGET_DATABASE");
    const wchar_t *budget_scope = _wgetenv(L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE");
    const wchar_t *budget_limit = _wgetenv(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT");
    const wchar_t *token_limit = _wgetenv(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT");
    FranchiseHostStatus status;
    if ((budget_database && *budget_database) || (budget_scope && *budget_scope) || (budget_limit && *budget_limit) ||
        (token_limit && *token_limit)) {
        unsigned long long limit = 0, tokens=0;
        if (!budget_database || !*budget_database || !budget_scope || !*budget_scope || !budget_limit || !*budget_limit) return 0;
        if (!positive_limit(budget_limit,&limit)) return 0;
        if (token_limit && *token_limit) {
            if (!positive_limit(token_limit,&tokens)) return 0;
            status=franchise_host_create_with_token_budget(python,database,FRANCHISE_HOST_VERTEX_RUNTIME,
                budget_database,budget_scope,limit,tokens,&franchise_client);
        } else {
            status = franchise_host_create_with_budget(python,database,FRANCHISE_HOST_VERTEX_RUNTIME,
                budget_database,budget_scope,limit,&franchise_client);
        }
    } else {
        status = franchise_host_create(python,database,FRANCHISE_HOST_VERTEX_RUNTIME,&franchise_client);
    }
    if (status != FRANCHISE_HOST_OK) {
        fprintf(stderr, "[FRANCHISE] Sidecar launch failed.\n");
        return 0;
    }
    /* A later verified franchise callback must perform hello and consume its
     * result before AI negotiation. Startup alone grants no AI access. */
    if (atexit(nfl2k5_franchise_stop)) {
        nfl2k5_franchise_stop();
        return 0;
    }
    hello_pending = hello_failed = 0;
    hello_consumed = context_pending = 0;
    context_enabled = inspect_context;
    context_revision = revision;
    context_sequence = context_logged = 0;
    InterlockedExchange(&franchise_foreign_sign_logged, 0);
    InterlockedExchange(&franchise_owner_thread, (LONG)GetCurrentThreadId());
    fprintf(stderr, "[FRANCHISE] Transport launched on owner thread=%lu; signing-screen control handshake available; guest transaction hooks remain unavailable.\n",
        (unsigned long)GetCurrentThreadId());
    return 1;
}
