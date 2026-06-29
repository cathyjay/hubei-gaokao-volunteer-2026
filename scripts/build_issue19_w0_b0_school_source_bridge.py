#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

W0_B0_ITEMS = WORKING / "issue19-stable-foundation-first-closure-w0-b0-execution-prefill-items-public-audit.csv"
SCHOOL_PROGRESS = WORKING / "issue19-school-source-progress-board-public-ledger.csv"
SCHOOL_RECONCILIATION = WORKING / "issue19-school-source-latest-reconciliation-public-ledger.csv"
STRUCTURED_CANDIDATES = WORKING / "issue19-school-source-structured-ingestion-candidates-public-ledger.csv"

OUTPUT = WORKING / "issue19-w0-b0-school-source-bridge-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-w0-b0-school-source-bridge-page-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-w0-b0-school-source-bridge-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_w0_b0_school_source_bridge"
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
    "W0B0高校源桥接ID",
    "来源W0B0执行预填公开审计",
    "来源高校源进度看板",
    "来源高校源最新对齐账本",
    "来源高校源结构化接入候选账本",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "桥接序号",
    "W0B0执行预填明细公开审计ID",
    "W0B0最小人工复核明细ID",
    "第一闭环事实范围缺口公开账本ID",
    "稳定基座第一闭环明细任务ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "院校代码",
    "事实域",
    "事实类型",
    "事实粒度",
    "字段名",
    "最小复核类型",
    "复核优先级",
    "核验动作层级",
    "候选提示综合桶",
    "PDFOCR与高校辅证关系桶",
    "是否有PDFOCR提示",
    "是否有机器坐标提示",
    "是否有高校辅证线索",
    "是否存在PDFOCR与高校冲突",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "高校源桥接桶",
    "高校源可作double_check提示",
    "高校源仍需补源或解析",
    "高校源进度任务数",
    "高校源最新对齐任务数",
    "结构化接入候选数",
    "最新高校侧证据层级集合",
    "最新证据来源族集合",
    "来源类型桶集合",
    "建议来源形态集合",
    "来源留存状态集合",
    "下一批推进优先级集合",
    "下一批推进动作集合",
    "仍需补源或解析原因集合",
    "next20结构化湖北物理行数合计",
    "live结构化输出记录数合计",
    "C4C6综合结构化官网证据行数合计",
    "C4C6可生成候选diff明细数合计",
    "C4C6计划数一致候选数合计",
    "C4C6官网可补OCR计划数候选数合计",
    "C4C6计划数冲突候选数合计",
    "结构化接入候选来源类型集合",
    "结构化适配器状态集合",
    "候选diff优先级集合",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "下一步桥接动作",
    "公开安全策略",
]

PAGE_FIELDS = [
    "W0B0高校源桥接页列汇总ID",
    "来源W0B0高校源桥接账本",
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
    "事实数",
    "字段事实数",
    "专业名归属事实数",
    "专业组边界事实数",
    "涉及任务数",
    "涉及院校代码数",
    "高校源桥接桶分布",
    "事实类型分布",
    "可作double_check提示事实数",
    "仍需补源或解析事实数",
    "结构化接入候选事实数",
    "需要双人复核事实数",
    "需要人工看图事实数",
    "高校源进度任务数合计",
    "结构化接入候选数合计",
    "事实集合SHA16",
    "任务集合SHA16",
    "院校代码集合SHA16",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "页列下一步桥接动作",
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
    "候选值",
    "字段读数",
    "人工读数",
    "字段确认值",
    "OCR行文本",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
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


def sha16(values):
    normalized = "\n".join(sorted({clean(value) for value in values if clean(value)}))
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def as_int(value):
    try:
        return int(float(clean(value) or "0"))
    except ValueError:
        return 0


def group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[clean(row.get(key))].append(row)
    return grouped


def join_unique(rows, field):
    values = sorted({clean(row.get(field)) for row in rows if clean(row.get(field))})
    return "；".join(values)


def sum_field(rows, field):
    return sum(as_int(row.get(field)) for row in rows)


def counter_text(rows, field):
    counter = Counter(clean(row.get(field)) for row in rows if clean(row.get(field)))
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()))


