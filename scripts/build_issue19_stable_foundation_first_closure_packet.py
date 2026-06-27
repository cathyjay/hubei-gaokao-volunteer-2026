#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]

AUTO_WORKBENCH = ROOT / "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv"
MANUAL_WORKBENCH = ROOT / "data/working/issue19-stable-foundation-minimal-manual-closure-workbench.csv"
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

DETAIL_OUTPUT = ROOT / "data/working/issue19-stable-foundation-first-closure-detail-packet.csv"
PAGE_SIDE_OUTPUT = ROOT / "data/working/issue19-stable-foundation-first-closure-page-side-packet.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-stable-foundation-first-closure-packet-summary.json"

DATA_STAGE_DETAIL = "issue19_stable_foundation_first_closure_detail_packet"
DATA_STAGE_PAGE_SIDE = "issue19_stable_foundation_first_closure_page_side_packet"

AUTO_PRIORITY_ACTIONS = {
    "C0-冲突先核PDF原页和湖北官方系统",
    "C1-官网补缺候选但禁止自动写回",
    "C7-官网源未匹配专业需人工确认专业名",
}

MANUAL_PRIORITY_BATCHES = {
    "EXEC-01-冲突异常立即核页",
    "EXEC-02-计划数偏大重点核页",
    "EXEC-03-高校辅证线索三方核验",
}

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

