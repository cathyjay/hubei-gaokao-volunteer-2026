#!/usr/bin/env python3
"""Build a public first-closure evidence status report.

This report does not confirm field values. It only aligns the existing first
closure task, OCR hint, school-source hint, and page-side blocker state into
one public status layer.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FIELD_CONFIRM = WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
TASK_REVIEW = WORKING / "issue19-stable-foundation-first-closure-task-review-public-ledger.csv"
PDF_OCR_AUDIT = WORKING / "issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv"
FIELD_STATUS = WORKING / "issue19-stable-foundation-first-closure-field-status-dashboard.csv"
OFFICIAL_STATUS = WORKING / "issue19-official-public-entry-status.json"

TASK_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-evidence-status-page-side-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-evidence-status-summary.json"

DATA_STAGE = "issue19_stable_foundation_first_closure_evidence_status_report"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"

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

TASK_FIELDS = [
    "第一闭环证据状态公开账本ID",
    "来源第一闭环字段确认公开账本",
    "来源第一闭环任务复核公开账本",
    "来源第一闭环PDFOCR候选公开审计",
    "来源第一闭环字段状态看板",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "证据状态总序",
    "稳定基座第一闭环明细任务ID",
    "第一闭环字段确认公开账本ID",
    "稳定基座第一闭环任务复核公开账本ID",
    "第一闭环PDFOCR候选公开审计ID",
    "第一闭环字段状态看板ID",
    "稳定基座第一闭环页列包ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "任务来源类型",
    "字段名",
    "第一闭环页列优先级",
    "执行泳道",
    "人工核验泳道",
    "人工核验方式",
    "人工核验动作",
    "必须完成证据步骤",
    "PDF原页证据状态",
    "OCR提示状态",
    "机器坐标提示状态",
    "高校辅证证据状态",
    "湖北官方侧状态",
    "冲突状态",
    "三方闭环状态",
    "字段写回门禁",
    "是否有PDFOCR提示",
    "是否有机器坐标提示",
    "是否有高校辅证线索",
    "是否存在PDFOCR与高校冲突",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "PDFOCR提示审阅桶",
    "PDFOCR与高校辅证关系桶",
    "候选提示综合桶",
    "官网辅证自动动作",
    "官网证据强度",
    "官网来源状态",
    "计划数核验状态",
    "页列主阻断",
    "页列建议下一步动作",
    "公开安全策略",
    "下一步",
]

PAGE_FIELDS = [
    "第一闭环页列证据状态汇总ID",
    "来源第一闭环证据状态公开账本",
    "来源第一闭环字段状态看板",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行顺序",
    "执行泳道",
    "第一闭环页列优先级",
    "稳定基座第一闭环页列包ID",
    "第一闭环字段状态看板ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "第一闭环任务ID集合SHA256",
    "专业行ID集合SHA256",
    "院校代码集合SHA256",
    "自动官网辅证任务数",
    "P0人工字段任务数",
    "专业计划数字段任务数",
    "学费字段任务数",
    "再选科目字段任务数",
    "待人工判定字段任务数",
    "PDF原页待核任务数",
    "湖北官方侧待核任务数",
    "高校辅证待核任务数",
    "PDFOCR提示任务数",
    "机器坐标提示任务数",
    "高校辅证线索任务数",
    "PDFOCR与高校辅证冲突任务数",
    "高校有线索但PDFOCR缺候选任务数",
    "仅PDFOCR候选待人工核页任务数",
    "PDFOCR与高校辅证一致仍需官方闭环任务数",
    "PDFOCR无候选任务数",
    "无候选需人工看图任务数",
    "需要人工直接看图任务数",
    "需要双人复核任务数",
    "字段事实写回可进入任务数",
    "字段事实写回阻断任务数",
    "任务来源类型分布",
    "OCR提示状态分布",
    "冲突状态分布",
    "人工核验泳道分布",
    "页列主阻断",
    "页列建议下一步动作",
    "完成条件",
    "公开安全策略",
]

FORBIDDEN_TOKENS = [
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
    "字段确认值",
    "人工读数",
    "候选值",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def source_path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix: str, parts: list[str]) -> str:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def sha_values(values) -> str:
    cleaned = sorted({str(value).strip() for value in values if str(value).strip()})
    if not cleaned:
        return ""
    return hashlib.sha256("\n".join(cleaned).encode("utf-8")).hexdigest()


def as_int(value) -> int:
    try:
        return int(str(value).strip() or "0")
    except ValueError:
        return 0


def is_true(value) -> bool:
    return str(value).strip().lower() == "true"


def false_gate_values() -> dict[str, str]:
    return {field: "false" for field in FALSE_FIELDS}


def split_field_names(value: str) -> list[str]:
    fields = [item.strip() for item in str(value).replace(",", "；").split("；")]
    return [field for field in fields if field]


def counter_summary(counter: Counter) -> str:
    return "；".join(f"{key}={value}" for key, value in sorted(counter.items()))


def pdf_source_status(row: dict[str, str]) -> str:
    if is_true(row.get("是否存在PDFOCR与高校冲突")):
        return "P0-有冲突线索，PDF原页优先人工核验"
    if is_true(row.get("是否有机器坐标提示")):
        return "P1-有机器坐标提示，仍待PDF原页人工核验"
    if is_true(row.get("是否有PDFOCR提示")):
        return "P2-有PDFOCR提示，仍待PDF原页人工确认"
    return "P3-无稳定OCR提示，需人工看PDF原页"


def ocr_status(row: dict[str, str]) -> str:
    relation = row.get("PDFOCR与高校辅证关系桶", "")
    if relation.startswith("R0"):
        return "O0-PDFOCR与高校辅证冲突"
    if relation.startswith("R1"):
        return "O1-PDFOCR与高校辅证有一致字段但仍待官方闭环"
    if relation.startswith("R2"):
        return "O2-高校有线索但PDFOCR缺候选"
    if relation.startswith("R3"):
        return "O3-仅PDFOCR候选待人工核页"
    if is_true(row.get("是否有机器坐标提示")):
        return "O4-无PDFOCR但有机器坐标提示"
    return "O5-无公开OCR候选提示"


def machine_status(row: dict[str, str]) -> str:
    if is_true(row.get("是否有机器坐标提示")):
        return "M1-有机器坐标提示可辅助定位"
    return "M0-无机器坐标提示"


def school_status(row: dict[str, str], task_row: dict[str, str]) -> str:
    if row.get("高校辅证私有记录状态") == "pending_private_school_reading":
        return "S1-有高校辅证线索或自动官网任务，待私有辅证记录"
    if is_true(row.get("是否有高校辅证线索")) or task_row.get("任务来源类型") == "自动官网辅证任务":
        return "S1-有高校辅证线索或自动官网任务，待私有辅证记录"
    return "S0-无高校字段线索，本任务高校辅证不适用"


def conflict_status(row: dict[str, str]) -> str:
    relation = row.get("PDFOCR与高校辅证关系桶", "")
    if relation.startswith("R0"):
        return "C0-PDFOCR与高校辅证冲突，必须回PDF原页和湖北官方侧"
    if relation.startswith("R2"):
        return "C1-高校补缺线索，PDF原页缺候选需人工看图"
    if relation.startswith("R1"):
        return "C2-多源有一致线索，仍待湖北官方侧闭环"
    if relation.startswith("R3"):
        return "C3-仅PDFOCR候选，需人工核页"
    return "C4-无可比候选，需人工看图或随页列闭环"


def build_task_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], dict]:
    field_rows = read_csv(FIELD_CONFIRM)
    task_rows = read_csv(TASK_REVIEW)
    pdf_rows = read_csv(PDF_OCR_AUDIT)
    page_rows = read_csv(FIELD_STATUS)

    task_by_id = {row["稳定基座第一闭环明细任务ID"]: row for row in task_rows}
    pdf_by_id = {row["稳定基座第一闭环明细任务ID"]: row for row in pdf_rows}
    page_by_key = {row["页码版面键"]: row for row in page_rows}

    output_rows: list[dict[str, str]] = []
    for idx, row in enumerate(field_rows, start=1):
        task_id = row.get("稳定基座第一闭环明细任务ID", "")
        task_row = task_by_id.get(task_id, {})
        pdf_row = pdf_by_id.get(task_id, {})
        page_row = page_by_key.get(row.get("页码版面键", ""), {})
        evidence_id = stable_id("FIRSTEVID", [task_id, row.get("字段名", "")])

        output_rows.append(
            {
                "第一闭环证据状态公开账本ID": evidence_id,
                "来源第一闭环字段确认公开账本": source_path(FIELD_CONFIRM),
                "来源第一闭环任务复核公开账本": source_path(TASK_REVIEW),
                "来源第一闭环PDFOCR候选公开审计": source_path(PDF_OCR_AUDIT),
                "来源第一闭环字段状态看板": source_path(FIELD_STATUS),
                "来源湖北官方公开入口状态快照": source_path(OFFICIAL_STATUS),
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "数据阶段": DATA_STAGE,
                "主表粒度": "第一闭环明细任务",
                "任务粒度": "专业行ID×字段或高校辅证任务×公开证据状态",
                **false_gate_values(),
                "证据状态总序": str(idx),
                "稳定基座第一闭环明细任务ID": task_id,
                "第一闭环字段确认公开账本ID": row.get("第一闭环字段确认公开账本ID", ""),
                "稳定基座第一闭环任务复核公开账本ID": row.get("稳定基座第一闭环任务复核公开账本ID", ""),
                "第一闭环PDFOCR候选公开审计ID": row.get("第一闭环PDFOCR候选公开审计ID", ""),
                "第一闭环字段状态看板ID": page_row.get("第一闭环字段状态看板ID", ""),
                "稳定基座第一闭环页列包ID": row.get("稳定基座第一闭环页列包ID", ""),
                "来源页码": row.get("来源页码", ""),
                "版面列": row.get("版面列", ""),
                "页码版面键": row.get("页码版面键", ""),
                "专业行ID": row.get("专业行ID", ""),
                "专业组出现ID": row.get("专业组出现ID", ""),
                "院校代码": row.get("院校代码", ""),
                "任务来源类型": row.get("任务来源类型", ""),
                "字段名": row.get("字段名", ""),
                "第一闭环页列优先级": row.get("第一闭环页列优先级", ""),
                "执行泳道": row.get("执行泳道", ""),
                "人工核验泳道": row.get("人工核验泳道", ""),
                "人工核验方式": row.get("人工核验方式", ""),
                "人工核验动作": row.get("人工核验动作", ""),
                "必须完成证据步骤": row.get("必须完成证据步骤", ""),
                "PDF原页证据状态": pdf_source_status(row),
                "OCR提示状态": ocr_status(row),
                "机器坐标提示状态": machine_status(row),
                "高校辅证证据状态": school_status(row, task_row),
                "湖北官方侧状态": row.get("湖北官方系统或省招办计划核验状态", ""),
                "冲突状态": conflict_status(row),
                "三方闭环状态": row.get("三方字段一致性公开状态", ""),
                "字段写回门禁": row.get("字段事实写回评估状态", ""),
                "是否有PDFOCR提示": row.get("是否有PDFOCR提示", ""),
                "是否有机器坐标提示": row.get("是否有机器坐标提示", ""),
                "是否有高校辅证线索": row.get("是否有高校辅证线索", ""),
                "是否存在PDFOCR与高校冲突": row.get("是否存在PDFOCR与高校冲突", ""),
                "是否需要人工直接看图": row.get("是否需要人工直接看图", ""),
                "是否需要双人复核": row.get("是否需要双人复核", ""),
                "PDFOCR提示审阅桶": row.get("PDFOCR提示审阅桶", ""),
                "PDFOCR与高校辅证关系桶": row.get("PDFOCR与高校辅证关系桶", ""),
                "候选提示综合桶": row.get("候选提示综合桶", ""),
                "官网辅证自动动作": task_row.get("官网辅证自动动作", ""),
                "官网证据强度": task_row.get("官网证据强度", ""),
                "官网来源状态": task_row.get("官网来源状态", ""),
                "计划数核验状态": task_row.get("计划数核验状态", ""),
                "页列主阻断": page_row.get("字段闭环主阻断", ""),
                "页列建议下一步动作": page_row.get("建议下一步动作", ""),
                "公开安全策略": "公开层只保存证据状态桶、计数、ID和SHA；不公开字段值、OCR原文、学校专业明细、人工记录或私有路径",
                "下一步": "按页列先核PDF原页，再核湖北官方侧；有高校辅证线索的任务只作double check，不替代湖北官方计划",
            }
        )

    page_summary_rows = build_page_rows(output_rows, page_rows)
    summary = build_summary(output_rows, page_summary_rows)
    return output_rows, page_summary_rows, summary


def build_page_rows(task_rows: list[dict[str, str]], page_status_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    tasks_by_page = defaultdict(list)
    for row in task_rows:
        tasks_by_page[row["页码版面键"]].append(row)
    page_by_key = {row["页码版面键"]: row for row in page_status_rows}

    page_rows = []
    for page_key in sorted(tasks_by_page, key=lambda key: as_int(key.split("-", 1)[0]) if "-" in key else key):
        rows = tasks_by_page[page_key]
        page_status = page_by_key.get(page_key, {})
        field_counter = Counter()
        for row in rows:
            for field_name in split_field_names(row.get("字段名", "")):
                field_counter[field_name] += 1

        task_ids = [row.get("稳定基座第一闭环明细任务ID", "") for row in rows]
        major_ids = [row.get("专业行ID", "") for row in rows]
        school_codes = [row.get("院校代码", "") for row in rows]
        source_counter = Counter(row.get("任务来源类型", "") for row in rows)
        ocr_counter = Counter(row.get("OCR提示状态", "") for row in rows)
        conflict_counter = Counter(row.get("冲突状态", "") for row in rows)
        lane_counter = Counter(row.get("人工核验泳道", "") for row in rows)

        page_rows.append(
            {
                "第一闭环页列证据状态汇总ID": stable_id("FIRSTEVIDPAGE", [page_key]),
                "来源第一闭环证据状态公开账本": source_path(TASK_OUTPUT),
                "来源第一闭环字段状态看板": source_path(FIELD_STATUS),
                "来源湖北官方公开入口状态快照": source_path(OFFICIAL_STATUS),
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "数据阶段": f"{DATA_STAGE}_page_side_summary",
                "主表粒度": "PDF页码×版面列",
                "任务粒度": "页列×第一闭环证据状态汇总",
                **false_gate_values(),
                "执行顺序": page_status.get("执行顺序", ""),
                "执行泳道": page_status.get("执行泳道", rows[0].get("执行泳道", "")),
                "第一闭环页列优先级": page_status.get("第一闭环页列优先级", rows[0].get("第一闭环页列优先级", "")),
                "稳定基座第一闭环页列包ID": page_status.get("稳定基座第一闭环页列包ID", rows[0].get("稳定基座第一闭环页列包ID", "")),
                "第一闭环字段状态看板ID": page_status.get("第一闭环字段状态看板ID", ""),
                "来源页码": rows[0].get("来源页码", ""),
                "版面列": rows[0].get("版面列", ""),
                "页码版面键": page_key,
                "页列任务数": str(len(rows)),
                "涉及专业行数": str(len({value for value in major_ids if value})),
                "涉及院校代码数": str(len({value for value in school_codes if value})),
                "第一闭环任务ID集合SHA256": sha_values(task_ids),
                "专业行ID集合SHA256": sha_values(major_ids),
                "院校代码集合SHA256": sha_values(school_codes),
                "自动官网辅证任务数": str(source_counter.get("自动官网辅证任务", 0)),
                "P0人工字段任务数": str(source_counter.get("P0人工字段任务", 0)),
                "专业计划数字段任务数": str(field_counter.get("专业计划数", 0)),
                "学费字段任务数": str(field_counter.get("学费", 0)),
                "再选科目字段任务数": str(field_counter.get("再选科目", 0)),
                "待人工判定字段任务数": str(field_counter.get("待人工判定字段", 0)),
                "PDF原页待核任务数": str(len(rows)),
                "湖北官方侧待核任务数": str(len(rows)),
                "高校辅证待核任务数": str(sum(row.get("高校辅证证据状态", "").startswith("S1") for row in rows)),
                "PDFOCR提示任务数": str(sum(is_true(row.get("是否有PDFOCR提示")) for row in rows)),
                "机器坐标提示任务数": str(sum(is_true(row.get("是否有机器坐标提示")) for row in rows)),
                "高校辅证线索任务数": str(sum(is_true(row.get("是否有高校辅证线索")) for row in rows)),
                "PDFOCR与高校辅证冲突任务数": str(sum(is_true(row.get("是否存在PDFOCR与高校冲突")) for row in rows)),
                "高校有线索但PDFOCR缺候选任务数": str(sum(row.get("PDFOCR与高校辅证关系桶", "").startswith("R2") for row in rows)),
                "仅PDFOCR候选待人工核页任务数": str(sum(row.get("PDFOCR与高校辅证关系桶", "").startswith("R3") for row in rows)),
                "PDFOCR与高校辅证一致仍需官方闭环任务数": str(sum(row.get("PDFOCR与高校辅证关系桶", "").startswith("R1") for row in rows)),
                "PDFOCR无候选任务数": str(sum(row.get("PDFOCR与高校辅证关系桶", "").startswith("R5") for row in rows)),
                "无候选需人工看图任务数": str(sum(row.get("候选提示综合桶", "").startswith("H4") for row in rows)),
                "需要人工直接看图任务数": str(sum(is_true(row.get("是否需要人工直接看图")) for row in rows)),
                "需要双人复核任务数": str(sum(is_true(row.get("是否需要双人复核")) for row in rows)),
                "字段事实写回可进入任务数": "0",
                "字段事实写回阻断任务数": str(len(rows)),
                "任务来源类型分布": counter_summary(source_counter),
                "OCR提示状态分布": counter_summary(ocr_counter),
                "冲突状态分布": counter_summary(conflict_counter),
                "人工核验泳道分布": counter_summary(lane_counter),
                "页列主阻断": page_status.get("字段闭环主阻断", ""),
                "页列建议下一步动作": page_status.get("建议下一步动作", ""),
                "完成条件": "PDF原页、湖北官方侧、必要高校辅证和双人复核状态均闭环后，才可进入字段写回评估",
                "公开安全策略": "公开层只保存页列状态桶、计数、集合SHA和门禁，不公开字段值、OCR原文、学校专业明细、人工记录或私有路径",
            }
        )
    return page_rows


def build_summary(task_rows: list[dict[str, str]], page_rows: list[dict[str, str]]) -> dict:
    field_counter = Counter()
    for row in task_rows:
        for field_name in split_field_names(row.get("字段名", "")):
            field_counter[field_name] += 1

    summary = {
        "status": "issue19_stable_foundation_first_closure_evidence_status_report_not_final",
        "generated_by": "build_issue19_first_closure_evidence_status_report.py",
        "source_first_closure_field_confirmation_public_ledger": source_path(FIELD_CONFIRM),
        "source_first_closure_task_review_public_ledger": source_path(TASK_REVIEW),
        "source_first_closure_pdf_ocr_candidate_public_audit": source_path(PDF_OCR_AUDIT),
        "source_first_closure_field_status_dashboard": source_path(FIELD_STATUS),
        "source_official_public_entry_status": source_path(OFFICIAL_STATUS),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_task_table": source_path(TASK_OUTPUT),
        "output_page_side_table": source_path(PAGE_OUTPUT),
        "task_row_grain": "第一闭环明细任务×公开证据状态",
        "page_row_grain": "PDF页码×版面列×公开证据状态汇总",
        "task_row_count": len(task_rows),
        "page_side_row_count": len(page_rows),
        "unique_pdf_page_count": len({row.get("来源页码", "") for row in page_rows if row.get("来源页码", "")}),
        "task_source_type_counts": dict(Counter(row.get("任务来源类型", "") for row in task_rows)),
        "field_task_counts_split": dict(field_counter),
        "pdf_source_status_counts": dict(Counter(row.get("PDF原页证据状态", "") for row in task_rows)),
        "ocr_status_counts": dict(Counter(row.get("OCR提示状态", "") for row in task_rows)),
        "machine_status_counts": dict(Counter(row.get("机器坐标提示状态", "") for row in task_rows)),
        "school_support_status_counts": dict(Counter(row.get("高校辅证证据状态", "") for row in task_rows)),
        "conflict_status_counts": dict(Counter(row.get("冲突状态", "") for row in task_rows)),
        "page_main_blocker_counts": dict(Counter(row.get("页列主阻断", "") for row in page_rows)),
        "execution_lane_counts": dict(Counter(row.get("执行泳道", "") for row in page_rows)),
        "pdf_ocr_hint_task_count": sum(is_true(row.get("是否有PDFOCR提示")) for row in task_rows),
        "machine_coordinate_hint_task_count": sum(is_true(row.get("是否有机器坐标提示")) for row in task_rows),
        "school_support_hint_task_count": sum(is_true(row.get("是否有高校辅证线索")) for row in task_rows),
        "pdf_school_conflict_task_count": sum(is_true(row.get("是否存在PDFOCR与高校冲突")) for row in task_rows),
        "missing_pdf_with_school_task_count": sum(row.get("PDFOCR与高校辅证关系桶", "").startswith("R2") for row in task_rows),
        "pdf_only_candidate_task_count": sum(row.get("PDFOCR与高校辅证关系桶", "").startswith("R3") for row in task_rows),
        "consistent_but_official_pending_task_count": sum(row.get("PDFOCR与高校辅证关系桶", "").startswith("R1") for row in task_rows),
        "pdf_ocr_no_candidate_task_count": sum(row.get("PDFOCR与高校辅证关系桶", "").startswith("R5") for row in task_rows),
        "no_candidate_manual_image_task_count": sum(row.get("候选提示综合桶", "").startswith("H4") for row in task_rows),
        "direct_image_review_required_count": sum(is_true(row.get("是否需要人工直接看图")) for row in task_rows),
        "double_review_required_count": sum(is_true(row.get("是否需要双人复核")) for row in task_rows),
        "pdf_pending_task_count": len(task_rows),
        "hubei_official_pending_task_count": len(task_rows),
        "school_support_pending_task_count": sum(row.get("高校辅证证据状态", "").startswith("S1") for row in task_rows),
        "three_way_pending_task_count": len(task_rows),
        "field_writeback_ready_count": 0,
        "field_writeback_blocked_task_count": len(task_rows),
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "public_boundary": "公开表只保存状态桶、计数、ID、SHA和门禁；不保存字段值、OCR原文、学校专业明细、人工记录或私有路径。",
        "next_use": "用于把第一闭环206条任务和37个页列按PDF原页、OCR提示、高校辅证、冲突状态和下一步动作排队；不得作为字段最终事实或志愿推荐依据。",
    }
    return summary


def validate_public_safety(task_rows, page_rows, summary) -> None:
    text = json.dumps(summary, ensure_ascii=False) + "\n"
    text += "\n".join(",".join(str(row.get(field, "")) for field in TASK_FIELDS) for row in task_rows)
    text += "\n"
    text += "\n".join(",".join(str(row.get(field, "")) for field in PAGE_FIELDS) for row in page_rows)
    leaked = [token for token in FORBIDDEN_TOKENS if token in text]
    if leaked:
        raise ValueError(f"public output contains forbidden token(s): {leaked[:10]}")


def validate_rows(task_rows, page_rows, summary) -> None:
    if len(task_rows) != 206:
        raise ValueError(f"expected 206 task rows, got {len(task_rows)}")
    if len(page_rows) != 37:
        raise ValueError(f"expected 37 page-side rows, got {len(page_rows)}")
    if len({row["第一闭环证据状态公开账本ID"] for row in task_rows}) != len(task_rows):
        raise ValueError("task evidence ids are not unique")
    if len({row["第一闭环页列证据状态汇总ID"] for row in page_rows}) != len(page_rows):
        raise ValueError("page evidence ids are not unique")
    for rows in (task_rows, page_rows):
        for row in rows:
            for field in FALSE_FIELDS:
                if row.get(field) != "false":
                    raise ValueError(f"non-final gate drifted: {field}={row.get(field)}")
    if summary.get("field_writeback_ready_count") != 0:
        raise ValueError("field writeback must remain blocked")


def main() -> None:
    task_rows, page_rows, summary = build_task_rows()
    validate_rows(task_rows, page_rows, summary)
    validate_public_safety(task_rows, page_rows, summary)
    write_csv(TASK_OUTPUT, task_rows, TASK_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
