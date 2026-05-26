# LIMINA Smoke Capture Tranche

This is a small real-measurement tranche for pipeline rehearsal and early red flags. It is not a material suitability claim.

**Status:** `smoke_capture_tranche_ready`
**Tasks:** 172
**H-A smoke runs:** 6
**ZRC-ND smoke runs:** 4
**Local/record tasks:** 152
**Outsource-preferred tasks:** 20

## Generated Files

| File | Purpose |
| --- | --- |
| `data/limina_smoke_capture_tasks.csv` | Smoke-only task table. |
| `data/nhi_pedot_h_a_smoke_local_capture_template.csv` | H-A local/record smoke rows. |
| `data/nhi_pedot_h_a_smoke_osmolality_outsource_template.csv` | H-A osmolality smoke rows. |
| `data/zrc_nd_phase_a_smoke_local_capture_template.csv` | ZRC-ND local/record smoke rows. |
| `data/zrc_nd_phase_a_smoke_osmolality_outsource_template.csv` | ZRC-ND osmolality smoke rows. |

## Entry Counts

| Template | Rows |
| --- | ---: |
| H-A local/record long-form rows | 102 |
| H-A osmolality outsource rows | 12 |
| ZRC-ND local/record wide rows | 4 |
| ZRC-ND osmolality outsource rows | 4 |

## Smoke Preflight

```bash
python3 scripts/preflight_limina_local_capture.py --tasks data/limina_smoke_capture_tasks.csv --h-a-local data/nhi_pedot_h_a_smoke_local_capture_template.csv --h-a-outsource data/nhi_pedot_h_a_smoke_osmolality_outsource_template.csv --zrc-local data/zrc_nd_phase_a_smoke_local_capture_template.csv --zrc-outsource data/zrc_nd_phase_a_smoke_osmolality_outsource_template.csv --json-out data/limina_smoke_capture_preflight.json --report reports/limina_smoke_capture_preflight.md
```

## Boundary

Passing this smoke tranche only proves the data pipeline and may reveal early red flags. It cannot satisfy the final material-discovery objective.
