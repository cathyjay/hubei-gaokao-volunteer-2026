#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RAW_MAJOR_DRAFT = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
QUALITY_WORKBENCH = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"
FOUNDATION_RELEASE = ROOT / "data/working/issue19-major-detail-foundation-release.csv"
MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
STRUCTURAL_REGISTER = ROOT / "data/working/issue19-admission-detail-structural-fidelity-register.csv"
STABILITY_DASHBOARD = ROOT / "data/working/issue19-foundation-stability-dashboard.csv"
PDF_ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
HISTORICAL_SIDECAR = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar.csv"
GAP_SCORECARD = ROOT / "data/working/issue19-foundation-closure-gap-scorecard.csv"
FIELD_GAP_CANDIDATES = ROOT / "data/working/issue19-field-gap-repair-candidates.csv"
STRUCTURAL_RISK_LEDGER = ROOT / "data/working/issue19-structural-risk-major-line-ledger.csv"
OFFICIAL_QUERY_COLLISIONS = ROOT / "data/working/issue19-hubei-official-query-key-collision-ledger.csv"

OUTPUT = ROOT / "data/working/issue19-raw-major-lineage-consistency-audit.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-raw-major-lineage-consistency-audit-summary.json"

DATA_STAGE = "issue19_raw_major_lineage_consistency_audit"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"

RAW_TO_QUALITY_FIELDS = [
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "专业组号OCR",
    "专业组标题OCR原文",
    "来源页码",
    "版面列",
    "专业组标题行号",
    "专业组标题y",
    "专业起始行号",
    "专业起始y",
    "专业代号OCR",
    "专业名称及备注OCR",
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "专业计划数OCR数字候选",
    "专业计划数是否纯数字",
    "学费OCR候选",
    "学费OCR数字候选",
    "学费是否纯数字",
    "OCR置信度",
]

QUALITY_TO_FOUNDATION_FIELDS = [
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR",
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "学费OCR候选",
]

FOUNDATION_TO_MASTER_FIELDS = [
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR",
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "学费OCR候选",
    "字段缺口数",
    "字段缺口字段",
]

QUALITY_TO_ANCHOR_FIELDS = [
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业组标题行号",
    "专业组标题y",
    "专业起始行号",
    "专业起始y",
]

MASTER_TO_STABILITY_FIELDS = [
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "字段缺口数",
    "字段缺口字段",
    "三年投档稳定性状态",
]

FOUNDATION_TO_HISTORY_FIELDS = [
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
]

