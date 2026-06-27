#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]

MASTER = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
FILTER_PREP = ROOT / "data/working/issue19-candidate-filter-prep-major-detail.csv"
FIELD_FACT = ROOT / "data/working/issue19-field-fact-closure-ledger.csv"
EVIDENCE_ROUTING = ROOT / "data/working/issue19-major-evidence-level-routing.csv"
MOE_ATTRIBUTE = ROOT / "data/working/issue19-moe-school-attribute-major-detail.csv"
HISTORICAL_SIDECAR = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar.csv"
FAMILY_GROUP = ROOT / "data/working/issue19-family-fit-group-screen.csv"
OFFICIAL_PUBLIC_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

MAJOR_OUTPUT = ROOT / "data/working/issue19-stable-foundation-major-screening-view.csv"
GROUP_OUTPUT = ROOT / "data/working/issue19-stable-foundation-group-screening-view.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-stable-foundation-screening-summary.json"

DATA_STAGE_MAJOR = "issue19_stable_foundation_major_screening_view"
DATA_STAGE_GROUP = "issue19_stable_foundation_group_screening_view"

SOURCE_LABELS = {
    "master": "data/working/issue19-admission-detail-master-workbench.csv",
    "filter": "data/working/issue19-candidate-filter-prep-major-detail.csv",
    "field": "data/working/issue19-field-fact-closure-ledger.csv",
    "routing": "data/working/issue19-major-evidence-level-routing.csv",
    "moe": "data/working/issue19-moe-school-attribute-major-detail.csv",
    "historical": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
    "family_group": "data/working/issue19-family-fit-group-screen.csv",
}

FORBIDDEN_TEXT_TOKENS = [
    "/Users/",
    "/private/",
    "private/",
    "private\\",
    "ocr-runs",
    "rendered-pages",
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
    "身份证",
    "准考证",
    "报名号",
    "序列号",
]

MAJOR_FIELDS = [
    "稳定基座逐专业筛选ID",
    "来源单一逐专业招生明细总工作台",
    "来源候选筛选准备表",
    "来源字段事实闭环总账",
    "来源证据等级与核验路由表",
    "来源教育部学校属性旁挂表",
    "来源三年投档线索旁挂表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否可作为机器初筛线索",
    "机器初筛线索等级",
    "初筛用途边界",
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
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "学费OCR候选",
    "字段缺口数",
    "字段缺口字段",
    "三字段OCR完整状态",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "候选初筛闸门状态",
    "初筛动作桶",
    "省招办证据等级",
    "自动官网核验可执行性",
    "人工核验优先级",
    "人工核验强度",
    "是否必须100%人工核验",
    "是否可低风险抽检",
    "PDF原页核验状态",
    "湖北官方系统核验状态",
    "高校官网来源状态",
    "高校官网证据匹配状态",
    "高校官网能否替代湖北官方计划",
    "教育部匹配状态",
    "公办民办机器线索",
    "家庭底线属性动作",
    "属性闸门等级",
    "教育部所在地",
    "教育部所在地命中城市",
    "城市候选",
    "城市字段状态",
    "专业偏好方向",
    "机器专业接受度初判",
    "专业风险类型",
    "是否超预算机器初判",
    "同组真实招生明细数",
    "同组偏好专业数",
    "同组医学护理排除专业数",
    "同组高收费或超预算专业数",
    "同组特殊限制待核专业数",
    "同组调剂结论",
    "同代码命中年份数",
    "同代码命中年份",
    "历史最高等位分差",
    "历史最低等位分差",
    "历史线索分层",
    "三年投档稳定性状态",
    "历史线使用口径",
    "机器核验下一步",
    "人工核验下一步",
    "不得进入原因",
    "下一步",
]

