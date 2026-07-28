#!/usr/bin/env python3
"""Generate the public evidence tables and SVG figures from `orx logs`."""

from __future__ import annotations

import csv
import datetime as dt
import html
import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGES = HERE / "images"
DATA = HERE / "data"

SIM_RUNS = {
    11: "600d7d0c-c4b9-46a6-8081-6e6e17be3172",
    29: "11e2a384-4f35-4bef-8568-94e3444d0e20",
    101: "98a014ea-19e2-4bdb-86c2-02750bcf0373",
    1009: "546a46d4-8ae7-418c-af20-70f947a7e912",
    2026: "4940390c-e630-4047-a759-ea29c6829e0e",
    8675309: "4ee2d5b0-b869-429c-a5e6-a1201f0b6b08",
    271828: "df8dae65-3fdb-407b-9d0f-8266b0e80528",
    314159: "7cbd8bf8-e96a-4c23-ad77-114358880982",
}

METRIC_RUNS = {
    "Vlassis–Thomas isolated": "22199362-315e-41d8-b787-441a2e569fc7",
    "Grünbaum isolated": "f58414eb-bc21-48ea-847a-b69f009b0b35",
    "Feige isolated": "1750f02d-3c74-4cbb-98f6-26041788b90a",
    "Combined clean build": "fb5ea88f-48ec-438e-bc32-4731aa9abef3",
    "Full replication, fast": "df8dae65-3fdb-407b-9d0f-8266b0e80528",
    "Full replication, saturated": "7cbd8bf8-e96a-4c23-ad77-114358880982",
}

BATCH_PODS = [
    ("Vlassis build", "19:32:39", "19:35:10", "pass"),
    ("Grünbaum build", "19:32:40", "19:34:28", "pass"),
    ("Feige build", "19:32:42", "19:35:17", "pass"),
    ("Combined build", "19:32:44", "19:35:23", "pass"),
    ("Audit-only VT", "19:32:46", "19:34:08", "diagnostic"),
    ("Audit-only Grünbaum", "19:32:48", "19:34:08", "diagnostic"),
    ("Audit-only Feige", "19:32:49", "19:34:12", "diagnostic"),
    ("Provenance", "19:32:51", "19:33:04", "pass"),
    ("Seed 11", "19:32:52", "19:33:07", "pass"),
    ("Seed 29", "19:32:54", "19:33:09", "pass"),
    ("Seed 101", "19:32:56", "19:33:11", "pass"),
    ("Seed 1009", "19:32:58", "19:33:13", "pass"),
    ("Seed 2026", "19:33:00", "19:33:15", "pass"),
    ("Seed 8675309", "19:33:01", "19:33:16", "pass"),
    ("Full replication A", "19:33:06", "19:45:15", "pass"),
    ("Full replication B", "19:33:09", "19:36:26", "pass"),
]


def log(run_id: str) -> str:
    return subprocess.check_output(
        ["orx", "logs", run_id, "--bytes", "200000"], text=True
    )


def metric_map(text: str) -> dict[str, float | str]:
    result: dict[str, float | str] = {}
    for key, value in re.findall(r"^ORX_METRIC ([^=]+)=(.+)$", text, re.MULTILINE):
        try:
            result[key] = float(value)
        except ValueError:
            result[key] = value.strip('"')
    return result


def summary(text: str) -> dict:
    line = next(
        line for line in text.splitlines() if line.startswith("SHARPNESS_SUMMARY ")
    )
    return json.loads(line.split(" ", 1)[1])


def svg_start(title: str, subtitle: str = "", width: int = 960, height: int = 540) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Inter,ui-sans-serif,system-ui,sans-serif}.title{font-size:28px;font-weight:700;fill:#172033}.sub{font-size:14px;fill:#5b6475}.label{font-size:14px;fill:#253047}.small{font-size:12px;fill:#667085}.value{font-size:18px;font-weight:700;fill:#172033}</style>",
        f'<rect width="{width}" height="{height}" fill="#fbfcfe"/>',
        f'<text x="50" y="48" class="title">{html.escape(title)}</text>',
        f'<text x="50" y="73" class="sub">{html.escape(subtitle)}</text>',
    ]


def write_svg(name: str, parts: list[str]) -> None:
    parts.append("</svg>")
    (IMAGES / name).write_text("\n".join(parts) + "\n", encoding="utf-8")


