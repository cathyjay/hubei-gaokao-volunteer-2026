#!/usr/bin/env python3
"""Build a public-safe 68-row G0 field-fact closure progress ledger."""

from __future__ import annotations

import csv
import hashlib
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"
PRIVATE_ROOT = ROOT / "private"
SCRIPTS = ROOT / "scripts"

RESOLUTION_GATE = WORKING / "issue19-first-closure-g0-conflict-field-resolution-gate-v1-public-ledger.csv"
CLOSURE_RESULT = WORKING / "issue19-first-closure-g0-conflict-field-evidence-closure-result-v1-public-ledger.csv"
GAP_TASKS = WORKING / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-public-ledger.csv"
REVIEW_LAUNCH = WORKING / "issue19-first-closure-g0-conflict-field-w0-w1-review-launch-v1-public-ledger.csv"
CANDIDATE_TRIAGE = WORKING / "issue19-first-closure-g0-conflict-field-w0-w1-candidate-triage-v1-public-ledger.csv"
FIELD_BACKLINK = WORKING / "issue19-w0-b0-school-source-field-backlink-queue-public-ledger.csv"
FIELD_STATUS = WORKING / "issue19-first-closure-field-verification-status-public-ledger.csv"
FIELD_CONFIRMATION = WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
PRIVATE_OVERLAY = (
    PRIVATE_ROOT
    / "review-assets/issue19-g0-conflict-field-review-overlay-v1/g0-conflict-field-review-private-overlay.csv"
)
CANDIDATE_SCRIPT = SCRIPTS / "build_issue19_first_closure_g0_conflict_field_w0_w1_candidate_triage_v1.py"

OUTPUT = WORKING / "issue19-first-closure-g0-field-closure-progress-v1-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-first-closure-g0-field-closure-progress-v1-page-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-g0-field-closure-progress-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_field_closure_progress_v1"

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "是否允许进入私有写回评审",
]

LEDGER_FIELDS = [
    "G0字段闭环进度ID",
    "来源G0冲突字段准出门禁",
    "来源G0冲突字段补证闭环结果",
    "来源G0冲突字段补证缺口任务",
    "来源G0冲突字段W0W1开核执行清单",
    "来源G0冲突字段W0W1候选分层",
    "来源W0B0高校源字段回接队列",
    "来源第一闭环字段核验状态",
    "来源第一闭环字段确认公开账本",
    "来源私有G0字段复核Overlay",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "字段闭环序号",
    "第一闭环事实范围缺口公开账本ID",
    "第一闭环字段事实公开账本ID",
    "第一闭环字段核验状态ID",
    "稳定基座第一闭环明细任务ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "事实域",
    "事实类型",
    "字段名",
    "字段事实状态",
    "字段核验优先级",
    "候选分层桶",
    "PDFOCR与高校辅证关系桶",
    "是否有PDFOCR提示",
    "是否有高校辅证线索",
    "是否存在PDFOCR与高校冲突",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "PDF原页记录状态",
    "湖北官方记录状态",
    "高校辅证人工核验状态",
    "冲突处理状态",
    "双人复核状态",
    "三方一致性闭环状态",
    "字段确认状态",
    "写回评审状态",
    "补证闭环状态",
    "字段写回门禁状态",
    "主阻断桶",
    "必要证据缺口数",
    "证据通道数",
    "当前可并行通道数",
    "前置阻断通道数",
    "证据通道分布",
    "证据通道状态分布",
    "阻断桶分布",
    "高校源桥接桶",
    "高校源回接泳道",
    "高校源可DoubleCheck提示",
    "结构化接入候选数",
    "计划数一致提示数",
    "计划数冲突提示数",
    "闭环准出阶段",
    "下一步动作",
    "来源缺口任务集合SHA256",
    "来源开核执行包集合SHA256",
    "来源回接记录SHA256",
    "来源私有Overlay记录集合SHA256",
    "来源私有Overlay文件SHA256",
    "公开安全策略",
]

