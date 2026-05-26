# LIMINA First-Wave RFQ Dispatch Cockpit

This report combines the H-A and ZRC Phase A RFQ send surfaces. It is not measured evidence.

**Status:** `first_wave_rfq_dispatch_cockpit_ready_for_manual_send`
**Tracks:** 2
**Vendor rows:** 8
**Ready to send:** 8
**Missing message files:** 0
**Missing bundles:** 0
**Confirmation files present:** 0
**Reply files present:** 0
**HTML:** `reports/limina_first_wave_rfq_dispatch_cockpit.html`

## Track Status

- H-A cockpit: `h_a_rfq_send_cockpit_ready_for_manual_send`; archive=`h_a_rfq_dispatch_archive_ready`
- ZRC Phase A cockpit: `zrc_phase_a_rfq_send_cockpit_ready_for_manual_send`; archive=`zrc_phase_a_rfq_dispatch_archive_ready`

## Dispatch Rows

| Track | Order | Vendor | Send status | Dispatch | Message | Bundle | Confirmation path | Reply path |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| NHI-PEDOT H-A | 1 | Materials Metric | `ready_to_send` | `ready_for_manual_dispatch` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/materials_metric_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/materials_metric_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/materials_metric_send_confirmation.txt` | `data/rfq_reply_files/h_a/materials_metric_reply.txt` |
| NHI-PEDOT H-A | 2 | The Osmolality Lab | `ready_to_send` | `ready_for_manual_dispatch` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/the_osmolality_lab_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/the_osmolality_lab_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/the_osmolality_lab_send_confirmation.txt` | `data/rfq_reply_files/h_a/the_osmolality_lab_reply.txt` |
| NHI-PEDOT H-A | 3 | Cambridge Polymer Group | `ready_to_send` | `ready_for_manual_dispatch` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/cambridge_polymer_group_hydrogel_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/cambridge_polymer_group_hydrogel_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/cambridge_polymer_group_hydrogel_send_confirmation.txt` | `data/rfq_reply_files/h_a/cambridge_polymer_group_hydrogel_reply.txt` |
| NHI-PEDOT H-A | 4 | MilliporeSigma Cell Culture Media Stability and Testing Services | `ready_to_send` | `ready_for_manual_dispatch` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/sigmaaldrich_media_testing_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/sigmaaldrich_media_testing_send_confirmation.txt` | `data/rfq_reply_files/h_a/sigmaaldrich_media_testing_reply.txt` |
| ZRC-ND Phase A | 1 | Pacific BioLabs Physicochemical Properties Testing | `ready_for_manual_dispatch` | `ready_for_manual_dispatch` | `data/zrc_nd_phase_a_rfq_outbox/emails/pacific_biolabs_physicochemical_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/pacific_biolabs_physicochemical_zrc_nd_phase_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/zrc_phase_a/pacific_biolabs_physicochemical_send_confirmation.txt` | `data/rfq_reply_files/zrc_phase_a/pacific_biolabs_physicochemical_reply.txt` |
| ZRC-ND Phase A | 2 | MilliporeSigma Cell Culture Media Stability and Testing Services | `ready_for_manual_dispatch` | `ready_for_manual_dispatch` | `data/zrc_nd_phase_a_rfq_outbox/emails/sigmaaldrich_media_testing_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_zrc_nd_phase_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/zrc_phase_a/sigmaaldrich_media_testing_send_confirmation.txt` | `data/rfq_reply_files/zrc_phase_a/sigmaaldrich_media_testing_reply.txt` |
| ZRC-ND Phase A | 3 | The Osmolality Lab | `ready_for_manual_dispatch` | `ready_for_manual_dispatch` | `data/zrc_nd_phase_a_rfq_outbox/emails/the_osmolality_lab_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/the_osmolality_lab_zrc_nd_phase_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/zrc_phase_a/the_osmolality_lab_send_confirmation.txt` | `data/rfq_reply_files/zrc_phase_a/the_osmolality_lab_reply.txt` |
| ZRC-ND Phase A | 4 | Jordi Labs Analytical Testing | `ready_for_manual_dispatch` | `ready_for_manual_dispatch` | `data/zrc_nd_phase_a_rfq_outbox/emails/jordi_labs_el_polymer_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/jordi_labs_el_polymer_zrc_nd_phase_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/zrc_phase_a/jordi_labs_el_polymer_send_confirmation.txt` | `data/rfq_reply_files/zrc_phase_a/jordi_labs_el_polymer_reply.txt` |

## Commands After Real Files Are Saved

- `python3 scripts/process_limina_first_wave_post_dispatch.py`
- `python3 scripts/run_limina_iteration.py`

## Boundary

This cockpit is dispatch scaffolding only. It does not send RFQs, create send confirmations, create measurements, select providers, authorize execution, or support any material suitability claim.
