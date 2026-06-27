#!/usr/bin/env python3
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MOE_DIR = ROOT / "data/official/moe-2025-national-higher-school-list"
MOE_SOURCE_PAGE = MOE_DIR / "source-page.html"
MOE_XLS = MOE_DIR / "national-regular-higher-schools-2025.xls"
MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
FILTER_PREP = ROOT / "data/working/issue19-candidate-filter-prep-major-detail.csv"

NORMALIZED_OUTPUT = ROOT / "data/working/moe-2025-regular-higher-schools-normalized.csv"
NORMALIZED_SUMMARY_OUTPUT = ROOT / "data/working/moe-2025-regular-higher-schools-summary.json"
MAJOR_OUTPUT = ROOT / "data/working/issue19-moe-school-attribute-major-detail.csv"
MAJOR_SUMMARY_OUTPUT = ROOT / "data/working/issue19-moe-school-attribute-major-detail-summary.json"
UNMATCHED_OUTPUT = ROOT / "data/working/issue19-moe-school-attribute-unmatched-schools.csv"

MOE_PAGE_URL = "https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202506/t20250627_1195683.html"
MOE_ATTACHMENT_URL = "https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202506/W020250729615142156867.xls"
MOE_PUBLISH_DATE = "2025-06-27"
MOE_AS_OF_DATE = "2025-06-20"
DATA_STAGE = "issue19_moe_school_attribute_major_detail"

PREFERRED_CITIES = ["成都", "西安", "武汉", "北京"]
VOCATIONAL_SCHOOL_TOKENS = ["职业大学", "职业技术大学"]
PRIVATE_REMARK_TOKEN = "民办"
COOP_REMARK_TOKENS = ["中外合作", "港澳合作"]

NORMALIZED_FIELDS = [
    "教育部名单行ID",
    "来源教育部页面URL",
    "来源教育部附件URL",
    "教育部名单发布日期",
    "教育部名单截至日期",
    "序号",
    "省份分组",
    "学校名称",
    "学校标识码",
    "主管部门",
    "所在地",
    "办学层次",
    "备注",
    "名单层级",
    "学校名称规范键",
]

MAJOR_FIELDS = [
    "学校属性核验ID",
    "来源候选筛选准备表",
    "来源单一逐专业招生明细总工作台",
    "来源教育部全国普通高等学校名单",
    "来源教育部页面URL",
    "来源教育部附件URL",
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
    "院校名称人工确认",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "教育部匹配状态",
    "教育部匹配方式",
    "教育部匹配学校名称",
    "教育部父校线索名称",
    "教育部学校标识码",
    "教育部主管部门",
    "教育部所在地",
    "教育部办学层次",
    "教育部备注",
    "教育部省份分组",
    "教育部名单发布日期",
    "教育部名单截至日期",
    "教育部所在地是否命中城市偏好",
    "教育部所在地命中城市",
    "公办民办机器线索",
    "中外合作/港澳合作机器线索",
    "职业本科名称线索",
    "本科层次机器线索",
    "家庭底线属性动作",
    "职业本科动作",
    "学校所在地字段状态",
    "所在地使用边界",
    "城市候选",
    "城市字段状态",
    "校区/办学地点候选",
    "校区字段状态",
    "中外合作/高收费初判",
    "学费OCR候选",
    "学费OCR数字候选",
    "是否超预算机器初判",
    "专业偏好方向",
    "专业风险类型",
    "调剂影响等级",
    "同组调剂结论",
    "办学属性核验状态",
    "属性闸门等级",
    "不得进入原因",
    "下一步核验动作",
]

UNMATCHED_FIELDS = [
    "院校代码",
    "院校名称OCR",
    "涉及专业明细数",
    "涉及专业组数",
    "来源页码集合",
    "疑似风险类型",
    "示例专业行ID",
    "示例专业名称及备注短摘",
    "建议核验动作",
]

