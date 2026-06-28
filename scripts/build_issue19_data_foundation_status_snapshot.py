#!/usr/bin/env python3
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"
EXPORTS = ROOT / "data/exports"

OUT_JSON = WORKING / "issue19-data-foundation-status-snapshot.json"
OUT_CSV = WORKING / "issue19-data-foundation-status-snapshot.csv"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"


def read_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def csv_count(path):
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        return sum(1 for _ in reader)


def count_values(rows, field):
    return dict(Counter(row.get(field, "") for row in rows))


def metric_rows(snapshot):
    rows = []

    def add(section, metric, value, source, note=""):
        rows.append(
            {
                "板块": section,
                "指标": metric,
                "当前值": value,
                "来源": source,
                "说明": note,
            }
        )

    foundation = snapshot["foundation"]
    add("全量结构化", "院校数", foundation["school_count"], foundation["source"])
    add("全量结构化", "院校专业组数", foundation["group_count"], foundation["source"])
    add("全量结构化", "逐专业招生明细数", foundation["major_detail_count"], foundation["source"])
    add("全量结构化", "字段核验任务数", foundation["field_verification_task_count"], foundation["source"])
    add("全量结构化", "PDF页数", foundation["pdf_page_count"], foundation["source"])
    add("全量结构化", "页列数", foundation["page_side_count"], foundation["source"])

    first = snapshot["first_closure"]
    add("第一闭环", "页列数", first["page_side_count"], first["source"])
    add("第一闭环", "逐任务数", first["detail_task_count"], first["source"])
    add("第一闭环", "PDF原页待核任务数", first["pdf_review_pending_count"], first["source"])
    add("第一闭环", "湖北官方侧待核任务数", first["hubei_official_review_pending_count"], first["source"])
    add("第一闭环", "需要高校辅证任务数", first["school_support_required_count"], first["source"])
    add("第一闭环", "需要双人复核任务数", first["double_review_required_count"], first["source"])
    add("第一闭环", "字段可写回任务数", first["field_writeback_ready_count"], first["source"])
    for lane, value in first["lane_counts"].items():
        add("第一闭环", f"执行泳道：{lane}", value, first["source"])

    gates = snapshot["gates"]
    add("门禁", "字段写回允许数", gates["field_writeback_allowed_count"], gates["source"])
    add("门禁", "可作为志愿推荐依据数", gates["recommendation_basis_allowed_count"], gates["source"])
    add("门禁", "最终可用数", gates["final_available_count"], gates["source"])

    source = snapshot["school_source"]
    add("高校官网辅证", "官网辅证任务数", source["task_count"], source["source"])
    add("高校官网辅证", "涉及学校数", source["unique_school_count"], source["source"])
    add("高校官网辅证", "live补源尝试数", source["live_source_attempt_count"], source["source"])
    add("高校官网辅证", "已取得湖北物理计划明细的live学校数", source["live_structured_hubei_plan_school_count"], source["source"])

    shortlist = snapshot["round4_shortlist"]
    add("候选压缩", "Round4优先讨论专业组", shortlist["source_priority_group_count"], shortlist["source"])
    add("候选压缩", "本轮重点核验专业组", shortlist["selected_group_count"], shortlist["source"])
    add("候选压缩", "暂缓专业组", shortlist["paused_group_count"], shortlist["source"])
    add("候选压缩", "重点组完整专业明细", shortlist["selected_major_detail_count"], shortlist["source"])

    return rows


