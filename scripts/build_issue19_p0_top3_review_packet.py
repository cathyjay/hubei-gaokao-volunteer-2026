#!/usr/bin/env python3
import csv
import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data/exports"
WORKING = ROOT / "data/working"
PRIVATE_ROOT = ROOT / "private"

P0_PACKAGES = EXPORTS / "issue19-data-foundation-next-execution-v1-p0-conflict-packages.csv"
P0_TASKS = EXPORTS / "issue19-data-foundation-next-execution-v1-p0-conflict-tasks.csv"
FIELD_PUBLIC = WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
FIELD_PRIVATE = (
    PRIVATE_ROOT
    / "review-assets/issue19-stable-foundation-first-closure-field-confirmation/first-closure-field-confirmation-private-workbench.csv"
)

PRIVATE_OUTPUT_DIR = PRIVATE_ROOT / "review-assets/issue19-p0-top3-review-packet"
PRIVATE_HTML_DIR = PRIVATE_OUTPUT_DIR / "html"
PRIVATE_TASK_CSV = PRIVATE_OUTPUT_DIR / "p0-top3-private-tasks.csv"
PRIVATE_FIELD_CSV = PRIVATE_OUTPUT_DIR / "p0-top3-private-field-review.csv"
PRIVATE_INDEX_CSV = PRIVATE_OUTPUT_DIR / "p0-top3-private-index.csv"
PRIVATE_MASTER_HTML = PRIVATE_OUTPUT_DIR / "index.html"

PUBLIC_LEDGER = WORKING / "issue19-p0-top3-review-packet-public-ledger.csv"
PUBLIC_FIELD_LEDGER = WORKING / "issue19-p0-top3-field-review-public-ledger.csv"
PUBLIC_SUMMARY = WORKING / "issue19-p0-top3-review-packet-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_p0_top3_private_review_packet_public_ledger"
TOP_PAGE_SIDES = ["135-left", "199-left", "209-right"]

PUBLIC_FIELDS = [
    "P0Top3公开复核包ID",
    "来源P0冲突包表",
    "来源P0冲突任务表",
    "来源第一闭环字段确认公开账本",
    "来源私有复核材料",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许字段写回",
    "公开包总序",
    "核验包编号",
    "页码版面",
    "来源页码",
    "版面列",
    "包内任务数",
    "双人复核任务数",
    "人工看图任务数",
    "高校辅证任务数",
    "PDF原页待记录任务数",
    "湖北官方待记录任务数",
    "高校辅证待记录任务数",
    "三方一致性待确认任务数",
    "字段写回ready任务数",
    "字段写回blocked任务数",
    "涉及任务ID集合SHA256",
    "涉及专业行ID集合SHA256",
    "涉及院校代码集合SHA256",
    "涉及专业组代码集合SHA256",
    "涉及专业代号集合SHA256",
    "私有任务CSV证据编号",
    "私有页HTML证据编号",
    "私有页图证据编号",
    "私有OCR文本证据编号",
    "私有任务CSV_SHA256",
    "私有页HTML_SHA256",
    "私有页图_SHA256",
    "私有OCR文本_SHA256",
    "私有材料状态",
    "字段事实写回状态",
    "下一步",
    "公开安全边界",
]

PRIVATE_TASK_FIELDS = [
    "P0Top3私有复核任务ID",
    "P0Top3公开复核包ID",
    "核验包编号",
    "页码版面",
    "来源页码",
    "版面列",
    "院校代码",
    "院校名称",
    "院校专业组代码",
    "专业代号",
    "专业名称短摘",
    "字段范围",
    "任务来源类型",
    "公开冲突桶",
    "候选提示桶",
    "PDFOCR提示状态",
    "机器坐标提示状态",
    "高校辅证线索",
    "是否需要双人复核",
    "是否需要人工看图",
    "专业行ID",
    "第一闭环任务ID",
    "第一闭环字段确认公开账本ID",
    "PDFOCR计划数候选值",
    "PDFOCR学费候选值",
    "PDFOCR选科候选值",
    "高校辅证计划数候选值",
    "高校辅证学费候选值",
    "高校辅证选科候选值",
    "OCR行文本",
    "私有页图相对路径",
    "私有OCR文本相对路径",
    "PDF原页专业代号读数",
    "PDF原页专业名称读数",
    "PDF原页专业计划数读数",
    "PDF原页学费读数",
    "PDF原页再选科目读数",
    "PDF原页专业组边界备注",
    "湖北官方专业代号",
    "湖北官方专业名称",
    "湖北官方专业计划数",
    "湖北官方学费",
    "湖北官方再选科目",
    "高校官网或招生章程专业计划数",
    "高校官网或招生章程学费",
    "高校官网或招生章程再选科目",
    "字段确认值",
    "PDF核页复核人A",
    "PDF核页复核人B",
    "湖北官方核验人",
    "高校辅证核验人",
    "三方一致性结论",
    "字段事实写回建议",
    "人工复核备注",
]

