# Falsiflow Adapter Profiles

Adapter profiles are named column-mapping presets for `falsiflow evidence
import` and `falsiflow ingest-wide-csv`. They keep common vendor, instrument,
and lab CSV imports explicit without forcing every user to remember each
metadata-column flag.

Falsiflow still writes the same long-form evidence CSV contract documented in
[falsiflow_data_contract.md](falsiflow_data_contract.md). Profiles only choose
defaults for metadata columns and ignored columns; they do not change claim
logic, acceptance rules, source provenance checks, or bundle verification.

## Profiles

| Profile | Intended CSV Shape | Sample Column | Metadata Columns |
| --- | --- | --- | --- |
| `generic-wide` | A wide CSV with `sample_id` plus value columns. | `sample_id` | User-provided flags or constants. |
| `vendor-measurement` | External lab or vendor measurement return. | `sample` | `article`, `source_file`, `measured_at`, `vendor_contact`, `instrument_id`, `notes`. |
| `instrument-export` | Instrument export with timestamped measured columns. | `sample_id` | `candidate_id`, `raw_file`, `timestamp`, `operator`, `instrument_id`, `notes`. |
| `plate-reader` | Plate-reader style export. | `well_id` | `sample_name`, `raw_file`, `read_at`, `operator`, `plate_reader_id`, `notes`. |

## Vendor Return Example

```bash
falsiflow evidence import \
  --profile vendor-measurement \
  --input vendor_return.csv \
  --out data/falsiflow/vendor_return/evidence.csv \
  --summary-out data/falsiflow/vendor_return/import_summary.json \
  --gate-id vendor_return_gate \
  --candidate-id fallback_candidate
```

With `vendor-measurement`, Falsiflow reads `sample` as `sample_id`, `article` as
`candidate_id`, `source_file` as raw provenance, `vendor_contact` as
`operator_or_agent`, and all non-metadata columns as measured value fields.

The summary records:

- `adapter_profile`
- `adapter_profile_description`
- `adapter_settings`
- `evidence_rows`
- `skipped_rows`
- `skipped_values`

## Overrides

Profile defaults can be overridden per run:

```bash
falsiflow evidence import \
  --profile instrument-export \
  --input impedance_export.csv \
  --out data/falsiflow/impedance/evidence.csv \
  --gate-id h_b_electrical_interface \
  --candidate-id lead_article \
  --sample-id-column specimen_id \
  --measured-at-column acquired_at \
  --field eis_1khz_final_ohm
```

Use explicit `--field` values when only a subset of measured columns should
become evidence rows. Use `--exclude-column` for extra non-evidence columns
that are not part of the selected profile.

## Coverage Check

When importing against a project, include `--config` and `--coverage-out`:

```bash
falsiflow evidence import \
  --profile plate-reader \
  --input plate_reader_export.csv \
  --out data/falsiflow/plate/evidence.csv \
  --config my_project/project.json \
  --coverage-out data/falsiflow/plate/import_coverage.json \
  --gate-id bioresponse_screen \
  --candidate-id fallback_sample \
  --strict
```

`--strict` exits non-zero if required evidence rows are missing or duplicated.
The coverage artifact is the bridge between an imported CSV and a claim gate:
it tells reviewers whether the adapter produced the rows the project actually
requires.

## Boundary

Profiles are deliberately simple. They are not plugins, executable scripts, or
hidden transformation code. If a CSV shape needs calculations, row joins, or
domain-specific normalization, convert it before Falsiflow or add a reviewed
adapter with schema coverage, documentation, tests, and `release-check`
coverage.
