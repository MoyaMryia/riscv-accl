# K1 fixed K32 M1 specialization

Status: inconclusive

One fixed K32 M1 specialization only. Repeated production operators are warm; cold ABBA uses complete prompts and 64 capped tokens, which does not establish useful-answer speedup. RS reference behavior is not rollback qualification. No production defaults changed.

## raw_numeric

{
  "cases": 480,
  "bitwise_equal": true,
  "checks": "M1 Q4_0 scalar reference; K32/K64, M1/2/3/4/7, zero points, N tails, input and output guards"
}

## production_numeric

{
  "cases_per_arm": 104,
  "arms": [
    -1,
    0,
    1
  ],
  "bitwise_equal": true,
  "sha256": {
    "-1": "e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc",
    "0": "e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc",
    "1": "e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc"
  },
  "full_shape_checks": [
    {
      "model": "2B",
      "m": 1,
      "k": 2048,
      "n": 6144,
      "sha256": {
        "-1": "3ae0c75777c7f09c71c782dc3d796ae27c0d7b0591c5af4a1d523db6b6771f08",
        "0": "3ae0c75777c7f09c71c782dc3d796ae27c0d7b0591c5af4a1d523db6b6771f08",
        "1": "3ae0c75777c7f09c71c782dc3d796ae27c0d7b0591c5af4a1d523db6b6771f08"
      }
    },
    {
      "model": "2B",
      "m": 1,
      "k": 6144,
      "n": 2048,
      "sha256": {
        "-1": "f77a9b4b0394ffd6293b1fd7fbe2fa2d565354f8293ffabdc22230d3b3fa062c",
        "0": "f77a9b4b0394ffd6293b1fd7fbe2fa2d565354f8293ffabdc22230d3b3fa062c",
        "1": "f77a9b4b0394ffd6293b1fd7fbe2fa2d565354f8293ffabdc22230d3b3fa062c"
      }
    },
    {
      "model": "2B",
      "m": 1,
      "k": 2048,
      "n": 248320,
      "sha256": {
        "-1": "015852f8a35a52164411ed8a123696bf044e3b1c3b4bd9f6ad79b6bd3decafe0",
        "0": "015852f8a35a52164411ed8a123696bf044e3b1c3b4bd9f6ad79b6bd3decafe0",
        "1": "015852f8a35a52164411ed8a123696bf044e3b1c3b4bd9f6ad79b6bd3decafe0"
      }
    },
    {
      "model": "4B",
      "m": 1,
      "k": 2560,
      "n": 9216,
      "sha256": {
        "-1": "f9f82f7a9d2f62b7603decc9db0a07cf5c4d828b8fd34de25adba2ef6a59e254",
        "0": "f9f82f7a9d2f62b7603decc9db0a07cf5c4d828b8fd34de25adba2ef6a59e254",
        "1": "f9f82f7a9d2f62b7603decc9db0a07cf5c4d828b8fd34de25adba2ef6a59e254"
      }
    },
    {
      "model": "4B",
      "m": 1,
      "k": 9216,
      "n": 2560,
      "sha256": {
        "-1": "7a98032d0359a5a5b4c882f8727327f009c45b458e4217d086e8c2c4b8009857",
        "0": "7a98032d0359a5a5b4c882f8727327f009c45b458e4217d086e8c2c4b8009857",
        "1": "7a98032d0359a5a5b4c882f8727327f009c45b458e4217d086e8c2c4b8009857"
      }
    },
    {
      "model": "4B",
      "m": 1,
      "k": 2560,
      "n": 248320,
      "sha256": {
        "-1": "dada06f6bfce6184042d1b20467d448b4e8bdbc6f55d598670ffb3e73f140086",
        "0": "dada06f6bfce6184042d1b20467d448b4e8bdbc6f55d598670ffb3e73f140086",
        "1": "dada06f6bfce6184042d1b20467d448b4e8bdbc6f55d598670ffb3e73f140086"
      }
    }
  ]
}

## operators

