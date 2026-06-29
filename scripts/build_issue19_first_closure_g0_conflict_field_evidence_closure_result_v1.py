#!/usr/bin/env python3
"""Build G0 conflict-field evidence closure result ledger.

This layer sits after the G0 conflict-field evidence execution packets and
before any private writeback review. It reads the private G0 page-side CSVs to
publish only status buckets, counts, evidence labels, and SHA256 digests. It
never publishes field readings, OCR text, school/profession names, reviewer
notes, or local paths.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"
PRIVATE_ROOT = ROOT / "private"

EXEC_PACKETS = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-execution-packets-v1-public-ledger.csv"
)
EXEC_ITEMS = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-execution-items-v1-public-ledger.csv"
)
EXEC_SUMMARY = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-execution-packets-v1-summary.json"
)
GATE_PUBLIC = WORKING / "issue19-first-closure-g0-conflict-field-resolution-gate-v1-public-ledger.csv"
GATE_PAGE = WORKING / "issue19-first-closure-g0-conflict-field-resolution-gate-v1-page-summary.csv"
OVERLAY_PUBLIC = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-public-ledger.csv"
OVERLAY_PAGE = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-page-summary.csv"
FIELD_BACKLINK = WORKING / "issue19-w0-b0-school-source-field-backlink-queue-public-ledger.csv"
FIELD_BACKLINK_PAGE = WORKING / "issue19-w0-b0-school-source-field-backlink-page-summary.csv"

PRIVATE_G0_PAGE_DIR = (
    PRIVATE_ROOT / "review-assets/issue19-g0-conflict-field-review-overlay-v1/page-sides"
)
PRIVATE_G0_INDEX = (
    PRIVATE_ROOT
    / "review-assets/issue19-g0-conflict-field-review-overlay-v1/g0-conflict-field-review-private-index.csv"
)

OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-closure-result-v1-public-ledger.csv"
)
PAGE_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-closure-result-v1-page-summary.csv"
)
SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-closure-result-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_evidence_closure_result_v1"

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

RESULT_FIELDS = [
    "G0冲突字段补证闭环结果公开账本ID",
    "来源G0冲突字段补证执行项公开账本",
    "来源G0冲突字段补证执行包公开账本",
    "来源G0冲突字段准出门禁公开账本",
    "来源G0冲突字段准出门禁页列汇总",
    "来源G0冲突字段复核Overlay公开账本",
    "来源G0冲突字段复核Overlay页列汇总",
    "来源W0B0高校源字段回接队列",
    "来源W0B0高校源字段回接页列汇总",
    "来源私有G0字段复核页列CSV",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "是否允许进入私有写回评审",
    "闭环结果序号",
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
    "准出门禁状态",
    "主缺口桶",
    "PDF原页核验结果状态",
    "OCR提示核验状态",
    "高校官网辅证核验状态",
    "湖北官方侧核验状态",
    "冲突处理状态",
    "双人复核结果状态",
    "三方闭环状态",
    "字段确认状态",
    "字段写回评审状态",
    "补证闭环状态",
    "私有写回评审准入状态",
    "当前主阻断桶",
    "必要证据缺口数",
    "私有字段复核记录证据编号",
    "私有字段复核记录SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有核页HTML证据编号",
    "私有核页HTML_SHA256",
    "当前私有页列CSV记录SHA256",
    "下一步闭环动作",
    "公开安全策略",
]

PAGE_FIELDS = [
    "G0冲突字段补证闭环结果页列汇总ID",
    "来源G0冲突字段补证闭环结果公开账本",
    "来源G0冲突字段补证执行包公开账本",
    "来源G0冲突字段准出门禁页列汇总",
    "来源G0冲突字段复核Overlay页列汇总",
    "来源W0B0高校源字段回接页列汇总",
    "来源私有G0字段复核页列CSV",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "可进入私有写回评审字段数",
    "页列汇总序号",
    "页码版面键",
    "来源页码",
    "版面列",
    "G0冲突字段补证执行包公开账本ID",
    "字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "补证执行优先级",
    "补证执行泳道",
    "PDF原页记录缺口字段数",
    "湖北官方记录缺口字段数",
    "高校辅证记录缺口字段数",
    "冲突处理缺口字段数",
    "双人复核缺口字段数",
    "三方一致性缺口字段数",
    "字段确认缺口字段数",
    "写回评审缺口字段数",
    "PDF原页核验结果状态分布",
    "OCR提示核验状态分布",
    "高校官网辅证核验状态分布",
    "湖北官方侧核验状态分布",
    "冲突处理状态分布",
    "双人复核结果状态分布",
    "三方闭环状态分布",
    "字段确认状态分布",
    "字段写回评审状态分布",
    "补证闭环状态分布",
    "当前主阻断桶分布",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有核页HTML证据编号",
    "私有核页HTML_SHA256",
    "当前私有页列CSV_SHA256",
    "字段事实集合SHA256",
    "补证执行项集合SHA256",
    "闭环结果集合SHA256",
    "页列补证闭环状态",
    "页列下一步闭环动作",
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
    "字段确认值",
    "PDF原页字段人工读数",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "高校官网字段值",
    "高校辅证人工核验记录值",
    "OCR正文",
    "OCR文本",
    "OCR原文",
    "OCR行文本",
    "截图路径",
    "人工复核备注",
    "人工备注正文",
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


def row_sha(row: dict[str, str], fields: list[str]) -> str:
    return hashlib.sha256(
        json.dumps({field: clean(row.get(field, "")) for field in fields}, ensure_ascii=False, sort_keys=True).encode(
            "utf-8"
        )
    ).hexdigest()


def add_false_fields(row: dict[str, str]) -> None:
    for field in FALSE_FIELDS:
        row[field] = "false"


def truthy(value: object) -> bool:
    return clean(value).lower() == "true"


def filled(row: dict[str, str], field: str) -> bool:
    return bool(clean(row.get(field, "")))


def dist(rows: list[dict[str, str]], field: str) -> str:
    counter = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter))


def count_true(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if truthy(row.get(field, "")))


def same_value(left: str, right: str) -> bool:
    return clean(left).replace("，", ",") == clean(right).replace("，", ",")


def private_ocr_value(row: dict[str, str], field_name: str) -> str:
    mapping = {
        "专业计划数": "PDFOCR计划数候选值",
        "学费": "PDFOCR学费候选值",
        "再选科目": "PDFOCR选科候选值",
    }
    return clean(row.get(mapping.get(field_name, ""), ""))


def private_school_seed(row: dict[str, str], field_name: str) -> str:
    mapping = {
        "专业计划数": "高校辅证计划数候选值",
        "学费": "高校辅证学费候选值",
        "再选科目": "高校辅证选科候选值",
    }
    return clean(row.get(mapping.get(field_name, ""), ""))


def pdf_status(private_row: dict[str, str]) -> str:
    return "pdf_page_record_present_sha_only" if filled(private_row, "PDF原页字段人工读数") else "pending_pdf_page_review"


def ocr_status(private_row: dict[str, str], exec_row: dict[str, str]) -> str:
    value = private_ocr_value(private_row, clean(exec_row.get("字段名", "")))
    if not truthy(exec_row.get("是否有PDFOCR提示", "")) and not value:
        return "no_ocr_hint"
    if not filled(private_row, "PDF原页字段人工读数"):
        return "ocr_hint_present_not_fact"
    if value and same_value(value, private_row.get("PDF原页字段人工读数", "")):
        return "ocr_hint_matched_pdf"
    return "ocr_hint_conflicts_pdf"


def school_status(private_row: dict[str, str], exec_row: dict[str, str]) -> str:
    if filled(private_row, "高校辅证人工核验记录值"):
        if filled(private_row, "PDF原页字段人工读数"):
            return (
                "school_source_supports_pdf"
                if same_value(private_row.get("高校辅证人工核验记录值", ""), private_row.get("PDF原页字段人工读数", ""))
                else "school_source_conflicts_pdf"
            )
        return "school_source_present_sha_only"
    if private_school_seed(private_row, clean(exec_row.get("字段名", ""))) or filled(private_row, "高校官网或招生章程字段值"):
        return "school_source_seed_present_pending_manual_review"
    return "school_source_pending"


def hubei_status(private_row: dict[str, str]) -> str:
    if filled(private_row, "湖北官方字段值"):
        if filled(private_row, "PDF原页字段人工读数"):
            return (
                "hubei_official_supports_pdf"
                if same_value(private_row.get("湖北官方字段值", ""), private_row.get("PDF原页字段人工读数", ""))
                else "hubei_official_conflicts_pdf"
            )
        return "hubei_official_present_sha_only"
    return "pending_hubei_official_plan_review"


def double_status(private_row: dict[str, str], exec_row: dict[str, str]) -> str:
    if not truthy(exec_row.get("双人复核缺口", "")):
        return "not_required"
    if filled(private_row, "PDF核页复核人A") and filled(private_row, "PDF核页复核人B"):
        if filled(private_row, "双人一致性结论"):
            return "double_review_completed_sha_only"
        return "double_review_reviewers_present_pending_conclusion"
    return "pending_double_review"


def conflict_status(private_row: dict[str, str]) -> str:
    if filled(private_row, "三方一致性结论") and filled(private_row, "字段确认值"):
        return "conflict_resolved_same_direction"
    if filled(private_row, "三方一致性结论") or filled(private_row, "双人一致性结论"):
        return "conflict_resolution_record_present_sha_only"
    return "pending_conflict_resolution"


def three_way_status(private_row: dict[str, str], exec_row: dict[str, str], double_state: str) -> str:
    if not filled(private_row, "PDF原页字段人工读数"):
        return "blocked_missing_pdf"
    if not filled(private_row, "湖北官方字段值"):
        return "blocked_missing_hubei"
    if truthy(exec_row.get("高校辅证记录缺口", "")) and not filled(private_row, "高校辅证人工核验记录值"):
        return "blocked_missing_school"
    if double_state == "pending_double_review":
        return "blocked_double_review"
    if not filled(private_row, "三方一致性结论"):
        return "pending_three_way_closure"
    return "closed_pdf_hubei_school_consistent"


def closure_status(
    private_row: dict[str, str],
    exec_row: dict[str, str],
    pdf_state: str,
    school_state: str,
    hubei_state: str,
    conflict_state: str,
    double_state: str,
    three_way_state: str,
) -> tuple[str, str, str, str, int]:
    gaps = []
    if pdf_state != "pdf_page_record_present_sha_only":
        gaps.append("G0-缺PDF原页记录")
    if hubei_state == "pending_hubei_official_plan_review":
        gaps.append("G1-缺湖北官方记录")
    if school_state in {"school_source_pending", "school_source_seed_present_pending_manual_review"}:
        gaps.append("G2-缺高校辅证人工核验")
    if conflict_state == "pending_conflict_resolution":
        gaps.append("G3-冲突未处理")
    if double_state == "pending_double_review":
        gaps.append("G4-双人复核未完成")
    if three_way_state != "closed_pdf_hubei_school_consistent":
        gaps.append("G5-三方一致性未闭环")
    if not filled(private_row, "字段确认值"):
        gaps.append("G6-字段确认未填写")
    if not filled(private_row, "字段事实写回建议"):
        gaps.append("G7-写回评审建议未填写")

    ready = not gaps
    private_review = "ready_for_private_writeback_review_sha_only" if ready else "blocked"
    writeback_review = "ready_for_private_writeback_review_sha_only" if ready else "blocked_until_required_evidence_closed"
    closure = "closure_ready_for_private_writeback_review" if ready else "closure_blocked_missing_required_evidence"
    main_gap = "G9-可进入私有写回评审" if ready else gaps[0]
    return private_review, writeback_review, closure, main_gap, len(gaps)


def load_private_rows() -> tuple[dict[str, dict[str, str]], dict[str, str], list[str]]:
    private_by_overlay_id: dict[str, dict[str, str]] = {}
    page_sha_by_key: dict[str, str] = {}
    fields: list[str] = []
    for path in sorted(PRIVATE_G0_PAGE_DIR.glob("*.csv")):
        page_rows = read_csv(path)
        page_sha_by_key[path.stem] = sha256_file(path)
        if page_rows and not fields:
            fields = list(page_rows[0].keys())
        for row in page_rows:
            overlay_id = clean(row.get("G0冲突字段复核Overlay公开账本ID", ""))
            if not overlay_id:
                raise RuntimeError(f"private G0 page CSV row missing overlay id: {path}")
            if overlay_id in private_by_overlay_id:
                raise RuntimeError(f"duplicate private G0 overlay id: {overlay_id}")
            private_by_overlay_id[overlay_id] = row
    return private_by_overlay_id, page_sha_by_key, fields


def main() -> None:
    exec_packets = read_csv(EXEC_PACKETS)
    exec_items = read_csv(EXEC_ITEMS)
    gate_rows = read_csv(GATE_PUBLIC)
    gate_pages = read_csv(GATE_PAGE)
    overlay_rows = read_csv(OVERLAY_PUBLIC)
    overlay_pages = read_csv(OVERLAY_PAGE)
    backlink_rows = read_csv(FIELD_BACKLINK)
    backlink_pages = read_csv(FIELD_BACKLINK_PAGE)
    private_by_overlay_id, page_sha_by_key, private_fields = load_private_rows()

    exec_packet_by_id = {
        row.get("G0冲突字段补证执行包公开账本ID", ""): row
        for row in exec_packets
    }
    gate_by_id = {row.get("G0冲突字段准出门禁公开账本ID", ""): row for row in gate_rows}
    overlay_by_id = {
        row.get("G0冲突字段复核Overlay公开账本ID", ""): row
        for row in overlay_rows
    }
    backlink_by_id = {
        row.get("高校源字段回接队列ID", ""): row
        for row in backlink_rows
    }
    gate_page_by_key = {row.get("页码版面键", ""): row for row in gate_pages}
    overlay_page_by_key = {row.get("页码版面键", ""): row for row in overlay_pages}
    backlink_page_by_key = {row.get("页码版面键", ""): row for row in backlink_pages}

    result_rows: list[dict[str, str]] = []
    for seq, exec_row in enumerate(exec_items, start=1):
        overlay_id = clean(exec_row.get("G0冲突字段复核Overlay公开账本ID", ""))
        private_row = private_by_overlay_id.get(overlay_id)
        if private_row is None:
            raise RuntimeError(f"missing private G0 overlay row for {overlay_id}")

        packet = exec_packet_by_id.get(exec_row.get("G0冲突字段补证执行包公开账本ID", ""), {})
        gate = gate_by_id.get(exec_row.get("G0冲突字段准出门禁公开账本ID", ""), {})
        overlay = overlay_by_id.get(overlay_id, {})
        backlink = backlink_by_id.get(exec_row.get("高校源字段回接队列ID", ""), {})
        page_key = exec_row.get("页码版面键", "")
        pdf_state = pdf_status(private_row)
        ocr_state = ocr_status(private_row, exec_row)
        school_state = school_status(private_row, exec_row)
        hubei_state = hubei_status(private_row)
        double_state = double_status(private_row, exec_row)
        conflict_state = conflict_status(private_row)
        three_way_state = three_way_status(private_row, exec_row, double_state)
        private_review, writeback_review, closure, main_gap, missing_count = closure_status(
            private_row,
            exec_row,
            pdf_state,
            school_state,
            hubei_state,
            conflict_state,
            double_state,
            three_way_state,
        )
        row = {
            "G0冲突字段补证闭环结果公开账本ID": stable_id(
                "G0FIELDCLOSURE",
                [SOURCE_PDF_SHA256, exec_row.get("G0冲突字段补证执行项公开账本ID", "")],
            ),
            "来源G0冲突字段补证执行项公开账本": source_path(EXEC_ITEMS),
            "来源G0冲突字段补证执行包公开账本": source_path(EXEC_PACKETS),
            "来源G0冲突字段准出门禁公开账本": source_path(GATE_PUBLIC),
            "来源G0冲突字段准出门禁页列汇总": source_path(GATE_PAGE),
            "来源G0冲突字段复核Overlay公开账本": source_path(OVERLAY_PUBLIC),
            "来源G0冲突字段复核Overlay页列汇总": source_path(OVERLAY_PAGE),
            "来源W0B0高校源字段回接队列": source_path(FIELD_BACKLINK),
            "来源W0B0高校源字段回接页列汇总": source_path(FIELD_BACKLINK_PAGE),
            "来源私有G0字段复核页列CSV": "g0_conflict_field_private_page_csv_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段补证闭环结果",
            "任务粒度": "字段事实×补证结果状态",
            "是否允许进入私有写回评审": "true" if private_review == "ready_for_private_writeback_review_sha_only" else "false",
            "闭环结果序号": str(seq),
            "G0冲突字段补证执行项公开账本ID": exec_row.get("G0冲突字段补证执行项公开账本ID", ""),
            "G0冲突字段补证执行包公开账本ID": exec_row.get("G0冲突字段补证执行包公开账本ID", ""),
            "G0冲突字段准出门禁公开账本ID": exec_row.get("G0冲突字段准出门禁公开账本ID", ""),
            "G0冲突字段复核Overlay公开账本ID": overlay_id,
            "G0冲突动作包闭环工作台ID": exec_row.get("G0冲突动作包闭环工作台ID", ""),
            "高校源字段回接队列ID": exec_row.get("高校源字段回接队列ID", ""),
            "W0B0执行预填明细公开审计ID": exec_row.get("W0B0执行预填明细公开审计ID", ""),
            "第一闭环事实范围缺口公开账本ID": exec_row.get("第一闭环事实范围缺口公开账本ID", ""),
            "第一闭环字段事实公开账本ID": exec_row.get("第一闭环字段事实公开账本ID", ""),
            "第一闭环字段核验状态ID": exec_row.get("第一闭环字段核验状态ID", ""),
            "稳定基座第一闭环明细任务ID": exec_row.get("稳定基座第一闭环明细任务ID", ""),
            "页码版面键": page_key,
            "来源页码": exec_row.get("来源页码", ""),
            "版面列": exec_row.get("版面列", ""),
            "专业行ID": exec_row.get("专业行ID", ""),
            "专业组出现ID": exec_row.get("专业组出现ID", ""),
            "院校代码": exec_row.get("院校代码", ""),
            "事实域": exec_row.get("事实域", ""),
            "事实类型": exec_row.get("事实类型", ""),
            "字段名": exec_row.get("字段名", ""),
            "补证执行优先级": exec_row.get("补证执行优先级", ""),
            "补证执行泳道": exec_row.get("补证执行泳道", ""),
            "回接泳道": exec_row.get("回接泳道", ""),
            "回接批次": exec_row.get("回接批次", ""),
            "字段事实状态": exec_row.get("字段事实状态", ""),
            "字段核验优先级": exec_row.get("字段核验优先级", ""),
            "PDFOCR与高校辅证关系桶": exec_row.get("PDFOCR与高校辅证关系桶", ""),
            "是否有PDFOCR提示": exec_row.get("是否有PDFOCR提示", ""),
            "是否有高校辅证线索": exec_row.get("是否有高校辅证线索", ""),
            "是否存在PDFOCR与高校冲突": exec_row.get("是否存在PDFOCR与高校冲突", ""),
            "是否需要人工直接看图": exec_row.get("是否需要人工直接看图", ""),
            "是否需要双人复核": exec_row.get("是否需要双人复核", ""),
            "PDF原页记录缺口": exec_row.get("PDF原页记录缺口", ""),
            "湖北官方记录缺口": exec_row.get("湖北官方记录缺口", ""),
            "高校辅证记录缺口": exec_row.get("高校辅证记录缺口", ""),
            "冲突处理缺口": exec_row.get("冲突处理缺口", ""),
            "双人复核缺口": exec_row.get("双人复核缺口", ""),
            "三方一致性缺口": exec_row.get("三方一致性缺口", ""),
            "字段确认缺口": exec_row.get("字段确认缺口", ""),
            "写回评审缺口": exec_row.get("写回评审缺口", ""),
            "准出门禁状态": exec_row.get("准出门禁状态", ""),
            "主缺口桶": exec_row.get("主缺口桶", ""),
            "PDF原页核验结果状态": pdf_state,
            "OCR提示核验状态": ocr_state,
            "高校官网辅证核验状态": school_state,
            "湖北官方侧核验状态": hubei_state,
            "冲突处理状态": conflict_state,
            "双人复核结果状态": double_state,
            "三方闭环状态": three_way_state,
            "字段确认状态": private_review,
            "字段写回评审状态": writeback_review,
            "补证闭环状态": closure,
            "私有写回评审准入状态": private_review,
            "当前主阻断桶": main_gap,
            "必要证据缺口数": str(missing_count),
            "私有字段复核记录证据编号": exec_row.get("私有字段复核记录证据编号", ""),
            "私有字段复核记录SHA256": exec_row.get("私有字段复核记录SHA256", ""),
            "私有页列CSV证据编号": exec_row.get("私有G0页列CSV证据编号", ""),
            "私有页列CSV_SHA256": exec_row.get("私有G0页列CSV_SHA256", ""),
            "私有核页HTML证据编号": exec_row.get("私有核页HTML证据编号", ""),
            "私有核页HTML_SHA256": exec_row.get("私有核页HTML_SHA256", ""),
            "当前私有页列CSV记录SHA256": row_sha(private_row, private_fields),
            "下一步闭环动作": "继续在本地未公开页列CSV补齐PDF原页、湖北官方侧、高校辅证、冲突处理、双人复核和三方一致性记录；仅当全部闭环后才可进入私有写回评审。",
            "公开安全策略": "公开层只保存ID、状态、计数、证据编号和SHA；具体核验内容、识别内容、明细文本、人工内容和本地位置不公开。",
        }
        add_false_fields(row)
        # Keep cross-source links exercised without publishing their sensitive content.
        if not (gate and overlay and backlink and packet):
            missing = [
                name
                for name, source_row in [
                    ("gate", gate),
                    ("overlay", overlay),
                    ("backlink", backlink),
                    ("packet", packet),
                ]
                if not source_row
            ]
            raise RuntimeError(f"missing G0 closure upstream rows for {overlay_id}: {missing}")
        result_rows.append(row)

    rows_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in result_rows:
        rows_by_page[row.get("页码版面键", "")].append(row)

    page_rows: list[dict[str, str]] = []
    for seq, page_key in enumerate(sorted(rows_by_page), start=1):
        rows = rows_by_page[page_key]
        packet = next(
            row
            for row in exec_packets
            if row.get("页码版面键", "") == page_key
        )
        gate_page = gate_page_by_key.get(page_key, {})
        overlay_page = overlay_page_by_key.get(page_key, {})
        backlink_page = backlink_page_by_key.get(page_key, {})
        ready_count = sum(1 for row in rows if row.get("是否允许进入私有写回评审") == "true")
        page_row = {
            "G0冲突字段补证闭环结果页列汇总ID": stable_id("G0FIELDCLOSUREPAGE", [SOURCE_PDF_SHA256, page_key]),
            "来源G0冲突字段补证闭环结果公开账本": source_path(OUTPUT),
            "来源G0冲突字段补证执行包公开账本": source_path(EXEC_PACKETS),
            "来源G0冲突字段准出门禁页列汇总": source_path(GATE_PAGE),
            "来源G0冲突字段复核Overlay页列汇总": source_path(OVERLAY_PAGE),
            "来源W0B0高校源字段回接页列汇总": source_path(FIELD_BACKLINK_PAGE),
            "来源私有G0字段复核页列CSV": "g0_conflict_field_private_page_csv_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段补证闭环结果页列汇总",
            "任务粒度": "页列×补证结果状态",
            "可进入私有写回评审字段数": str(ready_count),
            "页列汇总序号": str(seq),
            "页码版面键": page_key,
            "来源页码": rows[0].get("来源页码", ""),
            "版面列": rows[0].get("版面列", ""),
            "G0冲突字段补证执行包公开账本ID": packet.get("G0冲突字段补证执行包公开账本ID", ""),
            "字段事实数": str(len(rows)),
            "涉及任务数": str(len({row.get("稳定基座第一闭环明细任务ID", "") for row in rows if row.get("稳定基座第一闭环明细任务ID", "")})),
            "涉及专业行数": str(len({row.get("专业行ID", "") for row in rows if row.get("专业行ID", "")})),
            "涉及院校代码数": str(len({row.get("院校代码", "") for row in rows if row.get("院校代码", "")})),
            "字段名分布": dist(rows, "字段名"),
            "补证执行优先级": packet.get("补证执行优先级", ""),
            "补证执行泳道": packet.get("补证执行泳道", ""),
            "PDF原页记录缺口字段数": str(count_true(rows, "PDF原页记录缺口")),
            "湖北官方记录缺口字段数": str(count_true(rows, "湖北官方记录缺口")),
            "高校辅证记录缺口字段数": str(count_true(rows, "高校辅证记录缺口")),
            "冲突处理缺口字段数": str(count_true(rows, "冲突处理缺口")),
            "双人复核缺口字段数": str(count_true(rows, "双人复核缺口")),
            "三方一致性缺口字段数": str(count_true(rows, "三方一致性缺口")),
            "字段确认缺口字段数": str(count_true(rows, "字段确认缺口")),
            "写回评审缺口字段数": str(count_true(rows, "写回评审缺口")),
            "PDF原页核验结果状态分布": dist(rows, "PDF原页核验结果状态"),
            "OCR提示核验状态分布": dist(rows, "OCR提示核验状态"),
            "高校官网辅证核验状态分布": dist(rows, "高校官网辅证核验状态"),
            "湖北官方侧核验状态分布": dist(rows, "湖北官方侧核验状态"),
            "冲突处理状态分布": dist(rows, "冲突处理状态"),
            "双人复核结果状态分布": dist(rows, "双人复核结果状态"),
            "三方闭环状态分布": dist(rows, "三方闭环状态"),
            "字段确认状态分布": dist(rows, "字段确认状态"),
            "字段写回评审状态分布": dist(rows, "字段写回评审状态"),
            "补证闭环状态分布": dist(rows, "补证闭环状态"),
            "当前主阻断桶分布": dist(rows, "当前主阻断桶"),
            "私有页列CSV证据编号": packet.get("私有G0页列CSV证据编号", ""),
            "私有页列CSV_SHA256": packet.get("私有G0页列CSV_SHA256", ""),
            "私有核页HTML证据编号": packet.get("私有核页HTML证据编号", ""),
            "私有核页HTML_SHA256": packet.get("私有核页HTML_SHA256", ""),
            "当前私有页列CSV_SHA256": page_sha_by_key.get(page_key, ""),
            "字段事实集合SHA256": sha256_values([row.get("第一闭环事实范围缺口公开账本ID", "") for row in rows]),
            "补证执行项集合SHA256": sha256_values([row.get("G0冲突字段补证执行项公开账本ID", "") for row in rows]),
            "闭环结果集合SHA256": sha256_values([row.get("G0冲突字段补证闭环结果公开账本ID", "") for row in rows]),
            "页列补证闭环状态": "closure_ready_for_private_writeback_review" if ready_count == len(rows) else "closure_blocked_missing_required_evidence",
            "页列下一步闭环动作": "按页列继续补 PDF 原页、湖北官方侧、高校辅证人工核验、冲突处理、双人复核和三方一致性记录；未闭环前不得写回。",
            "公开安全策略": "公开层只保存页列状态、计数、证据编号和SHA；不公开具体核验内容、识别内容、明细文本、人工内容或本地位置。",
        }
        add_false_fields(page_row)
        # Keep page-level joins strict.
        if not (gate_page and overlay_page and backlink_page):
            raise RuntimeError(f"missing G0 closure page upstream rows for {page_key}")
        page_rows.append(page_row)

    write_csv(OUTPUT, result_rows, RESULT_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)

    summary = {
        "status": "issue19_first_closure_g0_conflict_field_evidence_closure_result_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_exec_items": source_path(EXEC_ITEMS),
        "source_exec_items_sha256": sha256_file(EXEC_ITEMS),
        "source_exec_packets": source_path(EXEC_PACKETS),
        "source_exec_packets_sha256": sha256_file(EXEC_PACKETS),
        "source_exec_summary": source_path(EXEC_SUMMARY),
        "source_exec_summary_sha256": sha256_file(EXEC_SUMMARY),
        "source_gate_public": source_path(GATE_PUBLIC),
        "source_gate_public_sha256": sha256_file(GATE_PUBLIC),
        "source_gate_page": source_path(GATE_PAGE),
        "source_gate_page_sha256": sha256_file(GATE_PAGE),
        "source_overlay_public": source_path(OVERLAY_PUBLIC),
        "source_overlay_public_sha256": sha256_file(OVERLAY_PUBLIC),
        "source_overlay_page": source_path(OVERLAY_PAGE),
        "source_overlay_page_sha256": sha256_file(OVERLAY_PAGE),
        "source_field_backlink": source_path(FIELD_BACKLINK),
        "source_field_backlink_sha256": sha256_file(FIELD_BACKLINK),
        "source_field_backlink_page": source_path(FIELD_BACKLINK_PAGE),
        "source_field_backlink_page_sha256": sha256_file(FIELD_BACKLINK_PAGE),
        "private_g0_index": "g0_conflict_field_private_index_not_public",
        "private_g0_index_sha256": sha256_file(PRIVATE_G0_INDEX),
        "private_g0_page_csv_count": len(page_sha_by_key),
        "private_g0_field_record_count": len(private_by_overlay_id),
        "output_table": source_path(OUTPUT),
        "page_summary_table": source_path(PAGE_OUTPUT),
        "row_count": len(result_rows),
        "page_summary_row_count": len(page_rows),
        "source_exec_item_row_count": len(exec_items),
        "source_exec_packet_row_count": len(exec_packets),
        "source_gate_row_count": len(gate_rows),
        "source_gate_page_row_count": len(gate_pages),
        "source_overlay_row_count": len(overlay_rows),
        "source_overlay_page_row_count": len(overlay_pages),
        "source_field_backlink_row_count": len(backlink_rows),
        "source_field_backlink_page_row_count": len(backlink_pages),
        "unique_fact_scope_count": len({row.get("第一闭环事实范围缺口公开账本ID", "") for row in result_rows}),
        "unique_page_side_count": len(rows_by_page),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID", "") for row in result_rows}),
        "unique_major_row_count": len({row.get("专业行ID", "") for row in result_rows}),
        "field_name_counts": dict(Counter(row.get("字段名", "") for row in result_rows)),
        "pdf_status_counts": dict(Counter(row.get("PDF原页核验结果状态", "") for row in result_rows)),
        "ocr_status_counts": dict(Counter(row.get("OCR提示核验状态", "") for row in result_rows)),
        "school_status_counts": dict(Counter(row.get("高校官网辅证核验状态", "") for row in result_rows)),
        "hubei_status_counts": dict(Counter(row.get("湖北官方侧核验状态", "") for row in result_rows)),
        "conflict_status_counts": dict(Counter(row.get("冲突处理状态", "") for row in result_rows)),
        "double_review_status_counts": dict(Counter(row.get("双人复核结果状态", "") for row in result_rows)),
        "three_way_status_counts": dict(Counter(row.get("三方闭环状态", "") for row in result_rows)),
        "field_confirmation_status_counts": dict(Counter(row.get("字段确认状态", "") for row in result_rows)),
        "writeback_review_status_counts": dict(Counter(row.get("字段写回评审状态", "") for row in result_rows)),
        "closure_status_counts": dict(Counter(row.get("补证闭环状态", "") for row in result_rows)),
        "main_blocker_counts": dict(Counter(row.get("当前主阻断桶", "") for row in result_rows)),
        "pdf_record_gap_count": count_true(result_rows, "PDF原页记录缺口"),
        "hubei_official_record_gap_count": count_true(result_rows, "湖北官方记录缺口"),
        "school_side_record_gap_count": count_true(result_rows, "高校辅证记录缺口"),
        "conflict_resolution_gap_count": count_true(result_rows, "冲突处理缺口"),
        "double_review_gap_count": count_true(result_rows, "双人复核缺口"),
        "three_way_gap_count": count_true(result_rows, "三方一致性缺口"),
        "field_confirmation_gap_count": count_true(result_rows, "字段确认缺口"),
        "writeback_review_gap_count": count_true(result_rows, "写回评审缺口"),
        "ready_for_private_writeback_review_count": sum(
            1 for row in result_rows if row.get("是否允许进入私有写回评审") == "true"
        ),
        "field_writeback_allowed_count": sum(1 for row in result_rows if row.get("是否允许写回字段事实") == "true"),
        "recommendation_basis_allowed_count": sum(1 for row in result_rows if row.get("是否允许作为志愿推荐依据") == "true"),
        "school_major_suggestion_allowed_count": sum(1 for row in result_rows if row.get("是否允许生成学校专业建议") == "true"),
        "official_plan_replacement_allowed_count": sum(1 for row in result_rows if row.get("是否允许官网证据替代湖北官方计划") == "true"),
        "next_stage_allowed_count": sum(1 for row in result_rows if row.get("可进入下一阶段") == "true"),
        "final_available_count": sum(1 for row in result_rows if row.get("最终可用") == "true"),
        "public_boundary": "该账本只公开G0补证结果状态和SHA，不公开具体核验内容、识别内容、明细文本或人工内容；进入私有写回评审也不等于允许写回字段事实。",
    }
    write_json(SUMMARY_OUTPUT, summary)

    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [OUTPUT, PAGE_OUTPUT, SUMMARY_OUTPUT]
    )
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if hits:
        raise SystemExit(f"public output contains forbidden tokens: {hits}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
