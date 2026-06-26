#!/usr/bin/env python3
import csv
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
FAMILY_PREFERENCES = ROOT / "data/working/family-preferences.json"
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
CANDIDATE_V2_GROUPS = ROOT / "data/working/issue19-candidate-v2-group-review-seed.csv"
CANDIDATE_V2_MAJORS = ROOT / "data/working/issue19-candidate-v2-major-review-seed.csv"

GROUP_OUTPUT = ROOT / "data/working/issue19-candidate-v2-verification-group-workbench.csv"
MAJOR_OUTPUT = ROOT / "data/working/issue19-candidate-v2-verification-major-workbench.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v2-verification-workbench-summary.json"

PENDING_PDF_STATUS = "pending_original_pdf_page_review"
PENDING_HUBEI_STATUS = "pending_hubei_official_plan_review"
PENDING_CHARTER_STATUS = "pending_school_charter_review"
PENDING_FAMILY_STATUS = "pending_family_acceptance_review"
PENDING_TRANSFER_STATUS = "pending_transfer_decision"
PENDING_GATE_STATUS = "pending_verification"
NOT_REVIEWED = "false"

STRUCTURE_ANOMALY_IDS = {
    "major_text_embeds_other_school_marker",
    "major_text_embeds_group_code",
    "major_text_embeds_page_header",
    "major_code_not_two_chars",
    "plan_count_number_ge_1000",
    "plan_count_not_plain_number",
    "tuition_number_le_500",
    "tuition_not_plain_number",
    "low_ocr_confidence",
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


def suspicious_tuition(row):
    field_flags = split_tags(row.get("字段完整性标记", ""))
    anomaly_rules = split_tags(row.get("结构异常规则ID", ""))
    tuition_text = row.get("学费候选", "")
    return (
        not tuition_text.isdigit()
        or "tuition_not_plain_number" in field_flags
        or "tuition_not_plain_number" in anomaly_rules
        or "tuition_number_le_500" in anomaly_rules
    )


def major_machine_acceptance(row):
    tags = split_tags(row.get("偏好和风险标签", ""))
    anomaly_rules = split_tags(row.get("结构异常规则ID", ""))
    risk_tags = tags & set(RISK_TAG_LABELS)
    preference_tags = tags & set(PREFERENCE_TAG_LABELS)

    if "rejected_medical" in risk_tags:
        return "默认不能接受", "命中医学/护理等当前明确排除方向"
    if {"high_fee_or_coop", "tuition_over_15000"} & risk_tags:
        return "默认不进主方案", "命中中外合作/高收费或超过当前家庭费用上限"
    if suspicious_tuition(row):
        return "费用待原页核验", "学费字段非纯数字或疑似截断，不能直接用于预算判断"
    if {"body_or_exam_limit", "language_or_single_subject", "special_plan_or_direction"} & risk_tags:
        return "限制风险待核验", f"命中限制类风险：{risk_labels(risk_tags)}"
    if anomaly_rules & STRUCTURE_ANOMALY_IDS:
        return "字段异常待核验", "命中 OCR 结构异常，需回看原页"
    if preference_tags:
        return "重点了解", labels_for(preference_tags, PREFERENCE_TAG_LABELS)
    return "待了解", "尚未命中明确偏好或硬排除，需要家庭继续判断"


def major_field_review_status(row):
    if row.get("证据来源") == "page_visual_review_seed":
        return "pending_page_visual_field_review"
    if row.get("结构异常规则ID") or row.get("字段完整性标记"):
        return "pending_ocr_anomaly_field_review"
    return "pending_ocr_field_review"


def transfer_blocker_from_acceptance(acceptance):
    if acceptance in {"默认不能接受", "默认不进主方案"}:
        return "是"
    return "待判断"


def historical_line_policy(group_row, *, zero_detail):
    relation_type = group_row.get("关联类型", "")
    code = group_row["2026院校专业组代码"]
    if zero_detail:
        return "false", "group_not_found_or_code_changed", "当前第19期页码和结构化表均无可用专业明细"
    if relation_type != "历史候选":
        return "false", "pending_new_group_evidence", "非历史候选补充组不能沿用原候选历史投档线"
    if code == "C10704":
        return "pending", "pending_structured_group_repair", "页面可见但结构化漏拆，需先确认2026组号与历史线对应关系"
    return "pending", "historical_candidate_pending_2026_confirmation", "需确认2026专业组与历史投档组稳定对应后再使用历史线"


def group_transfer_machine(majors, *, zero_detail, risk_labels_text, field_anomaly_count):
    if zero_detail:
        return "不可判断：当前无专业明细，需先定位2026专业组或补齐组内专业"
    if any(row["专业接受度机器初判"] == "默认不能接受" for row in majors):
        return "默认不可服从：组内含当前明确不能接受专业"
    if any(row["专业接受度机器初判"] == "默认不进主方案" for row in majors):
        return "默认不可服从：组内含高收费/中外合作/超预算风险"
    if any(row["专业接受度机器初判"] == "限制风险待核验" for row in majors):
        return "暂不可判断：组内含体检、色觉、语种、单科或特殊类型限制"
    if field_anomaly_count:
        return "暂不可判断：组内存在 OCR 字段或结构异常"
    if risk_labels_text:
        return f"暂不可判断：需复核风险标签 {risk_labels_text}"
    return "待家庭逐专业确认：当前未触发默认排除，但仍未完成调剂判断"


def group_priority(row, *, zero_detail, field_anomaly_count, risk_tags, preference_tags):
    code = row["2026院校专业组代码"]
    if zero_detail or code in {"C10704", "K15123", "C10702"}:
        return "P0-组号定位和页图边界"
    if field_anomaly_count or {"rejected_medical", "high_fee_or_coop", "tuition_over_15000"} & risk_tags:
        return "P1-风险或字段异常"
    if {"body_or_exam_limit", "language_or_single_subject", "special_plan_or_direction"} & risk_tags:
        return "P1-限制条件核验"
    if preference_tags:
        return "P2-偏好专业复核"
    return "P3-常规复核"


def main():
    preferences = json.loads(FAMILY_PREFERENCES.read_text())
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]
    tuition_limit = int(preferences["budget"]["annual_upper_limit_yuan"])

    group_seed_rows = read_csv(CANDIDATE_V2_GROUPS)
    major_seed_rows = read_csv(CANDIDATE_V2_MAJORS)
    majors_by_group = defaultdict(list)
    for row in major_seed_rows:
        majors_by_group[row["2026院校专业组代码"]].append(row)

    major_output_rows = []
    major_workbench_by_group = defaultdict(list)
    for row in major_seed_rows:
        acceptance, reason = major_machine_acceptance(row)
        tags = split_tags(row.get("偏好和风险标签", ""))
        risk_tags = tags & set(RISK_TAG_LABELS)
        preference_tags = tags & set(PREFERENCE_TAG_LABELS)
        gaps = [
            "原PDF页字段核验",
            "湖北官方计划字段核验",
            "高校章程字段核验",
            "家庭专业接受度确认",
        ]
        if row.get("结构异常规则ID") or row.get("字段完整性标记"):
            gaps.append("OCR异常修正")
        if suspicious_tuition(row):
            gaps.append("学费原页/章程核验")

        output = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "candidate_v2_verification_workbench",
            "最终可用": "false",
            "关联类型": row["关联类型"],
            "关联原候选": row["关联原候选"],
            "2026院校专业组代码": row["2026院校专业组代码"],
            "组内序号": row["组内序号"],
            "证据来源": row["证据来源"],
            "院校代码": row["院校代码"],
            "院校名称OCR": row["院校名称OCR"],
            "来源页码": row["来源页码"],
            "页图文件名": row["页图文件名"],
            "专业组名称": row["专业组名称"],
            "专业代号": row["专业代号"],
            "专业名称及备注": row["专业名称及备注"],
            "再选科目候选": row["再选科目候选"],
            "专业计划数候选": row["专业计划数候选"],
            "学费候选": row["学费候选"],
            "学费数字候选": row["学费数字候选"],
            "偏好方向": labels_for(preference_tags, PREFERENCE_TAG_LABELS),
            "风险类型": risk_labels(risk_tags),
            "字段完整性标记": row["字段完整性标记"],
            "结构异常规则ID": row["结构异常规则ID"],
            "结构异常类型": row["结构异常类型"],
            "专业接受度机器初判": acceptance,
            "机器初判原因": reason,
            "专业接受度人工确认": "pending_family_acceptance_review",
            "专业闸门状态": PENDING_GATE_STATUS,
            "专业字段复核状态": major_field_review_status(row),
            "专业代号核验状态": "pending",
            "专业名称核验状态": "pending",
            "计划数核验状态": "pending",
            "学费核验状态": "pending",
            "选科核验状态": "pending",
            "备注核验状态": "pending",
            "原PDF页字段核验状态": PENDING_PDF_STATUS,
            "湖北官方系统字段核验状态": PENDING_HUBEI_STATUS,
            "高校章程字段核验状态": PENDING_CHARTER_STATUS,
            "是否可能导致不能服从调剂": transfer_blocker_from_acceptance(acceptance),
            "是否允许进入最终专业列表": "false",
            "阻断原因": reason if acceptance in {"默认不能接受", "默认不进主方案"} else "",
            "风险说明": risk_labels(risk_tags) if risk_tags else "",
            "升级缺口": "；".join(gaps),
            "下一步": "逐字段回看原页；核湖北官方计划和高校章程；由家庭确认专业接受度",
        }
        major_output_rows.append(output)
        major_workbench_by_group[row["2026院校专业组代码"]].append(output)

    group_output_rows = []
    for row in group_seed_rows:
        code = row["2026院校专业组代码"]
        majors = major_workbench_by_group.get(code, [])
        seed_majors = majors_by_group.get(code, [])
        zero_detail = len(majors) == 0
        all_tags = {
            tag
            for major in seed_majors
            for tag in split_tags(major.get("偏好和风险标签", ""))
        }
        risk_tags = all_tags & set(RISK_TAG_LABELS)
        preference_tags = all_tags & set(PREFERENCE_TAG_LABELS)
        field_anomaly_count = sum(
            bool(major.get("字段完整性标记") or major.get("结构异常规则ID"))
            for major in seed_majors
        )
        suspicious_tuition_count = sum(suspicious_tuition(major) for major in seed_majors)
        default_rejected_count = sum(
            major["专业接受度机器初判"] == "默认不能接受" for major in majors
        )
        default_not_main_count = sum(
            major["专业接受度机器初判"] == "默认不进主方案" for major in majors
        )
        pending_acceptance_count = sum(
            major["专业接受度机器初判"] in {"待了解", "重点了解", "限制风险待核验", "字段异常待核验", "费用待原页核验"}
            for major in majors
        )
        risk_labels_text = risk_labels(risk_tags)
        transfer_machine = group_transfer_machine(
            majors,
            zero_detail=zero_detail,
            risk_labels_text=risk_labels_text,
            field_anomaly_count=field_anomaly_count,
        )
        historical_reuse_allowed, baseline_score_source, historical_line_note = historical_line_policy(row, zero_detail=zero_detail)
        gaps = [
            "原PDF页人工核验",
            "湖北官方系统/省招办计划核验",
            "高校官网/招生章程核验",
            "家庭逐专业接受度核验",
            "组内调剂结论",
            "三年投档稳定性复核",
        ]
        if zero_detail:
            gaps.append("2026组号定位或补齐专业明细")
        if field_anomaly_count:
            gaps.append("OCR结构异常修正")
        if suspicious_tuition_count:
            gaps.append("异常学费原页/章程核验")

        group_output_rows.append({
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "candidate_v2_verification_workbench",
            "最终可用": "false",
            "关联类型": row["关联类型"],
            "关联原候选": row["关联原候选"],
            "2026院校专业组代码": code,
            "院校代码": row["院校代码"],
            "院校名称": row["院校名称"],
            "来源页码": row["来源页码"],
            "页图文件名": row["页图文件名"],
            "证据来源": row["证据来源"],
            "结构化命中": row["结构化命中"],
            "专业明细行数": str(len(majors)),
            "零明细原因": "group_not_found_or_code_changed" if zero_detail else "",
            "V2定位结论": row["V2定位结论"],
            "偏好方向": labels_for(preference_tags, PREFERENCE_TAG_LABELS),
            "风险类型": risk_labels_text,
            "默认不能接受专业数": str(default_rejected_count),
            "默认不进主方案专业数": str(default_not_main_count),
            "待家庭确认专业数": str(pending_acceptance_count),
            "字段异常专业数": str(field_anomaly_count),
            "异常学费专业数": str(suspicious_tuition_count),
            "历史投档线可沿用": historical_reuse_allowed,
            "历史线基准来源": baseline_score_source,
            "历史线说明": historical_line_note,
            "原PDF页人工核验状态": PENDING_PDF_STATUS,
            "湖北官方系统/省招办计划核验状态": PENDING_HUBEI_STATUS,
            "高校官网/招生章程核验状态": PENDING_CHARTER_STATUS,
            "家庭接受度核验状态": PENDING_FAMILY_STATUS,
            "调剂结论状态": PENDING_TRANSFER_STATUS,
            "全部专业已复核": NOT_REVIEWED,
            "组内调剂机器初判": transfer_machine,
            "候选闸门状态": PENDING_GATE_STATUS,
            "可进入最终候选": "false",
            "当前复核优先级": group_priority(
                row,
                zero_detail=zero_detail,
                field_anomaly_count=field_anomaly_count,
                risk_tags=risk_tags,
                preference_tags=preference_tags,
            ),
            "升级缺口": "；".join(gaps),
            "下一步": "按升级缺口逐项补证据，未全部完成前不得进入冲稳保排序",
        })

    group_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "关联类型",
        "关联原候选",
        "2026院校专业组代码",
        "院校代码",
        "院校名称",
        "来源页码",
        "页图文件名",
        "证据来源",
        "结构化命中",
        "专业明细行数",
        "零明细原因",
        "V2定位结论",
        "偏好方向",
        "风险类型",
        "默认不能接受专业数",
        "默认不进主方案专业数",
        "待家庭确认专业数",
        "字段异常专业数",
        "异常学费专业数",
        "历史投档线可沿用",
        "历史线基准来源",
        "历史线说明",
        "原PDF页人工核验状态",
        "湖北官方系统/省招办计划核验状态",
        "高校官网/招生章程核验状态",
        "家庭接受度核验状态",
        "调剂结论状态",
        "全部专业已复核",
        "组内调剂机器初判",
        "候选闸门状态",
        "可进入最终候选",
        "当前复核优先级",
        "升级缺口",
        "下一步",
    ]
    major_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "关联类型",
        "关联原候选",
        "2026院校专业组代码",
        "组内序号",
        "证据来源",
        "院校代码",
        "院校名称OCR",
        "来源页码",
        "页图文件名",
        "专业组名称",
        "专业代号",
        "专业名称及备注",
        "再选科目候选",
        "专业计划数候选",
        "学费候选",
        "学费数字候选",
        "偏好方向",
        "风险类型",
        "字段完整性标记",
        "结构异常规则ID",
        "结构异常类型",
        "专业接受度机器初判",
        "机器初判原因",
        "专业接受度人工确认",
        "专业闸门状态",
        "专业字段复核状态",
        "专业代号核验状态",
        "专业名称核验状态",
        "计划数核验状态",
        "学费核验状态",
        "选科核验状态",
        "备注核验状态",
        "原PDF页字段核验状态",
        "湖北官方系统字段核验状态",
        "高校章程字段核验状态",
        "是否可能导致不能服从调剂",
        "是否允许进入最终专业列表",
        "阻断原因",
        "风险说明",
        "升级缺口",
        "下一步",
    ]
    write_csv(GROUP_OUTPUT, group_output_rows, group_fields)
    write_csv(MAJOR_OUTPUT, major_output_rows, major_fields)

    summary = {
        "status": "candidate_v2_verification_workbench_pending_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "candidate_v2_verification_workbench",
        "generated_by": "scripts/build_issue19_candidate_v2_verification_workbench.py",
        "inputs": input_snapshot(ROOT, [FAMILY_PREFERENCES, ISSUE19_SOURCE, CANDIDATE_V2_GROUPS, CANDIDATE_V2_MAJORS]),
        "group_count": len(group_output_rows),
        "major_count": len(major_output_rows),
        "group_can_enter_final_count": sum(row["可进入最终候选"] == "true" for row in group_output_rows),
        "major_can_enter_final_count": sum(row["是否允许进入最终专业列表"] == "true" for row in major_output_rows),
        "group_gate_status_counts": dict(Counter(row["候选闸门状态"] for row in group_output_rows)),
        "major_gate_status_counts": dict(Counter(row["专业闸门状态"] for row in major_output_rows)),
        "zero_detail_groups": sorted(
            row["2026院校专业组代码"]
            for row in group_output_rows
            if row["专业明细行数"] == "0"
        ),
        "group_priority_counts": dict(Counter(row["当前复核优先级"] for row in group_output_rows)),
        "group_transfer_machine_counts": dict(Counter(row["组内调剂机器初判"] for row in group_output_rows)),
        "major_machine_acceptance_counts": dict(Counter(row["专业接受度机器初判"] for row in major_output_rows)),
        "pending_gate_statuses": {
            "原PDF页人工核验状态": PENDING_PDF_STATUS,
            "湖北官方系统/省招办计划核验状态": PENDING_HUBEI_STATUS,
            "高校官网/招生章程核验状态": PENDING_CHARTER_STATUS,
            "家庭接受度核验状态": PENDING_FAMILY_STATUS,
            "调剂结论状态": PENDING_TRANSFER_STATUS,
        },
        "tuition_limit_yuan": tuition_limit,
        "outputs": [
            str(GROUP_OUTPUT.relative_to(ROOT)),
            str(MAJOR_OUTPUT.relative_to(ROOT)),
        ],
        "notes": [
            "本工作台是升级闸门，不是最终志愿表。",
            "所有行保持最终可用=false，且可进入最终候选=false。",
            "只有完成原PDF页、湖北官方计划/系统、高校章程、家庭接受度、调剂结论和三年投档稳定性复核后，才能另行升级。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出候选V2专业组升级工作台：{GROUP_OUTPUT}")
    print(f"写出候选V2专业明细升级工作台：{MAJOR_OUTPUT}")
    print(f"写出候选V2升级工作台摘要：{SUMMARY_OUTPUT}")
    print(f"专业组数：{len(group_output_rows)}")
    print(f"专业明细数：{len(major_output_rows)}")


if __name__ == "__main__":
    main()
