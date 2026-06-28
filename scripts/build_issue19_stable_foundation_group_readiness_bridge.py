#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]

STABLE_MAJOR = ROOT / "data/working/issue19-stable-foundation-major-screening-view.csv"
STABLE_GROUP = ROOT / "data/working/issue19-stable-foundation-group-screening-view.csv"
AUTO_WORKBENCH = ROOT / "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv"
FIRST_CLOSURE_DETAIL = ROOT / "data/working/issue19-stable-foundation-first-closure-detail-packet.csv"
FIRST_CLOSURE_PAGE_SIDE = ROOT / "data/working/issue19-stable-foundation-first-closure-page-side-packet.csv"
SCHOOL_SOURCE_REFRESH = ROOT / "data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv"
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

OUTPUT = ROOT / "data/working/issue19-stable-foundation-group-readiness-bridge.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-stable-foundation-group-readiness-bridge-summary.json"

DATA_STAGE = "issue19_stable_foundation_group_readiness_bridge"

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
    "稳定基座专业组就绪桥接ID",
    "来源稳定基座专业组筛选视图",
    "来源稳定基座逐专业筛选视图",
    "来源稳定基座自动官网辅证交叉核验工作台",
    "来源稳定基座第一闭环明细包",
    "来源稳定基座第一闭环页列包",
    "来源高校侧辅证刷新公开账本",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业明细行数",
    "机器筛选价值层级",
    "保真核验层级",
    "数据底座就绪等级",
    "候选讨论就绪层级",
    "主要阻断原因",
    "偏好专业数",
    "数字媒体技术专业数",
    "计算机类相关专业数",
    "师范类相关专业数",
    "医学护理排除专业数",
    "高收费或超预算专业数",
    "特殊限制待核专业数",
    "城市候选",
    "公办民办机器线索",
    "家庭底线属性动作",
    "属性闸门等级",
    "调剂初判",
    "字段缺口专业行数",
    "字段无候选阻断专业行数",
    "结构或归属未闭环专业行数",
    "P0人工核验专业行数",
    "P1人工核验专业行数",
    "P2人工核验专业行数",
    "P3低风险抽检专业行数",
    "必须100%人工核验专业行数",
    "可低风险抽检专业行数",
    "湖北官方系统待核专业行数",
    "PDF原页待核专业行数",
    "官网辅证命中专业行数",
    "自动官网辅证任务数",
    "C0冲突任务数",
    "C1官网补缺任务数",
    "C2强辅证抽检任务数",
    "C3字段辅证任务数",
    "C4部分来源待结构化任务数",
    "C5章程规则任务数",
    "C6继续补源任务数",
    "C7官网未匹配任务数",
    "第一闭环覆盖状态",
    "第一闭环明细任务数",
    "第一闭环自动任务数",
    "第一闭环人工字段任务数",
    "第一闭环双人复核任务数",
    "第一闭环涉及页列数",
    "第一闭环页列包ID集合SHA256",
    "第一闭环页列优先级集合",
    "高校侧刷新任务数",
    "高校侧刷新批次集合",
    "高校侧公开来源文件数量",
    "高校侧公开来源URL数量",
    "高校侧涉及招生明细数",
    "历史线索分层",
    "同代码命中年份最大值",
    "历史最高等位分差",
    "历史最低等位分差",
    "组内专业行ID集合SHA256",
    "机器核验下一步",
    "人工核验下一步",
    "桥接表使用边界",
    "下一步",
]

FORBIDDEN_PUBLIC_TOKENS = [
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
    "已确认",
    "已核准",
    "可填报",
    "最终推荐",
]


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


def sha_list(values):
    normalized = "；".join(sorted({value for value in values if value}))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""


def join_limited(values, limit=8):
    result = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    if len(seen) > limit:
        result = result[:limit] + [f"另{len(seen) - limit}项"]
    return "；".join(result)


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def group_count(row, field):
    return as_int(row.get(field)) or 0


