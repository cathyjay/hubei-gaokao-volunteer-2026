#!/usr/bin/env python3
import csv
import difflib
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
FOUNDATION_RELEASE = ROOT / "data/working/issue19-major-detail-foundation-release.csv"
DECISION_GATES = ROOT / "data/working/issue19-major-decision-readiness-gates.csv"
GAP_SCORECARD = ROOT / "data/working/issue19-foundation-closure-gap-scorecard.csv"
MOE_ATTRIBUTE = ROOT / "data/working/issue19-moe-school-attribute-major-detail.csv"
MOE_UNMATCHED_SCHOOLS = ROOT / "data/working/issue19-moe-school-attribute-unmatched-schools.csv"
MOE_NORMALIZED = ROOT / "data/working/moe-2025-regular-higher-schools-normalized.csv"
HUBEI_OFFICIAL_PACKETS = ROOT / "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"
B0_B1_DIFF_LEDGER = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
FIELD_GAP_CANDIDATES = ROOT / "data/working/issue19-field-gap-repair-candidates.csv"
STRUCTURAL_RISK_LEDGER = ROOT / "data/working/issue19-structural-risk-major-line-ledger.csv"
OFFICIAL_QUERY_KEY_COLLISIONS = ROOT / "data/working/issue19-hubei-official-query-key-collision-ledger.csv"
PDF_ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
HISTORICAL_SIDEcar = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar.csv"

STABILITY_OUTPUT = ROOT / "data/working/issue19-foundation-stability-dashboard.csv"
STABILITY_SUMMARY_OUTPUT = ROOT / "data/working/issue19-foundation-stability-dashboard-summary.json"
UNMATCHED_RESOLUTION_OUTPUT = ROOT / "data/working/issue19-moe-unmatched-school-resolution-major-detail.csv"
UNMATCHED_RESOLUTION_SUMMARY_OUTPUT = ROOT / "data/working/issue19-moe-unmatched-school-resolution-summary.json"

DATA_STAGE = "issue19_foundation_stability_dashboard"
UNMATCHED_STAGE = "issue19_moe_unmatched_school_resolution_major_detail"

SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"

STABILITY_FIELDS = [
    "底座稳定性看板ID",
    "来源单一逐专业招生明细总工作台",
    "来源统一逐专业底座入口",
    "来源逐专业决策闸门表",
    "来源教育部学校属性逐专业核验表",
    "来源湖北官方系统逐专业核验包",
    "来源高校官网差异账",
    "来源字段缺口候选表",
    "来源结构风险账本",
    "来源官方查询键碰撞清单",
    "来源三年投档线索旁挂表",
    "来源专业行原页证据锚点表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "稳定性用途",
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
    "PDF原页锚点状态",
    "PDF字段核验状态",
    "湖北官方平台字段核验状态",
    "湖北官方查询键是否碰撞",
    "教育部匹配状态",
    "教育部属性闸门等级",
    "公办民办机器线索",
    "中外合作/港澳合作机器线索",
    "职业本科名称线索",
    "家庭底线属性动作",
    "高校官网/章程辅证状态",
    "高校官网证据匹配状态",
    "高校官网计划数核验状态",
    "B0B1官网差异任务数",
    "字段缺口数",
    "字段缺口字段",
    "字段候选任务数",
    "非空字段候选数",
    "结构风险事件数",
    "最高结构风险等级",
    "结构风险类型集合",
    "候选初筛闸门状态",
    "初筛动作桶",
    "闭环执行批次",
    "看板动作桶",
    "风险阻断等级",
    "三年投档稳定性状态",
    "同代码命中年份数",
    "家庭接受度结论",
    "同组调剂结论",
    "调剂影响等级",
    "底座稳定性等级",
    "阻断原因集合",
    "今晚自动增强动作",
    "必须人工或官方闭环动作",
    "不得进入原因",
    "下一步",
]

UNMATCHED_RESOLUTION_FIELDS = [
    "未匹配校名解析ID",
    "来源教育部学校属性逐专业核验表",
    "来源教育部未匹配学校支持清单",
    "来源三年投档线索旁挂表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
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
    "涉及同校名专业明细数",
    "涉及同校名专业组数",
    "同校名来源页码集合",
    "原未匹配疑似风险类型",
    "历史同代码校名候选",
    "历史候选命中年份",
    "教育部相似校名候选",
    "最高教育部相似度",
    "OCR规则修正候选",
    "候选综合等级",
    "机器能否自动替换校名",
    "不得进入原因",
    "下一步核验动作",
]

