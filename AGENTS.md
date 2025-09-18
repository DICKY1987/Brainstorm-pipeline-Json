# Repository Guidelines

## Project Structure & Module Organization
- Root assets live in `Jason updates/`.
- JSON plans: `expanded_12_layer_plan.json` (12-layer SDLC flow).
- JSON patches: files named like `patch_*.json` (RFC 6902 ops).
- Tools: `json_plan_tool.py` (safe JSON edit/patch CLI).
- Notes/evidence: `evidence_brainstorm_example.md`, `Jason updates.md`.

## Build, Test, and Development Commands
- Run tool (validate JSON):
  - `python "Jason updates/json_plan_tool.py" path/to/plan.json validate --print-keys`
- Get/set via JSON Pointer:
  - `python "Jason updates/json_plan_tool.py" plan.json get --pointer "/layers/0/name"`
  - `python "Jason updates/json_plan_tool.py" plan.json set --pointer "/orchestrator/max_global_loops" --value "3" --dry-run`
- Apply RFC6902 patch:
  - `python "Jason updates/json_plan_tool.py" plan.json apply-patch --patch "Jason updates/patch_file.json" --dry-run`
- Clone a layer template:
  - `python "Jason updates/json_plan_tool.py" plan.json clone-layer --from-pointer "/layers/0" --to-pointer "/layers/-" --name "New Layer" --dry-run`

## Coding Style & Naming Conventions
- Python 3.11+, 4‑space indents, type hints where useful.
- Filenames: snake_case for scripts; JSON keys are lowerCamel or snake_case as in existing files.
- Prefer small, composable patches over manual edits.

## Testing Guidelines
- No formal test suite in-repo. When adding tests, use `pytest` and place files under `tests/` as `test_*.py`.
- For ad‑hoc checks, use `--dry-run` to preview diffs before writing.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`.
- In PRs, include: purpose, sample commands run, before/after JSON diff snippets, and linked issues.
- Group related JSON changes into a single patch file and attach the patch in the PR.

## Security & Configuration Tips
- Do not commit secrets; JSON files may reference external stores—use placeholders.
- The tool writes atomically and creates timestamped `.bak` files; review backups before cleanup.
- Validate patches locally with `--dry-run` and inspect the unified diff before applying.

## Agent-Specific Instructions
- Prefer patching via `apply-patch` or `clone-layer` rather than hand‑editing.
- When extending the plan, keep IDs (`S1A`, `S1D`, …) unique and update `transitions` accordingly.
- Keep artifacts/flow/gates fields consistent across layers to preserve orchestration semantics.

