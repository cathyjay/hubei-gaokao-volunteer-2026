#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import (
    PREFERENCE_TAG_LABELS,
    RISK_TAG_LABELS,
    as_int,
    input_snapshot,
    risk_labels,
    risk_level,
    split_tags,
)


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
FULL_GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
STRUCTURE_ANOMALIES = ROOT / "data/working/issue19-ocr-structure-anomaly-queue.csv"
GROUP_QUALITY = ROOT / "data/working/issue19-full-quality-group-tiers.csv"

MAJOR_WORKBENCH_OUTPUT = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"
MAJOR_REVIEW_QUEUE_OUTPUT = ROOT / "data/working/issue19-full-major-detail-review-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-full-major-detail-quality-summary.json"


PRIORITY_ORDER = {
    "P0-逐专业必须核页": 0,
    "P1-逐专业高优先核页": 1,
    "P3-逐专业相对完整但仍需核页": 3,
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def labels_for(tags, mapping):
    return "；".join(mapping[tag] for tag in sorted(tags) if tag in mapping)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def group_match_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        row.get("来源页码", ""),
        row.get("版面列", ""),
        row.get("专业组标题行号", ""),
        row.get("专业组标题OCR原文", ""),
    )


def major_match_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        row.get("专业代号OCR", ""),
        row.get("专业名称及备注OCR", ""),
        row.get("来源页码", ""),
        row.get("版面列", ""),
        row.get("专业计划数OCR候选", ""),
        row.get("学费OCR候选", ""),
    )


def major_line_id(row, index, source_pdf_sha256):
    return stable_id(
        "M",
        [
            source_pdf_sha256,
            index,
            row.get("院校代码", ""),
            row.get("院校专业组代码OCR规范化", ""),
            row.get("来源页码", ""),
            row.get("版面列", ""),
            row.get("专业起始行号", ""),
            row.get("专业起始y", ""),
            row.get("专业代号OCR", ""),
            row.get("专业名称及备注OCR", ""),
        ],
    )


def assign_group_occurrence_ids(group_rows, major_rows, source_pdf_sha256):
    group_ids_by_key = {}
    groups_by_code = defaultdict(list)
    group_id_by_row_index = {}
    for index, row in enumerate(group_rows, start=1):
        group_id = stable_id(
            "G",
            [
                source_pdf_sha256,
                index,
                row.get("院校代码", ""),
                row.get("院校专业组代码OCR规范化", ""),
                row.get("来源页码", ""),
                row.get("版面列", ""),
                row.get("专业组标题行号", ""),
                row.get("专业组标题OCR原文", ""),
            ],
        )
        group_id_by_row_index[index] = group_id
        group_ids_by_key[group_match_key(row)] = group_id
        groups_by_code[row["院校专业组代码OCR规范化"]].append((group_id, row))

    major_group_ids = {}
    unmatched_major_count = 0
    fallback_unique_group_code_count = 0
    for index, row in enumerate(major_rows, start=1):
        exact_group_id = group_ids_by_key.get(group_match_key(row))
        if exact_group_id:
            major_group_ids[index] = exact_group_id
            continue
        code_groups = groups_by_code.get(row["院校专业组代码OCR规范化"], [])
        if len(code_groups) == 1:
            major_group_ids[index] = code_groups[0][0]
            fallback_unique_group_code_count += 1
            continue
        unmatched_major_count += 1
    return major_group_ids, unmatched_major_count, fallback_unique_group_code_count


def count_flags(value):
    return len(split_tags(value))


def major_priority(
    *,
    group_priority,
    major_tags,
    major_flag_count,
    anomaly_count,
    high_anomaly_count,
    non_plain_plan,
    non_plain_tuition,
    suspicious_tuition,
    missing_subject,
    missing_plan,
    missing_tuition,
):
    if (
        group_priority == "P0-必须优先核页"
        or high_anomaly_count > 0
        or major_tags & set(PREFERENCE_TAG_LABELS)
        or major_tags & set(RISK_TAG_LABELS)
        or non_plain_plan
        or non_plain_tuition
        or suspicious_tuition
        or missing_subject
        or missing_plan
        or missing_tuition
    ):
        return "P0-逐专业必须核页"
    if group_priority in {"P1-高优先核页", "P2-常规核页"} or anomaly_count or major_flag_count:
        return "P1-逐专业高优先核页"
    return "P3-逐专业相对完整但仍需核页"


