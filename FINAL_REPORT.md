# LLM Reliability Lab — project handoff

## Public repository — 2026-09-12 Pacific

Published at **[DerekW00/llm-reliability-lab](https://github.com/DerekW00/llm-reliability-lab)**
following the user's explicit publication request. The default branch is `main`.
The repository includes the source, frozen synthetic inputs, generated examples,
MIT license and committed review records, with the original signed history intact.
Raw local review logs and temporary outputs are excluded from Git.

[GitHub Actions results](https://github.com/DerekW00/llm-reliability-lab/actions/workflows/ci.yml)
show the remote offline checks for each pushed revision. This publishes the source
repository; the application still runs locally with no live model calls. No hosted
application, package release or separate deployment was created.

The dated sections below preserve the pre-publication build and review evidence.
Their original restrictions describe the authorization in force at those times;
the later publication request authorized this GitHub repository and its pushes.

## Review follow-up — complete, 2026-09-12 Pacific

**Claude Opus review, repairs and local integration are complete.** The recovered
F3 reviewer reported no reproducible findings in its earlier snapshot. Opus then
independently reviewed `1c20cf9..5cb4d1c` and found no actionable runtime defects.
Both bounded Codex repair reviews also completed without actionable findings.
Claude Code now defaults to Opus.

Local main was fast-forwarded through `bd84199`. On that clean checkout, independent
verification passed **341 tests in 18.36 seconds and all 27 checks**, including
lint, offline verification, build, installed-wheel behavior, exact CLI statuses,
broken output streams, saved-report replay, frozen hashes and reviewed-source
identity. This completion commit changes documentation only. Runtime source remains
`57655fc`; verification-script follow-up is `5cb4d1c`. Saved examples retain their
real clean-source provenance from `57655fc`.

[The review record](docs/claude-review.md) separates repaired defects, test gaps,
refuted claims and coverage limits. The recovered review's unfinished mutation lead
was investigated without reproducing a current defect; the missing audit is not
claimed complete. All frozen inputs and policy remain unchanged. No push,
deployment, public release or application model API call occurred.

Run: `uv run reliability-lab demo --scenario regression` from
`/Users/dw/llm-reliability-lab` (expected exit 1).

**Review now:** inspect `README.md`'s synthetic-results limits, `policy.json`'s
illustrative thresholds, and `docs/claude-review.md`'s remaining review limits before
approving any public release.

## Original build handoff — 2026-09-11

The following section preserves the original delivery's results. Its 241-test
count and source revision are historical, not the current repair candidate.

**Complete.** Mandatory offline acceptance passes, including fresh independent AI
review, reproduction and repair of the one confirmed defect, and final combined
branch verification. Baseline and repaired pass; the simulated regression and
its saved comparison reject as intended. No required work remains for this local build.

Repository: `/Users/dw/llm-reliability-lab` · original delivery commit:
`126a9a7c6de0c56cc852800e8a4b8a4ed5653320`.
Final runtime source: `9b1ec55b221e98c7a0ce46fa34b1623002e55a44`.
The later report, review and delivery commits do not change runtime behavior.

## Results and exact commands

**Synthetic fixture evaluation only.** Fixed authored predictions over fictional
plain-text invoices demonstrate grading and a simulated postprocessing bug.
This is not a measured LLM, prompt experiment, real-world benchmark or production
outcome. No model/provider adapter or paid application API was added or called.

| Fixture | TP / FP / FN / TN | Micro precision / recall / F1 | Exact records | Critical errors | Exit |
| --- | --- | ---: | ---: | ---: | ---: |
| Baseline | 182 / 1 / 1 / 17 | 99.4536% | 39/40 | 0 | 0 |
| Regression | 174 / 9 / 9 / 17 | 95.0820% | 31/40 | 8 | 1 |
| Repaired | 182 / 1 / 1 / 17 | 99.4536% | 39/40 | 0 | 0 |

The regression drops significant zeros from numeric invoice IDs. The repair
removes that mechanism and preserves the baseline's supplier-name imperfection.
All scenarios use identical evaluation labels, normalization, evaluator and policy.

These exact commands were executed from the repository. The quickstart was also
run independently in a fresh worktree with a newly created project environment.

| Command | Actual exit | Observed result |
| --- | ---: | --- |
| `uv sync --frozen` | 0 | Pinned environment installed |
| `uv run reliability-lab demo --scenario baseline` | 0 | Accepted |
| `uv run reliability-lab demo --scenario regression` | 1 | Rejected; eight critical ID errors and six failed gate rules |
| `uv run reliability-lab demo --scenario repaired` | 0 | Accepted with original policy |
| `uv run reliability-lab compare reports/baseline.json reports/regression.json` | 1 | Rejection preserved by recomputation |
| `uv run pytest` | 0 | Published command passed; final combined-branch `uv run pytest -q` passed **241 tests** in 15.45 seconds |
| `uv run ruff check .` | 0 | Configured lint passed |
| `uv run --offline python scripts/verify_offline.py` | 0 | Offline CLI children returned 0/1/0 and rejected comparison 1 |
| `uv build` | 0 | Source distribution and wheel built |
| `uv run --offline python tests/review_support/verify_wheel.py dist/llm_reliability_lab-0.1.0-py3-none-any.whl` | 0 | Fresh wheel installation, imports, packaged data, real console, offline guard and unrelated-Git protection passed |
| `git diff --check` | 0 | No whitespace errors |

The README's ordinary `evaluate` command also returned 0, and replaying the saved
example regression against its saved baseline returned 1. Exit 1 is a completed
quality rejection; exit 2 is invalid input/execution failure. Invalid inputs never
produce a partial passing score. The independent review tested missing files and
malformed coverage/schema/policy inputs with that error distinction.

Three JSON/Markdown pairs in [examples/reports](examples/reports/) were generated
from clean `9b1ec55` source and copied without content edits. They contain actual
UTC timestamps, local evaluation duration, Python version, content fingerprints
and complete inputs for replay. Duration is not model latency. Variable provenance
fields are excluded from deterministic metric/decision comparisons.

## Review, freeze and limitations

Three real implementation agents worked concurrently in separate branches and
Git worktrees (dataset, evaluation, experience). The orchestrator owned shared
contracts/dependencies and integrated their commits. A fourth, fresh AI reviewer
recorded a code/data-only first pass before seeing implementation conclusions.
Its [review report](docs/review.md) includes all 62 source-label checks, concrete
reproductions, counterarguments, dispositions and command results.

The independent reviewer confirmed one P2 defect: a relative Git pathspec caused
tracked-checkout reports to omit available revision/dirty-state provenance.
The parent reproduced it; the evaluation owner fixed it in `9b1ec55`; parent and
reviewer verified closure in real clean/dirty checkouts and wheel installations.
The parent then integrated the review and independently reran all 241 tests,
lint, build and the stronger wheel helper. No confirmed implementation defect is
unresolved. The 60 independent probes also cover hand-counted asymmetric metrics,
all-null/undefined metrics, malicious report changes, incomplete/replaced inputs,
reordered/repeated runs, preserved relative rejection and safe output handling.
A new reviewer-selected date-convention inversion rejected; harmless formatting
passed. The evaluator never selects a score or verdict by scenario name.

Primary frozen file SHA-256 values remain unchanged:

| Artifact | Raw SHA-256 |
| --- | --- |
| `data/development.json` | `6ea77e04ff6ced3af2cebbc9ef25856acd247231048cdc94e6aa8819edbfa24a` |
| `data/evaluation.json` | `27b447e9318d25a4af94e2801ce35199e34771f0837603306172cbd8b89117e0` |
| `policy.json` | `b81326e57c06b797858a346824596d2e84d6e64c4ad7b56c90a6027652b43ff2` |

The primary corpus is 20 development and 40 evaluation cases. An integration
coverage audit found that the initial spec omitted duplicate-looking documents.
Two separately frozen development cases corrected that omission after primary
fixture construction, before any scoring; the original data, manifest and policy
were preserved. Total: 22 development, 40 evaluation. This disclosed coverage
correction did not tune evaluation outcomes.

Material limits and decisions:

- Labels and predictions are synthetic and agent-authored/reviewed. Some fixtures
  are constructed from reference labels; inference is not performed by evaluation.
  Separate layouts and a similarity check do not establish statistical holdout
  independence. EVAL-11's billing-notice/invoice-number wording remains a disclosed
  label ambiguity, not a proven contradiction or an altered frozen label.
- Four currencies, nonnegative two-place amounts, ISO output dates and five fields
  form a deliberately bounded contract. No OCR/PDF extraction, credit notes, line
  items, tax reconciliation, live adapter or semantic entailment judge is included.
  Evidence checks validate pointers; policy thresholds are illustrative.
- Network/DNS calls were instrumented to fail with credentials absent. Independent
  guards proved they loaded, exercised their interceptions, and found zero runtime
  application attempts. This is Python instrumentation, not an OS firewall.
  Dependency installation/build may use official registries and Python hosts.
- Verified locally on macOS Apple Silicon, Python 3.12.14, uv 0.12.8. A pinned GitHub
  Actions workflow runs tests, expected rejection, build and wheel checks, but no
  remote CI execution or Linux acceptance is claimed. No live provider calls,
  pushes, publication, deployment, messages, purchases or account changes occurred.
- Original-only contents were inspected before adding the MIT license. There is
  no claim of unaided authorship. Runtime dependencies are zero; dev/build versions
  are pinned. No private career/employer source was used or changed.

## Delivery state and morning review

All implementation and review agents completed. Their clean, integrated worktrees
were removed; local branches and meaningful commit history remain. No application
servers or project-owned background processes remain. No remote is configured.
The local source and deliverables are committed. Ignored `.venv/`, `dist/`,
`reports/`, `.pytest_cache/`, `.ruff_cache/` and Python bytecode are local runtime,
build, run and test artifacts, not uncommitted source changes. There are no signing
limitations or unresolved approval blockers for this authorized local build.

**Review now:**

1. [README — Actual results and limits](README.md): confirm the public framing is
   a synthetic reliability demonstration, not evidence of real model performance.
2. [Evaluation policy](docs/evaluation.md#policy-and-comparison): inspect the strict
   critical-error rule and illustrative thresholds before adapting them to a client.
3. [Independent review — EVAL-11 caveat](docs/review.md#individual-source-label-review):
   inspect the remaining label-wording limitation and the provenance defect closure.

No public release is authorized by this build. When ready, explicitly request the
specific publication action after reviewing those three items.

Start the demonstration (expected rejection exit 1):

```sh
cd /Users/dw/llm-reliability-lab
uv run reliability-lab demo --scenario regression
```

## Commit and identity audit

Before the first commit, the existing configured identity was checked against the
read-only authenticated GitHub user: `DerekW00`, account ID 40290496. Project-local
Git configuration uses **Derek Derui Wang <40290496+DerekW00@users.noreply.github.com>**
for both author and committer. Global configuration was not changed. Effective
identities and identity/date environment overrides were checked before each new
commit, including worker and integration commits. No overrides were present.
Existing SSH signing worked unattended and was preserved; signature verification
returned `G` for every audited commit. There were no identity repairs, backdating,
history rewrites, invented activity dates, optional AI trailers, false sign-offs,
or remote writes. Every commit has the same verified author and committer identity.

The table below is the actual reachable history before the delivery documentation
commit, in topological order. Each listed timestamp is both author and committer
date; they were checked separately and were equal. Parent relationships and all
subjects were inspected. `HEAD` in the final row denotes the delivery commit
containing this report, avoiding an impossible self-referential content hash.
Its metadata is available with `git show -s --format=fuller HEAD`; the final
post-commit audit checks this row as well.

| Commit | Parents | Author and committer date | Subject |
| --- | --- | --- | --- |
| `83fae78` | `root` | 2026-09-11T22:07:03-07:00 | Define strict extraction contracts and freeze the illustrative release policy |
| `43393be` | `83fae78` | 2026-09-11T22:11:02-07:00 | Test strict input boundaries and reject non-finite JSON values |
| `89cbdb2` | `43393be` | 2026-09-11T22:12:53-07:00 | Add offline CLI acceptance checks and a pinned CI workflow |
| `3b5651f` | `89cbdb2` | 2026-09-11T22:14:39-07:00 | Pin the interpreter and build tools for reproducible local runs |
| `1931ff4` | `83fae78` | 2026-09-11T22:17:24-07:00 | Implement deterministic evaluation and replay-verified policy gate |
| `9e38d11` | `3b5651f 1931ff4` | 2026-09-11T22:18:19-07:00 | Integrate the evaluator and replay-verified release gate |
| `666e433` | `83fae78` | 2026-09-11T22:17:18-07:00 | Add guarded offline CLI and computed reliability reports |
| `2b359cf` | `9e38d11 666e433` | 2026-09-11T22:18:19-07:00 | Integrate the terminal CLI and readable evaluation reports |
| `0b743ed` | `2b359cf` | 2026-09-11T22:19:20-07:00 | Record the first integrated CLI verification checkpoint |
| `c2c4c4f` | `83fae78` | 2026-09-11T22:19:26-07:00 | Freeze original synthetic invoice documents and reviewed reference labels |
| `7993f4f` | `0b743ed c2c4c4f` | 2026-09-11T22:19:58-07:00 | Integrate frozen synthetic documents and reviewed reference labels |
| `0c2970c` | `1931ff4` | 2026-09-11T22:19:18-07:00 | Bound report construction and test exact comparison boundaries |
| `6a27dde` | `7993f4f 0c2970c` | 2026-09-11T22:19:58-07:00 | Integrate exact gate arithmetic and bounded report replay |
| `92a8be3` | `6a27dde` | 2026-09-11T22:21:23-07:00 | Clarify supplemental development coverage without changing the evaluation freeze |
| `2e6bda6` | `92a8be3` | 2026-09-11T22:22:09-07:00 | License original project contents and document construction provenance |
| `d55789b` | `c2c4c4f` | 2026-09-11T22:23:34-07:00 | Add static regression fixtures and supplemental duplicate-looking invoices |
| `84ed2f2` | `2e6bda6 d55789b` | 2026-09-11T22:23:59-07:00 | Integrate fixture scenarios and supplemental duplicate-document cases |
| `e00e2b1` | `84ed2f2` | 2026-09-11T22:27:06-07:00 | Document computed demo results and complete integrated acceptance coverage |
| `9b1ec55` | `e00e2b1` | 2026-09-11T22:31:53-07:00 | Fix tracked source provenance path resolution |
| `92593f6` | `9b1ec55` | 2026-09-11T22:34:11-07:00 | Preserve generated reports with verified source provenance |
| `b03e7e9` | `9b1ec55` | 2026-09-11T22:41:07-07:00 | Add independent adversarial acceptance review |
| `c74f248` | `92593f6 b03e7e9` | 2026-09-11T22:42:01-07:00 | Integrate independent adversarial review and verified defect closure |
| `HEAD` (delivery) | `c74f248` | Actual creation metadata in `git show HEAD` | Complete verified local delivery and morning review handoff |

To inspect every identity, timestamp, signature status and parent again:

```sh
git log --graph --format='%h %p %s%n  author: %an <%ae> %aI%n  committer: %cn <%ce> %cI%n  signature: %G?'
git status --short
```

## Changed-path inventory

All retained deliverables live in this new repository. The ephemeral sibling
worktrees were removed after integration. No career workspace record was edited.
The full retained source/document inventory follows (paths relative to this repository):

```text
.github/workflows/ci.yml
.gitignore
.python-version
AGENTS.md
FINAL_REPORT.md
LICENSE
README.md
SPEC.md
STATUS.md
data/development.json
data/duplicate-looking-development.json
data/duplicate-looking-manifest.json
data/evaluation.json
data/manifest.json
data/predictions/baseline.json
data/predictions/manifest.json
data/predictions/regression.json
data/predictions/repaired.json
docs/dataset.md
docs/evaluation.md
docs/freeze.md
docs/quickstart.md
docs/reproducibility.md
docs/review.md
docs/walkthrough.md
examples/reports/README.md
examples/reports/baseline.json
examples/reports/baseline.md
examples/reports/regression.json
examples/reports/regression.md
examples/reports/repaired.json
examples/reports/repaired.md
policy.json
pyproject.toml
scripts/verify_offline.py
src/reliability_lab/__init__.py
src/reliability_lab/cli.py
src/reliability_lab/contracts.py
src/reliability_lab/evaluation.py
src/reliability_lab/gate.py
src/reliability_lab/reporting.py
src/reliability_lab/resources.py
tests/conftest.py
tests/review_support/verify_wheel.py
tests/test_acceptance.py
tests/test_cli.py
tests/test_contracts.py
tests/test_dataset.py
tests/test_evaluation.py
tests/test_gate.py
tests/test_review.py
uv.lock
```
