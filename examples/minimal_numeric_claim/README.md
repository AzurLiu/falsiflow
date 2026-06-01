# Minimal numeric claim

This is the smallest Falsiflow shape: one project config, one evidence CSV,
one source file, and one command.

```bash
CFG=project.json
falsiflow check --config "$CFG" --evidence evidence_placeholder.csv
falsiflow check --config "$CFG" --evidence evidence_blocked.csv
falsiflow check --config "$CFG" --evidence evidence_ready.csv --strict
```

The first run is blocked because the evidence contains a placeholder. The
second is blocked because the measured lift misses the threshold. The third is
ready because the source-backed value clears the configured gate.
