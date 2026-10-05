# Adaptive MTP screen

```json
{
  "status": "completed",
  "generation_exit": "0",
  "screen": "infrastructure",
  "verified_artifacts": 47,
  "models": {
    "2B": {
      "relative_quality_gate": {
        "pass": false,
        "reason": "incomplete eligible/judged coverage"
      },
      "timing_gate": false,
      "absolute_checks": false,
      "infrastructure_timing_available": true,
      "code_timing_metric": "median_decode_throughput_gain_pct",
      "quality_pairs": 6,
      "generation": {
        "state_gate": "pass",
        "calibration_quality": {
          "unicode_offsets": {
            "complete": false,
            "code_test": {
              "pass": false,
              "reason": "SyntaxError: unterminated string literal (detected at line 116) (<unknown>, line 116)"
            }
          },
          "chinese_policy": {
            "complete": true,
            "code_test": null
          },
          "routes": {
            "complete": true,
            "code_test": null
          }
        },
        "calibration_gate": "timing metadata pass",
        "timing_requests": 27,
        "status": "generation completed"
      },
      "qualified": false,
      "pairs": 9,
      "timing": {
        "unicode_offsets": {
          "loaded_off": {
            "paired_time_reduction_pct": [
              -4.950191987865149,
              -5.0904210565757335,
              -6.238932910362571
            ],
            "median_time_reduction_pct": -5.0904210565757335,
            "paired_decode_throughput_gain_pct": [
              -4.741332216637528,
              -4.892951582964756,
              -5.948183930247863
            ],
            "median_decode_throughput_gain_pct": -4.892951582964756,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          },
          "adaptive": {
            "paired_time_reduction_pct": [
              32.425032904917536,
              31.0126000183942,
              32.74901378985007
            ],
            "median_time_reduction_pct": 32.425032904917536,
            "paired_decode_throughput_gain_pct": [
              50.74424143051175,
              47.49755977210421,
              51.37660684925176
            ],
            "median_decode_throughput_gain_pct": 50.74424143051175,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          }
        },
        "chinese_policy": {
          "loaded_off": {
            "paired_time_reduction_pct": [
              -4.587968505163165,
              -4.7054811205846425,
              -5.767425486974909
            ],
            "median_time_reduction_pct": -4.7054811205846425,
            "paired_decode_throughput_gain_pct": [
              -4.559929268283758,
              -4.604485768870403,
              -5.7521392788110415
            ],
            "median_decode_throughput_gain_pct": -4.604485768870403,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          },
          "adaptive": {
            "paired_time_reduction_pct": [
              -5.7539392877651085,
              -6.6913520097442225,
              -5.771336931862625
            ],
            "median_time_reduction_pct": -5.771336931862625,
            "paired_decode_throughput_gain_pct": [
              -6.095067640330576,
              -6.606787601699782,
              -6.10521191493234
            ],
            "median_decode_throughput_gain_pct": -6.10521191493234,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          }
        },
        "routes": {
          "loaded_off": {
            "paired_time_reduction_pct": [
              -4.503235422422569,
              -5.07135264291696,
              -4.518938460274424
            ],
            "median_time_reduction_pct": -4.518938460274424,
            "paired_decode_throughput_gain_pct": [
              -5.8236461417327305,
              -5.824112831787986,
              -7.135144608488453
            ],
            "median_decode_throughput_gain_pct": -5.824112831787986,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          },
          "adaptive": {
            "paired_time_reduction_pct": [
              -4.8267776646793825,
              -4.75997855187531,
              -4.382913848035863
            ],
            "median_time_reduction_pct": -4.75997855187531,
            "paired_decode_throughput_gain_pct": [
              -6.475514524752413,
              -7.244567831349058,
              -7.167970431693449
            ],
            "median_decode_throughput_gain_pct": -7.167970431693449,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          }
        }
      },
      "comparisons": [
        {
          "repeat": 0,
          "case_id": "chinese_policy",
          "deterministic_regression": false,
          "quality_eligible": {
            "direct": true,
            "loaded_off": true,
            "adaptive": true
          },
          "finish_reason": {
            "direct": "stop",
            "loaded_off": "stop",
            "adaptive": "stop"
          },
          "wall_s": {
            "direct": 102.747,
            "loaded_off": 107.461,
            "adaptive": 108.659
          },
          "ttft_s": {
            "direct": 11.711,
            "loaded_off": 12.075,
            "adaptive": 11.714
          },
          "output_tokens": {
            "direct": 337,
            "loaded_off": 337,
            "adaptive": 337
          },
          "decode_tps": {
            "direct": 3.7019095855708923,
            "loaded_off": 3.533105126893043,
            "adaptive": 3.4762756923464653
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "2B-chinese_policy-1e7aa55c8ae3",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "direct": {
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
            "loaded_off": {
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
            "adaptive": {
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
            "direct": null,
            "loaded_off": null,
            "adaptive": null
          }
        },
        {
          "repeat": 0,
          "case_id": "routes",
          "deterministic_regression": false,
          "quality_eligible": {
            "direct": true,
            "loaded_off": true,
            "adaptive": true
          },
          "finish_reason": {
            "direct": "stop",
            "loaded_off": "stop",
            "adaptive": "stop"
          },
          "wall_s": {
            "direct": 110.032,
            "loaded_off": 114.987,
            "adaptive": 115.343
          },
          "ttft_s": {
            "direct": 100.63,
            "loaded_off": 105.002,
            "adaptive": 105.289
          },
          "output_tokens": {
            "direct": 31,
            "loaded_off": 31,
            "adaptive": 31
          },
          "decode_tps": {
            "direct": 3.2978614644994253,
            "loaded_off": 3.105805682562414,
            "adaptive": 3.0843079663595523
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "2B-routes-636195530a30",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "direct": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "loaded_off": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "adaptive": {
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
            "direct": null,
            "loaded_off": null,
            "adaptive": null
          }
        },
        {
          "repeat": 0,
          "case_id": "unicode_offsets",
          "deterministic_regression": false,
          "quality_eligible": {
            "direct": false,
            "loaded_off": false,
            "adaptive": false
          },
          "finish_reason": {
            "direct": "length",
            "loaded_off": "length",
            "adaptive": "length"
          },
          "wall_s": {
            "direct": 294.029,
            "loaded_off": 308.584,
            "adaptive": 198.69
          },
          "ttft_s": {
            "direct": 9.325,
            "loaded_off": 9.709,
            "adaptive": 9.822
          },
          "output_tokens": {
            "direct": 1024,
            "loaded_off": 1024,
            "adaptive": 1024
          },
          "decode_tps": {
            "direct": 3.596747329322028,
            "loaded_off": 3.4262135894458328,
            "adaptive": 5.421889477758682
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": true,
            "enabled_at_end": true,
            "reason": "eligible_code",
            "calibration_id": "2B-unicode_offsets-2002d92e5eb9",
            "cycles": 277,
            "committed_tokens": 1023,
            "cycle_ms": 188846.546,
            "windows": 23,
            "last_ms_per_token": 148.23270833333333,
            "fallback_at": -1
          },
          "facts": {
            "direct": {
              "facts": [],
              "citations": []
            },
            "loaded_off": {
              "facts": [],
              "citations": []
            },
            "adaptive": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "direct": {
              "pass": false,
              "reason": "SyntaxError: unterminated string literal (detected at line 116) (<unknown>, line 116)"
            },
            "loaded_off": {
              "pass": false,
              "reason": "SyntaxError: unterminated string literal (detected at line 116) (<unknown>, line 116)"
            },
            "adaptive": {
              "pass": false,
              "reason": "ValueError: Malformed spans: gaps or overlaps detected",
              "exit": 1
            }
          }
        },
        {
          "repeat": 1,
          "case_id": "chinese_policy",
          "deterministic_regression": false,
          "quality_eligible": {
            "adaptive": true,
            "direct": true,
            "loaded_off": true
          },
          "finish_reason": {
            "adaptive": "stop",
            "direct": "stop",
            "loaded_off": "stop"
          },
          "wall_s": {
            "adaptive": 109.492,
            "direct": 102.625,
            "loaded_off": 107.454
          },
          "ttft_s": {
            "adaptive": 12.098,
            "direct": 11.667,
            "loaded_off": 12.105
          },
          "output_tokens": {
            "adaptive": 337,
            "direct": 337,
            "loaded_off": 337
          },
          "decode_tps": {
            "adaptive": 3.4602719554024546,
            "direct": 3.7050572161981146,
            "loaded_off": 3.5344583839497665
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "2B-chinese_policy-1e7aa55c8ae3",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "adaptive": {
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
            "direct": {
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
            "loaded_off": {
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
            "adaptive": null,
            "direct": null,
            "loaded_off": null
          }
        },
        {
          "repeat": 1,
          "case_id": "routes",
          "deterministic_regression": false,
          "quality_eligible": {
            "adaptive": true,
            "direct": true,
            "loaded_off": true
          },
          "finish_reason": {
            "adaptive": "stop",
            "direct": "stop",
            "loaded_off": "stop"
          },
          "wall_s": {
            "adaptive": 111.363,
            "direct": 106.303,
            "loaded_off": 111.694
          },
          "ttft_s": {
            "adaptive": 101.279,
            "direct": 96.949,
            "loaded_off": 101.761
          },
          "output_tokens": {
            "adaptive": 31,
            "direct": 31,
            "loaded_off": 31
          },
          "decode_tps": {
            "adaptive": 3.0748639099949644,
            "direct": 3.3150229998434453,
            "loaded_off": 3.12195231993284
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "2B-routes-636195530a30",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "adaptive": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "direct": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "loaded_off": {
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
            "adaptive": null,
            "direct": null,
            "loaded_off": null
          }
        },
        {
          "repeat": 1,
          "case_id": "unicode_offsets",
          "deterministic_regression": false,
          "quality_eligible": {
            "adaptive": false,
            "direct": false,
            "loaded_off": false
          },
          "finish_reason": {
            "adaptive": "length",
            "direct": "length",
            "loaded_off": "length"
          },
          "wall_s": {
            "adaptive": 202.527,
            "direct": 293.571,
            "loaded_off": 308.515
          },
          "ttft_s": {
            "adaptive": 10.098,
            "direct": 9.746,
            "loaded_off": 10.087
          },
          "output_tokens": {
            "adaptive": 1024,
            "direct": 1024,
            "loaded_off": 1024
          },
          "decode_tps": {
            "adaptive": 5.321535184948682,
            "direct": 3.607880152845165,
            "loaded_off": 3.4313483237950564
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": true,
            "enabled_at_end": true,
            "reason": "eligible_code",
            "calibration_id": "2B-unicode_offsets-2002d92e5eb9",
            "cycles": 276,
            "committed_tokens": 1022,
            "cycle_ms": 192087.836,
            "windows": 23,
            "last_ms_per_token": 157.93735416666667,
            "fallback_at": -1
          },
          "facts": {
            "adaptive": {
              "facts": [],
              "citations": []
            },
            "direct": {
              "facts": [],
              "citations": []
            },
            "loaded_off": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "adaptive": {
              "pass": false,
              "reason": "ValueError: Malformed spans: gaps or overlaps detected",
              "exit": 1
            },
            "direct": {
              "pass": false,
              "reason": "SyntaxError: unterminated string literal (detected at line 116) (<unknown>, line 116)"
            },
            "loaded_off": {
              "pass": false,
              "reason": "SyntaxError: unterminated string literal (detected at line 116) (<unknown>, line 116)"
            }
          }
        },
        {
          "repeat": 2,
          "case_id": "chinese_policy",
          "deterministic_regression": false,
          "quality_eligible": {
            "loaded_off": true,
            "adaptive": true,
            "direct": true
          },
          "finish_reason": {
            "loaded_off": "stop",
            "adaptive": "stop",
            "direct": "stop"
          },
          "wall_s": {
            "loaded_off": 108.162,
            "adaptive": 108.166,
            "direct": 102.264
          },
          "ttft_s": {
            "loaded_off": 12.003,
            "adaptive": 11.645,
            "direct": 11.636
          },
          "output_tokens": {
            "loaded_off": 337,
            "adaptive": 337,
            "direct": 337
          },
          "decode_tps": {
            "loaded_off": 3.5046873060787362,
            "adaptive": 3.491557998140398,
            "direct": 3.7185855246588178
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "2B-chinese_policy-1e7aa55c8ae3",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "loaded_off": {
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
            "adaptive": {
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
            "direct": {
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
            "loaded_off": null,
            "adaptive": null,
            "direct": null
          }
        },
        {
          "repeat": 2,
          "case_id": "routes",
          "deterministic_regression": false,
          "quality_eligible": {
            "loaded_off": true,
            "adaptive": true,
            "direct": true
          },
          "finish_reason": {
            "loaded_off": "stop",
            "adaptive": "stop",
            "direct": "stop"
          },
          "wall_s": {
            "loaded_off": 114.489,
            "adaptive": 114.34,
            "direct": 109.539
          },
          "ttft_s": {
            "loaded_off": 104.455,
            "adaptive": 104.302,
            "direct": 100.221
          },
          "output_tokens": {
            "loaded_off": 31,
            "adaptive": 31,
            "direct": 31
          },
          "decode_tps": {
            "loaded_off": 3.0904255525955038,
            "adaptive": 3.0893331504979606,
            "direct": 3.3278741883207505
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "2B-routes-636195530a30",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "loaded_off": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "adaptive": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "direct": {
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
            "loaded_off": null,
            "adaptive": null,
            "direct": null
          }
        },
        {
          "repeat": 2,
          "case_id": "unicode_offsets",
          "deterministic_regression": false,
          "quality_eligible": {
            "loaded_off": false,
            "adaptive": false,
            "direct": false
          },
          "finish_reason": {
            "loaded_off": "length",
            "adaptive": "length",
            "direct": "length"
          },
          "wall_s": {
            "loaded_off": 310.785,
            "adaptive": 196.732,
            "direct": 292.534
          },
          "ttft_s": {
            "loaded_off": 9.672,
            "adaptive": 9.646,
            "direct": 9.331
          },
          "output_tokens": {
            "loaded_off": 1024,
            "adaptive": 1024,
            "direct": 1024
          },
          "decode_tps": {
            "loaded_off": 3.40073415739764,
            "adaptive": 5.473489179213897,
            "direct": 3.615809135334012
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": true,
            "enabled_at_end": true,
            "reason": "eligible_code",
            "calibration_id": "2B-unicode_offsets-2002d92e5eb9",
            "cycles": 277,
            "committed_tokens": 1023,
            "cycle_ms": 187067.579,
            "windows": 23,
            "last_ms_per_token": 146.93177083333333,
            "fallback_at": -1
          },
          "facts": {
            "loaded_off": {
              "facts": [],
              "citations": []
            },
            "adaptive": {
              "facts": [],
              "citations": []
            },
            "direct": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "loaded_off": {
              "pass": false,
              "reason": "SyntaxError: unterminated string literal (detected at line 116) (<unknown>, line 116)"
            },
            "adaptive": {
              "pass": false,
              "reason": "ValueError: Malformed spans: gaps or overlaps detected",
              "exit": 1
            },
            "direct": {
              "pass": false,
              "reason": "SyntaxError: unterminated string literal (detected at line 116) (<unknown>, line 116)"
            }
          }
        }
      ],
      "timing_interpretation": "Bounded decode throughput is infrastructure evidence. Wall-time changes can reflect different output lengths; capped answers do not establish useful-answer speedup."
    },
    "4B": {
      "relative_quality_gate": {
        "pass": true,
        "direct_mean_score": 5.0,
        "mtp_mean_score": 4.888888888888889,
        "worst_pair_score_loss": 0.5,
        "deterministic_no_regression": true,
        "thresholds": {
          "mean_score_loss": 0.25,
          "worst_pair_score_loss": 0.5
        },
        "interpretation": "descriptive pilot; no statistical noninferiority or universal equivalence claim"
      },
      "timing_gate": false,
      "absolute_checks": false,
      "infrastructure_timing_available": true,
      "code_timing_metric": "median_decode_throughput_gain_pct",
      "quality_pairs": 9,
      "generation": {
        "state_gate": "pass",
        "calibration_quality": {
          "unicode_offsets": {
            "complete": true,
            "code_test": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            }
          },
          "chinese_policy": {
            "complete": true,
            "code_test": null
          },
          "routes": {
            "complete": true,
            "code_test": null
          }
        },
        "calibration_gate": "timing metadata pass",
        "timing_requests": 27,
        "status": "generation completed"
      },
      "qualified": false,
      "pairs": 9,
      "timing": {
        "unicode_offsets": {
          "loaded_off": {
            "paired_time_reduction_pct": [
              -2.806037284978835,
              -4.3479806914453745,
              -2.814005861702018
            ],
            "median_time_reduction_pct": -2.814005861702018,
            "paired_decode_throughput_gain_pct": [
              -2.7867726996031794,
              -4.229565481459597,
              -2.7187202026301205
            ],
            "median_decode_throughput_gain_pct": -2.7867726996031794,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          },
          "adaptive": {
            "paired_time_reduction_pct": [
              37.466308224834385,
              37.22212838588662,
              37.14703397170969
            ],
            "median_time_reduction_pct": 37.22212838588662,
            "paired_decode_throughput_gain_pct": [
              53.69209025551176,
              53.354320842254886,
              53.01659698598024
            ],
            "median_decode_throughput_gain_pct": 53.354320842254886,
            "same_output_token_count": [
              false,
              false,
              false
            ]
          }
        },
        "chinese_policy": {
          "loaded_off": {
            "paired_time_reduction_pct": [
              -2.6225550594554337,
              -4.031007096635109,
              -2.6405537308794136
            ],
            "median_time_reduction_pct": -2.6405537308794136,
            "paired_decode_throughput_gain_pct": [
              -2.6123749395062346,
              -4.045517890015605,
              -2.5242490016172847
            ],
            "median_decode_throughput_gain_pct": -2.6123749395062346,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          },
          "adaptive": {
            "paired_time_reduction_pct": [
              -2.973816216487135,
              -3.30824080374994,
              -2.903475098070518
            ],
            "median_time_reduction_pct": -2.973816216487135,
            "paired_decode_throughput_gain_pct": [
              -3.335427215712783,
              -3.3657884798473203,
              -3.2194452416018815
            ],
            "median_decode_throughput_gain_pct": -3.335427215712783,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          }
        },
        "routes": {
          "loaded_off": {
            "paired_time_reduction_pct": [
              -2.4207089218985622,
              -3.9660014836521595,
              -4.219653386897981
            ],
            "median_time_reduction_pct": -3.9660014836521595,
            "paired_decode_throughput_gain_pct": [
              -4.154239669170945,
              -5.44215930257026,
              -4.163360526643367
            ],
            "median_decode_throughput_gain_pct": -4.163360526643367,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          },
          "adaptive": {
            "paired_time_reduction_pct": [
              -2.75544981030158,
              -3.624613862920878,
              -4.3382334446069315
            ],
            "median_time_reduction_pct": -3.624613862920878,
            "paired_decode_throughput_gain_pct": [
              -4.5960460644066,
              -4.985044197894595,
              -4.707737468889817
            ],
            "median_decode_throughput_gain_pct": -4.707737468889817,
            "same_output_token_count": [
              true,
              true,
              true
            ]
          }
        }
      },
      "comparisons": [
        {
          "repeat": 0,
          "case_id": "chinese_policy",
          "deterministic_regression": false,
          "quality_eligible": {
            "direct": true,
            "loaded_off": true,
            "adaptive": true
          },
          "finish_reason": {
            "direct": "stop",
            "loaded_off": "stop",
            "adaptive": "stop"
          },
          "wall_s": {
            "direct": 239.423,
            "loaded_off": 245.702,
            "adaptive": 246.543
          },
          "ttft_s": {
            "direct": 29.576,
            "loaded_off": 30.226,
            "adaptive": 29.454
          },
          "output_tokens": {
            "direct": 302,
            "loaded_off": 302,
            "adaptive": 302
          },
          "decode_tps": {
            "direct": 1.4391532487388252,
            "loaded_off": 1.4015571699276823,
            "adaptive": 1.3911513396045758
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "4B-chinese_policy-71ff50cb0f11",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "direct": {
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
            "loaded_off": {
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
            "adaptive": {
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
            "direct": null,
            "loaded_off": null,
            "adaptive": null
          }
        },
        {
          "repeat": 0,
          "case_id": "routes",
          "deterministic_regression": false,
          "quality_eligible": {
            "direct": true,
            "loaded_off": true,
            "adaptive": true
          },
          "finish_reason": {
            "direct": "stop",
            "loaded_off": "stop",
            "adaptive": "stop"
          },
          "wall_s": {
            "direct": 279.918,
            "loaded_off": 286.694,
            "adaptive": 287.631
          },
          "ttft_s": {
            "direct": 261.357,
            "loaded_off": 267.328,
            "adaptive": 268.176
          },
          "output_tokens": {
            "direct": 23,
            "loaded_off": 23,
            "adaptive": 23
          },
          "decode_tps": {
            "direct": 1.2393327130922138,
            "loaded_off": 1.1878478618919246,
            "adaptive": 1.1823724107072355
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "4B-routes-35280c38a065",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "direct": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "loaded_off": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "adaptive": {
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
            "direct": null,
            "loaded_off": null,
            "adaptive": null
          }
        },
        {
          "repeat": 0,
          "case_id": "unicode_offsets",
          "deterministic_regression": false,
          "quality_eligible": {
            "direct": true,
            "loaded_off": true,
            "adaptive": true
          },
          "finish_reason": {
            "direct": "stop",
            "loaded_off": "stop",
            "adaptive": "stop"
          },
          "wall_s": {
            "direct": 569.13,
            "loaded_off": 585.1,
            "adaptive": 355.898
          },
          "ttft_s": {
            "direct": 23.777,
            "loaded_off": 24.113,
            "adaptive": 24.192
          },
          "output_tokens": {
            "direct": 767,
            "loaded_off": 767,
            "adaptive": 717
          },
          "decode_tps": {
            "direct": 1.4064334715499256,
            "loaded_off": 1.367239367526691,
            "adaptive": 2.161577000478239
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": true,
            "enabled_at_end": true,
            "reason": "eligible_code",
            "calibration_id": "4B-unicode_offsets-5027e59dda37",
            "cycles": 195,
            "committed_tokens": 716,
            "cycle_ms": 331691.26,
            "windows": 16,
            "last_ms_per_token": 598.8214390243902,
            "fallback_at": -1
          },
          "facts": {
            "direct": {
              "facts": [],
              "citations": []
            },
            "loaded_off": {
              "facts": [],
              "citations": []
            },
            "adaptive": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "direct": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            },
            "loaded_off": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            },
            "adaptive": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            }
          }
        },
        {
          "repeat": 1,
          "case_id": "chinese_policy",
          "deterministic_regression": false,
          "quality_eligible": {
            "adaptive": true,
            "direct": true,
            "loaded_off": true
          },
          "finish_reason": {
            "adaptive": "stop",
            "direct": "stop",
            "loaded_off": "stop"
          },
          "wall_s": {
            "adaptive": 244.418,
            "direct": 236.591,
            "loaded_off": 246.128
          },
          "ttft_s": {
            "adaptive": 30.28,
            "direct": 29.661,
            "loaded_off": 30.474
          },
          "output_tokens": {
            "adaptive": 302,
            "direct": 302,
            "loaded_off": 302
          },
          "decode_tps": {
            "adaptive": 1.4103217714500718,
            "direct": 1.4594435544765165,
            "loaded_off": 1.4004015043854894
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "4B-chinese_policy-71ff50cb0f11",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "adaptive": {
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
            "direct": {
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
            "loaded_off": {
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
            "adaptive": null,
            "direct": null,
            "loaded_off": null
          }
        },
        {
          "repeat": 1,
          "case_id": "routes",
          "deterministic_regression": false,
          "quality_eligible": {
            "adaptive": true,
            "direct": true,
            "loaded_off": true
          },
          "finish_reason": {
            "adaptive": "stop",
            "direct": "stop",
            "loaded_off": "stop"
          },
          "wall_s": {
            "adaptive": 280.774,
            "direct": 270.953,
            "loaded_off": 281.699
          },
          "ttft_s": {
            "adaptive": 261.503,
            "direct": 252.643,
            "loaded_off": 262.335
          },
          "output_tokens": {
            "adaptive": 23,
            "direct": 23,
            "loaded_off": 23
          },
          "decode_tps": {
            "adaptive": 1.1937030813057636,
            "direct": 1.2563317755911778,
            "loaded_off": 1.1879601989946964
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "4B-routes-35280c38a065",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "adaptive": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "direct": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "loaded_off": {
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
            "adaptive": null,
            "direct": null,
            "loaded_off": null
          }
        },
        {
          "repeat": 1,
          "case_id": "unicode_offsets",
          "deterministic_regression": false,
          "quality_eligible": {
            "adaptive": true,
            "direct": true,
            "loaded_off": true
          },
          "finish_reason": {
            "adaptive": "stop",
            "direct": "stop",
            "loaded_off": "stop"
          },
          "wall_s": {
            "adaptive": 353.091,
            "direct": 562.445,
            "loaded_off": 586.9
          },
          "ttft_s": {
            "adaptive": 25.279,
            "direct": 24.678,
            "loaded_off": 25.383
          },
          "output_tokens": {
            "adaptive": 717,
            "direct": 767,
            "loaded_off": 767
          },
          "decode_tps": {
            "adaptive": 2.1872513841419425,
            "direct": 1.4262730727957895,
            "loaded_off": 1.3659479192374657
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": true,
            "enabled_at_end": true,
            "reason": "eligible_code",
            "calibration_id": "4B-unicode_offsets-5027e59dda37",
            "cycles": 193,
            "committed_tokens": 716,
            "cycle_ms": 327797.243,
            "windows": 16,
            "last_ms_per_token": 584.1512558139535,
            "fallback_at": -1
          },
          "facts": {
            "adaptive": {
              "facts": [],
              "citations": []
            },
            "direct": {
              "facts": [],
              "citations": []
            },
            "loaded_off": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "adaptive": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            },
            "direct": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            },
            "loaded_off": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            }
          }
        },
        {
          "repeat": 2,
          "case_id": "chinese_policy",
          "deterministic_regression": false,
          "quality_eligible": {
            "loaded_off": true,
            "adaptive": true,
            "direct": true
          },
          "finish_reason": {
            "loaded_off": "stop",
            "adaptive": "stop",
            "direct": "stop"
          },
          "wall_s": {
            "loaded_off": 244.381,
            "adaptive": 245.007,
            "direct": 238.094
          },
          "ttft_s": {
            "loaded_off": 30.407,
            "adaptive": 29.497,
            "direct": 29.522
          },
          "output_tokens": {
            "loaded_off": 302,
            "adaptive": 302,
            "direct": 302
          },
          "decode_tps": {
            "loaded_off": 1.4114009482156102,
            "adaptive": 1.4013348484701826,
            "direct": 1.4479508326527566
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "4B-chinese_policy-71ff50cb0f11",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "loaded_off": {
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
            "adaptive": {
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
            "direct": {
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
            "loaded_off": null,
            "adaptive": null,
            "direct": null
          }
        },
        {
          "repeat": 2,
          "case_id": "routes",
          "deterministic_regression": false,
          "quality_eligible": {
            "loaded_off": true,
            "adaptive": true,
            "direct": true
          },
          "finish_reason": {
            "loaded_off": "stop",
            "adaptive": "stop",
            "direct": "stop"
          },
          "wall_s": {
            "loaded_off": 290.036,
            "adaptive": 290.366,
            "direct": 278.293
          },
          "ttft_s": {
            "loaded_off": 270.778,
            "adaptive": 270.997,
            "direct": 259.836
          },
          "output_tokens": {
            "loaded_off": 23,
            "adaptive": 23,
            "direct": 23
          },
          "decode_tps": {
            "loaded_off": 1.1944428908031481,
            "adaptive": 1.1876581457186317,
            "direct": 1.2463321933728833
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": false,
            "enabled_at_end": false,
            "reason": "ineligible_workload_or_length",
            "calibration_id": "4B-routes-35280c38a065",
            "cycles": 0,
            "committed_tokens": 0,
            "cycle_ms": 0.0,
            "windows": 0,
            "last_ms_per_token": 0.0,
            "fallback_at": -1
          },
          "facts": {
            "loaded_off": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "adaptive": {
              "facts": [
                true,
                true,
                true
              ],
              "citations": [
                true
              ]
            },
            "direct": {
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
            "loaded_off": null,
            "adaptive": null,
            "direct": null
          }
        },
        {
          "repeat": 2,
          "case_id": "unicode_offsets",
          "deterministic_regression": false,
          "quality_eligible": {
            "loaded_off": true,
            "adaptive": true,
            "direct": true
          },
          "finish_reason": {
            "loaded_off": "stop",
            "adaptive": "stop",
            "direct": "stop"
          },
          "wall_s": {
            "loaded_off": 581.625,
            "adaptive": 355.563,
            "direct": 565.706
          },
          "ttft_s": {
            "loaded_off": 24.28,
            "adaptive": 24.325,
            "direct": 23.514
          },
          "output_tokens": {
            "loaded_off": 767,
            "adaptive": 717,
            "direct": 767
          },
          "decode_tps": {
            "loaded_off": 1.3761732785527854,
            "adaptive": 2.1646235779977876,
            "direct": 1.4146331970747694
          },
          "adaptive_policy": {
            "requested": "auto",
            "initially_enabled": true,
            "enabled_at_end": true,
            "reason": "eligible_code",
            "calibration_id": "4B-unicode_offsets-5027e59dda37",
            "cycles": 195,
            "committed_tokens": 716,
            "cycle_ms": 331224.076,
            "windows": 16,
            "last_ms_per_token": 600.5475609756098,
            "fallback_at": -1
          },
          "facts": {
            "loaded_off": {
              "facts": [],
              "citations": []
            },
            "adaptive": {
              "facts": [],
              "citations": []
            },
            "direct": {
              "facts": [],
              "citations": []
            }
          },
          "code_tests": {
            "loaded_off": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            },
            "adaptive": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            },
            "direct": {
              "pass": false,
              "reason": "AssertionError: functional output mismatch at check 4",
              "exit": 1
            }
          }
        }
      ],
      "timing_interpretation": "Bounded decode throughput is infrastructure evidence. Wall-time changes can reflect different output lengths; capped answers do not establish useful-answer speedup."
    }
  },
  "candidate_qualified": false,
  "limitations": "Three repetitions of three tasks/model, one slot, one two-order cloud judge. No long-context/concurrency or statistical-equivalence claim."
}
```
