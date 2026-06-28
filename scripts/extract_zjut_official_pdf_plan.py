#!/usr/bin/env python3
import csv
import hashlib
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PAGE = ROOT / "data/external/issue19-b0-b1-official-sources/zjut-2026-plan-page.html"
SOURCE_PDF = ROOT / "data/external/issue19-b0-b1-official-sources/zjut-2026-province-major-plan.pdf"
OUTPUT_CSV = ROOT / "data/external/issue19-b0-b1-official-sources/zjut-2026-hubei-physics-plan-extracted.csv"
AUDIT_CSV = ROOT / "data/external/issue19-b0-b1-official-sources/zjut-2026-pdf-grid-audit.csv"
TMP_DIR = ROOT / "tmp/pdfs/zjut-official-extract"

PDF_SHA256 = "bc9bd03c622b3c1944b5d75c430de28f8e5a1fe111052f93b75eb6daa1c7e495"
PAGE_SHA256 = "4091ae4fd9737e6e092648971a038244571b74fbe8f2cb6fcdb6b9d66e60895e"
PDF_URL = "https://zs.zjut.edu.cn/ueditor/jsp/upload/file/20260618/1781777775637059419.pdf"
PAGE_URL = "https://zs.zjut.edu.cn/html/n2569.html"
PAGE_NUMBER = 1
HUBEI_COLUMN_INDEX = 15
HUBEI_COLUMN_BBOX = (1622, 0, 1662, 0)

FIELDS = [
    "学校名称",
    "原始PDF",
    "官网入口页",
    "页码",
    "PDF表格行号",
    "科类",
    "专业代码OCR",
    "专业名称",
    "总计划数",
    "湖北计划数",
    "湖北列索引",
    "湖北格bbox_px",
    "提取方法",
    "提取局限性",
]

AUDIT_FIELDS = [
    "学校名称",
    "官网入口页",
    "原始PDF",
    "页码",
    "PDF_SHA256",
    "入口页SHA256",
    "PDF_URL",
    "官网入口URL",
    "PDF表格行号",
    "行类型",
    "科类",
    "专业代码OCR",
    "专业名称",
    "总计划数",
    "湖北计划数读数",
    "湖北列索引",
    "湖北格bbox_px",
    "湖北格深色像素数",
    "纳入湖北物理类匹配表",
    "审计说明",
]

EXTRACTION_METHOD = "official_image_pdf_grid_visual_transcription_with_coordinate_audit"
LIMITATION = (
    "浙江工业大学官网PDF为图像型宽表，按湖北列坐标人工核页转录并记录格子bbox；"
    "未给湖北院校专业组代码、专业代号、学费、校区、再选科目和组内调剂边界，"
    "需与第19期原页及湖北官方系统对齐。"
)

