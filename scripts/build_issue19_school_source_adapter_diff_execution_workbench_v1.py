#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

INGESTION = WORKING / "issue19-school-source-structured-ingestion-candidates-public-ledger.csv"
PROGRESS = WORKING / "issue19-school-source-progress-board-public-ledger.csv"
LATEST = WORKING / "issue19-school-source-latest-reconciliation-public-ledger.csv"
AUTO_BATCHES = WORKING / "issue19-school-source-auto-execution-batches-public-ledger.csv"

OUTPUT = WORKING / "issue19-school-source-adapter-diff-execution-workbench-v1-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-adapter-diff-execution-workbench-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_adapter_diff_execution_workbench_v1"
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
    "高校源AdapterDiff执行ID",
    "来源高校源结构化接入候选账本",
    "来源高校源进度看板",
    "来源高校源最新对齐账本",
    "来源高校官网辅证自动执行批次",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行序号",
    "院校代码",
    "学校键SHA16",
    "高校源结构化接入候选ID",
    "接入批次",
    "来源文件类型",
    "来源族",
    "公开证据集合SHA16",
    "公开URL线索数量",
    "结构化适配器状态",
    "Adapter执行阶段",
    "Parser状态桶",
    "Normalized桥接状态",
    "NormalizedSchema版本",
    "匹配规则状态",
    "Diff执行桶",
    "Diff优先级",
    "关联进度看板任务数",
    "关联最新对齐任务数",
    "关联自动批次数",
    "关联进度看板ID集合SHA16",
    "关联最新对齐ID集合SHA16",
    "关联自动批次ID集合SHA16",
    "候选涉及招生明细数",
    "候选涉及专业组数最大值",
    "进度看板涉及招生明细数合计",
    "进度看板涉及专业组数合计",
    "Next20结构化湖北物理行数合计",
    "C4C6综合结构化官网证据行数",
    "C4C6可生成候选diff明细数",
    "候选diff线索数",
    "计划数冲突线索数",
    "官网补缺线索数",
    "官网未匹配线索数",
    "需补结构化明细数",
    "需继续补源明细数",
    "章程规则是否另表承接",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "下一步自动动作",
    "最小人工核验动作",
    "完成条件",
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
    "院校专业组代码",
    "字段值",
    "字段读数",
    "人工读数",
    "OCR正文",
    "OCR行文本",
    "截图路径",
    "复核备注",
    "一审记录",
    "二审记录",
    "复核结论",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def clean(value):
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: clean(row.get(field, "")) for field in fields} for row in rows])


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path):
    return str(path.relative_to(ROOT))


def stable_id(prefix, parts):
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def stable_set_sha(values):
    normalized = sorted({clean(value) for value in values if clean(value)})
    if not normalized:
        return ""
    return hashlib.sha256("\n".join(normalized).encode("utf-8")).hexdigest()[:16]


def as_int(value):
    try:
        return int(float(clean(value) or "0"))
    except ValueError:
        return 0


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def index_by(rows, field):
    indexed = defaultdict(list)
    for row in rows:
        key = clean(row.get(field))
        if key:
            indexed[key].append(row)
    return indexed


def adapter_stage(adapter_status):
    status = clean(adapter_status)
    if status.startswith("new_"):
        return "A0-新建adapter或bridge"
    if "pdf_csv" in status:
        return "A2-复用PDF_CSV并补Parser规则"
    if "xlsx" in status:
        return "A3-复用XLSX并补列规则"
    return "A1-复用JSON并补schema或匹配规则"


def parser_bucket(source_type):
    text = clean(source_type)
    if text == "API/JSON；章程HTML":
        return "P1-JSON计划源与章程规则分流"
    if text == "API/JSON":
        return "P0-JSON结构可解析待schema统一"
    if text == "PDF抽取CSV":
        return "P2-PDF抽取CSV待网格抽检"
    if text == "XLSX":
        return "P3-XLSX待省份科类批次列校验"
    return "P9-来源类型待人工判定"


def normalized_state(adapter_status):
    return (
        "N0-需新建normalized桥接"
        if clean(adapter_status).startswith("new_")
        else "N1-已有结构化线索需统一normalized输出"
    )


def diff_bucket(priority):
    text = clean(priority)
    if text.startswith("D0"):
        return "D0-优先生成冲突或高明细diff"
    if text.startswith("D1"):
        return "D1-生成补缺或常规diff"
    if text.startswith("D2"):
        return "D2-先做来源边界防串校验再diff"
    return "D9-待判定diff动作"


