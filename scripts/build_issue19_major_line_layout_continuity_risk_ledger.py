#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"

OUTPUT = ROOT / "data/working/issue19-major-line-layout-continuity-risk-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-major-line-layout-continuity-risk-summary.json"

DATA_STAGE = "issue19_major_line_layout_continuity_risk_ledger"

FIELDS = [
    "版面连续性风险ID",
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
    "专业名称及备注短摘",
    "专业组标题行号",
    "专业组标题y",
    "专业起始行号",
    "相邻前一专业起始行号",
    "相邻行号差",
    "专业起始y",
    "相邻前一专业起始y",
    "相邻y差",
    "专业窗口行号范围",
    "合并证据窗口行号范围",
    "合并证据窗口行数",
    "窗口文本SHA256",
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


def as_float(value):
    try:
        return float(str(value or "").strip())
    except ValueError:
        return None


def sort_key(row):
    return (
        as_int(row.get("专业组内专业序号")) or 999999,
        as_int(row.get("专业起始行号")) or 999999,
        row.get("专业行ID", ""),
    )


def base_row(rule_id, risk_type, severity, current, previous=None, line_delta="", y_delta="", evidence=""):
    previous = previous or {}
    return {
        "版面连续性风险ID": stable_id(
            "LAYOUTRISK",
            [rule_id, current.get("专业行ID", ""), previous.get("专业行ID", "")],
        ),
        "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "来源期号": current.get("来源期号", ""),
        "来源PDF_SHA256": current.get("来源PDF_SHA256", ""),
        "数据阶段": DATA_STAGE,
        "主表粒度": "逐专业招生明细×版面连续性风险事件",
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
        "专业名称及备注短摘": current.get("专业名称及备注短摘", ""),
        "专业组标题行号": current.get("专业组标题行号", ""),
        "专业组标题y": current.get("专业组标题y", ""),
        "专业起始行号": current.get("专业起始行号", ""),
        "相邻前一专业起始行号": previous.get("专业起始行号", ""),
        "相邻行号差": str(line_delta) if line_delta != "" else "",
        "专业起始y": current.get("专业起始y", ""),
        "相邻前一专业起始y": previous.get("专业起始y", ""),
        "相邻y差": f"{y_delta:.6f}" if isinstance(y_delta, float) else "",
        "专业窗口行号范围": current.get("专业窗口行号范围", ""),
        "合并证据窗口行号范围": current.get("合并证据窗口行号范围", ""),
        "合并证据窗口行数": current.get("合并证据窗口行数", ""),
        "窗口文本SHA256": current.get("窗口文本SHA256", ""),
        "证据摘要": evidence,
        "不得进入原因": "版面连续性风险未人工核验前，不得把该专业行作为最终事实或志愿排序依据。",
        "下一步": "回看PDF原页同页同列上下文，核专业组标题、相邻专业行边界和专业归属；再用湖北官方系统或省招办计划确认。",
    }


def main():
    rows = read_csv(ANCHORS)
    by_group = defaultdict(list)
    for row in rows:
        by_group[row.get("专业组出现ID", "")].append(row)

    output_rows = []
    for row in rows:
        title_line = as_int(row.get("专业组标题行号"))
        start_line = as_int(row.get("专业起始行号"))
        if title_line is not None and start_line is not None and start_line <= title_line:
            output_rows.append(base_row(
                "L01_START_LINE_NOT_AFTER_GROUP_TITLE",
                "专业起始行号不在专业组标题之后",
                "P0-版面边界先核",
                row,
                evidence=f"专业起始行号 {start_line} <= 专业组标题行号 {title_line}",
            ))

    for group_rows in by_group.values():
        group_rows = sorted(group_rows, key=sort_key)
        for previous, current in zip(group_rows, group_rows[1:]):
            prev_line = as_int(previous.get("专业起始行号"))
            current_line = as_int(current.get("专业起始行号"))
            prev_y = as_float(previous.get("专业起始y"))
            current_y = as_float(current.get("专业起始y"))
            line_delta = None if prev_line is None or current_line is None else current_line - prev_line
            y_delta = None if prev_y is None or current_y is None else current_y - prev_y

            if y_delta is not None and y_delta > 0:
                output_rows.append(base_row(
                    "L02_ADJACENT_Y_DIRECTION_REVERSED",
                    "同组相邻专业行y方向反转",
                    "P1-相邻行顺序核验",
                    current,
                    previous,
                    line_delta=line_delta,
                    y_delta=y_delta,
                    evidence=f"相邻专业行 y 差 {y_delta:.6f} > 0",
                ))
            if y_delta == 0:
                output_rows.append(base_row(
                    "L03_ADJACENT_Y_ZERO_DELTA",
                    "同组相邻专业行y坐标完全相同",
                    "P1-相邻行顺序核验",
                    current,
                    previous,
                    line_delta=line_delta,
                    y_delta=y_delta,
                    evidence="相邻专业行 y 差为 0",
                ))
            if y_delta is not None and abs(y_delta) > 0.08:
                output_rows.append(base_row(
                    "L04_ADJACENT_Y_LARGE_DELTA",
                    "同组相邻专业行y坐标跨度异常",
                    "P2-版面跨度复核",
                    current,
                    previous,
                    line_delta=line_delta,
                    y_delta=y_delta,
                    evidence=f"相邻专业行 y 差绝对值 {abs(y_delta):.6f} > 0.08",
                ))
            if line_delta is not None and line_delta <= 0:
                output_rows.append(base_row(
                    "L05_ADJACENT_LINE_NOT_INCREASING",
                    "同组相邻专业起始行号不递增",
                    "P1-相邻行顺序核验",
                    current,
                    previous,
                    line_delta=line_delta,
                    y_delta=y_delta if y_delta is not None else "",
                    evidence=f"相邻专业起始行号差 {line_delta} <= 0",
                ))
            if line_delta is not None and line_delta > 12:
                output_rows.append(base_row(
                    "L06_ADJACENT_LINE_GAP_GT_12",
                    "同组相邻专业起始行号间隔过大",
                    "P2-版面跨度复核",
                    current,
                    previous,
                    line_delta=line_delta,
                    y_delta=y_delta if y_delta is not None else "",
                    evidence=f"相邻专业起始行号差 {line_delta} > 12",
                ))

    write_csv(OUTPUT, output_rows, FIELDS)

    involved_major_ids = set()
    for row in output_rows:
        involved_major_ids.add(row["专业行ID"])
        if row["相邻前一专业行ID"]:
            involved_major_ids.add(row["相邻前一专业行ID"])

    summary = {
        "status": "issue19_major_line_layout_continuity_risk_not_final",
        "generated_by": "build_issue19_major_line_layout_continuity_risk_ledger.py",
        "output_table": "data/working/issue19-major-line-layout-continuity-risk-ledger.csv",
        "source_anchor_table": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "source_row_count": len(rows),
        "risk_event_count": len(output_rows),
        "unique_risk_id_count": len({row["版面连续性风险ID"] for row in output_rows}),
        "unique_major_line_id_count": len(involved_major_ids),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in output_rows}),
        "risk_rule_counts": dict(Counter(row["风险规则ID"] for row in output_rows)),
        "risk_level_counts": dict(Counter(row["风险等级"] for row in output_rows)),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "machine_auto_fix_count": sum(row["机器能否自动修复"] == "true" for row in output_rows),
        "notes": [
            "本表只使用公开锚点字段生成，不保存OCR窗口原文或私有页图路径。",
            "版面连续性风险只用于排核验顺序，不直接判定OCR错误或志愿可用性。",
            "所有行均保持最终可用=false、可进入下一阶段=false、机器能否自动修复=false。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
