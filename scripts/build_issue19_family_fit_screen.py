#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
FAMILY_PREFERENCES = ROOT / "data/working/family-preferences.json"
GROUP_QUALITY = ROOT / "data/working/issue19-full-quality-group-tiers.csv"
MAJOR_WORKBENCH = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"

GROUP_SCREEN_OUTPUT = ROOT / "data/working/issue19-family-fit-group-screen.csv"
MAJOR_SCREEN_OUTPUT = ROOT / "data/working/issue19-family-fit-major-detail.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-family-fit-screen-summary.json"

REJECTED_MEDICAL_LABEL = "医学/护理等排除方向"
HIGH_FEE_LABELS = {"中外合作或高收费", "学费超过当前上限"}
SPECIAL_LIMIT_LABELS = {"体检或色觉限制", "语种或单科限制", "专项/预科/定向等特殊类型"}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def split_labels(value):
    if not value:
        return set()
    return {part.strip() for part in str(value).replace(";", "；").split("；") if part.strip()}


def contains_any(value, labels):
    return bool(split_labels(value) & set(labels))


def preference_rank(value):
    labels = split_labels(value)
    if "数字媒体技术" in labels:
        return 1
    if "计算机类相关" in labels:
        return 2
    if "师范类相关" in labels:
        return 3
    return 9


def numeric_tuition(row):
    if row.get("学费是否纯数字") != "是":
        return None
    return as_int(row.get("学费OCR数字候选"))


def major_machine_acceptance(row, tuition_limit):
    risk_labels = split_labels(row.get("专业风险类型", ""))
    tuition = numeric_tuition(row)
    reasons = []

    if REJECTED_MEDICAL_LABEL in risk_labels:
        reasons.append("医学/护理等明确排除方向")
    if risk_labels & HIGH_FEE_LABELS:
        reasons.append("中外合作/高收费/超预算风险")
    if tuition is not None and tuition > tuition_limit:
        reasons.append(f"学费候选值超过{tuition_limit}元")
    if risk_labels & SPECIAL_LIMIT_LABELS:
        reasons.append("体检/语种/专项等特殊限制待核")
    if row.get("学费是否纯数字") != "是":
        reasons.append("学费字段非纯数字或缺失")
    if row.get("专业计划数是否纯数字") != "是":
        reasons.append("计划数字段非纯数字或缺失")
    if as_int(row.get("专业行高严重结构异常数")):
        reasons.append("专业行存在高严重结构异常")

    if REJECTED_MEDICAL_LABEL in risk_labels:
        acceptance = "默认不能接受-医学护理等排除方向"
    elif (risk_labels & HIGH_FEE_LABELS) or (tuition is not None and tuition > tuition_limit):
        acceptance = "默认不能接受-高收费或超预算"
    elif risk_labels & SPECIAL_LIMIT_LABELS:
        acceptance = "暂缓判断-特殊限制待核"
    elif row.get("专业偏好方向"):
        acceptance = "优先了解-命中当前偏好方向"
    else:
        acceptance = "待了解-未命中当前偏好方向"

    if not reasons:
        reasons.append("未触发自动阻断；仍需原PDF和官方来源核验")

    return acceptance, "；".join(reasons)


def major_transfer_effect(row, machine_acceptance):
    if machine_acceptance.startswith("默认不能接受"):
        return "若服从调剂可能形成不能接受风险"
    if machine_acceptance.startswith("暂缓判断"):
        return "调剂影响待核"
    if row.get("专业偏好方向"):
        return "主动填报优先专业候选"
    return "可作为调剂接受度待家庭判断专业"


def compact_major_detail(majors):
    pieces = []
    for row in sorted(majors, key=lambda item: as_int(item.get("专业组内专业序号")) or 999):
        pieces.append(
            "{seq}. {code} {name}｜计划:{plan}｜学费:{tuition}｜选科:{subject}｜偏好:{pref}｜风险:{risk}｜接受度:{acceptance}｜专业行ID:{major_id}".format(
                seq=row.get("专业组内专业序号", ""),
                code=row.get("专业代号OCR", ""),
                name=row.get("专业名称及备注OCR", ""),
                plan=row.get("专业计划数OCR候选", ""),
                tuition=row.get("学费OCR候选", ""),
                subject=row.get("再选科目OCR候选", ""),
                pref=row.get("专业偏好方向", "") or "无",
                risk=row.get("专业风险类型", "") or "无",
                acceptance=row.get("机器专业接受度初判", ""),
                major_id=row.get("专业行ID", ""),
            )
        )
    return "；".join(pieces)


