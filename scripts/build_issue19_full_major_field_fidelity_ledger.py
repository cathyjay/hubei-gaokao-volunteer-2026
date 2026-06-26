#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAJOR_QUALITY = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"
FAMILY_MAJOR = ROOT / "data/working/issue19-family-fit-major-detail.csv"
FAMILY_GROUP = ROOT / "data/working/issue19-family-fit-group-screen.csv"

OUTPUT = ROOT / "data/working/issue19-full-major-field-fidelity-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-full-major-field-fidelity-ledger-summary.json"

DATA_STAGE = "issue19_full_major_field_fidelity_ledger"


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


def join_unique(values):
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return "；".join(seen)


def add_trigger(triggers, category, rule, severity, note):
    triggers.append({
        "category": category,
        "rule": rule,
        "severity": severity,
        "note": note,
    })


def classify_triggers(quality, family_major, family_group):
    triggers = []
    if not quality.get("专业名称及备注OCR"):
        add_trigger(triggers, "0明细或空专业名", "empty_major_name", "F0", "专业名称为空，不能判断专业和调剂。")

    high_structure_count = as_int(quality.get("专业行高严重结构异常数")) or 0
    structure_count = as_int(quality.get("专业行结构异常数")) or 0
    anomaly_rules = quality.get("专业行异常规则ID列表", "")
    if high_structure_count > 0:
        add_trigger(triggers, "结构异常", "high_structure_anomaly", "F0", "专业行存在高严重结构异常。")
    elif structure_count > 0:
        add_trigger(triggers, "结构异常", "structure_anomaly", "F1", "专业行存在结构异常，需核页。")

    critical_rules = {
        "major_text_embeds_other_school_marker": "专业名称疑似串入下一院校。",
        "major_text_embeds_group_code": "专业名称疑似串入下一专业组代码。",
        "plan_count_number_ge_1000": "专业计划数疑似吞入学费或备注。",
        "tuition_number_le_500": "学费数字疑似吞入计划数或截断。",
        "empty_major_name": "专业名称为空。",
    }
    for rule, note in critical_rules.items():
        if rule in anomaly_rules:
            add_trigger(triggers, "结构异常", rule, "F0", note)

    field_flags = split_flags(quality.get("专业字段完整性标记", ""))
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
        elif flag:
            add_trigger(triggers, "字段完整性", flag, "F1", "字段完整性标记待核。")

    plan_count = as_int(quality.get("专业计划数OCR候选"))
    if plan_count is not None and plan_count >= 1000:
        add_trigger(triggers, "计划数字段", "plan_count_value_ge_1000", "F0", "计划数异常偏大，疑似错位。")
    if quality.get("专业计划数是否纯数字") != "是":
        add_trigger(triggers, "计划数字段", "plan_count_not_verified_numeric", "F1", "计划数当前不能作为可信数字。")

    fee = as_int(quality.get("学费OCR数字候选"))
    if fee is not None and fee > 15000:
        add_trigger(triggers, "费用底线", "tuition_over_15000_numeric", "F1", "学费数值超过当前家庭预算上限。")
    if quality.get("学费是否纯数字") != "是":
        add_trigger(triggers, "学费字段", "tuition_not_verified_numeric", "F1", "学费当前不能作为可信数字。")

    risk_type = quality.get("专业风险类型", "")
    if "医学" in risk_type or "护理" in risk_type:
        add_trigger(triggers, "家庭底线", "medical_or_nursing_rejected", "F0", "专业方向触发不学医/护理底线。")
    if "中外合作" in risk_type or "高收费" in risk_type or "学费超过" in risk_type:
        add_trigger(triggers, "家庭底线", "high_fee_or_coop", "F1", "触发高收费或中外合作风险。")
    if any(token in risk_type for token in ["体检", "色觉", "语种", "单科", "专项", "预科", "定向"]):
        add_trigger(triggers, "特殊限制", "special_requirement_pending", "F1", "体检、色觉、语种、单科、专项、预科或定向限制需核。")

    family_decision = family_major.get("机器专业接受度初判", "")
    if family_decision.startswith("默认不能接受-医学"):
        add_trigger(triggers, "家庭底线", "family_machine_reject_medical", "F0", "家庭底线机器初判为医学护理默认不能接受。")
    elif family_decision.startswith("默认不能接受-高收费"):
        add_trigger(triggers, "家庭底线", "family_machine_reject_fee", "F1", "家庭底线机器初判为高收费或超预算默认不能接受。")
    elif family_decision.startswith("暂缓判断"):
        add_trigger(triggers, "特殊限制", "family_machine_pending_special", "F1", "家庭底线机器初判为特殊限制待核。")
    elif family_decision.startswith("优先了解"):
        add_trigger(triggers, "偏好专业", "preference_major_candidate", "F2", "命中当前偏好方向，需做专业研究和接受度判断。")

    if (as_int(family_group.get("医学护理排除专业数")) or 0) > 0:
        add_trigger(triggers, "调剂风险", "group_has_rejected_medical_or_nursing", "F1", "同组存在医学护理等默认不能接受专业。")
    if (as_int(family_group.get("高收费或超预算专业数")) or 0) > 0:
        add_trigger(triggers, "调剂风险", "group_has_high_fee_or_over_budget", "F1", "同组存在高收费或超预算专业。")
    if (as_int(family_group.get("特殊限制待核专业数")) or 0) > 0:
        add_trigger(triggers, "调剂风险", "group_has_special_requirement_pending", "F2", "同组存在特殊限制待核专业。")
    if (as_int(family_group.get("计划数非纯数字或缺失专业数")) or 0) > 0:
        add_trigger(triggers, "组内字段风险", "group_has_plan_count_untrusted", "F1", "同组存在计划数缺失或非纯数字专业。")

    deduped = []
    seen = set()
    for trigger in triggers:
        key = (trigger["category"], trigger["rule"])
        if key not in seen:
            deduped.append(trigger)
            seen.add(key)
    return deduped


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
        "empty_major_name" in rules
        or "high_structure_anomaly" in rules
        or "major_text_embeds_other_school_marker" in rules
        or "major_text_embeds_group_code" in rules
        or "plan_count_number_ge_1000" in rules
        or "plan_count_value_ge_1000" in rules
    ):
        return "P0-结构/空专业名/串校串行"
    if "计划数字段" in categories or "组内字段风险" in categories:
        return "P1-计划数保真"
    if "家庭底线" in categories or "费用底线" in categories or "学费字段" in categories:
        return "P2-家庭底线与费用"
    if "特殊限制" in categories or "再选科目字段" in categories:
        return "P3-选科与特殊限制"
    if "调剂风险" in categories:
        return "P4-调剂风险"
    if "偏好专业" in categories:
        return "P5-偏好专业待研究"
    return "P5-普通待核"


