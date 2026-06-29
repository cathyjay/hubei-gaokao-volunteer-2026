#!/usr/bin/env python3
import csv
import hashlib
import html
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

D0_D1_PUBLIC = WORKING / "issue19-school-source-adapter-d0-d1-manual-review-packets-v1-public-ledger.csv"
D0_D1_SUMMARY = WORKING / "issue19-school-source-adapter-d0-d1-manual-review-packets-v1-summary.json"
D0_D1_PRIVATE_REVIEW_ITEMS = (
    ROOT
    / "private/review-assets/issue19-school-source-adapter-d0-d1-manual-review-packets-v1"
    / "school-source-adapter-d0-d1-private-review-items.csv"
)

PUBLIC_OUTPUT = WORKING / "issue19-school-source-adapter-d0-d1-page-side-packets-v1-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-adapter-d0-d1-page-side-packets-v1-summary.json"
PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-school-source-adapter-d0-d1-page-side-packets-v1"
PRIVATE_PAGE_DIR = PRIVATE_OUTPUT_DIR / "page-sides"
PRIVATE_HTML_DIR = PRIVATE_OUTPUT_DIR / "html"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "page-side-packets-private-index.csv"
PRIVATE_MASTER_HTML = PRIVATE_OUTPUT_DIR / "index.html"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_adapter_d0_d1_page_side_packets_v1"
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
    "高校源AdapterD0D1页列核验包ID",
    "来源D0D1人工核验包公开账本",
    "来源D0D1人工核验包摘要",
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
    "涉及院校代码数",
    "涉及院校代码集合SHA16",
    "涉及D0D1人工核验包数",
    "私有核验项数",
    "R0计划数冲突项数",
    "R1OCR计划数可补项数",
    "R2疑似匹配项数",
    "R3计划数一致抽检项数",
    "双人复核建议项数",
    "页列执行优先级",
    "页列最小核验动作",
    "涉及D0D1人工核验包ID集合SHA256",
    "涉及专业行ID集合SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页列CSV行数",
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

SOURCE_PRIVATE_FIELDS = [
    "高校源AdapterD0D1人工核验项ID",
    "高校源AdapterD0D1人工核验包ID",
    "高校源Adapter候选diff公开ID",
    "高校源Adapter候选diff私有明细ID",
    "院校代码",
    "院校名称OCR",
    "招生明细总工作台ID",
    "专业行ID",
    "专业组出现ID",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR",
    "OCR专业计划数候选",
    "OCR学费候选",
    "OCR再选科目候选",
    "本轮高校源匹配状态",
    "本轮专业名称匹配方式",
    "本轮专业名称匹配分",
    "本轮计划数核验状态",
    "本轮高校源覆盖结论",
    "最佳高校源文件",
    "最佳高校源证据类型",
    "最佳高校源专业名称",
    "最佳高校源计划数",
    "最佳高校源专业组",
    "最佳高校源专业代号",
    "最佳高校源学费",
    "最佳高校源选科",
    "人工核验优先级",
    "人工核验原因",
    "建议核验动作",
    *FALSE_FIELDS,
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
    "复核备注",
]

PRIVATE_PAGE_FIELDS = [
    "高校源AdapterD0D1页列核验包ID",
    "页列执行序号",
    "页列执行优先级",
    "页列最小核验动作",
    *SOURCE_PRIVATE_FIELDS,
    "PDF原页人工核验记录",
    "湖北官方计划人工核验记录",
    "高校源差异解释记录",
    "最终字段处理建议",
    "复核人A",
    "复核人B",
    "人工复核时间",
    "页列复核备注",
]

