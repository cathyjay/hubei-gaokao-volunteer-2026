#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MAJOR_QUALITY = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
OCR_LINES = ROOT / "private/ocr-runs/issue19-full-120dpi/ocr-lines.csv"

OUTPUT = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors-summary.json"
PRIVATE_OUTPUT = ROOT / "private/derived/issue19-major-line-evidence-windows/major-line-ocr-window-evidence.jsonl"

DATA_STAGE = "issue19_major_line_pdf_evidence_anchors"


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


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def as_float(value):
    try:
        return float(str(value or "").strip())
    except ValueError:
        return 0.0


def short_text(value, limit=80):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def normalize_code(value):
    return (
        str(value or "")
        .upper()
        .replace("Ｏ", "0")
        .replace("O", "0")
        .replace("Ｉ", "1")
        .replace("I", "1")
        .replace("Ｌ", "1")
        .replace("L", "1")
        .replace("/", "")
        .replace(" ", "")
    )


def page_band_key(row):
    return (str(row.get("来源页码") or row.get("page") or ""), str(row.get("版面列") or row.get("table_band") or ""))


def line_sort_key(row):
    return (-as_float(row.get("y")), as_float(row.get("x")), as_int(row.get("line_no")))


def line_public_fingerprint(line):
    if not line:
        return ""
    material = "|".join([
        str(line.get("page", "")),
        str(line.get("table_band", "")),
        str(line.get("line_no", "")),
        str(line.get("text", "")),
        str(line.get("x", "")),
        str(line.get("y", "")),
    ])
    return sha256_text(material)


def line_private_payload(line):
    return {
        "line_no": as_int(line.get("line_no")),
        "text": line.get("text", ""),
        "confidence": line.get("confidence", ""),
        "x": line.get("x", ""),
        "y": line.get("y", ""),
        "width": line.get("width", ""),
        "height": line.get("height", ""),
        "table_band": line.get("table_band", ""),
        "line_type": line.get("line_type", ""),
    }


def confidence_stats(lines):
    values = [as_float(line.get("confidence")) for line in lines if line.get("confidence") != ""]
    if not values:
        return "", ""
    return f"{sum(values) / len(values):.4f}", f"{min(values):.4f}"


def bbox_summary(lines):
    if not lines:
        return ""
    xs = [as_float(line.get("x")) for line in lines]
    ys = [as_float(line.get("y")) for line in lines]
    rights = [as_float(line.get("x")) + as_float(line.get("width")) for line in lines]
    bottoms = [as_float(line.get("y")) - as_float(line.get("height")) for line in lines]
    return (
        f"x={min(xs):.6f}-{max(rights):.6f};"
        f"y={max(ys):.6f}-{min(bottoms):.6f}"
    )


def line_no_range(lines):
    if not lines:
        return ""
    line_numbers = [as_int(line.get("line_no")) for line in lines]
    return f"{min(line_numbers)}-{max(line_numbers)}"


def text_sha(lines):
    material = "\n".join(
        f"{line.get('line_no')}|{line.get('text')}|{line.get('confidence')}|{line.get('x')}|{line.get('y')}"
        for line in lines
    )
    return sha256_text(material)


def build_indexes():
    major_rows = read_csv(MAJOR_QUALITY)
    manifest_rows = read_csv(PAGE_MANIFEST)
    ocr_rows = read_csv(OCR_LINES)

    lines_by_page_band = defaultdict(list)
    lines_by_page_band_no = {}
    for line in ocr_rows:
        key = page_band_key(line)
        lines_by_page_band[key].append(line)
        lines_by_page_band_no[(line.get("page", ""), line.get("table_band", ""), line.get("line_no", ""))] = line

    for lines in lines_by_page_band.values():
        lines.sort(key=line_sort_key)

    majors_by_page_band = defaultdict(list)
    for row in major_rows:
        majors_by_page_band[page_band_key(row)].append(row)

    for rows in majors_by_page_band.values():
        rows.sort(key=lambda row: (-as_float(row.get("专业起始y")), as_int(row.get("专业起始行号"))))

    group_title_y_by_page_band = defaultdict(list)
    for row in major_rows:
        key = page_band_key(row)
        value = as_float(row.get("专业组标题y"))
        if value:
            group_title_y_by_page_band[key].append(value)
    for key in list(group_title_y_by_page_band):
        group_title_y_by_page_band[key] = sorted(set(group_title_y_by_page_band[key]), reverse=True)

    return {
        "major_rows": major_rows,
        "manifest_by_page": {row.get("PDF页码", ""): row for row in manifest_rows},
        "lines_by_page_band": lines_by_page_band,
        "lines_by_page_band_no": lines_by_page_band_no,
        "majors_by_page_band": majors_by_page_band,
        "group_title_y_by_page_band": group_title_y_by_page_band,
    }


