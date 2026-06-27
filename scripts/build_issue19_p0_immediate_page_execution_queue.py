#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PAGE_REVIEW_PACKETS = ROOT / "data/working/issue19-p0-immediate-page-review-packets.csv"
PDF_READING_CANDIDATES = (
    ROOT / "data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv"
)

OUTPUT = ROOT / "data/working/issue19-p0-immediate-page-execution-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-p0-immediate-page-execution-queue-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_p0_immediate_page_execution_queue"


FIELDS = [
    "P0即时页列核页执行队列ID",
    "来源P0即时按页核页包",
    "来源P0即时PDF原页候选公开审计",
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
    "P0即时按页核页包ID",
    "页列核页优先级桶",
    "页列核页优先级数值",
    "页列首要动作",
    "包内字段任务数",
    "包内专业行数",
    "包内裁图证据数",
    "包内字段名分布",
    "包内PDF原页候选审阅桶分布",
    "包内P0候选冲突任务数",
    "包内P1候选一致仍需官方任务数",
    "包内P2有候选人工确认任务数",
    "包内P3无稳定候选任务数",
    "包内私有候选已挂线索任务数",
    "包内需要人工直接看图任务数",
    "包内需要双人复核任务数",
    "包内高校辅证核验任务数",
    "包内机器线索一致任务数",
    "包内机器线索冲突任务数",
    "包内高校线索一致任务数",
    "包内高校线索冲突任务数",
    "包内专业计划数字段任务数",
    "包内学费字段任务数",
    "包内再选科目字段任务数",
    "P0即时PDF原页候选公开审计ID集合",
    "P0即时字段确认公开账本ID集合",
    "P0即时裁图OCR公开审计ID集合",
    "P0字段即时复核任务ID集合",
    "裁图证据编号集合",
    "裁图文件SHA256集合",
    "裁图规格SHA256集合",
    "裁图bbox归一化集合",
    "私有审阅HTML证据编号",
    "私有审阅HTML_SHA256",
    "私有审阅任务CSV_SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
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


def join_unique(rows, field):
    values = []
    seen = set()
    for row in rows:
        value = row.get(field, "")
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return "；".join(values)


def as_int(value, default=999999):
    try:
        return int(str(value).strip())
    except ValueError:
        return default


def priority_for_rows(rows):
    buckets = Counter(row["PDF原页候选审阅桶"] for row in rows)
    if buckets.get("P0-候选冲突优先核图", 0):
        return "Q0-候选冲突页列先核", 0, "先核候选冲突字段；同页同列字段一次性看完。"
    if buckets.get("P3-无稳定候选需人工看图", 0):
        return "Q1-无稳定候选页列先核", 1, "先人工看图补读无稳定候选字段；同页同列字段一次性看完。"
    if buckets.get("P1-候选与既有线索一致仍需核官方", 0):
        return "Q2-候选一致仍需官方闭环", 2, "候选与既有线索一致但仍需 PDF 原页和湖北官方核验。"
    return "Q3-常规候选人工确认", 3, "按页列常规核 PDF 原页，候选不得自动写入人工读数。"


def build_rows():
    packet_rows = read_csv(PAGE_REVIEW_PACKETS)
    candidate_rows = read_csv(PDF_READING_CANDIDATES)

    packet_by_id = {row["P0即时按页核页包ID"]: row for row in packet_rows}
    candidates_by_packet = defaultdict(list)
    for row in candidate_rows:
        candidates_by_packet[row["P0即时按页核页包ID"]].append(row)

    queue_rows = []
    for packet_id, packet in packet_by_id.items():
        rows = candidates_by_packet[packet_id]
        if not rows:
            raise RuntimeError(f"missing candidate rows for {packet_id}")
        bucket, priority, action = priority_for_rows(rows)
        bucket_counts = Counter(row["PDF原页候选审阅桶"] for row in rows)
        field_counts = Counter(row["字段名"] for row in rows)
        queue_rows.append({
            "P0即时页列核页执行队列ID": stable_id(
                "P0PAGEEXEC", [packet_id, packet["来源页码"], packet["版面列"]]
            ),
            "来源P0即时按页核页包": "data/working/issue19-p0-immediate-page-review-packets.csv",
            "来源P0即时PDF原页候选公开审计": (
                "data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv"
            ),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×P0即时PDF原页候选核页执行队列",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "页列执行总序": "",
            "来源页码": packet["来源页码"],
            "版面列": packet["版面列"],
            "页码版面键": packet["页码版面键"],
            "P0即时按页核页包ID": packet_id,
            "页列核页优先级桶": bucket,
            "页列核页优先级数值": str(priority),
            "页列首要动作": action,
            "包内字段任务数": str(len(rows)),
            "包内专业行数": str(len({row["专业行ID"] for row in rows})),
            "包内裁图证据数": str(len({row["裁图证据编号"] for row in rows})),
            "包内字段名分布": counter_text(field_counts),
            "包内PDF原页候选审阅桶分布": counter_text(bucket_counts),
            "包内P0候选冲突任务数": str(bucket_counts.get("P0-候选冲突优先核图", 0)),
            "包内P1候选一致仍需官方任务数": str(bucket_counts.get("P1-候选与既有线索一致仍需核官方", 0)),
            "包内P2有候选人工确认任务数": str(bucket_counts.get("P2-有候选但需人工确认", 0)),
            "包内P3无稳定候选任务数": str(bucket_counts.get("P3-无稳定候选需人工看图", 0)),
            "包内私有候选已挂线索任务数": str(sum(
                row["是否已有私有PDF原页候选"] == "true" for row in rows
            )),
            "包内需要人工直接看图任务数": str(sum(
                row["是否需要人工直接看图"] == "true" for row in rows
            )),
            "包内需要双人复核任务数": str(sum(row["是否需要双人复核"] == "true" for row in rows)),
            "包内高校辅证核验任务数": str(sum(row["是否仍需高校辅证核验"] == "true" for row in rows)),
            "包内机器线索一致任务数": str(sum(row["是否候选与机器线索一致"] == "true" for row in rows)),
            "包内机器线索冲突任务数": str(sum(row["是否候选与机器线索冲突"] == "true" for row in rows)),
            "包内高校线索一致任务数": str(sum(row["是否候选与高校线索一致"] == "true" for row in rows)),
            "包内高校线索冲突任务数": str(sum(row["是否候选与高校线索冲突"] == "true" for row in rows)),
            "包内专业计划数字段任务数": str(field_counts.get("专业计划数", 0)),
            "包内学费字段任务数": str(field_counts.get("学费", 0)),
            "包内再选科目字段任务数": str(field_counts.get("再选科目", 0)),
            "P0即时PDF原页候选公开审计ID集合": join_unique(
                rows, "P0即时PDF原页候选公开审计ID"
            ),
            "P0即时字段确认公开账本ID集合": join_unique(rows, "P0即时字段确认公开账本ID"),
            "P0即时裁图OCR公开审计ID集合": join_unique(rows, "P0即时裁图OCR公开审计ID"),
            "P0字段即时复核任务ID集合": join_unique(rows, "P0字段即时复核任务ID"),
            "裁图证据编号集合": join_unique(rows, "裁图证据编号"),
            "裁图文件SHA256集合": join_unique(rows, "裁图文件SHA256"),
            "裁图规格SHA256集合": join_unique(rows, "裁图规格SHA256"),
            "裁图bbox归一化集合": join_unique(rows, "裁图bbox归一化"),
            "私有审阅HTML证据编号": packet["私有审阅HTML证据编号"],
            "私有审阅HTML_SHA256": packet["私有审阅HTML_SHA256"],
            "私有审阅任务CSV_SHA256": packet["私有审阅任务CSV_SHA256"],
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "高校官网或招生章程辅证状态": "pending_if_school_clue_present",
            "三方字段一致性状态": "pending_private_three_way_field_confirmation",
            "字段事实写回状态": "blocked_until_required_private_readings_complete",
            "公开安全策略": (
                "只公开页列执行顺序、任务数量、证据编号、SHA、bbox和状态；不公开候选读数、"
                "OCR行文本、图片路径、人工读数、院校名、专业名、专业代号或专业组代码。"
            ),
            "下一步": action + " 完成后仍需湖北官方系统或省招办计划核验。"
        })

    queue_rows.sort(key=lambda row: (
        as_int(row["页列核页优先级数值"]),
        -as_int(row["包内需要人工直接看图任务数"], 0),
        -as_int(row["包内需要双人复核任务数"], 0),
        as_int(row["来源页码"]),
        row["版面列"],
        row["P0即时按页核页包ID"],
    ))
    for index, row in enumerate(queue_rows, start=1):
        row["页列执行总序"] = str(index)
    return queue_rows, packet_rows, candidate_rows


def main():
    queue_rows, packet_rows, candidate_rows = build_rows()
    write_csv(OUTPUT, queue_rows, FIELDS)

    priority_counts = Counter(row["页列核页优先级桶"] for row in queue_rows)
    candidate_bucket_counts = Counter(row["PDF原页候选审阅桶"] for row in candidate_rows)
    field_counts = Counter(row["字段名"] for row in candidate_rows)
    summary = {
        "status": "issue19_p0_immediate_page_execution_queue_not_final",
        "generated_by": Path(__file__).name,
        "source_page_review_packets": "data/working/issue19-p0-immediate-page-review-packets.csv",
        "source_pdf_reading_candidates": (
            "data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv"
        ),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": "data/working/issue19-p0-immediate-page-execution-queue.csv",
        "row_count": len(queue_rows),
        "source_page_packet_count": len(packet_rows),
        "source_candidate_task_count": len(candidate_rows),
        "unique_execution_queue_id_count": len({row["P0即时页列核页执行队列ID"] for row in queue_rows}),
        "unique_page_packet_count": len({row["P0即时按页核页包ID"] for row in queue_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in queue_rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in queue_rows}),
        "unique_candidate_task_count": len({
            row["P0字段即时复核任务ID"] for row in candidate_rows
        }),
        "unique_major_field_pair_count": len({
            (row["专业行ID"], row["字段名"]) for row in candidate_rows
        }),
        "field_counts": dict(field_counts),
        "candidate_bucket_counts": dict(candidate_bucket_counts),
        "page_execution_priority_counts": dict(priority_counts),
        "packet_with_direct_image_review_count": sum(
            as_int(row["包内需要人工直接看图任务数"], 0) > 0 for row in queue_rows
        ),
        "packet_with_double_review_count": sum(
            as_int(row["包内需要双人复核任务数"], 0) > 0 for row in queue_rows
        ),
        "direct_image_review_task_count": sum(
            as_int(row["包内需要人工直接看图任务数"], 0) for row in queue_rows
        ),
        "double_review_task_count": sum(
            as_int(row["包内需要双人复核任务数"], 0) for row in queue_rows
        ),
        "private_candidate_seeded_task_count": sum(
            as_int(row["包内私有候选已挂线索任务数"], 0) for row in queue_rows
        ),
        "hubei_official_review_required_task_count": len(candidate_rows),
        "pdf_manual_review_required_task_count": len(candidate_rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段"] == "true" for row in queue_rows),
        "recommendation_basis_allowed_count": sum(
            row["是否允许作为志愿推荐依据"] == "true" for row in queue_rows
        ),
        "school_major_suggestion_allowed_count": sum(
            row["是否允许生成学校专业建议"] == "true" for row in queue_rows
        ),
        "final_available_count": sum(row["最终可用"] == "true" for row in queue_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in queue_rows),
        "safety_note": (
            "公开队列只保存页列执行顺序、任务数量、证据编号、SHA、bbox和状态；"
            "不保存候选读数、OCR行文本、图片路径、人工读数、院校名、专业名、专业代号或专业组代码。"
        ),
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(queue_rows)} 行")


if __name__ == "__main__":
    main()
