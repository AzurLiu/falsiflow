# NHI-PEDOT Planned Runs

**Validation package:** `nhi_pedot_laminin_validation_v0_1`
**CSV:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_planned_runs.csv`
**Total planned rows:** 168

These rows are measurement templates, not experimental results.

## Phase Counts

| Phase | Rows |
| --- | ---: |
| H-A | 60 |
| H-B | 60 |
| H-C | 48 |

## Article Counts

| Article | Rows |
| --- | ---: |
| `challenge_nhi_pedot_high_loading` | 36 |
| `hydrogel_laminin_control` | 36 |
| `laminin_only_control` | 36 |
| `lead_nhi_pedot_low_loading` | 36 |
| `no_coating_mea_control` | 24 |

## First Decisive Batch

Start with Phase H-A rows only. If material blank, swelling, shedding, or medium-integrity gates fail, do not run H-B or H-C.

## Notes

- H-A verifies the material is not a medium-chemistry problem before live-cell exposure.
- H-B verifies PEDOT:PSS adds measurable electrochemical value after culture-medium soak.
- H-C is biological and should only start after H-A/H-B pass.
- The run IDs are deterministic so measured rows can be merged and audited across iterations.