DETAIL_FIELDS = [
    "稳定基座第一闭环明细任务ID",
    "来源稳定基座自动官网辅证交叉核验工作台",
    "来源稳定基座最小人工闭环工作台",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "第一闭环批次",
    "第一闭环纳入原因",
    "任务来源类型",
    "来源自动交叉核验任务ID",
    "来源最小人工闭环任务ID",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "字段名",
    "官网辅证自动动作",
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "差异字段集合",
    "疑似OCR把学费读入计划数",
    "最佳官网来源文件",
    "OCR专业计划数候选",
    "最佳官网计划数",
    "OCR学费候选",
    "最佳官网学费",
    "OCR再选科目候选",
    "最佳官网选科",
    "人工升级原因",
    "P0字段即时复核任务ID",
    "P0即时字段确认公开账本ID",
    "执行批次",
    "人工核验泳道",
    "人工核验方式",
    "页列执行进度桶",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图bbox归一化",
    "是否需要双人复核",
    "是否有高校字段线索",
    "是否裁图OCR与机器候选冲突",
    "是否裁图OCR与高校辅证冲突",
    "是否机器高校冲突",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PAGE_SIDE_FIELDS = [
    "稳定基座第一闭环页列包ID",
    "来源第一闭环明细包",
    "来源稳定基座自动官网辅证交叉核验工作台",
    "来源稳定基座最小人工闭环工作台",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "第一闭环批次",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列总任务数",
    "自动官网辅证任务数",
    "P0人工字段任务数",
    "C0冲突任务数",
    "C1官网补缺任务数",
    "C7官网未匹配任务数",
    "EXEC01冲突异常字段数",
    "EXEC02计划数偏大字段数",
    "EXEC03高校辅证字段数",
    "涉及专业行数",
    "涉及字段任务数",
    "涉及院校代码数",
    "院校代码集合",
    "院校名称集合短摘",
    "专业行ID集合SHA256",
    "第一闭环明细任务ID集合SHA256",
    "自动交叉核验任务ID集合SHA256",
    "最小人工闭环任务ID集合SHA256",
    "P0字段即时复核任务ID集合SHA256",
    "是否含计划数冲突或补缺",
    "是否含P0人工字段任务",
    "是否需要双人复核",
    "第一闭环页列优先级",
    "页列执行状态",
    "人工必做步骤",
    "工作量压缩说明",
    "字段事实写回状态",
    "公开安全策略",
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
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
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


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def page_side_key(page, side):
    page = str(page or "").strip()
    side = str(side or "").strip()
    if not page or not side:
        return ""
    try:
        page = f"{int(page):03d}"
    except ValueError:
        pass
    return f"{page}-{side}"


def sha_list(values):
    normalized = "；".join(sorted({value for value in values if value}))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def join_limited(values, limit=8):
    result = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    if len(result) > limit:
        result = result[:limit] + [f"另{len(seen) - limit}项"]
    return "；".join(result)


def auto_detail_row(row):
    action = row.get("官网辅证自动动作", "")
    reason = {
        "C0-冲突先核PDF原页和湖北官方系统": "官网计划数与OCR候选冲突，第一批必须回页核",
        "C1-官网补缺候选但禁止自动写回": "OCR计划数缺口但官网有补缺线索，第一批回页核",
        "C7-官网源未匹配专业需人工确认专业名": "官网源未稳定匹配专业名，第一批确认专业归属",
    }.get(action, "第一批自动辅证核验")
    return {
        "稳定基座第一闭环明细任务ID": stable_id(
            "FIRSTDETAIL",
            ["auto", row.get("稳定基座自动交叉核验任务ID", "")],
        ),
        "来源稳定基座自动官网辅证交叉核验工作台": "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv",
        "来源稳定基座最小人工闭环工作台": "",
        "来源湖北官方公开入口状态快照": "data/working/issue19-official-public-entry-status.json",
        "来源期号": row.get("来源期号", ""),
        "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
        "数据阶段": DATA_STAGE_DETAIL,
        "主表粒度": "逐专业招生明细",
        "任务粒度": "逐专业招生明细×第一闭环自动官网辅证任务",
        "第一闭环批次": "FIRST-AUTO-C0-C1-C7",
        "第一闭环纳入原因": reason,
        "任务来源类型": "自动官网辅证任务",
        "来源自动交叉核验任务ID": row.get("稳定基座自动交叉核验任务ID", ""),
        "来源最小人工闭环任务ID": "",
        **false_gate_values(),
        "专业行ID": row.get("专业行ID", ""),
        "专业组出现ID": row.get("专业组出现ID", ""),
        "院校代码": row.get("院校代码", ""),
        "院校名称OCR": row.get("院校名称OCR", ""),
        "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
        "来源页码": row.get("来源页码", ""),
        "版面列": row.get("版面列", ""),
        "页码版面键": page_side_key(row.get("来源页码", ""), row.get("版面列", "")),
        "专业组内专业序号": row.get("专业组内专业序号", ""),
        "专业代号OCR": row.get("专业代号OCR", ""),
        "专业名称及备注短摘": row.get("专业名称及备注短摘", ""),
        "字段名": "",
        "官网辅证自动动作": action,
        "官网证据强度": row.get("官网证据强度", ""),
        "官网来源状态": row.get("官网来源状态", ""),
        "官网证据匹配状态": row.get("官网证据匹配状态", ""),
        "计划数核验状态": row.get("计划数核验状态", ""),
        "差异字段集合": row.get("差异字段集合", ""),
        "疑似OCR把学费读入计划数": row.get("疑似OCR把学费读入计划数", ""),
        "最佳官网来源文件": row.get("最佳官网来源文件", ""),
        "OCR专业计划数候选": row.get("OCR专业计划数候选", ""),
        "最佳官网计划数": row.get("最佳官网计划数", ""),
        "OCR学费候选": row.get("OCR学费候选", ""),
        "最佳官网学费": row.get("最佳官网学费", ""),
        "OCR再选科目候选": row.get("OCR再选科目候选", ""),
        "最佳官网选科": row.get("最佳官网选科", ""),
        "人工升级原因": row.get("人工升级原因", ""),
        "P0字段即时复核任务ID": "",
        "P0即时字段确认公开账本ID": "",
        "执行批次": "",
        "人工核验泳道": "",
        "人工核验方式": "",
        "页列执行进度桶": "",
        "裁图证据编号": "",
        "裁图文件SHA256": "",
        "裁图bbox归一化": "",
        "是否需要双人复核": "true" if action == "C0-冲突先核PDF原页和湖北官方系统" else "false",
        "是否有高校字段线索": "true",
        "是否裁图OCR与机器候选冲突": "",
        "是否裁图OCR与高校辅证冲突": "",
        "是否机器高校冲突": "",
        "PDF原页核页状态": row.get("PDF原页核页状态", ""),
        "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统核验状态", ""),
        "高校官网或招生章程辅证状态": row.get("官网辅证状态", ""),
        "三方字段一致性状态": "pending_pdf_hubei_school_consistency_review",
        "字段事实写回状态": row.get("字段写回状态", "blocked_until_pdf_hubei_official_review"),
        "公开安全策略": "公开表只保存任务、页列、OCR候选和官网辅证相对来源；不保存私有OCR原文、图片路径、人工读数或登录态。",
        "下一步": "第一批回到PDF原页核同专业行，再用湖北官方系统或省招办计划确认；官网只作辅证。",
    }


def manual_detail_row(row):
    return {
        "稳定基座第一闭环明细任务ID": stable_id(
            "FIRSTDETAIL",
            ["manual", row.get("P0字段即时复核任务ID", "")],
        ),
        "来源稳定基座自动官网辅证交叉核验工作台": "",
        "来源稳定基座最小人工闭环工作台": "data/working/issue19-stable-foundation-minimal-manual-closure-workbench.csv",
        "来源湖北官方公开入口状态快照": "data/working/issue19-official-public-entry-status.json",
        "来源期号": row.get("来源期号", ""),
        "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
        "数据阶段": DATA_STAGE_DETAIL,
        "主表粒度": "逐专业招生明细",
        "任务粒度": "逐专业招生明细×第一闭环P0人工字段任务",
        "第一闭环批次": "FIRST-MANUAL-EXEC01-EXEC03",
        "第一闭环纳入原因": row.get("执行批次", ""),
        "任务来源类型": "P0人工字段任务",
        "来源自动交叉核验任务ID": "",
        "来源最小人工闭环任务ID": row.get("稳定基座最小人工闭环任务ID", ""),
        **false_gate_values(),
        "专业行ID": row.get("专业行ID", ""),
        "专业组出现ID": row.get("专业组出现ID", ""),
        "院校代码": row.get("院校代码", ""),
        "院校名称OCR": row.get("院校名称OCR", ""),
        "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
        "来源页码": row.get("来源页码", ""),
        "版面列": row.get("版面列", ""),
        "页码版面键": row.get("页码版面键", "") or page_side_key(row.get("来源页码", ""), row.get("版面列", "")),
        "专业组内专业序号": row.get("专业组内专业序号", ""),
        "专业代号OCR": row.get("专业代号OCR", ""),
        "专业名称及备注短摘": row.get("专业名称及备注短摘", ""),
        "字段名": row.get("字段名", ""),
        "官网辅证自动动作": row.get("同专业官网辅证自动动作", ""),
        "官网证据强度": row.get("高校官网证据强度", ""),
        "官网来源状态": row.get("高校官网来源状态", ""),
        "官网证据匹配状态": row.get("高校官网证据匹配状态", ""),
        "计划数核验状态": "",
        "差异字段集合": "",
        "疑似OCR把学费读入计划数": "",
        "最佳官网来源文件": "",
        "OCR专业计划数候选": "",
        "最佳官网计划数": "",
        "OCR学费候选": "",
        "最佳官网学费": "",
        "OCR再选科目候选": "",
        "最佳官网选科": "",
        "人工升级原因": row.get("人工必做步骤", ""),
        "P0字段即时复核任务ID": row.get("P0字段即时复核任务ID", ""),
        "P0即时字段确认公开账本ID": row.get("P0即时字段确认公开账本ID", ""),
        "执行批次": row.get("执行批次", ""),
        "人工核验泳道": row.get("人工核验泳道", ""),
        "人工核验方式": row.get("人工核验方式", ""),
        "页列执行进度桶": row.get("页列执行进度桶", ""),
        "裁图证据编号": row.get("裁图证据编号", ""),
        "裁图文件SHA256": row.get("裁图文件SHA256", ""),
        "裁图bbox归一化": row.get("裁图bbox归一化", ""),
        "是否需要双人复核": row.get("是否需要双人复核", ""),
        "是否有高校字段线索": row.get("是否有高校字段线索", ""),
        "是否裁图OCR与机器候选冲突": row.get("是否裁图OCR与机器候选冲突", ""),
        "是否裁图OCR与高校辅证冲突": row.get("是否裁图OCR与高校辅证冲突", ""),
        "是否机器高校冲突": row.get("是否机器高校冲突", ""),
        "PDF原页核页状态": row.get("PDF原页核页状态", ""),
        "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统或省招办计划核验状态", ""),
        "高校官网或招生章程辅证状态": row.get("高校官网或招生章程辅证状态", ""),
        "三方字段一致性状态": row.get("三方字段一致性状态", ""),
        "字段事实写回状态": row.get("字段事实写回状态", ""),
        "公开安全策略": "公开表保存任务ID、字段名、页列、证据SHA和状态；不保存图片路径、人工读数、OCR原文或登录态。",
        "下一步": "按页列集中看PDF原页，记录私有人工读数；再用湖北官方系统或省招办计划核验字段。",
    }


