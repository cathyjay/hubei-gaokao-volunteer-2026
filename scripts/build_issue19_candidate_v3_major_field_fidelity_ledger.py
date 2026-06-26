#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DETAIL = ROOT / "data/working/issue19-candidate-v3-admission-detail.csv"
CANDIDATE_QUEUE = ROOT / "data/working/issue19-candidate-v3-admission-detail-review-queue.csv"
FULL_MAJOR_QUALITY = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"
D0_PDF_EVIDENCE = ROOT / "data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv"
B0_B1_PLAN_CONFLICT = ROOT / "data/working/issue19-b0-b1-plan-conflict-review-queue.csv"
B0_B1_UNMATCHED_MAJOR = ROOT / "data/working/issue19-b0-b1-unmatched-major-review-queue.csv"

OUTPUT = ROOT / "data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v3-major-field-fidelity-ledger-summary.json"

DATA_STAGE = "issue19_candidate_v3_major_field_fidelity_ledger"


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


def as_int(value):
    text = str(value or "").strip()
    return int(text) if re.fullmatch(r"\d+", text) else None


def split_flags(value):
    return [part for part in re.split(r"[;；]", value or "") if part]


def clean_text(value):
    return " ".join(str(value or "").split())


def match_key(row):
    return (
        row.get("院校代码", ""),
        row.get("2026院校专业组代码", ""),
        row.get("专业代号OCR", ""),
        clean_text(row.get("专业名称及备注OCR", "")),
        row.get("来源页码", ""),
    )


def add_trigger(triggers, category, rule, severity, note):
    triggers.append({
        "category": category,
        "rule": rule,
        "severity": severity,
        "note": note,
    })


