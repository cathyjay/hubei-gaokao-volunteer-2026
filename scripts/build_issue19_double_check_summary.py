#!/usr/bin/env python3
import csv
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OCR_SAMPLE = ROOT / "private/derived/issue19-sample-school-ocr/样本学校OCR定位.csv"
DEFAULT_OFFICIAL_SOURCES = ROOT / "data/working/issue19-sample-school-official-sources.csv"
DEFAULT_OUTPUT = ROOT / "data/working/issue19-high-priority-double-check-summary.csv"

HIGH_PRIORITY_SCHOOLS = [
    "武汉商学院",
    "武汉科技大学",
    "湖北理工学院",
    "湖北科技学院",
    "湖北工程学院",
    "荆楚理工学院",
    "湖北大学",
]

FIELD_RISK_NOTES = {
    "武汉商学院": "专业组覆盖需回看原页；官网可核计划数/学费/选科，但不含第19期专业组代码。",
    "武汉科技大学": "校名也出现在中外合作/毕业证备注中，命中行需区分专业组标题和备注误召。",
    "湖北理工学院": "院校代码与组代码中的 C/CI/I/1/0 易误识别，组号需逐项核原页。",
    "湖北科技学院": "医学相关专业可能有体检、色觉等限制，备注必须逐条人工核。",
    "湖北工程学院": "跨页专业组边界风险较高，官网页面主体为图片，需人工/图片 OCR 交叉核。",
    "荆楚理工学院": "相邻湖北理工学院同页，需防止上下文窗口混入相邻学校专业。",
    "湖北大学": "专业组数量多且备注复杂，不能仅凭窗口上下文推断完整组内专业。",
}

EVIDENCE_TIERS = {
    "武汉商学院": "第一批结构化试跑：字段补充源",
    "武汉科技大学": "第一批结构化试跑：主证据",
    "湖北理工学院": "第一批结构化试跑：主证据",
    "湖北科技学院": "第二批：官网 PDF 附件 OCR 后加入",
    "湖北工程学院": "补充证据：不能单独证明专业组边界",
    "荆楚理工学院": "补充证据：不能单独证明专业组边界",
    "湖北大学": "第一批结构化试跑：主证据",
}

STRUCTURE_TRIAL_NOTES = {
    "武汉商学院": "先核专业名称、湖北计划数、学费和选科；专业组代码和组边界必须回第19期。",
    "武汉科技大学": "先核 C10203-C10215 组代码、边界、组计划数和中外合作/专项备注。",
    "湖北理工学院": "先核 C13805-C13814 物理类组边界、人数、学费和体检/中外合作/面向黄石备注。",
    "湖北科技学院": "先补齐官网 PDF 附件 OCR，再核 C11606-C11616 和医学体检限制。",
    "湖北工程学院": "先作为专业名称、湖北计划数、学费、选考科目的补充核验源。",
    "荆楚理工学院": "先作为专业名称、湖北计划数、学费、类别的补充核验源。",
    "湖北大学": "先核 C10301-C10339 组代码、边界、学费和专项/中外合作/艺体类标签。",
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sorted_pages(rows):
    pages = sorted({int(row["OCR页码"]) for row in rows if row.get("OCR页码")})
    if not pages:
        return ""
    ranges = []
    start = prev = pages[0]
    for page in pages[1:]:
        if page == prev + 1:
            prev = page
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = page
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return "、".join(ranges)


def is_hit_row(row):
    return row.get("命中行号") and row.get("上下文行号") == row.get("命中行号")


def is_probable_remark_hit(row):
    text = row.get("OCR文本", "")
    if "第" in text and "组" in text:
        return False
    if "（公办）" in text or "(公办)" in text:
        return False
    return bool(text)


def summarize_school(name, ocr_rows, official_by_school):
    rows = [row for row in ocr_rows if row.get("学校名称") == name and row.get("OCR页码")]
    unique_rows = {(row["OCR页码"], row["上下文行号"]): row for row in rows}.values()
    hit_rows = [row for row in rows if is_hit_row(row)]
    confidences = [
        float(row["OCR置信度"])
        for row in unique_rows
        if row.get("OCR置信度")
    ]
    low_confidence = sum(1 for row in unique_rows if row.get("OCR置信度") and float(row["OCR置信度"]) < 0.5)
    middle_confidence = sum(1 for row in unique_rows if row.get("OCR置信度") and float(row["OCR置信度"]) == 0.5)
    school_line_count = sum(1 for row in unique_rows if row.get("行类型") == "school")
    major_line_count = sum(1 for row in unique_rows if row.get("行类型") == "major_or_numbered_line")
    probable_remark_hits = sum(1 for row in hit_rows if is_probable_remark_hit(row))

    official = official_by_school.get(name, {})
    local_paths = [p.strip() for p in official.get("本地留存路径", "").split("；") if p.strip()]
    existing_local_paths = [
        p for p in local_paths
        if (ROOT / p).exists() and (ROOT / p).stat().st_size > 1000
    ]

    return {
        "学校名称": name,
        "PDF OCR页码": sorted_pages(rows),
        "学校名命中行数": len(hit_rows),
        "上下文唯一行数": len(list(unique_rows)),
        "疑似备注误召命中数": probable_remark_hits,
        "专业组/学校行线索数": school_line_count,
        "疑似专业/编号行数": major_line_count,
        "低置信度行数": low_confidence,
        "中置信度行数": middle_confidence,
        "平均置信度": f"{statistics.mean(confidences):.3f}" if confidences else "",
        "官网来源优先级": official.get("官网来源优先级", ""),
        "官网是否可核湖北2026": official.get("是否可核湖北2026", ""),
        "官网可核字段": official.get("可核字段", ""),
        "官网本地留存可用文件数": str(len(existing_local_paths)),
        "官网本地留存路径": "；".join(existing_local_paths),
        "证据集分层": EVIDENCE_TIERS[name],
        "主要OCR/对照风险": FIELD_RISK_NOTES[name],
        "初步结论": "可用于定位与生成复核任务；不可直接作为 final_allowed 结构化数据。",
        "结构化试跑建议": STRUCTURE_TRIAL_NOTES[name],
        "下一步": "100%回看第19期原PDF页，逐组核院校代码、专业组代码、选科、组内全部专业、专业代号、计划数、学费和备注；再与学校官网/官方系统交叉确认。",
    }


def main():
    ocr_rows = read_csv(DEFAULT_OCR_SAMPLE)
    official_rows = read_csv(DEFAULT_OFFICIAL_SOURCES)
    official_by_school = {row["学校名称"]: row for row in official_rows}

    output_rows = [
        summarize_school(name, ocr_rows, official_by_school)
        for name in HIGH_PRIORITY_SCHOOLS
    ]

    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with DEFAULT_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(output_rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"写出第19期高优先级样本 double check 摘要：{DEFAULT_OUTPUT}")
    print(f"学校数：{len(output_rows)}")


if __name__ == "__main__":
    main()
