#!/usr/bin/env python3
import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

PAGE_SIDE_PROGRESS = (
    WORKING / "issue19-school-source-adapter-d0-d1-page-side-progress-v1-public-ledger.csv"
)
PAGE_SIDE_PROGRESS_SUMMARY = (
    WORKING / "issue19-school-source-adapter-d0-d1-page-side-progress-v1-summary.json"
)
PAGE_MANIFEST = WORKING / "issue19-page-manifest.csv"
PRIVATE_PAGE_SIDE_DIR = (
    ROOT / "private/review-assets/issue19-school-source-adapter-d0-d1-page-side-packets-v1"
)
PRIVATE_PAGE_SIDE_INDEX = PRIVATE_PAGE_SIDE_DIR / "page-side-packets-private-index.csv"
RENDERED_PAGE_DIR = ROOT / "private/ocr-runs/issue19-full-120dpi/rendered-pages"

PRIVATE_OUTPUT_DIR = (
    ROOT
    / "private/review-assets/issue19-school-source-adapter-d0-d1-page-side-pdf-visual-audit-v1"
)
PRIVATE_CROP_DIR = PRIVATE_OUTPUT_DIR / "page-side-crops"
PRIVATE_HTML_DIR = PRIVATE_OUTPUT_DIR / "html"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "pdf-visual-private-index.csv"
PRIVATE_MASTER_HTML = PRIVATE_OUTPUT_DIR / "index.html"

