#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FACT_SCOPE = WORKING / "issue19-stable-foundation-first-closure-fact-scope-gap-public-ledger.csv"
RESULT = WORKING / "issue19-first-closure-verification-result-public-ledger.csv"
FIELD_STATUS = WORKING / "issue19-first-closure-field-verification-status-public-ledger.csv"
PUBLIC_EVIDENCE_MAP = WORKING / "issue19-stable-foundation-first-closure-public-evidence-map.csv"
REVIEW_LEDGER = WORKING / "issue19-stable-foundation-first-closure-review-public-ledger.csv"
TASK_REVIEW = WORKING / "issue19-stable-foundation-first-closure-task-review-public-ledger.csv"
PDF_OCR_AUDIT = WORKING / "issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv"
MACHINE_AUDIT = WORKING / "issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit.csv"
B0_CONFLICT = WORKING / "issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv"

OUTPUT = WORKING / "issue19-first-closure-fact-progress-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-first-closure-fact-progress-page-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-fact-progress-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_first_closure_fact_progress_public_ledger"
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

PROGRESS_FIELDS = [
    "第一闭环事实进度公开账本ID",
    "来源第一闭环事实范围缺口账本",
    "来源第一闭环核验结果看板",
    "来源第一闭环字段级公开状态",
    "来源第一闭环公开证据地图",
    "来源第一闭环复核材料公开账本",
    "来源第一闭环任务复核公开账本",
    "来源第一闭环PDFOCR候选审计",
    "来源第一闭环机器坐标候选审计",
    "来源第一闭环B0冲突页列状态",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "事实进度序号",
    "第一闭环事实范围缺口公开账本ID",
    "事实域",
    "事实类型",
    "事实粒度",
    "字段类别",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环页列包ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "执行泳道",
    "核验动作层级",
    "页列主阻断",
    "事实缺口桶",
    "PDF原页进度桶",
    "OCR提示进度桶",
    "机器坐标进度桶",
    "高校官网辅证进度桶",
    "冲突进度桶",
    "湖北官方侧进度桶",
    "双人复核进度桶",
    "三方闭环状态",
    "字段事实写回状态",
    "字段映射状态",
    "字段事实状态",
    "字段核验优先级",
    "字段事实阻断等级",
    "PDFOCR候选记录状态",
    "PDFOCR候选审阅桶",
    "PDFOCR与高校辅证关系桶",
    "机器坐标候选记录状态",
    "机器坐标候选审阅桶",
    "B0冲突闭环状态",
    "B0冲突优先级判定",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页列HTML证据编号",
    "私有页列HTML_SHA256",
    "最佳官网来源文件SHA256",
    "裁图证据编号",
    "裁图文件SHA256",
    "PDFOCR候选记录证据编号",
    "机器坐标候选任务ID",
    "完成条件",
    "下一步核验动作",
    "当前阻断原因",
    "公开安全策略",
]

PAGE_FIELDS = [
    "第一闭环事实进度页列汇总ID",
    "来源第一闭环事实进度账本",
    "来源第一闭环公开证据地图",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "页列汇总序号",
    "来源页码",
    "版面列",
    "页码版面键",
    "执行泳道",
    "页列主阻断",
    "事实范围数",
    "字段事实数",
    "专业名归属事实数",
    "专业组边界事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "事实类型分布",
    "字段类别分布",
    "PDF原页进度桶分布",
    "OCR提示进度桶分布",
    "机器坐标进度桶分布",
    "高校官网辅证进度桶分布",
    "冲突进度桶分布",
    "湖北官方侧进度桶分布",
    "双人复核进度桶分布",
    "B0冲突事实数",
    "需要双人复核事实数",
    "需要人工看图事实数",
    "私有页图SHA256",
    "私有OCR文本SHA256",
    "私有页列CSV_SHA256",
    "私有页列HTML_SHA256",
    "事实范围集合SHA16",
    "任务集合SHA16",
    "专业行集合SHA16",
    "院校代码集合SHA16",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "完成条件",
    "页列下一步核验动作",
    "公开安全策略",
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
    "字段读数",
    "OCR行文本",
    "字段确认值",
    "人工读数",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def clean(value):
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def public_safe_text(value):
    text = clean(value)
    replacements = [
        ("PDF原页人工读数", "PDF原页私有记录"),
        ("记录私有人工读数", "填写私有人工记录"),
        ("人工读数", "私有人工记录"),
        ("逐字段读数", "逐字段记录"),
        ("字段读数", "字段记录"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: clean(row.get(field, "")) for field in fields} for row in rows])


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha16(values):
    normalized = "\n".join(sorted({clean(value) for value in values if clean(value)}))
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def as_int(value):
    try:
        return int(float(clean(value) or "0"))
    except ValueError:
        return 0


