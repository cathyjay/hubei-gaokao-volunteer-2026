#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TRIAGE_WORKBENCH = ROOT / "data/working/issue19-field-fact-p0-triage-execution-workbench.csv"
OUTPUT = ROOT / "data/working/issue19-field-fact-p0-immediate-review-packet.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-fact-p0-immediate-review-packet-summary.json"

DATA_STAGE = "issue19_field_fact_p0_immediate_review_packet"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"

IMMEDIATE_BATCHES = {
    "EXEC-01-冲突异常立即核页": "IR-01-冲突异常和偏大先核",
    "EXEC-02-计划数偏大重点核页": "IR-01-冲突异常和偏大先核",
    "EXEC-03-高校辅证线索三方核验": "IR-02-高校辅证线索先核",
    "EXEC-04-多值坐标冲突核页": "IR-03-多值坐标冲突先核",
}

IMMEDIATE_STAGE_ORDER = {
    "IR-01-冲突异常和偏大先核": 1,
    "IR-02-高校辅证线索先核": 2,
    "IR-03-多值坐标冲突先核": 3,
}

FIELDS = [
    "P0字段即时复核任务ID",
    "来源P0字段三方核验执行工作台",
    "来源P0字段三方核验任务ID",
    "来源P0字段三方核验执行包ID",
    "来源P0字段语义与多源线索审计表",
    "来源专业行原页证据锚点表",
    "来源P0字段闭环推进工作台",
    "来源湖北官方系统核验包",
    "来源B0B1高校官网辅证旁挂表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动回填候选",
    "是否允许写回字段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "即时复核总序",
    "即时复核阶段",
    "即时复核阶段序号",
    "即时复核原因",
    "即时复核动作",
    "必须核验步骤",
    "是否需要双人复核",
    "执行批次",
    "执行方式",
    "执行总序",
    "执行优先级数值",
    "语义多源优先桶",
    "语义多源执行优先级",
    "P0闭环动作桶",
    "P0闭环批次",
    "P0字段语义多源审计ID",
    "P0字段闭环推进任务ID",
    "P0字段机器候选任务ID",
    "来源P0字段原页重读任务ID",
    "来源字段事实核验任务ID",
    "字段事实闭环ID",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "来源页码",
    "版面列",
    "字段名",
    "专业行原页证据锚点ID",
    "专业起始行号",
    "专业窗口行号范围",
    "OCR窗口y上界",
    "OCR窗口y下界",
    "窗口坐标摘要",
    "窗口文本SHA256",
    "起始行文本SHA256",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "私有窗口证据编号",
    "机器候选状态",
    "机器候选置信等级",
    "机器候选规则ID",
    "机器候选字段值",
    "机器候选规范值",
    "机器候选语义状态",
    "机器候选语义风险标签",
    "机器候选语义后可作为核页线索",
    "候选证据行号集合",
    "候选证据x集合",
    "候选证据y集合",
    "高校官网辅证覆盖状态",
    "高校官网证据旁挂ID",
    "高校官网证据强度",
    "高校官网证据匹配状态",
    "高校官网字段候选值",
    "高校官网字段规范值",
    "高校官网字段来源文件",
    "机器候选与高校辅证关系",
    "湖北官方核验包任务ID",
    "湖北官方平台匹配状态",
    "湖北官方字段核验状态",
    "湖北官方证据编号",
    "湖北官方证据SHA256",
    "PDF原页核页状态",
    "PDF原页人工读数",
    "湖北官方系统或省招办计划核验状态",
    "湖北官方字段值",
    "高校官网或招生章程辅证状态",
    "高校官网或招生章程字段值",
    "三方字段一致性状态",
    "字段事实写回状态",
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


def immediate_reason(row):
    batch = row.get("执行批次", "")
    if batch.startswith("EXEC-01-"):
        return "冲突或语义异常字段，先核 PDF 原页并保留多源差异。"
    if batch.startswith("EXEC-02-"):
        return "计划数候选偏大，需优先排除串列、串行或相邻数字误读。"
    if batch.startswith("EXEC-03-"):
        return "高校官网或章程已有字段线索，优先用作 PDF 原页和湖北官方字段闭环入口。"
    if batch.startswith("EXEC-04-"):
        return "同一字段存在多值坐标候选，需优先回页确认字段列和专业行边界。"
    return "不在即时复核批次内。"


def immediate_action(row):
    batch = row.get("执行批次", "")
    if batch.startswith("EXEC-01-"):
        return "双人回看 PDF 原页；核机器候选、高校辅证和湖北官方待核包；冲突不写回。"
    if batch.startswith("EXEC-02-"):
        return "双人回看 PDF 原页，重点核计划数字段和相邻数字；必要时对照高校辅证和湖北官方计划。"
    if batch.startswith("EXEC-03-"):
        return "按高校辅证值回看 PDF 原页；再等待或接入湖北官方计划字段核验。"
    if batch.startswith("EXEC-04-"):
        return "逐个候选坐标回看 PDF 原页；确认唯一人工读数前保持字段阻断。"
    return "保持待判。"


def build_rows():
    parent_rows = read_csv(TRIAGE_WORKBENCH)
    triage_rows = [
        row for row in parent_rows
        if row.get("执行批次", "") in IMMEDIATE_BATCHES
    ]
    sorted_rows = triage_rows

    output_rows = []
    for index, row in enumerate(sorted_rows, start=1):
        immediate_stage = IMMEDIATE_BATCHES[row.get("执行批次", "")]
        output_rows.append({
            "P0字段即时复核任务ID": stable_id(
                "P0IMMEDIATE",
                [row.get("P0字段三方核验任务ID", ""), row.get("专业行ID", ""), row.get("字段名", "")],
            ),
            "来源P0字段三方核验执行工作台": "data/working/issue19-field-fact-p0-triage-execution-workbench.csv",
            "来源P0字段三方核验任务ID": row.get("P0字段三方核验任务ID", ""),
            "来源P0字段三方核验执行包ID": row.get("P0字段三方核验执行包ID", ""),
            "来源P0字段语义与多源线索审计表": row.get("来源P0字段语义与多源线索审计表", ""),
            "来源专业行原页证据锚点表": row.get("来源专业行原页证据锚点表", ""),
            "来源P0字段闭环推进工作台": row.get("来源P0字段闭环推进工作台", ""),
            "来源湖北官方系统核验包": row.get("来源湖北官方系统核验包", ""),
            "来源B0B1高校官网辅证旁挂表": row.get("来源B0B1高校官网辅证旁挂表", ""),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0字段×即时复核批次",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "即时复核总序": str(index),
            "即时复核阶段": immediate_stage,
            "即时复核阶段序号": str(IMMEDIATE_STAGE_ORDER[immediate_stage]),
            "即时复核原因": immediate_reason(row),
            "即时复核动作": immediate_action(row),
            "必须核验步骤": row.get("必须核验步骤", ""),
            "是否需要双人复核": row.get("是否需要双人复核", ""),
            "执行批次": row.get("执行批次", ""),
            "执行方式": row.get("执行方式", ""),
            "执行总序": row.get("执行总序", ""),
            "执行优先级数值": row.get("执行优先级数值", ""),
            "语义多源优先桶": row.get("语义多源优先桶", ""),
            "语义多源执行优先级": row.get("语义多源执行优先级", ""),
            "P0闭环动作桶": row.get("P0闭环动作桶", ""),
            "P0闭环批次": row.get("P0闭环批次", ""),
            "P0字段语义多源审计ID": row.get("P0字段语义多源审计ID", ""),
            "P0字段闭环推进任务ID": row.get("P0字段闭环推进任务ID", ""),
            "P0字段机器候选任务ID": row.get("P0字段机器候选任务ID", ""),
            "来源P0字段原页重读任务ID": row.get("来源P0字段原页重读任务ID", ""),
            "来源字段事实核验任务ID": row.get("来源字段事实核验任务ID", ""),
            "字段事实闭环ID": row.get("字段事实闭环ID", ""),
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "字段名": row.get("字段名", ""),
            "专业行原页证据锚点ID": row.get("专业行原页证据锚点ID", ""),
            "专业起始行号": row.get("专业起始行号", ""),
            "专业窗口行号范围": row.get("专业窗口行号范围", ""),
            "OCR窗口y上界": row.get("OCR窗口y上界", ""),
            "OCR窗口y下界": row.get("OCR窗口y下界", ""),
            "窗口坐标摘要": row.get("窗口坐标摘要", ""),
            "窗口文本SHA256": row.get("窗口文本SHA256", ""),
            "起始行文本SHA256": row.get("起始行文本SHA256", ""),
            "私有页图证据编号": row.get("私有页图证据编号", ""),
            "私有页图SHA256": row.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": row.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": row.get("私有OCR文本SHA256", ""),
            "私有窗口证据编号": row.get("私有窗口证据编号", ""),
            "机器候选状态": row.get("机器候选状态", ""),
            "机器候选置信等级": row.get("机器候选置信等级", ""),
            "机器候选规则ID": row.get("机器候选规则ID", ""),
            "机器候选字段值": row.get("机器候选字段值", ""),
            "机器候选规范值": row.get("机器候选规范值", ""),
            "机器候选语义状态": row.get("机器候选语义状态", ""),
            "机器候选语义风险标签": row.get("机器候选语义风险标签", ""),
            "机器候选语义后可作为核页线索": row.get("机器候选语义后可作为核页线索", ""),
            "候选证据行号集合": row.get("候选证据行号集合", ""),
            "候选证据x集合": row.get("候选证据x集合", ""),
            "候选证据y集合": row.get("候选证据y集合", ""),
            "高校官网辅证覆盖状态": row.get("高校官网辅证覆盖状态", ""),
            "高校官网证据旁挂ID": row.get("高校官网证据旁挂ID", ""),
            "高校官网证据强度": row.get("高校官网证据强度", ""),
            "高校官网证据匹配状态": row.get("高校官网证据匹配状态", ""),
            "高校官网字段候选值": row.get("高校官网字段候选值", ""),
            "高校官网字段规范值": row.get("高校官网字段规范值", ""),
            "高校官网字段来源文件": row.get("高校官网字段来源文件", ""),
            "机器候选与高校辅证关系": row.get("机器候选与高校辅证关系", ""),
            "湖北官方核验包任务ID": row.get("湖北官方核验包任务ID", ""),
            "湖北官方平台匹配状态": row.get("湖北官方平台匹配状态", ""),
            "湖北官方字段核验状态": row.get("湖北官方字段核验状态", ""),
            "湖北官方证据编号": row.get("湖北官方证据编号", ""),
            "湖北官方证据SHA256": row.get("湖北官方证据SHA256", ""),
            "PDF原页核页状态": row.get("PDF原页核页状态", ""),
            "PDF原页人工读数": "",
            "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统或省招办计划核验状态", ""),
            "湖北官方字段值": "",
            "高校官网或招生章程辅证状态": row.get("高校官网或招生章程辅证状态", ""),
            "高校官网或招生章程字段值": "",
            "三方字段一致性状态": row.get("三方字段一致性状态", ""),
            "字段事实写回状态": row.get("字段事实写回状态", ""),
            "不得进入原因": (
                "本行只是P0字段即时复核任务；PDF原页、湖北官方系统或省招办计划、"
                "高校官网或章程未三方闭环前，不得写回字段、进入志愿排序或形成报考结论。"
            ),
            "下一步": "先按即时复核总序核 PDF 原页；再核湖北官方计划和高校官网/章程；闭环后另建人工确认表。",
        })
    return output_rows