def proof_matrix(total_trials: int) -> None:
    cards = [
        ("Pinned source", "PASS", "commit + tree verified"),
        ("Vlassis–Thomas", "PASS", "build + kernel audit"),
        ("Grünbaum", "PASS", "build + 9 audits"),
        ("Feige theorem", "PASS", "bound + sharpness"),
        ("Source integrity", "PASS", "98 files, 0 holes"),
        ("Bernoulli check", "PASS", f"n=1…512; {total_trials/1e6:.1f}M trials"),
    ]
    p = svg_start(
        "Central reproduction result",
        "Every primary component passed in clean Kubernetes jobs at the pinned public commit.",
    )
    for i, (label, status, detail) in enumerate(cards):
        col, row = i % 3, i // 3
        x, y = 50 + col * 300, 115 + row * 170
        p += [
            f'<rect x="{x}" y="{y}" width="270" height="135" rx="14" fill="#ffffff" stroke="#d8e0ec"/>',
            f'<circle cx="{x+32}" cy="{y+34}" r="13" fill="#15966a"/>',
            f'<path d="M{x+25} {y+34} l5 5 l10 -11" fill="none" stroke="white" stroke-width="3"/>',
            f'<text x="{x+55}" y="{y+40}" class="value">{status}</text>',
            f'<text x="{x+22}" y="{y+78}" class="label">{html.escape(label)}</text>',
            f'<text x="{x+22}" y="{y+105}" class="small">{html.escape(detail)}</text>',
        ]
    p.append('<text x="50" y="490" class="sub">Verdict: reproduced for the paper’s fixed-dimensional unit-slack theorem; the general δ-dependent theorem was out of scope.</text>')
    write_svg("primary_result.svg", p)


def sharpness_figure(rows: list[dict]) -> None:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["n"]].append(row)
    ns = sorted(grouped)
    xmin, xmax, ymin, ymax = 1, max(ns), 0.35, 0.52
    left, top, pw, ph = 90, 105, 800, 345

    def xmap(n: int) -> float:
        return left + (math.log(n) - math.log(xmin)) / (math.log(xmax) - math.log(xmin)) * pw

    def ymap(v: float) -> float:
        return top + (ymax - v) / (ymax - ymin) * ph

    p = svg_start(
        "Sharp Bernoulli construction",
        "Dots pool eight independent seeds (240,000 trials per n); the line is the exact value (n/(n+1))ⁿ.",
    )
    for tick in [0.36, 0.40, 0.44, 0.48, 0.52]:
        y = ymap(tick)
        p += [
            f'<line x1="{left}" y1="{y}" x2="{left+pw}" y2="{y}" stroke="#e5e9f0"/>',
            f'<text x="{left-12}" y="{y+4}" text-anchor="end" class="small">{tick:.2f}</text>',
        ]
    for n in ns:
        x = xmap(n)
        p.append(f'<text x="{x}" y="{top+ph+28}" text-anchor="middle" class="small">{n}</text>')
    exact_pts, obs_pts = [], []
    for n in ns:
        values = grouped[n]
        exact = values[0]["exact_probability"]
        pooled = sum(v["successes"] for v in values) / sum(v["trials"] for v in values)
        total = sum(v["trials"] for v in values)
        se = math.sqrt(pooled * (1 - pooled) / total)
        x, y, y1, y2 = xmap(n), ymap(pooled), ymap(pooled - 1.96 * se), ymap(pooled + 1.96 * se)
        exact_pts.append(f"{x:.1f},{ymap(exact):.1f}")
        obs_pts.append(f"{x:.1f},{y:.1f}")
        p += [
            f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="#e06c47" stroke-width="2"/>',
            f'<circle cx="{x}" cy="{y}" r="4.5" fill="#e06c47"/>',
        ]
    p += [
        f'<polyline points="{" ".join(exact_pts)}" fill="none" stroke="#2057a6" stroke-width="3"/>',
        f'<polyline points="{" ".join(obs_pts)}" fill="none" stroke="#e06c47" stroke-width="1.5" opacity=".65"/>',
        f'<line x1="{left}" y1="{top+ph}" x2="{left+pw}" y2="{top+ph}" stroke="#687386"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ph}" stroke="#687386"/>',
        '<text x="490" y="505" text-anchor="middle" class="label">dimension n (log scale)</text>',
        '<text x="23" y="280" transform="rotate(-90 23 280)" text-anchor="middle" class="label">event probability</text>',
        '<line x1="630" y1="92" x2="665" y2="92" stroke="#2057a6" stroke-width="3"/><text x="672" y="97" class="small">exact</text>',
        '<circle cx="750" cy="92" r="4.5" fill="#e06c47"/><text x="760" y="97" class="small">pooled simulation ±95%</text>',
    ]
    write_svg("sharpness_curve.svg", p)


