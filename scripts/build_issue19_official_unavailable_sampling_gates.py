#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from math import ceil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHOOL_REFRESH = ROOT / "data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv"
EVIDENCE_ROUTING = ROOT / "data/working/issue19-major-evidence-level-routing.csv"
LIVE_RECHECK = ROOT / "data/working/issue19-official-public-entry-live-recheck.json"
OUTPUT_CSV = ROOT / "data/working/issue19-official-unavailable-sampling-gates.csv"
OUTPUT_SUMMARY = ROOT / "data/working/issue19-official-unavailable-sampling-gates-summary.json"

FIELDS = [
    "官方不可得抽样门禁ID",
    "来源类型",
    "来源账本ID",
    "来源逐专业证据路由ID",
    "来源高校侧辅证刷新账本",
    "来源湖北官方活体复查",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许写回字段事实",
    "院校代码",
    "院校名称OCR",
    "专业行ID",
    "专业组出现ID",
    "院校专业组代码OCR规范化",
    "页码版面键",
    "来源文件类型集合",
    "官网辅证自动动作",
    "风险等级",
    "抽样分层",
    "抽样策略",
    "是否纳入抽样或100%核验",
    "样本选择原因",
    "样本最低明细数",
    "涉及招生明细数",
    "必核字段",
    "字段差异标记",
    "升级触发器",
    "升级范围",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方一致性状态",
    "字段事实写回状态",
    "当前用途边界",
    "下一步",
]

ACTION_RISK = {
    "C0-冲突先核PDF原页和湖北官方系统": (
        "R4-blocker",
        "100%人工核验",
        "计划数冲突或疑似字段错位，不能进入筛选。",
    ),
    "C1-官网补缺候选但禁止自动写回": (
        "R3-high",
        "100%人工核验",
        "OCR字段缺口但高校官网有补缺线索，必须回原页和湖北官方侧。",
    ),
    "C7-官网源未匹配专业需人工确认专业名": (
        "R3-high",
        "100%人工核验",
        "官网未匹配专业名或限定词，必须确认专业归属和组内边界。",
    ),
    "C4-已有部分来源需补结构化或补湖北行": (
        "R2-medium",
        "自动结构化刷新后人工抽检",
        "先自动复跑高校来源并产出字段级 diff，异常再人工升级。",
    ),
    "C3-字段辅证补充结构化后核原页": (
        "R2-medium",
        "自动结构化刷新后人工抽检",
        "字段辅证需补结构化，再回原页和湖北官方侧确认。",
    ),
    "C6-继续搜索高校官网2026湖北计划源": (
        "R2-medium",
        "自动补源后重新分层",
        "先继续搜索高校官网 2026 湖北计划源，不能用空源判断字段事实。",
    ),
    "C5-仅章程规则核特殊要求不能核计划数": (
        "R2-medium",
        "章程规则人工抽检",
        "章程只能核特殊要求，不能核计划数或专业组边界。",
    ),
    "C2-强辅证抽检并等待湖北官方闭环": (
        "R1-low",
        "强辅证分层抽检",
        "强辅证一致但湖北官方侧未闭环，只能抽检后作为机器筛选线索。",
    ),
}


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def page_side(row):
    page = str(row.get("来源页码", "")).strip()
    side = str(row.get("版面列", "")).strip()
    return f"{int(page):03d}-{side}" if page.isdigit() and side else f"{page}-{side}"


def deterministic_pick(rows, count):
    selected = []
    selected_ids = set()
    strata_fields = [
        "来源页码",
        "院校代码",
        "三年投档稳定性状态",
        "调剂影响等级",
    ]
    for field in strata_fields:
        first_by_key = {}
        for row in sorted(rows, key=lambda item: stable_id("P3SORT", [field, item.get("专业行ID", "")])):
            key = row.get(field, "")
            if key and key not in first_by_key:
                first_by_key[key] = row
        for key in sorted(first_by_key):
            row = first_by_key[key]
            major_id = row.get("专业行ID", "")
            if major_id not in selected_ids:
                selected.append(row)
                selected_ids.add(major_id)
            if len(selected) >= count:
                return selected
    for row in sorted(rows, key=lambda item: stable_id("P3FILL", [item.get("专业行ID", "")])):
        major_id = row.get("专业行ID", "")
        if major_id not in selected_ids:
            selected.append(row)
            selected_ids.add(major_id)
        if len(selected) >= count:
            break
    return selected


