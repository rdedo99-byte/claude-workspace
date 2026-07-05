"""Ollama HTTP client — one-shot, stateless (Protocol B), VRAM-safe (Protocol A).

Uses ``POST /api/generate`` (no conversation history). Prefers httpx; falls back to stdlib
urllib so the only hard pip dependency is ``mcp``. When CPU is forced we set
``options.num_gpu = 0``; ``keep_alive: 0`` means Qwen never holds VRAM after a call.
"""
from __future__ import annotations

import json


class OllamaError(RuntimeError):
    pass


def _post(url: str, body: dict, timeout_s: int) -> dict:
    try:
        import httpx  # type: ignore
    except ImportError:
        httpx = None
    if httpx is not None:
        try:
            r = httpx.post(url, json=body, timeout=timeout_s)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001 — normalize transport errors
            raise OllamaError(f"httpx POST {url} failed: {e!r}") from e
    # stdlib fallback
    import urllib.error
    import urllib.request
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        raise OllamaError(f"urllib POST {url} failed: {e!r}") from e


def ping(cfg) -> bool:
    """True if the Ollama server answers /api/tags."""
    url = f"{cfg.ollama.host}/api/tags"
    try:
        try:
            import httpx  # type: ignore
            return httpx.get(url, timeout=5).status_code == 200
        except ImportError:
            import urllib.request
            with urllib.request.urlopen(url, timeout=5) as resp:
                return getattr(resp, "status", 200) == 200
    except Exception:
        return False


def generate(cfg, prompt: str, force_cpu: bool, timeout_s: int | None = None) -> str:
    """One-shot completion. Returns the raw 'response' string (may contain <think>…</think>
    and markdown fences — see extract.py). Raises OllamaError on transport failure."""
    options = {"temperature": cfg.ollama.temperature}
    if force_cpu:
        options["num_gpu"] = 0          # zero GPU layers => pure CPU
    # GPU mode frees VRAM immediately (keep_alive 0); CPU mode may hold the model in RAM (safe)
    # so a 3-attempt self-heal loop doesn't reload the 17 GB weights each time.
    keep_alive = cfg.ollama.keep_alive_cpu if force_cpu else cfg.ollama.keep_alive
    body = {
        "model": cfg.ollama.model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": keep_alive,
        "options": options,
    }
    url = f"{cfg.ollama.host}/api/generate"
    data = _post(url, body, timeout_s or cfg.ollama.timeout_s)
    return data.get("response", "")
