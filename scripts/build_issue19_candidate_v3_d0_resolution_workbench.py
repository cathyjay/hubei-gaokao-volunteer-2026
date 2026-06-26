#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from issue19_review_rules import input_snapshot


ROOT = Path(__file__).resolve().parents[1]
D0_QUEUE = ROOT / "data/working/issue19-candidate-v3-admission-detail-review-queue.csv"
GROUP_DRAFT = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
CANDIDATE_PAGE_AUDIT = ROOT / "data/working/issue19-candidate-page-code-audit.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
HISTORY_FILES = [
    ("2023", ROOT / "data/derived/hubei-2023-physics-toudang-parsed.csv"),
    ("2024", ROOT / "data/derived/hubei-2024-physics-toudang-parsed.csv"),
    ("2025", ROOT / "data/derived/hubei-2025-physics-toudang-parsed.csv"),
]
OUTPUT = ROOT / "data/working/issue19-candidate-v3-d0-resolution-workbench.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v3-d0-resolution-workbench-summary.json"

DATA_STAGE = "issue19_candidate_v3_d0_resolution_workbench"
D0_PRIORITY = "D0-0明细或边界问题先补齐"
SUSPICIOUS_SCHOOL_NAMES = {
    "北京",
    "上海",
    "天津",
    "重庆",
    "河北",
    "山西",
    "辽宁",
    "吉林",
    "黑龙江",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "海南",
    "四川",
    "贵州",
    "云南",
    "陕西",
    "甘肃",
    "青海",
    "台湾",
    "内蒙古",
    "广西",
    "西藏",
    "宁夏",
    "新疆",
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def page_key(value):
    return str(value or "").strip().zfill(3)


def extract_school_name_from_group_title(title):
    title = str(title or "")
    match = re.search(r"([\u4e00-\u9fa5]{2,}(?:大学|学院|学校))", title)
    return match.group(1) if match else ""


def is_suspicious_school_name(name):
    name = str(name or "").strip()
    return name in SUSPICIOUS_SCHOOL_NAMES or (
        name and len(name) <= 2 and "大学" not in name and "学院" not in name
    )


def classify_issue(row):
    issues = []
    if row.get("是否0明细占位") == "true":
        issues.append("0明细占位")
    if is_suspicious_school_name(row.get("院校名称OCR")):
        issues.append("院校名称OCR疑似截断")
    if "同页边界风险" in row.get("复核批次", "") or "边界" in row.get("复核原因", ""):
        issues.append("专业组边界或明细缺失")
    if not issues:
        issues.append("D0其他待核")
    return "；".join(issues)


def suggestion_status(row, extracted_name, audit):
    if row.get("是否0明细占位") == "true":
        return "未在全量结构化专业组表/页面OCR命中-需核2026组号是否变化或取消"
    if extracted_name and extracted_name != row.get("院校名称OCR", ""):
        return "可从专业组标题OCR提取完整院校名-仍需PDF原页和官方系统核验"
    if extracted_name:
        return "专业组标题可辅助确认院校名-仍需核专业组边界"
    if audit:
        return "候选页码审计提供同校组号线索-需回看原页"
    return "缺少可直接提取的完整院校名线索-需回看原页和官方系统"


def build_history_evidence():
    evidence = {}
    for year, path in HISTORY_FILES:
        for row in read_csv(path):
            code = row.get("code", "")
            if not code:
                continue
            school_code = code[:4]
            evidence.setdefault(school_code, []).append({
                "year": year,
                "code": code,
                "name": row.get("name", ""),
                "req": row.get("req", ""),
                "score": row.get("score", ""),
            })
    return evidence


def history_summary(records, expected_name=""):
    if not records:
        return "", "", ""
    years = sorted({record["year"] for record in records})
    names = []
    for record in records:
        if expected_name and expected_name in record["name"]:
            name = expected_name
        else:
            name = extract_school_name_from_group_title(record["name"])
        if name and name not in names:
            names.append(name)
    samples = []
    for record in records[:6]:
        samples.append(f"{record['year']} {record['code']} {record['name']} {record['req']} {record['score']}")
    return "；".join(years), "；".join(names), "；".join(samples)


def conflict_flag(row, extracted_name, history_years):
    code = row.get("院校代码", "")
    group_code = row.get("2026院校专业组代码", "")
    title = row.get("专业组标题OCR原文", "")
    flags = []
    if code == "P012":
        flags.append("历史投档线未命中P012且同页疑似F012/PO1202字符混淆")
    if group_code.startswith("P012"):
        flags.append("专业组代码疑似P/F/O/0混淆-禁止自动修正")
    if "FO" in title or "PO" in title or "O" in group_code:
        flags.append("OCR含F/O/P/0易混字符")
    if extracted_name and not history_years and code not in {"P012"}:
        flags.append("无历史投档线代码校名佐证")
    return "；".join(flags)


def needs_history(row):
    return "是" if is_suspicious_school_name(row.get("院校名称OCR")) else "否"


def next_step(row, extracted_name, audit):
    if row.get("是否0明细占位") == "true":
        return "先回看私有页图和湖北官方系统，确认该候选组号是否存在；若不存在，标记为历史组号变化或取消，不得进入最终候选。"
    if extracted_name and extracted_name != row.get("院校名称OCR", ""):
        return "先核 PDF 原页学校标题和专业组标题，再用湖北官方系统确认院校代码、完整院校名和专业组边界。"
    if "同页边界风险" in row.get("复核批次", ""):
        return "先回看同页上下文，确认该专业行是否串入下一院校或相邻专业组。"
    return "按 D0 任务回看原页，补齐院校名、专业组边界和字段证据。"


def main():
    queue_rows = [row for row in read_csv(D0_QUEUE) if row.get("核验优先级") == D0_PRIORITY]
    group_rows = read_csv(GROUP_DRAFT)
    audit_rows = read_csv(CANDIDATE_PAGE_AUDIT)
    page_rows = read_csv(PAGE_MANIFEST)
    history_evidence = build_history_evidence()

    group_by_code = {}
    for row in group_rows:
        code = row.get("院校专业组代码OCR规范化", "")
        if code and code not in group_by_code:
            group_by_code[code] = row

    audit_by_code = {row.get("候选专业组代码", ""): row for row in audit_rows}
    page_by_number = {str(int(row.get("PDF页码", "0"))): row for row in page_rows if row.get("PDF页码", "").isdigit()}

    output_rows = []
    for row in queue_rows:
        code = row.get("2026院校专业组代码", "")
        group = group_by_code.get(code, {})
        audit = audit_by_code.get(code, {})
        page = page_by_number.get(str(row.get("来源页码", "")).split("；", 1)[0], {})
        title = group.get("专业组标题OCR原文", "")
        extracted_name = extract_school_name_from_group_title(title)
        history_years, history_names, history_samples = history_summary(
            history_evidence.get(row.get("院校代码", ""), []),
            extracted_name,
        )
        conflict = conflict_flag({**row, "专业组标题OCR原文": title}, extracted_name, history_years)
        evidence_level = (
            "G1-专业组标题可提取完整院校名-仍需原页确认"
            if extracted_name
            else "G0-无完整院校名提取线索-需原页/官方系统确认"
        )
        output_rows.append({
            "D0工作台ID": stable_id("D0", [row.get("逐专业复核队列ID", ""), row.get("招生明细主表行ID", "")]),
            "来源逐专业复核队列ID": row.get("逐专业复核队列ID", ""),
            "招生明细主表行ID": row.get("招生明细主表行ID", ""),
            "来源期号": row.get("来源期号", ""),
            "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "最终可用": "false",
            "D0问题类型": classify_issue(row),
            "核验结论状态": "pending_d0_manual_review",
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "建议完整院校名称": extracted_name,
            "建议来源": "专业组标题OCR原文" if extracted_name else "",
            "建议证据强度": evidence_level,
            "同代码专业组标题建议名称一致性": "待核-同代码多组一致" if extracted_name else "无标题建议",
            "历年投档线命中年份": history_years,
            "历年投档线院校名线索": history_names,
            "历年投档线样例": history_samples,
            "是否需要历年代码校名佐证": needs_history(row),
            "代码冲突标记": conflict,
            "疑似字符混淆": "是" if conflict else "否",
            "修正建议状态": suggestion_status(row, extracted_name, audit),
            "2026院校专业组代码": code,
            "专业组标题OCR原文": title,
            "来源页码": row.get("来源页码", ""),
            "版面列": group.get("版面列", ""),
            "私有页图证据编号": row.get("私有页图证据编号", ""),
            "私有页图SHA256": row.get("私有页图SHA256", "") or page.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": page.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": page.get("私有OCR文本SHA256", ""),
            "页面OCR是否出现候选组号": audit.get("页面OCR是否出现候选组号", ""),
            "页面OCR命中页码": audit.get("页面OCR命中页码", ""),
            "同校第19期OCR专业组": audit.get("同校第19期OCR专业组", ""),
            "同校第19期OCR页码": audit.get("同校第19期OCR页码", ""),
            "页面组号异常类型": audit.get("异常类型", ""),
            "页面组号异常规则ID": audit.get("异常规则ID", ""),
            "专业行来源": row.get("专业行来源", ""),
            "是否真实招生明细": row.get("是否真实招生明细", ""),
            "是否0明细占位": row.get("是否0明细占位", ""),
            "专业代号OCR": row.get("专业代号OCR", ""),
            "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
            "专业计划数OCR候选": row.get("专业计划数OCR候选", ""),
            "学费OCR候选": row.get("学费OCR候选", ""),
            "专业字段完整性标记": row.get("专业字段完整性标记", ""),
            "同组调剂机器风险": row.get("同组调剂机器风险", ""),
            "是否可自动写回主表": "false",
            "可进入下一阶段": "false",
            "下一步": next_step(row, extracted_name, audit),
        })

    fields = list(output_rows[0].keys())
    write_csv(OUTPUT, output_rows, fields)

    issue_counts = Counter()
    for row in output_rows:
        for item in row["D0问题类型"].split("；"):
            issue_counts[item] += 1

    summary = {
        "status": "issue19_candidate_v3_d0_resolution_workbench_not_final",
        "generated_by": Path(__file__).name,
        "source_queue": str(D0_QUEUE.relative_to(ROOT)),
        "output_table": str(OUTPUT.relative_to(ROOT)),
        "row_count": len(output_rows),
        "unique_group_count": len({row["2026院校专业组代码"] for row in output_rows}),
        "issue_counts": dict(issue_counts),
        "school_ocr_counts": dict(Counter(row["院校名称OCR"] for row in output_rows)),
        "extracted_full_school_name_count": sum(bool(row["建议完整院校名称"]) for row in output_rows),
        "name_correction_needed_count": sum(
            bool(row["建议完整院校名称"]) and row["建议完整院校名称"] != row["院校名称OCR"]
            for row in output_rows
        ),
        "zero_detail_placeholder_count": sum(row["是否0明细占位"] == "true" for row in output_rows),
        "history_supported_name_count": sum(bool(row["历年投档线院校名线索"]) for row in output_rows),
        "code_conflict_count": sum(bool(row["代码冲突标记"]) for row in output_rows),
        "auto_writeback_allowed_count": sum(row["是否可自动写回主表"] == "true" for row in output_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "fidelity_note": "该表只为 D0 原页核验和修正建议排序；建议完整院校名称来自OCR标题线索，不能替代PDF原页、湖北官方系统和高校官网/章程核验。",
        "inputs": input_snapshot(ROOT, [D0_QUEUE, GROUP_DRAFT, CANDIDATE_PAGE_AUDIT, PAGE_MANIFEST] + [path for _, path in HISTORY_FILES]),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
