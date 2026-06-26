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
FAMILY_FIT_MAJOR_DETAIL = ROOT / "data/working/issue19-family-fit-major-detail.csv"
CANDIDATE_V2_MAJOR_SEED = ROOT / "data/working/issue19-candidate-v2-major-review-seed.csv"

OUTPUT = ROOT / "data/working/issue19-candidate-v3-admission-detail.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v3-admission-detail-summary.json"

DATA_STAGE = "issue19_candidate_v3_admission_detail"


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


def v2_machine_acceptance(row):
    risk = row.get("风险类型", "")
    preference = row.get("偏好方向", "")
    if "医学" in risk or "护理" in risk:
        return "默认不能接受-医学护理等排除方向"
    if "中外合作" in risk or "高收费" in risk or "学费超过" in risk:
        return "默认不能接受-高收费或超预算"
    if "体检" in risk or "语种" in risk or "单科" in risk or "专项" in risk:
        return "暂缓判断-特殊限制待核"
    if preference:
        return "优先了解-命中当前偏好方向"
    return "待了解-未命中当前偏好方向"


def v2_block_reason(row):
    pieces = []
    if row.get("风险类型"):
        pieces.append(row["风险类型"])
    if row.get("字段完整性标记"):
        pieces.append(f"字段待核:{row['字段完整性标记']}")
    if row.get("结构异常类型"):
        pieces.append(f"结构异常:{row['结构异常类型']}")
    if not pieces:
        pieces.append("未触发自动阻断；仍需原PDF和官方来源核验")
    return "；".join(pieces)


def transfer_effect(machine_acceptance, preference):
    if machine_acceptance.startswith("默认不能接受"):
        return "若服从调剂可能形成不能接受风险"
    if machine_acceptance.startswith("暂缓判断"):
        return "调剂影响待核"
    if preference:
        return "主动填报优先专业候选"
    return "可作为调剂接受度待家庭判断专业"


def normalize_family_major(row):
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
        "机器专业接受度初判": row.get("机器专业接受度初判", ""),
        "机器阻断或待核原因": row.get("机器阻断或待核原因", ""),
        "调剂影响初判": row.get("调剂影响初判", ""),
    }


def normalize_v2_major(row):
    machine_acceptance = v2_machine_acceptance(row)
    preference = row.get("偏好方向", "")
    high_structure = "高" in row.get("结构异常类型", "")
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
        "专业偏好方向": preference,
        "专业风险类型": row.get("风险类型", ""),
        "专业字段完整性标记": row.get("字段完整性标记", ""),
        "专业行结构异常数": "1" if row.get("结构异常规则ID") else "0",
        "专业行高严重结构异常数": "1" if high_structure else "0",
        "逐专业复核优先级": "P0-逐专业必须核页",
        "机器专业接受度初判": machine_acceptance,
        "机器阻断或待核原因": v2_block_reason(row),
        "调剂影响初判": transfer_effect(machine_acceptance, preference),
    }


def zero_detail_major():
    return {
        "专业行来源": "zero_detail_group_placeholder",
        "专业行ID": "",
        "专业组内专业序号": "",
        "专业代号OCR": "",
        "专业名称及备注OCR": "",
        "再选科目OCR候选": "",
        "专业计划数OCR候选": "",
        "专业计划数是否纯数字": "否",
        "学费OCR候选": "",
        "学费OCR数字候选": "",
        "学费是否纯数字": "否",
        "专业偏好方向": "",
        "专业风险类型": "0明细组",
        "专业字段完整性标记": "zero_detail_group",
        "专业行结构异常数": "1",
        "专业行高严重结构异常数": "1",
        "逐专业复核优先级": "P0-先补齐专业明细",
        "机器专业接受度初判": "暂不可判断-无专业明细",
        "机器阻断或待核原因": "该院校专业组暂无可用逐专业明细，必须先核第19期原页或湖北官方系统",
        "调剂影响初判": "不可判断-无专业明细",
    }


