#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

OPPORTUNITY_QUEUE = WORKING / "issue19-school-source-opportunity-queue.csv"
SCHOOL_REFRESH = WORKING / "issue19-stable-foundation-school-source-refresh-public-ledger.csv"
C4C6_PACKETS = WORKING / "issue19-c4-c6-school-source-refresh-execution-packets.csv"
C4C6_REUSE = WORKING / "issue19-c4-c6-retained-source-reuse-public-ledger.csv"
C4C6_DIFF = WORKING / "issue19-c4-c6-structured-candidate-diff-public-ledger.csv"
C4C6_ATTEMPTS = WORKING / "issue19-c4-c6-school-source-acquisition-attempts-public-ledger.csv"
LIVE_LEDGER = WORKING / "issue19-school-source-live-20260629-ledger.csv"
OFFICIAL_LIVE_RECHECK = WORKING / "issue19-official-public-entry-live-recheck.json"

OUTPUT = WORKING / "issue19-school-source-status-snapshot-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-status-snapshot-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_status_snapshot_public_ledger"
GENERATED_AT = "2026-06-29"

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
    "高校官网辅证状态快照ID",
    "来源高校官网辅证机会队列",
    "来源高校侧辅证刷新公开账本",
    "来源C4C6高校源刷新执行包",
    "来源C4C6已留存官网源复用审计",
    "来源C4C6结构化候选diff公开账本",
    "来源C4C6高校官网补源尝试账本",
    "来源高校官网live补源账本",
    "来源湖北官方公开入口活体复查",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行建议序号",
    "机会队列ID",
    "高校侧辅证刷新公开账本ID",
    "院校代码",
    "院校名称公开",
    "机会优先级",
    "机会类型",
    "自动收益分",
    "官网辅证自动动作",
    "高校侧刷新批次",
    "高校侧刷新任务类型",
    "闭环优先级",
    "官网证据强度",
    "官网来源状态",
    "来源质量判断",
    "来源文件类型集合",
    "公开来源文件数量",
    "公开来源URL数量",
    "候选官网URL数量",
    "候选官网URL集合SHA256",
    "种子官网URL数量",
    "种子官网URL集合SHA256",
    "本地公开来源文件集合SHA256",
    "涉及招生明细数",
    "涉及专业组数",
    "涉及PDF页数",
    "计划数冲突行数",
    "官网补缺候选行数",
    "强辅证抽检行数",
    "部分来源待结构化行数",
    "继续补源行数",
    "仅章程规则行数",
    "官网未匹配行数",
    "字段辅证行数",
    "C4C6执行包数量",
    "C4C6需补结构化明细数",
    "C4C6需继续补源明细数",
    "C4C6综合结构化官网证据行数",
    "C4C6专业名匹配明细数",
    "C4C6未匹配明细数",
    "C4C6无结构化官网源明细数",
    "C4C6计划数一致候选数",
    "C4C6官网可补OCR计划数候选数",
    "C4C6计划数冲突候选数",
    "C4C6可生成候选diff明细数",
    "最新自动探针状态",
    "是否已有live补源记录",
    "live补源记录数",
    "live结构化线索记录数",
    "live补源状态桶",
    "学校任务总数",
    "学校P0任务数",
    "学校P1任务数",
    "学校P2任务数",
    "学校P3任务数",
    "学校可复用官网源任务数",
    "学校部分来源待跟进任务数",
    "学校仍需搜索计划网源任务数",
    "学校仅章程规则任务数",
    "自动化下一步桶",
    "人工最小核验动作桶",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源刷新状态",
    "字段事实写回状态",
    "快照结论桶",
    "建议下一步动作",
    "完成条件",
    "公开安全策略",
]

