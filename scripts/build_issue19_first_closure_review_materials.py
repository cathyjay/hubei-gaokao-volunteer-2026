#!/usr/bin/env python3
import csv
import hashlib
import html
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIRST_DETAIL = ROOT / "data/working/issue19-stable-foundation-first-closure-detail-packet.csv"
FIRST_PAGE_SIDE = ROOT / "data/working/issue19-stable-foundation-first-closure-page-side-packet.csv"
PAGE_PROGRESS = ROOT / "data/working/issue19-page-side-foundation-review-progress-public-ledger.csv"
FIELD_CLUE = ROOT / "data/working/issue19-page-side-foundation-field-clue-public-audit.csv"
OVERLAY_PUBLIC = ROOT / "data/working/issue19-page-side-foundation-human-review-overlay-public-ledger.csv"
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"

PRIVATE_OCR_LINES = ROOT / "private/ocr-runs/issue19-full-120dpi/ocr-lines.csv"
PRIVATE_RENDERED_PAGE_DIR = ROOT / "private/ocr-runs/issue19-full-120dpi/rendered-pages"
PRIVATE_TEXT_DIR = ROOT / "private/ocr-runs/issue19-full-120dpi/text"
PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-stable-foundation-first-closure-review"
)
PRIVATE_PAGE_SIDE_DIR = PRIVATE_OUTPUT_DIR / "page-sides"
PRIVATE_HTML_DIR = PRIVATE_OUTPUT_DIR / "html"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "first-closure-review-private-index.csv"
PRIVATE_MASTER_HTML = PRIVATE_OUTPUT_DIR / "index.html"

PUBLIC_OUTPUT = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-review-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_review_public_ledger"

