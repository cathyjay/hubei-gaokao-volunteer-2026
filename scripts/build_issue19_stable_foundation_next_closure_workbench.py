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
ROUTING = ROOT / "data/working/issue19-major-evidence-level-routing.csv"
B0B1_SIDECAR = ROOT / "data/working/issue19-b0-b1-official-evidence-by-major-line.csv"
B0B1_DIFF = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
P0_FIELD = ROOT / "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv"
P0_PAGE_PROGRESS = ROOT / "data/working/issue19-p0-immediate-page-execution-progress-public-ledger.csv"
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

AUTO_OUTPUT = ROOT / "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv"
MANUAL_OUTPUT = ROOT / "data/working/issue19-stable-foundation-minimal-manual-closure-workbench.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-stable-foundation-next-closure-workbench-summary.json"

DATA_STAGE_AUTO = "issue19_stable_foundation_auto_official_crosscheck_workbench"
DATA_STAGE_MANUAL = "issue19_stable_foundation_minimal_manual_closure_workbench"

SOURCE_LABELS = {
    "stable_major": "data/working/issue19-stable-foundation-major-screening-view.csv",
    "stable_group": "data/working/issue19-stable-foundation-group-screening-view.csv",
    "routing": "data/working/issue19-major-evidence-level-routing.csv",
    "b0b1_sidecar": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
    "b0b1_diff": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
    "p0_field": "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv",
    "p0_page_progress": "data/working/issue19-p0-immediate-page-execution-progress-public-ledger.csv",
    "official_status": "data/working/issue19-official-public-entry-status.json",
}

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
]

AUTO_FIELDS = [
    "稳定基座自动交叉核验任务ID",
    "来源稳定基座逐专业筛选视图",
    "来源逐专业证据路由表",
    "来源B0B1高校官网证据旁挂表",
    "来源B0B1公开官网差异账",
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
    "OCR专业计划数候选",
    "OCR学费候选",
    "OCR再选科目候选",
    "稳定筛选机器线索等级",
    "稳定筛选下一步",
    "人工核验优先级",
    "人工核验强度",
    "自动官网核验可执行性",
    "官网证据强度",
    "官网证据说明",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "差异字段集合",
    "疑似OCR把学费读入计划数",
    "最佳官网来源文件",
    "最佳官网专业名称",
    "最佳官网专业代号",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "专业名称匹配方式",
    "专业名称匹配分",
    "官网辅证自动动作",
    "闭环优先级",
    "人工升级原因",
    "PDF原页核页状态",
    "湖北官方系统核验状态",
    "官网辅证状态",
    "字段写回状态",
    "公开安全策略",
    "下一步",
]

