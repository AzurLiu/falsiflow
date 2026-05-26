# LIMINA RFQ Reply Intake Regression

**Status:** `pass`

## Checks

- `no_files_waits`: true
- `no_files_reply_log_stays_pending`: true
- `valid_eml_registers_one_row`: true
- `valid_eml_marks_clarification_for_review`: true
- `valid_eml_apply_updates_tracker_but_not_selection_fields`: true
- `unverified_send_does_not_apply`: true
- `text_reply_needs_manual_review`: true
- `text_reply_does_not_mark_received`: true

## Boundary

This regression uses temporary RFQ reply fixtures only. It does not create material evidence or select providers.
