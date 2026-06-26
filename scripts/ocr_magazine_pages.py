#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff"}
DEFAULT_LANGUAGES = "zh-Hans,en-US"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def natural_key(path):
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def collect_images(inputs):
    images = []
    for item in inputs:
        path = Path(item).expanduser()
        if not path.is_absolute():
            path = (ROOT / path).resolve()
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES:
                    images.append(child)
        elif path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            images.append(path)
        else:
            raise SystemExit(f"不是可识别的图片文件或目录: {path}")
    return sorted(dict.fromkeys(images), key=natural_key)


def run_vision_ocr(images, languages, fast):
    swift = shutil.which("swift")
    if not swift:
        raise SystemExit("未找到 swift，无法调用 macOS Vision OCR。")

    command = [swift, str(ROOT / "scripts/vision_ocr.swift"), "--languages", languages]
    if fast:
        command.append("--fast")
    command.extend(str(path) for path in images)

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
            "Vision OCR 执行失败。\n"
            f"command: {' '.join(command)}\n"
            f"stderr:\n{completed.stderr}"
        )

    results = []
    for line in completed.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        results.append(json.loads(line))
    return results


def safe_stem(path, index):
    stem = re.sub(r"[^0-9A-Za-z._-]+", "_", path.stem).strip("._-")
    return f"{index:03d}_{stem or 'page'}"


def line_reason(text):
    reasons = []
    if re.search(r"[A-Z]\d{4}\d{2}", text):
        reasons.append("疑似院校专业组")
    for keyword in ["院校专业组", "专业代号", "专业名称", "首选物理", "再选", "招生计划", "计划数", "学费", "备注"]:
        if keyword in text:
            reasons.append(keyword)
    if re.match(r"^\s*\d{1,3}\s+[\u4e00-\u9fffA-Za-z]", text):
        reasons.append("疑似专业行")
    return "、".join(dict.fromkeys(reasons))


def write_outputs(images, results, output_dir, languages):
    output_dir.mkdir(parents=True, exist_ok=True)
    text_dir = output_dir / "text"
    text_dir.mkdir(exist_ok=True)

    result_by_image = {Path(item["image"]).resolve(): item for item in results}
    jsonl_path = output_dir / "ocr.jsonl"
    manifest_path = output_dir / "manifest.csv"
    suspected_path = output_dir / "suspected_plan_lines.csv"
    template_path = output_dir / "manual_review_template.csv"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")

    manifest_fields = [
        "序号",
        "源图片",
        "SHA256",
        "大小字节",
        "OCR引擎",
        "识别语言",
        "识别行数",
        "平均置信度",
        "文本文件",
        "错误",
    ]
    suspected_fields = ["序号", "源图片", "行号", "OCR文本", "触发原因", "置信度"]
    template_fields = [
        "源图片",
        "页码",
        "院校代码",
        "院校名称",
        "院校专业组",
        "首选科目",
        "再选科目",
        "专业代号",
        "专业名称",
        "计划数",
        "学费",
        "备注",
        "OCR行号",
        "已人工核验",
        "核验说明",
    ]

    with manifest_path.open("w", newline="", encoding="utf-8-sig") as manifest_file, \
            suspected_path.open("w", newline="", encoding="utf-8-sig") as suspected_file, \
            template_path.open("w", newline="", encoding="utf-8-sig") as template_file:
        manifest_writer = csv.DictWriter(manifest_file, fieldnames=manifest_fields)
        suspected_writer = csv.DictWriter(suspected_file, fieldnames=suspected_fields)
        template_writer = csv.DictWriter(template_file, fieldnames=template_fields)
        manifest_writer.writeheader()
        suspected_writer.writeheader()
        template_writer.writeheader()

        for index, image in enumerate(images, start=1):
            resolved = image.resolve()
            result = result_by_image.get(resolved) or result_by_image.get(Path(str(image)).resolve())
            if not result:
                result = {
                    "engine": "apple_vision",
                    "languages": languages.split(","),
                    "lineCount": 0,
                    "averageConfidence": None,
                    "text": "",
                    "lines": [],
                    "error": "OCR result missing",
                }
            stem = safe_stem(image, index)
            text_path = text_dir / f"{stem}.txt"
            text_path.write_text(result.get("text", ""), encoding="utf-8")
            manifest_writer.writerow({
                "序号": index,
                "源图片": str(image),
                "SHA256": sha256(image),
                "大小字节": image.stat().st_size,
                "OCR引擎": result.get("engine", "apple_vision"),
                "识别语言": ",".join(result.get("languages") or languages.split(",")),
                "识别行数": result.get("lineCount", 0),
                "平均置信度": "" if result.get("averageConfidence") is None else f"{result['averageConfidence']:.4f}",
                "文本文件": str(text_path.relative_to(output_dir)),
                "错误": result.get("error") or "",
            })

            for line_index, line in enumerate(result.get("lines", []), start=1):
                text = line.get("text", "")
                reason = line_reason(text)
                if reason:
                    suspected_writer.writerow({
                        "序号": index,
                        "源图片": str(image),
                        "行号": line_index,
                        "OCR文本": text,
                        "触发原因": reason,
                        "置信度": f"{line.get('confidence', 0):.4f}",
                    })
                    template_writer.writerow({
                        "源图片": str(image),
                        "页码": "",
                        "院校代码": "",
                        "院校名称": "",
                        "院校专业组": "",
                        "首选科目": "",
                        "再选科目": "",
                        "专业代号": "",
                        "专业名称": "",
                        "计划数": "",
                        "学费": "",
                        "备注": "",
                        "OCR行号": line_index,
                        "已人工核验": "否",
                        "核验说明": text,
                    })

    readme = output_dir / "README.md"
    readme.write_text(
        "\n".join([
            "# OCR 运行输出",
            "",
            f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
            f"- 图片数量：{len(images)}",
            f"- 识别语言：{languages}",
            "- `ocr.jsonl`：逐页完整 OCR 结果。",
            "- `text/`：逐页纯文本，方便人工搜索。",
            "- `manifest.csv`：源图片、哈希、识别行数和置信度。",
            "- `suspected_plan_lines.csv`：疑似院校专业组、专业代号、计划数等行。",
            "- `manual_review_template.csv`：人工复核和结构化录入模板。",
            "",
            "注意：OCR 结果只能作为派生数据，最终志愿必须回看照片原件和官方系统逐项核验。",
        ]),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="批量 OCR 识别《湖北招生考试》图片页。")
    parser.add_argument("--input", nargs="+", required=True, help="图片文件或目录，可传多个。")
    parser.add_argument("--output-dir", help="输出目录，默认写入 private/ocr-runs/<时间戳>。")
    parser.add_argument("--languages", default=DEFAULT_LANGUAGES, help="Vision 识别语言，默认 zh-Hans,en-US。")
    parser.add_argument("--fast", action="store_true", help="使用较快但可能较低精度的识别模式。")
    args = parser.parse_args()

    images = collect_images(args.input)
    if not images:
        raise SystemExit("没有找到可识别的图片。")

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser()
        if not output_dir.is_absolute():
            output_dir = (ROOT / output_dir).resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = ROOT / "private" / "ocr-runs" / stamp

    results = run_vision_ocr(images, args.languages, args.fast)
    write_outputs(images, results, output_dir, args.languages)
    print(f"OCR 完成：{len(images)} 张图片")
    print(f"输出目录：{output_dir}")


if __name__ == "__main__":
    main()
