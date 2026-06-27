#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DIFF_LEDGER = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
DETAIL_EVIDENCE = ROOT / "data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv"
DETAIL_CROSSCHECK = ROOT / "data/working/issue19-candidate-v3-b0-b1-admission-detail-official-crosscheck.csv"
FOUNDATION_CLOSURE = ROOT / "data/working/issue19-foundation-closure-major-batches.csv"

SIDECAR_OUTPUT = ROOT / "data/working/issue19-b0-b1-official-evidence-by-major-line.csv"
FILL_OUTPUT = ROOT / "data/working/issue19-b0-b1-official-plan-fill-candidates.csv"
CONFLICT_OUTPUT = ROOT / "data/working/issue19-b0-b1-official-conflict-review.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-b0-b1-official-evidence-sidecar-summary.json"

DATA_STAGE = "issue19_b0_b1_official_evidence_sidecar"


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


def normalize_text(value):
    return "".join(str(value or "").split())


def closure_match_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化") or row.get("2026院校专业组代码", ""),
        row.get("来源页码", ""),
        row.get("专业组内专业序号", ""),
        row.get("专业代号OCR", ""),
        normalize_text(row.get("专业名称及备注OCR", "")),
    )


def likely_fee_value(value):
    text = str(value or "").strip()
    if not text:
        return "false"
    if "万" in text:
        return "true"
    try:
        number = int("".join(ch for ch in text if ch.isdigit()))
    except ValueError:
        return "false"
    return "true" if number >= 1000 else "false"


def classify(row):
    match_status = row.get("官网证据匹配状态增强") or row.get("官网证据匹配状态")
    plan_status = row.get("计划数核验状态增强") or row.get("计划数核验状态")
    source_status = row.get("官网来源状态增强") or row.get("官网来源状态")
    official_plan = row.get("官网计划数增强") or row.get("最佳官网计划数")
    official_fee = row.get("官网学费增强") or row.get("最佳官网学费")
    official_subject = row.get("官网选科增强") or row.get("最佳官网选科")

    if plan_status in {"match", "官网专业名+计划数一致"}:
        return (
            "strong_support",
            "官网专业名和计划数匹配，可作为强辅证；仍需 PDF 原页和湖北官方系统复核。",
            "PDF原页；湖北官方系统/省招办计划；专业组边界；家庭接受度；调剂范围",
        )
    if plan_status == "ocr_plan_missing_official_available":
        return (
            "fill_candidate",
            "OCR计划数缺失但官网有计划数，可作为计划数补缺候选。",
            "PDF原页计划数列；湖北官方系统/省招办计划；高校官网原始证据",
        )
    if plan_status in {"mismatch", "官网专业名匹配但计划数冲突-优先核页"} or "计划数冲突" in row.get("差异字段集合", ""):
        return (
            "conflict_review",
            "官网专业名匹配但计划数冲突，优先回看原页和字段列。",
            "PDF原页计划数列；湖北官方系统/省招办计划；OCR字段错位排查",
        )
    if match_status in {"matched", "possible_match"} and (official_plan or official_fee or official_subject):
        return (
            "field_support",
            "官网专业名有匹配并提供部分字段，可作为字段辅证候选。",
            "PDF原页；湖北官方系统/省招办计划；高校官网/章程字段口径",
        )
    if source_status == "charter_or_rules_only_no_plan":
        return (
            "rules_only",
            "目前只有章程或规则线索，不能作为逐专业计划证据。",
            "继续补高校逐专业计划源；核招生章程限制项",
        )
    if source_status == "needs_official_plan_source_search" or match_status == "no_school_source":
        return (
            "needs_source",
            "尚无可匹配的高校逐专业计划源。",
            "补高校招生网/计划查询/章程来源；再回到逐专业核验",
        )
    if match_status == "unmatched":
        return (
            "unmatched",
            "已有学校来源但专业未匹配，需核专业名、限定词和是否串校串行。",
            "PDF原页；高校官网原始计划；专业名称限定词人工比对",
        )
    return (
        "partial_source",
        "已有部分官网线索但不足以逐专业匹配。",
        "补结构化高校计划源；PDF原页和湖北官方系统交叉",
    )


