#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

D0_D1_PRIVATE_ITEMS = (
    ROOT
    / "private/review-assets/issue19-school-source-adapter-d0-d1-manual-review-packets-v1"
    / "school-source-adapter-d0-d1-private-review-items.csv"
)
PAGE_SIDE_PACKETS = (
    WORKING / "issue19-school-source-adapter-d0-d1-page-side-packets-v1-public-ledger.csv"
)
PAGE_SIDE_PROGRESS = (
    WORKING / "issue19-school-source-adapter-d0-d1-page-side-progress-v1-public-ledger.csv"
)
PAGE_SIDE_VISUAL = (
    WORKING
    / "issue19-school-source-adapter-d0-d1-page-side-pdf-visual-audit-v1-public-ledger.csv"
)
PAGE_SIDE_PRIVATE_INDEX = (
    ROOT
    / "private/review-assets/issue19-school-source-adapter-d0-d1-page-side-packets-v1"
    / "page-side-packets-private-index.csv"
)

PUBLIC_OUTPUT = (
    WORKING / "issue19-school-source-adapter-d0-d1-item-evidence-route-v1-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    WORKING / "issue19-school-source-adapter-d0-d1-item-evidence-route-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_adapter_d0_d1_item_evidence_route_v1"
GENERATED_AT = "2026-06-29"

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
]

PUBLIC_FIELDS = [
    "高校源AdapterD0D1逐项证据路由ID",
    "来源D0D1私有核验项",
    "来源D0D1页列包公开账本",
    "来源D0D1页列进度公开账本",
    "来源D0D1页列PDF视觉审计",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行序号",
    "来源页码",
    "版面列",
    "页码版面键SHA16",
    "高校源AdapterD0D1人工核验项ID",
    "高校源AdapterD0D1人工核验包ID",
    "高校源AdapterD0D1页列核验包ID",
    "高校源AdapterD0D1页列进度公开账本ID",
    "高校源AdapterD0D1页列PDF视觉核验审计ID",
    "人工核验优先级",
    "人工核验原因桶",
    "建议核验动作桶",
    "PDF_OCR计划状态",
    "PDF_OCR费用状态",
    "PDF_OCR选科状态",
    "高校源计划状态",
    "高校源费用状态",
    "高校源选科状态",
    "高校源匹配状态",
    "名称匹配方式",
    "名称匹配分层",
    "计划数核验状态",
    "高校源覆盖结论",
    "冲突核验桶",
    "是否建议双人复核",
    "PDF视觉素材状态",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有栏图证据编号",
    "私有栏图SHA256",
    "私有审阅HTML证据编号",
    "私有审阅HTML_SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页列HTML证据编号",
    "私有页列HTML_SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

FORBIDDEN_PUBLIC_TOKENS = [
    "/Users/",
    "/home/",
    "/var/folders/",
    "/private/",
    "private/",
    "private\\",
    "ocr-runs",
    "rendered-pages",
    "file://",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".heic",
    "Authorization",
    "Bearer ",
    "Cookie",
    "Set-Cookie",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "api_key",
    "身份证",
    "准考证",
    "报名号",
    "序列号",
    "手机号",
    "院校名称",
    "学校名称",
    "专业名称",
    "专业名称及备注OCR",
    "专业代号",
    "院校专业组代码",
    "官方来源文件",
    "最佳高校源专业名称",
    "最佳高校源计划数",
    "字段值",
    "字段读数",
    "人工读数",
    "候选值",
    "OCR正文",
    "OCR行文本",
    "截图路径",
    "复核备注",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
    "data/external/",
]

PRIORITY_SORT = {
    "R0-计划数冲突优先核PDF原页": 0,
    "R1-OCR计划数缺失但高校源可补": 1,
    "R2-疑似匹配专业名人工确认": 2,
    "R3-计划数一致候选抽检": 3,
}

CONFLICT_BUCKET_BY_PRIORITY = {
    "R0-计划数冲突优先核PDF原页": "C0-计划数冲突",
    "R1-OCR计划数缺失但高校源可补": "C1-OCR计划缺失可补",
    "R2-疑似匹配专业名人工确认": "C2-名称疑似匹配",
    "R3-计划数一致候选抽检": "C3-计划一致抽检",
}


def clean(value):
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames or []


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: clean(row.get(field, "")) for field in fields} for row in rows])


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path):
    return str(path.relative_to(ROOT))


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha16(values):
    text = "\n".join(sorted({clean(value) for value in values if clean(value)}))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else ""


