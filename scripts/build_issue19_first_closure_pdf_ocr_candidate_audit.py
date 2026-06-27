#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIRST_EXECUTION_QUEUE = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-execution-queue.csv"
)
FIRST_TASK_REVIEW = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv"
)
FIRST_PREFILL_AUDIT = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-triage-prefill-public-audit.csv"
)
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

PRIVATE_REVIEW_DIR = (
    ROOT / "private/review-assets/issue19-stable-foundation-first-closure-review"
)
PRIVATE_PREFILL_DIR = (
    ROOT / "private/review-assets/issue19-stable-foundation-first-closure-triage-prefill"
)
PRIVATE_PREFILL_MASTER = (
    PRIVATE_PREFILL_DIR / "first-closure-triage-prefill-private-workbench.csv"
)

PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-stable-foundation-first-closure-pdf-ocr-candidates"
)
PRIVATE_OUTPUT = PRIVATE_OUTPUT_DIR / "first-closure-pdf-ocr-candidates-private.csv"

PUBLIC_OUTPUT = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv"
)
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_pdf_ocr_candidate_public_audit"

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
    "第一闭环PDFOCR候选公开审计ID",
    "来源第一闭环执行队列",
    "来源第一闭环任务复核公开账本",
    "来源第一闭环私有预填公开审计",
    "来源第一闭环私有复核材料",
    "来源第一闭环PDFOCR候选私有工作台",
    "来源湖北官方公开入口状态快照",
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
    "PDFOCR候选审计总序",
    "第一闭环执行顺序",
    "执行泳道",
    "第一闭环页列优先级",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环任务复核公开账本ID",
    "稳定基座第一闭环页列包ID",
    "稳定基座第一闭环复核公开账本ID",
    "第一闭环私有预填公开审计ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "任务来源类型",
    "字段审计范围",
    "PDFOCR候选记录证据编号",
    "PDFOCR候选记录状态",
    "PDFOCR候选审阅桶",
    "PDFOCR与高校辅证关系桶",
    "PDFOCR候选字段数",
    "高校辅证候选字段数",
    "可比字段数",
    "一致字段数",
    "冲突字段数",
    "缺PDFOCR但有高校线索字段数",
    "是否有PDFOCR计划数候选",
    "是否有PDFOCR学费候选",
    "是否有PDFOCR选科候选",
    "是否有高校计划数线索",
    "是否有高校学费线索",
    "是否有高校选科线索",
    "是否存在PDFOCR与高校冲突",
    "是否存在PDFOCR与高校一致字段",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "是否可自动写入私有记录值",
    "PDF原页是否必核",
    "湖北官方侧是否必核",
    "高校辅证是否需要复核",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_EXTRA_FIELDS = [
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "专业代号OCR",
    "专业名称及备注短摘",
    "字段名",
    "差异字段集合",
    "PDFOCR计划数候选值",
    "PDFOCR学费候选值",
    "PDFOCR选科候选值",
    "高校辅证计划数候选值",
    "高校辅证学费候选值",
    "高校辅证选科候选值",
    "OCR行文本",
    "私有页图相对路径",
    "私有OCR文本相对路径",
    "最佳官网来源文件",
    "最佳官网来源文件SHA256",
    "候选不得自动写回声明",
]

PRIVATE_FIELDS = PUBLIC_FIELDS + PRIVATE_EXTRA_FIELDS

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
    "专业名称",
    "候选值",
    "候选计划数",
    "候选学费",
    "候选选科",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "OCR行文本",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "人工读数",
    "一审记录",
    "二审记录",
    "复核结论",
    "复核备注",
    "已确认",
    "已核准",
    "最终推荐",
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


def as_bool_text(value):
    return "true" if value else "false"


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def normalize(value):
    text = re.sub(r"\s+", "", str(value or ""))
    text = text.replace("，", ",").replace("；", ";")
    return text


def has_value(value):
    return bool(normalize(value))


def count_values(values):
    return sum(1 for value in values if has_value(value))


def infer_field_scope(row, review_row):
    field_name = row.get("字段名", "")
    if field_name:
        return field_name
    fields = []
    if has_value(review_row.get("OCR专业计划数候选")) or has_value(review_row.get("最佳官网计划数")):
        fields.append("专业计划数")
    if has_value(review_row.get("OCR学费候选")) or has_value(review_row.get("最佳官网学费")):
        fields.append("学费")
    if has_value(review_row.get("OCR再选科目候选")) or has_value(review_row.get("最佳官网选科")):
        fields.append("再选科目")
    return "；".join(fields) if fields else "待人工判定字段"


