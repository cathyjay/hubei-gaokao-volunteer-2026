#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"

OUTPUT = ROOT / "data/working/issue19-major-code-order-risk-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-major-code-order-risk-summary.json"

DATA_STAGE = "issue19_major_code_order_risk_ledger"

FIELDS = [
    "专业代号顺序风险ID",
    "来源专业行原页证据锚点表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "机器能否自动修复",
    "风险规则ID",
    "风险类型",
    "风险等级",
    "专业行ID",
    "相邻前一专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "相邻前一专业序号",
    "专业代号OCR",
    "相邻前一专业代号OCR",
    "专业代号解析值",
    "相邻前一专业代号解析值",
    "专业代号解析差",
    "专业名称及备注短摘",
    "专业起始行号",
    "相邻前一专业起始行号",
    "专业起始y",
    "相邻前一专业起始y",
    "证据摘要",
    "不得进入原因",
    "下一步",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return None


def parse_major_code(value):
    text = str(value or "").strip().upper()
    if re.fullmatch(r"\d{1,2}", text):
        return int(text)
    if re.fullmatch(r"[A-Z]\d", text):
        return 100 + (ord(text[0]) - ord("A")) * 10 + int(text[1])
    if re.fullmatch(r"[A-Z][A-Z]", text):
        return 100 + (ord(text[0]) - ord("A")) * 10 + 10 + (ord(text[1]) - ord("A"))
    return None


def sort_key(row):
    return (
        as_int(row.get("专业组内专业序号")) or 999999,
        as_int(row.get("专业起始行号")) or 999999,
        row.get("专业行ID", ""),
    )


def base_row(rule_id, risk_type, severity, current, previous=None, current_value=None, previous_value=None, diff="", evidence=""):
    previous = previous or {}
    return {
        "专业代号顺序风险ID": stable_id(
            "CODERISK",
            [rule_id, current.get("专业行ID", ""), previous.get("专业行ID", "")],
        ),
        "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "来源期号": current.get("来源期号", ""),
        "来源PDF_SHA256": current.get("来源PDF_SHA256", ""),
        "数据阶段": DATA_STAGE,
        "主表粒度": "逐专业招生明细×专业代号顺序风险事件",
        "最终可用": "false",
        "可进入下一阶段": "false",
        "机器能否自动修复": "false",
        "风险规则ID": rule_id,
        "风险类型": risk_type,
        "风险等级": severity,
        "专业行ID": current.get("专业行ID", ""),
        "相邻前一专业行ID": previous.get("专业行ID", ""),
        "专业组出现ID": current.get("专业组出现ID", ""),
        "院校代码": current.get("院校代码", ""),
        "院校名称OCR": current.get("院校名称OCR", ""),
        "院校专业组代码OCR规范化": current.get("院校专业组代码OCR规范化", ""),
        "来源页码": current.get("来源页码", ""),
        "版面列": current.get("版面列", ""),
        "专业组内专业序号": current.get("专业组内专业序号", ""),
        "相邻前一专业序号": previous.get("专业组内专业序号", ""),
        "专业代号OCR": current.get("专业代号OCR", ""),
        "相邻前一专业代号OCR": previous.get("专业代号OCR", ""),
        "专业代号解析值": "" if current_value is None else str(current_value),
        "相邻前一专业代号解析值": "" if previous_value is None else str(previous_value),
        "专业代号解析差": "" if diff == "" else str(diff),
        "专业名称及备注短摘": current.get("专业名称及备注短摘", ""),
        "专业起始行号": current.get("专业起始行号", ""),
        "相邻前一专业起始行号": previous.get("专业起始行号", ""),
        "专业起始y": current.get("专业起始y", ""),
        "相邻前一专业起始y": previous.get("专业起始y", ""),
        "证据摘要": evidence,
        "不得进入原因": "专业代号顺序风险未人工核验前，不得把该专业行作为最终事实或志愿排序依据。",
        "下一步": "回看PDF原页同组专业代号序列，并用湖北官方系统或省招办计划逐行确认专业代号。",
    }


def main():
    rows = read_csv(ANCHORS)
    by_group = defaultdict(list)
    for row in rows:
        by_group[row.get("专业组出现ID", "")].append(row)

    output_rows = []
    for row in rows:
        parsed = parse_major_code(row.get("专业代号OCR"))
        if parsed is None:
            output_rows.append(base_row(
                "C01_MAJOR_CODE_UNPARSEABLE",
                "专业代号无法按保守规则解析",
                "P1-专业代号先核",
                row,
                current_value=None,
                evidence=f"专业代号 OCR = {row.get('专业代号OCR', '')}",
            ))

    for group_rows in by_group.values():
        group_rows = sorted(group_rows, key=sort_key)
        for previous, current in zip(group_rows, group_rows[1:]):
            previous_value = parse_major_code(previous.get("专业代号OCR"))
            current_value = parse_major_code(current.get("专业代号OCR"))
            if previous_value is None or current_value is None:
                continue
            diff = current_value - previous_value
            if diff <= 0:
                output_rows.append(base_row(
                    "C02_MAJOR_CODE_NOT_INCREASING",
                    "同组相邻专业代号解析值不递增",
                    "P1-专业代号先核",
                    current,
                    previous,
                    current_value=current_value,
                    previous_value=previous_value,
                    diff=diff,
                    evidence=f"相邻专业代号解析差 {diff} <= 0",
                ))
            if diff > 5:
                output_rows.append(base_row(
                    "C03_MAJOR_CODE_JUMP_GT_5",
                    "同组相邻专业代号解析值跳变过大",
                    "P2-专业代号序列复核",
                    current,
                    previous,
                    current_value=current_value,
                    previous_value=previous_value,
                    diff=diff,
                    evidence=f"相邻专业代号解析差 {diff} > 5",
                ))

    write_csv(OUTPUT, output_rows, FIELDS)

    involved_major_ids = set()
    for row in output_rows:
        involved_major_ids.add(row["专业行ID"])
        if row["相邻前一专业行ID"]:
            involved_major_ids.add(row["相邻前一专业行ID"])

    summary = {
        "status": "issue19_major_code_order_risk_not_final",
        "generated_by": "build_issue19_major_code_order_risk_ledger.py",
        "output_table": "data/working/issue19-major-code-order-risk-ledger.csv",
        "source_anchor_table": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "source_row_count": len(rows),
        "risk_event_count": len(output_rows),
        "unique_risk_id_count": len({row["专业代号顺序风险ID"] for row in output_rows}),
        "unique_major_line_id_count": len(involved_major_ids),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in output_rows}),
        "risk_rule_counts": dict(Counter(row["风险规则ID"] for row in output_rows)),
        "risk_level_counts": dict(Counter(row["风险等级"] for row in output_rows)),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "machine_auto_fix_count": sum(row["机器能否自动修复"] == "true" for row in output_rows),
        "notes": [
            "本表用保守规则解析专业代号，数字、一位数字、A0/A1、AA/AB 等常见代号可解析；疑似OCR混淆仍保留为风险。",
            "专业代号顺序风险只用于排核验顺序，不直接判定OCR错误或志愿可用性。",
            "所有行均保持最终可用=false、可进入下一阶段=false、机器能否自动修复=false。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