def readiness_level(group, auto_counts, first_closure_count):
    if group_count(group, "专业明细行数") == 0 or group.get("无逐专业明细占位") == "true":
        return "B0-无逐专业明细先补结构", "无逐专业明细或OCR未拆出完整专业组。"
    if first_closure_count > 0:
        return "B2-第一闭环已排队待核", "已进入第一闭环批次，需按页列核PDF原页、湖北官方侧和高校辅证。"
    if group_count(group, "结构或归属未闭环专业行数") > 0:
        return "B1-结构或归属未闭环", "存在结构或专业组归属未闭环专业行。"
    if group_count(group, "字段无候选阻断专业行数") > 0 or group_count(group, "字段缺口专业行数") > 0:
        return "B3-字段事实缺口待补", "仍有计划数、学费或再选科目字段缺口。"
    if auto_counts["C0"] or auto_counts["C1"] or auto_counts["C7"]:
        return "B4-官网冲突补缺或未匹配待核", "存在官网冲突、补缺候选或专业名未稳定匹配。"
    if auto_counts["C4"] or auto_counts["C6"]:
        return "B5-高校源待结构化或继续补源", "高校侧已有部分来源待结构化，或仍需继续搜索2026湖北计划。"
    if group_count(group, "P0人工核验专业行数") or group_count(group, "P1人工核验专业行数"):
        return "B6-PDF页列核验待完成", "仍有P0/P1人工核验专业行。"
    if group_count(group, "P2人工核验专业行数") or group_count(group, "P3低风险抽检专业行数"):
        return "B7-官网后人工确认或低风险抽检", "可进入分层抽检或官网后人工确认，但不能定稿。"
    return "B8-机器观察池待官方闭环", "机器侧暂无新增硬阻断，但仍需湖北官方侧和原页闭环。"


def discussion_layer(group, readiness, first_closure_count):
    value_layer = group.get("机器筛选价值层级", "")
    if readiness.startswith(("B0", "B1")):
        return "D0-暂不可进入候选讨论"
    if value_layer.startswith("V0"):
        return "D1-家庭底线默认不进主方案"
    if first_closure_count > 0:
        return "D2-完成第一闭环后再讨论"
    if value_layer.startswith(("V1", "V2")):
        return "D3-偏好线索待核后优先讨论"
    if value_layer.startswith(("V3", "V4")):
        return "D4-普通观察池待抽检"
    return "D5-仅留存待补证"


def next_step(readiness, discussion, page_side_count, source_refresh_count):
    if readiness.startswith("B0"):
        return "先回PDF原页确认专业组标题和明细区域，补齐逐专业结构。"
    if readiness.startswith("B1"):
        return "先核专业组归属、跨页和切组，再进入字段事实核验。"
    if readiness.startswith("B2"):
        return f"先执行第一闭环页列核验：{page_side_count} 个页列，完成PDF原页、湖北官方侧和高校辅证三方记录。"
    if readiness.startswith("B3"):
        return "先补计划数、学费、再选科目字段候选，字段无候选行不得进入筛选。"
    if readiness.startswith(("B4", "B5")):
        return f"先处理高校侧辅证：{source_refresh_count} 个学校级刷新任务，并回到第19期原页判定差异。"
    if discussion.startswith("D1"):
        return "默认不进主方案；只有家庭明确接受相关费用、属性或调剂风险后再复核。"
    return "保留为机器观察池，等待官方计划、原页复核和家庭接受度闭环后再排序。"


