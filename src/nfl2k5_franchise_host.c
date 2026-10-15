#include "nfl2k5_franchise_host.h"
#include "host_client.h"
#include "finance_state.h"
#include "identity_state.h"
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
static int signing_active, context_sent;
static int saved_performance;
static int inspect_guest_offer;
static int proposal_requested, proposal_sent, proposal_pending;
static int journal_enabled, journal_pending, journal_locked;
static volatile LONG completion_failed;
static unsigned long long journal_next_check;
static char journal_last_reply[65536];
/* One bounded submit intent. Foreign callbacks never inspect owner state or
 * touch the transport. Screen transitions/stop invalidate the copied intent. */
static SRWLOCK submission_lock=SRWLOCK_INIT;
static int submission_enabled, submission_active, submission_pending;
static unsigned long long submission_epoch;
static FranchiseSigningObservation submitted_observation;
static void submission_screen(int active) {
    AcquireSRWLockExclusive(&submission_lock);
    submission_active=active;submission_pending=0;++submission_epoch;
    ReleaseSRWLockExclusive(&submission_lock);
}
static unsigned long long context_revision;
static unsigned context_sequence, context_logged;
static unsigned long long request_session;
static FranchiseSigningObservation observed, requested;
static int observation_valid, observation_fresh;
static unsigned long long changed_tick, screen_epoch, requested_epoch;
static SRWLOCK display_lock=SRWLOCK_INIT;
static FranchiseSigningDisplay display;
static int display_valid;
static void clear_display(void) {
    AcquireSRWLockExclusive(&display_lock);
    memset(&display,0,sizeof(display));
    display_valid=0;
    ReleaseSRWLockExclusive(&display_lock);
}
int nfl2k5_franchise_display(FranchiseSigningDisplay *out) {
    if(!out) return 0;
    AcquireSRWLockShared(&display_lock);
    *out=display;
    if(!display_valid) memset(out,0,sizeof(*out));
    ReleaseSRWLockShared(&display_lock);
    return out->title[0]!=0;
}
static int same_observation(const FranchiseSigningObservation *a,const FranchiseSigningObservation *b)
{
    return a->slot==b->slot && a->team_index==b->team_index && a->payroll==b->payroll && a->cap==b->cap &&
        a->team_flag==b->team_flag && a->accumulator==b->accumulator &&
        a->offer_amount==b->offer_amount && a->offer_flags==b->offer_flags &&
        !memcmp(a->calendar,b->calendar,sizeof(a->calendar)) &&
        !strcmp(a->first_name,b->first_name) && !strcmp(a->last_name,b->last_name) &&
        !strcmp(a->photo,b->photo) && !strcmp(a->dob,b->dob);
}
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
    clear_display();
    InterlockedExchange(&franchise_owner_thread, 0);
    InterlockedExchange(&franchise_foreign_sign_logged, 0);
    hello_pending = hello_failed = 0;
    context_enabled = hello_consumed = context_pending = 0;
    saved_performance = 0;
    inspect_guest_offer = 0;
    AcquireSRWLockExclusive(&submission_lock);
    submission_enabled=submission_active=submission_pending=0;++submission_epoch;
    ReleaseSRWLockExclusive(&submission_lock);
    proposal_requested=proposal_sent=proposal_pending=0;
    journal_enabled=journal_pending=journal_locked=0;
    InterlockedExchange(&completion_failed,0);
    journal_next_check=0;journal_last_reply[0]=0;
    context_sequence = context_logged = 0;
    signing_active = context_sent = 0;
    observation_valid = observation_fresh = 0;
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
    int active=push && descriptor==0x00557B2Cu;
    if (active || active!=signing_active) {
        clear_display();
        ++screen_epoch;
        submission_screen(active);
        context_sent=observation_valid=observation_fresh=0;
        proposal_requested=proposal_sent=0;
    }
    signing_active=active;
    nfl2k5_franchise_poll();
    if (hello_failed || hello_pending || context_pending || journal_locked) return;
    if (push && descriptor == 0x00557B2Cu && (!context_enabled || !hello_consumed)) {
        static const char request[] = "{\"protocol\":1,\"request_id\":\"game-sign-hello\",\"operation\":\"hello\"}";
        if (franchise_host_submit(franchise_client, request, sizeof(request) - 1) != FRANCHISE_HOST_OK)
            goto failed;
        hello_pending = 1;
    }
    return;
