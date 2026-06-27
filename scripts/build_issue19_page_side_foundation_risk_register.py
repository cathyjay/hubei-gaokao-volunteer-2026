#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIELD_PAGE_SIDE_QUEUE = ROOT / "data/working/issue19-field-fact-page-side-verification-queue.csv"
MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
STRUCTURAL_REGISTER = ROOT / "data/working/issue19-admission-detail-structural-fidelity-register.csv"
STRUCTURAL_RISK_LEDGER = ROOT / "data/working/issue19-structural-risk-major-line-ledger.csv"
LAYOUT_RISK_LEDGER = ROOT / "data/working/issue19-major-line-layout-continuity-risk-ledger.csv"
CODE_ORDER_RISK_LEDGER = ROOT / "data/working/issue19-major-code-order-risk-ledger.csv"
OFFICIAL_KEY_COLLISION_LEDGER = ROOT / "data/working/issue19-hubei-official-query-key-collision-ledger.csv"
MOE_UNMATCHED_RESOLUTION = ROOT / "data/working/issue19-moe-unmatched-school-resolution-major-detail.csv"
B0_B1_OFFICIAL_DIFF_LEDGER = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
DECISION_GATES = ROOT / "data/working/issue19-major-decision-readiness-gates.csv"
SOURCE_RISK_SIDECAR = ROOT / "data/working/issue19-major-source-evidence-risk-sidecar.csv"

OUTPUT = ROOT / "data/working/issue19-page-side-foundation-risk-register.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-page-side-foundation-risk-register-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_page_side_foundation_risk_register"


