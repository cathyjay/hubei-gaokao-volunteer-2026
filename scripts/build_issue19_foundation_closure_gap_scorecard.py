#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FOUNDATION_CLOSURE = ROOT / "data/working/issue19-foundation-closure-major-batches.csv"
FOUNDATION_RELEASE = ROOT / "data/working/issue19-major-detail-foundation-release.csv"
FIELD_CANDIDATES = ROOT / "data/working/issue19-field-gap-repair-candidates.csv"
B0_B1_SIDECAR = ROOT / "data/working/issue19-b0-b1-official-evidence-by-major-line.csv"
PDF_ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"

OUTPUT = ROOT / "data/working/issue19-foundation-closure-gap-scorecard.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-foundation-closure-gap-scorecard-summary.json"

DATA_STAGE = "issue19_foundation_closure_gap_scorecard"


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


def split_items(value):
    return [part.strip() for part in str(value or "").split("；") if part.strip()]


def join_unique(values):
    seen = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.append(text)
    return "；".join(seen)


def short_text(value, limit=120):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def build_indexes():
    closure_rows = read_csv(FOUNDATION_CLOSURE)
    release_rows = read_csv(FOUNDATION_RELEASE)
    field_candidate_rows = read_csv(FIELD_CANDIDATES)
    sidecar_rows = read_csv(B0_B1_SIDECAR)
    anchor_rows = read_csv(PDF_ANCHORS)

    field_candidates_by_major = defaultdict(list)
    for row in field_candidate_rows:
        field_candidates_by_major[row.get("专业行ID", "")].append(row)

    sidecar_by_major = defaultdict(list)
    for row in sidecar_rows:
        sidecar_by_major[row.get("专业行ID", "")].append(row)

    return {
        "closure_rows": closure_rows,
        "release_by_major": {row.get("专业行ID", ""): row for row in release_rows},
        "field_candidates_by_major": field_candidates_by_major,
        "sidecar_by_major": sidecar_by_major,
        "anchor_by_major": {row.get("专业行ID", ""): row for row in anchor_rows},
    }


def candidate_counts(rows):
    non_empty = [row for row in rows if row.get("候选值")]
    medium = [row for row in non_empty if row.get("候选置信等级") == "medium"]
    low = [row for row in non_empty if row.get("候选置信等级") == "low"]
    source_types = Counter(row.get("候选来源类型", "") for row in non_empty)
    statuses = Counter(row.get("候选状态", "") for row in rows)
    fields_with_candidate = join_unique(row.get("字段名") for row in non_empty)
    return {
        "non_empty": len(non_empty),
        "medium": len(medium),
        "low": len(low),
        "source_types": source_types,
        "statuses": statuses,
        "fields_with_candidate": fields_with_candidate,
    }


def official_strength(sidecar_rows):
    if not sidecar_rows:
        return "", "", "", "false"
    strengths = join_unique(row.get("官网证据强度") for row in sidecar_rows)
    actions = join_unique(row.get("建议动作") for row in sidecar_rows)
    plan_status = join_unique(row.get("官网计划数核验状态") or row.get("计划数状态") for row in sidecar_rows)
    can_replace = "true" if any(row.get("能否替代湖北官方计划") == "true" for row in sidecar_rows) else "false"
    return strengths, plan_status, actions, can_replace


def need_bool(condition):
    return "true" if condition else "false"


def action_bucket(row, field_counts, sidecar_rows, anchor_row):
    batch = row.get("闭环执行批次", "")
    field_candidates = field_counts["non_empty"]
    side_strength = {item for item in split_items(official_strength(sidecar_rows)[0])}
    anchor_status = anchor_row.get("证据锚点状态", "")

    if batch.startswith("C0"):
        if "conflict_review" in side_strength:
            return "S0-B0B1冲突+P0原页优先"
        if "strong_support" in side_strength or "fill_candidate" in side_strength:
            return "S1-P0原页+官网辅证同步核"
        return "S2-P0原页结构和字段先核"
    if batch.startswith("C1"):
        if field_candidates:
            return "S3-字段缺口有候选先核"
        return "S4-字段缺口无候选需原页重读"
    if batch.startswith("C2"):
        return "S5-官网辅证交叉核验"
    if batch.startswith("C3"):
        return "S6-常规三方闭环"
    if batch.startswith("C4"):
        if anchor_status and not anchor_status.startswith("P2"):
            return "S7-低风险但证据锚点异常抽检"
        return "S8-低风险抽检"
    return "S9-未分类待复核"


def score(row, field_counts, sidecar_rows, anchor_row):
    base = as_int(row.get("闭环执行排序分"))
    if not base:
        base = as_int(row.get("闭环执行总序")) + 600000
    side_strength = {item for item in split_items(official_strength(sidecar_rows)[0])}
    if "conflict_review" in side_strength:
        base -= 2000
    if "fill_candidate" in side_strength:
        base -= 900
    if "strong_support" in side_strength:
        base -= 700
    if field_counts["medium"]:
        base -= 500
    elif field_counts["non_empty"]:
        base -= 250
    if anchor_row.get("证据锚点状态", "").startswith(("P0", "P1")):
        base -= 150
    return base


