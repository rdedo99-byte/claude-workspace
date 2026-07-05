"""FastMCP adapter — thin wrapper over core.*. Registered once, globally, as the `centaur`
MCP server so every project inherits it. Requires ``mcp>=1.28,<2`` (the FastMCP API).

Run standalone:  python -m centaur.server   (stdio transport)
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import core

mcp = FastMCP("centaur")


@mcp.tool()
def vram_status() -> dict:
    """Report GPU/training state so Opus can choose CPU vs GPU for Qwen.

    Returns {training_alive, vram_used_mb, vram_total_mb, vram_pct, recommended_mode:
    'cpu'|'gpu', reason}. When a training is alive, mode is forced to 'cpu'.
    """
    return core.vram_status()


@mcp.tool()
def qwen_codegen_run(spec: str, interpreter: str = "python3", freeze_path: str = "",
                     test_args: str = "--test", run_args: str = "",
                     force_cpu: bool | None = None, max_attempts: int = 3,
                     timeout_s: int | None = None, regenerate: bool = False,
                     summarize: bool = False) -> dict:
    """Self-healing generate→smoke-test→freeze→run (HYBRID: the spec carries all intent; Qwen
    only writes/runs the script). If freeze_path already exists with a matching spec-hash (and
    not regenerate), the LLM is skipped and the script runs natively.

    interpreter: e.g. "python3" or a project's custom runner script (allow-listed in config.json).
    freeze_path: absolute path where the validated script is persisted.
    force_cpu:   None => auto (Traffic Cop). Set True to force CPU-only Qwen.
    Returns {frozen_path, generated, attempts, exit_code, stdout, stderr, mini_summary, mode}
    or {error, ...}. Judgment on the output stays in Opus.
    """
    return core.qwen_codegen_run(
        spec=spec, interpreter=interpreter, freeze_path=freeze_path, test_args=test_args,
        run_args=run_args, force_cpu=force_cpu, max_attempts=max_attempts, timeout_s=timeout_s,
        regenerate=regenerate, summarize=summarize,
    )


@mcp.tool()
def qwen_edit(file: str, delta_spec: str, protected: bool = True) -> dict:
    """Protocol D — minimal Search&Replace edit via Qwen. Protected files (obs/action space,
    PPO/env cfg, __init__) are forced protected: the diff is returned, NEVER auto-applied.
    Returns {applied, protected, file, diff} or {error, ...}.
    """
    return core.qwen_edit(file=file, delta_spec=delta_spec, protected=protected)


@mcp.tool()
def qwen_summarize(text: str, instruction: str = "Summarize in ONE short line, no preamble.") -> dict:
    """Mini-summary of verbose/free-text output via Qwen. Returns {summary} or {error}. For
    structured (JSON) output, prefer reading it in Opus directly — don't summarize machine data.
    """
    return core.qwen_summarize(text=text, instruction=instruction)


if __name__ == "__main__":
    mcp.run(transport="stdio")
