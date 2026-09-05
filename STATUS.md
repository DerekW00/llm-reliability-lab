# Build status

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