def group_machine_fit(group, majors):
    if not majors:
        return "暂不可判断-无专业明细"
    if any(row["机器专业接受度初判"].startswith("默认不能接受-医学护理") for row in majors):
        return "默认不进主方案-组内存在医学/护理等排除专业"
    if any(row["机器专业接受度初判"].startswith("默认不能接受-高收费") for row in majors):
        return "默认不进主方案-组内存在高收费/超预算专业"
    if any(row["机器专业接受度初判"].startswith("暂缓判断") for row in majors):
        return "暂缓进入主方案-组内存在特殊限制待核专业"
    if any(row.get("专业偏好方向") for row in majors):
        return "优先复核-有偏好专业且未触发自动阻断"
    return "普通备选待了解-未命中当前偏好且未触发自动阻断"


def group_transfer_judgement(group_fit, group, majors):
    if not majors:
        return "不可判断-无专业明细"
    if group_fit.startswith("默认不进主方案"):
        return "调剂风险线索-组内存在默认不能接受专业"
    if group_fit.startswith("暂缓进入主方案"):
        return "暂不判断-特殊限制待核"
    if as_int(group.get("高严重结构异常数")):
        return "暂不判断-组内结构异常需先核页"
    if any(row.get("学费是否纯数字") != "是" for row in majors):
        return "暂不判断-组内存在学费字段待核"
    return "可进入人工调剂接受度判断"


