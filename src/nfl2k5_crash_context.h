#ifndef NFL2K5_CRASH_CONTEXT_H
#define NFL2K5_CRASH_CONTEXT_H
/* Optional Windows crash evidence only. Never dereference an untrusted guest
 * pointer directly, scan arbitrary host memory, or change execution state. */
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
static void nfl2k5_crash_words(FILE *out,const char *label,uintptr_t base,size_t size,uint64_t address) {
    uint32_t words[24];SIZE_T read=0;
    if(address>UINT32_MAX || address>=size) return;
    const uintptr_t start=address>=16?((uintptr_t)address-16)&~(uintptr_t)3:0;
    if(size-start<sizeof(words) || base>UINTPTR_MAX-start) return;
    if(!ReadProcessMemory(GetCurrentProcess(),(const void*)(base+start),words,sizeof(words),&read) || read!=sizeof(words)) {
        fprintf(out,"[CRASH-CONTEXT] %s guest=%08llX unreadable\n",label,(unsigned long long)address);return;
    }
    fprintf(out,"[CRASH-CONTEXT] %s guest=%08llX window=%08llX\n",label,(unsigned long long)address,(unsigned long long)start);
    for(unsigned i=0;i<24;i+=4)
        fprintf(out,"[CRASH-CONTEXT] %08llX: %08X %08X %08X %08X\n",
            (unsigned long long)(start+i*4),words[i],words[i+1],words[i+2],words[i+3]);
}
static void nfl2k5_crash_context(FILE *out,const CONTEXT *context,uint32_t guest_stack,uintptr_t base,size_t size) {
    if(!out || !context || !size || size>128u*1024u*1024u) return;
    const struct {const char *name;uint64_t value;} registers[]={
        {"rax",context->Rax},{"rbx",context->Rbx},{"rcx",context->Rcx},{"rdx",context->Rdx},
        {"rsi",context->Rsi},{"rdi",context->Rdi},{"rbp",context->Rbp},
        {"r8",context->R8},{"r9",context->R9},{"r10",context->R10},{"r11",context->R11},
        {"r12",context->R12},{"r13",context->R13},{"r14",context->R14},{"r15",context->R15}};
    /* Only low guest RAM candidates are sampled, with a fixed96-byte window.
     * Register values can be ordinary integers; a window is evidence, not a
     * claim that the register holds an object pointer. */
    fprintf(out,"[CRASH-CONTEXT] opt-in bounded guest windows; native registers follow\n");
    for(unsigned i=0;i<sizeof(registers)/sizeof(registers[0]);++i) {
        fprintf(out,"[CRASH-CONTEXT] native %s=%016llX\n",registers[i].name,(unsigned long long)registers[i].value);
        if(registers[i].value>=0x10000u) nfl2k5_crash_words(out,registers[i].name,base,size,registers[i].value);
    }
    nfl2k5_crash_words(out,"guest-stack",base,size,guest_stack);
    fflush(out);
}
#endif
