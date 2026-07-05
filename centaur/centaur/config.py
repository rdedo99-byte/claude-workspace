"""Configuration loading — Python 3.10 safe (no tomllib).

Defaults live here as dataclasses; ``~/.claude/centaur/config.json`` (if present) shallow-
overrides them; a few env vars override on top of that. Editing the model is a one-liner in
config.json (``"model": "qwen3-coder:30b"``) — this is how we A/B the two Qwen models.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

CENTAUR_HOME = Path(os.path.expanduser("~/.claude/centaur"))
CONFIG_JSON = CENTAUR_HOME / "config.json"


@dataclass
class OllamaCfg:
    host: str = "http://localhost:11434"
    model: str = "qwen3-coder:30b"      # default: no-thinking MoE coder (fast executor for HYBRID); override in config.json
    temperature: float = 0.1            # deterministic code
    keep_alive: int = 0                 # GPU mode: NEVER hold VRAM after a call (Protocol A/B)
    keep_alive_cpu: int = 300           # CPU mode: keep model in RAM (safe, no VRAM) → no reload thrash in the self-heal loop
    timeout_s: int = 600                # LLM generation budget (CPU can be slow) — separate from run timeout


@dataclass
class TrafficCopCfg:
    vram_pct_threshold: float = 0.85    # >85% used AND no training → still CPU
    train_match: str = "train.py"       # pgrep -f pattern for "heavy GPU process" (override in config.json for your run)


@dataclass
class RunnerCfg:
    default_timeout_s: int = 300        # per-script execution budget
    max_attempts: int = 3               # self-healing retries (Protocol C)
    bridge_freeze_dir: str = "~/.claude/centaur/frozen"
    # HARD guard — MCP tools bypass Claude's Bash allow/deny, so the bridge re-enforces it.
    deny_substrings: list = field(default_factory=lambda: ["train.py", "train.sh"])
    # generic defaults; add your project's custom runner (e.g. a wrapper script) in config.json
    allow_interpreters: list = field(
        default_factory=lambda: ["python3", "/usr/bin/python3"]
    )


@dataclass
class Config:
    ollama: OllamaCfg = field(default_factory=OllamaCfg)
    traffic_cop: TrafficCopCfg = field(default_factory=TrafficCopCfg)
    runner: RunnerCfg = field(default_factory=RunnerCfg)


def _apply_section(obj, data: dict) -> None:
    for k, v in data.items():
        if hasattr(obj, k):
            setattr(obj, k, v)


def load_config(path: Path | None = None) -> Config:
    cfg = Config()
    p = path or CONFIG_JSON
    if p.exists():
        try:
            data = json.loads(p.read_text())
        except Exception:
            data = {}
        if isinstance(data, dict):
            if isinstance(data.get("ollama"), dict):
                _apply_section(cfg.ollama, data["ollama"])
            if isinstance(data.get("traffic_cop"), dict):
                _apply_section(cfg.traffic_cop, data["traffic_cop"])
            if isinstance(data.get("runner"), dict):
                _apply_section(cfg.runner, data["runner"])
    # env overrides (handy for one-off A/B without editing the file)
    if os.environ.get("CENTAUR_MODEL"):
        cfg.ollama.model = os.environ["CENTAUR_MODEL"]
    if os.environ.get("CENTAUR_OLLAMA_HOST"):
        cfg.ollama.host = os.environ["CENTAUR_OLLAMA_HOST"]
    return cfg