def machine_help_level(field_counts, sidecar_rows, anchor_row):
    side_strength = {item for item in split_items(official_strength(sidecar_rows)[0])}
    signals = []
    if field_counts["medium"]:
        signals.append("字段中置信候选")
    elif field_counts["non_empty"]:
        signals.append("字段低置信候选")
    if "strong_support" in side_strength:
        signals.append("官网强辅证")
    if "fill_candidate" in side_strength:
        signals.append("官网补缺候选")
    if "conflict_review" in side_strength:
        signals.append("官网冲突核页")
    if anchor_row.get("证据锚点状态", "").startswith("P2"):
        signals.append("专业行OCR锚点")
    if not signals:
        return "M0-暂无机器补线索"
    return "M1-" + "；".join(signals)


def build_rows():
    indexes = build_indexes()
    rows = []
    for closure in indexes["closure_rows"]:
        major_id = closure.get("专业行ID", "")
        release = indexes["release_by_major"].get(major_id, {})
        field_candidate_rows = indexes["field_candidates_by_major"].get(major_id, [])
        sidecar_rows = indexes["sidecar_by_major"].get(major_id, [])
        anchor = indexes["anchor_by_major"].get(major_id, {})
        field_counts = candidate_counts(field_candidate_rows)
        strengths, plan_status, official_actions, can_replace = official_strength(sidecar_rows)
        must_pdf = True
        must_official = True
        must_family = True
        must_transfer = True
        bucket = action_bucket(closure, field_counts, sidecar_rows, anchor)

        rows.append({
            "闭环缺口看板ID": stable_id("GAPSCORE", [major_id]),
            "来源逐专业闭环主表": "data/working/issue19-foundation-closure-major-batches.csv",
            "来源统一逐专业底座入口": "data/working/issue19-major-detail-foundation-release.csv",
            "来源字段候选表": "data/working/issue19-field-gap-repair-candidates.csv",
            "来源B0B1官网旁挂表": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
            "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
            "来源期号": closure.get("来源期号", ""),
            "来源PDF_SHA256": closure.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "最终志愿排序门禁": "阻断-待证据闭环",
            "专业行ID": major_id,
            "专业组出现ID": closure.get("专业组出现ID", ""),
            "院校代码": closure.get("院校代码", ""),
            "院校名称OCR": closure.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": closure.get("院校专业组代码OCR规范化", ""),
            "来源页码": closure.get("来源页码", ""),
            "版面列": closure.get("版面列", ""),
            "专业组内专业序号": closure.get("专业组内专业序号", ""),
            "专业代号OCR": closure.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": short_text(closure.get("专业名称及备注OCR")),
            "闭环执行总序": closure.get("闭环执行总序", ""),
            "闭环执行批次": closure.get("闭环执行批次", ""),
            "首要核验动作": closure.get("首要核验动作", ""),
            "闭环执行动作集合": closure.get("闭环执行动作集合", ""),
            "看板动作桶": bucket,
            "看板排序分": str(score(closure, field_counts, sidecar_rows, anchor)),
            "机器可辅助线索": machine_help_level(field_counts, sidecar_rows, anchor),
            "必须人工核PDF原页": need_bool(must_pdf),
            "必须湖北官方系统或省招办计划核验": need_bool(must_official),
            "必须家庭接受度确认": need_bool(must_family),
            "必须同组调剂结论确认": need_bool(must_transfer),
            "字段缺口字段": closure.get("字段缺口字段", ""),
            "字段缺口数": closure.get("字段缺口数", ""),
            "字段候选任务数": str(len(field_candidate_rows)),
            "非空字段候选数": str(field_counts["non_empty"]),
            "中置信字段候选数": str(field_counts["medium"]),
            "低置信字段候选数": str(field_counts["low"]),
            "有候选字段": field_counts["fields_with_candidate"],
            "字段候选状态分布": "；".join(f"{key}:{value}" for key, value in field_counts["statuses"].items() if key),
            "字段候选来源分布": "；".join(f"{key}:{value}" for key, value in field_counts["source_types"].items() if key),
            "B0B1官网证据任务数": str(len(sidecar_rows)),
            "B0B1官网证据强度": strengths,
            "B0B1计划数状态": plan_status,
            "B0B1官网建议动作": official_actions,
            "官网证据能否替代湖北官方计划": can_replace,
            "专业行原页证据锚点ID": anchor.get("专业行原页证据锚点ID", ""),
            "原页证据锚点状态": anchor.get("证据锚点状态", ""),
            "专业窗口行号范围": anchor.get("专业窗口行号范围", ""),
            "合并证据窗口行数": anchor.get("合并证据窗口行数", ""),
            "窗口文本SHA256": anchor.get("窗口文本SHA256", ""),
            "起始行专业代号匹配": anchor.get("起始行专业代号匹配", ""),
            "页级复核优先级": closure.get("页级复核优先级", ""),
            "页级阻断等级": closure.get("页级阻断等级", ""),
            "P0复核任务数": closure.get("P0复核任务数", ""),
            "P0证据项": closure.get("P0证据项", ""),
            "湖北官方平台字段核验状态": closure.get("湖北官方平台字段核验状态", ""),
            "家庭接受度结论": closure.get("家庭接受度结论", ""),
            "同组调剂结论": closure.get("同组调剂结论", ""),
            "机器专业接受度初判": closure.get("机器专业接受度初判", ""),
            "调剂影响等级": closure.get("调剂影响等级", ""),
            "专业偏好方向": closure.get("专业偏好方向", ""),
            "风险阻断等级": closure.get("风险阻断等级", ""),
            "三年投档稳定性状态": closure.get("三年投档稳定性状态", ""),
            "不得进入原因": release.get("不得进入原因") or closure.get("不得进入原因", ""),
            "下一步": (
                "按看板动作桶顺序核验：先打开专业行原页证据锚点和字段候选，"
                "再核 PDF 原页、湖北官方系统/省招办计划、高校官网/章程、家庭接受度和同组调剂；"
                "确认前不得进入最终志愿排序。"
            ),
        })

    rows.sort(key=lambda row: (
        as_int(row["看板排序分"]),
        as_int(row["闭环执行总序"]),
        row["专业行ID"],
    ))
    for index, row in enumerate(rows, start=1):
        row["看板执行总序"] = str(index)
    return rows


