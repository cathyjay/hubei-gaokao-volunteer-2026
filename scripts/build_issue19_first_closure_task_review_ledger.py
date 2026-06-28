#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIRST_DETAIL = ROOT / "data/working/issue19-stable-foundation-first-closure-detail-packet.csv"
FIRST_PAGE_SIDE = ROOT / "data/working/issue19-stable-foundation-first-closure-page-side-packet.csv"
FIRST_REVIEW = ROOT / "data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv"
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

PUBLIC_OUTPUT = ROOT / "data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-stable-foundation-first-closure-task-review-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_task_review_public_ledger"

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
    "稳定基座第一闭环任务复核公开账本ID",
    "来源第一闭环明细包",
    "来源第一闭环页列包",
    "来源第一闭环复核公开账本",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环页列包ID",
    "稳定基座第一闭环复核公开账本ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "任务来源类型",
    "第一闭环批次",
    "第一闭环纳入原因",
    "第一闭环页列优先级",
    "任务级复核状态",
    "任务级阻断原因",
    "PDF原页是否必核",
    "湖北官方侧是否必核",
    "高校辅证是否需要复核",
    "是否需要双人复核",
    "字段名",
    "官网辅证自动动作",
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "差异字段集合",
    "疑似OCR把学费读入计划数",
    "最佳官网来源文件",
    "最佳官网来源文件是否存在",
    "最佳官网来源文件SHA256",
    "自动辅证是否可作为核页提示",
    "自动辅证是否可替代湖北官方计划",
    "P0字段即时复核任务ID",
    "P0即时字段确认公开账本ID",
    "执行批次",
    "人工核验泳道",
    "人工核验方式",
    "人工最小动作",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图bbox归一化",
    "私有第一闭环页列CSV证据编号",
    "私有第一闭环页列CSV_SHA256",
    "私有第一闭环页列HTML证据编号",
    "私有第一闭环页列HTML_SHA256",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "官方公开计划页可定稿",
    "数智平台可定稿",
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
    "身份证",
    "准考证",
    "报名号",
    "序列号",
    "OCR行文本",
    "PDF原页人工读数",
    "湖北官方字段值",
    "字段确认值",
    "一审记录",
    "二审记录",
    "复核结论",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def load_official_status():
    data = json.loads(OFFICIAL_STATUS.read_text(encoding="utf-8"))
    return {
        "official_public_plan_page_can_finalize": bool(
            data.get("hubei_admission_plan_page", {}).get("can_finalize")
        ),
        "zspt_platform_can_finalize": bool(
            data.get("hubei_zspt_platform", {}).get("can_finalize")
        ),
    }


def source_file_status(value):
    value = (value or "").strip()
    if not value:
        return "not_applicable_no_best_school_source", ""
    path = ROOT / value
    if not path.is_file():
        return "false_missing_public_source_file", ""
    return "true_public_source_file_retained", sha256(path)


def needs_school_review(row):
    if row.get("任务来源类型") == "自动官网辅证任务":
        return "true"
    status = row.get("高校官网或招生章程辅证状态", "")
    if status == "pending_private_school_reading":
        return "true"
    return "false"


def auto_hint_allowed(row, source_exists_status):
    if row.get("任务来源类型") != "自动官网辅证任务":
        return "false"
    if source_exists_status == "false_missing_public_source_file":
        return "false"
    if row.get("官网证据强度") in {
        "conflict_review",
        "fill_candidate",
        "strong_support",
        "field_support",
        "partial_source",
    }:
        return "true"
    return "false"


def task_status(row):
    if row.get("任务来源类型") == "自动官网辅证任务":
        return (
            "T0-待PDF原页和湖北官方核验",
            "高校官网辅证只能提示冲突或补缺，不能替代第19期原页和湖北官方侧",
        )
    return (
        "T0-待PDF原页湖北官方和必要高校辅证核验",
        "P0字段任务尚未写入私有人工记录，禁止字段事实写回",
    )


def minimal_action(row):
    action = row.get("官网辅证自动动作", "")
    batch = row.get("执行批次", "")
    field = row.get("字段名", "")
    if action == "C0-冲突先核PDF原页和湖北官方系统":
        return "先核PDF原页字段列，再核湖北官方侧；官网只作冲突提示"
    if action == "C1-官网补缺候选但禁止自动写回":
        return "先看PDF原页是否为空或漏读，再核湖北官方侧；官网只作补缺候选"
    if action == "C7-官网源未匹配专业需人工确认专业名":
        return "先确认专业名和限定词归属，再决定是否继续核字段"
    if batch == "EXEC-01-冲突异常立即核页":
        return f"双人核PDF原页与湖北官方侧的{field or '字段'}，确认异常来源"
    if batch == "EXEC-02-计划数偏大重点核页":
        return "重点核专业计划数是否误读为学费或串列，并核湖北官方侧"
    if batch == "EXEC-03-高校辅证线索三方核验":
        return f"按高校辅证线索核PDF原页、湖北官方侧和{field or '字段'}一致性"
    return "按页列材料核PDF原页和湖北官方侧，必要时补高校辅证"


