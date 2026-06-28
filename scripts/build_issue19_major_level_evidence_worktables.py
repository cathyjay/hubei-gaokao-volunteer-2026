#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FULL_EVIDENCE = ROOT / "data/working/issue19-full-major-evidence-workbench.csv"
FIELD_FIDELITY = ROOT / "data/working/issue19-full-major-field-fidelity-ledger.csv"
CLOSURE_TASKS = ROOT / "data/working/issue19-full-major-evidence-closure-tasks.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
PAGE_FIDELITY = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"
B0B1_RETAINED = ROOT / "data/working/issue19-b0-b1-retained-official-plan-normalized.csv"
B0B1_MATCH = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-evidence-match.csv"

FIELD_GAP_OUTPUT = ROOT / "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv"
FIELD_GAP_SUMMARY = ROOT / "data/working/issue19-p1-field-gap-evidence-repair-matrix-summary.json"
HUBEI_OFFICIAL_OUTPUT = ROOT / "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"
HUBEI_OFFICIAL_SUMMARY = ROOT / "data/working/issue19-hubei-official-plan-major-crosscheck-packets-summary.json"
B0B1_DIFF_OUTPUT = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
B0B1_DIFF_SUMMARY = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger-summary.json"


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


def split_cn(value):
    return [part for part in str(value or "").split("；") if part]


def short_text(value, limit=80):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def build_indexes():
    full_rows = read_csv(FULL_EVIDENCE)
    fidelity_rows = read_csv(FIELD_FIDELITY)
    closure_rows = read_csv(CLOSURE_TASKS)
    manifest_rows = read_csv(PAGE_MANIFEST)
    page_rows = read_csv(PAGE_FIDELITY)
    retained_rows = read_csv(B0B1_RETAINED)
    match_rows = read_csv(B0B1_MATCH)

    return {
        "full_rows": full_rows,
        "fidelity_rows": fidelity_rows,
        "closure_rows": closure_rows,
        "manifest_by_page": {row.get("PDF页码"): row for row in manifest_rows},
        "page_by_page": {row.get("PDF页码"): row for row in page_rows},
        "full_by_major_id": {row.get("专业行ID"): row for row in full_rows},
        "full_by_workbench_id": {row.get("全量证据工作台ID"): row for row in full_rows},
        "fidelity_by_major_id": {row.get("专业行ID"): row for row in fidelity_rows},
        "field_gap_task_by_major_id": {
            row.get("专业行ID"): row
            for row in closure_rows
            if row.get("证据项") == "字段完整性补证"
        },
        "hubei_task_by_major_id": {
            row.get("专业行ID"): row
            for row in closure_rows
            if row.get("证据项") == "湖北官方系统/省招办计划核验"
        },
        "retained_rows": retained_rows,
        "match_rows": match_rows,
    }


def field_gap_issue_type(field_name, fidelity_row):
    if field_name == "再选科目":
        return "再选科目缺失或需核组内继承"
    if field_name == "专业计划数":
        if not fidelity_row.get("专业计划数OCR候选"):
            return "计划数缺失"
        if fidelity_row.get("专业计划数是否纯数字") != "true":
            return "计划数非纯数字或疑似错位"
        return "计划数字段被风险规则命中"
    if field_name == "学费":
        if not fidelity_row.get("学费OCR候选"):
            return "学费缺失"
        if fidelity_row.get("学费是否纯数字") != "true":
            return "学费非纯数字或疑似错位"
        return "学费字段被风险规则命中"
    return "字段缺口"


