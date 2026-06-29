#!/usr/bin/env python3
"""Build G0 conflict-field evidence gap execution waves.

This public-safe layer compresses field-level evidence gap tasks into
page-side execution waves. It does not publish field readings, OCR text,
school/profession names, reviewer notes, or local paths.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

GAP_TASKS = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-public-ledger.csv"
)
GAP_PAGE_CHANNEL = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-page-channel-summary.csv"
)
GAP_SUMMARY = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-summary.json"
)

OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-execution-waves-v1-public-ledger.csv"
)
WAVE_SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-execution-waves-v1-wave-summary.csv"
)
SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-execution-waves-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_evidence_gap_execution_waves_v1"

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "是否允许进入私有写回评审",
]

PACKET_FIELDS = [
    "G0冲突字段补证执行波次公开账本ID",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源G0冲突字段补证缺口页列通道汇总",
    "来源G0冲突字段补证缺口摘要",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "波次包序号",
    "执行波次序号",
    "执行波次",
    "波次类型",
    "波次前置条件",
    "波次准出条件",
    "波次当前执行状态",
    "是否当前可并行推进",
    "页码版面键",
    "来源页码",
    "版面列",
    "缺口任务数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "证据通道分布",
    "字段名分布",
    "当前通道状态分布",
    "当前阻断桶分布",
    "补证执行优先级分布",
    "补证执行泳道分布",
    "可并行执行任务数",
    "待前置闭环任务数",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有核页HTML证据编号",
    "私有核页HTML_SHA256",
    "缺口任务集合SHA256",
    "闭环结果集合SHA256",
    "波次下一步动作",
    "公开安全策略",
]

WAVE_SUMMARY_FIELDS = [
    "G0冲突字段补证执行波次汇总ID",
    "来源G0冲突字段补证执行波次公开账本",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "波次汇总序号",
    "执行波次序号",
    "执行波次",
    "波次类型",
    "波次前置条件",
    "波次准出条件",
    "波次当前执行状态",
    "波次包数",
    "缺口任务数",
    "涉及页列数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "证据通道分布",
    "字段名分布",
    "当前阻断桶分布",
    "可并行执行任务数",
    "待前置闭环任务数",
    "波次包集合SHA256",
    "缺口任务集合SHA256",
    "闭环结果集合SHA256",
    "波次下一步动作",
    "公开安全策略",
]

WAVES = [
    {
        "seq": "W0",
        "name": "一手证据与辅证采集",
        "kind": "PDF原页/湖北官方/高校辅证记录采集",
        "channels": {"01", "02", "03"},
        "prerequisite": "已生成G0冲突字段补证缺口任务",
        "exit_condition": "PDF原页记录、湖北官方侧记录和高校辅证人工核验记录均形成私有证据编号和SHA",
        "status": "ready_for_parallel_evidence_collection",
        "parallel": "true",
        "action": "优先补齐PDF原页记录、湖北官方侧记录和高校辅证人工核验记录；高校官网只作辅证。",
    },
    {
        "seq": "W1",
        "name": "双人复核",
        "kind": "冲突字段双人复核",
        "channels": {"05"},
        "prerequisite": "需要双人复核的字段已定位到私有页列材料",
        "exit_condition": "需要双人复核的字段形成A/B复核和一致性结论的私有证据编号和SHA",
        "status": "ready_for_double_review_after_pdf_material",
        "parallel": "true",
        "action": "对需要双人复核的字段安排A/B复核；准出仍依赖PDF原页和湖北官方侧证据。",
    },
    {
        "seq": "W2",
        "name": "冲突处理与三方闭环",
        "kind": "冲突处理/PDF-湖北官方-高校辅证闭环",
        "channels": {"04", "06"},
        "prerequisite": "W0证据采集完成，且必要双人复核已完成",
        "exit_condition": "冲突处理和三方一致性闭环形成私有证据编号和SHA",
        "status": "blocked_until_primary_evidence_and_double_review",
        "parallel": "false",
        "action": "等待PDF原页、湖北官方侧、高校辅证和必要双人复核后处理冲突并做三方闭环。",
    },
    {
        "seq": "W3",
        "name": "字段确认",
        "kind": "字段事实确认",
        "channels": {"07"},
        "prerequisite": "W2冲突处理与三方闭环完成",
        "exit_condition": "字段确认形成私有证据编号和SHA",
        "status": "blocked_until_three_way_closure",
        "parallel": "false",
        "action": "三方闭环完成后再做字段确认；公开层仍不保存具体核验内容。",
    },
    {
        "seq": "W4",
        "name": "写回评审",
        "kind": "字段写回评审",
        "channels": {"08"},
        "prerequisite": "W3字段确认完成",
        "exit_condition": "私有写回评审给出可写回或继续阻断结论",
        "status": "blocked_until_field_confirmation",
        "parallel": "false",
        "action": "字段确认后进入私有写回评审；通过评审前不得写回或用于推荐。",
    },
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
    "学校名称",
    "专业名称",
    "专业代号",
    "字段读数",
    "人工读数",
    "字段值",
    "候选值",
    "字段确认值",
    "OCR正文",
    "OCR文本",
    "OCR原文",
    "截图路径",
    "人工复核备注",
    "复核人员",
    "复核结论",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: clean(row.get(field, "")) for field in fields})


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def stable_id(prefix: str, parts: list[str]) -> str:
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_values(values) -> str:
    vals = sorted({clean(value) for value in values if clean(value)})
    return hashlib.sha256("|".join(vals).encode("utf-8")).hexdigest() if vals else ""


def add_false_fields(row: dict[str, str]) -> None:
    for field in FALSE_FIELDS:
        row[field] = "false"


def dist(rows: list[dict[str, str]], field: str) -> str:
    counter = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter))


def count_unique(rows: list[dict[str, str]], field: str) -> int:
    return len({clean(row.get(field, "")) for row in rows if clean(row.get(field, ""))})


def as_int(value: str) -> int:
    try:
        return int(clean(value))
    except ValueError:
        return 0


def side_rank(value: str) -> int:
    return {"left": 0, "right": 1}.get(clean(value), 9)


def public_safety_check(paths: list[Path]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    leaked = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if leaked:
        raise RuntimeError(f"public output contains forbidden tokens: {leaked[:20]}")


def build_packet_rows(tasks: list[dict[str, str]]) -> list[dict[str, str]]:
    wave_by_channel = {
        channel: wave
        for wave in WAVES
        for channel in wave["channels"]
    }
    grouped = defaultdict(list)
    for row in tasks:
        wave = wave_by_channel.get(row.get("证据通道序号", ""))
        if not wave:
            raise RuntimeError(f"unmapped evidence channel: {row.get('证据通道序号')}")
        grouped[(wave["seq"], row.get("页码版面键", ""))].append(row)

    rows = []
    sort_items = sorted(
        grouped.items(),
        key=lambda item: (
            next(i for i, wave in enumerate(WAVES) if wave["seq"] == item[0][0]),
            as_int(item[1][0].get("来源页码", "")),
            side_rank(item[1][0].get("版面列", "")),
            item[0][1],
        ),
    )
    for seq, ((wave_seq, page_key), group) in enumerate(sort_items, start=1):
        wave = next(item for item in WAVES if item["seq"] == wave_seq)
        out = {
            "G0冲突字段补证执行波次公开账本ID": stable_id(
                "G0FIELDGAPWAVE", [SOURCE_PDF_SHA256, wave_seq, page_key]
            ),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源G0冲突字段补证缺口页列通道汇总": source_path(GAP_PAGE_CHANNEL),
            "来源G0冲突字段补证缺口摘要": source_path(GAP_SUMMARY),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段补证执行波次",
            "任务粒度": "页列×执行波次",
            "波次包序号": str(seq),
            "执行波次序号": wave_seq,
            "执行波次": wave["name"],
            "波次类型": wave["kind"],
            "波次前置条件": wave["prerequisite"],
            "波次准出条件": wave["exit_condition"],
            "波次当前执行状态": wave["status"],
            "是否当前可并行推进": wave["parallel"],
            "页码版面键": page_key,
            "来源页码": group[0].get("来源页码", ""),
            "版面列": group[0].get("版面列", ""),
            "缺口任务数": str(len(group)),
            "涉及字段事实数": str(count_unique(group, "G0冲突字段补证闭环结果公开账本ID")),
            "涉及任务数": str(count_unique(group, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(group, "专业行ID")),
            "涉及院校代码数": str(count_unique(group, "院校代码")),
            "证据通道分布": dist(group, "证据通道"),
            "字段名分布": dist(group, "字段名"),
            "当前通道状态分布": dist(group, "当前通道状态"),
            "当前阻断桶分布": dist(group, "当前阻断桶"),
            "补证执行优先级分布": dist(group, "补证执行优先级"),
            "补证执行泳道分布": dist(group, "补证执行泳道"),
            "可并行执行任务数": str(sum(1 for item in group if item.get("是否当前可并行执行") == "true")),
            "待前置闭环任务数": str(sum(1 for item in group if item.get("是否当前可并行执行") != "true")),
            "私有页列CSV证据编号": group[0].get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": group[0].get("私有页列CSV_SHA256", ""),
            "私有核页HTML证据编号": group[0].get("私有核页HTML证据编号", ""),
            "私有核页HTML_SHA256": group[0].get("私有核页HTML_SHA256", ""),
            "缺口任务集合SHA256": sha256_values(
                item.get("G0冲突字段补证缺口任务公开账本ID", "") for item in group
            ),
            "闭环结果集合SHA256": sha256_values(
                item.get("G0冲突字段补证闭环结果公开账本ID", "") for item in group
            ),
            "波次下一步动作": wave["action"],
            "公开安全策略": "公开层只保存页列、波次、状态、计数、证据编号和SHA；不公开具体核验内容、识别内容、人工内容或本地位置。",
        }
        add_false_fields(out)
        rows.append(out)
    return rows


def build_wave_summary(packet_rows: list[dict[str, str]], task_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    tasks_by_wave = defaultdict(list)
    wave_by_channel = {
        channel: wave
        for wave in WAVES
        for channel in wave["channels"]
    }
    for row in task_rows:
        tasks_by_wave[wave_by_channel[row.get("证据通道序号", "")]["seq"]].append(row)

    packets_by_wave = defaultdict(list)
    for row in packet_rows:
        packets_by_wave[row.get("执行波次序号", "")].append(row)

    rows = []
    for seq, wave in enumerate(WAVES, start=1):
        packets = packets_by_wave[wave["seq"]]
        tasks = tasks_by_wave[wave["seq"]]
        out = {
            "G0冲突字段补证执行波次汇总ID": stable_id(
                "G0FIELDGAPWAVESUMMARY", [SOURCE_PDF_SHA256, wave["seq"]]
            ),
            "来源G0冲突字段补证执行波次公开账本": source_path(OUTPUT),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段补证执行波次汇总",
            "任务粒度": "执行波次",
            "波次汇总序号": str(seq),
            "执行波次序号": wave["seq"],
            "执行波次": wave["name"],
            "波次类型": wave["kind"],
            "波次前置条件": wave["prerequisite"],
            "波次准出条件": wave["exit_condition"],
            "波次当前执行状态": wave["status"],
            "波次包数": str(len(packets)),
            "缺口任务数": str(len(tasks)),
            "涉及页列数": str(count_unique(tasks, "页码版面键")),
            "涉及字段事实数": str(count_unique(tasks, "G0冲突字段补证闭环结果公开账本ID")),
            "涉及任务数": str(count_unique(tasks, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(tasks, "专业行ID")),
            "涉及院校代码数": str(count_unique(tasks, "院校代码")),
            "证据通道分布": dist(tasks, "证据通道"),
            "字段名分布": dist(tasks, "字段名"),
            "当前阻断桶分布": dist(tasks, "当前阻断桶"),
            "可并行执行任务数": str(sum(1 for item in tasks if item.get("是否当前可并行执行") == "true")),
            "待前置闭环任务数": str(sum(1 for item in tasks if item.get("是否当前可并行执行") != "true")),
            "波次包集合SHA256": sha256_values(
                item.get("G0冲突字段补证执行波次公开账本ID", "") for item in packets
            ),
            "缺口任务集合SHA256": sha256_values(
                item.get("G0冲突字段补证缺口任务公开账本ID", "") for item in tasks
            ),
            "闭环结果集合SHA256": sha256_values(
                item.get("G0冲突字段补证闭环结果公开账本ID", "") for item in tasks
            ),
            "波次下一步动作": wave["action"],
            "公开安全策略": "公开层只保存波次状态、计数和SHA；不公开具体核验内容、识别内容、人工内容或本地位置。",
        }
        add_false_fields(out)
        rows.append(out)
    return rows


def main() -> None:
    task_rows = read_csv(GAP_TASKS)
    packet_rows = build_packet_rows(task_rows)
    wave_summary_rows = build_wave_summary(packet_rows, task_rows)

    write_csv(OUTPUT, packet_rows, PACKET_FIELDS)
    write_csv(WAVE_SUMMARY_OUTPUT, wave_summary_rows, WAVE_SUMMARY_FIELDS)

    task_count_by_wave = {row["执行波次序号"]: int(row["缺口任务数"]) for row in wave_summary_rows}
    packet_count_by_wave = {row["执行波次序号"]: int(row["波次包数"]) for row in wave_summary_rows}
    status_counter = Counter(row["波次当前执行状态"] for row in packet_rows)

    summary = {
        "status": "issue19_first_closure_g0_conflict_field_evidence_gap_execution_waves_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_gap_tasks": source_path(GAP_TASKS),
        "source_gap_tasks_sha256": sha256_file(GAP_TASKS),
        "source_gap_page_channel": source_path(GAP_PAGE_CHANNEL),
        "source_gap_page_channel_sha256": sha256_file(GAP_PAGE_CHANNEL),
        "source_gap_summary": source_path(GAP_SUMMARY),
        "source_gap_summary_sha256": sha256_file(GAP_SUMMARY),
        "output_table": source_path(OUTPUT),
        "wave_summary_table": source_path(WAVE_SUMMARY_OUTPUT),
        "packet_row_count": len(packet_rows),
        "wave_summary_row_count": len(wave_summary_rows),
        "source_gap_task_row_count": len(task_rows),
        "unique_page_side_count": count_unique(task_rows, "页码版面键"),
        "unique_wave_count": len(WAVES),
        "unique_closure_result_count": count_unique(task_rows, "G0冲突字段补证闭环结果公开账本ID"),
        "unique_task_count": count_unique(task_rows, "稳定基座第一闭环明细任务ID"),
        "unique_major_row_count": count_unique(task_rows, "专业行ID"),
        "task_count_by_wave": task_count_by_wave,
        "packet_count_by_wave": packet_count_by_wave,
        "packet_status_counts": dict(status_counter),
        "parallel_executable_task_count": sum(
            int(row["可并行执行任务数"]) for row in wave_summary_rows
        ),
        "blocked_until_predecessor_task_count": sum(
            int(row["待前置闭环任务数"]) for row in wave_summary_rows
        ),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只把G0冲突字段补证缺口任务压成页列执行波次，不确认字段事实，不写回，不进入推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    public_safety_check([OUTPUT, WAVE_SUMMARY_OUTPUT, SUMMARY_OUTPUT])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
