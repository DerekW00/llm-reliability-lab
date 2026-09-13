# Reconstructed commit timeline

On September 12, 2026, the owner requested that the existing commit dates be
spread across the preceding two weeks. The 39 existing commits now have assigned
author and committer dates from **August 30 through September 12, 2026**, in
America/Los_Angeles time. This is a documented date reconstruction, not a record
that implementation took place over those two weeks.

The original implementation and reviews occurred on September 11–12; GitHub
publication occurred on September 12. Those actual dates remain in the original
signed history and the dated build/review records. The documentation commit that
records this rewrite uses its actual creation time.

## Sequence and preserved evidence

| Assigned dates | Existing milestones |
| --- | --- |
| August 30–31 | Contracts, frozen policy, input validation, CI and dependency setup |
| September 1–4 | Evaluator, CLI, data and fixture integration; comparison boundaries |
| September 5–6 | Integrated results, provenance repair, adversarial review and local handoff |
| September 7–11 | Review findings, repair regressions, output handling and stronger verification |
| September 12 | Final Opus review, local integration and GitHub publication |

Every rewritten commit retains its exact original file tree, message, author and
committer identity. Merge parents retain the same relationships under the new
hashes, and every parent precedes its child. All 39 replacement commits were
signed again with the configured project identity and their signatures verified.
Those new signatures were created during this rewrite, not on the assigned dates.

