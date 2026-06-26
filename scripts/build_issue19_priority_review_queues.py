#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

from issue19_review_rules import (
    GROUP_REVIEW_RISK_TAGS,
    PREFERENCE_TAG_LABELS,
    RISK_LEVEL_ORDER,
    as_int,
    combine_risk_levels,
    input_snapshot,
    review_risk_tags,
    risk_labels,
    risk_level,
    split_tags,
)


ROOT = Path(__file__).resolve().parents[1]
FAMILY_PREFERENCES = ROOT / "data/working/family-preferences.json"
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
FULL_GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
PREFERENCE_OUTPUT = ROOT / "data/working/issue19-preference-major-search.csv"
RISK_OUTPUT = ROOT / "data/working/issue19-hard-risk-group-review-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-priority-review-queues-summary.json"


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


def main():
    preferences = json.loads(FAMILY_PREFERENCES.read_text())
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]
    tuition_limit = int(preferences["budget"]["annual_upper_limit_yuan"])

    group_rows = read_csv(FULL_GROUPS)
    major_rows = read_csv(FULL_MAJORS)
    group_review_tags_by_code = {
        row["院校专业组代码OCR规范化"]: review_risk_tags(split_tags(row.get("偏好和风险标签", "")))
        for row in group_rows
    }

    preference_rows = []
    preference_counter = Counter()
    for row in major_rows:
        tags = split_tags(row.get("偏好和风险标签", ""))
        matched_preferences = tags & set(PREFERENCE_TAG_LABELS)
        if not matched_preferences:
            continue
        tuition = as_int(row.get("学费OCR数字候选"))
        major_review_tags = review_risk_tags(tags, tuition, tuition_limit)
        group_review_tags = group_review_tags_by_code.get(row["院校专业组代码OCR规范化"], set())
        major_level = risk_level(major_review_tags)
        group_level = risk_level(group_review_tags)
        combined_level = combine_risk_levels(major_level, group_level)
        for tag in matched_preferences:
            preference_counter[tag] += 1
        preference_rows.append({
            "来源期号": row["来源期号"],
            "来源PDF_SHA256": row["来源PDF_SHA256"],
            "数据阶段": "priority_review_queue_ocr_draft",
            "优先方向": "；".join(PREFERENCE_TAG_LABELS[tag] for tag in sorted(matched_preferences)),
            "综合风险等级": combined_level,
            "本专业OCR风险等级": major_level,
            "本专业风险类型": risk_labels(major_review_tags),
            "专业组风险类型": risk_labels(group_review_tags),
            "院校代码": row["院校代码"],
            "院校名称OCR": row["院校名称OCR"],
            "院校专业组代码": row["院校专业组代码OCR规范化"],
            "专业组号": row["专业组号OCR"],
            "来源页码": row["来源页码"],
            "专业代号OCR": row["专业代号OCR"],
            "专业名称及备注OCR": row["专业名称及备注OCR"],
            "再选科目OCR候选": row["再选科目OCR候选"],
            "专业计划数OCR候选": row["专业计划数OCR候选"],
            "学费OCR候选": row["学费OCR候选"],
            "学费OCR数字候选": row["学费OCR数字候选"],
            "偏好和风险标签": row["偏好和风险标签"],
            "字段完整性标记": row["字段完整性标记"],
            "候选池V1命中": row["候选池V1命中"],
            "样本学校命中": row["样本学校命中"],
            "核验状态": row["核验状态"],
            "最终可用": row["最终可用"],
            "下一步": "回看第19期原PDF页；核专业组内全部专业；再判断是否可服从调剂",
        })
    preference_rows.sort(key=lambda row: (
        RISK_LEVEL_ORDER.get(row["综合风险等级"], 9),
        row["优先方向"],
        row["院校代码"],
        row["院校专业组代码"],
        row["专业代号OCR"],
    ))

    risk_rows = []
    for row in group_rows:
        tags = split_tags(row.get("偏好和风险标签", ""))
        group_review_tags = tags & GROUP_REVIEW_RISK_TAGS
        if not group_review_tags:
            continue
        risk_rows.append({
            "来源期号": row["来源期号"],
            "来源PDF_SHA256": row["来源PDF_SHA256"],
            "数据阶段": "hard_risk_group_review_queue_ocr_draft",
            "综合风险等级": risk_level(group_review_tags),
            "风险类型": risk_labels(group_review_tags),
            "院校代码": row["院校代码"],
            "院校名称OCR": row["院校名称OCR"],
            "院校专业组代码": row["院校专业组代码OCR规范化"],
            "来源页码": row["来源页码"],
            "OCR专业行数": row["OCR专业行数"],
            "再选科目OCR候选": row["再选科目OCR候选"],
            "人数OCR候选": row["人数OCR候选"],
            "学费OCR候选": row["学费OCR候选"],
            "偏好和风险标签": row["偏好和风险标签"],
            "字段完整性标记": row["字段完整性标记"],
            "候选池V1命中": row["候选池V1命中"],
            "样本学校命中": row["样本学校命中"],
            "核验状态": row["核验状态"],
            "最终可用": row["最终可用"],
            "下一步": "风险标签必须人工复核；进入最终表前需证明组内调剂可接受",
        })
    risk_rows.sort(key=lambda row: (
        row["候选池V1命中"] != "是",
        row["风险类型"],
        row["院校代码"],
        row["院校专业组代码"],
    ))

    write_csv(PREFERENCE_OUTPUT, preference_rows)
    write_csv(RISK_OUTPUT, risk_rows)

    risk_counter = Counter()
    for row in risk_rows:
        for risk in row["风险类型"].split("；"):
            if risk:
                risk_counter[risk] += 1
    preference_risk_counter = Counter(row["综合风险等级"] for row in preference_rows)
    preference_major_only_risk_counter = Counter(row["本专业OCR风险等级"] for row in preference_rows)

    summary = {
        "status": "priority_review_queues_need_manual_pdf_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "priority_review_queue_ocr_draft",
        "generated_by": "scripts/build_issue19_priority_review_queues.py",
        "inputs": input_snapshot(ROOT, [FAMILY_PREFERENCES, FULL_GROUPS, FULL_MAJORS]),
        "preference_major_count": len(preference_rows),
        "preference_counts": {
            PREFERENCE_TAG_LABELS[tag]: preference_counter[tag]
            for tag in sorted(PREFERENCE_TAG_LABELS)
        },
        "preference_comprehensive_risk_level_counts": dict(preference_risk_counter),
        "preference_major_only_risk_level_counts": dict(preference_major_only_risk_counter),
        "preference_rows_with_group_risk_count": sum(
            bool(row["专业组风险类型"]) for row in preference_rows
        ),
        "hard_risk_group_count": len(risk_rows),
        "hard_risk_type_counts": dict(risk_counter),
        "tuition_limit_yuan": tuition_limit,
        "outputs": [
            str(PREFERENCE_OUTPUT.relative_to(ROOT)),
            str(RISK_OUTPUT.relative_to(ROOT)),
        ],
        "output_row_counts": {
            str(PREFERENCE_OUTPUT.relative_to(ROOT)): len(preference_rows),
            str(RISK_OUTPUT.relative_to(ROOT)): len(risk_rows),
        },
        "notes": [
            "优先专业检索队列只用于发现方向，不代表专业组可填。",
            "综合风险等级合并本专业行风险和所在院校专业组风险，避免把组内可调剂风险误判为安全。",
            "硬风险队列用于防止误服从调剂，风险标签必须回看第19期原PDF页确认。",
            "所有行仍为 OCR 初稿，最终可用均应为 false。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出优先专业检索队列：{PREFERENCE_OUTPUT}")
    print(f"写出硬风险专业组队列：{RISK_OUTPUT}")
    print(f"写出摘要：{SUMMARY_OUTPUT}")
    print(f"优先专业行数：{len(preference_rows)}")
    print(f"硬风险专业组数：{len(risk_rows)}")


if __name__ == "__main__":
    main()
