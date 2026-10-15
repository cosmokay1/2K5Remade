/* NFL 2K5 application adapter for the standalone sidecar transport.
 * Game-specific observations stay here, outside main.c and the generic addon.
 * Existing callbacks and read-only behavior are preserved; no guest writes.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "game_addon.h"
#include "franchise_addon.h"
#include "nfl2k5_sidecar_adapter.h"
#ifdef NFL2K5_FRANCHISE_CLIENT
#include "nfl2k5_franchise_host.h"
#endif

static NFL2K5AddonHost adapter_host;
static bool signing_screen_range(uint32_t address,uint64_t size)
{
    return size<=SIZE_MAX && adapter_host.memory_range && adapter_host.memory_range(address,(size_t)size)!=0;
}
static bool signing_screen_read(uint32_t address, void *out, size_t size)
{
    return adapter_host.read_memory && adapter_host.read_memory(address,out,size)!=0;
}

/* The retail slot getter (0x0031DBE0) uses this bank's count/base and
 * 0x54-byte stride. A slot is a locator in the current bank, not a durable ID. */
static bool signing_screen_slot(uint32_t player, uint32_t *slot)
{
    uint32_t bank, header[2];
    uint64_t end;
    if (!signing_screen_read(0x00B72918u, &bank, sizeof(bank)) ||
        !signing_screen_read(bank, header, sizeof(header)) ||
        !header[0] || header[0] > INT32_MAX || !header[1])
        return false;
    end = (uint64_t)header[1] + (uint64_t)header[0] * 0x54u;
    if (!signing_screen_range(header[1], (uint64_t)header[0] * 0x54u) ||
        player < header[1] ||
        (uint64_t)player + 0x54u > end || (player - header[1]) % 0x54u)
        return false;
    *slot = (player - header[1]) / 0x54u;
    return true;
}

/* Mirror the observed retail team-table selection (0xC4B80/C4BE0/C4C50),
 * with a strict bound. This yields a current-table locator, not franchise ID. */
static bool signing_screen_team(uint32_t team, uint32_t *index, uint32_t *mode)
{
    uint32_t count, base, bank;
    if (!team || !signing_screen_read(0x00E576A0u, mode, sizeof(*mode)) ||
        *mode > 2u)
        return false;
    if (*mode == 0u) {
        uint32_t header[2];
        if (!signing_screen_read(0x00B72918u, &bank, sizeof(bank)) ||
            bank > UINT32_MAX - 0x18u ||
            !signing_screen_read(bank + 0x18u, header, sizeof(header)))
            return false;
        count = header[0]; base = header[1];
        if (!count || count > 52u ||
            !signing_screen_range(base, (uint64_t)count * 0x1F4u) ||
            team < base || (uint64_t)team >= (uint64_t)base + count * 0x1F4u ||
            (team - base) % 0x1F4u)
            return false;
        *index = (team - base) / 0x1F4u;
        return true;
    }
    if (!signing_screen_read(0x00E576ACu, &count, sizeof(count)) ||
        !count || count > 52u)
        return false;
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t candidate;
        if (!signing_screen_read(0x00E5786Cu + i * 4u, &candidate, sizeof(candidate)))
            return false;
        if (candidate == team) { *index = i; return true; }
    }
    return false;
}

/* Read only relocated UTF-16 names, never guess relative pointers. Reject
 * malformed/unbounded text; a failed name is an unknown identity observation. */
