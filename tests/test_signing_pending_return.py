"""Execute the patched caller with the actual shim and authored retail outcomes."""
from contextlib import redirect_stdout
import importlib.util
import os
from io import StringIO
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class SigningPendingReturnTests(unittest.TestCase):
    def test_held_offers_do_not_consume_attempts_or_close_screen(self):
        compiler = shutil.which('cc')
        if not compiler:
            self.skipTest('C compiler unavailable; native signing-stage fixture runs in Windows CI')
        spec = importlib.util.spec_from_file_location('pending_patch', ROOT/'tools/apply-gen-patches.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PATCHES = [row for row in module.PATCHES if row[0] == 'FRANCHISE_SIGN_PENDING_RETURN']
        self.assertEqual(len(module.PATCHES), 1)
        with tempfile.TemporaryDirectory() as directory:
            module.GEN = directory
            source = Path(directory)/'recomp_authored.c'
            source.write_text(r'''
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "src/nfl2k5_sidecar_adapter.h"
#include "native/franchise_bridge/franchise_addon.h"
static unsigned char memory[64];
#define MEM32(address) (*(uint32_t *)(memory+(address)-0xCB8C34u))
static unsigned attempts, closes, restored, retail_result, held;
int nfl2k5_addon_start(void){return 1;}
void nfl2k5_addon_stop(void){}
void nfl2k5_addon_poll(void){}
int nfl2k5_addon_snapshot(const char *n,void *o,size_t c){return 0;}
int nfl2k5_addon_event(const char *n,const void *d,size_t s){
    return !strcmp(n,FRANCHISE_SIGN_GATE_EVENT) ? held : 0;
}
/* Authored caller preserves the retail acceptance/rejection/common cleanup
 * branches. Only the production patch can bypass a pending rejection. */
void sub_003478A0(void)
{
loc_003478B6: ;
    if(retail_result){attempts=0;++closes;}
    else if(attempts<7) ++attempts;
    goto loc_003478F0;
loc_003478F0: ;
    MEM32(0xCB8C3C)=1;
    ++restored;
}
static int offer(unsigned wait,unsigned accepted){
    held=wait;retail_result=accepted;
    nfl2k5_diag_signing(0,0x1234,0,0,0);
    nfl2k5_franchise_hold_signing_at(1,0x1234);
    MEM32(0xCB8C3C)=0;
    sub_003478A0();
    return MEM32(0xCB8C3C)==1;
}
int main(void){
    MEM32(0xCB8C34)=0x1234;
    attempts=3;
    for(unsigned i=0;i<12;++i) if(!offer(1,0)) return 1;
    if(attempts!=3 || closes || restored!=12) return 2;
    if(!offer(0,0) || attempts!=4 || closes || restored!=13) return 3;
    for(unsigned i=0;i<12;++i) offer(0,0);
    if(attempts!=7) return 4;
    if(!offer(0,1) || attempts || closes!=1 || restored!=26) return 5;
    return 0;
}
''')
            with patch.object(module.sys, 'argv', ['apply-gen-patches.py']), redirect_stdout(StringIO()):
                self.assertEqual(module.main(), 0)
                before = source.read_bytes()
                self.assertEqual(module.main(), 0)
                self.assertEqual(before, source.read_bytes())
            executable = Path(directory)/'pending-check'
            subprocess.run([compiler, '-std=c11', '-DNFL2K5_FRANCHISE_CLIENT', '-I', str(ROOT),
                            str(source), str(ROOT/'native/franchise_bridge/game_addon_adapter.c'),
                            '-o', str(executable)], check=True, capture_output=True)
            subprocess.run([str(executable)], check=True, capture_output=True,
                           env={**os.environ, 'NFL2K5_FRANCHISE_NEGOTIATION': '0'}, timeout=10)


class CPUSigningHoldTests(unittest.TestCase):
    def test_cpu_defers_before_free_agent_removal_and_offer_rejection(self):
        compiler = shutil.which('cc')
        if not compiler:
            self.skipTest('C compiler unavailable')
        spec = importlib.util.spec_from_file_location('cpu_patch', ROOT/'tools/apply-gen-patches.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PATCHES = [row for row in module.PATCHES if row[0] == 'FRANCHISE_SIGN_CPU_HOLD']
        self.assertEqual(len(module.PATCHES), 1)
        with tempfile.TemporaryDirectory() as directory:
            module.GEN = directory
            source = Path(directory)/'recomp_authored.c'
            source.write_text(r'''#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "src/nfl2k5_sidecar_adapter.h"
#include "native/franchise_bridge/franchise_addon.h"
static unsigned held,removed,rejected,submitted,visited,wrong_stage,direct,cleanups;
int nfl2k5_addon_start(void){return 1;}
void nfl2k5_addon_stop(void){}
void nfl2k5_addon_poll(void){}
int nfl2k5_addon_snapshot(const char*n,void*o,size_t c){return 0;}
int nfl2k5_addon_event(const char*n,const void*d,size_t s){
 if(!strcmp(n,FRANCHISE_SIGN_GATE_EVENT)){
  const FranchiseSignGateEvent *gate=d;
  if(gate->stage!=FRANCHISE_SIGN_PRECOMMIT) ++wrong_stage;
  return held;
 }
 if(!strcmp(n,FRANCHISE_SIGN_SUBMIT_EVENT)) ++submitted;
 return 0;
}
void sub_00324060(void)
{
loc_00324072: ;
 for(uint32_t esi=1;esi<=100;++esi){
  if(esi&1){++removed;++rejected;} /* Shared-signing route. */
  else ++direct; /* Automatic route bypasses shared signing entirely. */
  ++visited;
 }
loc_00324173: ;
 ++cleanups;
}
int main(void){
 held=1;
 for(unsigned pass=0;pass<12;++pass) sub_00324060();
 if(removed || rejected || direct || submitted || wrong_stage || visited || cleanups!=12) return 1;
 if(nfl2k5_franchise_signing_was_held(100)) return 2;
 held=0;sub_00324060();
 if(removed!=50 || rejected!=50 || direct!=50 || visited!=100 || wrong_stage || cleanups!=13) return 3;
 return 0;
}
''')
            with patch.object(module.sys, 'argv', ['apply-gen-patches.py']), redirect_stdout(StringIO()):
                self.assertEqual(module.main(), 0)
                before = source.read_bytes()
                self.assertEqual(module.main(), 0)
                self.assertEqual(before, source.read_bytes())
            executable = Path(directory)/'cpu-check'
            subprocess.run([compiler, '-std=c11', '-DNFL2K5_FRANCHISE_CLIENT', '-I', str(ROOT),
                            str(source), str(ROOT/'native/franchise_bridge/game_addon_adapter.c'),
                            '-o', str(executable)], check=True, capture_output=True)
            subprocess.run([str(executable)], check=True, capture_output=True,
                           env={**os.environ, 'NFL2K5_FRANCHISE_NEGOTIATION': '0'}, timeout=10)
