# ZRC-ND-3.5M Guard minimum validation BOM

**ID:** `zrc_nd_3p5m_guard_bom_v0_1`
**Parent validation package:** `zrc_nd_3p5k_guard_validation_v0_1`

## Objective

Define a procurement-ready minimum bill of materials for non-cell validation of the ZRC-ND-3.5M Guard lead without implying that any item is already proven compatible with CL1-like neural wetware.

## Items

### Assay

| ID | Role | Required spec | Anchor | Reject if | Evidence |
| --- | --- | --- | --- | --- | --- |
| `lactate_assay` | waste-clearance readout | Quantitative lactate assay compatible with cell culture supernatant or matched medium, with medium-matched standards/spike recovery. | Abcam L-Lactate Assay Kit ab65331 or equivalent enzymatic/colorimetric lactate assay. [source](https://www.abcam.com/en-us/products/assay-kits/l-lactate-assay-kit-colorimetric-ab65331) | No demonstrated compatibility with culture media or no workable spike/recovery controls. | `lactate_assay_cell_culture_vendor` |
| `ammonia_assay` | waste-clearance readout | Quantitative ammonia/ammonium assay compatible with cell culture media or matched medium standards. | Abcam Ammonia Assay Kit ab83360 or equivalent ammonia/ammonium assay. [source](https://www.abcam.com/en-us/products/assay-kits/ammonia-assay-kit-ab83360) | Cannot run pH/matrix-matched standards or cannot distinguish matrix interference. | `ammonia_assay_cell_culture_vendor`, `ammonia_importance_review_1996` |
| `bdnf_elisa` | trophic-factor retention readout | BDNF ELISA or validated immunoassay compatible with the selected species/proxy and cell culture supernatant matrix. | Abcam Human BDNF ELISA Kit ab212166 or species-matched equivalent. [source](https://www.abcam.com/en-us/products/elisa-kits/human-bdnf-elisa-kit-ab212166) | Wrong species/form specificity or no matrix recovery plan. | `bdnf_uniprot_p23560`, `bdnf_elisa_cell_culture_vendor` |
| `ngf_elisa` | trophic-factor retention readout | NGF ELISA or validated immunoassay compatible with the selected species/proxy and cell culture supernatant matrix. | R&D Systems Human beta-NGF DuoSet ELISA DY256 or species-matched equivalent. [source](https://www.rndsystems.com/products/human-beta-ngf-duoset-elisa_dy256) | Wrong species/form specificity or no matrix recovery plan. | `ngf_uniprot_p01138`, `ngf_elisa_cell_culture_vendor` |

### Coating Reagent

| ID | Role | Required spec | Anchor | Reject if | Evidence |
| --- | --- | --- | --- | --- | --- |
| `dopamine_hcl_pda_primer` | PDA primer precursor for controlled surface-only route | Dopamine hydrochloride or equivalent PDA precursor suitable for research coating trials, with lot documentation and no direct cell exposure before blank testing. | Sigma-Aldrich dopamine hydrochloride or equivalent research-grade dopamine hydrochloride. [source](https://www.sigmaaldrich.com/US/en/product/sigma/h8502-) | No lot/COA documentation, unknown purity, or incompatible contaminants for media blank testing. | `polympc_polyprev_retained_pore_2019`, `pda_click_pmpc_membrane_2025` |
| `mpc_monomer_or_polympc` | zwitterionic MPC chemistry source | MPC monomer or preformed polyMPC/PMPC compatible with surface-only coating development; document inhibitor, purity, polymerization or immobilization route. | Sigma-Aldrich 2-Methacryloyloxyethyl phosphorylcholine, 97%, or equivalent MPC source. [source](https://www.sigmaaldrich.com/US/en/product/aldrich/730114) | Unknown inhibitor/purity, no route to remove soluble residuals, or no way to check extractables after coating. | `polympc_polyprev_retained_pore_2019`, `pda_click_pmpc_membrane_2025`, `zwitterionic_membrane_antifouling_2016` |

### Housing

| ID | Role | Required spec | Anchor | Reject if | Evidence |
| --- | --- | --- | --- | --- | --- |
| `coc_observation_housing` | observed side-stream coupon cartridge or screening chip | COC/COP wetted housing or chip with optical access, mini-Luer/Luer-style ports, low dead volume, and no PDMS in the primary wetted path. | COC microfluidic chip with Mini Luer ports, such as a ChipShop/Darwin or Sigma COC screening chip. [source](https://darwin-microfluidics.com/products/open-4-straight-channels-chip-mini-luer) | PDMS primary wetted path, opaque housing, unknown adhesive exposure, or no way to observe bubbles/precipitate. | `organ_chip_perfusion_review_2022`, `coc_cop_ooc_material_review_2026`, `coc_pdms_sorption_2025` |

### Instrumentation

| ID | Role | Required spec | Anchor | Reject if | Evidence |
| --- | --- | --- | --- | --- | --- |
| `media_integrity_readouts` | blank-integrity and silent-failure readouts | pH, conductivity, osmolality, turbidity/visual inspection, and flow/pressure proxy readouts sufficient to evaluate gate thresholds. | Lab pH meter, conductivity meter, osmometer access, plate reader or turbidity/visual log, and simple flow/pressure monitoring. - | Cannot measure pH/osmolality/conductivity drift relative to no-module control. | `organ_chip_perfusion_review_2022`, `neural_microfluidic_systems_2023` |

### Membrane

| ID | Role | Required spec | Anchor | Reject if | Evidence |
| --- | --- | --- | --- | --- | --- |
| `rc_3p5k_primary_membrane` | lead primary exchange membrane | Regenerated cellulose dialysis membrane or tubing, nominal 3.5 kDa MWCO, low protein binding, aqueous medium compatible, enough area for coupon replicates. | Repligen Spectra/Por 3 Standard Grade RC, 3.5 kD MWCO trial kit or equivalent RC membrane. [source](https://store.repligen.com/products/spectra-por-3-dialysis-trial-kit) | Cellulose ester only, unknown MWCO, unknown preservative, high protein binding, or format cannot support replicated coupon testing. | `rc_3p5k_repligen_vendor_spec`, `dialysis_mwco_principle_thermo`, `low_binding_rc_membrane_vendor` |
| `rc_10k_challenge_membrane` | high-clearance challenge comparator | Regenerated cellulose dialysis membrane or tubing, nominal 10 kDa MWCO, same general geometry class as the 3.5 kDa membrane when possible. | Repligen Spectra/Por 7 pre-treated Standard Grade RC, 10 kD MWCO or equivalent matched RC membrane. [source](https://www.repligen.com/products/dialysis/spectrapor-dialysis-tubing-and-membranes/spectrapor-pre-treated-standard-grade-rc-dialysis-tubing-and-trial-kits) | Cannot be compared by membrane area/exposure to the 3.5 kDa lead. | `dialysis_mwco_principle_thermo`, `bdnf_uniprot_p23560`, `ngf_uniprot_p01138` |

### Prefilter

| ID | Role | Required spec | Anchor | Reject if | Evidence |
| --- | --- | --- | --- | --- | --- |
| `sfca_guard_filter` | low-binding debris guard | Sterile 0.22 um SFCA syringe or inline filter with low protein binding, low extractables/leachables, and low hold-up volume. | CELLTREAT 0.22 um sterile SFCA syringe filter or equivalent low-binding SFCA guard. [source](https://www.celltreat.com/product/229765/) | High protein binding, surfactant leaching concern, large hold-up volume, or unknown membrane material. | `low_binding_membrane_media_technical` |
| `pes_guard_filter_backup` | low-binding debris guard backup | Sterile 0.22 um PES syringe or inline filter with low protein binding and cell-culture media compatibility. | Sterile Millex or equivalent PES 0.22 um low-binding syringe filter. [source](https://www.fishersci.com/content/dam/fishersci/en_US/documents/programs/scientific/technical-documents/data-sheets/emd-millipore-sterile-millex-syringe-filters-data-sheet.pdf) | Binding/hold-up is not characterized enough for trophic-factor recovery testing. | `low_binding_membrane_media_technical` |

## Source Refs

- `rc_3p5k_repligen_vendor_spec`
- `dialysis_mwco_principle_thermo`
- `low_binding_membrane_media_technical`
- `polympc_polyprev_retained_pore_2019`
- `pda_click_pmpc_membrane_2025`
- `zwitterionic_membrane_antifouling_2016`
- `organ_chip_perfusion_review_2022`
- `coc_cop_ooc_material_review_2026`
- `coc_pdms_sorption_2025`
- `lactate_assay_cell_culture_vendor`
- `ammonia_assay_cell_culture_vendor`
- `bdnf_elisa_cell_culture_vendor`
- `ngf_elisa_cell_culture_vendor`
- `neural_microfluidic_systems_2023`