static bool signing_screen_name(uint32_t address, char out[151])
{
    size_t used = 0;
    for (uint32_t i = 0; i < 50; ++i) {
        uint16_t ch;
        uint64_t location = (uint64_t)address + i * 2u;
        if (!address || address % 2u || location > UINT32_MAX ||
            !signing_screen_read((uint32_t)location, &ch, sizeof(ch)))
            return false;
        if (!ch) { out[used] = 0; return used != 0; }
        /* Surrogate pairs are unsupported here; do not print broken UTF-8. */
        if (ch < 32 || (ch >= 0x7Fu && ch <= 0x9Fu) ||
            (ch >= 0xD800u && ch <= 0xDFFFu) || ch == '"' || ch == '\\')
            return false;
        if (ch < 0x80u) out[used++] = (char)ch;
        else if (ch < 0x800u) {
            out[used++] = (char)(0xC0u | (ch >> 6));
            out[used++] = (char)(0x80u | (ch & 0x3Fu));
        } else {
            out[used++] = (char)(0xE0u | (ch >> 12));
            out[used++] = (char)(0x80u | ((ch >> 6) & 0x3Fu));
            out[used++] = (char)(0x80u | (ch & 0x3Fu));
        }
    }
    return false;
}

#ifdef NFL2K5_FRANCHISE_CLIENT
static bool signing_screen_context(void)
{
    if (!nfl2k5_franchise_context_enabled()) return false;
    FranchiseSigningObservation observation = {0};
    uint32_t context, player, team, mode, first, last;
    uint8_t record[0x28];
    uint16_t accumulator;
    uint16_t offer_amount;
    if (!signing_screen_read(0x00CB8C34u,&context,sizeof(context)) ||
        !signing_screen_read(context,&player,sizeof(player)) || context > UINT32_MAX-0x0Cu ||
        !signing_screen_read(context+4u,&team,sizeof(team)) ||
        !signing_screen_read(player,record,sizeof(record)) ||
        !signing_screen_slot(player,&observation.slot) ||
        !signing_screen_team(team,&observation.team_index,&mode) || mode!=2u || observation.team_index>=32u ||
        team > UINT32_MAX-0x19Cu) return false;
    memcpy(&first,record+0x10,sizeof(first)); memcpy(&last,record+0x14,sizeof(last));
    if (!signing_screen_name(first,observation.first_name) || !signing_screen_name(last,observation.last_name) ||
        !signing_screen_read(team+0x124u,&observation.payroll,sizeof(observation.payroll)) ||
        !signing_screen_read(0x00E3C278u,&observation.cap,sizeof(observation.cap)) ||
        !signing_screen_read(0x00E576A4u,observation.calendar,sizeof(observation.calendar)) ||
        observation.calendar[5]>255u ||
        !signing_screen_read(0x00E5775Cu+observation.team_index*4u,&observation.team_flag,sizeof(observation.team_flag)) ||
        !signing_screen_read(team+0x19Cu,&accumulator,sizeof(accumulator)) ||
        !signing_screen_read(context+0x0Cu,&offer_amount,sizeof(offer_amount)) ||
        !signing_screen_read(context+8u,&observation.offer_flags,sizeof(observation.offer_flags))) return false;
    observation.accumulator=accumulator;
    observation.offer_amount=offer_amount;
    snprintf(observation.photo,sizeof(observation.photo),"%02x%02x%02x%02x",
        (unsigned)record[4],(unsigned)record[5],(unsigned)record[6],(unsigned)record[7]);
    snprintf(observation.dob,sizeof(observation.dob),"%02x%02x%02x",
        (unsigned)record[0x19],(unsigned)record[0x1A],(unsigned)record[0x1B]);
    nfl2k5_franchise_signing_context(&observation);
    return true;
}
void nfl2k5_franchise_guest_poll(void)
{
    if (!signing_screen_context()) nfl2k5_franchise_signing_context(NULL);
    nfl2k5_franchise_poll();
    if (!signing_screen_context()) nfl2k5_franchise_signing_context(NULL);
}
#endif
void nfl2k5_diag_fsm(uint32_t obj, uint32_t desc, int push)
{
#ifdef NFL2K5_FRANCHISE_CLIENT
    nfl2k5_franchise_on_fsm(desc, push);
    if (push && desc == 0x00557B2Cu && !signing_screen_context()) nfl2k5_franchise_signing_context(NULL);
#endif
    static unsigned int recorded;
    const char *enabled = getenv("NFL2K5_TRACE_FRANCHISE");
    if (!enabled || strcmp(enabled, "1") || recorded >= 256) return;
    /* Existing FSM probes only: no guest writes or guessed screen IDs. */
    fprintf(stderr, "[FRANCHISE-TRACE] fsm_%s sequence=%u object=0x%08X descriptor=0x%08X\n",
        push ? "push" : "pop", ++recorded, (unsigned int)obj, (unsigned int)desc);
    if (push && desc == 0x00557B2Cu) {
        uint32_t context = 0, player = 0, other = 0, other_raw = 0;
        uint8_t context_raw[16], player_raw[0x28];
        uint16_t salary_raw, offer_salary_raw;
        uint32_t offer_flags_raw;
        if (!signing_screen_read(0x00CB8C34u, &context, sizeof(context)) ||
            !signing_screen_read(context, context_raw, sizeof(context_raw))) {
            fprintf(stderr, "[FRANCHISE-TRACE] sign_screen unreadable_context\n");
            return;
        }
        memcpy(&player, context_raw, sizeof(player));
        memcpy(&other, context_raw + 4, sizeof(other));
        if (!signing_screen_read(player, player_raw, sizeof(player_raw)) ||
            !signing_screen_read(other, &other_raw, sizeof(other_raw))) {
            fprintf(stderr, "[FRANCHISE-TRACE] sign_screen unreadable_records context=0x%08X player=0x%08X other=0x%08X\n",
                (unsigned int)context, (unsigned int)player, (unsigned int)other);
            return;
        }
        uint32_t slot, first_pointer, last_pointer;
        char first_name[151], last_name[151];
        memcpy(&first_pointer, player_raw + 0x10, sizeof(first_pointer));
        memcpy(&last_pointer, player_raw + 0x14, sizeof(last_pointer));
        if (signing_screen_slot(player, &slot) &&
            signing_screen_name(first_pointer, first_name) &&
            signing_screen_name(last_pointer, last_name)) {
            fprintf(stderr, "[FRANCHISE-TRACE] sign_player bank_slot=%u first_name=\"%s\" last_name=\"%s\" identity_scope=current_bank_locator\n",
                (unsigned int)slot, first_name, last_name);
            fprintf(stderr, "[FRANCHISE-TRACE] sign_player_guard bank_slot=%u pbp_photo_raw=%02x%02x%02x%02x dob_region_raw=%02x%02x%02x identity_scope=unbound_snapshot_guard\n",
                (unsigned int)slot,
                (unsigned int)player_raw[4], (unsigned int)player_raw[5],
                (unsigned int)player_raw[6], (unsigned int)player_raw[7],
                (unsigned int)player_raw[0x19], (unsigned int)player_raw[0x1A],
                (unsigned int)player_raw[0x1B]);
        } else {
            fprintf(stderr, "[FRANCHISE-TRACE] sign_player identity=unverified\n");
        }
        uint32_t team_index, team_mode, payroll_raw, cap_raw;
        if (signing_screen_team(other, &team_index, &team_mode) &&
            other <= UINT32_MAX - 0x124u &&
            signing_screen_read(other + 0x124u, &payroll_raw, sizeof(payroll_raw)) &&
            signing_screen_read(0x00E3C278u, &cap_raw, sizeof(cap_raw))) {
            fprintf(stderr, "[FRANCHISE-TRACE] sign_team table_index=%u table_mode=%u payroll_124_raw=%u league_cap_raw=%u identity_scope=current_table_locator accounting_scope=original_unreconciled\n",
                (unsigned int)team_index, (unsigned int)team_mode,
                (unsigned int)payroll_raw, (unsigned int)cap_raw);
            if (team_mode == 2u && team_index < 32u) {
                uint32_t calendar[7], team_flag;
                uint16_t accumulator;
                if (signing_screen_read(0x00E576A4u, calendar, sizeof(calendar)) &&
                    calendar[5] <= 255u &&
                    signing_screen_read(0x00E5775Cu + team_index * 4u, &team_flag, sizeof(team_flag)) &&
                    other <= UINT32_MAX - 0x19Cu &&
                    signing_screen_read(other + 0x19Cu, &accumulator, sizeof(accumulator))) {
                    fprintf(stderr, "[FRANCHISE-TRACE] sign_calendar season_index_raw=%u display_year=%u phase_01_raw=%u phase_02_raw=%u step_04_raw=%u step_05_raw=%u counter_08_raw=%u team_flag_raw=%u first_year_accumulator_raw=%u scope=original_calendar_adjustment_unreconciled\n",
                        (unsigned int)calendar[5], (unsigned int)(2004u + calendar[5]),
                        (unsigned int)calendar[0], (unsigned int)calendar[1],
                        (unsigned int)calendar[3], (unsigned int)calendar[4],
                        (unsigned int)calendar[6], (unsigned int)team_flag,
                        (unsigned int)accumulator);
                } else {
                    fprintf(stderr, "[FRANCHISE-TRACE] sign_calendar state=unverified\n");
                }
            }
        } else {
            fprintf(stderr, "[FRANCHISE-TRACE] sign_team identity=unverified\n");
        }
        memcpy(&salary_raw, player_raw + 0x0A, sizeof(salary_raw));
        memcpy(&offer_salary_raw, context_raw + 0x0C, sizeof(offer_salary_raw));
        memcpy(&offer_flags_raw, context_raw + 8, sizeof(offer_flags_raw));
        fprintf(stderr, "[FRANCHISE-TRACE] sign_screen context=0x%08X player=0x%08X other=0x%08X context_08_raw=0x%02X context_09_raw=0x%02X context_0A_raw=0x%02X context_0C_raw=0x%02X context_08_word_raw=0x%08X context_0C_word_raw=%u player_salary_0A_raw=%u units=unverified player_profile_26_raw=0x%02X player_term_27_raw=0x%02X identity=unverified\n",
            (unsigned int)context, (unsigned int)player, (unsigned int)other,
            (unsigned int)context_raw[8], (unsigned int)context_raw[9],
            (unsigned int)context_raw[10], (unsigned int)context_raw[12],
            (unsigned int)offer_flags_raw, (unsigned int)offer_salary_raw,
            (unsigned int)salary_raw, (unsigned int)player_raw[0x26],
            (unsigned int)player_raw[0x27]);
    }
}
/* Read-only checkpoints in the shared signing transaction. Stage1 is the
 * interactive judgment return; stage2 may also be reached by its bypass path.
 * Neither checkpoint proves that a contract was committed or grants AI access. */
