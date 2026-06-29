#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

PAGE_SIDE_PUBLIC = (
    WORKING / "issue19-school-source-adapter-d0-d1-page-side-packets-v1-public-ledger.csv"
)
PAGE_SIDE_SUMMARY = (
    WORKING / "issue19-school-source-adapter-d0-d1-page-side-packets-v1-summary.json"
)
PRIVATE_PAGE_SIDE_DIR = (
    ROOT / "private/review-assets/issue19-school-source-adapter-d0-d1-page-side-packets-v1"
)
PRIVATE_PAGE_SIDE_INDEX = PRIVATE_PAGE_SIDE_DIR / "page-side-packets-private-index.csv"

PUBLIC_OUTPUT = (
    WORKING / "issue19-school-source-adapter-d0-d1-page-side-progress-v1-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    WORKING / "issue19-school-source-adapter-d0-d1-page-side-progress-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_adapter_d0_d1_page_side_progress_v1"
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

PUBLIC_FIELDS = [
    "高校源AdapterD0D1页列进度公开账本ID",
    "来源D0D1页列核验包公开账本",
    "来源D0D1页列核验包摘要",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "页列执行序号",
    "来源页码",
    "版面列",
    "页码版面键SHA16",
    "高校源AdapterD0D1页列核验包ID",
    "页列执行优先级",
    "私有核验项数",
    "R0计划数冲突项数",
    "R1OCR计划数可补项数",
    "R2疑似匹配项数",
    "R3计划数一致抽检项数",
    "PDF原页记录已填项数",
    "PDF原页记录未填项数",
    "湖北官方计划记录已填项数",
    "湖北官方计划记录未填项数",
    "高校源差异解释已填项数",
    "高校源差异解释未填项数",
    "最终字段处理建议已填项数",
    "最终字段处理建议未填项数",
    "双人复核建议项数",
    "双人复核已填项数",
    "双人复核未填项数",
    "可进入字段写回评审项数",
    "页列进度桶",
    "页列进度状态",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页列HTML证据编号",
    "私有页列HTML_SHA256",
    "私有页列索引CSV_SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

REQUIRED_PRIVATE_FIELDS = [
    "PDF原页人工核验记录",
    "湖北官方计划人工核验记录",
    "高校源差异解释记录",
    "最终字段处理建议",
    "复核人A",
    "复核人B",
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
    "专业名称及备注OCR",
    "专业代号",
    "院校专业组代码",
    "官方来源文件",
    "最佳高校源专业名称",
    "最佳高校源计划数",
    "字段值",
    "字段读数",
    "人工读数",
    "候选值",
    "OCR正文",
    "OCR行文本",
    "截图路径",
    "复核备注",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
    "data/external/",
]


def clean(value):
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames or []


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: clean(row.get(field, "")) for field in fields} for row in rows])


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha16(values):
    text = "\n".join(sorted({clean(value) for value in values if clean(value)}))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else ""


def source_path(path):
    return str(path.relative_to(ROOT))


def stable_id(prefix, parts):
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def as_int(value):
    try:
        return int(str(value).strip() or "0")
    except ValueError:
        return 0


def is_filled(row, field):
    return bool(clean(row.get(field, "")))


def progress_bucket(total, pdf_done, hubei_done, school_done, final_done, writeback_ready):
    if writeback_ready == total and total:
        return "R4-可进入字段写回评审", "all_required_private_records_complete"
    if pdf_done == total and hubei_done == total and school_done == total and total:
        return "R3-私有记录已齐待一致性复查", "private_records_complete_pending_consistency_review"
    if pdf_done or hubei_done or school_done or final_done:
        return "R1-部分私有记录已填仍未闭环", "partial_private_records_present"
    return "R0-未开始PDF和湖北官方核验", "pending_pdf_and_hubei_official_review"


def double_review_required(row):
    return row.get("人工核验优先级", "") in {
        "R0-计划数冲突优先核PDF原页",
        "R2-疑似匹配专业名人工确认",
    }


def row_writeback_ready(row):
    if not (
        is_filled(row, "PDF原页人工核验记录")
        and is_filled(row, "湖北官方计划人工核验记录")
        and is_filled(row, "高校源差异解释记录")
        and is_filled(row, "最终字段处理建议")
    ):
        return False
    if double_review_required(row) and not (is_filled(row, "复核人A") and is_filled(row, "复核人B")):
        return False
    return True


