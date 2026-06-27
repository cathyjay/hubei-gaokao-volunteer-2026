#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIELD_CLUE_PUBLIC_AUDIT = (
    ROOT / "data/working/issue19-page-side-foundation-field-clue-public-audit.csv"
)
PRIVATE_FIELD_CLUE_DIR = (
    ROOT / "private/review-assets/issue19-page-side-foundation-field-clue-audit/tasks"
)
PRIVATE_OVERLAY_DIR = (
    ROOT / "private/review-assets/issue19-page-side-foundation-human-review-overlay/overlays"
)
PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-page-side-foundation-batch-sample-review"
)
PRIVATE_DETAIL_DIR = PRIVATE_OUTPUT_DIR / "details"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_page_side_foundation_batch_sample_review"


PUBLIC_FIELDS = [
    "页列底座样板公开审计ID",
    "来源页列底座字段线索公开审计",
    "来源私有字段线索模板",
    "来源私有人工复核Overlay",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动标记核验完成",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "批次总序",
    "批次ID",
    "批次名称",
    "批内页列序号",
    "页列全局风险总序",
    "页列底座核验批次行ID",
    "页列底座字段线索公开审计ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "综合风险优先级桶",
    "页列首要核验动作",
    "包内专业行数",
    "包内字段任务数",
    "样板字段任务数",
    "样板专业行覆盖数",
    "样板字段名分布",
    "样板阻断等级分布",
    "样板字段状态分布",
    "样板候选值集合非空任务数",
    "样板OCR候选非空任务数",
    "样板多值候选任务数",
    "样板疑似错位候选任务数",
    "样板需PDF原页核验任务数",
    "样板需湖北官方核验字段数",
    "样板需高校辅证字段数",
    "样板可自动写入正式Overlay字段数",
    "样板建议动作分布",
    "样板页列状态",
    "私有样板明细证据编号",
    "私有样板明细CSV_SHA256",
    "私有样板页列记录数",
    "私有样板批次记录数",
    "公开安全策略",
    "下一步",
]


PRIVATE_FIELDS = [
    "样板复核任务ID",
    "批次总序",
    "批次ID",
    "批次名称",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列底座核验批次行ID",
    "字段事实核验任务ID",
    "专业行ID",
    "字段事实闭环ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "字段名",
    "字段OCR候选",
    "字段候选值集合",
    "字段候选来源类型集合",
    "字段候选置信等级集合",
    "字段候选状态集合",
    "字段事实状态",
    "字段事实阻断等级",
    "字段事实缺口类型",
    "字段PDF核验状态",
    "字段湖北官方核验状态",
    "字段事实核验动作",
    "湖北官方核验包任务ID",
    "高校官网证据匹配状态",
    "B0B1官网证据任务数",
    "官网证据能否替代湖北官方计划",
    "专业起始行号",
    "专业窗口行号范围",
    "窗口坐标摘要",
    "窗口文本SHA256",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "样板候选可读性",
    "样板候选关系",
    "样板疑似错位",
    "样板建议动作",
    "可否自动写入正式Overlay",
    "写入阻断原因",
    "正式Overlay记录是否存在",
    "正式Overlay是否已有人工填写",
    "正式OverlayID",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]}"


def filled(value):
    return bool(str(value or "").strip())


def as_int(value, default=0):
    try:
        return int(str(value or "").strip())
    except (TypeError, ValueError):
        return default


def compact_counter(values):
    counter = Counter(value for value in values if filled(value))
    if not counter:
        return "无"
    return "；".join(f"{key}:{value}" for key, value in sorted(counter.items()))


def has_multi_value(value):
    text = str(value or "").strip()
    return any(sep in text for sep in ["；", ";", "/", "|", "、"]) if text else False


def looks_misaligned(row):
    field = row.get("字段名", "")
    candidate = str(row.get("字段OCR候选", "") or row.get("字段候选值集合", "")).strip()
    if not candidate:
        return False
    if field == "再选科目":
        return any(ch.isdigit() for ch in candidate) and not any(
            token in candidate for token in ["不限", "化学", "生物", "地理", "政治"]
        )
    if field in {"专业计划数", "学费"}:
        return any(token in candidate for token in ["不限", "化学", "生物", "地理", "政治"])
    return False