PRIVATE_FIELD_FIELDS = [
    "P0Top3私有字段核验ID",
    "P0Top3字段公开账本ID",
    "P0Top3私有复核任务ID",
    "P0Top3公开复核包ID",
    "核验包编号",
    "页码版面",
    "来源页码",
    "版面列",
    "院校代码",
    "院校名称",
    "院校专业组代码",
    "专业代号",
    "专业名称短摘",
    "专业行ID",
    "第一闭环任务ID",
    "第一闭环字段确认公开账本ID",
    "字段名",
    "字段候选关系桶",
    "PDFOCR字段候选值",
    "高校辅证字段候选值",
    "PDF原页字段人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "字段确认来源组合",
    "PDF核页复核人A",
    "PDF核页复核人B",
    "湖北官方核验人",
    "高校辅证核验人",
    "双人一致性结论",
    "三方一致性结论",
    "字段事实写回建议",
    "人工复核备注",
]

PUBLIC_FIELD_FIELDS = [
    "P0Top3字段公开账本ID",
    "来源P0Top3公开复核包台账",
    "来源P0Top3私有字段核验表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许字段写回",
    "字段总序",
    "P0Top3公开复核包ID",
    "核验包编号",
    "页码版面",
    "来源页码",
    "版面列",
    "字段名",
    "字段候选关系桶",
    "PDFOCR字段候选状态",
    "高校辅证字段候选状态",
    "是否需要双人复核",
    "是否需要人工看图",
    "PDF原页待记录状态",
    "湖北官方待记录状态",
    "高校辅证待记录状态",
    "三方一致性状态",
    "字段事实写回状态",
    "来源任务ID_SHA256",
    "来源专业行ID_SHA256",
    "来源院校代码_SHA256",
    "来源专业组代码_SHA256",
    "来源专业代号_SHA256",
    "私有字段核验表证据编号",
    "私有字段核验表_SHA256",
    "私有字段线索_SHA256",
    "下一步",
    "公开安全边界",
]

