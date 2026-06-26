#!/usr/bin/env python3
import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DETAIL_LEDGER = ROOT / "data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv"
SCHOOL_SOURCE_QUEUE = ROOT / "data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv"
NORMALIZED_OFFICIAL = ROOT / "data/working/issue19-b0-b1-retained-official-plan-normalized.csv"

PLAN_CONFLICT_OUTPUT = ROOT / "data/working/issue19-b0-b1-plan-conflict-review-queue.csv"
UNMATCHED_MAJOR_OUTPUT = ROOT / "data/working/issue19-b0-b1-unmatched-major-review-queue.csv"
SOURCE_GAP_OUTPUT = ROOT / "data/working/issue19-b0-b1-official-source-gap-priority.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-b0-b1-fidelity-review-summary.json"


PLAN_CONFLICT_FIELDS = [
    "复核优先级",
    "冲突类型",
    "招生明细主表行ID",
    "来源页码",
    "院校代码",
    "院校名称",
    "2026院校专业组代码",
    "专业代号OCR",
    "专业名称及备注OCR",
    "OCR计划数候选",
    "官网专业名称",
    "官网计划数",
    "官网学费",
    "官网来源文件",
    "保真处理状态",
    "保真诊断",
    "计划数候选引用方式",
    "核页重点",
    "下一步",
]

UNMATCHED_MAJOR_FIELDS = [
    "复核优先级",
    "未匹配类型",
    "招生明细主表行ID",
    "来源页码",
    "院校代码",
    "院校名称",
    "2026院校专业组代码",
    "专业代号OCR",
    "专业名称及备注OCR",
    "OCR计划数候选",
    "官网来源状态",
    "官网证据覆盖结论",
    "专业名称匹配方式",
    "仍需核验",
    "核页重点",
    "下一步",
]

SOURCE_GAP_FIELDS = [
    "补源优先级",
    "结构化证据缺口类型",
    "院校代码",
    "院校名称",
    "官网来源状态",
    "B0B1专业组数",
    "逐专业核验任务数",
    "涉及专业组代码",
    "官网URL",
    "本地留存状态",
    "是否可核湖北2026",
    "可核字段",
    "局限性",
    "官方源缺口",
    "下一步",
]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_int(value):
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def has_next_school_noise(text):
    return bool(re.search(r"[A-Z]\d{3,4}\s*[\u4e00-\u9fff]{2,}", str(text or "")))


def classify_plan_conflict(row):
    ocr_plan = as_int(row.get("专业计划数OCR候选"))
    official_plan = as_int(row.get("最佳官网计划数"))
    official_fee = as_int(row.get("最佳官网学费"))
    text = row.get("专业名称及备注OCR", "")
    if ocr_plan is not None and official_fee is not None and ocr_plan == official_fee:
        return "OCR计划数疑似误取学费"
    if ocr_plan is not None and official_plan is not None and ocr_plan >= 1000 and official_plan <= 20:
        return "OCR计划数疑似列错位"
    if "." in str(row.get("专业计划数OCR候选", "")):
        return "OCR计划数字段含标点"
    if has_next_school_noise(text):
        return "专业名称疑似串入下一院校"
    return "OCR计划数与官网计划数不一致"


def conflict_priority(row, conflict_type):
    if "误取学费" in conflict_type or "列错位" in conflict_type:
        return "P0-计划数疑似学费错位"
    if "数字媒体技术" in row.get("专业名称及备注OCR", ""):
        return "P0-偏好专业计划数冲突"
    return "P1-计划数冲突待核页"


def conflict_focus(row, conflict_type):
    return "；".join(
        [
            "回看第19期PDF原页计划数列和学费列",
            "核湖北官方系统同专业组同专业代号",
            "对照高校官网计划数和学费",
            f"当前冲突类型：{conflict_type}",
        ]
    )


def conflict_diagnosis(row, conflict_type):
    if "误取学费" in conflict_type:
        return "OCR计划数与官网学费一致，初判为计划数列/学费列错位；官网计划数只能作为候选值，仍需核PDF原页和湖北官方系统。"
    if row.get("专业名称匹配方式") == "contains_after_normalization":
        return "官网专业名为包含式匹配，计划数差异可能来自OCR截断、专业方向差异或官网口径差异，不能自动改数。"
    return "OCR计划数与官网计划数不一致，需以PDF原页和湖北官方系统逐字段复核后定值。"


def plan_candidate_usage(row, conflict_type):
    if "误取学费" in conflict_type:
        return f"官网计划数候选={row.get('最佳官网计划数', '')}；不得直接写入最终表，先核原页计划数列。"
    return "不自动给出修正值；先核专业名是否同一专业、是否同一招生口径。"


