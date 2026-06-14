import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mate.agents import MockLLM  # noqa: E402
from mate.orchestrator import generate_tests  # noqa: E402

SAMPLE = """
def add(a, b):
    return a + b

def is_even(n):
    return n % 2 == 0
"""


def test_generate_tests_offline_runs_green():
    result = generate_tests(SAMPLE, llm=MockLLM(), fan=2)
    assert "def test_add_runs" in result.source
    assert "def test_is_even_runs" in result.source
    assert result.verified, result.pytest_output


def test_mockllm_handles_no_functions():
    result = generate_tests("x = 1\n", llm=MockLLM(), fan=1)
    assert result.verified, result.pytest_output
