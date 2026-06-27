#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

P0_ACTION_WORKBENCH = ROOT / "data/working/issue19-field-fact-p0-closure-action-workbench.csv"
B0_B1_SIDECAR = ROOT / "data/working/issue19-b0-b1-official-evidence-by-major-line.csv"
HUBEI_OFFICIAL_PACKETS = ROOT / "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"
OUTPUT = ROOT / "data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-fact-p0-semantic-crosssource-audit-summary.json"

DATA_STAGE = "issue19_field_fact_p0_semantic_crosssource_audit"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"


FIELDS = [
    "P0字段语义多源审计ID",
    "来源P0字段闭环推进工作台",
    "来源B0B1高校官网辅证旁挂表",
    "来源湖北官方系统核验包",
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
    "P0闭环动作桶",
    "P0闭环批次",
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
    "窗口文本SHA256",
    "私有窗口证据编号",
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
    "语义多源优先桶",
    "语义多源执行优先级",
    "PDF原页核页状态",
    "PDF原页人工读数",
    "湖北官方系统或省招办计划核验状态",
    "湖北官方字段值",
    "高校官网或招生章程辅证状态",
    "高校官网或招生章程字段值",
    "三方字段一致性状态",
    "语义多源审计说明",
    "不得进入原因",
    "下一步",
]


FIELD_ORDER = {
    "专业计划数": 1,
    "再选科目": 2,
    "学费": 3,
}

FIELD_TO_SIDECAR_VALUE = {
    "专业计划数": "最佳官网计划数",
    "再选科目": "最佳官网选科",
    "学费": "最佳官网学费",
}

ALLOWED_SUBJECTS = {"不限", "化学", "生物", "政治", "地理"}


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