def build_rows():
    diff_rows = read_csv(DIFF_LEDGER)
    detail_rows = read_csv(DETAIL_EVIDENCE)
    cross_rows = read_csv(DETAIL_CROSSCHECK)
    closure_rows = read_csv(FOUNDATION_CLOSURE)

    closure_by_major_id = {row.get("专业行ID"): row for row in closure_rows}
    closure_by_match_key = {}
    duplicate_closure_match_keys = set()
    for row in closure_rows:
        key = closure_match_key(row)
        if key in closure_by_match_key:
            duplicate_closure_match_keys.add(key)
        else:
            closure_by_match_key[key] = row

    major_id_by_admission_row_id = {
        row.get("招生明细主表行ID"): row.get("专业行ID", "")
        for row in cross_rows
    }
    detail_by_major_id = {}
    for row in detail_rows:
        major_id = major_id_by_admission_row_id.get(row.get("招生明细主表行ID"), "")
        if not major_id:
            key = closure_match_key(row)
            closure_match = (
                closure_by_match_key.get(key)
                if key not in duplicate_closure_match_keys
                else {}
            ) or {}
            major_id = closure_match.get("专业行ID", "")
        if major_id:
            detail_by_major_id[major_id] = row

    rows = []
    emitted_major_ids = set()
    for diff in diff_rows:
        major_id = diff.get("专业行ID", "")
        detail = detail_by_major_id.get(major_id, {})
        closure = closure_by_major_id.get(major_id, {})
        merged = {
            **diff,
            "官网来源状态增强": detail.get("官网来源状态", diff.get("官网来源状态", "")),
            "官网证据匹配状态增强": detail.get("官网证据匹配状态", diff.get("官网证据匹配状态", "")),
            "官网计划数增强": detail.get("最佳官网计划数", diff.get("最佳官网计划数", "")),
            "官网学费增强": detail.get("最佳官网学费", diff.get("最佳官网学费", "")),
            "官网选科增强": detail.get("最佳官网选科", diff.get("最佳官网选科", "")),
            "计划数核验状态增强": detail.get("计划数核验状态", diff.get("计划数核验状态", "")),
        }
        strength, explanation, action = classify(merged)
        rows.append({
            "官网证据旁挂ID": stable_id("B0B1SIDE", [major_id]),
            "来源招生明细主表行ID": detail.get("招生明细主表行ID", ""),
            "来源公开官网差异账ID": diff.get("公开官网差异账ID", ""),
            "来源底座闭环批次ID": closure.get("底座闭环批次ID", ""),
            "来源逐专业闭环主表": "data/working/issue19-foundation-closure-major-batches.csv",
            "来源公开官网差异账": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
            "来源期号": diff.get("来源期号", ""),
            "来源PDF_SHA256": diff.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "能否替代湖北官方计划": "false",
            "官网证据强度": strength,
            "官网证据说明": explanation,
            "建议动作": action,
            "闭环执行总序": closure.get("闭环执行总序", ""),
            "闭环执行批次": closure.get("闭环执行批次", ""),
            "专业行ID": major_id,
            "专业组出现ID": diff.get("专业组出现ID", ""),
            "院校代码": diff.get("院校代码", ""),
            "院校名称OCR": diff.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": diff.get("院校专业组代码OCR规范化", ""),
            "来源页码": diff.get("来源页码", ""),
            "专业组内专业序号": diff.get("专业组内专业序号", ""),
            "专业代号OCR": diff.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": short_text(diff.get("专业名称及备注OCR短摘")),
            "OCR计划数": diff.get("OCR计划数", ""),
            "OCR学费": diff.get("OCR学费", ""),
            "OCR再选科目": diff.get("OCR再选科目", ""),
            "官网来源状态": merged.get("官网来源状态增强", ""),
            "官网证据匹配状态": merged.get("官网证据匹配状态增强", ""),
            "最佳官网来源文件": diff.get("最佳官网来源文件", ""),
            "最佳官网专业名称": detail.get("最佳官网专业名称", diff.get("最佳官网专业名称", "")),
            "最佳官网专业代号": detail.get("最佳官网专业代号", diff.get("最佳官网专业代号", "")),
            "最佳官网计划数": merged.get("官网计划数增强", ""),
            "最佳官网学费": merged.get("官网学费增强", ""),
            "最佳官网选科": merged.get("官网选科增强", ""),
            "专业名称匹配方式": detail.get("专业名称匹配方式", diff.get("专业名称匹配方式", "")),
            "专业名称匹配分": detail.get("专业名称匹配分", diff.get("专业名称匹配分", "")),
            "计划数核验状态": merged.get("计划数核验状态增强", ""),
            "差异字段集合": diff.get("差异字段集合", ""),
            "疑似OCR把学费读入计划数": (
                "true"
                if strength == "conflict_review" and likely_fee_value(diff.get("OCR计划数", "")) == "true"
                else "false"
            ),
            "仍需核验": diff.get("仍需核验", ""),
            "下一步": "官网证据只作辅证；必须回到 PDF 原页、湖北官方系统/省招办计划、招生章程、家庭接受度和同组调剂结论。",
        })
        emitted_major_ids.add(major_id)

    for major_id, detail in detail_by_major_id.items():
        if major_id in emitted_major_ids:
            continue
        closure = closure_by_major_id.get(major_id, {})
        merged = {
            "官网来源状态增强": detail.get("官网来源状态", ""),
            "官网证据匹配状态增强": detail.get("官网证据匹配状态", ""),
            "官网计划数增强": detail.get("最佳官网计划数", ""),
            "官网学费增强": detail.get("最佳官网学费", ""),
            "官网选科增强": detail.get("最佳官网选科", ""),
            "计划数核验状态增强": detail.get("计划数核验状态", ""),
            "差异字段集合": "",
            "最佳官网计划数": "",
            "最佳官网学费": "",
            "最佳官网选科": "",
        }
        strength, explanation, action = classify(merged)
        rows.append({
            "官网证据旁挂ID": stable_id("B0B1SIDE", [major_id]),
            "来源招生明细主表行ID": detail.get("招生明细主表行ID", ""),
            "来源公开官网差异账ID": "",
            "来源底座闭环批次ID": closure.get("底座闭环批次ID", ""),
            "来源逐专业闭环主表": "data/working/issue19-foundation-closure-major-batches.csv",
            "来源公开官网差异账": "data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv",
            "来源期号": closure.get("来源期号", ""),
            "来源PDF_SHA256": closure.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "能否替代湖北官方计划": "false",
            "官网证据强度": strength,
            "官网证据说明": explanation + " 本行由 B0/B1 细账按闭环主表唯一键回连专业行ID。",
            "建议动作": action,
            "闭环执行总序": closure.get("闭环执行总序", ""),
            "闭环执行批次": closure.get("闭环执行批次", ""),
            "专业行ID": major_id,
            "专业组出现ID": closure.get("专业组出现ID", ""),
            "院校代码": detail.get("院校代码", ""),
            "院校名称OCR": detail.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": detail.get("2026院校专业组代码", ""),
            "来源页码": detail.get("来源页码", ""),
            "专业组内专业序号": detail.get("专业组内专业序号", ""),
            "专业代号OCR": detail.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": short_text(detail.get("专业名称及备注OCR")),
            "OCR计划数": detail.get("专业计划数OCR候选", ""),
            "OCR学费": detail.get("学费OCR候选", ""),
            "OCR再选科目": detail.get("再选科目OCR候选", ""),
            "官网来源状态": detail.get("官网来源状态", ""),
            "官网证据匹配状态": detail.get("官网证据匹配状态", ""),
            "最佳官网来源文件": detail.get("最佳官网来源文件", ""),
            "最佳官网专业名称": detail.get("最佳官网专业名称", ""),
            "最佳官网专业代号": detail.get("最佳官网专业代号", ""),
            "最佳官网计划数": detail.get("最佳官网计划数", ""),
            "最佳官网学费": detail.get("最佳官网学费", ""),
            "最佳官网选科": detail.get("最佳官网选科", ""),
            "专业名称匹配方式": detail.get("专业名称匹配方式", ""),
            "专业名称匹配分": detail.get("专业名称匹配分", ""),
            "计划数核验状态": detail.get("计划数核验状态", ""),
            "差异字段集合": "细账回连补充",
            "疑似OCR把学费读入计划数": (
                "true"
                if strength == "conflict_review" and likely_fee_value(detail.get("专业计划数OCR候选", "")) == "true"
                else "false"
            ),
            "仍需核验": detail.get("仍需核验", ""),
            "下一步": "官网证据只作辅证；必须回到 PDF 原页、湖北官方系统/省招办计划、招生章程、家庭接受度和同组调剂结论。",
        })
        emitted_major_ids.add(major_id)

    rows.sort(key=lambda row: (
        as_int(row.get("闭环执行总序")),
        as_int(row.get("来源页码")),
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        as_int(row.get("专业组内专业序号")),
        row.get("专业行ID", ""),
    ))
    return rows


