#!/usr/bin/env python3
"""Build a public priority ledger for remaining school-source gaps.

This layer compresses existing school-source status ledgers into one execution
queue. It is deliberately public-safe: no school names, major names, URLs,
OCR text, field readings, or private paths are emitted.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

LATEST = WORKING / "issue19-school-source-latest-reconciliation-public-ledger.csv"
STATUS = WORKING / "issue19-school-source-status-snapshot-public-ledger.csv"
AUTO = WORKING / "issue19-school-source-auto-execution-batches-public-ledger.csv"
C4C6_DIFF = WORKING / "issue19-c4-c6-structured-candidate-diff-public-ledger.csv"
C4C6_ATTEMPTS = WORKING / "issue19-c4-c6-school-source-acquisition-attempts-public-ledger.csv"

OUTPUT = WORKING / "issue19-school-source-gap-priority-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-gap-priority-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_gap_priority_public_ledger"
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
    "高校源缺口优先级ID",
    "来源高校源最新证据对齐账本",
    "来源高校官网辅证状态快照",
    "来源高校官网辅证自动执行批次",
    "来源C4C6结构化候选diff账本",
    "来源C4C6补源尝试账本",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "缺口优先级序号",
    "高校源最新对齐ID",
    "高校官网辅证状态快照ID",
    "高校官网辅证自动执行批次ID",
    "院校代码",
    "任务学校键SHA16",
    "原自动执行泳道",
    "原结构化输出状态桶",
    "原候选diff状态桶",
    "原补源状态桶",
    "最新高校侧证据层级",
    "相对原自动账本推进状态",
    "缺口主类",
    "缺口子类",
    "执行优先级",
    "执行优先级分",
    "自动推进泳道",
    "人工核验泳道",
    "是否需要自动补结构化",
    "是否需要继续补源",
    "是否需要回PDF原页",
    "是否需要湖北官方侧核验",
    "是否只核章程规则",
    "是否已有可用于提示的高校侧线索",
    "涉及招生明细数",
    "涉及专业组数",
    "next20任务数",
    "C4C6结构化diff包数",
    "C4C6可生成候选diff明细数",
    "C4C6计划数冲突候选数",
    "C4C6官网可补OCR计划数候选数",
    "C4C6补源尝试记录数",
    "最新公开证据集合SHA16",
    "缺口原因桶",
    "最小自动动作",
    "最小人工动作",
    "完成条件",
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
    "字段确认值",
    "人工读数",
    "候选值",
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


def to_int(value: str | int | None) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def stable_id(prefix: str, parts: list[str]) -> str:
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def sha16(parts: list[str]) -> str:
    text = "|".join(str(part or "").strip() for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def classify_gap(row: dict[str, str]) -> tuple[str, str, str, int, str, str]:
    lane = row.get("原自动执行泳道", "")
    level = row.get("最新高校侧证据层级", "")
    progress = row.get("相对原自动账本推进状态", "")
    diff_bucket = row.get("原候选diff状态桶", "")
    structure_bucket = row.get("原结构化输出状态桶", "")

    if lane == "A0-冲突回页和官方侧核验":
        return (
            "G0-冲突差异回页核验",
            "D0-计划数冲突或高校侧差异线索",
            "E0-人工先核回页",
            1000,
            "H0-整理冲突线索供核页",
            "R0-双人核PDF原页和湖北官方侧",
        )
    if lane == "A1-官网补缺线索回页核验":
        return (
            "G1-OCR补缺线索回页核验",
            "D1-高校侧可补OCR缺口线索",
            "E0-人工先核回页",
            900,
            "H1-整理补缺线索供核页",
            "R1-核PDF原页缺失字段和湖北官方侧",
        )
    if lane == "A2-专业名匹配规则或人工确认":
        return (
            "G2-专业名归属或匹配规则",
            "A2-同页专业名归属和规则待确认",
            "E0-人工先核回页",
            800,
            "H2-补专业名匹配规则",
            "R2-核同页上下文和专业组边界",
        )
    if lane == "A3-补结构化或解析公开来源":
        sub = "A3-L3已有线索待回页" if level.startswith("L3") else f"A3-{structure_bucket or '公开来源待解析'}"
        score = 720 if progress.startswith("P0") else 700
        return (
            "G3-已有公开来源待结构化",
            sub,
            "E1-自动补结构化或补源",
            score,
            "H3-补湖北物理结构化或生成diff",
            "R3-抽检结构化源后回PDF和湖北官方侧",
        )
    if lane == "A4-继续搜索高校计划网源":
        sub = "A4-仍需继续补源" if progress.startswith("P0") else "A4-已推进到结构化线索待核"
        score = 650 if progress.startswith("P0") else 620
        return (
            "G4-真缺或曾缺2026湖北物理计划网源",
            sub,
            "E1-自动补结构化或补源",
            score,
            "H4-继续补高校招生网计划网源",
            "R4-必要时人工补计划网源并核原页",
        )
    if lane == "A5-章程规则核验":
        return (
            "G5-章程规则限制专项",
            "A5-只核限制规则不核计划字段",
            "E2-规则抽检或留存",
            400,
            "H5-核章程限制规则",
            "R5-人工核体检语种单科收费校区调剂",
        )
    if lane == "A7-留存观察":
        return (
            "G6-低收益留存观察",
            "A7-暂不推进除非进入最终候选",
            "E2-规则抽检或留存",
            100,
            "H6-留存观察",
            "R6-最终候选前再升级核验",
        )
    if diff_bucket.startswith("D0"):
        return (
            "G0-冲突差异回页核验",
            "D0-计划数冲突或高校侧差异线索",
            "E0-人工先核回页",
            1000,
            "H0-整理冲突线索供核页",
            "R0-双人核PDF原页和湖北官方侧",
        )
    if diff_bucket.startswith("D1"):
        return (
            "G1-OCR补缺线索回页核验",
            "D1-高校侧可补OCR缺口线索",
            "E0-人工先核回页",
            900,
            "H1-整理补缺线索供核页",
            "R1-核PDF原页缺失字段和湖北官方侧",
        )
    return (
        "G7-其他高校侧线索待闭环",
        "Z0-按原账本继续",
        "E2-规则抽检或留存",
        300,
        "H7-按原自动账本推进",
        "R7-按原账本核验",
    )


def completion_condition(row: dict[str, str]) -> str:
    category = row.get("缺口主类", "")
    if category.startswith("G0") or category.startswith("G1"):
        return "PDF原页、湖北官方侧和高校侧差异线索三方闭环一致后，仍需人工决定是否写回。"
    if category.startswith("G2"):
        return "专业名归属、专业组边界和同页上下文人工闭环后，再进入字段事实核验。"
    if category.startswith("G3"):
        return "补出湖北物理普通本科结构化线索或确认无法结构化，并生成可回页核验的差异状态。"
    if category.startswith("G4"):
        return "找到可留存的2026湖北物理计划网源，或记录确证不可得并升级人工核第19期原页。"
    if category.startswith("G5"):
        return "章程限制、收费、校区、体检、语种、单科和调剂规则完成人工核验。"
    return "进入最终候选讨论前再升级核验，否则保持留存观察。"


def build_rows() -> list[dict[str, str]]:
    latest_rows = read_csv(LATEST)
    status_ids = {row.get("高校官网辅证状态快照ID", "") for row in read_csv(STATUS)}
    auto_ids = {row.get("高校官网辅证自动执行批次ID", "") for row in read_csv(AUTO)}

    rows: list[dict[str, str]] = []
    for source_seq, source in enumerate(latest_rows, start=1):
        status_id = source.get("高校官网辅证状态快照ID", "")
        auto_id = source.get("原自动执行批次ID", "")
        if status_id not in status_ids:
            raise ValueError(f"missing status row: {status_id}")
        if auto_id not in auto_ids:
            raise ValueError(f"missing auto row: {auto_id}")

        category, subcategory, priority, score, auto_lane, manual_lane = classify_gap(source)
        source_code = source.get("院校代码", "")
        row = {
            "高校源缺口优先级ID": stable_id(
                "SCHOOLGAP",
                [source.get("高校源最新对齐ID", ""), auto_id, status_id],
            ),
            "来源高校源最新证据对齐账本": source_path(LATEST),
            "来源高校官网辅证状态快照": source_path(STATUS),
            "来源高校官网辅证自动执行批次": source_path(AUTO),
            "来源C4C6结构化候选diff账本": source_path(C4C6_DIFF),
            "来源C4C6补源尝试账本": source_path(C4C6_ATTEMPTS),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校侧辅证任务×缺口优先级",
            "任务粒度": "公开任务级缺口；不保存学校文本、专业文本、字段读数、OCR正文或私有材料",
            "高校源最新对齐ID": source.get("高校源最新对齐ID", ""),
            "高校官网辅证状态快照ID": status_id,
            "高校官网辅证自动执行批次ID": auto_id,
            "院校代码": source_code,
            "任务学校键SHA16": sha16([source_code, auto_id, status_id]),
            "原自动执行泳道": source.get("原自动执行泳道", ""),
            "原结构化输出状态桶": source.get("原结构化输出状态桶", ""),
            "原候选diff状态桶": source.get("原候选diff状态桶", ""),
            "原补源状态桶": source.get("原补源状态桶", ""),
            "最新高校侧证据层级": source.get("最新高校侧证据层级", ""),
            "相对原自动账本推进状态": source.get("相对原自动账本推进状态", ""),
            "缺口主类": category,
            "缺口子类": subcategory,
            "执行优先级": priority,
            "执行优先级分": str(score),
            "自动推进泳道": auto_lane,
            "人工核验泳道": manual_lane,
            "是否需要自动补结构化": bool_text(category.startswith("G3")),
            "是否需要继续补源": bool_text(category.startswith("G4") and source.get("相对原自动账本推进状态", "").startswith("P0")),
            "是否需要回PDF原页": "true",
            "是否需要湖北官方侧核验": "true",
            "是否只核章程规则": bool_text(category.startswith("G5")),
            "是否已有可用于提示的高校侧线索": bool_text(source.get("最新高校侧证据层级", "").startswith("L3")),
            "涉及招生明细数": source.get("原涉及招生明细数", "0"),
            "涉及专业组数": source.get("原涉及专业组数", "0"),
            "next20任务数": source.get("next20任务数", "0"),
            "C4C6结构化diff包数": source.get("C4C6结构化diff包数", "0"),
            "C4C6可生成候选diff明细数": source.get("C4C6可生成候选diff明细数", "0"),
            "C4C6计划数冲突候选数": source.get("C4C6计划数冲突候选数", "0"),
            "C4C6官网可补OCR计划数候选数": source.get("C4C6官网可补OCR计划数候选数", "0"),
            "C4C6补源尝试记录数": source.get("C4C6补源尝试记录数", "0"),
            "最新公开证据集合SHA16": source.get("最新公开证据集合SHA16", ""),
            "缺口原因桶": source.get("仍需补源或解析原因", ""),
            "最小自动动作": source.get("最新自动建议动作", ""),
            "最小人工动作": source.get("人工最小核验动作", ""),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "公开安全策略": "公开层只保存任务ID、院校代码、状态桶、计数和SHA；不保存学校文本、专业文本、字段读数、OCR正文、URL、截图或私有路径。",
            "_source_seq": source_seq,
        }
        row["完成条件"] = completion_condition(row)
        for field in FALSE_FIELDS:
            row[field] = "false"
        rows.append(row)

    rows.sort(key=lambda row: (-to_int(row["执行优先级分"]), to_int(row["_source_seq"])))
    for index, row in enumerate(rows, start=1):
        row["缺口优先级序号"] = str(index)
        row.pop("_source_seq", None)
    return rows


def validate_public(rows: list[dict[str, str]], summary: dict) -> None:
    if len(rows) != 80:
        raise AssertionError(f"expected 80 rows, got {len(rows)}")
    if len({row["高校源缺口优先级ID"] for row in rows}) != len(rows):
        raise AssertionError("duplicate priority id")
    if any(row[field] != "false" for row in rows for field in FALSE_FIELDS):
        raise AssertionError("non-final gate opened")
    public_text = OUTPUT.read_text(encoding="utf-8-sig") + SUMMARY_OUTPUT.read_text(encoding="utf-8")
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if hits:
        raise AssertionError(f"forbidden public tokens: {hits[:8]}")
    if any(summary.get(field, 0) != 0 for field in [
        "field_writeback_ready_count",
        "recommendation_basis_allowed_count",
        "school_major_suggestion_allowed_count",
        "official_plan_replacement_allowed_count",
        "final_available_count",
    ]):
        raise AssertionError("summary gate opened")


def main() -> None:
    rows = build_rows()
    write_csv(OUTPUT, rows)

    gap_counts = Counter(row["缺口主类"] for row in rows)
    priority_counts = Counter(row["执行优先级"] for row in rows)
    evidence_counts = Counter(row["最新高校侧证据层级"] for row in rows)
    auto_lane_counts = Counter(row["原自动执行泳道"] for row in rows)
    progress_counts = Counter(row["相对原自动账本推进状态"] for row in rows)
    summary = {
        "status": "issue19_school_source_gap_priority_public_ledger_not_final",
        "generated_by": "build_issue19_school_source_gap_priority_ledger.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_latest_reconciliation": source_path(LATEST),
        "source_status_snapshot": source_path(STATUS),
        "source_auto_execution_batches": source_path(AUTO),
        "output_table": source_path(OUTPUT),
        "generated_at": GENERATED_AT,
        "row_count": len(rows),
        "unique_school_code_count": len({row["院校代码"] for row in rows if row["院校代码"]}),
        "gap_category_counts": dict(gap_counts),
        "execution_priority_counts": dict(priority_counts),
        "latest_evidence_level_counts": dict(evidence_counts),
        "auto_lane_counts": dict(auto_lane_counts),
        "progress_against_auto_counts": dict(progress_counts),
        "manual_first_count": priority_counts.get("E0-人工先核回页", 0),
        "auto_structure_or_source_count": priority_counts.get("E1-自动补结构化或补源", 0),
        "rules_or_observe_count": priority_counts.get("E2-规则抽检或留存", 0),
        "auto_structure_required_count": sum(row["是否需要自动补结构化"] == "true" for row in rows),
        "continue_source_search_required_count": sum(row["是否需要继续补源"] == "true" for row in rows),
        "pdf_page_review_required_count": sum(row["是否需要回PDF原页"] == "true" for row in rows),
        "hubei_official_review_required_count": sum(row["是否需要湖北官方侧核验"] == "true" for row in rows),
        "school_side_hint_available_count": sum(row["是否已有可用于提示的高校侧线索"] == "true" for row in rows),
        "c4c6_candidate_diff_detail_count": sum(to_int(row["C4C6可生成候选diff明细数"]) for row in rows),
        "c4c6_plan_conflict_candidate_count": sum(to_int(row["C4C6计划数冲突候选数"]) for row in rows),
        "c4c6_plan_fill_candidate_count": sum(to_int(row["C4C6官网可补OCR计划数候选数"]) for row in rows),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只安排高校源缺口优先级，不确认字段事实，不替代第19期PDF原页或湖北官方系统，不进入志愿推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    validate_public(rows, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
