#!/usr/bin/env python3
"""Build public-safe W0/W1 actionable evidence-channel items for G0 fields."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FIELD_PROGRESS = WORKING / "issue19-first-closure-g0-field-closure-progress-v1-public-ledger.csv"
GAP_TASKS = WORKING / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-public-ledger.csv"
REVIEW_LAUNCH = WORKING / "issue19-first-closure-g0-conflict-field-w0-w1-review-launch-v1-public-ledger.csv"
ACTIVE_WORKBOARD = WORKING / "issue19-first-closure-g0-conflict-field-w0-w1-active-workboard-v1-public-ledger.csv"
EVIDENCE_ADJUDICATION = WORKING / "issue19-first-closure-evidence-adjudication-board-v1-public-ledger.csv"

OUTPUT = WORKING / "issue19-first-closure-g0-field-w0-w1-action-items-v1-public-ledger.csv"
PAGE_CHANNEL_OUTPUT = WORKING / "issue19-first-closure-g0-field-w0-w1-action-items-v1-page-channel-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-g0-field-w0-w1-action-items-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_field_w0_w1_action_items_v1"

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

ITEM_FIELDS = [
    "G0字段W0W1可执行通道项ID",
    "来源G0字段闭环进度表",
    "来源G0字段补证缺口任务",
    "来源G0字段W0W1开核执行清单",
    "来源G0字段W0W1主动工作板",
    "来源第一闭环证据仲裁总视图",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行项序号",
    "证据通道序号",
    "证据通道",
    "证据通道类型",
    "证据通道执行层级",
    "当前执行波次",
    "当前证据动作组",
    "通道执行优先级",
    "G0冲突字段补证缺口任务公开账本ID",
    "G0字段闭环进度ID",
    "G0冲突字段W0W1开核执行清单ID",
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
    "候选分层桶",
    "闭环准出阶段",
    "证据缺口任务状态",
    "是否当前可并行执行",
    "当前通道状态",
    "当前阻断桶",
    "PDF原页记录状态",
    "湖北官方记录状态",
    "高校辅证人工核验状态",
    "冲突处理状态",
    "双人复核状态",
    "三方一致性闭环状态",
    "字段确认状态",
    "写回评审状态",
    "必要证据缺口数",
    "字段剩余缺口通道数",
    "高校源可DoubleCheck提示",
    "结构化接入候选数",
    "通道回填状态",
    "解除阻断条件",
    "下一步执行动作",
    "来源缺口任务记录SHA256",
    "来源字段进度记录SHA256",
    "来源开核执行包SHA256",
    "公开安全策略",
]

PAGE_CHANNEL_FIELDS = [
    "G0字段W0W1页列通道汇总ID",
    "来源G0字段W0W1可执行通道项",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "页列通道汇总序号",
    "页码版面键",
    "来源页码",
    "版面列",
    "证据通道序号",
    "证据通道",
    "当前执行波次",
    "当前证据动作组",
    "执行项数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "候选分层桶分布",
    "闭环准出阶段分布",
    "当前通道状态分布",
    "当前阻断桶分布",
    "通道回填状态分布",
    "需要双人复核字段数",
    "高校源可DoubleCheck字段数",
    "结构化接入候选字段数",
    "页列通道解除阻断条件",
    "页列通道下一步动作",
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
    digest = hashlib.sha256("|".join(clean(part) for part in parts).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


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


def wave_for_channel(channel: str) -> str:
    if channel == "双人复核":
        return "W1-双人复核"
    return "W0-一手证据与辅证采集"


def action_group(channel: str) -> str:
    return {
        "PDF原页记录": "A0-补PDF原页记录",
        "湖北官方侧记录": "A1-补湖北官方侧记录",
        "高校辅证人工核验": "A2-核高校辅证线索",
        "双人复核": "A3-冲突字段双人复核",
    }.get(channel, "A9-非W0W1通道")


def channel_rank(channel: str) -> str:
    return {
        "PDF原页记录": "01-PDF原页优先",
        "湖北官方侧记录": "02-湖北官方侧优先",
        "高校辅证人工核验": "03-高校辅证并行",
        "双人复核": "04-双人复核",
    }.get(channel, "99-非本轮通道")


def unblock_condition(channel: str) -> str:
    return {
        "PDF原页记录": "补齐PDF原页记录并保留证据编号和SHA。",
        "湖北官方侧记录": "补齐湖北官方系统或省招办计划记录并保留证据编号。",
        "高校辅证人工核验": "核高校辅证线索，仅作为double check，不替代湖北官方计划。",
        "双人复核": "完成双人复核记录，冲突字段才能进入三方闭环。",
    }.get(channel, "等待前置证据闭环。")


def next_action(channel: str) -> str:
    return {
        "PDF原页记录": "打开对应页列私有核页材料，逐字段补PDF原页记录。",
        "湖北官方侧记录": "按字段事实回查湖北官方侧记录，保留证据编号。",
        "高校辅证人工核验": "回接高校源线索并标注是否支持或冲突。",
        "双人复核": "对冲突字段做第二人复核，复核后再三方闭环。",
    }.get(channel, "等待前置闭环后再处理。")


def public_safety_check(paths: list[Path]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token and token in text]
    if hits:
        raise SystemExit(f"Public output contains forbidden tokens: {hits[:20]}")


def main() -> None:
    progress_rows = read_csv(FIELD_PROGRESS)
    gap_rows = read_csv(GAP_TASKS)
    launch_rows = read_csv(REVIEW_LAUNCH)
    active_rows = read_csv(ACTIVE_WORKBOARD)
    adjudication_rows = read_csv(EVIDENCE_ADJUDICATION)

    progress_by_fact = {
        clean(row.get("第一闭环事实范围缺口公开账本ID")): row for row in progress_rows
    }
    launch_by_page_channel: dict[tuple[str, str], dict[str, str]] = {}
    for row in launch_rows:
        launch_by_page_channel[
            (clean(row.get("页码版面键")), clean(row.get("证据通道序号")))
        ] = row

    active_keys = {
        (clean(row.get("页码版面键")), clean(row.get("证据通道序号"))) for row in active_rows
    }
    adjudication_task_ids = {
        clean(row.get("稳定基座第一闭环明细任务ID")) for row in adjudication_rows
    }

    active_gap_rows = [
        row
        for row in gap_rows
        if clean(row.get("是否当前可并行执行")) == "true"
        and clean(row.get("第一闭环事实范围缺口公开账本ID")) in progress_by_fact
    ]
    active_gap_rows.sort(
        key=lambda row: (
            as_int(row.get("来源页码")),
            clean(row.get("版面列")),
            as_int(row.get("证据通道序号")),
            clean(row.get("稳定基座第一闭环明细任务ID")),
            clean(row.get("字段名")),
        )
    )

    item_rows: list[dict[str, str]] = []
    for index, gap in enumerate(active_gap_rows, start=1):
        fact_id = clean(gap.get("第一闭环事实范围缺口公开账本ID"))
        page_key = clean(gap.get("页码版面键"))
        channel_no = clean(gap.get("证据通道序号"))
        channel = clean(gap.get("证据通道"))
        progress = progress_by_fact[fact_id]
        launch = launch_by_page_channel.get((page_key, channel_no), {})
        out = {
            "G0字段W0W1可执行通道项ID": stable_id(
                "G0-W0W1-ACTION-ITEM",
                [fact_id, channel_no, gap.get("G0冲突字段补证缺口任务公开账本ID", "")],
            ),
            "来源G0字段闭环进度表": source_path(FIELD_PROGRESS),
            "来源G0字段补证缺口任务": source_path(GAP_TASKS),
            "来源G0字段W0W1开核执行清单": source_path(REVIEW_LAUNCH),
            "来源G0字段W0W1主动工作板": source_path(ACTIVE_WORKBOARD),
            "来源第一闭环证据仲裁总视图": source_path(EVIDENCE_ADJUDICATION),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0字段事实×W0W1证据通道",
            "任务粒度": "当前可并行执行证据通道项",
            "执行项序号": str(index),
            "证据通道序号": channel_no,
            "证据通道": channel,
            "证据通道类型": clean(gap.get("证据通道类型")),
            "证据通道执行层级": clean(gap.get("证据通道执行层级")),
            "当前执行波次": wave_for_channel(channel),
            "当前证据动作组": action_group(channel),
            "通道执行优先级": channel_rank(channel),
            "G0冲突字段补证缺口任务公开账本ID": clean(
                gap.get("G0冲突字段补证缺口任务公开账本ID")
            ),
            "G0字段闭环进度ID": clean(progress.get("G0字段闭环进度ID")),
            "G0冲突字段W0W1开核执行清单ID": clean(
                launch.get("G0冲突字段W0W1开核执行清单ID")
            ),
            "第一闭环事实范围缺口公开账本ID": fact_id,
            "第一闭环字段事实公开账本ID": clean(gap.get("第一闭环字段事实公开账本ID")),
            "第一闭环字段核验状态ID": clean(gap.get("第一闭环字段核验状态ID")),
            "稳定基座第一闭环明细任务ID": clean(gap.get("稳定基座第一闭环明细任务ID")),
            "页码版面键": page_key,
            "来源页码": clean(gap.get("来源页码")),
            "版面列": clean(gap.get("版面列")),
            "专业行ID": clean(gap.get("专业行ID")),
            "专业组出现ID": clean(gap.get("专业组出现ID")),
            "院校代码": clean(gap.get("院校代码")),
            "事实域": clean(gap.get("事实域")),
            "事实类型": clean(gap.get("事实类型")),
            "字段名": clean(gap.get("字段名")),
            "字段事实状态": clean(progress.get("字段事实状态")),
            "候选分层桶": clean(progress.get("候选分层桶")),
            "闭环准出阶段": clean(progress.get("闭环准出阶段")),
            "证据缺口任务状态": clean(gap.get("证据缺口任务状态")),
            "是否当前可并行执行": clean(gap.get("是否当前可并行执行")),
            "当前通道状态": clean(gap.get("当前通道状态")),
            "当前阻断桶": clean(gap.get("当前阻断桶")),
            "PDF原页记录状态": clean(progress.get("PDF原页记录状态")),
            "湖北官方记录状态": clean(progress.get("湖北官方记录状态")),
            "高校辅证人工核验状态": clean(progress.get("高校辅证人工核验状态")),
            "冲突处理状态": clean(progress.get("冲突处理状态")),
            "双人复核状态": clean(progress.get("双人复核状态")),
            "三方一致性闭环状态": clean(progress.get("三方一致性闭环状态")),
            "字段确认状态": clean(progress.get("字段确认状态")),
            "写回评审状态": clean(progress.get("写回评审状态")),
            "必要证据缺口数": clean(progress.get("必要证据缺口数")),
            "字段剩余缺口通道数": clean(progress.get("证据通道数")),
            "高校源可DoubleCheck提示": clean(progress.get("高校源可DoubleCheck提示")),
            "结构化接入候选数": clean(progress.get("结构化接入候选数")),
            "通道回填状态": "pending_private_evidence_record",
            "解除阻断条件": unblock_condition(channel),
            "下一步执行动作": next_action(channel),
            "来源缺口任务记录SHA256": sha256_values(
                [gap.get("G0冲突字段补证缺口任务公开账本ID", "")]
            ),
            "来源字段进度记录SHA256": sha256_values([progress.get("G0字段闭环进度ID", "")]),
            "来源开核执行包SHA256": sha256_values(
                [launch.get("G0冲突字段W0W1开核执行清单ID", "")]
            ),
            "公开安全策略": "只公开可执行通道、状态、ID和SHA；不公开敏感明细、字段记录或最终志愿建议。",
        }
        add_false_fields(out)
        item_rows.append(out)

    page_channel_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in item_rows:
        page_channel_groups[(row.get("页码版面键", ""), row.get("证据通道序号", ""))].append(row)

    page_channel_rows: list[dict[str, str]] = []
    for index, ((page_key, channel_no), items) in enumerate(
        sorted(
            page_channel_groups.items(),
            key=lambda item: (
                as_int(item[1][0].get("来源页码")),
                clean(item[1][0].get("版面列")),
                as_int(item[1][0].get("证据通道序号")),
            ),
        ),
        start=1,
    ):
        first = items[0]
        out = {
            "G0字段W0W1页列通道汇总ID": stable_id(
                "G0-W0W1-ACTION-PAGE-CHANNEL", [page_key, channel_no, str(index)]
            ),
            "来源G0字段W0W1可执行通道项": source_path(OUTPUT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列×证据通道",
            "任务粒度": "G0字段事实W0W1可执行证据通道汇总",
            "页列通道汇总序号": str(index),
            "页码版面键": page_key,
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "证据通道序号": channel_no,
            "证据通道": first.get("证据通道", ""),
            "当前执行波次": first.get("当前执行波次", ""),
            "当前证据动作组": first.get("当前证据动作组", ""),
            "执行项数": str(len(items)),
            "涉及字段事实数": str(len({row.get("第一闭环事实范围缺口公开账本ID") for row in items})),
            "涉及任务数": str(len({row.get("稳定基座第一闭环明细任务ID") for row in items})),
            "涉及专业行数": str(len({row.get("专业行ID") for row in items})),
            "涉及院校代码数": str(len({row.get("院校代码") for row in items})),
            "字段名分布": dist(items, "字段名"),
            "候选分层桶分布": dist(items, "候选分层桶"),
            "闭环准出阶段分布": dist(items, "闭环准出阶段"),
            "当前通道状态分布": dist(items, "当前通道状态"),
            "当前阻断桶分布": dist(items, "当前阻断桶"),
            "通道回填状态分布": dist(items, "通道回填状态"),
            "需要双人复核字段数": str(count_value(items, "双人复核状态", "pending_double_review")),
            "高校源可DoubleCheck字段数": str(count_value(items, "高校源可DoubleCheck提示", "true")),
            "结构化接入候选字段数": str(
                sum(1 for row in items if as_int(row.get("结构化接入候选数")) > 0)
            ),
            "页列通道解除阻断条件": first.get("解除阻断条件", ""),
            "页列通道下一步动作": first.get("下一步执行动作", ""),
            "字段事实集合SHA256": sha256_values(
                row.get("第一闭环事实范围缺口公开账本ID") for row in items
            ),
            "缺口任务集合SHA256": sha256_values(
                row.get("G0冲突字段补证缺口任务公开账本ID") for row in items
            ),
            "公开安全策略": "页列通道汇总只公开计数、分布、ID集合SHA和下一步动作；不公开敏感明细。",
        }
        add_false_fields(out)
        page_channel_rows.append(out)

    channel_counts = Counter(row.get("证据通道") for row in item_rows)
    wave_counts = Counter(row.get("当前执行波次") for row in item_rows)
    candidate_counts = Counter(row.get("候选分层桶") for row in item_rows)
    status_counts = Counter(row.get("当前通道状态") for row in item_rows)
    action_counts = Counter(row.get("当前证据动作组") for row in item_rows)

    summary = {
        "status": "issue19_first_closure_g0_field_w0_w1_action_items_v1_ready_not_final",
        "generated_by": "build_issue19_first_closure_g0_field_w0_w1_action_items_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_field_progress": source_path(FIELD_PROGRESS),
        "source_field_progress_sha256": sha256_file(FIELD_PROGRESS),
        "source_gap_tasks": source_path(GAP_TASKS),
        "source_gap_tasks_sha256": sha256_file(GAP_TASKS),
        "source_review_launch": source_path(REVIEW_LAUNCH),
        "source_review_launch_sha256": sha256_file(REVIEW_LAUNCH),
        "source_active_workboard": source_path(ACTIVE_WORKBOARD),
        "source_active_workboard_sha256": sha256_file(ACTIVE_WORKBOARD),
        "source_evidence_adjudication": source_path(EVIDENCE_ADJUDICATION),
        "source_evidence_adjudication_sha256": sha256_file(EVIDENCE_ADJUDICATION),
        "output": source_path(OUTPUT),
        "page_channel_output": source_path(PAGE_CHANNEL_OUTPUT),
        "row_count": len(item_rows),
        "page_channel_summary_row_count": len(page_channel_rows),
        "source_field_progress_row_count": len(progress_rows),
        "source_gap_task_row_count": len(gap_rows),
        "source_review_launch_row_count": len(launch_rows),
        "source_active_workboard_row_count": len(active_rows),
        "source_evidence_adjudication_row_count": len(adjudication_rows),
        "unique_fact_scope_count": len({row.get("第一闭环事实范围缺口公开账本ID") for row in item_rows}),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID") for row in item_rows}),
        "unique_page_side_count": len({row.get("页码版面键") for row in item_rows}),
        "active_page_channel_key_count": len(page_channel_groups),
        "active_key_matches_workboard": set(page_channel_groups) == active_keys,
        "all_tasks_in_adjudication": {
            row.get("稳定基座第一闭环明细任务ID") for row in item_rows
        }.issubset(adjudication_task_ids),
        "channel_counts": dict(channel_counts),
        "wave_counts": dict(wave_counts),
        "candidate_bucket_counts": dict(candidate_counts),
        "current_channel_status_counts": dict(status_counts),
        "action_group_counts": dict(action_counts),
        "pdf_action_item_count": channel_counts.get("PDF原页记录", 0),
        "hubei_official_action_item_count": channel_counts.get("湖北官方侧记录", 0),
        "school_support_action_item_count": channel_counts.get("高校辅证人工核验", 0),
        "double_review_action_item_count": channel_counts.get("双人复核", 0),
        "w0_action_item_count": wave_counts.get("W0-一手证据与辅证采集", 0),
        "w1_action_item_count": wave_counts.get("W1-双人复核", 0),
        "pending_private_record_count": count_value(
            item_rows, "通道回填状态", "pending_private_evidence_record"
        ),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只描述68个G0字段事实在W0/W1的251条当前可执行证据通道；用于补私有证据记录，不确认字段事实，不进入志愿建议。",
    }

    write_csv(OUTPUT, item_rows, ITEM_FIELDS)
    write_csv(PAGE_CHANNEL_OUTPUT, page_channel_rows, PAGE_CHANNEL_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    public_safety_check([OUTPUT, PAGE_CHANNEL_OUTPUT, SUMMARY_OUTPUT])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
