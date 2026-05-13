#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import bisect
import heapq
import json
import os
import posixpath
import re
from collections import Counter, defaultdict, deque
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Iterable


IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".nuxt",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "DerivedData",
    "Pods",
    "target",
    "r0",
}

SUPPORTED_EXTS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".swift",
    ".go",
    ".java",
    ".kt",
    ".kts",
    ".rs",
}

RESOLUTION_EXTS = (".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".swift", ".go", ".java", ".kt", ".kts", ".rs")

ENTRY_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "__main__.py",
    "index.js",
    "index.ts",
    "main.js",
    "main.ts",
    "app.js",
    "app.ts",
    "server.js",
    "server.ts",
    "App.jsx",
    "App.tsx",
    "main.swift",
    "Package.swift",
    "main.go",
    "cmd.go",
    "Cargo.toml",
    "package.json",
    "pyproject.toml",
    "go.mod",
}

LAYER_HINTS = {
    "entry": {"main", "app", "server", "cmd", "cli", "bootstrap", "entry"},
    "api": {"api", "route", "routes", "router", "handler", "handlers", "controller", "controllers"},
    "domain": {"domain", "model", "models", "entity", "entities", "schema", "schemas"},
    "service": {"service", "services", "usecase", "usecases", "application"},
    "data": {"repo", "repos", "repository", "repositories", "dao", "db", "database", "store", "storage"},
    "ui": {"ui", "view", "views", "component", "components", "page", "pages", "screen", "screens"},
    "config": {"config", "configs", "setting", "settings", "env"},
    "infra": {"infra", "infrastructure", "adapter", "adapters", "client", "clients", "middleware"},
    "test": {"test", "tests", "spec", "specs", "__tests__"},
    "tooling": {"script", "scripts", "tool", "tools", "bin"},
}


@dataclass
class Symbol:
    name: str
    kind: str
    line: int | None = None
    complexity: int = 0


@dataclass
class FileReport:
    path: str
    language: str
    parser: str
    lines: int
    layer: str
    imports: list[str] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    entry_score: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        return self.lines + len(self.imports) * 8 + len(self.symbols) * 12 + sum(s.complexity for s in self.symbols)


@dataclass
class ResolvedEdge:
    from_path: str
    to_path: str | None
    imported: str
    status: str