def attention_type(tags, preference_labels, risk_label_text, anomaly_count, field_flag_count):
    if "rejected_medical" in tags:
        return "明确排除方向待人工确认"
    if "high_fee_or_coop" in tags or "tuition_over_15000" in tags:
        return "费用或合作办学风险待确认"
    if tags & {"body_or_exam_limit", "language_or_single_subject", "special_plan_or_direction"}:
        return "限制条件待确认"
    if preference_labels:
        return "偏好方向待研究"
    if anomaly_count or field_flag_count:
        return "字段或结构异常待核验"
    return "普通明细待核页"


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]

    group_rows = read_csv(FULL_GROUPS)
    major_rows = read_csv(FULL_MAJORS)
    anomaly_rows = read_csv(STRUCTURE_ANOMALIES)
    quality_rows = read_csv(GROUP_QUALITY)
    (
        major_group_ids,
        unmatched_major_group_occurrence_count,
        fallback_unique_group_code_major_count,
    ) = assign_group_occurrence_ids(group_rows, major_rows, source_pdf_sha256)

    quality_by_occurrence_id = {}
    for row in quality_rows:
        quality_by_occurrence_id[row["专业组出现ID"]] = row

    anomaly_by_major_key = defaultdict(list)
    for row in anomaly_rows:
        anomaly_by_major_key[major_match_key(row)].append(row)

    major_sequence_by_group = defaultdict(int)
    workbench_rows = []
    review_queue_rows = []
    unmatched_group_quality_count = 0
    matched_anomaly_count = 0

    for index, major in enumerate(major_rows, start=1):
        group_code = major["院校专业组代码OCR规范化"]
        group_occurrence_id = major_group_ids.get(index, "")
        line_id = major_line_id(major, index, source_pdf_sha256)
        major_sequence_by_group[group_occurrence_id or group_code] += 1
        group_quality = quality_by_occurrence_id.get(group_occurrence_id, {})
        group_quality_match = "按专业组出现ID匹配" if group_quality else "未匹配到专业组质量索引"
        if not group_quality:
            unmatched_group_quality_count += 1

        anomalies = anomaly_by_major_key.get(major_match_key(major), [])
        matched_anomaly_count += len(anomalies)
        anomaly_rules = Counter(row["异常规则ID"] for row in anomalies)
        anomaly_types = Counter(row["异常类型"] for row in anomalies)
        anomaly_severities = Counter(row["严重程度"] for row in anomalies)
        high_anomaly_count = anomaly_severities["高"]

        tags = split_tags(major.get("偏好和风险标签", ""))
        preference_tags = tags & set(PREFERENCE_TAG_LABELS)
        risk_tags = tags & set(RISK_TAG_LABELS)
        preference_label_text = labels_for(preference_tags, PREFERENCE_TAG_LABELS)
        risk_label_text = risk_labels(risk_tags)
        field_flag_count = count_flags(major.get("字段完整性标记", ""))
        tuition_number = as_int(major.get("学费OCR数字候选"))
        non_plain_plan = major.get("专业计划数是否纯数字") == "否"
        non_plain_tuition = major.get("学费是否纯数字") == "否"
        missing_subject = "missing_subject_candidate" in split_tags(major.get("字段完整性标记", ""))
        missing_plan = "missing_plan_count_candidate" in split_tags(major.get("字段完整性标记", ""))
        missing_tuition = "missing_tuition_candidate" in split_tags(major.get("字段完整性标记", ""))
        suspicious_tuition = (
            non_plain_tuition
            or "tuition_not_plain_number" in split_tags(major.get("字段完整性标记", ""))
            or (tuition_number is not None and 0 < tuition_number <= 500)
        )

        priority = major_priority(
            group_priority=group_quality.get("复核优先级", ""),
            major_tags=tags,
            major_flag_count=field_flag_count,
            anomaly_count=len(anomalies),
            high_anomaly_count=high_anomaly_count,
            non_plain_plan=non_plain_plan,
            non_plain_tuition=non_plain_tuition,
            suspicious_tuition=suspicious_tuition,
            missing_subject=missing_subject,
            missing_plan=missing_plan,
            missing_tuition=missing_tuition,
        )

        reasons = []
        if group_quality.get("复核优先级"):
            reasons.append(f"所在专业组{group_quality.get('复核优先级')}")
        if high_anomaly_count:
            reasons.append(f"专业行高严重结构异常{high_anomaly_count}条")
        elif anomalies:
            reasons.append(f"专业行结构异常{len(anomalies)}条")
        if field_flag_count:
            reasons.append(f"专业字段完整性标记{field_flag_count}项")
        if preference_label_text:
            reasons.append(f"命中偏好方向：{preference_label_text}")
        if risk_label_text:
            reasons.append(f"命中风险：{risk_label_text}")
        if non_plain_plan:
            reasons.append("计划数非纯数字或缺失")
        if suspicious_tuition:
            reasons.append("学费字段疑似异常")

        output = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "full_major_detail_quality_workbench",
            "最终可用": "false",
            "核验状态": "needs_manual_pdf_review",
            "原专业明细数据阶段": major.get("数据阶段", ""),
            "原专业明细核验状态": major.get("核验状态", ""),
            "专业行ID": line_id,
            "专业组出现ID": group_occurrence_id,
            "专业明细源行号": str(index + 1),
            "专业组内专业序号": str(major_sequence_by_group[group_occurrence_id or group_code]),
            "院校代码": major["院校代码"],
            "院校名称OCR": major["院校名称OCR"],
            "院校专业组代码OCR规范化": group_code,
            "专业组号OCR": major["专业组号OCR"],
            "专业组标题OCR原文": major["专业组标题OCR原文"],
            "来源页码": major["来源页码"],
            "版面列": major["版面列"],
            "专业组标题行号": major["专业组标题行号"],
            "专业组标题y": major.get("专业组标题y", ""),
            "专业起始行号": major["专业起始行号"],
            "专业起始y": major.get("专业起始y", ""),
            "专业代号OCR": major["专业代号OCR"],
            "专业名称及备注OCR": major["专业名称及备注OCR"],
            "再选科目OCR候选": major["再选科目OCR候选"],
            "专业计划数OCR候选": major["专业计划数OCR候选"],
            "专业计划数OCR数字候选": major["专业计划数OCR数字候选"],
            "专业计划数是否纯数字": major["专业计划数是否纯数字"],
            "学费OCR候选": major["学费OCR候选"],
            "学费OCR数字候选": major["学费OCR数字候选"],
            "学费是否纯数字": major["学费是否纯数字"],
            "OCR置信度": major["OCR置信度"],
            "专业偏好和风险标签原文": major.get("偏好和风险标签", ""),
            "专业偏好方向": preference_label_text,
            "专业风险类型": risk_label_text,
            "专业风险等级": risk_level(risk_tags),
            "专业字段完整性标记": major.get("字段完整性标记", ""),
            "专业字段完整性问题数": str(field_flag_count),
            "专业行结构异常数": str(len(anomalies)),
            "专业行高严重结构异常数": str(high_anomaly_count),
            "专业行异常规则ID列表": "；".join(sorted(anomaly_rules)),
            "专业行异常类型列表": "；".join(sorted(anomaly_types)),
            "专业行异常严重程度列表": "；".join(sorted(anomaly_severities)),
            "专业行异常证据摘要": "；".join(
                row.get("异常证据", "") for row in anomalies if row.get("异常证据", "")
            )[:300],
            "专业关注类型": attention_type(
                tags, preference_label_text, risk_label_text, len(anomalies), field_flag_count
            ),
            "逐专业复核优先级": priority,
            "逐专业复核原因说明": "；".join(reasons) or "未触发明显异常，仍需回看原页抽检",
            "组质量匹配方式": group_quality_match,
            "组相对质量层级": group_quality.get("相对质量层级", ""),
            "组复核优先级": group_quality.get("复核优先级", ""),
            "组优先级原因说明": group_quality.get("优先级原因说明", ""),
            "组结构异常数": group_quality.get("结构异常数", ""),
            "组高严重结构异常数": group_quality.get("高严重结构异常数", ""),
            "组字段完整性问题数": group_quality.get("字段完整性问题数", ""),
            "组偏好方向列表": group_quality.get("偏好方向列表", ""),
            "组硬风险命中": group_quality.get("硬风险命中", ""),
            "组硬风险类型列表": group_quality.get("硬风险类型列表", ""),
            "规范化专业组代码是否重复": group_quality.get("规范化专业组代码是否重复", ""),
            "规范化专业组代码重复行数": group_quality.get("规范化专业组代码重复行数", ""),
            "专业行候选池V1命中": major.get("候选池V1命中", ""),
            "专业行样本学校命中": major.get("样本学校命中", ""),
            "下一步": "回看第19期原PDF页，逐字段核对专业代号、专业名称、计划数、学费、选科和备注；确认组内全部专业后再判断调剂。",
        }
        workbench_rows.append(output)
        if priority != "P3-逐专业相对完整但仍需核页":
            review_queue_rows.append(output)

    workbench_rows.sort(key=lambda row: as_int(row["专业明细源行号"]) or 0)
    review_queue_rows.sort(
        key=lambda row: (
            PRIORITY_ORDER.get(row["逐专业复核优先级"], 99),
            as_int(row["来源页码"]) or 9999,
            row["院校代码"],
            row["院校专业组代码OCR规范化"],
            as_int(row["专业组内专业序号"]) or 9999,
        )
    )

    fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "原专业明细数据阶段",
        "原专业明细核验状态",
        "专业行ID",
        "专业组出现ID",
        "专业明细源行号",
        "专业组内专业序号",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组标题OCR原文",
        "来源页码",
        "版面列",
        "专业组标题行号",
        "专业组标题y",
        "专业起始行号",
        "专业起始y",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "专业计划数OCR数字候选",
        "专业计划数是否纯数字",
        "学费OCR候选",
        "学费OCR数字候选",
        "学费是否纯数字",
        "OCR置信度",
        "专业偏好和风险标签原文",
        "专业偏好方向",
        "专业风险类型",
        "专业风险等级",
        "专业字段完整性标记",
        "专业字段完整性问题数",
        "专业行结构异常数",
        "专业行高严重结构异常数",
        "专业行异常规则ID列表",
        "专业行异常类型列表",
        "专业行异常严重程度列表",
        "专业行异常证据摘要",
        "专业关注类型",
        "逐专业复核优先级",
        "逐专业复核原因说明",
        "组质量匹配方式",
        "组相对质量层级",
        "组复核优先级",
        "组优先级原因说明",
        "组结构异常数",
        "组高严重结构异常数",
        "组字段完整性问题数",
        "组偏好方向列表",
        "组硬风险命中",
        "组硬风险类型列表",
        "规范化专业组代码是否重复",
        "规范化专业组代码重复行数",
        "专业行候选池V1命中",
        "专业行样本学校命中",
        "下一步",
    ]
    write_csv(MAJOR_WORKBENCH_OUTPUT, workbench_rows, fields)
    write_csv(MAJOR_REVIEW_QUEUE_OUTPUT, review_queue_rows, fields)

    priority_counter = Counter(row["逐专业复核优先级"] for row in workbench_rows)
    attention_counter = Counter(row["专业关注类型"] for row in workbench_rows)
    summary = {
        "status": "full_major_detail_quality_need_manual_pdf_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "full_major_detail_quality_workbench",
        "generated_by": "scripts/build_issue19_major_detail_quality_workbench.py",
        "inputs": input_snapshot(
            ROOT, [ISSUE19_SOURCE, FULL_GROUPS, FULL_MAJORS, STRUCTURE_ANOMALIES, GROUP_QUALITY]
        ),
        "major_count": len(workbench_rows),
        "review_queue_count": len(review_queue_rows),
        "matched_anomaly_count": matched_anomaly_count,
        "unmatched_anomaly_count": len(anomaly_rows) - matched_anomaly_count,
        "unmatched_group_quality_count": unmatched_group_quality_count,
        "unmatched_major_group_occurrence_count": unmatched_major_group_occurrence_count,
        "fallback_unique_group_code_major_count": fallback_unique_group_code_major_count,
        "unique_major_line_id_count": len({row["专业行ID"] for row in workbench_rows}),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in workbench_rows if row["专业组出现ID"]}),
        "major_review_priority_counts": dict(priority_counter),
        "major_attention_type_counts": dict(attention_counter),
        "major_rows_with_structure_anomaly": sum(
            as_int(row["专业行结构异常数"]) > 0 for row in workbench_rows
        ),
        "major_rows_with_high_structure_anomaly": sum(
            as_int(row["专业行高严重结构异常数"]) > 0 for row in workbench_rows
        ),
        "preference_major_row_count": sum(bool(row["专业偏好方向"]) for row in workbench_rows),
        "risk_major_row_count": sum(row["专业风险等级"] != "未触发硬风险" for row in workbench_rows),
        "candidate_v1_major_row_count": sum(row["专业行候选池V1命中"] == "是" for row in workbench_rows),
        "duplicate_group_code_major_row_count": sum(
            row["规范化专业组代码是否重复"] == "是" for row in workbench_rows
        ),
        "outputs": [
            str(MAJOR_WORKBENCH_OUTPUT.relative_to(ROOT)),
            str(MAJOR_REVIEW_QUEUE_OUTPUT.relative_to(ROOT)),
        ],
        "notes": [
            "本工作台是逐专业明细派生表，用于后续展开完整招生明细和安排核页优先级。",
            "逐专业复核优先级不是录取建议，不代表该专业或专业组可报。",
            "所有行保持最终可用=false，必须回看第19期原PDF页和官方系统/章程。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出逐专业明细质量工作台：{MAJOR_WORKBENCH_OUTPUT}")
    print(f"写出逐专业明细复核队列：{MAJOR_REVIEW_QUEUE_OUTPUT}")
    print(f"写出逐专业明细质量摘要：{SUMMARY_OUTPUT}")
    print(f"专业明细行数：{len(workbench_rows)}")
    print(f"复核队列行数：{len(review_queue_rows)}")


if __name__ == "__main__":
    main()
