#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
FULL_GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
MASTER_WORKBENCH = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
QUALITY_WORKBENCH = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"

OUTPUT = ROOT / "data/working/issue19-admission-detail-structural-fidelity-register.csv"
RISK_EVENT_OUTPUT = ROOT / "data/working/issue19-structural-risk-major-line-ledger.csv"
ZERO_DETAIL_OUTPUT = ROOT / "data/working/issue19-zero-detail-group-placeholder-workbench.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-admission-detail-structural-fidelity-summary.json"

DATA_STAGE = "issue19_admission_detail_structural_fidelity_register"


REGISTER_FIELDS = [
    "结构保真登记ID",
    "来源单一逐专业招生明细总工作台",
    "来源全量专业明细OCR初稿",
    "来源全量专业组OCR初稿",
    "来源逐专业质量工作台",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR短摘",
    "专业组标题行号",
    "专业起始行号",
    "专业起始y",
    "专业组归属方式",
    "是否唯一组码回退归属",
    "回退归属风险说明",
    "规范化专业组代码是否重复",
    "规范化专业组代码重复行数",
    "是否2026同代码专业组重复出现",
    "组内专业代号出现次数",
    "是否组内专业代号重复",
    "组内重复专业代号风险说明",
    "专业行结构异常数",
    "专业行高严重结构异常数",
    "专业行异常规则ID列表",
    "专业行异常类型列表",
    "专业行异常严重程度列表",
    "专业行异常证据摘要",
    "原页证据锚点状态",
    "专业行原页证据锚点ID",
    "专业窗口行号范围",
    "合并证据窗口行号范围",
    "合并证据窗口行数",
    "窗口文本SHA256",
    "起始行专业代号匹配",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "结构保真风险标签",
    "结构保真优先级",
    "必须人工核PDF原页",
    "必须湖北官方系统或省招办计划核验",
    "机器能否自动修复",
    "不得进入原因",
    "下一步",
]


RISK_EVENT_FIELDS = [
    "结构风险事件ID",
    "来源结构保真登记表",
    "来源单一逐专业招生明细总工作台",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR短摘",
    "结构风险类型",
    "结构风险等级",
    "风险来源表",
    "风险来源字段",
    "风险证据摘要",
    "必须人工核PDF原页",
    "必须湖北官方系统或省招办计划核验",
    "机器能否自动修复",
    "公开安全策略",
    "不得进入原因",
    "下一步",
]


ZERO_DETAIL_FIELDS = [
    "0明细占位ID",
    "来源全量专业组OCR初稿",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组标题行号",
    "专业组标题OCR原文",
    "OCR专业行数",
    "是否缺失专业明细",
    "是否真实招生明细",
    "是否0明细占位",
    "占位风险类型",
    "缺失明细风险说明",
    "是否可作为招生明细行",
    "必须人工核PDF原页",
    "必须湖北官方系统或省招办计划核验",
    "机器能否自动补齐专业明细",
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


def group_match_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        row.get("来源页码", ""),
        row.get("版面列", ""),
        row.get("专业组标题行号", ""),
        row.get("专业组标题OCR原文", ""),
    )


def major_line_id(row, index, source_pdf_sha256):
    return stable_id(
        "M",
        [
            source_pdf_sha256,
            index,
            row.get("院校代码", ""),
            row.get("院校专业组代码OCR规范化", ""),
            row.get("来源页码", ""),
            row.get("版面列", ""),
            row.get("专业起始行号", ""),
            row.get("专业起始y", ""),
            row.get("专业代号OCR", ""),
            row.get("专业名称及备注OCR", ""),
        ],
    )


def group_occurrence_id(row, index, source_pdf_sha256):
    return stable_id(
        "G",
        [
            source_pdf_sha256,
            index,
            row.get("院校代码", ""),
            row.get("院校专业组代码OCR规范化", ""),
            row.get("来源页码", ""),
            row.get("版面列", ""),
            row.get("专业组标题行号", ""),
            row.get("专业组标题OCR原文", ""),
        ],
    )


