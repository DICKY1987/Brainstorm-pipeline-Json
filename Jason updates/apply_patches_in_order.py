#!/usr/bin/env python3
"""
Apply repository patch files in the required order to produce a final plan.

Order:
  1) patch_expand_to_263_layers.json
  2) patch_map_inception_bullets_to_layers.json
  3) patch_add_activity_object_to_layer_T001.json
  4) patch_file.json

Usage:
  python "Jason updates/apply_patches_in_order.py" \
    --base "Jason updates/expanded_12_layer_plan.json" \
    --out  "Jason updates/final_263_layers_plan.json"

Notes:
  - Writes atomically and creates .bak with timestamp/hash via json_plan_tool.
  - Supports --dry-run to preview without writing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List

# Local import of helpers from the repo tool
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from json_plan_tool import read_json, write_atomic, apply_patch, unified_diff  # type: ignore


def main() -> int:
    p = argparse.ArgumentParser(description="Apply patches in canonical order to produce final JSON")
    p.add_argument("--base", required=True, help="Path to base JSON (expanded_12_layer_plan.json)")
    p.add_argument("--out", required=True, help="Destination path for the final JSON")
    p.add_argument("--dry-run", action="store_true", help="Show unified diff only; do not write")
    args = p.parse_args()

    base_doc, before_bytes = read_json(args.base)

    # Patch list in canonical order
    here = os.path.dirname(os.path.abspath(__file__))
    patch_files: List[str] = [
        os.path.join(here, "patch_expand_to_263_layers.json"),
        os.path.join(here, "patch_map_inception_bullets_to_layers.json"),
        os.path.join(here, "patch_add_activity_object_to_layer_T001.json"),
        os.path.join(here, "patch_file.json"),
    ]

    doc = base_doc
    for pf in patch_files:
        with open(pf, "rb") as f:
            patch = json.loads(f.read().decode("utf-8"))
        doc = apply_patch(doc, patch)

    after_bytes = json.dumps(doc, indent=2, ensure_ascii=False).encode("utf-8")

    if args.dry_run:
        diff = unified_diff(before_bytes, after_bytes, fromfile=args.base, tofile=args.out)
        sys.stdout.write(diff)
        return 0

    write_atomic(args.out, doc, make_backup=True)
    print(f"Wrote {args.out}")
    # Simple confirmation
    try:
        layers = doc.get("layers", [])
        print(f"layers: {len(layers)}; first_id: {layers[0].get('id') if layers else 'n/a'}")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

