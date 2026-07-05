_v1.3 | updated by: family references genericized (per-family via agents family init) | 2026-07-01_

# Generic workflow — work pipeline

Canonical order of commands and agents, from "I open the project" to "deliverable shipped".
Generic: applies to every project with `.claude/`. The runtime-evaluation phases use the
FAMILY agents (`~/.claude/families/<family>/agents.md`, generated per project with
`agents family init`); the code phases use the global generics and the project-specific ones.
A project can have a LOCAL `workflow.md` that overrides/extends this one (see bottom). The
phases below use an RL/training run as the worked example; adapt the run/build steps to your domain.

Agent-level legend:
- **G** = global generics (coding): Code Implementer · Code Reviewer · Integration Validator → `agents code [task]`
- **F** = family (runtime evaluation): the family's monitor/eval/tune agents → `agents monitor` · `agents eval` · `agents tune` · `agents family`
- **P** = project-specific (static audit): in `.claude/agents.md` → `agents [name]` · `agents full`

---

## PHASE 0 — Opening the project (automatic)
1. `resume` (or automatic) → Level 0: reads `handoff.md` + `memory.md` + local `CLAUDE.md`.
2. Responds with status, next step, open issues.
3. (opt.) `status` → quick dashboard · `context` → what I know now · `onboard` → if you return from a long break.
→ Do NOT load other files until you know what to do (lazy loading Level 1/2).

## PHASE 1 — Deciding what to do
- Non-trivial change → `design [feature]` → doc in `assets/` with rationale, options, files to touch. **Wait for approval.**
- Multi-session objective → `plan [objective]` → step-by-step plan in `assets/`.
- Doubt about the why of past choices → `why [what]` / `log [topic]` (reads `decisions_log.md`).
- Global↔local rule conflicts → `sync`.

## PHASE 2 — Implementing the code
1. `agents code [task]` → **G**: Implementer writes → Reviewer classifies 🔴/🟡/🟢 →
   if 🔴 back to Implementer (max 3 iter) → Integration Validator → updates `memory.md`.
2. After changes to domain files → targeted **P** agents:
   - you touch scene/asset/reset → `agents [project's scene-auditor]`
   - you touch reward/obs/control → `agents [project's reward-auditor]`
   - you touch PPO cfg/obs space/export → `agents [project's onnx/integration-auditor]`
   - or all of them → `agents full`.
3. Architectural decision taken → goes into `memory.md` (🗂) and into `decisions_log.md` (`adr`/`log`).
4. New bug → `errors.md` right away; important bug fixed → `postmortem`.

## PHASE 3 — Writing the training configs (RL)
1. You modify `*_env_cfg.py` / `agents/*_ppo_cfg.py` → they are PROTECTED: **ask for confirmation** (they impact obs/action space).
2. After modifying the cfg → integration **P** agent (`agents full` or the onnx-auditor):
   verifies obs_space env↔cfg aligned, correct CNN flatten, share_cnn_encoders, etc.
3. Scene sanity before launching: visual check with a few GUI envs (command in local `CLAUDE.md`, e.g. `random_agent.py --num_envs=4`).
4. Decide a safe `num_envs` (see `errors.md`/`CLAUDE.md` for the project's OOM limits).

## PHASE 4 — Launching the training
1. Launch in background (project script, e.g. `train.sh --num_envs=N`).
2. Note the run timestamp in `memory.md` (🔄 In progress).

## PHASE 5 — Supervising the training (DURING) — **F** agent
- `agents monitor` → `training-monitor`: reads the tfevents of the active run, computes
  reward trend / plateau / action_std collapse / LR floor / value loss / ETA.
- VERDICT: ✅ continue · ⚠️ plateau, evaluate at end of run · ❌ stop and fix (with action: e.g. ↑entropy_coef).
- If ❌ → back to PHASE 3 (reshape reward / hyperparameters), relaunch.
- Repeat `agents monitor` at intervals or at end of run.

## PHASE 6 — Evaluating and correcting the policy (AFTER) — **F** agent
1. `agents eval` → `policy-evaluator`: runs play.py, measures success_rate / collision_rate /
   timeout / time-to-goal / smoothness over many episodes.
   - VERDICT: ✅ ready for export · ⚠️ usable but [limit] · ❌ not ready.
2. If ⚠️/❌ → `agents tune` → `policy-tuner`: takes the diagnosis from monitor+eval and produces the
   PRESCRIPTION — precise edits (file, param, current→proposed, rationale, risk), ordered by
   priority, + recommended run (from scratch / resume). It can APPLY the edits under supervision:
   shows the diff and asks for confirmation on PROTECTED files before writing.
3. Once the edits are applied (after ok) → new run (PHASE 4). For non-config refactoring → `agents code`.
4. If ✅ → jump to PHASE 7 (export).
- (`agents family` = monitor → eval → tune in sequence: eval only if the run is finished,
  tune only if there are problems to correct.)

## PHASE 7 — Export and integration
1. Pre-export → integration **P** agent (onnx-auditor): dual-input ONNX, no double
   normalization, grid format sim↔real, compatible checkpoint.
2. Export (play.py → `exported/policy.onnx`).
3. External consumer (e.g. Nav2/ROS2 plugin) = separate project, outside this repo.

## PHASE 8 — Closing the session
- Mid-session → `checkpoint` (only `memory.md`).
- End / chat switch → `handoff` (rewrites `handoff.md` + `memory.md`).
- Context emergency (~95%) → `dump` in `assets/`.
- Maintenance: `update` (aligns `.claude/` to the code) · `review` (consistency) · `clean` (old assets) · `agents update` (aligns the P agents to the code).

---

## Context window management (during ALL phases)
40% work · 60% checkpoint + ask before loading files · 80% automatic handoff · 95% dump.
(Single source of truth: section "Trigger automatico handoff" in `~/.claude/CLAUDE.md`.)

## LOCAL workflow (per-project override)
If a project has `.claude/workflow.md`, that takes precedence: it contains the EXACT commands
(real paths, task name, safe num_envs, checkpoint, the project's P agent names) and the
deviations from this generic flow. This global file remains the fallback.
