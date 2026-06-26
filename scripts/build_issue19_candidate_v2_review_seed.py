#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import (
    PREFERENCE_TAG_LABELS,
    RISK_TAG_LABELS,
    input_snapshot,
    risk_labels,
    split_tags,
)


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
CANDIDATE_SUMMARY = ROOT / "data/working/issue19-candidate-plan-review-summary.csv"
CANDIDATE_PAGE_AUDIT = ROOT / "data/working/issue19-candidate-page-code-audit.csv"
CANDIDATE_GROUP_PAGE_MAP = ROOT / "data/working/issue19-candidate-review-group-page-map.csv"
FULL_GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
STRUCTURE_ANOMALIES = ROOT / "data/working/issue19-ocr-structure-anomaly-queue.csv"

GROUP_OUTPUT = ROOT / "data/working/issue19-candidate-v2-group-review-seed.csv"
MAJOR_OUTPUT = ROOT / "data/working/issue19-candidate-v2-major-review-seed.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v2-review-seed-summary.json"


MANUAL_PAGE_SEEDS = [
    {
        "group_code": "C10703",
        "school_code": "C107",
        "school_name": "武汉体育学院",
        "group_name": "武汉体育学院第03组",
        "page": "69",
        "page_image_file": "page-069.png",
        "source_type": "page_visual_review_seed",
        "relation_type": "历史候选页图重切组",
        "source_candidate": "武汉体育学院 C10703 第03组",
        "group_subject": "不限",
        "group_plan": "53",
        "page_evidence": "页图第69页右栏；页面OCR第193-200行；C10703后至C10704前",
        "majors": [
            ("05", "运动康复", "不限", "10", "5200"),
            ("06", "应用心理学", "不限", "6", "4000"),
            ("07", "智能体育工程", "不限", "8", "4000"),
            ("08", "教育技术学", "不限", "2", "4000"),
            ("09", "信息管理与信息系统", "不限", "12", "4000"),
            ("10", "体育经济与管理", "不限", "9", "4000"),
            ("11", "新闻学", "不限", "6", "5200"),
        ],
        "review_note": "页图显示第03组为不限、合计53人；全量OCR把C10704部分专业误并入C10703，必须按页图重核。",
    },
    {
        "group_code": "C10704",
        "school_code": "C107",
        "school_name": "武汉体育学院",
        "group_name": "武汉体育学院第04组",
        "page": "69",
        "page_image_file": "page-069.png",
        "source_type": "page_visual_review_seed",
        "relation_type": "历史候选结构化漏拆补种",
        "source_candidate": "武汉体育学院 C10704 第04组",
        "group_subject": "化学",
        "group_plan": "20",
        "page_evidence": "页图第69页右栏；页面OCR第201-204行；C10704后至C10705前",
        "majors": [
            ("12", "中医骨伤科学（学制：五年）", "化学", "6", "5200"),
            ("13", "康复治疗学", "化学", "7", "5200"),
            ("14", "数据科学与大数据技术", "化学", "7", "4000"),
        ],
        "review_note": "页图和页面OCR均出现C10704，但全量专业组表未拆出；先按页图写入复核种子，不直接作为最终事实。",
    },
    {
        "group_code": "C10705",
        "school_code": "C107",
        "school_name": "武汉体育学院",
        "group_name": "武汉体育学院第05组",
        "page": "69",
        "page_image_file": "page-069.png",
        "source_type": "page_visual_review_seed",
        "relation_type": "同页相邻风险组",
        "source_candidate": "武汉体育学院 C10703/C10704 同页边界复核",
        "group_subject": "化学",
        "group_plan": "7",
        "page_evidence": "页图第69页右栏；页面OCR第205-206行；C10705后至C108前",
        "majors": [
            ("15", "康复治疗学（中外合作办学）", "化学", "7", "48000"),
        ],
        "review_note": "页图显示C10705为中外合作高收费医学相关风险组；用于说明同页边界，不进入主方案。",
    },
    {
        "group_code": "K15114",
        "school_code": "K151",
        "school_name": "成都理工大学",
        "group_name": "成都理工大学第14组",
        "page": "208",
        "page_image_file": "page-208.png",
        "source_type": "page_visual_review_seed",
        "relation_type": "同校偏好专业补充组",
        "source_candidate": "成都理工大学 K15123 第23组",
        "group_subject": "化学",
        "group_plan": "8",
        "page_evidence": "页图第208页右栏；页面OCR第190-197行；K15114后至K15115前",
        "majors": [
            ("53", "数字媒体技术（不能准确在显示器上识别红、黄、绿、蓝、紫各颜色中任何一种颜色的数码、字母者不能录取；宜宾校区就读）", "化学", "2", "6240"),
            ("54", "智能科学与技术（宜宾校区）", "化学", "4", "6240"),
            ("55", "电子信息工程（宜宾校区）", "化学", "2", "6240"),
        ],
        "review_note": "K15123在第208/209页未见；K15114是同校2026计划中的数字媒体技术相关组，但不能沿用K15123历史投档线。",
    },
]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def tag_major(name, tuition):
    tags = set()
    if "数字媒体技术" in name:
        tags.add("priority_1_digital_media")
    if any(keyword in name for keyword in ["计算机", "软件", "数据科学", "大数据", "智能科学", "人工智能"]):
        tags.add("priority_2_computer")
    if any(keyword in name for keyword in ["教育技术", "师范"]):
        tags.add("priority_3_teacher")
    if any(keyword in name for keyword in ["医学", "中医", "康复", "护理", "药学", "治疗"]):
        tags.add("rejected_medical")
    if "中外合作" in name or "高收费" in name:
        tags.add("high_fee_or_coop")
    if any(keyword in name for keyword in ["色盲", "色弱", "不能准确", "单色识别"]):
        tags.add("body_or_exam_limit")
    if any(keyword in name for keyword in ["英语", "单科"]):
        tags.add("language_or_single_subject")
    if tuition and tuition > 15000:
        tags.add("tuition_over_15000")
    return tags