FIELDS = [
    "原始专业行血缘审计ID",
    "来源全量专业明细OCR初稿",
    "来源逐专业质量工作台",
    "来源统一逐专业底座入口",
    "来源单一逐专业招生明细总工作台",
    "来源结构保真登记表",
    "来源底座稳定性总看板",
    "来源专业行原页证据锚点表",
    "来源三年投档线索旁挂表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "专业行ID",
    "原始CSV数据行号",
    "专业明细源行号",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "专业组号OCR",
    "专业组标题OCR原文",
    "来源页码",
    "版面列",
    "专业组标题行号",
    "专业组标题y",
    "专业组内专业序号",
    "专业起始行号",
    "专业起始y",
    "专业代号OCR",
    "专业名称及备注OCR",
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "专业计划数OCR数字候选",
    "专业计划数是否纯数字",
    "学费OCR候选",
    "学费OCR数字候选",
    "学费是否纯数字",
    "OCR置信度",
    "原始字段完整性标记",
    "原始核验状态",
    "原始到质量工作台匹配状态",
    "质量到统一底座匹配状态",
    "统一底座到总工作台匹配状态",
    "总工作台到结构保真匹配状态",
    "总工作台到底座稳定性匹配状态",
    "质量到原页锚点匹配状态",
    "统一底座到三年投档旁挂匹配状态",
    "闭环缺口看板匹配状态",
    "原始到质量核心字段漂移数",
    "原始到质量漂移字段",
    "质量到底座核心字段漂移数",
    "质量到底座漂移字段",
    "底座到总工作台核心字段漂移数",
    "底座到总工作台漂移字段",
    "质量到原页锚点核心字段漂移数",
    "质量到原页锚点漂移字段",
    "总工作台到底座稳定性核心字段漂移数",
    "总工作台到底座稳定性漂移字段",
    "底座到三年投档旁挂核心字段漂移数",
    "底座到三年投档旁挂漂移字段",
    "全链路核心字段漂移数",
    "全链路核心字段漂移字段",
    "字段缺口数",
    "字段缺口字段",
    "字段候选任务数",
    "非空字段候选数",
    "结构风险事件数",
    "最高结构风险等级",
    "结构风险类型集合",
    "结构保真风险标签",
    "底座稳定性等级",
    "看板动作桶",
    "风险阻断等级",
    "湖北官方查询键是否碰撞",
    "官方查询键碰撞事件数",
    "PDF原页锚点状态",
    "PDF字段核验状态",
    "专业行原页证据锚点ID",
    "专业窗口行号范围",
    "合并证据窗口行号范围",
    "窗口文本SHA256",
    "起始行回连状态",
    "起始行专业代号匹配",
    "三年投档旁挂ID",
    "三年投档稳定性状态",
    "同代码命中年份数",
    "三年再选要求规范集合",
    "再选要求是否跨年变化",
    "历史院校专业组名称是否疑似不一致",
    "2026同代码专业组是否重复出现",
    "血缘审计结论",
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


def split_cn_semicolon(value):
    return [part.strip() for part in str(value or "").split("；") if part.strip()]


def ordered_join(values):
    seen = set()
    result = []
    for value in values:
        cleaned = str(value or "").strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return "；".join(result)


def sorted_join(values):
    return "；".join(sorted({str(value).strip() for value in values if str(value).strip()}))


def by_major_id(rows):
    return {row.get("专业行ID", ""): row for row in rows if row.get("专业行ID", "")}


def group_by_major_id(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.get("专业行ID", "")].append(row)
    return grouped


def compare_fields(left, right, fields):
    drift = []
    for field in fields:
        if str(left.get(field, "")) != str(right.get(field, "")):
            drift.append(field)
    return drift


def match_status(row):
    return "matched" if row else "missing"


def short_status(row):
    return "已回连" if row else "缺失"


def audit_conclusion(
    missing_count,
    total_drift_count,
    source_line_ok,
    all_blocked,
):
    if not source_line_ok:
        return "A3-源行号异常"
    if missing_count:
        return "A2-链路缺失"
    if total_drift_count:
        return "A1-全链路回连但有核心字段漂移"
    if all_blocked:
        return "A0-全链路一一回连且核心OCR字段一致"
    return "A4-门禁状态异常"


def build_rows():
    raw_rows = read_csv(RAW_MAJOR_DRAFT)
    quality_rows = read_csv(QUALITY_WORKBENCH)
    foundation_rows = read_csv(FOUNDATION_RELEASE)
    master_rows = read_csv(MASTER_WORKBENCH)
    structural_rows = read_csv(STRUCTURAL_REGISTER)
    stability_rows = read_csv(STABILITY_DASHBOARD)
    anchor_rows = read_csv(PDF_ANCHORS)
    history_rows = read_csv(HISTORICAL_SIDECAR)
    gap_rows = read_csv(GAP_SCORECARD)
    field_candidate_rows = read_csv(FIELD_GAP_CANDIDATES)
    structural_risk_rows = read_csv(STRUCTURAL_RISK_LEDGER)
    official_collision_rows = read_csv(OFFICIAL_QUERY_COLLISIONS)

    quality_by_raw_line = {
        as_int(row.get("专业明细源行号")) - 1: row for row in quality_rows
    }
    foundation_by_id = by_major_id(foundation_rows)
    master_by_id = by_major_id(master_rows)
    structural_by_id = by_major_id(structural_rows)
    stability_by_id = by_major_id(stability_rows)
    anchor_by_id = by_major_id(anchor_rows)
    history_by_id = by_major_id(history_rows)
    gap_by_id = by_major_id(gap_rows)
    field_candidates_by_id = group_by_major_id(field_candidate_rows)
    structural_risks_by_id = group_by_major_id(structural_risk_rows)
    official_collisions_by_id = group_by_major_id(official_collision_rows)

    rows = []
    for raw_index, raw_row in enumerate(raw_rows, start=1):
        quality_row = quality_by_raw_line.get(raw_index)
        major_id = quality_row.get("专业行ID", "") if quality_row else ""
        foundation_row = foundation_by_id.get(major_id, {})
        master_row = master_by_id.get(major_id, {})
        structural_row = structural_by_id.get(major_id, {})
        stability_row = stability_by_id.get(major_id, {})
        anchor_row = anchor_by_id.get(major_id, {})
        history_row = history_by_id.get(major_id, {})
        gap_row = gap_by_id.get(major_id, {})
        field_rows = field_candidates_by_id.get(major_id, [])
        risk_rows = structural_risks_by_id.get(major_id, [])
        collision_rows = official_collisions_by_id.get(major_id, [])

        source_line_ok = bool(quality_row) and as_int(quality_row.get("专业明细源行号")) == raw_index + 1
        raw_to_quality_drift = compare_fields(raw_row, quality_row or {}, RAW_TO_QUALITY_FIELDS)
        quality_to_foundation_drift = compare_fields(
            quality_row or {}, foundation_row, QUALITY_TO_FOUNDATION_FIELDS
        )
        foundation_to_master_drift = compare_fields(
            foundation_row, master_row, FOUNDATION_TO_MASTER_FIELDS
        )
        quality_to_anchor_drift = compare_fields(
            quality_row or {}, anchor_row, QUALITY_TO_ANCHOR_FIELDS
        )
        master_to_stability_drift = compare_fields(
            master_row, stability_row, MASTER_TO_STABILITY_FIELDS
        )
        foundation_to_history_drift = compare_fields(
            foundation_row, history_row, FOUNDATION_TO_HISTORY_FIELDS
        )
        all_drift_fields = ordered_join(
            [
                *(f"原始到质量:{field}" for field in raw_to_quality_drift),
                *(f"质量到底座:{field}" for field in quality_to_foundation_drift),
                *(f"底座到总工作台:{field}" for field in foundation_to_master_drift),
                *(f"质量到原页锚点:{field}" for field in quality_to_anchor_drift),
                *(f"总工作台到底座稳定性:{field}" for field in master_to_stability_drift),
                *(f"底座到三年投档旁挂:{field}" for field in foundation_to_history_drift),
            ]
        )
        total_drift_count = (
            len(raw_to_quality_drift)
            + len(quality_to_foundation_drift)
            + len(foundation_to_master_drift)
            + len(quality_to_anchor_drift)
            + len(master_to_stability_drift)
            + len(foundation_to_history_drift)
        )
        linked_rows = [
            quality_row,
            foundation_row,
            master_row,
            structural_row,
            stability_row,
            anchor_row,
            history_row,
            gap_row,
        ]
        missing_count = sum(1 for row in linked_rows if not row)
        all_blocked = (
            bool(quality_row)
            and foundation_row.get("最终可用") == "false"
            and foundation_row.get("是否可进入最终专业列表") == "false"
            and foundation_row.get("可进入下一阶段") == "false"
            and master_row.get("最终可用") == "false"
            and master_row.get("可进入下一阶段") == "false"
            and structural_row.get("最终可用") == "false"
            and structural_row.get("可进入下一阶段") == "false"
            and stability_row.get("最终可用") == "false"
            and stability_row.get("可进入下一阶段") == "false"
            and anchor_row.get("最终可用") == "false"
            and anchor_row.get("可进入下一阶段") == "false"
            and history_row.get("最终可用") == "false"
            and history_row.get("可进入下一阶段") == "false"
        )
        conclusion = audit_conclusion(missing_count, total_drift_count, source_line_ok, all_blocked)
        block_reasons = [
            "本表仅做原始逐专业明细血缘和字段一致性审计",
            "2026招生计划仍需PDF原页、湖北官方系统或省招办计划、高校官网/章程三方闭环",
            "家庭接受度和同组调剂结论未确认",
            "未闭环前不得用于志愿推荐、排序或填报结论",
        ]
        if missing_count:
            block_reasons.append("存在下游链路缺失")
        if total_drift_count:
            block_reasons.append("存在核心字段漂移")
        if not source_line_ok:
            block_reasons.append("原始CSV行号与专业明细源行号未闭合")

        rows.append({
            "原始专业行血缘审计ID": stable_id("RAWLINEAGE", [major_id or raw_index, SOURCE_PDF_SHA256]),
            "来源全量专业明细OCR初稿": "data/working/issue19-full-admission-plan-major-ocr-draft.csv",
            "来源逐专业质量工作台": "data/working/issue19-full-major-detail-quality-workbench.csv",
            "来源统一逐专业底座入口": "data/working/issue19-major-detail-foundation-release.csv",
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源结构保真登记表": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
            "来源底座稳定性总看板": "data/working/issue19-foundation-stability-dashboard.csv",
            "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
            "来源三年投档线索旁挂表": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "是否允许作为志愿推荐依据": "false",
            "专业行ID": major_id,
            "原始CSV数据行号": str(raw_index),
            "专业明细源行号": quality_row.get("专业明细源行号", "") if quality_row else "",
            "专业组出现ID": quality_row.get("专业组出现ID", "") if quality_row else "",
            "院校代码": raw_row.get("院校代码", ""),
            "院校名称OCR": raw_row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": raw_row.get("院校专业组代码OCR规范化", ""),
            "专业组号OCR": raw_row.get("专业组号OCR", ""),
            "专业组标题OCR原文": raw_row.get("专业组标题OCR原文", ""),
            "来源页码": raw_row.get("来源页码", ""),
            "版面列": raw_row.get("版面列", ""),
            "专业组标题行号": raw_row.get("专业组标题行号", ""),
            "专业组标题y": raw_row.get("专业组标题y", ""),
            "专业组内专业序号": quality_row.get("专业组内专业序号", "") if quality_row else "",
            "专业起始行号": raw_row.get("专业起始行号", ""),
            "专业起始y": raw_row.get("专业起始y", ""),
            "专业代号OCR": raw_row.get("专业代号OCR", ""),
            "专业名称及备注OCR": raw_row.get("专业名称及备注OCR", ""),
            "再选科目OCR候选": raw_row.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": raw_row.get("专业计划数OCR候选", ""),
            "专业计划数OCR数字候选": raw_row.get("专业计划数OCR数字候选", ""),
            "专业计划数是否纯数字": raw_row.get("专业计划数是否纯数字", ""),
            "学费OCR候选": raw_row.get("学费OCR候选", ""),
            "学费OCR数字候选": raw_row.get("学费OCR数字候选", ""),
            "学费是否纯数字": raw_row.get("学费是否纯数字", ""),
            "OCR置信度": raw_row.get("OCR置信度", ""),
            "原始字段完整性标记": raw_row.get("字段完整性标记", ""),
            "原始核验状态": raw_row.get("核验状态", ""),
            "原始到质量工作台匹配状态": "已按原始CSV数据行号+专业明细源行号回连" if source_line_ok else "未回连",
            "质量到统一底座匹配状态": short_status(foundation_row),
            "统一底座到总工作台匹配状态": short_status(master_row),
            "总工作台到结构保真匹配状态": short_status(structural_row),
            "总工作台到底座稳定性匹配状态": short_status(stability_row),
            "质量到原页锚点匹配状态": short_status(anchor_row),
            "统一底座到三年投档旁挂匹配状态": short_status(history_row),
            "闭环缺口看板匹配状态": short_status(gap_row),
            "原始到质量核心字段漂移数": str(len(raw_to_quality_drift)),
            "原始到质量漂移字段": "；".join(raw_to_quality_drift),
            "质量到底座核心字段漂移数": str(len(quality_to_foundation_drift)),
            "质量到底座漂移字段": "；".join(quality_to_foundation_drift),
            "底座到总工作台核心字段漂移数": str(len(foundation_to_master_drift)),
            "底座到总工作台漂移字段": "；".join(foundation_to_master_drift),
            "质量到原页锚点核心字段漂移数": str(len(quality_to_anchor_drift)),
            "质量到原页锚点漂移字段": "；".join(quality_to_anchor_drift),
            "总工作台到底座稳定性核心字段漂移数": str(len(master_to_stability_drift)),
            "总工作台到底座稳定性漂移字段": "；".join(master_to_stability_drift),
            "底座到三年投档旁挂核心字段漂移数": str(len(foundation_to_history_drift)),
            "底座到三年投档旁挂漂移字段": "；".join(foundation_to_history_drift),
            "全链路核心字段漂移数": str(total_drift_count),
            "全链路核心字段漂移字段": all_drift_fields,
            "字段缺口数": stability_row.get("字段缺口数", ""),
            "字段缺口字段": stability_row.get("字段缺口字段", ""),
            "字段候选任务数": str(len(field_rows)),
            "非空字段候选数": str(sum(1 for row in field_rows if row.get("候选值"))),
            "结构风险事件数": str(len(risk_rows)),
            "最高结构风险等级": stability_row.get("最高结构风险等级", ""),
            "结构风险类型集合": stability_row.get("结构风险类型集合", ""),
            "结构保真风险标签": structural_row.get("结构保真风险标签", ""),
            "底座稳定性等级": stability_row.get("底座稳定性等级", ""),
            "看板动作桶": stability_row.get("看板动作桶", ""),
            "风险阻断等级": stability_row.get("风险阻断等级", ""),
            "湖北官方查询键是否碰撞": "true" if collision_rows else "false",
            "官方查询键碰撞事件数": str(len(collision_rows)),
            "PDF原页锚点状态": stability_row.get("PDF原页锚点状态", ""),
            "PDF字段核验状态": stability_row.get("PDF字段核验状态", ""),
            "专业行原页证据锚点ID": anchor_row.get("专业行原页证据锚点ID", ""),
            "专业窗口行号范围": anchor_row.get("专业窗口行号范围", ""),
            "合并证据窗口行号范围": anchor_row.get("合并证据窗口行号范围", ""),
            "窗口文本SHA256": anchor_row.get("窗口文本SHA256", ""),
            "起始行回连状态": anchor_row.get("起始行回连状态", ""),
            "起始行专业代号匹配": anchor_row.get("起始行专业代号匹配", ""),
            "三年投档旁挂ID": history_row.get("三年投档旁挂ID", ""),
            "三年投档稳定性状态": history_row.get("稳定性分层", ""),
            "同代码命中年份数": history_row.get("同代码命中年份数", ""),
            "三年再选要求规范集合": history_row.get("三年再选要求规范集合", ""),
            "再选要求是否跨年变化": history_row.get("再选要求是否跨年变化", ""),
            "历史院校专业组名称是否疑似不一致": history_row.get("历史院校专业组名称是否疑似不一致", ""),
            "2026同代码专业组是否重复出现": history_row.get("2026同代码专业组是否重复出现", ""),
            "血缘审计结论": conclusion,
            "不得进入原因": "；".join(block_reasons),
            "下一步": "继续逐专业核PDF原页、湖北官方系统或省招办计划、高校官网/章程证据；闭环前仅作为原始结构化底座审计依据",
        })

    context = {
        "raw_rows": raw_rows,
        "quality_rows": quality_rows,
        "foundation_rows": foundation_rows,
        "master_rows": master_rows,
        "structural_rows": structural_rows,
        "stability_rows": stability_rows,
        "anchor_rows": anchor_rows,
        "history_rows": history_rows,
        "gap_rows": gap_rows,
        "field_candidate_rows": field_candidate_rows,
        "structural_risk_rows": structural_risk_rows,
        "official_collision_rows": official_collision_rows,
    }
    return rows, context


def main():
    rows, context = build_rows()
    write_csv(OUTPUT, rows, FIELDS)

    conclusion_counts = Counter(row.get("血缘审计结论", "") for row in rows)
    stability_level_counts = Counter(row.get("底座稳定性等级", "") for row in rows)
    source_counts = {
        "raw_major_draft_row_count": len(context["raw_rows"]),
        "quality_workbench_row_count": len(context["quality_rows"]),
        "foundation_release_row_count": len(context["foundation_rows"]),
        "master_workbench_row_count": len(context["master_rows"]),
        "structural_register_row_count": len(context["structural_rows"]),
        "stability_dashboard_row_count": len(context["stability_rows"]),
        "pdf_anchor_row_count": len(context["anchor_rows"]),
        "historical_sidecar_row_count": len(context["history_rows"]),
        "gap_scorecard_row_count": len(context["gap_rows"]),
        "field_candidate_task_row_count": len(context["field_candidate_rows"]),
        "structural_risk_event_row_count": len(context["structural_risk_rows"]),
        "official_query_collision_row_count": len(context["official_collision_rows"]),
    }
    summary = {
        "status": "issue19_raw_major_lineage_consistency_audit_not_final",
        "generated_by": Path(__file__).name,
        "source_raw_major_draft": "data/working/issue19-full-admission-plan-major-ocr-draft.csv",
        "source_quality_workbench": "data/working/issue19-full-major-detail-quality-workbench.csv",
        "source_foundation_release": "data/working/issue19-major-detail-foundation-release.csv",
        "source_master_workbench": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_structural_register": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
        "source_stability_dashboard": "data/working/issue19-foundation-stability-dashboard.csv",
        "source_pdf_anchors": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "source_historical_sidecar": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
        "output_table": "data/working/issue19-raw-major-lineage-consistency-audit.csv",
        "row_grain": "逐专业招生明细",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_audit_id_count": len({row.get("原始专业行血缘审计ID") for row in rows}),
        "unique_major_line_id_count": len({row.get("专业行ID") for row in rows if row.get("专业行ID")}),
        "unique_group_occurrence_id_count": len({row.get("专业组出现ID") for row in rows if row.get("专业组出现ID")}),
        "unique_raw_csv_data_line_count": len({row.get("原始CSV数据行号") for row in rows}),
        "source_counts": source_counts,
        "quality_match_count": sum(row.get("原始到质量工作台匹配状态").startswith("已") for row in rows),
        "foundation_match_count": sum(row.get("质量到统一底座匹配状态") == "已回连" for row in rows),
        "master_match_count": sum(row.get("统一底座到总工作台匹配状态") == "已回连" for row in rows),
        "structural_match_count": sum(row.get("总工作台到结构保真匹配状态") == "已回连" for row in rows),
        "stability_match_count": sum(row.get("总工作台到底座稳定性匹配状态") == "已回连" for row in rows),
        "pdf_anchor_match_count": sum(row.get("质量到原页锚点匹配状态") == "已回连" for row in rows),
        "historical_sidecar_match_count": sum(row.get("统一底座到三年投档旁挂匹配状态") == "已回连" for row in rows),
        "gap_scorecard_match_count": sum(row.get("闭环缺口看板匹配状态") == "已回连" for row in rows),
        "core_field_drift_row_count": sum(as_int(row.get("全链路核心字段漂移数")) > 0 for row in rows),
        "core_field_drift_total_count": sum(as_int(row.get("全链路核心字段漂移数")) for row in rows),
        "raw_to_quality_drift_row_count": sum(as_int(row.get("原始到质量核心字段漂移数")) > 0 for row in rows),
        "quality_to_foundation_drift_row_count": sum(as_int(row.get("质量到底座核心字段漂移数")) > 0 for row in rows),
        "foundation_to_master_drift_row_count": sum(as_int(row.get("底座到总工作台核心字段漂移数")) > 0 for row in rows),
        "quality_to_anchor_drift_row_count": sum(as_int(row.get("质量到原页锚点核心字段漂移数")) > 0 for row in rows),
        "master_to_stability_drift_row_count": sum(as_int(row.get("总工作台到底座稳定性核心字段漂移数")) > 0 for row in rows),
        "foundation_to_history_drift_row_count": sum(as_int(row.get("底座到三年投档旁挂核心字段漂移数")) > 0 for row in rows),
        "lineage_conclusion_counts": dict(sorted(conclusion_counts.items())),
        "stability_level_counts": dict(sorted(stability_level_counts.items())),
        "field_candidate_task_count": sum(as_int(row.get("字段候选任务数")) for row in rows),
        "non_empty_field_candidate_count": sum(as_int(row.get("非空字段候选数")) for row in rows),
        "structural_risk_event_count": sum(as_int(row.get("结构风险事件数")) for row in rows),
        "official_query_collision_major_line_count": sum(row.get("湖北官方查询键是否碰撞") == "true" for row in rows),
        "official_query_collision_event_count": sum(as_int(row.get("官方查询键碰撞事件数")) for row in rows),
        "final_available_count": sum(row.get("最终可用") == "true" for row in rows),
        "next_stage_available_count": sum(row.get("可进入下一阶段") == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row.get("机器是否允许自动写回主表") == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row.get("是否允许作为志愿推荐依据") == "true" for row in rows),
        "public_safety_note": "本产物仅含公开安全的逐专业结构化字段、证据锚点ID和哈希；不含私有路径、登录态、个人身份信息、页面图片或OCR全文。",
        "decision_boundary_note": "本产物用于确认原始OCR逐专业明细到底座工作台的结构化血缘；不用于院校专业推荐、志愿排序或最终填报结论。",
    }
    write_json(SUMMARY_OUTPUT, summary)


if __name__ == "__main__":
    main()