def load_private_packet(index_row):
    csv_path = PRIVATE_PAGE_SIDE_DIR / index_row.get("私有页列CSV相对路径", "")
    html_path = PRIVATE_PAGE_SIDE_DIR / index_row.get("私有页列HTML相对路径", "")
    if not csv_path.exists():
        raise SystemExit(f"missing private page-side CSV for {index_row.get('高校源AdapterD0D1页列核验包ID')}")
    if not html_path.exists():
        raise SystemExit(f"missing private page-side HTML for {index_row.get('高校源AdapterD0D1页列核验包ID')}")
    rows, fields = read_csv(csv_path)
    missing_fields = [field for field in REQUIRED_PRIVATE_FIELDS if field not in fields]
    if missing_fields:
        raise SystemExit(
            f"private page-side CSV missing fields for {index_row.get('高校源AdapterD0D1页列核验包ID')}: {missing_fields}"
        )
    return csv_path, html_path, rows


def build_rows():
    page_rows, _ = read_csv(PAGE_SIDE_PUBLIC)
    index_rows, _ = read_csv(PRIVATE_PAGE_SIDE_INDEX)
    index_by_packet = {
        row.get("高校源AdapterD0D1页列核验包ID", ""): row for row in index_rows
    }
    private_index_sha = sha256(PRIVATE_PAGE_SIDE_INDEX)
    public_rows = []
    private_item_total = 0

    for page_row in page_rows:
        packet_id = page_row.get("高校源AdapterD0D1页列核验包ID", "")
        index_row = index_by_packet.get(packet_id)
        if not index_row:
            raise SystemExit(f"missing private page-side index row: {packet_id}")

        csv_path, html_path, private_rows = load_private_packet(index_row)
        total = len(private_rows)
        private_item_total += total
        pdf_done = sum(is_filled(row, "PDF原页人工核验记录") for row in private_rows)
        hubei_done = sum(is_filled(row, "湖北官方计划人工核验记录") for row in private_rows)
        school_done = sum(is_filled(row, "高校源差异解释记录") for row in private_rows)
        final_done = sum(is_filled(row, "最终字段处理建议") for row in private_rows)
        double_required = sum(double_review_required(row) for row in private_rows)
        double_done = sum(
            double_review_required(row) and is_filled(row, "复核人A") and is_filled(row, "复核人B")
            for row in private_rows
        )
        writeback_ready = sum(row_writeback_ready(row) for row in private_rows)
        bucket, status = progress_bucket(
            total, pdf_done, hubei_done, school_done, final_done, writeback_ready
        )

        public_rows.append({
            "高校源AdapterD0D1页列进度公开账本ID": stable_id("SSPAGEPROG", [packet_id]),
            "来源D0D1页列核验包公开账本": source_path(PAGE_SIDE_PUBLIC),
            "来源D0D1页列核验包摘要": source_path(PAGE_SIDE_SUMMARY),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "高校源Adapter D0/D1页列核验进度",
            **false_gate_values(),
            "页列执行序号": page_row.get("页列执行序号", ""),
            "来源页码": page_row.get("来源页码", ""),
            "版面列": page_row.get("版面列", ""),
            "页码版面键SHA16": page_row.get("页码版面键SHA16", "")
            or sha16([page_row.get("来源页码", ""), page_row.get("版面列", "")]),
            "高校源AdapterD0D1页列核验包ID": packet_id,
            "页列执行优先级": page_row.get("页列执行优先级", ""),
            "私有核验项数": total,
            "R0计划数冲突项数": page_row.get("R0计划数冲突项数", "0"),
            "R1OCR计划数可补项数": page_row.get("R1OCR计划数可补项数", "0"),
            "R2疑似匹配项数": page_row.get("R2疑似匹配项数", "0"),
            "R3计划数一致抽检项数": page_row.get("R3计划数一致抽检项数", "0"),
            "PDF原页记录已填项数": pdf_done,
            "PDF原页记录未填项数": total - pdf_done,
            "湖北官方计划记录已填项数": hubei_done,
            "湖北官方计划记录未填项数": total - hubei_done,
            "高校源差异解释已填项数": school_done,
            "高校源差异解释未填项数": total - school_done,
            "最终字段处理建议已填项数": final_done,
            "最终字段处理建议未填项数": total - final_done,
            "双人复核建议项数": double_required,
            "双人复核已填项数": double_done,
            "双人复核未填项数": double_required - double_done,
            "可进入字段写回评审项数": writeback_ready,
            "页列进度桶": bucket,
            "页列进度状态": status,
            "私有页列CSV证据编号": page_row.get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": sha256(csv_path),
            "私有页列HTML证据编号": page_row.get("私有页列HTML证据编号", ""),
            "私有页列HTML_SHA256": sha256(html_path),
            "私有页列索引CSV_SHA256": private_index_sha,
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网结构化源状态": "structured_school_source_candidate_not_verified",
            "字段事实写回状态": "blocked_until_required_private_records_complete",
            "公开安全策略": "公开层只保留页列进度计数、状态、证据编号和SHA；学校、专业、OCR线索、人工记录和本地材料路径不进入公开文件。",
            "下一步": "先在私有CSV逐条补PDF原页记录、湖北官方计划记录和高校源差异解释；双人复核与最终字段处理建议完成前不得写回字段事实或生成志愿建议。",
        })

    return public_rows, private_item_total, private_index_sha


