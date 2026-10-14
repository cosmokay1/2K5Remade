#include "nfl2k5_franchise_host.h"
#include "host_client.h"
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>

static FranchiseHostClient *franchise_client;
void nfl2k5_franchise_stop(void)
{
    franchise_host_destroy(franchise_client);
    franchise_client = NULL;
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
    if (franchise_host_create(python, database, FRANCHISE_HOST_VERTEX_RUNTIME,
                              &franchise_client) != FRANCHISE_HOST_OK) {
        fprintf(stderr, "[FRANCHISE] Sidecar launch failed.\n");
        return 0;
    }
    /* A later verified franchise callback must perform hello and consume its
     * result before AI negotiation. Startup alone grants no AI access. */
    if (atexit(nfl2k5_franchise_stop)) {
        nfl2k5_franchise_stop();
        return 0;
    }
    fprintf(stderr, "[FRANCHISE] Transport launched; guest transaction hooks remain unavailable.\n");
    return 1;
}
