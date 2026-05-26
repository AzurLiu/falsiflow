# NHI-PEDOT H-A Vendor Outreach Brief

This brief screens external services that may return real H-A acellular measurements. It is not a purchase recommendation and not material evidence.

**Status:** `ready_for_vendor_screening`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Last checked:** `2026-05-24`
**Service request:** `ready_to_request_real_measurements`
**Delivery package:** `ready_to_send`
**Runs:** 12
**Raw entries:** 228

## Outreach Strategy

- Ask first for non-GLP R&D feasibility and exact raw CSV return; only escalate to GLP/ISO if H-A passes and H-B/H-C need regulated-style support.
- Prefer vendors that will preserve sample-level run_id mapping rather than pooled averages.
- Split the work if one vendor can do media physicochemical tests but not hydrogel/coupon imaging.
- Reject any quote that substitutes broad pass/fail certificates for raw pH, osmolality, conductivity, and image-derived values.

## First-Wave Contacts

| Candidate | Fit | Likely covers | Main risk | Source |
| --- | --- | --- | --- | --- |
| `materials_metric` | integrated_custom_candidate | custom study design, microscopy, materials characterization, biomaterials evaluation | Custom scope must be tightly controlled so it returns the exact LIMINA fields rather than a broad narrative report. | [Materials Metric](https://materialsmetric.com/) |
| `the_osmolality_lab` | strong_media_panel_candidate | osmolality, conductivity, pH | May not cover hydrogel swelling, delamination, or imaging; likely needs pairing with a materials lab. | [The Osmolality Lab](https://theosmolalitylab.com/) |
| `cambridge_polymer_group_hydrogel` | strong_coupon_physical_candidate | swelling ratio, hydrogel physical characterization, microscopy or surface characterization | May be stronger for material characterization than cell-culture medium physicochemical testing. | [Cambridge Polymer Group](https://www.campoly.com/services/analytical-testing/material-characterization-techniques/hydrogel-characterization/) |
| `sigmaaldrich_media_testing` | strong_media_release_candidate | appearance, pH, osmolality | May be optimized for media products and release specifications, not custom hydrogel coupon extraction workflows. | [MilliporeSigma Cell Culture Media Stability and Testing Services](https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services) |

## Secondary/Escalation Contacts

| Candidate | Fit | Use only if | Source |
| --- | --- | --- | --- |
| `nikon_bioimaging_lab` | imaging_add_on_candidate | Does not cover pH/osmolality/conductivity and may be overpowered for simple H-A coupon inspection. | [Nikon BioImaging Lab USA](https://www.microscope.healthcare.nikon.com/bioimaging-centers/nikon-bioimaging-labs/boston-usa) |
| `sgs_extractables_leachables` | future_e_l_escalation_candidate | Too heavy for first H-A unless the project wants early E&L escalation; useful after H-A if leachables are a key decision. | [SGS USA Extractables and Leachables in Medical Devices](https://www.sgs.com/en-us/services/extractables-and-leachables-in-medical-devices) |
| `hohenstein_medical_el` | future_e_l_escalation_candidate | Regulatory E&L scope may be more expensive and slower than the minimal H-A decision package. | [Hohenstein Medical Extractables and Leachables](https://www.hohenstein.us/en-us/medical-device-testing-lab/medical-device-extractables-leachables) |
| `intertek_china_healthcare_testing` | second_wave_apac_split_scope_candidate | Service fit is broader and must be routed by RFQ; do not assume exact H-A field coverage until a technical reply confirms it. | [Intertek China Healthcare and Medical Device Testing](https://www.intertek.com.cn/) |
| `wuxi_apptec_medical_device_testing` | second_wave_apac_e_l_escalation_candidate | Likely better for regulated-style chemistry/biocompatibility escalation than the fastest minimal H-A panel. | [WuXi AppTec Medical Device Testing](https://www.wuxiapptec.com/) |
| `tuv_sud_china_medical_device_testing` | second_wave_apac_regulatory_escalation_candidate | May be too regulatory and too slow for the minimal first H-A decision unless chemistry/biocompatibility escalation is required. | [TUV SUD China Medical Device Testing](https://www.tuvsud.cn/) |
| `pony_testing_medical_device` | second_wave_china_screening_candidate | Broad testing company; H-A fit depends entirely on technical routing and must be confirmed before sample shipment. | [PONY Testing Medical Device and Life-Science Services](https://www.ponytest.com/) |

## Questions To Send

- Can you accept nonclinical R&D hydrogel-coated MEA witness coupons and matched soak media?
- Can you preserve one result per LIMINA run_id instead of returning pooled averages?
- Can you run 37 C acellular soak timepoints at 0 h, 24 h, and 72 h, or should we perform the soak and send aliquots/coupons?
- Can you report pH, osmolality, conductivity, visible precipitate, shedding, swelling fraction, delamination score, and optical transparency fraction?
- Can you return raw exports and image files with stable filenames that we can enter in the source_file column?
- Can you fill or accept the provided raw-measurement CSV schema without changing column names?
- What minimum sample volume, coupon size, and sample count are required?
- What handling constraints apply to alginate, laminin, PEDOT:PSS, neural medium, and sterile or aseptic samples?
- What turnaround time and chain-of-custody documentation can you support?
- Can you separate exploratory R&D testing from GLP/ISO 10993 testing in the quote?

## Candidate Details

### Materials Metric

- Source: [https://materialsmetric.com/](https://materialsmetric.com/)
- Service type: `custom_biomaterials_characterization`
- Evidence from source: Company page describes analytical testing, materials characterization, microscopy, spectroscopy, chemical analysis, biocompatibility, tissue engineering, and custom method development.
- Likely covers: custom study design, microscopy, materials characterization, biomaterials evaluation
- Unknowns to ask:
  - Can they execute the entire 12-run H-A service request as a custom R&D study?
  - Can they include pH, osmolality, and conductivity, or should media tests be subcontracted?
  - Can they return raw exports plus chain-of-custody by run_id?
- Risk: Custom scope must be tightly controlled so it returns the exact LIMINA fields rather than a broad narrative report.

### The Osmolality Lab

- Source: [https://theosmolalitylab.com/](https://theosmolalitylab.com/)
- Service type: `media_physicochemical_testing`
- Evidence from source: Public service page lists osmolality testing plus conductivity and pH testing.
- Likely covers: osmolality, conductivity, pH
- Unknowns to ask:
  - Can they run matched pre/post aliquots from 37 C acellular neural-medium soaks?
  - Can they preserve one result per LIMINA run_id rather than batch averages?
  - Can they accept PEDOT:PSS/alginate/laminin soak media as nonclinical R&D samples?
- Risk: May not cover hydrogel swelling, delamination, or imaging; likely needs pairing with a materials lab.

### Cambridge Polymer Group

- Source: [https://www.campoly.com/services/analytical-testing/material-characterization-techniques/hydrogel-characterization/](https://www.campoly.com/services/analytical-testing/material-characterization-techniques/hydrogel-characterization/)
- Service type: `hydrogel_characterization`
- Evidence from source: Hydrogel characterization page describes swell ratio testing and advanced techniques including DSC, TGA, GPC, AFM, and SEM.
- Likely covers: swelling ratio, hydrogel physical characterization, microscopy or surface characterization
- Unknowns to ask:
  - Can they do simple optical transparency and delamination scoring on MEA witness coupons?
  - Can they handle hydrated alginate-laminin-PEDOT:PSS coupons under culture-medium timing?
  - Can they pair physical scoring with pH/osmolality/conductivity or only coupon characterization?
- Risk: May be stronger for material characterization than cell-culture medium physicochemical testing.

### MilliporeSigma Cell Culture Media Stability and Testing Services

- Source: [https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services](https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services)
- Service type: `cell_culture_media_testing`
- Evidence from source: Service page lists cell culture media stability/testing and standard release specification tests including appearance, pH, osmolality, endotoxin, bioburden, and solubility.
- Likely covers: appearance, pH, osmolality
- Unknowns to ask:
  - Can conductivity be added to the report?
  - Can the service handle customer-prepared hydrogel coupon soak media rather than only standard media lots?
  - Can they return raw sample-level values in the LIMINA CSV schema?
- Risk: May be optimized for media products and release specifications, not custom hydrogel coupon extraction workflows.

### Nikon BioImaging Lab USA

- Source: [https://www.microscope.healthcare.nikon.com/bioimaging-centers/nikon-bioimaging-labs/boston-usa](https://www.microscope.healthcare.nikon.com/bioimaging-centers/nikon-bioimaging-labs/boston-usa)
- Service type: `microscopy_and_image_analysis`
- Evidence from source: Service page describes contract microscope-based imaging and analysis for biotech/pharma/research, including 2D/3D samples, organoids, spheroids, and microphysiological systems.
- Likely covers: imaging, image analysis, experimental design consultation
- Unknowns to ask:
  - Can they image hydrated coupons without disturbing swelling state?
  - Can they provide delamination/transparency measurements from coupon images?
  - Can they coordinate with a media testing lab?
- Risk: Does not cover pH/osmolality/conductivity and may be overpowered for simple H-A coupon inspection.

### SGS USA Extractables and Leachables in Medical Devices

- Source: [https://www.sgs.com/en-us/services/extractables-and-leachables-in-medical-devices](https://www.sgs.com/en-us/services/extractables-and-leachables-in-medical-devices)
- Service type: `iso_10993_chemical_characterization`
- Evidence from source: Service page describes ISO 10993-18 chemical characterization and extractables/leachables testing for medical devices and related products.
- Likely covers: extractables, leachables, chemical characterization, toxicological assessment support
- Unknowns to ask:
  - Can they run a non-GLP exploratory aqueous neural-medium soak before a full ISO 10993-18 program?
  - Can they avoid consuming all limited H-A coupon material?
  - What sample mass or surface area is required?
- Risk: Too heavy for first H-A unless the project wants early E&L escalation; useful after H-A if leachables are a key decision.

### Hohenstein Medical Extractables and Leachables

- Source: [https://www.hohenstein.us/en-us/medical-device-testing-lab/medical-device-extractables-leachables](https://www.hohenstein.us/en-us/medical-device-testing-lab/medical-device-extractables-leachables)
- Service type: `iso_10993_chemical_characterization`
- Evidence from source: Service page describes ISO 10993-18 extractables/leachables, sample preparation, VOC/SVOC/NVOC and elemental impurity screening, and GLP/ISO support.
- Likely covers: ISO 10993-18 chemical characterization, aqueous extract screening, elemental impurity screening, toxicological risk assessment support
- Unknowns to ask:
  - Can they adapt extraction to neural culture medium or compatible aqueous soak conditions?
  - Can they support an exploratory H-A screen before regulated-style chemistry?
  - What sample number and surface-area requirements apply to hydrogel-coated MEA coupons?
- Risk: Regulatory E&L scope may be more expensive and slower than the minimal H-A decision package.

### Intertek China Healthcare and Medical Device Testing

- Source: [https://www.intertek.com.cn/](https://www.intertek.com.cn/)
- Service type: `apac_materials_and_healthcare_testing`
- Evidence from source: Official China site describes testing, inspection, certification, and healthcare/medical-device related services; exact pH/osmolality/conductivity coverage must be confirmed by RFQ.
- Likely covers: China/APAC local intake, materials or medical-device testing routing, possible chemical/physical analysis
- Unknowns to ask:
  - Can the China lab route a non-GLP R&D hydrogel-coupon soak-media study to pH, osmolality, conductivity, and appearance testing?
  - Can coupon physical scoring or microscopy be paired with media measurements while preserving run_id labels?
  - Can they accept and return the exact LIMINA raw-measurement CSV plus source-file provenance?
- Risk: Service fit is broader and must be routed by RFQ; do not assume exact H-A field coverage until a technical reply confirms it.

### WuXi AppTec Medical Device Testing

- Source: [https://www.wuxiapptec.com/](https://www.wuxiapptec.com/)
- Service type: `medical_device_biocompatibility_and_chemistry`
- Evidence from source: Official company site lists global testing services; use RFQ to route specifically to medical-device chemistry, biocompatibility, or extractables/leachables feasibility.
- Likely covers: medical-device testing routing, biocompatibility or chemistry escalation, China/APAC logistics
- Unknowns to ask:
  - Can they run a small exploratory aqueous/neural-medium extract screen before full ISO 10993 work?
  - Can they add basic pH, osmolality, conductivity, and appearance fields, or should they only be used after H-A flags chemical risk?
  - What surface area, coupon count, sample volume, SDS, and chain-of-custody requirements apply?
- Risk: Likely better for regulated-style chemistry/biocompatibility escalation than the fastest minimal H-A panel.

### TUV SUD China Medical Device Testing

- Source: [https://www.tuvsud.cn/](https://www.tuvsud.cn/)
- Service type: `medical_device_testing_and_biocompatibility`
- Evidence from source: Official China site covers medical-device testing and certification services; use RFQ to confirm whether exploratory material-blank measurements can be scoped separately from full regulatory testing.
- Likely covers: medical-device testing routing, biocompatibility or chemical characterization escalation, China/APAC contact path
- Unknowns to ask:
  - Can they scope the first H-A pass as non-GLP R&D instead of a full regulatory submission package?
  - Can they return run_id-level raw pH/osmolality/conductivity and coupon inspection values in the LIMINA schema?
  - If not, can they quote only the later ISO 10993 chemical characterization path after H-A passes?
- Risk: May be too regulatory and too slow for the minimal first H-A decision unless chemistry/biocompatibility escalation is required.

### PONY Testing Medical Device and Life-Science Services

- Source: [https://www.ponytest.com/](https://www.ponytest.com/)
- Service type: `china_third_party_testing`
- Evidence from source: Official site describes third-party testing services across health, safety, and product categories; exact medical-device, media chemistry, and custom R&D coverage must be confirmed.
- Likely covers: China local third-party testing intake, possible physicochemical or product-safety routing, possible medical-device test routing
- Unknowns to ask:
  - Can they route a nonclinical hydrogel-coupon neural-medium soak study to pH, osmolality, conductivity, appearance, and coupon inspection outputs?
  - Can they preserve one row per run_id and return raw exports/source files?
  - Can they keep the scope exploratory rather than certificate-only or pooled product-release testing?
- Risk: Broad testing company; H-A fit depends entirely on technical routing and must be confirmed before sample shipment.

## Boundary

Vendor capability claims do not count as material evidence. Only returned real run-level measurements that pass LIMINA QC and claim audit can advance the material.
