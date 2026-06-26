#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHOOLS = ROOT / "data/working/issue19-sample-schools-20.csv"
DEFAULT_OCR_LINES = ROOT / "private/ocr-runs/issue19-full-120dpi/ocr-lines.csv"
DEFAULT_OUTPUT = ROOT / "private/derived/issue19-sample-school-ocr/样本学校OCR定位.csv"
FALSE_POSITIVE_SCHOOL_NAMES = {
    "湖北大学": ["湖北大学知行学院"],
    "武汉体育学院": ["武汉体育学院体育科技学院"],
    "湖北工程学院": ["湖北工程学院新技术学院"],
    "湖北文理学院": ["湖北文理学院理工学院"],
    "湖北经济学院": ["湖北经济学院法商学院"],
}


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def nearby_context(rows_by_page, page, line_no, window):
    rows = rows_by_page.get(page, [])
    selected = []
    for row in rows:
        current = int(row["line_no"])
        if abs(current - line_no) <= window:
            selected.append(row)
    return selected


def is_school_hit(name, text):
    if name not in text:
        return False
    for false_name in FALSE_POSITIVE_SCHOOL_NAMES.get(name, []):
        if false_name in text:
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="从第 19 期 OCR 行级数据中抽取样本学校定位上下文。")
    parser.add_argument("--schools", default=str(DEFAULT_SCHOOLS), help="样本学校 CSV，中文表头。")
    parser.add_argument("--ocr-lines", default=str(DEFAULT_OCR_LINES), help="ocr_jsonl_to_line_csv.py 生成的 OCR 行级 CSV。")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="输出 CSV，默认写入 private/derived。")
    parser.add_argument("--window", type=int, default=12, help="命中行上下文窗口，默认前后 12 行。")
    args = parser.parse_args()

    schools_path = Path(args.schools).expanduser()
    ocr_lines_path = Path(args.ocr_lines).expanduser()
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    schools = read_rows(schools_path)
    ocr_rows = read_rows(ocr_lines_path)
    rows_by_page = defaultdict(list)
    for row in ocr_rows:
        rows_by_page[row["page"]].append(row)

    fields = [
        "样本序号",
        "学校名称",
        "OCR页码",
        "命中行号",
        "上下文行号",
        "左右栏",
        "行类型",
        "OCR文本",
        "OCR置信度",
        "坐标x",
        "坐标y",
        "人工核验状态",
        "备注",
    ]

    output_rows = []
    for school in schools:
        name = school["学校名称"]
        hits = [
            row for row in ocr_rows
            if is_school_hit(name, row["text"]) and int(row["page"]) >= 10
        ]
        if not hits:
            output_rows.append({
                "样本序号": school["序号"],
                "学校名称": name,
                "OCR页码": "",
                "命中行号": "",
                "上下文行号": "",
                "左右栏": "",
                "行类型": "",
                "OCR文本": "",
                "OCR置信度": "",
                "坐标x": "",
                "坐标y": "",
                "人工核验状态": "未命中",
                "备注": "请检查学校名称或 OCR 误识别",
            })
            continue

        for hit in hits:
            page = hit["page"]
            line_no = int(hit["line_no"])
            for row in nearby_context(rows_by_page, page, line_no, args.window):
                output_rows.append({
                    "样本序号": school["序号"],
                    "学校名称": name,
                    "OCR页码": page,
                    "命中行号": hit["line_no"],
                    "上下文行号": row["line_no"],
                    "左右栏": row["table_band"],
                    "行类型": row["line_type"],
                    "OCR文本": row["text"],
                    "OCR置信度": row["confidence"],
                    "坐标x": row["x"],
                    "坐标y": row["y"],
                    "人工核验状态": "待回看PDF原页",
                    "备注": "",
                })

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"写出样本学校 OCR 定位：{output_path}")
    print(f"样本学校数：{len(schools)}")
    print(f"输出行数：{len(output_rows)}")


if __name__ == "__main__":
    main()