def detail_sort_key(row):
    seq = as_int(row.get("专业组内专业序号"))
    code = row.get("专业代号OCR", "")
    name = row.get("专业名称及备注OCR", "")
    return (seq if seq is not None else 9999, code, name)


def build_row(group, major, index):
    is_placeholder = major["专业行来源"] == "zero_detail_group_placeholder"
    detail_id = stable_id(
        "V3D",
        [
            group.get("来源PDF_SHA256", ""),
            group.get("候选V3入口ID", ""),
            major.get("专业行来源", ""),
            major.get("专业行ID", ""),
            major.get("专业组内专业序号", ""),
            major.get("专业代号OCR", ""),
            major.get("专业名称及备注OCR", ""),
            index,
        ],
    )
    next_step = (
        "0明细占位只用于保留专业组线索；先回看第19期原页或湖北官方系统补齐招生明细。"
        if is_placeholder
        else "逐专业回看第19期原PDF，并与湖北官方系统、省招办计划、高校章程交叉核验；再由家庭确认接受度。"
    )
    output = {
        "招生明细主表行ID": detail_id,
        "主表粒度": "逐专业招生明细",
        "是否真实招生明细": "false" if is_placeholder else "true",
        "是否0明细占位": "true" if is_placeholder else "false",
        "组级索引文件": "data/working/issue19-candidate-v3-review-intake.csv",
        "来源期号": group.get("来源期号", ""),
        "来源PDF_SHA256": group.get("来源PDF_SHA256", ""),
        "数据阶段": DATA_STAGE,
        "最终可用": "false",
        "核验状态": "pending_v3_detail_manual_review",
        "候选V3入口ID": group.get("候选V3入口ID", ""),
        "入口类型": group.get("入口类型", ""),
        "入口来源说明": group.get("入口来源说明", ""),
        "复核批次": group.get("复核批次", ""),
        "候选闸门状态": group.get("候选闸门状态", ""),
        "可进入最终候选": group.get("可进入最终候选", "false"),
        "院校代码": group.get("院校代码", ""),
        "院校名称OCR": group.get("院校名称OCR", ""),
        "2026院校专业组代码": group.get("2026院校专业组代码", ""),
        "专业组出现ID": group.get("专业组出现ID", ""),
        "来源页码": group.get("来源页码", ""),
        "私有页图证据编号": group.get("私有页图证据编号", ""),
        "私有页图SHA256": group.get("私有页图SHA256", ""),
        "私有OCR文本证据编号": group.get("私有OCR文本证据编号", ""),
        "办学属性核验状态": group.get("办学属性核验状态", ""),
        "专业明细来源": group.get("专业明细来源", ""),
        "专业明细行数": group.get("专业明细行数", ""),
        "偏好专业数": group.get("偏好专业数", ""),
        "数字媒体技术专业数": group.get("数字媒体技术专业数", ""),
        "计算机类相关专业数": group.get("计算机类相关专业数", ""),
        "师范类相关专业数": group.get("师范类相关专业数", ""),
        "医学护理排除专业数": group.get("医学护理排除专业数", ""),
        "高收费或超预算专业数": group.get("高收费或超预算专业数", ""),
        "特殊限制待核专业数": group.get("特殊限制待核专业数", ""),
        "机器家庭匹配初判": group.get("机器家庭匹配初判", ""),
        "调剂初判": group.get("调剂初判", ""),
        "下一轮复核优先级": group.get("下一轮复核优先级", ""),
        "组质量层级": group.get("组质量层级", ""),
        "组复核优先级": group.get("组复核优先级", ""),
        "组结构异常数": group.get("组结构异常数", ""),
        "组高严重结构异常数": group.get("组高严重结构异常数", ""),
        "历史候选匹配": group.get("历史候选匹配", ""),
        "候选池原始项": group.get("候选池原始项", ""),
        "候选城市": group.get("候选城市", ""),
        "候选年份覆盖": group.get("候选年份覆盖", ""),
        "2023同组投档线": group.get("2023同组投档线", ""),
        "2024同组投档线": group.get("2024同组投档线", ""),
        "2025同组投档线": group.get("2025同组投档线", ""),
        "三年同组命中数": group.get("三年同组命中数", ""),
        "等位分差摘要": group.get("等位分差摘要", ""),
        "历史线使用口径": group.get("历史线使用口径", ""),
        "组级PDF原页核验状态": group.get("PDF原页核验状态", ""),
        "组级湖北官方系统核验状态": group.get("湖北官方系统核验状态", ""),
        "组级高校官网章程核验状态": group.get("高校官网章程核验状态", ""),
        "组级家庭接受度核验状态": group.get("家庭接受度核验状态", ""),
        "组级调剂结论状态": group.get("调剂结论状态", ""),
        "组级历史线核验状态": group.get("历史线核验状态", ""),
        "组级核验缺口": group.get("核验缺口", ""),
        "专业行来源": major.get("专业行来源", ""),
        "专业行ID": major.get("专业行ID", ""),
        "专业组内专业序号": major.get("专业组内专业序号", ""),
        "专业代号OCR": major.get("专业代号OCR", ""),
        "专业名称及备注OCR": major.get("专业名称及备注OCR", ""),
        "再选科目OCR候选": major.get("再选科目OCR候选", ""),
        "专业计划数OCR候选": major.get("专业计划数OCR候选", ""),
        "专业计划数是否纯数字": major.get("专业计划数是否纯数字", ""),
        "学费OCR候选": major.get("学费OCR候选", ""),
        "学费OCR数字候选": major.get("学费OCR数字候选", ""),
        "学费是否纯数字": major.get("学费是否纯数字", ""),
        "专业偏好方向": major.get("专业偏好方向", ""),
        "专业风险类型": major.get("专业风险类型", ""),
        "专业字段完整性标记": major.get("专业字段完整性标记", ""),
        "专业行结构异常数": major.get("专业行结构异常数", ""),
        "专业行高严重结构异常数": major.get("专业行高严重结构异常数", ""),
        "逐专业复核优先级": major.get("逐专业复核优先级", ""),
        "机器专业接受度初判": major.get("机器专业接受度初判", ""),
        "机器阻断或待核原因": major.get("机器阻断或待核原因", ""),
        "调剂影响初判": major.get("调剂影响初判", ""),
        "PDF字段核验状态": "pending_original_pdf_page_review",
        "湖北官方系统字段核验状态": "pending_hubei_official_plan_review",
        "高校官网/章程字段核验状态": "pending_school_plan_or_charter_review",
        "家庭接受度人工结论状态": "pending_family_acceptance_review",
        "调剂影响人工结论状态": "pending_transfer_decision",
        "字段核验状态": "pending",
        "是否阻断组升级": "是",
        "可进入最终专业列表": "false",
        "可进入下一阶段": "false",
        "下一步": next_step,
    }
    return output


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_pdf_sha256 = issue19_source["source"]["sha256"]
    group_rows = read_csv(CANDIDATE_V3_INTAKE)
    family_major_rows = read_csv(FAMILY_FIT_MAJOR_DETAIL)
    v2_major_rows = read_csv(CANDIDATE_V2_MAJOR_SEED)

    family_by_group_occurrence = defaultdict(list)
    for row in family_major_rows:
        family_by_group_occurrence[row["专业组出现ID"]].append(normalize_family_major(row))

    v2_by_group_code = defaultdict(list)
    for row in v2_major_rows:
        v2_by_group_code[row["2026院校专业组代码"]].append(normalize_v2_major(row))

    output_rows = []
    missing_detail_groups = []
    expected_detail_count = 0
    for group_index, group in enumerate(group_rows, start=1):
        expected_count = as_int(group.get("专业明细行数")) or 0
        expected_detail_count += expected_count
        if group.get("专业明细来源") == "candidate_v2_review_seed":
            majors = v2_by_group_code.get(group["2026院校专业组代码"], [])
        else:
            majors = family_by_group_occurrence.get(group["专业组出现ID"], [])

        if not majors:
            if expected_count == 0:
                majors = [zero_detail_major()]
            else:
                missing_detail_groups.append(
                    {
                        "候选V3入口ID": group.get("候选V3入口ID", ""),
                        "2026院校专业组代码": group.get("2026院校专业组代码", ""),
                        "专业明细来源": group.get("专业明细来源", ""),
                        "专业明细行数": group.get("专业明细行数", ""),
                    }
                )
                majors = [zero_detail_major()]

        for major_index, major in enumerate(sorted(majors, key=detail_sort_key), start=1):
            output_rows.append(build_row(group, major, f"{group_index}-{major_index}"))

    fields = list(output_rows[0].keys()) if output_rows else []
    write_csv(OUTPUT, output_rows, fields)

    row_source_counts = Counter(row["专业行来源"] for row in output_rows)
    batch_counts = Counter(row["复核批次"] for row in output_rows)
    group_batch_counts = Counter(row["复核批次"] for row in group_rows)
    detail_rows_by_group = Counter(row["候选V3入口ID"] for row in output_rows)
    mismatch_groups = [
        {
            "候选V3入口ID": group.get("候选V3入口ID", ""),
            "2026院校专业组代码": group.get("2026院校专业组代码", ""),
            "专业明细行数": group.get("专业明细行数", ""),
            "实际招生明细主表行数": str(detail_rows_by_group.get(group.get("候选V3入口ID", ""), 0)),
        }
        for group in group_rows
        if detail_rows_by_group.get(group.get("候选V3入口ID", ""), 0)
        != ((as_int(group.get("专业明细行数")) or 0) or 1)
    ]
    summary = {
        "status": "issue19_candidate_v3_admission_detail_not_final",
        "generated_by": Path(__file__).name,
        "source_pdf_sha256": source_pdf_sha256,
        "default_discussion_table": str(OUTPUT.relative_to(ROOT)),
        "group_index_table": str(CANDIDATE_V3_INTAKE.relative_to(ROOT)),
        "group_index_count": len(group_rows),
        "expected_real_detail_count_from_group_index": expected_detail_count,
        "admission_detail_row_count": len(output_rows),
        "real_admission_detail_count": sum(row["是否真实招生明细"] == "true" for row in output_rows),
        "zero_detail_placeholder_count": sum(row["是否0明细占位"] == "true" for row in output_rows),
        "row_source_counts": dict(sorted(row_source_counts.items())),
        "batch_counts": dict(sorted(batch_counts.items())),
        "group_batch_counts": dict(sorted(group_batch_counts.items())),
        "missing_detail_group_count": len(missing_detail_groups),
        "missing_detail_groups": missing_detail_groups,
        "detail_count_mismatch_group_count": len(mismatch_groups),
        "detail_count_mismatch_groups": mismatch_groups[:20],
        "unique_admission_detail_id_count": len({row["招生明细主表行ID"] for row in output_rows}),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "major_final_available_count": sum(
            row["可进入最终专业列表"] == "true" for row in output_rows
        ),
        "fidelity_note": "该表一行对应一个招生专业或0明细占位；院校专业组文件只作索引、投档线和调剂范围承载，不能作为候选讨论主表。",
        "inputs": input_snapshot(
            ROOT,
            [ISSUE19_SOURCE, CANDIDATE_V3_INTAKE, FAMILY_FIT_MAJOR_DETAIL, CANDIDATE_V2_MAJOR_SEED],
        ),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"写出 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行；"
        f"真实明细 {summary['real_admission_detail_count']}，0明细占位 {summary['zero_detail_placeholder_count']}"
    )


if __name__ == "__main__":
    main()
