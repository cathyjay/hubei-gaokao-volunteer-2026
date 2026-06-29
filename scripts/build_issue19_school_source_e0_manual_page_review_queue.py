#!/usr/bin/env python3
"""Build a public E0 manual page-review queue from school-source gaps.

The output is an execution queue only. It keeps the school-source E0 tasks
linked to first-closure page-review hints by school code, without emitting
school names, major names, URLs, OCR text, field readings, or private paths.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

GAP_PRIORITY = WORKING / "issue19-school-source-gap-priority-public-ledger.csv"
FIRST_CLOSURE_NEXT_ACTION = WORKING / "issue19-stable-foundation-first-closure-next-action-matrix.csv"

OUTPUT = WORKING / "issue19-school-source-e0-manual-page-review-queue-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-e0-manual-page-review-queue-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_e0_manual_page_review_queue"
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

FIELDS = [
    "高校源E0人工回页队列ID",
    "来源高校源缺口优先级清单",
    "来源第一闭环下一步动作矩阵",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "人工回页队列序号",
    "高校源缺口优先级ID",
    "高校源最新对齐ID",
    "高校官网辅证状态快照ID",
    "高校官网辅证自动执行批次ID",
    "院校代码",
    "任务学校键SHA16",
    "缺口主类",
    "缺口子类",
    "原自动执行泳道",
    "人工回页风险桶",
    "人工回页优先级分",
    "最小人工动作",
    "完成条件",
    "涉及招生明细数",
    "涉及专业组数",
    "C4C6计划数冲突候选数",
    "C4C6官网可补OCR计划数候选数",
    "同校第一闭环页列提示状态",
    "同校第一闭环任务数",
    "同校第一闭环页列数",
    "同校第一闭环PDF页数",
    "同校N0冲突双人核页任务数",
    "同校N1高校补缺回页任务数",
    "同校N2机器坐标辅助核页任务数",
    "同校N3人工看图任务数",
    "同校N4PDFOCR确认任务数",
    "同校N5待湖北官方侧任务数",
    "同校E0冲突异常页列任务数",
    "同校E1计划数补缺页列任务数",
    "同校E2专业名归属页列任务数",
    "同校自动官网辅证任务数",
    "同校P0人工字段任务数",
    "同校专业计划数字段任务数",
    "同校学费字段任务数",
    "同校再选科目字段任务数",
    "同校需要双人复核任务数",
    "同校需要人工直接看图任务数",
    "同校PDFOCR与高校冲突任务数",
    "同校高校辅证线索任务数",
    "同校第一闭环任务集合SHA16",
    "同校页列集合SHA16",
    "同校核验动作层级分布",
    "同校执行泳道分布",
    "队列使用边界",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
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
    "院校名称",
    "专业名称",
    "专业代号",
    "院校专业组",
    "OCR行文本",
    "OCR原文",
    "字段确认值",
    "人工读数",
    "候选值",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "复核备注",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def to_int(value: str | int | None) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def stable_id(prefix: str, parts: list[str]) -> str:
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def sha16(parts: list[str]) -> str:
    text = "|".join(str(part or "").strip() for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def counter_text(counter: Counter[str]) -> str:
    if not counter:
        return ""
    return "；".join(f"{key}={counter[key]}" for key in sorted(counter))


def risk_bucket(row: dict[str, str]) -> tuple[str, int]:
    category = row.get("缺口主类", "")
    if category.startswith("G0-"):
        return "M0-计划数冲突或高校侧差异先核", 300
    if category.startswith("G1-"):
        return "M1-OCR补缺线索先核", 200
    if category.startswith("G2-"):
        return "M2-专业名归属或匹配规则先核", 100
    return "M9-其他人工回页任务", 0


def count_contains(rows: list[dict[str, str]], field: str, needle: str) -> int:
    return sum(1 for row in rows if needle in row.get(field, ""))


def build_queue_rows(
    gap_rows: list[dict[str, str]],
    next_action_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    by_school: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in next_action_rows:
        by_school[row.get("院校代码", "")].append(row)

    e0_rows = [row for row in gap_rows if row.get("执行优先级") == "E0-人工先核回页"]

    output_rows: list[dict[str, str]] = []
    for index, gap in enumerate(e0_rows, start=1):
        school_rows = by_school.get(gap.get("院校代码", ""), [])
        action_counter = Counter(row.get("核验动作层级", "") for row in school_rows if row.get("核验动作层级"))
        lane_counter = Counter(row.get("执行泳道", "") for row in school_rows if row.get("执行泳道"))
        task_ids = [row.get("第一闭环下一步动作ID", "") for row in school_rows]
        page_side_keys = [row.get("页码版面键", "") for row in school_rows]
        risk, risk_score = risk_bucket(gap)
        linked_status = "H1-有同校第一闭环页列提示" if school_rows else "H0-暂无同校第一闭环页列提示"

        row = {
            "高校源E0人工回页队列ID": stable_id(
                "SCHOOLSRCMANUAL",
                [
                    gap.get("高校源缺口优先级ID", ""),
                    gap.get("高校源最新对齐ID", ""),
                    gap.get("院校代码", ""),
                ],
            ),
            "来源高校源缺口优先级清单": source_path(GAP_PRIORITY),
            "来源第一闭环下一步动作矩阵": source_path(FIRST_CLOSURE_NEXT_ACTION),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校侧E0人工回页任务",
            "任务粒度": "公开任务级队列；不保存学校文本、专业文本、页图、OCR正文或字段读数",
            "人工回页队列序号": str(index),
            "高校源缺口优先级ID": gap.get("高校源缺口优先级ID", ""),
            "高校源最新对齐ID": gap.get("高校源最新对齐ID", ""),
            "高校官网辅证状态快照ID": gap.get("高校官网辅证状态快照ID", ""),
            "高校官网辅证自动执行批次ID": gap.get("高校官网辅证自动执行批次ID", ""),
            "院校代码": gap.get("院校代码", ""),
            "任务学校键SHA16": gap.get("任务学校键SHA16", ""),
            "缺口主类": gap.get("缺口主类", ""),
            "缺口子类": gap.get("缺口子类", ""),
            "原自动执行泳道": gap.get("原自动执行泳道", ""),
            "人工回页风险桶": risk,
            "人工回页优先级分": str(to_int(gap.get("执行优先级分")) + risk_score),
            "最小人工动作": gap.get("最小人工动作", ""),
            "完成条件": gap.get("完成条件", ""),
            "涉及招生明细数": gap.get("涉及招生明细数", "0"),
            "涉及专业组数": gap.get("涉及专业组数", "0"),
            "C4C6计划数冲突候选数": gap.get("C4C6计划数冲突候选数", "0"),
            "C4C6官网可补OCR计划数候选数": gap.get("C4C6官网可补OCR计划数候选数", "0"),
            "同校第一闭环页列提示状态": linked_status,
            "同校第一闭环任务数": str(len(school_rows)),
            "同校第一闭环页列数": str(len({row.get("页码版面键", "") for row in school_rows})),
            "同校第一闭环PDF页数": str(len({row.get("来源页码", "") for row in school_rows})),
            "同校N0冲突双人核页任务数": str(action_counter.get("N0-先双人核PDF原页冲突", 0)),
            "同校N1高校补缺回页任务数": str(action_counter.get("N1-高校补缺线索回PDF原页", 0)),
            "同校N2机器坐标辅助核页任务数": str(action_counter.get("N2-机器坐标辅助核PDF原页", 0)),
            "同校N3人工看图任务数": str(action_counter.get("N3-无稳定候选人工看图", 0)),
            "同校N4PDFOCR确认任务数": str(action_counter.get("N4-PDFOCR候选人工确认", 0)),
            "同校N5待湖北官方侧任务数": str(action_counter.get("N5-多源一致仍待湖北官方侧", 0)),
            "同校E0冲突异常页列任务数": str(lane_counter.get("E0-冲突异常双人优先核验", 0)),
            "同校E1计划数补缺页列任务数": str(lane_counter.get("E1-计划数补缺或偏大优先核验", 0)),
            "同校E2专业名归属页列任务数": str(lane_counter.get("E2-官网未匹配专业名归属核验", 0)),
            "同校自动官网辅证任务数": str(count_contains(school_rows, "任务来源类型", "自动官网辅证任务")),
            "同校P0人工字段任务数": str(count_contains(school_rows, "任务来源类型", "P0人工字段任务")),
            "同校专业计划数字段任务数": str(count_contains(school_rows, "字段名", "专业计划数")),
            "同校学费字段任务数": str(count_contains(school_rows, "字段名", "学费")),
            "同校再选科目字段任务数": str(count_contains(school_rows, "字段名", "再选科目")),
            "同校需要双人复核任务数": str(sum(1 for row in school_rows if row.get("是否需要双人复核") == "true")),
            "同校需要人工直接看图任务数": str(sum(1 for row in school_rows if row.get("是否需要人工直接看图") == "true")),
            "同校PDFOCR与高校冲突任务数": str(sum(1 for row in school_rows if row.get("是否存在PDFOCR与高校冲突") == "true")),
            "同校高校辅证线索任务数": str(sum(1 for row in school_rows if row.get("是否有高校辅证线索") == "true")),
            "同校第一闭环任务集合SHA16": sha16(sorted(task_ids)),
            "同校页列集合SHA16": sha16(sorted(page_side_keys)),
            "同校核验动作层级分布": counter_text(action_counter),
            "同校执行泳道分布": counter_text(lane_counter),
            "队列使用边界": "该队列只把E0任务接到同校页列提示；不能据此确认计划数、学费、选科、专业归属或专业组边界。",
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "公开安全策略": "公开层只保存任务ID、院校代码、状态桶、计数和SHA；不保存学校文本、专业文本、页图、OCR正文、字段读数、URL、截图或私有路径。",
        }
        for field in FALSE_FIELDS:
            row[field] = bool_text(False)
        output_rows.append(row)

    output_rows.sort(
        key=lambda row: (
            -to_int(row.get("人工回页优先级分")),
            to_int(row.get("人工回页队列序号")),
            row.get("高校源缺口优先级ID", ""),
        )
    )
    for index, row in enumerate(output_rows, start=1):
        row["人工回页队列序号"] = str(index)
    return output_rows


def validate_public_safety(path: Path, summary_path: Path) -> None:
    for check_path in [path, summary_path]:
        text = check_path.read_text(encoding="utf-8-sig")
        hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
        if hits:
            raise SystemExit(f"公开输出包含禁止内容 {hits}: {check_path}")


def main() -> None:
    gap_rows = read_csv(GAP_PRIORITY)
    next_action_rows = read_csv(FIRST_CLOSURE_NEXT_ACTION)
    output_rows = build_queue_rows(gap_rows, next_action_rows)

    school_codes = {row.get("院校代码", "") for row in output_rows}
    linked_rows_by_school = [
        row for row in next_action_rows if row.get("院校代码", "") in school_codes
    ]

    write_csv(OUTPUT, output_rows)
    summary = {
        "status": "issue19_school_source_e0_manual_page_review_queue_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_gap_priority": source_path(GAP_PRIORITY),
        "source_first_closure_next_action_matrix": source_path(FIRST_CLOSURE_NEXT_ACTION),
        "output_table": source_path(OUTPUT),
        "generated_at": GENERATED_AT,
        "row_count": len(output_rows),
        "unique_school_code_count": len(school_codes),
        "risk_bucket_counts": dict(Counter(row.get("人工回页风险桶", "") for row in output_rows)),
        "gap_category_counts": dict(Counter(row.get("缺口主类", "") for row in output_rows)),
        "gap_subcategory_counts": dict(Counter(row.get("缺口子类", "") for row in output_rows)),
        "linked_hint_status_counts": dict(Counter(row.get("同校第一闭环页列提示状态", "") for row in output_rows)),
        "linked_unique_first_closure_task_count": len({row.get("第一闭环下一步动作ID", "") for row in linked_rows_by_school}),
        "linked_unique_school_count": len({row.get("院校代码", "") for row in linked_rows_by_school}),
        "linked_unique_pdf_page_count": len({row.get("来源页码", "") for row in linked_rows_by_school}),
        "linked_unique_page_side_count": len({row.get("页码版面键", "") for row in linked_rows_by_school}),
        "linked_action_level_counts": dict(Counter(row.get("核验动作层级", "") for row in linked_rows_by_school)),
        "linked_execution_lane_counts": dict(Counter(row.get("执行泳道", "") for row in linked_rows_by_school)),
        "linked_source_type_counts": dict(Counter(row.get("任务来源类型", "") for row in linked_rows_by_school)),
        "linked_double_review_task_count": sum(1 for row in linked_rows_by_school if row.get("是否需要双人复核") == "true"),
        "linked_direct_image_review_task_count": sum(1 for row in linked_rows_by_school if row.get("是否需要人工直接看图") == "true"),
        "linked_pdfocr_school_conflict_task_count": sum(1 for row in linked_rows_by_school if row.get("是否存在PDFOCR与高校冲突") == "true"),
        "linked_school_source_hint_task_count": sum(1 for row in linked_rows_by_school if row.get("是否有高校辅证线索") == "true"),
        "pdf_page_review_required_count": len(output_rows),
        "hubei_official_review_required_count": len(output_rows),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该队列只安排E0人工回页顺序和同校页列提示，不确认字段事实，不替代第19期PDF原页或湖北官方系统，不进入志愿推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    validate_public_safety(OUTPUT, SUMMARY_OUTPUT)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
