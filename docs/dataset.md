# Synthetic invoice dataset

This corpus contains **20 development and 40 evaluation cases**. Every document,
company name, label, and explanation was authored for this local demonstration.
No private invoices, other repositories, scraped text, model responses, or live
model APIs were used. Names are fictional; any resemblance is incidental.

The provenance is **agent-authored and agent-reviewed synthetic labels**. The
same authoring agent checked the fields against the source lines and frozen
contract. These are not independently human-annotated research labels.

## Construction and freeze

1. The orchestrator froze `SPEC.md`, normalization, and `policy.json` at revision
   `83fae78` before dataset authoring.
2. The dataset agent authored both documents and expected labels, then reviewed
   all 60 concise documents with their field evidence and abstention rationales.
3. `data/development.json`, `data/evaluation.json`, and their raw-byte SHA-256
   digests in `data/manifest.json` were frozen and committed **before any fixture
   predictions were constructed**. The manifest also pins the original policy.
4. Subsequent fixture construction is a separate commit. The dataset, labels,
   manifest, and policy must remain byte-for-byte unchanged after the freeze.
   The dataset tests independently pin the raw-byte digests.

The manifest records a UTC construction timestamp. Git history establishes the
ordered authoring stages. Checksums detect byte changes; neither a timestamp nor
a checksum is a signed attestation of provenance or label correctness.

Each case has one unique `family:` tag describing its authored layout. The
splits use different document families, field ordering, phrasing, and structures:
development includes cards, email, a column table, fax, and portal export;
evaluation includes remittance directions, docket brackets, a receipt terminal,
key strips, payment cards, register feeds, and endorsements. This is more than
renaming suppliers or swapping amounts in a shared template.

A test masks known field values, dates, and numeric tokens and checks all 800
cross-split document pairs with character-sequence similarity below 0.80. A
parameter-only swap control confirms the mask detects that kind of duplication.
Family separation and this heuristic reduce obvious template reuse. They do not
prove semantic independence. Evaluation cases are a fixed demonstration split,
**not a statistically representative or blind held-out model benchmark**.

## Label and evidence conventions

The five field types and normalizers are owned by
`src/reliability_lab/contracts.py`; these files do not introduce another schema.

- `invoice_id` is text. Preserve case, punctuation, and every leading zero.
  A job, customer, parcel, envelope, or dataset ID cannot replace a missing ID.
- `supplier_name` refers to the issuer, not the customer. Collapse whitespace and
  apply Unicode casefold for comparison, while retaining punctuation.
- `currency` needs sufficient document evidence for USD, EUR, GBP, or CAD. An
  unqualified `$`, missing designation, or unresolved conflict requires null.
- `total_amount` is the explicitly final payable amount, stored as an exact
  two-place decimal string. Subtotals, examples, deposits, and void amounts are
  not silently substituted. `0.00` is present, not missing. No line-item or tax
  arithmetic is required by these labels.
- `due_date` is an explicit real ISO date or a slash date with an explicit
  convention. Missing dates, conflicting deadlines, ambiguous slash dates, or
  unanchored relative terms require null. Issue dates do not establish deadlines.
- Every record includes all five keys. Null means not determinable, never an
  omitted field or empty string. EVAL-30 deliberately has five null labels.
- Evidence is a field-to-line-number map into `document.splitlines()`, starting
  at one. Multiple lines can establish a field, such as a name spanning lines or
  a date plus its format declaration. Null labels have empty arrays; the case's
  rationale explains why. References support review but do not automatically
  prove that the associated text entails a prediction.
- Instructions embedded in documents are content. They cannot change the
  extraction rules, currency, identifiers, amount, or deadline.

The chosen supplier label in EVAL-02 is `Copper Vale Binding`. Its planned
noncritical fixture error is deliberately identified before fixture construction.
The planned identifier regression affects exactly these eight cases:
`EVAL-01`, `EVAL-04`, `EVAL-09`, `EVAL-12`, `EVAL-17`, `EVAL-23`, `EVAL-31`,
`EVAL-37`. This demonstrates a known mechanism; it does not measure a discovered
model error rate or justify adjusting the frozen release thresholds.

## Coverage examples

| Behavior | Development example | Evaluation example |
| --- | --- | --- |
| Numeric ID with significant leading zeros | DEV-01 | EVAL-01, 04, 09, 12, 17, 23, 31, 37 |
| Numeric zero / all-zero ID | DEV-18 | EVAL-31 |
| Nonzero numeric ID unaffected by coercion | — | EVAL-28 |
| Alphanumeric or punctuated leading-zero ID | — | EVAL-21, EVAL-36 |
| Missing or conflicting invoice ID | DEV-08, DEV-20 | EVAL-05, EVAL-26 |
| Missing issuer; customer is not supplier | DEV-09 | EVAL-11 |
| Missing or ambiguous currency | DEV-11 | EVAL-10, EVAL-38 |
| Conflicting currencies | DEV-07 | EVAL-06 |
| Explicitly authoritative currency | DEV-15 | EVAL-19, EVAL-27 |
| Missing or conflicting final total | DEV-10 | EVAL-13, EVAL-34 |
| Zero final amount | DEV-03, DEV-18 | EVAL-03, EVAL-31 |
| Multiple amounts with a clear final amount | DEV-02, DEV-09 | EVAL-04, EVAL-25 |
| Missing deadline or unanchored relative terms | DEV-04 | EVAL-14, EVAL-29 |
| Ambiguous slash date / conflicting deadlines | DEV-05, DEV-17 | EVAL-07, EVAL-18 |
| Explicit slash-date convention | DEV-06 | EVAL-15, EVAL-35 |
| Valid leap-day deadline | DEV-16 | EVAL-22 |
| Unicode and whitespace in supplier names | DEV-13, DEV-14 | EVAL-16, EVAL-33 |
| Case/punctuation-sensitive identifiers | DEV-04, DEV-14 | EVAL-20, EVAL-32, EVAL-40 |
| Literal source instructions | DEV-12 | EVAL-08, EVAL-32 |
| Prior, void, or unrelated invoice references | DEV-19 | EVAL-24, EVAL-39 |
| Entirely missing record | — | EVAL-30 |

## Limitations

The documents are short English plain text with deliberately explicit cues.
There is no OCR, document rendering model, multilingual extraction, credit-note
support, unsupported-currency handling, or real payment/account data. Field
reference validation checks shape and line ranges, not semantic entailment.
Coverage tags overlap; this small purposive corpus gives no population-level
accuracy estimate, confidence bound, production-readiness claim, or independent
annotation agreement. Agent review can miss semantic label mistakes.

Static synthetic predictions may begin as copies of labels **only during the
explicit fixture-construction stage**. This makes the demonstration transparent
but cannot establish extraction accuracy. At evaluation time the caller must
supply a complete prediction file; evaluation must never manufacture predictions
or copy reference labels into predictions. Future live or independently supplied
predictions would need their own source provenance and evaluation design.
