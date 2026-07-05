"""CLI adapter over core.* — lets the whole pipeline be exercised with the Bash tool BEFORE
any MCP registration. Every subcommand prints the same JSON the MCP tool returns.

Examples:
  python -m centaur.cli vram-status
  python -m centaur.cli ping
  python -m centaur.cli codegen-run --spec-file /tmp/spec.txt \
      --interpreter "python3" \
      --freeze-path /abs/reader.py --test-args "--test" --run-args "/abs/input_dir"
  python -m centaur.cli edit --file /abs/foo.py --spec-file /tmp/edit.txt [--allow-apply]
"""
from __future__ import annotations

import argparse
import json
import sys

from . import core


def _read_spec(a) -> str:
    if getattr(a, "spec", None):
        return a.spec
    if getattr(a, "spec_file", None):
        with open(a.spec_file) as fh:
            return fh.read()
    return ""


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="centaur")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("vram-status", help="Traffic-Cop resource gate")
    sub.add_parser("ping", help="is the Ollama server up?")

    g = sub.add_parser("codegen-run", help="self-healing generate+run (Protocol C)")
    g.add_argument("--spec")
    g.add_argument("--spec-file")
    g.add_argument("--interpreter", default="python3")
    g.add_argument("--freeze-path", required=True)
    g.add_argument("--test-args", default="--test")
    g.add_argument("--run-args", default="")
    g.add_argument("--force-cpu", choices=["true", "false"], default=None)
    g.add_argument("--timeout-s", type=int, default=None)
    g.add_argument("--regenerate", action="store_true")
    g.add_argument("--summarize", action="store_true")

    e = sub.add_parser("edit", help="delta Search&Replace edit (Protocol D)")
    e.add_argument("--file", required=True)
    e.add_argument("--spec")
    e.add_argument("--spec-file")
    e.add_argument("--allow-apply", action="store_true",
                   help="apply if not a protected file (default: return diff only)")

    s = sub.add_parser("summarize", help="mini-summary of verbose output (Qwen)")
    s.add_argument("--text")
    s.add_argument("--text-file")
    s.add_argument("--instruction", default="Summarize in ONE short line, no preamble.")

    a = p.parse_args(argv)

    if a.cmd == "vram-status":
        out = core.vram_status()
    elif a.cmd == "ping":
        from . import config, ollama_client
        out = {"up": ollama_client.ping(config.load_config())}
    elif a.cmd == "codegen-run":
        fc = None if a.force_cpu is None else (a.force_cpu == "true")
        out = core.qwen_codegen_run(
            spec=_read_spec(a), interpreter=a.interpreter, freeze_path=a.freeze_path,
            test_args=a.test_args, run_args=a.run_args, force_cpu=fc,
            timeout_s=a.timeout_s, regenerate=a.regenerate, summarize=a.summarize,
        )
    elif a.cmd == "edit":
        out = core.qwen_edit(file=a.file, delta_spec=_read_spec(a), protected=not a.allow_apply)
    elif a.cmd == "summarize":
        text = a.text or (open(a.text_file).read() if a.text_file else "")
        out = core.qwen_summarize(text=text, instruction=a.instruction)
    else:  # pragma: no cover
        p.error("unknown command")
        return 2

    print(json.dumps(out, indent=2, default=str))
    return 0 if not (isinstance(out, dict) and out.get("error")) else 1


if __name__ == "__main__":
    sys.exit(main())
