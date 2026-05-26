# NHI-PEDOT H-A Quote Tracker

This tracker is for RFQ responses. It is not measured evidence.

**Status:** `pending_outreach`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Tracker CSV:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_quote_tracker.csv`
**Rows:** 4

## Decision Rules

- Reject any response that cannot preserve run_id-level raw data.
- Prefer one integrated provider only if it covers both media physicochemical and coupon physical fields.
- Use a split-scope pair if media tests and coupon imaging/physical scoring are stronger separately.
- Do not proceed without CSV or bundle-entry schema acceptance and a clear mapping back to LIMINA run_id-level rows.
- Do not treat quote responses as material evidence; only returned measured rows can advance gates.
- Rerunning this tracker preserves existing contact dates, replies, decisions, and notes by candidate_id.

## Pending Vendors

| Candidate | Vendor | Decision | Notes |
| --- | --- | --- | --- |
| `materials_metric` | Materials Metric | `pending_outreach` | - |
| `the_osmolality_lab` | The Osmolality Lab | `pending_outreach` | - |
| `cambridge_polymer_group_hydrogel` | Cambridge Polymer Group | `pending_outreach` | - |
| `sigmaaldrich_media_testing` | MilliporeSigma Cell Culture Media Stability and Testing Services | `pending_outreach` | - |

## Disqualifiers

- Only returns pooled averages or narrative pass/fail certificates.
- Will not preserve run_id, sample_event, and target_field mapping.
- Cannot return source files or raw exports for provenance.
- Requires replacing the requested material stack or timepoints without a documented deviation log.
- Treats vendor capability claims as final material suitability evidence.
