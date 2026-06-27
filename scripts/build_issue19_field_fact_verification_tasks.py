#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIELD_FACT_LEDGER = ROOT / "data/working/issue19-field-fact-closure-ledger.csv"
PAGE_FIDELITY_QUEUE = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"

OUTPUT = ROOT / "data/working/issue19-field-fact-verification-tasks.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-fact-verification-tasks-summary.json"

DATA_STAGE = "issue19_field_fact_verification_tasks"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
KEY_FIELDS = ["再选科目", "专业计划数", "学费"]
FIELD_ORDER = {field_name: index for index, field_name in enumerate(KEY_FIELDS, start=1)}


FIELDS = [
    "字段事实核验任务ID",
    "来源字段事实闭环总账",
    "来源页级保真复核队列",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "任务状态",
    "字段核验优先级",
    "字段核验优先序",
    "页内字段任务序",
    "页内字段任务数",
    "页内阻断字段任务数",
    "页内无候选字段任务数",
    "页内有候选字段任务数",
    "页内OCR齐全待核字段任务数",
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
    "字段候选来源类型集合",
    "字段候选置信等级集合",
    "字段候选状态集合",
    "字段PDF核验状态",
    "字段湖北官方核验状态",
    "字段下一步",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "字段事实缺口类型",
    "字段缺口数",
    "字段缺口字段",
    "三字段OCR完整状态",
    "源证据下沉分层",
    "源证据核页优先级",
    "底座稳定性等级",
    "看板动作桶",
    "风险阻断等级",
    "候选初筛闸门状态",
    "初筛动作桶",
    "湖北官方核验包任务ID",
    "高校官网证据匹配状态",
    "B0B1官网证据任务数",
    "官网证据能否替代湖北官方计划",
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
    "字段事实核验动作",
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


def field_priority(status):
    if status.startswith("K0-"):
        return "P0-字段无候选原页重读"
    if status.startswith("K1-"):
        return "P1-字段有候选回看原页和官方"
    if status.startswith("K2-"):
        return "P3-OCR齐全字段三方闭环"
    return "P4-人工确认或异常字段最终门禁复核"


def priority_sort_key(priority):
    order = {
        "P0-字段无候选原页重读": 0,
        "P1-字段有候选回看原页和官方": 1,
        "P3-OCR齐全字段三方闭环": 3,
        "P4-人工确认或异常字段最终门禁复核": 4,
    }
    return order.get(priority, 9)


def field_action(field_name, status):
    if status.startswith("K0-"):
        return f"回看PDF原页对应行、同组上下文和页级OCR证据，补出{field_name}候选。"
    if status.startswith("K1-"):
        return f"用现有候选值核PDF原页，再以湖北官方系统或省招办计划确认{field_name}。"
    if status.startswith("K2-"):
        return f"保留OCR候选，继续用PDF原页、湖北官方系统和高校官网/章程闭环{field_name}。"
    return f"{field_name}进入人工门禁复核，不允许机器自动写回。"


def build_rows():
    field_fact_rows = read_csv(FIELD_FACT_LEDGER)
    page_rows = read_csv(PAGE_FIDELITY_QUEUE)
    page_by_number = index_by(page_rows, "PDF页码")

    rows = []
    for fact_row in field_fact_rows:
        page_row = page_by_number.get(fact_row.get("来源页码", ""), {})
        for field_name in KEY_FIELDS:
            status = fact_row.get(f"{field_name}字段事实状态", "")
            priority = field_priority(status)
            rows.append({
                "字段事实核验任务ID": stable_id(
                    "FIELDVERIFY",
                    [fact_row.get("专业行ID", ""), field_name, SOURCE_PDF_SHA256],
                ),
                "来源字段事实闭环总账": "data/working/issue19-field-fact-closure-ledger.csv",
                "来源页级保真复核队列": "data/working/issue19-page-fidelity-review-queue.csv",
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "数据阶段": DATA_STAGE,
                "主表粒度": "逐专业招生明细",
                "任务粒度": "逐专业招生明细×关键字段",
                "最终可用": "false",
                "可进入下一阶段": "false",
                "机器是否允许自动写回主表": "false",
                "是否允许作为志愿推荐依据": "false",
                "是否允许生成学校专业建议": "false",
                "任务状态": "pending_field_fact_verification",
                "字段核验优先级": priority,
                "字段核验优先序": "",
                "页内字段任务序": "",
                "页内字段任务数": "",
                "页内阻断字段任务数": "",
                "页内无候选字段任务数": "",
                "页内有候选字段任务数": "",
                "页内OCR齐全待核字段任务数": "",
                "专业行ID": fact_row.get("专业行ID", ""),
                "字段事实闭环ID": fact_row.get("字段事实闭环ID", ""),
                "专业组出现ID": fact_row.get("专业组出现ID", ""),
                "院校代码": fact_row.get("院校代码", ""),
                "院校名称OCR": fact_row.get("院校名称OCR", ""),
                "院校专业组代码OCR规范化": fact_row.get("院校专业组代码OCR规范化", ""),
                "来源页码": fact_row.get("来源页码", ""),
                "版面列": fact_row.get("版面列", ""),
                "专业组内专业序号": fact_row.get("专业组内专业序号", ""),
                "专业代号OCR": fact_row.get("专业代号OCR", ""),
                "专业名称及备注短摘": fact_row.get("专业名称及备注短摘", ""),
                "字段名": field_name,
                "字段OCR候选": fact_row.get(f"{field_name}OCR候选", ""),
                "字段人工确认": fact_row.get(f"{field_name}人工确认", ""),
                "字段事实状态": status,
                "字段候选任务数": fact_row.get(f"{field_name}候选任务数", ""),
                "字段非空候选数": fact_row.get(f"{field_name}非空候选数", ""),
                "字段候选值集合": fact_row.get(f"{field_name}候选值集合", ""),
                "字段候选来源类型集合": fact_row.get(f"{field_name}候选来源类型集合", ""),
                "字段候选置信等级集合": fact_row.get(f"{field_name}候选置信等级集合", ""),
                "字段候选状态集合": fact_row.get(f"{field_name}候选状态集合", ""),
                "字段PDF核验状态": fact_row.get(f"{field_name}PDF核验状态", ""),
                "字段湖北官方核验状态": fact_row.get(f"{field_name}官方核验状态", ""),
                "字段下一步": fact_row.get(f"{field_name}下一步", ""),
                "字段事实闭环等级": fact_row.get("字段事实闭环等级", ""),
                "字段事实阻断等级": fact_row.get("字段事实阻断等级", ""),
                "字段事实缺口类型": fact_row.get("字段事实缺口类型", ""),
                "字段缺口数": fact_row.get("字段缺口数", ""),
                "字段缺口字段": fact_row.get("字段缺口字段", ""),
                "三字段OCR完整状态": fact_row.get("三字段OCR完整状态", ""),
                "源证据下沉分层": fact_row.get("源证据下沉分层", ""),
                "源证据核页优先级": fact_row.get("源证据核页优先级", ""),
                "底座稳定性等级": fact_row.get("底座稳定性等级", ""),
                "看板动作桶": fact_row.get("看板动作桶", ""),
                "风险阻断等级": fact_row.get("风险阻断等级", ""),
                "候选初筛闸门状态": fact_row.get("候选初筛闸门状态", ""),
                "初筛动作桶": fact_row.get("初筛动作桶", ""),
                "湖北官方核验包任务ID": fact_row.get("湖北官方核验包任务ID", ""),
                "高校官网证据匹配状态": fact_row.get("高校官网证据匹配状态", ""),
                "B0B1官网证据任务数": fact_row.get("B0B1官网证据任务数", ""),
                "官网证据能否替代湖北官方计划": fact_row.get("官网证据能否替代湖北官方计划", ""),
                "页级保真队列ID": page_row.get("页级保真队列ID", ""),
                "页面复核优先级": page_row.get("页面复核优先级", ""),
                "页面阻断等级": page_row.get("页面阻断等级", ""),
                "私有页图证据编号": page_row.get("私有页图证据编号", ""),
                "私有页图SHA256": page_row.get("私有页图SHA256", ""),
                "私有OCR文本证据编号": page_row.get("私有OCR文本证据编号", ""),
                "私有OCR文本SHA256": page_row.get("私有OCR文本SHA256", ""),
                "OCR平均置信度": page_row.get("OCR平均置信度", ""),
                "OCR_QC_P0数": page_row.get("OCR_QC_P0数", ""),
                "OCR_QC_P1数": page_row.get("OCR_QC_P1数", ""),
                "页面专业明细数": page_row.get("页面专业明细数", ""),
                "页面结构异常数": page_row.get("页面结构异常数", ""),
                "页面高严重结构异常数": page_row.get("页面高严重结构异常数", ""),
                "字段事实核验动作": field_action(field_name, status),
                "不得进入原因": "该任务只安排字段核验；字段未经PDF原页、湖北官方系统或省招办计划、高校官网/章程闭环前，不得用于志愿推荐、学校专业建议或排序。",
                "下一步": fact_row.get(f"{field_name}下一步", ""),
            })

    page_task_count = Counter(row["来源页码"] for row in rows)
    page_k0_count = Counter(row["来源页码"] for row in rows if row["字段事实状态"].startswith("K0-"))
    page_k1_count = Counter(row["来源页码"] for row in rows if row["字段事实状态"].startswith("K1-"))
    page_k2_count = Counter(row["来源页码"] for row in rows if row["字段事实状态"].startswith("K2-"))

    rows.sort(key=lambda row: (
        priority_sort_key(row.get("字段核验优先级", "")),
        as_int(row.get("来源页码"), 999999),
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        as_int(row.get("专业组内专业序号"), 999999),
        FIELD_ORDER.get(row.get("字段名"), 99),
        row.get("专业行ID", ""),
    ))

    page_sequence = Counter()
    for index, row in enumerate(rows, start=1):
        page = row["来源页码"]
        page_sequence[page] += 1
        row["字段核验优先序"] = str(index)
        row["页内字段任务序"] = str(page_sequence[page])
        row["页内字段任务数"] = str(page_task_count[page])
        row["页内阻断字段任务数"] = str(page_k0_count[page])
        row["页内无候选字段任务数"] = str(page_k0_count[page])
        row["页内有候选字段任务数"] = str(page_k1_count[page])
        row["页内OCR齐全待核字段任务数"] = str(page_k2_count[page])

    return rows


def top_counts(counter, limit=30):
    return dict(counter.most_common(limit))


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    field_fact_rows = read_csv(FIELD_FACT_LEDGER)
    page_rows = read_csv(PAGE_FIDELITY_QUEUE)
    summary = {
        "status": "issue19_field_fact_verification_tasks_not_final",
        "generated_by": "build_issue19_field_fact_verification_tasks.py",
        "output_table": "data/working/issue19-field-fact-verification-tasks.csv",
        "row_grain": "逐专业招生明细×关键字段",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_task_id_count": len({row["字段事实核验任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "source_counts": {
            "field_fact_ledger_row_count": len(field_fact_rows),
            "page_fidelity_queue_row_count": len(page_rows),
        },
        "field_counts": dict(Counter(row["字段名"] for row in rows)),
        "field_status_counts": dict(Counter(row["字段事实状态"] for row in rows)),
        "field_priority_counts": dict(Counter(row["字段核验优先级"] for row in rows)),
        "field_candidate_task_total_count": sum(as_int(row["字段候选任务数"]) for row in rows),
        "field_candidate_non_empty_total_count": sum(as_int(row["字段非空候选数"]) for row in rows),
        "page_fidelity_hit_task_count": sum(bool(row["页级保真队列ID"]) for row in rows),
        "page_task_count_top30": top_counts(Counter(row["来源页码"] for row in rows)),
        "page_blocking_field_task_count_top30": top_counts(
            Counter(row["来源页码"] for row in rows if row["字段事实状态"].startswith("K0-"))
        ),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row["机器是否允许自动写回主表"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "public_safety_note": "本产物只保存字段核验任务、候选值集合、证据编号、哈希和状态；不保存私有OCR窗口原文、页图路径、登录态或个人身份信息。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出字段事实核验任务队列：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
