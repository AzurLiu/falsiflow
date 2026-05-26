# LIMINA RFQ Send Confirmation Intake Regression

**Status:** `pass`

## Checks

- `no_files_waits`: true
- `no_files_send_log_stays_pending`: true
- `valid_eml_applies_one_row`: true
- `valid_eml_matches_expected_bundle`: true
- `valid_eml_send_log_applies_tracker_date`: true
- `valid_eml_records_expected_bundle_hash`: true
- `wrong_bundle_needs_review`: true
- `wrong_bundle_does_not_apply_tracker`: true
- `text_confirmation_needs_manual_review`: true
- `text_confirmation_does_not_mark_sent`: true

## Boundary

This regression uses temporary outreach fixtures only. It does not create material evidence.
