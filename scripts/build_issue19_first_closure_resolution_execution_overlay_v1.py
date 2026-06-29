#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

EXECUTION_QUEUE = WORKING / "issue19-stable-foundation-first-closure-execution-queue.csv"
FACT_RESOLUTION = WORKING / "issue19-first-closure-fact-resolution-gate-v1-public-ledger.csv"
FACT_RESOLUTION_PAGE = WORKING / "issue19-first-closure-fact-resolution-gate-v1-page-summary.csv"
VERIFICATION_RESULT_PAGE = WORKING / "issue19-first-closure-verification-result-page-summary.csv"
PUBLIC_EVIDENCE_MAP = WORKING / "issue19-stable-foundation-first-closure-public-evidence-map.csv"

OUTPUT = WORKING / "issue19-first-closure-resolution-execution-overlay-v1.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-resolution-execution-overlay-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_resolution_execution_overlay_v1"

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
    "是否可以自动闭环",
]

OVERLAY_FIELDS = [
    "第一闭环准出执行叠加ID",
    "来源第一闭环执行队列",
    "来源第一闭环事实准出门禁账本",
    "来源第一闭环事实准出页列汇总",
    "来源第一闭环核验结果页列汇总",
    "来源第一闭环公开证据地图",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "叠加序号",
    "来源执行顺序",
    "页码版面键",
    "来源页码",
    "版面列",
    "执行泳道",
    "第一闭环页列优先级",
    "准出闭环波次",
    "准出闭环优先级",
    "页列主阻断",
    "执行队列首要动作",
    "准出主动作",
    "准出完成条件",
    "页列任务数",
    "事实范围数",
    "字段事实数",
    "专业名归属事实数",
    "专业组边界事实数",
    "涉及任务数",
    "涉及院校代码数",
    "PDF原页待核任务数",
    "湖北官方侧待核任务数",
    "高校辅证线索任务数",
    "PDFOCR提示任务数",
    "PDFOCR无候选任务数",
    "机器坐标提示任务数",
    "PDFOCR与高校辅证冲突任务数",
    "需要人工直接看图任务数",
    "需要双人复核任务数",
    "PDF待补事实数",
    "湖北官方待补事实数",
    "高校辅证待补事实数",
    "冲突待处理事实数",
    "双人复核待完成事实数",
    "三方闭环待完成事实数",
    "专业名归属待闭环事实数",
    "专业组边界待闭环事实数",
    "可进入私有写回评审事实数",
    "W0B0核心阻断事实数",
    "B0同页伴生阻断事实数",
    "结构事实阻断事实数",
    "双人复核阻断事实数",
    "人工看图阻断事实数",
    "常规阻断事实数",
    "是否仍需PDF原页",
    "是否仍需湖北官方侧",
    "是否仍需高校辅证",
    "是否仍需冲突处理",
    "是否仍需双人复核",
    "是否仍需专业名归属",
    "是否仍需专业组边界",
    "事实准出状态分布",
    "事实准出阻断等级分布",
    "事实类型分布",
    "事实集合SHA16",
    "任务集合SHA16",
    "院校代码集合SHA16",
    "公开安全策略",
    "下一步",
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
    "字段OCR候选",
    "字段人工确认",
    "字段候选值集合",
    "候选计划数",
    "候选学费",
    "候选选科",
    "机器候选字段值",
    "机器候选值集合",
    "专业名称及备注",
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

STATUS_COLUMNS = {
    "blocked_w0_b0_core_pdf_hubei": "W0B0核心阻断事实数",
    "blocked_b0_companion_pdf_hubei": "B0同页伴生阻断事实数",
    "blocked_structure_pdf_hubei": "结构事实阻断事实数",
    "blocked_double_review_pdf_hubei": "双人复核阻断事实数",
    "blocked_manual_image_pdf_hubei": "人工看图阻断事实数",
    "blocked_regular_pdf_hubei": "常规阻断事实数",
}


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


def as_int(value):
    try:
        return int(float(clean(value) or "0"))
    except ValueError:
        return 0


def bool_text(value):
    return "true" if value else "false"


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def public_text(value):
    return clean(value).replace("字段读数", "字段明细值")


def index_unique(rows, key):
    indexed = {}
    for row in rows:
        value = clean(row.get(key))
        if value:
            if value in indexed:
                raise SystemExit(f"duplicate {key}: {value}")
            indexed[value] = row
    return indexed


def group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[clean(row.get(key))].append(row)
    return grouped


def assert_same_keys(label, expected, actual):
    if expected != actual:
        missing = sorted(expected - actual)[:10]
        extra = sorted(actual - expected)[:10]
        raise SystemExit(f"{label} key mismatch; missing={missing}; extra={extra}")


def counter_text(counter):
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()) if key)


