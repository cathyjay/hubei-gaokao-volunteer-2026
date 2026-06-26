#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import input_snapshot


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
B0_B1_GROUP_PACK = ROOT / "data/working/issue19-candidate-v3-b0-b1-group-review-pack.csv"
B0_B1_MAJOR_PACK = ROOT / "data/working/issue19-candidate-v3-b0-b1-major-review-pack.csv"
SCHOOL_OFFICIAL_SOURCES = ROOT / "data/working/issue19-sample-school-official-sources.csv"
B0_B1_OFFICIAL_SOURCE_SEEDS = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv"

SCHOOL_QUEUE_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv"
GROUP_QUEUE_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-crosscheck-queue.csv"
MAJOR_QUEUE_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-major-official-crosscheck-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-crosscheck-summary.json"

DATA_STAGE = "issue19_candidate_v3_b0_b1_official_crosscheck_queue"

REQUIRED_GROUP_FIELDS = [
    "院校代码",
    "院校名称",
    "院校专业组代码",
    "专业组边界和组内全部专业",
    "专业代号",
    "专业名称及备注",
    "专业计划数",
    "学费",
    "学制",
    "校区",
    "再选科目",
    "特殊备注",
    "招生章程录取规则",
    "体检/语种/单科限制",
    "办学性质和高收费/中外合作",
]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def normalize_status(value):
    value = (value or "").strip()
    if value == "是":
        return "has_reusable_2026_hubei_plan_source"
    if value in {"部分", "可能"}:
        return "has_partial_source_needs_followup"
    if value == "否":
        return "charter_or_rules_only_no_plan"
    if value in {"未见", "待继续核验", ""}:
        return "needs_official_plan_source_search"
    return "needs_manual_source_status_review"


def source_gap(status, source_row):
    if status == "has_reusable_2026_hubei_plan_source":
        return "需逐字段比对第19期、湖北官方系统和高校官网字段"
    if status == "has_partial_source_needs_followup":
        return "已有部分官网线索，但仍需补齐湖北普通本科物理专业组或逐专业字段"
    if status == "charter_or_rules_only_no_plan":
        return "当前只可辅助核招生章程或规则，不能核湖北2026专业组计划"
    return "未定位可复用的高校官网湖北2026普通本科物理招生计划，需要优先补源"


def source_priority(status, batch_counts, group_count):
    if batch_counts.get("B0-历史候选和组号问题优先核页", 0):
        return "S0-B0历史候选学校优先补源"
    if status == "has_reusable_2026_hubei_plan_source":
        return "S1-已有官网计划源先做字段对照"
    if group_count >= 2:
        return "S2-多组学校优先补源"
    return "S3-B1单组学校按页码推进"


def search_query_for_school(name):
    return f"{name} 2026 湖北 招生计划 本科 专业组 招生网"


def charter_query_for_school(name):
    return f"{name} 2026 普通本科 招生章程"


def local_retention_state(source_row):
    value = (source_row.get("本地留存路径", "") if source_row else "").strip()
    if not value or value == "未留存":
        return "pending_local_retention"
    return "has_local_retention_metadata"


def source_row_for_school(name, sources_by_school):
    return sources_by_school.get(name, {})