def mandatory_fields(priority_value):
    base = ["PDF原页", "湖北官方系统", "高校官网/章程", "专业组边界", "调剂范围", "家庭接受度"]
    if priority_value.startswith("P0"):
        base.extend(["院校代码", "专业组代码", "专业代号", "专业名称及备注", "计划数", "学费"])
    elif priority_value.startswith("P1"):
        base.extend(["专业计划数", "学费列"])
    elif priority_value.startswith("P2"):
        base.extend(["办学性质", "学费", "中外合作/高收费说明"])
    elif priority_value.startswith("P3"):
        base.extend(["再选科目", "体检/语种/单科/专项限制", "校区/办学地点"])
    elif priority_value.startswith("P4"):
        base.extend(["组内全部专业", "不可接受专业数"])
    elif priority_value.startswith("P5"):
        base.extend(["专业学习内容", "就业/升学", "是否愿意长期学习"])
    return "；".join(dict.fromkeys(base))


def transfer_grade(group_row):
    rejected = (as_int(group_row.get("医学护理排除专业数")) or 0) + (
        as_int(group_row.get("高收费或超预算专业数")) or 0
    )
    special = as_int(group_row.get("特殊限制待核专业数")) or 0
    if rejected > 0:
        return "高-同组存在默认不能接受专业"
    if special > 0:
        return "中-同组存在特殊限制待核专业"
    return "待家庭确认"