def bool_text(value):
    return "true" if clean(value) == "true" else "false"


def source_path(path):
    return str(path.relative_to(ROOT))


def single_by(rows, key):
    result = {}
    for row in rows:
        value = clean(row.get(key))
        if value:
            result[value] = row
    return result


def field_category(row):
    fact_type = clean(row.get("事实类型"))
    if fact_type.startswith("字段事实-"):
        return fact_type.split("-", 1)[1]
    return clean(row.get("字段名"))


def counter_text(rows, field):
    counter = Counter(clean(row.get(field)) for row in rows if clean(row.get(field)))
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()))


def progress_pdf_bucket(fact, result, pdf_ocr):
    if result and clean(result.get("PDF原页证据状态")):
        return clean(result.get("PDF原页证据状态"))
    if pdf_ocr and clean(pdf_ocr.get("PDFOCR候选审阅桶")):
        return clean(pdf_ocr.get("PDFOCR候选审阅桶"))
    return clean(fact.get("PDF原页记录状态")) or "pending_pdf_page_review"


def progress_ocr_bucket(result, pdf_ocr):
    if result and clean(result.get("OCR提示状态")):
        return clean(result.get("OCR提示状态"))
    if pdf_ocr and clean(pdf_ocr.get("PDFOCR候选记录状态")):
        return clean(pdf_ocr.get("PDFOCR候选记录状态"))
    return "OZ-页列或事实级待人工核验"


def progress_machine_bucket(result, machine):
    if result and clean(result.get("机器坐标提示状态")):
        return clean(result.get("机器坐标提示状态"))
    if machine and clean(machine.get("机器坐标候选审阅桶")):
        return clean(machine.get("机器坐标候选审阅桶"))
    return "MZ-无任务级机器坐标提示"


def progress_school_bucket(fact, result, task):
    if result and clean(result.get("高校辅证证据状态")):
        return clean(result.get("高校辅证证据状态"))
    if task and clean(task.get("高校官网或招生章程辅证状态")):
        return clean(task.get("高校官网或招生章程辅证状态"))
    return clean(fact.get("高校辅证记录状态")) or "for_double_check_only_not_official_plan_replacement"


def progress_conflict_bucket(fact, result, pdf_ocr, b0):
    if result and clean(result.get("冲突状态")):
        return clean(result.get("冲突状态"))
    if b0 and clean(b0.get("B0冲突优先级判定")):
        return clean(b0.get("B0冲突优先级判定"))
    if pdf_ocr and clean(pdf_ocr.get("PDFOCR与高校辅证关系桶")):
        return clean(pdf_ocr.get("PDFOCR与高校辅证关系桶"))
    return clean(fact.get("事实缺口桶")) or "CZ-待按页列核验"


def next_action(fact, result, evidence, b0):
    for row, field in [
        (result, "下一步核验动作"),
        (b0, "建议下一步动作"),
        (evidence, "页列建议下一步动作"),
        (fact, "人工最小核验动作"),
    ]:
        if row and clean(row.get(field)):
            return public_safe_text(row.get(field))
    return "按页列先核PDF原页，再核湖北官方侧；高校官网只作差异解释。"


