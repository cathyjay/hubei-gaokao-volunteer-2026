#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PAGE_SIDE_PROGRESS = (
    ROOT / "data/working/issue19-page-side-foundation-review-progress-public-ledger.csv"
)
FIELD_TASKS = ROOT / "data/working/issue19-field-fact-verification-tasks.csv"
ADMISSION_DETAIL = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"

OUTPUT = ROOT / "data/working/issue19-page-side-foundation-field-clue-public-audit.csv"
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-page-side-foundation-field-clue-public-audit-summary.json"
)

PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-page-side-foundation-field-clue-audit"
)
PRIVATE_TASK_DIR = PRIVATE_OUTPUT_DIR / "tasks"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "field-clue-private-index.csv"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_page_side_foundation_field_clue_public_audit"


FIELDS = [
    "页列底座字段线索公开审计ID",
    "来源页列底座公开核页进度账本",
    "来源字段事实核验任务队列",
    "来源私有字段线索模板",
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
    "页列底座核页进度公开账本ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "综合风险优先级桶",
    "页列首要核验动作",
    "包内专业行数",
    "包内字段任务数",
    "字段任务回链数",
    "字段任务缺失数",
    "专业行覆盖数",
    "字段名任务分布",
    "字段核验优先级分布",
    "字段事实状态分布",
    "字段事实阻断等级分布",
    "字段线索状态分布",
    "三字段OCR完整状态分布",
    "字段线索非空任务数",
    "字段线索缺失任务数",
    "字段线索多值或冲突任务数",
    "字段PDF待核任务数",
    "湖北官方待核任务数",
    "高校官网线索任务数",
    "私有字段线索模板批次证据编号",
    "私有字段线索模板CSV_SHA256",
    "私有字段线索模板页列记录数",
    "私有字段线索模板批次记录数",
    "私有字段线索材料状态",
    "PDF原页人工确认完成字段数",
    "湖北官方字段完成字段数",
    "高校辅证字段完成字段数",
    "三方一致性可评估字段数",
    "字段事实写回复查可进入字段数",
    "页列是否满足字段复查条件",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]


PRIVATE_FIELDS = [
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
    "PDF原页候选读数",
    "PDF原页人工确认",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "核页人A",
    "核页人B",
    "一审记录",
    "二审记录",
    "复核备注",
]


