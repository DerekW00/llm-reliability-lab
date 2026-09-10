# LLM Reliability Lab

**SYNTHETIC FIXTURE EVALUATION**
Authored fixtures, no live model calls. These scores are not model accuracy or production evidence.

**Decision: REJECTED**
Dataset: "synthetic\-invoices\-evaluation\-v1"; split: evaluation; scenario: "regression".

## Coverage and metrics

Cases: 40; predictions: 40; complete coverage: true; schema valid: true.

Rates show numerator/denominator. A zero denominator is null (undefined). Wrong non-null values count as both FP and FN. TP = correct values; FP = wrong or invented values; FN = wrong or missed values; TN = correct nulls.

| Scope | TP | FP | FN | TN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| micro | 174 | 9 | 9 | 17 | 95.0820% (174/183) | 95.0820% (174/183) | 95.0820% (348/366) |
| invoice\_id | 29 | 8 | 8 | 3 | 78.3784% (29/37) | 78.3784% (29/37) | 78.3784% (58/74) |
| supplier\_name | 37 | 1 | 1 | 2 | 97.3684% (37/38) | 97.3684% (37/38) | 97.3684% (74/76) |
| currency | 36 | 0 | 0 | 4 | 100.0000% (36/36) | 100.0000% (36/36) | 100.0000% (72/72) |
| total\_amount | 37 | 0 | 0 | 3 | 100.0000% (37/37) | 100.0000% (37/37) | 100.0000% (74/74) |
| due\_date | 35 | 0 | 0 | 5 | 100.0000% (35/35) | 100.0000% (35/35) | 100.0000% (70/70) |

Exact-record accuracy: 77.5000% (31/40).
Critical failures: **8 field mismatches** (not a count of records).

| Abstention measure | Count |
| --- | ---: |
| expected null | 17 |
| predicted null | 17 |
| correct abstention | 17 |
| missed value | 0 |
| unsupported value | 0 |

## Gate checks

Failed rules:

- critical\_failure\_count 8 exceeds maximum 0\.
- micro\_f1 0\.9508196721311475 is below minimum 0\.98\.
- exact\_record\_accuracy 0\.775 is below minimum 0\.95\.
- field\_f1\.invoice\_id 0\.7837837837837838 is below minimum 0\.9\.
- micro\_f1\_drop 0\.04371584699453552 exceeds maximum 0\.005\.
- exact\_record\_accuracy\_drop 0\.2 exceeds maximum 0\.025\.

| Rule | Result | Actual | Required |
| --- | --- | --- | --- |
| critical\_failure\_count | FAIL | 8 | 0 |
| micro\_f1 | FAIL | 0\.9508196721311475 | 0\.98 |
| exact\_record\_accuracy | FAIL | 0\.775 | 0\.95 |
| field\_f1\.invoice\_id | FAIL | 0\.7837837837837838 | 0\.9 |
| field\_f1\.supplier\_name | PASS | 0\.9736842105263158 | 0\.9 |
| field\_f1\.currency | PASS | 1\.0 | 0\.9 |
| field\_f1\.total\_amount | PASS | 1\.0 | 0\.9 |
| field\_f1\.due\_date | PASS | 1\.0 | 0\.9 |
| micro\_f1\_drop | FAIL | 0\.04371584699453552 | 0\.005 |
| exact\_record\_accuracy\_drop | FAIL | 0\.2 | 0\.025 |

## Representative differences

Showing 9 of 9 field differences, critical first. The JSON report contains every difference.

### "EVAL\-01" / invoice\_id (CRITICAL)

Category: identifier\_format. Expected: "000482"; actual: "482".

Action: Keep invoice IDs as strings through postprocessing; preserve leading zeros\.

- Expected evidence lines: \[3\].
  - Line 3: "Enter 000482 in the invoice\-number field of the transfer\."
- Actual evidence lines: \[3\].
  - Line 3: "Enter 000482 in the invoice\-number field of the transfer\."

### "EVAL\-04" / invoice\_id (CRITICAL)

Category: identifier\_format. Expected: "001090"; actual: "1090".

Action: Keep invoice IDs as strings through postprocessing; preserve leading zeros\.