def build_plan_conflicts(ledger_rows):
    rows = []
    for row in ledger_rows:
        if row.get("计划数核验状态") != "mismatch":
            continue
        conflict_type = classify_plan_conflict(row)
        rows.append(
            {
                "复核优先级": conflict_priority(row, conflict_type),
                "冲突类型": conflict_type,
                "招生明细主表行ID": row.get("招生明细主表行ID", ""),
                "来源页码": row.get("来源页码", ""),
                "院校代码": row.get("院校代码", ""),
                "院校名称": row.get("院校名称OCR", ""),
                "2026院校专业组代码": row.get("2026院校专业组代码", ""),
                "专业代号OCR": row.get("专业代号OCR", ""),
                "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
                "OCR计划数候选": row.get("专业计划数OCR候选", ""),
                "官网专业名称": row.get("最佳官网专业名称", ""),
                "官网计划数": row.get("最佳官网计划数", ""),
                "官网学费": row.get("最佳官网学费", ""),
                "官网来源文件": row.get("最佳官网来源文件", ""),
                "保真处理状态": row.get("保真处理状态", ""),
                "保真诊断": conflict_diagnosis(row, conflict_type),
                "计划数候选引用方式": plan_candidate_usage(row, conflict_type),
                "核页重点": conflict_focus(row, conflict_type),
                "下一步": "先核PDF原页同一行，再核湖北官方系统；若PDF与高校官网冲突，以湖北省招办渠道为准并记录差异。",
            }
        )
    return rows


def is_suspect_code_noise(row):
    code = str(row.get("专业代号OCR") or "").strip()
    text = str(row.get("专业名称及备注OCR") or "").strip()
    if not code or code.isdigit():
        return False
    if text in {"。", ".", ""}:
        return True
    if "院校代号" in text or "及专业代号" in text:
        return True
    return bool(re.fullmatch(r"[GK]A", code) and len(text) <= 8)


def has_key_qualifier_gap(row):
    method = row.get("专业名称匹配方式", "")
    text = row.get("专业名称及备注OCR", "")
    return method == "unmatched_missing_key_qualifier" or any(
        token in text for token in ["面向武汉", "面向武", "中外合作", "英才班", "卓越班", "实验班", "游戏科学", "师范"]
    )


def unmatched_priority(row):
    if row.get("是否0明细占位") == "true":
        return "P0-0明细占位先定位专业组"
    if is_suspect_code_noise(row):
        return "P0-专业代号非数字疑似OCR噪声"
    if has_key_qualifier_gap(row):
        return "P0-关键限定词未获官网覆盖"
    if "数字媒体技术" in row.get("专业名称及备注OCR", ""):
        return "P0-偏好专业未匹配"
    if has_next_school_noise(row.get("专业名称及备注OCR", "")):
        return "P0-疑似串校串行"
    return "P1-官网未匹配待核"


def unmatched_type(row):
    if row.get("是否0明细占位") == "true":
        return "0明细占位"
    if is_suspect_code_noise(row):
        return "专业代号非数字疑似OCR噪声"
    if has_key_qualifier_gap(row):
        return "官网留存证据未覆盖关键限定词专业"
    if row.get("官网证据匹配状态") == "no_school_source":
        return "无可匹配结构化官网证据"
    if has_next_school_noise(row.get("专业名称及备注OCR", "")):
        return "OCR专业名疑似串入下一院校"
    return "官网留存证据未匹配该专业"


def build_unmatched_rows(ledger_rows):
    rows = []
    for row in ledger_rows:
        if row.get("官网证据匹配状态") not in {"unmatched", "possible_match"}:
            continue
        kind = unmatched_type(row)
        rows.append(
            {
                "复核优先级": unmatched_priority(row),
                "未匹配类型": kind,
                "招生明细主表行ID": row.get("招生明细主表行ID", ""),
                "来源页码": row.get("来源页码", ""),
                "院校代码": row.get("院校代码", ""),
                "院校名称": row.get("院校名称OCR", ""),
                "2026院校专业组代码": row.get("2026院校专业组代码", ""),
                "专业代号OCR": row.get("专业代号OCR", ""),
                "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
                "OCR计划数候选": row.get("专业计划数OCR候选", ""),
                "官网来源状态": row.get("官网来源状态", ""),
                "官网证据覆盖结论": row.get("官网证据覆盖结论", ""),
                "专业名称匹配方式": row.get("专业名称匹配方式", ""),
                "仍需核验": row.get("仍需核验", ""),
                "核页重点": "回看PDF原页专业名、专业代号和相邻行；确认是否OCR错字、串校、漏专业或高校官网表未覆盖。",
                "下一步": "先核PDF原页，再核湖北官方系统专业组完整专业；必要时补高校官网计划或章程。",
            }
        )
    return rows


def source_gap_kind(row, retained_school_names):
    name = row.get("院校名称OCR", "")
    status = row.get("官网来源状态", "")
    if status == "needs_official_plan_source_search":
        return "需继续寻找高校官网湖北2026计划"
    if name not in retained_school_names:
        return "有官网线索但尚未结构化到逐专业证据"
    if status == "charter_or_rules_only_no_plan":
        return "仅章程规则线索"
    return "已有结构化证据但仍需省招办闭环"