def school_task_row(row, c2_total_detail_count):
    action = row.get("官网辅证自动动作", "")
    risk, policy, reason = ACTION_RISK.get(
        action,
        ("R2-medium", "自动核验后人工抽检", "高校侧来源只能作为辅证。"),
    )
    involved_count = as_int(row.get("涉及招生明细数"))
    selected = action in {
        "C0-冲突先核PDF原页和湖北官方系统",
        "C1-官网补缺候选但禁止自动写回",
        "C7-官网源未匹配专业需人工确认专业名",
        "C2-强辅证抽检并等待湖北官方闭环",
    }
    if "100%人工核验" in policy:
        sample_min = involved_count
    elif action == "C2-强辅证抽检并等待湖北官方闭环":
        sample_min = max(1, ceil(involved_count * 20 / max(c2_total_detail_count, 1)))
    else:
        sample_min = 0
    return {
        "官方不可得抽样门禁ID": stable_id(
            "SAMPLINGGATE",
            [row.get("高校侧辅证刷新公开账本ID", ""), action],
        ),
        "来源类型": "高校侧辅证刷新任务",
        "来源账本ID": row.get("高校侧辅证刷新公开账本ID", ""),
        "来源逐专业证据路由ID": "",
        "来源高校侧辅证刷新账本": "data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv",
        "来源湖北官方活体复查": "data/working/issue19-official-public-entry-live-recheck.json",
        "来源期号": row.get("来源期号", ""),
        "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
        "数据阶段": "issue19_official_unavailable_sampling_gates",
        "主表粒度": "高校侧任务或低风险抽检专业明细",
        "任务粒度": "高校×动作 或 逐专业抽检样本",
        "最终可用": "false",
        "可进入下一阶段": "false",
        "是否允许作为志愿推荐依据": "false",
        "是否允许生成学校专业建议": "false",
        "是否允许自动写回主表": "false",
        "是否允许官网证据替代湖北官方计划": "false",
        "是否允许写回字段事实": "false",
        "院校代码": row.get("院校代码", ""),
        "院校名称OCR": row.get("院校名称OCR", ""),
        "专业行ID": "",
        "专业组出现ID": "",
        "院校专业组代码OCR规范化": "",
        "页码版面键": "",
        "来源文件类型集合": row.get("来源文件类型集合", ""),
        "官网辅证自动动作": action,
        "风险等级": risk,
        "抽样分层": row.get("高校侧刷新批次", ""),
        "抽样策略": policy,
        "是否纳入抽样或100%核验": "true" if selected else "false",
        "样本选择原因": reason,
        "样本最低明细数": str(sample_min),
        "涉及招生明细数": str(involved_count),
        "必核字段": "专业名；专业计划数；学费；再选科目；校区/学制/备注；特殊限制",
        "字段差异标记": row.get("差异字段集合", ""),
        "升级触发器": "计划数冲突；关键限定词缺失；物理/历史未拆；非2026湖北物理普通本科来源；同组家庭不可接受专业；抽检失败",
        "升级范围": "同页列100%；同一学校出现2个失败则同校100%；同一专业组失败则整组100%",
        "PDF原页核页状态": row.get("PDF原页核页状态", ""),
        "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统或省招办计划核验状态", ""),
        "高校官网或招生章程辅证状态": row.get("高校官网或招生章程辅证状态", ""),
        "三方一致性状态": "pending_pdf_hubei_school_consistency_review",
        "字段事实写回状态": row.get("字段事实写回状态", ""),
        "当前用途边界": "只用于官方不可得时的double-check、抽样和升级派单；不能作为最终志愿依据。",
        "下一步": row.get("下一步", ""),
    }


