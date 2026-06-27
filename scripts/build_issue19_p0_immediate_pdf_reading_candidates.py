#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIELD_CONFIRM_LEDGER = ROOT / "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv"
CROP_OCR_AUDIT = ROOT / "data/working/issue19-p0-immediate-crop-ocr-public-audit.csv"
PAGE_REVIEW_PACKETS = ROOT / "data/working/issue19-p0-immediate-page-review-packets.csv"
PRIVATE_CROP_OCR_READING = (
    ROOT / "private/review-assets/issue19-p0-immediate-crop-ocr-audit/crop-ocr-readings-private.csv"
)

OUTPUT = ROOT / "data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit-summary.json"

PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-p0-immediate-pdf-reading-candidates"
PRIVATE_OUTPUT = PRIVATE_OUTPUT_DIR / "pdf-reading-candidates-private.csv"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_p0_immediate_pdf_reading_candidate_public_audit"


FIELDS = [
    "P0即时PDF原页候选公开审计ID",
    "来源P0即时字段确认公开账本",
    "来源P0即时裁图OCR公开审计",
    "来源P0即时按页核页包",
    "来源私有裁图OCR读数候选",
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
    "PDF原页候选公开审计总序",
    "字段确认公开账本总序",
    "裁图OCR公开审计总序",
    "P0字段即时复核任务ID",
    "P0即时字段确认公开账本ID",
    "P0即时裁图OCR公开审计ID",
    "P0即时按页核页包ID",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "字段名",
    "来源页码",
    "版面列",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图规格SHA256",
    "裁图bbox归一化",
    "裁图bbox像素",
    "私有PDF原页候选记录证据编号",
    "私有PDF原页候选记录状态",
    "PDF原页候选审阅桶",
    "PDF原页候选来源状态",
    "PDF原页候选置信等级",
    "裁图OCR候选状态",
    "裁图OCR三方辅助桶",
    "裁图OCR与机器候选关系",
    "裁图OCR与高校辅证关系",
    "是否已有私有PDF原页候选",
    "是否候选与机器线索一致",
    "是否候选与机器线索冲突",
    "是否候选与高校线索一致",
    "是否候选与高校线索冲突",
    "是否有机器规范线索",
    "是否有高校字段线索",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "是否可自动写入人工读数",
    "是否仍需PDF原页人工核页",
    "是否仍需湖北官方核验",
    "是否仍需高校辅证核验",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_FIELDS = FIELDS + [
    "PDF原页私有候选字段读数",
    "PDF原页私有候选规范读数",
    "PDF原页私有候选来源说明",
    "裁图OCR候选行文本",
    "裁图OCR候选行序号",
    "裁图OCR候选x中心",
    "裁图OCR候选y中心",
    "裁图OCR候选置信度",
    "裁图OCR候选距目标行y",
    "裁图OCR全部候选短摘",
    "机器候选字段读数",
    "机器候选规范读数",
    "高校官网字段候选读数",
    "高校官网字段规范读数",
    "私有OCR图片本地路径",
    "候选不得自动写回声明",
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


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def bool_text(value):
    return "true" if str(value).strip().lower() == "true" else "false"


def candidate_bucket(row):
    has_candidate = row.get("是否裁图OCR有可比候选") == "true"
    has_conflict = (
        row.get("是否裁图OCR与机器候选冲突") == "true"
        or row.get("是否裁图OCR与高校辅证冲突") == "true"
    )
    has_match = (
        row.get("是否裁图OCR与机器候选一致") == "true"
        or row.get("是否裁图OCR与高校辅证一致") == "true"
    )
    if not has_candidate:
        return "P3-无稳定候选需人工看图"
    if has_conflict:
        return "P0-候选冲突优先核图"
    if has_match:
        return "P1-候选与既有线索一致仍需核官方"
    return "P2-有候选但需人工确认"


def candidate_source_status(row):
    if row.get("是否裁图OCR有可比候选") == "true":
        return "private_crop_ocr_candidate_available"
    return "private_crop_ocr_candidate_unavailable"


def needs_direct_image_review(row):
    return "true" if candidate_bucket(row) in {
        "P0-候选冲突优先核图",
        "P3-无稳定候选需人工看图",
    } else "false"


def counter_dict(rows, field):
    return dict(Counter(row[field] for row in rows))


def build_rows():
    confirm_rows = read_csv(FIELD_CONFIRM_LEDGER)
    crop_ocr_rows = read_csv(CROP_OCR_AUDIT)
    private_ocr_rows = read_csv(PRIVATE_CROP_OCR_READING)
    packet_rows = read_csv(PAGE_REVIEW_PACKETS)

    crop_ocr_by_task = {row["P0字段即时复核任务ID"]: row for row in crop_ocr_rows}
    private_ocr_by_task = {row["P0字段即时复核任务ID"]: row for row in private_ocr_rows}
    packet_by_page_side = {(row["来源页码"], row["版面列"]): row for row in packet_rows}

    public_rows = []
    private_rows = []
    for index, row in enumerate(confirm_rows, start=1):
        task_id = row["P0字段即时复核任务ID"]
        crop_ocr = crop_ocr_by_task[task_id]
        private_ocr = private_ocr_by_task[task_id]
        packet = packet_by_page_side[(row["来源页码"], row["版面列"])]
        public_id = stable_id("P0PDFCAND", [task_id, row["裁图证据编号"], row["字段名"]])
        private_evidence_id = f"PRIVATEPDFCAND-{public_id}"
        has_private_candidate = crop_ocr["是否裁图OCR有可比候选"] == "true"
        public_row = {
            "P0即时PDF原页候选公开审计ID": public_id,
            "来源P0即时字段确认公开账本": "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv",
            "来源P0即时裁图OCR公开审计": "data/working/issue19-p0-immediate-crop-ocr-public-audit.csv",
            "来源P0即时按页核页包": "data/working/issue19-p0-immediate-page-review-packets.csv",
            "来源私有裁图OCR读数候选": "private_crop_ocr_reading_candidates_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0字段×PDF原页读数候选公开状态",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "PDF原页候选公开审计总序": str(index),
            "字段确认公开账本总序": row["字段确认公开账本总序"],
            "裁图OCR公开审计总序": crop_ocr["裁图OCR公开审计总序"],
            "P0字段即时复核任务ID": task_id,
            "P0即时字段确认公开账本ID": row["P0即时字段确认公开账本ID"],
            "P0即时裁图OCR公开审计ID": row["P0即时裁图OCR公开审计ID"],
            "P0即时按页核页包ID": packet["P0即时按页核页包ID"],
            "专业行ID": row["专业行ID"],
            "专业组出现ID": row["专业组出现ID"],
            "院校代码": row["院校代码"],
            "字段名": row["字段名"],
            "来源页码": row["来源页码"],
            "版面列": row["版面列"],
            "裁图证据编号": row["裁图证据编号"],
            "裁图文件SHA256": row["裁图文件SHA256"],
            "裁图规格SHA256": row["裁图规格SHA256"],
            "裁图bbox归一化": row["裁图bbox归一化"],
            "裁图bbox像素": row["裁图bbox像素"],
            "私有PDF原页候选记录证据编号": private_evidence_id,
            "私有PDF原页候选记录状态": (
                "private_pdf_reading_candidate_seeded"
                if has_private_candidate
                else "private_pdf_reading_candidate_unavailable_needs_manual_image_review"
            ),
            "PDF原页候选审阅桶": candidate_bucket(crop_ocr),
            "PDF原页候选来源状态": candidate_source_status(crop_ocr),
            "PDF原页候选置信等级": crop_ocr["裁图OCR候选置信等级"],
            "裁图OCR候选状态": crop_ocr["裁图OCR候选状态"],
            "裁图OCR三方辅助桶": crop_ocr["裁图OCR三方辅助桶"],
            "裁图OCR与机器候选关系": crop_ocr["裁图OCR与机器候选关系"],
            "裁图OCR与高校辅证关系": crop_ocr["裁图OCR与高校辅证关系"],
            "是否已有私有PDF原页候选": "true" if has_private_candidate else "false",
            "是否候选与机器线索一致": bool_text(crop_ocr["是否裁图OCR与机器候选一致"]),
            "是否候选与机器线索冲突": bool_text(crop_ocr["是否裁图OCR与机器候选冲突"]),
            "是否候选与高校线索一致": bool_text(crop_ocr["是否裁图OCR与高校辅证一致"]),
            "是否候选与高校线索冲突": bool_text(crop_ocr["是否裁图OCR与高校辅证冲突"]),
            "是否有机器规范线索": bool_text(row["是否有机器规范候选"]),
            "是否有高校字段线索": bool_text(row["是否有高校字段线索"]),
            "是否需要人工直接看图": needs_direct_image_review(crop_ocr),
            "是否需要双人复核": bool_text(row["是否需要双人复核"]),
            "是否可自动写入人工读数": "false",
            "是否仍需PDF原页人工核页": "true",
            "是否仍需湖北官方核验": "true",
            "是否仍需高校辅证核验": bool_text(row["是否有高校字段线索"]),
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "高校官网或招生章程辅证状态": "pending_if_school_clue_present",
            "三方字段一致性状态": "pending_private_three_way_field_confirmation",
            "字段事实写回状态": "blocked_until_required_private_readings_complete",
            "公开安全策略": "公开表只保存候选存在性、关系桶、证据编号、SHA、bbox和门禁；私有候选明细、识别行文本、图片路径和人工记录不进入公开仓库。",
            "下一步": "打开私有候选表和页列核页包，人工回看PDF原页；完成湖北官方核验和必要高校辅证后再更新字段确认工作台。",
        }
        private_row = {
            **public_row,
            "PDF原页私有候选字段读数": private_ocr.get("裁图OCR候选字段值", ""),
            "PDF原页私有候选规范读数": private_ocr.get("裁图OCR候选规范值", ""),
            "PDF原页私有候选来源说明": "来自私有裁图OCR，仅作PDF原页人工核页线索，不得自动写入人工读数。",
            "裁图OCR候选行文本": private_ocr.get("裁图OCR候选行文本", ""),
            "裁图OCR候选行序号": private_ocr.get("裁图OCR候选行序号", ""),
            "裁图OCR候选x中心": private_ocr.get("裁图OCR候选x中心", ""),
            "裁图OCR候选y中心": private_ocr.get("裁图OCR候选y中心", ""),
            "裁图OCR候选置信度": private_ocr.get("裁图OCR候选置信度", ""),
            "裁图OCR候选距目标行y": private_ocr.get("裁图OCR候选距目标行y", ""),
            "裁图OCR全部候选短摘": private_ocr.get("裁图OCR全部候选短摘", ""),
            "机器候选字段读数": row.get("机器候选字段值", ""),
            "机器候选规范读数": row.get("机器候选规范值", ""),
            "高校官网字段候选读数": row.get("高校官网字段候选值", ""),
            "高校官网字段规范读数": row.get("高校官网字段规范值", ""),
            "私有OCR图片本地路径": private_ocr.get("私有OCR图片本地路径", ""),
            "候选不得自动写回声明": "候选值必须经PDF原页人工读数、湖北官方核验和三方一致性复核后，才可进入字段确认工作台。",
        }
        public_rows.append(public_row)
        private_rows.append(private_row)
    return public_rows, private_rows


def build_summary(rows):
    return {
        "status": "issue19_p0_immediate_pdf_reading_candidate_public_audit_not_final",
        "generated_by": Path(__file__).name,
        "source_field_confirmation_ledger": "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv",
        "source_crop_ocr_audit": "data/working/issue19-p0-immediate-crop-ocr-public-audit.csv",
        "source_page_review_packets": "data/working/issue19-p0-immediate-page-review-packets.csv",
        "source_private_crop_ocr_reading": "private_crop_ocr_reading_candidates_not_public",
        "output_table": "data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv",
        "row_count": len(rows),
        "private_pdf_reading_candidate_file_generated": True,
        "unique_public_audit_id_count": len({row["P0即时PDF原页候选公开审计ID"] for row in rows}),
        "unique_immediate_task_id_count": len({row["P0字段即时复核任务ID"] for row in rows}),
        "unique_field_confirmation_ledger_id_count": len({row["P0即时字段确认公开账本ID"] for row in rows}),
        "unique_crop_ocr_audit_id_count": len({row["P0即时裁图OCR公开审计ID"] for row in rows}),
        "unique_page_review_packet_count": len({row["P0即时按页核页包ID"] for row in rows}),
        "unique_major_field_pair_count": len({(row["专业行ID"], row["字段名"]) for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in rows}),
        "field_counts": counter_dict(rows, "字段名"),
        "candidate_private_status_counts": counter_dict(rows, "私有PDF原页候选记录状态"),
        "candidate_review_bucket_counts": counter_dict(rows, "PDF原页候选审阅桶"),
        "candidate_source_status_counts": counter_dict(rows, "PDF原页候选来源状态"),
        "candidate_confidence_counts": counter_dict(rows, "PDF原页候选置信等级"),
        "crop_ocr_candidate_status_counts": counter_dict(rows, "裁图OCR候选状态"),
        "crop_ocr_helper_bucket_counts": counter_dict(rows, "裁图OCR三方辅助桶"),
        "candidate_seeded_count": sum(row["是否已有私有PDF原页候选"] == "true" for row in rows),
        "candidate_unavailable_count": sum(row["是否已有私有PDF原页候选"] == "false" for row in rows),
        "candidate_machine_match_count": sum(row["是否候选与机器线索一致"] == "true" for row in rows),
        "candidate_machine_conflict_count": sum(row["是否候选与机器线索冲突"] == "true" for row in rows),
        "candidate_school_match_count": sum(row["是否候选与高校线索一致"] == "true" for row in rows),
        "candidate_school_conflict_count": sum(row["是否候选与高校线索冲突"] == "true" for row in rows),
        "direct_image_review_required_count": sum(row["是否需要人工直接看图"] == "true" for row in rows),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in rows),
        "auto_manual_reading_write_allowed_count": sum(row["是否可自动写入人工读数"] == "true" for row in rows),
        "pdf_manual_review_required_count": sum(row["是否仍需PDF原页人工核页"] == "true" for row in rows),
        "hubei_official_review_required_count": sum(row["是否仍需湖北官方核验"] == "true" for row in rows),
        "school_side_review_required_count": sum(row["是否仍需高校辅证核验"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "public_safety_note": "公开表只保存候选存在性、关系桶、证据编号、SHA、bbox和门禁；私有候选明细和人工记录不公开。",
    }


def main():
    public_rows, private_rows = build_rows()
    write_csv(OUTPUT, public_rows, FIELDS)
    write_csv(PRIVATE_OUTPUT, private_rows, PRIVATE_FIELDS)
    write_json(SUMMARY_OUTPUT, build_summary(public_rows))
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {PRIVATE_OUTPUT.relative_to(ROOT)}：{len(private_rows)} 行")


if __name__ == "__main__":
    main()
