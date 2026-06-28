#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FIELD_LEDGER = (
    WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
)
PAGE_CANDIDATE = (
    WORKING / "issue19-stable-foundation-first-closure-page-side-candidate-dashboard.csv"
)
EXECUTION_QUEUE = WORKING / "issue19-stable-foundation-first-closure-execution-queue.csv"
OFFICIAL_STATUS = WORKING / "issue19-official-public-entry-status.json"

OUTPUT = WORKING / "issue19-stable-foundation-first-closure-field-status-dashboard.csv"
SUMMARY_OUTPUT = (
    WORKING / "issue19-stable-foundation-first-closure-field-status-dashboard-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_field_status_dashboard"

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
    "第一闭环字段状态看板ID",
    "来源第一闭环字段确认公开账本",
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
    "稳定基座第一闭环页列包ID",
    "第一闭环页列候选看板ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "专业行ID集合SHA256",
    "院校代码集合SHA256",
    "第一闭环任务ID集合SHA256",
    "字段范围集合",
    "专业计划数字段任务数",
    "学费字段任务数",
    "再选科目字段任务数",
    "待人工判定字段任务数",
    "PDFOCR提示任务数",
    "机器坐标提示任务数",
    "高校辅证线索任务数",
    "PDFOCR与高校辅证冲突任务数",
    "高校有线索但PDFOCR缺候选任务数",
    "仅PDFOCR候选待人工核页任务数",
    "PDFOCR与高校辅证一致仍需官方闭环任务数",
    "无候选需人工看图任务数",
    "机器坐标可辅助核页任务数",
    "需要人工直接看图任务数",
    "需要双人复核任务数",
    "PDF原页待记录任务数",
    "湖北官方侧待记录任务数",
    "高校辅证待记录任务数",
    "高校辅证不适用任务数",
    "三方待确认任务数",
    "字段事实写回可进入任务数",
    "字段事实写回阻断任务数",
    "人工核验泳道摘要",
    "候选提示综合桶摘要",
    "PDFOCR与高校辅证关系桶摘要",
    "字段闭环主阻断",
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
    "OCR行文本",
    "字段确认值",
    "人工读数",
    "候选值",
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


def page_main_blocker(rows):
    conflict = sum(is_true(row.get("是否存在PDFOCR与高校冲突")) for row in rows)
    no_candidate = sum(row.get("候选提示综合桶") == "H4-无候选需人工看图" for row in rows)
    machine = sum(row.get("候选提示综合桶") == "H1-原缺PDFOCR但有机器坐标候选" for row in rows)
    pdf_only = sum(row.get("PDFOCR与高校辅证关系桶") == "R3-仅PDFOCR候选待人工核页" for row in rows)
    consistent = sum(row.get("PDFOCR与高校辅证关系桶") == "R1-PDFOCR与高校辅证存在一致字段" for row in rows)

    if conflict:
        return (
            "B0-PDFOCR与高校辅证冲突",
            "先按私有页列材料核PDF原页；冲突字段必须双人复核，并等待湖北官方侧记录后再判定。",
        )
    if no_candidate:
        return (
            "B1-缺PDFOCR候选需人工看图",
            "先人工看PDF原页补字段读数；再回连湖北官方侧和高校辅证记录。",
        )
    if machine:
        return (
            "B2-机器坐标候选辅助核页",
            "按机器坐标提示定位字段，但仍以PDF原页人工记录和湖北官方侧为准。",
        )
    if pdf_only:
        return (
            "B3-仅PDFOCR候选待人工确认",
            "按PDFOCR提示逐条核原页；确认后再做湖北官方侧和高校侧闭环。",
        )
    if consistent:
        return (
            "B4-候选一致但仍缺官方闭环",
            "PDFOCR与高校辅证已有一致线索，仍需补PDF原页人工记录和湖北官方侧记录。",
        )
    return (
        "B5-待人工判定字段范围",
        "先确认字段归属和专业行边界，再进入PDF原页、湖北官方侧、高校辅证三方闭环。",
    )


def completion_condition(row):
    return (
        "PDF原页人工记录、湖北官方系统或省招办计划记录、高校官网或章程辅证记录"
        "按任务要求补齐；需要双人复核的冲突字段完成二核；三方一致性确认后才允许字段事实写回。"
    )


def build_rows(field_rows, page_rows, execution_rows):
    page_by_key = {row["页码版面键"]: row for row in page_rows}
    execution_by_key = {row["页码版面键"]: row for row in execution_rows}

    grouped = defaultdict(list)
    for row in field_rows:
        grouped[row["页码版面键"]].append(row)

    output = []
    for page_key, rows in grouped.items():
        rows = sorted(rows, key=lambda row: as_int(row.get("第一闭环执行顺序")))
        page = page_by_key.get(page_key, {})
        execution = execution_by_key.get(page_key, {})
        field_counter = Counter()
        for row in rows:
            for field in split_fields(row.get("字段名", "")):
                field_counter[field] += 1

        lane_counter = Counter(row.get("人工核验泳道", "") for row in rows)
        hint_counter = Counter(row.get("候选提示综合桶", "") for row in rows)
        relation_counter = Counter(row.get("PDFOCR与高校辅证关系桶", "") for row in rows)
        blocker, action = page_main_blocker(rows)

        first_row = rows[0]
        output.append(
            {
                "第一闭环字段状态看板ID": stable_id("FIRSTFSTATUS", [page_key]),
                "来源第一闭环字段确认公开账本": str(FIELD_LEDGER.relative_to(ROOT)),
                "来源第一闭环页列候选看板": str(PAGE_CANDIDATE.relative_to(ROOT)),
                "来源第一闭环执行队列": str(EXECUTION_QUEUE.relative_to(ROOT)),
                "来源湖北官方公开入口状态快照": str(OFFICIAL_STATUS.relative_to(ROOT)),
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "数据阶段": DATA_STAGE,
                "主表粒度": "PDF页码×版面列",
                "任务粒度": "页列×第一闭环字段状态压缩",
                **{field: "false" for field in FALSE_FIELDS},
                "执行顺序": execution.get("执行顺序", page.get("执行顺序", "")),
                "执行泳道": first_row.get("执行泳道", ""),
                "第一闭环页列优先级": first_row.get("第一闭环页列优先级", ""),
                "稳定基座第一闭环页列包ID": first_row.get("稳定基座第一闭环页列包ID", ""),
                "第一闭环页列候选看板ID": first_row.get("第一闭环页列候选看板ID", ""),
                "来源页码": first_row.get("来源页码", ""),
                "版面列": first_row.get("版面列", ""),
                "页码版面键": page_key,
                "页列任务数": str(len(rows)),
                "涉及专业行数": str(len({row.get("专业行ID", "") for row in rows if row.get("专业行ID", "")})),
                "涉及院校代码数": str(len({row.get("院校代码", "") for row in rows if row.get("院校代码", "")})),
                "专业行ID集合SHA256": sha_values(row.get("专业行ID", "") for row in rows),
                "院校代码集合SHA256": sha_values(row.get("院校代码", "") for row in rows),
                "第一闭环任务ID集合SHA256": sha_values(
                    row.get("稳定基座第一闭环明细任务ID", "") for row in rows
                ),
                "字段范围集合": "；".join(sorted({row.get("字段名", "") for row in rows if row.get("字段名", "")})),
                "专业计划数字段任务数": str(field_counter.get("专业计划数", 0)),
                "学费字段任务数": str(field_counter.get("学费", 0)),
                "再选科目字段任务数": str(field_counter.get("再选科目", 0)),
                "待人工判定字段任务数": str(field_counter.get("待人工判定字段", 0)),
                "PDFOCR提示任务数": str(sum(is_true(row.get("是否有PDFOCR提示")) for row in rows)),
                "机器坐标提示任务数": str(sum(is_true(row.get("是否有机器坐标提示")) for row in rows)),
                "高校辅证线索任务数": str(sum(is_true(row.get("是否有高校辅证线索")) for row in rows)),
                "PDFOCR与高校辅证冲突任务数": str(
                    sum(is_true(row.get("是否存在PDFOCR与高校冲突")) for row in rows)
                ),
                "高校有线索但PDFOCR缺候选任务数": str(
                    sum(row.get("PDFOCR与高校辅证关系桶") == "R2-高校有线索但PDFOCR缺候选" for row in rows)
                ),
                "仅PDFOCR候选待人工核页任务数": str(
                    sum(row.get("PDFOCR与高校辅证关系桶") == "R3-仅PDFOCR候选待人工核页" for row in rows)
                ),
                "PDFOCR与高校辅证一致仍需官方闭环任务数": str(
                    sum(row.get("PDFOCR与高校辅证关系桶") == "R1-PDFOCR与高校辅证存在一致字段" for row in rows)
                ),
                "无候选需人工看图任务数": str(
                    sum(row.get("候选提示综合桶") == "H4-无候选需人工看图" for row in rows)
                ),
                "机器坐标可辅助核页任务数": str(
                    sum(row.get("候选提示综合桶") == "H1-原缺PDFOCR但有机器坐标候选" for row in rows)
                ),
                "需要人工直接看图任务数": str(
                    sum(is_true(row.get("是否需要人工直接看图")) for row in rows)
                ),
                "需要双人复核任务数": str(sum(is_true(row.get("是否需要双人复核")) for row in rows)),
                "PDF原页待记录任务数": str(
                    sum(row.get("PDF原页私有记录状态") == "pending_private_pdf_reading" for row in rows)
                ),
                "湖北官方侧待记录任务数": str(
                    sum(row.get("湖北官方私有记录状态") == "pending_private_hubei_reading" for row in rows)
                ),
                "高校辅证待记录任务数": str(
                    sum(row.get("高校辅证私有记录状态") == "pending_private_school_reading" for row in rows)
                ),
                "高校辅证不适用任务数": str(
                    sum(row.get("高校辅证私有记录状态") == "not_applicable_no_school_field_clue" for row in rows)
                ),
                "三方待确认任务数": str(
                    sum(
                        row.get("三方字段一致性公开状态")
                        == "pending_private_three_way_field_confirmation"
                        for row in rows
                    )
                ),
                "字段事实写回可进入任务数": "0",
                "字段事实写回阻断任务数": str(
                    sum(
                        row.get("字段事实写回评估状态")
                        == "blocked_until_required_private_readings_complete"
                        for row in rows
                    )
                ),
                "人工核验泳道摘要": counter_summary(lane_counter),
                "候选提示综合桶摘要": counter_summary(hint_counter),
                "PDFOCR与高校辅证关系桶摘要": counter_summary(relation_counter),
                "字段闭环主阻断": blocker,
                "建议下一步动作": action,
                "完成条件": completion_condition(first_row),
                "公开安全策略": "公开层只保存页列级状态、计数、集合SHA和门禁；不保存字段明细、候选明细、院校专业明细、OCR原文或私有路径。",
            }
        )

    return sorted(output, key=lambda row: (row["第一闭环页列优先级"], row["执行泳道"], row["页码版面键"]))


def public_safety_check():
    text = OUTPUT.read_text(encoding="utf-8-sig") + SUMMARY_OUTPUT.read_text(encoding="utf-8")
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise RuntimeError(f"第一闭环字段状态看板含禁止公开内容: {hits[:10]}")


def main():
    field_rows = read_csv(FIELD_LEDGER)
    page_rows = read_csv(PAGE_CANDIDATE)
    execution_rows = read_csv(EXECUTION_QUEUE)

    rows = build_rows(field_rows, page_rows, execution_rows)
    write_csv(OUTPUT, rows, FIELDS)

    field_counter = Counter()
    for row in field_rows:
        for field in split_fields(row.get("字段名", "")):
            field_counter[field] += 1

    summary = {
        "status": "issue19_stable_foundation_first_closure_field_status_dashboard_not_final",
        "generated_by": "build_issue19_first_closure_field_status_dashboard.py",
        "source_first_closure_field_confirmation_public_ledger": str(FIELD_LEDGER.relative_to(ROOT)),
        "source_first_closure_page_side_candidate_dashboard": str(PAGE_CANDIDATE.relative_to(ROOT)),
        "source_first_closure_execution_queue": str(EXECUTION_QUEUE.relative_to(ROOT)),
        "source_official_public_status": str(OFFICIAL_STATUS.relative_to(ROOT)),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": str(OUTPUT.relative_to(ROOT)),
        "row_grain": "PDF页码×版面列×第一闭环字段状态压缩",
        "row_count": len(rows),
        "source_field_task_count": len(field_rows),
        "unique_page_side_count": len({row["页码版面键"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "field_task_counts_split": dict(field_counter),
        "field_scope_counts": dict(Counter(row.get("字段名", "") for row in field_rows)),
        "execution_lane_counts": dict(Counter(row["执行泳道"] for row in rows)),
        "page_priority_counts": dict(Counter(row["第一闭环页列优先级"] for row in rows)),
        "main_blocker_counts": dict(Counter(row["字段闭环主阻断"] for row in rows)),
        "task_main_blocker_counts": {
            blocker: sum(as_int(row["页列任务数"]) for row in rows if row["字段闭环主阻断"] == blocker)
            for blocker in sorted({row["字段闭环主阻断"] for row in rows})
        },
        "pdf_ocr_hint_task_count": sum(as_int(row["PDFOCR提示任务数"]) for row in rows),
        "machine_coordinate_hint_task_count": sum(as_int(row["机器坐标提示任务数"]) for row in rows),
        "school_support_hint_task_count": sum(as_int(row["高校辅证线索任务数"]) for row in rows),
        "pdf_school_conflict_task_count": sum(as_int(row["PDFOCR与高校辅证冲突任务数"]) for row in rows),
        "missing_pdf_with_school_task_count": sum(as_int(row["高校有线索但PDFOCR缺候选任务数"]) for row in rows),
        "pdf_only_candidate_task_count": sum(as_int(row["仅PDFOCR候选待人工核页任务数"]) for row in rows),
        "consistent_but_official_pending_task_count": sum(
            as_int(row["PDFOCR与高校辅证一致仍需官方闭环任务数"]) for row in rows
        ),
        "no_candidate_manual_image_task_count": sum(as_int(row["无候选需人工看图任务数"]) for row in rows),
        "direct_image_review_required_count": sum(as_int(row["需要人工直接看图任务数"]) for row in rows),
        "double_review_required_count": sum(as_int(row["需要双人复核任务数"]) for row in rows),
        "pdf_pending_task_count": sum(as_int(row["PDF原页待记录任务数"]) for row in rows),
        "hubei_official_pending_task_count": sum(as_int(row["湖北官方侧待记录任务数"]) for row in rows),
        "school_support_pending_task_count": sum(as_int(row["高校辅证待记录任务数"]) for row in rows),
        "three_way_pending_task_count": sum(as_int(row["三方待确认任务数"]) for row in rows),
        "field_writeback_ready_count": sum(as_int(row["字段事实写回可进入任务数"]) for row in rows),
        "field_writeback_blocked_task_count": sum(as_int(row["字段事实写回阻断任务数"]) for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "official_plan_replacement_allowed_count": sum(row["是否允许官网证据替代湖北官方计划"] == "true" for row in rows),
        "public_boundary": "公开表只保存页列级字段状态、计数、集合SHA、阻断桶和门禁；不保存字段明细、候选明细、院校专业明细、OCR原文或私有路径。",
        "next_use": "用于把37个页列按字段闭环阻断重新排队，辅助人工核页和高校辅证double check；不得作为字段最终事实或志愿推荐依据。",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public_safety_check()

    print(f"wrote {OUTPUT}")
    print(f"wrote {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
