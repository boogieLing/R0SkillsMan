#!/usr/bin/env python3
"""Run the non-commit r0-submit preparation flow end to end.

Flow:
- prepare submit record
- run r0-review baseline
- refresh scope-check block after local record artifacts are created

This script never stages files and never invokes r0push.
"""

from __future__ import annotations

import argparse
import json
import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
PREPARE = SKILL_ROOT / "scripts" / "prepare_submit_record.py"
SCOPE_WRITER = SKILL_ROOT / "scripts" / "write_r0push_scope_record.py"
REVIEW_BASELINE = SKILL_ROOT.parent / "r0-review" / "scripts" / "r0-review_baseline.sh"
START = "<!-- review-baseline:start -->"
END = "<!-- review-baseline:end -->"
MANIFEST_SCHEMA_VERSION = 2
COMPLEXITY_HOTSPOT_THRESHOLD = 10
BRANCH_SIGNAL_HOTSPOT_THRESHOLD = 12


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def git(repo_root: Path, *args: str) -> str:
    completed = run(["git", *args], repo_root)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise RuntimeError(f"{' '.join(args)}: {stderr}")
    return completed.stdout.strip()


def parse_keyed_output(text: str, key: str) -> str | None:
    prefix = f"{key}="
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def upsert_block(text: str, block: str) -> str:
    if START in text and END in text:
        start = text.index(START)
        line_start = text.rfind("\n", 0, start)
        start = 0 if line_start == -1 else line_start + 1
        end = text.index(END) + len(END)
        return text[:start].rstrip() + "\n" + block + text[end:]
    return text.rstrip() + "\n\n" + block + "\n"


def replace_line(text: str, prefix: str, value: str) -> str:
    lines = text.splitlines()
    replaced = False
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{prefix} {value}".rstrip()
            replaced = True
            break
    if not replaced:
        lines.append(f"{prefix} {value}".rstrip())
    return "\n".join(lines) + "\n"


def render_review_block(mode: str, out_dir: Path, summary: Path, stdout: str, exit_code: int) -> str:
    rel_out = out_dir.name if out_dir.parent.name == "_artifacts" else str(out_dir)
    return "\n".join(
        [
            "## Review Baseline Artifact",
            START,
            "```text",
            f"mode={mode}",
            f"exit_code={exit_code}",
            f"out_dir={out_dir}",
            f"summary={summary}",
            f"artifact_label={rel_out}",
            "",
            "[stdout]",
            stdout.strip() or "<empty>",
            "```",
            END,
        ]
    )