PAGE_FIELDS = [
    "G0字段闭环进度页列汇总ID",
    "来源G0字段闭环进度清单",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "页列汇总序号",
    "页码版面键",
    "来源页码",
    "版面列",
    "字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "候选分层桶分布",
    "字段事实状态分布",
    "闭环准出阶段分布",
    "PDF原页待补字段数",
    "湖北官方待补字段数",
    "高校辅证待补字段数",
    "冲突处理待补字段数",
    "双人复核待补字段数",
    "三方闭环待补字段数",
    "字段确认待补字段数",
    "写回评审待补字段数",
    "证据通道数",
    "当前可并行通道数",
    "前置阻断通道数",
    "高校源可DoubleCheck字段数",
    "结构化接入候选字段数",
    "页列下一步动作",
    "字段事实集合SHA256",
    "缺口任务集合SHA256",
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
    "学校名称",
    "专业名称",
    "专业代号",
    "字段读数",
    "人工读数",
    "字段值",
    "候选值",
    "字段确认值",
    "OCR正文",
    "OCR文本",
    "OCR原文",
    "截图路径",
    "人工复核备注",
    "复核人员",
    "复核结论",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
    "录取概率",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: clean(row.get(field, "")) for field in fields})


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def stable_id(prefix: str, parts: list[str]) -> str:
    return f"{prefix}-{hashlib.sha256('|'.join(clean(part) for part in parts).encode('utf-8')).hexdigest()[:16]}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_values(values) -> str:
    vals = sorted({clean(value) for value in values if clean(value)})
    return hashlib.sha256("|".join(vals).encode("utf-8")).hexdigest() if vals else ""


def add_false_fields(row: dict[str, str]) -> None:
    for field in FALSE_FIELDS:
        row[field] = "false"


def as_int(value: object) -> int:
    try:
        return int(clean(value))
    except ValueError:
        return 0


def count_value(rows: list[dict[str, str]], field: str, value: str) -> int:
    return sum(1 for row in rows if clean(row.get(field, "")) == value)


def dist(rows: list[dict[str, str]], field: str) -> str:
    counter = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter))


def counter_text(counter: Counter) -> str:
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter)) if counter else ""


def status_from_gap(flag: str, pending_status: str, closed_status: str = "closed") -> str:
    return pending_status if clean(flag) == "true" else closed_status


def closure_stage(row: dict[str, str], bucket: str) -> str:
    if clean(row.get("PDF原页记录缺口")) == "true":
        if bucket == "C0-双侧候选冲突优先核":
            return "F0-先补PDF原页并处理冲突"
        if bucket == "C3-仅高校辅证候选需核原页":
            return "F1-高校线索回PDF原页"
        if bucket == "C2-仅PDFOCR候选需补辅证":
            return "F2-PDFOCR候选需补辅证并核原页"
        return "F3-补PDF原页基础记录"
    if clean(row.get("湖北官方记录缺口")) == "true":
        return "F4-补湖北官方侧记录"
    if clean(row.get("三方一致性缺口")) == "true":
        return "F5-三方一致性闭环"
    if clean(row.get("字段确认缺口")) == "true":
        return "F6-字段确认待填写"
    if clean(row.get("写回评审缺口")) == "true":
        return "F7-写回评审待判断"
    return "F8-字段事实准出待复核"


def next_action(stage: str) -> str:
    if stage.startswith("F0"):
        return "核PDF原页；补湖北官方侧记录；冲突字段进入双人复核。"
    if stage.startswith("F1"):
        return "用高校线索定位原页；补PDF原页记录后再核湖北官方侧。"
    if stage.startswith("F2"):
        return "核PDF原页候选；补高校或官方侧辅证后再做三方一致性。"
    if stage.startswith("F3"):
        return "先补PDF原页记录，再进入湖北官方侧和三方闭环。"
    if stage.startswith("F4"):
        return "补湖北官方侧记录；高校源只能作double check。"
    if stage.startswith("F5"):
        return "完成PDF原页、湖北官方侧、高校源三方一致性判断。"
    if stage.startswith("F6"):
        return "填写字段确认状态，仍不得直接进入推荐。"
    if stage.startswith("F7"):
        return "进入写回评审前再次检查三方闭环和门禁。"
    return "复核准出门禁；确认无缺口后再进入私有写回评审。"


def public_safety_check(paths: list[Path]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token and token in text]
    if hits:
        raise SystemExit(f"Public output contains forbidden tokens: {hits[:20]}")