PUBLIC_FIELDS = [
    "稳定基座第一闭环复核公开账本ID",
    "来源第一闭环明细包",
    "来源第一闭环页列包",
    "来源页列底座公开核页进度账本",
    "来源页列底座字段线索公开审计",
    "来源页列底座人工复核Overlay公开账本",
    "来源湖北官方公开入口状态快照",
    "来源第一闭环私有复核材料",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "稳定基座第一闭环页列包ID",
    "页列底座核验批次行ID",
    "页列底座核页进度公开账本ID",
    "页列底座字段线索公开审计ID",
    "页列底座Overlay公开账本ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "第一闭环页列优先级",
    "第一闭环页列执行状态",
    "第一闭环明细任务数",
    "自动官网辅证任务数",
    "P0人工字段任务数",
    "C0冲突任务数",
    "C1官网补缺任务数",
    "C7官网未匹配任务数",
    "EXEC01冲突异常字段数",
    "EXEC02计划数偏大字段数",
    "EXEC03高校辅证字段数",
    "涉及专业行数",
    "涉及字段任务数",
    "是否含计划数冲突或补缺",
    "是否需要双人复核",
    "批次总序",
    "批次ID",
    "批次名称",
    "批内页列序号",
    "页列全局风险总序",
    "综合风险优先级桶",
    "页列首要核验动作",
    "全量底座包内专业行数",
    "全量底座包内字段任务数",
    "OCR行数",
    "OCR低置信度行数",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "私有第一闭环页列CSV证据编号",
    "私有第一闭环页列CSV_SHA256",
    "私有第一闭环页列HTML证据编号",
    "私有第一闭环页列HTML_SHA256",
    "私有第一闭环材料状态",
    "Overlay进度桶",
    "PDF原页记录已填字段数",
    "湖北官方记录已填字段数",
    "高校辅证记录已填字段数",
    "字段最终记录已填字段数",
    "三方一致性可评估字段数",
    "首轮复核已填字段数",
    "次轮复核已填字段数",
    "复查结论已填字段数",
    "第一闭环PDF原页完成任务数",
    "第一闭环湖北官方完成任务数",
    "第一闭环高校辅证完成任务数",
    "第一闭环字段事实写回可进入任务数",
    "官方公开计划页可定稿",
    "数智平台可定稿",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_DETAIL_FIELDS = [
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环页列包ID",
    "页列底座核验批次行ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "任务来源类型",
    "第一闭环批次",
    "第一闭环纳入原因",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "字段名",
    "官网辅证自动动作",
    "执行批次",
    "OCR专业计划数候选",
    "最佳官网计划数",
    "OCR学费候选",
    "最佳官网学费",
    "OCR再选科目候选",
    "最佳官网选科",
    "计划数核验状态",
    "差异字段集合",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图bbox归一化",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "私有页图相对路径",
    "私有OCR文本相对路径",
    "OCR行文本",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "一审记录",
    "二审记录",
    "复核结论",
    "复核备注",
]

PRIVATE_INDEX_FIELDS = [
    "来源页码",
    "版面列",
    "页码版面键",
    "第一闭环页列优先级",
    "稳定基座第一闭环页列包ID",
    "页列底座核验批次行ID",
    "私有第一闭环页列CSV相对路径",
    "私有第一闭环页列HTML相对路径",
    "私有第一闭环页列CSV_SHA256",
    "私有第一闭环页列HTML_SHA256",
    "第一闭环明细任务数",
    "OCR行数",
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
    "身份证",
    "准考证",
    "报名号",
    "序列号",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
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


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def false_gate_values():
    return {
        "最终可用": "false",
        "可进入下一阶段": "false",
        "可否进入最终志愿方案": "false",
        "是否允许作为志愿推荐依据": "false",
        "是否允许自动写回主表": "false",
        "是否允许官网证据替代湖北官方计划": "false",
        "是否允许生成学校专业建议": "false",
        "是否允许写回字段事实": "false",
    }


def join_ocr_lines(lines):
    return "\n".join(
        f"{row.get('line_no', '')}. {row.get('text', '')} [{row.get('confidence', '')}]"
        for row in lines
    )


def ocr_stats(lines):
    confidences = [as_float(row.get("confidence")) for row in lines if row.get("confidence")]
    low_count = sum(conf < 0.75 for conf in confidences)
    return len(lines), low_count


def read_ocr_by_page_side():
    if not PRIVATE_OCR_LINES.exists():
        return defaultdict(list)
    result = defaultdict(list)
    for row in read_csv(PRIVATE_OCR_LINES):
        side = row.get("table_band", "")
        if side in {"left", "right"}:
            result[(row.get("page", ""), side)].append(row)
    for rows in result.values():
        rows.sort(key=lambda row: as_int(row.get("line_no")))
    return result


def private_detail_row(detail, page_side, foundation, ocr_text):
    page = page_side.get("来源页码", "")
    image_path = PRIVATE_RENDERED_PAGE_DIR / f"page-{page_no(page)}.png"
    text_path = PRIVATE_TEXT_DIR / f"{page_no(page)}_page-{page_no(page)}.txt"
    return {
        "稳定基座第一闭环明细任务ID": detail.get("稳定基座第一闭环明细任务ID", ""),
        "稳定基座第一闭环页列包ID": page_side.get("稳定基座第一闭环页列包ID", ""),
        "页列底座核验批次行ID": foundation.get("页列底座核验批次行ID", ""),
        "来源页码": page,
        "版面列": page_side.get("版面列", ""),
        "页码版面键": page_side.get("页码版面键", ""),
        "任务来源类型": detail.get("任务来源类型", ""),
        "第一闭环批次": detail.get("第一闭环批次", ""),
        "第一闭环纳入原因": detail.get("第一闭环纳入原因", ""),
        "专业行ID": detail.get("专业行ID", ""),
        "专业组出现ID": detail.get("专业组出现ID", ""),
        "院校代码": detail.get("院校代码", ""),
        "院校名称OCR": detail.get("院校名称OCR", ""),
        "院校专业组代码OCR规范化": detail.get("院校专业组代码OCR规范化", ""),
        "专业组内专业序号": detail.get("专业组内专业序号", ""),
        "专业代号OCR": detail.get("专业代号OCR", ""),
        "专业名称及备注短摘": detail.get("专业名称及备注短摘", ""),
        "字段名": detail.get("字段名", ""),
        "官网辅证自动动作": detail.get("官网辅证自动动作", ""),
        "执行批次": detail.get("执行批次", ""),
        "OCR专业计划数候选": detail.get("OCR专业计划数候选", ""),
        "最佳官网计划数": detail.get("最佳官网计划数", ""),
        "OCR学费候选": detail.get("OCR学费候选", ""),
        "最佳官网学费": detail.get("最佳官网学费", ""),
        "OCR再选科目候选": detail.get("OCR再选科目候选", ""),
        "最佳官网选科": detail.get("最佳官网选科", ""),
        "计划数核验状态": detail.get("计划数核验状态", ""),
        "差异字段集合": detail.get("差异字段集合", ""),
        "裁图证据编号": detail.get("裁图证据编号", ""),
        "裁图文件SHA256": detail.get("裁图文件SHA256", ""),
        "裁图bbox归一化": detail.get("裁图bbox归一化", ""),
        "PDF原页核页状态": detail.get("PDF原页核页状态", ""),
        "湖北官方系统或省招办计划核验状态": detail.get("湖北官方系统或省招办计划核验状态", ""),
        "高校官网或招生章程辅证状态": detail.get("高校官网或招生章程辅证状态", ""),
        "三方字段一致性状态": detail.get("三方字段一致性状态", ""),
        "字段事实写回状态": detail.get("字段事实写回状态", ""),
        "私有页图相对路径": rel_from_private_root(image_path),
        "私有OCR文本相对路径": rel_from_private_root(text_path),
        "OCR行文本": ocr_text,
        "PDF原页人工读数": "",
        "湖北官方字段值": "",
        "高校官网或招生章程字段值": "",
        "字段确认值": "",
        "一审记录": "",
        "二审记录": "",
        "复核结论": "",
        "复核备注": "",
    }


def write_page_side_html(page_side, private_rows, ocr_text):
    key = page_side.get("页码版面键", "")
    page = page_side.get("来源页码", "")
    image_path = PRIVATE_RENDERED_PAGE_DIR / f"page-{page_no(page)}.png"
    html_path = PRIVATE_HTML_DIR / f"{key}.html"
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:24px;line-height:1.45;color:#111}",
        ".warn{color:#9a3412;font-weight:600}",
        ".grid{display:grid;grid-template-columns:minmax(320px,1fr) minmax(420px,1fr);gap:18px;align-items:start}",
        "img{max-width:100%;border:1px solid #ddd;background:#fff}",
        "table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0}",
        "td,th{border:1px solid #ddd;padding:6px;vertical-align:top}",
        "pre{white-space:pre-wrap;background:#f7f7f7;border:1px solid #ddd;border-radius:6px;padding:10px;font-size:13px;max-height:520px;overflow:auto}",
        "</style>",
        f"<title>第一闭环页列 {html.escape(key)}</title>",
        f"<h1>第一闭环页列 {html.escape(key)}</h1>",
        "<p class='warn'>私有核页材料：包含页图、OCR 行和待核学校专业明细，不得提交公开仓库。</p>",
        "<div class='grid'>",
        "<section>",
        f"<h2>第 {html.escape(page)} 页 {html.escape(page_side.get('版面列',''))}</h2>",
        f"<img src='{html.escape(html_rel_to_private(image_path))}' alt='page {html.escape(page)}'>",
        "</section>",
        "<section>",
        "<h2>页列任务</h2>",
        "<table>",
        "<tr><th>任务</th><th>数量/状态</th></tr>",
        f"<tr><td>第一闭环优先级</td><td>{html.escape(page_side.get('第一闭环页列优先级',''))}</td></tr>",
        f"<tr><td>明细任务数</td><td>{html.escape(page_side.get('页列总任务数',''))}</td></tr>",
        f"<tr><td>自动官网辅证任务</td><td>{html.escape(page_side.get('自动官网辅证任务数',''))}</td></tr>",
        f"<tr><td>P0人工字段任务</td><td>{html.escape(page_side.get('P0人工字段任务数',''))}</td></tr>",
        f"<tr><td>是否需要双人复核</td><td>{html.escape(page_side.get('是否需要双人复核',''))}</td></tr>",
        "</table>",
        "<h2>OCR 行文本</h2>",
        f"<pre>{html.escape(ocr_text)}</pre>",
        "</section>",
        "</div>",
        "<h2>逐任务核验表</h2>",
        "<table>",
        "<tr><th>来源</th><th>院校/专业</th><th>待核字段</th><th>OCR/官网线索</th><th>人工记录</th></tr>",
    ]
    for row in private_rows:
        school_major = (
            f"{row.get('院校代码','')} {row.get('院校名称OCR','')}<br>"
            f"{row.get('专业代号OCR','')} {row.get('专业名称及备注短摘','')}"
        )
        clues = (
            f"OCR计划数：{row.get('OCR专业计划数候选','')}；官网计划数：{row.get('最佳官网计划数','')}<br>"
            f"OCR学费：{row.get('OCR学费候选','')}；官网学费：{row.get('最佳官网学费','')}<br>"
            f"OCR选科：{row.get('OCR再选科目候选','')}；官网选科：{row.get('最佳官网选科','')}"
        )
        lines.extend([
            "<tr>",
            f"<td>{html.escape(row.get('任务来源类型',''))}<br>{html.escape(row.get('第一闭环纳入原因',''))}</td>",
            f"<td>{school_major}</td>",
            f"<td>{html.escape(row.get('字段名','') or row.get('官网辅证自动动作',''))}</td>",
            f"<td>{clues}</td>",
            "<td>PDF原页：<br>湖北官方：<br>高校辅证：<br>结论：</td>",
            "</tr>",
        ])
    lines.extend(["</table>"])
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return html_path


def write_master_html(index_rows):
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<title>第19期稳定基座第一闭环私有复核索引</title>",
        "<h1>第19期稳定基座第一闭环私有复核索引</h1>",
        "<p>私有材料，不得提交公开仓库。按 Q0、Q1、Q2 顺序核页。</p>",
        "<ol>",
    ]
    for row in index_rows:
        lines.append(
            f"<li><a href='{html.escape(row['私有第一闭环页列HTML相对路径'])}'>"
            f"{html.escape(row['页码版面键'])}</a>："
            f"{html.escape(row['第一闭环页列优先级'])}，"
            f"{html.escape(row['第一闭环明细任务数'])} 个任务</li>"
        )
    lines.extend(["</ol>"])
    PRIVATE_MASTER_HTML.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_MASTER_HTML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build():
    first_detail_rows = read_csv(FIRST_DETAIL)
    first_page_rows = read_csv(FIRST_PAGE_SIDE)
    progress_by_key = {row.get("页码版面键", ""): row for row in read_csv(PAGE_PROGRESS)}
    field_clue_by_key = {row.get("页码版面键", ""): row for row in read_csv(FIELD_CLUE)}
    overlay_by_key = {row.get("页码版面键", ""): row for row in read_csv(OVERLAY_PUBLIC)}
    manifest_by_page = {row.get("PDF页码", ""): row for row in read_csv(PAGE_MANIFEST)}
    official_status = json.loads(OFFICIAL_STATUS.read_text(encoding="utf-8"))
    ocr_by_page_side = read_ocr_by_page_side()

    detail_by_key = defaultdict(list)
    for row in first_detail_rows:
        detail_by_key[row.get("页码版面键", "")].append(row)

    public_rows = []
    private_index_rows = []
    for page_side in first_page_rows:
        key = page_side.get("页码版面键", "")
        details = detail_by_key.get(key, [])
        progress = progress_by_key.get(key, {})
        field_clue = field_clue_by_key.get(key, {})
        overlay = overlay_by_key.get(key, {})
        manifest = manifest_by_page.get(page_side.get("来源页码", ""), {})
        ocr_lines = ocr_by_page_side.get((page_side.get("来源页码", ""), page_side.get("版面列", "")), [])
        ocr_count, ocr_low = ocr_stats(ocr_lines)
        ocr_text = join_ocr_lines(ocr_lines)

        private_rows = [
            private_detail_row(detail, page_side, progress, ocr_text)
            for detail in details
        ]
        private_csv = PRIVATE_PAGE_SIDE_DIR / f"{key}.csv"
        write_csv(private_csv, private_rows, PRIVATE_DETAIL_FIELDS)
        private_html = write_page_side_html(page_side, private_rows, ocr_text)
        private_csv_sha = file_sha(private_csv)
        private_html_sha = file_sha(private_html)

        first_detail_count = as_int(page_side.get("页列总任务数"))
        public_rows.append({
            "稳定基座第一闭环复核公开账本ID": stable_id("FIRSTREVIEW", [key]),
            "来源第一闭环明细包": "data/working/issue19-stable-foundation-first-closure-detail-packet.csv",
            "来源第一闭环页列包": "data/working/issue19-stable-foundation-first-closure-page-side-packet.csv",
            "来源页列底座公开核页进度账本": "data/working/issue19-page-side-foundation-review-progress-public-ledger.csv",
            "来源页列底座字段线索公开审计": "data/working/issue19-page-side-foundation-field-clue-public-audit.csv",
            "来源页列底座人工复核Overlay公开账本": "data/working/issue19-page-side-foundation-human-review-overlay-public-ledger.csv",
            "来源湖北官方公开入口状态快照": "data/working/issue19-official-public-entry-status.json",
            "来源第一闭环私有复核材料": "first_closure_private_review_material_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×第一闭环私有复核材料进度",
            **false_gate_values(),
            "稳定基座第一闭环页列包ID": page_side.get("稳定基座第一闭环页列包ID", ""),
            "页列底座核验批次行ID": progress.get("页列底座核验批次行ID", ""),
            "页列底座核页进度公开账本ID": progress.get("页列底座核页进度公开账本ID", ""),
            "页列底座字段线索公开审计ID": field_clue.get("页列底座字段线索公开审计ID", ""),
            "页列底座Overlay公开账本ID": overlay.get("页列底座Overlay公开账本ID", ""),
            "来源页码": page_side.get("来源页码", ""),
            "版面列": page_side.get("版面列", ""),
            "页码版面键": key,
            "第一闭环页列优先级": page_side.get("第一闭环页列优先级", ""),
            "第一闭环页列执行状态": "R0-私有复核材料已生成但未核页",
            "第一闭环明细任务数": page_side.get("页列总任务数", ""),
            "自动官网辅证任务数": page_side.get("自动官网辅证任务数", ""),
            "P0人工字段任务数": page_side.get("P0人工字段任务数", ""),
            "C0冲突任务数": page_side.get("C0冲突任务数", ""),
            "C1官网补缺任务数": page_side.get("C1官网补缺任务数", ""),
            "C7官网未匹配任务数": page_side.get("C7官网未匹配任务数", ""),
            "EXEC01冲突异常字段数": page_side.get("EXEC01冲突异常字段数", ""),
            "EXEC02计划数偏大字段数": page_side.get("EXEC02计划数偏大字段数", ""),
            "EXEC03高校辅证字段数": page_side.get("EXEC03高校辅证字段数", ""),
            "涉及专业行数": page_side.get("涉及专业行数", ""),
            "涉及字段任务数": page_side.get("涉及字段任务数", ""),
            "是否含计划数冲突或补缺": page_side.get("是否含计划数冲突或补缺", ""),
            "是否需要双人复核": page_side.get("是否需要双人复核", ""),
            "批次总序": progress.get("批次总序", ""),
            "批次ID": progress.get("批次ID", ""),
            "批次名称": progress.get("批次名称", ""),
            "批内页列序号": progress.get("批内页列序号", ""),
            "页列全局风险总序": progress.get("页列全局风险总序", ""),
            "综合风险优先级桶": progress.get("综合风险优先级桶", ""),
            "页列首要核验动作": progress.get("页列首要核验动作", ""),
            "全量底座包内专业行数": progress.get("包内专业行数", ""),
            "全量底座包内字段任务数": progress.get("包内字段任务数", ""),
            "OCR行数": str(ocr_count),
            "OCR低置信度行数": str(ocr_low),
            "私有页图证据编号": manifest.get("私有页图证据编号", ""),
            "私有页图SHA256": manifest.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": manifest.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": manifest.get("私有OCR文本SHA256", ""),
            "私有第一闭环页列CSV证据编号": f"first-closure-{key}-csv",
            "私有第一闭环页列CSV_SHA256": private_csv_sha,
            "私有第一闭环页列HTML证据编号": f"first-closure-{key}-html",
            "私有第一闭环页列HTML_SHA256": private_html_sha,
            "私有第一闭环材料状态": "private_first_closure_review_material_generated",
            "Overlay进度桶": overlay.get("Overlay进度桶", ""),
            "PDF原页记录已填字段数": overlay.get("PDF原页记录已填字段数", ""),
            "湖北官方记录已填字段数": overlay.get("湖北官方记录已填字段数", ""),
            "高校辅证记录已填字段数": overlay.get("高校辅证记录已填字段数", ""),
            "字段最终记录已填字段数": overlay.get("字段最终记录已填字段数", ""),
            "三方一致性可评估字段数": overlay.get("三方一致性可评估字段数", ""),
            "首轮复核已填字段数": overlay.get("首轮复核已填字段数", ""),
            "次轮复核已填字段数": overlay.get("次轮复核已填字段数", ""),
            "复查结论已填字段数": overlay.get("复查结论已填字段数", ""),
            "第一闭环PDF原页完成任务数": "0",
            "第一闭环湖北官方完成任务数": "0",
            "第一闭环高校辅证完成任务数": "0",
            "第一闭环字段事实写回可进入任务数": "0",
            "官方公开计划页可定稿": str(bool(official_status.get("official_plan_page", {}).get("can_finalize"))).lower(),
            "数智平台可定稿": str(bool(official_status.get("zspt_platform", {}).get("can_finalize"))).lower(),
            "字段事实写回状态": "blocked_until_first_closure_pdf_hubei_review_closed",
            "公开安全策略": (
                "公开表只保存页列计数、公开账本回链、私有材料证据编号和SHA；"
                "不保存页图路径、OCR文本、人工读数、登录态或私有记录。"
            ),
            "下一步": (
                "打开本页列私有HTML/CSV，先核PDF原页，再核湖北官方侧；"
                "高校官网只作辅证，冲突时回到PDF原页和湖北官方侧。"
            ),
        })
        private_index_rows.append({
            "来源页码": page_side.get("来源页码", ""),
            "版面列": page_side.get("版面列", ""),
            "页码版面键": key,
            "第一闭环页列优先级": page_side.get("第一闭环页列优先级", ""),
            "稳定基座第一闭环页列包ID": page_side.get("稳定基座第一闭环页列包ID", ""),
            "页列底座核验批次行ID": progress.get("页列底座核验批次行ID", ""),
            "私有第一闭环页列CSV相对路径": str(private_csv.relative_to(PRIVATE_OUTPUT_DIR)),
            "私有第一闭环页列HTML相对路径": str(private_html.relative_to(PRIVATE_OUTPUT_DIR)),
            "私有第一闭环页列CSV_SHA256": private_csv_sha,
            "私有第一闭环页列HTML_SHA256": private_html_sha,
            "第一闭环明细任务数": str(first_detail_count),
            "OCR行数": str(ocr_count),
        })

    write_csv(PRIVATE_INDEX, private_index_rows, PRIVATE_INDEX_FIELDS)
    write_master_html(private_index_rows)
    return public_rows, private_index_rows


