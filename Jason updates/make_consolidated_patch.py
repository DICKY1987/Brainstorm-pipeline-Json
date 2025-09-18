#!/usr/bin/env python3
"""Create a single consolidated JSON Patch by concatenating the repo patches
in the required order so it can be applied to the base plan in one step.

Usage:
  python "Jason updates/make_consolidated_patch.py" \
    --out "Jason updates/patch_all_in_order.json"
"""
from __future__ import annotations
import argparse, json, os, sys

def main() -> int:
    p = argparse.ArgumentParser(description="Make consolidated patch in canonical order")
    p.add_argument("--out", required=True, help="Destination path for consolidated patch JSON")
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    order = [
        os.path.join(here, 'patch_expand_to_263_layers.json'),
        os.path.join(here, 'patch_map_inception_bullets_to_layers.json'),
        os.path.join(here, 'patch_add_activity_object_to_layer_T001.json'),
        os.path.join(here, 'patch_file.json'),
    ]
    ops = []
    for path in order:
        with open(path, 'rb') as f:
            ops.extend(json.loads(f.read().decode('utf-8')))
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(ops, f, indent=2, ensure_ascii=False)
    print(f"Wrote {args.out} with {len(ops)} ops")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

