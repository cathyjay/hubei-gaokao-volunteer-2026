#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

W0_B0_BRIDGE = WORKING / "issue19-w0-b0-school-source-bridge-public-ledger.csv"
FIELD_STATUS = WORKING / "issue19-first-closure-field-verification-status-public-ledger.csv"
FACT_PROGRESS = WORKING / "issue19-first-closure-fact-progress-public-ledger.csv"
VERIFICATION_RESULT = WORKING / "issue19-first-closure-verification-result-public-ledger.csv"
SCHOOL_PROGRESS = WORKING / "issue19-school-source-progress-board-public-ledger.csv"
SCHOOL_RECONCILIATION = WORKING / "issue19-school-source-latest-reconciliation-public-ledger.csv"
STRUCTURED_CANDIDATES = WORKING / "issue19-school-source-structured-ingestion-candidates-public-ledger.csv"

OUTPUT = WORKING / "issue19-w0-b0-school-source-field-backlink-queue-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-w0-b0-school-source-field-backlink-page-summary.csv"
SCHOOL_OUTPUT = WORKING / "issue19-w0-b0-school-source-field-backlink-school-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-w0-b0-school-source-field-backlink-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_w0_b0_school_source_field_backlink_queue"
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

QUEUE_FIELDS = [
    "高校源字段回接队列ID",
    "来源W0B0高校源桥接账本",
    "来源第一闭环字段级公开状态",
    "来源第一闭环事实进度公开账本",
    "来源第一闭环核验结果看板",
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
    "回接序号",
    "回接泳道",
    "回接批次",
    "回接动作",
    "W0B0高校源桥接ID",
    "第一闭环字段核验状态ID",
    "第一闭环事实进度公开账本ID",
    "第一闭环核验结果ID",
    "第一闭环事实范围缺口公开账本ID",
    "稳定基座第一闭环明细任务ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "院校代码",
    "院校名称公开",
    "事实域",
    "事实类型",
    "事实粒度",
    "字段名",
    "字段事实状态",
    "字段核验优先级",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "字段事实缺口类型",
    "核验动作层级",
    "候选提示综合桶",
    "PDFOCR与高校辅证关系桶",
    "OCR提示状态",
    "高校辅证证据状态",
    "冲突状态",
    "三方闭环状态",
    "是否有PDFOCR提示",
    "是否有高校辅证线索",
    "是否存在PDFOCR与高校冲突",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "高校源桥接桶",
    "高校源可作double_check提示",
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
    "最新公开证据集合SHA16集合",
    "结构化接入候选来源类型集合",
    "结构化适配器状态集合",
    "候选diff优先级集合",
    "本地公开证据文件集合SHA16集合",
    "next20结构化湖北物理行数合计",
    "live结构化输出记录数合计",
    "C4C6综合结构化官网证据行数合计",
    "C4C6可生成候选diff明细数合计",
    "C4C6计划数一致候选数合计",
    "C4C6官网可补OCR计划数候选数合计",
    "C4C6计划数冲突候选数合计",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "公开安全策略",
]

PAGE_FIELDS = [
    "高校源字段回接页列汇总ID",
    "来源高校源字段回接队列",
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
    "字段事实数",
    "涉及任务数",
    "涉及院校代码数",
    "字段名分布",
    "回接泳道分布",
    "高校源桥接桶分布",
    "字段事实状态分布",
    "需要双人复核字段数",
    "需要人工看图字段数",
    "存在PDFOCR与高校冲突字段数",
    "结构化接入候选字段数",
    "高校源进度任务数合计",
    "高校源最新对齐任务数合计",
    "事实集合SHA16",
    "任务集合SHA16",
    "院校代码集合SHA16",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "页列回接动作",
    "公开安全策略",
]

