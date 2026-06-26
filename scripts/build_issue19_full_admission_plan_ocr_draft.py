#!/usr/bin/env python3
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OCR_LINES = ROOT / "private/ocr-runs/issue19-full-120dpi/ocr-lines.csv"
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
WORKING_DIR = ROOT / "data/working"
GROUP_OUTPUT = WORKING_DIR / "issue19-full-admission-plan-group-ocr-draft.csv"
MAJOR_OUTPUT = WORKING_DIR / "issue19-full-admission-plan-major-ocr-draft.csv"
SCHOOL_OUTPUT = WORKING_DIR / "issue19-full-admission-plan-school-ocr-draft.csv"
CANDIDATE_COVERAGE_OUTPUT = WORKING_DIR / "issue19-full-admission-plan-candidate-coverage.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-full-admission-plan-ocr-draft-summary.json"
CANDIDATE_POOL = ROOT / "data/working/candidate-pool-v1.csv"
SAMPLE_SCHOOLS = ROOT / "data/working/issue19-sample-schools-20.csv"

PLAN_PAGE_START = 10
PLAN_PAGE_END = 240
TUITION_LIMIT = 15000

RISK_KEYWORDS = {
    "rejected_medical": ["临床医学", "护理", "护理学", "预防医学", "药学", "医学", "医师", "中医学"],
    "high_fee_or_coop": ["中外合作", "合作办学", "高收费"],
    "body_or_exam_limit": ["色盲", "色弱", "单色识别", "不予录取", "体检"],
    "language_or_single_subject": ["英语语种", "外语语种", "单科", "英语单科"],
    "special_plan_or_direction": ["国家专项", "地方专项", "民族班", "预科", "定向", "免费"],
}

PREFERENCE_KEYWORDS = {
    "priority_1_digital_media": ["数字媒体技术"],
    "priority_2_computer": [
        "计算机",
        "软件工程",
        "网络工程",
        "数据科学",
        "大数据",
        "人工智能",
        "物联网",
        "信息安全",
        "密码科学",
        "智能科学",
    ],
    "priority_3_teacher": [
        "师范",
        "教育学",
        "小学教育",
        "教育技术",
        "学前教育",
        "特殊教育",
        "科学教育",
    ],
}


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def as_float(row, key):
    try:
        return float(row[key])
    except (TypeError, ValueError):
        return 0.0


def layout_side(row):
    return "left" if as_float(row, "x") < 0.48 else "right"


def normalize_code_text(text):
    return (
        text.upper()
        .replace("［", "")
        .replace("[", "")
        .replace("]", "")
        .replace("｜", "")
        .replace("|", "")
        .replace("/", "")
        .replace(" ", "")
        .replace("Ｏ", "0")
        .replace("O", "0")
        .replace("Ｉ", "1")
        .replace("I", "1")
        .replace("Ｌ", "1")
        .replace("L", "1")
    )


def normalize_title_text(text):
    return (
        text.strip()
        .replace("［", "")
        .replace("[", "")
        .replace("]", "")
        .replace("｜", "")
        .replace("|", "")
        .replace("/", "")
        .replace("「", "")
        .replace("」", "")
    )


def normalize_group_code(code):
    return (
        code.upper()
        .replace("Ｏ", "0")
        .replace("O", "0")
        .replace("Ｉ", "1")
        .replace("I", "1")
        .replace("Ｌ", "1")
        .replace("L", "1")
    )


def parse_group_title(text):
    if "第" not in text or "组" not in text:
        return None
    normalized = normalize_code_text(text)
    match = re.search(r"([A-Z])(\d{3})(\d{2})", normalized)
    if not match:
        return None

    school_code = f"{match.group(1)}{match.group(2)}"
    group_no = match.group(3)
    group_code = f"{school_code}{group_no}"

    title = normalize_title_text(text)
    code_match = re.search(r"[A-Za-zＡ-Ｚ][0-9ＯOＩIＬL]{3}[0-9ＯOＩIＬL]{2}", title)
    school_name = ""
    if code_match:
        rest = title[code_match.end():]
        if "第" in rest:
            school_name = rest.split("第", 1)[0].strip()
    school_name = re.sub(r"^[,，、:：\\s]+|[,，、:：\\s]+$", "", school_name)

    return {
        "院校代码": school_code,
        "院校名称OCR": school_name,
        "院校专业组代码OCR规范化": group_code,
        "专业组号OCR": group_no,
    }