def relation_counts(review_row):
    pairs = [
        ("计划数", review_row.get("OCR专业计划数候选"), review_row.get("最佳官网计划数")),
        ("学费", review_row.get("OCR学费候选"), review_row.get("最佳官网学费")),
        ("选科", review_row.get("OCR再选科目候选"), review_row.get("最佳官网选科")),
    ]
    comparable = 0
    matched = 0
    conflict = 0
    missing_pdf_with_school = 0
    for _, pdf_value, school_value in pairs:
        pdf_has = has_value(pdf_value)
        school_has = has_value(school_value)
        if pdf_has and school_has:
            comparable += 1
            if normalize(pdf_value) == normalize(school_value):
                matched += 1
            else:
                conflict += 1
        elif not pdf_has and school_has:
            missing_pdf_with_school += 1
    return comparable, matched, conflict, missing_pdf_with_school


def relation_bucket(review_row):
    comparable, matched, conflict, missing_pdf_with_school = relation_counts(review_row)
    pdf_count = count_values([
        review_row.get("OCR专业计划数候选"),
        review_row.get("OCR学费候选"),
        review_row.get("OCR再选科目候选"),
    ])
    school_count = count_values([
        review_row.get("最佳官网计划数"),
        review_row.get("最佳官网学费"),
        review_row.get("最佳官网选科"),
    ])
    if conflict:
        return "R0-PDFOCR与高校辅证存在冲突"
    if matched:
        return "R1-PDFOCR与高校辅证存在一致字段"
    if missing_pdf_with_school:
        return "R2-高校有线索但PDFOCR缺候选"
    if pdf_count:
        return "R3-仅PDFOCR候选待人工核页"
    if school_count:
        return "R4-仅高校辅证线索待回页"
    return "R5-无候选需人工看图"


def review_bucket(review_row):
    relation = relation_bucket(review_row)
    if relation.startswith("R0"):
        return "P0-候选冲突优先核PDF原页"
    if relation.startswith("R2") or relation.startswith("R5"):
        return "P1-缺PDFOCR候选需人工看图"
    if relation.startswith("R1"):
        return "P2-候选一致仍需官方闭环"
    return "P3-有候选但需人工确认"


def load_private_review_rows():
    result = {}
    for path in sorted((PRIVATE_REVIEW_DIR / "page-sides").glob("*.csv")):
        for row in read_csv(path):
            result[row["稳定基座第一闭环明细任务ID"]] = row
    return result


def ensure_public_safe(rows, summary):
    text_parts = [
        ",".join(row.get(field, "") for field in PUBLIC_FIELDS)
        for row in rows
    ]
    text_parts.append(json.dumps(summary, ensure_ascii=False))
    public_text = "\n".join(text_parts)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if hits:
        raise RuntimeError(f"公开PDFOCR候选审计含禁止内容: {hits[:20]}")