void nfl2k5_diag_signing(uint32_t stage, uint32_t context, uint32_t result,
                         uint32_t return_code, uint32_t stack)
{
    static unsigned int recorded;
    const char *enabled = getenv("NFL2K5_TRACE_FRANCHISE");
    if (!enabled || strcmp(enabled, "1") || stage > 2u || recorded >= 256u) return;
    uint8_t raw[16], guard[4], dob[3];
    uint32_t player, team, flags, slot, team_index, team_mode;
    uint32_t caller = 0, output = 0;
    uint16_t amount;
    int caller_known = stage == 0u && signing_screen_read(stack, &caller, sizeof(caller));
    int output_known = stage != 0u && signing_screen_read(result, &output, sizeof(output));
    ++recorded;
    if (!signing_screen_read(context, raw, sizeof(raw))) {
        fprintf(stderr, "[FRANCHISE-TRACE] sign_transaction sequence=%u stage=%u context=0x%08X state=unreadable\n",
            recorded, (unsigned int)stage, (unsigned int)context);
        return;
    }
    memcpy(&player, raw, sizeof(player));
    memcpy(&team, raw + 4, sizeof(team));
    memcpy(&flags, raw + 8, sizeof(flags));
    memcpy(&amount, raw + 0xC, sizeof(amount));
    fprintf(stderr, "[FRANCHISE-TRACE] sign_transaction sequence=%u stage=%u context=0x%08X result=0x%08X caller_known=%d caller_raw=0x%08X return_code_raw=%u output_known=%d output_raw=%u offer_flags_raw=0x%08X offer_amount_word_raw=%u scope=original_transaction_checkpoint\n",
        recorded, (unsigned int)stage, (unsigned int)context, (unsigned int)result,
        caller_known, (unsigned int)caller, (unsigned int)return_code,
        output_known, (unsigned int)output, (unsigned int)flags, (unsigned int)amount);
    if (signing_screen_slot(player, &slot) && player <= UINT32_MAX - 0x1Bu &&
        signing_screen_read(player + 4u, guard, sizeof(guard)) &&
        signing_screen_read(player + 0x19u, dob, sizeof(dob))) {
        fprintf(stderr, "[FRANCHISE-TRACE] sign_transaction_player sequence=%u bank_slot=%u pbp_photo_raw=%02x%02x%02x%02x dob_region_raw=%02x%02x%02x identity_scope=unbound_snapshot_guard\n",
            recorded, (unsigned int)slot, guard[0], guard[1], guard[2], guard[3], dob[0], dob[1], dob[2]);
    }
    if (signing_screen_team(team, &team_index, &team_mode)) {
        fprintf(stderr, "[FRANCHISE-TRACE] sign_transaction_team sequence=%u table_index=%u table_mode=%u identity_scope=current_table_locator\n",
            recorded, (unsigned int)team_index, (unsigned int)team_mode);
    }
}

