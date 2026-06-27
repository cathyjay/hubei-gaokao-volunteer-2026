#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FOUNDATION_RELEASE = ROOT / "data/working/issue19-major-detail-foundation-release.csv"
GAP_SCORECARD = ROOT / "data/working/issue19-foundation-closure-gap-scorecard.csv"
PDF_ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
HISTORICAL_SIDECAR = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar.csv"

OUTPUT = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-admission-detail-master-workbench-summary.json"

DATA_STAGE = "issue19_admission_detail_master_workbench"


FIELDS = [
    "招生明细总工作台ID",
    "来源统一逐专业底座入口",
    "来源逐专业闭环缺口看板",
    "来源专业行原页证据锚点表",
    "来源三年投档线索旁挂表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "最终志愿排序门禁",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR",
    "专业名称及备注短摘",
    "是否真实招生明细",
    "是否0明细占位",
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "学费OCR候选",
    "再选科目人工确认",
    "专业计划数人工确认",
    "学费人工确认",
    "字段缺口数",
    "字段缺口字段",
    "字段候选任务数",
    "非空字段候选数",
    "有候选字段",
    "字段候选来源分布",
    "PDF原页证据状态",
    "专业行原页证据锚点ID",
    "原页证据锚点状态",
    "专业起始行号",
    "专业起始y",
    "专业窗口行号范围",
    "合并证据窗口行号范围",
    "合并证据窗口行数",
    "窗口平均置信度",
    "窗口最低置信度",
    "窗口坐标摘要",
    "窗口文本SHA256",
    "起始行回连状态",
    "起始行专业代号匹配",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "私有窗口证据编号",
    "公开安全策略",
    "湖北官方核验包任务ID",
    "湖北官方平台字段核验状态",
    "湖北官方系统证据状态",
    "高校官网/章程辅证状态",
    "高校官网来源状态",
    "高校官网证据匹配状态",
    "高校官网计划数核验状态",
    "B0B1官网证据任务数",
    "B0B1官网证据强度",
    "B0B1计划数状态",
    "B0B1官网建议动作",
    "官网证据能否替代湖北官方计划",
    "家庭接受度核验状态",
    "家庭接受度结论",
    "机器专业接受度初判",
    "机器阻断或待核原因",
    "调剂影响初判",
    "调剂影响等级",
    "同组调剂结论",
    "同组真实招生明细数",
    "同组偏好专业数",
    "同组医学护理排除专业数",
    "同组高收费或超预算专业数",
    "同组特殊限制待核专业数",
    "专业偏好方向",
    "专业风险类型",
    "风险阻断等级",
    "闭环执行批次",
    "看板动作桶",
    "看板排序分",
    "首要核验动作",
    "闭环执行动作集合",
    "机器可辅助线索",
    "必须人工核PDF原页",
    "必须湖北官方系统或省招办计划核验",
    "必须家庭接受度确认",
    "必须同组调剂结论确认",
    "三年投档稳定性状态",
    "2023同代码命中",
    "2023投档分",
    "2023等位分差",
    "2024同代码命中",
    "2024投档分",
    "2024等位分差",
    "2025同代码命中",
    "2025投档分",
    "2025等位分差",
    "同代码命中年份数",
    "同代码命中年份",
    "三年投档分范围",
    "等位分差摘要",
    "三年再选要求规范集合",
    "再选要求是否跨年变化",
    "历史院校专业组名称是否疑似不一致",
    "历史投档代码是否重复",
    "2026同代码专业组是否重复出现",
    "稳定性分层",
    "历史线使用口径",
    "底座使用边界",
    "底座保真门禁",
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


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def by_major_id(rows):
    return {row.get("专业行ID", ""): row for row in rows}


def take(row, field):
    return row.get(field, "")


def build_rows():
    foundation_rows = read_csv(FOUNDATION_RELEASE)
    gap_by_major = by_major_id(read_csv(GAP_SCORECARD))
    anchor_by_major = by_major_id(read_csv(PDF_ANCHORS))
    history_by_major = by_major_id(read_csv(HISTORICAL_SIDECAR))

    rows = []
    join_missing = Counter()
    for foundation in foundation_rows:
        major_id = take(foundation, "专业行ID")
        gap = gap_by_major.get(major_id, {})
        anchor = anchor_by_major.get(major_id, {})
        history = history_by_major.get(major_id, {})
        if not gap:
            join_missing["gap_scorecard"] += 1
        if not anchor:
            join_missing["pdf_anchor"] += 1
        if not history:
            join_missing["historical_sidecar"] += 1

        rows.append({
            "招生明细总工作台ID": stable_id("ADMISSIONDETAIL", [major_id]),
            "来源统一逐专业底座入口": "data/working/issue19-major-detail-foundation-release.csv",
            "来源逐专业闭环缺口看板": "data/working/issue19-foundation-closure-gap-scorecard.csv",
            "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
            "来源三年投档线索旁挂表": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
            "来源期号": take(foundation, "来源期号"),
            "来源PDF_SHA256": take(foundation, "来源PDF_SHA256"),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "最终志愿排序门禁": take(foundation, "最终志愿排序门禁"),
            "专业行ID": major_id,
            "专业组出现ID": take(foundation, "专业组出现ID"),
            "院校代码": take(foundation, "院校代码"),
            "院校名称OCR": take(foundation, "院校名称OCR"),
            "院校专业组代码OCR规范化": take(foundation, "院校专业组代码OCR规范化"),
            "来源页码": take(foundation, "来源页码"),
            "版面列": take(foundation, "版面列"),
            "专业组内专业序号": take(foundation, "专业组内专业序号"),
            "专业代号OCR": take(foundation, "专业代号OCR"),
            "专业名称及备注OCR": take(foundation, "专业名称及备注OCR"),
            "专业名称及备注短摘": take(foundation, "专业名称及备注短摘"),
            "是否真实招生明细": take(foundation, "是否真实招生明细"),
            "是否0明细占位": take(foundation, "是否0明细占位"),
            "再选科目OCR候选": take(foundation, "再选科目OCR候选"),
            "专业计划数OCR候选": take(foundation, "专业计划数OCR候选"),
            "学费OCR候选": take(foundation, "学费OCR候选"),
            "再选科目人工确认": take(foundation, "再选科目人工确认"),
            "专业计划数人工确认": take(foundation, "专业计划数人工确认"),
            "学费人工确认": take(foundation, "学费人工确认"),
            "字段缺口数": take(foundation, "字段缺口数"),
            "字段缺口字段": take(foundation, "字段缺口字段"),
            "字段候选任务数": take(gap, "字段候选任务数"),
            "非空字段候选数": take(gap, "非空字段候选数"),
            "有候选字段": take(gap, "有候选字段"),
            "字段候选来源分布": take(gap, "字段候选来源分布"),
            "PDF原页证据状态": take(foundation, "PDF原页证据状态"),
            "专业行原页证据锚点ID": take(anchor, "专业行原页证据锚点ID"),
            "原页证据锚点状态": take(anchor, "证据锚点状态"),
            "专业起始行号": take(anchor, "专业起始行号"),
            "专业起始y": take(anchor, "专业起始y"),
            "专业窗口行号范围": take(anchor, "专业窗口行号范围"),
            "合并证据窗口行号范围": take(anchor, "合并证据窗口行号范围"),
            "合并证据窗口行数": take(anchor, "合并证据窗口行数"),
            "窗口平均置信度": take(anchor, "窗口平均置信度"),
            "窗口最低置信度": take(anchor, "窗口最低置信度"),
            "窗口坐标摘要": take(anchor, "窗口坐标摘要"),
            "窗口文本SHA256": take(anchor, "窗口文本SHA256"),
            "起始行回连状态": take(anchor, "起始行回连状态"),
            "起始行专业代号匹配": take(anchor, "起始行专业代号匹配"),
            "私有页图证据编号": take(anchor, "私有页图证据编号"),
            "私有页图SHA256": take(anchor, "私有页图SHA256"),
            "私有OCR文本证据编号": take(anchor, "私有OCR文本证据编号"),
            "私有OCR文本SHA256": take(anchor, "私有OCR文本SHA256"),
            "私有窗口证据编号": take(anchor, "私有窗口证据编号"),
            "公开安全策略": take(anchor, "公开安全策略"),
            "湖北官方核验包任务ID": take(foundation, "湖北官方核验包任务ID"),
            "湖北官方平台字段核验状态": take(foundation, "湖北官方平台字段核验状态"),
            "湖北官方系统证据状态": take(foundation, "湖北官方系统证据状态"),
            "高校官网/章程辅证状态": take(foundation, "高校官网/章程辅证状态"),
            "高校官网来源状态": take(foundation, "高校官网来源状态"),
            "高校官网证据匹配状态": take(foundation, "高校官网证据匹配状态"),
            "高校官网计划数核验状态": take(foundation, "高校官网计划数核验状态"),
            "B0B1官网证据任务数": take(gap, "B0B1官网证据任务数"),
            "B0B1官网证据强度": take(gap, "B0B1官网证据强度"),
            "B0B1计划数状态": take(gap, "B0B1计划数状态"),
            "B0B1官网建议动作": take(gap, "B0B1官网建议动作"),
            "官网证据能否替代湖北官方计划": take(gap, "官网证据能否替代湖北官方计划"),
            "家庭接受度核验状态": take(foundation, "家庭接受度核验状态"),
            "家庭接受度结论": take(foundation, "家庭接受度结论"),
            "机器专业接受度初判": take(foundation, "机器专业接受度初判"),
            "机器阻断或待核原因": take(foundation, "机器阻断或待核原因"),
            "调剂影响初判": take(foundation, "调剂影响初判"),
            "调剂影响等级": take(foundation, "调剂影响等级"),
            "同组调剂结论": take(foundation, "同组调剂结论"),
            "同组真实招生明细数": take(foundation, "同组真实招生明细数"),
            "同组偏好专业数": take(foundation, "同组偏好专业数"),
            "同组医学护理排除专业数": take(foundation, "同组医学护理排除专业数"),
            "同组高收费或超预算专业数": take(foundation, "同组高收费或超预算专业数"),
            "同组特殊限制待核专业数": take(foundation, "同组特殊限制待核专业数"),
            "专业偏好方向": take(foundation, "专业偏好方向"),
            "专业风险类型": take(foundation, "专业风险类型"),
            "风险阻断等级": take(gap, "风险阻断等级"),
            "闭环执行批次": take(gap, "闭环执行批次"),
            "看板动作桶": take(gap, "看板动作桶"),
            "看板排序分": take(gap, "看板排序分"),
            "首要核验动作": take(gap, "首要核验动作"),
            "闭环执行动作集合": take(gap, "闭环执行动作集合"),
            "机器可辅助线索": take(gap, "机器可辅助线索"),
            "必须人工核PDF原页": take(gap, "必须人工核PDF原页"),
            "必须湖北官方系统或省招办计划核验": take(gap, "必须湖北官方系统或省招办计划核验"),
            "必须家庭接受度确认": take(gap, "必须家庭接受度确认"),
            "必须同组调剂结论确认": take(gap, "必须同组调剂结论确认"),
            "三年投档稳定性状态": take(gap, "三年投档稳定性状态"),
            "2023同代码命中": take(history, "2023同代码命中"),
            "2023投档分": take(history, "2023投档分"),
            "2023等位分差": take(history, "2023等位分差"),
            "2024同代码命中": take(history, "2024同代码命中"),
            "2024投档分": take(history, "2024投档分"),
            "2024等位分差": take(history, "2024等位分差"),
            "2025同代码命中": take(history, "2025同代码命中"),
            "2025投档分": take(history, "2025投档分"),
            "2025等位分差": take(history, "2025等位分差"),
            "同代码命中年份数": take(history, "同代码命中年份数"),
            "同代码命中年份": take(history, "同代码命中年份"),
            "三年投档分范围": take(history, "三年投档分范围"),
            "等位分差摘要": take(history, "等位分差摘要"),
            "三年再选要求规范集合": take(history, "三年再选要求规范集合"),
            "再选要求是否跨年变化": take(history, "再选要求是否跨年变化"),
            "历史院校专业组名称是否疑似不一致": take(history, "历史院校专业组名称是否疑似不一致"),
            "历史投档代码是否重复": take(history, "历史投档代码是否重复"),
            "2026同代码专业组是否重复出现": take(history, "2026同代码专业组是否重复出现"),
            "稳定性分层": take(history, "稳定性分层"),
            "历史线使用口径": take(history, "历史线使用口径"),
            "底座使用边界": take(foundation, "底座使用边界"),
            "底座保真门禁": take(foundation, "底座保真门禁"),
            "不得进入原因": take(foundation, "不得进入原因"),
            "下一步": "以本行招生明细为默认讨论对象；确认前不得进入最终志愿排序或替代官方填报系统。",
        })

    return rows, join_missing


def main():
    rows, join_missing = build_rows()
    write_csv(OUTPUT, rows, FIELDS)

    summary = {
        "status": "issue19_admission_detail_master_workbench_not_final",
        "generated_by": "build_issue19_admission_detail_master_workbench.py",
        "output_table": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_foundation_release": "data/working/issue19-major-detail-foundation-release.csv",
        "source_gap_scorecard": "data/working/issue19-foundation-closure-gap-scorecard.csv",
        "source_pdf_anchors": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "source_historical_sidecar": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
        "row_grain_contract": "one_row_per_admission_major_detail",
        "row_count": len(rows),
        "unique_workbench_id_count": len({row["招生明细总工作台ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "missing_join_counts": dict(join_missing),
        "gap_scorecard_join_count": sum(1 for row in rows if row.get("闭环执行批次")),
        "pdf_anchor_join_count": sum(1 for row in rows if row.get("专业行原页证据锚点ID")),
        "historical_sidecar_join_count": sum(1 for row in rows if row.get("同代码命中年份数")),
        "final_available_count": sum(row.get("最终可用") == "true" for row in rows),
        "next_stage_available_count": sum(row.get("可进入下一阶段") == "true" for row in rows),
        "official_replace_allowed_count": sum(
            row.get("官网证据能否替代湖北官方计划") == "true" for row in rows
        ),
        "action_bucket_counts": dict(Counter(row.get("看板动作桶") for row in rows)),
        "pdf_anchor_status_counts": dict(Counter(row.get("原页证据锚点状态") for row in rows)),
        "historical_hit_year_count_distribution": dict(
            Counter(row.get("同代码命中年份数") for row in rows)
        ),
        "historical_stability_layer_counts": dict(Counter(row.get("稳定性分层") for row in rows)),
        "field_candidate_major_count": sum(as_int(row.get("非空字段候选数")) > 0 for row in rows),
        "b0_b1_evidence_major_count": sum(as_int(row.get("B0B1官网证据任务数")) > 0 for row in rows),
        "must_pdf_review_count": sum(row.get("必须人工核PDF原页") == "true" for row in rows),
        "must_hubei_official_review_count": sum(
            row.get("必须湖北官方系统或省招办计划核验") == "true" for row in rows
        ),
        "must_family_review_count": sum(row.get("必须家庭接受度确认") == "true" for row in rows),
        "must_transfer_review_count": sum(row.get("必须同组调剂结论确认") == "true" for row in rows),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
