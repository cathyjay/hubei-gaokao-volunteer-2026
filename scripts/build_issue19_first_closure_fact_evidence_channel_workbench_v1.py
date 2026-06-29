#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FACT_RESOLUTION = WORKING / "issue19-first-closure-fact-resolution-gate-v1-public-ledger.csv"
RESOLUTION_OVERLAY = WORKING / "issue19-first-closure-resolution-execution-overlay-v1.csv"
VERIFICATION_RESULT = WORKING / "issue19-first-closure-verification-result-public-ledger.csv"
FIELD_STATUS = WORKING / "issue19-first-closure-field-verification-status-public-ledger.csv"
SCHOOL_PROGRESS = WORKING / "issue19-school-source-progress-board-public-ledger.csv"

OUTPUT = WORKING / "issue19-first-closure-fact-evidence-channel-workbench-v1-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-fact-evidence-channel-workbench-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_fact_evidence_channel_workbench_v1"

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

WORKBENCH_FIELDS = [
    "事实证据通道工作台ID",
    "来源事实准出门禁账本",
    "来源准出执行叠加表",
    "来源第一闭环核验结果看板",
    "来源第一闭环字段级公开状态",
    "来源高校官网辅证进度看板",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "事实工作台序号",
    "来源准出序号",
    "来源执行顺序",
    "页码版面键",
    "来源页码",
    "版面列",
    "准出闭环波次",
    "执行泳道",
    "核验动作层级",
    "第一闭环页列优先级",
    "事实核验动作组",
    "事实通道优先级",
    "事实准出门禁ID",
    "第一闭环事实范围缺口公开账本ID",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环页列包ID",
    "第一闭环核验结果ID",
    "第一闭环字段核验状态ID",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "事实域",
    "事实类型",
    "事实粒度",
    "字段类别",
    "字段事实状态",
    "字段核验优先级",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "PDF原页通道状态",
    "OCR提示通道状态",
    "机器坐标通道状态",
    "高校官网辅证通道状态",
    "湖北官方侧通道状态",
    "冲突处理通道状态",
    "双人复核通道状态",
    "三方闭环通道状态",
    "字段写回评审状态",
    "专业名归属通道状态",
    "专业组边界通道状态",
    "同校高校源进度任务数",
    "同校高校源最高证据层级分布",
    "同校高校源下一批优先级分布",
    "同校高校源留存状态分布",
    "同校高校源候选diff数",
    "同校高校源冲突候选数",
    "同校高校源补缺候选数",
    "是否仍需PDF原页",
    "是否仍需湖北官方侧",
    "是否仍需高校辅证",
    "是否仍需冲突处理",
    "是否仍需双人复核",
    "是否仍需三方闭环",
    "是否仍需专业名归属",
    "是否仍需专业组边界",
    "是否可进入私有写回评审",
    "完成证据要求",
    "当前阻断原因",
    "下一步最小核验动作",
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
    "专业组代码",
    "院校专业组代码",
    "字段读数",
    "人工读数",
    "字段OCR候选",
    "字段人工确认",
    "字段候选值集合",
    "候选计划数",
    "候选学费",
    "候选选科",
    "机器候选字段值",
    "机器候选值集合",
    "专业名称及备注",
    "OCR正文",
    "OCR行文本",
    "截图路径",
    "复核备注",
    "一审记录",
    "二审记录",
    "复核结论",
    "已确认",
    "已核准",
    "最终候选",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]

ACTION_RANK = {
    "A0-W0B0冲突事实先核": 0,
    "A1-专业名归属事实先核": 1,
    "A2-专业组边界事实随页先核": 2,
    "A3-双人复核事实先核": 3,
    "A4-无稳定OCR人工看图": 4,
    "A5-机器坐标辅助核页": 5,
    "A6-高校辅证提示回接": 6,
    "A7-常规PDF湖北官方闭环": 7,
}


def clean(value):
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def public_text(value):
    text = clean(value)
    replacements = {
        "字段读数": "字段明细值",
        "人工读数": "人工记录值",
        "OCR正文": "OCR文本",
        "截图路径": "图像路径",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: public_text(row.get(field, "")) for field in fields} for row in rows])


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path):
    return str(path.relative_to(ROOT))


def stable_id(prefix, parts):
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(float(clean(value) or "0"))
    except ValueError:
        return 0


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def index_unique(rows, key):
    indexed = {}
    for row in rows:
        value = clean(row.get(key))
        if not value:
            continue
        if value in indexed:
            raise SystemExit(f"duplicate {key}: {value}")
        indexed[value] = row
    return indexed


