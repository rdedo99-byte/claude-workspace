_v2.0_

# Claude Code — Global Workspace

Portable global setup for **Claude Code**: session/memory management, custom commands, a
**3-level agent architecture**, and an optional **local-LLM execution bridge (Ollama)**.
This repo is the portable subset of `~/.claude/` — the reusable *system*, not per-project data
and not personal data (see [Privacy](#-privacy--security)).

## What's inside
| File / dir | Purpose |
|---|---|
| `CLAUDE.md` | Global rules, generic developer profile, all custom commands, the agent system, the Centaur (Ollama) execution protocol |
| `commands.md` | Full command reference (used by `help`) |
| `workflow.md` | Canonical work pipeline (project open → deliverable) |
| `families/` | Home of **family** runtime-evaluation agents. **Ships empty** — generated on demand with `agents family init` (e.g. `ros2_nav/`, `isaac_lab/`, …) |
| `settings.json` | Global Claude Code settings (model preferences) |

### The 3 agent levels
| Level | What it does | Trigger | Where it lives |
|---|---|---|---|
| **Generic (coding)** | Implementer → Reviewer → Validator pipeline on any code task | `agents code [task]` | `CLAUDE.md` (shipped) |
| **Family (runtime evaluation)** | Evaluates *runs/executions* (training logs, checkpoints, metrics) for a whole family of projects | `agents monitor` / `eval` / `tune` / `family` | `families/<family>/agents.md` (generated) |
| **Project (static audit)** | 3 code auditors tailored to one project's risk areas | `agents full` / `agents [name]` | the project's own `.claude/agents.md` (generated) |

---

## 🛠 Install (new machine)

**Prerequisites**: [Claude Code](https://claude.com/claude-code) installed. Git.

```bash
# 1. Clone straight into the Claude config dir
git clone https://github.com/rdedo99-byte/claude-workspace.git ~/.claude

# 2. Authenticate (credentials are NOT in this repo — log in fresh)
claude            # follow the auth prompt

# 3. Create your PERSONAL profile (local-only, never committed — the /* gitignore rule covers it)
cat > ~/.claude/profile.local.md <<'EOF'
# Personal profile — LOCAL-ONLY
## Identity
- <name, role, org>
## Machine
- <OS | GPU/RAM | key tool install paths>
## Platforms / active projects
- <robot platforms, project pointers>
EOF
```
`CLAUDE.md` instructs Claude to read `profile.local.md` at session start if present; without it,
everything still works and specifics are learned per-project.

> `~/.claude/` also holds machine/account state (`.credentials.json`, `projects/`, session caches).
> None of it is tracked here (whitelist `.gitignore`) and it is recreated locally on first use.

## 🚀 Usage

**Bootstrap a project** (once per project, in order):
```
1. init                → creates the project's .claude/ (CLAUDE.md, memory, handoff, errors, rules, skills)
                          and detects the project FAMILY
2. agents family init  → generates families/<family>/agents.md   (skip if the family already exists)
3. agents init         → generates the project's .claude/agents.md (3 static-audit agents)
```

**Daily loop**:
```
resume                     # open a project: auto-loads handoff + memory + local CLAUDE.md
agents code [task]         # implement via the generic 3-agent cycle
agents full                # static audit of the changed areas
agents monitor/eval/tune   # (family) supervise a run, measure the result, prescribe next changes
plan / design [x]          # multi-session plans and pre-implementation designs (assets/)
checkpoint | handoff       # save state mid-session / before closing the chat
status | context | help    # dashboards and full command list (help reads commands.md)
```
Session continuity: `handoff.md` + `memory.md` are updated automatically at context thresholds
(60/80/95%) so a new chat resumes exactly where the old one stopped (`resume`).
Full pipeline: `workflow.md`. Every command in detail: `commands.md`.

## 🦙 Local LLM execution — Centaur (Ollama) — *optional*

The system can offload the **mechanical** part of agent work (generate & run parsing scripts,
apply syntactic edits, summarize verbose output) to a **local model via Ollama**, while the frontier
model (Opus/Sonnet) keeps ALL judgment — diagnosis, severity, verdicts. Principle: **HYBRID —
the local LLM executes, Claude judges.** The full protocol lives in `CLAUDE.md` → *"Centaur
execution protocol"*; every agent (present or future-generated) carries an *Execution (Centaur)*
stanza wired to it.

The bridge code ships in `centaur/` (generic; your real paths live in a git-ignored `config.json`).

**Setup** (on the machine that will run it):
```bash
# 1. Ollama + a worker model (MoE coder recommended: fast executor, fits modest GPUs)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3-coder:30b        # ~18 GB; any capable local model works (configurable)

# 2. Isolated venv + deps for the bridge
python3 -m venv ~/.claude/centaur/.venv
~/.claude/centaur/.venv/bin/pip install -r ~/.claude/centaur/requirements.txt

# 3. Your local config (kept out of git — this is where your machine paths go)
cp ~/.claude/centaur/config.example.json ~/.claude/centaur/config.json
#    edit config.json: model, and your project's custom interpreter/run-matcher if any

# 4. Register the MCP server globally (all projects)
claude mcp add --scope user centaur \
  -e PYTHONPATH=$HOME/.claude/centaur \
  -- $HOME/.claude/centaur/.venv/bin/python -m centaur.server
```
Full bridge details: `centaur/README.md`.

**What you get** (4 generic, domain-agnostic MCP tools):
- `vram_status` — resource gate: if a GPU training is alive, the local LLM is forced **CPU-only**
  (it never steals VRAM from your run);
- `qwen_codegen_run` — self-healing *generate → smoke-test → freeze → run*: once a script is frozen,
  later calls run it **natively with no LLM** (instant, safe even during training);
- `qwen_edit` — delta-only search&replace edits; protected files return a **diff for confirmation**,
  never auto-applied;
- `qwen_summarize` — mini-summaries of verbose output.

**Graceful degradation**: without Ollama/the bridge, every agent simply does its mechanical step
itself. Nothing breaks — Centaur is an optimization, not a dependency.

**Practical notes** (from real use): generate/freeze scripts while the GPU is free (local LLM on GPU
= fast); during a training use only the frozen scripts (LLM generation on CPU under load can exceed
timeouts). Pick a model that fits your RAM/VRAM — an 18 GB MoE beats a 50 GB giant on a 16 GB GPU.

## 🔒 Privacy & security
- **Whitelist `.gitignore`**: everything in `~/.claude/` is ignored by default; only the files listed
  above are tracked. Credentials, session data, memories and caches can never be committed by accident —
  still, **check `git status --short` before every push**.
- **Personal data lives in `profile.local.md`** (never tracked). `CLAUDE.md` here is generic on purpose:
  no names, employers, hardware or absolute personal paths → the repo can stay public.
- Never commit `.credentials.json` or any token (the whitelist already excludes them).

## Versioning
Shipped files carry a minimal `_vN_` header (history = git). Project-side `.claude/` files use the
richer `_vN | updated by | date_` convention described in `CLAUDE.md`.
