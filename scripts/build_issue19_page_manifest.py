#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
OCR_RUN_SUMMARY = ROOT / "data/working/issue19-ocr-run-summary.json"
FOUNDATION_PAGE_AUDIT = ROOT / "data/working/issue19-foundation-page-audit.csv"
GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
STRUCTURE_ANOMALIES = ROOT / "data/working/issue19-ocr-structure-anomaly-queue.csv"
FIELD_LEDGER = ROOT / "data/working/issue19-candidate-v2-field-review-ledger.csv"
PRIVATE_OCR_DIR = ROOT / "private/ocr-runs/issue19-full-120dpi"
PRIVATE_PAGE_MANIFEST = PRIVATE_OCR_DIR / "manifest.csv"
PRIVATE_OCR_LINES = PRIVATE_OCR_DIR / "ocr-lines.csv"
PRIVATE_QC_ISSUES = PRIVATE_OCR_DIR / "qc_issues.csv"
PRIVATE_SUSPECTED_PLAN_LINES = PRIVATE_OCR_DIR / "suspected_plan_lines.csv"

PAGE_MANIFEST_OUTPUT = ROOT / "data/working/issue19-page-manifest.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-page-manifest-summary.json"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def basename_without_suffix(path_text):
    if not path_text:
        return ""
    return Path(path_text).stem


def text_sha_for_manifest_row(row):
    text_file = row.get("文本文件", "")
    if not text_file:
        return ""
    text_path = PRIVATE_OCR_DIR / text_file
    if not text_path.exists():
        return ""
    return sha256(text_path)