def build_group_assignment(group_rows, major_rows, source_pdf_sha256):
    groups_by_key = {}
    groups_by_code = defaultdict(list)
    group_ids_by_index = {}
    for index, row in enumerate(group_rows, start=1):
        gid = group_occurrence_id(row, index, source_pdf_sha256)
        group_ids_by_index[index] = gid
        groups_by_key[group_match_key(row)] = gid
        groups_by_code[row.get("院校专业组代码OCR规范化", "")].append((gid, row))

    assignment_by_major_id = {}
    for index, row in enumerate(major_rows, start=1):
        major_id = major_line_id(row, index, source_pdf_sha256)
        exact_gid = groups_by_key.get(group_match_key(row))
        if exact_gid:
            assignment_by_major_id[major_id] = {
                "专业组出现ID": exact_gid,
                "专业组归属方式": "exact_group_header_match",
            }
            continue
        code_groups = groups_by_code.get(row.get("院校专业组代码OCR规范化", ""), [])
        if len(code_groups) == 1:
            assignment_by_major_id[major_id] = {
                "专业组出现ID": code_groups[0][0],
                "专业组归属方式": "fallback_unique_group_code",
            }
            continue
        assignment_by_major_id[major_id] = {
            "专业组出现ID": "",
            "专业组归属方式": "unmatched_group_boundary",
        }
    return assignment_by_major_id, group_ids_by_index


def risk_labels(row, quality_row, assignment_method, duplicate_major_code):
    labels = []
    if assignment_method == "fallback_unique_group_code":
        labels.append("唯一组码回退归属")
    if row.get("规范化专业组代码是否重复") == "是":
        labels.append("2026规范化专业组代码重复")
    if duplicate_major_code:
        labels.append("组内专业代号重复")
    if as_int(quality_row.get("专业行高严重结构异常数")) > 0:
        labels.append("高严重结构异常")
    elif as_int(quality_row.get("专业行结构异常数")) > 0:
        labels.append("结构异常")
    if row.get("原页证据锚点状态") == "P0-专业窗口为空":
        labels.append("原页专业窗口为空")
    elif row.get("原页证据锚点状态") == "P1-缺少组标题上下文":
        labels.append("原页缺少组标题上下文")
    return labels


def priority_from(labels):
    label_set = set(labels)
    if label_set & {"2026规范化专业组代码重复", "组内专业代号重复", "原页专业窗口为空"}:
        return "R0-结构边界阻断优先核"
    if label_set & {"唯一组码回退归属", "高严重结构异常"}:
        return "R1-归属或结构异常先核"
    if label_set & {"原页缺少组标题上下文", "结构异常"}:
        return "R2-原页上下文补证"
    return "R3-结构常规抽检"


