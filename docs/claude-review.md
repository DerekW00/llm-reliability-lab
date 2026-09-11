# Claude Code review and repair record

Updated 2026-09-12 Pacific. **Awaiting the final Opus follow-up.** The latest
candidate passes 341 tests. All received, confirmed repair findings have been
addressed; the interrupted fresh Claude reviewer has not yet submitted its final
report. This is not a claim that the review loop is complete or that the code is
free of every possible defect.

## Current candidate and continuation

- Main still contains the original delivery at `126a9a7`.
- Repair branch: `review/claude-opus`. Runtime source was last changed in
  `57655fc`; verification-script follow-up is `5cb4d1c`.
- Examples were generated together from clean `57655fc`, committed in `f41daa3`.
  They retain actual timestamps, durations and source revisions. Prior examples
  at `9b1ec55` and `5ce81ab` remain in Git history.
- Claude reached its session quota at 04:09 Pacific; the provider advertised a
  05:30 reset. This task has an app continuation at **05:35 Pacific** to resume
  the existing Opus session and finish the remaining review/integration work.
- No push, pull request, deployment or public release has occurred.

The resumed task should read the local
[continuation record](../reports/claude-review/round6/RESUME.md), inspect live Git
state, finish the actual latest-source review, then fast-forward main and run the
independent final verification. It must not call an interrupted review clean.

## Models, scope and review coverage

Claude Code was launched with `--model opus --effort max`. Session initialization
confirmed **`claude-opus-5`** for session
`a405b7a8-4fc4-4fee-b8fa-cb3bdf8d7193`. The user's global Claude default is now
`opus`; only that setting was changed and the previous settings file was backed up.
The requested `pr-review-orchestrator` and `superpowers:receiving-code-review`
protocols were invoked/read and applied. The user's explicit automatic repair loop
superseded their ordinary per-finding interactive approval pause; no human sign-off
or teaching session is claimed.

The initial review covered the whole new project at `126a9a7`: all 52 tracked
files, using Git's empty tree as the conceptual base. Review tools requiring a
commit base used root commit `83fae78` plus explicit review of its foundational
contracts and configuration. Generated examples were checked for replay/provenance;
`uv.lock` was checked for consistency rather than reviewed line by line. Frozen
synthetic data and policy were reviewed without changing their bytes.

| Contract | Actual coverage |
| --- | --- |
| R1, review toolkit | Five specialist passes: code, silent failures, tests, comments and types. Sonnet used where the skill prescribed it. |
| R2, holistic review | Completed on Opus. |
| R3, built-in code review | Invoked at maximum effort, with its own review output/fan-out. |
| R4, plugin protocol | Compliance, shallow bugs, Git history and in-code guidance completed; protocol-specific Sonnet/Haiku roles used. Past-PR comments unavailable because there is no remote or PR history. |
| R5, repository-specific dual harness | Skipped: applies to the DBB/app repository, not this project. No employer source was read. |
| R6, native Codex review | Completed through the guarded wrapper; filesystem-dependent test coverage was limited by its read-only sandbox. |
| R7, adversarial Codex plus three Ralph rounds | Completed through the guarded wrapper. Separate model family on the already-authorized ChatGPT account. |
| Three Opus verification passes | At `1c20cf9`, all three independently confirmed closure of the original publication, stale-output and input-deletion mechanisms. They also found further repair/test gaps, addressed in the later candidate. |
| Fresh Opus F3 | Interrupted before final write-up. Existing transcript is preserved for continuation. |
| Final Codex repair review | `1c20cf9..f41daa3`: native, adversarial and all three Ralph rounds reported no actionable issues. The reviewer ran 14 focused tests; adversarial review also ran 14 in-memory checks. Full filesystem/wheel checks were performed separately by the parent. |
| Latest verification-script review | `f41daa3..5cb4d1c`: native/adversarial review and all three Ralph rounds completed without actionable findings. Adversarial in-memory checks accepted the healthy control and rejected 11 faults; five filesystem tests were blocked by sandbox permissions and their in-memory adaptations passed. Parent ran the complete suite separately. |

No formal advocate/skeptic/judge debate session is claimed. Contract-based
refutations and the three main closure votes are recorded separately. The Claude
orchestrator counted twelve verification/fresh-review jobs; interrupted jobs were
resumed rather than discarded and restarted as a new broad review campaign.

## Findings and resulting behavior

Runtime defects and test-coverage gaps are different categories. The rows below
summarize the final behavior instead of adding duplicate reviewer counts together.

