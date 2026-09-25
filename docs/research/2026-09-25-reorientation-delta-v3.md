# Re-Orientation Delta v3 — 2026-09-25

**Supersedes the operational content of:** `2026-08-30-reorientation-delta-v2.md` (uploaded, workspace-root) and the 2026-09-06 six-document corpus audit, for everything those two documents say about repository state. It does not supersede their governance findings (R1–R11), which still stand.
**Status:** ⚠️ Specified — read-only survey of the live GitHub state and three checked-out heads on 2026-09-25. Repo state is authoritative over this file.
**Type:** Re-orientation delta. Comparison + correction + verdict. No canon promotion, no new architecture, no new work track.
**Truth-status vocabulary used here:** the ADR Suite v2.0 four-label set (Verified / Specified / Aspirational / Unverified), because that is the one the repo actually uses in headers (see §6). Not the five-label `EPISTEMIC_TAG_SCHEMA_v0.1` set that this same session authored in 2025-11 — see §8.

**Evidence base.** Five uploaded documents (2026-08-30 → 2026-09-13) read in full; live GitHub PR/issue state for `G-0-B/FLOSS` and `kalisam/FLOSS`; three worktrees — `gob/main` @ `138f342`, PR #41 head `reconcile/pr38-salvage-20260817` @ `aee4745`, PR #43 head `feat/preservation-spine-standalone` @ `2ab47c1`; four parallel read-only audits (secrets across all 629 reachable commits; orientation-surface drift; test execution; self-knowledge synthesis of ~50 in-repo docs). Nothing was modified in any worktree. Exact commands are in §10.

---

## 0. Headline

The repo has more real, tested capability than any of its orientation surfaces admit, and less merged capability than its planning layer assumes. Specifically:

