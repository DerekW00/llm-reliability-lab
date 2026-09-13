# Build status

## GitHub publication — complete, 2026-09-12 Pacific

The user authorized public publication after the local review completed. The
repository is public at [DerekW00/llm-reliability-lab](https://github.com/DerekW00/llm-reliability-lab),
with `main` as the default branch and local `main` tracking `origin/main`.
Publication used the existing personal SSH credential verified as `DerekW00`;
no account permissions were changed. Original signed history is preserved.

The tracked source, frozen fixtures, MIT license, examples and review summaries
are published. Raw review sessions, temporary reports, environments and build
outputs remain excluded from Git. The runtime remains fully local; no hosted
application or package release was created.

[GitHub Actions](https://github.com/DerekW00/llm-reliability-lab/actions/workflows/ci.yml)
runs the offline verification workflow on pushes and pull requests. The local
341-test and 27-check evidence remains recorded below. Refer to the linked run
history for remote results and the exact source revision each run checked.

## Current review — complete, 2026-09-12 Pacific

The authorized Claude Code review/fix loop is complete. Claude defaults to Opus;
its recovered F3 reviewer and final Opus repair pass returned no actionable runtime
findings. Local `main` contains the reviewed repairs, fast-forwarded through
`bd84199`, followed by this documentation-only completion record.

Latest reviewed source is `5cb4d1c`; runtime changes are at `57655fc`, with examples
generated from that clean runtime source. Independent main-checkout verification
at 05:48 Pacific passed **341 tests and all 27 checks**, including offline execution,
wheel installation, failure handling, frozen hashes, snapshot identity and replay.
All confirmed findings are resolved. No push, deployment or public release occurred.

`docs/claude-review.md` records coverage, repairs and limitations. Raw review logs
and parent results are retained locally under `reports/claude-review/` and
`reports/claude-review-parent/`. Earlier pending checkpoints remain in Git history.

Next: inspect the synthetic-results claims, illustrative policy and review limits
before deciding whether to publish. No additional implementation blocker is known.
The older checkpoints below describe historical build states.

## Original delivery checkpoint — complete, 2026-09-11 Pacific

Mandatory offline acceptance is complete. Main contains the integrated build,
fresh AI adversarial review and reproduced P2 provenance fix. Final runtime
source is `9b1ec55`; saved reports identify that exact clean source revision.
`FINAL_REPORT.md` records delivery history, exact commands, remaining limits and
the morning review checklist. The original delivery commit is `126a9a7c6de0c56cc852800e8a4b8a4ed5653320`.

- Final combined-branch verification: **241 tests passed**, Ruff passed, source
  and wheel built, independent wheel/console/offline checks passed.
- Baseline/repaired pass; regression and its comparison return 1 as intended.
- No unresolved confirmed implementation defects; EVAL-11 wording ambiguity is
  documented as a label limitation. Primary frozen inputs and policy unchanged.
- All four agents completed; no project application processes remain. Integrated
  worktree cleanup is part of delivery; branch history is retained locally.
- No live provider calls, remote CI runs, public writes, deployment or account changes.
- Next command: `uv run reliability-lab demo --scenario regression` from this
  directory (expected exit 1). Review README, policy and review findings before release.

The dated entries below preserve original build checkpoints. Current review status
is recorded at the top of this file.

## 2026-09-11 — Contract and scaffold

- New local repository at `/Users/dw/llm-reliability-lab`, branch main.
- Contract, illustrative policy and ownership frozen before any fixture scores.
- Existing Git identity verified against authenticated GitHub user DerekW00
  (account ID 40290496); project configuration applied, globals unchanged.
- No private source data read; no provider calls or remote writes.
- Shared validation tests: 53 passed; lint passed. JSON numeric overflow fails closed.
- Three agents active in isolated sibling worktrees: build/dataset,
  build/evaluation, build/experience. Only orchestrator integrates branches.
- Next: integrate the first evaluator/data/CLI slice, then fresh independent review.
- Active: orchestrator plus the three named agents; no application servers.
- Resume: `cd /Users/dw/llm-reliability-lab && cat STATUS.md SPEC.md`

## 2026-09-11 — First integrated slice

- Evaluator/gate and CLI/reporting branches integrated, preserving worker commits.
- Independent one-record CLI smoke: matching external predictions exit 0 with
  F1 1.0; a schema-valid lost-zero identifier exits 1 with F1 .8 and one critical
  failure. Temporary smoke inputs removed; no demonstration labels were tuned.
- Integrated focused run: 152 passed; one demo integration test fails solely
  because the dataset branch is not integrated yet. This is an incomplete checkpoint.
- Runtime standard library only; dev/build versions and interpreter pinned.
- Active: dataset agent authoring/freeze; evaluation agent boundary hardening;
  experience agent finished. No project server or model process.
- Next: integrate frozen data/fixtures and evaluator boundary fix, run all exact
  quickstart commands, then launch a fresh reviewer in an isolated worktree.

## 2026-09-11 — Full offline integration

- Frozen primary data, all fixtures and development supplement integrated.
- Baseline and repaired: exit 0, micro F1 .994535519125683, exact records 39/40,
  zero critical failures. Regression: exit 1, micro F1 .9508196721311475, exact
  records 31/40, eight critical identifier failures. Comparison preserves exit 1.
- Complete suite: 180 passed; Ruff passed. Network-instrumented CLI runs outside
  repository CWD passed without API credentials. Source and wheel build succeeded.
- Primary data and original policy hashes unchanged. Development supplement
  corrects the initial spec's coverage omission without evaluation tuning.
- All three implementers finished; no project servers or model processes.
- Next: fresh independent adversarial review and clean-environment quickstart,
  then any confirmed fixes, final reports and commit/identity audit.

## 2026-09-11 — Independent finding fixed; final artifacts

- Fresh review recorded its independent first pass before implementer conclusions.
- Reviewer found a real checkout-provenance bug: a Git pathspec was relative to
  the wrong directory, returning null revision. Parent reproduced; evaluation
  owner fixed it in 9b1ec55. Parent now verifies exact HEAD and clean/dirty state.
  Reviewer closure and remaining acceptance probes are still in progress.
- Exact README quickstart rerun: sync0, baseline0, regression1, repaired0,
  rejected comparison1, pytest0 (181 passed). General evaluate0, Ruff0, build0,
  network-instrumented CLI script0. Results and frozen checksums unchanged.
- Three example report pairs generated from clean 9b1ec55 source and preserved
  with their actual provenance. Root output reports remain ignored; examples tracked.
- Active: fresh reviewer only; implementation/fix workers finished. No servers.
- Next: integrate review evidence and any further confirmed fixes, then complete
  FINAL_REPORT.md and inspect the final commit graph and all identities.