# Coordinates are from a 200 dpi pdftoppm rendering of the official A3 PDF. Row
# numbers follow the detected horizontal grid in that rendered image.
HUBEI_AUDIT_ROWS = [
    {
        "row": 1,
        "y0": 303,
        "y1": 339,
        "type": "总计",
        "subject": "",
        "code": "",
        "major": "总计",
        "total": "2010",
        "hubei": "50",
        "include": False,
        "note": "湖北列全校总计划数，供合计校验。",
    },
    {
        "row": 4,
        "y0": 411,
        "y1": 447,
        "type": "历史类专业",
        "subject": "历史类",
        "code": "050201",
        "major": "英语",
        "total": "28",
        "hubei": "2",
        "include": False,
        "note": "历史类计划，不进入湖北物理类匹配表。",
    },
    {
        "row": 11,
        "y0": 662,
        "y1": 698,
        "type": "历史类小计",
        "subject": "",
        "code": "",
        "major": "历史类小计",
        "total": "149",
        "hubei": "2",
        "include": False,
        "note": "湖北历史类小计，供总计校验。",
    },
    {
        "row": 17,
        "y0": 877,
        "y1": 913,
        "type": "物理类专业",
        "subject": "物理",
        "code": "0702",
        "major": "物理学类（物理与光电信息类）",
        "total": "43",
        "hubei": "3",
        "include": True,
        "note": "",
    },
    {
        "row": 18,
        "y0": 913,
        "y1": 949,
        "type": "物理类专业",
        "subject": "物理",
        "code": "071102",
        "major": "应用心理学",
        "total": "7",
        "hubei": "3",
        "include": True,
        "note": "",
    },
    {
        "row": 19,
        "y0": 949,
        "y1": 985,
        "type": "物理类专业",
        "subject": "物理",
        "code": "0802",
        "major": "机械类",
        "total": "110",
        "hubei": "4",
        "include": True,
        "note": "",
    },
    {
        "row": 21,
        "y0": 1020,
        "y1": 1056,
        "type": "物理类专业",
        "subject": "物理",
        "code": "0804",
        "major": "材料类",
        "total": "69",
        "hubei": "3",
        "include": True,
        "note": "",
    },
    {
        "row": 28,
        "y0": 1271,
        "y1": 1307,
        "type": "物理类专业",
        "subject": "物理",
        "code": "080803",
        "major": "机器人工程",
        "total": "42",
        "hubei": "2",
        "include": True,
        "note": "",
    },
    {
        "row": 29,
        "y0": 1307,
        "y1": 1343,
        "type": "物理类专业",
        "subject": "物理",
        "code": "0809",
        "major": "计算机类",
        "total": "108",
        "hubei": "5",
        "include": True,
        "note": "该类包含数字媒体技术等方向，需回第19期原页和湖北官方侧确认组内明细。",
    },
    {
        "row": 35,
        "y0": 1523,
        "y1": 1558,
        "type": "物理类专业",
        "subject": "物理",
        "code": "0810",
        "major": "土木类",
        "total": "61",
        "hubei": "7",
        "include": True,
        "note": "与第19期OCR候选存在计划数差异时，优先回PDF原页和湖北官方侧核。",
    },
    {
        "row": 36,
        "y0": 1558,
        "y1": 1594,
        "type": "物理类专业",
        "subject": "物理",
        "code": "081001H",
        "major": "土木工程（中外合作办学）",
        "total": "62",
        "hubei": "6",
        "include": True,
        "note": "中外合作办学，家庭预算默认不进入主方案，只作字段核验。",
    },
    {
        "row": 37,
        "y0": 1594,
        "y1": 1630,
        "type": "物理类专业",
        "subject": "物理",
        "code": "081008",
        "major": "智能建造",
        "total": "53",
        "hubei": "3",
        "include": True,
        "note": "",
    },
    {
        "row": 40,
        "y0": 1702,
        "y1": 1738,
        "type": "物理类专业",
        "subject": "物理",
        "code": "0827",
        "major": "食品科学与工程类",
        "total": "61",
        "hubei": "6",
        "include": True,
        "note": "",
    },
    {
        "row": 43,
        "y0": 1809,
        "y1": 1845,
        "type": "物理类专业",
        "subject": "物理",
        "code": "082901",
        "major": "安全工程",
        "total": "31",
        "hubei": "3",
        "include": True,
        "note": "",
    },
    {
        "row": 46,
        "y0": 1917,
        "y1": 1953,
        "type": "物理类专业",
        "subject": "物理",
        "code": "1201",
        "major": "管理科学与工程类",
        "total": "35",
        "hubei": "3",
        "include": True,
        "note": "该格位于湖北列；建筑学行湖北列为空，需避免相邻列误读。",
    },
    {
        "row": 22,
        "y0": 1343,
        "y1": 1379,
        "type": "重点空格审计",
        "subject": "物理",
        "code": "080902H",
        "major": "软件工程（中外合作办学）",
        "total": "28",
        "hubei": "",
        "include": False,
        "note": "湖北列为空，不进入湖北物理类匹配表。",
    },
    {
        "row": 23,
        "y0": 1379,
        "y1": 1415,
        "type": "重点空格审计",
        "subject": "物理",
        "code": "080906H",
        "major": "数字媒体技术（中外合作办学）",
        "total": "22",
        "hubei": "",
        "include": False,
        "note": "湖北列为空；不能把该中外合作专业作为湖北物理类计划证据。",
    },
    {
        "row": 38,
        "y0": 1630,
        "y1": 1666,
        "type": "重点空格审计",
        "subject": "物理",
        "code": "0813",
        "major": "化工与制药类（化学工程类）",
        "total": "138",
        "hubei": "",
        "include": False,
        "note": "湖北列为空。",
    },
    {
        "row": 41,
        "y0": 1738,
        "y1": 1774,
        "type": "重点空格审计",
        "subject": "物理",
        "code": "082801",
        "major": "建筑学",
        "total": "16",
        "hubei": "",
        "include": False,
        "note": "湖北列为空；相邻列有数值，需避免错读为湖北计划。",
    },
    {
        "row": 49,
        "y0": 2025,
        "y1": 2055,
        "type": "物理类小计",
        "subject": "",
        "code": "",
        "major": "理工/物理类小计",
        "total": "1561",
        "hubei": "48",
        "include": False,
        "note": "湖北物理类小计，必须等于纳入匹配表的物理类专业计划数合计。",
    },
]


