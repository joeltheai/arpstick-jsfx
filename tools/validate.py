#!/usr/bin/env python3
"""Compile-check and functionally test ArpStick.jsfx with Cockos' EEL2 engine.

Emulates REAPER's JSFX compilation:
  - strips the desc:/slider header
  - @init code is compiled inline (top level), first
  - the other sections are wrapped as functions, compiled after @init
    (REAPER compiles sections before "main" code, which is why all plugin
    helper functions must live inside @init)

Usage:
  python3 tools/validate.py [path/to/loose_eel] [--driver tools/regression.eel]

Without a binary the preprocessed source is printed to stdout.
Requires a loose_eel binary built from Cockos WDL with tools/loose_eel.patch
applied (see tools/README.md).
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "ArpStick.jsfx"


def preprocess(src: str) -> str:
    out = []
    current = None
    for ln in src.split("\n"):
        s = ln.strip()
        if s.startswith("desc:") or s.startswith("slider"):
            continue
        if s in ("@slider", "@block", "@sample", "@serialize", "@gfx"):
            if current is not None:
                out.append(");")
            out.append("function __%s() (" % s[1:])
            current = s[1:]
            continue
        if s == "@init":
            continue
        out.append(ln)
    if current is not None:
        out.append(");")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "loose_eel", nargs="?", default=None,
        help="path to the patched loose_eel binary",
    )
    ap.add_argument(
        "--driver", default=None,
        help="EEL driver to append and execute (regression tests)",
    )
    args = ap.parse_args()

    code = preprocess(PLUGIN.read_text())
    if args.driver:
        code += "\n" + Path(args.driver).read_text()

    if not args.loose_eel:
        print(code)
        return 0

    with tempfile.NamedTemporaryFile("w", suffix=".eel", delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        return subprocess.run([args.loose_eel, tmp]).returncode
    finally:
        Path(tmp).unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