def page_side_priority(counter):
    if counter["C0-冲突先核PDF原页和湖北官方系统"] or counter["EXEC-01-冲突异常立即核页"]:
        return "Q0-冲突页列第一批先核"
    if counter["C1-官网补缺候选但禁止自动写回"] or counter["EXEC-02-计划数偏大重点核页"]:
        return "Q1-补缺或计划数偏大页列先核"
    if counter["C7-官网源未匹配专业需人工确认专业名"] or counter["EXEC-03-高校辅证线索三方核验"]:
        return "Q2-官网未匹配或高校辅证页列先核"
    return "Q3-第一闭环保留页列"


def build_page_side_rows(detail_rows):
    grouped = defaultdict(list)
    for row in detail_rows:
        grouped[row.get("页码版面键", "")].append(row)

    rows = []
    for key, group in grouped.items():
        counters = Counter()
        for row in group:
            if row.get("任务来源类型") == "自动官网辅证任务":
                counters["auto"] += 1
                counters[row.get("官网辅证自动动作", "")] += 1
            if row.get("任务来源类型") == "P0人工字段任务":
                counters["manual"] += 1
                counters[row.get("执行批次", "")] += 1
        first = group[0]
        major_ids = [row.get("专业行ID", "") for row in group]
        detail_ids = [row.get("稳定基座第一闭环明细任务ID", "") for row in group]
        auto_ids = [
            row.get("来源自动交叉核验任务ID", "") for row in group
            if row.get("来源自动交叉核验任务ID", "")
        ]
        manual_ids = [
            row.get("来源最小人工闭环任务ID", "") for row in group
            if row.get("来源最小人工闭环任务ID", "")
        ]
        p0_task_ids = [
            row.get("P0字段即时复核任务ID", "") for row in group
            if row.get("P0字段即时复核任务ID", "")
        ]
        needs_double = any(row.get("是否需要双人复核") == "true" for row in group)
        has_plan_conflict_or_fill = bool(
            counters["C0-冲突先核PDF原页和湖北官方系统"]
            or counters["C1-官网补缺候选但禁止自动写回"]
            or counters["EXEC-01-冲突异常立即核页"]
            or counters["EXEC-02-计划数偏大重点核页"]
        )
        row = {
            "稳定基座第一闭环页列包ID": stable_id("FIRSTPAGE", [key]),
            "来源第一闭环明细包": "data/working/issue19-stable-foundation-first-closure-detail-packet.csv",
            "来源稳定基座自动官网辅证交叉核验工作台": "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv",
            "来源稳定基座最小人工闭环工作台": "data/working/issue19-stable-foundation-minimal-manual-closure-workbench.csv",
            "来源湖北官方公开入口状态快照": "data/working/issue19-official-public-entry-status.json",
            "来源期号": first.get("来源期号", ""),
            "来源PDF_SHA256": first.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE_PAGE_SIDE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×第一闭环核验包",
            "第一闭环批次": "FIRST-CLOSURE-PAGE-SIDE",
            **false_gate_values(),
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "页码版面键": key,
            "页列总任务数": str(len(group)),
            "自动官网辅证任务数": str(counters["auto"]),
            "P0人工字段任务数": str(counters["manual"]),
            "C0冲突任务数": str(counters["C0-冲突先核PDF原页和湖北官方系统"]),
            "C1官网补缺任务数": str(counters["C1-官网补缺候选但禁止自动写回"]),
            "C7官网未匹配任务数": str(counters["C7-官网源未匹配专业需人工确认专业名"]),
            "EXEC01冲突异常字段数": str(counters["EXEC-01-冲突异常立即核页"]),
            "EXEC02计划数偏大字段数": str(counters["EXEC-02-计划数偏大重点核页"]),
            "EXEC03高校辅证字段数": str(counters["EXEC-03-高校辅证线索三方核验"]),
            "涉及专业行数": str(len(set(major_ids))),
            "涉及字段任务数": str(len(p0_task_ids)),
            "涉及院校代码数": str(len({row.get("院校代码", "") for row in group if row.get("院校代码", "")})),
            "院校代码集合": join_limited([row.get("院校代码", "") for row in group], 12),
            "院校名称集合短摘": join_limited([row.get("院校名称OCR", "") for row in group], 8),
            "专业行ID集合SHA256": sha_list(major_ids),
            "第一闭环明细任务ID集合SHA256": sha_list(detail_ids),
            "自动交叉核验任务ID集合SHA256": sha_list(auto_ids),
            "最小人工闭环任务ID集合SHA256": sha_list(manual_ids),
            "P0字段即时复核任务ID集合SHA256": sha_list(p0_task_ids),
            "是否含计划数冲突或补缺": "true" if has_plan_conflict_or_fill else "false",
            "是否含P0人工字段任务": "true" if counters["manual"] else "false",
            "是否需要双人复核": "true" if needs_double else "false",
            "第一闭环页列优先级": page_side_priority(counters),
            "页列执行状态": "R0-未开始第一闭环核页",
            "人工必做步骤": "PDF原页核页；湖北官方系统或省招办计划核验；高校官网只作辅证；冲突或补缺项双人复核",
            "工作量压缩说明": "按PDF页码×版面列集中核验，同页列自动官网任务和P0字段任务一起处理。",
            "字段事实写回状态": "blocked_until_pdf_hubei_official_private_review",
            "公开安全策略": "公开表只保存页列计数、任务集合SHA、院校短摘和状态；不保存图片路径、人工读数、OCR原文或登录态。",
            "下一步": "先处理本页列内所有第一闭环明细任务，再回写私有核验状态；公开层保持非最终门禁。",
        }
        rows.append(row)
    rows.sort(key=lambda row: (
        row.get("第一闭环页列优先级", ""),
        -(as_int(row.get("页列总任务数")) or 0),
        as_int(row.get("来源页码")) or 9999,
        row.get("版面列", ""),
    ))
    return rows


