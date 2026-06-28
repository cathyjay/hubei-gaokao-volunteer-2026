#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

AUTO_LEDGER = WORKING / "issue19-school-source-auto-execution-batches-public-ledger.csv"
STATUS_SNAPSHOT = WORKING / "issue19-school-source-status-snapshot-public-ledger.csv"
NEXT20_LEDGER = WORKING / "issue19-school-source-next20-official-probe-public-ledger.csv"
LIVE_LEDGER = WORKING / "issue19-school-source-live-20260629-ledger.csv"
C4C6_REUSE = WORKING / "issue19-c4-c6-retained-source-reuse-public-ledger.csv"
C4C6_DIFF = WORKING / "issue19-c4-c6-structured-candidate-diff-public-ledger.csv"
C4C6_ATTEMPTS = WORKING / "issue19-c4-c6-school-source-acquisition-attempts-public-ledger.csv"

OUTPUT = WORKING / "issue19-school-source-latest-reconciliation-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-latest-reconciliation-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_latest_reconciliation_public_ledger"
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
    "高校源最新对齐ID",
    "来源高校官网辅证自动执行批次",
    "来源高校官网辅证状态快照",
    "来源next20官网源探测账本",
    "来源live补源账本",
    "来源C4C6复用审计账本",
    "来源C4C6结构化候选diff账本",
    "来源C4C6补源尝试账本",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "原自动执行批次ID",
    "高校官网辅证状态快照ID",
    "执行批次序号",
    "院校代码",
    "院校名称公开",
    "原自动执行泳道",
    "原官网辅证自动动作",
    "原官网来源状态",
    "原最新自动探针状态",
    "原结构化输出状态桶",
    "原候选diff状态桶",
    "原补源状态桶",
    "原涉及招生明细数",
    "原涉及专业组数",
    "next20任务数",
    "next20结构化湖北物理行数合计",
    "next20结构化计划数合计",
    "next20官网源类型集合",
    "next20当前自动判断集合",
    "live补源记录数",
    "live结构化输出记录数",
    "live湖北物理计划状态桶",
    "C4C6复用包数",
    "C4C6已有标准化官网证据行数",
    "C4C6复用可生成候选diff明细数",
    "C4C6结构化diff包数",
    "C4C6综合结构化官网证据行数",
    "C4C6可生成候选diff明细数",
    "C4C6计划数一致候选数",
    "C4C6官网可补OCR计划数候选数",
    "C4C6计划数冲突候选数",
    "C4C6补源尝试记录数",
    "C4C6最新自动探针状态集合",
    "最新证据来源族",
    "最新公开证据集合SHA16",
    "最新高校侧证据层级",
    "相对原自动账本推进状态",
    "最新自动建议动作",
    "人工最小核验动作",
    "仍需补源或解析原因",
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


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def to_int(value):
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def sha16(*parts):
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]


def compact_values(values, limit=6):
    clean = []
    for value in values:
        value = str(value or "").strip()
        if value and value not in clean:
            clean.append(value)
    clean.sort()
    if len(clean) > limit:
        rest = len(clean) - limit
        clean = clean[:limit] + [f"另有{rest}项"]
    return "；".join(clean)


def live_status_bucket(status):
    status = str(status or "")
    if "官网PDF抽取湖北物理" in status or "结构化" in status:
        return "live已取得湖北物理结构化线索"
    if "H5入口" in status or "官方入口" in status:
        return "live仅取得官方入口线索"
    if "章程" in status:
        return "live仅取得章程或规则线索"
    if "2025" in status or "2024" in status:
        return "live仅见历史招考信息"
    if "吉林省计划" in status or "外省计划" in status:
        return "live仅见外省计划不可迁移"
    if "未取得" in status:
        return "live未取得湖北物理计划"
    if status:
        return "live有边界记录待人工判定"
    return ""


def evidence_family(next_rows, live_rows, reuse_rows, diff_rows, attempt_rows):
    families = []
    if next_rows:
        families.append("next20")
    if live_rows:
        families.append("live")
    if reuse_rows:
        families.append("c4c6_reuse")
    if diff_rows:
        families.append("c4c6_diff")
    if attempt_rows:
        families.append("c4c6_attempt")
    return "；".join(families) if families else "none"


