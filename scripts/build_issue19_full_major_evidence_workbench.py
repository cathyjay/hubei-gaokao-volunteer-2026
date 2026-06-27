#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FULL_MAJOR_VERIFICATION_BATCHES = ROOT / "data/working/issue19-full-major-verification-batches.csv"
FULL_MAJOR_FIDELITY_LEDGER = ROOT / "data/working/issue19-full-major-field-fidelity-ledger.csv"
FAMILY_MAJOR_DETAIL = ROOT / "data/working/issue19-family-fit-major-detail.csv"
PAGE_FIDELITY_QUEUE = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"
PRIORITY_GROUP_MAJOR_PACK = ROOT / "data/working/issue19-priority-group-major-review-pack.csv"
PRIORITY_MAJOR_EVIDENCE_WORKBENCH = ROOT / "data/working/issue19-priority-major-evidence-workbench.csv"
V3_FIDELITY_LEDGER = ROOT / "data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv"
B0_B1_SCHOOL_SOURCE_QUEUE = ROOT / "data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv"
D0_PDF_EVIDENCE = ROOT / "data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv"
TOUDANG_2023 = ROOT / "data/derived/hubei-2023-physics-toudang-parsed.csv"
TOUDANG_2024 = ROOT / "data/derived/hubei-2024-physics-toudang-parsed.csv"
TOUDANG_2025 = ROOT / "data/derived/hubei-2025-physics-toudang-parsed.csv"

OUTPUT = ROOT / "data/working/issue19-full-major-evidence-workbench.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-full-major-evidence-workbench-summary.json"

DATA_STAGE = "issue19_full_major_evidence_workbench"
EXECUTION_REQUIRED_FIELDS = (
    "PDF原页；湖北官方系统/省招办计划；高校官网/章程；专业组边界；调剂范围；"
    "家庭接受度；三年投档稳定性"
)


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
        return 0


def join_flags(values):
    return "；".join(dict.fromkeys(value for value in values if value))


def by_major_id(rows):
    return {row.get("专业行ID"): row for row in rows if row.get("专业行ID")}


def source_status(v3_row, school_row):
    if v3_row and v3_row.get("官网证据匹配状态"):
        return v3_row.get("官网证据匹配状态")
    if school_row and school_row.get("官网来源状态"):
        return school_row.get("官网来源状态")
    return "not_yet_school_source_searched_in_full_workbench"


def evidence_markers(priority_row, v3_row, school_row, d0_row):
    markers = []
    if priority_row:
        markers.append("已纳入优先整组逐专业证据工作台")
    if v3_row:
        markers.append("命中候选V3保真总账")
    if school_row:
        markers.append("命中B0/B1学校官网来源队列")
    if d0_row:
        markers.append("命中D0原页OCR证据")
    if v3_row and v3_row.get("B0B1计划冲突来源明细ID"):
        markers.append("B0/B1计划数冲突")
    if v3_row and v3_row.get("B0B1未匹配专业来源明细ID"):
        markers.append("B0/B1官网未匹配专业")
    return join_flags(markers) or "暂无可复用辅证"


def gaps(row, priority_row, v3_row, school_row):
    items = [
        "PDF原页人工核验",
        "湖北官方系统/省招办计划",
        "高校官网/招生章程",
        "家庭逐专业接受度",
        "同组调剂结论",
        "三年投档稳定性",
    ]
    if not row.get("专业计划数OCR候选"):
        items.append("专业计划数缺失")
    if not row.get("学费OCR候选"):
        items.append("学费缺失")
    if not row.get("再选科目OCR候选"):
        items.append("再选科目缺失")
    if not school_row:
        items.append("高校官网湖北2026计划源未检索到本工作台")
    if not priority_row:
        items.append("未进入当前优先整组核验包，需按全量队列继续推进")
    if v3_row and v3_row.get("B0B1计划冲突来源明细ID"):
        items.append("计划数冲突需回看原页")
    if v3_row and v3_row.get("B0B1未匹配专业来源明细ID"):
        items.append("官网未匹配专业需补源")
    return join_flags(items)


