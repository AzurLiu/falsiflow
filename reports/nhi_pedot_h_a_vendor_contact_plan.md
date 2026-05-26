# NHI-PEDOT H-A Vendor Contact Plan

This plan maps RFQ outbox bundles to official vendor contact channels. It is not measured evidence.

**Status:** `contact_plan_ready`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Last checked:** `2026-05-24`
**Rows:** 8

## Status Counts

- `ready_to_send`: 4
- `standby_secondary_wave`: 4

## Contact Rows

| Wave | Vendor | Method | Email | Contact | Bundle | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `first_wave` | Materials Metric | `email_or_request_service_form` | `info@materialsmetric.com` | https://materialsmetric.com/contact-us/ | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/materials_metric_nhi_pedot_h_a_rfq_bundle.zip` | `ready_to_send` |
| `first_wave` | The Osmolality Lab | `email_or_contact_form` | `info@osmolab.com` | https://theosmolalitylab.com/contact-us/ | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/the_osmolality_lab_nhi_pedot_h_a_rfq_bundle.zip` | `ready_to_send` |
| `first_wave` | Cambridge Polymer Group | `request_quote_form_or_email` | `info@campoly.com` | https://quote.campoly.com/material-testing/ | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/cambridge_polymer_group_hydrogel_nhi_pedot_h_a_rfq_bundle.zip` | `ready_to_send` |
| `first_wave` | MilliporeSigma Cell Culture Media Stability and Testing Services | `service_page_or_technical_service` | `PSTechService@milliporesigma.com` | https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services | `data/nhi_pedot_h_a_rfq_outbox/vendor_packages/sigmaaldrich_media_testing_nhi_pedot_h_a_rfq_bundle.zip` | `ready_to_send` |
| `second_wave` | Intertek China Healthcare and Medical Device Testing | `contact_form_or_china_service_email` | `service.china@intertek.com` | https://www.intertek.com.cn/contact/ | `-` | `standby_secondary_wave` |
| `second_wave` | WuXi AppTec Medical Device Testing | `contact_form` | `-` | https://www.wuxiapptec.com/contact | `-` | `standby_secondary_wave` |
| `second_wave` | TUV SUD China Medical Device Testing | `contact_form` | `-` | https://www.tuvsud.cn/zh-cn/contact-us | `-` | `standby_secondary_wave` |
| `second_wave` | PONY Testing Medical Device and Life-Science Services | `contact_form_or_service_inquiry` | `-` | https://www.ponytest.com/ | `-` | `standby_secondary_wave` |

## Send Instructions

- Use the contact_url or quote_url when a vendor requires a form.
- Use primary_email when direct email is accepted; attach the matching bundle_zip.
- After sending, enter contact_date in data/nhi_pedot_h_a_quote_tracker.csv and rerun the iteration.
- Do not ship samples until the vendor confirms scope, sample acceptance, custody fields, and quote number if required.
- Do not treat a contact reply as evidence; only real returned measurements can move H-A.

## Source Notes

### Materials Metric

- Phone: 804-404-6414
- Secondary emails: -
- Sample submission URL: -
- Source URL: https://materialsmetric.com/contact-us/
- Source note: Official contact page lists service/quote request options plus info@materialsmetric.com and 804-404-6414.
- Send note: Use the service/quote request path first if a file upload is available; otherwise email the RFQ text and attach the vendor zip bundle.

### The Osmolality Lab

- Phone: 385-323-5141
- Secondary emails: billing@osmolab.com
- Sample submission URL: https://theosmolalitylab.com/submit-samples/
- Source URL: https://theosmolalitylab.com/contact-us/
- Source note: Official contact page lists info@osmolab.com and 385.323.5141; submission page says to request a quote before sending samples.
- Send note: Ask explicitly whether acellular neural-medium aliquots with PEDOT:PSS/alginate/laminin exposure fit their non-blood/non-urine and no-biohazard sample policy.

### Cambridge Polymer Group

- Phone: 617-629-4400
- Secondary emails: -
- Sample submission URL: https://www.campoly.com/contact-us/submit-sample/
- Source URL: https://www.campoly.com/contact-us/
- Source note: Official contact page lists info@campoly.com and 617-629-4400; sample submission page asks for a completed sample form and quote number.
- Send note: Use the quote form for initial feasibility; do not ship samples until a quote number, sample submission form, SDS expectations, and custody requirements are confirmed.

### MilliporeSigma Cell Culture Media Stability and Testing Services

- Phone: 1-800-325-3010; 1-800-221-1975; 1-866-CARE-811
- Secondary emails: PSClientCare@milliporesigma.com
- Sample submission URL: -
- Source URL: https://www.sigmaaldrich.com/US/en/collections/offices
- Source note: Official offices/contact page lists U.S. customer service, technical service, and Process Solutions technical/commercial service contacts.
- Send note: Use the service page/contact path first; if routed through support, ask them to assign the RFQ to cell culture media stability/testing or Process Solutions custom testing.

### Intertek China Healthcare and Medical Device Testing

- Phone: -
- Secondary emails: -
- Sample submission URL: -
- Source URL: https://www.intertek.com.cn/contact/
- Source note: Official China contact path should be used to route the RFQ to healthcare, materials, or medical-device testing; exact lab coverage must be confirmed.
- Send note: Use only after first-wave stalls or if China/APAC logistics are preferred; ask for non-GLP R&D routing and raw CSV return.

### WuXi AppTec Medical Device Testing

- Phone: -
- Secondary emails: -
- Sample submission URL: -
- Source URL: https://www.wuxiapptec.com/contact
- Source note: Use official contact routing for medical-device testing or chemistry/biocompatibility feasibility; do not assume H-A media-panel coverage until technical review.
- Send note: Best as chemistry/E&L or biocompatibility escalation after H-A or if local China execution is required.

### TUV SUD China Medical Device Testing

- Phone: -
- Secondary emails: -
- Sample submission URL: -
- Source URL: https://www.tuvsud.cn/zh-cn/contact-us
- Source note: Use official China contact routing for medical-device testing or biocompatibility; exploratory H-A scope requires confirmation.
- Send note: Use as second-wave regulatory/ISO route; ask whether non-GLP raw run_id-level testing can be scoped separately.

### PONY Testing Medical Device and Life-Science Services

- Phone: -
- Secondary emails: -
- Sample submission URL: -
- Source URL: https://www.ponytest.com/
- Source note: Use official site inquiry path to route custom medical-device or physicochemical testing; exact H-A fit must be confirmed.
- Send note: Use as China-local broad screening fallback only if the response commits to raw sample-level values and source-file provenance.

## Boundary

Contact details and vendor responses are sourcing artifacts only. They do not count as material evidence until real returned measurements pass LIMINA QC.