def p3_sample_row(row):
    trigger = row.get("升级触发器集合", "")
    trigger_text = f"{trigger}；低风险抽检失败" if trigger else "低风险抽检失败"
    return {
        "官方不可得抽样门禁ID": stable_id(
            "SAMPLINGGATE",
            [row.get("逐专业证据路由ID", ""), row.get("专业行ID", "")],
        ),
        "来源类型": "P3低风险抽检专业明细",
        "来源账本ID": "",
        "来源逐专业证据路由ID": row.get("逐专业证据路由ID", ""),
        "来源高校侧辅证刷新账本": "",
        "来源湖北官方活体复查": "data/working/issue19-official-public-entry-live-recheck.json",
        "来源期号": row.get("来源期号", ""),
        "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
        "数据阶段": "issue19_official_unavailable_sampling_gates",
        "主表粒度": "高校侧任务或低风险抽检专业明细",
        "任务粒度": "高校×动作 或 逐专业抽检样本",
        "最终可用": "false",
        "可进入下一阶段": "false",
        "是否允许作为志愿推荐依据": "false",
        "是否允许生成学校专业建议": "false",
        "是否允许自动写回主表": "false",
        "是否允许官网证据替代湖北官方计划": "false",
        "是否允许写回字段事实": "false",
        "院校代码": row.get("院校代码", ""),
        "院校名称OCR": row.get("院校名称OCR", ""),
        "专业行ID": row.get("专业行ID", ""),
        "专业组出现ID": row.get("专业组出现ID", ""),
        "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
        "页码版面键": page_side(row),
        "来源文件类型集合": "",
        "官网辅证自动动作": "P3-低风险抽检但非最终",
        "风险等级": "R0-observe",
        "抽样分层": "P3-低风险抽检池",
        "抽样策略": "10%且不少于25条逐专业明细分层抽检",
        "是否纳入抽样或100%核验": "true",
        "样本选择原因": "从184条P3低风险池按页码、学校、历史稳定性和调剂影响分层抽取；通过也只允许作为机器筛选线索。",
        "样本最低明细数": "1",
        "涉及招生明细数": "1",
        "必核字段": "专业名；专业计划数；学费；再选科目；备注/限定词",
        "字段差异标记": row.get("官网差异字段集合", ""),
        "升级触发器": trigger_text,
        "升级范围": "抽检失败则同页列100%；同一学校出现2个失败则同校100%；同一专业组失败则整组100%",
        "PDF原页核页状态": row.get("PDF原页核验状态", ""),
        "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统核验状态", ""),
        "高校官网或招生章程辅证状态": row.get("高校官网来源状态", ""),
        "三方一致性状态": "pending_pdf_hubei_school_consistency_review",
        "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
        "当前用途边界": "低风险样本只用于校验底座稳定性；不能作为志愿推荐依据。",
        "下一步": row.get("人工核验下一步", ""),
    }


