_v1.9_

# Global Developer Profile

## Technical identity
- Robotics developer: RL, autonomous navigation, embedded systems
- Recurring project types: Isaac Lab (RL), ROS2/Nav2, CAN bus, STM32
- Language: Italian for documentation, English for code and comments
- **Personal/machine specifics** (identity, hardware, install paths, robot platforms):
  → `~/.claude/profile.local.md` — LOCAL-ONLY, never versioned. **Read it at session start
  if it exists (Level 0)**; if absent (fresh clone), ask the user or learn per-project.

## How I reason
- I want to understand the why before the how — always give the rationale before
  architectural decisions
- I prefer consultable documents over long-term memory
- I'm a growing programmer: don't take for granted that I know
  advanced patterns, explain them the first time you use them
- Complete implementations, not skeletons — if you write a file, finish it

## Universal output preferences
- Technical answers: no useless prose, get to the point
- Visual files (SVG, HTML, diagrams): always in .claude/assets/ snake_case
- Documentation: Italian | Code and variable names: English

## Recurring stacks
| Domain               | Technologies                                    |
|----------------------|-------------------------------------------------|
| RL training          | Isaac Lab, RSL-RL, PPO, ONNX export             |
| Navigation           | ROS2 Humble, Nav2, SLAM Toolbox, AMCL           |
| Hardware interface   | CAN bus, CANopen, STM32, FreeRTOS               |
| Robot platform       | → see profile.local.md (local-only)             |
| Embedded             | No HAL at runtime, only peripheral registers    |

## Standard .claude/ structure
Every project has this structure. Create it with "init", maintain it
with the other commands.

.claude/
├── CLAUDE.md          ← what this project does
├── memory.md          ← live state, updated every session
├── handoff.md         ← snapshot for chat switch / pre-compact
├── errors.md          ← error and workaround log
├── rules.md           ← local overrides of the global rules
├── skills.md          ← what I know how to do on this project and the gaps
├── agents.md          ← project-specific agents (created by "agents init")
├── decisions_log.md   ← architectural decision history (append-only, created by "log"/"adr")
├── plans/             ← multi-session plans and designs (created by "plan"/"design")
└── assets/
    └── .gitkeep

Note: agents.md, decisions_log.md and plans/ are not created by "init" but
on-demand by the respective commands (agents init | log/adr | plan/design).
Custom commands are documented in ~/.claude/commands.md (global, not per-project).

### Two levels of files in .claude/
1. **Reproducible base** (the files above): they exist — or can exist on-demand — in
   EVERY project, regardless of domain. It's the standard that "init"/"update" guarantee.
