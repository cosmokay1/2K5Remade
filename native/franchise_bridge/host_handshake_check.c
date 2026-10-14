/* Authored transport stubs exercise game-host scheduling, never AI authority. */
#include "../../src/nfl2k5_franchise_host.h"
#include "host_client.h"
#include <windows.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>

static char owned;
static unsigned submissions, takes;
static int ready_value;
static DWORD owner;
static char last_request[4096];
static FranchiseHostStatus take_status = FRANCHISE_HOST_OK;
FranchiseHostStatus franchise_host_create(const wchar_t *python, const wchar_t *database,
    FranchiseHostMode mode, FranchiseHostClient **out)
{
    assert(python && database && mode == FRANCHISE_HOST_VERTEX_RUNTIME);
    *out = (FranchiseHostClient *)&owned;
    return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_create_with_budget(const wchar_t *python, const wchar_t *database,
    FranchiseHostMode mode, const wchar_t *budget, const wchar_t *scope,
    unsigned long long limit, FranchiseHostClient **out)
{
    (void)budget; (void)scope; (void)limit;
    return franchise_host_create(python, database, mode, out);
}
FranchiseHostStatus franchise_host_create_with_token_budget(const wchar_t *python, const wchar_t *database,
    FranchiseHostMode mode, const wchar_t *budget, const wchar_t *scope,
    unsigned long long limit, unsigned long long tokens, FranchiseHostClient **out)
{
    (void)tokens;
    return franchise_host_create_with_budget(python, database, mode, budget, scope, limit, out);
}
FranchiseHostStatus franchise_host_submit(FranchiseHostClient *client, const char *bytes, size_t size)
{
    assert(client == (FranchiseHostClient *)&owned && GetCurrentThreadId() == owner);
    assert(size == strlen(bytes) && (strstr(bytes, "\"operation\":\"hello\"") ||
        strstr(bytes, "\"operation\":\"signing_context\"")));
    assert(!memchr(bytes, '\n', size) && !memchr(bytes, '\r', size));
    ++submissions;
    assert(size < sizeof(last_request)); memcpy(last_request,bytes,size+1);
    return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_ready(FranchiseHostClient *client, int *ready)
{
    assert(client == (FranchiseHostClient *)&owned && GetCurrentThreadId() == owner);
    *ready = ready_value;
    return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_take(FranchiseHostClient *client, char *buffer, size_t capacity, size_t *required)
{
    assert(client == (FranchiseHostClient *)&owned && GetCurrentThreadId() == owner);
    ++takes; *required = 3;
    if (take_status != FRANCHISE_HOST_OK) return take_status;
    assert(capacity >= 3); memcpy(buffer, "{}", 3);
    return FRANCHISE_HOST_OK;
}
void franchise_host_destroy(FranchiseHostClient *client)
{
    assert(!client || client == (FranchiseHostClient *)&owned);
}
static DWORD WINAPI foreign_callback(void *unused)
{
    (void)unused;
    nfl2k5_franchise_on_fsm(0x557B2C, 1);
    nfl2k5_franchise_poll();
    return 0;
}
int main(void)
{
    owner = GetCurrentThreadId();
    _wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_DATABASE", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_SAVE", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_BINDINGS", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_REVISION", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_SAVED_PERFORMANCE", L"");
    assert(nfl2k5_franchise_start());
    nfl2k5_franchise_on_fsm(0x557B2C, 1); assert(!submissions);
    _wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER", L"vertex");
    _wputenv_s(L"NFL2K5_FRANCHISE_PYTHON", L"authored-peer");
    _wputenv_s(L"NFL2K5_FRANCHISE_DATABASE", L"authored-state");
    assert(nfl2k5_franchise_start());
    HANDLE thread = CreateThread(NULL, 0, foreign_callback, NULL, 0, NULL);
    assert(thread && WaitForSingleObject(thread, 3000) == WAIT_OBJECT_0);
    CloseHandle(thread); assert(!submissions);
    nfl2k5_franchise_on_fsm(0x1234, 1);
    nfl2k5_franchise_on_fsm(0x557B2C, 0); assert(!submissions);
    nfl2k5_franchise_on_fsm(0x557B2C, 1); assert(submissions == 1);
    nfl2k5_franchise_on_fsm(0x557B2C, 1); assert(submissions == 1 && !takes);
    ready_value = 1;
    nfl2k5_franchise_on_fsm(0, 0); assert(takes == 1 && submissions == 1);
    nfl2k5_franchise_on_fsm(0x557B2C, 1); assert(submissions == 2);
    take_status = FRANCHISE_HOST_BUFFER_TOO_SMALL;
    nfl2k5_franchise_on_fsm(0, 0); assert(takes == 2);
    nfl2k5_franchise_on_fsm(0x557B2C, 1); assert(submissions == 2);
    nfl2k5_franchise_stop(); nfl2k5_franchise_on_fsm(0x557B2C, 1);
    assert(submissions == 2);
    take_status = FRANCHISE_HOST_OK; ready_value = 0;
    assert(nfl2k5_franchise_start());
    nfl2k5_franchise_on_fsm(0x557B2C, 1); assert(submissions == 3);
    nfl2k5_franchise_stop();
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_SAVE", L"authored-save");
    assert(!nfl2k5_franchise_start()); /* Partial source configuration fails. */
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_BINDINGS", L"authored-bindings");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_REVISION", L"-1");
    assert(!nfl2k5_franchise_start());
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_REVISION", L"0");
    _wputenv_s(L"NFL2K5_FRANCHISE_SAVED_PERFORMANCE", L"unknown");
    assert(!nfl2k5_franchise_start());
    _wputenv_s(L"NFL2K5_FRANCHISE_SAVED_PERFORMANCE", L"1");
    assert(nfl2k5_franchise_start());
    FranchiseSigningObservation observation={0};
    strcpy(observation.first_name,"Authored"); strcpy(observation.last_name,"Player");
    strcpy(observation.photo,"00000000"); strcpy(observation.dob,"000000");
    observation.slot=1; observation.payroll=4766; observation.cap=80500;
    nfl2k5_franchise_signing_context(&observation); assert(submissions==3);
    nfl2k5_franchise_on_fsm(0x557B2C,1); assert(submissions==4);
    nfl2k5_franchise_signing_context(&observation); assert(submissions==4);
    ready_value=1;
    unsigned before_takes=takes;
    thread=CreateThread(NULL,0,foreign_callback,NULL,0,NULL);
    assert(thread && WaitForSingleObject(thread,3000)==WAIT_OBJECT_0);
    CloseHandle(thread); assert(takes==before_takes && submissions==4);
    nfl2k5_franchise_poll(); /* Hello collected without leaving the screen. */
    nfl2k5_franchise_signing_context(&observation); assert(submissions==5);
    assert(strstr(last_request,"\"operation\":\"signing_context\""));
    assert(strstr(last_request,"\"performance_format\":\"saved_history_v1\""));
    assert(strstr(last_request,"\"expected_revision\":0"));
    assert(strstr(last_request,"\"display_year\":2004"));
    nfl2k5_franchise_signing_context(&observation); assert(submissions==5);
    nfl2k5_franchise_poll(); /* Context collected on the same screen. */
    nfl2k5_franchise_signing_context(&observation); assert(submissions==5); /* Once per entry. */
    nfl2k5_franchise_on_fsm(0,0);
    assert(!nfl2k5_franchise_context_enabled());
    nfl2k5_franchise_signing_context(&observation); assert(submissions==5); /* Stale closed-screen observation. */
    nfl2k5_franchise_on_fsm(0x557B2C,1); assert(submissions==5); /* No redundant hello. */
    strcpy(observation.first_name,"Bad\"Name");
    nfl2k5_franchise_signing_context(&observation); assert(submissions==5);
    nfl2k5_franchise_stop();
    return 0;
}