def evidence_sha16(next_rows, live_rows, reuse_rows, diff_rows, attempt_rows):
    parts = []
    for row in next_rows:
        parts.extend(
            [
                row.get("next20官网源探测ID", ""),
                row.get("本地公开来源文件集合SHA256", ""),
                row.get("结构化湖北物理行数", ""),
                row.get("结构化计划数合计", ""),
            ]
        )
    for row in live_rows:
        parts.extend(
            [
                row.get("抓取日期", ""),
                row.get("院校代码", ""),
                live_status_bucket(row.get("湖北物理计划状态")),
                "live_structured" if str(row.get("结构化输出", "")).strip() else "live_unstructured",
            ]
        )
    for row in reuse_rows:
        parts.extend(
            [
                row.get("C4C6官网源复用审计ID", ""),
                row.get("已有标准化官网证据行数", ""),
                row.get("已有标准化官网来源文件数", ""),
                row.get("本地未公开明细CSV_SHA256", ""),
            ]
        )
    for row in diff_rows:
        parts.extend(
            [
                row.get("C4C6结构化候选diff公开ID", ""),
                row.get("综合结构化官网证据行数", ""),
                row.get("可生成候选diff明细数", ""),
                row.get("本地未公开明细CSV_SHA256", ""),
            ]
        )
    for row in attempt_rows:
        parts.extend(
            [
                row.get("C4C6高校官网补源尝试ID", ""),
                row.get("最新自动探针状态", ""),
                row.get("当前无结构化官网源明细数", ""),
            ]
        )
    return sha16(*parts) if any(parts) else ""


def index_by_code(rows, code_field="院校代码"):
    out = defaultdict(list)
    for row in rows:
        code = row.get(code_field, "").strip()
        if code:
            out[code].append(row)
    return out


def latest_level(next_rows, live_rows, reuse_rows, diff_rows, attempt_rows):
    next20_physics = sum(to_int(r.get("结构化湖北物理行数")) for r in next_rows)
    live_structured = sum(1 for r in live_rows if str(r.get("结构化输出", "")).strip())
    diff_candidate = sum(to_int(r.get("可生成候选diff明细数")) for r in diff_rows)
    diff_structured = sum(to_int(r.get("综合结构化官网证据行数")) for r in diff_rows)
    reuse_candidate = sum(to_int(r.get("已有源可生成候选diff明细数")) for r in reuse_rows)
    reuse_evidence = sum(to_int(r.get("已有标准化官网证据行数")) for r in reuse_rows)

    if next20_physics > 0 or live_structured > 0 or diff_candidate > 0:
        return "L3-已有湖北物理结构化或候选diff线索"
    if diff_structured > 0 or reuse_candidate > 0 or reuse_evidence > 0:
        return "L2-已有结构化高校源但仍需匹配或回页"
    if next_rows or live_rows or attempt_rows:
        return "L1-有入口或探针记录但未取得湖北物理结构化明细"
    return "L0-暂无可复用高校侧计划源"


def progress_state(auto_row, level):
    lane = auto_row.get("自动执行泳道", "")
    source_state = auto_row.get("官网来源状态", "")
    if lane == "A4-继续搜索高校计划网源":
        if level.startswith("L3"):
            return "P3-A4已推进到结构化或diff线索"
        if level.startswith("L2"):
            return "P2-A4已推进到结构化源待匹配"
        return "P0-A4仍需继续补源"
    if lane == "A3-补结构化或解析公开来源":
        if level.startswith("L3"):
            return "P3-A3已有diff或湖北物理结构化线索"
        if level.startswith("L2"):
            return "P1-A3仍需解析或匹配"
        return "P0-A3公开来源不足仍需补源"
    if "has_reusable" in source_state and (level.startswith("L2") or level.startswith("L3")):
        return "P2-原任务已有高校侧来源继续回页"
    return "P1-保持原执行泳道"


