# Reproduction: sharp unit-slack small-deviation bound

**Assessment: reproduced.** We tested the central fixed-dimensional claim from
[*Sharp Small-Deviation Inequalities for Sums of Independent Nonnegative Random
Variables* (arXiv:2607.23980)](https://arxiv.org/abs/2607.23980): for every
positive finite \(n\), the lower bound is \((n/(n+1))^n\), and this constant is
optimal. The pinned public Lean source built all three proof blocks separately
and together; all 11 kernel audits used only Lean’s standard foundations; exact
arithmetic matched the paper for every \(n=1,\ldots,512\). Eight seeded
simulations (2.4 million trials) had mean absolute error 0.00237 from the exact
probabilities.

This is the full formal unit-slack claim, not a downscaled theorem. The only
scope substitution is that the paper’s general positive-\(\delta\) result was
not tested; Monte Carlo is secondary to the exact and kernel-checked evidence.
All runs used Kubernetes on NVIDIA RTX PRO 6000 Blackwell GPUs, with a measured
peak of 14 concurrent GPUs and 994 seconds (0.276 hours) actual wall time.

- [Detailed illustrated report](reports/unit-slack/report.md)
- [Self-contained marimo notebook](notebooks/unit_slack_reproduction.py)
- [Static evidence data](reports/unit-slack/data/summary.json)

[![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/alphaXiv/feige-231f2e0b/blob/main/notebooks/unit_slack_reproduction.py)

Exact Molab URL:
https://molab.marimo.io/github/alphaXiv/feige-231f2e0b/blob/main/notebooks/unit_slack_reproduction.py

## Experiment log

`main` is presentation-only: **Not run as an experiment (publication surface)**.
The formal runs all used the exact command shown below, inherited unchanged
through the experiment tree.

| Branch / experiment | Purpose | Exact run command | Assessment / outcome | Compute |
|---|---|---|---|---|
| [`orx/lean-source-hole-scan`](https://github.com/alphaXiv/feige-231f2e0b/tree/orx/lean-source-hole-scan) | Pin commit/tree; scan 98 Lean files | `bash reproduction/run.sh` | Passed; 0 forbidden tokens | Kubernetes, RTX PRO 6000 Blackwell, 1 GPU |
| [`orx/vlassis-thomas-isolated-build`](https://github.com/alphaXiv/feige-231f2e0b/tree/orx/vlassis-thomas-isolated-build) | Build and audit exact calibration | `bash reproduction/run.sh` | Passed; standard foundations only | Kubernetes, RTX PRO 6000 Blackwell, 1 GPU |
| [`orx/grunbaum-isolated-build`](https://github.com/alphaXiv/feige-231f2e0b/tree/orx/grunbaum-isolated-build) | Build and audit geometry | `bash reproduction/run.sh` | Passed; 9 declarations audited | Kubernetes, RTX PRO 6000 Blackwell, 1 GPU |
| [`orx/feige-isolated-build`](https://github.com/alphaXiv/feige-231f2e0b/tree/orx/feige-isolated-build) | Build final theorem and sharpness | `bash reproduction/run.sh` | Passed; final theorem audit clean | Kubernetes, RTX PRO 6000 Blackwell, 1 GPU |
| [`orx/combined-default-build`](https://github.com/alphaXiv/feige-231f2e0b/tree/orx/combined-default-build) | Build all default targets together | `bash reproduction/run.sh` | Passed in 147 harness seconds | Kubernetes, RTX PRO 6000 Blackwell, 1 GPU |
| [`orx/full-proof-chain-replication-b`](https://github.com/alphaXiv/feige-231f2e0b/tree/orx/full-proof-chain-replication-b) | Complete clean-clone protocol | `bash reproduction/run.sh` | Reproduced in 184 harness seconds | Kubernetes, RTX PRO 6000 Blackwell, 1 GPU |
| [`orx/full-proof-chain-replication-a`](https://github.com/alphaXiv/feige-231f2e0b/tree/orx/full-proof-chain-replication-a) | Saturated-concurrency repeat | `bash reproduction/run.sh` | Reproduced in 717 harness seconds | Kubernetes, RTX PRO 6000 Blackwell, 1 GPU |
| [`orx/sharpness-seed-11`](https://github.com/alphaXiv/feige-231f2e0b/tree/orx/sharpness-seed-11) and [five seed siblings](https://github.com/alphaXiv/feige-231f2e0b/branches) | Independent sharpness simulations | `bash reproduction/run.sh` | Passed; pooled with two full-run seeds | Kubernetes, RTX PRO 6000 Blackwell, 1 GPU each |

---

# Feige's unit-slack conjecture in Lean

This repository gives a machine-checked Lean formalization of a proof of
Feige's unit-slack conjecture in every fixed positive dimension `n`.  

The proof is presented in *Sharp Small-Deviation Inequalities for Sums of Independent Nonnegative Random Variables* by Weibo Fu, Yanjun Han, Guanyang Wang, Jun Yan, Peng Zhang, and Zhengqing Zhou. 
ArXiv: https://arxiv.org/abs/2607.23980.

Specifically, it proves

$$
  \Pr \left[\sum_{i=1}^n X_i
    < \mathbb{E} \left(\sum_{i=1}^n X_i\right)+1\right]
  \ge \left(\frac{n}{n+1}\right)^n
$$

for any independent, nonnegative, integrable random variables satisfying
`E[Xᵢ] ≤ 1`. The constant is optimal for that fixed `n`.

The machine-checked entry point, defined in
[`Feige/MainTheorem.lean`](Feige/MainTheorem.lean), is:

```lean
theorem Feige.sharp_unit_slack_feige_complete
    {n : ℕ} (hn : 0 < n) :
    Feige.IsOptimalFixedDimensionalFeigeBound n
      (Feige.sharpConstant n)
```

## Proof architecture

The proof of the Feige conjecture depends on two substantive
mathematical results:

1. the [Vlassis--Thomas exact Dirichlet calibration
   theorem](https://arxiv.org/abs/2607.08415) for independent nonnegative
   random variables; and
2. Grünbaum's centroid halfspace theorem, including the sharp simplex case.

This repository independently formalizes both results.  Each has its own
public interface, build target, and kernel-axiom audit.  A third block connects
them through the normalized-exponential/simplex identification and assembles
the Feige theorem.

### Three independently buildable blocks

| Block | Public entry point | Build command |
|---|---|---|
| Vlassis--Thomas exact calibration | `VlassisThomas.exactCalibration` | `lake build VlassisThomas` |
| Grünbaum centroid halfspace theorem | `Grunbaum.lean` | `lake build Grunbaum` |
| Feige deduction and final assembly | `Feige.sharp_unit_slack_feige_complete` | `lake build Feige` |

The Vlassis--Thomas block reconstructs the main theorem of
Nikos Vlassis and Philip S. Thomas,
[*An Exact Distribution-Free Test for Means of Nonnegative Random Variables*](https://arxiv.org/abs/2607.08415).
It contains the two-point reduction, calibrated chains, exponential transfer,
local insertion, boundary approximation, measurable two-point mixing, and the
reduction to arbitrary independent nonnegative marginals.

The Grünbaum block proves the centroid halfspace inequality and its sharp
simplex model.  The Feige block uses only the public exact-calibration theorem,
the normalized-exponential/simplex identification, and the specialized
Grünbaum interface.  The intermediate theorem in
[`Feige/ConditionalMainTheorem.lean`](Feige/ConditionalMainTheorem.lean)
exposes those three structural inputs explicitly; `Feige/MainTheorem.lean`
discharges all three.

Here, “independently buildable” refers to theorem and build-target boundaries;
the targets share internal utility modules.  A theorem-by-theorem account,
including the precise scope of the Vlassis--Thomas reconstruction, is in
[`FORMALIZATION.md`](FORMALIZATION.md).

## Reproducible build

The repository pins Lean and Mathlib:

- Lean `v4.31.0`
- Mathlib tag `v4.31.0`
- Mathlib commit `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`

From a fresh clone:

```bash
lake exe cache get
lake build VlassisThomas
lake build Grunbaum
lake build Feige
```

Running `lake build` builds all three default targets.

## Proof audit

The three public results have dedicated kernel-axiom audits:

```bash
lake env lean VlassisThomas/Audit.lean
lake env lean Grunbaum/Audit.lean
lake env lean Feige/FinalAudit.lean
```

The final theorem uses only Lean's standard logical foundations:
`propext`, `Classical.choice`, and `Quot.sound`.  The project contains no
`sorry`, `admit`, `sorryAx`, or project-defined axiom.

## Scope

The final theorem is stated for positive finite dimensions and
small-universe probability spaces (`Ω : Type`).  It uses pointwise
nonnegativity and measurable representatives of the random variables.

## Attribution

- The exact calibration theorem and its proof strategy are due to Nikos
  Vlassis and Philip S. Thomas (arXiv:2607.08415).
- The centroid halfspace theorem is due to Branko Grünbaum,
  *Pacific Journal of Mathematics* 10 (1960), 1257--1261.
- The Brunn--Minkowski support files under `LeanPool/Isoperimetric/` are from
  `Vilin97/lean-pool`; see [`NOTICE.md`](NOTICE.md).

## License

Apache License 2.0.  See [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md).
