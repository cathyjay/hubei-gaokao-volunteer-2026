#!/usr/bin/env python3
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import input_snapshot


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
CANDIDATE_GROUP_PAGE_MAP = ROOT / "data/working/issue19-candidate-review-group-page-map.csv"
FULL_GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
PAGE_PACKET_TEXT_DIR = ROOT / "private/derived/issue19-candidate-review-page-packet/text"

CANDIDATE_CODE_AUDIT_OUTPUT = ROOT / "data/working/issue19-candidate-page-code-audit.csv"
STRUCTURE_ANOMALY_OUTPUT = ROOT / "data/working/issue19-ocr-structure-anomaly-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-integrity-audit-summary.json"

SCHOOL_CODE_IN_MAJOR_RE = re.compile(
    r"([A-Z][0-9OIl]{3})\s*([\u4e00-\u9fff]{1,30}(?:大学|学院|学校|职业|师范|医学院|中医|理工|科技|工程))"
)
GROUP_CODE_IN_MAJOR_RE = re.compile(r"[A-Z][0-9OIl]{3}[0-9OIl]{2}")
PAGE_HEADER_TOKENS = [
    "院校专业组及专业代号",
    "院校及专业代号",
    "高院校及专业代号",
    "資高院校",
    "招生计划",
    "人数 学费",
    "人数 学",
]

