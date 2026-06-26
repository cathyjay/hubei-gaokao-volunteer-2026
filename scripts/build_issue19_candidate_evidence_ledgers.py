#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
FAMILY_PREFERENCES = ROOT / "data/working/family-preferences.json"
CANDIDATE_GROUP_WORKBENCH = ROOT / "data/working/issue19-candidate-v2-verification-group-workbench.csv"
CANDIDATE_MAJOR_WORKBENCH = ROOT / "data/working/issue19-candidate-v2-verification-major-workbench.csv"
FULL_MAJOR_QUALITY = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"
FOUNDATION_AUDIT_SUMMARY = ROOT / "data/working/issue19-foundation-audit-summary.json"
FOUNDATION_PAGE_AUDIT = ROOT / "data/working/issue19-foundation-page-audit.csv"

FIELD_LEDGER_OUTPUT = ROOT / "data/working/issue19-candidate-v2-field-review-ledger.csv"
TRIANGULATION_OUTPUT = ROOT / "data/working/issue19-candidate-v2-triangulation-matrix.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v2-evidence-ledger-summary.json"

PENDING_FIELD_REVIEW = "pending_manual_field_review"
PENDING_GROUP_REVIEW = "pending_group_evidence_review"
DATA_STAGE = "candidate_v2_evidence_ledger"

GROUP_FIELD_SPECS = [
    ("专业组代码", "2026院校专业组代码", "核院校专业组代码是否与第19期和官方系统一致"),
    ("专业组边界", "专业明细行数", "核该专业组下全部专业是否完整，尤其是跨页、同校相邻组和0明细组"),
    ("PDF原页", "来源页码", "回看第19期原PDF页，确认页码、栏位、组号和组内范围"),
    ("湖北官方系统/省招办计划", "湖北官方系统/省招办计划核验状态", "登录湖北官方系统或使用省招办计划核对专业组和计划"),
    ("高校官网/招生章程", "高校官网/招生章程核验状态", "核高校官网或招生章程是否支持专业、学费、校区、限制条件"),
    ("历史投档线", "历史投档线可沿用", "确认2026专业组是否能沿用2023-2025历史投档线参照"),
    ("家庭接受度", "家庭接受度核验状态", "确认组内全部专业是否能接受"),
    ("调剂结论", "调剂结论状态", "确认是否可以服从该院校专业组内调剂"),
]

MAJOR_FIELD_SPECS = [
    ("专业代号", "专业代号", "核专业代号是否准确"),
    ("专业名称", "专业名称及备注", "核专业名称和方向备注是否准确"),
    ("再选科目", "再选科目候选", "核再选科目是否匹配化学、地理组合"),
    ("计划数", "专业计划数候选", "核招生计划数是否准确"),
    ("学费", "学费候选", "核学费是否为正常学费且不超过家庭上限"),
    ("备注/限制", "专业名称及备注", "核校区、语种、单科、体检、合作办学、专项等备注"),
    ("专业接受度", "专业接受度机器初判", "由家庭确认可接受、勉强接受或不能接受"),
    ("调剂影响", "是否可能导致不能服从调剂", "判断该专业是否会影响本组服从调剂"),
]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def full_major_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        row.get("来源页码", ""),
        row.get("专业代号OCR", ""),
        row.get("专业名称及备注OCR", ""),
        row.get("专业计划数OCR候选", ""),
        row.get("学费OCR候选", ""),
    )


def candidate_major_key(row):
    return (
        row.get("院校代码", ""),
        row.get("2026院校专业组代码", ""),
        row.get("来源页码", ""),
        row.get("专业代号", ""),
        row.get("专业名称及备注", ""),
        row.get("专业计划数候选", ""),
        row.get("学费候选", ""),
    )


def risk_text_for_major(row):
    pieces = []
    for field in ["字段完整性标记", "结构异常规则ID", "结构异常类型", "风险类型", "阻断原因", "风险说明"]:
        value = row.get(field, "")
        if value:
            pieces.append(f"{field}:{value}")
    return "；".join(pieces)


def priority_for_group(row):
    priority = row.get("当前复核优先级", "")
    if priority.startswith("P0"):
        return "P0-字段必须优先核"
    if priority.startswith("P1"):
        return "P1-字段高优先核"
    if priority.startswith("P2"):
        return "P2-字段常规核"
    return "P3-字段常规核"


def priority_for_major(row, field_name):
    if row.get("专业接受度机器初判") in {"默认不能接受", "默认不进主方案"}:
        return "P0-字段必须优先核"
    if field_name in {"计划数", "学费", "再选科目", "调剂影响", "专业接受度"}:
        return "P0-字段必须优先核"
    if row.get("字段完整性标记") or row.get("结构异常规则ID") or row.get("风险类型"):
        return "P1-字段高优先核"
    return "P2-字段常规核"