def bridge_bucket(fact_domain, code, progress_rows, structured_rows):
    if fact_domain == "专业组边界" or not code:
        return "B4-专业组边界或页列事实无单校高校源桥接"
    if fact_domain == "专业名归属":
        return "B5-专业名归属先核PDF原页和湖北官方侧，归属稳定后回接高校源"
    if structured_rows:
        return "B1-已有结构化接入候选，可作为高校侧double check提示"
    if any("L3-" in clean(row.get("最新高校侧证据层级")) for row in progress_rows):
        return "B2-已有高校侧结构化或diff线索，待接入到事实项"
    if progress_rows:
        return "B3-已有高校源任务但仍需补源或解析"
    return "B4-本事实暂未接到高校源任务"


def double_check_allowed(fact_domain, bucket):
    return "true" if fact_domain == "字段事实" and (bucket.startswith("B1-") or bucket.startswith("B2-")) else "false"


def needs_source_work(bucket):
    return "true" if bucket.startswith("B3-") else "false"


def next_action(bucket):
    if bucket.startswith("B1-"):
        return "把结构化接入候选接到本事实的私有核验材料；仍需回看PDF原页并核湖北官方侧。"
    if bucket.startswith("B2-"):
        return "把已有高校侧结构化或diff线索接到本事实项；仍需回看PDF原页并核湖北官方侧。"
    if bucket.startswith("B3-"):
        return "继续补源或解析高校官网公开计划；PDF原页和湖北官方侧仍优先核验。"
    return "先核PDF页列边界或字段记录，再核湖北官方侧；高校源仅作后续补充。"


def public_policy():
    return "not_final；school_source_bridge_only；no_field_values；no_private_paths；no_ocr_text；no_recommendation"


def assert_public_safe(rows, label):
    text = json.dumps(rows, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"{label} contains forbidden public tokens: {hits[:8]}")


