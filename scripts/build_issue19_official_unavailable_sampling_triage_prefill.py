#!/usr/bin/env python3
import csv
import hashlib
import html
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXECUTION_QUEUE = (
    ROOT / "data/working/issue19-official-unavailable-sampling-review-execution-queue.csv"
)
PRIVATE_OVERLAY = (
    ROOT / "private/review-assets/issue19-official-unavailable-sampling-review-overlay/sampling-review-overlay.csv"
)
OFFICIAL_LIVE_RECHECK = ROOT / "data/working/issue19-official-public-entry-live-recheck.json"

PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-official-unavailable-sampling-triage-prefill"
PRIVATE_PAGE_SIDE_DIR = PRIVATE_OUTPUT_DIR / "page-sides"
PRIVATE_MASTER_CSV = PRIVATE_OUTPUT_DIR / "sampling-triage-prefill-private-workbench.csv"
PRIVATE_INDEX_CSV = PRIVATE_OUTPUT_DIR / "sampling-triage-prefill-private-index.csv"
PRIVATE_INDEX_HTML = PRIVATE_OUTPUT_DIR / "index.html"

PUBLIC_AUDIT = (
    ROOT / "data/working/issue19-official-unavailable-sampling-triage-prefill-public-audit.csv"
)
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-official-unavailable-sampling-triage-prefill-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_official_unavailable_sampling_triage_prefill_public_audit"

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许写回字段事实",
]

PRIVATE_WORKBENCH_FIELDS = [
    "官方不可得抽样私有预填任务ID",
    "来源官方不可得抽样页列执行队列ID",
    "来源官方不可得抽样OverlayID",
    "来源官方不可得抽样执行明细ID",
    "来源执行明细行SHA256",
    "来源页码",
    "版面列",
    "页码版面键",
    "执行队列总序",
    "执行泳道",
    "执行优先级",
    "执行类别",
    "风险等级",
    "抽样策略",
    "样本序号",
    "是否100%人工核验",
    "是否抽样核验",
    "是否低风险样本",
    "是否需要双人复核",
    "院校代码",
    "院校名称OCR",
    "专业行ID",
    "专业组出现ID",
    "院校专业组代码OCR规范化",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "必核字段",
    "字段差异标记",
    "官网辅证自动动作",
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "疑似OCR把学费读入计划数",
    "官网专业名称线索",
    "官网专业代号线索",
    "官网计划数线索",
    "官网学费线索",
    "官网选科线索",
    "官网来源文件",
    "官网来源文件SHA256集合",
    "OCR计划数线索",
    "OCR学费线索",
    "OCR选科线索",
    "预填线索字段集合",
    "预填线索来源",
    "预填线索用途边界",
    "PDF原页是否必核",
    "湖北官方侧是否必核",
    "高校辅证是否需复核",
    "高校辅证待补源",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方一致性状态",
    "字段事实写回状态",
    "PDF原页人工读数_专业名称",
    "PDF原页人工读数_专业计划数",
    "PDF原页人工读数_学费",
    "PDF原页人工读数_再选科目",
    "PDF原页人工读数_备注限制",
    "湖北官方字段值_专业名称",
    "湖北官方字段值_专业计划数",
    "湖北官方字段值_学费",
    "湖北官方字段值_再选科目",
    "湖北官方字段值_备注限制",
    "高校辅证人工采纳值_专业名称",
    "高校辅证人工采纳值_专业计划数",
    "高校辅证人工采纳值_学费",
    "高校辅证人工采纳值_再选科目",
    "高校辅证人工采纳值_备注限制",
    "三方一致性人工结论",
    "是否抽检失败",
    "失败升级范围",
    "一审记录",
    "二审记录",
    "复核结论",
    "复核备注",
]

