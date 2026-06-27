#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]

IMMEDIATE_PACKET = ROOT / "data/working/issue19-field-fact-p0-immediate-review-packet.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
PDF_ANCHORS = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
RENDERED_PAGE_DIR = ROOT / "private" / "ocr-runs" / "issue19-full-120dpi" / "rendered-pages"
LOCAL_CROP_DIR = ROOT / "private" / "review-assets" / "issue19-p0-immediate-pdf-crops"
LOCAL_CROP_INDEX = LOCAL_CROP_DIR / "crop-index.csv"

OUTPUT = ROOT / "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-p0-immediate-pdf-crop-evidence-index-summary.json"

DATA_STAGE = "issue19_p0_immediate_pdf_crop_evidence_index"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"

RENDER_DPI = 120
VERTICAL_MARGIN_NORM = 0.035
X_MARGIN_NORM = 0.012
SIDE_DEFAULT_X = {
    "left": (0.055, 0.540),
    "right": (0.460, 0.945),
}

FIELDS = [
    "P0即时复核裁图证据索引ID",
    "来源P0字段即时复核包",
    "来源P0字段即时复核任务ID",
    "来源P0字段三方核验任务ID",
    "来源P0字段三方核验执行包ID",
    "来源专业行原页证据锚点表",
    "来源页级manifest",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动回填候选",
    "是否允许写回字段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "即时复核总序",
    "执行总序",
    "执行批次",
    "即时复核阶段",
    "字段名",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "来源页码",
    "版面列",
    "专业行原页证据锚点ID",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "私有窗口证据编号",
    "窗口文本SHA256",
    "窗口坐标摘要",
    "机器候选状态",
    "机器候选置信等级",
    "高校官网辅证覆盖状态",
    "机器候选与高校辅证关系",
    "语义多源优先桶",
    "是否需要双人复核",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图规格SHA256",
    "裁图字节数",
    "裁图宽度px",
    "裁图高度px",
    "源页图宽度px",
    "源页图高度px",
    "裁图bbox归一化",
    "裁图bbox像素",
    "裁图坐标来源",
    "裁图生成参数摘要",
    "裁图生成状态",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "证据索引用途",
    "下一步",
]

LOCAL_INDEX_FIELDS = FIELDS + ["本地裁图文件名"]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value, default=0):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return default


def as_float(value):
    try:
        return float(str(value or "").strip())
    except ValueError:
        return None


