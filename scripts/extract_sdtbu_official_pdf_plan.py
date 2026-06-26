#!/usr/bin/env python3
import csv
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = ROOT / "data/external/issue19-b0-b1-official-sources/sdtbu-2026-province-major-plan.pdf"
OUTPUT_CSV = ROOT / "data/external/issue19-b0-b1-official-sources/sdtbu-2026-hubei-physics-plan-extracted.csv"
AUDIT_CSV = ROOT / "data/external/issue19-b0-b1-official-sources/sdtbu-2026-pdf-ocr-grid-audit.csv"
TMP_DIR = ROOT / "tmp/pdfs/sdtbu-official-extract"

HUBEI_COLUMN_INDEX = 13
PAGE_NUMBER = 1

FIELDS = [
    "学校名称",
    "原始PDF",
    "页码",
    "PDF表格行号",
    "系",
    "专业名称",
    "专业名称OCR",
    "专业OCR置信度",
    "专业名称校正说明",
    "科类",
    "科类OCR",
    "科类OCR置信度",
    "校区",
    "学制",
    "学费",
    "总计划数",
    "湖北计划数",
    "湖北列索引",
    "提取方法",
    "提取局限性",
]

AUDIT_FIELDS = [
    "学校名称",
    "原始PDF",
    "页码",
    "PDF表格行号",
    "招生学院OCR",
    "专业名称OCR",
    "专业名称",
    "专业OCR置信度",
    "专业名称校正说明",
    "科类OCR",
    "科类",
    "科类OCR置信度",
    "总计划数",
    "湖北计划数",
    "湖北列索引",
    "PDF行上边界",
    "PDF行下边界",
    "纳入湖北物理类匹配表",
    "提取方法",
    "抽取说明",
]

MAJOR_CORRECTIONS = {
    "信息箵理与信息系统": ("信息管理与信息系统", "Apple Vision 将“管理”误识为“箵理”；已按PDF裁图人工复核校正。"),
    "信用风城管理与法佳力吃": ("信用风险管理与法律防控", "Apple Vision 对小字误识；已按PDF裁图人工复核校正。"),
}

SUBJECT_CORRECTIONS_BY_MAJOR = {
    "工程管理": ("物理", "Apple Vision 漏识该行科类；已按PDF裁图人工复核为理工类。"),
}

EXTRACTION_METHOD = "pdf_grid_numbers_plus_apple_vision_ocr_major_column"
LIMITATION = (
    "由高校官网PDF渲染图识别专业名列，并用PDF表格网格抽取湖北列计划数；"
    "未给湖北院校专业组代码、专业代号、学费、学制和校区，需与第19期原页及湖北官方系统对齐。"
)


def find_binary(name):
    deps_bin = os.environ.get("CODEX_DEPS_BIN")
    if deps_bin:
        bundled = Path(deps_bin).expanduser() / name
        if bundled.exists():
            return str(bundled)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit(f"未找到 {name}。")


def as_int(value):
    text = str(value or "").strip()
    return int(text) if re.fullmatch(r"\d+", text) else None


def clean_text(value):
    return " ".join(str(value or "").split())


def text_in_bbox(chars, bbox):
    if not bbox:
        return ""
    x0, top, x1, bottom = bbox
    picked = []
    for char in chars:
        cx = (char["x0"] + char["x1"]) / 2
        cy = (char["top"] + char["bottom"]) / 2
        if x0 <= cx <= x1 and top <= cy <= bottom:
            picked.append(char)
    picked.sort(key=lambda item: (round(item["top"], 1), item["x0"]))
    return "".join(item["text"] for item in picked).strip()


