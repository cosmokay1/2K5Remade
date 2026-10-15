/* Plain C exercises the host ABI only; no retail game or guest state. */
#include "host_client.h"
#include "../../src/nfl2k5_franchise_host.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int nfl2k5_franchise_source_path_matches(uint64_t epoch){return epoch!=0;}
int nfl2k5_franchise_read_loaded_source(char out[65],uint64_t *epoch){out[0]=0;*epoch=0;return 0;}
int nfl2k5_franchise_read_image(char out[65]){out[0]=0;return 0;}
int nfl2k5_franchise_read_finance(struct FranchiseFinanceSnapshot *out){(void)out;return 0;}
int nfl2k5_franchise_read_identity(const struct FranchiseFinanceSnapshot *finance,struct FranchiseIdentitySnapshot *out){(void)finance;(void)out;return 0;}

static int require_status(FranchiseHostStatus actual, FranchiseHostStatus expected) {
    if (actual == expected) return 1;
    fprintf(stderr,"C host status mismatch: %d expected %d\n",(int)actual,(int)expected);
    return 0;
}

static int receive(FranchiseHostClient* client) {
    int ready = 0;
    size_t required = 0;
    DWORD started = GetTickCount();
    while (!ready) {
        if (!require_status(franchise_host_ready(client,&ready),FRANCHISE_HOST_OK)) return 0;
        if (GetTickCount()-started > 7000) { fprintf(stderr,"C host response timeout\n"); return 0; }
        if (!ready) Sleep(1);
    }
    if (!require_status(franchise_host_take(client,NULL,0,&required),FRANCHISE_HOST_BUFFER_TOO_SMALL) || !required) return 0;
    if (!require_status(franchise_host_prepare_accepted(client,NULL,0,NULL,0),FRANCHISE_HOST_BUSY)) return 0;
    if (!require_status(franchise_host_check_saved(client),FRANCHISE_HOST_BUSY)) return 0;
    {
        char sentinel = 'x';
        size_t repeated = 0;
        char* response;
        if (!require_status(franchise_host_take(client,&sentinel,1,&repeated),FRANCHISE_HOST_BUFFER_TOO_SMALL) ||
            sentinel != 'x' || repeated != required) return 0;
        if (!require_status(franchise_host_submit(client,"{}",2),FRANCHISE_HOST_BUSY)) return 0;
        if (!require_status(franchise_host_ready(client,&ready),FRANCHISE_HOST_OK) || !ready) return 0;
        response = (char*)malloc(required);
        if (!response) return 0;
        if (!require_status(franchise_host_take(client,response,required,&repeated),FRANCHISE_HOST_OK) ||
            repeated != required || response[required-1] != '\0') { free(response); return 0; }
        puts(response); free(response);
    }
    return require_status(franchise_host_prepare_accepted(client,NULL,0,NULL,0),FRANCHISE_HOST_NOT_READY) &&
        require_status(franchise_host_check_saved(client),FRANCHISE_HOST_NOT_READY) &&
        require_status(franchise_host_take(client,NULL,0,&required),FRANCHISE_HOST_NOT_READY) &&
        require_status(franchise_host_ready(client,&ready),FRANCHISE_HOST_OK) && !ready;
}

