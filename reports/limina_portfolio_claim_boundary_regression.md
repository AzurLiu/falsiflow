# LIMINA Portfolio Claim-Boundary Regression

This regression proves that the portfolio selector cannot declare material suitability before the final claim audit.

**Status:** `pass`
**Portfolio status:** `claim_audit_required`
**Primary next branch:** `limina_nhi_pedot_laminin_v0_1`

## Assertions

| Assertion | Result | Detail |
| --- | --- | --- |
| `selector_command_succeeded` | `pass` | returncode=0; stderr= |
| `portfolio_does_not_claim_suitable_material_present` | `pass` | portfolio status=claim_audit_required |
| `portfolio_requires_claim_audit` | `pass` | portfolio status=claim_audit_required |
| `zrc_suitable_readiness_still_requires_claim_audit` | `pass` | zrc status=readiness_gates_passed_claim_audit_required |
| `nhi_long_pass_still_requires_claim_audit` | `pass` | nhi status=long_gates_passed_claim_audit_required |

## Boundary

Passing-looking portfolio inputs should only produce a claim-audit-required workflow state. The suitability claim remains gated by `audit_limina_suitability_claim.py`.
