#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIELD_FACT_TASKS = ROOT / "data/working/issue19-field-fact-verification-tasks.csv"
RAW_SOURCE_AUDIT = ROOT / "data/working/issue19-raw-major-source-evidence-audit.csv"
PDF_EVIDENCE_ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
PAGE_FIDELITY_QUEUE = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"

OUTPUT = ROOT / "data/working/issue19-field-fact-p0-reread-worklist.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-fact-p0-reread-worklist-summary.json"

DATA_STAGE = "issue19_field_fact_p0_reread_worklist"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
P0_PRIORITY = "P0-字段无候选原页重读"


FIELDS = [
    "P0字段原页重读任务ID",
    "来源字段事实核验任务队列",
    "来源原始逐专业明细源证据审计",
    "来源专业行原页证据锚点表",
    "来源页级保真复核队列",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动回填候选",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "P0原页重读状态",
    "P0原页重读优先序",
    "页内P0字段任务序",
    "页内P0字段任务数",
    "学校P0字段任务数",
    "专业行P0字段任务数",
    "来源字段事实核验任务ID",
    "专业行ID",
    "字段事实闭环ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "字段名",
    "字段OCR候选",
    "字段人工确认",
    "字段事实状态",
    "字段候选任务数",
    "字段非空候选数",
    "字段候选值集合",
    "字段候选状态集合",
    "字段PDF核验状态",
    "字段湖北官方核验状态",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "字段事实缺口类型",
    "字段缺口数",
    "字段缺口字段",
    "三字段OCR完整状态",
    "页级保真队列ID",
    "页面复核优先级",
    "页面阻断等级",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "OCR平均置信度",
    "OCR_QC_P0数",
    "OCR_QC_P1数",
    "页面专业明细数",
    "页面结构异常数",
    "页面高严重结构异常数",
    "原始专业行源证据审计ID",
    "私有OCR起始行匹配状态",
    "专业起始行号",
    "专业起始y",
    "起始行QC_P0数",
    "起始行QC_P1数",
    "起始行QC规则ID集合",
    "私有OCR起始行文本SHA256",
    "源证据覆盖结论",
    "源证据风险等级",
    "源证据风险标签",
    "专业行原页证据锚点ID",
    "证据锚点状态",
    "专业组标题行号",
    "专业组标题y",
    "OCR窗口y上界",
    "OCR窗口y下界",
    "专业窗口行号范围",
    "合并证据窗口行号范围",
    "专业窗口行数",
    "合并证据窗口行数",
    "窗口文本SHA256",
    "窗口平均置信度",
    "窗口最低置信度",
    "私有窗口证据编号",
    "P0原页重读动作",
    "不得进入原因",
    "下一步",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value, default=0):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return default


def index_by(rows, field):
    return {row.get(field, ""): row for row in rows if row.get(field, "")}


def field_action(field_name):
    if field_name == "专业计划数":
        return "回看PDF原页计划数列，重点排除把学费、学制或专业代号误读为计划数。"
    if field_name == "再选科目":
        return "回看PDF原页再选科目列和专业组标题上下文，不能把空值解释为不限选科。"
    if field_name == "学费":
        return "回看PDF原页学费列，重点排除把计划数、学制或备注数字误读为学费。"
    return "回看PDF原页对应字段列，并保留人工证据编号。"