PUBLIC_OUTPUT = (
    WORKING
    / "issue19-school-source-adapter-d0-d1-page-side-pdf-visual-audit-v1-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    WORKING / "issue19-school-source-adapter-d0-d1-page-side-pdf-visual-audit-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_adapter_d0_d1_page_side_pdf_visual_audit_v1"
GENERATED_AT = "2026-06-29"
RENDER_DPI = 120

SIDE_CROP_BBOX = {
    "left": (0.045, 0.545, 0.030, 0.970),
    "right": (0.455, 0.955, 0.030, 0.970),
}

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
    "高校源AdapterD0D1页列PDF视觉核验审计ID",
    "来源D0D1页列进度公开账本",
    "来源D0D1页列进度摘要",
    "来源页级manifest",
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
    "高校源AdapterD0D1页列进度公开账本ID",
    "页列执行优先级",
    "私有核验项数",
    "R0计划数冲突项数",
    "R1OCR计划数可补项数",
    "R2疑似匹配项数",
    "R3计划数一致抽检项数",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有页图大小字节",
    "源页图宽度px",
    "源页图高度px",
    "OCR识别行数",
    "OCR平均置信度",
    "私有栏图证据编号",
    "私有栏图SHA256",
    "私有栏图大小字节",
    "栏图宽度px",
    "栏图高度px",
    "栏图bbox归一化",
    "栏图bbox像素",
    "栏图生成参数摘要",
    "栏图生成状态",
    "私有审阅HTML证据编号",
    "私有审阅HTML_SHA256",
    "私有视觉索引CSV_SHA256",
    "私有视觉总览HTML_SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页列HTML证据编号",
    "私有页列HTML_SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_INDEX_FIELDS = [
    "高校源AdapterD0D1页列PDF视觉核验审计ID",
    "页列执行序号",
    "来源页码",
    "版面列",
    "高校源AdapterD0D1页列核验包ID",
    "高校源AdapterD0D1页列进度公开账本ID",
    "页列执行优先级",
    "私有核验项数",
    "私有源页图相对路径",
    "私有页图SHA256",
    "私有栏图相对路径",
    "私有栏图SHA256",
    "私有审阅HTML相对路径",
    "私有审阅HTML_SHA256",
    "私有页列CSV相对路径",
    "私有页列CSV_SHA256",
    "私有页列HTML相对路径",
    "私有页列HTML_SHA256",
    "栏图bbox像素",
    "栏图bbox归一化",
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


def stable_id(prefix, parts):
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def source_path(path):
    return str(path.relative_to(ROOT))


def private_output_path(path):
    return str(path.relative_to(PRIVATE_OUTPUT_DIR))


def private_root_path(path):
    return str(path.relative_to(ROOT / "private"))


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def as_int(value):
    try:
        return int(str(value).strip() or "0")
    except ValueError:
        return 0


def bbox_for_side(side, width, height):
    x1, x2, y1, y2 = SIDE_CROP_BBOX.get(side, SIDE_CROP_BBOX["left"])
    left = max(0, min(width - 1, int(round(x1 * width))))
    right = max(left + 1, min(width, int(round(x2 * width))))
    top = max(0, min(height - 1, int(round(y1 * height))))
    bottom = max(top + 1, min(height, int(round(y2 * height))))
    return (left, top, right, bottom), (x1, x2, y1, y2)


def fmt_bbox_px(bbox):
    left, top, right, bottom = bbox
    return f"x={left}-{right};y={top}-{bottom}"


def fmt_bbox_norm(bbox):
    x1, x2, y1, y2 = bbox
    return f"x={x1:.6f}-{x2:.6f};y_top_origin={y1:.6f}-{y2:.6f}"


def load_private_page_rows(index_row):
    csv_path = PRIVATE_PAGE_SIDE_DIR / index_row.get("私有页列CSV相对路径", "")
    html_path = PRIVATE_PAGE_SIDE_DIR / index_row.get("私有页列HTML相对路径", "")
    if not csv_path.exists():
        raise SystemExit(f"missing private page-side csv: {csv_path}")
    if not html_path.exists():
        raise SystemExit(f"missing private page-side html: {html_path}")
    rows, _ = read_csv(csv_path)
    return csv_path, html_path, rows


def private_review_html(row, page_image_rel, crop_rel, private_csv_rel, private_page_html_rel, private_rows):
    audit_id = row["高校源AdapterD0D1页列PDF视觉核验审计ID"]
    path = PRIVATE_HTML_DIR / f"{audit_id}.html"
    display_fields = [
        "人工核验优先级",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业代号OCR",
        "专业名称及备注OCR",
        "OCR专业计划数候选",
        "最佳高校源计划数",
        "最佳高校源专业名称",
        "建议核验动作",
        "PDF原页人工核验记录",
        "湖北官方计划人工核验记录",
        "高校源差异解释记录",
        "最终字段处理建议",
        "复核人A",
        "复核人B",
    ]
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:24px;line-height:1.45;color:#111}",
        "img{max-width:100%;border:1px solid #ddd;background:white;margin:8px 0}",
        "table{border-collapse:collapse;width:100%;font-size:12px;margin-top:12px}",
        "th,td{border:1px solid #d4d4d4;padding:6px;vertical-align:top}",
        "th{background:#f5f5f5;position:sticky;top:0}",
        ".warn{color:#9a3412;font-weight:600}",
        ".meta{color:#444;font-size:13px}",
        "</style>",
        f"<title>{html.escape(audit_id)}</title>",
        f"<h1>{html.escape(audit_id)}</h1>",
        "<p class='warn'>私有视觉核验材料：包含原页图、栏图、学校和专业线索，只能留在本地 private 目录。</p>",
        (
            "<p class='meta'>第 "
            f"{html.escape(row['来源页码'])} 页 / {html.escape(row['版面列'])}；"
            f"{html.escape(row['页列执行优先级'])}；"
            f"私有核验项 {html.escape(row['私有核验项数'])} 条。</p>"
        ),
        f"<p class='meta'>私有页列CSV：<a href='../{html.escape(private_csv_rel)}'>打开CSV</a>；"
        f"原页列包HTML：<a href='../{html.escape(private_page_html_rel)}'>打开HTML</a></p>",
        "<h2>栏图</h2>",
        f"<img src='{html.escape(crop_rel)}' alt='page side crop'>",
        "<h2>整页图</h2>",
        f"<img src='{html.escape(page_image_rel)}' alt='source page'>",
        "<h2>私有核验项</h2>",
        "<table><thead><tr>",
    ]
    for field in display_fields:
        lines.append(f"<th>{html.escape(field)}</th>")
    lines.append("</tr></thead><tbody>")
    for private_row in private_rows:
        lines.append("<tr>")
        for field in display_fields:
            lines.append(f"<td>{html.escape(clean(private_row.get(field, '')))}</td>")
        lines.append("</tr>")
    lines.append("</tbody></table>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_master_html(index_rows):
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:24px;color:#111}",
        "table{border-collapse:collapse;width:100%;font-size:13px}",
        "th,td{border:1px solid #d4d4d4;padding:6px;text-align:left;vertical-align:top}",
        "th{background:#f5f5f5}",
        ".warn{color:#9a3412;font-weight:600}",
        "</style>",
        "<title>D0/D1页列PDF视觉核验索引</title>",
        "<h1>D0/D1页列PDF视觉核验索引</h1>",
        "<p class='warn'>本索引仅在本地 private 目录保存，不进入公开仓库。</p>",
        "<table><thead><tr><th>序号</th><th>页码</th><th>版面列</th><th>优先级</th><th>明细数</th><th>HTML</th><th>栏图</th></tr></thead><tbody>",
    ]
    for row in index_rows:
        lines.append(
            "<tr>"
            f"<td>{html.escape(clean(row.get('页列执行序号', '')))}</td>"
            f"<td>{html.escape(clean(row.get('来源页码', '')))}</td>"
            f"<td>{html.escape(clean(row.get('版面列', '')))}</td>"
            f"<td>{html.escape(clean(row.get('页列执行优先级', '')))}</td>"
            f"<td>{html.escape(clean(row.get('私有核验项数', '')))}</td>"
            f"<td><a href='{html.escape(row.get('私有审阅HTML相对路径', ''))}'>HTML</a></td>"
            f"<td><a href='{html.escape(row.get('私有栏图相对路径', ''))}'>栏图</a></td>"
            "</tr>"
        )
    lines.append("</tbody></table>")
    PRIVATE_MASTER_HTML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_rows():
    progress_rows, _ = read_csv(PAGE_SIDE_PROGRESS)
    page_manifest_rows, _ = read_csv(PAGE_MANIFEST)
    private_index_rows, _ = read_csv(PRIVATE_PAGE_SIDE_INDEX)
    manifest_by_page = {row.get("PDF页码", ""): row for row in page_manifest_rows}
    private_index_by_packet = {
        row.get("高校源AdapterD0D1页列核验包ID", ""): row for row in private_index_rows
    }

    public_rows = []
    private_index_output_rows = []
    page_image_cache = {}
    for progress_row in progress_rows:
        page = progress_row.get("来源页码", "")
        side = progress_row.get("版面列", "")
        packet_id = progress_row.get("高校源AdapterD0D1页列核验包ID", "")
        manifest_row = manifest_by_page.get(page)
        private_packet_index = private_index_by_packet.get(packet_id)
        if not manifest_row:
            raise SystemExit(f"missing page manifest row: {page}")
        if not private_packet_index:
            raise SystemExit(f"missing private packet index row: {packet_id}")

        page_image_path = RENDERED_PAGE_DIR / f"page-{as_int(page):03d}.png"
        if not page_image_path.exists():
            raise SystemExit(f"missing rendered page image: {page_image_path}")
        page_image_sha = sha256(page_image_path)
        if page_image_sha != manifest_row.get("私有页图SHA256", ""):
            raise SystemExit(f"page image SHA mismatch for page {page}")
        if page not in page_image_cache:
            page_image_cache[page] = Image.open(page_image_path).convert("RGB")
        image = page_image_cache[page]
        width, height = image.size
        bbox_px, bbox_norm = bbox_for_side(side, width, height)
        crop = image.crop(bbox_px)

        audit_id = stable_id("SSPAGEVIS", [SOURCE_PDF_SHA256, packet_id, page, side])
        crop_path = PRIVATE_CROP_DIR / f"{audit_id}.png"
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        crop.save(crop_path)
        crop_sha = sha256(crop_path)

        private_csv_path, private_page_html_path, private_page_rows = load_private_page_rows(
            private_packet_index
        )
        html_path = private_review_html(
            {
                **progress_row,
                "高校源AdapterD0D1页列PDF视觉核验审计ID": audit_id,
            },
            page_image_rel=(
                "../../../ocr-runs/issue19-full-120dpi/rendered-pages/"
                f"page-{as_int(page):03d}.png"
            ),
            crop_rel=f"../page-side-crops/{audit_id}.png",
            private_csv_rel=(
                "../../issue19-school-source-adapter-d0-d1-page-side-packets-v1/"
                f"{private_packet_index.get('私有页列CSV相对路径', '')}"
            ),
            private_page_html_rel=(
                "../../issue19-school-source-adapter-d0-d1-page-side-packets-v1/"
                f"{private_packet_index.get('私有页列HTML相对路径', '')}"
            ),
            private_rows=private_page_rows,
        )
        html_sha = sha256(html_path)

        public_row = {
            "高校源AdapterD0D1页列PDF视觉核验审计ID": audit_id,
            "来源D0D1页列进度公开账本": source_path(PAGE_SIDE_PROGRESS),
            "来源D0D1页列进度摘要": source_path(PAGE_SIDE_PROGRESS_SUMMARY),
            "来源页级manifest": source_path(PAGE_MANIFEST),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "高校源Adapter D0/D1页列PDF视觉核验素材",
            **false_gate_values(),
            "页列执行序号": progress_row.get("页列执行序号", ""),
            "来源页码": page,
            "版面列": side,
            "页码版面键SHA16": progress_row.get("页码版面键SHA16", ""),
            "高校源AdapterD0D1页列核验包ID": packet_id,
            "高校源AdapterD0D1页列进度公开账本ID": progress_row.get(
                "高校源AdapterD0D1页列进度公开账本ID", ""
            ),
            "页列执行优先级": progress_row.get("页列执行优先级", ""),
            "私有核验项数": progress_row.get("私有核验项数", ""),
            "R0计划数冲突项数": progress_row.get("R0计划数冲突项数", "0"),
            "R1OCR计划数可补项数": progress_row.get("R1OCR计划数可补项数", "0"),
            "R2疑似匹配项数": progress_row.get("R2疑似匹配项数", "0"),
            "R3计划数一致抽检项数": progress_row.get("R3计划数一致抽检项数", "0"),
            "私有页图证据编号": manifest_row.get("私有页图证据编号", ""),
            "私有页图SHA256": page_image_sha,
            "私有页图大小字节": page_image_path.stat().st_size,
            "源页图宽度px": width,
            "源页图高度px": height,
            "OCR识别行数": manifest_row.get("OCR识别行数", ""),
            "OCR平均置信度": manifest_row.get("OCR平均置信度", ""),
            "私有栏图证据编号": f"local_d0_d1_page_side_visual_crop_{progress_row.get('页列执行序号', '').zfill(3)}",
            "私有栏图SHA256": crop_sha,
            "私有栏图大小字节": crop_path.stat().st_size,
            "栏图宽度px": bbox_px[2] - bbox_px[0],
            "栏图高度px": bbox_px[3] - bbox_px[1],
            "栏图bbox归一化": fmt_bbox_norm(bbox_norm),
            "栏图bbox像素": fmt_bbox_px(bbox_px),
            "栏图生成参数摘要": f"render_dpi={RENDER_DPI};crop=side_full_height;coord_y_origin=top;side={side}",
            "栏图生成状态": "local_page_side_crop_generated_hash_recorded",
            "私有审阅HTML证据编号": f"local_d0_d1_page_side_visual_html_{progress_row.get('页列执行序号', '').zfill(3)}",
            "私有审阅HTML_SHA256": html_sha,
            "私有视觉索引CSV_SHA256": "filled_after_index_write",
            "私有视觉总览HTML_SHA256": "filled_after_index_write",
            "私有页列CSV证据编号": progress_row.get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": sha256(private_csv_path),
            "私有页列HTML证据编号": progress_row.get("私有页列HTML证据编号", ""),
            "私有页列HTML_SHA256": sha256(private_page_html_path),
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网结构化源状态": "structured_school_source_candidate_not_verified",
            "字段事实写回状态": "blocked_until_required_private_records_complete",
            "公开安全策略": "公开层只保存页列、计数、尺寸、证据编号和SHA；栏图、整页图、学校专业线索、OCR线索、人工记录和本地材料路径均留在本地。",
            "下一步": "人工打开本地视觉HTML或栏图，对照第19期原页、湖北官方侧和高校辅证逐条填写私有核验记录；未闭环前不得写回字段事实或生成志愿建议。",
        }
        public_rows.append(public_row)
        private_index_output_rows.append({
            "高校源AdapterD0D1页列PDF视觉核验审计ID": audit_id,
            "页列执行序号": progress_row.get("页列执行序号", ""),
            "来源页码": page,
            "版面列": side,
            "高校源AdapterD0D1页列核验包ID": packet_id,
            "高校源AdapterD0D1页列进度公开账本ID": progress_row.get(
                "高校源AdapterD0D1页列进度公开账本ID", ""
            ),
            "页列执行优先级": progress_row.get("页列执行优先级", ""),
            "私有核验项数": progress_row.get("私有核验项数", ""),
            "私有源页图相对路径": private_root_path(page_image_path),
            "私有页图SHA256": page_image_sha,
            "私有栏图相对路径": private_output_path(crop_path),
            "私有栏图SHA256": crop_sha,
            "私有审阅HTML相对路径": private_output_path(html_path),
            "私有审阅HTML_SHA256": html_sha,
            "私有页列CSV相对路径": private_root_path(private_csv_path),
            "私有页列CSV_SHA256": sha256(private_csv_path),
            "私有页列HTML相对路径": private_root_path(private_page_html_path),
            "私有页列HTML_SHA256": sha256(private_page_html_path),
            "栏图bbox像素": fmt_bbox_px(bbox_px),
            "栏图bbox归一化": fmt_bbox_norm(bbox_norm),
        })

    write_csv(PRIVATE_INDEX, private_index_output_rows, PRIVATE_INDEX_FIELDS)
    write_master_html(private_index_output_rows)
    private_index_sha = sha256(PRIVATE_INDEX)
    private_master_sha = sha256(PRIVATE_MASTER_HTML)
    for row in public_rows:
        row["私有视觉索引CSV_SHA256"] = private_index_sha
        row["私有视觉总览HTML_SHA256"] = private_master_sha
    return public_rows, private_index_output_rows, private_index_sha, private_master_sha


