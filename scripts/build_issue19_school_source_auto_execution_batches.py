#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

STATUS_SNAPSHOT = WORKING / "issue19-school-source-status-snapshot-public-ledger.csv"
STATUS_SUMMARY = WORKING / "issue19-school-source-status-snapshot-summary.json"
C4C6_PACKETS = WORKING / "issue19-c4-c6-school-source-refresh-execution-packets.csv"
C4C6_DIFF = WORKING / "issue19-c4-c6-structured-candidate-diff-public-ledger.csv"
C4C6_ATTEMPTS = WORKING / "issue19-c4-c6-school-source-acquisition-attempts-public-ledger.csv"
LIVE_LEDGER = WORKING / "issue19-school-source-live-20260629-ledger.csv"

OUTPUT = WORKING / "issue19-school-source-auto-execution-batches-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-auto-execution-batches-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_auto_execution_batches_public_ledger"
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
    "高校官网辅证自动执行批次ID",
    "来源高校官网辅证状态快照",
    "来源高校官网辅证状态快照摘要",
    "来源C4C6高校源刷新执行包",
    "来源C4C6结构化候选diff公开账本",
    "来源C4C6高校官网补源尝试账本",
    "来源高校官网live补源账本",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行批次序号",
    "执行批次分层",
    "自动化下一步桶",
    "自动执行泳道",
    "自动执行动作",
    "人工最小核验动作桶",
    "人工最小核验动作",
    "结构化输出状态桶",
    "候选diff状态桶",
    "补源状态桶",
    "闭环阻断状态桶",
    "高校官网辅证状态快照ID",
    "机会队列ID",
    "执行建议序号",
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
    "ocr-runs",
    "rendered-pages",
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

ACTION_ORDER = {
    "A0-冲突回页和官方侧核验": "B0-先核冲突",
    "A1-官网补缺线索回页核验": "B1-先核补缺",
    "A2-专业名匹配规则或人工确认": "B2-先核专业名归属",
    "A3-补结构化或解析公开来源": "B3-自动补结构化",
    "A4-继续搜索高校计划网源": "B4-自动补源",
    "A5-章程规则核验": "B5-只核规则限制",
    "A6-强辅证分层抽检": "B6-抽检留痕",
    "A7-留存观察": "B7-低收益留存",
}

AUTO_ACTIONS = {
    "A0-冲突回页和官方侧核验": "整理高校侧差异线索，优先回第19期PDF原页和湖北官方侧核验。",
    "A1-官网补缺线索回页核验": "整理高校侧补缺线索，回第19期PDF原页和湖北官方侧确认。",
    "A2-专业名匹配规则或人工确认": "补专业名匹配规则，定位同页上下文和专业组边界。",
    "A3-补结构化或解析公开来源": "复用已有公开来源，补湖北物理普通本科计划结构化和包级diff。",
    "A4-继续搜索高校计划网源": "继续搜索学校招生网、公开API、XLSX、PDF或HTML计划源并留存SHA。",
    "A5-章程规则核验": "核体检、语种、单科、收费、校区、调剂和录取规则限制。",
    "A6-强辅证分层抽检": "对高校侧强辅证做分层抽检，失败时升级核验范围。",
    "A7-留存观察": "保留边界记录，若进入最终候选讨论再升级核验。",
}

MANUAL_ACTIONS = {
    "M0-人工核冲突来源": "人工优先核计划数冲突、专业组边界和同页上下文。",
    "M1-人工核专业名和同页上下文": "人工核专业名称归属、备注边界和同组调剂范围。",
    "M2-人工分层抽检": "人工按学校、页面和来源类型抽检高校侧线索。",
    "M3-人工核章程限制": "人工核章程限制、收费、校区和特殊要求。",
    "M4-人工补计划网源": "人工必要时补找招生网计划入口或附件。",
    "M5-人工按高校线索回页": "人工按高校侧线索回第19期PDF原页核页。",
    "M6-最终候选前人工核验": "进入最终候选讨论前再升级人工闭环。",
}


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


def structure_bucket(row):
    if as_int(row.get("C4C6需补结构化明细数")):
        return "T0-需补结构化或补湖北行"
    if as_int(row.get("C4C6综合结构化官网证据行数")):
        return "T1-已有结构化源可生成diff"
    if as_int(row.get("公开来源文件数量")) or as_int(row.get("公开来源URL数量")):
        return "T2-有公开来源待解析"
    return "T3-暂无结构化源"


def diff_bucket(row):
    diff_count = as_int(row.get("C4C6可生成候选diff明细数"))
    conflict_count = as_int(row.get("C4C6计划数冲突候选数"))
    fill_count = as_int(row.get("C4C6官网可补OCR计划数候选数"))
    if diff_count and conflict_count:
        return "D0-可生成diff且有计划数冲突线索"
    if diff_count and fill_count:
        return "D1-可生成diff且有OCR补缺线索"
    if diff_count:
        return "D2-可生成diff待回页"
    if as_int(row.get("C4C6综合结构化官网证据行数")):
        return "D3-已有结构化源但本任务无diff"
    if as_int(row.get("C4C6无结构化官网源明细数")):
        return "D4-无结构化官网源"
    return "D5-不适用"