PRIVATE_INDEX_FIELDS = [
    "来源页码",
    "版面列",
    "页码版面键",
    "执行队列总序",
    "执行泳道",
    "页列任务数",
    "高校辅证线索任务数",
    "高校来源文件任务数",
    "双人复核任务数",
    "私有预填页列CSV相对路径",
    "私有预填页列CSV_SHA256",
]

PUBLIC_AUDIT_FIELDS = [
    "官方不可得抽样私有预填公开审计ID",
    "来源抽样页列执行队列",
    "来源本地抽样复核Overlay",
    "来源本地私有预填材料",
    "来源湖北官方活体复查",
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
    "来源官方不可得抽样页列执行队列ID",
    "执行队列总序",
    "执行泳道",
    "执行优先级",
    "页列任务数",
    "高风险100%核验明细数",
    "C0冲突明细数",
    "C1官网补缺明细数",
    "C7官网未匹配明细数",
    "C2强辅证抽样明细数",
    "P3低风险抽样明细数",
    "PDF原页必核明细数",
    "湖北官方侧必核明细数",
    "高校辅证需复核明细数",
    "高校辅证待补源明细数",
    "双人复核明细数",
    "高校辅证线索明细数",
    "高校专业名称线索明细数",
    "高校计划数线索明细数",
    "高校学费线索明细数",
    "高校选科线索明细数",
    "高校来源文件明细数",
    "高校来源文件数",
    "OCR计划数线索明细数",
    "OCR学费线索明细数",
    "OCR选科线索明细数",
    "私有预填页列CSV证据编号",
    "私有预填页列CSV_SHA256",
    "私有预填材料状态",
    "官方公开计划页可定稿",
    "数智平台可定稿",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
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
    "院校代码",
    "院校名称OCR",
    "院校专业组",
    "专业代号",
    "专业名称及备注",
    "OCR文本",
    "OCR行文本",
    "PDF原页人工读数",
    "湖北官方字段值",
    "人工备注",
    "一审",
    "二审",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
    "字段读数",
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


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def filled(value):
    return bool(str(value or "").strip())


def false_values():
    return {field: "false" for field in FALSE_FIELDS}


def page_side_key(row):
    return (str(row.get("来源页码", "")).strip(), str(row.get("版面列", "")).strip())


def page_side_text(row):
    return f"{row.get('来源页码', '')}-{row.get('版面列', '')}"


def candidate_fields(row):
    fields = []
    if filled(row.get("最佳官网专业名称")):
        fields.append("专业名称")
    if filled(row.get("最佳官网计划数")):
        fields.append("专业计划数")
    if filled(row.get("最佳官网学费")):
        fields.append("学费")
    if filled(row.get("最佳官网选科")):
        fields.append("再选科目")
    return fields


def split_source_files(value):
    if not filled(value):
        return []
    parts = []
    for item in str(value).replace("；", ";").split(";"):
        item = item.strip()
        if item:
            parts.append(item)
    return parts


def source_file_sha_list(value):
    shas = []
    for source in split_source_files(value):
        path = ROOT / source
        if path.exists() and path.is_file():
            shas.append(sha256(path))
    return "；".join(shas)


def load_official_status():
    data = json.loads(OFFICIAL_LIVE_RECHECK.read_text(encoding="utf-8"))
    conclusion = data.get("current_conclusion", {})
    return {
        "official_public_plan_page_can_finalize": bool(
            conclusion.get("can_finalize_admission_plan_from_public_entry")
        ),
        "zspt_platform_can_finalize": not bool(
            conclusion.get("all_platform_probes_blocked_without_login", True)
        ),
    }


def private_row(overlay_row, queue_row):
    fields = candidate_fields(overlay_row)
    source_files = overlay_row.get("最佳官网来源文件", "")
    source = "高校官网辅证线索" if fields else "无可预填高校辅证线索"
    school_pending = overlay_row.get("高校官网或招生章程辅证状态") == (
        "not_yet_school_source_searched_in_full_workbench"
    )
    return {
        "官方不可得抽样私有预填任务ID": stable_id(
            "SAMPLINGPREFILL",
            [
                overlay_row.get("官方不可得抽样OverlayID", ""),
                overlay_row.get("来源官方不可得抽样执行明细ID", ""),
            ],
        ),
        "来源官方不可得抽样页列执行队列ID": queue_row.get("官方不可得抽样页列执行队列ID", ""),
        "来源官方不可得抽样OverlayID": overlay_row.get("官方不可得抽样OverlayID", ""),
        "来源官方不可得抽样执行明细ID": overlay_row.get("来源官方不可得抽样执行明细ID", ""),
        "来源执行明细行SHA256": overlay_row.get("来源执行明细行SHA256", ""),
        "来源页码": overlay_row.get("来源页码", ""),
        "版面列": overlay_row.get("版面列", ""),
        "页码版面键": overlay_row.get("页码版面键", ""),
        "执行队列总序": queue_row.get("执行队列总序", ""),
        "执行泳道": queue_row.get("执行泳道", ""),
        "执行优先级": queue_row.get("执行优先级", ""),
        "执行类别": overlay_row.get("执行类别", ""),
        "风险等级": overlay_row.get("风险等级", ""),
        "抽样策略": overlay_row.get("抽样策略", ""),
        "样本序号": overlay_row.get("样本序号", ""),
        "是否100%人工核验": overlay_row.get("是否100%人工核验", ""),
        "是否抽样核验": overlay_row.get("是否抽样核验", ""),
        "是否低风险样本": overlay_row.get("是否低风险样本", ""),
        "是否需要双人复核": overlay_row.get("是否需要双人复核", ""),
        "院校代码": overlay_row.get("院校代码", ""),
        "院校名称OCR": overlay_row.get("院校名称OCR", ""),
        "专业行ID": overlay_row.get("专业行ID", ""),
        "专业组出现ID": overlay_row.get("专业组出现ID", ""),
        "院校专业组代码OCR规范化": overlay_row.get("院校专业组代码OCR规范化", ""),
        "专业组内专业序号": overlay_row.get("专业组内专业序号", ""),
        "专业代号OCR": overlay_row.get("专业代号OCR", ""),
        "专业名称及备注短摘": overlay_row.get("专业名称及备注短摘", ""),
        "必核字段": overlay_row.get("必核字段", ""),
        "字段差异标记": overlay_row.get("字段差异标记", ""),
        "官网辅证自动动作": overlay_row.get("官网辅证自动动作", ""),
        "官网证据强度": overlay_row.get("官网证据强度", ""),
        "官网来源状态": overlay_row.get("官网来源状态", ""),
        "官网证据匹配状态": overlay_row.get("官网证据匹配状态", ""),
        "计划数核验状态": overlay_row.get("计划数核验状态", ""),
        "疑似OCR把学费读入计划数": overlay_row.get("疑似OCR把学费读入计划数", ""),
        "官网专业名称线索": overlay_row.get("最佳官网专业名称", ""),
        "官网专业代号线索": overlay_row.get("最佳官网专业代号", ""),
        "官网计划数线索": overlay_row.get("最佳官网计划数", ""),
        "官网学费线索": overlay_row.get("最佳官网学费", ""),
        "官网选科线索": overlay_row.get("最佳官网选科", ""),
        "官网来源文件": source_files,
        "官网来源文件SHA256集合": source_file_sha_list(source_files),
        "OCR计划数线索": overlay_row.get("OCR专业计划数候选", ""),
        "OCR学费线索": overlay_row.get("OCR学费候选", ""),
        "OCR选科线索": overlay_row.get("OCR再选科目候选", ""),
        "预填线索字段集合": "；".join(fields),
        "预填线索来源": source,
        "预填线索用途边界": "只作为人工核 PDF 原页、湖北官方侧和高校辅证时的提示；不得写回字段事实",
        "PDF原页是否必核": "true",
        "湖北官方侧是否必核": "true",
        "高校辅证是否需复核": "false" if school_pending else "true",
        "高校辅证待补源": "true" if school_pending else "false",
        "PDF原页核页状态": overlay_row.get("PDF原页核页状态", ""),
        "湖北官方系统或省招办计划核验状态": overlay_row.get("湖北官方系统或省招办计划核验状态", ""),
        "高校官网或招生章程辅证状态": overlay_row.get("高校官网或招生章程辅证状态", ""),
        "三方一致性状态": overlay_row.get("三方一致性状态", ""),
        "字段事实写回状态": overlay_row.get("字段事实写回状态", ""),
        "PDF原页人工读数_专业名称": "",
        "PDF原页人工读数_专业计划数": "",
        "PDF原页人工读数_学费": "",
        "PDF原页人工读数_再选科目": "",
        "PDF原页人工读数_备注限制": "",
        "湖北官方字段值_专业名称": "",
        "湖北官方字段值_专业计划数": "",
        "湖北官方字段值_学费": "",
        "湖北官方字段值_再选科目": "",
        "湖北官方字段值_备注限制": "",
        "高校辅证人工采纳值_专业名称": "",
        "高校辅证人工采纳值_专业计划数": "",
        "高校辅证人工采纳值_学费": "",
        "高校辅证人工采纳值_再选科目": "",
        "高校辅证人工采纳值_备注限制": "",
        "三方一致性人工结论": "",
        "是否抽检失败": "",
        "失败升级范围": "",
        "一审记录": "",
        "二审记录": "",
        "复核结论": "",
        "复核备注": "",
    }


def row_sort_key(row):
    return (
        as_int(row.get("执行队列总序"), 999),
        as_int(row.get("样本序号"), 999),
        row.get("来源官方不可得抽样执行明细ID", ""),
    )


def write_index_html(public_rows):
    rows = []
    for row in public_rows:
        rel = f"page-sides/{row['页码版面键']}.csv"
        rows.append(
            "<tr>"
            f"<td>{html.escape(row['执行队列总序'])}</td>"
            f"<td>{html.escape(row['执行泳道'])}</td>"
            f"<td>{html.escape(row['页码版面键'])}</td>"
            f"<td>{html.escape(row['页列任务数'])}</td>"
            f"<td>{html.escape(row['高校辅证线索明细数'])}</td>"
            f"<td>{html.escape(row['双人复核明细数'])}</td>"
            f"<td><a href='{html.escape(rel)}'>CSV</a></td>"
            "</tr>"
        )
    PRIVATE_INDEX_HTML.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>官方不可得抽样私有预填工作台</title></head><body>"
        "<h1>官方不可得抽样私有预填工作台</h1>"
        "<p>高校官网线索只作人工核页提示，不替代第19期原页、湖北官方侧或字段确认。</p>"
        "<table border='1' cellspacing='0' cellpadding='4'>"
        "<thead><tr><th>总序</th><th>泳道</th><th>页列</th><th>任务数</th>"
        "<th>高校线索</th><th>双人复核</th><th>页列CSV</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></body></html>\n",
        encoding="utf-8",
    )


