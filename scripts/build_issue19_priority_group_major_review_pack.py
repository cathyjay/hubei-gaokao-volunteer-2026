#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_BATCHES = ROOT / "data/working/issue19-full-major-verification-batches.csv"

OUTPUT = ROOT / "data/working/issue19-priority-group-major-review-pack.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-priority-group-major-review-pack-summary.json"

DATA_STAGE = "issue19_priority_group_major_review_pack"
SEED_BATCHES = {
    "A1-历史候选和样本先核",
    "A2-偏好专业逐专业先核",
    "A8-待补证字段核验",
}


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
        return 0


def split_flags(value):
    return [part for part in str(value or "").split("；") if part]


def join_flags(values):
    return "；".join(dict.fromkeys(v for v in values if v))


def seed_tags(row):
    tags = []
    if row.get("候选池V1命中") == "是":
        tags.append("历史候选")
    if row.get("样本学校命中") == "是":
        tags.append("样本学校")
    if "数字媒体技术" in row.get("专业偏好方向", ""):
        tags.append("数字媒体技术")
    if "计算机类相关" in row.get("专业偏好方向", ""):
        tags.append("计算机类相关")
    if "师范类相关" in row.get("专业偏好方向", ""):
        tags.append("师范类相关")
    if row.get("逐专业核验批次") == "A8-待补证字段核验":
        tags.append("待补证字段")
    return tags


def group_priority(tags):
    tag_set = set(tags)
    if {"历史候选", "样本学校"} & tag_set:
        return "W0-历史候选/样本整组先核", "00"
    if "数字媒体技术" in tag_set:
        return "W1-数字媒体技术整组先核", "01"
    if {"计算机类相关", "师范类相关"} & tag_set:
        return "W2-其他偏好专业整组先核", "02"
    if "待补证字段" in tag_set:
        return "W3-待补证整组先核", "03"
    return "W9-其他整组待核", "09"


def adjustment_risk(rows):
    default_no = sum(
        row.get("机器专业接受度初判", "").startswith("默认不能接受")
        for row in rows
    )
    special = sum(row.get("机器专业接受度初判", "").startswith("暂缓判断") for row in rows)
    if default_no:
        return "T1-同组存在默认不能接受专业，调剂高风险"
    if special:
        return "T2-同组存在特殊限制待核专业，调剂中风险"
    return "T3-未见机器默认不能接受专业，仍需家庭逐专业确认"


