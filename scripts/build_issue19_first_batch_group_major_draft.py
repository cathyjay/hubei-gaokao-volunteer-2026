#!/usr/bin/env python3
import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OCR_LINES = ROOT / "private/ocr-runs/issue19-full-120dpi/ocr-lines.csv"
DEFAULT_PRIVATE_DIR = ROOT / "private/derived/issue19-first-batch-structure-trial"
DEFAULT_MAJOR_OUTPUT = DEFAULT_PRIVATE_DIR / "院校专业组专业清单OCR初稿.csv"
DEFAULT_GROUP_OUTPUT = DEFAULT_PRIVATE_DIR / "院校专业组汇总OCR初稿.csv"
DEFAULT_SUMMARY = ROOT / "data/working/issue19-first-batch-group-major-draft-summary.json"

SCHOOLS = {
    "C102": "武汉科技大学",
    "C103": "湖北大学",
    "C138": "湖北理工学院",
    "C150": "武汉商学院",
}

RISK_KEYWORDS = {
    "rejected_medical": [
        "临床医学",
        "口腔医学",
        "预防医学",
        "中医学",
        "中医",
        "中药",
        "针灸",
        "推拿",
        "护理",
        "护理学",
        "助产",
        "药学",
        "药物",
        "药事",
        "制药",
        "生物制药",
        "医学",
        "医师",
        "医药",
        "医疗",
        "医用",
        "医工",
        "康复",
        "治疗",
        "麻醉",
        "影像",
        "卫生检验",
        "医学检验",
        "检验与检疫",
        "公共卫生",
        "卫生管理",
        "食品卫生与营养学",
        "健康服务与管理",
        "医事",
        "医养",
        "照护",
        "养老服务管理",
        "智慧健康养老管理",
        "眼视光",
        "动物医学",
        "动物药学",
        "兽医",
    ],
    "high_fee_or_coop": ["中外合作", "合作办学", "高收费"],
    "body_or_exam_limit": ["色盲", "色弱", "单色识别", "不予录取", "体检"],
    "language_or_single_subject": ["英语语种", "外语语种", "单科"],
}

PREFERENCE_KEYWORDS = {
    "priority_1_digital_media": ["数字媒体技术"],
    "priority_2_computer": ["计算机", "软件工程", "网络工程", "数据科学", "大数据", "人工智能", "物联网", "信息安全", "密码科学", "智能科学"],
    "priority_3_teacher": ["师范", "小学教育", "教育技术", "学前教育", "科学教育", "英语"],
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
    cleaned = (
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
    return cleaned


def parse_group_title(text):
    if "第" not in text or "组" not in text:
        return None
    normalized = normalize_code_text(text)
    match = re.search(r"C(\d{3})(\d{2})", normalized)
    if not match:
        return None
    school_code = f"C{match.group(1)}"
    if school_code not in SCHOOLS:
        return None
    group_no = match.group(2)
    return {
        "院校代码": school_code,
        "院校名称": SCHOOLS[school_code],
        "院校专业组代码OCR规范化": f"{school_code}{group_no}",
        "专业组号OCR": group_no,
    }


def is_any_group_title(row):
    text = row.get("text", "")
    if "第" not in text or "组" not in text:
        return False
    normalized = normalize_code_text(text)
    return bool(re.search(r"C\d{3}\d{2}", normalized))


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
    return match.group(1) if match else ""


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
    return ";".join(tags)


def build_major_rows(group, span_rows):
    majors = []
    current = None
    current_lines = []

    name_rows = [row for row in span_rows if is_name_zone(row)]
    for row in name_rows:
        text = row["text"].strip()
        if is_any_group_title(row):
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


def summarize_values(span_rows, zone):
    values = []
    for row in span_rows:
        if zone_for(row) != zone:
            continue
        text = row.get("text", "").strip()
        if text and text not in values:
            values.append(text)
    return "；".join(values)


def main():
    rows = read_rows(DEFAULT_OCR_LINES)
    for row in rows:
        row["版面列"] = layout_side(row)

    ordered_rows = sorted(rows, key=reading_key)
    all_group_indexes = [
        idx for idx, row in enumerate(ordered_rows)
        if is_any_group_title(row)
    ]

    first_batch_groups = []
    for idx in all_group_indexes:
        parsed = parse_group_title(ordered_rows[idx]["text"])
        if not parsed:
            continue
        first_batch_groups.append((idx, parsed))

    major_rows = []
    group_rows = []
    for position, (idx, parsed) in enumerate(first_batch_groups):
        next_idx = len(ordered_rows)
        later_group_indexes = [candidate for candidate in all_group_indexes if candidate > idx]
        if later_group_indexes:
            next_idx = later_group_indexes[0]

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

        tags = ";".join(sorted({tag for major in majors for tag in major["偏好和风险标签"].split(";") if tag}))
        group_rows.append({
            **group,
            "OCR专业行数": len(majors),
            "再选科目OCR候选": summarize_values(span_rows, "subject"),
            "人数OCR候选": summarize_values(span_rows, "count"),
            "学费OCR候选": summarize_values(span_rows, "tuition"),
            "偏好和风险标签": tags,
            "核验状态": "needs_manual_pdf_review",
            "备注": "OCR自动切组初稿；必须回看第19期原PDF页确认。",
        })

    DEFAULT_PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    major_fields = [
        "院校代码",
        "院校名称",
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
        "学费OCR候选",
        "OCR置信度",
        "偏好和风险标签",
        "核验状态",
    ]
    with DEFAULT_MAJOR_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=major_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(major_rows)

    group_fields = [
        "院校代码",
        "院校名称",
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
        "核验状态",
        "备注",
    ]
    with DEFAULT_GROUP_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=group_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(group_rows)

    school_summary = []
    by_school = defaultdict(list)
    for row in group_rows:
        by_school[row["院校名称"]].append(row)
    for school, groups in by_school.items():
        school_major_count = sum(int(row["OCR专业行数"]) for row in groups)
        tag_set = sorted({tag for row in groups for tag in row["偏好和风险标签"].split(";") if tag})
        school_summary.append({
            "学校名称": school,
            "院校代码": groups[0]["院校代码"],
            "OCR专业组数": len(groups),
            "OCR专业行数": school_major_count,
            "PDF OCR页码": sorted({int(row["来源页码"]) for row in groups}),
            "偏好和风险标签": tag_set,
            "状态": "ocr_group_major_draft_needs_manual_pdf_review",
        })

    summary = {
        "status": "ocr_group_major_draft_needs_manual_pdf_review",
        "schools": school_summary,
        "notes": [
            "公开摘要不含 OCR 原文、逐专业明细、原始文件路径或个人信息。",
            "本表由 OCR 行级数据自动切组，人数、学费、选科只作为候选，必须回看第19期原 PDF 页确认。",
            "完整专业组边界和组内全部专业均未人工复核，不得用于最终志愿。",
            "若高校官网或原 PDF 显示还有 OCR 未命中的专业组，应补录并标记来源。",
        ],
    }
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出私有专业组汇总：{DEFAULT_GROUP_OUTPUT}")
    print(f"写出私有专业清单：{DEFAULT_MAJOR_OUTPUT}")
    print(f"写出公开摘要：{DEFAULT_SUMMARY}")
    print(f"专业组数：{len(group_rows)}")
    print(f"专业行数：{len(major_rows)}")


if __name__ == "__main__":
    main()