OCR_REPLACEMENTS = [
    ("財", "财"),
    ("魯", "鲁"),
    ("晉", "晋"),
    ("复且", "复旦"),
    ("特教育", "特殊教育"),
    ("院西", "皖西"),
    ("路阳", "洛阳"),
    ("玫北", "豫北"),
    ("演西", "滇西"),
    ("4淮北", "淮北"),
    ("3安徽", "安徽"),
    ("（", ""),
    ("）", ""),
    ("(", ""),
    (")", ""),
]

SPECIAL_SCOPE_TOKENS = ["陆军", "香港", "北师香港", "网络空间安全学院"]
VOCATIONAL_TOKENS = ["职业大学", "职业技术大学"]
TRUNCATED_NAMES = {
    "北京",
    "上海",
    "山东",
    "湖北",
    "湖南",
    "新疆",
    "广东",
    "江苏",
    "浙江",
    "河南",
    "河北",
    "安徽",
    "四川",
    "重庆",
}


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


def index_by(rows, key):
    indexed = {}
    for row in rows:
        value = row.get(key, "")
        if value:
            indexed[value] = row
    return indexed


def truthy(value):
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def sorted_join(values):
    cleaned = sorted({str(value).strip() for value in values if str(value).strip()})
    return "；".join(cleaned)


def normalize_school_name(value):
    text = str(value or "").strip()
    for old, new in OCR_REPLACEMENTS:
        text = text.replace(old, new)
    text = re.sub(r"^[0-9A-Za-z]+", "", text)
    text = re.sub(r"^[【\[\]（）()省号信公微众北湖高等]+", "", text)
    return re.sub(r"\s+", "", text)


def extract_school_names_from_historical_text(text, moe_names):
    text = str(text or "").strip()
    if not text:
        return []
    hits = [name for name in moe_names if name and name in text]
    if hits:
        return sorted(set(hits), key=lambda name: (-len(name), name))
    cleaned = re.sub(r"第[0-9０-９一二三四五六七八九十]+组.*$", "", text)
    cleaned = normalize_school_name(cleaned)
    return [cleaned] if cleaned else []


def similar_moe_candidates(name, moe_names, limit=5):
    normalized = normalize_school_name(name)
    scored = []
    for candidate in moe_names:
        ratio = difflib.SequenceMatcher(None, normalized, candidate).ratio()
        if ratio >= 0.72:
            scored.append((ratio, candidate))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[:limit]


def manual_resolution_level(name, historical_candidates, similar_candidates):
    if any(token in name for token in SPECIAL_SCOPE_TOKENS):
        return "R0-特殊院校或港澳台主体，教育部普通高校名单可能不覆盖"
    if any(token in name for token in VOCATIONAL_TOKENS):
        return "R1-职业本科/职业大学线索，必须核2026计划和招生章程"
    if name in TRUNCATED_NAMES or len(name) <= 2:
        return "R1-校名截断，优先用历史同代码候选和PDF原页核名"
    if historical_candidates and similar_candidates:
        similar_names = {candidate for _, candidate in similar_candidates}
        if any(candidate in similar_names for candidate in historical_candidates):
            return "R2-历史同代码候选与教育部相似候选交叉命中"
    if historical_candidates:
        return "R2-有历史同代码校名候选，需核2026是否更名或组号沿用"
    if similar_candidates:
        return "R3-仅有教育部相似校名候选，需人工核OCR"
    return "R4-暂无可靠机器候选，必须回看PDF原页和官方系统"


def risk_level_rank(level):
    if "P0" in level or "高" in level or "阻断" in level:
        return 3
    if "P1" in level or "中" in level:
        return 2
    if level:
        return 1
    return 0


def highest_risk(levels):
    levels = [level for level in levels if level]
    if not levels:
        return ""
    return sorted(levels, key=lambda value: (-risk_level_rank(value), value))[0]


