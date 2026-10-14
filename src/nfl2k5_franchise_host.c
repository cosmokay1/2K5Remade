#include "nfl2k5_franchise_host.h"
#include "host_client.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>

static FranchiseHostClient *franchise_client;
static volatile LONG franchise_owner_thread;
static int hello_pending, hello_failed;
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
    hello_pending = hello_failed = 0;
    franchise_host_destroy(franchise_client);
    franchise_client = NULL;
}
void nfl2k5_franchise_on_fsm(uint32_t descriptor, int push)
{
    /* Guest callbacks may run on another host thread. Do not hand a single-owner
     * client to it, block the callback, or move ownership implicitly. */
    if ((DWORD)InterlockedCompareExchange(&franchise_owner_thread, 0, 0) != GetCurrentThreadId())
        return;
    if (!franchise_client || hello_failed) return;
    if (hello_pending) {
        int ready = 0;
        char response[4096];
        size_t required = 0;
        if (franchise_host_ready(franchise_client, &ready) != FRANCHISE_HOST_OK)
            goto failed;
        if (!ready) return;
        if (franchise_host_take(franchise_client, response, sizeof(response), &required) != FRANCHISE_HOST_OK)
            goto failed;
        hello_pending = 0;
        /* Receipt is not authorization. Native submit still rejects AI without
         * a validated hello grant; the service rechecks remote control per call. */
        fprintf(stderr, "[FRANCHISE] Control handshake reply consumed.\n");
    }
    if (push && descriptor == 0x00557B2Cu) {
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
    InterlockedExchange(&franchise_owner_thread, (LONG)GetCurrentThreadId());
    fprintf(stderr, "[FRANCHISE] Transport launched; signing-screen control handshake available; guest transaction hooks remain unavailable.\n");
    return 1;
}
