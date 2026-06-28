#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLING_GATES = ROOT / "data/working/issue19-official-unavailable-sampling-gates.csv"
AUTO_WORKBENCH = ROOT / "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv"
EVIDENCE_ROUTING = ROOT / "data/working/issue19-major-evidence-level-routing.csv"
ADMISSION_MASTER = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
LIVE_RECHECK = ROOT / "data/working/issue19-official-public-entry-live-recheck.json"
OUTPUT_CSV = ROOT / "data/working/issue19-official-unavailable-sampling-execution-detail.csv"
OUTPUT_SUMMARY = ROOT / "data/working/issue19-official-unavailable-sampling-execution-detail-summary.json"

HIGH_RISK_ACTIONS = {
    "C0-冲突先核PDF原页和湖北官方系统",
    "C1-官网补缺候选但禁止自动写回",
    "C7-官网源未匹配专业需人工确认专业名",
}
C2_ACTION = "C2-强辅证抽检并等待湖北官方闭环"
P3_ACTION = "P3-低风险抽检但非最终"

FIELDS = [
    "官方不可得抽样执行明细ID",
    "来源官方不可得抽样门禁ID",
    "来源稳定基座自动交叉核验任务ID",
    "来源逐专业证据路由ID",
    "来源招生明细总工作台ID",
    "来源湖北官方活体复查",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许写回字段事实",
    "执行类别",
    "执行优先级",
    "风险等级",
    "抽样策略",
    "样本选择原因",
    "样本序号",
    "样本最低明细数",
    "是否100%人工核验",
    "是否抽样核验",
    "是否低风险样本",
    "院校代码",
    "院校名称OCR",
    "专业行ID",
    "专业组出现ID",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "必核字段",
    "字段差异标记",
    "官网辅证自动动作",
    "OCR专业计划数候选",
    "OCR学费候选",
    "OCR再选科目候选",
    "最佳官网专业名称",
    "最佳官网专业代号",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "最佳官网来源文件",
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "疑似OCR把学费读入计划数",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方一致性状态",
    "字段事实写回状态",
    "是否需要双人复核",
    "升级触发器",
    "升级范围",
    "当前用途边界",
    "下一步",
]


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def page_side(row):
    page = str(row.get("来源页码", "")).strip()
    side = str(row.get("版面列", "")).strip()
    return f"{int(page):03d}-{side}" if page.isdigit() and side else f"{page}-{side}"


def deterministic_pick(rows, count):
    selected = []
    selected_ids = set()
    for field in ["来源页码", "专业组出现ID"]:
        first_by_key = {}
        for row in sorted(rows, key=lambda item: stable_id("C2SORT", [field, item.get("专业行ID", "")])):
            key = row.get(field, "")
            if key and key not in first_by_key:
                first_by_key[key] = row
        for key in sorted(first_by_key):
            row = first_by_key[key]
            major_id = row.get("专业行ID", "")
            if major_id not in selected_ids:
                selected.append(row)
                selected_ids.add(major_id)
            if len(selected) >= count:
                return selected
    for row in sorted(rows, key=lambda item: stable_id("C2FILL", [item.get("专业行ID", "")])):
        major_id = row.get("专业行ID", "")
        if major_id not in selected_ids:
            selected.append(row)
            selected_ids.add(major_id)
        if len(selected) >= count:
            break
    return selected


def gate_key(row):
    return (row.get("院校代码", ""), row.get("官网辅证自动动作", ""))


def is_double_review_required(action, row):
    return (
        action in {"C0-冲突先核PDF原页和湖北官方系统", "C7-官网源未匹配专业需人工确认专业名"}
        or row.get("疑似OCR把学费读入计划数") == "true"
        or row.get("计划数核验状态") == "mismatch"
    )


