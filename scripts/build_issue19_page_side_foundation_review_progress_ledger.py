#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_BATCHES = ROOT / "data/working/issue19-page-side-foundation-verification-batches.csv"
EXECUTION_PACKETS = ROOT / "data/working/issue19-page-side-foundation-batch-execution-packets.csv"
PRIVATE_TASK_DIR = (
    ROOT / "private/review-assets/issue19-page-side-foundation-batch-execution-packets/tasks"
)

OUTPUT = ROOT / "data/working/issue19-page-side-foundation-review-progress-public-ledger.csv"
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-page-side-foundation-review-progress-public-ledger-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_page_side_foundation_review_progress_public_ledger"


FIELDS = [
    "页列底座核页进度公开账本ID",
    "来源页列底座批次执行包表",
    "来源页列底座核验批次表",
    "来源私有批次任务CSV",
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
    "来源页码",
    "版面列",
    "页码版面键",
    "综合风险优先级桶",
    "页列首要核验动作",
    "包内专业行数",
    "包内字段任务数",
    "字段Q0无候选阻断任务数",
    "字段Q1有候选待人工核验任务数",
    "字段Q2待三方闭环任务数",
    "结构风险事件数",
    "官方查询键碰撞行数",
    "教育部未匹配校名专业行数",
    "官网辅证线索行数",
    "官网计划数冲突行数",
    "OCR行数",
    "OCR低置信度行数",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有批次审阅HTML证据编号",
    "私有批次审阅HTML_SHA256",
    "私有批次审阅任务CSV_SHA256",
    "私有任务CSV_SHA256匹配状态",
    "PDF原页核页记录状态",
    "湖北官方核验记录状态",
    "结构和官方消歧记录状态",
    "高校辅证记录状态",
    "高校辅证是否需要记录",
    "一审记录状态",
    "二审记录状态",
    "双人复核记录状态",
    "私有记录必填项数",
    "私有记录已填项数",
    "私有记录未填项数",
    "私有记录填写进度",
    "页列私有记录进度桶",
    "页列私有记录进度状态",
    "PDF原页核页是否完成",
    "湖北官方核验是否完成",
    "结构和官方消歧是否完成",
    "高校辅证是否完成",
    "页列是否满足升级条件",
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


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def filled(value):
    return bool(str(value or "").strip())


def yes_no(condition):
    return "true" if condition else "false"


def record_state(value):
    return "S1-已有私有记录待复查" if filled(value) else "S0-未记录"


def reviewer_state(row):
    a = filled(row.get("核页人A"))
    b = filled(row.get("核页人B"))
    if a and b:
        return "D2-双人记录已齐待事实复查"
    if a or b:
        return "D1-单人记录待补另一人"
    return "D0-未记录"


def progress_bucket(required, recorded, double_review_state):
    if recorded == 0:
        return "R0-未开始私有核页记录", "pending_private_review_records"
    if recorded < required:
        return "R1-已有部分私有记录但未闭环", "partial_private_review_records_present"
    if double_review_state != "D2-双人记录已齐待事实复查":
        return "R2-必填记录已齐待双人复核", "required_records_present_pending_dual_review"
    return "R3-记录和双人复核已齐待事实复查", "records_and_dual_review_present_pending_fact_review"


def task_csv_path(batch_no):
    return PRIVATE_TASK_DIR / f"batch-{batch_no:02d}.csv"


def build_rows():
    source_rows = read_csv(SOURCE_BATCHES)
    execution_rows = read_csv(EXECUTION_PACKETS)
    source_by_row_id = {row["页列底座核验批次行ID"]: row for row in source_rows}
    execution_by_batch_no = {as_int(row["批次总序"]): row for row in execution_rows}

    if len(source_by_row_id) != len(source_rows):
        raise RuntimeError("duplicate page-side foundation batch row id")
    if len(execution_by_batch_no) != len(execution_rows):
        raise RuntimeError("duplicate batch execution packet")

    output_rows = []
    private_task_row_count = 0
    for batch_no in sorted(execution_by_batch_no):
        task_path = task_csv_path(batch_no)
        if not task_path.exists():
            raise RuntimeError(f"missing private task csv for batch {batch_no:02d}")
        private_task_sha = file_sha(task_path)
        private_rows = read_csv(task_path)
        private_task_row_count += len(private_rows)
        exec_row = execution_by_batch_no[batch_no]
        expected_task_sha = exec_row.get("私有批次审阅任务CSV_SHA256", "")
        task_sha_status = (
            "matched_execution_packet_sha"
            if private_task_sha == expected_task_sha
            else "changed_after_execution_packet_sha"
        )

        for private_row in private_rows:
            row_id = private_row.get("页列底座核验批次行ID", "")
            source = source_by_row_id.get(row_id)
            if not source:
                raise RuntimeError(f"missing source batch row {row_id}")

            pdf_recorded = filled(private_row.get("PDF原页核页记录"))
            official_recorded = filled(private_row.get("湖北官方核验记录"))
            structure_recorded = filled(private_row.get("结构和官方消歧记录"))
            school_required = (
                as_int(private_row.get("官网辅证线索行数")) > 0
                or as_int(private_row.get("官网计划数冲突行数")) > 0
            )
            school_recorded = filled(private_row.get("高校辅证记录"))
            required_count = 3 + (1 if school_required else 0)
            recorded_count = (
                int(pdf_recorded)
                + int(official_recorded)
                + int(structure_recorded)
                + (int(school_recorded) if school_required else 0)
            )
            double_review = reviewer_state(private_row)
            bucket, status = progress_bucket(required_count, recorded_count, double_review)

            output_rows.append({
                "页列底座核页进度公开账本ID": stable_id("PSFOUNDATIONPROG", [row_id, batch_no]),
                "来源页列底座批次执行包表": "data/working/issue19-page-side-foundation-batch-execution-packets.csv",
                "来源页列底座核验批次表": "data/working/issue19-page-side-foundation-verification-batches.csv",
                "来源私有批次任务CSV": "private_batch_task_csv_not_public",
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "数据阶段": DATA_STAGE,
                "主表粒度": "PDF页码×版面列",
                "任务粒度": "PDF页码×版面列×私有核页记录进度",
                "最终可用": "false",
                "可进入下一阶段": "false",
                "机器是否允许自动写回主表": "false",
                "机器是否允许自动标记核验完成": "false",
                "是否允许作为志愿推荐依据": "false",
                "是否允许生成学校专业建议": "false",
                "批次总序": private_row.get("批次总序", ""),
                "批次ID": private_row.get("批次ID", ""),
                "批次名称": private_row.get("批次名称", ""),
                "批内页列序号": source.get("批内页列序号", ""),
                "页列全局风险总序": private_row.get("页列全局风险总序", ""),
                "页列底座核验批次行ID": row_id,
                "来源页码": private_row.get("来源页码", ""),
                "版面列": private_row.get("版面列", ""),
                "页码版面键": private_row.get("页码版面键", ""),
                "综合风险优先级桶": private_row.get("综合风险优先级桶", ""),
                "页列首要核验动作": private_row.get("页列首要核验动作", ""),
                "包内专业行数": private_row.get("包内专业行数", ""),
                "包内字段任务数": private_row.get("包内字段任务数", ""),
                "字段Q0无候选阻断任务数": private_row.get("字段Q0无候选阻断任务数", ""),
                "字段Q1有候选待人工核验任务数": private_row.get("字段Q1有候选待人工核验任务数", ""),
                "字段Q2待三方闭环任务数": private_row.get("字段Q2待三方闭环任务数", ""),
                "结构风险事件数": private_row.get("结构风险事件数", ""),
                "官方查询键碰撞行数": private_row.get("官方查询键碰撞行数", ""),
                "教育部未匹配校名专业行数": private_row.get("教育部未匹配校名专业行数", ""),
                "官网辅证线索行数": private_row.get("官网辅证线索行数", ""),
                "官网计划数冲突行数": private_row.get("官网计划数冲突行数", ""),
                "OCR行数": private_row.get("OCR行数", ""),
                "OCR低置信度行数": private_row.get("OCR低置信度行数", ""),
                "私有页图证据编号": private_row.get("私有页图证据编号", ""),
                "私有页图SHA256": private_row.get("私有页图SHA256", ""),
                "私有批次审阅HTML证据编号": exec_row.get("私有批次审阅HTML证据编号", ""),
                "私有批次审阅HTML_SHA256": exec_row.get("私有批次审阅HTML_SHA256", ""),
                "私有批次审阅任务CSV_SHA256": private_task_sha,
                "私有任务CSV_SHA256匹配状态": task_sha_status,
                "PDF原页核页记录状态": record_state(private_row.get("PDF原页核页记录")),
                "湖北官方核验记录状态": record_state(private_row.get("湖北官方核验记录")),
                "结构和官方消歧记录状态": record_state(private_row.get("结构和官方消歧记录")),
                "高校辅证记录状态": record_state(private_row.get("高校辅证记录")),
                "高校辅证是否需要记录": yes_no(school_required),
                "一审记录状态": record_state(private_row.get("核页人A")),
                "二审记录状态": record_state(private_row.get("核页人B")),
                "双人复核记录状态": double_review,
                "私有记录必填项数": str(required_count),
                "私有记录已填项数": str(recorded_count),
                "私有记录未填项数": str(required_count - recorded_count),
                "私有记录填写进度": f"{recorded_count}/{required_count}",
                "页列私有记录进度桶": bucket,
                "页列私有记录进度状态": status,
                "PDF原页核页是否完成": "false",
                "湖北官方核验是否完成": "false",
                "结构和官方消歧是否完成": "false",
                "高校辅证是否完成": "false",
                "页列是否满足升级条件": "false",
                "字段事实写回状态": "blocked_until_private_records_and_fact_review_closed",
                "公开安全策略": (
                    "公开账本只保存页列状态、计数、证据编号和SHA；不公开识别行内容、"
                    "页图路径、学校专业明细、字段值、核页记录内容或补充记录内容。"
                ),
                "下一步": (
                    "在本地私有任务CSV/HTML中补 PDF 原页、湖北官方、结构消歧和必要高校辅证记录；"
                    "公开账本只同步填写状态，不自动认定字段事实。"
                ),
            })

    return output_rows, private_task_row_count


def main():
    rows, private_task_row_count = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    summary = {
        "status": "issue19_page_side_foundation_review_progress_public_ledger_not_final",
        "generated_by": "build_issue19_page_side_foundation_review_progress_ledger.py",
        "source_batch_execution_packets": "data/working/issue19-page-side-foundation-batch-execution-packets.csv",
        "source_page_side_foundation_verification_batches": "data/working/issue19-page-side-foundation-verification-batches.csv",
        "source_private_batch_task_csv": "private_batch_task_csv_not_public",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": "data/working/issue19-page-side-foundation-review-progress-public-ledger.csv",
        "row_count": len(rows),
        "private_task_row_count": private_task_row_count,
        "batch_count": len({row["批次ID"] for row in rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "source_major_line_count": sum(as_int(row["包内专业行数"]) for row in rows),
        "source_field_task_count": sum(as_int(row["包内字段任务数"]) for row in rows),
        "progress_bucket_counts": dict(Counter(row["页列私有记录进度桶"] for row in rows)),
        "pdf_record_status_counts": dict(Counter(row["PDF原页核页记录状态"] for row in rows)),
        "hubei_official_record_status_counts": dict(Counter(row["湖北官方核验记录状态"] for row in rows)),
        "structure_record_status_counts": dict(Counter(row["结构和官方消歧记录状态"] for row in rows)),
        "school_support_required_page_side_count": sum(row["高校辅证是否需要记录"] == "true" for row in rows),
        "school_support_record_status_counts": dict(Counter(row["高校辅证记录状态"] for row in rows)),
        "dual_review_status_counts": dict(Counter(row["双人复核记录状态"] for row in rows)),
        "private_task_csv_sha_status_counts": dict(Counter(row["私有任务CSV_SHA256匹配状态"] for row in rows)),
        "private_required_record_slot_count": sum(as_int(row["私有记录必填项数"]) for row in rows),
        "private_recorded_slot_count": sum(as_int(row["私有记录已填项数"]) for row in rows),
        "private_missing_slot_count": sum(as_int(row["私有记录未填项数"]) for row in rows),
        "pdf_completed_page_side_count": sum(row["PDF原页核页是否完成"] == "true" for row in rows),
        "hubei_official_completed_page_side_count": sum(row["湖北官方核验是否完成"] == "true" for row in rows),
        "structure_completed_page_side_count": sum(row["结构和官方消歧是否完成"] == "true" for row in rows),
        "school_support_completed_page_side_count": sum(row["高校辅证是否完成"] == "true" for row in rows),
        "upgrade_ready_page_side_count": sum(row["页列是否满足升级条件"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "safety_note": (
            "公开账本只保存页列状态、计数、证据编号和SHA；不保存识别行内容、"
            "页图路径、学校专业明细、字段值、核页记录内容或补充记录内容。"
        ),
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
