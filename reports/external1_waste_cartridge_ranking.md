# LIMINA Candidate Ranking

| Rank | Priority | Score | Candidate | Main risks |
| ---: | --- | ---: | --- | --- |
| 1 | high | 4.020 | Regenerated-cellulose dialysis exchange module | MWCO may also remove helpful small signaling molecules; diffusion-limited clearance; biofouling over time |
| 2 | watch | 3.620 | Layered neuronal-media waste cartridge | module complexity; sterilization validation; unintended adsorption in ion-exchange zone |
| 3 | watch | 3.510 | Ion-concentration-polarization media regenerator | electrochemical byproducts; pH and conductivity perturbation; device complexity; neural medium validation gap |
| 4 | watch | 3.340 | Zwitterionic antifouling membrane coating | coating adhesion; scale-up chemistry; possible change in membrane permeability |
| 5 | hold | 3.230 | Ammonium-selective ion-exchange hydrogel insert | competes with essential cations; pH/osmolality shift; resin leachables; limited lactate handling |
| 6 | hold | 3.160 | Enzyme-assisted lactate polishing module | reactive byproducts; enzyme instability; oxygen dependence; new toxicity mode |
| 7 | hold | 2.140 | Broad adsorbent carbon/resin bed | nonselective stripping; growth-factor and hormone loss; batch variability; difficult mechanistic control |

## Gate Holds

- **Ammonium-selective ion-exchange hydrogel insert**
  - low_leachables below 3: Leachables in warm neuronal culture medium could invalidate otherwise promising waste removal.

- **Enzyme-assisted lactate polishing module**
  - low_leachables below 3: Leachables in warm neuronal culture medium could invalidate otherwise promising waste removal.
  - culture_stability below 3: The cartridge must remain stable under long-duration 37 C perfusion.

- **Broad adsorbent carbon/resin bed**
  - growth_factor_retention below 3: A waste cartridge must not silently strip critical trophic factors or serum proteins.
  - low_leachables below 3: Leachables in warm neuronal culture medium could invalidate otherwise promising waste removal.
