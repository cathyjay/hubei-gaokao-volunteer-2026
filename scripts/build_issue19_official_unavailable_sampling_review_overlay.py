#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXECUTION_DETAIL = (
    ROOT / "data/working/issue19-official-unavailable-sampling-execution-detail.csv"
)
EXECUTION_DETAIL_SUMMARY = (
    ROOT / "data/working/issue19-official-unavailable-sampling-execution-detail-summary.json"
)

PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-official-unavailable-sampling-review-overlay"
)
PRIVATE_OVERLAY = PRIVATE_OUTPUT_DIR / "sampling-review-overlay.csv"

OUTPUT = (
    ROOT / "data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    ROOT
    / "data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
DATA_STAGE = "issue19_official_unavailable_sampling_review_overlay_public_ledger"
PRIVATE_EVIDENCE_ID = "issue19-official-unavailable-sampling-review-overlay-csv"


FIELDS = [
    "官方不可得抽样Overlay公开账本ID",
    "来源官方不可得抽样执行明细",
    "来源私有抽样复核Overlay",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许写回字段事实",
    "来源官方不可得抽样执行明细ID",
    "专业行ID",
    "专业组出现ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "执行类别",
    "执行优先级",
    "风险等级",
    "官网辅证自动动作",
    "是否100%人工核验",
    "是否抽样核验",
    "是否低风险样本",
    "是否需要双人复核",
    "抽样策略",
    "样本序号",
    "样本最低明细数",
    "私有Overlay证据编号",
    "私有OverlayCSV_SHA256",
    "私有Overlay记录SHA256",
    "私有Overlay记录是否存在",
    "私有Overlay记录缺失数",
    "PDF原页已填字段数",
    "湖北官方侧已填字段数",
    "高校辅证已填字段数",
    "三方一致性可评估",
    "抽检失败状态",
    "升级状态",
    "首轮复核状态",
    "次轮复核状态",
    "字段事实写回状态",
    "Overlay进度桶",
    "公开安全策略",
    "下一步",
]


CONTEXT_FIELDS = [
    "来源官方不可得抽样执行明细ID",
    "来源稳定基座自动交叉核验任务ID",
    "来源逐专业证据路由ID",
    "来源招生明细总工作台ID",
    "来源湖北官方活体复查",
    "来源期号",
    "来源PDF_SHA256",
    "执行类别",
    "执行优先级",
    "风险等级",
    "抽样策略",
    "样本选择原因",
    "样本序号",
    "样本最低明细数",
    "是否100%人工核验",
    "是否抽样核验",
    "是否低风险样本",
    "院校代码",
    "院校名称OCR",
    "专业行ID",
    "专业组出现ID",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "必核字段",
    "字段差异标记",
    "官网辅证自动动作",
    "OCR专业计划数候选",
    "OCR学费候选",
    "OCR再选科目候选",
    "最佳官网专业名称",
    "最佳官网专业代号",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "最佳官网来源文件",
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "疑似OCR把学费读入计划数",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方一致性状态",
    "字段事实写回状态",
    "是否需要双人复核",
    "升级触发器",
    "升级范围",
    "当前用途边界",
    "下一步",
]


PRIVATE_FIELDS = [
    "官方不可得抽样OverlayID",
    "来源执行明细行SHA256",
    "执行明细锁定",
    "来源官方不可得抽样执行明细ID",
    "来源稳定基座自动交叉核验任务ID",
    "来源逐专业证据路由ID",
    "来源招生明细总工作台ID",
    "来源湖北官方活体复查",
    "来源期号",
    "来源PDF_SHA256",
    "执行类别",
    "执行优先级",
    "风险等级",
    "抽样策略",
    "样本选择原因",
    "样本序号",
    "样本最低明细数",
    "是否100%人工核验",
    "是否抽样核验",
    "是否低风险样本",
    "院校代码",
    "院校名称OCR",
    "专业行ID",
    "专业组出现ID",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "必核字段",
    "字段差异标记",
    "官网辅证自动动作",
    "OCR专业计划数候选",
    "OCR学费候选",
    "OCR再选科目候选",
    "最佳官网专业名称",
    "最佳官网专业代号",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "最佳官网来源文件",
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "疑似OCR把学费读入计划数",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方一致性状态",
    "字段事实写回状态",
    "是否需要双人复核",
    "升级触发器",
    "升级范围",
    "当前用途边界",
    "下一步",
    "PDF原页证据编号",
    "PDF原页证据SHA256",
    "PDF原页人工读数_专业名称",
    "PDF原页人工读数_专业计划数",
    "PDF原页人工读数_学费",
    "PDF原页人工读数_再选科目",
    "PDF原页人工读数_备注限制",
    "PDF原页记录状态",
    "湖北官方证据编号",
    "湖北官方证据SHA256",
    "湖北官方字段值_专业名称",
    "湖北官方字段值_专业计划数",
    "湖北官方字段值_学费",
    "湖北官方字段值_再选科目",
    "湖北官方字段值_备注限制",
    "湖北官方记录状态",
    "高校辅证证据编号",
    "高校辅证证据SHA256",
    "高校辅证字段值_专业名称",
    "高校辅证字段值_专业计划数",
    "高校辅证字段值_学费",
    "高校辅证字段值_再选科目",
    "高校辅证字段值_备注限制",
    "高校辅证记录状态",
    "三方一致性人工结论",
    "是否抽检失败",
    "失败升级范围",
    "一审复核人",
    "一审时间",
    "一审记录",
    "二审复核人",
    "二审时间",
    "二审记录",
    "复核结论",
    "人工备注",
    "字段事实是否允许写回",
    "人工是否允许作为志愿推荐依据",
    "人工是否最终可用",
    "人工记录锁定状态",
    "人工记录版本",
    "updated_at",
]


PDF_FIELDS = [
    "PDF原页人工读数_专业名称",
    "PDF原页人工读数_专业计划数",
    "PDF原页人工读数_学费",
    "PDF原页人工读数_再选科目",
    "PDF原页人工读数_备注限制",
]
HUBEI_OFFICIAL_FIELDS = [
    "湖北官方字段值_专业名称",
    "湖北官方字段值_专业计划数",
    "湖北官方字段值_学费",
    "湖北官方字段值_再选科目",
    "湖北官方字段值_备注限制",
]
SCHOOL_SUPPORT_FIELDS = [
    "高校辅证字段值_专业名称",
    "高校辅证字段值_专业计划数",
    "高校辅证字段值_学费",
    "高校辅证字段值_再选科目",
    "高校辅证字段值_备注限制",
]
MANUAL_FIELDS = [
    "PDF原页证据编号",
    "PDF原页证据SHA256",
    "PDF原页人工读数_专业名称",
    "PDF原页人工读数_专业计划数",
    "PDF原页人工读数_学费",
    "PDF原页人工读数_再选科目",
    "PDF原页人工读数_备注限制",
    "PDF原页记录状态",
    "湖北官方证据编号",
    "湖北官方证据SHA256",
    "湖北官方字段值_专业名称",
    "湖北官方字段值_专业计划数",
    "湖北官方字段值_学费",
    "湖北官方字段值_再选科目",
    "湖北官方字段值_备注限制",
    "湖北官方记录状态",
    "高校辅证证据编号",
    "高校辅证证据SHA256",
    "高校辅证字段值_专业名称",
    "高校辅证字段值_专业计划数",
    "高校辅证字段值_学费",
    "高校辅证字段值_再选科目",
    "高校辅证字段值_备注限制",
    "高校辅证记录状态",
    "三方一致性人工结论",
    "是否抽检失败",
    "失败升级范围",
    "一审复核人",
    "一审时间",
    "一审记录",
    "二审复核人",
    "二审时间",
    "二审记录",
    "复核结论",
    "人工备注",
    "字段事实是否允许写回",
    "人工是否允许作为志愿推荐依据",
    "人工是否最终可用",
    "人工记录锁定状态",
    "人工记录版本",
    "updated_at",
]
DEFAULT_GATE_FIELDS = {
    "字段事实是否允许写回",
    "人工是否允许作为志愿推荐依据",
    "人工是否最终可用",
}


COMPLETE_STATUS_TOKENS = {
    "done",
    "complete",
    "completed",
    "checked",
    "verified",
    "matched",
    "not_applicable",
    "na",
    "已完成",
    "完成",
    "一致",
    "不适用",
}
TRUE_TOKENS = {"true", "yes", "y", "1", "是", "失败", "需升级"}


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


def row_sha(row, fields):
    text = "\n".join(f"{field}={row.get(field, '')}" for field in fields)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def filled(value):
    return bool(str(value or "").strip())


def is_true(value):
    return str(value or "").strip().lower() in TRUE_TOKENS


def status_complete(value):
    text = str(value or "").strip().lower()
    return bool(text) and (
        text in COMPLETE_STATUS_TOKENS
        or any(token in text for token in ["done", "complete", "verified", "matched"])
    )


def manual_cell_count(row):
    return sum(
        1
        for field in MANUAL_FIELDS
        if field != "人工记录版本"
        and field not in DEFAULT_GATE_FIELDS
        and filled(row.get(field))
    )


def build_private_row(source_row):
    execution_id = source_row.get("官方不可得抽样执行明细ID", "")
    detail_sha = row_sha(source_row, sorted(source_row))
    row = {
        "官方不可得抽样OverlayID": stable_id(
            "SAMPLINGOVERLAY",
            [execution_id, detail_sha],
        ),
        "来源执行明细行SHA256": detail_sha,
        "执行明细锁定": "true",
    }
    for field in CONTEXT_FIELDS:
        if field == "来源官方不可得抽样执行明细ID":
            row[field] = execution_id
        else:
            row[field] = source_row.get(field, "")
    row.update({
        "PDF原页证据编号": "",
        "PDF原页证据SHA256": "",
        "PDF原页人工读数_专业名称": "",
        "PDF原页人工读数_专业计划数": "",
        "PDF原页人工读数_学费": "",
        "PDF原页人工读数_再选科目": "",
        "PDF原页人工读数_备注限制": "",
        "PDF原页记录状态": "",
        "湖北官方证据编号": "",
        "湖北官方证据SHA256": "",
        "湖北官方字段值_专业名称": "",
        "湖北官方字段值_专业计划数": "",
        "湖北官方字段值_学费": "",
        "湖北官方字段值_再选科目": "",
        "湖北官方字段值_备注限制": "",
        "湖北官方记录状态": "",
        "高校辅证证据编号": "",
        "高校辅证证据SHA256": "",
        "高校辅证字段值_专业名称": "",
        "高校辅证字段值_专业计划数": "",
        "高校辅证字段值_学费": "",
        "高校辅证字段值_再选科目": "",
        "高校辅证字段值_备注限制": "",
        "高校辅证记录状态": "",
        "三方一致性人工结论": "",
        "是否抽检失败": "",
        "失败升级范围": "",
        "一审复核人": "",
        "一审时间": "",
        "一审记录": "",
        "二审复核人": "",
        "二审时间": "",
        "二审记录": "",
        "复核结论": "",
        "人工备注": "",
        "字段事实是否允许写回": "false",
        "人工是否允许作为志愿推荐依据": "false",
        "人工是否最终可用": "false",
        "人工记录锁定状态": "",
        "人工记录版本": "1",
        "updated_at": "",
    })
    return row


def merge_existing_manual_values(new_row, existing_row):
    preserved_count = 0
    if not existing_row:
        return new_row, preserved_count
    for field in MANUAL_FIELDS:
        if field == "人工记录版本":
            continue
        old_value = existing_row.get(field, "")
        if field in DEFAULT_GATE_FIELDS and str(old_value).strip().lower() == "false":
            continue
        if filled(old_value):
            new_row[field] = old_value
            preserved_count += 1
    if not filled(new_row.get("人工记录版本")):
        new_row["人工记录版本"] = existing_row.get("人工记录版本") or "1"
    return new_row, preserved_count


def filled_count(row, fields):
    return sum(1 for field in fields if filled(row.get(field)))


def overlay_progress_bucket(row):
    if manual_cell_count(row) == 0:
        return "R0-Overlay已生成未填写"
    if (
        filled_count(row, PDF_FIELDS) > 0
        and filled_count(row, HUBEI_OFFICIAL_FIELDS) > 0
        and filled(row.get("三方一致性人工结论"))
        and filled(row.get("一审记录"))
        and (
            row.get("是否需要双人复核") != "true"
            or filled(row.get("二审记录"))
        )
        and filled(row.get("复核结论"))
    ):
        return "R3-Overlay核心记录已齐待事实复查"
    return "R1-Overlay已有部分填写"


def build_public_row(private_row, private_file_sha):
    execution_id = private_row.get("来源官方不可得抽样执行明细ID", "")
    pdf_filled = filled_count(private_row, PDF_FIELDS)
    hubei_filled = filled_count(private_row, HUBEI_OFFICIAL_FIELDS)
    school_filled = filled_count(private_row, SCHOOL_SUPPORT_FIELDS)
    tri_assessable = (
        pdf_filled > 0
        and hubei_filled > 0
        and filled(private_row.get("三方一致性人工结论"))
    )
    sampling_failed = is_true(private_row.get("是否抽检失败"))
    escalation_required = sampling_failed or filled(private_row.get("失败升级范围"))
    first_review_done = status_complete(private_row.get("一审记录")) or filled(
        private_row.get("一审记录")
    )
    second_review_done = status_complete(private_row.get("二审记录")) or filled(
        private_row.get("二审记录")
    )
    return {
        "官方不可得抽样Overlay公开账本ID": stable_id(
            "SAMPLINGOVERLAYPROG",
            [execution_id, PRIVATE_EVIDENCE_ID],
        ),
        "来源官方不可得抽样执行明细": (
            "data/working/issue19-official-unavailable-sampling-execution-detail.csv"
        ),
        "来源私有抽样复核Overlay": "local_sampling_review_overlay_not_public",
        "来源期号": private_row.get("来源期号", ""),
        "来源PDF_SHA256": private_row.get("来源PDF_SHA256", ""),
        "数据阶段": DATA_STAGE,
        "主表粒度": "逐专业招生明细",
        "任务粒度": "官方不可得抽样执行明细×人工复核Overlay进度",
        "最终可用": "false",
        "可进入下一阶段": "false",
        "是否允许作为志愿推荐依据": "false",
        "是否允许生成学校专业建议": "false",
        "是否允许自动写回主表": "false",
        "是否允许官网证据替代湖北官方计划": "false",
        "是否允许写回字段事实": "false",
        "来源官方不可得抽样执行明细ID": execution_id,
        "专业行ID": private_row.get("专业行ID", ""),
        "专业组出现ID": private_row.get("专业组出现ID", ""),
        "来源页码": private_row.get("来源页码", ""),
        "版面列": private_row.get("版面列", ""),
        "页码版面键": private_row.get("页码版面键", ""),
        "执行类别": private_row.get("执行类别", ""),
        "执行优先级": private_row.get("执行优先级", ""),
        "风险等级": private_row.get("风险等级", ""),
        "官网辅证自动动作": private_row.get("官网辅证自动动作", ""),
        "是否100%人工核验": private_row.get("是否100%人工核验", ""),
        "是否抽样核验": private_row.get("是否抽样核验", ""),
        "是否低风险样本": private_row.get("是否低风险样本", ""),
        "是否需要双人复核": private_row.get("是否需要双人复核", ""),
        "抽样策略": private_row.get("抽样策略", ""),
        "样本序号": private_row.get("样本序号", ""),
        "样本最低明细数": private_row.get("样本最低明细数", ""),
        "私有Overlay证据编号": PRIVATE_EVIDENCE_ID,
        "私有OverlayCSV_SHA256": private_file_sha,
        "私有Overlay记录SHA256": row_sha(private_row, PRIVATE_FIELDS),
        "私有Overlay记录是否存在": "true",
        "私有Overlay记录缺失数": "0",
        "PDF原页已填字段数": str(pdf_filled),
        "湖北官方侧已填字段数": str(hubei_filled),
        "高校辅证已填字段数": str(school_filled),
        "三方一致性可评估": "true" if tri_assessable else "false",
        "抽检失败状态": "failed" if sampling_failed else "not_evaluated",
        "升级状态": "required" if escalation_required else "not_evaluated",
        "首轮复核状态": "done" if first_review_done else "pending",
        "次轮复核状态": (
            "pending"
            if private_row.get("是否需要双人复核") == "true" and not second_review_done
            else "done"
            if second_review_done
            else "not_required_yet"
        ),
        "字段事实写回状态": "blocked_until_private_overlay_pdf_hubei_review_closed",
        "Overlay进度桶": overlay_progress_bucket(private_row),
        "公开安全策略": (
            "公开表只保存抽样复核进度、门禁状态、证据编号和SHA；"
            "不公开学校专业明细、字段读数、人员字段或备注正文。"
        ),
        "下一步": (
            "在本地抽样复核Overlay录入PDF原页、湖北官方侧和必要高校辅证；"
            "抽检失败时按同页列、同校或同组升级边界扩大人工核验。"
        ),
    }


def build_rows():
    execution_rows = read_csv(EXECUTION_DETAIL)
    existing_by_execution_id = {}
    if PRIVATE_OVERLAY.exists():
        for row in read_csv(PRIVATE_OVERLAY):
            execution_id = row.get("来源官方不可得抽样执行明细ID", "")
            if execution_id:
                existing_by_execution_id[execution_id] = row

    private_rows = []
    preserved_manual_cell_count = 0
    for source_row in execution_rows:
        execution_id = source_row.get("官方不可得抽样执行明细ID", "")
        new_row = build_private_row(source_row)
        new_row, preserved_count = merge_existing_manual_values(
            new_row,
            existing_by_execution_id.get(execution_id, {}),
        )
        preserved_manual_cell_count += preserved_count
        private_rows.append(new_row)

    write_csv(PRIVATE_OVERLAY, private_rows, PRIVATE_FIELDS)
    private_file_sha = sha256(PRIVATE_OVERLAY)
    public_rows = [build_public_row(row, private_file_sha) for row in private_rows]
    return execution_rows, private_rows, public_rows, preserved_manual_cell_count


def main():
    execution_summary = json.loads(EXECUTION_DETAIL_SUMMARY.read_text(encoding="utf-8"))
    execution_rows, private_rows, public_rows, preserved_manual_cell_count = build_rows()
    write_csv(OUTPUT, public_rows, FIELDS)

    action_counts = Counter(row["官网辅证自动动作"] for row in public_rows)
    execution_category_counts = Counter(row["执行类别"] for row in public_rows)
    risk_level_counts = Counter(row["风险等级"] for row in public_rows)
    progress_bucket_counts = Counter(row["Overlay进度桶"] for row in public_rows)
    summary = {
        "status": "issue19_official_unavailable_sampling_review_overlay_public_ledger_not_final",
        "generated_by": "build_issue19_official_unavailable_sampling_review_overlay.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": public_rows[0]["来源PDF_SHA256"] if public_rows else "",
        "source_execution_detail": (
            "data/working/issue19-official-unavailable-sampling-execution-detail.csv"
        ),
        "source_execution_detail_summary": (
            "data/working/issue19-official-unavailable-sampling-execution-detail-summary.json"
        ),
        "source_private_sampling_review_overlay": "local_sampling_review_overlay_not_public",
        "output_table": (
            "data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv"
        ),
        "row_grain": "逐专业招生明细",
        "row_count": len(public_rows),
        "unique_public_ledger_id_count": len({
            row["官方不可得抽样Overlay公开账本ID"] for row in public_rows
        }),
        "unique_execution_detail_id_count": len({
            row["来源官方不可得抽样执行明细ID"] for row in public_rows
        }),
        "unique_major_line_count": len({
            row["专业行ID"] for row in public_rows if row["专业行ID"]
        }),
        "private_overlay_record_count": len(private_rows),
        "private_overlay_missing_record_count": sum(
            as_int(row["私有Overlay记录缺失数"]) for row in public_rows
        ),
        "private_overlay_csv_sha256": sha256(PRIVATE_OVERLAY),
        "preserved_manual_cell_count": preserved_manual_cell_count,
        "pdf_page_filled_field_count": sum(
            as_int(row["PDF原页已填字段数"]) for row in public_rows
        ),
        "hubei_official_filled_field_count": sum(
            as_int(row["湖北官方侧已填字段数"]) for row in public_rows
        ),
        "school_support_filled_field_count": sum(
            as_int(row["高校辅证已填字段数"]) for row in public_rows
        ),
        "pdf_page_record_filled_detail_count": sum(
            as_int(row["PDF原页已填字段数"]) > 0 for row in public_rows
        ),
        "hubei_official_record_filled_detail_count": sum(
            as_int(row["湖北官方侧已填字段数"]) > 0 for row in public_rows
        ),
        "school_support_record_filled_detail_count": sum(
            as_int(row["高校辅证已填字段数"]) > 0 for row in public_rows
        ),
        "tri_consistency_assessable_count": sum(
            row["三方一致性可评估"] == "true" for row in public_rows
        ),
        "sampling_failure_count": sum(
            row["抽检失败状态"] == "failed" for row in public_rows
        ),
        "escalation_required_count": sum(
            row["升级状态"] == "required" for row in public_rows
        ),
        "first_review_done_count": sum(
            row["首轮复核状态"] == "done" for row in public_rows
        ),
        "second_review_done_count": sum(
            row["次轮复核状态"] == "done" for row in public_rows
        ),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "high_risk_100pct_detail_count": sum(
            row["是否100%人工核验"] == "true" for row in public_rows
        ),
        "c2_sample_detail_count": sum(
            row["官网辅证自动动作"] == "C2-强辅证抽检并等待湖北官方闭环"
            for row in public_rows
        ),
        "p3_sample_detail_count": sum(
            row["官网辅证自动动作"] == "P3-低风险抽检但非最终"
            for row in public_rows
        ),
        "double_review_required_count": sum(
            row["是否需要双人复核"] == "true" for row in public_rows
        ),
        "action_counts": dict(action_counts),
        "execution_category_counts": dict(execution_category_counts),
        "risk_level_counts": dict(risk_level_counts),
        "progress_bucket_counts": dict(progress_bucket_counts),
        "source_execution_detail_counts": {
            "row_count": execution_summary.get("row_count"),
            "high_risk_100pct_detail_count": execution_summary.get(
                "high_risk_100pct_detail_count"
            ),
            "c2_sample_detail_count": execution_summary.get("c2_sample_detail_count"),
            "p3_sample_detail_count": execution_summary.get("p3_sample_detail_count"),
            "double_review_required_count": execution_summary.get(
                "double_review_required_count"
            ),
        },
        "safety_note": (
            "公开账本只保存抽样复核进度、门禁状态、证据编号和SHA；"
            "字段读数、湖北官方侧值、高校辅证值和备注正文只留在本地私有Overlay。"
        ),
        "policy": {
            "official_priority": "湖北官方系统或省招办计划仍是定稿源；高校侧证据只能作为辅证和抽检线索。",
            "review_flow": f"{len(public_rows)}条抽样执行明细先在本地Overlay完成PDF原页、湖北官方侧、高校辅证三方复核。",
            "failure_escalation": "抽检失败时按执行明细中的同页列、同校或同组边界升级到100%人工核验。",
            "boundary": "本账本不确认字段、不写回、不生成学校专业建议或志愿推荐。",
        },
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出本地抽样复核Overlay：{PRIVATE_OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