def status_counter_for_page(rows):
    return Counter(clean(row.get("事实准出状态")) for row in rows if clean(row.get("事实准出状态")))


def closure_wave(page_summary, status_counter):
    conflict_count = as_int(page_summary.get("冲突待处理事实数"))
    major_assignment_count = as_int(page_summary.get("专业名归属待闭环事实数"))
    group_boundary_count = as_int(page_summary.get("专业组边界待闭环事实数"))
    double_count = as_int(page_summary.get("双人复核待完成事实数"))
    school_count = as_int(page_summary.get("高校辅证待补事实数"))
    if status_counter.get("blocked_w0_b0_core_pdf_hubei") or conflict_count:
        return "R0-W0B0冲突事实先闭环"
    if major_assignment_count:
        return "R1-专业名归属事实先闭环"
    if double_count:
        return "R2-双人复核事实先闭环"
    if school_count:
        return "R3-高校辅证提示回接"
    if group_boundary_count:
        return "R4-专业组边界随页闭环"
    return "R5-常规PDF湖北官方闭环"


def closure_priority(row, page_summary, status_counter):
    score = (
        as_int(page_summary.get("冲突待处理事实数")) * 100
        + status_counter.get("blocked_w0_b0_core_pdf_hubei", 0) * 80
        + as_int(page_summary.get("双人复核待完成事实数")) * 30
        + as_int(page_summary.get("专业名归属待闭环事实数")) * 20
        + as_int(page_summary.get("专业组边界待闭环事实数")) * 20
        + as_int(page_summary.get("事实范围数"))
    )
    return f"{score:05d}-沿执行顺序核页"


def main_action(page_summary, evidence, result_page):
    if as_int(page_summary.get("冲突待处理事实数")):
        return "先核PDF原页和湖北官方侧；冲突事实必须完成双人复核和三方闭环后才可进入写回评审。"
    if as_int(page_summary.get("专业名归属待闭环事实数")):
        return "先核专业名归属和限定词归属，再随页核PDF原页、湖北官方侧和专业组边界。"
    if as_int(page_summary.get("双人复核待完成事实数")):
        return "先完成双人复核，再补PDF原页、湖北官方侧和必要高校辅证记录。"
    if as_int(page_summary.get("高校辅证待补事实数")):
        return "高校源只作double check提示；仍以PDF原页和湖北官方侧闭环为准。"
    if as_int(page_summary.get("专业组边界待闭环事实数")):
        return "随页核专业组边界和左右列结构，再补PDF原页与湖北官方侧记录。"
    return clean(result_page.get("页列建议下一步动作")) or clean(evidence.get("页列建议下一步动作"))


def completion_condition(page_summary):
    return (
        f"PDF原页事实补齐={page_summary.get('PDF待补事实数', '0')}；"
        f"湖北官方侧事实补齐={page_summary.get('湖北官方待补事实数', '0')}；"
        f"三方闭环补齐={page_summary.get('三方闭环待完成事实数', '0')}；"
        "冲突、双人复核、专业名归属和专业组边界全部清零后，才可进入私有写回评审；仍不得直接生成推荐。"
    )


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"public overlay contains forbidden tokens: {hits[:10]}")


