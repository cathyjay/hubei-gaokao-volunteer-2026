#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

PAGE_SUMMARY = WORKING / "issue19-stable-foundation-first-closure-evidence-status-page-side-summary.csv"
TASK_REVIEW = WORKING / "issue19-stable-foundation-first-closure-task-review-public-ledger.csv"
PREFILL_AUDIT = WORKING / "issue19-stable-foundation-first-closure-triage-prefill-public-audit.csv"
OFFICIAL_STATUS = WORKING / "issue19-official-public-entry-status.json"

OUTPUT_CSV = WORKING / "issue19-stable-foundation-first-closure-public-evidence-map.csv"
SUMMARY_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-public-evidence-map-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_public_evidence_map"

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

OUTPUT_FIELDS = [
    "第一闭环公开证据地图ID",
    "来源页列证据状态汇总",
    "来源任务复核公开账本",
    "来源私有预填公开审计",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    *FALSE_FIELDS,
    "执行顺序",
    "来源页码",
    "版面列",
    "页码版面键",
    "执行泳道",
    "第一闭环页列优先级",
    "页列任务数",
    "自动官网辅证任务数",
    "P0人工字段任务数",
    "专业计划数字段任务数",
    "学费字段任务数",
    "再选科目字段任务数",
    "PDF原页待核任务数",
    "PDFOCR提示任务数",
    "PDFOCR无候选任务数",
    "机器坐标提示任务数",
    "高校辅证线索任务数",
    "高校辅证待核任务数",
    "公共高校来源文件任务数",
    "公共高校来源文件数",
    "湖北官方侧待核任务数",
    "PDFOCR与高校辅证冲突任务数",
    "高校有线索但PDFOCR缺候选任务数",
    "仅PDFOCR候选待人工核页任务数",
    "需要人工直接看图任务数",
    "需要双人复核任务数",
    "页列主阻断",
    "页列建议下一步动作",
    "字段事实写回阻断任务数",
    "字段事实写回可进入任务数",
    "官方公开计划页可定稿",
    "数智平台可定稿",
    "完成条件",
    "公开安全策略",
]

