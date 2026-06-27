#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

IMMEDIATE_PACKET = ROOT / "data/working/issue19-field-fact-p0-immediate-review-packet.csv"
CROP_INDEX = ROOT / "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv"
SCHOOL_SIDECAR = ROOT / "data/working/issue19-b0-b1-official-evidence-by-major-line.csv"

OUTPUT = ROOT / "data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-p0-immediate-three-way-closure-public-ledger-summary.json"

LOCAL_OUTPUT_DIR = ROOT / "private" / "review-assets" / "issue19-p0-immediate-three-way-closure"
LOCAL_WORKSHEET = LOCAL_OUTPUT_DIR / "three-way-readings-private-template.csv"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_p0_immediate_three_way_closure_public_ledger"

SCHOOL_GUIDE_BATCHES = {
    "R5-机器候选与高校辅证字段冲突": ("H0-机器高校冲突先核", "1"),
    "R4-机器候选与高校辅证字段一致": ("H1-机器高校一致仍需核PDF和湖北官方", "2"),
    "R3-高校辅证有字段值但机器无规范候选": ("H2-高校补缺线索回看PDF", "3"),
}

FIELDS = [
    "P0即时三方闭环公开账本ID",
    "来源P0字段即时复核包",
    "来源P0裁图证据索引",
    "来源B0B1高校官网辅证旁挂表",
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
    "闭环公开账本总序",
    "即时复核总序",
    "执行总序",
    "执行批次",
    "即时复核阶段",
    "语义多源优先桶",
    "字段名",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "来源页码",
    "版面列",
    "P0字段即时复核任务ID",
    "来源P0字段三方核验任务ID",
    "来源P0字段三方核验执行包ID",
    "专业行原页证据锚点ID",
    "P0即时复核裁图证据索引ID",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图规格SHA256",
    "裁图bbox归一化",
    "裁图bbox像素",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "私有窗口证据编号",
    "窗口文本SHA256",
    "机器候选状态",
    "机器候选置信等级",
    "机器候选与高校辅证关系",
    "高校官网辅证覆盖状态",
    "高校官网证据旁挂ID",
    "高校官网证据强度",
    "高校官网证据匹配状态",
    "高校官网来源状态",
    "高校官网来源文件",
    "高校官网是否可替代湖北官方计划",
    "高校线索复核批次",
    "高校线索复核批次序号",
    "是否有机器规范候选",
    "是否有高校字段线索",
    "是否机器高校可比对",
    "是否机器高校一致",
    "是否机器高校冲突",
    "是否高校补缺线索",
    "是否需要双人复核",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "PDF原页私有核验记录状态",
    "湖北官方私有核验记录状态",
    "高校辅证私有对照状态",
    "三方闭环私有记录状态",
    "人工字段确认表生成状态",
    "闭环公开状态",
    "闭环阻断原因",
    "公开安全策略",
    "下一步",
]