def build_rows():
    execution_rows = read_csv(EXECUTION_QUEUE)
    resolution_rows = read_csv(FACT_RESOLUTION)
    resolution_page_rows = read_csv(FACT_RESOLUTION_PAGE)
    result_page_rows = read_csv(VERIFICATION_RESULT_PAGE)
    evidence_rows = read_csv(PUBLIC_EVIDENCE_MAP)

    resolution_by_key = group_by(resolution_rows, "页码版面键")
    page_by_key = index_unique(resolution_page_rows, "页码版面键")
    result_by_key = index_unique(result_page_rows, "页码版面键")
    evidence_by_key = index_unique(evidence_rows, "页码版面键")

    execution_keys = {clean(row.get("页码版面键")) for row in execution_rows if clean(row.get("页码版面键"))}
    assert_same_keys("fact resolution page summary", execution_keys, set(page_by_key))
    assert_same_keys("verification result page summary", execution_keys, set(result_by_key))
    assert_same_keys("public evidence map", execution_keys, set(evidence_by_key))
    assert_same_keys("fact resolution ledger", execution_keys, set(resolution_by_key))

    overlay_rows = []
    for index, execution in enumerate(execution_rows, start=1):
        key = clean(execution.get("页码版面键"))
        page_summary = page_by_key.get(key, {})
        result_page = result_by_key.get(key, {})
        evidence = evidence_by_key.get(key, {})
        fact_group = resolution_by_key.get(key, [])
        status_counter = status_counter_for_page(fact_group)
        blocker_counter = Counter(clean(row.get("事实准出阻断等级")) for row in fact_group if clean(row.get("事实准出阻断等级")))
        fact_type_counter = Counter(clean(row.get("事实类型")) for row in fact_group if clean(row.get("事实类型")))

        row = {
            "第一闭环准出执行叠加ID": stable_id("FCRESEXEC", [SOURCE_PDF_SHA256, key]),
            "来源第一闭环执行队列": source_path(EXECUTION_QUEUE),
            "来源第一闭环事实准出门禁账本": source_path(FACT_RESOLUTION),
            "来源第一闭环事实准出页列汇总": source_path(FACT_RESOLUTION_PAGE),
            "来源第一闭环核验结果页列汇总": source_path(VERIFICATION_RESULT_PAGE),
            "来源第一闭环公开证据地图": source_path(PUBLIC_EVIDENCE_MAP),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列×事实准出执行叠加",
            "任务粒度": "页列执行队列×事实准出缺口×核验结果页列汇总",
            **false_gate_values(),
            "叠加序号": index,
            "来源执行顺序": execution.get("执行顺序"),
            "页码版面键": key,
            "来源页码": execution.get("来源页码"),
            "版面列": execution.get("版面列"),
            "执行泳道": execution.get("执行泳道"),
            "第一闭环页列优先级": execution.get("第一闭环页列优先级"),
            "准出闭环波次": closure_wave(page_summary, status_counter),
            "准出闭环优先级": closure_priority(execution, page_summary, status_counter),
            "页列主阻断": clean(result_page.get("页列主阻断")) or clean(evidence.get("页列主阻断")),
            "执行队列首要动作": public_text(execution.get("页列首要核验动作")),
            "准出主动作": main_action(page_summary, evidence, result_page),
            "准出完成条件": completion_condition(page_summary),
            "页列任务数": execution.get("页列总任务数"),
            "事实范围数": page_summary.get("事实范围数"),
            "字段事实数": page_summary.get("字段事实数"),
            "专业名归属事实数": page_summary.get("专业名归属事实数"),
            "专业组边界事实数": page_summary.get("专业组边界事实数"),
            "涉及任务数": page_summary.get("涉及任务数"),
            "涉及院校代码数": page_summary.get("涉及院校代码数"),
            "PDF原页待核任务数": evidence.get("PDF原页待核任务数") or result_page.get("PDF原页待核任务数"),
            "湖北官方侧待核任务数": evidence.get("湖北官方侧待核任务数") or result_page.get("湖北官方侧待核任务数"),
            "高校辅证线索任务数": evidence.get("高校辅证线索任务数") or result_page.get("高校辅证线索任务数"),
            "PDFOCR提示任务数": evidence.get("PDFOCR提示任务数"),
            "PDFOCR无候选任务数": evidence.get("PDFOCR无候选任务数"),
            "机器坐标提示任务数": evidence.get("机器坐标提示任务数"),
            "PDFOCR与高校辅证冲突任务数": evidence.get("PDFOCR与高校辅证冲突任务数"),
            "需要人工直接看图任务数": evidence.get("需要人工直接看图任务数") or result_page.get("需要人工直接看图任务数"),
            "需要双人复核任务数": evidence.get("需要双人复核任务数") or result_page.get("需要双人复核任务数"),
            "PDF待补事实数": page_summary.get("PDF待补事实数"),
            "湖北官方待补事实数": page_summary.get("湖北官方待补事实数"),
            "高校辅证待补事实数": page_summary.get("高校辅证待补事实数"),
            "冲突待处理事实数": page_summary.get("冲突待处理事实数"),
            "双人复核待完成事实数": page_summary.get("双人复核待完成事实数"),
            "三方闭环待完成事实数": page_summary.get("三方闭环待完成事实数"),
            "专业名归属待闭环事实数": page_summary.get("专业名归属待闭环事实数"),
            "专业组边界待闭环事实数": page_summary.get("专业组边界待闭环事实数"),
            "可进入私有写回评审事实数": page_summary.get("可进入私有写回评审事实数"),
            "是否仍需PDF原页": bool_text(as_int(page_summary.get("PDF待补事实数")) > 0),
            "是否仍需湖北官方侧": bool_text(as_int(page_summary.get("湖北官方待补事实数")) > 0),
            "是否仍需高校辅证": bool_text(as_int(page_summary.get("高校辅证待补事实数")) > 0),
            "是否仍需冲突处理": bool_text(as_int(page_summary.get("冲突待处理事实数")) > 0),
            "是否仍需双人复核": bool_text(as_int(page_summary.get("双人复核待完成事实数")) > 0),
            "是否仍需专业名归属": bool_text(as_int(page_summary.get("专业名归属待闭环事实数")) > 0),
            "是否仍需专业组边界": bool_text(as_int(page_summary.get("专业组边界待闭环事实数")) > 0),
            "事实准出状态分布": counter_text(status_counter),
            "事实准出阻断等级分布": counter_text(blocker_counter),
            "事实类型分布": counter_text(fact_type_counter),
            "事实集合SHA16": page_summary.get("事实集合SHA16"),
            "任务集合SHA16": page_summary.get("任务集合SHA16"),
            "院校代码集合SHA16": page_summary.get("院校代码集合SHA16"),
            "公开安全策略": "not_final；execution_overlay_only；no_field_values；no_school_names；no_major_names；no_private_paths；no_ocr_text；no_recommendation",
            "下一步": "按来源执行顺序回到私有核页材料，补PDF原页、湖北官方侧、必要高校辅证和双人复核记录；公开层只同步状态和计数。",
        }
        for status, field in STATUS_COLUMNS.items():
            row[field] = status_counter.get(status, 0)
        overlay_rows.append(row)

    return overlay_rows, execution_rows, resolution_rows, resolution_page_rows, result_page_rows, evidence_rows


