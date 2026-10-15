/* Synthetic x86 only: no game executable or assets. */
#include <stdio.h>
#include <string.h>
#include "recomp_types.h"
#include "x86_interp.h"
ptrdiff_t g_xbox_mem_offset;
RECOMP_TLS uint32_t g_eax,g_ecx,g_edx,g_esp,g_ebx,g_esi,g_edi,g_ebp,g_seh_ebp,g_fs_base;
RECOMP_TLS double g_fp_stack[8];
RECOMP_TLS int g_fp_top,g_fp_cmp,g_df;
RECOMP_TLS uint16_t g_fp_control_word,g_fp_cc;
RECOMP_TLS RecompXmm g_xmm0,g_xmm1,g_xmm2,g_xmm3,g_xmm4,g_xmm5,g_xmm6,g_xmm7;
static unsigned generated_jumps,native_calls,manual_jumps,kernel_jumps;
static unsigned char memory[0x4000];
ptrdiff_t xbox_GetMemoryOffset(void) {return g_xbox_mem_offset;}
static void shared_epilogue(void) {++generated_jumps;g_esp+=20;}
static void native_call(void) {++native_calls;g_esp+=4;g_eax=17;}
static void manual_jump(void) {++manual_jumps;g_esp+=4;g_eax=19;}
static void kernel_jump(void) {++kernel_jumps;g_esp+=4;g_eax=23;}
recomp_func_t recomp_lookup(uint32_t va) {
    if(va==0x1200) return shared_epilogue;
    return va==0x1300?native_call:NULL;
}
recomp_func_t recomp_lookup_manual(uint32_t va) {return va==0x1500?manual_jump:NULL;}
recomp_func_t recomp_lookup_kernel(uint32_t va) {return va==0xFE000100?kernel_jump:NULL;}
static void run(uint32_t va) {
    memset(memory+0x3000,0,0x1000);g_esp=0x3f00;MEM32(g_esp)=0xDEADBEEF;g_eax=0;
    recomp_interp_call(va);
}
int main(void) {
    g_xbox_mem_offset=(ptrdiff_t)memory;
    /* Outer call -> nested frame with 16 bytes of locals -> shared epilogue.
     * A generated entry at that epilogue must not treat local data as
     * the return address. The epilogue deallocates locals before RET. */
    const unsigned char outer[]={0xE8,0xFB,0,0,0,0xB8,42,0,0,0,0xC3};
    const unsigned char inner[]={0x83,0xEC,0x10,0xC7,0x04,0x24,0,0x20,0,0,0xE9,0xF1,0,0,0};
    const unsigned char poison[]={0xB8,99,0,0,0,0xC3};
    const unsigned char epilogue[]={0x83,0xC4,0x10,0xC3};
    const unsigned char call[]={0xE8,0xFB,0xFC,0xFF,0xFF,0xC3};
    const unsigned char manual[]={0xE9,0xFB,0xFD,0xFF,0xFF};
    const unsigned char kernel[]={0xE9,0xFB,0xE8,0xFF,0xFD};
    memcpy(memory+0x2000,poison,sizeof poison);
    memcpy(memory+0x1000,outer,sizeof outer);memcpy(memory+0x1100,inner,sizeof inner);
    memcpy(memory+0x1200,epilogue,sizeof epilogue);memcpy(memory+0x1600,call,sizeof call);
    memcpy(memory+0x1700,manual,sizeof manual);memcpy(memory+0x1800,kernel,sizeof kernel);
    run(0x1000);if(g_eax!=42 || g_esp!=0x3f04 || generated_jumps) return 1;
    run(0x1600);if(g_eax!=17 || g_esp!=0x3f04 || native_calls!=1) return 2;
    run(0x1700);if(g_eax!=19 || g_esp!=0x3f04 || manual_jumps!=1) return 3;
    run(0x1800);if(g_eax!=23 || g_esp!=0x3f04 || kernel_jumps!=1) return 4;
    puts("Shared epilogue, native call, manual and kernel jump checks passed");return 0;
}
