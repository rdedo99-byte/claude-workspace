"""Pull runnable code out of an LLM response.

Handles both configured models: qwen3.6:27b emits <think>…</think> reasoning that must be
stripped; qwen3-coder:30b (no thinking) does not. Then grabs the first fenced code block.
"""
from __future__ import annotations

import re

_THINK_FULL = re.compile(r"<think>.*?</think>", re.S)
_FENCE_PY = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)
_FENCE_ANY = re.compile(r"```[a-zA-Z0-9_+-]*\s*\n?(.*?)```", re.S)


def strip_think(text: str) -> str:
    """Remove <think>…</think> blocks; if only a stray closing tag survives (truncated open),
    keep everything after the last one."""
    text = _THINK_FULL.sub("", text)
    if "</think>" in text:
        text = text.split("</think>")[-1]
    return text


def extract_code(text: str) -> str:
    """Return the code Qwen produced: think-stripped, first fenced block, or the whole body."""
    text = strip_think(text)
    m = _FENCE_PY.search(text)
    if m:
        return m.group(1).strip("\n")
    m = _FENCE_ANY.search(text)
    if m:
        return m.group(1).strip("\n")
    return text.strip()