def full_execution_priority(row, priority_row, priority_evidence_row, v3_row, school_row, d0_row):
    if priority_evidence_row:
        return priority_evidence_row.get("证据执行优先级", ""), priority_evidence_row.get("证据执行排序", "")

    batch = row.get("逐专业核验批次", "")
    risk = row.get("风险阻断等级", "")
    family = row.get("机器专业接受度初判", "")
    group_judge = row.get("组机器家庭匹配初判", "")
    group_adjust = row.get("组调剂初判", "")
    official_status = source_status(v3_row, school_row)

    if d0_row or batch.startswith("A0") or risk.startswith("F0"):
        return "F0-非优先包PDF原页/结构阻断先核", "10"
    if official_status not in {"", "not_yet_school_source_searched_in_full_workbench"}:
        return "F1-非优先包已有官网辅证先交叉", "11"
    if (
        batch.startswith(("A5", "A6", "A7", "A8"))
        or not row.get("专业计划数OCR候选")
        or not row.get("学费OCR候选")
        or not row.get("再选科目OCR候选")
    ):
        return "F2-非优先包计划学费选科字段补证", "12"
    if (
        batch.startswith(("A3", "A4"))
        or "默认不能接受" in family
        or "默认不进主方案" in group_judge
        or "调剂风险" in group_adjust
    ):
        return "F3-非优先包家庭底线/调剂风险先核", "13"
    if batch.startswith("A9") or risk.startswith("F3"):
        return "F4-非优先包低风险抽检但非最终", "14"
    return "F5-非优先包普通待补证", "15"


def historical_line_text(rows_by_year, group_code):
    parts = []
    for year in ["2023", "2024", "2025"]:
        row = rows_by_year[year].get(group_code, {})
        if row:
            parts.append(
                f"{year}:{row.get('score', '')}/{row.get('req', '')}/{row.get('name', '')}"
            )
    return "；".join(parts)


def historical_status(rows_by_year, group_code):
    hit_years = [year for year, rows in rows_by_year.items() if group_code in rows]
    if len(hit_years) >= 2:
        return f"同代码{len(hit_years)}年命中，仅作稳定性线索"
    if len(hit_years) == 1:
        return "同代码1年命中，需重点核组号变化"
    return "同代码三年未命中或组号变化，需人工判断历史参照"


def next_action(priority, priority_row):
    if priority.startswith("E0") or priority.startswith("F0"):
        return "先回看PDF原页确认院校专业组边界、专业行切分、专业代号、计划数、学费和再选科目；结构阻断行不得进入候选排序。"
    if priority.startswith("E1"):
        return "历史候选或样本学校先补齐PDF原页、湖北官方系统和高校官网/章程三方证据，再进入家庭接受度判断。"
    if priority.startswith("E2"):
        return "数字媒体技术相关组先核完整专业组，确认同组是否存在不能接受专业，再形成调剂待核结论。"
    if priority.startswith("E3") or priority.startswith("F1"):
        return "已有高校官网辅证时，逐字段和第19期原页、湖北官方系统核对；官网证据只能辅助，不能替代省招办计划。"
    if priority.startswith("E4") or priority.startswith("F2"):
        return "优先补计划数、学费、再选科目和特殊备注；字段空值只代表OCR缺失，不代表不限或无费用。"
    if priority.startswith("E5") or priority.startswith("F3"):
        return "先做同组所有专业的家庭接受度标注，存在不能接受专业时不得默认服从调剂。"
    if priority.startswith("F4"):
        return "低风险行仍需抽检PDF原页和官方系统；当前只能作为底座完整性覆盖，不能直接用于最终填报。"
    if priority_row:
        return "按优先整组工作台继续推进三方证据闭环。"
    return "按PDF页码和学校聚合推进，补齐三方证据后再判断是否纳入下一轮人工复核清单。"


