#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
SOURCE_RISK_SIDECAR = ROOT / "data/working/issue19-major-source-evidence-risk-sidecar.csv"
FIELD_GAP_CANDIDATES = ROOT / "data/working/issue19-field-gap-repair-candidates.csv"
HUBEI_OFFICIAL_PACKETS = ROOT / "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"
B0_B1_OFFICIAL_EVIDENCE = ROOT / "data/working/issue19-b0-b1-official-evidence-by-major-line.csv"
DECISION_GATES = ROOT / "data/working/issue19-major-decision-readiness-gates.csv"

OUTPUT = ROOT / "data/working/issue19-field-fact-closure-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-fact-closure-ledger-summary.json"

DATA_STAGE = "issue19_field_fact_closure_ledger"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
KEY_FIELDS = ["再选科目", "专业计划数", "学费"]


FIELDS = [
    "字段事实闭环ID",
    "来源单一逐专业招生明细总工作台",
    "来源逐专业源证据风险侧账",
    "来源字段缺口候选修复表",
    "来源湖北官方系统逐专业核验包",
    "来源B0B1官网证据旁挂表",
    "来源逐专业决策闸门表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "学费OCR候选",
    "再选科目人工确认",
    "专业计划数人工确认",
    "学费人工确认",
    "字段缺口数",
    "字段缺口字段",
    "字段候选任务数",
    "非空字段候选数",
    "三字段OCR完整状态",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "字段事实缺口类型",
    "字段事实可机器修复",
    "字段事实可进入候选筛选",
    "PDF字段核验状态",
    "湖北官方平台字段核验状态",
    "湖北官方核验包任务ID",
    "高校官网证据匹配状态",
    "B0B1官网证据任务数",
    "官网证据能否替代湖北官方计划",
    "源证据下沉分层",
    "源证据核页优先级",
    "底座稳定性等级",
    "看板动作桶",
    "风险阻断等级",
    "候选初筛闸门状态",
    "初筛动作桶",
    "再选科目字段事实状态",
    "再选科目候选任务数",
    "再选科目非空候选数",
    "再选科目候选值集合",
    "再选科目候选来源类型集合",
    "再选科目候选置信等级集合",
    "再选科目候选状态集合",
    "再选科目官方核验状态",
    "再选科目PDF核验状态",
    "再选科目下一步",
    "专业计划数字段事实状态",
    "专业计划数候选任务数",
    "专业计划数非空候选数",
    "专业计划数候选值集合",
    "专业计划数候选来源类型集合",
    "专业计划数候选置信等级集合",
    "专业计划数候选状态集合",
    "专业计划数官方核验状态",
    "专业计划数PDF核验状态",
    "专业计划数下一步",
    "学费字段事实状态",
    "学费候选任务数",
    "学费非空候选数",
    "学费候选值集合",
    "学费候选来源类型集合",
    "学费候选置信等级集合",
    "学费候选状态集合",
    "学费官方核验状态",
    "学费PDF核验状态",
    "学费下一步",
    "建议下钻入口",
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


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def ordered_join(values):
    seen = set()
    result = []
    for value in values:
        cleaned = str(value or "").strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return "；".join(result)


def index_by(rows, field):
    result = {}
    for row in rows:
        key = row.get(field, "")
        if key:
            result[key] = row
    return result


def normalize_gap_fields(value):
    text = str(value or "").strip()
    if not text:
        return set()
    return {part.strip() for part in text.split("；") if part.strip()}


def candidate_summary(candidate_rows):
    return {
        "task_count": len(candidate_rows),
        "non_empty_count": sum(1 for row in candidate_rows if row.get("候选值", "").strip()),
        "values": ordered_join(row.get("候选值", "") for row in candidate_rows),
        "source_types": ordered_join(row.get("候选来源类型", "") for row in candidate_rows),
        "confidence": ordered_join(row.get("候选置信等级", "") for row in candidate_rows),
        "status": ordered_join(row.get("候选状态", "") for row in candidate_rows),
    }


def field_ocr_value(master_row, field_name):
    return master_row.get(f"{field_name}OCR候选", "")


def field_manual_value(master_row, field_name):
    return master_row.get(f"{field_name}人工确认", "")


def field_status(master_row, field_name, candidate_rows):
    manual = field_manual_value(master_row, field_name)
    if manual:
        return "K9-人工确认存在但仍需最终门禁复核"
    has_gap = field_name in normalize_gap_fields(master_row.get("字段缺口字段"))
    ocr_value = field_ocr_value(master_row, field_name)
    non_empty_candidates = sum(1 for row in candidate_rows if row.get("候选值", "").strip())
    if has_gap and non_empty_candidates:
        return "K1-字段缺口有候选待PDF原页和官方核验"
    if has_gap:
        return "K0-字段缺口无候选需原页重读"
    if ocr_value:
        return "K2-OCR候选存在但三方核验未闭环"
    return "K0-字段空值需原页重读"


def ledger_level(master_row):
    gap_count = as_int(master_row.get("字段缺口数"))
    non_empty = as_int(master_row.get("非空字段候选数"))
    if gap_count >= 3:
        return "L0-三字段缺口优先阻断"
    if gap_count == 2:
        return "L1-两字段缺口优先补证"
    if gap_count == 1 and non_empty > 0:
        return "L2-单字段缺口有候选待核"
    if gap_count == 1:
        return "L3-单字段缺口无候选需重读"
    return "L4-三字段OCR齐全但待三方闭环"


def blocking_level(master_row):
    gap_count = as_int(master_row.get("字段缺口数"))
    non_empty = as_int(master_row.get("非空字段候选数"))
    if gap_count and non_empty == 0:
        return "Q0-字段缺口无候选阻断"
    if gap_count:
        return "Q1-字段缺口有候选待人工核验"
    return "Q2-OCR字段齐全但PDF和官方未闭环"


def completeness_status(master_row):
    present = [
        bool(master_row.get("再选科目OCR候选", "").strip()),
        bool(master_row.get("专业计划数OCR候选", "").strip()),
        bool(master_row.get("学费OCR候选", "").strip()),
    ]
    if all(present):
        return "三字段OCR候选齐全"
    return f"三字段OCR候选缺{3 - sum(present)}项"


def field_next_step(field_name, status):
    if status.startswith("K1-"):
        return f"用候选值回看PDF原页中的{field_name}列，再用湖北官方系统或省招办计划确认。"
    if status.startswith("K0-"):
        return f"重读PDF原页对应行和同组上下文，补{field_name}候选后再交叉核验。"
    if status.startswith("K2-"):
        return f"OCR已给出{field_name}线索，但仍需PDF原页、湖北官方系统和高校官网/章程闭环。"
    return f"{field_name}已有人工确认线索，仍需最终门禁复核。"


def drilldown_entries(master_row, source_row, has_candidates):
    entries = ["data/working/issue19-field-fact-closure-ledger.csv"]
    if has_candidates:
        entries.append("data/working/issue19-field-gap-repair-candidates.csv")
    if as_int(master_row.get("字段缺口数")):
        entries.append("data/working/issue19-p1-field-gap-evidence-repair-matrix.csv")
    entries.extend([
        "data/working/issue19-major-source-evidence-risk-sidecar.csv",
        "data/working/issue19-admission-detail-master-workbench.csv",
        "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
    ])
    if source_row.get("建议下钻入口"):
        entries.append("data/working/issue19-raw-major-source-evidence-audit.csv")
    return ordered_join(entries)


def build_rows():
    master_rows = read_csv(MASTER_WORKBENCH)
    source_rows = read_csv(SOURCE_RISK_SIDECAR)
    candidate_rows = read_csv(FIELD_GAP_CANDIDATES)
    official_rows = read_csv(HUBEI_OFFICIAL_PACKETS)
    evidence_rows = read_csv(B0_B1_OFFICIAL_EVIDENCE)
    decision_rows = read_csv(DECISION_GATES)

    source_by_major = index_by(source_rows, "专业行ID")
    official_by_major = index_by(official_rows, "专业行ID")
    evidence_by_major = index_by(evidence_rows, "专业行ID")
    decision_by_major = index_by(decision_rows, "专业行ID")
    candidates_by_major_field = defaultdict(list)
    for row in candidate_rows:
        candidates_by_major_field[(row.get("专业行ID", ""), row.get("字段名", ""))].append(row)

    rows = []
    for master in master_rows:
        major_id = master.get("专业行ID", "")
        source = source_by_major.get(major_id, {})
        official = official_by_major.get(major_id, {})
        evidence = evidence_by_major.get(major_id, {})
        decision = decision_by_major.get(major_id, {})
        field_summaries = {}
        field_statuses = {}
        has_candidates = False
        for field_name in KEY_FIELDS:
            field_candidates = candidates_by_major_field.get((major_id, field_name), [])
            summary = candidate_summary(field_candidates)
            status = field_status(master, field_name, field_candidates)
            field_summaries[field_name] = summary
            field_statuses[field_name] = status
            has_candidates = has_candidates or bool(field_candidates)

        row = {
            "字段事实闭环ID": stable_id("FIELDFACT", [major_id, SOURCE_PDF_SHA256]),
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源逐专业源证据风险侧账": "data/working/issue19-major-source-evidence-risk-sidecar.csv",
            "来源字段缺口候选修复表": "data/working/issue19-field-gap-repair-candidates.csv",
            "来源湖北官方系统逐专业核验包": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
            "来源B0B1官网证据旁挂表": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
            "来源逐专业决策闸门表": "data/working/issue19-major-decision-readiness-gates.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "专业行ID": major_id,
            "专业组出现ID": master.get("专业组出现ID", ""),
            "院校代码": master.get("院校代码", ""),
            "院校名称OCR": master.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": master.get("院校专业组代码OCR规范化", ""),
            "来源页码": master.get("来源页码", ""),
            "版面列": master.get("版面列", ""),
            "专业组内专业序号": master.get("专业组内专业序号", ""),
            "专业代号OCR": master.get("专业代号OCR", ""),
            "专业名称及备注短摘": master.get("专业名称及备注短摘", ""),
            "再选科目OCR候选": master.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": master.get("专业计划数OCR候选", ""),
            "学费OCR候选": master.get("学费OCR候选", ""),
            "再选科目人工确认": master.get("再选科目人工确认", ""),
            "专业计划数人工确认": master.get("专业计划数人工确认", ""),
            "学费人工确认": master.get("学费人工确认", ""),
            "字段缺口数": master.get("字段缺口数", ""),
            "字段缺口字段": master.get("字段缺口字段", ""),
            "字段候选任务数": master.get("字段候选任务数", ""),
            "非空字段候选数": master.get("非空字段候选数", ""),
            "三字段OCR完整状态": completeness_status(master),
            "字段事实闭环等级": ledger_level(master),
            "字段事实阻断等级": blocking_level(master),
            "字段事实缺口类型": master.get("字段缺口字段", "") or "无机器字段缺口",
            "字段事实可机器修复": "false",
            "字段事实可进入候选筛选": "false",
            "PDF字段核验状态": master.get("PDF原页证据状态", ""),
            "湖北官方平台字段核验状态": master.get("湖北官方平台字段核验状态", ""),
            "湖北官方核验包任务ID": master.get("湖北官方核验包任务ID", official.get("湖北官方核验包任务ID", "")),
            "高校官网证据匹配状态": master.get("高校官网证据匹配状态", ""),
            "B0B1官网证据任务数": master.get("B0B1官网证据任务数", ""),
            "官网证据能否替代湖北官方计划": master.get("官网证据能否替代湖北官方计划", evidence.get("能否替代湖北官方计划", "")),
            "源证据下沉分层": source.get("源证据下沉分层", ""),
            "源证据核页优先级": source.get("源证据核页优先级", ""),
            "底座稳定性等级": source.get("底座稳定性等级", ""),
            "看板动作桶": master.get("看板动作桶", source.get("看板动作桶", "")),
            "风险阻断等级": master.get("风险阻断等级", source.get("风险阻断等级", "")),
            "候选初筛闸门状态": decision.get("候选初筛闸门状态", ""),
            "初筛动作桶": decision.get("初筛动作桶", ""),
            "建议下钻入口": drilldown_entries(master, source, has_candidates),
            "不得进入原因": "字段事实闭环账只证明字段缺口、候选和核验动作已经结构化；PDF原页、湖北官方系统、省招办计划和高校官网/章程未闭环前，不得用于志愿推荐或学校专业建议。",
            "下一步": "按字段事实阻断等级处理：先重读无候选缺口，再核有候选缺口，最后对OCR齐全行做PDF原页和湖北官方系统抽核闭环。",
        }
        for field_name in KEY_FIELDS:
            summary = field_summaries[field_name]
            status = field_statuses[field_name]
            row.update({
                f"{field_name}字段事实状态": status,
                f"{field_name}候选任务数": str(summary["task_count"]),
                f"{field_name}非空候选数": str(summary["non_empty_count"]),
                f"{field_name}候选值集合": summary["values"],
                f"{field_name}候选来源类型集合": summary["source_types"],
                f"{field_name}候选置信等级集合": summary["confidence"],
                f"{field_name}候选状态集合": summary["status"],
                f"{field_name}官方核验状态": official.get("平台字段核验状态", ""),
                f"{field_name}PDF核验状态": master.get("PDF原页证据状态", ""),
                f"{field_name}下一步": field_next_step(field_name, status),
            })
        rows.append(row)
    return rows


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    summary = {
        "status": "issue19_field_fact_closure_ledger_not_final",
        "generated_by": "build_issue19_field_fact_closure_ledger.py",
        "output_table": "data/working/issue19-field-fact-closure-ledger.csv",
        "row_grain": "逐专业招生明细",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_ledger_id_count": len({row["字段事实闭环ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "source_counts": {
            "master_workbench_row_count": len(read_csv(MASTER_WORKBENCH)),
            "source_risk_sidecar_row_count": len(read_csv(SOURCE_RISK_SIDECAR)),
            "field_gap_candidate_row_count": len(read_csv(FIELD_GAP_CANDIDATES)),
            "hubei_official_packet_row_count": len(read_csv(HUBEI_OFFICIAL_PACKETS)),
            "b0_b1_official_evidence_row_count": len(read_csv(B0_B1_OFFICIAL_EVIDENCE)),
            "decision_gate_row_count": len(read_csv(DECISION_GATES)),
        },
        "field_fact_closure_level_counts": dict(Counter(row["字段事实闭环等级"] for row in rows)),
        "field_fact_blocking_level_counts": dict(Counter(row["字段事实阻断等级"] for row in rows)),
        "three_field_ocr_completeness_counts": dict(Counter(row["三字段OCR完整状态"] for row in rows)),
        "field_gap_count_distribution": dict(Counter(row["字段缺口数"] for row in rows)),
        "field_gap_field_distribution": dict(Counter(row["字段缺口字段"] for row in rows)),
        "reselect_field_status_counts": dict(Counter(row["再选科目字段事实状态"] for row in rows)),
        "plan_count_field_status_counts": dict(Counter(row["专业计划数字段事实状态"] for row in rows)),
        "tuition_field_status_counts": dict(Counter(row["学费字段事实状态"] for row in rows)),
        "reselect_candidate_task_total_count": sum(as_int(row["再选科目候选任务数"]) for row in rows),
        "plan_count_candidate_task_total_count": sum(as_int(row["专业计划数候选任务数"]) for row in rows),
        "tuition_candidate_task_total_count": sum(as_int(row["学费候选任务数"]) for row in rows),
        "field_candidate_task_total_count": sum(
            as_int(row["再选科目候选任务数"])
            + as_int(row["专业计划数候选任务数"])
            + as_int(row["学费候选任务数"])
            for row in rows
        ),
        "field_candidate_non_empty_total_count": sum(
            as_int(row["再选科目非空候选数"])
            + as_int(row["专业计划数非空候选数"])
            + as_int(row["学费非空候选数"])
            for row in rows
        ),
        "manual_confirmed_field_count": sum(
            bool(row["再选科目人工确认"]) + bool(row["专业计划数人工确认"]) + bool(row["学费人工确认"])
            for row in rows
        ),
        "pdf_review_pending_count": sum(
            row["PDF字段核验状态"] != "pdf_original_review_completed" for row in rows
        ),
        "hubei_official_review_pending_count": sum(
            row["湖北官方平台字段核验状态"] != "hubei_official_plan_review_completed" for row in rows
        ),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row["机器是否允许自动写回主表"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "public_safety_note": "本产物只保存字段候选、证据编号、哈希和核验状态；不保存私有OCR窗口原文、图片路径、登录态或个人身份信息。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出字段事实闭环总账：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