PRIVATE_INDEX_FIELDS = [
    "批次总序",
    "批次ID",
    "批次名称",
    "私有字段线索模板相对路径",
    "私有字段线索模板CSV_SHA256",
    "批次页列数",
    "批次字段任务数",
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


def page_side_key(row):
    return str(row.get("来源页码", "")).strip(), str(row.get("版面列", "")).strip()


def counter_text(counter):
    return "；".join(f"{key}:{value}" for key, value in sorted(counter.items())) if counter else ""


def has_conflict_signal(task):
    text = "；".join(
        [
            task.get("字段候选状态集合", ""),
            task.get("字段事实状态", ""),
            task.get("字段事实阻断等级", ""),
            task.get("字段事实缺口类型", ""),
            task.get("字段事实核验动作", ""),
            task.get("字段下一步", ""),
        ]
    )
    return any(token in text for token in ["冲突", "多值", "异常", "疑似"])


def code_bucket(value, fallback="UNK"):
    text = str(value or "").strip()
    if not text:
        return fallback
    return text.split("-", 1)[0]


def clue_status_bucket(value):
    text = str(value or "").strip()
    if not text:
        return "C0-无单独线索状态"
    if "冲突" in text or "多值" in text or "疑似" in text:
        return "C2-冲突或疑似线索"
    if "无候选" in text or "无明确候选" in text:
        return "C1-缺线索"
    if "高校官网" in text:
        return "C3-高校辅证线索"
    if "组级" in text:
        return "C4-组级线索"
    if "OCR" in text:
        return "C5-OCR线索"
    return "C9-其他线索状态"


def tri_field_bucket(value):
    text = str(value or "").strip()
    if "齐全" in text:
        return "T0-三字段线索齐全"
    if "缺1项" in text:
        return "T1-缺1项"
    if "缺2项" in text:
        return "T2-缺2项"
    if "缺3项" in text:
        return "T3-缺3项"
    return "T9-其他完整性状态"


def private_row(progress, task, detail):
    return {
        "批次总序": progress.get("批次总序", ""),
        "批次ID": progress.get("批次ID", ""),
        "批次名称": progress.get("批次名称", ""),
        "来源页码": progress.get("来源页码", ""),
        "版面列": progress.get("版面列", ""),
        "页码版面键": progress.get("页码版面键", ""),
        "页列底座核验批次行ID": progress.get("页列底座核验批次行ID", ""),
        "字段事实核验任务ID": task.get("字段事实核验任务ID", ""),
        "专业行ID": task.get("专业行ID", ""),
        "字段事实闭环ID": task.get("字段事实闭环ID", ""),
        "专业组出现ID": task.get("专业组出现ID", ""),
        "院校代码": task.get("院校代码", ""),
        "院校名称OCR": task.get("院校名称OCR", ""),
        "院校专业组代码OCR规范化": task.get("院校专业组代码OCR规范化", ""),
        "专业组内专业序号": task.get("专业组内专业序号", ""),
        "专业代号OCR": task.get("专业代号OCR", ""),
        "专业名称及备注短摘": task.get("专业名称及备注短摘", ""),
        "字段名": task.get("字段名", ""),
        "字段OCR候选": task.get("字段OCR候选", ""),
        "字段候选值集合": task.get("字段候选值集合", ""),
        "字段候选来源类型集合": task.get("字段候选来源类型集合", ""),
        "字段候选置信等级集合": task.get("字段候选置信等级集合", ""),
        "字段候选状态集合": task.get("字段候选状态集合", ""),
        "字段事实状态": task.get("字段事实状态", ""),
        "字段事实阻断等级": task.get("字段事实阻断等级", ""),
        "字段事实缺口类型": task.get("字段事实缺口类型", ""),
        "字段PDF核验状态": task.get("字段PDF核验状态", ""),
        "字段湖北官方核验状态": task.get("字段湖北官方核验状态", ""),
        "字段事实核验动作": task.get("字段事实核验动作", ""),
        "湖北官方核验包任务ID": task.get("湖北官方核验包任务ID", ""),
        "高校官网证据匹配状态": task.get("高校官网证据匹配状态", ""),
        "B0B1官网证据任务数": task.get("B0B1官网证据任务数", ""),
        "官网证据能否替代湖北官方计划": task.get("官网证据能否替代湖北官方计划", ""),
        "专业起始行号": detail.get("专业起始行号", ""),
        "专业窗口行号范围": detail.get("专业窗口行号范围", ""),
        "窗口坐标摘要": detail.get("窗口坐标摘要", ""),
        "窗口文本SHA256": detail.get("窗口文本SHA256", ""),
        "私有页图证据编号": task.get("私有页图证据编号", ""),
        "私有页图SHA256": task.get("私有页图SHA256", ""),
        "私有OCR文本证据编号": task.get("私有OCR文本证据编号", ""),
        "私有OCR文本SHA256": task.get("私有OCR文本SHA256", ""),
        "PDF原页候选读数": "",
        "PDF原页人工确认": "",
        "湖北官方字段值": "",
        "高校官网或招生章程字段值": "",
        "字段确认值": "",
        "核页人A": "",
        "核页人B": "",
        "一审记录": "",
        "二审记录": "",
        "复核备注": "",
    }


def build_rows():
    progress_rows = read_csv(PAGE_SIDE_PROGRESS)
    field_task_rows = read_csv(FIELD_TASKS)
    detail_rows = read_csv(ADMISSION_DETAIL)
    detail_by_major = {row.get("专业行ID", ""): row for row in detail_rows}

    tasks_by_page_side = defaultdict(list)
    for task in field_task_rows:
        tasks_by_page_side[page_side_key(task)].append(task)
    for tasks in tasks_by_page_side.values():
        tasks.sort(
            key=lambda row: (
                as_int(row.get("页内字段任务序")),
                row.get("专业行ID", ""),
                row.get("字段名", ""),
            )
        )

    progress_by_batch = defaultdict(list)
    for row in progress_rows:
        progress_by_batch[as_int(row.get("批次总序"))].append(row)
    for rows in progress_by_batch.values():
        rows.sort(key=lambda row: as_int(row.get("页列全局风险总序")))

    private_index_rows = []
    private_sha_by_batch = {}
    private_count_by_batch = {}
    for batch_no in sorted(progress_by_batch):
        private_rows = []
        for progress in progress_by_batch[batch_no]:
            for task in tasks_by_page_side.get(page_side_key(progress), []):
                detail = detail_by_major.get(task.get("专业行ID", ""), {})
                private_rows.append(private_row(progress, task, detail))
        private_csv = PRIVATE_TASK_DIR / f"batch-{batch_no:02d}-field-clues.csv"
        write_csv(private_csv, private_rows, PRIVATE_FIELDS)
        private_sha = file_sha(private_csv)
        private_sha_by_batch[batch_no] = private_sha
        private_count_by_batch[batch_no] = len(private_rows)
        first = progress_by_batch[batch_no][0]
        private_index_rows.append({
            "批次总序": str(batch_no),
            "批次ID": first.get("批次ID", ""),
            "批次名称": first.get("批次名称", ""),
            "私有字段线索模板相对路径": str(private_csv.relative_to(PRIVATE_OUTPUT_DIR)),
            "私有字段线索模板CSV_SHA256": private_sha,
            "批次页列数": str(len(progress_by_batch[batch_no])),
            "批次字段任务数": str(len(private_rows)),
        })
    write_csv(PRIVATE_INDEX, private_index_rows, PRIVATE_INDEX_FIELDS)

    output_rows = []
    for progress in progress_rows:
        key = page_side_key(progress)
        tasks = tasks_by_page_side.get(key, [])
        batch_no = as_int(progress.get("批次总序"))
        expected_task_count = as_int(progress.get("包内字段任务数"))
        field_nonempty = sum(
            filled(task.get("字段OCR候选"))
            or filled(task.get("字段候选值集合"))
            or as_int(task.get("字段非空候选数")) > 0
            for task in tasks
        )
        field_conflicts = sum(has_conflict_signal(task) for task in tasks)
        pdf_pending = sum(
            task.get("字段PDF核验状态", "") == "pending_original_pdf_page_review"
            or "pending" in task.get("字段PDF核验状态", "")
            or not task.get("字段PDF核验状态", "")
            for task in tasks
        )
        official_pending = sum(
            task.get("字段湖北官方核验状态", "") == "pending_hubei_official_plan_review"
            or "pending" in task.get("字段湖北官方核验状态", "")
            or not task.get("字段湖北官方核验状态", "")
            for task in tasks
        )
        school_clue_tasks = sum(as_int(task.get("B0B1官网证据任务数")) > 0 for task in tasks)
        output_rows.append({
            "页列底座字段线索公开审计ID": stable_id(
                "PSFIELDCLUE", [progress.get("页列底座核验批次行ID", ""), batch_no]
            ),
            "来源页列底座公开核页进度账本": "data/working/issue19-page-side-foundation-review-progress-public-ledger.csv",
            "来源字段事实核验任务队列": "data/working/issue19-field-fact-verification-tasks.csv",
            "来源私有字段线索模板": "private_field_clue_templates_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×字段线索状态审计",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动标记核验完成": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "批次总序": progress.get("批次总序", ""),
            "批次ID": progress.get("批次ID", ""),
            "批次名称": progress.get("批次名称", ""),
            "批内页列序号": progress.get("批内页列序号", ""),
            "页列全局风险总序": progress.get("页列全局风险总序", ""),
            "页列底座核验批次行ID": progress.get("页列底座核验批次行ID", ""),
            "页列底座核页进度公开账本ID": progress.get("页列底座核页进度公开账本ID", ""),
            "来源页码": progress.get("来源页码", ""),
            "版面列": progress.get("版面列", ""),
            "页码版面键": progress.get("页码版面键", ""),
            "综合风险优先级桶": progress.get("综合风险优先级桶", ""),
            "页列首要核验动作": progress.get("页列首要核验动作", ""),
            "包内专业行数": progress.get("包内专业行数", ""),
            "包内字段任务数": progress.get("包内字段任务数", ""),
            "字段任务回链数": str(len(tasks)),
            "字段任务缺失数": str(max(expected_task_count - len(tasks), 0)),
            "专业行覆盖数": str(len({task.get("专业行ID", "") for task in tasks if task.get("专业行ID", "")})),
            "字段名任务分布": counter_text(Counter(task.get("字段名", "") for task in tasks)),
            "字段核验优先级分布": counter_text(Counter(code_bucket(task.get("字段核验优先级", "")) for task in tasks)),
            "字段事实状态分布": counter_text(Counter(code_bucket(task.get("字段事实状态", "")) for task in tasks)),
            "字段事实阻断等级分布": counter_text(Counter(code_bucket(task.get("字段事实阻断等级", "")) for task in tasks)),
            "字段线索状态分布": counter_text(Counter(clue_status_bucket(task.get("字段候选状态集合", "")) for task in tasks)),
            "三字段OCR完整状态分布": counter_text(Counter(tri_field_bucket(task.get("三字段OCR完整状态", "")) for task in tasks)),
            "字段线索非空任务数": str(field_nonempty),
            "字段线索缺失任务数": str(len(tasks) - field_nonempty),
            "字段线索多值或冲突任务数": str(field_conflicts),
            "字段PDF待核任务数": str(pdf_pending),
            "湖北官方待核任务数": str(official_pending),
            "高校官网线索任务数": str(school_clue_tasks),
            "私有字段线索模板批次证据编号": f"ps-field-clue-batch-{batch_no:02d}-csv",
            "私有字段线索模板CSV_SHA256": private_sha_by_batch.get(batch_no, ""),
            "私有字段线索模板页列记录数": str(len(tasks)),
            "私有字段线索模板批次记录数": str(private_count_by_batch.get(batch_no, 0)),
            "私有字段线索材料状态": "private_field_clue_template_generated",
            "PDF原页人工确认完成字段数": "0",
            "湖北官方字段完成字段数": "0",
            "高校辅证字段完成字段数": "0",
            "三方一致性可评估字段数": "0",
            "字段事实写回复查可进入字段数": "0",
            "页列是否满足字段复查条件": "false",
            "字段事实写回状态": "blocked_until_pdf_hubei_and_required_school_evidence_closed",
            "公开安全策略": (
                "公开表只保存页列字段任务计数、状态分布、证据编号和SHA；"
                "不公开具体读数、识别行内容、页图路径、学校专业明细或人工填写内容。"
            ),
            "下一步": (
                "在本地私有字段线索模板中核 PDF 原页和湖北官方侧；"
                "所有线索都保持待人工核验，不自动写回字段事实。"
            ),
        })
    return output_rows, private_index_rows


def main():
    rows, private_index_rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    field_name_counts = Counter()
    field_priority_counts = Counter()
    clue_status_counts = Counter()
    for row in rows:
        for item in row["字段名任务分布"].split("；"):
            if ":" in item:
                key, count = item.rsplit(":", 1)
                field_name_counts[key] += as_int(count)
        for item in row["字段核验优先级分布"].split("；"):
            if ":" in item:
                key, count = item.rsplit(":", 1)
                field_priority_counts[key] += as_int(count)
        for item in row["字段线索状态分布"].split("；"):
            if ":" in item:
                key, count = item.rsplit(":", 1)
                clue_status_counts[key] += as_int(count)

    summary = {
        "status": "issue19_page_side_foundation_field_clue_public_audit_not_final",
        "generated_by": "build_issue19_page_side_foundation_field_clue_audit.py",
        "source_page_side_progress": "data/working/issue19-page-side-foundation-review-progress-public-ledger.csv",
        "source_field_fact_verification_tasks": "data/working/issue19-field-fact-verification-tasks.csv",
        "source_private_field_clue_templates": "private_field_clue_templates_not_public",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": "data/working/issue19-page-side-foundation-field-clue-public-audit.csv",
        "row_count": len(rows),
        "batch_count": len({row["批次ID"] for row in rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "source_major_line_count": sum(as_int(row["包内专业行数"]) for row in rows),
        "source_field_task_count": sum(as_int(row["包内字段任务数"]) for row in rows),
        "linked_field_task_count": sum(as_int(row["字段任务回链数"]) for row in rows),
        "missing_field_task_count": sum(as_int(row["字段任务缺失数"]) for row in rows),
        "private_field_clue_template_count": len(private_index_rows),
        "private_field_clue_template_row_count": sum(as_int(row["批次字段任务数"]) for row in private_index_rows),
        "private_index_csv_sha256": file_sha(PRIVATE_INDEX),
        "field_name_counts": dict(field_name_counts),
        "field_priority_counts": dict(field_priority_counts),
        "clue_status_counts": dict(clue_status_counts),
        "field_clue_nonempty_task_count": sum(as_int(row["字段线索非空任务数"]) for row in rows),
        "field_clue_missing_task_count": sum(as_int(row["字段线索缺失任务数"]) for row in rows),
        "field_clue_conflict_task_count": sum(as_int(row["字段线索多值或冲突任务数"]) for row in rows),
        "pdf_pending_task_count": sum(as_int(row["字段PDF待核任务数"]) for row in rows),
        "hubei_official_pending_task_count": sum(as_int(row["湖北官方待核任务数"]) for row in rows),
        "school_website_clue_task_count": sum(as_int(row["高校官网线索任务数"]) for row in rows),
        "pdf_confirmed_task_count": 0,
        "hubei_official_confirmed_task_count": 0,
        "school_support_confirmed_task_count": 0,
        "field_writeback_review_ready_task_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "safety_note": (
            "公开表只保存页列字段任务计数、状态分布、证据编号和SHA；"
            "不保存具体读数、识别行内容、页图路径、学校专业明细或人工填写内容。"
        ),
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出私有字段线索模板：{PRIVATE_OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
