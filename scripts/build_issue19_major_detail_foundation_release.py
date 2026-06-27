#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FULL_EVIDENCE = ROOT / "data/working/issue19-full-major-evidence-workbench.csv"
P0_REVIEW = ROOT / "data/working/issue19-p0-evidence-review-worklist.csv"
FIELD_GAPS = ROOT / "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv"
HUBEI_OFFICIAL = ROOT / "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"
B0_B1_DIFF = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
PAGE_FIDELITY = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"

OUTPUT = ROOT / "data/working/issue19-major-detail-foundation-release.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-major-detail-foundation-release-summary.json"

DATA_STAGE = "issue19_major_detail_foundation_release"


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


def join_unique(values):
    seen = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.append(text)
    return "；".join(seen)


def short_text(value, limit=120):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def build_indexes():
    full_rows = read_csv(FULL_EVIDENCE)
    p0_rows = read_csv(P0_REVIEW)
    field_gap_rows = read_csv(FIELD_GAPS)
    hubei_rows = read_csv(HUBEI_OFFICIAL)
    b0_b1_rows = read_csv(B0_B1_DIFF)
    manifest_rows = read_csv(PAGE_MANIFEST)
    page_rows = read_csv(PAGE_FIDELITY)

    p0_by_major = defaultdict(list)
    for row in p0_rows:
        p0_by_major[row.get("专业行ID", "")].append(row)

    field_gaps_by_major = defaultdict(list)
    for row in field_gap_rows:
        field_gaps_by_major[row.get("专业行ID", "")].append(row)

    b0_b1_by_major = defaultdict(list)
    for row in b0_b1_rows:
        b0_b1_by_major[row.get("专业行ID", "")].append(row)

    return {
        "full_rows": full_rows,
        "p0_rows": p0_rows,
        "field_gap_rows": field_gap_rows,
        "hubei_rows": hubei_rows,
        "b0_b1_rows": b0_b1_rows,
        "p0_by_major": p0_by_major,
        "field_gaps_by_major": field_gaps_by_major,
        "hubei_by_major": {row.get("专业行ID", ""): row for row in hubei_rows},
        "b0_b1_by_major": b0_b1_by_major,
        "manifest_by_page": {row.get("PDF页码", ""): row for row in manifest_rows},
        "page_by_page": {row.get("PDF页码", ""): row for row in page_rows},
    }


def foundation_gate(full_row, p0_rows, field_gap_rows, b0_b1_rows):
    if p0_rows:
        return "G0-P0证据先核"
    if field_gap_rows:
        return "G1-字段缺口先补"
    if b0_b1_rows:
        return "G2-官网辅证先交叉"
    if full_row.get("全量证据执行优先级", "").startswith(("F4", "F5")):
        return "G4-低风险抽检仍待三方核验"
    return "G3-常规三方证据闭环"


def next_action(gate, full_row, field_gap_rows, b0_b1_rows):
    if gate.startswith("G0"):
        return "先处理P0复核清单：逐专业回看PDF原页，并补湖北官方系统、省招办计划或高校官网/章程证据。"
    if gate.startswith("G1"):
        fields = join_unique(row.get("字段名") for row in field_gap_rows)
        return f"先补字段缺口：{fields}；空值只代表OCR未稳，不能解释为不限、无计划或无学费。"
    if gate.startswith("G2"):
        conflicts = join_unique(row.get("差异字段集合") for row in b0_b1_rows)
        detail = f"；当前差异字段：{conflicts}" if conflicts else ""
        return f"已有官网辅证线索，先与PDF原页和湖北官方系统逐字段交叉{detail}。"
    if gate.startswith("G4"):
        return "机器暂未触发高优先风险，但仍需抽检PDF原页、湖北官方系统、高校官网/章程、家庭接受度和调剂结论。"
    return full_row.get("下一步") or "按全量证据工作台推进PDF原页、湖北官方系统、高校官网/章程、家庭接受度和调剂结论闭环。"


def block_reason(gate, full_row, p0_rows, field_gap_rows, b0_b1_rows):
    reasons = [
        "PDF原页、湖北官方系统/省招办计划、高校官网/章程、家庭接受度和同组调剂结论尚未全部闭环",
        "湖北官方平台字段核验状态仍为pending_hubei_official_plan_review",
    ]
    if p0_rows:
        reasons.append(f"P0复核任务未完成：{join_unique(row.get('证据项') for row in p0_rows)}")
    if field_gap_rows:
        reasons.append(f"字段缺口未补：{join_unique(row.get('字段名') for row in field_gap_rows)}")
    if b0_b1_rows:
        reasons.append("高校官网/章程辅证仍需和PDF原页、湖北官方系统逐字段交叉")
    if full_row.get("风险阻断等级"):
        reasons.append(f"机器风险等级：{full_row.get('风险阻断等级')}")
    if gate.startswith("G4"):
        reasons.append("机器低风险只表示抽检优先级低，不表示可直接排序")
    return "；".join(reasons)