def top_counter(counter, limit=30):
    return dict(counter.most_common(limit))


def school_source_public_ok(source):
    if not source:
        return True
    parts = [part.strip() for part in source.replace("；", ";").split(";") if part.strip()]
    return bool(parts) and all(
        part.startswith((
            "data/external/issue19-b0-b1-official-sources/",
            "data/external/issue19-sample-school-official/",
        ))
        and not part.startswith("/")
        and "\\" not in part
        and (ROOT / part).exists()
        for part in parts
    )


def write_summary(rows, parent_row_count):
    field_counts = Counter(row["字段名"] for row in rows)
    batch_counts = Counter(row["执行批次"] for row in rows)
    stage_counts = Counter(row["即时复核阶段"] for row in rows)
    mode_counts = Counter(row["执行方式"] for row in rows)
    priority_counts = Counter(row["语义多源优先桶"] for row in rows)
    relation_counts = Counter(row["机器候选与高校辅证关系"] for row in rows)
    page_counts = Counter(row["来源页码"] for row in rows)
    school_counts = Counter(row["院校代码"] for row in rows)

    summary = {
        "status": "issue19_field_fact_p0_immediate_review_packet_not_final",
        "generated_by": "build_issue19_field_fact_p0_immediate_review_packet.py",
        "source_parent_table": "data/working/issue19-field-fact-p0-triage-execution-workbench.csv",
        "source_triage_execution_workbench": "data/working/issue19-field-fact-p0-triage-execution-workbench.csv",
        "output_table": "data/working/issue19-field-fact-p0-immediate-review-packet.csv",
        "row_grain": "逐专业招生明细×P0字段×即时复核批次",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "included_execution_batches": list(IMMEDIATE_BATCHES),
        "parent_row_count": parent_row_count,
        "slice_row_count": len(rows),
        "slice_filter": "执行批次 in EXEC-01/EXEC-02/EXEC-03/EXEC-04",
        "row_count": len(rows),
        "unique_immediate_task_id_count": len({row["P0字段即时复核任务ID"] for row in rows}),
        "unique_source_triage_task_id_count": len({row["来源P0字段三方核验任务ID"] for row in rows}),
        "unique_execution_package_id_count": len({row["来源P0字段三方核验执行包ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_school_code_count": len({row["院校代码"] for row in rows}),
        "field_counts": dict(field_counts),
        "execution_batch_counts": dict(batch_counts),
        "immediate_stage_counts": dict(stage_counts),
        "execution_mode_counts": dict(mode_counts),
        "semantic_priority_bucket_counts": dict(priority_counts),
        "crosssource_relation_counts": dict(relation_counts),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in rows),
        "pdf_anchor_link_count": sum(bool(row["专业行原页证据锚点ID"]) for row in rows),
        "hubei_official_packet_link_count": sum(bool(row["湖北官方核验包任务ID"]) for row in rows),
        "school_sidecar_row_count": sum(row["高校官网辅证覆盖状态"] == "has_b0b1_school_sidecar" for row in rows),
        "school_sidecar_field_value_count": sum(bool(row["高校官网字段候选值"]) for row in rows),
        "school_source_bad_count": sum(not school_source_public_ok(row["高校官网字段来源文件"]) for row in rows),
        "pdf_manual_review_pending_count": sum(row["PDF原页核页状态"] == "pending_pdf_manual_review" for row in rows),
        "hubei_official_review_pending_count": sum(row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_plan_review" for row in rows),
        "three_way_closure_pending_count": sum(row["三方字段一致性状态"] == "pending_three_way_closure" for row in rows),
        "pdf_confirmed_count": sum(bool(row["PDF原页人工读数"]) for row in rows),
        "official_confirmed_count": sum(bool(row["湖北官方字段值"]) for row in rows),
        "school_official_confirmed_count": sum(bool(row["高校官网或招生章程字段值"]) for row in rows),
        "field_writeback_ready_count": sum(row["字段事实写回状态"] != "blocked_until_pdf_hubei_school_three_way_closure" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row["机器是否允许自动写回主表"] == "true" for row in rows),
        "auto_candidate_fill_allowed_count": sum(row["机器是否允许自动回填候选"] == "true" for row in rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "top_pdf_pages": top_counter(page_counts),
        "top_school_codes": top_counter(school_counts),
        "public_safety_note": "本产物只保存字段级即时复核顺序、页码/版面列、证据编号、哈希、机器候选、官网字段线索和待核状态；不保存私有路径、raw OCR 原文、院校名、专业名、专业代号、专业组代码、登录态或个人身份信息。",
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    write_summary(rows, parent_row_count=len(read_csv(TRIAGE_WORKBENCH)))
    print(f"写出P0字段即时复核包：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