def build_rows():
    execution_rows = read_csv(FIRST_EXECUTION_QUEUE)
    task_rows = read_csv(FIRST_TASK_REVIEW)
    prefill_rows = read_csv(FIRST_PREFILL_AUDIT)
    private_review_by_task_id = load_private_review_rows()
    private_prefill_by_task_id = {
        row["稳定基座第一闭环明细任务ID"]: row
        for row in read_csv(PRIVATE_PREFILL_MASTER)
    }
    execution_by_key = {row["页码版面键"]: row for row in execution_rows}
    prefill_audit_by_key = {row["页码版面键"]: row for row in prefill_rows}

    rows = []
    private_rows = []
    ordered_tasks = sorted(
        task_rows,
        key=lambda row: (
            int(execution_by_key[row["页码版面键"]]["执行顺序"]),
            row["稳定基座第一闭环明细任务ID"],
        ),
    )
    for index, task in enumerate(ordered_tasks, start=1):
        task_id = task["稳定基座第一闭环明细任务ID"]
        key = task["页码版面键"]
        execution = execution_by_key[key]
        prefill_audit = prefill_audit_by_key[key]
        review_private = private_review_by_task_id[task_id]
        prefill_private = private_prefill_by_task_id[task_id]
        pdf_count = count_values([
            review_private.get("OCR专业计划数候选"),
            review_private.get("OCR学费候选"),
            review_private.get("OCR再选科目候选"),
        ])
        school_count = count_values([
            review_private.get("最佳官网计划数"),
            review_private.get("最佳官网学费"),
            review_private.get("最佳官网选科"),
        ])
        comparable, matched, conflict, missing_pdf_with_school = relation_counts(review_private)
        public_id = stable_id("FIRSTPDFOCR", [task_id])
        evidence_id = f"FIRST-CLOSURE-PDFOCR-CAND-{public_id}"
        row = {
            "第一闭环PDFOCR候选公开审计ID": public_id,
            "来源第一闭环执行队列": str(FIRST_EXECUTION_QUEUE.relative_to(ROOT)),
            "来源第一闭环任务复核公开账本": str(FIRST_TASK_REVIEW.relative_to(ROOT)),
            "来源第一闭环私有预填公开审计": str(FIRST_PREFILL_AUDIT.relative_to(ROOT)),
            "来源第一闭环私有复核材料": "first_closure_private_review_material_not_public",
            "来源第一闭环PDFOCR候选私有工作台": "first_closure_pdf_ocr_candidate_private_workbench_not_public",
            "来源湖北官方公开入口状态快照": str(OFFICIAL_STATUS.relative_to(ROOT)),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细×第一闭环任务",
            "任务粒度": "逐任务×PDF原页OCR候选公开状态",
            **false_gate_values(),
            "PDFOCR候选审计总序": str(index),
            "第一闭环执行顺序": execution["执行顺序"],
            "执行泳道": execution["执行泳道"],
            "第一闭环页列优先级": task["第一闭环页列优先级"],
            "稳定基座第一闭环明细任务ID": task_id,
            "稳定基座第一闭环任务复核公开账本ID": task["稳定基座第一闭环任务复核公开账本ID"],
            "稳定基座第一闭环页列包ID": task["稳定基座第一闭环页列包ID"],
            "稳定基座第一闭环复核公开账本ID": task["稳定基座第一闭环复核公开账本ID"],
            "第一闭环私有预填公开审计ID": prefill_audit["第一闭环私有预填公开审计ID"],
            "来源页码": task["来源页码"],
            "版面列": task["版面列"],
            "页码版面键": key,
            "任务来源类型": task["任务来源类型"],
            "字段审计范围": infer_field_scope(task, review_private),
            "PDFOCR候选记录证据编号": evidence_id,
            "PDFOCR候选记录状态": (
                "private_pdf_ocr_candidate_seeded"
                if pdf_count
                else "private_pdf_ocr_candidate_unavailable_needs_manual_image_review"
            ),
            "PDFOCR候选审阅桶": review_bucket(review_private),
            "PDFOCR与高校辅证关系桶": relation_bucket(review_private),
            "PDFOCR候选字段数": str(pdf_count),
            "高校辅证候选字段数": str(school_count),
            "可比字段数": str(comparable),
            "一致字段数": str(matched),
            "冲突字段数": str(conflict),
            "缺PDFOCR但有高校线索字段数": str(missing_pdf_with_school),
            "是否有PDFOCR计划数候选": as_bool_text(has_value(review_private.get("OCR专业计划数候选"))),
            "是否有PDFOCR学费候选": as_bool_text(has_value(review_private.get("OCR学费候选"))),
            "是否有PDFOCR选科候选": as_bool_text(has_value(review_private.get("OCR再选科目候选"))),
            "是否有高校计划数线索": as_bool_text(has_value(review_private.get("最佳官网计划数"))),
            "是否有高校学费线索": as_bool_text(has_value(review_private.get("最佳官网学费"))),
            "是否有高校选科线索": as_bool_text(has_value(review_private.get("最佳官网选科"))),
            "是否存在PDFOCR与高校冲突": as_bool_text(conflict > 0),
            "是否存在PDFOCR与高校一致字段": as_bool_text(matched > 0),
            "是否需要人工直接看图": as_bool_text(conflict > 0 or pdf_count == 0),
            "是否需要双人复核": task["是否需要双人复核"],
            "是否可自动写入私有记录值": "false",
            "PDF原页是否必核": task["PDF原页是否必核"],
            "湖北官方侧是否必核": task["湖北官方侧是否必核"],
            "高校辅证是否需要复核": task["高校辅证是否需要复核"],
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "高校官网或招生章程辅证状态": "pending_if_school_clue_present",
            "三方字段一致性状态": "pending_private_three_way_field_confirmation",
            "字段事实写回状态": "blocked_until_private_pdf_hubei_review_confirms_values",
            "公开安全策略": "公开表只保存候选存在性、关系桶、计数、证据编号和门禁；私有候选明细、识别正文、私有路径和人工记录不进入公开仓库。",
            "下一步": "打开私有PDFOCR候选工作台和页列复核材料，人工回看PDF原页；完成湖北官方侧和必要高校辅证后再更新私有复核记录。",
        }
        private_row = {
            **row,
            "专业行ID": task.get("专业行ID", ""),
            "专业组出现ID": task.get("专业组出现ID", ""),
            "院校代码": task.get("院校代码", ""),
            "院校名称OCR": review_private.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": review_private.get("院校专业组代码OCR规范化", ""),
            "专业代号OCR": review_private.get("专业代号OCR", ""),
            "专业名称及备注短摘": review_private.get("专业名称及备注短摘", ""),
            "字段名": task.get("字段名", ""),
            "差异字段集合": task.get("差异字段集合", ""),
            "PDFOCR计划数候选值": review_private.get("OCR专业计划数候选", ""),
            "PDFOCR学费候选值": review_private.get("OCR学费候选", ""),
            "PDFOCR选科候选值": review_private.get("OCR再选科目候选", ""),
            "高校辅证计划数候选值": prefill_private.get("高校辅证候选计划数", ""),
            "高校辅证学费候选值": prefill_private.get("高校辅证候选学费", ""),
            "高校辅证选科候选值": prefill_private.get("高校辅证候选选科", ""),
            "OCR行文本": review_private.get("OCR行文本", ""),
            "私有页图相对路径": review_private.get("私有页图相对路径", ""),
            "私有OCR文本相对路径": review_private.get("私有OCR文本相对路径", ""),
            "最佳官网来源文件": prefill_private.get("最佳官网来源文件", ""),
            "最佳官网来源文件SHA256": prefill_private.get("最佳官网来源文件SHA256", ""),
            "候选不得自动写回声明": "PDFOCR候选和高校辅证候选都只能作为核页提示；必须经PDF原页人工读数、湖北官方侧核验、必要高校辅证和双人复核后，才可进入字段确认。",
        }
        rows.append(row)
        private_rows.append(private_row)
    return rows, private_rows


