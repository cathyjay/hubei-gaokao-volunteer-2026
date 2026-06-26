#!/usr/bin/env python3
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = ROOT / "data/external/issue19-b0-b1-official-sources/xztu-2026-province-major-plan.pdf"
OUTPUT_CSV = ROOT / "data/external/issue19-b0-b1-official-sources/xztu-2026-hubei-physics-plan-extracted.csv"

FIELDS = [
    "学校名称",
    "原始PDF",
    "页码",
    "系",
    "专业名称",
    "科类",
    "校区",
    "学制",
    "学费",
    "湖北计划数",
    "提取方法",
    "提取局限性",
]


def as_int(value):
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def clean_header(value):
    return str(value or "").replace("\n", "").strip()


def clean_cell(value):
    return " ".join(str(value or "").split())


def main():
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise SystemExit("缺少 pdfplumber；请使用 Codex bundled Python 或安装 pdfplumber 后重跑。") from exc

    rows = []
    with pdfplumber.open(SOURCE_PDF) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables() or []:
                if not table:
                    continue
                header = [clean_header(cell) for cell in table[0]]
                if "专业" not in header or "湖北" not in header:
                    continue
                index_by_name = {name: index for index, name in enumerate(header) if name}
                for raw in table[1:]:
                    subject = clean_cell(raw[index_by_name["科类"]])
                    plan = as_int(raw[index_by_name["湖北"]])
                    major = clean_cell(raw[index_by_name["专业"]])
                    if subject != "物理" or not major or plan is None:
                        continue
                    if "合计" in major or major.startswith("★"):
                        continue
                    rows.append(
                        {
                            "学校名称": "忻州师范学院",
                            "原始PDF": str(SOURCE_PDF.relative_to(ROOT)),
                            "页码": str(page_index),
                            "系": clean_cell(raw[index_by_name["系"]]),
                            "专业名称": major,
                            "科类": subject,
                            "校区": clean_cell(raw[index_by_name["地址"]]),
                            "学制": clean_cell(raw[index_by_name["学制"]]),
                            "学费": clean_cell(raw[index_by_name["学费"]]),
                            "湖北计划数": str(plan),
                            "提取方法": "pdfplumber_extract_tables_header_hubei_column",
                            "提取局限性": "由高校官网PDF宽表抽取湖北列；未给湖北院校专业组代码和专业代号，需与第19期原页及湖北官方系统对齐。",
                        }
                    )

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"写出忻州师范学院湖北物理类PDF抽取表：{OUTPUT_CSV}")
    print(f"抽取行数：{len(rows)}")


if __name__ == "__main__":
    main()