def public_text_safe(paths):
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    return all(token not in text for token in FORBIDDEN_PUBLIC_TOKENS)


def main():
    public_rows, private_index_rows = build()
    write_csv(PUBLIC_OUTPUT, public_rows, PUBLIC_FIELDS)
    summary = {
        "status": "issue19_stable_foundation_first_closure_review_materials_not_final",
        "generated_by": "build_issue19_first_closure_review_materials.py",
        "source_first_closure_detail_packet": "data/working/issue19-stable-foundation-first-closure-detail-packet.csv",
        "source_first_closure_page_side_packet": "data/working/issue19-stable-foundation-first-closure-page-side-packet.csv",
        "source_page_side_progress": "data/working/issue19-page-side-foundation-review-progress-public-ledger.csv",
        "source_page_side_field_clue": "data/working/issue19-page-side-foundation-field-clue-public-audit.csv",
        "source_page_side_overlay": "data/working/issue19-page-side-foundation-human-review-overlay-public-ledger.csv",
        "source_official_public_status": "data/working/issue19-official-public-entry-status.json",
        "source_private_first_closure_review_material": "first_closure_private_review_material_not_public",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": "data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv",
        "public_row_count": len(public_rows),
        "private_page_side_material_count": len(private_index_rows),
        "unique_page_side_count": len({row.get("页码版面键") for row in public_rows}),
        "unique_pdf_page_count": len({row.get("来源页码") for row in public_rows}),
        "first_closure_detail_task_count": sum(as_int(row.get("第一闭环明细任务数")) for row in public_rows),
        "auto_task_count": sum(as_int(row.get("自动官网辅证任务数")) for row in public_rows),
        "manual_task_count": sum(as_int(row.get("P0人工字段任务数")) for row in public_rows),
        "page_side_priority_counts": dict(Counter(row.get("第一闭环页列优先级") for row in public_rows)),
        "material_status_counts": dict(Counter(row.get("私有第一闭环材料状态") for row in public_rows)),
        "overlay_progress_bucket_counts": dict(Counter(row.get("Overlay进度桶") for row in public_rows)),
        "official_public_plan_page_can_finalize": False,
        "zspt_platform_can_finalize": False,
        "private_index_csv_sha256": file_sha(PRIVATE_INDEX),
        "private_master_html_sha256": file_sha(PRIVATE_MASTER_HTML),
        "pdf_review_completed_task_count": 0,
        "hubei_official_completed_task_count": 0,
        "school_support_completed_task_count": 0,
        "field_writeback_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "policy": {
            "purpose": "把第一闭环36个页列接到既有页图、OCR、全量页列底座和Overlay，方便优先人工核页。",
            "public_boundary": "公开表只保存状态、计数和SHA；私有HTML/CSV保留页图、OCR行和待核明细。",
            "no_finalization": "本材料包不确认字段事实，不自动写回，不生成学校专业建议。"
        },
    }
    write_json(SUMMARY_OUTPUT, summary)
    if not public_text_safe([PUBLIC_OUTPUT, SUMMARY_OUTPUT]):
        raise SystemExit("公开输出命中禁止公开 token")
    print(f"写出 {PUBLIC_OUTPUT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出私有第一闭环复核材料：{PRIVATE_OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