def build_indexes():
    master_rows = read_csv(MASTER_WORKBENCH)
    release_rows = read_csv(FOUNDATION_RELEASE)
    decision_rows = read_csv(DECISION_GATES)
    gap_rows = read_csv(GAP_SCORECARD)
    moe_rows = read_csv(MOE_ATTRIBUTE)
    official_rows = read_csv(HUBEI_OFFICIAL_PACKETS)
    diff_rows = read_csv(B0_B1_DIFF_LEDGER)
    field_candidate_rows = read_csv(FIELD_GAP_CANDIDATES)
    structural_rows = read_csv(STRUCTURAL_RISK_LEDGER)
    collision_rows = read_csv(OFFICIAL_QUERY_KEY_COLLISIONS)
    anchor_rows = read_csv(PDF_ANCHORS)
    historical_rows = read_csv(HISTORICAL_SIDEcar)
    unmatched_school_rows = read_csv(MOE_UNMATCHED_SCHOOLS)
    moe_normalized_rows = read_csv(MOE_NORMALIZED)

    field_candidates_by_major = defaultdict(list)
    for row in field_candidate_rows:
        field_candidates_by_major[row.get("专业行ID", "")].append(row)

    structural_by_major = defaultdict(list)
    for row in structural_rows:
        structural_by_major[row.get("专业行ID", "")].append(row)

    collisions_by_major = defaultdict(list)
    for row in collision_rows:
        collisions_by_major[row.get("专业行ID", "")].append(row)

    diff_by_major = index_by(diff_rows, "专业行ID")

    return {
        "master_rows": master_rows,
        "release_by_major": index_by(release_rows, "专业行ID"),
        "decision_by_major": index_by(decision_rows, "专业行ID"),
        "gap_by_major": index_by(gap_rows, "专业行ID"),
        "moe_by_major": index_by(moe_rows, "专业行ID"),
        "official_by_major": index_by(official_rows, "专业行ID"),
        "diff_by_major": diff_by_major,
        "field_candidates_by_major": field_candidates_by_major,
        "structural_by_major": structural_by_major,
        "collisions_by_major": collisions_by_major,
        "anchor_by_major": index_by(anchor_rows, "专业行ID"),
        "historical_by_major": index_by(historical_rows, "专业行ID"),
        "unmatched_school_by_key": {
            (row.get("院校代码", ""), row.get("院校名称OCR", "")): row
            for row in unmatched_school_rows
        },
        "moe_normalized_rows": moe_normalized_rows,
    }


def stability_level(row, moe_row, gap_row, structural_rows, collision_rows):
    if (
        moe_row.get("教育部匹配状态") == "unmatched_needs_school_name_or_special_school_review"
        or collision_rows
        or structural_rows
    ):
        return "B0-校名/结构/官方查询键强阻断"
    if gap_row.get("看板动作桶") in {
        "S0-B0B1冲突+P0原页优先",
        "S1-P0原页+官网辅证同步核",
        "S2-P0原页结构和字段先核",
    }:
        return "B1-P0原页或官网冲突优先"
    if as_int(row.get("字段缺口数")) > 0:
        return "B2-字段缺口补证优先"
    if gap_row.get("看板动作桶") in {"S7-低风险但证据锚点异常抽检", "S8-低风险抽检"}:
        return "B4-低风险抽检但仍非最终"
    return "B3-三方官方闭环待核"


def blocking_reasons(release_row, moe_row, structural_rows, collision_rows):
    reasons = [
        "PDF原页待人工核验",
        "湖北官方系统/省招办计划待核",
        "家庭接受度待核",
        "同组调剂结论待核",
    ]
    if moe_row.get("教育部匹配状态") == "unmatched_needs_school_name_or_special_school_review":
        reasons.append("教育部校名未匹配")
    if moe_row.get("教育部匹配状态") == "parent_school_name_match_location_not_campus":
        reasons.append("父校/校区线索待核")
    if "民办" in moe_row.get("公办民办机器线索", ""):
        reasons.append("民办线索")
    if "合作" in moe_row.get("中外合作/港澳合作机器线索", ""):
        reasons.append("合作办学线索")
    if truthy(moe_row.get("职业本科名称线索")):
        reasons.append("职业本科名称线索")
    if as_int(release_row.get("字段缺口数")) > 0:
        reasons.append("计划/学费/选科字段缺口")
    if structural_rows:
        reasons.append("结构风险待核")
    if collision_rows:
        reasons.append("湖北官方查询键碰撞待消歧")
    if release_row.get("高校官网/章程辅证状态") == "官网专业名匹配但计划数冲突-优先核页":
        reasons.append("高校官网计划数冲突")
    return "；".join(reasons)