def counter_text(counter):
    return "；".join(f"{key}:{value}" for key, value in sorted(counter.items()))


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    ocr_run_summary = json.loads(OCR_RUN_SUMMARY.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]

    private_manifest_rows = read_csv(PRIVATE_PAGE_MANIFEST)
    ocr_line_rows = read_csv(PRIVATE_OCR_LINES)
    qc_rows = read_csv(PRIVATE_QC_ISSUES)
    suspected_rows = read_csv(PRIVATE_SUSPECTED_PLAN_LINES)
    foundation_page_rows = read_csv(FOUNDATION_PAGE_AUDIT)
    group_rows = read_csv(GROUPS)
    major_rows = read_csv(MAJORS)
    anomaly_rows = read_csv(STRUCTURE_ANOMALIES)
    field_ledger_rows = read_csv(FIELD_LEDGER)

    private_manifest_by_page = {as_int(row["序号"]): row for row in private_manifest_rows}
    foundation_by_page = {as_int(row["来源页码"]): row for row in foundation_page_rows}

    line_type_counts_by_page = defaultdict(Counter)
    band_counts_by_page = defaultdict(Counter)
    for row in ocr_line_rows:
        page = as_int(row.get("page"))
        if page is None:
            continue
        line_type_counts_by_page[page][row.get("line_type", "")] += 1
        band_counts_by_page[page][row.get("table_band", "")] += 1

    qc_counts_by_page = defaultdict(Counter)
    for row in qc_rows:
        page = as_int(row.get("page"))
        if page is None:
            continue
        qc_counts_by_page[page][row.get("severity", "")] += 1

    suspected_count_by_page = Counter()
    for row in suspected_rows:
        page = as_int(row.get("序号"))
        if page is not None:
            suspected_count_by_page[page] += 1

    school_count_by_page = defaultdict(set)
    group_count_by_page = Counter()
    major_count_by_page = Counter()
    anomaly_count_by_page = Counter()
    high_anomaly_count_by_page = Counter()
    candidate_field_task_count_by_page = Counter()
    candidate_p0_field_task_count_by_page = Counter()
    for row in group_rows:
        page = as_int(row.get("来源页码"))
        if page is not None:
            group_count_by_page[page] += 1
            if row.get("院校代码"):
                school_count_by_page[page].add(row["院校代码"])
    for row in major_rows:
        page = as_int(row.get("来源页码"))
        if page is not None:
            major_count_by_page[page] += 1
    for row in anomaly_rows:
        page = as_int(row.get("来源页码"))
        if page is not None:
            anomaly_count_by_page[page] += 1
            high_anomaly_count_by_page[page] += row.get("严重程度") == "高"
    for row in field_ledger_rows:
        page = as_int(row.get("来源页码"))
        if page is not None:
            candidate_field_task_count_by_page[page] += 1
            candidate_p0_field_task_count_by_page[page] += row.get("复核优先级") == "P0-字段必须优先核"
    candidate_field_task_without_single_page_count = sum(
        as_int(row.get("来源页码")) is None for row in field_ledger_rows
    )
    candidate_p0_field_task_total_count = sum(
        row.get("复核优先级") == "P0-字段必须优先核" for row in field_ledger_rows
    )

    page_rows = []
    for page in range(1, 241):
        private_row = private_manifest_by_page.get(page, {})
        foundation_row = foundation_by_page.get(page, {})
        text_hash = text_sha_for_manifest_row(private_row)
        line_types = line_type_counts_by_page[page]
        bands = band_counts_by_page[page]
        qc_counts = qc_counts_by_page[page]
        structured_status = (
            "结构化招生计划页"
            if group_count_by_page[page] or major_count_by_page[page]
            else "非结构化前置页或未抽取招生明细页"
        )
        if page >= 10 and not (group_count_by_page[page] and major_count_by_page[page]):
            structured_status = "应有招生明细但结构化缺失"

        output = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "issue19_public_page_manifest",
            "最终可用": "false",
            "PDF页码": str(page),
            "页码范围角色": "招生计划明细页" if page >= 10 else "前置说明页",
            "私有页图证据编号": basename_without_suffix(private_row.get("源图片", "")),
            "私有页图SHA256": private_row.get("SHA256", ""),
            "私有页图大小字节": private_row.get("大小字节", ""),
            "私有OCR文本证据编号": basename_without_suffix(private_row.get("文本文件", "")),
            "私有OCR文本SHA256": text_hash,
            "OCR引擎": private_row.get("OCR引擎", ""),
            "识别语言": private_row.get("识别语言", ""),
            "OCR识别行数": private_row.get("识别行数", ""),
            "OCR平均置信度": private_row.get("平均置信度", ""),
            "OCR错误": private_row.get("错误", ""),
            "OCR行类型分布": counter_text(line_types),
            "OCR栏位分布": counter_text(bands),
            "OCR_QC_P0数": str(qc_counts["P0"]),
            "OCR_QC_P1数": str(qc_counts["P1"]),
            "疑似招生计划行数": str(suspected_count_by_page[page]),
            "结构化状态": structured_status,
            "结构化院校数": str(len(school_count_by_page[page])),
            "结构化专业组数": str(group_count_by_page[page]),
            "结构化专业明细数": str(major_count_by_page[page]),
            "结构异常数": str(anomaly_count_by_page[page]),
            "高严重结构异常数": str(high_anomaly_count_by_page[page]),
            "候选V2字段任务数": str(candidate_field_task_count_by_page[page]),
            "候选V2字段P0任务数": str(candidate_p0_field_task_count_by_page[page]),
            "底座页级复核优先级": foundation_row.get("页面复核优先级", ""),
            "底座页级审计状态": foundation_row.get("页面审计状态", ""),
            "核验状态": "needs_manual_pdf_review",
            "下一步": "如该页进入候选或存在异常，回看私有PDF页图和OCR文本；字段值必须再核湖北官方系统和高校章程。",
        }
        page_rows.append(output)
    candidate_p0_field_task_on_single_page_count = sum(
        as_int(row["候选V2字段P0任务数"]) or 0 for row in page_rows
    )

    fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "PDF页码",
        "页码范围角色",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有页图大小字节",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "OCR引擎",
        "识别语言",
        "OCR识别行数",
        "OCR平均置信度",
        "OCR错误",
        "OCR行类型分布",
        "OCR栏位分布",
        "OCR_QC_P0数",
        "OCR_QC_P1数",
        "疑似招生计划行数",
        "结构化状态",
        "结构化院校数",
        "结构化专业组数",
        "结构化专业明细数",
        "结构异常数",
        "高严重结构异常数",
        "候选V2字段任务数",
        "候选V2字段P0任务数",
        "底座页级复核优先级",
        "底座页级审计状态",
        "核验状态",
        "下一步",
    ]
    write_csv(PAGE_MANIFEST_OUTPUT, page_rows, fields)

    summary = {
        "status": "issue19_page_manifest_public_metadata_ready",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "issue19_public_page_manifest",
        "generated_by": "scripts/build_issue19_page_manifest.py",
        "inputs": input_snapshot(
            ROOT,
            [
                ISSUE19_SOURCE,
                OCR_RUN_SUMMARY,
                FOUNDATION_PAGE_AUDIT,
                GROUPS,
                MAJORS,
                STRUCTURE_ANOMALIES,
                FIELD_LEDGER,
            ],
        ),
        "private_inputs": {
            "ocr_run_id": "issue19-full-120dpi",
            "page_manifest_row_count": len(private_manifest_rows),
            "ocr_line_count": len(ocr_line_rows),
            "qc_issue_count": len(qc_rows),
            "suspected_plan_line_count": len(suspected_rows),
        },
        "page_count": len(page_rows),
        "rendered_page_count": sum(bool(row["私有页图SHA256"]) for row in page_rows),
        "ocr_text_page_count": sum(bool(row["私有OCR文本SHA256"]) for row in page_rows),
        "structured_plan_page_range": [10, 240],
        "structured_plan_page_count": sum(row["页码范围角色"] == "招生计划明细页" for row in page_rows),
        "structured_plan_pages_with_group_and_major_count": sum(
            row["页码范围角色"] == "招生计划明细页"
            and as_int(row["结构化专业组数"]) > 0
            and as_int(row["结构化专业明细数"]) > 0
            for row in page_rows
        ),
        "structured_school_count_sum_by_page": sum(as_int(row["结构化院校数"]) or 0 for row in page_rows),
        "structured_group_count": sum(as_int(row["结构化专业组数"]) or 0 for row in page_rows),
        "structured_major_count": sum(as_int(row["结构化专业明细数"]) or 0 for row in page_rows),
        "structure_anomaly_count": sum(as_int(row["结构异常数"]) or 0 for row in page_rows),
        "high_structure_anomaly_count": sum(as_int(row["高严重结构异常数"]) or 0 for row in page_rows),
        "candidate_v2_field_task_count": len(field_ledger_rows),
        "candidate_v2_field_task_on_single_page_count": sum(
            as_int(row["候选V2字段任务数"]) or 0 for row in page_rows
        ),
        "candidate_v2_field_task_without_single_page_count": candidate_field_task_without_single_page_count,
        "candidate_v2_p0_field_task_count": candidate_p0_field_task_total_count,
        "candidate_v2_p0_field_task_on_single_page_count": candidate_p0_field_task_on_single_page_count,
        "candidate_v2_p0_field_task_without_single_page_count": (
            candidate_p0_field_task_total_count - candidate_p0_field_task_on_single_page_count
        ),
        "low_confidence_page_count_below_0_65": ocr_run_summary["summary"][
            "low_confidence_page_count_below_0_65"
        ],
        "low_confidence_pages_below_0_65": ocr_run_summary["summary"][
            "low_confidence_pages_below_0_65"
        ],
        "outputs": [str(PAGE_MANIFEST_OUTPUT.relative_to(ROOT))],
        "notes": [
            "本表只公开页级元数据和哈希，不公开私有页图、整页OCR文本或本机绝对路径。",
            "私有页图证据编号和私有OCR文本证据编号只用于在本机私有目录定位证据。",
            "来源页码为复合页码的候选任务不强行拆入单页统计，已在摘要中单独计数。",
            "本表不能替代第19期原PDF页、湖北官方系统或高校章程的人工核验。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出第19期公开页级manifest：{PAGE_MANIFEST_OUTPUT}")
    print(f"写出第19期页级manifest摘要：{SUMMARY_OUTPUT}")
    print(f"页数：{len(page_rows)}")
    print(f"招生计划明细页：{summary['structured_plan_page_count']}")


if __name__ == "__main__":
    main()
