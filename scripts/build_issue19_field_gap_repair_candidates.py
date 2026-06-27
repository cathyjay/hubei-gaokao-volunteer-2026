#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIELD_GAPS = ROOT / "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv"
FOUNDATION_CLOSURE = ROOT / "data/working/issue19-foundation-closure-major-batches.csv"
GROUP_OCR = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_EVIDENCE = ROOT / "data/working/issue19-full-major-evidence-workbench.csv"

OUTPUT = ROOT / "data/working/issue19-field-gap-repair-candidates.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-gap-repair-candidates-summary.json"

DATA_STAGE = "issue19_field_gap_repair_candidates"


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


def short_text(value, limit=120):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def group_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        row.get("来源页码", ""),
        row.get("版面列", ""),
    )


def normalize_reselect(raw):
    text = str(raw or "").strip()
    if not text:
        return "", "无候选", "none", "组级 OCR 未给出再选科目候选。"

    subject_tokens = []
    if "不限" in text:
        subject_tokens.append("不限")
    if "化学" in text:
        subject_tokens.append("化学")
    if "生物" in text:
        subject_tokens.append("生物")
    if "政治" in text or "思想政治" in text:
        subject_tokens.append("政治")
    if "地理" in text:
        subject_tokens.append("地理")
    subject_tokens = list(dict.fromkeys(subject_tokens))

    if not subject_tokens:
        return "", "无明确候选", "none", "组级 OCR 字符串未识别出明确的不限/化学/生物/政治/地理。"

    if "不限" in subject_tokens and len(subject_tokens) > 1:
        return "；".join(subject_tokens), "冲突候选", "low", "同一组级 OCR 候选同时含不限和具体科目，必须回看原页。"

    if len(subject_tokens) > 1:
        return "；".join(subject_tokens), "多科目候选", "low", "同一组级 OCR 候选含多个再选科目词，必须回看原页确认是否为串列。"

    value = subject_tokens[0]
    cleaned = re.sub(r"[\\s\\[\\]【】（）()「」『』；:：、,，。·]", "", text)
    if cleaned == value:
        return value, "组级OCR清晰候选", "medium", "组级 OCR 候选可读，但仍需 PDF 原页和湖北官方系统确认。"
    return value, "组级OCR含噪候选", "low", "组级 OCR 含页眉/标点/错字噪声，只能作为回看原页线索。"


def numeric_text(value):
    return "".join(re.findall(r"\d+", str(value or "")))


def classify_plan_candidate(gap_row, evidence_row):
    ocr = gap_row.get("OCR候选值", "")
    official = evidence_row.get("最佳官网计划数", "")
    if official:
        return official, "高校官网辅证计划数候选", "medium", "高校官网/API/PDF/图片证据可作为辅证，但不能替代湖北官方系统或 PDF 原页。"
    if not ocr:
        return "", "无候选", "none", "OCR 未给出计划数候选。"
    digits = numeric_text(ocr)
    if digits and 0 < int(digits) <= 300:
        return ocr, "OCR计划数候选待回看", "low", "OCR 值处于计划数常见范围，但字段已被风险规则命中，需原页和官方系统确认。"
    return ocr, "疑似错列候选", "low", "OCR 值不符合计划数常见范围，可能串入学费或备注列。"


def classify_fee_candidate(gap_row, evidence_row):
    ocr = gap_row.get("OCR候选值", "")
    official = evidence_row.get("最佳官网学费", "")
    if official:
        return official, "高校官网辅证学费候选", "medium", "高校官网/API/PDF/图片证据可作为辅证，但不能替代湖北官方系统、PDF 原页或招生章程。"
    if not ocr:
        return "", "无候选", "none", "OCR 未给出学费候选。"
    if "万" in ocr:
        return ocr, "OCR学费中文金额候选", "low", "OCR 含万元写法，需确认是否为中外合作/高收费备注及年学费口径。"
    digits = numeric_text(ocr)
    if digits and 1000 <= int(digits) <= 200000:
        return ocr, "OCR学费候选待回看", "low", "OCR 值处于学费常见范围，但字段已被风险规则命中，需原页和章程确认。"
    return ocr, "疑似错列候选", "low", "OCR 值不符合学费常见范围，可能串入计划数或备注列。"