class UnionFind:
    def __init__(self, nodes: Iterable[str]) -> None:
        self.parent = {node: node for node in nodes}
        self.size = {node: 1 for node in nodes}

    def find(self, item: str) -> str:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if self.size[root_left] < self.size[root_right]:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        self.size[root_left] += self.size[root_right]

    def groups(self) -> list[list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for node in self.parent:
            grouped[self.find(node)].append(node)
        return [sorted(nodes) for nodes in grouped.values()]


class PythonVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[str] = []
        self.symbols: list[Symbol] = []

    def visit_Import(self, node: ast.Import) -> None:
        self.imports.extend(alias.name for alias in node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        prefix = "." * node.level + (node.module or "")
        if node.names and prefix:
            self.imports.extend(f"{prefix}.{alias.name}" if prefix != "." else f".{alias.name}" for alias in node.names)
        else:
            self.imports.append(prefix or ".")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.symbols.append(Symbol(node.name, "class", node.lineno, complexity=_complexity(node)))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.symbols.append(Symbol(node.name, "function", node.lineno, complexity=_complexity(node)))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.symbols.append(Symbol(node.name, "async_function", node.lineno, complexity=_complexity(node)))
        self.generic_visit(node)


def _complexity(node: ast.AST) -> int:
    branches = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.ExceptHandler,
        ast.With,
        ast.AsyncWith,
        ast.BoolOp,
        ast.Match,
    )
    return 1 + sum(isinstance(child, branches) for child in ast.walk(node))


def language_for(path: Path) -> str:
    ext = path.suffix
    return {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".swift": "swift",
        ".go": "go",
        ".java": "java",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".rs": "rust",
    }.get(ext, "unknown")


def should_skip(path: Path, root: Path, include_tests: bool) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    parts = set(rel.parts)
    if parts & IGNORE_DIRS:
        return True
    if path.suffix not in SUPPORTED_EXTS and path.name not in ENTRY_NAMES:
        return True
    if not include_tests and parts & LAYER_HINTS["test"]:
        return True
    return False


def layer_for(path: Path | PurePosixPath) -> str:
    tokens = {part.lower() for part in path.with_suffix("").parts}
    for layer, hints in LAYER_HINTS.items():
        if tokens & hints:
            return layer
    name = path.stem.lower()
    if name in LAYER_HINTS["entry"]:
        return "entry"
    return "unknown"


def entry_score(path: Path) -> int:
    score = 0
    if path.name in ENTRY_NAMES:
        score += 80
    if path.parent.name.lower() in {"cmd", "cli", "bin", "app", "src"}:
        score += 20
    if path.stem.lower() in {"main", "app", "server", "index"}:
        score += 30
    return score


def line_offsets(text: str) -> list[int]:
    return [0] + [index + 1 for index, char in enumerate(text) if char == "\n"]


def line_for_offset(offsets: list[int], offset: int) -> int:
    return bisect.bisect_right(offsets, offset)


def parse_python(path: Path, rel: Path, text: str) -> FileReport:
    report = FileReport(
        str(rel),
        "python",
        "python-ast",
        text.count("\n") + 1,
        layer_for(PurePosixPath(rel.as_posix())),
        entry_score=entry_score(path),
    )
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        report.errors.append(f"SyntaxError:{exc.lineno}:{exc.msg}")
        return report
    visitor = PythonVisitor()
    visitor.visit(tree)
    report.imports = sorted(set(visitor.imports))
    report.symbols = visitor.symbols
    return report


IMPORT_RE = re.compile(
    r"""(?:import\s+(?:[\w*{}\s,]+?\s+from\s+)?["']([^"']+)["']|require\(["']([^"']+)["']\)|from\s+([\w.*/@-]+)\s+import)"""
)
GO_IMPORT_BLOCK_RE = re.compile(r"^\s*import\s*\((.*?)^\s*\)", re.MULTILINE | re.DOTALL)
GO_SINGLE_IMPORT_RE = re.compile(r'^\s*import\s+(?:[._\w]+\s+)?\"([^\"]+)\"', re.MULTILINE)
GO_QUOTED_IMPORT_RE = re.compile(r'\"([^\"]+)\"')
SYMBOL_PATTERNS = [
    ("class", re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_][\w]*)", re.MULTILINE)),
    ("interface", re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_][\w]*)", re.MULTILINE)),
    ("struct", re.compile(r"^\s*(?:public\s+|private\s+|internal\s+)?struct\s+([A-Za-z_][\w]*)", re.MULTILINE)),
    ("protocol", re.compile(r"^\s*(?:public\s+|private\s+|internal\s+)?protocol\s+([A-Za-z_][\w]*)", re.MULTILINE)),
    ("function", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][\w]*)", re.MULTILINE)),
    ("function", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][\w]*)\s*=\s*(?:async\s*)?\(", re.MULTILINE)),
    ("function", re.compile(r"^\s*(?:public\s+|private\s+|internal\s+)?func\s+([A-Za-z_][\w]*)", re.MULTILINE)),
    ("function", re.compile(r"^\s*func\s+([A-Za-z_][\w]*)", re.MULTILINE)),
    ("function", re.compile(r"^\s*fn\s+([A-Za-z_][\w]*)", re.MULTILINE)),
    ("class", re.compile(r"^\s*(?:public\s+)?class\s+([A-Za-z_][\w]*)", re.MULTILINE)),
]


def parse_go_imports(text: str) -> list[str]:
    imports: list[str] = []
    for block in GO_IMPORT_BLOCK_RE.finditer(text):
        imports.extend(GO_QUOTED_IMPORT_RE.findall(block.group(1)))
    imports.extend(GO_SINGLE_IMPORT_RE.findall(text))
    return sorted(set(imports))


