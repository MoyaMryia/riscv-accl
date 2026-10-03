# K1 staged validation

Status: completed

Engineering pilot, not a RULER/LongBench score. Fixed-length timing and naturally stopped quality are separate. A single 32k request is feasibility only. No default is changed.

```json
{
  "status": "completed",
  "stages": {
    "2B-state": {
      "status": "mismatch",
      "counts": {
        "pass": 18,
        "mismatch": 18,
        "unsupported": 7
      },
      "records": 43,
      "sequence_isolation": "deferred",
      "partial_fresh": "seeded with matching attention prefix; partial snapshots omit attention KV"
    },
    "2B-forced": {
      "status": "pass",
      "replays": {
        "1": {
          "positions": 512,
          "first_flip": null,
          "flips": 0,
          "max_top2_shift": 0.0
        },
        "3": {
          "positions": 512,
          "first_flip": 208,
          "flips": 2,
          "max_top2_shift": 0.2452697999999991
        }
      },
      "interpretation": "Same forced token history; M>1 differences do not by themselves rule out a state bug."
    },
    "2B-mtp512": {
      "status": "pass",
      "results": {
        "checkpoint": {
          "first_difference": null,
          "tokens_equal": true,
          "text_equal": true,
          "direct_decode_ms": 141780.497,
          "mtp_decode_ms": 93856.943
        },
        "rs": {
          "first_difference": null,
          "tokens_equal": true,
          "text_equal": true,
          "direct_decode_ms": 141780.497,
          "mtp_decode_ms": 94995.835
        }
      },
      "output_tokens": 512,
      "speed_claim": "diagnostic only; identity gates deployment"
    },
    "4B-state": {
      "status": "mismatch",
      "counts": {
        "pass": 18,
        "mismatch": 18,
        "unsupported": 7
      },
      "records": 43,
      "sequence_isolation": "deferred",
      "partial_fresh": "seeded with matching attention prefix; partial snapshots omit attention KV"
    },
    "4B-forced": {
      "status": "pass",
      "replays": {
        "1": {
          "positions": 512,
          "first_flip": null,
          "flips": 0,
          "max_top2_shift": 0.0
        },
        "3": {
          "positions": 512,
          "first_flip": null,
          "flips": 0,
          "max_top2_shift": 0.5282286999999997
        }
      },
      "interpretation": "Same forced token history; M>1 differences do not by themselves rule out a state bug."
    },
    "4B-mtp512": {
      "status": "pass",
      "results": {
        "checkpoint": {
          "first_difference": null,
          "tokens_equal": true,
          "text_equal": true,
          "direct_decode_ms": 348637.624,
          "mtp_decode_ms": 202655.782
        },
        "rs": {
          "first_difference": null,
          "tokens_equal": true,
          "text_equal": true,
          "direct_decode_ms": 348637.624,
          "mtp_decode_ms": 186052.436
        }
      },
      "output_tokens": 512,
      "speed_claim": "diagnostic only; identity gates deployment"
    },
    "2B-8k-routing": {
      "status": "pass",
      "requests": 4,
      "input_tokens": 8192,
      "output_tokens": 64,
      "outputs_equal": true,
      "uncached_verified": true,
      "comparisons": {
        "prompt": {
          "reduction_pct": 4.425193983197973,
          "control_range_pct": 0.7714320498094449,
          "advance": true,
          "clear_regression": false,
          "base_ms": [
            453026.399,
            456534.722
          ],
          "candidate_ms": [
            436261.966,
            433049.311
          ]
        },
        "predicted": {
          "reduction_pct": 9.492743590635156,
          "control_range_pct": 0.41597515189173534,
          "advance": true,
          "clear_regression": false,
          "base_ms": [
            26719.468,
            26830.846
          ],
          "candidate_ms": [
            24254.329,
            24212.591
          ]
        }
      },
      "eligible": true
    },
    "2B-answers": {
      "status": "quality gate not cleared",
      "comparisons": {
        "routes": {
          "complete_cold_pair": true,
          "text_identical": true,
          "baseline_facts": [
            true,
            true,
            true
          ],
          "candidate_facts": [
            true,
            true,
            true
          ],
          "baseline_citations": true,
          "candidate_citations": true,
          "regression": false,
          "candidate_useful": true
        },
        "trace": {
          "complete_cold_pair": true,
          "text_identical": true,
          "baseline_facts": [
            true
          ],
          "candidate_facts": [
            true
          ],
          "baseline_citations": false,
          "candidate_citations": false,
          "regression": false,
          "candidate_useful": false
        },
        "aggregation": {
          "complete_cold_pair": true,
          "text_identical": true,
          "baseline_facts": [
            true
          ],
          "candidate_facts": [
            true
          ],
          "baseline_citations": true,
          "candidate_citations": true,
          "regression": false,
          "candidate_useful": true
        }
      },
      "requests": 6,
      "input": "full ~4k fixture, all source blocks preserved",
      "timing_claim": "none; one request per task and arm"
    },
    "4B-8k-routing": {
      "status": "pass",
      "requests": 4,
      "input_tokens": 8192,
      "output_tokens": 64,
      "outputs_equal": true,
      "uncached_verified": true,
      "comparisons": {
        "prompt": {
          "reduction_pct": 5.786678953990576,
          "control_range_pct": 1.842061542468561,
          "advance": true,
          "clear_regression": false,
          "base_ms": [
            1226376.266,
            1203991.828
          ],
          "candidate_ms": [
            1138724.684,
            1151005.811
          ]
        },
        "predicted": {
          "reduction_pct": 15.056717130469345,
          "control_range_pct": 0.028308183907311667,
          "advance": true,
          "clear_regression": false,
          "base_ms": [
            84542.29,
            84518.361
          ],
          "candidate_ms": [
            72250.765,
            71354.902
          ]
        }
      },
      "eligible": true
    },
    "4B-answers": {
      "status": "pass",
      "comparisons": {
        "routes": {
          "complete_cold_pair": true,
          "text_identical": true,
          "baseline_facts": [
            true,
            true,
            true
          ],
          "candidate_facts": [
            true,
            true,
            true
          ],
          "baseline_citations": true,
          "candidate_citations": true,
          "regression": false,
          "candidate_useful": true
        },
        "trace": {
          "complete_cold_pair": true,
          "text_identical": true,
          "baseline_facts": [
            true
          ],
          "candidate_facts": [
            true
          ],
          "baseline_citations": true,
          "candidate_citations": true,
          "regression": false,
          "candidate_useful": true
        },
        "aggregation": {
          "complete_cold_pair": true,
          "text_identical": true,
          "baseline_facts": [
            true
          ],
          "candidate_facts": [
            true
          ],
          "baseline_citations": true,
          "candidate_citations": true,
          "regression": false,
          "candidate_useful": true
        }
      },
      "requests": 6,
      "input": "full ~4k fixture, all source blocks preserved",
      "timing_claim": "none; one request per task and arm"
    },
    "4B-32k-feasibility": {
      "status": "skipped",
      "reason": "combined routing/quality prerequisite not cleared"
    }
  },
  "protocol": {
    "routing_order": [
      0,
      3,
      3,
      0
    ],
    "routing_tokens": 8192,
    "routing_output": 64,
    "quality_document_budget": 4096,
    "quality_cases": [
      "routes",
      "trace",
      "aggregation"
    ],
    "quality_output_cap": 512,
    "mtp_output": 512,
    "teacher_forced_k": [
      1,
      3
    ],
    "feasibility_input_tokens": 32768,
    "feasibility_output_tokens": 64,
    "feasibility_context": 33792,
    "feasibility_budget_s": 18000,
    "minimum_available_kib": 2097152,
    "overall_budget_s": 43200,
    "64k": "not scheduled; conditional on a measured need and resources"
  },
  "limitations": "Engineering pilot, not a RULER/LongBench score. Fixed-length timing and naturally stopped quality are separate. A single 32k request is feasibility only. No default is changed.",
  "elapsed_s": 14983.047091124055,
  "combined_routing_eligible": false,
  "mtp_identity_cleared": false
}
```
