#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
D0_WORKBENCH = ROOT / "data/working/issue19-candidate-v3-d0-resolution-workbench.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
FULL_GROUP_DRAFT = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_MAJOR_DRAFT = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
STRUCTURE_ANOMALY_QUEUE = ROOT / "data/working/issue19-ocr-structure-anomaly-queue.csv"
PRIVATE_OCR_LINES = ROOT / "private/ocr-runs/issue19-full-120dpi/ocr-lines.csv"

OUTPUT = ROOT / "data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v3-d0-pdf-page-evidence-summary.json"

DATA_STAGE = "issue19_candidate_v3_d0_pdf_page_evidence"


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def split_values(value):
    return [part.strip() for part in re.split(r"[；;]", value or "") if part.strip()]


def first_nonempty(rows, field):
    for row in rows:
        if row.get(field):
            return row[field]
    return ""


def unique_join(values):
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return "；".join(seen)


def code_variants(code):
    variants = {code}
    zero_positions = [index for index, char in enumerate(code) if char == "0"]
    for index in zero_positions:
        variants.add(code[:index] + "O" + code[index + 1:])
        variants.add(code[:index] + "o" + code[index + 1:])
    variants.add("".join("O" if char == "0" else char for char in code))
    variants.add("".join("o" if char == "0" else char for char in code))
    if code.startswith("P"):
        variants.add("F" + code[1:])
        variants.add(("F" + code[1:]).replace("0", "O"))
    if code.startswith("F"):
        variants.add("P" + code[1:])
        variants.add(("P" + code[1:]).replace("0", "O"))
    return sorted(variants, key=lambda item: (item != code, item))


def normalized_group_suffix(code):
    return code[-2:].replace("O", "0").replace("o", "0")


def extract_group_no(text):
    match = re.search(r"第\s*([0-9Oo]{1,2})\s*组", text or "")
    if not match:
        return ""
    return match.group(1).replace("O", "0").replace("o", "0").zfill(2)


def line_hash(row):
    return sha256_text(
        "|".join([
            row.get("page", ""),
            row.get("line_no", ""),
            row.get("text", ""),
            row.get("confidence", ""),
            row.get("x", ""),
            row.get("y", ""),
            row.get("width", ""),
            row.get("height", ""),
        ])
    )


def page_manifest_values(page_manifest_by_page, pages, field):
    values = []
    for page in pages:
        row = page_manifest_by_page.get(page, {})
        if row.get(field):
            values.append(row[field])
    return unique_join(values)


