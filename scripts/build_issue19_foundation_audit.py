#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import input_snapshot, split_tags


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
OCR_DRAFT_SUMMARY = ROOT / "data/working/issue19-full-admission-plan-ocr-draft-summary.json"
INTEGRITY_SUMMARY = ROOT / "data/working/issue19-integrity-audit-summary.json"
GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
GROUP_QUALITY = ROOT / "data/working/issue19-full-quality-group-tiers.csv"
MAJOR_WORKBENCH = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"
MAJOR_QUEUE = ROOT / "data/working/issue19-full-major-detail-review-queue.csv"
STRUCTURE_ANOMALIES = ROOT / "data/working/issue19-ocr-structure-anomaly-queue.csv"
CANDIDATE_COVERAGE = ROOT / "data/working/issue19-full-admission-plan-candidate-coverage.csv"

SUMMARY_OUTPUT = ROOT / "data/working/issue19-foundation-audit-summary.json"
FINDINGS_OUTPUT = ROOT / "data/working/issue19-foundation-audit-findings.csv"
PAGE_AUDIT_OUTPUT = ROOT / "data/working/issue19-foundation-page-audit.csv"

EXPECTED_PAGE_RANGE = range(10, 241)
FORBIDDEN_PATTERNS = [
    re.compile(r"/Users/"),
    re.compile(r"original_user_path"),
    re.compile(r"\b\d{17}[\dXx]\b"),
    re.compile(r"\b\d{9,12}\b"),
    re.compile(r"final_allowed"),
    re.compile(r"ready_for_discussion"),
    re.compile(r"已确认"),
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
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def group_match_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        row.get("来源页码", ""),
        row.get("版面列", ""),
        row.get("专业组标题行号", ""),
        row.get("专业组标题OCR原文", ""),
    )


def major_match_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        row.get("专业代号OCR", ""),
        row.get("专业名称及备注OCR", ""),
        row.get("来源页码", ""),
        row.get("版面列", ""),
        row.get("专业计划数OCR候选", ""),
        row.get("学费OCR候选", ""),
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


def add_finding(rows, audit_id, domain, item, status, severity, count, evidence, next_step):
    rows.append(
        {
            "审计编号": audit_id,
            "审计域": domain,
            "审计项": item,
            "审计状态": status,
            "严重程度": severity,
            "自动阻断": "是" if severity == "阻断" and status != "通过" else "否",
            "计数": str(count),
            "证据摘要": evidence,
            "下一步": next_step,
        }
    )


def row_has_forbidden_text(row):
    text = json.dumps(row, ensure_ascii=False)
    return any(pattern.search(text) for pattern in FORBIDDEN_PATTERNS)


