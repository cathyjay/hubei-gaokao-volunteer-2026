#!/usr/bin/env python3
"""Build the first-closure next-action matrix.

This matrix combines first-closure PDF/OCR/conflict status with the latest
school-source reconciliation layer. It is an execution aid only: it does not
confirm field values and it never opens writeback or recommendation gates.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"
EXPORTS = ROOT / "data/exports"

FIRST_EVIDENCE = WORKING / "issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv"
FIRST_PAGE = WORKING / "issue19-stable-foundation-first-closure-evidence-status-page-side-summary.csv"
SCHOOL_RECON = WORKING / "issue19-school-source-latest-reconciliation-public-ledger.csv"
ACTION_PACK = EXPORTS / "issue19-next-closure-family-review-v1-first-closure-action-pack.csv"

TASK_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-next-action-matrix.csv"
PAGE_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-next-action-page-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-next-action-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_next_action_matrix"
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

TASK_FIELDS = [
    "第一闭环下一步动作ID",
    "来源第一闭环证据状态账本",
    "来源第一闭环页列证据汇总",
    "来源高校源最新证据对齐账本",
    "来源第一闭环64小包",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "动作矩阵序号",
    "稳定基座第一闭环明细任务ID",
    "第一闭环证据状态公开账本ID",
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
    "第一闭环页列优先级",
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
    "候选提示综合桶",
    "官网辅证自动动作",
    "官网证据强度",
    "官网来源状态",
    "计划数核验状态",
    "同校高校源任务数",
    "同校高校源最新证据层级集合",
    "同校高校源最高证据层级",
    "同校高校源推进状态集合",
    "同校L3结构化或diff任务数",
    "同校L1入口探针任务数",
    "同校L0无源任务数",
    "同校高校源可用性",
    "同校高校源最新证据SHA16集合",
    "核验动作层级",
    "人工最小核验动作",
    "自动可继续推进动作",
    "页列主阻断",
    "页列建议下一步动作",
    "关联64小包数量",
    "关联64小包类型分布",
    "完成条件",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "公开安全策略",
]

PAGE_FIELDS = [
    "第一闭环页列下一步动作ID",
    "来源第一闭环下一步动作矩阵",
    "来源第一闭环页列证据汇总",
    "来源第一闭环64小包",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "页列动作序号",
    "稳定基座第一闭环页列包ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "执行泳道",
    "第一闭环页列优先级",
    "页列任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "动作矩阵任务数",
    "N0冲突双人核页任务数",
    "N1高校补缺回页任务数",
    "N2机器坐标辅助核页任务数",
    "N3无候选人工看图任务数",
    "N4PDFOCR候选确认任务数",
    "N5多源一致待官核任务数",
    "PDF原页待核任务数",
    "湖北官方侧待核任务数",
    "高校辅证线索任务数",
    "同校L3结构化或diff任务数",
    "同校L1入口探针任务数",
    "同校L0无源任务数",
    "关联64小包数量",
    "关联64小包类型分布",
    "核验动作层级分布",
    "高校源可用性分布",
    "页列主阻断",
    "页列建议下一步动作",
    "完成条件",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
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


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def sha16_values(values: list[str]) -> str:
    clean = [str(value or "").strip() for value in values if str(value or "").strip()]
    return hashlib.sha256("|".join(sorted(clean)).encode("utf-8")).hexdigest()[:16] if clean else ""


def compact(values: list[str], limit: int = 5) -> str:
    clean: list[str] = []
    for value in values:
        value = str(value or "").strip()
        if value and value not in clean:
            clean.append(value)
    clean.sort()
    if len(clean) > limit:
        clean = clean[:limit] + [f"另有{len(clean) - limit}项"]
    return "；".join(clean)


def compact_counter(counter: Counter) -> str:
    return "；".join(f"{key}×{counter[key]}" for key in sorted(counter))


def bool_true(value: str) -> bool:
    return str(value).strip().lower() == "true"


def evidence_rank(level: str) -> int:
    if level.startswith("L3-"):
        return 3
    if level.startswith("L1-"):
        return 1
    if level.startswith("L0-"):
        return 0
    return -1


def best_level(levels: list[str]) -> str:
    if not levels:
        return "LX-同校暂无高校源对齐任务"
    return sorted(levels, key=evidence_rank, reverse=True)[0]


def school_source_availability(levels: list[str]) -> str:
    best = best_level(levels)
    if best.startswith("L3-"):
        return "S3-同校已有结构化或diff线索可作核页提示"
    if best.startswith("L1-"):
        return "S1-同校只有入口或探针记录仍需补源"
    if best.startswith("L0-"):
        return "S0-同校暂无可复用高校侧计划源"
    return "SNA-同校不在80条高校源任务内"


def action_level(row: dict[str, str]) -> str:
    conflict = row.get("冲突状态", "")
    ocr_status = row.get("OCR提示状态", "")
    machine_status = row.get("机器坐标提示状态", "")
    if conflict.startswith("C0-") or bool_true(row.get("是否存在PDFOCR与高校冲突", "")):
        return "N0-先双人核PDF原页冲突"
    if conflict.startswith("C1-"):
        return "N1-高校补缺线索回PDF原页"
    if machine_status.startswith("M1-") or bool_true(row.get("是否有机器坐标提示", "")):
        return "N2-机器坐标辅助核PDF原页"
    if ocr_status.startswith("O5-"):
        return "N3-无稳定候选人工看图"
    if conflict.startswith("C3-"):
        return "N4-PDFOCR候选人工确认"
    if conflict.startswith("C2-"):
        return "N5-多源一致仍待湖北官方侧"
    return "N6-随页列常规闭环"


def manual_action(row: dict[str, str], availability: str) -> str:
    level = action_level(row)
    if level.startswith("N0-"):
        return "双人回看PDF原页，先判定PDFOCR与高校辅证冲突字段，再核湖北官方侧。"
    if level.startswith("N1-"):
        return "回看PDF原页补专业计划数/学费/选科，再用高校辅证作差异解释，最后核湖北官方侧。"
    if level.startswith("N2-"):
        return "按机器坐标提示定位原页字段，完成人工记录后再核湖北官方侧。"
    if level.startswith("N3-"):
        return "直接打开PDF原页所在页列人工看图，必要时同页列连带复核。"
    if level.startswith("N4-"):
        return "按PDFOCR候选逐项人工确认，不能自动写回。"
    if level.startswith("N5-"):
        return "保留多源一致线索，但必须等湖北官方侧确认后才能评估写回。"
    if availability.startswith("S3-"):
        return "同校高校源可辅助核页，但仍先完成PDF原页和湖北官方侧。"
    return "按页列执行队列完成PDF原页、湖北官方侧和必要高校辅证记录。"


def auto_action(row: dict[str, str], availability: str, progress_values: list[str]) -> str:
    if availability.startswith("S3-"):
        return "可把同校结构化或diff线索接入核页提示，不允许替代湖北官方计划。"
    if availability.startswith("S1-"):
        return "继续解析入口、PDF、XLSX、HTML或公开API，目标是取得湖北物理逐专业计划线索。"
    if availability.startswith("S0-"):
        return "继续搜索高校招生网分省分专业计划源，不能迁移外省计划。"
    if any(value.startswith("P0-") for value in progress_values):
        return "同校高校源仍缺口，自动补源和人工核页并行。"
    return "本任务暂无新增自动高校源动作，优先按第一闭环页列核验。"


def aggregate_school_reconciliation(rows: list[dict[str, str]]) -> dict[str, dict]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("院校代码", "")].append(row)

    result = {}
    for code, items in grouped.items():
        levels = [item.get("最新高校侧证据层级", "") for item in items]
        progress = [item.get("相对原自动账本推进状态", "") for item in items]
        result[code] = {
            "task_count": len(items),
            "levels": levels,
            "best_level": best_level(levels),
            "progress": progress,
            "l3": sum(level.startswith("L3-") for level in levels),
            "l1": sum(level.startswith("L1-") for level in levels),
            "l0": sum(level.startswith("L0-") for level in levels),
            "availability": school_source_availability(levels),
            "sha_set": [item.get("最新公开证据集合SHA16", "") for item in items],
        }
    return result


def aggregate_action_pack(rows: list[dict[str, str]]) -> dict[str, dict]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("页码版面", "")].append(row)
    return {
        key: {
            "count": len(items),
            "type_counts": Counter(item.get("包类型", "") for item in items),
        }
        for key, items in grouped.items()
    }


def main() -> None:
    evidence_rows = read_csv(FIRST_EVIDENCE)
    page_rows = read_csv(FIRST_PAGE)
    school_rows = read_csv(SCHOOL_RECON)
    action_rows = read_csv(ACTION_PACK)

    school_by_code = aggregate_school_reconciliation(school_rows)
    action_by_page = aggregate_action_pack(action_rows)
    page_by_key = {row.get("页码版面键", ""): row for row in page_rows}

    task_rows: list[dict[str, str]] = []
    for index, row in enumerate(evidence_rows, 1):
        code = row.get("院校代码", "")
        school = school_by_code.get(code, {
            "task_count": 0,
            "levels": [],
            "best_level": "LX-同校暂无高校源对齐任务",
            "progress": [],
            "l3": 0,
            "l1": 0,
            "l0": 0,
            "availability": "SNA-同校不在80条高校源任务内",
            "sha_set": [],
        })
        page_key = row.get("页码版面键", "")
        action_pack = action_by_page.get(page_key, {"count": 0, "type_counts": Counter()})
        level = action_level(row)
        availability = school["availability"]
        out = {
            "第一闭环下一步动作ID": stable_id(
                "FIRSTNEXT",
                [row.get("稳定基座第一闭环明细任务ID", ""), row.get("第一闭环证据状态公开账本ID", "")],
            ),
            "来源第一闭环证据状态账本": source_path(FIRST_EVIDENCE),
            "来源第一闭环页列证据汇总": source_path(FIRST_PAGE),
            "来源高校源最新证据对齐账本": source_path(SCHOOL_RECON),
            "来源第一闭环64小包": source_path(ACTION_PACK),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环明细任务",
            "任务粒度": "逐任务×下一步核验动作×同校高校源状态",
            "动作矩阵序号": str(index),
            "同校高校源任务数": str(school["task_count"]),
            "同校高校源最新证据层级集合": compact(school["levels"]),
            "同校高校源最高证据层级": school["best_level"],
            "同校高校源推进状态集合": compact(school["progress"]),
            "同校L3结构化或diff任务数": str(school["l3"]),
            "同校L1入口探针任务数": str(school["l1"]),
            "同校L0无源任务数": str(school["l0"]),
            "同校高校源可用性": availability,
            "同校高校源最新证据SHA16集合": compact(school["sha_set"]),
            "核验动作层级": level,
            "人工最小核验动作": manual_action(row, availability),
            "自动可继续推进动作": auto_action(row, availability, school["progress"]),
            "关联64小包数量": str(action_pack["count"]),
            "关联64小包类型分布": compact_counter(action_pack["type_counts"]),
            "完成条件": "PDF原页、湖北官方侧、必要高校辅证和双人复核记录完成后，仍需人工评估是否可写回。",
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "公开安全策略": "只保存公开状态桶、计数、ID和SHA，不保存学校专业明细、字段明细值、识别正文、人工记录或私有路径。",
        }
        for field in FALSE_FIELDS:
            out[field] = "false"
        for field in [
            "稳定基座第一闭环明细任务ID",
            "第一闭环证据状态公开账本ID",
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
            "第一闭环页列优先级",
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
            "候选提示综合桶",
            "官网辅证自动动作",
            "官网证据强度",
            "官网来源状态",
            "计划数核验状态",
            "页列主阻断",
            "页列建议下一步动作",
        ]:
            out[field] = row.get(field, "")
        task_rows.append(out)

    by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in task_rows:
        by_page[row.get("页码版面键", "")].append(row)

    page_out_rows: list[dict[str, str]] = []
    for page_index, key in enumerate(sorted(by_page, key=lambda value: to_int(value.split("-")[0])), 1):
        rows = by_page[key]
        page_source = page_by_key.get(key, {})
        level_counts = Counter(row.get("核验动作层级", "") for row in rows)
        availability_counts = Counter(row.get("同校高校源可用性", "") for row in rows)
        action_pack = action_by_page.get(key, {"count": 0, "type_counts": Counter()})
        out = {
            "第一闭环页列下一步动作ID": stable_id(
                "FIRSTNEXTPAGE",
                [page_source.get("稳定基座第一闭环页列包ID", ""), key],
            ),
            "来源第一闭环下一步动作矩阵": source_path(TASK_OUTPUT),
            "来源第一闭环页列证据汇总": source_path(FIRST_PAGE),
            "来源第一闭环64小包": source_path(ACTION_PACK),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": f"{DATA_STAGE}_page_summary",
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "页列×下一步核验动作汇总",
            "页列动作序号": str(page_index),
            "稳定基座第一闭环页列包ID": page_source.get("稳定基座第一闭环页列包ID", ""),
            "来源页码": page_source.get("来源页码", ""),
            "版面列": page_source.get("版面列", ""),
            "页码版面键": key,
            "执行泳道": page_source.get("执行泳道", ""),
            "第一闭环页列优先级": page_source.get("第一闭环页列优先级", ""),
            "页列任务数": page_source.get("页列任务数", str(len(rows))),
            "涉及专业行数": page_source.get("涉及专业行数", ""),
            "涉及院校代码数": page_source.get("涉及院校代码数", ""),
            "动作矩阵任务数": str(len(rows)),
            "N0冲突双人核页任务数": str(level_counts.get("N0-先双人核PDF原页冲突", 0)),
            "N1高校补缺回页任务数": str(level_counts.get("N1-高校补缺线索回PDF原页", 0)),
            "N2机器坐标辅助核页任务数": str(level_counts.get("N2-机器坐标辅助核PDF原页", 0)),
            "N3无候选人工看图任务数": str(level_counts.get("N3-无稳定候选人工看图", 0)),
            "N4PDFOCR候选确认任务数": str(level_counts.get("N4-PDFOCR候选人工确认", 0)),
            "N5多源一致待官核任务数": str(level_counts.get("N5-多源一致仍待湖北官方侧", 0)),
            "PDF原页待核任务数": page_source.get("PDF原页待核任务数", ""),
            "湖北官方侧待核任务数": page_source.get("湖北官方侧待核任务数", ""),
            "高校辅证线索任务数": page_source.get("高校辅证线索任务数", ""),
            "同校L3结构化或diff任务数": str(sum(to_int(row.get("同校L3结构化或diff任务数")) for row in rows)),
            "同校L1入口探针任务数": str(sum(to_int(row.get("同校L1入口探针任务数")) for row in rows)),
            "同校L0无源任务数": str(sum(to_int(row.get("同校L0无源任务数")) for row in rows)),
            "关联64小包数量": str(action_pack["count"]),
            "关联64小包类型分布": compact_counter(action_pack["type_counts"]),
            "核验动作层级分布": compact_counter(level_counts),
            "高校源可用性分布": compact_counter(availability_counts),
            "页列主阻断": page_source.get("页列主阻断", ""),
            "页列建议下一步动作": page_source.get("页列建议下一步动作", ""),
            "完成条件": "页列内所有任务完成PDF原页、湖北官方侧、必要高校辅证和双人复核记录后，仍不自动写回。",
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "公开安全策略": "页列摘要只保存计数、分布、ID和SHA，不保存学校专业明细、字段明细值、识别正文、人工记录或私有路径。",
        }
        for field in FALSE_FIELDS:
            out[field] = "false"
        page_out_rows.append(out)

    write_csv(TASK_OUTPUT, task_rows, TASK_FIELDS)
    write_csv(PAGE_OUTPUT, page_out_rows, PAGE_FIELDS)

    task_text = TASK_OUTPUT.read_text(encoding="utf-8", errors="ignore")
    page_text = PAGE_OUTPUT.read_text(encoding="utf-8", errors="ignore")
    forbidden_hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in task_text or token in page_text]
    if forbidden_hits:
        raise SystemExit(f"公开输出包含禁止内容：{forbidden_hits[:5]}")

    action_counts = Counter(row.get("核验动作层级", "") for row in task_rows)
    availability_counts = Counter(row.get("同校高校源可用性", "") for row in task_rows)
    source_type_counts = Counter(row.get("任务来源类型", "") for row in task_rows)
    summary = {
        "status": "issue19_stable_foundation_first_closure_next_action_matrix_ready_not_final",
        "generated_by": "build_issue19_first_closure_next_action_matrix.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_first_closure_evidence_status": source_path(FIRST_EVIDENCE),
        "source_first_closure_page_summary": source_path(FIRST_PAGE),
        "source_school_source_latest_reconciliation": source_path(SCHOOL_RECON),
        "source_first_closure_action_pack": source_path(ACTION_PACK),
        "output_task_matrix": source_path(TASK_OUTPUT),
        "output_page_summary": source_path(PAGE_OUTPUT),
        "task_row_count": len(task_rows),
        "page_side_row_count": len(page_out_rows),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID", "") for row in task_rows}),
        "unique_page_side_count": len({row.get("页码版面键", "") for row in task_rows}),
        "task_source_type_counts": dict(source_type_counts),
        "next_action_level_counts": dict(action_counts),
        "school_source_availability_counts": dict(availability_counts),
        "pdf_pending_task_count": sum(row.get("PDF原页核页状态") == "pending_pdf_page_review" for row in task_rows),
        "hubei_official_pending_task_count": sum(
            row.get("湖北官方系统或省招办计划核验状态") == "pending_hubei_official_plan_review"
            for row in task_rows
        ),
        "double_review_required_count": sum(bool_true(row.get("是否需要双人复核", "")) for row in task_rows),
        "direct_image_review_required_count": sum(bool_true(row.get("是否需要人工直接看图", "")) for row in task_rows),
        "with_school_source_l3_or_diff_task_count": sum(
            row.get("同校高校源可用性") == "S3-同校已有结构化或diff线索可作核页提示"
            for row in task_rows
        ),
        "with_school_source_l1_task_count": sum(
            row.get("同校高校源可用性") == "S1-同校只有入口或探针记录仍需补源"
            for row in task_rows
        ),
        "with_school_source_l0_task_count": sum(
            row.get("同校高校源可用性") == "S0-同校暂无可复用高校侧计划源"
            for row in task_rows
        ),
        "action_pack_linked_page_count": sum(to_int(row.get("关联64小包数量")) > 0 for row in page_out_rows),
        "action_pack_linked_task_count": sum(to_int(row.get("关联64小包数量")) > 0 for row in task_rows),
        "task_matrix_sha16": sha16_values([row.get("第一闭环下一步动作ID", "") for row in task_rows]),
        "page_summary_sha16": sha16_values([row.get("第一闭环页列下一步动作ID", "") for row in page_out_rows]),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该矩阵只安排第一闭环下一步动作，不确认计划数、学费、选科、专业名或专业组边界事实。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
