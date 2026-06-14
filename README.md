# multi-agent-test-gen

**Point a fleet of AI agents at a Python module; get back a pytest suite that
actually runs green.** Generation, adversarial critique, synthesis, and
*verification* — the agents don't just write tests, they prove they pass.

```
module.py
    |
    +--> generator x N   parallel — each drafts a candidate suite
    +--> critic          skeptic — finds gaps & weak assertions across drafts
    +--> synthesizer      merges drafts + critique into one suite
    +--> verifier         runs pytest — keeps the result honest
```

This is the thesis in miniature: **multi-agent orchestration that ships reliable
work**, not a single prompt hoping for the best. Two decades of validation rigor,
applied to agents.

## Run it (no API key needed)

With no `ANTHROPIC_API_KEY`, it runs fully offline via a deterministic mock so you
can see the graph end-to-end:

```bash
python -m mate examples/sample_module.py
pytest
```

## Run it for real

```bash
pip install -e ".[llm]"
export ANTHROPIC_API_KEY=sk-...
python -m mate path/to/your_module.py -o test_your_module.py
```

The `verified` flag (and the process exit code) tells you whether the generated
suite passed pytest against your module.

## How it works

`generate_tests()` fans `--fan` generator agents over the module in parallel, runs
a skeptical critic over all drafts, synthesizes one suite that fixes the gaps, then
executes it under pytest in a temp dir. Only a suite that runs is returned as
`verified=True`.

## License

MIT — Dan Ilushin
