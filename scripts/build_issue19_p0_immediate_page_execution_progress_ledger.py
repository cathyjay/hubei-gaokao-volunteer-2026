#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PAGE_EXECUTION_QUEUE = ROOT / "data/working/issue19-p0-immediate-page-execution-queue.csv"
FIELD_CONFIRMATION_PUBLIC_LEDGER = (
    ROOT / "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv"
)
PRIVATE_FIELD_CONFIRMATION_WORKBENCH = (
    ROOT
    / "private/review-assets/issue19-p0-immediate-field-confirmation/field-confirmation-private-workbench.csv"
)

OUTPUT = ROOT / "data/working/issue19-p0-immediate-page-execution-progress-public-ledger.csv"
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-p0-immediate-page-execution-progress-public-ledger-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_p0_immediate_page_execution_progress_public_ledger"


FIELDS = [
    "P0即时页列执行进度公开账本ID",
    "来源P0即时页列核页执行队列",
    "来源P0即时字段确认公开账本",
    "来源私有字段确认工作台",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动回填候选",
    "是否允许写回字段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "页列执行总序",
    "来源页码",
    "版面列",
    "页码版面键",
    "P0即时页列核页执行队列ID",
    "P0即时按页核页包ID",
    "页列核页优先级桶",
    "页列核页优先级数值",
    "包内字段任务数",
    "包内专业行数",
    "包内裁图证据数",
    "包内需要双人复核任务数",
    "包内高校辅证核验任务数",
    "PDF原页私有记录已录数",
    "PDF原页私有记录未录数",
    "湖北官方私有记录已录数",
    "湖北官方私有记录未录数",
    "高校辅证应录数",
    "高校辅证已录数",
    "高校辅证未录数",
    "字段确认私有记录已录数",
    "字段确认私有记录未录数",
    "双人复核应完成数",
    "双人复核已完成数",
    "双人复核未完成数",
    "冲突阻断任务数",
    "三方字段一致性可评估数",
    "可进入字段写回复查数",
    "PDF原页私有记录状态分布",
    "湖北官方私有记录状态分布",
    "高校辅证私有记录状态分布",
    "双人复核公开状态分布",
    "字段事实写回评估状态分布",
    "页列执行进度桶",
    "页列执行进度状态",
    "私有字段确认工作台SHA256",
    "字段确认公开账本ID集合SHA256",
    "P0字段即时复核任务ID集合SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
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
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha_list(values):
    normalized = "；".join(sorted({value for value in values if value}))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def counter_text(counter):
    return "；".join(f"{key}:{value}" for key, value in sorted(counter.items())) if counter else ""


def split_semicolon(value):
    return [item for item in str(value or "").split("；") if item]


def is_filled(row, field):
    return bool(str(row.get(field, "")).strip())


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except ValueError:
        return default


def progress_bucket(total, pdf_done, official_done, school_required, school_done, writeback_ready):
    if writeback_ready == total and total:
        return "R4-可进入字段写回复查", "all_required_private_records_complete"
    if pdf_done and official_done and school_done == school_required:
        return "R3-私有读数已齐待一致性复查", "private_readings_complete_pending_consistency_review"
    if pdf_done or official_done or school_done:
        return "R1-部分私有记录已录仍未闭环", "partial_private_records_present"
    return "R0-未开始PDF和湖北官方核验", "pending_pdf_and_hubei_official_review"


def build_rows():
    queue_rows = read_csv(PAGE_EXECUTION_QUEUE)
    public_rows = read_csv(FIELD_CONFIRMATION_PUBLIC_LEDGER)
    private_rows = read_csv(PRIVATE_FIELD_CONFIRMATION_WORKBENCH)
    private_sha = file_sha(PRIVATE_FIELD_CONFIRMATION_WORKBENCH)

    public_by_id = {row["P0即时字段确认公开账本ID"]: row for row in public_rows}
    private_by_id = {row["P0即时字段确认公开账本ID"]: row for row in private_rows}

    if set(public_by_id) != set(private_by_id):
        raise RuntimeError("private field confirmation workbench does not match public ledger IDs")

    rows_by_queue = defaultdict(list)
    for queue in queue_rows:
        for ledger_id in split_semicolon(queue["P0即时字段确认公开账本ID集合"]):
            private_row = private_by_id.get(ledger_id)
            public_row = public_by_id.get(ledger_id)
            if not private_row or not public_row:
                raise RuntimeError(f"missing field confirmation row {ledger_id}")
            rows_by_queue[queue["P0即时页列核页执行队列ID"]].append((private_row, public_row))

    output_rows = []
    for queue in queue_rows:
        queue_id = queue["P0即时页列核页执行队列ID"]
        pairs = rows_by_queue[queue_id]
        if not pairs:
            raise RuntimeError(f"missing private progress rows for {queue_id}")
        private_group = [pair[0] for pair in pairs]
        public_group = [pair[1] for pair in pairs]
        total = len(private_group)
        pdf_done = sum(is_filled(row, "PDF原页人工读数") for row in private_group)
        official_done = sum(is_filled(row, "湖北官方字段值") for row in private_group)
        school_required = sum(row.get("是否有高校字段线索") == "true" for row in private_group)
        school_done = sum(
            row.get("是否有高校字段线索") == "true"
            and is_filled(row, "高校官网或招生章程字段值")
            for row in private_group
        )
        field_confirm_done = sum(is_filled(row, "字段确认值") for row in private_group)
        double_required = sum(row.get("是否需要双人复核") == "true" for row in private_group)
        double_done = sum(
            row.get("是否需要双人复核") == "true"
            and is_filled(row, "PDF核页复核人A")
            and is_filled(row, "PDF核页复核人B")
            for row in private_group
        )
        conflict_count = sum(
            row.get("是否裁图OCR与机器候选冲突") == "true"
            or row.get("是否裁图OCR与高校辅证冲突") == "true"
            or row.get("是否机器高校冲突") == "true"
            for row in private_group
        )
        consistency_ready = sum(
            is_filled(row, "PDF原页人工读数")
            and is_filled(row, "湖北官方字段值")
            and (
                row.get("是否有高校字段线索") != "true"
                or is_filled(row, "高校官网或招生章程字段值")
            )
            for row in private_group
        )
        writeback_ready = sum(
            is_filled(row, "字段确认值")
            and is_filled(row, "PDF原页人工读数")
            and is_filled(row, "湖北官方字段值")
            and (
                row.get("是否有高校字段线索") != "true"
                or is_filled(row, "高校官网或招生章程字段值")
            )
            and (
                row.get("是否需要双人复核") != "true"
                or (is_filled(row, "PDF核页复核人A") and is_filled(row, "PDF核页复核人B"))
            )
            for row in private_group
        )
        bucket, status = progress_bucket(
            total, pdf_done, official_done, school_required, school_done, writeback_ready
        )
        output_rows.append({
            "P0即时页列执行进度公开账本ID": stable_id("P0PAGEPROG", [queue_id]),
            "来源P0即时页列核页执行队列": "data/working/issue19-p0-immediate-page-execution-queue.csv",
            "来源P0即时字段确认公开账本": "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv",
            "来源私有字段确认工作台": "private_field_confirmation_workbench_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×P0即时页列执行进度状态",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "页列执行总序": queue["页列执行总序"],
            "来源页码": queue["来源页码"],
            "版面列": queue["版面列"],
            "页码版面键": queue["页码版面键"],
            "P0即时页列核页执行队列ID": queue_id,
            "P0即时按页核页包ID": queue["P0即时按页核页包ID"],
            "页列核页优先级桶": queue["页列核页优先级桶"],
            "页列核页优先级数值": queue["页列核页优先级数值"],
            "包内字段任务数": str(total),
            "包内专业行数": queue["包内专业行数"],
            "包内裁图证据数": queue["包内裁图证据数"],
            "包内需要双人复核任务数": str(double_required),
            "包内高校辅证核验任务数": str(school_required),
            "PDF原页私有记录已录数": str(pdf_done),
            "PDF原页私有记录未录数": str(total - pdf_done),
            "湖北官方私有记录已录数": str(official_done),
            "湖北官方私有记录未录数": str(total - official_done),
            "高校辅证应录数": str(school_required),
            "高校辅证已录数": str(school_done),
            "高校辅证未录数": str(school_required - school_done),
            "字段确认私有记录已录数": str(field_confirm_done),
            "字段确认私有记录未录数": str(total - field_confirm_done),
            "双人复核应完成数": str(double_required),
            "双人复核已完成数": str(double_done),
            "双人复核未完成数": str(double_required - double_done),
            "冲突阻断任务数": str(conflict_count),
            "三方字段一致性可评估数": str(consistency_ready),
            "可进入字段写回复查数": str(writeback_ready),
            "PDF原页私有记录状态分布": counter_text(Counter(row["PDF原页私有记录状态"] for row in private_group)),
            "湖北官方私有记录状态分布": counter_text(Counter(row["湖北官方私有记录状态"] for row in private_group)),
            "高校辅证私有记录状态分布": counter_text(Counter(row["高校辅证私有记录状态"] for row in private_group)),
            "双人复核公开状态分布": counter_text(Counter(row["双人复核公开状态"] for row in private_group)),
            "字段事实写回评估状态分布": counter_text(Counter(row["字段事实写回评估状态"] for row in private_group)),
            "页列执行进度桶": bucket,
            "页列执行进度状态": status,
            "私有字段确认工作台SHA256": private_sha,
            "字段确认公开账本ID集合SHA256": sha_list(
                row["P0即时字段确认公开账本ID"] for row in public_group
            ),
            "P0字段即时复核任务ID集合SHA256": sha_list(
                row["P0字段即时复核任务ID"] for row in public_group
            ),
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "字段事实写回状态": "blocked_until_required_private_readings_complete",
            "公开安全策略": (
                "只公开页列进度计数、状态、任务集合哈希和证据SHA；不公开候选内容、"
                "人工填写内容、OCR行文本、图片路径、院校名、专业名、专业代号或专业组代码。"
            ),
            "下一步": (
                "先补 PDF 原页记录和湖北官方侧记录；如有高校辅证线索再补高校侧记录，"
                "完成双人复核后才允许进入字段写回复查。"
            ),
        })

    return output_rows, private_rows


def main():
    rows, private_rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    summary = {
        "status": "issue19_p0_immediate_page_execution_progress_public_ledger_not_final",
        "generated_by": "build_issue19_p0_immediate_page_execution_progress_ledger.py",
        "source_page_execution_queue": "data/working/issue19-p0-immediate-page-execution-queue.csv",
        "source_field_confirmation_public_ledger": (
            "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv"
        ),
        "source_private_field_confirmation_workbench": "private_field_confirmation_workbench_not_public",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": "data/working/issue19-p0-immediate-page-execution-progress-public-ledger.csv",
        "row_count": len(rows),
        "source_private_task_count": len(private_rows),
        "unique_page_execution_queue_id_count": len({row["P0即时页列核页执行队列ID"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "progress_bucket_counts": dict(Counter(row["页列执行进度桶"] for row in rows)),
        "pdf_reading_recorded_task_count": sum(as_int(row["PDF原页私有记录已录数"]) for row in rows),
        "pdf_reading_missing_task_count": sum(as_int(row["PDF原页私有记录未录数"]) for row in rows),
        "hubei_official_recorded_task_count": sum(as_int(row["湖北官方私有记录已录数"]) for row in rows),
        "hubei_official_missing_task_count": sum(as_int(row["湖北官方私有记录未录数"]) for row in rows),
        "school_support_required_task_count": sum(as_int(row["高校辅证应录数"]) for row in rows),
        "school_support_recorded_task_count": sum(as_int(row["高校辅证已录数"]) for row in rows),
        "double_review_required_task_count": sum(as_int(row["双人复核应完成数"]) for row in rows),
        "double_review_completed_task_count": sum(as_int(row["双人复核已完成数"]) for row in rows),
        "field_confirmation_recorded_task_count": sum(as_int(row["字段确认私有记录已录数"]) for row in rows),
        "three_way_consistency_evaluable_task_count": sum(as_int(row["三方字段一致性可评估数"]) for row in rows),
        "field_writeback_review_ready_task_count": sum(as_int(row["可进入字段写回复查数"]) for row in rows),
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "safety_note": (
            "公开账本只保存进度计数、状态、任务集合哈希和证据SHA；不保存候选内容、"
            "人工填写内容、OCR行文本、图片路径、院校名、专业名、专业代号或专业组代码。"
        ),
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
