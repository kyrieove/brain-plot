# Evidence-based recommendations for Claude orchestrate

Date: 2026-10-05
Audience: Claude, for discussion with the user.
Scope: general-purpose task orchestration, including code, research, analysis and batch work.

This is a recommendation memo, not an execution card. It does not authorize changing the skill, installing frameworks, dispatching agents, changing model preferences, committing or pushing.

## Assessment and evidence boundary

The highest-value additions are independently recorded acceptance evidence, durable orchestration state, and execution limits. Adopt these mechanisms incrementally while retaining the current lightweight workflow.

I inspected the current local `SKILL.md`, `ledger.mjs` and `cost.mjs`. I did not exercise live executors or inspect every external hook and launcher. Accordingly, "not specified" below means absent from these inspected files, not proof that the entire environment lacks that capability. The older `research/astra-review-orchestrate.md` targets an earlier Python implementation; its findings are not treated as current defects.

Local references:

- [Current skill](C:/Users/ASUS/.claude/skills/orchestrate/SKILL.md): modes; Review; Flow; Commands.
- [Ledger](C:/Users/ASUS/.claude/skills/orchestrate/ledger.mjs): per-stream executor/reviewer token accounting.
- [Cost analysis](C:/Users/ASUS/.claude/skills/orchestrate/cost.mjs): retrospective Claude transcript accounting.

SHA-256 at inspection, so Claude can detect changes since this memo:

| File | SHA-256 |
|---|---|
| SKILL.md | FBC914193118E43BB45EBA655E9D9EDA26C571E8D22105749C414BAD2F888D71 |
| ledger.mjs | 5B5ABE09D5CA2649E4CCCA6E63F3833E0C775E5E9EE893E1396371682647918F |
| cost.mjs | 0EAA0B21B6B5B62955C1538ED9A29A7311D4F3B8D30482165D969417F6383D84 |

## Existing mechanisms to preserve

The skill already provides detailed cards, small-job direct execution, explicit executor preferences, risk-tiered review, fresh/read-only review sessions, independent recomputation for consequential numbers, primary-source checks for decision-critical lookup claims, bounded fix rounds, resumable long computations, and cost/findings ledgers.

It also separates long computation from model waiting and avoids heartbeat turns. These are already implemented as policy; they should not be presented as new ideas borrowed from another project.

Respect the user's fixed modes and fallback approval rules. Keep `review pending` distinct from completed review. Retain the policy of never reverting user changes automatically. A framework's feature list or star count does not establish that replacing this workflow would improve cost or reliability.

## 1. Highest priority: mechanically validate evidence before acceptance

**Local evidence.** Review layer 1 delegates Check to the executor. Flow step 3 records `git status --short`; step 5 compares touched files. The executor's requested reply is free text. The review verdict has a prescribed first line, but no structured executor result or external Check receipt is specified. Fix handling explicitly avoids a second conformance review.