| Area | Reproduced failure and repair |
| --- | --- |
| Published reports and terminal failures | A display error deleted already-published reports and returned execution failure. Publication and presentation are now separate. The process entry point handles broken/closed streams while preserving 0/1/2 statuses; callable `main()` does not redirect the host's descriptor. |
| Failed reruns and bundled inputs | Early resource lookup failures left stale acceptance, and early repair attempts could delete a bundled input. Candidate input locations are protected even when every lookup fails. Recognized old reports are removed best effort; unknown/unreadable files are retained and named in stderr. |
| Partial publication | Interrupts could leave half a pair. Rollback removes newly published files and recognized stale reports, preserving unrelated files it never replaced. A successful explicit output name replaces its previous contents, as documented. Publication is atomic per file, not a two-file transaction. |
| Report replay | Shared acyclic objects caused repeated exponential traversal. An initial size cap incorrectly rejected valid large reports, and an initial cache weakened depth checks. The final cache records subtree height, preserving cycle/depth rejection regardless of traversal order without imposing a new artifact-size cap. |
| Fingerprints and rendering | Public fingerprint errors are normalized to `InputError`, with deterministic tie ordering. Huge finite duration metadata renders without overflow. JSON display notation distinguishes literal escapes from controls and survives Markdown HTML escaping, including `&`, `<` and `>`. Matching rules are unchanged. |
| Offline/wheel gates | Checks survive `python -O`; child environments omit unrelated credentials and instrument socket/DNS entry points. Parent/child import origins must agree, every child must provide a fresh receipt, and all four commands must produce a report with the expected acceptance decision. |
| Verification false pass | A comparison child could exit 1 without evaluating anything, first by reusing a prior receipt and later by crashing after its own receipt. Both triggers were reproduced. Missing/wrong comparison reports now fail verification explicitly. |
| Regression tests | Earlier subprocess tests sometimes imported the installed writer instead of the revision under test. Tests now pin their checkout source. Targeted repairs cover real stdout refusal, metadata collisions, both report markers, installation layouts, traversal and invalid-name validation. Missing test coverage is not described as a current runtime defect. |

The independent reviews also caught regressions introduced by earlier repairs:
empty-name fallback, unsafe early cleanup, arbitrary report-size rejection,
order-sensitive depth validation, ordinary backslash doubling, untested process
entry changes and the verification receipt bugs. These were reproduced and fixed;
they are not hidden behind the final passing test count.

## Refuted or deliberately unchanged

- Currency uppercase, supplier Unicode casefold, invoice-ID outer-trim-only and
  evidence `splitlines()` behavior follow the frozen specification. No evaluation
  labels, normalization rules or policy thresholds were changed to improve scores.
- Reports are unsigned reproducibility artifacts. Consistent edited inputs do not
  prove authorship or history; variable provenance is deliberately excluded from
  baseline identity. No attestation system was added.
- Parent-directory symlinks are allowed; leaf destinations and input collisions are
  protected. Directory confinement was not promised, and macOS `/tmp` aliases are
  legitimate. No new confinement guarantee is claimed.
- Best-effort Git provenance may be null after missing/failed/timed-out Git lookup.
  That is now described accurately rather than equated solely with a wheel install.
- An attempted umask-based permission change was reverted because it introduced a
  process-global race. No new file-permission policy was invented.
- Frozen labels were authored before fixture construction. Planning a deliberately
  imperfect fixture does not establish a violation of that construction order.
  This remains a synthetic, agent-authored demonstration, not blind annotation or
  measured model accuracy. EVAL-11's wording caveat remains documented.
- Python 3.12.14 was tested locally. The declared range includes 3.13, which was not
  tested in this run. No remote CI/Linux execution is claimed.
- Optional simplification and new features were left out. A machine-readable
  cleanup substatus was not added; execution failure remains exit 2, with details on
  stderr. Redirecting stderr hides those details.

Earlier raw consolidation notes are historical working material. In particular,
the initial dismissal of unrelated-file deletion was later reversed for failed
publication/validation paths. This record supersedes that stale disposition.

## Evidence and methodological limits

- Initial delivery: 241 passing tests. Latest candidate: **341 passing tests**;
  Ruff, offline verification, build and installed-wheel checks passed.
- Baseline and repaired remain accepted (0); regression and its comparison reject
  (1). Invalid execution remains 2. All ten frozen file hashes are unchanged.
- Ten targeted mutation families were caught by named regression tests, with
  outputs preserved in [mutation results](../reports/claude-review/round6/mutation-results.json).
  The mutation harness clears Python bytecode caches between edits; otherwise a
  same-length edit within one second can falsely appear to survive.
- Parent direct-exit verification at clean `5cb4d1c` passed **all 27 checks**,
  including the full suite, wheel, expected failure probes, frozen hashes, snapshot
  identity and saved replay. Evidence: `reports/claude-review-parent/candidate-checks/`
  in the main checkout. Main-checkout verification remains pending integration.
- Parent independently checked 5,000 shared/cyclic/depth graph cases against an
  uncached reference during the replay repair, with no mismatch.
- Some early reviewers overlapped writer edits. They detected drift and used Git
  archives for cited reproductions. Those passes are not represented as immutable
  live-tree reviews. Later snapshots at `1c20cf9`, `f41daa3` and `5cb4d1c` were kept
  separate and checked against every tracked file's committed bytes.
- The initial Codex wrapper hung on inherited stdin; its successful retry used
  `/dev/null`. One later adversarial pass returned an empty output and was retried.
  Native/adversarial read-only sandbox limits remain explicit in the raw reports.
- Claude's headless background ceiling killed unfinished jobs after ten minutes.
  Recovery disabled that ceiling for the same session. The later HTTP 429 quota
  interruption is a separate blocker and does not count as a successful review.
- Coding-agent subscriptions were used for review. The evaluation application
  still makes no live model calls and uses only standard-library runtime code.

Raw records are retained under `reports/claude-review/`. Parent direct-exit checks
are retained under main's `reports/claude-review-parent/`. Git identities and valid
signatures were checked for every added commit. Final integration/verification and
the completion statement remain pending the scheduled continuation.
