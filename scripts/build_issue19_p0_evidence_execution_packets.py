#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLOSURE_TASKS = ROOT / "data/working/issue19-full-major-evidence-closure-tasks.csv"
OUTPUT = ROOT / "data/working/issue19-p0-evidence-execution-packets.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-p0-evidence-execution-packets-summary.json"

DATA_STAGE = "issue19_p0_evidence_execution_packets"


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


def p0_bucket(row):
    priority = row.get("证据任务优先级", "")
    if priority == "P0-先核PDF结构阻断":
        return "P0A-PDF原页结构阻断"
    if priority == "P0-三方证据闭环先核":
        return "P0B-三方证据闭环"
    if priority == "P0-B0B1冲突/未匹配先核":
        return "P0C-B0B1差异复核"
    return ""


def main():
    rows = read_csv(CLOSURE_TASKS)
    p0_rows = [row for row in rows if row.get("证据任务优先级", "").startswith("P0-")]

    page_counts = Counter(row.get("来源页码", "") for row in p0_rows)
    school_counts = Counter((row.get("院校代码", ""), row.get("院校名称OCR", "")) for row in p0_rows)
    bucket_counts = Counter(p0_bucket(row) for row in p0_rows)

    page_rank = {
        page: rank
        for rank, (page, _count) in enumerate(
            sorted(page_counts.items(), key=lambda item: (-item[1], as_int(item[0]), item[0])),
            start=1,
        )
    }
    school_rank = {
        key: rank
        for rank, (key, _count) in enumerate(
            sorted(school_counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1])),
            start=1,
        )
    }

    output_rows = []
    for row in sorted(
        p0_rows,
        key=lambda item: (
            page_rank.get(item.get("来源页码", ""), 9999),
            school_rank.get((item.get("院校代码", ""), item.get("院校名称OCR", "")), 9999),
            item.get("证据项排序", ""),
            item.get("专业组内专业序号", ""),
            item.get("证据闭环任务ID", ""),
        ),
    ):
        bucket = p0_bucket(row)
        school_key = (row.get("院校代码", ""), row.get("院校名称OCR", ""))
        packet_id = stable_id(
            "P0PACK",
            [row.get("来源页码", ""), row.get("院校代码", ""), row.get("院校专业组代码OCR规范化", ""), bucket],
        )
        output_rows.append({
            "P0执行包任务ID": stable_id("P0TASK", [packet_id, row.get("证据闭环任务ID", "")]),
            "P0执行包ID": packet_id,
            "来源证据闭环任务队列": "data/working/issue19-full-major-evidence-closure-tasks.csv",
            "来源证据闭环任务ID": row.get("证据闭环任务ID", ""),
            "来源全量证据工作台ID": row.get("来源全量证据工作台ID", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0证据项",
            "最终可用": "false",
            "是否可升级": "false",
            "执行包状态": "pending_p0_evidence_execution",
            "P0执行包类型": bucket,
            "P0页码优先序": page_rank.get(row.get("来源页码", ""), ""),
            "P0学校优先序": school_rank.get(school_key, ""),
            "P0页内任务数": page_counts.get(row.get("来源页码", ""), 0),
            "P0学校任务数": school_counts.get(school_key, 0),
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
            "来源页码": row.get("来源页码", ""),
            "专业组内专业序号": row.get("专业组内专业序号", ""),
            "专业代号OCR": row.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": row.get("专业名称及备注OCR短摘", ""),
            "全量证据执行优先级": row.get("全量证据执行优先级", ""),
            "证据项": row.get("证据项", ""),
            "证据任务优先级": row.get("证据任务优先级", ""),
            "证据任务状态": row.get("证据任务状态", ""),
            "需要核验字段": row.get("需要核验字段", ""),
            "执行动作代码": row.get("执行动作代码", ""),
            "阻断或待核原因": row.get("阻断或待核原因", ""),
        })

    fields = [
        "P0执行包任务ID",
        "P0执行包ID",
        "来源证据闭环任务队列",
        "来源证据闭环任务ID",
        "来源全量证据工作台ID",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "是否可升级",
        "执行包状态",
        "P0执行包类型",
        "P0页码优先序",
        "P0学校优先序",
        "P0页内任务数",
        "P0学校任务数",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "全量证据执行优先级",
        "证据项",
        "证据任务优先级",
        "证据任务状态",
        "需要核验字段",
        "执行动作代码",
        "阻断或待核原因",
    ]
    write_csv(OUTPUT, output_rows, fields)

    top_pages = [
        {"来源页码": page, "P0任务数": count}
        for page, count in sorted(
            page_counts.items(), key=lambda item: (-item[1], as_int(item[0]), item[0])
        )[:30]
    ]
    top_schools = [
        {"院校代码": code, "院校名称OCR": name, "P0任务数": count}
        for (code, name), count in sorted(
            school_counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1])
        )[:30]
    ]
    summary = {
        "status": "issue19_p0_evidence_execution_packets_not_final",
        "generated_by": "build_issue19_p0_evidence_execution_packets.py",
        "source_closure_tasks": "data/working/issue19-full-major-evidence-closure-tasks.csv",
        "output_table": "data/working/issue19-p0-evidence-execution-packets.csv",
        "source_closure_task_count": len(rows),
        "p0_task_row_count": len(output_rows),
        "unique_p0_task_id_count": len({row["P0执行包任务ID"] for row in output_rows}),
        "unique_source_closure_task_id_count": len({row["来源证据闭环任务ID"] for row in output_rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "unique_packet_id_count": len({row["P0执行包ID"] for row in output_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in output_rows}),
        "unique_school_count": len({row["院校代码"] for row in output_rows}),
        "auto_upgrade_allowed_count": sum(row["是否可升级"] == "true" for row in output_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "packet_type_counts": dict(Counter(row["P0执行包类型"] for row in output_rows)),
        "task_status_counts": dict(Counter(row["证据任务状态"] for row in output_rows)),
        "evidence_item_counts": dict(Counter(row["证据项"] for row in output_rows)),
        "top_pdf_pages": top_pages,
        "top_schools": top_schools,
        "notes": [
            "本表只抽取P0证据任务，仍是一行一个专业行和一个P0证据项。",
            "P0执行包ID用于按页、学校和任务类型批量执行，不替代逐专业证据任务。",
            "所有P0任务仍需PDF原页、湖北官方系统/省招办计划、高校官网/章程等证据闭环后才可能升级。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