def stable_id(prefix, parts):
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def as_int(value):
    try:
        return int(str(value).strip() or "0")
    except ValueError:
        return 0


def page_side_key(row):
    return clean(row.get("来源页码", "")), clean(row.get("版面列", ""))


def side_sort_value(side):
    return {"left": 0, "左": 0, "左栏": 0, "right": 1, "右": 1, "右栏": 1}.get(side, 9)


def has_text(value):
    return bool(clean(value))


def status_from_text(value, present_status, missing_status):
    return present_status if has_text(value) else missing_status


def score_band(value):
    text = clean(value)
    if not text:
        return "名称匹配分缺失"
    try:
        score = float(text)
    except ValueError:
        return "名称匹配分异常"
    if score >= 0.95:
        return "名称匹配高"
    if score >= 0.85:
        return "名称匹配中"
    return "名称匹配低"


def double_review_required(priority):
    return priority in {
        "R0-计划数冲突优先核PDF原页",
        "R2-疑似匹配专业名人工确认",
    }


def reason_bucket(value):
    text = clean(value)
    if "计划数冲突" in text:
        return "计划数冲突"
    if "计划数缺失" in text or "OCR计划数缺失" in text:
        return "OCR计划缺失"
    if "疑似匹配" in text or "专业名" in text:
        return "名称疑似匹配"
    if "抽检" in text or "一致" in text:
        return "一致性抽检"
    return "其他"


def action_bucket(value):
    text = clean(value)
    if "PDF" in text and "湖北官方" in text:
        return "PDF原页和湖北官方侧双核"
    if "PDF" in text:
        return "PDF原页优先核验"
    if "湖北官方" in text:
        return "湖北官方侧优先核验"
    if "高校源" in text or "官网" in text:
        return "高校源辅证复核"
    return "人工复核"


def coverage_bucket(value):
    text = clean(value)
    if "OCR缺口" in text or "OCR漏识" in text:
        return "高校源可补PDF_OCR缺口"
    if "疑似" in text:
        return "高校源疑似匹配待人工确认"
    if "计划数" in text and "仍需" in text:
        return "高校源覆盖但计划字段待复核"
    if "计划数" in text:
        return "高校源覆盖计划待三方复核"
    return "高校源覆盖情况待复核"


def row_sort_key(row, page_side_sequence):
    page, side = page_side_key(row)
    return (
        page_side_sequence.get((page, side), 9999),
        PRIORITY_SORT.get(row.get("人工核验优先级", ""), 9),
        as_int(row.get("专业组内专业序号")),
        row.get("高校源AdapterD0D1人工核验项ID", ""),
    )


