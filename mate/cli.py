"""CLI: ``python -m mate path/to/module.py``

Generates a verified pytest suite using the multi-agent graph. With no
``ANTHROPIC_API_KEY`` set it runs fully offline via ``MockLLM`` (deterministic
demo).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .orchestrator import generate_tests


def main(argv=None):
    ap = argparse.ArgumentParser(description="Multi-agent test-suite generator")
    ap.add_argument("module", type=Path, help="Python module to generate tests for")
    ap.add_argument("-o", "--out", type=Path, help="write the suite here (default: stdout)")
    ap.add_argument("--fan", type=int, default=3, help="number of generator agents")
    args = ap.parse_args(argv)

    src = args.module.read_text(encoding="utf-8")
    result = generate_tests(src, fan=args.fan)

    if args.out:
        args.out.write_text(result.source, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(result.source)
    print(f"\n# verified={result.verified}", file=sys.stderr)
    return 0 if result.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
