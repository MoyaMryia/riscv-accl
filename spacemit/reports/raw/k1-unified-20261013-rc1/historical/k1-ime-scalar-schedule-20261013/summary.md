# K1 IME scalar instruction schedule

Status: inconclusive

Engineering screen; warm DDR operator tensors omit production packing, staging and SPERT synchronization. No significance, decode or quality claim.

## numeric

{
  "cases": 288,
  "bitwise_equal": true,
  "modes": [
    1
  ],
  "scalar_m4_reference": true
}

## operators

{
  "records": 96,
  "comparisons": [
    {
      "k": 2048,
      "n": 16,
      "reduction_pct": 0.3860013320007738,
      "control_range_pct": 1.1780494905225465,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.007806669,
        0.007862327,
        0.007899318,
        0.007887567,
        0.007887408,
        0.007844372
      ],
      "candidate_ms": [
        0.007860068,
        0.007848295,
        0.007858119,
        0.00785348,
        0.007769528,
        0.007816026
      ]
    },
    {
      "k": 2048,
      "n": 32,
      "reduction_pct": -1.1078096051891695,
      "control_range_pct": 2.702069144979526,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.019168774,
        0.019580013,
        0.019600511,
        0.019662613,
        0.019697412,
        0.01967583
      ],
      "candidate_ms": [
        0.019971821,
        0.019771346,
        0.019575681,
        0.019742592,
        0.019797874,
        0.019826243
      ]
    },
    {
      "k": 2560,
      "n": 16,
      "reduction_pct": 0.2888841481128557,
      "control_range_pct": 8.52435338672886,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.012263257,
        0.011300464,
        0.011360217,
        0.011300033,
        0.011283896,
        0.011425995
      ],
      "candidate_ms": [
        0.011750967,
        0.011416779,
        0.011294337,
        0.011309266,
        0.01152014,
        0.011443234
      ]
    },
    {
      "k": 2560,
      "n": 32,
      "reduction_pct": -0.16133521424421815,
      "control_range_pct": 0.26284575589038134,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.02364439,
        0.023638823,
        0.0236572,
        0.023693893,
        0.023701032,
        0.023669618
      ],
      "candidate_ms": [
        0.023717113,
        0.023680155,
        0.023719368,
        0.023707545,
        0.023643555,
        0.023766324
      ]
    },
    {
      "k": 6144,
      "n": 16,
      "reduction_pct": -0.10812146000649392,
      "control_range_pct": 2.1673489133229586,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.028459737,
        0.028984182,
        0.02907356,
        0.029060341,
        0.029084781,
        0.029087365
      ],
      "candidate_ms": [
        0.028838283,
        0.028938389,
        0.029014807,
        0.029022905,
        0.029054395,
        0.029069048
      ]
    },
    {
      "k": 6144,
      "n": 32,
      "reduction_pct": 0.049244637533252256,
      "control_range_pct": 1.5194687690855024,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.059089927,
        0.059898585,
        0.059926163,
        0.05999837,
        0.059914983,
        0.059893264
      ],
      "candidate_ms": [
        0.059469495,
        0.059601996,
        0.059777203,
        0.059925624,
        0.059883427,
        0.059886896
      ]
    },
    {
      "k": 9216,
      "n": 16,
      "reduction_pct": 0.33505059079069754,
      "control_range_pct": 1.8289028540854297,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.04020878,
        0.040525256,
        0.040453452,
        0.040433472,
        0.040949503,
        0.040435227
      ],
      "candidate_ms": [
        0.040270265,
        0.040377496,
        0.040347364,
        0.040401219,
        0.040423243,
        0.040371911
      ]
    },
    {
      "k": 9216,
      "n": 32,
      "reduction_pct": -0.46838950243268673,
      "control_range_pct": 7.417603527828395,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        0.116232591,
        0.125244326,
        0.124083851,
        0.125178182,
        0.124528403,
        0.125389084
      ],
      "candidate_ms": [
        0.123060425,
        0.124010241,
        0.124153148,
        0.124979568,
        0.124288264,
        0.123633948
      ]
    }
  ]
}

算子初筛未通过；保留原内核，不执行模型性能测试。