def audit_figure() -> None:
    blocks = [("Vlassis–Thomas", 1), ("Grünbaum", 9), ("Feige final theorem", 1)]
    p = svg_start(
        "Kernel-axiom audit",
        "All 11 audited declarations depended only on Lean’s three standard logical foundations.",
    )
    for i, (label, count) in enumerate(blocks):
        y = 140 + i * 105
        width = count * 62
        p += [
            f'<text x="50" y="{y+25}" class="label">{html.escape(label)}</text>',
            f'<rect x="240" y="{y}" width="{width}" height="38" rx="8" fill="#2a9d78"/>',
            f'<text x="{250+width}" y="{y+26}" class="value">{count}</text>',
            f'<text x="240" y="{y+62}" class="small">propext · Classical.choice · Quot.sound</text>',
        ]
    p += [
        '<rect x="50" y="450" width="860" height="50" rx="10" fill="#eef8f4"/>',
        '<text x="70" y="481" class="value">0</text>',
        '<text x="100" y="480" class="label">sorry / admit / sorryAx / project-defined axiom declarations</text>',
    ]
    write_svg("axiom_audit.svg", p)


def runtime_figure(metrics: dict[str, dict[str, float | str]]) -> None:
    labels = ["Vlassis", "Grünbaum", "Feige", "Combined"]
    fast = metrics["Full replication, fast"]
    saturated = metrics["Full replication, saturated"]
    fast_v = [fast["build_vlassis_seconds"], fast["build_grunbaum_seconds"], fast["build_feige_seconds"], fast["build_all_seconds"]]
    sat_v = [saturated["build_vlassis_seconds"], saturated["build_grunbaum_seconds"], saturated["build_feige_seconds"], saturated["build_all_seconds"]]
    p = svg_start(
        "Build-time robustness",
        "Identical code and command, measured once as the cluster drained and once under the 16-job submission wave.",
    )
    left, base, scale = 110, 450, 1.2
    for tick in [0, 50, 100, 150, 200, 250]:
        y = base - tick * scale
        p += [
            f'<line x1="{left}" y1="{y}" x2="900" y2="{y}" stroke="#e5e9f0"/>',
            f'<text x="{left-12}" y="{y+4}" text-anchor="end" class="small">{tick}</text>',
        ]
    for i, label in enumerate(labels):
        x = 170 + i * 180
        for offset, value, color in [(-28, fast_v[i], "#2057a6"), (22, sat_v[i], "#e06c47")]:
            height = float(value) * scale
            p += [
                f'<rect x="{x+offset}" y="{base-height}" width="42" height="{height}" rx="5" fill="{color}"/>',
                f'<text x="{x+offset+21}" y="{base-height-8}" text-anchor="middle" class="small">{int(value)}s</text>',
            ]
        p.append(f'<text x="{x+18}" y="{base+30}" text-anchor="middle" class="small">{label}</text>')
    p += [
        '<rect x="615" y="85" width="14" height="14" fill="#2057a6"/><text x="637" y="97" class="small">fast repeat</text>',
        '<rect x="745" y="85" width="14" height="14" fill="#e06c47"/><text x="767" y="97" class="small">saturated repeat</text>',
        '<text x="25" y="280" transform="rotate(-90 25 280)" text-anchor="middle" class="label">seconds</text>',
    ]
    write_svg("runtime_robustness.svg", p)


