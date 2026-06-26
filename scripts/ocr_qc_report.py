#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path


RISK_KEYWORDS = [
    "中外合作",
    "高收费",
    "色盲",
    "色弱",
    "不予录取",
    "单科",
    "英语",
    "外语",
    "口试",
    "校区",
    "定向",
    "专项",
    "预科",
    "民族班",
    "师范",
    "免费",
]


def severity_for(row):
    text = row["text"]
    confidence = float(row["confidence"])
    issues = []
    severity = "P2"

    if confidence < 0.5:
        issues.append("低置信度")
        severity = "P0"
    elif confidence < 0.85:
        issues.append("中置信度")
        severity = "P1"

    if re.search(r"[A-Z][0-9OIl]{3}[0-9OIl]{2}", text):
        issues.append("疑似院校专业组代码")
        severity = "P0"
    elif re.search(r"[A-Z][0-9OIl]{3}", text):
        issues.append("疑似院校代码")
        severity = min_severity(severity, "P1")

    if any(keyword in text for keyword in RISK_KEYWORDS):
        issues.append("含关键备注风险词")
        severity = "P0"

    if row["line_type"] == "major_or_numbered_line" and confidence < 0.85:
        issues.append("疑似专业行需回看")
        severity = min_severity(severity, "P1")

    if re.search(r"\b[1-9]\d{4,5}\b|万", text) and ("学费" not in text):
        issues.append("疑似学费/大额数字")
        severity = min_severity(severity, "P1")

    return severity, issues


def min_severity(current, candidate):
    order = {"P0": 0, "P1": 1, "P2": 2}
    return current if order[current] <= order[candidate] else candidate


def main():
    parser = argparse.ArgumentParser(description="从 OCR 行级 CSV 生成质量问题清单。")
    parser.add_argument("--lines", required=True, help="ocr_jsonl_to_line_csv.py 生成的行级 CSV。")
    parser.add_argument("--output", required=True, help="输出 QC CSV。")
    args = parser.parse_args()

    lines_path = Path(args.lines).expanduser()
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "severity",
        "page",
        "line_no",
        "table_band",
        "line_type",
        "field",
        "ocr_text",
        "confidence",
        "bbox",
        "rule_id",
        "issue",
        "status",
        "reviewer",
        "note",
    ]

    with lines_path.open(encoding="utf-8-sig") as source, output_path.open("w", newline="", encoding="utf-8-sig") as target:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for row in reader:
            severity, issues = severity_for(row)
            if not issues:
                continue
            writer.writerow({
                "severity": severity,
                "page": row["page"],
                "line_no": row["line_no"],
                "table_band": row["table_band"],
                "line_type": row["line_type"],
                "field": "ocr_line",
                "ocr_text": row["text"],
                "confidence": row["confidence"],
                "bbox": f"{row['x']},{row['y']},{row['width']},{row['height']}",
                "rule_id": "|".join(issues),
                "issue": "；".join(issues),
                "status": "open",
                "reviewer": "",
                "note": "",
            })

    print(f"写出 OCR QC 清单：{output_path}")


if __name__ == "__main__":
    main()