PRIVATE_INDEX_FIELDS = [
    "高校源AdapterD0D1页列核验包ID",
    "页列执行序号",
    "来源页码",
    "版面列",
    "页列执行优先级",
    "页列最小核验动作",
    "涉及院校代码集合",
    "涉及院校名称OCR集合",
    "涉及D0D1人工核验包ID集合",
    "私有核验项数",
    "R0计划数冲突项数",
    "R1OCR计划数可补项数",
    "R2疑似匹配项数",
    "R3计划数一致抽检项数",
    "私有页列CSV相对路径",
    "私有页列CSV_SHA256",
    "私有页列HTML相对路径",
    "私有页列HTML_SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
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

PRIORITY_ORDER = {
    "E0-计划数冲突页列先核": 0,
    "E1-OCR计划数缺失可补页列先核": 1,
    "E2-疑似匹配页列先核": 2,
    "E3-计划数一致抽检页列": 3,
}


def clean(value):
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


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


def local_private_path(path):
    return str(path.relative_to(PRIVATE_OUTPUT_DIR))


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


def page_side_key(row):
    return clean(row.get("来源页码", "")), clean(row.get("版面列", ""))


def side_sort_value(side):
    return {"left": 0, "左": 0, "左栏": 0, "right": 1, "右": 1, "右栏": 1}.get(side, 9)


def counter_text(counter):
    return "；".join(f"{key}:{value}" for key, value in sorted(counter.items())) if counter else ""


def priority_for_counts(counts):
    if counts.get("R0-计划数冲突优先核PDF原页", 0):
        return "E0-计划数冲突页列先核", "先核计划数冲突行；同页列其余R1/R2/R3随页一并抽查。"
    if counts.get("R1-OCR计划数缺失但高校源可补", 0):
        return "E1-OCR计划数缺失可补页列先核", "先回看PDF原页补读计划数；高校源只作提示，不能直接写回。"
    if counts.get("R2-疑似匹配专业名人工确认", 0):
        return "E2-疑似匹配页列先核", "先核名称限定词、组边界和行内编号，再判断是否同一条招生计划。"
    return "E3-计划数一致抽检页列", "作为一致性抽检页列，核PDF原页和湖北官方侧后再评估可写回。"


def sorted_items(rows):
    priority_rank = {
        "R0-计划数冲突优先核PDF原页": 0,
        "R1-OCR计划数缺失但高校源可补": 1,
        "R2-疑似匹配专业名人工确认": 2,
        "R3-计划数一致候选抽检": 3,
    }
    return sorted(
        rows,
        key=lambda row: (
            priority_rank.get(row.get("人工核验优先级", ""), 9),
            as_int(row.get("专业组内专业序号")),
            row.get("高校源AdapterD0D1人工核验项ID", ""),
        ),
    )


def html_table(rows, fields):
    lines = ["<table>", "<thead><tr>"]
    for field in fields:
        lines.append(f"<th>{html.escape(field)}</th>")
    lines.append("</tr></thead><tbody>")
    for row in rows:
        lines.append("<tr>")
        for field in fields:
            lines.append(f"<td>{html.escape(clean(row.get(field, '')))}</td>")
        lines.append("</tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


def write_page_html(packet_id, public_row, private_rows):
    path = PRIVATE_HTML_DIR / f"{packet_id}.html"
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
        "页列复核备注",
    ]
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:24px;line-height:1.45;color:#111}",
        "table{border-collapse:collapse;width:100%;font-size:12px}",
        "th,td{border:1px solid #d4d4d4;padding:6px;vertical-align:top}",
        "th{background:#f5f5f5;position:sticky;top:0}",
        ".warn{color:#9a3412;font-weight:600}",
        ".meta{color:#444;font-size:13px}",
        "</style>",
        f"<title>{html.escape(packet_id)}</title>",
        f"<h1>{html.escape(packet_id)}</h1>",
        "<p class='warn'>私有页列核验材料：含学校、专业、OCR候选和高校源差异，只能留在本地 private/ 目录。</p>",
        (
            "<p class='meta'>第 "
            f"{html.escape(public_row['来源页码'])} 页 / {html.escape(public_row['版面列'])}；"
            f"{html.escape(public_row['页列执行优先级'])}；"
            f"私有核验项 {html.escape(clean(public_row['私有核验项数']))} 条。</p>"
        ),
        f"<p class='meta'>最小动作：{html.escape(public_row['页列最小核验动作'])}</p>",
        html_table(private_rows, display_fields),
    ]
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
        "<title>D0/D1页列私有核验索引</title>",
        "<h1>D0/D1页列私有核验索引</h1>",
        "<p class='warn'>本索引仅在本地 private/ 目录保存，不进入公开仓库。</p>",
        "<table><thead><tr><th>序号</th><th>页码</th><th>版面列</th><th>优先级</th><th>明细数</th><th>CSV</th><th>HTML</th></tr></thead><tbody>",
    ]
    for row in index_rows:
        html_path = row.get("私有页列HTML相对路径", "")
        csv_path = row.get("私有页列CSV相对路径", "")
        lines.append(
            "<tr>"
            f"<td>{html.escape(clean(row.get('页列执行序号', '')))}</td>"
            f"<td>{html.escape(clean(row.get('来源页码', '')))}</td>"
            f"<td>{html.escape(clean(row.get('版面列', '')))}</td>"
            f"<td>{html.escape(clean(row.get('页列执行优先级', '')))}</td>"
            f"<td>{html.escape(clean(row.get('私有核验项数', '')))}</td>"
            f"<td><a href='{html.escape(csv_path)}'>CSV</a></td>"
            f"<td><a href='{html.escape(html_path)}'>HTML</a></td>"
            "</tr>"
        )
    lines.append("</tbody></table>")
    PRIVATE_MASTER_HTML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_rows():
    d0_d1_public_rows = read_csv(D0_D1_PUBLIC)
    source_items = read_csv(D0_D1_PRIVATE_REVIEW_ITEMS)
    public_by_packet = {
        row.get("高校源AdapterD0D1人工核验包ID", ""): row for row in d0_d1_public_rows
    }

    grouped = defaultdict(list)
    for item in source_items:
        grouped[page_side_key(item)].append(item)

    packets = []
    for (page, side), rows in grouped.items():
        counts = Counter(row.get("人工核验优先级", "") for row in rows)
        priority, action = priority_for_counts(counts)
        packets.append({
            "page": page,
            "side": side,
            "rows": sorted_items(rows),
            "counts": counts,
            "priority": priority,
            "action": action,
        })

    packets.sort(
        key=lambda packet: (
            PRIORITY_ORDER.get(packet["priority"], 9),
            as_int(packet["page"]),
            side_sort_value(packet["side"]),
            packet["side"],
        )
    )

    public_rows = []
    private_index_rows = []
    for index, packet in enumerate(packets, start=1):
        page = packet["page"]
        side = packet["side"]
        rows = packet["rows"]
        counts = packet["counts"]
        review_item_ids = [
            row.get("高校源AdapterD0D1人工核验项ID", "")
            for row in rows
            if row.get("高校源AdapterD0D1人工核验项ID", "")
        ]
        packet_id = stable_id("SSPAGE", [SOURCE_PDF_SHA256, page, side, sha16(review_item_ids)])
        d0_d1_packet_ids = sorted({
            row.get("高校源AdapterD0D1人工核验包ID", "") for row in rows if row.get("高校源AdapterD0D1人工核验包ID", "")
        })
        school_codes = sorted({row.get("院校代码", "") for row in rows if row.get("院校代码", "")})
        school_names = sorted({row.get("院校名称OCR", "") for row in rows if row.get("院校名称OCR", "")})
        major_ids = [row.get("专业行ID", "") for row in rows if row.get("专业行ID", "")]
        public_row = {
            "高校源AdapterD0D1页列核验包ID": packet_id,
            "来源D0D1人工核验包公开账本": source_path(D0_D1_PUBLIC),
            "来源D0D1人工核验包摘要": source_path(D0_D1_SUMMARY),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校源Adapter D0/D1逐专业私有核验项",
            "任务粒度": "PDF页码×版面列人工核验包",
            **false_gate_values(),
            "页列执行序号": index,
            "来源页码": page,
            "版面列": side,
            "页码版面键SHA16": sha16([page, side]),
            "涉及院校代码数": len(school_codes),
            "涉及院校代码集合SHA16": sha16(school_codes),
            "涉及D0D1人工核验包数": len(d0_d1_packet_ids),
            "私有核验项数": len(rows),
            "R0计划数冲突项数": counts.get("R0-计划数冲突优先核PDF原页", 0),
            "R1OCR计划数可补项数": counts.get("R1-OCR计划数缺失但高校源可补", 0),
            "R2疑似匹配项数": counts.get("R2-疑似匹配专业名人工确认", 0),
            "R3计划数一致抽检项数": counts.get("R3-计划数一致候选抽检", 0),
            "双人复核建议项数": counts.get("R0-计划数冲突优先核PDF原页", 0)
            + counts.get("R2-疑似匹配专业名人工确认", 0),
            "页列执行优先级": packet["priority"],
            "页列最小核验动作": packet["action"],
            "涉及D0D1人工核验包ID集合SHA256": sha16(d0_d1_packet_ids),
            "涉及专业行ID集合SHA256": sha16(major_ids),
            "私有页列CSV证据编号": f"local_school_source_adapter_d0_d1_page_side_csv_{index:03d}_not_public",
            "私有页列CSV_SHA256": "filled_after_write",
            "私有页列CSV行数": len(rows),
            "私有页列HTML证据编号": f"local_school_source_adapter_d0_d1_page_side_html_{index:03d}_not_public",
            "私有页列HTML_SHA256": "filled_after_write",
            "私有页列索引CSV_SHA256": "filled_after_write",
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网结构化源状态": "structured_school_source_candidate_not_verified",
            "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
            "公开安全策略": "公开层只保留页码、版面列、计数和SHA；学校名、专业名、OCR候选、高校源读数与人工备注只留在本地私有材料。",
            "下一步": "按页列打开私有CSV/HTML，对照第19期PDF原页与湖北官方侧核验；未闭环前不得写回字段事实或生成最终志愿建议。",
        }

        private_rows = []
        for source_row in rows:
            private_rows.append({
                "高校源AdapterD0D1页列核验包ID": packet_id,
                "页列执行序号": index,
                "页列执行优先级": packet["priority"],
                "页列最小核验动作": packet["action"],
                **source_row,
                "PDF原页人工核验记录": "",
                "湖北官方计划人工核验记录": "",
                "高校源差异解释记录": "",
                "最终字段处理建议": "",
                "复核人A": "",
                "复核人B": "",
                "人工复核时间": "",
                "页列复核备注": "",
            })

        csv_path = PRIVATE_PAGE_DIR / f"{packet_id}.csv"
        write_csv(csv_path, private_rows, PRIVATE_PAGE_FIELDS)
        html_path = write_page_html(packet_id, public_row, private_rows)
        csv_sha = sha256(csv_path)
        html_sha = sha256(html_path)
        public_row["私有页列CSV_SHA256"] = csv_sha
        public_row["私有页列HTML_SHA256"] = html_sha

        private_index_rows.append({
            "高校源AdapterD0D1页列核验包ID": packet_id,
            "页列执行序号": index,
            "来源页码": page,
            "版面列": side,
            "页列执行优先级": packet["priority"],
            "页列最小核验动作": packet["action"],
            "涉及院校代码集合": "；".join(school_codes),
            "涉及院校名称OCR集合": "；".join(school_names),
            "涉及D0D1人工核验包ID集合": "；".join(d0_d1_packet_ids),
            "私有核验项数": len(rows),
            "R0计划数冲突项数": counts.get("R0-计划数冲突优先核PDF原页", 0),
            "R1OCR计划数可补项数": counts.get("R1-OCR计划数缺失但高校源可补", 0),
            "R2疑似匹配项数": counts.get("R2-疑似匹配专业名人工确认", 0),
            "R3计划数一致抽检项数": counts.get("R3-计划数一致候选抽检", 0),
            "私有页列CSV相对路径": local_private_path(csv_path),
            "私有页列CSV_SHA256": csv_sha,
            "私有页列HTML相对路径": local_private_path(html_path),
            "私有页列HTML_SHA256": html_sha,
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网结构化源状态": "structured_school_source_candidate_not_verified",
            "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
        })
        public_rows.append(public_row)

        for packet_id_value in d0_d1_packet_ids:
            if packet_id_value not in public_by_packet:
                raise SystemExit(f"unknown d0/d1 packet id: {packet_id_value}")

    write_csv(PRIVATE_INDEX, private_index_rows, PRIVATE_INDEX_FIELDS)
    write_master_html(private_index_rows)
    private_index_sha = sha256(PRIVATE_INDEX)
    private_master_html_sha = sha256(PRIVATE_MASTER_HTML)
    for row in public_rows:
        row["私有页列索引CSV_SHA256"] = private_index_sha

    return public_rows, private_index_rows, private_index_sha, private_master_html_sha


