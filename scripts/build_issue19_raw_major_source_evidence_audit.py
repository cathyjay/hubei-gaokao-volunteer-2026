#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RAW_MAJOR_DRAFT = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
QUALITY_WORKBENCH = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
PDF_ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
RAW_LINEAGE_AUDIT = ROOT / "data/working/issue19-raw-major-lineage-consistency-audit.csv"

PRIVATE_OCR_LINES = ROOT / "private/ocr-runs/issue19-full-120dpi/ocr-lines.csv"
PRIVATE_PAGE_MANIFEST = ROOT / "private/ocr-runs/issue19-full-120dpi/manifest.csv"
PRIVATE_QC_ISSUES = ROOT / "private/ocr-runs/issue19-full-120dpi/qc_issues.csv"
PRIVATE_WINDOWS = (
    ROOT
    / "private/derived/issue19-major-line-evidence-windows/major-line-ocr-window-evidence.jsonl"
)

OUTPUT = ROOT / "data/working/issue19-raw-major-source-evidence-audit.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-raw-major-source-evidence-audit-summary.json"

DATA_STAGE = "issue19_raw_major_source_evidence_audit"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"


FIELDS = [
    "原始专业行源证据审计ID",
    "来源全量专业明细OCR初稿",
    "来源逐专业质量工作台",
    "来源原始专业行血缘审计表",
    "来源专业行原页证据锚点表",
    "来源公开页级manifest",
    "来源私有OCR行级CSV",
    "来源私有OCR页级manifest",
    "来源私有OCR窗口JSONL",
    "来源私有OCR_QC清单",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "专业行ID",
    "原始CSV数据行号",
    "专业明细源行号",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR短摘",
    "专业起始行号",
    "专业起始y",
    "OCR置信度",
    "私有OCR起始行匹配状态",
    "私有OCR起始行页码一致",
    "私有OCR起始行栏位一致",
    "私有OCR起始行行号一致",
    "私有OCR起始行y一致",
    "私有OCR起始行置信度一致",
    "私有OCR起始行文本SHA256",
    "私有OCR起始行哈希与公开锚点一致",
    "私有OCR起始行专业代号匹配",
    "私有OCR起始行类型",
    "起始行QC_P0数",
    "起始行QC_P1数",
    "起始行QC规则ID集合",
    "公开页级manifest匹配状态",
    "私有页级manifest匹配状态",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有页图SHA256一致",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "私有OCR行数一致",
    "私有OCR平均置信度一致",
    "OCR识别行数",
    "OCR平均置信度",
    "OCR_QC_P0数",
    "OCR_QC_P1数",
    "低置信度页标记",
    "公开锚点匹配状态",
    "专业行原页证据锚点ID",
    "证据锚点状态",
    "起始行回连状态",
    "起始行专业代号匹配",
    "专业窗口行号范围",
    "合并证据窗口行号范围",
    "专业窗口行数",
    "合并证据窗口行数",
    "窗口文本SHA256",
    "窗口平均置信度",
    "窗口最低置信度",
    "私有窗口JSONL匹配状态",
    "私有窗口证据编号",
    "私有窗口SHA一致",
    "私有窗口页码一致",
    "私有窗口栏位一致",
    "私有窗口专业代号一致",
    "私有窗口专业行数",
    "私有窗口组上下文行数",
    "私有窗口状态一致",
    "原始血缘审计匹配状态",
    "原始血缘审计结论",
    "源证据覆盖结论",
    "源证据风险等级",
    "源证据风险标签",
    "不得进入原因",
    "下一步",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def as_float(value):
    try:
        return float(str(value or "").strip())
    except ValueError:
        return 0.0


def bool_text(value):
    return "true" if value else "false"


def short_text(value, limit=80):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def normalize_code(value):
    return (
        str(value or "")
        .upper()
        .replace("Ｏ", "0")
        .replace("O", "0")
        .replace("Ｉ", "1")
        .replace("I", "1")
        .replace("Ｌ", "1")
        .replace("L", "1")
        .replace("/", "")
        .replace(" ", "")
    )


def same_float(left, right, tolerance=0.000001):
    if str(left or "").strip() == "" and str(right or "").strip() == "":
        return True
    return abs(as_float(left) - as_float(right)) <= tolerance


def ordered_join(values):
    seen = set()
    result = []
    for value in values:
        cleaned = str(value or "").strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return "；".join(result)


def line_public_fingerprint(line):
    if not line:
        return ""
    material = "|".join(
        [
            str(line.get("page", "")),
            str(line.get("table_band", "")),
            str(line.get("line_no", "")),
            str(line.get("text", "")),
            str(line.get("x", "")),
            str(line.get("y", "")),
        ]
    )
    return sha256_text(material)


def private_window_combined_sha(window):
    if not window:
        return ""
    lines = sorted(
        window.get("group_context_lines", []) + window.get("major_window_lines", []),
        key=lambda line: as_int(line.get("line_no")),
    )
    material = "\n".join(
        f"{line.get('line_no')}|{line.get('text')}|{line.get('confidence')}|{line.get('x')}|{line.get('y')}"
        for line in lines
    )
    return sha256_text(material)


def read_private_windows(path):
    windows = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            payload = json.loads(line)
            windows[payload.get("major_line_id", "")] = payload
    return windows


def page_key(row):
    return str(as_int(row.get("来源页码") or row.get("PDF页码") or row.get("page") or row.get("序号")))


def start_line_key(row):
    return (
        str(as_int(row.get("来源页码") or row.get("page"))),
        str(row.get("版面列") or row.get("table_band") or ""),
        str(as_int(row.get("专业起始行号") or row.get("line_no"))),
    )


def build_indexes():
    raw_rows = read_csv(RAW_MAJOR_DRAFT)
    quality_rows = read_csv(QUALITY_WORKBENCH)
    page_manifest_rows = read_csv(PAGE_MANIFEST)
    anchor_rows = read_csv(PDF_ANCHORS)
    raw_lineage_rows = read_csv(RAW_LINEAGE_AUDIT)
    ocr_line_rows = read_csv(PRIVATE_OCR_LINES)
    private_page_manifest_rows = read_csv(PRIVATE_PAGE_MANIFEST)
    qc_rows = read_csv(PRIVATE_QC_ISSUES)
    private_windows = read_private_windows(PRIVATE_WINDOWS)

    ocr_line_by_key = {}
    for row in ocr_line_rows:
        ocr_line_by_key[(page_key(row), row.get("table_band", ""), str(as_int(row.get("line_no"))))] = row

    qc_by_line_key = defaultdict(list)
    for row in qc_rows:
        key = (page_key(row), row.get("table_band", ""), str(as_int(row.get("line_no"))))
        qc_by_line_key[key].append(row)

    quality_by_raw_line = {
        as_int(row.get("专业明细源行号")) - 1: row
        for row in quality_rows
        if as_int(row.get("专业明细源行号"))
    }

    return {
        "raw_rows": raw_rows,
        "quality_by_raw_line": quality_by_raw_line,
        "page_manifest_by_page": {row.get("PDF页码", ""): row for row in page_manifest_rows},
        "anchor_by_major_id": {row.get("专业行ID", ""): row for row in anchor_rows},
        "lineage_by_major_id": {row.get("专业行ID", ""): row for row in raw_lineage_rows},
        "ocr_line_by_key": ocr_line_by_key,
        "private_page_manifest_by_page": {
            str(as_int(row.get("序号"))): row for row in private_page_manifest_rows
        },
        "qc_by_line_key": qc_by_line_key,
        "private_window_by_major_id": private_windows,
        "source_counts": {
            "raw_major_draft_row_count": len(raw_rows),
            "quality_workbench_row_count": len(quality_rows),
            "public_page_manifest_row_count": len(page_manifest_rows),
            "pdf_anchor_row_count": len(anchor_rows),
            "raw_lineage_audit_row_count": len(raw_lineage_rows),
            "private_ocr_line_row_count": len(ocr_line_rows),
            "private_page_manifest_row_count": len(private_page_manifest_rows),
            "private_qc_issue_row_count": len(qc_rows),
            "private_window_jsonl_row_count": len(private_windows),
        },
    }


def source_coverage_conclusion(
    ocr_line_match,
    start_hash_match,
    page_manifest_match,
    private_manifest_match,
    anchor_match,
    private_window_match,
    private_window_sha_match,
    lineage_match,
):
    if not (ocr_line_match and page_manifest_match and anchor_match and lineage_match):
        return "S2-源头证据主链路缺失"
    if not private_manifest_match:
        return "S1-页级私有manifest待核"
    if not private_window_match:
        return "S1-私有窗口证据待核"
    if not (start_hash_match and private_window_sha_match):
        return "S1-源头哈希一致性待核"
    return "S0-私有OCR起始行、页级manifest、窗口证据和公开锚点均已回连"


def source_risk_level(anchor_status, qc_p0_count, qc_p1_count, low_conf_page, coverage_conclusion):
    if coverage_conclusion.startswith("S2"):
        return "R0-源证据缺失阻断"
    if coverage_conclusion.startswith("S1"):
        return "R1-源证据一致性待核"
    if anchor_status.startswith("P0"):
        return "R2-锚点窗口阻断待人工核页"
    if qc_p0_count > 0:
        return "R2-起始行P0_QC待人工核页"
    if anchor_status.startswith("P1") or qc_p1_count > 0 or low_conf_page:
        return "R3-源证据已回连但需优先复核"
    return "R4-源证据已回连且未触发起始行QC风险"


def build_rows():
    indexes = build_indexes()
    rows = []

    for raw_index, raw_row in enumerate(indexes["raw_rows"], start=1):
        quality_row = indexes["quality_by_raw_line"].get(raw_index, {})
        major_id = quality_row.get("专业行ID", "")
        anchor_row = indexes["anchor_by_major_id"].get(major_id, {})
        page_manifest = indexes["page_manifest_by_page"].get(raw_row.get("来源页码", ""), {})
        private_page_manifest = indexes["private_page_manifest_by_page"].get(raw_row.get("来源页码", ""), {})
        private_window = indexes["private_window_by_major_id"].get(major_id, {})
        lineage_row = indexes["lineage_by_major_id"].get(major_id, {})
        line_key = start_line_key(raw_row)
        ocr_line = indexes["ocr_line_by_key"].get(line_key, {})
        qc_rows = indexes["qc_by_line_key"].get(line_key, [])
        qc_p0_count = sum(row.get("severity") == "P0" for row in qc_rows)
        qc_p1_count = sum(row.get("severity") == "P1" for row in qc_rows)

        start_fingerprint = line_public_fingerprint(ocr_line)
        major_code = normalize_code(raw_row.get("专业代号OCR", ""))
        start_code_match = bool(major_code) and major_code in normalize_code(ocr_line.get("text", ""))[:8]
        ocr_line_match = bool(ocr_line)
        start_hash_match = bool(start_fingerprint) and start_fingerprint == anchor_row.get("起始行文本SHA256", "")
        page_manifest_match = bool(page_manifest)
        private_manifest_match = bool(private_page_manifest)
        anchor_match = bool(anchor_row)
        private_window_match = bool(private_window)
        recomputed_private_window_sha = private_window_combined_sha(private_window)
        private_window_sha_match = (
            bool(private_window)
            and recomputed_private_window_sha
            and recomputed_private_window_sha == anchor_row.get("窗口文本SHA256", "")
            and private_window.get("combined_window_sha256", "") == recomputed_private_window_sha
        )
        lineage_match = bool(lineage_row)

        private_manifest_page_sha_match = (
            bool(private_page_manifest)
            and private_page_manifest.get("SHA256", "") == page_manifest.get("私有页图SHA256", "")
        )
        private_manifest_line_count_match = (
            bool(private_page_manifest)
            and str(as_int(private_page_manifest.get("识别行数"))) == str(as_int(page_manifest.get("OCR识别行数")))
        )
        private_manifest_confidence_match = (
            bool(private_page_manifest)
            and same_float(private_page_manifest.get("平均置信度"), page_manifest.get("OCR平均置信度"))
        )

        low_conf_page = as_float(page_manifest.get("OCR平均置信度")) < 0.65 if page_manifest else False
        coverage_conclusion = source_coverage_conclusion(
            ocr_line_match,
            start_hash_match,
            page_manifest_match,
            private_manifest_match,
            anchor_match,
            private_window_match,
            private_window_sha_match,
            lineage_match,
        )
        risk_tags = [
            f"anchor_status={anchor_row.get('证据锚点状态')}" if anchor_row else "missing_public_anchor",
            "start_line_qc_p0" if qc_p0_count else "",
            "start_line_qc_p1" if qc_p1_count else "",
            "low_confidence_page_below_0_65" if low_conf_page else "",
            "start_hash_mismatch" if ocr_line_match and not start_hash_match else "",
            "private_window_sha_mismatch" if private_window_match and not private_window_sha_match else "",
            "private_page_manifest_mismatch"
            if private_manifest_match
            and not (
                private_manifest_page_sha_match
                and private_manifest_line_count_match
                and private_manifest_confidence_match
            )
            else "",
        ]
        risk_level = source_risk_level(
            anchor_row.get("证据锚点状态", ""),
            qc_p0_count,
            qc_p1_count,
            low_conf_page,
            coverage_conclusion,
        )

        block_reasons = [
            "本表只审计原始逐专业明细能否回到OCR行、页级manifest、窗口证据和公开锚点",
            "字段事实仍需PDF原页、湖北官方系统或省招办计划、高校官网/章程交叉确认",
            "家庭接受度、完整专业组调剂风险和三年投档稳定性未在本表闭环",
            "闭环前不得用于志愿推荐、排序或填报结论",
        ]
        if not coverage_conclusion.startswith("S0"):
            block_reasons.append("存在源头证据一致性待核")
        if risk_level.startswith("R2"):
            block_reasons.append("存在锚点窗口或起始行QC阻断")

        rows.append({
            "原始专业行源证据审计ID": stable_id("RAWSOURCE", [major_id or raw_index, SOURCE_PDF_SHA256]),
            "来源全量专业明细OCR初稿": "data/working/issue19-full-admission-plan-major-ocr-draft.csv",
            "来源逐专业质量工作台": "data/working/issue19-full-major-detail-quality-workbench.csv",
            "来源原始专业行血缘审计表": "data/working/issue19-raw-major-lineage-consistency-audit.csv",
            "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
            "来源公开页级manifest": "data/working/issue19-page-manifest.csv",
            "来源私有OCR行级CSV": "private_ocr_lines_not_public",
            "来源私有OCR页级manifest": "private_ocr_page_manifest_not_public",
            "来源私有OCR窗口JSONL": "private_ocr_window_jsonl_not_public",
            "来源私有OCR_QC清单": "private_ocr_qc_issues_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "是否允许作为志愿推荐依据": "false",
            "专业行ID": major_id,
            "原始CSV数据行号": str(raw_index),
            "专业明细源行号": quality_row.get("专业明细源行号", ""),
            "专业组出现ID": quality_row.get("专业组出现ID", ""),
            "院校代码": raw_row.get("院校代码", ""),
            "院校名称OCR": raw_row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": raw_row.get("院校专业组代码OCR规范化", ""),
            "来源页码": raw_row.get("来源页码", ""),
            "版面列": raw_row.get("版面列", ""),
            "专业组内专业序号": quality_row.get("专业组内专业序号", ""),
            "专业代号OCR": raw_row.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": short_text(raw_row.get("专业名称及备注OCR")),
            "专业起始行号": raw_row.get("专业起始行号", ""),
            "专业起始y": raw_row.get("专业起始y", ""),
            "OCR置信度": raw_row.get("OCR置信度", ""),
            "私有OCR起始行匹配状态": "exact_private_ocr_start_line_hit" if ocr_line_match else "missing_private_ocr_start_line",
            "私有OCR起始行页码一致": bool_text(ocr_line_match and str(as_int(ocr_line.get("page"))) == raw_row.get("来源页码", "")),
            "私有OCR起始行栏位一致": bool_text(ocr_line_match and ocr_line.get("table_band", "") == raw_row.get("版面列", "")),
            "私有OCR起始行行号一致": bool_text(ocr_line_match and str(as_int(ocr_line.get("line_no"))) == str(as_int(raw_row.get("专业起始行号")))),
            "私有OCR起始行y一致": bool_text(ocr_line_match and same_float(ocr_line.get("y"), raw_row.get("专业起始y"))),
            "私有OCR起始行置信度一致": bool_text(ocr_line_match and same_float(ocr_line.get("confidence"), raw_row.get("OCR置信度"))),
            "私有OCR起始行文本SHA256": start_fingerprint,
            "私有OCR起始行哈希与公开锚点一致": bool_text(start_hash_match),
            "私有OCR起始行专业代号匹配": bool_text(start_code_match),
            "私有OCR起始行类型": ocr_line.get("line_type", ""),
            "起始行QC_P0数": str(qc_p0_count),
            "起始行QC_P1数": str(qc_p1_count),
            "起始行QC规则ID集合": ordered_join(row.get("rule_id", "") for row in qc_rows),
            "公开页级manifest匹配状态": "matched_public_page_manifest" if page_manifest_match else "missing_public_page_manifest",
            "私有页级manifest匹配状态": "matched_private_page_manifest" if private_manifest_match else "missing_private_page_manifest",
            "私有页图证据编号": page_manifest.get("私有页图证据编号", ""),
            "私有页图SHA256": page_manifest.get("私有页图SHA256", ""),
            "私有页图SHA256一致": bool_text(private_manifest_page_sha_match),
            "私有OCR文本证据编号": page_manifest.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": page_manifest.get("私有OCR文本SHA256", ""),
            "私有OCR行数一致": bool_text(private_manifest_line_count_match),
            "私有OCR平均置信度一致": bool_text(private_manifest_confidence_match),
            "OCR识别行数": page_manifest.get("OCR识别行数", ""),
            "OCR平均置信度": page_manifest.get("OCR平均置信度", ""),
            "OCR_QC_P0数": page_manifest.get("OCR_QC_P0数", ""),
            "OCR_QC_P1数": page_manifest.get("OCR_QC_P1数", ""),
            "低置信度页标记": bool_text(low_conf_page),
            "公开锚点匹配状态": "matched_public_pdf_anchor" if anchor_match else "missing_public_pdf_anchor",
            "专业行原页证据锚点ID": anchor_row.get("专业行原页证据锚点ID", ""),
            "证据锚点状态": anchor_row.get("证据锚点状态", ""),
            "起始行回连状态": anchor_row.get("起始行回连状态", ""),
            "起始行专业代号匹配": anchor_row.get("起始行专业代号匹配", ""),
            "专业窗口行号范围": anchor_row.get("专业窗口行号范围", ""),
            "合并证据窗口行号范围": anchor_row.get("合并证据窗口行号范围", ""),
            "专业窗口行数": anchor_row.get("专业窗口行数", ""),
            "合并证据窗口行数": anchor_row.get("合并证据窗口行数", ""),
            "窗口文本SHA256": anchor_row.get("窗口文本SHA256", ""),
            "窗口平均置信度": anchor_row.get("窗口平均置信度", ""),
            "窗口最低置信度": anchor_row.get("窗口最低置信度", ""),
            "私有窗口JSONL匹配状态": "matched_private_window_jsonl" if private_window_match else "missing_private_window_jsonl",
            "私有窗口证据编号": private_window.get("evidence_id", ""),
            "私有窗口SHA一致": bool_text(private_window_sha_match),
            "私有窗口页码一致": bool_text(private_window_match and str(private_window.get("source_page", "")) == raw_row.get("来源页码", "")),
            "私有窗口栏位一致": bool_text(private_window_match and private_window.get("table_band", "") == raw_row.get("版面列", "")),
            "私有窗口专业代号一致": bool_text(private_window_match and private_window.get("major_code_ocr", "") == raw_row.get("专业代号OCR", "")),
            "私有窗口专业行数": str(len(private_window.get("major_window_lines", []))) if private_window_match else "",
            "私有窗口组上下文行数": str(len(private_window.get("group_context_lines", []))) if private_window_match else "",
            "私有窗口状态一致": bool_text(private_window_match and private_window.get("public_anchor_status", "") == anchor_row.get("证据锚点状态", "")),
            "原始血缘审计匹配状态": "matched_raw_lineage_audit" if lineage_match else "missing_raw_lineage_audit",
            "原始血缘审计结论": lineage_row.get("血缘审计结论", ""),
            "源证据覆盖结论": coverage_conclusion,
            "源证据风险等级": risk_level,
            "源证据风险标签": ordered_join(risk_tags),
            "不得进入原因": "；".join(block_reasons),
            "下一步": "先按源证据风险等级和锚点状态安排PDF原页人工核页，再与湖北官方系统、省招办计划和高校官网/章程逐字段交叉；本表不生成学校或专业推荐。",
        })

    rows.sort(
        key=lambda row: (
            as_int(row.get("来源页码")),
            0 if row.get("版面列") == "left" else 1,
            as_int(row.get("专业起始行号")),
            row.get("专业行ID", ""),
        )
    )
    return rows, indexes


def write_summary(rows, indexes):
    summary = {
        "status": "issue19_raw_major_source_evidence_audit_not_final",
        "generated_by": Path(__file__).name,
        "source_raw_major_draft": "data/working/issue19-full-admission-plan-major-ocr-draft.csv",
        "source_quality_workbench": "data/working/issue19-full-major-detail-quality-workbench.csv",
        "source_raw_lineage_audit": "data/working/issue19-raw-major-lineage-consistency-audit.csv",
        "source_pdf_anchors": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "source_public_page_manifest": "data/working/issue19-page-manifest.csv",
        "source_private_ocr_lines": "private_ocr_lines_not_public",
        "source_private_page_manifest": "private_ocr_page_manifest_not_public",
        "source_private_windows": "private_ocr_window_jsonl_not_public",
        "source_private_qc_issues": "private_ocr_qc_issues_not_public",
        "output_table": "data/working/issue19-raw-major-source-evidence-audit.csv",
        "row_grain": "逐专业招生明细",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_audit_id_count": len({row.get("原始专业行源证据审计ID") for row in rows}),
        "unique_major_line_id_count": len({row.get("专业行ID") for row in rows}),
        "unique_raw_csv_data_line_count": len({row.get("原始CSV数据行号") for row in rows}),
        "source_counts": indexes["source_counts"],
        "private_ocr_start_line_match_count": sum(row.get("私有OCR起始行匹配状态") == "exact_private_ocr_start_line_hit" for row in rows),
        "private_ocr_start_line_hash_match_count": sum(row.get("私有OCR起始行哈希与公开锚点一致") == "true" for row in rows),
        "private_ocr_start_line_major_code_match_count": sum(row.get("私有OCR起始行专业代号匹配") == "true" for row in rows),
        "public_page_manifest_match_count": sum(row.get("公开页级manifest匹配状态") == "matched_public_page_manifest" for row in rows),
        "private_page_manifest_match_count": sum(row.get("私有页级manifest匹配状态") == "matched_private_page_manifest" for row in rows),
        "private_page_sha_match_count": sum(row.get("私有页图SHA256一致") == "true" for row in rows),
        "private_ocr_line_count_match_count": sum(row.get("私有OCR行数一致") == "true" for row in rows),
        "private_ocr_confidence_match_count": sum(row.get("私有OCR平均置信度一致") == "true" for row in rows),
        "public_anchor_match_count": sum(row.get("公开锚点匹配状态") == "matched_public_pdf_anchor" for row in rows),
        "private_window_jsonl_match_count": sum(row.get("私有窗口JSONL匹配状态") == "matched_private_window_jsonl" for row in rows),
        "private_window_sha_match_count": sum(row.get("私有窗口SHA一致") == "true" for row in rows),
        "raw_lineage_audit_match_count": sum(row.get("原始血缘审计匹配状态") == "matched_raw_lineage_audit" for row in rows),
        "coverage_conclusion_counts": dict(Counter(row.get("源证据覆盖结论") for row in rows)),
        "source_risk_level_counts": dict(Counter(row.get("源证据风险等级") for row in rows)),
        "anchor_status_counts": dict(Counter(row.get("证据锚点状态") for row in rows)),
        "start_line_qc_p0_row_count": sum(as_int(row.get("起始行QC_P0数")) > 0 for row in rows),
        "start_line_qc_p1_row_count": sum(as_int(row.get("起始行QC_P1数")) > 0 for row in rows),
        "start_line_qc_p0_total_count": sum(as_int(row.get("起始行QC_P0数")) for row in rows),
        "start_line_qc_p1_total_count": sum(as_int(row.get("起始行QC_P1数")) for row in rows),
        "low_confidence_page_major_line_count": sum(row.get("低置信度页标记") == "true" for row in rows),
        "final_available_count": sum(row.get("最终可用") == "true" for row in rows),
        "next_stage_available_count": sum(row.get("可进入下一阶段") == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row.get("机器是否允许自动写回主表") == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row.get("是否允许作为志愿推荐依据") == "true" for row in rows),
        "public_safety_note": "本产物只保存公开安全的源证据编号、页码、行号、坐标哈希和QC计数；不保存私有OCR窗口原文、图片路径、登录态或个人身份信息。",
        "decision_boundary_note": "本产物用于确认原始逐专业明细能否回到源头证据；不用于院校专业推荐、志愿排序或最终填报结论。",
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    rows, indexes = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    write_summary(rows, indexes)
    print(f"写出原始专业行源证据审计表：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