def group_risk_tags(group):
    tags = []
    if group.get("医学护理排除专业数") not in {"", "0"}:
        tags.append("医学护理排除方向")
    if group.get("高收费或超预算专业数") not in {"", "0"}:
        tags.append("高收费或超预算")
    if group.get("特殊限制待核专业数") not in {"", "0"}:
        tags.append("特殊限制待核")
    if group.get("专业明细行数") == "0":
        tags.append("0明细组")
    if "历史线不得直接沿用" in group.get("历史线使用口径", ""):
        tags.append("历史线不得直接沿用")
    return "；".join(tags) or "无"


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]
    group_rows = read_csv(B0_B1_GROUP_PACK)
    major_rows = read_csv(B0_B1_MAJOR_PACK)
    official_source_rows = read_csv(SCHOOL_OFFICIAL_SOURCES)
    official_source_seed_rows = read_csv(B0_B1_OFFICIAL_SOURCE_SEEDS)
    sources_by_school = {row["学校名称"]: row for row in official_source_rows}
    sources_by_school.update({row["学校名称"]: row for row in official_source_seed_rows})

    groups_by_school = defaultdict(list)
    majors_by_entry = defaultdict(list)
    for group in group_rows:
        groups_by_school[(group["院校代码"], group["院校名称OCR"])].append(group)
    for major in major_rows:
        majors_by_entry[major["候选V3入口ID"]].append(major)

    school_rows = []
    school_source_status_by_name = {}
    for (school_code, school_name), school_groups in sorted(groups_by_school.items()):
        source_row = source_row_for_school(school_name, sources_by_school)
        status = normalize_status(source_row.get("是否可核湖北2026", ""))
        batch_counts = Counter(group["复核批次"] for group in school_groups)
        group_count = len(school_groups)
        major_task_count = sum(len(majors_by_entry[group["候选V3入口ID"]]) for group in school_groups)
        school_source_status_by_name[school_name] = status
        row = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": DATA_STAGE,
            "最终可用": "false",
            "核验状态": "pending_school_official_source_review",
            "学校官方来源队列ID": stable_id("SSQ", [source_pdf_sha256, school_code, school_name]),
            "院校代码": school_code,
            "院校名称OCR": school_name,
            "B0组数": str(batch_counts.get("B0-历史候选和组号问题优先核页", 0)),
            "B1组数": str(batch_counts.get("B1-数字媒体技术优先核页", 0)),
            "B0B1专业组数": str(group_count),
            "逐专业核验任务数": str(major_task_count),
            "涉及专业组代码": "；".join(group["2026院校专业组代码"] for group in school_groups),
            "涉及PDF页码": "；".join(sorted({group["来源页码"] for group in school_groups})),
            "官网来源状态": status,
            "官网来源优先级": source_row.get("官网来源优先级", "待补源"),
            "官网URL": source_row.get("官网URL", ""),
            "本地留存路径": source_row.get("本地留存路径", ""),
            "本地留存状态": local_retention_state(source_row),
            "是否可核湖北2026": source_row.get("是否可核湖北2026", "未见"),
            "可核字段": source_row.get("可核字段", ""),
            "局限性": source_row.get("局限性", ""),
            "官方源缺口": source_gap(status, source_row),
            "补源优先级": source_priority(status, batch_counts, group_count),
            "高校官网计划检索式": search_query_for_school(school_name),
            "招生章程检索式": charter_query_for_school(school_name),
            "下一步": "优先找高校官网湖北2026普通本科物理招生计划；若没有固定计划页，则至少补招生章程，并回到湖北官方系统或省招办计划兜底。",
        }
        school_rows.append(row)

    group_queue_rows = []
    major_queue_rows = []
    for group in group_rows:
        school_name = group["院校名称OCR"]
        source_row = source_row_for_school(school_name, sources_by_school)
        status = school_source_status_by_name.get(school_name, "needs_official_plan_source_search")
        major_tasks = majors_by_entry[group["候选V3入口ID"]]
        group_task_id = stable_id(
            "OCQ",
            [source_pdf_sha256, group["候选V3入口ID"], group["2026院校专业组代码"]],
        )
        row = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": DATA_STAGE,
            "最终可用": "false",
            "核验状态": "pending_group_official_crosscheck",
            "官方交叉校验任务ID": group_task_id,
            "候选V3入口ID": group["候选V3入口ID"],
            "复核批次": group["复核批次"],
            "入口类型": group["入口类型"],
            "院校代码": group["院校代码"],
            "院校名称OCR": school_name,
            "2026院校专业组代码": group["2026院校专业组代码"],
            "来源页码": group["来源页码"],
            "专业明细来源": group["专业明细来源"],
            "专业明细行数": group["专业明细行数"],
            "逐专业核验任务数": str(len(major_tasks)),
            "风险线索": group_risk_tags(group),
            "历史线使用口径": group["历史线使用口径"],
            "官网来源状态": status,
            "官网URL": source_row.get("官网URL", ""),
            "本地留存路径": source_row.get("本地留存路径", ""),
            "可核字段": source_row.get("可核字段", ""),
            "官网来源局限": source_row.get("局限性", ""),
            "官方源缺口": source_gap(status, source_row),
            "必须核验字段": "；".join(REQUIRED_GROUP_FIELDS),
            "湖北官方系统核验状态": "pending_hubei_official_plan_review",
            "高校官网计划核验状态": "pending_school_plan_review",
            "招生章程核验状态": "pending_school_charter_review",
            "PDF原页核验状态": group["PDF原页核验状态"],
            "家庭接受度核验状态": group["家庭接受度核验状态"],
            "调剂结论状态": group["调剂结论状态"],
            "交叉校验结论": "pending",
            "可进入下一阶段": "false",
            "高校官网计划检索式": search_query_for_school(school_name),
            "招生章程检索式": charter_query_for_school(school_name),
            "下一步": "先补高校官网/章程来源，再按必须核验字段逐项比对第19期、湖北官方系统和高校官网；不一致时以省招办渠道为准并记录差异。",
        }
        group_queue_rows.append(row)
        for major in major_tasks:
            major_queue_rows.append({
                "来源期号": source_issue,
                "来源PDF_SHA256": source_pdf_sha256,
                "数据阶段": DATA_STAGE,
                "最终可用": "false",
                "核验状态": "pending_major_official_crosscheck",
                "官方逐专业校验任务ID": stable_id(
                    "OMQ",
                    [
                        source_pdf_sha256,
                        major["候选V3入口ID"],
                        major["专业核验任务ID"],
                        major["专业组内专业序号"],
                        major["专业代号OCR"],
                    ],
                ),
                "官方交叉校验任务ID": group_task_id,
                "专业核验任务ID": major["专业核验任务ID"],
                "候选V3入口ID": major["候选V3入口ID"],
                "复核批次": major["复核批次"],
                "入口类型": major["入口类型"],
                "院校代码": major["院校代码"],
                "院校名称OCR": major["院校名称OCR"],
                "2026院校专业组代码": major["2026院校专业组代码"],
                "来源页码": major["来源页码"],
                "专业明细来源": major["专业明细来源"],
                "专业行来源": major["专业行来源"],
                "专业行ID": major["专业行ID"],
                "专业组内专业序号": major["专业组内专业序号"],
                "专业代号OCR": major["专业代号OCR"],
                "专业名称及备注OCR": major["专业名称及备注OCR"],
                "再选科目OCR候选": major["再选科目OCR候选"],
                "专业计划数OCR候选": major["专业计划数OCR候选"],
                "学费OCR候选": major["学费OCR候选"],
                "专业偏好方向": major["专业偏好方向"],
                "专业风险类型": major["专业风险类型"],
                "专业字段完整性标记": major["专业字段完整性标记"],
                "机器专业接受度初判": major["机器专业接受度初判"],
                "机器阻断或待核原因": major["机器阻断或待核原因"],
                "调剂影响初判": major["调剂影响初判"],
                "官网来源状态": status,
                "官网URL": source_row.get("官网URL", ""),
                "本地留存路径": source_row.get("本地留存路径", ""),
                "可核字段": source_row.get("可核字段", ""),
                "官网来源局限": source_row.get("局限性", ""),
                "官方源缺口": source_gap(status, source_row),
                "PDF字段核验状态": "pending_original_pdf_page_review",
                "湖北官方系统字段核验状态": "pending_hubei_official_plan_review",
                "高校官网/章程字段核验状态": "pending_school_plan_or_charter_review",
                "家庭接受度人工结论状态": "pending_family_acceptance_review",
                "调剂影响人工结论状态": "pending_transfer_decision",
                "字段核验状态": major["字段核验状态"],
                "是否阻断组升级": major["是否阻断组升级"],
                "可进入最终专业列表": major["可进入最终专业列表"],
                "可进入下一阶段": "false",
                "高校官网计划检索式": search_query_for_school(school_name),
                "招生章程检索式": charter_query_for_school(school_name),
                "下一步": "逐专业比对PDF原页、湖北官方系统或省招办计划、高校官网/章程和家庭接受度；专业字段未全部确认前不得进入最终专业列表。",
            })

    school_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "学校官方来源队列ID",
        "院校代码",
        "院校名称OCR",
        "B0组数",
        "B1组数",
        "B0B1专业组数",
        "逐专业核验任务数",
        "涉及专业组代码",
        "涉及PDF页码",
        "官网来源状态",
        "官网来源优先级",
        "官网URL",
        "本地留存路径",
        "本地留存状态",
        "是否可核湖北2026",
        "可核字段",
        "局限性",
        "官方源缺口",
        "补源优先级",
        "高校官网计划检索式",
        "招生章程检索式",
        "下一步",
    ]
    group_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "官方交叉校验任务ID",
        "候选V3入口ID",
        "复核批次",
        "入口类型",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "来源页码",
        "专业明细来源",
        "专业明细行数",
        "逐专业核验任务数",
        "风险线索",
        "历史线使用口径",
        "官网来源状态",
        "官网URL",
        "本地留存路径",
        "可核字段",
        "官网来源局限",
        "官方源缺口",
        "必须核验字段",
        "湖北官方系统核验状态",
        "高校官网计划核验状态",
        "招生章程核验状态",
        "PDF原页核验状态",
        "家庭接受度核验状态",
        "调剂结论状态",
        "交叉校验结论",
        "可进入下一阶段",
        "高校官网计划检索式",
        "招生章程检索式",
        "下一步",
    ]
    major_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "官方逐专业校验任务ID",
        "官方交叉校验任务ID",
        "专业核验任务ID",
        "候选V3入口ID",
        "复核批次",
        "入口类型",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "来源页码",
        "专业明细来源",
        "专业行来源",
        "专业行ID",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业偏好方向",
        "专业风险类型",
        "专业字段完整性标记",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "调剂影响初判",
        "官网来源状态",
        "官网URL",
        "本地留存路径",
        "可核字段",
        "官网来源局限",
        "官方源缺口",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "家庭接受度人工结论状态",
        "调剂影响人工结论状态",
        "字段核验状态",
        "是否阻断组升级",
        "可进入最终专业列表",
        "可进入下一阶段",
        "高校官网计划检索式",
        "招生章程检索式",
        "下一步",
    ]
    write_csv(SCHOOL_QUEUE_OUTPUT, school_rows, school_fields)
    write_csv(GROUP_QUEUE_OUTPUT, group_queue_rows, group_fields)
    write_csv(MAJOR_QUEUE_OUTPUT, major_queue_rows, major_fields)

    summary = {
        "status": "issue19_candidate_v3_b0_b1_official_crosscheck_pending",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": DATA_STAGE,
        "generated_by": "scripts/build_issue19_candidate_v3_b0_b1_official_crosscheck_queue.py",
        "inputs": input_snapshot(
            ROOT,
            [
                ISSUE19_SOURCE,
                B0_B1_GROUP_PACK,
                B0_B1_MAJOR_PACK,
                SCHOOL_OFFICIAL_SOURCES,
                B0_B1_OFFICIAL_SOURCE_SEEDS,
            ],
        ),
        "school_count": len(school_rows),
        "group_count": len(group_queue_rows),
        "major_review_task_count": len(major_rows),
        "major_official_crosscheck_task_count": len(major_queue_rows),
        "school_source_status_counts": dict(sorted(Counter(row["官网来源状态"] for row in school_rows).items())),
        "group_source_status_counts": dict(sorted(Counter(row["官网来源状态"] for row in group_queue_rows).items())),
        "major_source_status_counts": dict(sorted(Counter(row["官网来源状态"] for row in major_queue_rows).items())),
        "major_row_source_counts": dict(sorted(Counter(row["专业行来源"] for row in major_queue_rows).items())),
        "source_priority_counts": dict(sorted(Counter(row["补源优先级"] for row in school_rows).items())),
        "schools_with_reusable_2026_hubei_plan_source": sorted(
            row["院校名称OCR"]
            for row in school_rows
            if row["官网来源状态"] == "has_reusable_2026_hubei_plan_source"
        ),
        "schools_needing_official_plan_source_search": sorted(
            row["院校名称OCR"]
            for row in school_rows
            if row["官网来源状态"] == "needs_official_plan_source_search"
        ),
        "final_available_count": sum(row["可进入下一阶段"] == "true" for row in group_queue_rows),
        "major_final_available_count": sum(row["可进入下一阶段"] == "true" for row in major_queue_rows),
        "notes": [
            "本队列用于补齐B0/B1优先组的高校官网/章程交叉校验证据，不是最终报考建议。",
            "高校官网只能辅助核专业、计划、学费、选科、校区和章程规则；若与省招办计划不一致，以湖北省招办渠道为准。",
            "没有官网湖北2026计划页的学校不删除，标为needs_official_plan_source_search并保留检索式。",
            "所有专业组和逐专业任务仍保持可进入下一阶段=false，必须完成PDF原页、湖北官方系统、高校官网/章程、家庭接受度和调剂结论后才能升级。",
        ],
        "outputs": [
            str(SCHOOL_QUEUE_OUTPUT.relative_to(ROOT)),
            str(GROUP_QUEUE_OUTPUT.relative_to(ROOT)),
            str(MAJOR_QUEUE_OUTPUT.relative_to(ROOT)),
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出B0/B1学校官方来源队列：{SCHOOL_QUEUE_OUTPUT}")
    print(f"写出B0/B1官方交叉校验队列：{GROUP_QUEUE_OUTPUT}")
    print(f"写出B0/B1逐专业官方交叉校验队列：{MAJOR_QUEUE_OUTPUT}")
    print(f"写出B0/B1官方交叉校验摘要：{SUMMARY_OUTPUT}")
    print(f"学校数：{len(school_rows)}")
    print(f"专业组数：{len(group_queue_rows)}")
    print(f"逐专业任务数：{len(major_queue_rows)}")


if __name__ == "__main__":
    main()