LOCAL_FIELDS = FIELDS + [
    "本地对照用途",
    "机器候选字段值",
    "机器候选规范值",
    "高校官网字段候选值",
    "高校官网字段规范值",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "PDF原页截图或裁图本地位置",
    "湖北官方系统证据本地位置",
    "高校官网或章程证据本地位置",
    "复核人A",
    "复核人B",
    "复核备注",
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
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def source_paths_are_public(value):
    if not value:
        return True
    parts = [part.strip() for part in value.replace("；", ";").split(";") if part.strip()]
    return bool(parts) and all(
        part.startswith("data/external/")
        and not part.startswith("/")
        and "\\" not in part
        and (ROOT / part).exists()
        for part in parts
    )


def school_batch(relation):
    return SCHOOL_GUIDE_BATCHES.get(relation, ("H9-无高校字段线索或待判", "9"))


def local_template_row(public_row, immediate_row):
    return {
        **public_row,
        "本地对照用途": "仅供人工三方闭环时记录字段值和证据位置；不得提交公开仓库。",
        "机器候选字段值": immediate_row.get("机器候选字段值", ""),
        "机器候选规范值": immediate_row.get("机器候选规范值", ""),
        "高校官网字段候选值": immediate_row.get("高校官网字段候选值", ""),
        "高校官网字段规范值": immediate_row.get("高校官网字段规范值", ""),
        "PDF原页人工读数": "",
        "湖北官方字段值": "",
        "高校官网或招生章程字段值": "",
        "字段确认值": "",
        "PDF原页截图或裁图本地位置": "",
        "湖北官方系统证据本地位置": "",
        "高校官网或章程证据本地位置": "",
        "复核人A": "",
        "复核人B": "",
        "复核备注": "",
    }


def build_rows():
    immediate_rows = read_csv(IMMEDIATE_PACKET)
    crop_by_task = {
        row["来源P0字段即时复核任务ID"]: row
        for row in read_csv(CROP_INDEX)
    }
    sidecar_by_id = {
        row["官网证据旁挂ID"]: row
        for row in read_csv(SCHOOL_SIDECAR)
    }

    public_rows = []
    local_rows = []
    for index, row in enumerate(immediate_rows, start=1):
        crop = crop_by_task.get(row["P0字段即时复核任务ID"])
        if not crop:
            raise ValueError(f"裁图证据缺失: {row['P0字段即时复核任务ID']}")
        if crop.get("专业行ID") != row.get("专业行ID") or crop.get("字段名") != row.get("字段名"):
            raise ValueError(f"裁图证据与即时任务不一致: {row['P0字段即时复核任务ID']}")

        sidecar_id = row.get("高校官网证据旁挂ID", "")
        sidecar = sidecar_by_id.get(sidecar_id, {}) if sidecar_id else {}
        if sidecar_id and not sidecar:
            raise ValueError(f"高校官网辅证旁挂缺失: {sidecar_id}")
        source_file = row.get("高校官网字段来源文件", "")
        if not source_paths_are_public(source_file):
            raise ValueError(f"高校官网来源文件不是公开相对路径: {source_file}")

        has_machine = bool(row.get("机器候选规范值"))
        has_school = bool(row.get("高校官网字段候选值"))
        relation = row.get("机器候选与高校辅证关系", "")
        is_agree = relation == "R4-机器候选与高校辅证字段一致"
        is_conflict = relation == "R5-机器候选与高校辅证字段冲突"
        is_fill = relation == "R3-高校辅证有字段值但机器无规范候选"
        is_comparable = is_agree or is_conflict
        guide_batch, guide_order = school_batch(relation)
        school_private_status = (
            "pending_private_school_sidecar_value_review"
            if has_school
            else "not_applicable_no_school_field_value"
        )
        public_row = {
            "P0即时三方闭环公开账本ID": stable_id(
                "P0CLOSURE",
                [row.get("P0字段即时复核任务ID", ""), row.get("专业行ID", ""), row.get("字段名", "")],
            ),
            "来源P0字段即时复核包": "data/working/issue19-field-fact-p0-immediate-review-packet.csv",
            "来源P0裁图证据索引": "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv",
            "来源B0B1高校官网辅证旁挂表": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0字段×三方闭环公开状态",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "闭环公开账本总序": str(index),
            "即时复核总序": row.get("即时复核总序", ""),
            "执行总序": row.get("执行总序", ""),
            "执行批次": row.get("执行批次", ""),
            "即时复核阶段": row.get("即时复核阶段", ""),
            "语义多源优先桶": row.get("语义多源优先桶", ""),
            "字段名": row.get("字段名", ""),
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "P0字段即时复核任务ID": row.get("P0字段即时复核任务ID", ""),
            "来源P0字段三方核验任务ID": row.get("来源P0字段三方核验任务ID", ""),
            "来源P0字段三方核验执行包ID": row.get("来源P0字段三方核验执行包ID", ""),
            "专业行原页证据锚点ID": row.get("专业行原页证据锚点ID", ""),
            "P0即时复核裁图证据索引ID": crop.get("P0即时复核裁图证据索引ID", ""),
            "裁图证据编号": crop.get("裁图证据编号", ""),
            "裁图文件SHA256": crop.get("裁图文件SHA256", ""),
            "裁图规格SHA256": crop.get("裁图规格SHA256", ""),
            "裁图bbox归一化": crop.get("裁图bbox归一化", ""),
            "裁图bbox像素": crop.get("裁图bbox像素", ""),
            "私有页图证据编号": row.get("私有页图证据编号", ""),
            "私有页图SHA256": row.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": row.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": row.get("私有OCR文本SHA256", ""),
            "私有窗口证据编号": row.get("私有窗口证据编号", ""),
            "窗口文本SHA256": row.get("窗口文本SHA256", ""),
            "机器候选状态": row.get("机器候选状态", ""),
            "机器候选置信等级": row.get("机器候选置信等级", ""),
            "机器候选与高校辅证关系": relation,
            "高校官网辅证覆盖状态": row.get("高校官网辅证覆盖状态", ""),
            "高校官网证据旁挂ID": sidecar_id,
            "高校官网证据强度": row.get("高校官网证据强度", ""),
            "高校官网证据匹配状态": row.get("高校官网证据匹配状态", ""),
            "高校官网来源状态": sidecar.get("官网来源状态", ""),
            "高校官网来源文件": source_file,
            "高校官网是否可替代湖北官方计划": sidecar.get("能否替代湖北官方计划", ""),
            "高校线索复核批次": guide_batch,
            "高校线索复核批次序号": guide_order,
            "是否有机器规范候选": str(has_machine).lower(),
            "是否有高校字段线索": str(has_school).lower(),
            "是否机器高校可比对": str(is_comparable).lower(),
            "是否机器高校一致": str(is_agree).lower(),
            "是否机器高校冲突": str(is_conflict).lower(),
            "是否高校补缺线索": str(is_fill).lower(),
            "是否需要双人复核": row.get("是否需要双人复核", ""),
            "PDF原页核页状态": row.get("PDF原页核页状态", ""),
            "湖北官方系统或省招办计划核验状态": row.get("湖北官方系统或省招办计划核验状态", ""),
            "高校官网或招生章程辅证状态": row.get("高校官网或招生章程辅证状态", ""),
            "三方字段一致性状态": row.get("三方字段一致性状态", ""),
            "字段事实写回状态": row.get("字段事实写回状态", ""),
            "PDF原页私有核验记录状态": "pending_private_pdf_page_review",
            "湖北官方私有核验记录状态": "pending_private_hubei_official_review",
            "高校辅证私有对照状态": school_private_status,
            "三方闭环私有记录状态": "pending_private_three_way_closure",
            "人工字段确认表生成状态": "blocked_until_private_three_way_closure",
            "闭环公开状态": "pending_private_three_way_review_not_final",
            "闭环阻断原因": (
                "PDF原页、湖北官方系统或省招办计划、高校官网或章程尚未在私有记录中三方闭环；"
                "公开账本不保存具体字段内容，不能写回主表或进入推荐。"
            ),
            "公开安全策略": "公开账本只保存任务ID、证据编号、SHA、bbox、状态和门禁；具体字段内容、本地裁图路径和复核备注只在本地私有模板。",
            "下一步": "按闭环公开账本总序回看裁图和PDF原页；再录入私有三方核验记录；闭环后另建人工确认表。",
        }
        public_rows.append(public_row)
        local_rows.append(local_template_row(public_row, row))
    return public_rows, local_rows


def write_summary(rows):
    field_counts = Counter(row["字段名"] for row in rows)
    batch_counts = Counter(row["执行批次"] for row in rows)
    stage_counts = Counter(row["即时复核阶段"] for row in rows)
    relation_counts = Counter(row["机器候选与高校辅证关系"] for row in rows)
    school_guide_counts = Counter(row["高校线索复核批次"] for row in rows)
    school_strength_counts = Counter(row["高校官网证据强度"] for row in rows if row["高校官网证据强度"])
    school_match_counts = Counter(row["高校官网证据匹配状态"] for row in rows if row["高校官网证据匹配状态"])
    page_counts = Counter(row["来源页码"] for row in rows)
    school_counts = Counter(row["院校代码"] for row in rows)
    source_file_counts = Counter(row["高校官网来源文件"] for row in rows if row["高校官网来源文件"])

    summary = {
        "status": "issue19_p0_immediate_three_way_closure_public_ledger_not_final",
        "generated_by": "build_issue19_p0_immediate_three_way_closure_ledger.py",
        "source_immediate_packet": "data/working/issue19-field-fact-p0-immediate-review-packet.csv",
        "source_crop_evidence_index": "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv",
        "source_school_sidecar": "data/working/issue19-b0-b1-official-evidence-by-major-line.csv",
        "output_table": "data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv",
        "row_grain": "逐专业招生明细×P0字段×三方闭环公开状态",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "local_private_template_generated": True,
        "unique_public_ledger_id_count": len({row["P0即时三方闭环公开账本ID"] for row in rows}),
        "unique_immediate_task_id_count": len({row["P0字段即时复核任务ID"] for row in rows}),
        "unique_source_triage_task_id_count": len({row["来源P0字段三方核验任务ID"] for row in rows}),
        "unique_crop_index_id_count": len({row["P0即时复核裁图证据索引ID"] for row in rows}),
        "unique_crop_evidence_id_count": len({row["裁图证据编号"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_major_field_pair_count": len({(row["专业行ID"], row["字段名"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "unique_school_code_count": len({row["院校代码"] for row in rows}),
        "field_counts": dict(field_counts),
        "execution_batch_counts": dict(batch_counts),
        "immediate_stage_counts": dict(stage_counts),
        "crosssource_relation_counts": dict(relation_counts),
        "school_guide_batch_counts": dict(school_guide_counts),
        "school_evidence_strength_counts": dict(school_strength_counts),
        "school_match_status_counts": dict(school_match_counts),
        "school_field_clue_count": sum(row["是否有高校字段线索"] == "true" for row in rows),
        "machine_candidate_present_count": sum(row["是否有机器规范候选"] == "true" for row in rows),
        "machine_school_comparable_count": sum(row["是否机器高校可比对"] == "true" for row in rows),
        "machine_school_agree_count": sum(row["是否机器高校一致"] == "true" for row in rows),
        "machine_school_conflict_count": sum(row["是否机器高校冲突"] == "true" for row in rows),
        "school_fill_clue_count": sum(row["是否高校补缺线索"] == "true" for row in rows),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in rows),
        "school_sidecar_cannot_replace_hubei_count": sum(
            row["高校官网是否可替代湖北官方计划"] == "false" for row in rows
        ),
        "pdf_private_review_pending_count": sum(
            row["PDF原页私有核验记录状态"] == "pending_private_pdf_page_review" for row in rows
        ),
        "hubei_private_review_pending_count": sum(
            row["湖北官方私有核验记录状态"] == "pending_private_hubei_official_review" for row in rows
        ),
        "school_private_review_pending_count": sum(
            row["高校辅证私有对照状态"] == "pending_private_school_sidecar_value_review" for row in rows
        ),
        "three_way_private_closure_pending_count": sum(
            row["三方闭环私有记录状态"] == "pending_private_three_way_closure" for row in rows
        ),
        "manual_confirmation_table_blocked_count": sum(
            row["人工字段确认表生成状态"] == "blocked_until_private_three_way_closure" for row in rows
        ),
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
        "unique_school_source_file_count": len(source_file_counts),
        "top_pdf_pages": dict(page_counts.most_common(30)),
        "top_school_codes": dict(school_counts.most_common(30)),
        "public_safety_note": "公开账本只保存闭环状态、任务ID、证据编号、SHA、bbox和门禁；不保存具体字段内容、本地裁图路径、复核备注、院校名、专业名、专业代号或专业组代码。",
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    public_rows, local_rows = build_rows()
    write_csv(OUTPUT, public_rows, FIELDS)
    write_csv(LOCAL_WORKSHEET, local_rows, LOCAL_FIELDS)
    write_summary(public_rows)
    print(f"写出P0即时三方闭环公开账本：{OUTPUT.relative_to(ROOT)}，{len(public_rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"本地私有三方核验模板已生成：{LOCAL_WORKSHEET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
