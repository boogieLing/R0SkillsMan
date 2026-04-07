# Diagram Gate Rules

## Gate checks

1. Referenced file must exist.
2. PNG size must be readable via `sips`.
3. PNG must not be placeholder size (`45x13` or <= `60x20`).
4. PNG must be above minimum size threshold (default `120x40`).
5. SVG must not contain `foreignObject`.

## Auto-fix strategy

1. Wrap risky SVG as a PNG-backed SVG wrapper when sibling PNG exists.
2. Regenerate PNG (and wrapper SVG) from same-name `.mmd` via `mmdc` when file is missing/tiny/placeholder.
3. Optionally drop unresolved markdown image references when `--drop-unfixable-refs` is enabled.

## Exit code

- `0`: gate passed (no issues after fix)
- `2`: gate failed
