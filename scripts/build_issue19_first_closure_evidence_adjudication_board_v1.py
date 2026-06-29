#!/usr/bin/env python3
"""Build a public-safe adjudication board for the first closure batch.

The board keeps the full 206 high-risk task scope, then overlays the G0 W0/W1
field-fact slice. It exposes only IDs, buckets, counts, and gate states. It does
not publish OCR text, candidate readings, private paths, school/major names, or
final recommendations.
"""

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

VERIFICATION_RESULT = WORKING / "issue19-first-closure-verification-result-public-ledger.csv"
VERIFICATION_PAGE = WORKING / "issue19-first-closure-verification-result-page-summary.csv"
FIELD_CONFIRMATION = WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
G0_GAP_TASKS = WORKING / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-public-ledger.csv"
W0_W1_CANDIDATE = WORKING / "issue19-first-closure-g0-conflict-field-w0-w1-candidate-triage-v1-public-ledger.csv"
W0_W1_CANDIDATE_PAGE = WORKING / "issue19-first-closure-g0-conflict-field-w0-w1-candidate-triage-v1-page-summary.csv"
FIELD_BACKLINK = WORKING / "issue19-w0-b0-school-source-field-backlink-queue-public-ledger.csv"
PRIVATE_OVERLAY = (
    PRIVATE_ROOT
    / "review-assets/issue19-g0-conflict-field-review-overlay-v1/g0-conflict-field-review-private-overlay.csv"
)
CANDIDATE_SCRIPT = SCRIPTS / "build_issue19_first_closure_g0_conflict_field_w0_w1_candidate_triage_v1.py"

OUTPUT = WORKING / "issue19-first-closure-evidence-adjudication-board-v1-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-first-closure-evidence-adjudication-board-v1-page-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-evidence-adjudication-board-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_evidence_adjudication_board_v1"

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

BOARD_FIELDS = [
    "第一闭环证据仲裁ID",
    "来源第一闭环核验结果看板",
    "来源第一闭环字段确认公开账本",
    "来源G0字段补证缺口任务公开账本",
    "来源G0字段W0W1候选分层清单",
    "来源W0B0高校源字段回接队列",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "仲裁序号",
    "第一闭环核验结果ID",
    "第一闭环字段确认公开账本ID",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环页列包ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "任务来源类型",
    "字段名",
    "执行泳道",
    "核验动作层级",
    "任务结果桶",
    "PDF原页证据状态",
    "OCR提示状态",
    "机器坐标提示状态",
    "高校官网辅证状态",
    "湖北官方侧状态",
    "冲突状态",
    "三方闭环状态",
    "字段写回门禁",
    "字段确认公开状态",
    "双人复核公开状态",
    "G0字段闭环命中状态",
    "G0字段事实数",
    "G0缺口任务数",
    "G0当前可并行通道数",
    "G0前置阻断通道数",
    "G0待PDF原页记录数",
    "G0待湖北官方记录数",
    "G0待高校辅证核验数",
    "G0待冲突处理数",
    "G0待双人复核数",
    "G0待三方一致性数",
    "G0待字段确认数",
    "G0待写回评审数",
    "G0候选分层分布",
    "G0候选主桶",
    "G0高校源回接事实数",
    "G0结构化接入候选字段数",
    "G0高校源可DoubleCheck字段数",
    "G0计划数一致提示字段数",
    "G0计划数冲突提示字段数",
    "证据准出阶段",
    "证据准出阻断原因",
    "下一步最小核验动作",
    "任务内G0事实集合SHA256",
    "任务内G0缺口任务集合SHA256",
    "任务内G0回接集合SHA256",
    "公开安全策略",
]

PAGE_FIELDS = [
    "第一闭环证据仲裁页列汇总ID",
    "来源第一闭环证据仲裁表",
    "来源第一闭环核验结果页列汇总",
    "来源G0字段W0W1候选分层页列汇总",
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
    "第一闭环任务数",
    "G0命中任务数",
    "G0字段事实数",
    "G0缺口任务数",
    "G0当前可并行通道数",
    "G0前置阻断通道数",
    "G0待PDF原页记录数",
    "G0待湖北官方记录数",
    "G0待高校辅证核验数",
    "G0待冲突处理数",
    "G0待双人复核数",
    "G0待三方一致性数",
    "G0待字段确认数",
    "G0待写回评审数",
    "任务结果桶分布",
    "PDF原页状态分布",
    "OCR提示状态分布",
    "高校官网辅证状态分布",
    "冲突状态分布",
    "证据准出阶段分布",
    "G0候选分层分布",
    "页列最小核验动作",
    "页列任务集合SHA256",
    "页列G0事实集合SHA256",
    "页列G0缺口任务集合SHA256",
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


def dist(rows: list[dict[str, str]], field: str) -> str:
    counter = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter))