def candidate_readability(row):
    if filled(row.get("字段候选值集合")):
        return "R1-有规范候选集合"
    if filled(row.get("字段OCR候选")):
        return "R2-仅有OCR候选"
    return "R0-无候选需看原页"


def candidate_relation(row):
    if has_multi_value(row.get("字段候选值集合")):
        return "C2-多值候选需人工判断"
    if filled(row.get("字段候选值集合")):
        return "C1-单值候选需核PDF和官方"
    if filled(row.get("字段OCR候选")):
        return "C0-OCR候选未规范化"
    return "C9-无候选"


def suggested_action(row):
    if looks_misaligned(row):
        return "A0-疑似错位先回PDF原页"
    if row.get("字段事实阻断等级", "").startswith("Q0"):
        return "A1-无候选先人工读PDF原页"
    if row.get("字段事实阻断等级", "").startswith("Q1"):
        return "A2-带候选核PDF原页再核湖北官方"
    if row.get("字段事实阻断等级", "").startswith("Q2"):
        return "A3-OCR齐全但仍需PDF和湖北官方闭环"
    return "A9-人工判断"


def overlay_has_manual_values(row):
    manual_fields = [
        "PDF原页人工读数",
        "湖北官方字段值",
        "高校官网或招生章程字段值",
        "字段确认值",
        "一审记录",
        "二审记录",
        "复核结论",
        "复核备注",
        "核页状态",
    ]
    return any(filled(row.get(field)) for field in manual_fields)


def public_output(batch_no):
    return (
        ROOT
        / f"data/working/issue19-page-side-foundation-batch-{batch_no:02d}-sample-public-audit.csv"
    )


def public_summary_output(batch_no):
    return (
        ROOT
        / f"data/working/issue19-page-side-foundation-batch-{batch_no:02d}-sample-public-audit-summary.json"
    )


def private_detail_output(batch_no):
    return PRIVATE_DETAIL_DIR / f"batch-{batch_no:02d}-sample-detail.csv"