def build_rows():
    gap_rows = read_csv(FIELD_GAPS)
    closure_rows = read_csv(FOUNDATION_CLOSURE)
    group_rows = read_csv(GROUP_OCR)
    evidence_rows = read_csv(FULL_EVIDENCE)

    closure_by_major_id = {row.get("专业行ID"): row for row in closure_rows}
    evidence_by_major_id = {row.get("专业行ID"): row for row in evidence_rows}
    groups_by_key = defaultdict(list)
    for row in group_rows:
        groups_by_key[group_key(row)].append(row)

    rows = []
    for gap in gap_rows:
        closure = closure_by_major_id.get(gap.get("专业行ID"), {})
        evidence = evidence_by_major_id.get(gap.get("专业行ID"), {})
        groups = groups_by_key.get(group_key(gap), [])
        group_join_status = "唯一组级OCR行" if len(groups) == 1 else ("无组级OCR行" if not groups else "多组级OCR行")
        group_raw = groups[0].get("再选科目OCR候选", "") if len(groups) == 1 else ""
        group_value, group_status, group_confidence, group_note = normalize_reselect(group_raw)

        candidate_value = ""
        candidate_status = "无候选"
        confidence = "none"
        evidence_note = ""
        source_type = "none"
        must_manual_reason = "字段缺口必须回看 PDF 原页，并与湖北官方系统/省招办计划交叉。"

        if gap.get("字段名") == "再选科目":
            candidate_value = group_value
            candidate_status = group_status
            confidence = group_confidence
            evidence_note = group_note
            source_type = "group_ocr_context" if group_value else "none"
            if group_join_status != "唯一组级OCR行":
                must_manual_reason = f"{must_manual_reason} 当前专业行与组级 OCR 回连状态为：{group_join_status}。"
        elif gap.get("字段名") == "专业计划数":
            candidate_value, candidate_status, confidence, evidence_note = classify_plan_candidate(gap, evidence)
            source_type = "school_official_auxiliary" if candidate_status.startswith("高校官网") else ("ocr_cell_candidate" if candidate_value else "none")
        elif gap.get("字段名") == "学费":
            candidate_value, candidate_status, confidence, evidence_note = classify_fee_candidate(gap, evidence)
            source_type = "school_official_auxiliary" if candidate_status.startswith("高校官网") else ("ocr_cell_candidate" if candidate_value else "none")

        if source_type == "school_official_auxiliary":
            must_manual_reason = "高校官网证据只能作辅证；仍需 PDF 原页、湖北官方系统/省招办计划和招生章程确认字段口径。"

        rows.append({
            "字段候选任务ID": stable_id("GAPCAND", [gap.get("字段补证任务ID", ""), gap.get("字段名", "")]),
            "来源字段补证任务ID": gap.get("字段补证任务ID", ""),
            "来源底座闭环批次ID": closure.get("底座闭环批次ID", ""),
            "来源统一逐专业底座入口": "data/working/issue19-foundation-closure-major-batches.csv",
            "来源字段缺口矩阵": "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv",
            "来源期号": gap.get("来源期号", ""),
            "来源PDF_SHA256": gap.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×字段缺口×候选修复",
            "最终可用": "false",
            "候选可自动写回主表": "false",
            "候选状态": candidate_status,
            "候选置信等级": confidence,
            "候选来源类型": source_type,
            "候选值": candidate_value,
            "候选证据说明": evidence_note,
            "必须人工核验原因": must_manual_reason,
            "闭环执行总序": closure.get("闭环执行总序", ""),
            "闭环执行批次": closure.get("闭环执行批次", ""),
            "专业行ID": gap.get("专业行ID", ""),
            "专业组出现ID": gap.get("专业组出现ID", ""),
            "院校代码": gap.get("院校代码", ""),
            "院校名称OCR": gap.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": gap.get("院校专业组代码OCR规范化", ""),
            "来源页码": gap.get("来源页码", ""),
            "版面列": gap.get("版面列", ""),
            "专业组内专业序号": gap.get("专业组内专业序号", ""),
            "专业代号OCR": gap.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": short_text(gap.get("专业名称及备注OCR短摘")),
            "字段名": gap.get("字段名", ""),
            "当前OCR候选值": gap.get("OCR候选值", ""),
            "当前OCR数字候选": gap.get("OCR数字候选") or numeric_text(gap.get("OCR候选值", "")),
            "字段问题类型": gap.get("字段问题类型", ""),
            "组级OCR回连状态": group_join_status,
            "组级再选科目OCR候选": group_raw,
            "组级再选科目规范候选": group_value,
            "高校官网计划数候选": evidence.get("最佳官网计划数", ""),
            "高校官网学费候选": evidence.get("最佳官网学费", ""),
            "高校官网辅证状态": evidence.get("高校官网/章程辅证状态", ""),
            "计划数核验状态": evidence.get("计划数核验状态", ""),
            "页级保真队列ID": gap.get("页级保真队列ID", ""),
            "页面复核优先级": gap.get("页面复核优先级", ""),
            "页面阻断等级": gap.get("页面阻断等级", ""),
            "私有页图证据编号": gap.get("私有页图证据编号", ""),
            "私有页图SHA256": gap.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": gap.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": gap.get("私有OCR文本SHA256", ""),
            "下一步": "按候选来源回看 PDF 原页；再用湖北官方系统/省招办计划、高校官网/章程交叉确认；确认前不得写回最终志愿表。",
        })

    rows.sort(key=lambda row: (
        as_int(row.get("闭环执行总序")),
        as_int(row.get("来源页码")),
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        as_int(row.get("专业组内专业序号")),
        {"再选科目": 1, "专业计划数": 2, "学费": 3}.get(row.get("字段名"), 99),
    ))
    return rows