def parse_structural(path: Path, rel: Path, text: str) -> FileReport:
    report = FileReport(
        str(rel),
        language_for(path),
        "structural-scan",
        text.count("\n") + 1,
        layer_for(PurePosixPath(rel.as_posix())),
        entry_score=entry_score(path),
    )
    imports = parse_go_imports(text) if path.suffix == ".go" else []
    if not imports:
        for match in IMPORT_RE.finditer(text):
            imports.extend(group for group in match.groups() if group)
    report.imports = sorted(set(imports))
    offsets = line_offsets(text)
    symbols: list[Symbol] = []
    for kind, pattern in SYMBOL_PATTERNS:
        for match in pattern.finditer(text):
            symbols.append(Symbol(match.group(1), kind, line_for_offset(offsets, match.start()), 1))
    report.symbols = sorted(symbols, key=lambda item: (item.line or 0, item.kind, item.name))
    return report


def collect_files(root: Path, max_files: int, include_tests: bool) -> list[Path]:
    files: list[Path] = []
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        dirnames[:] = sorted(
            dirname
            for dirname in dirnames
            if dirname not in IGNORE_DIRS and (include_tests or dirname not in LAYER_HINTS["test"])
        )
        for filename in sorted(filenames):
            path = current_path / filename
            if should_skip(path, root, include_tests):
                continue
            files.append(path)
            if len(files) >= max_files:
                return files
    return files


def analyze_file(path: Path, root: Path) -> FileReport:
    rel = path.relative_to(root)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return FileReport(str(rel), language_for(path), "unreadable", 0, layer_for(PurePosixPath(rel.as_posix())), errors=[str(exc)])
    if path.suffix == ".py":
        return parse_python(path, rel, text)
    return parse_structural(path, rel, text)


def analyze_file_worker(args: tuple[str, str]) -> FileReport:
    path, root = args
    return analyze_file(Path(path), Path(root))


def analyze_files(paths: list[Path], root: Path, workers: int) -> list[FileReport]:
    if workers <= 1 or len(paths) <= 1:
        return [analyze_file(path, root) for path in paths]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(analyze_file_worker, ((str(path), str(root)) for path in paths), chunksize=32))


def read_go_module(root: Path) -> str | None:
    go_mod = root / "go.mod"
    if not go_mod.is_file():
        return None
    for line in go_mod.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("module "):
            return stripped.split(None, 1)[1].strip()
    return None


def module_keys_for(path: PurePosixPath, go_module: str | None = None) -> set[str]:
    keys: set[str] = {path.as_posix()}
    if path.suffix:
        stem = path.with_suffix("")
        keys.add(stem.as_posix())
        keys.add(".".join(stem.parts))
        if path.name.startswith("__init__."):
            keys.add(path.parent.as_posix())
            keys.add(".".join(path.parent.parts))
        if path.stem == "index":
            keys.add(path.parent.as_posix())
            keys.add(".".join(path.parent.parts))
        if path.suffix == ".go":
            package_dir = path.parent.as_posix()
            if package_dir and package_dir != ".":
                keys.add(package_dir)
                if go_module:
                    keys.add(f"{go_module}/{package_dir}")
            elif go_module:
                keys.add(go_module)
    return {key for key in keys if key and key != "."}


def build_module_index(reports: list[FileReport], go_module: str | None = None) -> tuple[dict[str, str], dict[str, FileReport]]:
    module_index: dict[str, str] = {}
    reports_by_path = {report.path: report for report in reports}
    for report in reports:
        path = PurePosixPath(report.path)
        for key in module_keys_for(path, go_module):
            module_index.setdefault(key, report.path)
    return module_index, reports_by_path


def candidate_paths(base: str) -> list[str]:
    normalized = posixpath.normpath(base).lstrip("./")
    candidates = [normalized]
    for ext in RESOLUTION_EXTS:
        candidates.append(f"{normalized}{ext}")
    for ext in RESOLUTION_EXTS:
        candidates.append(posixpath.join(normalized, f"index{ext}"))
        candidates.append(posixpath.join(normalized, f"__init__{ext}"))
    return candidates


def resolve_candidate(base: str, module_index: dict[str, str]) -> str | None:
    for candidate in candidate_paths(base):
        if candidate in module_index:
            return module_index[candidate]
    dotted = base.replace("/", ".")
    return module_index.get(dotted)


