#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RAW_SOURCE_AUDIT = ROOT / "data/working/issue19-raw-major-source-evidence-audit.csv"
STABILITY_DASHBOARD = ROOT / "data/working/issue19-foundation-stability-dashboard.csv"
GAP_SCORECARD = ROOT / "data/working/issue19-foundation-closure-gap-scorecard.csv"
MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
P0_REVIEW_WORKLIST = ROOT / "data/working/issue19-p0-evidence-review-worklist.csv"

OUTPUT = ROOT / "data/working/issue19-major-source-evidence-risk-sidecar.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-major-source-evidence-risk-sidecar-summary.json"

DATA_STAGE = "issue19_major_source_evidence_risk_sidecar"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"


FIELDS = [
    "源证据风险侧账ID",
    "来源原始专业行源证据审计表",
    "来源底座稳定性总看板",
    "来源逐专业闭环缺口看板",
    "来源单一逐专业招生明细总工作台",
    "来源P0逐专业复核工作清单",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "专业行ID",
    "原始专业行源证据审计ID",
    "底座稳定性看板ID",
    "闭环缺口看板ID",
    "招生明细总工作台ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR短摘",
    "专业起始行号",
    "专业起始y",
    "OCR置信度",
    "源证据覆盖结论",
    "源证据风险等级",
    "源证据风险标签",
    "源证据下沉分层",
    "源证据核页优先级",
    "是否进入源证据优先核页清单",
    "建议核页原因",
    "私有OCR起始行匹配状态",
    "私有OCR起始行哈希与公开锚点一致",
    "私有OCR起始行专业代号匹配",
    "起始行QC_P0数",
    "起始行QC_P1数",
    "起始行QC规则ID集合",
    "公开页级manifest匹配状态",
    "私有页级manifest匹配状态",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "OCR识别行数",
    "OCR平均置信度",
    "OCR_QC_P0数",
    "OCR_QC_P1数",
    "低置信度页标记",
    "公开锚点匹配状态",
    "专业行原页证据锚点ID",
    "证据锚点状态",
    "起始行回连状态",
    "起始行专业代号匹配",
    "专业窗口行号范围",
    "合并证据窗口行号范围",
    "专业窗口行数",
    "合并证据窗口行数",
    "窗口文本SHA256",
    "窗口平均置信度",
    "窗口最低置信度",
    "私有窗口JSONL匹配状态",
    "私有窗口证据编号",
    "私有窗口SHA一致",
    "私有窗口页码一致",
    "私有窗口栏位一致",
    "私有窗口专业代号一致",
    "私有窗口专业行数",
    "私有窗口组上下文行数",
    "私有窗口状态一致",
    "底座稳定性等级",
    "闭环执行批次",
    "看板动作桶",
    "风险阻断等级",
    "PDF原页锚点状态",
    "PDF字段核验状态",
    "湖北官方平台字段核验状态",
    "字段缺口数",
    "字段缺口字段",
    "字段候选任务数",
    "非空字段候选数",
    "结构风险事件数",
    "最高结构风险等级",
    "结构风险类型集合",
    "三年投档稳定性状态",
    "同代码命中年份数",
    "家庭接受度结论",
    "同组调剂结论",
    "调剂影响等级",
    "首要核验动作",
    "闭环执行动作集合",
    "机器可辅助线索",
    "必须人工核PDF原页",
    "必须湖北官方系统或省招办计划核验",
    "必须家庭接受度确认",
    "必须同组调剂结论确认",
    "P0复核任务数",
    "P0证据项",
    "P0复核工作清单任务数",
    "P0复核工作清单ID集合",
    "P0复核证据项集合",
    "P0复核执行动作集合",
    "P0复核需要核验字段集合",
    "建议下钻入口",
    "源证据下沉结论",
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


def bool_text(value):
    return "true" if value else "false"


def ordered_join(values):
    seen = set()
    result = []
    for value in values:
        cleaned = str(value or "").strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return "；".join(result)


def index_by(rows, field):
    indexed = {}
    for row in rows:
        key = row.get(field, "")
        if key:
            indexed[key] = row
    return indexed


def source_bridge_layer(row):
    coverage = row.get("源证据覆盖结论", "")
    risk = row.get("源证据风险等级", "")
    if not coverage.startswith("S0-"):
        return "X0-源证据链路缺失阻断"
    if risk.startswith("R2-锚点窗口阻断"):
        return "X1-专业窗口P0先核"
    if risk.startswith("R2-起始行P0_QC"):
        return "X2-起始行P0_QC先核"
    if risk.startswith("R3-"):
        return "X3-源证据优先复核"
    return "X4-源证据低风险抽检但仍需三方闭环"


def source_review_priority(layer):
    if layer.startswith("X0-"):
        return "P0-源证据链路缺失阻断"
    if layer.startswith("X1-"):
        return "P0-专业窗口或锚点阻断先核"
    if layer.startswith("X2-"):
        return "P0-起始行QC先核"
    if layer.startswith("X3-"):
        return "P1-源证据优先复核"
    return "P3-低风险抽检但仍待三方闭环"


def source_review_reason(raw_row, layer):
    reasons = []
    risk = raw_row.get("源证据风险等级", "")
    if risk:
        reasons.append(risk)
    if raw_row.get("证据锚点状态", "").startswith("P0-"):
        reasons.append(raw_row.get("证据锚点状态", ""))
    if as_int(raw_row.get("起始行QC_P0数")) > 0:
        reasons.append(f"起始行QC_P0={raw_row.get('起始行QC_P0数')}")
    if raw_row.get("低置信度页标记") == "true":
        reasons.append("低置信度页")
    if layer.startswith("X4-") and not reasons:
        reasons.append("未触发起始行QC风险，但仍需PDF原页、湖北官方系统和高校官网/章程闭环")
    return ordered_join(reasons)


def drilldown_entry(row, p0_rows):
    entries = ["data/working/issue19-raw-major-source-evidence-audit.csv"]
    if p0_rows:
        entries.append("data/working/issue19-p0-evidence-review-worklist.csv")
    if as_int(row.get("字段缺口数")) > 0:
        entries.append("data/working/issue19-field-gap-repair-candidates.csv")
    entries.append("data/working/issue19-foundation-closure-gap-scorecard.csv")
    entries.append("data/working/issue19-foundation-stability-dashboard.csv")
    return "；".join(entries)


def build_rows():
    raw_rows = read_csv(RAW_SOURCE_AUDIT)
    stability_rows = read_csv(STABILITY_DASHBOARD)
    gap_rows = read_csv(GAP_SCORECARD)
    master_rows = read_csv(MASTER_WORKBENCH)
    p0_rows = read_csv(P0_REVIEW_WORKLIST)

    stability_by_major = index_by(stability_rows, "专业行ID")
    gap_by_major = index_by(gap_rows, "专业行ID")
    master_by_major = index_by(master_rows, "专业行ID")

    p0_by_major = defaultdict(list)
    for row in p0_rows:
        p0_by_major[row.get("专业行ID", "")].append(row)

    rows = []
    for raw_row in raw_rows:
        major_id = raw_row.get("专业行ID", "")
        stability_row = stability_by_major.get(major_id, {})
        gap_row = gap_by_major.get(major_id, {})
        master_row = master_by_major.get(major_id, {})
        p0_major_rows = p0_by_major.get(major_id, [])
        layer = source_bridge_layer(raw_row)
        enters_priority = not layer.startswith("X4-")

        row = {
            "源证据风险侧账ID": stable_id("SOURCERISK", [major_id, SOURCE_PDF_SHA256]),
            "来源原始专业行源证据审计表": "data/working/issue19-raw-major-source-evidence-audit.csv",
            "来源底座稳定性总看板": "data/working/issue19-foundation-stability-dashboard.csv",
            "来源逐专业闭环缺口看板": "data/working/issue19-foundation-closure-gap-scorecard.csv",
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源P0逐专业复核工作清单": "data/working/issue19-p0-evidence-review-worklist.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "专业行ID": major_id,
            "原始专业行源证据审计ID": raw_row.get("原始专业行源证据审计ID", ""),
            "底座稳定性看板ID": stability_row.get("底座稳定性看板ID", ""),
            "闭环缺口看板ID": gap_row.get("闭环缺口看板ID", ""),
            "招生明细总工作台ID": master_row.get("招生明细总工作台ID", ""),
            "专业组出现ID": raw_row.get("专业组出现ID", ""),
            "院校代码": raw_row.get("院校代码", ""),
            "院校名称OCR": raw_row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": raw_row.get("院校专业组代码OCR规范化", ""),
            "来源页码": raw_row.get("来源页码", ""),
            "版面列": raw_row.get("版面列", ""),
            "专业组内专业序号": raw_row.get("专业组内专业序号", ""),
            "专业代号OCR": raw_row.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": raw_row.get("专业名称及备注OCR短摘", ""),
            "专业起始行号": raw_row.get("专业起始行号", ""),
            "专业起始y": raw_row.get("专业起始y", ""),
            "OCR置信度": raw_row.get("OCR置信度", ""),
            "源证据覆盖结论": raw_row.get("源证据覆盖结论", ""),
            "源证据风险等级": raw_row.get("源证据风险等级", ""),
            "源证据风险标签": raw_row.get("源证据风险标签", ""),
            "源证据下沉分层": layer,
            "源证据核页优先级": source_review_priority(layer),
            "是否进入源证据优先核页清单": bool_text(enters_priority),
            "建议核页原因": source_review_reason(raw_row, layer),
            "私有OCR起始行匹配状态": raw_row.get("私有OCR起始行匹配状态", ""),
            "私有OCR起始行哈希与公开锚点一致": raw_row.get("私有OCR起始行哈希与公开锚点一致", ""),
            "私有OCR起始行专业代号匹配": raw_row.get("私有OCR起始行专业代号匹配", ""),
            "起始行QC_P0数": raw_row.get("起始行QC_P0数", ""),
            "起始行QC_P1数": raw_row.get("起始行QC_P1数", ""),
            "起始行QC规则ID集合": raw_row.get("起始行QC规则ID集合", ""),
            "公开页级manifest匹配状态": raw_row.get("公开页级manifest匹配状态", ""),
            "私有页级manifest匹配状态": raw_row.get("私有页级manifest匹配状态", ""),
            "私有页图证据编号": raw_row.get("私有页图证据编号", ""),
            "私有页图SHA256": raw_row.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": raw_row.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": raw_row.get("私有OCR文本SHA256", ""),
            "OCR识别行数": raw_row.get("OCR识别行数", ""),
            "OCR平均置信度": raw_row.get("OCR平均置信度", ""),
            "OCR_QC_P0数": raw_row.get("OCR_QC_P0数", ""),
            "OCR_QC_P1数": raw_row.get("OCR_QC_P1数", ""),
            "低置信度页标记": raw_row.get("低置信度页标记", ""),
            "公开锚点匹配状态": raw_row.get("公开锚点匹配状态", ""),
            "专业行原页证据锚点ID": raw_row.get("专业行原页证据锚点ID", ""),
            "证据锚点状态": raw_row.get("证据锚点状态", ""),
            "起始行回连状态": raw_row.get("起始行回连状态", ""),
            "起始行专业代号匹配": raw_row.get("起始行专业代号匹配", ""),
            "专业窗口行号范围": raw_row.get("专业窗口行号范围", ""),
            "合并证据窗口行号范围": raw_row.get("合并证据窗口行号范围", ""),
            "专业窗口行数": raw_row.get("专业窗口行数", ""),
            "合并证据窗口行数": raw_row.get("合并证据窗口行数", ""),
            "窗口文本SHA256": raw_row.get("窗口文本SHA256", ""),
            "窗口平均置信度": raw_row.get("窗口平均置信度", ""),
            "窗口最低置信度": raw_row.get("窗口最低置信度", ""),
            "私有窗口JSONL匹配状态": raw_row.get("私有窗口JSONL匹配状态", ""),
            "私有窗口证据编号": raw_row.get("私有窗口证据编号", ""),
            "私有窗口SHA一致": raw_row.get("私有窗口SHA一致", ""),
            "私有窗口页码一致": raw_row.get("私有窗口页码一致", ""),
            "私有窗口栏位一致": raw_row.get("私有窗口栏位一致", ""),
            "私有窗口专业代号一致": raw_row.get("私有窗口专业代号一致", ""),
            "私有窗口专业行数": raw_row.get("私有窗口专业行数", ""),
            "私有窗口组上下文行数": raw_row.get("私有窗口组上下文行数", ""),
            "私有窗口状态一致": raw_row.get("私有窗口状态一致", ""),
            "底座稳定性等级": stability_row.get("底座稳定性等级", ""),
            "闭环执行批次": gap_row.get("闭环执行批次", stability_row.get("闭环执行批次", "")),
            "看板动作桶": gap_row.get("看板动作桶", stability_row.get("看板动作桶", "")),
            "风险阻断等级": gap_row.get("风险阻断等级", stability_row.get("风险阻断等级", "")),
            "PDF原页锚点状态": stability_row.get("PDF原页锚点状态", ""),
            "PDF字段核验状态": stability_row.get("PDF字段核验状态", ""),
            "湖北官方平台字段核验状态": stability_row.get("湖北官方平台字段核验状态", ""),
            "字段缺口数": gap_row.get("字段缺口数", stability_row.get("字段缺口数", "")),
            "字段缺口字段": gap_row.get("字段缺口字段", stability_row.get("字段缺口字段", "")),
            "字段候选任务数": gap_row.get("字段候选任务数", stability_row.get("字段候选任务数", "")),
            "非空字段候选数": gap_row.get("非空字段候选数", stability_row.get("非空字段候选数", "")),
            "结构风险事件数": stability_row.get("结构风险事件数", ""),
            "最高结构风险等级": stability_row.get("最高结构风险等级", ""),
            "结构风险类型集合": stability_row.get("结构风险类型集合", ""),
            "三年投档稳定性状态": stability_row.get("三年投档稳定性状态", ""),
            "同代码命中年份数": stability_row.get("同代码命中年份数", ""),
            "家庭接受度结论": gap_row.get("家庭接受度结论", stability_row.get("家庭接受度结论", "")),
            "同组调剂结论": gap_row.get("同组调剂结论", stability_row.get("同组调剂结论", "")),
            "调剂影响等级": gap_row.get("调剂影响等级", stability_row.get("调剂影响等级", "")),
            "首要核验动作": gap_row.get("首要核验动作", ""),
            "闭环执行动作集合": gap_row.get("闭环执行动作集合", ""),
            "机器可辅助线索": gap_row.get("机器可辅助线索", ""),
            "必须人工核PDF原页": gap_row.get("必须人工核PDF原页", ""),
            "必须湖北官方系统或省招办计划核验": gap_row.get("必须湖北官方系统或省招办计划核验", ""),
            "必须家庭接受度确认": gap_row.get("必须家庭接受度确认", ""),
            "必须同组调剂结论确认": gap_row.get("必须同组调剂结论确认", ""),
            "P0复核任务数": gap_row.get("P0复核任务数", ""),
            "P0证据项": gap_row.get("P0证据项", ""),
            "P0复核工作清单任务数": str(len(p0_major_rows)),
            "P0复核工作清单ID集合": ordered_join(row.get("P0复核工作清单ID", "") for row in p0_major_rows),
            "P0复核证据项集合": ordered_join(row.get("证据项", "") for row in p0_major_rows),
            "P0复核执行动作集合": ordered_join(row.get("执行动作代码", "") for row in p0_major_rows),
            "P0复核需要核验字段集合": ordered_join(row.get("需要核验字段", "") for row in p0_major_rows),
            "建议下钻入口": drilldown_entry(gap_row or stability_row, p0_major_rows),
            "源证据下沉结论": "B0-源证据风险已下沉到逐专业侧账，仍需PDF原页、湖北官方系统和高校官网/章程闭环",
            "不得进入原因": "该侧账只用于原始证据定位、核页排序和风险解释；不得直接用于志愿推荐、录取概率或学校专业建议。",
            "下一步": "按源证据下沉分层、看板动作桶和P0复核工作清单逐专业核PDF原页，再回填湖北官方系统、省招办计划、高校官网/章程、家庭接受度和同组调剂结论。",
        }
        rows.append(row)

    return rows, {
        "raw_rows": raw_rows,
        "stability_rows": stability_rows,
        "gap_rows": gap_rows,
        "master_rows": master_rows,
        "p0_rows": p0_rows,
    }


def main():
    rows, sources = build_rows()
    write_csv(OUTPUT, rows, FIELDS)

    summary = {
        "status": "issue19_major_source_evidence_risk_sidecar_not_final",
        "generated_by": "build_issue19_major_source_evidence_risk_sidecar.py",
        "output_table": "data/working/issue19-major-source-evidence-risk-sidecar.csv",
        "row_grain": "逐专业招生明细",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_sidecar_id_count": len({row.get("源证据风险侧账ID") for row in rows}),
        "unique_major_line_id_count": len({row.get("专业行ID") for row in rows}),
        "source_counts": {
            "raw_source_audit_row_count": len(sources["raw_rows"]),
            "stability_dashboard_row_count": len(sources["stability_rows"]),
            "gap_scorecard_row_count": len(sources["gap_rows"]),
            "master_workbench_row_count": len(sources["master_rows"]),
            "p0_review_worklist_row_count": len(sources["p0_rows"]),
            "p0_review_worklist_major_line_count": len(
                {row.get("专业行ID") for row in sources["p0_rows"] if row.get("专业行ID")}
            ),
        },
        "join_match_counts": {
            "raw_source_audit_match_count": sum(1 for row in rows if row.get("原始专业行源证据审计ID")),
            "stability_dashboard_match_count": sum(1 for row in rows if row.get("底座稳定性看板ID")),
            "gap_scorecard_match_count": sum(1 for row in rows if row.get("闭环缺口看板ID")),
            "master_workbench_match_count": sum(1 for row in rows if row.get("招生明细总工作台ID")),
            "p0_review_worklist_major_line_count": sum(
                1 for row in rows if as_int(row.get("P0复核工作清单任务数")) > 0
            ),
        },
        "source_bridge_layer_counts": dict(Counter(row.get("源证据下沉分层") for row in rows)),
        "source_review_priority_counts": dict(Counter(row.get("源证据核页优先级") for row in rows)),
        "source_priority_review_major_line_count": sum(
            1 for row in rows if row.get("是否进入源证据优先核页清单") == "true"
        ),
        "source_low_risk_sample_major_line_count": sum(
            1 for row in rows if row.get("源证据下沉分层").startswith("X4-")
        ),
        "anchor_status_counts": dict(Counter(row.get("证据锚点状态") for row in rows)),
        "start_line_qc_p0_row_count": sum(1 for row in rows if as_int(row.get("起始行QC_P0数")) > 0),
        "start_line_qc_p1_row_count": sum(1 for row in rows if as_int(row.get("起始行QC_P1数")) > 0),
        "start_line_qc_p0_total_count": sum(as_int(row.get("起始行QC_P0数")) for row in rows),
        "start_line_qc_p1_total_count": sum(as_int(row.get("起始行QC_P1数")) for row in rows),
        "low_confidence_page_major_line_count": sum(
            1 for row in rows if row.get("低置信度页标记") == "true"
        ),
        "p0_review_worklist_task_total_count": sum(
            as_int(row.get("P0复核工作清单任务数")) for row in rows
        ),
        "p0_review_worklist_major_line_count": sum(
            1 for row in rows if as_int(row.get("P0复核工作清单任务数")) > 0
        ),
        "final_available_count": sum(1 for row in rows if row.get("最终可用") == "true"),
        "next_stage_available_count": sum(1 for row in rows if row.get("可进入下一阶段") == "true"),
        "auto_writeback_allowed_count": sum(
            1 for row in rows if row.get("机器是否允许自动写回主表") == "true"
        ),
        "recommendation_basis_allowed_count": sum(
            1 for row in rows if row.get("是否允许作为志愿推荐依据") == "true"
        ),
        "school_major_suggestion_allowed_count": sum(
            1 for row in rows if row.get("是否允许生成学校专业建议") == "true"
        ),
        "public_safety_note": "本产物只保存公开安全的证据编号、页码、行号、哈希、QC计数和状态；不保存私有OCR窗口原文、图片路径、登录态或个人身份信息。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出逐专业源证据风险侧账：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
