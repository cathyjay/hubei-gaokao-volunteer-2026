#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIRST_PAGE_SIDE = ROOT / "data/working/issue19-stable-foundation-first-closure-page-side-packet.csv"
FIRST_REVIEW = ROOT / "data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv"
FIRST_TASK_REVIEW = ROOT / "data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv"
FIRST_PREFILL = ROOT / "data/working/issue19-stable-foundation-first-closure-triage-prefill-public-audit.csv"
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

PUBLIC_OUTPUT = ROOT / "data/working/issue19-stable-foundation-first-closure-execution-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-stable-foundation-first-closure-execution-queue-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_execution_queue"

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
    "第一闭环核验执行队列ID",
    "来源第一闭环页列包",
    "来源第一闭环复核公开账本",
    "来源第一闭环任务复核公开账本",
    "来源第一闭环私有预填公开审计",
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
    "执行优先级说明",
    "稳定基座第一闭环页列包ID",
    "稳定基座第一闭环复核公开账本ID",
    "第一闭环私有预填公开审计ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "第一闭环页列优先级",
    "页列总任务数",
    "自动官网辅证任务数",
    "P0人工字段任务数",
    "PDF原页必核任务数",
    "湖北官方侧必核任务数",
    "高校辅证需复核任务数",
    "双人复核任务数",
    "专业计划数字段任务数",
    "再选科目字段任务数",
    "学费字段任务数",
    "高校辅证线索任务数",
    "含高校计划数线索任务数",
    "含高校学费线索任务数",
    "含高校选科线索任务数",
    "公共高校来源文件任务数",
    "公共高校来源文件数",
    "C0冲突任务数",
    "C1官网补缺任务数",
    "C7官网未匹配任务数",
    "EXEC01冲突异常字段数",
    "EXEC02计划数偏大字段数",
    "EXEC03高校辅证字段数",
    "任务级人工动作桶摘要",
    "页列首要核验动作",
    "私有复核页列CSV证据编号",
    "私有复核页列CSV_SHA256",
    "私有复核页列HTML证据编号",
    "私有复核页列HTML_SHA256",
    "私有预填页列CSV证据编号",
    "私有预填页列CSV_SHA256",
    "第一闭环PDF原页完成任务数",
    "第一闭环湖北官方完成任务数",
    "第一闭环高校辅证完成任务数",
    "第一闭环字段事实写回可进入任务数",
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
    "OCR原文",
    "OCR行文本",
    "候选计划数",
    "候选学费",
    "候选选科",
    "PDF原页人工读数",
    "湖北官方字段值",
    "字段确认值",
    "一审记录",
    "二审记录",
    "复核结论",
    "已确认",
    "已核准",
    "最终推荐",
    "可填报",
    "可排序",
]

PRIORITY_RANK = {
    "Q0-冲突页列第一批先核": 0,
    "Q1-补缺或计划数偏大页列先核": 1,
    "Q2-官网未匹配或高校辅证页列先核": 2,
}


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


def join_counter(counter, limit=4):
    items = [(key, value) for key, value in counter.most_common() if key]
    return "；".join(f"{key}:{value}" for key, value in items[:limit])


def execution_lane(page_row, task_rows):
    c0 = as_int(page_row.get("C0冲突任务数"))
    exec01 = as_int(page_row.get("EXEC01冲突异常字段数"))
    exec02 = as_int(page_row.get("EXEC02计划数偏大字段数"))
    c1 = as_int(page_row.get("C1官网补缺任务数"))
    c7 = as_int(page_row.get("C7官网未匹配任务数"))
    exec03 = as_int(page_row.get("EXEC03高校辅证字段数"))
    double_review = sum(row.get("是否需要双人复核") == "true" for row in task_rows)
    if c0 or exec01:
        return "E0-冲突异常双人优先核验"
    if exec02 or c1:
        return "E1-计划数补缺或偏大优先核验"
    if c7:
        return "E2-官网未匹配专业名归属核验"
    if exec03 or double_review:
        return "E3-高校辅证三方核验"
    return "E4-常规页列核验"


def sort_key(row):
    return (
        PRIORITY_RANK.get(row["第一闭环页列优先级"], 99),
        -as_int(row["C0冲突任务数"]),
        -as_int(row["EXEC01冲突异常字段数"]),
        -as_int(row["双人复核任务数"]),
        -as_int(row["C1官网补缺任务数"]),
        -as_int(row["EXEC02计划数偏大字段数"]),
        -as_int(row["页列总任务数"]),
        as_int(row["来源页码"]),
        row["版面列"],
    )


