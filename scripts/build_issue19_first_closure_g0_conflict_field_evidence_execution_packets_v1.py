#!/usr/bin/env python3
"""Build G0 conflict-field evidence execution packets.

This layer turns the G0 conflict-field resolution gate into page-side execution
packets. It does not confirm any field fact. Public outputs only expose ids,
counts, missing-evidence status, evidence labels, and SHA256 digests; field
readings and local review materials stay outside the public repository.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"
LOCAL_REVIEW_ROOT = ROOT / "private"

GATE_PUBLIC = WORKING / "issue19-first-closure-g0-conflict-field-resolution-gate-v1-public-ledger.csv"
GATE_PAGE = WORKING / "issue19-first-closure-g0-conflict-field-resolution-gate-v1-page-summary.csv"
GATE_SUMMARY = WORKING / "issue19-first-closure-g0-conflict-field-resolution-gate-v1-summary.json"
OVERLAY_PUBLIC = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-public-ledger.csv"
OVERLAY_PAGE = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-page-summary.csv"

LOCAL_G0_PAGE_DIR = (
    LOCAL_REVIEW_ROOT / "review-assets/issue19-g0-conflict-field-review-overlay-v1/page-sides"
)
LOCAL_FIRST_REVIEW_HTML_DIR = (
    LOCAL_REVIEW_ROOT / "review-assets/issue19-stable-foundation-first-closure-review/html"
)

PACKET_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-execution-packets-v1-public-ledger.csv"
)
ITEM_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-execution-items-v1-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-execution-packets-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_evidence_execution_packets_v1"

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
    "G0冲突字段补证执行包公开账本ID",
    "来源G0冲突字段准出门禁公开账本",
    "来源G0冲突字段准出门禁页列汇总",
    "来源G0冲突字段准出门禁摘要",
    "来源G0冲突字段复核Overlay公开账本",
    "来源G0冲突字段复核Overlay页列汇总",
    "来源私有G0字段复核Overlay",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "补证执行包序号",
    "页码版面键",
    "来源页码",
    "版面列",
    "字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "回接泳道分布",
    "准出门禁状态分布",
    "主缺口桶分布",
    "PDF原页记录缺口字段数",
    "湖北官方记录缺口字段数",
    "高校辅证记录缺口字段数",
    "冲突处理缺口字段数",
    "双人复核缺口字段数",
    "三方一致性缺口字段数",
    "字段确认缺口字段数",
    "写回评审缺口字段数",
    "可进入私有写回评审字段数",
    "补证执行优先级",
    "补证执行泳道",
    "补证最小动作组合",
    "页列执行状态",
    "页列准出状态",
    "私有G0页列CSV证据编号",
    "私有G0页列CSV_SHA256",
    "私有核页HTML证据编号",
    "私有核页HTML_SHA256",
    "字段事实集合SHA256",
    "任务集合SHA256",
    "专业行集合SHA256",
    "字段复核记录SHA集合SHA256",
    "补证执行项集合SHA256",
    "下一步页列补证动作",
    "公开安全策略",
]

ITEM_FIELDS = [
    "G0冲突字段补证执行项公开账本ID",
    "来源G0冲突字段补证执行包公开账本",
    "来源G0冲突字段准出门禁公开账本",
    "来源G0冲突字段复核Overlay公开账本",
    "来源私有G0字段复核Overlay",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "补证执行项序号",
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
    "高校源桥接桶",
    "结构化接入候选数",
    "PDF原页记录缺口",
    "湖北官方记录缺口",
    "高校辅证记录缺口",
    "冲突处理缺口",
    "双人复核缺口",
    "三方一致性缺口",
    "字段确认缺口",
    "写回评审缺口",
    "必要缺口数",
    "准出门禁状态",
    "主缺口桶",
    "准出阻断等级",
    "字段写回评审状态",
    "G0字段Overlay状态",
    "补证执行优先级",
    "补证执行泳道",
    "字段补证动作顺序",
    "字段补证执行状态",
    "私有字段复核记录证据编号",
    "私有字段复核记录SHA256",
    "私有G0页列CSV证据编号",
    "私有G0页列CSV_SHA256",
    "私有核页HTML证据编号",
    "私有核页HTML_SHA256",
    "下一步字段补证动作",
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
    "院校专业组代码",
    "字段读数",
    "人工读数",
    "字段值",
    "候选值",
    "OCR正文",
    "OCR行文本",
    "截图路径",
    "人工复核备注",
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
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_values(values: list[str]) -> str:
    vals = sorted({clean(value) for value in values if clean(value)})
    return hashlib.sha256("|".join(vals).encode("utf-8")).hexdigest() if vals else ""


def add_false_fields(row: dict[str, str]) -> None:
    for field in FALSE_FIELDS:
        row[field] = "false"


def dist(rows: list[dict[str, str]], field: str) -> str:
    counts = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counts[key]}" for key in sorted(counts))


def count_true(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if row.get(field) == "true")


def execution_lane(rows: list[dict[str, str]]) -> str:
    if count_true(rows, "双人复核缺口"):
        return "R0-冲突字段双人核页优先"
    return "R1-冲突字段单人初核后抽检复核"


def execution_priority(rows: list[dict[str, str]]) -> str:
    if count_true(rows, "双人复核缺口"):
        return "P0-含双人复核缺口页列"
    if len(rows) >= 5:
        return "P1-字段数较多冲突页列"
    return "P2-常规冲突字段页列"


def minimum_actions(rows: list[dict[str, str]]) -> str:
    actions = [
        ("PDF原页记录缺口", "补PDF原页记录"),
        ("湖北官方记录缺口", "补湖北官方记录"),
        ("高校辅证记录缺口", "补高校辅证记录"),
        ("冲突处理缺口", "处理PDFOCR与高校辅证冲突"),
        ("双人复核缺口", "完成双人复核"),
        ("三方一致性缺口", "完成三方一致性判断"),
        ("字段确认缺口", "完成字段确认"),
        ("写回评审缺口", "提交写回前评审"),
    ]
    return "；".join(label for field, label in actions if count_true(rows, field))


def html_evidence_id(page_key: str) -> str:
    return f"FIRST-CLOSURE-REVIEW-HTML-{page_key}"


def main() -> None:
    gate_rows = read_csv(GATE_PUBLIC)
    gate_page_rows = read_csv(GATE_PAGE)
    gate_page_by_key = {row.get("页码版面键", ""): row for row in gate_page_rows}

    rows_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in gate_rows:
        rows_by_page[row.get("页码版面键", "")].append(row)

    packet_rows: list[dict[str, str]] = []
    item_rows: list[dict[str, str]] = []
    packet_id_by_page: dict[str, str] = {}

    for packet_seq, page_key in enumerate(sorted(rows_by_page), start=1):
        rows = sorted(
            rows_by_page[page_key],
            key=lambda row: (
                row.get("是否需要双人复核") != "true",
                row.get("字段名", ""),
                row.get("稳定基座第一闭环明细任务ID", ""),
            ),
        )
        source_page = gate_page_by_key.get(page_key, {})
        packet_id = stable_id("G0FIELDEXECPACKET", [SOURCE_PDF_SHA256, page_key])
        packet_id_by_page[page_key] = packet_id
        local_g0_page = LOCAL_G0_PAGE_DIR / f"{page_key}.csv"
        local_html = LOCAL_FIRST_REVIEW_HTML_DIR / f"{page_key}.html"
        packet = {
            "G0冲突字段补证执行包公开账本ID": packet_id,
            "来源G0冲突字段准出门禁公开账本": source_path(GATE_PUBLIC),
            "来源G0冲突字段准出门禁页列汇总": source_path(GATE_PAGE),
            "来源G0冲突字段准出门禁摘要": source_path(GATE_SUMMARY),
            "来源G0冲突字段复核Overlay公开账本": source_path(OVERLAY_PUBLIC),
            "来源G0冲突字段复核Overlay页列汇总": source_path(OVERLAY_PAGE),
            "来源私有G0字段复核Overlay": "g0_conflict_field_review_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段页列补证执行包",
            "任务粒度": "页列×字段补证执行包",
            "补证执行包序号": str(packet_seq),
            "页码版面键": page_key,
            "来源页码": rows[0].get("来源页码", ""),
            "版面列": rows[0].get("版面列", ""),
            "字段事实数": str(len(rows)),
            "涉及任务数": str(len({row.get("稳定基座第一闭环明细任务ID", "") for row in rows if row.get("稳定基座第一闭环明细任务ID", "")})),
            "涉及专业行数": str(len({row.get("专业行ID", "") for row in rows if row.get("专业行ID", "")})),
            "涉及院校代码数": str(len({row.get("院校代码", "") for row in rows if row.get("院校代码", "")})),
            "字段名分布": dist(rows, "字段名"),
            "回接泳道分布": dist(rows, "回接泳道"),
            "准出门禁状态分布": dist(rows, "准出门禁状态"),
            "主缺口桶分布": dist(rows, "主缺口桶"),
            "PDF原页记录缺口字段数": str(count_true(rows, "PDF原页记录缺口")),
            "湖北官方记录缺口字段数": str(count_true(rows, "湖北官方记录缺口")),
            "高校辅证记录缺口字段数": str(count_true(rows, "高校辅证记录缺口")),
            "冲突处理缺口字段数": str(count_true(rows, "冲突处理缺口")),
            "双人复核缺口字段数": str(count_true(rows, "双人复核缺口")),
            "三方一致性缺口字段数": str(count_true(rows, "三方一致性缺口")),
            "字段确认缺口字段数": str(count_true(rows, "字段确认缺口")),
            "写回评审缺口字段数": str(count_true(rows, "写回评审缺口")),
            "可进入私有写回评审字段数": str(sum(1 for row in rows if row.get("是否允许进入私有写回评审") == "true")),
            "补证执行优先级": execution_priority(rows),
            "补证执行泳道": execution_lane(rows),
            "补证最小动作组合": minimum_actions(rows),
            "页列执行状态": "pending_private_evidence_collection",
            "页列准出状态": "blocked_missing_required_field_evidence",
            "私有G0页列CSV证据编号": source_page.get("私有页列CSV证据编号", f"G0FIELD-PRIVATE-PAGE-{page_key}"),
            "私有G0页列CSV_SHA256": source_page.get("私有页列CSV_SHA256", sha256_file(local_g0_page)),
            "私有核页HTML证据编号": html_evidence_id(page_key),
            "私有核页HTML_SHA256": sha256_file(local_html),
            "字段事实集合SHA256": sha256_values([row.get("第一闭环事实范围缺口公开账本ID", "") for row in rows]),
            "任务集合SHA256": sha256_values([row.get("稳定基座第一闭环明细任务ID", "") for row in rows]),
            "专业行集合SHA256": sha256_values([row.get("专业行ID", "") for row in rows]),
            "字段复核记录SHA集合SHA256": sha256_values([row.get("私有字段复核记录SHA256", "") for row in rows]),
            "补证执行项集合SHA256": "",
            "下一步页列补证动作": "按页列打开本地未公开核页材料，逐字段补PDF原页记录、湖北官方记录和高校辅证记录；冲突与必要双人复核完成前不得写回。",
            "公开安全策略": "公开层只保存页列ID、缺口计数、证据编号和SHA；字段明细、OCR文本、学校专业明细和本地核验内容不公开。",
        }
        add_false_fields(packet)
        packet_rows.append(packet)

        for row in rows:
            item_id = stable_id(
                "G0FIELDEXECITEM",
                [SOURCE_PDF_SHA256, packet_id, row.get("G0冲突字段准出门禁公开账本ID", "")],
            )
            item = {
                "G0冲突字段补证执行项公开账本ID": item_id,
                "来源G0冲突字段补证执行包公开账本": source_path(PACKET_OUTPUT),
                "来源G0冲突字段准出门禁公开账本": source_path(GATE_PUBLIC),
                "来源G0冲突字段复核Overlay公开账本": source_path(OVERLAY_PUBLIC),
                "来源私有G0字段复核Overlay": "g0_conflict_field_review_overlay_not_public",
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "生成日期": GENERATED_AT,
                "数据阶段": DATA_STAGE,
                "主表粒度": "G0冲突字段补证执行项",
                "任务粒度": "字段事实×补证执行项",
                "补证执行项序号": str(len(item_rows) + 1),
                "G0冲突字段补证执行包公开账本ID": packet_id,
                "G0冲突字段准出门禁公开账本ID": row.get("G0冲突字段准出门禁公开账本ID", ""),
                "G0冲突字段复核Overlay公开账本ID": row.get("G0冲突字段复核Overlay公开账本ID", ""),
                "G0冲突动作包闭环工作台ID": row.get("G0冲突动作包闭环工作台ID", ""),
                "高校源字段回接队列ID": row.get("高校源字段回接队列ID", ""),
                "W0B0执行预填明细公开审计ID": row.get("W0B0执行预填明细公开审计ID", ""),
                "第一闭环事实范围缺口公开账本ID": row.get("第一闭环事实范围缺口公开账本ID", ""),
                "第一闭环字段事实公开账本ID": row.get("第一闭环字段事实公开账本ID", ""),
                "第一闭环字段核验状态ID": row.get("第一闭环字段核验状态ID", ""),
                "稳定基座第一闭环明细任务ID": row.get("稳定基座第一闭环明细任务ID", ""),
                "页码版面键": page_key,
                "来源页码": row.get("来源页码", ""),
                "版面列": row.get("版面列", ""),
                "专业行ID": row.get("专业行ID", ""),
                "专业组出现ID": row.get("专业组出现ID", ""),
                "院校代码": row.get("院校代码", ""),
                "事实域": row.get("事实域", ""),
                "事实类型": row.get("事实类型", ""),
                "字段名": row.get("字段名", ""),
                "回接泳道": row.get("回接泳道", ""),
                "回接批次": row.get("回接批次", ""),
                "字段事实状态": row.get("字段事实状态", ""),
                "字段核验优先级": row.get("字段核验优先级", ""),
                "PDFOCR与高校辅证关系桶": row.get("PDFOCR与高校辅证关系桶", ""),
                "是否有PDFOCR提示": row.get("是否有PDFOCR提示", ""),
                "是否有高校辅证线索": row.get("是否有高校辅证线索", ""),
                "是否存在PDFOCR与高校冲突": row.get("是否存在PDFOCR与高校冲突", ""),
                "是否需要人工直接看图": row.get("是否需要人工直接看图", ""),
                "是否需要双人复核": row.get("是否需要双人复核", ""),
                "高校源桥接桶": row.get("高校源桥接桶", ""),
                "结构化接入候选数": row.get("结构化接入候选数", ""),
                "PDF原页记录缺口": row.get("PDF原页记录缺口", ""),
                "湖北官方记录缺口": row.get("湖北官方记录缺口", ""),
                "高校辅证记录缺口": row.get("高校辅证记录缺口", ""),
                "冲突处理缺口": row.get("冲突处理缺口", ""),
                "双人复核缺口": row.get("双人复核缺口", ""),
                "三方一致性缺口": row.get("三方一致性缺口", ""),
                "字段确认缺口": row.get("字段确认缺口", ""),
                "写回评审缺口": row.get("写回评审缺口", ""),
                "必要缺口数": row.get("必要缺口数", ""),
                "准出门禁状态": row.get("准出门禁状态", ""),
                "主缺口桶": row.get("主缺口桶", ""),
                "准出阻断等级": row.get("准出阻断等级", ""),
                "字段写回评审状态": row.get("字段写回评审状态", ""),
                "G0字段Overlay状态": row.get("G0字段Overlay状态", ""),
                "补证执行优先级": execution_priority(rows),
                "补证执行泳道": execution_lane(rows),
                "字段补证动作顺序": minimum_actions([row]),
                "字段补证执行状态": "pending_private_evidence_collection",
                "私有字段复核记录证据编号": row.get("私有字段复核记录证据编号", ""),
                "私有字段复核记录SHA256": row.get("私有字段复核记录SHA256", ""),
                "私有G0页列CSV证据编号": packet["私有G0页列CSV证据编号"],
                "私有G0页列CSV_SHA256": packet["私有G0页列CSV_SHA256"],
                "私有核页HTML证据编号": packet["私有核页HTML证据编号"],
                "私有核页HTML_SHA256": packet["私有核页HTML_SHA256"],
                "下一步字段补证动作": "在本地未公开复核表补齐该字段的PDF原页记录、湖北官方记录和高校辅证记录；冲突处理、必要复核和字段确认完成前不得写回。",
                "公开安全策略": "公开层只保存字段ID、缺口状态、证据编号和SHA；字段明细、OCR文本、学校专业明细和本地核验内容不公开。",
            }
            add_false_fields(item)
            item_rows.append(item)

    items_by_packet: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in item_rows:
        items_by_packet[item["G0冲突字段补证执行包公开账本ID"]].append(item)
    for packet in packet_rows:
        packet["补证执行项集合SHA256"] = sha256_values(
            [
                item.get("G0冲突字段补证执行项公开账本ID", "")
                for item in items_by_packet[packet["G0冲突字段补证执行包公开账本ID"]]
            ]
        )

    write_csv(PACKET_OUTPUT, packet_rows, PACKET_FIELDS)
    write_csv(ITEM_OUTPUT, item_rows, ITEM_FIELDS)

    summary = {
        "status": "issue19_first_closure_g0_conflict_field_evidence_execution_packets_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_gate_public": source_path(GATE_PUBLIC),
        "source_gate_public_sha256": sha256_file(GATE_PUBLIC),
        "source_gate_page": source_path(GATE_PAGE),
        "source_gate_page_sha256": sha256_file(GATE_PAGE),
        "source_gate_summary": source_path(GATE_SUMMARY),
        "source_gate_summary_sha256": sha256_file(GATE_SUMMARY),
        "source_overlay_public": source_path(OVERLAY_PUBLIC),
        "source_overlay_public_sha256": sha256_file(OVERLAY_PUBLIC),
        "source_overlay_page": source_path(OVERLAY_PAGE),
        "source_overlay_page_sha256": sha256_file(OVERLAY_PAGE),
        "private_g0_page_csv_count": len([path for path in LOCAL_G0_PAGE_DIR.glob("*.csv") if path.stem in rows_by_page]),
        "private_review_html_count": len([path for path in LOCAL_FIRST_REVIEW_HTML_DIR.glob("*.html") if path.stem in rows_by_page]),
        "output_packet_table": source_path(PACKET_OUTPUT),
        "output_item_table": source_path(ITEM_OUTPUT),
        "packet_row_count": len(packet_rows),
        "item_row_count": len(item_rows),
        "source_gate_row_count": len(gate_rows),
        "source_gate_page_row_count": len(gate_page_rows),
        "unique_fact_scope_count": len({row.get("第一闭环事实范围缺口公开账本ID", "") for row in item_rows}),
        "unique_page_side_count": len(rows_by_page),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID", "") for row in item_rows}),
        "unique_major_row_count": len({row.get("专业行ID", "") for row in item_rows}),
        "field_name_counts": dict(Counter(row.get("字段名", "") for row in item_rows)),
        "execution_priority_counts": dict(Counter(row.get("补证执行优先级", "") for row in packet_rows)),
        "execution_lane_counts": dict(Counter(row.get("补证执行泳道", "") for row in packet_rows)),
        "item_execution_lane_counts": dict(Counter(row.get("补证执行泳道", "") for row in item_rows)),
        "gate_status_counts": dict(Counter(row.get("准出门禁状态", "") for row in item_rows)),
        "pdf_record_gap_count": count_true(item_rows, "PDF原页记录缺口"),
        "hubei_official_record_gap_count": count_true(item_rows, "湖北官方记录缺口"),
        "school_side_record_gap_count": count_true(item_rows, "高校辅证记录缺口"),
        "conflict_resolution_gap_count": count_true(item_rows, "冲突处理缺口"),
        "double_review_gap_count": count_true(item_rows, "双人复核缺口"),
        "three_way_gap_count": count_true(item_rows, "三方一致性缺口"),
        "field_confirmation_gap_count": count_true(item_rows, "字段确认缺口"),
        "writeback_review_gap_count": count_true(item_rows, "写回评审缺口"),
        "ready_for_private_writeback_review_count": sum(1 for row in item_rows if row.get("是否允许进入私有写回评审") == "true"),
        "field_writeback_allowed_count": sum(1 for row in item_rows if row.get("是否允许写回字段事实") == "true"),
        "recommendation_basis_allowed_count": sum(1 for row in item_rows if row.get("是否允许作为志愿推荐依据") == "true"),
        "school_major_suggestion_allowed_count": sum(1 for row in item_rows if row.get("是否允许生成学校专业建议") == "true"),
        "official_plan_replacement_allowed_count": sum(1 for row in item_rows if row.get("是否允许官网证据替代湖北官方计划") == "true"),
        "next_stage_allowed_count": sum(1 for row in item_rows if row.get("可进入下一阶段") == "true"),
        "final_available_count": sum(1 for row in item_rows if row.get("最终可用") == "true"),
        "public_boundary": "该执行包只安排G0冲突字段补证，不公开字段明细或本地核验内容，不确认字段事实。",
    }
    write_json(SUMMARY_OUTPUT, summary)

    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [PACKET_OUTPUT, ITEM_OUTPUT, SUMMARY_OUTPUT]
    )
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if hits:
        raise SystemExit(f"public output contains forbidden tokens: {hits}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