def tonight_machine_action(release_row, moe_row, gap_row, structural_rows, collision_rows, field_rows):
    actions = []
    if moe_row.get("教育部匹配状态") == "unmatched_needs_school_name_or_special_school_review":
        actions.append("先用未匹配校名解析表对照历史同代码和教育部相似候选")
    if collision_rows:
        actions.append("官方查询键碰撞行需保留专业行ID和原页位置消歧")
    if structural_rows:
        actions.append("按结构风险账本回看PDF组边界和专业归属")
    if field_rows:
        actions.append("用字段候选表辅助核计划数/学费/再选科目")
    if release_row.get("高校官网/章程辅证状态") != "not_yet_school_source_searched_in_full_workbench":
        actions.append("同步核高校官网辅证但不得替代湖北官方计划")
    if not actions:
        actions.append("进入常规三方闭环或低风险抽检")
    return "；".join(actions)


def manual_actions(release_row, moe_row):
    actions = [
        "人工回看第19期PDF原页",
        "湖北官方系统/省招办计划逐专业核验",
        "高校招生章程或官网复核",
        "家庭接受度与同组调剂结论确认",
    ]
    if moe_row.get("教育部匹配状态") != "exact_school_name_match":
        actions.append("校名/校区/特殊院校性质单独核验")
    if as_int(release_row.get("字段缺口数")) > 0:
        actions.append("补齐计划数/学费/再选科目字段")
    return "；".join(actions)