def clip(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def parse_window_coords(summary):
    match = re.search(
        r"x=([0-9.]+)-([0-9.]+);y=([0-9.]+)-([0-9.]+)",
        summary or "",
    )
    if not match:
        return [], []
    x1, x2, y1, y2 = [float(part) for part in match.groups()]
    return [x1, x2], [y1, y2]


def parse_float_list(value):
    result = []
    for part in re.split(r"[；;,]\s*", str(value or "")):
        parsed = as_float(part)
        if parsed is not None:
            result.append(parsed)
    return result


def crop_bbox(row, image_width, image_height):
    side = row.get("版面列", "")
    default_x = SIDE_DEFAULT_X.get(side, (0.055, 0.945))
    xs = list(default_x)
    ys = []

    window_xs, window_ys = parse_window_coords(row.get("窗口坐标摘要", ""))
    xs.extend(window_xs)
    ys.extend(window_ys)
    xs.extend(parse_float_list(row.get("候选证据x集合", "")))
    ys.extend(parse_float_list(row.get("候选证据y集合", "")))
    for key in ["OCR窗口y上界", "OCR窗口y下界"]:
        parsed = as_float(row.get(key, ""))
        if parsed is not None:
            ys.append(parsed)

    coord_source = "window_and_candidate_coordinates" if ys else "side_context_fallback"
    x_min = clip(min(xs) - X_MARGIN_NORM)
    x_max = clip(max(xs) + X_MARGIN_NORM)
    if not ys:
        y_min, y_max = 0.05, 0.95
    else:
        y_min = clip(min(ys) - VERTICAL_MARGIN_NORM)
        y_max = clip(max(ys) + VERTICAL_MARGIN_NORM)

    # OCR y is normalized from the PDF/page bottom; pixel y is from the image top.
    left_px = int(round(x_min * image_width))
    right_px = int(round(x_max * image_width))
    top_px = int(round((1.0 - y_max) * image_height))
    bottom_px = int(round((1.0 - y_min) * image_height))

    left_px = max(0, min(image_width - 1, left_px))
    right_px = max(left_px + 1, min(image_width, right_px))
    top_px = max(0, min(image_height - 1, top_px))
    bottom_px = max(top_px + 1, min(image_height, bottom_px))

    bbox_norm = {
        "x_min": round(x_min, 6),
        "x_max": round(x_max, 6),
        "y_min_bottom_origin": round(y_min, 6),
        "y_max_bottom_origin": round(y_max, 6),
    }
    bbox_px = {
        "left": left_px,
        "top": top_px,
        "right": right_px,
        "bottom": bottom_px,
    }
    return bbox_norm, bbox_px, coord_source


def fmt_bbox_norm(bbox):
    return (
        f"x={bbox['x_min']:.6f}-{bbox['x_max']:.6f};"
        f"y_bottom_origin={bbox['y_min_bottom_origin']:.6f}-{bbox['y_max_bottom_origin']:.6f}"
    )


def fmt_bbox_px(bbox):
    return f"x={bbox['left']}-{bbox['right']};y={bbox['top']}-{bbox['bottom']}"


def spec_hash(spec):
    text = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_text(text)


def build_rows():
    immediate_rows = read_csv(IMMEDIATE_PACKET)
    page_manifest_by_page = {
        as_int(row.get("PDF页码")): row
        for row in read_csv(PAGE_MANIFEST)
    }
    anchors_by_id = {
        row.get("专业行原页证据锚点ID"): row
        for row in read_csv(PDF_ANCHORS)
    }

    image_cache = {}
    public_rows = []
    local_rows = []
    for row in immediate_rows:
        page = as_int(row.get("来源页码"))
        page_manifest = page_manifest_by_page.get(page)
        anchor = anchors_by_id.get(row.get("专业行原页证据锚点ID", ""))
        if not page_manifest:
            raise ValueError(f"page manifest missing for page {page}")
        if not anchor:
            raise ValueError(f"PDF anchor missing for {row.get('专业行原页证据锚点ID')}")
        for field in ["专业行ID", "专业组出现ID", "院校代码", "来源页码", "版面列", "窗口坐标摘要"]:
            if row.get(field, "") != anchor.get(field, ""):
                raise ValueError(f"anchor mismatch on {field} for {row.get('P0字段即时复核任务ID')}")

        page_image_path = RENDERED_PAGE_DIR / f"page-{page:03d}.png"
        if page not in image_cache:
            if not page_image_path.exists():
                raise FileNotFoundError(page_image_path)
            page_image_sha = sha256_file(page_image_path)
            if page_image_sha != row.get("私有页图SHA256") or page_image_sha != page_manifest.get("私有页图SHA256"):
                raise ValueError(f"page image sha mismatch for page {page}")
            image_cache[page] = {
                "image": Image.open(page_image_path).convert("RGB"),
                "sha256": page_image_sha,
            }
        image_record = image_cache[page]
        image = image_record["image"]
        width, height = image.size
        bbox_norm, bbox_px, coord_source = crop_bbox(row, width, height)

        crop_id = stable_id(
            "P0CROP",
            [
                SOURCE_PDF_SHA256,
                row.get("P0字段即时复核任务ID", ""),
                row.get("专业行ID", ""),
                row.get("字段名", ""),
            ],
        )
        crop_image = image.crop((bbox_px["left"], bbox_px["top"], bbox_px["right"], bbox_px["bottom"]))
        crop_filename = f"{crop_id}.png"
        crop_path = LOCAL_CROP_DIR / crop_filename
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        crop_image.save(crop_path)
        crop_sha = sha256_file(crop_path)

        spec = {
            "crop_evidence_id": crop_id,
            "source_issue": SOURCE_ISSUE,
            "source_pdf_sha256": SOURCE_PDF_SHA256,
            "source_page": page,
            "source_side": row.get("版面列", ""),
            "source_page_image_evidence_id": row.get("私有页图证据编号", ""),
            "source_page_image_sha256": image_record["sha256"],
            "source_ocr_text_evidence_id": row.get("私有OCR文本证据编号", ""),
            "source_ocr_text_sha256": row.get("私有OCR文本SHA256", ""),
            "source_window_evidence_id": row.get("私有窗口证据编号", ""),
            "window_text_sha256": row.get("窗口文本SHA256", ""),
            "immediate_task_id": row.get("P0字段即时复核任务ID", ""),
            "source_triage_task_id": row.get("来源P0字段三方核验任务ID", ""),
            "major_line_id": row.get("专业行ID", ""),
            "field_name": row.get("字段名", ""),
            "pdf_anchor_id": row.get("专业行原页证据锚点ID", ""),
            "render_dpi": RENDER_DPI,
            "coordinate_system": "normalized_x_left_origin_y_bottom_origin_to_pixel_y_top_origin",
            "crop_mode": "page_side_context_with_window_and_candidate_coordinates",
            "vertical_margin_norm": VERTICAL_MARGIN_NORM,
            "x_margin_norm": X_MARGIN_NORM,
            "source_page_width_px": width,
            "source_page_height_px": height,
            "crop_bbox_norm": bbox_norm,
            "crop_bbox_px": bbox_px,
        }
        crop_spec_sha = spec_hash(spec)
        crop_width = bbox_px["right"] - bbox_px["left"]
        crop_height = bbox_px["bottom"] - bbox_px["top"]

        output_row = {
            "P0即时复核裁图证据索引ID": stable_id(
                "P0CROPINDEX",
                [crop_id, row.get("P0字段即时复核任务ID", ""), crop_spec_sha],
            ),
            "来源P0字段即时复核包": "data/working/issue19-field-fact-p0-immediate-review-packet.csv",
            "来源P0字段即时复核任务ID": row.get("P0字段即时复核任务ID", ""),
            "来源P0字段三方核验任务ID": row.get("来源P0字段三方核验任务ID", ""),
            "来源P0字段三方核验执行包ID": row.get("来源P0字段三方核验执行包ID", ""),
            "来源专业行原页证据锚点表": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
            "来源页级manifest": "data/working/issue19-page-manifest.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0字段×即时复核裁图证据",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "即时复核总序": row.get("即时复核总序", ""),
            "执行总序": row.get("执行总序", ""),
            "执行批次": row.get("执行批次", ""),
            "即时复核阶段": row.get("即时复核阶段", ""),
            "字段名": row.get("字段名", ""),
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "专业行原页证据锚点ID": row.get("专业行原页证据锚点ID", ""),
            "私有页图证据编号": row.get("私有页图证据编号", ""),
            "私有页图SHA256": row.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": row.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": row.get("私有OCR文本SHA256", ""),
            "私有窗口证据编号": row.get("私有窗口证据编号", ""),
            "窗口文本SHA256": row.get("窗口文本SHA256", ""),
            "窗口坐标摘要": row.get("窗口坐标摘要", ""),
            "机器候选状态": row.get("机器候选状态", ""),
            "机器候选置信等级": row.get("机器候选置信等级", ""),
            "高校官网辅证覆盖状态": row.get("高校官网辅证覆盖状态", ""),
            "机器候选与高校辅证关系": row.get("机器候选与高校辅证关系", ""),
            "语义多源优先桶": row.get("语义多源优先桶", ""),
            "是否需要双人复核": row.get("是否需要双人复核", ""),
            "裁图证据编号": crop_id,
            "裁图文件SHA256": crop_sha,
            "裁图规格SHA256": crop_spec_sha,
            "裁图字节数": str(crop_path.stat().st_size),
            "裁图宽度px": str(crop_width),
            "裁图高度px": str(crop_height),
            "源页图宽度px": str(width),
            "源页图高度px": str(height),
            "裁图bbox归一化": fmt_bbox_norm(bbox_norm),
            "裁图bbox像素": fmt_bbox_px(bbox_px),
            "裁图坐标来源": coord_source,
            "裁图生成参数摘要": (
                f"render_dpi={RENDER_DPI};mode=side_context;"
                f"coord_y_origin=bottom;vertical_margin={VERTICAL_MARGIN_NORM};"
                f"x_margin={X_MARGIN_NORM}"
            ),
            "裁图生成状态": "local_crop_generated_hash_recorded",
            "PDF原页核页状态": row.get("PDF原页核页状态", ""),
            "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统或省招办计划核验状态", ""),
            "高校官网或招生章程辅证状态": row.get("高校官网或招生章程辅证状态", ""),
            "三方字段一致性状态": row.get("三方字段一致性状态", ""),
            "字段事实写回状态": row.get("字段事实写回状态", ""),
            "证据索引用途": "仅用于定位和复验PDF原页裁图；不提供字段读数，不代表字段事实完成核验。",
            "下一步": "人工回看裁图和PDF原页，再与湖北官方系统或省招办计划、高校官网或章程做三方闭环。",
        }
        public_rows.append(output_row)
        local_rows.append({**output_row, "本地裁图文件名": crop_filename})

    return public_rows, local_rows


