#!/usr/bin/env python3
"""Build G0 conflict-field evidence gap task queue.

This layer turns the G0 conflict-field closure result ledger into concrete
evidence-gap tasks. It is still public-safe: it publishes only IDs, status
buckets, counts, evidence labels, and SHA256 digests. It does not publish field
values, OCR text, school/profession names, reviewer notes, or local paths.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

CLOSURE_PUBLIC = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-closure-result-v1-public-ledger.csv"
)
CLOSURE_PAGE = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-closure-result-v1-page-summary.csv"
)
CLOSURE_SUMMARY = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-closure-result-v1-summary.json"
)

OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-public-ledger.csv"
)
PAGE_CHANNEL_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-page-channel-summary.csv"
)
CHANNEL_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-channel-summary.csv"
)
SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_evidence_gap_tasks_v1"

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

TASK_FIELDS = [
    "G0冲突字段补证缺口任务公开账本ID",
    "来源G0冲突字段补证闭环结果公开账本",
    "来源G0冲突字段补证闭环结果页列汇总",
    "来源G0冲突字段补证闭环结果摘要",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "缺口任务序号",
    "证据通道序号",
    "证据通道",
    "证据通道类型",
    "证据通道执行层级",
    "证据缺口任务状态",
    "是否当前可并行执行",
    "当前通道状态",
    "当前阻断桶",
    "G0冲突字段补证闭环结果公开账本ID",
    "G0冲突字段补证执行项公开账本ID",
    "G0冲突字段补证执行包公开账本ID",
    "G0冲突字段准出门禁公开账本ID",
    "G0冲突字段复核Overlay公开账本ID",
    "G0冲突动作包闭环工作台ID",
    "高校源字段回接队列ID",
    "W0B0执行预填明细公开审计ID",
    "第一闭环事实范围缺口公开账本ID",
    "第一闭环字段事实公开账本ID",
    "第一闭环字段核验状态ID",
    "稳定基座第一闭环明细任务ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "事实域",
    "事实类型",
    "字段名",
    "补证执行优先级",
    "补证执行泳道",
    "回接泳道",
    "回接批次",
    "字段事实状态",
    "字段核验优先级",
    "PDFOCR与高校辅证关系桶",
    "是否有PDFOCR提示",
    "是否有高校辅证线索",
    "是否存在PDFOCR与高校冲突",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "PDF原页记录缺口",
    "湖北官方记录缺口",
    "高校辅证记录缺口",
    "冲突处理缺口",
    "双人复核缺口",
    "三方一致性缺口",
    "字段确认缺口",
    "写回评审缺口",
    "必要证据缺口数",
    "私有字段复核记录证据编号",
    "私有字段复核记录SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有核页HTML证据编号",
    "私有核页HTML_SHA256",
    "当前私有页列CSV记录SHA256",
    "下一步缺口处理动作",
    "公开安全策略",
]

PAGE_CHANNEL_FIELDS = [
    "G0冲突字段补证缺口页列通道汇总ID",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源G0冲突字段补证闭环结果页列汇总",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "页列通道汇总序号",
    "页码版面键",
    "来源页码",
    "版面列",
    "证据通道序号",
    "证据通道",
    "证据通道类型",
    "证据通道执行层级",
    "缺口任务数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "可并行执行任务数",
    "待前置闭环任务数",
    "当前通道状态分布",
    "当前阻断桶分布",
    "补证执行优先级分布",
    "补证执行泳道分布",
    "缺口任务集合SHA256",
    "闭环结果集合SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有核页HTML证据编号",
    "私有核页HTML_SHA256",
    "页列通道下一步动作",
    "公开安全策略",
]

CHANNEL_FIELDS = [
    "G0冲突字段补证缺口通道汇总ID",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "通道汇总序号",
    "证据通道序号",
    "证据通道",
    "证据通道类型",
    "证据通道执行层级",
    "缺口任务数",
    "涉及页列数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "可并行执行任务数",
    "待前置闭环任务数",
    "当前通道状态分布",
    "当前阻断桶分布",
    "缺口任务集合SHA256",
    "闭环结果集合SHA256",
    "通道下一步动作",
    "公开安全策略",
]

CHANNELS = [
    {
        "seq": "01",
        "name": "PDF原页记录",
        "kind": "PDF原页核页",
        "level": "E0-PDF原页核页先行",
        "status_field": "PDF原页核验结果状态",
        "gap_field": "PDF原页记录缺口",
        "ready_value": "pdf_page_record_present_sha_only",
        "blocked": "G0-缺PDF原页记录",
        "parallel": "true",
        "task_status": "pending_primary_evidence_collection",
        "action": "在本地未公开页列材料中补齐PDF原页记录；未补齐前不得写回字段事实。",
    },
    {
        "seq": "02",
        "name": "湖北官方侧记录",
        "kind": "湖北官方或省招办计划核验",
        "level": "E1-湖北官方侧核验",
        "status_field": "湖北官方侧核验状态",
        "gap_field": "湖北官方记录缺口",
        "ready_value": "hubei_official_present_sha_only",
        "blocked": "G1-缺湖北官方记录",
        "parallel": "true",
        "task_status": "pending_primary_evidence_collection",
        "action": "补齐湖北官方系统或省招办计划侧记录；高校官网不得替代湖北官方计划。",
    },
    {
        "seq": "03",
        "name": "高校辅证人工核验",
        "kind": "高校官网辅证人工核验",
        "level": "E2-高校辅证人工核验",
        "status_field": "高校官网辅证核验状态",
        "gap_field": "高校辅证记录缺口",
        "ready_values": {"school_source_present_sha_only", "school_source_supports_pdf"},
        "blocked": "G2-缺高校辅证人工核验",
        "parallel": "true",
        "task_status": "pending_primary_evidence_collection",
        "action": "把高校侧线索人工核验为证据记录；仅作double check，不替代湖北官方计划。",
    },
    {
        "seq": "04",
        "name": "冲突处理",
        "kind": "冲突解释和处理",
        "level": "E3-冲突处理",
        "status_field": "冲突处理状态",
        "gap_field": "冲突处理缺口",
        "ready_value": "conflict_resolved_same_direction",
        "blocked": "G3-冲突未处理",
        "parallel": "false",
        "task_status": "blocked_until_primary_evidence_present",
        "action": "在PDF原页、湖北官方侧和高校辅证记录齐备后处理冲突方向。",
    },
    {
        "seq": "05",
        "name": "双人复核",
        "kind": "双人复核",
        "level": "E3-双人复核",
        "status_field": "双人复核结果状态",
        "gap_field": "双人复核缺口",
        "ready_values": {"not_required", "double_review_completed_sha_only"},
        "blocked": "G4-双人复核未完成",
        "parallel": "true",
        "task_status": "pending_double_review",
        "action": "需要双人复核的字段先完成A/B复核和一致性结论；未完成前不得写回。",
    },
    {
        "seq": "06",
        "name": "三方一致性闭环",
        "kind": "PDF/湖北官方/高校辅证三方闭环",
        "level": "E4-三方一致性闭环",
        "status_field": "三方闭环状态",
        "gap_field": "三方一致性缺口",
        "ready_value": "closed_pdf_hubei_school_consistent",
        "blocked": "G5-三方一致性未闭环",
        "parallel": "false",
        "task_status": "blocked_until_primary_evidence_present",
        "action": "等待PDF原页、湖北官方侧、高校辅证和必要双人复核后再做三方一致性闭环。",
    },
    {
        "seq": "07",
        "name": "字段确认",
        "kind": "字段确认",
        "level": "E5-字段确认",
        "status_field": "字段确认状态",
        "gap_field": "字段确认缺口",
        "ready_value": "ready_for_private_writeback_review_sha_only",
        "blocked": "G6-字段确认未填写",
        "parallel": "false",
        "task_status": "blocked_until_three_way_closure",
        "action": "三方闭环后在私有材料中填写字段确认；公开层仍不保存字段记录。",
    },
    {
        "seq": "08",
        "name": "写回评审",
        "kind": "字段写回评审",
        "level": "E6-写回评审",
        "status_field": "字段写回评审状态",
        "gap_field": "写回评审缺口",
        "ready_value": "ready_for_private_writeback_review_sha_only",
        "blocked": "G7-写回评审建议未填写",
        "parallel": "false",
        "task_status": "blocked_until_field_confirmation",
        "action": "字段确认完成后进入私有写回评审；通过评审前仍不得写回或推荐。",
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
    "PDF原页字段人工读数",
    "湖北官方字段值",
    "高校官网字段值",
    "高校辅证人工核验记录值",
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


def truthy(value: object) -> bool:
    return clean(value).lower() == "true"


def dist(rows: list[dict[str, str]], field: str) -> str:
    counter = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter))


def count_unique(rows: list[dict[str, str]], field: str) -> int:
    return len({clean(row.get(field, "")) for row in rows if clean(row.get(field, ""))})


def needs_channel_task(row: dict[str, str], channel: dict[str, object]) -> bool:
    gap_field = clean(channel.get("gap_field", ""))
    if gap_field and row.get(gap_field) != "true":
        return False
    status = clean(row.get(clean(channel["status_field"]), ""))
    ready_values = channel.get("ready_values")
    if ready_values:
        return status not in ready_values
    return status != clean(channel.get("ready_value", ""))


def channel_blocker(row: dict[str, str], channel: dict[str, object]) -> str:
    if clean(channel["name"]) == "高校辅证人工核验":
        status = clean(row.get("高校官网辅证核验状态", ""))
        if status == "school_source_pending":
            return "G2a-缺高校辅证线索"
        if status == "school_source_seed_present_pending_manual_review":
            return "G2b-高校辅证种子待人工核验"
    return clean(channel["blocked"])


def build_task(row: dict[str, str], channel: dict[str, object], seq: int) -> dict[str, str]:
    task = {
        "G0冲突字段补证缺口任务公开账本ID": stable_id(
            "G0FIELDGAPTASK",
            [
                SOURCE_PDF_SHA256,
                row.get("G0冲突字段补证闭环结果公开账本ID", ""),
                clean(channel["seq"]),
            ],
        ),
        "来源G0冲突字段补证闭环结果公开账本": source_path(CLOSURE_PUBLIC),
        "来源G0冲突字段补证闭环结果页列汇总": source_path(CLOSURE_PAGE),
        "来源G0冲突字段补证闭环结果摘要": source_path(CLOSURE_SUMMARY),
        "来源期号": SOURCE_ISSUE,
        "来源PDF_SHA256": SOURCE_PDF_SHA256,
        "生成日期": GENERATED_AT,
        "数据阶段": DATA_STAGE,
        "主表粒度": "G0冲突字段补证缺口任务",
        "任务粒度": "字段事实×证据缺口通道",
        "缺口任务序号": str(seq),
        "证据通道序号": clean(channel["seq"]),
        "证据通道": clean(channel["name"]),
        "证据通道类型": clean(channel["kind"]),
        "证据通道执行层级": clean(channel["level"]),
        "证据缺口任务状态": clean(channel["task_status"]),
        "是否当前可并行执行": clean(channel["parallel"]),
        "当前通道状态": clean(row.get(clean(channel["status_field"]), "")),
        "当前阻断桶": channel_blocker(row, channel),
        "下一步缺口处理动作": clean(channel["action"]),
        "公开安全策略": "公开层只保存ID、状态、计数、证据编号和SHA；不公开具体核验内容、识别内容、字段记录、人工内容或本地位置。",
    }
    add_false_fields(task)
    for field in [
        "G0冲突字段补证闭环结果公开账本ID",
        "G0冲突字段补证执行项公开账本ID",
        "G0冲突字段补证执行包公开账本ID",
        "G0冲突字段准出门禁公开账本ID",
        "G0冲突字段复核Overlay公开账本ID",
        "G0冲突动作包闭环工作台ID",
        "高校源字段回接队列ID",
        "W0B0执行预填明细公开审计ID",
        "第一闭环事实范围缺口公开账本ID",
        "第一闭环字段事实公开账本ID",
        "第一闭环字段核验状态ID",
        "稳定基座第一闭环明细任务ID",
        "页码版面键",
        "来源页码",
        "版面列",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "事实域",
        "事实类型",
        "字段名",
        "补证执行优先级",
        "补证执行泳道",
        "回接泳道",
        "回接批次",
        "字段事实状态",
        "字段核验优先级",
        "PDFOCR与高校辅证关系桶",
        "是否有PDFOCR提示",
        "是否有高校辅证线索",
        "是否存在PDFOCR与高校冲突",
        "是否需要人工直接看图",
        "是否需要双人复核",
        "PDF原页记录缺口",
        "湖北官方记录缺口",
        "高校辅证记录缺口",
        "冲突处理缺口",
        "双人复核缺口",
        "三方一致性缺口",
        "字段确认缺口",
        "写回评审缺口",
        "必要证据缺口数",
        "私有字段复核记录证据编号",
        "私有字段复核记录SHA256",
        "私有页列CSV证据编号",
        "私有页列CSV_SHA256",
        "私有核页HTML证据编号",
        "私有核页HTML_SHA256",
        "当前私有页列CSV记录SHA256",
    ]:
        task[field] = row.get(field, "")
    return task


def summarize_page_channel(
    tasks: list[dict[str, str]],
    closure_page_by_page: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    grouped = defaultdict(list)
    for row in tasks:
        grouped[(row.get("页码版面键", ""), row.get("证据通道序号", ""))].append(row)
    rows = []
    for seq, ((page_key, channel_seq), group) in enumerate(sorted(grouped.items()), start=1):
        channel = next(item for item in CHANNELS if item["seq"] == channel_seq)
        closure_page = closure_page_by_page.get(page_key, {})
        out = {
            "G0冲突字段补证缺口页列通道汇总ID": stable_id(
                "G0FIELDGAPPAGE", [SOURCE_PDF_SHA256, page_key, channel_seq]
            ),
            "来源G0冲突字段补证缺口任务公开账本": source_path(OUTPUT),
            "来源G0冲突字段补证闭环结果页列汇总": source_path(CLOSURE_PAGE),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段补证缺口页列通道汇总",
            "任务粒度": "页列×证据缺口通道",
            "页列通道汇总序号": str(seq),
            "页码版面键": page_key,
            "来源页码": group[0].get("来源页码", ""),
            "版面列": group[0].get("版面列", ""),
            "证据通道序号": channel_seq,
            "证据通道": clean(channel["name"]),
            "证据通道类型": clean(channel["kind"]),
            "证据通道执行层级": clean(channel["level"]),
            "缺口任务数": str(len(group)),
            "涉及字段事实数": str(count_unique(group, "G0冲突字段补证闭环结果公开账本ID")),
            "涉及任务数": str(count_unique(group, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(group, "专业行ID")),
            "涉及院校代码数": str(count_unique(group, "院校代码")),
            "字段名分布": dist(group, "字段名"),
            "可并行执行任务数": str(sum(1 for item in group if item.get("是否当前可并行执行") == "true")),
            "待前置闭环任务数": str(sum(1 for item in group if item.get("是否当前可并行执行") != "true")),
            "当前通道状态分布": dist(group, "当前通道状态"),
            "当前阻断桶分布": dist(group, "当前阻断桶"),
            "补证执行优先级分布": dist(group, "补证执行优先级"),
            "补证执行泳道分布": dist(group, "补证执行泳道"),
            "缺口任务集合SHA256": sha256_values(
                item.get("G0冲突字段补证缺口任务公开账本ID", "") for item in group
            ),
            "闭环结果集合SHA256": sha256_values(
                item.get("G0冲突字段补证闭环结果公开账本ID", "") for item in group
            ),
            "私有页列CSV证据编号": closure_page.get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": closure_page.get("私有页列CSV_SHA256", ""),
            "私有核页HTML证据编号": closure_page.get("私有核页HTML证据编号", ""),
            "私有核页HTML_SHA256": closure_page.get("私有核页HTML_SHA256", ""),
            "页列通道下一步动作": clean(channel["action"]),
            "公开安全策略": "公开层只保存页列通道状态、计数、证据编号和SHA；不公开具体核验内容、识别内容、字段记录、人工内容或本地位置。",
        }
        add_false_fields(out)
        rows.append(out)
    return rows


def summarize_channel(tasks: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for seq, channel in enumerate(CHANNELS, start=1):
        group = [row for row in tasks if row.get("证据通道序号") == channel["seq"]]
        out = {
            "G0冲突字段补证缺口通道汇总ID": stable_id(
                "G0FIELDGAPCHANNEL", [SOURCE_PDF_SHA256, clean(channel["seq"])]
            ),
            "来源G0冲突字段补证缺口任务公开账本": source_path(OUTPUT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段补证缺口通道汇总",
            "任务粒度": "证据缺口通道",
            "通道汇总序号": str(seq),
            "证据通道序号": clean(channel["seq"]),
            "证据通道": clean(channel["name"]),
            "证据通道类型": clean(channel["kind"]),
            "证据通道执行层级": clean(channel["level"]),
            "缺口任务数": str(len(group)),
            "涉及页列数": str(count_unique(group, "页码版面键")),
            "涉及字段事实数": str(count_unique(group, "G0冲突字段补证闭环结果公开账本ID")),
            "涉及任务数": str(count_unique(group, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(group, "专业行ID")),
            "涉及院校代码数": str(count_unique(group, "院校代码")),
            "字段名分布": dist(group, "字段名"),
            "可并行执行任务数": str(sum(1 for item in group if item.get("是否当前可并行执行") == "true")),
            "待前置闭环任务数": str(sum(1 for item in group if item.get("是否当前可并行执行") != "true")),
            "当前通道状态分布": dist(group, "当前通道状态"),
            "当前阻断桶分布": dist(group, "当前阻断桶"),
            "缺口任务集合SHA256": sha256_values(
                item.get("G0冲突字段补证缺口任务公开账本ID", "") for item in group
            ),
            "闭环结果集合SHA256": sha256_values(
                item.get("G0冲突字段补证闭环结果公开账本ID", "") for item in group
            ),
            "通道下一步动作": clean(channel["action"]),
            "公开安全策略": "公开层只保存通道状态、计数和SHA；不公开具体核验内容、识别内容、字段记录、人工内容或本地位置。",
        }
        add_false_fields(out)
        rows.append(out)
    return rows


def public_safety_check(paths: list[Path]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    leaked = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if leaked:
        raise RuntimeError(f"public output contains forbidden tokens: {leaked[:20]}")


def main() -> None:
    closure_rows = read_csv(CLOSURE_PUBLIC)
    closure_page_rows = read_csv(CLOSURE_PAGE)
    closure_page_by_page = {row.get("页码版面键", ""): row for row in closure_page_rows}

    task_rows: list[dict[str, str]] = []
    for closure_row in closure_rows:
        for channel in CHANNELS:
            if needs_channel_task(closure_row, channel):
                task_rows.append(build_task(closure_row, channel, len(task_rows) + 1))

    page_channel_rows = summarize_page_channel(task_rows, closure_page_by_page)
    channel_rows = summarize_channel(task_rows)

    write_csv(OUTPUT, task_rows, TASK_FIELDS)
    write_csv(PAGE_CHANNEL_OUTPUT, page_channel_rows, PAGE_CHANNEL_FIELDS)
    write_csv(CHANNEL_OUTPUT, channel_rows, CHANNEL_FIELDS)

    status_counter = Counter(row["证据缺口任务状态"] for row in task_rows)
    channel_counter = Counter(row["证据通道"] for row in task_rows)
    blocker_counter = Counter(row["当前阻断桶"] for row in task_rows)
    parallel_counter = Counter(row["是否当前可并行执行"] for row in task_rows)

    summary = {
        "status": "issue19_first_closure_g0_conflict_field_evidence_gap_tasks_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_closure_public": source_path(CLOSURE_PUBLIC),
        "source_closure_public_sha256": sha256_file(CLOSURE_PUBLIC),
        "source_closure_page": source_path(CLOSURE_PAGE),
        "source_closure_page_sha256": sha256_file(CLOSURE_PAGE),
        "source_closure_summary": source_path(CLOSURE_SUMMARY),
        "source_closure_summary_sha256": sha256_file(CLOSURE_SUMMARY),
        "output_table": source_path(OUTPUT),
        "page_channel_summary_table": source_path(PAGE_CHANNEL_OUTPUT),
        "channel_summary_table": source_path(CHANNEL_OUTPUT),
        "row_count": len(task_rows),
        "page_channel_summary_row_count": len(page_channel_rows),
        "channel_summary_row_count": len(channel_rows),
        "source_closure_row_count": len(closure_rows),
        "source_closure_page_row_count": len(closure_page_rows),
        "unique_closure_result_count": count_unique(task_rows, "G0冲突字段补证闭环结果公开账本ID"),
        "unique_page_side_count": count_unique(task_rows, "页码版面键"),
        "unique_task_count": count_unique(task_rows, "稳定基座第一闭环明细任务ID"),
        "unique_major_row_count": count_unique(task_rows, "专业行ID"),
        "unique_channel_count": count_unique(task_rows, "证据通道"),
        "field_name_counts": dict(Counter(row.get("字段名", "") for row in closure_rows)),
        "channel_task_counts": dict(channel_counter),
        "task_status_counts": dict(status_counter),
        "blocker_counts": dict(blocker_counter),
        "parallel_status_counts": dict(parallel_counter),
        "pdf_page_task_count": channel_counter.get("PDF原页记录", 0),
        "hubei_official_task_count": channel_counter.get("湖北官方侧记录", 0),
        "school_source_task_count": channel_counter.get("高校辅证人工核验", 0),
        "conflict_resolution_task_count": channel_counter.get("冲突处理", 0),
        "double_review_task_count": channel_counter.get("双人复核", 0),
        "three_way_task_count": channel_counter.get("三方一致性闭环", 0),
        "field_confirmation_task_count": channel_counter.get("字段确认", 0),
        "writeback_review_task_count": channel_counter.get("写回评审", 0),
        "parallel_executable_task_count": parallel_counter.get("true", 0),
        "blocked_until_predecessor_task_count": parallel_counter.get("false", 0),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只把G0冲突字段补证闭环结果拆成证据缺口任务，不确认字段事实，不写回，不进入推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    public_safety_check([OUTPUT, PAGE_CHANNEL_OUTPUT, CHANNEL_OUTPUT, SUMMARY_OUTPUT])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
