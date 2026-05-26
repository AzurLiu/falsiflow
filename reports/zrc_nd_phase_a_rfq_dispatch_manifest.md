# ZRC-ND Phase A RFQ Dispatch Manifest

This manifest binds the exact pre-send files for manual ZRC-ND Phase A RFQ outreach. It is not measured evidence.

**Status:** `zrc_phase_a_rfq_dispatch_manifest_ready`
**Dispatch rows:** 4
**Ready for manual dispatch:** 4
**Blocked rows:** 0
**Bundle SHA-256 matches:** 4
**Confirmation templates:** 4
**CSV:** `data/zrc_nd_phase_a_rfq_dispatch_manifest.csv`

## Dispatch Rows

| Order | Vendor | Status | Recipient/Form | Email text | Bundle SHA-256 | Confirmation save path |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | Pacific BioLabs Physicochemical Properties Testing | `ready_for_manual_dispatch` | `https://pacificbiolabs.com/contact/` | `data/zrc_nd_phase_a_rfq_outbox/emails/pacific_biolabs_physicochemical_rfq_email.txt` | `b00499c1a70ec472...` | `data/rfq_send_confirmation_files/zrc_phase_a/pacific_biolabs_physicochemical_send_confirmation.txt` |
| 2 | MilliporeSigma Cell Culture Media Stability and Testing Services | `ready_for_manual_dispatch` | `PSTechService@milliporesigma.com` | `data/zrc_nd_phase_a_rfq_outbox/emails/sigmaaldrich_media_testing_rfq_email.txt` | `020855375daaa1e6...` | `data/rfq_send_confirmation_files/zrc_phase_a/sigmaaldrich_media_testing_send_confirmation.txt` |
| 3 | The Osmolality Lab | `ready_for_manual_dispatch` | `info@osmolab.com` | `data/zrc_nd_phase_a_rfq_outbox/emails/the_osmolality_lab_rfq_email.txt` | `29125cb54ad2a21b...` | `data/rfq_send_confirmation_files/zrc_phase_a/the_osmolality_lab_send_confirmation.txt` |
| 4 | Jordi Labs Analytical Testing | `ready_for_manual_dispatch` | `info@jordilabs.com` | `data/zrc_nd_phase_a_rfq_outbox/emails/jordi_labs_el_polymer_rfq_email.txt` | `9c91fd2364629fa9...` | `data/rfq_send_confirmation_files/zrc_phase_a/jordi_labs_el_polymer_send_confirmation.txt` |

## Per-Row Manual Steps

- `pacific_biolabs_physicochemical`: Open data/zrc_nd_phase_a_rfq_outbox/emails/pacific_biolabs_physicochemical_rfq_email.txt, send or paste through https://pacificbiolabs.com/contact/, attach/upload data/zrc_nd_phase_a_rfq_outbox/vendor_packages/pacific_biolabs_physicochemical_zrc_nd_phase_a_rfq_bundle.zip with SHA-256 b00499c1a70ec472a11eb8d894c2a463d6cdd3bc3819011aeee203de8980ec3d, then save the original sent-email export, form confirmation, PDF, or screenshot at data/rfq_send_confirmation_files/zrc_phase_a/pacific_biolabs_physicochemical_send_confirmation.txt.
- `sigmaaldrich_media_testing`: Open data/zrc_nd_phase_a_rfq_outbox/emails/sigmaaldrich_media_testing_rfq_email.txt, send or paste through PSTechService@milliporesigma.com, attach/upload data/zrc_nd_phase_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_zrc_nd_phase_a_rfq_bundle.zip with SHA-256 020855375daaa1e6afde37c0d84b3ecffe2ddaadb5ca88e44a02ed842ac3b8d2, then save the original sent-email export, form confirmation, PDF, or screenshot at data/rfq_send_confirmation_files/zrc_phase_a/sigmaaldrich_media_testing_send_confirmation.txt.
- `the_osmolality_lab`: Open data/zrc_nd_phase_a_rfq_outbox/emails/the_osmolality_lab_rfq_email.txt, send or paste through info@osmolab.com, attach/upload data/zrc_nd_phase_a_rfq_outbox/vendor_packages/the_osmolality_lab_zrc_nd_phase_a_rfq_bundle.zip with SHA-256 29125cb54ad2a21b1b161a4ecf22ec430b6c4109d8c208c4bd931a607373406f, then save the original sent-email export, form confirmation, PDF, or screenshot at data/rfq_send_confirmation_files/zrc_phase_a/the_osmolality_lab_send_confirmation.txt.
- `jordi_labs_el_polymer`: Open data/zrc_nd_phase_a_rfq_outbox/emails/jordi_labs_el_polymer_rfq_email.txt, send or paste through info@jordilabs.com, attach/upload data/zrc_nd_phase_a_rfq_outbox/vendor_packages/jordi_labs_el_polymer_zrc_nd_phase_a_rfq_bundle.zip with SHA-256 9c91fd2364629fa9c84d200d10a6ef041e479bcac16a50dc70082a3bb31750c3, then save the original sent-email export, form confirmation, PDF, or screenshot at data/rfq_send_confirmation_files/zrc_phase_a/jordi_labs_el_polymer_send_confirmation.txt.

## Boundary

This ZRC-ND Phase A dispatch manifest only identifies files for manual RFQ outreach. It is not a send confirmation, quote reply, measurement result, or material suitability claim.
