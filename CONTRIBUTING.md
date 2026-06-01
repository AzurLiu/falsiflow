# Contributing

Falsiflow v0.2.0 is intentionally small. Contributions should improve the core
claim gate, not reintroduce launch, demo, discovery, MCP, or template-platform
systems.

Before opening a PR, run:

```bash
python3 -m py_compile falsiflow/core.py falsiflow/bundle.py falsiflow/claim_check.py falsiflow/cli.py scripts/falsiflow.py scripts/falsiflow_tests/regress_falsiflow_core.py
python3 scripts/falsiflow_tests/regress_falsiflow_core.py
python3 -m build
```

Every behavior change should preserve this boundary: `claim_ready` means the
configured evidence package passed, not that the underlying claim is true.
