#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

P0_REREAD_WORKLIST = ROOT / "data/working/issue19-field-fact-p0-reread-worklist.csv"
PRIVATE_WINDOW_JSONL = (
    ROOT
    / "private"
    / "derived"
    / "issue19-major-line-evidence-windows"
    / "major-line-ocr-window-evidence.jsonl"
)

OUTPUT = ROOT / "data/working/issue19-field-fact-p0-reread-machine-candidates.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-fact-p0-reread-machine-candidates-summary.json"

DATA_STAGE = "issue19_field_fact_p0_reread_machine_candidates"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"


FIELDS = [
    "P0字段机器候选任务ID",
    "来源P0字段原页重读任务ID",
    "来源P0字段原页重读工作清单",
    "来源私有OCR窗口JSONL",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动回填候选",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "机器候选状态",
    "机器候选置信等级",
    "机器候选规则ID",
    "机器候选字段值",
    "机器候选值集合",
    "机器候选去重值数",
    "机器候选原始命中数",
    "候选证据行号集合",
    "候选证据x集合",
    "候选证据y集合",
    "候选证据置信度集合",
    "候选证据来源范围",
    "来源字段事实核验任务ID",
    "专业行ID",
    "字段事实闭环ID",
    "专业组出现ID",
    "院校代码",
    "来源页码",
    "版面列",
    "字段名",
    "字段事实状态",
    "页级保真队列ID",
    "原始专业行源证据审计ID",
    "专业行原页证据锚点ID",
    "窗口文本SHA256",
    "私有窗口证据编号",
    "机器候选说明",
    "不得进入原因",
    "下一步",
]


SUBJECT_MAP = {
    "不限": "不限",
    "化学": "化学",
    "生物": "生物",
    "地理": "地理",
    "政治": "政治",
    "思想政治": "政治",
}


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value, default=0):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return default


def as_float(value, default=0.0):
    try:
        return float(str(value or "").strip())
    except ValueError:
        return default


def normalize_digits(value):
    return "".join(re.findall(r"\d+", str(value or "")))


def normalize_subject(value):
    text = re.sub(r"[\s\[\]【】（）()「」『』；:：、,，。·/|\\-]", "", str(value or ""))
    return SUBJECT_MAP.get(text, "")


def load_windows(path):
    windows = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            major_id = item.get("major_line_id", "")
            if major_id:
                windows[major_id] = item
    return windows


def value_list(items):
    values = []
    for item in items:
        value = item["value"]
        if value not in values:
            values.append(value)
    return values


def join_values(values):
    return "；".join(str(value) for value in values if str(value) != "")


def candidate_status(values, raw_count):
    if not values:
        return "P0C0-未找到坐标候选仍需人工原页重读", "none"
    if len(values) == 1:
        if raw_count == 1:
            return "P0C1-单一坐标候选待人工核验", "medium"
        return "P0C1-重复同值坐标候选待人工核验", "medium"
    return "P0C2-多值坐标候选冲突待人工核页", "low"


def coordinate_rule(field_name, table_band):
    if field_name == "专业计划数":
        if table_band == "right":
            return "R_PLAN_RIGHT_X_0.82_0.875_LEN_1_3"
        return "R_PLAN_LEFT_X_0.39_0.455_LEN_1_3"
    if field_name == "学费":
        if table_band == "right":
            return "R_TUITION_RIGHT_X_0.84_0.91_LEN_4_6"
        return "R_TUITION_LEFT_X_0.43_0.50_LEN_4_6"
    if field_name == "再选科目":
        return "R_RESELECT_GROUP_CONTEXT_EXACT_SUBJECT"
    return "R_UNKNOWN_FIELD"