def completion_condition(row):
    return (
        f"PDF原页记录完成={row['PDF原页必核任务数']}；"
        f"湖北官方侧记录完成={row['湖北官方侧必核任务数']}或记录官方系统不可得状态；"
        f"高校辅证记录完成={row['高校辅证需复核任务数']}；"
        f"双人复核完成={row['双人复核任务数']}；"
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
    if as_int(row["双人复核任务数"]):
        blockers.append("双人复核未完成")
    blockers.append("字段事实写回仍阻断")
    return "；".join(blockers)


def build_rows():
    page_rows = read_csv(FIRST_PAGE_SIDE)
    review_rows = read_csv(FIRST_REVIEW)
    task_rows = read_csv(FIRST_TASK_REVIEW)
    prefill_rows = read_csv(FIRST_PREFILL)
    official = load_official_status()

    review_by_key = {page_side_key(row): row for row in review_rows}
    prefill_by_key = {page_side_key(row): row for row in prefill_rows}
    tasks_by_key = defaultdict(list)
    for row in task_rows:
        tasks_by_key[page_side_key(row)].append(row)

    built = []
    for page_row in page_rows:
        key = page_side_key(page_row)
        review = review_by_key.get(key, {})
        prefill = prefill_by_key.get(key, {})
        tasks = tasks_by_key.get(key, [])
        field_counter = Counter(row.get("字段名", "") for row in tasks)
        action_counter = Counter(row.get("人工最小动作", "") for row in tasks)
        lane = execution_lane(page_row, tasks)
        task_count = len(tasks)
        row = {
            "第一闭环核验执行队列ID": stable_id("FIRSTEXEC", [SOURCE_PDF_SHA256, key_text(key)]),
            "来源第一闭环页列包": str(FIRST_PAGE_SIDE.relative_to(ROOT)),
            "来源第一闭环复核公开账本": str(FIRST_REVIEW.relative_to(ROOT)),
            "来源第一闭环任务复核公开账本": str(FIRST_TASK_REVIEW.relative_to(ROOT)),
            "来源第一闭环私有预填公开审计": str(FIRST_PREFILL.relative_to(ROOT)),
            "来源湖北官方公开入口状态快照": str(OFFICIAL_STATUS.relative_to(ROOT)),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×第一闭环核验执行队列",
            **false_gate_values(),
            "执行顺序": "",
            "执行泳道": lane,
            "执行优先级说明": "",
            "稳定基座第一闭环页列包ID": page_row.get("稳定基座第一闭环页列包ID", ""),
            "稳定基座第一闭环复核公开账本ID": review.get("稳定基座第一闭环复核公开账本ID", ""),
            "第一闭环私有预填公开审计ID": prefill.get("第一闭环私有预填公开审计ID", ""),
            "来源页码": page_row.get("来源页码", ""),
            "版面列": page_row.get("版面列", ""),
            "页码版面键": page_row.get("页码版面键", ""),
            "第一闭环页列优先级": page_row.get("第一闭环页列优先级", ""),
            "页列总任务数": str(task_count),
            "自动官网辅证任务数": page_row.get("自动官网辅证任务数", ""),
            "P0人工字段任务数": page_row.get("P0人工字段任务数", ""),
            "PDF原页必核任务数": str(sum(row.get("PDF原页是否必核") == "true" for row in tasks)),
            "湖北官方侧必核任务数": str(sum(row.get("湖北官方侧是否必核") == "true" for row in tasks)),
            "高校辅证需复核任务数": str(sum(row.get("高校辅证是否需要复核") == "true" for row in tasks)),
            "双人复核任务数": str(sum(row.get("是否需要双人复核") == "true" for row in tasks)),
            "专业计划数字段任务数": str(field_counter.get("专业计划数", 0)),
            "再选科目字段任务数": str(field_counter.get("再选科目", 0)),
            "学费字段任务数": str(field_counter.get("学费", 0)),
            "高校辅证线索任务数": prefill.get("高校辅证线索任务数", "0"),
            "含高校计划数线索任务数": prefill.get("含高校计划数线索任务数", "0"),
            "含高校学费线索任务数": prefill.get("含高校学费线索任务数", "0"),
            "含高校选科线索任务数": prefill.get("含高校选科线索任务数", "0"),
            "公共高校来源文件任务数": prefill.get("公共高校来源文件任务数", "0"),
            "公共高校来源文件数": prefill.get("公共高校来源文件数", "0"),
            "C0冲突任务数": page_row.get("C0冲突任务数", ""),
            "C1官网补缺任务数": page_row.get("C1官网补缺任务数", ""),
            "C7官网未匹配任务数": page_row.get("C7官网未匹配任务数", ""),
            "EXEC01冲突异常字段数": page_row.get("EXEC01冲突异常字段数", ""),
            "EXEC02计划数偏大字段数": page_row.get("EXEC02计划数偏大字段数", ""),
            "EXEC03高校辅证字段数": page_row.get("EXEC03高校辅证字段数", ""),
            "任务级人工动作桶摘要": join_counter(action_counter),
            "页列首要核验动作": review.get("页列首要核验动作", page_row.get("人工必做步骤", "")),
            "私有复核页列CSV证据编号": review.get("私有第一闭环页列CSV证据编号", ""),
            "私有复核页列CSV_SHA256": review.get("私有第一闭环页列CSV_SHA256", ""),
            "私有复核页列HTML证据编号": review.get("私有第一闭环页列HTML证据编号", ""),
            "私有复核页列HTML_SHA256": review.get("私有第一闭环页列HTML_SHA256", ""),
            "私有预填页列CSV证据编号": prefill.get("私有预填页列CSV证据编号", ""),
            "私有预填页列CSV_SHA256": prefill.get("私有预填页列CSV_SHA256", ""),
            "第一闭环PDF原页完成任务数": review.get("第一闭环PDF原页完成任务数", "0"),
            "第一闭环湖北官方完成任务数": review.get("第一闭环湖北官方完成任务数", "0"),
            "第一闭环高校辅证完成任务数": review.get("第一闭环高校辅证完成任务数", "0"),
            "第一闭环字段事实写回可进入任务数": review.get("第一闭环字段事实写回可进入任务数", "0"),
            "官方公开计划页可定稿": str(official["official_public_plan_page_can_finalize"]).lower(),
            "数智平台可定稿": str(official["zspt_platform_can_finalize"]).lower(),
            "完成条件": "",
            "当前阻断原因": "",
            "字段事实写回状态": "blocked_until_first_closure_private_review_confirms_values",
            "公开安全策略": "公开层只保存页列执行顺序、任务计数、证据编号、SHA和门禁；不公开候选值、私有记录值、识别正文或私有路径",
            "下一步": "按执行顺序在私有核页材料中完成PDF原页、湖北官方侧、高校辅证和双人复核记录，再同步公开进度",
        }
        row["完成条件"] = completion_condition(row)
        row["当前阻断原因"] = blocker_reason(row)
        built.append(row)

    built.sort(key=sort_key)
    for index, row in enumerate(built, start=1):
        row["执行顺序"] = str(index)
        row["执行优先级说明"] = (
            f"{row['第一闭环页列优先级']}；{row['执行泳道']}；"
            f"任务{row['页列总任务数']}条，双人复核{row['双人复核任务数']}条"
        )
    return built


def ensure_public_safe(rows):
    text = "\n".join(",".join(row.get(field, "") for field in PUBLIC_FIELDS) for row in rows)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise RuntimeError(f"公开执行队列含禁止内容: {hits[:10]}")


def main():
    rows = build_rows()
    ensure_public_safe(rows)
    write_csv(PUBLIC_OUTPUT, rows, PUBLIC_FIELDS)

    lane_counts = Counter(row["执行泳道"] for row in rows)
    priority_counts = Counter(row["第一闭环页列优先级"] for row in rows)
    summary = {
        "status": "issue19_stable_foundation_first_closure_execution_queue_not_final",
        "generated_by": "build_issue19_first_closure_execution_queue.py",
        "source_first_closure_page_side_packet": str(FIRST_PAGE_SIDE.relative_to(ROOT)),
        "source_first_closure_review_public_ledger": str(FIRST_REVIEW.relative_to(ROOT)),
        "source_first_closure_task_review_public_ledger": str(FIRST_TASK_REVIEW.relative_to(ROOT)),
        "source_first_closure_triage_prefill_public_audit": str(FIRST_PREFILL.relative_to(ROOT)),
        "source_official_public_status": str(OFFICIAL_STATUS.relative_to(ROOT)),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": str(PUBLIC_OUTPUT.relative_to(ROOT)),
        "public_row_count": len(rows),
        "unique_page_side_count": len({row["页码版面键"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "total_task_count": sum(as_int(row["页列总任务数"]) for row in rows),
        "auto_task_count": sum(as_int(row["自动官网辅证任务数"]) for row in rows),
        "manual_task_count": sum(as_int(row["P0人工字段任务数"]) for row in rows),
        "pdf_required_count": sum(as_int(row["PDF原页必核任务数"]) for row in rows),
        "hubei_official_required_count": sum(as_int(row["湖北官方侧必核任务数"]) for row in rows),
        "school_support_required_count": sum(as_int(row["高校辅证需复核任务数"]) for row in rows),
        "double_review_required_count": sum(as_int(row["双人复核任务数"]) for row in rows),
        "public_school_source_file_task_count": sum(as_int(row["公共高校来源文件任务数"]) for row in rows),
        "unique_public_school_source_file_count": sum(as_int(row["公共高校来源文件数"]) for row in rows),
        "lane_counts": dict(lane_counts),
        "priority_counts": dict(priority_counts),
        "first_execution_page_side_keys": [row["页码版面键"] for row in rows[:10]],
        "official_public_plan_page_can_finalize": False,
        "zspt_platform_can_finalize": False,
        "pdf_completed_count": sum(as_int(row["第一闭环PDF原页完成任务数"]) for row in rows),
        "hubei_official_completed_count": sum(as_int(row["第一闭环湖北官方完成任务数"]) for row in rows),
        "school_support_completed_count": sum(as_int(row["第一闭环高校辅证完成任务数"]) for row in rows),
        "field_writeback_allowed_count": sum(as_int(row["第一闭环字段事实写回可进入任务数"]) for row in rows),
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "policy": {
            "purpose": "把第一闭环36个页列排成可执行核验顺序，减少人工在多个账本之间跳转。",
            "public_boundary": "公开表只保存页列排序、计数、证据编号、SHA、完成条件和门禁，不保存候选值或私有记录值。",
            "no_finalization": "执行队列不确认字段事实，不自动写回，不生成学校专业建议。",
        },
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {PUBLIC_OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