def next_action(level, progress, auto_row):
    if progress == "P0-A4仍需继续补源":
        return "继续查学校招生网、公开API、XLSX、PDF或图片计划源；不能迁移外省计划。"
    if progress == "P0-A3公开来源不足仍需补源":
        return "先补可读公开来源或接口，再判断能否生成湖北物理结构化线索。"
    if level.startswith("L3"):
        return "把已有高校侧结构化或diff线索用于核页提示；仍必须回第19期PDF原页和湖北官方侧。"
    if level.startswith("L2"):
        return "补专业名匹配、湖北物理行过滤或附件解析；再生成差异线索并回页核验。"
    return auto_row.get("建议下一步动作") or "按原自动执行泳道继续推进。"


def manual_action(level, progress):
    if level.startswith("L3"):
        return "人工最小核验集中在计划数冲突、OCR补缺、专业组边界和湖北官方侧。"
    if level.startswith("L2"):
        return "人工抽检结构化来源是否为2026湖北物理普通本科，再决定是否升级回页。"
    if progress.startswith("P0-A4"):
        return "人工必要时补找学校招生网计划入口或附件。"
    return "人工按原账本要求核PDF原页、湖北官方侧和必要高校官网辅证。"


def missing_reason(level, next_rows, live_rows, diff_rows, attempt_rows):
    if level.startswith("L3"):
        return "已有高校侧线索，缺的是PDF原页、湖北官方侧和人工确认闭环。"
    if level.startswith("L2"):
        return "已有结构化或标准化高校源，但仍缺湖北物理行过滤、专业名匹配或候选diff。"
    reasons = []
    for row in live_rows:
        status = live_status_bucket(row.get("湖北物理计划状态", ""))
        if status:
            reasons.append(status)
    for row in next_rows:
        status = live_status_bucket(row.get("已有live湖北物理计划状态", ""))
        if status:
            reasons.append(status)
    for row in attempt_rows:
        status = row.get("最新自动探针状态", "")
        if status:
            reasons.append(status)
    return compact_values(reasons) or "暂无公开结构化湖北物理计划源线索。"