def counter_text(counter: Counter) -> str:
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter)) if counter else ""


def merge_dist_text(values: list[str]) -> str:
    counter = Counter()
    for value in values:
        for part in clean(value).split("；"):
            if not part or ":" not in part:
                continue
            key, raw_count = part.rsplit(":", 1)
            try:
                counter[key] += int(raw_count)
            except ValueError:
                continue
    return counter_text(counter)


def sum_field(rows: list[dict[str, str]], field: str) -> int:
    return sum(as_int(row.get(field, "")) for row in rows)


def count_value(rows: list[dict[str, str]], field: str, value: str) -> int:
    return sum(1 for row in rows if clean(row.get(field, "")) == value)


def count_unique_when(rows: list[dict[str, str]], id_field: str, flag_field: str, value: str = "true") -> int:
    return len({
        clean(row.get(id_field, ""))
        for row in rows
        if clean(row.get(id_field, "")) and clean(row.get(flag_field, "")) == value
    })


def choose_stage(row: dict[str, str], g0_tasks: list[dict[str, str]], bucket_counts: Counter) -> str:
    if not g0_tasks:
        return "A3-非G0本轮子集但仍待第一闭环"
    if bucket_counts.get("C0-双侧候选冲突优先核"):
        return "A0-G0候选冲突阻断准出"
    if bucket_counts.get("C2-仅PDFOCR候选需补辅证") or bucket_counts.get("C3-仅高校辅证候选需核原页"):
        return "A1-G0单侧候选需补另一侧"
    if bucket_counts.get("C1-双侧候选一致但仍待核"):
        return "A2-G0多源一致但仍待原页和湖北官方"
    if clean(row.get("是否需要人工直接看图", "")) == "true":
        return "A4-需人工看PDF原页补候选"
    return "A5-常规第一闭环待核"


def blocker_for_stage(stage: str, g0_tasks: list[dict[str, str]]) -> str:
    if not g0_tasks:
        return "未进入G0 W0/W1字段事实子集；仍按第一闭环总看板待核。"
    blockers = Counter(clean(row.get("当前阻断桶", "")) for row in g0_tasks if clean(row.get("当前阻断桶", "")))
    if blockers:
        return counter_text(blockers)
    if stage.startswith("A2"):
        return "PDF原页记录、湖北官方记录、字段确认和写回评审仍未完成。"
    return "G0字段事实存在待补证通道，尚未满足准出条件。"


def next_action(stage: str) -> str:
    if stage.startswith("A0"):
        return "先核PDF原页并补湖北官方侧记录；冲突字段完成双人复核后再做三方一致性。"
    if stage.startswith("A1"):
        return "补齐缺失侧证据；仅高校线索需回PDF原页，仅PDFOCR线索需补高校或官方侧辅证。"
    if stage.startswith("A2"):
        return "保留一致线索但不得准出；补PDF原页人工记录和湖北官方记录。"
    if stage.startswith("A3"):
        return "按第一闭环总看板继续核页；本表仅追踪G0 W0/W1字段事实子集。"
    if stage.startswith("A4"):
        return "人工看PDF原页补候选，再进入字段事实三方闭环。"
    return "继续按第一闭环证据状态表补齐必要证据。"


def public_safety_check(paths: list[Path]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token and token in text]
    if hits:
        raise SystemExit(f"Public output contains forbidden tokens: {hits[:20]}")


