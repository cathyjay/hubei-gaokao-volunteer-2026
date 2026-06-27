#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIRST_EXECUTION_QUEUE = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-execution-queue.csv"
)
FIRST_PDF_OCR_CANDIDATE_AUDIT = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv"
)
FIRST_PDF_OCR_CANDIDATE_SUMMARY = (
    ROOT
    / "data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit-summary.json"
)
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

PUBLIC_OUTPUT = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-page-side-candidate-dashboard.csv"
)
SUMMARY_OUTPUT = (
    ROOT
    / "data/working/issue19-stable-foundation-first-closure-page-side-candidate-dashboard-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_page_side_candidate_dashboard"

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
    "第一闭环页列候选看板ID",
    "来源第一闭环执行队列",
    "来源第一闭环PDFOCR候选公开审计",
    "来源第一闭环PDFOCR候选摘要",
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
    "执行顺序",
    "执行泳道",
    "第一闭环页列优先级",
    "稳定基座第一闭环页列包ID",
    "稳定基座第一闭环复核公开账本ID",
    "第一闭环私有预填公开审计ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列总任务数",
    "PDFOCR候选任务数",
    "无PDFOCR需看图任务数",
    "PDFOCR与高校辅证冲突任务数",
    "PDFOCR与高校辅证一致任务数",
    "仅PDFOCR候选任务数",
    "高校有线索但PDFOCR缺候选任务数",
    "无任何候选需看图任务数",
    "P0候选冲突任务数",
    "P1缺PDFOCR人工看图任务数",
    "P2一致仍需官方闭环任务数",
    "P3有候选需人工确认任务数",
    "PDFOCR候选字段数",
    "高校辅证候选字段数",
    "可比字段数",
    "一致字段数",
    "冲突字段数",
    "缺PDFOCR但有高校线索字段数",
    "PDFOCR计划数候选任务数",
    "PDFOCR学费候选任务数",
    "PDFOCR选科候选任务数",
    "高校计划数线索任务数",
    "高校学费线索任务数",
    "高校选科线索任务数",
    "需要人工直接看图任务数",
    "需要双人复核任务数",
    "PDF原页必核任务数",
    "湖北官方侧必核任务数",
    "高校辅证需复核任务数",
    "第一闭环PDF原页完成任务数",
    "第一闭环湖北官方完成任务数",
    "第一闭环高校辅证完成任务数",
    "第一闭环字段事实写回可进入任务数",
    "候选记录状态摘要",
    "候选审阅桶摘要",
    "候选关系桶摘要",
    "页列候选核验动作",
    "PDFOCR候选私有工作台_SHA256",
    "官方公开计划页可定稿",
    "数智平台可定稿",
    "完成条件",
    "当前阻断原因",
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


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def as_bool(value):
    return str(value).strip().lower() == "true"


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def page_side_key(row):
    return (str(row.get("来源页码", "")).strip(), str(row.get("版面列", "")).strip())


def key_text(key):
    page, side = key
    return f"{int(page):03d}-{side}" if str(page).isdigit() else f"{page}-{side}"


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


def join_counter(counter, limit=6):
    items = [(key, value) for key, value in counter.most_common() if key]
    return "；".join(f"{key}:{value}" for key, value in items[:limit])


def page_action(row):
    if as_int(row["PDFOCR与高校辅证冲突任务数"]):
        return "先核PDFOCR与高校辅证冲突任务，再做双人复核"
    if as_int(row["无PDFOCR需看图任务数"]):
        return "先人工看图补PDF原页读数，再核湖北官方侧"
    if as_int(row["PDFOCR与高校辅证一致任务数"]):
        return "先抽核一致字段原页，再等待或补核湖北官方侧"
    if as_int(row["PDFOCR候选任务数"]):
        return "先按PDFOCR候选逐条人工确认原页"
    return "先人工看图建立PDF原页读数"


def completion_condition(row):
    return (
        f"PDF原页记录完成={row['PDF原页必核任务数']}；"
        f"湖北官方侧记录完成={row['湖北官方侧必核任务数']}或记录官方系统不可得状态；"
        f"高校辅证记录完成={row['高校辅证需复核任务数']}；"
        f"双人复核完成={row['需要双人复核任务数']}；"
        "字段事实写回复查通过后才可进入下一层"
    )


def blocker_reason(row):
    blockers = []
    if row["第一闭环PDF原页完成任务数"] != row["PDF原页必核任务数"]:
        blockers.append("PDF原页记录未完成")
    if row["第一闭环湖北官方完成任务数"] != row["湖北官方侧必核任务数"]:
        blockers.append("湖北官方侧记录未完成或不可得状态未确认")
    if as_int(row["高校辅证需复核任务数"]) and (
        row["第一闭环高校辅证完成任务数"] != row["高校辅证需复核任务数"]
    ):
        blockers.append("高校辅证记录未完成")
    if as_int(row["需要双人复核任务数"]):
        blockers.append("双人复核未完成")
    blockers.append("字段事实写回仍阻断")
    return "；".join(blockers)


def build_rows():
    execution_rows = read_csv(FIRST_EXECUTION_QUEUE)
    candidate_rows = read_csv(FIRST_PDF_OCR_CANDIDATE_AUDIT)
    candidate_summary = json.loads(FIRST_PDF_OCR_CANDIDATE_SUMMARY.read_text(encoding="utf-8"))
    official = load_official_status()

    candidate_by_key = defaultdict(list)
    for row in candidate_rows:
        candidate_by_key[page_side_key(row)].append(row)

    built = []
    for execution in execution_rows:
        key = page_side_key(execution)
        tasks = candidate_by_key.get(key, [])
        status_counter = Counter(row.get("PDFOCR候选记录状态", "") for row in tasks)
        review_counter = Counter(row.get("PDFOCR候选审阅桶", "") for row in tasks)
        relation_counter = Counter(row.get("PDFOCR与高校辅证关系桶", "") for row in tasks)

        row = {
            "第一闭环页列候选看板ID": stable_id(
                "FIRSTPAGECAND", [SOURCE_PDF_SHA256, key_text(key)]
            ),
            "来源第一闭环执行队列": str(FIRST_EXECUTION_QUEUE.relative_to(ROOT)),
            "来源第一闭环PDFOCR候选公开审计": str(
                FIRST_PDF_OCR_CANDIDATE_AUDIT.relative_to(ROOT)
            ),
            "来源第一闭环PDFOCR候选摘要": str(
                FIRST_PDF_OCR_CANDIDATE_SUMMARY.relative_to(ROOT)
            ),
            "来源第一闭环PDFOCR候选私有工作台": "first_closure_pdf_ocr_candidate_private_workbench_not_public",
            "来源湖北官方公开入口状态快照": str(OFFICIAL_STATUS.relative_to(ROOT)),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×第一闭环PDFOCR候选状态",
            **false_gate_values(),
            "执行顺序": execution.get("执行顺序", ""),
            "执行泳道": execution.get("执行泳道", ""),
            "第一闭环页列优先级": execution.get("第一闭环页列优先级", ""),
            "稳定基座第一闭环页列包ID": execution.get("稳定基座第一闭环页列包ID", ""),
            "稳定基座第一闭环复核公开账本ID": execution.get("稳定基座第一闭环复核公开账本ID", ""),
            "第一闭环私有预填公开审计ID": execution.get("第一闭环私有预填公开审计ID", ""),
            "来源页码": execution.get("来源页码", ""),
            "版面列": execution.get("版面列", ""),
            "页码版面键": execution.get("页码版面键", ""),
            "页列总任务数": str(len(tasks)),
            "PDFOCR候选任务数": str(sum(as_int(row.get("PDFOCR候选字段数")) > 0 for row in tasks)),
            "无PDFOCR需看图任务数": str(
                sum(
                    row.get("PDFOCR候选记录状态")
                    == "private_pdf_ocr_candidate_unavailable_needs_manual_image_review"
                    for row in tasks
                )
            ),
            "PDFOCR与高校辅证冲突任务数": str(
                sum(row.get("是否存在PDFOCR与高校冲突") == "true" for row in tasks)
            ),
            "PDFOCR与高校辅证一致任务数": str(
                sum(row.get("是否存在PDFOCR与高校一致字段") == "true" for row in tasks)
            ),
            "仅PDFOCR候选任务数": str(
                sum(row.get("PDFOCR与高校辅证关系桶") == "R3-仅PDFOCR候选待人工核页" for row in tasks)
            ),
            "高校有线索但PDFOCR缺候选任务数": str(
                sum(row.get("PDFOCR与高校辅证关系桶") == "R2-高校有线索但PDFOCR缺候选" for row in tasks)
            ),
            "无任何候选需看图任务数": str(
                sum(row.get("PDFOCR与高校辅证关系桶") == "R5-无候选需人工看图" for row in tasks)
            ),
            "P0候选冲突任务数": str(
                sum(row.get("PDFOCR候选审阅桶") == "P0-候选冲突优先核PDF原页" for row in tasks)
            ),
            "P1缺PDFOCR人工看图任务数": str(
                sum(row.get("PDFOCR候选审阅桶") == "P1-缺PDFOCR候选需人工看图" for row in tasks)
            ),
            "P2一致仍需官方闭环任务数": str(
                sum(row.get("PDFOCR候选审阅桶") == "P2-候选一致仍需官方闭环" for row in tasks)
            ),
            "P3有候选需人工确认任务数": str(
                sum(row.get("PDFOCR候选审阅桶") == "P3-有候选但需人工确认" for row in tasks)
            ),
            "PDFOCR候选字段数": str(sum(as_int(row.get("PDFOCR候选字段数")) for row in tasks)),
            "高校辅证候选字段数": str(sum(as_int(row.get("高校辅证候选字段数")) for row in tasks)),
            "可比字段数": str(sum(as_int(row.get("可比字段数")) for row in tasks)),
            "一致字段数": str(sum(as_int(row.get("一致字段数")) for row in tasks)),
            "冲突字段数": str(sum(as_int(row.get("冲突字段数")) for row in tasks)),
            "缺PDFOCR但有高校线索字段数": str(
                sum(as_int(row.get("缺PDFOCR但有高校线索字段数")) for row in tasks)
            ),
            "PDFOCR计划数候选任务数": str(sum(as_bool(row.get("是否有PDFOCR计划数候选")) for row in tasks)),
            "PDFOCR学费候选任务数": str(sum(as_bool(row.get("是否有PDFOCR学费候选")) for row in tasks)),
            "PDFOCR选科候选任务数": str(sum(as_bool(row.get("是否有PDFOCR选科候选")) for row in tasks)),
            "高校计划数线索任务数": str(sum(as_bool(row.get("是否有高校计划数线索")) for row in tasks)),
            "高校学费线索任务数": str(sum(as_bool(row.get("是否有高校学费线索")) for row in tasks)),
            "高校选科线索任务数": str(sum(as_bool(row.get("是否有高校选科线索")) for row in tasks)),
            "需要人工直接看图任务数": str(sum(as_bool(row.get("是否需要人工直接看图")) for row in tasks)),
            "需要双人复核任务数": str(sum(as_bool(row.get("是否需要双人复核")) for row in tasks)),
            "PDF原页必核任务数": str(sum(as_bool(row.get("PDF原页是否必核")) for row in tasks)),
            "湖北官方侧必核任务数": str(sum(as_bool(row.get("湖北官方侧是否必核")) for row in tasks)),
            "高校辅证需复核任务数": str(sum(as_bool(row.get("高校辅证是否需要复核")) for row in tasks)),
            "第一闭环PDF原页完成任务数": execution.get("第一闭环PDF原页完成任务数", "0"),
            "第一闭环湖北官方完成任务数": execution.get("第一闭环湖北官方完成任务数", "0"),
            "第一闭环高校辅证完成任务数": execution.get("第一闭环高校辅证完成任务数", "0"),
            "第一闭环字段事实写回可进入任务数": execution.get("第一闭环字段事实写回可进入任务数", "0"),
            "候选记录状态摘要": join_counter(status_counter),
            "候选审阅桶摘要": join_counter(review_counter),
            "候选关系桶摘要": join_counter(relation_counter),
            "页列候选核验动作": "",
            "PDFOCR候选私有工作台_SHA256": candidate_summary.get(
                "private_pdf_ocr_candidate_workbench_sha256", ""
            ),
            "官方公开计划页可定稿": str(official["official_public_plan_page_can_finalize"]).lower(),
            "数智平台可定稿": str(official["zspt_platform_can_finalize"]).lower(),
            "完成条件": "",
            "当前阻断原因": "",
            "字段事实写回状态": "blocked_until_first_closure_private_review_confirms_values",
            "公开安全策略": "公开层只保存页列候选状态桶、计数、证据编号、SHA和门禁；不公开候选明细、学校专业明细、识别正文或私有路径",
            "下一步": "按执行顺序和页列候选核验动作回看PDF原页；再核湖北官方侧；必要时复核高校官网或招生章程；仍不得自动写回字段事实",
        }
        row["页列候选核验动作"] = page_action(row)
        row["完成条件"] = completion_condition(row)
        row["当前阻断原因"] = blocker_reason(row)
        built.append(row)

    built.sort(key=lambda row: as_int(row["执行顺序"]))
    return built


def ensure_public_safe(rows):
    text = "\n".join(",".join(row.get(field, "") for field in PUBLIC_FIELDS) for row in rows)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise RuntimeError(f"第一页列候选看板含禁止公开内容: {hits[:10]}")


def main():
    rows = build_rows()
    ensure_public_safe(rows)
    write_csv(PUBLIC_OUTPUT, rows, PUBLIC_FIELDS)

    summary = {
        "status": "issue19_stable_foundation_first_closure_page_side_candidate_dashboard_not_final",
        "generated_by": "build_issue19_first_closure_page_side_candidate_dashboard.py",
        "source_first_closure_execution_queue": str(FIRST_EXECUTION_QUEUE.relative_to(ROOT)),
        "source_first_closure_pdf_ocr_candidate_public_audit": str(
            FIRST_PDF_OCR_CANDIDATE_AUDIT.relative_to(ROOT)
        ),
        "source_first_closure_pdf_ocr_candidate_summary": str(
            FIRST_PDF_OCR_CANDIDATE_SUMMARY.relative_to(ROOT)
        ),
        "source_private_pdf_ocr_candidate_workbench": "first_closure_pdf_ocr_candidate_private_workbench_not_public",
        "source_official_public_status": str(OFFICIAL_STATUS.relative_to(ROOT)),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": str(PUBLIC_OUTPUT.relative_to(ROOT)),
        "public_row_count": len(rows),
        "unique_page_side_count": len({row["页码版面键"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "total_task_count": sum(as_int(row["页列总任务数"]) for row in rows),
        "pdf_ocr_candidate_task_count": sum(as_int(row["PDFOCR候选任务数"]) for row in rows),
        "no_pdf_ocr_manual_image_task_count": sum(as_int(row["无PDFOCR需看图任务数"]) for row in rows),
        "pdf_school_conflict_task_count": sum(as_int(row["PDFOCR与高校辅证冲突任务数"]) for row in rows),
        "pdf_school_consistent_task_count": sum(as_int(row["PDFOCR与高校辅证一致任务数"]) for row in rows),
        "only_pdf_ocr_candidate_task_count": sum(as_int(row["仅PDFOCR候选任务数"]) for row in rows),
        "school_clue_but_pdf_missing_task_count": sum(
            as_int(row["高校有线索但PDFOCR缺候选任务数"]) for row in rows
        ),
        "no_candidate_manual_image_task_count": sum(as_int(row["无任何候选需看图任务数"]) for row in rows),
        "direct_image_review_required_count": sum(as_int(row["需要人工直接看图任务数"]) for row in rows),
        "double_review_required_count": sum(as_int(row["需要双人复核任务数"]) for row in rows),
        "p0_conflict_task_count": sum(as_int(row["P0候选冲突任务数"]) for row in rows),
        "p1_missing_pdf_ocr_task_count": sum(as_int(row["P1缺PDFOCR人工看图任务数"]) for row in rows),
        "p2_consistent_official_task_count": sum(as_int(row["P2一致仍需官方闭环任务数"]) for row in rows),
        "p3_candidate_confirm_task_count": sum(as_int(row["P3有候选需人工确认任务数"]) for row in rows),
        "pdf_required_count": sum(as_int(row["PDF原页必核任务数"]) for row in rows),
        "hubei_official_required_count": sum(as_int(row["湖北官方侧必核任务数"]) for row in rows),
        "school_support_required_count": sum(as_int(row["高校辅证需复核任务数"]) for row in rows),
        "pdf_completed_count": sum(as_int(row["第一闭环PDF原页完成任务数"]) for row in rows),
        "hubei_official_completed_count": sum(as_int(row["第一闭环湖北官方完成任务数"]) for row in rows),
        "school_support_completed_count": sum(as_int(row["第一闭环高校辅证完成任务数"]) for row in rows),
        "field_writeback_allowed_count": sum(as_int(row["第一闭环字段事实写回可进入任务数"]) for row in rows),
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "field_writeback_gate_count": 0,
        "execution_lane_counts": dict(Counter(row["执行泳道"] for row in rows)),
        "page_side_priority_counts": dict(Counter(row["第一闭环页列优先级"] for row in rows)),
        "page_action_counts": dict(Counter(row["页列候选核验动作"] for row in rows)),
        "first_execution_page_side_keys": [row["页码版面键"] for row in rows[:10]],
        "private_pdf_ocr_candidate_workbench_sha256": rows[0]["PDFOCR候选私有工作台_SHA256"]
        if rows
        else "",
        "public_boundary": "公开表只保存页列候选状态桶、计数、证据编号、SHA和门禁；候选明细只在私有工作台。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {PUBLIC_OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
