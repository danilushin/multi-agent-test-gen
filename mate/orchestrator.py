"""The agent graph: generate -> critique -> synthesize -> verify.

    module.py
        |
        +--> generator x N   (parallel: each drafts a test suite)
        |
        +--> critic          (finds gaps / weak assertions across the drafts)
        |
        +--> synthesizer      (merges drafts + critic notes into one suite)
        |
        +--> verifier         (actually runs pytest on the result)

Returns a TestGenResult with the final source and whether it ran green.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .agents import LLM, default_llm


@dataclass
class TestGenResult:
    source: str
    verified: bool
    pytest_output: str


_GEN = """You are a test engineer. Write a pytest suite for this module.
Return ONLY Python code.

MODULE:
{module}
"""

_CRITIQUE = """You are a skeptical reviewer. List concrete gaps and weak assertions
in these candidate test suites for the module. Be specific.

MODULE:
{module}

CANDIDATES:
{candidates}
"""

_SYNTH = """Merge the candidate suites into ONE strong pytest file, fixing the gaps
the reviewer found. Return ONLY Python code.

MODULE:
{module}

CANDIDATES:
{candidates}

REVIEWER NOTES:
{critique}
"""


def _strip_fences(text: str) -> str:
    """Pull code out of a ```...``` block if the model wrapped it."""
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        # the code is the first fenced block (parts[1]); drop a leading 'python'
        block = parts[1] if len(parts) >= 2 else t
        block = block.lstrip()
        if block.lower().startswith("python"):
            block = block[len("python"):]
        return block.strip()
    return t


def generate_tests(module_src: str, *, llm: LLM | None = None, fan: int = 3) -> TestGenResult:
    """Run the full generate -> critique -> synthesize -> verify graph."""
    llm = llm or default_llm()

    # 1) fan out: N independent draft suites (parallel)
    def _draft(_i):
        return _strip_fences(llm.complete(_GEN.format(module=module_src)))

    with ThreadPoolExecutor(max_workers=fan) as pool:
        candidates = list(pool.map(_draft, range(fan)))
    candidates_block = "\n\n# --- candidate ---\n".join(candidates)

    # 2) critique
    critique = llm.complete(_CRITIQUE.format(module=module_src, candidates=candidates_block))

    # 3) synthesize
    final = _strip_fences(
        llm.complete(
            _SYNTH.format(module=module_src, candidates=candidates_block, critique=critique)
        )
    )

    # 4) verify: actually run pytest
    verified, output = _run_pytest(module_src, final)
    return TestGenResult(source=final, verified=verified, pytest_output=output)


def _run_pytest(module_src: str, test_src: str) -> tuple[bool, str]:
    """Write module + tests to a temp dir and run pytest; return (passed, output)."""
    with tempfile.TemporaryDirectory() as d:
        dpath = Path(d)
        (dpath / "target.py").write_text(module_src, encoding="utf-8")
        body = "from target import *  # noqa: F401,F403\n\n" + test_src
        (dpath / "test_generated.py").write_text(body, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(dpath)],
            capture_output=True,
            text=True,
            cwd=d,
        )
        return proc.returncode == 0, (proc.stdout + proc.stderr)
