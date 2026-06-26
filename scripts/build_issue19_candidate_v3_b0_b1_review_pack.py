#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
CANDIDATE_V3_INTAKE = ROOT / "data/working/issue19-candidate-v3-review-intake.csv"
FAMILY_FIT_MAJORS = ROOT / "data/working/issue19-family-fit-major-detail.csv"
CANDIDATE_V2_MAJORS = ROOT / "data/working/issue19-candidate-v2-major-review-seed.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"

GROUP_PACK_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-group-review-pack.csv"
MAJOR_PACK_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-major-review-pack.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-review-pack-summary.json"

TARGET_BATCHES = {
    "B0-历史候选和组号问题优先核页",
    "B1-数字媒体技术优先核页",
}

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


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def split_labels(value):
    if not value:
        return set()
    return {part.strip() for part in str(value).replace(";", "；").split("；") if part.strip()}


def page_manifest_join(page_text, page_manifest_by_page, field):
    pages = [part.strip() for part in str(page_text or "").replace(";", "；").split("；") if part.strip()]
    values = []
    for page in pages:
        value = page_manifest_by_page.get(page, {}).get(field, "")
        if value:
            values.append(value)
    return "；".join(values)


def major_acceptance_from_labels(preference, risk, field_issue="", high_structure_count=""):
    risk_labels = split_labels(risk)
    reasons = []
    if REJECTED_MEDICAL_LABEL in risk_labels:
        reasons.append("医学/护理等明确排除方向")
    if risk_labels & HIGH_FEE_LABELS:
        reasons.append("中外合作/高收费/超预算风险")
    if risk_labels & SPECIAL_LIMIT_LABELS:
        reasons.append("体检/语种/专项等特殊限制待核")
    if field_issue:
        reasons.append(f"字段待核:{field_issue}")
    if as_int(high_structure_count):
        reasons.append("专业行存在高严重结构异常")

    if REJECTED_MEDICAL_LABEL in risk_labels:
        acceptance = "默认不能接受-医学护理等排除方向"
    elif risk_labels & HIGH_FEE_LABELS:
        acceptance = "默认不能接受-高收费或超预算"
    elif risk_labels & SPECIAL_LIMIT_LABELS:
        acceptance = "暂缓判断-特殊限制待核"
    elif preference:
        acceptance = "优先了解-命中当前偏好方向"
    else:
        acceptance = "待了解-未命中当前偏好方向"

    if not reasons:
        reasons.append("未触发自动阻断；仍需原PDF和官方来源核验")
    return acceptance, "；".join(reasons)


def transfer_effect_from_acceptance(preference, acceptance):
    if acceptance.startswith("默认不能接受"):
        return "若服从调剂可能形成不能接受风险"
    if acceptance.startswith("暂缓判断"):
        return "调剂影响待核"
    if preference:
        return "主动填报优先专业候选"
    return "可作为调剂接受度待家庭判断专业"


def group_review_focus(row):
    focus = []
    if row.get("复核批次", "").startswith("B0"):
        focus.append("先核历史候选对应的2026专业组是否真实存在、组号是否变化、组内专业是否完整")
    if row.get("复核批次", "").startswith("B1"):
        focus.append("先核数字媒体技术专业是否真实属于该组，并核完整调剂范围")
    if row.get("专业明细行数") == "0":
        focus.append("0明细组必须先补齐或确认2026组号变化/旧组号")
    if row.get("医学护理排除专业数") not in {"", "0"}:
        focus.append("组内含医学护理等家庭明确排除方向，先判断是否阻断调剂")
    if row.get("高收费或超预算专业数") not in {"", "0"}:
        focus.append("组内含高收费/超预算线索，先核学费和办学性质")
    if "历史线不得直接沿用" in row.get("历史线使用口径", ""):
        focus.append("历史投档线不得直接沿用，必须重新找2026组证据和可比历史组")
    if not focus:
        focus.append("逐字段核原PDF、湖北官方系统、省招办计划和高校章程")
    return "；".join(focus)


