# The Osmolality Lab ZRC-ND Phase A RFQ Send Confirmation Notes

This is a planning template only. Do not cite this file as `send_confirmation_source_file`.

After a real email or web-form submission, save the original sent-email export, form confirmation page, PDF, or screenshot to:

`data/rfq_send_confirmation_files/zrc_phase_a/the_osmolality_lab_send_confirmation.txt`

Use these fields if manual review is needed:

- `candidate_id`: `the_osmolality_lab`
- `send_status`: `sent`, `emailed`, `submitted`, or `form_submitted`
- `sent_at`: ISO timestamp or date of the actual submission
- `sent_by`: human sender/account
- `send_method`: `email_or_contact_form`
- `recipient_or_form`: `info@osmolab.com`
- `message_id_or_confirmation`: message ID, ticket ID, quote request ID, or form confirmation text
- `send_confirmation_source_file`: `data/rfq_send_confirmation_files/zrc_phase_a/the_osmolality_lab_send_confirmation.txt`
- `sent_bundle_sha256`: `29125cb54ad2a21b1b161a4ecf22ec430b6c4109d8c208c4bd931a607373406f`

Then run:

`python3 scripts/apply_limina_rfq_send_log.py --profile zrc_phase_a`

Do not mark the row sent until the real submission has happened.
