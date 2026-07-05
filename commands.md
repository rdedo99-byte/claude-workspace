_v1.5_

# Commands — Complete Reference
_All custom commands available in any project._
_To update this file: edit manually or write "help update"_

---

## SESSION MANAGEMENT

### resume
Resumes work after a handoff in a new chat.
Lazy loading: Level 0 automatic, then asks what's needed.
When: always as the first thing in a new chat
Dependencies: none
Output: confirmation of loaded context + question about the task

### checkpoint
Light update of memory.md mid-session.
Does not touch handoff.md.
When: every ~1 hour during long sessions
Dependencies: none
Output: "📍 Checkpoint [TIME] — [state in 10 words]"

### handoff
Complete snapshot for chat switch or end of session.
Updates memory.md + rewrites handoff.md.
When: before closing the chat | manual | automatic at 80%
Dependencies: none
Output: "✅ Handoff ready — paste handoff.md into the next chat"

### dump
Emergency when context window is nearly exhausted.
Saves everything to assets/context_dump_[DATE-TIME].md.
When: automatic at 95% | manual if the situation is critical
Dependencies: none
Output: "💾 Dump saved — open a new chat"

### context
Shows what I know at this moment: files read, assumptions,
skills applied, known gaps.
When: whenever you suspect it's out of sync
Dependencies: none
Output: concise list without prose

### status
Text dashboard of the project state and the .claude/ files.
Includes file versions, project state, agents, recent decisions.
When: start of session | after long pauses | before agents full
Dependencies: none (reads without loading into context)
Output: formatted dashboard with all states

---

## INITIALIZATION AND MAINTENANCE

### init
Creates .claude/ from scratch by reading the project.
WARNING: if .claude/ already exists → runs update instead.
When: first start on a new project
Dependencies: none
Output: confirmation of created files + assumptions + things to verify

### update
Aligns .claude/ to the project's current code.
Updates only the files with real changes. Does not touch handoff.md.
When: after big code changes | every 2-3 sessions
Dependencies: none (but run review afterwards if changes are big)
Output: list of updated / unchanged files / additions

### review
Complete consistency check between .claude/ and the real code.
Looks for discrepancies, duplications, gaps. Asks for confirmation before fixing.
When: something doesn't add up | after long sessions | before a release
Dependencies: none
Output: classified list of problems + fix proposal

### sync
Verifies that global and local are consistent with each other.
Looks for rule conflicts and stale versions.
When: after updates to the global | if rules seem wrong
Dependencies: none
Output: list of conflicts + recommended action

### clean
Archives or removes old files from assets/.
Always asks for confirmation before deleting.
When: assets/ has grown large | start of a new sprint
Dependencies: none
Output: list of archivable files + confirmation before proceeding

---

## HISTORY AND TRACEABILITY