def source_bucket(row):
    source_status = row.get("官网来源状态", "")
    action = row.get("自动化下一步桶", "")
    if action.startswith("A4") or source_status == "needs_official_plan_source_search":
        return "S0-继续补高校官网计划网源"
    if as_int(row.get("C4C6需补结构化明细数")):
        return "S1-已有来源待结构化"
    if source_status == "has_reusable_2026_hubei_plan_source":
        return "S2-已有可复用高校官网源"
    if source_status == "charter_or_rules_only_no_plan":
        return "S3-仅章程规则源"
    if source_status == "has_partial_source_needs_followup":
        return "S4-部分来源待跟进"
    return "S5-留存观察"


def blocking_bucket(row):
    if (
        row.get("PDF原页核页状态") == "pending_manual_pdf_review"
        and row.get("湖北官方系统或省招办计划核验状态") == "pending_hubei_official_review"
        and row.get("字段事实写回状态") == "blocked_until_pdf_hubei_official_review"
    ):
        return "G0-PDF原页和湖北官方侧未闭环，禁止写回"
    return "G1-需重新检查闭环状态"


def build_rows():
    status_rows = read_csv(STATUS_SNAPSHOT)
    output = []
    for row in status_rows:
        action_bucket = row.get("自动化下一步桶", "")
        manual_bucket = row.get("人工最小核验动作桶", "")
        output_row = {
            "高校官网辅证自动执行批次ID": stable_id(
                "SCHOOLSRCEXEC",
                [
                    row.get("高校官网辅证状态快照ID", ""),
                    row.get("机会队列ID", ""),
                    action_bucket,
                ],
            ),
            "来源高校官网辅证状态快照": source_path(STATUS_SNAPSHOT),
            "来源高校官网辅证状态快照摘要": source_path(STATUS_SUMMARY),
            "来源C4C6高校源刷新执行包": source_path(C4C6_PACKETS),
            "来源C4C6结构化候选diff公开账本": source_path(C4C6_DIFF),
            "来源C4C6高校官网补源尝试账本": source_path(C4C6_ATTEMPTS),
            "来源高校官网live补源账本": source_path(LIVE_LEDGER),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校×高校侧辅证自动执行批次",
            "任务粒度": "公开任务级执行批次；逐专业字段仍留在原工作台和私有核验材料",
            **{field: "false" for field in FALSE_FIELDS},
            "执行批次序号": row.get("执行建议序号", ""),
            "执行批次分层": ACTION_ORDER.get(action_bucket, "B9-未分类"),
            "自动化下一步桶": action_bucket,
            "自动执行泳道": action_bucket,
            "自动执行动作": AUTO_ACTIONS.get(action_bucket, "保留任务，等待后续核验。"),
            "人工最小核验动作桶": manual_bucket,
            "人工最小核验动作": MANUAL_ACTIONS.get(manual_bucket, "按最终候选前闭环规则人工核验。"),
            "结构化输出状态桶": structure_bucket(row),
            "候选diff状态桶": diff_bucket(row),
            "补源状态桶": source_bucket(row),
            "闭环阻断状态桶": blocking_bucket(row),
            "高校官网辅证状态快照ID": row.get("高校官网辅证状态快照ID", ""),
            "机会队列ID": row.get("机会队列ID", ""),
            "执行建议序号": row.get("执行建议序号", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称公开": row.get("院校名称公开", ""),
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
            "最新自动探针状态": row.get("最新自动探针状态", ""),
            "是否已有live补源记录": row.get("是否已有live补源记录", ""),
            "live补源记录数": row.get("live补源记录数", "0"),
            "live结构化线索记录数": row.get("live结构化线索记录数", "0"),
            "live补源状态桶": row.get("live补源状态桶", ""),
            "学校任务总数": row.get("学校任务总数", "0"),
            "学校P0任务数": row.get("学校P0任务数", "0"),
            "学校P1任务数": row.get("学校P1任务数", "0"),
            "学校P2任务数": row.get("学校P2任务数", "0"),
            "学校P3任务数": row.get("学校P3任务数", "0"),
            "学校可复用官网源任务数": row.get("学校可复用官网源任务数", "0"),
            "学校部分来源待跟进任务数": row.get("学校部分来源待跟进任务数", "0"),
            "学校仍需搜索计划网源任务数": row.get("学校仍需搜索计划网源任务数", "0"),
            "学校仅章程规则任务数": row.get("学校仅章程规则任务数", "0"),
            "PDF原页核页状态": row.get("PDF原页核页状态", ""),
            "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统或省招办计划核验状态", ""),
            "高校官网源刷新状态": row.get("高校官网源刷新状态", ""),
            "字段事实写回状态": row.get("字段事实写回状态", ""),
            "快照结论桶": row.get("快照结论桶", ""),
            "建议下一步动作": row.get("建议下一步动作", ""),
            "完成条件": row.get("完成条件", ""),
            "公开安全策略": (
                "公开层只保存学校级任务、执行桶、来源数量、集合SHA、状态桶和门禁；"
                "不保存逐专业字段内容、OCR原文、人工核验内容、私有路径、URL正文或登录信息。"
            ),
        }
        output.append(output_row)
    return output


