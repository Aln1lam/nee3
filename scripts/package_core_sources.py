#!/usr/bin/env python3
"""Package core source files into a standalone output folder.

The script walks the repository root, keeps only selected source files,
copies them into an output folder, and generates a structured merged text
representation plus a manifest and zip archive.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


IGNORED_DIR_NAMES = {
    "node_modules",
    "dist",
    "venv",
    ".venv",
    ".git",
    "pycache",
    "__pycache__",
    ".vscode",
}

ALLOWED_SUFFIXES = {".py", ".vue", ".js", ".ts"}
ALLOWED_FILENAMES = {"requirements.txt", "package.json"}
GENERATED_BUNDLE_PREFIX = "core_source_bundle_"


def should_keep_file(path: Path) -> bool:
    name = path.name.lower()
    return path.suffix.lower() in ALLOWED_SUFFIXES or name in ALLOWED_FILENAMES


def should_skip_dir(path: Path, output_dir: Path) -> bool:
    if path == output_dir:
        return True
    if output_dir in path.parents:
        return True
    return path.name.lower() in IGNORED_DIR_NAMES


def collect_files(root: Path, output_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part.lower() in IGNORED_DIR_NAMES for part in path.parts):
            continue
        if any(part.lower().startswith(GENERATED_BUNDLE_PREFIX) for part in path.parts):
            continue
        if output_dir in path.parents:
            continue
        if should_keep_file(path):
            files.append(path)
    return sorted(files, key=lambda p: p.as_posix().lower())


def build_merged_text(root: Path, files: list[Path]) -> str:
    timestamp = datetime.now().isoformat(timespec="seconds")
    lines = [
        "# Core Source Bundle",
        "",
        f"Generated: {timestamp}",
        f"Root: {root}",
        f"Files: {len(files)}",
        "",
    ]

    for file_path in files:
        relative_path = file_path.relative_to(root).as_posix()
        lines.extend(
            [
                f"## {relative_path}",
                "```text",
                file_path.read_text(encoding="utf-8", errors="replace"),
                "```",
                "",
            ]
        )

    return "\n".join(lines)


def copy_files(root: Path, output_sources_dir: Path, files: list[Path]) -> None:
    for file_path in files:
        relative_path = file_path.relative_to(root)
        destination = output_sources_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Package core source files into a folder")
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory. Defaults to archives/core_source_bundle_<timestamp>",
    )
    args = parser.parse_args()

    script_root = Path(__file__).resolve().parent.parent
    root = Path(args.root).resolve() if args.root else script_root

    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = root / "archives" / f"core_source_bundle_{timestamp}"

    output_sources_dir = output_dir / "sources"
    output_dir.mkdir(parents=True, exist_ok=False)
    output_sources_dir.mkdir(parents=True, exist_ok=True)

    files = collect_files(root, output_dir)
    copy_files(root, output_sources_dir, files)

    merged_text = build_merged_text(root, files)
    (output_dir / "merged_sources.txt").write_text(merged_text, encoding="utf-8")

    manifest = {
        "root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "file_count": len(files),
        "files": [
            {
                "path": file_path.relative_to(root).as_posix(),
                "size_bytes": file_path.stat().st_size,
            }
            for file_path in files
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    zip_base = output_dir / "core_source_bundle"
    shutil.make_archive(str(zip_base), "zip", root_dir=output_dir)

    summary = {
        "output_dir": str(output_dir),
        "zip_path": str(zip_base.with_suffix(".zip")),
        "file_count": len(files),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())