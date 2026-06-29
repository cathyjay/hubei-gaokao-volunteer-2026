#!/usr/bin/env python3
"""Build the G0 conflict-field private review overlay and public progress ledger.

The public outputs expose only ids, status, counts, and SHA256 digests. Field
clues, OCR text, manual readings, reviewer names, and notes stay under
private/.
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

G0_PACKAGE = WORKING / "issue19-first-closure-g0-conflict-package-closure-workbench-v1-public-ledger.csv"
PREFILL_ITEMS = WORKING / "issue19-stable-foundation-first-closure-w0-b0-execution-prefill-items-public-audit.csv"
FIELD_BACKLINK = WORKING / "issue19-w0-b0-school-source-field-backlink-queue-public-ledger.csv"
FIELD_BACKLINK_PAGE = WORKING / "issue19-w0-b0-school-source-field-backlink-page-summary.csv"
PRIVATE_PREFILL = (
    PRIVATE_ROOT / "review-assets/issue19-w0-b0-minimal-execution-prefill/w0-b0-minimal-private-prefill.csv"
)

PRIVATE_OUTPUT_DIR = PRIVATE_ROOT / "review-assets/issue19-g0-conflict-field-review-overlay-v1"
PRIVATE_PAGE_DIR = PRIVATE_OUTPUT_DIR / "page-sides"
PRIVATE_MASTER = PRIVATE_OUTPUT_DIR / "g0-conflict-field-review-private-overlay.csv"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "g0-conflict-field-review-private-index.csv"

PUBLIC_OUTPUT = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-page-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-g0-conflict-field-review-overlay-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_review_overlay_v1"

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
    "G0冲突字段复核Overlay公开账本ID",
    "来源G0冲突动作包闭环工作台",
    "来源W0B0执行预填明细公开审计",
    "来源W0B0高校源字段回接队列",
    "来源私有字段复核Overlay",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "G0字段复核序号",
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
    "事实粒度",
    "字段名",
    "回接泳道",
    "回接批次",
    "字段事实状态",
    "字段核验优先级",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "字段事实缺口类型",
    "核验动作层级",
    "候选提示综合桶",
    "PDFOCR与高校辅证关系桶",
    "OCR提示状态",
    "高校辅证证据状态",
    "冲突状态",
    "三方闭环状态",
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
    "PDF原页字段记录填写状态",
    "湖北官方记录填写状态",
    "高校辅证人工核验状态",
    "双人复核状态",
    "三方一致性状态",
    "字段写回评审状态",
    "G0字段Overlay状态",
    "下一步字段闭环动作",
    "公开安全策略",
]

PAGE_FIELDS = [
    "G0冲突字段复核页列汇总ID",
    "来源G0冲突字段复核Overlay公开账本",
    "来源G0冲突动作包闭环工作台",
    "来源W0B0高校源字段回接页列汇总",
    "来源私有字段复核Overlay",
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
    "G0冲突动作包闭环工作台ID",
    "高校源字段回接页列汇总ID",
    "字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "回接泳道分布",
    "字段事实状态分布",
    "PDFOCR与高校辅证关系桶分布",
    "需要双人复核字段数",
    "需要人工看图字段数",
    "结构化接入候选字段数",
    "PDF原页字段记录已填数",
    "湖北官方记录已填数",
    "高校辅证人工核验已填数",
    "双人复核已完成数",
    "三方一致性已评估数",
    "可进入私有写回评审字段数",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "字段事实集合SHA256",
    "任务集合SHA256",
    "专业行集合SHA256",
    "页列Overlay状态",
    "页列下一步字段闭环动作",
    "公开安全策略",
]

PRIVATE_FIELDS = [
    "G0私有字段复核记录ID",
    "G0冲突字段复核Overlay公开账本ID",
    "G0冲突动作包闭环工作台ID",
    "高校源字段回接队列ID",
    "W0B0执行预填明细公开审计ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "事实类型",
    "字段名",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称",
    "院校专业组代码",
    "专业代号",
    "专业名称短摘",
    "稳定基座第一闭环明细任务ID",
    "第一闭环事实范围缺口公开账本ID",
    "第一闭环字段事实公开账本ID",
    "PDFOCR提示状态",
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
    "PDF原页专业代号读数",
    "PDF原页专业名称读数",
    "PDF原页字段人工读数",
    "湖北官方专业代号",
    "湖北官方专业名称",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "高校辅证人工核验记录值",
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
    "私有字段复核记录数",
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
    "院校专业组代码",
    "字段读数",
    "人工读数",
    "字段候选值",
    "PDFOCR计划数候选值",
    "PDFOCR学费候选值",
    "PDFOCR选科候选值",
    "机器坐标候选字段值",
    "高校辅证计划数候选值",
    "高校辅证学费候选值",
    "高校辅证选科候选值",
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
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def private_rel(path: Path) -> str:
    return path.relative_to(PRIVATE_ROOT).as_posix()


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
    text = "\n".join(f"{field}={row.get(field, '')}" for field in fields)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def boolish(value: str) -> bool:
    return clean(value).lower() == "true"


def add_false_fields(row: dict[str, str]) -> None:
    for field in FALSE_FIELDS:
        row[field] = "false"


def first_nonempty(*values: str) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def private_status(row: dict[str, str]) -> dict[str, str]:
    pdf_done = bool(clean(row.get("PDF原页字段人工读数", "")))
    hubei_done = bool(clean(row.get("湖北官方字段值", "")))
    school_done = bool(clean(row.get("高校辅证人工核验记录值", "")) or clean(row.get("高校辅证核验人", "")))
    double_done = bool(clean(row.get("PDF核页复核人A", "")) and clean(row.get("PDF核页复核人B", "")) and clean(row.get("双人一致性结论", "")))
    three_way_done = bool(clean(row.get("三方一致性结论", "")))
    ready = pdf_done and hubei_done and school_done and double_done and three_way_done
    any_manual = any(
        clean(row.get(field, ""))
        for field in [
            "PDF原页字段人工读数",
            "湖北官方字段值",
            "高校辅证人工核验记录值",
            "PDF核页复核人A",
            "PDF核页复核人B",
            "双人一致性结论",
            "三方一致性结论",
            "字段事实写回建议",
        ]
    )
    return {
        "PDF原页字段记录填写状态": "R1-PDF原页字段记录已填" if pdf_done else "R0-PDF原页字段记录未填",
        "湖北官方记录填写状态": "R1-湖北官方记录已填" if hubei_done else "R0-湖北官方记录未填",
        "高校辅证人工核验状态": "R1-高校辅证人工核验已填" if school_done else "R0-高校辅证人工核验未填",
        "双人复核状态": "R1-双人复核已完成" if double_done else "R0-双人复核未完成",
        "三方一致性状态": "R1-三方一致性已评估" if three_way_done else "R0-三方一致性未评估",
        "字段写回评审状态": "ready_for_private_writeback_review" if ready else "blocked_until_private_overlay_complete",
        "G0字段Overlay状态": (
            "R2-Overlay已完整填写待写回复查" if ready else
            "R1-Overlay部分填写仍阻断" if any_manual else
            "R0-Overlay已生成未填写"
        ),
    }


def preserve_manual(seed: dict[str, str], old_by_id: dict[str, dict[str, str]]) -> dict[str, str]:
    old = old_by_id.get(seed.get("G0私有字段复核记录ID", ""), {})
    for field in [
        "PDF原页专业代号读数",
        "PDF原页专业名称读数",
        "PDF原页字段人工读数",
        "湖北官方专业代号",
        "湖北官方专业名称",
        "湖北官方字段值",
        "高校辅证人工核验记录值",
        "字段确认值",
        "PDF核页复核人A",
        "PDF核页复核人B",
        "湖北官方核验人",
        "高校辅证核验人",
        "双人一致性结论",
        "三方一致性结论",
        "字段事实写回建议",
        "人工复核备注",
    ]:
        if clean(old.get(field, "")):
            seed[field] = old[field]
    return seed


def dist(rows: list[dict[str, str]], field: str) -> str:
    counts = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counts[key]}" for key in sorted(counts))


def main() -> None:
    g0_rows = read_csv(G0_PACKAGE)
    prefill_rows = read_csv(PREFILL_ITEMS)
    backlink_rows = read_csv(FIELD_BACKLINK)
    backlink_page_rows = read_csv(FIELD_BACKLINK_PAGE)
    private_prefill_rows = read_csv(PRIVATE_PREFILL)
    old_private_rows = read_csv(PRIVATE_MASTER) if PRIVATE_MASTER.exists() else []

    g0_by_page = {row.get("页码版面键", ""): row for row in g0_rows}
    prefill_by_fact = {row.get("第一闭环事实范围缺口公开账本ID", ""): row for row in prefill_rows}
    private_prefill_by_public = {
        row.get("W0B0执行预填明细公开审计ID", ""): row for row in private_prefill_rows
    }
    old_private_by_id = {row.get("G0私有字段复核记录ID", ""): row for row in old_private_rows}
    backlink_page_by_page = {row.get("页码版面键", ""): row for row in backlink_page_rows}

    private_rows: list[dict[str, str]] = []
    public_rows: list[dict[str, str]] = []
    field_rows = [
        row for row in backlink_rows
        if row.get("事实域") == "字段事实"
        and row.get("高校源可作double_check提示") == "true"
        and row.get("是否存在PDFOCR与高校冲突") == "true"
    ]
    for seq, row in enumerate(field_rows, start=1):
        page_key = row.get("页码版面键", "")
        g0 = g0_by_page.get(page_key, {})
        prefill = prefill_by_fact.get(row.get("第一闭环事实范围缺口公开账本ID", ""), {})
        private_prefill = private_prefill_by_public.get(prefill.get("W0B0执行预填明细公开审计ID", ""), {})
        public_id = stable_id(
            "G0FIELDPUB",
            [row.get("高校源字段回接队列ID", ""), row.get("第一闭环事实范围缺口公开账本ID", "")],
        )
        private_id = stable_id("G0FIELDPRIV", [public_id, row.get("稳定基座第一闭环明细任务ID", "")])
        private_row = {
            "G0私有字段复核记录ID": private_id,
            "G0冲突字段复核Overlay公开账本ID": public_id,
            "G0冲突动作包闭环工作台ID": g0.get("G0冲突动作包闭环工作台ID", ""),
            "高校源字段回接队列ID": row.get("高校源字段回接队列ID", ""),
            "W0B0执行预填明细公开审计ID": prefill.get("W0B0执行预填明细公开审计ID", ""),
            "页码版面键": page_key,
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "事实类型": row.get("事实类型", ""),
            "字段名": row.get("字段名", ""),
            "专业行ID": first_nonempty(row.get("专业行ID", ""), prefill.get("专业行ID", "")),
            "专业组出现ID": prefill.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称": private_prefill.get("院校名称", ""),
            "院校专业组代码": private_prefill.get("院校专业组代码", ""),
            "专业代号": private_prefill.get("专业代号", ""),
            "专业名称短摘": private_prefill.get("专业名称短摘", ""),
            "稳定基座第一闭环明细任务ID": row.get("稳定基座第一闭环明细任务ID", ""),
            "第一闭环事实范围缺口公开账本ID": row.get("第一闭环事实范围缺口公开账本ID", ""),
            "第一闭环字段事实公开账本ID": prefill.get("第一闭环字段事实公开账本ID", ""),
            "PDFOCR提示状态": private_prefill.get("PDFOCR提示状态", ""),
            "PDFOCR与高校辅证关系桶": row.get("PDFOCR与高校辅证关系桶", ""),
            "PDFOCR计划数候选值": private_prefill.get("PDFOCR计划数候选值", ""),
            "PDFOCR学费候选值": private_prefill.get("PDFOCR学费候选值", ""),
            "PDFOCR选科候选值": private_prefill.get("PDFOCR选科候选值", ""),
            "机器坐标候选字段值": private_prefill.get("机器坐标候选字段值", ""),
            "机器坐标候选值集合": private_prefill.get("机器坐标候选值集合", ""),
            "高校辅证计划数候选值": private_prefill.get("高校辅证计划数候选值", ""),
            "高校辅证学费候选值": private_prefill.get("高校辅证学费候选值", ""),
            "高校辅证选科候选值": private_prefill.get("高校辅证选科候选值", ""),
            "OCR行文本": private_prefill.get("OCR行文本", ""),
            "私有页图相对路径": private_prefill.get("私有页图相对路径", ""),
            "私有OCR文本相对路径": private_prefill.get("私有OCR文本相对路径", ""),
            "PDF原页专业代号读数": private_prefill.get("PDF原页专业代号读数", ""),
            "PDF原页专业名称读数": private_prefill.get("PDF原页专业名称读数", ""),
            "PDF原页字段人工读数": private_prefill.get("PDF原页字段人工读数", ""),
            "湖北官方专业代号": private_prefill.get("湖北官方专业代号", ""),
            "湖北官方专业名称": private_prefill.get("湖北官方专业名称", ""),
            "湖北官方字段值": private_prefill.get("湖北官方字段值", ""),
            "高校官网或招生章程字段值": private_prefill.get("高校官网或招生章程字段值", ""),
            "高校辅证人工核验记录值": "",
            "字段确认值": private_prefill.get("字段确认值", ""),
            "PDF核页复核人A": private_prefill.get("PDF核页复核人A", ""),
            "PDF核页复核人B": private_prefill.get("PDF核页复核人B", ""),
            "湖北官方核验人": private_prefill.get("湖北官方核验人", ""),
            "高校辅证核验人": private_prefill.get("高校辅证核验人", ""),
            "双人一致性结论": private_prefill.get("双人一致性结论", ""),
            "三方一致性结论": private_prefill.get("三方一致性结论", ""),
            "字段事实写回建议": private_prefill.get("字段事实写回建议", ""),
            "人工复核备注": private_prefill.get("人工复核备注", ""),
        }
        private_row = preserve_manual(private_row, old_private_by_id)
        private_rows.append(private_row)
        statuses = private_status(private_row)
        public_row = {
            "G0冲突字段复核Overlay公开账本ID": public_id,
            "来源G0冲突动作包闭环工作台": source_path(G0_PACKAGE),
            "来源W0B0执行预填明细公开审计": source_path(PREFILL_ITEMS),
            "来源W0B0高校源字段回接队列": source_path(FIELD_BACKLINK),
            "来源私有字段复核Overlay": "g0_conflict_field_review_private_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段事实",
            "任务粒度": "字段事实×私有人工核验Overlay",
            "G0字段复核序号": str(seq),
            "G0冲突动作包闭环工作台ID": g0.get("G0冲突动作包闭环工作台ID", ""),
            "高校源字段回接队列ID": row.get("高校源字段回接队列ID", ""),
            "W0B0执行预填明细公开审计ID": prefill.get("W0B0执行预填明细公开审计ID", ""),
            "第一闭环事实范围缺口公开账本ID": row.get("第一闭环事实范围缺口公开账本ID", ""),
            "第一闭环字段事实公开账本ID": prefill.get("第一闭环字段事实公开账本ID", ""),
            "第一闭环字段核验状态ID": row.get("第一闭环字段核验状态ID", ""),
            "稳定基座第一闭环明细任务ID": row.get("稳定基座第一闭环明细任务ID", ""),
            "页码版面键": page_key,
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "专业行ID": first_nonempty(row.get("专业行ID", ""), prefill.get("专业行ID", "")),
            "专业组出现ID": prefill.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "事实域": row.get("事实域", ""),
            "事实类型": row.get("事实类型", ""),
            "事实粒度": row.get("事实粒度", ""),
            "字段名": row.get("字段名", ""),
            "回接泳道": row.get("回接泳道", ""),
            "回接批次": row.get("回接批次", ""),
            "字段事实状态": row.get("字段事实状态", ""),
            "字段核验优先级": row.get("字段核验优先级", ""),
            "字段事实闭环等级": row.get("字段事实闭环等级", ""),
            "字段事实阻断等级": row.get("字段事实阻断等级", ""),
            "字段事实缺口类型": row.get("字段事实缺口类型", ""),
            "核验动作层级": row.get("核验动作层级", ""),
            "候选提示综合桶": row.get("候选提示综合桶", ""),
            "PDFOCR与高校辅证关系桶": row.get("PDFOCR与高校辅证关系桶", ""),
            "OCR提示状态": row.get("OCR提示状态", ""),
            "高校辅证证据状态": row.get("高校辅证证据状态", ""),
            "冲突状态": row.get("冲突状态", ""),
            "三方闭环状态": row.get("三方闭环状态", ""),
            "是否有PDFOCR提示": row.get("是否有PDFOCR提示", ""),
            "是否有高校辅证线索": row.get("是否有高校辅证线索", ""),
            "是否存在PDFOCR与高校冲突": row.get("是否存在PDFOCR与高校冲突", ""),
            "是否需要人工直接看图": row.get("是否需要人工直接看图", ""),
            "是否需要双人复核": row.get("是否需要双人复核", ""),
            "高校源桥接桶": row.get("高校源桥接桶", ""),
            "结构化接入候选数": row.get("结构化接入候选数", ""),
            "私有字段复核记录证据编号": f"G0FIELD-PRIVATE-{private_id}",
            "私有字段复核记录SHA256": row_sha(private_row, PRIVATE_FIELDS),
            "PDF原页字段记录填写状态": statuses["PDF原页字段记录填写状态"],
            "湖北官方记录填写状态": statuses["湖北官方记录填写状态"],
            "高校辅证人工核验状态": statuses["高校辅证人工核验状态"],
            "双人复核状态": statuses["双人复核状态"],
            "三方一致性状态": statuses["三方一致性状态"],
            "字段写回评审状态": statuses["字段写回评审状态"],
            "G0字段Overlay状态": statuses["G0字段Overlay状态"],
            "下一步字段闭环动作": "打开私有字段Overlay和第19期原页，填PDF原页读数、湖北官方字段值、高校辅证人工核验记录，并完成双人复核；全部闭环前不得写回。",
            "公开安全策略": "公开层只保存字段ID、状态、计数和私有记录SHA；字段线索、OCR文本、学校专业明细、人工记录和备注留在private目录。",
        }
        add_false_fields(public_row)
        public_rows.append(public_row)

    write_csv(PRIVATE_MASTER, private_rows, PRIVATE_FIELDS)

    private_rows_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in private_rows:
        private_rows_by_page[row.get("页码版面键", "")].append(row)
    private_index_rows: list[dict[str, str]] = []
    for page_key, rows in sorted(private_rows_by_page.items()):
        page_csv = PRIVATE_PAGE_DIR / f"{page_key}.csv"
        write_csv(page_csv, rows, PRIVATE_FIELDS)
        private_index_rows.append({
            "页码版面键": page_key,
            "来源页码": rows[0].get("来源页码", ""),
            "版面列": rows[0].get("版面列", ""),
            "私有页列CSV相对路径": private_rel(page_csv),
            "私有页列CSV_SHA256": sha256_file(page_csv),
            "私有字段复核记录数": str(len(rows)),
        })
    write_csv(PRIVATE_INDEX, private_index_rows, PRIVATE_INDEX_FIELDS)
    private_index_by_page = {row.get("页码版面键", ""): row for row in private_index_rows}
    public_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in public_rows:
        public_by_page[row.get("页码版面键", "")].append(row)

    for row in public_rows:
        priv = private_index_by_page.get(row.get("页码版面键", ""), {})
        row["私有页列CSV证据编号"] = f"G0FIELD-PRIVATE-PAGE-{row.get('页码版面键', '')}"
        row["私有页列CSV_SHA256"] = priv.get("私有页列CSV_SHA256", "")

    page_rows: list[dict[str, str]] = []
    for seq, page_key in enumerate(sorted(public_by_page), start=1):
        rows = public_by_page[page_key]
        g0 = g0_by_page.get(page_key, {})
        backlink_page = backlink_page_by_page.get(page_key, {})
        priv = private_index_by_page.get(page_key, {})
        status_counts = Counter(row.get("字段写回评审状态", "") for row in rows)
        page_row = {
            "G0冲突字段复核页列汇总ID": stable_id("G0FIELDPAGE", [page_key]),
            "来源G0冲突字段复核Overlay公开账本": source_path(PUBLIC_OUTPUT),
            "来源G0冲突动作包闭环工作台": source_path(G0_PACKAGE),
            "来源W0B0高校源字段回接页列汇总": source_path(FIELD_BACKLINK_PAGE),
            "来源私有字段复核Overlay": "g0_conflict_field_review_private_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE + "_page_summary",
            "主表粒度": "G0冲突字段页列汇总",
            "任务粒度": "页列×冲突字段Overlay进度",
            "页列汇总序号": str(seq),
            "页码版面键": page_key,
            "来源页码": rows[0].get("来源页码", ""),
            "版面列": rows[0].get("版面列", ""),
            "G0冲突动作包闭环工作台ID": g0.get("G0冲突动作包闭环工作台ID", ""),
            "高校源字段回接页列汇总ID": backlink_page.get("高校源字段回接页列汇总ID", ""),
            "字段事实数": str(len(rows)),
            "涉及任务数": str(len({row.get("稳定基座第一闭环明细任务ID", "") for row in rows if row.get("稳定基座第一闭环明细任务ID", "")})),
            "涉及专业行数": str(len({row.get("专业行ID", "") for row in rows if row.get("专业行ID", "")})),
            "涉及院校代码数": str(len({row.get("院校代码", "") for row in rows if row.get("院校代码", "")})),
            "字段名分布": dist(rows, "字段名"),
            "回接泳道分布": dist(rows, "回接泳道"),
            "字段事实状态分布": dist(rows, "字段事实状态"),
            "PDFOCR与高校辅证关系桶分布": dist(rows, "PDFOCR与高校辅证关系桶"),
            "需要双人复核字段数": str(sum(row.get("是否需要双人复核") == "true" for row in rows)),
            "需要人工看图字段数": str(sum(row.get("是否需要人工直接看图") == "true" for row in rows)),
            "结构化接入候选字段数": str(sum(1 for row in rows if clean(row.get("结构化接入候选数", "")) not in {"", "0"})),
            "PDF原页字段记录已填数": str(sum(row.get("PDF原页字段记录填写状态") == "R1-PDF原页字段记录已填" for row in rows)),
            "湖北官方记录已填数": str(sum(row.get("湖北官方记录填写状态") == "R1-湖北官方记录已填" for row in rows)),
            "高校辅证人工核验已填数": str(sum(row.get("高校辅证人工核验状态") == "R1-高校辅证人工核验已填" for row in rows)),
            "双人复核已完成数": str(sum(row.get("双人复核状态") == "R1-双人复核已完成" for row in rows)),
            "三方一致性已评估数": str(sum(row.get("三方一致性状态") == "R1-三方一致性已评估" for row in rows)),
            "可进入私有写回评审字段数": str(status_counts.get("ready_for_private_writeback_review", 0)),
            "私有页列CSV证据编号": f"G0FIELD-PRIVATE-PAGE-{page_key}",
            "私有页列CSV_SHA256": priv.get("私有页列CSV_SHA256", ""),
            "字段事实集合SHA256": sha256_values([row.get("第一闭环事实范围缺口公开账本ID", "") for row in rows]),
            "任务集合SHA256": sha256_values([row.get("稳定基座第一闭环明细任务ID", "") for row in rows]),
            "专业行集合SHA256": sha256_values([row.get("专业行ID", "") for row in rows]),
            "页列Overlay状态": "R0-Overlay已生成未填写" if status_counts.get("blocked_until_private_overlay_complete", 0) == len(rows) else "R1-Overlay部分填写仍阻断",
            "页列下一步字段闭环动作": "逐字段补 PDF 原页、湖北官方侧、高校辅证人工核验和双人复核；可进入写回评审前不得更新字段事实。",
            "公开安全策略": "公开层只保存页列计数、状态、ID和私有CSV SHA；不公开学校专业明细、字段线索、人工记录或备注。",
        }
        add_false_fields(page_row)
        page_rows.append(page_row)

    write_csv(PUBLIC_OUTPUT, public_rows, FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)

    public_text = PUBLIC_OUTPUT.read_text(encoding="utf-8", errors="ignore") + PAGE_OUTPUT.read_text(
        encoding="utf-8", errors="ignore"
    )
    forbidden_hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if forbidden_hits:
        raise SystemExit(f"公开输出包含禁止内容：{forbidden_hits[:8]}")

    field_counts = Counter(row.get("字段名", "") for row in public_rows)
    status_counts = Counter(row.get("G0字段Overlay状态", "") for row in public_rows)
    writeback_counts = Counter(row.get("字段写回评审状态", "") for row in public_rows)
    summary = {
        "status": "issue19_first_closure_g0_conflict_field_review_overlay_v1_ready_not_final",
        "generated_by": "build_issue19_first_closure_g0_conflict_field_review_overlay_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_g0_package_workbench": source_path(G0_PACKAGE),
        "source_g0_package_workbench_sha256": sha256_file(G0_PACKAGE),
        "source_w0_b0_execution_prefill_items": source_path(PREFILL_ITEMS),
        "source_w0_b0_execution_prefill_items_sha256": sha256_file(PREFILL_ITEMS),
        "source_w0_b0_field_backlink": source_path(FIELD_BACKLINK),
        "source_w0_b0_field_backlink_sha256": sha256_file(FIELD_BACKLINK),
        "source_w0_b0_field_backlink_page": source_path(FIELD_BACKLINK_PAGE),
        "source_w0_b0_field_backlink_page_sha256": sha256_file(FIELD_BACKLINK_PAGE),
        "output_table": source_path(PUBLIC_OUTPUT),
        "page_summary_table": source_path(PAGE_OUTPUT),
        "private_overlay_workbench": "g0_conflict_field_review_private_overlay_not_public",
        "private_master_csv_sha256": sha256_file(PRIVATE_MASTER),
        "private_index_csv_sha256": sha256_file(PRIVATE_INDEX),
        "row_count": len(public_rows),
        "page_summary_row_count": len(page_rows),
        "source_g0_package_row_count": len(g0_rows),
        "source_w0_b0_execution_prefill_item_row_count": len(prefill_rows),
        "source_w0_b0_field_backlink_row_count": len(backlink_rows),
        "source_w0_b0_field_backlink_page_row_count": len(backlink_page_rows),
        "private_overlay_row_count": len(private_rows),
        "private_page_side_csv_count": len(private_index_rows),
        "unique_page_side_count": len({row.get("页码版面键", "") for row in public_rows}),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID", "") for row in public_rows}),
        "unique_major_row_count": len({row.get("专业行ID", "") for row in public_rows}),
        "field_name_counts": dict(field_counts),
        "pdf_ocr_school_conflict_field_count": sum(row.get("是否存在PDFOCR与高校冲突") == "true" for row in public_rows),
        "school_source_double_check_field_count": sum(row.get("是否有高校辅证线索") == "true" for row in public_rows),
        "double_review_required_field_count": sum(row.get("是否需要双人复核") == "true" for row in public_rows),
        "manual_image_required_field_count": sum(row.get("是否需要人工直接看图") == "true" for row in public_rows),
        "structured_candidate_field_count": sum(1 for row in public_rows if clean(row.get("结构化接入候选数", "")) not in {"", "0"}),
        "pdf_reading_filled_count": sum(row.get("PDF原页字段记录填写状态") == "R1-PDF原页字段记录已填" for row in public_rows),
        "hubei_official_filled_count": sum(row.get("湖北官方记录填写状态") == "R1-湖北官方记录已填" for row in public_rows),
        "school_side_manual_filled_count": sum(row.get("高校辅证人工核验状态") == "R1-高校辅证人工核验已填" for row in public_rows),
        "double_review_completed_count": sum(row.get("双人复核状态") == "R1-双人复核已完成" for row in public_rows),
        "three_way_evaluated_count": sum(row.get("三方一致性状态") == "R1-三方一致性已评估" for row in public_rows),
        "ready_for_private_writeback_review_count": writeback_counts.get("ready_for_private_writeback_review", 0),
        "blocked_until_private_overlay_complete_count": writeback_counts.get("blocked_until_private_overlay_complete", 0),
        "overlay_status_counts": dict(status_counts),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该账本只同步G0冲突字段私有Overlay填写进度，不公开字段线索或人工记录，不确认字段事实。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