PRIVATE_INDEX_FIELDS = [
    "P0Top3公开复核包ID",
    "核验包编号",
    "页码版面",
    "来源页码",
    "版面列",
    "包内任务数",
    "双人复核任务数",
    "私有页HTML相对路径",
    "私有页HTML_SHA256",
    "私有页图相对路径",
    "私有页图_SHA256",
    "私有OCR文本相对路径",
    "私有OCR文本_SHA256",
    "私有任务CSV_SHA256",
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
    "OCR行文本",
    "PDFOCR计划数候选值",
    "PDFOCR学费候选值",
    "PDFOCR选科候选值",
    "高校辅证计划数候选值",
    "高校辅证学费候选值",
    "高校辅证选科候选值",
    "PDF原页专业代号读数",
    "PDF原页专业名称读数",
    "PDF原页专业计划数读数",
    "PDF原页学费读数",
    "PDF原页再选科目读数",
    "湖北官方专业计划数",
    "湖北官方学费",
    "字段确认值",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_values(values):
    text = "；".join(sorted({str(value) for value in values if value}))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def page_number(page_side):
    match = re.match(r"0*(\d+)-", page_side)
    if not match:
        return ""
    return match.group(1)


def page_image_path(page):
    return PRIVATE_ROOT / f"ocr-runs/issue19-full-120dpi/rendered-pages/page-{page}.png"


def page_text_path(page):
    return PRIVATE_ROOT / f"ocr-runs/issue19-full-120dpi/text/{page}_page-{page}.txt"


def private_rel(path):
    return path.relative_to(PRIVATE_ROOT).as_posix()


def html_rel_from_page_html(path):
    return Path("../..") / path.relative_to(PRIVATE_ROOT)


def build_private_task_rows(package_rows, task_rows, private_field_by_task):
    private_rows = []
    package_by_key = {row["页码版面"]: row for row in package_rows}
    for task in task_rows:
        page_side = task["页码版面键"]
        package = package_by_key[page_side]
        private_field = private_field_by_task.get(task["第一闭环任务ID"], {})
        private_rows.append({
            "P0Top3私有复核任务ID": stable_id("P0TOP3TASK", [task["第一闭环任务ID"]]),
            "P0Top3公开复核包ID": stable_id("P0TOP3PACK", [page_side, task["核验包编号"]]),
            "核验包编号": task["核验包编号"],
            "页码版面": page_side,
            "来源页码": package.get("来源页码", ""),
            "版面列": package.get("版面列", ""),
            "院校代码": task.get("院校代码", ""),
            "院校名称": task.get("院校名称", ""),
            "院校专业组代码": task.get("院校专业组代码", ""),
            "专业代号": task.get("专业代号", ""),
            "专业名称短摘": task.get("专业名称短摘", ""),
            "字段范围": task.get("字段范围", ""),
            "任务来源类型": task.get("任务来源类型", ""),
            "公开冲突桶": task.get("公开冲突桶", ""),
            "候选提示桶": task.get("候选提示桶", ""),
            "PDFOCR提示状态": task.get("PDFOCR提示状态", ""),
            "机器坐标提示状态": task.get("机器坐标提示状态", ""),
            "高校辅证线索": task.get("高校辅证线索", ""),
            "是否需要双人复核": task.get("是否需要双人复核", ""),
            "是否需要人工看图": task.get("是否需要人工看图", ""),
            "专业行ID": task.get("专业行ID", ""),
            "第一闭环任务ID": task.get("第一闭环任务ID", ""),
            "第一闭环字段确认公开账本ID": private_field.get("第一闭环字段确认公开账本ID", ""),
            "PDFOCR计划数候选值": private_field.get("PDFOCR计划数候选值", ""),
            "PDFOCR学费候选值": private_field.get("PDFOCR学费候选值", ""),
            "PDFOCR选科候选值": private_field.get("PDFOCR选科候选值", ""),
            "高校辅证计划数候选值": private_field.get("高校辅证计划数候选值", ""),
            "高校辅证学费候选值": private_field.get("高校辅证学费候选值", ""),
            "高校辅证选科候选值": private_field.get("高校辅证选科候选值", ""),
            "OCR行文本": private_field.get("OCR行文本", ""),
            "私有页图相对路径": private_field.get("私有页图相对路径", "") or private_rel(page_image_path(package.get("来源页码", ""))),
            "私有OCR文本相对路径": private_field.get("私有OCR文本相对路径", "") or private_rel(page_text_path(package.get("来源页码", ""))),
        })
    return private_rows


def split_fields(value):
    return [part.strip() for part in str(value or "").split("；") if part.strip()]


def field_candidate_values(row, field_name):
    if field_name == "专业计划数":
        return row.get("PDFOCR计划数候选值", ""), row.get("高校辅证计划数候选值", "")
    if field_name == "学费":
        return row.get("PDFOCR学费候选值", ""), row.get("高校辅证学费候选值", "")
    if field_name == "再选科目":
        return row.get("PDFOCR选科候选值", ""), row.get("高校辅证选科候选值", "")
    return "", ""


def relation_bucket(pdf_value, school_value):
    if pdf_value and school_value and pdf_value == school_value:
        return "R1-候选一致"
    if pdf_value and school_value and pdf_value != school_value:
        return "R0-候选冲突"
    if pdf_value and not school_value:
        return "R2-仅PDFOCR候选"
    if school_value and not pdf_value:
        return "R3-仅高校辅证候选"
    return "R4-候选均缺"


def clue_hash(row):
    parts = [
        row.get("P0Top3私有字段核验ID", ""),
        row.get("第一闭环任务ID", ""),
        row.get("字段名", ""),
        row.get("字段候选关系桶", ""),
        row.get("PDFOCR字段候选值", ""),
        row.get("高校辅证字段候选值", ""),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def build_private_field_rows(private_task_rows):
    rows = []
    for task in private_task_rows:
        for field_name in split_fields(task.get("字段范围", "")):
            pdf_value, school_value = field_candidate_values(task, field_name)
            private_field_id = stable_id(
                "P0TOP3FIELD",
                [task.get("第一闭环任务ID", ""), field_name],
            )
            public_field_id = stable_id(
                "P0TOP3FPUB",
                [task.get("第一闭环任务ID", ""), field_name],
            )
            rows.append({
                "P0Top3私有字段核验ID": private_field_id,
                "P0Top3字段公开账本ID": public_field_id,
                "P0Top3私有复核任务ID": task.get("P0Top3私有复核任务ID", ""),
                "P0Top3公开复核包ID": task.get("P0Top3公开复核包ID", ""),
                "核验包编号": task.get("核验包编号", ""),
                "页码版面": task.get("页码版面", ""),
                "来源页码": task.get("来源页码", ""),
                "版面列": task.get("版面列", ""),
                "院校代码": task.get("院校代码", ""),
                "院校名称": task.get("院校名称", ""),
                "院校专业组代码": task.get("院校专业组代码", ""),
                "专业代号": task.get("专业代号", ""),
                "专业名称短摘": task.get("专业名称短摘", ""),
                "专业行ID": task.get("专业行ID", ""),
                "第一闭环任务ID": task.get("第一闭环任务ID", ""),
                "第一闭环字段确认公开账本ID": task.get("第一闭环字段确认公开账本ID", ""),
                "字段名": field_name,
                "字段候选关系桶": relation_bucket(pdf_value, school_value),
                "PDFOCR字段候选值": pdf_value,
                "高校辅证字段候选值": school_value,
            })
    return rows


def build_public_field_rows(private_field_rows, private_field_csv_sha):
    public_rows = []
    for index, row in enumerate(private_field_rows, start=1):
        pdf_status = "has_pdfocr_candidate" if row.get("PDFOCR字段候选值") else "missing_pdfocr_candidate"
        school_status = (
            "has_school_evidence_candidate"
            if row.get("高校辅证字段候选值")
            else "missing_school_evidence_candidate"
        )
        public_rows.append({
            "P0Top3字段公开账本ID": row.get("P0Top3字段公开账本ID", ""),
            "来源P0Top3公开复核包台账": "data/working/issue19-p0-top3-review-packet-public-ledger.csv",
            "来源P0Top3私有字段核验表": "p0_top3_private_field_review_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": "issue19_p0_top3_field_review_public_ledger",
            "主表粒度": "逐字段",
            "任务粒度": "P0冲突top3×专业行×字段",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "是否允许字段写回": "false",
            "字段总序": str(index),
            "P0Top3公开复核包ID": row.get("P0Top3公开复核包ID", ""),
            "核验包编号": row.get("核验包编号", ""),
            "页码版面": row.get("页码版面", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "字段名": row.get("字段名", ""),
            "字段候选关系桶": row.get("字段候选关系桶", ""),
            "PDFOCR字段候选状态": pdf_status,
            "高校辅证字段候选状态": school_status,
            "是否需要双人复核": "true",
            "是否需要人工看图": "true",
            "PDF原页待记录状态": "pending_private_pdf_field_reading",
            "湖北官方待记录状态": "pending_private_hubei_field_reading",
            "高校辅证待记录状态": "pending_private_school_field_reading",
            "三方一致性状态": "pending_private_three_way_field_confirmation",
            "字段事实写回状态": "blocked_until_private_field_readings_complete",
            "来源任务ID_SHA256": hashlib.sha256(row.get("第一闭环任务ID", "").encode("utf-8")).hexdigest(),
            "来源专业行ID_SHA256": hashlib.sha256(row.get("专业行ID", "").encode("utf-8")).hexdigest(),
            "来源院校代码_SHA256": hashlib.sha256(row.get("院校代码", "").encode("utf-8")).hexdigest(),
            "来源专业组代码_SHA256": hashlib.sha256(row.get("院校专业组代码", "").encode("utf-8")).hexdigest(),
            "来源专业代号_SHA256": hashlib.sha256(row.get("专业代号", "").encode("utf-8")).hexdigest(),
            "私有字段核验表证据编号": "P0TOP3-PRIVATE-FIELD-REVIEW-CSV",
            "私有字段核验表_SHA256": private_field_csv_sha,
            "私有字段线索_SHA256": clue_hash(row),
            "下一步": "在私有字段核验表逐字段补PDF原页、湖北官方侧和高校辅证字段值；三方闭环前不得写回。",
            "公开安全边界": "公开层只保存字段名、状态、关系桶、证据编号和SHA；不保存候选值、人工读数、院校专业明细或复核备注。",
        })
    return public_rows


def write_page_html(public_id, package, rows, page_image, page_text, task_csv_sha):
    page_side = package["页码版面"]
    html_path = PRIVATE_HTML_DIR / f"{page_side}.html"
    page_text_value = page_text.read_text(encoding="utf-8", errors="ignore") if page_text.exists() else ""
    img_rel = html_rel_from_page_html(page_image).as_posix() if page_image.exists() else ""
    task_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row.get('专业代号',''))}</td>"
        f"<td>{html.escape(row.get('专业名称短摘',''))}</td>"
        f"<td>{html.escape(row.get('字段范围',''))}</td>"
        f"<td>{html.escape(row.get('PDFOCR计划数候选值',''))}</td>"
        f"<td>{html.escape(row.get('PDFOCR学费候选值',''))}</td>"
        f"<td>{html.escape(row.get('高校辅证计划数候选值',''))}</td>"
        f"<td>{html.escape(row.get('高校辅证学费候选值',''))}</td>"
        f"<td>{html.escape(row.get('是否需要双人复核',''))}</td>"
        "</tr>"
        for row in rows
    )
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:24px;line-height:1.45;color:#111}",
        ".warning{color:#9a3412;font-weight:700}",
        "img{max-width:100%;border:1px solid #ddd;background:white}",
        "table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0}",
        "td,th{border:1px solid #ddd;padding:6px;vertical-align:top}",
        "pre{white-space:pre-wrap;background:#f7f7f7;padding:12px;border:1px solid #ddd}",
        "</style>",
        f"<title>P0 top3 {html.escape(page_side)}</title>",
        f"<h1>P0 top3 私有复核包：{html.escape(page_side)}</h1>",
        "<p class='warning'>私有核验材料：只用于本机看原页和填读数，不提交公开仓库。公开层只同步状态、计数和 SHA。</p>",
        f"<p>公开复核包 ID：{html.escape(public_id)}；核验包编号：{html.escape(package['核验包编号'])}；私有任务 CSV SHA：{html.escape(task_csv_sha)}</p>",
        "<h2>原页图</h2>",
    ]
    if img_rel:
        lines.append(f"<img src='{html.escape(img_rel)}' alt='{html.escape(page_side)}'>")
    else:
        lines.append("<p>未找到页图，请回 PDF 原件核页。</p>")
    lines.extend([
        "<h2>包内任务</h2>",
        "<table>",
        "<tr><th>专业代号</th><th>专业名称</th><th>字段范围</th><th>PDFOCR计划数</th><th>PDFOCR学费</th><th>高校计划数</th><th>高校学费</th><th>双人复核</th></tr>",
        task_rows,
        "</table>",
        "<h2>人工填写位置</h2>",
        "<p>请在 <code>p0-top3-private-tasks.csv</code> 中补齐 PDF 原页读数、湖北官方字段值、高校辅证值、三方一致性结论和复核人。</p>",
        "<h2>OCR 文本线索</h2>",
        f"<pre>{html.escape(page_text_value)}</pre>",
    ])
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return html_path