def source_gap_priority(row, kind):
    if row.get("官网来源状态") == "needs_official_plan_source_search":
        return "P0-待补官方计划源"
    if "尚未结构化" in kind:
        return "P1-已有线索待结构化"
    return "P2-已有证据待闭环"


def build_source_gap_rows(school_rows, normalized_rows):
    retained_school_names = {row.get("学校名称") for row in normalized_rows}
    rows = []
    for row in school_rows:
        kind = source_gap_kind(row, retained_school_names)
        if kind == "已有结构化证据但仍需省招办闭环":
            continue
        priority = source_gap_priority(row, kind)
        rows.append(
            {
                "补源优先级": priority,
                "结构化证据缺口类型": kind,
                "院校代码": row.get("院校代码", ""),
                "院校名称": row.get("院校名称OCR", ""),
                "官网来源状态": row.get("官网来源状态", ""),
                "B0B1专业组数": row.get("B0B1专业组数", ""),
                "逐专业核验任务数": row.get("逐专业核验任务数", ""),
                "涉及专业组代码": row.get("涉及专业组代码", ""),
                "官网URL": row.get("官网URL", ""),
                "本地留存状态": row.get("本地留存状态", ""),
                "是否可核湖北2026": row.get("是否可核湖北2026", ""),
                "可核字段": row.get("可核字段", ""),
                "局限性": row.get("局限性", ""),
                "官方源缺口": row.get("官方源缺口", ""),
                "下一步": row.get("下一步", ""),
            }
        )
    rows.sort(key=lambda r: (r["补源优先级"], -as_int(r["逐专业核验任务数"] or 0), r["院校代码"]))
    return rows


def main():
    ledger_rows = read_csv(DETAIL_LEDGER)
    school_rows = read_csv(SCHOOL_SOURCE_QUEUE)
    normalized_rows = read_csv(NORMALIZED_OFFICIAL)

    conflict_rows = build_plan_conflicts(ledger_rows)
    unmatched_rows = build_unmatched_rows(ledger_rows)
    source_gap_rows = build_source_gap_rows(school_rows, normalized_rows)

    write_csv(PLAN_CONFLICT_OUTPUT, conflict_rows, PLAN_CONFLICT_FIELDS)
    write_csv(UNMATCHED_MAJOR_OUTPUT, unmatched_rows, UNMATCHED_MAJOR_FIELDS)
    write_csv(SOURCE_GAP_OUTPUT, source_gap_rows, SOURCE_GAP_FIELDS)

    summary = {
        "status": "b0_b1_fidelity_review_queues_not_final",
        "generated_by": "scripts/build_issue19_b0_b1_fidelity_review_queues.py",
        "inputs": [
            str(DETAIL_LEDGER.relative_to(ROOT)),
            str(SCHOOL_SOURCE_QUEUE.relative_to(ROOT)),
            str(NORMALIZED_OFFICIAL.relative_to(ROOT)),
        ],
        "plan_conflict_row_count": len(conflict_rows),
        "plan_conflict_type_counts": dict(Counter(row["冲突类型"] for row in conflict_rows)),
        "plan_conflict_school_counts": dict(Counter(row["院校名称"] for row in conflict_rows)),
        "unmatched_major_row_count": len(unmatched_rows),
        "unmatched_major_type_counts": dict(Counter(row["未匹配类型"] for row in unmatched_rows)),
        "source_gap_school_count": len(source_gap_rows),
        "source_gap_type_counts": dict(Counter(row["结构化证据缺口类型"] for row in source_gap_rows)),
        "source_gap_priority_counts": dict(Counter(row["补源优先级"] for row in source_gap_rows)),
        "notes": [
            "本摘要只用于安排人工核页和补源，不是最终志愿方案。",
            "计划数冲突必须先回看第19期PDF原页，再核湖北官方系统；高校官网只作交叉校验。",
            "source_gap 中的 P1 代表已有官网线索但尚未结构化，不等于完全没有官网来源。",
            "带面向武汉、实验班、英才班、中外合作等关键限定词的专业，不得用泛化专业官网计划数替代。",
        ],
        "outputs": [
            str(PLAN_CONFLICT_OUTPUT.relative_to(ROOT)),
            str(UNMATCHED_MAJOR_OUTPUT.relative_to(ROOT)),
            str(SOURCE_GAP_OUTPUT.relative_to(ROOT)),
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出计划数冲突复核队列：{PLAN_CONFLICT_OUTPUT}")
    print(f"写出专业未匹配复核队列：{UNMATCHED_MAJOR_OUTPUT}")
    print(f"写出学校补源缺口优先表：{SOURCE_GAP_OUTPUT}")
    print(f"写出保真复核摘要：{SUMMARY_OUTPUT}")
    print(f"计划数冲突行数：{len(conflict_rows)}")
    print(f"专业未匹配行数：{len(unmatched_rows)}")
    print(f"补源缺口学校数：{len(source_gap_rows)}")


if __name__ == "__main__":
    main()
