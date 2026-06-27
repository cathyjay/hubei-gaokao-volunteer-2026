#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FAMILY_PREFERENCES = ROOT / "data/working/family-preferences.json"
MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
FAMILY_FIT_MAJOR = ROOT / "data/working/issue19-family-fit-major-detail.csv"
STRUCTURAL_REGISTER = ROOT / "data/working/issue19-admission-detail-structural-fidelity-register.csv"

OUTPUT = ROOT / "data/working/issue19-candidate-filter-prep-major-detail.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-filter-prep-summary.json"

DATA_STAGE = "issue19_candidate_filter_prep_major_detail"

CITY_TO_PROVINCE = {
    "成都": "四川",
    "西安": "陕西",
    "武汉": "湖北",
    "北京": "北京",
}


FIELDS = [
    "候选筛选准备ID",
    "来源单一逐专业招生明细总工作台",
    "来源家庭底线逐专业筛选表",
    "来源结构保真登记表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "候选筛选可用状态",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校名称人工确认",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR",
    "专业名称及备注短摘",
    "省份候选",
    "城市候选",
    "城市偏好命中",
    "城市偏好顺序",
    "城市候选来源",
    "城市字段状态",
    "办学属性候选",
    "公办民办初判",
    "中外合作/高收费初判",
    "办学属性核验状态",
    "专业偏好方向",
    "专业方向机器标签来源",
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "专业计划数是否纯数字",
    "学费OCR候选",
    "学费OCR数字候选",
    "学费是否纯数字",
    "预算上限元",
    "是否超预算机器初判",
    "校区/办学地点候选",
    "校区字段状态",
    "体检/色觉/语种/单科/专项限制初判",
    "专业风险类型",
    "风险阻断等级",
    "结构保真优先级",
    "结构保真风险标签",
    "机器专业接受度初判",
    "机器阻断或待核原因",
    "家庭接受度核验状态",
    "家庭接受度结论",
    "同组真实招生明细数",
    "同组偏好专业数",
    "同组医学护理排除专业数",
    "同组高收费或超预算专业数",
    "同组特殊限制待核专业数",
    "调剂影响初判",
    "调剂影响等级",
    "同组调剂结论",
    "PDF字段核验状态",
    "湖北官方系统字段核验状态",
    "高校官网/章程字段核验状态",
    "官方系统证据编号",
    "高校官网证据状态",
    "高校官网证据匹配状态",
    "三年投档稳定性状态",
    "稳定性分层",
    "候选筛选机器动作",
    "不得进入原因",
    "下一步核验动作",
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


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return None


def by_major_id(rows):
    return {row.get("专业行ID", ""): row for row in rows}


def city_candidate(school_name, preferred_cities):
    hits = [city for city in preferred_cities if city and city in str(school_name or "")]
    if not hits:
        return "", "", "", "", "pending_school_location_review"
    city = hits[0]
    order = str(preferred_cities.index(city) + 1)
    province = CITY_TO_PROVINCE.get(city, "")
    return province, city, "true", order, "machine_school_name_keyword_unverified"


def tuition_over_budget(row, tuition_limit):
    tuition = as_int(row.get("学费OCR数字候选"))
    if row.get("学费是否纯数字") != "是" or tuition is None:
        return "pending_tuition_field_review"
    return "true" if tuition > tuition_limit else "false"


def high_fee_or_coop(row):
    text = "；".join([
        row.get("专业风险类型", ""),
        row.get("专业名称及备注OCR", ""),
        row.get("机器阻断或待核原因", ""),
    ])
    if any(token in text for token in ["中外合作", "高收费", "超预算"]):
        return "machine_risk_keyword_or_budget_signal"
    return "no_machine_signal_but_pending_attribute_review"


def special_limit(row):
    text = "；".join([row.get("专业风险类型", ""), row.get("专业名称及备注OCR", "")])
    labels = []
    for token, label in [
        ("体检", "体检限制线索"),
        ("色觉", "色觉限制线索"),
        ("色盲", "色觉限制线索"),
        ("语种", "语种要求线索"),
        ("英语", "语种或单科线索"),
        ("单科", "单科要求线索"),
        ("专项", "专项/预科/定向线索"),
        ("预科", "专项/预科/定向线索"),
        ("定向", "专项/预科/定向线索"),
    ]:
        if token in text and label not in labels:
            labels.append(label)
    return "；".join(labels) if labels else "no_machine_signal_but_pending_remark_review"


def campus_candidate(major_text):
    text = str(major_text or "")
    if "校区" not in text:
        return "", "pending_campus_or_location_review"
    matches = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{1,12}校区", text)
    if matches:
        return "；".join(dict.fromkeys(matches)), "machine_ocr_remark_candidate_unverified"
    return "含校区字样，需人工核备注", "machine_ocr_remark_candidate_unverified"


def machine_action(row):
    acceptance = row.get("机器专业接受度初判", "")
    if acceptance.startswith("默认不能接受"):
        return "K0-默认阻断风险先排除或低优先核"
    if row.get("结构保真优先级") in {"R0-结构边界阻断优先核", "R1-归属或结构异常先核"}:
        return "K1-结构保真先核"
    if row.get("专业偏好方向"):
        return "K2-偏好专业优先核验"
    if row.get("城市偏好命中") == "true":
        return "K3-城市偏好命中待核"
    if row.get("调剂影响等级") and row.get("调剂影响等级") != "待家庭确认":
        return "K4-调剂风险先核"
    return "K5-普通待了解"


def main():
    family_preferences = json.loads(FAMILY_PREFERENCES.read_text())
    preferred_cities = family_preferences.get("city_preference_order", [])
    tuition_limit = family_preferences["budget"]["annual_upper_limit_yuan"]

    master_rows = read_csv(MASTER_WORKBENCH)
    family_by_major = by_major_id(read_csv(FAMILY_FIT_MAJOR))
    structure_by_major = by_major_id(read_csv(STRUCTURAL_REGISTER))

    rows = []
    missing_join = Counter()
    for master in master_rows:
        major_id = master.get("专业行ID", "")
        family = family_by_major.get(major_id, {})
        structure = structure_by_major.get(major_id, {})
        if not family:
            missing_join["family_fit_major"] += 1
        if not structure:
            missing_join["structural_register"] += 1

        province, city, city_hit, city_order, city_status = city_candidate(
            master.get("院校名称OCR", ""), preferred_cities
        )
        campus, campus_status = campus_candidate(master.get("专业名称及备注OCR", ""))
        row = {
            "候选筛选准备ID": stable_id("FILTERPREP", [major_id]),
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源家庭底线逐专业筛选表": "data/working/issue19-family-fit-major-detail.csv",
            "来源结构保真登记表": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
            "来源期号": master.get("来源期号", ""),
            "来源PDF_SHA256": master.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "候选筛选可用状态": "pending_pdf_official_attribute_family_transfer_review",
            "专业行ID": major_id,
            "专业组出现ID": master.get("专业组出现ID", ""),
            "院校代码": master.get("院校代码", ""),
            "院校名称OCR": master.get("院校名称OCR", ""),
            "院校名称人工确认": "",
            "院校专业组代码OCR规范化": master.get("院校专业组代码OCR规范化", ""),
            "来源页码": master.get("来源页码", ""),
            "版面列": master.get("版面列", ""),
            "专业组内专业序号": master.get("专业组内专业序号", ""),
            "专业代号OCR": master.get("专业代号OCR", ""),
            "专业名称及备注OCR": master.get("专业名称及备注OCR", ""),
            "专业名称及备注短摘": master.get("专业名称及备注短摘", ""),
            "省份候选": province,
            "城市候选": city,
            "城市偏好命中": city_hit or "false",
            "城市偏好顺序": city_order,
            "城市候选来源": "院校名称OCR关键词" if city_hit else "",
            "城市字段状态": city_status,
            "办学属性候选": "",
            "公办民办初判": "pending_school_attribute_review",
            "中外合作/高收费初判": high_fee_or_coop(master),
            "办学属性核验状态": "pending_school_attribute_review",
            "专业偏好方向": master.get("专业偏好方向", ""),
            "专业方向机器标签来源": "专业名称及备注OCR关键词" if master.get("专业偏好方向") else "",
            "再选科目OCR候选": master.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": master.get("专业计划数OCR候选", ""),
            "专业计划数是否纯数字": family.get("专业计划数是否纯数字", ""),
            "学费OCR候选": master.get("学费OCR候选", ""),
            "学费OCR数字候选": family.get("学费OCR数字候选", ""),
            "学费是否纯数字": family.get("学费是否纯数字", ""),
            "预算上限元": str(tuition_limit),
            "是否超预算机器初判": tuition_over_budget(family, tuition_limit),
            "校区/办学地点候选": campus,
            "校区字段状态": campus_status,
            "体检/色觉/语种/单科/专项限制初判": special_limit(master),
            "专业风险类型": master.get("专业风险类型", ""),
            "风险阻断等级": master.get("风险阻断等级", ""),
            "结构保真优先级": structure.get("结构保真优先级", ""),
            "结构保真风险标签": structure.get("结构保真风险标签", ""),
            "机器专业接受度初判": master.get("机器专业接受度初判", ""),
            "机器阻断或待核原因": master.get("机器阻断或待核原因", ""),
            "家庭接受度核验状态": master.get("家庭接受度核验状态", ""),
            "家庭接受度结论": master.get("家庭接受度结论", ""),
            "同组真实招生明细数": master.get("同组真实招生明细数", ""),
            "同组偏好专业数": master.get("同组偏好专业数", ""),
            "同组医学护理排除专业数": master.get("同组医学护理排除专业数", ""),
            "同组高收费或超预算专业数": master.get("同组高收费或超预算专业数", ""),
            "同组特殊限制待核专业数": master.get("同组特殊限制待核专业数", ""),
            "调剂影响初判": master.get("调剂影响初判", ""),
            "调剂影响等级": master.get("调剂影响等级", ""),
            "同组调剂结论": master.get("同组调剂结论", ""),
            "PDF字段核验状态": master.get("PDF字段核验状态", ""),
            "湖北官方系统字段核验状态": master.get("湖北官方系统字段核验状态", ""),
            "高校官网/章程字段核验状态": "pending_school_charter_or_official_source_review",
            "官方系统证据编号": master.get("湖北官方核验包任务ID", ""),
            "高校官网证据状态": master.get("高校官网/章程辅证状态", ""),
            "高校官网证据匹配状态": master.get("高校官网证据匹配状态", ""),
            "三年投档稳定性状态": master.get("三年投档稳定性状态", ""),
            "稳定性分层": master.get("稳定性分层", ""),
            "候选筛选机器动作": "",
            "不得进入原因": "候选筛选准备表仍缺 PDF 原页、湖北官方系统、办学属性、校区、家庭接受度和调剂结论闭环；不得进入最终志愿排序",
            "下一步核验动作": "按机器动作筛选后，逐专业核 PDF 原页、湖北官方系统或省招办计划、高校官网/章程、办学属性、校区和家庭接受度。",
        }
        row["候选筛选机器动作"] = machine_action(row)
        rows.append(row)

    write_csv(OUTPUT, rows, FIELDS)
    summary = {
        "status": "issue19_candidate_filter_prep_not_final",
        "generated_by": "build_issue19_candidate_filter_prep_major_detail.py",
        "output_table": "data/working/issue19-candidate-filter-prep-major-detail.csv",
        "source_master_workbench": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_family_fit_major": "data/working/issue19-family-fit-major-detail.csv",
        "source_structural_register": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
        "row_count": len(rows),
        "unique_filter_prep_id_count": len({row["候选筛选准备ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "missing_join_counts": dict(missing_join),
        "city_hit_counts": dict(Counter(row["城市候选"] or "未命中当前城市偏好" for row in rows)),
        "city_status_counts": dict(Counter(row["城市字段状态"] for row in rows)),
        "school_attribute_status_counts": dict(Counter(row["办学属性核验状态"] for row in rows)),
        "tuition_over_budget_machine_counts": dict(Counter(row["是否超预算机器初判"] for row in rows)),
        "campus_status_counts": dict(Counter(row["校区字段状态"] for row in rows)),
        "machine_action_counts": dict(Counter(row["候选筛选机器动作"] for row in rows)),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "pending_school_attribute_review_count": sum(
            row["办学属性核验状态"] == "pending_school_attribute_review" for row in rows
        ),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
