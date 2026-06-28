#!/usr/bin/env python3
"""Build a field-atom public closure ledger for the first closure batch.

The public ledger expands 206 first-closure tasks into field atoms. It only
publishes completion states, relationship buckets, and hashes. Actual field
values and review notes stay in Git-ignored private workbooks.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"
PRIVATE = ROOT / "private/review-assets"

FIELD_CONFIRM = WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
EVIDENCE_STATUS = WORKING / "issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv"
NEXT_ACTION = WORKING / "issue19-stable-foundation-first-closure-next-action-matrix.csv"
P0_TOP3_FIELD_PUBLIC = WORKING / "issue19-p0-top3-field-review-public-ledger.csv"
B0_CONFLICT = WORKING / "issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv"

PRIVATE_FIELD_CONFIRM = (
    PRIVATE
    / "issue19-stable-foundation-first-closure-field-confirmation"
    / "first-closure-field-confirmation-private-workbench.csv"
)
PRIVATE_P0_TOP3_FIELD = (
    PRIVATE / "issue19-p0-top3-review-packet" / "p0-top3-private-field-review.csv"
)

OUTPUT = WORKING / "issue19-stable-foundation-first-closure-field-fact-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-field-fact-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_field_fact_public_ledger"
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

FIELDS = [
    "第一闭环字段事实公开账本ID",
    "来源第一闭环字段确认公开账本",
    "来源第一闭环证据状态账本",
    "来源第一闭环下一步动作矩阵",
    "来源P0Top3字段公开账本",
    "来源B0冲突页列核验状态",
    "来源私有字段确认工作台",
    "来源P0Top3私有字段核验表",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "字段事实序号",
    "稳定基座第一闭环明细任务ID",
    "第一闭环字段确认公开账本ID",
    "第一闭环证据状态公开账本ID",
    "第一闭环下一步动作ID",
    "P0Top3字段公开账本ID",
    "B0冲突页列核验状态ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "任务来源类型",
    "字段名",
    "字段候选关系桶",
    "PDF提示字段状态",
    "机器坐标字段状态",
    "高校辅证字段状态",
    "冲突类型桶",
    "核验动作层级",
    "人工最小核验动作",
    "PDF原页记录状态",
    "湖北官方记录状态",
    "高校辅证记录状态",
    "双人复核状态",
    "三方一致性状态",
    "字段事实闭环状态",
    "字段写回评估门禁",
    "完成证据组合",
    "字段事实值集合SHA256",
    "私有字段记录状态SHA256",
    "是否P0Top3重点字段",
    "是否B0冲突页列字段",
    "是否需要双人复核",
    "是否需要人工看图",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "公开安全策略",
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
    "专业名称",
    "专业代号",
    "院校专业组",
    "OCR行文本",
    "OCR原文",
    "候选值",
    "人工读数",
    "字段确认值",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "复核备注",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]

PRIVATE_VALUE_FIELDS = [
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
]

P0_PRIVATE_VALUE_FIELDS = [
    "PDF原页字段人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def stable_id(prefix: str, parts: list[str]) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def sha256_values(values: list[str]) -> str:
    clean = [str(value or "").strip() for value in values if str(value or "").strip()]
    return hashlib.sha256("|".join(clean).encode("utf-8")).hexdigest() if clean else ""


def bool_true(value: str) -> bool:
    return str(value).strip().lower() == "true"


def split_fields(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split("；") if part.strip()]


def private_value_sha(private_row: dict[str, str], p0_private_row: dict[str, str] | None) -> str:
    values = [private_row.get(field, "") for field in PRIVATE_VALUE_FIELDS]
    if p0_private_row:
        values.extend(p0_private_row.get(field, "") for field in P0_PRIVATE_VALUE_FIELDS)
    return sha256_values(values)


def private_state_sha(private_row: dict[str, str], p0_private_row: dict[str, str] | None) -> str:
    values = [
        private_row.get("PDF原页私有记录状态", ""),
        private_row.get("湖北官方私有记录状态", ""),
        private_row.get("高校辅证私有记录状态", ""),
        private_row.get("双人复核公开状态", ""),
        private_row.get("三方字段一致性公开状态", ""),
        private_row.get("字段事实写回评估状态", ""),
    ]
    if p0_private_row:
        values.extend([
            p0_private_row.get("字段确认来源组合", ""),
            p0_private_row.get("双人一致性结论", ""),
            p0_private_row.get("三方一致性结论", ""),
            p0_private_row.get("字段事实写回建议", ""),
        ])
    return sha256_values(values)


def completion_combo(pdf_status: str, hubei_status: str, school_status: str, double_status: str) -> str:
    parts = []
    parts.append("PDF原页记录待完成" if "pending" in pdf_status else "PDF原页记录已填写")
    parts.append("湖北官方侧待完成" if "pending" in hubei_status else "湖北官方侧已填写")
    if school_status.startswith("not_applicable"):
        parts.append("高校辅证不适用")
    elif "pending" in school_status:
        parts.append("高校辅证待完成")
    else:
        parts.append("高校辅证已填写")
    if double_status == "pending_double_review":
        parts.append("双人复核待完成")
    elif double_status == "double_review_not_required":
        parts.append("双人复核不要求")
    else:
        parts.append("双人复核已有状态")
    return "；".join(parts)


def field_relation(row: dict[str, str], field_name: str, p0_row: dict[str, str] | None) -> str:
    if p0_row:
        return p0_row.get("字段候选关系桶", "")
    relation = row.get("PDFOCR与高校辅证关系桶", "")
    combined = row.get("候选提示综合桶", "")
    if relation:
        return relation
    if combined:
        return combined
    if bool_true(row.get("是否有机器坐标提示", "")):
        return "R4-机器坐标候选待人工核页"
    return "R5-无公开候选关系桶"


def conflict_bucket(row: dict[str, str], p0_row: dict[str, str] | None) -> str:
    if p0_row and p0_row.get("字段候选关系桶", "").startswith("R0"):
        return "C0-字段候选冲突"
    if bool_true(row.get("是否存在PDFOCR与高校冲突", "")):
        return "C0-PDFOCR与高校辅证冲突"
    if row.get("PDFOCR与高校辅证关系桶", "").startswith("R1"):
        return "C1-多源候选一致但待官方侧"
    if bool_true(row.get("是否有机器坐标提示", "")):
        return "C2-机器坐标候选待核"
    if bool_true(row.get("是否需要人工直接看图", "")):
        return "C3-无稳定候选需看图"
    return "C4-常规待闭环"


def field_status(private_row: dict[str, str], p0_private_row: dict[str, str] | None) -> str:
    has_values = bool(private_value_sha(private_row, p0_private_row))
    if has_values:
        return "F1-私有字段记录已有值待人工评估写回"
    return "F0-字段记录未填写"


def main() -> None:
    public_rows = read_csv(FIELD_CONFIRM)
    evidence_rows = read_csv(EVIDENCE_STATUS)
    next_action_rows = read_csv(NEXT_ACTION) if NEXT_ACTION.exists() else []
    p0_public_rows = read_csv(P0_TOP3_FIELD_PUBLIC)
    b0_rows = read_csv(B0_CONFLICT)
    private_rows = read_csv(PRIVATE_FIELD_CONFIRM)
    p0_private_rows = read_csv(PRIVATE_P0_TOP3_FIELD)

    evidence_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in evidence_rows}
    next_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in next_action_rows}
    private_by_public_id = {row.get("第一闭环字段确认公开账本ID", ""): row for row in private_rows}
    p0_private_by_task_field = {
        (row.get("第一闭环任务ID", ""), row.get("字段名", "")): row for row in p0_private_rows
    }
    p0_public_by_id = {row.get("P0Top3字段公开账本ID", ""): row for row in p0_public_rows}
    p0_public_by_task_field = {}
    for item in p0_private_rows:
        pub = p0_public_by_id.get(item.get("P0Top3字段公开账本ID", ""), {})
        if pub:
            p0_public_by_task_field[(item.get("第一闭环任务ID", ""), item.get("字段名", ""))] = pub
    b0_by_page = {row.get("页码版面键", ""): row for row in b0_rows}

    output_rows: list[dict[str, str]] = []
    seq = 0
    for public_row in public_rows:
        task_id = public_row.get("稳定基座第一闭环明细任务ID", "")
        private_row = private_by_public_id.get(public_row.get("第一闭环字段确认公开账本ID", ""), {})
        evidence_row = evidence_by_task.get(task_id, {})
        next_row = next_by_task.get(task_id, {})
        page_key = public_row.get("页码版面键", "")
        b0_row = b0_by_page.get(page_key, {})
        for field_name in split_fields(public_row.get("字段名", "")):
            seq += 1
            p0_private = p0_private_by_task_field.get((task_id, field_name))
            p0_public = p0_public_by_task_field.get((task_id, field_name))
            pdf_status = public_row.get("PDF原页私有记录状态", "")
            hubei_status = public_row.get("湖北官方私有记录状态", "")
            school_status = public_row.get("高校辅证私有记录状态", "")
            double_status = public_row.get("双人复核公开状态", "")
            three_way = public_row.get("三方字段一致性公开状态", "")
            writeback = public_row.get("字段事实写回评估状态", "")
            value_sha = private_value_sha(private_row, p0_private)
            out = {
                "第一闭环字段事实公开账本ID": stable_id(
                    "FIRSTFACT",
                    [task_id, public_row.get("第一闭环字段确认公开账本ID", ""), field_name],
                ),
                "来源第一闭环字段确认公开账本": source_path(FIELD_CONFIRM),
                "来源第一闭环证据状态账本": source_path(EVIDENCE_STATUS),
                "来源第一闭环下一步动作矩阵": source_path(NEXT_ACTION),
                "来源P0Top3字段公开账本": source_path(P0_TOP3_FIELD_PUBLIC),
                "来源B0冲突页列核验状态": source_path(B0_CONFLICT),
                "来源私有字段确认工作台": "first_closure_field_confirmation_private_workbench_not_public",
                "来源P0Top3私有字段核验表": "p0_top3_private_field_review_not_public",
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "生成日期": GENERATED_AT,
                "数据阶段": DATA_STAGE,
                "主表粒度": "第一闭环字段原子",
                "任务粒度": "第一闭环任务×字段名×公开闭环状态",
                "字段事实序号": str(seq),
                "稳定基座第一闭环明细任务ID": task_id,
                "第一闭环字段确认公开账本ID": public_row.get("第一闭环字段确认公开账本ID", ""),
                "第一闭环证据状态公开账本ID": evidence_row.get("第一闭环证据状态公开账本ID", ""),
                "第一闭环下一步动作ID": next_row.get("第一闭环下一步动作ID", ""),
                "P0Top3字段公开账本ID": (p0_public or {}).get("P0Top3字段公开账本ID", ""),
                "B0冲突页列核验状态ID": b0_row.get("B0冲突页列核验状态ID", ""),
                "来源页码": public_row.get("来源页码", ""),
                "版面列": public_row.get("版面列", ""),
                "页码版面键": page_key,
                "专业行ID": public_row.get("专业行ID", ""),
                "专业组出现ID": public_row.get("专业组出现ID", ""),
                "院校代码": public_row.get("院校代码", ""),
                "任务来源类型": public_row.get("任务来源类型", ""),
                "字段名": field_name,
                "字段候选关系桶": field_relation(public_row, field_name, p0_public),
                "PDF提示字段状态": public_row.get("PDFOCR提示记录状态", ""),
                "机器坐标字段状态": public_row.get("机器坐标提示记录状态", ""),
                "高校辅证字段状态": school_status,
                "冲突类型桶": conflict_bucket(public_row, p0_public),
                "核验动作层级": next_row.get("核验动作层级", ""),
                "人工最小核验动作": next_row.get("人工最小核验动作", public_row.get("人工核验动作", "")),
                "PDF原页记录状态": pdf_status,
                "湖北官方记录状态": hubei_status,
                "高校辅证记录状态": school_status,
                "双人复核状态": double_status,
                "三方一致性状态": three_way,
                "字段事实闭环状态": field_status(private_row, p0_private),
                "字段写回评估门禁": writeback,
                "完成证据组合": completion_combo(pdf_status, hubei_status, school_status, double_status),
                "字段事实值集合SHA256": value_sha,
                "私有字段记录状态SHA256": private_state_sha(private_row, p0_private),
                "是否P0Top3重点字段": "true" if p0_public else "false",
                "是否B0冲突页列字段": "true" if b0_row else "false",
                "是否需要双人复核": public_row.get("是否需要双人复核", ""),
                "是否需要人工看图": public_row.get("是否需要人工直接看图", ""),
                "PDF原页核页状态": "pending_pdf_page_review",
                "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
                "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
                "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
                "公开安全策略": "只保存字段名、状态、关系桶、ID和SHA；字段明细值与人工记录只留在私有工作台。",
            }
            for field in FALSE_FIELDS:
                out[field] = "false"
            output_rows.append(out)

    write_csv(OUTPUT, output_rows)
    public_text = OUTPUT.read_text(encoding="utf-8", errors="ignore")
    forbidden_hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if forbidden_hits:
        raise SystemExit(f"公开输出包含禁止内容：{forbidden_hits[:5]}")

    field_counts = Counter(row.get("字段名", "") for row in output_rows)
    relation_counts = Counter(row.get("字段候选关系桶", "") for row in output_rows)
    closure_counts = Counter(row.get("字段事实闭环状态", "") for row in output_rows)
    conflict_counts = Counter(row.get("冲突类型桶", "") for row in output_rows)
    summary = {
        "status": "issue19_stable_foundation_first_closure_field_fact_public_ledger_ready_not_final",
        "generated_by": "build_issue19_first_closure_field_fact_public_ledger.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_first_closure_field_confirmation_public_ledger": source_path(FIELD_CONFIRM),
        "source_first_closure_evidence_status": source_path(EVIDENCE_STATUS),
        "source_first_closure_next_action_matrix": source_path(NEXT_ACTION),
        "source_p0_top3_field_public_ledger": source_path(P0_TOP3_FIELD_PUBLIC),
        "source_b0_conflict_status_public_ledger": source_path(B0_CONFLICT),
        "source_private_field_confirmation_workbench": "first_closure_field_confirmation_private_workbench_not_public",
        "source_private_p0_top3_field_review": "p0_top3_private_field_review_not_public",
        "output_table": source_path(OUTPUT),
        "row_grain": "第一闭环任务×字段名",
        "row_count": len(output_rows),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID", "") for row in output_rows}),
        "unique_task_field_count": len(
            {(row.get("稳定基座第一闭环明细任务ID", ""), row.get("字段名", "")) for row in output_rows}
        ),
        "field_counts": dict(field_counts),
        "field_candidate_relation_counts": dict(relation_counts),
        "field_fact_closure_status_counts": dict(closure_counts),
        "conflict_type_counts": dict(conflict_counts),
        "p0_top3_field_count": sum(row.get("是否P0Top3重点字段") == "true" for row in output_rows),
        "b0_conflict_page_field_count": sum(row.get("是否B0冲突页列字段") == "true" for row in output_rows),
        "double_review_required_field_count": sum(row.get("是否需要双人复核") == "true" for row in output_rows),
        "manual_image_required_field_count": sum(row.get("是否需要人工看图") == "true" for row in output_rows),
        "pdf_pending_field_count": sum(row.get("PDF原页记录状态") == "pending_private_pdf_reading" for row in output_rows),
        "hubei_pending_field_count": sum(row.get("湖北官方记录状态") == "pending_private_hubei_reading" for row in output_rows),
        "school_pending_field_count": sum(row.get("高校辅证记录状态") == "pending_private_school_reading" for row in output_rows),
        "three_way_pending_field_count": sum(
            row.get("三方一致性状态") == "pending_private_three_way_field_confirmation" for row in output_rows
        ),
        "field_value_sha_present_count": sum(bool(row.get("字段事实值集合SHA256")) for row in output_rows),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该公开账本只记录字段原子闭环进度，不公开字段明细值，不确认字段事实，不允许写回或推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