def page_sort_key(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 9999


def best_hit(code, rows, ocr_lines):
    variants = code_variants(code)
    source_pages = {
        page for row in rows for page in split_values(row.get("来源页码", ""))
    }
    hits = []
    for line in ocr_lines:
        text = line.get("text", "")
        matched_variant = next((variant for variant in variants if variant in text), "")
        if not matched_variant:
            continue
        page = line.get("page", "")
        score = 0
        if page in source_pages:
            score += 100
        if matched_variant == code:
            score += 20
        if "第" in text and "组" in text:
            score += 10
        score += int(float(line.get("confidence") or 0) * 10)
        hits.append((score, matched_variant, line))
    if not hits:
        return "", {}
    hits.sort(key=lambda item: (-item[0], page_sort_key(item[2].get("page")), int(item[2].get("line_no") or 0)))
    return hits[0][1], hits[0][2]


def title_relation(code, matched_variant):
    if not matched_variant:
        return "未命中候选组号"
    if matched_variant == code:
        return "精确命中"
    return "字符混淆命中-禁止自动写回"


def page_match_method(code, matched_variant, structured_group_exists):
    if not matched_variant and not structured_group_exists:
        return "missing_in_page_and_structured"
    if not matched_variant:
        return "missing_in_page_ocr"
    if matched_variant == code:
        return "exact_match"
    return "normalized_o0_match"


def hit_status(rows, matched_variant):
    is_zero = any(row.get("是否0明细占位") == "true" for row in rows)
    has_conflict = any(row.get("疑似字符混淆") == "是" for row in rows)
    if not matched_variant:
        if is_zero:
            return "未命中候选组号-0明细占位保持阻断"
        return "未命中候选组号-需回看原页"
    if has_conflict or matched_variant != first_nonempty(rows, "2026院校专业组代码"):
        return "疑似字符混淆命中-只作人工核页线索"
    return "精确命中专业组标题行-只作原页OCR佐证"


def conservative_grade(is_zero, has_conflict, anomaly_rule_ids, page_avg_confidence):
    if is_zero or has_conflict:
        return "P0-必须人工原页核验"
    if anomaly_rule_ids:
        return "P0-必须人工原页核验"
    try:
        if float(page_avg_confidence or 1) < 0.75:
            return "P1-低置信页优先核验"
    except ValueError:
        pass
    return "P1-标题命中但仍需人工核验"


def pdf_conclusion(rows, matched_variant, title_text, suggested_name):
    is_zero = any(row.get("是否0明细占位") == "true" for row in rows)
    has_conflict = any(row.get("疑似字符混淆") == "是" for row in rows)
    if not matched_variant and is_zero:
        return "候选组号未在原页OCR命中，保持0明细占位；需核2026组号是否变化、取消或OCR漏识。"
    if not matched_variant:
        return "候选组号未在原页OCR命中；不得写回完整院校名或专业组边界。"
    if has_conflict or matched_variant != first_nonempty(rows, "2026院校专业组代码"):
        return "原页OCR标题可提示完整院校名，但专业组代码存在F/O/P/0字符混淆；禁止自动修正，必须人工看原图并对湖北官方系统。"
    if suggested_name and suggested_name in title_text:
        return "原页OCR标题行可佐证完整院校名和专业组标题；仍需人工看原图并对湖北官方系统。"
    return "原页OCR标题行命中组号，但院校名仍需人工看原图确认。"


def main():
    d0_rows = read_csv(D0_WORKBENCH)
    page_manifest_rows = read_csv(PAGE_MANIFEST)
    full_group_rows = read_csv(FULL_GROUP_DRAFT)
    full_major_rows = read_csv(FULL_MAJOR_DRAFT)
    anomaly_rows = read_csv(STRUCTURE_ANOMALY_QUEUE)
    ocr_lines = read_csv(PRIVATE_OCR_LINES)

    page_manifest_by_page = {row["PDF页码"]: row for row in page_manifest_rows}
    group_by_code = {
        row["院校专业组代码OCR规范化"]: row
        for row in full_group_rows
    }
    major_count_by_code = Counter(row["院校专业组代码OCR规范化"] for row in full_major_rows)
    anomalies_by_code = defaultdict(list)
    for row in anomaly_rows:
        anomalies_by_code[row["院校专业组代码OCR规范化"]].append(row)

    rows_by_group = defaultdict(list)
    for row in d0_rows:
        rows_by_group[row["2026院校专业组代码"]].append(row)

    output_rows = []
    for group_code in sorted(rows_by_group):
        rows = rows_by_group[group_code]
        matched_variant, hit = best_hit(group_code, rows, ocr_lines)
        source_pages = sorted(
            {page for row in rows for page in split_values(row.get("来源页码", ""))},
            key=page_sort_key,
        )
        evidence_pages = [hit.get("page", "")] if hit else source_pages
        suggested_name = first_nonempty(rows, "建议完整院校名称")
        title_text = hit.get("text", "") if hit else ""
        group_no = extract_group_no(title_text)
        structured_group = group_by_code.get(group_code, {})
        structured_group_exists = bool(structured_group)
        group_anomalies = anomalies_by_code.get(group_code, [])
        anomaly_rule_ids = unique_join(row.get("异常规则ID", "") for row in group_anomalies)
        anomaly_types = unique_join(row.get("异常类型", "") for row in group_anomalies)
        anomaly_severities = unique_join(row.get("严重程度", "") for row in group_anomalies)
        page_avg_confidence = page_manifest_values(page_manifest_by_page, evidence_pages, "OCR平均置信度")
        is_zero = any(row.get("是否0明细占位") == "true" for row in rows)
        has_conflict = any(row.get("疑似字符混淆") == "是" for row in rows)
        match_method = page_match_method(group_code, matched_variant, structured_group_exists)
        output_rows.append({
            "D0原页证据ID": stable_id("D0PDF", [group_code, unique_join(source_pages), title_text]),
            "来源D0工作台文件": "data/working/issue19-candidate-v3-d0-resolution-workbench.csv",
            "来源D0任务数": str(len(rows)),
            "真实招生明细行数": str(sum(row.get("是否真实招生明细") == "true" for row in rows)),
            "0明细占位行数": str(sum(row.get("是否0明细占位") == "true" for row in rows)),
            "来源D0工作台ID列表": unique_join(row["D0工作台ID"] for row in rows),
            "来源招生明细主表行ID列表": unique_join(row["招生明细主表行ID"] for row in rows),
            "来源期号": first_nonempty(rows, "来源期号"),
            "来源PDF_SHA256": first_nonempty(rows, "来源PDF_SHA256"),
            "数据阶段": DATA_STAGE,
            "最终可用": "false",
            "核验状态": "pdf_page_ocr_evidence_only_pending_manual_image_and_official_system_review",
            "院校代码": first_nonempty(rows, "院校代码"),
            "院校名称OCR": first_nonempty(rows, "院校名称OCR"),
            "建议完整院校名称": suggested_name,
            "2026院校专业组代码": group_code,
            "是否0明细占位组": "true" if any(row.get("是否0明细占位") == "true" for row in rows) else "false",
            "D0问题类型汇总": unique_join(row.get("D0问题类型", "") for row in rows),
            "疑似字符混淆": "是" if any(row.get("疑似字符混淆") == "是" for row in rows) else "否",
            "代码冲突标记汇总": unique_join(row.get("代码冲突标记", "") for row in rows),
            "来源页码汇总": unique_join(source_pages),
            "PDF证据页码": unique_join(evidence_pages),
            "私有页图证据编号": page_manifest_values(page_manifest_by_page, evidence_pages, "私有页图证据编号"),
            "私有页图SHA256": page_manifest_values(page_manifest_by_page, evidence_pages, "私有页图SHA256"),
            "私有OCR文本证据编号": page_manifest_values(page_manifest_by_page, evidence_pages, "私有OCR文本证据编号"),
            "私有OCR文本SHA256": page_manifest_values(page_manifest_by_page, evidence_pages, "私有OCR文本SHA256"),
            "OCR引擎": page_manifest_values(page_manifest_by_page, evidence_pages, "OCR引擎"),
            "渲染DPI": "120",
            "OCR语言": page_manifest_values(page_manifest_by_page, evidence_pages, "识别语言"),
            "页面OCR匹配方式": match_method,
            "OCR标题命中状态": hit_status(rows, matched_variant),
            "OCR命中变体": matched_variant,
            "标题代码与2026组代码关系": title_relation(group_code, matched_variant),
            "OCR标题行号": hit.get("line_no", ""),
            "OCR标题行置信度": hit.get("confidence", ""),
            "OCR标题行SHA256": line_hash(hit) if hit else "",
            "OCR标题行原文": title_text,
            "OCR标题提取组号": group_no,
            "标题组号与代码组号是否一致": "是" if group_no and group_no == normalized_group_suffix(group_code) else ("否" if group_no else ""),
            "标题院校名与建议是否一致": "是" if suggested_name and suggested_name in title_text else ("待核" if suggested_name else ""),
            "同页同校专业组线索": first_nonempty(rows, "同校第19期OCR专业组"),
            "同页同校专业组页码": first_nonempty(rows, "同校第19期OCR页码"),
            "结构化组表是否出现": "是" if structured_group_exists else "否",
            "结构化专业明细数": str(major_count_by_code.get(group_code, 0)),
            "结构化组表专业行数": structured_group.get("OCR专业行数", "0"),
            "结构异常规则ID": anomaly_rule_ids,
            "结构异常类型": anomaly_types,
            "结构异常严重程度": anomaly_severities,
            "保守等级": conservative_grade(is_zero, has_conflict, anomaly_rule_ids, page_avg_confidence),
            "PDF原页OCR核验结论": pdf_conclusion(rows, matched_variant, title_text, suggested_name),
            "是否可写回D0建议": "false",
            "可进入下一阶段": "false",
            "下一步": "人工查看PDF原页截图；再对湖北官方系统/省招办计划和高校官网/章程。不得仅凭本表升级为最终候选。",
        })

    fields = [
        "D0原页证据ID",
        "来源D0工作台文件",
        "来源D0任务数",
        "真实招生明细行数",
        "0明细占位行数",
        "来源D0工作台ID列表",
        "来源招生明细主表行ID列表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "院校代码",
        "院校名称OCR",
        "建议完整院校名称",
        "2026院校专业组代码",
        "是否0明细占位组",
        "D0问题类型汇总",
        "疑似字符混淆",
        "代码冲突标记汇总",
        "来源页码汇总",
        "PDF证据页码",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "OCR引擎",
        "渲染DPI",
        "OCR语言",
        "页面OCR匹配方式",
        "OCR标题命中状态",
        "OCR命中变体",
        "标题代码与2026组代码关系",
        "OCR标题行号",
        "OCR标题行置信度",
        "OCR标题行SHA256",
        "OCR标题行原文",
        "OCR标题提取组号",
        "标题组号与代码组号是否一致",
        "标题院校名与建议是否一致",
        "同页同校专业组线索",
        "同页同校专业组页码",
        "结构化组表是否出现",
        "结构化专业明细数",
        "结构化组表专业行数",
        "结构异常规则ID",
        "结构异常类型",
        "结构异常严重程度",
        "保守等级",
        "PDF原页OCR核验结论",
        "是否可写回D0建议",
        "可进入下一阶段",
        "下一步",
    ]
    write_csv(OUTPUT, output_rows, fields)

    status_counts = Counter(row["OCR标题命中状态"] for row in output_rows)
    relation_counts = Counter(row["标题代码与2026组代码关系"] for row in output_rows)
    match_method_counts = Counter(row["页面OCR匹配方式"] for row in output_rows)
    conservative_grade_counts = Counter(row["保守等级"] for row in output_rows)
    summary = {
        "status": "issue19_candidate_v3_d0_pdf_page_evidence_not_final",
        "generated_by": Path(__file__).name,
        "source_d0_workbench": "data/working/issue19-candidate-v3-d0-resolution-workbench.csv",
        "output_table": "data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv",
        "private_ocr_run_id": "issue19-full-120dpi",
        "private_source_policy": "只读取私有行级OCR和页级哈希；公开输出不写入私有路径、整页OCR文本或页图。",
        "row_count": len(output_rows),
        "source_d0_task_count": len(d0_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "match_method_counts": dict(sorted(match_method_counts.items())),
        "conservative_grade_counts": dict(sorted(conservative_grade_counts.items())),
        "exact_title_hit_count": relation_counts.get("精确命中", 0),
        "confusable_title_hit_count": relation_counts.get("字符混淆命中-禁止自动写回", 0),
        "no_title_hit_count": relation_counts.get("未命中候选组号", 0),
        "zero_detail_group_count": sum(row["是否0明细占位组"] == "true" for row in output_rows),
        "structured_group_hit_count": sum(row["结构化组表是否出现"] == "是" for row in output_rows),
        "structured_group_missing_count": sum(row["结构化组表是否出现"] == "否" for row in output_rows),
        "auto_writeback_allowed_count": sum(row["是否可写回D0建议"] == "true" for row in output_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "fidelity_note": "本表只把D0组级任务绑定到PDF原页OCR标题行和页级哈希；不能替代人工看原页、湖北官方系统和高校官网/章程核验。",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