MANUAL_FIELDS = [
    "稳定基座最小人工闭环任务ID",
    "来源P0即时字段确认公开账本",
    "来源P0页列执行进度公开账本",
    "来源稳定基座逐专业筛选视图",
    "来源自动交叉核验工作台",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "P0即时字段确认公开账本ID",
    "P0字段即时复核任务ID",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "页码版面键",
    "字段名",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "人工核验泳道",
    "人工核验方式",
    "执行批次",
    "页列执行进度桶",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图规格SHA256",
    "裁图bbox归一化",
    "是否需要双人复核",
    "是否有高校字段线索",
    "是否裁图OCR与机器候选冲突",
    "是否裁图OCR与高校辅证冲突",
    "是否机器高校冲突",
    "高校官网证据强度",
    "高校官网证据匹配状态",
    "高校官网来源状态",
    "同专业官网辅证自动动作",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "最小人工闭环阶段",
    "人工必做步骤",
    "人工工作量压缩方式",
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


def evidence_action(strength, plan_status, source_status):
    if strength == "conflict_review":
        return "C0-冲突先核PDF原页和湖北官方系统"
    if strength == "fill_candidate":
        return "C1-官网补缺候选但禁止自动写回"
    if strength == "strong_support":
        return "C2-强辅证抽检并等待湖北官方闭环"
    if strength == "field_support":
        return "C3-字段辅证补充结构化后核原页"
    if strength == "partial_source":
        return "C4-已有部分来源需补结构化或补湖北行"
    if strength == "rules_only":
        return "C5-仅章程规则核特殊要求不能核计划数"
    if strength == "needs_source":
        return "C6-继续搜索高校官网2026湖北计划源"
    if strength == "unmatched":
        return "C7-官网源未匹配专业需人工确认专业名"
    if plan_status == "mismatch":
        return "C0-冲突先核PDF原页和湖北官方系统"
    if source_status == "needs_official_plan_source_search":
        return "C6-继续搜索高校官网2026湖北计划源"
    return "C8-保留辅证等待湖北官方闭环"


def action_priority(action):
    order = {
        "C0-冲突先核PDF原页和湖北官方系统": "00-P0冲突立即核",
        "C1-官网补缺候选但禁止自动写回": "01-P0补缺先核",
        "C7-官网源未匹配专业需人工确认专业名": "02-P1未匹配先核",
        "C2-强辅证抽检并等待湖北官方闭环": "03-P1强辅证抽检",
        "C3-字段辅证补充结构化后核原页": "04-P1字段辅证",
        "C4-已有部分来源需补结构化或补湖北行": "05-P1补结构化",
        "C5-仅章程规则核特殊要求不能核计划数": "06-P2规则核验",
        "C6-继续搜索高校官网2026湖北计划源": "07-P2补源",
    }
    return order.get(action, "08-P3留存等待")


def manual_upgrade_reason(row):
    strength = row.get("官网证据强度", "")
    plan_status = row.get("计划数核验状态", "")
    reasons = []
    if strength == "conflict_review" or plan_status == "mismatch":
        reasons.append("官网计划数与OCR候选冲突")
    if strength == "fill_candidate":
        reasons.append("OCR计划数字段缺口但官网有补缺线索")
    if row.get("疑似OCR把学费读入计划数") == "true":
        reasons.append("疑似把学费读成计划数")
    if strength == "unmatched":
        reasons.append("官网专业名称未能稳定匹配")
    if strength == "needs_source":
        reasons.append("缺高校官网2026湖北计划源")
    if strength == "rules_only":
        reasons.append("只有章程规则不能核计划数")
    if not reasons:
        reasons.append("高校官网只作辅证仍需PDF原页和湖北官方闭环")
    return "；".join(reasons)


def page_side_key(row):
    page = str(row.get("来源页码", "")).strip()
    side = str(row.get("版面列", "")).strip()
    if not page or not side:
        return ""
    try:
        page = f"{int(page):03d}"
    except ValueError:
        pass
    return f"{page}-{side}"


def compact_action_list(actions):
    filtered = [action for action in actions if action]
    if not filtered:
        return ""
    return "；".join(sorted(set(filtered), key=lambda value: action_priority(value)))


def build_auto_rows(stable_by_major, route_by_major, sidecar_rows):
    rows = []
    for idx, sidecar in enumerate(sidecar_rows, 1):
        major_id = sidecar.get("专业行ID", "")
        stable = stable_by_major.get(major_id, {})
        route = route_by_major.get(major_id, {})
        strength = sidecar.get("官网证据强度", "")
        plan_status = sidecar.get("计划数核验状态", "")
        source_status = sidecar.get("官网来源状态", "")
        action = evidence_action(strength, plan_status, source_status)
        row = {
            "稳定基座自动交叉核验任务ID": stable_id("STABLEAUTO", [major_id, idx, strength, plan_status]),
            "来源稳定基座逐专业筛选视图": SOURCE_LABELS["stable_major"],
            "来源逐专业证据路由表": SOURCE_LABELS["routing"],
            "来源B0B1高校官网证据旁挂表": SOURCE_LABELS["b0b1_sidecar"],
            "来源B0B1公开官网差异账": SOURCE_LABELS["b0b1_diff"],
            "来源湖北官方公开入口状态快照": SOURCE_LABELS["official_status"],
            "来源期号": sidecar.get("来源期号", stable.get("来源期号", "")),
            "来源PDF_SHA256": sidecar.get("来源PDF_SHA256", stable.get("来源PDF_SHA256", "")),
            "数据阶段": DATA_STAGE_AUTO,
            "主表粒度": "逐专业招生明细×高校官网辅证",
            **false_gate_values(),
            "专业行ID": major_id,
            "专业组出现ID": sidecar.get("专业组出现ID", stable.get("专业组出现ID", "")),
            "院校代码": sidecar.get("院校代码", stable.get("院校代码", "")),
            "院校名称OCR": sidecar.get("院校名称OCR", stable.get("院校名称OCR", "")),
            "院校专业组代码OCR规范化": sidecar.get(
                "院校专业组代码OCR规范化",
                stable.get("院校专业组代码OCR规范化", ""),
            ),
            "来源页码": sidecar.get("来源页码", stable.get("来源页码", "")),
            "版面列": stable.get("版面列", route.get("版面列", "")),
            "专业组内专业序号": sidecar.get("专业组内专业序号", stable.get("专业组内专业序号", "")),
            "专业代号OCR": sidecar.get("专业代号OCR", stable.get("专业代号OCR", "")),
            "专业名称及备注短摘": stable.get(
                "专业名称及备注短摘",
                sidecar.get("专业名称及备注OCR短摘", ""),
            ),
            "OCR专业计划数候选": stable.get("专业计划数OCR候选", sidecar.get("OCR计划数", "")),
            "OCR学费候选": stable.get("学费OCR候选", sidecar.get("OCR学费", "")),
            "OCR再选科目候选": stable.get("再选科目OCR候选", sidecar.get("OCR再选科目", "")),
            "稳定筛选机器线索等级": stable.get("机器初筛线索等级", ""),
            "稳定筛选下一步": stable.get("下一步", ""),
            "人工核验优先级": route.get("人工核验优先级", stable.get("人工核验优先级", "")),
            "人工核验强度": route.get("人工核验强度", stable.get("人工核验强度", "")),
            "自动官网核验可执行性": route.get("自动官网核验可执行性", stable.get("自动官网核验可执行性", "")),
            "官网证据强度": strength,
            "官网证据说明": sidecar.get("官网证据说明", ""),
            "官网来源状态": source_status,
            "官网证据匹配状态": sidecar.get("官网证据匹配状态", ""),
            "计划数核验状态": plan_status,
            "差异字段集合": sidecar.get("差异字段集合", ""),
            "疑似OCR把学费读入计划数": sidecar.get("疑似OCR把学费读入计划数", ""),
            "最佳官网来源文件": sidecar.get("最佳官网来源文件", ""),
            "最佳官网专业名称": sidecar.get("最佳官网专业名称", ""),
            "最佳官网专业代号": sidecar.get("最佳官网专业代号", ""),
            "最佳官网计划数": sidecar.get("最佳官网计划数", ""),
            "最佳官网学费": sidecar.get("最佳官网学费", ""),
            "最佳官网选科": sidecar.get("最佳官网选科", ""),
            "专业名称匹配方式": sidecar.get("专业名称匹配方式", ""),
            "专业名称匹配分": sidecar.get("专业名称匹配分", ""),
            "官网辅证自动动作": action,
            "闭环优先级": action_priority(action),
            "人工升级原因": manual_upgrade_reason(sidecar),
            "PDF原页核页状态": route.get("PDF原页核验状态", stable.get("PDF原页核验状态", "")),
            "湖北官方系统核验状态": route.get("湖北官方系统核验状态", stable.get("湖北官方系统核验状态", "")),
            "官网辅证状态": "school_official_evidence_sidecar_only_not_replacement",
            "字段写回状态": "blocked_until_pdf_hubei_official_review",
            "公开安全策略": "公开表只保存OCR候选、官网辅证、状态和来源文件相对路径；不保存私有OCR原文、截图路径、登录态或人工确认值。",
            "下一步": (
                f"{action}；必须回到PDF原页和湖北官方系统/省招办计划核验，"
                "高校官网不得替代湖北官方计划。"
            ),
        }
        rows.append(row)
    rows.sort(key=lambda row: (row["闭环优先级"], row["院校代码"], as_int(row["来源页码"]) or 9999, row["专业行ID"]))
    return rows


def build_manual_rows(stable_by_major, auto_actions_by_major, p0_field_rows, progress_by_page_side):
    rows = []
    for idx, task in enumerate(p0_field_rows, 1):
        major_id = task.get("专业行ID", "")
        stable = stable_by_major.get(major_id, {})
        key = task.get("页码版面键") or page_side_key(task)
        progress = progress_by_page_side.get(key, {})
        actions = auto_actions_by_major.get(major_id, [])
        double_review = task.get("是否需要双人复核", "")
        has_school = task.get("是否有高校字段线索", "")
        manual_steps = ["PDF原页逐字段读数"]
        manual_steps.append("湖北官方系统或省招办计划逐字段核验")
        if has_school == "true":
            manual_steps.append("高校官网或招生章程辅证核验")
        if double_review == "true":
            manual_steps.append("双人复核")
        row = {
            "稳定基座最小人工闭环任务ID": stable_id(
                "STABLEMANUAL",
                [task.get("P0字段即时复核任务ID", ""), major_id, task.get("字段名", "")],
            ),
            "来源P0即时字段确认公开账本": SOURCE_LABELS["p0_field"],
            "来源P0页列执行进度公开账本": SOURCE_LABELS["p0_page_progress"],
            "来源稳定基座逐专业筛选视图": SOURCE_LABELS["stable_major"],
            "来源自动交叉核验工作台": "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv",
            "来源湖北官方公开入口状态快照": SOURCE_LABELS["official_status"],
            "来源期号": task.get("来源期号", stable.get("来源期号", "")),
            "来源PDF_SHA256": task.get("来源PDF_SHA256", stable.get("来源PDF_SHA256", "")),
            "数据阶段": DATA_STAGE_MANUAL,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0字段×最小人工闭环",
            **false_gate_values(),
            "P0即时字段确认公开账本ID": task.get("P0即时字段确认公开账本ID", ""),
            "P0字段即时复核任务ID": task.get("P0字段即时复核任务ID", ""),
            "专业行ID": major_id,
            "专业组出现ID": task.get("专业组出现ID", stable.get("专业组出现ID", "")),
            "院校代码": task.get("院校代码", stable.get("院校代码", "")),
            "院校名称OCR": stable.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": stable.get("院校专业组代码OCR规范化", ""),
            "来源页码": task.get("来源页码", stable.get("来源页码", "")),
            "版面列": task.get("版面列", stable.get("版面列", "")),
            "页码版面键": key,
            "字段名": task.get("字段名", ""),
            "专业组内专业序号": stable.get("专业组内专业序号", ""),
            "专业代号OCR": stable.get("专业代号OCR", ""),
            "专业名称及备注短摘": stable.get("专业名称及备注短摘", ""),
            "人工核验泳道": task.get("人工核验泳道", ""),
            "人工核验方式": task.get("人工核验方式", ""),
            "执行批次": task.get("执行批次", ""),
            "页列执行进度桶": progress.get("页列执行进度桶", "R0-未开始PDF和湖北官方核验"),
            "裁图证据编号": task.get("裁图证据编号", ""),
            "裁图文件SHA256": task.get("裁图文件SHA256", ""),
            "裁图规格SHA256": task.get("裁图规格SHA256", ""),
            "裁图bbox归一化": task.get("裁图bbox归一化", ""),
            "是否需要双人复核": double_review,
            "是否有高校字段线索": has_school,
            "是否裁图OCR与机器候选冲突": task.get("是否裁图OCR与机器候选冲突", ""),
            "是否裁图OCR与高校辅证冲突": task.get("是否裁图OCR与高校辅证冲突", ""),
            "是否机器高校冲突": task.get("是否机器高校冲突", ""),
            "高校官网证据强度": task.get("高校官网证据强度", ""),
            "高校官网证据匹配状态": task.get("高校官网证据匹配状态", ""),
            "高校官网来源状态": task.get("高校官网来源状态", ""),
            "同专业官网辅证自动动作": compact_action_list(actions),
            "PDF原页核页状态": task.get("PDF原页核页状态", ""),
            "湖北官方系统或省招办计划核验状态": task.get("湖北官方系统或省招办计划核验状态", ""),
            "高校官网或招生章程辅证状态": task.get("高校官网或招生章程辅证状态", ""),
            "三方字段一致性状态": task.get("三方字段一致性状态", ""),
            "字段事实写回状态": task.get("字段事实写回状态", ""),
            "最小人工闭环阶段": "H0-P0即时字段核页",
            "人工必做步骤": "；".join(manual_steps),
            "人工工作量压缩方式": "按PDF页码×版面列集中核页，同一页列内字段一起完成；只公开状态不公开人工读数。",
            "公开安全策略": "公开表保存任务ID、证据SHA、bbox和状态；不保存图片路径、OCR原文、人工读数、登录态或个人信息。",
            "下一步": "先完成PDF原页读数，再等湖北官方系统/省招办计划字段核验；字段一致前不得写回主表。",
        }
        rows.append(row)
    rows.sort(key=lambda row: (row["执行批次"], as_int(row["来源页码"]) or 9999, row["版面列"], row["专业行ID"], row["字段名"]))
    return rows


def public_text_safe(paths):
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    return all(token not in text for token in FORBIDDEN_PUBLIC_TOKENS)


def main():
    stable_major_rows = read_csv(STABLE_MAJOR)
    route_rows = read_csv(ROUTING)
    sidecar_rows = read_csv(B0B1_SIDECAR)
    p0_field_rows = read_csv(P0_FIELD)
    p0_progress_rows = read_csv(P0_PAGE_PROGRESS)
    official_status = json.loads(OFFICIAL_STATUS.read_text(encoding="utf-8"))

    stable_by_major = {row.get("专业行ID", ""): row for row in stable_major_rows}
    route_by_major = {row.get("专业行ID", ""): row for row in route_rows}
    progress_by_page_side = {row.get("页码版面键", ""): row for row in p0_progress_rows}

    auto_rows = build_auto_rows(stable_by_major, route_by_major, sidecar_rows)
    auto_actions_by_major = defaultdict(list)
    for row in auto_rows:
        auto_actions_by_major[row.get("专业行ID", "")].append(row.get("官网辅证自动动作", ""))

    manual_rows = build_manual_rows(stable_by_major, auto_actions_by_major, p0_field_rows, progress_by_page_side)

    write_csv(AUTO_OUTPUT, auto_rows, AUTO_FIELDS)
    write_csv(MANUAL_OUTPUT, manual_rows, MANUAL_FIELDS)

    auto_action_counts = Counter(row.get("官网辅证自动动作") for row in auto_rows)
    auto_strength_counts = Counter(row.get("官网证据强度") for row in auto_rows)
    manual_field_counts = Counter(row.get("字段名") for row in manual_rows)
    manual_batch_counts = Counter(row.get("执行批次") for row in manual_rows)
    manual_progress_counts = Counter(row.get("页列执行进度桶") for row in manual_rows)

    summary = {
        "status": "issue19_stable_foundation_next_closure_workbench_not_final",
        "generated_by": "build_issue19_stable_foundation_next_closure_workbench.py",
        "source_issue": stable_major_rows[0].get("来源期号", "") if stable_major_rows else "",
        "source_pdf_sha256": stable_major_rows[0].get("来源PDF_SHA256", "") if stable_major_rows else "",
        "official_public_status_source": SOURCE_LABELS["official_status"],
        "official_public_plan_page_can_finalize": bool(
            official_status.get("official_plan_page", {}).get("can_finalize")
        ),
        "zspt_platform_can_finalize": bool(official_status.get("zspt_platform", {}).get("can_finalize")),
        "input_files": input_snapshot(
            ROOT,
            [
                STABLE_MAJOR,
                STABLE_GROUP,
                ROUTING,
                B0B1_SIDECAR,
                B0B1_DIFF,
                P0_FIELD,
                P0_PAGE_PROGRESS,
                OFFICIAL_STATUS,
            ],
        ),
        "auto_crosscheck_output_table": str(AUTO_OUTPUT.relative_to(ROOT)),
        "manual_closure_output_table": str(MANUAL_OUTPUT.relative_to(ROOT)),
        "auto_workbench_row_count": len(auto_rows),
        "manual_workbench_row_count": len(manual_rows),
        "unique_auto_task_id_count": len({row.get("稳定基座自动交叉核验任务ID") for row in auto_rows}),
        "unique_manual_task_id_count": len({row.get("稳定基座最小人工闭环任务ID") for row in manual_rows}),
        "unique_auto_major_line_id_count": len({row.get("专业行ID") for row in auto_rows}),
        "unique_manual_major_line_id_count": len({row.get("专业行ID") for row in manual_rows}),
        "unique_manual_page_side_count": len({row.get("页码版面键") for row in manual_rows}),
        "auto_action_counts": dict(auto_action_counts),
        "auto_evidence_strength_counts": dict(auto_strength_counts),
        "manual_field_counts": dict(manual_field_counts),
        "manual_execution_batch_counts": dict(manual_batch_counts),
        "manual_page_progress_bucket_counts": dict(manual_progress_counts),
        "manual_double_review_required_count": sum(1 for row in manual_rows if row.get("是否需要双人复核") == "true"),
        "manual_school_support_required_count": sum(1 for row in manual_rows if row.get("是否有高校字段线索") == "true"),
        "manual_crop_machine_conflict_count": sum(1 for row in manual_rows if row.get("是否裁图OCR与机器候选冲突") == "true"),
        "manual_crop_school_conflict_count": sum(1 for row in manual_rows if row.get("是否裁图OCR与高校辅证冲突") == "true"),
        "manual_machine_school_conflict_count": sum(1 for row in manual_rows if row.get("是否机器高校冲突") == "true"),
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "field_writeback_allowed_count": 0,
        "policy": {
            "official_boundary": "湖北官方公开结构化计划暂不可自动取得时，第19期PDF原页和后续湖北官方系统/省招办计划仍是最终闭环条件。",
            "school_evidence_boundary": "高校官网/API/PDF/附件/章程只作自动double-check、补缺候选和冲突发现，不能替代湖北官方计划。",
            "manual_compression": "人工核验优先压缩到P0即时字段：319个字段、148个页列，按页列集中核，不按全量13736行散扫。",
            "no_finalization": "本工作台不确认任何字段值，不自动写回主表，不生成学校专业建议。"
        },
        "next_steps": [
            "先处理C0冲突与C1补缺候选：回到PDF原页和湖北官方系统/省招办计划核验。",
            "并行继续补C4/C6高校官网2026湖北计划源，自动抓取后只生成diff。",
            "人工只在最小闭环表中记录私有读数和复核状态，公开层保持任务ID、SHA、bbox和状态。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not public_text_safe([AUTO_OUTPUT, MANUAL_OUTPUT, SUMMARY_OUTPUT]):
        raise SystemExit("公开输出命中禁止公开 token")


if __name__ == "__main__":
    main()
