# ZRC-ND Phase A Vendor Outreach Brief

This brief screens external services that may return real Phase A acellular measurements. It is not a purchase recommendation and not material evidence.

**Status:** `ready_for_vendor_screening`
**Active candidate:** `limina_zrc_nd_v0_1`
**Last checked:** `2026-05-24`
**Service request:** `ready_to_request_real_phase_a_measurements`
**Delivery package:** `ready_to_send`
**Runs:** 8
**Sample events:** 16

## Outreach Strategy

- Ask first for non-GLP or exploratory R&D feasibility and exact CSV return; escalate to GLP or E&L only after the material-blank gate identifies a need.
- Prefer vendors that can report pH, osmolality, appearance/turbidity, and possibly conductivity at sample level.
- If conductivity is not offered by a media lab, pair the media lab with an internal meter or a second physicochemical testing lab while preserving the same run_id labels.
- Ask membrane/component vendors for article preparation and compatibility support, but do not treat supplier guidance as measurement evidence.
- Reject any quote that returns only certificates, pooled averages, or narrative feasibility opinions.

## First-Wave Contacts

| Candidate | Fit | Likely covers | Main risk | Source |
| --- | --- | --- | --- | --- |
| `pacific_biolabs_physicochemical` | strong_integrated_physicochemical_candidate | appearance, pH, osmolality, possible analytical add-ons | May be oriented toward regulated pharma/biologics lot-release workflows; exploratory R&D scope and conductivity need confirmation. | [Pacific BioLabs Physicochemical Properties Testing](https://pacificbiolabs.com/physicochemical-properties) |
| `sigmaaldrich_media_testing` | strong_media_qc_candidate | appearance, pH, osmolality, media testing context | May focus on media products and release/stability programs rather than custom membrane exposure aliquots. | [MilliporeSigma Cell Culture Media Stability and Testing Services](https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services) |
| `the_osmolality_lab` | focused_osmolality_ph_candidate | osmolality, pH | Likely needs pairing for conductivity and module-specific appearance/turbidity interpretation. | [The Osmolality Lab](https://theosmolalitylab.com/services/) |
| `jordi_labs_el_polymer` | el_escalation_or_custom_chemistry_candidate | extractables/leachables escalation, polymer analysis, particle or residue analysis, custom analytical chemistry | Stronger for E&L and polymer chemistry than minimal Phase A media QC; may be better as escalation after blank-integrity drift. | [Jordi Labs Analytical Testing](https://jordilabs.com/lab-testing/) |

## Secondary/Escalation Contacts

| Candidate | Fit | Use only if | Source |
| --- | --- | --- | --- |
| `repligen_field_application_support` | component_support_candidate | Supplier support can improve article preparation but does not itself generate Phase A evidence. | [Repligen Field Applications and Customer Support](https://www.repligen.com/support/contact-overview) |
| `intertek_china_healthcare_testing` | second_wave_apac_split_scope_candidate | Useful for local routing but exact Phase A media-panel coverage is unconfirmed until technical review. | [Intertek China Healthcare and Medical Device Testing](https://www.intertek.com.cn/) |
| `wuxi_apptec_medical_device_testing` | second_wave_apac_e_l_escalation_candidate | Likely stronger after Phase A indicates chemical or biocompatibility risk; may be too heavy for first-pass media-panel testing. | [WuXi AppTec Medical Device Testing](https://www.wuxiapptec.com/) |
| `tuv_sud_china_medical_device_testing` | second_wave_apac_regulatory_escalation_candidate | Regulatory-service orientation may slow or over-scope Phase A unless the request is routed as a small exploratory screen. | [TUV SUD China Medical Device Testing](https://www.tuvsud.cn/) |
| `pony_testing_medical_device` | second_wave_china_screening_candidate | Broad testing company; Phase A fit depends on successful technical routing and raw-data return agreement. | [PONY Testing Medical Device and Life-Science Services](https://www.ponytest.com/) |

## Questions To Send

- Can you accept nonclinical acellular neural-medium aliquots exposed to small membrane/module witness articles?
- Can you preserve one result per LIMINA run_id rather than returning pooled averages?
- Can you report pH, osmolality, conductivity, and appearance/turbidity/visible precipitate for every requested row?
- If conductivity is not available, can you identify whether the sample may be returned or paired with a second lab while preserving run_id labels?
- Can you fill or accept the provided Phase A CSV schema without changing column names?
- What minimum aliquot volume, sample count, container, and turnaround time are required?
- What handling constraints apply to regenerated-cellulose membranes, guard filters, COC/COP/PEEK modules, and neural-medium proxies?
- Can you return raw exports or instrument reports with stable filenames that can be reconciled to run_id?
- Can this be scoped as exploratory non-GLP R&D rather than a full regulated E&L or product-release program?
- What sample acceptance, SDS, chain-of-custody, and quote-number requirements must be met before shipping?

## Candidate Details

### Pacific BioLabs Physicochemical Properties Testing

- Source: [https://pacificbiolabs.com/physicochemical-properties](https://pacificbiolabs.com/physicochemical-properties)
- Contact: [https://pacificbiolabs.com/contact/](https://pacificbiolabs.com/contact/)
- Service type: `physicochemical_testing`
- Evidence from source: Public page lists physicochemical testing including appearance, pH, osmolality, viscosity, optical activity, and spectral analysis; contact page provides quote phone and contact path.
- Likely covers: appearance, pH, osmolality, possible analytical add-ons
- Unknowns to ask:
  - Can conductivity be added to the pH/osmolality/appearance panel or routed to another internal analytical service?
  - Can they accept nonclinical neural-medium aliquots exposed to regenerated-cellulose membrane/module articles?
  - Can they preserve one report row per LIMINA run_id and return raw values in the provided CSV schema?
- Risk: May be oriented toward regulated pharma/biologics lot-release workflows; exploratory R&D scope and conductivity need confirmation.

### MilliporeSigma Cell Culture Media Stability and Testing Services

- Source: [https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services](https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services)
- Contact: [https://www.sigmaaldrich.com/US/en/collections/offices](https://www.sigmaaldrich.com/US/en/collections/offices)
- Service type: `cell_culture_media_testing`
- Evidence from source: Service page lists cell culture media stability/testing with standard product release tests including appearance, pH, osmolality, endotoxin, bioburden, and solubility.
- Likely covers: appearance, pH, osmolality, media testing context
- Unknowns to ask:
  - Can conductivity be added for the Phase A material-blank gate?
  - Can they test customer-prepared medium aliquots exposed to dialysis membrane/module witness articles?
  - Can they return one row per run_id instead of product-lot summaries?
- Risk: May focus on media products and release/stability programs rather than custom membrane exposure aliquots.

### The Osmolality Lab

- Source: [https://theosmolalitylab.com/services/](https://theosmolalitylab.com/services/)
- Contact: [https://theosmolalitylab.com/contact-us/](https://theosmolalitylab.com/contact-us/)
- Service type: `osmolality_and_ph_testing`
- Evidence from source: Service page lists osmolality by freezing point and vapor pressure plus pH testing; submission page asks for quote before samples and states sample policy constraints.
- Likely covers: osmolality, pH
- Unknowns to ask:
  - Can they accept acellular neural-medium aliquots that are non-biohazard and non-radioactive?
  - Can they run all 8 Phase A rows as individual run_id samples with pre/post mapping?
  - Can they support conductivity directly, or should conductivity be measured by another lab or internally?
- Risk: Likely needs pairing for conductivity and module-specific appearance/turbidity interpretation.

### Jordi Labs Analytical Testing

- Source: [https://jordilabs.com/lab-testing/](https://jordilabs.com/lab-testing/)
- Contact: [https://jordilabs.com/contact/](https://jordilabs.com/contact/)
- Service type: `polymer_and_extractables_testing`
- Evidence from source: Public lab-testing page describes contract polymer analytical testing with extractables/leachables, particulates/residue, polymer analysis, chromatography, mass spectrometry, microscopy, particle analysis, and physical testing.
- Likely covers: extractables/leachables escalation, polymer analysis, particle or residue analysis, custom analytical chemistry
- Unknowns to ask:
  - Can they run a minimal aqueous neural-medium material-blank screen before a full E&L program?
  - Can they preserve run_id-level aliquot identity and source-file provenance?
  - Can they add basic pH/osmolality/conductivity, or should they only be used after Phase A shows extractables or particulate concerns?
- Risk: Stronger for E&L and polymer chemistry than minimal Phase A media QC; may be better as escalation after blank-integrity drift.

### Repligen Field Applications and Customer Support

- Source: [https://www.repligen.com/support/contact-overview](https://www.repligen.com/support/contact-overview)
- Contact: [https://www.repligen.com/support/contact-overview/contact](https://www.repligen.com/support/contact-overview/contact)
- Service type: `membrane_supplier_application_support`
- Evidence from source: Support page describes field application support for membrane selection and optimization, downstream processing, experimental design, and customer service for product and pricing inquiries.
- Likely covers: membrane selection guidance, product handling guidance, application support, supplier documentation
- Unknowns to ask:
  - Can they recommend an off-the-shelf regenerated-cellulose or equivalent membrane format for a small acellular medium-integrity sentinel?
  - Can they advise on rinse/preconditioning and preservative removal without changing MWCO behavior?
  - Can they provide lot documentation needed for chain-of-custody and later measurement interpretation?
- Risk: Supplier support can improve article preparation but does not itself generate Phase A evidence.

### Intertek China Healthcare and Medical Device Testing

- Source: [https://www.intertek.com.cn/](https://www.intertek.com.cn/)
- Contact: [https://www.intertek.com.cn/contact/](https://www.intertek.com.cn/contact/)
- Service type: `apac_materials_and_healthcare_testing`
- Evidence from source: Official China site describes testing, inspection, certification, and healthcare/medical-device related services; exact pH/osmolality/conductivity coverage must be confirmed by RFQ.
- Likely covers: China/APAC local intake, possible physicochemical testing routing, possible medical-device material testing
- Unknowns to ask:
  - Can the China lab route nonclinical neural-medium aliquots from membrane/module exposures to pH, osmolality, conductivity, and appearance testing?
  - Can they preserve one result per LIMINA run_id and return raw values in the Phase A CSV schema?
  - Can they keep this as exploratory non-GLP R&D instead of a certificate-only program?
- Risk: Useful for local routing but exact Phase A media-panel coverage is unconfirmed until technical review.

### WuXi AppTec Medical Device Testing

- Source: [https://www.wuxiapptec.com/](https://www.wuxiapptec.com/)
- Contact: [https://www.wuxiapptec.com/contact](https://www.wuxiapptec.com/contact)
- Service type: `medical_device_biocompatibility_and_chemistry`
- Evidence from source: Official company site lists global testing services; RFQ must route specifically to medical-device chemistry, biocompatibility, or extractables/leachables feasibility.
- Likely covers: medical-device testing routing, chemistry or biocompatibility escalation, China/APAC logistics
- Unknowns to ask:
  - Can they run a small exploratory membrane/module material-blank screen before full ISO 10993 work?
  - Can pH, osmolality, conductivity, and appearance be returned at run_id level, or is this only an E&L escalation path?
  - What aliquot volume, module surface area, sample count, SDS, and custody requirements apply?
- Risk: Likely stronger after Phase A indicates chemical or biocompatibility risk; may be too heavy for first-pass media-panel testing.

### TUV SUD China Medical Device Testing

- Source: [https://www.tuvsud.cn/](https://www.tuvsud.cn/)
- Contact: [https://www.tuvsud.cn/zh-cn/contact-us](https://www.tuvsud.cn/zh-cn/contact-us)
- Service type: `medical_device_testing_and_biocompatibility`
- Evidence from source: Official China site covers medical-device testing and certification services; use RFQ to confirm whether exploratory material-blank measurements can be scoped separately.
- Likely covers: medical-device testing routing, biocompatibility or chemical characterization escalation, China/APAC contact path
- Unknowns to ask:
  - Can they quote the Phase A media-integrity panel as non-GLP R&D and return raw run_id-level values?
  - If not, can they quote a later ISO 10993 chemical characterization step after Phase A identifies a need?
  - What sample-prep, surface-area, and custody constraints apply to regenerated-cellulose/module witness articles?
- Risk: Regulatory-service orientation may slow or over-scope Phase A unless the request is routed as a small exploratory screen.

### PONY Testing Medical Device and Life-Science Services

- Source: [https://www.ponytest.com/](https://www.ponytest.com/)
- Contact: [https://www.ponytest.com/](https://www.ponytest.com/)
- Service type: `china_third_party_testing`
- Evidence from source: Official site describes third-party testing services across health, safety, and product categories; exact medical-device, media chemistry, and custom R&D coverage must be confirmed.
- Likely covers: China local third-party testing intake, possible physicochemical testing routing, possible product-safety or medical-device routing
- Unknowns to ask:
  - Can they route nonclinical neural-medium aliquots to pH, osmolality, conductivity, and appearance/turbidity readouts?
  - Can they return the provided Phase A CSV with one row per run_id and raw source-file references?
  - Can they avoid certificate-only or pooled-average reporting?
- Risk: Broad testing company; Phase A fit depends on successful technical routing and raw-data return agreement.

## Boundary

Vendor capability claims and supplier guidance do not count as material evidence. Only returned real run-level measurements that pass LIMINA QC and claim audit can advance the material.
