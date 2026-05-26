# NHI-PEDOT H-A RFQ Send Cockpit

This cockpit collects the files needed for the manual first-wave RFQ send. It is not measured evidence.

**Status:** `h_a_rfq_send_cockpit_ready_for_manual_send`
**Vendor rows:** 4
**Ready to use:** 4
**Missing EML drafts:** 0
**Missing bundles:** 0
**EML integrity:** `h_a_rfq_eml_integrity_ready`; pass=4; fail=0
**Dispatch manifest:** `h_a_rfq_dispatch_manifest_ready`; ready=4; blocked=0
**Confirmation files present:** 0
**Reply files present:** 0
**HTML:** `reports/nhi_pedot_h_a_rfq_send_cockpit.html`

## Send Rows

| Order | Vendor | Status | Dispatch | EML integrity | Recipient/Form | EML | Bundle | Confirmation | Reply file |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Materials Metric | `ready_to_send` | `ready_for_manual_dispatch` | `pass` | `info@materialsmetric.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/materials_metric_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/materials_metric_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/materials_metric_send_confirmation.txt` | `data/rfq_reply_files/h_a/materials_metric_reply.txt` |
| 2 | The Osmolality Lab | `ready_to_send` | `ready_for_manual_dispatch` | `pass` | `info@osmolab.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/the_osmolality_lab_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/the_osmolality_lab_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/the_osmolality_lab_send_confirmation.txt` | `data/rfq_reply_files/h_a/the_osmolality_lab_reply.txt` |
| 3 | Cambridge Polymer Group | `ready_to_send` | `ready_for_manual_dispatch` | `pass` | `info@campoly.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/cambridge_polymer_group_hydrogel_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/cambridge_polymer_group_hydrogel_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/cambridge_polymer_group_hydrogel_send_confirmation.txt` | `data/rfq_reply_files/h_a/cambridge_polymer_group_hydrogel_reply.txt` |
| 4 | MilliporeSigma Cell Culture Media Stability and Testing Services | `ready_to_send` | `ready_for_manual_dispatch` | `pass` | `PSTechService@milliporesigma.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/sigmaaldrich_media_testing_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/sigmaaldrich_media_testing_send_confirmation.txt` | `data/rfq_reply_files/h_a/sigmaaldrich_media_testing_reply.txt` |

## Immediate Commands

- `python3 scripts/intake_limina_rfq_send_confirmations.py --profile h_a`
- `python3 scripts/apply_limina_rfq_send_log.py --profile h_a`
- `python3 scripts/intake_limina_rfq_replies.py --profile h_a`
- `python3 scripts/apply_limina_rfq_reply_log.py --profile h_a`
- `python3 scripts/run_limina_iteration.py`

## Boundary

This cockpit is logistics scaffolding only. It does not send email, create measurement evidence, select a provider, authorize execution, or advance material suitability gates.