def build():
    detail_rows = read_csv(FIRST_DETAIL)
    page_side_rows = read_csv(FIRST_PAGE_SIDE)
    review_rows = read_csv(FIRST_REVIEW)
    official = load_official_status()

    page_side_by_key = {row["页码版面键"]: row for row in page_side_rows}
    review_by_key = {row["页码版面键"]: row for row in review_rows}

    output_rows = []
    for row in detail_rows:
        key = row.get("页码版面键", "")
        page_side = page_side_by_key.get(key)
        review = review_by_key.get(key)
        if not page_side or not review:
            raise RuntimeError(f"第一闭环任务无法回链页列复核账本：{row.get('稳定基座第一闭环明细任务ID')}")

        source_status, source_hash = source_file_status(row.get("最佳官网来源文件", ""))
        status_bucket, block_reason = task_status(row)
        out = {
            "稳定基座第一闭环任务复核公开账本ID": stable_id(
                "FIRSTTASKREVIEW", [row.get("稳定基座第一闭环明细任务ID", "")]
            ),
            "来源第一闭环明细包": "data/working/issue19-stable-foundation-first-closure-detail-packet.csv",
            "来源第一闭环页列包": "data/working/issue19-stable-foundation-first-closure-page-side-packet.csv",
            "来源第一闭环复核公开账本": "data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv",
            "来源湖北官方公开入口状态快照": "data/working/issue19-official-public-entry-status.json",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细×第一闭环任务",
            "任务粒度": "逐任务×PDF原页×湖北官方侧×高校辅证状态",
            **false_gate_values(),
            "稳定基座第一闭环明细任务ID": row.get("稳定基座第一闭环明细任务ID", ""),
            "稳定基座第一闭环页列包ID": page_side.get("稳定基座第一闭环页列包ID", ""),
            "稳定基座第一闭环复核公开账本ID": review.get("稳定基座第一闭环复核公开账本ID", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "页码版面键": key,
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "任务来源类型": row.get("任务来源类型", ""),
            "第一闭环批次": row.get("第一闭环批次", ""),
            "第一闭环纳入原因": row.get("第一闭环纳入原因", ""),
            "第一闭环页列优先级": page_side.get("第一闭环页列优先级", ""),
            "任务级复核状态": status_bucket,
            "任务级阻断原因": block_reason,
            "PDF原页是否必核": "true",
            "湖北官方侧是否必核": "true",
            "高校辅证是否需要复核": needs_school_review(row),
            "是否需要双人复核": row.get("是否需要双人复核", "false"),
            "字段名": row.get("字段名", ""),
            "官网辅证自动动作": row.get("官网辅证自动动作", ""),
            "官网证据强度": row.get("官网证据强度", ""),
            "官网来源状态": row.get("官网来源状态", ""),
            "官网证据匹配状态": row.get("官网证据匹配状态", ""),
            "计划数核验状态": row.get("计划数核验状态", ""),
            "差异字段集合": row.get("差异字段集合", ""),
            "疑似OCR把学费读入计划数": row.get("疑似OCR把学费读入计划数", ""),
            "最佳官网来源文件": row.get("最佳官网来源文件", ""),
            "最佳官网来源文件是否存在": source_status,
            "最佳官网来源文件SHA256": source_hash,
            "自动辅证是否可作为核页提示": auto_hint_allowed(row, source_status),
            "自动辅证是否可替代湖北官方计划": "false",
            "P0字段即时复核任务ID": row.get("P0字段即时复核任务ID", ""),
            "P0即时字段确认公开账本ID": row.get("P0即时字段确认公开账本ID", ""),
            "执行批次": row.get("执行批次", ""),
            "人工核验泳道": row.get("人工核验泳道", ""),
            "人工核验方式": row.get("人工核验方式", ""),
            "人工最小动作": minimal_action(row),
            "裁图证据编号": row.get("裁图证据编号", ""),
            "裁图文件SHA256": row.get("裁图文件SHA256", ""),
            "裁图bbox归一化": row.get("裁图bbox归一化", ""),
            "私有第一闭环页列CSV证据编号": review.get("私有第一闭环页列CSV证据编号", ""),
            "私有第一闭环页列CSV_SHA256": review.get("私有第一闭环页列CSV_SHA256", ""),
            "私有第一闭环页列HTML证据编号": review.get("私有第一闭环页列HTML证据编号", ""),
            "私有第一闭环页列HTML_SHA256": review.get("私有第一闭环页列HTML_SHA256", ""),
            "PDF原页核页状态": row.get("PDF原页核页状态", ""),
            "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统或省招办计划核验状态", ""),
            "高校官网或招生章程辅证状态": row.get("高校官网或招生章程辅证状态", ""),
            "三方字段一致性状态": row.get("三方字段一致性状态", ""),
            "字段事实写回状态": row.get("字段事实写回状态", ""),
            "官方公开计划页可定稿": str(official["official_public_plan_page_can_finalize"]).lower(),
            "数智平台可定稿": str(official["zspt_platform_can_finalize"]).lower(),
            "公开安全策略": "公开任务级状态、公共来源文件SHA和私有材料证据编号；不公开页图路径、OCR原文、人工读数或登录态",
            "下一步": "在私有页列材料中完成PDF原页、湖北官方侧和必要高校辅证记录后，再由公开账本同步完成计数",
        }
        output_rows.append(out)

    text_for_scan = "\n".join(
        "\t".join(str(row.get(field, "")) for field in PUBLIC_FIELDS) for row in output_rows
    )
    forbidden = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text_for_scan]
    if forbidden:
        raise RuntimeError(f"公开任务账本包含禁止公开内容：{forbidden[:5]}")

    write_csv(PUBLIC_OUTPUT, output_rows, PUBLIC_FIELDS)

    source_file_rows = [row for row in output_rows if row["最佳官网来源文件"]]
    source_unique = {row["最佳官网来源文件"] for row in source_file_rows}
    auto_task_action_counts = Counter(
        row["官网辅证自动动作"]
        for row in output_rows
        if row["任务来源类型"] == "自动官网辅证任务" and row["官网辅证自动动作"]
    )
    school_support_action_counts = Counter(
        row["官网辅证自动动作"] for row in output_rows if row["官网辅证自动动作"]
    )
    summary = {
        "status": "issue19_stable_foundation_first_closure_task_review_not_final",
        "generated_by": "build_issue19_first_closure_task_review_ledger.py",
        "source_first_closure_detail_packet": "data/working/issue19-stable-foundation-first-closure-detail-packet.csv",
        "source_first_closure_page_side_packet": "data/working/issue19-stable-foundation-first-closure-page-side-packet.csv",
        "source_first_closure_review_public_ledger": "data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv",
        "source_official_public_status": "data/working/issue19-official-public-entry-status.json",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": "data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv",
        "public_row_count": len(output_rows),
        "unique_task_count": len({row["稳定基座第一闭环明细任务ID"] for row in output_rows}),
        "unique_page_side_count": len({row["页码版面键"] for row in output_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in output_rows}),
        "auto_task_count": sum(1 for row in output_rows if row["任务来源类型"] == "自动官网辅证任务"),
        "manual_task_count": sum(1 for row in output_rows if row["任务来源类型"] == "P0人工字段任务"),
        "task_source_type_counts": dict(Counter(row["任务来源类型"] for row in output_rows)),
        "page_side_priority_counts": dict(Counter(row["第一闭环页列优先级"] for row in output_rows)),
        "auto_task_action_counts": dict(auto_task_action_counts),
        "school_support_action_counts": dict(school_support_action_counts),
        "manual_execution_batch_counts": dict(Counter(row["执行批次"] for row in output_rows if row["执行批次"])),
        "field_counts": dict(Counter(row["字段名"] for row in output_rows if row["字段名"])),
        "double_review_required_count": sum(1 for row in output_rows if row["是否需要双人复核"] == "true"),
        "pdf_required_count": sum(1 for row in output_rows if row["PDF原页是否必核"] == "true"),
        "hubei_official_required_count": sum(1 for row in output_rows if row["湖北官方侧是否必核"] == "true"),
        "school_support_required_count": sum(1 for row in output_rows if row["高校辅证是否需要复核"] == "true"),
        "school_source_reference_row_count": len(source_file_rows),
        "unique_school_source_file_count": len(source_unique),
        "school_source_file_missing_count": sum(
            1 for row in output_rows if row["最佳官网来源文件是否存在"] == "false_missing_public_source_file"
        ),
        "auto_hint_allowed_count": sum(1 for row in output_rows if row["自动辅证是否可作为核页提示"] == "true"),
        "official_public_plan_page_can_finalize": official["official_public_plan_page_can_finalize"],
        "zspt_platform_can_finalize": official["zspt_platform_can_finalize"],
        "field_writeback_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "policy": {
            "purpose": f"把第一闭环{len(output_rows)}条任务逐条接到{len({row.get('页码版面键') for row in output_rows})}个页列材料、公共高校来源文件SHA和三方核验状态。",
            "public_boundary": "公开表只保存任务状态、公共来源文件SHA、证据编号和门禁，不保存字段读数、页图路径或OCR原文。",
            "no_finalization": "本账本不确认字段事实，不自动写回，不生成学校专业建议。",
        },
    }
    write_json(SUMMARY_OUTPUT, summary)

    print(f"写出 {PUBLIC_OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