def counter_to_text(counter, limit=8):
    return "；".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    ocr_summary = json.loads(OCR_DRAFT_SUMMARY.read_text())
    integrity_summary = json.loads(INTEGRITY_SUMMARY.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]

    group_rows = read_csv(GROUPS)
    major_rows = read_csv(MAJORS)
    group_quality_rows = read_csv(GROUP_QUALITY)
    major_workbench_rows = read_csv(MAJOR_WORKBENCH)
    major_queue_rows = read_csv(MAJOR_QUEUE)
    anomaly_rows = read_csv(STRUCTURE_ANOMALIES)
    candidate_coverage_rows = read_csv(CANDIDATE_COVERAGE)

    findings = []
    page_rows = []

    group_ids_by_source_line = {
        index + 1: group_occurrence_id(row, index, source_pdf_sha256)
        for index, row in enumerate(group_rows, start=1)
    }
    group_ids = list(group_ids_by_source_line.values())
    major_ids_by_source_line = {
        index + 1: major_line_id(row, index, source_pdf_sha256)
        for index, row in enumerate(major_rows, start=1)
    }
    major_ids = list(major_ids_by_source_line.values())
    group_ids_by_key = {group_match_key(row): group_ids_by_source_line[index + 1] for index, row in enumerate(group_rows, start=1)}
    groups_by_code = defaultdict(list)
    for index, row in enumerate(group_rows, start=1):
        groups_by_code[row["院校专业组代码OCR规范化"]].append(group_ids_by_source_line[index + 1])

    source_major_by_line = {str(index + 1): row for index, row in enumerate(major_rows, start=1)}
    workbench_by_line = {row["专业明细源行号"]: row for row in major_workbench_rows}
    group_quality_by_id = {row["专业组出现ID"]: row for row in group_quality_rows}
    quality_group_ids = set(group_quality_by_id)
    workbench_group_ids = {row["专业组出现ID"] for row in major_workbench_rows if row["专业组出现ID"]}

    anomaly_counter = Counter(major_match_key(row) for row in anomaly_rows)
    workbench_anomaly_counter = Counter()
    workbench_high_anomaly_counter = Counter()
    for row in major_workbench_rows:
        source = source_major_by_line.get(row["专业明细源行号"])
        if not source:
            continue
        key = major_match_key(source)
        workbench_anomaly_counter[key] += as_int(row["专业行结构异常数"]) or 0
        workbench_high_anomaly_counter[key] += as_int(row["专业行高严重结构异常数"]) or 0

    missing_pages = [
        str(page)
        for page in EXPECTED_PAGE_RANGE
        if not any(as_int(row.get("来源页码")) == page for row in group_rows)
        or not any(as_int(row.get("来源页码")) == page for row in major_rows)
    ]
    outside_pages = [
        row.get("来源页码", "")
        for row in group_rows + major_rows
        if (as_int(row.get("来源页码")) or 0) not in EXPECTED_PAGE_RANGE
    ]
    exact_group_occurrence_major_count = 0
    fallback_unique_group_code_major_count = 0
    fallback_candidate_major_count = 0
    fallback_sample_major_count = 0
    unmatched_major_group_occurrence_count = 0
    fallback_groups = set()
    for row in major_rows:
        if group_match_key(row) in group_ids_by_key:
            exact_group_occurrence_major_count += 1
            continue
        code_groups = groups_by_code.get(row["院校专业组代码OCR规范化"], [])
        if len(code_groups) == 1:
            fallback_unique_group_code_major_count += 1
            fallback_groups.add(code_groups[0])
            fallback_candidate_major_count += row.get("候选池V1命中") == "是"
            fallback_sample_major_count += row.get("样本学校命中") == "是"
            continue
        unmatched_major_group_occurrence_count += 1

    duplicate_group_code_counts = Counter(row["院校专业组代码OCR规范化"] for row in group_rows)
    duplicate_group_codes = {code: count for code, count in duplicate_group_code_counts.items() if count > 1}
    duplicate_group_code_major_count = sum(
        duplicate_group_code_counts[row["院校专业组代码OCR规范化"]] > 1 for row in major_rows
    )
    major_source_signature_counter = Counter(
        (
            row.get("院校代码", ""),
            row.get("院校专业组代码OCR规范化", ""),
            row.get("来源页码", ""),
            row.get("版面列", ""),
            row.get("专业起始行号", ""),
            row.get("专业起始y", ""),
            row.get("专业代号OCR", ""),
            row.get("专业名称及备注OCR", ""),
            row.get("专业计划数OCR候选", ""),
            row.get("学费OCR候选", ""),
        )
        for row in major_rows
    )
    duplicate_major_source_signatures = sum(
        count for count in major_source_signature_counter.values() if count > 1
    )
    major_code_counter_by_group = defaultdict(Counter)
    major_group_label_by_id = {}
    for row in major_workbench_rows:
        group_id = row.get("专业组出现ID", "")
        major_code = row.get("专业代号OCR", "")
        if not group_id or not major_code:
            continue
        major_code_counter_by_group[group_id][major_code] += 1
        major_group_label_by_id[group_id] = (
            row.get("院校代码", ""),
            row.get("院校专业组代码OCR规范化", ""),
            row.get("院校名称OCR", ""),
            row.get("来源页码", ""),
        )
    duplicate_major_code_group_count = 0
    duplicate_major_code_pair_count = 0
    duplicate_major_code_row_count = 0
    duplicate_major_code_examples = []
    for group_id, counter in major_code_counter_by_group.items():
        duplicates = {code: count for code, count in counter.items() if count > 1}
        if not duplicates:
            continue
        duplicate_major_code_group_count += 1
        duplicate_major_code_pair_count += len(duplicates)
        duplicate_major_code_row_count += sum(duplicates.values())
        if len(duplicate_major_code_examples) < 5:
            school_code, group_code, school_name, page = major_group_label_by_id[group_id]
            duplicate_major_code_examples.append(
                f"{school_code}/{group_code}/{school_name}/页{page}:"
                + ",".join(f"{code}x{count}" for code, count in sorted(duplicates.items()))
            )

    line_mismatch_count = 0
    field_drift_count = 0
    for line, source in source_major_by_line.items():
        output = workbench_by_line.get(line)
        if not output:
            line_mismatch_count += 1
            continue
        expected_id = major_ids_by_source_line[as_int(line)]
        compared_fields = [
            "院校代码",
            "院校名称OCR",
            "院校专业组代码OCR规范化",
            "专业组号OCR",
            "专业组标题OCR原文",
            "来源页码",
            "版面列",
            "专业组标题行号",
            "专业代号OCR",
            "专业名称及备注OCR",
            "再选科目OCR候选",
            "专业计划数OCR候选",
            "专业计划数OCR数字候选",
            "学费OCR候选",
            "学费OCR数字候选",
        ]
        if output.get("专业行ID") != expected_id:
            field_drift_count += 1
            continue
        if any(output.get(field, "") != source.get(field, "") for field in compared_fields):
            field_drift_count += 1

    sequence_issue_count = 0
    sequences_by_group = defaultdict(list)
    for row in major_workbench_rows:
        sequences_by_group[row["专业组出现ID"]].append(as_int(row["专业组内专业序号"]) or -1)
    for sequence in sequences_by_group.values():
        if sorted(sequence) != list(range(1, len(sequence) + 1)):
            sequence_issue_count += 1

    final_true_count = sum(row.get("最终可用") != "false" for row in major_workbench_rows + group_quality_rows)
    privacy_leak_count = sum(row_has_forbidden_text(row) for row in major_workbench_rows + group_quality_rows)

    field_flag_counter = Counter()
    tag_counter = Counter()
    missing_subject_count = 0
    missing_plan_count = 0
    missing_tuition_count = 0
    non_plain_plan_count = 0
    non_plain_tuition_count = 0
    suspicious_tuition_count = 0
    for row in major_workbench_rows:
        flags = split_tags(row.get("专业字段完整性标记", ""))
        tags = split_tags(row.get("专业偏好和风险标签原文", ""))
        field_flag_counter.update(flags)
        tag_counter.update(tags)
        missing_subject_count += "missing_subject_candidate" in flags
        missing_plan_count += "missing_plan_count_candidate" in flags
        missing_tuition_count += "missing_tuition_candidate" in flags
        non_plain_plan_count += row.get("专业计划数是否纯数字") == "否"
        non_plain_tuition_count += row.get("学费是否纯数字") == "否"
        tuition = as_int(row.get("学费OCR数字候选"))
        suspicious_tuition_count += (
            row.get("学费是否纯数字") == "否" or (tuition is not None and 0 < tuition <= 500)
        )

    candidate_status_counter = Counter(
        "命中" if row.get("第19期全量OCR命中") == "是" else "未命中"
        for row in candidate_coverage_rows
    )

    add_finding(
        findings,
        "F001",
        "源文件",
        "第19期 PDF 指纹固定",
        "通过" if sha256(ROOT / issue19_source["source"]["local_private_path"]) == source_pdf_sha256 else "失败",
        "阻断",
        1,
        f"PDF SHA256={source_pdf_sha256}",
        "如失败，必须重新记录来源 PDF 并全量重跑 OCR。",
    )
    add_finding(
        findings,
        "F002",
        "页码覆盖",
        "page_range_used 10-240 每页均有专业组和专业明细",
        "通过" if not missing_pages and not outside_pages else "失败",
        "阻断",
        len(missing_pages) + len(outside_pages),
        f"缺页={','.join(missing_pages[:20]) or '无'}；越界页数={len(outside_pages)}",
        "如失败，必须回到 OCR 渲染页和切组脚本确认页码范围。",
    )
    add_finding(
        findings,
        "F003",
        "行数闭环",
        "学校/专业组/专业明细行数与 OCR 摘要一致",
        "通过"
        if (
            len(group_rows) == ocr_summary["counts"]["OCR院校专业组数"]
            and len(major_rows) == ocr_summary["counts"]["OCR专业行数"]
            and len(major_workbench_rows) == len(major_rows)
        )
        else "失败",
        "阻断",
        len(major_workbench_rows),
        f"专业组={len(group_rows)}；专业明细={len(major_rows)}；工作台={len(major_workbench_rows)}",
        "如失败，不能继续筛选候选，先定位哪一层丢行或重复。",
    )
    add_finding(
        findings,
        "F004",
        "主键",
        "专业组出现ID和专业行ID唯一",
        "通过" if len(set(group_ids)) == len(group_ids) and len(set(major_ids)) == len(major_ids) else "失败",
        "阻断",
        (len(group_ids) - len(set(group_ids))) + (len(major_ids) - len(set(major_ids))),
        f"专业组ID={len(set(group_ids))}/{len(group_ids)}；专业行ID={len(set(major_ids))}/{len(major_ids)}",
        "如失败，不能用该底座联表，必须修正 ID 生成口径。",
    )
    add_finding(
        findings,
        "F005",
        "源行追踪",
        "逐专业工作台逐行回指原始 OCR 明细且字段未漂移",
        "通过" if not line_mismatch_count and not field_drift_count else "失败",
        "阻断",
        line_mismatch_count + field_drift_count,
        f"缺失源行={line_mismatch_count}；字段漂移={field_drift_count}",
        "如失败，必须禁止使用逐专业工作台并重建。",
    )
    add_finding(
        findings,
        "F006",
        "专业组联表",
        "逐专业工作台关联到专业组质量索引且无串组",
        "通过"
        if workbench_group_ids.issubset(quality_group_ids)
        and len(workbench_group_ids) == len(quality_group_ids) - ocr_summary["counts"]["无专业行专业组数"]
        else "失败",
        "阻断",
        len(quality_group_ids - workbench_group_ids),
        f"有明细专业组={len(workbench_group_ids)}；质量索引专业组={len(quality_group_ids)}；无专业行组={ocr_summary['counts']['无专业行专业组数']}",
        "如失败，必须复核专业组出现ID和跨页续组逻辑。",
    )
    add_finding(
        findings,
        "F007",
        "异常闭环",
        "结构异常 5129 条全部精确挂到专业明细",
        "通过" if anomaly_counter == workbench_anomaly_counter else "失败",
        "阻断",
        sum((anomaly_counter - workbench_anomaly_counter).values())
        + sum((workbench_anomaly_counter - anomaly_counter).values()),
        f"异常队列={sum(anomaly_counter.values())}；工作台聚合={sum(workbench_anomaly_counter.values())}",
        "如失败，不能相信行级异常标记，必须修正 exact match key。",
    )
    add_finding(
        findings,
        "F008",
        "顺序",
        "专业组内专业序号连续无断点",
        "通过" if not sequence_issue_count else "失败",
        "阻断",
        sequence_issue_count,
        f"异常专业组数={sequence_issue_count}",
        "如失败，必须核对组内明细排序，防止调剂范围判断错位。",
    )
    add_finding(
        findings,
        "F009",
        "发布边界",
        "公开工作台不含本地路径、身份号、最终可用结论",
        "通过" if not final_true_count and not privacy_leak_count else "失败",
        "阻断",
        final_true_count + privacy_leak_count,
        f"最终可用非false={final_true_count}；敏感/越界文本={privacy_leak_count}",
        "如失败，必须清理公开数据后再提交。",
    )
    add_finding(
        findings,
        "R001",
        "OCR 质量",
        "字段完整性和结构异常仍需人工核页",
        "需人工复核",
        "高",
        sum(field_flag_counter.values()) + integrity_summary["structure_anomaly_count"],
        f"字段标记={counter_to_text(field_flag_counter)}；结构异常={integrity_summary['structure_anomaly_count']}",
        "按逐专业复核队列优先核 P0、候选池和偏好专业。",
    )
    add_finding(
        findings,
        "R002",
        "学费/计划",
        "计划数和学费字段存在 OCR 错位风险",
        "需人工复核",
        "高",
        non_plain_plan_count + non_plain_tuition_count + suspicious_tuition_count,
        f"非纯数字计划={non_plain_plan_count}；非纯数字学费={non_plain_tuition_count}；异常学费={suspicious_tuition_count}",
        "所有进入候选池的计划数、学费必须回看原 PDF 和官方系统。",
    )
    add_finding(
        findings,
        "R003",
        "选科",
        "再选科目 OCR 候选缺失较多",
        "需人工复核",
        "高",
        missing_subject_count,
        f"缺再选科目候选专业行={missing_subject_count}",
        "候选专业必须逐条确认选科要求，尤其是化学/地理限制。",
    )
    add_finding(
        findings,
        "R004",
        "调剂风险",
        "重复专业组代码和无专业明细组需要单独核页",
        "需人工复核",
        "高",
        len(duplicate_group_codes) + ocr_summary["counts"]["无专业行专业组数"],
        f"重复组码={duplicate_group_codes}；重复组码专业行={duplicate_group_code_major_count}；无专业行组={ocr_summary['counts']['无专业行专业组数']}",
        "判断能否服从调剂前，必须打开完整专业组核对全部专业。",
    )
    add_finding(
        findings,
        "R005",
        "候选池",
        "第一版候选池仍有未命中项",
        "需人工复核",
        "中",
        candidate_status_counter.get("未命中", 0),
        f"候选覆盖状态={counter_to_text(candidate_status_counter)}",
        "未命中项不能直接删除，要回 PDF 页和院校官网确认。",
    )
    add_finding(
        findings,
        "R006",
        "偏好/风险",
        "偏好专业和硬风险标签已进入复核队列",
        "需人工复核",
        "中",
        sum(tag_counter.values()),
        f"标签分布={counter_to_text(tag_counter, 12)}",
        "后续筛选只能把标签当线索，不能当最终专业结论。",
    )
    add_finding(
        findings,
        "R007",
        "重复明细",
        "原始专业明细签名重复需抽检",
        "需人工复核" if duplicate_major_source_signatures else "通过",
        "中",
        duplicate_major_source_signatures,
        f"重复专业明细签名行数={duplicate_major_source_signatures}",
        "如重复行进入候选池，需回看 PDF 判断是否真实重复招生或 OCR 重复。",
    )
    add_finding(
        findings,
        "R008",
        "专业组归属",
        "部分专业行依赖唯一组码回退归属",
        "需人工复核" if fallback_unique_group_code_major_count else "通过",
        "高",
        fallback_unique_group_code_major_count,
        f"精确归属={exact_group_occurrence_major_count}；回退归属={fallback_unique_group_code_major_count}；回退专业组={len(fallback_groups)}；候选命中回退={fallback_candidate_major_count}；样本学校回退={fallback_sample_major_count}",
        "回退归属多为跨页/跨栏续组线索，进入候选前必须回看原 PDF 页确认组边界。",
    )
    add_finding(
        findings,
        "R009",
        "专业代号",
        "同一专业组内专业代号重复",
        "需人工复核" if duplicate_major_code_row_count else "通过",
        "高",
        duplicate_major_code_row_count,
        f"重复专业组={duplicate_major_code_group_count}；重复代号组={duplicate_major_code_pair_count}；示例={'；'.join(duplicate_major_code_examples) or '无'}",
        "专业代号重复可能是真实方向拆分，也可能是 OCR 串行或重复识别，候选专业组必须人工核页。",
    )

    anomaly_by_page = Counter(row.get("来源页码", "") for row in anomaly_rows)
    high_anomaly_by_page = Counter(row.get("来源页码", "") for row in anomaly_rows if row.get("严重程度") == "高")
    group_by_page = defaultdict(list)
    major_by_page = defaultdict(list)
    for row in group_rows:
        group_by_page[row.get("来源页码", "")].append(row)
    for row in major_workbench_rows:
        major_by_page[row.get("来源页码", "")].append(row)

    for page in EXPECTED_PAGE_RANGE:
        key = str(page)
        page_groups = group_by_page[key]
        page_majors = major_by_page[key]
        page_rows.append(
            {
                "来源期号": source_issue,
                "来源PDF_SHA256": source_pdf_sha256,
                "来源页码": key,
                "页面专业组数": str(len(page_groups)),
                "页面专业明细数": str(len(page_majors)),
                "页面院校数": str(len({row.get("院校代码", "") for row in page_groups if row.get("院校代码", "")})),
                "页面结构异常数": str(anomaly_by_page[key]),
                "页面高严重结构异常数": str(high_anomaly_by_page[key]),
                "页面偏好专业明细数": str(sum(bool(row.get("专业偏好方向")) for row in page_majors)),
                "页面风险专业明细数": str(sum(row.get("专业风险等级") != "未触发硬风险" for row in page_majors)),
                "页面候选池V1专业明细数": str(sum(row.get("专业行候选池V1命中") == "是" for row in page_majors)),
                "页面复核优先级": "P0-优先核页"
                if anomaly_by_page[key]
                or any(row.get("专业行候选池V1命中") == "是" for row in page_majors)
                or any(bool(row.get("专业偏好方向")) for row in page_majors)
                else "P2-常规抽检",
                "页面审计状态": "有结构化记录待核页" if page_groups and page_majors else "缺结构化记录需回溯OCR",
                "下一步": "按页回看第19期原PDF，核对该页专业组边界、专业代号、计划数、学费和选科。",
            }
        )

    automatic_blocking_findings = [
        row for row in findings if row["自动阻断"] == "是" and row["审计状态"] != "通过"
    ]
    manual_review_findings = [row for row in findings if row["审计状态"] == "需人工复核"]
    status = (
        "issue19_foundation_machine_checks_passed_need_pdf_official_review"
        if not automatic_blocking_findings
        else "issue19_foundation_machine_checks_failed"
    )
    summary = {
        "status": status,
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "issue19_foundation_audit",
        "generated_by": "scripts/build_issue19_foundation_audit.py",
        "inputs": input_snapshot(
            ROOT,
            [
                ISSUE19_SOURCE,
                OCR_DRAFT_SUMMARY,
                INTEGRITY_SUMMARY,
                GROUPS,
                MAJORS,
                GROUP_QUALITY,
                MAJOR_WORKBENCH,
                MAJOR_QUEUE,
                STRUCTURE_ANOMALIES,
                CANDIDATE_COVERAGE,
            ],
        ),
        "expected_page_range": [EXPECTED_PAGE_RANGE.start, EXPECTED_PAGE_RANGE.stop - 1],
        "page_count": len(page_rows),
        "missing_page_count": len(missing_pages),
        "outside_page_row_count": len(outside_pages),
        "school_count": ocr_summary["counts"]["OCR院校数"],
        "group_count": len(group_rows),
        "major_count": len(major_rows),
        "major_workbench_count": len(major_workbench_rows),
        "major_review_queue_count": len(major_queue_rows),
        "structure_anomaly_count": len(anomaly_rows),
        "matched_structure_anomaly_count": sum(workbench_anomaly_counter.values()),
        "automatic_blocking_findings_count": len(automatic_blocking_findings),
        "manual_review_findings_count": len(manual_review_findings),
        "finding_status_counts": dict(Counter(row["审计状态"] for row in findings)),
        "finding_severity_counts": dict(Counter(row["严重程度"] for row in findings)),
        "duplicate_group_code_count": len(duplicate_group_codes),
        "duplicate_group_code_row_count": sum(duplicate_group_codes.values()),
        "duplicate_group_code_major_row_count": duplicate_group_code_major_count,
        "duplicate_major_source_signature_row_count": duplicate_major_source_signatures,
        "exact_group_occurrence_major_count": exact_group_occurrence_major_count,
        "fallback_unique_group_code_major_count": fallback_unique_group_code_major_count,
        "fallback_unique_group_code_group_count": len(fallback_groups),
        "fallback_candidate_major_count": fallback_candidate_major_count,
        "fallback_sample_major_count": fallback_sample_major_count,
        "unmatched_major_group_occurrence_count": unmatched_major_group_occurrence_count,
        "duplicate_major_code_group_count": duplicate_major_code_group_count,
        "duplicate_major_code_pair_count": duplicate_major_code_pair_count,
        "duplicate_major_code_row_count": duplicate_major_code_row_count,
        "field_flag_counts": dict(field_flag_counter),
        "risk_and_preference_tag_counts": dict(tag_counter),
        "candidate_coverage_status_counts": dict(candidate_status_counter),
        "outputs": [
            str(FINDINGS_OUTPUT.relative_to(ROOT)),
            str(PAGE_AUDIT_OUTPUT.relative_to(ROOT)),
        ],
        "notes": [
            "本审计只证明机器层面的底座闭环，不证明 OCR 文字等同于最终官方事实。",
            "所有招生明细进入志愿方案前，仍必须回看第19期 PDF、湖北志愿系统和高校招生章程/官网。",
            "字段异常、费用、选科、调剂范围和候选池未命中项均保持人工复核状态。",
        ],
    }

    finding_fields = [
        "审计编号",
        "审计域",
        "审计项",
        "审计状态",
        "严重程度",
        "自动阻断",
        "计数",
        "证据摘要",
        "下一步",
    ]
    page_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "来源页码",
        "页面专业组数",
        "页面专业明细数",
        "页面院校数",
        "页面结构异常数",
        "页面高严重结构异常数",
        "页面偏好专业明细数",
        "页面风险专业明细数",
        "页面候选池V1专业明细数",
        "页面复核优先级",
        "页面审计状态",
        "下一步",
    ]
    write_csv(FINDINGS_OUTPUT, findings, finding_fields)
    write_csv(PAGE_AUDIT_OUTPUT, page_rows, page_fields)
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出第19期底座审计摘要：{SUMMARY_OUTPUT}")
    print(f"写出第19期底座审计发现：{FINDINGS_OUTPUT}")
    print(f"写出第19期按页审计表：{PAGE_AUDIT_OUTPUT}")
    print(f"自动阻断项：{len(automatic_blocking_findings)}")
    print(f"人工复核项：{len(manual_review_findings)}")


if __name__ == "__main__":
    main()