2. **Project/family-specific extensions**: some projects add domain files
   NOT foreseen by the base template (e.g. an experiment/run registry, a `workflow.md` that wires
   the family-agent commands onto the project's exact commands, artifacts rendered under assets/).
   Rules for these extensions:
   - They are legitimate but **NOT part of the base template** → "init" does NOT create them by default.
   - The global stays AGNOSTIC: never assume they exist, don't hardcode their paths/names here.
   - They are discovered and assigned a reading level by "## Handling non-standard .md files".
   - Their contents (run logs, output paths, metrics, etc.) live ONLY in the project,
     never in the global.

## Behavior rules — apply to ALL projects

### Mandatory reading order (start of every session)
Before answering anything, read in this order:
a. .claude/handoff.md — if it exists and has a recent date
b. .claude/CLAUDE.md local — project context
c. .claude/memory.md — current state
d. ~/.claude/CLAUDE.md global — only if a refresh is needed
Don't answer anything until you've read all three.

### Start of every session
1. Check whether .claude/handoff.md exists
   - If it exists and is recent: read it first, notify me with:
     "📋 Handoff found from [DATE] — resuming from: [next step]"
   - If it doesn't exist: proceed normally without telling me anything
2. If memory.md has a "Next step", confirm to me that you've read it
3. Report inconsistencies between CLAUDE.md and the real code

### During the session
- Architectural decisions → always notify me with ⚠️ DECISION
- Newly discovered bugs → add them immediately to errors.md
- Don't modify CLAUDE.md (local or global) without me asking
- Visual files → .claude/assets/ with snake_case name
- Long unattended GPU runs (training, sim, batch inference): the launch command MUST block
  auto-suspend (`systemd-inhibit --what=sleep:idle:handle-lid-switch --mode=block …`) and the
  machine MUST stay on AC. A suspend with a live CUDA process corrupts the driver context →
  the run hangs (Ctrl+C dead). Symptom: hang at a "random" iteration immune to SIGINT →
  first suspect GPU/driver (check `journalctl -k | grep -iE "suspend|PM:|Xid"`), not the code.
  (agv_local_planner 2026-07-03: 5000-it run died at it501 this way.)

### Automatic memory.md update
Update without waiting for me to ask:
- Feature completed → ✅ Works
- Work started → 🔄 In progress
- Bug found → ❌ Open issues
- Decision made → 🗂 Session decisions

### Handoff — three scenarios

SCENARIO 1 — manual trigger (I write "handoff")
1. Update memory.md
2. Rewrite handoff.md with a complete snapshot
3. Reply to me: "✅ Handoff ready — paste handoff.md into the next chat"

SCENARIO 2 — pre-compacting
1. BEFORE compacting update memory.md
2. BEFORE compacting rewrite handoff.md
3. Add at the top: [PRE-COMPACT — [DATE TIME]]
4. Notify me: "⚠️ Context almost full — handoff.md and memory.md updated"
5. Only then proceed with compacting

SCENARIO 3 — post-compacting
1. Re-read handoff.md and memory.md
2. Notify me: "🔄 Resumed after compacting — I was in: [next step]"

### Default autonomy
Do without asking:
- Refactoring internal to a single file
- Type hints, docstring, formatting
- Updating memory.md / handoff.md / errors.md / skills.md

Ask first before:
- Changing public interfaces (ROS2 topic, observation/action space, API)
- Modifying hardware configurations (CAN timing, PWM, Nav2 parameters)
- Renaming registered tasks, topics or nodes
- Anything that breaks compatibility with external systems

Never do:
- Modify third-party repos (IsaacLab/, official ROS2 packages)
- Assume the code works without having verified it
- Duplicate information already present in the global into local files

## Quick commands — standard pipeline

### "init"
When the project does NOT yet have .claude/
1. Read the project structure recursively
   (use MCP Filesystem if available, otherwise ask for the key files)
2. Read all significant files:
   README.md, setup.py, extension.toml, CMakeLists.txt, package.xml,
   main __init__.py, env.py, cfg.py, main.py — whatever you find
3. If MCP Git available: read the first 20 commits
4. Infer project type and stack
5. Generate the complete .claude/: CLAUDE.md, memory.md, handoff.md,
   errors.md, rules.md, skills.md, assets/.gitkeep
   Every generated file must have the versioning header at the top
   (see "## Versioning of .claude/ files"): _v1.0 | updated by: init | [date time]_
   Do NOT generate agents.md, decisions_log.md, plans/ — those are born
   on-demand by the respective commands.
6. **Detect the FAMILY** of the project (see FAMILY LEVEL): RL/Isaac Lab → `isaac_lab`,
   ROS2/Nav2 → `ros2_nav`, embedded/STM32 → `embedded`, etc.
   - If `~/.claude/families/[family]/agents.md` exists → the family evaluation agents
     are already available (`agents monitor/eval/tune/family`). Note it in the local CLAUDE.md.
   - If it does NOT exist and the family makes sense for the project → suggest "agents family init".
7. **Centaur (local-LLM execution)**: note in the generated CLAUDE.md that agents offload their
   MECHANICAL work to Qwen via the `centaur` MCP (see global "Centaur execution protocol"; judgment
   stays in Opus). Check whether the server is reachable (the `vram_status` tool responds, or
   `~/.claude/centaur/` exists); if not, remind me to register it ONCE (snippet in "Centaur execution
   protocol"). After `init` + `agents init` the project's agents are already wired to Ollama — no
   extra per-project setup, because the fabrication commands embed the Execution stanza.
8. Conclude with:
   "✅ init completed — type: [TYPE] | family: [name | none]
    Family agents: [available | create with 'agents family init']
    Centaur MCP: [reachable | register once — see 'Centaur execution protocol']
    Assumptions: [list]
    Verify manually: [list]"

### "update"
When .claude/ already exists and you want to align it with the current code
1. Read all files in .claude/
2. Read the project's current structure
3. For each .claude/ file find what's missing relative to the code:
   - CLAUDE.md → new key files? changed commands? new constraints?
   - memory.md → in-progress things not recorded?
   - errors.md → known bugs not documented?
   - skills.md → new skills? gaps filled?
   - rules.md → new critical files to protect?
4. Update ONLY the files with real changes
5. Do NOT touch handoff.md
6. Conclude with:
   "✅ update completed
    Updated: [list]
    Unchanged: [list]
    Additions: [concise list]"

### "agents code [task]"
Launch the CYCLE of the 3 generic coding agents (LEVEL 1) on an implementation task.
Applies to ANY project (it's the generic write→review→validate pipeline). When I write
"agents code [task description]":
1. Read the minimal context: .claude/CLAUDE.md, memory.md, skills.md, rules.md.
2. Run the pipeline (full detail in "### LEVEL 1 — Generic coding agents"):
   Code Implementer → Code Reviewer → (if 🔴 go back to Implementer) → Integration Validator.
   Max 3 iterations; if 🔴 remain after the 3rd → stop and ask me how to proceed.
3. Respect the protected files (rules.md / local autonomy): on protected files show the diff
   and ask for confirmation BEFORE writing.
4. At the end update memory.md and conclude with the summary:
   "✅ agents code completed
    Implementer: [N files modified]
    Reviewer: [N issues, N resolved, N remaining]
    Validator: [✅ ok | ⚠️ N issues]
    memory.md updated: yes"
Note: "agents code" = GENERIC coding agents (this command). They are a different thing from the
family EVALUATION agents ("agents monitor/eval/tune/family") and from the project-specific AUDIT
agents ("agents full | agents [name]", created by "agents init").

### "review"
Complete consistency check between .claude/ and the real code
1. Read all .claude/ files and the project code
2. Look for these problems:

   DISCREPANCIES
   - Commands in CLAUDE.md no longer valid or with changed parameters
   - Key files in CLAUDE.md that don't exist in the repo
   - Architectural constraints contradicted by the real code
   - Skills in skills.md marked ✅ but with wrong patterns in the code

   DUPLICATIONS
   - Info present both in the global and in the local
   - Same info in CLAUDE.md and memory.md
   - Errors in errors.md already resolved but still 🔄 open

   GAPS
   - Important files in the repo not mentioned in CLAUDE.md
   - Code behaviors not documented in any .claude/ file
   - Known issues in the code absent from errors.md

3. For each problem: describe it, propose a fix, ask for confirmation
4. Conclude with:
   "✅ review completed
    Problems: [N] (discrepancies: [N] | duplications: [N] | gaps: [N])
    Do you want me to apply all fixes? (yes / selective)"

### "checkpoint"
Lightweight mid-session update of memory.md
1. Update ONLY memory.md with the current state
2. Do NOT touch handoff.md
3. Reply to me: "📍 Checkpoint [TIME] — [state in 10 words]"

### "design [feature]"
Before implementing something non-trivial
1. Read CLAUDE.md and the relevant code
2. Create .claude/assets/design_[feature]_[date].md with:
   - Feature objective in 2-3 lines
   - Implementation options (min 2) with pros/cons
   - Final proposal with rationale
   - Files to create/modify and in what order
   - Risks and dependencies
3. Do NOT start implementing — wait for approval
4. Reply to me: "📐 Design ready in assets/ — do you approve or should I modify it?"

### "plan [objective]"
For big objectives that require multiple sessions
1. Read CLAUDE.md and memory.md
2. Create .claude/assets/plan_[objective]_[date].md with:
   - Clear final objective
   - Steps ordered by dependencies
   - For each step: what it does, input, expected outputs, complexity
   - Global risks of the plan
3. Reply to me: "📋 Plan ready in assets/ — [N] steps"

### "postmortem"
After resolving an important bug
1. Add at the top of errors.md:
   - Date and title
   - Symptom
   - Root cause
   - Applied fix
   - Why we didn't see it right away
   - How to recognize it earlier in the future
2. If relevant, update skills.md
3. Reply to me: "📝 Postmortem added to errors.md"

### "context"
When you want to know what I know at this moment
1. List the .claude/ files read and when
2. List the active assumptions about the code
3. List the applied skills (from skills.md)
4. List what I do NOT know or am unsure about
Format: concise list, no prose

### "onboard"
Operational guide to resume after a long break
1. Read all .claude/ files and the project code
2. Create .claude/assets/onboarding_[date].md with:
   - What the project does in 5 lines
   - How to start it (exact commands)
   - Map of the key files with one line each
   - The 3 main pitfalls (from errors.md + constraints)
   - Current state (from memory.md)
   - First thing to do to get back into the flow
3. Reply to me: "📖 Onboarding ready in assets/"

### "dump"
Emergency — context window almost exhausted
1. Create .claude/assets/context_dump_[YYYY-MM-DD-HH-MM].md with:
   - Files touched and key changes
   - State of variables/tensors/parameters discussed
   - Active assumptions about the code
   - Exact next step to resume
2. Update memory.md
3. Reply to me: "💾 Dump saved in assets/ — you can close the chat"

## Standard skills.md structure

# Skills — [PROJECT NAME]
_What Claude knows how to do on this project and the known gaps._
_Updated by: [init|update|postmortem] on [DATE]_

## ✅ Consolidated skills
| Skill | Source of confidence |
|-------|----------------------|
|       |                      |

## ⚠️ Partial skills
| Skill | Known gap |
|-------|-----------|
|       |           |

## ❌ Absent skills — always ask me
-

## 📈 Progression
- [DATE] [skill] → [from level] to [to level] because [reason]

Rules for populating skills.md:
- Consolidated: inferred from the code you can read
- Partial: depend on specific versions or external integrations
- Absent: physical parameters, real hardware, local configs not readable

## Automatic handoff trigger — context window management

SINGLE SOURCE OF TRUTH for context management. Applies in EVERY
session (even without "resume"). Continuously monitor the length
of the conversation and apply without waiting for me to ask.
The estimate is approximate: better to intervene sooner than later.

~40% used:
→ no action, work normally

~60% used:
→ Notify me: "⚠️ Context at ~60% — I'll avoid new files unless strictly
  necessary. I recommend a checkpoint soon."
→ Run an automatic checkpoint (update memory.md)
→ From here on: always ask for confirmation before loading
  any additional file

~80% used:
→ Run a full automatic handoff without waiting (handoff.md + memory.md)
→ Notify me: "⚠️ Context at 80% — handoff.md and memory.md updated.
  Open a new chat soon."
→ Stop loading new files, use only what's already in memory

~95% used:
→ Run a dump in assets/context_dump_[YYYY-MM-DD-HH-MM].md
→ Notify me: "🚨 Context almost exhausted — dump saved in assets/.
  Open a new chat and write 'resume'."

---

## "resume" command
To be used at the start of a new chat after a handoff.
Strategy: level-based loading — only what's needed,
when it's needed. Never load everything in advance.

════════════════════════════════════════
LEVEL 0 — always, automatic, without asking me
════════════════════════════════════════
Read these 3 files as soon as I start a chat on a project
that has .claude/. Don't wait for me to say "resume".

1. .claude/handoff.md → what we were doing
2. .claude/memory.md → current state and next step
3. .claude/CLAUDE.md local → project context, constraints, commands

After reading them, reply to me with:
"📋 Base context loaded — [PROJECT NAME]
 Handoff from: [DATE]
 Next step: [from the handoff]
 Open problems: [N]
 What are we doing?"

Don't load anything else until I know what you're about to do.

════════════════════════════════════════
LEVEL 1 — load when the task requires it
════════════════════════════════════════
Load these files only at the moment they become
necessary, not before. Precise rules:

ERRORS.MD
Load when:
- You mention a bug or an error
- You're debugging something
- The code doesn't behave as expected
- You're about to touch an area that historically has had problems
Do NOT load for: new features, refactoring, theoretical questions
Note: once loaded, don't reload in the same session

SKILLS.MD
Load when:
- You're about to write new code
- I ask whether I can do something specific
- The task requires technologies not mentioned in CLAUDE.md
Do NOT load for: debug, review, questions about existing code
Note: once loaded, don't reload in the same session

RULES.MD
Load when:
- You're about to modify a file that might be protected
- There's ambiguity about what I can touch
- You're changing public interfaces or config
Do NOT load for: reading code, explanations, planning
Note: once loaded, don't reload in the same session

AGENTS.MD
Load when:
- You write "agents [anything]"
- You're about to start a training session
- You made big changes to env.py or cfg.py
When you load agents.md:
→ also re-read the "Agent system" section in ~/.claude/CLAUDE.md
→ so you have in memory both the 3 generic agents and the 3 specific ones
Do NOT load for: everything else
Note: once loaded, don't reload in the same session

════════════════════════════════════════
LEVEL 2 — load only on explicit request
════════════════════════════════════════
These files are never loaded automatically.
I read them only if I ask you explicitly or if
I write the corresponding command.

~/.claude/CLAUDE.md global
→ only if there's a rule conflict or a project switch
→ don't reload it if it's already been read in this session

.claude/assets/*
→ only if you cite a specific file in assets/
→ load only the cited file, not the whole folder

.claude/handoff.md (re-reading)
→ read automatically only once at the start of the session (Level 0)
→ don't reload during the session even if it gets updated
→ it's written by checkpoint/handoff but not re-read
→ the updated version will be read in the next session

DECISIONS_LOG.MD — Level 2
Load when:
- I write "log" or "log [topic]"
- I write "why [what]"
- I write "adr [decision]"
- You're about to make a decision similar to one already made
- Review finds inconsistencies that might have history
Never load automatically:
- It's append-only and grows over time
- Always loading it wastes context uselessly
Content: append-only history of architectural decisions

ADDITIONAL LEVEL 2 FILES:
[Populated automatically — see "## Handling non-standard .md files"
for the level-assignment rule]

════════════════════════════════════════
LOADING NOTICES
════════════════════════════════════════
Always notify me when you're loading a new file:
"📂 Loading [file] because [reason in 5 words]"

If you estimate that loading a file would push the context
over 50% → notify me first:
"⚠️ Loading [file] would use ~[N] tokens — current
context ~[X]%. Do I proceed?"

Never reload files already read in the same session.
If a file is already in memory use it even if time has passed.

════════════════════════════════════════
CONTEXT WINDOW MANAGEMENT
════════════════════════════════════════
The 40/60/80/95% thresholds are defined in the section
"## Automatic handoff trigger — context window management"
(single source of truth). It applies during resume too:
in particular from ~60% ask for confirmation before loading
the Level 1 files, and from ~80% don't load any more new ones.

════════════════════════════════════════
IF YOU DON'T HAVE MCP FILESYSTEM
════════════════════════════════════════
Without filesystem access (claude.ai browser):
1. After Level 0 notify me:
   "⚠️ No filesystem — paste me:
    1. handoff.md
    2. .claude/CLAUDE.md
    3. memory.md
    For other files I'll ask you only when needed."
2. For each Level 1 file: ask me only when
   the trigger is active, not all in advance
3. Never ask for more than 2 files at a time
4. When you ask for a file always specify why:
   "Can you paste [file]? I need it because [reason]"

---

## Agent system — global architecture

### Structure
Every project has THREE levels of agents:

LEVEL 1 — Generic agents (defined here in the global)
Apply to any coding project. Function: write/review/validate code.
Activation: "agents code [task]"

FAMILY LEVEL — Evaluation agents for a FAMILY of projects
Defined in ~/.claude/families/[family]/agents.md. Function: evaluate runtime,
not read sources. Reusable on any project of the same family.
No family ships preset — generate the current project's family with "agents family init".
Activation: "agents monitor" | "agents eval" | "agents tune" | "agents family"
Creation/update: command "agents family init" | "agents family update"

LEVEL 2 — Specific agents (defined in local .claude/agents.md)
Generated by Claude reading the specific project. Function: static audit of the code.
Activation: "agents [name]" | "agents full"
Creation: command "agents init"
Update: command "agents update"

---

### Centaur execution protocol (HYBRID)
_The generic substrate that lets ANY agent — the 3 generic here, the family agents, the project
agents, AND any agent a future "agents init"/"agents family init" creates — offload its MECHANICAL
work to a local LLM (Qwen via Ollama) while Opus keeps ALL judgment. The bridge lives in
`~/.claude/centaur/` (project-agnostic) and is registered once as the `centaur` MCP server. Model
default `qwen3.6:27b` (configurable in `~/.claude/centaur/config.json`; alt `qwen3-coder:30b`)._

Principle (HYBRID, non-negotiable): **Qwen executes, Opus judges.** Qwen only generates/runs code,
applies syntactic edits, or writes a mini-summary — it NEVER decides which lever, why, or the
🔴/🟡/🟢 classification. The SPEC Opus sends carries the full intent (what to compute/produce, which
file/function/algorithm, often the diff already designed); Qwen is the hands, Opus is the brain.

MCP tools (generic, domain-agnostic — the bridge knows nothing about the calling agent):
- `vram_status()` — resource gate. When a training is alive (or VRAM > 85%) Qwen is forced CPU-only.
- `qwen_codegen_run(spec, interpreter, freeze_path, test_args, run_args, …)` — self-healing
  generate→smoke-test→freeze→run; once frozen (spec-hash match) the script re-runs natively with NO
  LLM. `interpreter` is a parameter (`python3`, `<isaaclab>/isaaclab.sh -p`, …).
- `qwen_edit(file, delta_spec, protected)` — Delta-Only Search&Replace; protected files → diff
  returned, NEVER auto-applied.
- `qwen_summarize(text, instruction)` — mini-summary of verbose output.

Bridge-enforced protocols: A Traffic-Cop (CPU-only when the GPU is busy; `keep_alive:0` in GPU mode
so Qwen never holds VRAM; may hold RAM in CPU mode); B stateless one-shot; C self-healing
(generate→`--test`→≤3 retries feeding back the traceback→freeze→native reuse); D delta-only edits.
⚠️ Safety: MCP tool calls BYPASS Claude's Bash allow/deny, so the bridge re-enforces a denylist
(`train.py`/`train.sh`) + an interpreter allow-list internally.

**Agent stanza template** — every agent (present or fabricated later) carries ONE such line; only
this line varies per agent, the Data/Checklist/Verdict sections stay unchanged and in Opus:
> **Execution (Centaur):** <mechanical step> → dispatch to Qwen via `<tool>` with a spec carrying
> <what to compute/produce>; interpreter=`<python3 | isaaclab.sh -p | …>`; freeze reusable scripts to
> `<path>`; needs_gpu=<yes/no> (if yes → gate on `vram_status`, i.e. not during training). The
> VERDICT stays in Opus. Degrade gracefully if the `centaur` MCP is absent (Opus does the step itself).

---

### LEVEL 1 — Generic coding agents
Activation: "agents code [task description]"

GENERIC AGENT 1 — Code Implementer
Role: write or modify code to complete the task
Reads first: CLAUDE.md, memory.md, skills.md, rules.md
Constraints:
- Never touches the protected files in rules.md
- For each modified file: explains what it changed and why
- If it encounters an unclear architectural constraint → stop with ⚠️
- Complete implementations, no skeletons
- Execution (Centaur): transcribes/writes code from Opus's spec or diff via `qwen_codegen_run`
  (new scripts) / `qwen_edit` (edits). Opus designs substantial logic and any protected-file diff;
  Qwen only executes it. Protected files → `qwen_edit(protected=True)` → diff for confirmation.
Output: code + list of modified files + remaining open questions

GENERIC AGENT 2 — Code Reviewer
Role: find problems in the code produced by the Implementer
Never writes code, only analyzes.
Checks in order:
1. Violations of the architectural constraints in CLAUDE.md
2. Inconsistencies with the existing patterns in the project
3. Public interfaces changed without it being requested
4. Side effects on files not mentioned in the task
5. Unhandled edge cases
6. Duplications with already existing code
Classifies each problem:
🔴 blocking — breaks something or violates a constraint
🟡 important — suboptimal but not blocking
🟢 minor — style, naming, micro-optimizations
Execution (Centaur): mechanical checks (py_compile, grep, run the test suite) may be dispatched to
Qwen via `qwen_codegen_run`; the 🔴/🟡/🟢 classification and every judgment stay in Opus.
Output: list of classified problems, no direct fix

GENERIC AGENT 3 — Integration Validator
Role: verify that the new code integrates correctly
with the rest of the system
Checks:
- Consistency with the reference examples in CLAUDE.md
- Public interfaces not changed except on explicit request
- At least 3 edge case scenarios mentally simulated
- errors.md updated if it finds new bugs
- skills.md updated if it finds gaps filled or new ones
- Execution (Centaur): may dispatch running the checks/tests to Qwen via `qwen_codegen_run`; the
  ✅/❌ integration verdict stays in Opus.
Output: ✅ ok | ❌ [problems] + updates to the .claude/ files

GENERIC AGENTS FLOW:
1. Implementer performs the task
2. Reviewer analyzes
3. If 🔴 found → back to Implementer with the specific problems
4. If only 🟡/🟢 → Integration Validator analyzes
5. If Validator approves → final output + update memory.md
6. If Validator rejects → back to Implementer
Maximum 3 iterations. If after 3 iterations there are still 🔴
stop and ask me how to proceed.

Always conclude with:
"✅ agents code completed
 Implementer: [N files modified]
 Reviewer: [N problems, N resolved, N remaining]
 Validator: [✅ ok | ⚠️ N problems]
 memory.md updated: yes"

---

### FAMILY LEVEL — Evaluation agents (defined per family)
Defined in ~/.claude/families/[family]/agents.md (NOT in the project, NOT in the global).
They auto-configure by reading the local .claude/CLAUDE.md of the current project
(task, log path, constraints). No family ships preset — generate the current project's
family with "agents family init".

Registered command triggers (the concrete checklists live in the generated
~/.claude/families/<family>/agents.md — the family's agents define what each does):
- "agents monitor" → the family's monitoring agent: evaluates a run/process WHILE it runs
  (progress, health, divergence, ETA) → VERDICT continue | plateau, evaluate at end of run | stop and fix (+ action).
- "agents eval" → the family's evaluation agent: measures behavioral/output quality after a run
  → VERDICT ready for the next step/export | usable but [limit] | not ready.
- "agents tune" → the family's tuning agent: takes the diagnosis from monitor+eval and produces the
  PRESCRIPTION — precise edits ordered by priority (file, param, current→proposed, rationale, risk).
  It can APPLY the edits UNDER SUPERVISION: always shows the diff, and on PROTECTED files asks for
  explicit confirmation BEFORE writing.
- "agents family" → runs in sequence monitor → eval → tune (eval only if the run is finished;
  tune only if monitor/eval report problems; if ✅ skip ahead).

When to load ~/.claude/families/<family>/agents.md (Level 1 in resume):
- you write "agents monitor" | "agents eval" | "agents tune" | "agents family"
- you're about to supervise/evaluate/correct a training
Do NOT load for: code writing, debug, planning.

#### "agents family init" command
Generates from scratch the suite of evaluation agents for the FAMILY of the current project,
as "agents init" does for the project-specific agents. When I write "agents family init":
1. **Detect the family** of the current project from the local `.claude/CLAUDE.md` and the stack
   (RL/Isaac Lab+RSL-RL → `isaac_lab`; ROS2/Nav2 → `ros2_nav`; STM32/embedded → `embedded`; etc.).
   If ambiguous → ask me to confirm the family name.
2. If `~/.claude/families/[family]/agents.md` **already exists** → notify me and propose "agents family
   update" instead (don't overwrite for nothing).
3. Identify the **lifecycle evaluation phases** typical of that family
   (for RL: during-training, after-training, next-run-prescription). One agent per phase.
4. For each agent generate, in a **project-agnostic** way (it auto-configures by reading the local
   CLAUDE.md of the project it runs in, does NOT hardcode path/task):
   - Descriptive domain name (e.g. `training-monitor`, `policy-evaluator`, `policy-tuner`).
   - "Auto-configuration" block: what to read from the project to parameterize itself.
   - Which **runtime data** it reads (tfevents/checkpoint/play.py output/log), NOT the sources.
   - Computed 8-15 point checklist (metrics, not "eyeball it").
   - 🔴/🟡/🟢 criteria and Output format with verdict.
   - **Execution (Centaur) stanza** (per the global template): the mechanical read/run step →
     dispatch to Qwen via `qwen_codegen_run`; interpreter, freeze path, needs_gpu (set YES for any
     agent that launches the sim/GPU → it must gate on `vram_status`, i.e. not during training). The
     checklist and verdict stay in Opus.
5. Create `~/.claude/families/[family]/agents.md` with a versioning header and an index table.
6. Register the triggers above (this "Registered commands" section) and in `~/.claude/commands.md`.
7. Conclude with:
   "✅ agents family init completed — family: [name]
    Agents created: [list] | Phases covered: [list]
    Activation: agents [trigger] | agents family
    File created: ~/.claude/families/[name]/agents.md"

Generation rules (analogous to "agents init" but for the RUNTIME, not for the code):
- Family agents EVALUATE the execution, they don't do static audit of the sources (those are the P's).
- Project-agnostic ALWAYS: no hardcoded path/task/num_envs → derived from the project at runtime.
- They cover DIFFERENT and ordered lifecycle phases (diagnosis → prescription), they don't overlap.
- Reusable on EVERY project of the same family (present and future).
- Every generated agent carries an Execution (Centaur) stanza (mechanical work → Qwen via the
  `centaur` MCP, judgment → Opus) → the family's agents are auto-connected to Ollama.

#### "agents family update" command
When I write "agents family update":
1. Detect the family (as above) and re-read `~/.claude/families/[family]/agents.md`.
2. Add agents for lifecycle phases not yet covered; update checklists with
   new metrics/tools; remove checks on tools no longer used by the family.
3. Keep the auto-configuration project-agnostic.
4. Add/refresh the Execution (Centaur) stanza on any agent missing it (per the global template).
5. Conclude with: "✅ agents family [name] updated — [N] agents, [N] checks added/removed"

---

### LEVEL 2 — Specific agents (automatic generation)

#### "agents init" command
When I write "agents init":
1. Read .claude/CLAUDE.md, skills.md, errors.md and the main code
2. Identify the 3 most critical risk areas for THIS project
3. For each area create a specialized agent with:
   - Descriptive name specific to the domain
   - List of files to read (real project paths)
   - Checklist of 10-15 points specific to that area
   - 🔴/🟡/🟢 criteria calibrated on the project
   - Output format with metrics relevant to that domain
   - **Execution (Centaur) stanza** (per the global "Centaur execution protocol" template): the
     mechanical step (grep line numbers / dump a function body / run a check) → dispatch to Qwen via
     `qwen_codegen_run` (or `qwen_edit` for edits); interpreter, freeze path, needs_gpu. The
     🔴/🟡/🟢 classification and verdict ALWAYS stay in Opus.
4. Create .claude/agents.md with the 3 generated agents
5. Add the "agents full" command that runs them in sequence
6. Update .claude/rules.md adding the new commands
7. Conclude with:
   "✅ agents init completed
    Agents created: [name1] | [name2] | [name3]
    Areas covered: [list]
    Activation: agents full | agents [single name]
    File created: .claude/agents.md"

Rules for the generation:
- The 3 agents cover DIFFERENT and non-overlapping areas
- Checklists specific to the real code, not generic
- Use real names of files, classes and functions of the project
- Agent 1: foundations (setup, init, structure)
- Agent 2: core logic (algorithm, reward, control loop)
- Agent 3: external integration (export, interfaces, external systems)
- Each agent runs independently of the others
- Every generated agent carries an Execution (Centaur) stanza → its mechanical work runs on Qwen via
  the `centaur` MCP, judgment stays in Opus. This is what makes NEW agents auto-connected to Ollama
  without touching the bridge (see "Centaur execution protocol").

#### "agents update" command
When I write "agents update":
1. Re-read .claude/agents.md and the current code
2. Update checklists with new files or functions added
3. Remove checks on files that no longer exist
4. Add checks for error patterns found in errors.md
5. Ensure every agent carries an Execution (Centaur) stanza; add/refresh it where missing (per the
   global "Centaur execution protocol" template — mechanical step → Qwen, judgment → Opus).
6. Conclude with:
   "✅ agents.md updated — [N] checks added, [N] removed"

## Versioning of .claude/ files
Every time you modify a management Markdown file (both in local .claude/
and in global ~/.claude/) add or update this header,
as the FIRST line of the file:
_v[N] | updated by: [command] | [YYYY-MM-DD HH:MM]_
Increment N by 0.1 for minor changes, by 1.0 for rewrites.
Applies to ALL managed .md files (CLAUDE, memory, rules, skills, errors,
agents, decisions_log, handoff, README, global commands, plans/*).
Exception: assets/ (visual/binary files) and .gitkeep — not versioned.
Exception (public repo): the GLOBAL files shipped on GitHub (~/.claude/ CLAUDE.md, README.md,
commands.md, workflow.md) keep a MINIMAL header — version only, `_vN_` — no "updated by"/date
(they are published; the changelog lives in git). Do NOT re-add the long header to these 4 files.

## Dependencies between commands
agents full          → each agent starts only if the previous one has no 🔴 (order in agents.md)
agents [name]        → requires that "agents init" has been run (agents.md must exist)
agents update        → requires that "agents init" has been run
agents eval          → requires a finished run with a checkpoint (verify with monitor)
agents tune          → requires a diagnosis: run "agents monitor" and/or "agents eval" first
agents family        → monitor → eval → tune; eval only if run finished, tune only if there are problems
agents [monitor/eval/tune] → require ~/.claude/families/[family]/agents.md (created by "agents family init")
agents family update → requires that "agents family init" has been run for that family
postmortem           → automatically updates skills.md and errors.md
update               → run review afterward if there are big changes
agents init          → run update first to have an up-to-date .claude/
agents family init   → run after local "init" (the local CLAUDE.md is needed to detect the family)
agents tune          → can apply its edits under supervision (shows diff + confirms protected files)
design [feature]     → run agents code after approval of the design
plan [objective]     → run design for each non-trivial step of the plan

If a command requires an unsatisfied prerequisite notify me:
"⚠️ [command] requires [prerequisite] first — do I proceed with that?"

## Handling non-standard .md files
RULE FOR NEW FILES FOUND IN .claude/
When init/update/sync/review find a .md file in .claude/
not present in the reading levels (section "## resume command"):
1. Read the content of the file
2. Automatically assign a level:
   - Level 0 if: it's needed every session to understand the project
   - Level 1 if: it's needed only for specific tasks
   - Level 2 if: it's needed only on request or grows over time
3. Notify me: "📂 New file found: [name]
   Proposed level: [N] because [reason in 5 words]
   Do you confirm?"
4. After confirmation: add the rule under the block "ADDITIONAL LEVEL [N]
   FILES" of the resume section, and update the local rules.md
   (table "Registered additional files") with the same info.

NOTE — FAMILY LEVEL files: `~/.claude/families/[family]/agents.md` is NOT a local
file of `.claude/` and does not follow this rule. It's shared among all projects of the family,
loads as Level 1 in resume (trigger "agents monitor/eval/tune/family") and is created/updated
with "agents family init"/"agents family update". Same goes for `~/.claude/workflow.md`.

## Decision history
memory.md holds the current state but not the history.
So as not to lose the why of past decisions:

1. Every time you update the "🗂 Decisions made" section in
   memory.md, before overwriting it add the old decisions
   into .claude/decisions_log.md with this format:

   ## [YYYY-MM-DD] [decision title]
   **Context**: what was happening
   **Decision**: what was chosen
   **Why**: motivation
   **Discarded alternative**: what wasn't chosen and why
   **Impact**: files or components involved

2. decisions_log.md is never overwritten, only appended
3. Don't load it into the context automatically — only if I write
   "why [what]" or "log" or if I look for a specific decision

## "log" command
When I write "log" or "log [topic]":
1. If I write only "log":
   Read decisions_log.md and show the last 5 decisions in the format:
   "[DATE] [title] → [decision in one line]"
2. If I write "log [topic]":
   Search decisions_log.md for all decisions related
   to that topic and show me the complete detail
3. If decisions_log.md doesn't exist yet:
   Create it empty and notify me:
   "📜 decisions_log.md created — it will be populated automatically
   every time I make architectural decisions"

## "status" command
When I write "status":
1. Read .claude/ without loading anything new into the context
2. Reply with this dashboard:

"📊 STATUS — [PROJECT NAME]
 ─────────────────────────────
 Last handoff:    [date from handoff.md]
 Last update:     [date from memory.md]

 .claude/ FILES
 ✅ present: [list with version from header]
 ❌ missing: [list of standard files not found]

 PROJECT STATE (from memory.md)
 In progress:  [🔄 items]
 Problems:     [❌ items]
 Step:         [📌 next step]

 AGENTS (from agents.md)
 Available: [list | 'agents init never run']

 RECENT DECISIONS (from decisions_log.md)
 [last 3 in the format DATE → title]

 CURRENT CONTEXT
 Estimated: ~[X]% used
 Files in memory: [list]"

## "sync" command
When I write "sync":
1. Read ~/.claude/CLAUDE.md global and .claude/rules.md local
2. Look for conflicts between global rules and local overrides
3. Look for rules in the global not present in the local that
   might need to be overridden for this project
4. Check the header versions — is the local older
   than the global by more than 30 days?
5. Reply to me:
   "🔄 Sync completed
    Conflicts found: [N]
    [list of conflicts with proposed resolution]
    Local updated: [date] | Global: [date]
    Recommended action: [none | update local | update global]"

## "clean" command
When I write "clean":
1. List all files in .claude/assets/ with date
2. Identify files older than 30 days
3. Identify dumps and context_dumps never referenced in handoff.md
4. Ask for confirmation before deleting:
   "🧹 Clean — found [N] archivable files:
    [list with date and estimated size]
    Archive in assets/archive/ or delete? (archive/delete/skip)"
5. Execute only after explicit confirmation

## "help [optional command]" command
When I write "help" or "help [command]":
1. If I write only "help" → show the list of commands from ~/.claude/commands.md
2. If I write "help [command]" → show only that command with complete
   details: what it does, when to use it, expected output, dependencies
3. If I write "help update" → realign ~/.claude/commands.md to reality:
   compare the commands documented in commands.md with those actually
   defined in this global CLAUDE.md, add the missing ones, remove the
   obsolete ones, update the quick-reference table and the versioning header.
   Conclude: "✅ commands.md realigned — [N] added, [N] removed"
Don't generate the list from memory — always read commands.md
