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
        source = (ROOT / 'src/main.c').read_text()
        observer = source[source.index('static bool signing_screen_range('):
                          source.index('void nfl2k5_diag_texzero(')]
        harness = r'''
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
static unsigned char ram[0x1000000], before[0x1000000];
static unsigned char contig[0x10000], contig_before[0x10000];
#define XBOX_CONTIG_BASE 0x80000000u
#define XBOX_CONTIG_SIZE (sizeof contig)
static size_t g_xbox_total_ram = sizeof ram;
static unsigned reads;
static const char *trace_env;
static const char *test_getenv(const char *key) {
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
    uint32_t slot = 99;
    char name[151];
    put32(0xB72918, 0x5000); put32(0x5000, 2); put32(0x5004, 0x6000);
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
    put32(0xCB8C34, 0x1000); put32(0x1000, 0x6054); put32(0x1004, 0x4000);
    ram[0x100C] = 0x34; ram[0x100D] = 0x12;
    put32(0x6064, 0x8000); put32(0x6068, 0x8100);
    const uint16_t first[] = {'T','e','s','t',0}, last[] = {'P','l','a','y','e','r',0};
    memcpy(ram + 0x8000, first, sizeof first); memcpy(ram + 0x8100, last, sizeof last);
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
    memcpy(before, ram, sizeof ram); memcpy(contig_before, contig, sizeof contig);
    assert(signing_screen_slot(high_player, &slot) && slot == 1);
    assert(!signing_screen_read(XBOX_CONTIG_BASE + XBOX_CONTIG_SIZE - 1, name, 2));
    assert(!signing_screen_read(0x40000000u, name, 2));
    assert(!signing_screen_range(XBOX_CONTIG_BASE, UINT64_MAX));
    nfl2k5_diag_fsm(1, 0x557B2C, 1);
    assert(!memcmp(before, ram, sizeof ram)); assert(!memcmp(contig_before, contig, sizeof contig));
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'observer.c').write_text(harness + observer + cases)
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            str(path / 'observer.c'), '-o', str(path / 'observer.exe')], check=True)
            result = subprocess.run([str(path / 'observer.exe')], capture_output=True, text=True, check=True)
        self.assertIn('bank_slot=1 first_name="Test" last_name="Player"', result.stderr)
        self.assertEqual(result.stderr.count('bank_slot=1 first_name="Test" last_name="Player"'), 2)
        self.assertIn('identity_scope=current_bank_locator', result.stderr)
        self.assertIn('sign_player identity=unverified', result.stderr)
        self.assertIn('context_0C_word_raw=4660', result.stderr)