def from_auto_row(gate, row, sequence, sample_count):
    action = row.get("官网辅证自动动作", "")
    if action in HIGH_RISK_ACTIONS:
        category = "H0-高风险100%人工核验"
        priority = "00-高风险逐专业核验"
        is_100pct = "true"
        is_sample = "false"
        is_low = "false"
    else:
        category = "H1-C2强辅证抽样核验"
        priority = "10-强辅证抽样验收"
        is_100pct = "false"
        is_sample = "true"
        is_low = "false"
    return {
        "官方不可得抽样执行明细ID": stable_id(
            "SAMPLINGEXEC",
            [gate.get("官方不可得抽样门禁ID", ""), row.get("专业行ID", ""), action],
        ),
        "来源官方不可得抽样门禁ID": gate.get("官方不可得抽样门禁ID", ""),
        "来源稳定基座自动交叉核验任务ID": row.get("稳定基座自动交叉核验任务ID", ""),
        "来源逐专业证据路由ID": "",
        "来源招生明细总工作台ID": "",
        "来源湖北官方活体复查": "data/working/issue19-official-public-entry-live-recheck.json",
        "来源期号": row.get("来源期号", ""),
        "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
        "数据阶段": "issue19_official_unavailable_sampling_execution_detail",
        "主表粒度": "逐专业招生明细",
        "任务粒度": "官方不可得抽样门禁×逐专业招生明细",
        "最终可用": "false",
        "可进入下一阶段": "false",
        "是否允许作为志愿推荐依据": "false",
        "是否允许生成学校专业建议": "false",
        "是否允许自动写回主表": "false",
        "是否允许官网证据替代湖北官方计划": "false",
        "是否允许写回字段事实": "false",
        "执行类别": category,
        "执行优先级": priority,
        "风险等级": gate.get("风险等级", ""),
        "抽样策略": gate.get("抽样策略", ""),
        "样本选择原因": gate.get("样本选择原因", ""),
        "样本序号": str(sequence),
        "样本最低明细数": str(sample_count),
        "是否100%人工核验": is_100pct,
        "是否抽样核验": is_sample,
        "是否低风险样本": is_low,
        "院校代码": row.get("院校代码", ""),
        "院校名称OCR": row.get("院校名称OCR", ""),
        "专业行ID": row.get("专业行ID", ""),
        "专业组出现ID": row.get("专业组出现ID", ""),
        "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
        "来源页码": row.get("来源页码", ""),
        "版面列": row.get("版面列", ""),
        "页码版面键": page_side(row),
        "专业组内专业序号": row.get("专业组内专业序号", ""),
        "专业代号OCR": row.get("专业代号OCR", ""),
        "专业名称及备注短摘": row.get("专业名称及备注短摘", ""),
        "必核字段": gate.get("必核字段", ""),
        "字段差异标记": row.get("差异字段集合", "") or gate.get("字段差异标记", ""),
        "官网辅证自动动作": action,
        "OCR专业计划数候选": row.get("OCR专业计划数候选", ""),
        "OCR学费候选": row.get("OCR学费候选", ""),
        "OCR再选科目候选": row.get("OCR再选科目候选", ""),
        "最佳官网专业名称": row.get("最佳官网专业名称", ""),
        "最佳官网专业代号": row.get("最佳官网专业代号", ""),
        "最佳官网计划数": row.get("最佳官网计划数", ""),
        "最佳官网学费": row.get("最佳官网学费", ""),
        "最佳官网选科": row.get("最佳官网选科", ""),
        "最佳官网来源文件": row.get("最佳官网来源文件", ""),
        "官网证据强度": row.get("官网证据强度", ""),
        "官网来源状态": row.get("官网来源状态", ""),
        "官网证据匹配状态": row.get("官网证据匹配状态", ""),
        "计划数核验状态": row.get("计划数核验状态", ""),
        "疑似OCR把学费读入计划数": row.get("疑似OCR把学费读入计划数", ""),
        "PDF原页核页状态": row.get("PDF原页核页状态", ""),
        "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统核验状态", ""),
        "高校官网或招生章程辅证状态": row.get("官网辅证状态", ""),
        "三方一致性状态": "pending_pdf_hubei_school_consistency_review",
        "字段事实写回状态": row.get("字段写回状态", ""),
        "是否需要双人复核": "true" if is_double_review_required(action, row) else "false",
        "升级触发器": gate.get("升级触发器", ""),
        "升级范围": gate.get("升级范围", ""),
        "当前用途边界": "逐专业执行明细只用于人工核页、抽检和升级派单；不得作为志愿推荐或字段事实写回依据。",
        "下一步": row.get("下一步", "") or gate.get("下一步", ""),
    }


