#!/usr/bin/env python3
"""Build execution prefill audit for the W0/B0 minimal manual checklist.

The public outputs turn the 87 W0/B0 minimal facts into a review-ready status
layer. Sensitive clues and manual-entry columns stay in private/ and are
represented in public only by evidence ids and SHA256 hashes.
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

MIN_PACKETS = WORKING / "issue19-stable-foundation-first-closure-w0-b0-minimal-manual-packets-public-ledger.csv"
MIN_ITEMS = WORKING / "issue19-stable-foundation-first-closure-w0-b0-minimal-manual-items-public-ledger.csv"
B0_STATUS = WORKING / "issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv"
EVIDENCE_MAP = WORKING / "issue19-stable-foundation-first-closure-public-evidence-map.csv"
NEXT_ACTION = WORKING / "issue19-stable-foundation-first-closure-next-action-matrix.csv"
FIELD_CONFIRM = WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
PDF_OCR_AUDIT = WORKING / "issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv"
MACHINE_AUDIT = WORKING / "issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit.csv"

PRIVATE_FIELD_CONFIRM = (
    PRIVATE_ROOT
    / "review-assets/issue19-stable-foundation-first-closure-field-confirmation/first-closure-field-confirmation-private-workbench.csv"
)
PRIVATE_PDF_OCR = (
    PRIVATE_ROOT
    / "review-assets/issue19-stable-foundation-first-closure-pdf-ocr-candidates/first-closure-pdf-ocr-candidates-private.csv"
)
PRIVATE_MACHINE = (
    PRIVATE_ROOT
    / "review-assets/issue19-stable-foundation-first-closure-machine-coordinate-candidates/first-closure-machine-coordinate-candidates-private.csv"
)

PRIVATE_OUTPUT_DIR = PRIVATE_ROOT / "review-assets/issue19-w0-b0-minimal-execution-prefill"
PRIVATE_PAGE_DIR = PRIVATE_OUTPUT_DIR / "page-sides"
PRIVATE_MASTER = PRIVATE_OUTPUT_DIR / "w0-b0-minimal-private-prefill.csv"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "w0-b0-minimal-private-index.csv"

PUBLIC_PACKET_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-w0-b0-execution-prefill-packets-public-audit.csv"
PUBLIC_ITEM_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-w0-b0-execution-prefill-items-public-audit.csv"
SUMMARY_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-w0-b0-execution-prefill-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_w0_b0_execution_prefill_audit"
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

PUBLIC_PACKET_FIELDS = [
    "W0B0执行预填包公开审计ID",
    "来源W0B0最小人工复核包",
    "来源W0B0最小人工复核明细",
    "来源B0冲突页列核验状态",
    "来源第一闭环公开证据地图",
    "来源W0B0执行预填明细公开审计",
    "来源W0B0私有预填材料",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行预填包序号",
    "W0B0最小人工复核包ID",
    "B0冲突页列核验状态ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "B0冲突优先级判定",
    "最小人工复核事实数",
    "执行预填明细数",
    "专业组边界事实数",
    "明确冲突字段事实数",
    "专业名归属事实数",
    "专业计划数字段事实数",
    "学费字段事实数",
    "再选科目字段事实数",
    "任务回连事实数",
    "字段确认回连事实数",
    "PDFOCR提示事实数",
    "机器坐标提示事实数",
    "高校辅证线索事实数",
    "PDFOCR与高校冲突事实数",
    "需人工看图事实数",
    "需双人复核事实数",
    "私有页图存在",
    "私有OCR文本存在",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页图_SHA256",
    "私有OCR文本_SHA256",
    "事实集合SHA256",
    "任务ID集合SHA256",
    "专业行ID集合SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "下一步",
    "公开安全策略",
]

PUBLIC_ITEM_FIELDS = [
    "W0B0执行预填明细公开审计ID",
    "来源W0B0最小人工复核明细",
    "来源第一闭环下一步动作矩阵",
    "来源第一闭环字段确认公开账本",
    "来源第一闭环PDFOCR候选公开审计",
    "来源第一闭环机器坐标候选公开审计",
    "来源W0B0私有预填材料",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行预填明细序号",
    "W0B0执行预填包公开审计ID",
    "W0B0最小人工复核包ID",
    "W0B0最小人工复核明细ID",
    "第一闭环事实核验包明细ID",
    "第一闭环事实范围缺口公开账本ID",
    "第一闭环字段事实公开账本ID",
    "稳定基座第一闭环明细任务ID",
    "来源页码",
    "版面列",
    "页码版面键",
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
    "第一闭环下一步动作ID",
    "第一闭环字段确认公开账本ID",
    "第一闭环PDFOCR候选公开审计ID",
    "第一闭环机器坐标候选公开审计ID",
    "PDFOCR提示状态",
    "PDFOCR审阅桶",
    "PDFOCR与高校辅证关系桶",
    "机器坐标提示状态",
    "机器坐标审阅桶",
    "机器坐标关系桶",
    "候选提示综合桶",
    "高校辅证线索状态",
    "湖北官方侧状态",
    "是否有PDFOCR提示",
    "是否有机器坐标提示",
    "是否有高校辅证线索",
    "是否存在PDFOCR与高校冲突",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "私有预填记录状态",
    "私有预填记录证据编号",
    "私有预填记录SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "最小执行动作",
    "公开安全策略",
]

PRIVATE_FIELDS = [
    "W0B0私有预填记录ID",
    "W0B0执行预填明细公开审计ID",
    "W0B0最小人工复核包ID",
    "W0B0最小人工复核明细ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "事实域",
    "事实类型",
    "字段名",
    "最小复核类型",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称",
    "院校专业组代码",
    "专业代号",
    "专业名称短摘",
    "稳定基座第一闭环明细任务ID",
    "第一闭环字段确认公开账本ID",
    "PDFOCR提示状态",
    "机器坐标提示状态",
    "PDFOCR与高校辅证关系桶",
    "PDFOCR计划数候选值",
    "PDFOCR学费候选值",
    "PDFOCR选科候选值",
    "机器坐标候选字段值",
    "机器坐标候选值集合",
    "高校辅证计划数候选值",
    "高校辅证学费候选值",
    "高校辅证选科候选值",
    "OCR行文本",
    "私有页图相对路径",
    "私有OCR文本相对路径",
    "机器坐标证据行号集合",
    "机器坐标证据x集合",
    "机器坐标证据y集合",
    "机器坐标证据置信度集合",
    "PDF原页专业组边界记录",
    "PDF原页专业代号读数",
    "PDF原页专业名称读数",
    "PDF原页字段人工读数",
    "湖北官方专业代号",
    "湖北官方专业名称",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "PDF核页复核人A",
    "PDF核页复核人B",
    "湖北官方核验人",
    "高校辅证核验人",
    "双人一致性结论",
    "三方一致性结论",
    "字段事实写回建议",
    "人工复核备注",
]

PRIVATE_INDEX_FIELDS = [
    "页码版面键",
    "来源页码",
    "版面列",
    "私有页列CSV相对路径",
    "私有页列CSV_SHA256",
    "私有页图相对路径",
    "私有页图_SHA256",
    "私有OCR文本相对路径",
    "私有OCR文本_SHA256",
    "私有预填记录数",
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
    "OCR行文本",
    "候选值",
    "PDFOCR计划数候选值",
    "PDFOCR学费候选值",
    "PDFOCR选科候选值",
    "机器坐标候选字段值",
    "高校辅证计划数候选值",
    "高校辅证学费候选值",
    "高校辅证选科候选值",
    "PDF原页人工读数",
    "PDF原页字段人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "人工复核备注",
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def private_rel(path: Path) -> str:
    return path.relative_to(PRIVATE_ROOT).as_posix()


def stable_id(prefix: str, parts: list[str]) -> str:
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def packet_public_id(packet_id: str, page_key: str) -> str:
    return stable_id("W0B0EXEPKT", [packet_id, page_key])


def sha256_values(values: list[str]) -> str:
    clean = sorted({str(value or "").strip() for value in values if str(value or "").strip()})
    return hashlib.sha256("|".join(clean).encode("utf-8")).hexdigest() if clean else ""


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_sha(row: dict[str, str], fields: list[str]) -> str:
    text = "\n".join(f"{field}={row.get(field, '')}" for field in fields)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def to_int(value: str | int | None) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def add_false_fields(row: dict[str, str]) -> None:
    for field in FALSE_FIELDS:
        row[field] = "false"


def page_image_path(page: str) -> Path:
    normalized = str(page or "").strip().zfill(3)
    return PRIVATE_ROOT / f"ocr-runs/issue19-full-120dpi/rendered-pages/page-{normalized}.png"


def page_text_path(page: str) -> Path:
    normalized = str(page or "").strip().zfill(3)
    return PRIVATE_ROOT / f"ocr-runs/issue19-full-120dpi/text/{normalized}_page-{normalized}.txt"


def boolish(value: str) -> bool:
    return str(value or "").strip().lower() == "true"


def first_nonempty(*values: str) -> str:
    for value in values:
        if str(value or "").strip():
            return str(value).strip()
    return ""


def field_value(row: dict[str, str], field_name: str, prefix: str) -> str:
    mapping = {
        "专业计划数": f"{prefix}计划数候选值",
        "学费": f"{prefix}学费候选值",
        "再选科目": f"{prefix}选科候选值",
    }
    return row.get(mapping.get(field_name, ""), "")


def minimal_action(item: dict[str, str], field_confirm: dict[str, str], page_b0: dict[str, str]) -> str:
    if item.get("事实域") == "专业组边界":
        return "先核专业组标题、起止、跨页延续和左右栏边界，再处理同页字段事实。"
    if item.get("事实域") == "专业名归属":
        return "先核专业行归属、专业组内位置和上下文，再对字段候选做三方闭环。"
    if field_confirm.get("人工核验动作"):
        return field_confirm.get("人工核验动作", "")
    return page_b0.get("建议下一步动作", "") or "双人回看 PDF 原页，并等待湖北官方侧核验。"


def build_private_row(
    item: dict[str, str],
    item_public_id: str,
    field_public: dict[str, str],
    pdf_private: dict[str, str],
    machine_private: dict[str, str],
) -> dict[str, str]:
    page = item.get("来源页码", "")
    image_path = page_image_path(page)
    text_path = page_text_path(page)
    field_name = item.get("字段名", "")
    private_id = stable_id(
        "W0B0PRIV",
        [item.get("W0B0最小人工复核明细ID", ""), item.get("稳定基座第一闭环明细任务ID", "")],
    )
    row = {
        "W0B0私有预填记录ID": private_id,
        "W0B0执行预填明细公开审计ID": item_public_id,
        "W0B0最小人工复核包ID": item.get("W0B0最小人工复核包ID", ""),
        "W0B0最小人工复核明细ID": item.get("W0B0最小人工复核明细ID", ""),
        "页码版面键": item.get("页码版面键", ""),
        "来源页码": page,
        "版面列": item.get("版面列", ""),
        "事实域": item.get("事实域", ""),
        "事实类型": item.get("事实类型", ""),
        "字段名": field_name,
        "最小复核类型": item.get("最小复核类型", ""),
        "专业行ID": item.get("专业行ID", ""),
        "专业组出现ID": item.get("专业组出现ID", ""),
        "院校代码": item.get("院校代码", ""),
        "院校名称": pdf_private.get("院校名称OCR", ""),
        "院校专业组代码": pdf_private.get("院校专业组代码OCR规范化", ""),
        "专业代号": pdf_private.get("专业代号OCR", ""),
        "专业名称短摘": pdf_private.get("专业名称及备注短摘", ""),
        "稳定基座第一闭环明细任务ID": item.get("稳定基座第一闭环明细任务ID", ""),
        "第一闭环字段确认公开账本ID": field_public.get("第一闭环字段确认公开账本ID", ""),
        "PDFOCR提示状态": field_public.get("PDFOCR提示记录状态", ""),
        "机器坐标提示状态": field_public.get("机器坐标提示记录状态", ""),
        "PDFOCR与高校辅证关系桶": field_public.get("PDFOCR与高校辅证关系桶", ""),
        "PDFOCR计划数候选值": field_public.get("PDFOCR计划数候选值", ""),
        "PDFOCR学费候选值": field_public.get("PDFOCR学费候选值", ""),
        "PDFOCR选科候选值": field_public.get("PDFOCR选科候选值", ""),
        "机器坐标候选字段值": machine_private.get("机器坐标候选字段值", ""),
        "机器坐标候选值集合": machine_private.get("机器坐标候选值集合", ""),
        "高校辅证计划数候选值": field_public.get("高校辅证计划数候选值", ""),
        "高校辅证学费候选值": field_public.get("高校辅证学费候选值", ""),
        "高校辅证选科候选值": field_public.get("高校辅证选科候选值", ""),
        "OCR行文本": field_public.get("OCR行文本", "") or pdf_private.get("OCR行文本", ""),
        "私有页图相对路径": private_rel(image_path) if image_path.exists() else "",
        "私有OCR文本相对路径": private_rel(text_path) if text_path.exists() else "",
        "机器坐标证据行号集合": field_public.get("机器坐标证据行号集合", "") or machine_private.get("候选证据行号集合", ""),
        "机器坐标证据x集合": field_public.get("机器坐标证据x集合", "") or machine_private.get("候选证据x集合", ""),
        "机器坐标证据y集合": field_public.get("机器坐标证据y集合", "") or machine_private.get("候选证据y集合", ""),
        "机器坐标证据置信度集合": field_public.get("机器坐标证据置信度集合", "") or machine_private.get("候选证据置信度集合", ""),
        "PDF原页专业组边界记录": "",
        "PDF原页专业代号读数": "",
        "PDF原页专业名称读数": "",
        "PDF原页字段人工读数": "",
        "湖北官方专业代号": "",
        "湖北官方专业名称": "",
        "湖北官方字段值": "",
        "高校官网或招生章程字段值": field_value(field_public, field_name, "高校辅证"),
        "字段确认值": "",
        "PDF核页复核人A": "",
        "PDF核页复核人B": "",
        "湖北官方核验人": "",
        "高校辅证核验人": "",
        "双人一致性结论": "",
        "三方一致性结论": "",
        "字段事实写回建议": "",
        "人工复核备注": "",
    }
    return row


def main() -> None:
    min_packets = read_csv(MIN_PACKETS)
    min_items = read_csv(MIN_ITEMS)
    b0_rows = read_csv(B0_STATUS)
    evidence_rows = read_csv(EVIDENCE_MAP)
    next_rows = read_csv(NEXT_ACTION)
    field_rows = read_csv(FIELD_CONFIRM)
    pdf_rows = read_csv(PDF_OCR_AUDIT)
    machine_rows = read_csv(MACHINE_AUDIT)
    private_field_rows = read_csv(PRIVATE_FIELD_CONFIRM)
    private_pdf_rows = read_csv(PRIVATE_PDF_OCR)
    private_machine_rows = read_csv(PRIVATE_MACHINE)

    b0_by_key = {row.get("页码版面键", ""): row for row in b0_rows}
    evidence_by_key = {row.get("页码版面键", ""): row for row in evidence_rows}
    packet_by_id = {row.get("W0B0最小人工复核包ID", ""): row for row in min_packets}
    next_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in next_rows}
    field_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in field_rows}
    pdf_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in pdf_rows}
    machine_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in machine_rows}
    private_field_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in private_field_rows}
    private_pdf_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in private_pdf_rows}
    private_machine_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in private_machine_rows}

    private_rows: list[dict[str, str]] = []
    public_item_rows: list[dict[str, str]] = []
    for seq, item in enumerate(min_items, start=1):
        task_id = item.get("稳定基座第一闭环明细任务ID", "")
        page_key = item.get("页码版面键", "")
        b0 = b0_by_key.get(page_key, {})
        evidence = evidence_by_key.get(page_key, {})
        next_row = next_by_task.get(task_id, {})
        field_public = dict(private_field_by_task.get(task_id, field_by_task.get(task_id, {})))
        pdf_public = pdf_by_task.get(task_id, {})
        machine_public = machine_by_task.get(task_id, {})
        private_pdf = private_pdf_by_task.get(task_id, {})
        private_machine = private_machine_by_task.get(task_id, {})
        public_id = stable_id("W0B0EXEITEM", [item.get("W0B0最小人工复核明细ID", ""), task_id])
        public_packet_id = packet_public_id(item.get("W0B0最小人工复核包ID", ""), page_key)
        private_row = build_private_row(item, public_id, field_public, private_pdf, private_machine)
        private_rows.append(private_row)
        private_row_digest = row_sha(private_row, PRIVATE_FIELDS)
        row = {
            "W0B0执行预填明细公开审计ID": public_id,
            "来源W0B0最小人工复核明细": source_path(MIN_ITEMS),
            "来源第一闭环下一步动作矩阵": source_path(NEXT_ACTION),
            "来源第一闭环字段确认公开账本": source_path(FIELD_CONFIRM),
            "来源第一闭环PDFOCR候选公开审计": source_path(PDF_OCR_AUDIT),
            "来源第一闭环机器坐标候选公开审计": source_path(MACHINE_AUDIT),
            "来源W0B0私有预填材料": "w0_b0_minimal_private_prefill_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE + "_items",
            "主表粒度": "W0-B0最小人工复核事实",
            "任务粒度": "最小事实×执行预填状态",
            "执行预填明细序号": str(seq),
            "W0B0执行预填包公开审计ID": public_packet_id,
            "W0B0最小人工复核包ID": item.get("W0B0最小人工复核包ID", ""),
            "W0B0最小人工复核明细ID": item.get("W0B0最小人工复核明细ID", ""),
            "第一闭环事实核验包明细ID": item.get("第一闭环事实核验包明细ID", ""),
            "第一闭环事实范围缺口公开账本ID": item.get("第一闭环事实范围缺口公开账本ID", ""),
            "第一闭环字段事实公开账本ID": item.get("第一闭环字段事实公开账本ID", ""),
            "稳定基座第一闭环明细任务ID": task_id,
            "来源页码": item.get("来源页码", ""),
            "版面列": item.get("版面列", ""),
            "页码版面键": page_key,
            "专业行ID": item.get("专业行ID", ""),
            "专业组出现ID": item.get("专业组出现ID", ""),
            "院校代码": item.get("院校代码", ""),
            "事实域": item.get("事实域", ""),
            "事实类型": item.get("事实类型", ""),
            "事实粒度": item.get("事实粒度", ""),
            "字段名": item.get("字段名", ""),
            "最小复核类型": item.get("最小复核类型", ""),
            "复核优先级": item.get("复核优先级", ""),
            "页列主阻断": item.get("页列主阻断", ""),
            "核验动作层级": item.get("核验动作层级", ""),
            "第一闭环下一步动作ID": next_row.get("第一闭环下一步动作ID", ""),
            "第一闭环字段确认公开账本ID": field_by_task.get(task_id, {}).get("第一闭环字段确认公开账本ID", ""),
            "第一闭环PDFOCR候选公开审计ID": pdf_public.get("第一闭环PDFOCR候选公开审计ID", ""),
            "第一闭环机器坐标候选公开审计ID": machine_public.get("第一闭环机器坐标候选公开审计ID", ""),
            "PDFOCR提示状态": first_nonempty(field_by_task.get(task_id, {}).get("PDFOCR提示记录状态", ""), pdf_public.get("PDFOCR候选记录状态", ""), "page_side_review" if item.get("事实域") == "专业组边界" else ""),
            "PDFOCR审阅桶": first_nonempty(field_by_task.get(task_id, {}).get("PDFOCR提示审阅桶", ""), pdf_public.get("PDFOCR候选审阅桶", "")),
            "PDFOCR与高校辅证关系桶": first_nonempty(field_by_task.get(task_id, {}).get("PDFOCR与高校辅证关系桶", ""), pdf_public.get("PDFOCR与高校辅证关系桶", "")),
            "机器坐标提示状态": first_nonempty(field_by_task.get(task_id, {}).get("机器坐标提示记录状态", ""), machine_public.get("机器坐标候选记录状态", "")),
            "机器坐标审阅桶": first_nonempty(field_by_task.get(task_id, {}).get("机器坐标提示审阅桶", ""), machine_public.get("机器坐标候选审阅桶", "")),
            "机器坐标关系桶": first_nonempty(field_by_task.get(task_id, {}).get("机器坐标提示关系桶", ""), machine_public.get("机器坐标候选关系桶", "")),
            "候选提示综合桶": field_by_task.get(task_id, {}).get("候选提示综合桶", ""),
            "高校辅证线索状态": "has_school_side_evidence" if boolish(field_by_task.get(task_id, {}).get("是否有高校辅证线索", "")) else ("page_side_has_school_side_evidence" if to_int(evidence.get("高校辅证线索任务数")) else "no_school_side_evidence"),
            "湖北官方侧状态": next_row.get("湖北官方侧状态", "") or "pending_hubei_official_plan_review",
            "是否有PDFOCR提示": field_by_task.get(task_id, {}).get("是否有PDFOCR提示", "true" if to_int(evidence.get("PDFOCR提示任务数")) else "false"),
            "是否有机器坐标提示": field_by_task.get(task_id, {}).get("是否有机器坐标提示", "true" if to_int(evidence.get("机器坐标提示任务数")) else "false"),
            "是否有高校辅证线索": field_by_task.get(task_id, {}).get("是否有高校辅证线索", "true" if to_int(evidence.get("高校辅证线索任务数")) else "false"),
            "是否存在PDFOCR与高校冲突": field_by_task.get(task_id, {}).get("是否存在PDFOCR与高校冲突", "true" if item.get("事实域") == "字段事实" else "false"),
            "是否需要人工直接看图": item.get("是否需要人工看图", ""),
            "是否需要双人复核": item.get("是否需要双人复核", ""),
            "私有预填记录状态": "private_prefill_seeded_pending_manual_review",
            "私有预填记录证据编号": f"W0B0-PRIV-{private_row['W0B0私有预填记录ID']}",
            "私有预填记录SHA256": private_row_digest,
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "三方字段一致性状态": "pending_three_way_closure",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "最小执行动作": minimal_action(item, field_by_task.get(task_id, {}), b0),
            "公开安全策略": "公开层只保存状态、ID、计数和私有记录SHA；学校专业明细、字段读数、OCR正文和人工备注只在private目录。",
        }
        add_false_fields(row)
        public_item_rows.append(row)

    write_csv(PRIVATE_MASTER, private_rows, PRIVATE_FIELDS)

    private_index_rows: list[dict[str, str]] = []
    private_rows_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in private_rows:
        private_rows_by_page[row.get("页码版面键", "")].append(row)
    for page_key, rows in sorted(private_rows_by_page.items()):
        page = rows[0].get("来源页码", "")
        side = rows[0].get("版面列", "")
        page_csv = PRIVATE_PAGE_DIR / f"{page_key}.csv"
        write_csv(page_csv, rows, PRIVATE_FIELDS)
        image_path = page_image_path(page)
        text_path = page_text_path(page)
        private_index_rows.append({
            "页码版面键": page_key,
            "来源页码": page,
            "版面列": side,
            "私有页列CSV相对路径": private_rel(page_csv),
            "私有页列CSV_SHA256": sha256_file(page_csv),
            "私有页图相对路径": private_rel(image_path) if image_path.exists() else "",
            "私有页图_SHA256": sha256_file(image_path),
            "私有OCR文本相对路径": private_rel(text_path) if text_path.exists() else "",
            "私有OCR文本_SHA256": sha256_file(text_path),
            "私有预填记录数": str(len(rows)),
        })
    write_csv(PRIVATE_INDEX, private_index_rows, PRIVATE_INDEX_FIELDS)

    private_index_by_key = {row["页码版面键"]: row for row in private_index_rows}
    public_items_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in public_item_rows:
        public_items_by_page[row.get("页码版面键", "")].append(row)

    public_packet_rows: list[dict[str, str]] = []
    for packet in min_packets:
        page_key = packet.get("页码版面键", "")
        rows = public_items_by_page.get(page_key, [])
        b0 = b0_by_key.get(page_key, {})
        priv = private_index_by_key.get(page_key, {})
        packet_id = packet_public_id(packet.get("W0B0最小人工复核包ID", ""), page_key)
        row = {
            "W0B0执行预填包公开审计ID": packet_id,
            "来源W0B0最小人工复核包": source_path(MIN_PACKETS),
            "来源W0B0最小人工复核明细": source_path(MIN_ITEMS),
            "来源B0冲突页列核验状态": source_path(B0_STATUS),
            "来源第一闭环公开证据地图": source_path(EVIDENCE_MAP),
            "来源W0B0执行预填明细公开审计": source_path(PUBLIC_ITEM_OUTPUT),
            "来源W0B0私有预填材料": "w0_b0_minimal_private_prefill_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE + "_packets",
            "主表粒度": "W0-B0页列最小执行预填包",
            "任务粒度": "页列×最小事实×私有预填",
            "执行预填包序号": packet.get("最小人工复核包序号", ""),
            "W0B0最小人工复核包ID": packet.get("W0B0最小人工复核包ID", ""),
            "B0冲突页列核验状态ID": b0.get("B0冲突页列核验状态ID", ""),
            "来源页码": packet.get("来源页码", ""),
            "版面列": packet.get("版面列", ""),
            "页码版面键": page_key,
            "B0冲突优先级判定": packet.get("B0冲突优先级判定", ""),
            "最小人工复核事实数": packet.get("最小人工复核事实数", ""),
            "执行预填明细数": str(len(rows)),
            "专业组边界事实数": str(sum(item.get("事实域") == "专业组边界" for item in rows)),
            "明确冲突字段事实数": str(sum(item.get("事实域") == "字段事实" for item in rows)),
            "专业名归属事实数": str(sum(item.get("事实域") == "专业名归属" for item in rows)),
            "专业计划数字段事实数": str(sum(item.get("事实类型") == "字段事实-专业计划数" for item in rows)),
            "学费字段事实数": str(sum(item.get("事实类型") == "字段事实-学费" for item in rows)),
            "再选科目字段事实数": str(sum(item.get("事实类型") == "字段事实-再选科目" for item in rows)),
            "任务回连事实数": str(sum(bool(item.get("稳定基座第一闭环明细任务ID", "")) for item in rows)),
            "字段确认回连事实数": str(sum(bool(item.get("第一闭环字段确认公开账本ID", "")) for item in rows)),
            "PDFOCR提示事实数": str(sum(boolish(item.get("是否有PDFOCR提示", "")) for item in rows)),
            "机器坐标提示事实数": str(sum(boolish(item.get("是否有机器坐标提示", "")) for item in rows)),
            "高校辅证线索事实数": str(sum(boolish(item.get("是否有高校辅证线索", "")) for item in rows)),
            "PDFOCR与高校冲突事实数": str(sum(boolish(item.get("是否存在PDFOCR与高校冲突", "")) for item in rows)),
            "需人工看图事实数": str(sum(item.get("是否需要人工直接看图") == "true" for item in rows)),
            "需双人复核事实数": str(sum(item.get("是否需要双人复核") == "true" for item in rows)),
            "私有页图存在": "true" if priv.get("私有页图_SHA256", "") else "false",
            "私有OCR文本存在": "true" if priv.get("私有OCR文本_SHA256", "") else "false",
            "私有页列CSV证据编号": f"W0B0-PRIVATE-PAGE-{page_key}",
            "私有页列CSV_SHA256": priv.get("私有页列CSV_SHA256", ""),
            "私有页图_SHA256": priv.get("私有页图_SHA256", ""),
            "私有OCR文本_SHA256": priv.get("私有OCR文本_SHA256", ""),
            "事实集合SHA256": sha256_values([item.get("W0B0最小人工复核明细ID", "") for item in rows]),
            "任务ID集合SHA256": sha256_values([item.get("稳定基座第一闭环明细任务ID", "") for item in rows]),
            "专业行ID集合SHA256": sha256_values([item.get("专业行ID", "") for item in rows]),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "下一步": "按页列打开私有预填CSV和PDF原页，先核专业组边界，再核冲突字段和专业名归属；核完仍需湖北官方侧闭环。",
            "公开安全策略": "公开层只保存页列计数、状态、ID和私有材料SHA；不公开学校专业明细、字段读数、OCR正文或人工备注。",
        }
        add_false_fields(row)
        public_packet_rows.append(row)

    write_csv(PUBLIC_ITEM_OUTPUT, public_item_rows, PUBLIC_ITEM_FIELDS)
    write_csv(PUBLIC_PACKET_OUTPUT, public_packet_rows, PUBLIC_PACKET_FIELDS)

    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [PUBLIC_PACKET_OUTPUT, PUBLIC_ITEM_OUTPUT]
    )
    forbidden_hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if forbidden_hits:
        raise SystemExit(f"公开输出包含禁止内容：{forbidden_hits[:8]}")

    fact_type_counts = Counter(row.get("事实类型", "") for row in public_item_rows)
    review_type_counts = Counter(row.get("最小复核类型", "") for row in public_item_rows)
    summary = {
        "status": "issue19_stable_foundation_first_closure_w0_b0_execution_prefill_audit_ready_not_final",
        "generated_by": "build_issue19_first_closure_w0_b0_execution_prefill_audit.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_minimal_packets": source_path(MIN_PACKETS),
        "source_minimal_items": source_path(MIN_ITEMS),
        "packet_output_table": source_path(PUBLIC_PACKET_OUTPUT),
        "item_output_table": source_path(PUBLIC_ITEM_OUTPUT),
        "private_prefill_workbench": "w0_b0_minimal_private_prefill_not_public",
        "packet_row_count": len(public_packet_rows),
        "item_row_count": len(public_item_rows),
        "private_prefill_row_count": len(private_rows),
        "private_page_side_csv_count": len(private_index_rows),
        "private_master_csv_sha256": sha256_file(PRIVATE_MASTER),
        "private_index_csv_sha256": sha256_file(PRIVATE_INDEX),
        "unique_page_side_count": len({row.get("页码版面键", "") for row in public_item_rows}),
        "task_backed_item_count": sum(bool(row.get("稳定基座第一闭环明细任务ID", "")) for row in public_item_rows),
        "field_confirmation_join_count": sum(bool(row.get("第一闭环字段确认公开账本ID", "")) for row in public_item_rows),
        "pdfocr_hint_item_count": sum(boolish(row.get("是否有PDFOCR提示", "")) for row in public_item_rows),
        "machine_hint_item_count": sum(boolish(row.get("是否有机器坐标提示", "")) for row in public_item_rows),
        "school_side_hint_item_count": sum(boolish(row.get("是否有高校辅证线索", "")) for row in public_item_rows),
        "pdfocr_school_conflict_item_count": sum(boolish(row.get("是否存在PDFOCR与高校冲突", "")) for row in public_item_rows),
        "manual_image_required_item_count": sum(row.get("是否需要人工直接看图") == "true" for row in public_item_rows),
        "double_review_required_item_count": sum(row.get("是否需要双人复核") == "true" for row in public_item_rows),
        "private_page_image_found_count": sum(row.get("私有页图存在") == "true" for row in public_packet_rows),
        "private_page_text_found_count": sum(row.get("私有OCR文本存在") == "true" for row in public_packet_rows),
        "review_type_counts": dict(review_type_counts),
        "fact_type_counts": dict(fact_type_counts),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该公开审计只把W0/B0最小事实接到私有预填和证据状态，不公开读数，不确认字段事实，不生成志愿排序。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