FORBIDDEN_PUBLIC_TOKENS = [
    "/Users/",
    "/home/",
    "/var/folders/",
    "/private/",
    "private/",
    "private\\",
    "file://",
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
    "Set-Cookie",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "api_key",
    "身份证",
    "准考证",
    "报名号",
    "序列号",
    "手机号",
    "OCR行文本",
    "字段确认值",
    "人工读数",
    "候选值",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_int(value):
    try:
        return int(str(value).strip() or "0")
    except ValueError:
        return 0


def stable_id(prefix, parts):
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def source_path(path):
    return str(path.relative_to(ROOT))


def count_by(rows, field, value):
    return sum(1 for row in rows if row.get(field) == value)


def live_bucket(live_rows):
    if not live_rows:
        return "L0-暂无live补源记录"
    structured = sum(1 for row in live_rows if row.get("结构化输出", "").strip())
    if structured:
        return "L2-live已有结构化线索仍待PDF和湖北官方闭环"
    return "L1-live已有入口或来源记录仍待结构化"


def conclusion_bucket(row):
    source_status = row.get("官网来源状态", "")
    priority = row.get("机会优先级", "")
    opportunity_type = row.get("机会类型", "")
    live_status = row.get("live补源状态桶", "")

    if opportunity_type.startswith("O8"):
        return "S4-仅章程规则核验，不核计划数字段"
    if source_status == "needs_official_plan_source_search":
        if live_status.startswith("L2"):
            return "S2-live已有结构化线索，转PDF原页和湖北官方侧核验"
        return "S3-仍需继续找2026湖北物理类计划网源"
    if priority == "P0-立即处理":
        return "S0-高风险冲突或补缺，先核PDF原页和湖北官方侧"
    if source_status == "has_reusable_2026_hubei_plan_source":
        return "S1-已有高校侧结构化线索，可生成diff但不得写回"
    if source_status == "has_partial_source_needs_followup":
        return "S2-已有入口或部分来源，先补结构化和匹配规则"
    return "S5-低收益留存，最终候选前再核"


def next_action(row):
    bucket = row["快照结论桶"]
    if bucket.startswith("S0"):
        return "先核第19期PDF原页和湖北官方侧；高校官网只作冲突解释和差异提示。"
    if bucket.startswith("S1"):
        return "复用已有高校结构化来源生成差异线索；字段事实仍等待PDF原页和湖北官方侧确认。"
    if bucket.startswith("S2-live"):
        return "把live结构化线索接入差异核验；重点核PDF原页、湖北官方侧和专业组边界。"
    if bucket.startswith("S2"):
        return "补结构化、专业名匹配规则或公开附件解析；再回PDF原页和湖北官方侧核验。"
    if bucket.startswith("S3"):
        return "继续查高校招生网、公开API、XLSX、PDF或图片计划；不可使用外省计划迁移。"
    if bucket.startswith("S4"):
        return "只核章程中的体检、语种、单科、收费、调剂和录取规则；计划字段等待省源。"
    return "暂作低收益留存；若学校进入最终候选再升级PDF原页和湖北官方侧核验。"


def action_bucket(row):
    value = row.get("自动化下一步", "")
    if "冲突" in value:
        return "A0-冲突回页和官方侧核验"
    if "补计划数缺口" in value or "缺口" in value:
        return "A1-官网补缺线索回页核验"
    if "专业名" in value:
        return "A2-专业名匹配规则或人工确认"
    if "结构化" in value or "抽取" in value:
        return "A3-补结构化或解析公开来源"
    if "全网检索" in value or "继续搜索" in value:
        return "A4-继续搜索高校计划网源"
    if "章程" in value or "规则" in value:
        return "A5-章程规则核验"
    if "抽检" in value:
        return "A6-强辅证分层抽检"
    return "A7-留存观察"


def manual_bucket(row):
    value = row.get("人工最小核验动作", "")
    if "冲突" in value:
        return "M0-人工核冲突来源"
    if "专业名称" in value:
        return "M1-人工核专业名和同页上下文"
    if "抽检" in value:
        return "M2-人工分层抽检"
    if "体检" in value or "语种" in value or "单科" in value:
        return "M3-人工核章程限制"
    if "官网入口" in value or "招生网" in value:
        return "M4-人工补计划网源"
    if "高校源定位" in value:
        return "M5-人工按高校线索回页"
    return "M6-最终候选前人工核验"


def build_rows():
    opportunity_rows = read_csv(OPPORTUNITY_QUEUE)
    refresh_rows = read_csv(SCHOOL_REFRESH)
    live_rows = read_csv(LIVE_LEDGER) if LIVE_LEDGER.exists() else []

    opportunity_by_school = defaultdict(list)
    for row in opportunity_rows:
        opportunity_by_school[row["院校代码"]].append(row)

    refresh_by_key = {}
    for row in refresh_rows:
        key = (
            row.get("院校代码", ""),
            row.get("官网辅证自动动作", ""),
            row.get("高校侧刷新批次", ""),
            row.get("高校侧刷新任务类型", ""),
        )
        refresh_by_key[key] = row

    live_by_school = defaultdict(list)
    for row in live_rows:
        live_by_school[row["院校代码"]].append(row)

    output = []
    for row in opportunity_rows:
        school_rows = opportunity_by_school[row["院校代码"]]
        school_live_rows = live_by_school.get(row["院校代码"], [])
        refresh_row = refresh_by_key.get(
            (
                row.get("院校代码", ""),
                row.get("官网辅证自动动作", ""),
                row.get("高校侧刷新批次", ""),
                row.get("高校侧刷新任务类型", ""),
            ),
            {},
        )
        output_row = {
            "高校官网辅证状态快照ID": stable_id(
                "SCHOOLSRCSTATUS",
                [row.get("高校官网辅证机会ID", ""), row.get("院校代码", "")],
            ),
            "来源高校官网辅证机会队列": source_path(OPPORTUNITY_QUEUE),
            "来源高校侧辅证刷新公开账本": source_path(SCHOOL_REFRESH),
            "来源C4C6高校源刷新执行包": source_path(C4C6_PACKETS),
            "来源C4C6已留存官网源复用审计": source_path(C4C6_REUSE),
            "来源C4C6结构化候选diff公开账本": source_path(C4C6_DIFF),
            "来源C4C6高校官网补源尝试账本": source_path(C4C6_ATTEMPTS),
            "来源高校官网live补源账本": source_path(LIVE_LEDGER),
            "来源湖北官方公开入口活体复查": source_path(OFFICIAL_LIVE_RECHECK),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校×高校侧辅证机会任务",
            "任务粒度": "公开任务级状态快照；逐专业字段仍留在原工作台和私有核验材料",
            **{field: "false" for field in FALSE_FIELDS},
            "执行建议序号": row.get("执行建议序号", ""),
            "机会队列ID": row.get("高校官网辅证机会ID", ""),
            "高校侧辅证刷新公开账本ID": refresh_row.get("高校侧辅证刷新公开账本ID", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称公开": row.get("院校名称OCR", ""),
            "机会优先级": row.get("机会优先级", ""),
            "机会类型": row.get("机会类型", ""),
            "自动收益分": row.get("自动收益分", ""),
            "官网辅证自动动作": row.get("官网辅证自动动作", ""),
            "高校侧刷新批次": row.get("高校侧刷新批次", ""),
            "高校侧刷新任务类型": row.get("高校侧刷新任务类型", ""),
            "闭环优先级": row.get("闭环优先级", ""),
            "官网证据强度": row.get("官网证据强度", ""),
            "官网来源状态": row.get("官网来源状态", ""),
            "来源质量判断": row.get("来源质量判断", ""),
            "来源文件类型集合": row.get("来源文件类型集合", ""),
            "公开来源文件数量": row.get("公开来源文件数量", "0"),
            "公开来源URL数量": row.get("公开来源URL数量", "0"),
            "候选官网URL数量": row.get("候选官网URL数量", "0"),
            "候选官网URL集合SHA256": row.get("候选官网URL集合SHA256", ""),
            "种子官网URL数量": row.get("种子官网URL数量", "0"),
            "种子官网URL集合SHA256": row.get("种子官网URL集合SHA256", ""),
            "本地公开来源文件集合SHA256": row.get("本地公开来源文件集合SHA256", ""),
            "涉及招生明细数": row.get("涉及招生明细数", "0"),
            "涉及专业组数": row.get("涉及专业组数", "0"),
            "涉及PDF页数": row.get("涉及PDF页数", "0"),
            "计划数冲突行数": row.get("计划数冲突行数", "0"),
            "官网补缺候选行数": row.get("官网补缺候选行数", "0"),
            "强辅证抽检行数": row.get("强辅证抽检行数", "0"),
            "部分来源待结构化行数": row.get("部分来源待结构化行数", "0"),
            "继续补源行数": row.get("继续补源行数", "0"),
            "仅章程规则行数": row.get("仅章程规则行数", "0"),
            "官网未匹配行数": row.get("官网未匹配行数", "0"),
            "字段辅证行数": row.get("字段辅证行数", "0"),
            "C4C6执行包数量": row.get("C4C6执行包数量", "0"),
            "C4C6需补结构化明细数": row.get("C4C6需补结构化明细数", "0"),
            "C4C6需继续补源明细数": row.get("C4C6需继续补源明细数", "0"),
            "C4C6综合结构化官网证据行数": row.get("C4C6综合结构化官网证据行数", "0"),
            "C4C6专业名匹配明细数": row.get("C4C6专业名匹配明细数", "0"),
            "C4C6未匹配明细数": row.get("C4C6未匹配明细数", "0"),
            "C4C6无结构化官网源明细数": row.get("C4C6无结构化官网源明细数", "0"),
            "C4C6计划数一致候选数": row.get("C4C6计划数一致候选数", "0"),
            "C4C6官网可补OCR计划数候选数": row.get("C4C6官网可补OCR计划数候选数", "0"),
            "C4C6计划数冲突候选数": row.get("C4C6计划数冲突候选数", "0"),
            "C4C6可生成候选diff明细数": row.get("C4C6可生成候选diff明细数", "0"),
            "最新自动探针状态": row.get("最新自动探针状态", "") or "no_live_probe_record",
            "是否已有live补源记录": "true" if school_live_rows else "false",
            "live补源记录数": str(len(school_live_rows)),
            "live结构化线索记录数": str(
                sum(1 for live_row in school_live_rows if live_row.get("结构化输出", "").strip())
            ),
            "live补源状态桶": live_bucket(school_live_rows),
            "学校任务总数": str(len(school_rows)),
            "学校P0任务数": str(count_by(school_rows, "机会优先级", "P0-立即处理")),
            "学校P1任务数": str(count_by(school_rows, "机会优先级", "P1-高收益自动补源")),
            "学校P2任务数": str(count_by(school_rows, "机会优先级", "P2-常规自动补源或抽检")),
            "学校P3任务数": str(count_by(school_rows, "机会优先级", "P3-低收益留存")),
            "学校可复用官网源任务数": str(
                count_by(school_rows, "官网来源状态", "has_reusable_2026_hubei_plan_source")
            ),
            "学校部分来源待跟进任务数": str(
                count_by(school_rows, "官网来源状态", "has_partial_source_needs_followup")
            ),
            "学校仍需搜索计划网源任务数": str(
                count_by(school_rows, "官网来源状态", "needs_official_plan_source_search")
            ),
            "学校仅章程规则任务数": str(
                count_by(school_rows, "官网来源状态", "charter_or_rules_only_no_plan")
            ),
            "自动化下一步桶": action_bucket(row),
            "人工最小核验动作桶": manual_bucket(row),
            "PDF原页核页状态": row.get("PDF原页核页状态", ""),
            "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统或省招办计划核验状态", ""),
            "高校官网源刷新状态": row.get("高校官网源刷新状态", ""),
            "字段事实写回状态": row.get("字段事实写回状态", ""),
            "快照结论桶": "",
            "建议下一步动作": "",
            "完成条件": (
                "高校官网侧线索完成结构化或补源后，仍必须回到第19期PDF原页和湖北官方系统或省招办计划核验；"
                "需要章程限制的学校还需核录取规则、体检、语种、单科、收费、校区和调剂范围。"
            ),
            "公开安全策略": (
                "公开层只保存学校、任务桶、来源数量、集合SHA、状态桶和门禁；"
                "不保存逐专业字段内容、OCR原文、人工核验内容、私有路径、URL正文或登录信息。"
            ),
        }
        output_row["快照结论桶"] = conclusion_bucket(output_row)
        output_row["建议下一步动作"] = next_action(output_row)
        output.append(output_row)
    return output


def build_summary(rows):
    priority_counts = Counter(row["机会优先级"] for row in rows)
    opportunity_type_counts = Counter(row["机会类型"] for row in rows)
    source_status_counts = Counter(row["官网来源状态"] for row in rows)
    conclusion_counts = Counter(row["快照结论桶"] for row in rows)
    live_bucket_counts = Counter(row["live补源状态桶"] for row in rows)

    summary = {
        "status": f"{DATA_STAGE}_not_final",
        "generated_by": Path(__file__).name,
        "source_school_source_opportunity_queue": source_path(OPPORTUNITY_QUEUE),
        "source_school_refresh_public_ledger": source_path(SCHOOL_REFRESH),
        "source_c4c6_packets": source_path(C4C6_PACKETS),
        "source_c4c6_reuse": source_path(C4C6_REUSE),
        "source_c4c6_diff": source_path(C4C6_DIFF),
        "source_c4c6_attempts": source_path(C4C6_ATTEMPTS),
        "source_school_source_live_ledger": source_path(LIVE_LEDGER),
        "source_official_live_recheck": source_path(OFFICIAL_LIVE_RECHECK),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "output_table": source_path(OUTPUT),
        "row_grain": "高校×高校侧辅证机会任务",
        "row_count": len(rows),
        "unique_school_count": len({row["院校代码"] for row in rows}),
        "priority_counts": dict(sorted(priority_counts.items())),
        "opportunity_type_counts": dict(sorted(opportunity_type_counts.items())),
        "source_status_counts": dict(sorted(source_status_counts.items())),
        "snapshot_conclusion_counts": dict(sorted(conclusion_counts.items())),
        "live_bucket_counts": dict(sorted(live_bucket_counts.items())),
        "top_15_school_codes_by_execution_order": [row["院校代码"] for row in rows[:15]],
        "top_15_school_names_by_execution_order": [row["院校名称公开"] for row in rows[:15]],
        "total_involved_major_detail_count": sum(as_int(row["涉及招生明细数"]) for row in rows),
        "total_involved_group_count": sum(as_int(row["涉及专业组数"]) for row in rows),
        "total_plan_conflict_row_count": sum(as_int(row["计划数冲突行数"]) for row in rows),
        "total_fill_candidate_row_count": sum(as_int(row["官网补缺候选行数"]) for row in rows),
        "total_c4c6_packet_count": sum(as_int(row["C4C6执行包数量"]) for row in rows),
        "total_c4c6_need_structure_detail_count": sum(
            as_int(row["C4C6需补结构化明细数"]) for row in rows
        ),
        "total_c4c6_need_source_search_detail_count": sum(
            as_int(row["C4C6需继续补源明细数"]) for row in rows
        ),
        "total_c4c6_structured_source_row_count": sum(
            as_int(row["C4C6综合结构化官网证据行数"]) for row in rows
        ),
        "total_c4c6_candidate_diff_detail_count": sum(
            as_int(row["C4C6可生成候选diff明细数"]) for row in rows
        ),
        "total_c4c6_no_structured_source_detail_count": sum(
            as_int(row["C4C6无结构化官网源明细数"]) for row in rows
        ),
        "live_record_task_row_count": sum(row["是否已有live补源记录"] == "true" for row in rows),
        "live_record_school_count": len(
            {row["院校代码"] for row in rows if row["是否已有live补源记录"] == "true"}
        ),
        "live_structured_task_row_count": sum(as_int(row["live结构化线索记录数"]) > 0 for row in rows),
        "pdf_pending_task_count": sum(row["PDF原页核页状态"] == "pending_manual_pdf_review" for row in rows),
        "hubei_official_pending_task_count": sum(
            row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_review"
            for row in rows
        ),
        "school_source_refresh_pending_task_count": sum(
            row["高校官网源刷新状态"] == "pending_school_source_refresh" for row in rows
        ),
        "field_writeback_blocked_count": sum(
            row["字段事实写回状态"] == "blocked_until_pdf_hubei_official_review"
            for row in rows
        ),
        "field_writeback_ready_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "public_boundary": (
            "公开表只保存学校、任务桶、来源数量、集合SHA、状态桶和非最终门禁；"
            "不保存逐专业字段内容、OCR原文、人工核验内容、私有路径、URL正文或登录态。"
        ),
        "next_use": (
            "用于给36所学校80个高校侧辅证任务分派自动补源、补结构化、规则核验和PDF/湖北官方侧核验；"
            "不得作为字段最终事实、学校专业建议或志愿推荐依据。"
        ),
    }
    return summary


def validate_public_safety(rows, summary):
    text = json.dumps(summary, ensure_ascii=False) + "\n"
    text += "\n".join(",".join(str(row.get(field, "")) for field in FIELDS) for row in rows)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise ValueError(f"public output contains forbidden tokens: {hits}")


def main():
    rows = build_rows()
    summary = build_summary(rows)
    validate_public_safety(rows, summary)
    write_csv(OUTPUT, rows, FIELDS)
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