def is_group_title(row):
    text = row.get("text", "")
    if "第" not in text or "组" not in text:
        return False
    normalized = normalize_code_text(text)
    return bool(re.search(r"[A-Z]\d{3}\d{2}", normalized))


def reading_key(row):
    side_order = 0 if row["版面列"] == "left" else 1
    return (
        int(row["page"]),
        side_order,
        -as_float(row, "y"),
        as_float(row, "x"),
        int(row["line_no"]),
    )


def is_name_zone(row):
    x = as_float(row, "x")
    side = row["版面列"]
    text = row.get("text", "").strip()
    if not text:
        return False
    if row.get("line_type") in {"page_header", "table_header"}:
        return False
    if "湖北招生考试" in text or "hbksw.com" in text or text.isdigit():
        return False
    if side == "left":
        return x < 0.35
    return 0.50 <= x < 0.78


def is_major_start(text):
    text = text.strip()
    if not text:
        return False
    if re.match(r"^[0-9A-ZＡ-Ｚ]{1,2}\s*[/|、 ]?\s*[\\+\"]", text, re.I):
        return False
    return bool(re.match(r"^[0-9A-ZＡ-Ｚ]{1,2}\s*[/|、 ]?\s*[\u4e00-\u9fffA-Za-z]", text, re.I))


def extract_major_code(text):
    match = re.match(r"^([0-9A-ZＡ-Ｚ]{1,2})\s*[/|、 ]?", text.strip(), re.I)
    return normalize_group_code(match.group(1)) if match else ""


def clean_major_name(text):
    return re.sub(r"^[0-9A-ZＡ-Ｚ]{1,2}\s*[/|、 ]?\s*", "", text.strip(), flags=re.I)


def zone_for(row):
    x = as_float(row, "x")
    side = row["版面列"]
    text = row.get("text", "").strip()
    if not text:
        return ""
    if side == "left":
        if 0.35 <= x < 0.40:
            return "subject"
        if 0.40 <= x < 0.44:
            return "count"
        if 0.44 <= x < 0.49:
            return "tuition"
    else:
        if 0.78 <= x < 0.82:
            return "subject"
        if 0.82 <= x < 0.86:
            return "count"
        if 0.86 <= x < 0.91:
            return "tuition"
    return ""


def nearest_value(rows, y, zone, max_distance=0.018):
    candidates = []
    for row in rows:
        if zone_for(row) != zone:
            continue
        text = row.get("text", "").strip()
        if zone in {"count", "tuition"} and not re.search(r"\d", text):
            continue
        distance = abs(as_float(row, "y") - y)
        if distance <= max_distance:
            candidates.append((distance, text))
    if not candidates:
        return ""
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def tag_text(text):
    tags = []
    for tag, keywords in PREFERENCE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)
    for tag, keywords in RISK_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)
    if any(value > TUITION_LIMIT for value in extract_numbers(text)):
        tags.append("tuition_over_15000")
    return ";".join(dict.fromkeys(tags))


def extract_numbers(text):
    values = []
    for match in re.finditer(r"\d{4,6}", text or ""):
        try:
            values.append(int(match.group(0)))
        except ValueError:
            pass
    return values


def first_number(text):
    match = re.search(r"\d+", text or "")
    return match.group(0) if match else ""


def is_plain_number(text):
    return bool(re.fullmatch(r"\d+", (text or "").strip()))


def yes_no(condition):
    return "是" if condition else "否"