def next_auto_action(source_type, adapter_status):
    source = clean(source_type)
    adapter = clean(adapter_status)
    if source == "API/JSON；章程HTML":
        return "JSON计划源先接normalized；章程规则另入限制规则侧账。"
    if source == "API/JSON" and adapter.startswith("new_"):
        return "新建JSON bridge，输出normalized行后生成候选diff。"
    if source == "API/JSON":
        return "复用JSON解析，补schema或匹配规则后生成候选diff。"
    if source == "PDF抽取CSV" and adapter.startswith("new_"):
        return "先做来源边界防串校验，再接PDF_CSV normalized行。"
    if source == "PDF抽取CSV":
        return "复核PDF_CSV网格和字段映射，再生成候选diff。"
    if source == "XLSX":
        return "校验省份、科类、批次列后生成候选diff。"
    return "先人工判定来源类型，再决定adapter。"


def counter_dict(rows, field):
    return dict(sorted(Counter(clean(row.get(field)) for row in rows if clean(row.get(field))).items()))


def build_rows():
    ingestion_rows = read_csv(INGESTION)
    progress_rows = read_csv(PROGRESS)
    latest_rows = read_csv(LATEST)
    auto_rows = read_csv(AUTO_BATCHES)

    progress_by_code = index_by(progress_rows, "院校代码")
    latest_by_code = index_by(latest_rows, "院校代码")
    auto_by_code = index_by(auto_rows, "院校代码")

    rows = []
    for source in sorted(ingestion_rows, key=lambda row: as_int(row.get("接入优先序"))):
        code = clean(source.get("院校代码"))
        progress = progress_by_code.get(code, [])
        latest = latest_by_code.get(code, [])
        auto = auto_by_code.get(code, [])
        source_type = clean(source.get("来源文件类型"))
        adapter_status = clean(source.get("结构化适配器状态"))
        diff_priority = clean(source.get("候选diff优先级"))

        candidate_diff_count = sum(as_int(row.get("C4C6可生成候选diff明细数")) for row in progress)
        conflict_count = sum(
            as_int(row.get("C4C6计划数冲突候选数")) + as_int(row.get("计划数冲突行数"))
            for row in progress
        )
        fill_count = sum(
            as_int(row.get("C4C6官网可补OCR计划数候选数")) + as_int(row.get("官网补缺候选行数"))
            for row in progress
        )
        row = {
            "高校源AdapterDiff执行ID": stable_id("SSAD", [SOURCE_PDF_SHA256, code, source.get("高校源结构化接入候选ID")]),
            "来源高校源结构化接入候选账本": source_path(INGESTION),
            "来源高校源进度看板": source_path(PROGRESS),
            "来源高校源最新对齐账本": source_path(LATEST),
            "来源高校官网辅证自动执行批次": source_path(AUTO_BATCHES),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校官网结构化源AdapterDiff执行候选",
            "任务粒度": "院校代码×结构化源类型×AdapterDiff动作",
            **false_gate_values(),
            "执行序号": as_int(source.get("接入优先序")),
            "院校代码": code,
            "学校键SHA16": clean(source.get("学校键SHA16")),
            "高校源结构化接入候选ID": clean(source.get("高校源结构化接入候选ID")),
            "接入批次": clean(source.get("接入批次")),
            "来源文件类型": source_type,
            "来源族": clean(source.get("来源族")),
            "公开证据集合SHA16": clean(source.get("本地公开证据文件集合SHA16")),
            "公开URL线索数量": as_int(source.get("公开URL线索数量")),
            "结构化适配器状态": adapter_status,
            "Adapter执行阶段": adapter_stage(adapter_status),
            "Parser状态桶": parser_bucket(source_type),
            "Normalized桥接状态": normalized_state(adapter_status),
            "NormalizedSchema版本": "school_source_normalized_v1_pending",
            "匹配规则状态": clean(source.get("匹配规则状态")),
            "Diff执行桶": diff_bucket(diff_priority),
            "Diff优先级": diff_priority,
            "关联进度看板任务数": len(progress),
            "关联最新对齐任务数": len(latest),
            "关联自动批次数": len(auto),
            "关联进度看板ID集合SHA16": stable_set_sha(row.get("高校源进度看板ID") for row in progress),
            "关联最新对齐ID集合SHA16": stable_set_sha(row.get("高校源最新对齐ID") for row in latest),
            "关联自动批次ID集合SHA16": stable_set_sha(row.get("高校官网辅证自动执行批次ID") for row in auto),
            "候选涉及招生明细数": as_int(source.get("涉及招生明细数合计")),
            "候选涉及专业组数最大值": as_int(source.get("涉及专业组数最大值")),
            "进度看板涉及招生明细数合计": sum(as_int(row.get("涉及招生明细数")) for row in progress),
            "进度看板涉及专业组数合计": sum(as_int(row.get("涉及专业组数")) for row in progress),
            "Next20结构化湖北物理行数合计": sum(as_int(row.get("next20结构化湖北物理行数合计")) for row in progress),
            "C4C6综合结构化官网证据行数": sum(as_int(row.get("C4C6综合结构化官网证据行数")) for row in progress),
            "C4C6可生成候选diff明细数": candidate_diff_count,
            "候选diff线索数": candidate_diff_count,
            "计划数冲突线索数": conflict_count,
            "官网补缺线索数": fill_count,
            "官网未匹配线索数": sum(as_int(row.get("官网未匹配行数")) for row in progress),
            "需补结构化明细数": sum(as_int(row.get("需补结构化明细数")) for row in progress),
            "需继续补源明细数": sum(as_int(row.get("需继续补源明细数")) for row in progress),
            "章程规则是否另表承接": "true" if "章程" in source_type else "false",
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "下一步自动动作": next_auto_action(source_type, adapter_status),
            "最小人工核验动作": "adapter输出只作提示；字段进入候选前仍需回看PDF原页并核湖北官方侧。",
            "完成条件": "normalized行、候选diff、PDF原页、湖北官方侧和必要人工复核全部闭环后，才可进入私有写回评审。",
            "公开安全策略": "not_final；adapter_diff_execution_only；no_school_names；no_major_names；no_field_values；no_evidence_paths；no_private_paths；no_login_state；no_recommendation",
        }
        rows.append(row)

    rows.sort(key=lambda row: as_int(row["执行序号"]))
    return rows, ingestion_rows, progress_rows, latest_rows, auto_rows


