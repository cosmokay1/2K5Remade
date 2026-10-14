/* Plain C exercises the host ABI only; no retail game or guest state. */
#include "host_client.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
    return require_status(franchise_host_take(client,NULL,0,&required),FRANCHISE_HOST_NOT_READY) &&
        require_status(franchise_host_ready(client,&ready),FRANCHISE_HOST_OK) && !ready;
}

int wmain(int argc, wchar_t** argv) {
    FranchiseHostClient* client = NULL;
    char oversized[4096];
    int ready = 1, ok = 0;
    const char* requests[] = {
        "{\"protocol\":1,\"request_id\":\"c-hello\",\"operation\":\"hello\"}",
        "{\"protocol\":1,\"request_id\":\"c-preview\",\"operation\":\"preview\",\"team_id\":\"a\",\"offer\":{\"player_id\":\"v\",\"salaries\":[10],\"signing_bonus\":0},\"expected_revision\":0,\"timeout_ms\":1000}",
        "{\"protocol\":1,\"request_id\":\"c-manual\",\"operation\":\"manual_sign\",\"team_id\":\"a\",\"offer\":{\"player_id\":\"v\",\"salaries\":[10],\"signing_bonus\":0},\"expected_revision\":0,\"timeout_ms\":1000,\"decision_mode\":\"manual\"}",
        "{\"protocol\":1,\"request_id\":\"c-context\",\"operation\":\"player_context\",\"team_id\":\"a\",\"player_id\":\"v\",\"timeout_ms\":1000}"
    };
    size_t i;
    if (argc != 3) { fprintf(stderr,"Usage: c_host_smoke PYTHON DATABASE\n"); return 2; }
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
