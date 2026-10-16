"""Compile the actual fixed guest dispatcher with authored registers/memory."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
class NativeDispatchTests(unittest.TestCase):
    def test_fixed_calls_preserve_registers_and_reject_bad_contexts(self):
        cc=shutil.which('cc')
        if not cc:self.skipTest('Native fixture requires C compiler')
        text=(ROOT/'src/recomp_manual.c').read_text()
        start=text.index('#ifdef NFL2K5_FRANCHISE_NATIVE_APPLICATION')
        body=text[start:text.index('\n#endif',start)+len('\n#endif')]
        prefix=r'''
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#define NFL2K5_FRANCHISE_NATIVE_APPLICATION
#define RECOMP_TLS _Thread_local
static uint32_t g_eax=1,g_ebx=2,g_ecx=3,g_edx=4,g_esi=5,g_edi=6,g_ebp=7,g_esp=0x18000,g_seh_ebp=9;
static int g_fp_top=1,g_fp_cmp=2,g_df=1;
static uint16_t g_fp_cc=3,g_fp_control_word=4;
static double g_fp_stack[8]={1,2,3,4,5,6,7,8};
typedef struct {uint64_t a,b;} RecompXmm;
static RecompXmm g_xmm0={1,2},g_xmm1={3,4},g_xmm2={5,6},g_xmm3={7,8},g_xmm4={9,10},g_xmm5={11,12},g_xmm6={13,14},g_xmm7={15,16};
static unsigned char memory[0x20000];static uint32_t selected=0x10000,team=0x12000;
static unsigned signs,recalculations;static uint64_t serial=1;
uint64_t xbox_ggl_current_serial(void){return serial;}
#define MEM16(a) (*(uint16_t*)(memory+(a)))
#define MEM32(a) (*(uint32_t*)(memory+(a)))
#define PUSH32(sp,v) ((sp)-=4,MEM32(sp)=(v))
#define RECOMP_ABI_CALL(a,f) f()
static int nfl2k5_qb_read(uint32_t a,void*out,size_t n){
 if(a==0xCB8C34 && n==4){memcpy(out,&selected,4);return 1;}
 if(a==0xE5786C && n==4){memcpy(out,&team,4);return 1;}
 if(a>sizeof(memory) || n>sizeof(memory)-a)return 0;memcpy(out,memory+a,n);return 1;
}
void sub_003478A0(void){
 if(g_ecx!=0x11000 || MEM16(0x1000C)!=600 || MEM32(0x10008)!=196608) signs=999;else ++signs;
 g_eax=g_ebx=g_ecx=g_edx=g_esi=g_edi=g_ebp=g_seh_ebp=99;
 g_df=0;g_fp_top=g_fp_cmp=99;g_fp_cc=g_fp_control_word=99;g_fp_stack[0]=99;g_xmm0.a=99;g_xmm7.b=99;g_esp+=4;
}
void sub_000C3F00(void){if(g_ecx!=0x12000)recalculations=999;else ++recalculations;g_eax=99;g_esp+=4;}
'''
        suffix=r'''
int main(void){
 if(!nfl2k5_franchise_dispatch_native(0x10000,0x11000,600,196608) || signs!=1)return 1;
 if(g_eax!=1 || g_ebx!=2 || g_ecx!=3 || g_edx!=4 || g_esi!=5 || g_edi!=6 || g_ebp!=7 || g_esp!=0x18000 || g_seh_ebp!=9 ||
    g_df!=1 || g_fp_top!=1 || g_fp_cmp!=2 || g_fp_cc!=3 || g_fp_control_word!=4 || g_fp_stack[0]!=1 || g_xmm0.a!=1 || g_xmm7.b!=16)return 2;
 if(!nfl2k5_franchise_dispatch_native(0,0,0,0) || recalculations!=1 || g_ecx!=3 || g_eax!=1 || g_esp!=0x18000)return 3;
 if(nfl2k5_franchise_dispatch_native(0x10001,0x11000,600,196608) || nfl2k5_franchise_dispatch_native(0x10000,0,600,196608) ||
    nfl2k5_franchise_dispatch_native(0x10000,0x11000,65536,196608) || nfl2k5_franchise_dispatch_native(0,0,0,32))return 4;
 serial=0;if(nfl2k5_franchise_dispatch_native(0x10000,0x11000,600,196608) || signs!=1 || recalculations!=1)return 5;
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'dispatch.c';source.write_text(prefix+body+suffix)
            exe=Path(directory)/'dispatch'
            subprocess.run([cc,'-std=c11',str(source),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True,timeout=10)