def build_stability_dashboard(indexes):
    rows = []
    for master in indexes["master_rows"]:
        major_id = master.get("专业行ID", "")
        release = indexes["release_by_major"].get(major_id, {})
        decision = indexes["decision_by_major"].get(major_id, {})
        gap = indexes["gap_by_major"].get(major_id, {})
        moe = indexes["moe_by_major"].get(major_id, {})
        official = indexes["official_by_major"].get(major_id, {})
        diff = indexes["diff_by_major"].get(major_id, {})
        field_rows = indexes["field_candidates_by_major"].get(major_id, [])
        structural_rows = indexes["structural_by_major"].get(major_id, [])
        collision_rows = indexes["collisions_by_major"].get(major_id, [])
        anchor = indexes["anchor_by_major"].get(major_id, {})
        historical = indexes["historical_by_major"].get(major_id, {})
        structural_types = [row.get("结构风险类型", "") for row in structural_rows]
        structural_levels = [row.get("结构风险等级", "") for row in structural_rows]

        rows.append({
            "底座稳定性看板ID": stable_id("STABILITY", [major_id]),
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源统一逐专业底座入口": "data/working/issue19-major-detail-foundation-release.csv",
            "来源逐专业决策闸门表": "data/working/issue19-major-decision-readiness-gates.csv",
            "来源教育部学校属性逐专业核验表": "data/working/issue19-moe-school-attribute-major-detail.csv",
            "来源湖北官方系统逐专业核验包": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
            "来源高校官网差异账": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
            "来源字段缺口候选表": "data/working/issue19-field-gap-repair-candidates.csv",
            "来源结构风险账本": "data/working/issue19-structural-risk-major-line-ledger.csv",
            "来源官方查询键碰撞清单": "data/working/issue19-hubei-official-query-key-collision-ledger.csv",
            "来源三年投档线索旁挂表": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
            "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "稳定性用途": "用于底座核验排序、缺口收敛和风险解释；不得作为最终志愿方案或录取概率结论",
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
            "PDF原页锚点状态": anchor.get("证据锚点状态", release.get("PDF原页证据状态", "")),
            "PDF字段核验状态": release.get("PDF字段核验状态", decision.get("PDF字段核验状态", "")),
            "湖北官方平台字段核验状态": official.get("平台字段核验状态", release.get("湖北官方平台字段核验状态", "")),
            "湖北官方查询键是否碰撞": "true" if collision_rows else "false",
            "教育部匹配状态": moe.get("教育部匹配状态", ""),
            "教育部属性闸门等级": moe.get("属性闸门等级", ""),
            "公办民办机器线索": moe.get("公办民办机器线索", ""),
            "中外合作/港澳合作机器线索": moe.get("中外合作/港澳合作机器线索", ""),
            "职业本科名称线索": moe.get("职业本科名称线索", ""),
            "家庭底线属性动作": moe.get("家庭底线属性动作", ""),
            "高校官网/章程辅证状态": release.get("高校官网/章程辅证状态", diff.get("高校官网/章程辅证状态", "")),
            "高校官网证据匹配状态": release.get("高校官网证据匹配状态", diff.get("官网证据匹配状态", "")),
            "高校官网计划数核验状态": release.get("高校官网计划数核验状态", diff.get("计划数核验状态", "")),
            "B0B1官网差异任务数": release.get("B0B1官网差异任务数", "0"),
            "字段缺口数": release.get("字段缺口数", decision.get("字段缺口数", "")),
            "字段缺口字段": release.get("字段缺口字段", decision.get("字段缺口字段", "")),
            "字段候选任务数": str(len(field_rows)),
            "非空字段候选数": str(sum(1 for row in field_rows if row.get("候选值", ""))),
            "结构风险事件数": str(len(structural_rows)),
            "最高结构风险等级": highest_risk(structural_levels),
            "结构风险类型集合": sorted_join(structural_types),
            "候选初筛闸门状态": decision.get("候选初筛闸门状态", ""),
            "初筛动作桶": decision.get("初筛动作桶", ""),
            "闭环执行批次": gap.get("闭环执行批次", ""),
            "看板动作桶": gap.get("看板动作桶", ""),
            "风险阻断等级": release.get("风险阻断等级", gap.get("风险阻断等级", "")),
            "三年投档稳定性状态": historical.get("三年投档稳定性状态", release.get("三年投档稳定性状态", "")),
            "同代码命中年份数": historical.get("同代码命中年份数", ""),
            "家庭接受度结论": release.get("家庭接受度结论", decision.get("家庭接受度结论", "")),
            "同组调剂结论": release.get("同组调剂结论", decision.get("同组调剂结论", "")),
            "调剂影响等级": release.get("调剂影响等级", decision.get("调剂影响等级", "")),
            "底座稳定性等级": stability_level(release, moe, gap, structural_rows, collision_rows),
            "阻断原因集合": blocking_reasons(release, moe, structural_rows, collision_rows),
            "今晚自动增强动作": tonight_machine_action(release, moe, gap, structural_rows, collision_rows, field_rows),
            "必须人工或官方闭环动作": manual_actions(release, moe),
            "不得进入原因": release.get("不得进入原因", decision.get("不得进入原因", "")),
            "下一步": "按底座稳定性等级、看板动作桶和逐专业证据项继续核PDF原页、湖北官方计划、官网/章程、家庭接受度和调剂范围",
        })
    return rows