def build(batch_no):
    field_clue_private = PRIVATE_FIELD_CLUE_DIR / f"batch-{batch_no:02d}-field-clues.csv"
    overlay_private = PRIVATE_OVERLAY_DIR / f"batch-{batch_no:02d}-human-review-overlay.csv"
    if not field_clue_private.exists():
        raise FileNotFoundError(field_clue_private)
    if not overlay_private.exists():
        raise FileNotFoundError(overlay_private)

    public_clues = [
        row
        for row in read_csv(FIELD_CLUE_PUBLIC_AUDIT)
        if as_int(row.get("批次总序")) == batch_no
    ]
    private_clues = read_csv(field_clue_private)
    overlay_rows = read_csv(overlay_private)
    overlay_by_task_id = {row.get("字段事实核验任务ID"): row for row in overlay_rows}

    private_rows = []
    for row in private_clues:
        task_id = row.get("字段事实核验任务ID", "")
        overlay = overlay_by_task_id.get(task_id, {})
        private_rows.append({
            "样板复核任务ID": stable_id("PSSAMPLE", [batch_no, task_id]),
            "批次总序": row.get("批次总序", ""),
            "批次ID": row.get("批次ID", ""),
            "批次名称": row.get("批次名称", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "页码版面键": row.get("页码版面键", ""),
            "页列底座核验批次行ID": row.get("页列底座核验批次行ID", ""),
            "字段事实核验任务ID": task_id,
            "专业行ID": row.get("专业行ID", ""),
            "字段事实闭环ID": row.get("字段事实闭环ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
            "专业组内专业序号": row.get("专业组内专业序号", ""),
            "专业代号OCR": row.get("专业代号OCR", ""),
            "专业名称及备注短摘": row.get("专业名称及备注短摘", ""),
            "字段名": row.get("字段名", ""),
            "字段OCR候选": row.get("字段OCR候选", ""),
            "字段候选值集合": row.get("字段候选值集合", ""),
            "字段候选来源类型集合": row.get("字段候选来源类型集合", ""),
            "字段候选置信等级集合": row.get("字段候选置信等级集合", ""),
            "字段候选状态集合": row.get("字段候选状态集合", ""),
            "字段事实状态": row.get("字段事实状态", ""),
            "字段事实阻断等级": row.get("字段事实阻断等级", ""),
            "字段事实缺口类型": row.get("字段事实缺口类型", ""),
            "字段PDF核验状态": row.get("字段PDF核验状态", ""),
            "字段湖北官方核验状态": row.get("字段湖北官方核验状态", ""),
            "字段事实核验动作": row.get("字段事实核验动作", ""),
            "湖北官方核验包任务ID": row.get("湖北官方核验包任务ID", ""),
            "高校官网证据匹配状态": row.get("高校官网证据匹配状态", ""),
            "B0B1官网证据任务数": row.get("B0B1官网证据任务数", ""),
            "官网证据能否替代湖北官方计划": row.get("官网证据能否替代湖北官方计划", ""),
            "专业起始行号": row.get("专业起始行号", ""),
            "专业窗口行号范围": row.get("专业窗口行号范围", ""),
            "窗口坐标摘要": row.get("窗口坐标摘要", ""),
            "窗口文本SHA256": row.get("窗口文本SHA256", ""),
            "私有页图证据编号": row.get("私有页图证据编号", ""),
            "私有页图SHA256": row.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": row.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": row.get("私有OCR文本SHA256", ""),
            "样板候选可读性": candidate_readability(row),
            "样板候选关系": candidate_relation(row),
            "样板疑似错位": "true" if looks_misaligned(row) else "false",
            "样板建议动作": suggested_action(row),
            "可否自动写入正式Overlay": "false",
            "写入阻断原因": "样板只做流程验证；正式写入必须人工回看PDF原页并核湖北官方系统或省招办计划。",
            "正式Overlay记录是否存在": "true" if overlay else "false",
            "正式Overlay是否已有人工填写": "true" if overlay_has_manual_values(overlay) else "false",
            "正式OverlayID": overlay.get("人工复核OverlayID", ""),
        })

    private_detail = private_detail_output(batch_no)
    write_csv(private_detail, private_rows, PRIVATE_FIELDS)
    private_sha = file_sha(private_detail)

    private_rows_by_page_side = defaultdict(list)
    for row in private_rows:
        private_rows_by_page_side[row.get("页列底座核验批次行ID", "")].append(row)

    public_rows = []
    for clue in public_clues:
        row_id = clue.get("页列底座核验批次行ID", "")
        rows = private_rows_by_page_side.get(row_id, [])
        public_rows.append({
            "页列底座样板公开审计ID": stable_id("PSSAMPLEPUB", [batch_no, row_id]),
            "来源页列底座字段线索公开审计": "data/working/issue19-page-side-foundation-field-clue-public-audit.csv",
            "来源私有字段线索模板": "private_field_clue_templates_not_public",
            "来源私有人工复核Overlay": "private_human_review_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×第1批样板复核审计",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动标记核验完成": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "批次总序": clue.get("批次总序", ""),
            "批次ID": clue.get("批次ID", ""),
            "批次名称": clue.get("批次名称", ""),
            "批内页列序号": clue.get("批内页列序号", ""),
            "页列全局风险总序": clue.get("页列全局风险总序", ""),
            "页列底座核验批次行ID": row_id,
            "页列底座字段线索公开审计ID": clue.get("页列底座字段线索公开审计ID", ""),
            "来源页码": clue.get("来源页码", ""),
            "版面列": clue.get("版面列", ""),
            "页码版面键": clue.get("页码版面键", ""),
            "综合风险优先级桶": clue.get("综合风险优先级桶", ""),
            "页列首要核验动作": clue.get("页列首要核验动作", ""),
            "包内专业行数": clue.get("包内专业行数", ""),
            "包内字段任务数": clue.get("包内字段任务数", ""),
            "样板字段任务数": str(len(rows)),
            "样板专业行覆盖数": str(len({row.get("专业行ID", "") for row in rows if row.get("专业行ID", "")})),
            "样板字段名分布": compact_counter(row.get("字段名", "") for row in rows),
            "样板阻断等级分布": compact_counter(row.get("字段事实阻断等级", "") for row in rows),
            "样板字段状态分布": compact_counter(row.get("字段事实状态", "") for row in rows),
            "样板候选值集合非空任务数": str(sum(filled(row.get("字段候选值集合")) for row in rows)),
            "样板OCR候选非空任务数": str(sum(filled(row.get("字段OCR候选")) for row in rows)),
            "样板多值候选任务数": str(sum(row.get("样板候选关系") == "C2-多值候选需人工判断" for row in rows)),
            "样板疑似错位候选任务数": str(sum(row.get("样板疑似错位") == "true" for row in rows)),
            "样板需PDF原页核验任务数": str(len(rows)),
            "样板需湖北官方核验字段数": str(len(rows)),
            "样板需高校辅证字段数": str(sum(as_int(row.get("B0B1官网证据任务数")) > 0 for row in rows)),
            "样板可自动写入正式Overlay字段数": "0",
            "样板建议动作分布": compact_counter(row.get("样板建议动作", "") for row in rows),
            "样板页列状态": "S0-样板已生成但未事实核准",
            "私有样板明细证据编号": f"batch-{batch_no:02d}-sample-detail",
            "私有样板明细CSV_SHA256": private_sha,
            "私有样板页列记录数": str(len(rows)),
            "私有样板批次记录数": str(len(private_rows)),
            "公开安全策略": "公开表只保存计数、状态分布、SHA和非最终门禁；字段候选值、学校专业明细和人工记录只在私有样板详表。",
            "下一步": "人工回看PDF原页并核湖北官方系统或省招办计划；通过后再写入正式Overlay。",
        })

    output = public_output(batch_no)
    write_csv(output, public_rows, PUBLIC_FIELDS)

    summary = {
        "status": "issue19_page_side_foundation_batch_sample_review_not_final",
        "generated_by": "build_issue19_page_side_foundation_batch_sample_review.py",
        "batch_no": batch_no,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_field_clue_public_audit": "data/working/issue19-page-side-foundation-field-clue-public-audit.csv",
        "source_private_field_clue_template": "private_field_clue_templates_not_public",
        "source_private_human_review_overlay": "private_human_review_overlay_not_public",
        "output_table": str(output.relative_to(ROOT)),
        "private_sample_detail": "private_sample_detail_not_public",
        "private_sample_detail_sha256": private_sha,
        "public_row_count": len(public_rows),
        "private_detail_row_count": len(private_rows),
        "unique_page_side_count": len({(row.get("来源页码"), row.get("版面列")) for row in private_rows}),
        "unique_pdf_page_count": len({row.get("来源页码") for row in private_rows}),
        "unique_major_count": len({row.get("专业行ID") for row in private_rows}),
        "field_task_count": len(private_rows),
        "field_name_distribution": dict(Counter(row.get("字段名") for row in private_rows)),
        "block_level_distribution": dict(Counter(row.get("字段事实阻断等级") for row in private_rows)),
        "fact_status_distribution": dict(Counter(row.get("字段事实状态") for row in private_rows)),
        "candidate_value_set_nonempty_count": sum(filled(row.get("字段候选值集合")) for row in private_rows),
        "ocr_candidate_nonempty_count": sum(filled(row.get("字段OCR候选")) for row in private_rows),
        "multi_value_candidate_count": sum(
            row.get("样板候选关系") == "C2-多值候选需人工判断" for row in private_rows
        ),
        "suspected_misaligned_candidate_count": sum(
            row.get("样板疑似错位") == "true" for row in private_rows
        ),
        "pdf_page_manual_read_required_count": len(private_rows),
        "hubei_official_review_required_count": len(private_rows),
        "school_support_required_count": sum(
            as_int(row.get("B0B1官网证据任务数")) > 0 for row in private_rows
        ),
        "official_overlay_existing_record_count": sum(
            row.get("正式Overlay记录是否存在") == "true" for row in private_rows
        ),
        "official_overlay_manual_filled_count": sum(
            row.get("正式Overlay是否已有人工填写") == "true" for row in private_rows
        ),
        "auto_write_to_formal_overlay_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "sample_runtime_boundary": (
            "样板只验证批次复核流程和工作量；省招办原件、湖北官方渠道、"
            "高校官网或章程辅证未闭环前，不得写成事实结论。"
        ),
    }
    write_json(public_summary_output(batch_no), summary)

    return output, public_summary_output(batch_no), private_detail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-no", type=int, default=1)
    args = parser.parse_args()
    output, summary, private_detail = build(args.batch_no)
    print(f"写出 {output.relative_to(ROOT)}")
    print(f"写出 {summary.relative_to(ROOT)}")
    print(f"写出私有样板详表：{private_detail.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