def from_p3_row(gate, routing_row, master_row, sequence):
    return {
        "官方不可得抽样执行明细ID": stable_id(
            "SAMPLINGEXEC",
            [gate.get("官方不可得抽样门禁ID", ""), gate.get("专业行ID", ""), P3_ACTION],
        ),
        "来源官方不可得抽样门禁ID": gate.get("官方不可得抽样门禁ID", ""),
        "来源稳定基座自动交叉核验任务ID": "",
        "来源逐专业证据路由ID": routing_row.get("逐专业证据路由ID", ""),
        "来源招生明细总工作台ID": master_row.get("招生明细总工作台ID", ""),
        "来源湖北官方活体复查": "data/working/issue19-official-public-entry-live-recheck.json",
        "来源期号": routing_row.get("来源期号", ""),
        "来源PDF_SHA256": routing_row.get("来源PDF_SHA256", ""),
        "数据阶段": "issue19_official_unavailable_sampling_execution_detail",
        "主表粒度": "逐专业招生明细",
        "任务粒度": "官方不可得抽样门禁×逐专业招生明细",
        "最终可用": "false",
        "可进入下一阶段": "false",
        "是否允许作为志愿推荐依据": "false",
        "是否允许生成学校专业建议": "false",
        "是否允许自动写回主表": "false",
        "是否允许官网证据替代湖北官方计划": "false",
        "是否允许写回字段事实": "false",
        "执行类别": "H2-P3低风险抽样验收",
        "执行优先级": "20-低风险抽样验收",
        "风险等级": gate.get("风险等级", ""),
        "抽样策略": gate.get("抽样策略", ""),
        "样本选择原因": gate.get("样本选择原因", ""),
        "样本序号": str(sequence),
        "样本最低明细数": "1",
        "是否100%人工核验": "false",
        "是否抽样核验": "true",
        "是否低风险样本": "true",
        "院校代码": routing_row.get("院校代码", ""),
        "院校名称OCR": routing_row.get("院校名称OCR", ""),
        "专业行ID": routing_row.get("专业行ID", ""),
        "专业组出现ID": routing_row.get("专业组出现ID", ""),
        "院校专业组代码OCR规范化": routing_row.get("院校专业组代码OCR规范化", ""),
        "来源页码": routing_row.get("来源页码", ""),
        "版面列": routing_row.get("版面列", ""),
        "页码版面键": page_side(routing_row),
        "专业组内专业序号": routing_row.get("专业组内专业序号", ""),
        "专业代号OCR": routing_row.get("专业代号OCR", ""),
        "专业名称及备注短摘": routing_row.get("专业名称及备注短摘", ""),
        "必核字段": gate.get("必核字段", ""),
        "字段差异标记": routing_row.get("官网差异字段集合", ""),
        "官网辅证自动动作": P3_ACTION,
        "OCR专业计划数候选": master_row.get("专业计划数OCR候选", ""),
        "OCR学费候选": master_row.get("学费OCR候选", ""),
        "OCR再选科目候选": master_row.get("再选科目OCR候选", ""),
        "最佳官网专业名称": "",
        "最佳官网专业代号": "",
        "最佳官网计划数": "",
        "最佳官网学费": "",
        "最佳官网选科": "",
        "最佳官网来源文件": "",
        "官网证据强度": "",
        "官网来源状态": routing_row.get("高校官网来源状态", ""),
        "官网证据匹配状态": routing_row.get("高校官网证据匹配状态", ""),
        "计划数核验状态": routing_row.get("高校官网计划数核验状态", ""),
        "疑似OCR把学费读入计划数": "false",
        "PDF原页核页状态": routing_row.get("PDF原页核验状态", ""),
        "湖北官方系统或省招办计划核验状态": routing_row.get("湖北官方系统核验状态", ""),
        "高校官网或招生章程辅证状态": routing_row.get("高校官网来源状态", ""),
        "三方一致性状态": "pending_pdf_hubei_school_consistency_review",
        "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
        "是否需要双人复核": "false",
        "升级触发器": gate.get("升级触发器", ""),
        "升级范围": gate.get("升级范围", ""),
        "当前用途边界": "低风险抽样只验证底座稳定性；不得作为志愿推荐或字段事实写回依据。",
        "下一步": routing_row.get("人工核验下一步", "") or gate.get("下一步", ""),
    }