def main():
    rows = read_csv(VERIFICATION_BATCHES)
    groups = defaultdict(list)
    for row in rows:
        groups[row.get("专业组出现ID")].append(row)

    group_seed_tags = {}
    for group_id, group_rows in groups.items():
        tags = []
        for row in group_rows:
            if row.get("逐专业核验批次") in SEED_BATCHES:
                tags.extend(seed_tags(row))
        if tags:
            group_seed_tags[group_id] = join_flags(tags)

    output_rows = []
    for group_id, group_rows in groups.items():
        tags_text = group_seed_tags.get(group_id)
        if not tags_text:
            continue
        tags = split_flags(tags_text)
        priority, order = group_priority(tags)
        seed_major_count = sum(row.get("逐专业核验批次") in SEED_BATCHES for row in group_rows)
        preference_major_count = sum(bool(row.get("专业偏好方向")) for row in group_rows)
        default_no_count = sum(
            row.get("机器专业接受度初判", "").startswith("默认不能接受")
            for row in group_rows
        )
        special_count = sum(
            row.get("机器专业接受度初判", "").startswith("暂缓判断")
            for row in group_rows
        )
        risk = adjustment_risk(group_rows)
        group_batch_counts = Counter(row.get("逐专业核验批次") for row in group_rows)
        for row in group_rows:
            output_rows.append(
                {
                    "优先整组核验包ID": stable_id(
                        "PRIGRP",
                        [row.get("来源PDF_SHA256", ""), group_id],
                    ),
                    "优先整组核验明细ID": stable_id(
                        "PRIMAJ",
                        [row.get("来源PDF_SHA256", ""), row.get("专业行ID", "")],
                    ),
                    "来源全量逐专业核验批次表": "data/working/issue19-full-major-verification-batches.csv",
                    "来源期号": row.get("来源期号", ""),
                    "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
                    "数据阶段": DATA_STAGE,
                    "主表粒度": "逐专业招生明细",
                    "最终可用": "false",
                    "核验状态": "pending_priority_group_major_review",
                    "是否可进入最终专业列表": "false",
                    "可进入下一阶段": "false",
                    "专业组信息用途": "本行携带院校专业组上下文用于判断调剂范围；不得把本表降格为学校/专业组两层摘要。",
                    "整组核验优先级": priority,
                    "整组核验排序": order,
                    "整组入选原因": tags_text,
                    "整组调剂机器风险": risk,
                    "整组招生明细数": str(len(group_rows)),
                    "整组种子专业数": str(seed_major_count),
                    "整组偏好专业数": str(preference_major_count),
                    "整组默认不能接受专业数": str(default_no_count),
                    "整组特殊限制待核专业数": str(special_count),
                    "整组批次分布": "；".join(
                        f"{key}:{value}" for key, value in sorted(group_batch_counts.items())
                    ),
                    "专业行ID": row.get("专业行ID", ""),
                    "专业组出现ID": group_id,
                    "院校代码": row.get("院校代码", ""),
                    "院校名称OCR": row.get("院校名称OCR", ""),
                    "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
                    "专业组号OCR": row.get("专业组号OCR", ""),
                    "来源页码": row.get("来源页码", ""),
                    "版面列": row.get("版面列", ""),
                    "专业组内专业序号": row.get("专业组内专业序号", ""),
                    "专业代号OCR": row.get("专业代号OCR", ""),
                    "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
                    "再选科目OCR候选": row.get("再选科目OCR候选", ""),
                    "专业计划数OCR候选": row.get("专业计划数OCR候选", ""),
                    "学费OCR候选": row.get("学费OCR候选", ""),
                    "页级保真队列ID": row.get("页级保真队列ID", ""),
                    "私有页图证据编号": row.get("私有页图证据编号", ""),
                    "私有页图SHA256": row.get("私有页图SHA256", ""),
                    "私有OCR文本证据编号": row.get("私有OCR文本证据编号", ""),
                    "私有OCR文本SHA256": row.get("私有OCR文本SHA256", ""),
                    "逐专业核验批次": row.get("逐专业核验批次", ""),
                    "批次触发原因": row.get("批次触发原因", ""),
                    "全量保真复核优先级": row.get("全量保真复核优先级", ""),
                    "风险阻断等级": row.get("风险阻断等级", ""),
                    "高风险字段集合": row.get("高风险字段集合", ""),
                    "风险触发规则": row.get("风险触发规则", ""),
                    "专业偏好方向": row.get("专业偏好方向", ""),
                    "专业风险类型": row.get("专业风险类型", ""),
                    "机器专业接受度初判": row.get("机器专业接受度初判", ""),
                    "机器阻断或待核原因": row.get("机器阻断或待核原因", ""),
                    "调剂影响等级": row.get("调剂影响等级", ""),
                    "候选池V1命中": row.get("候选池V1命中", ""),
                    "样本学校命中": row.get("样本学校命中", ""),
                    "必须核验字段": row.get("必须核验字段", ""),
                    "核验动作": "整组回看PDF原页，逐专业核专业代号、名称、计划、学费、选科、备注，并补湖北官方系统/省招办计划、高校官网/章程、家庭接受度和调剂结论。",
                    "下一步": "先核整组边界和所有专业，再判断该院校专业组能否服从调剂；不要只核命中的偏好专业。",
                }
            )

    output_rows.sort(
        key=lambda row: (
            row["整组核验排序"],
            as_int(row["来源页码"]),
            row["院校代码"],
            row["院校专业组代码OCR规范化"],
            as_int(row["专业组内专业序号"]),
            row["专业行ID"],
        )
    )

    priority_counts = Counter(row["整组核验优先级"] for row in output_rows)
    batch_counts = Counter(row["逐专业核验批次"] for row in output_rows)
    adjustment_counts = Counter(row["整组调剂机器风险"] for row in output_rows)
    summary = {
        "status": "issue19_priority_group_major_review_pack_not_final",
        "generated_by": Path(__file__).name,
        "source_full_major_verification_batches": "data/working/issue19-full-major-verification-batches.csv",
        "output_table": "data/working/issue19-priority-group-major-review-pack.csv",
        "row_count": len(output_rows),
        "source_row_count": len(rows),
        "seed_group_count": len(group_seed_tags),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in output_rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "unique_school_count": len({row["院校代码"] for row in output_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in output_rows}),
        "priority_counts": dict(sorted(priority_counts.items())),
        "batch_counts": dict(sorted(batch_counts.items())),
        "adjustment_risk_counts": dict(sorted(adjustment_counts.items())),
        "candidate_v1_hit_row_count": sum(row["候选池V1命中"] == "是" for row in output_rows),
        "sample_school_hit_row_count": sum(row["样本学校命中"] == "是" for row in output_rows),
        "preference_major_row_count": sum(bool(row["专业偏好方向"]) for row in output_rows),
        "auto_final_list_allowed_count": sum(row["是否可进入最终专业列表"] == "true" for row in output_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "notes": [
            "本表只覆盖有历史候选、样本学校、偏好专业或待补证字段种子的专业组，并展开整组所有专业。",
            "本表用于整组核页和调剂风险判断，不产生最终可报结论。",
            "所有行仍需PDF原页、湖北官方系统/省招办计划、高校官网/章程、家庭接受度和调剂结论闭环。",
        ],
    }
    write_csv(OUTPUT, output_rows, list(output_rows[0].keys()))
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