def write_master_html(index_rows):
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<title>P0 top3 私有复核包</title>",
        "<h1>P0 top3 私有复核包</h1>",
        "<p>从 135-left、199-left、209-right 开始，先完成 PDF 原页、湖北官方侧、高校侧和双人复核闭环。</p>",
        "<ol>",
    ]
    for row in index_rows:
        rel = row["私有页HTML相对路径"]
        lines.append(
            f"<li><a href='{html.escape(rel)}'>{html.escape(row['页码版面'])}</a>："
            f"{html.escape(row['包内任务数'])} 个任务，"
            f"{html.escape(row['双人复核任务数'])} 个双人复核</li>"
        )
    lines.extend(["</ol>", "<p>本目录位于 Git 忽略区，不提交公开仓库。</p>"])
    PRIVATE_MASTER_HTML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def public_safety_check():
    text = (
        PUBLIC_LEDGER.read_text(encoding="utf-8", errors="ignore")
        + PUBLIC_FIELD_LEDGER.read_text(encoding="utf-8", errors="ignore")
        + PUBLIC_SUMMARY.read_text(encoding="utf-8", errors="ignore")
    )
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise RuntimeError(f"public output contains forbidden tokens: {hits}")


def main():
    packages_all = read_csv(P0_PACKAGES)
    tasks_all = read_csv(P0_TASKS)
    field_public_rows = read_csv(FIELD_PUBLIC)
    field_private_rows = read_csv(FIELD_PRIVATE)

    public_field_by_task = {
        row.get("稳定基座第一闭环明细任务ID", ""): row for row in field_public_rows
    }
    private_field_by_task = {
        row.get("稳定基座第一闭环明细任务ID", ""): row for row in field_private_rows
    }

    packages = [row for row in packages_all if row.get("页码版面") in TOP_PAGE_SIDES]
    package_by_key = {row["页码版面"]: row for row in packages}
    tasks = [row for row in tasks_all if row.get("页码版面键") in TOP_PAGE_SIDES]
    tasks_by_page_side = {
        key: [row for row in tasks if row.get("页码版面键") == key] for key in TOP_PAGE_SIDES
    }

    if set(package_by_key) != set(TOP_PAGE_SIDES):
        raise RuntimeError("top3 package set mismatch")
    if sum(len(rows) for rows in tasks_by_page_side.values()) != 15:
        raise RuntimeError("top3 task count mismatch")
    missing_private = [row["第一闭环任务ID"] for row in tasks if row["第一闭环任务ID"] not in private_field_by_task]
    if missing_private:
        raise RuntimeError(f"missing private field rows: {missing_private[:5]}")
    missing_public = [row["第一闭环任务ID"] for row in tasks if row["第一闭环任务ID"] not in public_field_by_task]
    if missing_public:
        raise RuntimeError(f"missing public field rows: {missing_public[:5]}")

    PRIVATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PRIVATE_HTML_DIR.mkdir(parents=True, exist_ok=True)

    private_task_rows = build_private_task_rows(packages, tasks, private_field_by_task)
    write_csv(PRIVATE_TASK_CSV, private_task_rows, PRIVATE_TASK_FIELDS)
    private_task_csv_sha = sha256_file(PRIVATE_TASK_CSV)
    private_field_rows = build_private_field_rows(private_task_rows)
    write_csv(PRIVATE_FIELD_CSV, private_field_rows, PRIVATE_FIELD_FIELDS)
    private_field_csv_sha = sha256_file(PRIVATE_FIELD_CSV)
    public_field_rows = build_public_field_rows(private_field_rows, private_field_csv_sha)
    write_csv(PUBLIC_FIELD_LEDGER, public_field_rows, PUBLIC_FIELD_FIELDS)

    public_rows = []
    private_index_rows = []
    for index, page_side in enumerate(TOP_PAGE_SIDES, start=1):
        package = package_by_key[page_side]
        rows = tasks_by_page_side[page_side]
        private_rows = [row for row in private_task_rows if row["页码版面"] == page_side]
        public_id = stable_id("P0TOP3PACK", [page_side, package["核验包编号"]])
        page = package["来源页码"] or page_number(page_side)
        image = page_image_path(page)
        text = page_text_path(page)
        html_path = write_page_html(public_id, package, private_rows, image, text, private_task_csv_sha)
        html_sha = sha256_file(html_path)
        image_sha = sha256_file(image) if image.exists() else ""
        text_sha = sha256_file(text) if text.exists() else ""
        counter = Counter(row.get("字段写回状态", "") for row in rows)
        public_row = {
            "P0Top3公开复核包ID": public_id,
            "来源P0冲突包表": "data/exports/issue19-data-foundation-next-execution-v1-p0-conflict-packages.csv",
            "来源P0冲突任务表": "data/exports/issue19-data-foundation-next-execution-v1-p0-conflict-tasks.csv",
            "来源第一闭环字段确认公开账本": "data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv",
            "来源私有复核材料": "p0_top3_private_review_packet_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×P0冲突top3私有复核包",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "是否允许字段写回": "false",
            "公开包总序": str(index),
            "核验包编号": package["核验包编号"],
            "页码版面": page_side,
            "来源页码": package["来源页码"],
            "版面列": package["版面列"],
            "包内任务数": str(len(rows)),
            "双人复核任务数": str(sum(row.get("是否需要双人复核") == "true" for row in rows)),
            "人工看图任务数": str(sum(row.get("是否需要人工看图") == "true" for row in rows)),
            "高校辅证任务数": str(sum(row.get("高校辅证线索") == "true" for row in rows)),
            "PDF原页待记录任务数": str(sum(row.get("PDF原页记录状态") == "pending_private_pdf_reading" for row in rows)),
            "湖北官方待记录任务数": str(sum(row.get("湖北官方记录状态") == "pending_private_hubei_reading" for row in rows)),
            "高校辅证待记录任务数": str(sum(row.get("高校辅证记录状态") == "pending_private_school_reading" for row in rows)),
            "三方一致性待确认任务数": str(sum(row.get("三方一致性状态") == "pending_private_three_way_field_confirmation" for row in rows)),
            "字段写回ready任务数": str(counter.get("ready_for_manual_field_writeback_review", 0)),
            "字段写回blocked任务数": str(counter.get("blocked_until_required_private_readings_complete", 0)),
            "涉及任务ID集合SHA256": sha256_values(row.get("第一闭环任务ID", "") for row in rows),
            "涉及专业行ID集合SHA256": sha256_values(row.get("专业行ID", "") for row in rows),
            "涉及院校代码集合SHA256": sha256_values(row.get("院校代码", "") for row in rows),
            "涉及专业组代码集合SHA256": sha256_values(row.get("院校专业组代码", "") for row in rows),
            "涉及专业代号集合SHA256": sha256_values(row.get("专业代号", "") for row in rows),
            "私有任务CSV证据编号": "P0TOP3-PRIVATE-TASKS-CSV",
            "私有页HTML证据编号": f"P0TOP3-PRIVATE-HTML-{page_side}",
            "私有页图证据编号": f"P0TOP3-PRIVATE-PAGE-IMAGE-{page}",
            "私有OCR文本证据编号": f"P0TOP3-PRIVATE-OCR-TEXT-{page}",
            "私有任务CSV_SHA256": private_task_csv_sha,
            "私有页HTML_SHA256": html_sha,
            "私有页图_SHA256": image_sha,
            "私有OCR文本_SHA256": text_sha,
            "私有材料状态": "private_review_packet_generated_not_reviewed",
            "字段事实写回状态": "blocked_until_private_pdf_hubei_school_double_review_closed",
            "下一步": "按私有复核包回看PDF原页，补湖北官方侧和高校辅证值；同步公开状态前不得写回字段事实。",
            "公开安全边界": "公开层只保存状态、计数、证据编号、集合SHA和私有材料SHA；不保存页图路径、OCR文本、字段读数、学校专业明细人工备注。",
        }
        public_rows.append(public_row)
        private_index_rows.append({
            "P0Top3公开复核包ID": public_id,
            "核验包编号": package["核验包编号"],
            "页码版面": page_side,
            "来源页码": package["来源页码"],
            "版面列": package["版面列"],
            "包内任务数": str(len(rows)),
            "双人复核任务数": public_row["双人复核任务数"],
            "私有页HTML相对路径": html_path.relative_to(PRIVATE_OUTPUT_DIR).as_posix(),
            "私有页HTML_SHA256": html_sha,
            "私有页图相对路径": private_rel(image) if image.exists() else "",
            "私有页图_SHA256": image_sha,
            "私有OCR文本相对路径": private_rel(text) if text.exists() else "",
            "私有OCR文本_SHA256": text_sha,
            "私有任务CSV_SHA256": private_task_csv_sha,
        })

    write_csv(PRIVATE_INDEX_CSV, private_index_rows, PRIVATE_INDEX_FIELDS)
    write_master_html(private_index_rows)
    write_csv(PUBLIC_LEDGER, public_rows, PUBLIC_FIELDS)

    summary = {
        "status": "issue19_p0_top3_review_packet_ready_not_final",
        "generated_by": "build_issue19_p0_top3_review_packet.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "usage_boundary": "用于把P0冲突top3转成私有人工复核入口；不确认字段事实，不允许字段写回，不作为志愿推荐依据。",
        "output_public_ledger": "data/working/issue19-p0-top3-review-packet-public-ledger.csv",
        "source_private_review_material": "p0_top3_private_review_packet_not_public",
        "top_page_sides": TOP_PAGE_SIDES,
        "public_package_count": len(public_rows),
        "private_task_count": len(private_task_rows),
        "private_field_review_row_count": len(private_field_rows),
        "public_field_review_row_count": len(public_field_rows),
        "unique_task_count": len({row["第一闭环任务ID"] for row in private_task_rows}),
        "unique_field_task_count": len({row["P0Top3私有字段核验ID"] for row in private_field_rows}),
        "unique_page_side_count": len({row["页码版面"] for row in private_task_rows}),
        "field_name_counts": dict(Counter(row.get("字段名", "") for row in private_field_rows)),
        "field_candidate_relation_counts": dict(
            Counter(row.get("字段候选关系桶", "") for row in private_field_rows)
        ),
        "double_review_task_count": sum(row.get("是否需要双人复核") == "true" for row in tasks),
        "double_review_field_count": len(private_field_rows),
        "school_evidence_task_count": sum(row.get("高校辅证线索") == "true" for row in tasks),
        "field_pdf_pending_count": len(private_field_rows),
        "field_hubei_pending_count": len(private_field_rows),
        "field_school_pending_count": len(private_field_rows),
        "field_three_way_pending_count": len(private_field_rows),
        "pdf_pending_task_count": sum(row.get("PDF原页记录状态") == "pending_private_pdf_reading" for row in tasks),
        "hubei_pending_task_count": sum(row.get("湖北官方记录状态") == "pending_private_hubei_reading" for row in tasks),
        "school_pending_task_count": sum(row.get("高校辅证记录状态") == "pending_private_school_reading" for row in tasks),
        "three_way_pending_task_count": sum(row.get("三方一致性状态") == "pending_private_three_way_field_confirmation" for row in tasks),
        "field_writeback_ready_count": sum(row.get("字段写回状态") == "ready_for_manual_field_writeback_review" for row in tasks),
        "field_review_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "field_writeback_allowed_count": 0,
        "private_task_csv_sha256": private_task_csv_sha,
        "private_field_review_csv_sha256": private_field_csv_sha,
        "private_index_csv_sha256": sha256_file(PRIVATE_INDEX_CSV),
        "private_master_html_sha256": sha256_file(PRIVATE_MASTER_HTML),
        "private_page_html_count": len(private_index_rows),
        "hashes": {
            "public_ledger_sha256": sha256_file(PUBLIC_LEDGER),
            "public_field_ledger_sha256": sha256_file(PUBLIC_FIELD_LEDGER),
            "page_html_sha16": hashlib.sha256("；".join(row["私有页HTML_SHA256"] for row in private_index_rows).encode("utf-8")).hexdigest()[:16],
            "page_image_sha16": hashlib.sha256("；".join(row["私有页图_SHA256"] for row in private_index_rows).encode("utf-8")).hexdigest()[:16],
            "page_text_sha16": hashlib.sha256("；".join(row["私有OCR文本_SHA256"] for row in private_index_rows).encode("utf-8")).hexdigest()[:16],
        },
    }
    write_json(PUBLIC_SUMMARY, summary)
    public_safety_check()


if __name__ == "__main__":
    main()
