#!/usr/bin/env python3
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

NEXT_ACTION = WORKING / "issue19-stable-foundation-first-closure-next-action-matrix.csv"
NEXT_ACTION_PAGE = WORKING / "issue19-stable-foundation-first-closure-next-action-page-summary.csv"
EVIDENCE_STATUS = WORKING / "issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv"
FIELD_TASKS = WORKING / "issue19-field-fact-verification-tasks.csv"
SCHOOL_SOURCE_E0 = WORKING / "issue19-school-source-e0-manual-page-review-queue-public-ledger.csv"

OUTPUT = WORKING / "issue19-first-closure-verification-result-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-first-closure-verification-result-page-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-verification-result-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_first_closure_verification_result_board"
GENERATED_AT = "2026-06-29"
PACKET_TASK_LIMIT = 10

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

RESULT_FIELDS = [
    "第一闭环核验结果ID",
    "来源第一闭环下一步动作矩阵",
    "来源第一闭环页列下一步汇总",
    "来源第一闭环证据状态账本",
    "来源字段事实核验任务",
    "来源高校源E0人工回页队列",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "结果序号",
    "第一闭环下一步动作ID",
    "第一闭环证据状态公开账本ID",
    "第一闭环页列下一步动作ID",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环页列包ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "任务来源类型",
    "字段名",
    "执行泳道",
    "第一闭环页列优先级",
    "核验动作层级",
    "任务结果桶",
    "核验结果状态",
    "PDF原页证据状态",
    "OCR提示状态",
    "机器坐标提示状态",
    "高校辅证证据状态",
    "湖北官方侧状态",
    "冲突状态",
    "三方闭环状态",
    "字段写回门禁",
    "是否有PDFOCR提示",
    "是否有机器坐标提示",
    "是否有高校辅证线索",
    "是否存在PDFOCR与高校冲突",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "专业行字段任务数",
    "专业行P0字段任务数",
    "专业行P1字段任务数",
    "专业行P3字段任务数",
    "专业行字段状态分布",
    "专业行字段缺口类型分布",
    "页列任务数",
    "页列双人复核任务数",
    "页列人工看图任务数",
    "页列高校辅证线索任务数",
    "页列核验动作层级分布",
    "同校E0人工回页提示状态",
    "同校E0人工回页任务数",
    "同校E0人工回页风险桶分布",
    "同校E0人工回页队列集合SHA16",
    "完成证据要求",
    "当前阻断原因",
    "下一步核验动作",
    "公开安全策略",
]

PAGE_FIELDS = [
    "第一闭环核验结果页列汇总ID",
    "来源第一闭环核验结果表",
    "来源第一闭环下一步动作页列汇总",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "页列汇总序号",
    "第一闭环页列下一步动作ID",
    "稳定基座第一闭环页列包ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "执行泳道",
    "第一闭环页列优先级",
    "页列任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "N0冲突双人核页任务数",
    "N1高校补缺回页任务数",
    "N2机器坐标辅助核页任务数",
    "N3无候选人工看图任务数",
    "N4PDFOCR候选确认任务数",
    "N5多源一致待官核任务数",
    "PDF原页待核任务数",
    "湖北官方侧待核任务数",
    "高校辅证线索任务数",
    "需要双人复核任务数",
    "需要人工直接看图任务数",
    "任务结果桶分布",
    "OCR提示状态分布",
    "冲突状态分布",
    "字段优先级分布",
    "专业行字段缺口类型分布",
    "页列主阻断",
    "页列建议下一步动作",
    "建议人工核验小包类型",
    "建议物理小包数量",
    "建议每包任务上限",
    "关联任务集合SHA16",
    "关联专业行集合SHA16",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "字段事实写回状态",
    "完成条件",
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
    "OCR行文本",
    "字段确认值",
    "人工读数",
    "候选值",
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


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha16(values):
    normalized = "\n".join(sorted({str(value).strip() for value in values if str(value).strip()}))
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def counter_text(counter):
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()) if key)


def page_side_key(row):
    return (row.get("来源页码", ""), row.get("版面列", ""))


def boolish(row, field):
    return str(row.get(field, "")).strip().lower() == "true"