def main():
    quality_rows = read_csv(MAJOR_QUALITY)
    family_major_rows = read_csv(FAMILY_MAJOR)
    family_group_rows = read_csv(FAMILY_GROUP)

    family_major_by_id = {row["专业行ID"]: row for row in family_major_rows}
    family_group_by_occurrence_id = {row["专业组出现ID"]: row for row in family_group_rows}

    output_rows = []
    for quality in quality_rows:
        family_major = family_major_by_id.get(quality.get("专业行ID", ""), {})
        family_group = family_group_by_occurrence_id.get(quality.get("专业组出现ID", ""), {})
        triggers = classify_triggers(quality, family_major, family_group)
        priority = fidelity_priority(triggers)
        block = block_level(triggers)
        output_rows.append({
            "全量保真总账ID": stable_id("FULLFID", [quality.get("专业行ID", ""), priority]),
            "来源主表": "data/working/issue19-full-major-detail-quality-workbench.csv",
            "来源家庭底线逐专业表": "data/working/issue19-family-fit-major-detail.csv",
            "来源家庭底线专业组表": "data/working/issue19-family-fit-group-screen.csv",
            "专业行ID": quality.get("专业行ID", ""),
            "专业组出现ID": quality.get("专业组出现ID", ""),
            "主表粒度": "逐专业招生明细",
            "复核优先级序号": priority.split("-", 1)[0].replace("P", ""),
            "全量保真复核优先级": priority,
            "来源期号": quality.get("来源期号", ""),
            "来源PDF_SHA256": quality.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "最终可用": "false",
            "核验状态": "pending_full_major_field_fidelity_review",
            "是否高风险保真行": "true" if triggers else "false",
            "风险阻断等级": block,
            "高风险字段集合": join_unique(trigger["category"] for trigger in triggers),
            "风险触发规则": join_unique(trigger["rule"] for trigger in triggers),
            "异常类型列表": quality.get("专业行异常类型列表", ""),
            "阻断原因": join_unique(trigger["note"] for trigger in triggers)
            or "暂未触发机器高风险；仍需按最终志愿门禁核 PDF 原页、湖北官方系统、高校官网/章程、家庭接受度和调剂结论。",
            "调剂影响等级": transfer_grade(family_group),
            "必须核验字段": mandatory_fields(priority),
            "院校代码": quality.get("院校代码", ""),
            "院校名称OCR": quality.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": quality.get("院校专业组代码OCR规范化", ""),
            "专业组号OCR": quality.get("专业组号OCR", ""),
            "专业组标题OCR原文": quality.get("专业组标题OCR原文", ""),
            "来源页码": quality.get("来源页码", ""),
            "版面列": quality.get("版面列", ""),
            "专业组内专业序号": quality.get("专业组内专业序号", ""),
            "专业代号OCR": quality.get("专业代号OCR", ""),
            "专业名称及备注OCR": quality.get("专业名称及备注OCR", ""),
            "再选科目OCR候选": quality.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": quality.get("专业计划数OCR候选", ""),
            "专业计划数是否纯数字": quality.get("专业计划数是否纯数字", ""),
            "学费OCR候选": quality.get("学费OCR候选", ""),
            "学费OCR数字候选": quality.get("学费OCR数字候选", ""),
            "学费是否纯数字": quality.get("学费是否纯数字", ""),
            "OCR置信度": quality.get("OCR置信度", ""),
            "专业偏好方向": quality.get("专业偏好方向", ""),
            "专业风险类型": quality.get("专业风险类型", ""),
            "专业风险等级": quality.get("专业风险等级", ""),
            "专业字段完整性标记": quality.get("专业字段完整性标记", ""),
            "专业行结构异常数": quality.get("专业行结构异常数", ""),
            "专业行高严重结构异常数": quality.get("专业行高严重结构异常数", ""),
            "结构异常规则ID列表": quality.get("专业行异常规则ID列表", ""),
            "结构异常严重程度列表": quality.get("专业行异常严重程度列表", ""),
            "结构异常证据摘要": quality.get("专业行异常证据摘要", ""),
            "专业关注类型": quality.get("专业关注类型", ""),
            "逐专业复核优先级": quality.get("逐专业复核优先级", ""),
            "组相对质量层级": quality.get("组相对质量层级", ""),
            "组复核优先级": quality.get("组复核优先级", ""),
            "规范化专业组代码是否重复": quality.get("规范化专业组代码是否重复", ""),
            "规范化专业组代码重复行数": quality.get("规范化专业组代码重复行数", ""),
            "候选池V1命中": quality.get("专业行候选池V1命中", ""),
            "样本学校命中": quality.get("专业行样本学校命中", ""),
            "预算上限元": family_major.get("预算上限元", ""),
            "机器专业接受度初判": family_major.get("机器专业接受度初判", ""),
            "机器阻断或待核原因": family_major.get("机器阻断或待核原因", ""),
            "调剂影响初判": family_major.get("调剂影响初判", ""),
            "家庭接受度核验状态": family_major.get("家庭接受度核验状态", ""),
            "同组真实招生明细数": family_group.get("专业明细行数", ""),
            "同组偏好专业数": family_group.get("偏好专业数", ""),
            "同组数字媒体技术专业数": family_group.get("数字媒体技术专业数", ""),
            "同组计算机类相关专业数": family_group.get("计算机类相关专业数", ""),
            "同组师范类相关专业数": family_group.get("师范类相关专业数", ""),
            "同组医学护理排除专业数": family_group.get("医学护理排除专业数", ""),
            "同组高收费或超预算专业数": family_group.get("高收费或超预算专业数", ""),
            "同组特殊限制待核专业数": family_group.get("特殊限制待核专业数", ""),
            "组机器家庭匹配初判": family_group.get("机器家庭匹配初判", ""),
            "组调剂初判": family_group.get("调剂初判", ""),
            "PDF字段核验状态": "pending_original_pdf_page_review",
            "湖北官方系统字段核验状态": "pending_hubei_official_plan_review",
            "高校官网/章程字段核验状态": "pending_school_plan_or_charter_review",
            "是否可进入最终专业列表": "false",
            "可进入下一阶段": "false",
            "下一步": "按逐专业风险触发规则回看PDF原页、湖北官方系统和高校官网/章程；再做家庭接受度和调剂影响人工结论。",
        })

    output_rows.sort(key=lambda row: (
        int(row["复核优先级序号"]),
        int(row.get("来源页码") or 9999) if str(row.get("来源页码", "")).isdigit() else 9999,
        row["院校代码"],
        row["院校专业组代码OCR规范化"],
        int(row.get("专业组内专业序号") or 9999)
        if str(row.get("专业组内专业序号", "")).isdigit()
        else 9999,
        row["专业行ID"],
    ))

    fields = [
        "全量保真总账ID",
        "来源主表",
        "来源家庭底线逐专业表",
        "来源家庭底线专业组表",
        "专业行ID",
        "专业组出现ID",
        "主表粒度",
        "复核优先级序号",
        "全量保真复核优先级",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
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
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组标题OCR原文",
        "来源页码",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "专业计划数是否纯数字",
        "学费OCR候选",
        "学费OCR数字候选",
        "学费是否纯数字",
        "OCR置信度",
        "专业偏好方向",
        "专业风险类型",
        "专业风险等级",
        "专业字段完整性标记",
        "专业行结构异常数",
        "专业行高严重结构异常数",
        "结构异常规则ID列表",
        "结构异常严重程度列表",
        "结构异常证据摘要",
        "专业关注类型",
        "逐专业复核优先级",
        "组相对质量层级",
        "组复核优先级",
        "规范化专业组代码是否重复",
        "规范化专业组代码重复行数",
        "候选池V1命中",
        "样本学校命中",
        "预算上限元",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "调剂影响初判",
        "家庭接受度核验状态",
        "同组真实招生明细数",
        "同组偏好专业数",
        "同组数字媒体技术专业数",
        "同组计算机类相关专业数",
        "同组师范类相关专业数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "组机器家庭匹配初判",
        "组调剂初判",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "下一步",
    ]
    write_csv(OUTPUT, output_rows, fields)

    priority_counts = Counter(row["全量保真复核优先级"] for row in output_rows)
    block_counts = Counter(row["风险阻断等级"] for row in output_rows)
    category_counts = Counter()
    rule_counts = Counter()
    for row in output_rows:
        category_counts.update(split_flags(row["高风险字段集合"]))
        rule_counts.update(split_flags(row["风险触发规则"]))

    summary = {
        "status": "issue19_full_major_field_fidelity_ledger_not_final",
        "generated_by": Path(__file__).name,
        "source_major_quality_table": "data/working/issue19-full-major-detail-quality-workbench.csv",
        "source_family_major_table": "data/working/issue19-family-fit-major-detail.csv",
        "source_family_group_table": "data/working/issue19-family-fit-group-screen.csv",
        "output_table": "data/working/issue19-full-major-field-fidelity-ledger.csv",
        "major_quality_row_count": len(quality_rows),
        "family_major_row_count": len(family_major_rows),
        "family_group_row_count": len(family_group_rows),
        "ledger_row_count": len(output_rows),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in output_rows}),
        "high_risk_row_count": sum(row["是否高风险保真行"] == "true" for row in output_rows),
        "low_risk_row_count": sum(row["是否高风险保真行"] == "false" for row in output_rows),
        "priority_counts": dict(sorted(priority_counts.items())),
        "block_level_counts": dict(sorted(block_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "top_rule_counts": dict(rule_counts.most_common(30)),
        "empty_major_name_row_count": rule_counts.get("empty_major_name", 0),
        "high_structure_anomaly_row_count": sum((as_int(row["专业行高严重结构异常数"]) or 0) > 0 for row in output_rows),
        "plan_count_untrusted_row_count": sum("计划数字段" in row["高风险字段集合"] for row in output_rows),
        "tuition_untrusted_row_count": sum("学费字段" in row["高风险字段集合"] for row in output_rows),
        "family_bottom_line_row_count": sum("家庭底线" in row["高风险字段集合"] for row in output_rows),
        "preference_major_candidate_row_count": rule_counts.get("preference_major_candidate", 0),
        "auto_final_list_allowed_count": sum(row["是否可进入最终专业列表"] == "true" for row in output_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "fidelity_note": "本表是第19期全量逐专业字段保真总账，一行对应一个招生专业；所有行均不产生可报结论。",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