def pending_group_output(row, source_issue, source_pdf_sha256, task_count):
    return {
        "来源期号": source_issue,
        "来源PDF_SHA256": source_pdf_sha256,
        "数据阶段": "issue19_candidate_v3_b0_b1_review_pack",
        "最终可用": "false",
        "核验状态": "pending_b0_b1_original_page_review",
        "组核验包ID": stable_id(
            "GPK",
            [source_pdf_sha256, row.get("候选V3入口ID", ""), row.get("2026院校专业组代码", "")],
        ),
        "候选V3入口ID": row.get("候选V3入口ID", ""),
        "复核批次": row.get("复核批次", ""),
        "入口类型": row.get("入口类型", ""),
        "入口来源说明": row.get("入口来源说明", ""),
        "院校代码": row.get("院校代码", ""),
        "院校名称OCR": row.get("院校名称OCR", ""),
        "2026院校专业组代码": row.get("2026院校专业组代码", ""),
        "专业组出现ID": row.get("专业组出现ID", ""),
        "来源页码": row.get("来源页码", ""),
        "私有页图证据编号": row.get("私有页图证据编号", ""),
        "私有页图SHA256": row.get("私有页图SHA256", ""),
        "私有OCR文本证据编号": row.get("私有OCR文本证据编号", ""),
        "专业明细来源": row.get("专业明细来源", ""),
        "专业明细行数": row.get("专业明细行数", ""),
        "逐专业核验任务数": str(task_count),
        "偏好专业数": row.get("偏好专业数", ""),
        "数字媒体技术专业数": row.get("数字媒体技术专业数", ""),
        "计算机类相关专业数": row.get("计算机类相关专业数", ""),
        "师范类相关专业数": row.get("师范类相关专业数", ""),
        "医学护理排除专业数": row.get("医学护理排除专业数", ""),
        "高收费或超预算专业数": row.get("高收费或超预算专业数", ""),
        "特殊限制待核专业数": row.get("特殊限制待核专业数", ""),
        "机器家庭匹配初判": row.get("机器家庭匹配初判", ""),
        "调剂初判": row.get("调剂初判", ""),
        "组质量层级": row.get("组质量层级", ""),
        "组复核优先级": row.get("组复核优先级", ""),
        "组结构异常数": row.get("组结构异常数", ""),
        "组高严重结构异常数": row.get("组高严重结构异常数", ""),
        "历史候选匹配": row.get("历史候选匹配", ""),
        "候选池原始项": row.get("候选池原始项", ""),
        "候选城市": row.get("候选城市", ""),
        "候选年份覆盖": row.get("候选年份覆盖", ""),
        "2023同组投档线": row.get("2023同组投档线", ""),
        "2024同组投档线": row.get("2024同组投档线", ""),
        "2025同组投档线": row.get("2025同组投档线", ""),
        "三年同组命中数": row.get("三年同组命中数", ""),
        "等位分差摘要": row.get("等位分差摘要", ""),
        "历史线使用口径": row.get("历史线使用口径", ""),
        "组内招生明细": row.get("组内招生明细", ""),
        "核页重点": group_review_focus(row),
        "PDF原页核验状态": "pending_original_pdf_page_review",
        "湖北官方系统核验状态": "pending_hubei_official_plan_review",
        "高校官网章程核验状态": "pending_school_charter_review",
        "家庭接受度核验状态": "pending_family_acceptance_review",
        "调剂结论状态": "pending_transfer_decision",
        "历史线核验状态": "pending_history_line_review",
        "升级判定状态": "pending_upgrade_decision",
        "可进入下一阶段": "false",
        "下一步": "按页码回看第19期原PDF；逐专业核对后，再补湖北官方系统、省招办计划、高校章程、家庭接受度和调剂结论。",
    }


def output_major_from_family(row, group_row, source_issue, source_pdf_sha256):
    acceptance = row.get("机器专业接受度初判", "")
    transfer_effect = row.get("调剂影响初判", "")
    if not acceptance:
        acceptance, _ = major_acceptance_from_labels(
            row.get("专业偏好方向", ""),
            row.get("专业风险类型", ""),
            row.get("专业字段完整性标记", ""),
            row.get("专业行高严重结构异常数", ""),
        )
    if not transfer_effect:
        transfer_effect = transfer_effect_from_acceptance(row.get("专业偏好方向", ""), acceptance)
    return {
        "专业行来源": "family_fit_major_detail",
        "专业行ID": row.get("专业行ID", ""),
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
        "机器专业接受度初判": acceptance,
        "机器阻断或待核原因": row.get("机器阻断或待核原因", ""),
        "调剂影响初判": transfer_effect,
    }


