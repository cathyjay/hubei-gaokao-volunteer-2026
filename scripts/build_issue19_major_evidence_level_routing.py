#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
STABILITY_DASHBOARD = ROOT / "data/working/issue19-foundation-stability-dashboard.csv"
DECISION_GATES = ROOT / "data/working/issue19-major-decision-readiness-gates.csv"
FIELD_FACT_LEDGER = ROOT / "data/working/issue19-field-fact-closure-ledger.csv"
B0_B1_DIFF_LEDGER = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
HISTORICAL_SIDECAR = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar.csv"

OUTPUT = ROOT / "data/working/issue19-major-evidence-level-routing.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-major-evidence-level-routing-summary.json"

DATA_STAGE = "issue19_major_evidence_level_routing"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"


FIELDS = [
    "逐专业证据路由ID",
    "来源单一逐专业招生明细总工作台",
    "来源底座稳定性总看板",
    "来源逐专业决策闸门表",
    "来源字段事实闭环总账",
    "来源B0B1高校官网差异账",
    "来源三年投档线索旁挂表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "是否真实招生明细",
    "省招办证据等级",
    "证据等级说明",
    "底座稳定性等级",
    "决策闸门状态",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "字段缺口数",
    "字段缺口字段",
    "三字段OCR完整状态",
    "PDF原页核验状态",
    "湖北官方系统核验状态",
    "高校官网来源状态",
    "高校官网证据匹配状态",
    "高校官网计划数核验状态",
    "高校官网能否替代湖北官方计划",
    "官网差异账是否命中",
    "官网差异字段集合",
    "自动官网核验可执行性",
    "人工核验优先级",
    "人工核验强度",
    "人工核验范围",
    "是否必须100%人工核验",
    "是否可低风险抽检",
    "升级触发器集合",
    "学校所在地/校区核验状态",
    "家庭接受度核验状态",
    "同组调剂结论",
    "同组真实招生明细数",
    "同组医学护理排除专业数",
    "同组高收费或超预算专业数",
    "同组特殊限制待核专业数",
    "专业偏好方向",
    "专业风险类型",
    "机器专业接受度初判",
    "调剂影响等级",
    "三年投档稳定性状态",
    "同代码命中年份数",
    "历史线使用口径",
    "可否进入候选讨论",
    "可否进入最终志愿方案",
    "自动官网核验下一步",
    "人工核验下一步",
    "不得进入原因",
    "下一步",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def index_by(rows, field):
    result = {}
    for row in rows:
        key = row.get(field, "")
        if key:
            result[key] = row
    return result


def ordered_join(values):
    seen = set()
    result = []
    for value in values:
        cleaned = str(value or "").strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return "；".join(result)


def has_reusable_school_source(source_status, match_status, plan_status):
    source_text = " ".join([source_status, match_status, plan_status])
    return (
        "has_reusable_2026_hubei_plan_source" in source_text
        or "matched" in source_text
        or "possible_match" in source_text
        or "官网专业名匹配" in source_text
        or "mismatch" in source_text
    )


def evidence_level(master_row, diff_row):
    source_status = master_row.get("高校官网来源状态", "")
    match_status = master_row.get("高校官网证据匹配状态", "")
    plan_status = master_row.get("高校官网计划数核验状态", "")
    if has_reusable_school_source(source_status, match_status, plan_status):
        return (
            "L3-高校辅证加第三方提示",
            "已存在高校官网/API/PDF/XLSX等辅证线索，可用于 double check；但未完成第19期PDF原页和湖北官方系统闭环。",
        )
    if diff_row:
        return (
            "L3-高校辅证加第三方提示",
            "已有B0/B1高校官网差异账线索，但仍需回看第19期PDF原页并核湖北官方系统。",
        )
    return (
        "L4-OCR或单源线索",
        "当前主要来自第19期PDF OCR及旁挂线索；尚未形成高校官网或省招办闭环证据。",
    )


def automatic_route(master_row):
    source_status = master_row.get("高校官网来源状态", "")
    match_status = master_row.get("高校官网证据匹配状态", "")
    plan_status = master_row.get("高校官网计划数核验状态", "")
    if "官网专业名匹配但计划数冲突" in source_status or "mismatch" in plan_status:
        return "A0-已有高校官网结构化源但存在冲突"
    if has_reusable_school_source(source_status, match_status, plan_status):
        return "A1-已有高校官网结构化源可自动复跑比对"
    if "has_partial_source_needs_followup" in source_status:
        return "A2-已有部分高校来源需补结构化"
    if "charter_or_rules_only_no_plan" in source_status:
        return "A3-仅章程规则辅证不可核计划数"
    if "needs_official_plan_source_search" in source_status:
        return "A4-需继续自动搜索高校官网计划源"
    return "A5-暂未搜索到高校官网源"


def build_triggers(master_row, stability_row, decision_row, field_row, diff_row, evidence_id):
    triggers = []
    if master_row.get("是否真实招生明细") != "true":
        triggers.append("非真实招生明细或0明细占位")
    if stability_row.get("底座稳定性等级", "").startswith("B0-"):
        triggers.append("B0结构或官方查询键强阻断")
    if stability_row.get("底座稳定性等级", "").startswith("B1-"):
        triggers.append("B1原页或官网冲突")
    if decision_row.get("候选初筛闸门状态", "").startswith("G0-"):
        triggers.append("G0结构或归属未闭环")
    if decision_row.get("候选初筛闸门状态", "").startswith("G1-"):
        triggers.append("G1家庭底线风险待确认")
    if decision_row.get("候选初筛闸门状态", "").startswith("G2-"):
        triggers.append("G2字段缺口未闭环")
    if field_row.get("字段事实阻断等级", "").startswith("Q0-"):
        triggers.append("字段缺口无候选")
    elif field_row.get("字段事实阻断等级", "").startswith("Q1-"):
        triggers.append("字段缺口有候选待核")
    if diff_row:
        triggers.append("命中B0/B1高校官网差异账")
        if "冲突" in diff_row.get("计划数核验状态", "") or "mismatch" in diff_row.get("计划数核验状态", ""):
            triggers.append("官网计划数冲突")
        if "unmatched" in diff_row.get("官网证据匹配状态", ""):
            triggers.append("官网专业未匹配")
    if as_int(stability_row.get("结构风险事件数")):
        triggers.append("结构风险事件")
    if stability_row.get("湖北官方查询键是否碰撞") == "true":
        triggers.append("湖北官方查询键碰撞")
    if stability_row.get("教育部匹配状态", "").startswith("unmatched"):
        triggers.append("教育部校名未匹配")
    if as_int(decision_row.get("同组医学护理排除专业数")):
        triggers.append("同组含不接受医学护理")
    if as_int(decision_row.get("同组高收费或超预算专业数")):
        triggers.append("同组含高收费或超预算")
    if as_int(decision_row.get("同组特殊限制待核专业数")):
        triggers.append("同组含特殊限制待核")
    if evidence_id.startswith("L4-"):
        triggers.append("仅OCR或单源线索")
    return ordered_join(triggers)


def manual_priority(master_row, stability_row, decision_row, field_row, diff_row):
    source_status = master_row.get("高校官网来源状态", "")
    plan_status = master_row.get("高校官网计划数核验状态", "")
    match_status = master_row.get("高校官网证据匹配状态", "")
    if (
        master_row.get("是否真实招生明细") != "true"
        or stability_row.get("底座稳定性等级", "").startswith("B0-")
        or decision_row.get("候选初筛闸门状态", "").startswith("G0-")
        or "官网专业名匹配但计划数冲突" in source_status
        or "mismatch" in plan_status
        or "unmatched" in match_status
        or (diff_row and "冲突" in diff_row.get("计划数核验状态", ""))
    ):
        return "P0-最终候选/冲突/结构强阻断先核"
    if (
        stability_row.get("底座稳定性等级", "").startswith("B1-")
        or stability_row.get("底座稳定性等级", "").startswith("B2-")
        or decision_row.get("候选初筛闸门状态", "").startswith("G2-")
        or field_row.get("字段事实阻断等级", "").startswith(("Q0-", "Q1-"))
        or diff_row
    ):
        return "P1-字段缺口和B0B1辅证优先核"
    if (
        decision_row.get("候选初筛闸门状态", "").startswith("G1-")
        or decision_row.get("候选初筛闸门状态", "").startswith("G3-")
        or stability_row.get("底座稳定性等级", "").startswith("B3-")
    ):
        return "P2-家庭费用调剂与三方闭环核"
    return "P3-低风险抽检但非最终"


def manual_strength(priority, auto_route):
    if priority.startswith("P0-"):
        return (
            "H0-100%人工核验",
            "同页列、同校、同专业组范围内回看PDF原页；冲突字段同步核高校官网和湖北官方系统。",
            "true",
            "false",
        )
    if priority.startswith("P1-"):
        return (
            "H1-页列集中人工核验",
            "按页列批次回看三字段和专业行上下文；命中最终候选或发现冲突时升级100%。",
            "false",
            "false",
        )
    if priority.startswith("P2-"):
        return (
            "H2-自动官网核验后人工确认",
            "优先自动复跑高校官网/章程辅证，人工确认费用、校区、特殊要求和调剂风险。",
            "false",
            "false",
        )
    if auto_route.startswith(("A1-", "A2-")):
        return (
            "H3-自动核验加低风险抽检",
            "自动官网 double check 后按学校、页列和字段分层抽检；出现异常即升级同校或同页列100%。",
            "false",
            "true",
        )
    return (
        "H4-低风险抽检",
        "保留为后备线索；进入候选讨论前仍需PDF原页和湖北官方系统核验。",
        "false",
        "true",
    )


def automatic_next_step(auto_route):
    if auto_route.startswith("A0-"):
        return "优先复跑已有高校官网结构化源，定位专业名、计划数、学费或选科冲突，再回看PDF原页。"
    if auto_route.startswith("A1-"):
        return "复跑已有高校官网/API/PDF/XLSX源，与OCR专业名、计划数、学费、选科字段自动比对。"
    if auto_route.startswith("A2-"):
        return "补抓或解析已有部分高校来源，先转成一行一个专业的结构化辅证表。"
    if auto_route.startswith("A3-"):
        return "章程只用于核录取规则、体检、语种、收费口径；不得用于替代招生计划数。"
    if auto_route.startswith("A4-"):
        return "继续按学校官网招生计划、招生章程、附件PDF/XLSX和新闻页自动检索。"
    return "暂不消耗人工做官网核验；待进入候选或抽检批次后再补高校来源。"


def manual_next_step(priority):
    if priority.startswith("P0-"):
        return "先人工核PDF原页和同组边界；若高校官网/湖北官方字段冲突，按省招办材料优先并记录差异。"
    if priority.startswith("P1-"):
        return "按全19批页列Overlay补三字段候选，补齐后再做PDF原页、湖北官方、高校辅证三方一致性判断。"
    if priority.startswith("P2-"):
        return "结合家庭底线确认公办/费用/专业可接受性，再核完整专业组调剂范围。"
    return "只做分层抽检；一旦进入候选讨论、发现字段异常或同组含硬风险，立即升级。"


def main():
    master_rows = read_csv(MASTER_WORKBENCH)
    stability_by_major = index_by(read_csv(STABILITY_DASHBOARD), "专业行ID")
    decision_by_major = index_by(read_csv(DECISION_GATES), "专业行ID")
    field_by_major = index_by(read_csv(FIELD_FACT_LEDGER), "专业行ID")
    diff_by_major = index_by(read_csv(B0_B1_DIFF_LEDGER), "专业行ID")
    historical_by_major = index_by(read_csv(HISTORICAL_SIDECAR), "专业行ID")

    rows = []
    missing_join_counts = Counter()
    for master in master_rows:
        major_id = master.get("专业行ID", "")
        stability = stability_by_major.get(major_id, {})
        decision = decision_by_major.get(major_id, {})
        field = field_by_major.get(major_id, {})
        diff = diff_by_major.get(major_id, {})
        historical = historical_by_major.get(major_id, {})
        for name, joined in [
            ("底座稳定性总看板", stability),
            ("逐专业决策闸门表", decision),
            ("字段事实闭环总账", field),
            ("三年投档线索旁挂表", historical),
        ]:
            if not joined:
                missing_join_counts[name] += 1

        evidence_id, evidence_note = evidence_level(master, diff)
        route = automatic_route(master)
        priority = manual_priority(master, stability, decision, field, diff)
        strength, scope, must_100, low_risk_sample = manual_strength(priority, route)
        triggers = build_triggers(master, stability, decision, field, diff, evidence_id)

        can_discuss = "false"
        can_final = "false"
        cannot_enter_reason = ordered_join([
            "PDF原页未人工闭环",
            "湖北官方系统或省招办计划未闭环",
            "完整专业组调剂范围未人工确认",
            "家庭接受度未确认",
        ])

        row = {
            "逐专业证据路由ID": stable_id("MAJOREVIDROUTE", [SOURCE_PDF_SHA256, major_id]),
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源底座稳定性总看板": "data/working/issue19-foundation-stability-dashboard.csv",
            "来源逐专业决策闸门表": "data/working/issue19-major-decision-readiness-gates.csv",
            "来源字段事实闭环总账": "data/working/issue19-field-fact-closure-ledger.csv",
            "来源B0B1高校官网差异账": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
            "来源三年投档线索旁挂表": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "专业行ID": major_id,
            "专业组出现ID": master.get("专业组出现ID", ""),
            "院校代码": master.get("院校代码", ""),
            "院校名称OCR": master.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": master.get("院校专业组代码OCR规范化", ""),
            "来源页码": master.get("来源页码", ""),
            "版面列": master.get("版面列", ""),
            "专业组内专业序号": master.get("专业组内专业序号", ""),
            "专业代号OCR": master.get("专业代号OCR", ""),
            "专业名称及备注短摘": master.get("专业名称及备注短摘", ""),
            "是否真实招生明细": master.get("是否真实招生明细", ""),
            "省招办证据等级": evidence_id,
            "证据等级说明": evidence_note,
            "底座稳定性等级": stability.get("底座稳定性等级", master.get("稳定性分层", "")),
            "决策闸门状态": decision.get("候选初筛闸门状态", master.get("候选初筛闸门状态", "")),
            "字段事实闭环等级": field.get("字段事实闭环等级", ""),
            "字段事实阻断等级": field.get("字段事实阻断等级", ""),
            "字段缺口数": master.get("字段缺口数", ""),
            "字段缺口字段": master.get("字段缺口字段", ""),
            "三字段OCR完整状态": field.get("三字段OCR完整状态", ""),
            "PDF原页核验状态": master.get("PDF原页证据状态", master.get("必须人工核PDF原页", "")),
            "湖北官方系统核验状态": master.get("湖北官方平台字段核验状态", master.get("湖北官方系统证据状态", "")),
            "高校官网来源状态": master.get("高校官网来源状态", ""),
            "高校官网证据匹配状态": master.get("高校官网证据匹配状态", ""),
            "高校官网计划数核验状态": master.get("高校官网计划数核验状态", ""),
            "高校官网能否替代湖北官方计划": master.get("官网证据能否替代湖北官方计划", "false"),
            "官网差异账是否命中": "true" if diff else "false",
            "官网差异字段集合": diff.get("差异字段集合", ""),
            "自动官网核验可执行性": route,
            "人工核验优先级": priority,
            "人工核验强度": strength,
            "人工核验范围": scope,
            "是否必须100%人工核验": must_100,
            "是否可低风险抽检": low_risk_sample,
            "升级触发器集合": triggers,
            "学校所在地/校区核验状态": decision.get("城市字段状态", "学校所在地和实际校区待核"),
            "家庭接受度核验状态": master.get("家庭接受度核验状态", ""),
            "同组调剂结论": master.get("同组调剂结论", ""),
            "同组真实招生明细数": master.get("同组真实招生明细数", ""),
            "同组医学护理排除专业数": master.get("同组医学护理排除专业数", ""),
            "同组高收费或超预算专业数": master.get("同组高收费或超预算专业数", ""),
            "同组特殊限制待核专业数": master.get("同组特殊限制待核专业数", ""),
            "专业偏好方向": master.get("专业偏好方向", ""),
            "专业风险类型": master.get("专业风险类型", ""),
            "机器专业接受度初判": master.get("机器专业接受度初判", ""),
            "调剂影响等级": master.get("调剂影响等级", ""),
            "三年投档稳定性状态": historical.get("稳定性分层", master.get("三年投档稳定性状态", "")),
            "同代码命中年份数": historical.get("同代码命中年份数", master.get("同代码命中年份数", "")),
            "历史线使用口径": historical.get("历史线使用口径", master.get("历史线使用口径", "")),
            "可否进入候选讨论": can_discuss,
            "可否进入最终志愿方案": can_final,
            "自动官网核验下一步": automatic_next_step(route),
            "人工核验下一步": manual_next_step(priority),
            "不得进入原因": cannot_enter_reason,
            "下一步": "先按人工核验优先级压缩复核面；进入最终候选前必须回到PDF原页、湖北官方系统或省招办计划、招生章程和家庭底线闭环。",
        }
        rows.append(row)

    write_csv(OUTPUT, rows, FIELDS)

    summary = {
        "status": "issue19_major_evidence_level_routing_not_final",
        "generated_by": Path(__file__).name,
        "output_table": "data/working/issue19-major-evidence-level-routing.csv",
        "source_master_workbench": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_foundation_stability_dashboard": "data/working/issue19-foundation-stability-dashboard.csv",
        "source_decision_gates": "data/working/issue19-major-decision-readiness-gates.csv",
        "source_field_fact_ledger": "data/working/issue19-field-fact-closure-ledger.csv",
        "source_b0_b1_diff_ledger": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
        "source_historical_sidecar": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_route_id_count": len({row["逐专业证据路由ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in rows if row["专业组出现ID"]}),
        "unique_school_code_name_count": len({
            (row["院校代码"], row["院校名称OCR"])
            for row in rows
            if row["院校代码"] or row["院校名称OCR"]
        }),
        "missing_join_counts": dict(missing_join_counts),
        "evidence_level_counts": dict(Counter(row["省招办证据等级"] for row in rows)),
        "automatic_route_counts": dict(Counter(row["自动官网核验可执行性"] for row in rows)),
        "manual_priority_counts": dict(Counter(row["人工核验优先级"] for row in rows)),
        "manual_strength_counts": dict(Counter(row["人工核验强度"] for row in rows)),
        "must_100_percent_manual_review_count": sum(row["是否必须100%人工核验"] == "true" for row in rows),
        "low_risk_sampling_allowed_count": sum(row["是否可低风险抽检"] == "true" for row in rows),
        "school_official_diff_hit_count": sum(row["官网差异账是否命中"] == "true" for row in rows),
        "reusable_school_auto_check_target_count": sum(
            row["自动官网核验可执行性"].startswith(("A0-", "A1-", "A2-"))
            for row in rows
        ),
        "pdf_page_review_required_count": len(rows),
        "hubei_official_review_required_count": len(rows),
        "family_acceptance_review_required_count": len(rows),
        "transfer_decision_review_required_count": len(rows),
        "candidate_discussion_allowed_count": sum(row["可否进入候选讨论"] == "true" for row in rows),
        "final_plan_allowed_count": sum(row["可否进入最终志愿方案"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "policy": {
            "official_system_unavailable_fallback": "官方结构化计划暂不可公开自动取得时，第19期PDF原页是省招办原件层，高校官网只做自动 double check 和冲突发现。",
            "manual_review_compression": "P0 100%人工核验；P1 按页列集中核；P2 自动官网核验后人工确认家庭/费用/调剂；P3 低风险抽检，异常即升级同页列/同校/同组100%。",
            "final_candidate_rule": "任何最终候选院校专业组必须完整核该专业组全部专业、调剂范围、学费、校区、选科和特殊要求，不能只看拟填的6个专业。",
        },
        "notes": [
            "本表一行一个招生专业明细，用于把官方不可得时的自动 double check 和人工核验优先级落到每条明细。",
            "本表不确认任何字段值，不自动写回主表，不生成学校专业建议。",
            "高校官网、千问高考等第三方或学校侧来源只作辅证和发现冲突；最终仍以省招办渠道和志愿系统为准。",
        ],
    }
    write_json(SUMMARY_OUTPUT, summary)


if __name__ == "__main__":
    main()