def build_rows():
    task_rows = read_csv(FIELD_FACT_TASKS)
    raw_source_rows = read_csv(RAW_SOURCE_AUDIT)
    anchor_rows = read_csv(PDF_EVIDENCE_ANCHORS)
    page_rows = read_csv(PAGE_FIDELITY_QUEUE)

    raw_by_major = index_by(raw_source_rows, "专业行ID")
    anchor_by_major = index_by(anchor_rows, "专业行ID")
    page_by_number = index_by(page_rows, "PDF页码")

    p0_tasks = [
        row for row in task_rows
        if row.get("字段核验优先级") == P0_PRIORITY
        and row.get("字段事实状态", "").startswith("K0-")
    ]
    page_p0_counts = Counter(row.get("来源页码", "") for row in p0_tasks)
    school_p0_counts = Counter(
        (row.get("院校代码", ""), row.get("院校名称OCR", ""))
        for row in p0_tasks
    )
    major_p0_counts = Counter(row.get("专业行ID", "") for row in p0_tasks)

    rows = []
    for task in p0_tasks:
        major_id = task.get("专业行ID", "")
        raw = raw_by_major.get(major_id, {})
        anchor = anchor_by_major.get(major_id, {})
        page = page_by_number.get(task.get("来源页码", ""), {})
        rows.append({
            "P0字段原页重读任务ID": stable_id(
                "FIELDP0REREAD",
                [task.get("字段事实核验任务ID", ""), major_id, task.get("字段名", ""), SOURCE_PDF_SHA256],
            ),
            "来源字段事实核验任务队列": "data/working/issue19-field-fact-verification-tasks.csv",
            "来源原始逐专业明细源证据审计": "data/working/issue19-raw-major-source-evidence-audit.csv",
            "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
            "来源页级保真复核队列": "data/working/issue19-page-fidelity-review-queue.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×K0字段原页重读",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "P0原页重读状态": "pending_original_page_reread",
            "P0原页重读优先序": "",
            "页内P0字段任务序": "",
            "页内P0字段任务数": str(page_p0_counts[task.get("来源页码", "")]),
            "学校P0字段任务数": str(school_p0_counts[(task.get("院校代码", ""), task.get("院校名称OCR", ""))]),
            "专业行P0字段任务数": str(major_p0_counts[major_id]),
            "来源字段事实核验任务ID": task.get("字段事实核验任务ID", ""),
            "专业行ID": major_id,
            "字段事实闭环ID": task.get("字段事实闭环ID", ""),
            "专业组出现ID": task.get("专业组出现ID", ""),
            "院校代码": task.get("院校代码", ""),
            "院校名称OCR": task.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": task.get("院校专业组代码OCR规范化", ""),
            "来源页码": task.get("来源页码", ""),
            "版面列": task.get("版面列", ""),
            "专业组内专业序号": task.get("专业组内专业序号", ""),
            "专业代号OCR": task.get("专业代号OCR", ""),
            "专业名称及备注短摘": task.get("专业名称及备注短摘", ""),
            "字段名": task.get("字段名", ""),
            "字段OCR候选": task.get("字段OCR候选", ""),
            "字段人工确认": task.get("字段人工确认", ""),
            "字段事实状态": task.get("字段事实状态", ""),
            "字段候选任务数": task.get("字段候选任务数", ""),
            "字段非空候选数": task.get("字段非空候选数", ""),
            "字段候选值集合": task.get("字段候选值集合", ""),
            "字段候选状态集合": task.get("字段候选状态集合", ""),
            "字段PDF核验状态": task.get("字段PDF核验状态", ""),
            "字段湖北官方核验状态": task.get("字段湖北官方核验状态", ""),
            "字段事实闭环等级": task.get("字段事实闭环等级", ""),
            "字段事实阻断等级": task.get("字段事实阻断等级", ""),
            "字段事实缺口类型": task.get("字段事实缺口类型", ""),
            "字段缺口数": task.get("字段缺口数", ""),
            "字段缺口字段": task.get("字段缺口字段", ""),
            "三字段OCR完整状态": task.get("三字段OCR完整状态", ""),
            "页级保真队列ID": task.get("页级保真队列ID", ""),
            "页面复核优先级": task.get("页面复核优先级", ""),
            "页面阻断等级": task.get("页面阻断等级", ""),
            "私有页图证据编号": task.get("私有页图证据编号", page.get("私有页图证据编号", "")),
            "私有页图SHA256": task.get("私有页图SHA256", page.get("私有页图SHA256", "")),
            "私有OCR文本证据编号": task.get("私有OCR文本证据编号", page.get("私有OCR文本证据编号", "")),
            "私有OCR文本SHA256": task.get("私有OCR文本SHA256", page.get("私有OCR文本SHA256", "")),
            "OCR平均置信度": task.get("OCR平均置信度", page.get("OCR平均置信度", "")),
            "OCR_QC_P0数": task.get("OCR_QC_P0数", page.get("OCR_QC_P0数", "")),
            "OCR_QC_P1数": task.get("OCR_QC_P1数", page.get("OCR_QC_P1数", "")),
            "页面专业明细数": task.get("页面专业明细数", page.get("页面专业明细数", "")),
            "页面结构异常数": task.get("页面结构异常数", page.get("页面结构异常数", "")),
            "页面高严重结构异常数": task.get("页面高严重结构异常数", page.get("页面高严重结构异常数", "")),
            "原始专业行源证据审计ID": raw.get("原始专业行源证据审计ID", ""),
            "私有OCR起始行匹配状态": raw.get("私有OCR起始行匹配状态", ""),
            "专业起始行号": raw.get("专业起始行号", anchor.get("专业起始行号", "")),
            "专业起始y": raw.get("专业起始y", anchor.get("专业起始y", "")),
            "起始行QC_P0数": raw.get("起始行QC_P0数", ""),
            "起始行QC_P1数": raw.get("起始行QC_P1数", ""),
            "起始行QC规则ID集合": raw.get("起始行QC规则ID集合", ""),
            "私有OCR起始行文本SHA256": raw.get("私有OCR起始行文本SHA256", ""),
            "源证据覆盖结论": raw.get("源证据覆盖结论", ""),
            "源证据风险等级": raw.get("源证据风险等级", ""),
            "源证据风险标签": raw.get("源证据风险标签", ""),
            "专业行原页证据锚点ID": anchor.get("专业行原页证据锚点ID", ""),
            "证据锚点状态": anchor.get("证据锚点状态", ""),
            "专业组标题行号": anchor.get("专业组标题行号", ""),
            "专业组标题y": anchor.get("专业组标题y", ""),
            "OCR窗口y上界": anchor.get("OCR窗口y上界", ""),
            "OCR窗口y下界": anchor.get("OCR窗口y下界", ""),
            "专业窗口行号范围": anchor.get("专业窗口行号范围", ""),
            "合并证据窗口行号范围": anchor.get("合并证据窗口行号范围", ""),
            "专业窗口行数": anchor.get("专业窗口行数", ""),
            "合并证据窗口行数": anchor.get("合并证据窗口行数", ""),
            "窗口文本SHA256": anchor.get("窗口文本SHA256", ""),
            "窗口平均置信度": anchor.get("窗口平均置信度", ""),
            "窗口最低置信度": anchor.get("窗口最低置信度", ""),
            "私有窗口证据编号": anchor.get("私有窗口证据编号", ""),
            "P0原页重读动作": field_action(task.get("字段名", "")),
            "不得进入原因": "本清单只安排K0无候选字段的PDF原页重读；没有人工证据编号、湖北官方系统或省招办计划、高校官网/章程闭环前，不得写回字段、推荐学校专业或进入志愿排序。",
            "下一步": "按优先序回看PDF原页、页级OCR文本证据和专业行窗口证据，补出字段候选后进入K1候选回看和湖北官方字段核验。",
        })

    rows.sort(key=lambda row: (
        -as_int(row.get("页内P0字段任务数")),
        as_int(row.get("来源页码"), 999999),
        -as_int(row.get("学校P0字段任务数")),
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        as_int(row.get("专业组内专业序号"), 999999),
        {"专业计划数": 1, "再选科目": 2, "学费": 3}.get(row.get("字段名"), 9),
        row.get("来源字段事实核验任务ID", ""),
    ))
    page_sequence = Counter()
    for index, row in enumerate(rows, start=1):
        page_sequence[row["来源页码"]] += 1
        row["P0原页重读优先序"] = str(index)
        row["页内P0字段任务序"] = str(page_sequence[row["来源页码"]])

    return rows


