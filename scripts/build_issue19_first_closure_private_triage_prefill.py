#!/usr/bin/env python3
import csv
import hashlib
import html
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIRST_DETAIL = ROOT / "data/working/issue19-stable-foundation-first-closure-detail-packet.csv"
FIRST_TASK_REVIEW = ROOT / "data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv"
FIRST_REVIEW = ROOT / "data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv"
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-stable-foundation-first-closure-triage-prefill"
PRIVATE_PAGE_SIDE_DIR = PRIVATE_OUTPUT_DIR / "page-sides"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "first-closure-triage-prefill-private-index.csv"
PRIVATE_MASTER_CSV = PRIVATE_OUTPUT_DIR / "first-closure-triage-prefill-private-workbench.csv"
PRIVATE_MASTER_HTML = PRIVATE_OUTPUT_DIR / "index.html"

PUBLIC_AUDIT = ROOT / "data/working/issue19-stable-foundation-first-closure-triage-prefill-public-audit.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-stable-foundation-first-closure-triage-prefill-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_triage_prefill_public_audit"

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

PRIVATE_WORKBENCH_FIELDS = [
    "稳定基座第一闭环私有预填任务ID",
    "稳定基座第一闭环任务复核公开账本ID",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环页列包ID",
    "稳定基座第一闭环复核公开账本ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "第一闭环页列优先级",
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
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "差异字段集合",
    "疑似OCR把学费读入计划数",
    "最佳官网来源文件",
    "最佳官网来源文件SHA256",
    "高校辅证候选计划数",
    "高校辅证候选学费",
    "高校辅证候选选科",
    "OCR候选计划数",
    "OCR候选学费",
    "OCR候选选科",
    "预填候选来源",
    "预填候选字段集合",
    "预填候选用途边界",
    "自动辅证是否可作为核页提示",
    "自动辅证是否可替代湖北官方计划",
    "PDF原页是否必核",
    "湖北官方侧是否必核",
    "高校辅证是否需要复核",
    "是否需要双人复核",
    "P0字段即时复核任务ID",
    "P0即时字段确认公开账本ID",
    "执行批次",
    "人工核验泳道",
    "人工核验方式",
    "人工最小动作",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图bbox归一化",
    "私有第一闭环页列CSV证据编号",
    "私有第一闭环页列CSV_SHA256",
    "私有第一闭环页列HTML证据编号",
    "私有第一闭环页列HTML_SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
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
    "稳定基座第一闭环复核公开账本ID",
    "私有预填页列CSV相对路径",
    "私有预填页列CSV_SHA256",
    "预填任务数",
    "高校辅证候选任务数",
    "双人复核任务数",
]

