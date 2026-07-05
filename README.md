_v1.1 | aggiornato da: repo generico — families/ vuota (popolata da agents family init), rif. isaac_lab rimossi dal README | 2026-07-01_

# Claude Code — Global Config

Portable global setup for **Claude Code**: session/memory management, custom commands, and a
**3-level agent architecture**, reusable across projects and machines. This repo is the portable
subset of `~/.claude/` — the reusable *system*, not per-project data.

## What's inside
| File / dir | Purpose |
|---|---|
| `CLAUDE.md` | Global rules + developer profile + all custom commands + agent system |
| `commands.md` | Full command reference (used by `help`) |
| `workflow.md` | Canonical work pipeline (project open → deliverable) |
| `families/` | Home of **family** runtime-evaluation agents. **Ships empty** — you generate a family's agents on demand with `agents family init` (e.g. `ros2_nav/`, `isaac_lab/`, …) |
| `settings.json` | Global Claude Code settings (model/theme) |

### The 3 agent levels
- **Generic (coding)** — Implementer → Reviewer → Validator. Trigger: `agents code [task]`. Defined in `CLAUDE.md`.
- **Family (runtime evaluation)** — reusable across projects of the same family. Trigger: `agents monitor` / `agents eval` / `agents tune` / `agents family`. Generated on demand with `agents family init` into `families/<family>/agents.md` (not shipped — this repo is domain-neutral).
- **Project (static audit)** — generated per project. Trigger: `agents full` / `agents [name]`. Lives in the project's own `.claude/agents.md`.

## Install (new machine)
```bash
# 1. Clone into the Claude config dir (or clone elsewhere and copy the files in)
git clone <this-repo> ~/.claude

# 2. Authenticate (credentials are NOT in this repo — log in fresh)
claude            # then follow the auth prompt

# 3. Adjust machine-specific paths in CLAUDE.md
#    (home dir, tool install paths, OS/GPU in the "Technical identity" section)
```
> `~/.claude/` also holds machine/account state (`.credentials.json`, `projects/`, caches). Those are
> **not** tracked here (see `.gitignore`) and are recreated locally on first use.

## Bootstrap a project (build the architecture)
Run these once per project, in order:
```
1. init                → creates the project's .claude/ (CLAUDE.md, memory, handoff, errors, rules, skills)
                          and detects the project family
2. agents family init  → generates ~/.claude/families/<family>/agents.md  (skip if the family already exists)
3. agents init         → generates the project's .claude/agents.md (3 static-audit agents)
```
On-demand files appear when needed: `log`/`adr` → `decisions_log.md`, `plan`/`design` → `plans/`.

## Daily workflow
```
resume                     # open a project (auto-loads handoff + memory + local CLAUDE.md)
agents code [task]         # implement with the generic 3-agent cycle
agents full                # static audit of the changed areas
agents monitor/eval/tune   # (family) evaluate a run and prescribe fixes
checkpoint | handoff       # save state mid-session / at the end
help                       # list all commands (reads commands.md)
```
Full pipeline and command details: see `workflow.md` and `commands.md`.

## ⚠️ Security
- **Never commit `~/.claude/.credentials.json`** or any auth token. The `.gitignore` whitelists only the
  portable files — verify `git status` before every push.
- Keep this repo **private**: `CLAUDE.md` contains a personal developer profile and absolute paths.

## Versioning
Every managed `.md` file starts with a `_vN | updated by: … | date_` header. Bump `+0.1` for minor
edits, `+1.0` for rewrites.
