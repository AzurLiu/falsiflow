# CL1 External Materials Map

This note separates public facts about CL1 from material choices that are
reasonable engineering inferences from adjacent MEA, perfusion, and
organ-on-chip systems. Cortical Labs has not published a full bill of materials
for CL1, so inferred materials should be treated as LIMINA research targets, not
confirmed CL1 composition.

## Public CL1 Hardware Signals

Official and design sources describe CL1 as a self-contained system where the
cell culture is only one part of a larger biological-computing instrument:

- A modular, transparent enclosure that can be desktop or rack-mounted.
- Embedded processing, control, recording, and life support.
- A closed-loop fluid system with temperature and gas regulation.
- Single-use sterile tube sets to simplify setup and prevent contamination.
- A removable MEA headstage with a locking mechanism and precise electrical
  bonding.
- A pogo-pin array for electrical contact.
- Embedded heating near the MEA headstage.
- A capacitive touchscreen for local monitoring.
- USB and external ports for cameras, sensors, actuators, and broader testing.
- A perfusion architecture with media supply, gas exchange, gas mixing,
  peristaltic pumps, filtration, bubble control, and a cell-hosting compartment.

## External Material Zones

### 1. Transparent Enclosure and Chassis

Probable role:

- protect the wetware and electronics;
- make the living system visible for monitoring and product trust;
- support desktop and rack-mounted deployment;
- reduce contamination from normal lab handling.

Candidate materials:

- polycarbonate, PMMA/acrylic, COC/COP, glass, or coated glass;
- aluminum or stainless subframes where stiffness, heat spreading, or EMI
  control matters;
- transparent coatings with anti-fog, anti-scratch, and low-outgassing behavior.

LIMINA opportunity:

- low-autofluorescence transparent enclosure/window materials;
- coatings that resist disinfectants and repeated wipe-down;
- thermal-insulating but optically clear panels;
- modular panels that separate service access from the sterile fluid path.

### 2. Sterile Tubeset and Fluidic Manifold

Probable role:

- circulate medium without introducing leachables or bubbles;
- support long-term low-shear perfusion;
- simplify sterile setup as a consumable module.

Candidate materials:

- platinum-cured silicone for peristaltic pump sections and gas permeability;
- FEP/PTFE/PFA tubing for low adsorption and chemical inertness;
- PEEK for rigid, chemically resistant microfluidic connections;
- COC/COP, PC, PMMA, or PS for reservoirs and transparent manifolds;
- parylene or other barrier coatings where PDMS/silicone absorption is risky.

LIMINA opportunity:

- hybrid tubesets: silicone only where pumping/gas transfer is needed, FEP/PTFE
  elsewhere to reduce molecule adsorption;
- bubble-resistant connector geometries;
- low-leachable adhesive-free bonds;
- disposable manifolds with integrated sampling and degassing.

### 3. Gas Exchange and Gas Mixing

Probable role:

- maintain oxygen, CO2, pH, and dissolved gas balance outside a standard
  incubator;
- keep cells alive for weeks to months.

Candidate materials:

- silicone or PDMS membranes when gas permeability matters;
- fluoropolymer membranes where chemical inertness and lower absorption matter;
- hollow-fiber membranes from polysulfone, polypropylene, cellulose
  derivatives, or silicone variants;
- gas-impermeable COC/COP/PC reservoirs when gas exchange must be localized.

LIMINA opportunity:

- membrane modules that tune oxygenation without excessive evaporation;
- gas exchange surfaces with lower absorption of hydrophobic drugs;
- sensor-integrated gas exchange cartridges for pH/DO feedback control.

### 4. Filtration and Waste Management

Probable role:

- remove waste such as lactate/ammonium while retaining useful proteins and
  growth factors;
- support longer intervals between media changes.

Candidate materials:

- PES, polysulfone, cellulose acetate, regenerated cellulose, or nylon
  membranes depending on molecular weight cut-off and protein binding;
- activated carbon or ion-exchange elements only if validated not to strip
  growth factors unpredictably;
- low-protein-binding housings and seals.

LIMINA opportunity:

- selective waste filters that preserve neurotrophic factors;
- modular cartridges optimized for neuronal medium rather than generic
  mammalian cell culture;
- indicators for filter exhaustion and protein loss.

### 5. MEA Headstage, Electrical Contacts, and Thermal Control

Probable role:

- make stable, low-noise electrical connection to the MEA;
- allow sterile dish removal;
- keep the culture near physiological temperature.

Candidate materials:

- gold-plated pogo pins or noble-metal contact finishes;
- corrosion-resistant stainless or spring alloys kept outside the wet path;
- PEEK, PEI/Ultem, LCP, or ceramic insulators for dimensional stability;
- silicone, FKM, EPDM, or PTFE seals depending on sterilization and leachables;
- copper/aluminum heat spreaders isolated from fluidics.

LIMINA opportunity:

- low-noise, humidity-resistant contact stacks;
- spring/contact materials with less fretting corrosion;
- gasket materials that keep sterility without outgassing or leaching;
- thermal interface layers that avoid hot spots near cells.

### 6. Sensors, Ports, and User-Service Interfaces

Probable role:

- pH, dissolved oxygen, temperature, flow, pressure, leak, bubble, and impedance
  monitoring;
- external cameras, actuators, and experimental devices.

Candidate materials:

- optical windows in glass/COC/COP/PMMA depending on imaging wavelength;
- PEEK/fluoropolymer wetted sensor housings;
- medical-grade connector plastics and elastomer seals;
- antimicrobial or wipe-compatible exterior coatings.

LIMINA opportunity:

- sensor-compatible materials with low drift in warm humid environments;
- self-diagnosing ports that detect tube mis-seat, leaks, and bubbles;
- exterior materials that tolerate ethanol/isopropanol/hypochlorite workflows.

## External-Material Scoring Add-On

For non-cell-contact materials, LIMINA should add these dimensions:

- `low_leachables`: minimal extractables into medium or gas path.
- `adsorption_control`: low loss of growth factors, drugs, hormones, and small
  molecules.
- `sterility_workflow`: compatible with single-use or validated cleaning.
- `gas_transport_fit`: gas permeability only where wanted.
- `bubble_control`: reduces nucleation, trapping, and transition bubbles.
- `thermal_stability`: supports stable 37 C operation without local hot spots.
- `manufacturability`: injection molding, bonding, assembly, and quality control.
- `serviceability`: easy cartridge/tubeset replacement without contamination.

## Immediate Research Hypotheses

Current external-material discovery priority for LIMINA:

1. `LIMINA-External-1`: selective neuronal-media waste cartridge.
2. `LIMINA-External-2`: hybrid low-adsorption sterile tubeset and manifold.
3. `LIMINA-External-3`: controlled gas-exchange membrane module.
4. `LIMINA-External-4`: bubble-suppressing surface/material geometry.
5. `LIMINA-External-5`: humidity-resistant low-noise electrical contacts, seals,
   and headstage materials.
6. `LIMINA-External-6`: transparent low-autofluorescence enclosure/window
   materials.
7. `LIMINA-External-7`: ordinary structural enclosure materials.

1. A CL1-like platform may benefit from a **two-material tubeset**: platinum-cured
   silicone for pump/gas sections and FEP/PTFE/PEEK for low-adsorption media
   transport.
2. A **selective waste filtration cartridge** designed around neuronal medium
   could be as important as the cell-facing substrate, because it controls
   long-term health and media-change frequency.
3. **Bubble-control materials and geometries** may be a hidden performance lever:
   bubbles can disrupt flow, gas exchange, recording stability, and cell stress.
4. **Transparent, low-autofluorescence, disinfectant-resistant enclosure
   materials** matter if CL1 is used as a visible, monitorable lab instrument.
5. **Humidity-resistant electrical-contact materials** are a separate discovery
   lane from cell-contact coatings, because signal integrity depends on the
   headstage, pogo pins, seals, and thermal design.

## Sources

- Cortical Labs CL1 product page:
  https://www.corticallabs.com/cl1.html?pubDate=20250329
- Victorian Premier's Design Awards CL1 page:
  https://premiersdesignawards.vic.gov.au/entries/2025/product-design/cortical-labs-cl1-biological-computer
- D+I / Capgemini CL1 product design page:
  https://www.design-industry.com.au/cortical-labs-cl1
- Cortical Labs perfusion circuit poster:
  https://corticallabs.com/readings/posters/perfusion_poster_v7.pdf
- Microfluidic organ-on-chip material review:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9966054/
- Biomedical organ-on-chip materials review:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7387427/
- PDMS biological implications in microfluidic cell culture:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC2792742/
- Microfluidic leakage/materials review:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9490024/