def resolve_relative_import(importer_path: str, imported: str, module_index: dict[str, str]) -> str | None:
    parent = PurePosixPath(importer_path).parent.as_posix()
    if imported.startswith(("./", "../")):
        return resolve_candidate(posixpath.normpath(posixpath.join(parent, imported)), module_index)

    level = len(imported) - len(imported.lstrip("."))
    rest = imported[level:]
    parts = list(PurePosixPath(parent).parts)
    for _ in range(max(level - 1, 0)):
        if parts:
            parts.pop()
    base = "/".join(parts)
    if rest:
        base = posixpath.join(base, rest.replace(".", "/"))
    return resolve_candidate(base or ".", module_index)


def resolve_import(importer_path: str, imported: str, module_index: dict[str, str]) -> str | None:
    if imported.startswith("."):
        return resolve_relative_import(importer_path, imported, module_index)
    if imported in module_index:
        return module_index[imported]
    slash_candidate = resolve_candidate(imported, module_index)
    if slash_candidate:
        return slash_candidate
    return resolve_candidate(imported.replace(".", "/"), module_index)


def looks_internal(imported: str, top_dirs: set[str]) -> bool:
    if imported.startswith("."):
        return True
    normalized = imported.lstrip("./")
    head = re.split(r"[./]", normalized, maxsplit=1)[0]
    return head in top_dirs


def infer_edges(reports: list[FileReport], go_module: str | None = None) -> list[ResolvedEdge]:
    module_index, _ = build_module_index(reports, go_module)
    top_dirs = {PurePosixPath(report.path).parts[0] for report in reports if len(PurePosixPath(report.path).parts) > 1}
    edges: list[ResolvedEdge] = []
    seen: set[tuple[str, str, str | None]] = set()
    for report in reports:
        for imported in report.imports:
            resolved = resolve_import(report.path, imported, module_index)
            status = "resolved" if resolved else ("unresolved_internal" if looks_internal(imported, top_dirs) else "external")
            key = (report.path, imported, resolved)
            if key in seen:
                continue
            seen.add(key)
            edges.append(ResolvedEdge(report.path, resolved, imported, status))
    return edges


def build_adjacency(nodes: Iterable[str], edges: list[ResolvedEdge]) -> dict[str, list[str]]:
    adjacency = {node: [] for node in nodes}
    for edge in edges:
        if edge.status == "resolved" and edge.to_path:
            adjacency.setdefault(edge.from_path, []).append(edge.to_path)
            adjacency.setdefault(edge.to_path, [])
    return {node: sorted(set(targets)) for node, targets in adjacency.items()}


def architecture_clusters(reports: list[FileReport], edges: list[ResolvedEdge]) -> list[dict[str, object]]:
    nodes = [report.path for report in reports]
    uf = UnionFind(nodes)
    go_package_groups: dict[str, list[str]] = defaultdict(list)
    for report in reports:
        if report.language == "go":
            go_package_groups[PurePosixPath(report.path).parent.as_posix()].append(report.path)
    for files in go_package_groups.values():
        if len(files) > 1:
            first = files[0]
            for file in files[1:]:
                uf.union(first, file)
    for edge in edges:
        if edge.status == "resolved" and edge.to_path:
            uf.union(edge.from_path, edge.to_path)
    report_map = {report.path: report for report in reports}
    clusters = []
    for index, files in enumerate(sorted(uf.groups(), key=lambda group: (-len(group), group[0])), start=1):
        if len(files) <= 1:
            continue
        cluster_reports = [report_map[file] for file in files]
        layers = Counter(report.layer for report in cluster_reports)
        languages = Counter(report.language for report in cluster_reports)
        hotspots = heapq.nlargest(5, cluster_reports, key=lambda report: (report.score, report.path))
        entries = sorted((report for report in cluster_reports if report.entry_score), key=lambda report: (-report.entry_score, report.path))[:5]
        clusters.append(
            {
                "id": f"cluster-{index}",
                "size": len(files),
                "layers": dict(layers.most_common()),
                "languages": dict(languages.most_common()),
                "entry_candidates": [report.path for report in entries],
                "hotspots": [report.path for report in hotspots],
                "files": files[:50],
                "truncated": len(files) > 50,
            }
        )
    return clusters[:30]


