#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SEMANTIC_AUDIT = ROOT / "data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv"
PDF_ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
OUTPUT = ROOT / "data/working/issue19-field-fact-p0-triage-execution-workbench.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-fact-p0-triage-execution-workbench-summary.json"

DATA_STAGE = "issue19_field_fact_p0_triage_execution_workbench"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"


FIELDS = [
    "P0字段三方核验任务ID",
    "P0字段三方核验执行包ID",
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
    "执行总序",
    "执行批次",
    "执行方式",
    "是否需要双人复核",
    "执行优先级数值",
    "语义多源优先桶",
    "语义多源执行优先级",
    "P0闭环动作桶",
    "P0闭环批次",
    "字段核验优先原因",
    "首要核验动作",
    "必须核验步骤",
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


FIELD_ORDER = {
    "专业计划数": 1,
    "再选科目": 2,
    "学费": 3,
}

PRIORITY_ORDER = {
    "S1-多源字段冲突优先核页": 10,
    "S2-机器候选语义异常优先排除": 20,
    "S5-机器候选偏大重点核页": 30,
    "S3-机器与高校辅证一致优先核PDF和湖北官方": 40,
    "S4-高校辅证补缺线索优先核PDF": 50,
    "S6-多值坐标冲突核页": 60,
    "S8-机器候选语义通过常规核页": 70,
    "S7-无坐标候选重读": 80,
    "S9-无机器候选保持原页重读": 90,
}


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


def execution_batch(priority_bucket):
    if priority_bucket in {"S1-多源字段冲突优先核页", "S2-机器候选语义异常优先排除"}:
        return "EXEC-01-冲突异常立即核页"
    if priority_bucket == "S5-机器候选偏大重点核页":
        return "EXEC-02-计划数偏大重点核页"
    if priority_bucket in {
        "S3-机器与高校辅证一致优先核PDF和湖北官方",
        "S4-高校辅证补缺线索优先核PDF",
    }:
        return "EXEC-03-高校辅证线索三方核验"
    if priority_bucket == "S6-多值坐标冲突核页":
        return "EXEC-04-多值坐标冲突核页"
    if priority_bucket == "S8-机器候选语义通过常规核页":
        return "EXEC-05-常规机器候选核页"
    if priority_bucket == "S7-无坐标候选重读":
        return "EXEC-06-无候选原页重读"
    return "EXEC-99-其他待判"


def execution_mode(priority_bucket):
    if priority_bucket in {
        "S1-多源字段冲突优先核页",
        "S2-机器候选语义异常优先排除",
        "S5-机器候选偏大重点核页",
        "S6-多值坐标冲突核页",
    }:
        return "双人复核"
    if priority_bucket in {
        "S3-机器与高校辅证一致优先核PDF和湖北官方",
        "S4-高校辅证补缺线索优先核PDF",
    }:
        return "三方线索优先核验"
    if priority_bucket == "S8-机器候选语义通过常规核页":
        return "常规核页抽检"
    if priority_bucket == "S7-无坐标候选重读":
        return "人工重读或高分辨率OCR"
    return "待判"


def priority_reason(row):
    priority = row.get("语义多源优先桶", "")
    if priority.startswith("S1-"):
        return "机器候选与高校辅证字段冲突，先核原页并保留冲突证据。"
    if priority.startswith("S2-"):
        return "机器候选语义异常，疑似串列、串行或 OCR 噪声。"
    if priority.startswith("S5-"):
        return "计划数偏大，需排除串入代码、学费或合计数字。"
    if priority.startswith("S3-"):
        return "机器候选与高校辅证一致，但仍需 PDF 原页和湖北官方计划闭环。"
    if priority.startswith("S4-"):
        return "高校辅证有字段值而机器无规范候选，可作补缺线索。"
    if priority.startswith("S6-"):
        return "同字段存在多值坐标候选，需回到原页确认字段列和专业行边界。"
    if priority.startswith("S8-"):
        return "机器候选语义通过，可按坐标常规核页但不能自动写回。"
    if priority.startswith("S7-"):
        return "机器未找到可用坐标候选，需人工重读原页或补充高分辨率 OCR。"
    return "未归入已知优先桶，保持待判。"


def primary_action(row):
    priority = row.get("语义多源优先桶", "")
    if priority.startswith("S1-"):
        return "PDF原页核字段列；复核高校辅证来源；冲突保留到三方闭环。"
    if priority.startswith("S2-"):
        return "PDF原页核字段列并判断机器候选是否 OCR 噪声。"
    if priority.startswith("S5-"):
        return "PDF原页重点核计划数字段和相邻数字。"
    if priority.startswith("S3-"):
        return "PDF原页核候选值，再等湖北官方计划核验。"
    if priority.startswith("S4-"):
        return "用高校辅证值回看 PDF 原页，补齐机器缺失字段线索。"
    if priority.startswith("S6-"):
        return "逐个候选坐标回看 PDF 原页。"
    if priority.startswith("S8-"):
        return "按候选坐标常规核 PDF 原页。"
    if priority.startswith("S7-"):
        return "人工重读 PDF 原页对应专业行和字段列。"
    return "保持待判，先补原页证据。"


def required_steps(row):
    priority = row.get("语义多源优先桶", "")
    steps = [
        "1.PDF原页人工核字段",
        "2.湖北官方系统或省招办计划核字段",
        "3.高校官网或招生章程辅证",
        "4.三方字段一致性判定",
    ]
    if priority.startswith("S7-"):
        steps.insert(1, "1A.必要时重跑高分辨率OCR")
    if priority.startswith(("S1-", "S2-", "S5-", "S6-")):
        steps.append("5.双人复核后仍不得自动写回")
    else:
        steps.append("5.人工复核后仍不得自动写回")
    return "；".join(steps)


def bool_text(value):
    return "true" if value else "false"


def school_source_public_ok(source):
    if not source:
        return True
    parts = [part.strip() for part in re.split(r"[;；]", source) if part.strip()]
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


def build_rows():
    semantic_rows = read_csv(SEMANTIC_AUDIT)
    anchors_by_major_id = {row.get("专业行ID", ""): row for row in read_csv(PDF_ANCHORS)}
    sorted_rows = sorted(
        semantic_rows,
        key=lambda row: (
            PRIORITY_ORDER.get(row.get("语义多源优先桶", ""), 999),
            as_int(row.get("来源页码")),
            row.get("版面列", ""),
            row.get("院校代码", ""),
            row.get("专业组出现ID", ""),
            row.get("专业行ID", ""),
            FIELD_ORDER.get(row.get("字段名", ""), 9),
            row.get("P0字段语义多源审计ID", ""),
        ),
    )

    output_rows = []
    for index, row in enumerate(sorted_rows, start=1):
        anchor = anchors_by_major_id.get(row.get("专业行ID", ""), {})
        priority = row.get("语义多源优先桶", "")
        batch = execution_batch(priority)
        mode = execution_mode(priority)
        package_id = stable_id(
            "P0TRIAGEPACK",
            [
                row.get("来源页码", ""),
                row.get("版面列", ""),
                row.get("院校代码", ""),
                priority,
                row.get("字段名", ""),
                SOURCE_PDF_SHA256,
            ],
        )
        output_rows.append({
            "P0字段三方核验任务ID": stable_id(
                "P0TRIAGE",
                [row.get("P0字段语义多源审计ID", ""), row.get("专业行ID", ""), row.get("字段名", "")],
            ),
            "P0字段三方核验执行包ID": package_id,
            "来源P0字段语义与多源线索审计表": "data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv",
            "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
            "来源P0字段闭环推进工作台": row.get("来源P0字段闭环推进工作台", ""),
            "来源湖北官方系统核验包": row.get("来源湖北官方系统核验包", ""),
            "来源B0B1高校官网辅证旁挂表": row.get("来源B0B1高校官网辅证旁挂表", ""),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0字段×PDF原页锚点×湖北官方待核包×高校辅证线索",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
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
            "执行总序": str(index),
            "执行批次": batch,
            "执行方式": mode,
            "是否需要双人复核": bool_text(mode == "双人复核"),
            "执行优先级数值": str(PRIORITY_ORDER.get(priority, 999)),
            "语义多源优先桶": priority,
            "语义多源执行优先级": row.get("语义多源执行优先级", ""),
            "P0闭环动作桶": row.get("P0闭环动作桶", ""),
            "P0闭环批次": row.get("P0闭环批次", ""),
            "字段核验优先原因": priority_reason(row),
            "首要核验动作": primary_action(row),
            "必须核验步骤": required_steps(row),
            "专业行原页证据锚点ID": anchor.get("专业行原页证据锚点ID", ""),
            "专业起始行号": anchor.get("专业起始行号", ""),
            "专业窗口行号范围": anchor.get("专业窗口行号范围", ""),
            "OCR窗口y上界": anchor.get("OCR窗口y上界", ""),
            "OCR窗口y下界": anchor.get("OCR窗口y下界", ""),
            "窗口坐标摘要": anchor.get("窗口坐标摘要", ""),
            "窗口文本SHA256": row.get("窗口文本SHA256", "") or anchor.get("窗口文本SHA256", ""),
            "起始行文本SHA256": anchor.get("起始行文本SHA256", ""),
            "私有页图证据编号": anchor.get("私有页图证据编号", ""),
            "私有页图SHA256": anchor.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": anchor.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": anchor.get("私有OCR文本SHA256", ""),
            "私有窗口证据编号": row.get("私有窗口证据编号", "") or anchor.get("私有窗口证据编号", ""),
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
            "PDF原页核页状态": "pending_pdf_manual_review",
            "PDF原页人工读数": "",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "湖北官方字段值": "",
            "高校官网或招生章程辅证状态": row.get("高校官网或招生章程辅证状态", ""),
            "高校官网或招生章程字段值": "",
            "三方字段一致性状态": "pending_three_way_closure",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "不得进入原因": (
                "本行仅是P0字段三方核验执行任务；PDF原页、湖北官方系统或省招办计划、"
                "高校官网或章程未三方闭环前，不得写回字段、进入志愿排序或形成报考结论。"
            ),
            "下一步": "按执行总序核 PDF 原页；再核湖北官方计划与高校官网/章程；三方闭环后另建人工确认表。",
        })
    return output_rows


def top_counter(counter, limit=30):
    return dict(counter.most_common(limit))


def write_summary(rows):
    execution_batch_counts = Counter(row["执行批次"] for row in rows)
    execution_mode_counts = Counter(row["执行方式"] for row in rows)
    priority_counts = Counter(row["语义多源优先桶"] for row in rows)
    field_counts = Counter(row["字段名"] for row in rows)
    semantic_counts = Counter(row["机器候选语义状态"] for row in rows)
    relation_counts = Counter(row["机器候选与高校辅证关系"] for row in rows)
    page_counts = Counter(row["来源页码"] for row in rows)
    package_counts = Counter(row["P0字段三方核验执行包ID"] for row in rows)
    school_source_bad_count = sum(
        not school_source_public_ok(row["高校官网字段来源文件"])
        for row in rows
    )

    summary = {
        "status": "issue19_field_fact_p0_triage_execution_workbench_not_final",
        "generated_by": "build_issue19_field_fact_p0_triage_execution_workbench.py",
        "source_semantic_audit": "data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv",
        "source_pdf_anchors": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "source_hubei_official_packets": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
        "source_b0_b1_sidecar": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
        "output_table": "data/working/issue19-field-fact-p0-triage-execution-workbench.csv",
        "row_grain": "逐专业招生明细×P0字段×PDF原页锚点×湖北官方待核包×高校辅证线索",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_triage_task_id_count": len({row["P0字段三方核验任务ID"] for row in rows}),
        "unique_execution_package_id_count": len({row["P0字段三方核验执行包ID"] for row in rows}),
        "unique_semantic_audit_id_count": len({row["P0字段语义多源审计ID"] for row in rows}),
        "unique_p0_action_task_id_count": len({row["P0字段闭环推进任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_school_code_count": len({row["院校代码"] for row in rows}),
        "field_counts": dict(field_counts),
        "execution_batch_counts": dict(execution_batch_counts),
        "execution_mode_counts": dict(execution_mode_counts),
        "semantic_priority_bucket_counts": dict(priority_counts),
        "machine_semantic_status_counts": dict(semantic_counts),
        "crosssource_relation_counts": dict(relation_counts),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in rows),
        "pdf_anchor_link_count": sum(bool(row["专业行原页证据锚点ID"]) for row in rows),
        "hubei_official_packet_link_count": sum(bool(row["湖北官方核验包任务ID"]) for row in rows),
        "school_sidecar_row_count": sum(row["高校官网辅证覆盖状态"] == "has_b0b1_school_sidecar" for row in rows),
        "school_sidecar_field_value_count": sum(bool(row["高校官网字段候选值"]) for row in rows),
        "school_source_bad_count": school_source_bad_count,
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
        "top_execution_packages": top_counter(package_counts),
        "public_safety_note": "本产物只保存字段级执行顺序、页码/版面列、证据编号、哈希、机器候选、官网字段线索和待核状态；不保存私有路径、raw OCR 原文、院校名、专业名、专业代号、专业组代码、登录态或个人身份信息。",
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    write_summary(rows)
    print(f"写出P0字段三方核验执行工作台：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
