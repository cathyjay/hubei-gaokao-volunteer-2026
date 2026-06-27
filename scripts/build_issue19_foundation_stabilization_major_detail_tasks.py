#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

STABILITY_DASHBOARD = ROOT / "data/working/issue19-foundation-stability-dashboard.csv"
GAP_SCORECARD = ROOT / "data/working/issue19-foundation-closure-gap-scorecard.csv"
FIELD_GAP_CANDIDATES = ROOT / "data/working/issue19-field-gap-repair-candidates.csv"
B0_B1_DIFF_LEDGER = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
UNMATCHED_SCHOOL_RESOLUTION = ROOT / "data/working/issue19-moe-unmatched-school-resolution-major-detail.csv"
STRUCTURAL_RISK_LEDGER = ROOT / "data/working/issue19-structural-risk-major-line-ledger.csv"
OFFICIAL_QUERY_KEY_COLLISIONS = ROOT / "data/working/issue19-hubei-official-query-key-collision-ledger.csv"
PDF_EVIDENCE_ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
HISTORICAL_TOUDANG_SIDECAR = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar.csv"

OUTPUT = ROOT / "data/working/issue19-foundation-stabilization-major-detail-tasks.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-foundation-stabilization-major-detail-tasks-summary.json"

DATA_STAGE = "issue19_foundation_stabilization_major_detail_tasks"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
INCLUDED_STABILITY_LEVELS = {
    "B0-校名/结构/官方查询键强阻断",
    "B1-P0原页或官网冲突优先",
    "B2-字段缺口补证优先",
}

FIELDS = [
    "稳定化逐专业任务ID",
    "来源底座稳定性总看板",
    "来源闭环缺口看板",
    "来源字段缺口候选表",
    "来源高校官网差异账",
    "来源未匹配校名逐专业解析表",
    "来源结构风险账本",
    "来源官方查询键碰撞清单",
    "来源专业行原页证据锚点表",
    "来源三年投档线索旁挂表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "专业行ID",
    "底座稳定性看板ID",
    "闭环缺口看板ID",
    "未匹配校名解析ID",
    "公开官网差异账ID集合",
    "字段候选任务ID集合",
    "结构风险账本ID集合",
    "官方查询键碰撞ID集合",
    "专业行原页证据锚点ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "底座稳定性等级",
    "任务优先级",
    "看板动作桶",
    "闭环执行批次",
    "风险阻断等级",
    "任务类型集合",
    "第一核验动作",
    "逐专业保真状态",
    "保真证据链",
    "保真校验规则集合",
    "需要双重佐证字段",
    "字段缺口数",
    "字段缺口字段",
    "字段候选任务数",
    "非空字段候选数",
    "字段候选字段集合",
    "字段候选状态分布",
    "字段候选来源类型集合",
    "字段候选值短摘",
    "B0B1官网差异任务数",
    "官网计划数核验状态集合",
    "官网差异字段集合",
    "官网差异下一步集合",
    "结构风险事件数",
    "最高结构风险等级",
    "结构风险类型集合",
    "湖北官方查询键是否碰撞",
    "湖北官方平台字段核验状态",
    "教育部匹配状态",
    "教育部属性闸门等级",
    "未匹配校名候选综合等级",
    "历史同代码校名候选",
    "教育部相似校名候选",
    "OCR规则修正候选",
    "机器能否自动替换校名",
    "公办民办机器线索",
    "中外合作/港澳合作机器线索",
    "职业本科名称线索",
    "家庭底线属性动作",
    "家庭接受度结论",
    "同组调剂结论",
    "调剂影响等级",
    "三年投档稳定性状态",
    "同代码命中年份数",
    "PDF原页锚点状态",
    "PDF字段核验状态",
    "原页证据窗口SHA256",
    "三年投档旁挂ID",
    "阻断原因集合",
    "今晚自动增强动作",
    "必须人工或官方闭环动作",
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
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def sorted_join(values):
    cleaned = sorted({str(value).strip() for value in values if str(value).strip()})
    return "；".join(cleaned)


def ordered_join(values):
    seen = set()
    result = []
    for value in values:
        cleaned = str(value or "").strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return "；".join(result)


def index_by(rows, key):
    return {row.get(key, ""): row for row in rows if row.get(key, "")}


def group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.get(key, "")].append(row)
    return grouped