def build_rows():
    auto_rows = read_csv(AUTO_LEDGER)
    status_by_id = {row.get("高校官网辅证状态快照ID"): row for row in read_csv(STATUS_SNAPSHOT)}
    next_by_code = index_by_code(read_csv(NEXT20_LEDGER))
    live_by_code = index_by_code(read_csv(LIVE_LEDGER))
    reuse_by_code = index_by_code(read_csv(C4C6_REUSE))
    diff_by_code = index_by_code(read_csv(C4C6_DIFF))
    attempt_by_code = index_by_code(read_csv(C4C6_ATTEMPTS))

    rows = []
    for index, auto in enumerate(auto_rows, start=1):
        code = auto.get("院校代码", "").strip()
        next_rows = next_by_code.get(code, [])
        live_rows = live_by_code.get(code, [])
        reuse_rows = reuse_by_code.get(code, [])
        diff_rows = diff_by_code.get(code, [])
        attempt_rows = attempt_by_code.get(code, [])

        level = latest_level(next_rows, live_rows, reuse_rows, diff_rows, attempt_rows)
        progress = progress_state(auto, level)
        status_id = auto.get("高校官网辅证状态快照ID", "")

        row = {
            "高校源最新对齐ID": f"SOURCESYNC-{sha16(code, auto.get('高校官网辅证自动执行批次ID'), index)}",
            "来源高校官网辅证自动执行批次": str(AUTO_LEDGER.relative_to(ROOT)),
            "来源高校官网辅证状态快照": str(STATUS_SNAPSHOT.relative_to(ROOT)),
            "来源next20官网源探测账本": str(NEXT20_LEDGER.relative_to(ROOT)),
            "来源live补源账本": str(LIVE_LEDGER.relative_to(ROOT)),
            "来源C4C6复用审计账本": str(C4C6_REUSE.relative_to(ROOT)),
            "来源C4C6结构化候选diff账本": str(C4C6_DIFF.relative_to(ROOT)),
            "来源C4C6补源尝试账本": str(C4C6_ATTEMPTS.relative_to(ROOT)),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校×高校侧辅证自动执行任务×最新公开证据对齐",
            "任务粒度": "公开任务级状态；不保存逐专业字段记录、人工字段记录或私有材料",
            "原自动执行批次ID": auto.get("高校官网辅证自动执行批次ID", ""),
            "高校官网辅证状态快照ID": status_id,
            "执行批次序号": auto.get("执行批次序号", ""),
            "院校代码": code,
            "院校名称公开": auto.get("院校名称公开", ""),
            "原自动执行泳道": auto.get("自动执行泳道", ""),
            "原官网辅证自动动作": auto.get("官网辅证自动动作", ""),
            "原官网来源状态": auto.get("官网来源状态", ""),
            "原最新自动探针状态": auto.get("最新自动探针状态", ""),
            "原结构化输出状态桶": auto.get("结构化输出状态桶", ""),
            "原候选diff状态桶": auto.get("候选diff状态桶", ""),
            "原补源状态桶": auto.get("补源状态桶", ""),
            "原涉及招生明细数": auto.get("涉及招生明细数", "0"),
            "原涉及专业组数": auto.get("涉及专业组数", "0"),
            "next20任务数": len(next_rows),
            "next20结构化湖北物理行数合计": sum(to_int(r.get("结构化湖北物理行数")) for r in next_rows),
            "next20结构化计划数合计": sum(to_int(r.get("结构化计划数合计")) for r in next_rows),
            "next20官网源类型集合": compact_values(r.get("官网源类型") for r in next_rows),
            "next20当前自动判断集合": compact_values(r.get("当前自动判断") for r in next_rows),
            "live补源记录数": len(live_rows),
            "live结构化输出记录数": sum(1 for r in live_rows if str(r.get("结构化输出", "")).strip()),
            "live湖北物理计划状态桶": compact_values((live_status_bucket(r.get("湖北物理计划状态")) for r in live_rows), limit=3),
            "C4C6复用包数": len(reuse_rows),
            "C4C6已有标准化官网证据行数": sum(to_int(r.get("已有标准化官网证据行数")) for r in reuse_rows),
            "C4C6复用可生成候选diff明细数": sum(to_int(r.get("已有源可生成候选diff明细数")) for r in reuse_rows),
            "C4C6结构化diff包数": len(diff_rows),
            "C4C6综合结构化官网证据行数": sum(to_int(r.get("综合结构化官网证据行数")) for r in diff_rows),
            "C4C6可生成候选diff明细数": sum(to_int(r.get("可生成候选diff明细数")) for r in diff_rows),
            "C4C6计划数一致候选数": sum(to_int(r.get("计划数一致候选数")) for r in diff_rows),
            "C4C6官网可补OCR计划数候选数": sum(to_int(r.get("官网可补OCR计划数候选数")) for r in diff_rows),
            "C4C6计划数冲突候选数": sum(to_int(r.get("计划数冲突候选数")) for r in diff_rows),
            "C4C6补源尝试记录数": len(attempt_rows),
            "C4C6最新自动探针状态集合": compact_values(r.get("最新自动探针状态") for r in attempt_rows),
            "最新证据来源族": evidence_family(next_rows, live_rows, reuse_rows, diff_rows, attempt_rows),
            "最新公开证据集合SHA16": evidence_sha16(next_rows, live_rows, reuse_rows, diff_rows, attempt_rows),
            "最新高校侧证据层级": level,
            "相对原自动账本推进状态": progress,
            "最新自动建议动作": next_action(level, progress, auto),
            "人工最小核验动作": manual_action(level, progress),
            "仍需补源或解析原因": missing_reason(level, next_rows, live_rows, diff_rows, attempt_rows),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "公开安全策略": "只保存公开任务状态、计数和证据层级，不保存逐专业官网字段记录、人工字段记录、识别正文、登录态、截图或私有路径。",
        }
        for field in FALSE_FIELDS:
            row[field] = "false"
        if status_id and status_id not in status_by_id:
            raise ValueError(f"missing status snapshot row: {status_id}")
        rows.append(row)

    return rows


