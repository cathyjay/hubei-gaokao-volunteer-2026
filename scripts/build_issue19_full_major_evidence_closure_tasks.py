#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FULL_EVIDENCE_WORKBENCH = ROOT / "data/working/issue19-full-major-evidence-workbench.csv"
OUTPUT = ROOT / "data/working/issue19-full-major-evidence-closure-tasks.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-full-major-evidence-closure-tasks-summary.json"

DATA_STAGE = "issue19_full_major_evidence_closure_tasks"

BASE_EVIDENCE_ITEMS = [
    ("01", "PDF原页核验"),
    ("02", "湖北官方系统/省招办计划核验"),
    ("03", "高校官网/章程辅证"),
    ("04", "家庭接受度核验"),
    ("05", "同组调剂结论核验"),
    ("06", "三年投档稳定性核验"),
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


def short_text(value, limit=120):
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def join_flags(values):
    return "；".join(dict.fromkeys(value for value in values if value))


def has_field_gap(row):
    return (
        not row.get("再选科目OCR候选")
        or not row.get("专业计划数OCR候选")
        or not row.get("学费OCR候选")
        or "计划数字段" in row.get("高风险字段集合", "")
        or "学费字段" in row.get("高风险字段集合", "")
        or "再选科目字段" in row.get("高风险字段集合", "")
    )


def evidence_status(row, item):
    if item == "PDF原页核验":
        if row.get("D0原页OCR证据状态") != "not_d0_group":
            return "has_d0_page_ocr_evidence_pending_original_pdf_review"
        return row.get("PDF字段核验状态", "pending_original_pdf_page_review")
    if item == "湖北官方系统/省招办计划核验":
        return row.get("湖北官方系统字段核验状态", "pending_hubei_official_plan_review")
    if item == "高校官网/章程辅证":
        status = row.get("高校官网/章程辅证状态", "")
        if status == "has_reusable_2026_hubei_plan_source":
            return "has_school_plan_source_pending_crosscheck"
        if status == "has_partial_source_needs_followup":
            return "has_partial_school_source_pending_followup"
        if status == "charter_or_rules_only_no_plan":
            return "has_charter_or_rules_but_no_plan_detail"
        if status == "needs_official_plan_source_search":
            return "pending_school_plan_source_search"
        if status == "官网专业名匹配但计划数冲突-优先核页":
            return "school_source_conflict_pending_pdf_and_hubei_review"
        return "pending_school_plan_or_charter_review"
    if item == "家庭接受度核验":
        return row.get("家庭接受度核验状态", "pending_family_acceptance_review")
    if item == "同组调剂结论核验":
        return "pending_full_group_adjustment_review"
    if item == "三年投档稳定性核验":
        if row.get("三年投档线索"):
            return "has_historical_line_pending_stability_review"
        return "pending_group_code_change_or_missing_history_review"
    if item == "字段完整性补证":
        return "pending_field_gap_review"
    if item == "B0/B1官网冲突或未匹配复核":
        if row.get("B0B1计划冲突来源明细ID"):
            return "pending_b0_b1_plan_conflict_review"
        return "pending_b0_b1_unmatched_major_review"
    return "pending_review"


def required_fields_for(item, row):
    if item == "PDF原页核验":
        return "PDF核心字段"
    if item == "湖北官方系统/省招办计划核验":
        return "湖北官方计划字段"
    if item == "高校官网/章程辅证":
        return "高校官网章程字段"
    if item == "家庭接受度核验":
        return "家庭接受度字段"
    if item == "同组调剂结论核验":
        return "同组调剂字段"
    if item == "三年投档稳定性核验":
        return "三年投档稳定性字段"
    if item == "字段完整性补证":
        fields = []
        if not row.get("再选科目OCR候选") or "再选科目字段" in row.get("高风险字段集合", ""):
            fields.append("再选科目")
        if not row.get("专业计划数OCR候选") or "计划数字段" in row.get("高风险字段集合", ""):
            fields.append("计划数")
        if not row.get("学费OCR候选") or "学费字段" in row.get("高风险字段集合", ""):
            fields.append("学费")
        return join_flags(fields) or "字段完整性"
    if item == "B0/B1官网冲突或未匹配复核":
        return "B0B1官网差异字段"
    return ""


def action_for(item, row):
    if item == "PDF原页核验":
        return "review_pdf_original_page"
    if item == "湖北官方系统/省招办计划核验":
        return "review_hubei_official_plan_system"
    if item == "高校官网/章程辅证":
        return "crosscheck_school_plan_or_charter"
    if item == "家庭接受度核验":
        return "review_family_acceptance"
    if item == "同组调剂结论核验":
        return "review_full_group_adjustment"
    if item == "三年投档稳定性核验":
        return "review_three_year_toudang_stability"
    if item == "字段完整性补证":
        return "repair_field_gap_with_evidence"
    if item == "B0/B1官网冲突或未匹配复核":
        return "review_b0_b1_conflict_or_unmatched"
    return "continue_evidence_closure"


def reusable_hint(item, row):
    if item == "PDF原页核验":
        hints = [row.get("页级保真队列ID"), row.get("D0原页OCR证据状态")]
        return join_flags(hints)
    if item == "高校官网/章程辅证":
        return join_flags([
            row.get("高校官网/章程辅证状态"),
            row.get("高校官网可核字段"),
        ])
    if item == "三年投档稳定性核验":
        return row.get("三年投档稳定性状态", "")
    if item == "B0/B1官网冲突或未匹配复核":
        return join_flags([
            row.get("B0B1计划冲突来源明细ID"),
            row.get("B0B1未匹配专业来源明细ID"),
            row.get("计划数核验状态"),
        ])
    return ""


def blocker_reason(item, row):
    reasons = []
    if row.get("风险阻断等级", "").startswith("F0"):
        reasons.append("结构阻断")
    if row.get("D0原页OCR证据状态") != "not_d0_group":
        reasons.append("D0原页证据待人工核验")
    if "默认不能接受" in row.get("机器专业接受度初判", ""):
        reasons.append("机器初判默认不能接受")
    if "调剂风险线索" in row.get("组调剂初判", ""):
        reasons.append("同组调剂风险")
    if item == "字段完整性补证" and has_field_gap(row):
        reasons.append("字段缺失或高风险")
    if item == "B0/B1官网冲突或未匹配复核":
        if row.get("B0B1计划冲突来源明细ID"):
            reasons.append("B0/B1计划数冲突")
        if row.get("B0B1未匹配专业来源明细ID"):
            reasons.append("B0/B1官网未匹配专业")
    return join_flags(reasons) or "证据未闭环"


def task_priority(item, row):
    evidence_priority = row.get("全量证据执行优先级", "")
    if item == "PDF原页核验" and (
        evidence_priority.startswith("E0")
        or evidence_priority.startswith("F0")
        or row.get("风险阻断等级", "").startswith("F0")
    ):
        return "P0-先核PDF结构阻断"
    if item == "B0/B1官网冲突或未匹配复核":
        return "P0-B0B1冲突/未匹配先核"
    if item in {"湖北官方系统/省招办计划核验", "高校官网/章程辅证"} and (
        evidence_priority.startswith(("E1", "E2", "E3", "F1"))
    ):
        return "P0-三方证据闭环先核"
    if item == "字段完整性补证" or evidence_priority.startswith(("E4", "F2")):
        return "P1-字段补证"
    if item in {"家庭接受度核验", "同组调剂结论核验"} and (
        "调剂风险线索" in row.get("组调剂初判", "")
        or "默认不能接受" in row.get("机器专业接受度初判", "")
    ):
        return "P1-家庭底线和调剂风险"
    return "P2-常规证据闭环"


def task_items_for(row):
    items = list(BASE_EVIDENCE_ITEMS)
    if has_field_gap(row):
        items.append(("07", "字段完整性补证"))
    if row.get("B0B1计划冲突来源明细ID") or row.get("B0B1未匹配专业来源明细ID"):
        items.append(("08", "B0/B1官网冲突或未匹配复核"))
    return items


def main():
    evidence_rows = read_csv(FULL_EVIDENCE_WORKBENCH)
    output_rows = []
    for row in evidence_rows:
        for item_sort, item in task_items_for(row):
            output_rows.append({
                "证据闭环任务ID": stable_id(
                    "CLOSETASK",
                    [row.get("全量证据工作台ID", ""), item],
                ),
                "来源全量证据工作台ID": row.get("全量证据工作台ID", ""),
                "最终可用": "false",
                "是否可升级": "false",
                "任务状态": "pending_evidence_closure",
                "专业行ID": row.get("专业行ID", ""),
                "专业组出现ID": row.get("专业组出现ID", ""),
                "院校代码": row.get("院校代码", ""),
                "院校名称OCR": row.get("院校名称OCR", ""),
                "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
                "来源页码": row.get("来源页码", ""),
                "专业组内专业序号": row.get("专业组内专业序号", ""),
                "专业代号OCR": row.get("专业代号OCR", ""),
                "专业名称及备注OCR短摘": short_text(row.get("专业名称及备注OCR", ""), 30),
                "全量证据执行优先级": row.get("全量证据执行优先级", ""),
                "证据项排序": item_sort,
                "证据项": item,
                "证据任务优先级": task_priority(item, row),
                "证据任务状态": evidence_status(row, item),
                "需要核验字段": required_fields_for(item, row),
                "执行动作代码": action_for(item, row),
                "阻断或待核原因": blocker_reason(item, row),
            })

    fields = [
        "证据闭环任务ID",
        "来源全量证据工作台ID",
        "最终可用",
        "是否可升级",
        "任务状态",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "全量证据执行优先级",
        "证据项排序",
        "证据项",
        "证据任务优先级",
        "证据任务状态",
        "需要核验字段",
        "执行动作代码",
        "阻断或待核原因",
    ]
    write_csv(OUTPUT, output_rows, fields)

    evidence_item_counts = Counter(row["证据项"] for row in output_rows)
    task_priority_counts = Counter(row["证据任务优先级"] for row in output_rows)
    task_status_counts = Counter(row["证据任务状态"] for row in output_rows)
    execution_priority_counts = Counter(row["全量证据执行优先级"] for row in output_rows)

    summary = {
        "status": "issue19_full_major_evidence_closure_tasks_not_final",
        "generated_by": "build_issue19_full_major_evidence_closure_tasks.py",
        "source_full_major_evidence_workbench": "data/working/issue19-full-major-evidence-workbench.csv",
        "output_table": "data/working/issue19-full-major-evidence-closure-tasks.csv",
        "source_major_row_count": len(evidence_rows),
        "task_row_count": len(output_rows),
        "unique_task_id_count": len({row["证据闭环任务ID"] for row in output_rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "base_task_count": len(evidence_rows) * len(BASE_EVIDENCE_ITEMS),
        "conditional_field_gap_task_count": evidence_item_counts.get("字段完整性补证", 0),
        "conditional_b0_b1_task_count": evidence_item_counts.get("B0/B1官网冲突或未匹配复核", 0),
        "auto_upgrade_allowed_count": sum(row["是否可升级"] == "true" for row in output_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "evidence_item_counts": dict(evidence_item_counts),
        "task_priority_counts": dict(task_priority_counts),
        "task_status_counts": dict(task_status_counts),
        "execution_priority_counts": dict(execution_priority_counts),
        "notes": [
            "本表是一行一个专业行和一个证据项的闭环任务，不替代全量逐专业证据工作台。",
            "专业名称只保留短摘，完整OCR原文以专业行ID回链到全量证据工作台。",
            "所有任务仍需PDF原页、湖北官方系统/省招办计划、高校官网/章程、家庭接受度和调剂结论闭环。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
