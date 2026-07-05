"""Low-level execution + freeze + guardrails (Protocol C machinery + the §9 safety guard).

The self-healing ORCHESTRATION lives in core.py; this module provides the primitives it uses:
run a script (killing the whole process group on timeout), freeze a validated script with a
spec-hash sidecar, and enforce the internal denylist/allow-list that replaces Claude's Bash
allow/deny (which MCP tool calls bypass).
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import signal
import subprocess
import time
from pathlib import Path


class DenylistViolation(Exception):
    pass


def _expand(p: str) -> str:
    return os.path.abspath(os.path.expanduser(p))


def spec_hash(spec: str, model: str) -> str:
    return hashlib.sha256((model + "\x00" + spec).encode()).hexdigest()


def sidecar_path(freeze_path_abs: str) -> str:
    return freeze_path_abs + ".centaur.json"


def check_denylist(cfg, *parts: str) -> None:
    """Reject if any denied substring (e.g. 'train.py') appears in the command/paths/spec.
    This is load-bearing: without it the 'never launch training' invariant is defeated."""
    text = " ".join(p for p in parts if p)
    for bad in cfg.runner.deny_substrings:
        if bad and bad in text:
            raise DenylistViolation(f"denied substring '{bad}' present in command/paths")


def check_interpreter(cfg, interpreter: str) -> None:
    tok = shlex.split(interpreter)[0] if interpreter else ""
    if not tok:
        raise DenylistViolation("empty interpreter")
    base = os.path.basename(tok)
    for allowed in cfg.runner.allow_interpreters:
        if tok == allowed or base == os.path.basename(allowed) or tok.startswith(allowed):
            return
    raise DenylistViolation(f"interpreter '{interpreter}' not in allow_interpreters")


def run_script(cfg, interpreter: str, script_path: str, args: str, timeout_s: int):
    """Run ``interpreter script_path args``. Returns (exit_code, stdout, stderr). On timeout
    kills the whole process group (wrapper interpreters often spawn children) and returns exit 124."""
    check_interpreter(cfg, interpreter)
    check_denylist(cfg, interpreter, script_path, args)
    cmd = shlex.split(interpreter) + [script_path] + shlex.split(args or "")
    # some wrapper interpreters call tput/tset at startup; with no TERM (non-interactive MCP
    # subprocess) they error ('ansi+tabs': unknown terminal type) and exit. Ensure TERM is set.
    env = os.environ.copy()
    env.setdefault("TERM", "xterm")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True, env=env,
    )
    try:
        out, err = proc.communicate(timeout=timeout_s)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            proc.kill()
        out, err = proc.communicate()
        return 124, out or "", (err or "") + f"\n[centaur] timeout after {timeout_s}s, killed process group"


def freeze(freeze_path: str, code: str, spec: str, model: str, attempts: int) -> str:
    """Persist a validated script + a sidecar recording the spec hash (so later calls with the
    same spec skip the LLM and run it natively — Protocol C endpoint)."""
    fp = _expand(freeze_path)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    Path(fp).write_text(code)
    Path(sidecar_path(fp)).write_text(json.dumps({
        "spec_sha256": spec_hash(spec, model),
        "model": model,
        "attempts": attempts,
        "frozen_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }, indent=2))
    return fp


def is_frozen_current(freeze_path: str, spec: str, model: str) -> bool:
    fp = _expand(freeze_path)
    sc = sidecar_path(fp)
    if not (os.path.exists(fp) and os.path.exists(sc)):
        return False
    try:
        meta = json.loads(Path(sc).read_text())
    except Exception:
        return False
    return meta.get("spec_sha256") == spec_hash(spec, model)