def write_summary(rows):
    field_counts = Counter(row["字段名"] for row in rows)
    batch_counts = Counter(row["执行批次"] for row in rows)
    stage_counts = Counter(row["即时复核阶段"] for row in rows)
    side_counts = Counter(row["版面列"] for row in rows)
    page_counts = Counter(row["来源页码"] for row in rows)
    coord_source_counts = Counter(row["裁图坐标来源"] for row in rows)
    crop_status_counts = Counter(row["裁图生成状态"] for row in rows)

    summary = {
        "status": "issue19_p0_immediate_pdf_crop_evidence_index_not_final",
        "generated_by": "build_issue19_p0_immediate_pdf_crop_evidence_index.py",
        "source_immediate_packet": "data/working/issue19-field-fact-p0-immediate-review-packet.csv",
        "source_pdf_anchor_table": "data/working/issue19-major-line-pdf-evidence-anchors.csv",
        "source_page_manifest": "data/working/issue19-page-manifest.csv",
        "output_table": "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv",
        "row_grain": "逐专业招生明细×P0字段×即时复核裁图证据",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "local_crop_asset_count": len(rows),
        "local_crop_index_generated": True,
        "unique_crop_index_id_count": len({row["P0即时复核裁图证据索引ID"] for row in rows}),
        "unique_crop_evidence_id_count": len({row["裁图证据编号"] for row in rows}),
        "unique_immediate_task_id_count": len({row["来源P0字段即时复核任务ID"] for row in rows}),
        "unique_source_triage_task_id_count": len({row["来源P0字段三方核验任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_major_field_pair_count": len({(row["专业行ID"], row["字段名"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "field_counts": dict(field_counts),
        "execution_batch_counts": dict(batch_counts),
        "immediate_stage_counts": dict(stage_counts),
        "side_counts": dict(side_counts),
        "crop_coordinate_source_counts": dict(coord_source_counts),
        "crop_status_counts": dict(crop_status_counts),
        "crop_file_hash_count": sum(bool(row["裁图文件SHA256"]) for row in rows),
        "crop_spec_hash_count": sum(bool(row["裁图规格SHA256"]) for row in rows),
        "pdf_anchor_link_count": sum(bool(row["专业行原页证据锚点ID"]) for row in rows),
        "page_manifest_link_count": sum(row["来源页级manifest"] == "data/working/issue19-page-manifest.csv" for row in rows),
        "pdf_manual_review_pending_count": sum(row["PDF原页核页状态"] == "pending_pdf_manual_review" for row in rows),
        "hubei_official_review_pending_count": sum(
            row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_plan_review"
            for row in rows
        ),
        "three_way_closure_pending_count": sum(row["三方字段一致性状态"] == "pending_three_way_closure" for row in rows),
        "field_writeback_ready_count": sum(
            row["字段事实写回状态"] != "blocked_until_pdf_hubei_school_three_way_closure"
            for row in rows
        ),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row["机器是否允许自动写回主表"] == "true" for row in rows),
        "auto_candidate_fill_allowed_count": sum(row["机器是否允许自动回填候选"] == "true" for row in rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "top_pdf_pages": dict(page_counts.most_common(30)),
        "public_safety_note": "公开表只保存证据编号、哈希、页码、版面列、bbox、生成参数和非最终门禁；裁图图片、整页图和OCR原文只在本地留存。",
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    public_rows, local_rows = build_rows()
    write_csv(OUTPUT, public_rows, FIELDS)
    write_csv(LOCAL_CROP_INDEX, local_rows, LOCAL_INDEX_FIELDS)
    write_summary(public_rows)
    print(f"写出P0即时复核裁图证据索引：{OUTPUT.relative_to(ROOT)}，{len(public_rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"本地裁图索引已生成：{LOCAL_CROP_INDEX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
