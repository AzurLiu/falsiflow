# NHI-PEDOT H-A Measurement Merge

**Raw measurements:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_raw_measurements_template.csv`
**Output active runs:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_runs_active.csv`

| Metric | Count |
| --- | ---: |
| Raw rows | 228 |
| Applied values | 0 |
| Blank values skipped | 228 |
| Missing run_id rows skipped | 0 |
| Unknown run_id rows skipped | 0 |
| Unresolved targets | 0 |
| Unit warnings | 0 |
| Operator updates | 0 |
| Date updates | 0 |
| Source-file updates | 0 |
| Synthetic marker propagations | 0 |
| Output rows | 12 |

## Output Provenance

- Measured rows: 0
- Placeholder rows: 12
- Synthetic rows: 0
- Claimable measurement source: `False`

## Next Step

Run intake QC on the active runs file:

```bash
python3 scripts/qc_nhi_pedot_h_a_intake.py --runs /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_runs_active.csv
```