def build_unmatched_resolution(indexes):
    moe_names = [row.get("学校名称", "") for row in indexes["moe_normalized_rows"] if row.get("学校名称")]
    moe_name_set = set(moe_names)
    unmatched_major_rows = [
        row
        for row in indexes["moe_by_major"].values()
        if row.get("教育部匹配状态") == "unmatched_needs_school_name_or_special_school_review"
    ]

    historical_candidates_by_major = {}
    historical_years_by_major = {}
    for row in unmatched_major_rows:
        major_id = row.get("专业行ID", "")
        historical = indexes["historical_by_major"].get(major_id, {})
        candidate_counter = Counter()
        year_hits = []
        for year in ["2023", "2024", "2025"]:
            name_text = historical.get(f"{year}院校专业组名称", "")
            candidates = extract_school_names_from_historical_text(name_text, moe_names)
            if candidates:
                year_hits.append(year)
            for candidate in candidates:
                candidate_counter[candidate] += 1
        historical_candidates_by_major[major_id] = [
            name for name, _ in candidate_counter.most_common(5)
        ]
        historical_years_by_major[major_id] = year_hits

    rows = []
    for moe_row in unmatched_major_rows:
        major_id = moe_row.get("专业行ID", "")
        key = (moe_row.get("院校代码", ""), moe_row.get("院校名称OCR", ""))
        support = indexes["unmatched_school_by_key"].get(key, {})
        historical_candidates = historical_candidates_by_major.get(major_id, [])
        similar_candidates = similar_moe_candidates(moe_row.get("院校名称OCR", ""), moe_names)
        corrected = normalize_school_name(moe_row.get("院校名称OCR", ""))
        corrected_candidate = corrected if corrected in moe_name_set else ""
        candidate_level = manual_resolution_level(
            moe_row.get("院校名称OCR", ""),
            historical_candidates,
            similar_candidates,
        )
        rows.append({
            "未匹配校名解析ID": stable_id("UNMATCHEDSCHOOL", [major_id]),
            "来源教育部学校属性逐专业核验表": "data/working/issue19-moe-school-attribute-major-detail.csv",
            "来源教育部未匹配学校支持清单": "data/working/issue19-moe-school-attribute-unmatched-schools.csv",
            "来源三年投档线索旁挂表": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": UNMATCHED_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "专业行ID": major_id,
            "专业组出现ID": moe_row.get("专业组出现ID", ""),
            "院校代码": moe_row.get("院校代码", ""),
            "院校名称OCR": moe_row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": moe_row.get("院校专业组代码OCR规范化", ""),
            "来源页码": moe_row.get("来源页码", ""),
            "版面列": moe_row.get("版面列", ""),
            "专业组内专业序号": moe_row.get("专业组内专业序号", ""),
            "专业代号OCR": moe_row.get("专业代号OCR", ""),
            "专业名称及备注短摘": moe_row.get("专业名称及备注短摘", ""),
            "涉及同校名专业明细数": support.get("涉及专业明细数", ""),
            "涉及同校名专业组数": support.get("涉及专业组数", ""),
            "同校名来源页码集合": support.get("来源页码集合", ""),
            "原未匹配疑似风险类型": support.get("疑似风险类型", ""),
            "历史同代码校名候选": sorted_join(historical_candidates),
            "历史候选命中年份": sorted_join(historical_years_by_major.get(major_id, [])),
            "教育部相似校名候选": "；".join(
                f"{candidate}:{ratio:.2f}" for ratio, candidate in similar_candidates
            ),
            "最高教育部相似度": f"{similar_candidates[0][0]:.2f}" if similar_candidates else "",
            "OCR规则修正候选": corrected_candidate,
            "候选综合等级": candidate_level,
            "机器能否自动替换校名": "false",
            "不得进入原因": "教育部名单未匹配；历史同代码和相似校名只能作为核名线索，不能自动替换2026招生计划校名",
            "下一步核验动作": "回看PDF原页校名，并用湖北官方系统、学校官网或招生章程确认学校全称、性质、校区和2026招生计划口径",
        })
    return rows


