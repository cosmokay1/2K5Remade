"""Exercise the actual Windows handler's opt-in dispatch without a game build."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class CrashCaptureTests(unittest.TestCase):
    def test_recognized_faults_capture_only_when_enabled(self):
        cc = shutil.which('clang') or shutil.which('cc')
        if not cc:
            self.skipTest('C compiler unavailable')
        text = (Path(__file__).resolve().parents[1] / 'src/main.c').read_text()
        start = text.index('static LONG CALLBACK crash_report(')
        handler = text[start:text.index('\n#else', start)]
        harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned long DWORD;
typedef long LONG;
#define CALLBACK
#define EXCEPTION_ACCESS_VIOLATION 0xC0000005ul
#define EXCEPTION_ILLEGAL_INSTRUCTION 0xC000001Dul
#define EXCEPTION_STACK_OVERFLOW 0xC00000FDul
#define EXCEPTION_INT_DIVIDE_BY_ZERO 0xC0000094ul
#define EXCEPTION_CONTINUE_SEARCH 0
#define EXCEPTION_EXECUTE_HANDLER 1
typedef struct { DWORD ExceptionCode; } RECORD;
typedef struct { uint64_t Rip; } CONTEXT;
typedef struct { RECORD *ExceptionRecord; CONTEXT *ContextRecord; } EXCEPTION_POINTERS;
static unsigned g_eax,g_ecx,g_edx,g_esp,g_ebx,g_esi,g_edi,g_xbox_total_ram=64u*1024u*1024u;
static int captures,dumps;
static uintptr_t xbox_GetMemoryOffset(void) { return 0; }
static void nfl2k5_crash_context(FILE *f,const CONTEXT *c,uint32_t sp,uintptr_t base,size_t size) {
    (void)f;(void)c;(void)sp;(void)base;(void)size;captures++;
}
#define RECOMP_ICALL_FEEDBACK_DUMP() (++dumps)
''' + handler + r'''
int main(void) {
    const DWORD codes[]={EXCEPTION_ACCESS_VIOLATION,EXCEPTION_ILLEGAL_INSTRUCTION,
        EXCEPTION_STACK_OVERFLOW,EXCEPTION_INT_DIVIDE_BY_ZERO};
    RECORD r={0}; CONTEXT c={0}; EXCEPTION_POINTERS ep={&r,&c};
    for(unsigned enabled=0;enabled<2;enabled++) {
        if(enabled)setenv("NFL2K5_CRASH_GUEST_CONTEXT","1",1);
        else unsetenv("NFL2K5_CRASH_GUEST_CONTEXT");
        for(unsigned i=0;i<4;i++) {
            captures=dumps=0;r.ExceptionCode=codes[i];
            if(crash_report(&ep)!=EXCEPTION_EXECUTE_HANDLER || captures!=(int)enabled || dumps!=1)return 2;
        }
    }
    captures=dumps=0;r.ExceptionCode=7;
    if(crash_report(&ep)!=EXCEPTION_CONTINUE_SEARCH || captures || dumps)return 3;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'dispatch.c'
            exe = Path(directory) / 'dispatch'
            source.write_text(harness)
            built = subprocess.run([cc, '-std=c11', '-D_POSIX_C_SOURCE=200809L',
                                    str(source), '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            ran = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(ran.returncode, 0, ran.stderr)
