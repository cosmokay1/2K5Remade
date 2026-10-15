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
static uint32_t g_esi,g_edi,context;
#define MEM32(address) context
static unsigned count,events,object,descriptor,pushed,stage,held_context,consumed;
static int hold_reply=1;
static struct {uint32_t va;uint32_t (*callback)(void);} hooks[16];
void recomp_interp_add_hook(uint32_t va,uint32_t from,uint32_t (*callback)(void)){
 hooks[count].va=va;hooks[count++].callback=callback;
}
void nfl2k5_diag_fsm(uint32_t obj,uint32_t desc,int push){
 ++events;object=obj;descriptor=desc;pushed=push;
}
int nfl2k5_franchise_hold_signing_at(uint32_t s,uint32_t c){stage=s;held_context=c;return hold_reply;}
int nfl2k5_franchise_signing_was_held(uint32_t c){++consumed;return 0;}
''' + block + r'''
int main(void){
 nfl2k5_franchise_interp_hooks();
 if(count!=2 || hooks[0].va!=0x6E3E6 || hooks[1].va!=0x6E439) return 1;
 g_esi=0x12345678;g_edi=0x557B2C;
 if(hooks[0].callback() || events!=1 || object!=g_esi || descriptor!=g_edi || pushed!=1) return 2;
 if(hooks[1].callback() || events!=2 || object!=g_esi || descriptor || pushed) return 3;
 if(g_esi!=0x12345678 || g_edi!=0x557B2C) return 4;
#ifdef _WIN32
 if(_putenv_s("NFL2K5_FRANCHISE_NEGOTIATION","1")) return 5;
#else
 if(setenv("NFL2K5_FRANCHISE_NEGOTIATION","1",1)) return 5;
#endif
 count=0;nfl2k5_franchise_interp_hooks();
 if(count!=7 || hooks[2].va!=0x324072 || hooks[3].va!=0x323D80 ||
    hooks[4].va!=0x3478B6 || hooks[5].va!=0x323F0A || hooks[6].va!=0x323F17) return 6;
 if(hooks[2].callback()!=0x324173 || stage!=2 || held_context || consumed!=1) return 7;
 hold_reply=0;
 if(hooks[2].callback() || consumed!=1) return 8;
 return 0;
}
''')
            subprocess.run([compiler, '-std=c11', '-D_POSIX_C_SOURCE=200809L',
                            '-DNFL2K5_FRANCHISE_CLIENT', str(source), '-o', str(executable)],
                           check=True, capture_output=True)
            subprocess.run([str(executable)], check=True, capture_output=True, timeout=10,
                           env={**os.environ, 'NFL2K5_FRANCHISE_NEGOTIATION': '0'})
