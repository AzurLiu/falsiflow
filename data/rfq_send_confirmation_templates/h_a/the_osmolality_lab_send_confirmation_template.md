# The Osmolality Lab H-A RFQ Send Confirmation Notes

This is a planning template only. Do not cite this file as `send_confirmation_source_file`.

After a real email or web-form submission, save the original sent-email export, form confirmation page, PDF, or screenshot to:

`data/rfq_send_confirmation_files/h_a/the_osmolality_lab_send_confirmation.txt`

The intake script can fill the matching row in `data/nhi_pedot_h_a_rfq_send_log.csv` when the saved confirmation proves the expected bundle.
Use these fields if manual review is needed:

- `candidate_id`: `the_osmolality_lab`
- `send_status`: `sent`, `emailed`, `submitted`, or `form_submitted`
- `sent_at`: ISO timestamp or date of the actual submission
- `sent_by`: human sender/account
- `send_method`: `email_or_contact_form`
- `recipient_or_form`: `info@osmolab.com`
- `message_id_or_confirmation`: message ID, ticket ID, quote request ID, or form confirmation text
- `send_confirmation_source_file`: `data/rfq_send_confirmation_files/h_a/the_osmolality_lab_send_confirmation.txt`
- `sent_bundle_sha256`: `b89d68822a7e42b1d387d3b239b6cee86140d3b188e1a3ae14e92792094c023a`

After saving the real confirmation, run:

`python3 scripts/intake_limina_rfq_send_confirmations.py --profile h_a`

Then run:

`python3 scripts/apply_limina_rfq_send_log.py --profile h_a`

Do not mark the row sent until the real submission has happened.