SCHOOL_FIELDS = [
    "高校源字段回接院校汇总ID",
    "来源高校源字段回接队列",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "院校汇总序号",
    "院校代码",
    "院校名称公开",
    "字段事实数",
    "涉及任务数",
    "涉及页列数",
    "字段名分布",
    "回接泳道分布",
    "高校源桥接桶分布",
    "字段事实状态分布",
    "需要双人复核字段数",
    "需要人工看图字段数",
    "存在PDFOCR与高校冲突字段数",
    "结构化接入候选字段数",
    "高校源进度任务数合计",
    "高校源最新对齐任务数合计",
    "最新高校侧证据层级集合",
    "最新证据来源族集合",
    "建议来源形态集合",
    "来源留存状态集合",
    "下一批推进优先级集合",
    "结构化接入候选来源类型集合",
    "结构化适配器状态集合",
    "候选diff优先级集合",
    "next20结构化湖北物理行数合计",
    "C4C6综合结构化官网证据行数合计",
    "C4C6可生成候选diff明细数合计",
    "C4C6计划数一致候选数合计",
    "C4C6官网可补OCR计划数候选数合计",
    "C4C6计划数冲突候选数合计",
    "事实集合SHA16",
    "任务集合SHA16",
    "页列集合SHA16",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "院校回接动作",
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


def index_unique(rows, key):
    indexed = {}
    for row in rows:
        value = clean(row.get(key))
        if value:
            indexed[value] = row
    return indexed


def join_unique(rows, field):
    values = sorted({clean(row.get(field)) for row in rows if clean(row.get(field))})
    return "；".join(values)


def sum_field(rows, field):
    return sum(as_int(row.get(field)) for row in rows)


def counter_text(rows, field):
    counter = Counter(clean(row.get(field)) for row in rows if clean(row.get(field)))
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()))


def public_policy():
    return "not_final；field_backlink_queue_only；no_field_values；no_private_paths；no_ocr_text；no_recommendation"


def backlink_lane(bridge_row):
    if as_int(bridge_row.get("结构化接入候选数")) > 0:
        return "R0-B1结构化接入候选优先回接私有核验"
    if clean(bridge_row.get("是否需要双人复核")) == "true":
        return "R1-B2冲突字段双人核页前回接高校线索"
    return "R2-B2冲突字段核页提示回接"


def backlink_batch(lane):
    if lane.startswith("R0-"):
        return "BACKLINK-01-结构化候选优先"
    if lane.startswith("R1-"):
        return "BACKLINK-02-双人复核冲突优先"
    return "BACKLINK-03-普通冲突提示回接"


def backlink_action(lane):
    if lane.startswith("R0-"):
        return "把结构化接入候选接入私有核验材料，生成字段级double check提示；仍需PDF原页和湖北官方侧闭环。"
    if lane.startswith("R1-"):
        return "把高校侧结构化或diff线索接到字段事实项，供双人回看PDF原页和湖北官方侧时定位冲突。"
    return "把高校侧L3线索接到字段事实项，供人工回看PDF原页和湖北官方侧时作提示。"


def school_name(progress_rows, structured_rows):
    return clean(
        (progress_rows[0].get("院校名称公开") if progress_rows else "")
        or (structured_rows[0].get("院校名称公开") if structured_rows else "")
    )


def assert_public_safe(rows, label):
    text = json.dumps(rows, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"{label} contains forbidden public tokens: {hits[:8]}")