def build_summary(rows, execution_rows, resolution_rows, resolution_page_rows, result_page_rows, evidence_rows):
    summary = {
        "status": f"{DATA_STAGE}_not_final",
        "generated_by": Path(__file__).name,
        "source_execution_queue": source_path(EXECUTION_QUEUE),
        "source_fact_resolution": source_path(FACT_RESOLUTION),
        "source_fact_resolution_page_summary": source_path(FACT_RESOLUTION_PAGE),
        "source_verification_result_page_summary": source_path(VERIFICATION_RESULT_PAGE),
        "source_public_evidence_map": source_path(PUBLIC_EVIDENCE_MAP),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": source_path(OUTPUT),
        "public_row_count": len(rows),
        "source_execution_row_count": len(execution_rows),
        "source_fact_resolution_row_count": len(resolution_rows),
        "source_fact_resolution_page_row_count": len(resolution_page_rows),
        "source_verification_result_page_row_count": len(result_page_rows),
        "source_public_evidence_map_row_count": len(evidence_rows),
        "unique_page_side_count": len({row.get("页码版面键") for row in rows}),
        "unique_pdf_page_count": len({row.get("来源页码") for row in rows}),
        "total_task_count": sum(as_int(row.get("页列任务数")) for row in rows),
        "fact_count": sum(as_int(row.get("事实范围数")) for row in rows),
        "field_fact_count": sum(as_int(row.get("字段事实数")) for row in rows),
        "major_assignment_fact_count": sum(as_int(row.get("专业名归属事实数")) for row in rows),
        "group_boundary_fact_count": sum(as_int(row.get("专业组边界事实数")) for row in rows),
        "missing_pdf_count": sum(as_int(row.get("PDF待补事实数")) for row in rows),
        "missing_hubei_official_count": sum(as_int(row.get("湖北官方待补事实数")) for row in rows),
        "missing_school_source_count": sum(as_int(row.get("高校辅证待补事实数")) for row in rows),
        "missing_conflict_count": sum(as_int(row.get("冲突待处理事实数")) for row in rows),
        "missing_double_review_count": sum(as_int(row.get("双人复核待完成事实数")) for row in rows),
        "missing_three_way_count": sum(as_int(row.get("三方闭环待完成事实数")) for row in rows),
        "missing_major_assignment_count": sum(as_int(row.get("专业名归属待闭环事实数")) for row in rows),
        "missing_group_boundary_count": sum(as_int(row.get("专业组边界待闭环事实数")) for row in rows),
        "private_writeback_review_ready_count": sum(as_int(row.get("可进入私有写回评审事实数")) for row in rows),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "auto_closure_allowed_count": 0,
        "lane_counts": dict(Counter(row.get("执行泳道") for row in rows)),
        "closure_wave_counts": dict(Counter(row.get("准出闭环波次") for row in rows)),
        "priority_counts": dict(Counter(row.get("第一闭环页列优先级") for row in rows)),
        "first_overlay_page_side_keys": [row.get("页码版面键") for row in rows[:10]],
        "policy": {
            "purpose": "把第一闭环执行队列和439个事实准出缺口按页列叠加，形成下一轮补证闭环的公开执行入口。",
            "public_boundary": "只公开页列顺序、状态桶、计数、集合SHA和门禁，不公开学校专业明细、字段明细值、OCR正文、图片路径、人工记录或登录态。",
            "no_finalization": "该叠加表不确认字段事实，不写回主表，不生成学校专业建议或志愿推荐。",
        },
    }
    return summary


def main():
    rows, execution_rows, resolution_rows, resolution_page_rows, result_page_rows, evidence_rows = build_rows()
    summary = build_summary(
        rows,
        execution_rows,
        resolution_rows,
        resolution_page_rows,
        result_page_rows,
        evidence_rows,
    )
    assert_public_safe(rows, summary)
    write_csv(OUTPUT, rows, OVERLAY_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