def main():
    full_rows = read_csv(FULL_MAJOR_VERIFICATION_BATCHES)
    full_fidelity_rows = read_csv(FULL_MAJOR_FIDELITY_LEDGER)
    family_rows = read_csv(FAMILY_MAJOR_DETAIL)
    page_rows = read_csv(PAGE_FIDELITY_QUEUE)
    priority_pack_rows = read_csv(PRIORITY_GROUP_MAJOR_PACK)
    priority_evidence_rows = read_csv(PRIORITY_MAJOR_EVIDENCE_WORKBENCH)
    v3_rows = read_csv(V3_FIDELITY_LEDGER)
    school_rows = read_csv(B0_B1_SCHOOL_SOURCE_QUEUE)
    d0_rows = read_csv(D0_PDF_EVIDENCE)
    toudang_rows_by_year = {
        "2023": {row.get("code"): row for row in read_csv(TOUDANG_2023)},
        "2024": {row.get("code"): row for row in read_csv(TOUDANG_2024)},
        "2025": {row.get("code"): row for row in read_csv(TOUDANG_2025)},
    }

    full_fidelity_by_major_id = by_major_id(full_fidelity_rows)
    family_by_major_id = by_major_id(family_rows)
    priority_pack_by_major_id = by_major_id(priority_pack_rows)
    priority_evidence_by_major_id = by_major_id(priority_evidence_rows)
    v3_by_major_line_id = by_major_id(v3_rows)
    page_by_queue_id = {row.get("页级保真队列ID"): row for row in page_rows if row.get("页级保真队列ID")}
    school_by_code = {row.get("院校代码"): row for row in school_rows if row.get("院校代码")}
    d0_by_group_code = {row.get("2026院校专业组代码"): row for row in d0_rows if row.get("2026院校专业组代码")}

    output_rows = []
    for row in full_rows:
        major_id = row.get("专业行ID", "")
        group_code = row.get("院校专业组代码OCR规范化", "")
        full_fidelity_row = full_fidelity_by_major_id.get(major_id, {})
        family_row = family_by_major_id.get(major_id, {})
        priority_row = priority_pack_by_major_id.get(major_id, {})
        priority_evidence_row = priority_evidence_by_major_id.get(major_id, {})
        v3_row = v3_by_major_line_id.get(major_id, {})
        page_row = page_by_queue_id.get(row.get("页级保真队列ID"), {})
        school_row = school_by_code.get(row.get("院校代码"), {})
        d0_row = d0_by_group_code.get(group_code, {})
        priority, order = full_execution_priority(
            row,
            priority_row,
            priority_evidence_row,
            v3_row,
            school_row,
            d0_row,
        )
        official_status = source_status(v3_row, school_row)
        output_rows.append(
            {
                "全量证据工作台ID": stable_id(
                    "FULLEVID",
                    [row.get("来源PDF_SHA256", ""), major_id],
                ),
                "来源全量逐专业核验批次表": "data/working/issue19-full-major-verification-batches.csv",
                "来源全量逐专业保真总账": "data/working/issue19-full-major-field-fidelity-ledger.csv",
                "来源家庭底线逐专业表": "data/working/issue19-family-fit-major-detail.csv",
                "来源页级保真复核队列": "data/working/issue19-page-fidelity-review-queue.csv",
                "来源优先整组核验包": "data/working/issue19-priority-group-major-review-pack.csv",
                "来源优先逐专业证据工作台": "data/working/issue19-priority-major-evidence-workbench.csv",
                "来源候选V3保真总账": "data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv",
                "来源B0B1学校官网来源队列": "data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv",
                "来源D0原页OCR证据表": "data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv",
                "来源期号": row.get("来源期号", ""),
                "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
                "数据阶段": DATA_STAGE,
                "主表粒度": "逐专业招生明细",
                "最终可用": "false",
                "核验状态": "pending_full_major_evidence_execution",
                "是否可进入最终专业列表": "false",
                "可进入下一阶段": "false",
                "是否在优先整组核验包": "true" if priority_row else "false",
                "来源优先整组核验明细ID": priority_row.get("优先整组核验明细ID", ""),
                "来源优先证据工作台ID": priority_evidence_row.get("证据执行工作台ID", ""),
                "全量证据执行优先级": priority,
                "全量证据执行排序": order,
                "已有辅证标记": evidence_markers(priority_evidence_row, v3_row, school_row, d0_row),
                "证据缺口": gaps(row, priority_evidence_row, v3_row, school_row),
                "执行必须核验字段": EXECUTION_REQUIRED_FIELDS,
                "PDF原页证据状态": "has_page_hash_pending_manual_pdf_review",
                "D0原页OCR证据状态": d0_row.get("PDF原页OCR核验结论", "not_d0_group"),
                "湖北官方系统证据状态": "pending_hubei_official_plan_or_platform_review",
                "高校官网/章程辅证状态": official_status,
                "PDF字段核验状态": row.get("PDF字段核验状态", ""),
                "湖北官方系统字段核验状态": row.get("湖北官方系统字段核验状态", ""),
                "高校官网/章程字段核验状态": row.get("高校官网/章程字段核验状态", ""),
                "家庭接受度核验状态": row.get("家庭接受度核验状态", ""),
                "调剂影响初判": family_row.get("调剂影响初判", full_fidelity_row.get("调剂影响初判", "")),
                "调剂影响等级": row.get("调剂影响等级", full_fidelity_row.get("调剂影响等级", "")),
                "组机器家庭匹配初判": row.get("组机器家庭匹配初判", full_fidelity_row.get("组机器家庭匹配初判", "")),
                "组调剂初判": row.get("组调剂初判", full_fidelity_row.get("组调剂初判", "")),
                "页级保真队列ID": row.get("页级保真队列ID", ""),
                "页级复核优先级": page_row.get("页面复核优先级", ""),
                "页级阻断等级": page_row.get("页面阻断等级", ""),
                "页级OCR平均置信度": page_row.get("OCR平均置信度", ""),
                "页级OCR_QC_P0数": page_row.get("OCR_QC_P0数", ""),
                "页级OCR_QC_P1数": page_row.get("OCR_QC_P1数", ""),
                "三年投档线索": historical_line_text(toudang_rows_by_year, group_code),
                "三年投档稳定性状态": historical_status(toudang_rows_by_year, group_code),
                "高校官网URL": school_row.get("官网URL", ""),
                "高校官网可核字段": school_row.get("可核字段", ""),
                "高校官网局限性": school_row.get("局限性", ""),
                "B0B1计划冲突来源明细ID": v3_row.get("B0B1计划冲突来源明细ID", ""),
                "B0B1未匹配专业来源明细ID": v3_row.get("B0B1未匹配专业来源明细ID", ""),
                "最佳官网专业名称": v3_row.get("最佳官网专业名称", ""),
                "最佳官网计划数": v3_row.get("最佳官网计划数", ""),
                "最佳官网学费": v3_row.get("最佳官网学费", ""),
                "计划数核验状态": v3_row.get("计划数核验状态", "pending_original_pdf_and_hubei_official_review"),
                "专业行ID": major_id,
                "专业组出现ID": row.get("专业组出现ID", ""),
                "院校代码": row.get("院校代码", ""),
                "院校名称OCR": row.get("院校名称OCR", ""),
                "院校专业组代码OCR规范化": group_code,
                "来源页码": row.get("来源页码", ""),
                "版面列": row.get("版面列", ""),
                "专业组内专业序号": row.get("专业组内专业序号", ""),
                "专业代号OCR": row.get("专业代号OCR", ""),
                "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
                "再选科目OCR候选": row.get("再选科目OCR候选", ""),
                "专业计划数OCR候选": row.get("专业计划数OCR候选", ""),
                "学费OCR候选": row.get("学费OCR候选", ""),
                "整组核验优先级": priority_row.get("整组核验优先级", ""),
                "整组入选原因": priority_row.get("整组入选原因", ""),
                "整组调剂机器风险": priority_row.get("整组调剂机器风险", ""),
                "同组真实招生明细数": row.get("同组真实招生明细数", full_fidelity_row.get("同组真实招生明细数", "")),
                "同组偏好专业数": row.get("同组偏好专业数", full_fidelity_row.get("同组偏好专业数", "")),
                "同组医学护理排除专业数": row.get("同组医学护理排除专业数", full_fidelity_row.get("同组医学护理排除专业数", "")),
                "同组高收费或超预算专业数": row.get("同组高收费或超预算专业数", full_fidelity_row.get("同组高收费或超预算专业数", "")),
                "同组特殊限制待核专业数": row.get("同组特殊限制待核专业数", full_fidelity_row.get("同组特殊限制待核专业数", "")),
                "逐专业核验批次": row.get("逐专业核验批次", ""),
                "批次触发原因": row.get("批次触发原因", ""),
                "全量保真复核优先级": row.get("全量保真复核优先级", ""),
                "风险阻断等级": row.get("风险阻断等级", ""),
                "高风险字段集合": row.get("高风险字段集合", ""),
                "风险触发规则": row.get("风险触发规则", ""),
                "专业偏好方向": row.get("专业偏好方向", family_row.get("专业偏好方向", "")),
                "专业风险类型": row.get("专业风险类型", ""),
                "机器专业接受度初判": row.get("机器专业接受度初判", ""),
                "机器阻断或待核原因": row.get("机器阻断或待核原因", ""),
                "必须核验字段": row.get("必须核验字段", ""),
                "下一步": next_action(priority, priority_row),
            }
        )

    fields = [
        "全量证据工作台ID",
        "来源全量逐专业核验批次表",
        "来源全量逐专业保真总账",
        "来源家庭底线逐专业表",
        "来源页级保真复核队列",
        "来源优先整组核验包",
        "来源优先逐专业证据工作台",
        "来源候选V3保真总账",
        "来源B0B1学校官网来源队列",
        "来源D0原页OCR证据表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "核验状态",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "是否在优先整组核验包",
        "来源优先整组核验明细ID",
        "来源优先证据工作台ID",
        "全量证据执行优先级",
        "全量证据执行排序",
        "已有辅证标记",
        "证据缺口",
        "执行必须核验字段",
        "PDF原页证据状态",
        "D0原页OCR证据状态",
        "湖北官方系统证据状态",
        "高校官网/章程辅证状态",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "家庭接受度核验状态",
        "调剂影响初判",
        "调剂影响等级",
        "组机器家庭匹配初判",
        "组调剂初判",
        "页级保真队列ID",
        "页级复核优先级",
        "页级阻断等级",
        "页级OCR平均置信度",
        "页级OCR_QC_P0数",
        "页级OCR_QC_P1数",
        "三年投档线索",
        "三年投档稳定性状态",
        "高校官网URL",
        "高校官网可核字段",
        "高校官网局限性",
        "B0B1计划冲突来源明细ID",
        "B0B1未匹配专业来源明细ID",
        "最佳官网专业名称",
        "最佳官网计划数",
        "最佳官网学费",
        "计划数核验状态",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "整组核验优先级",
        "整组入选原因",
        "整组调剂机器风险",
        "同组真实招生明细数",
        "同组偏好专业数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "逐专业核验批次",
        "批次触发原因",
        "全量保真复核优先级",
        "风险阻断等级",
        "高风险字段集合",
        "风险触发规则",
        "专业偏好方向",
        "专业风险类型",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "必须核验字段",
        "下一步",
    ]
    write_csv(OUTPUT, output_rows, fields)

    priority_counter = Counter(row["全量证据执行优先级"] for row in output_rows)
    official_source_status_counter = Counter(row["高校官网/章程辅证状态"] for row in output_rows)
    historical_status_counter = Counter(row["三年投档稳定性状态"] for row in output_rows)
    marker_counter = Counter()
    for row in output_rows:
        for marker in row["已有辅证标记"].split("；"):
            if marker:
                marker_counter[marker] += 1

    summary = {
        "status": "issue19_full_major_evidence_workbench_not_final",
        "generated_by": "build_issue19_full_major_evidence_workbench.py",
        "source_full_major_verification_batches": "data/working/issue19-full-major-verification-batches.csv",
        "source_full_major_fidelity_ledger": "data/working/issue19-full-major-field-fidelity-ledger.csv",
        "source_family_major_detail": "data/working/issue19-family-fit-major-detail.csv",
        "source_page_fidelity_review_queue": "data/working/issue19-page-fidelity-review-queue.csv",
        "source_priority_group_major_review_pack": "data/working/issue19-priority-group-major-review-pack.csv",
        "source_priority_major_evidence_workbench": "data/working/issue19-priority-major-evidence-workbench.csv",
        "source_candidate_v3_major_fidelity_ledger": "data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv",
        "source_b0_b1_school_official_source_queue": "data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv",
        "source_d0_pdf_page_evidence": "data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv",
        "output_table": "data/working/issue19-full-major-evidence-workbench.csv",
        "row_count": len(output_rows),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in output_rows}),
        "unique_school_count": len({row["院校代码"] for row in output_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in output_rows}),
        "priority_pack_row_count": sum(row["是否在优先整组核验包"] == "true" for row in output_rows),
        "non_priority_row_count": sum(row["是否在优先整组核验包"] == "false" for row in output_rows),
        "candidate_v3_fidelity_hit_row_count": sum("命中候选V3保真总账" in row["已有辅证标记"] for row in output_rows),
        "b0_b1_school_source_hit_row_count": sum("命中B0/B1学校官网来源队列" in row["已有辅证标记"] for row in output_rows),
        "d0_pdf_evidence_hit_row_count": sum("命中D0原页OCR证据" in row["已有辅证标记"] for row in output_rows),
        "b0_b1_plan_conflict_row_count": sum(bool(row["B0B1计划冲突来源明细ID"]) for row in output_rows),
        "b0_b1_unmatched_major_row_count": sum(bool(row["B0B1未匹配专业来源明细ID"]) for row in output_rows),
        "missing_plan_count_row_count": sum(not row["专业计划数OCR候选"] for row in output_rows),
        "missing_tuition_row_count": sum(not row["学费OCR候选"] for row in output_rows),
        "missing_subject_row_count": sum(not row["再选科目OCR候选"] for row in output_rows),
        "historical_exact_group_hit_row_count": sum(bool(row["三年投档线索"]) for row in output_rows),
        "auto_final_list_allowed_count": sum(row["是否可进入最终专业列表"] == "true" for row in output_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "priority_counts": dict(priority_counter),
        "official_source_status_counts": dict(official_source_status_counter),
        "historical_status_counts": dict(historical_status_counter),
        "evidence_marker_counts": dict(marker_counter),
        "notes": [
            "本表覆盖第19期本科普通批（下）OCR结构化后的全部逐专业招生明细。",
            "本表仍是一行一个招生专业明细，不是学校或院校专业组汇总表。",
            "优先整组工作台只是本表中的优先级字段和证据来源，不再作为唯一候选主表。",
            "所有行仍需PDF原页、湖北官方系统/省招办计划、高校官网/章程、家庭接受度和调剂结论闭环。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