def output_major_from_v2(row, group_row, source_issue, source_pdf_sha256):
    acceptance, reason = major_acceptance_from_labels(
        row.get("偏好方向", ""),
        row.get("风险类型", ""),
        row.get("字段完整性标记", ""),
        "1" if row.get("结构异常类型") else "",
    )
    return {
        "专业行来源": "candidate_v2_major_review_seed",
        "专业行ID": "",
        "专业组内专业序号": row.get("组内序号", ""),
        "专业代号OCR": row.get("专业代号", ""),
        "专业名称及备注OCR": row.get("专业名称及备注", ""),
        "再选科目OCR候选": row.get("再选科目候选", ""),
        "专业计划数OCR候选": row.get("专业计划数候选", ""),
        "专业计划数是否纯数字": "是" if str(row.get("专业计划数候选", "")).isdigit() else "否",
        "学费OCR候选": row.get("学费候选", ""),
        "学费OCR数字候选": row.get("学费数字候选", ""),
        "学费是否纯数字": "是" if str(row.get("学费候选", "")).isdigit() else "否",
        "专业偏好方向": row.get("偏好方向", ""),
        "专业风险类型": row.get("风险类型", ""),
        "专业字段完整性标记": row.get("字段完整性标记", ""),
        "专业行结构异常数": "1" if row.get("结构异常类型") else "0",
        "专业行高严重结构异常数": "1" if row.get("结构异常类型") else "0",
        "逐专业复核优先级": "P0-逐专业必须核页",
        "机器专业接受度初判": acceptance,
        "机器阻断或待核原因": reason,
        "调剂影响初判": transfer_effect_from_acceptance(row.get("偏好方向", ""), acceptance),
    }


def placeholder_major(group_row):
    return {
        "专业行来源": "zero_detail_group_placeholder",
        "专业行ID": "",
        "专业组内专业序号": "",
        "专业代号OCR": "",
        "专业名称及备注OCR": "",
        "再选科目OCR候选": "",
        "专业计划数OCR候选": "",
        "专业计划数是否纯数字": "",
        "学费OCR候选": "",
        "学费OCR数字候选": "",
        "学费是否纯数字": "",
        "专业偏好方向": "",
        "专业风险类型": "0明细组",
        "专业字段完整性标记": "missing_major_detail",
        "专业行结构异常数": "",
        "专业行高严重结构异常数": "",
        "逐专业复核优先级": "P0-先补齐组内专业明细",
        "机器专业接受度初判": "暂不可判断-无专业明细",
        "机器阻断或待核原因": "0明细组，必须先核第19期原页或确认2026组号变化/旧组号",
        "调剂影响初判": "不可判断-无专业明细",
    }