def main():
    bridge_rows = read_csv(W0_B0_BRIDGE)
    field_rows = read_csv(FIELD_STATUS)
    fact_rows = read_csv(FACT_PROGRESS)
    result_rows = read_csv(VERIFICATION_RESULT)
    progress_rows = read_csv(SCHOOL_PROGRESS)
    reconciliation_rows = read_csv(SCHOOL_RECONCILIATION)
    structured_rows = read_csv(STRUCTURED_CANDIDATES)

    field_by_task_field = {
        (clean(row.get("稳定基座第一闭环明细任务ID")), clean(row.get("字段名"))): row
        for row in field_rows
    }
    fact_by_scope = index_unique(fact_rows, "第一闭环事实范围缺口公开账本ID")
    result_by_task = index_unique(result_rows, "稳定基座第一闭环明细任务ID")
    progress_by_code = group_by(progress_rows, "院校代码")
    reconciliation_by_code = group_by(reconciliation_rows, "院校代码")
    structured_by_code = group_by(structured_rows, "院校代码")

    queue_rows = []
    source_bridge_rows = [
        row
        for row in bridge_rows
        if clean(row.get("事实域")) == "字段事实"
        and clean(row.get("高校源可作double_check提示")) == "true"
    ]

    def sort_key(row):
        lane = backlink_lane(row)
        return (
            lane,
            clean(row.get("院校代码")),
            as_int(row.get("来源页码")),
            clean(row.get("版面列")),
            clean(row.get("稳定基座第一闭环明细任务ID")),
            clean(row.get("字段名")),
        )

    for index, bridge in enumerate(sorted(source_bridge_rows, key=sort_key), start=1):
        code = clean(bridge.get("院校代码"))
        task_id = clean(bridge.get("稳定基座第一闭环明细任务ID"))
        field_name = clean(bridge.get("字段名"))
        fact_scope_id = clean(bridge.get("第一闭环事实范围缺口公开账本ID"))
        field_status = field_by_task_field.get((task_id, field_name))
        fact = fact_by_scope.get(fact_scope_id)
        result = result_by_task.get(task_id)
        if not field_status or not fact or not result:
            raise SystemExit(f"missing upstream row for {task_id} {field_name} {fact_scope_id}")

        school_progress = progress_by_code.get(code, [])
        school_reconciliation = reconciliation_by_code.get(code, [])
        structured = structured_by_code.get(code, [])
        lane = backlink_lane(bridge)
        row = {
            "高校源字段回接队列ID": stable_id("W0B0FIELDLINK", [SOURCE_PDF_SHA256, fact_scope_id]),
            "来源W0B0高校源桥接账本": source_path(W0_B0_BRIDGE),
            "来源第一闭环字段级公开状态": source_path(FIELD_STATUS),
            "来源第一闭环事实进度公开账本": source_path(FACT_PROGRESS),
            "来源第一闭环核验结果看板": source_path(VERIFICATION_RESULT),
            "来源高校源进度看板": source_path(SCHOOL_PROGRESS),
            "来源高校源最新对齐账本": source_path(SCHOOL_RECONCILIATION),
            "来源高校源结构化接入候选账本": source_path(STRUCTURED_CANDIDATES),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "W0/B0字段事实×高校源double check回接队列",
            "任务粒度": "字段事实×院校代码×高校侧证据层级",
            **{field: "false" for field in FALSE_FIELDS},
            "回接序号": index,
            "回接泳道": lane,
            "回接批次": backlink_batch(lane),
            "回接动作": backlink_action(lane),
            "W0B0高校源桥接ID": bridge.get("W0B0高校源桥接ID", ""),
            "第一闭环字段核验状态ID": field_status.get("第一闭环字段核验状态ID", ""),
            "第一闭环事实进度公开账本ID": fact.get("第一闭环事实进度公开账本ID", ""),
            "第一闭环核验结果ID": result.get("第一闭环核验结果ID", ""),
            "第一闭环事实范围缺口公开账本ID": fact_scope_id,
            "稳定基座第一闭环明细任务ID": task_id,
            "页码版面键": bridge.get("页码版面键", ""),
            "来源页码": bridge.get("来源页码", ""),
            "版面列": bridge.get("版面列", ""),
            "院校代码": code,
            "院校名称公开": school_name(school_progress, structured),
            "事实域": bridge.get("事实域", ""),
            "事实类型": bridge.get("事实类型", ""),
            "事实粒度": bridge.get("事实粒度", ""),
            "字段名": field_name,
            "字段事实状态": field_status.get("字段事实状态", ""),
            "字段核验优先级": field_status.get("字段核验优先级", ""),
            "字段事实闭环等级": field_status.get("字段事实闭环等级", ""),
            "字段事实阻断等级": field_status.get("字段事实阻断等级", ""),
            "字段事实缺口类型": field_status.get("字段事实缺口类型", ""),
            "核验动作层级": bridge.get("核验动作层级", "") or field_status.get("核验动作层级", ""),
            "候选提示综合桶": bridge.get("候选提示综合桶", ""),
            "PDFOCR与高校辅证关系桶": bridge.get("PDFOCR与高校辅证关系桶", ""),
            "OCR提示状态": field_status.get("OCR提示状态", ""),
            "高校辅证证据状态": field_status.get("高校辅证证据状态", ""),
            "冲突状态": field_status.get("冲突状态", ""),
            "三方闭环状态": field_status.get("三方闭环状态", ""),
            "是否有PDFOCR提示": bridge.get("是否有PDFOCR提示", ""),
            "是否有高校辅证线索": bridge.get("是否有高校辅证线索", ""),
            "是否存在PDFOCR与高校冲突": bridge.get("是否存在PDFOCR与高校冲突", ""),
            "是否需要人工直接看图": bridge.get("是否需要人工直接看图", ""),
            "是否需要双人复核": bridge.get("是否需要双人复核", ""),
            "高校源桥接桶": bridge.get("高校源桥接桶", ""),
            "高校源可作double_check提示": bridge.get("高校源可作double_check提示", ""),
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
            "最新公开证据集合SHA16集合": join_unique(school_progress, "最新公开证据集合SHA16"),
            "结构化接入候选来源类型集合": join_unique(structured, "来源文件类型"),
            "结构化适配器状态集合": join_unique(structured, "结构化适配器状态"),
            "候选diff优先级集合": join_unique(structured, "候选diff优先级"),
            "本地公开证据文件集合SHA16集合": join_unique(structured, "本地公开证据文件集合SHA16"),
            "next20结构化湖北物理行数合计": sum_field(school_progress, "next20结构化湖北物理行数合计"),
            "live结构化输出记录数合计": sum_field(school_progress, "live结构化输出记录数"),
            "C4C6综合结构化官网证据行数合计": sum_field(school_progress, "C4C6综合结构化官网证据行数"),
            "C4C6可生成候选diff明细数合计": sum_field(school_progress, "C4C6可生成候选diff明细数"),
            "C4C6计划数一致候选数合计": sum_field(school_progress, "C4C6计划数一致候选数"),
            "C4C6官网可补OCR计划数候选数合计": sum_field(school_progress, "C4C6官网可补OCR计划数候选数"),
            "C4C6计划数冲突候选数合计": sum_field(school_progress, "C4C6计划数冲突候选数"),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "公开安全策略": public_policy(),
        }
        queue_rows.append(row)

    rows_by_page = defaultdict(list)
    rows_by_school = defaultdict(list)
    for row in queue_rows:
        rows_by_page[row["页码版面键"]].append(row)
        rows_by_school[row["院校代码"]].append(row)

    page_rows = []
    for index, page_key in enumerate(sorted(rows_by_page, key=lambda value: (as_int(value.split("-", 1)[0]), value)), start=1):
        rows = rows_by_page[page_key]
        first = rows[0]
        page_rows.append({
            "高校源字段回接页列汇总ID": stable_id("W0B0FIELDLINKPAGE", [SOURCE_PDF_SHA256, page_key]),
            "来源高校源字段回接队列": source_path(OUTPUT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "W0/B0高校源字段回接页列汇总",
            "任务粒度": "PDF页码×版面列×字段事实",
            **{field: "false" for field in FALSE_FIELDS},
            "页列汇总序号": index,
            "页码版面键": page_key,
            "来源页码": first["来源页码"],
            "版面列": first["版面列"],
            "字段事实数": len(rows),
            "涉及任务数": len({row["稳定基座第一闭环明细任务ID"] for row in rows}),
            "涉及院校代码数": len({row["院校代码"] for row in rows}),
            "字段名分布": counter_text(rows, "字段名"),
            "回接泳道分布": counter_text(rows, "回接泳道"),
            "高校源桥接桶分布": counter_text(rows, "高校源桥接桶"),
            "字段事实状态分布": counter_text(rows, "字段事实状态"),
            "需要双人复核字段数": sum(row["是否需要双人复核"] == "true" for row in rows),
            "需要人工看图字段数": sum(row["是否需要人工直接看图"] == "true" for row in rows),
            "存在PDFOCR与高校冲突字段数": sum(row["是否存在PDFOCR与高校冲突"] == "true" for row in rows),
            "结构化接入候选字段数": sum(as_int(row["结构化接入候选数"]) > 0 for row in rows),
            "高校源进度任务数合计": sum_field(rows, "高校源进度任务数"),
            "高校源最新对齐任务数合计": sum_field(rows, "高校源最新对齐任务数"),
            "事实集合SHA16": sha16(row["第一闭环事实范围缺口公开账本ID"] for row in rows),
            "任务集合SHA16": sha16(row["稳定基座第一闭环明细任务ID"] for row in rows),
            "院校代码集合SHA16": sha16(row["院校代码"] for row in rows),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "页列回接动作": "把本页列高校侧double check线索接入私有核验材料；仍需PDF原页和湖北官方侧闭环。",
            "公开安全策略": public_policy(),
        })

    school_rows = []
    for index, code in enumerate(sorted(rows_by_school), start=1):
        rows = rows_by_school[code]
        first = rows[0]
        school_rows.append({
            "高校源字段回接院校汇总ID": stable_id("W0B0FIELDLINKSCHOOL", [SOURCE_PDF_SHA256, code]),
            "来源高校源字段回接队列": source_path(OUTPUT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "W0/B0高校源字段回接院校汇总",
            "任务粒度": "院校代码×字段事实×高校侧证据层级",
            **{field: "false" for field in FALSE_FIELDS},
            "院校汇总序号": index,
            "院校代码": code,
            "院校名称公开": first["院校名称公开"],
            "字段事实数": len(rows),
            "涉及任务数": len({row["稳定基座第一闭环明细任务ID"] for row in rows}),
            "涉及页列数": len({row["页码版面键"] for row in rows}),
            "字段名分布": counter_text(rows, "字段名"),
            "回接泳道分布": counter_text(rows, "回接泳道"),
            "高校源桥接桶分布": counter_text(rows, "高校源桥接桶"),
            "字段事实状态分布": counter_text(rows, "字段事实状态"),
            "需要双人复核字段数": sum(row["是否需要双人复核"] == "true" for row in rows),
            "需要人工看图字段数": sum(row["是否需要人工直接看图"] == "true" for row in rows),
            "存在PDFOCR与高校冲突字段数": sum(row["是否存在PDFOCR与高校冲突"] == "true" for row in rows),
            "结构化接入候选字段数": sum(as_int(row["结构化接入候选数"]) > 0 for row in rows),
            "高校源进度任务数合计": sum_field(rows, "高校源进度任务数"),
            "高校源最新对齐任务数合计": sum_field(rows, "高校源最新对齐任务数"),
            "最新高校侧证据层级集合": join_unique(rows, "最新高校侧证据层级集合"),
            "最新证据来源族集合": join_unique(rows, "最新证据来源族集合"),
            "建议来源形态集合": join_unique(rows, "建议来源形态集合"),
            "来源留存状态集合": join_unique(rows, "来源留存状态集合"),
            "下一批推进优先级集合": join_unique(rows, "下一批推进优先级集合"),
            "结构化接入候选来源类型集合": join_unique(rows, "结构化接入候选来源类型集合"),
            "结构化适配器状态集合": join_unique(rows, "结构化适配器状态集合"),
            "候选diff优先级集合": join_unique(rows, "候选diff优先级集合"),
            "next20结构化湖北物理行数合计": sum_field(rows, "next20结构化湖北物理行数合计"),
            "C4C6综合结构化官网证据行数合计": sum_field(rows, "C4C6综合结构化官网证据行数合计"),
            "C4C6可生成候选diff明细数合计": sum_field(rows, "C4C6可生成候选diff明细数合计"),
            "C4C6计划数一致候选数合计": sum_field(rows, "C4C6计划数一致候选数合计"),
            "C4C6官网可补OCR计划数候选数合计": sum_field(rows, "C4C6官网可补OCR计划数候选数合计"),
            "C4C6计划数冲突候选数合计": sum_field(rows, "C4C6计划数冲突候选数合计"),
            "事实集合SHA16": sha16(row["第一闭环事实范围缺口公开账本ID"] for row in rows),
            "任务集合SHA16": sha16(row["稳定基座第一闭环明细任务ID"] for row in rows),
            "页列集合SHA16": sha16(row["页码版面键"] for row in rows),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "院校回接动作": "优先把本校高校侧证据接入字段私有核验材料；不得替代湖北官方计划。",
            "公开安全策略": public_policy(),
        })

    assert_public_safe(queue_rows, "field_backlink_queue")
    assert_public_safe(page_rows, "field_backlink_page_summary")
    assert_public_safe(school_rows, "field_backlink_school_summary")

    write_csv(OUTPUT, queue_rows, QUEUE_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)
    write_csv(SCHOOL_OUTPUT, school_rows, SCHOOL_FIELDS)

    summary = {
        "status": "issue19_w0_b0_school_source_field_backlink_queue_ready_not_final",
        "generated_by": "build_issue19_w0_b0_school_source_field_backlink_queue.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output": source_path(OUTPUT),
        "page_output": source_path(PAGE_OUTPUT),
        "school_output": source_path(SCHOOL_OUTPUT),
        "row_count": len(queue_rows),
        "page_summary_row_count": len(page_rows),
        "school_summary_row_count": len(school_rows),
        "source_bridge_row_count": len(bridge_rows),
        "source_double_check_field_fact_count": len(source_bridge_rows),
        "unique_fact_scope_count": len({row["第一闭环事实范围缺口公开账本ID"] for row in queue_rows}),
        "unique_task_count": len({row["稳定基座第一闭环明细任务ID"] for row in queue_rows}),
        "unique_page_side_count": len({row["页码版面键"] for row in queue_rows}),
        "unique_school_code_count": len({row["院校代码"] for row in queue_rows}),
        "field_counts": dict(Counter(row["字段名"] for row in queue_rows)),
        "backlink_lane_counts": dict(Counter(row["回接泳道"] for row in queue_rows)),
        "backlink_batch_counts": dict(Counter(row["回接批次"] for row in queue_rows)),
        "bridge_bucket_counts": dict(Counter(row["高校源桥接桶"] for row in queue_rows)),
        "field_status_counts": dict(Counter(row["字段事实状态"] for row in queue_rows)),
        "field_priority_counts": dict(Counter(row["字段核验优先级"] for row in queue_rows)),
        "field_closure_level_counts": dict(Counter(row["字段事实闭环等级"] for row in queue_rows)),
        "structured_candidate_fact_count": sum(as_int(row["结构化接入候选数"]) > 0 for row in queue_rows),
        "b2_l3_hint_fact_count": sum(row["高校源桥接桶"].startswith("B2-") for row in queue_rows),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in queue_rows),
        "manual_image_required_count": sum(row["是否需要人工直接看图"] == "true" for row in queue_rows),
        "pdf_ocr_school_conflict_count": sum(row["是否存在PDFOCR与高校冲突"] == "true" for row in queue_rows),
        "pdf_pending_count": sum(row["PDF原页核页状态"] == "pending_pdf_page_review" for row in queue_rows),
        "hubei_official_pending_count": sum(
            row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_plan_review"
            for row in queue_rows
        ),
        "school_source_hint_count": sum(row["高校源可作double_check提示"] == "true" for row in queue_rows),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "policy": "本队列只把高校源double check线索回接到W0/B0字段事实核验任务，不公开字段值，不确认事实，不替代湖北官方计划。",
    }
    write_json(SUMMARY_OUTPUT, summary)

    public_text = (
        OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + PAGE_OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + SCHOOL_OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + SUMMARY_OUTPUT.read_text(encoding="utf-8", errors="ignore")
    )
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if hits:
        raise SystemExit(f"public output contains forbidden tokens: {hits[:8]}")

    print(f"wrote {OUTPUT}")
    print(f"wrote {PAGE_OUTPUT}")
    print(f"wrote {SCHOOL_OUTPUT}")
    print(f"wrote {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
