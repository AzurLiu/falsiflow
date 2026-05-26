# MilliporeSigma Cell Culture Media Stability and Testing Services ZRC-ND Phase A RFQ Send Confirmation Notes

This is a planning template only. Do not cite this file as `send_confirmation_source_file`.

After a real email or web-form submission, save the original sent-email export, form confirmation page, PDF, or screenshot to:

`data/rfq_send_confirmation_files/zrc_phase_a/sigmaaldrich_media_testing_send_confirmation.txt`

Use these fields if manual review is needed:

- `candidate_id`: `sigmaaldrich_media_testing`
- `send_status`: `sent`, `emailed`, `submitted`, or `form_submitted`
- `sent_at`: ISO timestamp or date of the actual submission
- `sent_by`: human sender/account
- `send_method`: `service_page_or_technical_service`
- `recipient_or_form`: `PSTechService@milliporesigma.com`
- `message_id_or_confirmation`: message ID, ticket ID, quote request ID, or form confirmation text
- `send_confirmation_source_file`: `data/rfq_send_confirmation_files/zrc_phase_a/sigmaaldrich_media_testing_send_confirmation.txt`
- `sent_bundle_sha256`: `020855375daaa1e6afde37c0d84b3ecffe2ddaadb5ca88e44a02ed842ac3b8d2`

Then run:

`python3 scripts/apply_limina_rfq_send_log.py --profile zrc_phase_a`

Do not mark the row sent until the real submission has happened.