def result_bucket(row):
    conflict = row.get("冲突状态", "")
    action = row.get("核验动作层级", "")
    if action.startswith("N0-") or conflict.startswith("C0-"):
        return "R0-冲突优先双人核PDF原页和湖北官方侧"
    if action.startswith("N1-") or conflict.startswith("C1-"):
        return "R1-高校补缺线索回PDF原页"
    if action.startswith("N2-"):
        return "R2-机器坐标辅助核PDF原页"
    if action.startswith("N3-") or conflict.startswith("C4-"):
        return "R3-无稳定候选需人工看图"
    if action.startswith("N4-") or conflict.startswith("C3-"):
        return "R4-PDFOCR候选人工确认"
    if action.startswith("N5-") or conflict.startswith("C2-"):
        return "R5-多源一致线索仍待湖北官方侧"
    return "R9-待人工分流"


def result_status(row):
    if (
        row.get("PDF原页核页状态", "") == "pending_pdf_page_review"
        and row.get("湖北官方系统或省招办计划核验状态", "") == "pending_hubei_official_plan_review"
    ):
        return "pending_pdf_hubei_school_closure"
    return "pending_manual_review"


def blocking_reason(row):
    reasons = []
    if row.get("PDF原页核页状态", "") == "pending_pdf_page_review":
        reasons.append("PDF原页未完成逐项核页")
    if row.get("湖北官方系统或省招办计划核验状态", "") == "pending_hubei_official_plan_review":
        reasons.append("湖北官方系统或省招办计划未闭环")
    if row.get("高校辅证证据状态", "").startswith("S1-"):
        reasons.append("高校官网辅证仍待私有记录或回页核验")
    if row.get("冲突状态", "").startswith("C0-"):
        reasons.append("PDFOCR与高校辅证存在冲突线索")
    if row.get("冲突状态", "").startswith("C4-"):
        reasons.append("无可比候选，需人工看图")
    return "；".join(reasons) or "仍未满足三方闭环写回条件"


def field_distribution(field_rows, field):
    return counter_text(Counter(row.get(field, "") for row in field_rows))


def packet_type(rows):
    buckets = Counter(row.get("任务结果桶", "") for row in rows)
    if any(bucket.startswith("R0-") for bucket in buckets):
        return "P0-冲突双人核页包"
    if any(bucket.startswith("R3-") for bucket in buckets):
        return "P1-人工看图补候选包"
    if any(bucket.startswith("R1-") for bucket in buckets):
        return "P2-高校补缺回页包"
    if any(bucket.startswith("R2-") for bucket in buckets):
        return "P3-机器坐标辅助核页包"
    if any(bucket.startswith("R4-") for bucket in buckets):
        return "P4-PDFOCR候选确认包"
    return "P5-官核闭环确认包"


