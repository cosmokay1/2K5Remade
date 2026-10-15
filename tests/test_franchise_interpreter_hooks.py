"""Compile the actual owned hook block; no game code or assets are included."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FranchiseInterpreterHooksTests(unittest.TestCase):
    def test_observation_hooks_run_with_negotiation_off(self):
        compiler = shutil.which('cc')
        if not compiler:
            self.skipTest('C compiler unavailable')
        manual = (ROOT/'src/recomp_manual.c').read_text()
        block = manual[manual.index('extern void nfl2k5_diag_fsm(uint32_t object'):]
        # This owned hook block is the final section of the translation unit.
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'hooks.c'
            executable = Path(directory)/'hooks-check'
            source.write_text(r'''
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
static uint32_t g_esi,g_edi,g_ebp,g_eax,g_ebx,g_esp,context;
#define MEM32(address) context
static unsigned count,events,object,descriptor,pushed,stage,held_context,consumed,completed;
static uint32_t load_stage,load_buffer,load_offset,load_table,load_stack;
static int hold_reply=1;
static int judgment_reply=1;
static struct {uint32_t va;uint32_t (*callback)(void);} hooks[16];
void recomp_interp_add_hook(uint32_t va,uint32_t from,uint32_t (*callback)(void)){
 hooks[count].va=va;hooks[count++].callback=callback;
}
void nfl2k5_diag_fsm(uint32_t obj,uint32_t desc,int push){
 ++events;object=obj;descriptor=desc;pushed=push;
}
int nfl2k5_franchise_hold_signing_at(uint32_t s,uint32_t c){stage=s;held_context=c;return hold_reply;}
int nfl2k5_franchise_judge_signing(uint32_t c){held_context=c;return judgment_reply;}
int nfl2k5_franchise_signing_was_held(uint32_t c){++consumed;return 0;}
void nfl2k5_franchise_signing_completed(uint32_t c){completed=c;}
void nfl2k5_franchise_load_boundary(uint32_t s,uint32_t b,uint32_t o,uint32_t t,uint32_t sp){load_stage=s;load_buffer=b;load_offset=o;load_table=t;load_stack=sp;}
''' + block + r'''
int main(void){
 nfl2k5_franchise_interp_hooks();
 if(count!=6 || hooks[0].va!=0x6E3E6 || hooks[1].va!=0x6E439) return 1;
 g_esi=0x12345678;g_edi=0x557B2C;
 if(hooks[0].callback() || events!=1 || object!=g_esi || descriptor!=g_edi || pushed!=1) return 2;
 if(hooks[1].callback() || events!=2 || object!=g_esi || descriptor || pushed) return 3;
 if(g_esi!=0x12345678 || g_edi!=0x557B2C) return 4;
 g_ebx=13;g_ebp=24;g_esp=0x2000;
 for(unsigned i=2;i<6;++i){
  static const uint32_t addresses[]={0x16E6CA,0x16E6DC,0x16E70B,0x16E81A};
  if(hooks[i].va!=addresses[i-2] || hooks[i].callback() || load_stage!=i-1 || load_buffer!=g_esi || load_offset!=g_ebx || load_table!=g_ebp || load_stack!=g_esp)return 13;
 }
#ifdef _WIN32
 if(_putenv_s("NFL2K5_FRANCHISE_NEGOTIATION","1")) return 5;
#else
 if(setenv("NFL2K5_FRANCHISE_NEGOTIATION","1",1)) return 5;
#endif
 count=0;nfl2k5_franchise_interp_hooks();
 if(count!=12 || hooks[6].va!=0x324072 || hooks[7].va!=0x323D80 ||
    hooks[8].va!=0x3478B6 || hooks[9].va!=0x323F0A || hooks[10].va!=0x323F17 || hooks[11].va!=0x32404E) return 6;
 if(hooks[6].callback()!=0x324173 || stage!=2 || held_context || consumed!=1) return 7;
 hold_reply=0;
 if(hooks[6].callback() || consumed!=1) return 8;
 g_ebp=0x10000;g_eax=0x87654321;g_edi=0x11223344;
 if(hooks[9].callback()!=0x323E99 || held_context!=g_esi || g_eax!=0x87654321 || g_edi!=0x11223344) return 9;
 judgment_reply=0;
 if(hooks[9].callback() || g_eax!=0x87654321 || g_edi!=0x11223344) return 10;
 judgment_reply=2;
 if(hooks[9].callback()!=0x323F13 || g_eax!=1 || g_edi!=g_ebp || g_esi!=0x12345678) return 11;
 if(hooks[11].callback() || completed!=g_esi || g_eax!=1 || g_edi!=g_ebp) return 12;
 return 0;
}
''')
            subprocess.run([compiler, '-std=c11', '-D_POSIX_C_SOURCE=200809L',
                            '-DNFL2K5_FRANCHISE_CLIENT', str(source), '-o', str(executable)],
                           check=True, capture_output=True)
            subprocess.run([str(executable)], check=True, capture_output=True, timeout=10,
                           env={**os.environ, 'NFL2K5_FRANCHISE_NEGOTIATION': '0'})