def public_text_safe(paths):
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    return all(token not in text for token in FORBIDDEN_PUBLIC_TOKENS)


def main():
    auto_rows = read_csv(AUTO_WORKBENCH)
    manual_rows = read_csv(MANUAL_WORKBENCH)
    official_status = json.loads(OFFICIAL_STATUS.read_text(encoding="utf-8"))

    detail_rows = [
        auto_detail_row(row)
        for row in auto_rows
        if row.get("官网辅证自动动作", "") in AUTO_PRIORITY_ACTIONS
    ]
    detail_rows.extend(
        manual_detail_row(row)
        for row in manual_rows
        if row.get("执行批次", "") in MANUAL_PRIORITY_BATCHES
    )
    detail_rows.sort(key=lambda row: (
        row.get("第一闭环批次", ""),
        row.get("页码版面键", ""),
        row.get("院校代码", ""),
        row.get("专业行ID", ""),
        row.get("字段名", ""),
    ))
    page_side_rows = build_page_side_rows(detail_rows)

    write_csv(DETAIL_OUTPUT, detail_rows, DETAIL_FIELDS)
    write_csv(PAGE_SIDE_OUTPUT, page_side_rows, PAGE_SIDE_FIELDS)

    summary = {
        "status": "issue19_stable_foundation_first_closure_packet_not_final",
        "generated_by": "build_issue19_stable_foundation_first_closure_packet.py",
        "source_issue": detail_rows[0].get("来源期号", "") if detail_rows else "",
        "source_pdf_sha256": detail_rows[0].get("来源PDF_SHA256", "") if detail_rows else "",
        "official_public_status_source": "data/working/issue19-official-public-entry-status.json",
        "official_public_plan_page_can_finalize": bool(
            official_status.get("official_plan_page", {}).get("can_finalize")
        ),
        "zspt_platform_can_finalize": bool(official_status.get("zspt_platform", {}).get("can_finalize")),
        "input_files": input_snapshot(ROOT, [AUTO_WORKBENCH, MANUAL_WORKBENCH, OFFICIAL_STATUS]),
        "detail_output_table": str(DETAIL_OUTPUT.relative_to(ROOT)),
        "page_side_output_table": str(PAGE_SIDE_OUTPUT.relative_to(ROOT)),
        "detail_row_count": len(detail_rows),
        "page_side_row_count": len(page_side_rows),
        "unique_detail_task_id_count": len({row.get("稳定基座第一闭环明细任务ID") for row in detail_rows}),
        "unique_major_line_id_count": len({row.get("专业行ID") for row in detail_rows}),
        "unique_pdf_page_count": len({row.get("来源页码") for row in detail_rows}),
        "unique_page_side_count": len({row.get("页码版面键") for row in detail_rows}),
        "auto_priority_detail_count": sum(1 for row in detail_rows if row.get("任务来源类型") == "自动官网辅证任务"),
        "manual_priority_detail_count": sum(1 for row in detail_rows if row.get("任务来源类型") == "P0人工字段任务"),
        "auto_action_counts": dict(Counter(row.get("官网辅证自动动作") for row in detail_rows if row.get("任务来源类型") == "自动官网辅证任务")),
        "manual_execution_batch_counts": dict(Counter(row.get("执行批次") for row in detail_rows if row.get("任务来源类型") == "P0人工字段任务")),
        "page_side_priority_counts": dict(Counter(row.get("第一闭环页列优先级") for row in page_side_rows)),
        "page_side_with_auto_and_manual_count": sum(
            1 for row in page_side_rows
            if as_int(row.get("自动官网辅证任务数")) and as_int(row.get("P0人工字段任务数"))
        ),
        "page_side_with_plan_conflict_or_fill_count": sum(
            1 for row in page_side_rows if row.get("是否含计划数冲突或补缺") == "true"
        ),
        "page_side_with_double_review_count": sum(
            1 for row in page_side_rows if row.get("是否需要双人复核") == "true"
        ),
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "field_writeback_allowed_count": 0,
        "policy": {
            "scope": "第一闭环批次只纳入C0/C1/C7官网辅证任务和EXEC-01/02/03 P0字段任务。",
            "manual_compression": "205条明细任务压缩到36个页列、32个PDF页，按页列集中核验。",
            "official_boundary": "第19期PDF原页和湖北官方系统/省招办计划仍是字段事实闭环条件；高校官网不能替代湖北官方计划。",
            "no_finalization": "本批次不确认任何字段值，不自动写回主表，不生成学校专业建议。"
        },
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not public_text_safe([DETAIL_OUTPUT, PAGE_SIDE_OUTPUT, SUMMARY_OUTPUT]):
        raise SystemExit("公开输出命中禁止公开 token")


if __name__ == "__main__":
    main()
