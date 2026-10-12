#!/usr/bin/env python3
"""Generate a server-only patch for the tested a990751 source files."""
import argparse
import difflib
from pathlib import Path

HERE=Path(__file__).resolve().parent
def generate(original, output):
    files={name:(original/name).read_text() for name in
           ('server-context.cpp','server-schema.cpp','server-task.h','server-task.cpp')}
    changed=dict(files)
    def replace(name, old, new):
        if changed[name].count(old)!=1: raise ValueError('ambiguous/missing source anchor: '+name+' '+old[:60])
        changed[name]=changed[name].replace(old,new)
    replace('server-task.h','#pragma once','#pragma once\n#include "spine-mtp-policy.h"')
    replace('server-task.h','    struct common_params_sampling sampling;',
            '    spine_mtp_config spine_mtp;\n\n    struct common_params_sampling sampling;')
    replace('server-task.h','    json to_json() const;\n};\n\nstruct result_prompt_progress',
            '    json spine_mtp;\n    json to_json() const;\n};\n\nstruct result_prompt_progress')
    replace('server-schema.cpp','    // TODO: to keep things simple, we disable speculative parameter adjustments for now',r'''    add((new field_json("spine_mtp"))
        ->set_desc("Experimental per-request checkpoint-MTP policy")
        ->set_handler([&](field_eval_context & ctx, const json & data) {
            const auto & value = data.at("spine_mtp");
            if (!value.is_object()) throw std::runtime_error("spine_mtp must be an object");
            const std::set<std::string> keys = {"mode", "workload", "expected_output_tokens",
                "direct_ms_per_token", "calibration_id", "calibrated_prompt_max", "test_fallback_after"};
            for (auto it=value.begin(); it!=value.end(); ++it)
                if (!keys.count(it.key())) throw std::runtime_error("unknown spine_mtp setting");
            spine_mtp_config cfg;
            cfg.mode = value.value("mode", std::string("auto"));
            cfg.workload = value.value("workload", std::string("unknown"));
            if (cfg.mode!="on" && cfg.mode!="off" && cfg.mode!="auto")
                throw std::runtime_error("spine_mtp.mode must be on, off or auto");
            if (cfg.workload!="code" && cfg.workload!="prose" && cfg.workload!="qa" && cfg.workload!="unknown")
                throw std::runtime_error("invalid spine_mtp.workload");
            auto integer = [&](const char * key) {
                if (!value.contains(key)) return 0;
                if (!value.at(key).is_number_integer()) throw std::runtime_error("spine_mtp integer setting required");
                const int64_t n=value.at(key).get<int64_t>();
                if (n<0 || n>1000000) throw std::runtime_error("spine_mtp integer outside bounds");
                return int(n);
            };
            cfg.expected_output_tokens=integer("expected_output_tokens");
            cfg.calibrated_prompt_max=integer("calibrated_prompt_max");
            cfg.test_fallback_after=integer("test_fallback_after");
            cfg.direct_ms_per_token=value.value("direct_ms_per_token",0.0);
            cfg.calibration_id=value.value("calibration_id",std::string());
            if (!std::isfinite(cfg.direct_ms_per_token) || cfg.direct_ms_per_token<0 || cfg.direct_ms_per_token>60000)
                throw std::runtime_error("invalid spine_mtp direct calibration");
            const char * hooks=getenv("SPINE_MTP_TEST_HOOKS");
            if (cfg.test_fallback_after && (!hooks || std::string(hooks)!="1"))
                throw std::runtime_error("MTP test hook disabled");
            ctx.params.spine_mtp=std::move(cfg);
        }));

    // TODO: to keep things simple, we disable speculative parameter adjustments for now''')
    replace('server-schema.cpp','#include "json-schema-to-grammar.h"',
            '#include "json-schema-to-grammar.h"\n#include <cmath>\n#include <cstdlib>\n#include <set>')
    replace('server-task.cpp','    if (draft_n > 0) {',
            '    if (!spine_mtp.is_null()) base["spine_mtp"] = spine_mtp;\n\n    if (draft_n > 0) {')
    replace('server-context.cpp','    bool    spec_lowacc_disabled = false;',
            '    spine_mtp_policy mtp_policy;\n    bool    spec_lowacc_disabled = false;')
    replace('server-context.cpp','        if (can_speculate()) {\n            spec_draft.clear();\n            spec_i_batch.clear();\n            spec_ckpt.clear();\n        }',
            '        spec_draft.clear();\n        spec_i_batch.clear();\n        spec_ckpt.clear();\n        mtp_policy = spine_mtp_policy{};')
    replace('server-context.cpp','        if (!spec || spec_lowacc_disabled) {\n            return false;\n        }',
            '        if (!spec) return false;\n        // A scheduled draft/replay must be verified even if load or policy changes.\n        if (!spec_draft.empty()) return true;\n        if (spec_lowacc_disabled || !mtp_policy.enabled) return false;')
    replace('server-context.cpp','        return timings;',r'''        if (!mtp_policy.config.mode.empty()) {
            timings.spine_mtp = {
                {"requested",mtp_policy.config.mode}, {"initially_enabled",mtp_policy.initially_enabled},
                {"enabled_at_end",mtp_policy.enabled}, {"reason",mtp_policy.reason},
                {"calibration_id",mtp_policy.config.calibration_id}, {"cycles",mtp_policy.cycles},
                {"committed_tokens",mtp_policy.committed_tokens}, {"cycle_ms",mtp_policy.total_us/1000.0},
                {"windows",mtp_policy.windows}, {"last_ms_per_token",mtp_policy.last_ms_per_token},
                {"fallback_at",mtp_policy.fallback_at}
            };
        }
        return timings;''')
    replace('server-context.cpp','        // initialize samplers\n',r'''        slot.mtp_policy.begin(task.params.spine_mtp, slot.spec != nullptr, task.n_tokens());
        if (!task.params.spine_mtp.mode.empty()) {
            SLT_INF(slot, "MTP_POLICY start requested=%s enabled=%d reason=%s prompt=%d calibration=%s\n",
                task.params.spine_mtp.mode.c_str(), int(slot.mtp_policy.enabled), slot.mtp_policy.reason.c_str(),
                task.n_tokens(), task.params.spine_mtp.calibration_id.c_str());
        }
        // initialize samplers
''')
    replace('server-context.cpp','                    GGML_ASSERT(slot.can_speculate());\n',
            '                    GGML_ASSERT(slot.can_speculate());\n                    slot.mtp_policy.begin_cycle(ggml_time_us());\n')
    replace('server-context.cpp','            for (size_t i = 0; i < ids.size(); ++i) {\n                completion_token_output result;',r'''            auto finish_policy_cycle = [&](int tokens) {
                const int old_windows=slot.mtp_policy.windows;
                const bool switched=slot.mtp_policy.finish_cycle(ggml_time_us(),tokens,slot.n_decoded);
                if (switched || old_windows!=slot.mtp_policy.windows) {
                    SLT_INF(slot, "MTP_POLICY boundary cycles=%d tokens=%d ms_per_token=%.3f switched=%d output=%d reason=%s\n",
                        slot.mtp_policy.cycles, slot.mtp_policy.committed_tokens,
                        slot.mtp_policy.last_ms_per_token, int(switched), slot.n_decoded,slot.mtp_policy.reason.c_str());
                }
            };
            for (size_t i = 0; i < ids.size(); ++i) {
                completion_token_output result;''')
    # This occurrence is specific to the ids loop; EOS/length count only emitted tokens.
    replace('server-context.cpp','                if (!process_token(result, slot)) {\n                    slot.print_timings();',
            '                if (!process_token(result, slot)) {\n                    finish_policy_cycle(int(i)+1);\n                    slot.print_timings();')
    replace('server-context.cpp','            SLT_DBG(slot, "accepted %d/%d draft tokens, new n_tokens = %d\\n",',
            '            finish_policy_cycle(int(ids.size()));\n\n            SLT_DBG(slot, "accepted %d/%d draft tokens, new n_tokens = %d\\n",')
    chunks=[]
    for name in files:
        path='tools/server/'+name
        chunks.extend(difflib.unified_diff(files[name].splitlines(True),changed[name].splitlines(True),
                     fromfile='a/'+path,tofile='b/'+path))
    header=(HERE/'spine-mtp-policy.h').read_text()
    chunks.extend(difflib.unified_diff([],header.splitlines(True),fromfile='/dev/null',tofile='b/tools/server/spine-mtp-policy.h'))
    output.write_text(''.join(chunks))
    return changed

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('original',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();generate(args.original,args.output)
