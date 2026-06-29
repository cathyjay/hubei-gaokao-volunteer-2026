#!/usr/bin/env python3
"""Build a public-safe launch list for G0 W0/W1 review work.

This layer turns the W0/W1 active workboard plus the material-readiness audit
into an operator-facing launch checklist. It publishes only IDs, counts,
status buckets, and hashes; it does not publish private paths, OCR text,
school/major detail, field readings, or any final fact decision.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

MATERIAL_LEDGER = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-material-readiness-v1-public-ledger.csv"
)
MATERIAL_PAGE = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-material-readiness-v1-page-summary.csv"
)
MATERIAL_SUMMARY = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-material-readiness-v1-summary.json"
)
ACTIVE_WORKBOARD = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-active-workboard-v1-public-ledger.csv"
)
GAP_TASKS = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-public-ledger.csv"
)
FIELD_STATUS = (
    WORKING
    / "issue19-first-closure-field-verification-status-public-ledger.csv"
)
EVIDENCE_STATUS = (
    WORKING
    / "issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv"
)
CLOSURE_RESULT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-closure-result-v1-public-ledger.csv"
)

OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-review-launch-v1-public-ledger.csv"
)
PAGE_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-review-launch-v1-page-summary.csv"
)
SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-review-launch-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_w0_w1_review_launch_v1"

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
    "G0冲突字段W0W1开核执行清单ID",
    "来源G0冲突字段W0W1材料就绪公开账本",
    "来源G0冲突字段W0W1材料就绪页列汇总",
    "来源G0冲突字段W0W1材料就绪摘要",
    "来源G0冲突字段W0W1主动工作包公开账本",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源第一闭环字段级公开状态",
    "来源第一闭环证据状态报告",
    "来源G0冲突字段补证闭环结果",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "开核序号",
    "材料就绪公开账本ID",
    "主动工作包ID",
    "执行波次序号",
    "执行波次",
    "证据通道序号",
    "证据通道",
    "开核动作组",
    "开核优先级",
    "页码版面键",
    "来源页码",
    "版面列",
    "缺口任务数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "私有材料就绪状态",
    "人工补证记录状态",
    "开核执行状态",
    "PDF原页证据状态分布",
    "OCR提示状态分布",
    "机器坐标提示状态分布",
    "高校辅证证据状态分布",
    "湖北官方侧状态分布",
    "冲突状态分布",
    "三方闭环状态分布",
    "字段写回状态分布",
    "PDF原页待核任务数",
    "湖北官方侧待核任务数",
    "高校辅证线索任务数",
    "需要双人复核任务数",
    "PDFOCR提示任务数",
    "机器坐标提示任务数",
    "PDFOCR与高校辅证冲突任务数",
    "私有页列CSV是否存在",
    "私有核页HTML是否存在",
    "人工记录已填合计",
    "字段确认记录已填数",
    "写回建议记录已填数",
    "开核准出条件",
    "下一步开核动作",
    "来源缺口任务集合SHA256",
    "来源字段状态集合SHA256",
    "来源证据状态集合SHA256",
    "来源闭环结果集合SHA256",
    "公开安全策略",
]

PAGE_FIELDS = [
    "G0冲突字段W0W1开核执行页列汇总ID",
    "来源G0冲突字段W0W1开核执行清单",
    "来源G0冲突字段W0W1材料就绪页列汇总",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源第一闭环字段级公开状态",
    "来源第一闭环证据状态报告",
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
    "开核工作包数",
    "材料就绪工作包数",
    "人工记录就绪工作包数",
    "人工记录阻断工作包数",
    "当前可并行任务数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "证据通道分布",
    "字段名分布",
    "PDF原页证据状态分布",
    "OCR提示状态分布",
    "高校辅证证据状态分布",
    "冲突状态分布",
    "私有材料页列状态",
    "页列开核执行状态",
    "页列下一步开核动作",
    "开核工作包集合SHA256",
    "来源缺口任务集合SHA256",
    "来源字段状态集合SHA256",
    "来源证据状态集合SHA256",
    "来源闭环结果集合SHA256",
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
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


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


def side_rank(value: str) -> int:
    return {"left": 0, "right": 1}.get(clean(value), 9)


def count_unique(rows: list[dict[str, str]], field: str) -> int:
    return len({clean(row.get(field, "")) for row in rows if clean(row.get(field, ""))})


def count_true(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if clean(row.get(field, "")).lower() == "true")


def sum_fields(row: dict[str, str], fields: list[str]) -> int:
    return sum(as_int(row.get(field, "")) for field in fields)


def dist(rows: list[dict[str, str]], field: str) -> str:
    counter = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter))


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
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter)) if counter else ""


def launch_action_group(channel_seq: str) -> str:
    return {
        "01": "A01-PDF原页人工核页",
        "02": "A02-湖北官方侧核验",
        "03": "A03-高校辅证人工核验",
        "05": "A05-双人核页复核",
    }.get(channel_seq, "A99-其他开核动作")


def launch_priority(channel_seq: str) -> str:
    return {
        "01": "P0-PDF原页先核",
        "05": "P0-双人复核先核",
        "02": "P1-湖北官方侧并行核",
        "03": "P2-高校辅证并行核",
    }.get(channel_seq, "P9-其他")


def launch_condition(channel_seq: str) -> str:
    return {
        "01": "材料齐备后填写PDF原页人工记录；不得直接写回字段事实。",
        "02": "材料齐备后核湖北官方系统或省招办计划记录；高校源不得替代湖北官方侧。",
        "03": "材料齐备后人工核高校辅证线索；只作double check。",
        "05": "材料齐备后完成A/B双人核页一致性记录；未完成前不得定案。",
    }.get(channel_seq, "按证据通道补齐人工记录；不得越权定案。")


def next_action(channel_seq: str, human_status: str) -> str:
    if human_status.startswith("ready_"):
        return "本通道人工记录已具备；仍需等待跨通道闭环后才能评估字段确认。"
    return {
        "01": "打开已就绪材料，优先补PDF原页人工核页记录。",
        "02": "打开已就绪材料，补湖北官方侧核验记录；官方侧不可用时继续保留阻断。",
        "03": "打开已就绪材料，补高校辅证人工核验记录；只作为double check线索。",
        "05": "打开已就绪材料，安排A/B双人核页并填写一致性记录。",
    }.get(channel_seq, "打开已就绪材料，按通道补齐人工记录。")


def execution_status(material_status: str, human_status: str) -> str:
    if material_status != "ready_private_materials_present":
        return "blocked_missing_private_materials"
    if human_status.startswith("ready_"):
        return "human_records_present_waiting_cross_channel_closure"
    return "ready_to_launch_human_review_not_fact"


def public_safety_check(paths: list[Path]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    leaked = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if leaked:
        raise RuntimeError(f"public output contains forbidden tokens: {leaked[:20]}")


def build_rows(
    material_rows: list[dict[str, str]],
    active_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    field_status_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    closure_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    active_by_id = {
        row.get("G0冲突字段W0W1主动工作包公开账本ID", ""): row
        for row in active_rows
    }
    field_status_by_id = {
        row.get("第一闭环字段核验状态ID", ""): row
        for row in field_status_rows
    }
    evidence_by_task_id = {
        row.get("稳定基座第一闭环明细任务ID", ""): row
        for row in evidence_rows
    }
    closure_by_id = {
        row.get("G0冲突字段补证闭环结果公开账本ID", ""): row
        for row in closure_rows
    }
    gap_by_page_channel = defaultdict(list)
    for row in gap_rows:
        if row.get("是否当前可并行执行") == "true" and row.get("证据通道序号") in {"01", "02", "03", "05"}:
            gap_by_page_channel[(row.get("页码版面键", ""), row.get("证据通道序号", ""))].append(row)

    rows = []
    sorted_material = sorted(
        material_rows,
        key=lambda row: (
            as_int(row.get("来源页码", "")),
            side_rank(row.get("版面列", "")),
            row.get("证据通道序号", ""),
        ),
    )
    for seq, material in enumerate(sorted_material, start=1):
        active = active_by_id.get(material.get("主动工作包ID", ""), {})
        page_key = material.get("页码版面键", "")
        channel_seq = material.get("证据通道序号", "")
        tasks = gap_by_page_channel[(page_key, channel_seq)]
        field_statuses = [
            field_status_by_id.get(task.get("第一闭环字段核验状态ID", ""), {})
            for task in tasks
        ]
        field_statuses = [row for row in field_statuses if row]
        evidence_statuses = [
            evidence_by_task_id.get(task.get("稳定基座第一闭环明细任务ID", ""), {})
            for task in tasks
        ]
        evidence_statuses = [row for row in evidence_statuses if row]
        closure_statuses = [
            closure_by_id.get(task.get("G0冲突字段补证闭环结果公开账本ID", ""), {})
            for task in tasks
        ]
        closure_statuses = [row for row in closure_statuses if row]
        human_status = material.get("人工补证记录状态", "")
        material_status = material.get("私有材料就绪状态", "")
        out = {
            "G0冲突字段W0W1开核执行清单ID": stable_id(
                "G0W0W1LAUNCH", [SOURCE_PDF_SHA256, page_key, channel_seq]
            ),
            "来源G0冲突字段W0W1材料就绪公开账本": source_path(MATERIAL_LEDGER),
            "来源G0冲突字段W0W1材料就绪页列汇总": source_path(MATERIAL_PAGE),
            "来源G0冲突字段W0W1材料就绪摘要": source_path(MATERIAL_SUMMARY),
            "来源G0冲突字段W0W1主动工作包公开账本": source_path(ACTIVE_WORKBOARD),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源第一闭环字段级公开状态": source_path(FIELD_STATUS),
            "来源第一闭环证据状态报告": source_path(EVIDENCE_STATUS),
            "来源G0冲突字段补证闭环结果": source_path(CLOSURE_RESULT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段W0/W1开核执行清单",
            "任务粒度": "页列×证据通道",
            "开核序号": str(seq),
            "材料就绪公开账本ID": material.get("G0冲突字段W0W1材料就绪公开账本ID", ""),
            "主动工作包ID": material.get("主动工作包ID", ""),
            "执行波次序号": material.get("执行波次序号", ""),
            "执行波次": material.get("执行波次", ""),
            "证据通道序号": channel_seq,
            "证据通道": material.get("证据通道", ""),
            "开核动作组": launch_action_group(channel_seq),
            "开核优先级": launch_priority(channel_seq),
            "页码版面键": page_key,
            "来源页码": material.get("来源页码", ""),
            "版面列": material.get("版面列", ""),
            "缺口任务数": material.get("缺口任务数", ""),
            "涉及字段事实数": material.get("涉及字段事实数", ""),
            "涉及任务数": material.get("涉及任务数", ""),
            "涉及专业行数": material.get("涉及专业行数", ""),
            "涉及院校代码数": material.get("涉及院校代码数", ""),
            "字段名分布": material.get("字段名分布", ""),
            "私有材料就绪状态": material_status,
            "人工补证记录状态": human_status,
            "开核执行状态": execution_status(material_status, human_status),
            "PDF原页证据状态分布": dist(field_statuses, "PDF原页证据状态"),
            "OCR提示状态分布": dist(field_statuses, "OCR提示状态"),
            "机器坐标提示状态分布": dist(field_statuses, "机器坐标提示状态"),
            "高校辅证证据状态分布": dist(field_statuses, "高校辅证证据状态"),
            "湖北官方侧状态分布": dist(field_statuses, "湖北官方侧状态"),
            "冲突状态分布": dist(field_statuses, "冲突状态"),
            "三方闭环状态分布": dist(field_statuses, "三方闭环状态"),
            "字段写回状态分布": dist(field_statuses, "字段事实写回状态"),
            "PDF原页待核任务数": str(count_true(tasks, "PDF原页记录缺口")),
            "湖北官方侧待核任务数": str(count_true(tasks, "湖北官方记录缺口")),
            "高校辅证线索任务数": str(count_true(tasks, "是否有高校辅证线索")),
            "需要双人复核任务数": str(count_true(tasks, "是否需要双人复核")),
            "PDFOCR提示任务数": str(count_true(tasks, "是否有PDFOCR提示")),
            "机器坐标提示任务数": str(count_true(tasks, "是否有机器坐标提示")),
            "PDFOCR与高校辅证冲突任务数": str(count_true(tasks, "是否存在PDFOCR与高校冲突")),
            "私有页列CSV是否存在": material.get("私有页列CSV是否存在", ""),
            "私有核页HTML是否存在": material.get("私有核页HTML是否存在", ""),
            "人工记录已填合计": str(sum_fields(material, [
                "PDF原页字段人工记录已填数",
                "湖北官方字段记录已填数",
                "高校辅证人工核验记录已填数",
                "双人一致性记录已填数",
            ])),
            "字段确认记录已填数": material.get("字段确认记录已填数", "0"),
            "写回建议记录已填数": material.get("写回建议记录已填数", "0"),
            "开核准出条件": launch_condition(channel_seq),
            "下一步开核动作": next_action(channel_seq, human_status),
            "来源缺口任务集合SHA256": material.get("来源缺口任务集合SHA256", ""),
            "来源字段状态集合SHA256": sha256_values(
                row.get("第一闭环字段核验状态ID", "") for row in field_statuses
            ),
            "来源证据状态集合SHA256": sha256_values(
                row.get("第一闭环证据状态公开账本ID", "") for row in evidence_statuses
            ),
            "来源闭环结果集合SHA256": sha256_values(
                row.get("G0冲突字段补证闭环结果公开账本ID", "") for row in closure_statuses
            ),
            "公开安全策略": "公开层只保存开核动作、状态桶、计数、ID和SHA；不公开私有路径、识别内容、字段记录、人工内容或学校专业明细。",
        }
        add_false_fields(out)
        rows.append(out)
    return rows


def build_page_rows(rows: list[dict[str, str]], gap_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows_by_page = defaultdict(list)
    for row in rows:
        rows_by_page[row.get("页码版面键", "")].append(row)
    active_gap_by_page = defaultdict(list)
    for row in gap_rows:
        if row.get("是否当前可并行执行") == "true" and row.get("证据通道序号") in {"01", "02", "03", "05"}:
            active_gap_by_page[row.get("页码版面键", "")].append(row)

    page_rows = []
    for seq, page_key in enumerate(
        sorted(
            rows_by_page,
            key=lambda key: (
                as_int(rows_by_page[key][0].get("来源页码", "")),
                side_rank(rows_by_page[key][0].get("版面列", "")),
                key,
            ),
        ),
        start=1,
    ):
        packets = rows_by_page[page_key]
        gap_items = active_gap_by_page[page_key]
        first = packets[0]
        material_ready = sum(
            1 for row in packets
            if row.get("私有材料就绪状态") == "ready_private_materials_present"
        )
        human_ready = sum(
            1 for row in packets
            if row.get("人工补证记录状态", "").startswith("ready_")
        )
        out = {
            "G0冲突字段W0W1开核执行页列汇总ID": stable_id(
                "G0W0W1LAUNCHPAGE", [SOURCE_PDF_SHA256, page_key]
            ),
            "来源G0冲突字段W0W1开核执行清单": source_path(OUTPUT),
            "来源G0冲突字段W0W1材料就绪页列汇总": source_path(MATERIAL_PAGE),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源第一闭环字段级公开状态": source_path(FIELD_STATUS),
            "来源第一闭环证据状态报告": source_path(EVIDENCE_STATUS),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段W0/W1开核执行页列汇总",
            "任务粒度": "页列",
            "页列汇总序号": str(seq),
            "页码版面键": page_key,
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "开核工作包数": str(len(packets)),
            "材料就绪工作包数": str(material_ready),
            "人工记录就绪工作包数": str(human_ready),
            "人工记录阻断工作包数": str(len(packets) - human_ready),
            "当前可并行任务数": str(len(gap_items)),
            "涉及字段事实数": str(count_unique(gap_items, "G0冲突字段补证闭环结果公开账本ID")),
            "涉及任务数": str(count_unique(gap_items, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(gap_items, "专业行ID")),
            "涉及院校代码数": str(count_unique(gap_items, "院校代码")),
            "证据通道分布": dist(gap_items, "证据通道"),
            "字段名分布": dist(gap_items, "字段名"),
            "PDF原页证据状态分布": merge_dist_text([row.get("PDF原页证据状态分布", "") for row in packets]),
            "OCR提示状态分布": merge_dist_text([row.get("OCR提示状态分布", "") for row in packets]),
            "高校辅证证据状态分布": merge_dist_text([row.get("高校辅证证据状态分布", "") for row in packets]),
            "冲突状态分布": merge_dist_text([row.get("冲突状态分布", "") for row in packets]),
            "私有材料页列状态": (
                "ready_private_materials_present"
                if material_ready == len(packets) else "blocked_missing_private_materials"
            ),
            "页列开核执行状态": (
                "ready_to_launch_human_review_not_fact"
                if material_ready == len(packets) and human_ready == 0
                else "human_records_partially_or_fully_present_waiting_closure"
            ),
            "页列下一步开核动作": "按PDF原页、湖北官方侧、高校辅证和双人复核通道补齐人工记录；不得据此确认字段事实。",
            "开核工作包集合SHA256": sha256_values(
                row.get("G0冲突字段W0W1开核执行清单ID", "") for row in packets
            ),
            "来源缺口任务集合SHA256": sha256_values(
                row.get("G0冲突字段补证缺口任务公开账本ID", "") for row in gap_items
            ),
            "来源字段状态集合SHA256": sha256_values(
                row.get("来源字段状态集合SHA256", "") for row in packets
            ),
            "来源证据状态集合SHA256": sha256_values(
                row.get("来源证据状态集合SHA256", "") for row in packets
            ),
            "来源闭环结果集合SHA256": sha256_values(
                row.get("来源闭环结果集合SHA256", "") for row in packets
            ),
            "公开安全策略": "公开层只保存页列开核状态、计数、状态桶、ID和SHA；不公开私有路径、识别内容、字段记录、人工内容或学校专业明细。",
        }
        add_false_fields(out)
        page_rows.append(out)
    return page_rows


def main() -> None:
    material_rows = read_csv(MATERIAL_LEDGER)
    active_rows = read_csv(ACTIVE_WORKBOARD)
    gap_rows = read_csv(GAP_TASKS)
    field_status_rows = read_csv(FIELD_STATUS)
    evidence_rows = read_csv(EVIDENCE_STATUS)
    closure_rows = read_csv(CLOSURE_RESULT)

    ledger_rows = build_rows(
        material_rows,
        active_rows,
        gap_rows,
        field_status_rows,
        evidence_rows,
        closure_rows,
    )
    page_rows = build_page_rows(ledger_rows, gap_rows)

    write_csv(OUTPUT, ledger_rows, LEDGER_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)

    summary = {
        "status": "issue19_first_closure_g0_conflict_field_w0_w1_review_launch_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_material_ledger": source_path(MATERIAL_LEDGER),
        "source_material_ledger_sha256": sha256_file(MATERIAL_LEDGER),
        "source_material_page": source_path(MATERIAL_PAGE),
        "source_material_page_sha256": sha256_file(MATERIAL_PAGE),
        "source_material_summary": source_path(MATERIAL_SUMMARY),
        "source_material_summary_sha256": sha256_file(MATERIAL_SUMMARY),
        "source_active_workboard": source_path(ACTIVE_WORKBOARD),
        "source_active_workboard_sha256": sha256_file(ACTIVE_WORKBOARD),
        "source_gap_tasks": source_path(GAP_TASKS),
        "source_gap_tasks_sha256": sha256_file(GAP_TASKS),
        "source_field_status": source_path(FIELD_STATUS),
        "source_field_status_sha256": sha256_file(FIELD_STATUS),
        "source_evidence_status": source_path(EVIDENCE_STATUS),
        "source_evidence_status_sha256": sha256_file(EVIDENCE_STATUS),
        "source_closure_result": source_path(CLOSURE_RESULT),
        "source_closure_result_sha256": sha256_file(CLOSURE_RESULT),
        "output_table": source_path(OUTPUT),
        "page_summary_table": source_path(PAGE_OUTPUT),
        "ledger_row_count": len(ledger_rows),
        "page_summary_row_count": len(page_rows),
        "source_material_row_count": len(material_rows),
        "source_active_workboard_row_count": len(active_rows),
        "source_gap_task_row_count": len(gap_rows),
        "source_field_status_row_count": len(field_status_rows),
        "source_evidence_status_row_count": len(evidence_rows),
        "source_closure_result_row_count": len(closure_rows),
        "active_task_row_count": sum(as_int(row.get("缺口任务数")) for row in ledger_rows),
        "unique_page_side_count": count_unique(ledger_rows, "页码版面键"),
        "unique_launch_package_count": count_unique(ledger_rows, "G0冲突字段W0W1开核执行清单ID"),
        "launch_ready_package_count": sum(
            1 for row in ledger_rows
            if row.get("开核执行状态") == "ready_to_launch_human_review_not_fact"
        ),
        "material_ready_package_count": sum(
            1 for row in ledger_rows
            if row.get("私有材料就绪状态") == "ready_private_materials_present"
        ),
        "human_ready_package_count": sum(
            1 for row in ledger_rows
            if row.get("人工补证记录状态", "").startswith("ready_")
        ),
        "human_blocked_package_count": sum(
            1 for row in ledger_rows
            if not row.get("人工补证记录状态", "").startswith("ready_")
        ),
        "package_count_by_channel": dict(Counter(row.get("证据通道序号", "") for row in ledger_rows)),
        "package_count_by_action_group": dict(Counter(row.get("开核动作组", "") for row in ledger_rows)),
        "package_count_by_launch_priority": dict(Counter(row.get("开核优先级", "") for row in ledger_rows)),
        "page_ready_count": sum(
            1 for row in page_rows
            if row.get("页列开核执行状态") == "ready_to_launch_human_review_not_fact"
        ),
        "pdf_original_pending_task_count": sum(as_int(row.get("PDF原页待核任务数")) for row in ledger_rows),
        "hubei_official_pending_task_count": sum(as_int(row.get("湖北官方侧待核任务数")) for row in ledger_rows),
        "school_support_hint_task_count": sum(as_int(row.get("高校辅证线索任务数")) for row in ledger_rows),
        "double_review_required_task_count": sum(as_int(row.get("需要双人复核任务数")) for row in ledger_rows),
        "pdf_ocr_hint_task_count": sum(as_int(row.get("PDFOCR提示任务数")) for row in ledger_rows),
        "machine_coordinate_hint_task_count": sum(as_int(row.get("机器坐标提示任务数")) for row in ledger_rows),
        "pdf_school_conflict_task_count": sum(as_int(row.get("PDFOCR与高校辅证冲突任务数")) for row in ledger_rows),
        "human_record_filled_total_count": sum(as_int(row.get("人工记录已填合计")) for row in ledger_rows),
        "field_confirmation_record_filled_count": sum(as_int(row.get("字段确认记录已填数")) for row in ledger_rows),
        "writeback_suggestion_record_filled_count": sum(as_int(row.get("写回建议记录已填数")) for row in ledger_rows),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只把W0/W1材料就绪包转成开核执行入口，不确认字段事实，不写回，不进入推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    public_safety_check([OUTPUT, PAGE_OUTPUT, SUMMARY_OUTPUT])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