def main():
    stable_summary = read_json(WORKING / "issue19-stable-foundation-v0-status-summary.json")
    closure_summary = read_json(EXPORTS / "issue19-closure-and-shortlist-v1-summary.json")
    first_exec_summary = read_json(WORKING / "issue19-stable-foundation-first-closure-execution-queue-summary.json")
    first_field_summary = read_json(WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger-summary.json")
    page_side_summary = read_json(WORKING / "issue19-page-side-foundation-risk-register-summary.json")

    major_browser = EXPORTS / "issue19-stable-foundation-major-browser.csv"
    group_browser = EXPORTS / "issue19-stable-foundation-group-browser.csv"
    field_tasks = WORKING / "issue19-field-fact-verification-tasks.csv"
    live_rows = read_csv_rows(WORKING / "issue19-school-source-live-20260629-ledger.csv")
    first_field_rows = read_csv_rows(WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv")

    first_closure = closure_summary.get("first_closure", {})
    school_source = closure_summary.get("school_source", {})
    round4 = closure_summary.get("round4_shortlist", {})
    gates = closure_summary.get("gates", {})

    structured_hubei_live = [
        row
        for row in live_rows
        if row.get("结构化输出", "").strip()
        and "湖北" in row.get("湖北物理计划状态", "")
        and "未取得" not in row.get("湖北物理计划状态", "")
    ]

    snapshot = {
        "status": "issue19_data_foundation_status_snapshot_not_final",
        "generated_date": date.today().isoformat(),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "usage_boundary": "用于回答数据基座推进状态、后续核验动作和人工协作范围；不确认字段事实，不生成最终志愿方案。",
        "foundation": {
            "source": "data/working/issue19-stable-foundation-v0-status-summary.json；data/exports/issue19-stable-foundation-*-browser.csv",
            "school_count": stable_summary.get("full_ocr_school_rows"),
            "group_count": stable_summary.get("full_ocr_group_rows") or csv_count(group_browser),
            "major_detail_count": stable_summary.get("full_ocr_major_rows") or csv_count(major_browser),
            "field_verification_task_count": csv_count(field_tasks),
            "pdf_page_count": page_side_summary.get("unique_pdf_page_count"),
            "page_side_count": page_side_summary.get("unique_page_side_count") or page_side_summary.get("row_count"),
        },
        "first_closure": {
            "source": "data/exports/issue19-closure-and-shortlist-v1-summary.json；data/working/issue19-stable-foundation-first-closure-*-summary.json",
            "page_side_count": first_closure.get("page_side_count") or first_exec_summary.get("public_row_count"),
            "detail_task_count": first_closure.get("detail_task_count") or first_exec_summary.get("total_task_count"),
            "pdf_review_pending_count": first_closure.get("pdf_review_pending_count") or first_field_summary.get("pdf_manual_review_pending_count"),
            "hubei_official_review_pending_count": first_closure.get("hubei_official_review_pending_count") or first_field_summary.get("hubei_official_review_pending_count"),
            "school_support_required_count": first_exec_summary.get("school_support_required_count"),
            "double_review_required_count": first_exec_summary.get("double_review_required_count") or first_field_summary.get("double_review_required_count"),
            "field_writeback_ready_count": first_closure.get("field_writeback_ready_count") or first_field_summary.get("field_writeback_ready_count", 0),
            "lane_counts": first_exec_summary.get("lane_counts", first_closure.get("lane_counts", {})),
            "manual_review_lane_counts": first_field_summary.get("manual_review_lane_counts", count_values(first_field_rows, "人工核验泳道")),
            "field_counts": first_field_summary.get("field_counts", count_values(first_field_rows, "字段名")),
        },
        "school_source": {
            "source": "data/exports/issue19-closure-and-shortlist-v1-summary.json；data/working/issue19-school-source-live-20260629-ledger.csv",
            "task_count": school_source.get("task_count"),
            "unique_school_count": school_source.get("unique_school_count"),
            "opportunity_type_counts": school_source.get("opportunity_type_counts", {}),
            "live_source_attempt_count": len(live_rows),
            "live_structured_hubei_plan_school_count": len({row.get("院校代码") for row in structured_hubei_live}),
            "live_structured_hubei_plan_schools": [
                {
                    "院校代码": row.get("院校代码"),
                    "院校名称": row.get("院校名称"),
                    "官方来源URL": row.get("官方来源URL"),
                    "湖北物理计划状态": row.get("湖北物理计划状态"),
                }
                for row in structured_hubei_live
            ],
        },
        "round4_shortlist": {
            "source": "data/exports/issue19-closure-and-shortlist-v1-summary.json",
            "source_priority_group_count": round4.get("source_priority_group_count"),
            "selected_group_count": round4.get("selected_group_count"),
            "paused_group_count": round4.get("paused_group_count"),
            "selected_major_detail_count": round4.get("selected_major_detail_count"),
            "gradient_counts": round4.get("gradient_counts", {}),
            "major_acceptance_counts": round4.get("major_acceptance_counts", {}),
        },
        "gates": {
            "source": "data/exports/issue19-closure-and-shortlist-v1-summary.json",
            "field_writeback_allowed_count": gates.get("field_writeback_ready_count", 0),
            "recommendation_basis_allowed_count": gates.get("recommendation_basis_allowed_count", 0),
            "final_available_count": gates.get("final_available_count", 0),
        },
        "current_assessment": {
            "what_is_solid": [
                "第19期全量OCR结构化底稿已经可以浏览、筛选、回溯页码版面列。",
                "专业组和逐专业明细已经能用于候选发现、风险分层和核验排队。",
                "第一闭环已经压缩到37个页列、206条关键字段任务。",
            ],
            "what_is_not_solid": [
                "计划数、学费、再选科目等字段尚未完成PDF原页和湖北官方侧闭环。",
                "高校官网辅证只允许作为double check和冲突发现，不能替代湖北官方计划。",
                "字段写回、志愿推荐依据和最终可用门禁当前均为0。",
            ],
            "assistant_can_continue": [
                "继续自动搜索高校官网2026湖北物理招生计划源，并沉淀来源URL、留存文件、结构化抽取和冲突摘要。",
                "继续把第一闭环队列拆成更小的人工核页批次，优先E0冲突、E1计划数补缺或偏大、E2官网未匹配。",
                "继续为55个重点专业组展开完整专业、标记调剂风险和家庭接受度初判。",
                "继续生成/更新Excel浏览表、公开状态账本、校验脚本和GitHub同步。",
            ],
            "user_needed": [
                "在最终候选组收窄后，按我给出的页码版面键核第19期PDF或纸质原页。",
                "能登录湖北官方系统时，对入围院校专业组逐项核专业代号、专业名称、计划数、学费、选科、备注和组边界。",
                "对需要双人复核的冲突页列做第二遍确认，尤其是左右栏串读、计划数异常、官网与OCR不一致处。",
                "继续补充家庭无法接受专业、预算、地域、读研/就业/师范意愿等决策偏好。",
            ],
        },
    }

    OUT_JSON.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = metric_rows(snapshot)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["板块", "指标", "当前值", "来源", "说明"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
