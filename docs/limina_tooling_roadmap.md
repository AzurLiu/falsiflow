# LIMINA Tooling Roadmap

This roadmap is tuned for a MacBook M4 Pro plus Codex as the primary research
agent. Local compute is used where it can multiply the agent's search and
screening efficiency; it is not expected to replace wet-lab validation or
large-scale cloud/HPC simulation.

## Fixed External-Material Priorities

1. `LIMINA-External-1`: selective neuronal-media waste cartridge.
2. `LIMINA-External-2`: hybrid low-adsorption sterile tubeset and manifold.
3. `LIMINA-External-3`: controlled gas-exchange membrane module.
4. `LIMINA-External-4`: bubble-suppressing surface/material geometry.
5. `LIMINA-External-5`: humidity-resistant low-noise electrical contacts, seals,
   and headstage materials.
6. `LIMINA-External-6`: transparent low-autofluorescence enclosure/window
   materials.
7. `LIMINA-External-7`: ordinary structural enclosure materials.

## Project Tool Layers

### 1. Evidence Engine

Purpose:

- keep every material hypothesis tied to literature, patents, assay results, and
  caveats;
- prevent the agent from promoting plausible but unsupported ideas.

Tools:

- NCBI PubMed/PubMed Central through E-utilities;
- Semantic Scholar Academic Graph API;
- Zotero for local paper management;
- local JSON now, SQLite/DuckDB later.

First build:

- query packs for each priority lane;
- normalized evidence records with `claim`, `assay`, `material`, `readout`,
  `caveat`, and `source_url`.

### 2. Candidate and Recipe Builder

Purpose:

- turn a broad idea like "better gas exchange membrane" into a testable material
  architecture, formulation, and experiment plan.

Tools:

- Codex for synthesis and decomposition;
- structured JSON candidate records;
- later: a small schema validator and report generator.

First build:

- recipe templates for waste cartridges, hybrid tubesets, gas-exchange modules,
  and bubble-control surfaces.

### 3. Descriptor and Lightweight Simulation Layer

Purpose:

- cheaply reject risky monomers, crosslinkers, additives, coatings, and small
  membrane chemistries before deeper study.

Mac-local tools:

- RDKit: molecular descriptors, substructure filters, simple property proxies.
- xTB/GFN2-xTB: small-molecule and fragment conformers, charges, rough
  energetics.
- ASE: common structure/calculator interface.
- OpenMM/OpenFF: small soft-matter or solvent interaction simulations when the
  system is small enough.
- pymatgen: inorganic/solid materials handling.

Use cases:

- screen low-leachable coatings and additives;
- compare hydrophobicity/charge/polar surface proxies;
- generate small molecule alerts for potential cytotoxicity;
- test simple diffusion/adsorption hypotheses before expensive experiments.

### 4. Atomistic Foundation Model Watchlist

Purpose:

- use modern ML interatomic potentials as DFT substitutes where the chemistry is
  within their domain.

Tools to evaluate:

- MatterSim and MatterSim-MT: ASE-compatible materials simulation and
  multi-property characterization.
- MACE foundation models: ASE-compatible universal potentials.
- Orb-v3: universal atomistic models with confidence estimates.
- UMA / FAIR Chemistry: broad universal models for atoms.
- SevenNet: universal potential with ASE and LAMMPS support.
- MatterGen: generative inorganic material model; useful for future solid
  components, less central for wet biomaterials.

Caveat:

- These are strongest for inorganic crystals, catalysts, and atomistic materials.
  They are not a magic answer for warm, hydrated, protein-rich neuronal culture
  interfaces. Use them as filters and idea generators, not as proof.

### 5. Active Learning Optimizer

Purpose:

- maximize discovery under small compute and limited experiments by choosing the
  next best candidate batch.

Tools:

- Optuna ask-and-tell for simple, robust batched optimization.
- scikit-learn GaussianProcessRegressor for transparent surrogate models.
- BoTorch later if multi-objective Bayesian optimization becomes complex.

Objectives:

- maximize cell-fit score and electrical/transport performance;
- minimize leachable, adsorption, cytotoxicity, bubble, and manufacturability
  risks;
- keep uncertainty explicit so the agent explores, not only exploits.

### 6. Assay Planner and Result Store

Purpose:

- convert ranked candidates into wet-lab-readable plans and capture results back
  into the optimizer.

Initial readouts:

- Live/Dead or viability;
- neurite outgrowth / network morphology;
- medium pH/osmolality drift;
- lactate/ammonium removal for filters;
- protein/growth-factor retention;
- flow and bubble events;
- electrode impedance/noise drift where relevant;
- 7/14/28-day stability.

Storage:

- JSON reports now;
- SQLite or DuckDB once repeated experiments begin.

## Highest-Leverage Technologies for M4 Pro Scale

1. **Bayesian / active learning loops**: save compute and wet-lab iterations by
   selecting the next most informative candidates.
2. **Descriptor-first screening**: RDKit/xTB descriptors are cheap and useful for
   eliminating bad monomers, coatings, and additives.
3. **ASE calculator abstraction**: one candidate structure can be tested with
   simple calculators first and ML potentials later.
4. **Modern universal ML potentials**: MatterSim, MACE, Orb, UMA, and SevenNet can
   be much cheaper than DFT for suitable atomistic problems.
5. **Evidence-grounded RAG**: PubMed/Semantic Scholar/Zotero records keep the
   agent aligned with real assays and failure modes.
6. **MLX/Ollama local helpers**: useful for local embeddings, summarization
   drafts, or offline operation, but not the scientific decision layer.

## Near-Term Implementation Order

1. Create an evidence schema and import script.
2. Add candidate recipe schemas for the four top external-material lanes.
3. Add RDKit/xTB environment setup and descriptor scripts.
4. Add Optuna/scikit-learn optimizer for candidate batch selection.
5. Evaluate one ML potential through ASE on a tiny benchmark before adopting it.
6. Generate wet-lab assay plans for top candidates.

## Tool Selection Rule

Prefer boring, inspectable tools for the decision loop. Add frontier models only
when they produce a measurable gain in ranking, uncertainty reduction, or
experiment design.
