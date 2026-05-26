# ZRC-ND Phase A RFQ Send Cockpit

This cockpit collects the files needed for manual first-wave ZRC-ND Phase A RFQ dispatch. It is not measured evidence.

**Status:** `zrc_phase_a_rfq_send_cockpit_ready_for_manual_send`
**Vendor rows:** 4
**Ready to use:** 4
**Missing email text:** 0
**Missing bundles:** 0
**Dispatch manifest:** `zrc_phase_a_rfq_dispatch_manifest_ready`; ready=4; blocked=0
**Dispatch archive:** `zrc_phase_a_rfq_dispatch_archive_ready`; archive=`data/zrc_nd_phase_a_rfq_dispatch_archive/zrc_nd_phase_a_rfq_dispatch_archive.zip`; sha256=`2a2ca661089a7d5ae0a91205968a383b98d7fbd90cea45c46fd4f6c8eab917d7`
**Confirmation files present:** 0
**Reply files present:** 0
**Confirmation entry sheet:** `zrc_phase_a_rfq_send_confirmation_entry_sheet_waiting_for_confirmation_files`; rows=4; ready=0; blocked=0
**Confirmation entry apply:** `zrc_phase_a_rfq_send_confirmation_entry_apply_no_apply_rows`; apply_rows=0; applied=0; blocked=0
**Reply action pack:** `zrc_phase_a_rfq_reply_action_pack_waiting_for_send`; waiting_send=4; awaiting_reply=0; ready_apply=0
**HTML:** `reports/zrc_nd_phase_a_rfq_send_cockpit.html`

## Send Rows

| Order | Vendor | Status | Dispatch | Reply action | Recipient/Form | Email | Bundle | Confirmation | Reply file |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Pacific BioLabs Physicochemical Properties Testing | `ready_for_manual_dispatch` | `ready_for_manual_dispatch` | `waiting_for_rfq_send` | `https://pacificbiolabs.com/contact/` | `data/zrc_nd_phase_a_rfq_outbox/emails/pacific_biolabs_physicochemical_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/pacific_biolabs_physicochemical_zrc_nd_phase_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/zrc_phase_a/pacific_biolabs_physicochemical_send_confirmation.txt` | `data/rfq_reply_files/zrc_phase_a/pacific_biolabs_physicochemical_reply.txt` |
| 2 | MilliporeSigma Cell Culture Media Stability and Testing Services | `ready_for_manual_dispatch` | `ready_for_manual_dispatch` | `waiting_for_rfq_send` | `PSTechService@milliporesigma.com` | `data/zrc_nd_phase_a_rfq_outbox/emails/sigmaaldrich_media_testing_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_zrc_nd_phase_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/zrc_phase_a/sigmaaldrich_media_testing_send_confirmation.txt` | `data/rfq_reply_files/zrc_phase_a/sigmaaldrich_media_testing_reply.txt` |
| 3 | The Osmolality Lab | `ready_for_manual_dispatch` | `ready_for_manual_dispatch` | `waiting_for_rfq_send` | `info@osmolab.com` | `data/zrc_nd_phase_a_rfq_outbox/emails/the_osmolality_lab_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/the_osmolality_lab_zrc_nd_phase_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/zrc_phase_a/the_osmolality_lab_send_confirmation.txt` | `data/rfq_reply_files/zrc_phase_a/the_osmolality_lab_reply.txt` |
| 4 | Jordi Labs Analytical Testing | `ready_for_manual_dispatch` | `ready_for_manual_dispatch` | `waiting_for_rfq_send` | `info@jordilabs.com` | `data/zrc_nd_phase_a_rfq_outbox/emails/jordi_labs_el_polymer_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/jordi_labs_el_polymer_zrc_nd_phase_a_rfq_bundle.zip` | `data/rfq_send_confirmation_files/zrc_phase_a/jordi_labs_el_polymer_send_confirmation.txt` | `data/rfq_reply_files/zrc_phase_a/jordi_labs_el_polymer_reply.txt` |

## Commands After Saving Real Files

- `python3 scripts/intake_limina_rfq_send_confirmations.py --profile zrc_phase_a`
- `python3 scripts/render_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py`
- `python3 scripts/apply_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py`
- `python3 scripts/apply_limina_rfq_send_log.py --profile zrc_phase_a`
- `python3 scripts/intake_limina_rfq_replies.py --profile zrc_phase_a`
- `python3 scripts/apply_limina_rfq_reply_log.py --profile zrc_phase_a`
- `python3 scripts/evaluate_zrc_nd_phase_a_quote_replies.py`
- `python3 scripts/run_limina_iteration.py`

## Boundary

This cockpit is logistics scaffolding only. It does not send email, create measurement evidence, select a provider, authorize execution, or advance material suitability gates.
