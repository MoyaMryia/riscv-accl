# K1 recurrent prefill fusion screen

Status: inconclusive

Engineering screen; operator graph timing excludes full-model costs. No significance, decode or quality claim.

## numeric

{
  "cases": 158,
  "bitwise_equal": true,
  "attention_and_state": true
}

## operators

{
  "records": 48,
  "comparisons": [
    {
      "heads": 16,
      "tokens": 8,
      "reduction_pct": 24.284240296516167,
      "control_range_pct": 2.828397387962723,
      "advance": true,
      "clear_regression": false,
      "base_ms": [
        3.159145437,
        3.077031875,
        3.071690578,
        3.0823315,
        3.081536547,
        3.080436266
      ],
      "candidate_ms": [
        2.332012687,
        2.338487469,
        2.329476156,
        2.356960641,
        2.346445375,
        2.343535797
      ]
    },
    {
      "heads": 16,
      "tokens": 32,
      "reduction_pct": 26.44648573595465,
      "control_range_pct": 2.6538757632635597,
      "advance": true,
      "clear_regression": false,
      "base_ms": [
        10.21497875,
        10.049864875,
        10.058971875,
        10.319630125,
        10.198241375,
        10.148036875
      ],
      "candidate_ms": [
        7.440816625,
        7.43106375,
        7.423274437,
        7.43052725,
        7.70161025,
        7.432792938
      ]
    },
    {
      "heads": 32,
      "tokens": 8,
      "reduction_pct": 26.14246522385787,
      "control_range_pct": 1.531352547518424,
      "advance": true,
      "clear_regression": false,
      "base_ms": [
        6.212786719,
        6.158121187,
        6.162362156,
        6.248415312,
        6.15374475,
        6.157489656
      ],
      "candidate_ms": [
        4.635031094,
        4.556306281,
        4.546757844,
        4.544218719,
        4.542755125,
        4.570847063
      ]
    },
    {
      "heads": 32,
      "tokens": 32,
      "reduction_pct": 27.82333399637945,
      "control_range_pct": 1.2652417868859631,
      "advance": true,
      "clear_regression": false,
      "base_ms": [
        20.068505,
        20.090463875,
        19.95809575,
        20.085542,
        20.212160125,
        20.06704675
      ],
      "candidate_ms": [
        14.39349475,
        14.51002925,
        14.490794375,
        14.47431475,
        14.517701375,
        14.573421625
      ]
    }
  ]
}

## 2B-512

{
  "reduction_pct": 2.380018547594631,
  "control_range_pct": 0.018692639342656366,
  "advance": false,
  "clear_regression": false,
  "base_ms": [
    22064.222,
    22060.098
  ],
  "candidate_ms": [
    21560.296,
    21513.857
  ],
  "ttft_ms": {
    "0": [
      22068.702,
      22064.466
    ],
    "1": [
      21564.802,
      21518.31
    ]
  },
  "outputs_equal": true,
  "uncached_verified": true,
  "requests": 4
}

2B/512 benefit gate failed; retain control.
