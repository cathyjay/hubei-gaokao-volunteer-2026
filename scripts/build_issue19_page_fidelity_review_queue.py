#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
FOUNDATION_PAGE_AUDIT = ROOT / "data/working/issue19-foundation-page-audit.csv"
FULL_MAJOR_FIDELITY = ROOT / "data/working/issue19-full-major-field-fidelity-ledger.csv"

OUTPUT = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-page-fidelity-review-queue-summary.json"

DATA_STAGE = "issue19_page_fidelity_review_queue"


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


def split_flags(value):
    return [part for part in str(value or "").split("；") if part]


def join_top(counter, limit=8):
    return "；".join(f"{key}:{value}" for key, value in counter.most_common(limit) if key)


def page_priority(stats, manifest_row):
    if (
        stats["候选池V1专业明细数"] > 0
        or stats["F0行数"] > 0
        or stats["空专业名行数"] > 0
        or stats["高严重结构异常专业行数"] > 0
        or as_int(manifest_row.get("候选V2字段P0任务数")) > 0
        or as_int(manifest_row.get("高严重结构异常数")) > 0
    ):
        return "P0-必须优先核页"
    if (
        stats["F1行数"] > 0
        or stats["计划数字段风险行数"] > 0
        or stats["学费字段风险行数"] > 0
        or as_int(manifest_row.get("OCR_QC_P0数")) > 0
    ):
        return "P1-字段高风险核页"
    if stats["偏好专业行数"] > 0 or stats["家庭底线风险行数"] > 0:
        return "P2-偏好和家庭底线核页"
    return "P3-抽检核页"


