#!/usr/bin/env python3
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FULL_OCR_SUMMARY = ROOT / "data/working/issue19-full-admission-plan-ocr-draft-summary.json"
STABILITY_SUMMARY = ROOT / "data/working/issue19-foundation-stability-dashboard-summary.json"
SCREENING_SUMMARY = ROOT / "data/working/issue19-stable-foundation-screening-summary.json"
GROUP_READINESS_SUMMARY = ROOT / "data/working/issue19-stable-foundation-group-readiness-bridge-summary.json"
FIELD_FACT_SUMMARY = ROOT / "data/working/issue19-field-fact-closure-ledger-summary.json"
FIELD_TASK_SUMMARY = ROOT / "data/working/issue19-field-fact-verification-tasks-summary.json"
PAGE_BATCH_SUMMARY = ROOT / "data/working/issue19-page-side-foundation-all-batch-review-public-ledger-summary.json"
FIRST_CLOSURE_SUMMARY = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger-summary.json"
)
SCHOOL_OPPORTUNITY_SUMMARY = ROOT / "data/working/issue19-school-source-opportunity-queue-summary.json"
C4_C6_DIFF_SUMMARY = ROOT / "data/working/issue19-c4-c6-structured-candidate-diff-summary.json"

STATUS_CSV = ROOT / "data/working/issue19-stable-foundation-v0-status.csv"
STATUS_JSON = ROOT / "data/working/issue19-stable-foundation-v0-status-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"