def build_summary(rows):
    return {
        "status": "issue19_stable_foundation_first_closure_pdf_ocr_candidate_public_audit_not_final",
        "generated_by": Path(__file__).name,
        "source_first_closure_execution_queue": str(FIRST_EXECUTION_QUEUE.relative_to(ROOT)),
        "source_first_closure_task_review_public_ledger": str(FIRST_TASK_REVIEW.relative_to(ROOT)),
        "source_first_closure_triage_prefill_public_audit": str(FIRST_PREFILL_AUDIT.relative_to(ROOT)),
        "source_private_review_material": "first_closure_private_review_material_not_public",
        "source_private_triage_prefill_material": "first_closure_triage_prefill_private_material_not_public",
        "source_official_public_status": str(OFFICIAL_STATUS.relative_to(ROOT)),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": str(PUBLIC_OUTPUT.relative_to(ROOT)),
        "source_private_pdf_ocr_candidate_workbench": "first_closure_pdf_ocr_candidate_private_workbench_not_public",
        "public_row_count": len(rows),
        "unique_task_count": len({row["稳定基座第一闭环明细任务ID"] for row in rows}),
        "unique_page_side_count": len({row["页码版面键"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "candidate_record_status_counts": dict(Counter(row["PDFOCR候选记录状态"] for row in rows)),
        "candidate_review_bucket_counts": dict(Counter(row["PDFOCR候选审阅桶"] for row in rows)),
        "candidate_relation_bucket_counts": dict(Counter(row["PDFOCR与高校辅证关系桶"] for row in rows)),
        "execution_lane_counts": dict(Counter(row["执行泳道"] for row in rows)),
        "page_side_priority_counts": dict(Counter(row["第一闭环页列优先级"] for row in rows)),
        "task_source_type_counts": dict(Counter(row["任务来源类型"] for row in rows)),
        "pdf_ocr_candidate_task_count": sum(row["PDFOCR候选字段数"] != "0" for row in rows),
        "school_candidate_task_count": sum(row["高校辅证候选字段数"] != "0" for row in rows),
        "comparable_field_task_count": sum(row["可比字段数"] != "0" for row in rows),
        "matched_field_task_count": sum(row["一致字段数"] != "0" for row in rows),
        "conflict_field_task_count": sum(row["冲突字段数"] != "0" for row in rows),
        "missing_pdf_ocr_with_school_task_count": sum(row["缺PDFOCR但有高校线索字段数"] != "0" for row in rows),
        "direct_image_review_required_count": sum(row["是否需要人工直接看图"] == "true" for row in rows),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in rows),
        "pdf_required_count": sum(row["PDF原页是否必核"] == "true" for row in rows),
        "hubei_official_required_count": sum(row["湖北官方侧是否必核"] == "true" for row in rows),
        "school_support_required_count": sum(row["高校辅证是否需要复核"] == "true" for row in rows),
        "auto_private_record_write_allowed_count": sum(row["是否可自动写入私有记录值"] == "true" for row in rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段事实"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "official_plan_replacement_allowed_count": sum(row["是否允许官网证据替代湖北官方计划"] == "true" for row in rows),
        "public_boundary": "公开表只保存候选存在性、关系桶、计数、证据编号和门禁；候选明细只在私有工作台。",
    }


def main():
    rows, private_rows = build_rows()
    write_csv(PRIVATE_OUTPUT, private_rows, PRIVATE_FIELDS)
    summary = build_summary(rows)
    summary["private_pdf_ocr_candidate_workbench_sha256"] = sha256(PRIVATE_OUTPUT)
    ensure_public_safe(rows, summary)
    write_csv(PUBLIC_OUTPUT, rows, PUBLIC_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {PUBLIC_OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {PRIVATE_OUTPUT.relative_to(ROOT)}：{len(private_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
