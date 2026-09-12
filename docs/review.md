# Independent adversarial review

Final verdict: **PASS after one confirmed P2 provenance defect was fixed and
independently retested**. Review performed by a fresh AI review agent, not a human
annotator. No unresolved implementation defects were confirmed. This verdict is
for the local synthetic evaluation contract, not model or production reliability.

## Independent first pass — recorded before implementation summaries or tests

Reviewed checkout: `e00e2b1` in isolated `review/adversarial` worktree.
Sources inspected: `AGENTS.md`, `SPEC.md`, the six functional runtime Python modules,
`pyproject.toml`, `policy.json`, all 62 synthetic cases with document lines,
expected values, evidence and rationales, and the raw prediction/freeze files.
No README results, STATUS, implementer documentation, or existing test suite was
read or executed before this assessment.

Preliminary verdict: the arithmetic implementation and replay-based gate appear
consistent with the written contract; acceptance remains unverified until the
execution and adversarial probes below. No inference or scenario-dependent
scoring was visible. The fixture construction is transparently label-derived and
cannot measure model performance or real extraction generalization.

Independent risk register:

1. **Likely provenance defect:** `evaluation._code_provenance` invokes Git from
   `src/reliability_lab` but passes the repository-relative tracked source path to
   `git ls-files`. Git interprets that path relative to its invocation directory.
   The direct command `git -C src/reliability_lab ls-files --error-unmatch --
   src/reliability_lab/evaluation.py` fails in the tracked checkout. Runtime
   verification must determine whether checkout reports therefore lose revision
   and dirty-state provenance.
2. **Report trust:** replay checks reconstruct summary, field metrics, diffs,
   decisions and hashes; probes still need to try nested-baseline replacement,
   aggregate/type tampering, and preservation of an existing relative rejection.
3. **Output safety:** destinations are guarded against names with paths, direct
   symlinks, hard-link/input collisions, and pre-existing directories. Execution
   must test stale output cleanup and failure paths, including exception handling.
4. **Semantic label limits:** all 62 sets of labels and references were read individually
   by this fresh AI review agent. Missing/conflicting values use null consistently; explicit slash
   conventions and zero values are preserved. EVAL-11 names LN-11 as a billing
   notice rather than explicitly an invoice number, a mild wording ambiguity
   worth documenting rather than treating as evidence of model robustness. The
   duplicate-looking pair is two development records distinguished only by IDs
   011842/011843; it is visibly supplemental and does not change evaluation data.
5. **Independence limits:** separate layout-family tags do not establish a human
   annotated or statistical holdout. The source labels explicitly name the
   planned noncritical fixture error, so all outcome claims must stay limited to
   synthetic evaluation mechanics.

Planned independent executions: fresh README quickstart with exact exits;
network/DNS blocking with credentials absent; hand-counted asymmetric errors and
nulls; malformed/incomplete/replaced/shuffled input cases; a new date mutation;
format equivalence; report tampering; frozen checksums and repeat stability;
installed wheel use outside the source checkout and unrelated Git provenance;
lint, build, and full suite. Pending execution is not a pass.

## Confirmed finding, counterargument, and closure

**R1 — P2 — Source-checkout reports omitted available Git provenance.** Original
location: `src/reliability_lab/evaluation.py:51` at `e00e2b1`.

- Reproduction: in the fresh tracked checkout, run the actual README command
  `uv run reliability-lab demo --scenario baseline`. It returned 0 and its JSON
  and Markdown showed both `code_revision` and `working_tree_dirty` as null.
  The other two demos and comparison also returned null provenance. Git was
  available; `git rev-parse HEAD` returned
  `e00e2b1f7603d82301a90251d50368662c51c7f9`.
- Cause: Git ran from the module directory while its `ls-files` check used a
  repository-root-relative path. The exact direct command
  `git -C src/reliability_lab ls-files --error-unmatch -- src/reliability_lab/evaluation.py`
  returned 1. Exception handling then discarded both provenance values.
- Strongest counterargument: null provenance is legal for an installed wheel or
  unavailable Git, and no quality score was wrong. It was still a reproducibility
  defect for an accessible tracked source checkout: the available source revision
  and dirty state could never be recorded.
- Disposition: the parent routed the fix to the evaluator owner and integrated
  `9b1ec55`. The reviewer did not change runtime source. The tracked-file pathspec
  is now explicitly root-anchored and literal.
- Actual independent retest: `test_review_checkout_provenance_is_actual_tracked_revision`
  passed at `9b1ec55`, comparing the returned revision with actual `git rev-parse
  HEAD`, and dirty state with actual `git status --porcelain`. The review worktree
  was dirty because its own review files were untracked; this was correctly true.
  The fresh installed-wheel probe also passed: an untracked installed package
  nested inside this real Git checkout returned `(None, None)` while its actual
  console command ran outside the checkout. The positive checkout fix therefore
  did not remove the unrelated-repository protection.

