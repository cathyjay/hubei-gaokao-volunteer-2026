#!/usr/bin/env python3
"""Build the G0 conflict-field resolution gate.

This gate reads the public G0 conflict-field overlay and its local non-public
review rows. Public outputs keep only ids, status, missing-evidence flags,
counts, and SHA256 digests. Field readings, OCR text, school/profession names,
reviewer notes, and local paths stay under the ignored local review assets.
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

OVERLAY_PUBLIC = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-public-ledger.csv"
OVERLAY_PAGE = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-page-summary.csv"
OVERLAY_SUMMARY = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-summary.json"
LOCAL_OVERLAY = (
    LOCAL_REVIEW_ROOT
    / "review-assets/issue19-g0-conflict-field-review-overlay-v1/g0-conflict-field-review-private-overlay.csv"
)

PUBLIC_OUTPUT = WORKING / "issue19-first-closure-g0-conflict-field-resolution-gate-v1-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-first-closure-g0-conflict-field-resolution-gate-v1-page-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-g0-conflict-field-resolution-gate-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_resolution_gate_v1"

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

FIELDS = [
    "G0冲突字段准出门禁公开账本ID",
    "来源G0冲突字段复核Overlay公开账本",
    "来源G0冲突字段复核Overlay页列汇总",
    "来源G0冲突字段复核Overlay摘要",
    "来源私有G0字段复核Overlay",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "准出门禁序号",
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
    "私有字段复核记录证据编号",
    "私有字段复核记录SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
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
    "下一步字段准出动作",
    "公开安全策略",
]

PAGE_FIELDS = [
    "G0冲突字段准出门禁页列汇总ID",
    "来源G0冲突字段准出门禁公开账本",
    "来源G0冲突字段复核Overlay页列汇总",
    "来源私有G0字段复核Overlay",
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
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "字段事实集合SHA256",
    "任务集合SHA256",
    "专业行集合SHA256",
    "页列准出状态",
    "页列下一步字段准出动作",
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


def boolish(value: str) -> bool:
    return clean(value).lower() == "true"


def local_status(row: dict[str, str], requires_double_review: bool) -> dict[str, bool]:
    pdf_done = bool(clean(row.get("PDF原页字段人工读数", "")))
    hubei_done = bool(clean(row.get("湖北官方字段值", "")))
    school_done = bool(clean(row.get("高校辅证人工核验记录值", "")))
    double_done = bool(
        clean(row.get("PDF核页复核人A", ""))
        and clean(row.get("PDF核页复核人B", ""))
        and clean(row.get("双人一致性结论", ""))
    )
    three_way_done = bool(clean(row.get("三方一致性结论", "")))
    field_confirm_done = bool(clean(row.get("字段确认值", "")))
    conflict_done = bool(clean(row.get("字段事实写回建议", "")) or three_way_done)
    return {
        "pdf_done": pdf_done,
        "hubei_done": hubei_done,
        "school_done": school_done,
        "conflict_done": conflict_done,
        "double_done": (not requires_double_review) or double_done,
        "three_way_done": three_way_done,
        "field_confirm_done": field_confirm_done,
    }


def missing_flags(local_row: dict[str, str], public_row: dict[str, str]) -> dict[str, bool]:
    requires_double_review = boolish(public_row.get("是否需要双人复核", ""))
    status = local_status(local_row, requires_double_review)
    flags = {
        "PDF原页记录缺口": not status["pdf_done"],
        "湖北官方记录缺口": not status["hubei_done"],
        "高校辅证记录缺口": not status["school_done"],
        "冲突处理缺口": not status["conflict_done"],
        "双人复核缺口": not status["double_done"],
        "三方一致性缺口": not status["three_way_done"],
        "字段确认缺口": not status["field_confirm_done"],
    }
    flags["写回评审缺口"] = any(flags.values())
    return flags


def gate_status(flags: dict[str, bool]) -> str:
    return "ready_for_private_writeback_review" if not any(flags.values()) else "blocked_missing_required_field_evidence"


def main_gap_bucket(flags: dict[str, bool]) -> str:
    order = [
        ("PDF原页记录缺口", "G0-缺PDF原页记录"),
        ("湖北官方记录缺口", "G1-缺湖北官方记录"),
        ("高校辅证记录缺口", "G2-缺高校辅证记录"),
        ("冲突处理缺口", "G3-冲突未处理"),
        ("双人复核缺口", "G4-双人复核未完成"),
        ("三方一致性缺口", "G5-三方一致性未评估"),
        ("字段确认缺口", "G6-字段确认未完成"),
        ("写回评审缺口", "G7-写回评审未满足"),
    ]
    for field, label in order:
        if flags.get(field):
            return label
    return "G9-可进入私有写回评审"


def gate_level(flags: dict[str, bool]) -> str:
    if flags.get("PDF原页记录缺口") or flags.get("湖北官方记录缺口"):
        return "L0-省招办原件或湖北官方侧未闭环"
    if flags.get("高校辅证记录缺口") or flags.get("冲突处理缺口"):
        return "L1-高校辅证或冲突处理未闭环"
    if flags.get("双人复核缺口") or flags.get("三方一致性缺口"):
        return "L2-复核与一致性未闭环"
    if flags.get("字段确认缺口") or flags.get("写回评审缺口"):
        return "L3-字段确认或写回评审未完成"
    return "L9-可进入私有写回评审"


def dist(rows: list[dict[str, str]], field: str) -> str:
    counts = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counts[key]}" for key in sorted(counts))


def count_true(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if row.get(field) == "true")


def main() -> None:
    overlay_rows = read_csv(OVERLAY_PUBLIC)
    overlay_page_rows = read_csv(OVERLAY_PAGE)
    local_rows = read_csv(LOCAL_OVERLAY) if LOCAL_OVERLAY.exists() else []
    local_by_public = {
        row.get("G0冲突字段复核Overlay公开账本ID", ""): row for row in local_rows
    }
    overlay_page_by_key = {row.get("页码版面键", ""): row for row in overlay_page_rows}

    public_rows: list[dict[str, str]] = []
    for seq, row in enumerate(overlay_rows, start=1):
        public_id = row.get("G0冲突字段复核Overlay公开账本ID", "")
        local_row = local_by_public.get(public_id, {})
        flags = missing_flags(local_row, row)
        missing_count = sum(1 for value in flags.values() if value)
        out = {
            "G0冲突字段准出门禁公开账本ID": stable_id(
                "G0FIELDGATE",
                [SOURCE_PDF_SHA256, public_id, row.get("第一闭环事实范围缺口公开账本ID", "")],
            ),
            "来源G0冲突字段复核Overlay公开账本": source_path(OVERLAY_PUBLIC),
            "来源G0冲突字段复核Overlay页列汇总": source_path(OVERLAY_PAGE),
            "来源G0冲突字段复核Overlay摘要": source_path(OVERLAY_SUMMARY),
            "来源私有G0字段复核Overlay": "g0_conflict_field_review_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段事实",
            "任务粒度": "字段事实×准出门禁",
            "准出门禁序号": str(seq),
            "G0冲突字段复核Overlay公开账本ID": public_id,
            "G0冲突动作包闭环工作台ID": row.get("G0冲突动作包闭环工作台ID", ""),
            "高校源字段回接队列ID": row.get("高校源字段回接队列ID", ""),
            "W0B0执行预填明细公开审计ID": row.get("W0B0执行预填明细公开审计ID", ""),
            "第一闭环事实范围缺口公开账本ID": row.get("第一闭环事实范围缺口公开账本ID", ""),
            "第一闭环字段事实公开账本ID": row.get("第一闭环字段事实公开账本ID", ""),
            "第一闭环字段核验状态ID": row.get("第一闭环字段核验状态ID", ""),
            "稳定基座第一闭环明细任务ID": row.get("稳定基座第一闭环明细任务ID", ""),
            "页码版面键": row.get("页码版面键", ""),
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
            "私有字段复核记录证据编号": row.get("私有字段复核记录证据编号", ""),
            "私有字段复核记录SHA256": row.get("私有字段复核记录SHA256", ""),
            "私有页列CSV证据编号": row.get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": row.get("私有页列CSV_SHA256", ""),
            "必要缺口数": str(missing_count),
            "准出门禁状态": gate_status(flags),
            "主缺口桶": main_gap_bucket(flags),
            "准出阻断等级": gate_level(flags),
            "字段写回评审状态": (
                "ready_for_private_writeback_review"
                if missing_count == 0
                else "blocked_until_required_evidence_closed"
            ),
            "G0字段Overlay状态": row.get("G0字段Overlay状态", ""),
            "下一步字段准出动作": (
                "继续补齐本地未公开复核记录中的PDF原页、湖北官方侧、高校辅证、冲突处理、双人复核、三方一致性和字段确认；全部闭环后才可进入写回评审。"
                if missing_count
                else "进入私有写回评审，仍不得自动进入最终志愿方案。"
            ),
            "公开安全策略": "公开层只保存字段ID、缺口状态、计数和SHA；字段明细、OCR文本、学校专业明细和人工记录留在本地未公开复核材料。",
        }
        add_false_fields(out)
        for field, value in flags.items():
            out[field] = "true" if value else "false"
        if missing_count == 0:
            out["是否允许进入私有写回评审"] = "true"
        public_rows.append(out)

    page_rows: list[dict[str, str]] = []
    by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in public_rows:
        by_page[row.get("页码版面键", "")].append(row)
    for seq, page_key in enumerate(sorted(by_page), start=1):
        rows = by_page[page_key]
        source_page = overlay_page_by_key.get(page_key, {})
        page_row = {
            "G0冲突字段准出门禁页列汇总ID": stable_id("G0FIELDGATEPAGE", [SOURCE_PDF_SHA256, page_key]),
            "来源G0冲突字段准出门禁公开账本": source_path(PUBLIC_OUTPUT),
            "来源G0冲突字段复核Overlay页列汇总": source_path(OVERLAY_PAGE),
            "来源私有G0字段复核Overlay": "g0_conflict_field_review_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段页列",
            "任务粒度": "页列×字段准出门禁",
            "页列汇总序号": str(seq),
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
            "私有页列CSV证据编号": rows[0].get("私有页列CSV证据编号", source_page.get("私有页列CSV证据编号", "")),
            "私有页列CSV_SHA256": rows[0].get("私有页列CSV_SHA256", source_page.get("私有页列CSV_SHA256", "")),
            "字段事实集合SHA256": sha256_values([row.get("第一闭环事实范围缺口公开账本ID", "") for row in rows]),
            "任务集合SHA256": sha256_values([row.get("稳定基座第一闭环明细任务ID", "") for row in rows]),
            "专业行集合SHA256": sha256_values([row.get("专业行ID", "") for row in rows]),
            "页列准出状态": (
                "ready_for_private_writeback_review"
                if all(row.get("是否允许进入私有写回评审") == "true" for row in rows)
                else "blocked_missing_required_field_evidence"
            ),
            "页列下一步字段准出动作": "继续按页列补齐本地未公开复核记录；页列内所有字段闭环前不得写回。",
            "公开安全策略": "公开层只保存页列计数、缺口状态和SHA；字段明细、OCR文本、学校专业明细和人工记录留在本地未公开复核材料。",
        }
        add_false_fields(page_row)
        if page_row["页列准出状态"] == "ready_for_private_writeback_review":
            page_row["是否允许进入私有写回评审"] = "true"
        page_rows.append(page_row)

    write_csv(PUBLIC_OUTPUT, public_rows, FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)

    summary = {
        "status": "issue19_first_closure_g0_conflict_field_resolution_gate_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_overlay_public": source_path(OVERLAY_PUBLIC),
        "source_overlay_public_sha256": sha256_file(OVERLAY_PUBLIC),
        "source_overlay_page": source_path(OVERLAY_PAGE),
        "source_overlay_page_sha256": sha256_file(OVERLAY_PAGE),
        "source_overlay_summary": source_path(OVERLAY_SUMMARY),
        "source_overlay_summary_sha256": sha256_file(OVERLAY_SUMMARY),
        "private_overlay_workbench": "g0_conflict_field_review_overlay_not_public",
        "private_overlay_sha256": sha256_file(LOCAL_OVERLAY),
        "output_table": source_path(PUBLIC_OUTPUT),
        "page_summary_table": source_path(PAGE_OUTPUT),
        "row_count": len(public_rows),
        "page_summary_row_count": len(page_rows),
        "source_overlay_row_count": len(overlay_rows),
        "source_overlay_page_row_count": len(overlay_page_rows),
        "private_overlay_row_count": len(local_rows),
        "unique_fact_scope_count": len({row.get("第一闭环事实范围缺口公开账本ID", "") for row in public_rows}),
        "unique_page_side_count": len(by_page),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID", "") for row in public_rows}),
        "unique_major_row_count": len({row.get("专业行ID", "") for row in public_rows}),
        "field_name_counts": dict(Counter(row.get("字段名", "") for row in public_rows)),
        "gate_status_counts": dict(Counter(row.get("准出门禁状态", "") for row in public_rows)),
        "main_gap_bucket_counts": dict(Counter(row.get("主缺口桶", "") for row in public_rows)),
        "pdf_record_gap_count": count_true(public_rows, "PDF原页记录缺口"),
        "hubei_official_record_gap_count": count_true(public_rows, "湖北官方记录缺口"),
        "school_side_record_gap_count": count_true(public_rows, "高校辅证记录缺口"),
        "conflict_resolution_gap_count": count_true(public_rows, "冲突处理缺口"),
        "double_review_gap_count": count_true(public_rows, "双人复核缺口"),
        "three_way_gap_count": count_true(public_rows, "三方一致性缺口"),
        "field_confirmation_gap_count": count_true(public_rows, "字段确认缺口"),
        "writeback_review_gap_count": count_true(public_rows, "写回评审缺口"),
        "ready_for_private_writeback_review_count": sum(1 for row in public_rows if row.get("是否允许进入私有写回评审") == "true"),
        "field_writeback_allowed_count": sum(1 for row in public_rows if row.get("是否允许写回字段事实") == "true"),
        "recommendation_basis_allowed_count": sum(1 for row in public_rows if row.get("是否允许作为志愿推荐依据") == "true"),
        "school_major_suggestion_allowed_count": sum(1 for row in public_rows if row.get("是否允许生成学校专业建议") == "true"),
        "official_plan_replacement_allowed_count": sum(1 for row in public_rows if row.get("是否允许官网证据替代湖北官方计划") == "true"),
        "next_stage_allowed_count": sum(1 for row in public_rows if row.get("可进入下一阶段") == "true"),
        "final_available_count": sum(1 for row in public_rows if row.get("最终可用") == "true"),
        "public_boundary": "该账本只同步G0冲突字段写回前缺口门禁，不公开字段明细或人工记录，不确认字段事实。",
    }
    write_json(SUMMARY_OUTPUT, summary)

    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [PUBLIC_OUTPUT, PAGE_OUTPUT, SUMMARY_OUTPUT]
    )
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if hits:
        raise SystemExit(f"public output contains forbidden tokens: {hits}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