def index_field_status(rows):
    indexed = {}
    for row in rows:
        task_id = clean(row.get("稳定基座第一闭环明细任务ID"))
        field = clean(row.get("字段名"))
        if task_id and field:
            key = (task_id, field)
            if key in indexed:
                raise SystemExit(f"duplicate field status: {key}")
            indexed[key] = row
    return indexed


def group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[clean(row.get(key))].append(row)
    return grouped


def counter_text(counter):
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()) if key)


def sum_int(rows, field):
    return sum(as_int(row.get(field)) for row in rows)


def school_summary(rows):
    if not rows:
        return {
            "count": 0,
            "level": "",
            "priority": "",
            "retention": "",
            "candidate_diff": 0,
            "conflict": 0,
            "fill": 0,
        }
    return {
        "count": len(rows),
        "level": counter_text(Counter(clean(row.get("最新高校侧证据层级")) for row in rows)),
        "priority": counter_text(Counter(clean(row.get("下一批推进优先级")) for row in rows)),
        "retention": counter_text(Counter(clean(row.get("来源留存状态")) for row in rows)),
        "candidate_diff": sum_int(rows, "C4C6可生成候选diff明细数"),
        "conflict": sum_int(rows, "C4C6计划数冲突候选数") + sum_int(rows, "计划数冲突行数"),
        "fill": sum_int(rows, "C4C6官网可补OCR计划数候选数") + sum_int(rows, "官网补缺候选行数"),
    }


def first_nonempty(*values, default=""):
    for value in values:
        text = clean(value)
        if text:
            return text
    return default


def fact_action_group(fact, result, field_status):
    domain = clean(fact.get("事实域"))
    status = clean(fact.get("事实准出状态"))
    if status in {"blocked_w0_b0_core_pdf_hubei", "blocked_b0_companion_pdf_hubei"} or clean(fact.get("是否仍需冲突处理")) == "true":
        return "A0-W0B0冲突事实先核"
    if domain == "专业名归属":
        return "A1-专业名归属事实先核"
    if domain == "专业组边界":
        return "A2-专业组边界事实随页先核"
    if clean(fact.get("是否仍需双人复核")) == "true" or clean(result.get("是否需要双人复核")) == "true":
        return "A3-双人复核事实先核"
    if clean(result.get("是否需要人工直接看图")) == "true" or "无稳定" in clean(result.get("OCR提示状态")):
        return "A4-无稳定OCR人工看图"
    if clean(result.get("是否有机器坐标提示")) == "true":
        return "A5-机器坐标辅助核页"
    if clean(fact.get("是否仍需高校辅证")) == "true" or clean(result.get("是否有高校辅证线索")) == "true":
        return "A6-高校辅证提示回接"
    if clean(field_status.get("字段核验优先级")).startswith("P0-"):
        return "A4-无稳定OCR人工看图"
    return "A7-常规PDF湖北官方闭环"


def evidence_requirement(fact):
    missing = []
    if clean(fact.get("是否仍需PDF原页")) == "true":
        missing.append("PDF原页")
    if clean(fact.get("是否仍需湖北官方侧")) == "true":
        missing.append("湖北官方侧")
    if clean(fact.get("是否仍需高校辅证")) == "true":
        missing.append("高校官网辅证")
    if clean(fact.get("是否仍需冲突处理")) == "true":
        missing.append("冲突处理")
    if clean(fact.get("是否仍需双人复核")) == "true":
        missing.append("双人复核")
    if clean(fact.get("是否仍需三方闭环")) == "true":
        missing.append("三方闭环")
    if clean(fact.get("是否仍需专业名归属")) == "true":
        missing.append("专业名归属")
    if clean(fact.get("是否仍需专业组边界")) == "true":
        missing.append("专业组边界")
    return "；".join(missing)


def next_min_action(fact, result, field_status, action_group):
    if action_group == "A0-W0B0冲突事实先核":
        return "回PDF原页和湖北官方侧核同一事实；有高校官网辅证时只作double check，冲突事实完成双人复核后再评估写回。"
    if action_group == "A1-专业名归属事实先核":
        return "先核专业名、限定词和备注归属，确认该事实属于哪个专业行或专业组，再继续字段闭环。"
    if action_group == "A2-专业组边界事实随页先核":
        return "随页核专业组边界、左右列和组内专业范围，防止字段串组后再做字段写回评审。"
    if action_group == "A3-双人复核事实先核":
        return "完成双人复核记录，再补PDF原页、湖北官方侧和必要高校辅证状态。"
    if action_group == "A4-无稳定OCR人工看图":
        return "人工看PDF原页定位该事实；有机器或高校线索时只作定位提示，不直接写回。"
    if action_group == "A5-机器坐标辅助核页":
        return "按机器坐标定位PDF原页，但以人工记录和湖北官方侧为准。"
    if action_group == "A6-高校辅证提示回接":
        return "先整理高校官网辅证提示，再回PDF原页和湖北官方侧闭环。"
    return public_text(first_nonempty(fact.get("下一步事实准出动作"), result.get("下一步核验动作"), field_status.get("下一步核验动作")))