def block_reason(fact, result):
    if result and clean(result.get("当前阻断原因")):
        return clean(result.get("当前阻断原因"))
    reasons = []
    if clean(fact.get("PDF原页记录状态")).startswith("pending"):
        reasons.append("PDF原页未闭环")
    if clean(fact.get("湖北官方侧记录状态")).startswith("pending"):
        reasons.append("湖北官方侧未闭环")
    if clean(fact.get("三方一致性状态")).startswith("pending"):
        reasons.append("三方一致性未闭环")
    return "；".join(reasons) or "待核验"


def public_policy():
    return "not_final；fact_progress_only；no_field_values；no_private_paths；no_ocr_text；no_recommendation"


def assert_public_safe(rows, label):
    text = json.dumps(rows, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"{label} contains forbidden public tokens: {hits[:5]}")


def main():
    fact_rows = read_csv(FACT_SCOPE)
    result_rows = read_csv(RESULT)
    field_rows = read_csv(FIELD_STATUS)
    evidence_rows = read_csv(PUBLIC_EVIDENCE_MAP)
    review_rows = read_csv(REVIEW_LEDGER)
    task_rows = read_csv(TASK_REVIEW)
    pdf_ocr_rows = read_csv(PDF_OCR_AUDIT)
    machine_rows = read_csv(MACHINE_AUDIT)
    b0_rows = read_csv(B0_CONFLICT)

    result_by_task = single_by(result_rows, "稳定基座第一闭环明细任务ID")
    task_by_task = single_by(task_rows, "稳定基座第一闭环明细任务ID")
    pdf_ocr_by_task = single_by(pdf_ocr_rows, "稳定基座第一闭环明细任务ID")
    machine_by_task = single_by(machine_rows, "稳定基座第一闭环明细任务ID")
    evidence_by_page = single_by(evidence_rows, "页码版面键")
    review_by_page = single_by(review_rows, "页码版面键")
    b0_by_page = single_by(b0_rows, "页码版面键")
    field_by_task_field = {
        (clean(row.get("稳定基座第一闭环明细任务ID")), clean(row.get("字段名"))): row
        for row in field_rows
    }

    progress_rows = []
    for index, fact in enumerate(fact_rows, start=1):
        task_id = clean(fact.get("稳定基座第一闭环明细任务ID"))
        page_key = clean(fact.get("页码版面键"))
        category = field_category(fact)
        result = result_by_task.get(task_id, {})
        task = task_by_task.get(task_id, {})
        pdf_ocr = pdf_ocr_by_task.get(task_id, {})
        machine = machine_by_task.get(task_id, {})
        field = field_by_task_field.get((task_id, category), {})
        evidence = evidence_by_page.get(page_key, {})
        review = review_by_page.get(page_key, {})
        b0 = b0_by_page.get(page_key, {})

        row = {
            "第一闭环事实进度公开账本ID": stable_id(
                "FCFACTPROG",
                [SOURCE_PDF_SHA256, clean(fact.get("第一闭环事实范围缺口公开账本ID"))],
            ),
            "来源第一闭环事实范围缺口账本": source_path(FACT_SCOPE),
            "来源第一闭环核验结果看板": source_path(RESULT),
            "来源第一闭环字段级公开状态": source_path(FIELD_STATUS),
            "来源第一闭环公开证据地图": source_path(PUBLIC_EVIDENCE_MAP),
            "来源第一闭环复核材料公开账本": source_path(REVIEW_LEDGER),
            "来源第一闭环任务复核公开账本": source_path(TASK_REVIEW),
            "来源第一闭环PDFOCR候选审计": source_path(PDF_OCR_AUDIT),
            "来源第一闭环机器坐标候选审计": source_path(MACHINE_AUDIT),
            "来源第一闭环B0冲突页列状态": source_path(B0_CONFLICT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环事实范围缺口进度",
            "任务粒度": "字段事实/专业名归属/专业组边界×证据状态",
            **{field_name: "false" for field_name in FALSE_FIELDS},
            "事实进度序号": index,
            "第一闭环事实范围缺口公开账本ID": fact.get("第一闭环事实范围缺口公开账本ID", ""),
            "事实域": fact.get("事实域", ""),
            "事实类型": fact.get("事实类型", ""),
            "事实粒度": fact.get("事实粒度", ""),
            "字段类别": category,
            "稳定基座第一闭环明细任务ID": task_id,
            "稳定基座第一闭环页列包ID": fact.get("稳定基座第一闭环页列包ID", ""),
            "来源页码": fact.get("来源页码", ""),
            "版面列": fact.get("版面列", ""),
            "页码版面键": page_key,
            "专业行ID": fact.get("专业行ID", ""),
            "专业组出现ID": fact.get("专业组出现ID", ""),
            "院校代码": fact.get("院校代码", ""),
            "执行泳道": fact.get("执行泳道", ""),
            "核验动作层级": fact.get("核验动作层级", ""),
            "页列主阻断": fact.get("页列主阻断", "") or evidence.get("页列主阻断", ""),
            "事实缺口桶": fact.get("事实缺口桶", ""),
            "PDF原页进度桶": progress_pdf_bucket(fact, result, pdf_ocr),
            "OCR提示进度桶": progress_ocr_bucket(result, pdf_ocr),
            "机器坐标进度桶": progress_machine_bucket(result, machine),
            "高校官网辅证进度桶": progress_school_bucket(fact, result, task),
            "冲突进度桶": progress_conflict_bucket(fact, result, pdf_ocr, b0),
            "湖北官方侧进度桶": fact.get("湖北官方侧记录状态", "") or "pending_hubei_official_plan_review",
            "双人复核进度桶": fact.get("双人复核状态", ""),
            "三方闭环状态": fact.get("三方一致性状态", ""),
            "字段事实写回状态": fact.get("字段事实写回状态", ""),
            "字段映射状态": field.get("字段映射状态", ""),
            "字段事实状态": field.get("字段事实状态", ""),
            "字段核验优先级": field.get("字段核验优先级", ""),
            "字段事实阻断等级": field.get("字段事实阻断等级", ""),
            "PDFOCR候选记录状态": pdf_ocr.get("PDFOCR候选记录状态", ""),
            "PDFOCR候选审阅桶": pdf_ocr.get("PDFOCR候选审阅桶", ""),
            "PDFOCR与高校辅证关系桶": pdf_ocr.get("PDFOCR与高校辅证关系桶", ""),
            "机器坐标候选记录状态": machine.get("机器坐标候选记录状态", ""),
            "机器坐标候选审阅桶": machine.get("机器坐标候选审阅桶", ""),
            "B0冲突闭环状态": b0.get("B0冲突闭环状态", ""),
            "B0冲突优先级判定": b0.get("B0冲突优先级判定", ""),
            "私有页图证据编号": review.get("私有页图证据编号", ""),
            "私有页图SHA256": review.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": review.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": review.get("私有OCR文本SHA256", ""),
            "私有页列CSV证据编号": review.get("私有第一闭环页列CSV证据编号", ""),
            "私有页列CSV_SHA256": review.get("私有第一闭环页列CSV_SHA256", ""),
            "私有页列HTML证据编号": review.get("私有第一闭环页列HTML证据编号", ""),
            "私有页列HTML_SHA256": review.get("私有第一闭环页列HTML_SHA256", ""),
            "最佳官网来源文件SHA256": task.get("最佳官网来源文件SHA256", ""),
            "裁图证据编号": task.get("裁图证据编号", ""),
            "裁图文件SHA256": task.get("裁图文件SHA256", ""),
            "PDFOCR候选记录证据编号": pdf_ocr.get("PDFOCR候选记录证据编号", ""),
            "机器坐标候选任务ID": machine.get("P0字段机器候选任务ID", ""),
            "完成条件": public_safe_text(fact.get("完成条件", "")),
            "下一步核验动作": next_action(fact, result, evidence, b0),
            "当前阻断原因": block_reason(fact, result),
            "公开安全策略": public_policy(),
        }
        progress_rows.append(row)

    progress_by_page = defaultdict(list)
    for row in progress_rows:
        progress_by_page[clean(row.get("页码版面键"))].append(row)

    page_rows = []
    for index, page_key in enumerate(sorted(progress_by_page, key=lambda value: (
        as_int(value.split("-", 1)[0]) if "-" in value else 9999,
        value,
    )), start=1):
        rows = progress_by_page[page_key]
        first = rows[0]
        evidence = evidence_by_page.get(page_key, {})
        review = review_by_page.get(page_key, {})
        page_rows.append(
            {
                "第一闭环事实进度页列汇总ID": stable_id("FCFACTPAGE", [SOURCE_PDF_SHA256, page_key]),
                "来源第一闭环事实进度账本": source_path(OUTPUT),
                "来源第一闭环公开证据地图": source_path(PUBLIC_EVIDENCE_MAP),
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "生成日期": GENERATED_AT,
                "数据阶段": DATA_STAGE,
                "主表粒度": "第一闭环事实进度页列汇总",
                "任务粒度": "PDF页码×版面列",
                **{field_name: "false" for field_name in FALSE_FIELDS},
                "页列汇总序号": index,
                "来源页码": first.get("来源页码", ""),
                "版面列": first.get("版面列", ""),
                "页码版面键": page_key,
                "执行泳道": first.get("执行泳道", "") or evidence.get("执行泳道", ""),
                "页列主阻断": first.get("页列主阻断", "") or evidence.get("页列主阻断", ""),
                "事实范围数": len(rows),
                "字段事实数": sum(row.get("事实域") == "字段事实" for row in rows),
                "专业名归属事实数": sum(row.get("事实域") == "专业名归属" for row in rows),
                "专业组边界事实数": sum(row.get("事实域") == "专业组边界" for row in rows),
                "涉及任务数": len({row.get("稳定基座第一闭环明细任务ID") for row in rows if row.get("稳定基座第一闭环明细任务ID")}),
                "涉及专业行数": len({row.get("专业行ID") for row in rows if row.get("专业行ID")}),
                "涉及院校代码数": len({row.get("院校代码") for row in rows if row.get("院校代码")}),
                "事实类型分布": counter_text(rows, "事实类型"),
                "字段类别分布": counter_text(rows, "字段类别"),
                "PDF原页进度桶分布": counter_text(rows, "PDF原页进度桶"),
                "OCR提示进度桶分布": counter_text(rows, "OCR提示进度桶"),
                "机器坐标进度桶分布": counter_text(rows, "机器坐标进度桶"),
                "高校官网辅证进度桶分布": counter_text(rows, "高校官网辅证进度桶"),
                "冲突进度桶分布": counter_text(rows, "冲突进度桶"),
                "湖北官方侧进度桶分布": counter_text(rows, "湖北官方侧进度桶"),
                "双人复核进度桶分布": counter_text(rows, "双人复核进度桶"),
                "B0冲突事实数": sum(bool(row.get("B0冲突闭环状态")) for row in rows),
                "需要双人复核事实数": sum("pending_double_review" in row.get("双人复核进度桶", "") for row in rows),
                "需要人工看图事实数": sum(row.get("事实缺口桶", "").startswith("G0") or "人工看图" in row.get("下一步核验动作", "") for row in rows),
                "私有页图SHA256": review.get("私有页图SHA256", ""),
                "私有OCR文本SHA256": review.get("私有OCR文本SHA256", ""),
                "私有页列CSV_SHA256": review.get("私有第一闭环页列CSV_SHA256", ""),
                "私有页列HTML_SHA256": review.get("私有第一闭环页列HTML_SHA256", ""),
                "事实范围集合SHA16": sha16(row.get("第一闭环事实范围缺口公开账本ID") for row in rows),
                "任务集合SHA16": sha16(row.get("稳定基座第一闭环明细任务ID") for row in rows),
                "专业行集合SHA16": sha16(row.get("专业行ID") for row in rows),
                "院校代码集合SHA16": sha16(row.get("院校代码") for row in rows),
                "PDF原页核页状态": "pending_pdf_page_review",
                "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
                "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
                "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
                "完成条件": "PDF原页、湖北官方侧、必要高校辅证和三方一致性均闭环后，才可进入字段写回评估。",
                "页列下一步核验动作": public_safe_text(evidence.get("页列建议下一步动作", "")) or next_action(
                    first,
                    {},
                    evidence,
                    b0_by_page.get(page_key, {}),
                ),
                "公开安全策略": public_policy(),
            }
        )

    assert_public_safe(progress_rows, "fact_progress")
    assert_public_safe(page_rows, "fact_progress_page")
    write_csv(OUTPUT, progress_rows, PROGRESS_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)

    summary = {
        "status": "issue19_first_closure_fact_progress_public_ledger_ready_not_final",
        "generated_by": "build_issue19_first_closure_fact_progress_public_ledger.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output": source_path(OUTPUT),
        "page_output": source_path(PAGE_OUTPUT),
        "fact_progress_row_count": len(progress_rows),
        "page_summary_row_count": len(page_rows),
        "unique_fact_scope_count": len({row["第一闭环事实范围缺口公开账本ID"] for row in progress_rows}),
        "unique_page_side_count": len({row["页码版面键"] for row in page_rows}),
        "unique_task_count": len({row["稳定基座第一闭环明细任务ID"] for row in progress_rows if row["稳定基座第一闭环明细任务ID"]}),
        "fact_domain_counts": dict(Counter(row["事实域"] for row in progress_rows)),
        "fact_type_counts": dict(Counter(row["事实类型"] for row in progress_rows)),
        "field_category_counts": dict(Counter(row["字段类别"] for row in progress_rows if row["事实域"] == "字段事实")),
        "pdf_progress_counts": dict(Counter(row["PDF原页进度桶"] for row in progress_rows)),
        "ocr_progress_counts": dict(Counter(row["OCR提示进度桶"] for row in progress_rows)),
        "machine_progress_counts": dict(Counter(row["机器坐标进度桶"] for row in progress_rows)),
        "school_source_progress_counts": dict(Counter(row["高校官网辅证进度桶"] for row in progress_rows)),
        "conflict_progress_counts": dict(Counter(row["冲突进度桶"] for row in progress_rows)),
        "hubei_official_pending_count": sum(row["湖北官方侧进度桶"].startswith("pending") for row in progress_rows),
        "pdf_pending_count": sum("pending" in row["PDF原页进度桶"] or row["PDF原页进度桶"].startswith("P") for row in progress_rows),
        "double_review_pending_count": sum("pending_double_review" in row["双人复核进度桶"] for row in progress_rows),
        "b0_conflict_fact_count": sum(bool(row["B0冲突闭环状态"]) for row in progress_rows),
        "official_page_finalize_allowed_count": 0,
        "platform_finalize_allowed_count": 0,
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "policy": "本账本只公开第一闭环事实范围的核验进度，不公开字段内容、OCR正文、截图路径或最终建议。",
    }
    write_json(SUMMARY_OUTPUT, summary)

    public_text = (
        OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + PAGE_OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + SUMMARY_OUTPUT.read_text(encoding="utf-8", errors="ignore")
    )
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if hits:
        raise SystemExit(f"public output contains forbidden tokens: {hits[:5]}")

    print(f"wrote {OUTPUT}")
    print(f"wrote {PAGE_OUTPUT}")
    print(f"wrote {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