PUBLIC_AUDIT_FIELDS = [
    "第一闭环私有预填公开审计ID",
    "来源第一闭环任务复核公开账本",
    "来源第一闭环复核公开账本",
    "来源湖北官方公开入口状态快照",
    "来源第一闭环私有预填材料",
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
    "稳定基座第一闭环复核公开账本ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "第一闭环页列优先级",
    "预填任务数",
    "自动官网辅证任务数",
    "P0人工字段任务数",
    "高校辅证线索任务数",
    "含高校计划数线索任务数",
    "含高校学费线索任务数",
    "含高校选科线索任务数",
    "公共高校来源文件任务数",
    "公共高校来源文件数",
    "自动辅证可作为核页提示任务数",
    "PDF原页必核任务数",
    "湖北官方侧必核任务数",
    "高校辅证需复核任务数",
    "双人复核任务数",
    "C0冲突任务数",
    "C1官网补缺任务数",
    "C7官网未匹配任务数",
    "EXEC01冲突异常字段数",
    "EXEC02计划数偏大字段数",
    "EXEC03高校辅证字段数",
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
    "OCR候选计划数",
    "高校辅证候选计划数",
    "候选计划数",
    "候选学费",
    "候选选科",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "PDF原页人工读数",
    "湖北官方字段值",
    "字段确认值",
    "一审记录",
    "二审记录",
    "复核结论",
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


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def load_official_status():
    data = json.loads(OFFICIAL_STATUS.read_text(encoding="utf-8"))
    return {
        "official_public_plan_page_can_finalize": bool(
            data.get("hubei_admission_plan_page", {}).get("can_finalize")
        ),
        "zspt_platform_can_finalize": bool(
            data.get("hubei_zspt_platform", {}).get("can_finalize")
        ),
    }


def candidate_fields(detail_row):
    fields = []
    if detail_row.get("最佳官网计划数", ""):
        fields.append("专业计划数")
    if detail_row.get("最佳官网学费", ""):
        fields.append("学费")
    if detail_row.get("最佳官网选科", ""):
        fields.append("再选科目")
    return fields


def task_sort_key(row):
    priority_order = {
        "Q0-冲突页列第一批先核": 0,
        "Q1-补缺或计划数偏大页列先核": 1,
        "Q2-官网未匹配或高校辅证页列先核": 2,
    }
    try:
        page = int(row.get("来源页码", "9999"))
    except ValueError:
        page = 9999
    return (
        priority_order.get(row.get("第一闭环页列优先级", ""), 9),
        page,
        row.get("版面列", ""),
        row.get("任务来源类型", ""),
        row.get("稳定基座第一闭环明细任务ID", ""),
    )


def build_private_row(task_row, detail_row):
    candidates = candidate_fields(detail_row)
    source = "高校官网辅证候选线索" if candidates else "无可预填高校辅证候选"
    return {
        "稳定基座第一闭环私有预填任务ID": stable_id(
            "FIRSTPREFILL", [task_row.get("稳定基座第一闭环明细任务ID", "")]
        ),
        "稳定基座第一闭环任务复核公开账本ID": task_row.get("稳定基座第一闭环任务复核公开账本ID", ""),
        "稳定基座第一闭环明细任务ID": task_row.get("稳定基座第一闭环明细任务ID", ""),
        "稳定基座第一闭环页列包ID": task_row.get("稳定基座第一闭环页列包ID", ""),
        "稳定基座第一闭环复核公开账本ID": task_row.get("稳定基座第一闭环复核公开账本ID", ""),
        "来源页码": task_row.get("来源页码", ""),
        "版面列": task_row.get("版面列", ""),
        "页码版面键": task_row.get("页码版面键", ""),
        "第一闭环页列优先级": task_row.get("第一闭环页列优先级", ""),
        "任务来源类型": task_row.get("任务来源类型", ""),
        "第一闭环批次": task_row.get("第一闭环批次", ""),
        "第一闭环纳入原因": task_row.get("第一闭环纳入原因", ""),
        "专业行ID": task_row.get("专业行ID", ""),
        "专业组出现ID": task_row.get("专业组出现ID", ""),
        "院校代码": task_row.get("院校代码", ""),
        "院校名称OCR": detail_row.get("院校名称OCR", ""),
        "院校专业组代码OCR规范化": detail_row.get("院校专业组代码OCR规范化", ""),
        "专业组内专业序号": detail_row.get("专业组内专业序号", ""),
        "专业代号OCR": detail_row.get("专业代号OCR", ""),
        "专业名称及备注短摘": detail_row.get("专业名称及备注短摘", ""),
        "字段名": task_row.get("字段名", ""),
        "官网辅证自动动作": task_row.get("官网辅证自动动作", ""),
        "官网证据强度": task_row.get("官网证据强度", ""),
        "官网来源状态": task_row.get("官网来源状态", ""),
        "官网证据匹配状态": task_row.get("官网证据匹配状态", ""),
        "计划数核验状态": task_row.get("计划数核验状态", ""),
        "差异字段集合": task_row.get("差异字段集合", ""),
        "疑似OCR把学费读入计划数": task_row.get("疑似OCR把学费读入计划数", ""),
        "最佳官网来源文件": task_row.get("最佳官网来源文件", ""),
        "最佳官网来源文件SHA256": task_row.get("最佳官网来源文件SHA256", ""),
        "高校辅证候选计划数": detail_row.get("最佳官网计划数", ""),
        "高校辅证候选学费": detail_row.get("最佳官网学费", ""),
        "高校辅证候选选科": detail_row.get("最佳官网选科", ""),
        "OCR候选计划数": detail_row.get("OCR专业计划数候选", ""),
        "OCR候选学费": detail_row.get("OCR学费候选", ""),
        "OCR候选选科": detail_row.get("OCR再选科目候选", ""),
        "预填候选来源": source,
        "预填候选字段集合": "；".join(candidates),
        "预填候选用途边界": "仅作高校辅证核页线索；不得写入PDF原页人工读数、湖北官方字段值或字段确认值",
        "自动辅证是否可作为核页提示": task_row.get("自动辅证是否可作为核页提示", ""),
        "自动辅证是否可替代湖北官方计划": "false",
        "PDF原页是否必核": task_row.get("PDF原页是否必核", "true"),
        "湖北官方侧是否必核": task_row.get("湖北官方侧是否必核", "true"),
        "高校辅证是否需要复核": task_row.get("高校辅证是否需要复核", ""),
        "是否需要双人复核": task_row.get("是否需要双人复核", ""),
        "P0字段即时复核任务ID": task_row.get("P0字段即时复核任务ID", ""),
        "P0即时字段确认公开账本ID": task_row.get("P0即时字段确认公开账本ID", ""),
        "执行批次": task_row.get("执行批次", ""),
        "人工核验泳道": task_row.get("人工核验泳道", ""),
        "人工核验方式": task_row.get("人工核验方式", ""),
        "人工最小动作": task_row.get("人工最小动作", ""),
        "裁图证据编号": task_row.get("裁图证据编号", ""),
        "裁图文件SHA256": task_row.get("裁图文件SHA256", ""),
        "裁图bbox归一化": task_row.get("裁图bbox归一化", ""),
        "私有第一闭环页列CSV证据编号": task_row.get("私有第一闭环页列CSV证据编号", ""),
        "私有第一闭环页列CSV_SHA256": task_row.get("私有第一闭环页列CSV_SHA256", ""),
        "私有第一闭环页列HTML证据编号": task_row.get("私有第一闭环页列HTML证据编号", ""),
        "私有第一闭环页列HTML_SHA256": task_row.get("私有第一闭环页列HTML_SHA256", ""),
        "PDF原页核页状态": task_row.get("PDF原页核页状态", ""),
        "湖北官方系统或省招办计划核验状态": task_row.get("湖北官方系统或省招办计划核验状态", ""),
        "高校官网或招生章程辅证状态": task_row.get("高校官网或招生章程辅证状态", ""),
        "三方字段一致性状态": task_row.get("三方字段一致性状态", ""),
        "字段事实写回状态": task_row.get("字段事实写回状态", ""),
        "PDF原页人工读数": "",
        "湖北官方字段值": "",
        "高校官网或招生章程字段值": "",
        "字段确认值": "",
        "一审记录": "",
        "二审记录": "",
        "复核结论": "",
        "复核备注": "",
    }


def write_master_html(page_side_audit_rows):
    rows = []
    for row in page_side_audit_rows:
        rel = f"page-sides/{row['页码版面键']}.csv"
        rows.append(
            "<tr>"
            f"<td>{html.escape(row['第一闭环页列优先级'])}</td>"
            f"<td>{html.escape(row['页码版面键'])}</td>"
            f"<td>{html.escape(row['预填任务数'])}</td>"
            f"<td>{html.escape(row['高校辅证线索任务数'])}</td>"
            f"<td><a href='{html.escape(rel)}'>CSV</a></td>"
            "</tr>"
        )
    PRIVATE_MASTER_HTML.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>第一闭环私有预填工作台</title></head><body>"
        "<h1>第一闭环私有预填工作台</h1>"
        "<p>高校官网候选只作核页线索，不得替代 PDF 原页、湖北官方侧或字段确认值。</p>"
        "<table border='1' cellspacing='0' cellpadding='4'>"
        "<thead><tr><th>优先级</th><th>页列</th><th>任务数</th><th>候选任务数</th><th>页列CSV</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></body></html>\n",
        encoding="utf-8",
    )


