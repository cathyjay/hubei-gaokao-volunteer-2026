#!/usr/bin/env python3
"""Audit private material readiness for G0 W0/W1 active work.

This public-safe layer checks whether the private review materials needed for
the active W0/W1 workboard are present and whether human review records have
been filled. It publishes only counts, statuses, IDs, and hashes.
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

ACTIVE_WORKBOARD = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-active-workboard-v1-public-ledger.csv"
)
ACTIVE_PAGE_SUMMARY = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-active-workboard-v1-page-summary.csv"
)
ACTIVE_SUMMARY = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-active-workboard-v1-summary.json"
)
GAP_TASKS = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-evidence-gap-tasks-v1-public-ledger.csv"
)
PRIVATE_OVERLAY = (
    PRIVATE_ROOT
    / "review-assets/issue19-g0-conflict-field-review-overlay-v1/g0-conflict-field-review-private-overlay.csv"
)
PRIVATE_PAGE_SIDE_DIR = (
    PRIVATE_ROOT
    / "review-assets/issue19-g0-conflict-field-review-overlay-v1/page-sides"
)
PRIVATE_REVIEW_HTML_DIR = (
    PRIVATE_ROOT
    / "review-assets/issue19-official-unavailable-sampling-review-packets/html"
)

OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-material-readiness-v1-public-ledger.csv"
)
PAGE_SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-material-readiness-v1-page-summary.csv"
)
SUMMARY_OUTPUT = (
    WORKING
    / "issue19-first-closure-g0-conflict-field-w0-w1-material-readiness-v1-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_field_w0_w1_material_readiness_v1"

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
    "G0冲突字段W0W1材料就绪公开账本ID",
    "来源G0冲突字段W0W1主动工作包公开账本",
    "来源G0冲突字段W0W1主动工作页列汇总",
    "来源G0冲突字段W0W1主动工作摘要",
    "来源G0冲突字段补证缺口任务公开账本",
    "来源私有G0字段复核Overlay",
    "来源私有页列CSV目录",
    "来源私有核页HTML目录",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "材料就绪序号",
    "主动工作包ID",
    "执行波次序号",
    "执行波次",
    "证据通道序号",
    "证据通道",
    "页码版面键",
    "来源页码",
    "版面列",
    "缺口任务数",
    "匹配私有复核行数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "字段名分布",
    "私有页图存在行数",
    "私有OCR材料存在行数",
    "私有页列CSV是否存在",
    "私有核页HTML是否存在",
    "私有材料就绪状态",
    "PDF原页专业代码记录已填数",
    "PDF原页专业名记录已填数",
    "PDF原页字段人工记录已填数",
    "湖北官方专业代码记录已填数",
    "湖北官方专业名记录已填数",
    "湖北官方字段记录已填数",
    "高校辅证种子线索行数",
    "高校辅证人工核验记录已填数",
    "PDF核页复核A记录已填数",
    "PDF核页复核B记录已填数",
    "湖北官方核验人记录已填数",
    "高校辅证核验人记录已填数",
    "双人一致性记录已填数",
    "三方一致性记录已填数",
    "字段确认记录已填数",
    "写回建议记录已填数",
    "人工补证记录状态",
    "下一步材料动作",
    "来源缺口任务集合SHA256",
    "来源私有复核记录集合SHA256",
    "私有Overlay_SHA256",
    "公开安全策略",
]

PAGE_SUMMARY_FIELDS = [
    "G0冲突字段W0W1材料就绪页列汇总ID",
    "来源G0冲突字段W0W1材料就绪公开账本",
    "来源G0冲突字段W0W1主动工作页列汇总",
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
    "材料就绪工作包数",
    "当前可并行任务数",
    "匹配私有复核行数",
    "涉及字段事实数",
    "涉及任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "证据通道分布",
    "字段名分布",
    "私有页图存在行数",
    "私有OCR材料存在行数",
    "私有页列CSV是否存在",
    "私有核页HTML是否存在",
    "PDF原页字段人工记录已填数",
    "湖北官方字段记录已填数",
    "高校辅证种子线索行数",
    "高校辅证人工核验记录已填数",
    "双人一致性记录已填数",
    "三方一致性记录已填数",
    "字段确认记录已填数",
    "写回建议记录已填数",
    "页列材料就绪状态",
    "页列人工补证记录状态",
    "材料就绪工作包集合SHA256",
    "来源缺口任务集合SHA256",
    "来源私有复核记录集合SHA256",
    "页列下一步材料动作",
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


def dist(rows: list[dict[str, str]], field: str) -> str:
    counter = Counter(clean(row.get(field, "")) or "空" for row in rows)
    return "；".join(f"{key}:{counter[key]}" for key in sorted(counter))


def count_unique(rows: list[dict[str, str]], field: str) -> int:
    return len({clean(row.get(field, "")) for row in rows if clean(row.get(field, ""))})


def count_filled(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if clean(row.get(field, "")))


def private_rel_exists(value: str) -> bool:
    value = clean(value)
    return bool(value) and (PRIVATE_ROOT / value).exists()


def material_status(rows: list[dict[str, str]], page_key: str) -> str:
    page_csv_exists = (PRIVATE_PAGE_SIDE_DIR / f"{page_key}.csv").exists()
    html_exists = (PRIVATE_REVIEW_HTML_DIR / f"{page_key}.html").exists()
    page_images_ok = sum(1 for row in rows if private_rel_exists(row.get("私有页图相对路径", ""))) == len(rows)
    ocr_text_ok = sum(1 for row in rows if private_rel_exists(row.get("私有OCR文本相对路径", ""))) == len(rows)
    if rows and page_csv_exists and html_exists and page_images_ok and ocr_text_ok:
        return "ready_private_materials_present"
    return "blocked_missing_private_materials"


def human_record_status(rows: list[dict[str, str]], channel_seq: str) -> str:
    if not rows:
        return "blocked_no_private_overlay_match"
    if channel_seq == "01":
        return (
            "ready_for_field_confirmation_after_pdf_records"
            if count_filled(rows, "PDF原页字段人工读数") == len(rows)
            else "blocked_missing_pdf_original_records"
        )
    if channel_seq == "02":
        return (
            "ready_for_field_confirmation_after_hubei_records"
            if count_filled(rows, "湖北官方字段值") == len(rows)
            else "blocked_missing_hubei_official_records"
        )
    if channel_seq == "03":
        return (
            "ready_for_field_confirmation_after_school_support_review"
            if count_filled(rows, "高校辅证人工核验记录值") == len(rows)
            else "blocked_missing_school_support_manual_review"
        )
    if channel_seq == "05":
        a_ok = count_filled(rows, "PDF核页复核人A") == len(rows)
        b_ok = count_filled(rows, "PDF核页复核人B") == len(rows)
        conclusion_ok = count_filled(rows, "双人一致性结论") == len(rows)
        return (
            "ready_for_three_way_after_double_review"
            if a_ok and b_ok and conclusion_ok
            else "blocked_missing_double_review_records"
        )
    return "blocked_unknown_channel"


def next_action(channel_seq: str, human_status: str) -> str:
    if human_status.startswith("ready_"):
        return "本通道人工记录已具备；仍需等待其他通道和三方闭环后才能字段确认。"
    if channel_seq == "01":
        return "打开私有页图、OCR材料和页列CSV，人工核PDF原页并填写PDF原页记录。"
    if channel_seq == "02":
        return "优先进入湖北官方系统或省招办计划核验并填写湖北官方记录；不可用高校源替代。"
    if channel_seq == "03":
        return "对高校官网或章程辅证种子做人工核验；只作为double check线索。"
    if channel_seq == "05":
        return "安排A/B双人核页并填写一致性记录；未完成前不得进入冲突定案。"
    return "按证据通道补齐私有人工记录。"


def public_safety_check(paths: list[Path]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    leaked = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if leaked:
        raise RuntimeError(f"public output contains forbidden tokens: {leaked[:20]}")


def build_rows(
    active_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    private_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    gap_by_page_channel = defaultdict(list)
    for row in gap_rows:
        if row.get("是否当前可并行执行") == "true" and row.get("证据通道序号") in {"01", "02", "03", "05"}:
            gap_by_page_channel[(row.get("页码版面键", ""), row.get("证据通道序号", ""))].append(row)
    private_by_overlay_id = {
        row.get("G0冲突字段复核Overlay公开账本ID", ""): row
        for row in private_rows
    }

    rows = []
    for seq, active in enumerate(active_rows, start=1):
        page_key = active.get("页码版面键", "")
        channel_seq = active.get("证据通道序号", "")
        source_tasks = gap_by_page_channel[(page_key, channel_seq)]
        overlay_rows = [
            private_by_overlay_id.get(row.get("G0冲突字段复核Overlay公开账本ID", ""), {})
            for row in source_tasks
        ]
        overlay_rows = [row for row in overlay_rows if row]
        private_material_status = material_status(overlay_rows, page_key)
        private_human_status = human_record_status(overlay_rows, channel_seq)
        out = {
            "G0冲突字段W0W1材料就绪公开账本ID": stable_id(
                "G0W0W1MATERIAL", [SOURCE_PDF_SHA256, page_key, channel_seq]
            ),
            "来源G0冲突字段W0W1主动工作包公开账本": source_path(ACTIVE_WORKBOARD),
            "来源G0冲突字段W0W1主动工作页列汇总": source_path(ACTIVE_PAGE_SUMMARY),
            "来源G0冲突字段W0W1主动工作摘要": source_path(ACTIVE_SUMMARY),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源私有G0字段复核Overlay": "g0_conflict_field_review_private_overlay_not_public",
            "来源私有页列CSV目录": "g0_conflict_field_private_page_side_csv_dir_not_public",
            "来源私有核页HTML目录": "first_closure_private_review_html_dir_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段W0/W1材料就绪",
            "任务粒度": "页列×证据通道",
            "材料就绪序号": str(seq),
            "主动工作包ID": active.get("G0冲突字段W0W1主动工作包公开账本ID", ""),
            "执行波次序号": active.get("执行波次序号", ""),
            "执行波次": active.get("执行波次", ""),
            "证据通道序号": channel_seq,
            "证据通道": active.get("证据通道", ""),
            "页码版面键": page_key,
            "来源页码": active.get("来源页码", ""),
            "版面列": active.get("版面列", ""),
            "缺口任务数": str(len(source_tasks)),
            "匹配私有复核行数": str(len(overlay_rows)),
            "涉及字段事实数": str(count_unique(source_tasks, "G0冲突字段补证闭环结果公开账本ID")),
            "涉及任务数": str(count_unique(source_tasks, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(source_tasks, "专业行ID")),
            "涉及院校代码数": str(count_unique(source_tasks, "院校代码")),
            "字段名分布": active.get("字段名分布", ""),
            "私有页图存在行数": str(sum(1 for row in overlay_rows if private_rel_exists(row.get("私有页图相对路径", "")))),
            "私有OCR材料存在行数": str(sum(1 for row in overlay_rows if private_rel_exists(row.get("私有OCR文本相对路径", "")))),
            "私有页列CSV是否存在": str((PRIVATE_PAGE_SIDE_DIR / f"{page_key}.csv").exists()).lower(),
            "私有核页HTML是否存在": str((PRIVATE_REVIEW_HTML_DIR / f"{page_key}.html").exists()).lower(),
            "私有材料就绪状态": private_material_status,
            "PDF原页专业代码记录已填数": str(count_filled(overlay_rows, "PDF原页专业代号读数")),
            "PDF原页专业名记录已填数": str(count_filled(overlay_rows, "PDF原页专业名称读数")),
            "PDF原页字段人工记录已填数": str(count_filled(overlay_rows, "PDF原页字段人工读数")),
            "湖北官方专业代码记录已填数": str(count_filled(overlay_rows, "湖北官方专业代号")),
            "湖北官方专业名记录已填数": str(count_filled(overlay_rows, "湖北官方专业名称")),
            "湖北官方字段记录已填数": str(count_filled(overlay_rows, "湖北官方字段值")),
            "高校辅证种子线索行数": str(count_filled(overlay_rows, "高校官网或招生章程字段值")),
            "高校辅证人工核验记录已填数": str(count_filled(overlay_rows, "高校辅证人工核验记录值")),
            "PDF核页复核A记录已填数": str(count_filled(overlay_rows, "PDF核页复核人A")),
            "PDF核页复核B记录已填数": str(count_filled(overlay_rows, "PDF核页复核人B")),
            "湖北官方核验人记录已填数": str(count_filled(overlay_rows, "湖北官方核验人")),
            "高校辅证核验人记录已填数": str(count_filled(overlay_rows, "高校辅证核验人")),
            "双人一致性记录已填数": str(count_filled(overlay_rows, "双人一致性结论")),
            "三方一致性记录已填数": str(count_filled(overlay_rows, "三方一致性结论")),
            "字段确认记录已填数": str(count_filled(overlay_rows, "字段确认值")),
            "写回建议记录已填数": str(count_filled(overlay_rows, "字段事实写回建议")),
            "人工补证记录状态": private_human_status,
            "下一步材料动作": next_action(channel_seq, private_human_status),
            "来源缺口任务集合SHA256": sha256_values(
                row.get("G0冲突字段补证缺口任务公开账本ID", "") for row in source_tasks
            ),
            "来源私有复核记录集合SHA256": sha256_values(
                row.get("G0私有字段复核记录ID", "") for row in overlay_rows
            ),
            "私有Overlay_SHA256": sha256_file(PRIVATE_OVERLAY),
            "公开安全策略": "公开层只保存材料是否存在、记录填充计数、ID和SHA；不公开私有路径、识别内容、候选内容、人工内容或学校专业明细。",
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
        all_material_ready = all(row.get("私有材料就绪状态") == "ready_private_materials_present" for row in packets)
        all_human_ready = all(row.get("人工补证记录状态", "").startswith("ready_") for row in packets)
        out = {
            "G0冲突字段W0W1材料就绪页列汇总ID": stable_id(
                "G0W0W1MATERIALPAGE", [SOURCE_PDF_SHA256, page_key]
            ),
            "来源G0冲突字段W0W1材料就绪公开账本": source_path(OUTPUT),
            "来源G0冲突字段W0W1主动工作页列汇总": source_path(ACTIVE_PAGE_SUMMARY),
            "来源G0冲突字段补证缺口任务公开账本": source_path(GAP_TASKS),
            "来源私有G0字段复核Overlay": "g0_conflict_field_review_private_overlay_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突字段W0/W1材料就绪页列汇总",
            "任务粒度": "页列",
            "页列汇总序号": str(seq),
            "页码版面键": page_key,
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "材料就绪工作包数": str(len(packets)),
            "当前可并行任务数": str(len(gap_items)),
            "匹配私有复核行数": str(max(as_int(row.get("匹配私有复核行数")) for row in packets)),
            "涉及字段事实数": str(count_unique(gap_items, "G0冲突字段补证闭环结果公开账本ID")),
            "涉及任务数": str(count_unique(gap_items, "稳定基座第一闭环明细任务ID")),
            "涉及专业行数": str(count_unique(gap_items, "专业行ID")),
            "涉及院校代码数": str(count_unique(gap_items, "院校代码")),
            "证据通道分布": dist(gap_items, "证据通道"),
            "字段名分布": dist(gap_items, "字段名"),
            "私有页图存在行数": str(max(as_int(row.get("私有页图存在行数")) for row in packets)),
            "私有OCR材料存在行数": str(max(as_int(row.get("私有OCR材料存在行数")) for row in packets)),
            "私有页列CSV是否存在": str(all(row.get("私有页列CSV是否存在") == "true" for row in packets)).lower(),
            "私有核页HTML是否存在": str(all(row.get("私有核页HTML是否存在") == "true" for row in packets)).lower(),
            "PDF原页字段人工记录已填数": str(max(as_int(row.get("PDF原页字段人工记录已填数")) for row in packets)),
            "湖北官方字段记录已填数": str(max(as_int(row.get("湖北官方字段记录已填数")) for row in packets)),
            "高校辅证种子线索行数": str(max(as_int(row.get("高校辅证种子线索行数")) for row in packets)),
            "高校辅证人工核验记录已填数": str(max(as_int(row.get("高校辅证人工核验记录已填数")) for row in packets)),
            "双人一致性记录已填数": str(max(as_int(row.get("双人一致性记录已填数")) for row in packets)),
            "三方一致性记录已填数": str(max(as_int(row.get("三方一致性记录已填数")) for row in packets)),
            "字段确认记录已填数": str(max(as_int(row.get("字段确认记录已填数")) for row in packets)),
            "写回建议记录已填数": str(max(as_int(row.get("写回建议记录已填数")) for row in packets)),
            "页列材料就绪状态": (
                "ready_private_materials_present"
                if all_material_ready else "blocked_missing_private_materials"
            ),
            "页列人工补证记录状态": (
                "ready_all_w0_w1_human_records_present"
                if all_human_ready else "blocked_missing_w0_w1_human_records"
            ),
            "材料就绪工作包集合SHA256": sha256_values(
                row.get("G0冲突字段W0W1材料就绪公开账本ID", "") for row in packets
            ),
            "来源缺口任务集合SHA256": sha256_values(
                row.get("G0冲突字段补证缺口任务公开账本ID", "") for row in gap_items
            ),
            "来源私有复核记录集合SHA256": sha256_values(
                row.get("来源私有复核记录集合SHA256", "") for row in packets
            ),
            "页列下一步材料动作": "私有页图、OCR材料、页列CSV和核页HTML已就绪时，下一步应补 PDF 原页、湖北官方侧、高校辅证和双人复核人工记录。",
            "公开安全策略": "公开层只保存页列级材料状态、记录填充计数、ID和SHA；不公开私有路径、识别内容、候选内容、人工内容或学校专业明细。",
        }
        add_false_fields(out)
        page_rows.append(out)
    return page_rows


def main() -> None:
    active_rows = read_csv(ACTIVE_WORKBOARD)
    gap_rows = read_csv(GAP_TASKS)
    private_rows = read_csv(PRIVATE_OVERLAY)
    ledger_rows = build_rows(active_rows, gap_rows, private_rows)
    page_rows = build_page_rows(ledger_rows, gap_rows)

    write_csv(OUTPUT, ledger_rows, LEDGER_FIELDS)
    write_csv(PAGE_SUMMARY_OUTPUT, page_rows, PAGE_SUMMARY_FIELDS)

    summary = {
        "status": "issue19_first_closure_g0_conflict_field_w0_w1_material_readiness_v1_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_active_workboard": source_path(ACTIVE_WORKBOARD),
        "source_active_workboard_sha256": sha256_file(ACTIVE_WORKBOARD),
        "source_active_page_summary": source_path(ACTIVE_PAGE_SUMMARY),
        "source_active_page_summary_sha256": sha256_file(ACTIVE_PAGE_SUMMARY),
        "source_active_summary": source_path(ACTIVE_SUMMARY),
        "source_active_summary_sha256": sha256_file(ACTIVE_SUMMARY),
        "source_gap_tasks": source_path(GAP_TASKS),
        "source_gap_tasks_sha256": sha256_file(GAP_TASKS),
        "private_overlay_sha256": sha256_file(PRIVATE_OVERLAY),
        "output_table": source_path(OUTPUT),
        "page_summary_table": source_path(PAGE_SUMMARY_OUTPUT),
        "ledger_row_count": len(ledger_rows),
        "page_summary_row_count": len(page_rows),
        "source_active_workboard_row_count": len(active_rows),
        "source_gap_task_row_count": len(gap_rows),
        "private_overlay_row_count": len(private_rows),
        "active_task_row_count": sum(as_int(row.get("缺口任务数")) for row in ledger_rows),
        "unique_page_side_count": count_unique(ledger_rows, "页码版面键"),
        "unique_material_package_count": count_unique(ledger_rows, "G0冲突字段W0W1材料就绪公开账本ID"),
        "material_ready_package_count": sum(
            1 for row in ledger_rows
            if row.get("私有材料就绪状态") == "ready_private_materials_present"
        ),
        "material_blocked_package_count": sum(
            1 for row in ledger_rows
            if row.get("私有材料就绪状态") != "ready_private_materials_present"
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
        "human_status_counts": dict(Counter(row.get("人工补证记录状态", "") for row in ledger_rows)),
        "page_material_ready_count": sum(
            1 for row in page_rows
            if row.get("页列材料就绪状态") == "ready_private_materials_present"
        ),
        "page_human_ready_count": sum(
            1 for row in page_rows
            if row.get("页列人工补证记录状态") == "ready_all_w0_w1_human_records_present"
        ),
        "pdf_original_field_manual_record_filled_count": sum(
            as_int(row.get("PDF原页字段人工记录已填数")) for row in ledger_rows
        ),
        "hubei_official_field_record_filled_count": sum(
            as_int(row.get("湖北官方字段记录已填数")) for row in ledger_rows
        ),
        "school_support_seed_count": sum(
            as_int(row.get("高校辅证种子线索行数")) for row in ledger_rows
            if row.get("证据通道序号") == "03"
        ),
        "school_support_manual_record_filled_count": sum(
            as_int(row.get("高校辅证人工核验记录已填数")) for row in ledger_rows
        ),
        "double_review_consensus_filled_count": sum(
            as_int(row.get("双人一致性记录已填数")) for row in ledger_rows
        ),
        "three_way_consensus_filled_count": sum(
            as_int(row.get("三方一致性记录已填数")) for row in ledger_rows
        ),
        "field_confirmation_record_filled_count": sum(
            as_int(row.get("字段确认记录已填数")) for row in ledger_rows
        ),
        "writeback_suggestion_record_filled_count": sum(
            as_int(row.get("写回建议记录已填数")) for row in ledger_rows
        ),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只审计W0/W1私有材料是否就绪和人工记录填充计数，不确认字段事实，不写回，不进入推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    public_safety_check([OUTPUT, PAGE_SUMMARY_OUTPUT, SUMMARY_OUTPUT])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