def build_rows():
    private_items, _ = read_csv(D0_D1_PRIVATE_ITEMS)
    page_rows, _ = read_csv(PAGE_SIDE_PACKETS)
    progress_rows, _ = read_csv(PAGE_SIDE_PROGRESS)
    visual_rows, _ = read_csv(PAGE_SIDE_VISUAL)
    private_index_rows, _ = read_csv(PAGE_SIDE_PRIVATE_INDEX)

    page_by_key = {page_side_key(row): row for row in page_rows}
    progress_by_packet = {
        row.get("高校源AdapterD0D1页列核验包ID", ""): row for row in progress_rows
    }
    visual_by_packet = {
        row.get("高校源AdapterD0D1页列核验包ID", ""): row for row in visual_rows
    }
    private_index_by_packet = {
        row.get("高校源AdapterD0D1页列核验包ID", ""): row for row in private_index_rows
    }
    page_side_sequence = {
        page_side_key(row): as_int(row.get("页列执行序号")) for row in page_rows
    }

    rows = []
    for index, item in enumerate(
        sorted(private_items, key=lambda row: row_sort_key(row, page_side_sequence)),
        start=1,
    ):
        key = page_side_key(item)
        page_row = page_by_key.get(key)
        if not page_row:
            raise SystemExit(f"missing page-side public row for {key}")
        packet_id = page_row.get("高校源AdapterD0D1页列核验包ID", "")
        progress_row = progress_by_packet.get(packet_id)
        visual_row = visual_by_packet.get(packet_id)
        private_index_row = private_index_by_packet.get(packet_id)
        if not progress_row:
            raise SystemExit(f"missing progress row for {packet_id}")
        if not visual_row:
            raise SystemExit(f"missing visual row for {packet_id}")
        if not private_index_row:
            raise SystemExit(f"missing private page-side index row for {packet_id}")

        priority = item.get("人工核验优先级", "")
        route_id = stable_id(
            "SSITEMROUTE",
            [
                SOURCE_PDF_SHA256,
                item.get("高校源AdapterD0D1人工核验项ID", ""),
                packet_id,
            ],
        )
        rows.append({
            "高校源AdapterD0D1逐项证据路由ID": route_id,
            "来源D0D1私有核验项": "local_d0_d1_private_review_items_sha_recorded_not_public",
            "来源D0D1页列包公开账本": source_path(PAGE_SIDE_PACKETS),
            "来源D0D1页列进度公开账本": source_path(PAGE_SIDE_PROGRESS),
            "来源D0D1页列PDF视觉审计": source_path(PAGE_SIDE_VISUAL),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校源Adapter D0/D1私有核验项",
            "任务粒度": "逐项证据路由",
            **false_gate_values(),
            "执行序号": index,
            "来源页码": item.get("来源页码", ""),
            "版面列": item.get("版面列", ""),
            "页码版面键SHA16": page_row.get("页码版面键SHA16", ""),
            "高校源AdapterD0D1人工核验项ID": item.get("高校源AdapterD0D1人工核验项ID", ""),
            "高校源AdapterD0D1人工核验包ID": item.get("高校源AdapterD0D1人工核验包ID", ""),
            "高校源AdapterD0D1页列核验包ID": packet_id,
            "高校源AdapterD0D1页列进度公开账本ID": progress_row.get(
                "高校源AdapterD0D1页列进度公开账本ID", ""
            ),
            "高校源AdapterD0D1页列PDF视觉核验审计ID": visual_row.get(
                "高校源AdapterD0D1页列PDF视觉核验审计ID", ""
            ),
            "人工核验优先级": priority,
            "人工核验原因桶": reason_bucket(item.get("人工核验原因", "")),
            "建议核验动作桶": action_bucket(item.get("建议核验动作", "")),
            "PDF_OCR计划状态": status_from_text(
                item.get("OCR专业计划数候选", ""),
                "PDF_OCR计划有线索",
                "PDF_OCR计划缺线索",
            ),
            "PDF_OCR费用状态": status_from_text(
                item.get("OCR学费候选", ""),
                "PDF_OCR费用有线索",
                "PDF_OCR费用缺线索",
            ),
            "PDF_OCR选科状态": status_from_text(
                item.get("OCR再选科目候选", ""),
                "PDF_OCR选科有线索",
                "PDF_OCR选科缺线索",
            ),
            "高校源计划状态": status_from_text(
                item.get("最佳高校源计划数", ""),
                "高校源计划有线索",
                "高校源计划缺线索",
            ),
            "高校源费用状态": status_from_text(
                item.get("最佳高校源学费", ""),
                "高校源费用有线索",
                "高校源费用缺线索",
            ),
            "高校源选科状态": status_from_text(
                item.get("最佳高校源选科", ""),
                "高校源选科有线索",
                "高校源选科缺线索",
            ),
            "高校源匹配状态": item.get("本轮高校源匹配状态", ""),
            "名称匹配方式": item.get("本轮专业名称匹配方式", ""),
            "名称匹配分层": score_band(item.get("本轮专业名称匹配分", "")),
            "计划数核验状态": item.get("本轮计划数核验状态", ""),
            "高校源覆盖结论": coverage_bucket(item.get("本轮高校源覆盖结论", "")),
            "冲突核验桶": CONFLICT_BUCKET_BY_PRIORITY.get(priority, "C9-其他"),
            "是否建议双人复核": "true" if double_review_required(priority) else "false",
            "PDF视觉素材状态": "local_pdf_visual_ready_sha_recorded",
            "私有页图证据编号": visual_row.get("私有页图证据编号", ""),
            "私有页图SHA256": visual_row.get("私有页图SHA256", ""),
            "私有栏图证据编号": visual_row.get("私有栏图证据编号", ""),
            "私有栏图SHA256": visual_row.get("私有栏图SHA256", ""),
            "私有审阅HTML证据编号": visual_row.get("私有审阅HTML证据编号", ""),
            "私有审阅HTML_SHA256": visual_row.get("私有审阅HTML_SHA256", ""),
            "私有页列CSV证据编号": progress_row.get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": progress_row.get("私有页列CSV_SHA256", ""),
            "私有页列HTML证据编号": progress_row.get("私有页列HTML证据编号", ""),
            "私有页列HTML_SHA256": progress_row.get("私有页列HTML_SHA256", ""),
            "PDF原页核页状态": item.get("PDF原页核页状态", ""),
            "湖北官方系统或省招办计划核验状态": item.get(
                "湖北官方系统或省招办计划核验状态", ""
            ),
            "高校官网结构化源状态": item.get("高校官网结构化源状态", ""),
            "字段事实写回状态": item.get("字段事实写回状态", ""),
            "公开安全策略": "公开层只保存逐项状态、桶、证据编号和SHA；学校、专业、代码、OCR线索、数值线索、人工记录和本地材料路径均留在本地。",
            "下一步": "先核PDF原页和湖北官方侧，再用高校官网结构化源作辅证；三方一致并完成私有记录前不得写回字段事实或生成志愿建议。",
        })
    return rows