def next_round_priority(group, majors, group_fit):
    candidate_hit = group.get("候选池V1命中") == "是"
    preference_hit = bool(majors) and any(row.get("专业偏好方向") for row in majors)
    if candidate_hit:
        return "R0-历史候选优先复核"
    if preference_hit and "默认不进主方案" not in group_fit:
        return "R1-偏好专业且未自动阻断"
    if preference_hit:
        return "R2-偏好专业但有硬风险先核风险"
    if group_fit.startswith("默认不进主方案"):
        return "R4-默认不进主方案低优先"
    return "R3-普通备选或保底扩展待了解"


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    family_preferences = json.loads(FAMILY_PREFERENCES.read_text())
    tuition_limit = family_preferences["budget"]["annual_upper_limit_yuan"]
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]

    group_rows = read_csv(GROUP_QUALITY)
    major_rows = read_csv(MAJOR_WORKBENCH)

    major_screen_rows = []
    majors_by_group = defaultdict(list)
    for row in major_rows:
        machine_acceptance, block_reason = major_machine_acceptance(row, tuition_limit)
        transfer_effect = major_transfer_effect(row, machine_acceptance)
        output = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "issue19_family_fit_screen_ocr_draft",
            "最终可用": "false",
            "核验状态": "needs_manual_pdf_review",
            "家庭偏好版本": family_preferences["last_updated"],
            "预算上限元": str(tuition_limit),
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
            "专业组号OCR": row.get("专业组号OCR", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "专业组内专业序号": row.get("专业组内专业序号", ""),
            "专业代号OCR": row.get("专业代号OCR", ""),
            "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
            "再选科目OCR候选": row.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": row.get("专业计划数OCR候选", ""),
            "专业计划数是否纯数字": row.get("专业计划数是否纯数字", ""),
            "学费OCR候选": row.get("学费OCR候选", ""),
            "学费OCR数字候选": row.get("学费OCR数字候选", ""),
            "学费是否纯数字": row.get("学费是否纯数字", ""),
            "专业偏好方向": row.get("专业偏好方向", ""),
            "专业风险类型": row.get("专业风险类型", ""),
            "专业字段完整性标记": row.get("专业字段完整性标记", ""),
            "专业行结构异常数": row.get("专业行结构异常数", ""),
            "专业行高严重结构异常数": row.get("专业行高严重结构异常数", ""),
            "逐专业复核优先级": row.get("逐专业复核优先级", ""),
            "机器专业接受度初判": machine_acceptance,
            "机器阻断或待核原因": block_reason,
            "调剂影响初判": transfer_effect,
            "家庭接受度核验状态": "pending_family_acceptance_review",
            "下一步": "回看第19期原PDF页和湖北官方系统；逐字段核对后由家庭确认是否接受该专业。",
        }
        major_screen_rows.append(output)
        majors_by_group[output["专业组出现ID"]].append(output)

    group_screen_rows = []
    for group in group_rows:
        group_id = group.get("专业组出现ID", "")
        majors = majors_by_group.get(group_id, [])
        preference_counts = Counter()
        for major in majors:
            preference_counts.update(split_labels(major.get("专业偏好方向", "")))
        preference_major_count = sum(1 for major in majors if major.get("专业偏好方向"))
        medical_reject_count = sum(
            row["机器专业接受度初判"].startswith("默认不能接受-医学护理") for row in majors
        )
        high_fee_reject_count = sum(
            row["机器专业接受度初判"].startswith("默认不能接受-高收费") for row in majors
        )
        special_limit_count = sum(row["机器专业接受度初判"].startswith("暂缓判断") for row in majors)
        tuition_unknown_count = sum(row.get("学费是否纯数字") != "是" for row in majors)
        plan_unknown_count = sum(row.get("专业计划数是否纯数字") != "是" for row in majors)
        group_fit = group_machine_fit(group, majors)
        transfer_judgement = group_transfer_judgement(group_fit, group, majors)
        priority = next_round_priority(group, majors, group_fit)
        output = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "issue19_family_fit_screen_ocr_draft",
            "最终可用": "false",
            "核验状态": "needs_manual_pdf_review",
            "家庭偏好版本": family_preferences["last_updated"],
            "预算上限元": str(tuition_limit),
            "院校代码": group.get("院校代码", ""),
            "院校名称OCR": group.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": group.get("院校专业组代码OCR规范化", ""),
            "专业组号OCR": group.get("专业组号OCR", ""),
            "专业组出现ID": group_id,
            "来源页码": group.get("来源页码", ""),
            "版面列": group.get("版面列", ""),
            "专业组标题OCR原文": group.get("专业组标题OCR原文", ""),
            "办学属性核验状态": "pending_school_attribute_review",
            "专业明细行数": str(len(majors)),
            "组内招生明细OCR": compact_major_detail(majors),
            "偏好专业数": str(preference_major_count),
            "数字媒体技术专业数": str(preference_counts.get("数字媒体技术", 0)),
            "计算机类相关专业数": str(preference_counts.get("计算机类相关", 0)),
            "师范类相关专业数": str(preference_counts.get("师范类相关", 0)),
            "医学护理排除专业数": str(medical_reject_count),
            "高收费或超预算专业数": str(high_fee_reject_count),
            "特殊限制待核专业数": str(special_limit_count),
            "学费非纯数字或缺失专业数": str(tuition_unknown_count),
            "计划数非纯数字或缺失专业数": str(plan_unknown_count),
            "组质量层级": group.get("相对质量层级", ""),
            "组复核优先级": group.get("复核优先级", ""),
            "组结构异常数": group.get("结构异常数", ""),
            "组高严重结构异常数": group.get("高严重结构异常数", ""),
            "候选池V1命中": group.get("候选池V1命中", ""),
            "样本学校命中": group.get("样本学校命中", ""),
            "机器家庭匹配初判": group_fit,
            "调剂初判": transfer_judgement,
            "下一轮复核优先级": priority,
            "下一步": "先核办学属性、公办/普通学费、组内全部专业和调剂范围；通过后再接入历史投档线排序。",
        }
        group_screen_rows.append(output)

    group_screen_rows.sort(
        key=lambda row: (
            row["下一轮复核优先级"],
            preference_rank(
                "；".join(
                    label
                    for label, count in [
                        ("数字媒体技术", as_int(row["数字媒体技术专业数"]) or 0),
                        ("计算机类相关", as_int(row["计算机类相关专业数"]) or 0),
                        ("师范类相关", as_int(row["师范类相关专业数"]) or 0),
                    ]
                    if count
                )
            ),
            row.get("院校专业组代码OCR规范化", ""),
        )
    )

    group_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "家庭偏好版本",
        "预算上限元",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组出现ID",
        "来源页码",
        "版面列",
        "专业组标题OCR原文",
        "办学属性核验状态",
        "专业明细行数",
        "组内招生明细OCR",
        "偏好专业数",
        "数字媒体技术专业数",
        "计算机类相关专业数",
        "师范类相关专业数",
        "医学护理排除专业数",
        "高收费或超预算专业数",
        "特殊限制待核专业数",
        "学费非纯数字或缺失专业数",
        "计划数非纯数字或缺失专业数",
        "组质量层级",
        "组复核优先级",
        "组结构异常数",
        "组高严重结构异常数",
        "候选池V1命中",
        "样本学校命中",
        "机器家庭匹配初判",
        "调剂初判",
        "下一轮复核优先级",
        "下一步",
    ]
    major_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "家庭偏好版本",
        "预算上限元",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
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
        "专业偏好方向",
        "专业风险类型",
        "专业字段完整性标记",
        "专业行结构异常数",
        "专业行高严重结构异常数",
        "逐专业复核优先级",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "调剂影响初判",
        "家庭接受度核验状态",
        "下一步",
    ]
    write_csv(GROUP_SCREEN_OUTPUT, group_screen_rows, group_fields)
    write_csv(MAJOR_SCREEN_OUTPUT, major_screen_rows, major_fields)

    group_fit_counts = Counter(row["机器家庭匹配初判"] for row in group_screen_rows)
    transfer_counts = Counter(row["调剂初判"] for row in group_screen_rows)
    priority_counts = Counter(row["下一轮复核优先级"] for row in group_screen_rows)
    major_acceptance_counts = Counter(row["机器专业接受度初判"] for row in major_screen_rows)
    summary = {
        "status": "issue19_family_fit_screen_ocr_draft_needs_manual_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "issue19_family_fit_screen_ocr_draft",
        "generated_by": "scripts/build_issue19_family_fit_screen.py",
        "inputs": input_snapshot(
            ROOT,
            [
                ISSUE19_SOURCE,
                FAMILY_PREFERENCES,
                GROUP_QUALITY,
                MAJOR_WORKBENCH,
            ],
        ),
        "family_preference_version": family_preferences["last_updated"],
        "tuition_limit_yuan": tuition_limit,
        "group_count": len(group_screen_rows),
        "major_count": len(major_screen_rows),
        "group_fit_counts": dict(sorted(group_fit_counts.items())),
        "transfer_judgement_counts": dict(sorted(transfer_counts.items())),
        "next_round_priority_counts": dict(sorted(priority_counts.items())),
        "major_acceptance_counts": dict(sorted(major_acceptance_counts.items())),
        "groups_with_preference_major_count": sum(as_int(row["偏好专业数"]) > 0 for row in group_screen_rows),
        "groups_with_digital_media_count": sum(as_int(row["数字媒体技术专业数"]) > 0 for row in group_screen_rows),
        "groups_with_computer_count": sum(as_int(row["计算机类相关专业数"]) > 0 for row in group_screen_rows),
        "groups_with_teacher_count": sum(as_int(row["师范类相关专业数"]) > 0 for row in group_screen_rows),
        "groups_default_not_main_plan_count": sum(
            row["机器家庭匹配初判"].startswith("默认不进主方案") for row in group_screen_rows
        ),
        "groups_priority_review_without_auto_block_count": sum(
            row["机器家庭匹配初判"] == "优先复核-有偏好专业且未触发自动阻断"
            for row in group_screen_rows
        ),
        "outputs": [
            str(GROUP_SCREEN_OUTPUT.relative_to(ROOT)),
            str(MAJOR_SCREEN_OUTPUT.relative_to(ROOT)),
        ],
        "notes": [
            "本表是 OCR 草案筛选视图，不是最终报考建议。",
            "办学属性没有权威字段时统一保持 pending_school_attribute_review，不自动判定公办或民办。",
            "医学护理、高收费/超预算、特殊限制和偏好方向均来自 OCR 风险/偏好标签，必须回看原PDF、湖北官方系统和高校章程。",
            "偏好专业数按命中偏好的专业行数统计，数字媒体技术/计算机类相关/师范类相关子类按标签拆分统计。",
            "组内招生明细已在专业组表中展开，后续判断调剂时必须看完整组内专业。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出家庭底线专业组筛选表：{GROUP_SCREEN_OUTPUT}")
    print(f"写出家庭底线逐专业筛选表：{MAJOR_SCREEN_OUTPUT}")
    print(f"写出家庭底线筛选摘要：{SUMMARY_OUTPUT}")
    print(f"专业组数：{len(group_screen_rows)}")
    print(f"专业明细数：{len(major_screen_rows)}")


if __name__ == "__main__":
    main()
