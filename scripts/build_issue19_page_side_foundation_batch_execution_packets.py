#!/usr/bin/env python3
import csv
import hashlib
import html
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_BATCHES = ROOT / "data/working/issue19-page-side-foundation-verification-batches.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
PRIVATE_OCR_LINES = ROOT / "private/ocr-runs/issue19-full-120dpi/ocr-lines.csv"
PRIVATE_RENDERED_PAGE_DIR = ROOT / "private/ocr-runs/issue19-full-120dpi/rendered-pages"
PRIVATE_TEXT_DIR = ROOT / "private/ocr-runs/issue19-full-120dpi/text"

OUTPUT = ROOT / "data/working/issue19-page-side-foundation-batch-execution-packets.csv"
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-page-side-foundation-batch-execution-packets-summary.json"
)

PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-page-side-foundation-batch-execution-packets"
)
PRIVATE_TASK_DIR = PRIVATE_OUTPUT_DIR / "tasks"
PRIVATE_HTML_DIR = PRIVATE_OUTPUT_DIR / "html"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "batch-execution-private-index.csv"
PRIVATE_MASTER_HTML = PRIVATE_OUTPUT_DIR / "index.html"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_page_side_foundation_batch_execution_packets"


FIELDS = [
    "页列底座批次执行包ID",
    "来源页列底座核验批次表",
    "来源私有OCR行表",
    "来源私有页图",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "批次总序",
    "批次ID",
    "批次名称",
    "批次页列数",
    "批次PDF页数",
    "批次专业行数",
    "批次字段任务数",
    "批次Z0页列数",
    "批次Z1页列数",
    "批次Z2页列数",
    "批次Z3页列数",
    "批次字段Q0任务数",
    "批次字段Q1任务数",
    "批次字段Q2任务数",
    "批次结构R0专业行数",
    "批次源证据X1专业行数",
    "批次源证据X2专业行数",
    "批次官方查询键碰撞行数",
    "批次教育部未匹配校名专业行数",
    "批次官网辅证线索行数",
    "批次官网计划数冲突行数",
    "批次OCR行数",
    "批次OCR低置信度行数",
    "批次页图证据编号集合SHA256",
    "批次页图SHA256集合SHA256",
    "批次页列核验行ID集合SHA256",
    "批次页码版面键集合SHA256",
    "私有批次审阅HTML证据编号",
    "私有批次审阅HTML_SHA256",
    "私有批次审阅任务CSV_SHA256",
    "私有审阅材料状态",
    "PDF原页核页完成页列数",
    "湖北官方核验完成页列数",
    "结构和官方消歧完成页列数",
    "高校辅证完成页列数",
    "批次完成状态",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "结构和官方消歧状态",
    "高校官网或招生章程辅证状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]


PRIVATE_FIELDS = [
    "批次总序",
    "批次ID",
    "批次名称",
    "页列底座核验批次行ID",
    "页列全局风险总序",
    "来源页码",
    "版面列",
    "页码版面键",
    "综合风险优先级桶",
    "页列首要核验动作",
    "包内专业行数",
    "包内字段任务数",
    "字段Q0无候选阻断任务数",
    "字段Q1有候选待人工核验任务数",
    "字段Q2待三方闭环任务数",
    "结构风险事件数",
    "官方查询键碰撞行数",
    "教育部未匹配校名专业行数",
    "官网辅证线索行数",
    "官网计划数冲突行数",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有页图相对路径",
    "私有OCR文本相对路径",
    "OCR行数",
    "OCR平均置信度",
    "OCR低置信度行数",
    "OCR行文本",
    "PDF原页核页记录",
    "湖北官方核验记录",
    "结构和官方消歧记录",
    "高校辅证记录",
    "核页人A",
    "核页人B",
    "复核备注",
]


PRIVATE_INDEX_FIELDS = [
    "批次总序",
    "批次ID",
    "批次名称",
    "私有审阅HTML相对路径",
    "私有审阅任务CSV相对路径",
    "私有审阅HTML_SHA256",
    "私有审阅任务CSV_SHA256",
    "批次页列数",
    "批次OCR行数",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha_list(values):
    normalized = "；".join(sorted({value for value in values if value}))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def as_float(value, default=0.0):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def page_no(value):
    return f"{as_int(value):03d}"


def rel_from_private_root(path):
    return str(path.relative_to(ROOT / "private"))


def html_rel_to_private(path):
    return "../../../" + rel_from_private_root(path)


def join_text_lines(lines):
    parts = []
    for line in lines:
        parts.append(
            f"{line.get('line_no', '')}. {line.get('text', '')}"
            f" [{line.get('confidence', '')}]"
        )
    return "\n".join(parts)


def ocr_stats(lines):
    confidences = [as_float(row.get("confidence")) for row in lines if row.get("confidence")]
    average = sum(confidences) / len(confidences) if confidences else 0.0
    low = sum(conf < 0.75 for conf in confidences)
    return len(lines), f"{average:.4f}", low


def counter_sum(rows, field):
    return sum(as_int(row.get(field)) for row in rows)


def build_private_csv(batch_no, batch_rows, page_manifest_by_page, ocr_by_page_side):
    output_rows = []
    for row in batch_rows:
        page = row.get("来源页码", "")
        side = row.get("版面列", "")
        manifest = page_manifest_by_page.get(page, {})
        ocr_lines = ocr_by_page_side.get((page, side), [])
        line_count, avg_confidence, low_count = ocr_stats(ocr_lines)
        image_path = PRIVATE_RENDERED_PAGE_DIR / f"page-{page_no(page)}.png"
        text_path = PRIVATE_TEXT_DIR / f"{page_no(page)}_page-{page_no(page)}.txt"
        output_rows.append({
            "批次总序": row.get("批次总序", ""),
            "批次ID": row.get("批次ID", ""),
            "批次名称": row.get("批次名称", ""),
            "页列底座核验批次行ID": row.get("页列底座核验批次行ID", ""),
            "页列全局风险总序": row.get("页列全局风险总序", ""),
            "来源页码": page,
            "版面列": side,
            "页码版面键": row.get("页码版面键", ""),
            "综合风险优先级桶": row.get("综合风险优先级桶", ""),
            "页列首要核验动作": row.get("页列首要核验动作", ""),
            "包内专业行数": row.get("包内专业行数", ""),
            "包内字段任务数": row.get("包内字段任务数", ""),
            "字段Q0无候选阻断任务数": row.get("字段Q0无候选阻断任务数", ""),
            "字段Q1有候选待人工核验任务数": row.get("字段Q1有候选待人工核验任务数", ""),
            "字段Q2待三方闭环任务数": row.get("字段Q2待三方闭环任务数", ""),
            "结构风险事件数": row.get("结构风险事件数", ""),
            "官方查询键碰撞行数": row.get("官方查询键碰撞行数", ""),
            "教育部未匹配校名专业行数": row.get("教育部未匹配校名专业行数", ""),
            "官网辅证线索行数": row.get("官网辅证线索行数", ""),
            "官网计划数冲突行数": row.get("官网计划数冲突行数", ""),
            "私有页图证据编号": manifest.get("私有页图证据编号", ""),
            "私有页图SHA256": manifest.get("私有页图SHA256", ""),
            "私有页图相对路径": rel_from_private_root(image_path),
            "私有OCR文本相对路径": rel_from_private_root(text_path),
            "OCR行数": str(line_count),
            "OCR平均置信度": avg_confidence,
            "OCR低置信度行数": str(low_count),
            "OCR行文本": join_text_lines(ocr_lines),
            "PDF原页核页记录": "",
            "湖北官方核验记录": "",
            "结构和官方消歧记录": "",
            "高校辅证记录": "",
            "核页人A": "",
            "核页人B": "",
            "复核备注": "",
        })
    csv_path = PRIVATE_TASK_DIR / f"batch-{batch_no:02d}.csv"
    write_csv(csv_path, output_rows, PRIVATE_FIELDS)
    return csv_path, output_rows


def write_private_html(batch_no, batch_rows, private_rows):
    html_path = PRIVATE_HTML_DIR / f"batch-{batch_no:02d}.html"
    private_by_key = {
        (row["来源页码"], row["版面列"]): row for row in private_rows
    }
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:24px;line-height:1.45;color:#111}",
        ".side{border:1px solid #ccc;border-radius:8px;padding:14px;margin:16px 0;break-inside:avoid}",
        ".meta{font-size:13px;color:#444;margin:4px 0}",
        "img{max-width:100%;border:1px solid #ddd;background:#fff}",
        "pre{white-space:pre-wrap;background:#f7f7f7;border:1px solid #ddd;border-radius:6px;padding:10px;font-size:13px}",
        "table{border-collapse:collapse;width:100%;font-size:13px;margin-top:10px}",
        "td,th{border:1px solid #ddd;padding:6px;vertical-align:top}",
        ".warn{color:#9a3412;font-weight:600}",
        "</style>",
        f"<title>页列底座核验第 {batch_no:02d} 批</title>",
        f"<h1>页列底座核验第 {batch_no:02d} 批</h1>",
        "<p class='warn'>私有审阅材料：包含本地页图和 OCR 行文本，不得提交公开仓库。</p>",
    ]
    for row in batch_rows:
        private_row = private_by_key[(row["来源页码"], row["版面列"])]
        image_path = PRIVATE_RENDERED_PAGE_DIR / f"page-{page_no(row['来源页码'])}.png"
        lines.extend([
            "<section class='side'>",
            f"<h2>第 {html.escape(row['来源页码'])} 页 {html.escape(row['版面列'])}</h2>",
            f"<div class='meta'>页列键：{html.escape(row.get('页码版面键',''))}；风险：{html.escape(row.get('综合风险优先级桶',''))}</div>",
            f"<div class='meta'>专业行：{html.escape(row.get('包内专业行数',''))}；字段任务：{html.escape(row.get('包内字段任务数',''))}；首要动作：{html.escape(row.get('页列首要核验动作',''))}</div>",
            f"<img src='{html.escape(html_rel_to_private(image_path))}' alt='page {html.escape(row['来源页码'])}'>",
            "<table>",
            "<tr><th>核验项</th><th>待记录</th></tr>",
            "<tr><td>PDF原页核页记录</td><td></td></tr>",
            "<tr><td>湖北官方核验记录</td><td></td></tr>",
            "<tr><td>结构和官方消歧记录</td><td></td></tr>",
            "<tr><td>高校辅证记录</td><td></td></tr>",
            "</table>",
            "<h3>本页列 OCR 行</h3>",
            f"<pre>{html.escape(private_row.get('OCR行文本',''))}</pre>",
            "</section>",
        ])
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return html_path


def write_master_html(index_rows):
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<title>第19期页列底座核验批次私有索引</title>",
        "<h1>第19期页列底座核验批次私有索引</h1>",
        "<p>私有材料，不得提交公开仓库。</p>",
        "<ol>",
    ]
    for row in index_rows:
        lines.append(
            f"<li><a href='{html.escape(row['私有审阅HTML相对路径'])}'>"
            f"{html.escape(row['批次名称'])}</a>："
            f"{html.escape(row['批次页列数'])} 个页列，"
            f"{html.escape(row['批次OCR行数'])} 行 OCR</li>"
        )
    lines.extend(["</ol>"])
    PRIVATE_MASTER_HTML.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_MASTER_HTML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_rows():
    source_rows = read_csv(SOURCE_BATCHES)
    page_manifest_rows = read_csv(PAGE_MANIFEST)
    ocr_rows = read_csv(PRIVATE_OCR_LINES)
    page_manifest_by_page = {
        row.get("PDF页码", ""): row for row in page_manifest_rows
    }
    ocr_by_page_side = defaultdict(list)
    for row in ocr_rows:
        side = row.get("table_band", "")
        if side in {"left", "right"}:
            ocr_by_page_side[(row.get("page", ""), side)].append(row)
    for rows in ocr_by_page_side.values():
        rows.sort(key=lambda row: as_int(row.get("line_no")))

    batches = defaultdict(list)
    for row in source_rows:
        batches[as_int(row.get("批次总序"))].append(row)

    output_rows = []
    private_index_rows = []
    for batch_no in sorted(batches):
        batch_rows = batches[batch_no]
        private_csv, private_rows = build_private_csv(
            batch_no, batch_rows, page_manifest_by_page, ocr_by_page_side
        )
        private_html = write_private_html(batch_no, batch_rows, private_rows)
        csv_sha = sha256(private_csv)
        html_sha = sha256(private_html)
        batch_id = batch_rows[0].get("批次ID", "")
        packet_id = stable_id("PSFOUNDATIONEXECPACK", [batch_id, batch_no])
        page_count = len({row.get("来源页码", "") for row in batch_rows})
        ocr_line_count = sum(as_int(row["OCR行数"]) for row in private_rows)
        low_conf_count = sum(as_int(row["OCR低置信度行数"]) for row in private_rows)
        page_manifest_values = [
            page_manifest_by_page.get(row.get("来源页码", ""), {})
            for row in batch_rows
        ]
        output_rows.append({
            "页列底座批次执行包ID": packet_id,
            "来源页列底座核验批次表": "data/working/issue19-page-side-foundation-verification-batches.csv",
            "来源私有OCR行表": "private_ocr_lines_not_public",
            "来源私有页图": "private_rendered_pages_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列批次",
            "任务粒度": "页列底座核验批次×私有审阅材料",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "批次总序": str(batch_no),
            "批次ID": batch_id,
            "批次名称": batch_rows[0].get("批次名称", ""),
            "批次页列数": str(len(batch_rows)),
            "批次PDF页数": str(page_count),
            "批次专业行数": str(counter_sum(batch_rows, "包内专业行数")),
            "批次字段任务数": str(counter_sum(batch_rows, "包内字段任务数")),
            "批次Z0页列数": batch_rows[0].get("批次Z0页列数", ""),
            "批次Z1页列数": batch_rows[0].get("批次Z1页列数", ""),
            "批次Z2页列数": batch_rows[0].get("批次Z2页列数", ""),
            "批次Z3页列数": batch_rows[0].get("批次Z3页列数", ""),
            "批次字段Q0任务数": str(counter_sum(batch_rows, "字段Q0无候选阻断任务数")),
            "批次字段Q1任务数": str(counter_sum(batch_rows, "字段Q1有候选待人工核验任务数")),
            "批次字段Q2任务数": str(counter_sum(batch_rows, "字段Q2待三方闭环任务数")),
            "批次结构R0专业行数": batch_rows[0].get("批次结构R0专业行数", ""),
            "批次源证据X1专业行数": batch_rows[0].get("批次源证据X1专业行数", ""),
            "批次源证据X2专业行数": batch_rows[0].get("批次源证据X2专业行数", ""),
            "批次官方查询键碰撞行数": batch_rows[0].get("批次官方查询键碰撞行数", ""),
            "批次教育部未匹配校名专业行数": str(counter_sum(batch_rows, "教育部未匹配校名专业行数")),
            "批次官网辅证线索行数": str(counter_sum(batch_rows, "官网辅证线索行数")),
            "批次官网计划数冲突行数": str(counter_sum(batch_rows, "官网计划数冲突行数")),
            "批次OCR行数": str(ocr_line_count),
            "批次OCR低置信度行数": str(low_conf_count),
            "批次页图证据编号集合SHA256": sha_list(
                row.get("私有页图证据编号", "") for row in page_manifest_values
            ),
            "批次页图SHA256集合SHA256": sha_list(
                row.get("私有页图SHA256", "") for row in page_manifest_values
            ),
            "批次页列核验行ID集合SHA256": sha_list(
                row.get("页列底座核验批次行ID", "") for row in batch_rows
            ),
            "批次页码版面键集合SHA256": sha_list(
                row.get("页码版面键", "") for row in batch_rows
            ),
            "私有批次审阅HTML证据编号": f"ps-foundation-batch-{batch_no:02d}-html",
            "私有批次审阅HTML_SHA256": html_sha,
            "私有批次审阅任务CSV_SHA256": csv_sha,
            "私有审阅材料状态": "private_batch_review_assets_generated",
            "PDF原页核页完成页列数": "0",
            "湖北官方核验完成页列数": "0",
            "结构和官方消歧完成页列数": "0",
            "高校辅证完成页列数": "0",
            "批次完成状态": "R0-未开始页列底座核验",
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "结构和官方消歧状态": "pending_structure_and_official_key_review",
            "高校官网或招生章程辅证状态": "pending_if_school_clue_present",
            "字段事实写回状态": "blocked_until_batch_evidence_closed",
            "公开安全策略": (
                "公开表只保存批次计数、私有材料证据编号和SHA、状态和非最终门禁；"
                "不公开识别行内容、页图路径、学校专业明细、字段读数或人工记录。"
            ),
            "下一步": (
                f"{batch_rows[0].get('批次名称', '')} 已生成私有核页材料；"
                "先核PDF原页和结构边界，再核湖北官方侧与必要高校辅证。"
            ),
        })
        private_index_rows.append({
            "批次总序": str(batch_no),
            "批次ID": batch_id,
            "批次名称": batch_rows[0].get("批次名称", ""),
            "私有审阅HTML相对路径": str(private_html.relative_to(PRIVATE_OUTPUT_DIR)),
            "私有审阅任务CSV相对路径": str(private_csv.relative_to(PRIVATE_OUTPUT_DIR)),
            "私有审阅HTML_SHA256": html_sha,
            "私有审阅任务CSV_SHA256": csv_sha,
            "批次页列数": str(len(batch_rows)),
            "批次OCR行数": str(ocr_line_count),
        })

    write_csv(PRIVATE_INDEX, private_index_rows, PRIVATE_INDEX_FIELDS)
    write_master_html(private_index_rows)
    return output_rows, private_index_rows


