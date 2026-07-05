"""Protocol A — Traffic Cop.

Before any Ollama dispatch, decide whether Qwen may touch the GPU. The PRIMARY gate is
``training_alive`` (a live training saturates a 16 GB card and one PhysX spike = OOM), not the
raw VRAM %. If no training is detected we fall back to the VRAM threshold. When nvidia-smi is
unavailable we choose CPU conservatively.
"""
from __future__ import annotations

import subprocess


def _vram():
    """Return (used_mb, total_mb) for GPU 0, or (None, None) if nvidia-smi is unavailable."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL, timeout=15,
        ).strip()
        if not out:
            return None, None
        line = out.splitlines()[0]                      # first GPU
        used_s, total_s = line.split(",")               # real format: "13803, 16303"
        return int(used_s.strip()), int(total_s.strip())
    except Exception:
        return None, None


def _training_alive(match: str) -> bool:
    """pgrep -f <match>: a path fragment (e.g. 'myproj/train.py') avoids matching a bare
    'train.py' in an unrelated command line. pgrep excludes itself; exit 0 == found."""
    try:
        return subprocess.run(
            ["pgrep", "-f", match],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
        ).returncode == 0
    except Exception:
        return False


def status(cfg) -> dict:
    used, total = _vram()
    alive = _training_alive(cfg.traffic_cop.train_match)
    threshold = cfg.traffic_cop.vram_pct_threshold
    pct = (used / total) if (used is not None and total) else None

    if alive:
        mode = "cpu"
        reason = f"training alive (pgrep '{cfg.traffic_cop.train_match}')"
        if pct is not None:
            reason += f"; VRAM {pct:.0%}"
    elif pct is None:
        mode = "cpu"
        reason = "nvidia-smi unavailable -> conservative CPU"
    elif pct > threshold:
        mode = "cpu"
        reason = f"VRAM {pct:.0%} > {threshold:.0%} threshold"
    else:
        mode = "gpu"
        reason = f"GPU free ({pct:.0%} used), no training"

    return {
        "training_alive": alive,
        "vram_used_mb": used,
        "vram_total_mb": total,
        "vram_pct": round(pct, 3) if pct is not None else None,
        "recommended_mode": mode,
        "reason": reason,
    }