def build_summary(public_rows, private_index_rows, private_index_sha, private_master_html_sha):
    priority_counts = Counter(row["页列执行优先级"] for row in public_rows)
    review_item_counts = Counter()
    for row in public_rows:
        review_item_counts["R0-计划数冲突优先核PDF原页"] += as_int(row.get("R0计划数冲突项数"))
        review_item_counts["R1-OCR计划数缺失但高校源可补"] += as_int(row.get("R1OCR计划数可补项数"))
        review_item_counts["R2-疑似匹配专业名人工确认"] += as_int(row.get("R2疑似匹配项数"))
        review_item_counts["R3-计划数一致候选抽检"] += as_int(row.get("R3计划数一致抽检项数"))
    return {
        "status": "issue19_school_source_adapter_d0_d1_page_side_packets_v1_not_final",
        "generated_by": "build_issue19_school_source_adapter_d0_d1_page_side_packets_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_d0_d1_public": source_path(D0_D1_PUBLIC),
        "source_d0_d1_summary": source_path(D0_D1_SUMMARY),
        "output_public_table": source_path(PUBLIC_OUTPUT),
        "row_count": len(public_rows),
        "private_page_index_row_count": len(private_index_rows),
        "private_review_item_count": sum(as_int(row.get("私有核验项数")) for row in public_rows),
        "page_priority_counts": dict(sorted(priority_counts.items())),
        "review_priority_counts": dict(sorted(review_item_counts.items())),
        "plan_conflict_review_item_count": review_item_counts.get("R0-计划数冲突优先核PDF原页", 0),
        "ocr_plan_missing_review_item_count": review_item_counts.get("R1-OCR计划数缺失但高校源可补", 0),
        "possible_match_review_item_count": review_item_counts.get("R2-疑似匹配专业名人工确认", 0),
        "plan_match_sample_review_item_count": review_item_counts.get("R3-计划数一致候选抽检", 0),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "final_available_count": 0,
        "private_page_index_csv_sha256": private_index_sha,
        "private_master_html_sha256": private_master_html_sha,
        "public_boundary": "公开表只保存页列任务计数、状态和私有文件SHA；逐专业明细与人工记录留在Git忽略私有目录。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"adapter d0/d1 page-side packets contains forbidden public tokens: {hits[:10]}")


def main():
    public_rows, private_index_rows, private_index_sha, private_master_html_sha = build_rows()
    summary = build_summary(public_rows, private_index_rows, private_index_sha, private_master_html_sha)
    assert_public_safe(public_rows, summary)
    write_csv(PUBLIC_OUTPUT, public_rows, PUBLIC_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(PUBLIC_OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")
    print(f"private page-side packets: {len(private_index_rows)}")


if __name__ == "__main__":
    main()