def main():
    w0_rows = read_csv(W0_B0_ITEMS)
    progress_rows = read_csv(SCHOOL_PROGRESS)
    reconciliation_rows = read_csv(SCHOOL_RECONCILIATION)
    structured_rows = read_csv(STRUCTURED_CANDIDATES)

    progress_by_code = group_by(progress_rows, "院校代码")
    reconciliation_by_code = group_by(reconciliation_rows, "院校代码")
    structured_by_code = group_by(structured_rows, "院校代码")

    bridge_rows = []
    for index, item in enumerate(w0_rows, start=1):
        code = clean(item.get("院校代码"))
        school_progress = progress_by_code.get(code, [])
        school_reconciliation = reconciliation_by_code.get(code, [])
        structured = structured_by_code.get(code, [])
        fact_domain = clean(item.get("事实域"))
        bucket = bridge_bucket(fact_domain, code, school_progress, structured)
        row = {
            "W0B0高校源桥接ID": stable_id(
                "W0B0SCHOOL",
                [SOURCE_PDF_SHA256, item.get("W0B0执行预填明细公开审计ID")],
            ),
            "来源W0B0执行预填公开审计": source_path(W0_B0_ITEMS),
            "来源高校源进度看板": source_path(SCHOOL_PROGRESS),
            "来源高校源最新对齐账本": source_path(SCHOOL_RECONCILIATION),
            "来源高校源结构化接入候选账本": source_path(STRUCTURED_CANDIDATES),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "W0/B0核心事实×高校源桥接状态",
            "任务粒度": "事实范围缺口×院校代码×高校侧证据层级",
            **{field: "false" for field in FALSE_FIELDS},
            "桥接序号": index,
            "W0B0执行预填明细公开审计ID": item.get("W0B0执行预填明细公开审计ID", ""),
            "W0B0最小人工复核明细ID": item.get("W0B0最小人工复核明细ID", ""),
            "第一闭环事实范围缺口公开账本ID": item.get("第一闭环事实范围缺口公开账本ID", ""),
            "稳定基座第一闭环明细任务ID": item.get("稳定基座第一闭环明细任务ID", ""),
            "页码版面键": item.get("页码版面键", ""),
            "来源页码": item.get("来源页码", ""),
            "版面列": item.get("版面列", ""),
            "院校代码": code,
            "事实域": fact_domain,
            "事实类型": item.get("事实类型", ""),
            "事实粒度": item.get("事实粒度", ""),
            "字段名": item.get("字段名", ""),
            "最小复核类型": item.get("最小复核类型", ""),
            "复核优先级": item.get("复核优先级", ""),
            "核验动作层级": item.get("核验动作层级", ""),
            "候选提示综合桶": item.get("候选提示综合桶", ""),
            "PDFOCR与高校辅证关系桶": item.get("PDFOCR与高校辅证关系桶", ""),
            "是否有PDFOCR提示": item.get("是否有PDFOCR提示", ""),
            "是否有机器坐标提示": item.get("是否有机器坐标提示", ""),
            "是否有高校辅证线索": item.get("是否有高校辅证线索", ""),
            "是否存在PDFOCR与高校冲突": item.get("是否存在PDFOCR与高校冲突", ""),
            "是否需要人工直接看图": item.get("是否需要人工直接看图", ""),
            "是否需要双人复核": item.get("是否需要双人复核", ""),
            "高校源桥接桶": bucket,
            "高校源可作double_check提示": double_check_allowed(fact_domain, bucket),
            "高校源仍需补源或解析": needs_source_work(bucket),
            "高校源进度任务数": len(school_progress),
            "高校源最新对齐任务数": len(school_reconciliation),
            "结构化接入候选数": len(structured),
            "最新高校侧证据层级集合": join_unique(school_progress, "最新高校侧证据层级"),
            "最新证据来源族集合": join_unique(school_progress, "最新证据来源族"),
            "来源类型桶集合": join_unique(school_progress, "来源类型桶"),
            "建议来源形态集合": join_unique(school_progress, "建议来源形态"),
            "来源留存状态集合": join_unique(school_progress, "来源留存状态"),
            "下一批推进优先级集合": join_unique(school_progress, "下一批推进优先级"),
            "下一批推进动作集合": join_unique(school_progress, "下一批推进动作"),
            "仍需补源或解析原因集合": join_unique(school_progress, "仍需补源或解析原因"),
            "next20结构化湖北物理行数合计": sum_field(school_progress, "next20结构化湖北物理行数合计"),
            "live结构化输出记录数合计": sum_field(school_progress, "live结构化输出记录数"),
            "C4C6综合结构化官网证据行数合计": sum_field(school_progress, "C4C6综合结构化官网证据行数"),
            "C4C6可生成候选diff明细数合计": sum_field(school_progress, "C4C6可生成候选diff明细数"),
            "C4C6计划数一致候选数合计": sum_field(school_progress, "C4C6计划数一致候选数"),
            "C4C6官网可补OCR计划数候选数合计": sum_field(school_progress, "C4C6官网可补OCR计划数候选数"),
            "C4C6计划数冲突候选数合计": sum_field(school_progress, "C4C6计划数冲突候选数"),
            "结构化接入候选来源类型集合": join_unique(structured, "来源文件类型"),
            "结构化适配器状态集合": join_unique(structured, "结构化适配器状态"),
            "候选diff优先级集合": join_unique(structured, "候选diff优先级"),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "下一步桥接动作": next_action(bucket),
            "公开安全策略": public_policy(),
        }
        bridge_rows.append(row)

    rows_by_page = defaultdict(list)
    for row in bridge_rows:
        rows_by_page[clean(row.get("页码版面键"))].append(row)

    page_rows = []
    for index, page_key in enumerate(sorted(rows_by_page, key=lambda value: (as_int(value.split("-", 1)[0]), value)), start=1):
        rows = rows_by_page[page_key]
        first = rows[0]
        page_rows.append({
            "W0B0高校源桥接页列汇总ID": stable_id("W0B0SCHOOLPAGE", [SOURCE_PDF_SHA256, page_key]),
            "来源W0B0高校源桥接账本": source_path(OUTPUT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "W0/B0高校源桥接页列汇总",
            "任务粒度": "PDF页码×版面列",
            **{field: "false" for field in FALSE_FIELDS},
            "页列汇总序号": index,
            "页码版面键": page_key,
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "事实数": len(rows),
            "字段事实数": sum(row.get("事实域") == "字段事实" for row in rows),
            "专业名归属事实数": sum(row.get("事实域") == "专业名归属" for row in rows),
            "专业组边界事实数": sum(row.get("事实域") == "专业组边界" for row in rows),
            "涉及任务数": len({row.get("稳定基座第一闭环明细任务ID") for row in rows if row.get("稳定基座第一闭环明细任务ID")}),
            "涉及院校代码数": len({row.get("院校代码") for row in rows if row.get("院校代码")}),
            "高校源桥接桶分布": counter_text(rows, "高校源桥接桶"),
            "事实类型分布": counter_text(rows, "事实类型"),
            "可作double_check提示事实数": sum(row.get("高校源可作double_check提示") == "true" for row in rows),
            "仍需补源或解析事实数": sum(row.get("高校源仍需补源或解析") == "true" for row in rows),
            "结构化接入候选事实数": sum(as_int(row.get("结构化接入候选数")) > 0 for row in rows),
            "需要双人复核事实数": sum(row.get("是否需要双人复核") == "true" for row in rows),
            "需要人工看图事实数": sum(row.get("是否需要人工直接看图") == "true" for row in rows),
            "高校源进度任务数合计": sum_field(rows, "高校源进度任务数"),
            "结构化接入候选数合计": sum_field(rows, "结构化接入候选数"),
            "事实集合SHA16": sha16(row.get("第一闭环事实范围缺口公开账本ID") for row in rows),
            "任务集合SHA16": sha16(row.get("稳定基座第一闭环明细任务ID") for row in rows),
            "院校代码集合SHA16": sha16(row.get("院校代码") for row in rows),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "页列下一步桥接动作": "先按页列回看PDF原页和湖北官方侧；对 B1/B2 事实把高校源线索接入私有核验材料。",
            "公开安全策略": public_policy(),
        })

    assert_public_safe(bridge_rows, "w0_b0_school_source_bridge")
    assert_public_safe(page_rows, "w0_b0_school_source_bridge_page")
    write_csv(OUTPUT, bridge_rows, FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)

    summary = {
        "status": "issue19_w0_b0_school_source_bridge_ready_not_final",
        "generated_by": "build_issue19_w0_b0_school_source_bridge.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output": source_path(OUTPUT),
        "page_output": source_path(PAGE_OUTPUT),
        "row_count": len(bridge_rows),
        "page_summary_row_count": len(page_rows),
        "source_w0_b0_item_count": len(w0_rows),
        "unique_fact_scope_count": len({row["第一闭环事实范围缺口公开账本ID"] for row in bridge_rows}),
        "unique_task_count": len({row["稳定基座第一闭环明细任务ID"] for row in bridge_rows if row["稳定基座第一闭环明细任务ID"]}),
        "unique_page_side_count": len({row["页码版面键"] for row in bridge_rows}),
        "unique_school_code_count": len({row["院校代码"] for row in bridge_rows if row["院校代码"]}),
        "fact_domain_counts": dict(Counter(row["事实域"] for row in bridge_rows)),
        "fact_type_counts": dict(Counter(row["事实类型"] for row in bridge_rows)),
        "bridge_bucket_counts": dict(Counter(row["高校源桥接桶"] for row in bridge_rows)),
        "school_code_present_count": sum(bool(row["院校代码"]) for row in bridge_rows),
        "school_code_absent_count": sum(not bool(row["院校代码"]) for row in bridge_rows),
        "unique_page_count": len({row["来源页码"] for row in bridge_rows if row["来源页码"]}),
        "double_check_hint_fact_count": sum(row["高校源可作double_check提示"] == "true" for row in bridge_rows),
        "pdf_hubei_first_fact_count": sum(row["高校源可作double_check提示"] != "true" for row in bridge_rows),
        "structured_candidate_fact_count": sum(as_int(row["结构化接入候选数"]) > 0 for row in bridge_rows),
        "need_source_or_parse_fact_count": sum(row["高校源仍需补源或解析"] == "true" for row in bridge_rows),
        "no_single_school_bridge_fact_count": sum(row["高校源桥接桶"].startswith("B4-") for row in bridge_rows),
        "double_review_required_fact_count": sum(row["是否需要双人复核"] == "true" for row in bridge_rows),
        "manual_image_required_fact_count": sum(row["是否需要人工直接看图"] == "true" for row in bridge_rows),
        "pdf_pending_count": sum(row["PDF原页核页状态"] == "pending_pdf_page_review" for row in bridge_rows),
        "hubei_official_pending_count": sum(row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_plan_review" for row in bridge_rows),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "policy": "本账本只公开 W0/B0 核心事实与高校源状态的桥接关系，不公开字段值、人工记录或最终结论。",
    }
    write_json(SUMMARY_OUTPUT, summary)

    public_text = (
        OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + PAGE_OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + SUMMARY_OUTPUT.read_text(encoding="utf-8", errors="ignore")
    )
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if hits:
        raise SystemExit(f"public output contains forbidden tokens: {hits[:8]}")

    print(f"wrote {OUTPUT}")
    print(f"wrote {PAGE_OUTPUT}")
    print(f"wrote {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