def field_flags(*, subject, plan_count, tuition, confidence, tags):
    flags = []
    if not subject:
        flags.append("missing_subject_candidate")
    if not plan_count:
        flags.append("missing_plan_count_candidate")
    elif not is_plain_number(plan_count):
        flags.append("plan_count_not_plain_number")
    if not tuition:
        flags.append("missing_tuition_candidate")
    elif not is_plain_number(tuition):
        flags.append("tuition_not_plain_number")
    try:
        if float(confidence) < 0.5:
            flags.append("low_ocr_confidence")
    except (TypeError, ValueError):
        flags.append("missing_ocr_confidence")
    if "tuition_over_15000" in (tags or ""):
        flags.append("tuition_over_15000")
    return ";".join(flags)


def summarize_values(span_rows, zone):
    values = []
    for row in span_rows:
        if zone_for(row) != zone:
            continue
        text = row.get("text", "").strip()
        if text and text not in values:
            values.append(text)
    return "；".join(values)


def best_school_names(group_rows):
    names_by_code = defaultdict(Counter)
    for row in group_rows:
        name = row.get("院校名称OCR", "").strip()
        if name:
            names_by_code[row["院校代码"]][name] += 1
    best = {}
    for code, counts in names_by_code.items():
        best[code] = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))[0][0]
    return best


def build_major_rows(group, span_rows):
    majors = []
    current = None
    current_lines = []

    name_rows = [row for row in span_rows if is_name_zone(row)]
    for row in name_rows:
        text = row["text"].strip()
        if is_group_title(row):
            continue
        if is_major_start(text):
            if current:
                current["专业名称及备注OCR"] = "".join(current_lines)
                current["偏好和风险标签"] = tag_text(current["专业名称及备注OCR"])
                majors.append(current)
            current = {
                **group,
                "来源页码": row["page"],
                "版面列": row["版面列"],
                "专业代号OCR": extract_major_code(text),
                "专业名称及备注OCR": "",
                "专业起始行号": row["line_no"],
                "专业起始y": f"{as_float(row, 'y'):.6f}",
                "OCR置信度": row["confidence"],
                "再选科目OCR候选": nearest_value(span_rows, as_float(row, "y"), "subject"),
                "专业计划数OCR候选": nearest_value(span_rows, as_float(row, "y"), "count"),
                "学费OCR候选": nearest_value(span_rows, as_float(row, "y"), "tuition"),
                "核验状态": "needs_manual_pdf_review",
                "偏好和风险标签": "",
            }
            current_lines = [clean_major_name(text)]
        elif current:
            current_lines.append(text)

    if current:
        current["专业名称及备注OCR"] = "".join(current_lines)
        current["偏好和风险标签"] = tag_text(current["专业名称及备注OCR"])
        majors.append(current)

    return majors


def group_codes_from_candidate_pool():
    codes = set()
    if not CANDIDATE_POOL.exists():
        return codes
    with CANDIDATE_POOL.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            text = row.get("学校/专业组", "")
            match = re.search(r"([A-Z])([0-9]{3})([0-9]{2})", normalize_code_text(text))
            if match:
                codes.add(match.group(0))
    return codes


def candidate_pool_rows():
    if not CANDIDATE_POOL.exists():
        return []
    rows = []
    with CANDIDATE_POOL.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            text = row.get("学校/专业组", "")
            match = re.search(r"([A-Z])([0-9]{3})([0-9]{2})", normalize_code_text(text))
            row["候选专业组代码OCR规范化"] = match.group(0) if match else ""
            rows.append(row)
    return rows


def school_codes_from_sample_schools():
    codes = set()
    if not SAMPLE_SCHOOLS.exists():
        return codes
    with SAMPLE_SCHOOLS.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            for code in re.findall(r"[A-Z]\d{3}", normalize_code_text(row.get("第19期OCR院校代码线索", ""))):
                codes.add(code)
    return codes


