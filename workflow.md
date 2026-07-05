_v2.0_

# Generic workflow — work pipeline

Canonical order of commands and agents, from "I open the project" to "deliverable shipped".
**Domain-neutral**: applies to any project with `.claude/`. The runtime-evaluation phases use the
FAMILY agents (`~/.claude/families/<family>/agents.md`, generated per project with
`agents family init`) — those carry the domain-specific checklists (they are NOT in this repo).
Any project can add a LOCAL `.claude/workflow.md` that overrides/extends this one with its exact
commands (see bottom).

Terminology used below (map it to your domain):
- **run** = any long-running produced process: a build, a training, a batch/data job, a deploy.
- **artifact** = what the run produces: a binary, a trained model, a dataset, a report.
- **telemetry** = whatever the run emits while running: logs, metrics, progress counters.

Agent-level legend:
- **G** = global generics (coding): Implementer · Reviewer · Integration Validator → `agents code [task]`
- **F** = family (runtime evaluation): the family's monitor/eval/tune agents → `agents monitor` · `agents eval` · `agents tune` · `agents family`
- **P** = project-specific (static audit): in `.claude/agents.md` → `agents [name]` · `agents full`

---

## PHASE 0 — Opening the project (automatic)
1. `resume` (or automatic) → Level 0: reads `handoff.md` + `memory.md` + local `CLAUDE.md`.
2. Responds with status, next step, open issues.
3. (opt.) `status` → quick dashboard · `context` → what I know now · `onboard` → returning after a long break.
→ Do NOT load other files until you know what to do (lazy loading Level 1/2).

## PHASE 1 — Deciding what to do
- Non-trivial change → `design [feature]` → doc in `assets/` with rationale, options, files to touch. **Wait for approval.**
- Multi-session objective → `plan [objective]` → step-by-step plan in `assets/`.
- Doubt about the why of past choices → `why [what]` / `log [topic]` (reads `decisions_log.md`).
- Global↔local rule conflicts → `sync`.

## PHASE 2 — Implementing the code
1. `agents code [task]` → **G**: Implementer writes → Reviewer classifies 🔴/🟡/🟢 →
   if 🔴 back to Implementer (max 3 iter) → Integration Validator → updates `memory.md`.
2. After changes to sensitive areas → the matching **P** agent (the ones `agents init` created for
   THIS project's risk areas), or all of them → `agents full`.
3. Architectural decision taken → goes into `memory.md` (🗂) and into `decisions_log.md` (`adr`/`log`).
4. New bug → `errors.md` right away; important bug fixed → `postmortem`.

## PHASE 3 — Config / protected files
1. Editing files that impact a public contract (interfaces, config that changes I/O shape, registered
   names) → they are **PROTECTED**: **ask for confirmation** before writing, show the diff.
2. After a protected edit → the integration **P** agent verifies the change is internally consistent
   (interfaces aligned, no unintended shape/contract change).
3. Sanity check before launching a run (a quick smoke / dry-run — exact command in the local `CLAUDE.md`).
4. Note any resource limits the project documents (e.g. memory/OOM ceilings) before a heavy run.

## PHASE 4 — Launching the run
1. Launch it (the project's run command). Long unattended GPU/compute runs: block auto-suspend, stay on power.
2. Note the run identifier/timestamp in `memory.md` (🔄 In progress).
   *(House rule option: some projects forbid the assistant from launching runs itself — it provides the
   command and the user launches it. Encode that in the local rules if wanted.)*

## PHASE 5 — Supervising the run (DURING) — **F** agent
- `agents monitor` → the family's monitor: reads the run's telemetry, computes the family's health
  signals (progress trend / plateau / instability / divergence / ETA). It reads telemetry only — safe
  to run while the run is live.
- VERDICT: ✅ continue · ⚠️ plateau, evaluate at the end · ❌ stop and fix (+ concrete action).
- If ❌ → back to PHASE 3 (adjust config/params), relaunch. Repeat `agents monitor` at intervals.

## PHASE 6 — Evaluating & correcting the output (AFTER) — **F** agent
1. `agents eval` → the family's evaluator: exercises the produced artifact and measures the family's
   target quality metrics over a representative sample.
   - VERDICT: ✅ ready for the next step · ⚠️ usable but [limit] · ❌ not ready.
   - Do NOT run a heavy eval while a run is competing for the same resources.
2. If ⚠️/❌ → `agents tune` → the family's tuner: turns the monitor+eval diagnosis into a PRESCRIPTION —
   precise edits (file, param, current→proposed, rationale, risk), ordered by priority, + recommended
   next run. It can APPLY the edits under supervision: shows the diff, asks confirmation on PROTECTED files.
3. Once applied (after ok) → new run (PHASE 4). For non-config refactoring → `agents code`.
4. If ✅ → PHASE 7.
- (`agents family` = monitor → eval → tune in sequence: eval only if the run is finished, tune only if
  there are problems to correct.)

## PHASE 7 — Ship / export / integrate
1. Pre-ship → the integration **P** agent: verifies the artifact meets its external contract
   (interface, format, no double-processing, downstream compatibility).
2. Produce the deliverable.
3. External consumers are separate projects, outside this repo.

## PHASE 8 — Closing the session
- Mid-session → `checkpoint` (only `memory.md`).
- End / chat switch → `handoff` (rewrites `handoff.md` + `memory.md`).
- Context emergency (~95%) → `dump` in `assets/`.
- Maintenance: `update` (aligns `.claude/` to the code) · `review` (consistency) · `clean` (old assets) · `agents update`.

---

## Context window management (during ALL phases)
40% work · 60% checkpoint + ask before loading files · 80% automatic handoff · 95% dump.
(Single source of truth: the auto-handoff section in `~/.claude/CLAUDE.md`.)

## LOCAL workflow (per-project override)
If a project has `.claude/workflow.md`, that takes precedence: it holds the EXACT commands (real
paths, run/build command, resource limits, checkpoint/artifact names, the project's P agent names)
and any deviation from this generic flow. **All domain-specific detail lives there and in the family
agents (`families/<family>/agents.md`) — never in this published, domain-neutral file.**
