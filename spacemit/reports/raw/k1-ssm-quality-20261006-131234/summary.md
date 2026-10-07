# K1 hybrid SSM complete-answer pilot

Status: generation completed; judging pending

Complete answers, full prompts and cold input; one pair per task/model is descriptive, not statistical speedup. Operator gates retain their thresholds; quality is collected after exact state checks even if timing is inconclusive. No production defaults change.

## numeric

{
  "cases_per_arm": 432,
  "sha256": {
    "original": "7e154f0a52c2475581a62a64f549a17c7d342d46c55dae7adf05d09c05001c69",
    "control": "7e154f0a52c2475581a62a64f549a17c7d342d46c55dae7adf05d09c05001c69",
    "hybrid": "7e154f0a52c2475581a62a64f549a17c7d342d46c55dae7adf05d09c05001c69"
  },
  "bitwise_equal": true
}

## dispatch_boundary

{
  "targeted_cases": 4,
  "tokens": [
    31,
    32
  ],
  "sequences": 2,
  "projection_padding": 3,
  "reference_state_output_checks": true
}

## operators

{
  "records": 48,
  "comparisons": [
    {
      "model": "2B",
      "tokens": 1,
      "reduction_pct": -0.6678096394560074,
      "control_range_pct": 2.780973508056404,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.232704882,
        0.230553291,
        0.231160322,
        0.229552123,
        0.229178495,
        0.235615357
      ],
      "candidate_ms": [
        0.241244788,
        0.230346662,
        0.236851681,
        0.229385696,
        0.230238258,
        0.229971688
      ]
    },
    {
      "model": "2B",
      "tokens": 32,
      "reduction_pct": 73.60838219263329,
      "control_range_pct": 2.56647590448991,
      "advance": true,
      "clear_regression": false,
      "base_ms": [
        8.44985328,
        8.41007616,
        8.23601794,
        8.26487156,
        8.31087541,
        8.31950322
      ],
      "candidate_ms": [
        2.21322716,
        2.21462986,
        2.15780374,
        2.20025738,
        2.162103,
        2.24546466
      ]
    },
    {
      "model": "4B",
      "tokens": 1,
      "reduction_pct": 0.7034439624877042,
      "control_range_pct": 3.267327588401171,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.30018871,
        0.301857292,
        0.300847742,
        0.304384826,
        0.294570956,
        0.300333402
      ],
      "candidate_ms": [
        0.299192019,
        0.299820779,
        0.29865355,
        0.297297921,
        0.298613141,
        0.295928171
      ]
    },
    {
      "model": "4B",
      "tokens": 32,
      "reduction_pct": 79.0221071678899,
      "control_range_pct": 9.344288020107074,
      "advance": true,
      "clear_regression": false,
      "base_ms": [
        14.1414094,
        13.230939,
        13.6567606,
        13.3154908,
        13.9674566,
        12.8769864
      ],
      "candidate_ms": [
        2.91132316,
        2.88118626,
        2.77391441,
        2.74718809,
        2.89442812,
        2.82371035
      ]
    }
  ],
  "eligible": true
}

## state-2B

{
  "comparisons": 16,
  "bitwise_equal": true,
  "chunks": [
    32,
    1,
    31,
    32
  ],
  "reset": true,
  "rs3_reference_fallback": true
}

## state-4B

{
  "comparisons": 16,
  "bitwise_equal": true,
  "chunks": [
    32,
    1,
    31,
    32
  ],
  "reset": true,
  "rs3_reference_fallback": true
}

## 2B-control-activation

{
  "markers": 84,
  "selected_shapes": [
    [
      0,
      1
    ],
    [
      0,
      2
    ],
    [
      0,
      4
    ],
    [
      0,
      5
    ],
    [
      0,
      10
    ],
    [
      0,
      11
    ],
    [
      0,
      13
    ],
    [
      0,
      16
    ],
    [
      0,
      18
    ],
    [
      0,
      21
    ],
    [
      0,
      28
    ],
    [
      0,
      29
    ],
    [
      0,
      32
    ]
  ]
}

## 2B-hybrid-activation

{
  "markers": 84,
  "selected_shapes": [
    [
      0,
      1
    ],
    [
      0,
      2
    ],
    [
      0,
      4
    ],
    [
      0,
      5
    ],
    [
      0,
      10
    ],
    [
      0,
      11
    ],
    [
      0,
      13
    ],
    [
      0,
      16
    ],
    [
      0,
      18
    ],
    [
      0,
      21
    ],
    [
      0,
      28
    ],
    [
      0,
      29
    ],
    [
      2,
      32
    ]
  ]
}

## 4B-hybrid-activation

{
  "markers": 84,
  "selected_shapes": [
    [
      0,
      1
    ],
    [
      0,
      2
    ],
    [
      0,
      4
    ],
    [
      0,
      5
    ],
    [
      0,
      10
    ],
    [
      0,
      11
    ],
    [
      0,
      13
    ],
    [
      0,
      16
    ],
    [
      0,
      18
    ],
    [
      0,
      21
    ],
    [
      0,
      28
    ],
    [
      0,
      29
    ],
    [
      2,
      32
    ]
  ]
}

## 4B-control-activation

{
  "markers": 84,
  "selected_shapes": [
    [
      0,
      1
    ],
    [
      0,
      2
    ],
    [
      0,
      4
    ],
    [
      0,
      5
    ],
    [
      0,
      10
    ],
    [
      0,
      11
    ],
    [
      0,
      13
    ],
    [
      0,
      16
    ],
    [
      0,
      18
    ],
    [
      0,
      21
    ],
    [
      0,
      28
    ],
    [
      0,
      29
    ],
    [
      0,
      32
    ]
  ]
}


