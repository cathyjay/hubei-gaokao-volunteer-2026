#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

NEXT_ACTION = WORKING / "issue19-stable-foundation-first-closure-next-action-matrix.csv"
FIELD_TASKS = WORKING / "issue19-field-fact-verification-tasks.csv"
SCHOOL_SOURCE_E0 = WORKING / "issue19-school-source-e0-manual-page-review-queue-public-ledger.csv"

OUTPUT = WORKING / "issue19-first-closure-field-verification-status-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-field-verification-status-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_first_closure_field_verification_status"
GENERATED_AT = "2026-06-29"
ALLOWED_FIELDS = {"专业计划数", "学费", "再选科目", "待人工判定字段"}

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

FIELDS = [
    "第一闭环字段核验状态ID",
    "来源第一闭环下一步动作矩阵",
    "来源字段事实核验任务",
    "来源高校源E0人工回页队列",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "字段状态序号",
    "第一闭环下一步动作ID",
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
    "字段映射状态",
    "字段事实核验任务ID",
    "字段事实状态",
    "字段核验优先级",
    "字段PDF核验状态",
    "字段湖北官方核验状态",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "字段事实缺口类型",
    "PDF原页证据状态",
    "OCR提示状态",
    "机器坐标提示状态",
    "高校辅证证据状态",
    "湖北官方侧状态",
    "冲突状态",
    "三方闭环状态",
    "核验动作层级",
    "执行泳道",
    "同校高校源可用性",
    "同校高校源最高证据层级",
    "同校E0人工回页任务数",
    "同校E0风险桶分布",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "当前阻断原因",
    "下一步核验动作",
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
    "字段OCR候选",
    "字段人工确认",
    "字段候选值集合",
    "专业名称及备注",
    "院校名称OCR",
    "人工读数",
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


def split_fields(value):
    return [part for part in str(value or "").split("；") if part]


def blocking_reason(row, field_row):
    reasons = []
    if row.get("PDF原页核页状态") == "pending_pdf_page_review":
        reasons.append("PDF原页未完成逐字段核页")
    if row.get("湖北官方系统或省招办计划核验状态") == "pending_hubei_official_plan_review":
        reasons.append("湖北官方系统或省招办计划未核验")
    if field_row and field_row.get("字段事实状态", "").startswith("K0-"):
        reasons.append("字段无稳定提示需原页重读")
    if row.get("冲突状态", "").startswith("C0-"):
        reasons.append("存在PDFOCR与高校辅证冲突线索")
    return "；".join(reasons) or "字段未满足写回条件"


def counter_text(counter):
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()) if key)