def build_summary(rows):
    return {
        "status": f"{DATA_STAGE}_not_final",
        "generated_by": Path(__file__).name,
        "source_school_source_status_snapshot": source_path(STATUS_SNAPSHOT),
        "source_school_source_status_snapshot_summary": source_path(STATUS_SUMMARY),
        "source_c4c6_packets": source_path(C4C6_PACKETS),
        "source_c4c6_diff": source_path(C4C6_DIFF),
        "source_c4c6_attempts": source_path(C4C6_ATTEMPTS),
        "source_school_source_live_ledger": source_path(LIVE_LEDGER),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "output_table": source_path(OUTPUT),
        "row_grain": "高校×高校侧辅证自动执行批次",
        "row_count": len(rows),
        "unique_school_count": len({row["院校代码"] for row in rows}),
        "unique_execution_batch_count": len({row["高校官网辅证自动执行批次ID"] for row in rows}),
        "execution_lane_counts": dict(sorted(Counter(row["自动执行泳道"] for row in rows).items())),
        "execution_layer_counts": dict(sorted(Counter(row["执行批次分层"] for row in rows).items())),
        "manual_bucket_counts": dict(sorted(Counter(row["人工最小核验动作桶"] for row in rows).items())),
        "structure_bucket_counts": dict(sorted(Counter(row["结构化输出状态桶"] for row in rows).items())),
        "diff_bucket_counts": dict(sorted(Counter(row["候选diff状态桶"] for row in rows).items())),
        "source_bucket_counts": dict(sorted(Counter(row["补源状态桶"] for row in rows).items())),
        "blocking_bucket_counts": dict(sorted(Counter(row["闭环阻断状态桶"] for row in rows).items())),
        "priority_counts": dict(sorted(Counter(row["机会优先级"] for row in rows).items())),
        "opportunity_type_counts": dict(sorted(Counter(row["机会类型"] for row in rows).items())),
        "school_source_action_counts": dict(sorted(Counter(row["官网辅证自动动作"] for row in rows).items())),
        "source_status_counts": dict(sorted(Counter(row["官网来源状态"] for row in rows).items())),
        "snapshot_conclusion_counts": dict(sorted(Counter(row["快照结论桶"] for row in rows).items())),
        "live_bucket_counts": dict(sorted(Counter(row["live补源状态桶"] for row in rows).items())),
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
        "total_c4c6_plan_match_candidate_count": sum(
            as_int(row["C4C6计划数一致候选数"]) for row in rows
        ),
        "total_c4c6_plan_fill_candidate_count": sum(
            as_int(row["C4C6官网可补OCR计划数候选数"]) for row in rows
        ),
        "total_c4c6_plan_conflict_candidate_count": sum(
            as_int(row["C4C6计划数冲突候选数"]) for row in rows
        ),
        "pdf_pending_task_count": sum(row["PDF原页核页状态"] == "pending_manual_pdf_review" for row in rows),
        "hubei_official_pending_task_count": sum(
            row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_review"
            for row in rows
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
            "该表只安排高校官网侧自动补源、补结构化、候选diff和人工最小核验；"
            "不得替代第19期PDF原页、湖北官方系统或省招办计划，不得作为字段事实或志愿建议。"
        ),
        "next_use": (
            "优先按A0/A1回页核验冲突和补缺，按A3/A4继续补结构化和补计划网源，"
            "按A2/A5核专业名归属和章程限制。"
        ),
    }


def validate_rows(rows):
    if len(rows) != 80:
        raise ValueError(f"expected 80 rows, got {len(rows)}")
    if len({row["高校官网辅证自动执行批次ID"] for row in rows}) != 80:
        raise ValueError("execution batch ids are not unique")
    if [as_int(row["执行批次序号"]) for row in rows] != list(range(1, 81)):
        raise ValueError("execution order must remain 1..80")
    if any(row[field] != "false" for row in rows for field in FALSE_FIELDS):
        raise ValueError("all public gates must remain false")
    if any(row["闭环阻断状态桶"] != "G0-PDF原页和湖北官方侧未闭环，禁止写回" for row in rows):
        raise ValueError("all rows must stay blocked until PDF and Hubei official review")


def validate_public_safety(rows, summary):
    text = json.dumps(summary, ensure_ascii=False) + "\n"
    text += "\n".join(",".join(str(row.get(field, "")) for field in FIELDS) for row in rows)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise ValueError(f"public output contains forbidden tokens: {hits}")


def main():
    rows = build_rows()
    summary = build_summary(rows)
    validate_rows(rows)
    validate_public_safety(rows, summary)
    write_csv(OUTPUT, rows, FIELDS)
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
