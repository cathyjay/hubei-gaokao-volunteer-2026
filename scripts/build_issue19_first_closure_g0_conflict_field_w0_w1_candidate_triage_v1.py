#!/usr/bin/env python3
"""Build a public-safe candidate triage layer for G0 W0/W1 review launch.

This layer reads the private G0 conflict-field overlay only to classify whether
PDF OCR and school-support clues are present or divergent. Public outputs keep
only IDs, counts, buckets, and SHA values; they never publish private paths,
OCR text, school/major details, field readings, clue values, or final facts.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"
PRIVATE_ROOT = ROOT / "private"

LAUNCH_LEDGER = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-review-launch-v1-public-ledger.csv"
)
LAUNCH_PAGE = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-review-launch-v1-page-summary.csv"
)
LAUNCH_SUMMARY = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-review-launch-v1-summary.json"
)
GAP_TASKS = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-public-ledger.csv"
)
PRIVATE_OVERLAY = (
    PRIVATE_ROOT
    / "review-assets/issue19-g0-conflict-field-review-overlay-v1/g0-conflict-field-review-private-overlay.csv"
)

OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-candidate-triage-v1-public-ledger.csv"
)
PAGE_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-candidate-triage-v1-page-summary.csv"
)
SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-candidate-triage-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_w0_w1_candidate_triage_v1"

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
    "G0冲突字段W0W1候选分层ID",
    "来源G0冲突字段W0W1开核执行清单",
    "来源G0冲突字段W0W1开核执行页列汇总",
    "来源G0冲突字段W0W1开核执行摘要",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源私有G0字段复核Overlay",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "候选分层序号",
    "开核执行清单ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "证据通道序号",
    "证据通道",
    "开核动作组",
    "开核优先级",
    "缺口任务数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "私有Overlay候选字段数",
    "PDFOCR有候选字段数",
    "高校辅证有候选字段数",
    "双侧候选字段数",
    "候选一致字段数",
    "候选冲突字段数",
    "仅PDFOCR候选字段数",
    "仅高校辅证候选字段数",
    "候选缺失字段数",
    "高校官网或招生章程线索已填字段数",
    "PDF原页人工记录已填字段数",
    "湖北官方记录已填字段数",
    "高校辅证人工核验已填字段数",
    "字段确认已填字段数",
    "候选分层分布",
    "候选分层主桶",
    "PDFOCR与高校辅证关系桶分布",
    "开核候选提示状态",
    "下一步候选核验动作",
    "来源缺口任务集合SHA256",
    "来源私有Overlay记录集合SHA256",
    "来源私有Overlay文件SHA256",
    "公开安全策略",
]

PAGE_FIELDS = [
    "G0冲突字段W0W1候选分层页列汇总ID",
    "来源G0冲突字段W0W1候选分层清单",
    "来源G0冲突字段W0W1开核执行页列汇总",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源私有G0字段复核Overlay",
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
    "开核分层工作包数",
    "当前可并行任务数",
    "唯一候选字段数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "证据通道分布",
    "候选分层分布",
    "候选分层主桶",
    "候选一致唯一字段数",
    "候选冲突唯一字段数",
    "单侧候选唯一字段数",
    "候选缺失唯一字段数",
    "人工记录已填合计",
    "页列候选核验状态",
    "页列下一步候选核验动作",
    "候选分层工作包集合SHA256",
    "来源缺口任务集合SHA256",
    "来源私有Overlay记录集合SHA256",
    "来源私有Overlay文件SHA256",
    "公开安全策略",
]

PRIVATE_FIELDS = [
    "G0私有字段复核记录ID",
    "G0冲突字段复核Overlay公开账本ID",
    "G0冲突动作包闭环工作台ID",
    "高校源字段回接队列ID",
    "W0B0执行预填明细公开审计ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "事实类型",
    "字段名",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称",
    "院校专业组代码",
    "专业代号",
    "专业名称短摘",
    "稳定基座第一闭环明细任务ID",
    "第一闭环事实范围缺口公开账本ID",
    "第一闭环字段事实公开账本ID",
    "PDFOCR提示状态",
    "PDFOCR与高校辅证关系桶",
    "PDFOCR计划数候选值",
    "PDFOCR学费候选值",
    "PDFOCR选科候选值",
    "机器坐标候选字段值",
    "机器坐标候选值集合",
    "高校辅证计划数候选值",
    "高校辅证学费候选值",
    "高校辅证选科候选值",
    "OCR行文本",
    "私有页图相对路径",
    "私有OCR文本相对路径",
    "PDF原页专业代号读数",
    "PDF原页专业名称读数",
    "PDF原页字段人工读数",
    "湖北官方专业代号",
    "湖北官方专业名称",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "高校辅证人工核验记录值",
    "字段确认值",
    "PDF核页复核人A",
    "PDF核页复核人B",
    "湖北官方核验人",
    "高校辅证核验人",
    "双人一致性结论",
    "三方一致性结论",
    "字段事实写回建议",
    "人工复核备注",
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

FIELD_CANDIDATE_COLUMNS = {
    "专业计划数": ("PDFOCR计划数候选值", "高校辅证计划数候选值"),
    "学费": ("PDFOCR学费候选值", "高校辅证学费候选值"),
    "再选科目": ("PDFOCR选科候选值", "高校辅证选科候选值"),
}


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def norm(value: object) -> str:
    return "".join(clean(value).split())


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


def count_filled(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if clean(row.get(field, "")))


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


def candidate_pair(row: dict[str, str]) -> tuple[str, str]:
    ocr_col, school_col = FIELD_CANDIDATE_COLUMNS.get(clean(row.get("字段名", "")), ("", ""))
    return clean(row.get(ocr_col, "")), clean(row.get(school_col, ""))


def candidate_bucket(row: dict[str, str]) -> str:
    ocr_value, school_value = candidate_pair(row)
    has_ocr = bool(ocr_value)
    has_school = bool(school_value) or bool(clean(row.get("高校官网或招生章程字段值", "")))
    if has_ocr and has_school and norm(ocr_value) == norm(school_value):
        return "C1-双侧候选一致但仍待核"
    if has_ocr and has_school:
        return "C0-双侧候选冲突优先核"
    if has_ocr:
        return "C2-仅PDFOCR候选需补辅证"
    if has_school:
        return "C3-仅高校辅证候选需核原页"
    return "C4-无候选需人工看图"


def candidate_main_bucket(rows: list[dict[str, str]]) -> str:
    buckets = Counter(candidate_bucket(row) for row in rows)
    if buckets.get("C0-双侧候选冲突优先核"):
        return "T0-候选冲突优先核PDF原页与湖北官方"
    if buckets.get("C4-无候选需人工看图"):
        return "T1-候选缺失需人工看图"
    if buckets.get("C2-仅PDFOCR候选需补辅证") or buckets.get("C3-仅高校辅证候选需核原页"):
        return "T2-单侧候选需补另一侧"
    if buckets.get("C1-双侧候选一致但仍待核"):
        return "T3-候选一致但仍待PDF和湖北官方"
    return "T9-无私有候选记录"


def next_action(channel_seq: str, main_bucket: str) -> str:
    if channel_seq == "01":
        if main_bucket.startswith("T0"):
            return "优先核PDF原页，判定双侧线索差异来源；不得直接确认字段事实。"
        return "核PDF原页并补人工记录；仍需湖北官方侧闭环后才能字段确认。"
    if channel_seq == "02":
        return "核湖北官方系统或省招办计划记录；官方侧不可用时继续保留阻断。"
    if channel_seq == "03":
        return "核高校辅证线索作为double check；不得替代湖北官方计划。"
    if channel_seq == "05":
        return "安排A/B双人复核冲突字段并记录一致性；未完成前不得定案。"
    return "按通道补齐人工核验记录；不得越权定案。"


def status_for_bucket(main_bucket: str) -> str:
    return {
        "T0-候选冲突优先核PDF原页与湖北官方": "candidate_conflict_ready_for_human_review_not_fact",
        "T1-候选缺失需人工看图": "candidate_missing_ready_for_image_review_not_fact",
        "T2-单侧候选需补另一侧": "single_sided_candidate_ready_for_crosscheck_not_fact",
        "T3-候选一致但仍待PDF和湖北官方": "candidate_consensus_waiting_required_sources_not_fact",
    }.get(main_bucket, "candidate_triage_pending_not_fact")


def public_safety_check(paths: list[Path]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    leaked = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if leaked:
        raise RuntimeError(f"public output contains forbidden tokens: {leaked[:20]}")


def build_rows(
    launch_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    private_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    private_by_fact = {
        row.get("第一闭环事实范围缺口公开账本ID", ""): row
        for row in private_rows
    }
    tasks_by_page_channel = defaultdict(list)
    for row in gap_rows:
        if row.get("是否当前可并行执行") == "true" and row.get("证据通道序号") in {"01", "02", "03", "05"}:
            tasks_by_page_channel[(row.get("页码版面键", ""), row.get("证据通道序号", ""))].append(row)

    sorted_launch = sorted(
        launch_rows,
        key=lambda row: (
            as_int(row.get("来源页码", "")),
            side_rank(row.get("版面列", "")),
            row.get("证据通道序号", ""),
        ),
    )
    rows = []
    private_overlay_sha = sha256_file(PRIVATE_OVERLAY)
    for seq, launch in enumerate(sorted_launch, start=1):
        page_key = launch.get("页码版面键", "")
        channel_seq = launch.get("证据通道序号", "")
        tasks = tasks_by_page_channel[(page_key, channel_seq)]
        private_items = [
            private_by_fact.get(task.get("第一闭环事实范围缺口公开账本ID", ""), {})
            for task in tasks
        ]
        private_items = [item for item in private_items if item]
        buckets = Counter(candidate_bucket(item) for item in private_items)
        main_bucket = candidate_main_bucket(private_items)
        out = {
            "G0冲突字段W0W1候选分层ID": stable_id(
                "G0W0W1CANDTRIAGE", [SOURCE_PDF_SHA256, page_key, channel_seq]
            ),
            "来源G0冲突字段W0W1开核执行清单": source_path(LAUNCH_LEDGER),
            "来源G0冲突字段W0W1开核执行页列汇总": source_path(LAUNCH_PAGE),
            "来源G0冲突字段W0W1开核执行摘要": source_path(LAUNCH_SUMMARY),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源私有G0字段复核Overlay": "g0_conflict_field_review_private_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段W0/W1候选分层",
            "任务粒度": "页列×证据通道",
            "候选分层序号": str(seq),
            "开核执行清单ID": launch.get("G0冲突字段W0W1开核执行清单ID", ""),
            "页码版面键": page_key,
            "来源页码": launch.get("来源页码", ""),
            "版面列": launch.get("版面列", ""),
            "证据通道序号": channel_seq,
            "证据通道": launch.get("证据通道", ""),
            "开核动作组": launch.get("开核动作组", ""),
            "开核优先级": launch.get("开核优先级", ""),
            "缺口任务数": str(len(tasks)),
            "涉及字段事实数": str(count_unique(tasks, "第一闭环事实范围缺口公开账本ID")),
            "涉及任务数": str(count_unique(tasks, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(tasks, "专业行ID")),
            "涉及院校代码数": str(count_unique(tasks, "院校代码")),
            "字段名分布": dist(tasks, "字段名"),
            "私有Overlay候选字段数": str(len(private_items)),
            "PDFOCR有候选字段数": str(sum(1 for item in private_items if candidate_pair(item)[0])),
            "高校辅证有候选字段数": str(sum(
                1 for item in private_items
                if candidate_pair(item)[1] or clean(item.get("高校官网或招生章程字段值", ""))
            )),
            "双侧候选字段数": str(sum(
                1 for item in private_items
                if candidate_pair(item)[0] and (
                    candidate_pair(item)[1] or clean(item.get("高校官网或招生章程字段值", ""))
                )
            )),
            "候选一致字段数": str(buckets.get("C1-双侧候选一致但仍待核", 0)),
            "候选冲突字段数": str(buckets.get("C0-双侧候选冲突优先核", 0)),
            "仅PDFOCR候选字段数": str(buckets.get("C2-仅PDFOCR候选需补辅证", 0)),
            "仅高校辅证候选字段数": str(buckets.get("C3-仅高校辅证候选需核原页", 0)),
            "候选缺失字段数": str(buckets.get("C4-无候选需人工看图", 0)),
            "高校官网或招生章程线索已填字段数": str(count_filled(private_items, "高校官网或招生章程字段值")),
            "PDF原页人工记录已填字段数": str(count_filled(private_items, "PDF原页字段人工读数")),
            "湖北官方记录已填字段数": str(count_filled(private_items, "湖北官方字段值")),
            "高校辅证人工核验已填字段数": str(count_filled(private_items, "高校辅证人工核验记录值")),
            "字段确认已填字段数": str(count_filled(private_items, "字段确认值")),
            "候选分层分布": "；".join(f"{key}:{buckets[key]}" for key in sorted(buckets)),
            "候选分层主桶": main_bucket,
            "PDFOCR与高校辅证关系桶分布": dist(private_items, "PDFOCR与高校辅证关系桶"),
            "开核候选提示状态": status_for_bucket(main_bucket),
            "下一步候选核验动作": next_action(channel_seq, main_bucket),
            "来源缺口任务集合SHA256": sha256_values(
                task.get("G0冲突字段补证缺口任务公开账本ID", "") for task in tasks
            ),
            "来源私有Overlay记录集合SHA256": sha256_values(
                item.get("G0私有字段复核记录ID", "") for item in private_items
            ),
            "来源私有Overlay文件SHA256": private_overlay_sha,
            "公开安全策略": "公开层只保存候选分层、计数、ID和SHA；不公开私有内容、具体线索、字段记录或学校专业明细。",
        }
        add_false_fields(out)
        rows.append(out)
    return rows


def build_page_rows(
    rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    private_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    packets_by_page = defaultdict(list)
    for row in rows:
        packets_by_page[row.get("页码版面键", "")].append(row)

    active_gap_by_page = defaultdict(list)
    for row in gap_rows:
        if row.get("是否当前可并行执行") == "true" and row.get("证据通道序号") in {"01", "02", "03", "05"}:
            active_gap_by_page[row.get("页码版面键", "")].append(row)

    private_by_page = defaultdict(list)
    for row in private_rows:
        private_by_page[row.get("页码版面键", "")].append(row)

    private_overlay_sha = sha256_file(PRIVATE_OVERLAY)
    page_rows = []
    for seq, page_key in enumerate(
        sorted(
            packets_by_page,
            key=lambda key: (
                as_int(packets_by_page[key][0].get("来源页码", "")),
                side_rank(packets_by_page[key][0].get("版面列", "")),
                key,
            ),
        ),
        start=1,
    ):
        packets = packets_by_page[page_key]
        tasks = active_gap_by_page[page_key]
        private_items = private_by_page[page_key]
        buckets = Counter(candidate_bucket(item) for item in private_items)
        main_bucket = candidate_main_bucket(private_items)
        single_sided = buckets.get("C2-仅PDFOCR候选需补辅证", 0) + buckets.get("C3-仅高校辅证候选需核原页", 0)
        first = packets[0]
        out = {
            "G0冲突字段W0W1候选分层页列汇总ID": stable_id(
                "G0W0W1CANDTRIAGEPAGE", [SOURCE_PDF_SHA256, page_key]
            ),
            "来源G0冲突字段W0W1候选分层清单": source_path(OUTPUT),
            "来源G0冲突字段W0W1开核执行页列汇总": source_path(LAUNCH_PAGE),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源私有G0字段复核Overlay": "g0_conflict_field_review_private_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段W0/W1候选分层页列汇总",
            "任务粒度": "页列",
            "页列汇总序号": str(seq),
            "页码版面键": page_key,
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "开核分层工作包数": str(len(packets)),
            "当前可并行任务数": str(len(tasks)),
            "唯一候选字段数": str(len(private_items)),
            "涉及任务数": str(count_unique(tasks, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(tasks, "专业行ID")),
            "涉及院校代码数": str(count_unique(tasks, "院校代码")),
            "字段名分布": dist(private_items, "字段名"),
            "证据通道分布": dist(tasks, "证据通道"),
            "候选分层分布": "；".join(f"{key}:{buckets[key]}" for key in sorted(buckets)),
            "候选分层主桶": main_bucket,
            "候选一致唯一字段数": str(buckets.get("C1-双侧候选一致但仍待核", 0)),
            "候选冲突唯一字段数": str(buckets.get("C0-双侧候选冲突优先核", 0)),
            "单侧候选唯一字段数": str(single_sided),
            "候选缺失唯一字段数": str(buckets.get("C4-无候选需人工看图", 0)),
            "人工记录已填合计": str(
                count_filled(private_items, "PDF原页字段人工读数")
                + count_filled(private_items, "湖北官方字段值")
                + count_filled(private_items, "高校辅证人工核验记录值")
                + count_filled(private_items, "字段确认值")
            ),
            "页列候选核验状态": status_for_bucket(main_bucket),
            "页列下一步候选核验动作": "按候选分层先核冲突和单侧线索，再补PDF原页、湖北官方侧、高校辅证和双人复核记录；不得直接定案。",
            "候选分层工作包集合SHA256": sha256_values(
                row.get("G0冲突字段W0W1候选分层ID", "") for row in packets
            ),
            "来源缺口任务集合SHA256": sha256_values(
                row.get("G0冲突字段补证缺口任务公开账本ID", "") for row in tasks
            ),
            "来源私有Overlay记录集合SHA256": sha256_values(
                row.get("G0私有字段复核记录ID", "") for row in private_items
            ),
            "来源私有Overlay文件SHA256": private_overlay_sha,
            "公开安全策略": "公开层只保存页列候选分层、计数、ID和SHA；不公开私有内容、具体线索、字段记录或学校专业明细。",
        }
        add_false_fields(out)
        page_rows.append(out)
    return page_rows


def main() -> None:
    launch_rows = read_csv(LAUNCH_LEDGER)
    gap_rows = read_csv(GAP_TASKS)
    private_rows = read_csv(PRIVATE_OVERLAY)

    ledger_rows = build_rows(launch_rows, gap_rows, private_rows)
    page_rows = build_page_rows(ledger_rows, gap_rows, private_rows)

    write_csv(OUTPUT, ledger_rows, LEDGER_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)

    unique_buckets = Counter(candidate_bucket(row) for row in private_rows)
    package_buckets = Counter()
    for row in ledger_rows:
        for part in row.get("候选分层分布", "").split("；"):
            if not part or ":" not in part:
                continue
            key, raw_count = part.rsplit(":", 1)
            try:
                package_buckets[key] += int(raw_count)
            except ValueError:
                continue

    summary = {
        "status": "issue19_first_closure_g0_conflict_field_w0_w1_candidate_triage_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_launch_ledger": source_path(LAUNCH_LEDGER),
        "source_launch_ledger_sha256": sha256_file(LAUNCH_LEDGER),
        "source_launch_page": source_path(LAUNCH_PAGE),
        "source_launch_page_sha256": sha256_file(LAUNCH_PAGE),
        "source_launch_summary": source_path(LAUNCH_SUMMARY),
        "source_launch_summary_sha256": sha256_file(LAUNCH_SUMMARY),
        "source_gap_tasks": source_path(GAP_TASKS),
        "source_gap_tasks_sha256": sha256_file(GAP_TASKS),
        "source_private_overlay": "g0_conflict_field_review_private_overlay_not_public",
        "source_private_overlay_sha256": sha256_file(PRIVATE_OVERLAY),
        "output_table": source_path(OUTPUT),
        "page_summary_table": source_path(PAGE_OUTPUT),
        "ledger_row_count": len(ledger_rows),
        "page_summary_row_count": len(page_rows),
        "source_launch_row_count": len(launch_rows),
        "source_gap_task_row_count": len(gap_rows),
        "source_private_overlay_row_count": len(private_rows),
        "active_task_row_count": sum(as_int(row.get("缺口任务数")) for row in ledger_rows),
        "unique_page_side_count": count_unique(ledger_rows, "页码版面键"),
        "unique_candidate_field_count": len(private_rows),
        "candidate_field_task_channel_count": sum(as_int(row.get("私有Overlay候选字段数")) for row in ledger_rows),
        "unique_candidate_bucket_counts": dict(unique_buckets),
        "candidate_task_channel_bucket_counts": dict(package_buckets),
        "package_count_by_status": dict(Counter(row.get("开核候选提示状态", "") for row in ledger_rows)),
        "page_count_by_status": dict(Counter(row.get("页列候选核验状态", "") for row in page_rows)),
        "pdf_original_manual_record_filled_count": sum(as_int(row.get("PDF原页人工记录已填字段数")) for row in ledger_rows),
        "hubei_official_field_value_filled_count": sum(as_int(row.get("湖北官方记录已填字段数")) for row in ledger_rows),
        "school_support_manual_record_filled_count": sum(as_int(row.get("高校辅证人工核验已填字段数")) for row in ledger_rows),
        "field_confirmation_filled_count": sum(as_int(row.get("字段确认已填字段数")) for row in ledger_rows),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只把私有候选线索转成公开分层和开核优先级，不公开线索内容，不确认字段事实，不写回，不进入推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    public_safety_check([OUTPUT, PAGE_OUTPUT, SUMMARY_OUTPUT])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