FIELDS = [
    "官网证据旁挂ID",
    "来源招生明细主表行ID",
    "来源公开官网差异账ID",
    "来源底座闭环批次ID",
    "来源逐专业闭环主表",
    "来源公开官网差异账",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "能否替代湖北官方计划",
    "官网证据强度",
    "官网证据说明",
    "建议动作",
    "闭环执行总序",
    "闭环执行批次",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR短摘",
    "OCR计划数",
    "OCR学费",
    "OCR再选科目",
    "官网来源状态",
    "官网证据匹配状态",
    "最佳官网来源文件",
    "最佳官网专业名称",
    "最佳官网专业代号",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "专业名称匹配方式",
    "专业名称匹配分",
    "计划数核验状态",
    "差异字段集合",
    "疑似OCR把学费读入计划数",
    "仍需核验",
    "下一步",
]


def write_summary(rows, fill_rows, conflict_rows):
    summary = {
        "status": "issue19_b0_b1_official_evidence_sidecar_not_final",
        "generated_by": "build_issue19_b0_b1_official_evidence_sidecar.py",
        "source_public_official_diff_ledger": "data/working/issue19-b0-b1-public-official-diff-ledger.csv",
        "source_detail_evidence_ledger": "data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv",
        "source_detail_official_crosscheck": "data/working/issue19-candidate-v3-b0-b1-admission-detail-official-crosscheck.csv",
        "source_foundation_closure": "data/working/issue19-foundation-closure-major-batches.csv",
        "output_sidecar": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
        "output_fill_candidates": "data/working/issue19-b0-b1-official-plan-fill-candidates.csv",
        "output_conflict_review": "data/working/issue19-b0-b1-official-conflict-review.csv",
        "sidecar_row_count": len(rows),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_school_count": len({row["院校代码"] for row in rows}),
        "evidence_strength_counts": dict(Counter(row["官网证据强度"] for row in rows)),
        "plan_status_counts": dict(Counter(row["计划数核验状态"] for row in rows)),
        "matched_major_name_count": sum(row["官网证据匹配状态"] == "matched" for row in rows),
        "official_plan_non_empty_count": sum(bool(row["最佳官网计划数"]) for row in rows),
        "official_fee_non_empty_count": sum(bool(row["最佳官网学费"]) for row in rows),
        "fill_candidate_row_count": len(fill_rows),
        "conflict_review_row_count": len(conflict_rows),
        "suspected_plan_fee_misread_count": sum(
            row["疑似OCR把学费读入计划数"] == "true" for row in conflict_rows
        ),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "official_plan_replacement_allowed_count": sum(
            row["能否替代湖北官方计划"] == "true" for row in rows
        ),
        "notes": [
            "本表为高校官网/API/PDF/图片证据旁挂表，不是湖北官方计划替代表。",
            "strong_support、fill_candidate、conflict_review 仍必须回到 PDF 原页和湖北官方系统/省招办计划确认。",
            "final_available 和能否替代湖北官方计划均保持 false。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    rows = build_rows()
    fill_rows = [row for row in rows if row["官网证据强度"] == "fill_candidate"]
    conflict_rows = [row for row in rows if row["官网证据强度"] == "conflict_review"]
    write_csv(SIDECAR_OUTPUT, rows, FIELDS)
    write_csv(FILL_OUTPUT, fill_rows, FIELDS)
    write_csv(CONFLICT_OUTPUT, conflict_rows, FIELDS)
    write_summary(rows, fill_rows, conflict_rows)
    print(f"写入 {SIDECAR_OUTPUT.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写入 {FILL_OUTPUT.relative_to(ROOT)}：{len(fill_rows)} 行")
    print(f"写入 {CONFLICT_OUTPUT.relative_to(ROOT)}：{len(conflict_rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