def page_audit_text(row):
    if not row:
        return ""
    return (
        f"页{row.get('来源页码')}：专业组{row.get('页面专业组数')}；"
        f"专业明细{row.get('页面专业明细数')}；"
        f"结构异常{row.get('页面结构异常数')}；"
        f"候选命中{row.get('页面候选池V1专业明细数')}；"
        f"{row.get('页面复核优先级')}"
    )


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]
    preferences = json.loads(FAMILY_PREFERENCES.read_text())
    foundation_summary = json.loads(FOUNDATION_AUDIT_SUMMARY.read_text())

    group_rows = read_csv(CANDIDATE_GROUP_WORKBENCH)
    major_rows = read_csv(CANDIDATE_MAJOR_WORKBENCH)
    full_major_rows = read_csv(FULL_MAJOR_QUALITY)
    page_rows = read_csv(FOUNDATION_PAGE_AUDIT)

    page_by_number = {row["来源页码"]: row for row in page_rows}
    full_major_index = defaultdict(list)
    for row in full_major_rows:
        full_major_index[full_major_key(row)].append(row)

    major_match_by_index = {}
    for index, row in enumerate(major_rows, start=1):
        matches = full_major_index.get(candidate_major_key(row), [])
        if len(matches) == 1:
            major_match_by_index[index] = ("exact_full_major_match", matches[0])
        elif len(matches) > 1:
            major_match_by_index[index] = ("ambiguous_full_major_match", {})
        else:
            major_match_by_index[index] = ("not_in_full_major_workbench", {})

    field_rows = []
    group_field_count_by_code = Counter()
    group_p0_field_count_by_code = Counter()

    for group in group_rows:
        group_code = group["2026院校专业组代码"]
        page_audit = page_by_number.get(group.get("来源页码", ""), {})
        for field_name, source_field, task_note in GROUP_FIELD_SPECS:
            priority = priority_for_group(group)
            task_id = stable_id(
                "FR",
                [source_pdf_sha256, "group", group_code, group.get("关联原候选", ""), field_name],
            )
            output = {
                "来源期号": source_issue,
                "来源PDF_SHA256": source_pdf_sha256,
                "数据阶段": DATA_STAGE,
                "最终可用": "false",
                "复核状态": PENDING_GROUP_REVIEW,
                "复核任务ID": task_id,
                "复核对象类型": "专业组字段",
                "字段类别": "专业组",
                "字段名称": field_name,
                "关联类型": group.get("关联类型", ""),
                "关联原候选": group.get("关联原候选", ""),
                "院校代码": group.get("院校代码", ""),
                "院校名称": group.get("院校名称", ""),
                "2026院校专业组代码": group_code,
                "专业组出现ID": "",
                "专业行ID": "",
                "组内序号": "",
                "专业代号": "",
                "专业名称及备注": "",
                "来源页码": group.get("来源页码", ""),
                "页图文件名": group.get("页图文件名", ""),
                "证据来源": group.get("证据来源", ""),
                "OCR原值": group.get(source_field, ""),
                "OCR风险提示": "；".join(
                    part
                    for part in [
                        group.get("风险类型", ""),
                        group.get("零明细原因", ""),
                        group.get("升级缺口", ""),
                        page_audit_text(page_audit),
                    ]
                    if part
                ),
                "原PDF人工确认值": "",
                "湖北官方系统确认值": "",
                "高校官网/章程确认值": "",
                "家庭确认值": "",
                "私有证据编号": "",
                "核验责任阶段": task_note,
                "字段核验状态": "pending",
                "是否阻断候选升级": "是",
                "复核优先级": priority,
                "下一步": "回看第19期原PDF页；再用湖北官方系统、省招办计划和高校章程交叉核验。",
            }
            field_rows.append(output)
            group_field_count_by_code[group_code] += 1
            if priority.startswith("P0"):
                group_p0_field_count_by_code[group_code] += 1

    for index, major in enumerate(major_rows, start=1):
        group_code = major["2026院校专业组代码"]
        match_status, matched_full_major = major_match_by_index[index]
        page_audit = page_by_number.get(major.get("来源页码", ""), {})
        for field_name, source_field, task_note in MAJOR_FIELD_SPECS:
            priority = priority_for_major(major, field_name)
            task_id = stable_id(
                "FR",
                [
                    source_pdf_sha256,
                    "major",
                    group_code,
                    major.get("组内序号", ""),
                    major.get("专业代号", ""),
                    field_name,
                    major.get("专业名称及备注", ""),
                ],
            )
            output = {
                "来源期号": source_issue,
                "来源PDF_SHA256": source_pdf_sha256,
                "数据阶段": DATA_STAGE,
                "最终可用": "false",
                "复核状态": PENDING_FIELD_REVIEW,
                "复核任务ID": task_id,
                "复核对象类型": "专业字段",
                "字段类别": "专业明细",
                "字段名称": field_name,
                "关联类型": major.get("关联类型", ""),
                "关联原候选": major.get("关联原候选", ""),
                "院校代码": major.get("院校代码", ""),
                "院校名称": major.get("院校名称OCR", ""),
                "2026院校专业组代码": group_code,
                "专业组出现ID": matched_full_major.get("专业组出现ID", ""),
                "专业行ID": matched_full_major.get("专业行ID", ""),
                "组内序号": major.get("组内序号", ""),
                "专业代号": major.get("专业代号", ""),
                "专业名称及备注": major.get("专业名称及备注", ""),
                "来源页码": major.get("来源页码", ""),
                "页图文件名": major.get("页图文件名", ""),
                "证据来源": f"{major.get('证据来源', '')};{match_status}",
                "OCR原值": major.get(source_field, ""),
                "OCR风险提示": "；".join(
                    part
                    for part in [
                        risk_text_for_major(major),
                        page_audit_text(page_audit),
                    ]
                    if part
                ),
                "原PDF人工确认值": "",
                "湖北官方系统确认值": "",
                "高校官网/章程确认值": "",
                "家庭确认值": "",
                "私有证据编号": "",
                "核验责任阶段": task_note,
                "字段核验状态": "pending",
                "是否阻断候选升级": "是",
                "复核优先级": priority,
                "下一步": "逐字段核 PDF 原页；补湖北官方系统和高校章程值；再由家庭确认专业接受度。",
            }
            field_rows.append(output)
            group_field_count_by_code[group_code] += 1
            if priority.startswith("P0"):
                group_p0_field_count_by_code[group_code] += 1

    matrix_rows = []
    for group in group_rows:
        group_code = group["2026院校专业组代码"]
        page_audit = page_by_number.get(group.get("来源页码", ""), {})
        group_task_count = group_field_count_by_code[group_code]
        p0_task_count = group_p0_field_count_by_code[group_code]
        output = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": DATA_STAGE,
            "最终可用": "false",
            "证据矩阵ID": stable_id(
                "TM",
                [source_pdf_sha256, group_code, group.get("关联原候选", ""), group.get("来源页码", "")],
            ),
            "关联类型": group.get("关联类型", ""),
            "关联原候选": group.get("关联原候选", ""),
            "院校代码": group.get("院校代码", ""),
            "院校名称": group.get("院校名称", ""),
            "2026院校专业组代码": group_code,
            "来源页码": group.get("来源页码", ""),
            "页图文件名": group.get("页图文件名", ""),
            "专业明细行数": group.get("专业明细行数", ""),
            "字段复核任务数": str(group_task_count),
            "字段P0任务数": str(p0_task_count),
            "原PDF页证据状态": group.get("原PDF页人工核验状态", ""),
            "湖北官方系统证据状态": group.get("湖北官方系统/省招办计划核验状态", ""),
            "高校官网/章程证据状态": group.get("高校官网/招生章程核验状态", ""),
            "家庭接受度证据状态": group.get("家庭接受度核验状态", ""),
            "调剂结论状态": group.get("调剂结论状态", ""),
            "三年历史线证据状态": group.get("历史线基准来源", ""),
            "第19期PDF底座状态": foundation_summary.get("status", ""),
            "页级审计摘要": page_audit_text(page_audit),
            "组内调剂机器初判": group.get("组内调剂机器初判", ""),
            "历史投档线可沿用": group.get("历史投档线可沿用", ""),
            "当前复核优先级": group.get("当前复核优先级", ""),
            "候选闸门状态": group.get("候选闸门状态", ""),
            "可进入最终候选": group.get("可进入最终候选", ""),
            "升级缺口": "；".join(
                part
                for part in [
                    group.get("升级缺口", ""),
                    "逐字段复核总账待回填",
                    "官方系统/官网/家庭调剂结论待补证据",
                ]
                if part
            ),
            "下一步": "先按字段复核总账回填 PDF 原页值；再补官方系统、官网章程、家庭接受度和调剂证据。",
        }
        matrix_rows.append(output)

    field_rows.sort(
        key=lambda row: (
            row["关联类型"],
            row["院校代码"],
            row["2026院校专业组代码"],
            as_int(row["来源页码"]) or 9999,
            as_int(row["组内序号"]) or 9999,
            row["字段类别"],
            row["字段名称"],
        )
    )
    matrix_rows.sort(
        key=lambda row: (
            row["关联类型"],
            row["院校代码"],
            row["2026院校专业组代码"],
            as_int(row["来源页码"]) or 9999,
        )
    )

    field_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "复核状态",
        "复核任务ID",
        "复核对象类型",
        "字段类别",
        "字段名称",
        "关联类型",
        "关联原候选",
        "院校代码",
        "院校名称",
        "2026院校专业组代码",
        "专业组出现ID",
        "专业行ID",
        "组内序号",
        "专业代号",
        "专业名称及备注",
        "来源页码",
        "页图文件名",
        "证据来源",
        "OCR原值",
        "OCR风险提示",
        "原PDF人工确认值",
        "湖北官方系统确认值",
        "高校官网/章程确认值",
        "家庭确认值",
        "私有证据编号",
        "核验责任阶段",
        "字段核验状态",
        "是否阻断候选升级",
        "复核优先级",
        "下一步",
    ]
    matrix_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "证据矩阵ID",
        "关联类型",
        "关联原候选",
        "院校代码",
        "院校名称",
        "2026院校专业组代码",
        "来源页码",
        "页图文件名",
        "专业明细行数",
        "字段复核任务数",
        "字段P0任务数",
        "原PDF页证据状态",
        "湖北官方系统证据状态",
        "高校官网/章程证据状态",
        "家庭接受度证据状态",
        "调剂结论状态",
        "三年历史线证据状态",
        "第19期PDF底座状态",
        "页级审计摘要",
        "组内调剂机器初判",
        "历史投档线可沿用",
        "当前复核优先级",
        "候选闸门状态",
        "可进入最终候选",
        "升级缺口",
        "下一步",
    ]
    write_csv(FIELD_LEDGER_OUTPUT, field_rows, field_fields)
    write_csv(TRIANGULATION_OUTPUT, matrix_rows, matrix_fields)

    field_status_counts = Counter(row["字段核验状态"] for row in field_rows)
    field_priority_counts = Counter(row["复核优先级"] for row in field_rows)
    match_status_counts = Counter(status for status, _ in major_match_by_index.values())
    summary = {
        "status": "candidate_v2_evidence_ledgers_pending_manual_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": DATA_STAGE,
        "generated_by": "scripts/build_issue19_candidate_evidence_ledgers.py",
        "inputs": input_snapshot(
            ROOT,
            [
                ISSUE19_SOURCE,
                FAMILY_PREFERENCES,
                CANDIDATE_GROUP_WORKBENCH,
                CANDIDATE_MAJOR_WORKBENCH,
                FULL_MAJOR_QUALITY,
                FOUNDATION_AUDIT_SUMMARY,
                FOUNDATION_PAGE_AUDIT,
            ],
        ),
        "group_count": len(group_rows),
        "major_count": len(major_rows),
        "field_review_task_count": len(field_rows),
        "group_field_review_task_count": len(group_rows) * len(GROUP_FIELD_SPECS),
        "major_field_review_task_count": len(major_rows) * len(MAJOR_FIELD_SPECS),
        "triangulation_matrix_count": len(matrix_rows),
        "field_review_status_counts": dict(field_status_counts),
        "field_review_priority_counts": dict(field_priority_counts),
        "major_full_workbench_match_status_counts": dict(match_status_counts),
        "final_available_count": sum(row["最终可用"] != "false" for row in field_rows + matrix_rows),
        "candidate_can_enter_final_count": sum(row["可进入最终候选"] == "true" for row in matrix_rows),
        "tuition_limit_yuan": preferences["budget"]["annual_upper_limit_yuan"],
        "outputs": [
            str(FIELD_LEDGER_OUTPUT.relative_to(ROOT)),
            str(TRIANGULATION_OUTPUT.relative_to(ROOT)),
        ],
        "notes": [
            "字段复核总账是回填模板，不代表已核准结果。",
            "原PDF、湖北官方系统、高校官网/章程和家庭接受度都必须留证后才能升级候选。",
            "公开表不保存私有截图或账号信息，只保存私有证据编号占位。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出候选V2逐字段复核总账：{FIELD_LEDGER_OUTPUT}")
    print(f"写出候选V2三方证据矩阵：{TRIANGULATION_OUTPUT}")
    print(f"写出候选V2证据总账摘要：{SUMMARY_OUTPUT}")
    print(f"字段复核任务数：{len(field_rows)}")
    print(f"证据矩阵行数：{len(matrix_rows)}")


if __name__ == "__main__":
    main()