def top_counts(counter, limit=30):
    return dict(counter.most_common(limit))


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    all_task_rows = read_csv(FIELD_FACT_TASKS)
    raw_source_rows = read_csv(RAW_SOURCE_AUDIT)
    anchor_rows = read_csv(PDF_EVIDENCE_ANCHORS)
    page_rows = read_csv(PAGE_FIDELITY_QUEUE)
    summary = {
        "status": "issue19_field_fact_p0_reread_worklist_not_final",
        "generated_by": "build_issue19_field_fact_p0_reread_worklist.py",
        "output_table": "data/working/issue19-field-fact-p0-reread-worklist.csv",
        "row_grain": "逐专业招生明细×K0字段原页重读",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_task_id_count": len({row["P0字段原页重读任务ID"] for row in rows}),
        "unique_source_field_task_id_count": len({row["来源字段事实核验任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_school_code_name_count": len({(row["院校代码"], row["院校名称OCR"]) for row in rows}),
        "source_counts": {
            "field_fact_verification_task_row_count": len(all_task_rows),
            "raw_source_audit_row_count": len(raw_source_rows),
            "pdf_evidence_anchor_row_count": len(anchor_rows),
            "page_fidelity_queue_row_count": len(page_rows),
        },
        "field_counts": dict(Counter(row["字段名"] for row in rows)),
        "field_status_counts": dict(Counter(row["字段事实状态"] for row in rows)),
        "field_fact_closure_level_counts": dict(Counter(row["字段事实闭环等级"] for row in rows)),
        "source_risk_level_counts": dict(Counter(row["源证据风险等级"] for row in rows)),
        "anchor_status_counts": dict(Counter(row["证据锚点状态"] for row in rows)),
        "page_task_count_top30": top_counts(Counter(row["来源页码"] for row in rows)),
        "school_task_count_top30": top_counts(Counter(
            f"{row['院校代码']}|{row['院校名称OCR']}" for row in rows
        )),
        "field_candidate_task_total_count": sum(as_int(row["字段候选任务数"]) for row in rows),
        "field_candidate_non_empty_total_count": sum(as_int(row["字段非空候选数"]) for row in rows),
        "raw_source_hit_count": sum(bool(row["原始专业行源证据审计ID"]) for row in rows),
        "pdf_anchor_hit_count": sum(bool(row["专业行原页证据锚点ID"]) for row in rows),
        "page_fidelity_hit_count": sum(bool(row["页级保真队列ID"]) for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row["机器是否允许自动写回主表"] == "true" for row in rows),
        "auto_candidate_fill_allowed_count": sum(row["机器是否允许自动回填候选"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "public_safety_note": "本产物只保存P0字段原页重读任务、证据编号、哈希、坐标摘要和状态；不保存私有OCR窗口原文、页图路径、登录态或个人身份信息。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出P0字段原页重读工作清单：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
