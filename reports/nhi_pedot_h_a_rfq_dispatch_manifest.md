# NHI-PEDOT H-A RFQ Dispatch Manifest

This manifest binds the exact pre-send files for manual H-A RFQ outreach. It is not measured evidence.

**Status:** `h_a_rfq_dispatch_manifest_ready`
**Dispatch rows:** 4
**Ready for manual dispatch:** 4
**Blocked rows:** 0
**EML integrity pass:** 4
**Bundle SHA-256 matches:** 4
**CSV:** `data/nhi_pedot_h_a_rfq_dispatch_manifest.csv`

## Dispatch Rows

| Order | Vendor | Status | Recipient/Form | EML | Bundle SHA-256 | Confirmation save path |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | Materials Metric | `ready_for_manual_dispatch` | `info@materialsmetric.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/materials_metric_rfq_draft.eml` | `6799fdef01396d5e...` | `data/rfq_send_confirmation_files/h_a/materials_metric_send_confirmation.txt` |
| 2 | The Osmolality Lab | `ready_for_manual_dispatch` | `info@osmolab.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/the_osmolality_lab_rfq_draft.eml` | `b89d68822a7e42b1...` | `data/rfq_send_confirmation_files/h_a/the_osmolality_lab_send_confirmation.txt` |
| 3 | Cambridge Polymer Group | `ready_for_manual_dispatch` | `info@campoly.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/cambridge_polymer_group_hydrogel_rfq_draft.eml` | `bad885c9487cfc4e...` | `data/rfq_send_confirmation_files/h_a/cambridge_polymer_group_hydrogel_send_confirmation.txt` |
| 4 | MilliporeSigma Cell Culture Media Stability and Testing Services | `ready_for_manual_dispatch` | `PSTechService@milliporesigma.com` | `data/nhi_pedot_h_a_rfq_outbox/eml_drafts/sigmaaldrich_media_testing_rfq_draft.eml` | `6950279d9e72509b...` | `data/rfq_send_confirmation_files/h_a/sigmaaldrich_media_testing_send_confirmation.txt` |

## Per-Row Manual Steps

### Materials Metric

- Dispatch status: `ready_for_manual_dispatch`
- EML SHA-256: `b20d27e34c986c9b45e1cea094dffe9cb0ae102c5c43fae1c8e6ddcf81ccf265`
- Bundle SHA-256: `6799fdef01396d5ed999a13a4de131bf1d490719369c0e4b90f81c7c73cd9d35`
- Attached bundle verified: `true`
- Step: Open data/nhi_pedot_h_a_rfq_outbox/eml_drafts/materials_metric_rfq_draft.eml, confirm To=info@materialsmetric.com and attached bundle data/nhi_pedot_h_a_rfq_outbox/vendor_packages/materials_metric_nhi_pedot_h_a_rfq_bundle.zip with SHA-256 6799fdef01396d5ed999a13a4de131bf1d490719369c0e4b90f81c7c73cd9d35, send manually, then save the original sent-email export, form confirmation, PDF, or screenshot at data/rfq_send_confirmation_files/h_a/materials_metric_send_confirmation.txt.

### The Osmolality Lab

- Dispatch status: `ready_for_manual_dispatch`
- EML SHA-256: `f3a9108c7580672eda874b87b5d3b7e8e52a8697c034b23b91c7e97e4a70149e`
- Bundle SHA-256: `b89d68822a7e42b1d387d3b239b6cee86140d3b188e1a3ae14e92792094c023a`
- Attached bundle verified: `true`
- Step: Open data/nhi_pedot_h_a_rfq_outbox/eml_drafts/the_osmolality_lab_rfq_draft.eml, confirm To=info@osmolab.com and attached bundle data/nhi_pedot_h_a_rfq_outbox/vendor_packages/the_osmolality_lab_nhi_pedot_h_a_rfq_bundle.zip with SHA-256 b89d68822a7e42b1d387d3b239b6cee86140d3b188e1a3ae14e92792094c023a, send manually, then save the original sent-email export, form confirmation, PDF, or screenshot at data/rfq_send_confirmation_files/h_a/the_osmolality_lab_send_confirmation.txt.

### Cambridge Polymer Group

- Dispatch status: `ready_for_manual_dispatch`
- EML SHA-256: `2e6218e69068de0c0306d900194399dc909d5d6161a91165d1fa01ffa2e5cd59`
- Bundle SHA-256: `bad885c9487cfc4e33c6abda168421232f8da5b1fc2a6698b4d129453d7811a1`
- Attached bundle verified: `true`
- Step: Open data/nhi_pedot_h_a_rfq_outbox/eml_drafts/cambridge_polymer_group_hydrogel_rfq_draft.eml, confirm To=info@campoly.com and attached bundle data/nhi_pedot_h_a_rfq_outbox/vendor_packages/cambridge_polymer_group_hydrogel_nhi_pedot_h_a_rfq_bundle.zip with SHA-256 bad885c9487cfc4e33c6abda168421232f8da5b1fc2a6698b4d129453d7811a1, send manually, then save the original sent-email export, form confirmation, PDF, or screenshot at data/rfq_send_confirmation_files/h_a/cambridge_polymer_group_hydrogel_send_confirmation.txt.

### MilliporeSigma Cell Culture Media Stability and Testing Services

- Dispatch status: `ready_for_manual_dispatch`
- EML SHA-256: `bdd950ff0b9a5f45cdfe574dfea68fdd97f911376abdf2eb9882e44e6b03fdac`
- Bundle SHA-256: `6950279d9e72509ba62950b8ad0ea46f1f9d4c4b3e54960054d5967bc66ea8cd`
- Attached bundle verified: `true`
- Step: Open data/nhi_pedot_h_a_rfq_outbox/eml_drafts/sigmaaldrich_media_testing_rfq_draft.eml, confirm To=PSTechService@milliporesigma.com and attached bundle data/nhi_pedot_h_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_nhi_pedot_h_a_rfq_bundle.zip with SHA-256 6950279d9e72509ba62950b8ad0ea46f1f9d4c4b3e54960054d5967bc66ea8cd, send manually, then save the original sent-email export, form confirmation, PDF, or screenshot at data/rfq_send_confirmation_files/h_a/sigmaaldrich_media_testing_send_confirmation.txt.

## Boundary

This dispatch manifest only identifies files for manual RFQ outreach. It is not a send confirmation, quote reply, measurement result, or material suitability claim.
