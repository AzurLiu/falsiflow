# ZRC-ND Phase A Quote Tracker

This tracker is for RFQ responses. It is not measured evidence.

**Status:** `pending_outreach`
**Active candidate:** `limina_zrc_nd_v0_1`
**Tracker CSV:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_quote_tracker.csv`
**Rows:** 4

## Decision Rules

- Reject any response that cannot preserve run_id-level raw data.
- Prefer one provider only if it covers pH, osmolality, conductivity, and appearance without losing source-file provenance.
- Use split scope if pH/osmolality and conductivity must be produced by different providers, but keep the same run_id labels.
- Do not proceed without CSV schema acceptance or an explicit mapping back to the LIMINA Phase A template.
- Do not treat quote responses or supplier guidance as material evidence; only returned measured rows can advance gates.
- Rerunning this tracker preserves existing contact dates, replies, decisions, and notes by candidate_id.

## Pending Vendors

| Candidate | Vendor | Decision | Notes |
| --- | --- | --- | --- |
| `pacific_biolabs_physicochemical` | Pacific BioLabs Physicochemical Properties Testing | `pending_outreach` | - |
| `sigmaaldrich_media_testing` | MilliporeSigma Cell Culture Media Stability and Testing Services | `pending_outreach` | - |
| `the_osmolality_lab` | The Osmolality Lab | `pending_outreach` | - |
| `jordi_labs_el_polymer` | Jordi Labs Analytical Testing | `pending_outreach` | - |

## Disqualifiers

- Only returns pooled averages, certificates, or narrative feasibility opinions.
- Will not preserve run_id, sample_event, and target-field mapping.
- Cannot return raw exports, instrument reports, or traceable source files.
- Requires changing article identity, timepoints, membrane material, or control rows without a deviation log.
- Treats quote, supplier support, or vendor capability claims as final material suitability evidence.
