#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import (
    DEFAULT_EXCLUDE_RISK_TAGS,
    PAUSE_REVIEW_RISK_TAGS,
    PREFERENCE_TAG_LABELS,
    RISK_TAG_LABELS,
    as_int,
    input_snapshot,
    risk_labels,
    review_risk_tags,
    split_tags,
)


ROOT = Path(__file__).resolve().parents[1]
FAMILY_PREFERENCES = ROOT / "data/working/family-preferences.json"
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
CANDIDATE_COVERAGE = ROOT / "data/working/issue19-full-admission-plan-candidate-coverage.csv"
FULL_GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-plan-review-summary.csv"
MAJOR_DETAIL_OUTPUT = ROOT / "data/working/issue19-candidate-plan-review-major-detail.csv"
QUEUE_OUTPUT = ROOT / "data/working/issue19-priority-review-queue.csv"
JSON_SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-plan-review-summary.json"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None):
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def classify_candidate(*, coverage, majors, tuition_limit):
    if coverage["第19期全量OCR命中"] != "是":
        return "待定位", "未在第19期全量OCR初稿命中，需核对2026组号变化、OCR漏识别或历史组调整"

    historical_risk = coverage.get("历史风险初判", "")
    max_tuition = 0
    all_review_risk_tags = set()
    preferred_count = 0
    incomplete_count = 0
    for major in majors:
        tags = split_tags(major.get("偏好和风险标签", ""))
        tuition = as_int(major.get("学费OCR数字候选"))
        if tuition and tuition > max_tuition:
            max_tuition = tuition
        all_review_risk_tags |= review_risk_tags(tags, tuition, tuition_limit)
        if tags & set(PREFERENCE_TAG_LABELS):
            preferred_count += 1
        if major.get("字段完整性标记"):
            incomplete_count += 1

    if "主方案排除" in historical_risk:
        return "默认排除", "历史候选池已标记为主方案排除/历史样本"
    if all_review_risk_tags & DEFAULT_EXCLUDE_RISK_TAGS or max_tuition > tuition_limit:
        return "默认排除", "含中外合作/高收费或学费超过当前家庭上限"
    if all_review_risk_tags & PAUSE_REVIEW_RISK_TAGS:
        return "高风险暂缓", f"组内含需优先复核风险：{risk_labels(all_review_risk_tags)}"
    if incomplete_count > 0:
        return "可复核但字段不完整", "OCR 字段存在缺失或非纯数字，需先回看原 PDF 页"
    if preferred_count > 0:
        return "优先人工复核", "命中当前优先专业方向且未触发硬排除"
    return "可人工复核", "未触发硬排除，但需确认组内全部专业接受度"


