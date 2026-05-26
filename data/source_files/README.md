# LIMINA Source Files

Place real raw exports, photos, reports, worksheets, calibration logs, and build records here before filling `source_file` fields.

Do not use emails, quotes, verbal notes, capability claims, synthetic fixtures, or placeholder files as measured evidence.

## Allowed Roots

- `data/source_files/full/h_a`: Local instrument exports, photos, worksheets, calibration logs, and bench records for the full H-A matrix.
- `data/source_files/full/zrc_nd_phase_a`: Local records and instrument outputs for the full ZRC-ND Phase A matrix.
- `data/source_files/full/nhi_pedot_forward`: Local instrument exports, images, worksheets, and biological assay records for NHI-PEDOT H-B/H-C coupon gates.
- `data/source_files/full/nhi_pedot_long`: Long-duration MEA, neural health, stimulus-recovery, imaging, and material-integrity records for NHI-PEDOT.
- `data/source_files/full/zrc_nd_bio`: Biological assay records, imaging, MEA outputs, and worksheets for ZRC-ND conditioned-medium follow-up gates.
- `data/source_files/smoke/h_a`: Minimal source files for the smoke-tranche H-A pipeline rehearsal.
- `data/source_files/smoke/zrc_nd_phase_a`: Minimal source files for the smoke-tranche ZRC-ND pipeline rehearsal.
- `data/source_files/calibration_logs`: Calibration or standard-check files referenced by pH, conductivity, temperature, osmometer, image, mass, or dimension records.
- `data/source_files/bench_records`: Bench logs, pipetting worksheets, chain-of-custody exports, and operator worksheets.
- `data/source_files/build_records`: Recipe records, supplier CoAs, sample labels, coating logs, and build sheets.
- `data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports`: Original external lab exports, reports, images, and worksheets referenced by returned H-A rows.
- `data/zrc_nd_phase_a_vendor_return_inbox/external_lab_exports`: Original external lab exports, reports, images, and worksheets referenced by returned ZRC-ND rows.

Run `python3 scripts/preflight_limina_local_capture.py` after entries are filled.