def build_rows():
    next_rows = read_csv(NEXT_ACTION)
    next_page_rows = read_csv(NEXT_ACTION_PAGE)
    evidence_rows = read_csv(EVIDENCE_STATUS)
    field_rows = read_csv(FIELD_TASKS)
    school_rows = read_csv(SCHOOL_SOURCE_E0)

    evidence_by_task = {
        row.get("稳定基座第一闭环明细任务ID", ""): row
        for row in evidence_rows
        if row.get("稳定基座第一闭环明细任务ID", "")
    }
    page_by_key = {page_side_key(row): row for row in next_page_rows}

    fields_by_major = defaultdict(list)
    for row in field_rows:
        fields_by_major[row.get("专业行ID", "")].append(row)

    school_e0_by_code = defaultdict(list)
    for row in school_rows:
        school_e0_by_code[row.get("院校代码", "")].append(row)

    result_rows = []
    for index, row in enumerate(next_rows, start=1):
        task_id = row.get("稳定基座第一闭环明细任务ID", "")
        evidence = evidence_by_task.get(task_id, {})
        page = page_by_key.get(page_side_key(row), {})
        major_fields = fields_by_major.get(row.get("专业行ID", ""), [])
        school_e0 = school_e0_by_code.get(row.get("院校代码", ""), [])

        p0_count = sum(f.get("字段核验优先级", "").startswith("P0-") for f in major_fields)
        p1_count = sum(f.get("字段核验优先级", "").startswith("P1-") for f in major_fields)
        p3_count = sum(f.get("字段核验优先级", "").startswith("P3-") for f in major_fields)
        bucket = result_bucket(row)

        result_rows.append({
            "第一闭环核验结果ID": stable_id(
                "FIRSTRESULT",
                [row.get("第一闭环下一步动作ID", ""), task_id, SOURCE_PDF_SHA256],
            ),
            "来源第一闭环下一步动作矩阵": "data/working/issue19-stable-foundation-first-closure-next-action-matrix.csv",
            "来源第一闭环页列下一步汇总": "data/working/issue19-stable-foundation-first-closure-next-action-page-summary.csv",
            "来源第一闭环证据状态账本": "data/working/issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv",
            "来源字段事实核验任务": "data/working/issue19-field-fact-verification-tasks.csv",
            "来源高校源E0人工回页队列": "data/working/issue19-school-source-e0-manual-page-review-queue-public-ledger.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环高风险明细任务",
            "任务粒度": "逐任务×PDF/OCR/高校官网/湖北官方/冲突状态",
            **{field: "false" for field in FALSE_FIELDS},
            "结果序号": str(index),
            "第一闭环下一步动作ID": row.get("第一闭环下一步动作ID", ""),
            "第一闭环证据状态公开账本ID": evidence.get("第一闭环证据状态公开账本ID", ""),
            "第一闭环页列下一步动作ID": page.get("第一闭环页列下一步动作ID", ""),
            "稳定基座第一闭环明细任务ID": task_id,
            "稳定基座第一闭环页列包ID": row.get("稳定基座第一闭环页列包ID", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "页码版面键": row.get("页码版面键", ""),
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "任务来源类型": row.get("任务来源类型", ""),
            "字段名": row.get("字段名", ""),
            "执行泳道": row.get("执行泳道", ""),
            "第一闭环页列优先级": row.get("第一闭环页列优先级", ""),
            "核验动作层级": row.get("核验动作层级", ""),
            "任务结果桶": bucket,
            "核验结果状态": result_status(row),
            "PDF原页证据状态": row.get("PDF原页证据状态", ""),
            "OCR提示状态": row.get("OCR提示状态", ""),
            "机器坐标提示状态": row.get("机器坐标提示状态", ""),
            "高校辅证证据状态": row.get("高校辅证证据状态", ""),
            "湖北官方侧状态": row.get("湖北官方侧状态", ""),
            "冲突状态": row.get("冲突状态", ""),
            "三方闭环状态": row.get("三方闭环状态", ""),
            "字段写回门禁": row.get("字段写回门禁", ""),
            "是否有PDFOCR提示": row.get("是否有PDFOCR提示", ""),
            "是否有机器坐标提示": row.get("是否有机器坐标提示", ""),
            "是否有高校辅证线索": row.get("是否有高校辅证线索", ""),
            "是否存在PDFOCR与高校冲突": row.get("是否存在PDFOCR与高校冲突", ""),
            "是否需要人工直接看图": row.get("是否需要人工直接看图", ""),
            "是否需要双人复核": row.get("是否需要双人复核", ""),
            "专业行字段任务数": str(len(major_fields)),
            "专业行P0字段任务数": str(p0_count),
            "专业行P1字段任务数": str(p1_count),
            "专业行P3字段任务数": str(p3_count),
            "专业行字段状态分布": field_distribution(major_fields, "字段事实状态"),
            "专业行字段缺口类型分布": field_distribution(major_fields, "字段事实缺口类型"),
            "页列任务数": page.get("页列任务数", ""),
            "页列双人复核任务数": page.get("N0冲突双人核页任务数", ""),
            "页列人工看图任务数": page.get("N3无候选人工看图任务数", ""),
            "页列高校辅证线索任务数": page.get("高校辅证线索任务数", ""),
            "页列核验动作层级分布": page.get("核验动作层级分布", ""),
            "同校E0人工回页提示状态": (
                "H1-同校存在E0人工回页队列" if school_e0 else "H0-同校暂无E0人工回页队列"
            ),
            "同校E0人工回页任务数": str(len(school_e0)),
            "同校E0人工回页风险桶分布": counter_text(Counter(r.get("人工回页风险桶", "") for r in school_e0)),
            "同校E0人工回页队列集合SHA16": sha16(r.get("高校源E0人工回页队列ID", "") for r in school_e0),
            "完成证据要求": row.get("完成条件", ""),
            "当前阻断原因": blocking_reason(row),
            "下一步核验动作": row.get("人工最小核验动作", "") or row.get("页列建议下一步动作", ""),
            "公开安全策略": "公开结果表只保存状态、计数、ID和SHA；不保存学校专业文本、字段读数、OCR正文、截图路径、人工记录、登录态或个人身份信息。",
        })

    result_rows.sort(
        key=lambda r: (
            as_int(r.get("来源页码")),
            r.get("版面列", ""),
            r.get("执行泳道", ""),
            as_int(r.get("结果序号")),
        )
    )
    for index, row in enumerate(result_rows, start=1):
        row["结果序号"] = str(index)

    rows_by_page = defaultdict(list)
    for row in result_rows:
        rows_by_page[(row.get("来源页码", ""), row.get("版面列", ""))].append(row)

    page_rows = []
    for index, page in enumerate(next_page_rows, start=1):
        rows = rows_by_page.get(page_side_key(page), [])
        major_ids = [row.get("专业行ID", "") for row in rows]
        school_codes = [row.get("院校代码", "") for row in rows]
        field_rows_for_page = []
        for major_id in sorted({value for value in major_ids if value}):
            field_rows_for_page.extend(fields_by_major.get(major_id, []))
        packet_count = max(1, math.ceil(len(rows) / PACKET_TASK_LIMIT)) if rows else 0

        page_rows.append({
            "第一闭环核验结果页列汇总ID": stable_id(
                "FIRSTRESULTPAGE",
                [page.get("第一闭环页列下一步动作ID", ""), SOURCE_PDF_SHA256],
            ),
            "来源第一闭环核验结果表": "data/working/issue19-first-closure-verification-result-public-ledger.csv",
            "来源第一闭环下一步动作页列汇总": "data/working/issue19-stable-foundation-first-closure-next-action-page-summary.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": f"{DATA_STAGE}_page_summary",
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "页列×核验结果汇总×建议人工小包",
            **{field: "false" for field in FALSE_FIELDS},
            "页列汇总序号": str(index),
            "第一闭环页列下一步动作ID": page.get("第一闭环页列下一步动作ID", ""),
            "稳定基座第一闭环页列包ID": page.get("稳定基座第一闭环页列包ID", ""),
            "来源页码": page.get("来源页码", ""),
            "版面列": page.get("版面列", ""),
            "页码版面键": page.get("页码版面键", ""),
            "执行泳道": page.get("执行泳道", ""),
            "第一闭环页列优先级": page.get("第一闭环页列优先级", ""),
            "页列任务数": str(len(rows)),
            "涉及专业行数": str(len({value for value in major_ids if value})),
            "涉及院校代码数": str(len({value for value in school_codes if value})),
            "N0冲突双人核页任务数": str(sum(r.get("核验动作层级", "").startswith("N0-") for r in rows)),
            "N1高校补缺回页任务数": str(sum(r.get("核验动作层级", "").startswith("N1-") for r in rows)),
            "N2机器坐标辅助核页任务数": str(sum(r.get("核验动作层级", "").startswith("N2-") for r in rows)),
            "N3无候选人工看图任务数": str(sum(r.get("核验动作层级", "").startswith("N3-") for r in rows)),
            "N4PDFOCR候选确认任务数": str(sum(r.get("核验动作层级", "").startswith("N4-") for r in rows)),
            "N5多源一致待官核任务数": str(sum(r.get("核验动作层级", "").startswith("N5-") for r in rows)),
            "PDF原页待核任务数": str(sum(bool(r.get("PDF原页证据状态", "")) for r in rows)),
            "湖北官方侧待核任务数": str(sum(r.get("湖北官方侧状态", "") == "pending_hubei_official_review" for r in rows)),
            "高校辅证线索任务数": str(sum(r.get("高校辅证证据状态", "").startswith("S1-") for r in rows)),
            "需要双人复核任务数": str(sum(boolish(r, "是否需要双人复核") for r in rows)),
            "需要人工直接看图任务数": str(sum(boolish(r, "是否需要人工直接看图") for r in rows)),
            "任务结果桶分布": counter_text(Counter(r.get("任务结果桶", "") for r in rows)),
            "OCR提示状态分布": counter_text(Counter(r.get("OCR提示状态", "") for r in rows)),
            "冲突状态分布": counter_text(Counter(r.get("冲突状态", "") for r in rows)),
            "字段优先级分布": counter_text(Counter(r.get("字段核验优先级", "") for r in field_rows_for_page)),
            "专业行字段缺口类型分布": counter_text(Counter(r.get("字段事实缺口类型", "") for r in field_rows_for_page)),
            "页列主阻断": page.get("页列主阻断", ""),
            "页列建议下一步动作": page.get("页列建议下一步动作", ""),
            "建议人工核验小包类型": packet_type(rows),
            "建议物理小包数量": str(packet_count),
            "建议每包任务上限": str(PACKET_TASK_LIMIT),
            "关联任务集合SHA16": sha16(row.get("第一闭环下一步动作ID", "") for row in rows),
            "关联专业行集合SHA16": sha16(major_ids),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网或招生章程辅证状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "完成条件": page.get("完成条件", ""),
            "公开安全策略": "页列汇总只保存状态、计数、分布、ID和SHA；不保存学校专业文本、字段读数、OCR正文、图片路径、人工记录或登录态。",
        })

    page_rows.sort(key=lambda r: (as_int(r.get("来源页码")), r.get("版面列", "")))
    for index, row in enumerate(page_rows, start=1):
        row["页列汇总序号"] = str(index)

    return result_rows, page_rows, next_rows, next_page_rows, field_rows, school_rows


def ensure_public_safe(paths):
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    return [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]


def main():
    result_rows, page_rows, next_rows, next_page_rows, field_rows, school_rows = build_rows()
    write_csv(OUTPUT, result_rows, RESULT_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)

    unsafe_tokens = ensure_public_safe([OUTPUT, PAGE_OUTPUT])
    if unsafe_tokens:
        raise SystemExit(f"公开产物包含禁止词：{unsafe_tokens[:5]}")

    summary = {
        "status": "issue19_first_closure_verification_result_board_not_final",
        "generated_by": "build_issue19_first_closure_verification_result_board.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_next_action_matrix": "data/working/issue19-stable-foundation-first-closure-next-action-matrix.csv",
        "source_next_action_page_summary": "data/working/issue19-stable-foundation-first-closure-next-action-page-summary.csv",
        "source_evidence_status": "data/working/issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv",
        "source_field_tasks": "data/working/issue19-field-fact-verification-tasks.csv",
        "source_school_source_e0_manual_queue": "data/working/issue19-school-source-e0-manual-page-review-queue-public-ledger.csv",
        "output_result_table": "data/working/issue19-first-closure-verification-result-public-ledger.csv",
        "output_page_summary": "data/working/issue19-first-closure-verification-result-page-summary.csv",
        "row_grain": "第一闭环高风险明细任务",
        "page_summary_grain": "PDF页码×版面列",
        "result_row_count": len(result_rows),
        "page_summary_row_count": len(page_rows),
        "source_next_action_row_count": len(next_rows),
        "source_page_side_row_count": len(next_page_rows),
        "unique_result_id_count": len({row["第一闭环核验结果ID"] for row in result_rows}),
        "unique_task_count": len({row["第一闭环下一步动作ID"] for row in result_rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in page_rows}),
        "unique_major_line_count": len({row["专业行ID"] for row in result_rows if row["专业行ID"]}),
        "field_task_linked_count": sum(as_int(row["专业行字段任务数"]) for row in result_rows),
        "result_bucket_counts": dict(Counter(row["任务结果桶"] for row in result_rows)),
        "execution_lane_counts": dict(Counter(row["执行泳道"] for row in result_rows)),
        "action_level_counts": dict(Counter(row["核验动作层级"] for row in result_rows)),
        "pdf_status_counts": dict(Counter(row["PDF原页证据状态"] for row in result_rows)),
        "ocr_status_counts": dict(Counter(row["OCR提示状态"] for row in result_rows)),
        "school_source_status_counts": dict(Counter(row["高校辅证证据状态"] for row in result_rows)),
        "conflict_status_counts": dict(Counter(row["冲突状态"] for row in result_rows)),
        "e0_manual_hint_counts": dict(Counter(row["同校E0人工回页提示状态"] for row in result_rows)),
        "page_packet_type_counts": dict(Counter(row["建议人工核验小包类型"] for row in page_rows)),
        "suggested_physical_packet_count": sum(as_int(row["建议物理小包数量"]) for row in page_rows),
        "packet_task_limit": PACKET_TASK_LIMIT,
        "pdf_pending_task_count": sum(bool(row["PDF原页证据状态"]) for row in result_rows),
        "hubei_official_pending_task_count": sum(
            row["湖北官方侧状态"] == "pending_hubei_official_review" for row in result_rows
        ),
        "school_source_hint_task_count": sum(
            row["高校辅证证据状态"].startswith("S1-") for row in result_rows
        ),
        "double_review_required_count": sum(boolish(row, "是否需要双人复核") for row in result_rows),
        "direct_image_review_required_count": sum(boolish(row, "是否需要人工直接看图") for row in result_rows),
        "field_writeback_ready_count": sum(row["字段写回门禁"] != "blocked_until_required_private_readings_complete" for row in result_rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in result_rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in result_rows),
        "official_plan_replacement_allowed_count": sum(row["是否允许官网证据替代湖北官方计划"] == "true" for row in result_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in result_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in result_rows),
        "source_field_task_total_count": len(field_rows),
        "source_school_source_e0_count": len(school_rows),
        "public_boundary": "该表只是第一闭环核验结果看板，展示PDF/OCR/机器坐标/高校官网/湖北官方/冲突状态；不确认计划数、学费、选科、专业名或专业组边界事实，不进入志愿推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)


if __name__ == "__main__":
    main()