def build_release_table(indexes):
    rows = []
    for full_row in indexes["full_rows"]:
        major_id = full_row.get("专业行ID", "")
        p0_rows = indexes["p0_by_major"].get(major_id, [])
        field_gap_rows = indexes["field_gaps_by_major"].get(major_id, [])
        hubei_row = indexes["hubei_by_major"].get(major_id, {})
        b0_b1_rows = indexes["b0_b1_by_major"].get(major_id, [])
        manifest_row = indexes["manifest_by_page"].get(full_row.get("来源页码", ""), {})
        page_row = indexes["page_by_page"].get(full_row.get("来源页码", ""), {})
        field_gap_names = join_unique(row.get("字段名") for row in field_gap_rows)
        p0_items = join_unique(row.get("证据项") for row in p0_rows)
        b0_b1_statuses = join_unique(row.get("官网来源状态") for row in b0_b1_rows)
        b0_b1_match = join_unique(row.get("官网证据匹配状态") for row in b0_b1_rows)
        b0_b1_plan_status = join_unique(row.get("计划数核验状态") for row in b0_b1_rows)
        b0_b1_diff_fields = join_unique(row.get("差异字段集合") for row in b0_b1_rows)
        gate = foundation_gate(full_row, p0_rows, field_gap_rows, b0_b1_rows)

        rows.append({
            "底座发布明细ID": stable_id("BASEMAJOR", [major_id]),
            "来源期号": full_row.get("来源期号", ""),
            "来源PDF_SHA256": full_row.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "底座发布状态": "公开底座待核验",
            "核验状态": "pending_foundation_release_verification",
            "最终可用": "false",
            "是否可进入最终专业列表": "false",
            "可进入下一阶段": "false",
            "最终志愿排序门禁": "阻断-待证据闭环",
            "不得进入原因": block_reason(gate, full_row, p0_rows, field_gap_rows, b0_b1_rows),
            "底座使用边界": "仅用于检索、复核、补证和后续筛选预处理；不得直接用于冲稳保排序。",
            "底座保真门禁": gate,
            "专业行ID": major_id,
            "专业组出现ID": full_row.get("专业组出现ID", ""),
            "院校代码": full_row.get("院校代码", ""),
            "院校名称OCR": full_row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": full_row.get("院校专业组代码OCR规范化", ""),
            "来源页码": full_row.get("来源页码", ""),
            "版面列": full_row.get("版面列", ""),
            "专业组内专业序号": full_row.get("专业组内专业序号", ""),
            "专业代号OCR": full_row.get("专业代号OCR", ""),
            "专业名称及备注OCR": full_row.get("专业名称及备注OCR", ""),
            "专业名称及备注短摘": short_text(full_row.get("专业名称及备注OCR")),
            "是否真实招生明细": "true" if full_row.get("专业名称及备注OCR", "").strip() else "false",
            "是否0明细占位": "false",
            "再选科目OCR候选": full_row.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": full_row.get("专业计划数OCR候选", ""),
            "学费OCR候选": full_row.get("学费OCR候选", ""),
            "再选科目人工确认": "",
            "专业计划数人工确认": "",
            "学费人工确认": "",
            "字段缺口数": str(len(field_gap_rows)),
            "字段缺口字段": field_gap_names,
            "再选科目字段缺口": "true" if "再选科目" in field_gap_names else "false",
            "专业计划数字段缺口": "true" if "专业计划数" in field_gap_names else "false",
            "学费字段缺口": "true" if "学费" in field_gap_names else "false",
            "P0复核任务数": str(len(p0_rows)),
            "P0证据项": p0_items,
            "湖北官方核验包任务ID": hubei_row.get("湖北官方核验包任务ID", ""),
            "湖北官方平台匹配状态": hubei_row.get("平台匹配状态", ""),
            "湖北官方平台字段核验状态": hubei_row.get("平台字段核验状态", ""),
            "湖北官方字段差异集合": hubei_row.get("字段差异集合", ""),
            "湖北官方系统证据状态": full_row.get("湖北官方系统证据状态", ""),
            "湖北官方系统字段核验状态": full_row.get("湖北官方系统字段核验状态", ""),
            "高校官网/章程辅证状态": full_row.get("高校官网/章程辅证状态", ""),
            "高校官网来源状态": b0_b1_statuses or full_row.get("高校官网/章程辅证状态", ""),
            "高校官网证据匹配状态": b0_b1_match,
            "高校官网计划数核验状态": b0_b1_plan_status or full_row.get("计划数核验状态", ""),
            "高校官网差异字段集合": b0_b1_diff_fields,
            "B0B1官网差异任务数": str(len(b0_b1_rows)),
            "PDF原页证据状态": full_row.get("PDF原页证据状态", ""),
            "PDF字段核验状态": full_row.get("PDF字段核验状态", ""),
            "私有页图证据编号": manifest_row.get("私有页图证据编号", ""),
            "私有页图SHA256": manifest_row.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": manifest_row.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": manifest_row.get("私有OCR文本SHA256", ""),
            "页级保真队列ID": full_row.get("页级保真队列ID", ""),
            "页级复核优先级": full_row.get("页级复核优先级", "") or page_row.get("页面复核优先级", ""),
            "页级阻断等级": full_row.get("页级阻断等级", "") or page_row.get("页面阻断等级", ""),
            "页级OCR平均置信度": full_row.get("页级OCR平均置信度", "") or manifest_row.get("OCR平均置信度", ""),
            "页级OCR_QC_P0数": full_row.get("页级OCR_QC_P0数", "") or manifest_row.get("OCR_QC_P0数", ""),
            "页级OCR_QC_P1数": full_row.get("页级OCR_QC_P1数", "") or manifest_row.get("OCR_QC_P1数", ""),
            "家庭接受度核验状态": full_row.get("家庭接受度核验状态", ""),
            "家庭接受度结论": "pending_family_acceptance_review",
            "机器专业接受度初判": full_row.get("机器专业接受度初判", ""),
            "机器阻断或待核原因": full_row.get("机器阻断或待核原因", ""),
            "调剂影响初判": full_row.get("调剂影响初判", ""),
            "调剂影响等级": full_row.get("调剂影响等级", ""),
            "同组调剂结论": "pending_transfer_decision",
            "组机器家庭匹配初判": full_row.get("组机器家庭匹配初判", ""),
            "组调剂初判": full_row.get("组调剂初判", ""),
            "同组真实招生明细数": full_row.get("同组真实招生明细数", ""),
            "同组偏好专业数": full_row.get("同组偏好专业数", ""),
            "同组医学护理排除专业数": full_row.get("同组医学护理排除专业数", ""),
            "同组高收费或超预算专业数": full_row.get("同组高收费或超预算专业数", ""),
            "同组特殊限制待核专业数": full_row.get("同组特殊限制待核专业数", ""),
            "专业偏好方向": full_row.get("专业偏好方向", ""),
            "专业风险类型": full_row.get("专业风险类型", ""),
            "全量证据执行优先级": full_row.get("全量证据执行优先级", ""),
            "全量保真复核优先级": full_row.get("全量保真复核优先级", ""),
            "风险阻断等级": full_row.get("风险阻断等级", ""),
            "高风险字段集合": full_row.get("高风险字段集合", ""),
            "风险触发规则": full_row.get("风险触发规则", ""),
            "证据缺口": full_row.get("证据缺口", ""),
            "执行必须核验字段": full_row.get("执行必须核验字段", ""),
            "三年投档线索": full_row.get("三年投档线索", ""),
            "三年投档稳定性状态": full_row.get("三年投档稳定性状态", ""),
            "下一步": next_action(gate, full_row, field_gap_rows, b0_b1_rows),
        })

    rows.sort(key=lambda row: (
        as_int(row.get("来源页码")),
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        as_int(row.get("专业组内专业序号")),
        row.get("专业代号OCR", ""),
    ))
    return rows


