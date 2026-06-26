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
    split_tags,
)


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
FULL_GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
STRUCTURE_ANOMALIES = ROOT / "data/working/issue19-ocr-structure-anomaly-queue.csv"

QUALITY_GROUP_OUTPUT = ROOT / "data/working/issue19-full-quality-group-tiers.csv"
QUALITY_QUEUE_OUTPUT = ROOT / "data/working/issue19-full-quality-review-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-full-quality-tier-summary.json"

HIGH_SEVERITY_RULES = {
    "major_text_embeds_other_school_marker",
    "major_text_embeds_group_code",
    "plan_count_number_ge_1000",
    "plan_count_not_plain_number",
    "tuition_number_le_500",
    "tuition_not_plain_number",
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
    return (
        group_id_by_row_index,
        major_group_ids,
        unmatched_major_count,
        fallback_unique_group_code_count,
    )


def major_flags(majors):
    flag_counter = Counter()
    non_plain_plan = 0
    non_plain_tuition = 0
    suspicious_tuition = 0
    plan_ge_1000 = 0
    tuition_le_500 = 0
    tuition_over_budget = 0
    for major in majors:
        flags = split_tags(major.get("字段完整性标记", ""))
        flag_counter.update(flags)
        if major.get("专业计划数是否纯数字") == "否":
            non_plain_plan += 1
        if major.get("学费是否纯数字") == "否":
            non_plain_tuition += 1
        tuition = major.get("学费OCR候选", "")
        if (
            tuition and not tuition.isdigit()
            or "tuition_not_plain_number" in flags
        ):
            suspicious_tuition += 1
        plan_number = as_int(major.get("专业计划数OCR数字候选"))
        tuition_number = as_int(major.get("学费OCR数字候选"))
        if plan_number is not None and plan_number >= 1000:
            plan_ge_1000 += 1
        if tuition_number is not None and 0 < tuition_number <= 500:
            tuition_le_500 += 1
            suspicious_tuition += 1
        if tuition_number is not None and tuition_number > 15000:
            tuition_over_budget += 1
    return flag_counter, non_plain_plan, non_plain_tuition, suspicious_tuition, plan_ge_1000, tuition_le_500, tuition_over_budget


def quality_tier(*, major_count, high_anomaly_count, medium_anomaly_count, field_issue_count, group_candidate_hit, preference_hit):
    if major_count == 0:
        return "Q0-无专业明细"
    if high_anomaly_count:
        return "Q1-高风险结构异常"
    if medium_anomaly_count or field_issue_count:
        if group_candidate_hit or preference_hit:
            return "Q2-重点候选字段待核"
        return "Q3-字段待核"
    return "Q4-结构相对完整待抽检"


def review_priority(
    tier,
    *,
    group_candidate_hit,
    preference_hit,
    risk_hit,
    high_anomaly_count,
    duplicate_group_code,
    suspicious_tuition_count,
    missing_subject_count,
    missing_plan_count,
    line_count_mismatch,
):
    if (
        tier == "Q0-无专业明细"
        or high_anomaly_count
        or group_candidate_hit
        or preference_hit
        or risk_hit
        or duplicate_group_code
        or suspicious_tuition_count
        or missing_subject_count
        or missing_plan_count
        or line_count_mismatch
    ):
        return "P0-必须优先核页"
    if tier in {"Q2-重点候选字段待核", "Q3-字段待核"}:
        return "P1-高优先核页"
    if tier == "Q4-结构相对完整待抽检":
        return "P3-相对完整但仍需核页"
    return "P2-常规核页"


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]

    group_rows = read_csv(FULL_GROUPS)
    major_rows = read_csv(FULL_MAJORS)
    anomaly_rows = read_csv(STRUCTURE_ANOMALIES)
    group_code_counts = Counter(row["院校专业组代码OCR规范化"] for row in group_rows)
    (
        group_id_by_row_index,
        major_group_ids,
        unmatched_major_count,
        fallback_unique_group_code_count,
    ) = assign_group_occurrence_ids(group_rows, major_rows, source_pdf_sha256)

    majors_by_group = defaultdict(list)
    major_group_id_by_key = {}
    for index, row in enumerate(major_rows, start=1):
        group_id = major_group_ids.get(index)
        if group_id:
            majors_by_group[group_id].append(row)
            major_group_id_by_key[major_match_key(row)] = group_id

    anomalies_by_group = defaultdict(list)
    for row in anomaly_rows:
        group_id = major_group_id_by_key.get(major_match_key(row))
        if group_id:
            anomalies_by_group[group_id].append(row)

    quality_rows = []
    queue_rows = []
    for index, row in enumerate(group_rows, start=1):
        group_code = row["院校专业组代码OCR规范化"]
        group_occurrence_id = group_id_by_row_index[index]
        duplicate_group_code_count = group_code_counts[group_code]
        duplicate_group_code = duplicate_group_code_count > 1
        majors = majors_by_group.get(group_occurrence_id, [])
        anomalies = anomalies_by_group.get(group_occurrence_id, [])
        anomaly_rule_counter = Counter(item["异常规则ID"] for item in anomalies)
        anomaly_type_counter = Counter(item["异常类型"] for item in anomalies)
        high_anomaly_count = sum(item["严重程度"] == "高" for item in anomalies)
        medium_anomaly_count = sum(item["严重程度"] == "中" for item in anomalies)

        (
            flag_counter,
            non_plain_plan_count,
            non_plain_tuition_count,
            suspicious_tuition_count,
            plan_ge_1000_count,
            tuition_le_500_count,
            tuition_over_budget_count,
        ) = major_flags(majors)
        field_issue_count = sum(flag_counter.values()) + non_plain_plan_count + non_plain_tuition_count

        tags = split_tags(row.get("偏好和风险标签", ""))
        major_preference_tags = set()
        for major in majors:
            major_preference_tags.update(split_tags(major.get("偏好和风险标签", "")) & set(PREFERENCE_TAG_LABELS))
        risk_tags = tags & set(RISK_TAG_LABELS)
        group_candidate_hit = row.get("候选池V1命中") == "是"
        sample_hit = row.get("样本学校命中") == "是"
        preference_hit = bool(major_preference_tags)
        risk_hit = bool(risk_tags)
        line_count_mismatch = str(len(majors)) != row["OCR专业行数"]
        unique_major_code_count = len({major.get("专业代号OCR", "") for major in majors if major.get("专业代号OCR", "")})
        empty_major_code_count = sum(not major.get("专业代号OCR", "") for major in majors)
        tier = quality_tier(
            major_count=len(majors),
            high_anomaly_count=high_anomaly_count,
            medium_anomaly_count=medium_anomaly_count,
            field_issue_count=field_issue_count,
            group_candidate_hit=group_candidate_hit,
            preference_hit=preference_hit,
        )
        priority = review_priority(
            tier,
            group_candidate_hit=group_candidate_hit,
            preference_hit=preference_hit,
            risk_hit=risk_hit,
            high_anomaly_count=high_anomaly_count,
            duplicate_group_code=duplicate_group_code,
            suspicious_tuition_count=suspicious_tuition_count,
            missing_subject_count=flag_counter["missing_subject_candidate"],
            missing_plan_count=flag_counter["missing_plan_count_candidate"],
            line_count_mismatch=line_count_mismatch,
        )

        reasons = []
        if len(majors) == 0:
            reasons.append("无专业明细")
        if high_anomaly_count:
            reasons.append(f"高严重度结构异常{high_anomaly_count}条")
        if medium_anomaly_count:
            reasons.append(f"中严重度结构异常{medium_anomaly_count}条")
        if field_issue_count:
            reasons.append(f"字段完整性/纯数字问题{field_issue_count}项")
        if line_count_mismatch:
            reasons.append("组表专业行数与明细表聚合不一致")
        if duplicate_group_code:
            reasons.append(f"规范化专业组代码重复出现{duplicate_group_code_count}行")
        if suspicious_tuition_count:
            reasons.append(f"异常学费{ suspicious_tuition_count }项")
        if group_candidate_hit:
            reasons.append("命中历史候选池")
        if preference_hit:
            reasons.append("命中当前偏好专业方向")
        if risk_hit:
            reasons.append("命中风险标签")

        output = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "full_quality_tier_ocr_draft",
            "最终可用": "false",
            "专业组出现ID": group_occurrence_id,
            "专业组源行号": str(index + 1),
            "院校代码": row["院校代码"],
            "院校名称OCR": row["院校名称OCR"],
            "院校专业组代码OCR规范化": group_code,
            "专业组号OCR": row["专业组号OCR"],
            "专业组标题OCR原文": row["专业组标题OCR原文"],
            "来源页码": row["来源页码"],
            "版面列": row["版面列"],
            "专业组标题行号": row["专业组标题行号"],
            "OCR专业行数_组表": row["OCR专业行数"],
            "专业明细行数_专业表": str(len(majors)),
            "专业行数是否一致": "是" if not line_count_mismatch else "否",
            "规范化专业组代码是否重复": "是" if duplicate_group_code else "否",
            "规范化专业组代码重复行数": str(duplicate_group_code_count),
            "唯一专业代号数": str(unique_major_code_count),
            "空专业代号数": str(empty_major_code_count),
            "相对质量层级": tier,
            "复核优先级": priority,
            "优先级原因代码": priority,
            "优先级原因说明": "；".join(reasons) or "未触发明显异常，仍需抽检核页",
            "组字段完整性标记": row.get("字段完整性标记", ""),
            "结构异常数": str(len(anomalies)),
            "高严重结构异常数": str(high_anomaly_count),
            "中严重结构异常数": str(medium_anomaly_count),
            "结构异常规则ID列表": "；".join(sorted(anomaly_rule_counter)),
            "结构异常类型列表": "；".join(sorted(anomaly_type_counter)),
            "字段完整性问题数": str(field_issue_count),
            "缺再选科目专业数": str(flag_counter["missing_subject_candidate"]),
            "缺计划数专业数": str(flag_counter["missing_plan_count_candidate"]),
            "缺学费专业数": str(flag_counter["missing_tuition_candidate"]),
            "非纯数字计划数专业数": str(non_plain_plan_count),
            "计划数>=1000专业数": str(plan_ge_1000_count),
            "非纯数字学费专业数": str(non_plain_tuition_count),
            "学费<=500专业数": str(tuition_le_500_count),
            "学费超过预算专业数": str(tuition_over_budget_count),
            "异常学费专业数": str(suspicious_tuition_count),
            "偏好专业命中数": str(sum(1 for major in majors if split_tags(major.get("偏好和风险标签", "")) & set(PREFERENCE_TAG_LABELS))),
            "偏好方向列表": labels_for(major_preference_tags, PREFERENCE_TAG_LABELS),
            "硬风险命中": "是" if risk_hit else "否",
            "硬风险类型列表": risk_labels(risk_tags),
            "候选池V1命中": row.get("候选池V1命中", ""),
            "样本学校命中": row.get("样本学校命中", ""),
            "核验状态": "needs_manual_pdf_review",
            "下一步": "按复核优先级回看第19期原PDF页；修正结构异常和字段问题后才能进入候选升级闸门",
        }
        quality_rows.append(output)
        if priority != "P3-相对完整但仍需核页":
            queue_rows.append(output)

    quality_rows.sort(key=lambda item: (item["院校代码"], item["院校专业组代码OCR规范化"]))
    priority_order = {
        "P0-必须优先核页": 0,
        "P1-高优先核页": 1,
        "P2-常规核页": 2,
        "P3-相对完整但仍需核页": 3,
    }
    queue_rows.sort(key=lambda item: (
        priority_order.get(item["复核优先级"], 99),
        item["来源页码"],
        item["院校代码"],
        item["院校专业组代码OCR规范化"],
    ))

    fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "专业组出现ID",
        "专业组源行号",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组标题OCR原文",
        "来源页码",
        "版面列",
        "专业组标题行号",
        "OCR专业行数_组表",
        "专业明细行数_专业表",
        "专业行数是否一致",
        "规范化专业组代码是否重复",
        "规范化专业组代码重复行数",
        "唯一专业代号数",
        "空专业代号数",
        "相对质量层级",
        "复核优先级",
        "优先级原因代码",
        "优先级原因说明",
        "组字段完整性标记",
        "结构异常数",
        "高严重结构异常数",
        "中严重结构异常数",
        "结构异常规则ID列表",
        "结构异常类型列表",
        "字段完整性问题数",
        "缺再选科目专业数",
        "缺计划数专业数",
        "缺学费专业数",
        "非纯数字计划数专业数",
        "计划数>=1000专业数",
        "非纯数字学费专业数",
        "学费<=500专业数",
        "学费超过预算专业数",
        "异常学费专业数",
        "偏好专业命中数",
        "偏好方向列表",
        "硬风险命中",
        "硬风险类型列表",
        "候选池V1命中",
        "样本学校命中",
        "下一步",
    ]
    write_csv(QUALITY_GROUP_OUTPUT, quality_rows, fields)
    write_csv(QUALITY_QUEUE_OUTPUT, queue_rows, fields)

    tier_counter = Counter(row["相对质量层级"] for row in quality_rows)
    priority_counter = Counter(row["复核优先级"] for row in quality_rows)
    summary = {
        "status": "full_quality_tiers_need_manual_pdf_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "full_quality_tier_ocr_draft",
        "generated_by": "scripts/build_issue19_full_quality_tiers.py",
        "inputs": input_snapshot(ROOT, [ISSUE19_SOURCE, FULL_GROUPS, FULL_MAJORS, STRUCTURE_ANOMALIES]),
        "group_count": len(quality_rows),
        "major_count": len(major_rows),
        "review_queue_count": len(queue_rows),
        "quality_tier_counts": dict(tier_counter),
        "review_priority_counts": dict(priority_counter),
        "groups_with_any_structure_anomaly": sum(as_int(row["结构异常数"]) > 0 for row in quality_rows),
        "groups_with_high_structure_anomaly": sum(as_int(row["高严重结构异常数"]) > 0 for row in quality_rows),
        "groups_with_no_major_detail": sum(row["相对质量层级"] == "Q0-无专业明细" for row in quality_rows),
        "duplicate_normalized_group_code_count": sum(1 for count in group_code_counts.values() if count > 1),
        "duplicate_normalized_group_code_row_count": sum(count for count in group_code_counts.values() if count > 1),
        "unmatched_major_group_occurrence_count": unmatched_major_count,
        "fallback_unique_group_code_major_count": fallback_unique_group_code_count,
        "candidate_v1_hit_group_count": sum(row["候选池V1命中"] == "是" for row in quality_rows),
        "preference_hit_group_count": sum(bool(row["偏好方向列表"]) for row in quality_rows),
        "risk_hit_group_count": sum(row["硬风险命中"] == "是" for row in quality_rows),
        "outputs": [
            str(QUALITY_GROUP_OUTPUT.relative_to(ROOT)),
            str(QUALITY_QUEUE_OUTPUT.relative_to(ROOT)),
        ],
        "notes": [
            "质量分层只用于安排复核优先级，不代表可填报。",
            "所有行保持最终可用=false，仍需回看第19期原PDF页和官方系统/章程。",
            "Q4 只是结构相对完整待抽检，不是最终事实。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出全量专业组质量分层：{QUALITY_GROUP_OUTPUT}")
    print(f"写出全量质量复核队列：{QUALITY_QUEUE_OUTPUT}")
    print(f"写出质量分层摘要：{SUMMARY_OUTPUT}")
    print(f"专业组数：{len(quality_rows)}")
    print(f"复核队列数：{len(queue_rows)}")


if __name__ == "__main__":
    main()
