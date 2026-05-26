# NHI-PEDOT H-A RFQ Outbox

This outbox turns the H-A RFQ packet into vendor-specific emails and zip bundles. It is not measured evidence.

**Status:** `ready_to_send_outbox`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Quote requests:** 4
**Ready to send:** 4 / 4
**Attachment count:** 20

## Outbox Files

- Outbox directory: `data/nhi_pedot_h_a_rfq_outbox`
- Attachment manifest: `data/nhi_pedot_h_a_rfq_outbox/attachment_manifest.csv`
- Outbox CSV: `data/nhi_pedot_h_a_rfq_outbox/rfq_outbox.csv`

## Vendor Bundles

| Vendor | Email | Bundle | Bytes | SHA256 | Status |
| --- | --- | --- | ---: | --- | --- |
| Materials Metric | `data/nhi_pedot_h_a_rfq_outbox/emails/materials_metric_rfq_email.txt` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/materials_metric_nhi_pedot_h_a_rfq_bundle.zip` | 36253 | `6799fdef01396d5e...` | `ready_to_send` |
| The Osmolality Lab | `data/nhi_pedot_h_a_rfq_outbox/emails/the_osmolality_lab_rfq_email.txt` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/the_osmolality_lab_nhi_pedot_h_a_rfq_bundle.zip` | 36279 | `b89d68822a7e42b1...` | `ready_to_send` |
| Cambridge Polymer Group | `data/nhi_pedot_h_a_rfq_outbox/emails/cambridge_polymer_group_hydrogel_rfq_email.txt` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/cambridge_polymer_group_hydrogel_nhi_pedot_h_a_rfq_bundle.zip` | 36349 | `bad885c9487cfc4e...` | `ready_to_send` |
| MilliporeSigma Cell Culture Media Stability and Testing Services | `data/nhi_pedot_h_a_rfq_outbox/emails/sigmaaldrich_media_testing_rfq_email.txt` | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_nhi_pedot_h_a_rfq_bundle.zip` | 36340 | `6950279d9e72509b...` | `ready_to_send` |

## Send Steps

- Open the vendor-specific email text file.
- Attach the matching vendor zip bundle.
- Send to the vendor or collaborator through the user's email account.
- Record contact_date in data/nhi_pedot_h_a_quote_tracker.csv.
- Paste any reply into the quote tracker before selecting an execution path.

## Boundary

RFQ emails, vendor capability replies, and quote packages are sourcing artifacts only. They do not count as material evidence until real returned measurements pass LIMINA QC.