def structural_channel(domain, channel):
    if domain == "专业组边界" and channel in {"OCR", "机器坐标"}:
        return "not_applicable_structure_fact_pdf_hubei_first"
    if domain == "专业名归属" and channel == "机器坐标":
        return "not_applicable_major_assignment_pdf_hubei_first"
    return ""


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"fact evidence channel workbench contains forbidden public tokens: {hits[:10]}")


def build_rows():
    fact_rows = read_csv(FACT_RESOLUTION)
    overlay_rows = read_csv(RESOLUTION_OVERLAY)
    result_rows = read_csv(VERIFICATION_RESULT)
    field_status_rows = read_csv(FIELD_STATUS)
    school_progress_rows = read_csv(SCHOOL_PROGRESS)

    overlay_by_key = index_unique(overlay_rows, "页码版面键")
    result_by_task = index_unique(result_rows, "稳定基座第一闭环明细任务ID")
    field_by_task_field = index_field_status(field_status_rows)
    school_by_code = group_by(school_progress_rows, "院校代码")
    overlay_keys = set(overlay_by_key)
    fact_keys = {clean(row.get("页码版面键")) for row in fact_rows if clean(row.get("页码版面键"))}
    if fact_keys != overlay_keys:
        raise SystemExit(
            f"page key mismatch fact_vs_overlay; missing={sorted(overlay_keys - fact_keys)[:10]}; extra={sorted(fact_keys - overlay_keys)[:10]}"
        )

    rows = []
    for fact in fact_rows:
        task_id = clean(fact.get("稳定基座第一闭环明细任务ID"))
        field = clean(fact.get("字段类别"))
        page_key = clean(fact.get("页码版面键"))
        domain = clean(fact.get("事实域"))
        result = result_by_task.get(task_id, {}) if task_id else {}
        field_status = (
            field_by_task_field.get((task_id, field), {})
            if domain == "字段事实" and task_id and field
            else {}
        )
        if domain == "字段事实" and not field_status:
            raise SystemExit(f"missing field status for {(task_id, field)}")
        overlay = overlay_by_key[page_key]
        school = school_summary(school_by_code.get(clean(fact.get("院校代码")), []))
        action_group = fact_action_group(fact, result, field_status)
        action_rank = ACTION_RANK[action_group]
        exec_order = as_int(overlay.get("来源执行顺序"))
        source_seq = as_int(fact.get("准出序号"))

        row = {
            "事实证据通道工作台ID": stable_id("FCFACTCHANNEL", [SOURCE_PDF_SHA256, fact.get("第一闭环事实范围缺口公开账本ID")]),
            "来源事实准出门禁账本": source_path(FACT_RESOLUTION),
            "来源准出执行叠加表": source_path(RESOLUTION_OVERLAY),
            "来源第一闭环核验结果看板": source_path(VERIFICATION_RESULT),
            "来源第一闭环字段级公开状态": source_path(FIELD_STATUS),
            "来源高校官网辅证进度看板": source_path(SCHOOL_PROGRESS),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环事实范围×证据通道工作台",
            "任务粒度": "事实范围×PDF/OCR/机器坐标/高校官网/湖北官方/冲突/复核通道",
            **false_gate_values(),
            "事实工作台序号": 0,
            "来源准出序号": source_seq,
            "来源执行顺序": exec_order,
            "页码版面键": page_key,
            "来源页码": fact.get("来源页码"),
            "版面列": fact.get("版面列"),
            "准出闭环波次": overlay.get("准出闭环波次"),
            "执行泳道": fact.get("执行泳道"),
            "核验动作层级": fact.get("核验动作层级"),
            "第一闭环页列优先级": fact.get("第一闭环页列优先级"),
            "事实核验动作组": action_group,
            "事实通道优先级": f"{action_rank:02d}-{exec_order:03d}-{source_seq:03d}",
            "事实准出门禁ID": fact.get("事实准出门禁ID"),
            "第一闭环事实范围缺口公开账本ID": fact.get("第一闭环事实范围缺口公开账本ID"),
            "稳定基座第一闭环明细任务ID": task_id,
            "稳定基座第一闭环页列包ID": fact.get("稳定基座第一闭环页列包ID"),
            "第一闭环核验结果ID": fact.get("第一闭环核验结果ID") or result.get("第一闭环核验结果ID"),
            "第一闭环字段核验状态ID": field_status.get("第一闭环字段核验状态ID"),
            "专业行ID": fact.get("专业行ID"),
            "专业组出现ID": fact.get("专业组出现ID"),
            "院校代码": fact.get("院校代码"),
            "事实域": domain,
            "事实类型": fact.get("事实类型"),
            "事实粒度": fact.get("事实粒度"),
            "字段类别": field,
            "字段事实状态": field_status.get("字段事实状态") if domain == "字段事实" else "not_applicable_non_field_fact",
            "字段核验优先级": field_status.get("字段核验优先级") if domain == "字段事实" else "not_applicable_non_field_fact",
            "字段事实闭环等级": field_status.get("字段事实闭环等级") if domain == "字段事实" else "not_applicable_non_field_fact",
            "字段事实阻断等级": field_status.get("字段事实阻断等级") if domain == "字段事实" else "not_applicable_non_field_fact",
            "PDF原页通道状态": first_nonempty(fact.get("PDF原页证据状态"), result.get("PDF原页证据状态"), field_status.get("PDF原页证据状态")),
            "OCR提示通道状态": first_nonempty(result.get("OCR提示状态"), field_status.get("OCR提示状态"), structural_channel(domain, "OCR"), default="no_task_level_ocr_channel"),
            "机器坐标通道状态": first_nonempty(result.get("机器坐标提示状态"), field_status.get("机器坐标提示状态"), structural_channel(domain, "机器坐标"), default="no_task_level_machine_coordinate_channel"),
            "高校官网辅证通道状态": first_nonempty(fact.get("高校辅证证据状态"), result.get("高校辅证证据状态"), field_status.get("高校辅证证据状态")),
            "湖北官方侧通道状态": first_nonempty(fact.get("湖北官方侧证据状态"), result.get("湖北官方侧状态"), field_status.get("湖北官方侧状态")),
            "冲突处理通道状态": first_nonempty(fact.get("冲突处理状态"), result.get("冲突状态"), field_status.get("冲突状态")),
            "双人复核通道状态": fact.get("双人复核状态"),
            "三方闭环通道状态": first_nonempty(fact.get("三方闭环状态"), result.get("三方闭环状态"), field_status.get("三方闭环状态")),
            "字段写回评审状态": first_nonempty(fact.get("字段写回评审状态"), field_status.get("字段事实写回状态"), result.get("字段写回门禁")),
            "专业名归属通道状态": fact.get("专业名归属状态"),
            "专业组边界通道状态": fact.get("专业组边界状态"),
            "同校高校源进度任务数": school["count"],
            "同校高校源最高证据层级分布": school["level"],
            "同校高校源下一批优先级分布": school["priority"],
            "同校高校源留存状态分布": school["retention"],
            "同校高校源候选diff数": school["candidate_diff"],
            "同校高校源冲突候选数": school["conflict"],
            "同校高校源补缺候选数": school["fill"],
            "是否仍需PDF原页": fact.get("是否仍需PDF原页"),
            "是否仍需湖北官方侧": fact.get("是否仍需湖北官方侧"),
            "是否仍需高校辅证": fact.get("是否仍需高校辅证"),
            "是否仍需冲突处理": fact.get("是否仍需冲突处理"),
            "是否仍需双人复核": fact.get("是否仍需双人复核"),
            "是否仍需三方闭环": fact.get("是否仍需三方闭环"),
            "是否仍需专业名归属": fact.get("是否仍需专业名归属"),
            "是否仍需专业组边界": fact.get("是否仍需专业组边界"),
            "是否可进入私有写回评审": fact.get("是否可进入私有写回评审"),
            "完成证据要求": evidence_requirement(fact),
            "当前阻断原因": public_text(first_nonempty(fact.get("事实准出主阻断"), result.get("当前阻断原因"), field_status.get("当前阻断原因"))),
            "下一步最小核验动作": next_min_action(fact, result, field_status, action_group),
            "公开安全策略": "not_final；fact_channel_workbench_only；no_field_values；no_school_names；no_major_names；no_private_paths；no_ocr_text；no_recommendation",
        }
        rows.append(row)

    rows.sort(
        key=lambda row: (
            as_int(row["来源执行顺序"]),
            ACTION_RANK[row["事实核验动作组"]],
            as_int(row["来源准出序号"]),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["事实工作台序号"] = index
    return rows, fact_rows, overlay_rows, result_rows, field_status_rows, school_progress_rows


def build_summary(rows, fact_rows, overlay_rows, result_rows, field_status_rows, school_progress_rows):
    summary = {
        "status": f"{DATA_STAGE}_not_final",
        "generated_by": Path(__file__).name,
        "source_fact_resolution": source_path(FACT_RESOLUTION),
        "source_resolution_overlay": source_path(RESOLUTION_OVERLAY),
        "source_verification_result": source_path(VERIFICATION_RESULT),
        "source_field_status": source_path(FIELD_STATUS),
        "source_school_progress": source_path(SCHOOL_PROGRESS),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": source_path(OUTPUT),
        "row_count": len(rows),
        "source_fact_resolution_row_count": len(fact_rows),
        "source_overlay_row_count": len(overlay_rows),
        "source_verification_result_row_count": len(result_rows),
        "source_field_status_row_count": len(field_status_rows),
        "source_school_progress_row_count": len(school_progress_rows),
        "unique_fact_scope_count": len({row.get("第一闭环事实范围缺口公开账本ID") for row in rows}),
        "unique_page_side_count": len({row.get("页码版面键") for row in rows}),
        "unique_task_count": len({row.get("稳定基座第一闭环明细任务ID") for row in rows if row.get("稳定基座第一闭环明细任务ID")}),
        "unique_school_code_count": len({row.get("院校代码") for row in rows if row.get("院校代码")}),
        "fact_domain_counts": dict(Counter(row.get("事实域") for row in rows)),
        "fact_type_counts": dict(Counter(row.get("事实类型") for row in rows)),
        "field_category_counts": dict(Counter(row.get("字段类别") for row in rows if row.get("事实域") == "字段事实")),
        "action_group_counts": dict(Counter(row.get("事实核验动作组") for row in rows)),
        "closure_wave_counts": dict(Counter(row.get("准出闭环波次") for row in rows)),
        "pdf_channel_counts": dict(Counter(row.get("PDF原页通道状态") for row in rows)),
        "ocr_channel_counts": dict(Counter(row.get("OCR提示通道状态") for row in rows)),
        "school_channel_counts": dict(Counter(row.get("高校官网辅证通道状态") for row in rows)),
        "conflict_channel_counts": dict(Counter(row.get("冲突处理通道状态") for row in rows)),
        "double_review_channel_counts": dict(Counter(row.get("双人复核通道状态") for row in rows)),
        "missing_pdf_count": sum(1 for row in rows if row.get("是否仍需PDF原页") == "true"),
        "missing_hubei_official_count": sum(1 for row in rows if row.get("是否仍需湖北官方侧") == "true"),
        "missing_school_source_count": sum(1 for row in rows if row.get("是否仍需高校辅证") == "true"),
        "missing_conflict_count": sum(1 for row in rows if row.get("是否仍需冲突处理") == "true"),
        "missing_double_review_count": sum(1 for row in rows if row.get("是否仍需双人复核") == "true"),
        "missing_three_way_count": sum(1 for row in rows if row.get("是否仍需三方闭环") == "true"),
        "missing_major_assignment_count": sum(1 for row in rows if row.get("是否仍需专业名归属") == "true"),
        "missing_group_boundary_count": sum(1 for row in rows if row.get("是否仍需专业组边界") == "true"),
        "private_writeback_review_ready_count": sum(1 for row in rows if row.get("是否可进入私有写回评审") == "true"),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "policy": {
            "purpose": "把439个第一闭环事实范围压成事实级证据通道工作台，便于按PDF、OCR、机器坐标、高校官网、湖北官方、冲突和复核状态逐项推进。",
            "public_boundary": "公开层只保存事实ID、页列、状态桶、计数、院校代码和SHA，不保存学校专业明细、字段明细值、OCR文本、图像路径、人工记录或登录态。",
            "no_finalization": "该工作台不确认字段事实，不自动写回，不生成学校专业建议或志愿推荐。",
        },
    }
    return summary


def main():
    rows, fact_rows, overlay_rows, result_rows, field_status_rows, school_progress_rows = build_rows()
    summary = build_summary(rows, fact_rows, overlay_rows, result_rows, field_status_rows, school_progress_rows)
    assert_public_safe(rows, summary)
    write_csv(OUTPUT, rows, WORKBENCH_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