static int addon_start(const NFL2K5AddonHost *host) {
    if(!host || host->size!=sizeof(*host) || !host->read_memory || !host->memory_range) return 0;
    adapter_host=*host;
    if(!nfl2k5_franchise_start()) { memset(&adapter_host,0,sizeof(adapter_host));return 0; }
    return 1;
}
static void addon_stop(void) {
    nfl2k5_franchise_stop();
    memset(&adapter_host,0,sizeof(adapter_host));
}
static int addon_event(const char *name,const void *data,size_t size) {
    if(!name || !data) return 0;
    if(!strcmp(name,FRANCHISE_FSM_EVENT) && size==sizeof(FranchiseFSMEvent)) {
        FranchiseFSMEvent event;memcpy(&event,data,sizeof(event));
        nfl2k5_diag_fsm(event.object,event.descriptor,event.push!=0);return 1;
    }
    if(!strcmp(name,FRANCHISE_SIGNING_EVENT) && size==sizeof(FranchiseSigningEvent)) {
        FranchiseSigningEvent event;memcpy(&event,data,sizeof(event));
        nfl2k5_diag_signing(event.stage,event.context,event.result,event.code,event.stack);return 1;
    }
    return 0;
}
static int addon_snapshot(const char *name,void *out,size_t capacity) {
    if(!name || !out || strcmp(name,FRANCHISE_DISPLAY_SNAPSHOT) || capacity!=sizeof(FranchiseSigningDisplay)) return 0;
    FranchiseSigningDisplay display;
    if(!nfl2k5_franchise_display(&display)) return 0;
    memcpy(out,&display,sizeof(display));return 1;
}
static const NFL2K5AddonAPI addon_api={sizeof(NFL2K5AddonAPI),addon_start,addon_stop,
    nfl2k5_franchise_guest_poll,addon_event,addon_snapshot};
#ifdef _WIN32
__declspec(dllexport)
#endif
const NFL2K5AddonAPI *nfl2k5_addon_query(uint32_t abi) {
    return abi==NFL2K5_ADDON_ABI ? &addon_api : NULL;
}
