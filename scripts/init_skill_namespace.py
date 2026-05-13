#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


DEFAULT_NAME = "ouo"
SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__"}
HOME_PREFIXES = (
    "/Users/r0/",
    "/home/r0/",
)
MAX_RESIDUALS = 50


@dataclass(frozen=True)
class NamespaceConfig:
    repo_root: Path
    current_prefix: str
    target_prefix: str
    current_contract_name: str
    target_contract_name: str
    current_repo_name: str
    target_repo_name: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Initialize a cloned skill repository by replacing the current "
            "skill namespace prefix with a custom one."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to rewrite. Defaults to the current directory.",
    )
    parser.add_argument(
        "--name",
        help=(
            "Target namespace prefix. Defaults to the sanitized Git user name; "
            f"falls back to {DEFAULT_NAME!r}."
        ),
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow running on a dirty worktree. Disabled by default for safety.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned changes without modifying files.",
    )
    return parser.parse_args()


def normalize_name(raw: str) -> str:
    value = unicodedata.normalize("NFKD", raw.strip().lower())
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value


def run_git_config(repo_root: Path, key: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "config", "--get", key],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def detect_target_prefix(repo_root: Path, explicit_name: str | None) -> str:
    candidates: list[str] = []
    if explicit_name:
        candidates.append(explicit_name)

    user_name = run_git_config(repo_root, "user.name")
    if user_name:
        candidates.append(user_name)

    user_email = run_git_config(repo_root, "user.email")
    if user_email and "@" in user_email:
        candidates.append(user_email.split("@", 1)[0])

    candidates.append(DEFAULT_NAME)

    for candidate in candidates:
        normalized = normalize_name(candidate)
        if normalized:
            return normalized
    return DEFAULT_NAME


def detect_current_prefix(repo_root: Path) -> str:
    shared_dir = repo_root / "shared"
    for contract_file in sorted(shared_dir.glob("*-core-contract.md")):
        name = contract_file.name.removesuffix("-core-contract.md")
        if name:
            return name

    for skill_dir in sorted(repo_root.glob("*-request")):
        if skill_dir.is_dir():
            return skill_dir.name.rsplit("-", 1)[0]

    raise SystemExit("error: unable to detect the current skill prefix")


def build_config(repo_root: Path, explicit_name: str | None) -> NamespaceConfig:
    current_prefix = detect_current_prefix(repo_root)
    target_prefix = detect_target_prefix(repo_root, explicit_name)
    current_repo_name = repo_root.name
    current_contract_name = f"{current_prefix}-core-contract.md"
    target_contract_name = f"{target_prefix}-core-contract.md"

    if current_repo_name == f"{current_prefix}-skills":
        target_repo_name = f"{target_prefix}-skills"
    else:
        target_repo_name = current_repo_name.replace(current_prefix, target_prefix)

    return NamespaceConfig(
        repo_root=repo_root,
        current_prefix=current_prefix,
        target_prefix=target_prefix,
        current_contract_name=current_contract_name,
        target_contract_name=target_contract_name,
        current_repo_name=current_repo_name,
        target_repo_name=target_repo_name,
    )


def ensure_safe_worktree(repo_root: Path, allow_dirty: bool) -> None:
    if allow_dirty or not (repo_root / ".git").exists():
        return

    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--short"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.stdout.strip():
        raise SystemExit(
            "error: worktree is dirty; commit/stash changes or rerun with "
            "--allow-dirty"
        )


def is_text_file(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if b"\x00" in data:
        return False
    return True


def filtered_dirnames(
    dirnames: list[str],
    root_path: Path,
    repo_root: Path,
    config: NamespaceConfig | None = None,
) -> list[str]:
    skip_dirs = set(SKIP_DIRS)
    if config is not None and root_path == repo_root:
        # The bare prefix directory is the local record root, not skill source.
        # Do not rewrite user-local execution records during namespace setup.
        skip_dirs.update({config.current_prefix, config.target_prefix})
    return [name for name in dirnames if name not in skip_dirs]


def token_pattern(token: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(token)}(?=[^A-Za-z0-9]|$)"
    )


def escaped_token_pattern(token: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<=\\[nrt]){re.escape(token)}(?=[^A-Za-z0-9]|$)"
    )


def compound_prefix_pattern(token: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(token)}(?=[a-z])"
    )


def replace_placeholder_token(text: str, current: str, target: str) -> str:
    updated = token_pattern(current).sub(target, text)
    updated = escaped_token_pattern(current).sub(target, updated)
    updated = compound_prefix_pattern(current).sub(target, updated)
    return updated


def apply_text_replacements(text: str, config: NamespaceConfig) -> str:
    updated = text

    for home_prefix in HOME_PREFIXES:
        updated = updated.replace(home_prefix, "$HOME/")

    updated = updated.replace(config.current_contract_name, config.target_contract_name)
    updated = updated.replace(config.current_repo_name, config.target_repo_name)

    updated = replace_placeholder_token(
        updated,
        config.current_prefix.upper(),
        config.target_prefix.upper(),
    )
    updated = replace_placeholder_token(
        updated,
        config.current_prefix,
        config.target_prefix,
    )
    return updated


