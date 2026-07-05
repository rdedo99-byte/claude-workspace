"""Protocol D — Delta-Only edits (phase 2; implemented, not yet wired to agents).

Qwen emits SEARCH/REPLACE blocks (never a whole-file rewrite). Protected files (obs/action
space, PPO/env config, __init__) are FORCED to protected regardless of the caller: the diff is
returned for confirmation and never auto-applied.
"""
from __future__ import annotations

import difflib
import os
import re
from pathlib import Path

from . import extract, ollama_client, traffic_cop

# Filename substrings that always require confirmation before an edit is applied.
# Generic defaults: config files (*_cfg.py) and package registration (__init__.py).
# Extend for your project's sensitive files (e.g. anything defining a public interface / I/O shape).
PROTECTED_PATTERNS = ["_cfg.py", "__init__.py"]

_SR_BLOCK = re.compile(r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE", re.S)


def _is_protected(path: str) -> bool:
    base = os.path.basename(path)
    return any(pat in base for pat in PROTECTED_PATTERNS)


def _parse_blocks(text: str):
    return [(m.group(1), m.group(2)) for m in _SR_BLOCK.finditer(text)]


def _unified_diff(a: str, b: str, path: str) -> str:
    return "".join(difflib.unified_diff(
        a.splitlines(keepends=True), b.splitlines(keepends=True),
        fromfile=path, tofile=path,
    ))


def apply_edit(cfg, file: str, delta_spec: str, protected: bool = True) -> dict:
    fp = os.path.abspath(os.path.expanduser(file))
    if not os.path.exists(fp):
        return {"error": "file_not_found", "file": fp}
    forced = _is_protected(fp)
    protected = bool(protected) or forced
    original = Path(fp).read_text()

    if not ollama_client.ping(cfg):
        return {"error": "ollama_unreachable"}
    cpu = traffic_cop.status(cfg)["recommended_mode"] == "cpu"

    prompt = (
        "You are a code-editing engine. Produce a MINIMAL edit as one or more SEARCH/REPLACE "
        "blocks in EXACTLY this format (no prose, no whole-file rewrite):\n"
        "<<<<<<< SEARCH\n<exact existing lines>\n=======\n<replacement lines>\n>>>>>>> REPLACE\n\n"
        f"FILE: {fp}\n\nEDIT REQUEST:\n{delta_spec}\n\n"
        # 12k troncava i file reali (env_cfg ~15k) → Qwen vedeva un file mozzato e rispondeva in prosa
        "Current content:\n```\n" + original[:120000] + "\n```\n"
    )
    raw = extract.strip_think(ollama_client.generate(cfg, prompt, force_cpu=cpu))
    blocks = _parse_blocks(raw)
    if not blocks:
        return {"error": "no_edit_blocks", "raw": raw[:2000], "file": fp}

    new_content = original
    for search, replace in blocks:
        if search not in new_content:
            return {"error": "search_not_found", "search": search[:400], "applied": False, "file": fp}
        new_content = new_content.replace(search, replace, 1)

    diff = _unified_diff(original, new_content, fp)
    if protected:
        return {"applied": False, "protected": True, "forced": forced, "file": fp, "diff": diff,
                "reason": "protected file -> confirm before applying"}
    Path(fp).write_text(new_content)
    return {"applied": True, "protected": False, "file": fp, "diff": diff}