def main():
    gates = read_csv(SAMPLING_GATES)
    auto_rows = read_csv(AUTO_WORKBENCH)
    routing_rows = read_csv(EVIDENCE_ROUTING)
    master_rows = read_csv(ADMISSION_MASTER)
    live_status = json.loads(LIVE_RECHECK.read_text(encoding="utf-8"))

    auto_by_gate = defaultdict(list)
    for row in auto_rows:
        auto_by_gate[(row.get("院校代码", ""), row.get("官网辅证自动动作", ""))].append(row)
    routing_by_id = {row.get("逐专业证据路由ID", ""): row for row in routing_rows}
    master_by_major = {row.get("专业行ID", ""): row for row in master_rows}

    output_rows = []
    for gate in gates:
        action = gate.get("官网辅证自动动作", "")
        if gate.get("来源类型") == "高校侧辅证刷新任务" and action in HIGH_RISK_ACTIONS:
            candidates = auto_by_gate.get(gate_key(gate), [])
            for sequence, row in enumerate(
                sorted(candidates, key=lambda item: (as_int(item.get("来源页码")), item.get("版面列", ""), as_int(item.get("专业组内专业序号")), item.get("专业行ID", ""))),
                start=1,
            ):
                output_rows.append(from_auto_row(gate, row, sequence, len(candidates)))
        elif gate.get("来源类型") == "高校侧辅证刷新任务" and action == C2_ACTION:
            candidates = auto_by_gate.get(gate_key(gate), [])
            sample_count = min(as_int(gate.get("样本最低明细数")), len(candidates))
            for sequence, row in enumerate(deterministic_pick(candidates, sample_count), start=1):
                output_rows.append(from_auto_row(gate, row, sequence, sample_count))
        elif gate.get("来源类型") == "P3低风险抽检专业明细":
            routing_row = routing_by_id.get(gate.get("来源逐专业证据路由ID", ""), {})
            master_row = master_by_major.get(gate.get("专业行ID", ""), {})
            output_rows.append(from_p3_row(gate, routing_row, master_row, 1))

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    action_counts = Counter(row["官网辅证自动动作"] for row in output_rows)
    category_counts = Counter(row["执行类别"] for row in output_rows)
    risk_counts = Counter(row["风险等级"] for row in output_rows)
    high_risk_count = sum(row["是否100%人工核验"] == "true" for row in output_rows)
    c2_sample_count = sum(row["官网辅证自动动作"] == C2_ACTION for row in output_rows)
    p3_sample_count = sum(row["官网辅证自动动作"] == P3_ACTION for row in output_rows)

    summary = {
        "status": "issue19_official_unavailable_sampling_execution_detail_not_final",
        "generated_by": "build_issue19_official_unavailable_sampling_execution_detail.py",
        "source_issue": "湖北招生考试2026年19期·本科普通批（下）",
        "source_pdf_sha256": output_rows[0]["来源PDF_SHA256"] if output_rows else "",
        "source_sampling_gates": "data/working/issue19-official-unavailable-sampling-gates.csv",
        "source_auto_workbench": "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv",
        "source_evidence_routing": "data/working/issue19-major-evidence-level-routing.csv",
        "source_admission_master": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_official_live_recheck": "data/working/issue19-official-public-entry-live-recheck.json",
        "official_live_recheck_can_finalize": live_status.get("current_conclusion", {}).get("can_finalize_admission_plan_from_public_entry"),
        "official_live_recheck_without_login_structured_plan_available": live_status.get("current_conclusion", {}).get("can_get_official_structured_plan_without_login"),
        "input_files": [
            {"path": "data/working/issue19-official-unavailable-sampling-gates.csv", "sha256": sha256(SAMPLING_GATES), "row_count": len(gates)},
            {"path": "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv", "sha256": sha256(AUTO_WORKBENCH), "row_count": len(auto_rows)},
            {"path": "data/working/issue19-major-evidence-level-routing.csv", "sha256": sha256(EVIDENCE_ROUTING), "row_count": len(routing_rows)},
            {"path": "data/working/issue19-admission-detail-master-workbench.csv", "sha256": sha256(ADMISSION_MASTER), "row_count": len(master_rows)},
            {"path": "data/working/issue19-official-public-entry-live-recheck.json", "sha256": sha256(LIVE_RECHECK)},
        ],
        "output_table": "data/working/issue19-official-unavailable-sampling-execution-detail.csv",
        "row_grain": "逐专业招生明细",
        "row_count": len(output_rows),
        "unique_execution_detail_id_count": len({row["官方不可得抽样执行明细ID"] for row in output_rows}),
        "unique_major_line_count": len({row["专业行ID"] for row in output_rows if row["专业行ID"]}),
        "high_risk_100pct_detail_count": high_risk_count,
        "c2_sample_detail_count": c2_sample_count,
        "p3_sample_detail_count": p3_sample_count,
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in output_rows),
        "action_counts": dict(action_counts),
        "execution_category_counts": dict(category_counts),
        "risk_level_counts": dict(risk_counts),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "policy": {
            "high_risk": f"C0/C1/C7 已展开到 {high_risk_count} 条逐专业明细，全部必须回第19期原页并核湖北官方侧。",
            "sampling": f"C2 强辅证抽 {c2_sample_count} 条逐专业明细，P3 低风险池抽 {p3_sample_count} 条逐专业明细。",
            "boundary": "本表只把任务下沉到可执行明细，仍不确认字段、不写回、不生成学校专业建议或志愿推荐。",
        },
    }
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
