"""Orchestration — the functions BOTH the CLI and the MCP server call.

HYBRID contract: the *spec* (written by Opus) carries all intent; Qwen only writes/runs code.
Every function returns a plain dict (never raises across the MCP boundary) so Opus can reason
about the outcome. Judgment/verdict stays in Opus.
"""
from __future__ import annotations

import os
from pathlib import Path

from . import config as _config
from . import extract, ollama_client, runner

# Qwen is an execution engine, not an assistant. Keep it mechanical.
SYSTEM_PREAMBLE = (
    "You are a code execution engine, NOT an assistant. Write a small, self-contained script "
    "that satisfies the SPEC exactly. Do not explain, do not add prose. "
    "Output ONLY one ```python code block and nothing else.\n\nSPEC:\n"
)


def _cfg():
    return _config.load_config()


def vram_status() -> dict:
    from . import traffic_cop
    return traffic_cop.status(_cfg())


def _decide_cpu(cfg, force_cpu):
    if force_cpu is not None:
        return bool(force_cpu), "forced by caller"
    from . import traffic_cop
    st = traffic_cop.status(cfg)
    return (st["recommended_mode"] == "cpu"), st["reason"]


def _mini_summary(cfg, rc, out, err, summarize, cpu, timeout_s) -> str:
    """Deterministic, bridge-computed one-liner by default (no wasted LLM call on structured
    output). Only fire Qwen to summarize verbose/free-text output when summarize=True."""
    base = (f"exit {rc} · stdout {len(out)}B/{out.count(chr(10))}L · "
            f"stderr {len(err)}B · mode {'cpu' if cpu else 'gpu'}")
    if summarize and out.strip():
        try:
            if ollama_client.ping(cfg):
                q = "Summarize this program output in ONE short line, no preamble:\n\n" + out[-4000:]
                s = extract.strip_think(ollama_client.generate(cfg, q, force_cpu=cpu, timeout_s=timeout_s))
                first = s.strip().splitlines()
                if first:
                    return base + " · " + first[0][:200]
        except Exception:
            pass
    return base


def qwen_codegen_run(spec, interpreter="python3", freeze_path="", test_args="--test",
                     run_args="", force_cpu=None, max_attempts=None, timeout_s=None,
                     regenerate=False, summarize=False, **_ignore) -> dict:
    """Self-healing generate→smoke→freeze→run (Protocol C). If freeze_path exists and its
    spec-hash matches (and not regenerate) → skip the LLM, run natively."""
    cfg = _cfg()
    max_attempts = max_attempts or cfg.runner.max_attempts
    run_timeout = timeout_s or cfg.runner.default_timeout_s
    gen_timeout = cfg.ollama.timeout_s

    if not freeze_path:
        return {"error": "freeze_path required"}

    # Up-front guards (interpreter allow-list + denylist on all inputs incl. the spec).
    try:
        runner.check_interpreter(cfg, interpreter)
        runner.check_denylist(cfg, interpreter, freeze_path, test_args, run_args, spec)
    except runner.DenylistViolation as e:
        return {"error": "denylist", "detail": str(e)}

    cpu, mode_reason = _decide_cpu(cfg, force_cpu)
    mode = "cpu" if cpu else "gpu"

    fp = runner._expand(freeze_path)
    generated = False
    attempts = 0

    if not regenerate and runner.is_frozen_current(freeze_path, spec, cfg.ollama.model):
        # Fast path: validated script already frozen → no LLM.
        pass
    else:
        if not ollama_client.ping(cfg):
            return {"error": "ollama_unreachable", "detail": f"no response from {cfg.ollama.host}", "mode": mode}
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        candidate = fp + ".candidate.py"
        prompt = SYSTEM_PREAMBLE + spec
        rc = out = err = None
        for attempts in range(1, max_attempts + 1):
            try:
                raw = ollama_client.generate(cfg, prompt, force_cpu=cpu, timeout_s=gen_timeout)
            except ollama_client.OllamaError as e:
                return {"error": "ollama_error", "detail": str(e), "attempts": attempts, "mode": mode}
            code = extract.extract_code(raw)
            Path(candidate).write_text(code)
            rc, out, err = runner.run_script(cfg, interpreter, candidate, test_args, run_timeout)
            if rc == 0:
                generated = True
                runner.freeze(freeze_path, code, spec, cfg.ollama.model, attempts)
                try:
                    os.remove(candidate)
                except OSError:
                    pass
                break
            # Feed the traceback back for the next attempt.
            prompt = (SYSTEM_PREAMBLE + spec +
                      "\n\nYour previous attempt FAILED its smoke test. Fix the script. "
                      f"Do not change the interface. Error output:\nexit={rc}\n"
                      f"STDERR:\n{(err or '')[-4000:]}\nSTDOUT:\n{(out or '')[-1000:]}")
        else:
            # All attempts failed → do NOT freeze; leave the candidate for inspection.
            return {"error": "codegen_failed", "attempts": attempts, "exit_code": rc,
                    "stderr": (err or "")[-4000:], "stdout": (out or "")[-2000:],
                    "candidate": candidate, "frozen_path": None, "generated": False, "mode": mode,
                    "mini_summary": f"failed after {attempts} attempts (last exit {rc})"}

    # Real run of the (now validated) frozen script.
    rc, out, err = runner.run_script(cfg, interpreter, fp, run_args, run_timeout)
    return {
        "frozen_path": fp,
        "generated": generated,
        "attempts": attempts,
        "exit_code": rc,
        "stdout": out,
        "stderr": err,
        "mode": mode,
        "mode_reason": mode_reason,
        "mini_summary": _mini_summary(cfg, rc, out, err, summarize, cpu, run_timeout),
    }


def qwen_edit(file, delta_spec, protected=True) -> dict:
    """Protocol D — delta/Search&Replace edit. Protected files → return the diff, never apply."""
    from . import editor
    return editor.apply_edit(_cfg(), file, delta_spec, protected)


def qwen_summarize(text, instruction="Summarize in ONE short line, no preamble.") -> dict:
    """Mini-summary of verbose/free-text output. For structured (JSON) output, Opus should read it
    directly — don't waste a CPU LLM call summarizing machine-readable data."""
    cfg = _cfg()
    if not text or not text.strip():
        return {"summary": "", "note": "empty input"}
    if not ollama_client.ping(cfg):
        return {"error": "ollama_unreachable"}
    from . import traffic_cop
    cpu = traffic_cop.status(cfg)["recommended_mode"] == "cpu"
    prompt = instruction.strip() + "\n\n---\n" + text[-8000:]
    try:
        raw = ollama_client.generate(cfg, prompt, force_cpu=cpu, timeout_s=cfg.ollama.timeout_s)
    except ollama_client.OllamaError as e:
        return {"error": "ollama_error", "detail": str(e)}
    return {"summary": extract.strip_think(raw).strip(), "mode": "cpu" if cpu else "gpu"}