def classify_triggers(detail, queue_row, quality_row, d0_row, plan_conflict_row, unmatched_row):
    triggers = []
    is_zero = detail.get("是否0明细占位") == "true"
    if is_zero:
        add_trigger(triggers, "0明细占位", "zero_detail_group_placeholder", "F0", "没有真实专业明细，不能判断专业和调剂。")

    d0_method = d0_row.get("页面OCR匹配方式", "") if d0_row else ""
    if d0_method == "missing_in_page_and_structured":
        add_trigger(triggers, "专业组存在性", "d0_missing_in_page_and_structured", "F0", "D0 组号在原页 OCR 和结构化组表均未命中。")
    elif d0_method == "normalized_o0_match":
        add_trigger(triggers, "专业组代码混淆", "d0_normalized_o0_match", "F0", "原页标题只通过 0/O 规范化命中，禁止自动写回代码。")
    d0_anomaly_rules = d0_row.get("结构异常规则ID", "") if d0_row else ""
    if d0_anomaly_rules:
        add_trigger(triggers, "D0原页结构风险", "d0_pdf_page_structure_anomaly", "F0", "D0 原页证据表保留结构异常，必须人工核页。")
        for rule in split_flags(d0_anomaly_rules):
            add_trigger(triggers, "D0原页结构风险", f"d0_{rule}", "F0", "D0 原页证据表结构异常规则。")

    high_structure_count = as_int(detail.get("专业行高严重结构异常数")) or 0
    structure_count = as_int(detail.get("专业行结构异常数")) or 0
    anomaly_rules = quality_row.get("专业行异常规则ID列表", "") if quality_row else ""
    anomaly_types = quality_row.get("专业行异常类型列表", "") if quality_row else ""
    if high_structure_count > 0:
        add_trigger(triggers, "结构异常", "high_structure_anomaly", "F0", "专业行存在高严重结构异常。")
    elif structure_count > 0:
        add_trigger(triggers, "结构异常", "structure_anomaly", "F1", "专业行存在结构异常，需核页。")

    critical_rules = {
        "major_text_embeds_other_school_marker": "专业名称疑似串入下一院校",
        "plan_count_number_ge_1000": "专业计划数疑似吞入学费或备注",
        "tuition_number_le_500": "学费数字疑似吞入计划数或截断",
    }
    for rule, note in critical_rules.items():
        if rule in anomaly_rules:
            add_trigger(triggers, "结构异常", rule, "F0", note)

    field_flags = split_flags(detail.get("专业字段完整性标记", ""))
    for flag in field_flags:
        if flag in {"missing_plan_count_candidate", "plan_count_not_plain_number"}:
            add_trigger(triggers, "计划数字段", flag, "F1", "计划数字段缺失或不是纯数字。")
        elif flag in {"missing_tuition_candidate", "tuition_not_plain_number"}:
            add_trigger(triggers, "学费字段", flag, "F1", "学费字段缺失或不是纯数字。")
        elif flag == "missing_subject_candidate":
            add_trigger(triggers, "再选科目字段", flag, "F2", "再选科目字段缺失，需核组内选科继承或原页。")
        elif flag == "low_ocr_confidence":
            add_trigger(triggers, "OCR置信度", flag, "F1", "OCR 置信度偏低。")
        elif flag == "tuition_over_15000":
            add_trigger(triggers, "费用底线", flag, "F1", "学费超过当前家庭预算上限。")
        elif flag != "zero_detail_group":
            add_trigger(triggers, "字段完整性", flag, "F1", "字段完整性标记待核。")

    plan_count = as_int(detail.get("专业计划数OCR候选"))
    if plan_count is not None and plan_count >= 1000:
        add_trigger(triggers, "计划数字段", "plan_count_value_ge_1000", "F0", "计划数异常偏大，疑似错位。")
    if detail.get("专业计划数是否纯数字") != "是" and detail.get("是否真实招生明细") == "true":
        add_trigger(triggers, "计划数字段", "plan_count_not_verified_numeric", "F1", "计划数当前不能作为可信数字。")

    fee = as_int(detail.get("学费OCR数字候选"))
    if fee is not None and fee > 15000:
        add_trigger(triggers, "费用底线", "tuition_over_15000_numeric", "F1", "学费数值超过当前家庭预算上限。")
    if detail.get("学费是否纯数字") != "是" and detail.get("是否真实招生明细") == "true":
        add_trigger(triggers, "学费字段", "tuition_not_verified_numeric", "F1", "学费当前不能作为可信数字。")

    if plan_conflict_row:
        add_trigger(triggers, "计划数保真", "b0_b1_plan_conflict", "F1", "B0/B1 官网证据与 OCR 计划数存在冲突，必须核 PDF 原页和湖北官方系统。")
        if "学费" in plan_conflict_row.get("冲突类型", ""):
            add_trigger(triggers, "计划数保真", "b0_b1_plan_conflict_tuition_shift", "F1", "OCR 计划数疑似误取学费。")

    if unmatched_row:
        add_trigger(triggers, "官网证据覆盖", "b0_b1_unmatched_major", "F1", "B0/B1 官网留存证据未覆盖该 OCR 专业行。")
        if "关键限定词" in unmatched_row.get("未匹配类型", ""):
            add_trigger(triggers, "关键限定词", "b0_b1_key_qualifier_uncovered", "F1", "关键限定词未被官网证据覆盖。")
        if "embedded_other_school" in unmatched_row.get("专业名称匹配方式", ""):
            add_trigger(triggers, "结构异常", "b0_b1_embedded_other_school_marker", "F0", "B0/B1 复核队列提示专业名疑似串入下一院校。")

    risk_type = detail.get("专业风险类型", "")
    if "医学" in risk_type or "护理" in risk_type:
        add_trigger(triggers, "家庭底线", "medical_or_nursing_rejected", "F0", "专业方向触发不学医/护理底线。")
    if "中外合作" in risk_type or "高收费" in risk_type or "学费超过" in risk_type:
        add_trigger(triggers, "家庭底线", "high_fee_or_coop", "F1", "触发高收费或中外合作风险。")
    if any(token in risk_type for token in ["体检", "语种", "单科", "专项"]):
        add_trigger(triggers, "特殊限制", "special_requirement_pending", "F1", "体检、语种、单科或专项限制需核。")

    transfer_risk = queue_row.get("同组调剂机器风险", "") if queue_row else ""
    if transfer_risk.startswith("T1"):
        add_trigger(triggers, "调剂风险", "group_transfer_t1", "F1", "同组存在默认不能接受专业，服从调剂风险高。")
    elif transfer_risk.startswith("T2"):
        add_trigger(triggers, "调剂风险", "group_transfer_t2", "F2", "同组存在特殊限制待核专业。")
    elif transfer_risk.startswith("T0"):
        add_trigger(triggers, "调剂风险", "group_transfer_t0", "F0", "同组专业明细缺失，无法判断调剂。")

    # De-duplicate repeated triggers while keeping first severity/note.
    deduped = []
    seen = set()
    for trigger in triggers:
        key = (trigger["category"], trigger["rule"])
        if key not in seen:
            deduped.append(trigger)
            seen.add(key)
    return deduped, anomaly_rules, anomaly_types


