"""Run the actual manual worker dispatch without game assets."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class IoWorkerDispatchTests(unittest.TestCase):
    def test_pack_worker_defers_before_retail_frame_or_table_access(self):
        compiler = shutil.which('cc')
        if not compiler:
            self.skipTest('C compiler unavailable')
        manual = (ROOT / 'src/recomp_manual.c').read_text()
        start = manual.index('static void nfl2k5_io_worker(void)')
        block = manual[start:manual.index('static void nfl2k5_io_completion(void)', start)]
        stubs = '\n'.join(f'void sub_{name}(void){{}}' for name in (
            '0004B910', '0004D630', '0004D720', '0004CF30', '0004D210',
            '0004CFE0', '0004D2E0', '0004D350', '0004D3C0', '0004D430',
            '0004D480', '0004D4C0', '0003A4F0'))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'worker.c'
            binary = Path(directory) / 'worker'
            source.write_text(r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static uint32_t g_eax,g_ecx,g_edx,g_esp,g_esi;
static uint32_t state,stack[16],interpreted;
static int g_interp_active;
static uint32_t *mem(uint32_t address) {
    /* Any retail-table/frame access in pack mode is a regression. */
    if(g_interp_active) abort();
    if(address==0xA7D300) return &state;
    if(address>=0x1000 && address<0x1040) return &stack[(address-0x1000)/4];
    abort();
}
#define MEM32(address) (*mem(address))
#define PUSH32(sp,value) do{(sp)-=4;MEM32(sp)=(value);}while(0)
#define POP32(sp,value) do{(value)=MEM32(sp);(sp)+=4;}while(0)
void recomp_interp_call(uint32_t address) {
    if(address!=0x4D810 || g_esp!=0x1020 || g_esi!=123) abort();
    ++interpreted;
    g_esp+=8;g_eax=42;
}
void sub_0004B920(void){g_esp+=4;}
''' + stubs + '\n' + block + r'''
int main(void){
    /* Changed pack: no native stack/table accesses before interpreting. */
    g_interp_active=1;g_esp=0x1020;g_esi=123;state=11;
    nfl2k5_io_worker();
    if(interpreted!=1 || g_esp!=0x1028 || g_eax!=42 || g_esi!=123 || state!=11) return 1;
    /* Unmodified native path keeps its saved ESI and ret-4 ABI. */
    g_interp_active=0;g_esp=0x1020;g_esi=123;state=13;
    nfl2k5_io_worker();
    return interpreted!=1 || g_esp!=0x1028 || g_esi!=123 || state!=0;
}
''')
            subprocess.run([compiler, '-std=c11', str(source), '-o', str(binary)], check=True, capture_output=True)
            subprocess.run([str(binary)], check=True, capture_output=True)