def concurrency_figure() -> None:
    origin = dt.datetime.fromisoformat("2026-07-28T19:32:39+00:00")

    def seconds(hms: str) -> float:
        stamp = dt.datetime.fromisoformat(f"2026-07-28T{hms}+00:00")
        return (stamp - origin).total_seconds()

    p = svg_start(
        "Kubernetes execution timeline",
        "Sixteen one-GPU jobs were submitted; measured peak overlap was 14 allocated RTX PRO 6000 Blackwell GPUs.",
        height=650,
    )
    left, top, width, row_h = 190, 105, 700, 29
    xmax = max(seconds(end) for _, _, end, _ in BATCH_PODS)
    for tick in [0, 150, 300, 450, 600, 750]:
        x = left + tick / xmax * width
        p += [
            f'<line x1="{x}" y1="{top-10}" x2="{x}" y2="{top+row_h*len(BATCH_PODS)}" stroke="#e5e9f0"/>',
            f'<text x="{x}" y="{top+row_h*len(BATCH_PODS)+25}" text-anchor="middle" class="small">{tick}s</text>',
        ]
    for i, (label, start, end, outcome) in enumerate(BATCH_PODS):
        y = top + i * row_h
        x1 = left + seconds(start) / xmax * width
        x2 = left + seconds(end) / xmax * width
        color = "#2a9d78" if outcome == "pass" else "#d39a2c"
        p += [
            f'<text x="{left-10}" y="{y+16}" text-anchor="end" class="small">{html.escape(label)}</text>',
            f'<rect x="{x1}" y="{y+4}" width="{max(3, x2-x1)}" height="17" rx="4" fill="{color}"/>',
        ]
    p += [
        '<rect x="620" y="82" width="12" height="12" fill="#2a9d78"/><text x="639" y="93" class="small">passed</text>',
        '<rect x="710" y="82" width="12" height="12" fill="#d39a2c"/><text x="729" y="93" class="small">diagnostic prerequisite</text>',
        '<text x="540" y="630" text-anchor="middle" class="label">seconds since first batch pod started</text>',
    ]
    write_svg("kubernetes_timeline.svg", p)


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    sim_rows = []
    summaries = {}
    for seed, run_id in SIM_RUNS.items():
        parsed = summary(log(run_id))
        summaries[seed] = parsed
        sim_rows.extend(parsed["rows"])

    with (DATA / "simulation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sim_rows[0]))
        writer.writeheader()
        writer.writerows(sim_rows)

    metrics = {name: metric_map(log(run_id)) for name, run_id in METRIC_RUNS.items()}
    with (DATA / "runtimes.csv").open("w", newline="", encoding="utf-8") as handle:
        keys = [
            "name", "cache_get_seconds", "build_vlassis_seconds", "build_grunbaum_seconds",
            "build_feige_seconds", "build_all_seconds", "total_seconds",
        ]
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for name, values in metrics.items():
            writer.writerow({"name": name, **{key: values.get(key, "") for key in keys[1:]}})

    aggregate = {
        "verdict": "reproduced",
        "paper_id": "2607.23980",
        "pinned_commit": "98ab466e74280ae9d40622c19dc7f24f01b60864",
        "pinned_tree": "4406b0e9177f06cf24be645e8c54637137f0ab3e",
        "lean_files": 98,
        "forbidden_tokens": 0,
        "audited_declarations": 11,
        "simulation_seeds": sorted(SIM_RUNS),
        "simulation_points": len(sim_rows),
        "simulation_trials": sum(row["trials"] for row in sim_rows),
        "inside_wilson95": sum(row["exact_in_wilson95"] for row in sim_rows),
        "mean_absolute_error": sum(
            abs(row["observed_probability"] - row["exact_probability"]) for row in sim_rows
        ) / len(sim_rows),
        "max_absolute_z": max(abs(row["z_score"]) for row in sim_rows),
        "exact_grid": [1, 512],
        "exact_grid_sha256": next(iter(summaries.values()))["exact_grid_sha256"],
        "compute": {
            "backend": "kubernetes",
            "gpu_model": "NVIDIA RTX PRO 6000 Blackwell",
            "peak_concurrent_gpu_count": 14,
            "first_job_created": "2026-07-28T19:28:43Z",
            "last_job_completed": "2026-07-28T19:45:17Z",
            "wall_seconds": 994,
            "wall_hours": 994 / 3600,
        },
    }
    (DATA / "summary.json").write_text(
        json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    proof_matrix(aggregate["simulation_trials"])
    sharpness_figure(sim_rows)
    audit_figure()
    runtime_figure(metrics)
    concurrency_figure()


if __name__ == "__main__":
    main()