failed:
    hello_failed = 1;
    clear_display();
    fprintf(stderr, "[FRANCHISE] Control handshake transport unavailable; no AI request submitted.\n");
}
void nfl2k5_franchise_poll(void)
{
    if ((DWORD)InterlockedCompareExchange(&franchise_owner_thread,0,0) != GetCurrentThreadId() ||
        !franchise_client || hello_failed) return;
    if(InterlockedCompareExchange(&completion_failed,0,0)) goto failed;
    if (hello_pending || context_pending || journal_pending) {
        int ready = 0;
        static char response[65536];
        size_t required = 0;
        if (franchise_host_ready(franchise_client, &ready) != FRANCHISE_HOST_OK)
            goto failed;
        if (!ready) return;
        if (franchise_host_take(franchise_client, response, sizeof(response), &required) != FRANCHISE_HOST_OK)
            goto failed;
        if(journal_pending) {
            journal_pending=0;
            journal_next_check=GetTickCount64()+2000;
            /* A lost/error receipt may still follow a committed preparation.
             * Never unlock or submit another offer without journal recovery. */
            if(strcmp(journal_last_reply,response)) {
                snprintf(journal_last_reply,sizeof(journal_last_reply),"%s",response);
                fprintf(stderr,"[FRANCHISE] Held signing saved-state reply: %s\n",response);
            }
            if(signing_active && observation_valid && observation_fresh &&
               screen_epoch==requested_epoch && same_observation(&observed,&requested)) {
                FranchiseSigningDisplay next={0};
                if(franchise_host_signing_display(response,&next)!=FRANCHISE_HOST_OK) {
                    snprintf(next.offer,sizeof(next.offer),"Signing paused. Original signing remains held.");
                    snprintf(next.history,sizeof(next.history),"Check saved-signing recovery before further offers.");
                }
                snprintf(next.title,sizeof(next.title),"%s %s",requested.first_name,requested.last_name);
                AcquireSRWLockExclusive(&display_lock);display=next;display_valid=1;ReleaseSRWLockExclusive(&display_lock);
            }
        } else if (context_pending) {
            context_pending = 0;
            const int was_proposal=proposal_pending;proposal_pending=0;
            int current=signing_active && observation_valid && observation_fresh &&
                screen_epoch==requested_epoch && same_observation(&observed,&requested);
            if(current) {
                FranchiseSigningDisplay next={0};
                if(franchise_host_signing_display(response,&next)==FRANCHISE_HOST_OK) {
                    snprintf(next.title,sizeof(next.title),"%s %s",observed.first_name,observed.last_name);
                    AcquireSRWLockExclusive(&display_lock); display=next; display_valid=1; ReleaseSRWLockExclusive(&display_lock);
                } else clear_display();
            } else clear_display();
            /* Changed terms retain the debounce; unreadable or new-screen
             * samples may retry once a valid observation becomes available. */
            if (!observation_valid || !observation_fresh || screen_epoch!=requested_epoch)
                context_sent=0;
            if (context_logged++ < 16) {
                if (current)
                    fprintf(stderr, "[FRANCHISE] %s reply: %s\n", was_proposal ? "Held negotiation" : "Read-only signing context", response);
                else fprintf(stderr,"[FRANCHISE] Discarded obsolete signing context reply.\n");
            }
            if(current && was_proposal && journal_enabled) {
                /* This owner read binds preparation to the observed league.
                 * It does not lock guest mutations or authorize application. */
                FranchiseFinanceSnapshot finance;
                const int captured=nfl2k5_franchise_read_finance(&finance);
                FranchiseIdentitySnapshot *identity=malloc(sizeof(*identity));
                const int identified=captured && identity && nfl2k5_franchise_read_identity(&finance,identity);
                const FranchiseHostStatus status=franchise_host_prepare_accepted(franchise_client,
                    captured?finance.bytes:NULL,captured?finance.size:0,
                    identified?identity->bytes:NULL,identified?identity->size:0);
                free(identity);
                if(status!=FRANCHISE_HOST_NOT_READY) {
                    journal_locked=1;
                    if(status!=FRANCHISE_HOST_OK) goto failed;
                    journal_pending=1;
                    AcquireSRWLockExclusive(&display_lock);
                    snprintf(display.offer,sizeof(display.offer),"Preparing accepted terms. Signing remains held.");
                    ReleaseSRWLockExclusive(&display_lock);
                }
            }
        } else {
            hello_pending = 0;
            hello_consumed = 1;
            /* Receipt is not authorization. Native submit still rejects AI without
             * a validated hello grant; the service rechecks remote control per call. */
            fprintf(stderr, "[FRANCHISE] Control handshake reply consumed.\n");
        }
    }
    if(journal_enabled && journal_locked && !journal_pending && GetTickCount64()>=journal_next_check) {
        const FranchiseHostStatus status=franchise_host_check_saved(franchise_client);
        if(status==FRANCHISE_HOST_OK) journal_pending=1;
        else if(status==FRANCHISE_HOST_NOT_READY) journal_next_check=~0ULL;
        else goto failed;
    }
    return;
failed:
    hello_failed = 1;
    clear_display();
    fprintf(stderr,"[FRANCHISE] Sidecar transport unavailable; signing remains held. Check journal recovery.\n");
}
int nfl2k5_franchise_completed(void)
{
    /* Foreign callbacks cannot read owner/client state or hand unchecked guest
     * pointers across threads. Leave the durable journal for explicit recovery. */
    if((DWORD)InterlockedCompareExchange(&franchise_owner_thread,0,0)!=GetCurrentThreadId()) {
        InterlockedExchange(&completion_failed,1);return 0;
    }
    if(!franchise_client || hello_failed || !journal_enabled || !journal_locked) {
        InterlockedExchange(&completion_failed,1);return 0;
    }
    FranchiseFinanceSnapshot finance;
    FranchiseIdentitySnapshot *identity=malloc(sizeof(*identity));
    const int captured=identity && nfl2k5_franchise_read_finance(&finance) &&
        nfl2k5_franchise_read_identity(&finance,identity);
    const FranchiseHostStatus status=captured ? franchise_host_observe_completed(franchise_client,
        finance.bytes,finance.size,identity->bytes,identity->size) : FRANCHISE_HOST_INVALID_ARGUMENT;
    free(identity);
    if(status!=FRANCHISE_HOST_OK) {InterlockedExchange(&completion_failed,1);return 0;}
    journal_next_check=0;
    return 1;
}
int nfl2k5_franchise_context_enabled(void)
{
    return (DWORD)InterlockedCompareExchange(&franchise_owner_thread, 0, 0) == GetCurrentThreadId()
        && context_enabled && signing_active && hello_consumed && !hello_pending && !hello_failed;
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
static int valid_observation(const FranchiseSigningObservation *o) {
    return o && o->team_index<32 && o->calendar[5]<=255 && o->offer_amount<=65535 &&
        safe_name(o->first_name,sizeof(o->first_name)) && safe_name(o->last_name,sizeof(o->last_name)) &&
        safe_hex(o->photo,8) && safe_hex(o->dob,6);
}
static void consume_submission(const FranchiseSigningObservation *o) {
    int matches=0;
    AcquireSRWLockExclusive(&submission_lock);
    if(submission_pending) {
        matches=submission_enabled && submission_active && o && same_observation(o,&submitted_observation);
        submission_pending=0;
    }
    ReleaseSRWLockExclusive(&submission_lock);
    if(matches && !proposal_sent) {
        proposal_requested=1;
        AcquireSRWLockExclusive(&display_lock);
        snprintf(display.title,sizeof(display.title),"%s %s",o->first_name,o->last_name);
        snprintf(display.offer,sizeof(display.offer),"Negotiating with player. Original signing held.");
        snprintf(display.history,sizeof(display.history),"Waiting for a controlled, cap-checked response.");
        display_valid=1;
        ReleaseSRWLockExclusive(&display_lock);
    }
}
void nfl2k5_franchise_signing_context(const FranchiseSigningObservation *o)
{
    if (!nfl2k5_franchise_context_enabled() || !franchise_client) return;
    observation_fresh=0; /* NULL or failed sampling invalidates reply freshness. */
    if (!o) {
        consume_submission(NULL);proposal_requested=0;
        AcquireSRWLockExclusive(&display_lock); display_valid=0; ReleaseSRWLockExclusive(&display_lock);
        return;
    }
    if (!valid_observation(o)) { consume_submission(NULL); proposal_requested=0; clear_display(); return; }
    if (!observation_valid || !same_observation(&observed,o)) {
        clear_display();
        observed=*o; observation_valid=1; changed_tick=GetTickCount64();
        proposal_requested=proposal_sent=0;
    }
    observation_fresh=1;
    if(journal_locked) return; /* Still sample freshness; never queue another offer. */
    consume_submission(o);
    AcquireSRWLockExclusive(&display_lock); display_valid=display.title[0]!=0; ReleaseSRWLockExclusive(&display_lock);
    if (context_pending || (!proposal_requested && context_sent && (same_observation(&requested,&observed) ||
        GetTickCount64()-changed_tick<300))) return;
    char request[4096];
    char offer_field[128] = {0};
    if (inspect_guest_offer) {
        if (o->offer_amount > 65535) return;
        snprintf(offer_field,sizeof(offer_field),"\"guest_offer\":{\"amount_word\":%u,\"flags_word\":%u},",
            o->offer_amount,o->offer_flags);
    }
    const int proposing=proposal_requested && !proposal_sent;
    int length = snprintf(request,sizeof(request),
        "{\"protocol\":1,\"request_id\":\"game-sign-%s-%lu-%llu-%u\",\"operation\":\"%s\","
        "%s%s\"expected_revision\":%llu,\"timeout_ms\":10000,\"observation\":{"
        "\"biography\":{\"source_slot\":%u,\"first_name\":\"%s\",\"last_name\":\"%s\","
        "\"pbp_photo_raw\":\"%s\",\"dob_region_raw\":\"%s\"},"
        "\"team\":{\"table_index\":%u,\"table_mode\":2,\"payroll_raw\":%u,\"league_cap_raw\":%u,"
        "\"team_flag_raw\":%u,\"first_year_accumulator_raw\":%u},"
        "\"calendar\":{\"season_index\":%u,\"display_year\":%u,\"phase_01_raw\":%u,\"phase_02_raw\":%u,"
        "\"step_04_raw\":%u,\"step_05_raw\":%u,\"counter_08_raw\":%u}}}",
        proposing ? "proposal" : "context",(unsigned long)GetCurrentProcessId(),request_session,++context_sequence,
        proposing ? "negotiate_proposal" : "signing_context",saved_performance && !proposing ? "\"performance_format\":\"saved_history_v1\"," : "",
        offer_field,context_revision,o->slot,o->first_name,o->last_name,o->photo,o->dob,
        o->team_index,o->payroll,o->cap,o->team_flag,o->accumulator,o->calendar[5],2004u+o->calendar[5],
        o->calendar[0],o->calendar[1],o->calendar[3],o->calendar[4],o->calendar[6]);
    if (length <= 0 || (size_t)length >= sizeof(request) ||
        franchise_host_submit(franchise_client,request,(size_t)length) != FRANCHISE_HOST_OK) {
        hello_failed = 1;
        clear_display();
        fprintf(stderr,"[FRANCHISE] Signing context transport unavailable; no transaction submitted.\n");
        return;
    }
    context_pending = 1;
    proposal_pending=proposing;
    if(proposing) {proposal_requested=0;proposal_sent=1;}
    context_sent = 1;
    requested=observed;
    requested_epoch=screen_epoch;
}
unsigned long long nfl2k5_franchise_submission_epoch(void) {
    unsigned long long epoch;
    AcquireSRWLockShared(&submission_lock);
    epoch=submission_enabled && submission_active ? submission_epoch : 0;
    ReleaseSRWLockShared(&submission_lock);
    return epoch;
}
int nfl2k5_franchise_submit_held(const FranchiseSigningObservation *o, unsigned long long epoch)
{
    int held;
    AcquireSRWLockExclusive(&submission_lock);
    held=submission_enabled;
    if(held && submission_active && epoch && epoch==submission_epoch && valid_observation(o)) {
        submitted_observation=*o;
        submission_pending=1;
    }
    ReleaseSRWLockExclusive(&submission_lock);
    /* Never a commit permit, even for malformed, obsolete or shutdown input. */
    return held;
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
    const wchar_t *performance = _wgetenv(L"NFL2K5_FRANCHISE_SAVED_PERFORMANCE");
    if (performance && *performance && wcscmp(performance,L"0") && wcscmp(performance,L"1")) return 0;
    int inspect_performance = performance && !wcscmp(performance,L"1");
    if (inspect_performance && !inspect_context) return 0;
    const wchar_t *offer_mode = _wgetenv(L"NFL2K5_FRANCHISE_GUEST_OFFER");
    if (offer_mode && *offer_mode && wcscmp(offer_mode,L"0") && wcscmp(offer_mode,L"1")) return 0;
    int offer_enabled = offer_mode && !wcscmp(offer_mode,L"1");
    if (offer_enabled && !inspect_context) return 0;
    const wchar_t *negotiate=_wgetenv(L"NFL2K5_FRANCHISE_NEGOTIATION");
    if(negotiate && *negotiate && wcscmp(negotiate,L"0") && wcscmp(negotiate,L"1")) return 0;
    const int hold_enabled=negotiate && !wcscmp(negotiate,L"1");
    if(hold_enabled && (!inspect_context || !inspect_performance || !offer_enabled)) return 0;
    const wchar_t *journal=_wgetenv(L"NFL2K5_FRANCHISE_GUEST_SIGNING");
    if(journal && wcscmp(journal,L"0") && wcscmp(journal,L"1")) return 0;
    const int prepare_enabled=journal && !wcscmp(journal,L"1");
    if(prepare_enabled && !hold_enabled) return 0;
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
    saved_performance = inspect_performance;
    inspect_guest_offer = offer_enabled;
    AcquireSRWLockExclusive(&submission_lock);
    submission_enabled=hold_enabled;submission_active=submission_pending=0;++submission_epoch;
    ReleaseSRWLockExclusive(&submission_lock);
    proposal_requested=proposal_sent=proposal_pending=0;
    journal_enabled=prepare_enabled;journal_pending=journal_locked=0;
    InterlockedExchange(&completion_failed,0);
    journal_next_check=0;journal_last_reply[0]=0;
    context_revision = revision;
    context_sequence = context_logged = 0;
    request_session=GetTickCount64();
    signing_active = context_sent = 0;
    observation_valid = observation_fresh = 0;
    screen_epoch=requested_epoch=changed_tick=0;
    InterlockedExchange(&franchise_foreign_sign_logged, 0);
    InterlockedExchange(&franchise_owner_thread, (LONG)GetCurrentThreadId());
    fprintf(stderr, "[FRANCHISE] Transport launched on owner thread=%lu; held negotiation mode=%d; guest commits unavailable.\n",
        (unsigned long)GetCurrentThreadId(),hold_enabled);
    return 1;
}
