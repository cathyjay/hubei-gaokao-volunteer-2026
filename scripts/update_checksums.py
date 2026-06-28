#!/usr/bin/env python3
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "candidate-screenshots",
    "private",
    "scratch",
    "tmp",
    "user-provided",
}
EXCLUDED_SUFFIXES = {".pyc"}
EXCLUDED_FILENAMES = {".DS_Store"}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def public_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel.as_posix() == "CHECKSUMS.sha256":
            continue
        if path.name in EXCLUDED_FILENAMES:
            continue
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        yield rel.as_posix(), path


def main():
    lines = []
    for rel, path in sorted(public_files()):
        lines.append(f"{sha256(path)}  {rel}")
    (ROOT / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"更新 CHECKSUMS.sha256：{len(lines)} 个公开文件")


if __name__ == "__main__":
    main()