def main():
    preferences = json.loads(FAMILY_PREFERENCES.read_text())
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]
    tuition_limit = int(preferences["budget"]["annual_upper_limit_yuan"])
    rejected_directions = set(preferences["major_preference"]["rejected_directions"])

    coverage_rows = read_csv(CANDIDATE_COVERAGE)
    group_rows = read_csv(FULL_GROUPS)
    major_rows = read_csv(FULL_MAJORS)

    groups_by_code = {row["院校专业组代码OCR规范化"]: row for row in group_rows}
    majors_by_group = defaultdict(list)
    for row in major_rows:
        majors_by_group[row["院校专业组代码OCR规范化"]].append(row)

    summary_rows = []
    detail_rows = []
    queue_rows = []
    overall_risk_type_counter = Counter()

    for index, coverage in enumerate(coverage_rows, start=1):
        group_code = coverage["候选专业组代码OCR规范化"]
        group = groups_by_code.get(group_code, {})
        majors = majors_by_group.get(group_code, [])
        decision, decision_reason = classify_candidate(
            coverage=coverage,
            majors=majors,
            tuition_limit=tuition_limit,
        )

        tag_counter = Counter()
        review_risk_type_counter = Counter()
        hard_risk_major_count = 0
        hard_risk_tag_hit_count = 0
        hard_risk_types = set()
        max_tuition = 0
        missing_subject = 0
        missing_plan = 0
        missing_tuition = 0
        for major in majors:
            tags = split_tags(major.get("偏好和风险标签", ""))
            tag_counter.update(tags)
            tuition = as_int(major.get("学费OCR数字候选"))
            if tuition and tuition > max_tuition:
                max_tuition = tuition
            review_tags = review_risk_tags(tags, tuition, tuition_limit)
            if review_tags:
                hard_risk_major_count += 1
                hard_risk_tag_hit_count += len(review_tags)
                hard_risk_types |= review_tags
                review_risk_type_counter.update(review_tags)
                overall_risk_type_counter.update(review_tags)
            flags = split_tags(major.get("字段完整性标记", ""))
            missing_subject += "missing_subject_candidate" in flags
            missing_plan += "missing_plan_count_candidate" in flags
            missing_tuition += "missing_tuition_candidate" in flags

        preferred_hit_count = sum(tag_counter[tag] for tag in PREFERENCE_TAG_LABELS)

        summary_rows.append({
            "序号": index,
            "来源期号": group.get("来源期号", source_issue),
            "来源PDF_SHA256": group.get("来源PDF_SHA256", source_pdf_sha256),
            "数据阶段": "candidate_review_workbench_ocr_draft",
            "候选池学校专业组": coverage["候选池学校专业组"],
            "城市": coverage["城市"],
            "候选专业组代码": group_code,
            "第19期全量OCR命中": coverage["第19期全量OCR命中"],
            "第19期OCR院校名称": coverage["第19期OCR院校名称"],
            "第19期OCR页码": coverage["第19期OCR页码"],
            "历史年份覆盖": coverage["年份覆盖"],
            "2023最低分": coverage["2023最低分"],
            "2024最低分": coverage["2024最低分"],
            "2025最低分": coverage["2025最低分"],
            "历史风险初判": coverage["历史风险初判"],
            "OCR专业行数": str(len(majors)),
            "最大年学费OCR数字候选": str(max_tuition) if max_tuition else "",
            "优先专业命中数": str(preferred_hit_count),
            "硬风险专业行数": str(hard_risk_major_count),
            "硬风险标签命中数": str(hard_risk_tag_hit_count),
            "硬风险类型": risk_labels(hard_risk_types),
            "医学护理等风险专业行数": str(review_risk_type_counter["rejected_medical"]),
            "中外合作高收费专业行数": str(review_risk_type_counter["high_fee_or_coop"]),
            "学费超过上限专业行数": str(review_risk_type_counter["tuition_over_15000"]),
            "体检或色觉限制专业行数": str(review_risk_type_counter["body_or_exam_limit"]),
            "语种或单科限制专业行数": str(review_risk_type_counter["language_or_single_subject"]),
            "专项预科定向等特殊类型专业行数": str(review_risk_type_counter["special_plan_or_direction"]),
            "数字媒体技术命中数": str(tag_counter["priority_1_digital_media"]),
            "计算机相关命中数": str(tag_counter["priority_2_computer"]),
            "师范相关命中数": str(tag_counter["priority_3_teacher"]),
            "缺再选科目候选专业数": str(missing_subject),
            "缺计划数候选专业数": str(missing_plan),
            "缺学费候选专业数": str(missing_tuition),
            "家庭费用上限": str(tuition_limit),
            "明确不接受方向": "；".join(sorted(rejected_directions)),
            "机器初判": decision,
            "初判原因": decision_reason,
            "核验状态": "needs_manual_pdf_review" if coverage["第19期全量OCR命中"] == "是" else "needs_original_page_or_code_change_review",
            "下一步": "回看第19期原PDF页并核学校官网/章程" if coverage["第19期全量OCR命中"] == "是" else "核对2026组号变化、OCR漏识别或历史组调整",
        })

        for major_index, major in enumerate(majors, start=1):
            detail_rows.append({
                "来源期号": major["来源期号"],
                "来源PDF_SHA256": major["来源PDF_SHA256"],
                "数据阶段": "candidate_review_workbench_ocr_draft",
                "候选池学校专业组": coverage["候选池学校专业组"],
                "候选专业组代码": group_code,
                "机器初判": decision,
                "组内序号": major_index,
                "院校代码": major["院校代码"],
                "院校名称OCR": major["院校名称OCR"],
                "来源页码": major["来源页码"],
                "专业代号OCR": major["专业代号OCR"],
                "专业名称及备注OCR": major["专业名称及备注OCR"],
                "再选科目OCR候选": major["再选科目OCR候选"],
                "专业计划数OCR候选": major["专业计划数OCR候选"],
                "学费OCR候选": major["学费OCR候选"],
                "学费OCR数字候选": major["学费OCR数字候选"],
                "偏好和风险标签": major["偏好和风险标签"],
                "字段完整性标记": major["字段完整性标记"],
                "核验状态": major["核验状态"],
                "最终可用": major["最终可用"],
            })

        priority = 0
        if decision == "待定位":
            priority = 100
        elif decision == "默认排除":
            priority = 90
        elif decision == "高风险暂缓":
            priority = 80
        elif decision == "优先人工复核":
            priority = 70
        elif decision == "可复核但字段不完整":
            priority = 60
        else:
            priority = 50
        queue_rows.append({
            "复核优先级": priority,
            "来源期号": group.get("来源期号", source_issue),
            "来源PDF_SHA256": group.get("来源PDF_SHA256", source_pdf_sha256),
            "数据阶段": "candidate_review_workbench_ocr_draft",
            "候选池学校专业组": coverage["候选池学校专业组"],
            "候选专业组代码": group_code,
            "机器初判": decision,
            "初判原因": decision_reason,
            "硬风险类型": risk_labels(hard_risk_types),
            "第19期全量OCR命中": coverage["第19期全量OCR命中"],
            "第19期OCR页码": coverage["第19期OCR页码"],
            "OCR专业行数": str(len(majors)),
            "下一步": "先复核" if priority >= 70 else "排队复核",
        })

    queue_rows.sort(key=lambda row: (-int(row["复核优先级"]), row["候选池学校专业组"]))

    write_csv(SUMMARY_OUTPUT, summary_rows)
    write_csv(MAJOR_DETAIL_OUTPUT, detail_rows)
    write_csv(QUEUE_OUTPUT, queue_rows)

    json_summary = {
        "status": "candidate_review_workbench_needs_manual_pdf_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "candidate_review_workbench_ocr_draft",
        "generated_by": "scripts/build_issue19_candidate_review_workbench.py",
        "inputs": input_snapshot(ROOT, [FAMILY_PREFERENCES, CANDIDATE_COVERAGE, FULL_GROUPS, FULL_MAJORS]),
        "candidate_count": len(summary_rows),
        "matched_candidate_count": sum(row["第19期全量OCR命中"] == "是" for row in summary_rows),
        "unmatched_candidate_count": sum(row["第19期全量OCR命中"] != "是" for row in summary_rows),
        "machine_decision_counts": dict(Counter(row["机器初判"] for row in summary_rows)),
        "candidate_major_detail_count": len(detail_rows),
        "candidate_hard_risk_major_counts_by_type": {
            RISK_TAG_LABELS[tag]: overall_risk_type_counter[tag]
            for tag in sorted(RISK_TAG_LABELS)
            if overall_risk_type_counter[tag]
        },
        "tuition_limit_yuan": tuition_limit,
        "outputs": [
            str(SUMMARY_OUTPUT.relative_to(ROOT)),
            str(MAJOR_DETAIL_OUTPUT.relative_to(ROOT)),
            str(QUEUE_OUTPUT.relative_to(ROOT)),
        ],
        "output_row_counts": {
            str(SUMMARY_OUTPUT.relative_to(ROOT)): len(summary_rows),
            str(MAJOR_DETAIL_OUTPUT.relative_to(ROOT)): len(detail_rows),
            str(QUEUE_OUTPUT.relative_to(ROOT)): len(queue_rows),
        },
        "notes": [
            "机器初判只用于复核优先级，不是最终志愿建议。",
            "所有候选仍需回看第19期原PDF页，核对组边界、组内全部专业、计划数、学费、选科和备注。",
            "服从调剂判断必须覆盖院校专业组内全部专业。",
        ],
    }
    JSON_SUMMARY_OUTPUT.write_text(json.dumps(json_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出候选组级复核表：{SUMMARY_OUTPUT}")
    print(f"写出候选专业明细表：{MAJOR_DETAIL_OUTPUT}")
    print(f"写出复核优先队列：{QUEUE_OUTPUT}")
    print(f"写出摘要：{JSON_SUMMARY_OUTPUT}")
    print(f"候选数：{len(summary_rows)}")
    print(f"命中候选数：{json_summary['matched_candidate_count']}")
    print(f"候选专业明细行数：{len(detail_rows)}")


if __name__ == "__main__":
    main()
