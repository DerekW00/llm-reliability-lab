# LLM Reliability Lab

**SYNTHETIC FIXTURE EVALUATION**
Authored fixtures, no live model calls. These scores are not model accuracy or production evidence.

**Decision: ACCEPTED**
Dataset: "synthetic\-invoices\-evaluation\-v1"; split: evaluation; scenario: "baseline".

## Coverage and metrics

Cases: 40; predictions: 40; complete coverage: true; schema valid: true.

Rates show numerator/denominator. A zero denominator is null (undefined). Wrong non-null values count as both FP and FN. TP = correct values; FP = wrong or invented values; FN = wrong or missed values; TN = correct nulls.

| Scope | TP | FP | FN | TN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| micro | 182 | 1 | 1 | 17 | 99.4536% (182/183) | 99.4536% (182/183) | 99.4536% (364/366) |
| invoice\_id | 37 | 0 | 0 | 3 | 100.0000% (37/37) | 100.0000% (37/37) | 100.0000% (74/74) |
| supplier\_name | 37 | 1 | 1 | 2 | 97.3684% (37/38) | 97.3684% (37/38) | 97.3684% (74/76) |
| currency | 36 | 0 | 0 | 4 | 100.0000% (36/36) | 100.0000% (36/36) | 100.0000% (72/72) |
| total\_amount | 37 | 0 | 0 | 3 | 100.0000% (37/37) | 100.0000% (37/37) | 100.0000% (74/74) |
| due\_date | 35 | 0 | 0 | 5 | 100.0000% (35/35) | 100.0000% (35/35) | 100.0000% (70/70) |

Exact-record accuracy: 97.5000% (39/40).
Critical failures: **0 field mismatches** (not a count of records).

| Abstention measure | Count |
| --- | ---: |
| expected null | 17 |
| predicted null | 17 |
| correct abstention | 17 |
| missed value | 0 |
| unsupported value | 0 |

## Gate checks

All required policy checks passed.

| Rule | Result | Actual | Required |
| --- | --- | --- | --- |
| critical\_failure\_count | PASS | 0 | 0 |
| micro\_f1 | PASS | 0\.994535519125683 | 0\.98 |
| exact\_record\_accuracy | PASS | 0\.975 | 0\.95 |
| field\_f1\.invoice\_id | PASS | 1\.0 | 0\.9 |
| field\_f1\.supplier\_name | PASS | 0\.9736842105263158 | 0\.9 |
| field\_f1\.currency | PASS | 1\.0 | 0\.9 |
| field\_f1\.total\_amount | PASS | 1\.0 | 0\.9 |
| field\_f1\.due\_date | PASS | 1\.0 | 0\.9 |

## Representative differences

Showing 1 of 1 field differences, critical first. The JSON report contains every difference.

### "EVAL\-02" / supplier\_name (noncritical)

Category: wrong\_value. Expected: "Copper Vale Binding"; actual: "Copper Vale Bindery".

Action: Check supplier selection and spelling against the cited source\.

- Expected evidence lines: \[1\].
  - Line 1: "\[ seller = Copper Vale Binding \]"
- Actual evidence lines: \[1\].
  - Line 1: "\[ seller = Copper Vale Binding \]"


## Reproducibility and limits

Timestamp (UTC): 2026\-09\-12T10:24:15\.993079Z.
Code revision: "5ce81ab5057a822c5c115bcff4d22f35a0d31c68"; working tree dirty: false; Python: 3\.12\.14.
Evaluation time: 0.046635 seconds (fixture\_evaluation); this is not model latency.

- dataset\_sha256: 9007d10d0528565e20efc317a01e917f55586db0d6ff2a83e862bb65980ed88f
- predictions\_sha256: 3a3f032762a8fc4c5e2c30f603ff7dcabd4a87d96f25edc76375129240410ea4
- policy\_sha256: 893762e325fe8ad26f5b84448a1690fe6b7796dbd01afae24d5294cfdd42ba3d

The JSON embeds validated inputs and any comparison baseline. Reports support reproduction; they are not signed evidence or secure attestations. Evidence line references aid inspection and do not prove semantic entailment. Policy thresholds are illustrative, not calibrated production guarantees.
