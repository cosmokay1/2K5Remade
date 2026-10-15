"""Production judgment/commit patches plus the actual shim, authored grants only."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
from io import StringIO
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class SigningApplicationTests(unittest.TestCase):
    def test_authorized_judgment_skips_retail_but_keeps_original_commit_boundary(self):
        compiler=shutil.which('cc')
        if not compiler:self.skipTest('C compiler unavailable; native application fixture runs in CI')
        spec=importlib.util.spec_from_file_location('application_patch',ROOT/'tools/apply-gen-patches.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.PATCHES=[row for row in module.PATCHES if row[0] in ('FRANCHISE_SIGN_HOLD_JUDGMENT','FRANCHISE_SIGN_HOLD_COMMIT','FRANCHISE_SIGN_COMPLETED')]
        self.assertEqual(len(module.PATCHES),3)
        with tempfile.TemporaryDirectory() as directory:
            module.GEN=directory;source=Path(directory)/'recomp_authored.c'
            source.write_text(r'''
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "src/nfl2k5_sidecar_adapter.h"
#include "native/franchise_bridge/franchise_addon.h"
static uint32_t esi=0x1234,edi,ebp=0x5678,eax;
static unsigned retail_calls,writes,history,completions;
static int judgment,commit,retail_accept;
uint64_t xbox_ggl_current_serial(void){return 1;}
int nfl2k5_addon_start(void){return 1;}
void nfl2k5_addon_stop(void){}
void nfl2k5_addon_poll(void){}
int nfl2k5_addon_snapshot(const char*n,void*o,size_t c){return 0;}
int nfl2k5_addon_event(const char*n,const void*d,size_t size){
 if(!strcmp(n,FRANCHISE_SIGN_COMPLETED_EVENT)) {
  if(size!=sizeof(uint32_t) || *(const uint32_t *)d!=esi || writes!=1 || history!=1) abort();
  ++completions;return 2; /* A reply cannot authorize any subsequent signing. */
 }
 if(strcmp(n,FRANCHISE_SIGN_APPLICATION_EVENT)) return 0;
 if(size!=sizeof(FranchiseSignGateEvent)) abort();
 const FranchiseSignGateEvent *event=d;
 if(event->context!=esi) abort();
 return event->stage==1?judgment:commit;
}
/* Authored routine retains judgment, precommit, success and failure cleanup.
 * Both inserted bodies come from the production patcher. */
void sub_00323D80(void)
{
 nfl2k5_diag_signing(0,esi,0,0,0);
loc_00323F0A: ;
 edi=ebp;++retail_calls;eax=retail_accept;
loc_00323F13: ;
 if(!eax) goto loc_00323E99;
loc_00323F17: ;
 ++writes;++history;
loc_0032404E: ;
 eax=1;return;
loc_00323E99: ;
 eax=0;return;
}
int main(void){
 judgment=commit=2;retail_accept=0;
 sub_00323D80();
 if(eax!=1 || edi!=ebp || retail_calls || writes!=1 || history!=1 ||
    completions!=1 || nfl2k5_franchise_signing_was_held(esi)) return 1;
 commit=0;
 sub_00323D80();
 if(eax || retail_calls || writes!=1 || history!=1 || !nfl2k5_franchise_signing_was_held(esi)) return 2;
 judgment=0;commit=2;
 sub_00323D80();
 if(eax || retail_calls || writes!=1 || history!=1 || !nfl2k5_franchise_signing_was_held(esi)) return 3;
#ifdef _WIN32
 if(_putenv_s("NFL2K5_FRANCHISE_NEGOTIATION","0")) return 4;
#else
 if(setenv("NFL2K5_FRANCHISE_NEGOTIATION","0",1)) return 4;
#endif
 sub_00323D80();
 if(eax || retail_calls!=1 || writes!=1 || history!=1 || nfl2k5_franchise_signing_was_held(esi)) return 5;
 retail_accept=1;sub_00323D80();
 if(eax!=1 || retail_calls!=2 || writes!=2 || history!=2 || completions!=1) return 6;
 return 0;
}
''')
            with patch.object(module.sys,'argv',['apply-gen-patches.py']),redirect_stdout(StringIO()):
                self.assertEqual(module.main(),0)
                before=source.read_bytes();self.assertEqual(module.main(),0)
                self.assertEqual(source.read_bytes(),before)
            completion=next(row for row in module.PATCHES if row[0]=='FRANCHISE_SIGN_COMPLETED')
            text=source.read_text()
            # A moved or customized completion callback could report success
            # before writes. Refuse these caches rather than trusting a marker.
            lines=text.splitlines(keepends=True)
            index=next(i for i,line in enumerate(lines) if 'NFL2K5-GENPATCH:FRANCHISE_SIGN_COMPLETED' in line)
            block=''.join(lines[index:index+2])
            for invalid in (text.replace(completion[4].strip(),completion[4].strip()+' /* custom */'),
                            text.replace(block,'').replace('loc_00323F17: ;','loc_00323F17: ;\n'+block)):
                source.write_text(invalid)
                with patch.object(module.sys,'argv',['apply-gen-patches.py','--check']),redirect_stdout(StringIO()),redirect_stderr(StringIO()):
                    self.assertEqual(module.main(),1)
                self.assertEqual(source.read_text(),invalid)
            source.write_text(text)
            executable=Path(directory)/'application-check'
            subprocess.run([compiler,'-std=c11','-D_POSIX_C_SOURCE=200809L','-DNFL2K5_FRANCHISE_CLIENT',
                '-I',str(ROOT),str(source),str(ROOT/'native/franchise_bridge/game_addon_adapter.c'),
                '-o',str(executable)],check=True,capture_output=True)
            subprocess.run([str(executable)],check=True,capture_output=True,timeout=10,
                env={**os.environ,'NFL2K5_FRANCHISE_NEGOTIATION':'1','NFL2K5_FRANCHISE_GUEST_SIGNING':'1'})
