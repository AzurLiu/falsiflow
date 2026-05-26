# NHI-PEDOT H-A RFQ Send Action Pack

This pack turns the first-wave RFQ outbox into an actionable send checklist. It is not measured evidence.

**Status:** `h_a_rfq_send_action_pack_ready`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Action rows:** 4
**Ready to send:** 4
**Sent confirmations verified:** 0
**Sent rows needing confirmation file:** 0
**EML drafts ready:** 4
**CSV:** `data/nhi_pedot_h_a_rfq_send_action_queue.csv`
**Confirmation templates:** `data/rfq_send_confirmation_templates/h_a`

## Action Queue

| Order | Vendor | Status | Recipient/Form | EML draft | Email | Bundle | Confirmation file to save |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | Materials Metric | `ready_to_send` | `info@materialsmetric.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/materials_metric_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/emails/materials_metric_rfq_email.txt` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/materials_metric_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/materials_metric_send_confirmation.txt` |
| 2 | The Osmolality Lab | `ready_to_send` | `info@osmolab.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/the_osmolality_lab_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/emails/the_osmolality_lab_rfq_email.txt` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/the_osmolality_lab_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/the_osmolality_lab_send_confirmation.txt` |
| 3 | Cambridge Polymer Group | `ready_to_send` | `info@campoly.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/cambridge_polymer_group_hydrogel_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/emails/cambridge_polymer_group_hydrogel_rfq_email.txt` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/cambridge_polymer_group_hydrogel_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/cambridge_polymer_group_hydrogel_send_confirmation.txt` |
| 4 | MilliporeSigma Cell Culture Media Stability and Testing Services | `ready_to_send` | `PSTechService@milliporesigma.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/sigmaaldrich_media_testing_rfq_draft.eml` | `data/nhi_pedot_h_a_rfq_outbox/emails/sigmaaldrich_media_testing_rfq_email.txt` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_nhi_pedot_h_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/h_a/sigmaaldrich_media_testing_send_confirmation.txt` |

## After Sending

1. Save the real sent-email export, web-form confirmation, PDF, or screenshot at the listed confirmation path.
2. Run `python3 scripts/intake_limina_rfq_send_confirmations.py --profile h_a`.
3. Run `python3 scripts/apply_limina_rfq_send_log.py --profile h_a`.
4. Run `python3 scripts/run_limina_iteration.py`.

## Per-Vendor Notes

### Materials Metric

- Send method: `email_or_request_service_form`
- Recipient or form: `info@materialsmetric.com`
- EML draft: `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/materials_metric_rfq_draft.eml`
- EML draft status: `ready_to_open`
- Bundle SHA-256 to record: `6799fdef01396d5ed999a13a4de131bf1d490719369c0e4b90f81c7c73cd9d35`
- Confirmation template: `data/rfq_send_confirmation_templates/h_a/materials_metric_send_confirmation_template.md`
- Next action: Open the prepared .eml draft, review recipient/body/attached bundle, send manually, save the original confirmation, then run send-confirmation intake.

### The Osmolality Lab

- Send method: `email_or_contact_form`
- Recipient or form: `info@osmolab.com`
- EML draft: `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/the_osmolality_lab_rfq_draft.eml`
- EML draft status: `ready_to_open`
- Bundle SHA-256 to record: `b89d68822a7e42b1d387d3b239b6cee86140d3b188e1a3ae14e92792094c023a`
- Confirmation template: `data/rfq_send_confirmation_templates/h_a/the_osmolality_lab_send_confirmation_template.md`
- Next action: Open the prepared .eml draft, review recipient/body/attached bundle, send manually, save the original confirmation, then run send-confirmation intake.

### Cambridge Polymer Group

- Send method: `request_quote_form_or_email`
- Recipient or form: `info@campoly.com`
- EML draft: `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/cambridge_polymer_group_hydrogel_rfq_draft.eml`
- EML draft status: `ready_to_open`
- Bundle SHA-256 to record: `bad885c9487cfc4e33c6abda168421232f8da5b1fc2a6698b4d129453d7811a1`
- Confirmation template: `data/rfq_send_confirmation_templates/h_a/cambridge_polymer_group_hydrogel_send_confirmation_template.md`
- Next action: Open the prepared .eml draft, review recipient/body/attached bundle, send manually, save the original confirmation, then run send-confirmation intake.

### MilliporeSigma Cell Culture Media Stability and Testing Services

- Send method: `service_page_or_technical_service`
- Recipient or form: `PSTechService@milliporesigma.com`
- EML draft: `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/sigmaaldrich_media_testing_rfq_draft.eml`
- EML draft status: `ready_to_open`
- Bundle SHA-256 to record: `6950279d9e72509ba62950b8ad0ea46f1f9d4c4b3e54960054d5967bc66ea8cd`
- Confirmation template: `data/rfq_send_confirmation_templates/h_a/sigmaaldrich_media_testing_send_confirmation_template.md`
- Next action: Open the prepared .eml draft, review recipient/body/attached bundle, send manually, save the original confirmation, then run send-confirmation intake.

## Boundary

This send action pack is logistics scaffolding only. It must not be used as evidence; only real returned measurement files can advance H-A gates.