def public_row(key, queue_row, group, page_csv_sha, official):
    counters = Counter()
    source_files = set()
    for row in group:
        counters["task"] += 1
        if row.get("是否100%人工核验") == "true":
            counters["high_risk"] += 1
        if row.get("是否需要双人复核") == "true":
            counters["double_review"] += 1
        action = row.get("官网辅证自动动作", "")
        if action.startswith("C0-"):
            counters["c0"] += 1
        if action.startswith("C1-"):
            counters["c1"] += 1
        if action.startswith("C7-"):
            counters["c7"] += 1
        if action.startswith("C2-"):
            counters["c2"] += 1
        if action.startswith("P3-"):
            counters["p3"] += 1
        if row.get("高校辅证是否需复核") == "true":
            counters["school_required"] += 1
        if row.get("高校辅证待补源") == "true":
            counters["school_pending"] += 1
        if row.get("预填线索字段集合"):
            counters["school_clue"] += 1
        if row.get("官网专业名称线索"):
            counters["school_name"] += 1
        if row.get("官网计划数线索"):
            counters["school_plan"] += 1
        if row.get("官网学费线索"):
            counters["school_tuition"] += 1
        if row.get("官网选科线索"):
            counters["school_elective"] += 1
        if row.get("OCR计划数线索"):
            counters["ocr_plan"] += 1
        if row.get("OCR学费线索"):
            counters["ocr_tuition"] += 1
        if row.get("OCR选科线索"):
            counters["ocr_elective"] += 1
        files = split_source_files(row.get("官网来源文件", ""))
        if files:
            counters["source_file_rows"] += 1
            source_files.update(files)
    page, side = key
    page_key = group[0].get("页码版面键", f"{page}-{side}")
    return {
        "官方不可得抽样私有预填公开审计ID": stable_id("SAMPLINGPREFILLAUDIT", [page, side]),
        "来源抽样页列执行队列": "data/working/issue19-official-unavailable-sampling-review-execution-queue.csv",
        "来源本地抽样复核Overlay": "local_sampling_review_overlay_not_public",
        "来源本地私有预填材料": "local_sampling_triage_prefill_not_public",
        "来源湖北官方活体复查": "data/working/issue19-official-public-entry-live-recheck.json",
        "来源期号": SOURCE_ISSUE,
        "来源PDF_SHA256": SOURCE_PDF_SHA256,
        "数据阶段": DATA_STAGE,
        "主表粒度": "PDF页码×版面列",
        "任务粒度": "PDF页码×版面列×官方不可得抽样私有预填审计",
        **false_values(),
        "来源页码": page,
        "版面列": side,
        "页码版面键": page_key,
        "来源官方不可得抽样页列执行队列ID": queue_row.get("官方不可得抽样页列执行队列ID", ""),
        "执行队列总序": queue_row.get("执行队列总序", ""),
        "执行泳道": queue_row.get("执行泳道", ""),
        "执行优先级": queue_row.get("执行优先级", ""),
        "页列任务数": str(counters["task"]),
        "高风险100%核验明细数": str(counters["high_risk"]),
        "C0冲突明细数": str(counters["c0"]),
        "C1官网补缺明细数": str(counters["c1"]),
        "C7官网未匹配明细数": str(counters["c7"]),
        "C2强辅证抽样明细数": str(counters["c2"]),
        "P3低风险抽样明细数": str(counters["p3"]),
        "PDF原页必核明细数": str(counters["task"]),
        "湖北官方侧必核明细数": str(counters["task"]),
        "高校辅证需复核明细数": str(counters["school_required"]),
        "高校辅证待补源明细数": str(counters["school_pending"]),
        "双人复核明细数": str(counters["double_review"]),
        "高校辅证线索明细数": str(counters["school_clue"]),
        "高校专业名称线索明细数": str(counters["school_name"]),
        "高校计划数线索明细数": str(counters["school_plan"]),
        "高校学费线索明细数": str(counters["school_tuition"]),
        "高校选科线索明细数": str(counters["school_elective"]),
        "高校来源文件明细数": str(counters["source_file_rows"]),
        "高校来源文件数": str(len(source_files)),
        "OCR计划数线索明细数": str(counters["ocr_plan"]),
        "OCR学费线索明细数": str(counters["ocr_tuition"]),
        "OCR选科线索明细数": str(counters["ocr_elective"]),
        "私有预填页列CSV证据编号": f"SAMPLING-PREFILL-CSV-{page}-{side}",
        "私有预填页列CSV_SHA256": page_csv_sha,
        "私有预填材料状态": "private_sampling_triage_prefill_generated_not_reviewed",
        "官方公开计划页可定稿": str(official["official_public_plan_page_can_finalize"]).lower(),
        "数智平台可定稿": str(official["zspt_platform_can_finalize"]).lower(),
        "字段事实写回状态": "blocked_until_private_overlay_pdf_hubei_review_closed",
        "公开安全策略": "公开层只保存页列计数和私有预填CSV的SHA；不公开高校线索值、OCR线索值、人工读数、私有路径或复核记录",
        "下一步": "人工按执行队列打开私有预填页列CSV和原页材料；核PDF原页、湖北官方侧和高校辅证后再回写私有Overlay",
    }