def build_summary(rows):
    priority_counts = Counter(row["人工核验优先级"] for row in rows)
    conflict_counts = Counter(row["冲突核验桶"] for row in rows)
    return {
        "status": "issue19_school_source_adapter_d0_d1_item_evidence_route_v1_not_final",
        "generated_by": "build_issue19_school_source_adapter_d0_d1_item_evidence_route_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_private_review_items_sha256": sha256(D0_D1_PRIVATE_ITEMS),
        "source_page_side_packets_public": source_path(PAGE_SIDE_PACKETS),
        "source_page_side_progress_public": source_path(PAGE_SIDE_PROGRESS),
        "source_page_side_visual_public": source_path(PAGE_SIDE_VISUAL),
        "source_page_side_private_index_sha256": sha256(PAGE_SIDE_PRIVATE_INDEX),
        "output_public_table": source_path(PUBLIC_OUTPUT),
        "row_count": len(rows),
        "unique_review_item_count": len({
            row["高校源AdapterD0D1人工核验项ID"] for row in rows
        }),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "page_priority_counts": dict(priority_counts),
        "conflict_bucket_counts": dict(conflict_counts),
        "pdf_visual_ready_count": count_value(
            rows, "PDF视觉素材状态", "local_pdf_visual_ready_sha_recorded"
        ),
        "double_review_suggested_count": count_value(rows, "是否建议双人复核", "true"),
        "pdf_manual_review_pending_count": count_value(
            rows, "PDF原页核页状态", "pending_manual_pdf_review"
        ),
        "hubei_official_review_pending_count": count_value(
            rows, "湖北官方系统或省招办计划核验状态", "pending_hubei_official_plan_review"
        ),
        "field_writeback_ready_count": 0,
        "final_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "public_boundary": "公开表只保存逐项状态、桶、证据编号和SHA；学校、专业、代码、OCR线索、数值线索、人工记录和本地材料路径留在Git忽略私有目录。",
    }


def count_value(rows, field, value):
    return sum(row.get(field, "") == value for row in rows)


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"adapter d0/d1 item evidence route contains forbidden public tokens: {hits[:10]}")


def main():
    rows = build_rows()
    summary = build_summary(rows)
    assert_public_safe(rows, summary)
    write_csv(PUBLIC_OUTPUT, rows, PUBLIC_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(PUBLIC_OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")
    print(f"public route rows: {len(rows)}")


if __name__ == "__main__":
    main()