int wmain(int argc, wchar_t** argv) {
    if(!require_status(franchise_host_prepare_accepted(NULL,NULL,0,NULL,0),FRANCHISE_HOST_INVALID_ARGUMENT)) return 1;
    FranchiseHostClient* client = NULL;
    char oversized[4096];
    int ready = 1, ok = 0;
    const char* requests[] = {
        "{\"protocol\":1,\"request_id\":\"c-hello\",\"operation\":\"hello\"}",
        "{\"protocol\":1,\"request_id\":\"c-preview\",\"operation\":\"preview\",\"team_id\":\"a\",\"offer\":{\"player_id\":\"v\",\"salaries\":[10],\"signing_bonus\":0},\"expected_revision\":0,\"timeout_ms\":1000}",
        "{\"protocol\":1,\"request_id\":\"c-proposal\",\"operation\":\"negotiate_proposal\",\"team_id\":\"a\",\"offer\":{\"player_id\":\"v\",\"salaries\":[10],\"signing_bonus\":0},\"expected_revision\":0,\"timeout_ms\":1000,\"personality\":{},\"performance\":{},\"relationships\":{}}",
        "{\"protocol\":1,\"request_id\":\"c-manual\",\"operation\":\"manual_sign\",\"team_id\":\"a\",\"offer\":{\"player_id\":\"v\",\"salaries\":[10],\"signing_bonus\":0},\"expected_revision\":0,\"timeout_ms\":1000,\"decision_mode\":\"manual\"}",
        "{\"protocol\":1,\"request_id\":\"c-context\",\"operation\":\"player_context\",\"team_id\":\"a\",\"player_id\":\"v\",\"timeout_ms\":1000}"
    };
    size_t i;
    if (argc == 5 || argc == 6) {
        wchar_t missing_credentials[4096];
        int token_budget = argc == 6;
        const char* budget_requests[] = {
            "{\"protocol\":1,\"request_id\":\"budget-hello\",\"operation\":\"hello\"}",
            "{\"protocol\":1,\"request_id\":\"budget-context\",\"operation\":\"player_context\",\"team_id\":\"a\",\"player_id\":\"v\",\"timeout_ms\":5000}"
        };
        if (token_budget && wcscmp(argv[5],L"token-budget")) return 2;
        /* Explicit missing ADC prevents credentials or model requests in CI. */
        if (wcslen(argv[3]) > 4000 || swprintf(missing_credentials,4096,L"%ls.missing-adc.json",argv[3]) < 0 ||
            _wputenv_s(L"GOOGLE_APPLICATION_CREDENTIALS",missing_credentials)) return 1;
        if (!require_status(franchise_host_create_with_budget(argv[1],argv[2],FRANCHISE_HOST_OFFLINE_FIXTURE,
                argv[3],argv[4],2,&client),FRANCHISE_HOST_INVALID_ARGUMENT) || client) return 1;
        if (!require_status(franchise_host_create_with_budget(argv[1],argv[2],FRANCHISE_HOST_VERTEX_RUNTIME,
                argv[3],argv[4],0,&client),FRANCHISE_HOST_INVALID_ARGUMENT) || client) return 1;
        if (token_budget) {
            if (!require_status(franchise_host_create_with_token_budget(argv[1],argv[2],FRANCHISE_HOST_VERTEX_RUNTIME,
                    argv[3],argv[4],2,0,&client),FRANCHISE_HOST_INVALID_ARGUMENT) || client) return 1;
            if (!require_status(franchise_host_create_with_token_budget(argv[1],argv[2],FRANCHISE_HOST_VERTEX_RUNTIME,
                    argv[3],argv[4],2,9223372036854775808ULL,&client),FRANCHISE_HOST_INVALID_ARGUMENT) || client) return 1;
            if (!require_status(franchise_host_create_with_token_budget(argv[1],argv[2],FRANCHISE_HOST_OFFLINE_FIXTURE,
                    argv[3],argv[4],2,30000,&client),FRANCHISE_HOST_INVALID_ARGUMENT) || client) return 1;
            if (!require_status(franchise_host_create_with_token_budget(argv[1],argv[2],FRANCHISE_HOST_VERTEX_RUNTIME,
                    argv[3],argv[4],2,30000,&client),FRANCHISE_HOST_OK)) return 1;
        } else if (!require_status(franchise_host_create_with_budget(argv[1],argv[2],FRANCHISE_HOST_VERTEX_RUNTIME,
                    argv[3],argv[4],2,&client),FRANCHISE_HOST_OK)) return 1;
        for (i=0;i<2;++i) {
            if (!require_status(franchise_host_submit(client,budget_requests[i],strlen(budget_requests[i])),FRANCHISE_HOST_OK) ||
                !receive(client)) goto done;
        }
        ok=1;
        goto done;
    }
    if (argc != 3) { fprintf(stderr,"Usage: c_host_smoke PYTHON DATABASE [BUDGET_DATABASE SCOPE [token-budget]]\n"); return 2; }
    /* Exercise the actual host startup policy without launching Vertex. */
    if (_wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER", L"") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_PYTHON", L"") ||
        _wputenv_s(L"NFL2K5_FRANCHISE_DATABASE", L"") ||
        !nfl2k5_franchise_start()) return 1;
    nfl2k5_franchise_stop();
    nfl2k5_franchise_stop();
    if (_wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER", L"offline-fixture") ||
        nfl2k5_franchise_start()) return 1;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER", L"vertex") ||
        nfl2k5_franchise_start()) return 1;
    if (_wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER", L"")) return 1;
    if (!require_status(franchise_host_create(argv[1],argv[2],(FranchiseHostMode)99,&client),FRANCHISE_HOST_INVALID_ARGUMENT) || client) return 1;
    if (!require_status(franchise_host_create(argv[1],argv[2],FRANCHISE_HOST_OFFLINE_FIXTURE,NULL),FRANCHISE_HOST_INVALID_ARGUMENT)) return 1;
    franchise_host_destroy(NULL);
    if (!require_status(franchise_host_create(argv[1],argv[2],FRANCHISE_HOST_OFFLINE_FIXTURE,&client),FRANCHISE_HOST_OK)) return 1;
    if (!require_status(franchise_host_ready(client,&ready),FRANCHISE_HOST_OK) || ready) goto done;
    {
        size_t required = 99;
        char output = 'x';
        if (!require_status(franchise_host_take(client,&output,1,&required),FRANCHISE_HOST_NOT_READY) ||
            required != 0 || output != 'x' ||
            !require_status(franchise_host_ready(NULL,&ready),FRANCHISE_HOST_INVALID_ARGUMENT) || ready != 0 ||
            !require_status(franchise_host_ready(client,NULL),FRANCHISE_HOST_INVALID_ARGUMENT) ||
            !require_status(franchise_host_take(client,NULL,1,&required),FRANCHISE_HOST_INVALID_ARGUMENT) ||
            !require_status(franchise_host_take(client,&output,1,NULL),FRANCHISE_HOST_INVALID_ARGUMENT) ||
            !require_status(franchise_host_submit(client,NULL,1),FRANCHISE_HOST_INVALID_ARGUMENT) ||
            !require_status(franchise_host_submit(client,"",0),FRANCHISE_HOST_INVALID_ARGUMENT)) goto done;
    }
    {
        const char* ai = "{\"protocol\":1,\"request_id\":\"c-ai-before-hello\",\"operation\":\"negotiate\"}";
        if (!require_status(franchise_host_submit(client,ai,strlen(ai)),FRANCHISE_HOST_SERVICE_FAILURE)) goto done;
        const char* proposal = "{\"protocol\":1,\"request_id\":\"c-proposal-before-hello\",\"operation\":\"negotiate_proposal\"}";
        if (!require_status(franchise_host_submit(client,proposal,strlen(proposal)),FRANCHISE_HOST_SERVICE_FAILURE)) goto done;
    }
    memset(oversized,'x',sizeof oversized);
    if (!require_status(franchise_host_submit(client,oversized,sizeof oversized),FRANCHISE_HOST_INVALID_ARGUMENT) ||
        !require_status(franchise_host_submit(client,"{}",2),FRANCHISE_HOST_INVALID_ARGUMENT) ||
        !require_status(franchise_host_submit(client,"a\0b",3),FRANCHISE_HOST_INVALID_ARGUMENT) ||
        !require_status(franchise_host_submit(client,"{}\n",3),FRANCHISE_HOST_INVALID_ARGUMENT)) goto done;
    for (i=0;i<sizeof requests/sizeof requests[0];++i) {
        if (!require_status(franchise_host_submit(client,requests[i],strlen(requests[i])),FRANCHISE_HOST_OK) ||
            !require_status(franchise_host_submit(client,requests[i],strlen(requests[i])),FRANCHISE_HOST_BUSY) ||
            !receive(client)) goto done;
    }
    ok = 1;
done:
    franchise_host_destroy(client);
    return ok ? 0 : 1;
}
