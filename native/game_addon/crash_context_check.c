/* Authored local memory only; no game, assets, guest execution or AI. */
#include "../../src/nfl2k5_crash_context.h"
#include <assert.h>
#include <string.h>
int main(void) {
    uint32_t *memory=VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
    assert(memory);
    for(unsigned i=0;i<1024;++i) memory[i]=0x12340000u+i;
    memory[0x248/4]=0;
    uint32_t before[1024];memcpy(before,memory,sizeof(before));
    CONTEXT context={0};context.R11=0x10100;context.R8=0x10248;context.R9=UINT64_MAX;
    FILE *out=tmpfile();assert(out);
    nfl2k5_crash_context(NULL,&context,0,(uintptr_t)memory-0x10000,0x11000);
    nfl2k5_crash_context(out,NULL,0,(uintptr_t)memory-0x10000,0x11000);
    nfl2k5_crash_context(out,&context,0x10300,(uintptr_t)memory-0x10000,0x11000);
    rewind(out);char text[16000]={0};assert(fread(text,1,sizeof(text)-1,out));fclose(out);
    assert(strstr(text,"native r11=0000000000010100"));
    assert(strstr(text,"r8 guest=00010248 window=00010238"));
    assert(strstr(text,"00010248: 00000000 12340093 12340094 12340095"));
    assert(strstr(text,"guest-stack guest=00010300"));
    assert(!strstr(text,"r9 guest="));
    assert(!memcmp(memory,before,sizeof(before)));
    DWORD old;assert(VirtualProtect(memory,4096,PAGE_NOACCESS,&old));
    out=tmpfile();assert(out);
    nfl2k5_crash_context(out,&context,0x10300,(uintptr_t)memory-0x10000,0x11000);
    rewind(out);memset(text,0,sizeof(text));assert(fread(text,1,sizeof(text)-1,out));fclose(out);
    assert(strstr(text,"r11 guest=00010100 unreadable"));
    assert(VirtualProtect(memory,4096,old,&old));assert(!memcmp(memory,before,sizeof(before)));
    assert(VirtualFree(memory,0,MEM_RELEASE));
    puts("Bounded register/guest windows, unreadable pages and unchanged memory passed");
    return 0;
}