def rel_to_repo(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def review_metrics(out_dir: Path) -> dict[str, object]:
    complexity_csv = out_dir / "complexity.csv"
    comment_csv = out_dir / "comment_coverage.csv"
    security_hits = out_dir / "security_hits.txt"

    metrics: dict[str, object] = {
        "target_count": 0,
        "total_lines": 0,
        "total_branch_signals": 0,
        "max_est_complexity": 0,
        "max_nesting": 0,
        "comment_file_count": 0,
        "comment_total_non_empty": 0,
        "comment_total_lines": 0,
        "comment_ratio_avg": 0.0,
        "security_hit_count": 0,
    }

    if complexity_csv.exists():
        with complexity_csv.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                metrics["target_count"] += 1
                metrics["total_lines"] += int(row["total_lines"])
                metrics["total_branch_signals"] += int(row["branch_signals"])
                metrics["max_est_complexity"] = max(metrics["max_est_complexity"], int(row["est_complexity"]))
                metrics["max_nesting"] = max(metrics["max_nesting"], int(row["max_nesting"]))

    if comment_csv.exists():
        ratio_sum = 0.0
        with comment_csv.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                metrics["comment_file_count"] += 1
                metrics["comment_total_non_empty"] += int(row["total_non_empty"])
                metrics["comment_total_lines"] += int(row["comment_lines"])
                ratio_sum += float(row["comment_ratio"])
        if metrics["comment_file_count"]:
            metrics["comment_ratio_avg"] = round(ratio_sum / metrics["comment_file_count"], 4)

    if security_hits.exists():
        metrics["security_hit_count"] = sum(1 for line in security_hits.read_text(encoding="utf-8").splitlines() if line.strip())

    return metrics


def derive_risk_flags(metrics: dict[str, object], final_scope_exit_code: int | str | None) -> dict[str, bool]:
    max_est_complexity = int(metrics.get("max_est_complexity", 0) or 0)
    total_branch_signals = int(metrics.get("total_branch_signals", 0) or 0)
    security_hit_count = int(metrics.get("security_hit_count", 0) or 0)
    target_count = int(metrics.get("target_count", 0) or 0)

    return {
        "review_has_security_hits": security_hit_count > 0,
        "review_has_complexity_hotspot": max_est_complexity >= COMPLEXITY_HOTSPOT_THRESHOLD,
        "review_has_branch_signal_hotspot": total_branch_signals >= BRANCH_SIGNAL_HOTSPOT_THRESHOLD,
        "review_has_no_targets": target_count == 0,
        "scope_check_blocked": final_scope_exit_code not in (0, "0", None),
    }


def risk_flag_thresholds() -> dict[str, object]:
    return {
        "review_has_security_hits": "security_hit_count > 0",
        "review_has_complexity_hotspot": f"max_est_complexity >= {COMPLEXITY_HOTSPOT_THRESHOLD}",
        "review_has_branch_signal_hotspot": f"total_branch_signals >= {BRANCH_SIGNAL_HOTSPOT_THRESHOLD}",
        "review_has_no_targets": "target_count == 0",
        "scope_check_blocked": "final_scope_exit_code != 0",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare r0-submit dry-run artifacts without invoking r0push.")
    parser.add_argument("--repo-root", default=".", help="Git repo root or any path inside it.")
    parser.add_argument("--review-mode", default="quick", choices=["quick", "full"], help="Mode for r0-review baseline.")
    parser.add_argument("--record-file", help="Optional target record file.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    try:
        repo_root = Path(git(repo_root, "rev-parse", "--show-toplevel"))
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    for required in (PREPARE, SCOPE_WRITER, REVIEW_BASELINE):
        if not required.exists():
            print(f"[ERROR] missing helper: {required}")
            return 1

    prepare_cmd = ["python3", str(PREPARE), "--repo-root", str(repo_root)]
    if args.record_file:
        prepare_cmd.extend(["--record-file", args.record_file])
    prepared = run(prepare_cmd, repo_root)
    if prepared.returncode != 0:
        sys.stdout.write(prepared.stdout)
        sys.stderr.write(prepared.stderr)
        return prepared.returncode

    record_file_raw = parse_keyed_output(prepared.stdout, "record_file")
    if not record_file_raw:
        print("[ERROR] prepare_submit_record.py did not report record_file")
        return 1
    record_file = Path(record_file_raw)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = repo_root / "r0" / "review" / "_artifacts" / f"submit_dry_run_{ts}"
    baseline = run(
        ["bash", str(REVIEW_BASELINE), "--mode", args.review_mode, "--out-dir", str(out_dir)],
        repo_root,
    )
    summary = out_dir / "summary.md"

    text = record_file.read_text(encoding="utf-8")
    text = upsert_block(
        text,
        render_review_block(args.review_mode, out_dir, summary, baseline.stdout, baseline.returncode),
    )

    refresh = run(
        ["python3", str(SCOPE_WRITER), "--repo-root", str(repo_root), "--record-file", str(record_file)],
        repo_root,
    )
    if refresh.returncode != 0:
        sys.stdout.write(refresh.stdout)
        sys.stderr.write(refresh.stderr)
        return refresh.returncode

    final_scope = parse_keyed_output(refresh.stdout, "checker_exit_code")
    final_scope_value = int(final_scope) if final_scope and final_scope.isdigit() else final_scope
    metrics = review_metrics(out_dir)
    manifest_path = record_file.with_suffix(".dry-run.json")
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "repo_root": str(repo_root),
        "record_file": str(record_file),
        "review_mode": args.review_mode,
        "review_out_dir": str(out_dir),
        "review_summary": str(summary),
        "review_exit_code": baseline.returncode,
        "review_metrics": metrics,
        "risk_flag_thresholds": risk_flag_thresholds(),
        "risk_flags": derive_risk_flags(metrics, final_scope_value),
        "final_scope_exit_code": final_scope_value,
        "prepared_at": datetime.now().isoformat(timespec="seconds"),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    text = record_file.read_text(encoding="utf-8")
    text = upsert_block(
        text,
        render_review_block(args.review_mode, out_dir, summary, baseline.stdout, baseline.returncode),
    )
    text = replace_line(text, "- dry-run manifest 路径：", rel_to_repo(manifest_path, repo_root))
    record_file.write_text(text, encoding="utf-8")

    print(f"repo_root={repo_root}")
    print(f"record_file={record_file}")
    print(f"manifest_file={manifest_path}")
    print(f"review_out_dir={out_dir}")
    print(f"review_summary={summary}")
    print(f"review_exit_code={baseline.returncode}")
    print(f"final_scope_exit_code={final_scope or '<unknown>'}")
    print("[OK] dry-run submit flow completed without invoking r0push.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