def main():
    rows = [
        row for row in read_rows(OCR_LINES)
        if PLAN_PAGE_START <= int(row["page"]) <= PLAN_PAGE_END
    ]
    for row in rows:
        row["版面列"] = layout_side(row)

    ordered_rows = sorted(rows, key=reading_key)
    group_indexes = [idx for idx, row in enumerate(ordered_rows) if is_group_title(row)]

    group_rows = []
    major_rows = []
    for position, idx in enumerate(group_indexes):
        parsed = parse_group_title(ordered_rows[idx]["text"])
        if not parsed:
            continue
        next_idx = group_indexes[position + 1] if position + 1 < len(group_indexes) else len(ordered_rows)
        title_row = ordered_rows[idx]
        span_rows = ordered_rows[idx + 1:next_idx]
        group = {
            **parsed,
            "专业组标题OCR原文": title_row["text"],
            "来源页码": title_row["page"],
            "版面列": title_row["版面列"],
            "专业组标题行号": title_row["line_no"],
            "专业组标题y": f"{as_float(title_row, 'y'):.6f}",
        }
        majors = build_major_rows(group, span_rows)
        major_rows.extend(majors)
        tags = sorted({tag for major in majors for tag in major["偏好和风险标签"].split(";") if tag})
        all_text = "；".join([
            group["专业组标题OCR原文"],
            summarize_values(span_rows, "tuition"),
            *[major["专业名称及备注OCR"] for major in majors],
        ])
        for tag in tag_text(all_text).split(";"):
            if tag and tag not in tags:
                tags.append(tag)
        group_rows.append({
            **group,
            "OCR专业行数": len(majors),
            "再选科目OCR候选": summarize_values(span_rows, "subject"),
            "人数OCR候选": summarize_values(span_rows, "count"),
            "学费OCR候选": summarize_values(span_rows, "tuition"),
            "偏好和风险标签": ";".join(sorted(tags)),
            "核验状态": "needs_manual_pdf_review",
            "备注": "第19期全量OCR自动切组初稿；必须回看原PDF页确认。",
        })

    canonical_names = best_school_names(group_rows)
    for row in group_rows + major_rows:
        row["院校名称OCR"] = canonical_names.get(row["院校代码"], row.get("院校名称OCR", ""))

    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_pdf_sha256 = issue19_source["source"]["sha256"]
    candidate_codes = group_codes_from_candidate_pool()
    sample_school_codes = school_codes_from_sample_schools()

    for row in group_rows:
        row["来源期号"] = "《湖北招生考试》2026年第19期"
        row["来源PDF_SHA256"] = source_pdf_sha256
        row["数据阶段"] = "full_ocr_draft"
        row["最终可用"] = "false"
        row["候选池V1命中"] = yes_no(row["院校专业组代码OCR规范化"] in candidate_codes)
        row["样本学校命中"] = yes_no(row["院校代码"] in sample_school_codes)
        row["字段完整性标记"] = field_flags(
            subject=row["再选科目OCR候选"],
            plan_count=row["人数OCR候选"],
            tuition=row["学费OCR候选"],
            confidence="0.5",
            tags=row["偏好和风险标签"],
        )
    for row in major_rows:
        tags = row["偏好和风险标签"]
        row["来源期号"] = "《湖北招生考试》2026年第19期"
        row["来源PDF_SHA256"] = source_pdf_sha256
        row["数据阶段"] = "full_ocr_draft"
        row["最终可用"] = "false"
        row["候选池V1命中"] = yes_no(row["院校专业组代码OCR规范化"] in candidate_codes)
        row["样本学校命中"] = yes_no(row["院校代码"] in sample_school_codes)
        row["专业计划数OCR数字候选"] = first_number(row["专业计划数OCR候选"])
        row["学费OCR数字候选"] = first_number(row["学费OCR候选"])
        row["专业计划数是否纯数字"] = yes_no(is_plain_number(row["专业计划数OCR候选"]))
        row["学费是否纯数字"] = yes_no(is_plain_number(row["学费OCR候选"]))
        row["字段完整性标记"] = field_flags(
            subject=row["再选科目OCR候选"],
            plan_count=row["专业计划数OCR候选"],
            tuition=row["学费OCR候选"],
            confidence=row["OCR置信度"],
            tags=tags,
        )

    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    group_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组标题OCR原文",
        "来源页码",
        "版面列",
        "专业组标题行号",
        "专业组标题y",
        "OCR专业行数",
        "再选科目OCR候选",
        "人数OCR候选",
        "学费OCR候选",
        "偏好和风险标签",
        "字段完整性标记",
        "候选池V1命中",
        "样本学校命中",
        "核验状态",
        "备注",
    ]
    with GROUP_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=group_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(group_rows)

    major_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组标题OCR原文",
        "来源页码",
        "版面列",
        "专业组标题行号",
        "专业组标题y",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业起始行号",
        "专业起始y",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "专业计划数OCR数字候选",
        "专业计划数是否纯数字",
        "学费OCR候选",
        "学费OCR数字候选",
        "学费是否纯数字",
        "OCR置信度",
        "偏好和风险标签",
        "字段完整性标记",
        "候选池V1命中",
        "样本学校命中",
        "核验状态",
    ]
    with MAJOR_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=major_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(major_rows)

    groups_by_school = defaultdict(list)
    majors_by_school = defaultdict(list)
    for row in group_rows:
        groups_by_school[row["院校代码"]].append(row)
    for row in major_rows:
        majors_by_school[row["院校代码"]].append(row)

    school_rows = []
    for code, groups in sorted(groups_by_school.items()):
        tags = sorted({tag for row in groups for tag in row["偏好和风险标签"].split(";") if tag})
        school_rows.append({
            "来源期号": "《湖北招生考试》2026年第19期",
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "full_ocr_draft",
            "最终可用": "false",
            "院校代码": code,
            "院校名称OCR": canonical_names.get(code, ""),
            "OCR专业组数": len(groups),
            "OCR专业行数": len(majors_by_school.get(code, [])),
            "PDF OCR页码": "；".join(str(page) for page in sorted({int(row["来源页码"]) for row in groups})),
            "偏好和风险标签": "；".join(tags),
            "候选池V1命中": yes_no(any(row["候选池V1命中"] == "是" for row in groups)),
            "样本学校命中": yes_no(code in sample_school_codes),
            "核验状态": "needs_manual_pdf_review",
        })
    with SCHOOL_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(school_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(school_rows)

    full_group_codes = {row["院校专业组代码OCR规范化"] for row in group_rows}
    full_school_codes = set(groups_by_school)

    group_by_code = {row["院校专业组代码OCR规范化"]: row for row in group_rows}
    candidate_coverage_rows = []
    for row in candidate_pool_rows():
        group_code = row.get("候选专业组代码OCR规范化", "")
        matched = group_by_code.get(group_code)
        candidate_coverage_rows.append({
            "候选池学校专业组": row.get("学校/专业组", ""),
            "城市": row.get("城市", ""),
            "年份覆盖": row.get("年份覆盖", ""),
            "2023最低分": row.get("2023最低分", ""),
            "2024最低分": row.get("2024最低分", ""),
            "2025最低分": row.get("2025最低分", ""),
            "历史风险初判": row.get("风险初判", ""),
            "候选专业组代码OCR规范化": group_code,
            "第19期全量OCR命中": yes_no(matched is not None),
            "第19期OCR院校名称": matched.get("院校名称OCR", "") if matched else "",
            "第19期OCR页码": matched.get("来源页码", "") if matched else "",
            "第19期OCR专业行数": matched.get("OCR专业行数", "") if matched else "",
            "第19期OCR风险标签": matched.get("偏好和风险标签", "") if matched else "",
            "当前状态": "needs_manual_pdf_review" if matched else "needs_original_page_or_code_change_review",
            "下一步": "回看第19期原PDF页，核组边界和组内全部专业" if matched else "核对2026是否组号变化、OCR漏识别或该历史组已调整",
        })
    if candidate_coverage_rows:
        with CANDIDATE_COVERAGE_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(candidate_coverage_rows[0].keys()), lineterminator="\n")
            writer.writeheader()
            writer.writerows(candidate_coverage_rows)

    tag_counts = Counter(
        tag
        for row in group_rows
        for tag in row["偏好和风险标签"].split(";")
        if tag
    )
    groups_without_majors = [row["院校专业组代码OCR规范化"] for row in group_rows if int(row["OCR专业行数"]) == 0]
    major_field_counts = {
        "有再选科目候选专业行数": sum(bool(row["再选科目OCR候选"]) for row in major_rows),
        "有专业计划数候选专业行数": sum(bool(row["专业计划数OCR候选"]) for row in major_rows),
        "专业计划数纯数字专业行数": sum(row["专业计划数是否纯数字"] == "是" for row in major_rows),
        "有学费候选专业行数": sum(bool(row["学费OCR候选"]) for row in major_rows),
        "学费纯数字专业行数": sum(row["学费是否纯数字"] == "是" for row in major_rows),
        "最终可用true专业行数": sum(row["最终可用"] == "true" for row in major_rows),
    }

    summary = {
        "status": "full_ocr_draft_needs_manual_pdf_review",
        "scope": "湖北省 2026 本科普通批首选物理在鄂招生计划；包括省内外院校在湖北招生专业组，不等同于只看湖北省内高校。",
        "source_issue": "《湖北招生考试》2026 年第 19 期·本科普通批首选物理",
        "source_pdf_sha256": source_pdf_sha256,
        "page_range_used": [PLAN_PAGE_START, PLAN_PAGE_END],
        "public_detail_files": [
            str(SCHOOL_OUTPUT.relative_to(ROOT)),
            str(GROUP_OUTPUT.relative_to(ROOT)),
            str(MAJOR_OUTPUT.relative_to(ROOT)),
            str(CANDIDATE_COVERAGE_OUTPUT.relative_to(ROOT)),
        ],
        "public_data_policy": "招生明细 CSV 已公开；原始 PDF、渲染图片、OCR 行级源文件和本地路径不提交。所有明细仍为 OCR 初稿，必须人工复核。",
        "counts": {
            "OCR院校数": len(groups_by_school),
            "OCR院校专业组数": len(group_rows),
            "OCR专业行数": len(major_rows),
            "无专业行专业组数": len(groups_without_majors),
        },
        "major_field_completeness": major_field_counts,
        "candidate_pool_v1_coverage": {
            "候选专业组数": len(candidate_codes),
            "全量OCR命中候选专业组数": len(candidate_codes & full_group_codes),
            "未命中候选专业组数": len(candidate_codes - full_group_codes),
            "未命中候选专业组": sorted(candidate_codes - full_group_codes),
        },
        "sample_school_coverage": {
            "样本院校代码数": len(sample_school_codes),
            "全量OCR命中样本院校数": len(sample_school_codes & full_school_codes),
            "未命中样本院校代码": sorted(sample_school_codes - full_school_codes),
        },
        "risk_and_preference_tag_counts": dict(sorted(tag_counts.items())),
        "quality_gates": [
            "本表是 OCR 自动切组初稿，不能直接作为最终志愿表。",
            "所有专业组须回看第 19 期原 PDF 页确认组边界和组内全部专业。",
            "院校代码、专业组代码、专业代号、计划数、学费、选科和备注必须逐字段核验。",
            "超过 15000 元/年、中外合作、医学护理、体检限制、语种单科、专项预科等风险标签必须优先人工复核。",
            "进入最终志愿表前，必须与湖北官方计划或志愿系统、高校官网/招生章程交叉核验。",
        ],
        "notes": [
            "全量底座先用于搜索、筛选、定位和生成复核任务。",
            "省外高校只要在湖北招生，也属于本底座范围。",
            "如后续官方系统与第 19 期存在调整，以官方系统公告和志愿填报系统为准。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出公开院校汇总：{SCHOOL_OUTPUT}")
    print(f"写出公开专业组汇总：{GROUP_OUTPUT}")
    print(f"写出公开专业清单：{MAJOR_OUTPUT}")
    print(f"写出公开候选池命中表：{CANDIDATE_COVERAGE_OUTPUT}")
    print(f"写出公开摘要：{SUMMARY_OUTPUT}")
    print(f"院校数：{len(groups_by_school)}")
    print(f"专业组数：{len(group_rows)}")
    print(f"专业行数：{len(major_rows)}")
    print(f"候选池命中：{len(candidate_codes & full_group_codes)}/{len(candidate_codes)}")


if __name__ == "__main__":
    main()