def labels_for(tags, mapping):
    return "；".join(mapping[tag] for tag in sorted(tags) if tag in mapping)


def anomaly_key(row):
    return (row["院校专业组代码OCR规范化"], row["专业代号OCR"], row["专业名称及备注OCR"])


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]

    candidate_rows = read_csv(CANDIDATE_SUMMARY)
    page_audit_rows = read_csv(CANDIDATE_PAGE_AUDIT)
    group_page_map_rows = read_csv(CANDIDATE_GROUP_PAGE_MAP)
    group_rows = read_csv(FULL_GROUPS)
    major_rows = read_csv(FULL_MAJORS)
    anomaly_rows = read_csv(STRUCTURE_ANOMALIES)

    candidates_by_code = {row["候选专业组代码"]: row for row in candidate_rows}
    page_audit_by_code = {row["候选专业组代码"]: row for row in page_audit_rows}
    groups_by_code = {row["院校专业组代码OCR规范化"]: row for row in group_rows}
    majors_by_group = defaultdict(list)
    for row in major_rows:
        majors_by_group[row["院校专业组代码OCR规范化"]].append(row)

    anomaly_rules_by_major = defaultdict(set)
    anomaly_types_by_major = defaultdict(set)
    anomaly_rows_by_group = Counter()
    for row in anomaly_rows:
        anomaly_rules_by_major[anomaly_key(row)].add(row["异常规则ID"])
        anomaly_types_by_major[anomaly_key(row)].add(row["异常类型"])
        anomaly_rows_by_group[row["院校专业组代码OCR规范化"]] += 1

    manual_seeds_by_group = {seed["group_code"]: seed for seed in MANUAL_PAGE_SEEDS}
    candidate_codes = set(candidates_by_code)

    selected_groups = {}
    for row in candidate_rows:
        selected_groups[row["候选专业组代码"]] = {
            "relation_type": "历史候选",
            "source_candidate": row["候选池学校专业组"],
        }

    for seed in MANUAL_PAGE_SEEDS:
        if seed["group_code"] not in selected_groups:
            selected_groups[seed["group_code"]] = {
                "relation_type": seed["relation_type"],
                "source_candidate": seed.get("source_candidate", "页面相邻或同校偏好补充"),
            }

    for row in group_page_map_rows:
        source_candidate = row["候选池学校专业组"]
        same_groups = [part for part in row.get("同校第19期OCR专业组", "").split("；") if part]
        for group_code in same_groups:
            if group_code in candidate_codes or group_code in selected_groups:
                continue
            preference_tags = {
                tag
                for major in majors_by_group.get(group_code, [])
                for tag in split_tags(major.get("偏好和风险标签", ""))
                if tag in PREFERENCE_TAG_LABELS
            }
            if "priority_1_digital_media" in preference_tags:
                selected_groups[group_code] = {
                    "relation_type": "同校偏好专业补充组",
                    "source_candidate": source_candidate,
                }

    group_output_rows = []
    major_output_rows = []

    for group_code in sorted(selected_groups):
        selection = selected_groups[group_code]
        candidate = candidates_by_code.get(group_code, {})
        page_audit = page_audit_by_code.get(group_code, {})
        manual_seed = manual_seeds_by_group.get(group_code)
        full_group = groups_by_code.get(group_code, {})
        full_major_rows = majors_by_group.get(group_code, [])

        seed_major_rows = []
        if manual_seed:
            for index, (major_code, name, subject, plan, tuition) in enumerate(manual_seed["majors"], start=1):
                tuition_number = as_int(tuition)
                tags = tag_major(name, tuition_number)
                seed_major_rows.append({
                    "组内序号": str(index),
                    "证据来源": manual_seed["source_type"],
                    "院校代码": manual_seed["school_code"],
                    "院校名称OCR": manual_seed["school_name"],
                    "院校专业组代码": group_code,
                    "专业组名称": manual_seed["group_name"],
                    "来源页码": manual_seed["page"],
                    "页图文件名": manual_seed["page_image_file"],
                    "页面证据": manual_seed["page_evidence"],
                    "专业组再选科目候选": manual_seed["group_subject"],
                    "专业组计划数候选": manual_seed["group_plan"],
                    "专业代号": major_code,
                    "专业名称及备注": name,
                    "再选科目候选": subject,
                    "专业计划数候选": plan,
                    "学费候选": tuition,
                    "学费数字候选": tuition,
                    "偏好和风险标签": ";".join(sorted(tags)),
                    "字段完整性标记": "",
                    "结构异常规则ID": "",
                    "结构异常类型": "",
                    "视觉复核说明": manual_seed["review_note"],
                })
        else:
            for index, major in enumerate(full_major_rows, start=1):
                key = anomaly_key(major)
                tags = split_tags(major.get("偏好和风险标签", ""))
                seed_major_rows.append({
                    "组内序号": str(index),
                    "证据来源": "full_ocr_draft",
                    "院校代码": major.get("院校代码", ""),
                    "院校名称OCR": major.get("院校名称OCR", ""),
                    "院校专业组代码": group_code,
                    "专业组名称": full_group.get("专业组标题OCR原文", ""),
                    "来源页码": major.get("来源页码", ""),
                    "页图文件名": f"page-{int(major['来源页码']):03d}.png" if str(major.get("来源页码", "")).isdigit() else "",
                    "页面证据": "全量OCR结构化初稿；需回看页图逐字段确认",
                    "专业组再选科目候选": full_group.get("再选科目OCR候选", ""),
                    "专业组计划数候选": full_group.get("人数OCR候选", ""),
                    "专业代号": major.get("专业代号OCR", ""),
                    "专业名称及备注": major.get("专业名称及备注OCR", ""),
                    "再选科目候选": major.get("再选科目OCR候选", ""),
                    "专业计划数候选": major.get("专业计划数OCR候选", ""),
                    "学费候选": major.get("学费OCR候选", ""),
                    "学费数字候选": major.get("学费OCR数字候选", ""),
                    "偏好和风险标签": ";".join(sorted(tags)),
                    "字段完整性标记": major.get("字段完整性标记", ""),
                    "结构异常规则ID": ";".join(sorted(anomaly_rules_by_major.get(key, []))),
                    "结构异常类型": "；".join(sorted(anomaly_types_by_major.get(key, []))),
                    "视觉复核说明": "",
                })

        all_tags = {tag for row in seed_major_rows for tag in split_tags(row["偏好和风险标签"])}
        preference_tags = all_tags & set(PREFERENCE_TAG_LABELS)
        risk_tags = all_tags & set(RISK_TAG_LABELS)
        max_tuition = max((as_int(row["学费数字候选"]) or 0 for row in seed_major_rows), default=0)
        if max_tuition > 15000:
            risk_tags.add("tuition_over_15000")
        anomaly_count = sum(1 for row in seed_major_rows if row["结构异常规则ID"])

        if page_audit.get("异常规则ID") == "candidate_group_page_hit_structured_miss":
            conclusion = "页面有组号但结构化漏拆，必须按页图重核"
        elif page_audit.get("异常规则ID") == "candidate_group_missing_in_page_and_structured":
            conclusion = "第19期候选页未见该组号，按2026组号变化/旧组号处理"
        elif selection["relation_type"] == "同校偏好专业补充组":
            conclusion = "同校同页发现偏好专业，补入复核但不能沿用原候选历史线"
        elif risk_tags:
            conclusion = f"需风险复核：{risk_labels(risk_tags)}"
        else:
            conclusion = "可进入人工逐字段复核"

        group_output_rows.append({
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "candidate_v2_review_seed",
            "最终可用": "false",
            "关联类型": selection["relation_type"],
            "关联原候选": selection["source_candidate"],
            "原候选专业组代码": group_code if group_code in candidate_codes else "",
            "2026院校专业组代码": group_code,
            "院校代码": (manual_seed or {}).get("school_code", full_group.get("院校代码", group_code[:4])),
            "院校名称": (manual_seed or {}).get(
                "school_name",
                full_group.get("院校名称OCR")
                or candidate.get("第19期OCR院校名称")
                or candidate.get("候选池学校专业组", "").split(" ")[0],
            ),
            "来源页码": (manual_seed or {}).get("page", full_group.get("来源页码", page_audit.get("候选复核页码", ""))),
            "证据来源": (manual_seed or {}).get("source_type", "full_ocr_draft" if full_major_rows else "page_code_audit_only"),
            "页图文件名": (manual_seed or {}).get("page_image_file", f"page-{int(full_group['来源页码']):03d}.png" if str(full_group.get("来源页码", "")).isdigit() else ""),
            "页面组号审计": page_audit.get("异常类型", ""),
            "页面组号证据": page_audit.get("页面OCR证据", ""),
            "结构化命中": "是" if full_group else "否",
            "专业明细行数": str(len(seed_major_rows)),
            "结构异常行数": str(anomaly_count or anomaly_rows_by_group.get(group_code, 0)),
            "偏好方向": labels_for(preference_tags, PREFERENCE_TAG_LABELS),
            "风险类型": risk_labels(risk_tags),
            "最高学费候选": str(max_tuition) if max_tuition else "",
            "V2定位结论": conclusion,
            "核验状态": "needs_manual_pdf_review",
            "下一步": "回看页图逐字段确认；再核湖北官方系统/高校章程；确认组内全部专业能否接受调剂",
        })

        for row in seed_major_rows:
            major_output_rows.append({
                "来源期号": source_issue,
                "来源PDF_SHA256": source_pdf_sha256,
                "数据阶段": "candidate_v2_review_seed",
                "最终可用": "false",
                "关联类型": selection["relation_type"],
                "关联原候选": selection["source_candidate"],
                "2026院校专业组代码": group_code,
                **row,
                "风险类型": risk_labels(split_tags(row["偏好和风险标签"]) & set(RISK_TAG_LABELS)),
                "偏好方向": labels_for(split_tags(row["偏好和风险标签"]) & set(PREFERENCE_TAG_LABELS), PREFERENCE_TAG_LABELS),
                "核验状态": "needs_manual_pdf_review",
                "下一步": "逐字段核对专业代号、专业名称、计划数、学费、选科、备注；再判断调剂可接受性",
            })

    group_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "关联类型",
        "关联原候选",
        "原候选专业组代码",
        "2026院校专业组代码",
        "院校代码",
        "院校名称",
        "来源页码",
        "证据来源",
        "页图文件名",
        "页面组号审计",
        "页面组号证据",
        "结构化命中",
        "专业明细行数",
        "结构异常行数",
        "偏好方向",
        "风险类型",
        "最高学费候选",
        "V2定位结论",
        "核验状态",
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
        "院校专业组代码",
        "专业组名称",
        "来源页码",
        "页图文件名",
        "页面证据",
        "专业组再选科目候选",
        "专业组计划数候选",
        "专业代号",
        "专业名称及备注",
        "再选科目候选",
        "专业计划数候选",
        "学费候选",
        "学费数字候选",
        "偏好和风险标签",
        "偏好方向",
        "风险类型",
        "字段完整性标记",
        "结构异常规则ID",
        "结构异常类型",
        "视觉复核说明",
        "核验状态",
        "下一步",
    ]
    write_csv(GROUP_OUTPUT, group_output_rows, group_fields)
    write_csv(MAJOR_OUTPUT, major_output_rows, major_fields)

    summary = {
        "status": "candidate_v2_review_seed_needs_manual_pdf_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "candidate_v2_review_seed",
        "generated_by": "scripts/build_issue19_candidate_v2_review_seed.py",
        "inputs": input_snapshot(
            ROOT,
            [
                ISSUE19_SOURCE,
                CANDIDATE_SUMMARY,
                CANDIDATE_PAGE_AUDIT,
                CANDIDATE_GROUP_PAGE_MAP,
                FULL_GROUPS,
                FULL_MAJORS,
                STRUCTURE_ANOMALIES,
            ],
        ),
        "group_seed_count": len(group_output_rows),
        "major_seed_count": len(major_output_rows),
        "relation_type_counts": dict(Counter(row["关联类型"] for row in group_output_rows)),
        "evidence_source_counts": dict(Counter(row["证据来源"] for row in major_output_rows)),
        "key_findings": [
            "C10704 页面OCR和页图可见，但全量结构化专业组表漏拆；已补为页图复核种子。",
            "C10703 当前全量OCR吞入C10704专业；候选V2种子按页图重切为7个专业。",
            "K15123 在第208/209页未见；同校K15114含数字媒体技术，作为同校偏好专业补充组，不沿用K15123历史投档线。",
        ],
        "outputs": [
            str(GROUP_OUTPUT.relative_to(ROOT)),
            str(MAJOR_OUTPUT.relative_to(ROOT)),
        ],
        "notes": [
            "本表仍是复核种子，不是最终志愿表。",
            "所有行保持最终可用=false，进入最终方案前必须回看原页、湖北官方系统和高校章程。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出候选V2专业组复核种子：{GROUP_OUTPUT}")
    print(f"写出候选V2专业明细复核种子：{MAJOR_OUTPUT}")
    print(f"写出候选V2复核种子摘要：{SUMMARY_OUTPUT}")
    print(f"专业组数：{len(group_output_rows)}")
    print(f"专业明细数：{len(major_output_rows)}")


if __name__ == "__main__":
    main()