def risk_event(register_row, risk_type, risk_level, source_table, source_field, evidence):
    major_id = register_row["专业行ID"]
    return {
        "结构风险事件ID": stable_id("STRUCTEVENT", [major_id, risk_type]),
        "来源结构保真登记表": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
        "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
        "来源期号": register_row["来源期号"],
        "来源PDF_SHA256": register_row["来源PDF_SHA256"],
        "数据阶段": "issue19_structural_risk_major_line_ledger",
        "主表粒度": "逐专业招生明细×结构风险事件",
        "最终可用": "false",
        "可进入下一阶段": "false",
        "专业行ID": major_id,
        "专业组出现ID": register_row["专业组出现ID"],
        "院校代码": register_row["院校代码"],
        "院校名称OCR": register_row["院校名称OCR"],
        "院校专业组代码OCR规范化": register_row["院校专业组代码OCR规范化"],
        "来源页码": register_row["来源页码"],
        "版面列": register_row["版面列"],
        "专业组内专业序号": register_row["专业组内专业序号"],
        "专业代号OCR": register_row["专业代号OCR"],
        "专业名称及备注OCR短摘": register_row["专业名称及备注OCR短摘"],
        "结构风险类型": risk_type,
        "结构风险等级": risk_level,
        "风险来源表": source_table,
        "风险来源字段": source_field,
        "风险证据摘要": evidence,
        "必须人工核PDF原页": "true",
        "必须湖北官方系统或省招办计划核验": "true",
        "机器能否自动修复": "false",
        "公开安全策略": "公开表只保留风险类型、证据摘要和哈希/编号；不保存私有 OCR 原文、图片路径或登录态",
        "不得进入原因": "结构风险未闭环；确认前不得进入最终志愿排序",
        "下一步": "回看 PDF 原页的院校专业组边界、专业代号和专业窗口，再用湖北官方系统或省招办计划核验。",
    }


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]

    group_rows = read_csv(FULL_GROUPS)
    major_rows = read_csv(FULL_MAJORS)
    master_rows = read_csv(MASTER_WORKBENCH)
    quality_rows = read_csv(QUALITY_WORKBENCH)

    assignment_by_major_id, group_ids_by_index = build_group_assignment(
        group_rows, major_rows, source_pdf_sha256
    )
    master_by_major_id = {row.get("专业行ID", ""): row for row in master_rows}
    quality_by_major_id = {row.get("专业行ID", ""): row for row in quality_rows}

    code_count_by_group = Counter(
        (
            assignment_by_major_id[major_line_id(row, index, source_pdf_sha256)]["专业组出现ID"],
            row.get("专业代号OCR", ""),
        )
        for index, row in enumerate(major_rows, start=1)
        if row.get("专业代号OCR", "")
    )

    register_rows = []
    for index, major in enumerate(major_rows, start=1):
        major_id = major_line_id(major, index, source_pdf_sha256)
        master = master_by_major_id.get(major_id, {})
        quality = quality_by_major_id.get(major_id, {})
        assignment = assignment_by_major_id.get(major_id, {})
        group_id = assignment.get("专业组出现ID", "")
        code_count = code_count_by_group.get((group_id, major.get("专业代号OCR", "")), 0)
        duplicate_major_code = code_count > 1
        labels = risk_labels(master, quality, assignment.get("专业组归属方式", ""), duplicate_major_code)
        priority = priority_from(labels)
        register_rows.append({
            "结构保真登记ID": stable_id("STRUCTFID", [major_id]),
            "来源单一逐专业招生明细总工作台": "data/working/issue19-admission-detail-master-workbench.csv",
            "来源全量专业明细OCR初稿": "data/working/issue19-full-admission-plan-major-ocr-draft.csv",
            "来源全量专业组OCR初稿": "data/working/issue19-full-admission-plan-group-ocr-draft.csv",
            "来源逐专业质量工作台": "data/working/issue19-full-major-detail-quality-workbench.csv",
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "专业行ID": major_id,
            "专业组出现ID": group_id,
            "院校代码": master.get("院校代码", major.get("院校代码", "")),
            "院校名称OCR": master.get("院校名称OCR", major.get("院校名称OCR", "")),
            "院校专业组代码OCR规范化": master.get("院校专业组代码OCR规范化", major.get("院校专业组代码OCR规范化", "")),
            "来源页码": master.get("来源页码", major.get("来源页码", "")),
            "版面列": master.get("版面列", major.get("版面列", "")),
            "专业组内专业序号": master.get("专业组内专业序号", ""),
            "专业代号OCR": master.get("专业代号OCR", major.get("专业代号OCR", "")),
            "专业名称及备注OCR短摘": master.get("专业名称及备注短摘", major.get("专业名称及备注OCR", "")[:100]),
            "专业组标题行号": major.get("专业组标题行号", ""),
            "专业起始行号": major.get("专业起始行号", ""),
            "专业起始y": major.get("专业起始y", ""),
            "专业组归属方式": assignment.get("专业组归属方式", ""),
            "是否唯一组码回退归属": "true" if assignment.get("专业组归属方式") == "fallback_unique_group_code" else "false",
            "回退归属风险说明": "专业明细未精确匹配专业组标题行，仅因同组码唯一而回退归属，需核原页组边界" if assignment.get("专业组归属方式") == "fallback_unique_group_code" else "",
            "规范化专业组代码是否重复": quality.get("规范化专业组代码是否重复", ""),
            "规范化专业组代码重复行数": quality.get("规范化专业组代码重复行数", ""),
            "是否2026同代码专业组重复出现": master.get("2026同代码专业组是否重复出现", ""),
            "组内专业代号出现次数": str(code_count),
            "是否组内专业代号重复": "true" if duplicate_major_code else "false",
            "组内重复专业代号风险说明": "同一专业组出现重复专业代号，需核 PDF 原页确认是否串行、漏列或 OCR 切分错误" if duplicate_major_code else "",
            "专业行结构异常数": quality.get("专业行结构异常数", ""),
            "专业行高严重结构异常数": quality.get("专业行高严重结构异常数", ""),
            "专业行异常规则ID列表": quality.get("专业行异常规则ID列表", ""),
            "专业行异常类型列表": quality.get("专业行异常类型列表", ""),
            "专业行异常严重程度列表": quality.get("专业行异常严重程度列表", ""),
            "专业行异常证据摘要": quality.get("专业行异常证据摘要", ""),
            "原页证据锚点状态": master.get("原页证据锚点状态", ""),
            "专业行原页证据锚点ID": master.get("专业行原页证据锚点ID", ""),
            "专业窗口行号范围": master.get("专业窗口行号范围", ""),
            "合并证据窗口行号范围": master.get("合并证据窗口行号范围", ""),
            "合并证据窗口行数": master.get("合并证据窗口行数", ""),
            "窗口文本SHA256": master.get("窗口文本SHA256", ""),
            "起始行专业代号匹配": master.get("起始行专业代号匹配", ""),
            "私有页图证据编号": master.get("私有页图证据编号", ""),
            "私有页图SHA256": master.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": master.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": master.get("私有OCR文本SHA256", ""),
            "结构保真风险标签": "；".join(labels) if labels else "暂未触发结构保真专项风险",
            "结构保真优先级": priority,
            "必须人工核PDF原页": "true",
            "必须湖北官方系统或省招办计划核验": "true",
            "机器能否自动修复": "false",
            "不得进入原因": "结构保真未闭环；确认前不得进入最终志愿排序",
            "下一步": "按结构保真优先级回看 PDF 原页、组边界和专业代号，再用湖北官方系统或省招办计划核验。",
        })

    risk_event_rows = []
    for row in register_rows:
        if row["是否唯一组码回退归属"] == "true":
            risk_event_rows.append(risk_event(
                row,
                "唯一组码回退归属",
                "R1-归属或结构异常先核",
                "data/working/issue19-full-admission-plan-major-ocr-draft.csv",
                "专业组标题行号/专业组标题OCR原文",
                row["回退归属风险说明"],
            ))
        if row["是否组内专业代号重复"] == "true":
            risk_event_rows.append(risk_event(
                row,
                "组内专业代号重复",
                "R0-结构边界阻断优先核",
                "data/working/issue19-full-admission-plan-major-ocr-draft.csv",
                "专业代号OCR",
                row["组内重复专业代号风险说明"],
            ))
        if row["规范化专业组代码是否重复"] == "是":
            risk_event_rows.append(risk_event(
                row,
                "2026规范化专业组代码重复",
                "R0-结构边界阻断优先核",
                "data/working/issue19-full-major-detail-quality-workbench.csv",
                "规范化专业组代码是否重复",
                "同一规范化院校专业组代码在第 19 期结构化结果中重复出现，需核原页确认是否串校、跨页或 OCR 切组错误。",
            ))
        if row["原页证据锚点状态"] == "P0-专业窗口为空":
            risk_event_rows.append(risk_event(
                row,
                "原页专业窗口为空",
                "R0-结构边界阻断优先核",
                "data/working/issue19-major-line-pdf-evidence-anchors.csv",
                "证据锚点状态",
                "专业行起始位置已回连，但公开原页证据窗口为空，需直接回看页图和 OCR 行级私有证据。",
            ))
        if row["原页证据锚点状态"] == "P1-缺少组标题上下文":
            risk_event_rows.append(risk_event(
                row,
                "原页缺少组标题上下文",
                "R2-原页上下文补证",
                "data/working/issue19-major-line-pdf-evidence-anchors.csv",
                "证据锚点状态",
                "专业行原页窗口存在，但缺少专业组标题上下文，需核专业组边界和调剂范围。",
            ))

    zero_detail_rows = []
    for index, group in enumerate(group_rows, start=1):
        if as_int(group.get("OCR专业行数")) != 0:
            continue
        group_id = group_ids_by_index[index]
        zero_detail_rows.append({
            "0明细占位ID": stable_id("ZERODETAIL", [group_id]),
            "来源全量专业组OCR初稿": "data/working/issue19-full-admission-plan-group-ocr-draft.csv",
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "issue19_missing_major_detail_group_remediation",
            "主表粒度": "专业明细缺失专业组占位",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "专业组出现ID": group_id,
            "院校代码": group.get("院校代码", ""),
            "院校名称OCR": group.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": group.get("院校专业组代码OCR规范化", ""),
            "来源页码": group.get("来源页码", ""),
            "版面列": group.get("版面列", ""),
            "专业组标题行号": group.get("专业组标题行号", ""),
            "专业组标题OCR原文": group.get("专业组标题OCR原文", ""),
            "OCR专业行数": group.get("OCR专业行数", ""),
            "是否缺失专业明细": "true",
            "是否真实招生明细": "false",
            "是否0明细占位": "true",
            "占位风险类型": "group_without_major_details",
            "缺失明细风险说明": "该专业组当前没有可下沉到逐专业表的招生明细，必须回看原页补齐后才能讨论调剂或专业接受度。",
            "是否可作为招生明细行": "false",
            "必须人工核PDF原页": "true",
            "必须湖北官方系统或省招办计划核验": "true",
            "机器能否自动补齐专业明细": "false",
            "下一步": "回看 PDF 原页和湖北官方系统；补齐真实招生专业明细后再进入逐专业总工作台。",
        })

    write_csv(OUTPUT, register_rows, REGISTER_FIELDS)
    write_csv(RISK_EVENT_OUTPUT, risk_event_rows, RISK_EVENT_FIELDS)
    write_csv(ZERO_DETAIL_OUTPUT, zero_detail_rows, ZERO_DETAIL_FIELDS)

    label_counts = Counter()
    for row in register_rows:
        for label in row["结构保真风险标签"].split("；"):
            if label:
                label_counts[label] += 1

    summary = {
        "status": "issue19_admission_detail_structural_fidelity_not_final",
        "generated_by": "build_issue19_admission_detail_structural_fidelity_register.py",
        "output_table": "data/working/issue19-admission-detail-structural-fidelity-register.csv",
        "risk_event_output_table": "data/working/issue19-structural-risk-major-line-ledger.csv",
        "zero_detail_output_table": "data/working/issue19-zero-detail-group-placeholder-workbench.csv",
        "source_master_workbench": "data/working/issue19-admission-detail-master-workbench.csv",
        "source_major_ocr_draft": "data/working/issue19-full-admission-plan-major-ocr-draft.csv",
        "source_group_ocr_draft": "data/working/issue19-full-admission-plan-group-ocr-draft.csv",
        "source_major_quality_workbench": "data/working/issue19-full-major-detail-quality-workbench.csv",
        "row_count": len(register_rows),
        "unique_register_id_count": len({row["结构保真登记ID"] for row in register_rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in register_rows}),
        "assignment_method_counts": dict(Counter(row["专业组归属方式"] for row in register_rows)),
        "fallback_unique_group_code_major_count": sum(
            row["是否唯一组码回退归属"] == "true" for row in register_rows
        ),
        "duplicate_normalized_group_code_major_count": sum(
            row["规范化专业组代码是否重复"] == "是" for row in register_rows
        ),
        "duplicate_major_code_row_count": sum(
            row["是否组内专业代号重复"] == "true" for row in register_rows
        ),
        "duplicate_major_code_group_count": len(
            {
                row["专业组出现ID"]
                for row in register_rows
                if row["是否组内专业代号重复"] == "true"
            }
        ),
        "anchor_status_counts": dict(Counter(row["原页证据锚点状态"] for row in register_rows)),
        "risk_label_counts": dict(label_counts),
        "structural_priority_counts": dict(Counter(row["结构保真优先级"] for row in register_rows)),
        "risk_event_count": len(risk_event_rows),
        "risk_event_type_counts": dict(Counter(row["结构风险类型"] for row in risk_event_rows)),
        "zero_detail_group_count": len(zero_detail_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in register_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in register_rows),
        "machine_auto_fix_count": sum(row["机器能否自动修复"] == "true" for row in register_rows),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUTPUT.relative_to(ROOT)}：{len(register_rows)} 行")
    print(f"写入 {RISK_EVENT_OUTPUT.relative_to(ROOT)}：{len(risk_event_rows)} 行")
    print(f"写入 {ZERO_DETAIL_OUTPUT.relative_to(ROOT)}：{len(zero_detail_rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