GROUP_FIELDS = [
    "稳定基座专业组筛选ID",
    "来源专业组家庭底线筛选表",
    "来源稳定基座逐专业筛选视图",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否进入机器初筛观察池",
    "机器筛选价值层级",
    "保真核验层级",
    "专业组使用边界",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "专业组号OCR",
    "来源页码",
    "版面列",
    "专业明细行数",
    "无逐专业明细占位",
    "城市候选",
    "教育部所在地命中城市",
    "教育部所在地是否命中城市偏好",
    "公办民办机器线索",
    "家庭底线属性动作",
    "属性闸门等级",
    "机器家庭匹配初判",
    "调剂初判",
    "偏好专业数",
    "数字媒体技术专业数",
    "计算机类相关专业数",
    "师范类相关专业数",
    "医学护理排除专业数",
    "高收费或超预算专业数",
    "特殊限制待核专业数",
    "字段缺口专业行数",
    "三字段OCR齐全专业行数",
    "字段无候选阻断专业行数",
    "结构或归属未闭环专业行数",
    "P0人工核验专业行数",
    "P1人工核验专业行数",
    "P2人工核验专业行数",
    "P3低风险抽检专业行数",
    "必须100%人工核验专业行数",
    "可低风险抽检专业行数",
    "A1官网自动复跑专业行数",
    "A2官网补结构化专业行数",
    "A4官网继续搜索专业行数",
    "湖北官方系统待核专业行数",
    "PDF原页待核专业行数",
    "官网辅证命中专业行数",
    "同代码命中年份最大值",
    "历史最高等位分差",
    "历史最低等位分差",
    "历史线索分层",
    "组内专业行ID集合SHA256",
    "组内完整专业清单索引",
    "机器核验下一步",
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


def by_major_id(rows):
    return {row.get("专业行ID", ""): row for row in rows}


def by_group_id(rows):
    return {row.get("专业组出现ID", ""): row for row in rows}


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def bool_text(condition):
    return "true" if condition else "false"


def parse_diff(value):
    if not value:
        return None
    match = re.search(r"=\s*([+-]?\d+)", str(value))
    if not match:
        return None
    return as_int(match.group(1))


def historical_diffs(row):
    diffs = []
    for year in ["2023", "2024", "2025"]:
        diff = parse_diff(row.get(f"{year}等位分差", ""))
        if diff is not None:
            diffs.append(diff)
    return diffs


def historical_layer(diffs):
    if not diffs:
        return "H0-无同代码历史线索"
    hardest = max(diffs)
    if hardest <= -20:
        return "H1-历史最高线低于等位分20分以上"
    if hardest <= 0:
        return "H2-历史最高线不高于等位分"
    if hardest <= 15:
        return "H3-历史最高线高于等位分15分内"
    if hardest <= 30:
        return "H4-历史最高线高于等位分16-30分"
    return "H5-历史最高线高于等位分30分以上"


def major_signal_level(field_row, filter_row, moe_row):
    gate = field_row.get("候选初筛闸门状态", "")
    action = field_row.get("初筛动作桶", "")
    attribute_gate = moe_row.get("属性闸门等级", "")
    acceptance = filter_row.get("机器专业接受度初判", "")
    if attribute_gate.startswith("G0") or acceptance.startswith("默认不能接受"):
        return "M0-家庭底线或属性风险先排除"
    if gate == "G3-可作机器预筛线索但不可定案":
        return "M1-可作机器预筛线索但不可定案"
    if action in {"D3-偏好专业线索优先核", "D4-城市偏好线索待位置核", "D5-调剂风险先核"}:
        return "M2-有偏好城市或调剂线索需先核"
    if gate == "G4-常规留存但不可定案":
        return "M3-常规留存但不可定案"
    if gate == "G2-字段缺口未闭环":
        return "M4-字段缺口先补"
    if gate == "G0-结构或归属未闭环":
        return "M5-结构归属先核"
    return "M6-仅留存待补证"


def major_next_step(signal_level, route_row, field_row):
    if signal_level.startswith("M0"):
        return "先核公办/民办/合作办学、费用和家庭底线；默认不进入主方案。"
    if route_row.get("人工核验优先级", "").startswith("P0"):
        return "先做P0：核PDF原页结构、专业组归属和关键字段，再看官网辅证。"
    if field_row.get("字段事实阻断等级") == "Q0-字段缺口无候选阻断":
        return "回到原PDF页重读缺口字段，补出候选后再进入筛选视图。"
    if route_row.get("自动官网核验可执行性", "").startswith(("A1", "A2")):
        return "先自动复跑/结构化高校官网来源，再人工确认冲突字段。"
    return "按页列集中核PDF原页、湖北官方计划入口、学校属性、校区和调剂范围。"


def group_value_layer(group_row, majors):
    if not majors:
        return "V5-无逐专业明细先补结构"
    group_fit = group_row.get("机器家庭匹配初判", "")
    attribute_actions = {row.get("家庭底线属性动作", "") for row in majors}
    attribute_gates = {row.get("属性闸门等级", "") for row in majors}
    if (
        group_fit.startswith("默认不进主方案")
        or any(action.startswith("默认不进主方案") for action in attribute_actions)
        or any(gate.startswith("G0") for gate in attribute_gates)
    ):
        return "V0-默认不进主方案风险"
    if as_int(group_row.get("偏好专业数")):
        return "V1-偏好专业优先线索"
    if group_row.get("教育部所在地是否命中城市偏好") == "true" or group_row.get("城市候选"):
        return "V2-城市偏好扩展线索"
    if any(row.get("同代码命中年份数", "0") not in {"", "0"} for row in majors):
        return "V3-历史线索普通留存"
    return "V4-普通留存待了解"


def group_review_layer(majors):
    if not majors:
        return "R0-无明细结构阻断"
    priorities = Counter(row.get("人工核验优先级", "") for row in majors)
    if any(key.startswith("P0") for key in priorities):
        return "R1-P0整组先核"
    if any(key.startswith("P1") for key in priorities):
        return "R2-P1页列集中核"
    if any(key.startswith("P2") for key in priorities):
        return "R3-P2官网后人工确认"
    if any(key.startswith("P3") for key in priorities):
        return "R4-P3低风险抽检"
    return "R5-常规留存"


def group_next_steps(value_layer, review_layer):
    if value_layer == "V5-无逐专业明细先补结构":
        return "先回原PDF页确认该专业组是否有明细、是否跨页或OCR漏拆。", "需要人工定位专业组标题和明细区域。"
    if value_layer.startswith("V0"):
        return "先核家庭底线风险，不把该组放入主方案。", "仅在保底不足或家庭明确可接受时再核整组。"
    if review_layer.startswith("R1"):
        return "按P0优先核PDF原页结构、字段缺口和官网冲突。", "整组所有专业都要核，不能只核拟填6个专业。"
    if review_layer.startswith("R2"):
        return "按页列集中核字段缺口，再接湖北官方计划和高校官网辅证。", "同一页列若发现结构错误，整页列升级核验。"
    if review_layer.startswith("R3"):
        return "先自动核高校官网/章程来源，再人工确认费用、校区、调剂范围。", "官网只作辅证，不能替代湖北省招办计划。"
    return "保留为机器初筛观察池，等官方计划或人工抽检结果后再排序。", "低风险抽检发现异常时升级同页列/同校/同组。"


def main():
    master_rows = read_csv(MASTER)
    filter_rows = by_major_id(read_csv(FILTER_PREP))
    field_rows = by_major_id(read_csv(FIELD_FACT))
    route_rows = by_major_id(read_csv(EVIDENCE_ROUTING))
    moe_rows = by_major_id(read_csv(MOE_ATTRIBUTE))
    hist_rows = by_major_id(read_csv(HISTORICAL_SIDECAR))
    family_group_rows = read_csv(FAMILY_GROUP)

    source_status = json.loads(OFFICIAL_PUBLIC_STATUS.read_text())
    source_pdf_sha256 = source_status["official_plan_page"]["sha256"]
    issue_pdf_sha256 = master_rows[0].get("来源PDF_SHA256", "") if master_rows else ""

    major_output_rows = []
    missing_join_counts = Counter()
    for master in master_rows:
        major_id = master.get("专业行ID", "")
        filter_row = filter_rows.get(major_id, {})
        field_row = field_rows.get(major_id, {})
        route_row = route_rows.get(major_id, {})
        moe_row = moe_rows.get(major_id, {})
        hist_row = hist_rows.get(major_id, {})
        for name, row in [
            ("filter_prep", filter_row),
            ("field_fact", field_row),
            ("evidence_routing", route_row),
            ("moe_attribute", moe_row),
            ("historical_sidecar", hist_row),
        ]:
            if not row:
                missing_join_counts[name] += 1

        diffs = historical_diffs(hist_row)
        signal_level = major_signal_level(field_row, filter_row, moe_row)
        as_machine_signal = signal_level.startswith(("M1", "M2", "M3"))
        next_step = major_next_step(signal_level, route_row, field_row)
        reason = (
            "稳定基座筛选视图仍未完成PDF原页、湖北官方系统/省招办计划、"
            "高校官网/章程、家庭接受度和同组调剂结论闭环；不得用于最终志愿排序。"
        )
        major_output_rows.append({
            "稳定基座逐专业筛选ID": stable_id("STABLEMAJOR", [major_id]),
            "来源单一逐专业招生明细总工作台": SOURCE_LABELS["master"],
            "来源候选筛选准备表": SOURCE_LABELS["filter"],
            "来源字段事实闭环总账": SOURCE_LABELS["field"],
            "来源证据等级与核验路由表": SOURCE_LABELS["routing"],
            "来源教育部学校属性旁挂表": SOURCE_LABELS["moe"],
            "来源三年投档线索旁挂表": SOURCE_LABELS["historical"],
            "来源期号": master.get("来源期号", ""),
            "来源PDF_SHA256": issue_pdf_sha256,
            "数据阶段": DATA_STAGE_MAJOR,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "可否进入最终志愿方案": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许自动写回主表": "false",
            "是否可作为机器初筛线索": bool_text(as_machine_signal),
            "机器初筛线索等级": signal_level,
            "初筛用途边界": "只能用于机器粗筛和安排核验顺序，不得作为录取概率、最终志愿或专业确认依据。",
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
            "再选科目OCR候选": master.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": master.get("专业计划数OCR候选", ""),
            "学费OCR候选": master.get("学费OCR候选", ""),
            "字段缺口数": field_row.get("字段缺口数", master.get("字段缺口数", "")),
            "字段缺口字段": field_row.get("字段缺口字段", master.get("字段缺口字段", "")),
            "三字段OCR完整状态": field_row.get("三字段OCR完整状态", ""),
            "字段事实闭环等级": field_row.get("字段事实闭环等级", ""),
            "字段事实阻断等级": field_row.get("字段事实阻断等级", ""),
            "候选初筛闸门状态": field_row.get("候选初筛闸门状态", ""),
            "初筛动作桶": field_row.get("初筛动作桶", ""),
            "省招办证据等级": route_row.get("省招办证据等级", ""),
            "自动官网核验可执行性": route_row.get("自动官网核验可执行性", ""),
            "人工核验优先级": route_row.get("人工核验优先级", ""),
            "人工核验强度": route_row.get("人工核验强度", ""),
            "是否必须100%人工核验": route_row.get("是否必须100%人工核验", "false"),
            "是否可低风险抽检": route_row.get("是否可低风险抽检", "false"),
            "PDF原页核验状态": route_row.get("PDF原页核验状态", master.get("PDF原页证据状态", "")),
            "湖北官方系统核验状态": route_row.get("湖北官方系统核验状态", master.get("湖北官方平台字段核验状态", "")),
            "高校官网来源状态": route_row.get("高校官网来源状态", ""),
            "高校官网证据匹配状态": route_row.get("高校官网证据匹配状态", ""),
            "高校官网能否替代湖北官方计划": "false",
            "教育部匹配状态": moe_row.get("教育部匹配状态", ""),
            "公办民办机器线索": moe_row.get("公办民办机器线索", ""),
            "家庭底线属性动作": moe_row.get("家庭底线属性动作", ""),
            "属性闸门等级": moe_row.get("属性闸门等级", ""),
            "教育部所在地": moe_row.get("教育部所在地", ""),
            "教育部所在地命中城市": moe_row.get("教育部所在地命中城市", ""),
            "城市候选": filter_row.get("城市候选", ""),
            "城市字段状态": filter_row.get("城市字段状态", ""),
            "专业偏好方向": filter_row.get("专业偏好方向", master.get("专业偏好方向", "")),
            "机器专业接受度初判": filter_row.get("机器专业接受度初判", master.get("机器专业接受度初判", "")),
            "专业风险类型": filter_row.get("专业风险类型", master.get("专业风险类型", "")),
            "是否超预算机器初判": filter_row.get("是否超预算机器初判", ""),
            "同组真实招生明细数": master.get("同组真实招生明细数", ""),
            "同组偏好专业数": master.get("同组偏好专业数", ""),
            "同组医学护理排除专业数": master.get("同组医学护理排除专业数", ""),
            "同组高收费或超预算专业数": master.get("同组高收费或超预算专业数", ""),
            "同组特殊限制待核专业数": master.get("同组特殊限制待核专业数", ""),
            "同组调剂结论": master.get("同组调剂结论", ""),
            "同代码命中年份数": hist_row.get("同代码命中年份数", ""),
            "同代码命中年份": hist_row.get("同代码命中年份", ""),
            "历史最高等位分差": str(max(diffs)) if diffs else "",
            "历史最低等位分差": str(min(diffs)) if diffs else "",
            "历史线索分层": historical_layer(diffs),
            "三年投档稳定性状态": hist_row.get("稳定性分层", master.get("三年投档稳定性状态", "")),
            "历史线使用口径": hist_row.get("历史线使用口径", master.get("历史线使用口径", "")),
            "机器核验下一步": next_step,
            "人工核验下一步": route_row.get("人工核验下一步", ""),
            "不得进入原因": reason,
            "下一步": next_step,
        })

    majors_by_group = defaultdict(list)
    for row in major_output_rows:
        majors_by_group[row.get("专业组出现ID", "")].append(row)

    group_output_rows = []
    group_missing_major_count = 0
    for group in family_group_rows:
        group_id = group.get("专业组出现ID", "")
        majors = majors_by_group.get(group_id, [])
        if not majors:
            group_missing_major_count += 1
        value_layer = group_value_layer(group, majors)
        review_layer = group_review_layer(majors)
        machine_next, human_next = group_next_steps(value_layer, review_layer)
        major_ids = sorted(row.get("专业行ID", "") for row in majors if row.get("专业行ID"))
        diffs = []
        for row in majors:
            for field in ["历史最高等位分差", "历史最低等位分差"]:
                value = as_int(row.get(field))
                if value is not None:
                    diffs.append(value)
        id_hash = hashlib.sha256("；".join(major_ids).encode("utf-8")).hexdigest() if major_ids else ""
        group_output_rows.append({
            "稳定基座专业组筛选ID": stable_id("STABLEGROUP", [group_id]),
            "来源专业组家庭底线筛选表": SOURCE_LABELS["family_group"],
            "来源稳定基座逐专业筛选视图": str(MAJOR_OUTPUT.relative_to(ROOT)),
            "来源期号": group.get("来源期号", ""),
            "来源PDF_SHA256": issue_pdf_sha256,
            "数据阶段": DATA_STAGE_GROUP,
            "主表粒度": "院校专业组",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "可否进入最终志愿方案": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否进入机器初筛观察池": bool_text(value_layer.startswith(("V1", "V2", "V3", "V4"))),
            "机器筛选价值层级": value_layer,
            "保真核验层级": review_layer,
            "专业组使用边界": "本表用于整组调剂风险和核验排队；最终志愿必须回到完整专业组明细逐项核验。",
            "专业组出现ID": group_id,
            "院校代码": group.get("院校代码", ""),
            "院校名称OCR": group.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": group.get("院校专业组代码OCR规范化", ""),
            "专业组号OCR": group.get("专业组号OCR", ""),
            "来源页码": group.get("来源页码", ""),
            "版面列": group.get("版面列", ""),
            "专业明细行数": str(len(majors)),
            "无逐专业明细占位": bool_text(not majors),
            "城市候选": majors[0].get("城市候选", "") if majors else "",
            "教育部所在地命中城市": majors[0].get("教育部所在地命中城市", "") if majors else "",
            "教育部所在地是否命中城市偏好": "true" if any(row.get("教育部所在地命中城市") for row in majors) else "false",
            "公办民办机器线索": "；".join(sorted({row.get("公办民办机器线索", "") for row in majors if row.get("公办民办机器线索")})),
            "家庭底线属性动作": "；".join(sorted({row.get("家庭底线属性动作", "") for row in majors if row.get("家庭底线属性动作")})),
            "属性闸门等级": "；".join(sorted({row.get("属性闸门等级", "") for row in majors if row.get("属性闸门等级")})),
            "机器家庭匹配初判": group.get("机器家庭匹配初判", ""),
            "调剂初判": group.get("调剂初判", ""),
            "偏好专业数": group.get("偏好专业数", "0"),
            "数字媒体技术专业数": group.get("数字媒体技术专业数", "0"),
            "计算机类相关专业数": group.get("计算机类相关专业数", "0"),
            "师范类相关专业数": group.get("师范类相关专业数", "0"),
            "医学护理排除专业数": group.get("医学护理排除专业数", "0"),
            "高收费或超预算专业数": group.get("高收费或超预算专业数", "0"),
            "特殊限制待核专业数": group.get("特殊限制待核专业数", "0"),
            "字段缺口专业行数": str(sum(as_int(row.get("字段缺口数")) and as_int(row.get("字段缺口数")) > 0 for row in majors)),
            "三字段OCR齐全专业行数": str(sum(row.get("三字段OCR完整状态") == "三字段OCR候选齐全" for row in majors)),
            "字段无候选阻断专业行数": str(sum(row.get("字段事实阻断等级") == "Q0-字段缺口无候选阻断" for row in majors)),
            "结构或归属未闭环专业行数": str(sum(row.get("候选初筛闸门状态") == "G0-结构或归属未闭环" for row in majors)),
            "P0人工核验专业行数": str(sum(row.get("人工核验优先级", "").startswith("P0") for row in majors)),
            "P1人工核验专业行数": str(sum(row.get("人工核验优先级", "").startswith("P1") for row in majors)),
            "P2人工核验专业行数": str(sum(row.get("人工核验优先级", "").startswith("P2") for row in majors)),
            "P3低风险抽检专业行数": str(sum(row.get("人工核验优先级", "").startswith("P3") for row in majors)),
            "必须100%人工核验专业行数": str(sum(row.get("是否必须100%人工核验") == "true" for row in majors)),
            "可低风险抽检专业行数": str(sum(row.get("是否可低风险抽检") == "true" for row in majors)),
            "A1官网自动复跑专业行数": str(sum(row.get("自动官网核验可执行性", "").startswith("A1") for row in majors)),
            "A2官网补结构化专业行数": str(sum(row.get("自动官网核验可执行性", "").startswith("A2") for row in majors)),
            "A4官网继续搜索专业行数": str(sum(row.get("自动官网核验可执行性", "").startswith("A4") for row in majors)),
            "湖北官方系统待核专业行数": str(sum(row.get("湖北官方系统核验状态") == "pending_hubei_official_plan_review" for row in majors)),
            "PDF原页待核专业行数": str(sum(row.get("PDF原页核验状态") == "has_page_hash_pending_manual_pdf_review" for row in majors)),
            "官网辅证命中专业行数": str(sum(row.get("省招办证据等级") == "L3-高校辅证加第三方提示" for row in majors)),
            "同代码命中年份最大值": str(max((as_int(row.get("同代码命中年份数")) or 0 for row in majors), default=0)),
            "历史最高等位分差": str(max(diffs)) if diffs else "",
            "历史最低等位分差": str(min(diffs)) if diffs else "",
            "历史线索分层": historical_layer(diffs),
            "组内专业行ID集合SHA256": id_hash,
            "组内完整专业清单索引": "；".join(
                f"{row.get('专业组内专业序号')}.{row.get('专业代号OCR')} {row.get('专业名称及备注短摘')}[{row.get('专业行ID')}]"
                for row in sorted(majors, key=lambda item: as_int(item.get("专业组内专业序号")) or 999)
            ),
            "机器核验下一步": machine_next,
            "人工核验下一步": human_next,
            "不得进入原因": "专业组筛选视图未完成完整组内专业、PDF原页、湖北官方计划、学校官网/章程、家庭接受度和调剂范围闭环。",
            "下一步": machine_next,
        })

    value_order = {
        "V1-偏好专业优先线索": 1,
        "V2-城市偏好扩展线索": 2,
        "V3-历史线索普通留存": 3,
        "V4-普通留存待了解": 4,
        "V0-默认不进主方案风险": 8,
        "V5-无逐专业明细先补结构": 9,
    }
    review_order = {
        "R1-P0整组先核": 1,
        "R2-P1页列集中核": 2,
        "R3-P2官网后人工确认": 3,
        "R4-P3低风险抽检": 4,
        "R5-常规留存": 5,
        "R0-无明细结构阻断": 9,
    }
    group_output_rows.sort(
        key=lambda row: (
            value_order.get(row["机器筛选价值层级"], 99),
            review_order.get(row["保真核验层级"], 99),
            row.get("来源页码", ""),
            row.get("院校专业组代码OCR规范化", ""),
        )
    )

    write_csv(MAJOR_OUTPUT, major_output_rows, MAJOR_FIELDS)
    write_csv(GROUP_OUTPUT, group_output_rows, GROUP_FIELDS)

    major_signal_counts = Counter(row["机器初筛线索等级"] for row in major_output_rows)
    group_value_counts = Counter(row["机器筛选价值层级"] for row in group_output_rows)
    group_review_counts = Counter(row["保真核验层级"] for row in group_output_rows)
    summary = {
        "status": "issue19_stable_foundation_screening_views_not_final",
        "generated_by": "build_issue19_stable_foundation_screening_views.py",
        "major_output_table": str(MAJOR_OUTPUT.relative_to(ROOT)),
        "group_output_table": str(GROUP_OUTPUT.relative_to(ROOT)),
        "source_pdf_sha256": issue_pdf_sha256,
        "official_public_status_source": str(OFFICIAL_PUBLIC_STATUS.relative_to(ROOT)),
        "official_public_plan_page_sha256": source_pdf_sha256,
        "inputs": input_snapshot(
            ROOT,
            [MASTER, FILTER_PREP, FIELD_FACT, EVIDENCE_ROUTING, MOE_ATTRIBUTE, HISTORICAL_SIDECAR, FAMILY_GROUP, OFFICIAL_PUBLIC_STATUS],
        ),
        "major_row_count": len(major_output_rows),
        "group_row_count": len(group_output_rows),
        "unique_major_line_id_count": len({row["专业行ID"] for row in major_output_rows}),
        "unique_group_occurrence_id_count_in_major_view": len({row["专业组出现ID"] for row in major_output_rows}),
        "zero_detail_group_count": group_missing_major_count,
        "missing_join_counts": dict(missing_join_counts),
        "major_machine_signal_counts": dict(major_signal_counts),
        "major_machine_signal_true_count": sum(row["是否可作为机器初筛线索"] == "true" for row in major_output_rows),
        "group_value_layer_counts": dict(group_value_counts),
        "group_review_layer_counts": dict(group_review_counts),
        "group_machine_observation_pool_count": sum(row["是否进入机器初筛观察池"] == "true" for row in group_output_rows),
        "group_default_not_main_plan_count": group_value_counts.get("V0-默认不进主方案风险", 0),
        "group_preference_priority_count": group_value_counts.get("V1-偏好专业优先线索", 0),
        "group_city_extension_count": group_value_counts.get("V2-城市偏好扩展线索", 0),
        "group_zero_detail_count": group_value_counts.get("V5-无逐专业明细先补结构", 0),
        "p0_group_review_count": group_review_counts.get("R1-P0整组先核", 0),
        "p1_group_review_count": group_review_counts.get("R2-P1页列集中核", 0),
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "policy": {
            "usage": "本产物是稳定数据基座的筛选入口，连接逐专业明细、整组调剂、字段缺口、学校属性、历史线索和核验路由。",
            "non_final_gate": "所有行最终可用=false、可进入下一阶段=false、可否进入最终志愿方案=false。",
            "score_line_boundary": "三年投档线只作冲稳保机器线索；不替代2026招生计划、专业组完整明细或投档规则。",
            "official_boundary": "高校官网和教育部名单只作辅证；不能替代湖北官方系统/省招办计划。",
        },
        "notes": [
            "专业组视图保留整组专业清单索引，后续服从调剂判断必须看完整专业组。",
            "机器初筛观察池只表示值得继续核验，不表示可以填报。",
            "零明细专业组单独保留，防止OCR漏拆被静默丢失。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [MAJOR_OUTPUT, GROUP_OUTPUT, SUMMARY_OUTPUT]
    )
    leaked = [token for token in FORBIDDEN_TEXT_TOKENS if token in public_text]
    if leaked:
        raise SystemExit(f"公开输出含禁止内容：{leaked}")

    print(f"写入 {MAJOR_OUTPUT.relative_to(ROOT)}：{len(major_output_rows)} 行")
    print(f"写入 {GROUP_OUTPUT.relative_to(ROOT)}：{len(group_output_rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