def main() -> None:
    candidate_ns = runpy.run_path(
        str(CANDIDATE_SCRIPT),
        run_name=f"__{CANDIDATE_SCRIPT.stem}_runtime_for_adjudication",
    )
    candidate_bucket = candidate_ns["candidate_bucket"]
    candidate_main_bucket = candidate_ns["candidate_main_bucket"]

    verification_rows = read_csv(VERIFICATION_RESULT)
    verification_page_rows = read_csv(VERIFICATION_PAGE)
    confirmation_rows = read_csv(FIELD_CONFIRMATION)
    gap_rows = read_csv(G0_GAP_TASKS)
    candidate_rows = read_csv(W0_W1_CANDIDATE)
    candidate_page_rows = read_csv(W0_W1_CANDIDATE_PAGE)
    backlink_rows = read_csv(FIELD_BACKLINK)
    private_rows = read_csv(PRIVATE_OVERLAY)

    confirmation_by_task = {
        clean(row.get("稳定基座第一闭环明细任务ID")): row for row in confirmation_rows
    }
    gap_by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    gap_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in gap_rows:
        gap_by_task[clean(row.get("稳定基座第一闭环明细任务ID"))].append(row)
        gap_by_page[clean(row.get("页码版面键"))].append(row)

    private_by_fact: dict[str, list[dict[str, str]]] = defaultdict(list)
    private_by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    private_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in private_rows:
        fact_id = clean(row.get("第一闭环事实范围缺口公开账本ID"))
        task_id = clean(row.get("稳定基座第一闭环明细任务ID"))
        page_key = clean(row.get("页码版面键"))
        private_by_fact[fact_id].append(row)
        private_by_task[task_id].append(row)
        private_by_page[page_key].append(row)

    backlink_by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    backlink_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in backlink_rows:
        backlink_by_task[clean(row.get("稳定基座第一闭环明细任务ID"))].append(row)
        backlink_by_page[clean(row.get("页码版面键"))].append(row)

    candidate_packets_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidate_rows:
        candidate_packets_by_page[clean(row.get("页码版面键"))].append(row)
    candidate_page_by_page = {clean(row.get("页码版面键")): row for row in candidate_page_rows}

    board_rows: list[dict[str, str]] = []
    for index, row in enumerate(verification_rows, start=1):
        task_id = clean(row.get("稳定基座第一闭环明细任务ID"))
        page_key = clean(row.get("页码版面键"))
        confirmation = confirmation_by_task.get(task_id, {})
        task_gap_rows = gap_by_task.get(task_id, [])
        task_private_rows = private_by_task.get(task_id, [])
        task_backlink_rows = backlink_by_task.get(task_id, [])
        bucket_counts = Counter(candidate_bucket(item) for item in task_private_rows)
        main_bucket = candidate_main_bucket(task_private_rows) if task_private_rows else "T9-非G0候选分层范围"
        stage = choose_stage(row, task_gap_rows, bucket_counts)
        g0_fact_ids = [clean(item.get("第一闭环事实范围缺口公开账本ID")) for item in task_gap_rows]
        out = {
            "第一闭环证据仲裁ID": stable_id("FIRST-ADJ", [task_id, str(index)]),
            "来源第一闭环核验结果看板": source_path(VERIFICATION_RESULT),
            "来源第一闭环字段确认公开账本": source_path(FIELD_CONFIRMATION),
            "来源G0字段补证缺口任务公开账本": source_path(G0_GAP_TASKS),
            "来源G0字段W0W1候选分层清单": source_path(W0_W1_CANDIDATE),
            "来源W0B0高校源字段回接队列": source_path(FIELD_BACKLINK),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环高风险明细任务",
            "任务粒度": "206明细任务叠加G0 W0/W1字段事实准出状态",
            "仲裁序号": str(index),
            "第一闭环核验结果ID": clean(row.get("第一闭环核验结果ID")),
            "第一闭环字段确认公开账本ID": clean(confirmation.get("第一闭环字段确认公开账本ID")),
            "稳定基座第一闭环明细任务ID": task_id,
            "稳定基座第一闭环页列包ID": clean(row.get("稳定基座第一闭环页列包ID")),
            "页码版面键": page_key,
            "来源页码": clean(row.get("来源页码")),
            "版面列": clean(row.get("版面列")),
            "专业行ID": clean(row.get("专业行ID")),
            "专业组出现ID": clean(row.get("专业组出现ID")),
            "院校代码": clean(row.get("院校代码")),
            "任务来源类型": clean(row.get("任务来源类型")),
            "字段名": clean(row.get("字段名")),
            "执行泳道": clean(row.get("执行泳道")),
            "核验动作层级": clean(row.get("核验动作层级")),
            "任务结果桶": clean(row.get("任务结果桶")),
            "PDF原页证据状态": clean(row.get("PDF原页证据状态")),
            "OCR提示状态": clean(row.get("OCR提示状态")),
            "机器坐标提示状态": clean(row.get("机器坐标提示状态")),
            "高校官网辅证状态": clean(row.get("高校辅证证据状态")),
            "湖北官方侧状态": clean(row.get("湖北官方侧状态")),
            "冲突状态": clean(row.get("冲突状态")),
            "三方闭环状态": clean(row.get("三方闭环状态")),
            "字段写回门禁": clean(row.get("字段写回门禁")),
            "字段确认公开状态": clean(confirmation.get("私有字段确认工作台状态")),
            "双人复核公开状态": clean(confirmation.get("双人复核公开状态")),
            "G0字段闭环命中状态": "G0-W0W1字段事实命中" if task_gap_rows else "非G0-W0W1字段事实子集",
            "G0字段事实数": str(len(set(g0_fact_ids))),
            "G0缺口任务数": str(len(task_gap_rows)),
            "G0当前可并行通道数": str(count_value(task_gap_rows, "是否当前可并行执行", "true")),
            "G0前置阻断通道数": str(count_value(task_gap_rows, "是否当前可并行执行", "false")),
            "G0待PDF原页记录数": str(count_unique_when(task_gap_rows, "第一闭环事实范围缺口公开账本ID", "PDF原页记录缺口")),
            "G0待湖北官方记录数": str(count_unique_when(task_gap_rows, "第一闭环事实范围缺口公开账本ID", "湖北官方记录缺口")),
            "G0待高校辅证核验数": str(count_unique_when(task_gap_rows, "第一闭环事实范围缺口公开账本ID", "高校辅证记录缺口")),
            "G0待冲突处理数": str(count_unique_when(task_gap_rows, "第一闭环事实范围缺口公开账本ID", "冲突处理缺口")),
            "G0待双人复核数": str(count_unique_when(task_gap_rows, "第一闭环事实范围缺口公开账本ID", "双人复核缺口")),
            "G0待三方一致性数": str(count_unique_when(task_gap_rows, "第一闭环事实范围缺口公开账本ID", "三方一致性缺口")),
            "G0待字段确认数": str(count_unique_when(task_gap_rows, "第一闭环事实范围缺口公开账本ID", "字段确认缺口")),
            "G0待写回评审数": str(count_unique_when(task_gap_rows, "第一闭环事实范围缺口公开账本ID", "写回评审缺口")),
            "G0候选分层分布": counter_text(bucket_counts),
            "G0候选主桶": main_bucket,
            "G0高校源回接事实数": str(len(task_backlink_rows)),
            "G0结构化接入候选字段数": str(count_value(task_backlink_rows, "高校源桥接桶", "B1-已有结构化接入候选，可作为高校侧double check提示")),
            "G0高校源可DoubleCheck字段数": str(count_value(task_backlink_rows, "高校源可作double_check提示", "true")),
            "G0计划数一致提示字段数": str(sum_field(task_backlink_rows, "C4C6计划数一致候选数合计")),
            "G0计划数冲突提示字段数": str(sum_field(task_backlink_rows, "C4C6计划数冲突候选数合计")),
            "证据准出阶段": stage,
            "证据准出阻断原因": blocker_for_stage(stage, task_gap_rows),
            "下一步最小核验动作": next_action(stage),
            "任务内G0事实集合SHA256": sha256_values(g0_fact_ids),
            "任务内G0缺口任务集合SHA256": sha256_values(row.get("G0冲突字段补证缺口任务公开账本ID") for row in task_gap_rows),
            "任务内G0回接集合SHA256": sha256_values(row.get("高校源字段回接队列ID") for row in task_backlink_rows),
            "公开安全策略": "只公开状态、分桶、计数、ID和SHA；不公开敏感明细、学校专业文本或最终志愿建议。",
        }
        add_false_fields(out)
        board_rows.append(out)

    page_rows: list[dict[str, str]] = []
    verification_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    board_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in verification_rows:
        verification_by_page[clean(row.get("页码版面键"))].append(row)
    for row in board_rows:
        board_by_page[clean(row.get("页码版面键"))].append(row)

    page_keys = sorted(
        verification_by_page,
        key=lambda key: (
            as_int((verification_by_page[key][0] if verification_by_page[key] else {}).get("来源页码")),
            clean((verification_by_page[key][0] if verification_by_page[key] else {}).get("版面列")),
        ),
    )
    for index, page_key in enumerate(page_keys, start=1):
        board_items = board_by_page[page_key]
        source_items = verification_by_page[page_key]
        page_gap_rows = gap_by_page.get(page_key, [])
        page_private_rows = private_by_page.get(page_key, [])
        page_candidate = candidate_page_by_page.get(page_key, {})
        bucket_counts = Counter(candidate_bucket(item) for item in page_private_rows)
        g0_task_ids = {clean(row.get("稳定基座第一闭环明细任务ID")) for row in page_gap_rows if clean(row.get("稳定基座第一闭环明细任务ID"))}
        source = source_items[0] if source_items else {}
        page_out = {
            "第一闭环证据仲裁页列汇总ID": stable_id("FIRST-ADJ-PAGE", [page_key, str(index)]),
            "来源第一闭环证据仲裁表": source_path(OUTPUT),
            "来源第一闭环核验结果页列汇总": source_path(VERIFICATION_PAGE),
            "来源G0字段W0W1候选分层页列汇总": source_path(W0_W1_CANDIDATE_PAGE),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "37页列叠加G0 W0/W1字段事实准出状态",
            "页列汇总序号": str(index),
            "页码版面键": page_key,
            "来源页码": clean(source.get("来源页码")),
            "版面列": clean(source.get("版面列")),
            "第一闭环任务数": str(len(board_items)),
            "G0命中任务数": str(len(g0_task_ids)),
            "G0字段事实数": str(len({clean(row.get("第一闭环事实范围缺口公开账本ID")) for row in page_gap_rows if clean(row.get("第一闭环事实范围缺口公开账本ID"))})),
            "G0缺口任务数": str(len(page_gap_rows)),
            "G0当前可并行通道数": str(count_value(page_gap_rows, "是否当前可并行执行", "true")),
            "G0前置阻断通道数": str(count_value(page_gap_rows, "是否当前可并行执行", "false")),
            "G0待PDF原页记录数": str(count_unique_when(page_gap_rows, "第一闭环事实范围缺口公开账本ID", "PDF原页记录缺口")),
            "G0待湖北官方记录数": str(count_unique_when(page_gap_rows, "第一闭环事实范围缺口公开账本ID", "湖北官方记录缺口")),
            "G0待高校辅证核验数": str(count_unique_when(page_gap_rows, "第一闭环事实范围缺口公开账本ID", "高校辅证记录缺口")),
            "G0待冲突处理数": str(count_unique_when(page_gap_rows, "第一闭环事实范围缺口公开账本ID", "冲突处理缺口")),
            "G0待双人复核数": str(count_unique_when(page_gap_rows, "第一闭环事实范围缺口公开账本ID", "双人复核缺口")),
            "G0待三方一致性数": str(count_unique_when(page_gap_rows, "第一闭环事实范围缺口公开账本ID", "三方一致性缺口")),
            "G0待字段确认数": str(count_unique_when(page_gap_rows, "第一闭环事实范围缺口公开账本ID", "字段确认缺口")),
            "G0待写回评审数": str(count_unique_when(page_gap_rows, "第一闭环事实范围缺口公开账本ID", "写回评审缺口")),
            "任务结果桶分布": dist(board_items, "任务结果桶"),
            "PDF原页状态分布": dist(board_items, "PDF原页证据状态"),
            "OCR提示状态分布": dist(board_items, "OCR提示状态"),
            "高校官网辅证状态分布": dist(board_items, "高校官网辅证状态"),
            "冲突状态分布": dist(board_items, "冲突状态"),
            "证据准出阶段分布": dist(board_items, "证据准出阶段"),
            "G0候选分层分布": counter_text(bucket_counts) or clean(page_candidate.get("候选分层分布")),
            "页列最小核验动作": "优先处理G0 W0/W1冲突字段。" if page_gap_rows else "按第一闭环总看板继续核页。",
            "页列任务集合SHA256": sha256_values(row.get("稳定基座第一闭环明细任务ID") for row in board_items),
            "页列G0事实集合SHA256": sha256_values(row.get("第一闭环事实范围缺口公开账本ID") for row in page_gap_rows),
            "页列G0缺口任务集合SHA256": sha256_values(row.get("G0冲突字段补证缺口任务公开账本ID") for row in page_gap_rows),
            "公开安全策略": "页列汇总只公开状态分布、数量和SHA；不公开敏感明细或学校专业文本。",
        }
        add_false_fields(page_out)
        page_rows.append(page_out)

    summary = {
        "status": "issue19_first_closure_evidence_adjudication_board_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_verification_result": source_path(VERIFICATION_RESULT),
        "source_verification_result_sha256": sha256_file(VERIFICATION_RESULT),
        "source_verification_page": source_path(VERIFICATION_PAGE),
        "source_verification_page_sha256": sha256_file(VERIFICATION_PAGE),
        "source_field_confirmation": source_path(FIELD_CONFIRMATION),
        "source_field_confirmation_sha256": sha256_file(FIELD_CONFIRMATION),
        "source_g0_gap_tasks": source_path(G0_GAP_TASKS),
        "source_g0_gap_tasks_sha256": sha256_file(G0_GAP_TASKS),
        "source_w0_w1_candidate": source_path(W0_W1_CANDIDATE),
        "source_w0_w1_candidate_sha256": sha256_file(W0_W1_CANDIDATE),
        "source_w0_w1_candidate_page": source_path(W0_W1_CANDIDATE_PAGE),
        "source_w0_w1_candidate_page_sha256": sha256_file(W0_W1_CANDIDATE_PAGE),
        "source_field_backlink": source_path(FIELD_BACKLINK),
        "source_field_backlink_sha256": sha256_file(FIELD_BACKLINK),
        "source_private_overlay_sha256": sha256_file(PRIVATE_OVERLAY),
        "output": source_path(OUTPUT),
        "page_output": source_path(PAGE_OUTPUT),
        "row_count": len(board_rows),
        "page_summary_row_count": len(page_rows),
        "source_verification_row_count": len(verification_rows),
        "source_verification_page_row_count": len(verification_page_rows),
        "source_field_confirmation_row_count": len(confirmation_rows),
        "source_g0_gap_task_row_count": len(gap_rows),
        "source_w0_w1_candidate_row_count": len(candidate_rows),
        "source_field_backlink_row_count": len(backlink_rows),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID") for row in board_rows}),
        "unique_page_side_count": len({row.get("页码版面键") for row in board_rows}),
        "g0_hit_task_count": count_value(board_rows, "G0字段闭环命中状态", "G0-W0W1字段事实命中"),
        "g0_fact_count": sum(as_int(row.get("G0字段事实数")) for row in board_rows),
        "g0_gap_task_count": sum(as_int(row.get("G0缺口任务数")) for row in board_rows),
        "g0_parallel_channel_count": sum(as_int(row.get("G0当前可并行通道数")) for row in board_rows),
        "g0_blocked_channel_count": sum(as_int(row.get("G0前置阻断通道数")) for row in board_rows),
        "g0_pdf_pending_count": sum(as_int(row.get("G0待PDF原页记录数")) for row in board_rows),
        "g0_hubei_official_pending_count": sum(as_int(row.get("G0待湖北官方记录数")) for row in board_rows),
        "g0_school_support_pending_count": sum(as_int(row.get("G0待高校辅证核验数")) for row in board_rows),
        "g0_conflict_resolution_pending_count": sum(as_int(row.get("G0待冲突处理数")) for row in board_rows),
        "g0_double_review_pending_count": sum(as_int(row.get("G0待双人复核数")) for row in board_rows),
        "g0_three_way_pending_count": sum(as_int(row.get("G0待三方一致性数")) for row in board_rows),
        "g0_field_confirmation_pending_count": sum(as_int(row.get("G0待字段确认数")) for row in board_rows),
        "g0_writeback_review_pending_count": sum(as_int(row.get("G0待写回评审数")) for row in board_rows),
        "task_result_bucket_counts": dict(Counter(row.get("任务结果桶", "") for row in board_rows)),
        "evidence_stage_counts": dict(Counter(row.get("证据准出阶段", "") for row in board_rows)),
        "g0_candidate_bucket_counts": dict(Counter(candidate_bucket(row) for row in private_rows)),
        "g0_candidate_main_bucket_counts": dict(Counter(row.get("G0候选主桶", "") for row in board_rows)),
        "field_confirmation_status_counts": dict(Counter(row.get("字段确认公开状态", "") for row in board_rows)),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表是206条第一闭环高风险明细的证据仲裁总视图，并叠加G0 W0/W1字段事实子状态；只给出下一步核验路径，不确认字段事实，不进入志愿建议。",
    }

    write_csv(OUTPUT, board_rows, BOARD_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    public_safety_check([OUTPUT, PAGE_OUTPUT, SUMMARY_OUTPUT])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
