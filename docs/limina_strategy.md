# LIMINA Strategy

LIMINA means **Living Interface Materials Intelligence for Neural Adaptation**
in this workspace.

The project goal is to discover material technologies that help living neural
cells form a stable, low-noise, long-lived interface with silicon or MEA-like
hardware. The focus is cell adaptation and interface quality, not direct control
of a CL1 device or any CL1 API.

## Working Hypothesis

A useful material for CL1-like biological computing should optimize the cell
microenvironment and the electrical interface at the same time:

- Cells need soft, hydrated, ECM-like, low-toxicity surfaces.
- Electrodes need low impedance, charge-injection capacity, and stable mixed
  ionic/electronic transport.
- The interface must survive culture medium, sterilization, perfusion, and
  repeated stimulation/recording.
- The best technology may be a layered interface, not a single magic material.

## Evidence Anchors

The first search pass supports these design priors:

- Conductive hydrogels are attractive because they combine softness, hydration,
  electrical activity, and tissue-like microenvironments.
- PEDOT:PSS is a leading neural bioelectronic coating because it supports mixed
  ionic/electronic conduction and can reduce electrode impedance, but residual
  reagents, swelling, delamination, and long-term stability must be controlled.
- Graphene and related carbon materials offer conductivity, transparency, and
  flexible neural interfaces, but long-term safety and process reproducibility
  remain important caveats.
- Zwitterionic and PEG-like layers can reduce nonspecific protein/cell fouling,
  but purely antifouling surfaces may also reduce desired neuron adhesion unless
  paired with ECM ligands or patterned adhesive domains.
- Brain-like substrate stiffness, often near sub-kPa to low-kPa regimes, is a
  recurring target for neuronal survival, neurite outgrowth, and reduced glial
  activation, though results vary by cell type and assay.

## Scoring Dimensions

Each candidate is scored from 1 to 5 on:

- `cell_compatibility`: toxicity, viability, neuronal adhesion, maturation.
- `electrical_coupling`: impedance, charge transfer, mixed conduction.
- `mechanical_match`: softness, hydration, strain buffering, 2D/3D support.
- `culture_stability`: stability in medium, sterilization, leaching, swelling.
- `mea_integration`: compatibility with MEA fabrication and electrode geometry.
- `novelty_upside`: potential for a non-obvious CL1-specific improvement.
- `risk_control`: how manageable the experimental and safety risks appear.

The score is not a truth claim. It is a queueing tool that tells the research
agent which hypotheses deserve deeper reading, modeling, or wet-lab testing.

## Agent Loop

1. Search current literature and patents for neural interface material signals.
2. Extract claims into structured evidence: material, mechanism, assay, outcome,
   caveat, and source.
3. Generate candidate interface designs as material stacks.
4. Score candidates with the current rubric.
5. Select top candidates for deeper computational or experimental design.
6. Update the rubric when new evidence contradicts the current assumptions.

## Local Compute Role

Local compute on a MacBook M4 Pro should be used for reproducible helper tasks:

- ranking and filtering candidate materials;
- calculating molecular descriptors for small monomers/additives;
- simple polymer fragment screening with RDKit/xTB where useful;
- small atomistic or coarse simulations through ASE/OpenMM;
- literature metadata storage and report generation.

Codex remains the primary research agent. Local models are optional helpers, not
the scientific decision maker.