def write_summary(rows, indexes):
    field_gap_counter = Counter()
    for row in indexes["field_gap_rows"]:
        field_gap_counter[row.get("字段名", "")] += 1

    summary = {
        "status": "issue19_major_detail_foundation_release_not_final",
        "generated_by": "build_issue19_major_detail_foundation_release.py",
        "source_full_major_evidence_workbench": "data/working/issue19-full-major-evidence-workbench.csv",
        "source_p0_review_worklist": "data/working/issue19-p0-evidence-review-worklist.csv",
        "source_field_gap_matrix": "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv",
        "source_hubei_official_packets": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
        "source_b0_b1_diff_ledger": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
        "source_page_manifest": "data/working/issue19-page-manifest.csv",
        "source_page_fidelity_review_queue": "data/working/issue19-page-fidelity-review-queue.csv",
        "output_table": "data/working/issue19-major-detail-foundation-release.csv",
        "row_count": len(rows),
        "unique_release_id_count": len({row["底座发布明细ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in rows}),
        "unique_school_count": len({row["院校代码"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "p0_task_row_count": len(indexes["p0_rows"]),
        "p0_major_line_count": len(indexes["p0_by_major"]),
        "field_gap_task_row_count": len(indexes["field_gap_rows"]),
        "field_gap_major_line_count": len(indexes["field_gaps_by_major"]),
        "field_gap_field_counts": dict(field_gap_counter),
        "hubei_official_packet_row_count": len(indexes["hubei_rows"]),
        "hubei_official_major_line_count": len(indexes["hubei_by_major"]),
        "b0_b1_diff_row_count": len(indexes["b0_b1_rows"]),
        "b0_b1_diff_major_line_count": len(indexes["b0_b1_by_major"]),
        "release_gate_counts": dict(Counter(row["底座保真门禁"] for row in rows)),
        "official_platform_status_counts": dict(Counter(row["湖北官方平台字段核验状态"] for row in rows)),
        "missing_subject_count": sum(not row["再选科目OCR候选"] for row in rows),
        "missing_plan_count": sum(not row["专业计划数OCR候选"] for row in rows),
        "missing_tuition_count": sum(not row["学费OCR候选"] for row in rows),
        "real_major_detail_count": sum(row["是否真实招生明细"] == "true" for row in rows),
        "zero_detail_placeholder_count": sum(row["是否0明细占位"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "final_major_list_candidate_count": sum(row["是否可进入最终专业列表"] == "true" for row in rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "final_sort_gate_open_count": sum(row["最终志愿排序门禁"] != "阻断-待证据闭环" for row in rows),
        "notes": [
            "本表是一行一个招生专业明细的公开底座入口，用于检索、复核、补证和后续筛选预处理。",
            "本表汇总P0复核、P1字段缺口、湖北官方系统核验包、B0/B1官网差异和页级证据编号，但不保存私有页图、整页OCR文本、登录态或接口原文。",
            "所有行均保持最终可用=false、可进入下一阶段=false、最终志愿排序门禁=阻断-待证据闭环。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    indexes = build_indexes()
    rows = build_release_table(indexes)
    fields = [
        "底座发布明细ID",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "底座发布状态",
        "核验状态",
        "最终可用",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "最终志愿排序门禁",
        "不得进入原因",
        "底座使用边界",
        "底座保真门禁",
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
        "专业名称及备注短摘",
        "是否真实招生明细",
        "是否0明细占位",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "再选科目人工确认",
        "专业计划数人工确认",
        "学费人工确认",
        "字段缺口数",
        "字段缺口字段",
        "再选科目字段缺口",
        "专业计划数字段缺口",
        "学费字段缺口",
        "P0复核任务数",
        "P0证据项",
        "湖北官方核验包任务ID",
        "湖北官方平台匹配状态",
        "湖北官方平台字段核验状态",
        "湖北官方字段差异集合",
        "湖北官方系统证据状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程辅证状态",
        "高校官网来源状态",
        "高校官网证据匹配状态",
        "高校官网计划数核验状态",
        "高校官网差异字段集合",
        "B0B1官网差异任务数",
        "PDF原页证据状态",
        "PDF字段核验状态",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "页级保真队列ID",
        "页级复核优先级",
        "页级阻断等级",
        "页级OCR平均置信度",
        "页级OCR_QC_P0数",
        "页级OCR_QC_P1数",
        "家庭接受度核验状态",
        "家庭接受度结论",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "调剂影响初判",
        "调剂影响等级",
        "同组调剂结论",
        "组机器家庭匹配初判",
        "组调剂初判",
        "同组真实招生明细数",
        "同组偏好专业数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "专业偏好方向",
        "专业风险类型",
        "全量证据执行优先级",
        "全量保真复核优先级",
        "风险阻断等级",
        "高风险字段集合",
        "风险触发规则",
        "证据缺口",
        "执行必须核验字段",
        "三年投档线索",
        "三年投档稳定性状态",
        "下一步",
    ]
    write_csv(OUTPUT, rows, fields)
    write_summary(rows, indexes)
    print(f"写入 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