def block_level(triggers):
    if not triggers:
        return "F3-暂未触发机器高风险但仍非最终"
    if any(trigger["severity"] == "F0" for trigger in triggers):
        return "F0-阻断级：不得进入候选排序"
    if any(trigger["severity"] == "F1" for trigger in triggers):
        return "F1-高优先：必须逐字段核验"
    return "F2-待补证：字段需核验"


def fidelity_priority(triggers):
    if not triggers:
        return "P6-暂未触发机器高风险"
    rules = {trigger["rule"] for trigger in triggers}
    categories = {trigger["category"] for trigger in triggers}
    if (
        "zero_detail_group_placeholder" in rules
        or "d0_missing_in_page_and_structured" in rules
        or "high_structure_anomaly" in rules
        or "major_text_embeds_other_school_marker" in rules
        or "b0_b1_embedded_other_school_marker" in rules
        or "d0_pdf_page_structure_anomaly" in rules
    ):
        return "P0-组边界/0明细/串校串行"
    if "计划数字段" in categories or "计划数保真" in categories:
        return "P1-计划数保真"
    if "关键限定词" in categories or "官网证据覆盖" in categories:
        return "P2-关键限定词和官网未覆盖"
    if "费用底线" in categories or "学费字段" in categories or "家庭底线" in categories:
        return "P3-费用与高收费"
    if "特殊限制" in categories or "再选科目字段" in categories:
        return "P4-限制条件"
    return "P5-调剂接受度"


def mandatory_fields(priority_value):
    base = ["PDF原页", "湖北官方系统", "高校官网/章程", "专业组边界", "调剂范围", "家庭接受度"]
    if priority_value.startswith("P1"):
        base.extend(["专业计划数", "学费列"])
    elif priority_value.startswith("P2"):
        base.extend(["专业名称及备注", "关键限定词"])
    elif priority_value.startswith("P3"):
        base.extend(["学费", "中外合作/高收费说明"])
    elif priority_value.startswith("P4"):
        base.extend(["体检/语种/单科/专项限制", "校区/办学地点"])
    return "；".join(dict.fromkeys(base))


def transfer_grade(queue_row):
    risk = queue_row.get("同组调剂机器风险", "")
    if risk.startswith("T0"):
        return "不可判断-专业组明细缺失"
    if risk.startswith("T1"):
        return "高-同组存在默认不能接受专业"
    if risk.startswith("T2"):
        return "中-同组存在特殊限制待核专业"
    if risk.startswith("T3"):
        return "待家庭确认"
    return "待核"


def join_unique(values):
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return "；".join(seen)


