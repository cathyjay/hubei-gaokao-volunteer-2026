#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FULL_FIDELITY = ROOT / "data/working/issue19-full-major-field-fidelity-ledger.csv"
PAGE_FIDELITY = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"

OUTPUT = ROOT / "data/working/issue19-full-major-verification-batches.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-full-major-verification-batches-summary.json"

DATA_STAGE = "issue19_full_major_verification_batches"


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


def split_flags(value):
    return [part for part in str(value or "").split("；") if part]


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def truthy(value):
    return str(value or "").strip() in {"true", "是", "1", "yes"}


def classify_batch(row):
    reasons = []
    priority = row.get("全量保真复核优先级", "")
    block = row.get("风险阻断等级", "")
    categories = set(split_flags(row.get("高风险字段集合")))
    rules = set(split_flags(row.get("风险触发规则")))

    if block.startswith("F0") or priority.startswith("P0"):
        reasons.append("阻断级结构/空专业名/串校串行风险")
        if "empty_major_name" in rules:
            reasons.append("空专业名")
        if "high_structure_anomaly" in rules:
            reasons.append("高严重结构异常")
        return "A0-阻断级结构先核", "00", "；".join(reasons)

    if truthy(row.get("候选池V1命中")) or truthy(row.get("样本学校命中")):
        if truthy(row.get("候选池V1命中")):
            reasons.append("第一版历史候选命中")
        if truthy(row.get("样本学校命中")):
            reasons.append("样本学校命中")
        return "A1-历史候选和样本先核", "01", "；".join(reasons)

    if row.get("专业偏好方向"):
        reasons.append(f"命中偏好方向：{row.get('专业偏好方向')}")
        return "A2-偏好专业逐专业先核", "02", "；".join(reasons)

    if "家庭底线" in categories or row.get("机器专业接受度初判", "").startswith("默认不能接受"):
        if "家庭底线" in categories:
            reasons.append("触发家庭底线字段")
        if row.get("机器专业接受度初判"):
            reasons.append(row.get("机器专业接受度初判"))
        return "A3-家庭底线和费用先核", "03", "；".join(reasons)

    if row.get("调剂影响等级", "").startswith("高") or row.get("组调剂初判", "").startswith("T1"):
        reasons.append(row.get("调剂影响等级") or row.get("组调剂初判"))
        return "A4-调剂风险先核", "04", "；".join(reasons)

    if priority.startswith("P1") or "计划数字段" in categories:
        reasons.append("计划数字段需保真")
        return "A5-计划数字段先核", "05", "；".join(reasons)

    if priority.startswith("P3") or "再选科目字段" in categories:
        reasons.append("再选科目/特殊限制需核")
        return "A6-选科和特殊限制先核", "06", "；".join(reasons)

    if priority.startswith("P2") or "学费字段" in categories:
        reasons.append("学费或费用字段需核")
        return "A7-学费字段先核", "07", "；".join(reasons)

    if block.startswith("F2"):
        reasons.append("待补证字段需核")
        return "A8-待补证字段核验", "08", "；".join(reasons)

    return "A9-低风险抽检但非最终", "09", "机器暂未触发高风险，仍需最终门禁"


def action_text(row, batch):
    core = ["PDF原页", "湖北官方系统/省招办计划", "高校官网/章程", "家庭接受度", "调剂结论"]
    if batch.startswith("A0"):
        return "先回看PDF原页核专业组边界、院校标题、专业行是否串校串组，再接官方系统和高校官网。"
    if batch.startswith("A1"):
        return "优先核历史候选或样本学校：PDF原页、官方系统、官网/章程、家庭接受度和调剂结论同步补齐。"
    if batch.startswith("A2"):
        return "优先核偏好专业：专业名称、计划数、学费、选科、校区/备注、组内可调剂专业全部确认。"
    if batch.startswith("A3"):
        return "核费用、医学护理、高收费、中外合作和家庭不能接受项；判断该专业组能否服从调剂。"
    if batch.startswith("A4"):
        return "核完整专业组内全部专业，确认是否存在不能接受专业以及服从调剂风险。"
    if batch.startswith("A5"):
        return "逐字段核计划数，重点排除OCR把学费、年份、专业代码误作计划数。"
    if batch.startswith("A6"):
        return "核再选科目、体检/色觉、语种、单科、校区和专项/定向等特殊限制。"
    if batch.startswith("A7"):
        return "核学费数字、收费单位、高收费/中外合作备注和预算上限。"
    if batch.startswith("A8"):
        return "补齐缺失字段证据后再判断是否能进入候选讨论。"
    return f"按抽检比例回看{core[0]}，并在进入候选前补齐{'、'.join(core[1:])}。"


