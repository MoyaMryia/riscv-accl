# K1 sustained decode packing audit

Status: diagnostic complete

Diagnostic only. Separate profiler and counter runs; instrumentation perturbs timings. CPU shares and overlapping GEMM worker elapsed are not removable wall-time fractions. Capped tokens do not measure useful answers.

## native

{
  "cases_per_arm": 104,
  "output_sha256": {
    "baseline": "e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc",
    "audit-off": "e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc",
    "audit-on": "e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc"
  },
  "bitwise_equal": true
}

## 2B-256

{
  "exact_identity": true,
  "cpu_profile": {
    "samples": 14051,
    "sampled_cpu_s": 70.608031375,
    "multi_frame_samples_pct": 27.314781866059356,
    "unknown_leaf_samples_pct": 0.014233862358550993,
    "cpu_share_pct": {
      "other_or_unattributed": 96.79738096932603,
      "recurrent_visible_stack": 2.4838089815671482,
      "attention_visible_stack": 0.7188100491068251
    },
    "attention_copy_visible_cpu_pct": 0.0,
    "top_self": [
      {
        "symbol": "LOOP_INNER360",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 59.789338837093446
      },
      {
        "symbol": "spert::detail::sync_impl(spert::detail::Future*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 20.00569354494342
      },
      {
        "symbol": "LOOP_K360",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 6.782435413849548
      },
      {
        "symbol": "spert::detail::barrier_coro(spert::detail::Tile*, spert::detail::Barrier*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 4.72564230303893
      },
      {
        "symbol": "ggml_gdn_decode_step_rvv(float*, float const*, float const*, float const*, float, float, float, long, float*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 2.334353426802363
      },
      {
        "symbol": "void spacemit_kernels::rvv::forward_concat<int>(ggml_compute_params*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.7045761867482742
      },
      {
        "symbol": "ggml_compute_forward_flash_attn_ext_f16_one_chunk(ggml_compute_params const*, ggml_tensor*, int, int, long, long, float*, long)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.6476407373140701
      },
      {
        "symbol": "ggml_vec_dot_f16",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.5907052878798662
      },
      {
        "symbol": "ggml_compute_forward_dup_bytes(ggml_compute_params const*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.46971745783218277
      },
      {
        "symbol": "getenv",
        "dso": "/usr/lib/riscv64-linux-gnu/libc.so.6",
        "cpu_pct": 0.3771973525016013
      },
      {
        "symbol": "ggml_graph_compute_spert_kernel",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.23485872891609139
      },
      {
        "symbol": "memcpy_main_loop149",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.22774179773681588
      },
      {
        "symbol": "ggml_compute_forward_ssm_conv",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.2135079353782649
      },
      {
        "symbol": "$xrv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_v1p0_zicbop1p0_zicsr2p0_zifencei2p0_zihintpause2p0_zmmul1p0_zfh1p0_zfhmin1p0_zba1p0_zve32f1p0_zve32x1p0_zve64d1p0_zve64f1p0_zve64x1p0_zvfh1p0_zvfhmin1p0_zvl128b1p0_zvl32b1p0_zvl64b1p0",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.2135079353782649
      },
      {
        "symbol": "llama_token_data_array_partial_sort_inplace(llama_token_data_array*, int)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libllama.so.0.0.7",
        "cpu_pct": 0.19215714184043842
      },
      {
        "symbol": "LOOP_MAIN67",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.15657248594406092
      },
      {
        "symbol": "__tls_get_addr",
        "dso": "/usr/lib/riscv64-linux-gnu/ld-linux-riscv64-lp64d.so.1",
        "cpu_pct": 0.13522169240623444
      },
      {
        "symbol": "spert::detail::worker_main(spert::detail::WorkerPool*, unsigned int)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 0.12810476122695894
      },
      {
        "symbol": "ggml_compute_forward_gated_delta_net",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.12098783004768345
      },
      {
        "symbol": "expf@@GLIBC_2.27",
        "dso": "/usr/lib/riscv64-linux-gnu/libm.so.6",
        "cpu_pct": 0.10675396768913245
      },
      {
        "symbol": "ggml_cpu_extra_compute_forward",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.09963703650985695
      },
      {
        "symbol": "ggml_vec_silu_f32",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.09963703650985695
      },
      {
        "symbol": "ggml_compute_forward_rms_norm_mul_fused",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.09252010533058146
      },
      {
        "symbol": "ggml_is_empty",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libggml-base.so.0.16.0",
        "cpu_pct": 0.09252010533058146
      },
      {
        "symbol": "ggml_compute_forward_l2_norm",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.07116931179275496
      },
      {
        "symbol": "ggml_vec_swiglu_f32",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.07116931179275496
      },
      {
        "symbol": "spert::detail::ctx_sync(spert::detail::Tile*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 0.07116931179275496
      },
      {
        "symbol": "ggml::cpu::riscv64_spacemit::extra_buffer_type::get_tensor_traits(ggml_tensor const*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.06405238061347947
      },
      {
        "symbol": "common_sampler_sample(common_sampler*, llama_context*, int, bool)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libllama-common.so.0.0.7",
        "cpu_pct": 0.06405238061347947
      },
      {
        "symbol": "void spacemit_kernels::rvv::forward_binary<(ggml_op)2, float>(ggml_compute_params*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.05693544943420397
      }
    ],
    "limitations": "Visible stacks give lower bounds when frames are missing. Attention copy samples exclude inlined K transpose; they are not total packing cost. CPU shares are sampled user CPU time, not wall-time percentages or speedups.",
    "sample_window_verification": {
      "first_sample_ns": 808865689463000,
      "last_sample_ns": 808880138403000,
      "timed_samples": 14051,
      "tolerance_ns": 1000000
    },
    "window": {
      "enable_sent_ns": 808865679513387,
      "enable_ack_ns": 808865685507256,
      "disable_sent_ns": 808880145947464,
      "disable_ack_ns": 808880148993838
    },
    "perf_clockid": "CLOCK_MONOTONIC",
    "scope": "Enabled after receiving first streamed token, disabled after final event; excludes prefill. Pipelining may omit part of the first decode execution."
  },
  "counters": {
    "prefill": {
      "records": 6696,
      "worker_elapsed_ns": 28211793680.0,
      "section_ns": {
        "activation_quantization": 584607020.0,
        "staging_copies": 0.0,
        "gemm": 27218188679.0,
        "grid_wait": 66041681.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.020722079093270895,
        "staging_copies": 0.0,
        "gemm": 0.9647805094468562,
        "grid_wait": 0.0023409245703798864,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 490733568,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "decode": {
      "records": 47872,
      "worker_elapsed_ns": 49291061543.0,
      "section_ns": {
        "activation_quantization": 169369941.0,
        "staging_copies": 0.0,
        "gemm": 48719016769.0,
        "grid_wait": 97316085.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.0034361187545585096,
        "staging_copies": 0.0,
        "gemm": 0.9883945535743642,
        "grid_wait": 0.001974315057408623,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 123207680,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "startup_compatibility_probe": {
      "records": 748,
      "worker_elapsed_ns": 963259715.0,
      "section_ns": {
        "activation_quantization": 2221395.0,
        "staging_copies": 0.0,
        "gemm": 935929247.0,
        "grid_wait": 8839597.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.002306122601628783,
        "staging_copies": 0.0,
        "gemm": 0.9716271037038022,
        "grid_wait": 0.009176753540450926,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 3842048,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "request_only_records": 54572,
    "decode_weights": {
      "blk.0.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 162592033.0,
        "section_ns": {
          "activation_quantization": 1374080.0,
          "staging_copies": 0.0,
          "gemm": 158578433.0,
          "grid_wait": 538808.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.008451090589414059,
          "staging_copies": 0.0,
          "gemm": 0.9753149036521365,
          "grid_wait": 0.0033138647082418854,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 326518239.0,
        "section_ns": {
          "activation_quantization": 865654.0,
          "staging_copies": 0.0,
          "gemm": 323519886.0,
          "grid_wait": 459397.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026511658357927137,
          "staging_copies": 0.0,
          "gemm": 0.990817195972933,
          "grid_wait": 0.0014069566263953787,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 339830335.0,
        "section_ns": {
          "activation_quantization": 1541715.0,
          "staging_copies": 0.0,
          "gemm": 336077362.0,
          "grid_wait": 551427.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004536719772235754,
          "staging_copies": 0.0,
          "gemm": 0.9889563331654898,
          "grid_wait": 0.0016226538457786589,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 345918667.0,
        "section_ns": {
          "activation_quantization": 661314.0,
          "staging_copies": 0.0,
          "gemm": 343141801.0,
          "grid_wait": 396386.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019117615297702334,
          "staging_copies": 0.0,
          "gemm": 0.9919724887237727,
          "grid_wait": 0.0011458936386338468,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 325980377.0,
        "section_ns": {
          "activation_quantization": 929027.0,
          "staging_copies": 0.0,
          "gemm": 322979042.0,
          "grid_wait": 419178.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028499476212336546,
          "staging_copies": 0.0,
          "gemm": 0.9907928967147615,
          "grid_wait": 0.0012858994883609206,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3682303.0,
        "section_ns": {
          "activation_quantization": 974870.0,
          "staging_copies": 0.0,
          "gemm": 623474.0,
          "grid_wait": 421168.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2647446448594806,
          "staging_copies": 0.0,
          "gemm": 0.16931632187791174,
          "grid_wait": 0.1143762476906436,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2423850.0,
        "section_ns": {
          "activation_quantization": 564136.0,
          "staging_copies": 0.0,
          "gemm": 537268.0,
          "grid_wait": 544348.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.23274377539864266,
          "staging_copies": 0.0,
          "gemm": 0.22165893103946202,
          "grid_wait": 0.22457990387193927,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 120772118.0,
        "section_ns": {
          "activation_quantization": 507676.0,
          "staging_copies": 0.0,
          "gemm": 118020670.0,
          "grid_wait": 407972.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00420358612904346,
          "staging_copies": 0.0,
          "gemm": 0.9772178542070447,
          "grid_wait": 0.003378031343293988,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 165668397.0,
        "section_ns": {
          "activation_quantization": 1493740.0,
          "staging_copies": 0.0,
          "gemm": 161517389.0,
          "grid_wait": 561191.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009016445061637193,
          "staging_copies": 0.0,
          "gemm": 0.9749438753849957,
          "grid_wait": 0.003387435444311084,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 317178938.0,
        "section_ns": {
          "activation_quantization": 677179.0,
          "staging_copies": 0.0,
          "gemm": 314402039.0,
          "grid_wait": 455189.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021350062027132456,
          "staging_copies": 0.0,
          "gemm": 0.9912450082041703,
          "grid_wait": 0.0014351173595265648,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 344481623.0,
        "section_ns": {
          "activation_quantization": 1533164.0,
          "staging_copies": 0.0,
          "gemm": 340726575.0,
          "grid_wait": 584277.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0044506408981938635,
          "staging_copies": 0.0,
          "gemm": 0.9890994243254596,
          "grid_wait": 0.0016961049907733394,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 298218846.0,
        "section_ns": {
          "activation_quantization": 648894.0,
          "staging_copies": 0.0,
          "gemm": 295465941.0,
          "grid_wait": 436553.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021758987022570666,
          "staging_copies": 0.0,
          "gemm": 0.9907688429590396,
          "grid_wait": 0.00146386791396812,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 347029310.0,
        "section_ns": {
          "activation_quantization": 895191.0,
          "staging_copies": 0.0,
          "gemm": 344034829.0,
          "grid_wait": 431608.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002579583263442503,
          "staging_copies": 0.0,
          "gemm": 0.9913711006139511,
          "grid_wait": 0.0012437220360435838,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3675097.0,
        "section_ns": {
          "activation_quantization": 1037228.0,
          "staging_copies": 0.0,
          "gemm": 588139.0,
          "grid_wait": 419436.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2822314621899776,
          "staging_copies": 0.0,
          "gemm": 0.16003359911316625,
          "grid_wait": 0.11412923250733246,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2200769.0,
        "section_ns": {
          "activation_quantization": 548803.0,
          "staging_copies": 0.0,
          "gemm": 541262.0,
          "grid_wait": 382556.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.24936874338015486,
          "staging_copies": 0.0,
          "gemm": 0.24594221383525486,
          "grid_wait": 0.17382833000646591,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 117115228.0,
        "section_ns": {
          "activation_quantization": 499645.0,
          "staging_copies": 0.0,
          "gemm": 114422687.0,
          "grid_wait": 374105.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004266268430950755,
          "staging_copies": 0.0,
          "gemm": 0.9770094713900057,
          "grid_wait": 0.0031943326789237005,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 157254440.0,
        "section_ns": {
          "activation_quantization": 1299700.0,
          "staging_copies": 0.0,
          "gemm": 153147696.0,
          "grid_wait": 684024.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.008264949466609654,
          "staging_copies": 0.0,
          "gemm": 0.9738847182947585,
          "grid_wait": 0.004349791331805957,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 315710185.0,
        "section_ns": {
          "activation_quantization": 643064.0,
          "staging_copies": 0.0,
          "gemm": 312932664.0,
          "grid_wait": 443055.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002036880755050712,
          "staging_copies": 0.0,
          "gemm": 0.9912023079014698,
          "grid_wait": 0.0014033598567623025,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 308871093.0,
        "section_ns": {
          "activation_quantization": 1502201.0,
          "staging_copies": 0.0,
          "gemm": 305157024.0,
          "grid_wait": 561350.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004863520847514209,
          "staging_copies": 0.0,
          "gemm": 0.9879753428398688,
          "grid_wait": 0.0018174248504375253,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 306102140.0,
        "section_ns": {
          "activation_quantization": 671769.0,
          "staging_copies": 0.0,
          "gemm": 303327976.0,
          "grid_wait": 414238.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002194590995018852,
          "staging_copies": 0.0,
          "gemm": 0.9909371296783486,
          "grid_wait": 0.0013532672460244805,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 305368410.0,
        "section_ns": {
          "activation_quantization": 939671.0,
          "staging_copies": 0.0,
          "gemm": 302361677.0,
          "grid_wait": 410111.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003077171603965191,
          "staging_copies": 0.0,
          "gemm": 0.9901537523151134,
          "grid_wait": 0.0013430040127595385,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3665231.0,
        "section_ns": {
          "activation_quantization": 961943.0,
          "staging_copies": 0.0,
          "gemm": 618305.0,
          "grid_wait": 467727.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2624508523473691,
          "staging_copies": 0.0,
          "gemm": 0.1686946880019295,
          "grid_wait": 0.12761187494048806,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2241189.0,
        "section_ns": {
          "activation_quantization": 617010.0,
          "staging_copies": 0.0,
          "gemm": 498969.0,
          "grid_wait": 385429.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.27530476010724664,
          "staging_copies": 0.0,
          "gemm": 0.222635841957104,
          "grid_wait": 0.17197523278938098,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 125170322.0,
        "section_ns": {
          "activation_quantization": 625023.0,
          "staging_copies": 0.0,
          "gemm": 122454163.0,
          "grid_wait": 373636.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004993380140062275,
          "staging_copies": 0.0,
          "gemm": 0.9783002954965635,
          "grid_wait": 0.0029850206824585785,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32600112.0,
        "section_ns": {
          "activation_quantization": 882808.0,
          "staging_copies": 0.0,
          "gemm": 29766967.0,
          "grid_wait": 394300.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.02707990696473681,
          "staging_copies": 0.0,
          "gemm": 0.9130940102291674,
          "grid_wait": 0.012095050470992246,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 121702523.0,
        "section_ns": {
          "activation_quantization": 471485.0,
          "staging_copies": 0.0,
          "gemm": 118969190.0,
          "grid_wait": 423472.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003874077450308898,
          "staging_copies": 0.0,
          "gemm": 0.9775408682365607,
          "grid_wait": 0.0034795663192619267,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 229537504.0,
        "section_ns": {
          "activation_quantization": 663490.0,
          "staging_copies": 0.0,
          "gemm": 226842216.0,
          "grid_wait": 409000.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028905516024082933,
          "staging_copies": 0.0,
          "gemm": 0.988257744581905,
          "grid_wait": 0.0017818438942335106,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32706215.0,
        "section_ns": {
          "activation_quantization": 798596.0,
          "staging_copies": 0.0,
          "gemm": 29689558.0,
          "grid_wait": 436435.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.024417255252556738,
          "staging_copies": 0.0,
          "gemm": 0.9077650226417211,
          "grid_wait": 0.013344099890494818,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 345559989.0,
        "section_ns": {
          "activation_quantization": 1557512.0,
          "staging_copies": 0.0,
          "gemm": 341752689.0,
          "grid_wait": 578845.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00450721162628582,
          "staging_copies": 0.0,
          "gemm": 0.9889822313890628,
          "grid_wait": 0.0016750926566327677,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 313000696.0,
        "section_ns": {
          "activation_quantization": 701347.0,
          "staging_copies": 0.0,
          "gemm": 310155082.0,
          "grid_wait": 423552.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002240720257056553,
          "staging_copies": 0.0,
          "gemm": 0.9909086016856653,
          "grid_wait": 0.001353198268926533,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 348341805.0,
        "section_ns": {
          "activation_quantization": 921787.0,
          "staging_copies": 0.0,
          "gemm": 344465625.0,
          "grid_wait": 1173785.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026462141114529736,
          "staging_copies": 0.0,
          "gemm": 0.9888724811539631,
          "grid_wait": 0.003369635751873078,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 161886683.0,
        "section_ns": {
          "activation_quantization": 1428398.0,
          "staging_copies": 0.0,
          "gemm": 157856693.0,
          "grid_wait": 562933.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.008823443494731435,
          "staging_copies": 0.0,
          "gemm": 0.9751061055466804,
          "grid_wait": 0.003477327409321247,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 361471749.0,
        "section_ns": {
          "activation_quantization": 645098.0,
          "staging_copies": 0.0,
          "gemm": 358707844.0,
          "grid_wait": 462895.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0017846429265485973,
          "staging_copies": 0.0,
          "gemm": 0.9923537454651815,
          "grid_wait": 0.0012805841709084712,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 343892688.0,
        "section_ns": {
          "activation_quantization": 1516948.0,
          "staging_copies": 0.0,
          "gemm": 340084940.0,
          "grid_wait": 597803.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004411108618860776,
          "staging_copies": 0.0,
          "gemm": 0.9889275110147151,
          "grid_wait": 0.0017383417003620618,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 366887802.0,
        "section_ns": {
          "activation_quantization": 673724.0,
          "staging_copies": 0.0,
          "gemm": 364138699.0,
          "grid_wait": 436889.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018363216120224134,
          "staging_copies": 0.0,
          "gemm": 0.9925069653855649,
          "grid_wait": 0.0011907972890306121,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 331291809.0,
        "section_ns": {
          "activation_quantization": 932064.0,
          "staging_copies": 0.0,
          "gemm": 328072984.0,
          "grid_wait": 637383.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002813423014633,
          "staging_copies": 0.0,
          "gemm": 0.9902840187636514,
          "grid_wait": 0.0019239322635954455,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3708351.0,
        "section_ns": {
          "activation_quantization": 1015786.0,
          "staging_copies": 0.0,
          "gemm": 604849.0,
          "grid_wait": 450172.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2739185152646014,
          "staging_copies": 0.0,
          "gemm": 0.16310457127709863,
          "grid_wait": 0.12139411830217797,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2215889.0,
        "section_ns": {
          "activation_quantization": 519218.0,
          "staging_copies": 0.0,
          "gemm": 492888.0,
          "grid_wait": 442176.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.23431588856662044,
          "staging_copies": 0.0,
          "gemm": 0.22243352442292913,
          "grid_wait": 0.1995479015419996,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 120513030.0,
        "section_ns": {
          "activation_quantization": 486765.0,
          "staging_copies": 0.0,
          "gemm": 118008753.0,
          "grid_wait": 377932.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004039106808616463,
          "staging_copies": 0.0,
          "gemm": 0.9792198652710001,
          "grid_wait": 0.0031360260380143127,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 160955328.0,
        "section_ns": {
          "activation_quantization": 1553119.0,
          "staging_copies": 0.0,
          "gemm": 156757961.0,
          "grid_wait": 543089.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009649379236454975,
          "staging_copies": 0.0,
          "gemm": 0.973922161806287,
          "grid_wait": 0.0033741598165672403,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 347913129.0,
        "section_ns": {
          "activation_quantization": 779814.0,
          "staging_copies": 0.0,
          "gemm": 344913467.0,
          "grid_wait": 507346.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002241404347807754,
          "staging_copies": 0.0,
          "gemm": 0.9913781293375681,
          "grid_wait": 0.0014582548277446582,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 352941064.0,
        "section_ns": {
          "activation_quantization": 1532340.0,
          "staging_copies": 0.0,
          "gemm": 349181168.0,
          "grid_wait": 565394.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004341631383533201,
          "staging_copies": 0.0,
          "gemm": 0.989346957938564,
          "grid_wait": 0.0016019501771547897,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 350388413.0,
        "section_ns": {
          "activation_quantization": 678051.0,
          "staging_copies": 0.0,
          "gemm": 347648337.0,
          "grid_wait": 406772.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019351410458884096,
          "staging_copies": 0.0,
          "gemm": 0.9921798898070296,
          "grid_wait": 0.0011609173845597456,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 356050438.0,
        "section_ns": {
          "activation_quantization": 944811.0,
          "staging_copies": 0.0,
          "gemm": 353040399.0,
          "grid_wait": 415712.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002653587523462055,
          "staging_copies": 0.0,
          "gemm": 0.9915460320259457,
          "grid_wait": 0.0011675649167436216,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3672440.0,
        "section_ns": {
          "activation_quantization": 970985.0,
          "staging_copies": 0.0,
          "gemm": 649513.0,
          "grid_wait": 438169.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.26439778457918983,
          "staging_copies": 0.0,
          "gemm": 0.17686143272592608,
          "grid_wait": 0.11931277297927263,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2199948.0,
        "section_ns": {
          "activation_quantization": 561023.0,
          "staging_copies": 0.0,
          "gemm": 492220.0,
          "grid_wait": 425521.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2550164822077613,
          "staging_copies": 0.0,
          "gemm": 0.2237416520754127,
          "grid_wait": 0.19342320818492073,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 128079107.0,
        "section_ns": {
          "activation_quantization": 518892.0,
          "staging_copies": 0.0,
          "gemm": 125354064.0,
          "grid_wait": 383918.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004051339926971852,
          "staging_copies": 0.0,
          "gemm": 0.9787237507831781,
          "grid_wait": 0.0029975068455154047,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 157281302.0,
        "section_ns": {
          "activation_quantization": 1419666.0,
          "staging_copies": 0.0,
          "gemm": 153205832.0,
          "grid_wait": 519902.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009026285909052304,
          "staging_copies": 0.0,
          "gemm": 0.9740880196935298,
          "grid_wait": 0.0033055550366692665,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 350447261.0,
        "section_ns": {
          "activation_quantization": 638102.0,
          "staging_copies": 0.0,
          "gemm": 347735300.0,
          "grid_wait": 436384.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018208217641056124,
          "staging_copies": 0.0,
          "gemm": 0.9922614290313999,
          "grid_wait": 0.001245220175939683,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 344636967.0,
        "section_ns": {
          "activation_quantization": 1559928.0,
          "staging_copies": 0.0,
          "gemm": 340875696.0,
          "grid_wait": 556758.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004526293315481737,
          "staging_copies": 0.0,
          "gemm": 0.9890862810430896,
          "grid_wait": 0.0016154912366089852,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 355011444.0,
        "section_ns": {
          "activation_quantization": 670610.0,
          "staging_copies": 0.0,
          "gemm": 352255411.0,
          "grid_wait": 405924.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001888981359147397,
          "staging_copies": 0.0,
          "gemm": 0.9922367770206304,
          "grid_wait": 0.0011434110276174647,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 338924945.0,
        "section_ns": {
          "activation_quantization": 922075.0,
          "staging_copies": 0.0,
          "gemm": 335930360.0,
          "grid_wait": 432680.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002720587592040474,
          "staging_copies": 0.0,
          "gemm": 0.9911644597301624,
          "grid_wait": 0.0012766248291343678,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3659721.0,
        "section_ns": {
          "activation_quantization": 1008445.0,
          "staging_copies": 0.0,
          "gemm": 601389.0,
          "grid_wait": 436480.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.27555242599094304,
          "staging_copies": 0.0,
          "gemm": 0.16432646095153156,
          "grid_wait": 0.11926592218368559,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2247642.0,
        "section_ns": {
          "activation_quantization": 557721.0,
          "staging_copies": 0.0,
          "gemm": 496841.0,
          "grid_wait": 396580.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.24813604657681249,
          "staging_copies": 0.0,
          "gemm": 0.22104988249908125,
          "grid_wait": 0.17644268971660076,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 123265722.0,
        "section_ns": {
          "activation_quantization": 500856.0,
          "staging_copies": 0.0,
          "gemm": 120729451.0,
          "grid_wait": 375092.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004063222052924007,
          "staging_copies": 0.0,
          "gemm": 0.9794243609752271,
          "grid_wait": 0.003042954634216964,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32916315.0,
        "section_ns": {
          "activation_quantization": 1072067.0,
          "staging_copies": 0.0,
          "gemm": 29282127.0,
          "grid_wait": 913795.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.03256947200803006,
          "staging_copies": 0.0,
          "gemm": 0.8895931090706842,
          "grid_wait": 0.027761157347048114,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 121590140.0,
        "section_ns": {
          "activation_quantization": 468600.0,
          "staging_copies": 0.0,
          "gemm": 118864596.0,
          "grid_wait": 424339.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003853930919069589,
          "staging_copies": 0.0,
          "gemm": 0.9775841692426706,
          "grid_wait": 0.003489912915636087,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 220878521.0,
        "section_ns": {
          "activation_quantization": 673019.0,
          "staging_copies": 0.0,
          "gemm": 218139222.0,
          "grid_wait": 428096.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0030470097180703235,
          "staging_copies": 0.0,
          "gemm": 0.987598164875434,
          "grid_wait": 0.0019381513334200567,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32583195.0,
        "section_ns": {
          "activation_quantization": 809811.0,
          "staging_copies": 0.0,
          "gemm": 29740599.0,
          "grid_wait": 405891.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.024853640043586887,
          "staging_copies": 0.0,
          "gemm": 0.9127588316615359,
          "grid_wait": 0.012457065674498771,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 353560165.0,
        "section_ns": {
          "activation_quantization": 1521795.0,
          "staging_copies": 0.0,
          "gemm": 349787923.0,
          "grid_wait": 565968.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004304203783817105,
          "staging_copies": 0.0,
          "gemm": 0.9893306928397887,
          "grid_wait": 0.0016007685707466507,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 341569929.0,
        "section_ns": {
          "activation_quantization": 669687.0,
          "staging_copies": 0.0,
          "gemm": 338748144.0,
          "grid_wait": 451089.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019606146301011174,
          "staging_copies": 0.0,
          "gemm": 0.9917387780351121,
          "grid_wait": 0.0013206344051440197,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 333723512.0,
        "section_ns": {
          "activation_quantization": 893770.0,
          "staging_copies": 0.0,
          "gemm": 330762965.0,
          "grid_wait": 434726.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002678175099631578,
          "staging_copies": 0.0,
          "gemm": 0.9911287431255368,
          "grid_wait": 0.0013026531975367682,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 155027328.0,
        "section_ns": {
          "activation_quantization": 1276373.0,
          "staging_copies": 0.0,
          "gemm": 151165605.0,
          "grid_wait": 525932.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.008233212921014803,
          "staging_copies": 0.0,
          "gemm": 0.9750900499297775,
          "grid_wait": 0.0033925115448032494,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 355076156.0,
        "section_ns": {
          "activation_quantization": 628480.0,
          "staging_copies": 0.0,
          "gemm": 352366710.0,
          "grid_wait": 452810.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001769986492700456,
          "staging_copies": 0.0,
          "gemm": 0.9923693946940216,
          "grid_wait": 0.0012752475556257852,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 357359015.0,
        "section_ns": {
          "activation_quantization": 1535908.0,
          "staging_copies": 0.0,
          "gemm": 353636084.0,
          "grid_wait": 552138.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004297941105529407,
          "staging_copies": 0.0,
          "gemm": 0.9895820985515085,
          "grid_wait": 0.0015450512700791947,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 354590606.0,
        "section_ns": {
          "activation_quantization": 754562.0,
          "staging_copies": 0.0,
          "gemm": 351636075.0,
          "grid_wait": 438460.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021279807959717918,
          "staging_copies": 0.0,
          "gemm": 0.9916677685477093,
          "grid_wait": 0.0012365245795597868,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 346730895.0,
        "section_ns": {
          "activation_quantization": 951356.0,
          "staging_copies": 0.0,
          "gemm": 343690907.0,
          "grid_wait": 433541.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002743787801199544,
          "staging_copies": 0.0,
          "gemm": 0.9912324282495796,
          "grid_wait": 0.0012503673778478841,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3623294.0,
        "section_ns": {
          "activation_quantization": 996368.0,
          "staging_copies": 0.0,
          "gemm": 588553.0,
          "grid_wait": 407762.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.27498955370444683,
          "staging_copies": 0.0,
          "gemm": 0.16243589396830618,
          "grid_wait": 0.11253903216244666,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2309856.0,
        "section_ns": {
          "activation_quantization": 578415.0,
          "staging_copies": 0.0,
          "gemm": 496845.0,
          "grid_wait": 426341.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2504117139769752,
          "staging_copies": 0.0,
          "gemm": 0.2150978242799551,
          "grid_wait": 0.1845747094191153,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 127646480.0,
        "section_ns": {
          "activation_quantization": 508016.0,
          "staging_copies": 0.0,
          "gemm": 125111659.0,
          "grid_wait": 377516.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003979866894880298,
          "staging_copies": 0.0,
          "gemm": 0.9801418652515917,
          "grid_wait": 0.0029575120285338066,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 160408806.0,
        "section_ns": {
          "activation_quantization": 1455407.0,
          "staging_copies": 0.0,
          "gemm": 156350528.0,
          "grid_wait": 543228.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009073111609595797,
          "staging_copies": 0.0,
          "gemm": 0.9747004039167276,
          "grid_wait": 0.0033865223085071776,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 348680949.0,
        "section_ns": {
          "activation_quantization": 628971.0,
          "staging_copies": 0.0,
          "gemm": 345941086.0,
          "grid_wait": 438590.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018038582314401123,
          "staging_copies": 0.0,
          "gemm": 0.9921422061977926,
          "grid_wait": 0.0012578547846042486,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 336479707.0,
        "section_ns": {
          "activation_quantization": 1565212.0,
          "staging_copies": 0.0,
          "gemm": 332509340.0,
          "grid_wait": 563099.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004651727778638371,
          "staging_copies": 0.0,
          "gemm": 0.9882002780036895,
          "grid_wait": 0.0016735006251060484,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 344259000.0,
        "section_ns": {
          "activation_quantization": 651519.0,
          "staging_copies": 0.0,
          "gemm": 341538218.0,
          "grid_wait": 392843.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018925256856029908,
          "staging_copies": 0.0,
          "gemm": 0.9920967004493709,
          "grid_wait": 0.0011411263031612827,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 347738623.0,
        "section_ns": {
          "activation_quantization": 910606.0,
          "staging_copies": 0.0,
          "gemm": 344731721.0,
          "grid_wait": 447930.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026186507329673298,
          "staging_copies": 0.0,
          "gemm": 0.9913529823806774,
          "grid_wait": 0.001288122659874914,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3783019.0,
        "section_ns": {
          "activation_quantization": 1027296.0,
          "staging_copies": 0.0,
          "gemm": 587309.0,
          "grid_wait": 549763.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2715545441352528,
          "staging_copies": 0.0,
          "gemm": 0.15524875767211319,
          "grid_wait": 0.14532388021313136,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2130103.0,
        "section_ns": {
          "activation_quantization": 515886.0,
          "staging_copies": 0.0,
          "gemm": 480637.0,
          "grid_wait": 400339.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.24218828854754912,
          "staging_copies": 0.0,
          "gemm": 0.2256402624661812,
          "grid_wait": 0.18794349381227105,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 124333213.0,
        "section_ns": {
          "activation_quantization": 497294.0,
          "staging_copies": 0.0,
          "gemm": 121768198.0,
          "grid_wait": 377386.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003999687517123844,
          "staging_copies": 0.0,
          "gemm": 0.9793698325804546,
          "grid_wait": 0.003035279077039536,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 163025630.0,
        "section_ns": {
          "activation_quantization": 1335746.0,
          "staging_copies": 0.0,
          "gemm": 159018775.0,
          "grid_wait": 532012.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.008193472400628048,
          "staging_copies": 0.0,
          "gemm": 0.9754219321219615,
          "grid_wait": 0.003263364171633626,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 350702958.0,
        "section_ns": {
          "activation_quantization": 644522.0,
          "staging_copies": 0.0,
          "gemm": 347951842.0,
          "grid_wait": 444125.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018378002959416157,
          "staging_copies": 0.0,
          "gemm": 0.9921554240212596,
          "grid_wait": 0.001266385098468431,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 349230549.0,
        "section_ns": {
          "activation_quantization": 1510242.0,
          "staging_copies": 0.0,
          "gemm": 345448409.0,
          "grid_wait": 563007.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004324484224889501,
          "staging_copies": 0.0,
          "gemm": 0.9891700768709097,
          "grid_wait": 0.0016121355981374929,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 344315219.0,
        "section_ns": {
          "activation_quantization": 674228.0,
          "staging_copies": 0.0,
          "gemm": 341505759.0,
          "grid_wait": 438430.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001958170777226086,
          "staging_copies": 0.0,
          "gemm": 0.9918404419991671,
          "grid_wait": 0.001273339009740374,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 336433955.0,
        "section_ns": {
          "activation_quantization": 954612.0,
          "staging_copies": 0.0,
          "gemm": 333406625.0,
          "grid_wait": 406550.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00283744249298499,
          "staging_copies": 0.0,
          "gemm": 0.9910017108707116,
          "grid_wait": 0.00120840953761638,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3633345.0,
        "section_ns": {
          "activation_quantization": 973360.0,
          "staging_copies": 0.0,
          "gemm": 593100.0,
          "grid_wait": 438960.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.267896387488664,
          "staging_copies": 0.0,
          "gemm": 0.16323800795135063,
          "grid_wait": 0.1208142909632859,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2209687.0,
        "section_ns": {
          "activation_quantization": 559807.0,
          "staging_copies": 0.0,
          "gemm": 468804.0,
          "grid_wait": 408925.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2533422154359418,
          "staging_copies": 0.0,
          "gemm": 0.21215855458261737,
          "grid_wait": 0.18506014652753988,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 126338802.0,
        "section_ns": {
          "activation_quantization": 506683.0,
          "staging_copies": 0.0,
          "gemm": 123589067.0,
          "grid_wait": 565562.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004010509771970134,
          "staging_copies": 0.0,
          "gemm": 0.9782352297435906,
          "grid_wait": 0.00447655028421118,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 33077094.0,
        "section_ns": {
          "activation_quantization": 985619.0,
          "staging_copies": 0.0,
          "gemm": 29653207.0,
          "grid_wait": 847692.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.029797629743410953,
          "staging_copies": 0.0,
          "gemm": 0.8964876721032385,
          "grid_wait": 0.02562776524443169,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 120085761.0,
        "section_ns": {
          "activation_quantization": 478384.0,
          "staging_copies": 0.0,
          "gemm": 117350879.0,
          "grid_wait": 412215.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003983686292332361,
          "staging_copies": 0.0,
          "gemm": 0.9772255929660136,
          "grid_wait": 0.0034326717553132715,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 229934844.0,
        "section_ns": {
          "activation_quantization": 657309.0,
          "staging_copies": 0.0,
          "gemm": 226401631.0,
          "grid_wait": 1229072.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028586750427438477,
          "staging_copies": 0.0,
          "gemm": 0.9846338513183326,
          "grid_wait": 0.00534530555969151,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32148911.0,
        "section_ns": {
          "activation_quantization": 792612.0,
          "staging_copies": 0.0,
          "gemm": 29318036.0,
          "grid_wait": 412001.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.02465439653616883,
          "staging_copies": 0.0,
          "gemm": 0.9119449178231884,
          "grid_wait": 0.012815395208876593,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 342831827.0,
        "section_ns": {
          "activation_quantization": 1564457.0,
          "staging_copies": 0.0,
          "gemm": 339013362.0,
          "grid_wait": 569006.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004563336530595801,
          "staging_copies": 0.0,
          "gemm": 0.9888619880090654,
          "grid_wait": 0.0016597233838502399,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 352629225.0,
        "section_ns": {
          "activation_quantization": 679855.0,
          "staging_copies": 0.0,
          "gemm": 349662208.0,
          "grid_wait": 572481.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001927959884776992,
          "staging_copies": 0.0,
          "gemm": 0.9915860150275406,
          "grid_wait": 0.0016234644193203215,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 338904139.0,
        "section_ns": {
          "activation_quantization": 943162.0,
          "staging_copies": 0.0,
          "gemm": 335889973.0,
          "grid_wait": 406547.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002782975748785411,
          "staging_copies": 0.0,
          "gemm": 0.9911061398987517,
          "grid_wait": 0.0011995929031719497,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 163938911.0,
        "section_ns": {
          "activation_quantization": 1316958.0,
          "staging_copies": 0.0,
          "gemm": 160010413.0,
          "grid_wait": 519300.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.008033224034286772,
          "staging_copies": 0.0,
          "gemm": 0.9760368177631727,
          "grid_wait": 0.003167643342464316,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 348147347.0,
        "section_ns": {
          "activation_quantization": 726758.0,
          "staging_copies": 0.0,
          "gemm": 345323408.0,
          "grid_wait": 432754.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002087501186674273,
          "staging_copies": 0.0,
          "gemm": 0.9918886671855064,
          "grid_wait": 0.0012430196689104743,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 342024067.0,
        "section_ns": {
          "activation_quantization": 1516206.0,
          "staging_copies": 0.0,
          "gemm": 338259667.0,
          "grid_wait": 585191.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004433038918281736,
          "staging_copies": 0.0,
          "gemm": 0.9889937569802654,
          "grid_wait": 0.001710964392456043,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 342146690.0,
        "section_ns": {
          "activation_quantization": 667424.0,
          "staging_copies": 0.0,
          "gemm": 339414908.0,
          "grid_wait": 403085.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019506954750899389,
          "staging_copies": 0.0,
          "gemm": 0.9920157579195052,
          "grid_wait": 0.001178105800175942,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 345331960.0,
        "section_ns": {
          "activation_quantization": 944900.0,
          "staging_copies": 0.0,
          "gemm": 341620558.0,
          "grid_wait": 1023620.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002736207792641029,
          "staging_copies": 0.0,
          "gemm": 0.9892526541707869,
          "grid_wait": 0.002964162367132194,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3626979.0,
        "section_ns": {
          "activation_quantization": 991687.0,
          "staging_copies": 0.0,
          "gemm": 625935.0,
          "grid_wait": 400629.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.27341955936331586,
          "staging_copies": 0.0,
          "gemm": 0.17257750872006702,
          "grid_wait": 0.11045804235425681,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2218812.0,
        "section_ns": {
          "activation_quantization": 561660.0,
          "staging_copies": 0.0,
          "gemm": 517184.0,
          "grid_wait": 376260.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.25313546167949336,
          "staging_copies": 0.0,
          "gemm": 0.23309050068234713,
          "grid_wait": 0.16957723322210264,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 121730614.0,
        "section_ns": {
          "activation_quantization": 508352.0,
          "staging_copies": 0.0,
          "gemm": 119159489.0,
          "grid_wait": 387415.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0041760407123223745,
          "staging_copies": 0.0,
          "gemm": 0.9788785670628426,
          "grid_wait": 0.003182560140541146,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 161541091.0,
        "section_ns": {
          "activation_quantization": 1468884.0,
          "staging_copies": 0.0,
          "gemm": 157492269.0,
          "grid_wait": 513067.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009092943417102463,
          "staging_copies": 0.0,
          "gemm": 0.9749362717873435,
          "grid_wait": 0.0031760773486419007,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 346801643.0,
        "section_ns": {
          "activation_quantization": 654892.0,
          "staging_copies": 0.0,
          "gemm": 343322356.0,
          "grid_wait": 1172355.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018883762900742658,
          "staging_copies": 0.0,
          "gemm": 0.9899675013938731,
          "grid_wait": 0.0033804770642335163,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 337379184.0,
        "section_ns": {
          "activation_quantization": 1539368.0,
          "staging_copies": 0.0,
          "gemm": 333622252.0,
          "grid_wait": 555513.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004562723703783693,
          "staging_copies": 0.0,
          "gemm": 0.9888643633686659,
          "grid_wait": 0.001646553866820663,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 348766697.0,
        "section_ns": {
          "activation_quantization": 664035.0,
          "staging_copies": 0.0,
          "gemm": 346033503.0,
          "grid_wait": 406055.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019039518558160958,
          "staging_copies": 0.0,
          "gemm": 0.9921632597850936,
          "grid_wait": 0.0011642596712724553,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 343980786.0,
        "section_ns": {
          "activation_quantization": 906268.0,
          "staging_copies": 0.0,
          "gemm": 341015246.0,
          "grid_wait": 423268.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026346471572979077,
          "staging_copies": 0.0,
          "gemm": 0.9913787626498417,
          "grid_wait": 0.0012304989616483985,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3677853.0,
        "section_ns": {
          "activation_quantization": 1039895.0,
          "staging_copies": 0.0,
          "gemm": 595810.0,
          "grid_wait": 424253.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2827451233097136,
          "staging_copies": 0.0,
          "gemm": 0.16199940563149207,
          "grid_wait": 0.11535344126043101,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2195209.0,
        "section_ns": {
          "activation_quantization": 538390.0,
          "staging_copies": 0.0,
          "gemm": 476804.0,
          "grid_wait": 406907.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.24525682975971763,
          "staging_copies": 0.0,
          "gemm": 0.21720209784125338,
          "grid_wait": 0.18536139383539335,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 122736832.0,
        "section_ns": {
          "activation_quantization": 506425.0,
          "staging_copies": 0.0,
          "gemm": 120144483.0,
          "grid_wait": 375155.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004126104542114954,
          "staging_copies": 0.0,
          "gemm": 0.9788788014342752,
          "grid_wait": 0.003056580440335954,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 158050298.0,
        "section_ns": {
          "activation_quantization": 1312157.0,
          "staging_copies": 0.0,
          "gemm": 154141609.0,
          "grid_wait": 531342.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.008302148218663909,
          "staging_copies": 0.0,
          "gemm": 0.9752693348290935,
          "grid_wait": 0.0033618538321262765,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 352054336.0,
        "section_ns": {
          "activation_quantization": 719424.0,
          "staging_copies": 0.0,
          "gemm": 349226841.0,
          "grid_wait": 432520.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020435027393044237,
          "staging_copies": 0.0,
          "gemm": 0.9919685835086548,
          "grid_wait": 0.0012285603549561169,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 347123792.0,
        "section_ns": {
          "activation_quantization": 1580786.0,
          "staging_copies": 0.0,
          "gemm": 343328300.0,
          "grid_wait": 552765.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0045539546306869105,
          "staging_copies": 0.0,
          "gemm": 0.9890658834471363,
          "grid_wait": 0.001592414616166673,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 352394926.0,
        "section_ns": {
          "activation_quantization": 678776.0,
          "staging_copies": 0.0,
          "gemm": 349530623.0,
          "grid_wait": 539801.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019261798338152008,
          "staging_copies": 0.0,
          "gemm": 0.9918718948864774,
          "grid_wait": 0.0015318069591047404,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 347175332.0,
        "section_ns": {
          "activation_quantization": 939814.0,
          "staging_copies": 0.0,
          "gemm": 344146042.0,
          "grid_wait": 419802.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002707029887711031,
          "staging_copies": 0.0,
          "gemm": 0.9912744664704461,
          "grid_wait": 0.0012091930540733234,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3595857.0,
        "section_ns": {
          "activation_quantization": 982314.0,
          "staging_copies": 0.0,
          "gemm": 578477.0,
          "grid_wait": 426176.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2731793839410188,
          "staging_copies": 0.0,
          "gemm": 0.1608731937894082,
          "grid_wait": 0.11851861739774412,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2163338.0,
        "section_ns": {
          "activation_quantization": 550085.0,
          "staging_copies": 0.0,
          "gemm": 488016.0,
          "grid_wait": 387814.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.25427603083752975,
          "staging_copies": 0.0,
          "gemm": 0.22558472138889069,
          "grid_wait": 0.1792664854035754,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 124617436.0,
        "section_ns": {
          "activation_quantization": 508280.0,
          "staging_copies": 0.0,
          "gemm": 122073534.0,
          "grid_wait": 375554.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004078722980626884,
          "staging_copies": 0.0,
          "gemm": 0.9795863076495973,
          "grid_wait": 0.0030136553282961143,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 155609727.0,
        "section_ns": {
          "activation_quantization": 1489491.0,
          "staging_copies": 0.0,
          "gemm": 151509227.0,
          "grid_wait": 545189.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009571965896450676,
          "staging_copies": 0.0,
          "gemm": 0.9736488195239877,
          "grid_wait": 0.003503566329115146,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 348385859.0,
        "section_ns": {
          "activation_quantization": 812860.0,
          "staging_copies": 0.0,
          "gemm": 345319977.0,
          "grid_wait": 440939.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002333217548878756,
          "staging_copies": 0.0,
          "gemm": 0.9911997518820074,
          "grid_wait": 0.0012656627374763795,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 336044822.0,
        "section_ns": {
          "activation_quantization": 1594491.0,
          "staging_copies": 0.0,
          "gemm": 331475195.0,
          "grid_wait": 1271738.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004744875967765991,
          "staging_copies": 0.0,
          "gemm": 0.9864017336354017,
          "grid_wait": 0.0037844296853947654,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 357201924.0,
        "section_ns": {
          "activation_quantization": 655734.0,
          "staging_copies": 0.0,
          "gemm": 354228724.0,
          "grid_wait": 402632.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001835751590184604,
          "staging_copies": 0.0,
          "gemm": 0.9916764166141502,
          "grid_wait": 0.001127183178330249,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 353530993.0,
        "section_ns": {
          "activation_quantization": 902360.0,
          "staging_copies": 0.0,
          "gemm": 349818843.0,
          "grid_wait": 1174369.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025524211960675255,
          "staging_copies": 0.0,
          "gemm": 0.9894997890609268,
          "grid_wait": 0.0033218275717059975,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3732837.0,
        "section_ns": {
          "activation_quantization": 1033516.0,
          "staging_copies": 0.0,
          "gemm": 594266.0,
          "grid_wait": 471881.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.27687145192785007,
          "staging_copies": 0.0,
          "gemm": 0.15919955786979179,
          "grid_wait": 0.12641350265227225,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2433559.0,
        "section_ns": {
          "activation_quantization": 541020.0,
          "staging_copies": 0.0,
          "gemm": 496678.0,
          "grid_wait": 638302.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2223163687422413,
          "staging_copies": 0.0,
          "gemm": 0.20409531883139057,
          "grid_wait": 0.2622915655630293,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 124295678.0,
        "section_ns": {
          "activation_quantization": 482677.0,
          "staging_copies": 0.0,
          "gemm": 121779643.0,
          "grid_wait": 379182.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0038832967305588856,
          "staging_copies": 0.0,
          "gemm": 0.9797576630138338,
          "grid_wait": 0.003050645091617747,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32934886.0,
        "section_ns": {
          "activation_quantization": 905071.0,
          "staging_copies": 0.0,
          "gemm": 30099845.0,
          "grid_wait": 407803.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.027480617361177444,
          "staging_copies": 0.0,
          "gemm": 0.9139198174239923,
          "grid_wait": 0.012382098422930627,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 122338162.0,
        "section_ns": {
          "activation_quantization": 467220.0,
          "staging_copies": 0.0,
          "gemm": 119526616.0,
          "grid_wait": 428523.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0038190863125767737,
          "staging_copies": 0.0,
          "gemm": 0.9770182422717778,
          "grid_wait": 0.003502774547160517,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 231821275.0,
        "section_ns": {
          "activation_quantization": 666983.0,
          "staging_copies": 0.0,
          "gemm": 228493398.0,
          "grid_wait": 1044645.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002877143178511118,
          "staging_copies": 0.0,
          "gemm": 0.9856446437023522,
          "grid_wait": 0.0045062516371717825,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32941973.0,
        "section_ns": {
          "activation_quantization": 797985.0,
          "staging_copies": 0.0,
          "gemm": 30115026.0,
          "grid_wait": 417382.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.024223958898879554,
          "staging_copies": 0.0,
          "gemm": 0.9141840411319626,
          "grid_wait": 0.012670218629588458,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 343912187.0,
        "section_ns": {
          "activation_quantization": 1549873.0,
          "staging_copies": 0.0,
          "gemm": 339943835.0,
          "grid_wait": 716525.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004506595167562352,
          "staging_copies": 0.0,
          "gemm": 0.988461147496352,
          "grid_wait": 0.0020834533554927497,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 358651078.0,
        "section_ns": {
          "activation_quantization": 693268.0,
          "staging_copies": 0.0,
          "gemm": 355043837.0,
          "grid_wait": 1183292.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019329873588167495,
          "staging_copies": 0.0,
          "gemm": 0.9899421994766735,
          "grid_wait": 0.0032992846601732507,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 351309595.0,
        "section_ns": {
          "activation_quantization": 910193.0,
          "staging_copies": 0.0,
          "gemm": 347405579.0,
          "grid_wait": 1107371.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002590857218118395,
          "staging_copies": 0.0,
          "gemm": 0.9888872491512792,
          "grid_wait": 0.003152122844808722,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32488740.0,
        "section_ns": {
          "activation_quantization": 853265.0,
          "staging_copies": 0.0,
          "gemm": 29717631.0,
          "grid_wait": 412848.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.02626340695268576,
          "staging_copies": 0.0,
          "gemm": 0.9147055564481725,
          "grid_wait": 0.012707418016211156,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 120977758.0,
        "section_ns": {
          "activation_quantization": 459130.0,
          "staging_copies": 0.0,
          "gemm": 118254798.0,
          "grid_wait": 409835.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0037951604294071974,
          "staging_copies": 0.0,
          "gemm": 0.97749206097868,
          "grid_wait": 0.0033876888345046037,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 217893557.0,
        "section_ns": {
          "activation_quantization": 640265.0,
          "staging_copies": 0.0,
          "gemm": 215110673.0,
          "grid_wait": 393022.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0029384301620263144,
          "staging_copies": 0.0,
          "gemm": 0.987228240989246,
          "grid_wait": 0.001803733921329303,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32891346.0,
        "section_ns": {
          "activation_quantization": 807612.0,
          "staging_copies": 0.0,
          "gemm": 30049980.0,
          "grid_wait": 417959.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.02455393585899464,
          "staging_copies": 0.0,
          "gemm": 0.9136135687484483,
          "grid_wait": 0.01270726348505166,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 350336747.0,
        "section_ns": {
          "activation_quantization": 1586413.0,
          "staging_copies": 0.0,
          "gemm": 346512094.0,
          "grid_wait": 543758.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004528251785131749,
          "staging_copies": 0.0,
          "gemm": 0.9890829236934143,
          "grid_wait": 0.001552100956169465,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 353593961.0,
        "section_ns": {
          "activation_quantization": 693969.0,
          "staging_copies": 0.0,
          "gemm": 350747101.0,
          "grid_wait": 420436.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019626155323393658,
          "staging_copies": 0.0,
          "gemm": 0.9919487878357741,
          "grid_wait": 0.001189036144200438,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 341189368.0,
        "section_ns": {
          "activation_quantization": 936026.0,
          "staging_copies": 0.0,
          "gemm": 338191499.0,
          "grid_wait": 406704.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0027434207738853103,
          "staging_copies": 0.0,
          "gemm": 0.9912134747411003,
          "grid_wait": 0.0011920183866925185,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 159377908.0,
        "section_ns": {
          "activation_quantization": 1413785.0,
          "staging_copies": 0.0,
          "gemm": 155090663.0,
          "grid_wait": 627221.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0088706459868955,
          "staging_copies": 0.0,
          "gemm": 0.9731001300380979,
          "grid_wait": 0.0039354325067436574,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 354031924.0,
        "section_ns": {
          "activation_quantization": 654447.0,
          "staging_copies": 0.0,
          "gemm": 351209377.0,
          "grid_wait": 449973.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018485536349541179,
          "staging_copies": 0.0,
          "gemm": 0.9920274223631877,
          "grid_wait": 0.0012709955501075095,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 331585333.0,
        "section_ns": {
          "activation_quantization": 1555915.0,
          "staging_copies": 0.0,
          "gemm": 327794930.0,
          "grid_wait": 573895.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004692351696991374,
          "staging_copies": 0.0,
          "gemm": 0.9885688460170824,
          "grid_wait": 0.0017307611130073718,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 300964540.0,
        "section_ns": {
          "activation_quantization": 652685.0,
          "staging_copies": 0.0,
          "gemm": 298209754.0,
          "grid_wait": 444170.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002168644186454657,
          "staging_copies": 0.0,
          "gemm": 0.9908468087303574,
          "grid_wait": 0.001475821703114925,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 345897403.0,
        "section_ns": {
          "activation_quantization": 907913.0,
          "staging_copies": 0.0,
          "gemm": 342917534.0,
          "grid_wait": 471477.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026248043267326875,
          "staging_copies": 0.0,
          "gemm": 0.9913851073348475,
          "grid_wait": 0.0013630544661822743,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3614455.0,
        "section_ns": {
          "activation_quantization": 1017481.0,
          "staging_copies": 0.0,
          "gemm": 596935.0,
          "grid_wait": 397022.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.28150329717758277,
          "staging_copies": 0.0,
          "gemm": 0.16515214603584774,
          "grid_wait": 0.10984283937689085,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2297099.0,
        "section_ns": {
          "activation_quantization": 586854.0,
          "staging_copies": 0.0,
          "gemm": 500101.0,
          "grid_wait": 400116.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2554761462174682,
          "staging_copies": 0.0,
          "gemm": 0.21770981572844705,
          "grid_wait": 0.17418317625840243,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 125468241.0,
        "section_ns": {
          "activation_quantization": 498886.0,
          "staging_copies": 0.0,
          "gemm": 122886850.0,
          "grid_wait": 403306.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003976193465563927,
          "staging_copies": 0.0,
          "gemm": 0.9794259409438919,
          "grid_wait": 0.0032144070625808804,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 166923734.0,
        "section_ns": {
          "activation_quantization": 1540911.0,
          "staging_copies": 0.0,
          "gemm": 162659918.0,
          "grid_wait": 533255.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009231227717443703,
          "staging_copies": 0.0,
          "gemm": 0.9744565023928832,
          "grid_wait": 0.003194602632121805,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 352526757.0,
        "section_ns": {
          "activation_quantization": 683765.0,
          "staging_copies": 0.0,
          "gemm": 349717187.0,
          "grid_wait": 450600.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019396116363445287,
          "staging_copies": 0.0,
          "gemm": 0.9920301936116582,
          "grid_wait": 0.0012782008487372775,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 344285127.0,
        "section_ns": {
          "activation_quantization": 1554662.0,
          "staging_copies": 0.0,
          "gemm": 340494654.0,
          "grid_wait": 551962.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0045156234704265925,
          "staging_copies": 0.0,
          "gemm": 0.98899030860546,
          "grid_wait": 0.001603211863404137,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 337462442.0,
        "section_ns": {
          "activation_quantization": 680218.0,
          "staging_copies": 0.0,
          "gemm": 334471616.0,
          "grid_wait": 631721.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020156850521457436,
          "staging_copies": 0.0,
          "gemm": 0.9911373070666039,
          "grid_wait": 0.0018719742447664738,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 343194012.0,
        "section_ns": {
          "activation_quantization": 936487.0,
          "staging_copies": 0.0,
          "gemm": 340195216.0,
          "grid_wait": 442453.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0027287393347643837,
          "staging_copies": 0.0,
          "gemm": 0.9912620969622279,
          "grid_wait": 0.0012892212117034257,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3632093.0,
        "section_ns": {
          "activation_quantization": 986224.0,
          "staging_copies": 0.0,
          "gemm": 593018.0,
          "grid_wait": 396727.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2715304921983,
          "staging_copies": 0.0,
          "gemm": 0.16327170036670316,
          "grid_wait": 0.10922820533505062,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2282354.0,
        "section_ns": {
          "activation_quantization": 590534.0,
          "staging_copies": 0.0,
          "gemm": 512549.0,
          "grid_wait": 404223.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2587390036777818,
          "staging_copies": 0.0,
          "gemm": 0.2245703339622162,
          "grid_wait": 0.1771079333004433,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 124198878.0,
        "section_ns": {
          "activation_quantization": 512457.0,
          "staging_copies": 0.0,
          "gemm": 120631445.0,
          "grid_wait": 1184323.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0041261000763630085,
          "staging_copies": 0.0,
          "gemm": 0.9712764474410147,
          "grid_wait": 0.00953569806000985,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 161601144.0,
        "section_ns": {
          "activation_quantization": 1517696.0,
          "staging_copies": 0.0,
          "gemm": 157486273.0,
          "grid_wait": 507808.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00939161668310962,
          "staging_copies": 0.0,
          "gemm": 0.97453686961523,
          "grid_wait": 0.0031423539922464903,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 354876946.0,
        "section_ns": {
          "activation_quantization": 658851.0,
          "staging_copies": 0.0,
          "gemm": 352110084.0,
          "grid_wait": 442253.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018565618517242311,
          "staging_copies": 0.0,
          "gemm": 0.9922033199643236,
          "grid_wait": 0.0012462150753517812,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 344443003.0,
        "section_ns": {
          "activation_quantization": 1573997.0,
          "staging_copies": 0.0,
          "gemm": 340668868.0,
          "grid_wait": 536340.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0045696878330839545,
          "staging_copies": 0.0,
          "gemm": 0.9890427880168029,
          "grid_wait": 0.00155712264533938,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 354612949.0,
        "section_ns": {
          "activation_quantization": 662144.0,
          "staging_copies": 0.0,
          "gemm": 351865783.0,
          "grid_wait": 419850.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018672301783317,
          "staging_copies": 0.0,
          "gemm": 0.9922530578543538,
          "grid_wait": 0.0011839669171246198,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 336179985.0,
        "section_ns": {
          "activation_quantization": 912495.0,
          "staging_copies": 0.0,
          "gemm": 333226830.0,
          "grid_wait": 413422.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0027143049578040764,
          "staging_copies": 0.0,
          "gemm": 0.9912155537754576,
          "grid_wait": 0.0012297638718735738,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3633307.0,
        "section_ns": {
          "activation_quantization": 1023274.0,
          "staging_copies": 0.0,
          "gemm": 601637.0,
          "grid_wait": 395048.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.28163708709448443,
          "staging_copies": 0.0,
          "gemm": 0.16558936528072085,
          "grid_wait": 0.10872959537963624,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2176436.0,
        "section_ns": {
          "activation_quantization": 527598.0,
          "staging_copies": 0.0,
          "gemm": 498054.0,
          "grid_wait": 405005.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2424137443049095,
          "staging_copies": 0.0,
          "gemm": 0.2288392583103753,
          "grid_wait": 0.18608633564230698,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 126898736.0,
        "section_ns": {
          "activation_quantization": 483938.0,
          "staging_copies": 0.0,
          "gemm": 124168911.0,
          "grid_wait": 402817.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00381357620457307,
          "staging_copies": 0.0,
          "gemm": 0.978488162403761,
          "grid_wait": 0.003174318458144453,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32868808.0,
        "section_ns": {
          "activation_quantization": 896522.0,
          "staging_copies": 0.0,
          "gemm": 30042953.0,
          "grid_wait": 392540.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.027275768564530848,
          "staging_copies": 0.0,
          "gemm": 0.9140262403187849,
          "grid_wait": 0.011942629620155376,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 117487077.0,
        "section_ns": {
          "activation_quantization": 475220.0,
          "staging_copies": 0.0,
          "gemm": 114758442.0,
          "grid_wait": 413966.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004044870398809905,
          "staging_copies": 0.0,
          "gemm": 0.9767750201156167,
          "grid_wait": 0.003523502418908592,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 232185155.0,
        "section_ns": {
          "activation_quantization": 663941.0,
          "staging_copies": 0.0,
          "gemm": 229154690.0,
          "grid_wait": 574635.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028595325140403573,
          "staging_copies": 0.0,
          "gemm": 0.9869480673732134,
          "grid_wait": 0.002474899827252091,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 33391308.0,
        "section_ns": {
          "activation_quantization": 1026702.0,
          "staging_copies": 0.0,
          "gemm": 30201488.0,
          "grid_wait": 538136.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.030747582574483154,
          "staging_copies": 0.0,
          "gemm": 0.9044715469067579,
          "grid_wait": 0.01611605032064033,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 337540398.0,
        "section_ns": {
          "activation_quantization": 1536037.0,
          "staging_copies": 0.0,
          "gemm": 333580291.0,
          "grid_wait": 750611.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004550676034931973,
          "staging_copies": 0.0,
          "gemm": 0.9882677539534097,
          "grid_wait": 0.002223766412694696,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 344398204.0,
        "section_ns": {
          "activation_quantization": 684474.0,
          "staging_copies": 0.0,
          "gemm": 341564297.0,
          "grid_wait": 438850.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001987449388673351,
          "staging_copies": 0.0,
          "gemm": 0.9917714234073067,
          "grid_wait": 0.001274251708931676,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 346375808.0,
        "section_ns": {
          "activation_quantization": 891387.0,
          "staging_copies": 0.0,
          "gemm": 343450600.0,
          "grid_wait": 405261.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025734678329498114,
          "staging_copies": 0.0,
          "gemm": 0.9915548143593216,
          "grid_wait": 0.0011700037665448044,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 158797814.0,
        "section_ns": {
          "activation_quantization": 1331564.0,
          "staging_copies": 0.0,
          "gemm": 154105588.0,
          "grid_wait": 1230703.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.008385279157558177,
          "staging_copies": 0.0,
          "gemm": 0.9704515705738871,
          "grid_wait": 0.007750125577925147,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 340183593.0,
        "section_ns": {
          "activation_quantization": 934109.0,
          "staging_copies": 0.0,
          "gemm": 336405033.0,
          "grid_wait": 1166567.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002745896684088465,
          "staging_copies": 0.0,
          "gemm": 0.9888925860101666,
          "grid_wait": 0.0034292276994087718,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 351581190.0,
        "section_ns": {
          "activation_quantization": 1534470.0,
          "staging_copies": 0.0,
          "gemm": 347243907.0,
          "grid_wait": 1135659.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00436448263913095,
          "staging_copies": 0.0,
          "gemm": 0.9876634953081534,
          "grid_wait": 0.003230147210093919,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 355907506.0,
        "section_ns": {
          "activation_quantization": 666177.0,
          "staging_copies": 0.0,
          "gemm": 353169276.0,
          "grid_wait": 411668.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018717700210571,
          "staging_copies": 0.0,
          "gemm": 0.992306343772362,
          "grid_wait": 0.001156671306617512,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 344018022.0,
        "section_ns": {
          "activation_quantization": 937191.0,
          "staging_copies": 0.0,
          "gemm": 341008775.0,
          "grid_wait": 421154.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002724249719684744,
          "staging_copies": 0.0,
          "gemm": 0.9912526472232318,
          "grid_wait": 0.0012242207473653808,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3686214.0,
        "section_ns": {
          "activation_quantization": 1000773.0,
          "staging_copies": 0.0,
          "gemm": 654807.0,
          "grid_wait": 419880.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.27149074904495507,
          "staging_copies": 0.0,
          "gemm": 0.17763672971780803,
          "grid_wait": 0.11390548676772429,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2174272.0,
        "section_ns": {
          "activation_quantization": 558980.0,
          "staging_copies": 0.0,
          "gemm": 470550.0,
          "grid_wait": 401137.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2570883495717187,
          "staging_copies": 0.0,
          "gemm": 0.2164172651811733,
          "grid_wait": 0.18449255658905603,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 124906818.0,
        "section_ns": {
          "activation_quantization": 502023.0,
          "staging_copies": 0.0,
          "gemm": 122327155.0,
          "grid_wait": 407020.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0040191801219369785,
          "staging_copies": 0.0,
          "gemm": 0.9793473003211082,
          "grid_wait": 0.003258589134822088,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 161040253.0,
        "section_ns": {
          "activation_quantization": 1760451.0,
          "staging_copies": 0.0,
          "gemm": 156344121.0,
          "grid_wait": 541630.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.010931745120892228,
          "staging_copies": 0.0,
          "gemm": 0.9708387691119685,
          "grid_wait": 0.003363320597863194,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 339245179.0,
        "section_ns": {
          "activation_quantization": 629272.0,
          "staging_copies": 0.0,
          "gemm": 336525952.0,
          "grid_wait": 456851.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018549180326008405,
          "staging_copies": 0.0,
          "gemm": 0.9919844785767759,
          "grid_wait": 0.0013466691003440907,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 333677582.0,
        "section_ns": {
          "activation_quantization": 1528009.0,
          "staging_copies": 0.0,
          "gemm": 329918975.0,
          "grid_wait": 589312.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004579297748567358,
          "staging_copies": 0.0,
          "gemm": 0.9887358120450537,
          "grid_wait": 0.0017661120548398124,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 356370072.0,
        "section_ns": {
          "activation_quantization": 657111.0,
          "staging_copies": 0.0,
          "gemm": 353592374.0,
          "grid_wait": 422389.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018439006292312896,
          "staging_copies": 0.0,
          "gemm": 0.9922055800465759,
          "grid_wait": 0.0011852538503850571,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 295133306.0,
        "section_ns": {
          "activation_quantization": 898722.0,
          "staging_copies": 0.0,
          "gemm": 292162417.0,
          "grid_wait": 453800.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0030451392022830524,
          "staging_copies": 0.0,
          "gemm": 0.9899337386204727,
          "grid_wait": 0.001537610262123381,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 4084488.0,
        "section_ns": {
          "activation_quantization": 1074069.0,
          "staging_copies": 0.0,
          "gemm": 625889.0,
          "grid_wait": 767193.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2629629466410478,
          "staging_copies": 0.0,
          "gemm": 0.1532356074984184,
          "grid_wait": 0.1878308860253721,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2184980.0,
        "section_ns": {
          "activation_quantization": 547051.0,
          "staging_copies": 0.0,
          "gemm": 477639.0,
          "grid_wait": 408265.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2503688820950306,
          "staging_copies": 0.0,
          "gemm": 0.2186010855934608,
          "grid_wait": 0.18685068055542842,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 126095923.0,
        "section_ns": {
          "activation_quantization": 781280.0,
          "staging_copies": 0.0,
          "gemm": 122394242.0,
          "grid_wait": 1210253.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0061959180075949,
          "staging_copies": 0.0,
          "gemm": 0.9706439279563385,
          "grid_wait": 0.00959787573782223,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "token_embd.weight": {
        "records": 256,
        "worker_elapsed_ns": 10764465116.0,
        "section_ns": {
          "activation_quantization": 522852.0,
          "staging_copies": 0.0,
          "gemm": 10761798544.0,
          "grid_wait": 394053.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 4.857203719512709e-05,
          "staging_copies": 0.0,
          "gemm": 0.9997522801206317,
          "grid_wait": 3.66068351519195e-05,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      }
    },
    "ffn_pairs": {
      "adjacent_same_input_pairs": 1536,
      "pairs_by_layer": {
        "blk.0": 64,
        "blk.1": 64,
        "blk.2": 64,
        "blk.3": 64,
        "blk.4": 64,
        "blk.5": 64,
        "blk.6": 64,
        "blk.7": 64,
        "blk.8": 64,
        "blk.9": 64,
        "blk.10": 64,
        "blk.11": 64,
        "blk.12": 64,
        "blk.13": 64,
        "blk.14": 64,
        "blk.15": 64,
        "blk.16": 64,
        "blk.17": 64,
        "blk.18": 64,
        "blk.19": 64,
        "blk.20": 64,
        "blk.21": 64,
        "blk.22": 64,
        "blk.23": 64
      },
      "smaller_branch_worker_packing_ns": 16099234.0,
      "smaller_branch_input_bytes": 12582912,
      "worker_elapsed_fraction": 0.0003266156884439489,
      "implementation_priority_signal": false,
      "caveat": "Same input addresses/names/shapes in adjacent executions identify a reuse opportunity, not prove a safe lifetime. Worker elapsed overlaps and instrumentation overhead prevent a wall-time savings estimate. No pointer cache is implemented."
    }
  },
  "baseline_timings": {
    "cache_n": 0,
    "prompt_n": 256,
    "prompt_ms": 10378.879,
    "prompt_per_token_ms": 40.54249609375,
    "prompt_per_second": 24.66547687857234,
    "predicted_n": 65,
    "predicted_ms": 14463.469,
    "predicted_per_token_ms": 222.51490769230767,
    "predicted_per_second": 4.494080915166341
  },
  "diagnostic_timings": {
    "cache_n": 0,
    "prompt_n": 256,
    "prompt_ms": 11206.926,
    "prompt_per_token_ms": 43.7770546875,
    "prompt_per_second": 22.843016898657137,
    "predicted_n": 65,
    "predicted_ms": 18519.19,
    "predicted_per_token_ms": 284.91061538461537,
    "predicted_per_second": 3.5098727320147374
  }
}

## 2B-2048

{
  "exact_identity": true,
  "cpu_profile": {
    "samples": 16674,
    "sampled_cpu_s": 83.78893425,
    "multi_frame_samples_pct": 27.701811203070648,
    "unknown_leaf_samples_pct": 0.011994722322178242,
    "cpu_share_pct": {
      "other_or_unattributed": 91.70564951421375,
      "recurrent_visible_stack": 1.9311502938706968,
      "attention_visible_stack": 6.363200191915557
    },
    "attention_copy_visible_cpu_pct": 0.0,
    "top_self": [
      {
        "symbol": "LOOP_INNER360",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 50.419815281276236
      },
      {
        "symbol": "spert::detail::sync_impl(spert::detail::Future*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 20.073167806165287
      },
      {
        "symbol": "ggml_vec_dot_f16",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 6.057334772700012
      },
      {
        "symbol": "ggml_compute_forward_flash_attn_ext_f16_one_chunk(ggml_compute_params const*, ggml_tensor*, int, int, long, long, float*, long)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 5.949382271800408
      },
      {
        "symbol": "LOOP_K360",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 5.613530046779417
      },
      {
        "symbol": "spert::detail::barrier_coro(spert::detail::Tile*, spert::detail::Barrier*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 4.899844068609812
      },
      {
        "symbol": "ggml_gdn_decode_step_rvv(float*, float const*, float const*, float const*, float, float, float, long, float*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 1.8531845987765383
      },
      {
        "symbol": "void spacemit_kernels::rvv::forward_concat<int>(ggml_compute_params*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.6537123665587141
      },
      {
        "symbol": "expf@@GLIBC_2.27",
        "dso": "/usr/lib/riscv64-linux-gnu/libm.so.6",
        "cpu_pct": 0.5637519491423774
      },
      {
        "symbol": "ggml_compute_forward_dup_bytes(ggml_compute_params const*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.33585222502099077
      },
      {
        "symbol": "getenv",
        "dso": "/usr/lib/riscv64-linux-gnu/libc.so.6",
        "cpu_pct": 0.2818759745711887
      },
      {
        "symbol": "ggml_graph_compute_spert_kernel",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.2638838910879213
      },
      {
        "symbol": "ggml_compute_forward_ssm_conv",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.2578865299268322
      },
      {
        "symbol": "$xrv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_v1p0_zicbop1p0_zicsr2p0_zifencei2p0_zihintpause2p0_zmmul1p0_zfh1p0_zfhmin1p0_zba1p0_zve32f1p0_zve32x1p0_zve64d1p0_zve64f1p0_zve64x1p0_zvfh1p0_zvfhmin1p0_zvl128b1p0_zvl32b1p0_zvl64b1p0",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.2518891687657431
      },
      {
        "symbol": "LOOP_MAIN67",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.16192875134940626
      },
      {
        "symbol": "memcpy_main_loop149",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.1439366678661389
      },
      {
        "symbol": "llama_token_data_array_partial_sort_inplace(llama_token_data_array*, int)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libllama.so.0.0.7",
        "cpu_pct": 0.1439366678661389
      },
      {
        "symbol": "spert::detail::worker_main(spert::detail::WorkerPool*, unsigned int)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 0.13793930670504978
      },
      {
        "symbol": "ggml_compute_forward_rms_norm_mul_fused",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.12594458438287154
      },
      {
        "symbol": "__tls_get_addr",
        "dso": "/usr/lib/riscv64-linux-gnu/ld-linux-riscv64-lp64d.so.1",
        "cpu_pct": 0.10195513973851505
      },
      {
        "symbol": "ggml_cpu_extra_compute_forward",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.10195513973851505
      },
      {
        "symbol": "void spacemit_kernels::rvv::forward_binary<(ggml_op)2, float>(ggml_compute_params*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.08396305625524769
      },
      {
        "symbol": "ggml_vec_swiglu_f32",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.07796569509415857
      },
      {
        "symbol": "ggml_is_empty",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libggml-base.so.0.16.0",
        "cpu_pct": 0.07196833393306945
      },
      {
        "symbol": "strncmp",
        "dso": "/usr/lib/riscv64-linux-gnu/libc.so.6",
        "cpu_pct": 0.07196833393306945
      },
      {
        "symbol": "ggml_backend_cpu_get_extra_buffer_types()",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.07196833393306945
      },
      {
        "symbol": "common_sampler_sample(common_sampler*, llama_context*, int, bool)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libllama-common.so.0.0.7",
        "cpu_pct": 0.07196833393306945
      },
      {
        "symbol": "ggml_compute_forward_l2_norm",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.06597097277198033
      },
      {
        "symbol": "spert::detail::ctx_sync(spert::detail::Tile*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 0.05997361161089121
      },
      {
        "symbol": "ggml_compute_forward_gated_delta_net",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.05397625044980209
      }
    ],
    "limitations": "Visible stacks give lower bounds when frames are missing. Attention copy samples exclude inlined K transpose; they are not total packing cost. CPU shares are sampled user CPU time, not wall-time percentages or speedups.",
    "sample_window_verification": {
      "first_sample_ns": 809044281918000,
      "last_sample_ns": 809061390291000,
      "timed_samples": 16674,
      "tolerance_ns": 1000000
    },
    "window": {
      "enable_sent_ns": 809044272309182,
      "enable_ack_ns": 809044276650132,
      "disable_sent_ns": 809061393011203,
      "disable_ack_ns": 809061395894780
    },
    "perf_clockid": "CLOCK_MONOTONIC",
    "scope": "Enabled after receiving first streamed token, disabled after final event; excludes prefill. Pipelining may omit part of the first decode execution."
  },
  "counters": {
    "prefill": {
      "records": 48360,
      "worker_elapsed_ns": 224114700339.0,
      "section_ns": {
        "activation_quantization": 4783985761.0,
        "staging_copies": 0.0,
        "gemm": 216312216119.0,
        "grid_wait": 301773535.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.021346148886100088,
        "staging_copies": 0.0,
        "gemm": 0.9651853082006766,
        "grid_wait": 0.001346513792016016,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 3925868544,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "decode": {
      "records": 47872,
      "worker_elapsed_ns": 49343249291.0,
      "section_ns": {
        "activation_quantization": 177656530.0,
        "staging_copies": 0.0,
        "gemm": 48771364797.0,
        "grid_wait": 91015044.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.003600422196606412,
        "staging_copies": 0.0,
        "gemm": 0.98841007630796,
        "grid_wait": 0.0018445287918361865,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 123207680,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "startup_compatibility_probe": {
      "records": 748,
      "worker_elapsed_ns": 971123516.0,
      "section_ns": {
        "activation_quantization": 2225234.0,
        "staging_copies": 0.0,
        "gemm": 943842222.0,
        "grid_wait": 9144741.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.002291401622283442,
        "staging_copies": 0.0,
        "gemm": 0.9719074931761821,
        "grid_wait": 0.009416661062504845,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 3842048,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "request_only_records": 96236,
    "decode_weights": {
      "blk.0.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 159953982.0,
        "section_ns": {
          "activation_quantization": 1792842.0,
          "staging_copies": 0.0,
          "gemm": 155431406.0,
          "grid_wait": 646134.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.01120848620073741,
          "staging_copies": 0.0,
          "gemm": 0.9717257679774424,
          "grid_wait": 0.0040394993104954395,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 358827301.0,
        "section_ns": {
          "activation_quantization": 844486.0,
          "staging_copies": 0.0,
          "gemm": 355886303.0,
          "grid_wait": 420083.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0023534608365822197,
          "staging_copies": 0.0,
          "gemm": 0.9918038622150437,
          "grid_wait": 0.0011707108094319723,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 353951899.0,
        "section_ns": {
          "activation_quantization": 1552145.0,
          "staging_copies": 0.0,
          "gemm": 350113563.0,
          "grid_wait": 536100.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004385186248146108,
          "staging_copies": 0.0,
          "gemm": 0.9891557694397339,
          "grid_wait": 0.0015146125829939396,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 305644955.0,
        "section_ns": {
          "activation_quantization": 725517.0,
          "staging_copies": 0.0,
          "gemm": 302738519.0,
          "grid_wait": 462511.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0023737247683345533,
          "staging_copies": 0.0,
          "gemm": 0.9904908098352221,
          "grid_wait": 0.0015132296229132917,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 310531876.0,
        "section_ns": {
          "activation_quantization": 972404.0,
          "staging_copies": 0.0,
          "gemm": 307500357.0,
          "grid_wait": 416904.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0031314144381106948,
          "staging_copies": 0.0,
          "gemm": 0.9902376559886561,
          "grid_wait": 0.001342548164040976,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3826057.0,
        "section_ns": {
          "activation_quantization": 971518.0,
          "staging_copies": 0.0,
          "gemm": 628851.0,
          "grid_wait": 584318.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2539214653623822,
          "staging_copies": 0.0,
          "gemm": 0.16436007095555555,
          "grid_wait": 0.15272067300617842,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2313855.0,
        "section_ns": {
          "activation_quantization": 593257.0,
          "staging_copies": 0.0,
          "gemm": 538144.0,
          "grid_wait": 380795.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.25639333493239636,
          "staging_copies": 0.0,
          "gemm": 0.2325746427498698,
          "grid_wait": 0.16457167800056616,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 120596618.0,
        "section_ns": {
          "activation_quantization": 503966.0,
          "staging_copies": 0.0,
          "gemm": 117433452.0,
          "grid_wait": 1004823.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004178939744396481,
          "staging_copies": 0.0,
          "gemm": 0.9737706906507113,
          "grid_wait": 0.008332099329684354,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 165784229.0,
        "section_ns": {
          "activation_quantization": 1579164.0,
          "staging_copies": 0.0,
          "gemm": 161307316.0,
          "grid_wait": 525474.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009525417523279612,
          "staging_copies": 0.0,
          "gemm": 0.9729955435025125,
          "grid_wait": 0.0031696259841459346,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 322611760.0,
        "section_ns": {
          "activation_quantization": 671054.0,
          "staging_copies": 0.0,
          "gemm": 319897878.0,
          "grid_wait": 401137.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020800667650801075,
          "staging_copies": 0.0,
          "gemm": 0.9915877772093615,
          "grid_wait": 0.0012434047661498762,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 304897464.0,
        "section_ns": {
          "activation_quantization": 1567338.0,
          "staging_copies": 0.0,
          "gemm": 301049206.0,
          "grid_wait": 570679.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005140541280461421,
          "staging_copies": 0.0,
          "gemm": 0.9873785175202375,
          "grid_wait": 0.0018717079260455903,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 293723713.0,
        "section_ns": {
          "activation_quantization": 730690.0,
          "staging_copies": 0.0,
          "gemm": 290928370.0,
          "grid_wait": 418407.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024876779356251704,
          "staging_copies": 0.0,
          "gemm": 0.9904830870771404,
          "grid_wait": 0.0014244917297501275,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 348541190.0,
        "section_ns": {
          "activation_quantization": 950109.0,
          "staging_copies": 0.0,
          "gemm": 345584598.0,
          "grid_wait": 397305.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002725959017928412,
          "staging_copies": 0.0,
          "gemm": 0.9915172378908789,
          "grid_wait": 0.001139908313275685,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3543259.0,
        "section_ns": {
          "activation_quantization": 1020737.0,
          "staging_copies": 0.0,
          "gemm": 575597.0,
          "grid_wait": 402059.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2880785739907808,
          "staging_copies": 0.0,
          "gemm": 0.16244846905066776,
          "grid_wait": 0.11347152437910973,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2119438.0,
        "section_ns": {
          "activation_quantization": 549966.0,
          "staging_copies": 0.0,
          "gemm": 500683.0,
          "grid_wait": 359923.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.25948671298712206,
          "staging_copies": 0.0,
          "gemm": 0.23623385067173466,
          "grid_wait": 0.16982001832561272,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 122076603.0,
        "section_ns": {
          "activation_quantization": 500722.0,
          "staging_copies": 0.0,
          "gemm": 119554578.0,
          "grid_wait": 357221.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004101703255946596,
          "staging_copies": 0.0,
          "gemm": 0.9793406358137275,
          "grid_wait": 0.0029262036395295175,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 161324896.0,
        "section_ns": {
          "activation_quantization": 1514216.0,
          "staging_copies": 0.0,
          "gemm": 157219701.0,
          "grid_wait": 533337.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009386127234819354,
          "staging_copies": 0.0,
          "gemm": 0.9745532456441193,
          "grid_wait": 0.00330598074583603,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 332483584.0,
        "section_ns": {
          "activation_quantization": 718219.0,
          "staging_copies": 0.0,
          "gemm": 329646787.0,
          "grid_wait": 430836.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002160163793229563,
          "staging_copies": 0.0,
          "gemm": 0.9914678584552313,
          "grid_wait": 0.0012958113444782886,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 344874201.0,
        "section_ns": {
          "activation_quantization": 1605015.0,
          "staging_copies": 0.0,
          "gemm": 341120122.0,
          "grid_wait": 539508.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004653914370359063,
          "staging_copies": 0.0,
          "gemm": 0.989114642414206,
          "grid_wait": 0.0015643617250453593,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 314718238.0,
        "section_ns": {
          "activation_quantization": 729360.0,
          "staging_copies": 0.0,
          "gemm": 311942709.0,
          "grid_wait": 391213.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0023175015360882897,
          "staging_copies": 0.0,
          "gemm": 0.991180908301857,
          "grid_wait": 0.0012430579253560768,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 344651531.0,
        "section_ns": {
          "activation_quantization": 951887.0,
          "staging_copies": 0.0,
          "gemm": 341692564.0,
          "grid_wait": 393182.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0027618824069578847,
          "staging_copies": 0.0,
          "gemm": 0.9914146123436196,
          "grid_wait": 0.0011408102521964425,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3493482.0,
        "section_ns": {
          "activation_quantization": 965079.0,
          "staging_copies": 0.0,
          "gemm": 587106.0,
          "grid_wait": 408970.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.27625131602223796,
          "staging_copies": 0.0,
          "gemm": 0.16805754258931346,
          "grid_wait": 0.11706658285343964,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2196057.0,
        "section_ns": {
          "activation_quantization": 575051.0,
          "staging_copies": 0.0,
          "gemm": 495429.0,
          "grid_wait": 389124.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.261856135792468,
          "staging_copies": 0.0,
          "gemm": 0.22559933553637268,
          "grid_wait": 0.17719212206240548,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 125239570.0,
        "section_ns": {
          "activation_quantization": 516123.0,
          "staging_copies": 0.0,
          "gemm": 122710891.0,
          "grid_wait": 360975.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004121085692006129,
          "staging_copies": 0.0,
          "gemm": 0.9798092647555401,
          "grid_wait": 0.00288227594521444,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32480224.0,
        "section_ns": {
          "activation_quantization": 925950.0,
          "staging_copies": 0.0,
          "gemm": 29666985.0,
          "grid_wait": 393832.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.028508116200183842,
          "staging_copies": 0.0,
          "gemm": 0.9133860961057412,
          "grid_wait": 0.012125285835467145,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 124511758.0,
        "section_ns": {
          "activation_quantization": 520046.0,
          "staging_copies": 0.0,
          "gemm": 121699226.0,
          "grid_wait": 385893.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004176681852006298,
          "staging_copies": 0.0,
          "gemm": 0.97741151482256,
          "grid_wait": 0.0030992494700781592,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 211335858.0,
        "section_ns": {
          "activation_quantization": 697888.0,
          "staging_copies": 0.0,
          "gemm": 208619987.0,
          "grid_wait": 387887.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0033022696981219344,
          "staging_copies": 0.0,
          "gemm": 0.987149028916806,
          "grid_wait": 0.0018354055183574195,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32161552.0,
        "section_ns": {
          "activation_quantization": 896480.0,
          "staging_copies": 0.0,
          "gemm": 29236808.0,
          "grid_wait": 404969.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.027874276714009324,
          "staging_copies": 0.0,
          "gemm": 0.9090608562671354,
          "grid_wait": 0.012591711992008345,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 304621840.0,
        "section_ns": {
          "activation_quantization": 1576207.0,
          "staging_copies": 0.0,
          "gemm": 300693815.0,
          "grid_wait": 670819.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005174307265690471,
          "staging_copies": 0.0,
          "gemm": 0.9871052416990194,
          "grid_wait": 0.0022021369183509625,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 356067787.0,
        "section_ns": {
          "activation_quantization": 726434.0,
          "staging_copies": 0.0,
          "gemm": 353224086.0,
          "grid_wait": 391148.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020401564716664472,
          "staging_copies": 0.0,
          "gemm": 0.9920135965571073,
          "grid_wait": 0.0010985211644545649,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 342203667.0,
        "section_ns": {
          "activation_quantization": 969742.0,
          "staging_copies": 0.0,
          "gemm": 339115704.0,
          "grid_wait": 405926.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002833815337227231,
          "staging_copies": 0.0,
          "gemm": 0.9909762422271179,
          "grid_wait": 0.0011862117187657138,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 163571192.0,
        "section_ns": {
          "activation_quantization": 1789627.0,
          "staging_copies": 0.0,
          "gemm": 159194920.0,
          "grid_wait": 521501.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.010940966915494508,
          "staging_copies": 0.0,
          "gemm": 0.9732454599951805,
          "grid_wait": 0.0031882203316094928,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 339448672.0,
        "section_ns": {
          "activation_quantization": 675391.0,
          "staging_copies": 0.0,
          "gemm": 336731840.0,
          "grid_wait": 392087.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001989670473655587,
          "staging_copies": 0.0,
          "gemm": 0.9919963392874903,
          "grid_wait": 0.0011550700660864568,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 334022742.0,
        "section_ns": {
          "activation_quantization": 1579243.0,
          "staging_copies": 0.0,
          "gemm": 330125265.0,
          "grid_wait": 551184.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00472795052978758,
          "staging_copies": 0.0,
          "gemm": 0.9883317016779654,
          "grid_wait": 0.0016501391393284233,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 362719400.0,
        "section_ns": {
          "activation_quantization": 711069.0,
          "staging_copies": 0.0,
          "gemm": 359934286.0,
          "grid_wait": 398122.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019603831501706277,
          "staging_copies": 0.0,
          "gemm": 0.9923215741975753,
          "grid_wait": 0.001097603271289046,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 347605989.0,
        "section_ns": {
          "activation_quantization": 961439.0,
          "staging_copies": 0.0,
          "gemm": 344616698.0,
          "grid_wait": 398000.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002765887327677775,
          "staging_copies": 0.0,
          "gemm": 0.991400346672393,
          "grid_wait": 0.001144974518836613,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3651440.0,
        "section_ns": {
          "activation_quantization": 1028537.0,
          "staging_copies": 0.0,
          "gemm": 686934.0,
          "grid_wait": 407757.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.281679830423066,
          "staging_copies": 0.0,
          "gemm": 0.1881268759722192,
          "grid_wait": 0.11167019039064041,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2171887.0,
        "section_ns": {
          "activation_quantization": 574615.0,
          "staging_copies": 0.0,
          "gemm": 492595.0,
          "grid_wait": 373970.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2645694734578733,
          "staging_copies": 0.0,
          "gemm": 0.22680507779640469,
          "grid_wait": 0.17218667453693492,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 125634454.0,
        "section_ns": {
          "activation_quantization": 502098.0,
          "staging_copies": 0.0,
          "gemm": 123132975.0,
          "grid_wait": 359956.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0039964992405666045,
          "staging_copies": 0.0,
          "gemm": 0.9800892277527627,
          "grid_wait": 0.002865105777432678,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 155368238.0,
        "section_ns": {
          "activation_quantization": 1461459.0,
          "staging_copies": 0.0,
          "gemm": 151308427.0,
          "grid_wait": 564930.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00940642063534247,
          "staging_copies": 0.0,
          "gemm": 0.9738697493628009,
          "grid_wait": 0.003636071357132852,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 353213972.0,
        "section_ns": {
          "activation_quantization": 760353.0,
          "staging_copies": 0.0,
          "gemm": 350386643.0,
          "grid_wait": 414842.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021526696571334955,
          "staging_copies": 0.0,
          "gemm": 0.9919954214042246,
          "grid_wait": 0.0011744778884341528,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 350646982.0,
        "section_ns": {
          "activation_quantization": 1542489.0,
          "staging_copies": 0.0,
          "gemm": 346605328.0,
          "grid_wait": 885696.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004398979826382763,
          "staging_copies": 0.0,
          "gemm": 0.9884737236951322,
          "grid_wait": 0.0025258908402639555,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 347722026.0,
        "section_ns": {
          "activation_quantization": 730117.0,
          "staging_copies": 0.0,
          "gemm": 344932661.0,
          "grid_wait": 371304.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002099714557627707,
          "staging_copies": 0.0,
          "gemm": 0.9919781756937077,
          "grid_wait": 0.001067818464856178,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 354380832.0,
        "section_ns": {
          "activation_quantization": 1118699.0,
          "staging_copies": 0.0,
          "gemm": 351182003.0,
          "grid_wait": 427643.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0031567706235307896,
          "staging_copies": 0.0,
          "gemm": 0.9909734705967392,
          "grid_wait": 0.001206732874310764,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3490337.0,
        "section_ns": {
          "activation_quantization": 946495.0,
          "staging_copies": 0.0,
          "gemm": 593893.0,
          "grid_wait": 426050.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2711758205583014,
          "staging_copies": 0.0,
          "gemm": 0.1701534837466984,
          "grid_wait": 0.12206557704886377,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2375028.0,
        "section_ns": {
          "activation_quantization": 573756.0,
          "staging_copies": 0.0,
          "gemm": 498767.0,
          "grid_wait": 558528.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.24157862559936136,
          "staging_copies": 0.0,
          "gemm": 0.21000468205006426,
          "grid_wait": 0.23516691171640924,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 122667634.0,
        "section_ns": {
          "activation_quantization": 519517.0,
          "staging_copies": 0.0,
          "gemm": 120167503.0,
          "grid_wait": 356302.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004235159536866913,
          "staging_copies": 0.0,
          "gemm": 0.9796186580072133,
          "grid_wait": 0.0029046129641662447,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 159938663.0,
        "section_ns": {
          "activation_quantization": 1572116.0,
          "staging_copies": 0.0,
          "gemm": 155800383.0,
          "grid_wait": 532281.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009829493197651652,
          "staging_copies": 0.0,
          "gemm": 0.9741258309755909,
          "grid_wait": 0.003328032071894961,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 358297106.0,
        "section_ns": {
          "activation_quantization": 669322.0,
          "staging_copies": 0.0,
          "gemm": 355447684.0,
          "grid_wait": 388385.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018680642092598985,
          "staging_copies": 0.0,
          "gemm": 0.9920473206389783,
          "grid_wait": 0.0010839747056176335,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 350915093.0,
        "section_ns": {
          "activation_quantization": 1735045.0,
          "staging_copies": 0.0,
          "gemm": 346944652.0,
          "grid_wait": 589677.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004944344186415487,
          "staging_copies": 0.0,
          "gemm": 0.9886854652900324,
          "grid_wait": 0.0016803979417323038,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 351132838.0,
        "section_ns": {
          "activation_quantization": 702517.0,
          "staging_copies": 0.0,
          "gemm": 348403050.0,
          "grid_wait": 380042.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020007157519115314,
          "staging_copies": 0.0,
          "gemm": 0.9922257684141749,
          "grid_wait": 0.0010823311262047213,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 352510124.0,
        "section_ns": {
          "activation_quantization": 962111.0,
          "staging_copies": 0.0,
          "gemm": 349510250.0,
          "grid_wait": 409804.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002729314520339847,
          "staging_copies": 0.0,
          "gemm": 0.991489963562011,
          "grid_wait": 0.001162531150452859,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3642190.0,
        "section_ns": {
          "activation_quantization": 1023233.0,
          "staging_copies": 0.0,
          "gemm": 656769.0,
          "grid_wait": 408766.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2809389405824518,
          "staging_copies": 0.0,
          "gemm": 0.1803225531891527,
          "grid_wait": 0.11223082815558771,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2172181.0,
        "section_ns": {
          "activation_quantization": 574568.0,
          "staging_copies": 0.0,
          "gemm": 490142.0,
          "grid_wait": 384464.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.26451202731264106,
          "staging_copies": 0.0,
          "gemm": 0.22564510047735434,
          "grid_wait": 0.17699445856491702,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 124825899.0,
        "section_ns": {
          "activation_quantization": 501133.0,
          "staging_copies": 0.0,
          "gemm": 122050165.0,
          "grid_wait": 466303.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004014655644498903,
          "staging_copies": 0.0,
          "gemm": 0.9777631563462643,
          "grid_wait": 0.003735627011186196,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32679230.0,
        "section_ns": {
          "activation_quantization": 911529.0,
          "staging_copies": 0.0,
          "gemm": 29820189.0,
          "grid_wait": 431003.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.02789322147431258,
          "staging_copies": 0.0,
          "gemm": 0.9125119839114937,
          "grid_wait": 0.013188897045615823,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 122080856.0,
        "section_ns": {
          "activation_quantization": 506397.0,
          "staging_copies": 0.0,
          "gemm": 119289537.0,
          "grid_wait": 385231.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004148045947515309,
          "staging_copies": 0.0,
          "gemm": 0.9771354896135394,
          "grid_wait": 0.003155539800605592,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 225552758.0,
        "section_ns": {
          "activation_quantization": 691771.0,
          "staging_copies": 0.0,
          "gemm": 222800932.0,
          "grid_wait": 425381.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003067003064533576,
          "staging_copies": 0.0,
          "gemm": 0.987799634886309,
          "grid_wait": 0.0018859490071054684,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32340427.0,
        "section_ns": {
          "activation_quantization": 818654.0,
          "staging_copies": 0.0,
          "gemm": 29517517.0,
          "grid_wait": 414263.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0253136422719465,
          "staging_copies": 0.0,
          "gemm": 0.9127126552781755,
          "grid_wait": 0.012809447444834294,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 352697841.0,
        "section_ns": {
          "activation_quantization": 1572374.0,
          "staging_copies": 0.0,
          "gemm": 348917272.0,
          "grid_wait": 561890.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004458133328919357,
          "staging_copies": 0.0,
          "gemm": 0.9892809976117772,
          "grid_wait": 0.001593120044077616,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 338249649.0,
        "section_ns": {
          "activation_quantization": 727227.0,
          "staging_copies": 0.0,
          "gemm": 334664353.0,
          "grid_wait": 1099111.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021499711888836284,
          "staging_copies": 0.0,
          "gemm": 0.9894004442854574,
          "grid_wait": 0.0032494076586610148,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 337926853.0,
        "section_ns": {
          "activation_quantization": 983569.0,
          "staging_copies": 0.0,
          "gemm": 334838210.0,
          "grid_wait": 412785.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002910597341608718,
          "staging_copies": 0.0,
          "gemm": 0.9908600249652253,
          "grid_wait": 0.0012215217474889455,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 162877163.0,
        "section_ns": {
          "activation_quantization": 1537613.0,
          "staging_copies": 0.0,
          "gemm": 158491372.0,
          "grid_wait": 519060.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009440322827823321,
          "staging_copies": 0.0,
          "gemm": 0.9730730145391837,
          "grid_wait": 0.00318681876844822,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 350742924.0,
        "section_ns": {
          "activation_quantization": 690426.0,
          "staging_copies": 0.0,
          "gemm": 348028813.0,
          "grid_wait": 393423.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019684673667144316,
          "staging_copies": 0.0,
          "gemm": 0.9922618225079289,
          "grid_wait": 0.0011216847813015323,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 349681426.0,
        "section_ns": {
          "activation_quantization": 1571796.0,
          "staging_copies": 0.0,
          "gemm": 345910826.0,
          "grid_wait": 583892.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004494937057366038,
          "staging_copies": 0.0,
          "gemm": 0.9892170423715899,
          "grid_wait": 0.001669782712450961,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 363605236.0,
        "section_ns": {
          "activation_quantization": 727722.0,
          "staging_copies": 0.0,
          "gemm": 360862651.0,
          "grid_wait": 387303.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020014068224254063,
          "staging_copies": 0.0,
          "gemm": 0.9924572455826791,
          "grid_wait": 0.0010651744299963821,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 352476551.0,
        "section_ns": {
          "activation_quantization": 981072.0,
          "staging_copies": 0.0,
          "gemm": 349371257.0,
          "grid_wait": 493519.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002783368133898927,
          "staging_copies": 0.0,
          "gemm": 0.9911900692650616,
          "grid_wait": 0.001400147041270839,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3609640.0,
        "section_ns": {
          "activation_quantization": 1002571.0,
          "staging_copies": 0.0,
          "gemm": 602472.0,
          "grid_wait": 420855.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2777481964960495,
          "staging_copies": 0.0,
          "gemm": 0.16690639509757205,
          "grid_wait": 0.11659195930896156,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2147560.0,
        "section_ns": {
          "activation_quantization": 582147.0,
          "staging_copies": 0.0,
          "gemm": 473685.0,
          "grid_wait": 374173.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2710736836223435,
          "staging_copies": 0.0,
          "gemm": 0.22056892473318557,
          "grid_wait": 0.1742316861927024,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 122605706.0,
        "section_ns": {
          "activation_quantization": 506149.0,
          "staging_copies": 0.0,
          "gemm": 120060443.0,
          "grid_wait": 397007.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0041282662651932365,
          "staging_copies": 0.0,
          "gemm": 0.9792402565668518,
          "grid_wait": 0.0032380793109253823,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 159928776.0,
        "section_ns": {
          "activation_quantization": 1884514.0,
          "staging_copies": 0.0,
          "gemm": 154707225.0,
          "grid_wait": 1207376.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.011783457906286984,
          "staging_copies": 0.0,
          "gemm": 0.9673507724463545,
          "grid_wait": 0.007549460642404967,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 354229543.0,
        "section_ns": {
          "activation_quantization": 835566.0,
          "staging_copies": 0.0,
          "gemm": 351365394.0,
          "grid_wait": 405025.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002358826406525895,
          "staging_copies": 0.0,
          "gemm": 0.9919144265163676,
          "grid_wait": 0.001143397009097008,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 340072040.0,
        "section_ns": {
          "activation_quantization": 1569995.0,
          "staging_copies": 0.0,
          "gemm": 336348145.0,
          "grid_wait": 539807.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004616654165393897,
          "staging_copies": 0.0,
          "gemm": 0.9890496878249679,
          "grid_wait": 0.0015873313195639371,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 332780966.0,
        "section_ns": {
          "activation_quantization": 718843.0,
          "staging_copies": 0.0,
          "gemm": 330036348.0,
          "grid_wait": 384845.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002160108520148956,
          "staging_copies": 0.0,
          "gemm": 0.9917524790164832,
          "grid_wait": 0.0011564513578580092,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 343658221.0,
        "section_ns": {
          "activation_quantization": 1226534.0,
          "staging_copies": 0.0,
          "gemm": 340325760.0,
          "grid_wait": 442600.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003569051822566468,
          "staging_copies": 0.0,
          "gemm": 0.9903029789588534,
          "grid_wait": 0.0012879074992359924,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3597885.0,
        "section_ns": {
          "activation_quantization": 1045284.0,
          "staging_copies": 0.0,
          "gemm": 618679.0,
          "grid_wait": 418298.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2905273514856645,
          "staging_copies": 0.0,
          "gemm": 0.1719563021052646,
          "grid_wait": 0.11626219292723364,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2365355.0,
        "section_ns": {
          "activation_quantization": 562221.0,
          "staging_copies": 0.0,
          "gemm": 500099.0,
          "grid_wait": 399267.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.23768990278414867,
          "staging_copies": 0.0,
          "gemm": 0.21142661460964632,
          "grid_wait": 0.16879791828287932,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 123342936.0,
        "section_ns": {
          "activation_quantization": 496178.0,
          "staging_copies": 0.0,
          "gemm": 120841573.0,
          "grid_wait": 369475.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004022751655595421,
          "staging_copies": 0.0,
          "gemm": 0.9797202573481792,
          "grid_wait": 0.0029955100144527127,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 158212185.0,
        "section_ns": {
          "activation_quantization": 1478877.0,
          "staging_copies": 0.0,
          "gemm": 154186343.0,
          "grid_wait": 529222.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00934742794937065,
          "staging_copies": 0.0,
          "gemm": 0.9745541596559076,
          "grid_wait": 0.003345014165628267,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 348743945.0,
        "section_ns": {
          "activation_quantization": 717601.0,
          "staging_copies": 0.0,
          "gemm": 345951675.0,
          "grid_wait": 408598.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020576730013190624,
          "staging_copies": 0.0,
          "gemm": 0.991993352027947,
          "grid_wait": 0.0011716275102640133,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 353367731.0,
        "section_ns": {
          "activation_quantization": 1555589.0,
          "staging_copies": 0.0,
          "gemm": 349489521.0,
          "grid_wait": 556892.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004402181816652636,
          "staging_copies": 0.0,
          "gemm": 0.9890250023989882,
          "grid_wait": 0.001575956011671026,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 358042456.0,
        "section_ns": {
          "activation_quantization": 735901.0,
          "staging_copies": 0.0,
          "gemm": 355325927.0,
          "grid_wait": 368214.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002055345637557575,
          "staging_copies": 0.0,
          "gemm": 0.992412829946625,
          "grid_wait": 0.0010284087650208724,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 325334858.0,
        "section_ns": {
          "activation_quantization": 959611.0,
          "staging_copies": 0.0,
          "gemm": 322311304.0,
          "grid_wait": 404476.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0029496101521343894,
          "staging_copies": 0.0,
          "gemm": 0.9907063324889704,
          "grid_wait": 0.001243260566932548,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3588142.0,
        "section_ns": {
          "activation_quantization": 951891.0,
          "staging_copies": 0.0,
          "gemm": 695896.0,
          "grid_wait": 419295.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2652879958485478,
          "staging_copies": 0.0,
          "gemm": 0.19394327203326958,
          "grid_wait": 0.11685574316735514,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2132145.0,
        "section_ns": {
          "activation_quantization": 569389.0,
          "staging_copies": 0.0,
          "gemm": 483354.0,
          "grid_wait": 365965.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.26704984886112343,
          "staging_copies": 0.0,
          "gemm": 0.2266984656296828,
          "grid_wait": 0.1716417035426765,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 124762019.0,
        "section_ns": {
          "activation_quantization": 512837.0,
          "staging_copies": 0.0,
          "gemm": 122251666.0,
          "grid_wait": 358002.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004110521808724497,
          "staging_copies": 0.0,
          "gemm": 0.979878868423891,
          "grid_wait": 0.0028694790519541045,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32457219.0,
        "section_ns": {
          "activation_quantization": 929566.0,
          "staging_copies": 0.0,
          "gemm": 29591397.0,
          "grid_wait": 406223.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.028639730347815688,
          "staging_copies": 0.0,
          "gemm": 0.9117046349534752,
          "grid_wait": 0.012515644054408975,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 117578288.0,
        "section_ns": {
          "activation_quantization": 503646.0,
          "staging_copies": 0.0,
          "gemm": 114793308.0,
          "grid_wait": 381921.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004283494925525706,
          "staging_copies": 0.0,
          "gemm": 0.9763138241985629,
          "grid_wait": 0.0032482272577399663,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 219466432.0,
        "section_ns": {
          "activation_quantization": 710105.0,
          "staging_copies": 0.0,
          "gemm": 216733479.0,
          "grid_wait": 400165.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0032355973236034567,
          "staging_copies": 0.0,
          "gemm": 0.9875472846799642,
          "grid_wait": 0.0018233540152509519,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32861866.0,
        "section_ns": {
          "activation_quantization": 877548.0,
          "staging_copies": 0.0,
          "gemm": 29948866.0,
          "grid_wait": 400466.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.026704143946055893,
          "staging_copies": 0.0,
          "gemm": 0.9113562206114528,
          "grid_wait": 0.01218634389173153,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 342394775.0,
        "section_ns": {
          "activation_quantization": 1737671.0,
          "staging_copies": 0.0,
          "gemm": 336927505.0,
          "grid_wait": 2067028.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005075051159878243,
          "staging_copies": 0.0,
          "gemm": 0.9840322621745615,
          "grid_wait": 0.006036972964905788,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 346612785.0,
        "section_ns": {
          "activation_quantization": 749061.0,
          "staging_copies": 0.0,
          "gemm": 343693863.0,
          "grid_wait": 406296.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021610887780726265,
          "staging_copies": 0.0,
          "gemm": 0.9915787237911607,
          "grid_wait": 0.0011721898833016214,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 352630966.0,
        "section_ns": {
          "activation_quantization": 965242.0,
          "staging_copies": 0.0,
          "gemm": 348796684.0,
          "grid_wait": 1168612.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002737258190762521,
          "staging_copies": 0.0,
          "gemm": 0.98912664408491,
          "grid_wait": 0.003313980088748077,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 161370064.0,
        "section_ns": {
          "activation_quantization": 1499333.0,
          "staging_copies": 0.0,
          "gemm": 156607813.0,
          "grid_wait": 1200199.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00929127102533714,
          "staging_copies": 0.0,
          "gemm": 0.9704886341248523,
          "grid_wait": 0.007437556695769793,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 343915875.0,
        "section_ns": {
          "activation_quantization": 730059.0,
          "staging_copies": 0.0,
          "gemm": 341136967.0,
          "grid_wait": 430181.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021227836603936938,
          "staging_copies": 0.0,
          "gemm": 0.9919198030623041,
          "grid_wait": 0.0012508320530420411,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 356702522.0,
        "section_ns": {
          "activation_quantization": 1742891.0,
          "staging_copies": 0.0,
          "gemm": 352809680.0,
          "grid_wait": 555062.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004886119083845446,
          "staging_copies": 0.0,
          "gemm": 0.9890865868338323,
          "grid_wait": 0.0015560921657851356,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 356545285.0,
        "section_ns": {
          "activation_quantization": 740060.0,
          "staging_copies": 0.0,
          "gemm": 353692309.0,
          "grid_wait": 410638.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002075640966616625,
          "staging_copies": 0.0,
          "gemm": 0.991998278703924,
          "grid_wait": 0.0011517134492467064,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 355622589.0,
        "section_ns": {
          "activation_quantization": 962938.0,
          "staging_copies": 0.0,
          "gemm": 352638595.0,
          "grid_wait": 390734.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0027077526281661483,
          "staging_copies": 0.0,
          "gemm": 0.9916090988247094,
          "grid_wait": 0.0010987322292960416,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3500645.0,
        "section_ns": {
          "activation_quantization": 991029.0,
          "staging_copies": 0.0,
          "gemm": 578184.0,
          "grid_wait": 423268.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.28309897176091836,
          "staging_copies": 0.0,
          "gemm": 0.16516499102308288,
          "grid_wait": 0.12091143203609621,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2282431.0,
        "section_ns": {
          "activation_quantization": 606300.0,
          "staging_copies": 0.0,
          "gemm": 480057.0,
          "grid_wait": 401728.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2656378221291246,
          "staging_copies": 0.0,
          "gemm": 0.21032705917506378,
          "grid_wait": 0.17600882567753418,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 122157782.0,
        "section_ns": {
          "activation_quantization": 502348.0,
          "staging_copies": 0.0,
          "gemm": 119669757.0,
          "grid_wait": 354050.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0041122881553301285,
          "staging_copies": 0.0,
          "gemm": 0.9796326933964796,
          "grid_wait": 0.0028983008221285483,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 156783279.0,
        "section_ns": {
          "activation_quantization": 1545870.0,
          "staging_copies": 0.0,
          "gemm": 152323070.0,
          "grid_wait": 524723.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009859916247828953,
          "staging_copies": 0.0,
          "gemm": 0.9715517558476373,
          "grid_wait": 0.0033468046040802603,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 343733201.0,
        "section_ns": {
          "activation_quantization": 647683.0,
          "staging_copies": 0.0,
          "gemm": 341002405.0,
          "grid_wait": 439816.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001884260810755956,
          "staging_copies": 0.0,
          "gemm": 0.9920554779344692,
          "grid_wait": 0.0012795272575371619,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 342978505.0,
        "section_ns": {
          "activation_quantization": 1580586.0,
          "staging_copies": 0.0,
          "gemm": 339195064.0,
          "grid_wait": 566646.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0046084112472296185,
          "staging_copies": 0.0,
          "gemm": 0.9889688684718012,
          "grid_wait": 0.0016521326897730806,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 345947890.0,
        "section_ns": {
          "activation_quantization": 700770.0,
          "staging_copies": 0.0,
          "gemm": 343200027.0,
          "grid_wait": 400887.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020256518980358573,
          "staging_copies": 0.0,
          "gemm": 0.992057003151544,
          "grid_wait": 0.001158807472420196,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 344848354.0,
        "section_ns": {
          "activation_quantization": 951725.0,
          "staging_copies": 0.0,
          "gemm": 341685467.0,
          "grid_wait": 585847.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002759836284444031,
          "staging_copies": 0.0,
          "gemm": 0.9908281800875292,
          "grid_wait": 0.0016988539838006592,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3675484.0,
        "section_ns": {
          "activation_quantization": 1021537.0,
          "staging_copies": 0.0,
          "gemm": 615393.0,
          "grid_wait": 471355.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2779326477818976,
          "staging_copies": 0.0,
          "gemm": 0.16743182666554934,
          "grid_wait": 0.12824297425862824,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2172722.0,
        "section_ns": {
          "activation_quantization": 542758.0,
          "staging_copies": 0.0,
          "gemm": 496231.0,
          "grid_wait": 380774.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2498055434611515,
          "staging_copies": 0.0,
          "gemm": 0.22839139107534237,
          "grid_wait": 0.17525205709704234,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 118396100.0,
        "section_ns": {
          "activation_quantization": 508690.0,
          "staging_copies": 0.0,
          "gemm": 115762538.0,
          "grid_wait": 396968.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0042965097667913045,
          "staging_copies": 0.0,
          "gemm": 0.9777563450147428,
          "grid_wait": 0.0033528807114423533,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 156875140.0,
        "section_ns": {
          "activation_quantization": 1454202.0,
          "staging_copies": 0.0,
          "gemm": 152842539.0,
          "grid_wait": 570722.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009269805273161827,
          "staging_copies": 0.0,
          "gemm": 0.9742941998330646,
          "grid_wait": 0.0036380652791768026,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 344683740.0,
        "section_ns": {
          "activation_quantization": 720277.0,
          "staging_copies": 0.0,
          "gemm": 341882925.0,
          "grid_wait": 462564.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002089675016291746,
          "staging_copies": 0.0,
          "gemm": 0.9918742468095536,
          "grid_wait": 0.0013419954187569162,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 357570569.0,
        "section_ns": {
          "activation_quantization": 1595950.0,
          "staging_copies": 0.0,
          "gemm": 353788308.0,
          "grid_wait": 567537.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004463314764588469,
          "staging_copies": 0.0,
          "gemm": 0.9894223369373557,
          "grid_wait": 0.001587202776747546,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 346858117.0,
        "section_ns": {
          "activation_quantization": 977829.0,
          "staging_copies": 0.0,
          "gemm": 343794847.0,
          "grid_wait": 421898.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028191036970889164,
          "staging_copies": 0.0,
          "gemm": 0.9911685215081762,
          "grid_wait": 0.0012163417239562538,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 345763571.0,
        "section_ns": {
          "activation_quantization": 958253.0,
          "staging_copies": 0.0,
          "gemm": 342669901.0,
          "grid_wait": 525277.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0027714111039187526,
          "staging_copies": 0.0,
          "gemm": 0.9910526433104198,
          "grid_wait": 0.0015191797056029364,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3560142.0,
        "section_ns": {
          "activation_quantization": 977569.0,
          "staging_copies": 0.0,
          "gemm": 617730.0,
          "grid_wait": 420966.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2745870810771031,
          "staging_copies": 0.0,
          "gemm": 0.17351274190748572,
          "grid_wait": 0.11824415992395809,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2379017.0,
        "section_ns": {
          "activation_quantization": 587256.0,
          "staging_copies": 0.0,
          "gemm": 495311.0,
          "grid_wait": 415540.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.24684817300590958,
          "staging_copies": 0.0,
          "gemm": 0.20819985733603416,
          "grid_wait": 0.1746687812655395,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 123484275.0,
        "section_ns": {
          "activation_quantization": 511880.0,
          "staging_copies": 0.0,
          "gemm": 120984291.0,
          "grid_wait": 364224.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0041453051410797045,
          "staging_copies": 0.0,
          "gemm": 0.9797546367746015,
          "grid_wait": 0.0029495577473326057,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 158407572.0,
        "section_ns": {
          "activation_quantization": 1559246.0,
          "staging_copies": 0.0,
          "gemm": 154303248.0,
          "grid_wait": 524277.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009843254210095461,
          "staging_copies": 0.0,
          "gemm": 0.974090102207993,
          "grid_wait": 0.0033096713331355145,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 343677767.0,
        "section_ns": {
          "activation_quantization": 661800.0,
          "staging_copies": 0.0,
          "gemm": 340656020.0,
          "grid_wait": 425817.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019256410031318668,
          "staging_copies": 0.0,
          "gemm": 0.991207615708234,
          "grid_wait": 0.0012390007177857391,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 350170155.0,
        "section_ns": {
          "activation_quantization": 1573290.0,
          "staging_copies": 0.0,
          "gemm": 346300043.0,
          "grid_wait": 548760.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004492930015694799,
          "staging_copies": 0.0,
          "gemm": 0.9889479101952592,
          "grid_wait": 0.0015671238458343202,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 358303741.0,
        "section_ns": {
          "activation_quantization": 707977.0,
          "staging_copies": 0.0,
          "gemm": 355425618.0,
          "grid_wait": 393127.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019759129447660443,
          "staging_copies": 0.0,
          "gemm": 0.9919673654760975,
          "grid_wait": 0.001097189214108708,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 344278742.0,
        "section_ns": {
          "activation_quantization": 982204.0,
          "staging_copies": 0.0,
          "gemm": 341086325.0,
          "grid_wait": 404768.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028529324648223563,
          "staging_copies": 0.0,
          "gemm": 0.9907272317150503,
          "grid_wait": 0.001175698498398719,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3719186.0,
        "section_ns": {
          "activation_quantization": 1020834.0,
          "staging_copies": 0.0,
          "gemm": 611932.0,
          "grid_wait": 448143.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2744778024008479,
          "staging_copies": 0.0,
          "gemm": 0.16453385229993875,
          "grid_wait": 0.12049491474747431,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2273913.0,
        "section_ns": {
          "activation_quantization": 602596.0,
          "staging_copies": 0.0,
          "gemm": 538927.0,
          "grid_wait": 375595.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2650039821224471,
          "staging_copies": 0.0,
          "gemm": 0.23700423015304456,
          "grid_wait": 0.1651756245731477,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 124789904.0,
        "section_ns": {
          "activation_quantization": 482438.0,
          "staging_copies": 0.0,
          "gemm": 122092082.0,
          "grid_wait": 363218.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0038660018522011204,
          "staging_copies": 0.0,
          "gemm": 0.9783810876238834,
          "grid_wait": 0.002910636104023287,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32194300.0,
        "section_ns": {
          "activation_quantization": 918727.0,
          "staging_copies": 0.0,
          "gemm": 29373985.0,
          "grid_wait": 401126.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.02853694598112088,
          "staging_copies": 0.0,
          "gemm": 0.91239707028884,
          "grid_wait": 0.012459534762364766,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 119083868.0,
        "section_ns": {
          "activation_quantization": 516390.0,
          "staging_copies": 0.0,
          "gemm": 115432730.0,
          "grid_wait": 1231282.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0043363556178742865,
          "staging_copies": 0.0,
          "gemm": 0.969339776568225,
          "grid_wait": 0.010339620476553549,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 216726308.0,
        "section_ns": {
          "activation_quantization": 711856.0,
          "staging_copies": 0.0,
          "gemm": 214005020.0,
          "grid_wait": 397760.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00328458509061115,
          "staging_copies": 0.0,
          "gemm": 0.9874436655839678,
          "grid_wait": 0.0018353101830166367,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32469934.0,
        "section_ns": {
          "activation_quantization": 840986.0,
          "staging_copies": 0.0,
          "gemm": 29606277.0,
          "grid_wait": 398678.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.025900453016011675,
          "staging_copies": 0.0,
          "gemm": 0.9118058878715306,
          "grid_wait": 0.01227837420303965,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 343993865.0,
        "section_ns": {
          "activation_quantization": 1533789.0,
          "staging_copies": 0.0,
          "gemm": 340263633.0,
          "grid_wait": 566806.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004458768472513311,
          "staging_copies": 0.0,
          "gemm": 0.9891561089323497,
          "grid_wait": 0.0016477212464239732,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 351668310.0,
        "section_ns": {
          "activation_quantization": 712061.0,
          "staging_copies": 0.0,
          "gemm": 348781417.0,
          "grid_wait": 433346.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002024808547577119,
          "staging_copies": 0.0,
          "gemm": 0.9917908639535931,
          "grid_wait": 0.001232257748786065,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 331586660.0,
        "section_ns": {
          "activation_quantization": 989366.0,
          "staging_copies": 0.0,
          "gemm": 328437326.0,
          "grid_wait": 480216.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0029837328196496205,
          "staging_copies": 0.0,
          "gemm": 0.9905022294925857,
          "grid_wait": 0.001448236789742989,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32741991.0,
        "section_ns": {
          "activation_quantization": 902862.0,
          "staging_copies": 0.0,
          "gemm": 29401488.0,
          "grid_wait": 746900.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.027575048811173394,
          "staging_copies": 0.0,
          "gemm": 0.8979749582119182,
          "grid_wait": 0.022811685459201304,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 116626264.0,
        "section_ns": {
          "activation_quantization": 513230.0,
          "staging_copies": 0.0,
          "gemm": 113816541.0,
          "grid_wait": 397467.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004400638264465026,
          "staging_copies": 0.0,
          "gemm": 0.9759083168436228,
          "grid_wait": 0.00340804023354465,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 216906057.0,
        "section_ns": {
          "activation_quantization": 698481.0,
          "staging_copies": 0.0,
          "gemm": 213988277.0,
          "grid_wait": 453962.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.003220200531329561,
          "staging_copies": 0.0,
          "gemm": 0.9865481856968152,
          "grid_wait": 0.002092896834134973,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32642653.0,
        "section_ns": {
          "activation_quantization": 884260.0,
          "staging_copies": 0.0,
          "gemm": 29720700.0,
          "grid_wait": 418137.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.027089097200524725,
          "staging_copies": 0.0,
          "gemm": 0.9104866568290267,
          "grid_wait": 0.01280952868628662,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 348265122.0,
        "section_ns": {
          "activation_quantization": 1587921.0,
          "staging_copies": 0.0,
          "gemm": 344428971.0,
          "grid_wait": 573734.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004559517734308175,
          "staging_copies": 0.0,
          "gemm": 0.9889849693303483,
          "grid_wait": 0.0016474058519130147,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 343023567.0,
        "section_ns": {
          "activation_quantization": 727568.0,
          "staging_copies": 0.0,
          "gemm": 340127741.0,
          "grid_wait": 413632.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021210437707331053,
          "staging_copies": 0.0,
          "gemm": 0.9915579386415745,
          "grid_wait": 0.0012058413467550468,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 337644829.0,
        "section_ns": {
          "activation_quantization": 946346.0,
          "staging_copies": 0.0,
          "gemm": 334611748.0,
          "grid_wait": 403131.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028027854085690735,
          "staging_copies": 0.0,
          "gemm": 0.9910169481671522,
          "grid_wait": 0.0011939498709159855,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 166345212.0,
        "section_ns": {
          "activation_quantization": 1639923.0,
          "staging_copies": 0.0,
          "gemm": 161783122.0,
          "grid_wait": 856140.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009858552466180993,
          "staging_copies": 0.0,
          "gemm": 0.9725745637932759,
          "grid_wait": 0.005146766713068964,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 364404789.0,
        "section_ns": {
          "activation_quantization": 650811.0,
          "staging_copies": 0.0,
          "gemm": 361672006.0,
          "grid_wait": 440176.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0017859562213382437,
          "staging_copies": 0.0,
          "gemm": 0.9925006940564659,
          "grid_wait": 0.0012079314358297306,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 305071314.0,
        "section_ns": {
          "activation_quantization": 1616914.0,
          "staging_copies": 0.0,
          "gemm": 301284338.0,
          "grid_wait": 537442.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005300118122544947,
          "staging_copies": 0.0,
          "gemm": 0.9875865877051947,
          "grid_wait": 0.001761693005327928,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 349750736.0,
        "section_ns": {
          "activation_quantization": 709444.0,
          "staging_copies": 0.0,
          "gemm": 346996202.0,
          "grid_wait": 411559.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020284274684128183,
          "staging_copies": 0.0,
          "gemm": 0.9921242939142807,
          "grid_wait": 0.0011767208975937652,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 345766058.0,
        "section_ns": {
          "activation_quantization": 966953.0,
          "staging_copies": 0.0,
          "gemm": 342716191.0,
          "grid_wait": 432089.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0027965526911262065,
          "staging_copies": 0.0,
          "gemm": 0.9911793915873605,
          "grid_wait": 0.0012496570730490845,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3651594.0,
        "section_ns": {
          "activation_quantization": 1027323.0,
          "staging_copies": 0.0,
          "gemm": 629891.0,
          "grid_wait": 428384.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2813354934858585,
          "staging_copies": 0.0,
          "gemm": 0.1724975449077855,
          "grid_wait": 0.11731424687410484,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2256058.0,
        "section_ns": {
          "activation_quantization": 572339.0,
          "staging_copies": 0.0,
          "gemm": 518013.0,
          "grid_wait": 376096.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2536898430802754,
          "staging_copies": 0.0,
          "gemm": 0.22960978840083013,
          "grid_wait": 0.16670493400435626,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 119756742.0,
        "section_ns": {
          "activation_quantization": 501783.0,
          "staging_copies": 0.0,
          "gemm": 117057755.0,
          "grid_wait": 395388.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004190018796603535,
          "staging_copies": 0.0,
          "gemm": 0.977462755291055,
          "grid_wait": 0.0033015928238929546,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 161689727.0,
        "section_ns": {
          "activation_quantization": 1489952.0,
          "staging_copies": 0.0,
          "gemm": 157607551.0,
          "grid_wait": 529756.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.009214883515759786,
          "staging_copies": 0.0,
          "gemm": 0.9747530280634341,
          "grid_wait": 0.003276373891088331,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 355228886.0,
        "section_ns": {
          "activation_quantization": 731355.0,
          "staging_copies": 0.0,
          "gemm": 352459192.0,
          "grid_wait": 404572.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002058827501995432,
          "staging_copies": 0.0,
          "gemm": 0.9922030721341732,
          "grid_wait": 0.0011389051283402668,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 346493422.0,
        "section_ns": {
          "activation_quantization": 1588289.0,
          "staging_copies": 0.0,
          "gemm": 342740640.0,
          "grid_wait": 519262.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004583893659025943,
          "staging_copies": 0.0,
          "gemm": 0.9891692547052163,
          "grid_wait": 0.0014986200805855415,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 343760172.0,
        "section_ns": {
          "activation_quantization": 717179.0,
          "staging_copies": 0.0,
          "gemm": 341018563.0,
          "grid_wait": 388222.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020862771734940833,
          "staging_copies": 0.0,
          "gemm": 0.992024646182688,
          "grid_wait": 0.001129339672310846,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 340827371.0,
        "section_ns": {
          "activation_quantization": 954697.0,
          "staging_copies": 0.0,
          "gemm": 336923415.0,
          "grid_wait": 1101870.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002801115993703452,
          "staging_copies": 0.0,
          "gemm": 0.9885456499912385,
          "grid_wait": 0.0032329269705278453,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3496441.0,
        "section_ns": {
          "activation_quantization": 947657.0,
          "staging_copies": 0.0,
          "gemm": 593351.0,
          "grid_wait": 417927.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2710347464750585,
          "staging_copies": 0.0,
          "gemm": 0.16970141924316756,
          "grid_wait": 0.11952925846596582,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2394977.0,
        "section_ns": {
          "activation_quantization": 775049.0,
          "staging_copies": 0.0,
          "gemm": 488056.0,
          "grid_wait": 373928.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.32361438126545683,
          "staging_copies": 0.0,
          "gemm": 0.20378316785505665,
          "grid_wait": 0.15613010062309576,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 124891482.0,
        "section_ns": {
          "activation_quantization": 654008.0,
          "staging_copies": 0.0,
          "gemm": 122232486.0,
          "grid_wait": 351651.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005236610131666145,
          "staging_copies": 0.0,
          "gemm": 0.978709548822553,
          "grid_wait": 0.002815652391729966,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 165011993.0,
        "section_ns": {
          "activation_quantization": 1835226.0,
          "staging_copies": 0.0,
          "gemm": 160634074.0,
          "grid_wait": 504730.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.011121773433764902,
          "staging_copies": 0.0,
          "gemm": 0.973469085971224,
          "grid_wait": 0.0030587473723803823,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 334667585.0,
        "section_ns": {
          "activation_quantization": 652629.0,
          "staging_copies": 0.0,
          "gemm": 332018619.0,
          "grid_wait": 389844.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019500813023167452,
          "staging_copies": 0.0,
          "gemm": 0.9920847846677473,
          "grid_wait": 0.0011648693135309176,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 351387132.0,
        "section_ns": {
          "activation_quantization": 1592533.0,
          "staging_copies": 0.0,
          "gemm": 347601862.0,
          "grid_wait": 528223.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004532132383265532,
          "staging_copies": 0.0,
          "gemm": 0.9892276362584616,
          "grid_wait": 0.0015032508361746155,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 333262328.0,
        "section_ns": {
          "activation_quantization": 717534.0,
          "staging_copies": 0.0,
          "gemm": 330513534.0,
          "grid_wait": 383960.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002153060636364516,
          "staging_copies": 0.0,
          "gemm": 0.9917518610144258,
          "grid_wait": 0.0011521254211487113,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 346263276.0,
        "section_ns": {
          "activation_quantization": 975106.0,
          "staging_copies": 0.0,
          "gemm": 342849731.0,
          "grid_wait": 658716.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028160826388068942,
          "staging_copies": 0.0,
          "gemm": 0.9901417642684117,
          "grid_wait": 0.0019023559402816948,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3743679.0,
        "section_ns": {
          "activation_quantization": 1026567.0,
          "staging_copies": 0.0,
          "gemm": 592891.0,
          "grid_wait": 402847.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.274213414130859,
          "staging_copies": 0.0,
          "gemm": 0.15837121719036273,
          "grid_wait": 0.1076072494463334,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2207392.0,
        "section_ns": {
          "activation_quantization": 601771.0,
          "staging_copies": 0.0,
          "gemm": 485967.0,
          "grid_wait": 372221.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2726162820196866,
          "staging_copies": 0.0,
          "gemm": 0.22015437221843695,
          "grid_wait": 0.16862478436091097,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 119089152.0,
        "section_ns": {
          "activation_quantization": 499288.0,
          "staging_copies": 0.0,
          "gemm": 116607912.0,
          "grid_wait": 342591.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004192556514299472,
          "staging_copies": 0.0,
          "gemm": 0.979164852899448,
          "grid_wait": 0.0028767607649099725,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 32847236.0,
        "section_ns": {
          "activation_quantization": 926783.0,
          "staging_copies": 0.0,
          "gemm": 29817564.0,
          "grid_wait": 574270.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.02821494630476671,
          "staging_copies": 0.0,
          "gemm": 0.9077647811828063,
          "grid_wait": 0.017483053977509707,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 115696115.0,
        "section_ns": {
          "activation_quantization": 521489.0,
          "staging_copies": 0.0,
          "gemm": 112888227.0,
          "grid_wait": 389728.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004507402863095273,
          "staging_copies": 0.0,
          "gemm": 0.975730490172466,
          "grid_wait": 0.0033685487192028876,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 216328127.0,
        "section_ns": {
          "activation_quantization": 708726.0,
          "staging_copies": 0.0,
          "gemm": 213585885.0,
          "grid_wait": 379806.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0032761620498845258,
          "staging_copies": 0.0,
          "gemm": 0.9873236918470616,
          "grid_wait": 0.0017556940249383289,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 32937832.0,
        "section_ns": {
          "activation_quantization": 837802.0,
          "staging_copies": 0.0,
          "gemm": 30067594.0,
          "grid_wait": 389881.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.02543585746627161,
          "staging_copies": 0.0,
          "gemm": 0.9128589276914157,
          "grid_wait": 0.011836874995294165,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 341242392.0,
        "section_ns": {
          "activation_quantization": 1605243.0,
          "staging_copies": 0.0,
          "gemm": 337153368.0,
          "grid_wait": 613853.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0047041136670967895,
          "staging_copies": 0.0,
          "gemm": 0.9880172449383136,
          "grid_wait": 0.0017988767351038847,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 341254601.0,
        "section_ns": {
          "activation_quantization": 721527.0,
          "staging_copies": 0.0,
          "gemm": 338404082.0,
          "grid_wait": 392640.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002114336328025069,
          "staging_copies": 0.0,
          "gemm": 0.9916469433916878,
          "grid_wait": 0.0011505778936003268,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 342377210.0,
        "section_ns": {
          "activation_quantization": 968813.0,
          "staging_copies": 0.0,
          "gemm": 339378575.0,
          "grid_wait": 390548.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028296655609758607,
          "staging_copies": 0.0,
          "gemm": 0.991241721375088,
          "grid_wait": 0.0011406950830635018,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 158508080.0,
        "section_ns": {
          "activation_quantization": 1683088.0,
          "staging_copies": 0.0,
          "gemm": 153969656.0,
          "grid_wait": 550439.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.010618310435657287,
          "staging_copies": 0.0,
          "gemm": 0.9713678697010272,
          "grid_wait": 0.0034726242346762386,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 346641914.0,
        "section_ns": {
          "activation_quantization": 738573.0,
          "staging_copies": 0.0,
          "gemm": 343851685.0,
          "grid_wait": 433351.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002130651171052558,
          "staging_copies": 0.0,
          "gemm": 0.9919506877636268,
          "grid_wait": 0.0012501402239545676,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 346582003.0,
        "section_ns": {
          "activation_quantization": 1582625.0,
          "staging_copies": 0.0,
          "gemm": 342803733.0,
          "grid_wait": 567019.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004566379633970781,
          "staging_copies": 0.0,
          "gemm": 0.989098481838943,
          "grid_wait": 0.001636031285790682,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 349743092.0,
        "section_ns": {
          "activation_quantization": 757520.0,
          "staging_copies": 0.0,
          "gemm": 346935055.0,
          "grid_wait": 399547.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021659327012526096,
          "staging_copies": 0.0,
          "gemm": 0.9919711437788741,
          "grid_wait": 0.0011424014058868102,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 342584416.0,
        "section_ns": {
          "activation_quantization": 950612.0,
          "staging_copies": 0.0,
          "gemm": 339614664.0,
          "grid_wait": 397640.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002774825577588445,
          "staging_copies": 0.0,
          "gemm": 0.9913313278091436,
          "grid_wait": 0.0011607066212842559,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3564895.0,
        "section_ns": {
          "activation_quantization": 977358.0,
          "staging_copies": 0.0,
          "gemm": 649018.0,
          "grid_wait": 428499.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2741617915815192,
          "staging_copies": 0.0,
          "gemm": 0.1820580970828033,
          "grid_wait": 0.12019961317233747,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2267236.0,
        "section_ns": {
          "activation_quantization": 597217.0,
          "staging_copies": 0.0,
          "gemm": 494014.0,
          "grid_wait": 399089.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.26341192535757196,
          "staging_copies": 0.0,
          "gemm": 0.21789262344105334,
          "grid_wait": 0.1760244632671676,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 120836036.0,
        "section_ns": {
          "activation_quantization": 505644.0,
          "staging_copies": 0.0,
          "gemm": 118172430.0,
          "grid_wait": 363713.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004184546404683451,
          "staging_copies": 0.0,
          "gemm": 0.9779568571746263,
          "grid_wait": 0.0030099712969730323,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 174227208.0,
        "section_ns": {
          "activation_quantization": 1713631.0,
          "staging_copies": 0.0,
          "gemm": 169351907.0,
          "grid_wait": 852525.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00983561075030256,
          "staging_copies": 0.0,
          "gemm": 0.9720175680023524,
          "grid_wait": 0.004893179485491153,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 351510418.0,
        "section_ns": {
          "activation_quantization": 684024.0,
          "staging_copies": 0.0,
          "gemm": 348703464.0,
          "grid_wait": 416052.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001945956549145579,
          "staging_copies": 0.0,
          "gemm": 0.9920145922958107,
          "grid_wait": 0.0011836121454585167,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 341438405.0,
        "section_ns": {
          "activation_quantization": 1561632.0,
          "staging_copies": 0.0,
          "gemm": 337704505.0,
          "grid_wait": 532554.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004573685845328384,
          "staging_copies": 0.0,
          "gemm": 0.9890642061779781,
          "grid_wait": 0.0015597366675843042,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1572864,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 346829680.0,
        "section_ns": {
          "activation_quantization": 725316.0,
          "staging_copies": 0.0,
          "gemm": 344019850.0,
          "grid_wait": 406513.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0020912743107798617,
          "staging_copies": 0.0,
          "gemm": 0.9918985307139804,
          "grid_wait": 0.0011720825045884193,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 344503437.0,
        "section_ns": {
          "activation_quantization": 980571.0,
          "staging_copies": 0.0,
          "gemm": 340851133.0,
          "grid_wait": 1018990.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002846331544727085,
          "staging_copies": 0.0,
          "gemm": 0.9893983525046806,
          "grid_wait": 0.002957851477110227,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 3676975.0,
        "section_ns": {
          "activation_quantization": 1032439.0,
          "staging_copies": 0.0,
          "gemm": 649559.0,
          "grid_wait": 438767.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.28078488431387216,
          "staging_copies": 0.0,
          "gemm": 0.1766558108227551,
          "grid_wait": 0.11932825216380312,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 2109125.0,
        "section_ns": {
          "activation_quantization": 534795.0,
          "staging_copies": 0.0,
          "gemm": 478267.0,
          "grid_wait": 387928.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2535624962958573,
          "staging_copies": 0.0,
          "gemm": 0.22676086054643513,
          "grid_wait": 0.18392840632963905,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 121663975.0,
        "section_ns": {
          "activation_quantization": 497024.0,
          "staging_copies": 0.0,
          "gemm": 119098180.0,
          "grid_wait": 395136.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0040852191456016455,
          "staging_copies": 0.0,
          "gemm": 0.9789108074103283,
          "grid_wait": 0.0032477650019243575,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "token_embd.weight": {
        "records": 256,
        "worker_elapsed_ns": 10778590641.0,
        "section_ns": {
          "activation_quantization": 534479.0,
          "staging_copies": 0.0,
          "gemm": 10775909448.0,
          "grid_wait": 421426.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 4.958709517800306e-05,
          "staging_copies": 0.0,
          "gemm": 0.9997512482763933,
          "grid_wait": 3.9098432627820955e-05,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 524288,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      }
    },
    "ffn_pairs": {
      "adjacent_same_input_pairs": 1536,
      "pairs_by_layer": {
        "blk.0": 64,
        "blk.1": 64,
        "blk.2": 64,
        "blk.3": 64,
        "blk.4": 64,
        "blk.5": 64,
        "blk.6": 64,
        "blk.7": 64,
        "blk.8": 64,
        "blk.9": 64,
        "blk.10": 64,
        "blk.11": 64,
        "blk.12": 64,
        "blk.13": 64,
        "blk.14": 64,
        "blk.15": 64,
        "blk.16": 64,
        "blk.17": 64,
        "blk.18": 64,
        "blk.19": 64,
        "blk.20": 64,
        "blk.21": 64,
        "blk.22": 64,
        "blk.23": 64
      },
      "smaller_branch_worker_packing_ns": 17392197.0,
      "smaller_branch_input_bytes": 12582912,
      "worker_elapsed_fraction": 0.0003524736868751824,
      "implementation_priority_signal": false,
      "caveat": "Same input addresses/names/shapes in adjacent executions identify a reuse opportunity, not prove a safe lifetime. Worker elapsed overlaps and instrumentation overhead prevent a wall-time savings estimate. No pointer cache is implemented."
    }
  },
  "baseline_timings": {
    "cache_n": 0,
    "prompt_n": 2048,
    "prompt_ms": 86972.953,
    "prompt_per_token_ms": 42.46726220703125,
    "prompt_per_second": 23.547550466637603,
    "predicted_n": 65,
    "predicted_ms": 17118.587,
    "predicted_per_token_ms": 263.3628769230769,
    "predicted_per_second": 3.7970423610313166
  },
  "diagnostic_timings": {
    "cache_n": 0,
    "prompt_n": 2048,
    "prompt_ms": 93722.469,
    "prompt_per_token_ms": 45.76292431640625,
    "prompt_per_second": 21.85175040576449,
    "predicted_n": 65,
    "predicted_ms": 21166.066,
    "predicted_per_token_ms": 325.6317846153846,
    "predicted_per_second": 3.0709532890996374
  }
}

## 4B-256

{
  "exact_identity": true,
  "cpu_profile": {
    "samples": 30628,
    "sampled_cpu_s": 153.9095285,
    "multi_frame_samples_pct": 28.839623873579733,
    "unknown_leaf_samples_pct": 0.0,
    "cpu_share_pct": {
      "other_or_unattributed": 94.74337207783728,
      "recurrent_visible_stack": 3.6273997649209875,
      "attention_visible_stack": 1.6292281572417395
    },
    "attention_copy_visible_cpu_pct": 0.0,
    "top_self": [
      {
        "symbol": "LOOP_INNER360",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 56.307953506595275
      },
      {
        "symbol": "spert::detail::sync_impl(spert::detail::Future*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 20.043750816246572
      },
      {
        "symbol": "spert::detail::barrier_coro(spert::detail::Tile*, spert::detail::Barrier*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 6.8368812850986025
      },
      {
        "symbol": "LOOP_K360",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 6.291628575159985
      },
      {
        "symbol": "ggml_gdn_decode_step_rvv(float*, float const*, float const*, float const*, float, float, float, long, float*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 3.46088546428105
      },
      {
        "symbol": "ggml_compute_forward_flash_attn_ext_f16_one_chunk(ggml_compute_params const*, ggml_tensor*, int, int, long, long, float*, long)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 1.521483609768839
      },
      {
        "symbol": "ggml_vec_dot_f16",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 1.5182186234817814
      },
      {
        "symbol": "void spacemit_kernels::rvv::forward_concat<int>(ggml_compute_params*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.5517826825127334
      },
      {
        "symbol": "getenv",
        "dso": "/usr/lib/riscv64-linux-gnu/libc.so.6",
        "cpu_pct": 0.26119890296460757
      },
      {
        "symbol": "ggml_compute_forward_dup_bytes(ggml_compute_params const*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.25793391667754995
      },
      {
        "symbol": "expf@@GLIBC_2.27",
        "dso": "/usr/lib/riscv64-linux-gnu/libm.so.6",
        "cpu_pct": 0.2285490400940316
      },
      {
        "symbol": "$xrv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_v1p0_zicbop1p0_zicsr2p0_zifencei2p0_zihintpause2p0_zmmul1p0_zfh1p0_zfhmin1p0_zba1p0_zve32f1p0_zve32x1p0_zve64d1p0_zve64f1p0_zve64x1p0_zvfh1p0_zvfhmin1p0_zvl128b1p0_zvl32b1p0_zvl64b1p0",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.19916416351051325
      },
      {
        "symbol": "ggml_compute_forward_ssm_conv",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.18610421836228289
      },
      {
        "symbol": "ggml_compute_forward_rms_norm_mul_fused",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.1763092595011101
      },
      {
        "symbol": "ggml_graph_compute_spert_kernel",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.1763092595011101
      },
      {
        "symbol": "memcpy_main_loop149",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.13059945148230379
      },
      {
        "symbol": "LOOP_MAIN67",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.1142745200470158
      },
      {
        "symbol": "ggml_compute_forward_gated_delta_net",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.10774454747290062
      },
      {
        "symbol": "llama_token_data_array_partial_sort_inplace(llama_token_data_array*, int)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libllama.so.0.0.7",
        "cpu_pct": 0.08488964346349745
      },
      {
        "symbol": "ggml_vec_swiglu_f32",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.08488964346349745
      },
      {
        "symbol": "ggml_cpu_extra_compute_forward",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.08162465717643985
      },
      {
        "symbol": "ggml_vec_silu_f32",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.07835967088938227
      },
      {
        "symbol": "spert::detail::worker_main(spert::detail::WorkerPool*, unsigned int)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 0.07835967088938227
      },
      {
        "symbol": "ggml_compute_forward_l2_norm",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.06529972574115189
      },
      {
        "symbol": "__tls_get_addr",
        "dso": "/usr/lib/riscv64-linux-gnu/ld-linux-riscv64-lp64d.so.1",
        "cpu_pct": 0.062034739454094295
      },
      {
        "symbol": "void spacemit_kernels::rvv::forward_binary<(ggml_op)2, float>(ggml_compute_params*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.04897479430586391
      },
      {
        "symbol": "ggml_is_empty",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libggml-base.so.0.16.0",
        "cpu_pct": 0.04570980801880632
      },
      {
        "symbol": "ggml::cpu::riscv64_spacemit::extra_buffer_type::get_tensor_traits(ggml_tensor const*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.042444821731748725
      },
      {
        "symbol": "common_sampler_sample(common_sampler*, llama_context*, int, bool)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libllama-common.so.0.0.7",
        "cpu_pct": 0.042444821731748725
      },
      {
        "symbol": "strncmp",
        "dso": "/usr/lib/riscv64-linux-gnu/libc.so.6",
        "cpu_pct": 0.042444821731748725
      }
    ],
    "limitations": "Visible stacks give lower bounds when frames are missing. Attention copy samples exclude inlined K transpose; they are not total packing cost. CPU shares are sampled user CPU time, not wall-time percentages or speedups.",
    "sample_window_verification": {
      "first_sample_ns": 809264885918000,
      "last_sample_ns": 809296076191000,
      "timed_samples": 30628,
      "tolerance_ns": 1000000
    },
    "window": {
      "enable_sent_ns": 809264872439504,
      "enable_ack_ns": 809264880643203,
      "disable_sent_ns": 809296083034871,
      "disable_ack_ns": 809296085995916
    },
    "perf_clockid": "CLOCK_MONOTONIC",
    "scope": "Enabled after receiving first streamed token, disabled after final event; excludes prefill. Pipelining may omit part of the first decode execution."
  },
  "counters": {
    "prefill": {
      "records": 8928,
      "worker_elapsed_ns": 71912894224.0,
      "section_ns": {
        "activation_quantization": 1119981176.0,
        "staging_copies": 0.0,
        "gemm": 70069563692.0,
        "grid_wait": 115137060.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.015574135738597776,
        "staging_copies": 0.0,
        "gemm": 0.9743671764029098,
        "grid_wait": 0.0016010628030261435,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 918552576,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "decode": {
      "records": 63744,
      "worker_elapsed_ns": 99254041991.0,
      "section_ns": {
        "activation_quantization": 276659254.0,
        "staging_copies": 0.0,
        "gemm": 98416997648.0,
        "grid_wait": 145029807.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.0027873852636156266,
        "staging_copies": 0.0,
        "gemm": 0.9915666473001079,
        "grid_wait": 0.0014611979934595588,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 230293504,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "startup_compatibility_probe": {
      "records": 996,
      "worker_elapsed_ns": 2181493097.0,
      "section_ns": {
        "activation_quantization": 3833655.0,
        "staging_copies": 0.0,
        "gemm": 2132016569.0,
        "grid_wait": 14976685.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.0017573537157977081,
        "staging_copies": 0.0,
        "gemm": 0.9773198787252454,
        "grid_wait": 0.006865336874361881,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 7186432,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "request_only_records": 72676,
    "decode_weights": {
      "blk.0.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 329388416.0,
        "section_ns": {
          "activation_quantization": 1701510.0,
          "staging_copies": 0.0,
          "gemm": 324575865.0,
          "grid_wait": 736563.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005165664356575309,
          "staging_copies": 0.0,
          "gemm": 0.9853894345816946,
          "grid_wait": 0.002236153319975891,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 543568703.0,
        "section_ns": {
          "activation_quantization": 975034.0,
          "staging_copies": 0.0,
          "gemm": 539425125.0,
          "grid_wait": 1062773.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0017937640534098226,
          "staging_copies": 0.0,
          "gemm": 0.9923770850361118,
          "grid_wait": 0.0019551769521211747,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525031581.0,
        "section_ns": {
          "activation_quantization": 2279026.0,
          "staging_copies": 0.0,
          "gemm": 520265536.0,
          "grid_wait": 697217.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004340740790600176,
          "staging_copies": 0.0,
          "gemm": 0.9909223651062621,
          "grid_wait": 0.001327952498918346,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 518486770.0,
        "section_ns": {
          "activation_quantization": 761061.0,
          "staging_copies": 0.0,
          "gemm": 515557813.0,
          "grid_wait": 477435.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001467850375430023,
          "staging_copies": 0.0,
          "gemm": 0.9943509513270705,
          "grid_wait": 0.000920823881388526,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 513714833.0,
        "section_ns": {
          "activation_quantization": 983508.0,
          "staging_copies": 0.0,
          "gemm": 510615117.0,
          "grid_wait": 459300.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019145018535993879,
          "staging_copies": 0.0,
          "gemm": 0.993966076506107,
          "grid_wait": 0.0008940757994426063,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5454079.0,
        "section_ns": {
          "activation_quantization": 1058731.0,
          "staging_copies": 0.0,
          "gemm": 1920722.0,
          "grid_wait": 806396.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19411728359636887,
          "staging_copies": 0.0,
          "gemm": 0.352162482428289,
          "grid_wait": 0.14785191046921028,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3756897.0,
        "section_ns": {
          "activation_quantization": 771060.0,
          "staging_copies": 0.0,
          "gemm": 1682137.0,
          "grid_wait": 404974.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2052385253042604,
          "staging_copies": 0.0,
          "gemm": 0.4477463715401301,
          "grid_wait": 0.10779481045128467,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 309648167.0,
        "section_ns": {
          "activation_quantization": 691025.0,
          "staging_copies": 0.0,
          "gemm": 306835438.0,
          "grid_wait": 434304.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0022316456987132756,
          "staging_copies": 0.0,
          "gemm": 0.9909163712246357,
          "grid_wait": 0.0014025724880199276,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 310950662.0,
        "section_ns": {
          "activation_quantization": 1660624.0,
          "staging_copies": 0.0,
          "gemm": 306629383.0,
          "grid_wait": 558216.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005340474238964637,
          "staging_copies": 0.0,
          "gemm": 0.9861030075568709,
          "grid_wait": 0.0017951915471400412,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 545738261.0,
        "section_ns": {
          "activation_quantization": 745322.0,
          "staging_copies": 0.0,
          "gemm": 542825596.0,
          "grid_wait": 512811.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013657132974959217,
          "staging_copies": 0.0,
          "gemm": 0.9946628902385131,
          "grid_wait": 0.0009396647379282795,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 532556590.0,
        "section_ns": {
          "activation_quantization": 2240523.0,
          "staging_copies": 0.0,
          "gemm": 527881025.0,
          "grid_wait": 751937.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004207107830549989,
          "staging_copies": 0.0,
          "gemm": 0.9912205292586841,
          "grid_wait": 0.001411938212988783,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 530045720.0,
        "section_ns": {
          "activation_quantization": 803619.0,
          "staging_copies": 0.0,
          "gemm": 527087644.0,
          "grid_wait": 485308.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001516131476356417,
          "staging_copies": 0.0,
          "gemm": 0.9944192059507622,
          "grid_wait": 0.0009155964885444221,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 521412642.0,
        "section_ns": {
          "activation_quantization": 999452.0,
          "staging_copies": 0.0,
          "gemm": 518291017.0,
          "grid_wait": 461928.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019168158182094864,
          "staging_copies": 0.0,
          "gemm": 0.9940131390216657,
          "grid_wait": 0.0008859163794498102,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5299939.0,
        "section_ns": {
          "activation_quantization": 1210362.0,
          "staging_copies": 0.0,
          "gemm": 1895390.0,
          "grid_wait": 558187.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.22837281712110272,
          "staging_copies": 0.0,
          "gemm": 0.3576248707768146,
          "grid_wait": 0.1053195140547844,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3686193.0,
        "section_ns": {
          "activation_quantization": 692266.0,
          "staging_copies": 0.0,
          "gemm": 1693467.0,
          "grid_wait": 413886.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18779971640117596,
          "staging_copies": 0.0,
          "gemm": 0.4594081210614854,
          "grid_wait": 0.11228006780979727,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 289936857.0,
        "section_ns": {
          "activation_quantization": 685546.0,
          "staging_copies": 0.0,
          "gemm": 287113193.0,
          "grid_wait": 452129.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002364466550039204,
          "staging_copies": 0.0,
          "gemm": 0.9902611070933972,
          "grid_wait": 0.001559405053494113,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 317360272.0,
        "section_ns": {
          "activation_quantization": 1601249.0,
          "staging_copies": 0.0,
          "gemm": 313147742.0,
          "grid_wait": 563632.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0050455244127090996,
          "staging_copies": 0.0,
          "gemm": 0.9867263473986435,
          "grid_wait": 0.0017760004944790317,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 551103968.0,
        "section_ns": {
          "activation_quantization": 659217.0,
          "staging_copies": 0.0,
          "gemm": 548279182.0,
          "grid_wait": 503573.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0011961753830086739,
          "staging_copies": 0.0,
          "gemm": 0.9948743138064287,
          "grid_wait": 0.0009137531740653335,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 527076054.0,
        "section_ns": {
          "activation_quantization": 2225244.0,
          "staging_copies": 0.0,
          "gemm": 522560268.0,
          "grid_wait": 610481.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004221865104879153,
          "staging_copies": 0.0,
          "gemm": 0.9914323825456886,
          "grid_wait": 0.0011582408181267897,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 511629869.0,
        "section_ns": {
          "activation_quantization": 777347.0,
          "staging_copies": 0.0,
          "gemm": 508666766.0,
          "grid_wait": 486711.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015193542189383005,
          "staging_copies": 0.0,
          "gemm": 0.9942085027096024,
          "grid_wait": 0.0009512951246401918,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 527416560.0,
        "section_ns": {
          "activation_quantization": 964826.0,
          "staging_copies": 0.0,
          "gemm": 524302681.0,
          "grid_wait": 481637.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018293433941475026,
          "staging_copies": 0.0,
          "gemm": 0.9940959779495737,
          "grid_wait": 0.0009132003742923809,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5226455.0,
        "section_ns": {
          "activation_quantization": 1123326.0,
          "staging_copies": 0.0,
          "gemm": 1960627.0,
          "grid_wait": 504731.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21493077047444203,
          "staging_copies": 0.0,
          "gemm": 0.37513515375144335,
          "grid_wait": 0.09657234205594423,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3907728.0,
        "section_ns": {
          "activation_quantization": 713475.0,
          "staging_copies": 0.0,
          "gemm": 1831632.0,
          "grid_wait": 424928.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18258051737480194,
          "staging_copies": 0.0,
          "gemm": 0.4687204431833536,
          "grid_wait": 0.10874042410321291,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 312147702.0,
        "section_ns": {
          "activation_quantization": 766097.0,
          "staging_copies": 0.0,
          "gemm": 309058943.0,
          "grid_wait": 410890.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002454277238279973,
          "staging_copies": 0.0,
          "gemm": 0.9901048158285016,
          "grid_wait": 0.0013163319715869637,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65490228.0,
        "section_ns": {
          "activation_quantization": 1025737.0,
          "staging_copies": 0.0,
          "gemm": 62039248.0,
          "grid_wait": 756986.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.015662443563335893,
          "staging_copies": 0.0,
          "gemm": 0.947305420894244,
          "grid_wait": 0.011558762629441449,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 303510132.0,
        "section_ns": {
          "activation_quantization": 767647.0,
          "staging_copies": 0.0,
          "gemm": 300005567.0,
          "grid_wait": 839192.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00252923022681826,
          "staging_copies": 0.0,
          "gemm": 0.9884532190839679,
          "grid_wait": 0.0027649554710746857,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 532152548.0,
        "section_ns": {
          "activation_quantization": 918982.0,
          "staging_copies": 0.0,
          "gemm": 529091147.0,
          "grid_wait": 497057.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001726914591415242,
          "staging_copies": 0.0,
          "gemm": 0.9942471364432892,
          "grid_wait": 0.0009340498356497581,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66807972.0,
        "section_ns": {
          "activation_quantization": 884165.0,
          "staging_copies": 0.0,
          "gemm": 63606330.0,
          "grid_wait": 440763.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.013234423580467313,
          "staging_copies": 0.0,
          "gemm": 0.9520769467452178,
          "grid_wait": 0.006597461153288712,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526350909.0,
        "section_ns": {
          "activation_quantization": 2234282.0,
          "staging_copies": 0.0,
          "gemm": 521853821.0,
          "grid_wait": 580145.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004244852553299191,
          "staging_copies": 0.0,
          "gemm": 0.9914561029094755,
          "grid_wait": 0.0011022019532600446,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 518709432.0,
        "section_ns": {
          "activation_quantization": 825329.0,
          "staging_copies": 0.0,
          "gemm": 515616108.0,
          "grid_wait": 486079.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015911200936095566,
          "staging_copies": 0.0,
          "gemm": 0.9940364994172691,
          "grid_wait": 0.000937093042873375,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 518311050.0,
        "section_ns": {
          "activation_quantization": 985604.0,
          "staging_copies": 0.0,
          "gemm": 515175502.0,
          "grid_wait": 468892.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019015685658254826,
          "staging_copies": 0.0,
          "gemm": 0.9939504511817759,
          "grid_wait": 0.000904653682378564,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 327072807.0,
        "section_ns": {
          "activation_quantization": 1748180.0,
          "staging_copies": 0.0,
          "gemm": 322605141.0,
          "grid_wait": 529061.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005344926152787749,
          "staging_copies": 0.0,
          "gemm": 0.9863404541607154,
          "grid_wait": 0.0016175633946847803,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 542107330.0,
        "section_ns": {
          "activation_quantization": 744893.0,
          "staging_copies": 0.0,
          "gemm": 539241821.0,
          "grid_wait": 446260.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013740692272137328,
          "staging_copies": 0.0,
          "gemm": 0.9947141297646722,
          "grid_wait": 0.0008231949197218934,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 528369504.0,
        "section_ns": {
          "activation_quantization": 2389653.0,
          "staging_copies": 0.0,
          "gemm": 523677621.0,
          "grid_wait": 625438.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004522692891828973,
          "staging_copies": 0.0,
          "gemm": 0.9911200722894106,
          "grid_wait": 0.0011837132825894508,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 529443375.0,
        "section_ns": {
          "activation_quantization": 812062.0,
          "staging_copies": 0.0,
          "gemm": 526534585.0,
          "grid_wait": 435560.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001533803308049704,
          "staging_copies": 0.0,
          "gemm": 0.994505946929641,
          "grid_wait": 0.0008226753238719816,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 522115801.0,
        "section_ns": {
          "activation_quantization": 1000856.0,
          "staging_copies": 0.0,
          "gemm": 519004041.0,
          "grid_wait": 444988.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019169234068056869,
          "staging_copies": 0.0,
          "gemm": 0.994040096097379,
          "grid_wait": 0.0008522783626692041,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5102814.0,
        "section_ns": {
          "activation_quantization": 1161990.0,
          "staging_copies": 0.0,
          "gemm": 1836047.0,
          "grid_wait": 470511.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.22771553107755838,
          "staging_copies": 0.0,
          "gemm": 0.3598106848495752,
          "grid_wait": 0.09220618270624796,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3822898.0,
        "section_ns": {
          "activation_quantization": 755849.0,
          "staging_copies": 0.0,
          "gemm": 1731835.0,
          "grid_wait": 436351.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1977162351702818,
          "staging_copies": 0.0,
          "gemm": 0.453016271948663,
          "grid_wait": 0.11414141836899651,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 294133357.0,
        "section_ns": {
          "activation_quantization": 694816.0,
          "staging_copies": 0.0,
          "gemm": 291367230.0,
          "grid_wait": 410933.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002362248223345848,
          "staging_copies": 0.0,
          "gemm": 0.990595670520974,
          "grid_wait": 0.0013970975757095106,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 324157684.0,
        "section_ns": {
          "activation_quantization": 1684917.0,
          "staging_copies": 0.0,
          "gemm": 319780693.0,
          "grid_wait": 616808.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005197831435641674,
          "staging_copies": 0.0,
          "gemm": 0.9864973399797612,
          "grid_wait": 0.0019028023410976739,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 557473316.0,
        "section_ns": {
          "activation_quantization": 927615.0,
          "staging_copies": 0.0,
          "gemm": 553673788.0,
          "grid_wait": 1108736.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0016639630514620003,
          "staging_copies": 0.0,
          "gemm": 0.9931843769182308,
          "grid_wait": 0.0019888593196808724,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 528153704.0,
        "section_ns": {
          "activation_quantization": 2253273.0,
          "staging_copies": 0.0,
          "gemm": 522233661.0,
          "grid_wait": 1980938.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004266320548231921,
          "staging_copies": 0.0,
          "gemm": 0.9887910603387532,
          "grid_wait": 0.003750684668113205,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 521239791.0,
        "section_ns": {
          "activation_quantization": 747479.0,
          "staging_copies": 0.0,
          "gemm": 518322134.0,
          "grid_wait": 483891.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014340405565852127,
          "staging_copies": 0.0,
          "gemm": 0.9944024668676916,
          "grid_wait": 0.0009283462397827567,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 519492033.0,
        "section_ns": {
          "activation_quantization": 985317.0,
          "staging_copies": 0.0,
          "gemm": 516340288.0,
          "grid_wait": 516142.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018966931875931195,
          "staging_copies": 0.0,
          "gemm": 0.9939330253405445,
          "grid_wait": 0.000993551329400272,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5201205.0,
        "section_ns": {
          "activation_quantization": 1085785.0,
          "staging_copies": 0.0,
          "gemm": 1963969.0,
          "grid_wait": 521686.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20875643240364491,
          "staging_copies": 0.0,
          "gemm": 0.3775988448830607,
          "grid_wait": 0.10030098794413987,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3751898.0,
        "section_ns": {
          "activation_quantization": 714600.0,
          "staging_copies": 0.0,
          "gemm": 1713843.0,
          "grid_wait": 425890.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19046360002324156,
          "staging_copies": 0.0,
          "gemm": 0.45679360153181137,
          "grid_wait": 0.11351321384536574,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 306595383.0,
        "section_ns": {
          "activation_quantization": 693016.0,
          "staging_copies": 0.0,
          "gemm": 303785889.0,
          "grid_wait": 442141.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002260360195965508,
          "staging_copies": 0.0,
          "gemm": 0.9908364764905804,
          "grid_wait": 0.0014420993417242685,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 322952545.0,
        "section_ns": {
          "activation_quantization": 1710377.0,
          "staging_copies": 0.0,
          "gemm": 318651974.0,
          "grid_wait": 573992.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005296062924662817,
          "staging_copies": 0.0,
          "gemm": 0.9866835822581922,
          "grid_wait": 0.0017773261393558611,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 547006169.0,
        "section_ns": {
          "activation_quantization": 709625.0,
          "staging_copies": 0.0,
          "gemm": 544112960.0,
          "grid_wait": 521726.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012972888428247325,
          "staging_copies": 0.0,
          "gemm": 0.9947108293032798,
          "grid_wait": 0.0009537844901343333,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524982908.0,
        "section_ns": {
          "activation_quantization": 2232010.0,
          "staging_copies": 0.0,
          "gemm": 519594108.0,
          "grid_wait": 1413296.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004251586034492384,
          "staging_copies": 0.0,
          "gemm": 0.989735284867598,
          "grid_wait": 0.002692080024822446,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 528560192.0,
        "section_ns": {
          "activation_quantization": 786865.0,
          "staging_copies": 0.0,
          "gemm": 525600641.0,
          "grid_wait": 482678.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001488695160758531,
          "staging_copies": 0.0,
          "gemm": 0.9944007304280682,
          "grid_wait": 0.0009131940076183414,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 526790509.0,
        "section_ns": {
          "activation_quantization": 991438.0,
          "staging_copies": 0.0,
          "gemm": 523547576.0,
          "grid_wait": 460884.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018820346666496225,
          "staging_copies": 0.0,
          "gemm": 0.9938439798276624,
          "grid_wait": 0.0008748904775731257,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5094100.0,
        "section_ns": {
          "activation_quantization": 1132659.0,
          "staging_copies": 0.0,
          "gemm": 1834472.0,
          "grid_wait": 506135.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2223472252213345,
          "staging_copies": 0.0,
          "gemm": 0.36011699809583636,
          "grid_wait": 0.0993570993894898,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3883912.0,
        "section_ns": {
          "activation_quantization": 716398.0,
          "staging_copies": 0.0,
          "gemm": 1835047.0,
          "grid_wait": 442804.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.184452685848701,
          "staging_copies": 0.0,
          "gemm": 0.472473887152953,
          "grid_wait": 0.11400979218890644,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 284979511.0,
        "section_ns": {
          "activation_quantization": 710604.0,
          "staging_copies": 0.0,
          "gemm": 281469646.0,
          "grid_wait": 1138073.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002493526631112789,
          "staging_copies": 0.0,
          "gemm": 0.9876837987836957,
          "grid_wait": 0.00399352569595784,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65618621.0,
        "section_ns": {
          "activation_quantization": 995111.0,
          "staging_copies": 0.0,
          "gemm": 62504811.0,
          "grid_wait": 452680.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.015165070293080373,
          "staging_copies": 0.0,
          "gemm": 0.9525468540401055,
          "grid_wait": 0.006898651527590011,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 277174533.0,
        "section_ns": {
          "activation_quantization": 755312.0,
          "staging_copies": 0.0,
          "gemm": 274006825.0,
          "grid_wait": 519179.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0027250411205707705,
          "staging_copies": 0.0,
          "gemm": 0.9885714319937179,
          "grid_wait": 0.001873112202555781,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 528772821.0,
        "section_ns": {
          "activation_quantization": 709562.0,
          "staging_copies": 0.0,
          "gemm": 525967363.0,
          "grid_wait": 472176.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013419033123867764,
          "staging_copies": 0.0,
          "gemm": 0.9946943982584158,
          "grid_wait": 0.0008929657146655803,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66847725.0,
        "section_ns": {
          "activation_quantization": 911321.0,
          "staging_copies": 0.0,
          "gemm": 63596261.0,
          "grid_wait": 473059.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.013632790046332915,
          "staging_copies": 0.0,
          "gemm": 0.9513601397803739,
          "grid_wait": 0.007076665660648886,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 523272452.0,
        "section_ns": {
          "activation_quantization": 2202933.0,
          "staging_copies": 0.0,
          "gemm": 518759600.0,
          "grid_wait": 628690.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00420991586998354,
          "staging_copies": 0.0,
          "gemm": 0.9913757126278071,
          "grid_wait": 0.0012014582414898462,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 521659992.0,
        "section_ns": {
          "activation_quantization": 786110.0,
          "staging_copies": 0.0,
          "gemm": 518664151.0,
          "grid_wait": 484395.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015069394089167567,
          "staging_copies": 0.0,
          "gemm": 0.9942571003221577,
          "grid_wait": 0.0009285645965351316,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 525957728.0,
        "section_ns": {
          "activation_quantization": 998492.0,
          "staging_copies": 0.0,
          "gemm": 522854928.0,
          "grid_wait": 449925.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001898426331326764,
          "staging_copies": 0.0,
          "gemm": 0.9941006665843686,
          "grid_wait": 0.0008554394698427171,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 318605392.0,
        "section_ns": {
          "activation_quantization": 1548000.0,
          "staging_copies": 0.0,
          "gemm": 314074174.0,
          "grid_wait": 560720.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0048586748337266054,
          "staging_copies": 0.0,
          "gemm": 0.9857779619749812,
          "grid_wait": 0.0017599199953276371,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 535667336.0,
        "section_ns": {
          "activation_quantization": 663906.0,
          "staging_copies": 0.0,
          "gemm": 532698552.0,
          "grid_wait": 634255.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012393998203392414,
          "staging_copies": 0.0,
          "gemm": 0.9944577841498254,
          "grid_wait": 0.0011840464358648145,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525462434.0,
        "section_ns": {
          "activation_quantization": 2254976.0,
          "staging_copies": 0.0,
          "gemm": 520881377.0,
          "grid_wait": 654517.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004291412390481182,
          "staging_copies": 0.0,
          "gemm": 0.9912818563162976,
          "grid_wait": 0.001245601888259818,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 519123615.0,
        "section_ns": {
          "activation_quantization": 763677.0,
          "staging_copies": 0.0,
          "gemm": 516158986.0,
          "grid_wait": 503218.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014710889235890377,
          "staging_copies": 0.0,
          "gemm": 0.994289165596907,
          "grid_wait": 0.0009693606406250657,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 516069226.0,
        "section_ns": {
          "activation_quantization": 966896.0,
          "staging_copies": 0.0,
          "gemm": 512253654.0,
          "grid_wait": 1117078.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018735781001597643,
          "staging_copies": 0.0,
          "gemm": 0.9926064725277768,
          "grid_wait": 0.002164589445990333,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5218529.0,
        "section_ns": {
          "activation_quantization": 1101231.0,
          "staging_copies": 0.0,
          "gemm": 1964597.0,
          "grid_wait": 547193.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21102325961971277,
          "staging_copies": 0.0,
          "gemm": 0.3764656668574612,
          "grid_wait": 0.10485579365372885,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3810474.0,
        "section_ns": {
          "activation_quantization": 710902.0,
          "staging_copies": 0.0,
          "gemm": 1739463.0,
          "grid_wait": 477219.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18656524096477237,
          "staging_copies": 0.0,
          "gemm": 0.45649517619067864,
          "grid_wait": 0.12523874982482494,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 309038938.0,
        "section_ns": {
          "activation_quantization": 692185.0,
          "staging_copies": 0.0,
          "gemm": 306274907.0,
          "grid_wait": 408334.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002239798662523232,
          "staging_copies": 0.0,
          "gemm": 0.9910560429119777,
          "grid_wait": 0.0013213027544121316,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 319631854.0,
        "section_ns": {
          "activation_quantization": 1835297.0,
          "staging_copies": 0.0,
          "gemm": 315071000.0,
          "grid_wait": 583229.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005741908940026985,
          "staging_copies": 0.0,
          "gemm": 0.9857309152923163,
          "grid_wait": 0.0018246898508432142,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 547496441.0,
        "section_ns": {
          "activation_quantization": 734689.0,
          "staging_copies": 0.0,
          "gemm": 544587979.0,
          "grid_wait": 488840.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013419064398995791,
          "staging_copies": 0.0,
          "gemm": 0.9946877061069334,
          "grid_wait": 0.0008928642515139199,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526332495.0,
        "section_ns": {
          "activation_quantization": 2246857.0,
          "staging_copies": 0.0,
          "gemm": 521812857.0,
          "grid_wait": 589049.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00426889280320798,
          "staging_copies": 0.0,
          "gemm": 0.9914129603569318,
          "grid_wait": 0.0011191575773789153,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 519656969.0,
        "section_ns": {
          "activation_quantization": 789563.0,
          "staging_copies": 0.0,
          "gemm": 516612835.0,
          "grid_wait": 449646.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015193926899881526,
          "staging_copies": 0.0,
          "gemm": 0.994142031798673,
          "grid_wait": 0.0008652746462060821,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 530351317.0,
        "section_ns": {
          "activation_quantization": 989271.0,
          "staging_copies": 0.0,
          "gemm": 526999930.0,
          "grid_wait": 688152.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018653126112629225,
          "staging_copies": 0.0,
          "gemm": 0.9936808170498047,
          "grid_wait": 0.0012975399097575919,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5461280.0,
        "section_ns": {
          "activation_quantization": 1184992.0,
          "staging_copies": 0.0,
          "gemm": 1910186.0,
          "grid_wait": 508849.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21698063457650954,
          "staging_copies": 0.0,
          "gemm": 0.3497689186417836,
          "grid_wait": 0.09317394456977118,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3796059.0,
        "section_ns": {
          "activation_quantization": 731939.0,
          "staging_copies": 0.0,
          "gemm": 1761765.0,
          "grid_wait": 428841.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19281549628180172,
          "staging_copies": 0.0,
          "gemm": 0.46410369280351016,
          "grid_wait": 0.11297005657709745,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 283570686.0,
        "section_ns": {
          "activation_quantization": 703220.0,
          "staging_copies": 0.0,
          "gemm": 280731712.0,
          "grid_wait": 442930.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024798755115329517,
          "staging_copies": 0.0,
          "gemm": 0.9899884785693257,
          "grid_wait": 0.0015619738635466714,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 322996554.0,
        "section_ns": {
          "activation_quantization": 1595691.0,
          "staging_copies": 0.0,
          "gemm": 318774867.0,
          "grid_wait": 573680.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0049402725206783476,
          "staging_copies": 0.0,
          "gemm": 0.9869296221655665,
          "grid_wait": 0.0017761180201321901,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 550952533.0,
        "section_ns": {
          "activation_quantization": 680780.0,
          "staging_copies": 0.0,
          "gemm": 548112835.0,
          "grid_wait": 479387.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012356418370437004,
          "staging_copies": 0.0,
          "gemm": 0.9948458391060705,
          "grid_wait": 0.0008701058100045072,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 529027001.0,
        "section_ns": {
          "activation_quantization": 2256016.0,
          "staging_copies": 0.0,
          "gemm": 524439388.0,
          "grid_wait": 604888.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004264462864344423,
          "staging_copies": 0.0,
          "gemm": 0.991328206327223,
          "grid_wait": 0.0011433972157500521,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 521645360.0,
        "section_ns": {
          "activation_quantization": 753024.0,
          "staging_copies": 0.0,
          "gemm": 518749114.0,
          "grid_wait": 475564.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014435554454083517,
          "staging_copies": 0.0,
          "gemm": 0.9944478639664311,
          "grid_wait": 0.0009116615165521649,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 518226094.0,
        "section_ns": {
          "activation_quantization": 973433.0,
          "staging_copies": 0.0,
          "gemm": 515140881.0,
          "grid_wait": 474105.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018783944136938808,
          "staging_copies": 0.0,
          "gemm": 0.9940465888620421,
          "grid_wait": 0.0009148613037613656,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5232572.0,
        "section_ns": {
          "activation_quantization": 1114817.0,
          "staging_copies": 0.0,
          "gemm": 2009807.0,
          "grid_wait": 490309.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21305335120090083,
          "staging_copies": 0.0,
          "gemm": 0.3840954314627682,
          "grid_wait": 0.09370324956828115,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3752858.0,
        "section_ns": {
          "activation_quantization": 718282.0,
          "staging_copies": 0.0,
          "gemm": 1709460.0,
          "grid_wait": 408190.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1913959973971837,
          "staging_copies": 0.0,
          "gemm": 0.4555088415282433,
          "grid_wait": 0.10876777112270168,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 308645636.0,
        "section_ns": {
          "activation_quantization": 846408.0,
          "staging_copies": 0.0,
          "gemm": 305725723.0,
          "grid_wait": 403048.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002742329394218294,
          "staging_copies": 0.0,
          "gemm": 0.9905395940864687,
          "grid_wait": 0.0013058600316642741,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65371386.0,
        "section_ns": {
          "activation_quantization": 1025326.0,
          "staging_copies": 0.0,
          "gemm": 62255309.0,
          "grid_wait": 426733.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.015684629969448714,
          "staging_copies": 0.0,
          "gemm": 0.9523327071572263,
          "grid_wait": 0.006527825492333909,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 310131321.0,
        "section_ns": {
          "activation_quantization": 754606.0,
          "staging_copies": 0.0,
          "gemm": 307073765.0,
          "grid_wait": 464812.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024331821680145618,
          "staging_copies": 0.0,
          "gemm": 0.9901410925212549,
          "grid_wait": 0.0014987586500494093,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 537865859.0,
        "section_ns": {
          "activation_quantization": 743618.0,
          "staging_copies": 0.0,
          "gemm": 535021360.0,
          "grid_wait": 455982.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013825343021074703,
          "staging_copies": 0.0,
          "gemm": 0.99471150854362,
          "grid_wait": 0.0008477615605641183,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66187790.0,
        "section_ns": {
          "activation_quantization": 897824.0,
          "staging_copies": 0.0,
          "gemm": 63138380.0,
          "grid_wait": 431633.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.01356479797859998,
          "staging_copies": 0.0,
          "gemm": 0.9539279072469409,
          "grid_wait": 0.006521338754474202,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524573560.0,
        "section_ns": {
          "activation_quantization": 2269443.0,
          "staging_copies": 0.0,
          "gemm": 519986028.0,
          "grid_wait": 619143.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004326262650370712,
          "staging_copies": 0.0,
          "gemm": 0.9912547403265998,
          "grid_wait": 0.0011802787010462366,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 514982754.0,
        "section_ns": {
          "activation_quantization": 761861.0,
          "staging_copies": 0.0,
          "gemm": 512008906.0,
          "grid_wait": 475932.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014793912885090518,
          "staging_copies": 0.0,
          "gemm": 0.994225344486002,
          "grid_wait": 0.0009241707538812067,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 523277487.0,
        "section_ns": {
          "activation_quantization": 980445.0,
          "staging_copies": 0.0,
          "gemm": 520141980.0,
          "grid_wait": 473399.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001873661727014065,
          "staging_copies": 0.0,
          "gemm": 0.9940079459218164,
          "grid_wait": 0.0009046806173795892,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 323505250.0,
        "section_ns": {
          "activation_quantization": 1630207.0,
          "staging_copies": 0.0,
          "gemm": 317940045.0,
          "grid_wait": 1703127.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005039197972830425,
          "staging_copies": 0.0,
          "gemm": 0.9827971725342942,
          "grid_wait": 0.005264603897463797,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 541265920.0,
        "section_ns": {
          "activation_quantization": 669676.0,
          "staging_copies": 0.0,
          "gemm": 538399718.0,
          "grid_wait": 515970.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012372402829278445,
          "staging_copies": 0.0,
          "gemm": 0.9947046324291025,
          "grid_wait": 0.0009532652637727496,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 532761258.0,
        "section_ns": {
          "activation_quantization": 2220217.0,
          "staging_copies": 0.0,
          "gemm": 528248223.0,
          "grid_wait": 631437.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004167376975448166,
          "staging_copies": 0.0,
          "gemm": 0.9915289730020121,
          "grid_wait": 0.0011852156862352029,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 512915739.0,
        "section_ns": {
          "activation_quantization": 787180.0,
          "staging_copies": 0.0,
          "gemm": 509943069.0,
          "grid_wait": 516222.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015347160169713568,
          "staging_copies": 0.0,
          "gemm": 0.9942043696966765,
          "grid_wait": 0.0010064460119832664,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 522771393.0,
        "section_ns": {
          "activation_quantization": 966945.0,
          "staging_copies": 0.0,
          "gemm": 518949312.0,
          "grid_wait": 1201007.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018496517080841873,
          "staging_copies": 0.0,
          "gemm": 0.992688809963249,
          "grid_wait": 0.002297384700237413,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5163147.0,
        "section_ns": {
          "activation_quantization": 1097580.0,
          "staging_copies": 0.0,
          "gemm": 1916652.0,
          "grid_wait": 508353.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21257965345553786,
          "staging_copies": 0.0,
          "gemm": 0.3712177863616899,
          "grid_wait": 0.09845797533945867,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3846881.0,
        "section_ns": {
          "activation_quantization": 715575.0,
          "staging_copies": 0.0,
          "gemm": 1807225.0,
          "grid_wait": 440878.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18601433213036744,
          "staging_copies": 0.0,
          "gemm": 0.46978968156280376,
          "grid_wait": 0.1146066124738457,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 309414956.0,
        "section_ns": {
          "activation_quantization": 702438.0,
          "staging_copies": 0.0,
          "gemm": 306109362.0,
          "grid_wait": 686637.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0022702134669922032,
          "staging_copies": 0.0,
          "gemm": 0.9893166314817697,
          "grid_wait": 0.002219146122981851,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 324107671.0,
        "section_ns": {
          "activation_quantization": 1735590.0,
          "staging_copies": 0.0,
          "gemm": 318956523.0,
          "grid_wait": 1352835.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005354979703642991,
          "staging_copies": 0.0,
          "gemm": 0.9841066766975719,
          "grid_wait": 0.004174029561922957,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 541311042.0,
        "section_ns": {
          "activation_quantization": 715399.0,
          "staging_copies": 0.0,
          "gemm": 538445844.0,
          "grid_wait": 485012.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013216042986243018,
          "staging_copies": 0.0,
          "gemm": 0.994706928590605,
          "grid_wait": 0.000895995023873908,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524806282.0,
        "section_ns": {
          "activation_quantization": 2215056.0,
          "staging_copies": 0.0,
          "gemm": 520279950.0,
          "grid_wait": 632773.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004220711672045115,
          "staging_copies": 0.0,
          "gemm": 0.9913752328140005,
          "grid_wait": 0.0012057268018754394,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 522072692.0,
        "section_ns": {
          "activation_quantization": 761861.0,
          "staging_copies": 0.0,
          "gemm": 519206567.0,
          "grid_wait": 452142.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014593006140225392,
          "staging_copies": 0.0,
          "gemm": 0.9945101035853452,
          "grid_wait": 0.0008660518102716623,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 525290753.0,
        "section_ns": {
          "activation_quantization": 982163.0,
          "staging_copies": 0.0,
          "gemm": 522141788.0,
          "grid_wait": 463513.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018697511699772868,
          "staging_copies": 0.0,
          "gemm": 0.9940052913895479,
          "grid_wait": 0.0008823932219495971,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5166235.0,
        "section_ns": {
          "activation_quantization": 1154776.0,
          "staging_copies": 0.0,
          "gemm": 1887920.0,
          "grid_wait": 492725.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2235237073032876,
          "staging_copies": 0.0,
          "gemm": 0.365434402422654,
          "grid_wait": 0.09537409738426533,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3644358.0,
        "section_ns": {
          "activation_quantization": 690982.0,
          "staging_copies": 0.0,
          "gemm": 1663674.0,
          "grid_wait": 420432.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18960321680800843,
          "staging_copies": 0.0,
          "gemm": 0.4565067427513982,
          "grid_wait": 0.11536517543007575,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 285611887.0,
        "section_ns": {
          "activation_quantization": 701441.0,
          "staging_copies": 0.0,
          "gemm": 282841352.0,
          "grid_wait": 395882.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024559236919995562,
          "staging_copies": 0.0,
          "gemm": 0.990299650938548,
          "grid_wait": 0.0013860837661844236,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 305422970.0,
        "section_ns": {
          "activation_quantization": 1554175.0,
          "staging_copies": 0.0,
          "gemm": 301244385.0,
          "grid_wait": 543265.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005088598935436978,
          "staging_copies": 0.0,
          "gemm": 0.9863186943667007,
          "grid_wait": 0.0017787300018724853,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 504744448.0,
        "section_ns": {
          "activation_quantization": 676816.0,
          "staging_copies": 0.0,
          "gemm": 501909793.0,
          "grid_wait": 486315.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013409082609661513,
          "staging_copies": 0.0,
          "gemm": 0.9943839798313145,
          "grid_wait": 0.0009634875666824571,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524454902.0,
        "section_ns": {
          "activation_quantization": 2201103.0,
          "staging_copies": 0.0,
          "gemm": 519808709.0,
          "grid_wait": 648615.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004196934744257572,
          "staging_copies": 0.0,
          "gemm": 0.9911409103389408,
          "grid_wait": 0.0012367412288959785,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 504872582.0,
        "section_ns": {
          "activation_quantization": 771183.0,
          "staging_copies": 0.0,
          "gemm": 501905953.0,
          "grid_wait": 461096.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015274804524837515,
          "staging_copies": 0.0,
          "gemm": 0.9941240045394265,
          "grid_wait": 0.0009132918214203995,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 506491834.0,
        "section_ns": {
          "activation_quantization": 1130362.0,
          "staging_copies": 0.0,
          "gemm": 503030363.0,
          "grid_wait": 512777.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0022317477284342553,
          "staging_copies": 0.0,
          "gemm": 0.993165791099408,
          "grid_wait": 0.001012409214873936,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5154035.0,
        "section_ns": {
          "activation_quantization": 1099530.0,
          "staging_copies": 0.0,
          "gemm": 1941641.0,
          "grid_wait": 499936.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21333382485761157,
          "staging_copies": 0.0,
          "gemm": 0.37672250964535553,
          "grid_wait": 0.09699895324731012,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3827278.0,
        "section_ns": {
          "activation_quantization": 734233.0,
          "staging_copies": 0.0,
          "gemm": 1715224.0,
          "grid_wait": 421751.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19184208724843088,
          "staging_copies": 0.0,
          "gemm": 0.4481576723718528,
          "grid_wait": 0.11019607146384454,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 314527642.0,
        "section_ns": {
          "activation_quantization": 681438.0,
          "staging_copies": 0.0,
          "gemm": 311330972.0,
          "grid_wait": 847084.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021665440775472445,
          "staging_copies": 0.0,
          "gemm": 0.989836600752566,
          "grid_wait": 0.00269319413267976,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 314729459.0,
        "section_ns": {
          "activation_quantization": 1674579.0,
          "staging_copies": 0.0,
          "gemm": 309324542.0,
          "grid_wait": 1659420.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005320693542068459,
          "staging_copies": 0.0,
          "gemm": 0.9828267839395358,
          "grid_wait": 0.005272528365385713,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 541013708.0,
        "section_ns": {
          "activation_quantization": 731139.0,
          "staging_copies": 0.0,
          "gemm": 538036576.0,
          "grid_wait": 462262.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013514241676109249,
          "staging_copies": 0.0,
          "gemm": 0.9944971227974874,
          "grid_wait": 0.0008544367604082963,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524884015.0,
        "section_ns": {
          "activation_quantization": 2300863.0,
          "staging_copies": 0.0,
          "gemm": 520287575.0,
          "grid_wait": 633847.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004383564624272278,
          "staging_copies": 0.0,
          "gemm": 0.9912429415477627,
          "grid_wait": 0.0012075944054040205,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 518729967.0,
        "section_ns": {
          "activation_quantization": 805016.0,
          "staging_copies": 0.0,
          "gemm": 515801435.0,
          "grid_wait": 443382.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015518980032244792,
          "staging_copies": 0.0,
          "gemm": 0.9943544190883423,
          "grid_wait": 0.000854745297566354,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 523254321.0,
        "section_ns": {
          "activation_quantization": 1008831.0,
          "staging_copies": 0.0,
          "gemm": 520114647.0,
          "grid_wait": 458560.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019279936342847708,
          "staging_copies": 0.0,
          "gemm": 0.9939997170133259,
          "grid_wait": 0.0008763616115460612,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5124649.0,
        "section_ns": {
          "activation_quantization": 1180576.0,
          "staging_copies": 0.0,
          "gemm": 1883387.0,
          "grid_wait": 471610.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.23037207036033103,
          "staging_copies": 0.0,
          "gemm": 0.3675153166587604,
          "grid_wait": 0.09202776619432862,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3776655.0,
        "section_ns": {
          "activation_quantization": 730410.0,
          "staging_copies": 0.0,
          "gemm": 1751215.0,
          "grid_wait": 432521.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19340130353447693,
          "staging_copies": 0.0,
          "gemm": 0.4636947245644625,
          "grid_wait": 0.11452489041228282,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 284073277.0,
        "section_ns": {
          "activation_quantization": 692598.0,
          "staging_copies": 0.0,
          "gemm": 281312979.0,
          "grid_wait": 398931.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002438096280348116,
          "staging_copies": 0.0,
          "gemm": 0.9902831479639671,
          "grid_wait": 0.0014043242793302236,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 66017793.0,
        "section_ns": {
          "activation_quantization": 1121612.0,
          "staging_copies": 0.0,
          "gemm": 61898929.0,
          "grid_wait": 1123074.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.01698954098632167,
          "staging_copies": 0.0,
          "gemm": 0.9376097895305285,
          "grid_wait": 0.017011686531235602,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 269168628.0,
        "section_ns": {
          "activation_quantization": 774740.0,
          "staging_copies": 0.0,
          "gemm": 266074673.0,
          "grid_wait": 480853.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028782700486179986,
          "staging_copies": 0.0,
          "gemm": 0.9885055140972818,
          "grid_wait": 0.001786437756780482,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 543448851.0,
        "section_ns": {
          "activation_quantization": 714452.0,
          "staging_copies": 0.0,
          "gemm": 540500981.0,
          "grid_wait": 600683.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001314662821874289,
          "staging_copies": 0.0,
          "gemm": 0.9945756256645393,
          "grid_wait": 0.0011053165332757322,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66593423.0,
        "section_ns": {
          "activation_quantization": 909816.0,
          "staging_copies": 0.0,
          "gemm": 63499003.0,
          "grid_wait": 453679.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.013662250099382938,
          "staging_copies": 0.0,
          "gemm": 0.9535326484118409,
          "grid_wait": 0.006812669773710236,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525572796.0,
        "section_ns": {
          "activation_quantization": 2222775.0,
          "staging_copies": 0.0,
          "gemm": 521074538.0,
          "grid_wait": 597932.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004229242869716567,
          "staging_copies": 0.0,
          "gemm": 0.9914412274869722,
          "grid_wait": 0.0011376768442938967,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 522801894.0,
        "section_ns": {
          "activation_quantization": 802899.0,
          "staging_copies": 0.0,
          "gemm": 519802300.0,
          "grid_wait": 448442.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001535761459961352,
          "staging_copies": 0.0,
          "gemm": 0.9942624653153992,
          "grid_wait": 0.0008577665940896534,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 521195252.0,
        "section_ns": {
          "activation_quantization": 1008576.0,
          "staging_copies": 0.0,
          "gemm": 518062757.0,
          "grid_wait": 460721.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019351212355249929,
          "staging_copies": 0.0,
          "gemm": 0.9939897860005832,
          "grid_wait": 0.0008839700634878386,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 308414234.0,
        "section_ns": {
          "activation_quantization": 1574215.0,
          "staging_copies": 0.0,
          "gemm": 304221554.0,
          "grid_wait": 534769.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005104222913395106,
          "staging_copies": 0.0,
          "gemm": 0.9864056858024264,
          "grid_wait": 0.0017339309961939046,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 551695491.0,
        "section_ns": {
          "activation_quantization": 668727.0,
          "staging_copies": 0.0,
          "gemm": 548687482.0,
          "grid_wait": 497564.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001212130624428105,
          "staging_copies": 0.0,
          "gemm": 0.9945477005901431,
          "grid_wait": 0.0009018815780026014,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525173881.0,
        "section_ns": {
          "activation_quantization": 2262816.0,
          "staging_copies": 0.0,
          "gemm": 520640661.0,
          "grid_wait": 617029.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004308698665080795,
          "staging_copies": 0.0,
          "gemm": 0.9913681541218917,
          "grid_wait": 0.0011749042028234454,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 529075486.0,
        "section_ns": {
          "activation_quantization": 761062.0,
          "staging_copies": 0.0,
          "gemm": 526147974.0,
          "grid_wait": 485992.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014384752651344728,
          "staging_copies": 0.0,
          "gemm": 0.9944667404227456,
          "grid_wait": 0.0009185683571814552,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 514800946.0,
        "section_ns": {
          "activation_quantization": 980161.0,
          "staging_copies": 0.0,
          "gemm": 511679019.0,
          "grid_wait": 484388.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019039611477326228,
          "staging_copies": 0.0,
          "gemm": 0.99393566188202,
          "grid_wait": 0.0009409229018782728,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5136860.0,
        "section_ns": {
          "activation_quantization": 1132985.0,
          "staging_copies": 0.0,
          "gemm": 1877726.0,
          "grid_wait": 512518.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.22055983616450517,
          "staging_copies": 0.0,
          "gemm": 0.36553964873483025,
          "grid_wait": 0.09977262374290909,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3791438.0,
        "section_ns": {
          "activation_quantization": 746237.0,
          "staging_copies": 0.0,
          "gemm": 1719959.0,
          "grid_wait": 422886.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1968216280999452,
          "staging_copies": 0.0,
          "gemm": 0.45364291859711275,
          "grid_wait": 0.11153710017149165,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 312391088.0,
        "section_ns": {
          "activation_quantization": 704409.0,
          "staging_copies": 0.0,
          "gemm": 309588331.0,
          "grid_wait": 430929.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0022548946722833526,
          "staging_copies": 0.0,
          "gemm": 0.9910280507105887,
          "grid_wait": 0.0013794535649493305,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 318649597.0,
        "section_ns": {
          "activation_quantization": 1731526.0,
          "staging_copies": 0.0,
          "gemm": 314242073.0,
          "grid_wait": 628468.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005433950070239693,
          "staging_copies": 0.0,
          "gemm": 0.9861681168233205,
          "grid_wait": 0.001972285563568436,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 551937531.0,
        "section_ns": {
          "activation_quantization": 741528.0,
          "staging_copies": 0.0,
          "gemm": 549024984.0,
          "grid_wait": 513099.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001343499867922553,
          "staging_copies": 0.0,
          "gemm": 0.9947230495546787,
          "grid_wait": 0.0009296323789947164,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524901367.0,
        "section_ns": {
          "activation_quantization": 2216519.0,
          "staging_copies": 0.0,
          "gemm": 520372656.0,
          "grid_wait": 628470.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004222734287525679,
          "staging_copies": 0.0,
          "gemm": 0.9913722628960119,
          "grid_wait": 0.0011973106558893758,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 516876745.0,
        "section_ns": {
          "activation_quantization": 757321.0,
          "staging_copies": 0.0,
          "gemm": 513966583.0,
          "grid_wait": 477299.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014651868309532865,
          "staging_copies": 0.0,
          "gemm": 0.994369717678051,
          "grid_wait": 0.0009234290468997595,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 520886137.0,
        "section_ns": {
          "activation_quantization": 997482.0,
          "staging_copies": 0.0,
          "gemm": 517778630.0,
          "grid_wait": 449800.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019149712943886622,
          "staging_copies": 0.0,
          "gemm": 0.9940341913918127,
          "grid_wait": 0.0008635284528603225,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5820714.0,
        "section_ns": {
          "activation_quantization": 1161398.0,
          "staging_copies": 0.0,
          "gemm": 2037320.0,
          "grid_wait": 799442.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19952844273056536,
          "staging_copies": 0.0,
          "gemm": 0.35001204319607526,
          "grid_wait": 0.1373443189271969,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3831711.0,
        "section_ns": {
          "activation_quantization": 709655.0,
          "staging_copies": 0.0,
          "gemm": 1750929.0,
          "grid_wait": 464392.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18520577360870902,
          "staging_copies": 0.0,
          "gemm": 0.45695747930885183,
          "grid_wait": 0.12119703182207635,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 281475331.0,
        "section_ns": {
          "activation_quantization": 706596.0,
          "staging_copies": 0.0,
          "gemm": 278692781.0,
          "grid_wait": 416679.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025103301148618243,
          "staging_copies": 0.0,
          "gemm": 0.9901144089959344,
          "grid_wait": 0.00148033931968269,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 311231392.0,
        "section_ns": {
          "activation_quantization": 1538841.0,
          "staging_copies": 0.0,
          "gemm": 307101686.0,
          "grid_wait": 531069.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004944363067334801,
          "staging_copies": 0.0,
          "gemm": 0.9867310749938747,
          "grid_wait": 0.0017063477966901231,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 535371456.0,
        "section_ns": {
          "activation_quantization": 884147.0,
          "staging_copies": 0.0,
          "gemm": 532300284.0,
          "grid_wait": 530385.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001651464586113459,
          "staging_copies": 0.0,
          "gemm": 0.9942634745174013,
          "grid_wait": 0.0009906859883093953,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 527474688.0,
        "section_ns": {
          "activation_quantization": 2227269.0,
          "staging_copies": 0.0,
          "gemm": 522961314.0,
          "grid_wait": 621219.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0042225135170846344,
          "staging_copies": 0.0,
          "gemm": 0.99144343017271,
          "grid_wait": 0.0011777228635471509,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 520354285.0,
        "section_ns": {
          "activation_quantization": 813140.0,
          "staging_copies": 0.0,
          "gemm": 517282405.0,
          "grid_wait": 477254.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001562666097772213,
          "staging_copies": 0.0,
          "gemm": 0.9940965605769922,
          "grid_wait": 0.0009171712691863391,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 517254695.0,
        "section_ns": {
          "activation_quantization": 969246.0,
          "staging_copies": 0.0,
          "gemm": 514142929.0,
          "grid_wait": 489638.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018738273608130324,
          "staging_copies": 0.0,
          "gemm": 0.9939840739386618,
          "grid_wait": 0.0009466090974775976,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5167272.0,
        "section_ns": {
          "activation_quantization": 1150242.0,
          "staging_copies": 0.0,
          "gemm": 1906970.0,
          "grid_wait": 498513.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.22260140360329397,
          "staging_copies": 0.0,
          "gemm": 0.369047729633741,
          "grid_wait": 0.09647508395145446,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3754315.0,
        "section_ns": {
          "activation_quantization": 723977.0,
          "staging_copies": 0.0,
          "gemm": 1714798.0,
          "grid_wait": 403161.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19283864033785125,
          "staging_copies": 0.0,
          "gemm": 0.4567538951846076,
          "grid_wait": 0.10738603446967024,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 314694079.0,
        "section_ns": {
          "activation_quantization": 695295.0,
          "staging_copies": 0.0,
          "gemm": 311915199.0,
          "grid_wait": 408542.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0022094314650260706,
          "staging_copies": 0.0,
          "gemm": 0.99116958282523,
          "grid_wait": 0.0012982195321190012,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 64958405.0,
        "section_ns": {
          "activation_quantization": 1028402.0,
          "staging_copies": 0.0,
          "gemm": 61753240.0,
          "grid_wait": 445009.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.01583170030113886,
          "staging_copies": 0.0,
          "gemm": 0.9506581942706259,
          "grid_wait": 0.00685067621349385,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 308829827.0,
        "section_ns": {
          "activation_quantization": 782688.0,
          "staging_copies": 0.0,
          "gemm": 304903038.0,
          "grid_wait": 1270652.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002534366604427752,
          "staging_copies": 0.0,
          "gemm": 0.9872849425259692,
          "grid_wait": 0.004114408288678671,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 529587265.0,
        "section_ns": {
          "activation_quantization": 748561.0,
          "staging_copies": 0.0,
          "gemm": 526712513.0,
          "grid_wait": 464646.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014134799861548785,
          "staging_copies": 0.0,
          "gemm": 0.9945717123692542,
          "grid_wait": 0.0008773738167589812,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66027322.0,
        "section_ns": {
          "activation_quantization": 880273.0,
          "staging_copies": 0.0,
          "gemm": 62925704.0,
          "grid_wait": 482343.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.01333195067338942,
          "staging_copies": 0.0,
          "gemm": 0.9530252340084306,
          "grid_wait": 0.007305203139997106,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 531052329.0,
        "section_ns": {
          "activation_quantization": 2239395.0,
          "staging_copies": 0.0,
          "gemm": 525898389.0,
          "grid_wait": 1223453.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004216900816943785,
          "staging_copies": 0.0,
          "gemm": 0.9902948547279603,
          "grid_wait": 0.002303827576283918,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 522754638.0,
        "section_ns": {
          "activation_quantization": 756192.0,
          "staging_copies": 0.0,
          "gemm": 519751136.0,
          "grid_wait": 497591.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014465524455088623,
          "staging_copies": 0.0,
          "gemm": 0.9942544708709021,
          "grid_wait": 0.0009518633864325466,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 521337425.0,
        "section_ns": {
          "activation_quantization": 972575.0,
          "staging_copies": 0.0,
          "gemm": 518212759.0,
          "grid_wait": 497718.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018655384274397719,
          "staging_copies": 0.0,
          "gemm": 0.9940064421808966,
          "grid_wait": 0.0009546945531485678,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 323131566.0,
        "section_ns": {
          "activation_quantization": 1777141.0,
          "staging_copies": 0.0,
          "gemm": 318732440.0,
          "grid_wait": 538422.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005499744336336364,
          "staging_copies": 0.0,
          "gemm": 0.9863859602004962,
          "grid_wait": 0.001666262465982664,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 551628350.0,
        "section_ns": {
          "activation_quantization": 730810.0,
          "staging_copies": 0.0,
          "gemm": 548749731.0,
          "grid_wait": 484806.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001324823134996597,
          "staging_copies": 0.0,
          "gemm": 0.9947815970662132,
          "grid_wait": 0.0008788634594287984,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 529636250.0,
        "section_ns": {
          "activation_quantization": 2228566.0,
          "staging_copies": 0.0,
          "gemm": 525119699.0,
          "grid_wait": 585183.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004207729361424941,
          "staging_copies": 0.0,
          "gemm": 0.9914723529592244,
          "grid_wait": 0.0011048771680563783,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 522905005.0,
        "section_ns": {
          "activation_quantization": 782532.0,
          "staging_copies": 0.0,
          "gemm": 519981516.0,
          "grid_wait": 477768.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014965089117859945,
          "staging_copies": 0.0,
          "gemm": 0.9944091393808709,
          "grid_wait": 0.0009136802964813848,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 517848652.0,
        "section_ns": {
          "activation_quantization": 994526.0,
          "staging_copies": 0.0,
          "gemm": 514561603.0,
          "grid_wait": 480259.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019204954887089287,
          "staging_copies": 0.0,
          "gemm": 0.993652490959849,
          "grid_wait": 0.000927411895628532,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5440866.0,
        "section_ns": {
          "activation_quantization": 1136939.0,
          "staging_copies": 0.0,
          "gemm": 1982681.0,
          "grid_wait": 493351.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20896287466002655,
          "staging_copies": 0.0,
          "gemm": 0.3644054089918774,
          "grid_wait": 0.09067508738498614,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3797563.0,
        "section_ns": {
          "activation_quantization": 727017.0,
          "staging_copies": 0.0,
          "gemm": 1695470.0,
          "grid_wait": 459100.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1914430386013346,
          "staging_copies": 0.0,
          "gemm": 0.44646263932948577,
          "grid_wait": 0.1208933202688145,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 284261772.0,
        "section_ns": {
          "activation_quantization": 706600.0,
          "staging_copies": 0.0,
          "gemm": 281457027.0,
          "grid_wait": 445561.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002485736984711402,
          "staging_copies": 0.0,
          "gemm": 0.990133231843781,
          "grid_wait": 0.0015674320077059113,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 320419155.0,
        "section_ns": {
          "activation_quantization": 1559664.0,
          "staging_copies": 0.0,
          "gemm": 315307711.0,
          "grid_wait": 1480218.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0048675741623499386,
          "staging_copies": 0.0,
          "gemm": 0.9840476328576548,
          "grid_wait": 0.004619630184094331,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 543704839.0,
        "section_ns": {
          "activation_quantization": 696110.0,
          "staging_copies": 0.0,
          "gemm": 540658989.0,
          "grid_wait": 684193.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012803086345163097,
          "staging_copies": 0.0,
          "gemm": 0.9943979715067425,
          "grid_wait": 0.0012583904922722235,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526854331.0,
        "section_ns": {
          "activation_quantization": 2256946.0,
          "staging_copies": 0.0,
          "gemm": 522288876.0,
          "grid_wait": 600603.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004283814077633539,
          "staging_copies": 0.0,
          "gemm": 0.9913345022876922,
          "grid_wait": 0.0011399792402959292,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 515664680.0,
        "section_ns": {
          "activation_quantization": 743281.0,
          "staging_copies": 0.0,
          "gemm": 511831030.0,
          "grid_wait": 1425915.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014414037432232123,
          "staging_copies": 0.0,
          "gemm": 0.992565614538502,
          "grid_wait": 0.002765198112851165,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 521327884.0,
        "section_ns": {
          "activation_quantization": 971579.0,
          "staging_copies": 0.0,
          "gemm": 518177750.0,
          "grid_wait": 537427.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001863662063393486,
          "staging_copies": 0.0,
          "gemm": 0.9939574803177035,
          "grid_wait": 0.0010308809800781728,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5399562.0,
        "section_ns": {
          "activation_quantization": 1126745.0,
          "staging_copies": 0.0,
          "gemm": 1997551.0,
          "grid_wait": 668483.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20867340721339991,
          "staging_copies": 0.0,
          "gemm": 0.36994685865260923,
          "grid_wait": 0.1238031899624451,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3803268.0,
        "section_ns": {
          "activation_quantization": 725773.0,
          "staging_copies": 0.0,
          "gemm": 1760725.0,
          "grid_wait": 412353.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1908287819843356,
          "staging_copies": 0.0,
          "gemm": 0.46295054674032965,
          "grid_wait": 0.10842070556163805,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 313683048.0,
        "section_ns": {
          "activation_quantization": 688723.0,
          "staging_copies": 0.0,
          "gemm": 310924696.0,
          "grid_wait": 400353.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0021956015933637576,
          "staging_copies": 0.0,
          "gemm": 0.9912065633843241,
          "grid_wait": 0.0012762978508165988,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 66395238.0,
        "section_ns": {
          "activation_quantization": 1035064.0,
          "staging_copies": 0.0,
          "gemm": 63237163.0,
          "grid_wait": 464354.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.015589431278188957,
          "staging_copies": 0.0,
          "gemm": 0.9524352183209284,
          "grid_wait": 0.006993784704860912,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 297065073.0,
        "section_ns": {
          "activation_quantization": 746179.0,
          "staging_copies": 0.0,
          "gemm": 294033929.0,
          "grid_wait": 457102.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002511836859394103,
          "staging_copies": 0.0,
          "gemm": 0.9897963635731758,
          "grid_wait": 0.0015387268364598352,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 533904045.0,
        "section_ns": {
          "activation_quantization": 729690.0,
          "staging_copies": 0.0,
          "gemm": 531017924.0,
          "grid_wait": 523149.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013667062589870433,
          "staging_copies": 0.0,
          "gemm": 0.9945943076718964,
          "grid_wait": 0.0009798558465688343,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 67334927.0,
        "section_ns": {
          "activation_quantization": 890064.0,
          "staging_copies": 0.0,
          "gemm": 64280750.0,
          "grid_wait": 458762.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.013218459418542178,
          "staging_copies": 0.0,
          "gemm": 0.9546420091908617,
          "grid_wait": 0.006813135774246848,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526005145.0,
        "section_ns": {
          "activation_quantization": 2265258.0,
          "staging_copies": 0.0,
          "gemm": 521452097.0,
          "grid_wait": 583097.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004306532020708657,
          "staging_copies": 0.0,
          "gemm": 0.9913440998756771,
          "grid_wait": 0.0011085385866330263,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 519894022.0,
        "section_ns": {
          "activation_quantization": 779697.0,
          "staging_copies": 0.0,
          "gemm": 516902790.0,
          "grid_wait": 475433.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014997229569991093,
          "staging_copies": 0.0,
          "gemm": 0.9942464581752779,
          "grid_wait": 0.0009144806054338512,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 517305562.0,
        "section_ns": {
          "activation_quantization": 980647.0,
          "staging_copies": 0.0,
          "gemm": 514191853.0,
          "grid_wait": 456600.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018956823046878432,
          "staging_copies": 0.0,
          "gemm": 0.9939809094880755,
          "grid_wait": 0.0008826504749624169,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 315179338.0,
        "section_ns": {
          "activation_quantization": 1975353.0,
          "staging_copies": 0.0,
          "gemm": 310310791.0,
          "grid_wait": 560401.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.006267393708403563,
          "staging_copies": 0.0,
          "gemm": 0.9845530895810182,
          "grid_wait": 0.0017780385083491735,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 545024903.0,
        "section_ns": {
          "activation_quantization": 750150.0,
          "staging_copies": 0.0,
          "gemm": 542115040.0,
          "grid_wait": 492849.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013763591275754972,
          "staging_copies": 0.0,
          "gemm": 0.9946610457907828,
          "grid_wait": 0.0009042687724674481,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524851531.0,
        "section_ns": {
          "activation_quantization": 2256488.0,
          "staging_copies": 0.0,
          "gemm": 520318155.0,
          "grid_wait": 610056.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004299288211469464,
          "staging_copies": 0.0,
          "gemm": 0.9913625554423695,
          "grid_wait": 0.00116234013614795,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 523425003.0,
        "section_ns": {
          "activation_quantization": 940059.0,
          "staging_copies": 0.0,
          "gemm": 520322184.0,
          "grid_wait": 483850.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0017959764906377619,
          "staging_copies": 0.0,
          "gemm": 0.994072084859882,
          "grid_wait": 0.0009243922189937877,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 516681511.0,
        "section_ns": {
          "activation_quantization": 979958.0,
          "staging_copies": 0.0,
          "gemm": 513598708.0,
          "grid_wait": 453973.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018966384109688028,
          "staging_copies": 0.0,
          "gemm": 0.9940334559407139,
          "grid_wait": 0.0008786321754021502,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5103566.0,
        "section_ns": {
          "activation_quantization": 1132239.0,
          "staging_copies": 0.0,
          "gemm": 1902094.0,
          "grid_wait": 482513.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2218525242937977,
          "staging_copies": 0.0,
          "gemm": 0.372699010848493,
          "grid_wait": 0.09454428530952672,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3660819.0,
        "section_ns": {
          "activation_quantization": 685396.0,
          "staging_copies": 0.0,
          "gemm": 1672881.0,
          "grid_wait": 421845.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1872247712875179,
          "staging_copies": 0.0,
          "gemm": 0.4569690552851698,
          "grid_wait": 0.11523241110800615,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 287529918.0,
        "section_ns": {
          "activation_quantization": 717656.0,
          "staging_copies": 0.0,
          "gemm": 284742540.0,
          "grid_wait": 406804.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002495935049096352,
          "staging_copies": 0.0,
          "gemm": 0.9903057809796336,
          "grid_wait": 0.001414823204589096,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 66402014.0,
        "section_ns": {
          "activation_quantization": 998387.0,
          "staging_copies": 0.0,
          "gemm": 62695472.0,
          "grid_wait": 1051785.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.015035492748759096,
          "staging_copies": 0.0,
          "gemm": 0.9441802774235131,
          "grid_wait": 0.015839655104437043,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 285689987.0,
        "section_ns": {
          "activation_quantization": 775438.0,
          "staging_copies": 0.0,
          "gemm": 282562426.0,
          "grid_wait": 495677.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002714263835925058,
          "staging_copies": 0.0,
          "gemm": 0.9890526054733588,
          "grid_wait": 0.0017350170553929844,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 520243611.0,
        "section_ns": {
          "activation_quantization": 724817.0,
          "staging_copies": 0.0,
          "gemm": 516104608.0,
          "grid_wait": 1770840.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013932261438189964,
          "staging_copies": 0.0,
          "gemm": 0.9920441060447737,
          "grid_wait": 0.0034038668857386506,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 65575292.0,
        "section_ns": {
          "activation_quantization": 913555.0,
          "staging_copies": 0.0,
          "gemm": 62514692.0,
          "grid_wait": 447015.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.01393139049994623,
          "staging_copies": 0.0,
          "gemm": 0.9533269329551747,
          "grid_wait": 0.006816820579312099,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 527196064.0,
        "section_ns": {
          "activation_quantization": 2210779.0,
          "staging_copies": 0.0,
          "gemm": 522657170.0,
          "grid_wait": 600815.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004193466436805567,
          "staging_copies": 0.0,
          "gemm": 0.9913905009730877,
          "grid_wait": 0.001139642423430536,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 520218436.0,
        "section_ns": {
          "activation_quantization": 801654.0,
          "staging_copies": 0.0,
          "gemm": 517151641.0,
          "grid_wait": 457007.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015409949831151314,
          "staging_copies": 0.0,
          "gemm": 0.994104793702467,
          "grid_wait": 0.0008784905885188582,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 525399129.0,
        "section_ns": {
          "activation_quantization": 984107.0,
          "staging_copies": 0.0,
          "gemm": 522277259.0,
          "grid_wait": 448429.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018730655337649029,
          "staging_copies": 0.0,
          "gemm": 0.9940580982577152,
          "grid_wait": 0.0008535016052529466,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 328002756.0,
        "section_ns": {
          "activation_quantization": 1831668.0,
          "staging_copies": 0.0,
          "gemm": 323258455.0,
          "grid_wait": 590978.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005584306736739737,
          "staging_copies": 0.0,
          "gemm": 0.985535789217576,
          "grid_wait": 0.0018017470560521753,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 557969702.0,
        "section_ns": {
          "activation_quantization": 744318.0,
          "staging_copies": 0.0,
          "gemm": 554940297.0,
          "grid_wait": 444849.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013339756573377526,
          "staging_copies": 0.0,
          "gemm": 0.9945706639820382,
          "grid_wait": 0.000797263719527194,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 528370305.0,
        "section_ns": {
          "activation_quantization": 2238596.0,
          "staging_copies": 0.0,
          "gemm": 523770961.0,
          "grid_wait": 660441.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0042367937388154316,
          "staging_copies": 0.0,
          "gemm": 0.991295226176649,
          "grid_wait": 0.0012499585872828337,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 526520704.0,
        "section_ns": {
          "activation_quantization": 798272.0,
          "staging_copies": 0.0,
          "gemm": 523563043.0,
          "grid_wait": 458052.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015161265149413765,
          "staging_copies": 0.0,
          "gemm": 0.9943826311529053,
          "grid_wait": 0.0008699600918257528,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 523292158.0,
        "section_ns": {
          "activation_quantization": 972358.0,
          "staging_copies": 0.0,
          "gemm": 520136435.0,
          "grid_wait": 517434.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018581551149482352,
          "staging_copies": 0.0,
          "gemm": 0.9939694815759116,
          "grid_wait": 0.0009888051867194233,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5175360.0,
        "section_ns": {
          "activation_quantization": 1191533.0,
          "staging_copies": 0.0,
          "gemm": 1887522.0,
          "grid_wait": 465888.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.23023190657268286,
          "staging_copies": 0.0,
          "gemm": 0.3647131793730291,
          "grid_wait": 0.09002040437766648,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 4412804.0,
        "section_ns": {
          "activation_quantization": 711565.0,
          "staging_copies": 0.0,
          "gemm": 1747636.0,
          "grid_wait": 1074326.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.16125008044771533,
          "staging_copies": 0.0,
          "gemm": 0.3960375307854144,
          "grid_wait": 0.24345654146433876,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 282597150.0,
        "section_ns": {
          "activation_quantization": 703029.0,
          "staging_copies": 0.0,
          "gemm": 279772940.0,
          "grid_wait": 447515.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024877427107810536,
          "staging_copies": 0.0,
          "gemm": 0.9900062332546524,
          "grid_wait": 0.0015835793106901467,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 328680603.0,
        "section_ns": {
          "activation_quantization": 1600573.0,
          "staging_copies": 0.0,
          "gemm": 323529828.0,
          "grid_wait": 1446168.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0048696910781802355,
          "staging_copies": 0.0,
          "gemm": 0.9843289352855422,
          "grid_wait": 0.004399918908509487,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 533232768.0,
        "section_ns": {
          "activation_quantization": 672238.0,
          "staging_copies": 0.0,
          "gemm": 530341278.0,
          "grid_wait": 518301.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001260683964568359,
          "staging_copies": 0.0,
          "gemm": 0.9945774337709118,
          "grid_wait": 0.0009719976548778037,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524335117.0,
        "section_ns": {
          "activation_quantization": 2269696.0,
          "staging_copies": 0.0,
          "gemm": 519792389.0,
          "grid_wait": 611834.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004328712547399338,
          "staging_copies": 0.0,
          "gemm": 0.9913362125619368,
          "grid_wait": 0.0011668758779702334,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 511988078.0,
        "section_ns": {
          "activation_quantization": 771238.0,
          "staging_copies": 0.0,
          "gemm": 508966195.0,
          "grid_wait": 510973.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015063592945615426,
          "staging_copies": 0.0,
          "gemm": 0.9940977473307494,
          "grid_wait": 0.0009980173796156247,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 516263989.0,
        "section_ns": {
          "activation_quantization": 954067.0,
          "staging_copies": 0.0,
          "gemm": 513101981.0,
          "grid_wait": 478728.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018480215942390666,
          "staging_copies": 0.0,
          "gemm": 0.9938752110017884,
          "grid_wait": 0.0009272930326348987,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5155021.0,
        "section_ns": {
          "activation_quantization": 1089992.0,
          "staging_copies": 0.0,
          "gemm": 1918969.0,
          "grid_wait": 517801.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21144278558710042,
          "staging_copies": 0.0,
          "gemm": 0.3722524117748502,
          "grid_wait": 0.10044595356643551,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3833695.0,
        "section_ns": {
          "activation_quantization": 759901.0,
          "staging_copies": 0.0,
          "gemm": 1708797.0,
          "grid_wait": 431092.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19821634219727965,
          "staging_copies": 0.0,
          "gemm": 0.4457310766766788,
          "grid_wait": 0.11244817336799093,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 314727443.0,
        "section_ns": {
          "activation_quantization": 695872.0,
          "staging_copies": 0.0,
          "gemm": 311912937.0,
          "grid_wait": 426471.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002211030577336721,
          "staging_copies": 0.0,
          "gemm": 0.9910573225735514,
          "grid_wait": 0.0013550486603101845,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 327844835.0,
        "section_ns": {
          "activation_quantization": 1823378.0,
          "staging_copies": 0.0,
          "gemm": 323403482.0,
          "grid_wait": 544643.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005561710313356012,
          "staging_copies": 0.0,
          "gemm": 0.9864528809795036,
          "grid_wait": 0.001661282844367519,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 538947143.0,
        "section_ns": {
          "activation_quantization": 714240.0,
          "staging_copies": 0.0,
          "gemm": 536059514.0,
          "grid_wait": 478392.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013252505543015745,
          "staging_copies": 0.0,
          "gemm": 0.9946420923878986,
          "grid_wait": 0.0008876417775165755,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 520711007.0,
        "section_ns": {
          "activation_quantization": 2452852.0,
          "staging_copies": 0.0,
          "gemm": 515972485.0,
          "grid_wait": 610137.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004710582198236497,
          "staging_copies": 0.0,
          "gemm": 0.9908999004509232,
          "grid_wait": 0.0011717382421301496,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 520181277.0,
        "section_ns": {
          "activation_quantization": 797656.0,
          "staging_copies": 0.0,
          "gemm": 517232181.0,
          "grid_wait": 478179.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015334192814479173,
          "staging_copies": 0.0,
          "gemm": 0.9943306379325914,
          "grid_wait": 0.0009192545390287086,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 517757284.0,
        "section_ns": {
          "activation_quantization": 1010363.0,
          "staging_copies": 0.0,
          "gemm": 514296333.0,
          "grid_wait": 783234.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001951422087574146,
          "staging_copies": 0.0,
          "gemm": 0.9933154952968272,
          "grid_wait": 0.0015127435657670053,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5098443.0,
        "section_ns": {
          "activation_quantization": 1164394.0,
          "staging_copies": 0.0,
          "gemm": 1856852.0,
          "grid_wait": 468632.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.22838227278406367,
          "staging_copies": 0.0,
          "gemm": 0.36419981551230446,
          "grid_wait": 0.09191668907546872,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3917023.0,
        "section_ns": {
          "activation_quantization": 722396.0,
          "staging_copies": 0.0,
          "gemm": 1818382.0,
          "grid_wait": 447377.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1844247531862846,
          "staging_copies": 0.0,
          "gemm": 0.46422551003657625,
          "grid_wait": 0.11421352389301773,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 289315512.0,
        "section_ns": {
          "activation_quantization": 698637.0,
          "staging_copies": 0.0,
          "gemm": 286352542.0,
          "grid_wait": 417184.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024147927470961183,
          "staging_copies": 0.0,
          "gemm": 0.989758689468403,
          "grid_wait": 0.0014419690016482765,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65566360.0,
        "section_ns": {
          "activation_quantization": 983185.0,
          "staging_copies": 0.0,
          "gemm": 62465477.0,
          "grid_wait": 446054.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.014995265864995402,
          "staging_copies": 0.0,
          "gemm": 0.952706189576484,
          "grid_wait": 0.006803092317462797,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 281012093.0,
        "section_ns": {
          "activation_quantization": 757977.0,
          "staging_copies": 0.0,
          "gemm": 276693469.0,
          "grid_wait": 1303367.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026973109659020975,
          "staging_copies": 0.0,
          "gemm": 0.9846318926922479,
          "grid_wait": 0.004638117121884858,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 534219261.0,
        "section_ns": {
          "activation_quantization": 712486.0,
          "staging_copies": 0.0,
          "gemm": 531397727.0,
          "grid_wait": 464216.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013336958286870903,
          "staging_copies": 0.0,
          "gemm": 0.994718397096506,
          "grid_wait": 0.0008689615554688882,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66029501.0,
        "section_ns": {
          "activation_quantization": 911866.0,
          "staging_copies": 0.0,
          "gemm": 62955400.0,
          "grid_wait": 442850.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.01380997866393084,
          "staging_copies": 0.0,
          "gemm": 0.9534435221614048,
          "grid_wait": 0.006706850624238399,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 523136239.0,
        "section_ns": {
          "activation_quantization": 2243648.0,
          "staging_copies": 0.0,
          "gemm": 518600980.0,
          "grid_wait": 606972.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004288840712485988,
          "staging_copies": 0.0,
          "gemm": 0.9913306350011818,
          "grid_wait": 0.0011602560762379148,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 518177756.0,
        "section_ns": {
          "activation_quantization": 816992.0,
          "staging_copies": 0.0,
          "gemm": 515187882.0,
          "grid_wait": 448927.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015766635880062748,
          "staging_copies": 0.0,
          "gemm": 0.9942300224867237,
          "grid_wait": 0.0008663571425092204,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 528674855.0,
        "section_ns": {
          "activation_quantization": 1005764.0,
          "staging_copies": 0.0,
          "gemm": 525490573.0,
          "grid_wait": 445404.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019024245062686026,
          "staging_copies": 0.0,
          "gemm": 0.9939768612600272,
          "grid_wait": 0.0008424913645647096,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 320895514.0,
        "section_ns": {
          "activation_quantization": 1552625.0,
          "staging_copies": 0.0,
          "gemm": 316740032.0,
          "grid_wait": 547727.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004838412917171538,
          "staging_copies": 0.0,
          "gemm": 0.987050358080107,
          "grid_wait": 0.0017068702306633056,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 539712046.0,
        "section_ns": {
          "activation_quantization": 738149.0,
          "staging_copies": 0.0,
          "gemm": 536802686.0,
          "grid_wait": 489179.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001367671901101129,
          "staging_copies": 0.0,
          "gemm": 0.9946094217804433,
          "grid_wait": 0.0009063703573516311,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 521428070.0,
        "section_ns": {
          "activation_quantization": 2223943.0,
          "staging_copies": 0.0,
          "gemm": 515712806.0,
          "grid_wait": 1820720.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00426510026589094,
          "staging_copies": 0.0,
          "gemm": 0.9890392091856505,
          "grid_wait": 0.003491795138685188,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 522735052.0,
        "section_ns": {
          "activation_quantization": 765164.0,
          "staging_copies": 0.0,
          "gemm": 519681882.0,
          "grid_wait": 487599.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014637702160443604,
          "staging_copies": 0.0,
          "gemm": 0.9941592399661769,
          "grid_wait": 0.0009327842051808686,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 504822071.0,
        "section_ns": {
          "activation_quantization": 977936.0,
          "staging_copies": 0.0,
          "gemm": 501539699.0,
          "grid_wait": 487594.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019371894696735635,
          "staging_copies": 0.0,
          "gemm": 0.9934979625722427,
          "grid_wait": 0.000965872983790362,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5154014.0,
        "section_ns": {
          "activation_quantization": 1131039.0,
          "staging_copies": 0.0,
          "gemm": 1890677.0,
          "grid_wait": 504262.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2194481815532515,
          "staging_copies": 0.0,
          "gemm": 0.3668358293167229,
          "grid_wait": 0.09783869426819562,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3804854.0,
        "section_ns": {
          "activation_quantization": 734766.0,
          "staging_copies": 0.0,
          "gemm": 1732591.0,
          "grid_wait": 408093.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1931127974949893,
          "staging_copies": 0.0,
          "gemm": 0.455363333257991,
          "grid_wait": 0.10725588945068588,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 309022447.0,
        "section_ns": {
          "activation_quantization": 695720.0,
          "staging_copies": 0.0,
          "gemm": 306238741.0,
          "grid_wait": 407720.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0022513574879562065,
          "staging_copies": 0.0,
          "gemm": 0.99099189710319,
          "grid_wait": 0.001319386355127788,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 290962724.0,
        "section_ns": {
          "activation_quantization": 1848267.0,
          "staging_copies": 0.0,
          "gemm": 286217281.0,
          "grid_wait": 561688.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0063522466884795865,
          "staging_copies": 0.0,
          "gemm": 0.9836905465594967,
          "grid_wait": 0.0019304465956264557,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 487124819.0,
        "section_ns": {
          "activation_quantization": 730525.0,
          "staging_copies": 0.0,
          "gemm": 484246403.0,
          "grid_wait": 482960.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014996669672870846,
          "staging_copies": 0.0,
          "gemm": 0.994091009351753,
          "grid_wait": 0.000991450201596072,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526734135.0,
        "section_ns": {
          "activation_quantization": 2198770.0,
          "staging_copies": 0.0,
          "gemm": 521703639.0,
          "grid_wait": 1161419.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004174344994747683,
          "staging_copies": 0.0,
          "gemm": 0.9904496487587614,
          "grid_wait": 0.0022049434863377518,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 519788599.0,
        "section_ns": {
          "activation_quantization": 771323.0,
          "staging_copies": 0.0,
          "gemm": 516894302.0,
          "grid_wait": 458768.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014839167336180839,
          "staging_copies": 0.0,
          "gemm": 0.9944317805246821,
          "grid_wait": 0.0008826049684094745,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 503293914.0,
        "section_ns": {
          "activation_quantization": 980153.0,
          "staging_copies": 0.0,
          "gemm": 500011974.0,
          "grid_wait": 471556.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019474763607016316,
          "staging_copies": 0.0,
          "gemm": 0.9934790787078741,
          "grid_wait": 0.0009369396030487268,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5078475.0,
        "section_ns": {
          "activation_quantization": 1108491.0,
          "staging_copies": 0.0,
          "gemm": 1839308.0,
          "grid_wait": 501479.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2182724144551268,
          "staging_copies": 0.0,
          "gemm": 0.36217722840025796,
          "grid_wait": 0.09874598181540718,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3723906.0,
        "section_ns": {
          "activation_quantization": 722597.0,
          "staging_copies": 0.0,
          "gemm": 1709547.0,
          "grid_wait": 435931.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19404276047784236,
          "staging_copies": 0.0,
          "gemm": 0.45907361786253464,
          "grid_wait": 0.11706283670962693,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 267081746.0,
        "section_ns": {
          "activation_quantization": 692138.0,
          "staging_copies": 0.0,
          "gemm": 264300401.0,
          "grid_wait": 413968.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025914837324749257,
          "staging_copies": 0.0,
          "gemm": 0.9895861658774688,
          "grid_wait": 0.0015499674021151562,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "token_embd.weight": {
        "records": 256,
        "worker_elapsed_ns": 13479872028.0,
        "section_ns": {
          "activation_quantization": 534134.0,
          "staging_copies": 0.0,
          "gemm": 13477227490.0,
          "grid_wait": 392794.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 3.962456015090591e-05,
          "staging_copies": 0.0,
          "gemm": 0.9998038157933171,
          "grid_wait": 2.913929740461183e-05,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      }
    },
    "ffn_pairs": {
      "adjacent_same_input_pairs": 2048,
      "pairs_by_layer": {
        "blk.0": 64,
        "blk.1": 64,
        "blk.2": 64,
        "blk.3": 64,
        "blk.4": 64,
        "blk.5": 64,
        "blk.6": 64,
        "blk.7": 64,
        "blk.8": 64,
        "blk.9": 64,
        "blk.10": 64,
        "blk.11": 64,
        "blk.12": 64,
        "blk.13": 64,
        "blk.14": 64,
        "blk.15": 64,
        "blk.16": 64,
        "blk.17": 64,
        "blk.18": 64,
        "blk.19": 64,
        "blk.20": 64,
        "blk.21": 64,
        "blk.22": 64,
        "blk.23": 64,
        "blk.24": 64,
        "blk.25": 64,
        "blk.26": 64,
        "blk.27": 64,
        "blk.28": 64,
        "blk.29": 64,
        "blk.30": 64,
        "blk.31": 64
      },
      "smaller_branch_worker_packing_ns": 24954581.0,
      "smaller_branch_input_bytes": 20971520,
      "worker_elapsed_fraction": 0.0002514213073787241,
      "implementation_priority_signal": false,
      "caveat": "Same input addresses/names/shapes in adjacent executions identify a reuse opportunity, not prove a safe lifetime. Worker elapsed overlaps and instrumentation overhead prevent a wall-time savings estimate. No pointer cache is implemented."
    }
  },
  "baseline_timings": {
    "cache_n": 0,
    "prompt_n": 256,
    "prompt_ms": 26079.399,
    "prompt_per_token_ms": 101.87265234375,
    "prompt_per_second": 9.81617712892847,
    "predicted_n": 65,
    "predicted_ms": 31208.726,
    "predicted_per_token_ms": 480.1342461538461,
    "predicted_per_second": 2.0827508306490947
  },
  "diagnostic_timings": {
    "cache_n": 0,
    "prompt_n": 256,
    "prompt_ms": 27185.291,
    "prompt_per_token_ms": 106.19254296875,
    "prompt_per_second": 9.41685707907265,
    "predicted_n": 65,
    "predicted_ms": 35680.445,
    "predicted_per_token_ms": 548.929923076923,
    "predicted_per_second": 1.8217261584041342
  }
}

## 4B-2048

{
  "exact_identity": true,
  "cpu_profile": {
    "samples": 40811,
    "sampled_cpu_s": 205.080376375,
    "multi_frame_samples_pct": 27.23040356766558,
    "unknown_leaf_samples_pct": 0.007350959300188675,
    "cpu_share_pct": {
      "other_or_unattributed": 86.88833892823014,
      "attention_visible_stack": 10.408958369067163,
      "recurrent_visible_stack": 2.7027027027027026
    },
    "attention_copy_visible_cpu_pct": 0.0,
    "top_self": [
      {
        "symbol": "LOOP_INNER360",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 44.01509396976305
      },
      {
        "symbol": "spert::detail::sync_impl(spert::detail::Future*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 20.055867290681434
      },
      {
        "symbol": "ggml_compute_forward_flash_attn_ext_f16_one_chunk(ggml_compute_params const*, ggml_tensor*, int, int, long, long, float*, long)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 10.038960084291
      },
      {
        "symbol": "ggml_vec_dot_f16",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 9.936046654088358
      },
      {
        "symbol": "spert::detail::barrier_coro(spert::detail::Tile*, spert::detail::Barrier*)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 5.405405405405405
      },
      {
        "symbol": "LOOP_K360",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 4.599250202151381
      },
      {
        "symbol": "ggml_gdn_decode_step_rvv(float*, float const*, float const*, float const*, float, float, float, long, float*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 2.599789272500061
      },
      {
        "symbol": "expf@@GLIBC_2.27",
        "dso": "/usr/lib/riscv64-linux-gnu/libm.so.6",
        "cpu_pct": 0.5562225870476097
      },
      {
        "symbol": "void spacemit_kernels::rvv::forward_concat<int>(ggml_compute_params*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.39695180221018844
      },
      {
        "symbol": "getenv",
        "dso": "/usr/lib/riscv64-linux-gnu/libc.so.6",
        "cpu_pct": 0.2352306976060376
      },
      {
        "symbol": "ggml_compute_forward_dup_bytes(ggml_compute_params const*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.19602558133836465
      },
      {
        "symbol": "ggml_compute_forward_ssm_conv",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.18622430227144643
      },
      {
        "symbol": "ggml_graph_compute_spert_kernel",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.1347675871701257
      },
      {
        "symbol": "LOOP_MAIN67",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.11516502903628924
      },
      {
        "symbol": "memcpy_main_loop149",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.11271470926955968
      },
      {
        "symbol": "ggml_compute_forward_rms_norm_mul_fused",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.09556247090245278
      },
      {
        "symbol": "$xrv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_v1p0_zicbop1p0_zicsr2p0_zifencei2p0_zihintpause2p0_zmmul1p0_zfh1p0_zfhmin1p0_zba1p0_zve32f1p0_zve32x1p0_zve64d1p0_zve64f1p0_zve64x1p0_zvfh1p0_zvfhmin1p0_zvl128b1p0_zvl32b1p0_zvl64b1p0",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.08821151160226409
      },
      {
        "symbol": "llama_token_data_array_partial_sort_inplace(llama_token_data_array*, int)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libllama.so.0.0.7",
        "cpu_pct": 0.07350959300188675
      },
      {
        "symbol": "ggml_vec_swiglu_f32",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.06615863370169807
      },
      {
        "symbol": "ggml_compute_forward_gated_delta_net",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.06370831393496851
      },
      {
        "symbol": "__tls_get_addr",
        "dso": "/usr/lib/riscv64-linux-gnu/ld-linux-riscv64-lp64d.so.1",
        "cpu_pct": 0.06370831393496851
      },
      {
        "symbol": "ggml_cpu_extra_compute_forward",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.044105755801132046
      },
      {
        "symbol": "ggml_is_empty",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libggml-base.so.0.16.0",
        "cpu_pct": 0.044105755801132046
      },
      {
        "symbol": "ggml_compute_forward_l2_norm",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.044105755801132046
      },
      {
        "symbol": "spert::detail::worker_main(spert::detail::WorkerPool*, unsigned int)",
        "dso": "/home/moyamryia/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib/libspert.so.0.6.2",
        "cpu_pct": 0.04165543603440249
      },
      {
        "symbol": "ggml_vec_silu_f32",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.03920511626767293
      },
      {
        "symbol": "void spacemit_kernels::rvv::forward_binary<(ggml_op)2, float>(ggml_compute_params*, ggml_tensor*)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.03920511626767293
      },
      {
        "symbol": "ggml_type_size",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libggml-base.so.0.16.0",
        "cpu_pct": 0.034304476734213815
      },
      {
        "symbol": "common_sampler_sample(common_sampler*, llama_context*, int, bool)",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source/build/bin/libllama-common.so.0.0.7",
        "cpu_pct": 0.026953517434025142
      },
      {
        "symbol": "ggml_backend_cpu_get_extra_buffer_types()",
        "dso": "/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-gemm-routing-20261003-005740/lib/libggml-cpu.so.0.16.0",
        "cpu_pct": 0.026953517434025142
      }
    ],
    "limitations": "Visible stacks give lower bounds when frames are missing. Attention copy samples exclude inlined K transpose; they are not total packing cost. CPU shares are sampled user CPU time, not wall-time percentages or speedups.",
    "sample_window_verification": {
      "first_sample_ns": 809653241923000,
      "last_sample_ns": 809694716368000,
      "timed_samples": 40811,
      "tolerance_ns": 1000000
    },
    "window": {
      "enable_sent_ns": 809653231798147,
      "enable_ack_ns": 809653236650701,
      "disable_sent_ns": 809694720318498,
      "disable_ack_ns": 809694723201371
    },
    "perf_clockid": "CLOCK_MONOTONIC",
    "scope": "Enabled after receiving first streamed token, disabled after final event; excludes prefill. Pipelining may omit part of the first decode execution."
  },
  "counters": {
    "prefill": {
      "records": 64480,
      "worker_elapsed_ns": 571102448120.0,
      "section_ns": {
        "activation_quantization": 9061234980.0,
        "staging_copies": 0.0,
        "gemm": 556690409753.0,
        "grid_wait": 531999984.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.01586621631517863,
        "staging_copies": 0.0,
        "gemm": 0.9747645305768822,
        "grid_wait": 0.0009315316117997382,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 7348420608,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "decode": {
      "records": 63744,
      "worker_elapsed_ns": 99362275996.0,
      "section_ns": {
        "activation_quantization": 276900049.0,
        "staging_copies": 0.0,
        "gemm": 98519686543.0,
        "grid_wait": 147862641.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.002786772406573568,
        "staging_copies": 0.0,
        "gemm": 0.9915200266443784,
        "grid_wait": 0.0014881164860389518,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 230293504,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "startup_compatibility_probe": {
      "records": 996,
      "worker_elapsed_ns": 2218801977.0,
      "section_ns": {
        "activation_quantization": 3826193.0,
        "staging_copies": 0.0,
        "gemm": 2168868466.0,
        "grid_wait": 15173434.0,
        "pair_wait": 0.0
      },
      "elapsed_fraction": {
        "activation_quantization": 0.0017244409549216839,
        "staging_copies": 0.0,
        "gemm": 0.9774952828068442,
        "grid_wait": 0.0068385706148124635,
        "pair_wait": 0.0
      },
      "packing_input_bytes": 7186432,
      "staging_copy_bytes": 0,
      "buffer_sizes": [
        0
      ]
    },
    "request_only_records": 128228,
    "decode_weights": {
      "blk.0.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 321746469.0,
        "section_ns": {
          "activation_quantization": 1504534.0,
          "staging_copies": 0.0,
          "gemm": 317654703.0,
          "grid_wait": 540720.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00467614766581945,
          "staging_copies": 0.0,
          "gemm": 0.9872826389898937,
          "grid_wait": 0.001680577883824422,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 537053933.0,
        "section_ns": {
          "activation_quantization": 825156.0,
          "staging_copies": 0.0,
          "gemm": 533809421.0,
          "grid_wait": 576229.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015364490403983319,
          "staging_copies": 0.0,
          "gemm": 0.9939586849650722,
          "grid_wait": 0.0010729443815468715,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 523213590.0,
        "section_ns": {
          "activation_quantization": 2381786.0,
          "staging_copies": 0.0,
          "gemm": 518412622.0,
          "grid_wait": 701561.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00455222502917021,
          "staging_copies": 0.0,
          "gemm": 0.9908240762630038,
          "grid_wait": 0.0013408692232172333,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 516192179.0,
        "section_ns": {
          "activation_quantization": 719682.0,
          "staging_copies": 0.0,
          "gemm": 513287525.0,
          "grid_wait": 503924.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013942132974471121,
          "staging_copies": 0.0,
          "gemm": 0.994372921330139,
          "grid_wait": 0.000976233310966147,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 518789509.0,
        "section_ns": {
          "activation_quantization": 942621.0,
          "staging_copies": 0.0,
          "gemm": 515736384.0,
          "grid_wait": 463431.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018169623395372092,
          "staging_copies": 0.0,
          "gemm": 0.9941149060514252,
          "grid_wait": 0.0008932929289439429,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5170725.0,
        "section_ns": {
          "activation_quantization": 1041942.0,
          "staging_copies": 0.0,
          "gemm": 1817174.0,
          "grid_wait": 644355.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20150791233337684,
          "staging_copies": 0.0,
          "gemm": 0.35143505021056043,
          "grid_wait": 0.12461598711979462,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 4682257.0,
        "section_ns": {
          "activation_quantization": 696525.0,
          "staging_copies": 0.0,
          "gemm": 1622588.0,
          "grid_wait": 1415024.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1487583872478593,
          "staging_copies": 0.0,
          "gemm": 0.3465397136466452,
          "grid_wait": 0.30220981035428,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.0.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 312315418.0,
        "section_ns": {
          "activation_quantization": 720403.0,
          "staging_copies": 0.0,
          "gemm": 309446495.0,
          "grid_wait": 436224.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0023066520526373755,
          "staging_copies": 0.0,
          "gemm": 0.9908140205873538,
          "grid_wait": 0.001396741802865461,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 298029431.0,
        "section_ns": {
          "activation_quantization": 2254565.0,
          "staging_copies": 0.0,
          "gemm": 293101714.0,
          "grid_wait": 623974.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.007564907238976677,
          "staging_copies": 0.0,
          "gemm": 0.983465669872047,
          "grid_wait": 0.0020936657091426654,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 543647816.0,
        "section_ns": {
          "activation_quantization": 678071.0,
          "staging_copies": 0.0,
          "gemm": 540736455.0,
          "grid_wait": 553391.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012472615175556964,
          "staging_copies": 0.0,
          "gemm": 0.9946447664934609,
          "grid_wait": 0.0010179218672700416,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 523160175.0,
        "section_ns": {
          "activation_quantization": 2372726.0,
          "staging_copies": 0.0,
          "gemm": 518461606.0,
          "grid_wait": 621576.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004535371982395258,
          "staging_copies": 0.0,
          "gemm": 0.991018871036963,
          "grid_wait": 0.0011881179602403794,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 526087164.0,
        "section_ns": {
          "activation_quantization": 746942.0,
          "staging_copies": 0.0,
          "gemm": 523135993.0,
          "grid_wait": 501937.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014198065474944756,
          "staging_copies": 0.0,
          "gemm": 0.9943903383280418,
          "grid_wait": 0.0009540947476908979,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 526932150.0,
        "section_ns": {
          "activation_quantization": 968908.0,
          "staging_copies": 0.0,
          "gemm": 523696303.0,
          "grid_wait": 457187.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018387718418775548,
          "staging_copies": 0.0,
          "gemm": 0.9938590822366788,
          "grid_wait": 0.0008676392207231994,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5092517.0,
        "section_ns": {
          "activation_quantization": 1118165.0,
          "staging_copies": 0.0,
          "gemm": 1825138.0,
          "grid_wait": 506106.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21957020467481994,
          "staging_copies": 0.0,
          "gemm": 0.3583960544461609,
          "grid_wait": 0.09938228974002443,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3714183.0,
        "section_ns": {
          "activation_quantization": 665315.0,
          "staging_copies": 0.0,
          "gemm": 1612712.0,
          "grid_wait": 431924.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.17912822281508478,
          "staging_copies": 0.0,
          "gemm": 0.4342036997100035,
          "grid_wait": 0.11629044664735151,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.1.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 286392687.0,
        "section_ns": {
          "activation_quantization": 744268.0,
          "staging_copies": 0.0,
          "gemm": 283495029.0,
          "grid_wait": 450425.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025987674748133498,
          "staging_copies": 0.0,
          "gemm": 0.9898822207006983,
          "grid_wait": 0.0015727531478483597,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 314914477.0,
        "section_ns": {
          "activation_quantization": 1551659.0,
          "staging_copies": 0.0,
          "gemm": 310721746.0,
          "grid_wait": 554425.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004927239340603576,
          "staging_copies": 0.0,
          "gemm": 0.9866861281197943,
          "grid_wait": 0.0017605573591969225,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 534177965.0,
        "section_ns": {
          "activation_quantization": 668935.0,
          "staging_copies": 0.0,
          "gemm": 531261683.0,
          "grid_wait": 520316.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012522699246869907,
          "staging_copies": 0.0,
          "gemm": 0.9945406171892546,
          "grid_wait": 0.0009740499123733042,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 523138454.0,
        "section_ns": {
          "activation_quantization": 2372643.0,
          "staging_copies": 0.0,
          "gemm": 518425633.0,
          "grid_wait": 653476.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004535401635758934,
          "staging_copies": 0.0,
          "gemm": 0.9909912548695952,
          "grid_wait": 0.001249145412659724,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 516938249.0,
        "section_ns": {
          "activation_quantization": 734306.0,
          "staging_copies": 0.0,
          "gemm": 512963921.0,
          "grid_wait": 1311358.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014204907480158235,
          "staging_copies": 0.0,
          "gemm": 0.9923117935117237,
          "grid_wait": 0.002536778817463747,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 513402174.0,
        "section_ns": {
          "activation_quantization": 944197.0,
          "staging_copies": 0.0,
          "gemm": 510262972.0,
          "grid_wait": 477464.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001839098172576106,
          "staging_copies": 0.0,
          "gemm": 0.9938854914159362,
          "grid_wait": 0.000929999957499206,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5006171.0,
        "section_ns": {
          "activation_quantization": 1086789.0,
          "staging_copies": 0.0,
          "gemm": 1818965.0,
          "grid_wait": 509096.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2170898676853028,
          "staging_copies": 0.0,
          "gemm": 0.36334456014387045,
          "grid_wait": 0.10169368964823615,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3654440.0,
        "section_ns": {
          "activation_quantization": 706557.0,
          "staging_copies": 0.0,
          "gemm": 1624126.0,
          "grid_wait": 405004.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.193342071562264,
          "staging_copies": 0.0,
          "gemm": 0.4444254112805245,
          "grid_wait": 0.11082518799049923,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.10.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 308073571.0,
        "section_ns": {
          "activation_quantization": 877313.0,
          "staging_copies": 0.0,
          "gemm": 304093057.0,
          "grid_wait": 1390498.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0028477386007253443,
          "staging_copies": 0.0,
          "gemm": 0.9870793395646392,
          "grid_wait": 0.004513525764272716,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65789563.0,
        "section_ns": {
          "activation_quantization": 1004399.0,
          "staging_copies": 0.0,
          "gemm": 62657230.0,
          "grid_wait": 451970.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.015266844073732485,
          "staging_copies": 0.0,
          "gemm": 0.9523886030372325,
          "grid_wait": 0.006869934673376687,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 301036719.0,
        "section_ns": {
          "activation_quantization": 750608.0,
          "staging_copies": 0.0,
          "gemm": 297768681.0,
          "grid_wait": 519172.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024934101145315767,
          "staging_copies": 0.0,
          "gemm": 0.9891440552140751,
          "grid_wait": 0.0017246135346033983,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 539027574.0,
        "section_ns": {
          "activation_quantization": 691984.0,
          "staging_copies": 0.0,
          "gemm": 536195113.0,
          "grid_wait": 484521.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012837636391491913,
          "staging_copies": 0.0,
          "gemm": 0.9947452391368757,
          "grid_wait": 0.0008988798038743747,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 67036390.0,
        "section_ns": {
          "activation_quantization": 870015.0,
          "staging_copies": 0.0,
          "gemm": 63998315.0,
          "grid_wait": 464386.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.012978249574596723,
          "staging_copies": 0.0,
          "gemm": 0.9546802117476791,
          "grid_wait": 0.006927371834909368,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525062715.0,
        "section_ns": {
          "activation_quantization": 2370527.0,
          "staging_copies": 0.0,
          "gemm": 520277971.0,
          "grid_wait": 676231.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004514750204649363,
          "staging_copies": 0.0,
          "gemm": 0.9908872904830045,
          "grid_wait": 0.0012879051981438065,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 517575809.0,
        "section_ns": {
          "activation_quantization": 735774.0,
          "staging_copies": 0.0,
          "gemm": 514542435.0,
          "grid_wait": 533670.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001421577259226194,
          "staging_copies": 0.0,
          "gemm": 0.9941392662731654,
          "grid_wait": 0.0010310953308097907,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.11.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 522171560.0,
        "section_ns": {
          "activation_quantization": 958695.0,
          "staging_copies": 0.0,
          "gemm": 519002553.0,
          "grid_wait": 512390.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018359770493820077,
          "staging_copies": 0.0,
          "gemm": 0.9939310999626253,
          "grid_wait": 0.0009812675359033342,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 332718777.0,
        "section_ns": {
          "activation_quantization": 1693214.0,
          "staging_copies": 0.0,
          "gemm": 328421735.0,
          "grid_wait": 559524.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005089024476667874,
          "staging_copies": 0.0,
          "gemm": 0.9870850631312581,
          "grid_wait": 0.0016816724473593505,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 537624283.0,
        "section_ns": {
          "activation_quantization": 667476.0,
          "staging_copies": 0.0,
          "gemm": 534726989.0,
          "grid_wait": 553511.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001241528742480555,
          "staging_copies": 0.0,
          "gemm": 0.9946109316643348,
          "grid_wait": 0.0010295498501506487,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525834086.0,
        "section_ns": {
          "activation_quantization": 2393601.0,
          "staging_copies": 0.0,
          "gemm": 521077457.0,
          "grid_wait": 657881.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0045520080643840196,
          "staging_copies": 0.0,
          "gemm": 0.9909541257848393,
          "grid_wait": 0.0012511189698721813,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 529787223.0,
        "section_ns": {
          "activation_quantization": 746140.0,
          "staging_copies": 0.0,
          "gemm": 526779399.0,
          "grid_wait": 486497.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014083767361826316,
          "staging_copies": 0.0,
          "gemm": 0.9943225810864827,
          "grid_wait": 0.0009182875291803706,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 526162919.0,
        "section_ns": {
          "activation_quantization": 969867.0,
          "staging_copies": 0.0,
          "gemm": 523079922.0,
          "grid_wait": 462043.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018432826886457196,
          "staging_copies": 0.0,
          "gemm": 0.9941406038155266,
          "grid_wait": 0.000878136758246166,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5250353.0,
        "section_ns": {
          "activation_quantization": 1090395.0,
          "staging_copies": 0.0,
          "gemm": 1808051.0,
          "grid_wait": 726733.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20768032168503717,
          "staging_copies": 0.0,
          "gemm": 0.34436751205109445,
          "grid_wait": 0.13841602650336082,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3829078.0,
        "section_ns": {
          "activation_quantization": 693857.0,
          "staging_copies": 0.0,
          "gemm": 1648551.0,
          "grid_wait": 549890.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18120732980628756,
          "staging_copies": 0.0,
          "gemm": 0.43053471357856904,
          "grid_wait": 0.1436089836770105,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.12.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 295435433.0,
        "section_ns": {
          "activation_quantization": 726650.0,
          "staging_copies": 0.0,
          "gemm": 292578564.0,
          "grid_wait": 435304.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002459589875937461,
          "staging_copies": 0.0,
          "gemm": 0.9903299716930027,
          "grid_wait": 0.0014734319292026153,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 331894401.0,
        "section_ns": {
          "activation_quantization": 1611003.0,
          "staging_copies": 0.0,
          "gemm": 327607953.0,
          "grid_wait": 565262.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004853962571064885,
          "staging_copies": 0.0,
          "gemm": 0.9870849041529929,
          "grid_wait": 0.0017031381014469117,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 533712884.0,
        "section_ns": {
          "activation_quantization": 742403.0,
          "staging_copies": 0.0,
          "gemm": 530778216.0,
          "grid_wait": 508506.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013910156982457258,
          "staging_copies": 0.0,
          "gemm": 0.9945014106123771,
          "grid_wait": 0.0009527707035830149,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524430132.0,
        "section_ns": {
          "activation_quantization": 2353190.0,
          "staging_copies": 0.0,
          "gemm": 518516829.0,
          "grid_wait": 1767547.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004487137287527178,
          "staging_copies": 0.0,
          "gemm": 0.9887243263893921,
          "grid_wait": 0.0033704146503923615,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 515268952.0,
        "section_ns": {
          "activation_quantization": 745355.0,
          "staging_copies": 0.0,
          "gemm": 512269199.0,
          "grid_wait": 488635.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014465358277593252,
          "staging_copies": 0.0,
          "gemm": 0.994178277211626,
          "grid_wait": 0.0009483105824703368,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 518062077.0,
        "section_ns": {
          "activation_quantization": 955148.0,
          "staging_copies": 0.0,
          "gemm": 514436634.0,
          "grid_wait": 1007028.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018436941100400213,
          "staging_copies": 0.0,
          "gemm": 0.9930019139385877,
          "grid_wait": 0.0019438365491477579,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5093637.0,
        "section_ns": {
          "activation_quantization": 1054019.0,
          "staging_copies": 0.0,
          "gemm": 1902305.0,
          "grid_wait": 505805.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20692856597358625,
          "staging_copies": 0.0,
          "gemm": 0.3734669353155712,
          "grid_wait": 0.09930134401018369,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3641174.0,
        "section_ns": {
          "activation_quantization": 708269.0,
          "staging_copies": 0.0,
          "gemm": 1631007.0,
          "grid_wait": 420527.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19451665863812057,
          "staging_copies": 0.0,
          "gemm": 0.44793437501201533,
          "grid_wait": 0.11549214621438031,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.13.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 318542414.0,
        "section_ns": {
          "activation_quantization": 731313.0,
          "staging_copies": 0.0,
          "gemm": 315523050.0,
          "grid_wait": 549140.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002295810441117584,
          "staging_copies": 0.0,
          "gemm": 0.9905213124930986,
          "grid_wait": 0.0017239148567512268,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 331249973.0,
        "section_ns": {
          "activation_quantization": 1645592.0,
          "staging_copies": 0.0,
          "gemm": 327014269.0,
          "grid_wait": 551625.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004967825310585007,
          "staging_copies": 0.0,
          "gemm": 0.98721296801434,
          "grid_wait": 0.0016652831546042119,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 549269054.0,
        "section_ns": {
          "activation_quantization": 676897.0,
          "staging_copies": 0.0,
          "gemm": 546382309.0,
          "grid_wait": 520806.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012323596151477341,
          "staging_copies": 0.0,
          "gemm": 0.9947443880572234,
          "grid_wait": 0.0009481801244895912,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526470457.0,
        "section_ns": {
          "activation_quantization": 2499226.0,
          "staging_copies": 0.0,
          "gemm": 521576039.0,
          "grid_wait": 684523.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004747134367693495,
          "staging_copies": 0.0,
          "gemm": 0.9907033377943181,
          "grid_wait": 0.0013002116090248155,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 520535515.0,
        "section_ns": {
          "activation_quantization": 747655.0,
          "staging_copies": 0.0,
          "gemm": 517609483.0,
          "grid_wait": 489679.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001436318903235642,
          "staging_copies": 0.0,
          "gemm": 0.9943788042973398,
          "grid_wait": 0.0009407215951441853,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 522274728.0,
        "section_ns": {
          "activation_quantization": 966998.0,
          "staging_copies": 0.0,
          "gemm": 518233078.0,
          "grid_wait": 1394705.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001851512141326509,
          "staging_copies": 0.0,
          "gemm": 0.9922614482698079,
          "grid_wait": 0.0026704432078130344,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5170852.0,
        "section_ns": {
          "activation_quantization": 1088153.0,
          "staging_copies": 0.0,
          "gemm": 1953350.0,
          "grid_wait": 507306.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2104397882592656,
          "staging_copies": 0.0,
          "gemm": 0.37776173056200407,
          "grid_wait": 0.09810878362018484,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3784937.0,
        "section_ns": {
          "activation_quantization": 763465.0,
          "staging_copies": 0.0,
          "gemm": 1669463.0,
          "grid_wait": 438208.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2017114155400737,
          "staging_copies": 0.0,
          "gemm": 0.4410807894556765,
          "grid_wait": 0.11577682798947513,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.14.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 289502732.0,
        "section_ns": {
          "activation_quantization": 748523.0,
          "staging_copies": 0.0,
          "gemm": 286626480.0,
          "grid_wait": 428596.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025855472755953127,
          "staging_copies": 0.0,
          "gemm": 0.9900648536884965,
          "grid_wait": 0.001480455804472339,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65863509.0,
        "section_ns": {
          "activation_quantization": 970486.0,
          "staging_copies": 0.0,
          "gemm": 62472622.0,
          "grid_wait": 749219.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.014734805581038811,
          "staging_copies": 0.0,
          "gemm": 0.9485164539289882,
          "grid_wait": 0.011375327725098886,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 281600260.0,
        "section_ns": {
          "activation_quantization": 750971.0,
          "staging_copies": 0.0,
          "gemm": 278355959.0,
          "grid_wait": 473309.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026667979638939254,
          "staging_copies": 0.0,
          "gemm": 0.988479055381554,
          "grid_wait": 0.0016807832492768296,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 524061987.0,
        "section_ns": {
          "activation_quantization": 689975.0,
          "staging_copies": 0.0,
          "gemm": 520894903.0,
          "grid_wait": 684848.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013165904360851878,
          "staging_copies": 0.0,
          "gemm": 0.9939566614664612,
          "grid_wait": 0.0013068072422509056,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66471633.0,
        "section_ns": {
          "activation_quantization": 850266.0,
          "staging_copies": 0.0,
          "gemm": 63282997.0,
          "grid_wait": 483130.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.012791411337825867,
          "staging_copies": 0.0,
          "gemm": 0.9520301238875838,
          "grid_wait": 0.007268213194040231,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525047975.0,
        "section_ns": {
          "activation_quantization": 2367960.0,
          "staging_copies": 0.0,
          "gemm": 520285167.0,
          "grid_wait": 670350.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004509987873012937,
          "staging_copies": 0.0,
          "gemm": 0.9909288136955485,
          "grid_wait": 0.0012767404730967679,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 521184151.0,
        "section_ns": {
          "activation_quantization": 744178.0,
          "staging_copies": 0.0,
          "gemm": 518123651.0,
          "grid_wait": 535857.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014278599964564157,
          "staging_copies": 0.0,
          "gemm": 0.9941277953404227,
          "grid_wait": 0.0010281529071285976,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.15.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 523538835.0,
        "section_ns": {
          "activation_quantization": 979978.0,
          "staging_copies": 0.0,
          "gemm": 520390918.0,
          "grid_wait": 483057.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018718343979200703,
          "staging_copies": 0.0,
          "gemm": 0.9939872330578877,
          "grid_wait": 0.000922676538408082,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 327781292.0,
        "section_ns": {
          "activation_quantization": 1534330.0,
          "staging_copies": 0.0,
          "gemm": 323611180.0,
          "grid_wait": 573940.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004680956593459276,
          "staging_copies": 0.0,
          "gemm": 0.9872777608064343,
          "grid_wait": 0.0017509846169011989,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 547058822.0,
        "section_ns": {
          "activation_quantization": 669415.0,
          "staging_copies": 0.0,
          "gemm": 544181791.0,
          "grid_wait": 492561.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012236618313779793,
          "staging_copies": 0.0,
          "gemm": 0.994740911060566,
          "grid_wait": 0.0009003803250978374,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 524186154.0,
        "section_ns": {
          "activation_quantization": 2356940.0,
          "staging_copies": 0.0,
          "gemm": 519453230.0,
          "grid_wait": 660388.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004496379734593295,
          "staging_copies": 0.0,
          "gemm": 0.9909709099260183,
          "grid_wait": 0.0012598348791944627,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 517375087.0,
        "section_ns": {
          "activation_quantization": 720230.0,
          "staging_copies": 0.0,
          "gemm": 514461936.0,
          "grid_wait": 479469.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013920848106085944,
          "staging_copies": 0.0,
          "gemm": 0.9943693635948111,
          "grid_wait": 0.0009267338378819157,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 534220046.0,
        "section_ns": {
          "activation_quantization": 950934.0,
          "staging_copies": 0.0,
          "gemm": 531102182.0,
          "grid_wait": 494093.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0017800417770171058,
          "staging_copies": 0.0,
          "gemm": 0.9941637083382678,
          "grid_wait": 0.0009248866711377581,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5437987.0,
        "section_ns": {
          "activation_quantization": 1298700.0,
          "staging_copies": 0.0,
          "gemm": 1841543.0,
          "grid_wait": 696985.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2388199898234402,
          "staging_copies": 0.0,
          "gemm": 0.33864424464420384,
          "grid_wait": 0.1281696701371298,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3625548.0,
        "section_ns": {
          "activation_quantization": 716143.0,
          "staging_copies": 0.0,
          "gemm": 1630380.0,
          "grid_wait": 416550.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19752682904763638,
          "staging_copies": 0.0,
          "gemm": 0.4496920189720285,
          "grid_wait": 0.11489297617904935,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.16.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 316862200.0,
        "section_ns": {
          "activation_quantization": 722847.0,
          "staging_copies": 0.0,
          "gemm": 314026492.0,
          "grid_wait": 433363.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002281266115049381,
          "staging_copies": 0.0,
          "gemm": 0.9910506586143756,
          "grid_wait": 0.0013676702364624118,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 328036059.0,
        "section_ns": {
          "activation_quantization": 1666386.0,
          "staging_copies": 0.0,
          "gemm": 323740974.0,
          "grid_wait": 580558.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005079886659655303,
          "staging_copies": 0.0,
          "gemm": 0.9869066680867544,
          "grid_wait": 0.0017697993378221874,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 541529099.0,
        "section_ns": {
          "activation_quantization": 681112.0,
          "staging_copies": 0.0,
          "gemm": 538665773.0,
          "grid_wait": 517947.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012577569723543148,
          "staging_copies": 0.0,
          "gemm": 0.9947125168245115,
          "grid_wait": 0.0009564527574906921,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 527708284.0,
        "section_ns": {
          "activation_quantization": 2374605.0,
          "staging_copies": 0.0,
          "gemm": 522964828.0,
          "grid_wait": 647308.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004499844084312309,
          "staging_copies": 0.0,
          "gemm": 0.9910112155828882,
          "grid_wait": 0.0012266398304257055,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 525199803.0,
        "section_ns": {
          "activation_quantization": 740347.0,
          "staging_copies": 0.0,
          "gemm": 522261141.0,
          "grid_wait": 487506.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014096482819891689,
          "staging_copies": 0.0,
          "gemm": 0.99440467802308,
          "grid_wait": 0.0009282295941759902,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 523850883.0,
        "section_ns": {
          "activation_quantization": 988410.0,
          "staging_copies": 0.0,
          "gemm": 520736633.0,
          "grid_wait": 470889.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018868155654134882,
          "staging_copies": 0.0,
          "gemm": 0.9940550830378194,
          "grid_wait": 0.0008988989334203336,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5225222.0,
        "section_ns": {
          "activation_quantization": 1107004.0,
          "staging_copies": 0.0,
          "gemm": 1985263.0,
          "grid_wait": 521718.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21185779283636177,
          "staging_copies": 0.0,
          "gemm": 0.3799384983068662,
          "grid_wait": 0.09984609266362271,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3618856.0,
        "section_ns": {
          "activation_quantization": 645262.0,
          "staging_copies": 0.0,
          "gemm": 1688679.0,
          "grid_wait": 428886.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.17830551975541442,
          "staging_copies": 0.0,
          "gemm": 0.4666333780620174,
          "grid_wait": 0.11851424870179969,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.17.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 289408106.0,
        "section_ns": {
          "activation_quantization": 740681.0,
          "staging_copies": 0.0,
          "gemm": 286524198.0,
          "grid_wait": 425892.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025592959721729425,
          "staging_copies": 0.0,
          "gemm": 0.9900351512614508,
          "grid_wait": 0.0014715966525139417,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 319890619.0,
        "section_ns": {
          "activation_quantization": 1517375.0,
          "staging_copies": 0.0,
          "gemm": 315736213.0,
          "grid_wait": 561954.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00474341824947358,
          "staging_copies": 0.0,
          "gemm": 0.9870130421048702,
          "grid_wait": 0.001756706719805372,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 553779516.0,
        "section_ns": {
          "activation_quantization": 674611.0,
          "staging_copies": 0.0,
          "gemm": 550916007.0,
          "grid_wait": 492968.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012181942099859107,
          "staging_copies": 0.0,
          "gemm": 0.9948291532690061,
          "grid_wait": 0.0008901882170737424,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525017723.0,
        "section_ns": {
          "activation_quantization": 2373187.0,
          "staging_copies": 0.0,
          "gemm": 520292160.0,
          "grid_wait": 635528.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004520203597012667,
          "staging_copies": 0.0,
          "gemm": 0.990999231467849,
          "grid_wait": 0.0012104886600180543,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 523529392.0,
        "section_ns": {
          "activation_quantization": 728739.0,
          "staging_copies": 0.0,
          "gemm": 520611983.0,
          "grid_wait": 471797.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013919734233374236,
          "staging_copies": 0.0,
          "gemm": 0.9944274208008554,
          "grid_wait": 0.0009011853149211535,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 519100421.0,
        "section_ns": {
          "activation_quantization": 939281.0,
          "staging_copies": 0.0,
          "gemm": 515007321.0,
          "grid_wait": 1310332.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018094398732918769,
          "staging_copies": 0.0,
          "gemm": 0.9921150131373135,
          "grid_wait": 0.002524236057207898,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 4932231.0,
        "section_ns": {
          "activation_quantization": 1035431.0,
          "staging_copies": 0.0,
          "gemm": 1763509.0,
          "grid_wait": 515101.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20993157052052103,
          "staging_copies": 0.0,
          "gemm": 0.3575479331766902,
          "grid_wait": 0.10443570059877569,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3699312.0,
        "section_ns": {
          "activation_quantization": 718553.0,
          "staging_copies": 0.0,
          "gemm": 1664877.0,
          "grid_wait": 397594.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19423963158554888,
          "staging_copies": 0.0,
          "gemm": 0.45005044181188286,
          "grid_wait": 0.1074778229032858,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.18.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 313478946.0,
        "section_ns": {
          "activation_quantization": 730988.0,
          "staging_copies": 0.0,
          "gemm": 310611350.0,
          "grid_wait": 441979.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0023318567620806024,
          "staging_copies": 0.0,
          "gemm": 0.9908523489804001,
          "grid_wait": 0.001409916058605097,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 66310081.0,
        "section_ns": {
          "activation_quantization": 1013078.0,
          "staging_copies": 0.0,
          "gemm": 63027856.0,
          "grid_wait": 446004.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.015277888138909075,
          "staging_copies": 0.0,
          "gemm": 0.9505018701455062,
          "grid_wait": 0.006726036121114073,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 306003435.0,
        "section_ns": {
          "activation_quantization": 756110.0,
          "staging_copies": 0.0,
          "gemm": 302746976.0,
          "grid_wait": 473010.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024709199751303443,
          "staging_copies": 0.0,
          "gemm": 0.9893580965847655,
          "grid_wait": 0.0015457669617336158,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 534690780.0,
        "section_ns": {
          "activation_quantization": 717306.0,
          "staging_copies": 0.0,
          "gemm": 531800276.0,
          "grid_wait": 501333.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00134153426023168,
          "staging_copies": 0.0,
          "gemm": 0.9945940642552318,
          "grid_wait": 0.0009376129507974684,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66023169.0,
        "section_ns": {
          "activation_quantization": 884401.0,
          "staging_copies": 0.0,
          "gemm": 62955707.0,
          "grid_wait": 478102.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.013395312787848763,
          "staging_copies": 0.0,
          "gemm": 0.9535396127380678,
          "grid_wait": 0.007241427626716918,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526783325.0,
        "section_ns": {
          "activation_quantization": 2443524.0,
          "staging_copies": 0.0,
          "gemm": 521789010.0,
          "grid_wait": 762726.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004638575072587956,
          "staging_copies": 0.0,
          "gemm": 0.9905192234397321,
          "grid_wait": 0.0014478932111224288,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 522393476.0,
        "section_ns": {
          "activation_quantization": 766870.0,
          "staging_copies": 0.0,
          "gemm": 519335847.0,
          "grid_wait": 495774.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014679930650588753,
          "staging_copies": 0.0,
          "gemm": 0.9941468851728156,
          "grid_wait": 0.000949043245708528,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.19.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 507754995.0,
        "section_ns": {
          "activation_quantization": 970254.0,
          "staging_copies": 0.0,
          "gemm": 503754454.0,
          "grid_wait": 1332322.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0019108704189113885,
          "staging_copies": 0.0,
          "gemm": 0.9921211193599385,
          "grid_wait": 0.0026239466142524114,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 323767050.0,
        "section_ns": {
          "activation_quantization": 1541220.0,
          "staging_copies": 0.0,
          "gemm": 319593516.0,
          "grid_wait": 533498.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004760274400992936,
          "staging_copies": 0.0,
          "gemm": 0.987109454158476,
          "grid_wait": 0.0016477834912477969,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 534499358.0,
        "section_ns": {
          "activation_quantization": 695317.0,
          "staging_copies": 0.0,
          "gemm": 531602731.0,
          "grid_wait": 500313.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013008752762617912,
          "staging_copies": 0.0,
          "gemm": 0.9945806726301063,
          "grid_wait": 0.0009360404133544347,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525120603.0,
        "section_ns": {
          "activation_quantization": 2357914.0,
          "staging_copies": 0.0,
          "gemm": 520405856.0,
          "grid_wait": 644928.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004490233265519007,
          "staging_copies": 0.0,
          "gemm": 0.9910215920436852,
          "grid_wait": 0.0012281521546013308,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 518679951.0,
        "section_ns": {
          "activation_quantization": 745829.0,
          "staging_copies": 0.0,
          "gemm": 515747454.0,
          "grid_wait": 508310.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014379368212749754,
          "staging_copies": 0.0,
          "gemm": 0.9943462302825736,
          "grid_wait": 0.000980007033277444,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 516236067.0,
        "section_ns": {
          "activation_quantization": 966371.0,
          "staging_copies": 0.0,
          "gemm": 513172016.0,
          "grid_wait": 451799.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001871955606697275,
          "staging_copies": 0.0,
          "gemm": 0.9940646320629899,
          "grid_wait": 0.0008751790680289682,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5110524.0,
        "section_ns": {
          "activation_quantization": 1057995.0,
          "staging_copies": 0.0,
          "gemm": 1928514.0,
          "grid_wait": 496716.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20702280235842743,
          "staging_copies": 0.0,
          "gemm": 0.3773613038506423,
          "grid_wait": 0.09719472993376022,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3678688.0,
        "section_ns": {
          "activation_quantization": 699600.0,
          "staging_copies": 0.0,
          "gemm": 1696339.0,
          "grid_wait": 402941.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.19017649770787845,
          "staging_copies": 0.0,
          "gemm": 0.4611260862568394,
          "grid_wait": 0.10953388816882541,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.2.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 311103372.0,
        "section_ns": {
          "activation_quantization": 736014.0,
          "staging_copies": 0.0,
          "gemm": 308221042.0,
          "grid_wait": 451752.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002365818137130317,
          "staging_copies": 0.0,
          "gemm": 0.9907351373870676,
          "grid_wait": 0.0014520961219282446,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 326267873.0,
        "section_ns": {
          "activation_quantization": 1803426.0,
          "staging_copies": 0.0,
          "gemm": 321796213.0,
          "grid_wait": 561306.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005527439718221966,
          "staging_copies": 0.0,
          "gemm": 0.9862945132817291,
          "grid_wait": 0.001720383912883755,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 554682340.0,
        "section_ns": {
          "activation_quantization": 703942.0,
          "staging_copies": 0.0,
          "gemm": 551788625.0,
          "grid_wait": 503927.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012690903409688507,
          "staging_copies": 0.0,
          "gemm": 0.9947831131598673,
          "grid_wait": 0.0009084965639973322,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 528419391.0,
        "section_ns": {
          "activation_quantization": 2391607.0,
          "staging_copies": 0.0,
          "gemm": 523697803.0,
          "grid_wait": 621697.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004525963733984168,
          "staging_copies": 0.0,
          "gemm": 0.9910646958071226,
          "grid_wait": 0.0011765219266906123,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 515844799.0,
        "section_ns": {
          "activation_quantization": 751545.0,
          "staging_copies": 0.0,
          "gemm": 512903925.0,
          "grid_wait": 483759.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014569207665889445,
          "staging_copies": 0.0,
          "gemm": 0.9942989170275612,
          "grid_wait": 0.000937799510507423,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 517030796.0,
        "section_ns": {
          "activation_quantization": 1001530.0,
          "staging_copies": 0.0,
          "gemm": 513725197.0,
          "grid_wait": 635168.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001937079972311746,
          "staging_copies": 0.0,
          "gemm": 0.9936065723249491,
          "grid_wait": 0.0012284916196752041,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5142385.0,
        "section_ns": {
          "activation_quantization": 1106519.0,
          "staging_copies": 0.0,
          "gemm": 1867344.0,
          "grid_wait": 520836.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21517622659524716,
          "staging_copies": 0.0,
          "gemm": 0.3631280038347965,
          "grid_wait": 0.10128296500553731,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3736428.0,
        "section_ns": {
          "activation_quantization": 669853.0,
          "staging_copies": 0.0,
          "gemm": 1739594.0,
          "grid_wait": 429553.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.17927630346416418,
          "staging_copies": 0.0,
          "gemm": 0.4655767487022365,
          "grid_wait": 0.11496354272048064,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.20.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 292561567.0,
        "section_ns": {
          "activation_quantization": 724140.0,
          "staging_copies": 0.0,
          "gemm": 289626821.0,
          "grid_wait": 445464.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024751713200934556,
          "staging_copies": 0.0,
          "gemm": 0.9899687917654612,
          "grid_wait": 0.0015226333539565709,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 303210024.0,
        "section_ns": {
          "activation_quantization": 1876671.0,
          "staging_copies": 0.0,
          "gemm": 298605226.0,
          "grid_wait": 554061.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.006189343529091241,
          "staging_copies": 0.0,
          "gemm": 0.9848131735908573,
          "grid_wait": 0.0018273175559657619,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 493934559.0,
        "section_ns": {
          "activation_quantization": 675655.0,
          "staging_copies": 0.0,
          "gemm": 491056563.0,
          "grid_wait": 503570.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013679038805624452,
          "staging_copies": 0.0,
          "gemm": 0.9941733252967222,
          "grid_wait": 0.0010195075254898292,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 516268773.0,
        "section_ns": {
          "activation_quantization": 2375861.0,
          "staging_copies": 0.0,
          "gemm": 510928785.0,
          "grid_wait": 1289117.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004601984710781645,
          "staging_copies": 0.0,
          "gemm": 0.9896565737087492,
          "grid_wait": 0.0024969881337370756,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 499439270.0,
        "section_ns": {
          "activation_quantization": 751840.0,
          "staging_copies": 0.0,
          "gemm": 496505687.0,
          "grid_wait": 500103.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001505368210233048,
          "staging_copies": 0.0,
          "gemm": 0.9941262468207596,
          "grid_wait": 0.001001328950364676,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 507192477.0,
        "section_ns": {
          "activation_quantization": 921532.0,
          "staging_copies": 0.0,
          "gemm": 502986987.0,
          "grid_wait": 1649963.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018169275803355419,
          "staging_copies": 0.0,
          "gemm": 0.9917082957837327,
          "grid_wait": 0.003253129876372358,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 4971589.0,
        "section_ns": {
          "activation_quantization": 1039727.0,
          "staging_copies": 0.0,
          "gemm": 1785880.0,
          "grid_wait": 512931.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2091337397359275,
          "staging_copies": 0.0,
          "gemm": 0.35921714365366886,
          "grid_wait": 0.1031724464753623,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3984988.0,
        "section_ns": {
          "activation_quantization": 838228.0,
          "staging_copies": 0.0,
          "gemm": 1698127.0,
          "grid_wait": 463178.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21034643015236182,
          "staging_copies": 0.0,
          "gemm": 0.4261310197169979,
          "grid_wait": 0.11623071386915092,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.21.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 315817811.0,
        "section_ns": {
          "activation_quantization": 734691.0,
          "staging_copies": 0.0,
          "gemm": 312511262.0,
          "grid_wait": 869602.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002326312748713213,
          "staging_copies": 0.0,
          "gemm": 0.9895302010056678,
          "grid_wait": 0.002753492582468694,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 328406273.0,
        "section_ns": {
          "activation_quantization": 1817046.0,
          "staging_copies": 0.0,
          "gemm": 323868026.0,
          "grid_wait": 563306.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005532921108361411,
          "staging_copies": 0.0,
          "gemm": 0.9861809978276511,
          "grid_wait": 0.001715271742083928,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 537874607.0,
        "section_ns": {
          "activation_quantization": 815323.0,
          "staging_copies": 0.0,
          "gemm": 533939630.0,
          "grid_wait": 1255081.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0015158235569949486,
          "staging_copies": 0.0,
          "gemm": 0.9926842112477714,
          "grid_wait": 0.0023334081655206305,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526905654.0,
        "section_ns": {
          "activation_quantization": 2501983.0,
          "staging_copies": 0.0,
          "gemm": 521995593.0,
          "grid_wait": 682560.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0047484459143799585,
          "staging_copies": 0.0,
          "gemm": 0.9906813279327612,
          "grid_wait": 0.0012954121763893618,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 522749489.0,
        "section_ns": {
          "activation_quantization": 748853.0,
          "staging_copies": 0.0,
          "gemm": 519823908.0,
          "grid_wait": 476929.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014325274644123086,
          "staging_copies": 0.0,
          "gemm": 0.9944034742040656,
          "grid_wait": 0.0009123471376554516,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 518190515.0,
        "section_ns": {
          "activation_quantization": 982287.0,
          "staging_copies": 0.0,
          "gemm": 515090281.0,
          "grid_wait": 472179.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018956097642968243,
          "staging_copies": 0.0,
          "gemm": 0.994017192692151,
          "grid_wait": 0.0009112073384824499,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 4998134.0,
        "section_ns": {
          "activation_quantization": 1100453.0,
          "staging_copies": 0.0,
          "gemm": 1765083.0,
          "grid_wait": 510348.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2201727684771957,
          "staging_copies": 0.0,
          "gemm": 0.3531483949810069,
          "grid_wait": 0.10210770659610166,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3611717.0,
        "section_ns": {
          "activation_quantization": 669729.0,
          "staging_copies": 0.0,
          "gemm": 1623675.0,
          "grid_wait": 434472.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18543230269702748,
          "staging_copies": 0.0,
          "gemm": 0.44955764806600296,
          "grid_wait": 0.12029513940322567,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.22.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 293447255.0,
        "section_ns": {
          "activation_quantization": 734073.0,
          "staging_copies": 0.0,
          "gemm": 290513836.0,
          "grid_wait": 440238.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00250155006561571,
          "staging_copies": 0.0,
          "gemm": 0.990003590253383,
          "grid_wait": 0.0015002287208309378,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65445646.0,
        "section_ns": {
          "activation_quantization": 968570.0,
          "staging_copies": 0.0,
          "gemm": 62206527.0,
          "grid_wait": 588209.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.014799609434674997,
          "staging_copies": 0.0,
          "gemm": 0.9505067304248169,
          "grid_wait": 0.00898774839811345,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 282787125.0,
        "section_ns": {
          "activation_quantization": 747485.0,
          "staging_copies": 0.0,
          "gemm": 279537368.0,
          "grid_wait": 493562.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026432780488149874,
          "staging_copies": 0.0,
          "gemm": 0.988508115424279,
          "grid_wait": 0.0017453482014076842,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 542326026.0,
        "section_ns": {
          "activation_quantization": 709728.0,
          "staging_copies": 0.0,
          "gemm": 539470318.0,
          "grid_wait": 481637.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013086740557791338,
          "staging_copies": 0.0,
          "gemm": 0.9947343334763727,
          "grid_wait": 0.0008880949408834013,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66585705.0,
        "section_ns": {
          "activation_quantization": 889159.0,
          "staging_copies": 0.0,
          "gemm": 63496379.0,
          "grid_wait": 502853.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.013353601948045756,
          "staging_copies": 0.0,
          "gemm": 0.9536037652526169,
          "grid_wait": 0.007551966296669833,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 521814133.0,
        "section_ns": {
          "activation_quantization": 2411263.0,
          "staging_copies": 0.0,
          "gemm": 517027485.0,
          "grid_wait": 660195.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004620923136246293,
          "staging_copies": 0.0,
          "gemm": 0.9908269100101204,
          "grid_wait": 0.001265191872447809,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 525154142.0,
        "section_ns": {
          "activation_quantization": 762483.0,
          "staging_copies": 0.0,
          "gemm": 522092684.0,
          "grid_wait": 503925.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001451922281515586,
          "staging_copies": 0.0,
          "gemm": 0.9941703630321933,
          "grid_wait": 0.0009595754078618692,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.23.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 521877594.0,
        "section_ns": {
          "activation_quantization": 986780.0,
          "staging_copies": 0.0,
          "gemm": 518718358.0,
          "grid_wait": 472131.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018908265297168515,
          "staging_copies": 0.0,
          "gemm": 0.9939464042213699,
          "grid_wait": 0.0009046776589531069,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 326051002.0,
        "section_ns": {
          "activation_quantization": 1636959.0,
          "staging_copies": 0.0,
          "gemm": 321712874.0,
          "grid_wait": 551439.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0050205611697522095,
          "staging_copies": 0.0,
          "gemm": 0.986694940443704,
          "grid_wait": 0.0016912660798999784,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 544757732.0,
        "section_ns": {
          "activation_quantization": 717474.0,
          "staging_copies": 0.0,
          "gemm": 541853262.0,
          "grid_wait": 504887.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013170515219047868,
          "staging_copies": 0.0,
          "gemm": 0.9946683271674976,
          "grid_wait": 0.0009268101586119387,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 530335209.0,
        "section_ns": {
          "activation_quantization": 2365688.0,
          "staging_copies": 0.0,
          "gemm": 525644822.0,
          "grid_wait": 634566.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0044607409801448806,
          "staging_copies": 0.0,
          "gemm": 0.991155806892693,
          "grid_wait": 0.0011965375657342033,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 514687888.0,
        "section_ns": {
          "activation_quantization": 738200.0,
          "staging_copies": 0.0,
          "gemm": 511754480.0,
          "grid_wait": 501390.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001434267285497109,
          "staging_copies": 0.0,
          "gemm": 0.9943006080609381,
          "grid_wait": 0.0009741632000479483,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 515538364.0,
        "section_ns": {
          "activation_quantization": 962478.0,
          "staging_copies": 0.0,
          "gemm": 512427491.0,
          "grid_wait": 491446.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018669376853591444,
          "staging_copies": 0.0,
          "gemm": 0.9939657778795294,
          "grid_wait": 0.0009532675632263907,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5256831.0,
        "section_ns": {
          "activation_quantization": 1228656.0,
          "staging_copies": 0.0,
          "gemm": 1814630.0,
          "grid_wait": 526933.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.23372560388568703,
          "staging_copies": 0.0,
          "gemm": 0.3451946619550828,
          "grid_wait": 0.10023776682187424,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3733598.0,
        "section_ns": {
          "activation_quantization": 770898.0,
          "staging_copies": 0.0,
          "gemm": 1636415.0,
          "grid_wait": 435883.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20647589804794195,
          "staging_copies": 0.0,
          "gemm": 0.43829437448809433,
          "grid_wait": 0.11674609853551454,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.24.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 302195411.0,
        "section_ns": {
          "activation_quantization": 746029.0,
          "staging_copies": 0.0,
          "gemm": 299321958.0,
          "grid_wait": 441046.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024686973158569905,
          "staging_copies": 0.0,
          "gemm": 0.990491407561447,
          "grid_wait": 0.0014594728574485202,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 318014818.0,
        "section_ns": {
          "activation_quantization": 1709791.0,
          "staging_copies": 0.0,
          "gemm": 313629945.0,
          "grid_wait": 564847.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005376450728783336,
          "staging_copies": 0.0,
          "gemm": 0.986211733693491,
          "grid_wait": 0.0017761656628214099,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 544447088.0,
        "section_ns": {
          "activation_quantization": 685277.0,
          "staging_copies": 0.0,
          "gemm": 541498216.0,
          "grid_wait": 563605.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001258665929351063,
          "staging_copies": 0.0,
          "gemm": 0.9945837307885463,
          "grid_wait": 0.0010351878307777818,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526387043.0,
        "section_ns": {
          "activation_quantization": 2370522.0,
          "staging_copies": 0.0,
          "gemm": 521680917.0,
          "grid_wait": 647543.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004503382124472239,
          "staging_copies": 0.0,
          "gemm": 0.9910595709704807,
          "grid_wait": 0.001230165158149609,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 523974780.0,
        "section_ns": {
          "activation_quantization": 754519.0,
          "staging_copies": 0.0,
          "gemm": 521024055.0,
          "grid_wait": 483973.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001439991062165244,
          "staging_copies": 0.0,
          "gemm": 0.9943685743806219,
          "grid_wait": 0.0009236570508221789,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 522158769.0,
        "section_ns": {
          "activation_quantization": 967073.0,
          "staging_copies": 0.0,
          "gemm": 519050773.0,
          "grid_wait": 479305.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018520669524559876,
          "staging_copies": 0.0,
          "gemm": 0.9940477950682468,
          "grid_wait": 0.0009179296192189391,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5055800.0,
        "section_ns": {
          "activation_quantization": 1133439.0,
          "staging_copies": 0.0,
          "gemm": 1815214.0,
          "grid_wait": 501439.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.22418588551762333,
          "staging_copies": 0.0,
          "gemm": 0.359035958700898,
          "grid_wait": 0.09918094070176826,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3625763.0,
        "section_ns": {
          "activation_quantization": 667929.0,
          "staging_copies": 0.0,
          "gemm": 1630994.0,
          "grid_wait": 436395.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18421750125421876,
          "staging_copies": 0.0,
          "gemm": 0.44983469686242594,
          "grid_wait": 0.12035949398788613,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.25.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 290093910.0,
        "section_ns": {
          "activation_quantization": 758699.0,
          "staging_copies": 0.0,
          "gemm": 287059924.0,
          "grid_wait": 440584.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026153565236857264,
          "staging_copies": 0.0,
          "gemm": 0.9895413661045143,
          "grid_wait": 0.0015187633549425426,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 329728346.0,
        "section_ns": {
          "activation_quantization": 1854134.0,
          "staging_copies": 0.0,
          "gemm": 325309047.0,
          "grid_wait": 553015.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005623216876840792,
          "staging_copies": 0.0,
          "gemm": 0.9865971517049977,
          "grid_wait": 0.0016771836777417979,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 539801632.0,
        "section_ns": {
          "activation_quantization": 682770.0,
          "staging_copies": 0.0,
          "gemm": 536924085.0,
          "grid_wait": 504865.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012648535304909934,
          "staging_copies": 0.0,
          "gemm": 0.9946692510184927,
          "grid_wait": 0.0009352787581049773,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526765606.0,
        "section_ns": {
          "activation_quantization": 2388058.0,
          "staging_copies": 0.0,
          "gemm": 521981665.0,
          "grid_wait": 669977.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0045334356928383055,
          "staging_copies": 0.0,
          "gemm": 0.9909182738100027,
          "grid_wait": 0.0012718692951263033,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 518819227.0,
        "section_ns": {
          "activation_quantization": 739481.0,
          "staging_copies": 0.0,
          "gemm": 515845211.0,
          "grid_wait": 484295.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014253153343524796,
          "staging_copies": 0.0,
          "gemm": 0.9942677220788504,
          "grid_wait": 0.0009334561535052747,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 514524593.0,
        "section_ns": {
          "activation_quantization": 956901.0,
          "staging_copies": 0.0,
          "gemm": 511416594.0,
          "grid_wait": 487268.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018597769922340719,
          "staging_copies": 0.0,
          "gemm": 0.9939594743530559,
          "grid_wait": 0.0009470256750195807,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5031969.0,
        "section_ns": {
          "activation_quantization": 1040934.0,
          "staging_copies": 0.0,
          "gemm": 1869264.0,
          "grid_wait": 512085.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20686415198503807,
          "staging_copies": 0.0,
          "gemm": 0.371477646225563,
          "grid_wait": 0.1017663264618681,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3628012.0,
        "section_ns": {
          "activation_quantization": 706890.0,
          "staging_copies": 0.0,
          "gemm": 1623374.0,
          "grid_wait": 416295.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1948422441822133,
          "staging_copies": 0.0,
          "gemm": 0.44745552109529957,
          "grid_wait": 0.11474465905845957,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.26.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 314139051.0,
        "section_ns": {
          "activation_quantization": 716172.0,
          "staging_copies": 0.0,
          "gemm": 311289247.0,
          "grid_wait": 423065.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002279792969769938,
          "staging_copies": 0.0,
          "gemm": 0.9909282084130318,
          "grid_wait": 0.0013467443753116832,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65515860.0,
        "section_ns": {
          "activation_quantization": 1010238.0,
          "staging_copies": 0.0,
          "gemm": 62415896.0,
          "grid_wait": 441097.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.015419747218459774,
          "staging_copies": 0.0,
          "gemm": 0.9526837623744846,
          "grid_wait": 0.006732675111034183,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 306147313.0,
        "section_ns": {
          "activation_quantization": 743100.0,
          "staging_copies": 0.0,
          "gemm": 302896310.0,
          "grid_wait": 466540.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024272628517239348,
          "staging_copies": 0.0,
          "gemm": 0.9893809193745888,
          "grid_wait": 0.001523906891189994,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 538389393.0,
        "section_ns": {
          "activation_quantization": 684184.0,
          "staging_copies": 0.0,
          "gemm": 535576933.0,
          "grid_wait": 478555.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012707976956745134,
          "staging_copies": 0.0,
          "gemm": 0.9947761600867943,
          "grid_wait": 0.0008888640939477053,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 67189013.0,
        "section_ns": {
          "activation_quantization": 860987.0,
          "staging_copies": 0.0,
          "gemm": 63198163.0,
          "grid_wait": 1193992.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.012814401664153036,
          "staging_copies": 0.0,
          "gemm": 0.9406026398988775,
          "grid_wait": 0.017770643542568486,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 525845549.0,
        "section_ns": {
          "activation_quantization": 2441234.0,
          "staging_copies": 0.0,
          "gemm": 520934648.0,
          "grid_wait": 766431.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004642492466927775,
          "staging_copies": 0.0,
          "gemm": 0.9906609440560273,
          "grid_wait": 0.0014575211323125605,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 515272866.0,
        "section_ns": {
          "activation_quantization": 762549.0,
          "staging_copies": 0.0,
          "gemm": 512225077.0,
          "grid_wait": 492376.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014798935676927339,
          "staging_copies": 0.0,
          "gemm": 0.9940850970406038,
          "grid_wait": 0.0009555636100582094,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.27.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 514561592.0,
        "section_ns": {
          "activation_quantization": 942893.0,
          "staging_copies": 0.0,
          "gemm": 511446769.0,
          "grid_wait": 494883.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001832420092481368,
          "staging_copies": 0.0,
          "gemm": 0.9939466469156913,
          "grid_wait": 0.0009617565859831995,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 312370622.0,
        "section_ns": {
          "activation_quantization": 1672130.0,
          "staging_copies": 0.0,
          "gemm": 308055586.0,
          "grid_wait": 552509.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0053530322067226925,
          "staging_copies": 0.0,
          "gemm": 0.9861861657400035,
          "grid_wait": 0.001768761084068911,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 549034888.0,
        "section_ns": {
          "activation_quantization": 690342.0,
          "staging_copies": 0.0,
          "gemm": 544990400.0,
          "grid_wait": 1629083.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012573736479930214,
          "staging_copies": 0.0,
          "gemm": 0.9926334590234638,
          "grid_wait": 0.002967175739841145,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 523724144.0,
        "section_ns": {
          "activation_quantization": 2386775.0,
          "staging_copies": 0.0,
          "gemm": 518992208.0,
          "grid_wait": 632483.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004557313286667953,
          "staging_copies": 0.0,
          "gemm": 0.9909648312872129,
          "grid_wait": 0.0012076643921155562,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 517675890.0,
        "section_ns": {
          "activation_quantization": 741073.0,
          "staging_copies": 0.0,
          "gemm": 513908855.0,
          "grid_wait": 1331416.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001431538563636796,
          "staging_copies": 0.0,
          "gemm": 0.9927231785895998,
          "grid_wait": 0.002571910389722805,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 524508383.0,
        "section_ns": {
          "activation_quantization": 960610.0,
          "staging_copies": 0.0,
          "gemm": 521261162.0,
          "grid_wait": 486247.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018314483259650781,
          "staging_copies": 0.0,
          "gemm": 0.9938090198264763,
          "grid_wait": 0.0009270528665697227,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5322779.0,
        "section_ns": {
          "activation_quantization": 1096563.0,
          "staging_copies": 0.0,
          "gemm": 1874955.0,
          "grid_wait": 673893.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20601324984561636,
          "staging_copies": 0.0,
          "gemm": 0.35225114550125036,
          "grid_wait": 0.12660548183571024,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3626893.0,
        "section_ns": {
          "activation_quantization": 660055.0,
          "staging_copies": 0.0,
          "gemm": 1619582.0,
          "grid_wait": 437686.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1819891019668901,
          "staging_copies": 0.0,
          "gemm": 0.44654805090748473,
          "grid_wait": 0.12067794666123319,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.28.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 298627033.0,
        "section_ns": {
          "activation_quantization": 715866.0,
          "staging_copies": 0.0,
          "gemm": 295761364.0,
          "grid_wait": 443255.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.002397190879902691,
          "staging_copies": 0.0,
          "gemm": 0.9904038526880452,
          "grid_wait": 0.0014843096940925639,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 318599923.0,
        "section_ns": {
          "activation_quantization": 1537255.0,
          "staging_copies": 0.0,
          "gemm": 314425911.0,
          "grid_wait": 559101.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004825032553444779,
          "staging_copies": 0.0,
          "gemm": 0.9868988920000461,
          "grid_wait": 0.0017548685973787885,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 539091240.0,
        "section_ns": {
          "activation_quantization": 750649.0,
          "staging_copies": 0.0,
          "gemm": 535980031.0,
          "grid_wait": 600343.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013924340525362645,
          "staging_copies": 0.0,
          "gemm": 0.9942287895459032,
          "grid_wait": 0.0011136203956866374,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526254587.0,
        "section_ns": {
          "activation_quantization": 2385579.0,
          "staging_copies": 0.0,
          "gemm": 521148288.0,
          "grid_wait": 1023452.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004533127233340391,
          "staging_copies": 0.0,
          "gemm": 0.9902969035783435,
          "grid_wait": 0.001944784948734328,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 514727303.0,
        "section_ns": {
          "activation_quantization": 741229.0,
          "staging_copies": 0.0,
          "gemm": 511798151.0,
          "grid_wait": 510273.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014400421265393804,
          "staging_copies": 0.0,
          "gemm": 0.9943093129450722,
          "grid_wait": 0.0009913462857438515,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 520045878.0,
        "section_ns": {
          "activation_quantization": 955107.0,
          "staging_copies": 0.0,
          "gemm": 516918626.0,
          "grid_wait": 488639.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001836582194773208,
          "staging_copies": 0.0,
          "gemm": 0.9939865843913102,
          "grid_wait": 0.0009396074859380003,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5105688.0,
        "section_ns": {
          "activation_quantization": 1059786.0,
          "staging_copies": 0.0,
          "gemm": 1943469.0,
          "grid_wait": 490344.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.20756967523279918,
          "staging_copies": 0.0,
          "gemm": 0.38064781866812075,
          "grid_wait": 0.09603877087671632,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 4339448.0,
        "section_ns": {
          "activation_quantization": 680279.0,
          "staging_copies": 0.0,
          "gemm": 1672420.0,
          "grid_wait": 1106160.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.15676625229752725,
          "staging_copies": 0.0,
          "gemm": 0.3853992489367311,
          "grid_wait": 0.2549079975148913,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.29.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 315808379.0,
        "section_ns": {
          "activation_quantization": 725883.0,
          "staging_copies": 0.0,
          "gemm": 312952550.0,
          "grid_wait": 427178.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00229849189656871,
          "staging_copies": 0.0,
          "gemm": 0.9909570828708126,
          "grid_wait": 0.001352649354499869,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65073179.0,
        "section_ns": {
          "activation_quantization": 1022233.0,
          "staging_copies": 0.0,
          "gemm": 61919180.0,
          "grid_wait": 441042.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.015708975890051415,
          "staging_copies": 0.0,
          "gemm": 0.9515315057836655,
          "grid_wait": 0.006777631072857221,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 308592943.0,
        "section_ns": {
          "activation_quantization": 749233.0,
          "staging_copies": 0.0,
          "gemm": 305193881.0,
          "grid_wait": 638968.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024279006276562843,
          "staging_copies": 0.0,
          "gemm": 0.9889852892715049,
          "grid_wait": 0.0020705852628651977,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 539533035.0,
        "section_ns": {
          "activation_quantization": 708800.0,
          "staging_copies": 0.0,
          "gemm": 536680297.0,
          "grid_wait": 510509.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013137286394335427,
          "staging_copies": 0.0,
          "gemm": 0.994712579555022,
          "grid_wait": 0.0009462052680425768,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 67006318.0,
        "section_ns": {
          "activation_quantization": 888738.0,
          "staging_copies": 0.0,
          "gemm": 63973271.0,
          "grid_wait": 457317.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.013263495540823478,
          "staging_copies": 0.0,
          "gemm": 0.9547349102214511,
          "grid_wait": 0.006824983279934886,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 523334371.0,
        "section_ns": {
          "activation_quantization": 2383246.0,
          "staging_copies": 0.0,
          "gemm": 518551752.0,
          "grid_wait": 650054.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004553964218795788,
          "staging_copies": 0.0,
          "gemm": 0.9908612556999433,
          "grid_wait": 0.0012421389383576336,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 525773070.0,
        "section_ns": {
          "activation_quantization": 760121.0,
          "staging_copies": 0.0,
          "gemm": 521966297.0,
          "grid_wait": 1273496.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014457206794558724,
          "staging_copies": 0.0,
          "gemm": 0.9927596653057944,
          "grid_wait": 0.0024221400308692114,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.3.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 519513402.0,
        "section_ns": {
          "activation_quantization": 960612.0,
          "staging_copies": 0.0,
          "gemm": 516385487.0,
          "grid_wait": 477013.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018490610565615399,
          "staging_copies": 0.0,
          "gemm": 0.9939791447382141,
          "grid_wait": 0.0009181919045083653,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 321359787.0,
        "section_ns": {
          "activation_quantization": 1810680.0,
          "staging_copies": 0.0,
          "gemm": 316893484.0,
          "grid_wait": 558144.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0056344324126652474,
          "staging_copies": 0.0,
          "gemm": 0.9861018609649501,
          "grid_wait": 0.0017368196724626282,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 541999403.0,
        "section_ns": {
          "activation_quantization": 732265.0,
          "staging_copies": 0.0,
          "gemm": 539050066.0,
          "grid_wait": 517131.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001351043923566831,
          "staging_copies": 0.0,
          "gemm": 0.9945584128254105,
          "grid_wait": 0.0009541172870996687,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526898616.0,
        "section_ns": {
          "activation_quantization": 2363783.0,
          "staging_copies": 0.0,
          "gemm": 522205759.0,
          "grid_wait": 636225.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004486219792993345,
          "staging_copies": 0.0,
          "gemm": 0.9910934345669262,
          "grid_wait": 0.0012074903609160363,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 524662163.0,
        "section_ns": {
          "activation_quantization": 726822.0,
          "staging_copies": 0.0,
          "gemm": 521602163.0,
          "grid_wait": 607475.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013853143055791504,
          "staging_copies": 0.0,
          "gemm": 0.994167675476152,
          "grid_wait": 0.0011578403072302357,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 522987792.0,
        "section_ns": {
          "activation_quantization": 963486.0,
          "staging_copies": 0.0,
          "gemm": 519206843.0,
          "grid_wait": 1104286.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018422724483021966,
          "staging_copies": 0.0,
          "gemm": 0.992770483254416,
          "grid_wait": 0.002111494793744631,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5048594.0,
        "section_ns": {
          "activation_quantization": 1097140.0,
          "staging_copies": 0.0,
          "gemm": 1808556.0,
          "grid_wait": 516520.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21731594974759308,
          "staging_copies": 0.0,
          "gemm": 0.35822963779618644,
          "grid_wait": 0.10230967275245345,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 4636083.0,
        "section_ns": {
          "activation_quantization": 699818.0,
          "staging_copies": 0.0,
          "gemm": 1722504.0,
          "grid_wait": 1210617.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1509502741862042,
          "staging_copies": 0.0,
          "gemm": 0.37154295986504127,
          "grid_wait": 0.26112927658974183,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.30.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 295596023.0,
        "section_ns": {
          "activation_quantization": 726932.0,
          "staging_copies": 0.0,
          "gemm": 292759414.0,
          "grid_wait": 428352.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024592076463762166,
          "staging_copies": 0.0,
          "gemm": 0.9904037646676999,
          "grid_wait": 0.0014491128657708632,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65979736.0,
        "section_ns": {
          "activation_quantization": 965662.0,
          "staging_copies": 0.0,
          "gemm": 62852275.0,
          "grid_wait": 477047.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.014635736038713461,
          "staging_copies": 0.0,
          "gemm": 0.9525996739362522,
          "grid_wait": 0.007230204740437276,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 288635572.0,
        "section_ns": {
          "activation_quantization": 747518.0,
          "staging_copies": 0.0,
          "gemm": 285356242.0,
          "grid_wait": 477520.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025898332448087862,
          "staging_copies": 0.0,
          "gemm": 0.9886385105713859,
          "grid_wait": 0.0016544045374975473,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 532193781.0,
        "section_ns": {
          "activation_quantization": 695471.0,
          "staging_copies": 0.0,
          "gemm": 529085748.0,
          "grid_wait": 541260.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001306800313775181,
          "staging_copies": 0.0,
          "gemm": 0.9941599599413583,
          "grid_wait": 0.0010170355598349242,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 66485583.0,
        "section_ns": {
          "activation_quantization": 870305.0,
          "staging_copies": 0.0,
          "gemm": 63423799.0,
          "grid_wait": 496816.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.013090131134143774,
          "staging_copies": 0.0,
          "gemm": 0.953948151436079,
          "grid_wait": 0.007472537316849579,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 523526188.0,
        "section_ns": {
          "activation_quantization": 2532938.0,
          "staging_copies": 0.0,
          "gemm": 518622992.0,
          "grid_wait": 649101.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004838225972374853,
          "staging_copies": 0.0,
          "gemm": 0.9906342870473559,
          "grid_wait": 0.0012398634774694404,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 522295016.0,
        "section_ns": {
          "activation_quantization": 750691.0,
          "staging_copies": 0.0,
          "gemm": 519188855.0,
          "grid_wait": 517341.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014372930566122807,
          "staging_copies": 0.0,
          "gemm": 0.9940528611132678,
          "grid_wait": 0.0009905149085320775,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.31.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 524217273.0,
        "section_ns": {
          "activation_quantization": 976365.0,
          "staging_copies": 0.0,
          "gemm": 521049110.0,
          "grid_wait": 475512.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018625197037336083,
          "staging_copies": 0.0,
          "gemm": 0.9939563933445589,
          "grid_wait": 0.0009070895304130888,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 314535677.0,
        "section_ns": {
          "activation_quantization": 1812000.0,
          "staging_copies": 0.0,
          "gemm": 310064709.0,
          "grid_wait": 562095.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0057608727165153984,
          "staging_copies": 0.0,
          "gemm": 0.9857854980311184,
          "grid_wait": 0.0017870627757117677,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 551735795.0,
        "section_ns": {
          "activation_quantization": 703014.0,
          "staging_copies": 0.0,
          "gemm": 548650007.0,
          "grid_wait": 693305.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012741859534417194,
          "staging_copies": 0.0,
          "gemm": 0.9944071274186588,
          "grid_wait": 0.0012565887627428631,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 527903804.0,
        "section_ns": {
          "activation_quantization": 2355270.0,
          "staging_copies": 0.0,
          "gemm": 523160501.0,
          "grid_wait": 671222.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004461551483724485,
          "staging_copies": 0.0,
          "gemm": 0.9910148345890685,
          "grid_wait": 0.0012714854390403294,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 522958207.0,
        "section_ns": {
          "activation_quantization": 752944.0,
          "staging_copies": 0.0,
          "gemm": 520023742.0,
          "grid_wait": 498388.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014397785328187803,
          "staging_copies": 0.0,
          "gemm": 0.9943887198618914,
          "grid_wait": 0.000953016882284056,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 518067617.0,
        "section_ns": {
          "activation_quantization": 969937.0,
          "staging_copies": 0.0,
          "gemm": 514887599.0,
          "grid_wait": 495307.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018722208610850116,
          "staging_copies": 0.0,
          "gemm": 0.9938617703642342,
          "grid_wait": 0.0009560663198140022,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5220145.0,
        "section_ns": {
          "activation_quantization": 1126525.0,
          "staging_copies": 0.0,
          "gemm": 1925386.0,
          "grid_wait": 517972.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21580339243450133,
          "staging_copies": 0.0,
          "gemm": 0.3688376472301057,
          "grid_wait": 0.09922559622385968,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3605903.0,
        "section_ns": {
          "activation_quantization": 671309.0,
          "staging_copies": 0.0,
          "gemm": 1638047.0,
          "grid_wait": 422687.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18616945602807397,
          "staging_copies": 0.0,
          "gemm": 0.45426818192280827,
          "grid_wait": 0.11722084592957714,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.4.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 292442437.0,
        "section_ns": {
          "activation_quantization": 733186.0,
          "staging_copies": 0.0,
          "gemm": 289560580.0,
          "grid_wait": 440732.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025071121945273627,
          "staging_copies": 0.0,
          "gemm": 0.9901455581154249,
          "grid_wait": 0.0015070726551222112,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 312080138.0,
        "section_ns": {
          "activation_quantization": 1517121.0,
          "staging_copies": 0.0,
          "gemm": 307841225.0,
          "grid_wait": 563691.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004861318665528147,
          "staging_copies": 0.0,
          "gemm": 0.9864172291541348,
          "grid_wait": 0.0018062379862187833,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 537388893.0,
        "section_ns": {
          "activation_quantization": 667900.0,
          "staging_copies": 0.0,
          "gemm": 534483022.0,
          "grid_wait": 539138.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012428615639437863,
          "staging_copies": 0.0,
          "gemm": 0.994592610606859,
          "grid_wait": 0.0010032548253653616,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 526556208.0,
        "section_ns": {
          "activation_quantization": 2389771.0,
          "staging_copies": 0.0,
          "gemm": 521639295.0,
          "grid_wait": 669545.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004538491738758496,
          "staging_copies": 0.0,
          "gemm": 0.9906621307938316,
          "grid_wait": 0.0012715546599348041,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 510313436.0,
        "section_ns": {
          "activation_quantization": 726647.0,
          "staging_copies": 0.0,
          "gemm": 506501001.0,
          "grid_wait": 1227526.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014239229241065877,
          "staging_copies": 0.0,
          "gemm": 0.9925292286444913,
          "grid_wait": 0.0024054353920636338,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 521695760.0,
        "section_ns": {
          "activation_quantization": 939235.0,
          "staging_copies": 0.0,
          "gemm": 518635383.0,
          "grid_wait": 486881.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001800350073767132,
          "staging_copies": 0.0,
          "gemm": 0.9941337897781649,
          "grid_wait": 0.0009332661626385463,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 6064210.0,
        "section_ns": {
          "activation_quantization": 1040989.0,
          "staging_copies": 0.0,
          "gemm": 2003932.0,
          "grid_wait": 1378501.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.17166110672288723,
          "staging_copies": 0.0,
          "gemm": 0.3304522765537473,
          "grid_wait": 0.2273174906541825,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3879605.0,
        "section_ns": {
          "activation_quantization": 720599.0,
          "staging_copies": 0.0,
          "gemm": 1732965.0,
          "grid_wait": 421335.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1857403008811464,
          "staging_copies": 0.0,
          "gemm": 0.44668593838805754,
          "grid_wait": 0.10860255103290155,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.5.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 322982749.0,
        "section_ns": {
          "activation_quantization": 736134.0,
          "staging_copies": 0.0,
          "gemm": 319881907.0,
          "grid_wait": 458402.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0022791743592472796,
          "staging_copies": 0.0,
          "gemm": 0.99039935721149,
          "grid_wait": 0.001419277040087364,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 325390639.0,
        "section_ns": {
          "activation_quantization": 1800288.0,
          "staging_copies": 0.0,
          "gemm": 320959313.0,
          "grid_wait": 526761.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.005532697577080575,
          "staging_copies": 0.0,
          "gemm": 0.9863815197215923,
          "grid_wait": 0.0016188572652822996,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 550373369.0,
        "section_ns": {
          "activation_quantization": 715318.0,
          "staging_copies": 0.0,
          "gemm": 547322423.0,
          "grid_wait": 539230.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0012996958797256049,
          "staging_copies": 0.0,
          "gemm": 0.9944565886144829,
          "grid_wait": 0.000979753073771998,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 523618512.0,
        "section_ns": {
          "activation_quantization": 2417035.0,
          "staging_copies": 0.0,
          "gemm": 518811296.0,
          "grid_wait": 653346.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00461602281930017,
          "staging_copies": 0.0,
          "gemm": 0.990819239790361,
          "grid_wait": 0.0012477519129422987,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 523775142.0,
        "section_ns": {
          "activation_quantization": 745762.0,
          "staging_copies": 0.0,
          "gemm": 520027247.0,
          "grid_wait": 1297281.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014238209113024306,
          "staging_copies": 0.0,
          "gemm": 0.9928444580518103,
          "grid_wait": 0.0024767899351741287,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 521868390.0,
        "section_ns": {
          "activation_quantization": 964158.0,
          "staging_copies": 0.0,
          "gemm": 518757131.0,
          "grid_wait": 473467.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001847511783574399,
          "staging_copies": 0.0,
          "gemm": 0.9940382305967985,
          "grid_wait": 0.0009072536468437952,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5180730.0,
        "section_ns": {
          "activation_quantization": 1119194.0,
          "staging_copies": 0.0,
          "gemm": 1922669.0,
          "grid_wait": 509857.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.2160301733539482,
          "staging_copies": 0.0,
          "gemm": 0.371119321022327,
          "grid_wait": 0.09841412310620318,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3937567.0,
        "section_ns": {
          "activation_quantization": 855557.0,
          "staging_copies": 0.0,
          "gemm": 1715178.0,
          "grid_wait": 457380.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21728062024087463,
          "staging_copies": 0.0,
          "gemm": 0.4355933499036334,
          "grid_wait": 0.11615802346982286,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.6.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 295198392.0,
        "section_ns": {
          "activation_quantization": 745658.0,
          "staging_copies": 0.0,
          "gemm": 292297803.0,
          "grid_wait": 453509.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0025259554936871067,
          "staging_copies": 0.0,
          "gemm": 0.9901741029808862,
          "grid_wait": 0.001536285468655263,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_k.weight": {
        "records": 256,
        "worker_elapsed_ns": 65040144.0,
        "section_ns": {
          "activation_quantization": 974603.0,
          "staging_copies": 0.0,
          "gemm": 61965186.0,
          "grid_wait": 435962.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.014984637795389874,
          "staging_copies": 0.0,
          "gemm": 0.9527221526446805,
          "grid_wait": 0.006702967939308376,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_output.weight": {
        "records": 256,
        "worker_elapsed_ns": 283697013.0,
        "section_ns": {
          "activation_quantization": 752335.0,
          "staging_copies": 0.0,
          "gemm": 280435519.0,
          "grid_wait": 481680.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026518960916941344,
          "staging_copies": 0.0,
          "gemm": 0.9885036011993542,
          "grid_wait": 0.001697867717768322,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_q.weight": {
        "records": 256,
        "worker_elapsed_ns": 532749855.0,
        "section_ns": {
          "activation_quantization": 704685.0,
          "staging_copies": 0.0,
          "gemm": 529743936.0,
          "grid_wait": 501515.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013227314721652999,
          "staging_copies": 0.0,
          "gemm": 0.9943577291072186,
          "grid_wait": 0.0009413705049248676,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.attn_v.weight": {
        "records": 256,
        "worker_elapsed_ns": 67205447.0,
        "section_ns": {
          "activation_quantization": 865192.0,
          "staging_copies": 0.0,
          "gemm": 64180654.0,
          "grid_wait": 460775.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.012873837443563168,
          "staging_copies": 0.0,
          "gemm": 0.9549918476102094,
          "grid_wait": 0.006856215092208225,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 522247218.0,
        "section_ns": {
          "activation_quantization": 2382113.0,
          "staging_copies": 0.0,
          "gemm": 517491214.0,
          "grid_wait": 631895.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004561274656708655,
          "staging_copies": 0.0,
          "gemm": 0.9908931941883509,
          "grid_wait": 0.0012099537885905981,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 514081586.0,
        "section_ns": {
          "activation_quantization": 762475.0,
          "staging_copies": 0.0,
          "gemm": 510853991.0,
          "grid_wait": 526384.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014831789754087788,
          "staging_copies": 0.0,
          "gemm": 0.993721628846671,
          "grid_wait": 0.0010239308590990848,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.7.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 520850482.0,
        "section_ns": {
          "activation_quantization": 977479.0,
          "staging_copies": 0.0,
          "gemm": 517695690.0,
          "grid_wait": 465890.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001876697888896261,
          "staging_copies": 0.0,
          "gemm": 0.9939429987894299,
          "grid_wait": 0.0008944793488738674,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 328388693.0,
        "section_ns": {
          "activation_quantization": 1534381.0,
          "staging_copies": 0.0,
          "gemm": 324192657.0,
          "grid_wait": 557977.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.004672453810704134,
          "staging_copies": 0.0,
          "gemm": 0.9872223493395371,
          "grid_wait": 0.0016991358469215017,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 543128936.0,
        "section_ns": {
          "activation_quantization": 672940.0,
          "staging_copies": 0.0,
          "gemm": 540249352.0,
          "grid_wait": 525309.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001239005980708787,
          "staging_copies": 0.0,
          "gemm": 0.9946981576396806,
          "grid_wait": 0.0009671902290251021,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 527555034.0,
        "section_ns": {
          "activation_quantization": 2386147.0,
          "staging_copies": 0.0,
          "gemm": 522791197.0,
          "grid_wait": 660676.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00452302953477267,
          "staging_copies": 0.0,
          "gemm": 0.9909699714854773,
          "grid_wait": 0.001252335694705929,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 520755425.0,
        "section_ns": {
          "activation_quantization": 754606.0,
          "staging_copies": 0.0,
          "gemm": 517821058.0,
          "grid_wait": 491304.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.00144906027623236,
          "staging_copies": 0.0,
          "gemm": 0.9943651724799603,
          "grid_wait": 0.0009434448042475985,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 505178299.0,
        "section_ns": {
          "activation_quantization": 975530.0,
          "staging_copies": 0.0,
          "gemm": 502101842.0,
          "grid_wait": 463093.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.001931060779790147,
          "staging_copies": 0.0,
          "gemm": 0.9939101560655123,
          "grid_wait": 0.0009166921875240725,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 4954120.0,
        "section_ns": {
          "activation_quantization": 1047479.0,
          "staging_copies": 0.0,
          "gemm": 1778460.0,
          "grid_wait": 514430.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.21143593615011344,
          "staging_copies": 0.0,
          "gemm": 0.3589860560503177,
          "grid_wait": 0.103838825058739,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3782437.0,
        "section_ns": {
          "activation_quantization": 691339.0,
          "staging_copies": 0.0,
          "gemm": 1777175.0,
          "grid_wait": 417385.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.18277607796243533,
          "staging_copies": 0.0,
          "gemm": 0.469849200396464,
          "grid_wait": 0.11034816971174934,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.8.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 306939524.0,
        "section_ns": {
          "activation_quantization": 752224.0,
          "staging_copies": 0.0,
          "gemm": 304020870.0,
          "grid_wait": 458426.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0024507238109876,
          "staging_copies": 0.0,
          "gemm": 0.9904911105550551,
          "grid_wait": 0.001493538512166325,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.attn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 290910438.0,
        "section_ns": {
          "activation_quantization": 1707257.0,
          "staging_copies": 0.0,
          "gemm": 286561982.0,
          "grid_wait": 559392.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0058686687618957145,
          "staging_copies": 0.0,
          "gemm": 0.9850522517174168,
          "grid_wait": 0.0019229010957661134,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.attn_qkv.weight": {
        "records": 256,
        "worker_elapsed_ns": 485782185.0,
        "section_ns": {
          "activation_quantization": 674889.0,
          "staging_copies": 0.0,
          "gemm": 482874177.0,
          "grid_wait": 546351.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0013892831413733298,
          "staging_copies": 0.0,
          "gemm": 0.9940137615380029,
          "grid_wait": 0.0011246830716939527,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_down.weight": {
        "records": 256,
        "worker_elapsed_ns": 522347516.0,
        "section_ns": {
          "activation_quantization": 2346313.0,
          "staging_copies": 0.0,
          "gemm": 517612940.0,
          "grid_wait": 658101.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0044918620805693655,
          "staging_copies": 0.0,
          "gemm": 0.9909359653200687,
          "grid_wait": 0.0012598911258151746,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 2359296,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_gate.weight": {
        "records": 256,
        "worker_elapsed_ns": 527308413.0,
        "section_ns": {
          "activation_quantization": 744278.0,
          "staging_copies": 0.0,
          "gemm": 524345443.0,
          "grid_wait": 496297.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0014114661963491183,
          "staging_copies": 0.0,
          "gemm": 0.9943809544339661,
          "grid_wait": 0.0009411892315095682,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ffn_up.weight": {
        "records": 256,
        "worker_elapsed_ns": 508245204.0,
        "section_ns": {
          "activation_quantization": 957660.0,
          "staging_copies": 0.0,
          "gemm": 505177964.0,
          "grid_wait": 454932.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0018842479820035843,
          "staging_copies": 0.0,
          "gemm": 0.9939650389696545,
          "grid_wait": 0.0008951033800606213,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_alpha.weight": {
        "records": 256,
        "worker_elapsed_ns": 5219054.0,
        "section_ns": {
          "activation_quantization": 1152691.0,
          "staging_copies": 0.0,
          "gemm": 1818633.0,
          "grid_wait": 658731.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.22086205661025926,
          "staging_copies": 0.0,
          "gemm": 0.34846027651754513,
          "grid_wait": 0.12621655188852232,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_beta.weight": {
        "records": 256,
        "worker_elapsed_ns": 3691933.0,
        "section_ns": {
          "activation_quantization": 708350.0,
          "staging_copies": 0.0,
          "gemm": 1669051.0,
          "grid_wait": 435681.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.1918642618920766,
          "staging_copies": 0.0,
          "gemm": 0.4520805225880318,
          "grid_wait": 0.11800891294614502,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "blk.9.ssm_out.weight": {
        "records": 256,
        "worker_elapsed_ns": 279855333.0,
        "section_ns": {
          "activation_quantization": 737101.0,
          "staging_copies": 0.0,
          "gemm": 276942296.0,
          "grid_wait": 458927.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 0.0026338644045064527,
          "staging_copies": 0.0,
          "gemm": 0.9895909183906815,
          "grid_wait": 0.0016398722692913628,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 1048576,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      },
      "token_embd.weight": {
        "records": 256,
        "worker_elapsed_ns": 13533777326.0,
        "section_ns": {
          "activation_quantization": 502706.0,
          "staging_copies": 0.0,
          "gemm": 13531059870.0,
          "grid_wait": 452432.0,
          "pair_wait": 0.0
        },
        "elapsed_fraction": {
          "activation_quantization": 3.7144544933086924e-05,
          "staging_copies": 0.0,
          "gemm": 0.999799209346028,
          "grid_wait": 3.342983921649311e-05,
          "pair_wait": 0.0
        },
        "packing_input_bytes": 655360,
        "staging_copy_bytes": 0,
        "buffer_sizes": [
          0
        ]
      }
    },
    "ffn_pairs": {
      "adjacent_same_input_pairs": 2048,
      "pairs_by_layer": {
        "blk.0": 64,
        "blk.1": 64,
        "blk.2": 64,
        "blk.3": 64,
        "blk.4": 64,
        "blk.5": 64,
        "blk.6": 64,
        "blk.7": 64,
        "blk.8": 64,
        "blk.9": 64,
        "blk.10": 64,
        "blk.11": 64,
        "blk.12": 64,
        "blk.13": 64,
        "blk.14": 64,
        "blk.15": 64,
        "blk.16": 64,
        "blk.17": 64,
        "blk.18": 64,
        "blk.19": 64,
        "blk.20": 64,
        "blk.21": 64,
        "blk.22": 64,
        "blk.23": 64,
        "blk.24": 64,
        "blk.25": 64,
        "blk.26": 64,
        "blk.27": 64,
        "blk.28": 64,
        "blk.29": 64,
        "blk.30": 64,
        "blk.31": 64
      },
      "smaller_branch_worker_packing_ns": 23831825.0,
      "smaller_branch_input_bytes": 20971520,
      "worker_elapsed_fraction": 0.00023984781710273414,
      "implementation_priority_signal": false,
      "caveat": "Same input addresses/names/shapes in adjacent executions identify a reuse opportunity, not prove a safe lifetime. Worker elapsed overlaps and instrumentation overhead prevent a wall-time savings estimate. No pointer cache is implemented."
    }
  },
  "baseline_timings": {
    "cache_n": 0,
    "prompt_n": 2048,
    "prompt_ms": 221661.627,
    "prompt_per_token_ms": 108.23321630859375,
    "prompt_per_second": 9.239307803149888,
    "predicted_n": 65,
    "predicted_ms": 41486.372,
    "predicted_per_token_ms": 638.251876923077,
    "predicted_per_second": 1.5667795679988599
  },
  "diagnostic_timings": {
    "cache_n": 0,
    "prompt_n": 2048,
    "prompt_ms": 232443.237,
    "prompt_per_token_ms": 113.49767431640625,
    "prompt_per_second": 8.810753224883028,
    "predicted_n": 65,
    "predicted_ms": 45398.154,
    "predicted_per_token_ms": 698.4331384615385,
    "predicted_per_second": 1.4317762788328352
  }
}

Select the next implementation using decode CPU and branch packing evidence; no new optimization qualified by this diagnostic.