def main():
    group_rows = read_csv(STABLE_GROUP)
    major_rows = read_csv(STABLE_MAJOR)
    auto_rows = read_csv(AUTO_WORKBENCH)
    first_detail_rows = read_csv(FIRST_CLOSURE_DETAIL)
    first_page_rows = read_csv(FIRST_CLOSURE_PAGE_SIDE)
    school_refresh_rows = read_csv(SCHOOL_SOURCE_REFRESH)
    official_status = json.loads(OFFICIAL_STATUS.read_text())

    issue_pdf_sha256 = group_rows[0].get("来源PDF_SHA256", "") if group_rows else ""

    major_ids_by_group = defaultdict(list)
    for row in major_rows:
        major_ids_by_group[row.get("专业组出现ID", "")].append(row.get("专业行ID", ""))

    auto_by_group = defaultdict(list)
    for row in auto_rows:
        auto_by_group[row.get("专业组出现ID", "")].append(row)

    first_detail_by_group = defaultdict(list)
    for row in first_detail_rows:
        first_detail_by_group[row.get("专业组出现ID", "")].append(row)

    page_side_by_key = {
        row.get("页码版面键", ""): row for row in first_page_rows
    }
    school_refresh_by_school = defaultdict(list)
    for row in school_refresh_rows:
        school_refresh_by_school[row.get("院校代码", "")].append(row)

    output_rows = []
    first_closure_groups = set()
    source_refresh_schools = set()

    for group in group_rows:
        group_id = group.get("专业组出现ID", "")
        school_code = group.get("院校代码", "")
        auto_tasks = auto_by_group.get(group_id, [])
        closure_tasks = first_detail_by_group.get(group_id, [])
        school_tasks = school_refresh_by_school.get(school_code, [])

        auto_action_counts = Counter()
        for task in auto_tasks:
            action = task.get("官网辅证自动动作", "")
            if action.startswith("C0"):
                auto_action_counts["C0"] += 1
            elif action.startswith("C1"):
                auto_action_counts["C1"] += 1
            elif action.startswith("C2"):
                auto_action_counts["C2"] += 1
            elif action.startswith("C3"):
                auto_action_counts["C3"] += 1
            elif action.startswith("C4"):
                auto_action_counts["C4"] += 1
            elif action.startswith("C5"):
                auto_action_counts["C5"] += 1
            elif action.startswith("C6"):
                auto_action_counts["C6"] += 1
            elif action.startswith("C7"):
                auto_action_counts["C7"] += 1

        page_side_keys = sorted({row.get("页码版面键", "") for row in closure_tasks if row.get("页码版面键")})
        page_side_packets = [page_side_by_key[key] for key in page_side_keys if key in page_side_by_key]
        page_side_ids = [row.get("稳定基座第一闭环页列包ID", "") for row in page_side_packets]
        page_side_priorities = [row.get("第一闭环页列优先级", "") for row in page_side_packets]

        first_auto_count = sum(row.get("任务来源类型") == "auto_official_crosscheck" for row in closure_tasks)
        first_manual_count = sum(row.get("任务来源类型") == "manual_field_closure" for row in closure_tasks)
        first_double_count = sum(row.get("是否需要双人复核") == "true" for row in closure_tasks)

        readiness, block_reason = readiness_level(group, auto_action_counts, len(closure_tasks))
        discussion = discussion_layer(group, readiness, len(closure_tasks))
        source_file_count = sum(as_int(row.get("公开来源文件数量")) or 0 for row in school_tasks)
        source_url_count = sum(as_int(row.get("公开来源URL数量")) or 0 for row in school_tasks)
        source_refresh_detail_count = sum(as_int(row.get("涉及招生明细数")) or 0 for row in school_tasks)
        step = next_step(readiness, discussion, len(page_side_keys), len(school_tasks))

        if closure_tasks:
            first_closure_groups.add(group_id)
        if school_tasks:
            source_refresh_schools.add(school_code)

        output_rows.append({
            "稳定基座专业组就绪桥接ID": stable_id("STABLEGROUPREADY", [group_id]),
            "来源稳定基座专业组筛选视图": str(STABLE_GROUP.relative_to(ROOT)),
            "来源稳定基座逐专业筛选视图": str(STABLE_MAJOR.relative_to(ROOT)),
            "来源稳定基座自动官网辅证交叉核验工作台": str(AUTO_WORKBENCH.relative_to(ROOT)),
            "来源稳定基座第一闭环明细包": str(FIRST_CLOSURE_DETAIL.relative_to(ROOT)),
            "来源稳定基座第一闭环页列包": str(FIRST_CLOSURE_PAGE_SIDE.relative_to(ROOT)),
            "来源高校侧辅证刷新公开账本": str(SCHOOL_SOURCE_REFRESH.relative_to(ROOT)),
            "来源湖北官方公开入口状态快照": str(OFFICIAL_STATUS.relative_to(ROOT)),
            "来源期号": group.get("来源期号", ""),
            "来源PDF_SHA256": issue_pdf_sha256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "院校专业组",
            **false_gate_values(),
            "专业组出现ID": group_id,
            "院校代码": school_code,
            "院校名称OCR": group.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": group.get("院校专业组代码OCR规范化", ""),
            "来源页码": group.get("来源页码", ""),
            "版面列": group.get("版面列", ""),
            "专业明细行数": group.get("专业明细行数", ""),
            "机器筛选价值层级": group.get("机器筛选价值层级", ""),
            "保真核验层级": group.get("保真核验层级", ""),
            "数据底座就绪等级": readiness,
            "候选讨论就绪层级": discussion,
            "主要阻断原因": block_reason,
            "偏好专业数": group.get("偏好专业数", "0"),
            "数字媒体技术专业数": group.get("数字媒体技术专业数", "0"),
            "计算机类相关专业数": group.get("计算机类相关专业数", "0"),
            "师范类相关专业数": group.get("师范类相关专业数", "0"),
            "医学护理排除专业数": group.get("医学护理排除专业数", "0"),
            "高收费或超预算专业数": group.get("高收费或超预算专业数", "0"),
            "特殊限制待核专业数": group.get("特殊限制待核专业数", "0"),
            "城市候选": group.get("城市候选", ""),
            "公办民办机器线索": group.get("公办民办机器线索", ""),
            "家庭底线属性动作": group.get("家庭底线属性动作", ""),
            "属性闸门等级": group.get("属性闸门等级", ""),
            "调剂初判": group.get("调剂初判", ""),
            "字段缺口专业行数": group.get("字段缺口专业行数", "0"),
            "字段无候选阻断专业行数": group.get("字段无候选阻断专业行数", "0"),
            "结构或归属未闭环专业行数": group.get("结构或归属未闭环专业行数", "0"),
            "P0人工核验专业行数": group.get("P0人工核验专业行数", "0"),
            "P1人工核验专业行数": group.get("P1人工核验专业行数", "0"),
            "P2人工核验专业行数": group.get("P2人工核验专业行数", "0"),
            "P3低风险抽检专业行数": group.get("P3低风险抽检专业行数", "0"),
            "必须100%人工核验专业行数": group.get("必须100%人工核验专业行数", "0"),
            "可低风险抽检专业行数": group.get("可低风险抽检专业行数", "0"),
            "湖北官方系统待核专业行数": group.get("湖北官方系统待核专业行数", "0"),
            "PDF原页待核专业行数": group.get("PDF原页待核专业行数", "0"),
            "官网辅证命中专业行数": group.get("官网辅证命中专业行数", "0"),
            "自动官网辅证任务数": str(len(auto_tasks)),
            "C0冲突任务数": str(auto_action_counts["C0"]),
            "C1官网补缺任务数": str(auto_action_counts["C1"]),
            "C2强辅证抽检任务数": str(auto_action_counts["C2"]),
            "C3字段辅证任务数": str(auto_action_counts["C3"]),
            "C4部分来源待结构化任务数": str(auto_action_counts["C4"]),
            "C5章程规则任务数": str(auto_action_counts["C5"]),
            "C6继续补源任务数": str(auto_action_counts["C6"]),
            "C7官网未匹配任务数": str(auto_action_counts["C7"]),
            "第一闭环覆盖状态": "Y-已进入第一闭环批次" if closure_tasks else "N-未进入第一闭环批次",
            "第一闭环明细任务数": str(len(closure_tasks)),
            "第一闭环自动任务数": str(first_auto_count),
            "第一闭环人工字段任务数": str(first_manual_count),
            "第一闭环双人复核任务数": str(first_double_count),
            "第一闭环涉及页列数": str(len(page_side_keys)),
            "第一闭环页列包ID集合SHA256": sha_list(page_side_ids),
            "第一闭环页列优先级集合": join_limited(page_side_priorities),
            "高校侧刷新任务数": str(len(school_tasks)),
            "高校侧刷新批次集合": join_limited(row.get("高校侧刷新批次", "") for row in school_tasks),
            "高校侧公开来源文件数量": str(source_file_count),
            "高校侧公开来源URL数量": str(source_url_count),
            "高校侧涉及招生明细数": str(source_refresh_detail_count),
            "历史线索分层": group.get("历史线索分层", ""),
            "同代码命中年份最大值": group.get("同代码命中年份最大值", ""),
            "历史最高等位分差": group.get("历史最高等位分差", ""),
            "历史最低等位分差": group.get("历史最低等位分差", ""),
            "组内专业行ID集合SHA256": group.get("组内专业行ID集合SHA256", sha_list(major_ids_by_group.get(group_id, []))),
            "机器核验下一步": group.get("机器核验下一步", ""),
            "人工核验下一步": group.get("人工核验下一步", ""),
            "桥接表使用边界": "只用于稳定基座完成度、复核排队和后续候选讨论准备；不确认字段事实，不生成志愿排序。",
            "下一步": step,
        })

    readiness_order = {
        "B0-无逐专业明细先补结构": 0,
        "B1-结构或归属未闭环": 1,
        "B2-第一闭环已排队待核": 2,
        "B3-字段事实缺口待补": 3,
        "B4-官网冲突补缺或未匹配待核": 4,
        "B5-高校源待结构化或继续补源": 5,
        "B6-PDF页列核验待完成": 6,
        "B7-官网后人工确认或低风险抽检": 7,
        "B8-机器观察池待官方闭环": 8,
    }
    discussion_order = {
        "D2-完成第一闭环后再讨论": 0,
        "D3-偏好线索待核后优先讨论": 1,
        "D4-普通观察池待抽检": 2,
        "D1-家庭底线默认不进主方案": 8,
        "D0-暂不可进入候选讨论": 9,
        "D5-仅留存待补证": 10,
    }
    output_rows.sort(
        key=lambda row: (
            discussion_order.get(row["候选讨论就绪层级"], 99),
            readiness_order.get(row["数据底座就绪等级"], 99),
            -(as_int(row["偏好专业数"]) or 0),
            row.get("来源页码", ""),
            row.get("院校专业组代码OCR规范化", ""),
        )
    )

    write_csv(OUTPUT, output_rows, FIELDS)

    public_text = OUTPUT.read_text(encoding="utf-8-sig")
    forbidden_hits = sorted(token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text)
    if forbidden_hits:
        raise SystemExit(f"公开桥接表含禁止内容：{forbidden_hits}")

    readiness_counts = Counter(row["数据底座就绪等级"] for row in output_rows)
    discussion_counts = Counter(row["候选讨论就绪层级"] for row in output_rows)
    first_closure_coverage_counts = Counter(row["第一闭环覆盖状态"] for row in output_rows)
    summary = {
        "status": "issue19_stable_foundation_group_readiness_bridge_not_final",
        "generated_by": "build_issue19_stable_foundation_group_readiness_bridge.py",
        "output_table": str(OUTPUT.relative_to(ROOT)),
        "source_issue": "湖北招生考试2026年19期·本科普通批（下）",
        "source_pdf_sha256": issue_pdf_sha256,
        "official_public_status_source": str(OFFICIAL_STATUS.relative_to(ROOT)),
        "official_public_plan_page_can_finalize": bool(official_status.get("official_plan_page", {}).get("can_finalize_plan")),
        "zspt_platform_can_finalize": bool(official_status.get("zspt_platform", {}).get("can_finalize_plan")),
        "input_files": input_snapshot(
            ROOT,
            [
                STABLE_GROUP,
                STABLE_MAJOR,
                AUTO_WORKBENCH,
                FIRST_CLOSURE_DETAIL,
                FIRST_CLOSURE_PAGE_SIDE,
                SCHOOL_SOURCE_REFRESH,
                OFFICIAL_STATUS,
            ],
        ),
        "row_count": len(output_rows),
        "unique_group_occurrence_id_count": len({row["专业组出现ID"] for row in output_rows}),
        "unique_school_count": len({row["院校代码"] for row in output_rows if row["院校代码"]}),
        "readiness_level_counts": dict(readiness_counts),
        "discussion_layer_counts": dict(discussion_counts),
        "first_closure_coverage_counts": dict(first_closure_coverage_counts),
        "first_closure_group_count": len(first_closure_groups),
        "first_closure_detail_task_count": len(first_detail_rows),
        "first_closure_page_side_count": len(first_page_rows),
        "school_source_refresh_school_count": len(source_refresh_schools),
        "school_source_refresh_task_count": len(school_refresh_rows),
        "auto_official_crosscheck_task_count": len(auto_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in output_rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in output_rows),
        "official_plan_replacement_allowed_count": sum(row["是否允许官网证据替代湖北官方计划"] == "true" for row in output_rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段事实"] == "true" for row in output_rows),
        "policy": {
            "usage": "本表把稳定筛选视图、第一闭环批次、高校侧辅证刷新任务接到同一院校专业组粒度，用于判断下一步复核和候选讨论准备度。",
            "non_final_gate": "所有行最终可用、可进入下一阶段、推荐依据、学校专业建议、官网替代湖北官方计划和字段写回均为false。",
            "official_boundary": "湖北官方系统/省招办计划和第19期PDF原页仍是字段事实闭环条件；高校侧来源只作辅证和差异发现。",
            "group_boundary": "服从调剂判断必须看完整专业组，本表只压缩工作量和排序核验任务。"
        },
        "next_steps": [
            "优先处理D2/B2：完成第一闭环页列核验后，才能把相关专业组带入候选讨论。",
            "D3偏好线索必须继续核完整专业组，不得只看拟填6个专业。",
            "D1家庭底线风险默认不进主方案，除非家庭明确接受相关费用、属性或调剂风险。"
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary_text = SUMMARY_OUTPUT.read_text(encoding="utf-8")
    forbidden_summary_hits = sorted(token for token in FORBIDDEN_PUBLIC_TOKENS if token in summary_text)
    if forbidden_summary_hits:
        raise SystemExit(f"公开桥接摘要含禁止内容：{forbidden_summary_hits}")

    print(f"写出稳定基座专业组就绪桥接表：{OUTPUT.relative_to(ROOT)}")
    print(f"专业组行数：{len(output_rows)}")
    print(f"第一闭环覆盖专业组数：{len(first_closure_groups)}")


if __name__ == "__main__":
    main()