def numeric_candidates(window, field_name, table_band):
    matches = []
    for line in window.get("major_window_lines", []):
        value = normalize_digits(line.get("text", ""))
        if not value:
            continue
        x = as_float(line.get("x"))
        if field_name == "专业计划数":
            in_column = 0.82 <= x <= 0.875 if table_band == "right" else 0.39 <= x <= 0.455
            valid_length = len(value) <= 3
        elif field_name == "学费":
            in_column = 0.84 <= x <= 0.91 if table_band == "right" else 0.43 <= x <= 0.50
            valid_length = 4 <= len(value) <= 6
        else:
            in_column = False
            valid_length = False
        if in_column and valid_length:
            matches.append({
                "value": value,
                "line_no": str(as_int(line.get("line_no"))),
                "x": f"{as_float(line.get('x')):.6f}",
                "y": f"{as_float(line.get('y')):.6f}",
                "confidence": str(line.get("confidence", "")),
                "source_range": "major_window_lines",
            })
    return matches


def subject_candidates(window):
    matches = []
    for line in window.get("group_context_lines", []):
        value = normalize_subject(line.get("text", ""))
        if value:
            matches.append({
                "value": value,
                "line_no": str(as_int(line.get("line_no"))),
                "x": f"{as_float(line.get('x')):.6f}",
                "y": f"{as_float(line.get('y')):.6f}",
                "confidence": str(line.get("confidence", "")),
                "source_range": "group_context_lines",
            })
    return matches


def machine_candidates(row, window):
    field_name = row.get("字段名", "")
    table_band = row.get("版面列", "")
    if not window:
        return []
    if field_name in {"专业计划数", "学费"}:
        return numeric_candidates(window, field_name, table_band)
    if field_name == "再选科目":
        return subject_candidates(window)
    return []


def build_rows():
    reread_rows = read_csv(P0_REREAD_WORKLIST)
    windows = load_windows(PRIVATE_WINDOW_JSONL)
    rows = []
    for source in reread_rows:
        window = windows.get(source.get("专业行ID", ""), {})
        candidates = machine_candidates(source, window)
        values = value_list(candidates)
        status, confidence = candidate_status(values, len(candidates))
        rule_id = coordinate_rule(source.get("字段名", ""), source.get("版面列", ""))
        candidate_value = values[0] if len(values) == 1 else ""
        row = {
            "P0字段机器候选任务ID": stable_id(
                "P0COORDCAND",
                [
                    source.get("P0字段原页重读任务ID", ""),
                    source.get("专业行ID", ""),
                    source.get("字段名", ""),
                    SOURCE_PDF_SHA256,
                ],
            ),
            "来源P0字段原页重读任务ID": source.get("P0字段原页重读任务ID", ""),
            "来源P0字段原页重读工作清单": "data/working/issue19-field-fact-p0-reread-worklist.csv",
            "来源私有OCR窗口JSONL": "private_ocr_window_jsonl_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×K0字段×机器坐标候选",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "机器候选状态": status,
            "机器候选置信等级": confidence,
            "机器候选规则ID": rule_id,
            "机器候选字段值": candidate_value,
            "机器候选值集合": join_values(values),
            "机器候选去重值数": str(len(values)),
            "机器候选原始命中数": str(len(candidates)),
            "候选证据行号集合": join_values(item["line_no"] for item in candidates),
            "候选证据x集合": join_values(item["x"] for item in candidates),
            "候选证据y集合": join_values(item["y"] for item in candidates),
            "候选证据置信度集合": join_values(item["confidence"] for item in candidates),
            "候选证据来源范围": join_values(sorted({item["source_range"] for item in candidates})),
            "机器候选说明": (
                "仅按专业行窗口坐标和字段类型抽取机器候选；公开输出不保存 OCR 原文，"
                "候选值必须回看 PDF 原页并用湖北官方系统或省招办计划确认。"
            ),
            "不得进入原因": (
                "本表只是 K0 字段的机器坐标候选层；没有人工核页、湖北官方系统或省招办计划、"
                "高校官网/章程闭环前，不得写回字段、回填候选、推荐学校专业或进入志愿排序。"
            ),
            "下一步": (
                "若存在单一候选，按证据行号和坐标回看 PDF 原页；若无候选或多值冲突，"
                "继续人工重读原页或更高分辨率 OCR。全部结果再进入 K1 候选回看和湖北官方字段核验。"
            ),
        }
        for field in [
            "来源字段事实核验任务ID",
            "专业行ID",
            "字段事实闭环ID",
            "专业组出现ID",
            "院校代码",
            "来源页码",
            "版面列",
            "字段名",
            "字段事实状态",
            "页级保真队列ID",
            "原始专业行源证据审计ID",
            "专业行原页证据锚点ID",
            "窗口文本SHA256",
            "私有窗口证据编号",
        ]:
            row[field] = source.get(field, "")
        rows.append(row)

    rows.sort(key=lambda row: (
        0 if row.get("机器候选状态") == "P0C1-单一坐标候选待人工核验" else 1,
        as_int(row.get("来源页码")),
        row.get("院校代码", ""),
        row.get("专业组出现ID", ""),
        row.get("专业行ID", ""),
        {"专业计划数": 1, "再选科目": 2, "学费": 3}.get(row.get("字段名"), 9),
        row.get("来源P0字段原页重读任务ID", ""),
    ))
    return rows


