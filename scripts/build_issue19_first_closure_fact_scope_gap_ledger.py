#!/usr/bin/env python3
"""Build a public fact-scope gap ledger for the first closure batch.

The first closure already has field-atom rows. This ledger widens the public
view to the full fact scope we must close before using the data for decisions:
field facts, major-name assignment facts, and group-boundary facts. It does not
publish school names, major names, field values, OCR text, or private paths.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FIELD_FACT = WORKING / "issue19-stable-foundation-first-closure-field-fact-public-ledger.csv"
NEXT_ACTION = WORKING / "issue19-stable-foundation-first-closure-next-action-matrix.csv"
NEXT_ACTION_PAGE = WORKING / "issue19-stable-foundation-first-closure-next-action-page-summary.csv"
EVIDENCE_STATUS = WORKING / "issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv"
EVIDENCE_PAGE = WORKING / "issue19-stable-foundation-first-closure-evidence-status-page-side-summary.csv"

OUTPUT = WORKING / "issue19-stable-foundation-first-closure-fact-scope-gap-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-fact-scope-gap-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_fact_scope_gap_public_ledger"
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
    "第一闭环事实范围缺口公开账本ID",
    "来源第一闭环字段事实公开账本",
    "来源第一闭环下一步动作矩阵",
    "来源第一闭环页列下一步动作汇总",
    "来源第一闭环证据状态账本",
    "来源第一闭环页列证据汇总",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "事实序号",
    "事实域",
    "事实类型",
    "事实粒度",
    "事实闭环状态",
    "稳定基座第一闭环明细任务ID",
    "第一闭环字段事实公开账本ID",
    "第一闭环下一步动作ID",
    "第一闭环页列下一步动作ID",
    "第一闭环证据状态公开账本ID",
    "第一闭环页列证据状态汇总ID",
    "稳定基座第一闭环页列包ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "任务来源类型",
    "字段名",
    "执行泳道",
    "核验动作层级",
    "页列主阻断",
    "事实缺口桶",
    "PDF原页记录状态",
    "湖北官方侧记录状态",
    "高校辅证记录状态",
    "双人复核状态",
    "三方一致性状态",
    "人工最小核验动作",
    "完成条件",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "事实对象集合SHA256",
    "页列任务集合SHA256",
    "专业行集合SHA256",
    "院校代码集合SHA256",
    "是否字段事实",
    "是否专业名归属事实",
    "是否专业组边界事实",
    "是否需要人工看图",
    "是否需要双人复核",
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
    clean = sorted({str(value or "").strip() for value in values if str(value or "").strip()})
    return hashlib.sha256("|".join(clean).encode("utf-8")).hexdigest() if clean else ""


def to_int(value: str | int | None) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def is_true(value: str) -> bool:
    return str(value).strip().lower() == "true"


def is_major_name_assignment(row: dict[str, str]) -> bool:
    return "专业名" in row.get("执行泳道", "") or "专业名" in row.get("官网辅证自动动作", "")


def base_row(seq: int, fact_domain: str, fact_type: str, fact_grain: str, fact_gap: str) -> dict[str, str]:
    row = {
        "来源第一闭环字段事实公开账本": source_path(FIELD_FACT),
        "来源第一闭环下一步动作矩阵": source_path(NEXT_ACTION),
        "来源第一闭环页列下一步动作汇总": source_path(NEXT_ACTION_PAGE),
        "来源第一闭环证据状态账本": source_path(EVIDENCE_STATUS),
        "来源第一闭环页列证据汇总": source_path(EVIDENCE_PAGE),
        "来源期号": SOURCE_ISSUE,
        "来源PDF_SHA256": SOURCE_PDF_SHA256,
        "生成日期": GENERATED_AT,
        "数据阶段": DATA_STAGE,
        "主表粒度": "第一闭环事实范围缺口",
        "任务粒度": fact_grain,
        "事实序号": str(seq),
        "事实域": fact_domain,
        "事实类型": fact_type,
        "事实粒度": fact_grain,
        "事实闭环状态": "F0-待原页与湖北官方侧闭环",
        "事实缺口桶": fact_gap,
        "PDF原页记录状态": "pending_pdf_page_review",
        "湖北官方侧记录状态": "pending_hubei_official_plan_review",
        "高校辅证记录状态": "for_double_check_only_not_official_plan_replacement",
        "三方一致性状态": "pending_three_way_closure",
        "PDF原页核页状态": "pending_pdf_page_review",
        "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
        "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
        "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
        "公开安全策略": "公开层只保存ID、页列、状态桶、计数和SHA；不保存学校专业明细、字段明细值、识别正文或私有材料。",
    }
    for field in FALSE_FIELDS:
        row[field] = "false"
    return row


def field_fact_scope_row(
    seq: int,
    field_row: dict[str, str],
    next_row: dict[str, str],
    evidence_row: dict[str, str],
) -> dict[str, str]:
    fact_type = f"字段事实-{field_row.get('字段名', '')}"
    row = base_row(seq, "字段事实", fact_type, "第一闭环任务×字段", "G0-关键字段待闭环")
    row.update({
        "第一闭环事实范围缺口公开账本ID": stable_id(
            "FIRSTSCOPE",
            [
                "field",
                field_row.get("第一闭环字段事实公开账本ID", ""),
                field_row.get("字段名", ""),
            ],
        ),
        "稳定基座第一闭环明细任务ID": field_row.get("稳定基座第一闭环明细任务ID", ""),
        "第一闭环字段事实公开账本ID": field_row.get("第一闭环字段事实公开账本ID", ""),
        "第一闭环下一步动作ID": field_row.get("第一闭环下一步动作ID", ""),
        "第一闭环证据状态公开账本ID": field_row.get("第一闭环证据状态公开账本ID", ""),
        "稳定基座第一闭环页列包ID": evidence_row.get("稳定基座第一闭环页列包ID", ""),
        "来源页码": field_row.get("来源页码", ""),
        "版面列": field_row.get("版面列", ""),
        "页码版面键": field_row.get("页码版面键", ""),
        "专业行ID": field_row.get("专业行ID", ""),
        "专业组出现ID": field_row.get("专业组出现ID", ""),
        "院校代码": field_row.get("院校代码", ""),
        "任务来源类型": field_row.get("任务来源类型", ""),
        "字段名": field_row.get("字段名", ""),
        "执行泳道": next_row.get("执行泳道", ""),
        "核验动作层级": field_row.get("核验动作层级", ""),
        "页列主阻断": next_row.get("页列主阻断", ""),
        "PDF原页记录状态": field_row.get("PDF原页核页状态", "pending_pdf_page_review"),
        "湖北官方侧记录状态": field_row.get("湖北官方系统或省招办计划核验状态", "pending_hubei_official_plan_review"),
        "高校辅证记录状态": field_row.get("高校官网源状态", "for_double_check_only_not_official_plan_replacement"),
        "双人复核状态": field_row.get("双人复核状态", ""),
        "三方一致性状态": field_row.get("三方一致性状态", "pending_three_way_closure"),
        "人工最小核验动作": field_row.get("人工最小核验动作", ""),
        "完成条件": "PDF原页、湖北官方侧、必要高校辅证和双人复核均闭环后，才可评估字段写回。",
        "涉及任务数": "1",
        "涉及专业行数": "1",
        "涉及院校代码数": "1",
        "事实对象集合SHA256": sha256_values([
            field_row.get("稳定基座第一闭环明细任务ID", ""),
            field_row.get("第一闭环字段事实公开账本ID", ""),
            field_row.get("字段名", ""),
        ]),
        "是否字段事实": "true",
        "是否专业名归属事实": "false",
        "是否专业组边界事实": "false",
        "是否需要人工看图": field_row.get("是否需要人工看图", ""),
        "是否需要双人复核": field_row.get("是否需要双人复核", ""),
    })
    return row


def major_name_scope_row(
    seq: int,
    next_row: dict[str, str],
    evidence_row: dict[str, str],
) -> dict[str, str]:
    row = base_row(seq, "专业名归属", "专业名归属事实", "第一闭环任务×专业名归属", "G1-专业名归属待闭环")
    row.update({
        "第一闭环事实范围缺口公开账本ID": stable_id(
            "FIRSTSCOPE",
            ["major_name", next_row.get("稳定基座第一闭环明细任务ID", "")],
        ),
        "稳定基座第一闭环明细任务ID": next_row.get("稳定基座第一闭环明细任务ID", ""),
        "第一闭环下一步动作ID": next_row.get("第一闭环下一步动作ID", ""),
        "第一闭环证据状态公开账本ID": next_row.get("第一闭环证据状态公开账本ID", ""),
        "稳定基座第一闭环页列包ID": next_row.get("稳定基座第一闭环页列包ID", ""),
        "来源页码": next_row.get("来源页码", ""),
        "版面列": next_row.get("版面列", ""),
        "页码版面键": next_row.get("页码版面键", ""),
        "专业行ID": next_row.get("专业行ID", ""),
        "专业组出现ID": next_row.get("专业组出现ID", ""),
        "院校代码": next_row.get("院校代码", ""),
        "任务来源类型": next_row.get("任务来源类型", ""),
        "字段名": next_row.get("字段名", ""),
        "执行泳道": next_row.get("执行泳道", ""),
        "核验动作层级": next_row.get("核验动作层级", ""),
        "页列主阻断": next_row.get("页列主阻断", ""),
        "双人复核状态": "pending_double_review" if is_true(next_row.get("是否需要双人复核", "")) else "double_review_not_required",
        "人工最小核验动作": next_row.get("人工最小核验动作", ""),
        "完成条件": "回看PDF原页确认专业行归属，并用湖北官方侧计划记录复核；高校侧来源只能辅助定位。",
        "涉及任务数": "1",
        "涉及专业行数": "1",
        "涉及院校代码数": "1",
        "事实对象集合SHA256": sha256_values([
            next_row.get("稳定基座第一闭环明细任务ID", ""),
            next_row.get("专业行ID", ""),
            next_row.get("专业组出现ID", ""),
        ]),
        "页列任务集合SHA256": evidence_row.get("第一闭环任务ID集合SHA256", ""),
        "专业行集合SHA256": evidence_row.get("专业行ID集合SHA256", ""),
        "院校代码集合SHA256": evidence_row.get("院校代码集合SHA256", ""),
        "是否字段事实": "false",
        "是否专业名归属事实": "true",
        "是否专业组边界事实": "false",
        "是否需要人工看图": next_row.get("是否需要人工直接看图", ""),
        "是否需要双人复核": next_row.get("是否需要双人复核", ""),
    })
    return row


def group_boundary_scope_row(
    seq: int,
    page_row: dict[str, str],
    evidence_page_row: dict[str, str],
) -> dict[str, str]:
    row = base_row(seq, "专业组边界", "专业组边界事实", "PDF页码×版面列×专业组边界", "G2-专业组边界待闭环")
    row.update({
        "第一闭环事实范围缺口公开账本ID": stable_id(
            "FIRSTSCOPE",
            ["group_boundary", page_row.get("页码版面键", ""), page_row.get("稳定基座第一闭环页列包ID", "")],
        ),
        "第一闭环页列下一步动作ID": page_row.get("第一闭环页列下一步动作ID", ""),
        "第一闭环页列证据状态汇总ID": evidence_page_row.get("第一闭环页列证据状态汇总ID", ""),
        "稳定基座第一闭环页列包ID": page_row.get("稳定基座第一闭环页列包ID", ""),
        "来源页码": page_row.get("来源页码", ""),
        "版面列": page_row.get("版面列", ""),
        "页码版面键": page_row.get("页码版面键", ""),
        "执行泳道": page_row.get("执行泳道", ""),
        "核验动作层级": page_row.get("核验动作层级分布", ""),
        "页列主阻断": page_row.get("页列主阻断", ""),
        "双人复核状态": "pending_double_review" if to_int(page_row.get("N0冲突双人核页任务数")) > 0 else "double_review_not_required_or_task_level",
        "人工最小核验动作": page_row.get("页列建议下一步动作", ""),
        "完成条件": "逐页列核清专业组起止、跨页延续、左右栏边界和组内专业归属后，才可用于调剂风险判断。",
        "涉及任务数": page_row.get("页列任务数", ""),
        "涉及专业行数": page_row.get("涉及专业行数", ""),
        "涉及院校代码数": page_row.get("涉及院校代码数", ""),
        "事实对象集合SHA256": sha256_values([
            page_row.get("页码版面键", ""),
            evidence_page_row.get("第一闭环任务ID集合SHA256", ""),
            evidence_page_row.get("专业行ID集合SHA256", ""),
        ]),
        "页列任务集合SHA256": evidence_page_row.get("第一闭环任务ID集合SHA256", ""),
        "专业行集合SHA256": evidence_page_row.get("专业行ID集合SHA256", ""),
        "院校代码集合SHA256": evidence_page_row.get("院校代码集合SHA256", ""),
        "是否字段事实": "false",
        "是否专业名归属事实": "false",
        "是否专业组边界事实": "true",
        "是否需要人工看图": "true" if to_int(page_row.get("N3无候选人工看图任务数")) > 0 else "false",
        "是否需要双人复核": "true" if to_int(page_row.get("N0冲突双人核页任务数")) > 0 else "false",
    })
    return row


def main() -> None:
    field_rows = read_csv(FIELD_FACT)
    next_rows = read_csv(NEXT_ACTION)
    next_page_rows = read_csv(NEXT_ACTION_PAGE)
    evidence_rows = read_csv(EVIDENCE_STATUS)
    evidence_page_rows = read_csv(EVIDENCE_PAGE)

    next_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in next_rows}
    evidence_by_task = {row.get("稳定基座第一闭环明细任务ID", ""): row for row in evidence_rows}
    evidence_page_by_key = {row.get("页码版面键", ""): row for row in evidence_page_rows}

    output_rows: list[dict[str, str]] = []
    seq = 0
    for field_row in field_rows:
        seq += 1
        task_id = field_row.get("稳定基座第一闭环明细任务ID", "")
        output_rows.append(field_fact_scope_row(seq, field_row, next_by_task.get(task_id, {}), evidence_by_task.get(task_id, {})))

    for next_row in next_rows:
        if not is_major_name_assignment(next_row):
            continue
        seq += 1
        page_key = next_row.get("页码版面键", "")
        output_rows.append(major_name_scope_row(seq, next_row, evidence_page_by_key.get(page_key, {})))

    for page_row in next_page_rows:
        seq += 1
        page_key = page_row.get("页码版面键", "")
        output_rows.append(group_boundary_scope_row(seq, page_row, evidence_page_by_key.get(page_key, {})))

    write_csv(OUTPUT, output_rows)
    public_text = OUTPUT.read_text(encoding="utf-8", errors="ignore")
    forbidden_hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if forbidden_hits:
        raise SystemExit(f"公开输出包含禁止内容：{forbidden_hits[:5]}")

    fact_domain_counts = Counter(row.get("事实域", "") for row in output_rows)
    fact_type_counts = Counter(row.get("事实类型", "") for row in output_rows)
    closure_counts = Counter(row.get("事实闭环状态", "") for row in output_rows)
    gap_counts = Counter(row.get("事实缺口桶", "") for row in output_rows)
    summary = {
        "status": "issue19_stable_foundation_first_closure_fact_scope_gap_public_ledger_ready_not_final",
        "generated_by": "build_issue19_first_closure_fact_scope_gap_ledger.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_first_closure_field_fact_public_ledger": source_path(FIELD_FACT),
        "source_first_closure_next_action_matrix": source_path(NEXT_ACTION),
        "source_first_closure_next_action_page_summary": source_path(NEXT_ACTION_PAGE),
        "source_first_closure_evidence_status": source_path(EVIDENCE_STATUS),
        "source_first_closure_evidence_page_summary": source_path(EVIDENCE_PAGE),
        "output_table": source_path(OUTPUT),
        "row_grain": "第一闭环事实范围缺口",
        "row_count": len(output_rows),
        "source_field_fact_row_count": len(field_rows),
        "source_next_action_task_count": len(next_rows),
        "source_page_side_count": len(next_page_rows),
        "field_fact_atom_count": fact_domain_counts.get("字段事实", 0),
        "major_name_assignment_fact_count": fact_domain_counts.get("专业名归属", 0),
        "group_boundary_fact_count": fact_domain_counts.get("专业组边界", 0),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID", "") for row in output_rows if row.get("稳定基座第一闭环明细任务ID", "")}),
        "unique_page_side_count": len({row.get("页码版面键", "") for row in output_rows if row.get("页码版面键", "")}),
        "fact_domain_counts": dict(fact_domain_counts),
        "fact_type_counts": dict(fact_type_counts),
        "fact_gap_counts": dict(gap_counts),
        "fact_closure_status_counts": dict(closure_counts),
        "pdf_pending_fact_count": sum(row.get("PDF原页核页状态") == "pending_pdf_page_review" for row in output_rows),
        "hubei_official_pending_fact_count": sum(
            row.get("湖北官方系统或省招办计划核验状态") == "pending_hubei_official_plan_review"
            for row in output_rows
        ),
        "double_review_required_fact_count": sum(row.get("是否需要双人复核") == "true" for row in output_rows),
        "manual_image_required_fact_count": sum(row.get("是否需要人工看图") == "true" for row in output_rows),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该公开账本只说明第一闭环还缺哪些事实范围，不公开学校专业明细和字段明细值，不写回字段，不生成志愿排序。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
