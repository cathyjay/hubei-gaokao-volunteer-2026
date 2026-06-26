#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from ocr_magazine_pages import sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DPI = 150


def resolve_path(value):
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


def find_binary(name):
    deps_bin = os.environ.get("CODEX_DEPS_BIN")
    if deps_bin:
        bundled = Path(deps_bin).expanduser() / name
        if bundled.exists():
            return str(bundled)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit(f"未找到 {name}，无法处理 PDF。")


def pdf_page_count(pdf_path):
    pdfinfo = find_binary("pdfinfo")
    completed = subprocess.run(
        [pdfinfo, str(pdf_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"pdfinfo 执行失败:\n{completed.stderr}")
    match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.MULTILINE)
    if not match:
        raise SystemExit("无法从 pdfinfo 输出中读取页数。")
    return int(match.group(1)), completed.stdout


def parse_pages(spec, total_pages):
    if not spec:
        return list(range(1, total_pages + 1))
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            start = int(left) if left else 1
            end = int(right) if right else total_pages
            if start > end:
                raise SystemExit(f"页码范围错误: {part}")
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    invalid = [p for p in pages if p < 1 or p > total_pages]
    if invalid:
        raise SystemExit(f"页码超出范围: {invalid[:10]}")
    return sorted(pages)


def render_pages(pdf_path, pages, output_dir, dpi):
    pdftoppm = find_binary("pdftoppm")
    render_dir = output_dir / "rendered-pages"
    render_dir.mkdir(parents=True, exist_ok=True)

    rendered = []
    for page in pages:
        temp_prefix = render_dir / f"_tmp_page_{page:03d}"
        before = set(render_dir.glob(f"{temp_prefix.name}-*.png"))
        command = [
            pdftoppm,
            "-f",
            str(page),
            "-l",
            str(page),
            "-png",
            "-r",
            str(dpi),
            str(pdf_path),
            str(temp_prefix),
        ]
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(f"第 {page} 页渲染失败:\n{completed.stderr}")
        after = set(render_dir.glob(f"{temp_prefix.name}-*.png"))
        generated = sorted(after - before)
        if len(generated) != 1:
            raise SystemExit(f"第 {page} 页渲染输出异常: {generated}")
        target = render_dir / f"page-{page:03d}.png"
        if target.exists():
            target.unlink()
        generated[0].rename(target)
        rendered.append(target)
    return rendered


def run_image_ocr(image_dir, output_dir, languages, fast):
    command = [
        sys.executable,
        str(ROOT / "scripts/ocr_magazine_pages.py"),
        "--input",
        str(image_dir),
        "--output-dir",
        str(output_dir),
        "--languages",
        languages,
    ]
    if fast:
        command.append("--fast")
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "图片 OCR 执行失败。\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    print(completed.stdout.strip())


def write_pdf_manifest(pdf_path, output_dir, total_pages, pdfinfo_text, selected_pages, rendered_pages, dpi, languages):
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_pdf": {
            "path": str(pdf_path),
            "file_name": pdf_path.name,
            "sha256": sha256(pdf_path),
            "size_bytes": pdf_path.stat().st_size,
            "total_pages": total_pages,
        },
        "render": {
            "dpi": dpi,
            "selected_pages": selected_pages,
            "rendered_image_count": len(rendered_pages),
            "rendered_dir": str((output_dir / "rendered-pages").relative_to(output_dir)),
            "rendered_images": [
                {
                    "page": page,
                    "path": str(path.relative_to(output_dir)),
                    "sha256": sha256(path),
                    "size_bytes": path.stat().st_size,
                }
                for page, path in zip(selected_pages, rendered_pages)
            ],
        },
        "ocr": {
            "engine": "apple_vision",
            "languages": languages.split(","),
            "outputs": {
                "jsonl": "ocr.jsonl",
                "manifest_csv": "manifest.csv",
                "suspected_plan_lines_csv": "suspected_plan_lines.csv",
                "manual_review_template_csv": "manual_review_template.csv",
                "text_dir": "text",
            },
        },
        "pdfinfo": pdfinfo_text,
    }
    (output_dir / "pdf_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="渲染 PDF 页并调用图片 OCR 工作流。")
    parser.add_argument("--pdf", required=True, help="PDF 路径。")
    parser.add_argument("--pages", help="页码，如 1-5,10,20-；不填则处理全 PDF。")
    parser.add_argument("--output-dir", help="输出目录，默认 private/ocr-runs/pdf-<时间戳>。")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI, help=f"渲染 DPI，默认 {DEFAULT_DPI}。")
    parser.add_argument("--languages", default="zh-Hans,en-US", help="OCR 语言，默认 zh-Hans,en-US。")
    parser.add_argument("--fast", action="store_true", help="使用较快但可能较低精度的 OCR 模式。")
    args = parser.parse_args()

    pdf_path = resolve_path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF 不存在: {pdf_path}")

    if args.output_dir:
        output_dir = resolve_path(args.output_dir)
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = ROOT / "private" / "ocr-runs" / f"pdf-{stamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_pages, pdfinfo_text = pdf_page_count(pdf_path)
    selected_pages = parse_pages(args.pages, total_pages)
    rendered_pages = render_pages(pdf_path, selected_pages, output_dir, args.dpi)
    run_image_ocr(output_dir / "rendered-pages", output_dir, args.languages, args.fast)
    write_pdf_manifest(
        pdf_path=pdf_path,
        output_dir=output_dir,
        total_pages=total_pages,
        pdfinfo_text=pdfinfo_text,
        selected_pages=selected_pages,
        rendered_pages=rendered_pages,
        dpi=args.dpi,
        languages=args.languages,
    )
    print(f"PDF OCR 输出目录：{output_dir}")


if __name__ == "__main__":
    main()