FORBIDDEN_TOKENS = [
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
    "专业代号",
    "OCR原文",
    "字段确认值",
    "人工读数",
    "候选值",
    "湖北官方字段值",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def rel(path):
    return str(path.relative_to(ROOT))


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def digest(parts):
    text = "|".join(str(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def false_gates():
    return {field: "false" for field in FALSE_FIELDS}


def as_int(value):
    try:
        return int(str(value).strip() or "0")
    except ValueError:
        return 0


def bool_text(value):
    return "true" if bool(value) else "false"


def official_flags():
    obj = json.loads(OFFICIAL_STATUS.read_text(encoding="utf-8"))
    return {
        "official_plan_page_can_finalize": bool(obj.get("official_plan_page", {}).get("can_finalize")),
        "zspt_platform_can_finalize": bool(obj.get("zspt_platform", {}).get("can_finalize")),
    }


def build_rows():
    page_rows = read_csv(PAGE_SUMMARY)
    task_rows = read_csv(TASK_REVIEW)
    prefill_rows = read_csv(PREFILL_AUDIT)
    prefill_by_key = {row.get("页码版面键", ""): row for row in prefill_rows}
    flags = official_flags()

    source_sha_by_page = {}
    for row in task_rows:
        key = row.get("页码版面键", "")
        sha = row.get("最佳官网来源文件SHA256", "")
        if sha:
            source_sha_by_page.setdefault(key, set()).add(sha)

    output = []
    for row in sorted(page_rows, key=lambda item: as_int(item.get("执行顺序"))):
        key = row.get("页码版面键", "")
        prefill = prefill_by_key.get(key, {})
        source_file_count = prefill.get("公共高校来源文件数")
        if source_file_count == "":
            source_file_count = str(len(source_sha_by_page.get(key, set())))
        output.append({
            "第一闭环公开证据地图ID": f"FIRSTEVIDMAP-{digest([key, row.get('执行顺序', '')])}",
            "来源页列证据状态汇总": rel(PAGE_SUMMARY),
            "来源任务复核公开账本": rel(TASK_REVIEW),
            "来源私有预填公开审计": rel(PREFILL_AUDIT),
            "来源湖北官方公开入口状态快照": rel(OFFICIAL_STATUS),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列×公开证据地图",
            **false_gates(),
            "执行顺序": row.get("执行顺序", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "页码版面键": key,
            "执行泳道": row.get("执行泳道", ""),
            "第一闭环页列优先级": row.get("第一闭环页列优先级", ""),
            "页列任务数": row.get("页列任务数", ""),
            "自动官网辅证任务数": row.get("自动官网辅证任务数", ""),
            "P0人工字段任务数": row.get("P0人工字段任务数", ""),
            "专业计划数字段任务数": row.get("专业计划数字段任务数", ""),
            "学费字段任务数": row.get("学费字段任务数", ""),
            "再选科目字段任务数": row.get("再选科目字段任务数", ""),
            "PDF原页待核任务数": row.get("PDF原页待核任务数", ""),
            "PDFOCR提示任务数": row.get("PDFOCR提示任务数", ""),
            "PDFOCR无候选任务数": row.get("PDFOCR无候选任务数", ""),
            "机器坐标提示任务数": row.get("机器坐标提示任务数", ""),
            "高校辅证线索任务数": row.get("高校辅证线索任务数", ""),
            "高校辅证待核任务数": row.get("高校辅证待核任务数", ""),
            "公共高校来源文件任务数": prefill.get("公共高校来源文件任务数", ""),
            "公共高校来源文件数": source_file_count,
            "湖北官方侧待核任务数": row.get("湖北官方侧待核任务数", ""),
            "PDFOCR与高校辅证冲突任务数": row.get("PDFOCR与高校辅证冲突任务数", ""),
            "高校有线索但PDFOCR缺候选任务数": row.get("高校有线索但PDFOCR缺候选任务数", ""),
            "仅PDFOCR候选待人工核页任务数": row.get("仅PDFOCR候选待人工核页任务数", ""),
            "需要人工直接看图任务数": row.get("需要人工直接看图任务数", ""),
            "需要双人复核任务数": row.get("需要双人复核任务数", ""),
            "页列主阻断": row.get("页列主阻断", ""),
            "页列建议下一步动作": row.get("页列建议下一步动作", ""),
            "字段事实写回阻断任务数": row.get("字段事实写回阻断任务数", ""),
            "字段事实写回可进入任务数": row.get("字段事实写回可进入任务数", ""),
            "官方公开计划页可定稿": bool_text(flags["official_plan_page_can_finalize"]),
            "数智平台可定稿": bool_text(flags["zspt_platform_can_finalize"]),
            "完成条件": row.get("完成条件", ""),
            "公开安全策略": "公开层只保存页列状态桶、计数、集合SHA和门禁；不公开学校专业明细、字段读数、识别正文、截图、人工记录或私有路径。",
        })
    return output


def validate(rows, summary):
    if len(rows) != 37:
        raise ValueError(f"expected 37 page-side rows, got {len(rows)}")
    if sum(as_int(row["页列任务数"]) for row in rows) != 206:
        raise ValueError("task count must sum to 206")
    if any(row[field] != "false" for row in rows for field in FALSE_FIELDS):
        raise ValueError("non-final gate drifted")
    if summary["field_writeback_ready_count"] != 0:
        raise ValueError("field writeback must stay blocked")
    text = json.dumps(summary, ensure_ascii=False) + "\n"
    text += "\n".join(",".join(str(row.get(field, "")) for field in OUTPUT_FIELDS) for row in rows)
    leaked = [token for token in FORBIDDEN_TOKENS if token in text]
    if leaked:
        raise ValueError(f"public map contains forbidden token(s): {leaked[:10]}")


def build_summary(rows):
    blocker_counts = Counter(row["页列主阻断"] for row in rows)
    lane_counts = Counter(row["执行泳道"] for row in rows)
    priority_counts = Counter(row["第一闭环页列优先级"] for row in rows)
    source_sha_values = {
        row.get("最佳官网来源文件SHA256", "")
        for row in read_csv(TASK_REVIEW)
        if row.get("最佳官网来源文件SHA256", "")
    }
    return {
        "status": "issue19_stable_foundation_first_closure_public_evidence_map_not_final",
        "generated_by": "build_issue19_first_closure_public_evidence_map.py",
        "source_page_summary": rel(PAGE_SUMMARY),
        "source_task_review": rel(TASK_REVIEW),
        "source_prefill_audit": rel(PREFILL_AUDIT),
        "source_official_public_entry_status": rel(OFFICIAL_STATUS),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_csv": rel(OUTPUT_CSV),
        "row_grain": "PDF页码×版面列",
        "row_count": len(rows),
        "task_count": sum(as_int(row["页列任务数"]) for row in rows),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows if row["来源页码"]}),
        "lane_counts": dict(lane_counts),
        "priority_counts": dict(priority_counts),
        "main_blocker_counts": dict(blocker_counts),
        "pdf_pending_task_count": sum(as_int(row["PDF原页待核任务数"]) for row in rows),
        "hubei_official_pending_task_count": sum(as_int(row["湖北官方侧待核任务数"]) for row in rows),
        "pdf_ocr_hint_task_count": sum(as_int(row["PDFOCR提示任务数"]) for row in rows),
        "pdf_ocr_no_candidate_task_count": sum(as_int(row["PDFOCR无候选任务数"]) for row in rows),
        "machine_coordinate_hint_task_count": sum(as_int(row["机器坐标提示任务数"]) for row in rows),
        "school_support_hint_task_count": sum(as_int(row["高校辅证线索任务数"]) for row in rows),
        "public_school_source_file_task_count": sum(as_int(row["公共高校来源文件任务数"]) for row in rows),
        "public_school_source_unique_sha_count": len(source_sha_values),
        "pdf_school_conflict_task_count": sum(as_int(row["PDFOCR与高校辅证冲突任务数"]) for row in rows),
        "direct_image_review_required_count": sum(as_int(row["需要人工直接看图任务数"]) for row in rows),
        "double_review_required_count": sum(as_int(row["需要双人复核任务数"]) for row in rows),
        "official_public_plan_page_can_finalize": False,
        "zspt_platform_can_finalize": False,
        "field_writeback_ready_count": sum(as_int(row["字段事实写回可进入任务数"]) for row in rows),
        "field_writeback_blocked_task_count": sum(as_int(row["字段事实写回阻断任务数"]) for row in rows),
        "final_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "public_boundary": "公开证据地图只保存37个页列的状态桶和计数，不保存学校专业明细、字段读数、识别正文、截图、人工记录或私有路径。",
        "next_use": "用于向家庭解释第一闭环每个页列卡在PDF/OCR/高校辅证/湖北官方/冲突的哪一步，不能作为字段事实或志愿推荐依据。",
    }


def main():
    rows = build_rows()
    summary = build_summary(rows)
    validate(rows, summary)
    write_csv(OUTPUT_CSV, rows, OUTPUT_FIELDS)
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
