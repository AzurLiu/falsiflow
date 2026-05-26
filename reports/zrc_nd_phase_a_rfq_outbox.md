# ZRC-ND Phase A RFQ Outbox

This outbox turns the Phase A RFQ packet into vendor-specific emails and zip bundles. It is not measured evidence.

**Status:** `ready_to_send_outbox`
**Active candidate:** `limina_zrc_nd_v0_1`
**Quote requests:** 4
**Ready to send:** 4 / 4
**Attachment count:** 10

## Outbox Files

- Outbox directory: `data/zrc_nd_phase_a_rfq_outbox`
- Attachment manifest: `data/zrc_nd_phase_a_rfq_outbox/attachment_manifest.csv`
- Outbox CSV: `data/zrc_nd_phase_a_rfq_outbox/rfq_outbox.csv`

## Vendor Bundles

| Vendor | Email | Bundle | Bytes | SHA256 | Status |
| --- | --- | --- | ---: | --- | --- |
| Pacific BioLabs Physicochemical Properties Testing | `data/zrc_nd_phase_a_rfq_outbox/emails/pacific_biolabs_physicochemical_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/pacific_biolabs_physicochemical_zrc_nd_phase_a_rfq_bundle.zip` | 17424 | `b00499c1a70ec472...` | `ready_to_send` |
| MilliporeSigma Cell Culture Media Stability and Testing Services | `data/zrc_nd_phase_a_rfq_outbox/emails/sigmaaldrich_media_testing_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_zrc_nd_phase_a_rfq_bundle.zip` | 17423 | `020855375daaa1e6...` | `ready_to_send` |
| The Osmolality Lab | `data/zrc_nd_phase_a_rfq_outbox/emails/the_osmolality_lab_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/the_osmolality_lab_zrc_nd_phase_a_rfq_bundle.zip` | 17359 | `29125cb54ad2a21b...` | `ready_to_send` |
| Jordi Labs Analytical Testing | `data/zrc_nd_phase_a_rfq_outbox/emails/jordi_labs_el_polymer_rfq_email.txt` | `data/zrc_nd_phase_a_rfq_outbox/vendor_packages/jordi_labs_el_polymer_zrc_nd_phase_a_rfq_bundle.zip` | 17391 | `9c91fd2364629fa9...` | `ready_to_send` |

## Send Steps

- Open the vendor-specific email text file.
- Attach the matching vendor zip bundle when emailing or upload the bundle through the vendor form if available.
- Send through the user's email account or official vendor contact form.
- Record contact_date in data/zrc_nd_phase_a_quote_tracker.csv.
- Paste any reply into the quote tracker before selecting an execution path.

## Boundary

RFQ emails, vendor capability replies, supplier guidance, and quote packages are sourcing artifacts only. They do not count as material evidence until real returned measurements pass LIMINA QC.