def main():
    full_rows = read_csv(FULL_FIDELITY)
    page_rows = read_csv(PAGE_FIDELITY)
    page_by_number = {row.get("PDF页码"): row for row in page_rows}

    output_rows = []
    for row in full_rows:
        page = row.get("来源页码", "")
        page_row = page_by_number.get(page, {})
        batch, batch_order, reasons = classify_batch(row)
        output_rows.append(
            {
                "逐专业核验批次ID": stable_id(
                    "MAJVER",
                    [row.get("来源PDF_SHA256", ""), row.get("专业行ID", ""), batch],
                ),
                "来源全量逐专业保真总账": "data/working/issue19-full-major-field-fidelity-ledger.csv",
                "来源页级保真复核队列": "data/working/issue19-page-fidelity-review-queue.csv",
                "来源期号": row.get("来源期号", ""),
                "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
                "数据阶段": DATA_STAGE,
                "最终可用": "false",
                "核验状态": "pending_full_major_manual_verification_batch",
                "是否可进入最终专业列表": "false",
                "可进入下一阶段": "false",
                "专业行ID": row.get("专业行ID", ""),
                "专业组出现ID": row.get("专业组出现ID", ""),
                "院校代码": row.get("院校代码", ""),
                "院校名称OCR": row.get("院校名称OCR", ""),
                "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
                "专业组号OCR": row.get("专业组号OCR", ""),
                "来源页码": page,
                "版面列": row.get("版面列", ""),
                "专业组内专业序号": row.get("专业组内专业序号", ""),
                "专业代号OCR": row.get("专业代号OCR", ""),
                "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
                "再选科目OCR候选": row.get("再选科目OCR候选", ""),
                "专业计划数OCR候选": row.get("专业计划数OCR候选", ""),
                "专业计划数是否纯数字": row.get("专业计划数是否纯数字", ""),
                "学费OCR候选": row.get("学费OCR候选", ""),
                "学费是否纯数字": row.get("学费是否纯数字", ""),
                "预算上限元": row.get("预算上限元", ""),
                "页级保真队列ID": page_row.get("页级保真队列ID", ""),
                "私有页图证据编号": page_row.get("私有页图证据编号", ""),
                "私有页图SHA256": page_row.get("私有页图SHA256", ""),
                "私有OCR文本证据编号": page_row.get("私有OCR文本证据编号", ""),
                "私有OCR文本SHA256": page_row.get("私有OCR文本SHA256", ""),
                "页级复核优先级": page_row.get("页面复核优先级", ""),
                "页级阻断等级": page_row.get("页面阻断等级", ""),
                "全量保真复核优先级": row.get("全量保真复核优先级", ""),
                "风险阻断等级": row.get("风险阻断等级", ""),
                "高风险字段集合": row.get("高风险字段集合", ""),
                "风险触发规则": row.get("风险触发规则", ""),
                "批次排序": batch_order,
                "逐专业核验批次": batch,
                "批次触发原因": reasons,
                "核验动作": action_text(row, batch),
                "必须核验字段": row.get("必须核验字段", ""),
                "PDF字段核验状态": row.get("PDF字段核验状态", ""),
                "湖北官方系统字段核验状态": row.get("湖北官方系统字段核验状态", ""),
                "高校官网/章程字段核验状态": row.get("高校官网/章程字段核验状态", ""),
                "家庭接受度核验状态": row.get("家庭接受度核验状态", ""),
                "调剂影响等级": row.get("调剂影响等级", ""),
                "机器专业接受度初判": row.get("机器专业接受度初判", ""),
                "机器阻断或待核原因": row.get("机器阻断或待核原因", ""),
                "专业偏好方向": row.get("专业偏好方向", ""),
                "专业风险类型": row.get("专业风险类型", ""),
                "候选池V1命中": row.get("候选池V1命中", ""),
                "样本学校命中": row.get("样本学校命中", ""),
                "同组真实招生明细数": row.get("同组真实招生明细数", ""),
                "同组偏好专业数": row.get("同组偏好专业数", ""),
                "同组医学护理排除专业数": row.get("同组医学护理排除专业数", ""),
                "同组高收费或超预算专业数": row.get("同组高收费或超预算专业数", ""),
                "同组特殊限制待核专业数": row.get("同组特殊限制待核专业数", ""),
                "组机器家庭匹配初判": row.get("组机器家庭匹配初判", ""),
                "组调剂初判": row.get("组调剂初判", ""),
                "下一步": "按本批次顺序逐专业回看第19期PDF原页，并补齐湖北官方系统/省招办计划、高校官网/章程、家庭接受度和调剂结论。",
            }
        )

    batch_counts = Counter(row["逐专业核验批次"] for row in output_rows)
    block_counts = Counter(row["风险阻断等级"] for row in output_rows)
    page_priority_counts = Counter(row["页级复核优先级"] for row in output_rows)
    summary = {
        "status": "issue19_full_major_verification_batches_not_final",
        "generated_by": Path(__file__).name,
        "source_full_major_fidelity_ledger": "data/working/issue19-full-major-field-fidelity-ledger.csv",
        "source_page_fidelity_review_queue": "data/working/issue19-page-fidelity-review-queue.csv",
        "output_table": "data/working/issue19-full-major-verification-batches.csv",
        "row_count": len(output_rows),
        "source_full_major_row_count": len(full_rows),
        "source_page_count": len(page_rows),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in output_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in output_rows}),
        "batch_counts": dict(sorted(batch_counts.items())),
        "block_level_counts": dict(sorted(block_counts.items())),
        "page_priority_counts": dict(sorted(page_priority_counts.items())),
        "candidate_v1_hit_count": sum(row["候选池V1命中"] == "是" for row in output_rows),
        "sample_school_hit_count": sum(row["样本学校命中"] == "是" for row in output_rows),
        "preference_major_row_count": sum(bool(row["专业偏好方向"]) for row in output_rows),
        "auto_final_list_allowed_count": sum(row["是否可进入最终专业列表"] == "true" for row in output_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "notes": [
            "本表是一行一个招生专业的全量核验批次表，只安排逐专业人工核验顺序，不生成最终志愿结论。",
            "页级字段来自按页保真复核队列，用于定位PDF页图和OCR文本证据编号。",
            "所有专业仍需PDF原页、湖北官方系统/省招办计划、高校官网/章程、家庭接受度和调剂结论闭环。",
        ],
    }

    write_csv(OUTPUT, output_rows, list(output_rows[0].keys()))
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