def find_binary(name):
    deps_bin = os.environ.get("CODEX_DEPS_BIN")
    if deps_bin:
        bundled = Path(deps_bin).expanduser() / name
        if bundled.exists():
            return str(bundled)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit(f"未找到 {name}。")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def render_pdf_page():
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    pdftoppm = find_binary("pdftoppm")
    output_prefix = TMP_DIR / "page"
    image_path = TMP_DIR / "page-1.png"
    if image_path.exists():
        image_path.unlink()
    completed = subprocess.run(
        [
            pdftoppm,
            "-f",
            "1",
            "-l",
            "1",
            "-png",
            "-r",
            "200",
            str(SOURCE_PDF),
            str(output_prefix),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"PDF渲染失败:\n{completed.stderr}")
    if not image_path.exists():
        raise SystemExit(f"PDF渲染未生成预期图片: {image_path}")
    return image_path


def dark_pixels(image_path, row):
    from PIL import Image

    x0, _, x1, _ = HUBEI_COLUMN_BBOX
    y0 = row["y0"]
    y1 = row["y1"]
    image = Image.open(image_path).convert("L")
    crop = image.crop((x0 + 2, y0 + 3, x1 - 2, y1 - 3))
    pixels = crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata()
    return sum(1 for pixel in pixels if pixel < 150)


def as_int(value):
    text = str(value or "").strip()
    return int(text) if text.isdigit() else 0


def hubei_bbox(row):
    x0, _, x1, _ = HUBEI_COLUMN_BBOX
    return f"{x0},{row['y0']},{x1},{row['y1']}"


def validate_inputs():
    if not SOURCE_PAGE.exists():
        raise SystemExit(f"缺少浙江工业大学官网入口页留存：{SOURCE_PAGE}")
    if not SOURCE_PDF.exists():
        raise SystemExit(f"缺少浙江工业大学官方PDF留存：{SOURCE_PDF}")
    actual_pdf_sha = sha256(SOURCE_PDF)
    actual_page_sha = sha256(SOURCE_PAGE)
    if actual_pdf_sha != PDF_SHA256:
        raise SystemExit(f"浙江工业大学PDF SHA不一致：{actual_pdf_sha}")
    if actual_page_sha != PAGE_SHA256:
        raise SystemExit(f"浙江工业大学官网入口页 SHA不一致：{actual_page_sha}")


def build_rows(image_path):
    output_rows = []
    audit_rows = []
    for row in HUBEI_AUDIT_ROWS:
        dark = dark_pixels(image_path, row)
        audit_rows.append(
            {
                "学校名称": "浙江工业大学",
                "官网入口页": str(SOURCE_PAGE.relative_to(ROOT)),
                "原始PDF": str(SOURCE_PDF.relative_to(ROOT)),
                "页码": str(PAGE_NUMBER),
                "PDF_SHA256": PDF_SHA256,
                "入口页SHA256": PAGE_SHA256,
                "PDF_URL": PDF_URL,
                "官网入口URL": PAGE_URL,
                "PDF表格行号": str(row["row"]),
                "行类型": row["type"],
                "科类": row["subject"],
                "专业代码OCR": row["code"],
                "专业名称": row["major"],
                "总计划数": row["total"],
                "湖北计划数读数": row["hubei"],
                "湖北列索引": str(HUBEI_COLUMN_INDEX),
                "湖北格bbox_px": hubei_bbox(row),
                "湖北格深色像素数": str(dark),
                "纳入湖北物理类匹配表": "是" if row["include"] else "否",
                "审计说明": row["note"],
            }
        )
        if row["include"]:
            output_rows.append(
                {
                    "学校名称": "浙江工业大学",
                    "原始PDF": str(SOURCE_PDF.relative_to(ROOT)),
                    "官网入口页": str(SOURCE_PAGE.relative_to(ROOT)),
                    "页码": str(PAGE_NUMBER),
                    "PDF表格行号": str(row["row"]),
                    "科类": row["subject"],
                    "专业代码OCR": row["code"],
                    "专业名称": row["major"],
                    "总计划数": row["total"],
                    "湖北计划数": row["hubei"],
                    "湖北列索引": str(HUBEI_COLUMN_INDEX),
                    "湖北格bbox_px": hubei_bbox(row),
                    "提取方法": EXTRACTION_METHOD,
                    "提取局限性": LIMITATION,
                }
            )
    return output_rows, audit_rows


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    validate_inputs()
    image_path = render_pdf_page()
    output_rows, audit_rows = build_rows(image_path)

    physics_sum = sum(as_int(row["湖北计划数"]) for row in output_rows)
    audit_total = next(row for row in audit_rows if row["行类型"] == "总计")
    history_subtotal = next(row for row in audit_rows if row["行类型"] == "历史类小计")
    physics_subtotal = next(row for row in audit_rows if row["行类型"] == "物理类小计")
    digital_media_empty = next(
        row for row in audit_rows if row["专业名称"] == "数字媒体技术（中外合作办学）"
    )
    architecture_empty = next(row for row in audit_rows if row["专业名称"] == "建筑学")
    management_row = next(row for row in output_rows if row["专业名称"] == "管理科学与工程类")

    if physics_sum != 48:
        raise SystemExit(f"浙江工业大学湖北物理类计划合计异常：{physics_sum}")
    if audit_total["湖北计划数读数"] != "50":
        raise SystemExit("浙江工业大学湖北总计划数应为 50")
    if history_subtotal["湖北计划数读数"] != "2":
        raise SystemExit("浙江工业大学湖北历史类小计应为 2")
    if physics_subtotal["湖北计划数读数"] != "48":
        raise SystemExit("浙江工业大学湖北物理类小计应为 48")
    if digital_media_empty["湖北计划数读数"] != "":
        raise SystemExit("浙江工业大学数字媒体技术中外合作湖北列应为空")
    if architecture_empty["湖北计划数读数"] != "":
        raise SystemExit("浙江工业大学建筑学湖北列应为空")
    if management_row["湖北计划数"] != "3":
        raise SystemExit("浙江工业大学管理科学与工程类湖北列应为 3")

    write_csv(OUTPUT_CSV, FIELDS, output_rows)
    write_csv(AUDIT_CSV, AUDIT_FIELDS, audit_rows)

    public_text = OUTPUT_CSV.read_text(encoding="utf-8", errors="ignore") + AUDIT_CSV.read_text(
        encoding="utf-8", errors="ignore"
    )
    forbidden = ["/Users/", "private/", "Authorization", "Bearer ", "Cookie", "最终推荐", "最终方案", "可填报"]
    if any(token in public_text for token in forbidden):
        raise SystemExit("公开浙江工业大学PDF抽取表包含禁止公开内容")

    print(f"写出浙江工业大学湖北物理类PDF抽取表：{OUTPUT_CSV.relative_to(ROOT)}")
    print(f"湖北物理类抽取行数：{len(output_rows)}")
    print(f"湖北物理类计划合计：{physics_sum}")
    print(f"写出浙江工业大学PDF网格审计表：{AUDIT_CSV.relative_to(ROOT)}")
    print(f"审计行数：{len(audit_rows)}")


if __name__ == "__main__":
    main()