{
  "records": 144,
  "comparisons": [
    {
      "model": "2B",
      "m": 1,
      "k": 2048,
      "n": 6144,
      "reduction_pct": -0.2601196563466912,
      "control_range_pct": 9.50492190629579,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        1.399373508,
        1.428675492,
        1.422602813,
        1.529322539,
        1.538025625,
        1.434441234
      ],
      "candidate_ms": [
        1.42431525,
        1.490725664,
        1.536963312,
        1.484952852,
        1.424339609,
        1.413911344
      ]
    },
    {
      "model": "2B",
      "m": 1,
      "k": 6144,
      "n": 2048,
      "reduction_pct": -9.229106407236397,
      "control_range_pct": 26.360628977379353,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        1.924454656,
        1.515589609,
        1.521743172,
        1.492339125,
        1.868401422,
        1.512947445
      ],
      "candidate_ms": [
        1.456137078,
        1.722040469,
        2.025638594,
        1.929184906,
        2.050879016,
        1.559321859
      ]
    },
    {
      "model": "2B",
      "m": 1,
      "k": 2048,
      "n": 248320,
      "reduction_pct": 0.9342996906388179,
      "control_range_pct": 2.5365263710695825,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        45.34230125,
        44.42781075,
        44.68539275,
        45.5693765,
        44.53650375,
        45.4691015
      ],
      "candidate_ms": [
        44.96559375,
        44.49348925,
        44.25822525,
        44.07132575,
        45.15580825,
        44.56315025
      ]
    },
    {
      "model": "4B",
      "m": 1,
      "k": 2560,
      "n": 9216,
      "reduction_pct": -0.41674856377091896,
      "control_range_pct": 2.078760367313634,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        2.270230922,
        2.272296234,
        2.310324047,
        2.262917906,
        2.276841609,
        2.290392406
      ],
      "candidate_ms": [
        2.281331484,
        2.281663656,
        2.297190219,
        2.294080859,
        2.288010562,
        2.297750063
      ]
    },
    {
      "model": "4B",
      "m": 1,
      "k": 9216,
      "n": 2560,
      "reduction_pct": 1.310918960854801,
      "control_range_pct": 6.7232076313466305,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        2.461332422,
        2.453903328,
        2.3098605,
        2.452179516,
        2.301187359,
        2.313381344
      ],
      "candidate_ms": [
        2.303436266,
        2.303774938,
        2.491627766,
        2.350660516,
        2.355505375,
        2.299485109
      ]
    },
    {
      "model": "4B",
      "m": 1,
      "k": 2560,
      "n": 248320,
      "reduction_pct": -1.40180674114323,
      "control_range_pct": 2.2393286746790455,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        56.193178,
        55.6968345,
        55.256908,
        56.2083525,
        55.728435,
        56.5094135
      ],
      "candidate_ms": [
        56.019695,
        56.0484685,
        55.368203,
        55.410164,
        55.982834,
        61.468124
      ]
    },
    {
      "model": "2B",
      "m": 32,
      "k": 2048,
      "n": 6144,
      "reduction_pct": -0.024070158810185482,
      "control_range_pct": 1.0640057732436012,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        7.81377275,
        7.876720125,
        7.79335625,
        7.863389687,
        7.800716375,
        7.861493688
      ],
      "candidate_ms": [
        7.8386015,
        7.848177687,
        7.824932562,
        7.857798312,
        7.865572438,
        7.785681625
      ]
    },
    {
      "model": "4B",
      "m": 32,
      "k": 2560,
      "n": 9216,
      "reduction_pct": -0.3736049860760593,
      "control_range_pct": 1.7660279915027586,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        13.95129725,
        13.823841375,
        13.854145,
        13.827743625,
        14.069257375,
        13.85268825
      ],
      "candidate_ms": [
        13.863456375,
        14.013857,
        14.0038885,
        13.94361125,
        13.999474,
        13.86619375
      ]
    }
  ],
  "original_control_checks": [
    {
      "model": "2B",
      "m": 1,
      "k": 2048,
      "n": 6144,
      "reduction_pct": 0.9915065587576044,
      "control_range_pct": 7.467783237699256,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        1.499542203,
        1.423025922,
        1.533052398,
        1.491859289,
        1.469493172,
        1.423118312
      ],
      "candidate_ms": [
        1.399373508,
        1.428675492,
        1.422602813,
        1.529322539,
        1.538025625,
        1.434441234
      ]
    },
    {
      "model": "2B",
      "m": 1,
      "k": 6144,
      "n": 2048,
      "reduction_pct": -3.6135747377572525,
      "control_range_pct": 34.58577808043039,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        1.502335578,
        1.468800914,
        1.534532258,
        2.015974344,
        1.474390766,
        1.496424492
      ],
      "candidate_ms": [
        1.924454656,
        1.515589609,
        1.521743172,
        1.492339125,
        1.868401422,
        1.512947445
      ]
    },
    {
      "model": "2B",
      "m": 1,
      "k": 2048,
      "n": 248320,
      "reduction_pct": -1.1450579050105603,
      "control_range_pct": 2.0252640406869187,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        44.91896675,
        44.09529175,
        44.1889625,
        44.99644475,
        44.33224025,
        44.4415795
      ],
      "candidate_ms": [
        45.34230125,
        44.42781075,
        44.68539275,
        45.5693765,
        44.53650375,
        45.4691015
      ]
    },
    {
      "model": "4B",
      "m": 1,
      "k": 2560,
      "n": 9216,
      "reduction_pct": 0.8398028237345367,
      "control_range_pct": 1.7559834186166436,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        2.306808094,
        2.317836516,
        2.303849922,
        2.277452156,
        2.292948875,
        2.299991
      ],
      "candidate_ms": [
        2.270230922,
        2.272296234,
        2.310324047,
        2.262917906,
        2.276841609,
        2.290392406
      ]
    },
    {
      "model": "4B",
      "m": 1,
      "k": 9216,
      "n": 2560,
      "reduction_pct": -1.8986844255843183,
      "control_range_pct": 8.656005341230687,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        2.475908984,
        2.294889937,
        2.347828328,
        2.315262422,
        2.318086969,
        2.273567016
      ],
      "candidate_ms": [
        2.461332422,
        2.453903328,
        2.3098605,
        2.452179516,
        2.301187359,
        2.313381344
      ]
    },
    {
      "model": "4B",
      "m": 1,
      "k": 2560,
      "n": 248320,
      "reduction_pct": 0.029001865224198564,
      "control_range_pct": 1.7709331630192955,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        55.504138,
        56.4754395,
        55.7852345,
        56.4401925,
        56.000843,
        55.4846305
      ],
      "candidate_ms": [
        56.193178,
        55.6968345,
        55.256908,
        56.2083525,
        55.728435,
        56.5094135
      ]
    },
    {
      "model": "2B",
      "m": 32,
      "k": 2048,
      "n": 6144,
      "reduction_pct": -2.0042788773967812,
      "control_range_pct": 3.0127482830809535,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        7.612407938,
        7.651883375,
        7.843815937,
        7.62727125,
        7.644940938,
        7.70544225
      ],
      "candidate_ms": [
        7.81377275,
        7.876720125,
        7.79335625,
        7.863389687,
        7.800716375,
        7.861493688
      ]
    },
    {
      "model": "4B",
      "m": 32,
      "k": 2560,
      "n": 9216,
      "reduction_pct": -1.4299458311737734,
      "control_range_pct": 1.7724736434527206,
      "advance": false,
      "clear_regression": false,
      "base_ms": [
        13.731822625,
        13.826914375,
        13.584075125,
        13.7082715,
        13.6441355,
        13.708288125
      ],
      "candidate_ms": [
        13.95129725,
        13.823841375,
        13.854145,
        13.827743625,
        14.069257375,
        13.85268825
      ]
    }
  ]
}

Operator/control gates did not justify long model tests; candidate remains disabled.