def build_summary(public_rows, private_index_rows, private_index_sha, private_master_sha):
    return {
        "status": "issue19_school_source_adapter_d0_d1_page_side_pdf_visual_audit_v1_not_final",
        "generated_by": "build_issue19_school_source_adapter_d0_d1_page_side_pdf_visual_audit_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_page_side_progress_public": source_path(PAGE_SIDE_PROGRESS),
        "source_page_side_progress_summary": source_path(PAGE_SIDE_PROGRESS_SUMMARY),
        "source_page_manifest": source_path(PAGE_MANIFEST),
        "output_public_table": source_path(PUBLIC_OUTPUT),
        "row_count": len(public_rows),
        "private_visual_index_row_count": len(private_index_rows),
        "unique_pdf_page_count": len({row["来源页码"] for row in public_rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in public_rows}),
        "private_page_side_crop_count": len(public_rows),
        "private_review_html_count": len(public_rows),
        "private_review_item_count": sum(as_int(row.get("私有核验项数")) for row in public_rows),
        "page_priority_counts": dict(Counter(row["页列执行优先级"] for row in public_rows)),
        "side_counts": dict(Counter(row["版面列"] for row in public_rows)),
        "crop_status_counts": dict(Counter(row["栏图生成状态"] for row in public_rows)),
        "source_page_image_hash_count": len({row["私有页图SHA256"] for row in public_rows}),
        "page_side_crop_hash_count": len({row["私有栏图SHA256"] for row in public_rows}),
        "review_html_hash_count": len({row["私有审阅HTML_SHA256"] for row in public_rows}),
        "private_visual_index_csv_sha256": private_index_sha,
        "private_master_html_sha256": private_master_sha,
        "pdf_manual_review_pending_count": len(public_rows),
        "hubei_official_review_pending_count": len(public_rows),
        "field_writeback_ready_count": 0,
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "公开表只保存页列、计数、尺寸、证据编号和SHA；栏图、整页图、学校专业线索、OCR线索、人工记录和本地材料路径留在Git忽略私有目录。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"adapter d0/d1 visual audit contains forbidden public tokens: {hits[:10]}")


def main():
    public_rows, private_index_rows, private_index_sha, private_master_sha = build_rows()
    summary = build_summary(public_rows, private_index_rows, private_index_sha, private_master_sha)
    assert_public_safe(public_rows, summary)
    write_csv(PUBLIC_OUTPUT, public_rows, PUBLIC_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(PUBLIC_OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")
    print(f"private visual packets: {len(private_index_rows)}")


if __name__ == "__main__":
    main()
