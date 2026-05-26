# LIMINA-External-1 Research Brief

## Objective

Discover material technologies for a **selective neuronal-media waste cartridge**
that can remove harmful low-molecular-weight waste while preserving the soluble
factors that neural cultures use for survival, maturation, and network stability.

## Current Working Requirements

- Remove or buffer: lactate, ammonium/ammonia, small inhibitory metabolites, and
  debris.
- Preserve: BDNF, NGF, FGF, EGF, albumin, transferrin, hormones, secretome
  factors, and extracellular-vesicle-like signaling where relevant.
- Avoid: leachables, protein stripping, pH drift, osmolality drift,
  electrochemical byproducts, reactive oxygen byproducts, and excess shear.
- Make it testable with 7/14/28-day neural culture readouts.

## First-Pass Ranking

The current ranking is generated with:

```bash
conda activate limina
python scripts/rank_limina_candidates.py \
  --profile data/external_scoring_profile.json \
  --candidates data/external_material_candidates.json \
  --out reports/external1_waste_cartridge_ranking.md
```

Top result:

1. **Regenerated-cellulose dialysis exchange module**  
   Best first baseline because it matches the core separation logic: let small
   wastes exchange while retaining larger proteins/growth factors.

2. **Layered neuronal-media waste cartridge**  
   More ambitious and probably more novel, but complexity and unintended
   adsorption risk keep it behind the simpler dialysis baseline for now.

3. **Ion-concentration-polarization media regenerator**  
   High novelty and monitorability, but electrochemical byproducts, pH drift,
   and neural-medium compatibility are serious unknowns.

Held back:

- **Broad adsorbent carbon/resin bed**: likely too nonselective; high risk of
  stripping useful hormones, proteins, lipids, vitamins, or trophic factors.
- **Enzyme-assisted lactate polishing**: reactive byproducts and enzyme
  instability make it a second-phase concept.
- **Ammonium-selective ion-exchange hydrogel**: attractive as a module, but
  essential-cation competition and extractables must be solved.

## Evidence Synthesis

- Medium exchange is not neutral. It removes waste and replenishes nutrients,
  but it can also remove cell secretome components that mediate communication.
  That makes selective waste management more valuable than bulk medium exchange.
- Dialysis-like partitioning is directly relevant because membrane MWCO can be
  used to exchange low-MW medium components while retaining high-MW growth
  factors and proteins.
- Ammonia/ammonium and lactate are established mammalian cell-culture stressors;
  lactate and ammonia can interact, so monitoring only one may be misleading.
- Modern spent-media regeneration work shows that electromembrane or ICP-style
  processes can remove critical waste products, but neural culture adds stricter
  pH, conductivity, and byproduct constraints.
- Metabolomics evidence suggests inhibitory waste is broader than lactate and
  ammonium, so the cartridge should eventually be evaluated with untargeted or
  semi-targeted medium analytics.
- Neural microfluidic literature supports the importance of perfusion,
  gradients, and shear control, but does not solve cartridge material selection
  by itself.

## Proposed Baseline Experiment

Start with a passive side-stream dialysis cartridge:

- membrane: regenerated cellulose, multiple MWCO options;
- loop: neuronal medium side stream, not directly over cells;
- comparison: no cartridge, bulk medium exchange, fresh-medium perfusion;
- first readouts: lactate, ammonium, pH, osmolality, albumin retention, BDNF/NGF
  retention, total protein, flow resistance, and 7-day conditioned-media
  viability.

Decision rule:

- If low-MW waste removal works while BDNF/NGF/albumin retention is high, the
  dialysis baseline becomes the control architecture.
- If retention fails, prioritize zwitterionic/low-fouling membrane surface work.
- If lactate/ammonium clearance is too weak, add a confined ion-exchange or ICP
  polishing stage in a side stream rather than inside the cell chamber.

## Next Candidate Generation Targets

1. Regenerated-cellulose MWCO sweep: 1 kDa, 3.5 kDa, 10 kDa, 20 kDa.
2. Low-binding PES/SFCA prefilter variants for debris control.
3. Zwitterionic-coated RC/PES membranes for lower protein fouling.
4. Confined weak ion-exchange hydrogel for ammonium polishing.
5. ICP side-stream module only after passive dialysis baseline is quantified.

## Key Source Set

- Frontiers review on medium exchange, secretome loss, and dialysis-like medium
  partitioning:
  https://www.frontiersin.org/articles/10.3389/fbioe.2020.00911/full
- ICP spent-media regeneration:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11718426/
- Inhibitory metabolite identification:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8427323/
- Neural microfluidic systems review:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10451731/
- Lactate/ammonia growth inhibition:
  https://pubmed.ncbi.nlm.nih.gov/1952924/
- Zwitterionic antifouling membrane review:
  https://pubmed.ncbi.nlm.nih.gov/27025359/

