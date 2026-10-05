#pragma once
#include <algorithm>
#include <cstdint>
#include <string>

// A slot owns this policy. Call finish_cycle only after target verification,
// any checkpoint replay, and committing the accepted tokens at a safe boundary.
struct spine_mtp_config {
    std::string mode; // empty means preserve the original server behavior
    std::string workload;
    int expected_output_tokens = 0;
    double direct_ms_per_token = 0;
    std::string calibration_id;
    int calibrated_prompt_max = 0;
    int test_fallback_after = 0; // requires SPINE_MTP_TEST_HOOKS on the server
};

struct spine_mtp_policy {
    spine_mtp_config config;
    bool enabled = true;
    bool initially_enabled = true;
    std::string reason = "inherit";
    int cycles = 0;
    int committed_tokens = 0;
    int fallback_at = -1;
    int windows = 0;
    int bad_windows = 0;
    int window_cycles = 0;
    int window_tokens = 0;
    int64_t cycle_start_us = 0;
    int64_t total_us = 0;
    int64_t window_us = 0;
    double last_ms_per_token = 0;

    void begin(const spine_mtp_config & cfg, bool available, int prompt_tokens) {
        *this = spine_mtp_policy{};
        config = cfg;
        enabled = available;
        reason = available ? "inherit" : "unavailable";
        if (!cfg.mode.empty() && available) {
            if (cfg.mode == "off") { enabled = false; reason = "requested_off"; }
            else if (cfg.mode == "on") { reason = "requested_on"; }
            else if (cfg.workload != "code" || cfg.expected_output_tokens < 256) {
                enabled = false; reason = "ineligible_workload_or_length";
            } else if (cfg.direct_ms_per_token <= 0 || cfg.calibration_id.empty() ||
                       cfg.calibrated_prompt_max < prompt_tokens) {
                enabled = false; reason = "missing_or_out_of_range_calibration";
            } else { reason = "eligible_code"; }
        }
        initially_enabled = enabled;
    }

    void begin_cycle(int64_t now) {
        if (!config.mode.empty() && enabled && cycle_start_us == 0) cycle_start_us = now;
    }

    bool finish_cycle(int64_t now, int tokens, int output_position) {
        if (cycle_start_us == 0) return false;
        const int64_t elapsed = std::max<int64_t>(1, now - cycle_start_us);
        cycle_start_us = 0;
        total_us += elapsed; window_us += elapsed;
        committed_tokens += tokens; window_tokens += tokens;
        ++cycles; ++window_cycles;
        if (config.test_fallback_after > 0 && cycles >= config.test_fallback_after) {
            enabled = false; reason = "test_forced_boundary"; fallback_at = output_position;
            return true;
        }
        if (window_cycles >= 12 && window_tokens >= 32) {
            last_ms_per_token = double(window_us) / 1000 / window_tokens;
            ++windows;
            const bool slower = config.direct_ms_per_token > 0 &&
                                last_ms_per_token > 1.05 * config.direct_ms_per_token;
            bad_windows = slower ? bad_windows + 1 : 0;
            window_us = 0; window_tokens = 0; window_cycles = 0;
            if (bad_windows >= 2) {
                enabled = false; reason = "measured_cost"; fallback_at = output_position;
                return true;
            }
        }
        return false;
    }
};
