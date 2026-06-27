#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FILTER_PREP = ROOT / "data/working/issue19-candidate-filter-prep-major-detail.csv"
MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
STRUCTURAL_REGISTER = ROOT / "data/working/issue19-admission-detail-structural-fidelity-register.csv"

OUTPUT = ROOT / "data/working/issue19-major-decision-readiness-gates.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-major-decision-readiness-gates-summary.json"

DATA_STAGE = "issue19_major_decision_readiness_gates"

FIELDS = [
    "决策闸门ID",
    "来源候选筛选准备表",
    "来源单一逐专业招生明细总工作台",
    "来源结构保真登记表",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "初筛讨论用途",
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
    "候选初筛闸门状态",
    "机器预筛线索等级",
    "初筛动作桶",
    "可参考字段集合",
    "阻断闸门集合",
    "城市闸门",
    "城市字段状态",
    "城市候选",
    "城市偏好命中",
    "办学属性闸门",
    "办学属性核验状态",
    "公办民办初判",
    "费用闸门",
    "学费OCR候选",
    "学费OCR数字候选",
    "是否超预算机器初判",
    "专业方向闸门",
    "专业偏好方向",
    "结构保真闸门",
    "结构保真优先级",
    "结构保真风险标签",
    "PDF原页闸门",
    "PDF字段核验状态",
    "湖北官方闸门",
    "湖北官方系统字段核验状态",
    "高校官网闸门",
    "高校官网/章程字段核验状态",
    "官网证据能否替代湖北官方计划",
    "家庭接受度闸门",
    "家庭接受度核验状态",
    "家庭接受度结论",
    "调剂闸门",
    "调剂影响等级",
    "同组调剂结论",
    "同组真实招生明细数",
    "同组偏好专业数",
    "同组医学护理排除专业数",
    "同组高收费或超预算专业数",
    "同组特殊限制待核专业数",
    "历史投档闸门",
    "三年投档稳定性状态",
    "同代码命中年份数",
    "稳定性分层",
    "字段缺口闸门",
    "字段缺口数",
    "字段缺口字段",
    "下一步核验动作",
    "不得进入原因",
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


def join_labels(labels):
    clean = [label for label in labels if label]
    return "；".join(dict.fromkeys(clean)) if clean else ""


def city_gate(row):
    if row.get("城市字段状态") == "machine_school_name_keyword_unverified":
        return "城市仅院校名称OCR关键词线索-需核学校所在地和实际校区"
    return "学校所在地和实际校区待核-不得按城市直接取舍"


def tuition_gate(row):
    flag = row.get("是否超预算机器初判", "")
    if flag == "true":
        return "学费OCR超预算线索-默认不进主方案并待官方核验"
    if flag == "false":
        return "学费OCR数字未超预算线索-仍需官方计划或章程核验"
    return "学费字段待核-不得用于预算放行"


def professional_gate(row):
    if row.get("专业偏好方向"):
        return "专业方向关键词命中-可排专业研究和逐字段核验"
    return "未命中当前偏好方向-待专业了解和家庭确认"


def structural_gate(row):
    priority = row.get("结构保真优先级", "")
    if priority.startswith("R0"):
        return "结构边界阻断-先核PDF原页和组边界"
    if priority.startswith("R1"):
        return "归属或结构异常-先核专业是否属于该组"
    if priority.startswith("R2"):
        return "原页上下文补证-核组标题和专业窗口"
    return "结构常规抽检-仍需PDF原页闭环"


def school_source_gate(row):
    status = row.get("高校官网/章程字段核验状态", "") or row.get("高校官网/章程辅证状态", "")
    if status == "has_reusable_2026_hubei_plan_source":
        return "已有高校官网湖北计划辅证-不能替代湖北官方计划"
    if status in {"has_partial_source_needs_followup", "charter_or_rules_only_no_plan"}:
        return "高校官网或章程仅部分辅证-需继续补源"
    if "冲突" in status:
        return "高校官网辅证存在冲突-优先核PDF原页和湖北官方系统"
    return "高校官网或章程辅证待补-不能替代湖北官方计划"


def historical_gate(row):
    years = as_int(row.get("同代码命中年份数"))
    if years == 0:
        return "三年同代码未命中-需按2026计划和相邻代码另核"
    if years < 3:
        return f"三年同代码命中{years}年-仅作风险线索"
    return "三年同代码命中3年-仍需核计划变化后再用"


def field_gap_gate(row):
    count = as_int(row.get("字段缺口数"))
    if count:
        return "存在计划数/学费/选科等字段缺口-先补字段"
    return "机器未发现计划数/学费/选科字段缺口-仍需官方核验"


def make_reference_fields(filter_row, master_row):
    labels = []
    if filter_row.get("专业偏好方向"):
        labels.append("专业方向关键词")
    if filter_row.get("城市偏好命中") == "true":
        labels.append("城市名称关键词")
    if filter_row.get("是否超预算机器初判") in {"true", "false"}:
        labels.append("学费OCR数字线索")
    if as_int(master_row.get("非空字段候选数")):
        labels.append("字段候选线索")
    if master_row.get("高校官网/章程辅证状态") != "not_yet_school_source_searched_in_full_workbench":
        labels.append("高校官网/章程辅证线索")
    if as_int(master_row.get("同代码命中年份数")):
        labels.append("三年同代码投档线索")
    return join_labels(labels) or "暂无可直接参考机器线索"


def make_blocking_gates(filter_row, master_row, structure_row):
    labels = []
    priority = structure_row.get("结构保真优先级", "")
    if priority.startswith(("R0", "R1", "R2")):
        labels.append("结构保真未闭环")
    if master_row.get("PDF原页证据状态") != "pdf_original_review_completed":
        labels.append("PDF原页待核")
    if master_row.get("湖北官方平台字段核验状态") != "hubei_official_plan_review_completed":
        labels.append("湖北官方系统待核")
    if filter_row.get("办学属性核验状态") == "pending_school_attribute_review":
        labels.append("办学属性待核")
    if filter_row.get("城市字段状态") != "school_location_confirmed":
        labels.append("学校所在地/校区待核")
    if filter_row.get("是否超预算机器初判") == "true":
        labels.append("费用超预算线索")
    if filter_row.get("是否超预算机器初判") == "pending_tuition_field_review":
        labels.append("学费字段待核")
    if master_row.get("家庭接受度核验状态") != "family_acceptance_completed":
        labels.append("家庭接受度待核")
    if master_row.get("同组调剂结论") != "group_transfer_decision_completed":
        labels.append("同组调剂结论待核")
    if as_int(master_row.get("字段缺口数")):
        labels.append("计划/学费/选科字段缺口")
    if filter_row.get("机器专业接受度初判", "").startswith("默认不能接受"):
        labels.append("家庭底线默认不接受线索")
    return join_labels(labels)


def action_bucket(filter_row, master_row, structure_row):
    priority = structure_row.get("结构保真优先级", "")
    if priority.startswith(("R0", "R1")):
        return "D0-结构归属和PDF原页先核"
    if filter_row.get("机器专业接受度初判", "").startswith("默认不能接受"):
        return "D1-家庭底线风险先确认"
    if as_int(master_row.get("字段缺口数")):
        return "D2-计划学费选科字段先补"
    if filter_row.get("专业偏好方向"):
        return "D3-偏好专业线索优先核"
    if filter_row.get("城市偏好命中") == "true":
        return "D4-城市偏好线索待位置核"
    if filter_row.get("调剂影响等级") and filter_row.get("调剂影响等级") != "待家庭确认":
        return "D5-调剂风险先核"
    return "D6-常规留存待了解"


def readiness_status(filter_row, master_row, structure_row):
    bucket = action_bucket(filter_row, master_row, structure_row)
    if bucket.startswith("D0"):
        return "G0-结构或归属未闭环"
    if bucket.startswith("D1"):
        return "G1-家庭底线风险待确认"
    if bucket.startswith("D2"):
        return "G2-字段缺口未闭环"
    if bucket.startswith(("D3", "D4", "D5")):
        return "G3-可作机器预筛线索但不可定案"
    return "G4-常规留存但不可定案"


def signal_level(status):
    if status.startswith("G0"):
        return "仅排核验顺序-结构闭环前不作候选"
    if status.startswith("G1"):
        return "仅排风险确认-默认不进主方案"
    if status.startswith("G2"):
        return "仅排字段补证-补齐前不作候选"
    if status.startswith("G3"):
        return "可作机器预筛线索-不得定案"
    return "低优先留存-不得定案"


def next_action(filter_row, master_row, structure_row):
    return join_labels([
        "回看PDF原页" if "PDF" in make_blocking_gates(filter_row, master_row, structure_row) else "",
        "核湖北官方系统或省招办计划",
        "补学校官网/章程辅证" if "高校官网" in school_source_gate(master_row) else "",
        "核办学属性/公办民办/校区",
        "逐专业确认家庭接受度",
        "整组确认是否服从调剂",
    ])


def main():
    filter_rows = read_csv(FILTER_PREP)
    master_by_major = by_major_id(read_csv(MASTER_WORKBENCH))
    structure_by_major = by_major_id(read_csv(STRUCTURAL_REGISTER))

    rows = []
    missing_join = Counter()
    for filter_row in filter_rows:
        major_id = filter_row.get("专业行ID", "")
        master_row = master_by_major.get(major_id, {})
        structure_row = structure_by_major.get(major_id, {})
        if not master_row:
            missing_join["master_workbench"] += 1
        if not structure_row:
            missing_join["structural_register"] += 1

        status = readiness_status(filter_row, master_row, structure_row)
        blockers = make_blocking_gates(filter_row, master_row, structure_row)
        row = {
            "决策闸门ID": stable_id("DECISIONGATE", [major_id]),
            "来源候选筛选准备表": "data/working/issue19-candidate-filter-prep-major-detail.csv",
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源结构保真登记表": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
            "来源期号": filter_row.get("来源期号", ""),
            "来源PDF_SHA256": filter_row.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "初筛讨论用途": "仅用于机器预筛、核验排序和家庭讨论准备；不产生报考结论",
            "专业行ID": major_id,
            "专业组出现ID": filter_row.get("专业组出现ID", ""),
            "院校代码": filter_row.get("院校代码", ""),
            "院校名称OCR": filter_row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": filter_row.get("院校专业组代码OCR规范化", ""),
            "来源页码": filter_row.get("来源页码", ""),
            "版面列": filter_row.get("版面列", ""),
            "专业组内专业序号": filter_row.get("专业组内专业序号", ""),
            "专业代号OCR": filter_row.get("专业代号OCR", ""),
            "专业名称及备注短摘": filter_row.get("专业名称及备注短摘", ""),
            "候选初筛闸门状态": status,
            "机器预筛线索等级": signal_level(status),
            "初筛动作桶": action_bucket(filter_row, master_row, structure_row),
            "可参考字段集合": make_reference_fields(filter_row, master_row),
            "阻断闸门集合": blockers,
            "城市闸门": city_gate(filter_row),
            "城市字段状态": filter_row.get("城市字段状态", ""),
            "城市候选": filter_row.get("城市候选", ""),
            "城市偏好命中": filter_row.get("城市偏好命中", ""),
            "办学属性闸门": "办学属性/公办民办全部待官方或章程核验",
            "办学属性核验状态": filter_row.get("办学属性核验状态", ""),
            "公办民办初判": filter_row.get("公办民办初判", ""),
            "费用闸门": tuition_gate(filter_row),
            "学费OCR候选": filter_row.get("学费OCR候选", ""),
            "学费OCR数字候选": filter_row.get("学费OCR数字候选", ""),
            "是否超预算机器初判": filter_row.get("是否超预算机器初判", ""),
            "专业方向闸门": professional_gate(filter_row),
            "专业偏好方向": filter_row.get("专业偏好方向", ""),
            "结构保真闸门": structural_gate(structure_row),
            "结构保真优先级": structure_row.get("结构保真优先级", ""),
            "结构保真风险标签": structure_row.get("结构保真风险标签", ""),
            "PDF原页闸门": "PDF原页待人工核验；页图哈希不能替代字段确认",
            "PDF字段核验状态": filter_row.get("PDF字段核验状态", ""),
            "湖北官方闸门": "湖北官方系统或省招办计划未核前不得进入志愿排序",
            "湖北官方系统字段核验状态": filter_row.get("湖北官方系统字段核验状态", ""),
            "高校官网闸门": school_source_gate(master_row),
            "高校官网/章程字段核验状态": filter_row.get("高校官网/章程字段核验状态", ""),
            "官网证据能否替代湖北官方计划": master_row.get("官网证据能否替代湖北官方计划", ""),
            "家庭接受度闸门": "逐专业家庭接受度未确认",
            "家庭接受度核验状态": master_row.get("家庭接受度核验状态", ""),
            "家庭接受度结论": master_row.get("家庭接受度结论", ""),
            "调剂闸门": "同组完整专业接受度和服从调剂结论未确认",
            "调剂影响等级": filter_row.get("调剂影响等级", ""),
            "同组调剂结论": master_row.get("同组调剂结论", ""),
            "同组真实招生明细数": filter_row.get("同组真实招生明细数", ""),
            "同组偏好专业数": filter_row.get("同组偏好专业数", ""),
            "同组医学护理排除专业数": filter_row.get("同组医学护理排除专业数", ""),
            "同组高收费或超预算专业数": filter_row.get("同组高收费或超预算专业数", ""),
            "同组特殊限制待核专业数": filter_row.get("同组特殊限制待核专业数", ""),
            "历史投档闸门": historical_gate(master_row),
            "三年投档稳定性状态": filter_row.get("三年投档稳定性状态", ""),
            "同代码命中年份数": master_row.get("同代码命中年份数", ""),
            "稳定性分层": filter_row.get("稳定性分层", ""),
            "字段缺口闸门": field_gap_gate(master_row),
            "字段缺口数": master_row.get("字段缺口数", ""),
            "字段缺口字段": master_row.get("字段缺口字段", ""),
            "下一步核验动作": next_action(filter_row, master_row, structure_row),
            "不得进入原因": "任何行都尚未完成PDF原页、湖北官方系统、办学属性、家庭接受度和同组调剂闭环；不得进入志愿排序",
        }
        rows.append(row)

    write_csv(OUTPUT, rows, FIELDS)

    blockers = Counter()
    references = Counter()
    for row in rows:
        for label in row["阻断闸门集合"].split("；"):
            if label:
                blockers[label] += 1
        for label in row["可参考字段集合"].split("；"):
            if label:
                references[label] += 1

    summary = {
        "status": "issue19_major_decision_readiness_gates_not_final",
        "generated_by": "build_issue19_major_decision_readiness_gates.py",
        "output_table": "data/working/issue19-major-decision-readiness-gates.csv",
        "source_filter_prep": "data/working/issue19-candidate-filter-prep-major-detail.csv",
        "source_master_workbench": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_structural_register": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
        "row_count": len(rows),
        "unique_gate_id_count": len({row["决策闸门ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "missing_join_counts": dict(missing_join),
        "readiness_status_counts": dict(Counter(row["候选初筛闸门状态"] for row in rows)),
        "signal_level_counts": dict(Counter(row["机器预筛线索等级"] for row in rows)),
        "action_bucket_counts": dict(Counter(row["初筛动作桶"] for row in rows)),
        "blocking_gate_counts": dict(blockers),
        "reference_field_counts": dict(references),
        "city_gate_counts": dict(Counter(row["城市闸门"] for row in rows)),
        "school_attribute_gate_counts": dict(Counter(row["办学属性核验状态"] for row in rows)),
        "tuition_gate_counts": dict(Counter(row["费用闸门"] for row in rows)),
        "pdf_field_review_status_counts": dict(Counter(row["PDF字段核验状态"] for row in rows)),
        "hubei_official_field_review_status_counts": dict(Counter(row["湖北官方系统字段核验状态"] for row in rows)),
        "school_source_review_status_counts": dict(Counter(row["高校官网/章程字段核验状态"] for row in rows)),
        "family_acceptance_status_counts": dict(Counter(row["家庭接受度核验状态"] for row in rows)),
        "transfer_decision_status_counts": dict(Counter(row["同组调剂结论"] for row in rows)),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "candidate_decision_allowed_count": 0,
        "notes": [
            "本表是一行一个招生专业明细的决策闸门表，只用于机器预筛、核验排序和家庭讨论准备。",
            "所有城市、办学属性、公办民办、校区、湖北官方系统、家庭接受度和同组调剂结论仍需核验。",
            "所有行均保持最终可用=false、可进入下一阶段=false，不产生报考结论。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