def main():
    school_rows = read_csv(SCHOOL_REFRESH)
    routing_rows = read_csv(EVIDENCE_ROUTING)
    live_status = json.loads(LIVE_RECHECK.read_text(encoding="utf-8"))
    p3_pool = [
        row for row in routing_rows
        if row.get("人工核验优先级", "").startswith("P3-")
        and row.get("是否可低风险抽检") == "true"
    ]
    p3_sample_count = max(25, ceil(len(p3_pool) * 0.10))
    p3_samples = deterministic_pick(p3_pool, min(p3_sample_count, len(p3_pool)))

    c2_total_detail_count = sum(
        as_int(row.get("涉及招生明细数"))
        for row in school_rows
        if row.get("官网辅证自动动作") == "C2-强辅证抽检并等待湖北官方闭环"
    )
    rows = [school_task_row(row, c2_total_detail_count) for row in school_rows]
    rows.extend(p3_sample_row(row) for row in p3_samples)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    action_counts = Counter(row["官网辅证自动动作"] for row in rows)
    risk_counts = Counter(row["风险等级"] for row in rows)
    selected_count = sum(row["是否纳入抽样或100%核验"] == "true" for row in rows)
    c2_rows = [
        row for row in rows
        if row["官网辅证自动动作"] == "C2-强辅证抽检并等待湖北官方闭环"
    ]
    summary = {
        "status": "issue19_official_unavailable_sampling_gates_not_final",
        "generated_by": "build_issue19_official_unavailable_sampling_gates.py",
        "source_issue": "湖北招生考试2026年19期·本科普通批（下）",
        "source_pdf_sha256": rows[0]["来源PDF_SHA256"] if rows else "",
        "source_school_refresh_ledger": "data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv",
        "source_evidence_routing": "data/working/issue19-major-evidence-level-routing.csv",
        "source_official_live_recheck": "data/working/issue19-official-public-entry-live-recheck.json",
        "official_live_recheck_can_finalize": live_status.get("current_conclusion", {}).get("can_finalize_admission_plan_from_public_entry"),
        "official_live_recheck_without_login_structured_plan_available": live_status.get("current_conclusion", {}).get("can_get_official_structured_plan_without_login"),
        "input_files": [
            {
                "path": "data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv",
                "sha256": sha256(SCHOOL_REFRESH),
                "row_count": len(school_rows),
            },
            {
                "path": "data/working/issue19-major-evidence-level-routing.csv",
                "sha256": sha256(EVIDENCE_ROUTING),
                "row_count": len(routing_rows),
            },
            {
                "path": "data/working/issue19-official-public-entry-live-recheck.json",
                "sha256": sha256(LIVE_RECHECK),
            },
        ],
        "output_table": "data/working/issue19-official-unavailable-sampling-gates.csv",
        "row_grain": "高校侧任务或低风险抽检专业明细",
        "row_count": len(rows),
        "unique_sampling_gate_id_count": len({row["官方不可得抽样门禁ID"] for row in rows}),
        "school_refresh_task_count": len(school_rows),
        "p3_low_risk_pool_major_count": len(p3_pool),
        "p3_low_risk_sample_major_count": len(p3_samples),
        "selected_or_100pct_task_count": selected_count,
        "risk_level_counts": dict(risk_counts),
        "action_counts": dict(action_counts),
        "c0_c1_c7_100pct_major_count": sum(
            as_int(row.get("涉及招生明细数"))
            for row in school_rows
            if row.get("官网辅证自动动作")
            in {
                "C0-冲突先核PDF原页和湖北官方系统",
                "C1-官网补缺候选但禁止自动写回",
                "C7-官网源未匹配专业需人工确认专业名",
            }
        ),
        "c2_strong_support_pool_major_count": c2_total_detail_count,
        "c2_selected_school_task_count": len(c2_rows),
        "c2_min_sample_major_count": sum(as_int(row["样本最低明细数"]) for row in c2_rows),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "policy": {
            "high_risk": "C0/C1/C7 和任何后续冲突、缺口、未匹配项必须 100% 回看第19期原页并核湖北官方侧。",
            "automatic_double_check": "C3/C4/C5/C6 先自动补结构化、补源或核章程规则，只产出 diff 和升级提示，不写回字段。",
            "sampling": "C2 强辅证抽检最低覆盖 20 条明细；P3 低风险池抽 10% 且不少于 25 条。",
            "escalation": "抽检失败即同页列100%；同校2个失败则同校100%；同组失败则整组100%。",
            "boundary": "通过抽检最多开放机器初筛线索，推荐依据和最终可用仍需 PDF 原页、湖北官方侧、高校官网/章程、家庭接受度和调剂结论闭环。",
        },
    }
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