### log
Shows the history of the project's architectural decisions.
Reads decisions_log.md without loading it into permanent context.
When: you want to understand why a choice was made
Dependencies: none (creates decisions_log.md if it doesn't exist)
Output: last 5 decisions | detail for a specific topic

### why [what]
Reconstructs the reasoning behind a choice in the code.
Searches CLAUDE.md, errors.md, decisions_log.md, git history.
When: you find something strange and don't remember why
Dependencies: MCP Git recommended for complete history
Output: explanation with cited sources

### postmortem
Documents a fixed bug in errors.md with root cause.
Automatically updates skills.md if the gap has been closed.
Adds an entry in decisions_log.md if the fix changed the architecture.
When: after fixing an important bug
Dependencies: none
Output: "📝 Postmortem added to errors.md"

---

## PLANNING AND DESIGN

### design [feature]
Design document before implementing.
Creates assets/design_[feature]_[date].md with options and proposal.
Never starts implementing without approval.
When: any non-trivial feature
Dependencies: none
Output: "📐 Design ready — do you approve or should I modify?"

### plan [objective]
Multi-session plan for large objectives.
Creates assets/plan_[objective]_[date].md with steps and dependencies.
When: objectives that require multiple sessions or multiple files
Dependencies: none (run design for non-trivial steps)
Output: "📋 Plan ready — [N] steps"

### adr [decision]
Architecture Decision Record for important decisions.
Creates assets/adr_[NNN]_[title].md with standard format.
Automatically adds an entry in decisions_log.md.
When: irreversible architectural decisions
Dependencies: none
Output: ADR file created in assets/

### onboard
Operational guide to resume after a long pause.
Creates assets/onboarding_[date].md with everything needed.
When: after long pauses | to onboard someone
Dependencies: reads all .claude/ files + main code
Output: "📖 Onboarding ready in assets/"

---

## AGENTS

_All agent commands run under the **Centaur execution protocol** (HYBRID): the mechanical work
(generate/run code, edits, mini-summaries) is dispatched to a local Qwen via the `centaur` MCP
server, while Opus keeps every judgment/verdict. `agents init` / `agents family init` embed an
Execution stanza in each agent they create, so new agents are auto-wired to Ollama with no extra
setup. Definition + tools (`vram_status`, `qwen_codegen_run`, `qwen_edit`, `qwen_summarize`) live in
`~/.claude/CLAUDE.md` → "Centaur execution protocol"; the bridge is `~/.claude/centaur/`._

### agents code [task]
Generic 3-agent pipeline for any coding task.
Sequence: Implementer → Reviewer → Integration Validator.
Max 3 iterations before asking for help.
When: coding tasks that benefit from automatic review
Dependencies: none
Output: code + pipeline report + updated memory.md

### agents init
Generates 3 project-specific agents by reading the code.
Creates .claude/agents.md with checklists based on real files.
When: first start | project structure changed radically
Dependencies: update recommended first
Output: agents.md created + agent names + covered areas

### agents update
Updates agents.md to the current code.
Adds checks for new files, removes checks for deleted files.
When: after big code changes
Dependencies: agents init must have been run first
Output: N checks added / removed

### agents full
Runs all 3 project-specific agents in sequence.
The second only starts if the first has no 🔴 blockers.
When: start of a training session | after big changes
Dependencies: agents init must have been run
Output: complete report + updated memory.md

### agents [name]
Runs a single project-specific agent.
When: you want to validate only a specific area
Dependencies: agents init must have been run
Output: specific agent report

---

## FAMILY AGENTS (runtime evaluation — reusable per project family)
_Defined in ~/.claude/families/[family]/agents.md. Project-agnostic: they auto-configure
from the local CLAUDE.md. No family ships preset — generate one with "agents family init". The
descriptions below are the generic command roles; the concrete checklists come from the family file._

### agents monitor
The family's monitoring agent: evaluates a run/process WHILE it runs, from its telemetry.
Progress trend / plateau / instability / divergence / ETA.
When: DURING a run, to decide whether to continue or stop
Dependencies: a running/recent run with telemetry; ~/.claude/families/[family]/agents.md existing
Output: verdict ✅ continue | ⚠️ plateau | ❌ stop and fix (+ action)

### agents eval
The family's evaluation agent: runs the built artifact and measures behavioral/output quality
against the family's target metrics.
When: AFTER a run, on the produced artifact/checkpoint
Dependencies: finished run + artifact; no other run competing for the same resources
Output: verdict ✅ ready for the next step | ⚠️ usable but [limitation] | ❌ not ready

### agents tune
The family's tuning agent: turns the diagnosis (monitor+eval) into a precise prescription.
Edits ordered by priority: file, param, current→proposed, rationale, risk.
Can APPLY the edits under supervision: shows the diff and asks for confirmation on PROTECTED files.
When: the result is mediocre and you need to know (and apply) WHAT to change in the next run
Dependencies: a diagnosis (agents monitor and/or eval)
Output: prioritized list of edits + recommended run (from scratch/resume) + diffs applied after ok

### agents family
Runs monitor → eval → tune in sequence.
eval only if the run is finished; tune only if monitor/eval flag problems (if ✅ → next step).
When: at the end of a run cycle, for complete diagnosis+prescription
Dependencies: ~/.claude/families/[family]/agents.md existing
Output: combined report of the three agents

### agents family init
Generates the suite of evaluation agents for the current project's family from scratch
(like "agents init" for the specific ones, but for the runtime). Detects the family from the local CLAUDE.md.
When: new project family without evaluation agents
Dependencies: local init run (needs the CLAUDE.md to detect the family)
Output: ~/.claude/families/[name]/agents.md created + triggers registered

### agents family update
Updates the family agents: new lifecycle phases, new metrics/tools.
When: the family needs one more agent or updated checks
Dependencies: agents family init run for that family
Output: "✅ agents family [name] updated — [N] agents, [N] checks added/removed"

---

## META

### help [optional command]
Shows the available commands by reading this file (never from memory).
When: you don't remember a command or its details
Dependencies: none
Output: complete list | detail for a single command

### help update
Realigns this commands.md to the commands actually defined in the
global CLAUDE.md: adds missing ones, removes obsolete ones, updates the table and header.
When: after adding/removing commands in the global
Dependencies: none
Output: "✅ commands.md realigned — [N] added, [N] removed"

---

## QUICK REFERENCE

| Command | When | Touches file |
|---------|------|--------------|
| resume | start of chat | reads only |
| checkpoint | every hour | memory.md |
| handoff | end of chat | memory + handoff |
| dump | emergency | assets/ |
| context | sync check | reads only |
| status | overview | reads only |
| init | new project | creates .claude/ |
| update | maintenance | .claude/ (no handoff) |
| review | verification | proposes fixes |
| sync | rule conflicts | suggests fixes |
| clean | cleanup | assets/ (with confirmation) |
| log | decision history | reads decisions_log |
| why [what] | understanding | reads only |
| postmortem | fixed bug | errors+skills+log |
| design | pre-implementation | assets/ |
| plan | large objectives | assets/ |
| adr | arch. decisions | assets/+decisions_log |
| onboard | long pause | assets/ |
| agents code | generic coding | memory |
| agents init | setup P agents | agents.md |
| agents update | P agents maintenance | agents.md |
| agents full | complete P validation | memory+errors+skills |
| agents [name] | single P validation | memory |
| agents monitor | monitor training (F) | reads tfevents |
| agents eval | evaluate policy (F) | runs play.py |
| agents tune | next run prescription (F) | edits under supervision |
| agents family | monitor+eval+tune (F) | reads tfevents+play.py |
| agents family init | create family agents | families/[fam]/agents.md |
| agents family update | F agents maintenance | families/[fam]/agents.md |
| help | command list | reads commands.md |