def render_pdf_page():
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    pdftoppm = find_binary("pdftoppm")
    output_prefix = TMP_DIR / "page"
    image_path = TMP_DIR / "page-1.png"
    if image_path.exists():
        image_path.unlink()
    completed = subprocess.run(
        [
            pdftoppm,
            "-f",
            "1",
            "-l",
            "1",
            "-png",
            "-r",
            "300",
            str(SOURCE_PDF),
            str(output_prefix),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"PDF渲染失败:\n{completed.stderr}")
    if not image_path.exists():
        raise SystemExit(f"PDF渲染未生成预期图片: {image_path}")
    return image_path


def run_vision_ocr(image_path):
    swift = shutil.which("swift")
    if not swift:
        raise SystemExit("未找到 swift，无法调用 macOS Vision OCR。")
    completed = subprocess.run(
        [
            swift,
            str(ROOT / "scripts/vision_ocr.swift"),
            "--languages",
            "zh-Hans,en-US",
            str(image_path),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Vision OCR失败:\n{completed.stderr}")
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise SystemExit(f"Vision OCR输出异常，JSON行数={len(lines)}")
    return json.loads(lines[0])


def row_bounds_from_table(table):
    bounds = []
    for row_index, row in enumerate(table.rows):
        cell = None
        for column_index in [1, 2, 3, HUBEI_COLUMN_INDEX, 4]:
            if column_index < len(row.cells) and row.cells[column_index]:
                cell = row.cells[column_index]
                break
        if cell:
            bounds.append((row_index, cell[1], cell[3]))
    return bounds


def row_for_y(row_bounds, y):
    candidates = [
        (row_index, top, bottom, bottom - top)
        for row_index, top, bottom in row_bounds
        if top - 0.6 <= y <= bottom + 0.6
    ]
    if candidates:
        row_index, top, bottom, _ = min(candidates, key=lambda item: item[3])
        return row_index, top, bottom
    row_index, top, bottom = min(row_bounds, key=lambda item: abs(((item[1] + item[2]) / 2) - y))
    return row_index, top, bottom


def ocr_center(line, page_width, page_height):
    box = line["boundingBox"]
    x = (box["x"] + box["width"] / 2) * page_width
    y = (1 - (box["y"] + box["height"] / 2)) * page_height
    return x, y


def subject_from_ocr(major, value):
    text = clean_text(value)
    if "理工" in text:
        return "物理", ""
    if "文史" in text:
        return "历史", ""
    if major in SUBJECT_CORRECTIONS_BY_MAJOR:
        return SUBJECT_CORRECTIONS_BY_MAJOR[major]
    return "", ""


def extract_rows(pdfplumber, ocr_result):
    rows = []
    audit_rows = []
    with pdfplumber.open(SOURCE_PDF) as pdf:
        page = pdf.pages[0]
        table = page.find_tables()[0]
        row_bounds = row_bounds_from_table(table)
        page_width = page.width
        page_height = page.height
        by_row = {}

        for line in ocr_result["lines"]:
            text = clean_text(line.get("text", ""))
            if not text:
                continue
            x, y = ocr_center(line, page_width, page_height)
            row_index, _, _ = row_for_y(row_bounds, y)
            entry = {
                "x": x,
                "y": y,
                "confidence": line.get("confidence", 0),
                "text": text,
            }
            if 30 <= x <= 58:
                by_row.setdefault(row_index, {}).setdefault("college", []).append(entry)
            elif 58 < x <= 124:
                by_row.setdefault(row_index, {}).setdefault("major", []).append(entry)
            elif 124 < x <= 150:
                by_row.setdefault(row_index, {}).setdefault("subject", []).append(entry)

        bounds_by_row = {row_index: (top, bottom) for row_index, top, bottom in row_bounds}
        for row_index in range(4, len(table.rows)):
            values = by_row.get(row_index, {})
            major_candidates = [
                entry
                for entry in values.get("major", [])
                if not any(token in entry["text"] for token in ["专业", "本科中外", "招生学院"])
                and not re.fullmatch(r"[\d\s]+", entry["text"])
            ]
            if not major_candidates:
                continue
            major_entry = max(major_candidates, key=lambda item: (len(item["text"]), item["confidence"]))
            major_ocr = major_entry["text"]
            major, correction_note = MAJOR_CORRECTIONS.get(major_ocr, (major_ocr, ""))

            subject_candidates = [
                entry
                for entry in values.get("subject", [])
                if any(token in entry["text"] for token in ["理工", "文史", "科类", "春季"])
            ]
            subject_entry = max(subject_candidates, key=lambda item: item["confidence"]) if subject_candidates else None
            subject_ocr = subject_entry["text"] if subject_entry else ""
            subject, subject_note = subject_from_ocr(major, subject_ocr)
            subject_confidence = subject_entry["confidence"] if subject_entry else ""

            hubei_plan = text_in_bbox(page.chars, table.rows[row_index].cells[HUBEI_COLUMN_INDEX])
            total_plan = text_in_bbox(page.chars, table.rows[row_index].cells[3])
            if as_int(hubei_plan) is None:
                continue

            college_ocr = clean_text("".join(entry["text"] for entry in sorted(values.get("college", []), key=lambda item: item["y"])))
            top, bottom = bounds_by_row.get(row_index, ("", ""))
            include_physics = subject == "物理"
            extraction_note = "；".join(part for part in [correction_note, subject_note] if part)
            audit_row = {
                "学校名称": "山东工商学院",
                "原始PDF": str(SOURCE_PDF.relative_to(ROOT)),
                "页码": str(PAGE_NUMBER),
                "PDF表格行号": str(row_index),
                "招生学院OCR": college_ocr,
                "专业名称OCR": major_ocr,
                "专业名称": major,
                "专业OCR置信度": f"{major_entry['confidence']:.3f}",
                "专业名称校正说明": correction_note,
                "科类OCR": subject_ocr,
                "科类": subject,
                "科类OCR置信度": f"{subject_confidence:.3f}" if subject_confidence != "" else "",
                "总计划数": total_plan,
                "湖北计划数": hubei_plan,
                "湖北列索引": str(HUBEI_COLUMN_INDEX),
                "PDF行上边界": f"{top:.3f}" if top != "" else "",
                "PDF行下边界": f"{bottom:.3f}" if bottom != "" else "",
                "纳入湖北物理类匹配表": "是" if include_physics else "否",
                "提取方法": EXTRACTION_METHOD,
                "抽取说明": extraction_note,
            }
            audit_rows.append(audit_row)
            if include_physics:
                rows.append(
                    {
                        "学校名称": "山东工商学院",
                        "原始PDF": str(SOURCE_PDF.relative_to(ROOT)),
                        "页码": str(PAGE_NUMBER),
                        "PDF表格行号": str(row_index),
                        "系": college_ocr,
                        "专业名称": major,
                        "专业名称OCR": major_ocr,
                        "专业OCR置信度": f"{major_entry['confidence']:.3f}",
                        "专业名称校正说明": correction_note,
                        "科类": "物理",
                        "科类OCR": subject_ocr,
                        "科类OCR置信度": f"{subject_confidence:.3f}" if subject_confidence != "" else "",
                        "校区": "",
                        "学制": "",
                        "学费": "",
                        "总计划数": total_plan,
                        "湖北计划数": hubei_plan,
                        "湖北列索引": str(HUBEI_COLUMN_INDEX),
                        "提取方法": EXTRACTION_METHOD,
                        "提取局限性": LIMITATION,
                    }
                )
    return rows, audit_rows


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise SystemExit("缺少 pdfplumber；请使用 Codex bundled Python 或安装 pdfplumber 后重跑。") from exc

    image_path = render_pdf_page()
    ocr_result = run_vision_ocr(image_path)
    rows, audit_rows = extract_rows(pdfplumber, ocr_result)
    write_csv(OUTPUT_CSV, FIELDS, rows)
    write_csv(AUDIT_CSV, AUDIT_FIELDS, audit_rows)
    print(f"写出山东工商学院湖北物理类PDF抽取表：{OUTPUT_CSV}")
    print(f"湖北物理类抽取行数：{len(rows)}")
    print(f"写出山东工商学院PDF网格OCR审计表：{AUDIT_CSV}")
    print(f"审计行数：{len(audit_rows)}")


if __name__ == "__main__":
    main()
