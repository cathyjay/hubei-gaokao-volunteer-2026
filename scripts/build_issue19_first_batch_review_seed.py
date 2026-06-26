#!/usr/bin/env python3
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OCR_SAMPLE = ROOT / "private/derived/issue19-sample-school-ocr/样本学校OCR定位.csv"
DEFAULT_SUMMARY = ROOT / "data/working/issue19-first-batch-review-seed-summary.json"
DEFAULT_PRIVATE_OUTPUT = ROOT / "private/derived/issue19-first-batch-structure-trial/逐组复核种子.csv"

FIRST_BATCH_SCHOOLS = [
    "武汉科技大学",
    "湖北大学",
    "湖北理工学院",
    "武汉商学院",
]


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def is_group_title_candidate(row):
    text = row.get("OCR文本", "")
    return row.get("命中行号") == row.get("上下文行号") and "第" in text and "组" in text


def context_text(rows, page, line_no, window=2):
    selected = []
    for row in rows:
        if row.get("OCR页码") != page:
            continue
        current = int(row["上下文行号"])
        if abs(current - line_no) <= window:
            selected.append(f"{row['上下文行号']}:{row['OCR文本']}")
    return " | ".join(selected)


def main():
    rows = read_rows(DEFAULT_OCR_SAMPLE)
    private_rows = []
    summary = {
        "status": "review_seed_only_not_final",
        "private_output": str(DEFAULT_PRIVATE_OUTPUT.relative_to(ROOT)),
        "source": str(DEFAULT_OCR_SAMPLE.relative_to(ROOT)),
        "schools": [],
        "notes": [
            "该摘要不含 OCR 原文；OCR 原文只保存在 private 逐组复核种子表。",
            "逐组复核种子只用于人工回看第19期原 PDF 页，不可直接作为最终招生计划。",
        ],
    }

    fields = [
        "学校名称",
        "PDF OCR页码",
        "左右栏",
        "OCR命中行号",
        "OCR专业组标题原文",
        "OCR置信度",
        "OCR邻近上下文",
        "人工核验状态",
        "院校代码_人工确认",
        "院校专业组代码_人工确认",
        "专业组边界_人工确认",
        "组内全部专业数_人工确认",
        "官网交叉核验状态",
        "备注",
    ]

    for school in FIRST_BATCH_SCHOOLS:
        school_rows = [
            row for row in rows
            if row.get("学校名称") == school and row.get("OCR页码")
        ]
        candidates = [row for row in school_rows if is_group_title_candidate(row)]
        seen = set()
        output_candidates = []
        for row in candidates:
            key = (row["OCR页码"], row["上下文行号"], row["OCR文本"])
            if key in seen:
                continue
            seen.add(key)
            line_no = int(row["上下文行号"])
            output_candidates.append(row)
            private_rows.append({
                "学校名称": school,
                "PDF OCR页码": row["OCR页码"],
                "左右栏": row["左右栏"],
                "OCR命中行号": row["命中行号"],
                "OCR专业组标题原文": row["OCR文本"],
                "OCR置信度": row["OCR置信度"],
                "OCR邻近上下文": context_text(school_rows, row["OCR页码"], line_no),
                "人工核验状态": "待回看第19期原PDF页",
                "院校代码_人工确认": "",
                "院校专业组代码_人工确认": "",
                "专业组边界_人工确认": "",
                "组内全部专业数_人工确认": "",
                "官网交叉核验状态": "待核",
                "备注": "",
            })

        summary["schools"].append({
            "学校名称": school,
            "PDF OCR页码": sorted({int(row["OCR页码"]) for row in school_rows}),
            "专业组标题候选数": len(output_candidates),
            "状态": "待人工逐组复核",
        })

    DEFAULT_PRIVATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with DEFAULT_PRIVATE_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(private_rows)

    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出私有逐组复核种子：{DEFAULT_PRIVATE_OUTPUT}")
    print(f"写出公开摘要：{DEFAULT_SUMMARY}")
    print(f"学校数：{len(FIRST_BATCH_SCHOOLS)}")
    print(f"复核候选行数：{len(private_rows)}")


if __name__ == "__main__":
    main()