def main():
    manifest_rows = read_csv(PAGE_MANIFEST)
    foundation_rows = read_csv(FOUNDATION_PAGE_AUDIT)
    fidelity_rows = read_csv(FULL_MAJOR_FIDELITY)

    manifest_by_page = {as_int(row.get("PDF页码")): row for row in manifest_rows}
    foundation_by_page = {as_int(row.get("来源页码")): row for row in foundation_rows}
    page_stats = defaultdict(lambda: {
        "专业明细行数": 0,
        "高风险保真行数": 0,
        "低风险行数": 0,
        "F0行数": 0,
        "F1行数": 0,
        "F2行数": 0,
        "F3行数": 0,
        "P0行数": 0,
        "P1行数": 0,
        "P2行数": 0,
        "P3行数": 0,
        "P4行数": 0,
        "P5行数": 0,
        "P6行数": 0,
        "空专业名行数": 0,
        "高严重结构异常专业行数": 0,
        "结构异常专业行数": 0,
        "计划数字段风险行数": 0,
        "学费字段风险行数": 0,
        "再选科目字段风险行数": 0,
        "家庭底线风险行数": 0,
        "偏好专业行数": 0,
        "候选池V1专业明细数": 0,
        "样本学校专业明细数": 0,
        "风险规则计数": Counter(),
        "风险字段计数": Counter(),
        "涉及院校代码": set(),
        "涉及专业组代码": set(),
    })

    for row in fidelity_rows:
        page = as_int(row.get("来源页码"))
        stats = page_stats[page]
        stats["专业明细行数"] += 1
        stats["高风险保真行数"] += row.get("是否高风险保真行") == "true"
        stats["低风险行数"] += row.get("是否高风险保真行") == "false"
        block = row.get("风险阻断等级", "")
        if block.startswith("F0"):
            stats["F0行数"] += 1
        elif block.startswith("F1"):
            stats["F1行数"] += 1
        elif block.startswith("F2"):
            stats["F2行数"] += 1
        elif block.startswith("F3"):
            stats["F3行数"] += 1
        priority = row.get("全量保真复核优先级", "")
        for key in ["P0", "P1", "P2", "P3", "P4", "P5", "P6"]:
            if priority.startswith(key):
                stats[f"{key}行数"] += 1
                break
        categories = set(split_flags(row.get("高风险字段集合")))
        rules = split_flags(row.get("风险触发规则"))
        stats["风险规则计数"].update(rules)
        stats["风险字段计数"].update(categories)
        stats["空专业名行数"] += "empty_major_name" in rules
        stats["高严重结构异常专业行数"] += (as_int(row.get("专业行高严重结构异常数")) > 0)
        stats["结构异常专业行数"] += (as_int(row.get("专业行结构异常数")) > 0)
        stats["计划数字段风险行数"] += "计划数字段" in categories
        stats["学费字段风险行数"] += "学费字段" in categories
        stats["再选科目字段风险行数"] += "再选科目字段" in categories
        stats["家庭底线风险行数"] += "家庭底线" in categories
        stats["偏好专业行数"] += "偏好专业" in categories
        stats["候选池V1专业明细数"] += row.get("候选池V1命中") == "是"
        stats["样本学校专业明细数"] += row.get("样本学校命中") == "是"
        if row.get("院校代码"):
            stats["涉及院校代码"].add(row.get("院校代码"))
        if row.get("院校专业组代码OCR规范化"):
            stats["涉及专业组代码"].add(row.get("院校专业组代码OCR规范化"))

    output_rows = []
    for page in range(10, 241):
        manifest = manifest_by_page.get(page, {})
        foundation = foundation_by_page.get(page, {})
        stats = page_stats[page]
        priority = page_priority(stats, manifest)
        block_level = (
            "F0-本页存在阻断级专业行"
            if stats["F0行数"] > 0
            else "F1-本页存在高优先字段风险"
            if stats["F1行数"] > 0
            else "F2-本页待补证或抽检"
            if stats["F2行数"] > 0
            else "F3-本页暂未触发机器高风险但仍非最终"
        )
        output_rows.append({
            "页级保真队列ID": stable_id("PAGEFID", [manifest.get("来源PDF_SHA256", ""), page]),
            "来源页级manifest": "data/working/issue19-page-manifest.csv",
            "来源底座按页审计": "data/working/issue19-foundation-page-audit.csv",
            "来源全量逐专业保真总账": "data/working/issue19-full-major-field-fidelity-ledger.csv",
            "来源期号": manifest.get("来源期号", foundation.get("来源期号", "")),
            "来源PDF_SHA256": manifest.get("来源PDF_SHA256", foundation.get("来源PDF_SHA256", "")),
            "数据阶段": DATA_STAGE,
            "最终可用": "false",
            "核验状态": "pending_page_fidelity_review",
            "PDF页码": str(page),
            "页码范围角色": manifest.get("页码范围角色", ""),
            "私有页图证据编号": manifest.get("私有页图证据编号", ""),
            "私有页图SHA256": manifest.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": manifest.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": manifest.get("私有OCR文本SHA256", ""),
            "OCR识别行数": manifest.get("OCR识别行数", ""),
            "OCR平均置信度": manifest.get("OCR平均置信度", ""),
            "OCR_QC_P0数": manifest.get("OCR_QC_P0数", ""),
            "OCR_QC_P1数": manifest.get("OCR_QC_P1数", ""),
            "疑似招生计划行数": manifest.get("疑似招生计划行数", ""),
            "页面复核优先级": priority,
            "页面阻断等级": block_level,
            "页面审计状态": foundation.get("页面审计状态", ""),
            "页面专业组数": foundation.get("页面专业组数", manifest.get("结构化专业组数", "")),
            "页面专业明细数": str(stats["专业明细行数"]),
            "页面院校数": foundation.get("页面院校数", manifest.get("结构化院校数", "")),
            "页面结构异常数": foundation.get("页面结构异常数", manifest.get("结构异常数", "")),
            "页面高严重结构异常数": foundation.get("页面高严重结构异常数", manifest.get("高严重结构异常数", "")),
            "高风险保真行数": str(stats["高风险保真行数"]),
            "低风险行数": str(stats["低风险行数"]),
            "F0阻断行数": str(stats["F0行数"]),
            "F1高优先行数": str(stats["F1行数"]),
            "F2待补证行数": str(stats["F2行数"]),
            "F3低风险非最终行数": str(stats["F3行数"]),
            "P0结构串行行数": str(stats["P0行数"]),
            "P1计划数保真行数": str(stats["P1行数"]),
            "P2家庭费用行数": str(stats["P2行数"]),
            "P3选科限制行数": str(stats["P3行数"]),
            "P4调剂风险行数": str(stats["P4行数"]),
            "P5偏好或普通待核行数": str(stats["P5行数"]),
            "P6暂未触发机器高风险行数": str(stats["P6行数"]),
            "空专业名行数": str(stats["空专业名行数"]),
            "高严重结构异常专业行数": str(stats["高严重结构异常专业行数"]),
            "结构异常专业行数": str(stats["结构异常专业行数"]),
            "计划数字段风险行数": str(stats["计划数字段风险行数"]),
            "学费字段风险行数": str(stats["学费字段风险行数"]),
            "再选科目字段风险行数": str(stats["再选科目字段风险行数"]),
            "家庭底线风险行数": str(stats["家庭底线风险行数"]),
            "偏好专业行数": str(stats["偏好专业行数"]),
            "候选池V1专业明细数": str(stats["候选池V1专业明细数"]),
            "样本学校专业明细数": str(stats["样本学校专业明细数"]),
            "涉及院校数": str(len(stats["涉及院校代码"])),
            "涉及专业组数": str(len(stats["涉及专业组代码"])),
            "风险字段Top": join_top(stats["风险字段计数"]),
            "风险规则Top": join_top(stats["风险规则计数"]),
            "必须核验字段": "PDF原页；页内专业组边界；院校代码；专业组代码；专业代号；专业名称及备注；计划数；学费；再选科目；校区/特殊限制；湖北官方系统；高校官网/章程",
            "是否可进入最终页级结论": "false",
            "可进入下一阶段": "false",
            "下一步": "按页回看第19期原PDF，对照全量逐专业保真总账逐行核专业组边界、专业字段、计划数、学费、选科和备注；再接湖北官方系统和高校官网/章程。",
        })

    priority_counts = Counter(row["页面复核优先级"] for row in output_rows)
    block_counts = Counter(row["页面阻断等级"] for row in output_rows)
    summary = {
        "status": "issue19_page_fidelity_review_queue_not_final",
        "generated_by": Path(__file__).name,
        "source_page_manifest": "data/working/issue19-page-manifest.csv",
        "source_foundation_page_audit": "data/working/issue19-foundation-page-audit.csv",
        "source_full_major_fidelity_ledger": "data/working/issue19-full-major-field-fidelity-ledger.csv",
        "output_table": "data/working/issue19-page-fidelity-review-queue.csv",
        "page_range": [10, 240],
        "page_count": len(output_rows),
        "total_major_detail_count": sum(as_int(row["页面专业明细数"]) for row in output_rows),
        "total_group_count": sum(as_int(row["页面专业组数"]) for row in output_rows),
        "total_high_risk_fidelity_rows": sum(as_int(row["高风险保真行数"]) for row in output_rows),
        "total_low_risk_rows": sum(as_int(row["低风险行数"]) for row in output_rows),
        "total_f0_rows": sum(as_int(row["F0阻断行数"]) for row in output_rows),
        "total_f1_rows": sum(as_int(row["F1高优先行数"]) for row in output_rows),
        "total_f2_rows": sum(as_int(row["F2待补证行数"]) for row in output_rows),
        "total_f3_rows": sum(as_int(row["F3低风险非最终行数"]) for row in output_rows),
        "total_p0_rows": sum(as_int(row["P0结构串行行数"]) for row in output_rows),
        "total_p1_rows": sum(as_int(row["P1计划数保真行数"]) for row in output_rows),
        "total_p2_rows": sum(as_int(row["P2家庭费用行数"]) for row in output_rows),
        "total_p3_rows": sum(as_int(row["P3选科限制行数"]) for row in output_rows),
        "total_p4_rows": sum(as_int(row["P4调剂风险行数"]) for row in output_rows),
        "total_p5_rows": sum(as_int(row["P5偏好或普通待核行数"]) for row in output_rows),
        "total_p6_rows": sum(as_int(row["P6暂未触发机器高风险行数"]) for row in output_rows),
        "total_empty_major_name_rows": sum(as_int(row["空专业名行数"]) for row in output_rows),
        "total_high_structure_anomaly_major_rows": sum(as_int(row["高严重结构异常专业行数"]) for row in output_rows),
        "total_plan_count_risk_rows": sum(as_int(row["计划数字段风险行数"]) for row in output_rows),
        "total_tuition_risk_rows": sum(as_int(row["学费字段风险行数"]) for row in output_rows),
        "total_preference_major_rows": sum(as_int(row["偏好专业行数"]) for row in output_rows),
        "total_family_bottom_line_rows": sum(as_int(row["家庭底线风险行数"]) for row in output_rows),
        "priority_counts": dict(sorted(priority_counts.items())),
        "block_level_counts": dict(sorted(block_counts.items())),
        "auto_final_page_allowed_count": sum(row["是否可进入最终页级结论"] == "true" for row in output_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "notes": [
            "本表是第19期按页保真复核队列，只安排人工核页顺序，不产生最终志愿结论。",
            "第1-9页为前置说明页，不进入招生计划明细核页队列；仍在page manifest中留存。",
            "所有页均需回看PDF原页，并最终接湖北官方系统和高校官网/章程闭环。",
        ],
    }
    write_csv(OUTPUT, output_rows, list(output_rows[0].keys()))
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
