# K1 sustained decode packing audit

Status: failed

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

ValueError: perf samples outside declared decode window