def write_summary(rows):
    summary = {
        "status": "issue19_foundation_closure_gap_scorecard_not_final",
        "generated_by": "build_issue19_foundation_closure_gap_scorecard.py",
        "output_table": "data/working/issue19-foundation-closure-gap-scorecard.csv",
        "source_foundation_closure": "data/working/issue19-foundation-closure-major-batches.csv",
        "source_field_candidates": "data/working/issue19-field-gap-repair-candidates.csv",
        "source_b0_b1_sidecar": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
        "source_pdf_anchors": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "row_count": len(rows),
        "unique_scorecard_id_count": len({row["闭环缺口看板ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "batch_counts": dict(Counter(row["闭环执行批次"] for row in rows)),
        "action_bucket_counts": dict(Counter(row["看板动作桶"] for row in rows)),
        "machine_help_counts": dict(Counter(row["机器可辅助线索"] for row in rows)),
        "non_empty_field_candidate_major_count": sum(as_int(row["非空字段候选数"]) > 0 for row in rows),
        "b0_b1_sidecar_major_count": sum(as_int(row["B0B1官网证据任务数"]) > 0 for row in rows),
        "pdf_anchor_major_count": sum(bool(row["专业行原页证据锚点ID"]) for row in rows),
        "official_replace_allowed_count": sum(row["官网证据能否替代湖北官方计划"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "notes": [
            "本表是逐专业闭环缺口看板，不是最终志愿方案。",
            "所有行仍需 PDF 原页、湖北官方系统/省招办计划、高校官网/章程、家庭接受度和同组调剂结论闭环。",
            "字段候选、官网辅证和 OCR 锚点只能加速核验，不得自动写回最终事实表。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


FIELDS = [
    "闭环缺口看板ID",
    "来源逐专业闭环主表",
    "来源统一逐专业底座入口",
    "来源字段候选表",
    "来源B0B1官网旁挂表",
    "来源专业行原页证据锚点表",
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
    "专业名称及备注OCR短摘",
    "闭环执行总序",
    "看板执行总序",
    "闭环执行批次",
    "首要核验动作",
    "闭环执行动作集合",
    "看板动作桶",
    "看板排序分",
    "机器可辅助线索",
    "必须人工核PDF原页",
    "必须湖北官方系统或省招办计划核验",
    "必须家庭接受度确认",
    "必须同组调剂结论确认",
    "字段缺口字段",
    "字段缺口数",
    "字段候选任务数",
    "非空字段候选数",
    "中置信字段候选数",
    "低置信字段候选数",
    "有候选字段",
    "字段候选状态分布",
    "字段候选来源分布",
    "B0B1官网证据任务数",
    "B0B1官网证据强度",
    "B0B1计划数状态",
    "B0B1官网建议动作",
    "官网证据能否替代湖北官方计划",
    "专业行原页证据锚点ID",
    "原页证据锚点状态",
    "专业窗口行号范围",
    "合并证据窗口行数",
    "窗口文本SHA256",
    "起始行专业代号匹配",
    "页级复核优先级",
    "页级阻断等级",
    "P0复核任务数",
    "P0证据项",
    "湖北官方平台字段核验状态",
    "家庭接受度结论",
    "同组调剂结论",
    "机器专业接受度初判",
    "调剂影响等级",
    "专业偏好方向",
    "风险阻断等级",
    "三年投档稳定性状态",
    "不得进入原因",
    "下一步",
]


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    write_summary(rows)
    print(f"写出逐专业闭环缺口看板：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
