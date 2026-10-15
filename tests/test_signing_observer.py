"""Compile actual observation code against authored RAM; no retail fixtures."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SigningObserverTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'), 'Portable C compiler required')
    def test_bank_identity_bounds_names_and_read_only_observation(self):
        source = (ROOT / 'src/nfl2k5_sidecar_adapter.c').read_text()
        host = (ROOT / 'src/main.c').read_text()
        capability = host[host.index('int nfl2k5_addon_guest_range('):]
        capability = capability[:capability.index('\n#endif')]
        observer = capability + source[source.index('static NFL2K5AddonHost adapter_host;'):
                                       source.index('static int addon_start(')]
        harness = r'''
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "nfl2k5_franchise_host.h"
#include "game_addon.h"
#include "finance_state.h"
#include "identity_state.h"
#define NFL2K5_FRANCHISE_CLIENT 1
static int reads_allowed=1;
int nfl2k5_addon_guest_read_allowed(void) {return reads_allowed;}
static int context_enabled;
static unsigned contexts;
static unsigned invalidations;
static unsigned polls;
static FranchiseSigningObservation captured;
int nfl2k5_franchise_context_enabled(void) { return context_enabled; }
void nfl2k5_franchise_on_fsm(uint32_t descriptor,int push) { (void)descriptor; (void)push; }
void nfl2k5_franchise_poll(void) { ++polls; }
void nfl2k5_franchise_signing_context(const FranchiseSigningObservation *observation) {
    if(!context_enabled) return;
    if (!observation) { ++invalidations; return; }
    captured=*observation; ++contexts;
}
static unsigned char ram[0x1000000], before[0x1000000];
static unsigned char contig[0x10000], contig_before[0x10000];
#define XBOX_CONTIG_BASE 0x80000000u
#define XBOX_CONTIG_SIZE (sizeof contig)
static size_t g_xbox_total_ram = sizeof ram;
static unsigned reads;
static const char *trace_env;
static const char *test_getenv(const char *key) {
    if(!strcmp(key,"NFL2K5_FRANCHISE_CAPTURE")) return NULL;
    assert(!strcmp(key, "NFL2K5_TRACE_FRANCHISE"));
    return trace_env;
}
#define getenv test_getenv
static void *xbox_GetMemoryOffset(void) { return ram; }
static bool xbox_guest_memory_read(uintptr_t base, uint64_t addr, void *out, size_t n) {
    ++reads;
    if (addr == 0x3000) return false;
    if (addr >= XBOX_CONTIG_BASE) {
        uint64_t offset = addr - XBOX_CONTIG_BASE;
        assert(offset + n <= sizeof contig);
        memcpy(out, contig + offset, n);
    } else {
        assert(addr + n <= sizeof ram);
        memcpy(out, (void *)(base + addr), n);
    }
    return true;
}
'''
        cases = r'''
static void put32(uint32_t address, uint32_t value) { memcpy(ram + address, &value, 4); }
int main(void) {
    adapter_host=(NFL2K5AddonHost){sizeof(NFL2K5AddonHost),nfl2k5_addon_guest_range,nfl2k5_addon_guest_read};
    uint32_t untouched=42;reads_allowed=0;
    assert(!nfl2k5_addon_guest_read(0x1000,&untouched,sizeof(untouched)) && untouched==42);reads_allowed=1;
    uint32_t slot = 99;
    uint32_t team_index = 99, team_mode = 99;
    char name[151];
    put32(0xB72918, 0x5000); put32(0x5000, 2); put32(0x5004, 0x6000);
    put32(0x5018, 52); put32(0x501C, 0x9000);
    assert(signing_screen_team(0x9000 + 15 * 0x1F4, &team_index, &team_mode));
    assert(team_index == 15 && team_mode == 0);
    assert(!signing_screen_team(0x9001, &team_index, &team_mode));
    assert(!signing_screen_team(0x9000 + 52 * 0x1F4, &team_index, &team_mode));
    assert(!signing_screen_team(0, &team_index, &team_mode));
    put32(0x5018, 53); assert(!signing_screen_team(0x9000, &team_index, &team_mode));
    put32(0x5018, 52); put32(0x501C, UINT32_MAX - 10);
    assert(!signing_screen_team(UINT32_MAX - 10, &team_index, &team_mode));
    put32(0x501C, 0x9000);
    put32(0xE576A0, 1); put32(0xE576AC, 2);
    put32(0xE5786C, 0x4000); put32(0xE57870, 0x4500);
    assert(signing_screen_team(0x4500, &team_index, &team_mode));
    assert(team_index == 1 && team_mode == 1);
    assert(!signing_screen_team(0x9000, &team_index, &team_mode));
    put32(0xE576A0, 2);
    assert(signing_screen_team(0x4000, &team_index, &team_mode));
    put32(0xE576AC, 53);
    assert(!signing_screen_team(0x4000, &team_index, &team_mode));
    put32(0xE576AC, 0);
    assert(!signing_screen_team(0x4000, &team_index, &team_mode));
    put32(0xE576AC, 2);
    put32(0xE576A0, 3);
    assert(!signing_screen_team(0x4000, &team_index, &team_mode));
    put32(0xE576A0, 0);
    assert(signing_screen_slot(0x6054, &slot) && slot == 1);
    assert(!signing_screen_slot(0x6055, &slot));
    assert(!signing_screen_slot(0x5FFF, &slot));
    assert(!signing_screen_slot(0x60A8, &slot));
    put32(0x5000, UINT32_MAX); assert(!signing_screen_slot(0x6000, &slot));
    put32(0x5000, 2); put32(0x5004, UINT32_MAX - 10);
    assert(!signing_screen_slot(UINT32_MAX - 10, &slot));
    put32(0x5004, 0x6000);
    /* BMP Unicode, quote/control rejection, bounded termination and read faults. */
    const uint16_t valid[] = {'R', 0xE9, 0}; memcpy(ram + 0x7000, valid, sizeof valid);
    assert(signing_screen_name(0x7000, name) && !strcmp(name, "R\xC3\xA9"));
    assert(!signing_screen_name(0x7001, name));
    ram[0x7000] = 10; assert(!signing_screen_name(0x7000, name));
    ram[0x7000] = '"'; assert(!signing_screen_name(0x7000, name));
    for (unsigned i = 0; i < 50; ++i) { ram[0x7000 + 2*i] = 'a'; ram[0x7001 + 2*i] = 0; }
    assert(!signing_screen_name(0x7000, name));
    assert(!signing_screen_name(0x3000, name));
    assert(!signing_screen_name(sizeof ram - 2, name));
    assert(!signing_screen_read(UINT32_MAX, name, 2));
    put32(0xCB8C34, 0x1000); put32(0x1000, 0x6054);
    put32(0x1004, 0x9000 + 15 * 0x1F4);
    put32(0x9000 + 15 * 0x1F4 + 0x124, 77038); put32(0xE3C278, 80500);
    ram[0x100C] = 0x34; ram[0x100D] = 0x12;
    put32(0x6064, 0x8000); put32(0x6068, 0x8100);
    const uint16_t first[] = {'T','e','s','t',0}, last[] = {'P','l','a','y','e','r',0};
    memcpy(ram + 0x8000, first, sizeof first); memcpy(ram + 0x8100, last, sizeof last);
    ram[0x6058] = 0x12; ram[0x6059] = 0x34; ram[0x605A] = 0xAB; ram[0x605B] = 0xCD;
    ram[0x606D] = 0x56; ram[0x606E] = 0x78; ram[0x606F] = 0xEF;
    memcpy(before, ram, sizeof ram);
    reads = 0; trace_env = NULL;
    nfl2k5_diag_fsm(1, 0x557B2C, 1); assert(reads == 0);
    trace_env = "1";
    nfl2k5_diag_fsm(1, 0x557B2C, 0); assert(reads == 0);
    nfl2k5_diag_fsm(1, 0x557B2C, 1); assert(reads > 0);
    assert(!memcmp(before, ram, sizeof ram));
    put32(0x1000, 0x6055); nfl2k5_diag_fsm(1, 0x557B2C, 1);
    /* Separate high-memory bank, player and names: do not wrap into low RAM. */
    put32(0xB72918, 0x5000); put32(0x5000, 2); put32(0x5004, XBOX_CONTIG_BASE + 0x1000);
    uint32_t high_player = XBOX_CONTIG_BASE + 0x1054;
    uint32_t high_first = XBOX_CONTIG_BASE + 0x2000, high_last = XBOX_CONTIG_BASE + 0x2100;
    memcpy(contig + 0x1064, &high_first, 4); memcpy(contig + 0x1068, &high_last, 4);
    memcpy(contig + 0x2000, first, sizeof first); memcpy(contig + 0x2100, last, sizeof last);
    put32(0x1000, high_player);
    put32(0x5018, 2); put32(0x501C, XBOX_CONTIG_BASE + 0x3000);
    put32(0x1004, XBOX_CONTIG_BASE + 0x31F4);
    const uint32_t high_payroll = 72272;
    memcpy(contig + 0x31F4 + 0x124, &high_payroll, sizeof high_payroll);
    assert(signing_screen_team(XBOX_CONTIG_BASE + 0x31F4, &team_index, &team_mode));
    assert(team_index == 1 && team_mode == 0);
    memcpy(before, ram, sizeof ram); memcpy(contig_before, contig, sizeof contig);
    assert(signing_screen_slot(high_player, &slot) && slot == 1);
    assert(!signing_screen_read(XBOX_CONTIG_BASE + XBOX_CONTIG_SIZE - 1, name, 2));
    assert(!signing_screen_read(0x40000000u, name, 2));
    assert(!signing_screen_range(XBOX_CONTIG_BASE, UINT64_MAX));
    nfl2k5_diag_fsm(1, 0x557B2C, 1);
    assert(!memcmp(before, ram, sizeof ram)); assert(!memcmp(contig_before, contig, sizeof contig));
    /* Actual franchise uses mode2 pointers. Calendar fields remain raw,
     * including nonzero retained accumulator; they do not grant a signing. */
    put32(0xE576A0, 2); put32(0xE576AC, 2);
    put32(0xE57870, XBOX_CONTIG_BASE + 0x31F4);
    put32(0xE576A4, 7); put32(0xE576B0, 5);
    put32(0xE576B8, 2); put32(0xE576BC, 99); put32(0xE57760, 1);
    const uint16_t accumulator = 500;
    memcpy(contig + 0x31F4 + 0x19C, &accumulator, sizeof accumulator);
    memcpy(before, ram, sizeof ram); memcpy(contig_before, contig, sizeof contig);
    context_enabled=1; trace_env=NULL;
    nfl2k5_franchise_guest_poll();
    assert(polls==1 && contexts==2 && invalidations==0 && captured.slot==1 && captured.team_index==1);
    assert(!strcmp(captured.first_name,"Test") && !strcmp(captured.last_name,"Player"));
    assert(!strcmp(captured.photo,"00000000") && !strcmp(captured.dob,"000000"));
    assert(captured.payroll==72272 && captured.cap==80500 && captured.accumulator==500);
    assert(captured.offer_amount==4660 && captured.offer_flags==0);
    assert(captured.calendar[5]==2 && captured.calendar[6]==99 && captured.team_flag==1);
    assert(!memcmp(before,ram,sizeof ram) && !memcmp(contig_before,contig,sizeof contig));
    put32(0xE576B8,256);
    nfl2k5_franchise_guest_poll(); assert(polls==2 && contexts==2 && invalidations==2);
    put32(0xE576B8,2);
    context_enabled=0; trace_env="1";
    nfl2k5_diag_fsm(1, 0x557B2C, 1);
    assert(!memcmp(before, ram, sizeof ram)); assert(!memcmp(contig_before, contig, sizeof contig));
    put32(0xE576B8, 256); memcpy(before, ram, sizeof ram);
    nfl2k5_diag_fsm(1, 0x557B2C, 1);
    assert(!memcmp(before, ram, sizeof ram)); assert(!memcmp(contig_before, contig, sizeof contig));
    /* Transaction checkpoints have their own bound, do not read when disabled,
     * and accept high-memory locators without touching terms or guest registers. */
    put32(0x2200, 95); put32(0x2300, 0x3478B6);
    memcpy(before, ram, sizeof ram); memcpy(contig_before, contig, sizeof contig);
    trace_env = NULL; reads = 0;
    nfl2k5_diag_signing(0, 0x1000, 0x2200, 0, 0x2300); assert(!reads);
    trace_env = "1";
    nfl2k5_diag_signing(3, 0x1000, 0x2200, 0, 0x2300); assert(!reads);
    nfl2k5_diag_signing(0, 0x1000, 0x2200, 0, 0x2300);
    nfl2k5_diag_signing(1, 0x1000, 0x2200, 1, 0x2300);
    nfl2k5_diag_signing(2, 0x1000, 0x2200, 0, 0x2300);
    nfl2k5_diag_signing(1, 0x1000, UINT32_MAX, 0, 0x2300);
    nfl2k5_diag_signing(0, UINT32_MAX, 0x2200, 0, UINT32_MAX);
    assert(!memcmp(before, ram, sizeof ram)); assert(!memcmp(contig_before, contig, sizeof contig));
    for (unsigned i=5; i<256; ++i)
        nfl2k5_diag_signing(0, UINT32_MAX, 0, 0, 0);
    reads = 0;
    nfl2k5_diag_signing(1, 0x1000, 0x2200, 1, 0x2300); assert(!reads);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'observer.c').write_text(harness + observer + cases)
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-I', str(ROOT / 'src'),
                            '-I', str(ROOT / 'native/franchise_bridge'),
                            str(path / 'observer.c'), '-o', str(path / 'observer.exe')], check=True)
            result = subprocess.run([str(path / 'observer.exe')], capture_output=True, text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('bank_slot=1 first_name="Test" last_name="Player"', result.stderr)
        self.assertEqual(result.stderr.count('bank_slot=1 first_name="Test" last_name="Player"'), 4)
        self.assertIn('identity_scope=current_bank_locator', result.stderr)
        self.assertIn('sign_player identity=unverified', result.stderr)
        self.assertIn('context_0C_word_raw=4660', result.stderr)
        self.assertIn('sign_player_guard bank_slot=1 pbp_photo_raw=1234abcd dob_region_raw=5678ef', result.stderr)
        self.assertEqual(result.stderr.count('sign_player_guard bank_slot=1'), 4)
        self.assertIn('sign_team table_index=15 table_mode=0 payroll_124_raw=77038 league_cap_raw=80500', result.stderr)
        self.assertIn('accounting_scope=original_unreconciled', result.stderr)
        self.assertIn('sign_team table_index=1 table_mode=0 payroll_124_raw=72272 league_cap_raw=80500', result.stderr)
        self.assertIn('sign_calendar season_index_raw=2 display_year=2006 phase_01_raw=7', result.stderr)
        self.assertIn('counter_08_raw=99 team_flag_raw=1 first_year_accumulator_raw=500', result.stderr)
        self.assertIn('sign_calendar state=unverified', result.stderr)
        self.assertIn('stage=0 context=0x00001000 result=0x00002200 caller_known=1 caller_raw=0x003478B6', result.stderr)
        self.assertIn('return_code_raw=1 output_known=1 output_raw=95', result.stderr)
        self.assertIn('result=0xFFFFFFFF', result.stderr)
        self.assertIn('return_code_raw=0 output_known=0 output_raw=0', result.stderr)
        self.assertIn('sign_transaction_player sequence=1 bank_slot=1', result.stderr)
        self.assertIn('sign_transaction_team sequence=1 table_index=1 table_mode=2', result.stderr)
        self.assertEqual(result.stderr.count('[FRANCHISE-TRACE] sign_transaction sequence='), 256)
