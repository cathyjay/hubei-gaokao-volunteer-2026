#!/usr/bin/env python3
import argparse
import csv
import json
import re
from pathlib import Path


def page_from_image(image_path):
    match = re.search(r"page-(\d+)\.png$", image_path)
    return int(match.group(1)) if match else ""


def table_band(x):
    if 0.06 <= x < 0.50:
        return "left"
    if 0.50 <= x <= 0.94:
        return "right"
    return "outside"


def line_type(text):
    if re.match(r"^[A-Z][0-9OIl]{3}\s*.+", text):
        return "school"
    if re.match(r"^[A-Z][0-9OIl]{3}[0-9OIl]{2}", text):
        return "major_group"
    if re.match(r"^\s*\d{1,3}[\s/、]?\S+", text):
        return "major_or_numbered_line"
    if "院校专业组" in text:
        return "table_header"
    if "本科普通批" in text or "招生计划" in text:
        return "page_header"
    return "text"


def main():
    parser = argparse.ArgumentParser(description="把 Vision OCR JSONL 展平成带坐标的行级 CSV。")
    parser.add_argument("--jsonl", required=True, help="OCR JSONL 路径。")
    parser.add_argument("--output", required=True, help="输出 CSV 路径。")
    args = parser.parse_args()

    jsonl_path = Path(args.jsonl).expanduser()
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "page",
        "image",
        "line_no",
        "text",
        "confidence",
        "x",
        "y",
        "width",
        "height",
        "table_band",
        "line_type",
    ]

    with jsonl_path.open(encoding="utf-8") as source, output_path.open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for raw in source:
            if not raw.strip():
                continue
            page_result = json.loads(raw)
            image = page_result.get("image", "")
            page = page_from_image(image)
            for index, line in enumerate(page_result.get("lines", []), start=1):
                box = line.get("boundingBox") or {}
                x = float(box.get("x", 0))
                text = line.get("text", "")
                writer.writerow({
                    "page": page,
                    "image": image,
                    "line_no": index,
                    "text": text,
                    "confidence": f"{float(line.get('confidence', 0)):.4f}",
                    "x": f"{x:.6f}",
                    "y": f"{float(box.get('y', 0)):.6f}",
                    "width": f"{float(box.get('width', 0)):.6f}",
                    "height": f"{float(box.get('height', 0)):.6f}",
                    "table_band": table_band(x),
                    "line_type": line_type(text),
                })

    print(f"写出行级 OCR CSV：{output_path}")


if __name__ == "__main__":
    main()
