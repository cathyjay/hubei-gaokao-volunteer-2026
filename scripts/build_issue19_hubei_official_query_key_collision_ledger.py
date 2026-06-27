#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OFFICIAL_PACKETS = ROOT / "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"

OUTPUT = ROOT / "data/working/issue19-hubei-official-query-key-collision-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-hubei-official-query-key-collision-summary.json"

DATA_STAGE = "issue19_hubei_official_query_key_collision_ledger"

FIELDS = [
    "官方查询键碰撞ID",
    "来源湖北官方系统逐专业核验包",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "碰撞键",
    "碰撞键内行数",
    "碰撞键内专业组出现ID数",
    "碰撞键内页码数",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "平台查询院校代码",
    "平台查询专业组代码",
    "平台查询专业代号",
    "来源页码",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR短摘",
    "OCR再选科目",
    "OCR专业计划数",
    "OCR学费",
    "平台匹配状态",
    "平台字段核验状态",
    "官方系统证据编号",
    "字段差异集合",
    "消歧要求",
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


def key_for(row):
    return (
        row.get("平台查询院校代码", ""),
        row.get("平台查询专业组代码", ""),
        row.get("平台查询专业代号", ""),
    )


def key_text(key):
    return "|".join(key)


def main():
    rows = read_csv(OFFICIAL_PACKETS)
    grouped = defaultdict(list)
    for row in rows:
        grouped[key_for(row)].append(row)

    collision_groups = {
        key: group
        for key, group in grouped.items()
        if len(group) > 1 and all(part for part in key)
    }

    output_rows = []
    for key in sorted(collision_groups):
        group = collision_groups[key]
        group_count = len(group)
        group_occurrence_count = len({row.get("专业组出现ID", "") for row in group})
        page_count = len({row.get("来源页码", "") for row in group})
        for row in group:
            output_rows.append({
                "官方查询键碰撞ID": stable_id("OFFICIALKEYCOLLISION", [key_text(key), row.get("专业行ID", "")]),
                "来源湖北官方系统逐专业核验包": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
                "来源期号": row.get("来源期号", ""),
                "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
                "数据阶段": DATA_STAGE,
                "主表粒度": "逐专业招生明细×官方查询键碰撞",
                "最终可用": "false",
                "可进入下一阶段": "false",
                "碰撞键": key_text(key),
                "碰撞键内行数": str(group_count),
                "碰撞键内专业组出现ID数": str(group_occurrence_count),
                "碰撞键内页码数": str(page_count),
                "专业行ID": row.get("专业行ID", ""),
                "专业组出现ID": row.get("专业组出现ID", ""),
                "院校代码": row.get("院校代码", ""),
                "院校名称OCR": row.get("院校名称OCR", ""),
                "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
                "平台查询院校代码": row.get("平台查询院校代码", ""),
                "平台查询专业组代码": row.get("平台查询专业组代码", ""),
                "平台查询专业代号": row.get("平台查询专业代号", ""),
                "来源页码": row.get("来源页码", ""),
                "专业组内专业序号": row.get("专业组内专业序号", ""),
                "专业代号OCR": row.get("专业代号OCR", ""),
                "专业名称及备注OCR短摘": row.get("专业名称及备注OCR短摘", ""),
                "OCR再选科目": row.get("OCR再选科目", ""),
                "OCR专业计划数": row.get("OCR专业计划数", ""),
                "OCR学费": row.get("OCR学费", ""),
                "平台匹配状态": row.get("平台匹配状态", ""),
                "平台字段核验状态": row.get("平台字段核验状态", ""),
                "官方系统证据编号": row.get("官方系统证据编号", ""),
                "字段差异集合": row.get("字段差异集合", ""),
                "消歧要求": "官方系统回填必须同时使用专业行ID、专业组出现ID、来源页码、专业组内专业序号和官方返回行证据；不得只按院校代码+专业组代码+专业代号合并。",
                "不得进入原因": "官方查询键不唯一，未消歧前不得写入最终事实或志愿排序。",
                "下一步": "回看PDF原页位置，并在湖北官方系统或省招办计划中逐行截图/导出证据后按专业行ID回填。",
            })

    write_csv(OUTPUT, output_rows, FIELDS)
    summary = {
        "status": "issue19_hubei_official_query_key_collision_not_final",
        "generated_by": "build_issue19_hubei_official_query_key_collision_ledger.py",
        "output_table": "data/working/issue19-hubei-official-query-key-collision-ledger.csv",
        "source_hubei_official_packets": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
        "source_row_count": len(rows),
        "collision_key_count": len(collision_groups),
        "collision_row_count": len(output_rows),
        "unique_collision_id_count": len({row["官方查询键碰撞ID"] for row in output_rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "collision_size_counts": dict(Counter(str(len(group)) for group in collision_groups.values())),
        "platform_field_review_status_counts": dict(Counter(row["平台字段核验状态"] for row in output_rows)),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "notes": [
            "本表只记录官方查询键碰撞，防止后续按非唯一三元组回填官方计划。",
            "回填官方系统结果必须使用专业行ID和原页位置消歧。",
            "所有行均保持最终可用=false、可进入下一阶段=false。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
