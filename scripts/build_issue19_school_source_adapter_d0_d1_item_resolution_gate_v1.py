#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

ITEM_ROUTE_PUBLIC = (
    WORKING / "issue19-school-source-adapter-d0-d1-item-evidence-route-v1-public-ledger.csv"
)
ITEM_ROUTE_SUMMARY = (
    WORKING / "issue19-school-source-adapter-d0-d1-item-evidence-route-v1-summary.json"
)

PUBLIC_OUTPUT = (
    WORKING / "issue19-school-source-adapter-d0-d1-item-resolution-gate-v1-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    WORKING / "issue19-school-source-adapter-d0-d1-item-resolution-gate-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_adapter_d0_d1_item_resolution_gate_v1"
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
    "是否可进入私有写回评审",
]

PUBLIC_FIELDS = [
    "高校源AdapterD0D1逐项准出门禁ID",
    "来源D0D1逐项证据路由公开账本",
    "来源D0D1逐项证据路由摘要",
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
    "高校源AdapterD0D1逐项证据路由ID",
    "高校源AdapterD0D1人工核验项ID",
    "高校源AdapterD0D1页列核验包ID",
    "高校源AdapterD0D1页列进度公开账本ID",
    "高校源AdapterD0D1页列PDF视觉核验审计ID",
    "人工核验优先级",
    "冲突核验桶",
    "准出门禁状态",
    "准出动作组",
    "PDF原页证据缺口",
    "湖北官方侧证据缺口",
    "高校辅证验证缺口",
    "冲突处理缺口",
    "双人复核缺口",
    "三方闭环缺口",
    "字段写回缺口",
    "必要缺口数",
    "缺口组合桶",
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

ACTION_GROUP_BY_CONFLICT = {
    "C0-计划数冲突": "G0-计划数冲突双核",
    "C1-OCR计划缺失可补": "G1-OCR缺口补读",
    "C2-名称疑似匹配": "G2-疑似匹配核名称",
    "C3-计划一致抽检": "G3-一致抽检三方确认",
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


def stable_id(prefix, parts):
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def is_true(value):
    return clean(value).lower() == "true"


def evidence_missing(row):
    pdf_missing = row.get("PDF原页核页状态", "") != "verified_against_pdf_original"
    hubei_missing = (
        row.get("湖北官方系统或省招办计划核验状态", "")
        != "verified_against_hubei_official_plan"
    )
    school_missing = row.get("高校官网结构化源状态", "") != "structured_school_source_verified"
    conflict_missing = row.get("冲突核验桶", "") in {"C0-计划数冲突", "C2-名称疑似匹配"}
    double_missing = is_true(row.get("是否建议双人复核", ""))
    three_way_missing = pdf_missing or hubei_missing or school_missing or conflict_missing
    writeback_missing = row.get("字段事实写回状态", "") != "ready_for_private_writeback_review"
    return {
        "PDF原页证据缺口": pdf_missing,
        "湖北官方侧证据缺口": hubei_missing,
        "高校辅证验证缺口": school_missing,
        "冲突处理缺口": conflict_missing,
        "双人复核缺口": double_missing,
        "三方闭环缺口": three_way_missing,
        "字段写回缺口": writeback_missing,
    }


def missing_combo(missing):
    labels = []
    if missing["PDF原页证据缺口"]:
        labels.append("缺PDF原页")
    if missing["湖北官方侧证据缺口"]:
        labels.append("缺湖北官方侧")
    if missing["高校辅证验证缺口"]:
        labels.append("高校辅证未验证")
    if missing["冲突处理缺口"]:
        labels.append("冲突未处理")
    if missing["双人复核缺口"]:
        labels.append("双人复核未完成")
    if missing["三方闭环缺口"]:
        labels.append("三方闭环未完成")
    if missing["字段写回缺口"]:
        labels.append("字段写回阻断")
    return "+".join(labels) if labels else "无缺口"


def build_rows():
    route_rows, _ = read_csv(ITEM_ROUTE_PUBLIC)
    public_rows = []
    for row in route_rows:
        missing = evidence_missing(row)
        missing_count = sum(1 for value in missing.values() if value)
        route_id = row.get("高校源AdapterD0D1逐项证据路由ID", "")
        gate_id = stable_id("SSITEMGATE", [SOURCE_PDF_SHA256, route_id])
        conflict_bucket = row.get("冲突核验桶", "")
        public_rows.append({
            "高校源AdapterD0D1逐项准出门禁ID": gate_id,
            "来源D0D1逐项证据路由公开账本": source_path(ITEM_ROUTE_PUBLIC),
            "来源D0D1逐项证据路由摘要": source_path(ITEM_ROUTE_SUMMARY),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校源Adapter D0/D1逐项证据路由",
            "任务粒度": "逐项准出门禁",
            **false_gate_values(),
            "执行序号": row.get("执行序号", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "页码版面键SHA16": row.get("页码版面键SHA16", ""),
            "高校源AdapterD0D1逐项证据路由ID": route_id,
            "高校源AdapterD0D1人工核验项ID": row.get("高校源AdapterD0D1人工核验项ID", ""),
            "高校源AdapterD0D1页列核验包ID": row.get("高校源AdapterD0D1页列核验包ID", ""),
            "高校源AdapterD0D1页列进度公开账本ID": row.get(
                "高校源AdapterD0D1页列进度公开账本ID", ""
            ),
            "高校源AdapterD0D1页列PDF视觉核验审计ID": row.get(
                "高校源AdapterD0D1页列PDF视觉核验审计ID", ""
            ),
            "人工核验优先级": row.get("人工核验优先级", ""),
            "冲突核验桶": conflict_bucket,
            "准出门禁状态": "blocked_missing_required_evidence" if missing_count else "ready_for_private_writeback_review",
            "准出动作组": ACTION_GROUP_BY_CONFLICT.get(conflict_bucket, "G9-其他人工核验"),
            **{field: "true" if value else "false" for field, value in missing.items()},
            "必要缺口数": missing_count,
            "缺口组合桶": missing_combo(missing),
            "PDF视觉素材状态": row.get("PDF视觉素材状态", ""),
            "私有页图证据编号": row.get("私有页图证据编号", ""),
            "私有页图SHA256": row.get("私有页图SHA256", ""),
            "私有栏图证据编号": row.get("私有栏图证据编号", ""),
            "私有栏图SHA256": row.get("私有栏图SHA256", ""),
            "私有审阅HTML证据编号": row.get("私有审阅HTML证据编号", ""),
            "私有审阅HTML_SHA256": row.get("私有审阅HTML_SHA256", ""),
            "私有页列CSV证据编号": row.get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": row.get("私有页列CSV_SHA256", ""),
            "私有页列HTML证据编号": row.get("私有页列HTML证据编号", ""),
            "私有页列HTML_SHA256": row.get("私有页列HTML_SHA256", ""),
            "PDF原页核页状态": row.get("PDF原页核页状态", ""),
            "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统或省招办计划核验状态", ""),
            "高校官网结构化源状态": row.get("高校官网结构化源状态", ""),
            "字段事实写回状态": row.get("字段事实写回状态", ""),
            "公开安全策略": "公开层只保存准出门禁、缺口桶、证据编号和SHA；学校、专业、代码、OCR线索、字段内容、人工记录和本地材料路径均留在本地。",
            "下一步": "逐条补齐PDF原页、湖北官方侧、高校辅证、冲突处理和必要双人复核；全部完成后才允许进入私有写回评审。",
        })
    return public_rows


def count_true(rows, field):
    return sum(row.get(field, "") == "true" for row in rows)


def build_summary(rows):
    return {
        "status": "issue19_school_source_adapter_d0_d1_item_resolution_gate_v1_not_final",
        "generated_by": "build_issue19_school_source_adapter_d0_d1_item_resolution_gate_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_item_route_public": source_path(ITEM_ROUTE_PUBLIC),
        "source_item_route_summary": source_path(ITEM_ROUTE_SUMMARY),
        "source_item_route_public_sha256": sha256(ITEM_ROUTE_PUBLIC),
        "output_public_table": source_path(PUBLIC_OUTPUT),
        "row_count": len(rows),
        "unique_gate_id_count": len({row["高校源AdapterD0D1逐项准出门禁ID"] for row in rows}),
        "unique_route_id_count": len({row["高校源AdapterD0D1逐项证据路由ID"] for row in rows}),
        "unique_review_item_count": len({row["高校源AdapterD0D1人工核验项ID"] for row in rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "priority_counts": dict(Counter(row["人工核验优先级"] for row in rows)),
        "conflict_bucket_counts": dict(Counter(row["冲突核验桶"] for row in rows)),
        "action_group_counts": dict(Counter(row["准出动作组"] for row in rows)),
        "gate_status_counts": dict(Counter(row["准出门禁状态"] for row in rows)),
        "pdf_original_missing_count": count_true(rows, "PDF原页证据缺口"),
        "hubei_official_missing_count": count_true(rows, "湖北官方侧证据缺口"),
        "school_source_unverified_count": count_true(rows, "高校辅证验证缺口"),
        "conflict_processing_missing_count": count_true(rows, "冲突处理缺口"),
        "double_review_missing_count": count_true(rows, "双人复核缺口"),
        "three_way_closure_missing_count": count_true(rows, "三方闭环缺口"),
        "field_writeback_missing_count": count_true(rows, "字段写回缺口"),
        "private_writeback_review_ready_count": 0,
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "公开表只保存准出门禁、缺口桶、证据编号和SHA；学校、专业、代码、OCR线索、字段内容、人工记录和本地材料路径留在Git忽略私有目录。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"adapter d0/d1 item resolution gate contains forbidden public tokens: {hits[:10]}")


def main():
    rows = build_rows()
    summary = build_summary(rows)
    assert_public_safe(rows, summary)
    write_csv(PUBLIC_OUTPUT, rows, PUBLIC_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(PUBLIC_OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")
    print(f"resolution gate rows: {len(rows)}")


if __name__ == "__main__":
    main()