FIELDS = [
    "层级序号",
    "底座层级",
    "当前状态",
    "是否完成",
    "是否可用于候选发现",
    "是否可用于定稿依据",
    "关键证据表",
    "当前规模",
    "已完成证据",
    "主要缺口",
    "下一步最短动作",
    "保真边界",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(rows):
    STATUS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with STATUS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def int_value(obj, key, default=0):
    value = obj.get(key, default)
    return value if isinstance(value, int) else default


def main():
    full = load_json(FULL_OCR_SUMMARY)
    stability = load_json(STABILITY_SUMMARY)
    screening = load_json(SCREENING_SUMMARY)
    groups = load_json(GROUP_READINESS_SUMMARY)
    field_fact = load_json(FIELD_FACT_SUMMARY)
    field_tasks = load_json(FIELD_TASK_SUMMARY)
    page_batch = load_json(PAGE_BATCH_SUMMARY)
    first_closure = load_json(FIRST_CLOSURE_SUMMARY)
    school_opp = load_json(SCHOOL_OPPORTUNITY_SUMMARY)
    c4_c6 = load_json(C4_C6_DIFF_SUMMARY)

    full_counts = full["counts"]
    rows = [
        {
            "层级序号": "1",
            "底座层级": "原始结构化层",
            "当前状态": "完成V0",
            "是否完成": "true",
            "是否可用于候选发现": "true",
            "是否可用于定稿依据": "false",
            "关键证据表": "data/working/issue19-full-admission-plan-ocr-draft.csv；data/working/issue19-full-admission-plan-ocr-draft-summary.json",
            "当前规模": (
                f"{full_counts['OCR院校数']}所院校；"
                f"{full_counts['OCR院校专业组数']}个专业组；"
                f"{full_counts['OCR专业行数']}条逐专业明细；"
                f"{full_counts['无专业行专业组数']}个0明细专业组"
            ),
            "已完成证据": "第19期PDF全量OCR结构化、来源期号、PDF SHA256、公开CSV和摘要均已留存。",
            "主要缺口": "OCR初稿不能直接当定稿事实；0明细专业组和字段缺口仍需核验。",
            "下一步最短动作": "把本层锁定为候选发现底座，不再等待全量人工核完才开始筛候选。",
            "保真边界": "只代表第19期PDF的机器结构化读数，不代表已人工确认或湖北官方系统确认。",
        },
        {
            "层级序号": "2",
            "底座层级": "血缘追溯与页列证据层",
            "当前状态": "完成V0",
            "是否完成": "true",
            "是否可用于候选发现": "true",
            "是否可用于定稿依据": "false",
            "关键证据表": "data/working/issue19-page-manifest.csv；data/working/issue19-major-line-pdf-evidence-anchors.csv；data/working/issue19-page-side-foundation-all-batch-review-public-ledger.csv",
            "当前规模": (
                f"{page_batch['unique_pdf_page_count']}个PDF页；"
                f"{page_batch['unique_page_side_count']}个页列；"
                f"{page_batch['unique_major_count']}条专业行；"
                f"{page_batch['field_task_count']}个字段任务"
            ),
            "已完成证据": "专业行、页码、版面列、页列批次、字段任务、私有核验模板SHA已连通。",
            "主要缺口": "人工字段记录尚未填入公开状态机，不能写回字段事实。",
            "下一步最短动作": "候选组确定后按页列回看原页；优先核第一闭环37个页列。",
            "保真边界": "公开层只保存页列、任务、SHA和状态，不保存原图路径、OCR窗口原文或人工字段记录。",
        },
        {
            "层级序号": "3",
            "底座层级": "证据分层与筛选入口层",
            "当前状态": "完成V0",
            "是否完成": "true",
            "是否可用于候选发现": "true",
            "是否可用于定稿依据": "false",
            "关键证据表": "data/working/issue19-stable-foundation-major-screening-view.csv；data/working/issue19-stable-foundation-group-screening-view.csv；data/working/issue19-stable-foundation-group-readiness-bridge.csv",
            "当前规模": (
                f"{screening['major_row_count']}条逐专业筛选行；"
                f"{screening['group_row_count']}个专业组；"
                f"{screening['major_machine_signal_true_count']}条机器初筛线索；"
                f"{groups['discussion_layer_counts'].get('D3-偏好线索待核后优先讨论', 0)}个偏好线索组"
            ),
            "已完成证据": "家庭底线、字段缺口、专业偏好、调剂风险、历史投档线索和核验路由已聚合到逐专业/专业组视图。",
            "主要缺口": "所有定稿门禁仍为false；只能筛线索，不能直接生成志愿表。",
            "下一步最短动作": "先用专业组桥接表筛出偏好线索和可讨论观察池，再对入围组做完整专业组核验。",
            "保真边界": "机器初筛线索不是可报结论；服从调剂必须看完整专业组。",
        },
        {
            "层级序号": "4",
            "底座层级": "字段事实闭环层",
            "当前状态": "未完成",
            "是否完成": "false",
            "是否可用于候选发现": "limited",
            "是否可用于定稿依据": "false",
            "关键证据表": "data/working/issue19-field-fact-closure-ledger.csv；data/working/issue19-field-fact-verification-tasks.csv；data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv",
            "当前规模": (
                f"{field_fact['row_count']}条逐专业字段账本；"
                f"{field_tasks['row_count']}个逐字段任务；"
                f"{first_closure['row_count']}个第一闭环任务；"
                f"{first_closure['field_writeback_ready_count']}个字段可写回"
            ),
            "已完成证据": "字段缺口、候选值、核验任务、第一闭环任务和私有复核模板已生成。",
            "主要缺口": (
                f"{field_fact['manual_confirmed_field_count']}个字段人工确认；"
                f"{field_fact['pdf_review_pending_count']}条PDF原页待核；"
                f"{field_fact['hubei_official_review_pending_count']}条湖北官方待核"
            ),
            "下一步最短动作": "不要全量人工核；只核进入候选讨论的专业组和第一闭环任务。",
            "保真边界": "字段事实未闭环前，不允许自动写回，不允许作为定稿方案依据。",
        },
        {
            "层级序号": "5",
            "底座层级": "高校官网辅证层",
            "当前状态": "进行中",
            "是否完成": "false",
            "是否可用于候选发现": "true",
            "是否可用于定稿依据": "false",
            "关键证据表": "data/working/issue19-school-source-opportunity-queue.csv；data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv",
            "当前规模": (
                f"{school_opp['row_count']}个高校辅证机会；"
                f"{school_opp['unique_school_count']}所学校；"
                f"{c4_c6['private_detail_row_count']}条C4/C6私有明细；"
                f"{c4_c6['plan_match_candidate_count']}条计划数一致候选；"
                f"{c4_c6['plan_mismatch_candidate_count']}条计划数冲突候选"
            ),
            "已完成证据": "已把可复用高校官网/API/PDF/XLSX源统一为辅证、diff和抽检线索。",
            "主要缺口": "仍有学校缺结构化源；官网源不能替代湖北官方专业组边界。",
            "下一步最短动作": "只继续处理入围候选组相关学校；停止为全库无限制扩源。",
            "保真边界": "高校官网只做double check、补缺候选和冲突发现，不替代第19期PDF原页或湖北官方系统。",
        },
        {
            "层级序号": "6",
            "底座层级": "稳定基座V0发布结论",
            "当前状态": "可用于候选发现；不可用于定稿依据",
            "是否完成": "conditional",
            "是否可用于候选发现": "true",
            "是否可用于定稿依据": "false",
            "关键证据表": "data/working/issue19-stable-foundation-v0-status.csv；docs/STABLE_FOUNDATION_V0_STATUS.md",
            "当前规模": (
                f"闭环可用专业行={stability['final_available_count']}；"
                f"可进入下一阶段专业行={stability['next_stage_available_count']}；"
                f"推荐依据专业组={groups['recommendation_basis_allowed_count']}"
            ),
            "已完成证据": "结构化、血缘、筛选、分层、辅证机会均可复用且可追溯。",
            "主要缺口": "字段事实和湖北官方侧未闭环；不能直接给定稿志愿表。",
            "下一步最短动作": "立刻进入候选发现和筛选：先选专业组，再对入围组逐项核字段和调剂风险。",
            "保真边界": "V0是筛选底座，不是录取定稿方案；定稿方案必须做入围组100%核验。",
        },
    ]

    write_csv(rows)
    summary = {
        "status": "issue19_stable_foundation_v0_candidate_discovery_ready_not_final",
        "generated_by": "build_issue19_stable_foundation_v0_status.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": str(STATUS_CSV.relative_to(ROOT)),
        "row_count": len(rows),
        "stable_foundation_v0_candidate_discovery_ready": True,
        "stable_foundation_v0_final_recommendation_ready": False,
        "full_ocr_major_rows": full_counts["OCR专业行数"],
        "full_ocr_group_rows": full_counts["OCR院校专业组数"],
        "full_ocr_school_rows": full_counts["OCR院校数"],
        "zero_detail_group_count": full_counts["无专业行专业组数"],
        "machine_signal_major_count": screening["major_machine_signal_true_count"],
        "machine_observation_group_count": screening["group_machine_observation_pool_count"],
        "preference_group_count": screening["group_preference_priority_count"],
        "first_closure_task_count": first_closure["row_count"],
        "first_closure_page_side_count": first_closure["unique_page_side_count"],
        "field_writeback_ready_count": first_closure["field_writeback_ready_count"],
        "field_fact_manual_confirmed_field_count": field_fact["manual_confirmed_field_count"],
        "pdf_review_pending_count": field_fact["pdf_review_pending_count"],
        "hubei_official_review_pending_count": field_fact["hubei_official_review_pending_count"],
        "school_source_opportunity_count": school_opp["row_count"],
        "school_source_opportunity_school_count": school_opp["unique_school_count"],
        "c4_c6_plan_match_candidate_count": c4_c6["plan_match_candidate_count"],
        "c4_c6_plan_mismatch_candidate_count": c4_c6["plan_mismatch_candidate_count"],
        "final_available_count": stability["final_available_count"],
        "next_stage_available_count": stability["next_stage_available_count"],
        "recommendation_basis_allowed_count": groups["recommendation_basis_allowed_count"],
        "release_decision": "V0可用于候选发现和排序核验优先级；不可用于定稿方案依据、字段写回或替代湖北官方计划。",
        "fastest_path": [
            "停止全库无限扩源，锁定V0用于候选发现。",
            "按家庭偏好和分数排名筛出专业组观察池。",
            "只对入围专业组做完整专业组、字段事实、调剂和章程限制100%核验。",
            "志愿定稿方案必须在入围组核验完成后生成。",
        ],
        "hard_boundaries": {
            "official_plan_replacement_allowed": False,
            "field_writeback_allowed": False,
            "recommendation_basis_allowed": False,
            "school_major_suggestion_allowed": False,
        },
    }
    STATUS_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public_text = STATUS_CSV.read_text(encoding="utf-8", errors="ignore") + STATUS_JSON.read_text(
        encoding="utf-8", errors="ignore"
    )
    forbidden = [
        "/Users/",
        "private/",
        "Authorization",
        "Bearer ",
        "Cookie",
        "最终推荐",
        "最终方案",
        "可填报",
        "人工读数",
    ]
    if any(token in public_text for token in forbidden):
        raise SystemExit("稳定基座V0状态公开文件包含禁止公开内容")
    print(f"写出稳定基座 V0 状态表：{STATUS_CSV.relative_to(ROOT)}")
    print(f"写出稳定基座 V0 状态摘要：{STATUS_JSON.relative_to(ROOT)}")
    print("V0结论：可用于候选发现；不可用于定稿依据。")


if __name__ == "__main__":
    main()