def top_counts(counter, limit=30):
    return dict(counter.most_common(limit))


def write_summary(rows):
    status_counts = Counter(row["机器候选状态"] for row in rows)
    non_empty_rows = [row for row in rows if row["机器候选字段值"]]
    summary = {
        "status": "issue19_field_fact_p0_reread_machine_candidates_not_final",
        "generated_by": "build_issue19_field_fact_p0_reread_machine_candidates.py",
        "source_p0_reread_worklist": "data/working/issue19-field-fact-p0-reread-worklist.csv",
        "source_private_window_jsonl": "private_ocr_window_jsonl_not_public",
        "output_table": "data/working/issue19-field-fact-p0-reread-machine-candidates.csv",
        "row_grain": "逐专业招生明细×K0字段×机器坐标候选",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_candidate_task_id_count": len({row["P0字段机器候选任务ID"] for row in rows}),
        "unique_source_p0_reread_task_id_count": len({row["来源P0字段原页重读任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_school_code_count": len({row["院校代码"] for row in rows}),
        "field_counts": dict(Counter(row["字段名"] for row in rows)),
        "candidate_status_counts": dict(status_counts),
        "candidate_confidence_counts": dict(Counter(row["机器候选置信等级"] for row in rows)),
        "candidate_rule_counts": dict(Counter(row["机器候选规则ID"] for row in rows)),
        "field_candidate_value_counts": {
            field: sum(bool(row["机器候选字段值"]) for row in rows if row["字段名"] == field)
            for field in ["专业计划数", "再选科目", "学费"]
        },
        "non_empty_candidate_value_count": len(non_empty_rows),
        "single_candidate_count": status_counts.get("P0C1-单一坐标候选待人工核验", 0),
        "duplicate_same_value_candidate_count": status_counts.get("P0C1-重复同值坐标候选待人工核验", 0),
        "multi_value_conflict_count": status_counts.get("P0C2-多值坐标候选冲突待人工核页", 0),
        "no_coordinate_candidate_count": status_counts.get("P0C0-未找到坐标候选仍需人工原页重读", 0),
        "page_candidate_value_count_top30": top_counts(Counter(row["来源页码"] for row in non_empty_rows)),
        "school_code_candidate_value_count_top30": top_counts(Counter(row["院校代码"] for row in non_empty_rows)),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row["机器是否允许自动写回主表"] == "true" for row in rows),
        "auto_candidate_fill_allowed_count": sum(row["机器是否允许自动回填候选"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "public_safety_note": "本产物只保存机器候选值、坐标摘要、必要来源ID、页码/版面列、字段名、证据编号、哈希和非最终门禁；不保存私有OCR窗口原文、院校名、专业名、专业代号、专业组代码、图片路径、登录态或个人身份信息。",
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    write_summary(rows)
    print(f"写出P0字段机器候选表：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