def main():
    details = read_csv(CANDIDATE_DETAIL)
    queue_rows = read_csv(CANDIDATE_QUEUE)
    quality_rows = read_csv(FULL_MAJOR_QUALITY)
    d0_rows = read_csv(D0_PDF_EVIDENCE)
    plan_conflict_rows = read_csv(B0_B1_PLAN_CONFLICT)
    unmatched_rows = read_csv(B0_B1_UNMATCHED_MAJOR)

    queue_by_detail_id = {row["招生明细主表行ID"]: row for row in queue_rows}
    quality_by_major_id = {row["专业行ID"]: row for row in quality_rows if row.get("专业行ID")}
    d0_by_group_code = {row["2026院校专业组代码"]: row for row in d0_rows}
    plan_conflict_by_key = {match_key(row): row for row in plan_conflict_rows}
    unmatched_by_key = {match_key(row): row for row in unmatched_rows}

    output_rows = []
    for detail in details:
        queue_row = queue_by_detail_id.get(detail["招生明细主表行ID"], {})
        quality_row = quality_by_major_id.get(detail.get("专业行ID", ""), {})
        d0_row = d0_by_group_code.get(detail.get("2026院校专业组代码", ""), {})
        detail_key = match_key(detail)
        plan_conflict_row = plan_conflict_by_key.get(detail_key, {})
        unmatched_row = unmatched_by_key.get(detail_key, {})
        triggers, anomaly_rules, anomaly_types = classify_triggers(
            detail, queue_row, quality_row, d0_row, plan_conflict_row, unmatched_row
        )
        risk_priority = block_level(triggers)
        fidelity_priority_value = fidelity_priority(triggers)
        output_rows.append({
            "保真总账ID": stable_id("V3FID", [detail["招生明细主表行ID"], fidelity_priority_value]),
            "来源主表": "data/working/issue19-candidate-v3-admission-detail.csv",
            "来源复核队列": "data/working/issue19-candidate-v3-admission-detail-review-queue.csv",
            "招生明细主表行ID": detail["招生明细主表行ID"],
            "主表粒度": detail.get("主表粒度", "逐专业招生明细"),
            "逐专业复核队列ID": queue_row.get("逐专业复核队列ID", ""),
            "复核优先级序号": fidelity_priority_value.split("-", 1)[0].replace("P", ""),
            "保真复核优先级": fidelity_priority_value,
            "来源期号": detail.get("来源期号", ""),
            "来源PDF_SHA256": detail.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "候选V3入口ID": detail.get("候选V3入口ID", ""),
            "复核批次": detail.get("复核批次", ""),
            "入口类型": detail.get("入口类型", ""),
            "最终可用": "false",
            "核验状态": "pending_major_field_fidelity_review",
            "是否高风险保真行": "true" if triggers else "false",
            "风险阻断等级": risk_priority,
            "高风险字段集合": join_unique(trigger["category"] for trigger in triggers),
            "风险触发规则": join_unique(trigger["rule"] for trigger in triggers),
            "异常类型列表": join_unique([anomaly_types, unmatched_row.get("未匹配类型", ""), plan_conflict_row.get("冲突类型", "")]),
            "阻断原因": join_unique(trigger["note"] for trigger in triggers)
            or "暂未触发机器高风险；仍需按最终志愿门禁核 PDF 原页、湖北官方系统、高校官网/章程、家庭接受度和调剂结论。",
            "调剂影响等级": transfer_grade(queue_row),
            "必须核验字段": mandatory_fields(fidelity_priority_value),
            "院校代码": detail.get("院校代码", ""),
            "院校名称OCR": detail.get("院校名称OCR", ""),
            "2026院校专业组代码": detail.get("2026院校专业组代码", ""),
            "专业组出现ID": detail.get("专业组出现ID", ""),
            "来源页码": detail.get("来源页码", ""),
            "私有页图证据编号": detail.get("私有页图证据编号", ""),
            "私有页图SHA256": detail.get("私有页图SHA256", ""),
            "专业行来源": detail.get("专业行来源", ""),
            "专业行ID": detail.get("专业行ID", ""),
            "是否真实招生明细": detail.get("是否真实招生明细", ""),
            "是否0明细占位": detail.get("是否0明细占位", ""),
            "专业组内专业序号": detail.get("专业组内专业序号", ""),
            "专业代号OCR": detail.get("专业代号OCR", ""),
            "专业名称及备注OCR": detail.get("专业名称及备注OCR", ""),
            "再选科目OCR候选": detail.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": detail.get("专业计划数OCR候选", ""),
            "专业计划数是否纯数字": detail.get("专业计划数是否纯数字", ""),
            "学费OCR候选": detail.get("学费OCR候选", ""),
            "学费OCR数字候选": detail.get("学费OCR数字候选", ""),
            "学费是否纯数字": detail.get("学费是否纯数字", ""),
            "专业偏好方向": detail.get("专业偏好方向", ""),
            "专业风险类型": detail.get("专业风险类型", ""),
            "专业字段完整性标记": detail.get("专业字段完整性标记", ""),
            "专业行结构异常数": detail.get("专业行结构异常数", ""),
            "专业行高严重结构异常数": detail.get("专业行高严重结构异常数", ""),
            "结构异常规则ID列表": anomaly_rules,
            "结构异常类型列表": anomaly_types,
            "结构异常严重程度列表": quality_row.get("专业行异常严重程度列表", ""),
            "结构异常证据摘要": quality_row.get("专业行异常证据摘要", ""),
            "同组调剂机器风险": queue_row.get("同组调剂机器风险", ""),
            "同组真实招生明细数": queue_row.get("同组真实招生明细数", ""),
            "同组0明细占位数": queue_row.get("同组0明细占位数", ""),
            "同组默认不能接受专业数": queue_row.get("同组默认不能接受专业数", ""),
            "同组暂缓判断专业数": queue_row.get("同组暂缓判断专业数", ""),
            "官网证据匹配状态": plan_conflict_row.get("保真处理状态", "") or unmatched_row.get("官网来源状态", ""),
            "官网证据覆盖结论": unmatched_row.get("官网证据覆盖结论", ""),
            "B0B1计划冲突来源明细ID": plan_conflict_row.get("招生明细主表行ID", ""),
            "B0B1计划冲突类型": plan_conflict_row.get("冲突类型", ""),
            "B0B1未匹配专业来源明细ID": unmatched_row.get("招生明细主表行ID", ""),
            "B0B1未匹配类型": unmatched_row.get("未匹配类型", ""),
            "最佳官网专业名称": plan_conflict_row.get("官网专业名称", ""),
            "最佳官网计划数": plan_conflict_row.get("官网计划数", ""),
            "最佳官网学费": plan_conflict_row.get("官网学费", ""),
            "计划数核验状态": plan_conflict_row.get("保真处理状态", ""),
            "机器专业接受度初判": detail.get("机器专业接受度初判", ""),
            "机器阻断或待核原因": detail.get("机器阻断或待核原因", ""),
            "调剂影响初判": detail.get("调剂影响初判", ""),
            "PDF字段核验状态": detail.get("PDF字段核验状态", ""),
            "湖北官方系统字段核验状态": detail.get("湖北官方系统字段核验状态", ""),
            "高校官网/章程字段核验状态": detail.get("高校官网/章程字段核验状态", ""),
            "D0原页匹配方式": d0_row.get("页面OCR匹配方式", ""),
            "D0保守等级": d0_row.get("保守等级", ""),
            "是否可进入最终专业列表": "false",
            "可进入下一阶段": "false",
            "下一步": "按风险触发规则回看PDF原页、湖北官方系统和高校官网/章程；再做家庭接受度和调剂影响人工结论。",
        })

    order = {
        "F0-阻断级：不得进入候选排序": 0,
        "F1-高优先：必须逐字段核验": 1,
        "F2-待补证：字段需核验": 2,
    }
    output_rows.sort(key=lambda row: (
        int(row["复核优先级序号"]),
        int(row.get("来源页码") or 9999) if str(row.get("来源页码", "")).isdigit() else 9999,
        row["2026院校专业组代码"],
        row["专业组内专业序号"],
        row["招生明细主表行ID"],
    ))

    fields = [
        "保真总账ID",
        "来源主表",
        "来源复核队列",
        "招生明细主表行ID",
        "主表粒度",
        "逐专业复核队列ID",
        "复核优先级序号",
        "保真复核优先级",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "候选V3入口ID",
        "复核批次",
        "入口类型",
        "最终可用",
        "核验状态",
        "是否高风险保真行",
        "风险阻断等级",
        "高风险字段集合",
        "风险触发规则",
        "异常类型列表",
        "阻断原因",
        "调剂影响等级",
        "必须核验字段",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业组出现ID",
        "来源页码",
        "私有页图证据编号",
        "私有页图SHA256",
        "专业行来源",
        "专业行ID",
        "是否真实招生明细",
        "是否0明细占位",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "专业计划数是否纯数字",
        "学费OCR候选",
        "学费OCR数字候选",
        "学费是否纯数字",
        "专业偏好方向",
        "专业风险类型",
        "专业字段完整性标记",
        "专业行结构异常数",
        "专业行高严重结构异常数",
        "结构异常规则ID列表",
        "结构异常类型列表",
        "结构异常严重程度列表",
        "结构异常证据摘要",
        "同组调剂机器风险",
        "同组真实招生明细数",
        "同组0明细占位数",
        "同组默认不能接受专业数",
        "同组暂缓判断专业数",
        "官网证据匹配状态",
        "官网证据覆盖结论",
        "B0B1计划冲突来源明细ID",
        "B0B1计划冲突类型",
        "B0B1未匹配专业来源明细ID",
        "B0B1未匹配类型",
        "最佳官网专业名称",
        "最佳官网计划数",
        "最佳官网学费",
        "计划数核验状态",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "调剂影响初判",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "D0原页匹配方式",
        "D0保守等级",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "下一步",
    ]
    write_csv(OUTPUT, output_rows, fields)

    priority_counts = Counter(row["保真复核优先级"] for row in output_rows)
    block_level_counts = Counter(row["风险阻断等级"] for row in output_rows)
    category_counts = Counter()
    rule_counts = Counter()
    for row in output_rows:
        category_counts.update(split_flags(row["高风险字段集合"]))
        rule_counts.update(split_flags(row["风险触发规则"]))
    summary = {
        "status": "issue19_candidate_v3_major_field_fidelity_ledger_not_final",
        "generated_by": Path(__file__).name,
        "source_detail_table": "data/working/issue19-candidate-v3-admission-detail.csv",
        "source_review_queue": "data/working/issue19-candidate-v3-admission-detail-review-queue.csv",
        "source_b0_b1_plan_conflict_queue": "data/working/issue19-b0-b1-plan-conflict-review-queue.csv",
        "source_b0_b1_unmatched_major_queue": "data/working/issue19-b0-b1-unmatched-major-review-queue.csv",
        "output_table": "data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv",
        "candidate_detail_row_count": len(details),
        "candidate_real_detail_count": sum(row["是否真实招生明细"] == "true" for row in details),
        "candidate_zero_detail_count": sum(row["是否0明细占位"] == "true" for row in details),
        "ledger_row_count": len(output_rows),
        "high_risk_row_count": sum(row["是否高风险保真行"] == "true" for row in output_rows),
        "low_risk_row_count": sum(row["是否高风险保真行"] == "false" for row in output_rows),
        "priority_counts": dict(sorted(priority_counts.items())),
        "block_level_counts": dict(sorted(block_level_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "top_rule_counts": dict(rule_counts.most_common(30)),
        "unique_group_count": len({row["2026院校专业组代码"] for row in output_rows}),
        "zero_detail_row_count": sum(row["是否0明细占位"] == "true" for row in output_rows),
        "high_structure_anomaly_row_count": sum((as_int(row["专业行高严重结构异常数"]) or 0) > 0 for row in output_rows),
        "plan_count_untrusted_row_count": sum("计划数字段" in row["高风险字段集合"] or "计划数保真" in row["高风险字段集合"] for row in output_rows),
        "tuition_untrusted_row_count": sum("学费字段" in row["高风险字段集合"] for row in output_rows),
        "family_bottom_line_row_count": sum("家庭底线" in row["高风险字段集合"] for row in output_rows),
        "b0_b1_plan_conflict_covered_count": sum("b0_b1_plan_conflict" in row["风险触发规则"] for row in output_rows),
        "b0_b1_unmatched_major_covered_count": sum("b0_b1_unmatched_major" in row["风险触发规则"] for row in output_rows),
        "b0_b1_plan_conflict_source_id_count": sum(bool(row["B0B1计划冲突来源明细ID"]) for row in output_rows),
        "b0_b1_unmatched_major_source_id_count": sum(bool(row["B0B1未匹配专业来源明细ID"]) for row in output_rows),
        "auto_final_list_allowed_count": sum(row["是否可进入最终专业列表"] == "true" for row in output_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "fidelity_note": "本表是候选V3逐专业字段保真总账，一行对应一个招生明细；高风险只是优先级标签，所有行均不产生可报结论。",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