def major_review_row(base, group_row, source_issue, source_pdf_sha256):
    task_id = stable_id(
        "MPK",
        [
            source_pdf_sha256,
            group_row.get("候选V3入口ID", ""),
            group_row.get("2026院校专业组代码", ""),
            base.get("专业行来源", ""),
            base.get("专业行ID", ""),
            base.get("专业组内专业序号", ""),
            base.get("专业代号OCR", ""),
            base.get("专业名称及备注OCR", ""),
        ],
    )
    return {
        "来源期号": source_issue,
        "来源PDF_SHA256": source_pdf_sha256,
        "数据阶段": "issue19_candidate_v3_b0_b1_review_pack",
        "最终可用": "false",
        "核验状态": "pending_b0_b1_major_review",
        "专业核验任务ID": task_id,
        "候选V3入口ID": group_row.get("候选V3入口ID", ""),
        "复核批次": group_row.get("复核批次", ""),
        "入口类型": group_row.get("入口类型", ""),
        "院校代码": group_row.get("院校代码", ""),
        "院校名称OCR": group_row.get("院校名称OCR", ""),
        "2026院校专业组代码": group_row.get("2026院校专业组代码", ""),
        "专业组出现ID": group_row.get("专业组出现ID", ""),
        "来源页码": group_row.get("来源页码", ""),
        "私有页图证据编号": group_row.get("私有页图证据编号", ""),
        "专业明细来源": group_row.get("专业明细来源", ""),
        "专业行来源": base.get("专业行来源", ""),
        "专业行ID": base.get("专业行ID", ""),
        "专业组内专业序号": base.get("专业组内专业序号", ""),
        "专业代号OCR": base.get("专业代号OCR", ""),
        "专业名称及备注OCR": base.get("专业名称及备注OCR", ""),
        "再选科目OCR候选": base.get("再选科目OCR候选", ""),
        "专业计划数OCR候选": base.get("专业计划数OCR候选", ""),
        "专业计划数是否纯数字": base.get("专业计划数是否纯数字", ""),
        "学费OCR候选": base.get("学费OCR候选", ""),
        "学费OCR数字候选": base.get("学费OCR数字候选", ""),
        "学费是否纯数字": base.get("学费是否纯数字", ""),
        "专业偏好方向": base.get("专业偏好方向", ""),
        "专业风险类型": base.get("专业风险类型", ""),
        "专业字段完整性标记": base.get("专业字段完整性标记", ""),
        "专业行结构异常数": base.get("专业行结构异常数", ""),
        "专业行高严重结构异常数": base.get("专业行高严重结构异常数", ""),
        "逐专业复核优先级": base.get("逐专业复核优先级", ""),
        "机器专业接受度初判": base.get("机器专业接受度初判", ""),
        "机器阻断或待核原因": base.get("机器阻断或待核原因", ""),
        "调剂影响初判": base.get("调剂影响初判", ""),
        "PDF专业代号确认值": "",
        "PDF专业名称确认值": "",
        "PDF计划数确认值": "",
        "PDF学费确认值": "",
        "PDF选科确认值": "",
        "湖北官方系统确认值": "",
        "高校官网章程确认值": "",
        "家庭接受度人工结论": "",
        "调剂影响人工结论": "",
        "私有证据编号": "",
        "字段核验状态": "pending",
        "是否阻断组升级": "是",
        "可进入最终专业列表": "false",
        "下一步": "逐专业回看第19期原PDF，并与湖北官方系统、省招办计划、高校章程交叉核验；再由家庭确认接受度。",
    }


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]

    intake_rows = read_csv(CANDIDATE_V3_INTAKE)
    family_major_rows = read_csv(FAMILY_FIT_MAJORS)
    v2_major_rows = read_csv(CANDIDATE_V2_MAJORS)
    page_manifest_rows = read_csv(PAGE_MANIFEST)
    page_manifest_by_page = {row["PDF页码"]: row for row in page_manifest_rows}

    selected_groups = [row for row in intake_rows if row.get("复核批次") in TARGET_BATCHES]
    family_majors_by_group_id = defaultdict(list)
    for row in family_major_rows:
        family_majors_by_group_id[row.get("专业组出现ID", "")].append(row)

    v2_majors_by_code = defaultdict(list)
    for row in v2_major_rows:
        v2_majors_by_code[row.get("2026院校专业组代码", "")].append(row)

    major_rows = []
    major_count_by_group = Counter()
    placeholder_count = 0
    for group in selected_groups:
        group_code = group.get("2026院校专业组代码", "")
        if group.get("专业明细来源") == "candidate_v2_review_seed":
            source_majors = [
                output_major_from_v2(row, group, source_issue, source_pdf_sha256)
                for row in sorted(v2_majors_by_code.get(group_code, []), key=lambda item: as_int(item.get("组内序号")) or 999)
            ]
        else:
            group_id = group.get("专业组出现ID", "")
            source_majors = [
                output_major_from_family(row, group, source_issue, source_pdf_sha256)
                for row in sorted(
                    family_majors_by_group_id.get(group_id, []),
                    key=lambda item: as_int(item.get("专业组内专业序号")) or 999,
                )
            ]
        if not source_majors:
            source_majors = [placeholder_major(group)]
            placeholder_count += 1

        for major in source_majors:
            major_rows.append(major_review_row(major, group, source_issue, source_pdf_sha256))
            major_count_by_group[group.get("候选V3入口ID", "")] += 1

    group_rows = [
        pending_group_output(row, source_issue, source_pdf_sha256, major_count_by_group[row.get("候选V3入口ID", "")])
        for row in selected_groups
    ]

    group_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "组核验包ID",
        "候选V3入口ID",
        "复核批次",
        "入口类型",
        "入口来源说明",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业组出现ID",
        "来源页码",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "专业明细来源",
        "专业明细行数",
        "逐专业核验任务数",
        "偏好专业数",
        "数字媒体技术专业数",
        "计算机类相关专业数",
        "师范类相关专业数",
        "医学护理排除专业数",
        "高收费或超预算专业数",
        "特殊限制待核专业数",
        "机器家庭匹配初判",
        "调剂初判",
        "组质量层级",
        "组复核优先级",
        "组结构异常数",
        "组高严重结构异常数",
        "历史候选匹配",
        "候选池原始项",
        "候选城市",
        "候选年份覆盖",
        "2023同组投档线",
        "2024同组投档线",
        "2025同组投档线",
        "三年同组命中数",
        "等位分差摘要",
        "历史线使用口径",
        "组内招生明细",
        "核页重点",
        "PDF原页核验状态",
        "湖北官方系统核验状态",
        "高校官网章程核验状态",
        "家庭接受度核验状态",
        "调剂结论状态",
        "历史线核验状态",
        "升级判定状态",
        "可进入下一阶段",
        "下一步",
    ]
    major_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "专业核验任务ID",
        "候选V3入口ID",
        "复核批次",
        "入口类型",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业组出现ID",
        "来源页码",
        "私有页图证据编号",
        "专业明细来源",
        "专业行来源",
        "专业行ID",
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
        "PDF专业代号确认值",
        "PDF专业名称确认值",
        "PDF计划数确认值",
        "PDF学费确认值",
        "PDF选科确认值",
        "湖北官方系统确认值",
        "高校官网章程确认值",
        "家庭接受度人工结论",
        "调剂影响人工结论",
        "私有证据编号",
        "字段核验状态",
        "是否阻断组升级",
        "可进入最终专业列表",
        "下一步",
    ]
    write_csv(GROUP_PACK_OUTPUT, group_rows, group_fields)
    write_csv(MAJOR_PACK_OUTPUT, major_rows, major_fields)

    selected_pages = sorted({page for row in group_rows for page in str(row.get("来源页码", "")).replace(";", "；").split("；") if page})
    missing_page_hash_groups = [
        row.get("2026院校专业组代码", "")
        for row in group_rows
        if not page_manifest_join(row.get("来源页码", ""), page_manifest_by_page, "私有页图SHA256")
    ]

    summary = {
        "status": "issue19_candidate_v3_b0_b1_review_pack_pending_manual_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "issue19_candidate_v3_b0_b1_review_pack",
        "generated_by": "scripts/build_issue19_candidate_v3_b0_b1_review_pack.py",
        "inputs": input_snapshot(
            ROOT,
            [ISSUE19_SOURCE, CANDIDATE_V3_INTAKE, FAMILY_FIT_MAJORS, CANDIDATE_V2_MAJORS, PAGE_MANIFEST],
        ),
        "target_batches": sorted(TARGET_BATCHES),
        "group_count": len(group_rows),
        "major_review_task_count": len(major_rows),
        "placeholder_major_task_count": placeholder_count,
        "batch_counts": dict(sorted(Counter(row["复核批次"] for row in group_rows).items())),
        "group_major_source_counts": dict(sorted(Counter(row["专业明细来源"] for row in group_rows).items())),
        "major_row_source_counts": dict(sorted(Counter(row["专业行来源"] for row in major_rows).items())),
        "zero_detail_group_codes": sorted(
            row["2026院校专业组代码"] for row in group_rows if row.get("专业明细行数") == "0"
        ),
        "selected_page_count": len(selected_pages),
        "selected_pages": selected_pages,
        "missing_page_hash_groups": missing_page_hash_groups,
        "final_available_count": sum(row["可进入下一阶段"] == "true" for row in group_rows)
        + sum(row["可进入最终专业列表"] == "true" for row in major_rows),
        "notes": [
            "本包只覆盖候选V3的B0和B1优先批次，用于原页核验和逐专业字段回填，不是最终建议。",
            "逐专业行不从组内招生明细文本切分；candidate_v2_review_seed 使用V2补种明细，family_fit_full_ocr 使用家庭底线逐专业结构化表。",
            "0明细组保留占位任务，必须先确认2026组号变化、旧组号或补齐专业明细。",
            "所有行保持最终可用=false，进入下一阶段前必须完成PDF原页、湖北官方系统、高校章程、家庭接受度和调剂结论核验。",
        ],
        "outputs": [
            str(GROUP_PACK_OUTPUT.relative_to(ROOT)),
            str(MAJOR_PACK_OUTPUT.relative_to(ROOT)),
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出候选V3 B0/B1组级核验包：{GROUP_PACK_OUTPUT}")
    print(f"写出候选V3 B0/B1逐专业核验包：{MAJOR_PACK_OUTPUT}")
    print(f"写出候选V3 B0/B1核验包摘要：{SUMMARY_OUTPUT}")
    print(f"组数：{len(group_rows)}")
    print(f"逐专业任务数：{len(major_rows)}")


if __name__ == "__main__":
    main()
