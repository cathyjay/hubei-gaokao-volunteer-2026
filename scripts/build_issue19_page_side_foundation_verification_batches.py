#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_REGISTER = ROOT / "data/working/issue19-page-side-foundation-risk-register.csv"
FIELD_PAGE_SIDE_QUEUE = ROOT / "data/working/issue19-field-fact-page-side-verification-queue.csv"
OUTPUT = ROOT / "data/working/issue19-page-side-foundation-verification-batches.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-page-side-foundation-verification-batches-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_page_side_foundation_verification_batches"
BATCH_SIZE = 25


FIELDS = [
    "页列底座核验批次行ID",
    "来源页列底座综合风险登记表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "批次总序",
    "批次ID",
    "批次名称",
    "批次容量上限",
    "批内页列序号",
    "页列全局风险总序",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列底座综合风险登记ID",
    "综合风险优先级桶",
    "综合风险优先级数值",
    "页列首要核验动作",
    "批次执行线",
    "批次页列数",
    "批次专业行数",
    "批次字段任务数",
    "批次Z0页列数",
    "批次Z1页列数",
    "批次Z2页列数",
    "批次Z3页列数",
    "批次结构R0专业行数",
    "批次源证据X1专业行数",
    "批次源证据X2专业行数",
    "批次官方查询键碰撞行数",
    "批次字段Q0任务数",
    "包内专业行数",
    "包内字段任务数",
    "字段Q0无候选阻断任务数",
    "字段Q1有候选待人工核验任务数",
    "字段Q2待三方闭环任务数",
    "结构R0专业行数",
    "结构R1专业行数",
    "结构R2专业行数",
    "结构R3专业行数",
    "结构风险事件数",
    "版面风险事件数",
    "专业代号风险事件数",
    "官方查询键碰撞行数",
    "教育部未匹配校名专业行数",
    "官网辅证线索行数",
    "官网计划数冲突行数",
    "决策G0结构或归属未闭环行数",
    "决策G1家庭底线风险待确认行数",
    "决策G2字段缺口未闭环行数",
    "源证据X1专业窗口P0行数",
    "源证据X2起始行P0_QC行数",
    "源证据X3优先复核行数",
    "源证据X4低风险抽检行数",
    "专业行ID集合SHA256",
    "字段任务集合SHA256",
    "风险登记ID集合SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "结构和官方消歧状态",
    "高校官网或招生章程辅证状态",
    "字段事实写回状态",
    "批次完成状态",
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


def sha_list(values):
    normalized = "；".join(sorted({value for value in values if value}))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def batch_line(row):
    bucket = row.get("综合风险优先级桶", "")
    if bucket.startswith("Z0"):
        return "L0-结构源证据官方消歧先核"
    if bucket.startswith("Z1"):
        return "L1-字段缺口结构风险并行核"
    if bucket.startswith("Z2"):
        return "L2-候选字段辅证线索核验"
    return "L3-常规三方闭环抽检"


def sum_field(rows, field):
    return sum(as_int(row.get(field)) for row in rows)


def build_rows():
    source_rows = read_csv(SOURCE_REGISTER)
    field_page_rows = read_csv(FIELD_PAGE_SIDE_QUEUE)
    field_page_by_side = {
        (row.get("来源页码", ""), row.get("版面列", "")): row
        for row in field_page_rows
    }
    rows_by_batch = defaultdict(list)
    for index, row in enumerate(source_rows, start=1):
        batch_no = (index - 1) // BATCH_SIZE + 1
        rows_by_batch[batch_no].append(row)

    batch_totals = {}
    for batch_no, batch_rows in rows_by_batch.items():
        priority_counts = Counter(row.get("综合风险优先级桶", "") for row in batch_rows)
        batch_totals[batch_no] = {
            "批次页列数": len(batch_rows),
            "批次专业行数": sum_field(batch_rows, "包内专业行数"),
            "批次字段任务数": sum_field(batch_rows, "包内字段任务数"),
            "批次Z0页列数": sum(
                count for bucket, count in priority_counts.items() if bucket.startswith("Z0")
            ),
            "批次Z1页列数": sum(
                count for bucket, count in priority_counts.items() if bucket.startswith("Z1")
            ),
            "批次Z2页列数": sum(
                count for bucket, count in priority_counts.items() if bucket.startswith("Z2")
            ),
            "批次Z3页列数": sum(
                count for bucket, count in priority_counts.items() if bucket.startswith("Z3")
            ),
            "批次结构R0专业行数": sum_field(batch_rows, "结构R0专业行数"),
            "批次源证据X1专业行数": sum_field(batch_rows, "源证据X1专业窗口P0行数"),
            "批次源证据X2专业行数": sum_field(batch_rows, "源证据X2起始行P0_QC行数"),
            "批次官方查询键碰撞行数": sum_field(batch_rows, "官方查询键碰撞行数"),
            "批次字段Q0任务数": sum_field(batch_rows, "字段Q0无候选阻断任务数"),
        }

    output_rows = []
    for index, source in enumerate(source_rows, start=1):
        field_page_row = field_page_by_side.get(
            (source.get("来源页码", ""), source.get("版面列", "")),
            {},
        )
        batch_no = (index - 1) // BATCH_SIZE + 1
        batch_id = stable_id("PSFOUNDATIONBATCH", [batch_no, BATCH_SIZE, SOURCE_PDF_SHA256])
        batch_name = f"第{batch_no:02d}批-页列底座核验"
        batch_rows = rows_by_batch[batch_no]
        totals = batch_totals[batch_no]
        row = {
            "页列底座核验批次行ID": stable_id(
                "PSFOUNDATIONBATCHROW",
                [batch_id, source.get("页列底座综合风险登记ID", "")],
            ),
            "来源页列底座综合风险登记表": "data/working/issue19-page-side-foundation-risk-register.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×底座核验批次",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "批次总序": str(batch_no),
            "批次ID": batch_id,
            "批次名称": batch_name,
            "批次容量上限": str(BATCH_SIZE),
            "批内页列序号": str((index - 1) % BATCH_SIZE + 1),
            "页列全局风险总序": source.get("页列综合风险总序", ""),
            "来源页码": source.get("来源页码", ""),
            "版面列": source.get("版面列", ""),
            "页码版面键": source.get("页码版面键", ""),
            "页列底座综合风险登记ID": source.get("页列底座综合风险登记ID", ""),
            "综合风险优先级桶": source.get("综合风险优先级桶", ""),
            "综合风险优先级数值": source.get("综合风险优先级数值", ""),
            "页列首要核验动作": source.get("页列首要核验动作", ""),
            "批次执行线": batch_line(source),
            "批次页列数": str(totals["批次页列数"]),
            "批次专业行数": str(totals["批次专业行数"]),
            "批次字段任务数": str(totals["批次字段任务数"]),
            "批次Z0页列数": str(totals["批次Z0页列数"]),
            "批次Z1页列数": str(totals["批次Z1页列数"]),
            "批次Z2页列数": str(totals["批次Z2页列数"]),
            "批次Z3页列数": str(totals["批次Z3页列数"]),
            "批次结构R0专业行数": str(totals["批次结构R0专业行数"]),
            "批次源证据X1专业行数": str(totals["批次源证据X1专业行数"]),
            "批次源证据X2专业行数": str(totals["批次源证据X2专业行数"]),
            "批次官方查询键碰撞行数": str(totals["批次官方查询键碰撞行数"]),
            "批次字段Q0任务数": str(totals["批次字段Q0任务数"]),
            "包内专业行数": source.get("包内专业行数", ""),
            "包内字段任务数": source.get("包内字段任务数", ""),
            "字段Q0无候选阻断任务数": source.get("字段Q0无候选阻断任务数", ""),
            "字段Q1有候选待人工核验任务数": source.get("字段Q1有候选待人工核验任务数", ""),
            "字段Q2待三方闭环任务数": source.get("字段Q2待三方闭环任务数", ""),
            "结构R0专业行数": source.get("结构R0专业行数", ""),
            "结构R1专业行数": source.get("结构R1专业行数", ""),
            "结构R2专业行数": source.get("结构R2专业行数", ""),
            "结构R3专业行数": source.get("结构R3专业行数", ""),
            "结构风险事件数": source.get("结构风险事件数", ""),
            "版面风险事件数": source.get("版面风险事件数", ""),
            "专业代号风险事件数": source.get("专业代号风险事件数", ""),
            "官方查询键碰撞行数": source.get("官方查询键碰撞行数", ""),
            "教育部未匹配校名专业行数": source.get("教育部未匹配校名专业行数", ""),
            "官网辅证线索行数": source.get("官网辅证线索行数", ""),
            "官网计划数冲突行数": source.get("官网计划数冲突行数", ""),
            "决策G0结构或归属未闭环行数": source.get("决策G0结构或归属未闭环行数", ""),
            "决策G1家庭底线风险待确认行数": source.get("决策G1家庭底线风险待确认行数", ""),
            "决策G2字段缺口未闭环行数": source.get("决策G2字段缺口未闭环行数", ""),
            "源证据X1专业窗口P0行数": source.get("源证据X1专业窗口P0行数", ""),
            "源证据X2起始行P0_QC行数": source.get("源证据X2起始行P0_QC行数", ""),
            "源证据X3优先复核行数": source.get("源证据X3优先复核行数", ""),
            "源证据X4低风险抽检行数": source.get("源证据X4低风险抽检行数", ""),
            "专业行ID集合SHA256": source.get("专业行ID集合SHA256", ""),
            "字段任务集合SHA256": field_page_row.get("字段任务ID集合SHA256", ""),
            "风险登记ID集合SHA256": sha_list(
                row.get("页列底座综合风险登记ID", "") for row in batch_rows
            ),
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "结构和官方消歧状态": "pending_structure_and_official_key_review",
            "高校官网或招生章程辅证状态": "pending_if_school_clue_present",
            "字段事实写回状态": "blocked_until_batch_evidence_closed",
            "批次完成状态": "R0-未开始页列底座核验",
            "公开安全策略": (
                "只公开批次、页列、风险计数、集合SHA和非最终门禁；"
                "不公开学校专业明细、字段读数、人工记录、图片路径或私有识别材料。"
            ),
            "下一步": (
                f"{batch_name} 内先按页列风险顺序核 PDF 原页、湖北官方侧和必要高校辅证；"
                "完成前不得写回字段事实或进入志愿推荐。"
            ),
        }
        output_rows.append(row)

    return output_rows


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    priority_counts = Counter(row["综合风险优先级桶"] for row in rows)
    line_counts = Counter(row["批次执行线"] for row in rows)
    batch_counts = Counter(row["批次完成状态"] for row in rows)
    summary = {
        "status": "issue19_page_side_foundation_verification_batches_not_final",
        "generated_by": "build_issue19_page_side_foundation_verification_batches.py",
        "source_page_side_foundation_risk_register": "data/working/issue19-page-side-foundation-risk-register.csv",
        "source_field_page_side_queue": "data/working/issue19-field-fact-page-side-verification-queue.csv",
        "output_table": "data/working/issue19-page-side-foundation-verification-batches.csv",
        "row_count": len(rows),
        "batch_size": BATCH_SIZE,
        "batch_count": len({row["批次ID"] for row in rows}),
        "unique_batch_row_id_count": len({row["页列底座核验批次行ID"] for row in rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "source_major_line_count": sum(as_int(row["包内专业行数"]) for row in rows),
        "source_field_task_count": sum(as_int(row["包内字段任务数"]) for row in rows),
        "priority_bucket_counts": dict(priority_counts),
        "execution_line_counts": dict(line_counts),
        "batch_status_counts": dict(batch_counts),
        "field_q0_task_count": sum(as_int(row["字段Q0无候选阻断任务数"]) for row in rows),
        "field_q1_task_count": sum(as_int(row["字段Q1有候选待人工核验任务数"]) for row in rows),
        "field_q2_task_count": sum(as_int(row["字段Q2待三方闭环任务数"]) for row in rows),
        "structural_r0_major_line_count": sum(as_int(row["结构R0专业行数"]) for row in rows),
        "source_x1_count": sum(as_int(row["源证据X1专业窗口P0行数"]) for row in rows),
        "source_x2_count": sum(as_int(row["源证据X2起始行P0_QC行数"]) for row in rows),
        "official_key_collision_row_count": sum(as_int(row["官方查询键碰撞行数"]) for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "safety_note": (
            "公开表只保存批次、页列、风险计数、集合SHA和非最终门禁；"
            "不保存学校专业明细、字段读数、人工记录、图片路径或私有识别材料。"
        ),
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
