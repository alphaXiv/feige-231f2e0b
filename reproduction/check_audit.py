#!/usr/bin/env python3
"""Reject any kernel dependency outside Lean's standard logical foundations."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED = {"propext", "Classical.choice", "Quot.sound"}


def main() -> None:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    if "error:" in text.lower() or "sorryAx" in text:
        raise SystemExit("Lean audit output contains an error or sorryAx")
    blocks = re.findall(r"depends on axioms:\s*\[(.*?)\]", text, flags=re.DOTALL)
    if not blocks and "does not depend on any axioms" not in text:
        raise SystemExit("Could not parse any '#print axioms' result")
    observed: set[str] = set()
    for block in blocks:
        observed.update(re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", block))
    unexpected = observed - ALLOWED
    if unexpected:
        raise SystemExit(f"Unexpected axiom dependencies: {sorted(unexpected)}")
    print("AUDIT_AXIOMS allowed=" + ",".join(sorted(observed)))


if __name__ == "__main__":
    main()