The original signed history is retained under
[`history/original-timestamps-2026-09-12`](https://github.com/DerekW00/llm-reliability-lab/tree/history/original-timestamps-2026-09-12).
Existing source hashes in generated reports and review records continue to refer
to that original history. Report timestamps, frozen data, policy, evaluation code,
tests and CI configuration have not been changed to fit the reconstructed dates.

A local Git bundle and a full machine-readable mapping are also retained as
recovery evidence. The public mapping below links both versions of each commit.
Original author and committer times were equal in this history; both assigned
fields use the new time shown. All times below are Pacific (UTC−07:00).

## Commit mapping

| Original | Rewritten | Original time | Assigned time | Existing commit subject |
| --- | --- | --- | --- | --- |
| [83fae78](https://github.com/DerekW00/llm-reliability-lab/commit/83fae7824dd9daea8deedb862963e3b39f56c3f9) | [0a58e4a](https://github.com/DerekW00/llm-reliability-lab/commit/0a58e4a9929da2fc24bd9fcb91938a23e08ca572) | 2026-09-11 22:07:03 | 2026-08-30 09:30:00 | Define strict extraction contracts and freeze the illustrative release policy |
| [43393be](https://github.com/DerekW00/llm-reliability-lab/commit/43393be08955cdcc349c3d1b4db91b274db39d88) | [31f6206](https://github.com/DerekW00/llm-reliability-lab/commit/31f6206fc5c6308967396a1326575163f4a28e21) | 2026-09-11 22:11:02 | 2026-08-31 10:15:00 | Test strict input boundaries and reject non-finite JSON values |
| [89cbdb2](https://github.com/DerekW00/llm-reliability-lab/commit/89cbdb277cb8e635a011ef182d4bf8489a7bdc76) | [69ef3bc](https://github.com/DerekW00/llm-reliability-lab/commit/69ef3bcd4429828ef8b417645e50d7d970133f11) | 2026-09-11 22:12:53 | 2026-08-31 14:10:00 | Add offline CLI acceptance checks and a pinned CI workflow |
| [3b5651f](https://github.com/DerekW00/llm-reliability-lab/commit/3b5651fbe1bbfa1a20e62a3f3978b695df1b7cae) | [0eb9fcb](https://github.com/DerekW00/llm-reliability-lab/commit/0eb9fcb943041aab4ae25da15bcbf516729c8cd4) | 2026-09-11 22:14:39 | 2026-08-31 16:30:00 | Pin the interpreter and build tools for reproducible local runs |
| [1931ff4](https://github.com/DerekW00/llm-reliability-lab/commit/1931ff41eaf0b91b6654fba8eaf5c227566cf4b1) | [0d1683e](https://github.com/DerekW00/llm-reliability-lab/commit/0d1683e8280886725879c03ee9bf16a37a6dd4c8) | 2026-09-11 22:17:24 | 2026-09-01 11:20:00 | Implement deterministic evaluation and replay-verified policy gate |
| [9e38d11](https://github.com/DerekW00/llm-reliability-lab/commit/9e38d11b375a1d121e3fae258bc95b805be16b63) | [b7b2d4e](https://github.com/DerekW00/llm-reliability-lab/commit/b7b2d4e76e56db8cb56b015e09ff73d7bc839e58) | 2026-09-11 22:18:19 | 2026-09-01 15:40:00 | Integrate the evaluator and replay-verified release gate |
| [666e433](https://github.com/DerekW00/llm-reliability-lab/commit/666e4337a5c96720138c50e81ad7788d44b7806e) | [966e4b5](https://github.com/DerekW00/llm-reliability-lab/commit/966e4b5b2d9de1b8700243d91f9d00af4e821cb1) | 2026-09-11 22:17:18 | 2026-09-01 16:20:00 | Add guarded offline CLI and computed reliability reports |
| [2b359cf](https://github.com/DerekW00/llm-reliability-lab/commit/2b359cf092af94aa576163ca571500f15db803a7) | [cdef370](https://github.com/DerekW00/llm-reliability-lab/commit/cdef37038c39f18aa54be0710d9eefc083762399) | 2026-09-11 22:18:19 | 2026-09-02 10:10:00 | Integrate the terminal CLI and readable evaluation reports |
| [0b743ed](https://github.com/DerekW00/llm-reliability-lab/commit/0b743ed403e7dda62f71bddf947c45d1172b5388) | [a274276](https://github.com/DerekW00/llm-reliability-lab/commit/a274276c3e363865f33a2ece4d8f229634dc0823) | 2026-09-11 22:19:20 | 2026-09-02 11:00:00 | Record the first integrated CLI verification checkpoint |
| [c2c4c4f](https://github.com/DerekW00/llm-reliability-lab/commit/c2c4c4f26abbe413eb8db02e1b2570f3ffd458b2) | [d97eec8](https://github.com/DerekW00/llm-reliability-lab/commit/d97eec881421867b26279d10266de1b58d3a0d1e) | 2026-09-11 22:19:26 | 2026-09-02 13:40:00 | Freeze original synthetic invoice documents and reviewed reference labels |
| [7993f4f](https://github.com/DerekW00/llm-reliability-lab/commit/7993f4f0c2fb0b43a34224595939b0c623acaeed) | [76b41b1](https://github.com/DerekW00/llm-reliability-lab/commit/76b41b1508288a8e5e6c68787a09d2d4167a4e75) | 2026-09-11 22:19:58 | 2026-09-02 15:05:00 | Integrate frozen synthetic documents and reviewed reference labels |
| [0c2970c](https://github.com/DerekW00/llm-reliability-lab/commit/0c2970c09e84744b26ea69be085b43a2554cefee) | [e3f123d](https://github.com/DerekW00/llm-reliability-lab/commit/e3f123db73d177f4d2ad628f58a7b2af184e0949) | 2026-09-11 22:19:18 | 2026-09-03 10:15:00 | Bound report construction and test exact comparison boundaries |
| [6a27dde](https://github.com/DerekW00/llm-reliability-lab/commit/6a27dde8fb6ea0038729852ccfba894386bf39bc) | [ae74f29](https://github.com/DerekW00/llm-reliability-lab/commit/ae74f29eba374e4cae68d63a46320f1563fbbcef) | 2026-09-11 22:19:58 | 2026-09-03 11:25:00 | Integrate exact gate arithmetic and bounded report replay |
| [92a8be3](https://github.com/DerekW00/llm-reliability-lab/commit/92a8be3c3f5294e3b9037568d130ec1d0b4844f5) | [419607f](https://github.com/DerekW00/llm-reliability-lab/commit/419607f0f6c47fc8f906368944ac730d54be1a01) | 2026-09-11 22:21:23 | 2026-09-03 15:10:00 | Clarify supplemental development coverage without changing the evaluation freeze |
| [2e6bda6](https://github.com/DerekW00/llm-reliability-lab/commit/2e6bda66a92b27405963d256b234ea0bebc0e2f4) | [b22d0ab](https://github.com/DerekW00/llm-reliability-lab/commit/b22d0abd5df4d682c3851c0611daf38ffc41cdbf) | 2026-09-11 22:22:09 | 2026-09-04 10:00:00 | License original project contents and document construction provenance |
| [d55789b](https://github.com/DerekW00/llm-reliability-lab/commit/d55789baeae2d998f8bd04f3d806adcc57aa691f) | [958ee73](https://github.com/DerekW00/llm-reliability-lab/commit/958ee73c2bf6fb56bce91d0cd3ed747192e5d35f) | 2026-09-11 22:23:34 | 2026-09-04 13:25:00 | Add static regression fixtures and supplemental duplicate-looking invoices |
| [84ed2f2](https://github.com/DerekW00/llm-reliability-lab/commit/84ed2f21b86f9d022af874603a6f65ff1afd55b9) | [50ff0ba](https://github.com/DerekW00/llm-reliability-lab/commit/50ff0ba9f33e922456764e9974cb41382cdf4a0a) | 2026-09-11 22:23:59 | 2026-09-04 15:10:00 | Integrate fixture scenarios and supplemental duplicate-document cases |
| [e00e2b1](https://github.com/DerekW00/llm-reliability-lab/commit/e00e2b1f7603d82301a90251d50368662c51c7f9) | [ab9bb19](https://github.com/DerekW00/llm-reliability-lab/commit/ab9bb191bf6dc15e477662b72cce18af00c3c656) | 2026-09-11 22:27:06 | 2026-09-05 12:40:00 | Document computed demo results and complete integrated acceptance coverage |
| [9b1ec55](https://github.com/DerekW00/llm-reliability-lab/commit/9b1ec55b221e98c7a0ce46fa34b1623002e55a44) | [797c268](https://github.com/DerekW00/llm-reliability-lab/commit/797c268831d6720a82f6ea7d6dea26b3bd1d3027) | 2026-09-11 22:31:53 | 2026-09-05 15:05:00 | Fix tracked source provenance path resolution |
| [92593f6](https://github.com/DerekW00/llm-reliability-lab/commit/92593f67a046f965738ff5353b99a396fe185b13) | [0290d93](https://github.com/DerekW00/llm-reliability-lab/commit/0290d936a6db1c5f66a44b2ba830e7a91fda22b6) | 2026-09-11 22:34:11 | 2026-09-05 16:00:00 | Preserve generated reports with verified source provenance |
| [b03e7e9](https://github.com/DerekW00/llm-reliability-lab/commit/b03e7e9be622f01ec68a5c909302428abe9eff70) | [5556a23](https://github.com/DerekW00/llm-reliability-lab/commit/5556a239ed7663f20e8e14f442f224c7dc0078f1) | 2026-09-11 22:41:07 | 2026-09-06 12:20:00 | Add independent adversarial acceptance review |
| [c74f248](https://github.com/DerekW00/llm-reliability-lab/commit/c74f248bb4ddb37696f9947428fa5a9fe6dbaf9e) | [fbf5bcd](https://github.com/DerekW00/llm-reliability-lab/commit/fbf5bcd1e44b5f7f9ffb04cc77b3ea0ea79d1c69) | 2026-09-11 22:42:01 | 2026-09-06 14:40:00 | Integrate independent adversarial review and verified defect closure |
| [126a9a7](https://github.com/DerekW00/llm-reliability-lab/commit/126a9a7c6de0c56cc852800e8a4b8a4ed5653320) | [d658a5a](https://github.com/DerekW00/llm-reliability-lab/commit/d658a5a7d889266c584e58084ddb05a8f528252f) | 2026-09-11 22:46:48 | 2026-09-06 16:05:00 | Complete verified local delivery and morning review handoff |
| [10b1792](https://github.com/DerekW00/llm-reliability-lab/commit/10b179262e86240188967fff50d29451b4f2e2db) | [7be3c35](https://github.com/DerekW00/llm-reliability-lab/commit/7be3c35fd17dd8529b46a86e6c451723d32bf9b7) | 2026-09-12 01:51:59 | 2026-09-07 10:00:00 | Fix reproduced defects found by an independent multi-reviewer pass |
| [d5b2210](https://github.com/DerekW00/llm-reliability-lab/commit/d5b22105ca5db18b6c3b5a225707c23e26ddf55f) | [740f138](https://github.com/DerekW00/llm-reliability-lab/commit/740f138d80002d26cad80614970568f518d15785) | 2026-09-12 01:56:45 | 2026-09-07 15:15:00 | Close two public-contract gaps raised by the in-code guidance reviewer |
| [0395a1a](https://github.com/DerekW00/llm-reliability-lab/commit/0395a1a67fb08e99cfd0f813e04e5d285f03b547) | [ff0eb23](https://github.com/DerekW00/llm-reliability-lab/commit/ff0eb230cc1c3c20d3267b3a358d6caf793938a6) | 2026-09-12 02:05:25 | 2026-09-08 11:20:00 | Repair three regressions introduced by the first round of fixes |
| [2653c68](https://github.com/DerekW00/llm-reliability-lab/commit/2653c68d6bfaf31d261d5941fdd2d60c14f65c92) | [53f6db7](https://github.com/DerekW00/llm-reliability-lab/commit/53f6db7fc5b89647036162848511d6feff404d9c) | 2026-09-12 02:10:21 | 2026-09-08 14:35:00 | Make the replay nesting limit independent of traversal order |
| [b05f74a](https://github.com/DerekW00/llm-reliability-lab/commit/b05f74a1e916e0660162b0a025321aa6934cc73c) | [08be037](https://github.com/DerekW00/llm-reliability-lab/commit/08be037ec829f9304a66adbfa1faae613b324275) | 2026-09-12 02:50:03 | 2026-09-08 16:15:00 | Repair the repair code, and replace the tests that only looked like guards |
| [3e98fef](https://github.com/DerekW00/llm-reliability-lab/commit/3e98fef484721ecaadd860a47778326d04a0d6d2) | [a1621bd](https://github.com/DerekW00/llm-reliability-lab/commit/a1621bde8b046f1e1ac9a2e396315762f196d042) | 2026-09-12 03:16:23 | 2026-09-09 10:15:00 | Make failure cleanup best effort and say so, and close the guard gaps |
| [5ce81ab](https://github.com/DerekW00/llm-reliability-lab/commit/5ce81ab5057a822c5c115bcff4d22f35a0d31c68) | [c7f2c0b](https://github.com/DerekW00/llm-reliability-lab/commit/c7f2c0b282f24f18fbd8c34f5cb12014bc899aa1) | 2026-09-12 03:22:39 | 2026-09-09 13:45:00 | Give supplied identifiers and excerpts a reversible display notation |
| [baec9f3](https://github.com/DerekW00/llm-reliability-lab/commit/baec9f356ba31f0e7e4295436125547909d4b451) | [e84f0c2](https://github.com/DerekW00/llm-reliability-lab/commit/e84f0c288bf8b1ee0acd18212009aa0458bfa53b) | 2026-09-12 03:25:12 | 2026-09-09 15:10:00 | Regenerate the example reports at the revision that produced them |
| [1c20cf9](https://github.com/DerekW00/llm-reliability-lab/commit/1c20cf925cdbb3f76727d3febd9c6f8cac1fe124) | [5b6a281](https://github.com/DerekW00/llm-reliability-lab/commit/5b6a281e4a804e9d53d65fba50287eca04a03a06) | 2026-09-12 03:33:55 | 2026-09-10 10:20:00 | Stop the offline gate certifying code it was not given, and finish the notation |
| [57655fc](https://github.com/DerekW00/llm-reliability-lab/commit/57655fca4f8e205bd5517f32561c59c5a27806df) | [3cb9b6b](https://github.com/DerekW00/llm-reliability-lab/commit/3cb9b6b88e95755d26e3ecb81229b09403c1f09a) | 2026-09-12 04:19:19 | 2026-09-10 14:05:00 | Require fresh subprocess evidence and preserve untouched outputs on failure |
| [f41daa3](https://github.com/DerekW00/llm-reliability-lab/commit/f41daa3d2176a039450ae7f13dd2fe50b1260c07) | [3f32d10](https://github.com/DerekW00/llm-reliability-lab/commit/3f32d102a8dc6d250160a26b38e7e002f2d416da) | 2026-09-12 04:20:14 | 2026-09-10 15:30:00 | Regenerate example reports from the verified repair source |
| [5cb4d1c](https://github.com/DerekW00/llm-reliability-lab/commit/5cb4d1c88dc8746a890b3e5ac2942a106f86c5e2) | [93f45c2](https://github.com/DerekW00/llm-reliability-lab/commit/93f45c247ec0fa2a71bd46ab6cb721506dbb9452) | 2026-09-12 04:30:21 | 2026-09-11 10:15:00 | Require every offline scenario to produce its expected verdict report |
| [bd84199](https://github.com/DerekW00/llm-reliability-lab/commit/bd841999cd9f903be98a88de250525cf1ffa8ba2) | [70acc5c](https://github.com/DerekW00/llm-reliability-lab/commit/70acc5c4ce0abd6d97da2ee3e602b3cbc0244dbc) | 2026-09-12 04:38:22 | 2026-09-11 15:00:00 | Record verified repairs and the scheduled final Opus review handoff |
| [599596f](https://github.com/DerekW00/llm-reliability-lab/commit/599596fa14973140a869360f9f6bfc0eeed353df) | [16e51bf](https://github.com/DerekW00/llm-reliability-lab/commit/16e51bf174284edc657d73bbf294de87bb645ad0) | 2026-09-12 05:50:28 | 2026-09-12 10:00:00 | Complete Opus repair review and verify local main integration |
| [4860d43](https://github.com/DerekW00/llm-reliability-lab/commit/4860d43eed1ee8e29bdaf6705dea7e8663546d0d) | [4e8bc3c](https://github.com/DerekW00/llm-reliability-lab/commit/4e8bc3c5e990db9b2cefd385889318595395682f) | 2026-09-12 21:57:27 | 2026-09-12 21:57:27 | Prepare GitHub quickstart and document publication authorization |
| [10bc892](https://github.com/DerekW00/llm-reliability-lab/commit/10bc8927e971e70bbb4976e888bd26ca4c9529f6) | [1c2db09](https://github.com/DerekW00/llm-reliability-lab/commit/1c2db092c41246741575f5b67601754df716bd76) | 2026-09-12 21:59:38 | 2026-09-12 21:59:38 | Record public GitHub publication and remote verification links |