## Actual execution ledger

Python 3.12.14; uv 0.12.8. The worktree had no `.venv` before installation. All
commands below were executed locally; no provider calls, private source reads,
remote writes, pushes, or deployments occurred. Dependency installation and
build preceded the separately instrumented offline execution.

README commands were executed exactly, one command per invocation:

| Command at original `e00e2b1` | Actual exit | Result |
| --- | ---: | --- |
| `uv sync --frozen` | 0 | Fresh `.venv` created; pinned local package plus dev dependencies installed |
| `uv run reliability-lab demo --scenario baseline` | 0 | Accepted; TP182 FP1 FN1 TN17; 39/40 exact; zero critical mismatches |
| `uv run reliability-lab demo --scenario regression` | 1 | Rejected; TP174 FP9 FN9 TN17; 31/40 exact; eight critical mismatches |
| `uv run reliability-lab demo --scenario repaired` | 0 | Accepted; baseline counts and its supplier imperfection preserved |
| `uv run reliability-lab compare reports/baseline.json reports/regression.json` | 1 | Rejection and all six failed rules preserved |
| `uv run pytest` | 0 | 180 passed in 5.17 seconds |
| `uv run --offline python scripts/verify_offline.py` | 0 | Child demo exits 0/1/0 and comparison 1 |
| `uv run ruff check .` | 0 | All selected checks passed |
| `uv build` | 0 | Source distribution and wheel built |

Additional independent commands after `9b1ec55`:

| Command | Actual exit | Result |
| --- | ---: | --- |
| `uv run --offline pytest tests/test_review.py -q` | 0 | 60 independent probes passed in 6.66 seconds |
| `uv run --offline pytest` | 0 | Final combined suite: 241 passed in 15.89 seconds |
| `uv build` | 0 | Rebuilt distributions containing the provenance fix |
| `uv run --offline python tests/review_support/verify_wheel.py dist/llm_reliability_lab-0.1.0-py3-none-any.whl` | 0 | New wheel-only environment; real console entry point and resources worked outside repository |
| `uv run --offline ruff check .` | 0 | Reviewer tests/helper and runtime passed |
| `git diff --check` | 0 | No whitespace errors |

The wheel helper actually executed `uv venv --python <reviewer Python> <new env>`
and `uv pip install --python <new env Python> --no-index --no-deps <local wheel>`;
both returned 0. Package and resource imports resolved to that environment's
`site-packages`, not the source directory. Actual console exits were help 0,
baseline 0, regression 1, repaired 0, compare 1, and explicit evaluate 0.
Every console process used a minimal environment without API credentials and a
startup guard patching socket connect, connect_ex, send/sendall/sendto, connection
creation, getaddrinfo, hostname/address lookups and getfqdn. An exit marker proved
the guard loaded and recorded zero network attempts, including swallowed attempts.
This is Python runtime instrumentation, not an operating-system firewall.

The independent editable-install offline test separately ran baseline, regression,
repaired, compare and evaluate from an external temporary directory, each in a
fresh Python process with only PATH/LANG inherited. It first proved that both a
DNS lookup and a socket connection were intercepted, reset its counter, and then
asserted zero attempted calls while running the CLI. Expected exits were 0/1/0/1/0.

## Independent acceptance probes and counterarguments

- **Hand arithmetic:** three authored cases yielded TP3 FP3 FN4 TN6; precision
  3/6, recall 3/7, F1 6/13; one of three records exact. Per-field counts were
  checked independently. Expected-null8, predicted-null9, correct-abstention6,
  missed-value3 and unsupported-value2 were exact. Six critical field mismatches
  occurred across two bad records, proving the critical count is not a record
  count. An all-null case had exact accuracy1 but undefined P/R/F1 and rejected
  even when all required score minima were zero.
- **New critical mutation:** EVAL-15 explicitly declares MM/DD/YYYY for
  08/12/2026. The reviewer changed only the supplied due date from 2026-08-12 to
  2026-12-08, retaining scenario `baseline`. The ordinary evaluator rejected with
  one critical due-date mismatch. Micro F1 was 181/183 and exact accuracy .95:
  aggregate minimum thresholds passed, but the critical gate and relative F1
  gate caught the defect. This differs from the implemented leading-zero ID bug
  and the implementer's separate amount mutation.
- **Harmless formatting:** supplier Unicode casefold/whitespace, currency case,
  and permitted outer whitespace on all non-null field strings preserved metrics
  and acceptance. Meaning-bearing ID case, punctuation, leading zeros and money
  remained governed by the frozen normalizer.