def distribution(rows, field):
    return sorted_join(
        f"{key}:{value}"
        for key, value in sorted(Counter(row.get(field, "") or "空值" for row in rows).items())
    )


def short_values(values, limit=6):
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    if not cleaned:
        return ""
    unique = []
    seen = set()
    for value in cleaned:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    sample = unique[:limit]
    if len(unique) > limit:
        sample.append(f"另{len(unique) - limit}项")
    return "；".join(sample)


def task_priority(row):
    level = row.get("底座稳定性等级", "")
    action = row.get("看板动作桶", "")
    if level.startswith("B0"):
        return "P0-强阻断逐专业核验"
    if level.startswith("B1") or action.startswith("S0") or action.startswith("S1"):
        return "P0-原页或官网冲突逐专业核验"
    if level.startswith("B2"):
        return "P1-字段缺口逐专业补证"
    return "P2-常规抽检"


def task_types(stability_row, field_rows, diff_rows, unmatched_row, structural_rows, collision_rows):
    types = ["湖北官方计划逐专业核验", "PDF原页逐专业复核", "家庭接受度与同组调剂复核"]
    if field_rows or as_int(stability_row.get("字段缺口数")) > 0:
        types.append("计划数/学费/选科字段缺口补证")
    if diff_rows or as_int(stability_row.get("B0B1官网差异任务数")) > 0:
        types.append("高校官网/章程三方差异核验")
    if unmatched_row:
        types.append("院校全称与属性核名")
    if structural_rows or as_int(stability_row.get("结构风险事件数")) > 0:
        types.append("专业组边界与结构风险核验")
    if collision_rows or stability_row.get("湖北官方查询键是否碰撞") == "true":
        types.append("湖北官方查询键碰撞排查")
    return ordered_join(types)


def first_action(stability_row, field_rows, diff_rows, unmatched_row, structural_rows, collision_rows):
    if unmatched_row:
        return "先核院校全称/代码是否为2026湖北计划真实口径，再核专业明细"
    if collision_rows or stability_row.get("湖北官方查询键是否碰撞") == "true":
        return "先排除湖北官方查询键碰撞，再读取官方专业明细"
    if structural_rows:
        return "先回看PDF原页确认专业组边界、跨列/跨页归属和专业行顺序"
    if diff_rows:
        return "先对照高校官网/章程差异，再以湖北官方系统或省招办计划定稿"
    if field_rows or as_int(stability_row.get("字段缺口数")) > 0:
        return "先补齐计划数、学费、再选科目字段，并保留原页与官方来源证据"
    return "按官方计划、原页、官网/章程顺序完成常规三方闭环"


def double_check_fields(stability_row, field_rows, diff_rows, unmatched_row, structural_rows, collision_rows):
    fields = []
    fields.extend(
        field_name
        for field_name in str(stability_row.get("字段缺口字段", "")).split("；")
        if field_name.strip()
    )
    if diff_rows:
        fields.extend(["专业名称", "专业代号", "专业计划数", "学费", "再选科目"])
    if unmatched_row:
        fields.extend(["院校全称", "院校代码", "办学性质", "校区"])
    if structural_rows:
        fields.extend(["专业组边界", "专业行顺序", "跨页/跨列归属"])
    if collision_rows:
        fields.extend(["官方查询键", "院校专业组代码"])
    fields.extend(["调剂范围", "家庭底线"])
    return sorted_join(fields)