**Technical basis.** `git status --short` records status and paths, not a recoverable content baseline. A previously modified file can remain `M` after additional edits. The list cannot identify those additional changes. This follows from the [official Git status format](https://git-scm.com/docs/git-status#_short_format); it is a semantic limitation, not a failure reproduced against your current workflow.

**External mechanism.** CrewAI exposes structured task outputs and function-based guardrails that validate output before downstream tasks receive it. These are useful precedents for deterministic handoff checks; they are not evidence that CrewAI guarantees task correctness. [CrewAI Tasks](https://docs.crewai.com/v1.15.23/en/concepts/tasks#task-guardrails).

**Proposed adaptation.**

- Capture an immutable card/check specification and a task-start content baseline. Preserve existing dirty files' contents and track newly created files explicitly. Store runtime snapshots outside the project; avoid copying large datasets unnecessarily.
- Have a small non-LLM launcher run the card's Check and record command, working directory, relevant parameters, exit status and output. Avoid running the same expensive Check twice: choose one owner for its execution. Protect the validation specification from executor modification; a successful exit alone is still insufficient if the task's goal is not covered.
- Require an executor result with `done`, `blocked` or `failed`, artifact paths and unresolved work. The launcher verifies evidence; it must not turn the executor's self-reported status into proof.
- Associate review and acceptance with a digest of the actual artifacts/change manifest. A later modification makes that evidence stale. Verify the final version after fixes using the smallest relevant check and targeted inspection. This proposal does not require a new full-model review after every fix or silently override the user's existing review policy.
- Distinguish prevented writes from detected writes. Snapshots detect changes afterward; actual read-only guarantees require filesystem or sandbox enforcement. An isolated worktree alone is not a security boundary.

**General-task acceptance examples.** Code: expected behavior and final changes; lookup: key claim plus primary-source location; batch work: expected output inventory and saved parameters; external action: the service's operation receipt and resulting state. Use the existing project-specific checks rather than inventing a universal score.

**Verification for a future implementation.** A dirty file is changed again; an untracked artifact is omitted; a blocked executor exits zero; Check fails despite a success claim; or an artifact changes after PASS. Each case must prevent stale or unsupported acceptance and preserve the user's prior work.

## 2. High priority: persist the orchestration stage, not only computation checkpoints

**Local evidence.** The skill already requires checkpoint/resume for long scripts. However, no durable record of orchestration stages is specified. Agent streams use task-name paths; first dispatch clears same-name streams, and reruns require saving ledger rows beforehand. Review-pending work is recorded in prose.

**External mechanism.** LangGraph separates thread-scoped state checkpoints from longer-term stores. Persistent checkpoints support interruption recovery; its documentation explicitly distinguishes persistent storage from in-memory state lost on restart. [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence).

**Proposed adaptation.** Maintain a small persistent record per invocation with a unique `run_id`, card digest, baseline identity, stage, actual executor/model/session, artifact digest, Check receipt and review status. Use run-specific streams rather than relying on display names for identity. Atomically save completed stages.

Resume only the missing stage after checking that its inputs still match. For example, executor and Check complete plus reviewer quota failure should restore as `review_pending`, not repeat execution. Record an interrupted or uncertain stage explicitly. Do not blindly replay a commit, upload or other external side effect merely because a stage lacks a completion marker; reconcile the actual result first.

A JSON record is a plausible first implementation. A database or LangGraph migration is not required by this recommendation. Reuse current checkpoint and ledger conventions where possible.

**Verification.** Interrupt after execution, after Check and during review. Recovery must retain receipts and usage, avoid repeating completed work, reject incompatible card/artifact changes, and never print a previous invocation's PASS as the current result.

## 3. High priority: add execution limits alongside retrospective accounting

**Local evidence.** The skill reports substantial token consumption from underspecified execution and model waiting. These are observations recorded in the skill, not measurements independently reproduced here. `ledger.mjs` and `cost.mjs` analyze recorded streams/transcripts; neither provides an active cost stop. Commands specify a background timeout, but no per-card token limit or task-wide budget is specified.

**External mechanism.** DeerFlow's inspected configuration defines time, turn, token and total-delegation limits, including per-agent overrides. The useful precedent is that limits are execution configuration rather than instructions the model must remember. Its default numerical limits should not be copied. [DeerFlow subagent configuration](https://github.com/bytedance/deer-flow/blob/main/backend/packages/harness/deerflow/config/subagents_config.py).

**Proposed adaptation.** Select per-card time and resource limits from observed comparable jobs. Enforce supported limits in the launcher; record consumption and checkpoint on limit exhaustion. Preserve fixed executor choices and request the already-required approval before fallback.

Determine when each CLI emits usage before promising an active token ceiling. The current ledger reads completion/result events; if usage arrives only at completion, that stream cannot enforce a precise mid-run token ceiling. In that case use an honest time/turn bound and retrospective token accounting, or a provider-supported budget. A stopped run also needs controlled process-tree termination before it is considered inactive.

Preserve zero-model-token monitoring: ordinary code can observe exit/process/checkpoint signals. An unchanged progress line alone does not prove a stalled computation, so inactivity limits must reflect the task's actual checkpoint cadence.

**Verification.** Exercise timeout and cancellation, including a descendant process. Confirm that work stops, state remains recoverable, the outcome is `budget_exhausted` or `interrupted`, and no heartbeat turns are introduced. Report measured budget overshoot where usage is delayed.

## 4. Medium priority: extend context isolation to the coordinating Claude

**Local evidence.** Cards already reduce executor exploration, and recon can be delegated read-only. The cost helper analyzes repeated Claude context reads, but no explicit checkpoint for starting a fresh coordinating session is specified. The expected savings from a fresh session have not been measured here.

**External mechanism.** DeerFlow distinguishes isolated delegation from a parent-context snapshot and documents the latter's extra input-token cost. Its lead delegates scoped work only when there is a concrete benefit. [DeerFlow Sub-Agents](https://github.com/bytedance/deer-flow#sub-agents).

**Proposed adaptation.** At a completed task boundary, prepare a compact handoff containing the user's constraints and authorizations, current card/state, decisions, unresolved issues and evidence paths. Permit a fresh Claude session to accept/recover from those materials. Summaries must retain provenance and identify unknowns. Do not discard requirements just to shrink the context.

Use this selectively for long sessions; another handoff on every small task could cost more than it saves.

**Verification.** Compare matched task sequences with and without the handoff. Measure coordinating-Claude usage, total usage, missing requirements and recovery quality. Do not treat the cost helper's counterfactual cache cap as a measured saving: rebuilding context and changed behavior also have costs.

## 5. Later: bounded parallelism and stronger evidence for executor routing

**Local evidence.** The flow defines one task per card but no dependency/resource model for concurrent cards. The ledger already records cost and review findings, and the skill says to revise routing after 10-15 cards. Those foundations should be extended, not replaced.

**External mechanism.** DeerFlow explicitly avoids parallel dispatch for interdependent scopes and overlapping side effects, and asks the lead to use the fewest useful workers. This supports selective concurrency, not automatic fan-out. [DeerFlow Sub-Agents](https://github.com/bytedance/deer-flow#sub-agents).

**Proposed adaptation.** When parallel work has clear latency benefit, declare dependencies and overlapping resources. Separate write paths do not establish independence: shared inputs, environments, caches and external services can still conflict. Independent read-only lookups are a simpler starting point than concurrent repository writers.

For routing evidence, group ledger rows by task family and comparable complexity. Include planning, review and fixes in total cost; report completion, accepted quality, later misses and elapsed time. The skill's sol Cartool-port observation versus a typical agy card is not a controlled comparison. It motivates measurement but cannot establish a universal cost ratio.

**Verification.** A task whose prerequisite is incomplete must wait; tasks sharing a writable resource must not overlap. Evaluate routing changes on comparable cards while preserving the user's chosen modes and model permissions.

## Suggested review order for Claude

First check whether existing hooks already provide any proposed mechanism. Then discuss recommendation 1 as the smallest reliability improvement; add stage recovery and execution limits next. Treat context handoffs and parallel dispatch as conditional optimizations requiring measurement.

For each proposed change, classify it as already present, useful now, useful later, or unsupported. Identify the smallest change to the current skill/helpers, its verification case and added token/runtime cost before proposing an execution card. Keep the user's general-purpose scope; do not turn this into a writing-specific workflow.
