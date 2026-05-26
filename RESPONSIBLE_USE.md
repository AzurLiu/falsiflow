# Responsible Use

Falsiflow helps make high-risk technical claims harder to advance without
evidence. It does not create experimental facts. It audits the project config,
evidence rows, source-file provenance, derived metrics, bundle manifests, and
acceptance rules supplied by the user.

## What Falsiflow Can Say

Falsiflow can report that a configured claim is ready under the evidence gates
you defined. It can also show why a claim is blocked, which files support the
claim, and whether a portable evidence bundle verifies against its manifest.

## What Falsiflow Cannot Say

Falsiflow output is not proof of:

- biological safety
- clinical safety or efficacy
- regulatory compliance
- material biocompatibility
- experimental truth
- commercial readiness
- absence of hidden confounders or measurement error

Use Falsiflow as an audit and handoff layer, not as a substitute for independent
experimental validation, expert review, legal review, clinical review, or
regulatory review.

## User Responsibilities

- Keep raw source files, chain-of-custody records, and metadata accurate.
- Define acceptance rules before interpreting results where possible.
- Preserve failed and blocked evidence instead of deleting inconvenient rows.
- Verify received bundles before relying on them.
- Document assumptions, controls, measurement limits, and known missing data.
- Avoid presenting `claim_ready` as a universal truth outside the configured
  project scope.

## High-Risk Domains

For biomaterials, wetware, neural interfaces, medical devices, cell assays, or
other safety-sensitive work, Falsiflow should only support planning,
traceability, and review. Decisions that affect people, animals, patients,
regulated products, or paid customer claims require independent expert
judgment and appropriate external validation.