def main():
    stability_rows = read_csv(STABILITY_DASHBOARD)
    gap_rows = read_csv(GAP_SCORECARD)
    field_rows = read_csv(FIELD_GAP_CANDIDATES)
    diff_rows = read_csv(B0_B1_DIFF_LEDGER)
    unmatched_rows = read_csv(UNMATCHED_SCHOOL_RESOLUTION)
    structural_rows = read_csv(STRUCTURAL_RISK_LEDGER)
    collision_rows = read_csv(OFFICIAL_QUERY_KEY_COLLISIONS)
    anchor_rows = read_csv(PDF_EVIDENCE_ANCHORS)
    history_rows = read_csv(HISTORICAL_TOUDANG_SIDECAR)

    gap_by_major_id = index_by(gap_rows, "专业行ID")
    unmatched_by_major_id = index_by(unmatched_rows, "专业行ID")
    anchor_by_major_id = index_by(anchor_rows, "专业行ID")
    history_by_major_id = index_by(history_rows, "专业行ID")
    field_rows_by_major_id = group_by(field_rows, "专业行ID")
    diff_rows_by_major_id = group_by(diff_rows, "专业行ID")
    structural_rows_by_major_id = group_by(structural_rows, "专业行ID")
    collision_rows_by_major_id = group_by(collision_rows, "专业行ID")

    output_rows = []
    for row in stability_rows:
        if row.get("底座稳定性等级") not in INCLUDED_STABILITY_LEVELS:
            continue
        major_id = row.get("专业行ID", "")
        gap_row = gap_by_major_id.get(major_id, {})
        unmatched_row = unmatched_by_major_id.get(major_id, {})
        anchor_row = anchor_by_major_id.get(major_id, {})
        history_row = history_by_major_id.get(major_id, {})
        major_field_rows = field_rows_by_major_id.get(major_id, [])
        major_diff_rows = diff_rows_by_major_id.get(major_id, [])
        major_structural_rows = structural_rows_by_major_id.get(major_id, [])
        major_collision_rows = collision_rows_by_major_id.get(major_id, [])
        priority = task_priority(row)

        output_rows.append({
            "稳定化逐专业任务ID": stable_id("STABILIZEMAJOR", [major_id]),
            "来源底座稳定性总看板": "data/working/issue19-foundation-stability-dashboard.csv",
            "来源闭环缺口看板": "data/working/issue19-foundation-closure-gap-scorecard.csv",
            "来源字段缺口候选表": "data/working/issue19-field-gap-repair-candidates.csv",
            "来源高校官网差异账": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
            "来源未匹配校名逐专业解析表": "data/working/issue19-moe-unmatched-school-resolution-major-detail.csv",
            "来源结构风险账本": "data/working/issue19-structural-risk-major-line-ledger.csv",
            "来源官方查询键碰撞清单": "data/working/issue19-hubei-official-query-key-collision-ledger.csv",
            "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
            "来源三年投档线索旁挂表": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "是否允许作为志愿推荐依据": "false",
            "专业行ID": major_id,
            "底座稳定性看板ID": row.get("底座稳定性看板ID", ""),
            "闭环缺口看板ID": gap_row.get("闭环缺口看板ID", ""),
            "未匹配校名解析ID": unmatched_row.get("未匹配校名解析ID", ""),
            "公开官网差异账ID集合": ordered_join(diff_row.get("公开官网差异账ID", "") for diff_row in major_diff_rows),
            "字段候选任务ID集合": ordered_join(field_row.get("字段候选任务ID", "") for field_row in major_field_rows),
            "结构风险账本ID集合": ordered_join(structural_row.get("结构风险事件ID", "") for structural_row in major_structural_rows),
            "官方查询键碰撞ID集合": ordered_join(collision_row.get("官方查询键碰撞ID", "") for collision_row in major_collision_rows),
            "专业行原页证据锚点ID": anchor_row.get("专业行原页证据锚点ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "专业组内专业序号": row.get("专业组内专业序号", ""),
            "专业代号OCR": row.get("专业代号OCR", ""),
            "专业名称及备注短摘": row.get("专业名称及备注短摘", ""),
            "底座稳定性等级": row.get("底座稳定性等级", ""),
            "任务优先级": priority,
            "看板动作桶": row.get("看板动作桶", ""),
            "闭环执行批次": row.get("闭环执行批次", ""),
            "风险阻断等级": row.get("风险阻断等级", ""),
            "任务类型集合": task_types(
                row, major_field_rows, major_diff_rows, unmatched_row, major_structural_rows, major_collision_rows
            ),
            "第一核验动作": first_action(
                row, major_field_rows, major_diff_rows, unmatched_row, major_structural_rows, major_collision_rows
            ),
            "逐专业保真状态": "待PDF原页、湖北官方计划、官网/章程、家庭接受度和同组调剂全部闭环",
            "保真证据链": "第19期PDF原页证据锚点；湖北官方系统/省招办计划；高校官网或招生章程；教育部学校名单属性；近三年投档线索；家庭底线与调剂接受度",
            "保真校验规则集合": "专业行ID唯一；来源PDF_SHA256一致；候选证据不得自动写回；最终可用=false；可进入下一阶段=false；未闭环前不得用于志愿推荐",
            "需要双重佐证字段": double_check_fields(
                row, major_field_rows, major_diff_rows, unmatched_row, major_structural_rows, major_collision_rows
            ),
            "字段缺口数": row.get("字段缺口数", ""),
            "字段缺口字段": row.get("字段缺口字段", ""),
            "字段候选任务数": str(len(major_field_rows)),
            "非空字段候选数": str(sum(1 for field_row in major_field_rows if field_row.get("候选值"))),
            "字段候选字段集合": sorted_join(field_row.get("字段名", "") for field_row in major_field_rows),
            "字段候选状态分布": distribution(major_field_rows, "候选状态"),
            "字段候选来源类型集合": sorted_join(field_row.get("候选来源类型", "") for field_row in major_field_rows),
            "字段候选值短摘": short_values(field_row.get("候选值", "") for field_row in major_field_rows),
            "B0B1官网差异任务数": str(len(major_diff_rows)),
            "官网计划数核验状态集合": sorted_join(diff_row.get("计划数核验状态", "") for diff_row in major_diff_rows),
            "官网差异字段集合": sorted_join(diff_row.get("差异字段集合", "") for diff_row in major_diff_rows),
            "官网差异下一步集合": short_values(
                (diff_row.get("下一步", "") for diff_row in major_diff_rows),
                limit=3,
            ),
            "结构风险事件数": str(len(major_structural_rows)),
            "最高结构风险等级": row.get("最高结构风险等级", ""),
            "结构风险类型集合": row.get("结构风险类型集合", ""),
            "湖北官方查询键是否碰撞": row.get("湖北官方查询键是否碰撞", ""),
            "湖北官方平台字段核验状态": row.get("湖北官方平台字段核验状态", ""),
            "教育部匹配状态": row.get("教育部匹配状态", ""),
            "教育部属性闸门等级": row.get("教育部属性闸门等级", ""),
            "未匹配校名候选综合等级": unmatched_row.get("候选综合等级", ""),
            "历史同代码校名候选": unmatched_row.get("历史同代码校名候选", ""),
            "教育部相似校名候选": unmatched_row.get("教育部相似校名候选", ""),
            "OCR规则修正候选": unmatched_row.get("OCR规则修正候选", ""),
            "机器能否自动替换校名": unmatched_row.get("机器能否自动替换校名", "false" if unmatched_row else ""),
            "公办民办机器线索": row.get("公办民办机器线索", ""),
            "中外合作/港澳合作机器线索": row.get("中外合作/港澳合作机器线索", ""),
            "职业本科名称线索": row.get("职业本科名称线索", ""),
            "家庭底线属性动作": row.get("家庭底线属性动作", ""),
            "家庭接受度结论": row.get("家庭接受度结论", ""),
            "同组调剂结论": row.get("同组调剂结论", ""),
            "调剂影响等级": row.get("调剂影响等级", ""),
            "三年投档稳定性状态": row.get("三年投档稳定性状态", ""),
            "同代码命中年份数": row.get("同代码命中年份数", ""),
            "PDF原页锚点状态": row.get("PDF原页锚点状态", ""),
            "PDF字段核验状态": row.get("PDF字段核验状态", ""),
            "原页证据窗口SHA256": anchor_row.get("窗口文本SHA256", ""),
            "三年投档旁挂ID": history_row.get("三年投档旁挂ID", ""),
            "阻断原因集合": row.get("阻断原因集合", ""),
            "今晚自动增强动作": row.get("今晚自动增强动作", ""),
            "必须人工或官方闭环动作": row.get("必须人工或官方闭环动作", ""),
            "不得进入原因": row.get("不得进入原因", ""),
            "下一步": row.get("下一步", ""),
        })

    summary = {
        "status": "issue19_foundation_stabilization_major_detail_tasks_not_final",
        "generated_by": "build_issue19_foundation_stabilization_major_detail_tasks.py",
        "output_table": "data/working/issue19-foundation-stabilization-major-detail-tasks.csv",
        "source_stability_dashboard": "data/working/issue19-foundation-stability-dashboard.csv",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_grain": "逐专业招生明细",
        "task_grain": "逐专业招生明细",
        "included_stability_levels": sorted(INCLUDED_STABILITY_LEVELS),
        "row_count": len(output_rows),
        "unique_task_id_count": len({row["稳定化逐专业任务ID"] for row in output_rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in output_rows}),
        "unique_school_code_name_count": len({(row["院校代码"], row["院校名称OCR"]) for row in output_rows}),
        "stability_level_counts": dict(Counter(row["底座稳定性等级"] for row in output_rows)),
        "task_priority_counts": dict(Counter(row["任务优先级"] for row in output_rows)),
        "scorecard_action_bucket_counts": dict(Counter(row["看板动作桶"] for row in output_rows)),
        "foundation_batch_counts": dict(Counter(row["闭环执行批次"] for row in output_rows)),
        "field_gap_major_line_count": sum(1 for row in output_rows if as_int(row["字段缺口数"]) > 0),
        "field_candidate_task_count": sum(as_int(row["字段候选任务数"]) for row in output_rows),
        "non_empty_field_candidate_count": sum(as_int(row["非空字段候选数"]) for row in output_rows),
        "b0_b1_official_diff_major_line_count": sum(1 for row in output_rows if as_int(row["B0B1官网差异任务数"]) > 0),
        "structural_risk_major_line_count": sum(1 for row in output_rows if as_int(row["结构风险事件数"]) > 0),
        "official_query_collision_major_line_count": sum(1 for row in output_rows if row["湖北官方查询键是否碰撞"] == "true"),
        "unmatched_school_resolution_major_line_count": sum(1 for row in output_rows if row["未匹配校名解析ID"]),
        "auto_writeback_allowed_count": sum(1 for row in output_rows if row["机器是否允许自动写回主表"] == "true"),
        "recommendation_basis_allowed_count": sum(1 for row in output_rows if row["是否允许作为志愿推荐依据"] == "true"),
        "final_available_count": sum(1 for row in output_rows if row["最终可用"] == "true"),
        "next_stage_available_count": sum(1 for row in output_rows if row["可进入下一阶段"] == "true"),
        "source_row_counts": {
            "stability_dashboard": len(stability_rows),
            "gap_scorecard": len(gap_rows),
            "field_gap_candidates": len(field_rows),
            "b0_b1_diff_ledger": len(diff_rows),
            "unmatched_school_resolution": len(unmatched_rows),
            "structural_risk_ledger": len(structural_rows),
            "official_query_key_collisions": len(collision_rows),
            "pdf_evidence_anchors": len(anchor_rows),
            "historical_toudang_sidecar": len(history_rows),
        },
        "fidelity_boundary": (
            "本表只把 B0/B1/B2 逐专业明细拆成可执行核验任务；所有行仍为非最终、不可进入下一阶段，"
            "不得作为志愿排序、推荐或报考结论。"
        ),
        "fidelity_methods": [
            "逐专业行ID做主键，不用学校层或专业组层汇总替代明细。",
            "所有候选值只作线索，候选可自动写回主表统一为 false。",
            "每行保留 PDF 原页、湖北官方计划、高校官网/章程、教育部属性、三年投档、家庭调剂六类证据链。",
            "冲突、字段缺口、校名未匹配、结构风险、官方查询键碰撞均保持 pending，闭环前不得进志愿推荐。",
            "摘要计数、行数、主键唯一性和敏感信息扫描纳入 verify_baseline.py 与 CHECKSUMS.sha256。",
        ],
    }
    write_csv(OUTPUT, output_rows, FIELDS)
    write_json(SUMMARY_OUTPUT, summary)


if __name__ == "__main__":
    main()