- **Fail-closed inputs:** independent parameterized probes rejected omitted,
  duplicate and unknown/replaced prediction IDs; wrong dataset IDs; omitted and
  blank fields; float money; malformed calendar dates and decimal strings;
  inconsistent/missing/out-of-range evidence; duplicate/empty datasets; unknown,
  missing, NaN, boolean or empty policy settings. Strict JSON rejected duplicate
  keys, NaN, Infinity, exponent overflow, syntax errors, wrong root type and invalid
  UTF-8. These raised InputError rather than producing partial quality scores.
- **Missing reference files:** actual CLI calls for missing dataset, predictions,
  policy and baseline each returned 2 without a traceback and removed prior
  accepted JSON/Markdown in that invocation's reserved output slots.
- **Replacement and tampering:** self-consistent reports over changed documents,
  labels, policy or mode could be evaluated individually but could not compare to
  the original baseline. Twelve additional forged report variants changed flags,
  counts/types, scores, checks, diffs, excerpt text, predictions, hashes, structure,
  provider claims and extra keys; all comparisons raised InputError.
- **Rejection preservation:** using the unchanged frozen policy, a perfect
  baseline versus the ordinary baseline's one supplier error produces an
  exclusively comparative rejection: 1/183 F1 drop exceeds .005, although both
  reports individually pass and exact-record drop equals the allowed .025.
  Replaying against that same baseline preserved the rejection. Replacing it
  with the easier ordinary baseline raised InputError.
- **Freeze and determinism:** reviewer-pinned raw hashes for both primary data
  files, the supplement, all three predictions and policy matched. Every scenario
  was evaluated with the same source and policy; arbitrary scenario labels,
  repeated runs, reversed cases and rotated prediction order preserved stable
  metrics/decisions. Source file bytes did not change during these runs. The
  evaluation file read directly from freeze commit `c2c4c4f` had the same raw
  SHA-256 `27b447e9318d25a4af94e2801ce35199e34771f0837603306172cbd8b89117e0`.
  `git diff 83fae78 -- policy.json` was empty. Contract changes since that initial
  freeze only hardened numeric-overflow validation; normalization was unchanged.
- **Output safety:** actual same-path, hardlink and symlink collisions returned 2
  and preserved source bytes. Control sequences, bidirectional text, HTML script
  markup and Markdown-link input were inert in rendered human reports. Expected
  failures do not produce accepted output. The implementation does not claim a
  hostile-concurrent-filesystem or signed-report security boundary.
- **Claims:** README numerical results matched computed counts. Corpus provenance,
  label-derived construction, lack of live inference, non-entailing evidence
  references, illustrative thresholds, agent authorship and absent remote CI
  evidence are disclosed. Self-consistent replacement of all report artifacts can
  create a different valid experiment; documentation explicitly says reports are
  not signed evidence. This bounded limitation is not a bypass of the implemented
  consistency checks.

## Individual source-label review

Each row records inspection by this fresh AI review agent of **all five reference
values and every evidence pointer** against the raw numbered document lines.
Notes emphasize the load-bearing interpretation. This is AI review of synthetic
labels, not independent human annotation or a semantic entailment test.