def build_field_gap_matrix(indexes):
    fields_to_emit = [
        ("再选科目字段", "再选科目", "再选科目OCR候选", ""),
        ("计划数字段", "专业计划数", "专业计划数OCR候选", ""),
        ("学费字段", "学费", "学费OCR候选", "学费OCR数字候选"),
    ]
    rows = []
    for fidelity_row in indexes["fidelity_rows"]:
        field_set = set(split_cn(fidelity_row.get("高风险字段集合")))
        full_row = indexes["full_by_major_id"].get(fidelity_row.get("专业行ID"), {})
        task_row = indexes["field_gap_task_by_major_id"].get(fidelity_row.get("专业行ID"), {})
        manifest_row = indexes["manifest_by_page"].get(fidelity_row.get("来源页码"), {})
        page_row = indexes["page_by_page"].get(fidelity_row.get("来源页码"), {})
        for risk_field, field_name, candidate_field, numeric_field in fields_to_emit:
            if risk_field not in field_set:
                continue
            rows.append({
                "字段补证任务ID": stable_id(
                    "FIELDGAP",
                    [fidelity_row.get("专业行ID", ""), field_name],
                ),
                "来源字段保真总账ID": fidelity_row.get("全量保真总账ID", ""),
                "来源全量证据工作台ID": full_row.get("全量证据工作台ID", ""),
                "来源证据闭环任务ID": task_row.get("证据闭环任务ID", ""),
                "来源期号": fidelity_row.get("来源期号", ""),
                "来源PDF_SHA256": fidelity_row.get("来源PDF_SHA256", ""),
                "数据阶段": "issue19_p1_field_gap_evidence_repair_matrix",
                "主表粒度": "逐专业招生明细",
                "任务粒度": "逐专业招生明细×字段缺口",
                "最终可用": "false",
                "可进入下一阶段": "false",
                "证据状态": "pending_field_gap_review",
                "专业行ID": fidelity_row.get("专业行ID", ""),
                "专业组出现ID": fidelity_row.get("专业组出现ID", ""),
                "院校代码": fidelity_row.get("院校代码", ""),
                "院校名称OCR": fidelity_row.get("院校名称OCR", ""),
                "院校专业组代码OCR规范化": fidelity_row.get("院校专业组代码OCR规范化", ""),
                "来源页码": fidelity_row.get("来源页码", ""),
                "版面列": fidelity_row.get("版面列", ""),
                "专业组内专业序号": fidelity_row.get("专业组内专业序号", ""),
                "专业代号OCR": fidelity_row.get("专业代号OCR", ""),
                "专业名称及备注OCR短摘": short_text(fidelity_row.get("专业名称及备注OCR")),
                "字段名": field_name,
                "OCR候选值": fidelity_row.get(candidate_field, ""),
                "OCR数字候选": fidelity_row.get(numeric_field, ""),
                "字段问题类型": field_gap_issue_type(field_name, fidelity_row),
                "高风险字段集合": fidelity_row.get("高风险字段集合", ""),
                "风险触发规则": fidelity_row.get("风险触发规则", ""),
                "页级保真队列ID": full_row.get("页级保真队列ID", ""),
                "页面复核优先级": page_row.get("页面复核优先级", ""),
                "页面阻断等级": page_row.get("页面阻断等级", ""),
                "私有页图证据编号": manifest_row.get("私有页图证据编号", ""),
                "私有页图SHA256": manifest_row.get("私有页图SHA256", ""),
                "私有OCR文本证据编号": manifest_row.get("私有OCR文本证据编号", ""),
                "私有OCR文本SHA256": manifest_row.get("私有OCR文本SHA256", ""),
                "核验动作代码": "repair_field_gap_with_pdf_hubei_official_and_school_source",
                "人工核验结论状态": "pending_manual_field_review",
                "人工确认值": "",
                "人工证据编号": "",
                "人工证据SHA256": "",
                "下一步": "回看PDF原页字段列；再用湖北官方系统/省招办计划和高校官网/章程交叉确认，不得把空值当成不限或无计划。",
            })

    rows.sort(key=lambda row: (
        as_int(row.get("来源页码")),
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        as_int(row.get("专业组内专业序号")),
        {"再选科目": 1, "专业计划数": 2, "学费": 3}.get(row.get("字段名"), 99),
    ))
    fields = [
        "字段补证任务ID",
        "来源字段保真总账ID",
        "来源全量证据工作台ID",
        "来源证据闭环任务ID",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "可进入下一阶段",
        "证据状态",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "字段名",
        "OCR候选值",
        "OCR数字候选",
        "字段问题类型",
        "高风险字段集合",
        "风险触发规则",
        "页级保真队列ID",
        "页面复核优先级",
        "页面阻断等级",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "核验动作代码",
        "人工核验结论状态",
        "人工确认值",
        "人工证据编号",
        "人工证据SHA256",
        "下一步",
    ]
    write_csv(FIELD_GAP_OUTPUT, rows, fields)
    FIELD_GAP_SUMMARY.write_text(json.dumps({
        "status": "issue19_p1_field_gap_evidence_repair_matrix_not_final",
        "generated_by": "build_issue19_major_level_evidence_worktables.py",
        "source_full_major_field_fidelity_ledger": "data/working/issue19-full-major-field-fidelity-ledger.csv",
        "source_full_major_evidence_workbench": "data/working/issue19-full-major-evidence-workbench.csv",
        "source_closure_tasks": "data/working/issue19-full-major-evidence-closure-tasks.csv",
        "source_page_manifest": "data/working/issue19-page-manifest.csv",
        "source_page_fidelity_review_queue": "data/working/issue19-page-fidelity-review-queue.csv",
        "output_table": "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv",
        "row_count": len(rows),
        "unique_task_id_count": len({row["字段补证任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "field_counts": dict(Counter(row["字段名"] for row in rows)),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "notes": [
            "本表一行一个招生专业明细和一个字段缺口。",
            "字段缺口来自全量逐专业字段保真总账的高风险字段集合，不把空值解释为不限或无计划。",
        ],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_hubei_official_packets(indexes):
    rows = []
    for full_row in indexes["full_rows"]:
        task_row = indexes["hubei_task_by_major_id"].get(full_row.get("专业行ID"), {})
        rows.append({
            "湖北官方核验包任务ID": stable_id(
                "HBPLAN",
                [full_row.get("专业行ID", ""), task_row.get("证据闭环任务ID", "")],
            ),
            "来源证据闭环任务ID": task_row.get("证据闭环任务ID", ""),
            "来源全量证据工作台ID": full_row.get("全量证据工作台ID", ""),
            "来源期号": full_row.get("来源期号", ""),
            "来源PDF_SHA256": full_row.get("来源PDF_SHA256", ""),
            "数据阶段": "issue19_hubei_official_plan_major_crosscheck_packets",
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×湖北官方系统核验",
            "最终可用": "false",
            "是否可升级": "false",
            "专业行ID": full_row.get("专业行ID", ""),
            "专业组出现ID": full_row.get("专业组出现ID", ""),
            "院校代码": full_row.get("院校代码", ""),
            "院校名称OCR": full_row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": full_row.get("院校专业组代码OCR规范化", ""),
            "来源页码": full_row.get("来源页码", ""),
            "专业组内专业序号": full_row.get("专业组内专业序号", ""),
            "专业代号OCR": full_row.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": short_text(full_row.get("专业名称及备注OCR")),
            "OCR再选科目": full_row.get("再选科目OCR候选", ""),
            "OCR专业计划数": full_row.get("专业计划数OCR候选", ""),
            "OCR学费": full_row.get("学费OCR候选", ""),
            "平台查询院校代码": full_row.get("院校代码", ""),
            "平台查询专业组代码": full_row.get("院校专业组代码OCR规范化", ""),
            "平台查询专业代号": full_row.get("专业代号OCR", ""),
            "平台匹配状态": "pending_hubei_official_platform_query",
            "平台字段核验状态": "pending_hubei_official_plan_review",
            "字段差异集合": "",
            "官方系统证据编号": "",
            "官方系统证据SHA256": "",
            "原始接口响应保存位置": "私有原始响应留存，不提交公开仓库",
            "公开原始行SHA256": "",
            "下一步": "用湖北招生数智综合平台或最终志愿系统逐专业核验；公开仓库只保存规范化字段、哈希和状态，不保存登录态或原始接口全文。",
        })
    rows.sort(key=lambda row: (
        as_int(row.get("来源页码")),
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        as_int(row.get("专业组内专业序号")),
    ))
    fields = [
        "湖北官方核验包任务ID",
        "来源证据闭环任务ID",
        "来源全量证据工作台ID",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "是否可升级",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "OCR再选科目",
        "OCR专业计划数",
        "OCR学费",
        "平台查询院校代码",
        "平台查询专业组代码",
        "平台查询专业代号",
        "平台匹配状态",
        "平台字段核验状态",
        "字段差异集合",
        "官方系统证据编号",
        "官方系统证据SHA256",
        "原始接口响应保存位置",
        "公开原始行SHA256",
        "下一步",
    ]
    write_csv(HUBEI_OFFICIAL_OUTPUT, rows, fields)
    HUBEI_OFFICIAL_SUMMARY.write_text(json.dumps({
        "status": "issue19_hubei_official_plan_major_crosscheck_packets_not_final",
        "generated_by": "build_issue19_major_level_evidence_worktables.py",
        "source_full_major_evidence_workbench": "data/working/issue19-full-major-evidence-workbench.csv",
        "source_closure_tasks": "data/working/issue19-full-major-evidence-closure-tasks.csv",
        "output_table": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
        "row_count": len(rows),
        "unique_task_id_count": len({row["湖北官方核验包任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_source_closure_task_id_count": len({row["来源证据闭环任务ID"] for row in rows}),
        "platform_status_counts": dict(Counter(row["平台字段核验状态"] for row in rows)),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "auto_upgrade_allowed_count": sum(row["是否可升级"] == "true" for row in rows),
        "notes": [
            "本表一行一个招生专业明细和一个湖北官方系统核验任务。",
            "公开仓库不保存登录态、密钥、原始接口全文或最终建议结论。",
        ],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def best_match_index(match_rows):
    exact = {}
    fallback = {}
    for row in match_rows:
        key = (
            row.get("院校代码", ""),
            row.get("2026院校专业组代码", ""),
            row.get("专业代号OCR", ""),
            row.get("专业名称及备注OCR", ""),
        )
        exact[key] = row
        fallback_key = (
            row.get("院校代码", ""),
            row.get("专业代号OCR", ""),
            row.get("专业名称及备注OCR", ""),
        )
        fallback[fallback_key] = row
    return exact, fallback


def build_b0b1_diff_ledger(indexes):
    exact_match, fallback_match = best_match_index(indexes["match_rows"])
    rows = []
    for full_row in indexes["full_rows"]:
        source_status = full_row.get("高校官网/章程辅证状态", "")
        if source_status == "not_yet_school_source_searched_in_full_workbench":
            continue
        match_row = exact_match.get((
            full_row.get("院校代码", ""),
            full_row.get("院校专业组代码OCR规范化", ""),
            full_row.get("专业代号OCR", ""),
            full_row.get("专业名称及备注OCR", ""),
        )) or fallback_match.get((
            full_row.get("院校代码", ""),
            full_row.get("专业代号OCR", ""),
            full_row.get("专业名称及备注OCR", ""),
        ), {})
        effective_source_status = match_row.get("官网来源状态") or source_status
        diff_fields = []
        if (
            full_row.get("B0B1计划冲突来源明细ID")
            or match_row.get("计划数核验状态") == "mismatch"
        ):
            diff_fields.append("计划数冲突")
        if full_row.get("B0B1未匹配专业来源明细ID"):
            diff_fields.append("官网专业未匹配")
        if not match_row.get("最佳官网来源文件") and effective_source_status in {
            "needs_official_plan_source_search",
            "has_partial_source_needs_followup",
        }:
            diff_fields.append("官网计划源待补强")
        if effective_source_status == "charter_or_rules_only_no_plan":
            diff_fields.append("仅章程或规则线索")
        rows.append({
            "公开官网差异账ID": stable_id("B0B1DIFF", [full_row.get("专业行ID", "")]),
            "来源全量证据工作台ID": full_row.get("全量证据工作台ID", ""),
            "来源期号": full_row.get("来源期号", ""),
            "来源PDF_SHA256": full_row.get("来源PDF_SHA256", ""),
            "数据阶段": "issue19_b0_b1_public_official_diff_ledger",
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "专业行ID": full_row.get("专业行ID", ""),
            "专业组出现ID": full_row.get("专业组出现ID", ""),
            "院校代码": full_row.get("院校代码", ""),
            "院校名称OCR": full_row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": full_row.get("院校专业组代码OCR规范化", ""),
            "来源页码": full_row.get("来源页码", ""),
            "专业组内专业序号": full_row.get("专业组内专业序号", ""),
            "专业代号OCR": full_row.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": short_text(full_row.get("专业名称及备注OCR")),
            "OCR计划数": full_row.get("专业计划数OCR候选", ""),
            "OCR学费": full_row.get("学费OCR候选", ""),
            "OCR再选科目": full_row.get("再选科目OCR候选", ""),
            "高校官网/章程辅证状态": effective_source_status,
            "官网来源状态": effective_source_status,
            "官网证据匹配状态": match_row.get("官网证据匹配状态", ""),
            "最佳官网来源文件": match_row.get("最佳官网来源文件", ""),
            "最佳官网专业名称": match_row.get("最佳官网专业名称", full_row.get("最佳官网专业名称", "")),
            "最佳官网专业代号": match_row.get("最佳官网专业代号", ""),
            "最佳官网计划数": match_row.get("最佳官网计划数", full_row.get("最佳官网计划数", "")),
            "最佳官网学费": match_row.get("最佳官网学费", full_row.get("最佳官网学费", "")),
            "最佳官网选科": match_row.get("最佳官网选科", ""),
            "专业名称匹配方式": match_row.get("专业名称匹配方式", ""),
            "专业名称匹配分": match_row.get("专业名称匹配分", ""),
            "计划数核验状态": full_row.get("计划数核验状态", "") or match_row.get("计划数核验状态", ""),
            "差异字段集合": "；".join(diff_fields),
            "仍需核验": match_row.get("仍需核验", "PDF原页；湖北官方系统；高校官网/章程；家庭接受度；调剂范围"),
            "下一步": "官网证据只作交叉校验；计划、专业组边界和最终建议判断必须以湖北官方系统/省招办计划和最终志愿系统为准。",
        })
    rows.sort(key=lambda row: (
        as_int(row.get("来源页码")),
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        as_int(row.get("专业组内专业序号")),
    ))
    fields = [
        "公开官网差异账ID",
        "来源全量证据工作台ID",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "可进入下一阶段",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "OCR计划数",
        "OCR学费",
        "OCR再选科目",
        "高校官网/章程辅证状态",
        "官网来源状态",
        "官网证据匹配状态",
        "最佳官网来源文件",
        "最佳官网专业名称",
        "最佳官网专业代号",
        "最佳官网计划数",
        "最佳官网学费",
        "最佳官网选科",
        "专业名称匹配方式",
        "专业名称匹配分",
        "计划数核验状态",
        "差异字段集合",
        "仍需核验",
        "下一步",
    ]
    write_csv(B0B1_DIFF_OUTPUT, rows, fields)
    B0B1_DIFF_SUMMARY.write_text(json.dumps({
        "status": "issue19_b0_b1_public_official_diff_ledger_not_final",
        "generated_by": "build_issue19_major_level_evidence_worktables.py",
        "source_full_major_evidence_workbench": "data/working/issue19-full-major-evidence-workbench.csv",
        "source_b0_b1_retained_official_plan_normalized": "data/working/issue19-b0-b1-retained-official-plan-normalized.csv",
        "source_b0_b1_official_evidence_match": "data/working/issue19-candidate-v3-b0-b1-official-evidence-match.csv",
        "output_table": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
        "row_count": len(rows),
        "unique_diff_id_count": len({row["公开官网差异账ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "school_source_status_counts": dict(Counter(row["高校官网/章程辅证状态"] for row in rows)),
        "match_status_counts": dict(Counter(row["官网证据匹配状态"] for row in rows)),
        "plan_conflict_count": sum("计划数冲突" in row["差异字段集合"] for row in rows),
        "unmatched_major_count": sum("官网专业未匹配" in row["差异字段集合"] for row in rows),
        "source_match_hit_count": sum(bool(row["最佳官网来源文件"]) for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "notes": [
            "本表一行一个已有官网/章程辅证线索的招生专业明细。",
            "高校官网/API/PDF/图片抽取只作辅证，不替代湖北官方系统或省招办计划。",
        ],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    indexes = build_indexes()
    build_field_gap_matrix(indexes)
    build_hubei_official_packets(indexes)
    build_b0b1_diff_ledger(indexes)


if __name__ == "__main__":
    main()
