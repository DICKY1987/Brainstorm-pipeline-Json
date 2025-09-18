#!/usr/bin/env python3
import json, argparse, sys, os, tempfile, hashlib, shutil, difflib, datetime
from typing import Any, Tuple, List

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def read_json(path: str):
    with open(path, "rb") as f:
        data = f.read()
    try:
        return json.loads(data.decode("utf-8")), data
    except Exception as e:
        print(f"ERROR: Failed to parse JSON from {path}: {e}", file=sys.stderr)
        sys.exit(2)

def write_atomic(path: str, obj: Any, make_backup: bool = True):
    """Write JSON atomically: temp file + rename; make .bak with hash in name."""
    data = json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
    new_hash = sha256_bytes(data)
    dirn = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(dirn, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=".jsontmp-", dir=dirn)
    with os.fdopen(tmp_fd, "wb") as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
    if make_backup and os.path.exists(path):
        ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        bak_path = f"{path}.bak.{ts}.{new_hash[:8]}"
        shutil.copy2(path, bak_path)
    os.replace(tmp_path, path)
    return path, new_hash

# --- JSON Pointer helpers (RFC 6901) ---
def _unescape_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")

def _split_pointer(ptr: str) -> List[str]:
    if ptr == "" or ptr == "/":
        return []
    if not ptr.startswith("/"):
        raise ValueError(f"Invalid JSON Pointer (must start with '/'): {ptr}")
    return [_unescape_token(t) for t in ptr.split("/")[1:]]

def pointer_get(doc: Any, pointer: str) -> Any:
    tokens = _split_pointer(pointer)
    cur = doc
    for t in tokens:
        if isinstance(cur, list):
            if t == "-":
                raise KeyError("'-' is not valid for get operations")
            idx = int(t)
            cur = cur[idx]
        else:
            cur = cur[t]
    return cur

def _ensure_parent(doc: Any, tokens: List[str]):
    cur = doc
    for t in tokens[:-1]:
        if isinstance(cur, list):
            idx = int(t)
            cur = cur[idx]
        else:
            cur = cur.setdefault(t, {})
    return cur, tokens[-1] if tokens else ""

def pointer_add(doc: Any, pointer: str, value: Any) -> Any:
    tokens = _split_pointer(pointer)
    if not tokens:
        return value  # replace root
    parent, last = _ensure_parent(doc, tokens)
    if isinstance(parent, list):
        if last == "-":
            parent.append(value)
        else:
            parent.insert(int(last), value)
    else:
        if last in parent:
            raise KeyError(f"Add target exists: {pointer}")
        parent[last] = value
    return doc

def pointer_replace(doc: Any, pointer: str, value: Any) -> Any:
    tokens = _split_pointer(pointer)
    if not tokens:
        return value
    parent, last = _ensure_parent(doc, tokens)
    if isinstance(parent, list):
        parent[int(last)] = value
    else:
        if last not in parent:
            raise KeyError(f"Replace target missing: {pointer}")
        parent[last] = value
    return doc

def pointer_remove(doc: Any, pointer: str) -> Any:
    tokens = _split_pointer(pointer)
    if not tokens:
        raise KeyError("Cannot remove document root")
    parent, last = _ensure_parent(doc, tokens)
    if isinstance(parent, list):
        del parent[int(last)]
    else:
        del parent[last]
    return doc

# --- JSON Patch (RFC 6902) ---
def apply_patch(doc: Any, patch: List[dict]) -> Any:
    # operations: add, remove, replace, move, copy, test
    for i, op in enumerate(patch):
        optype = op.get("op")
        path = op.get("path")
        if optype in ("add", "replace", "test"):
            value = op.get("value")
        if optype in ("move", "copy"):
            from_ptr = op.get("from")
            if not isinstance(from_ptr, str):
                raise ValueError(f"Patch[{i}] missing 'from' for {optype}")
        if not isinstance(path, str):
            raise ValueError(f"Patch[{i}] missing valid 'path'")

        if optype == "add":
            doc = pointer_add(doc, path, value)
        elif optype == "remove":
            doc = pointer_remove(doc, path)
        elif optype == "replace":
            doc = pointer_replace(doc, path, value)
        elif optype == "move":
            val = pointer_get(doc, from_ptr)
            doc = pointer_remove(doc, from_ptr)
            doc = pointer_add(doc, path, val)
        elif optype == "copy":
            val = pointer_get(doc, from_ptr)
            doc = pointer_add(doc, path, json.loads(json.dumps(val)))
        elif optype == "test":
            cur = pointer_get(doc, path)
            if cur != value:
                raise AssertionError(f"Patch[{i}] test failed at {path}: {cur!r} != {value!r}")
        else:
            raise ValueError(f"Unsupported op: {optype}")
    return doc