FIELDS = [
    "页列底座综合风险登记ID",
    "来源全量字段页列核验队列",
    "来源单一逐专业招生明细总工作台",
    "来源结构保真登记表",
    "来源结构风险事件表",
    "来源版面连续性风险清单",
    "来源专业代号顺序风险清单",
    "来源官方查询键碰撞清单",
    "来源教育部未匹配校名解析表",
    "来源B0B1官网差异账",
    "来源逐专业决策闸门表",
    "来源逐专业源证据风险侧账",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "页列综合风险总序",
    "来源页码",
    "版面列",
    "页码版面键",
    "综合风险优先级桶",
    "综合风险优先级数值",
    "页列首要核验动作",
    "字段页列核验队列ID",
    "字段页列核验优先级桶",
    "包内专业行数",
    "包内字段任务数",
    "字段Q0无候选阻断任务数",
    "字段Q1有候选待人工核验任务数",
    "字段Q2待三方闭环任务数",
    "PDF原页核验待完成任务数",
    "湖北官方核验待完成任务数",
    "结构R0专业行数",
    "结构R1专业行数",
    "结构R2专业行数",
    "结构R3专业行数",
    "结构风险事件数",
    "结构风险专业行数",
    "结构风险类型分布",
    "版面风险事件数",
    "版面风险专业行数",
    "版面风险等级分布",
    "专业代号风险事件数",
    "专业代号风险专业行数",
    "专业代号风险等级分布",
    "官方查询键碰撞行数",
    "官方查询键碰撞键数",
    "教育部未匹配校名专业行数",
    "教育部未匹配校名等级分布",
    "官网辅证线索行数",
    "官网计划数冲突行数",
    "官网未匹配专业行数",
    "官网来源状态分布",
    "决策G0结构或归属未闭环行数",
    "决策G1家庭底线风险待确认行数",
    "决策G2字段缺口未闭环行数",
    "决策G3机器预筛线索行数",
    "决策G4常规留存行数",
    "决策动作桶分布",
    "源证据X1专业窗口P0行数",
    "源证据X2起始行P0_QC行数",
    "源证据X3优先复核行数",
    "源证据X4低风险抽检行数",
    "源证据优先核页行数",
    "低置信度页专业行数",
    "专业行ID集合SHA256",
    "专业组出现ID集合SHA256",
    "院校代码集合SHA256",
    "结构风险事件ID集合SHA256",
    "版面风险ID集合SHA256",
    "专业代号风险ID集合SHA256",
    "官方查询键碰撞ID集合SHA256",
    "教育部未匹配解析ID集合SHA256",
    "官网差异账ID集合SHA256",
    "决策闸门ID集合SHA256",
    "源证据风险侧账ID集合SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha_list(values):
    normalized = "；".join(sorted({value for value in values if value}))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def counter_text(counter):
    return "；".join(f"{key}:{value}" for key, value in sorted(counter.items()) if key) if counter else ""


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except ValueError:
        return default


def page_side_key(row):
    return (str(row.get("来源页码", "")).strip(), str(row.get("版面列", "")).strip())


def group_by_page_side(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[page_side_key(row)].append(row)
    return grouped


def group_by_major_page_side(rows, major_to_page_side):
    grouped = defaultdict(list)
    for row in rows:
        key = major_to_page_side.get(row.get("专业行ID", ""))
        if key:
            grouped[key].append(row)
    return grouped


def unique_count(rows, field):
    return len({row.get(field, "") for row in rows if row.get(field, "")})


def count_value(rows, field, value):
    return sum(row.get(field, "") == value for row in rows)


def count_contains(rows, field, needle):
    return sum(needle in row.get(field, "") for row in rows)


def priority_for_page_side(data):
    if (
        data["结构R0专业行数"]
        or data["源证据X1专业窗口P0行数"]
        or data["源证据X2起始行P0_QC行数"]
        or data["版面P0风险事件数"]
        or data["官方查询键碰撞行数"]
    ):
        return (
            "Z0-结构源证据或官方消歧阻断页列先核",
            0,
            "先核结构边界、源证据和官方查询键消歧，再处理字段读数。",
        )
    if (
        data["字段Q0无候选阻断任务数"]
        or data["结构R1专业行数"]
        or data["结构R2专业行数"]
        or data["版面P1风险事件数"]
        or data["专业代号P1风险事件数"]
        or data["教育部未匹配校名专业行数"]
        or data["官网计划数冲突行数"]
    ):
        return (
            "Z1-字段缺口和结构风险并行核页",
            1,
            "并行核字段缺口、结构归属、校名待核和计划数冲突。",
        )
    if (
        data["字段Q1有候选待人工核验任务数"]
        or data["官网辅证线索行数"]
        or data["源证据X3优先复核行数"]
        or data["专业代号P2风险事件数"]
    ):
        return (
            "Z2-候选字段和辅证线索核验页列",
            2,
            "核对候选字段和高校辅证线索，仍需 PDF 原页与湖北官方侧闭环。",
        )
    return (
        "Z3-常规三方闭环抽检页列",
        3,
        "执行常规 PDF 原页、湖北官方侧和必要高校辅证闭环抽检。",
    )


def build_rows():
    field_page_rows = read_csv(FIELD_PAGE_SIDE_QUEUE)
    master_rows = read_csv(MASTER_WORKBENCH)
    structural_rows = read_csv(STRUCTURAL_REGISTER)
    structural_risk_rows = read_csv(STRUCTURAL_RISK_LEDGER)
    layout_risk_rows = read_csv(LAYOUT_RISK_LEDGER)
    code_order_risk_rows = read_csv(CODE_ORDER_RISK_LEDGER)
    official_collision_rows = read_csv(OFFICIAL_KEY_COLLISION_LEDGER)
    moe_unmatched_rows = read_csv(MOE_UNMATCHED_RESOLUTION)
    official_diff_rows = read_csv(B0_B1_OFFICIAL_DIFF_LEDGER)
    decision_gate_rows = read_csv(DECISION_GATES)
    source_risk_rows = read_csv(SOURCE_RISK_SIDECAR)

    major_to_page_side = {
        row["专业行ID"]: page_side_key(row)
        for row in master_rows
        if row.get("专业行ID")
    }

    structural_by_side = group_by_page_side(structural_rows)
    structural_risk_by_side = group_by_major_page_side(structural_risk_rows, major_to_page_side)
    layout_risk_by_side = group_by_page_side(layout_risk_rows)
    code_order_risk_by_side = group_by_page_side(code_order_risk_rows)
    official_collision_by_side = group_by_major_page_side(official_collision_rows, major_to_page_side)
    moe_unmatched_by_side = group_by_major_page_side(moe_unmatched_rows, major_to_page_side)
    official_diff_by_side = group_by_major_page_side(official_diff_rows, major_to_page_side)
    decision_gate_by_side = group_by_page_side(decision_gate_rows)
    source_risk_by_side = group_by_page_side(source_risk_rows)

    output_rows = []
    for base in field_page_rows:
        key = page_side_key(base)
        structural = structural_by_side.get(key, [])
        structural_risk = structural_risk_by_side.get(key, [])
        layout_risk = layout_risk_by_side.get(key, [])
        code_order_risk = code_order_risk_by_side.get(key, [])
        official_collision = official_collision_by_side.get(key, [])
        moe_unmatched = moe_unmatched_by_side.get(key, [])
        official_diff = official_diff_by_side.get(key, [])
        decision_gate = decision_gate_by_side.get(key, [])
        source_risk = source_risk_by_side.get(key, [])

        structural_priority = Counter(row.get("结构保真优先级", "") for row in structural)
        structural_risk_type = Counter(row.get("结构风险类型", "") for row in structural_risk)
        layout_risk_level = Counter(row.get("风险等级", "") for row in layout_risk)
        code_order_risk_level = Counter(row.get("风险等级", "") for row in code_order_risk)
        moe_level = Counter(row.get("候选综合等级", "") for row in moe_unmatched)
        official_source_status = Counter(row.get("官网来源状态", "") for row in official_diff)
        decision_status = Counter(row.get("候选初筛闸门状态", "") for row in decision_gate)
        decision_action = Counter(row.get("初筛动作桶", "") for row in decision_gate)
        source_layer = Counter(row.get("源证据下沉分层", "") for row in source_risk)

        data = {
            "字段Q0无候选阻断任务数": as_int(base.get("包内Q0无候选阻断任务数")),
            "字段Q1有候选待人工核验任务数": as_int(base.get("包内Q1有候选待人工核验任务数")),
            "结构R0专业行数": structural_priority.get("R0-结构边界阻断优先核", 0),
            "结构R1专业行数": structural_priority.get("R1-归属或结构异常先核", 0),
            "结构R2专业行数": structural_priority.get("R2-原页上下文补证", 0),
            "版面P0风险事件数": layout_risk_level.get("P0-版面边界先核", 0),
            "版面P1风险事件数": layout_risk_level.get("P1-相邻行顺序核验", 0),
            "专业代号P1风险事件数": code_order_risk_level.get("P1-专业代号先核", 0),
            "专业代号P2风险事件数": code_order_risk_level.get("P2-专业代号序列复核", 0),
            "官方查询键碰撞行数": len(official_collision),
            "教育部未匹配校名专业行数": len(moe_unmatched),
            "官网计划数冲突行数": count_value(official_diff, "计划数核验状态", "官网专业名匹配但计划数冲突-优先核页"),
            "官网辅证线索行数": len(official_diff),
            "源证据X1专业窗口P0行数": source_layer.get("X1-专业窗口P0先核", 0),
            "源证据X2起始行P0_QC行数": source_layer.get("X2-起始行P0_QC先核", 0),
            "源证据X3优先复核行数": source_layer.get("X3-源证据优先复核", 0),
        }
        bucket, priority, action = priority_for_page_side(data)

        output_rows.append({
            "页列底座综合风险登记ID": stable_id("PSFOUNDATIONRISK", [base["来源页码"], base["版面列"]]),
            "来源全量字段页列核验队列": "data/working/issue19-field-fact-page-side-verification-queue.csv",
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源结构保真登记表": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
            "来源结构风险事件表": "data/working/issue19-structural-risk-major-line-ledger.csv",
            "来源版面连续性风险清单": "data/working/issue19-major-line-layout-continuity-risk-ledger.csv",
            "来源专业代号顺序风险清单": "data/working/issue19-major-code-order-risk-ledger.csv",
            "来源官方查询键碰撞清单": "data/working/issue19-hubei-official-query-key-collision-ledger.csv",
            "来源教育部未匹配校名解析表": "data/working/issue19-moe-unmatched-school-resolution-major-detail.csv",
            "来源B0B1官网差异账": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
            "来源逐专业决策闸门表": "data/working/issue19-major-decision-readiness-gates.csv",
            "来源逐专业源证据风险侧账": "data/working/issue19-major-source-evidence-risk-sidecar.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×底座综合风险",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "页列综合风险总序": "",
            "来源页码": base["来源页码"],
            "版面列": base["版面列"],
            "页码版面键": base["页码版面键"],
            "综合风险优先级桶": bucket,
            "综合风险优先级数值": str(priority),
            "页列首要核验动作": action,
            "字段页列核验队列ID": base["全量字段页列核验队列ID"],
            "字段页列核验优先级桶": base["页列核验优先级桶"],
            "包内专业行数": base["包内专业行数"],
            "包内字段任务数": base["包内字段任务数"],
            "字段Q0无候选阻断任务数": base["包内Q0无候选阻断任务数"],
            "字段Q1有候选待人工核验任务数": base["包内Q1有候选待人工核验任务数"],
            "字段Q2待三方闭环任务数": base["包内Q2OCR齐全待三方闭环任务数"],
            "PDF原页核验待完成任务数": base["包内PDF原页核验待完成任务数"],
            "湖北官方核验待完成任务数": base["包内湖北官方核验待完成任务数"],
            "结构R0专业行数": str(data["结构R0专业行数"]),
            "结构R1专业行数": str(data["结构R1专业行数"]),
            "结构R2专业行数": str(data["结构R2专业行数"]),
            "结构R3专业行数": str(structural_priority.get("R3-结构常规抽检", 0)),
            "结构风险事件数": str(len(structural_risk)),
            "结构风险专业行数": str(unique_count(structural_risk, "专业行ID")),
            "结构风险类型分布": counter_text(structural_risk_type),
            "版面风险事件数": str(len(layout_risk)),
            "版面风险专业行数": str(unique_count(layout_risk, "专业行ID")),
            "版面风险等级分布": counter_text(layout_risk_level),
            "专业代号风险事件数": str(len(code_order_risk)),
            "专业代号风险专业行数": str(unique_count(code_order_risk, "专业行ID")),
            "专业代号风险等级分布": counter_text(code_order_risk_level),
            "官方查询键碰撞行数": str(len(official_collision)),
            "官方查询键碰撞键数": str(unique_count(official_collision, "碰撞键")),
            "教育部未匹配校名专业行数": str(len(moe_unmatched)),
            "教育部未匹配校名等级分布": counter_text(moe_level),
            "官网辅证线索行数": str(len(official_diff)),
            "官网计划数冲突行数": str(data["官网计划数冲突行数"]),
            "官网未匹配专业行数": str(count_value(official_diff, "官网证据匹配状态", "unmatched")),
            "官网来源状态分布": counter_text(official_source_status),
            "决策G0结构或归属未闭环行数": str(decision_status.get("G0-结构或归属未闭环", 0)),
            "决策G1家庭底线风险待确认行数": str(decision_status.get("G1-家庭底线风险待确认", 0)),
            "决策G2字段缺口未闭环行数": str(decision_status.get("G2-字段缺口未闭环", 0)),
            "决策G3机器预筛线索行数": str(decision_status.get("G3-可作机器预筛线索但不可定案", 0)),
            "决策G4常规留存行数": str(decision_status.get("G4-常规留存但不可定案", 0)),
            "决策动作桶分布": counter_text(decision_action),
            "源证据X1专业窗口P0行数": str(data["源证据X1专业窗口P0行数"]),
            "源证据X2起始行P0_QC行数": str(data["源证据X2起始行P0_QC行数"]),
            "源证据X3优先复核行数": str(data["源证据X3优先复核行数"]),
            "源证据X4低风险抽检行数": str(source_layer.get("X4-源证据低风险抽检但仍需三方闭环", 0)),
            "源证据优先核页行数": str(count_value(source_risk, "是否进入源证据优先核页清单", "true")),
            "低置信度页专业行数": str(count_value(source_risk, "低置信度页标记", "true")),
            "专业行ID集合SHA256": sha_list(row["专业行ID"] for row in structural),
            "专业组出现ID集合SHA256": base["专业组出现ID集合SHA256"],
            "院校代码集合SHA256": base["院校代码集合SHA256"],
            "结构风险事件ID集合SHA256": sha_list(row["结构风险事件ID"] for row in structural_risk),
            "版面风险ID集合SHA256": sha_list(row["版面连续性风险ID"] for row in layout_risk),
            "专业代号风险ID集合SHA256": sha_list(row["专业代号顺序风险ID"] for row in code_order_risk),
            "官方查询键碰撞ID集合SHA256": sha_list(row["官方查询键碰撞ID"] for row in official_collision),
            "教育部未匹配解析ID集合SHA256": sha_list(row["未匹配校名解析ID"] for row in moe_unmatched),
            "官网差异账ID集合SHA256": sha_list(row["公开官网差异账ID"] for row in official_diff),
            "决策闸门ID集合SHA256": sha_list(row["决策闸门ID"] for row in decision_gate),
            "源证据风险侧账ID集合SHA256": sha_list(row["源证据风险侧账ID"] for row in source_risk),
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "字段事实写回状态": "blocked_until_page_side_foundation_risks_verified",
            "公开安全策略": (
                "只公开页列风险计数、分布、证据集合哈希和非最终门禁；"
                "不公开院校名、专业名、专业代号、专业组代码、字段候选值、人工记录值、图片路径或私有识别材料。"
            ),
            "下一步": f"{action} 完成后仍需逐专业回填 PDF 原页、湖北官方侧和必要高校辅证证据。",
        })

    output_rows.sort(
        key=lambda row: (
            as_int(row["综合风险优先级数值"]),
            -as_int(row["结构R0专业行数"]),
            -as_int(row["源证据X2起始行P0_QC行数"]),
            -as_int(row["字段Q0无候选阻断任务数"]),
            -as_int(row["结构风险事件数"]),
            -as_int(row["包内字段任务数"]),
            as_int(row["来源页码"]),
            0 if row["版面列"] == "left" else 1,
        )
    )
    for idx, row in enumerate(output_rows, start=1):
        row["页列综合风险总序"] = str(idx)

    return output_rows, {
        "field_page_rows": field_page_rows,
        "master_rows": master_rows,
        "structural_rows": structural_rows,
        "structural_risk_rows": structural_risk_rows,
        "layout_risk_rows": layout_risk_rows,
        "code_order_risk_rows": code_order_risk_rows,
        "official_collision_rows": official_collision_rows,
        "moe_unmatched_rows": moe_unmatched_rows,
        "official_diff_rows": official_diff_rows,
        "decision_gate_rows": decision_gate_rows,
        "source_risk_rows": source_risk_rows,
    }


def main():
    rows, sources = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    priority_counts = Counter(row["综合风险优先级桶"] for row in rows)
    summary = {
        "status": "issue19_page_side_foundation_risk_register_not_final",
        "generated_by": "build_issue19_page_side_foundation_risk_register.py",
        "source_field_page_side_queue": "data/working/issue19-field-fact-page-side-verification-queue.csv",
        "source_master_workbench": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_structural_register": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
        "source_structural_risk_ledger": "data/working/issue19-structural-risk-major-line-ledger.csv",
        "source_layout_risk_ledger": "data/working/issue19-major-line-layout-continuity-risk-ledger.csv",
        "source_code_order_risk_ledger": "data/working/issue19-major-code-order-risk-ledger.csv",
        "source_official_key_collision_ledger": "data/working/issue19-hubei-official-query-key-collision-ledger.csv",
        "source_moe_unmatched_resolution": "data/working/issue19-moe-unmatched-school-resolution-major-detail.csv",
        "source_b0_b1_official_diff_ledger": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
        "source_decision_gates": "data/working/issue19-major-decision-readiness-gates.csv",
        "source_source_risk_sidecar": "data/working/issue19-major-source-evidence-risk-sidecar.csv",
        "output_table": "data/working/issue19-page-side-foundation-risk-register.csv",
        "row_count": len(rows),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "source_major_line_count": len(sources["master_rows"]),
        "source_structural_major_line_count": len(sources["structural_rows"]),
        "source_field_task_count": sum(as_int(row["包内字段任务数"]) for row in rows),
        "priority_bucket_counts": dict(priority_counts),
        "field_q0_task_count": sum(as_int(row["字段Q0无候选阻断任务数"]) for row in rows),
        "field_q1_task_count": sum(as_int(row["字段Q1有候选待人工核验任务数"]) for row in rows),
        "field_q2_task_count": sum(as_int(row["字段Q2待三方闭环任务数"]) for row in rows),
        "structural_r0_major_line_count": sum(as_int(row["结构R0专业行数"]) for row in rows),
        "structural_r1_major_line_count": sum(as_int(row["结构R1专业行数"]) for row in rows),
        "structural_r2_major_line_count": sum(as_int(row["结构R2专业行数"]) for row in rows),
        "structural_r3_major_line_count": sum(as_int(row["结构R3专业行数"]) for row in rows),
        "structural_risk_event_count": sum(as_int(row["结构风险事件数"]) for row in rows),
        "layout_risk_event_count": sum(as_int(row["版面风险事件数"]) for row in rows),
        "code_order_risk_event_count": sum(as_int(row["专业代号风险事件数"]) for row in rows),
        "official_key_collision_row_count": sum(as_int(row["官方查询键碰撞行数"]) for row in rows),
        "moe_unmatched_major_line_count": sum(as_int(row["教育部未匹配校名专业行数"]) for row in rows),
        "official_diff_row_count": sum(as_int(row["官网辅证线索行数"]) for row in rows),
        "official_plan_conflict_row_count": sum(as_int(row["官网计划数冲突行数"]) for row in rows),
        "official_unmatched_major_row_count": sum(as_int(row["官网未匹配专业行数"]) for row in rows),
        "decision_g0_count": sum(as_int(row["决策G0结构或归属未闭环行数"]) for row in rows),
        "decision_g1_count": sum(as_int(row["决策G1家庭底线风险待确认行数"]) for row in rows),
        "decision_g2_count": sum(as_int(row["决策G2字段缺口未闭环行数"]) for row in rows),
        "decision_g3_count": sum(as_int(row["决策G3机器预筛线索行数"]) for row in rows),
        "decision_g4_count": sum(as_int(row["决策G4常规留存行数"]) for row in rows),
        "source_x1_count": sum(as_int(row["源证据X1专业窗口P0行数"]) for row in rows),
        "source_x2_count": sum(as_int(row["源证据X2起始行P0_QC行数"]) for row in rows),
        "source_x3_count": sum(as_int(row["源证据X3优先复核行数"]) for row in rows),
        "source_x4_count": sum(as_int(row["源证据X4低风险抽检行数"]) for row in rows),
        "source_priority_review_major_line_count": sum(as_int(row["源证据优先核页行数"]) for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "safety_note": (
            "公开表只保存页列风险计数、分布、证据集合哈希和非最终门禁；"
            "不保存院校名、专业名、专业代号、专业组代码、字段候选值、人工记录值、图片路径或私有识别材料。"
        ),
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