def main() -> None:
    candidate_ns = runpy.run_path(
        str(CANDIDATE_SCRIPT),
        run_name=f"__{CANDIDATE_SCRIPT.stem}_runtime_for_progress",
    )
    candidate_bucket = candidate_ns["candidate_bucket"]

    gate_rows = read_csv(RESOLUTION_GATE)
    closure_rows = read_csv(CLOSURE_RESULT)
    gap_rows = read_csv(GAP_TASKS)
    launch_rows = read_csv(REVIEW_LAUNCH)
    candidate_rows = read_csv(CANDIDATE_TRIAGE)
    backlink_rows = read_csv(FIELD_BACKLINK)
    field_status_rows = read_csv(FIELD_STATUS)
    confirmation_rows = read_csv(FIELD_CONFIRMATION)
    private_rows = read_csv(PRIVATE_OVERLAY)

    closure_by_fact = {clean(row.get("第一闭环事实范围缺口公开账本ID")): row for row in closure_rows}
    backlink_by_fact = {clean(row.get("第一闭环事实范围缺口公开账本ID")): row for row in backlink_rows}
    private_by_fact: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in private_rows:
        private_by_fact[clean(row.get("第一闭环事实范围缺口公开账本ID"))].append(row)
    gap_by_fact: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in gap_rows:
        gap_by_fact[clean(row.get("第一闭环事实范围缺口公开账本ID"))].append(row)
    launch_by_page_channel: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in launch_rows:
        launch_by_page_channel[(clean(row.get("页码版面键")), clean(row.get("证据通道序号")))].append(row)
    field_status_by_id = {clean(row.get("第一闭环字段核验状态ID")): row for row in field_status_rows}
    confirmation_by_task = {
        clean(row.get("稳定基座第一闭环明细任务ID")): row for row in confirmation_rows
    }

    ledger_rows: list[dict[str, str]] = []
    sorted_gate_rows = sorted(
        gate_rows,
        key=lambda row: (
            as_int(row.get("来源页码")),
            clean(row.get("版面列")),
            clean(row.get("稳定基座第一闭环明细任务ID")),
            clean(row.get("字段名")),
        ),
    )
    for index, gate in enumerate(sorted_gate_rows, start=1):
        fact_id = clean(gate.get("第一闭环事实范围缺口公开账本ID"))
        task_id = clean(gate.get("稳定基座第一闭环明细任务ID"))
        page_key = clean(gate.get("页码版面键"))
        closure = closure_by_fact.get(fact_id, {})
        backlink = backlink_by_fact.get(fact_id, {})
        private_items = private_by_fact.get(fact_id, [])
        gap_items = gap_by_fact.get(fact_id, [])
        launch_items = []
        for gap in gap_items:
            launch_items.extend(launch_by_page_channel.get((page_key, clean(gap.get("证据通道序号"))), []))
        field_status = field_status_by_id.get(clean(gate.get("第一闭环字段核验状态ID")), {})
        confirmation = confirmation_by_task.get(task_id, {})
        bucket = candidate_bucket(private_items[0]) if private_items else "C9-无私有候选分层"
        stage = closure_stage(gate, bucket)
        out = {
            "G0字段闭环进度ID": stable_id("G0-FIELD-PROGRESS", [fact_id, str(index)]),
            "来源G0冲突字段准出门禁": source_path(RESOLUTION_GATE),
            "来源G0冲突字段补证闭环结果": source_path(CLOSURE_RESULT),
            "来源G0冲突字段补证缺口任务": source_path(GAP_TASKS),
            "来源G0冲突字段W0W1开核执行清单": source_path(REVIEW_LAUNCH),
            "来源G0冲突字段W0W1候选分层": source_path(CANDIDATE_TRIAGE),
            "来源W0B0高校源字段回接队列": source_path(FIELD_BACKLINK),
            "来源第一闭环字段核验状态": source_path(FIELD_STATUS),
            "来源第一闭环字段确认公开账本": source_path(FIELD_CONFIRMATION),
            "来源私有G0字段复核Overlay": "g0_conflict_field_review_private_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段事实",
            "任务粒度": "68个G0字段事实逐项闭环进度",
            "字段闭环序号": str(index),
            "第一闭环事实范围缺口公开账本ID": fact_id,
            "第一闭环字段事实公开账本ID": clean(gate.get("第一闭环字段事实公开账本ID")),
            "第一闭环字段核验状态ID": clean(gate.get("第一闭环字段核验状态ID")),
            "稳定基座第一闭环明细任务ID": task_id,
            "页码版面键": page_key,
            "来源页码": clean(gate.get("来源页码")),
            "版面列": clean(gate.get("版面列")),
            "专业行ID": clean(gate.get("专业行ID")),
            "专业组出现ID": clean(gate.get("专业组出现ID")),
            "院校代码": clean(gate.get("院校代码")),
            "事实域": clean(gate.get("事实域")),
            "事实类型": clean(gate.get("事实类型")),
            "字段名": clean(gate.get("字段名")),
            "字段事实状态": clean(gate.get("字段事实状态")),
            "字段核验优先级": clean(gate.get("字段核验优先级")),
            "候选分层桶": bucket,
            "PDFOCR与高校辅证关系桶": clean(gate.get("PDFOCR与高校辅证关系桶")),
            "是否有PDFOCR提示": clean(gate.get("是否有PDFOCR提示")),
            "是否有高校辅证线索": clean(gate.get("是否有高校辅证线索")),
            "是否存在PDFOCR与高校冲突": clean(gate.get("是否存在PDFOCR与高校冲突")),
            "是否需要人工直接看图": clean(gate.get("是否需要人工直接看图")),
            "是否需要双人复核": clean(gate.get("是否需要双人复核")),
            "PDF原页记录状态": clean(closure.get("PDF原页核验结果状态")) or status_from_gap(gate.get("PDF原页记录缺口"), "pending_pdf_page_review"),
            "湖北官方记录状态": clean(closure.get("湖北官方侧核验状态")) or status_from_gap(gate.get("湖北官方记录缺口"), "pending_hubei_official_plan_review"),
            "高校辅证人工核验状态": clean(closure.get("高校官网辅证核验状态")) or status_from_gap(gate.get("高校辅证记录缺口"), "pending_school_source_review"),
            "冲突处理状态": clean(closure.get("冲突处理状态")) or status_from_gap(gate.get("冲突处理缺口"), "pending_conflict_resolution"),
            "双人复核状态": clean(closure.get("双人复核结果状态")) or status_from_gap(gate.get("双人复核缺口"), "pending_double_review", "not_required"),
            "三方一致性闭环状态": clean(closure.get("三方闭环状态")) or status_from_gap(gate.get("三方一致性缺口"), "pending_three_way_closure"),
            "字段确认状态": clean(closure.get("字段确认状态")) or clean(confirmation.get("私有字段确认工作台状态")) or "blocked",
            "写回评审状态": clean(closure.get("字段写回评审状态")) or clean(confirmation.get("字段事实写回评估状态")) or "blocked",
            "补证闭环状态": clean(closure.get("补证闭环状态")) or "closure_blocked_missing_required_evidence",
            "字段写回门禁状态": clean(backlink.get("字段事实写回状态")) or clean(field_status.get("字段事实写回状态")) or "blocked_until_pdf_hubei_school_three_way_closure",
            "主阻断桶": clean(closure.get("当前主阻断桶")) or clean(gate.get("主缺口桶")),
            "必要证据缺口数": clean(closure.get("必要证据缺口数")) or clean(gate.get("必要缺口数")),
            "证据通道数": str(len(gap_items)),
            "当前可并行通道数": str(count_value(gap_items, "是否当前可并行执行", "true")),
            "前置阻断通道数": str(count_value(gap_items, "是否当前可并行执行", "false")),
            "证据通道分布": dist(gap_items, "证据通道"),
            "证据通道状态分布": dist(gap_items, "证据缺口任务状态"),
            "阻断桶分布": dist(gap_items, "当前阻断桶"),
            "高校源桥接桶": clean(backlink.get("高校源桥接桶")) or clean(gate.get("高校源桥接桶")),
            "高校源回接泳道": clean(backlink.get("回接泳道")) or clean(gate.get("回接泳道")),
            "高校源可DoubleCheck提示": clean(backlink.get("高校源可作double_check提示")) or "false",
            "结构化接入候选数": clean(backlink.get("结构化接入候选数")) or clean(gate.get("结构化接入候选数")),
            "计划数一致提示数": clean(backlink.get("C4C6计划数一致候选数合计")) or "0",
            "计划数冲突提示数": clean(backlink.get("C4C6计划数冲突候选数合计")) or "0",
            "闭环准出阶段": stage,
            "下一步动作": next_action(stage),
            "来源缺口任务集合SHA256": sha256_values(row.get("G0冲突字段补证缺口任务公开账本ID") for row in gap_items),
            "来源开核执行包集合SHA256": sha256_values(row.get("G0冲突字段W0W1开核执行清单ID") for row in launch_items),
            "来源回接记录SHA256": sha256_values([backlink.get("高校源字段回接队列ID", "")]),
            "来源私有Overlay记录集合SHA256": sha256_values(row.get("G0私有字段复核记录ID") for row in private_items),
            "来源私有Overlay文件SHA256": sha256_file(PRIVATE_OVERLAY),
            "公开安全策略": "只公开逐字段状态、通道分布、ID和SHA；不公开敏感明细、学校专业文本或最终志愿建议。",
        }
        add_false_fields(out)
        ledger_rows.append(out)

    page_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ledger_rows:
        page_groups[row.get("页码版面键", "")].append(row)

    page_rows: list[dict[str, str]] = []
    for index, (page_key, items) in enumerate(
        sorted(
            page_groups.items(),
            key=lambda item: (as_int(item[1][0].get("来源页码")), clean(item[1][0].get("版面列"))),
        ),
        start=1,
    ):
        first = items[0]
        out = {
            "G0字段闭环进度页列汇总ID": stable_id("G0-FIELD-PROGRESS-PAGE", [page_key, str(index)]),
            "来源G0字段闭环进度清单": source_path(OUTPUT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "10个G0页列字段事实闭环进度汇总",
            "页列汇总序号": str(index),
            "页码版面键": page_key,
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "字段事实数": str(len(items)),
            "涉及任务数": str(len({row.get("稳定基座第一闭环明细任务ID") for row in items})),
            "涉及专业行数": str(len({row.get("专业行ID") for row in items})),
            "涉及院校代码数": str(len({row.get("院校代码") for row in items})),
            "字段名分布": dist(items, "字段名"),
            "候选分层桶分布": dist(items, "候选分层桶"),
            "字段事实状态分布": dist(items, "字段事实状态"),
            "闭环准出阶段分布": dist(items, "闭环准出阶段"),
            "PDF原页待补字段数": str(count_value(items, "PDF原页记录状态", "pending_pdf_page_review")),
            "湖北官方待补字段数": str(count_value(items, "湖北官方记录状态", "pending_hubei_official_plan_review")),
            "高校辅证待补字段数": str(
                count_value(items, "高校辅证人工核验状态", "school_source_seed_present_pending_manual_review")
                + count_value(items, "高校辅证人工核验状态", "school_source_pending")
            ),
            "冲突处理待补字段数": str(count_value(items, "冲突处理状态", "pending_conflict_resolution")),
            "双人复核待补字段数": str(count_value(items, "双人复核状态", "pending_double_review")),
            "三方闭环待补字段数": str(count_value(items, "三方一致性闭环状态", "blocked_missing_pdf")),
            "字段确认待补字段数": str(count_value(items, "字段确认状态", "blocked")),
            "写回评审待补字段数": str(count_value(items, "写回评审状态", "blocked_until_required_evidence_closed")),
            "证据通道数": str(sum(as_int(row.get("证据通道数")) for row in items)),
            "当前可并行通道数": str(sum(as_int(row.get("当前可并行通道数")) for row in items)),
            "前置阻断通道数": str(sum(as_int(row.get("前置阻断通道数")) for row in items)),
            "高校源可DoubleCheck字段数": str(count_value(items, "高校源可DoubleCheck提示", "true")),
            "结构化接入候选字段数": str(count_value(items, "高校源桥接桶", "B1-已有结构化接入候选，可作为高校侧double check提示")),
            "页列下一步动作": "优先补PDF原页和湖北官方侧；冲突字段完成双人复核后再三方闭环。",
            "字段事实集合SHA256": sha256_values(row.get("第一闭环事实范围缺口公开账本ID") for row in items),
            "缺口任务集合SHA256": sha256_values(row.get("来源缺口任务集合SHA256") for row in items),
            "公开安全策略": "页列汇总只公开状态分布、数量和SHA；不公开敏感明细或学校专业文本。",
        }
        add_false_fields(out)
        page_rows.append(out)

    summary = {
        "status": "issue19_first_closure_g0_field_closure_progress_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_resolution_gate": source_path(RESOLUTION_GATE),
        "source_resolution_gate_sha256": sha256_file(RESOLUTION_GATE),
        "source_closure_result": source_path(CLOSURE_RESULT),
        "source_closure_result_sha256": sha256_file(CLOSURE_RESULT),
        "source_gap_tasks": source_path(GAP_TASKS),
        "source_gap_tasks_sha256": sha256_file(GAP_TASKS),
        "source_review_launch": source_path(REVIEW_LAUNCH),
        "source_review_launch_sha256": sha256_file(REVIEW_LAUNCH),
        "source_candidate_triage": source_path(CANDIDATE_TRIAGE),
        "source_candidate_triage_sha256": sha256_file(CANDIDATE_TRIAGE),
        "source_field_backlink": source_path(FIELD_BACKLINK),
        "source_field_backlink_sha256": sha256_file(FIELD_BACKLINK),
        "source_field_status": source_path(FIELD_STATUS),
        "source_field_status_sha256": sha256_file(FIELD_STATUS),
        "source_field_confirmation": source_path(FIELD_CONFIRMATION),
        "source_field_confirmation_sha256": sha256_file(FIELD_CONFIRMATION),
        "source_private_overlay": "g0_conflict_field_review_private_overlay_not_public",
        "source_private_overlay_sha256": sha256_file(PRIVATE_OVERLAY),
        "output": source_path(OUTPUT),
        "page_output": source_path(PAGE_OUTPUT),
        "row_count": len(ledger_rows),
        "page_summary_row_count": len(page_rows),
        "source_resolution_gate_row_count": len(gate_rows),
        "source_closure_result_row_count": len(closure_rows),
        "source_gap_task_row_count": len(gap_rows),
        "source_review_launch_row_count": len(launch_rows),
        "source_candidate_triage_row_count": len(candidate_rows),
        "source_field_backlink_row_count": len(backlink_rows),
        "unique_fact_scope_count": len({row.get("第一闭环事实范围缺口公开账本ID") for row in ledger_rows}),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID") for row in ledger_rows}),
        "unique_page_side_count": len({row.get("页码版面键") for row in ledger_rows}),
        "field_counts": dict(Counter(row.get("字段名") for row in ledger_rows)),
        "candidate_bucket_counts": dict(Counter(row.get("候选分层桶") for row in ledger_rows)),
        "field_status_counts": dict(Counter(row.get("字段事实状态") for row in ledger_rows)),
        "closure_stage_counts": dict(Counter(row.get("闭环准出阶段") for row in ledger_rows)),
        "pdf_pending_count": count_value(ledger_rows, "PDF原页记录状态", "pending_pdf_page_review"),
        "hubei_official_pending_count": count_value(ledger_rows, "湖北官方记录状态", "pending_hubei_official_plan_review"),
        "school_support_pending_count": (
            count_value(ledger_rows, "高校辅证人工核验状态", "school_source_seed_present_pending_manual_review")
            + count_value(ledger_rows, "高校辅证人工核验状态", "school_source_pending")
        ),
        "conflict_resolution_pending_count": count_value(ledger_rows, "冲突处理状态", "pending_conflict_resolution"),
        "double_review_pending_count": count_value(ledger_rows, "双人复核状态", "pending_double_review"),
        "three_way_pending_count": count_value(ledger_rows, "三方一致性闭环状态", "blocked_missing_pdf"),
        "field_confirmation_pending_count": count_value(ledger_rows, "字段确认状态", "blocked"),
        "writeback_review_pending_count": count_value(ledger_rows, "写回评审状态", "blocked_until_required_evidence_closed"),
        "evidence_channel_count": sum(as_int(row.get("证据通道数")) for row in ledger_rows),
        "parallel_channel_count": sum(as_int(row.get("当前可并行通道数")) for row in ledger_rows),
        "blocked_channel_count": sum(as_int(row.get("前置阻断通道数")) for row in ledger_rows),
        "structured_candidate_fact_count": count_value(ledger_rows, "高校源桥接桶", "B1-已有结构化接入候选，可作为高校侧double check提示"),
        "school_double_check_fact_count": count_value(ledger_rows, "高校源可DoubleCheck提示", "true"),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只描述68个G0字段事实的证据闭环进度；高校源只作double check，不替代湖北官方计划，不确认字段事实，不进入志愿建议。",
    }

    write_csv(OUTPUT, ledger_rows, LEDGER_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    public_safety_check([OUTPUT, PAGE_OUTPUT, SUMMARY_OUTPUT])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
