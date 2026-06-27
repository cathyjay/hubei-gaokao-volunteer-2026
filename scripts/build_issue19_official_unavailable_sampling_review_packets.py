#!/usr/bin/env python3
import csv
import hashlib
import html
import json
import os
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PUBLIC_OVERLAY = (
    ROOT / "data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv"
)
PRIVATE_OVERLAY = (
    ROOT / "private/review-assets/issue19-official-unavailable-sampling-review-overlay/sampling-review-overlay.csv"
)
PRIVATE_OCR_LINES = ROOT / "private/ocr-runs/issue19-full-120dpi/ocr-lines.csv"
PRIVATE_RENDERED_PAGE_DIR = ROOT / "private/ocr-runs/issue19-full-120dpi/rendered-pages"
PRIVATE_TEXT_DIR = ROOT / "private/ocr-runs/issue19-full-120dpi/text"

PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-official-unavailable-sampling-review-packets"
)
PRIVATE_PAGE_SIDE_DIR = PRIVATE_OUTPUT_DIR / "page-sides"
PRIVATE_HTML_DIR = PRIVATE_OUTPUT_DIR / "html"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "sampling-review-packets-private-index.csv"
PRIVATE_MASTER_HTML = PRIVATE_OUTPUT_DIR / "index.html"

PUBLIC_OUTPUT = (
    ROOT / "data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-official-unavailable-sampling-review-packets-public-ledger-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_official_unavailable_sampling_review_packets_public_ledger"

PUBLIC_FIELDS = [
    "官方不可得抽样页列包公开账本ID",
    "来源抽样复核Overlay公开账本",
    "来源本地抽样复核Overlay",
    "来源本地抽样页列核验包",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许写回字段事实",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列包排序",
    "页列抽样明细数",
    "涉及专业行数",
    "涉及专业组数",
    "高风险100%核验明细数",
    "C2强辅证抽样明细数",
    "P3低风险抽样明细数",
    "C0冲突明细数",
    "C1官网补缺明细数",
    "C7官网未匹配明细数",
    "双人复核明细数",
    "R4阻断明细数",
    "R3高风险明细数",
    "R1低风险明细数",
    "R0观察明细数",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR摘要证据编号",
    "私有OCR摘要SHA256",
    "OCR行数",
    "OCR低置信度行数",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页列HTML证据编号",
    "私有页列HTML_SHA256",
    "本地包状态",
    "PDF原页已填字段数",
    "湖北官方侧已填字段数",
    "高校辅证已填字段数",
    "三方一致性可评估明细数",
    "抽检失败明细数",
    "升级要求明细数",
    "首轮复核完成明细数",
    "次轮复核完成明细数",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_INDEX_FIELDS = [
    "来源页码",
    "版面列",
    "页码版面键",
    "页列包排序",
    "私有页列CSV相对路径",
    "私有页列HTML相对路径",
    "私有页列CSV_SHA256",
    "私有页列HTML_SHA256",
    "页列抽样明细数",
    "高风险100%核验明细数",
    "双人复核明细数",
]

PRIVATE_PACKET_FIELDS = [
    "页列包说明",
    "本页列CSV用途",
    "人工填写权威表",
    "私有页图相对路径",
    "私有OCR文本相对路径",
    "OCR行文本",
    "官方不可得抽样OverlayID",
    "来源官方不可得抽样执行明细ID",
    "执行类别",
    "执行优先级",
    "风险等级",
    "抽样策略",
    "样本选择原因",
    "样本序号",
    "样本最低明细数",
    "是否100%人工核验",
    "是否抽样核验",
    "是否低风险样本",
    "是否需要双人复核",
    "院校代码",
    "院校名称OCR",
    "专业行ID",
    "专业组出现ID",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "必核字段",
    "字段差异标记",
    "官网辅证自动动作",
    "OCR专业计划数候选",
    "OCR学费候选",
    "OCR再选科目候选",
    "最佳官网专业名称",
    "最佳官网专业代号",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "最佳官网来源文件",
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "疑似OCR把学费读入计划数",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方一致性状态",
    "字段事实写回状态",
    "升级触发器",
    "升级范围",
    "当前用途边界",
    "下一步",
    "PDF原页证据编号",
    "PDF原页证据SHA256",
    "PDF原页人工读数_专业名称",
    "PDF原页人工读数_专业计划数",
    "PDF原页人工读数_学费",
    "PDF原页人工读数_再选科目",
    "PDF原页人工读数_备注限制",
    "PDF原页记录状态",
    "湖北官方证据编号",
    "湖北官方证据SHA256",
    "湖北官方字段值_专业名称",
    "湖北官方字段值_专业计划数",
    "湖北官方字段值_学费",
    "湖北官方字段值_再选科目",
    "湖北官方字段值_备注限制",
    "湖北官方记录状态",
    "高校辅证证据编号",
    "高校辅证证据SHA256",
    "高校辅证字段值_专业名称",
    "高校辅证字段值_专业计划数",
    "高校辅证字段值_学费",
    "高校辅证字段值_再选科目",
    "高校辅证字段值_备注限制",
    "高校辅证记录状态",
    "三方一致性人工结论",
    "是否抽检失败",
    "失败升级范围",
    "一审复核人",
    "一审时间",
    "一审记录",
    "二审复核人",
    "二审时间",
    "二审记录",
    "复核结论",
    "人工备注",
    "字段事实是否允许写回",
    "人工是否允许作为志愿推荐依据",
    "人工是否最终可用",
    "人工记录锁定状态",
    "人工记录版本",
    "updated_at",
]

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许写回字段事实",
]

COMPLETE_TOKENS = {
    "done",
    "complete",
    "completed",
    "checked",
    "verified",
    "matched",
    "已完成",
    "完成",
    "一致",
}


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


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


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


def filled(value):
    return bool(str(value or "").strip())


def complete(value):
    text = str(value or "").strip().lower()
    return bool(text) and (
        text in COMPLETE_TOKENS
        or any(token in text for token in ["done", "complete", "verified", "matched"])
    )


def false_values():
    return {field: "false" for field in FALSE_FIELDS}


def page_no(page):
    return f"{as_int(page):03d}"


def page_key(row):
    page = str(row.get("来源页码", "")).strip()
    side = str(row.get("版面列", "")).strip()
    return f"{int(page):03d}-{side}" if page.isdigit() and side else row.get("页码版面键", "")


def rel_from_private_root(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def html_rel_to_private(path):
    return os.path.relpath(path, PRIVATE_HTML_DIR)


def read_ocr_by_page_side():
    result = defaultdict(list)
    if not PRIVATE_OCR_LINES.exists():
        return result
    for row in read_csv(PRIVATE_OCR_LINES):
        side = row.get("table_band", "")
        if side in {"left", "right"}:
            result[(row.get("page", ""), side)].append(row)
    for rows in result.values():
        rows.sort(key=lambda row: as_int(row.get("line_no")))
    return result


def join_ocr_lines(rows):
    return "\n".join(
        f"{row.get('line_no','')}. {row.get('text','')} [{row.get('confidence','')}]"
        for row in rows
    )


def ocr_stats(rows):
    confidences = [as_float(row.get("confidence")) for row in rows if row.get("confidence")]
    return len(rows), sum(conf < 0.75 for conf in confidences)


def private_packet_row(row, ocr_text):
    page = row.get("来源页码", "")
    image_path = PRIVATE_RENDERED_PAGE_DIR / f"page-{page_no(page)}.png"
    text_path = PRIVATE_TEXT_DIR / f"{page_no(page)}_page-{page_no(page)}.txt"
    output = {field: row.get(field, "") for field in PRIVATE_PACKET_FIELDS}
    output.update({
        "页列包说明": "本页列包按官方不可得抽样执行明细切片；公开仓库只保存SHA和计数。",
        "本页列CSV用途": "查看和分工；人工填写以本地抽样复核Overlay总表为权威。",
        "人工填写权威表": "issue19-official-unavailable-sampling-review-overlay/sampling-review-overlay.csv",
        "私有页图相对路径": rel_from_private_root(image_path),
        "私有OCR文本相对路径": rel_from_private_root(text_path),
        "OCR行文本": ocr_text,
    })
    return output


def write_page_side_html(key, rows, ocr_text):
    page = rows[0].get("来源页码", "") if rows else ""
    side = rows[0].get("版面列", "") if rows else ""
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
        f"<title>官方不可得抽样页列 {html.escape(key)}</title>",
        f"<h1>官方不可得抽样页列 {html.escape(key)}</h1>",
        "<p class='warn'>私有核页材料：包含页图、OCR 行、学校专业明细和字段线索，不得提交公开仓库。人工填写以抽样复核 Overlay 总表为准。</p>",
        "<div class='grid'>",
        "<section>",
        f"<h2>第 {html.escape(page)} 页 {html.escape(side)}</h2>",
        f"<img src='{html.escape(html_rel_to_private(image_path))}' alt='page {html.escape(page)}'>",
        "</section>",
        "<section>",
        "<h2>OCR 行文本</h2>",
        f"<pre>{html.escape(ocr_text)}</pre>",
        "</section>",
        "</div>",
        "<h2>抽样明细</h2>",
        "<table>",
        "<tr><th>动作/风险</th><th>院校/专业</th><th>OCR 候选</th><th>官网辅证</th><th>人工核验栏</th></tr>",
    ]
    for row in rows:
        school_major = (
            f"{html.escape(row.get('院校代码',''))} {html.escape(row.get('院校名称OCR',''))}<br>"
            f"{html.escape(row.get('院校专业组代码OCR规范化',''))} / "
            f"{html.escape(row.get('专业代号OCR',''))} "
            f"{html.escape(row.get('专业名称及备注短摘',''))}"
        )
        ocr = (
            f"计划数：{html.escape(row.get('OCR专业计划数候选',''))}<br>"
            f"学费：{html.escape(row.get('OCR学费候选',''))}<br>"
            f"选科：{html.escape(row.get('OCR再选科目候选',''))}"
        )
        school = (
            f"专业：{html.escape(row.get('最佳官网专业名称',''))}<br>"
            f"代号：{html.escape(row.get('最佳官网专业代号',''))}<br>"
            f"计划数：{html.escape(row.get('最佳官网计划数',''))}<br>"
            f"学费：{html.escape(row.get('最佳官网学费',''))}<br>"
            f"选科：{html.escape(row.get('最佳官网选科',''))}"
        )
        lines.extend([
            "<tr>",
            f"<td>{html.escape(row.get('官网辅证自动动作',''))}<br>{html.escape(row.get('风险等级',''))}<br>双人复核：{html.escape(row.get('是否需要双人复核',''))}</td>",
            f"<td>{school_major}</td>",
            f"<td>{ocr}</td>",
            f"<td>{school}</td>",
            "<td>PDF原页：<br>湖北官方：<br>高校辅证：<br>三方结论：<br>抽检失败/升级：</td>",
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
        "<title>第19期官方不可得抽样核验包索引</title>",
        "<h1>第19期官方不可得抽样核验包索引</h1>",
        "<p>私有材料，不得提交公开仓库。建议先核高风险 100% 页列，再核 C2/P3 抽样页列。</p>",
        "<ol>",
    ]
    for row in index_rows:
        lines.append(
            f"<li><a href='{html.escape(row['私有页列HTML相对路径'])}'>"
            f"{html.escape(row['页码版面键'])}</a>："
            f"{html.escape(row['页列抽样明细数'])} 条，"
            f"高风险 {html.escape(row['高风险100%核验明细数'])}，"
            f"双人复核 {html.escape(row['双人复核明细数'])}</li>"
        )
    lines.extend(["</ol>"])
    PRIVATE_MASTER_HTML.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_MASTER_HTML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build():
    public_rows = read_csv(PUBLIC_OVERLAY)
    private_rows = read_csv(PRIVATE_OVERLAY)
    public_by_execution_id = {
        row.get("来源官方不可得抽样执行明细ID", ""): row for row in public_rows
    }
    ocr_by_page_side = read_ocr_by_page_side()
    private_by_key = defaultdict(list)
    for row in private_rows:
        private_by_key[page_key(row)].append(row)
    for rows in private_by_key.values():
        rows.sort(
            key=lambda row: (
                as_int(row.get("来源页码")),
                row.get("版面列", ""),
                as_int(row.get("专业组内专业序号")),
                row.get("专业行ID", ""),
            )
        )

    ledger_rows = []
    private_index_rows = []
    sorted_keys = sorted(
        private_by_key,
        key=lambda key: (
            -sum(r.get("是否100%人工核验") == "true" for r in private_by_key[key]),
            -sum(r.get("是否需要双人复核") == "true" for r in private_by_key[key]),
            as_int(private_by_key[key][0].get("来源页码")),
            private_by_key[key][0].get("版面列", ""),
        ),
    )

    for order, key in enumerate(sorted_keys, start=1):
        rows = private_by_key[key]
        page = rows[0].get("来源页码", "")
        side = rows[0].get("版面列", "")
        ocr_lines = ocr_by_page_side.get((page, side), [])
        ocr_text = join_ocr_lines(ocr_lines)
        ocr_count, ocr_low = ocr_stats(ocr_lines)

        packet_rows = [private_packet_row(row, ocr_text) for row in rows]
        packet_csv = PRIVATE_PAGE_SIDE_DIR / f"{key}.csv"
        write_csv(packet_csv, packet_rows, PRIVATE_PACKET_FIELDS)
        packet_html = write_page_side_html(key, rows, ocr_text)
        csv_sha = file_sha(packet_csv)
        html_sha = file_sha(packet_html)
        image_path = PRIVATE_RENDERED_PAGE_DIR / f"page-{page_no(page)}.png"
        text_path = PRIVATE_TEXT_DIR / f"{page_no(page)}_page-{page_no(page)}.txt"
        image_sha = file_sha(image_path) if image_path.exists() else ""
        text_sha = file_sha(text_path) if text_path.exists() else ""

        action_counts = Counter(row.get("官网辅证自动动作", "") for row in rows)
        risk_counts = Counter(row.get("风险等级", "") for row in rows)
        public_slice = [
            public_by_execution_id.get(row.get("来源官方不可得抽样执行明细ID", ""), {})
            for row in rows
        ]
        ledger_rows.append({
            "官方不可得抽样页列包公开账本ID": stable_id(
                "SAMPLINGPACKET", [key, SOURCE_PDF_SHA256]
            ),
            "来源抽样复核Overlay公开账本": (
                "data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv"
            ),
            "来源本地抽样复核Overlay": "local_sampling_review_overlay_not_public",
            "来源本地抽样页列核验包": "local_sampling_review_packet_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "官方不可得抽样复核Overlay×PDF页码×版面列",
            **false_values(),
            "来源页码": page,
            "版面列": side,
            "页码版面键": key,
            "页列包排序": str(order),
            "页列抽样明细数": str(len(rows)),
            "涉及专业行数": str(len({row.get("专业行ID", "") for row in rows if row.get("专业行ID", "")})),
            "涉及专业组数": str(len({row.get("专业组出现ID", "") for row in rows if row.get("专业组出现ID", "")})),
            "高风险100%核验明细数": str(sum(row.get("是否100%人工核验") == "true" for row in rows)),
            "C2强辅证抽样明细数": str(action_counts.get("C2-强辅证抽检并等待湖北官方闭环", 0)),
            "P3低风险抽样明细数": str(action_counts.get("P3-低风险抽检但非最终", 0)),
            "C0冲突明细数": str(action_counts.get("C0-冲突先核PDF原页和湖北官方系统", 0)),
            "C1官网补缺明细数": str(action_counts.get("C1-官网补缺候选但禁止自动写回", 0)),
            "C7官网未匹配明细数": str(action_counts.get("C7-官网源未匹配专业需人工确认专业名", 0)),
            "双人复核明细数": str(sum(row.get("是否需要双人复核") == "true" for row in rows)),
            "R4阻断明细数": str(risk_counts.get("R4-blocker", 0)),
            "R3高风险明细数": str(risk_counts.get("R3-high", 0)),
            "R1低风险明细数": str(risk_counts.get("R1-low", 0)),
            "R0观察明细数": str(risk_counts.get("R0-observe", 0)),
            "私有页图证据编号": f"sampling-review-page-{page_no(page)}-image",
            "私有页图SHA256": image_sha,
            "私有OCR摘要证据编号": f"sampling-review-page-{page_no(page)}-ocr-summary",
            "私有OCR摘要SHA256": text_sha,
            "OCR行数": str(ocr_count),
            "OCR低置信度行数": str(ocr_low),
            "私有页列CSV证据编号": f"sampling-review-{key}-csv",
            "私有页列CSV_SHA256": csv_sha,
            "私有页列HTML证据编号": f"sampling-review-{key}-html",
            "私有页列HTML_SHA256": html_sha,
            "本地包状态": "R0-页列包已生成未填写",
            "PDF原页已填字段数": str(sum(as_int(row.get("PDF原页已填字段数")) for row in public_slice)),
            "湖北官方侧已填字段数": str(sum(as_int(row.get("湖北官方侧已填字段数")) for row in public_slice)),
            "高校辅证已填字段数": str(sum(as_int(row.get("高校辅证已填字段数")) for row in public_slice)),
            "三方一致性可评估明细数": str(sum(row.get("三方一致性可评估") == "true" for row in public_slice)),
            "抽检失败明细数": str(sum(row.get("抽检失败状态") == "failed" for row in public_slice)),
            "升级要求明细数": str(sum(row.get("升级状态") == "required" for row in public_slice)),
            "首轮复核完成明细数": str(sum(row.get("首轮复核状态") == "done" for row in public_slice)),
            "次轮复核完成明细数": str(sum(row.get("次轮复核状态") == "done" for row in public_slice)),
            "字段事实写回状态": "blocked_until_private_overlay_pdf_hubei_review_closed",
            "公开安全策略": (
                "公开表只保存页列包计数、证据编号、SHA和状态；"
                "学校专业明细、OCR明细、字段记录内容和人工记录内容只留在本地私有包。"
            ),
            "下一步": "打开本地页列HTML/CSV，回看PDF原页并把结论写回本地抽样复核Overlay总表。",
        })
        private_index_rows.append({
            "来源页码": page,
            "版面列": side,
            "页码版面键": key,
            "页列包排序": str(order),
            "私有页列CSV相对路径": str(packet_csv.relative_to(PRIVATE_OUTPUT_DIR)),
            "私有页列HTML相对路径": str(packet_html.relative_to(PRIVATE_OUTPUT_DIR)),
            "私有页列CSV_SHA256": csv_sha,
            "私有页列HTML_SHA256": html_sha,
            "页列抽样明细数": str(len(rows)),
            "高风险100%核验明细数": str(sum(row.get("是否100%人工核验") == "true" for row in rows)),
            "双人复核明细数": str(sum(row.get("是否需要双人复核") == "true" for row in rows)),
        })

    write_csv(PRIVATE_INDEX, private_index_rows, PRIVATE_INDEX_FIELDS)
    write_master_html(private_index_rows)
    write_csv(PUBLIC_OUTPUT, ledger_rows, PUBLIC_FIELDS)

    summary = {
        "status": "issue19_official_unavailable_sampling_review_packets_public_ledger_not_final",
        "generated_by": "build_issue19_official_unavailable_sampling_review_packets.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_public_overlay": (
            "data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv"
        ),
        "source_private_overlay": "local_sampling_review_overlay_not_public",
        "source_private_packets": "local_sampling_review_packet_not_public",
        "output_table": (
            "data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv"
        ),
        "row_grain": "PDF页码×版面列",
        "row_count": len(ledger_rows),
        "unique_page_side_count": len({row["页码版面键"] for row in ledger_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in ledger_rows}),
        "private_page_side_packet_count": len(private_index_rows),
        "private_page_side_packet_csv_count": len(private_index_rows),
        "private_page_side_packet_html_count": len(private_index_rows),
        "private_index_csv_sha256": file_sha(PRIVATE_INDEX),
        "private_master_html_sha256": file_sha(PRIVATE_MASTER_HTML),
        "sampling_detail_count": sum(as_int(row["页列抽样明细数"]) for row in ledger_rows),
        "high_risk_100pct_detail_count": sum(as_int(row["高风险100%核验明细数"]) for row in ledger_rows),
        "c2_sample_detail_count": sum(as_int(row["C2强辅证抽样明细数"]) for row in ledger_rows),
        "p3_sample_detail_count": sum(as_int(row["P3低风险抽样明细数"]) for row in ledger_rows),
        "double_review_required_count": sum(as_int(row["双人复核明细数"]) for row in ledger_rows),
        "pdf_page_filled_field_count": sum(as_int(row["PDF原页已填字段数"]) for row in ledger_rows),
        "hubei_official_filled_field_count": sum(as_int(row["湖北官方侧已填字段数"]) for row in ledger_rows),
        "school_support_filled_field_count": sum(as_int(row["高校辅证已填字段数"]) for row in ledger_rows),
        "tri_consistency_assessable_count": sum(as_int(row["三方一致性可评估明细数"]) for row in ledger_rows),
        "sampling_failure_count": sum(as_int(row["抽检失败明细数"]) for row in ledger_rows),
        "escalation_required_count": sum(as_int(row["升级要求明细数"]) for row in ledger_rows),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "packet_status_counts": dict(Counter(row["本地包状态"] for row in ledger_rows)),
        "safety_note": (
            "公开账本只保存页列包计数、证据编号、SHA和状态；"
            "学校专业明细、OCR明细、字段记录内容和人工记录内容只留在本地私有包。"
        ),
        "policy": {
            "authoritative_manual_table": (
                "本地抽样复核Overlay总表是人工填写权威表；页列包用于查看、分工和核页。"
            ),
            "boundary": "本账本不确认字段、不写回、不生成学校专业建议或志愿推荐。",
        },
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    build()
    print(f"写出 {PUBLIC_OUTPUT.relative_to(ROOT)}")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出本地抽样页列核验包：{PRIVATE_OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