def build_summary(rows, private_item_total, private_index_sha):
    return {
        "status": "issue19_school_source_adapter_d0_d1_page_side_progress_v1_not_final",
        "generated_by": "build_issue19_school_source_adapter_d0_d1_page_side_progress_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_page_side_public": source_path(PAGE_SIDE_PUBLIC),
        "source_page_side_summary": source_path(PAGE_SIDE_SUMMARY),
        "source_private_page_side_index": "local_page_side_private_index_not_public",
        "output_public_table": source_path(PUBLIC_OUTPUT),
        "row_count": len(rows),
        "private_review_item_count": private_item_total,
        "progress_bucket_counts": dict(Counter(row["页列进度桶"] for row in rows)),
        "pdf_recorded_item_count": sum(as_int(row.get("PDF原页记录已填项数")) for row in rows),
        "pdf_missing_item_count": sum(as_int(row.get("PDF原页记录未填项数")) for row in rows),
        "hubei_official_recorded_item_count": sum(as_int(row.get("湖北官方计划记录已填项数")) for row in rows),
        "hubei_official_missing_item_count": sum(as_int(row.get("湖北官方计划记录未填项数")) for row in rows),
        "school_difference_explanation_recorded_item_count": sum(
            as_int(row.get("高校源差异解释已填项数")) for row in rows
        ),
        "school_difference_explanation_missing_item_count": sum(
            as_int(row.get("高校源差异解释未填项数")) for row in rows
        ),
        "final_field_handling_recorded_item_count": sum(
            as_int(row.get("最终字段处理建议已填项数")) for row in rows
        ),
        "final_field_handling_missing_item_count": sum(
            as_int(row.get("最终字段处理建议未填项数")) for row in rows
        ),
        "double_review_suggested_item_count": sum(as_int(row.get("双人复核建议项数")) for row in rows),
        "double_review_completed_item_count": sum(as_int(row.get("双人复核已填项数")) for row in rows),
        "field_writeback_review_ready_item_count": sum(
            as_int(row.get("可进入字段写回评审项数")) for row in rows
        ),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "final_available_count": 0,
        "private_page_index_csv_sha256": private_index_sha,
        "public_boundary": "公开账本只保存进度计数、状态、证据编号和SHA；逐专业明细、OCR线索、人工记录和本地材料路径留在Git忽略私有目录。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"adapter d0/d1 page-side progress contains forbidden public tokens: {hits[:10]}")


def main():
    rows, private_item_total, private_index_sha = build_rows()
    summary = build_summary(rows, private_item_total, private_index_sha)
    assert_public_safe(rows, summary)
    write_csv(PUBLIC_OUTPUT, rows, PUBLIC_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(PUBLIC_OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")
    print(f"page-side progress rows: {len(rows)}")


if __name__ == "__main__":
    main()