def write_summary(rows):
    summary = {
        "status": "issue19_field_gap_repair_candidates_not_final",
        "generated_by": "build_issue19_field_gap_repair_candidates.py",
        "source_field_gap_matrix": "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv",
        "source_foundation_closure": "data/working/issue19-foundation-closure-major-batches.csv",
        "source_group_ocr": "data/working/issue19-full-admission-plan-group-ocr-draft.csv",
        "source_full_evidence_workbench": "data/working/issue19-full-major-evidence-workbench.csv",
        "output_table": "data/working/issue19-field-gap-repair-candidates.csv",
        "row_count": len(rows),
        "unique_candidate_task_id_count": len({row["字段候选任务ID"] for row in rows}),
        "unique_field_gap_task_id_count": len({row["来源字段补证任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "field_counts": dict(Counter(row["字段名"] for row in rows)),
        "candidate_status_counts": dict(Counter(row["候选状态"] for row in rows)),
        "candidate_source_type_counts": dict(Counter(row["候选来源类型"] for row in rows)),
        "candidate_confidence_counts": dict(Counter(row["候选置信等级"] for row in rows)),
        "group_ocr_join_status_counts": dict(Counter(row["组级OCR回连状态"] for row in rows if row["字段名"] == "再选科目")),
        "non_empty_candidate_value_count": sum(bool(row["候选值"]) for row in rows),
        "auto_write_allowed_count": sum(row["候选可自动写回主表"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "notes": [
            "本表是字段缺口候选修复线索表，不是字段修复结果表。",
            "所有候选均不可自动写回主表，必须经 PDF 原页、湖北官方系统/省招办计划和高校官网/章程交叉确认。",
            "再选科目候选优先来自同一院校专业组 OCR 行；计划数和学费候选优先来自已留存高校官网辅证或当前 OCR 单元格。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    rows = build_rows()
    fields = [
        "字段候选任务ID",
        "来源字段补证任务ID",
        "来源底座闭环批次ID",
        "来源统一逐专业底座入口",
        "来源字段缺口矩阵",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "候选可自动写回主表",
        "候选状态",
        "候选置信等级",
        "候选来源类型",
        "候选值",
        "候选证据说明",
        "必须人工核验原因",
        "闭环执行总序",
        "闭环执行批次",
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
        "字段名",
        "当前OCR候选值",
        "当前OCR数字候选",
        "字段问题类型",
        "组级OCR回连状态",
        "组级再选科目OCR候选",
        "组级再选科目规范候选",
        "高校官网计划数候选",
        "高校官网学费候选",
        "高校官网辅证状态",
        "计划数核验状态",
        "页级保真队列ID",
        "页面复核优先级",
        "页面阻断等级",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "下一步",
    ]
    write_csv(OUTPUT, rows, fields)
    write_summary(rows)
    print(f"写入 {OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