def summarize_stability(rows):
    return {
        "status": "issue19_foundation_stability_dashboard_not_final",
        "generated_by": "build_issue19_foundation_stability_dashboard.py",
        "output_table": "data/working/issue19-foundation-stability-dashboard.csv",
        "source_master_workbench": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_foundation_release": "data/working/issue19-major-detail-foundation-release.csv",
        "source_decision_gates": "data/working/issue19-major-decision-readiness-gates.csv",
        "source_moe_attribute": "data/working/issue19-moe-school-attribute-major-detail.csv",
        "source_hubei_official_packets": "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv",
        "source_b0_b1_diff_ledger": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
        "source_field_gap_candidates": "data/working/issue19-field-gap-repair-candidates.csv",
        "source_structural_risk_ledger": "data/working/issue19-structural-risk-major-line-ledger.csv",
        "source_official_query_key_collisions": "data/working/issue19-hubei-official-query-key-collision-ledger.csv",
        "source_historical_sidecar": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
        "source_pdf_anchors": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "row_count": len(rows),
        "unique_stability_id_count": len({row["底座稳定性看板ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in rows}),
        "unique_school_code_name_count": len({(row["院校代码"], row["院校名称OCR"]) for row in rows}),
        "stability_level_counts": dict(Counter(row["底座稳定性等级"] for row in rows)),
        "foundation_batch_counts": dict(Counter(row["闭环执行批次"] for row in rows)),
        "scorecard_action_bucket_counts": dict(Counter(row["看板动作桶"] for row in rows)),
        "moe_match_status_counts": dict(Counter(row["教育部匹配状态"] for row in rows)),
        "official_status_counts": dict(Counter(row["湖北官方平台字段核验状态"] for row in rows)),
        "school_source_status_counts": dict(Counter(row["高校官网/章程辅证状态"] for row in rows)),
        "field_gap_count_distribution": dict(Counter(row["字段缺口数"] for row in rows)),
        "structural_risk_major_line_count": sum(as_int(row["结构风险事件数"]) > 0 for row in rows),
        "official_query_collision_major_line_count": sum(row["湖北官方查询键是否碰撞"] == "true" for row in rows),
        "unmatched_moe_major_line_count": sum(
            row["教育部匹配状态"] == "unmatched_needs_school_name_or_special_school_review"
            for row in rows
        ),
        "b0_b1_diff_major_line_count": sum(as_int(row["B0B1官网差异任务数"]) > 0 for row in rows),
        "pdf_anchor_status_counts": dict(Counter(row["PDF原页锚点状态"] for row in rows)),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "notes": [
            "本表一行一个招生专业明细，是今晚排核验顺序和解释底座缺口的总看板，不是最终志愿方案。",
            "所有行仍需 PDF 原页、湖北官方系统/省招办计划、高校官网/章程、家庭接受度和同组调剂结论闭环。",
            "底座稳定性等级只说明先核什么，不生成填报建议或录取概率。",
        ],
    }


def summarize_unmatched(rows):
    return {
        "status": "issue19_moe_unmatched_school_resolution_major_detail_not_final",
        "generated_by": "build_issue19_foundation_stability_dashboard.py",
        "output_table": "data/working/issue19-moe-unmatched-school-resolution-major-detail.csv",
        "source_moe_attribute": "data/working/issue19-moe-school-attribute-major-detail.csv",
        "source_moe_unmatched_schools": "data/working/issue19-moe-school-attribute-unmatched-schools.csv",
        "source_historical_sidecar": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
        "row_count": len(rows),
        "unique_resolution_id_count": len({row["未匹配校名解析ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_school_code_name_count": len({(row["院校代码"], row["院校名称OCR"]) for row in rows}),
        "candidate_level_counts": dict(Counter(row["候选综合等级"] for row in rows)),
        "historical_candidate_major_line_count": sum(bool(row["历史同代码校名候选"]) for row in rows),
        "similar_moe_candidate_major_line_count": sum(bool(row["教育部相似校名候选"]) for row in rows),
        "ocr_rule_candidate_major_line_count": sum(bool(row["OCR规则修正候选"]) for row in rows),
        "auto_replace_allowed_count": sum(row["机器能否自动替换校名"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "notes": [
            "本表把教育部未匹配校名下沉到逐专业招生明细；历史同代码和相似校名只作核名线索。",
            "机器能否自动替换校名全部为 false；任何校名修正都必须回看 PDF 原页、湖北官方系统和学校官网/章程。",
            "特殊院校、港澳台主体、职业本科/职业大学、新设或更名线索均保持 pending。",
        ],
    }


def main():
    indexes = build_indexes()
    stability_rows = build_stability_dashboard(indexes)
    unmatched_rows = build_unmatched_resolution(indexes)
    write_csv(STABILITY_OUTPUT, stability_rows, STABILITY_FIELDS)
    write_json(STABILITY_SUMMARY_OUTPUT, summarize_stability(stability_rows))
    write_csv(UNMATCHED_RESOLUTION_OUTPUT, unmatched_rows, UNMATCHED_RESOLUTION_FIELDS)
    write_json(UNMATCHED_RESOLUTION_SUMMARY_OUTPUT, summarize_unmatched(unmatched_rows))
    print(f"wrote {STABILITY_OUTPUT.relative_to(ROOT)} ({len(stability_rows)} rows)")
    print(f"wrote {UNMATCHED_RESOLUTION_OUTPUT.relative_to(ROOT)} ({len(unmatched_rows)} rows)")


if __name__ == "__main__":
    main()
