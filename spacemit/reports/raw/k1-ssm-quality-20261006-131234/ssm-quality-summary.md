# Hybrid SSM complete-answer pilot

Six tasks/model, one pair/task, two answer orders from one cloud judge. Deterministic task checks establish correctness only for these tasks. Shared failures are not optimization regressions; identical answers alone do not establish usefulness. No general speedup claim.

```json
{
  "status": "scoring completed",
  "generation_exit": "0",
  "verified_artifacts": 114,
  "judge_model": "mimo-v2.6-flash",
  "models": {
    "2B": {
      "status": "complete-answer pilot completed",
      "eligible_pairs": 6,
      "judged_pairs": 6,
      "relative_quality_gate": {
        "pass": true,
        "control_mean_score": 3.1666666666666665,
        "hybrid_mean_score": 3.1666666666666665,
        "worst_pair_score_loss": 0.0,
        "deterministic_no_regression": true,
        "thresholds": {
          "mean_score_loss": 0.25,
          "worst_pair_score_loss": 0.5
        },
        "interpretation": "descriptive pilot; no statistical noninferiority or universal equivalence claim"
      },
      "useful_answers": {
        "control": 2,
        "hybrid": 2
      },
      "all_candidate_answers_useful": false,
      "paired_total_wall_s": {
        "control": 777.534,
        "hybrid": 754.8639999999999
      },
      "total_wall_reduction_pct": 2.9156281268729156,
      "state_identity": true,
      "comparisons": [
        {
          "case_id": "routes",
          "kind": "facts",
          "eligible": true,
          "absolute_checks": {
            "control": true,
            "hybrid": true
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "control": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "hybrid": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            }
          },
          "code_tests": {
            "control": {},
            "hybrid": {}
          },
          "output_tokens": {
            "control": 31,
            "hybrid": 31
          },
          "wall_s": {
            "control": 99.902,
            "hybrid": 93.188
          },
          "ttft_s": {
            "control": 91.85,
            "hybrid": 85.123
          },
          "prefill_ms": {
            "control": 91673.421,
            "hybrid": 84946.197
          },
          "decode_ms": {
            "control": 8049.233,
            "hybrid": 8061.957
          },
          "wall_reduction_pct": 6.720586174450959,
          "scores": {
            "control": 5.0,
            "hybrid": 5.0
          },
          "useful": {
            "control": true,
            "hybrid": true
          }
        },
        {
          "case_id": "trace",
          "kind": "facts",
          "eligible": true,
          "absolute_checks": {
            "control": false,
            "hybrid": false
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "control": {
              "facts": [
                true
              ],
              "citations": [
                false,
                false,
                false
              ]
            },
            "hybrid": {
              "facts": [
                true
              ],
              "citations": [
                false,
                false,
                false
              ]
            }
          },
          "code_tests": {
            "control": {},
            "hybrid": {}
          },
          "output_tokens": {
            "control": 8,
            "hybrid": 8
          },
          "wall_s": {
            "control": 95.155,
            "hybrid": 87.209
          },
          "ttft_s": {
            "control": 93.264,
            "hybrid": 85.318
          },
          "prefill_ms": {
            "control": 93088.071,
            "hybrid": 85139.007
          },
          "decode_ms": {
            "control": 1887.916,
            "hybrid": 1888.026
          },
          "wall_reduction_pct": 8.35058588618569,
          "scores": {
            "control": 5.0,
            "hybrid": 5.0
          },
          "useful": {
            "control": false,
            "hybrid": false
          }
        },
        {
          "case_id": "aggregation",
          "kind": "facts",
          "eligible": true,
          "absolute_checks": {
            "control": false,
            "hybrid": false
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "control": {
              "facts": [
                false
              ],
              "citations": [
                true,
                true,
                true
              ]
            },
            "hybrid": {
              "facts": [
                false
              ],
              "citations": [
                true,
                true,
                true
              ]
            }
          },
          "code_tests": {
            "control": {},
            "hybrid": {}
          },
          "output_tokens": {
            "control": 50,
            "hybrid": 50
          },
          "wall_s": {
            "control": 106.269,
            "hybrid": 98.673
          },
          "ttft_s": {
            "control": 93.115,
            "hybrid": 85.543
          },
          "prefill_ms": {
            "control": 92939.156,
            "hybrid": 85213.262
          },
          "decode_ms": {
            "control": 13151.261,
            "hybrid": 13126.585
          },
          "wall_reduction_pct": 7.14789825819383,
          "scores": {
            "control": 0.0,
            "hybrid": 0.0
          },
          "useful": {
            "control": false,
            "hybrid": false
          }
        },
        {
          "case_id": "free_windows",
          "kind": "code",
          "eligible": true,
          "absolute_checks": {
            "control": false,
            "hybrid": false
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "control": {
              "facts": [],
              "citations": []
            },
            "hybrid": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "control": {
              "pass": false,
              "reason": "IndexError: list index out of range",
              "exit": 1
            },
            "hybrid": {
              "pass": false,
              "reason": "IndexError: list index out of range",
              "exit": 1
            }
          },
          "output_tokens": {
            "control": 1086,
            "hybrid": 1086
          },
          "wall_s": {
            "control": 264.44,
            "hybrid": 264.541
          },
          "ttft_s": {
            "control": 7.441,
            "hybrid": 7.062
          },
          "prefill_ms": {
            "control": 7117.624,
            "hybrid": 6765.452
          },
          "decode_ms": {
            "control": 256996.621,
            "hybrid": 257476.889
          },
          "wall_reduction_pct": -0.03819391922552651,
          "scores": {
            "control": 1.0,
            "hybrid": 1.0
          },
          "useful": {
            "control": false,
            "hybrid": false
          }
        },
        {
          "case_id": "unicode_runs",
          "kind": "code",
          "eligible": true,
          "absolute_checks": {
            "control": true,
            "hybrid": true
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "control": {
              "facts": [],
              "citations": []
            },
            "hybrid": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "control": {
              "pass": true,
              "checks": 106,
              "restriction": "builtin-only functions, AST checks and resource limits"
            },
            "hybrid": {
              "pass": true,
              "checks": 106,
              "restriction": "builtin-only functions, AST checks and resource limits"
            }
          },
          "output_tokens": {
            "control": 508,
            "hybrid": 508
          },
          "wall_s": {
            "control": 123.743,
            "hybrid": 123.742
          },
          "ttft_s": {
            "control": 7.157,
            "hybrid": 6.795
          },
          "prefill_ms": {
            "control": 6837.842,
            "hybrid": 6500.596
          },
          "decode_ms": {
            "control": 116583.909,
            "hybrid": 116945.866
          },
          "wall_reduction_pct": 0.0008081265202797283,
          "scores": {
            "control": 5.0,
            "hybrid": 5.0
          },
          "useful": {
            "control": true,
            "hybrid": true
          }
        },
        {
          "case_id": "chinese_policy",
          "kind": "facts",
          "eligible": true,
          "absolute_checks": {
            "control": true,
            "hybrid": true
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "control": {
              "facts": [
                true,
                true,
                true,
                true,
                true,
                true,
                true,
                true
              ],
              "citations": []
            },
            "hybrid": {
              "facts": [
                true,
                true,
                true,
                true,
                true,
                true,
                true,
                true
              ],
              "citations": []
            }
          },
          "code_tests": {
            "control": {},
            "hybrid": {}
          },
          "output_tokens": {
            "control": 337,
            "hybrid": 337
          },
          "wall_s": {
            "control": 88.025,
            "hybrid": 87.511
          },
          "ttft_s": {
            "control": 10.658,
            "hybrid": 9.865
          },
          "prefill_ms": {
            "control": 10356.267,
            "hybrid": 9706.5
          },
          "decode_ms": {
            "control": 77365.045,
            "hybrid": 77644.176
          },
          "wall_reduction_pct": 0.5839250213007796,
          "scores": {
            "control": 3.0,
            "hybrid": 3.0
          },
          "useful": {
            "control": false,
            "hybrid": false
          }
        }
      ],
      "qualified": false
    },
    "4B": {
      "status": "complete-answer pilot completed",
      "eligible_pairs": 6,
      "judged_pairs": 6,
      "relative_quality_gate": {
        "pass": true,
        "control_mean_score": 4.5,
        "hybrid_mean_score": 4.5,
        "worst_pair_score_loss": 0.0,
        "deterministic_no_regression": true,
        "thresholds": {
          "mean_score_loss": 0.25,
          "worst_pair_score_loss": 0.5
        },
        "interpretation": "descriptive pilot; no statistical noninferiority or universal equivalence claim"
      },
      "useful_answers": {
        "control": 5,
        "hybrid": 5
      },
      "all_candidate_answers_useful": false,
      "paired_total_wall_s": {
        "control": 1767.333,
        "hybrid": 1729.7090000000003
      },
      "total_wall_reduction_pct": 2.128857436600784,
      "state_identity": true,
      "comparisons": [
        {
          "case_id": "routes",
          "kind": "facts",
          "eligible": true,
          "absolute_checks": {
            "hybrid": true,
            "control": true
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "hybrid": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "control": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            }
          },
          "code_tests": {
            "hybrid": {},
            "control": {}
          },
          "output_tokens": {
            "hybrid": 23,
            "control": 23
          },
          "wall_s": {
            "hybrid": 238.163,
            "control": 248.415
          },
          "ttft_s": {
            "hybrid": 223.981,
            "control": 234.426
          },
          "prefill_ms": {
            "hybrid": 223810.588,
            "control": 234252.286
          },
          "decode_ms": {
            "hybrid": 14179.525,
            "control": 13986.755
          },
          "wall_reduction_pct": 4.126964957832646,
          "scores": {
            "control": 5.0,
            "hybrid": 5.0
          },
          "useful": {
            "hybrid": true,
            "control": true
          }
        },
        {
          "case_id": "trace",
          "kind": "facts",
          "eligible": true,
          "absolute_checks": {
            "hybrid": true,
            "control": true
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "hybrid": {
              "facts": [
                true
              ],
              "citations": [
                true,
                true,
                true
              ]
            },
            "control": {
              "facts": [
                true
              ],
              "citations": [
                true,
                true,
                true
              ]
            }
          },
          "code_tests": {
            "hybrid": {},
            "control": {}
          },
          "output_tokens": {
            "hybrid": 64,
            "control": 64
          },
          "wall_s": {
            "hybrid": 265.601,
            "control": 277.022
          },
          "ttft_s": {
            "hybrid": 224.952,
            "control": 236.878
          },
          "prefill_ms": {
            "hybrid": 224779.568,
            "control": 236703.095
          },
          "decode_ms": {
            "hybrid": 40646.451,
            "control": 40141.432
          },
          "wall_reduction_pct": 4.122777252348186,
          "scores": {
            "control": 5.0,
            "hybrid": 5.0
          },
          "useful": {
            "hybrid": true,
            "control": true
          }
        },
        {
          "case_id": "aggregation",
          "kind": "facts",
          "eligible": true,
          "absolute_checks": {
            "hybrid": true,
            "control": true
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "hybrid": {
              "facts": [
                true
              ],
              "citations": [
                true,
                true,
                true
              ]
            },
            "control": {
              "facts": [
                true
              ],
              "citations": [
                true,
                true,
                true
              ]
            }
          },
          "code_tests": {
            "hybrid": {},
            "control": {}
          },
          "output_tokens": {
            "hybrid": 45,
            "control": 45
          },
          "wall_s": {
            "hybrid": 254.052,
            "control": 265.058
          },
          "ttft_s": {
            "hybrid": 225.694,
            "control": 237.082
          },
          "prefill_ms": {
            "hybrid": 225131.982,
            "control": 236910.437
          },
          "decode_ms": {
            "hybrid": 28355.087,
            "control": 27972.309
          },
          "wall_reduction_pct": 4.152298742162097,
          "scores": {
            "control": 5.0,
            "hybrid": 5.0
          },
          "useful": {
            "hybrid": true,
            "control": true
          }
        },
        {
          "case_id": "free_windows",
          "kind": "code",
          "eligible": true,
          "absolute_checks": {
            "hybrid": false,
            "control": false
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "hybrid": {
              "facts": [],
              "citations": []
            },
            "control": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "hybrid": {
              "pass": false,
              "reason": "ValueError: Interval (8, 8) has start >= end.",
              "exit": 1
            },
            "control": {
              "pass": false,
              "reason": "ValueError: Interval (8, 8) has start >= end.",
              "exit": 1
            }
          },
          "output_tokens": {
            "hybrid": 982,
            "control": 982
          },
          "wall_s": {
            "hybrid": 523.839,
            "control": 524.579
          },
          "ttft_s": {
            "hybrid": 18.251,
            "control": 18.74
          },
          "prefill_ms": {
            "hybrid": 17732.133,
            "control": 18155.786
          },
          "decode_ms": {
            "hybrid": 505585.969,
            "control": 505836.091
          },
          "wall_reduction_pct": 0.1410655020501972,
          "scores": {
            "control": 2.0,
            "hybrid": 2.0
          },
          "useful": {
            "hybrid": false,
            "control": false
          }
        },
        {
          "case_id": "unicode_runs",
          "kind": "code",
          "eligible": true,
          "absolute_checks": {
            "hybrid": true,
            "control": true
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "hybrid": {
              "facts": [],
              "citations": []
            },
            "control": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "hybrid": {
              "pass": true,
              "checks": 106,
              "restriction": "builtin-only functions, AST checks and resource limits"
            },
            "control": {
              "pass": true,
              "checks": 106,
              "restriction": "builtin-only functions, AST checks and resource limits"
            }
          },
          "output_tokens": {
            "hybrid": 521,
            "control": 521
          },
          "wall_s": {
            "hybrid": 274.132,
            "control": 276.194
          },
          "ttft_s": {
            "hybrid": 17.193,
            "control": 18.155
          },
          "prefill_ms": {
            "hybrid": 16676.734,
            "control": 17610.7
          },
          "decode_ms": {
            "hybrid": 256936.496,
            "control": 258037.739
          },
          "wall_reduction_pct": 0.7465766816078578,
          "scores": {
            "control": 5.0,
            "hybrid": 5.0
          },
          "useful": {
            "hybrid": true,
            "control": true
          }
        },
        {
          "case_id": "chinese_policy",
          "kind": "facts",
          "eligible": true,
          "absolute_checks": {
            "hybrid": true,
            "control": true
          },
          "deterministic_regression": false,
          "text_identical": true,
          "facts": {
            "hybrid": {
              "facts": [
                true,
                true,
                true,
                true,
                true,
                true,
                true,
                true
              ],
              "citations": []
            },
            "control": {
              "facts": [
                true,
                true,
                true,
                true,
                true,
                true,
                true,
                true
              ],
              "citations": []
            }
          },
          "code_tests": {
            "hybrid": {},
            "control": {}
          },
          "output_tokens": {
            "hybrid": 302,
            "control": 302
          },
          "wall_s": {
            "hybrid": 173.922,
            "control": 176.065
          },
          "ttft_s": {
            "hybrid": 25.173,
            "control": 26.79
          },
          "prefill_ms": {
            "hybrid": 25022.802,
            "control": 26266.03
          },
          "decode_ms": {
            "hybrid": 148747.295,
            "control": 149273.25
          },
          "wall_reduction_pct": 1.2171641155255153,
          "scores": {
            "control": 5.0,
            "hybrid": 5.0
          },
          "useful": {
            "hybrid": true,
            "control": true
          }
        }
      ],
      "qualified": false
    }
  },
  "operator_gate": true,
  "limitations": "Six tasks/model, one pair/task, two answer orders from one cloud judge. Deterministic task checks establish correctness only for these tasks. Shared failures are not optimization regressions; identical answers alone do not establish usefulness. No general speedup claim.",
  "candidate_qualified": false
}
```