| Case | Source interpretation checked |
| --- | --- |
| DEV-01 | Explicit labels; 002713 preserves both initial zeros |
| DEV-02 | Final 86.20 beats subtotal 80; preparation date is not deadline |
| DEV-03 | Table columns govern line 2; zero final total is present |
| DEV-04 | DP:4/2 punctuation preserved; deadline explicitly absent |
| DEV-05 | 04/05/2027 convention absent; due date null |
| DEV-06 | DD/MM/YYYY makes 19/11/2026 November 19 |
| DEV-07 | Equal USD/CAD boxes conflict; currency null, amount 310.00 usable |
| DEV-08 | JT-441 explicitly job-ticket only; invoice ID null |
| DEV-09 | Supplier panel empty; final 162.00 includes handling |
| DEV-10 | Subtotal 49 excludes unprovided freight; total null |
| DEV-11 | Total 88.80 known; currency explicitly unspecified |
| DEV-12 | Unrelated margin instruction cannot replace payable 190.10 |
| DEV-13 | Supplier spans lines 2/3; whitespace normalization only |
| DEV-14 | ne-A 7 preserves case; Unicode supplier preserved |
| DEV-15 | GBP settlement 31.25 takes precedence over USD estimate |
| DEV-16 | Explicit valid leap deadline 2028-02-29; log date ignored |
| DEV-17 | Equal-revision deadline conflict; due date null |
| DEV-18 | Invoice ID 0 and amount 0.00 are present values |
| DEV-19 | Replacement SC-12B supersedes void SC-12 |
| DEV-20 | Two unsuperseded invoice IDs conflict; ID null |
| EVAL-01 | Transfer's invoice-number field identifies 000482 |
| EVAL-02 | Bracketed values explicit; Copper Vale Binding is source label |
| EVAL-03 | Explicit GBP 0.00 and deadline remain present |
| EVAL-04 | CAD 105.50 is final; 001090 retains zeros |
| EVAL-05 | Header absent; tracking FHF-222 is explicitly not invoice ID |
| EVAL-06 | Equal EUR/GBP total seals conflict; currency null |
| EVAL-07 | 06/07/2027 ambiguous; due date null |
| EVAL-08 | Promotional instruction footer does not amend EUR 460.25/deadline |
| EVAL-09 | Downward labels associate standalone ID 000063 and supplier |
| EVAL-10 | Torn currency panel leaves currency null; digits 75.00 known |
| EVAL-11 | Issuer blank, recipient excluded; LN-11 wording caveat below |
| EVAL-12 | Named slots map identity 007501, moneyUSD 38.44 and deadline |
| EVAL-13 | Provisional goods charge not final; total null |
| EVAL-14 | Issue date cannot replace omitted deadline; due date null |
| EVAL-15 | MM/DD/YYYY makes 08/12/2026 August 12, not December 8 |
| EVAL-16 | Pépinière Pixel & Co. accents/punctuation retained |
| EVAL-17 | Map document node identifies 003008 |
| EVAL-18 | Equally valid December 18/28 deadlines conflict; due date null |
| EVAL-19 | Actual USD 369.55 demand overrides CAD example |
| EVAL-20 | Repeated ta.Xq-20 establishes exact case/punctuation |
| EVAL-21 | 00A-21 invoice differs from site/parcel codes |
| EVAL-22 | Explicit next leap day 2028-02-29 is valid |
| EVAL-23 | Register labels identify 000905 and CAD 59.05 |
| EVAL-24 | Current replacement YPJ-24-R supersedes cancellation |
| EVAL-25 | Explicit current final invoice payable 350.00 after credited deposit |
| EVAL-26 | Equal current AS-26A/AS-26B stickers conflict; ID null |
| EVAL-27 | Authorized GBP 57.17 correction replaces void USD 70.00 |
| EVAL-28 | Postfixed feed tags; numeric 429 has no zeros to lose |
| EVAL-29 | Relative terms lack acceptance date; due date null |
| EVAL-30 | All five fields explicitly omitted; envelope key not invoice ID |
| EVAL-31 | All four zeros in 0000 preserved; USD 0.00 is a value |
| EVAL-32 | Embedded machine-message sample is unrelated to billing facts |
| EVAL-33 | Legal supplier block distinct from customer; Straße casefold allowed |
| EVAL-34 | Equal final amount 34.00/43.00 conflict; total null |
| EVAL-35 | DD/MM/YYYY caption makes 07/01/2027 January 7 |
| EVAL-36 | Hyphenated 000-51 retained, not coerced as numeric |
| EVAL-37 | Endorsement explicitly identifies 000712 and GBP 712.07 |
| EVAL-38 | Dollar sign alone cannot identify USD/CAD; currency null |
| EVAL-39 | Current MPD-39 beats another supplier's old CUSTOMER-9 |
| EVAL-40 | Legal-name punctuation and nv-Q 40 case are significant |
| DUPDEV-01 | Invoice 011842, otherwise matching companion slip |
| DUPDEV-02 | Invoice 011843, distinct obligation despite visual similarity |

**EVAL-11 caveat:** line1 says "Billing notice LN-11," while the reference treats
LN-11 as invoice_id. A reader could interpret that as a separate notice number.
The strongest supporting interpretation is that the single billing notice is the
invoice artifact; the following issuer field is explicitly an invoice issuer,
and no competing identity appears. The bounded corpus does not resolve that
linguistic ambiguity independently. It is recorded as a label-wording limitation,
not a proven contradictory label. No reference label or evaluation text was
changed, and the case does not establish robustness to notice/invoice ambiguity.

The supplement was additionally graded from reviewer-transcribed predictions:
both IDs passed as two exact records; substituting 011842 for the second ID
rejected with one critical failure; omitting the second prediction raised an
InputError. Visual similarity never removed a case from the denominator.

## Closure and changed paths

Review complete at runtime revision `9b1ec55` on 2026-09-12 UTC. The only
confirmed implementation defect, R1, is fixed and independently retested. All
mandatory local acceptance categories were actually executed. No unresolved
implementation blocker remains; EVAL-11 wording and the synthetic/AI-label and
runtime-instrumentation limits above remain disclosed.

Reviewer-owned changes only: `docs/review.md`, `tests/test_review.py`, and
`tests/review_support/verify_wheel.py`. The parent alone integrates these files
and performs the final combined-branch validation. No source, dataset, policy,
README, lockfile, or gate was modified by this reviewer.