def unified_diff(a_bytes: bytes, b_bytes: bytes, fromfile: str, tofile: str) -> str:
    a = a_bytes.decode("utf-8").splitlines(keepends=True)
    b = b_bytes.decode("utf-8").splitlines(keepends=True)
    return "".join(difflib.unified_diff(a, b, fromfile=fromfile, tofile=tofile))

# --- Template insertion for SDLC-like 'layer' objects ---
def clone_layer(doc: Any, source_pointer: str, dest_pointer: str, name: str = None) -> Any:
    layer = pointer_get(doc, source_pointer)
    clone = json.loads(json.dumps(layer))
    if name and isinstance(clone, dict):
        clone["name"] = name
    return pointer_add(doc, dest_pointer, clone)

def main():
    p = argparse.ArgumentParser(
        description="Reliable JSON editor (RFC6902 patches, JSON Pointer ops, dry-run diff, atomic writes)."
    )
    p.add_argument("json_file", help="Path to JSON file to modify")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate JSON is parseable; print SHA256")
    v.add_argument("--print-keys", action="store_true", help="Print top-level keys")

    g = sub.add_parser("get", help="Get value at JSON Pointer")
    g.add_argument("--pointer", required=True)

    s = sub.add_parser("set", help="Replace value at JSON Pointer (value is parsed as JSON)")
    s.add_argument("--pointer", required=True)
    s.add_argument("--value", required=True, help='Value in JSON (e.g., "42", "\\"text\\"", "{\\"a\\":1}")')
    s.add_argument("--dry-run", action="store_true")

    r = sub.add_parser("remove", help="Remove value at JSON Pointer")
    r.add_argument("--pointer", required=True)
    r.add_argument("--dry-run", action="store_true")

    a = sub.add_parser("add", help="Add value at JSON Pointer (create or insert)")
    a.add_argument("--pointer", required=True)
    a.add_argument("--value", required=True)
    a.add_argument("--dry-run", action="store_true")

    ap = sub.add_parser("apply-patch", help="Apply a JSON Patch (RFC6902) from a file")
    ap.add_argument("--patch", required=True, help="Path to JSON Patch file (list of ops)")
    ap.add_argument("--dry-run", action="store_true")

    cl = sub.add_parser("clone-layer", help="Clone an existing layer to a new location (optional rename)")
    cl.add_argument("--from-pointer", required=True, help="Pointer to existing layer object")
    cl.add_argument("--to-pointer", required=True, help="Pointer destination (array or new key)")
    cl.add_argument("--name", default=None, help="Optional new 'name' value")
    cl.add_argument("--dry-run", action="store_true")

    args = p.parse_args()

    doc, before_bytes = read_json(args.json_file)

    if args.cmd == "validate":
        print(f"OK: parsed {args.json_file}")
        print(f"SHA256: {sha256_bytes(before_bytes)}")
        if args.print-keys:
            if isinstance(doc, dict):
                print("Top-level keys:", ", ".join(doc.keys()))
            else:
                print("Top-level is not an object")
        return

    if args.cmd == "get":
        val = pointer_get(doc, args.pointer)
        print(json.dumps(val, indent=2, ensure_ascii=False))
        return

    if args.cmd in ("set", "add", "remove", "apply-patch", "clone-layer"):
        new_doc = json.loads(json.dumps(doc))  # deep copy

        if args.cmd == "set":
            value = json.loads(args.value)
            new_doc = pointer_replace(new_doc, args.pointer, value)
        elif args.cmd == "add":
            value = json.loads(args.value)
            new_doc = pointer_add(new_doc, args.pointer, value)
        elif args.cmd == "remove":
            new_doc = pointer_remove(new_doc, args.pointer)
        elif args.cmd == "apply-patch":
            patch_doc, _ = read_json(args.patch)
            if not isinstance(patch_doc, list):
                print("ERROR: Patch file must be a JSON array of operations.", file=sys.stderr)
                sys.exit(2)
            new_doc = apply_patch(new_doc, patch_doc)
        elif args.cmd == "clone-layer":
            new_doc = clone_layer(new_doc, args.from_pointer, args.to_pointer, args.name)

        after_bytes = json.dumps(new_doc, indent=2, ensure_ascii=False).encode("utf-8")
        if getattr(args, "dry_run", False):
            diff = unified_diff(before_bytes, after_bytes, fromfile=args.json_file, tofile=f"{args.json_file} (new)")
            print(diff if diff else "(no changes)")
            return
        else:
            path, new_hash = write_atomic(args.json_file, new_doc)
            print(f"Wrote {path} (SHA256 {new_hash})")
            return

if __name__ == "__main__":
    main()