CANDIDATE_RULE_IDS = {
    "页面有组号但结构化未拆出": "candidate_group_page_hit_structured_miss",
    "复核页未见候选组号且结构化未命中": "candidate_group_missing_in_page_and_structured",
    "结构化命中但页面OCR未检出组号": "structured_hit_page_text_miss",
    "页面与结构化均命中": "page_and_structured_match",
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_pages(value):
    pages = []
    for part in str(value or "").replace("；", ";").split(";"):
        part = part.strip()
        if part.isdigit():
            pages.append(int(part))
    return pages


def read_page_lines(page):
    text_path = PAGE_PACKET_TEXT_DIR / f"{page:03d}_page-{page:03d}.txt"
    if not text_path.exists():
        return []
    return text_path.read_text(encoding="utf-8", errors="ignore").splitlines()


def find_group_code_on_pages(group_code, pages):
    hit_pages = []
    evidence = []
    for page in pages:
        for line_number, line in enumerate(read_page_lines(page), start=1):
            if group_code in line:
                hit_pages.append(page)
                evidence.append(f"第{page}页第{line_number}行含{group_code}")
                break
    return hit_pages, evidence


def candidate_anomaly_type(page_hit, full_hit):
    if page_hit and not full_hit:
        return "页面有组号但结构化未拆出"
    if not page_hit and not full_hit:
        return "复核页未见候选组号且结构化未命中"
    if not page_hit and full_hit:
        return "结构化命中但页面OCR未检出组号"
    return "页面与结构化均命中"


def candidate_severity(anomaly_type):
    if anomaly_type == "页面有组号但结构化未拆出":
        return "高"
    if anomaly_type == "复核页未见候选组号且结构化未命中":
        return "中"
    if anomaly_type == "结构化命中但页面OCR未检出组号":
        return "中"
    return "低"


def number_or_none(value):
    value = str(value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def build_candidate_code_audit(source_issue, source_pdf_sha256, candidate_rows, groups_by_code, majors_by_group):
    rows = []
    for row in candidate_rows:
        group_code = row["候选专业组代码"]
        pages = parse_pages(row.get("候选复核页码", ""))
        hit_pages, evidence = find_group_code_on_pages(group_code, pages)
        full_hit = group_code in groups_by_code
        anomaly = candidate_anomaly_type(bool(hit_pages), full_hit)
        rows.append({
            "来源期号": row.get("来源期号") or source_issue,
            "来源PDF_SHA256": row.get("来源PDF_SHA256") or source_pdf_sha256,
            "数据阶段": "issue19_candidate_page_code_audit",
            "最终可用": "false",
            "候选池学校专业组": row["候选池学校专业组"],
            "候选专业组代码": group_code,
            "第19期全量OCR命中": row["第19期全量OCR命中"],
            "全量专业组表是否出现": "是" if full_hit else "否",
            "全量专业行数": str(len(majors_by_group.get(group_code, []))),
            "候选复核页码": row.get("候选复核页码", ""),
            "页面OCR是否出现候选组号": "是" if hit_pages else "否",
            "页面OCR命中页码": "；".join(str(page) for page in hit_pages),
            "页面OCR证据": "；".join(evidence),
            "同校第19期OCR专业组": row.get("同校第19期OCR专业组", ""),
            "同校第19期OCR页码": row.get("同校第19期OCR页码", ""),
            "异常规则ID": CANDIDATE_RULE_IDS[anomaly],
            "异常类型": anomaly,
            "严重程度": candidate_severity(anomaly),
            "核验状态": "needs_manual_pdf_review",
            "下一步": "回看候选页图，逐字段确认该组是否存在、是否被自动切组漏拆、是否为历史组号变化",
        })
    return rows


def structure_anomalies_for_major(row):
    name = row.get("专业名称及备注OCR", "")
    anomalies = []

    school_hits = SCHOOL_CODE_IN_MAJOR_RE.findall(name)
    if school_hits:
        evidence = "；".join(f"{code}{school}" for code, school in school_hits[:3])
        anomalies.append(("major_text_embeds_other_school_marker", "专业名称疑似串入下一院校", "高", evidence))

    group_hits = GROUP_CODE_IN_MAJOR_RE.findall(name)
    if group_hits:
        anomalies.append(("major_text_embeds_group_code", "专业名称疑似串入专业组代码", "高", "；".join(group_hits[:3])))

    header_hits = [token for token in PAGE_HEADER_TOKENS if token in name]
    if header_hits:
        anomalies.append(("major_text_embeds_page_header", "专业名称疑似串入页眉或栏目文字", "中", "；".join(header_hits)))

    major_code = row.get("专业代号OCR", "")
    if major_code and not re.fullmatch(r"[0-9A-Z]{2}", major_code):
        anomalies.append(("major_code_not_two_chars", "专业代号疑似漏位或误识别", "中", major_code))

    flags = set(filter(None, row.get("字段完整性标记", "").split(";")))
    plan_number = number_or_none(row.get("专业计划数OCR数字候选"))
    tuition_number = number_or_none(row.get("学费OCR数字候选"))
    if plan_number is not None and plan_number >= 1000:
        anomalies.append((
            "plan_count_number_ge_1000",
            "专业计划数疑似吞入学费或备注",
            "高",
            row.get("专业计划数OCR候选", ""),
        ))
    if tuition_number is not None and 0 < tuition_number <= 500:
        anomalies.append((
            "tuition_number_le_500",
            "学费数字疑似吞入计划数或截断",
            "高",
            row.get("学费OCR候选", ""),
        ))
    if row.get("专业计划数是否纯数字") == "否" and row.get("专业计划数OCR候选"):
        anomalies.append((
            "plan_count_not_plain_number",
            "专业计划数字段非纯数字",
            "高",
            row.get("专业计划数OCR候选", ""),
        ))
    if row.get("学费是否纯数字") == "否" and row.get("学费OCR候选"):
        anomalies.append((
            "tuition_not_plain_number",
            "学费字段非纯数字",
            "高",
            row.get("学费OCR候选", ""),
        ))
    if "low_ocr_confidence" in flags:
        anomalies.append(("low_ocr_confidence", "OCR置信度低", "中", "low_ocr_confidence"))

    return anomalies


def build_structure_anomaly_queue(source_issue, source_pdf_sha256, major_rows):
    rows = []
    for row in major_rows:
        for rule_id, anomaly_type, severity, evidence in structure_anomalies_for_major(row):
            rows.append({
                "来源期号": row.get("来源期号") or source_issue,
                "来源PDF_SHA256": row.get("来源PDF_SHA256") or source_pdf_sha256,
                "数据阶段": "issue19_ocr_structure_anomaly_queue",
                "最终可用": "false",
                "源文件": str(FULL_MAJORS.relative_to(ROOT)),
                "院校代码": row.get("院校代码", ""),
                "院校名称OCR": row.get("院校名称OCR", ""),
                "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
                "专业组号OCR": row.get("专业组号OCR", ""),
                "专业组标题OCR原文": row.get("专业组标题OCR原文", ""),
                "版面列": row.get("版面列", ""),
                "专业代号OCR": row.get("专业代号OCR", ""),
                "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
                "来源页码": row.get("来源页码", ""),
                "再选科目OCR候选": row.get("再选科目OCR候选", ""),
                "专业计划数OCR候选": row.get("专业计划数OCR候选", ""),
                "专业计划数OCR数字候选": row.get("专业计划数OCR数字候选", ""),
                "学费OCR候选": row.get("学费OCR候选", ""),
                "学费OCR数字候选": row.get("学费OCR数字候选", ""),
                "字段完整性标记": row.get("字段完整性标记", ""),
                "异常规则ID": rule_id,
                "异常类型": anomaly_type,
                "严重程度": severity,
                "异常证据": evidence,
                "核验状态": "needs_manual_pdf_review",
                "下一步": "回看原PDF页和相邻页，确认该专业行边界、专业组边界、计划数、学费和备注是否串行",
            })
    rows.sort(key=lambda item: (item["严重程度"] != "高", item["来源页码"], item["院校专业组代码OCR规范化"], item["专业代号OCR"]))
    return rows


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]

    candidate_rows = read_csv(CANDIDATE_GROUP_PAGE_MAP)
    group_rows = read_csv(FULL_GROUPS)
    major_rows = read_csv(FULL_MAJORS)

    groups_by_code = {row["院校专业组代码OCR规范化"]: row for row in group_rows}
    majors_by_group = defaultdict(list)
    for row in major_rows:
        majors_by_group[row["院校专业组代码OCR规范化"]].append(row)

    candidate_code_rows = build_candidate_code_audit(
        source_issue,
        source_pdf_sha256,
        candidate_rows,
        groups_by_code,
        majors_by_group,
    )
    structure_anomaly_rows = build_structure_anomaly_queue(source_issue, source_pdf_sha256, major_rows)

    candidate_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "候选池学校专业组",
        "候选专业组代码",
        "第19期全量OCR命中",
        "全量专业组表是否出现",
        "全量专业行数",
        "候选复核页码",
        "页面OCR是否出现候选组号",
        "页面OCR命中页码",
        "页面OCR证据",
        "同校第19期OCR专业组",
        "同校第19期OCR页码",
        "异常规则ID",
        "异常类型",
        "严重程度",
        "核验状态",
        "下一步",
    ]
    structure_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "源文件",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组标题OCR原文",
        "版面列",
        "专业代号OCR",
        "专业名称及备注OCR",
        "来源页码",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "专业计划数OCR数字候选",
        "学费OCR候选",
        "学费OCR数字候选",
        "字段完整性标记",
        "异常规则ID",
        "异常类型",
        "严重程度",
        "异常证据",
        "核验状态",
        "下一步",
    ]
    write_csv(CANDIDATE_CODE_AUDIT_OUTPUT, candidate_code_rows, candidate_fields)
    write_csv(STRUCTURE_ANOMALY_OUTPUT, structure_anomaly_rows, structure_fields)

    candidate_counter = Counter(row["异常类型"] for row in candidate_code_rows)
    candidate_rule_counter = Counter(row["异常规则ID"] for row in candidate_code_rows)
    structure_counter = Counter(row["异常类型"] for row in structure_anomaly_rows)
    structure_rule_counter = Counter(row["异常规则ID"] for row in structure_anomaly_rows)
    severity_counter = Counter(row["严重程度"] for row in structure_anomaly_rows)
    summary = {
        "status": "issue19_integrity_audit_queues_need_manual_pdf_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "issue19_integrity_audit",
        "generated_by": "scripts/build_issue19_integrity_audit_queues.py",
        "inputs": input_snapshot(ROOT, [ISSUE19_SOURCE, CANDIDATE_GROUP_PAGE_MAP, FULL_GROUPS, FULL_MAJORS]),
        "candidate_page_code_audit_count": len(candidate_code_rows),
        "candidate_page_code_anomaly_counts": dict(candidate_counter),
        "candidate_page_code_rule_counts": dict(candidate_rule_counter),
        "structure_anomaly_count": len(structure_anomaly_rows),
        "structure_anomaly_type_counts": dict(structure_counter),
        "structure_anomaly_rule_counts": dict(structure_rule_counter),
        "structure_anomaly_severity_counts": dict(severity_counter),
        "outputs": [
            str(CANDIDATE_CODE_AUDIT_OUTPUT.relative_to(ROOT)),
            str(STRUCTURE_ANOMALY_OUTPUT.relative_to(ROOT)),
        ],
        "notes": [
            "候选页码审计用于发现页面OCR命中与结构化切组结果不一致的问题。",
            "结构异常队列用于发现专业明细层面的串校、串组、页眉串入、专业代号异常、计划数/学费错位和低置信度。",
            "所有输出仍为复核队列，不能作为最终填报依据。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出候选页码组号审计：{CANDIDATE_CODE_AUDIT_OUTPUT}")
    print(f"写出全量结构异常队列：{STRUCTURE_ANOMALY_OUTPUT}")
    print(f"写出完整性审计摘要：{SUMMARY_OUTPUT}")
    print(f"候选审计行数：{len(candidate_code_rows)}")
    print(f"结构异常行数：{len(structure_anomaly_rows)}")


if __name__ == "__main__":
    main()