def validate_public_outputs(rows, summary):
    if len(rows) != 80:
        raise AssertionError(f"expected 80 rows, got {len(rows)}")
    if len({row["高校源最新对齐ID"] for row in rows}) != len(rows):
        raise AssertionError("duplicate reconciliation id")
    if any(row[field] != "false" for row in rows for field in FALSE_FIELDS):
        raise AssertionError("non-final gate opened")
    text = OUTPUT.read_text(encoding="utf-8-sig") + SUMMARY_OUTPUT.read_text(encoding="utf-8")
    for token in FORBIDDEN_PUBLIC_TOKENS:
        if token in text:
            raise AssertionError(f"forbidden public token found: {token}")
    if summary["field_writeback_ready_count"] != 0 or summary["final_available_count"] != 0:
        raise AssertionError("summary gate opened")


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows)
    next_source_rows = read_csv(NEXT20_LEDGER)
    live_source_rows = read_csv(LIVE_LEDGER)
    diff_source_rows = read_csv(C4C6_DIFF)

    latest_counts = Counter(row["最新高校侧证据层级"] for row in rows)
    progress_counts = Counter(row["相对原自动账本推进状态"] for row in rows)
    auto_lane_counts = Counter(row["原自动执行泳道"] for row in rows)
    source_status_counts = Counter(row["原官网来源状态"] for row in rows)

    summary = {
        "status": "issue19_school_source_latest_reconciliation_ready_not_final",
        "generated_by": Path(__file__).name,
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_csv": str(OUTPUT.relative_to(ROOT)),
        "row_count": len(rows),
        "unique_school_count": len({row["院校代码"] for row in rows}),
        "auto_lane_counts": dict(auto_lane_counts),
        "source_status_counts": dict(source_status_counts),
        "latest_evidence_level_counts": dict(latest_counts),
        "progress_against_auto_counts": dict(progress_counts),
        "source_next20_row_count": len(next_source_rows),
        "source_next20_structured_hubei_physics_row_count": sum(to_int(row.get("结构化湖北物理行数")) for row in next_source_rows),
        "source_live_record_count": len(live_source_rows),
        "source_live_structured_record_count": sum(1 for row in live_source_rows if str(row.get("结构化输出", "")).strip()),
        "source_c4c6_diff_row_count": len(diff_source_rows),
        "source_c4c6_candidate_diff_detail_count": sum(to_int(row.get("可生成候选diff明细数")) for row in diff_source_rows),
        "row_linked_next20_task_count": sum(to_int(row["next20任务数"]) for row in rows),
        "row_linked_next20_structured_hubei_physics_row_count": sum(to_int(row["next20结构化湖北物理行数合计"]) for row in rows),
        "row_linked_live_source_record_count": sum(to_int(row["live补源记录数"]) for row in rows),
        "row_linked_live_structured_record_count": sum(to_int(row["live结构化输出记录数"]) for row in rows),
        "row_linked_c4c6_diff_package_count": sum(to_int(row["C4C6结构化diff包数"]) for row in rows),
        "row_linked_c4c6_candidate_diff_detail_count": sum(to_int(row["C4C6可生成候选diff明细数"]) for row in rows),
        "a4_rows_with_latest_structured_or_diff": sum(
            1
            for row in rows
            if row["原自动执行泳道"] == "A4-继续搜索高校计划网源"
            and row["最新高校侧证据层级"].startswith("L3")
        ),
        "a4_rows_still_need_source": sum(
            1
            for row in rows
            if row["原自动执行泳道"] == "A4-继续搜索高校计划网源"
            and row["最新高校侧证据层级"] in {"L0-暂无可复用高校侧计划源", "L1-有入口或探针记录但未取得湖北物理结构化明细"}
        ),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该表只做高校侧公开证据状态对齐，不能替代第19期PDF原页、湖北官方系统或省招办计划，不确认字段事实。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    validate_public_outputs(rows, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
