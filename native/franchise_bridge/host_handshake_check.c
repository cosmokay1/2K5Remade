/* Authored transport stubs exercise game-host scheduling, never AI authority. */
#include "../../src/nfl2k5_franchise_host.h"
#include "host_client.h"
#include <windows.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static char owned;
static FranchiseHostMode expected_mode = FRANCHISE_HOST_VERTEX_RUNTIME;
static unsigned submissions, takes;
static int ready_value;
static DWORD owner;
static int reviewed_kind,reply_failed;
static unsigned reviewed_amount,reviewed_flags;
int franchise_host_reviewed_offer(FranchiseHostClient *c,unsigned int *amount,unsigned int *flags) {
    (void)c;assert(GetCurrentThreadId()==owner);*amount=reviewed_amount;*flags=reviewed_flags;return reviewed_kind;
}
int franchise_host_reply_failed(FranchiseHostClient *c){(void)c;return reply_failed;}
static char last_request[4096];
/* Near the transport limit, includes UTF-8 and data the compact display omits.
 * This fixture exercises ownership/framing, not the separate protocol parser. */
static char authored_response[65536];
static FranchiseNegotiationView full_view;
static int image_present;
static char image_digest[65];
int nfl2k5_franchise_source_path_matches(uint64_t epoch){return epoch!=0;}
int nfl2k5_franchise_read_loaded_source(char out[65],uint64_t *epoch){memset(out,'d',64);out[64]=0;*epoch=1;return 1;}
FranchiseHostStatus franchise_host_loaded_payload_matches(FranchiseHostClient *c,const char *hash){(void)c;(void)hash;return FRANCHISE_HOST_OK;}
int nfl2k5_franchise_read_image(char out[65]){memcpy(out,image_digest,65);return image_present;}
static FranchiseHostStatus take_status = FRANCHISE_HOST_OK;
int nfl2k5_franchise_read_finance(struct FranchiseFinanceSnapshot *out){(void)out;assert(0);return 0;}
int nfl2k5_franchise_read_identity(const struct FranchiseFinanceSnapshot *finance,struct FranchiseIdentitySnapshot *out){(void)finance;(void)out;assert(0);return 0;}
FranchiseHostStatus franchise_host_prepare_accepted(FranchiseHostClient *client,const void *finance,size_t size,const void *identity,size_t identity_size) {
    (void)client;(void)finance;(void)size;(void)identity;(void)identity_size;assert(0);return FRANCHISE_HOST_SERVICE_FAILURE;
}
FranchiseHostStatus franchise_host_observe_completed(FranchiseHostClient *client,const void *finance,size_t size,const void *identity,size_t identity_size) {
    (void)client;(void)finance;(void)size;(void)identity;(void)identity_size;return FRANCHISE_HOST_SERVICE_FAILURE;
}
int nfl2k5_franchise_publish_cap(const struct FranchiseCapEnforcement *p){(void)p;assert(0);return 0;}
FranchiseHostStatus franchise_host_authorize_accepted(FranchiseHostClient *c,const void *f,size_t n,const void *i,size_t m){(void)c;(void)f;(void)n;(void)i;(void)m;assert(0);return FRANCHISE_HOST_NOT_READY;}
int franchise_host_application(FranchiseHostClient *c,unsigned s,unsigned x,unsigned long long e,const void *f,size_t n,const void *i,size_t m,struct FranchiseCapEnforcement *p){(void)c;(void)s;(void)x;(void)e;(void)f;(void)n;(void)i;(void)m;(void)p;assert(0);return 0;}
int franchise_host_application_terms(FranchiseHostClient *c,unsigned long long e,unsigned *a,unsigned *f){(void)c;(void)e;(void)a;(void)f;return 0;}
FranchiseHostStatus franchise_host_restore_cap(FranchiseHostClient *c,unsigned long long e,const char *p,const void *f,size_t n,const void *i,size_t m){(void)c;(void)e;(void)p;(void)f;(void)n;(void)i;(void)m;assert(0);return FRANCHISE_HOST_NOT_READY;}
int franchise_host_take_restored_cap(FranchiseHostClient *c,struct FranchiseCapEnforcement *p){(void)c;(void)p;return 0;}
FranchiseHostStatus franchise_host_check_saved(FranchiseHostClient *client) {
    (void)client;assert(0);return FRANCHISE_HOST_SERVICE_FAILURE;
}
FranchiseHostStatus franchise_host_signing_display(const char *response,FranchiseSigningDisplay *out) {
    assert(response && out); memset(out,0,sizeof(*out));
    strcpy(out->priorities,"Authored priorities");return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_create(const wchar_t *python, const wchar_t *database,
    FranchiseHostMode mode, FranchiseHostClient **out)
{
    assert(python && database && mode == expected_mode);
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
    assert(size == strlen(bytes) && (strstr(bytes, "\"operation\":\"hello\"") || strstr(bytes,"\"operation\":\"bind_runtime\"") ||
        strstr(bytes, "\"operation\":\"signing_context\"") || strstr(bytes,"\"operation\":\"negotiate_proposal\"")));
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
    ++takes; *required = strlen(authored_response)+1;
    if (take_status != FRANCHISE_HOST_OK) return take_status;
    assert(capacity >= *required); memcpy(buffer, authored_response, *required);
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
    FranchiseSigningDisplay view={0};
    nfl2k5_franchise_display(&view); /* Renderer copy does not access transport. */
    nfl2k5_franchise_negotiation_view(&full_view);
    return 0;
}
static DWORD WINAPI foreign_preview(void *flags) {
    return nfl2k5_franchise_preview_offer(full_view.preview_epoch,1955,*(const uint32_t*)flags)?0:1;
}
int main(void)
{
    const char prefix[]="{\"result\":{\"reason\":\"";
    const char suffix[]="\xe2\x80\x99\",\"performance_context\":{\"saved_history\":[]},\"offer\":{\"salaries\":[6328000,3796000],\"signing_bonus\":6752000}},\"error\":null}";
    memset(authored_response,'r',sizeof(authored_response)-1);
    memcpy(authored_response,prefix,sizeof(prefix)-1);
    memcpy(authored_response+sizeof(authored_response)-sizeof(suffix),suffix,sizeof(suffix));
    assert(strlen(authored_response)==65535);
    memset(&full_view,0x7f,sizeof(full_view));
    assert(!nfl2k5_franchise_negotiation_view(&full_view));
    for(size_t i=0;i<sizeof(full_view);++i) assert(!((unsigned char*)&full_view)[i]);

    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_PREVIEW",L"0");
    owner = GetCurrentThreadId();
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_SIGNING",L"0");
    _wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_DATABASE", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_SAVE", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_BINDINGS", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_REVISION", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_SAVED_PERFORMANCE", L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_OFFER", L"");
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
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_OFFER", L"unknown");
    assert(!nfl2k5_franchise_start());
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_OFFER", L"1");
    image_present=1;memset(image_digest,'a',64);image_digest[64]=0;
    assert(nfl2k5_franchise_start());
    FranchiseSigningObservation observation={0};
    strcpy(observation.first_name,"Authored"); strcpy(observation.last_name,"Player");
    strcpy(observation.photo,"00000000"); strcpy(observation.dob,"000000");
    observation.slot=1; observation.payroll=4766; observation.cap=80500;
    observation.offer_amount=1949; observation.offer_flags=0x4D060004;
    nfl2k5_franchise_signing_context(&observation); assert(submissions==3);
    nfl2k5_franchise_on_fsm(0x557B2C,1); assert(submissions==4);
    assert(strstr(last_request,"\"operation\":\"bind_runtime\""));
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
    assert(strstr(last_request,"\"guest_offer\":{\"amount_word\":1949,\"flags_word\":1292238852}"));
    assert(strstr(last_request,"\"expected_revision\":0"));
    assert(strstr(last_request,"\"display_year\":2004"));
    nfl2k5_franchise_signing_context(&observation); assert(submissions==5);
    nfl2k5_franchise_poll(); /* Context collected on the same screen. */
    FranchiseSigningDisplay view={0};
    assert(nfl2k5_franchise_display(&view) && !strcmp(view.title,"Authored Player"));
    assert(nfl2k5_franchise_negotiation_view(&full_view));
    assert(!strcmp(full_view.summary.title,view.title) && !strcmp(full_view.response,authored_response));
    // Consumer edits never mutate the host-owned original or its v1 summary.
    full_view.response[0]='!';full_view.summary.title[0]='!';
    assert(nfl2k5_franchise_negotiation_view(&full_view) && !strcmp(full_view.response,authored_response));
    assert(!strcmp(full_view.summary.title,"Authored Player"));

    nfl2k5_franchise_signing_context(&observation); assert(submissions==5); /* Unchanged sample. */
    assert(nfl2k5_franchise_display(&view));
    nfl2k5_franchise_signing_context(NULL); assert(!nfl2k5_franchise_display(&view));
    assert(!nfl2k5_franchise_negotiation_view(&full_view) && !full_view.response[0] && !full_view.summary.title[0]);
    nfl2k5_franchise_signing_context(&observation); assert(nfl2k5_franchise_display(&view));
    observation.offer_amount=1950;
    nfl2k5_franchise_signing_context(&observation); assert(submissions==5); /* Debounce edits. */
    assert(!nfl2k5_franchise_display(&view));
    assert(!nfl2k5_franchise_negotiation_view(&full_view));
    Sleep(350);
    nfl2k5_franchise_signing_context(&observation); assert(submissions==6);
    ready_value=0;
    observation.offer_amount=1951;
    nfl2k5_franchise_signing_context(&observation); assert(submissions==6);
    ready_value=1;
    nfl2k5_franchise_poll(); /* Obsolete changed-offer receipt discarded. */
    nfl2k5_franchise_signing_context(&observation); assert(submissions==6);
    Sleep(350);
    nfl2k5_franchise_signing_context(&observation); assert(submissions==7);
    assert(strstr(last_request,"\"amount_word\":1951"));
    nfl2k5_franchise_signing_context(NULL);
    assert(!nfl2k5_franchise_display(&view));
    nfl2k5_franchise_poll(); /* Unreadable sample cannot consume a current receipt. */
    nfl2k5_franchise_signing_context(&observation); assert(submissions==8);
    nfl2k5_franchise_on_fsm(0,0); /* Pending response belongs to the closed screen. */
    nfl2k5_franchise_on_fsm(0x557B2C,1);
    nfl2k5_franchise_signing_context(&observation); assert(submissions==9);
    nfl2k5_franchise_poll();
    nfl2k5_franchise_on_fsm(0,0);
    assert(!nfl2k5_franchise_context_enabled());
    nfl2k5_franchise_signing_context(&observation); assert(submissions==9); /* Stale closed-screen observation. */
    nfl2k5_franchise_on_fsm(0x557B2C,1); assert(submissions==9); /* No redundant hello. */
    strcpy(observation.first_name,"Bad\"Name");
    nfl2k5_franchise_signing_context(&observation); assert(submissions==9);
    nfl2k5_franchise_stop();
    assert(!nfl2k5_franchise_negotiation_view(&full_view) && !full_view.response[0]);
    /* Same host path forwards any canonical load identity, with no name lookup. */
    for(unsigned i=0;i<2;++i) {
        memset(image_digest,'a'+i,64);image_digest[64]=0;image_present=1;
        assert(nfl2k5_franchise_start());
        nfl2k5_franchise_on_fsm(0x557B2C,1);
        assert(strstr(last_request,"\"loaded_image_sha256\":\"") && strstr(last_request,image_digest));
        nfl2k5_franchise_stop();
    }
    assert(nfl2k5_franchise_start());
    image_digest[0]='G';unsigned before=submissions;
    nfl2k5_franchise_on_fsm(0x557B2C,1);assert(submissions==before);
    nfl2k5_franchise_stop();
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_PREVIEW",L"1");
    _wputenv_s(L"NFL2K5_FRANCHISE_NEGOTIATION",L"1");
    assert(!nfl2k5_franchise_start()); // Read-only screen cannot submit AI proposals.
    _wputenv_s(L"NFL2K5_FRANCHISE_NEGOTIATION",L"0");
    assert(nfl2k5_franchise_start());
    image_digest[0]='a';
    nfl2k5_franchise_on_fsm(0x557B2C,1);
    assert(nfl2k5_franchise_negotiation_view(&full_view));
    assert(!strcmp(full_view.summary.title,"Contract negotiation") && !full_view.response[0]);
    nfl2k5_franchise_on_fsm(0,0);
    assert(!nfl2k5_franchise_negotiation_view(&full_view));
    assert(!nfl2k5_franchise_submit_held(&observation,nfl2k5_franchise_submission_epoch()));
    nfl2k5_franchise_stop();
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_EDIT",L"1");
    assert(nfl2k5_franchise_start());
    strcpy(observation.first_name,"Authored");
    nfl2k5_franchise_on_fsm(0x557B2C,1);nfl2k5_franchise_poll();
    nfl2k5_franchise_signing_context(&observation);nfl2k5_franchise_poll();
    assert(nfl2k5_franchise_negotiation_view(&full_view) && full_view.preview_enabled && !full_view.preview_pending);
    const unsigned long long epoch=full_view.preview_epoch;
    const uint32_t edited_flags=(observation.offer_flags&~0xe00f000fu)|0x40020005u;
    assert(!nfl2k5_franchise_preview_offer(epoch,0,edited_flags));
    assert(!nfl2k5_franchise_preview_offer(epoch,65536,edited_flags));
    assert(!nfl2k5_franchise_preview_offer(epoch,1955,edited_flags^0x10u)); // Reserved bits cannot change.
    assert(!nfl2k5_franchise_preview_offer(epoch,1955,(edited_flags&~0xf0000u)|0x80000u));
    assert(!nfl2k5_franchise_preview_offer(epoch,1955,(edited_flags&~15u)|11u));
    assert(!nfl2k5_franchise_preview_offer(epoch,1955,(edited_flags&0x1fffffffu)|0xe0000000u));
    const unsigned before_draft=submissions;
    thread=CreateThread(NULL,0,foreign_preview,(void*)&edited_flags,0,NULL);
    assert(thread && WaitForSingleObject(thread,3000)==WAIT_OBJECT_0);
    DWORD preview_exit=1;assert(GetExitCodeThread(thread,&preview_exit) && !preview_exit);CloseHandle(thread);
    assert(!nfl2k5_franchise_preview_offer(epoch,1956,edited_flags));
    assert(submissions==before_draft); // UI callback only copies intent.
    assert(nfl2k5_franchise_negotiation_view(&full_view) && full_view.preview_pending);
    nfl2k5_franchise_signing_context(&observation);
    assert(submissions==before_draft+1 && strstr(last_request,"\"operation\":\"signing_context\""));
    assert(strstr(last_request,"\"amount_word\":1955"));
    char expected_flags[64];snprintf(expected_flags,sizeof(expected_flags),"\"flags_word\":%u",edited_flags);
    assert(strstr(last_request,expected_flags));
    nfl2k5_franchise_poll();
    assert(nfl2k5_franchise_negotiation_view(&full_view) && !full_view.preview_pending && full_view.preview_epoch!=epoch);
    assert(!nfl2k5_franchise_preview_offer(epoch,1955,edited_flags)); // Consumed contexts cannot replay.
    assert(nfl2k5_franchise_preview_offer(full_view.preview_epoch,1956,edited_flags));
    ++observation.slot;nfl2k5_franchise_signing_context(&observation);
    assert(submissions==before_draft+1); // Changing player discards queued terms.
    assert(nfl2k5_franchise_negotiation_view(&full_view) && !full_view.response[0] && !full_view.preview_enabled);
    nfl2k5_franchise_on_fsm(0,0);
    assert(!nfl2k5_franchise_preview_offer(epoch,1955,edited_flags));
    nfl2k5_franchise_stop();
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_PREVIEW",L"0");
    assert(!nfl2k5_franchise_start()); // Editor cannot bypass read-only screen mode.
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_EDIT",L"bad");assert(!nfl2k5_franchise_start());
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_EDIT",L"0");
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_PREVIEW",L"bad");assert(!nfl2k5_franchise_start());
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_PREVIEW",L"1");
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_SUBMIT",L"1");
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_EDIT",L"1");
    _wputenv_s(L"NFL2K5_FRANCHISE_NEGOTIATION",L"0");
    assert(!nfl2k5_franchise_start()); // Explicit UI mode still requires controlled negotiation.
    _wputenv_s(L"NFL2K5_FRANCHISE_NEGOTIATION",L"1");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_SIGNING",L"1");
    assert(nfl2k5_franchise_start()); // Explicit application mode starts without granting any signing.
    nfl2k5_franchise_stop();
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_SIGNING",L"0");
    reviewed_kind=2;reviewed_amount=observation.offer_amount;reviewed_flags=observation.offer_flags;
    assert(nfl2k5_franchise_start());
    nfl2k5_franchise_on_fsm(0x557B2C,1);nfl2k5_franchise_poll();
    nfl2k5_franchise_signing_context(&observation);nfl2k5_franchise_poll();
    assert(nfl2k5_franchise_negotiation_view(&full_view) && full_view.submit_enabled);
    unsigned sent=submissions;
    assert(!nfl2k5_franchise_submission_epoch());
    assert(nfl2k5_franchise_submit_held(&observation,1)); // Native action still held if addon rendering fails.
    nfl2k5_franchise_signing_context(&observation);assert(submissions==sent); // No native-menu inference bypass.
    assert(!nfl2k5_franchise_send_offer(full_view.preview_epoch,reviewed_amount+1,reviewed_flags));
    assert(nfl2k5_franchise_send_offer(full_view.preview_epoch,reviewed_amount,reviewed_flags));
    assert(submissions==sent); // Renderer copies intent only.
    assert(!nfl2k5_franchise_send_offer(full_view.preview_epoch,reviewed_amount,reviewed_flags));
    assert(nfl2k5_franchise_negotiation_view(&full_view) && full_view.proposal_pending && !full_view.submit_enabled);
    nfl2k5_franchise_signing_context(&observation);
    assert(submissions==sent+1 && strstr(last_request,"\"operation\":\"negotiate_proposal\""));
    assert(strstr(last_request,"\"amendment_rule\":\"legacy_bonus_carry_v1\""));
    char failed_proposal[4096];strcpy(failed_proposal,last_request);
    reply_failed=1;nfl2k5_franchise_poll();reply_failed=0;reviewed_kind=0;
    assert(nfl2k5_franchise_negotiation_view(&full_view) && full_view.response[0] && full_view.notice[0]);
    assert(!full_view.submit_enabled && !full_view.proposal_pending && !full_view.preview_pending);
    assert(!nfl2k5_franchise_send_offer(full_view.preview_epoch,reviewed_amount,reviewed_flags));
    // Read-only recheck recovers without reopening or resending a negotiation.
    assert(nfl2k5_franchise_preview_offer(full_view.preview_epoch,reviewed_amount,reviewed_flags));
    nfl2k5_franchise_signing_context(&observation);reviewed_kind=2;nfl2k5_franchise_poll();
    assert(nfl2k5_franchise_negotiation_view(&full_view) && full_view.submit_enabled && !full_view.notice[0]);
    assert(nfl2k5_franchise_send_offer(full_view.preview_epoch,reviewed_amount,reviewed_flags));
    nfl2k5_franchise_signing_context(&observation);
    assert(!strcmp(last_request,failed_proposal)); // Same durable dialogue ID, not another agent contact.
    nfl2k5_franchise_poll();
    assert(nfl2k5_franchise_negotiation_view(&full_view) && !full_view.submit_enabled);
    assert(nfl2k5_franchise_preview_offer(full_view.preview_epoch,reviewed_amount,reviewed_flags));
    nfl2k5_franchise_signing_context(&observation);nfl2k5_franchise_poll();
    assert(nfl2k5_franchise_negotiation_view(&full_view) && full_view.submit_enabled);
    assert(nfl2k5_franchise_send_offer(full_view.preview_epoch,reviewed_amount,reviewed_flags));
    reviewed_kind=0;sent=submissions;nfl2k5_franchise_signing_context(&observation);
    assert(submissions==sent); // Owner rejects a grant revoked after the UI queued intent.
    assert(nfl2k5_franchise_negotiation_view(&full_view) && !full_view.submit_enabled && full_view.notice[0]);
    nfl2k5_franchise_on_fsm(0,0);nfl2k5_franchise_stop();
    reviewed_kind=0;reply_failed=1;
    assert(nfl2k5_franchise_start());nfl2k5_franchise_on_fsm(0x557B2C,1);
    const unsigned before_fallback=submissions;nfl2k5_franchise_poll();
    assert(submissions==before_fallback+1 && strstr(last_request,"\"operation\":\"bind_runtime\""));
    reply_failed=0;nfl2k5_franchise_poll();
    nfl2k5_franchise_signing_context(&observation);nfl2k5_franchise_poll();
    assert(nfl2k5_franchise_negotiation_view(&full_view) && full_view.preview_enabled && !full_view.submit_enabled);
    sent=submissions;nfl2k5_franchise_poll();assert(submissions==sent); // No AI reauthorization loop.
    nfl2k5_franchise_stop();
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_SUBMIT",L"bad");assert(!nfl2k5_franchise_start());
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_SUBMIT",L"0");
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_EDIT",L"0");
    _wputenv_s(L"NFL2K5_FRANCHISE_SCREEN_PREVIEW",L"0");
    _wputenv_s(L"NFL2K5_FRANCHISE_NEGOTIATION",L"0");
    _wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER",L"local-rules");
    _wputenv_s(L"NFL2K5_FRANCHISE_LOCAL_CONFIG",L"");
    assert(!nfl2k5_franchise_start());
    _wputenv_s(L"NFL2K5_FRANCHISE_LOCAL_CONFIG",L"authored-local-policy");
    expected_mode=FRANCHISE_HOST_LOCAL_RULES;
    assert(nfl2k5_franchise_start());nfl2k5_franchise_stop();
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE",L"forbidden-in-local-mode");
    assert(!nfl2k5_franchise_start());
    _wputenv_s(L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE",L"");
    _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_BINDINGS",L"");
    assert(!nfl2k5_franchise_start());
    return 0;
}