def next_boundary_y(row, majors_same_band, group_title_ys):
    start_y = as_float(row.get("专业起始y"))
    next_major_ys = [
        as_float(item.get("专业起始y"))
        for item in majors_same_band
        if as_float(item.get("专业起始y")) < start_y - 0.000001
    ]
    next_group_ys = [value for value in group_title_ys if value < start_y - 0.000001]
    candidates = []
    if next_major_ys:
        candidates.append(max(next_major_ys))
    if next_group_ys:
        candidates.append(max(next_group_ys))
    if candidates:
        return max(candidates) + 0.004
    return max(start_y - 0.080, 0.0)


def y_window_lines(row, lines, majors_same_band, group_title_ys):
    start_y = as_float(row.get("专业起始y"))
    upper_y = start_y + 0.004
    lower_y = next_boundary_y(row, majors_same_band, group_title_ys)
    return [
        line for line in lines
        if lower_y < as_float(line.get("y")) <= upper_y
    ], lower_y, upper_y


def group_context_lines(row, lines):
    group_y = as_float(row.get("专业组标题y"))
    if not group_y:
        return []
    return [
        line for line in lines
        if abs(as_float(line.get("y")) - group_y) <= 0.003
    ]


def start_line_status(row, lines_by_page_band_no):
    key = (row.get("来源页码", ""), row.get("版面列", ""), row.get("专业起始行号", ""))
    line = lines_by_page_band_no.get(key)
    if not line:
        return None, "missing_start_line", "false"
    start_text = normalize_code(line.get("text", ""))[:8]
    major_code = normalize_code(row.get("专业代号OCR", ""))
    code_match = "true" if major_code and major_code in start_text else "false"
    return line, "exact_start_line_hit", code_match


def evidence_status(start_status, window_lines, group_lines):
    if start_status != "exact_start_line_hit":
        return "P0-起始OCR行未回连"
    if not window_lines:
        return "P0-专业窗口为空"
    if not group_lines:
        return "P1-缺少组标题上下文"
    return "P2-已生成专业行级OCR证据锚点"


def build_rows_and_private_payloads():
    indexes = build_indexes()
    public_rows = []
    private_payloads = []

    for row in indexes["major_rows"]:
        key = page_band_key(row)
        lines = indexes["lines_by_page_band"].get(key, [])
        majors_same_band = indexes["majors_by_page_band"].get(key, [])
        group_title_ys = indexes["group_title_y_by_page_band"].get(key, [])
        major_lines, lower_y, upper_y = y_window_lines(row, lines, majors_same_band, group_title_ys)
        group_lines = group_context_lines(row, lines)
        start_line, start_status, code_match = start_line_status(row, indexes["lines_by_page_band_no"])
        combined_lines = sorted(group_lines + major_lines, key=lambda line: as_int(line.get("line_no")))
        avg_conf, min_conf = confidence_stats(combined_lines)
        manifest = indexes["manifest_by_page"].get(row.get("来源页码", ""), {})
        evidence_id = stable_id("PDFANCHOR", [row.get("专业行ID", ""), row.get("专业起始行号", "")])
        status = evidence_status(start_status, major_lines, group_lines)

        public_rows.append({
            "专业行原页证据锚点ID": evidence_id,
            "来源逐专业质量工作台": "data/working/issue19-full-major-detail-quality-workbench.csv",
            "来源私有OCR行级CSV": "private_ocr_lines_not_public",
            "来源期号": row.get("来源期号", ""),
            "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "证据锚点状态": status,
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "专业组内专业序号": row.get("专业组内专业序号", ""),
            "专业代号OCR": row.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": short_text(row.get("专业名称及备注OCR")),
            "专业组标题行号": row.get("专业组标题行号", ""),
            "专业组标题y": row.get("专业组标题y", ""),
            "专业起始行号": row.get("专业起始行号", ""),
            "专业起始y": row.get("专业起始y", ""),
            "OCR窗口y上界": f"{upper_y:.6f}",
            "OCR窗口y下界": f"{lower_y:.6f}",
            "组标题上下文行号范围": line_no_range(group_lines),
            "专业窗口行号范围": line_no_range(major_lines),
            "合并证据窗口行号范围": line_no_range(combined_lines),
            "组标题上下文行数": str(len(group_lines)),
            "专业窗口行数": str(len(major_lines)),
            "合并证据窗口行数": str(len(combined_lines)),
            "窗口平均置信度": avg_conf,
            "窗口最低置信度": min_conf,
            "窗口坐标摘要": bbox_summary(combined_lines),
            "窗口文本SHA256": text_sha(combined_lines) if combined_lines else "",
            "起始行回连状态": start_status,
            "起始行文本SHA256": line_public_fingerprint(start_line),
            "起始行专业代号匹配": code_match,
            "私有页图证据编号": manifest.get("私有页图证据编号", ""),
            "私有页图SHA256": manifest.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": manifest.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": manifest.get("私有OCR文本SHA256", ""),
            "私有窗口证据编号": evidence_id,
            "公开安全策略": "公开表只保留锚点、坐标摘要和哈希；OCR窗口原文仅留在private目录，不提交公开仓库。",
            "下一步": "按本锚点回看 PDF 原页或私有 OCR 窗口，再与湖北官方系统/省招办计划和高校官网/章程交叉确认；确认前不得作为最终志愿事实。",
        })

        private_payloads.append({
            "evidence_id": evidence_id,
            "major_line_id": row.get("专业行ID", ""),
            "source_page": as_int(row.get("来源页码")),
            "table_band": row.get("版面列", ""),
            "school_code": row.get("院校代码", ""),
            "school_name_ocr": row.get("院校名称OCR", ""),
            "group_code_ocr_normalized": row.get("院校专业组代码OCR规范化", ""),
            "major_code_ocr": row.get("专业代号OCR", ""),
            "major_name_ocr": row.get("专业名称及备注OCR", ""),
            "group_context_lines": [line_private_payload(line) for line in group_lines],
            "major_window_lines": [line_private_payload(line) for line in major_lines],
            "combined_window_sha256": public_rows[-1]["窗口文本SHA256"],
            "public_anchor_status": status,
        })

    public_rows.sort(key=lambda item: (
        as_int(item["来源页码"]),
        0 if item["版面列"] == "left" else 1,
        as_int(item["专业起始行号"]),
        item["专业行ID"],
    ))
    return public_rows, private_payloads