def build_summary(rows, ingestion_rows, progress_rows, latest_rows, auto_rows):
    return {
        "status": "issue19_school_source_adapter_diff_execution_workbench_v1_not_final",
        "generated_by": "build_issue19_school_source_adapter_diff_execution_workbench_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_structured_ingestion": source_path(INGESTION),
        "source_progress_board": source_path(PROGRESS),
        "source_latest_reconciliation": source_path(LATEST),
        "source_auto_batches": source_path(AUTO_BATCHES),
        "output_table": source_path(OUTPUT),
        "row_count": len(rows),
        "unique_school_count": len({row["院校代码"] for row in rows}),
        "source_ingestion_row_count": len(ingestion_rows),
        "source_progress_row_count": len(progress_rows),
        "source_latest_row_count": len(latest_rows),
        "source_auto_row_count": len(auto_rows),
        "source_type_counts": counter_dict(rows, "来源文件类型"),
        "adapter_stage_counts": counter_dict(rows, "Adapter执行阶段"),
        "parser_bucket_counts": counter_dict(rows, "Parser状态桶"),
        "normalized_state_counts": counter_dict(rows, "Normalized桥接状态"),
        "diff_bucket_counts": counter_dict(rows, "Diff执行桶"),
        "batch_counts": counter_dict(rows, "接入批次"),
        "rule_sidecar_count": sum(1 for row in rows if row["章程规则是否另表承接"] == "true"),
        "attached_progress_task_count": sum(as_int(row["关联进度看板任务数"]) for row in rows),
        "attached_latest_task_count": sum(as_int(row["关联最新对齐任务数"]) for row in rows),
        "attached_auto_batch_count": sum(as_int(row["关联自动批次数"]) for row in rows),
        "candidate_major_detail_count": sum(as_int(row["候选涉及招生明细数"]) for row in rows),
        "progress_major_detail_count": sum(as_int(row["进度看板涉及招生明细数合计"]) for row in rows),
        "candidate_diff_hint_count": sum(as_int(row["候选diff线索数"]) for row in rows),
        "conflict_hint_count": sum(as_int(row["计划数冲突线索数"]) for row in rows),
        "fill_hint_count": sum(as_int(row["官网补缺线索数"]) for row in rows),
        "unmatched_hint_count": sum(as_int(row["官网未匹配线索数"]) for row in rows),
        "need_structure_count": sum(as_int(row["需补结构化明细数"]) for row in rows),
        "need_source_count": sum(as_int(row["需继续补源明细数"]) for row in rows),
        "pdf_pending_count": len(rows),
        "hubei_official_pending_count": len(rows),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "本表只安排高校公开源adapter、parser、normalized bridge和候选diff执行，不保存学校名、专业名、字段明细或证据路径，不替代第19期PDF原页和湖北官方计划。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"adapter diff workbench contains forbidden public tokens: {hits[:10]}")


def main():
    rows, ingestion_rows, progress_rows, latest_rows, auto_rows = build_rows()
    summary = build_summary(rows, ingestion_rows, progress_rows, latest_rows, auto_rows)
    assert_public_safe(rows, summary)
    write_csv(OUTPUT, rows, FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")


if __name__ == "__main__":
    main()
