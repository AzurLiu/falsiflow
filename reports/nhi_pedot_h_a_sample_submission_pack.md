# NHI-PEDOT H-A Sample Submission Pack

This pack prepares vendor sample-submission questions and material disclosure. It is not measured evidence and not a certified SDS.

**Status:** `sample_submission_precheck_ready`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Protocol:** `nhi_pedot_alg_lam_protocol_v0_2`
**Shipping status:** `do_not_ship_until_vendor_confirms_quote_sample_acceptance_sds_and_custody`
**Runs:** 12
**Raw entries:** 228
**Sample labels:** 36
**Custody rows:** 36

## Nonclinical Statement

Planned H-A samples are nonclinical R&D, acellular medium/coupon samples with no live cells and no intended human or animal use.

## Material Disclosure

| Component | Role | Actual lot? | SDS before shipping? | Handling note |
| --- | --- | --- | --- | --- |
| MEA witness coupon or equivalent electrode-window coupon | device-contact substrate/control surface | `yes` | `vendor_dependent` | No electronics need to be powered; disclose substrate material and any cleaning/sterilization residues. |
| Sodium alginate | hydrogel matrix | `yes` | `yes` | Provide supplier SDS and lot; keep dry powder handling separate from hydrated coupon shipment notes. |
| Calcium sulfate dihydrate | ionic crosslinker | `yes` | `yes` | Provide supplier SDS and final preparation batch ID. |
| DMEM or DMEM/F12 / CL1-proxy medium | crosslinking and soak medium | `yes` | `yes` | Disclose all supplements if used; do not send biohazardous or cell-containing material. |
| PEDOT:PSS dispersion | conductive phase | `yes` | `yes` | Provide supplier SDS, loading fraction, pre-rinse/conditioning record, and whether free dispersion is present in shipped aliquots. |
| Laminin or equivalent cell-adhesion cue | neural cell-contact cue retained above or within hydrogel | `yes` | `yes` | Disclose biological source if applicable; no live cells or human subject material should be included. |
| Acellular soak aliquots | media physicochemical test article | `yes` | `vendor_dependent` | Confirm volume, container, temperature, and no-biohazard acceptance with vendor before shipment. |

## Vendor Pre-Ship Actions

| Vendor | Contact/quote URL | Sample submission URL | Status | Action |
| --- | --- | --- | --- | --- |
| Materials Metric | https://materialsmetric.com/contact-us/ | - | `do_not_ship_until_vendor_confirms` | Use the service/quote request path first if a file upload is available; otherwise email the RFQ text and attach the vendor zip bundle. |
| The Osmolality Lab | https://theosmolalitylab.com/contact-us/ | https://theosmolalitylab.com/submit-samples/ | `do_not_ship_until_vendor_confirms` | Ask explicitly whether acellular neural-medium aliquots with PEDOT:PSS/alginate/laminin exposure fit their non-blood/non-urine and no-biohazard sample policy. |
| Cambridge Polymer Group | https://quote.campoly.com/material-testing/ | https://www.campoly.com/contact-us/submit-sample/ | `do_not_ship_until_vendor_confirms` | Use the quote form for initial feasibility; do not ship samples until a quote number, sample submission form, SDS expectations, and custody requirements are confirmed. |
| MilliporeSigma Cell Culture Media Stability and Testing Services | https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services | - | `do_not_ship_until_vendor_confirms` | Use the service page/contact path first; if routed through support, ask them to assign the RFQ to cell culture media stability/testing or Process Solutions custom testing. |
| Intertek China Healthcare and Medical Device Testing | https://www.intertek.com.cn/contact/ | - | `do_not_ship_until_vendor_confirms` | Use only after first-wave stalls or if China/APAC logistics are preferred; ask for non-GLP R&D routing and raw CSV return. |
| WuXi AppTec Medical Device Testing | https://www.wuxiapptec.com/contact | - | `do_not_ship_until_vendor_confirms` | Best as chemistry/E&L or biocompatibility escalation after H-A or if local China execution is required. |
| TUV SUD China Medical Device Testing | https://www.tuvsud.cn/zh-cn/contact-us | - | `do_not_ship_until_vendor_confirms` | Use as second-wave regulatory/ISO route; ask whether non-GLP raw run_id-level testing can be scoped separately. |
| PONY Testing Medical Device and Life-Science Services | https://www.ponytest.com/ | - | `do_not_ship_until_vendor_confirms` | Use as China-local broad screening fallback only if the response commits to raw sample-level values and source-file provenance. |

## Pre-Ship Questions

- Will you accept acellular neural-medium soak aliquots and hydrated hydrogel/MEA witness coupons as nonclinical R&D samples?
- What minimum aliquot volume and coupon count are required for pH, osmolality, conductivity, and imaging/inspection?
- Which supplier SDS files, lot numbers, and preparation-batch records are required before shipment?
- Do you require a quote number, sample submission form, purchase order, or project ID before samples are sent?
- What container, temperature, timing, and chain-of-custody requirements apply to 0 h, 24 h, and 72 h samples?
- Can returned files preserve run_id, sample_event, target_field, source_file, and instrument export provenance?

## Rejection Rules

- Do not ship any live cells, human subject material, animal tissue, or unknown biological material.
- Do not ship hydrated PEDOT:PSS/alginate/laminin samples until the vendor confirms SDS and sample acceptance requirements.
- Do not treat vendor acceptance, quote numbers, or sample-submission forms as measured evidence.
- Do not substitute vendor-proposed pooled reporting for LIMINA run_id-level raw data without a documented rejection or split-scope decision.

## Boundary

This pack is a nonclinical R&D material disclosure and shipping-readiness checklist. It is not a certified SDS, toxicology opinion, biological safety approval, or material evidence.