1. **Almost all of the last three months of work is on one unmerged branch.** PR #41 is 267 commits / 366 files / +75,638 lines ahead of `main`. `main` has moved two commits (a js-yaml bump) since 2026-08-23. Every ADR from 18 to 20, the renamed ADR-10/11, the v1.4.0 kernel, the corrected CLAUDE.md, the anchors, the review records, the reasoning ensemble, and the activity log exist **only on PR #41**. An agent that starts from `main` is orienting against July.
2. **Nothing can merge without an operator bypass**, and this is a configuration fact, not a review backlog. The `safety rulez` ruleset requires a Copilot code review that cannot be requested on this repository (seam packet §3, verified at `docs/research/2026-09-02-pr41-lineage-seam-packet.md:78-95`). All four substantive PRs (#41, #43, #59, #61) show 0 failing checks, `REVIEW_REQUIRED`, no approvals.
3. **The code on PR #41 is in better shape than its own documents say.** The required Python gate passes 1052/1052 (main: 346). The four active Rust crates pass `cargo test` (40/40) and `cargo fmt --check`. Two of the P1 "integrity holes" from the 08-30 delta (`_AUDIT_SINK` never read; `$PID` assignment) are **fixed at PR #41 head** and no document records that.
4. **Three of the corpus audit's P0s were mis-scoped as repo problems.** The `ow_mcp_at_…` token, the six provider keys, and the atlas `FILE_INVENTORY.tsv` are not in any git object in any reachable ref. They are workspace-root (`C:\~shit\`) files. Only one credential is actually committed: the Supabase anon JWT, in two archived `.env` files sharing blob `f4beee0`, present on `main`, #41, #43, and never deleted on any branch.
5. **The corpus audit's central diagnosis — "rule production outpacing rule application" — is confirmed and has a measurable second form: capability outpacing orientation.** INDEX.md marks three ADRs Accepted whose files say PROPOSED; CLAUDE.md lists a `packages/memory` that does not exist and omits four packages that do; the work board is 142 commits stale; `heartbeat-running.md` still says STOP is present (it was removed 2026-05-26); the context surface routes a `serena-memory` lane to a tool that was removed 2026-08-11 and then quietly resurrected by a main-merge.

The single highest-leverage move is unchanged from the corpus audit but now has concrete shape: **one operator decision (§7.1) unblocks four PRs and moves the entire ADR-18/19/20 canon onto `main`**, after which every orientation-surface correction in §5 becomes a one-branch job instead of a two-branch job.

---

## 1. Assumption corrections against the 2026-08-30 delta and 2026-09-06 audit

| Prior claim | Live reality (2026-09-25) | Verdict |
|---|---|---|
| PR #41 "dominant blocker, 368 files, 27 triaged inline comments" — a review backlog | Still open, now 366 files. The actual blocker is an unsatisfiable ruleset rule, not review volume. The 09-05 fix-sweep packet (`docs/reviews/2026-09-05-pr41-fix-sweep/`) has a PACKET.md but no reviewer outputs and no RESULT.md — the external review never returned. | ❌ Mischaracterised — blocker is configuration |
| `_AUDIT_SINK` never read → every consensus MCP call bypasses the audit trail (P1) | At `aee4745`, `_AUDIT_SINK` is defined and passed to `register_audited_tools(...)` in both `packages/metacoordinator_mcp/server.py:162,189` and `packages/reasoning_ensemble/mcp_server.py:369,396`. Only comments describing the old behaviour remain. | ❌ Falsified (fixed on #41; still true on `main`) |
| `stop_mcp_daemons.ps1:19` assigns to read-only `$PID` (P1) | Script uses `$daemonPid`; reads `$PID` only for a self-check at line 100; line 84 comments explain why. No `$pid =` in any `scripts/*.ps1`. | ❌ Falsified (fixed on #41) |
| `jsonschema` undeclared in `ARF/requirements.txt` (P2) | Still absent from `ARF/requirements.txt`, but `requirements-ci.txt:26` declares `jsonschema[format-nongpl]>=4.23.0` and both CI jobs install it. Runtime installs from `ARF/requirements.txt` alone would still get the silent no-op. | ⚠️ Partially held |
| `ow_mcp_at_…` bearer token + six provider keys (P0, "in repo") | Zero hits across all 629 commits, all refs, all three trees. Workspace-root files only. | ❌ Out-of-repo (rotate-only) |
| `FILE_INVENTORY.tsv` re-leaks the JWT | Not in any tracked ref. Out-of-repo. | ❌ Out-of-repo |
| Supabase anon JWT in two archived `.env` (P0) | Confirmed: blob `f4beee0` at `archive/bolt_snapshot_5_4/project/.env` and `archive/old_project/.env` on `main`, #41, #43. Added in `af544f6` and `edad4cd`. `git log --all --diff-filter=D` on these paths returns nothing. `.gitignore` has `.env` but that does not untrack committed files. No secret-scan CI, no pre-commit, no `hooks/` on any ref. | ✅ Held — the one real in-repo exposure |
| "Are ADR-18/19/20 on `main` or branch-only?" (open question) | Branch-only. `main`'s `docs/adr/` has 21 files stopping at ADR-17 plus the un-renamed `ADR-MCP-ORCHESTRATOR.md` / `ADR-N-IPFS…`. | ✅ Resolved: branch-only |
| "Does `provenance_validation.test.ts` pass, is it in CI?" | Exists with six siblings. No workflow runs Tryorama or Sweettest. No Sweettest code on #41 (one comment header in `consent_integrity/src/lib.rs:601`). PR #61 would add it; PR #64 would retire Tryorama. | ✅ Resolved: exists, never run |
| Heartbeat "alive but shallow" | Not checkable from here (workspace-root). `heartbeat-running.md` in-repo still asserts STOP present as of 05-19. | Unverified; doc confirmed stale |
| Single-machine 94-commit exposure | `G-0-B/FLOSS` has 2 forks; `kalisam/FLOSS` is one (fork created 2026-04-19, pushed 2026-09-11, lagging `main` by 2 commits). PR #41's 267 commits are on GitHub. The specific "94 commits" figure could not be reconstructed. | ⚠️ Likely closed by push; count unverified |

---

## 2. Where things actually are

### 2.1 Remotes and branches

| Ref | Head | Role |
|---|---|---|
| `G-0-B/FLOSS` `main` | `138f342` (2026-09-13) | Canonical. Org repo, created 2025-08-25, signoff required, 2 real issues (#28, #62), 14 open PRs (10 dependabot). |
| `kalisam/FLOSS` `main` | `2d5e647` (2026-08-23) | **Fork**, 2 commits behind canonical. This session's designated branch lives here. Zero open PRs. |
| PR #41 `reconcile/pr38-salvage-20260817` | `aee4745` (2026-09-07) | 267 commits ahead. Carries ADR-18/19/20, kernel v1.4.0, corrected CLAUDE.md, `.anchors/`, `docs/reviews/`, `packages/{activity_log,reasoning_ensemble,tests,mcp_daemon.py,omniroute_client.py}`, `hooks/`, +9,988 lines of `skill-corpus`, +12,605 lines of `docs/reviews`. |
| PR #43 `feat/preservation-spine-standalone` | `2ab47c1` (2026-09-06) | 46 commits, 26 files, +15,397. `packages/preservation_spine/` and its specs. Merge-base with #41 is `2d5e647`; the **only shared touched file is `docs/specs/spec-registry.json`** — one predictable conflict. |
| PR #59 → base #43 | `7edd1c8` | Durability fix for #43; folds in. |
| PR #61 `codex/sweettest-substrate-bridge` | `4618ec0` | Rust Sweettest coverage. No adversarial review recorded. |
| PR #64 `chore/retire-tryorama-suite-main` | `8c92928` | Retires JS Tryorama. Pairs with #61. |

The seam packet's proposed merge order (§9.2 there) — **#61 → #43 (with #59 folded in) → #41 → `feat/coordination-room-rebased`** — is consistent with the file-overlap measurement above and is still the right order.

### 2.2 Where PR #41's +75k lines land (insertions, files)

| Area | Lines | Files | Note |
|---|---|---|---|
| `docs/reviews` | 12,605 | 34 | Multi-model review records; the 08-29 model-identity anomaly review alone has 10 reviewer JSONs across 9 models |
| `scripts` | 11,260 | 41 | |
| `skill-corpus` | 9,988 | 64 | |
| `docs/research` | 8,717 | 74 | |
| `packages/activity_log` | 6,701 | 9 | |
| `.anchors` | 5,606 | 5 | Two genesis anchors, `prev_root: None` on both, `.ots` proofs both PENDING (no Bitcoin attestation) |
| `packages/reasoning_ensemble` | 3,187 | 9 | |
| everything else | ~17,500 | | |

Roughly 40% of the branch by line count is documents about the work rather than the work.

### 2.3 Doc mass vs code mass (PR #41, tracked, excl. `node_modules`)

| | Files | Lines |
|---|---|---|
| Markdown, all | 630 | 191,247 |
| — `docs/research` | 182 | 63,880 (of which `intake_raw` 88 / 29,940) |
| — `archive` | 28 | 19,316 |
| Python | 216 | 73,788 (32,566 in tests) |
| Rust | 31 | 9,961 |
| TypeScript | 16 | 2,696 |
| **Code total** | | **≈86,400** |

Markdown : code ≈ **2.2 : 1**. `docs/research` alone is 0.74× all code. This is the quantified form of `doc-explosion-acknowledged.md`.

---

## 3. What is actually verified (measured 2026-09-25)

| Check | PR #41 `aee4745` | `main` `138f342` |
|---|---|---|
| Required Python gate (`pytest packages/ tests/ scripts/tests/` minus one deselect) | **1052 passed**, 9 skipped, 0 failed, 46 s | 346 passed, 0 failed, 12 s |
| Advisory full suite (`pytest -q` from root, with `ARF/requirements.txt`) | **69 failed**, 1173 passed, 16 skipped | (CI baseline: 77 failed) |
| `cargo test` — `rose_forest_integrity`, `consent_integrity` | 15/15, 15/15 | not run |
| `cargo test` — `rose_forest`, `consent` coordinators | 8/8, 2/2 | not run |
| `cargo fmt --all -- --check` | clean | not run |
| Tryorama / Sweettest in any CI workflow | **none** | none |
| Secret-scan CI or pre-commit | **none** | none |

The 69 advisory failures have three root causes, not sixty-nine:
- **~48** — `MultiScaleEmbedding` API mismatch (tests call `.add/.compose/.to_dict/.from_dict`, which don't exist). This is the open item CLAUDE.md already names.
- **~20** — `ConversationMemory` knock-on from the same mismatch (`NoneType has no attribute add_embedding`), plus two genuine assertion failures (a search returning nothing; a test expecting `'Claude'` and getting `'Claude Sonnet 4.5'`).
- **~8** — hygiene: six `async def` tests with no asyncio marker; one test reading stdin under capture; one migration-report text mismatch.
- **1** — `test_audit_packets_classifies_older_packet…superseded` asserts `2 == 0`. This is the test the green set *deselects*. It is ADR-20 D-B1 (the unbuilt supersession view) failing honestly. Deselecting it is the ratchet working as designed, but the ratchet should be recorded next to the ADR, not only in a workflow YAML.

**Excluded Rust crates** (`ontology_integrity` 47 `#[test]`s, `memory_coordinator` 3, `hrea_coordinator` 2) are not in the workspace and were not run. CLAUDE.md's statement of the four-member zome set matches `ARF/Cargo.toml` — the one orientation claim that is fully accurate.

---

## 4. What the repo says blocks it, ranked, with what this survey adds

| # | Blocker (as the repo states it) | Source | This survey |
|---|---|---|---|
| 1 | Unsatisfiable `copilot_code_review` rule in ruleset `safety rulez` (id `9980168`) | seam packet §3, §9.1 | Confirmed by live PR state: all four PRs `REVIEW_REQUIRED`, zero approvals, zero failing checks. **Operator-only.** |
| 2 | `entry_has_consent()` accepts any non-empty string as `decision_action_hash`; the consent anchor does not exist; ADR-19 ratification and all governed ADR changes wait on it | ADR-12, ADR-19, `adr19-ratification-deferred-to-consent-gate.md` | Compounded by a **new contradiction**: commit `aee4745` records a 2026-09-01 packet whose `consent_ref` is a SHA-256 source-chain digest (admittedly not an ActionHash), while ADR-19 forbids any placeholder. The evidence file it cites, `docs/research/2026-09-06-consent-anchor-lane-a-probe.md`, **does not exist in the repo**. |
| 3 | No end-to-end Holochain test path: Tryorama incompatible with hc 0.6.1; Sweettest port unwritten | `tryorama-tooling-gap-2026-05-26.md`, ADR-12, `holochain-0-7-migration-pending.md` | Confirmed. Seven Tryorama files exist, none run in CI. PR #61 is the fix and has no review. |
| 4 | Provenance anchor has no external witness | `docs/specs/provenance-anchor.spec.md` "CORRECTION 2026-08-29" | Confirmed at head: `git tag` → 0 tags; `scripts/provenance_anchor.py` prints commands without running them; both `.ots` PENDING; two genesis anchors with `prev_root: None`; `opentimestamps` in no requirements file. Spec header says tier-2 review "PERFORMED 2026-08-29"; its Outstanding section says it "has **not** been performed". |
| 5 | ADR-20 D-B1 (audit disposition / `superseded` view) unbuilt | ADR-20 | Confirmed by the deselected failing test (§3). |
| 6 | Agent-surface projections never regenerated → new timeouts reach no harness | `2026-08-31-review-loop-session-learnings.md` §7 | Not checkable (workspace-root). Row 0.12 "armed footgun" (`refresh_agent_surfaces.py` without `--check` wipes hooks) still stands as documented. |

Not in the tracker: `G-0-B/FLOSS` has **two** open issues (#28 CI gap matrix, #62 consent integrity test). Every blocker above lives in a markdown file. The corpus audit's "no closing mechanism with teeth" is structurally true: there is no queue to close.

---

## 5. Orientation drift — measured

This is the recurring named defect from the 08-30 delta. It has widened, and it is now on **two branches**, which doubles the correction cost.

| Surface | Says | Is | Severity |
|---|---|---|---|
| `docs/adr/INDEX.md` (#41, "v2.2.0, Updated 2026-07-16") | ADR-1, ADR-2, ADR-9 **Accepted** | Files say **PROPOSED** (`ADR-1:5,179`, `ADR-2:4`, `ADR-9`) | misleading |
| same | ADR-15 Truth Status **Specified** | File header: ✅ **Verified** (R2–R4 unit-tested) | stale |
| same | ADR-19 "Stage 3.5 equivalence run pending" | File: Stages 0–3.5 done, run closed 2026-07-26 | stale |
| same | scope line "post-suite additions (ADR-12..18)" | Has ADR-19 and ADR-20 rows | stale |
| `docs/adr/INDEX.md` (`main`, v2.1.0) | 19 rows, stops at ADR-17, links `ADR-MCP-ORCHESTRATOR.md` | #41 renamed it to `ADR-10-local-agent-node.md` | stale |
| `CLAUDE.md` (#41) | `packages/` = metacoordinator_mcp, orchestrator, source_chain, **memory** | `memory/` does not exist; `activity_log`, `reasoning_ensemble`, `tests`, `mcp_daemon.py`, `omniroute_client.py` unlisted; no port `20128` anywhere | misleading |
| same | "ADR-0..6", "31 files" in `docs/architecture/` | 22 ADR files; 45 architecture files | stale |
| same | "Mandatory `st` Smart Tree" | `st` not installed in this environment | misleading |
| `CLAUDE.md` (`main`) | Kernel v1.3.1; Radicle canonical; Fable "pulled back" | #41: kernel v1.4.0; GitHub now / Radicle target; Fable "RESTORED 07-03 via Pioneer.ai" | misleading on `main` |
| `FLOSSI0ULLK_Master_Metaprompt_v1_4_0_Kernel.md` (#41) | heading v1.4.0, YAML 1.4.0 | Changelog stops at v1.3.2; `rollback_plan` says "Revert to v1.2.0"; **17 non-archive files** still cite v1.3.1 in prose (ADR-3 ×8, the Suite, MVP_PLAN, a test) | stale |
| `shared-context-surface.json` | routes `serena-memory` → `.serena/project.yml` | Serena removed `4657bda` (08-11); `.serena/project.yml` **resurrected by a main-merge**; `project.local.yml` added 08-24; `.serena/memories` empty; no generation timestamp; points to `.agent-surface/context/CONTEXT_L0.md` which is untracked and absent | misleading |
| `docs/research/2026-05-15-working-todo-list.md` §0 (the "live" work board) | refreshed 2026-08-21 | **142 commits since**; `main`'s copy is from 07-03 | misleading |
| `docs/agent-memory/project/heartbeat-running.md` | "As of 2026-05-19, STOP is present… Do not remove" | STOP removed 2026-05-26 per 08-30 delta | stale, actively misleading |
| `docs/agent-memory/CHATGPT_MEMORY_EXPORT.md` vs `MEMORY.md` | (assumed byte-identical) | Differ by one line — a near-duplicate that has **started drifting** | stale |
| `ARF/ADR-0-recognition-protocol.md` | — | Duplicates `docs/adr/ADR-0…` | stale |
| `scripts/triage_review_queue.py` | — | 27-line deprecated shim still tracked | cosmetic |
| `docs/research/_write_agorai_deepdive.py` | — | still tracked, still 0 bytes | cosmetic |
| `__pycache__` / `.pyc` | — | none tracked (fixed in `c563af9`) | ✅ |
| `ARF/Cargo.toml` zome set | 4 members, hdi 0.7.1 / hdk 0.6.1 | matches | ✅ |

### 5.1 Internal contradictions (documents vs documents, documents vs code)

- **Tryorama.** `CLAUDE.md` (both branches): "hApp/Tryorama integration tests pass." `MVP_PLAN.md`, ADR-12, `tryorama-tooling-gap-2026-05-26.md`: they cannot run. `consent-gate-substrate-loop.md` records a 2/2 pass on 2026-05-19, seven days *before* the gap was recorded — plausible as a one-time historical pass on an older toolchain, but stated as if current.
- **Migration path.** `MVP_PLAN.md` and `holochain-0-7-migration-pending.md`: migrate to 0.7 so Tryorama pairs. ADR-12: port to Sweettest first, Tryorama retired.
- **Source chain.** `CLAUDE.md`: mirrors Holochain Cell structure "1:1". `packages/source_chain/cell.py` docstring (corrected in `aee4745`): identifiers do not carry across and need remapping.
- **Dead voter.** `heartbeat-running.md` runs synthesis on `groq/llama-3.3-70b-versatile`; `omniroute-voter-probe-log.md` records it returning 404.
- **ADR-19 evidence.** Its "Verified" equivalence rests on a run that included `groq-qwen3-32b`; the probe log says the default roster built on that model was two Groq voters and failed the independence bar. ADR-19 Decision §3 says litellm stays default; its Evidence section says `FLOSS_MODEL_BACKEND=omniroute` is live.
- **Seam packet stale on itself.** Lists the Codex label (§6) and `synthesizer.py:511` (§7) as unfixed; both are fixed at `aee4745`. Lists four live threads; the learnings doc says two.
- **Anchor spec** self-contradiction on whether the tier-2 review happened (§4 row 4).

---

## 6. Truth-status vocabulary — resolving corpus finding R2

The corpus audit counted four vocabularies and recommended canonicalising. Measured in-repo usage settles which one:

| Vocabulary | Declared where | Header usage on #41 |
|---|---|---|
| **Verified / Specified / Aspirational / Unverified** | ADR Suite v2.0 (`:111, :886`), uop-v2.1, Architecture Spec v0.1 — declared canonical | **37 Specified, 21 Verified, 3 Unverified** |
| same + Blocked (+ Unknown) | manual-review-protocol v1.0, orient skill | partial |
| Hypothesis / Speculative / Working / Robust / Validated | `ARF/dev/specs/EPISTEMIC_TAG_SCHEMA_v0.1.md` | **0** — cited only by its own three sibling files in `ARF/dev` |
| Verified / Specified / Research / Aspirational | (PR38 handoff, per corpus audit) | 0 |
| observed / reproduced / inferred / … | memory packs | 0 as a label system |
| Validated / Accepted / Proposed / Draft | ADR-0, ADR-0.1 use "Validated" as a *decision* status | yes — and this blurs decision status with truth status |

**Verdict:** the canonical set already exists and is already used. The fix is not to design a mapping; it is to (a) add `Blocked` to the Suite's declaration so the two dialects become one, (b) state that Accepted/Proposed is a *decision* axis orthogonal to truth status and stop using "Validated" on that axis, and (c) demote the `ARF/dev` five-level schema (see §8). ADR-20's "evidence vocabulary" (`extracted / inferred / verified / binary`) is a third orthogonal axis — provenance of a *row*, not truth of a *claim* — and should be named as such wherever it appears.

---

## 7. Decisions that need the human operator

Nothing below can be done silently by an agent under the repo's own rules (ADR-5, ADR-12, the supplement §12/§15, the pack §2).

1. **Ruleset.** Either use `--admin` bypass per PR, or remove `copilot_code_review` from `safety rulez` (id `9980168`). Until one of these happens, every other item in this document is branch-local.
2. **Merge order.** `#61 → #43 (+#59 folded locally) → #41 → feat/coordination-room-rebased`. The only predicted conflict is `docs/specs/spec-registry.json`. Merge #64 (retire Tryorama) *after* #61 lands, not before.
3. **Supabase anon key.** Rotate in the Supabase project first (blob persists until 2035 otherwise). Then decide: purge history (`git filter-repo`, force-push to `G-0-B` and `kalisam`, which rewrites the #41/#43 heads) or rotate-and-accept. Rotation is P0; purge is optional after rotation. Also `git rm --cached` the two `.env` files and add `.hermes/`, `opencode.jsonc` to `.gitignore`.
4. **Out-of-repo secrets.** `ow_mcp_at_…`, the six provider keys, `FILE_INVENTORY.tsv` — rotate-only, no purge needed, cannot be done from a repo clone.
5. **Consent-gate design.** What `decision_action_hash` points to. This unblocks ADR-12 promotion and ADR-19 ratification. Also: keep or remap the 2026-09-01 `consent_ref` SHA-256 digest, and either create or de-cite `2026-09-06-consent-anchor-lane-a-probe.md`.
6. **Anchor publication.** Push a tag carrier to the public remote; add `opentimestamps` as a declared dependency; decide whether two genesis anchors should be chained or one retired.
7. **Declined findings.** The Hermes V4A parser (declined for lack of reviewer) and the PowerShell `UNKNOWN` refusal the author disagreed with (`docs/reviews/2026-09-05-pr41-fix-sweep/PACKET.md`).

---

## 8. This session's own prior work, re-graded

This session (2025-11-16) authored `ARF/dev/specs/PLAN_DNA_SPECIFICATION_v0.1.md`, `EPISTEMIC_TAG_SCHEMA_v0.1.md`, `METALOOP_v0.1_IMPLEMENTATION_ROADMAP.md`, a critique, and a distillation, and pushed them to `kalisam/FLOSS`. They are now on `main` and #41. Honest status after ten months:

- **Adoption: zero.** The five-level epistemic schema is cited by nothing outside its own directory (§6). "MetaLoop" appears in `docs/ARCHITECTURE.md:33` as **L4 Meta-Learning — Aspirational**, in `HOLISTIC_ARCHITECTURE.md:161` as the optimization harness, and in `v4-kernel-landed.md:54` as a scope to relate to CCES. No Plan DNA was scaffolded. No `arf plan` CLI exists.
- **It is part of the R2 problem.** The corpus audit's vocabulary fork includes a set this session invented. Under the repo's own reuse gate (ADR-18, supplement §12), a fifth status vocabulary should not have been introduced without first identifying the Suite's four-label set as the existing owner of the concern.
- **What actually got built instead** fills the same role with different names: `docs/reviews/` multi-model review records, the manual-review-protocol v1.0 Lane A/B/C structure, `review_independence.py`, ADR-18's reuse gate, ADR-20's evidence vocabulary. The Plan DNA's `Critique` entry type is, functionally, a `docs/reviews/<date>/a1.json`. The `Distillation` type is a `docs/research/*-learnings.md`. The governance did land — as files and protocol, not as a Holochain DNA.
- **Disposition.** Treat `PLAN_DNA_SPECIFICATION_v0.1.md` and the roadmap as **Aspirational** research intake, correctly located under `ARF/dev/`. Do not build the DNA. Retire `EPISTEMIC_TAG_SCHEMA_v0.1.md` in favour of the Suite's four-label set, or reframe it explicitly as a *confidence-calibration* annex to that set rather than a competing vocabulary. Move the `META_REFLEXIVE_PLANNING_ANALYSIS.md` (already in `docs/research/`) and the distillation into `archive/` when the next consolidation runs — they describe a 2025-11 state.

The meta-principle this session opened with — "forever expanding the meta" — is precisely the failure mode the recurring-principles document names as *conceptual inventory debt*: abstractions generated faster than they are retired. The repo's 2026 work is the better version of the idea: it expands the meta by *recording reviews* and *falsifying its own conclusions* (round 43), not by designing new entry types.

---

## 9. Guidance for the next agent

1. **Start from PR #41's head, not `main`,** until §7.1/7.2 land. `main` is July. Verify with `git log -1 --format=%ci`.
2. **Do not trust `docs/adr/INDEX.md` for ADR status.** Read each ADR's own header. Three "Accepted" rows are PROPOSED files.
3. **Do not trust `CLAUDE.md`'s directory map on either branch.** `ls packages/` instead. There is no `packages/memory`.
4. **The work board is 142 commits stale.** Do not read §0 as current.
5. **`_AUDIT_SINK` and `$PID` are fixed on #41.** Do not re-fix them. Do note they are still broken on `main`.
6. **The only in-repo credential is the Supabase anon JWT.** Do not go looking for `ow_mcp_at_` in the repo; it is not there.
7. **The required Python gate is green (1052).** The 69 advisory failures are ~3 root causes, dominated by the known `MultiScaleEmbedding` mismatch. Fixing that one API reconciliation would clear roughly two-thirds of them.
8. **Prefer reconciliation over construction,** exactly as the 08-30 delta said. Every new surface added since then (`.anchors/`, `docs/reviews/`, `skill-corpus/`) is more capability with less orientation. The ratio is now 2.2:1 markdown to code.
9. **Do not add a fifth truth-status vocabulary.** Use Verified / Specified / Aspirational / Unverified (+ Blocked).
10. **Do not run `refresh_agent_surfaces.py` without `--check`** (unchanged from 08-30).

---

## 10. Method and limits

**Commands (all read-only):**
- `git fetch gob main reconcile/pr38-salvage-20260817 feat/preservation-spine-standalone`; worktrees at `/home/user/pr41`, `/home/user/pr43`, `/home/user/mainwt`.
- `git rev-list --count gob/main..<branch>`; `git diff --shortstat / --numstat gob/main...<branch>`; `comm -12` on touched-file lists for the #41/#43 overlap.
- Secrets: Python scan over every blob from `git rev-list --all --objects` (629 commits) for `sk-`, `sk-ant-`, `gsk_`, `AIza`, `ghp_`, `github_pat_`, `xox`, `eyJhbGciOi`, `ow_mcp_at_`, `-----BEGIN .*PRIVATE KEY`, `csk-`, `api_key\s*[:=]`. Five hits, one real (§1). Script and redacted output in the session scratchpad, not committed.
- Tests: `uv venv -p python3.13`; `uv pip install -r requirements-ci.txt`; the exact CI green-set command from `.github/workflows/python-ci.yml`; full suite with `ARF/requirements.txt` + CPU torch; `cargo test -p rose_forest_integrity -p consent_integrity -p rose_forest -p consent`; `cargo fmt --all -- --check`. Deviations from CI: `uv pip` not `pip`; `-p no:cacheprovider`.
- GitHub: `list_pull_requests`, `list_issues`, `search_repositories` on both repos.

**Not verified:** anything at the workspace root (`C:\~shit\`) — heartbeat state, `.agent-surface/`, `opencode.jsonc`, `.hermes/`, the atlas, the six live services and their ports. The wasm32 `cargo check`. Whether the Tryorama tests would pass on a compatible toolchain. The Supabase project's RLS posture (which determines whether the anon key is actually dangerous). Whether the "94 commits" single-machine figure was ever accurate.

**Anti-sycophancy record:** this document downgrades two of the 08-30 delta's P1s to *fixed*, reclassifies three of the corpus audit's P0s as *out-of-repo*, and re-grades this session's own 2025-11 output from "specified, ready for implementation" to *Aspirational, unadopted, and a contributor to the vocabulary fork it now criticises*.

---

**Provenance:** authored 2026-09-25 in session `014eqDXY8HcJxqNfejD8zK37`, branch `claude/meta-reflexive-planning-014eqDXY8HcJxqNfejD8zK37` on `kalisam/FLOSS` (fork). Inputs: five uploaded documents dated 2026-08-30 → 2026-09-13; live GitHub state; heads `138f342`, `aee4745`, `2ab47c1`. Truth status of this document: **Specified** (observations are from live reads; no claim here has yet been independently re-verified by a second agent).