def build_rows():
    next_rows = read_csv(NEXT_ACTION)
    field_rows = read_csv(FIELD_TASKS)
    school_rows = read_csv(SCHOOL_SOURCE_E0)
    field_by_major_name = {
        (row.get("专业行ID", ""), row.get("字段名", "")): row
        for row in field_rows
        if row.get("专业行ID") and row.get("字段名")
    }
    school_e0_by_code = defaultdict(list)
    for row in school_rows:
        school_e0_by_code[row.get("院校代码", "")].append(row)

    rows = []
    for action in next_rows:
        fields = split_fields(action.get("字段名", ""))
        for field_name in fields:
            if field_name not in ALLOWED_FIELDS:
                raise SystemExit(f"发现未允许字段名：{field_name}")
            field_row = field_by_major_name.get((action.get("专业行ID", ""), field_name), {})
            school_e0 = school_e0_by_code.get(action.get("院校代码", ""), [])
            rows.append({
                "第一闭环字段核验状态ID": stable_id(
                    "FIRSTFIELDSTATUS",
                    [action.get("稳定基座第一闭环明细任务ID", ""), field_name, SOURCE_PDF_SHA256],
                ),
                "来源第一闭环下一步动作矩阵": "data/working/issue19-stable-foundation-first-closure-next-action-matrix.csv",
                "来源字段事实核验任务": "data/working/issue19-field-fact-verification-tasks.csv",
                "来源高校源E0人工回页队列": "data/working/issue19-school-source-e0-manual-page-review-queue-public-ledger.csv",
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "生成日期": GENERATED_AT,
                "数据阶段": DATA_STAGE,
                "主表粒度": "第一闭环明细任务×待核字段",
                "任务粒度": "拆分后的字段级公开核验状态；不保存字段读数或候选文本",
                **{field: "false" for field in FALSE_FIELDS},
                "字段状态序号": "",
                "第一闭环下一步动作ID": action.get("第一闭环下一步动作ID", ""),
                "稳定基座第一闭环明细任务ID": action.get("稳定基座第一闭环明细任务ID", ""),
                "稳定基座第一闭环页列包ID": action.get("稳定基座第一闭环页列包ID", ""),
                "来源页码": action.get("来源页码", ""),
                "版面列": action.get("版面列", ""),
                "页码版面键": action.get("页码版面键", ""),
                "专业行ID": action.get("专业行ID", ""),
                "专业组出现ID": action.get("专业组出现ID", ""),
                "院校代码": action.get("院校代码", ""),
                "任务来源类型": action.get("任务来源类型", ""),
                "字段名": field_name,
                "字段映射状态": "M1-已映射字段事实核验任务" if field_row else "M0-待人工判定字段未映射",
                "字段事实核验任务ID": field_row.get("字段事实核验任务ID", ""),
                "字段事实状态": field_row.get("字段事实状态", ""),
                "字段核验优先级": field_row.get("字段核验优先级", ""),
                "字段PDF核验状态": field_row.get("字段PDF核验状态", ""),
                "字段湖北官方核验状态": field_row.get("字段湖北官方核验状态", ""),
                "字段事实闭环等级": field_row.get("字段事实闭环等级", ""),
                "字段事实阻断等级": field_row.get("字段事实阻断等级", ""),
                "字段事实缺口类型": field_row.get("字段事实缺口类型", ""),
                "PDF原页证据状态": action.get("PDF原页证据状态", ""),
                "OCR提示状态": action.get("OCR提示状态", ""),
                "机器坐标提示状态": action.get("机器坐标提示状态", ""),
                "高校辅证证据状态": action.get("高校辅证证据状态", ""),
                "湖北官方侧状态": action.get("湖北官方侧状态", ""),
                "冲突状态": action.get("冲突状态", ""),
                "三方闭环状态": action.get("三方闭环状态", ""),
                "核验动作层级": action.get("核验动作层级", ""),
                "执行泳道": action.get("执行泳道", ""),
                "同校高校源可用性": action.get("同校高校源可用性", ""),
                "同校高校源最高证据层级": action.get("同校高校源最高证据层级", ""),
                "同校E0人工回页任务数": str(len(school_e0)),
                "同校E0风险桶分布": counter_text(Counter(row.get("人工回页风险桶", "") for row in school_e0)),
                "PDF原页核页状态": action.get("PDF原页核页状态", ""),
                "湖北官方系统或省招办计划核验状态": action.get("湖北官方系统或省招办计划核验状态", ""),
                "高校官网源状态": action.get("高校官网源状态", ""),
                "字段事实写回状态": action.get("字段事实写回状态", ""),
                "当前阻断原因": blocking_reason(action, field_row),
                "下一步核验动作": action.get("人工最小核验动作", ""),
                "公开安全策略": "字段级公开状态只保存ID、状态桶、计数和核验动作；不保存院校名称、专业名称、字段读数、OCR正文、人工记录、图片路径或登录态。",
            })

    rows.sort(
        key=lambda row: (
            int(row.get("来源页码", "0") or "0"),
            row.get("版面列", ""),
            row.get("稳定基座第一闭环明细任务ID", ""),
            row.get("字段名", ""),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["字段状态序号"] = str(index)
    return rows, next_rows, field_rows, school_rows


def ensure_public_safe(paths):
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    return [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]


def main():
    rows, next_rows, field_rows, school_rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    unsafe_tokens = ensure_public_safe([OUTPUT])
    if unsafe_tokens:
        raise SystemExit(f"公开产物包含禁止词：{unsafe_tokens[:5]}")

    summary = {
        "status": "issue19_first_closure_field_verification_status_not_final",
        "generated_by": "build_issue19_first_closure_field_verification_status.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_next_action_matrix": "data/working/issue19-stable-foundation-first-closure-next-action-matrix.csv",
        "source_field_tasks": "data/working/issue19-field-fact-verification-tasks.csv",
        "source_school_source_e0_manual_queue": "data/working/issue19-school-source-e0-manual-page-review-queue-public-ledger.csv",
        "output_table": "data/working/issue19-first-closure-field-verification-status-public-ledger.csv",
        "row_grain": "第一闭环明细任务×待核字段",
        "row_count": len(rows),
        "source_next_action_row_count": len(next_rows),
        "source_field_task_row_count": len(field_rows),
        "source_school_source_e0_count": len(school_rows),
        "unique_status_id_count": len({row["第一闭环字段核验状态ID"] for row in rows}),
        "unique_task_field_count": len({(row["稳定基座第一闭环明细任务ID"], row["字段名"]) for row in rows}),
        "field_counts": dict(Counter(row["字段名"] for row in rows)),
        "field_mapping_status_counts": dict(Counter(row["字段映射状态"] for row in rows)),
        "field_fact_status_counts": dict(Counter(row["字段事实状态"] for row in rows)),
        "field_priority_counts": dict(Counter(row["字段核验优先级"] for row in rows)),
        "pdf_status_counts": dict(Counter(row["PDF原页核页状态"] for row in rows)),
        "hubei_official_status_counts": dict(Counter(row["湖北官方系统或省招办计划核验状态"] for row in rows)),
        "writeback_status_counts": dict(Counter(row["字段事实写回状态"] for row in rows)),
        "mapped_field_count": sum(row["字段映射状态"].startswith("M1-") for row in rows),
        "unmapped_field_count": sum(row["字段映射状态"].startswith("M0-") for row in rows),
        "field_writeback_ready_count": sum(
            row["字段事实写回状态"] != "blocked_until_pdf_hubei_school_three_way_closure"
            for row in rows
        ),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "official_plan_replacement_allowed_count": sum(row["是否允许官网证据替代湖北官方计划"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "public_boundary": "该表只把第一闭环206条任务拆成字段级公开状态，不确认任何字段事实，不保存字段读数，不进入推荐或写回。",
    }
    write_json(SUMMARY_OUTPUT, summary)


if __name__ == "__main__":
    main()
