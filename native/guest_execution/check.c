/* Actual runtime lock, authored threads and read scopes; no guest/game assets. */
#include "../game_addon/read_scope.h"
#include "platform/xbox_winnt.h"
#if !defined(_WIN32)
#include "platform/win32_compat.h"
#endif
#define XBOX_GGL_IMPL
#include "xbox_ggl.h"
extern void xbox_ggl_Sleep(DWORD ms); /* wrappers are hidden by XBOX_GGL_IMPL above */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(value) do {if(!(value)){fprintf(stderr,"Failed at %d: %s\n",__LINE__,#value);abort();}}while(0)
static HANDLE entered,claimed;
static uint64_t other_serial;
static DWORD WINAPI worker(void *unused) {
    (void)unused;CHECK(!xbox_ggl_current_serial());CHECK(SetEvent(entered));
    xbox_ggl_enter();other_serial=xbox_ggl_current_serial();CHECK(other_serial);
    CHECK(SetEvent(claimed));xbox_ggl_leave();CHECK(!xbox_ggl_current_serial());return 0;
}
int main(int argc,char **argv) {
    CHECK(argc==2);int enabled=!strcmp(argv[1],"enabled");
    CHECK(!xbox_ggl_current_serial());CHECK(xbox_ggl_enabled()==enabled);
    NFL2K5AddonReadScope scope={0};CHECK(!addon_read_allowed(&scope,1));
    addon_read_begin(&scope,0);addon_read_begin(&scope,1);CHECK(!addon_read_allowed(&scope,1));
    addon_read_end(&scope);addon_read_end(&scope);addon_read_end(&scope);
    xbox_ggl_enter();uint64_t first=xbox_ggl_current_serial();CHECK((first!=0)==enabled);
    addon_read_begin(&scope,first);CHECK(addon_read_allowed(&scope,first)==enabled);
    if(!enabled) {CHECK(!xbox_ggl_release_all());addon_read_end(&scope);return 0;}
    xbox_ggl_enter();CHECK(xbox_ggl_current_serial()==first);
    addon_read_begin(&scope,first);addon_read_end(&scope);xbox_ggl_leave();
    CHECK(addon_read_allowed(&scope,xbox_ggl_current_serial()));
    entered=CreateEventA(NULL,TRUE,FALSE,NULL);claimed=CreateEventA(NULL,TRUE,FALSE,NULL);CHECK(entered && claimed);
    HANDLE thread=CreateThread(NULL,0,worker,NULL,0,NULL);CHECK(thread);
    CHECK(WaitForSingleObject(entered,5000)==WAIT_OBJECT_0);
    CHECK(WaitForSingleObject(claimed,0)==WAIT_TIMEOUT); /* another thread cannot inherit ownership */
    int depth=xbox_ggl_release_all();CHECK(depth==1 && !xbox_ggl_current_serial());
    CHECK(!addon_read_allowed(&scope,xbox_ggl_current_serial()));
    CHECK(WaitForSingleObject(thread,5000)==WAIT_OBJECT_0);CHECK(other_serial>first);
    xbox_ggl_reacquire(depth);uint64_t resumed=xbox_ggl_current_serial();CHECK(resumed>other_serial);
    CHECK(!addon_read_allowed(&scope,resumed)); /* reacquisition cannot revive an old read scope */
    addon_read_end(&scope);addon_read_begin(&scope,resumed);CHECK(addon_read_allowed(&scope,resumed));
    xbox_ggl_Sleep(0);CHECK(xbox_ggl_current_serial()>resumed);
    CHECK(!addon_read_allowed(&scope,xbox_ggl_current_serial()));
    addon_read_end(&scope);xbox_ggl_leave();CHECK(!xbox_ggl_current_serial());
    CloseHandle(thread);CloseHandle(entered);CloseHandle(claimed);
    puts("Actual guest-lock ownership, recursion, cross-thread exclusion, yield invalidation and scoped reads passed");return 0;
}