PARENT_SUFFIX_RULES = [
    (r"（北京）$", ""),
    (r"（保定）$", ""),
    (r"（深圳）$", ""),
    (r"（苏州校区）$", ""),
    (r"（珠海校区）$", ""),
    (r"（威海校区）$", ""),
    (r"（威海）$", ""),
    (r"（盘锦校区）$", ""),
    (r"（沙河校区）$", ""),
    (r"（荣昌校区）$", ""),
    (r"（马来西亚校区）$", ""),
    (r"（宜城校区）$", ""),
    (r"秦皇岛分校$", ""),
    (r"威海分校$", ""),
    (r"医学部$", ""),
    (r"医学院$", ""),
]


def ensure_xlrd():
    try:
        import xlrd  # type: ignore

        return xlrd
    except ModuleNotFoundError:
        local_dep = ROOT / "tmp/python-deps/xlrd"
        if local_dep.exists():
            sys.path.insert(0, str(local_dep))
            try:
                import xlrd  # type: ignore

                return xlrd
            except ModuleNotFoundError:
                pass
        raise SystemExit(
            "缺少读取 .xls 所需的 xlrd。可先运行："
            f"{sys.executable} -m pip install --target tmp/python-deps/xlrd xlrd==2.0.1"
        )


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_text(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def normalize_school_key(value):
    return re.sub(r"\s+", "", clean_text(value))


def province_from_group(value):
    return re.sub(r"（.*?）", "", clean_text(value))


def parent_school_candidate(name):
    normalized = normalize_school_key(name)
    for pattern, repl in PARENT_SUFFIX_RULES:
        candidate = re.sub(pattern, repl, normalized)
        if candidate != normalized:
            return candidate
    return ""


def read_moe_school_list():
    xlrd = ensure_xlrd()
    book = xlrd.open_workbook(str(MOE_XLS))
    sheet = book.sheet_by_index(0)
    rows = []
    current_province = ""
    for index in range(sheet.nrows):
        values = [clean_text(sheet.cell_value(index, col)) for col in range(sheet.ncols)]
        if not any(values):
            continue
        first = values[0]
        if first == "序号":
            continue
        if first.startswith("附件") or "全国普通高等学校名单" in first:
            continue
        if not first.isdigit():
            current_province = province_from_group(first)
            continue
        row = {
            "教育部名单行ID": stable_id("MOESCHOOL", [MOE_AS_OF_DATE, first, values[1], values[2]]),
            "来源教育部页面URL": MOE_PAGE_URL,
            "来源教育部附件URL": MOE_ATTACHMENT_URL,
            "教育部名单发布日期": MOE_PUBLISH_DATE,
            "教育部名单截至日期": MOE_AS_OF_DATE,
            "序号": first,
            "省份分组": current_province,
            "学校名称": values[1],
            "学校标识码": values[2],
            "主管部门": values[3],
            "所在地": values[4],
            "办学层次": values[5],
            "备注": values[6],
            "名单层级": "全国普通高等学校名单",
            "学校名称规范键": normalize_school_key(values[1]),
        }
        rows.append(row)
    return rows


def by_major_id(rows):
    return {row.get("专业行ID", ""): row for row in rows}


def city_hit_from_moe_location(location):
    hits = [city for city in PREFERRED_CITIES if city in clean_text(location)]
    return ("true", hits[0]) if hits else ("false", "")


def school_type_signal(moe_row, matched):
    if not matched:
        return "未匹配-待核"
    remark = moe_row.get("备注", "")
    if PRIVATE_REMARK_TOKEN in remark:
        return "民办-教育部备注民办"
    if any(token in remark for token in COOP_REMARK_TOKENS):
        return "中外合作或港澳合作办学线索-教育部备注"
    return "非民办线索-教育部名单未备注民办"


def coop_signal(moe_row, matched, filter_row):
    signals = []
    if matched and any(token in moe_row.get("备注", "") for token in COOP_REMARK_TOKENS):
        signals.append("教育部备注合作办学线索")
    if filter_row.get("中外合作/高收费初判") == "machine_risk_keyword_or_budget_signal":
        signals.append("第19期OCR或预算高收费线索")
    return "；".join(signals) if signals else "未触发机器线索"


def vocational_signal(school_name, moe_row):
    text = "；".join([clean_text(school_name), moe_row.get("学校名称", "") if moe_row else ""])
    return "true" if any(token in text for token in VOCATIONAL_SCHOOL_TOKENS) else "false"


def undergraduate_signal(moe_row, matched):
    if not matched:
        return "未匹配-待核"
    if moe_row.get("办学层次") == "本科":
        return "本科-教育部名单"
    return f"{moe_row.get('办学层次', '')}-教育部名单需核"


def family_attribute_action(public_private_signal, vocational, coop):
    if public_private_signal == "民办-教育部备注民办":
        return "默认不进主方案-民办线索"
    if "合作办学" in public_private_signal or "合作办学" in coop:
        return "单独讨论-中外合作或港澳合作办学线索"
    if public_private_signal == "未匹配-待核":
        return "先核学校名称或特殊院校"
    if vocational == "true":
        return "单独讨论-职业本科名称线索"
    return "继续核公办普通学费-非民办线索"


def attribute_gate(match_status, public_private_signal, vocational, coop):
    if match_status == "unmatched_needs_school_name_or_special_school_review":
        return "G0-校名未匹配阻断"
    if public_private_signal == "民办-教育部备注民办":
        return "G0-民办线索阻断"
    if "合作办学" in public_private_signal or "合作办学" in coop:
        return "G0-合作办学/高收费线索阻断"
    if vocational == "true":
        return "G1-职业本科需家庭确认"
    if match_status == "parent_school_name_match_location_not_campus":
        return "G1-父校线索待校区核验"
    return "G1-教育部名单命中仍待2026计划和章程核验"


def location_status(match_status):
    if match_status == "exact_school_name_match":
        return "moe_school_location_source_not_campus"
    if match_status == "parent_school_name_match_location_not_campus":
        return "parent_school_location_not_campus"
    return "pending_school_name_or_special_school_location_review"


def location_boundary(match_status):
    if match_status == "parent_school_name_match_location_not_campus":
        return "教育部所在地为父校登记地线索，不能当作实际就读校区或城市"
    if match_status == "exact_school_name_match":
        return "教育部所在地为学校登记地线索，不能替代2026招生计划和章程中的办学地点"
    return "未匹配教育部学校名单，不能使用所在地字段"


def blocking_reason(match_status, action, filter_row):
    pieces = [
        "学校属性表仍未完成PDF原页、湖北官方系统、招生章程、校区地点、家庭接受度和同组调剂闭环",
        "教育部名单只作学校登记信息线索，不能替代2026湖北招生计划",
    ]
    if match_status == "unmatched_needs_school_name_or_special_school_review":
        pieces.append("教育部名单未匹配，需先核OCR校名或特殊院校性质")
    if action.startswith("默认不进主方案"):
        pieces.append(action)
    if "职业本科" in action:
        pieces.append("职业本科/职业大学需家庭单独确认培养定位和接受度")
    if "中外合作" in action or "港澳合作" in action:
        pieces.append("合作办学或高收费线索需单独核费用和家庭接受度")
    if filter_row.get("同组调剂结论") == "pending_transfer_decision":
        pieces.append("同组完整专业接受度和是否服从调剂尚未确认")
    return "；".join(dict.fromkeys(pieces))


def next_action(match_status, action):
    if match_status == "unmatched_needs_school_name_or_special_school_review":
        return "回看PDF原页校名并用湖北官方系统/学校官网确认学校全称、院校代码和办学属性"
    if action.startswith("默认不进主方案"):
        return "保留为风险线索，除非家庭明确接受民办/高收费后再补招生章程和官方计划"
    if "职业本科" in action:
        return "补学校官网和招生章程，确认职业本科定位、学费、校区和家庭接受度"
    return "继续核2026湖北官方计划、招生章程、实际校区/办学地点、学费、家庭接受度和同组调剂"


def unmatched_risk_type(name):
    risks = []
    if re.search(r"[0-9A-Za-z]", name):
        risks.append("OCR混入字母或数字")
    if any(token in name for token in ["（", ")", "(", "，"]):
        risks.append("OCR括号或标点异常")
    if "职业" in name:
        risks.append("职业本科/职业大学或新增学校待核")
    if any(token in name for token in ["军", "陆军", "香港", "学院", "大学"]):
        risks.append("特殊院校或校名OCR待核")
    return "；".join(risks) if risks else "校名未匹配待人工核验"


def main():
    source_text = MOE_SOURCE_PAGE.read_text(encoding="utf-8", errors="ignore")
    moe_rows = read_moe_school_list()
    write_csv(NORMALIZED_OUTPUT, moe_rows, NORMALIZED_FIELDS)

    exact_index = {row["学校名称规范键"]: row for row in moe_rows}
    master_rows = read_csv(MASTER_WORKBENCH)
    filter_rows = read_csv(FILTER_PREP)
    filter_by_major = by_major_id(filter_rows)

    output_rows = []
    unmatched_school_rows = {}
    match_status_counts = Counter()
    public_private_counts = Counter()
    action_counts = Counter()
    gate_counts = Counter()
    matched_school_names_by_status = defaultdict(set)

    for master in master_rows:
        major_id = master.get("专业行ID", "")
        filter_row = filter_by_major.get(major_id, {})
        school_name = master.get("院校名称OCR", "")
        school_key = normalize_school_key(school_name)
        moe_row = exact_index.get(school_key)
        parent_name = ""
        if moe_row:
            match_status = "exact_school_name_match"
            match_method = "院校名称OCR精确匹配教育部学校名称"
        else:
            parent_key = parent_school_candidate(school_name)
            parent_name = parent_key
            moe_row = exact_index.get(parent_key) if parent_key else None
            if moe_row:
                match_status = "parent_school_name_match_location_not_campus"
                match_method = "院校名称OCR按分校/校区/医学部后缀折回父校匹配，所在地不得当校区"
            else:
                match_status = "unmatched_needs_school_name_or_special_school_review"
                match_method = "未匹配教育部2025全国普通高等学校名单"
                moe_row = {}

        matched = bool(moe_row)
        city_hit, city = city_hit_from_moe_location(moe_row.get("所在地", ""))
        public_private = school_type_signal(moe_row, matched)
        coop = coop_signal(moe_row, matched, filter_row)
        vocational = vocational_signal(school_name, moe_row)
        undergrad = undergraduate_signal(moe_row, matched)
        action = family_attribute_action(public_private, vocational, coop)
        vocational_action = "默认不进主方案-职业本科名称线索" if vocational == "true" else "未触发"
        gate = attribute_gate(match_status, public_private, vocational, coop)

        row = {
            "学校属性核验ID": stable_id("MOEATTR", [major_id]),
            "来源候选筛选准备表": "data/working/issue19-candidate-filter-prep-major-detail.csv",
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源教育部全国普通高等学校名单": "data/official/moe-2025-national-higher-school-list/national-regular-higher-schools-2025.xls",
            "来源教育部页面URL": MOE_PAGE_URL,
            "来源教育部附件URL": MOE_ATTACHMENT_URL,
            "来源期号": master.get("来源期号", ""),
            "来源PDF_SHA256": master.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "专业行ID": major_id,
            "专业组出现ID": master.get("专业组出现ID", ""),
            "院校代码": master.get("院校代码", ""),
            "院校名称OCR": school_name,
            "院校名称人工确认": filter_row.get("院校名称人工确认", ""),
            "院校专业组代码OCR规范化": master.get("院校专业组代码OCR规范化", ""),
            "来源页码": master.get("来源页码", ""),
            "版面列": master.get("版面列", ""),
            "专业组内专业序号": master.get("专业组内专业序号", ""),
            "专业代号OCR": master.get("专业代号OCR", ""),
            "专业名称及备注短摘": master.get("专业名称及备注短摘", ""),
            "教育部匹配状态": match_status,
            "教育部匹配方式": match_method,
            "教育部匹配学校名称": moe_row.get("学校名称", ""),
            "教育部父校线索名称": parent_name if match_status.startswith("parent_") else "",
            "教育部学校标识码": moe_row.get("学校标识码", ""),
            "教育部主管部门": moe_row.get("主管部门", ""),
            "教育部所在地": moe_row.get("所在地", ""),
            "教育部办学层次": moe_row.get("办学层次", ""),
            "教育部备注": moe_row.get("备注", ""),
            "教育部省份分组": moe_row.get("省份分组", ""),
            "教育部名单发布日期": MOE_PUBLISH_DATE,
            "教育部名单截至日期": MOE_AS_OF_DATE,
            "教育部所在地是否命中城市偏好": city_hit,
            "教育部所在地命中城市": city,
            "公办民办机器线索": public_private,
            "中外合作/港澳合作机器线索": coop,
            "职业本科名称线索": vocational,
            "本科层次机器线索": undergrad,
            "家庭底线属性动作": action,
            "职业本科动作": vocational_action,
            "学校所在地字段状态": location_status(match_status),
            "所在地使用边界": location_boundary(match_status),
            "城市候选": filter_row.get("城市候选", ""),
            "城市字段状态": filter_row.get("城市字段状态", ""),
            "校区/办学地点候选": filter_row.get("校区/办学地点候选", ""),
            "校区字段状态": filter_row.get("校区字段状态", ""),
            "中外合作/高收费初判": filter_row.get("中外合作/高收费初判", ""),
            "学费OCR候选": filter_row.get("学费OCR候选", ""),
            "学费OCR数字候选": filter_row.get("学费OCR数字候选", ""),
            "是否超预算机器初判": filter_row.get("是否超预算机器初判", ""),
            "专业偏好方向": filter_row.get("专业偏好方向", ""),
            "专业风险类型": filter_row.get("专业风险类型", ""),
            "调剂影响等级": filter_row.get("调剂影响等级", ""),
            "同组调剂结论": filter_row.get("同组调剂结论", ""),
            "办学属性核验状态": (
                "pending_school_name_or_special_school_review"
                if not matched
                else "moe_list_matched_pending_2026_plan_and_charter_review"
            ),
            "属性闸门等级": gate,
            "不得进入原因": blocking_reason(match_status, action, filter_row),
            "下一步核验动作": next_action(match_status, action),
        }
        output_rows.append(row)
        match_status_counts[match_status] += 1
        public_private_counts[public_private] += 1
        action_counts[action] += 1
        gate_counts[gate] += 1
        matched_school_names_by_status[match_status].add((master.get("院校代码", ""), school_name))

        if not matched:
            key = (master.get("院校代码", ""), school_name)
            item = unmatched_school_rows.setdefault(
                key,
                {
                    "院校代码": master.get("院校代码", ""),
                    "院校名称OCR": school_name,
                    "专业行ID集合": set(),
                    "专业组出现ID集合": set(),
                    "来源页码集合": set(),
                    "疑似风险类型": unmatched_risk_type(school_name),
                    "示例专业行ID": major_id,
                    "示例专业名称及备注短摘": master.get("专业名称及备注短摘", ""),
                    "建议核验动作": "回看PDF原页校名，并用湖北官方系统、学校官网或招生章程确认学校全称和性质",
                },
            )
            item["专业行ID集合"].add(major_id)
            item["专业组出现ID集合"].add(master.get("专业组出现ID", ""))
            item["来源页码集合"].add(master.get("来源页码", ""))

    write_csv(MAJOR_OUTPUT, output_rows, MAJOR_FIELDS)

    unmatched_rows = []
    for item in unmatched_school_rows.values():
        unmatched_rows.append(
            {
                "院校代码": item["院校代码"],
                "院校名称OCR": item["院校名称OCR"],
                "涉及专业明细数": str(len(item["专业行ID集合"])),
                "涉及专业组数": str(len(item["专业组出现ID集合"] - {""})),
                "来源页码集合": "；".join(sorted(item["来源页码集合"] - {""}, key=lambda x: int(x) if x.isdigit() else 9999)),
                "疑似风险类型": item["疑似风险类型"],
                "示例专业行ID": item["示例专业行ID"],
                "示例专业名称及备注短摘": item["示例专业名称及备注短摘"],
                "建议核验动作": item["建议核验动作"],
            }
        )
    unmatched_rows.sort(key=lambda row: (row["院校代码"], row["院校名称OCR"]))
    write_csv(UNMATCHED_OUTPUT, unmatched_rows, UNMATCHED_FIELDS)

    normalized_summary = {
        "status": "moe_regular_higher_school_list_normalized",
        "generated_by": Path(__file__).name,
        "source_page": "data/official/moe-2025-national-higher-school-list/source-page.html",
        "source_xls": "data/official/moe-2025-national-higher-school-list/national-regular-higher-schools-2025.xls",
        "source_page_url": MOE_PAGE_URL,
        "source_attachment_url": MOE_ATTACHMENT_URL,
        "source_page_sha256": sha256(MOE_SOURCE_PAGE),
        "source_xls_sha256": sha256(MOE_XLS),
        "published_date": MOE_PUBLISH_DATE,
        "as_of_date": MOE_AS_OF_DATE,
        "row_count": len(moe_rows),
        "unique_school_name_count": len({row["学校名称"] for row in moe_rows}),
        "undergraduate_count": sum(row["办学层次"] == "本科" for row in moe_rows),
        "junior_college_count": sum(row["办学层次"] == "专科" for row in moe_rows),
        "remark_counts": dict(Counter(row["备注"] or "空" for row in moe_rows)),
        "province_group_counts": dict(Counter(row["省份分组"] for row in moe_rows)),
        "source_page_mentions_expected_counts": (
            "普通高等学校2919所" in source_text
            and "本科学校1365所" in source_text
            and "高职（专科）学校1554所" in source_text
        ),
        "output_table": "data/working/moe-2025-regular-higher-schools-normalized.csv",
    }
    NORMALIZED_SUMMARY_OUTPUT.write_text(
        json.dumps(normalized_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    major_summary = {
        "status": "issue19_moe_school_attribute_major_detail_not_final",
        "generated_by": Path(__file__).name,
        "output_table": "data/working/issue19-moe-school-attribute-major-detail.csv",
        "support_unmatched_school_table": "data/working/issue19-moe-school-attribute-unmatched-schools.csv",
        "source_master_workbench": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_filter_prep": "data/working/issue19-candidate-filter-prep-major-detail.csv",
        "source_moe_normalized": "data/working/moe-2025-regular-higher-schools-normalized.csv",
        "source_page_url": MOE_PAGE_URL,
        "source_attachment_url": MOE_ATTACHMENT_URL,
        "row_count": len(output_rows),
        "unique_attribute_id_count": len({row["学校属性核验ID"] for row in output_rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "unique_school_code_name_count": len({(row["院校代码"], row["院校名称OCR"]) for row in output_rows}),
        "match_status_counts": dict(match_status_counts),
        "matched_school_count_by_status": {
            status: len(values) for status, values in sorted(matched_school_names_by_status.items())
        },
        "public_private_machine_signal_counts": dict(public_private_counts),
        "family_attribute_action_counts": dict(action_counts),
        "attribute_gate_counts": dict(gate_counts),
        "vocational_name_signal_count": sum(row["职业本科名称线索"] == "true" for row in output_rows),
        "moe_location_preferred_city_hit_count": sum(
            row["教育部所在地是否命中城市偏好"] == "true" for row in output_rows
        ),
        "unmatched_school_count": len(unmatched_rows),
        "unmatched_major_line_count": match_status_counts.get(
            "unmatched_needs_school_name_or_special_school_review", 0
        ),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "location_boundary": "教育部所在地只作学校登记地线索，不替代2026招生计划或招生章程中的实际校区/办学地点。",
        "public_private_boundary": "教育部备注为空只能表示名单备注列未标注民办或合作办学，不能单独等于公办最终结论。",
    }
    MAJOR_SUMMARY_OUTPUT.write_text(
        json.dumps(major_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"写入 {NORMALIZED_OUTPUT.relative_to(ROOT)}：{len(moe_rows)} 行")
    print(f"写入 {MAJOR_OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写入 {UNMATCHED_OUTPUT.relative_to(ROOT)}：{len(unmatched_rows)} 行")


if __name__ == "__main__":
    main()