def rewrite_text_files(
    repo_root: Path,
    config: NamespaceConfig,
    *,
    dry_run: bool,
) -> list[Path]:
    changed_files: list[Path] = []
    for root, dirnames, filenames in os.walk(repo_root):
        root_path = Path(root)
        dirnames[:] = filtered_dirnames(dirnames, root_path, repo_root, config)
        for filename in filenames:
            file_path = root_path / filename
            if file_path.is_symlink() or not file_path.is_file():
                continue
            if not is_text_file(file_path):
                continue
            try:
                original = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            updated = apply_text_replacements(original, config)
            if updated == original:
                continue
            changed_files.append(file_path.relative_to(repo_root))
            if not dry_run:
                file_path.write_text(updated, encoding="utf-8")
    return changed_files


def rename_segment(name: str, config: NamespaceConfig) -> str:
    renamed = apply_text_replacements(name, config)
    return renamed


def rename_paths(
    repo_root: Path,
    config: NamespaceConfig,
    *,
    dry_run: bool,
) -> list[tuple[Path, Path]]:
    candidates: list[Path] = []
    for root, dirnames, filenames in os.walk(repo_root):
        root_path = Path(root)
        dirnames[:] = filtered_dirnames(dirnames, root_path, repo_root, config)
        for dirname in dirnames:
            candidates.append(root_path / dirname)
        for filename in filenames:
            candidates.append(root_path / filename)

    candidates.sort(
        key=lambda path: (len(path.relative_to(repo_root).parts), str(path)),
        reverse=True,
    )

    renamed_paths: list[tuple[Path, Path]] = []
    for path in candidates:
        new_name = rename_segment(path.name, config)
        if new_name == path.name:
            continue
        target_path = path.with_name(new_name)
        if target_path.exists():
            raise SystemExit(
                f"error: refusing to rename {path.relative_to(repo_root)} to "
                f"{target_path.relative_to(repo_root)} because the target already exists"
            )
        renamed_paths.append(
            (path.relative_to(repo_root), target_path.relative_to(repo_root))
        )
        if not dry_run:
            path.rename(target_path)
    return renamed_paths


def residual_patterns(config: NamespaceConfig) -> list[tuple[str, re.Pattern[str]]]:
    return [
        ("upper-token", token_pattern(config.current_prefix.upper())),
        ("upper-escaped-token", escaped_token_pattern(config.current_prefix.upper())),
        ("upper-compound-prefix", compound_prefix_pattern(config.current_prefix.upper())),
        ("lower-token", token_pattern(config.current_prefix)),
        ("lower-escaped-token", escaped_token_pattern(config.current_prefix)),
        ("lower-compound-prefix", compound_prefix_pattern(config.current_prefix)),
    ]


def find_residual_placeholders(repo_root: Path, config: NamespaceConfig) -> list[str]:
    patterns = residual_patterns(config)
    findings: list[str] = []
    for root, dirnames, filenames in os.walk(repo_root):
        root_path = Path(root)
        dirnames[:] = filtered_dirnames(dirnames, root_path, repo_root, config)
        for filename in filenames:
            file_path = root_path / filename
            if file_path.is_symlink() or not file_path.is_file():
                continue
            if not is_text_file(file_path):
                continue
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_no, line in enumerate(lines, 1):
                for label, pattern in patterns:
                    if not pattern.search(line):
                        continue
                    rel = file_path.relative_to(repo_root)
                    findings.append(f"{rel}:{line_no}:{label}: {line.strip()}")
                    if len(findings) >= MAX_RESIDUALS:
                        return findings
                    break
    return findings


def print_summary(
    config: NamespaceConfig,
    *,
    dry_run: bool,
    changed_files: list[Path],
    renamed_paths: list[tuple[Path, Path]],
    residuals: list[str],
) -> None:
    mode = "dry-run" if dry_run else "applied"
    print(f"mode={mode}")
    print(f"repo_root={config.repo_root}")
    print(f"current_prefix={config.current_prefix}")
    print(f"target_prefix={config.target_prefix}")
    print(f"text_files_changed={len(changed_files)}")
    for file_path in changed_files:
        print(f"  file: {file_path}")
    print(f"paths_renamed={len(renamed_paths)}")
    for old_path, new_path in renamed_paths:
        print(f"  rename: {old_path} -> {new_path}")
    if dry_run:
        print("residual_check=skipped_dry_run")
    else:
        print(f"residual_placeholders={len(residuals)}")
        for item in residuals:
            print(f"  residual: {item}")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    config = build_config(repo_root, args.name)

    if config.current_prefix == config.target_prefix:
        print(
            f"target prefix is already {config.target_prefix!r}; nothing to do",
            file=sys.stderr,
        )
        return 0

    ensure_safe_worktree(repo_root, args.allow_dirty)
    changed_files = rewrite_text_files(repo_root, config, dry_run=args.dry_run)
    renamed_paths = rename_paths(repo_root, config, dry_run=args.dry_run)
    residuals = [] if args.dry_run else find_residual_placeholders(repo_root, config)
    print_summary(
        config,
        dry_run=args.dry_run,
        changed_files=changed_files,
        renamed_paths=renamed_paths,
        residuals=residuals,
    )
    if residuals:
        print(
            "error: namespace initialization left residual placeholder tokens; "
            "fix the listed files or add an explicit rule before continuing",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