def build():
    queue_rows = read_csv(EXECUTION_QUEUE)
    overlay_rows = read_csv(PRIVATE_OVERLAY)
    official = load_official_status()

    queue_by_key = {page_side_key(row): row for row in queue_rows}
    private_rows = []
    for row in overlay_rows:
        key = page_side_key(row)
        queue_row = queue_by_key.get(key)
        if not queue_row:
            raise RuntimeError(f"抽样Overlay无法回链执行队列：{key}")
        private_rows.append(private_row(row, queue_row))

    private_rows.sort(key=row_sort_key)
    PRIVATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PRIVATE_PAGE_SIDE_DIR.mkdir(parents=True, exist_ok=True)
    for stale_csv in PRIVATE_PAGE_SIDE_DIR.glob("*.csv"):
        stale_csv.unlink()
    write_csv(PRIVATE_MASTER_CSV, private_rows, PRIVATE_WORKBENCH_FIELDS)

    grouped = defaultdict(list)
    for row in private_rows:
        grouped[(row["来源页码"], row["版面列"])].append(row)

    public_rows = []
    index_rows = []
    for key in sorted(grouped, key=lambda k: as_int(queue_by_key[k].get("执行队列总序"), 999)):
        group = grouped[key]
        page, side = key
        page_key = group[0].get("页码版面键", f"{page}-{side}")
        page_csv = PRIVATE_PAGE_SIDE_DIR / f"{page_key}.csv"
        write_csv(page_csv, group, PRIVATE_WORKBENCH_FIELDS)
        page_sha = sha256(page_csv)
        queue_row = queue_by_key[key]
        audit_row = public_row(key, queue_row, group, page_sha, official)
        public_rows.append(audit_row)
        index_rows.append({
            "来源页码": page,
            "版面列": side,
            "页码版面键": page_key,
            "执行队列总序": queue_row.get("执行队列总序", ""),
            "执行泳道": queue_row.get("执行泳道", ""),
            "页列任务数": audit_row["页列任务数"],
            "高校辅证线索任务数": audit_row["高校辅证线索明细数"],
            "高校来源文件任务数": audit_row["高校来源文件明细数"],
            "双人复核任务数": audit_row["双人复核明细数"],
            "私有预填页列CSV相对路径": f"page-sides/{page_key}.csv",
            "私有预填页列CSV_SHA256": page_sha,
        })

    write_csv(PRIVATE_INDEX_CSV, index_rows, PRIVATE_INDEX_FIELDS)
    write_index_html(public_rows)
    write_csv(PUBLIC_AUDIT, public_rows, PUBLIC_AUDIT_FIELDS)

    public_text = "\n".join(
        "\t".join(str(row.get(field, "")) for field in PUBLIC_AUDIT_FIELDS)
        for row in public_rows
    )
    forbidden_hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if forbidden_hits:
        raise RuntimeError(f"公开预填审计包含禁止公开内容：{forbidden_hits[:5]}")

    summary = {
        "status": "issue19_official_unavailable_sampling_triage_prefill_not_final",
        "generated_by": "build_issue19_official_unavailable_sampling_triage_prefill.py",
        "source_execution_queue": "data/working/issue19-official-unavailable-sampling-review-execution-queue.csv",
        "source_private_overlay": "local_sampling_review_overlay_not_public",
        "source_official_live_recheck": "data/working/issue19-official-public-entry-live-recheck.json",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_public_audit": "data/working/issue19-official-unavailable-sampling-triage-prefill-public-audit.csv",
        "source_private_triage_prefill_material": "local_sampling_triage_prefill_not_public",
        "public_row_count": len(public_rows),
        "private_workbench_row_count": len(private_rows),
        "unique_page_side_count": len(grouped),
        "unique_pdf_page_count": len({row["来源页码"] for row in private_rows}),
        "sampling_detail_count": len(private_rows),
        "high_risk_100pct_detail_count": sum(row["是否100%人工核验"] == "true" for row in private_rows),
        "c0_conflict_detail_count": sum(row["官网辅证自动动作"].startswith("C0-") for row in private_rows),
        "c1_fill_candidate_detail_count": sum(row["官网辅证自动动作"].startswith("C1-") for row in private_rows),
        "c7_unmatched_detail_count": sum(row["官网辅证自动动作"].startswith("C7-") for row in private_rows),
        "c2_sample_detail_count": sum(row["官网辅证自动动作"].startswith("C2-") for row in private_rows),
        "p3_sample_detail_count": sum(row["官网辅证自动动作"].startswith("P3-") for row in private_rows),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in private_rows),
        "pdf_required_detail_count": len(private_rows),
        "hubei_official_required_detail_count": len(private_rows),
        "school_support_required_detail_count": sum(row["高校辅证是否需复核"] == "true" for row in private_rows),
        "school_support_pending_source_detail_count": sum(row["高校辅证待补源"] == "true" for row in private_rows),
        "school_support_clue_detail_count": sum(bool(row["预填线索字段集合"]) for row in private_rows),
        "school_name_clue_detail_count": sum(bool(row["官网专业名称线索"]) for row in private_rows),
        "school_plan_clue_detail_count": sum(bool(row["官网计划数线索"]) for row in private_rows),
        "school_tuition_clue_detail_count": sum(bool(row["官网学费线索"]) for row in private_rows),
        "school_elective_clue_detail_count": sum(bool(row["官网选科线索"]) for row in private_rows),
        "school_source_file_detail_count": sum(bool(row["官网来源文件"]) for row in private_rows),
        "unique_school_source_file_count": len({
            source
            for row in private_rows
            for source in split_source_files(row["官网来源文件"])
        }),
        "ocr_plan_clue_detail_count": sum(bool(row["OCR计划数线索"]) for row in private_rows),
        "ocr_tuition_clue_detail_count": sum(bool(row["OCR学费线索"]) for row in private_rows),
        "ocr_elective_clue_detail_count": sum(bool(row["OCR选科线索"]) for row in private_rows),
        "private_master_csv_sha256": sha256(PRIVATE_MASTER_CSV),
        "private_index_csv_sha256": sha256(PRIVATE_INDEX_CSV),
        "private_index_html_sha256": sha256(PRIVATE_INDEX_HTML),
        "official_public_plan_page_can_finalize": official["official_public_plan_page_can_finalize"],
        "zspt_platform_can_finalize": official["zspt_platform_can_finalize"],
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "execution_lane_counts": dict(Counter(row["执行泳道"] for row in private_rows)),
        "policy": {
            "purpose": "把高校官网专业名、计划数、学费、选科等线索只预填到私有核页工作台，减少人工在多表间查找。",
            "public_boundary": "公开审计只保存页列计数、私有材料SHA和门禁，不保存线索值、人工读数、OCR原文或私有路径。",
            "no_finalization": "预填线索不得替代PDF原页、湖北官方侧或正式字段结论，不自动写回，不生成学校专业建议。",
        },
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {PUBLIC_AUDIT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出私有预填材料：{PRIVATE_OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
