#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIELD_FACT_TASKS = ROOT / "data/working/issue19-field-fact-verification-tasks.csv"
PAGE_FIDELITY_QUEUE = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"

OUTPUT = ROOT / "data/working/issue19-field-fact-page-side-verification-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-fact-page-side-verification-queue-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_field_fact_page_side_verification_queue"


FIELDS = [
    "全量字段页列核验队列ID",
    "来源字段事实核验任务队列",
    "来源页级保真复核队列",
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
    "页列核验优先级桶",
    "页列核验优先级数值",
    "页列首要动作",
    "包内字段任务数",
    "包内专业行数",
    "包内专业组数",
    "包内院校代码数",
    "包内字段名分布",
    "包内字段核验优先级分布",
    "包内字段事实阻断等级分布",
    "包内Q0无候选阻断任务数",
    "包内Q1有候选待人工核验任务数",
    "包内Q2OCR齐全待三方闭环任务数",
    "包内专业计划数字段任务数",
    "包内学费字段任务数",
    "包内再选科目字段任务数",
    "包内PDF原页核验待完成任务数",
    "包内湖北官方核验待完成任务数",
    "包内高校官网辅证线索任务数",
    "包内源证据P0任务数",
    "包内源证据P1任务数",
    "页面复核优先级",
    "页面阻断等级",
    "页级保真队列ID",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有识别材料证据编号",
    "私有识别材料SHA256",
    "OCR平均置信度",
    "OCR_QC_P0数",
    "OCR_QC_P1数",
    "页面专业明细数",
    "页面结构异常数",
    "页面高严重结构异常数",
    "字段任务ID集合SHA256",
    "专业行ID集合SHA256",
    "专业组出现ID集合SHA256",
    "院校代码集合SHA256",
    "下钻筛选键",
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


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def counter_text(counter):
    return "；".join(f"{key}:{value}" for key, value in sorted(counter.items())) if counter else ""


def sha_list(values):
    normalized = "；".join(sorted({value for value in values if value}))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except ValueError:
        return default


def priority_for_rows(rows):
    block_counts = Counter(row["字段事实阻断等级"] for row in rows)
    if block_counts.get("Q0-字段缺口无候选阻断", 0):
        return (
            "V0-Q0无候选阻断页列先核",
            0,
            "先按页列重读无候选字段，优先补专业计划数、再选科目和学费缺口。",
        )
    if block_counts.get("Q1-字段缺口有候选待人工核验", 0):
        return (
            "V1-Q1有候选待人工核验页列",
            1,
            "核对已有候选字段，候选不得自动写回，仍需 PDF 原页和湖北官方闭环。",
        )
    return (
        "V2-Q2 OCR齐全待三方闭环页列",
        2,
        "OCR 三字段齐全但仍需 PDF 原页、湖北官方系统和必要官网章程闭环。",
    )


def pending_count(rows, field, expected):
    return sum(row.get(field) == expected for row in rows)


def build_rows():
    task_rows = read_csv(FIELD_FACT_TASKS)
    page_rows = read_csv(PAGE_FIDELITY_QUEUE)
    page_by_number = {row["PDF页码"]: row for row in page_rows}

    rows_by_page_side = defaultdict(list)
    for row in task_rows:
        rows_by_page_side[(row["来源页码"], row["版面列"])].append(row)

    queue_rows = []
    for (page, side), rows in rows_by_page_side.items():
        page_row = page_by_number.get(page)
        if not page_row:
            raise RuntimeError(f"missing page fidelity row for page {page}")
        bucket, priority, action = priority_for_rows(rows)
        field_counts = Counter(row["字段名"] for row in rows)
        verification_priority_counts = Counter(row["字段核验优先级"] for row in rows)
        block_counts = Counter(row["字段事实阻断等级"] for row in rows)
        source_evidence_priority_counts = Counter(row["源证据核页优先级"] for row in rows)
        queue_rows.append({
            "全量字段页列核验队列ID": stable_id("FIELDPSIDE", [page, side]),
            "来源字段事实核验任务队列": "data/working/issue19-field-fact-verification-tasks.csv",
            "来源页级保真复核队列": "data/working/issue19-page-fidelity-review-queue.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×全量字段事实核验任务",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "页列执行总序": "",
            "来源页码": page,
            "版面列": side,
            "页码版面键": f"{int(page):03d}-{side}",
            "页列核验优先级桶": bucket,
            "页列核验优先级数值": str(priority),
            "页列首要动作": action,
            "包内字段任务数": str(len(rows)),
            "包内专业行数": str(len({row["专业行ID"] for row in rows})),
            "包内专业组数": str(len({row["专业组出现ID"] for row in rows})),
            "包内院校代码数": str(len({row["院校代码"] for row in rows})),
            "包内字段名分布": counter_text(field_counts),
            "包内字段核验优先级分布": counter_text(verification_priority_counts),
            "包内字段事实阻断等级分布": counter_text(block_counts),
            "包内Q0无候选阻断任务数": str(block_counts.get("Q0-字段缺口无候选阻断", 0)),
            "包内Q1有候选待人工核验任务数": str(block_counts.get("Q1-字段缺口有候选待人工核验", 0)),
            "包内Q2OCR齐全待三方闭环任务数": str(block_counts.get("Q2-OCR字段齐全但PDF和官方未闭环", 0)),
            "包内专业计划数字段任务数": str(field_counts.get("专业计划数", 0)),
            "包内学费字段任务数": str(field_counts.get("学费", 0)),
            "包内再选科目字段任务数": str(field_counts.get("再选科目", 0)),
            "包内PDF原页核验待完成任务数": str(pending_count(
                rows, "字段PDF核验状态", "has_page_hash_pending_manual_pdf_review"
            )),
            "包内湖北官方核验待完成任务数": str(pending_count(
                rows, "字段湖北官方核验状态", "pending_hubei_official_plan_review"
            )),
            "包内高校官网辅证线索任务数": str(sum(as_int(row.get("B0B1官网证据任务数")) > 0 for row in rows)),
            "包内源证据P0任务数": str(source_evidence_priority_counts.get("P0-源证据阻断级先核", 0)),
            "包内源证据P1任务数": str(source_evidence_priority_counts.get("P1-源证据优先复核", 0)),
            "页面复核优先级": page_row["页面复核优先级"],
            "页面阻断等级": page_row["页面阻断等级"],
            "页级保真队列ID": page_row["页级保真队列ID"],
            "私有页图证据编号": page_row["私有页图证据编号"],
            "私有页图SHA256": page_row["私有页图SHA256"],
            "私有识别材料证据编号": page_row["私有OCR文本证据编号"],
            "私有识别材料SHA256": page_row["私有OCR文本SHA256"],
            "OCR平均置信度": page_row["OCR平均置信度"],
            "OCR_QC_P0数": page_row["OCR_QC_P0数"],
            "OCR_QC_P1数": page_row["OCR_QC_P1数"],
            "页面专业明细数": page_row["页面专业明细数"],
            "页面结构异常数": page_row["页面结构异常数"],
            "页面高严重结构异常数": page_row["页面高严重结构异常数"],
            "字段任务ID集合SHA256": sha_list(row["字段事实核验任务ID"] for row in rows),
            "专业行ID集合SHA256": sha_list(row["专业行ID"] for row in rows),
            "专业组出现ID集合SHA256": sha_list(row["专业组出现ID"] for row in rows),
            "院校代码集合SHA256": sha_list(row["院校代码"] for row in rows),
            "下钻筛选键": f"来源页码={page}；版面列={side}",
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "字段事实写回状态": "blocked_until_pdf_and_hubei_official_fields_verified",
            "公开安全策略": (
                "只公开页列执行顺序、任务数量、状态、证据编号、SHA和任务集合哈希；"
                "不公开字段候选值、人工确认值、私有识别材料、图片路径、院校名、专业名、专业代号或专业组代码。"
            ),
            "下一步": f"{action} 完成后仍需湖北官方系统或省招办计划核验。",
        })

    queue_rows.sort(
        key=lambda row: (
            as_int(row["页列核验优先级数值"]),
            -as_int(row["包内Q0无候选阻断任务数"]),
            -as_int(row["包内Q1有候选待人工核验任务数"]),
            -as_int(row["包内字段任务数"]),
            as_int(row["来源页码"]),
            0 if row["版面列"] == "left" else 1,
        )
    )
    for idx, row in enumerate(queue_rows, start=1):
        row["页列执行总序"] = str(idx)
    return queue_rows, task_rows


def main():
    queue_rows, task_rows = build_rows()
    write_csv(OUTPUT, queue_rows, FIELDS)

    block_counts = Counter(row["字段事实阻断等级"] for row in task_rows)
    field_counts = Counter(row["字段名"] for row in task_rows)
    priority_counts = Counter(row["页列核验优先级桶"] for row in queue_rows)
    summary = {
        "status": "issue19_field_fact_page_side_verification_queue_not_final",
        "generated_by": "build_issue19_field_fact_page_side_verification_queue.py",
        "source_field_fact_verification_tasks": "data/working/issue19-field-fact-verification-tasks.csv",
        "source_page_fidelity_review_queue": "data/working/issue19-page-fidelity-review-queue.csv",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": "data/working/issue19-field-fact-page-side-verification-queue.csv",
        "row_count": len(queue_rows),
        "source_field_task_count": len(task_rows),
        "unique_pdf_page_count": len({row["来源页码"] for row in queue_rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in queue_rows}),
        "unique_major_line_count": len({row["专业行ID"] for row in task_rows}),
        "field_counts": dict(field_counts),
        "field_block_counts": dict(block_counts),
        "page_side_priority_counts": dict(priority_counts),
        "pdf_manual_review_required_task_count": sum(
            row["字段PDF核验状态"] == "has_page_hash_pending_manual_pdf_review"
            for row in task_rows
        ),
        "hubei_official_review_required_task_count": sum(
            row["字段湖北官方核验状态"] == "pending_hubei_official_plan_review"
            for row in task_rows
        ),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "safety_note": (
            "公开队列只保存页列执行顺序、任务数量、状态、证据编号、SHA和任务集合哈希；"
            "不保存字段候选值、人工确认值、私有识别材料、图片路径、院校名、专业名、专业代号或专业组代码。"
        ),
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(queue_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
