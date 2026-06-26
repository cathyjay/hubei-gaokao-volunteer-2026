#!/usr/bin/env python3
import csv
import json
import shutil
from collections import defaultdict
from pathlib import Path

from issue19_review_rules import input_snapshot, sha256_file


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
CANDIDATE_REVIEW = ROOT / "data/working/issue19-candidate-plan-review-summary.csv"
FULL_GROUPS = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
FULL_MAJORS = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
RENDERED_PAGES = ROOT / "private/ocr-runs/issue19-full-120dpi/rendered-pages"
OCR_TEXT = ROOT / "private/ocr-runs/issue19-full-120dpi/text"
PRIVATE_PACKET_DIR = ROOT / "private/derived/issue19-candidate-review-page-packet"
PUBLIC_PAGE_OUTPUT = ROOT / "data/working/issue19-candidate-review-page-packet.csv"
PUBLIC_GROUP_OUTPUT = ROOT / "data/working/issue19-candidate-review-group-page-map.csv"
PUBLIC_SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-review-page-packet-summary.json"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None):
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def page_image(page):
    return RENDERED_PAGES / f"page-{page:03d}.png"


def page_text(page):
    return OCR_TEXT / f"{page:03d}_page-{page:03d}.txt"


def parse_pages(value):
    pages = []
    for part in str(value or "").replace("；", ";").split(";"):
        part = part.strip()
        if part.isdigit():
            pages.append(int(part))
    return pages


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    source_pdf_sha256 = issue19_source["source"]["sha256"]
    source_issue = issue19_source["source"]["title"]

    candidate_rows = read_csv(CANDIDATE_REVIEW)
    group_rows = read_csv(FULL_GROUPS)
    major_rows = read_csv(FULL_MAJORS)

    groups_by_school = defaultdict(list)
    for row in group_rows:
        groups_by_school[row["院校代码"]].append(row)

    majors_by_group = defaultdict(list)
    for row in major_rows:
        majors_by_group[row["院校专业组代码OCR规范化"]].append(row)

    review_pages = set()
    group_map_rows = []
    for row in candidate_rows:
        group_code = row["候选专业组代码"]
        school_code = group_code[:4]
        matched_pages = parse_pages(row.get("第19期OCR页码"))
        same_school_groups = groups_by_school.get(school_code, [])
        same_school_pages = sorted({
            page
            for group in same_school_groups
            for page in parse_pages(group.get("来源页码", ""))
        })
        pages = matched_pages or same_school_pages
        review_pages.update(pages)
        group_map_rows.append({
            "来源期号": row.get("来源期号", source_issue),
            "来源PDF_SHA256": row.get("来源PDF_SHA256", source_pdf_sha256),
            "数据阶段": "candidate_review_page_packet",
            "候选池学校专业组": row["候选池学校专业组"],
            "候选专业组代码": group_code,
            "第19期全量OCR命中": row["第19期全量OCR命中"],
            "候选复核页码": "；".join(str(page) for page in pages),
            "同校第19期OCR专业组": "；".join(group["院校专业组代码OCR规范化"] for group in same_school_groups),
            "同校第19期OCR页码": "；".join(str(page) for page in same_school_pages),
            "OCR专业行数": row["OCR专业行数"],
            "机器初判": row["机器初判"],
            "硬风险类型": row["硬风险类型"],
            "核验状态": row["核验状态"],
            "下一步": "打开私有页图和页面OCR文本，逐字段核对候选专业组及同校相邻专业组",
        })

    PRIVATE_PACKET_DIR.mkdir(parents=True, exist_ok=True)
    (PRIVATE_PACKET_DIR / "pages").mkdir(exist_ok=True)
    (PRIVATE_PACKET_DIR / "text").mkdir(exist_ok=True)

    page_rows = []
    for page in sorted(review_pages):
        image = page_image(page)
        text = page_text(page)
        if not image.exists() or not text.exists():
            raise FileNotFoundError(f"Missing rendered page or OCR text for page {page}")
        target_image = PRIVATE_PACKET_DIR / "pages" / image.name
        target_text = PRIVATE_PACKET_DIR / "text" / text.name
        shutil.copy2(image, target_image)
        shutil.copy2(text, target_text)

        related_candidates = [
            row["候选专业组代码"]
            for row in group_map_rows
            if str(page) in row["候选复核页码"].split("；")
        ]
        related_groups = [
            group["院校专业组代码OCR规范化"]
            for group in group_rows
            if page in parse_pages(group.get("来源页码", ""))
        ]
        page_rows.append({
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "candidate_review_page_packet",
            "页码": str(page),
            "页图文件名": image.name,
            "页图SHA256": sha256_file(image),
            "页面OCR文本文件名": text.name,
            "页面OCR文本SHA256": sha256_file(text),
            "关联候选专业组": "；".join(related_candidates),
            "本页OCR专业组": "；".join(related_groups),
            "本页OCR专业组数": str(len(related_groups)),
            "公开状态": "public_metadata_only_private_page_assets",
            "核验状态": "needs_manual_pdf_review",
        })

    index_lines = [
        "# 第 19 期候选池页面复核包",
        "",
        f"- 来源：{source_issue}",
        f"- PDF SHA256：{source_pdf_sha256}",
        f"- 页数：{len(page_rows)}",
        "",
        "## 使用方式",
        "",
        "1. 先看 `candidate-review-group-page-map.csv` 定位候选专业组和同校 OCR 专业组。",
        "2. 打开 `pages/` 下对应页图，逐字段核对院校专业组、专业代号、专业名称、计划数、学费、选科和备注。",
        "3. 对照 `text/` 下同页 OCR 文本，只把人工确认后的结果升级到候选池 V2。",
        "",
        "## 页码清单",
        "",
    ]
    for row in page_rows:
        index_lines.append(
            f"- 第 {row['页码']} 页：候选 {row['关联候选专业组'] or '无直接候选'}；"
            f"本页专业组 {row['本页OCR专业组']}"
        )
    (PRIVATE_PACKET_DIR / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    write_csv(PRIVATE_PACKET_DIR / "candidate-review-group-page-map.csv", group_map_rows)
    write_csv(PRIVATE_PACKET_DIR / "candidate-review-pages.csv", page_rows)

    write_csv(PUBLIC_GROUP_OUTPUT, group_map_rows)
    write_csv(PUBLIC_PAGE_OUTPUT, page_rows)

    summary = {
        "status": "candidate_review_page_packet_ready_private_assets_not_committed",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "candidate_review_page_packet",
        "generated_by": "scripts/build_issue19_candidate_review_page_packet.py",
        "inputs": input_snapshot(ROOT, [ISSUE19_SOURCE, CANDIDATE_REVIEW, FULL_GROUPS, FULL_MAJORS]),
        "candidate_count": len(candidate_rows),
        "review_page_count": len(page_rows),
        "review_pages": [int(row["页码"]) for row in page_rows],
        "group_map_row_count": len(group_map_rows),
        "outputs": [
            str(PUBLIC_PAGE_OUTPUT.relative_to(ROOT)),
            str(PUBLIC_GROUP_OUTPUT.relative_to(ROOT)),
        ],
        "private_assets_generated_locally": True,
        "private_asset_types": ["readme", "page_images", "page_ocr_text"],
        "notes": [
            "公开文件只保存页码、文件名和哈希，不提交 PDF 原页图或整页 OCR 文本。",
            "页面复核包用于人工回看第19期原页，不代表任何专业组已可填报。",
        ],
    }
    PUBLIC_SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出公开页面清单：{PUBLIC_PAGE_OUTPUT}")
    print(f"写出公开候选组页码映射：{PUBLIC_GROUP_OUTPUT}")
    print(f"写出公开摘要：{PUBLIC_SUMMARY_OUTPUT}")
    print(f"写出私有页面复核包：{PRIVATE_PACKET_DIR}")
    print(f"复核页数：{len(page_rows)}")


if __name__ == "__main__":
    main()