- Expected evidence lines: \[2\].
  - Line 2: "Receipt for invoice no\. 001090"
- Actual evidence lines: \[2\].
  - Line 2: "Receipt for invoice no\. 001090"

### "EVAL\-09" / invoice\_id (CRITICAL)

Category: identifier\_format. Expected: "000063"; actual: "63".

Action: Keep invoice IDs as strings through postprocessing; preserve leading zeros\.

- Expected evidence lines: \[2\].
  - Line 2: "000063"
- Actual evidence lines: \[2\].
  - Line 2: "000063"

### "EVAL\-12" / invoice\_id (CRITICAL)

Category: identifier\_format. Expected: "007501"; actual: "7501".

Action: Keep invoice IDs as strings through postprocessing; preserve leading zeros\.

- Expected evidence lines: \[2\].
  - Line 2: "Card slot I: invoice 007501"
- Actual evidence lines: \[2\].
  - Line 2: "Card slot I: invoice 007501"

### "EVAL\-17" / invoice\_id (CRITICAL)

Category: identifier\_format. Expected: "003008"; actual: "3008".

Action: Keep invoice IDs as strings through postprocessing; preserve leading zeros\.

- Expected evidence lines: \[3\].
  - Line 3: "Document node: invoice 003008"
- Actual evidence lines: \[3\].
  - Line 3: "Document node: invoice 003008"

### "EVAL\-23" / invoice\_id (CRITICAL)

Category: identifier\_format. Expected: "000905"; actual: "905".

Action: Keep invoice IDs as strings through postprocessing; preserve leading zeros\.

- Expected evidence lines: \[2\].
  - Line 2: "invoice\[id\] 000905 ; terms\[due\] 2026\-12\-23"
- Actual evidence lines: \[2\].
  - Line 2: "invoice\[id\] 000905 ; terms\[due\] 2026\-12\-23"

### "EVAL\-31" / invoice\_id (CRITICAL)

Category: identifier\_format. Expected: "0000"; actual: "0".

Action: Keep invoice IDs as strings through postprocessing; preserve leading zeros\.

- Expected evidence lines: \[2\].
  - Line 2: "Tab belongs to invoice 0000\."
- Actual evidence lines: \[2\].
  - Line 2: "Tab belongs to invoice 0000\."

### "EVAL\-37" / invoice\_id (CRITICAL)

Category: identifier\_format. Expected: "000712"; actual: "712".

Action: Keep invoice IDs as strings through postprocessing; preserve leading zeros\.

- Expected evidence lines: \[2\].
  - Line 2: "We endorse invoice 000712 for payment\."
- Actual evidence lines: \[2\].
  - Line 2: "We endorse invoice 000712 for payment\."

### "EVAL\-02" / supplier\_name (noncritical)

Category: wrong\_value. Expected: "Copper Vale Binding"; actual: "Copper Vale Bindery".

Action: Check supplier selection and spelling against the cited source\.

- Expected evidence lines: \[1\].
  - Line 1: "\[ seller = Copper Vale Binding \]"
- Actual evidence lines: \[1\].
  - Line 1: "\[ seller = Copper Vale Binding \]"


## Reproducibility and limits

Timestamp (UTC): 2026\-09\-12T11:20:14\.312483Z.
Code revision: "57655fca4f8e205bd5517f32561c59c5a27806df"; working tree dirty: false; Python: 3\.12\.14.
Evaluation time: 0.043191 seconds (fixture\_evaluation); this is not model latency.

- dataset\_sha256: 9007d10d0528565e20efc317a01e917f55586db0d6ff2a83e862bb65980ed88f
- predictions\_sha256: 2b89cc4c330040e9f27e1d63b0d9f9e3611a0f7a8d4d64a07efea2ff9e24b855
- policy\_sha256: 893762e325fe8ad26f5b84448a1690fe6b7796dbd01afae24d5294cfdd42ba3d

The JSON embeds validated inputs and any comparison baseline. Reports support reproduction; they are not signed evidence or secure attestations. Evidence line references aid inspection and do not prove semantic entailment. Policy thresholds are illustrative, not calibrated production guarantees.
