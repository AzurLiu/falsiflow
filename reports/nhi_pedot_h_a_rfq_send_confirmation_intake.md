# NHI-PEDOT H-A RFQ Send Confirmation Intake

This report scans original RFQ send confirmations. It is not measured evidence.

**Status:** `nhi_pedot_h_a_rfq_send_confirmation_intake_waiting_for_confirmation_files`
**Send confirmation directory:** `data/rfq_send_confirmation_files/h_a`
**Send log CSV:** `data/nhi_pedot_h_a_rfq_send_log.csv`
**Intake CSV:** `data/nhi_pedot_h_a_rfq_send_confirmation_intake.csv`
**Files scanned:** 0
**Applied rows:** 0
**Needs review:** 0
**Unmatched:** 0
**Bundle hash matched:** 0

## Intake Rows

| Candidate | File | Status | Bundle match | Applied |
| --- | --- | --- | --- | --- |

## Auto-Apply Rule

A confirmation is auto-applied only when it is a sent `.eml`, maps to a known candidate, has From/To/Date/Message-ID headers, and includes a zip attachment whose SHA-256 matches the RFQ outbox bundle.

Other confirmation files remain review items; they can still be used by filling the send log manually.

## Boundary

RFQ send confirmations only document outreach logistics. They are not material measurement evidence and cannot advance suitability gates without returned raw measurements.
