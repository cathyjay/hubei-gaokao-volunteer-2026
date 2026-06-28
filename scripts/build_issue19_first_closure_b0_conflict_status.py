#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FIELD_STATUS = (
    WORKING / "issue19-stable-foundation-first-closure-field-status-dashboard.csv"
)
FIELD_LEDGER = (
    WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
)
TASK_LEDGER = (
    WORKING / "issue19-stable-foundation-first-closure-task-review-public-ledger.csv"
)
PAGE_CANDIDATE = (
    WORKING / "issue19-stable-foundation-first-closure-page-side-candidate-dashboard.csv"
)
EXECUTION_QUEUE = WORKING / "issue19-stable-foundation-first-closure-execution-queue.csv"
PLAN_CONFLICT_REVIEW = WORKING / "issue19-b0-b1-plan-conflict-review-queue.csv"
OFFICIAL_STATUS = WORKING / "issue19-official-public-entry-status.json"

OUTPUT = WORKING / "issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv"
SUMMARY_OUTPUT = (
    WORKING
    / "issue19-stable-foundation-first-closure-b0-conflict-status-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_b0_conflict_status_public_ledger"
B0_BLOCKER = "B0-PDFOCR与高校辅证冲突"

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
    "B0冲突页列核验状态ID",
    "来源第一闭环字段状态看板",
    "来源第一闭环字段确认公开账本",
    "来源第一闭环任务复核公开账本",
    "来源第一闭环页列候选看板",
    "来源第一闭环执行队列",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行顺序",
    "执行泳道",
    "第一闭环页列优先级",
    "字段状态看板ID",
    "第一闭环页列候选看板ID",
    "第一闭环核验执行队列ID",
    "稳定基座第一闭环页列包ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列任务数",
    "B0页列冲突任务数",
    "同页非冲突待闭环任务数",
    "同页B0B1计划数冲突专项记录数",
    "同页疑似学费错位专项记录数",
    "同页计划数不一致专项记录数",
    "涉及专业行数",
    "冲突涉及专业行数",
    "专业行ID集合SHA256",
    "冲突专业行ID集合SHA256",
    "第一闭环任务ID集合SHA256",
    "B0冲突任务ID集合SHA256",
    "涉及字段范围集合",
    "B0冲突字段范围集合",
    "B0冲突专业计划数字段数",
    "B0冲突学费字段数",
    "B0冲突再选科目字段数",
    "B0冲突字段组合摘要",
    "PDFOCR提示任务数",
    "机器坐标提示任务数",
    "高校辅证线索任务数",
    "PDFOCR与高校辅证冲突任务数",
    "PDFOCR与高校辅证一致仍需官方闭环任务数",
    "高校有线索但PDFOCR缺候选任务数",
    "仅PDFOCR候选待人工核页任务数",
    "无候选需人工看图任务数",
    "需要人工直接看图任务数",
    "需要双人复核任务数",
    "PDF原页待记录任务数",
    "湖北官方侧待记录任务数",
    "高校辅证待记录任务数",
    "三方待确认任务数",
    "字段事实写回可进入任务数",
    "字段事实写回阻断任务数",
    "任务级人工动作桶摘要",
    "候选关系桶摘要",
    "私有复核页列CSV证据编号",
    "私有复核页列CSV_SHA256",
    "私有复核页列HTML证据编号",
    "私有复核页列HTML_SHA256",
    "B0冲突闭环状态",
    "B0冲突优先级判定",
    "建议下一步动作",
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
    "院校专业组",
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


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_int(value):
    try:
        return int(str(value).strip() or "0")
    except ValueError:
        return 0


def is_true(value):
    return str(value).strip().lower() == "true"


def stable_id(prefix, parts):
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def sha_values(values):
    cleaned = sorted({str(value).strip() for value in values if str(value).strip()})
    if not cleaned:
        return ""
    return hashlib.sha256("\n".join(cleaned).encode("utf-8")).hexdigest()


def split_fields(value):
    normalized = str(value).replace("；", ";")
    return [part.strip() for part in normalized.split(";") if part.strip()]


def counter_summary(counter):
    return "；".join(f"{key}={value}" for key, value in sorted(counter.items()) if key)


def field_range(rows):
    fields = []
    for row in rows:
        fields.extend(split_fields(row.get("字段名", "")))
    return "；".join(sorted(set(fields)))


def source_path(path):
    return str(path.relative_to(ROOT))


def b0_priority(row):
    conflict_count = as_int(row.get("B0页列冲突任务数"))
    double_count = as_int(row.get("需要双人复核任务数"))
    direct_count = as_int(row.get("需要人工直接看图任务数"))
    total_count = as_int(row.get("页列任务数"))
    if conflict_count >= 10:
        return "P0-整页列高冲突，先双人核PDF原页与湖北官方侧"
    if conflict_count >= 2 or double_count >= 4:
        return "P1-多字段冲突或双人复核较多，优先核PDF原页"
    if total_count >= 20 or direct_count >= 7:
        return "P2-同页任务密集，按页列集中核验"
    return "P3-单点冲突，随同页列材料完成核验"


def next_action(row):
    priority = row["B0冲突优先级判定"]
    if priority.startswith("P0"):
        return (
            "先按私有页列材料逐项核PDF原页，再补湖北官方侧记录；"
            "B0冲突字段必须双人复核，高校官网只作提示，不可替代湖北官方计划。"
        )
    if priority.startswith("P1"):
        return (
            "优先核冲突字段所在行的PDF原页和湖北官方侧；"
            "若高校辅证与PDF原页不一致，升级双人复核并保留差异。"
        )
    if priority.startswith("P2"):
        return (
            "按页列集中处理，同步清理同页非冲突待闭环任务；"
            "先完成PDF原页记录，再补湖北官方侧和高校辅证记录。"
        )
    return (
        "作为同页列补充核验项处理；仍需PDF原页、湖北官方侧和高校辅证三方记录后再写回。"
    )


def completion_condition():
    return (
        "B0冲突字段完成PDF原页人工记录、湖北官方系统或省招办计划记录、高校官网或章程辅证记录；"
        "双人复核完成并记录三方一致性后，才允许进入字段事实写回评估。"
    )


def build_rows(status_rows, field_rows, task_rows, candidate_rows, execution_rows):
    status_by_key = {row["页码版面键"]: row for row in status_rows}
    candidate_by_key = {row["页码版面键"]: row for row in candidate_rows}
    execution_by_key = {row["页码版面键"]: row for row in execution_rows}
    task_by_key = defaultdict(list)
    for row in task_rows:
        task_by_key[row.get("页码版面键", "")].append(row)

    plan_conflict_rows = read_csv(PLAN_CONFLICT_REVIEW)
    plan_conflict_by_page = defaultdict(list)
    for row in plan_conflict_rows:
        plan_conflict_by_page[row.get("来源页码", "")].append(row)

    field_by_key = defaultdict(list)
    for row in field_rows:
        field_by_key[row.get("页码版面键", "")].append(row)

    output = []
    b0_status_rows = [
        row for row in status_rows if row.get("字段闭环主阻断") == B0_BLOCKER
    ]
    b0_status_rows.sort(key=lambda row: as_int(row.get("执行顺序")))

    for status in b0_status_rows:
        page_key = status["页码版面键"]
        rows = field_by_key[page_key]
        conflict_rows = [row for row in rows if is_true(row.get("是否存在PDFOCR与高校冲突"))]
        tasks = task_by_key.get(page_key, [])
        task_action_counter = Counter(row.get("人工核验动作", "") for row in rows)
        relation_counter = Counter(row.get("PDFOCR与高校辅证关系桶", "") for row in rows)
        conflict_field_counter = Counter()
        conflict_combo_counter = Counter(row.get("字段名", "") for row in conflict_rows)
        for row in conflict_rows:
            for field in split_fields(row.get("字段名", "")):
                conflict_field_counter[field] += 1

        candidate = candidate_by_key.get(page_key, {})
        execution = execution_by_key.get(page_key, {})
        same_page_plan_conflicts = plan_conflict_by_page.get(status.get("来源页码", ""), [])
        source_task_ids = [row.get("稳定基座第一闭环明细任务ID", "") for row in rows]
        conflict_task_ids = [
            row.get("稳定基座第一闭环明细任务ID", "") for row in conflict_rows
        ]
        output_row = {
            "B0冲突页列核验状态ID": stable_id("FIRSTB0STATUS", [page_key]),
            "来源第一闭环字段状态看板": source_path(FIELD_STATUS),
            "来源第一闭环字段确认公开账本": source_path(FIELD_LEDGER),
            "来源第一闭环任务复核公开账本": source_path(TASK_LEDGER),
            "来源第一闭环页列候选看板": source_path(PAGE_CANDIDATE),
            "来源第一闭环执行队列": source_path(EXECUTION_QUEUE),
            "来源湖北官方公开入口状态快照": source_path(OFFICIAL_STATUS),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "B0冲突页列×公开核验状态压缩",
            **{field: "false" for field in FALSE_FIELDS},
            "执行顺序": status.get("执行顺序", ""),
            "执行泳道": status.get("执行泳道", ""),
            "第一闭环页列优先级": status.get("第一闭环页列优先级", ""),
            "字段状态看板ID": status.get("第一闭环字段状态看板ID", ""),
            "第一闭环页列候选看板ID": candidate.get("第一闭环页列候选看板ID", ""),
            "第一闭环核验执行队列ID": execution.get("第一闭环核验执行队列ID", ""),
            "稳定基座第一闭环页列包ID": status.get("稳定基座第一闭环页列包ID", ""),
            "来源页码": status.get("来源页码", ""),
            "版面列": status.get("版面列", ""),
            "页码版面键": page_key,
            "页列任务数": str(len(rows)),
            "B0页列冲突任务数": str(len(conflict_rows)),
            "同页非冲突待闭环任务数": str(len(rows) - len(conflict_rows)),
            "同页B0B1计划数冲突专项记录数": str(len(same_page_plan_conflicts)),
            "同页疑似学费错位专项记录数": str(
                sum(
                    row.get("冲突类型") == "OCR计划数疑似误取学费"
                    for row in same_page_plan_conflicts
                )
            ),
            "同页计划数不一致专项记录数": str(
                sum(
                    row.get("冲突类型") == "OCR计划数与官网计划数不一致"
                    for row in same_page_plan_conflicts
                )
            ),
            "涉及专业行数": str(
                len({row.get("专业行ID", "") for row in rows if row.get("专业行ID", "")})
            ),
            "冲突涉及专业行数": str(
                len(
                    {
                        row.get("专业行ID", "")
                        for row in conflict_rows
                        if row.get("专业行ID", "")
                    }
                )
            ),
            "专业行ID集合SHA256": sha_values(row.get("专业行ID", "") for row in rows),
            "冲突专业行ID集合SHA256": sha_values(
                row.get("专业行ID", "") for row in conflict_rows
            ),
            "第一闭环任务ID集合SHA256": sha_values(source_task_ids),
            "B0冲突任务ID集合SHA256": sha_values(conflict_task_ids),
            "涉及字段范围集合": field_range(rows),
            "B0冲突字段范围集合": field_range(conflict_rows),
            "B0冲突专业计划数字段数": str(conflict_field_counter["专业计划数"]),
            "B0冲突学费字段数": str(conflict_field_counter["学费"]),
            "B0冲突再选科目字段数": str(conflict_field_counter["再选科目"]),
            "B0冲突字段组合摘要": counter_summary(conflict_combo_counter),
            "PDFOCR提示任务数": status.get("PDFOCR提示任务数", "0"),
            "机器坐标提示任务数": status.get("机器坐标提示任务数", "0"),
            "高校辅证线索任务数": status.get("高校辅证线索任务数", "0"),
            "PDFOCR与高校辅证冲突任务数": status.get("PDFOCR与高校辅证冲突任务数", "0"),
            "PDFOCR与高校辅证一致仍需官方闭环任务数": status.get(
                "PDFOCR与高校辅证一致仍需官方闭环任务数", "0"
            ),
            "高校有线索但PDFOCR缺候选任务数": status.get(
                "高校有线索但PDFOCR缺候选任务数", "0"
            ),
            "仅PDFOCR候选待人工核页任务数": status.get("仅PDFOCR候选待人工核页任务数", "0"),
            "无候选需人工看图任务数": status.get("无候选需人工看图任务数", "0"),
            "需要人工直接看图任务数": status.get("需要人工直接看图任务数", "0"),
            "需要双人复核任务数": status.get("需要双人复核任务数", "0"),
            "PDF原页待记录任务数": status.get("PDF原页待记录任务数", "0"),
            "湖北官方侧待记录任务数": status.get("湖北官方侧待记录任务数", "0"),
            "高校辅证待记录任务数": status.get("高校辅证待记录任务数", "0"),
            "三方待确认任务数": status.get("三方待确认任务数", "0"),
            "字段事实写回可进入任务数": status.get("字段事实写回可进入任务数", "0"),
            "字段事实写回阻断任务数": status.get("字段事实写回阻断任务数", "0"),
            "任务级人工动作桶摘要": counter_summary(task_action_counter),
            "候选关系桶摘要": counter_summary(relation_counter),
            "私有复核页列CSV证据编号": execution.get("私有复核页列CSV证据编号", ""),
            "私有复核页列CSV_SHA256": execution.get("私有复核页列CSV_SHA256", ""),
            "私有复核页列HTML证据编号": execution.get("私有复核页列HTML证据编号", ""),
            "私有复核页列HTML_SHA256": execution.get("私有复核页列HTML_SHA256", ""),
            "B0冲突闭环状态": "R0-B0冲突未闭环，字段事实不得写回",
            "B0冲突优先级判定": "",
            "建议下一步动作": "",
            "完成条件": completion_condition(),
            "公开安全策略": (
                "公开层只保存页列级计数、字段类型、证据编号、集合SHA、状态桶和门禁；"
                "不保存学校专业明细、字段备选内容、OCR原文、人工核验内容、私有路径或登录信息。"
            ),
        }
        output_row["B0冲突优先级判定"] = b0_priority(output_row)
        output_row["建议下一步动作"] = next_action(output_row)
        output.append(output_row)

    return output


def validate_public_safety(rows, summary):
    text = json.dumps(summary, ensure_ascii=False) + "\n"
    text += "\n".join(",".join(str(row.get(field, "")) for field in FIELDS) for row in rows)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise ValueError(f"public output contains forbidden tokens: {hits}")


def build_summary(rows):
    row_counter = Counter(row["B0冲突优先级判定"] for row in rows)
    lane_counter = Counter(row["执行泳道"] for row in rows)
    page_priority_counter = Counter(row["第一闭环页列优先级"] for row in rows)

    summary = {
        "status": f"{DATA_STAGE}_not_final",
        "generated_by": Path(__file__).name,
        "source_first_closure_field_status_dashboard": source_path(FIELD_STATUS),
        "source_first_closure_field_confirmation_public_ledger": source_path(FIELD_LEDGER),
        "source_first_closure_task_review_public_ledger": source_path(TASK_LEDGER),
        "source_first_closure_page_side_candidate_dashboard": source_path(PAGE_CANDIDATE),
        "source_first_closure_execution_queue": source_path(EXECUTION_QUEUE),
        "source_official_public_status": source_path(OFFICIAL_STATUS),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": source_path(OUTPUT),
        "row_grain": "PDF页码×版面列×B0冲突公开核验状态压缩",
        "row_count": len(rows),
        "b0_page_side_count": len(rows),
        "b0_unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "b0_page_side_task_count": sum(as_int(row["页列任务数"]) for row in rows),
        "b0_conflict_task_count": sum(as_int(row["B0页列冲突任务数"]) for row in rows),
        "b0_non_conflict_pending_same_page_task_count": sum(
            as_int(row["同页非冲突待闭环任务数"]) for row in rows
        ),
        "b0_b1_plan_conflict_review_row_count": sum(
            as_int(row["同页B0B1计划数冲突专项记录数"]) for row in rows
        ),
        "same_page_suspected_fee_as_plan_count": sum(
            as_int(row["同页疑似学费错位专项记录数"]) for row in rows
        ),
        "same_page_plan_mismatch_count": sum(
            as_int(row["同页计划数不一致专项记录数"]) for row in rows
        ),
        "global_plan_conflict_review_row_count": len(read_csv(PLAN_CONFLICT_REVIEW)),
        "global_suspected_fee_as_plan_count": sum(
            row.get("冲突类型") == "OCR计划数疑似误取学费"
            for row in read_csv(PLAN_CONFLICT_REVIEW)
        ),
        "global_plan_mismatch_count": sum(
            row.get("冲突类型") == "OCR计划数与官网计划数不一致"
            for row in read_csv(PLAN_CONFLICT_REVIEW)
        ),
        "b0_conflict_plan_field_count": sum(
            as_int(row["B0冲突专业计划数字段数"]) for row in rows
        ),
        "b0_conflict_tuition_field_count": sum(as_int(row["B0冲突学费字段数"]) for row in rows),
        "b0_conflict_subject_field_count": sum(
            as_int(row["B0冲突再选科目字段数"]) for row in rows
        ),
        "pdf_ocr_hint_task_count": sum(as_int(row["PDFOCR提示任务数"]) for row in rows),
        "machine_coordinate_hint_task_count": sum(
            as_int(row["机器坐标提示任务数"]) for row in rows
        ),
        "school_support_hint_task_count": sum(as_int(row["高校辅证线索任务数"]) for row in rows),
        "pdf_school_conflict_task_count": sum(
            as_int(row["PDFOCR与高校辅证冲突任务数"]) for row in rows
        ),
        "direct_image_review_required_count": sum(
            as_int(row["需要人工直接看图任务数"]) for row in rows
        ),
        "double_review_required_count": sum(as_int(row["需要双人复核任务数"]) for row in rows),
        "pdf_pending_task_count": sum(as_int(row["PDF原页待记录任务数"]) for row in rows),
        "hubei_official_pending_task_count": sum(
            as_int(row["湖北官方侧待记录任务数"]) for row in rows
        ),
        "school_support_pending_task_count": sum(
            as_int(row["高校辅证待记录任务数"]) for row in rows
        ),
        "three_way_pending_task_count": sum(as_int(row["三方待确认任务数"]) for row in rows),
        "field_writeback_ready_count": sum(
            as_int(row["字段事实写回可进入任务数"]) for row in rows
        ),
        "field_writeback_blocked_task_count": sum(
            as_int(row["字段事实写回阻断任务数"]) for row in rows
        ),
        "b0_priority_counts": dict(sorted(row_counter.items())),
        "execution_lane_counts": dict(sorted(lane_counter.items())),
        "page_priority_counts": dict(sorted(page_priority_counter.items())),
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "public_boundary": (
            "公开表只保存B0冲突页列级计数、字段类型、状态桶、证据编号和集合SHA；"
            "不保存学校专业明细、字段备选内容、OCR原文、人工核验内容、私有路径或登录态。"
        ),
        "next_use": (
            "用于把B0冲突页列优先派发到PDF原页、湖北官方侧、高校辅证和双人复核；"
            "不得作为字段最终事实、学校专业建议或志愿推荐依据。"
        ),
    }
    return summary


def main():
    status_rows = read_csv(FIELD_STATUS)
    field_rows = read_csv(FIELD_LEDGER)
    task_rows = read_csv(TASK_LEDGER)
    candidate_rows = read_csv(PAGE_CANDIDATE)
    execution_rows = read_csv(EXECUTION_QUEUE)

    rows = build_rows(status_rows, field_rows, task_rows, candidate_rows, execution_rows)
    summary = build_summary(rows)
    validate_public_safety(rows, summary)
    write_csv(OUTPUT, rows, FIELDS)
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