def strongly_connected_components(adjacency: dict[str, list[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in adjacency.get(node, []):
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] == indices[node]:
            component = []
            while True:
                target = stack.pop()
                on_stack.remove(target)
                component.append(target)
                if target == node:
                    break
            components.append(sorted(component))

    for node in adjacency:
        if node not in indices:
            visit(node)
    return sorted((component for component in components if len(component) > 1), key=lambda group: (-len(group), group[0]))


def dag_layers(adjacency: dict[str, list[str]], sccs: list[list[str]]) -> list[dict[str, object]]:
    component_for: dict[str, int] = {}
    components: list[list[str]] = []
    scc_nodes = {node for component in sccs for node in component}
    for component in sccs:
        component_id = len(components)
        components.append(component)
        for node in component:
            component_for[node] = component_id
    for node in adjacency:
        if node not in scc_nodes:
            component_for[node] = len(components)
            components.append([node])

    dag: dict[int, set[int]] = defaultdict(set)
    indegree: Counter[int] = Counter()
    for node, targets in adjacency.items():
        source_component = component_for[node]
        indegree.setdefault(source_component, 0)
        for target in targets:
            target_component = component_for[target]
            if source_component == target_component:
                continue
            if target_component not in dag[source_component]:
                dag[source_component].add(target_component)
                indegree[target_component] += 1

    queue = deque(sorted(component_id for component_id in range(len(components)) if indegree[component_id] == 0))
    depth = {component_id: 0 for component_id in range(len(components))}
    ordered: list[int] = []
    while queue:
        component_id = queue.popleft()
        ordered.append(component_id)
        for target in sorted(dag.get(component_id, [])):
            depth[target] = max(depth[target], depth[component_id] + 1)
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)

    grouped: dict[int, list[int]] = defaultdict(list)
    for component_id in ordered:
        grouped[depth[component_id]].append(component_id)
    return [
        {
            "depth": layer_depth,
            "component_count": len(component_ids),
            "sample_components": [components[component_id][:8] for component_id in component_ids[:10]],
        }
        for layer_depth, component_ids in sorted(grouped.items())
    ]


def centrality(adjacency: dict[str, list[str]]) -> dict[str, list[dict[str, object]]]:
    fan_out = Counter({node: len(targets) for node, targets in adjacency.items()})
    fan_in: Counter[str] = Counter()
    for targets in adjacency.values():
        fan_in.update(targets)
    bridge = Counter({node: fan_in[node] * fan_out[node] for node in adjacency})
    return {
        "fan_in": [{"path": path, "count": count} for path, count in fan_in.most_common(20)],
        "fan_out": [{"path": path, "count": count} for path, count in fan_out.most_common(20) if count],
        "bridge_score": [{"path": path, "score": score} for path, score in bridge.most_common(20) if score],
    }


def directory_hotspots(reports: list[FileReport]) -> list[dict[str, object]]:
    stats: dict[str, dict[str, object]] = defaultdict(lambda: {"files": 0, "lines": 0, "imports": 0, "symbols": 0, "layers": Counter(), "languages": Counter()})
    for report in reports:
        parts = PurePosixPath(report.path).parts[:-1]
        prefixes = ["/".join(parts[:index]) for index in range(1, len(parts) + 1)] or ["."]
        for prefix in prefixes:
            item = stats[prefix]
            item["files"] += 1
            item["lines"] += report.lines
            item["imports"] += len(report.imports)
            item["symbols"] += len(report.symbols)
            item["layers"].update([report.layer])
            item["languages"].update([report.language])
    rows = []
    for path, item in stats.items():
        score = int(item["lines"]) + int(item["imports"]) * 8 + int(item["symbols"]) * 12
        rows.append(
            {
                "path": path,
                "score": score,
                "files": item["files"],
                "lines": item["lines"],
                "imports": item["imports"],
                "symbols": item["symbols"],
                "top_layers": dict(item["layers"].most_common(3)),
                "top_languages": dict(item["languages"].most_common(3)),
            }
        )
    return sorted(rows, key=lambda item: (-int(item["score"]), str(item["path"])))[:30]


def summarize(root: Path, reports: list[FileReport], include_full_files: bool) -> dict[str, object]:
    languages = Counter(report.language for report in reports)
    layers = Counter(report.layer for report in reports)
    parsers = Counter(report.parser for report in reports)
    entries = heapq.nlargest(20, (report for report in reports if report.entry_score), key=lambda r: (r.entry_score, r.path))
    hotspots = heapq.nlargest(20, reports, key=lambda report: (report.score, report.path))
    go_module = read_go_module(root)
    edges = infer_edges(reports, go_module)
    resolved_edges = [edge for edge in edges if edge.status == "resolved" and edge.to_path]
    unresolved_internal = [edge for edge in edges if edge.status == "unresolved_internal"]
    adjacency = build_adjacency((report.path for report in reports), edges)
    sccs = strongly_connected_components(adjacency)
    summary: dict[str, object] = {
        "root": str(root),
        "file_count": len(reports),
        "languages": dict(languages.most_common()),
        "layers": dict(layers.most_common()),
        "parsers": dict(parsers.most_common()),
        "go_module": go_module,
        "entry_candidates": [asdict(report) for report in sorted(entries, key=lambda r: (-r.entry_score, r.path))],
        "hotspots": [asdict(report) for report in sorted(hotspots, key=lambda r: (-r.score, r.path))],
        "dependency_graph": {
            "resolved_edge_count": len(resolved_edges),
            "unresolved_internal_count": len(unresolved_internal),
            "external_import_count": sum(1 for edge in edges if edge.status == "external"),
            "resolved_edges": [asdict(edge) for edge in resolved_edges[:500]],
            "unresolved_internal": [asdict(edge) for edge in unresolved_internal[:100]],
        },
        "architecture_clusters": architecture_clusters(reports, edges),
        "strongly_connected_components": [{"size": len(component), "files": component[:50], "truncated": len(component) > 50} for component in sccs[:30]],
        "dag_layers": dag_layers(adjacency, sccs),
        "centrality": centrality(adjacency),
        "directory_hotspots": directory_hotspots(reports),
        "files_omitted": not include_full_files,
    }
    if include_full_files:
        summary["files"] = [asdict(report) for report in reports]
    else:
        summary["files_sample"] = [asdict(report) for report in reports[:100]]
    return summary


def table(rows: Iterable[Iterable[object]], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(out)


def render_markdown(summary: dict[str, object]) -> str:
    graph = summary["dependency_graph"]
    central = summary["centrality"]
    lines = [
        "# AST 架构分析报告",
        "",
        f"- Target: `{summary['root']}`",
        f"- Files analyzed: `{summary['file_count']}`",
        f"- Parsers: `{json.dumps(summary['parsers'], ensure_ascii=False)}`",
        f"- Resolved dependency edges: `{graph['resolved_edge_count']}`",
        f"- Unresolved internal imports: `{graph['unresolved_internal_count']}`",
        "",
        "## 语言分布",
        "",
        table(((k, v) for k, v in summary["languages"].items()), ["Language", "Files"]),
        "",
        "## 分层信号",
        "",
        table(((k, v) for k, v in summary["layers"].items()), ["Layer", "Files"]),
        "",
        "## 入口候选",
        "",
    ]
    entries = summary["entry_candidates"]
    if entries:
        lines.append(table(((item["path"], item["language"], item["entry_score"], item["layer"]) for item in entries), ["File", "Lang", "Score", "Layer"]))
    else:
        lines.append("- 未识别到高置信入口候选。")

    lines.extend(["", "## 结构热点", ""])
    hotspots = summary["hotspots"]
    if hotspots:
        lines.append(
            table(
                ((item["path"], item["language"], item["layer"], item["lines"], len(item["imports"]), len(item["symbols"])) for item in hotspots[:12]),
                ["File", "Lang", "Layer", "Lines", "Imports", "Symbols"],
            )
        )
    else:
        lines.append("- 未识别到结构热点。")

    lines.extend(["", "## 架构聚类（并查集）", ""])
    clusters = summary["architecture_clusters"]
    if clusters:
        lines.append(table(((item["id"], item["size"], item["layers"], item["entry_candidates"], item["hotspots"][:3]) for item in clusters[:12]), ["Cluster", "Files", "Layers", "Entries", "Hotspots"]))
    else:
        lines.append("- 未识别到多文件架构簇。")

    lines.extend(["", "## 强连通分量（Tarjan SCC）", ""])
    sccs = summary["strongly_connected_components"]
    if sccs:
        lines.append(table(((item["size"], item["files"][:8]) for item in sccs[:12]), ["Size", "Files"]))
    else:
        lines.append("- 未发现多文件循环依赖。")

    lines.extend(["", "## DAG 分层", ""])
    dag_layers_summary = summary["dag_layers"]
    if dag_layers_summary:
        lines.append(table(((item["depth"], item["component_count"], item["sample_components"][:3]) for item in dag_layers_summary[:12]), ["Depth", "Components", "Samples"]))
    else:
        lines.append("- 无可用 DAG 分层。")

    lines.extend(["", "## 中心性", ""])
    lines.append("### Fan-in")
    lines.append(table(((item["path"], item["count"]) for item in central["fan_in"][:12]), ["File", "Incoming"]) if central["fan_in"] else "- 无 fan-in 数据。")
    lines.append("")
    lines.append("### Fan-out")
    lines.append(table(((item["path"], item["count"]) for item in central["fan_out"][:12]), ["File", "Outgoing"]) if central["fan_out"] else "- 无 fan-out 数据。")
    lines.append("")
    lines.append("### Bridge score")
    lines.append(table(((item["path"], item["score"]) for item in central["bridge_score"][:12]), ["File", "Score"]) if central["bridge_score"] else "- 无 bridge score 数据。")

    lines.extend(["", "## 目录热区（Path Trie 聚合）", ""])
    directory_rows = summary["directory_hotspots"]
    if directory_rows:
        lines.append(table(((item["path"], item["score"], item["files"], item["top_layers"]) for item in directory_rows[:12]), ["Directory", "Score", "Files", "Layers"]))
    else:
        lines.append("- 未识别到目录热区。")

    lines.extend(["", "## 依赖边样本", ""])
    resolved_edges = graph["resolved_edges"]
    if resolved_edges:
        lines.append(table(((edge["from_path"], edge["to_path"], edge["imported"]) for edge in resolved_edges[:30]), ["From", "To", "Import"]))
    else:
        lines.append("- 无已解析内部依赖边样本。")

    lines.extend(
        [
            "",
            "## 使用说明",
            "",
            "- `python-ast` 代表通过 Python 标准库 AST 解析得到的结构信号。",
            "- `structural-scan` 代表无外部依赖的轻量结构扫描，适合作为 roadmap 的辅助证据，不等同完整语言 AST。",
            "- 并查集用于聚合弱连接架构簇；Tarjan SCC 用于识别循环依赖；DAG 分层用于辅助判断控制入口到依赖层的方向。",
            "- Roadmap 正文应把本报告作为证据输入之一，并继续读取关键文件确认控制流与功能职责。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(summary: dict[str, object], output_dir: Path, fmt: str) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    outputs: list[Path] = []
    if fmt in {"json", "both"}:
        json_path = output_dir / f"ast-architecture-{stamp}.json"
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs.append(json_path)
    if fmt in {"markdown", "both"}:
        md_path = output_dir / f"ast-architecture-{stamp}.md"
        md_path.write_text(render_markdown(summary), encoding="utf-8")
        outputs.append(md_path)
    return outputs


def default_worker_count() -> int:
    return min(8, max(1, (os.cpu_count() or 2) - 1))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze project architecture with AST, dependency graph, clustering, and centrality signals.")
    parser.add_argument("--target-dir", default=".", help="Project or module directory to analyze.")
    parser.add_argument("--output-dir", help="Output directory. Defaults to <target-dir>/r0/roadmap.")
    parser.add_argument("--format", choices=["json", "markdown", "both"], default="both")
    parser.add_argument("--max-files", type=int, default=2000)
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--workers", type=int, default=1, help="Parallel file parsing workers. Use 0 for auto.")
    parser.add_argument("--full-files", action="store_true", help="Include all per-file reports in JSON output.")
    args = parser.parse_args()

    root = Path(args.target_dir).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"[ERROR] target-dir 不存在或不是目录: {root}")

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else root / "r0" / "roadmap"
    workers = default_worker_count() if args.workers == 0 else max(1, args.workers)
    paths = collect_files(root, args.max_files, args.include_tests)
    reports = analyze_files(paths, root, workers)
    summary = summarize(root, reports, include_full_files=args.full_files)
    outputs = write_outputs(summary, output_dir, args.format)
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
