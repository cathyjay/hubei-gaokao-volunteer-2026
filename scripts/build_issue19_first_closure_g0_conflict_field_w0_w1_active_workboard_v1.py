#!/usr/bin/env python3
"""Build the active W0/W1 workboard for G0 conflict-field closure.

This public-safe layer extracts only the evidence tasks that can be worked on
now from the larger G0 conflict-field gap queue. It does not publish field
readings, OCR text, school/profession names, reviewer notes, or local paths.
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
GAP_WAVES = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-execution-waves-v1-public-ledger.csv"
)
GAP_WAVE_SUMMARY = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-execution-waves-v1-summary.json"
)
VERIFICATION_PAGE_SUMMARY = (
    WORKING
    / "issue19-first-closure-verification-result-page-summary.csv"
)
PUBLIC_EVIDENCE_MAP = (
    WORKING
    / "issue19-stable-foundation-first-closure-public-evidence-map.csv"
)
FIELD_BACKLINK_PAGE_SUMMARY = (
    WORKING
    / "issue19-w0-b0-school-source-field-backlink-page-summary.csv"
)

OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-active-workboard-v1-public-ledger.csv"
)
PAGE_SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-active-workboard-v1-page-summary.csv"
)
SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-active-workboard-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_w0_w1_active_workboard_v1"

ACTIVE_CHANNELS = {"01", "02", "03", "05"}
CHANNEL_TO_WAVE = {
    "01": "W0",
    "02": "W0",
    "03": "W0",
    "05": "W1",
}
CHANNEL_ACTIONS = {
    "01": "核PDF原页私有材料并登记私有证据编号和SHA；公开层只保留状态与计数。",
    "02": "优先核湖北官方系统或省招办计划；不可得时继续阻断，不能用高校官网替代。",
    "03": "核高校官网或章程辅证，作为double check线索；不能替代湖北官方计划。",
    "05": "安排A/B双人复核并记录一致性私有证据；准出仍依赖一手证据闭环。",
}
CHANNEL_EXIT = {
    "01": "PDF原页记录形成私有证据编号和SHA",
    "02": "湖北官方侧记录形成私有证据编号和SHA",
    "03": "高校辅证人工核验记录形成私有证据编号和SHA",
    "05": "A/B复核和一致性结论形成私有证据编号和SHA",
}

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

WORKBOARD_FIELDS = [
    "G0冲突字段W0W1主动工作包公开账本ID",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源G0冲突字段补证执行波次公开账本",
    "来源G0冲突字段补证执行波次摘要",
    "来源第一闭环核验结果页列汇总",
    "来源第一闭环公开证据地图",
    "来源W0B0高校源字段回接页列汇总",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "主动工作包序号",
    "执行波次序号",
    "执行波次",
    "证据通道序号",
    "证据通道",
    "证据通道类型",
    "证据通道执行层级",
    "当前执行状态",
    "当前是否可并行执行",
    "页码版面键",
    "来源页码",
    "版面列",
    "缺口任务数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "当前通道状态分布",
    "当前阻断桶分布",
    "补证执行优先级分布",
    "补证执行泳道分布",
    "PDF原页待核任务数",
    "湖北官方侧待核任务数",
    "高校辅证线索任务数",
    "需要双人复核任务数",
    "PDFOCR提示任务数",
    "机器坐标提示任务数",
    "PDFOCR与高校辅证冲突任务数",
    "高校源结构化接入候选字段数",
    "高校源最新对齐任务数合计",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有核页HTML证据编号",
    "私有核页HTML_SHA256",
    "来源波次包ID",
    "缺口任务集合SHA256",
    "闭环结果集合SHA256",
    "主动下一步动作",
    "本通道准出条件",
    "公开安全策略",
]

PAGE_SUMMARY_FIELDS = [
    "G0冲突字段W0W1主动工作页列汇总ID",
    "来源G0冲突字段W0W1主动工作包公开账本",
    "来源G0冲突字段补证执行波次公开账本",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "页列汇总序号",
    "页码版面键",
    "来源页码",
    "版面列",
    "主动工作包数",
    "当前可并行任务数",
    "W0一手证据与辅证采集任务数",
    "W1双人复核任务数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "证据通道分布",
    "字段名分布",
    "当前阻断桶分布",
    "PDF原页待核任务数",
    "湖北官方侧待核任务数",
    "高校辅证线索任务数",
    "需要双人复核任务数",
    "PDFOCR提示任务数",
    "机器坐标提示任务数",
    "PDFOCR与高校辅证冲突任务数",
    "高校源结构化接入候选字段数",
    "高校源最新对齐任务数合计",
    "主动工作包集合SHA256",
    "缺口任务集合SHA256",
    "闭环结果集合SHA256",
    "页列下一步动作",
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


def as_int(value: object) -> int:
    try:
        return int(clean(value))
    except ValueError:
        return 0


def side_rank(value: str) -> int:
    return {"left": 0, "right": 1}.get(clean(value), 9)


def dist(rows: list[dict[str, str]], field: str) -> str:
    counter = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter))


def count_unique(rows: list[dict[str, str]], field: str) -> int:
    return len({clean(row.get(field, "")) for row in rows if clean(row.get(field, ""))})


def public_safety_check(paths: list[Path]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    leaked = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if leaked:
        raise RuntimeError(f"public output contains forbidden tokens: {leaked[:20]}")


def index_by_page(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("页码版面键", ""): row for row in rows if row.get("页码版面键", "")}


def build_workboard_rows(
    gap_rows: list[dict[str, str]],
    wave_rows: list[dict[str, str]],
    verification_pages: dict[str, dict[str, str]],
    evidence_pages: dict[str, dict[str, str]],
    backlink_pages: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    active_rows = [
        row for row in gap_rows
        if row.get("证据通道序号") in ACTIVE_CHANNELS and row.get("是否当前可并行执行") == "true"
    ]
    wave_by_key = {
        (row.get("执行波次序号", ""), row.get("页码版面键", "")): row
        for row in wave_rows
    }
    grouped = defaultdict(list)
    for row in active_rows:
        grouped[(row.get("页码版面键", ""), row.get("证据通道序号", ""))].append(row)

    sort_items = sorted(
        grouped.items(),
        key=lambda item: (
            as_int(item[1][0].get("来源页码", "")),
            side_rank(item[1][0].get("版面列", "")),
            item[0][1],
        ),
    )
    rows = []
    for seq, ((page_key, channel_seq), group) in enumerate(sort_items, start=1):
        wave_seq = CHANNEL_TO_WAVE[channel_seq]
        wave = wave_by_key.get((wave_seq, page_key))
        if not wave:
            raise RuntimeError(f"missing wave packet for {wave_seq} {page_key}")
        verification = verification_pages.get(page_key, {})
        evidence = evidence_pages.get(page_key, {})
        backlink = backlink_pages.get(page_key, {})
        out = {
            "G0冲突字段W0W1主动工作包公开账本ID": stable_id(
                "G0W0W1ACTIVE", [SOURCE_PDF_SHA256, page_key, channel_seq]
            ),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源G0冲突字段补证执行波次公开账本": source_path(GAP_WAVES),
            "来源G0冲突字段补证执行波次摘要": source_path(GAP_WAVE_SUMMARY),
            "来源第一闭环核验结果页列汇总": source_path(VERIFICATION_PAGE_SUMMARY),
            "来源第一闭环公开证据地图": source_path(PUBLIC_EVIDENCE_MAP),
            "来源W0B0高校源字段回接页列汇总": source_path(FIELD_BACKLINK_PAGE_SUMMARY),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段W0/W1主动工作包",
            "任务粒度": "页列×证据通道",
            "主动工作包序号": str(seq),
            "执行波次序号": wave_seq,
            "执行波次": wave.get("执行波次", ""),
            "证据通道序号": channel_seq,
            "证据通道": group[0].get("证据通道", ""),
            "证据通道类型": group[0].get("证据通道类型", ""),
            "证据通道执行层级": group[0].get("证据通道执行层级", ""),
            "当前执行状态": "ready_for_parallel_w0_w1_execution",
            "当前是否可并行执行": "true",
            "页码版面键": page_key,
            "来源页码": group[0].get("来源页码", ""),
            "版面列": group[0].get("版面列", ""),
            "缺口任务数": str(len(group)),
            "涉及字段事实数": str(count_unique(group, "G0冲突字段补证闭环结果公开账本ID")),
            "涉及任务数": str(count_unique(group, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(group, "专业行ID")),
            "涉及院校代码数": str(count_unique(group, "院校代码")),
            "字段名分布": dist(group, "字段名"),
            "当前通道状态分布": dist(group, "当前通道状态"),
            "当前阻断桶分布": dist(group, "当前阻断桶"),
            "补证执行优先级分布": dist(group, "补证执行优先级"),
            "补证执行泳道分布": dist(group, "补证执行泳道"),
            "PDF原页待核任务数": verification.get("PDF原页待核任务数", ""),
            "湖北官方侧待核任务数": verification.get("湖北官方侧待核任务数", ""),
            "高校辅证线索任务数": verification.get("高校辅证线索任务数", ""),
            "需要双人复核任务数": verification.get("需要双人复核任务数", ""),
            "PDFOCR提示任务数": evidence.get("PDFOCR提示任务数", ""),
            "机器坐标提示任务数": evidence.get("机器坐标提示任务数", ""),
            "PDFOCR与高校辅证冲突任务数": evidence.get("PDFOCR与高校辅证冲突任务数", ""),
            "高校源结构化接入候选字段数": backlink.get("结构化接入候选字段数", ""),
            "高校源最新对齐任务数合计": backlink.get("高校源最新对齐任务数合计", ""),
            "私有页列CSV证据编号": group[0].get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": group[0].get("私有页列CSV_SHA256", ""),
            "私有核页HTML证据编号": group[0].get("私有核页HTML证据编号", ""),
            "私有核页HTML_SHA256": group[0].get("私有核页HTML_SHA256", ""),
            "来源波次包ID": wave.get("G0冲突字段补证执行波次公开账本ID", ""),
            "缺口任务集合SHA256": sha256_values(
                item.get("G0冲突字段补证缺口任务公开账本ID", "") for item in group
            ),
            "闭环结果集合SHA256": sha256_values(
                item.get("G0冲突字段补证闭环结果公开账本ID", "") for item in group
            ),
            "主动下一步动作": CHANNEL_ACTIONS[channel_seq],
            "本通道准出条件": CHANNEL_EXIT[channel_seq],
            "公开安全策略": "公开层只保存页列、通道、状态、计数、证据编号和SHA；不公开具体核验内容、识别内容、人工内容或本地位置。",
        }
        add_false_fields(out)
        rows.append(out)
    return rows


def build_page_summary(rows: list[dict[str, str]], gap_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    source_active = [
        row for row in gap_rows
        if row.get("证据通道序号") in ACTIVE_CHANNELS and row.get("是否当前可并行执行") == "true"
    ]
    tasks_by_page = defaultdict(list)
    for row in source_active:
        tasks_by_page[row.get("页码版面键", "")].append(row)
    packets_by_page = defaultdict(list)
    for row in rows:
        packets_by_page[row.get("页码版面键", "")].append(row)

    out_rows = []
    sort_pages = sorted(
        tasks_by_page,
        key=lambda key: (
            as_int(tasks_by_page[key][0].get("来源页码", "")),
            side_rank(tasks_by_page[key][0].get("版面列", "")),
            key,
        ),
    )
    for seq, page_key in enumerate(sort_pages, start=1):
        tasks = tasks_by_page[page_key]
        packets = packets_by_page[page_key]
        first = tasks[0]
        w0_tasks = [row for row in tasks if CHANNEL_TO_WAVE[row.get("证据通道序号", "")] == "W0"]
        w1_tasks = [row for row in tasks if CHANNEL_TO_WAVE[row.get("证据通道序号", "")] == "W1"]
        first_packet = packets[0] if packets else {}
        out = {
            "G0冲突字段W0W1主动工作页列汇总ID": stable_id(
                "G0W0W1ACTIVEPAGE", [SOURCE_PDF_SHA256, page_key]
            ),
            "来源G0冲突字段W0W1主动工作包公开账本": source_path(OUTPUT),
            "来源G0冲突字段补证执行波次公开账本": source_path(GAP_WAVES),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段W0/W1主动工作页列汇总",
            "任务粒度": "页列",
            "页列汇总序号": str(seq),
            "页码版面键": page_key,
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "主动工作包数": str(len(packets)),
            "当前可并行任务数": str(len(tasks)),
            "W0一手证据与辅证采集任务数": str(len(w0_tasks)),
            "W1双人复核任务数": str(len(w1_tasks)),
            "涉及字段事实数": str(count_unique(tasks, "G0冲突字段补证闭环结果公开账本ID")),
            "涉及任务数": str(count_unique(tasks, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(tasks, "专业行ID")),
            "涉及院校代码数": str(count_unique(tasks, "院校代码")),
            "证据通道分布": dist(tasks, "证据通道"),
            "字段名分布": dist(tasks, "字段名"),
            "当前阻断桶分布": dist(tasks, "当前阻断桶"),
            "PDF原页待核任务数": first_packet.get("PDF原页待核任务数", ""),
            "湖北官方侧待核任务数": first_packet.get("湖北官方侧待核任务数", ""),
            "高校辅证线索任务数": first_packet.get("高校辅证线索任务数", ""),
            "需要双人复核任务数": first_packet.get("需要双人复核任务数", ""),
            "PDFOCR提示任务数": first_packet.get("PDFOCR提示任务数", ""),
            "机器坐标提示任务数": first_packet.get("机器坐标提示任务数", ""),
            "PDFOCR与高校辅证冲突任务数": first_packet.get("PDFOCR与高校辅证冲突任务数", ""),
            "高校源结构化接入候选字段数": first_packet.get("高校源结构化接入候选字段数", ""),
            "高校源最新对齐任务数合计": first_packet.get("高校源最新对齐任务数合计", ""),
            "主动工作包集合SHA256": sha256_values(
                item.get("G0冲突字段W0W1主动工作包公开账本ID", "") for item in packets
            ),
            "缺口任务集合SHA256": sha256_values(
                item.get("G0冲突字段补证缺口任务公开账本ID", "") for item in tasks
            ),
            "闭环结果集合SHA256": sha256_values(
                item.get("G0冲突字段补证闭环结果公开账本ID", "") for item in tasks
            ),
            "页列下一步动作": "先并行完成PDF原页、湖北官方侧、高校辅证和必要双人复核；完成前不得冲突定案、字段确认或写回。",
            "公开安全策略": "公开层只保存页列级状态、计数、证据编号和SHA；不公开具体核验内容、识别内容、人工内容或本地位置。",
        }
        add_false_fields(out)
        out_rows.append(out)
    return out_rows


def main() -> None:
    gap_rows = read_csv(GAP_TASKS)
    wave_rows = read_csv(GAP_WAVES)
    verification_pages = index_by_page(read_csv(VERIFICATION_PAGE_SUMMARY))
    evidence_pages = index_by_page(read_csv(PUBLIC_EVIDENCE_MAP))
    backlink_pages = index_by_page(read_csv(FIELD_BACKLINK_PAGE_SUMMARY))

    workboard_rows = build_workboard_rows(
        gap_rows,
        wave_rows,
        verification_pages,
        evidence_pages,
        backlink_pages,
    )
    page_summary_rows = build_page_summary(workboard_rows, gap_rows)

    write_csv(OUTPUT, workboard_rows, WORKBOARD_FIELDS)
    write_csv(PAGE_SUMMARY_OUTPUT, page_summary_rows, PAGE_SUMMARY_FIELDS)

    active_task_rows = [
        row for row in gap_rows
        if row.get("证据通道序号") in ACTIVE_CHANNELS and row.get("是否当前可并行执行") == "true"
    ]
    summary = {
        "status": "issue19_first_closure_g0_conflict_field_w0_w1_active_workboard_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_gap_tasks": source_path(GAP_TASKS),
        "source_gap_tasks_sha256": sha256_file(GAP_TASKS),
        "source_gap_waves": source_path(GAP_WAVES),
        "source_gap_waves_sha256": sha256_file(GAP_WAVES),
        "source_gap_wave_summary": source_path(GAP_WAVE_SUMMARY),
        "source_gap_wave_summary_sha256": sha256_file(GAP_WAVE_SUMMARY),
        "source_verification_page_summary": source_path(VERIFICATION_PAGE_SUMMARY),
        "source_verification_page_summary_sha256": sha256_file(VERIFICATION_PAGE_SUMMARY),
        "source_public_evidence_map": source_path(PUBLIC_EVIDENCE_MAP),
        "source_public_evidence_map_sha256": sha256_file(PUBLIC_EVIDENCE_MAP),
        "source_field_backlink_page_summary": source_path(FIELD_BACKLINK_PAGE_SUMMARY),
        "source_field_backlink_page_summary_sha256": sha256_file(FIELD_BACKLINK_PAGE_SUMMARY),
        "output_table": source_path(OUTPUT),
        "page_summary_table": source_path(PAGE_SUMMARY_OUTPUT),
        "workboard_row_count": len(workboard_rows),
        "page_summary_row_count": len(page_summary_rows),
        "source_gap_task_row_count": len(gap_rows),
        "active_task_row_count": len(active_task_rows),
        "active_wave_packet_count": len({row.get("来源波次包ID", "") for row in workboard_rows}),
        "unique_page_side_count": count_unique(active_task_rows, "页码版面键"),
        "unique_closure_result_count": count_unique(active_task_rows, "G0冲突字段补证闭环结果公开账本ID"),
        "unique_task_count": count_unique(active_task_rows, "稳定基座第一闭环明细任务ID"),
        "unique_major_row_count": count_unique(active_task_rows, "专业行ID"),
        "active_task_count_by_wave": dict(Counter(CHANNEL_TO_WAVE[row.get("证据通道序号", "")] for row in active_task_rows)),
        "active_task_count_by_channel": dict(Counter(row.get("证据通道序号", "") for row in active_task_rows)),
        "workboard_row_count_by_wave": dict(Counter(row.get("执行波次序号", "") for row in workboard_rows)),
        "workboard_row_count_by_channel": dict(Counter(row.get("证据通道序号", "") for row in workboard_rows)),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只抽取W0/W1当前可执行补证工作包，不确认字段事实，不写回，不进入推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    public_safety_check([OUTPUT, PAGE_SUMMARY_OUTPUT, SUMMARY_OUTPUT])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