def build():
    detail_rows = read_csv(FIRST_DETAIL)
    task_rows = read_csv(FIRST_TASK_REVIEW)
    review_rows = read_csv(FIRST_REVIEW)
    official = load_official_status()

    detail_by_id = {row["稳定基座第一闭环明细任务ID"]: row for row in detail_rows}
    review_by_key = {row["页码版面键"]: row for row in review_rows}

    private_rows = []
    for task_row in sorted(task_rows, key=task_sort_key):
        task_id = task_row["稳定基座第一闭环明细任务ID"]
        detail_row = detail_by_id.get(task_id)
        if not detail_row:
            raise RuntimeError(f"任务级账本无法回链第一闭环明细包：{task_id}")
        private_rows.append(build_private_row(task_row, detail_row))

    PRIVATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PRIVATE_PAGE_SIDE_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(PRIVATE_MASTER_CSV, private_rows, PRIVATE_WORKBENCH_FIELDS)

    rows_by_key = defaultdict(list)
    for row in private_rows:
        rows_by_key[row["页码版面键"]].append(row)

    index_rows = []
    public_rows = []
    for key in sorted(rows_by_key, key=lambda k: task_sort_key(rows_by_key[k][0])):
        group = rows_by_key[key]
        first = group[0]
        review = review_by_key.get(key, {})
        page_csv = PRIVATE_PAGE_SIDE_DIR / f"{key}.csv"
        write_csv(page_csv, group, PRIVATE_WORKBENCH_FIELDS)
        page_sha = sha256(page_csv)

        counters = Counter()
        source_files = set()
        for row in group:
            counters[row["任务来源类型"]] += 1
            counters[row["官网辅证自动动作"]] += 1
            counters[row["执行批次"]] += 1
            if row["预填候选字段集合"]:
                counters["prefill_candidate"] += 1
            if row["高校辅证候选计划数"]:
                counters["candidate_plan"] += 1
            if row["高校辅证候选学费"]:
                counters["candidate_tuition"] += 1
            if row["高校辅证候选选科"]:
                counters["candidate_elective"] += 1
            if row["最佳官网来源文件"]:
                counters["source_file_rows"] += 1
                source_files.add(row["最佳官网来源文件"])
            if row["自动辅证是否可作为核页提示"] == "true":
                counters["auto_hint"] += 1
            if row["PDF原页是否必核"] == "true":
                counters["pdf_required"] += 1
            if row["湖北官方侧是否必核"] == "true":
                counters["hubei_required"] += 1
            if row["高校辅证是否需要复核"] == "true":
                counters["school_required"] += 1
            if row["是否需要双人复核"] == "true":
                counters["double_review"] += 1

        index_rows.append({
            "来源页码": first["来源页码"],
            "版面列": first["版面列"],
            "页码版面键": key,
            "第一闭环页列优先级": first["第一闭环页列优先级"],
            "稳定基座第一闭环页列包ID": first["稳定基座第一闭环页列包ID"],
            "稳定基座第一闭环复核公开账本ID": first["稳定基座第一闭环复核公开账本ID"],
            "私有预填页列CSV相对路径": f"page-sides/{key}.csv",
            "私有预填页列CSV_SHA256": page_sha,
            "预填任务数": str(len(group)),
            "高校辅证候选任务数": str(counters["prefill_candidate"]),
            "双人复核任务数": str(counters["double_review"]),
        })

        public_rows.append({
            "第一闭环私有预填公开审计ID": stable_id("FIRSTPREFILLAUDIT", [key]),
            "来源第一闭环任务复核公开账本": "data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv",
            "来源第一闭环复核公开账本": "data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv",
            "来源湖北官方公开入口状态快照": "data/working/issue19-official-public-entry-status.json",
            "来源第一闭环私有预填材料": "first_closure_triage_prefill_private_material_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×第一闭环私有预填审计",
            **false_gate_values(),
            "稳定基座第一闭环页列包ID": first["稳定基座第一闭环页列包ID"],
            "稳定基座第一闭环复核公开账本ID": first["稳定基座第一闭环复核公开账本ID"],
            "来源页码": first["来源页码"],
            "版面列": first["版面列"],
            "页码版面键": key,
            "第一闭环页列优先级": first["第一闭环页列优先级"],
            "预填任务数": str(len(group)),
            "自动官网辅证任务数": str(counters["自动官网辅证任务"]),
            "P0人工字段任务数": str(counters["P0人工字段任务"]),
            "高校辅证线索任务数": str(counters["prefill_candidate"]),
            "含高校计划数线索任务数": str(counters["candidate_plan"]),
            "含高校学费线索任务数": str(counters["candidate_tuition"]),
            "含高校选科线索任务数": str(counters["candidate_elective"]),
            "公共高校来源文件任务数": str(counters["source_file_rows"]),
            "公共高校来源文件数": str(len(source_files)),
            "自动辅证可作为核页提示任务数": str(counters["auto_hint"]),
            "PDF原页必核任务数": str(counters["pdf_required"]),
            "湖北官方侧必核任务数": str(counters["hubei_required"]),
            "高校辅证需复核任务数": str(counters["school_required"]),
            "双人复核任务数": str(counters["double_review"]),
            "C0冲突任务数": str(counters["C0-冲突先核PDF原页和湖北官方系统"]),
            "C1官网补缺任务数": str(counters["C1-官网补缺候选但禁止自动写回"]),
            "C7官网未匹配任务数": str(counters["C7-官网源未匹配专业需人工确认专业名"]),
            "EXEC01冲突异常字段数": str(counters["EXEC-01-冲突异常立即核页"]),
            "EXEC02计划数偏大字段数": str(counters["EXEC-02-计划数偏大重点核页"]),
            "EXEC03高校辅证字段数": str(counters["EXEC-03-高校辅证线索三方核验"]),
            "私有预填页列CSV证据编号": f"FIRST-CLOSURE-PREFILL-CSV-{key}",
            "私有预填页列CSV_SHA256": page_sha,
            "私有预填材料状态": "private_triage_prefill_material_generated_not_reviewed",
            "官方公开计划页可定稿": str(official["official_public_plan_page_can_finalize"]).lower(),
            "数智平台可定稿": str(official["zspt_platform_can_finalize"]).lower(),
            "字段事实写回状态": "blocked_until_private_pdf_hubei_review_confirms_values",
            "公开安全策略": "公开层只保存页列计数和私有预填CSV的SHA；不公开高校候选值、OCR候选值、人工读数、私有路径或复核记录",
            "下一步": "人工在私有预填工作台中按页列核PDF原页、湖北官方侧和高校辅证线索，完成后再进入字段事实复查",
        })

    write_csv(PRIVATE_INDEX, index_rows, PRIVATE_INDEX_FIELDS)
    write_master_html(public_rows)
    write_csv(PUBLIC_AUDIT, public_rows, PUBLIC_AUDIT_FIELDS)

    public_scan_text = "\n".join(
        "\t".join(str(row.get(field, "")) for field in PUBLIC_AUDIT_FIELDS) for row in public_rows
    )
    forbidden = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_scan_text]
    if forbidden:
        raise RuntimeError(f"公开预填审计包含禁止公开内容：{forbidden[:5]}")

    summary = {
        "status": "issue19_stable_foundation_first_closure_triage_prefill_not_final",
        "generated_by": "build_issue19_first_closure_private_triage_prefill.py",
        "source_first_closure_task_review_public_ledger": "data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv",
        "source_first_closure_review_public_ledger": "data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv",
        "source_official_public_status": "data/working/issue19-official-public-entry-status.json",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_public_audit": "data/working/issue19-stable-foundation-first-closure-triage-prefill-public-audit.csv",
        "source_private_triage_prefill_material": "first_closure_triage_prefill_private_material_not_public",
        "public_row_count": len(public_rows),
        "private_workbench_row_count": len(private_rows),
        "unique_task_count": len({row["稳定基座第一闭环明细任务ID"] for row in private_rows}),
        "unique_page_side_count": len(rows_by_key),
        "unique_pdf_page_count": len({row["来源页码"] for row in private_rows}),
        "prefill_candidate_task_count": sum(1 for row in private_rows if row["预填候选字段集合"]),
        "candidate_plan_task_count": sum(1 for row in private_rows if row["高校辅证候选计划数"]),
        "candidate_tuition_task_count": sum(1 for row in private_rows if row["高校辅证候选学费"]),
        "candidate_elective_task_count": sum(1 for row in private_rows if row["高校辅证候选选科"]),
        "public_school_source_file_task_count": sum(1 for row in private_rows if row["最佳官网来源文件"]),
        "unique_public_school_source_file_count": len({row["最佳官网来源文件"] for row in private_rows if row["最佳官网来源文件"]}),
        "double_review_required_count": sum(1 for row in private_rows if row["是否需要双人复核"] == "true"),
        "pdf_required_count": sum(1 for row in private_rows if row["PDF原页是否必核"] == "true"),
        "hubei_official_required_count": sum(1 for row in private_rows if row["湖北官方侧是否必核"] == "true"),
        "school_support_required_count": sum(1 for row in private_rows if row["高校辅证是否需要复核"] == "true"),
        "private_master_csv_sha256": sha256(PRIVATE_MASTER_CSV),
        "private_index_csv_sha256": sha256(PRIVATE_INDEX),
        "private_master_html_sha256": sha256(PRIVATE_MASTER_HTML),
        "official_public_plan_page_can_finalize": official["official_public_plan_page_can_finalize"],
        "zspt_platform_can_finalize": official["zspt_platform_can_finalize"],
        "field_writeback_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "policy": {
            "purpose": "把高校官网计划数、学费、选科等候选只作为私有核页线索预填，减少人工打开来源和逐行查找成本。",
            "public_boundary": "公开审计只保存页列计数、私有材料SHA和门禁，不保存候选值、人工读数、OCR原文或私有路径。",
            "no_finalization": "预填线索不得替代PDF原页、湖北官方侧或正式字段结论，不自动写回，不生成学校专业建议。",
        },
    }
    write_json(SUMMARY_OUTPUT, summary)

    print(f"写出 {PUBLIC_AUDIT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出私有预填工作台：{PRIVATE_OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
