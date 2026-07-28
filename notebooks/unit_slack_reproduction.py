import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import math
    import random
    from fractions import Fraction

    import marimo as mo

    return Fraction, math, mo


@app.cell
def _(mo):
    mo.md(r"""
    # Feige's unit-slack bound: an executable reproduction

    **Verdict: reproduced.** On Kubernetes with NVIDIA RTX PRO 6000
    Blackwell GPUs, the pinned Lean project built its three proof blocks
    separately and together. All 11 published kernel audits used only
    `propext`, `Classical.choice`, and `Quot.sound`; a 98-file scan found
    no proof holes or project-defined axioms.

    The paper proves that independent nonnegative variables with means at
    most one obey
    \[
    \Pr[S < \mathbb E S + 1] \geq (n/(n+1))^n,
    \]
    and that this number is best possible at every fixed positive
    dimension. This notebook embeds the completed evidence, so opening it
    does not rerun the Lean build.
    """)
    return


@app.cell
def _(mo):
    evidence = [
        {"component": "Pinned public source", "observed": "commit and tree match", "status": "PASS"},
        {"component": "Vlassis–Thomas", "observed": "build + exactCalibration audit", "status": "PASS"},
        {"component": "Grünbaum", "observed": "build + 9 declaration audits", "status": "PASS"},
        {"component": "Feige assembly", "observed": "bound + optimality audit", "status": "PASS"},
        {"component": "Source integrity", "observed": "98 files; 0 forbidden tokens", "status": "PASS"},
        {"component": "Sharpness", "observed": "exact n=1…512; 2.4M trials", "status": "PASS"},
    ]
    mo.ui.table(evidence, selection=None)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Why the Bernoulli construction is sharp

    Set each coordinate to \(n+1\) with probability \(1/(n+1)\), and to
    zero otherwise. Each coordinate has mean one, so the threshold is
    \(\mathbb E S+1=n+1\). Because the inequality is strict, the event
    \(S<n+1\) occurs exactly when all \(n\) coordinates are zero:

    \[
    \Pr(S<n+1)=\left(1-\frac1{n+1}\right)^n
    =\left(\frac n{n+1}\right)^n.
    \]
    """)
    return


@app.cell
def _(mo):
    dimension = mo.ui.slider(1, 200, value=10, step=1, label="dimension n")
    dimension
    return (dimension,)


@app.cell
def _(Fraction, dimension, math, mo):
    n = dimension.value
    exact = Fraction(n, n + 1) ** n
    mo.callout(
        mo.md(
            fr"""
            At **n = {n}**, the exact sharp constant is
            `{exact.numerator}/{exact.denominator}` = **{float(exact):.9f}**.
            Its distance from \(e^{{-1}}\) is
            **{float(exact) - math.exp(-1):.9f}**.
            """
        ),
        kind="info",
    )
    return


@app.cell
def _(mo):
    pooled = [
        (1, 0.500000000, 0.501766667),
        (2, 0.444444444, 0.443941667),
        (3, 0.421875000, 0.422166667),
        (5, 0.401877572, 0.403091667),
        (8, 0.389744343, 0.389183333),
        (13, 0.381591873, 0.383133333),
        (21, 0.376468715, 0.376758333),
        (34, 0.373224093, 0.373141667),
        (55, 0.371198692, 0.370920833),
        (89, 0.369936558, 0.370654167),
    ]
    rows = [
        {"n": n, "exact": exact, "pooled simulation": observed, "difference": observed - exact}
        for n, exact, observed in pooled
    ]
    mo.md("## Embedded observed evidence")
    mo.ui.table(rows, selection=None)
    return (pooled,)


@app.cell
def _(mo, pooled):
    left, top, width, height = 70, 30, 650, 260
    ymin, ymax = 0.36, 0.51

    def xmap(index):
        return left + index / (len(pooled) - 1) * width

    def ymap(value):
        return top + (ymax - value) / (ymax - ymin) * height

    exact_points = " ".join(
        f"{xmap(i):.1f},{ymap(row[1]):.1f}" for i, row in enumerate(pooled)
    )
    observed_points = " ".join(
        f"{xmap(i):.1f},{ymap(row[2]):.1f}" for i, row in enumerate(pooled)
    )
    dots = "".join(
        f'<circle cx="{xmap(i):.1f}" cy="{ymap(row[2]):.1f}" r="4" fill="#e06c47"/>'
        for i, row in enumerate(pooled)
    )
    labels = "".join(
        f'<text x="{xmap(i):.1f}" y="315" text-anchor="middle" font-size="11">{row[0]}</text>'
        for i, row in enumerate(pooled)
    )
    chart = f"""
    <svg viewBox="0 0 760 340" style="width:100%;max-width:760px;background:#fbfcfe">
      <line x1="{left}" y1="{top+height}" x2="{left+width}" y2="{top+height}" stroke="#667085"/>
      <polyline points="{exact_points}" fill="none" stroke="#2057a6" stroke-width="3"/>
      <polyline points="{observed_points}" fill="none" stroke="#e06c47" stroke-width="1.5"/>
      {dots}{labels}
      <text x="395" y="335" text-anchor="middle" font-size="13">dimension n</text>
      <text x="500" y="22" font-size="12" fill="#2057a6">exact</text>
      <text x="565" y="22" font-size="12" fill="#e06c47">pooled simulation</text>
    </svg>
    """
    mo.Html(chart)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Reproduction record

    - Public source: `pengzhang91/Feige` at
      `98ab466e74280ae9d40622c19dc7f24f01b60864`.
    - Formal target: `Feige.sharp_unit_slack_feige_complete`.
    - Exact arithmetic: every `n` from 1 through 512.
    - Simulation: 8 seeds × 10 dimensions × 30,000 trials = 2.4 million.
    - Compute: Kubernetes, NVIDIA RTX PRO 6000 Blackwell, peak 14
      concurrently allocated GPUs, 994 seconds (0.276 hours) wall time.

    Scope is limited to the unit-slack theorem (\(\delta=1\)); the paper's
    full positive-\(\delta\) inequality was not reproduced here.
    """)
    return


if __name__ == "__main__":
    app.run()