def write_private_payloads(payloads):
    PRIVATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with PRIVATE_OUTPUT.open("w", encoding="utf-8") as f:
        for payload in payloads:
            f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def write_summary(rows):
    status_counts = Counter(row["证据锚点状态"] for row in rows)
    summary = {
        "status": "issue19_major_line_pdf_evidence_anchors_not_final",
        "generated_by": "build_issue19_major_line_pdf_evidence_anchors.py",
        "source_major_quality_workbench": "data/working/issue19-full-major-detail-quality-workbench.csv",
        "source_page_manifest": "data/working/issue19-page-manifest.csv",
        "source_private_ocr_lines": "private_ocr_lines_not_public",
        "output_table": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "private_output_policy": "private_jsonl_not_committed_public_repository",
        "row_count": len(rows),
        "unique_anchor_id_count": len({row["专业行原页证据锚点ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "status_counts": dict(status_counts),
        "exact_start_line_hit_count": sum(row["起始行回连状态"] == "exact_start_line_hit" for row in rows),
        "start_line_major_code_match_count": sum(row["起始行专业代号匹配"] == "true" for row in rows),
        "non_empty_window_count": sum(as_int(row["合并证据窗口行数"]) > 0 for row in rows),
        "window_sha_non_empty_count": sum(bool(row["窗口文本SHA256"]) for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "notes": [
            "本表只把每条招生专业明细锚定到私有 OCR 行级窗口，不能替代 PDF 原页人工核验。",
            "公开表不保存 OCR 窗口原文和本机绝对路径，只保存坐标摘要、行号范围和哈希。",
            "私有 JSONL 可用于人工回看，但不提交 public GitHub。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


FIELDS = [
    "专业行原页证据锚点ID",
    "来源逐专业质量工作台",
    "来源私有OCR行级CSV",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "证据锚点状态",
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
    "专业组标题行号",
    "专业组标题y",
    "专业起始行号",
    "专业起始y",
    "OCR窗口y上界",
    "OCR窗口y下界",
    "组标题上下文行号范围",
    "专业窗口行号范围",
    "合并证据窗口行号范围",
    "组标题上下文行数",
    "专业窗口行数",
    "合并证据窗口行数",
    "窗口平均置信度",
    "窗口最低置信度",
    "窗口坐标摘要",
    "窗口文本SHA256",
    "起始行回连状态",
    "起始行文本SHA256",
    "起始行专业代号匹配",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "私有窗口证据编号",
    "公开安全策略",
    "下一步",
]


def main():
    rows, private_payloads = build_rows_and_private_payloads()
    write_csv(OUTPUT, rows, FIELDS)
    write_private_payloads(private_payloads)
    write_summary(rows)
    print(f"写出专业行原页证据锚点表：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print("写出私有 OCR 窗口 JSONL：private/derived/issue19-major-line-evidence-windows/major-line-ocr-window-evidence.jsonl")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
