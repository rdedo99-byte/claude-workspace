"""Centaur — generic HYBRID execution bridge.

Opus (cloud) orchestrates and keeps ALL judgment; Qwen (local, via Ollama) does ONLY
mechanical execution (generate/run code, edit, summarize). Domain-agnostic on purpose:
tools receive a spec + interpreter + path and nothing else. See ~/.claude/CLAUDE.md
"Centaur execution protocol (HYBRID)".
"""

__version__ = "0.1.0"
