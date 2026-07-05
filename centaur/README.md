# Centaur — generic HYBRID execution bridge (Ollama ↔ Claude Code via MCP)

Local-LLM execution substrate for the `.claude/` agent system. **HYBRID**: the local model (via
Ollama) does the MECHANICAL work — generate/run scripts, apply syntactic edits, summarize verbose
output — while the frontier model (Opus/Sonnet, in Claude Code) keeps ALL judgment (which lever, why,
the 🔴/🟡/🟢 verdicts). Project- and domain-agnostic: the bridge knows nothing about the calling
agent. Canonical protocol: `~/.claude/CLAUDE.md` → "Centaur execution protocol".

## Layout (this repo ships the code + template only)
```
centaur/               # the python package (config, traffic_cop, ollama_client, extract,
                       #   runner, editor, core, cli, server)   ← shipped
requirements.txt       # mcp + httpx                            ← shipped
config.example.json    # copy → config.json and adapt           ← shipped
README.md              # this file                              ← shipped
config.json            # YOUR real config (paths, model) — git-ignored, stays local
.venv/                 # recreated via pip                      — git-ignored
frozen/                # throwaway frozen scripts (hash-named)  — git-ignored
specs/                 # project-specific reusable specs        — git-ignored
```

## Install
```bash
# 1. Ollama + a worker model (MoE coder recommended: fast executor, fits modest GPUs)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3-coder:30b

# 2. Isolated venv for the bridge
python3 -m venv ~/.claude/centaur/.venv
~/.claude/centaur/.venv/bin/pip install -r ~/.claude/centaur/requirements.txt

# 3. Your local config (kept out of git)
cp ~/.claude/centaur/config.example.json ~/.claude/centaur/config.json
#    → edit config.json: set your model, and add your project's custom interpreter/run-matcher
#      to allow_interpreters / train_match if you use a wrapper (e.g. a sim launcher).

# 4. Register the MCP server globally (all projects)
claude mcp add --scope user centaur \
  -e PYTHONPATH=$HOME/.claude/centaur \
  -- $HOME/.claude/centaur/.venv/bin/python -m centaur.server
```

## MCP tools (generic, domain-agnostic)
- `vram_status()` — resource gate; a heavy GPU job alive OR VRAM>threshold ⇒ local LLM forced CPU-only.
- `qwen_codegen_run(spec, interpreter, freeze_path, …)` — self-healing generate→smoke→freeze→run;
  once frozen with a matching spec-hash it runs natively, **no LLM** (instant, safe during a heavy job).
- `qwen_edit(file, delta_spec, protected)` — delta-only search&replace; protected files (`*_cfg.py`,
  `__init__.py`, extend in `editor.py`) return a **diff for confirmation**, never auto-applied.
- `qwen_summarize(text, instruction)` — mini-summary of verbose output.

## Test via CLI (before/without MCP)
```bash
export PYTHONPATH=$HOME/.claude/centaur
PY=$HOME/.claude/centaur/.venv/bin/python
$PY -m centaur.cli vram-status
$PY -m centaur.cli ping
$PY -m centaur.cli codegen-run --spec-file /path/to/spec.txt \
   --interpreter "python3" --freeze-path /abs/reader.py \
   --test-args "--test /abs/input" --run-args "/abs/input"
```

## Protocols enforced
A Traffic-Cop (CPU when GPU busy; `keep_alive:0` GPU / `keep_alive_cpu` RAM-safe CPU) ·
B stateless one-shot · C self-healing (≤3 retries, freeze, native reuse) · D delta-only edits.
**Safety:** MCP calls bypass Claude's Bash allow/deny, so the bridge re-enforces `deny_substrings`
+ an `allow_interpreters` allow-list internally (config.json).

## Config knobs (`config.json`, overrides the code defaults)
- `ollama.model` — worker model (default `qwen3-coder:30b`; a thinking model works but wastes its
  reasoning in the HYBRID role and is slower on CPU).
- `traffic_cop.train_match` — `pgrep -f` pattern for your "heavy GPU job" (e.g. `myproj/train.py`).
- `runner.deny_substrings`, `runner.allow_interpreters`, timeouts.
- Env overrides: `CENTAUR_MODEL`, `CENTAUR_OLLAMA_HOST`.

**Notes from real use**: generate/freeze scripts while the GPU is free (local LLM on GPU = fast);
during a heavy job use only the already-frozen scripts (LLM generation on CPU under load can exceed
the timeout). Pick a model that fits your RAM/VRAM — an ~18 GB MoE beats a 50 GB giant on a 16 GB GPU.
Graceful degradation: without Ollama/this bridge, each agent just does its mechanical step itself.
