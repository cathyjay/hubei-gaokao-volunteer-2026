#!/usr/bin/env python3
"""Build the minimal public manual checklist for W0/B0 first-closure packets.

W0/B0 packets include many companion facts on the same page-side. This script
extracts the smallest public checklist that should be reviewed first: group
boundary facts, explicit conflict field facts, and major-name assignment facts.
It does not publish school names, major names, field values, OCR text, image
paths, or private review notes.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FACT_PACKETS = WORKING / "issue19-stable-foundation-first-closure-fact-verification-packets-public-ledger.csv"
FACT_ITEMS = WORKING / "issue19-stable-foundation-first-closure-fact-verification-items-public-ledger.csv"
B0_STATUS = WORKING / "issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv"

PACKET_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-w0-b0-minimal-manual-packets-public-ledger.csv"
ITEM_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-w0-b0-minimal-manual-items-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-w0-b0-minimal-manual-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_w0_b0_minimal_manual_checklist"
GENERATED_AT = "2026-06-29"

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
]

PACKET_FIELDS = [
    "W0B0最小人工复核包ID",
    "来源第一闭环事实核验包",
    "来源第一闭环事实核验包明细",
    "来源B0冲突页列核验状态",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "最小人工复核包序号",
    "原事实核验包序号",
    "第一闭环事实核验包ID",
    "B0冲突页列核验状态ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "B0冲突优先级判定",
    "W0事实范围总数",
    "最小人工复核事实数",
    "同页伴生待核事实数",
    "专业组边界先核事实数",
    "明确冲突字段事实数",
    "专业名归属事实数",
    "专业计划数冲突字段事实数",
    "学费冲突字段事实数",
    "再选科目冲突字段事实数",
    "涉及第一闭环任务数",
    "涉及冲突任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "需双人复核事实数",
    "需人工看图事实数",
    "B0页列任务数",
    "B0明确冲突任务数",
    "B0同页非冲突待闭环任务数",
    "全局计划数冲突专项同页行数",
    "最小复核类型分布",
    "事实类型分布",
    "人工最小复核动作",
    "完成条件",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "最小人工复核事实集合SHA256",
    "同页W0事实集合SHA256",
    "任务ID集合SHA256",
    "专业行ID集合SHA256",
    "院校代码集合SHA256",
    "公开安全策略",
]

ITEM_FIELDS = [
    "W0B0最小人工复核明细ID",
    "W0B0最小人工复核包ID",
    "来源第一闭环事实核验包明细",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "包内最小复核序号",
    "最小人工复核包序号",
    "页码版面键",
    "来源页码",
    "版面列",
    "第一闭环事实核验包明细ID",
    "第一闭环事实范围缺口公开账本ID",
    "第一闭环字段事实公开账本ID",
    "稳定基座第一闭环明细任务ID",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "事实域",
    "事实类型",
    "事实粒度",
    "字段名",
    "最小复核类型",
    "复核优先级",
    "页列主阻断",
    "核验动作层级",
    "是否需要人工看图",
    "是否需要双人复核",
    "人工最小复核动作",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "事实对象集合SHA256",
    "公开安全策略",
]

FORBIDDEN_PUBLIC_TOKENS = [
    "/Users/",
    "/home/",
    "/var/folders/",
    "/private/",
    "private/",
    "private\\",
    "ocr-runs",
    "rendered-pages",
    "file://",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".heic",
    "Authorization",
    "Bearer ",
    "Cookie",
    "Set-Cookie",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "api_key",
    "身份证",
    "准考证",
    "报名号",
    "序列号",
    "手机号",
    "院校名称",
    "专业名称",
    "专业代号",
    "院校专业组",
    "OCR行文本",
    "OCR原文",
    "候选值",
    "人工读数",
    "字段确认值",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "复核备注",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def stable_id(prefix: str, parts: list[str]) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def sha256_values(values: list[str]) -> str:
    clean = sorted({str(value or "").strip() for value in values if str(value or "").strip()})
    return hashlib.sha256("|".join(clean).encode("utf-8")).hexdigest() if clean else ""


def to_int(value: str | int | None) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def compact_counter(values: list[str]) -> str:
    counter = Counter(value for value in values if value)
    return "；".join(f"{key}×{count}" for key, count in sorted(counter.items())) if counter else ""


def add_false_fields(row: dict[str, str]) -> None:
    for field in FALSE_FIELDS:
        row[field] = "false"


def is_w0(row: dict[str, str]) -> bool:
    return row.get("核验波次", "") == "W0-B0冲突优先"


def is_minimal_item(row: dict[str, str]) -> bool:
    if not is_w0(row):
        return False
    if row.get("事实域", "") == "专业组边界":
        return True
    if row.get("事实域", "") == "专业名归属":
        return True
    return row.get("事实域", "") == "字段事实" and row.get("核验动作层级", "") == "N0-先双人核PDF原页冲突"


def minimal_type(row: dict[str, str]) -> tuple[int, str, str]:
    if row.get("事实域", "") == "专业组边界":
        return (0, "M0-先核专业组边界", "先核页列内专业组起止、跨页延续、左右栏边界和组内归属，防止后续字段串组。")
    if row.get("事实域", "") == "字段事实":
        return (1, "M1-双人核明确冲突字段", "双人回看PDF原页，记录计划数、学费或选科冲突字段，并等待湖北官方侧复核。")
    return (2, "M2-核专业名归属", "回看PDF原页确认专业行归属，并用湖北官方侧计划记录复核；高校侧来源只作定位。")


def build_packet_row(
    seq: int,
    page_key: str,
    packet_row: dict[str, str],
    b0_row: dict[str, str],
    w0_rows: list[dict[str, str]],
    minimal_rows: list[dict[str, str]],
) -> dict[str, str]:
    type_counter = Counter(row.get("最小复核类型", "") for row in minimal_rows)
    fact_type_counter = Counter(row.get("事实类型", "") for row in minimal_rows)
    task_ids = [row.get("稳定基座第一闭环明细任务ID", "") for row in minimal_rows]
    major_ids = [row.get("专业行ID", "") for row in minimal_rows]
    school_ids = [row.get("院校代码", "") for row in minimal_rows]
    row = {
        "W0B0最小人工复核包ID": stable_id(
            "W0B0MANPKT",
            [
                page_key,
                packet_row.get("第一闭环事实核验包ID", ""),
                sha256_values([item.get("第一闭环事实核验包明细ID", "") for item in minimal_rows]),
            ],
        ),
        "来源第一闭环事实核验包": source_path(FACT_PACKETS),
        "来源第一闭环事实核验包明细": source_path(FACT_ITEMS),
        "来源B0冲突页列核验状态": source_path(B0_STATUS),
        "来源期号": SOURCE_ISSUE,
        "来源PDF_SHA256": SOURCE_PDF_SHA256,
        "生成日期": GENERATED_AT,
        "数据阶段": DATA_STAGE,
        "主表粒度": "W0-B0页列最小人工复核包",
        "任务粒度": "PDF页码×版面列×最小人工复核事实",
        "最小人工复核包序号": str(seq),
        "原事实核验包序号": packet_row.get("核验包序号", ""),
        "第一闭环事实核验包ID": packet_row.get("第一闭环事实核验包ID", ""),
        "B0冲突页列核验状态ID": b0_row.get("B0冲突页列核验状态ID", ""),
        "来源页码": packet_row.get("来源页码", ""),
        "版面列": packet_row.get("版面列", ""),
        "页码版面键": page_key,
        "B0冲突优先级判定": b0_row.get("B0冲突优先级判定", ""),
        "W0事实范围总数": str(len(w0_rows)),
        "最小人工复核事实数": str(len(minimal_rows)),
        "同页伴生待核事实数": str(len(w0_rows) - len(minimal_rows)),
        "专业组边界先核事实数": str(fact_type_counter.get("专业组边界事实", 0)),
        "明确冲突字段事实数": str(sum(row.get("事实域") == "字段事实" for row in minimal_rows)),
        "专业名归属事实数": str(fact_type_counter.get("专业名归属事实", 0)),
        "专业计划数冲突字段事实数": str(fact_type_counter.get("字段事实-专业计划数", 0)),
        "学费冲突字段事实数": str(fact_type_counter.get("字段事实-学费", 0)),
        "再选科目冲突字段事实数": str(fact_type_counter.get("字段事实-再选科目", 0)),
        "涉及第一闭环任务数": str(len({value for value in task_ids if value})),
        "涉及冲突任务数": b0_row.get("B0页列冲突任务数", ""),
        "涉及专业行数": str(len({value for value in major_ids if value})),
        "涉及院校代码数": str(len({value for value in school_ids if value})),
        "需双人复核事实数": str(sum(row.get("是否需要双人复核") == "true" for row in minimal_rows)),
        "需人工看图事实数": str(sum(row.get("是否需要人工看图") == "true" for row in minimal_rows)),
        "B0页列任务数": b0_row.get("页列任务数", ""),
        "B0明确冲突任务数": b0_row.get("B0页列冲突任务数", ""),
        "B0同页非冲突待闭环任务数": b0_row.get("同页非冲突待闭环任务数", ""),
        "全局计划数冲突专项同页行数": b0_row.get("同页B0B1计划数冲突专项记录数", ""),
        "最小复核类型分布": compact_counter([row.get("最小复核类型", "") for row in minimal_rows]),
        "事实类型分布": compact_counter([row.get("事实类型", "") for row in minimal_rows]),
        "人工最小复核动作": "先核专业组边界，再双人核明确冲突字段；如有专业名归属事实，同页同步核归属。",
        "完成条件": "最小清单内事实完成PDF原页记录、湖北官方侧核验、必要高校辅证和双人复核后，才能继续同页伴生事实闭环；仍不自动写回字段。",
        "PDF原页核页状态": "pending_pdf_page_review",
        "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
        "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
        "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
        "最小人工复核事实集合SHA256": sha256_values([row.get("第一闭环事实核验包明细ID", "") for row in minimal_rows]),
        "同页W0事实集合SHA256": sha256_values([row.get("第一闭环事实核验包明细ID", "") for row in w0_rows]),
        "任务ID集合SHA256": sha256_values(task_ids),
        "专业行ID集合SHA256": sha256_values(major_ids),
        "院校代码集合SHA256": sha256_values(school_ids),
        "公开安全策略": "公开层只保存页列、状态桶、计数、ID和SHA；不保存学校专业明细、字段明细值、识别正文或私有材料。",
    }
    add_false_fields(row)
    return row


def build_item_row(packet_row: dict[str, str], source_row: dict[str, str], seq: int) -> dict[str, str]:
    priority_rank, min_type, action = minimal_type(source_row)
    row = {
        "W0B0最小人工复核明细ID": stable_id(
            "W0B0MANITEM",
            [
                packet_row.get("W0B0最小人工复核包ID", ""),
                source_row.get("第一闭环事实核验包明细ID", ""),
            ],
        ),
        "W0B0最小人工复核包ID": packet_row.get("W0B0最小人工复核包ID", ""),
        "来源第一闭环事实核验包明细": source_path(FACT_ITEMS),
        "来源期号": SOURCE_ISSUE,
        "来源PDF_SHA256": SOURCE_PDF_SHA256,
        "生成日期": GENERATED_AT,
        "数据阶段": DATA_STAGE + "_items",
        "主表粒度": "W0-B0页列最小人工复核明细",
        "任务粒度": "最小人工复核包×事实范围",
        "包内最小复核序号": str(seq),
        "最小人工复核包序号": packet_row.get("最小人工复核包序号", ""),
        "页码版面键": source_row.get("页码版面键", ""),
        "来源页码": source_row.get("来源页码", ""),
        "版面列": source_row.get("版面列", ""),
        "第一闭环事实核验包明细ID": source_row.get("第一闭环事实核验包明细ID", ""),
        "第一闭环事实范围缺口公开账本ID": source_row.get("第一闭环事实范围缺口公开账本ID", ""),
        "第一闭环字段事实公开账本ID": source_row.get("第一闭环字段事实公开账本ID", ""),
        "稳定基座第一闭环明细任务ID": source_row.get("稳定基座第一闭环明细任务ID", ""),
        "专业行ID": source_row.get("专业行ID", ""),
        "专业组出现ID": source_row.get("专业组出现ID", ""),
        "院校代码": source_row.get("院校代码", ""),
        "事实域": source_row.get("事实域", ""),
        "事实类型": source_row.get("事实类型", ""),
        "事实粒度": source_row.get("事实粒度", ""),
        "字段名": source_row.get("字段名", ""),
        "最小复核类型": min_type,
        "复核优先级": f"P{priority_rank}",
        "页列主阻断": source_row.get("页列主阻断", ""),
        "核验动作层级": source_row.get("核验动作层级", ""),
        "是否需要人工看图": source_row.get("是否需要人工看图", ""),
        "是否需要双人复核": source_row.get("是否需要双人复核", ""),
        "人工最小复核动作": action,
        "PDF原页核页状态": "pending_pdf_page_review",
        "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
        "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
        "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
        "事实对象集合SHA256": source_row.get("事实对象集合SHA256", ""),
        "公开安全策略": "公开层只保存最小复核类型、页列、状态桶、ID和SHA；不保存字段明细值、识别正文或私有材料。",
    }
    add_false_fields(row)
    return row


def main() -> None:
    packet_rows = read_csv(FACT_PACKETS)
    item_rows = read_csv(FACT_ITEMS)
    b0_rows = read_csv(B0_STATUS)

    fact_packet_by_key = {row.get("页码版面键", ""): row for row in packet_rows}
    b0_by_key = {row.get("页码版面键", ""): row for row in b0_rows}
    w0_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    min_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in item_rows:
        if is_w0(row):
            w0_by_key[row.get("页码版面键", "")].append(row)
        if is_minimal_item(row):
            enriched = dict(row)
            _, min_type, _ = minimal_type(enriched)
            enriched["最小复核类型"] = min_type
            min_by_key[row.get("页码版面键", "")].append(enriched)

    packet_output: list[dict[str, str]] = []
    for seq, page_key in enumerate(sorted(b0_by_key), start=1):
        packet_output.append(
            build_packet_row(
                seq,
                page_key,
                fact_packet_by_key.get(page_key, {}),
                b0_by_key.get(page_key, {}),
                w0_by_key.get(page_key, []),
                min_by_key.get(page_key, []),
            )
        )

    packet_output.sort(
        key=lambda row: (
            0 if "P0-" in row.get("B0冲突优先级判定", "") else 1 if "P1-" in row.get("B0冲突优先级判定", "") else 2,
            -to_int(row.get("最小人工复核事实数")),
            row.get("页码版面键", ""),
        )
    )
    packet_by_key = {}
    for seq, row in enumerate(packet_output, start=1):
        row["最小人工复核包序号"] = str(seq)
        packet_by_key[row.get("页码版面键", "")] = row

    item_output: list[dict[str, str]] = []
    for packet in packet_output:
        page_key = packet.get("页码版面键", "")
        sorted_items = sorted(
            min_by_key.get(page_key, []),
            key=lambda row: (
                minimal_type(row)[0],
                row.get("事实类型", ""),
                row.get("稳定基座第一闭环明细任务ID", ""),
                row.get("第一闭环事实核验包明细ID", ""),
            ),
        )
        for seq, item in enumerate(sorted_items, start=1):
            item_output.append(build_item_row(packet, item, seq))

    write_csv(PACKET_OUTPUT, packet_output, PACKET_FIELDS)
    write_csv(ITEM_OUTPUT, item_output, ITEM_FIELDS)

    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [PACKET_OUTPUT, ITEM_OUTPUT]
    )
    forbidden_hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if forbidden_hits:
        raise SystemExit(f"公开输出包含禁止内容：{forbidden_hits[:5]}")

    min_type_counts = Counter(row.get("最小复核类型", "") for row in item_output)
    fact_type_counts = Counter(row.get("事实类型", "") for row in item_output)
    priority_counts = Counter(row.get("B0冲突优先级判定", "") for row in packet_output)
    summary = {
        "status": "issue19_stable_foundation_first_closure_w0_b0_minimal_manual_checklist_ready_not_final",
        "generated_by": "build_issue19_first_closure_w0_b0_minimal_manual_checklist.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_first_closure_fact_verification_packets": source_path(FACT_PACKETS),
        "source_first_closure_fact_verification_items": source_path(FACT_ITEMS),
        "source_b0_conflict_status": source_path(B0_STATUS),
        "packet_output_table": source_path(PACKET_OUTPUT),
        "item_output_table": source_path(ITEM_OUTPUT),
        "packet_row_count": len(packet_output),
        "item_row_count": len(item_output),
        "w0_total_fact_scope_count": sum(to_int(row.get("W0事实范围总数")) for row in packet_output),
        "companion_pending_fact_count": sum(to_int(row.get("同页伴生待核事实数")) for row in packet_output),
        "unique_page_side_count": len({row.get("页码版面键", "") for row in packet_output}),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID", "") for row in item_output if row.get("稳定基座第一闭环明细任务ID", "")}),
        "minimal_review_type_counts": dict(min_type_counts),
        "fact_type_counts": dict(fact_type_counts),
        "b0_priority_counts": dict(priority_counts),
        "group_boundary_fact_count": fact_type_counts.get("专业组边界事实", 0),
        "major_name_assignment_fact_count": fact_type_counts.get("专业名归属事实", 0),
        "explicit_conflict_field_fact_count": sum(row.get("事实域") == "字段事实" for row in item_output),
        "plan_count_conflict_field_fact_count": fact_type_counts.get("字段事实-专业计划数", 0),
        "tuition_conflict_field_fact_count": fact_type_counts.get("字段事实-学费", 0),
        "reselect_conflict_field_fact_count": fact_type_counts.get("字段事实-再选科目", 0),
        "double_review_required_fact_count": sum(row.get("是否需要双人复核") == "true" for row in item_output),
        "manual_image_required_fact_count": sum(row.get("是否需要人工看图") == "true" for row in item_output),
        "pdf_pending_packet_count": sum(row.get("PDF原页核页状态") == "pending_pdf_page_review" for row in packet_output),
        "hubei_official_pending_packet_count": sum(row.get("湖北官方系统或省招办计划核验状态") == "pending_hubei_official_plan_review" for row in packet_output),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该公开账本只把W0/B0页列压成最小人工复核入口，不公开字段明细值，不确认字段事实，不生成志愿排序。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