def normalize_subject(value):
    text = str(value or "").strip()
    replacements = {
        "【": "",
        "】": "",
        "［": "",
        "］": "",
        "[": "",
        "]": "",
        "「": "",
        "」": "",
        " ": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    if text in {"无", "不提科目要求", "不提科目", "不限科目"}:
        return "不限"
    if "不限" in text:
        return "不限"
    reselect_hits = [subject for subject in ["化学", "生物", "政治", "地理"] if subject in text]
    if len(reselect_hits) == 1:
        return reselect_hits[0]
    if not reselect_hits and text in {"物理", "仅物理"}:
        return "不限"
    return text


def normalize_number(value):
    text = str(value or "").strip().replace(",", "")
    if not re.fullmatch(r"\d+", text):
        return ""
    return str(int(text))


def semantic_check(field_name, value, machine_status):
    raw_value = str(value or "").strip()
    if not raw_value:
        return ("M0-无机器候选", "", "no_machine_candidate")
    if machine_status == "P0C2-多值坐标候选冲突待人工核页":
        return ("M3-多值冲突不生成快速候选", "", "machine_multi_value_conflict")

    if field_name == "再选科目":
        normalized = normalize_subject(raw_value)
        if normalized in ALLOWED_SUBJECTS:
            return ("M1-语义枚举通过", normalized, "semantic_ok")
        return ("M4-再选科目不在受控枚举", normalized, "subject_out_of_enum")

    if field_name == "专业计划数":
        normalized = normalize_number(raw_value)
        if not normalized:
            return ("M4-计划数非纯数字", "", "plan_not_integer")
        number = int(normalized)
        if number <= 0:
            return ("M4-计划数非正数", normalized, "plan_not_positive")
        if number > 200:
            return ("M4-计划数异常偏大", normalized, "plan_unusually_large_gt200")
        if number > 100:
            return ("M2-计划数偏大需重点核页", normalized, "plan_large_gt100")
        return ("M1-语义范围通过", normalized, "semantic_ok")

    if field_name == "学费":
        normalized = normalize_number(raw_value)
        if not normalized:
            return ("M4-学费非纯数字", "", "fee_not_integer")
        number = int(normalized)
        if number < 1000:
            return ("M4-学费异常偏低", normalized, "fee_unusually_low_lt1000")
        if number > 100000:
            return ("M4-学费异常偏高", normalized, "fee_unusually_high_gt100000")
        return ("M1-语义范围通过", normalized, "semantic_ok")

    return ("M9-未知字段", "", "unknown_field")


def normalize_field_value(field_name, value):
    if field_name == "再选科目":
        normalized = normalize_subject(value)
        return normalized if normalized in ALLOWED_SUBJECTS else ""
    return normalize_number(value)


def sidecar_relation(field_name, machine_norm, sidecar):
    if not sidecar:
        return ("R0-无高校官网辅证行", "", "")
    field_value = str(sidecar.get(FIELD_TO_SIDECAR_VALUE[field_name], "") or "").strip()
    if not field_value:
        return ("R1-有高校官网辅证行但本字段无值", "", "")
    field_norm = normalize_field_value(field_name, field_value)
    if not field_norm:
        return ("R2-高校辅证字段值不可规范化", field_value, "")
    if machine_norm and machine_norm == field_norm:
        return ("R4-机器候选与高校辅证字段一致", field_value, field_norm)
    if machine_norm and machine_norm != field_norm:
        return ("R5-机器候选与高校辅证字段冲突", field_value, field_norm)
    return ("R3-高校辅证有字段值但机器无规范候选", field_value, field_norm)


def priority_bucket(row, semantic_status, relation):
    if relation == "R5-机器候选与高校辅证字段冲突":
        return ("S1-多源字段冲突优先核页", "10")
    if semantic_status.startswith("M4-"):
        return ("S2-机器候选语义异常优先排除", "20")
    if relation == "R4-机器候选与高校辅证字段一致":
        return ("S3-机器与高校辅证一致优先核PDF和湖北官方", "30")
    if relation == "R3-高校辅证有字段值但机器无规范候选":
        return ("S4-高校辅证补缺线索优先核PDF", "40")
    if semantic_status.startswith("M2-"):
        return ("S5-机器候选偏大重点核页", "50")
    if row.get("P0闭环动作桶", "").startswith("A2-"):
        return ("S6-多值坐标冲突核页", "60")
    if row.get("P0闭环动作桶", "").startswith("A3-"):
        return ("S7-无坐标候选重读", "70")
    if semantic_status.startswith("M1-"):
        return ("S8-机器候选语义通过常规核页", "80")
    return ("S9-无机器候选保持原页重读", "90")


def next_step(priority, semantic_status, relation):
    if priority.startswith("S1-"):
        return "优先回看 PDF 原页字段列，并对照高校官网原始来源；冲突未消除前不得写回。"
    if priority.startswith("S2-"):
        return "优先核 PDF 原页，判断机器候选是否为串列、串行或 OCR 噪声；异常未排除前不得进入普通候选。"
    if priority.startswith("S3-"):
        return "先核 PDF 原页，再等湖北官方系统或省招办计划；三方一致前仍不得写回。"
    if priority.startswith("S4-"):
        return "用高校官网字段值作为补缺线索回看 PDF 原页；仍需湖北官方系统或省招办计划确认。"
    if priority.startswith("S5-"):
        return "重点核计划数是否串入院校代码、专业代号、学费或合计数字。"
    if priority.startswith("S6-"):
        return "逐个候选坐标回看 PDF 原页，确认字段列和专业行边界。"
    if priority.startswith("S7-"):
        return "人工重读 PDF 原页对应专业行、同组上下文和字段列；必要时更高分辨率 OCR。"
    if priority.startswith("S8-"):
        return "按候选坐标常规核 PDF 原页；核对后仍进入人工和官方闭环，不自动写回。"
    return "保持原页重读；补充 PDF 原页、高校官网或湖北官方字段线索。"


def bool_text(value):
    return "true" if value else "false"


def build_rows():
    p0_rows = read_csv(P0_ACTION_WORKBENCH)
    sidecar_by_major_id = {row.get("专业行ID", ""): row for row in read_csv(B0_B1_SIDECAR)}
    hubei_by_major_id = {row.get("专业行ID", ""): row for row in read_csv(HUBEI_OFFICIAL_PACKETS)}

    rows = []
    for source in p0_rows:
        field_name = source.get("字段名", "")
        sidecar = sidecar_by_major_id.get(source.get("专业行ID", ""), {})
        hubei = hubei_by_major_id.get(source.get("专业行ID", ""), {})
        semantic_status, machine_norm, semantic_tag = semantic_check(
            field_name,
            source.get("机器候选字段值", ""),
            source.get("机器候选状态", ""),
        )
        relation, sidecar_field_value, sidecar_field_norm = sidecar_relation(field_name, machine_norm, sidecar)
        priority, priority_order = priority_bucket(source, semantic_status, relation)
        has_sidecar = bool(sidecar)
        semantic_candidate_ok = semantic_status.startswith("M1-") or semantic_status.startswith("M2-")

        rows.append({
            "P0字段语义多源审计ID": stable_id(
                "P0SEMANTIC",
                [
                    source.get("P0字段闭环推进任务ID", ""),
                    source.get("专业行ID", ""),
                    field_name,
                    SOURCE_PDF_SHA256,
                ],
            ),
            "来源P0字段闭环推进工作台": "data/working/issue19-field-fact-p0-closure-action-workbench.csv",
            "来源B0B1高校官网辅证旁挂表": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
            "来源湖北官方系统核验包": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×K0字段×机器候选语义×高校辅证线索×湖北官方待核",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "P0字段闭环推进任务ID": source.get("P0字段闭环推进任务ID", ""),
            "P0字段机器候选任务ID": source.get("P0字段机器候选任务ID", ""),
            "来源P0字段原页重读任务ID": source.get("来源P0字段原页重读任务ID", ""),
            "来源字段事实核验任务ID": source.get("来源字段事实核验任务ID", ""),
            "字段事实闭环ID": source.get("字段事实闭环ID", ""),
            "专业行ID": source.get("专业行ID", ""),
            "专业组出现ID": source.get("专业组出现ID", ""),
            "院校代码": source.get("院校代码", ""),
            "来源页码": source.get("来源页码", ""),
            "版面列": source.get("版面列", ""),
            "字段名": field_name,
            "P0闭环动作桶": source.get("P0闭环动作桶", ""),
            "P0闭环批次": source.get("P0闭环批次", ""),
            "机器候选状态": source.get("机器候选状态", ""),
            "机器候选置信等级": source.get("机器候选置信等级", ""),
            "机器候选规则ID": source.get("机器候选规则ID", ""),
            "机器候选字段值": source.get("机器候选字段值", ""),
            "机器候选规范值": machine_norm,
            "机器候选语义状态": semantic_status,
            "机器候选语义风险标签": semantic_tag,
            "机器候选语义后可作为核页线索": bool_text(semantic_candidate_ok),
            "候选证据行号集合": source.get("候选证据行号集合", ""),
            "候选证据x集合": source.get("候选证据x集合", ""),
            "候选证据y集合": source.get("候选证据y集合", ""),
            "窗口文本SHA256": source.get("窗口文本SHA256", ""),
            "私有窗口证据编号": source.get("私有窗口证据编号", ""),
            "高校官网辅证覆盖状态": "has_b0b1_school_sidecar" if has_sidecar else "no_b0b1_school_sidecar",
            "高校官网证据旁挂ID": sidecar.get("官网证据旁挂ID", ""),
            "高校官网证据强度": sidecar.get("官网证据强度", ""),
            "高校官网证据匹配状态": sidecar.get("官网证据匹配状态", ""),
            "高校官网字段候选值": sidecar_field_value,
            "高校官网字段规范值": sidecar_field_norm,
            "高校官网字段来源文件": sidecar.get("最佳官网来源文件", "") if sidecar_field_value else "",
            "机器候选与高校辅证关系": relation,
            "湖北官方核验包任务ID": hubei.get("湖北官方核验包任务ID", ""),
            "湖北官方平台匹配状态": hubei.get("平台匹配状态", ""),
            "湖北官方字段核验状态": hubei.get("平台字段核验状态", ""),
            "湖北官方证据编号": hubei.get("官方系统证据编号", ""),
            "湖北官方证据SHA256": hubei.get("官方系统证据SHA256", ""),
            "语义多源优先桶": priority,
            "语义多源执行优先级": priority_order,
            "PDF原页核页状态": "pending_pdf_manual_review",
            "PDF原页人工读数": "",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "湖北官方字段值": "",
            "高校官网或招生章程辅证状态": (
                "school_sidecar_field_value_available_pending_pdf_and_hubei_review"
                if sidecar_field_value
                else "pending_school_official_or_charter_review"
            ),
            "高校官网或招生章程字段值": "",
            "三方字段一致性状态": "pending_three_way_closure",
            "语义多源审计说明": (
                "本表只做机器候选语义审计和高校官网/章程辅证线索并列；"
                "高校辅证不能替代湖北官方计划，机器候选也不能自动写回字段。"
            ),
            "不得进入原因": (
                "PDF原页人工读数、湖北官方字段值、高校官网或章程字段值未三方闭环；"
                "不得写回主表、生成学校专业建议、进入志愿排序或形成报考结论。"
            ),
            "下一步": next_step(priority, semantic_status, relation),
        })

    rows.sort(key=lambda row: (
        as_int(row.get("语义多源执行优先级")),
        as_int(row.get("来源页码")),
        row.get("版面列", ""),
        row.get("院校代码", ""),
        row.get("专业组出现ID", ""),
        row.get("专业行ID", ""),
        FIELD_ORDER.get(row.get("字段名", ""), 9),
        row.get("P0字段语义多源审计ID", ""),
    ))
    return rows


def nested_counts(rows, outer_field, inner_field):
    counts = defaultdict(Counter)
    for row in rows:
        counts[row.get(outer_field, "")][row.get(inner_field, "")] += 1
    return {key: dict(counter) for key, counter in counts.items()}


def top_counts(counter, limit=30):
    return dict(counter.most_common(limit))


def write_summary(rows):
    semantic_counts = Counter(row["机器候选语义状态"] for row in rows)
    relation_counts = Counter(row["机器候选与高校辅证关系"] for row in rows)
    priority_counts = Counter(row["语义多源优先桶"] for row in rows)
    field_counts = Counter(row["字段名"] for row in rows)
    source_page_counts = Counter(row["来源页码"] for row in rows)
    summary = {
        "status": "issue19_field_fact_p0_semantic_crosssource_audit_not_final",
        "generated_by": "build_issue19_field_fact_p0_semantic_crosssource_audit.py",
        "source_p0_action_workbench": "data/working/issue19-field-fact-p0-closure-action-workbench.csv",
        "source_b0_b1_sidecar": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
        "source_hubei_official_packets": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
        "output_table": "data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv",
        "row_grain": "逐专业招生明细×K0字段×机器候选语义×高校辅证线索×湖北官方待核",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_semantic_audit_id_count": len({row["P0字段语义多源审计ID"] for row in rows}),
        "unique_p0_action_task_id_count": len({row["P0字段闭环推进任务ID"] for row in rows}),
        "unique_machine_candidate_task_id_count": len({row["P0字段机器候选任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_school_code_count": len({row["院校代码"] for row in rows}),
        "field_counts": dict(field_counts),
        "machine_semantic_status_counts": dict(semantic_counts),
        "field_machine_semantic_status_counts": nested_counts(rows, "字段名", "机器候选语义状态"),
        "crosssource_relation_counts": dict(relation_counts),
        "semantic_priority_bucket_counts": dict(priority_counts),
        "semantic_candidate_line_count": sum(row["机器候选语义后可作为核页线索"] == "true" for row in rows),
        "semantic_warning_count": semantic_counts.get("M2-计划数偏大需重点核页", 0),
        "semantic_anomaly_count": sum(count for key, count in semantic_counts.items() if key.startswith("M4-")),
        "school_sidecar_row_count": sum(row["高校官网辅证覆盖状态"] == "has_b0b1_school_sidecar" for row in rows),
        "school_sidecar_field_value_count": sum(bool(row["高校官网字段候选值"]) for row in rows),
        "machine_school_same_field_match_count": relation_counts.get("R4-机器候选与高校辅证字段一致", 0),
        "machine_school_same_field_conflict_count": relation_counts.get("R5-机器候选与高校辅证字段冲突", 0),
        "school_field_value_machine_empty_count": relation_counts.get("R3-高校辅证有字段值但机器无规范候选", 0),
        "hubei_official_packet_link_count": sum(bool(row["湖北官方核验包任务ID"]) for row in rows),
        "hubei_official_status_counts": dict(Counter(row["湖北官方字段核验状态"] for row in rows)),
        "pdf_manual_review_pending_count": sum(row["PDF原页核页状态"] == "pending_pdf_manual_review" for row in rows),
        "hubei_official_review_pending_count": sum(row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_plan_review" for row in rows),
        "three_way_closure_pending_count": sum(row["三方字段一致性状态"] == "pending_three_way_closure" for row in rows),
        "pdf_confirmed_count": sum(bool(row["PDF原页人工读数"]) for row in rows),
        "official_confirmed_count": sum(bool(row["湖北官方字段值"]) for row in rows),
        "school_official_confirmed_count": sum(bool(row["高校官网或招生章程字段值"]) for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row["机器是否允许自动写回主表"] == "true" for row in rows),
        "auto_candidate_fill_allowed_count": sum(row["机器是否允许自动回填候选"] == "true" for row in rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "page_task_count_top30": top_counts(source_page_counts),
        "public_safety_note": "本产物只保存字段级机器候选、规范化值、语义风险、高校字段辅证线索、湖北官方待核状态、证据编号和哈希；不保存私有OCR原文、院校名、专业名、专业代号、专业组代码、图片路径、登录态或个人身份信息。",
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    write_summary(rows)
    print(f"写出P0字段语义与多源线索审计表：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
