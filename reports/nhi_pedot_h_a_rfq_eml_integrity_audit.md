# NHI-PEDOT H-A RFQ EML Integrity Audit

This pre-send audit parses each local .eml draft and verifies recipient, subject, boundary headers, body markers, bundle file hash, and attached zip hash.

**Status:** `h_a_rfq_eml_integrity_ready`
**Rows:** 4
**Pass:** 4
**Fail:** 0
**Missing EML:** 0
**Missing bundle:** 0
**Attachment mismatch:** 0

## Rows

| Vendor | Status | To | Subject | Bundle file | Attached bundle | Errors |
| --- | --- | --- | --- | --- | --- | --- |
| Materials Metric | `pass` | `true` | `true` | `true` | `true` | `-` |
| The Osmolality Lab | `pass` | `true` | `true` | `true` | `true` | `-` |
| Cambridge Polymer Group | `pass` | `true` | `true` | `true` | `true` | `-` |
| MilliporeSigma Cell Culture Media Stability and Testing Services | `pass` | `true` | `true` | `true` | `true` | `-` |

## Boundary

This audit only verifies draft-mail logistics. Passing rows are not send confirmations, quote replies, measurement evidence, provider authorization, or material suitability evidence.
