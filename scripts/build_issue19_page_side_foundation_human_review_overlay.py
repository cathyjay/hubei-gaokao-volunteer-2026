#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIELD_CLUE_PUBLIC_AUDIT = (
    ROOT / "data/working/issue19-page-side-foundation-field-clue-public-audit.csv"
)
FIELD_CLUE_PRIVATE_DIR = (
    ROOT / "private/review-assets/issue19-page-side-foundation-field-clue-audit"
)
FIELD_CLUE_PRIVATE_INDEX = FIELD_CLUE_PRIVATE_DIR / "field-clue-private-index.csv"

PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-page-side-foundation-human-review-overlay"
)
PRIVATE_OVERLAY_DIR = PRIVATE_OUTPUT_DIR / "overlays"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "human-review-overlay-private-index.csv"
PRIVATE_ORPHANED = PRIVATE_OUTPUT_DIR / "orphaned-overlay-rows.csv"

OUTPUT = (
    ROOT / "data/working/issue19-page-side-foundation-human-review-overlay-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-page-side-foundation-human-review-overlay-public-ledger-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_page_side_foundation_human_review_overlay_public_ledger"


FIELDS = [
    "页列底座Overlay公开账本ID",
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
    "包内字段任务数",
    "Overlay字段记录数",
    "Overlay字段记录缺失数",
    "私有字段线索模板CSV_SHA256",
    "私有Overlay批次证据编号",
    "私有OverlayCSV_SHA256",
    "私有Overlay页列记录数",
    "私有Overlay批次记录数",
    "PDF原页记录已填字段数",
    "PDF原页状态完成字段数",
    "湖北官方记录已填字段数",
    "湖北官方状态完成字段数",
    "高校辅证记录已填字段数",
    "高校辅证状态完成字段数",
    "字段最终记录已填字段数",
    "三方一致性可评估字段数",
    "首轮复核已填字段数",
    "次轮复核已填字段数",
    "复查结论已填字段数",
    "字段事实写回复查可进入字段数",
    "Overlay进度桶",
    "字段事实写回状态",
    "Overlay合并策略",
    "公开安全策略",
    "下一步",
]


OVERLAY_FIELDS = [
    "人工复核OverlayID",
    "批次总序",
    "批次ID",
    "批次名称",
    "来源PDF_SHA256",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列底座核验批次行ID",
    "字段事实核验任务ID",
    "专业行ID",
    "字段名",
    "来源字段线索模板CSV_SHA256",
    "来源字段线索模板行SHA256",
    "字段线索模板锁定",
    "PDF原页证据编号",
    "PDF原页证据SHA256",
    "PDF原页人工读数",
    "PDF原页记录状态",
    "湖北官方证据编号",
    "湖北官方证据SHA256",
    "湖北官方字段值",
    "湖北官方记录状态",
    "高校辅证证据编号",
    "高校辅证证据SHA256",
    "高校官网或招生章程字段值",
    "高校辅证记录状态",
    "字段确认值",
    "字段确认状态",
    "三方一致性状态",
    "差异原因",
    "一审核页人",
    "一审时间",
    "一审记录",
    "二审核页人",
    "二审时间",
    "二审记录",
    "复核结论",
    "复核备注",
    "核页状态",
    "字段写回评估状态",
    "人工记录锁定状态",
    "人工记录版本",
    "updated_at",
]


PRIVATE_INDEX_FIELDS = [
    "批次总序",
    "批次ID",
    "批次名称",
    "私有人工复核Overlay相对路径",
    "私有OverlayCSV_SHA256",
    "来源字段线索模板CSV_SHA256",
    "批次页列数",
    "批次字段任务数",
    "保留既有人工填写单元数",
    "孤立旧Overlay记录数",
]


MANUAL_FIELDS = [
    "PDF原页人工读数",
    "PDF原页记录状态",
    "PDF原页证据编号",
    "PDF原页证据SHA256",
    "湖北官方字段值",
    "湖北官方记录状态",
    "湖北官方证据编号",
    "湖北官方证据SHA256",
    "高校官网或招生章程字段值",
    "高校辅证记录状态",
    "高校辅证证据编号",
    "高校辅证证据SHA256",
    "字段确认值",
    "字段确认状态",
    "三方一致性状态",
    "差异原因",
    "一审核页人",
    "一审时间",
    "一审记录",
    "二审核页人",
    "二审时间",
    "二审记录",
    "复核结论",
    "复核备注",
    "核页状态",
    "字段写回评估状态",
    "人工记录锁定状态",
    "人工记录版本",
    "updated_at",
]


COMPLETE_STATUS_TOKENS = {
    "done",
    "complete",
    "completed",
    "checked",
    "verified",
    "matched",
    "not_applicable",
    "na",
    "已完成",
    "完成",
    "已核准",
    "核准",
    "一致",
    "不适用",
}


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


def row_sha(row, fields):
    text = "\n".join(f"{field}={row.get(field, '')}" for field in fields)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def filled(value):
    return bool(str(value or "").strip())


def page_side_key(row):
    return str(row.get("来源页码", "")).strip(), str(row.get("版面列", "")).strip()


def status_complete(value):
    text = str(value or "").strip().lower()
    return bool(text) and (
        text in COMPLETE_STATUS_TOKENS
        or any(token in text for token in ["done", "complete", "verified", "matched"])
    )


def manual_cell_count(row):
    return sum(1 for field in MANUAL_FIELDS if field != "人工记录版本" and filled(row.get(field)))


def build_overlay_row(template_row, template_sha):
    task_id = template_row.get("字段事实核验任务ID", "")
    return {
        "人工复核OverlayID": stable_id("PSHUMANOVERLAY", [task_id, template_sha]),
        "批次总序": template_row.get("批次总序", ""),
        "批次ID": template_row.get("批次ID", ""),
        "批次名称": template_row.get("批次名称", ""),
        "来源PDF_SHA256": SOURCE_PDF_SHA256,
        "来源页码": template_row.get("来源页码", ""),
        "版面列": template_row.get("版面列", ""),
        "页码版面键": template_row.get("页码版面键", ""),
        "页列底座核验批次行ID": template_row.get("页列底座核验批次行ID", ""),
        "字段事实核验任务ID": task_id,
        "专业行ID": template_row.get("专业行ID", ""),
        "字段名": template_row.get("字段名", ""),
        "来源字段线索模板CSV_SHA256": template_sha,
        "来源字段线索模板行SHA256": row_sha(template_row, sorted(template_row)),
        "字段线索模板锁定": "true",
        "PDF原页证据编号": "",
        "PDF原页证据SHA256": "",
        "PDF原页人工读数": "",
        "PDF原页记录状态": "",
        "湖北官方证据编号": "",
        "湖北官方证据SHA256": "",
        "湖北官方字段值": "",
        "湖北官方记录状态": "",
        "高校辅证证据编号": "",
        "高校辅证证据SHA256": "",
        "高校官网或招生章程字段值": "",
        "高校辅证记录状态": "",
        "字段确认值": "",
        "字段确认状态": "",
        "三方一致性状态": "",
        "差异原因": "",
        "一审核页人": "",
        "一审时间": "",
        "一审记录": "",
        "二审核页人": "",
        "二审时间": "",
        "二审记录": "",
        "复核结论": "",
        "复核备注": "",
        "核页状态": "",
        "字段写回评估状态": "",
        "人工记录锁定状态": "",
        "人工记录版本": "1",
        "updated_at": "",
    }


def merge_existing_manual_values(new_row, existing_row):
    preserved_count = 0
    if not existing_row:
        return new_row, preserved_count
    for field in MANUAL_FIELDS:
        if field == "人工记录版本":
            continue
        old_value = existing_row.get(field, "")
        if filled(old_value):
            new_row[field] = old_value
            preserved_count += 1
    if not filled(new_row.get("人工记录版本")):
        new_row["人工记录版本"] = existing_row.get("人工记录版本") or "1"
    return new_row, preserved_count


def progress_bucket(rows):
    if not rows:
        return "R9-Overlay记录缺失"
    review_ready = sum(
        filled(row.get("PDF原页人工读数"))
        and filled(row.get("湖北官方字段值"))
        and filled(row.get("字段确认值"))
        and filled(row.get("一审记录"))
        and filled(row.get("二审记录"))
        and filled(row.get("复核结论"))
        for row in rows
    )
    any_manual = any(manual_cell_count(row) > 0 for row in rows)
    if review_ready == len(rows):
        return "R3-Overlay核心记录已齐待事实复查"
    if any_manual:
        return "R1-Overlay已有部分填写"
    return "R0-Overlay已生成未填写"


def build_rows():
    field_clue_rows = read_csv(FIELD_CLUE_PUBLIC_AUDIT)
    field_clue_by_page_side = {page_side_key(row): row for row in field_clue_rows}
    field_clue_private_index = read_csv(FIELD_CLUE_PRIVATE_INDEX)

    overlay_private_index_rows = []
    overlay_rows_by_page_side = defaultdict(list)
    overlay_count_by_batch = {}
    overlay_sha_by_batch = {}
    preserved_manual_cell_count_by_batch = {}
    orphan_rows = []

    for index_row in field_clue_private_index:
        batch_no = as_int(index_row.get("批次总序"))
        template_rel = index_row.get("私有字段线索模板相对路径", "")
        template_csv = FIELD_CLUE_PRIVATE_DIR / template_rel
        template_sha = file_sha(template_csv)
        template_rows = read_csv(template_csv)

        overlay_csv = PRIVATE_OVERLAY_DIR / f"batch-{batch_no:02d}-human-review-overlay.csv"
        existing_by_task = {}
        if overlay_csv.exists():
            for old_row in read_csv(overlay_csv):
                task_id = old_row.get("字段事实核验任务ID", "")
                if task_id:
                    existing_by_task[task_id] = old_row

        overlay_rows = []
        preserved_manual_cell_count = 0
        seen_task_ids = set()
        for template_row in template_rows:
            task_id = template_row.get("字段事实核验任务ID", "")
            seen_task_ids.add(task_id)
            new_row = build_overlay_row(template_row, template_sha)
            new_row, preserved_count = merge_existing_manual_values(
                new_row,
                existing_by_task.get(task_id, {}),
            )
            preserved_manual_cell_count += preserved_count
            overlay_rows.append(new_row)
            overlay_rows_by_page_side[page_side_key(new_row)].append(new_row)

        batch_orphans = [
            row for task_id, row in existing_by_task.items() if task_id not in seen_task_ids
        ]
        orphan_rows.extend(batch_orphans)

        write_csv(overlay_csv, overlay_rows, OVERLAY_FIELDS)
        overlay_sha = file_sha(overlay_csv)
        overlay_count_by_batch[batch_no] = len(overlay_rows)
        overlay_sha_by_batch[batch_no] = overlay_sha
        preserved_manual_cell_count_by_batch[batch_no] = preserved_manual_cell_count
        overlay_private_index_rows.append({
            "批次总序": str(batch_no),
            "批次ID": index_row.get("批次ID", ""),
            "批次名称": index_row.get("批次名称", ""),
            "私有人工复核Overlay相对路径": str(overlay_csv.relative_to(PRIVATE_OUTPUT_DIR)),
            "私有OverlayCSV_SHA256": overlay_sha,
            "来源字段线索模板CSV_SHA256": template_sha,
            "批次页列数": index_row.get("批次页列数", ""),
            "批次字段任务数": str(len(overlay_rows)),
            "保留既有人工填写单元数": str(preserved_manual_cell_count),
            "孤立旧Overlay记录数": str(len(batch_orphans)),
        })

    write_csv(PRIVATE_INDEX, overlay_private_index_rows, PRIVATE_INDEX_FIELDS)
    if orphan_rows:
        write_csv(PRIVATE_ORPHANED, orphan_rows, OVERLAY_FIELDS)
    elif PRIVATE_ORPHANED.exists():
        PRIVATE_ORPHANED.unlink()

    public_rows = []
    for field_clue in field_clue_rows:
        key = page_side_key(field_clue)
        batch_no = as_int(field_clue.get("批次总序"))
        overlay_rows = overlay_rows_by_page_side.get(key, [])
        overlay_count = len(overlay_rows)
        pdf_filled = sum(filled(row.get("PDF原页人工读数")) for row in overlay_rows)
        pdf_done = sum(status_complete(row.get("PDF原页记录状态")) for row in overlay_rows)
        hubei_filled = sum(filled(row.get("湖北官方字段值")) for row in overlay_rows)
        hubei_done = sum(status_complete(row.get("湖北官方记录状态")) for row in overlay_rows)
        school_filled = sum(filled(row.get("高校官网或招生章程字段值")) for row in overlay_rows)
        school_done = sum(status_complete(row.get("高校辅证记录状态")) for row in overlay_rows)
        final_filled = sum(filled(row.get("字段确认值")) for row in overlay_rows)
        tri_ready = sum(filled(row.get("三方一致性状态")) for row in overlay_rows)
        first_done = sum(filled(row.get("一审记录")) for row in overlay_rows)
        second_done = sum(filled(row.get("二审记录")) for row in overlay_rows)
        conclusion_done = sum(filled(row.get("复核结论")) for row in overlay_rows)
        writeback_ready = sum(
            filled(row.get("PDF原页人工读数"))
            and filled(row.get("湖北官方字段值"))
            and filled(row.get("字段确认值"))
            and filled(row.get("一审记录"))
            and filled(row.get("二审记录"))
            and filled(row.get("复核结论"))
            for row in overlay_rows
        )
        public_rows.append({
            "页列底座Overlay公开账本ID": stable_id(
                "PSOVERLAYPROG",
                [field_clue.get("页列底座核验批次行ID", ""), batch_no],
            ),
            "来源页列底座字段线索公开审计": "data/working/issue19-page-side-foundation-field-clue-public-audit.csv",
            "来源私有字段线索模板": "private_field_clue_templates_not_public",
            "来源私有人工复核Overlay": "private_human_review_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×人工复核Overlay进度",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动标记核验完成": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "批次总序": field_clue.get("批次总序", ""),
            "批次ID": field_clue.get("批次ID", ""),
            "批次名称": field_clue.get("批次名称", ""),
            "批内页列序号": field_clue.get("批内页列序号", ""),
            "页列全局风险总序": field_clue.get("页列全局风险总序", ""),
            "页列底座核验批次行ID": field_clue.get("页列底座核验批次行ID", ""),
            "页列底座字段线索公开审计ID": field_clue.get("页列底座字段线索公开审计ID", ""),
            "来源页码": field_clue.get("来源页码", ""),
            "版面列": field_clue.get("版面列", ""),
            "页码版面键": field_clue.get("页码版面键", ""),
            "综合风险优先级桶": field_clue.get("综合风险优先级桶", ""),
            "页列首要核验动作": field_clue.get("页列首要核验动作", ""),
            "包内字段任务数": field_clue.get("包内字段任务数", ""),
            "Overlay字段记录数": str(overlay_count),
            "Overlay字段记录缺失数": str(max(as_int(field_clue.get("包内字段任务数")) - overlay_count, 0)),
            "私有字段线索模板CSV_SHA256": field_clue.get("私有字段线索模板CSV_SHA256", ""),
            "私有Overlay批次证据编号": f"ps-human-review-overlay-batch-{batch_no:02d}-csv",
            "私有OverlayCSV_SHA256": overlay_sha_by_batch.get(batch_no, ""),
            "私有Overlay页列记录数": str(overlay_count),
            "私有Overlay批次记录数": str(overlay_count_by_batch.get(batch_no, 0)),
            "PDF原页记录已填字段数": str(pdf_filled),
            "PDF原页状态完成字段数": str(pdf_done),
            "湖北官方记录已填字段数": str(hubei_filled),
            "湖北官方状态完成字段数": str(hubei_done),
            "高校辅证记录已填字段数": str(school_filled),
            "高校辅证状态完成字段数": str(school_done),
            "字段最终记录已填字段数": str(final_filled),
            "三方一致性可评估字段数": str(tri_ready),
            "首轮复核已填字段数": str(first_done),
            "次轮复核已填字段数": str(second_done),
            "复查结论已填字段数": str(conclusion_done),
            "字段事实写回复查可进入字段数": str(writeback_ready),
            "Overlay进度桶": progress_bucket(overlay_rows),
            "字段事实写回状态": "blocked_until_overlay_pdf_hubei_review_closed",
            "Overlay合并策略": (
                "机器重跑只刷新来源键和SHA；"
                "按字段事实核验任务ID保留既有人工填写列；"
                "孤立旧记录写入本地私有orphan文件。"
            ),
            "公开安全策略": (
                "公开表只保存Overlay记录计数、完成状态计数、证据编号和SHA；"
                "不公开具体字段读数、官方值、学校专业明细、人员字段或备注正文。"
            ),
            "下一步": (
                "在本地Overlay逐字段录入PDF原页、湖北官方侧和必要高校辅证；"
                "完成双人复查后再进入字段事实写回复查。"
            ),
        })
    return public_rows, overlay_private_index_rows, orphan_rows


def main():
    rows, private_index_rows, orphan_rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    summary = {
        "status": "issue19_page_side_foundation_human_review_overlay_public_ledger_not_final",
        "generated_by": "build_issue19_page_side_foundation_human_review_overlay.py",
        "source_field_clue_public_audit": "data/working/issue19-page-side-foundation-field-clue-public-audit.csv",
        "source_private_field_clue_templates": "private_field_clue_templates_not_public",
        "source_private_human_review_overlay": "private_human_review_overlay_not_public",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": "data/working/issue19-page-side-foundation-human-review-overlay-public-ledger.csv",
        "row_count": len(rows),
        "batch_count": len({row["批次ID"] for row in rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "source_field_task_count": sum(as_int(row["包内字段任务数"]) for row in rows),
        "overlay_field_record_count": sum(as_int(row["Overlay字段记录数"]) for row in rows),
        "overlay_missing_field_record_count": sum(as_int(row["Overlay字段记录缺失数"]) for row in rows),
        "private_overlay_template_count": len(private_index_rows),
        "private_overlay_template_row_count": sum(as_int(row["批次字段任务数"]) for row in private_index_rows),
        "private_overlay_index_csv_sha256": file_sha(PRIVATE_INDEX),
        "orphaned_overlay_row_count": len(orphan_rows),
        "preserved_manual_cell_count": sum(as_int(row["保留既有人工填写单元数"]) for row in private_index_rows),
        "pdf_page_record_filled_task_count": sum(as_int(row["PDF原页记录已填字段数"]) for row in rows),
        "pdf_page_status_done_task_count": sum(as_int(row["PDF原页状态完成字段数"]) for row in rows),
        "hubei_official_record_filled_task_count": sum(as_int(row["湖北官方记录已填字段数"]) for row in rows),
        "hubei_official_status_done_task_count": sum(as_int(row["湖北官方状态完成字段数"]) for row in rows),
        "school_support_record_filled_task_count": sum(as_int(row["高校辅证记录已填字段数"]) for row in rows),
        "school_support_status_done_task_count": sum(as_int(row["高校辅证状态完成字段数"]) for row in rows),
        "final_field_record_filled_task_count": sum(as_int(row["字段最终记录已填字段数"]) for row in rows),
        "tri_consistency_assessable_task_count": sum(as_int(row["三方一致性可评估字段数"]) for row in rows),
        "first_review_record_filled_task_count": sum(as_int(row["首轮复核已填字段数"]) for row in rows),
        "second_review_record_filled_task_count": sum(as_int(row["次轮复核已填字段数"]) for row in rows),
        "review_conclusion_filled_task_count": sum(as_int(row["复查结论已填字段数"]) for row in rows),
        "field_writeback_review_ready_task_count": sum(as_int(row["字段事实写回复查可进入字段数"]) for row in rows),
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "safety_note": (
            "公开表只保存Overlay记录计数、完成状态计数、证据编号和SHA；"
            "不保存具体字段读数、官方值、学校专业明细、人员字段或备注正文。"
        ),
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出私有人工复核Overlay：{PRIVATE_OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