def main():
    rows, private_index_rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    summary = {
        "status": "issue19_page_side_foundation_batch_execution_packets_not_final",
        "generated_by": "build_issue19_page_side_foundation_batch_execution_packets.py",
        "source_page_side_foundation_verification_batches": "data/working/issue19-page-side-foundation-verification-batches.csv",
        "output_table": "data/working/issue19-page-side-foundation-batch-execution-packets.csv",
        "row_count": len(rows),
        "batch_count": len({row["批次ID"] for row in rows}),
        "source_page_side_count": sum(as_int(row["批次页列数"]) for row in rows),
        "source_major_line_count": sum(as_int(row["批次专业行数"]) for row in rows),
        "source_field_task_count": sum(as_int(row["批次字段任务数"]) for row in rows),
        "private_batch_review_asset_count": len(private_index_rows),
        "private_master_html_sha256": sha256(PRIVATE_MASTER_HTML),
        "private_index_csv_sha256": sha256(PRIVATE_INDEX),
        "batch_status_counts": dict(Counter(row["批次完成状态"] for row in rows)),
        "private_material_status_counts": dict(Counter(row["私有审阅材料状态"] for row in rows)),
        "pdf_review_completed_page_side_count": sum(as_int(row["PDF原页核页完成页列数"]) for row in rows),
        "hubei_official_completed_page_side_count": sum(as_int(row["湖北官方核验完成页列数"]) for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "safety_note": (
            "公开摘要只保存批次计数、私有材料SHA和非最终门禁；"
            "私有HTML/CSV在private目录，不提交公开仓库。"
        ),
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出私有批次材料：{PRIVATE_OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
