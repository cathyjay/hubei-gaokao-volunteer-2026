#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FACT_PROGRESS = WORKING / "issue19-first-closure-fact-progress-public-ledger.csv"
FACT_PROGRESS_PAGE = WORKING / "issue19-first-closure-fact-progress-page-summary.csv"
FIELD_STATUS = WORKING / "issue19-first-closure-field-verification-status-public-ledger.csv"
VERIFICATION_RESULT = WORKING / "issue19-first-closure-verification-result-public-ledger.csv"
W0_B0_BRIDGE = WORKING / "issue19-w0-b0-school-source-bridge-public-ledger.csv"
FIELD_BACKLINK = WORKING / "issue19-w0-b0-school-source-field-backlink-queue-public-ledger.csv"
FIELD_CONFIRMATION = WORKING / "issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
TASK_REVIEW = WORKING / "issue19-stable-foundation-first-closure-task-review-public-ledger.csv"

OUTPUT = WORKING / "issue19-first-closure-fact-gate-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-first-closure-fact-gate-page-summary.csv"
TASK_OUTPUT = WORKING / "issue19-first-closure-fact-gate-task-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-fact-gate-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_first_closure_fact_gate"
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
    "是否允许进入私有写回评审",
]

GATE_FIELDS = [
    "第一闭环事实准入门禁ID",
    "来源第一闭环事实进度公开账本",
    "来源第一闭环字段级公开状态",
    "来源第一闭环核验结果看板",
    "来源W0B0高校源桥接账本",
    "来源W0B0高校源字段回接队列",
    "来源第一闭环字段确认公开账本",
    "来源第一闭环任务复核公开账本",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "准入序号",
    "第一闭环事实进度公开账本ID",
    "第一闭环事实范围缺口公开账本ID",
    "第一闭环字段核验状态ID",
    "第一闭环核验结果ID",
    "W0B0高校源桥接ID",
    "高校源字段回接队列ID",
    "第一闭环字段确认公开账本ID",
    "稳定基座第一闭环任务复核公开账本ID",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环页列包ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "事实域",
    "事实类型",
    "事实粒度",
    "字段类别",
    "执行泳道",
    "核验动作层级",
    "页列主阻断",
    "第一闭环页列优先级",
    "事实缺口桶",
    "准入总状态",
    "准入阻断等级",
    "PDF原页准入状态",
    "湖北官方侧准入状态",
    "高校源准入状态",
    "冲突处理准入状态",
    "双人复核准入状态",
    "三方闭环准入状态",
    "写回评审准入状态",
    "PDF原页进度桶",
    "OCR提示进度桶",
    "机器坐标进度桶",
    "高校官网辅证进度桶",
    "冲突进度桶",
    "湖北官方侧进度桶",
    "双人复核进度桶",
    "三方闭环状态",
    "字段事实写回状态",
    "字段映射状态",
    "字段事实状态",
    "字段核验优先级",
    "字段事实阻断等级",
    "PDFOCR候选审阅桶",
    "PDFOCR与高校辅证关系桶",
    "机器坐标候选审阅桶",
    "B0冲突闭环状态",
    "B0冲突优先级判定",
    "W0B0命中状态",
    "W0B0事实类型",
    "高校源桥接桶",
    "高校源可作double_check提示",
    "高校源字段回接状态",
    "高校源字段回接泳道",
    "结构化接入候选数",
    "是否PDF湖北官方先行",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "是否存在PDFOCR与高校冲突",
    "PDF原页私有记录状态",
    "湖北官方私有记录状态",
    "高校辅证私有记录状态",
    "双人复核公开状态",
    "三方字段一致性公开状态",
    "字段事实写回评估状态",
    "任务级复核状态",
    "任务级阻断原因",
    "PDF原页是否必核",
    "湖北官方侧是否必核",
    "高校辅证是否需要复核",
    "自动辅证是否可作为核页提示",
    "自动辅证是否可替代湖北官方计划",
    "官方公开计划页可定稿",
    "数智平台可定稿",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR文本证据编号",
    "私有OCR文本SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页列HTML证据编号",
    "私有页列HTML_SHA256",
    "最佳官网来源文件SHA256",
    "裁图证据编号",
    "裁图文件SHA256",
    "证据集合SHA16",
    "当前准入阻断原因",
    "下一步准入动作",
    "公开安全策略",
]

PAGE_FIELDS = [
    "第一闭环事实准入页列汇总ID",
    "来源第一闭环事实准入门禁账本",
    "来源第一闭环事实进度页列汇总",
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
    "事实范围数",
    "字段事实数",
    "专业名归属事实数",
    "专业组边界事实数",
    "涉及任务数",
    "涉及院校代码数",
    "事实类型分布",
    "准入阻断等级分布",
    "核验动作层级分布",
    "执行泳道分布",
    "W0B0命中事实数",
    "高校源double_check事实数",
    "PDF湖北官方先行事实数",
    "B0冲突事实数",
    "需要双人复核事实数",
    "需要人工看图事实数",
    "结构化接入候选事实数",
    "PDF待核事实数",
    "湖北官方待核事实数",
    "准入总状态分布",
    "事实集合SHA16",
    "任务集合SHA16",
    "院校代码集合SHA16",
    "证据集合SHA16",
    "页列准入动作",
    "公开安全策略",
]

TASK_FIELDS = [
    "第一闭环事实准入任务汇总ID",
    "来源第一闭环事实准入门禁账本",
    "来源第一闭环核验结果看板",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "任务汇总序号",
    "稳定基座第一闭环明细任务ID",
    "第一闭环核验结果ID",
    "稳定基座第一闭环任务复核公开账本ID",
    "稳定基座第一闭环页列包ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "字段名",
    "执行泳道",
    "第一闭环页列优先级",
    "核验动作层级",
    "事实范围数",
    "字段事实数",
    "专业名归属事实数",
    "专业组边界事实数",
    "准入阻断等级分布",
    "事实类型分布",
    "W0B0命中事实数",
    "高校源double_check事实数",
    "PDF湖北官方先行事实数",
    "B0冲突事实数",
    "需要双人复核事实数",
    "需要人工看图事实数",
    "结构化接入候选事实数",
    "PDF待核事实数",
    "湖北官方待核事实数",
    "任务级复核状态",
    "任务级阻断原因",
    "PDF原页是否必核",
    "湖北官方侧是否必核",
    "高校辅证是否需要复核",
    "自动辅证是否可作为核页提示",
    "自动辅证是否可替代湖北官方计划",
    "官方公开计划页可定稿",
    "数智平台可定稿",
    "事实集合SHA16",
    "证据集合SHA16",
    "任务准入动作",
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


def index_unique(rows, key):
    indexed = {}
    for row in rows:
        value = clean(row.get(key))
        if value:
            indexed[value] = row
    return indexed


def index_by_task_field(rows):
    indexed = {}
    for row in rows:
        key = (clean(row.get("稳定基座第一闭环明细任务ID")), clean(row.get("字段名")))
        if key[0] and key[1]:
            indexed[key] = row
    return indexed


def group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[clean(row.get(key))].append(row)
    return grouped


def counter_text(rows, field):
    counter = Counter(clean(row.get(field)) for row in rows if clean(row.get(field)))
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()))


def public_policy():
    return "not_final；fact_gate_only；no_field_values；no_private_paths；no_ocr_text；no_recommendation"


def is_pending(value):
    return "pending" in clean(value) or "待" in clean(value) or "blocked" in clean(value)


def pdf_gate(fact, task_review):
    if task_review and clean(task_review.get("PDF原页是否必核")) == "true":
        return "blocked_pdf_required_pending_manual_review"
    if is_pending(fact.get("PDF原页进度桶")):
        return "blocked_pending_pdf_page_review"
    return "blocked_pdf_page_review_not_closed"


def hubei_gate(fact):
    if clean(fact.get("湖北官方侧进度桶")) == "pending_hubei_official_plan_review":
        return "blocked_pending_hubei_official_plan_review"
    return "blocked_hubei_official_review_not_closed"


def school_gate(fact, bridge, backlink):
    if backlink:
        return "hint_only_field_backlink_ready_not_replacement"
    if bridge and clean(bridge.get("高校源可作double_check提示")) == "true":
        return "hint_only_double_check_not_replacement"
    if bridge:
        return "pdf_hubei_first_school_source_later"
    if clean(fact.get("高校官网辅证进度桶")).startswith("S1-"):
        return "hint_only_school_source_pending_private_record"
    return "not_applicable_or_sidecar_only"


def conflict_gate(fact, bridge):
    if clean(fact.get("B0冲突闭环状态")).startswith("R0-") or clean(fact.get("冲突进度桶")).startswith("C0-"):
        return "blocked_b0_conflict_not_closed"
    if bridge and clean(bridge.get("是否存在PDFOCR与高校冲突")) == "true":
        return "blocked_pdf_ocr_school_conflict_not_closed"
    return "blocked_conflict_review_not_closed_or_not_required"


def double_review_gate(fact, field_confirmation):
    if clean(fact.get("双人复核进度桶")) == "pending_double_review":
        return "blocked_pending_double_review"
    if field_confirmation and clean(field_confirmation.get("双人复核公开状态")) == "pending_double_review":
        return "blocked_pending_double_review"
    return "not_required_or_task_level_pending"


def three_way_gate(fact, field_confirmation):
    value = clean((field_confirmation or {}).get("三方字段一致性公开状态")) or clean(fact.get("三方闭环状态"))
    if "pending" in value:
        return "blocked_pending_three_way_closure"
    return "blocked_three_way_closure_not_ready"


def writeback_gate(fact, field_confirmation):
    value = clean((field_confirmation or {}).get("字段事实写回评估状态")) or clean(fact.get("字段事实写回状态"))
    if "blocked" in value or "pending" in value:
        return "blocked_writeback_review_not_allowed"
    return "blocked_writeback_not_allowed"


def gate_level(fact, bridge, backlink):
    fact_domain = clean(fact.get("事实域"))
    if bridge:
        return "G0-W0B0核心事实优先阻断"
    if clean(fact.get("B0冲突闭环状态")).startswith("R0-") or clean(fact.get("页列主阻断")).startswith("B0-"):
        return "G1-B0同页伴生事实阻断"
    if fact_domain in {"专业名归属", "专业组边界"}:
        return "G2-结构事实PDF湖北官方先行"
    if clean(fact.get("双人复核进度桶")) == "pending_double_review":
        return "G3-双人复核待完成"
    if "人工看图" in clean(fact.get("当前阻断原因")) or clean(fact.get("PDF原页进度桶")).startswith("P3-"):
        return "G4-人工看图待完成"
    if backlink:
        return "G5-高校源回接后仍待官方闭环"
    return "G6-常规PDF湖北官方闭环待完成"


def needs_double_review(fact, bridge, field_confirmation):
    return (
        clean(bridge.get("是否需要双人复核")) == "true"
        or clean(fact.get("双人复核进度桶")) == "pending_double_review"
        or clean(field_confirmation.get("双人复核公开状态")) == "pending_double_review"
    )


def needs_manual_image(fact):
    return (
        clean(fact.get("事实缺口桶")).startswith("G0")
        or "人工看图" in clean(fact.get("下一步核验动作"))
    )


def has_pdf_ocr_school_conflict(fact, bridge, result):
    return (
        clean(bridge.get("是否存在PDFOCR与高校冲突")) == "true"
        or clean(result.get("是否存在PDFOCR与高校冲突")) == "true"
        or clean(fact.get("PDFOCR与高校辅证关系桶")).startswith("R0-")
        or clean(fact.get("冲突进度桶")).startswith("C0-")
    )


def atomic_action_level(fact, result):
    task_action = clean(result.get("核验动作层级"))
    if task_action:
        return task_action
    fact_action = clean(fact.get("核验动作层级"))
    if fact_action and "×" not in fact_action and "；" not in fact_action:
        return fact_action
    if clean(fact.get("事实域")) == "专业组边界":
        return "N6-专业组边界PDF湖北官方侧核验"
    return "N7-待拆分核验动作"


def yes_no(value):
    return "true" if value else "false"


def evidence_sha(row):
    fields = [
        "私有页图SHA256",
        "私有OCR文本SHA256",
        "私有页列CSV_SHA256",
        "私有页列HTML_SHA256",
        "最佳官网来源文件SHA256",
        "裁图文件SHA256",
    ]
    return sha16(row.get(field) for field in fields)


def aggregate(rows, field, value="true"):
    return sum(clean(row.get(field)) == value for row in rows)


def assert_public_safe(rows, label):
    text = json.dumps(rows, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"{label} contains forbidden public tokens: {hits[:8]}")


def main():
    fact_rows = read_csv(FACT_PROGRESS)
    fact_page_rows = read_csv(FACT_PROGRESS_PAGE)
    field_rows = read_csv(FIELD_STATUS)
    result_rows = read_csv(VERIFICATION_RESULT)
    bridge_rows = read_csv(W0_B0_BRIDGE)
    backlink_rows = read_csv(FIELD_BACKLINK)
    confirmation_rows = read_csv(FIELD_CONFIRMATION)
    task_review_rows = read_csv(TASK_REVIEW)

    field_by_task_field = index_by_task_field(field_rows)
    result_by_task = index_unique(result_rows, "稳定基座第一闭环明细任务ID")
    bridge_by_fact = index_unique(bridge_rows, "第一闭环事实范围缺口公开账本ID")
    backlink_by_fact = index_unique(backlink_rows, "第一闭环事实范围缺口公开账本ID")
    confirmation_by_task = index_unique(confirmation_rows, "稳定基座第一闭环明细任务ID")
    task_review_by_task = index_unique(task_review_rows, "稳定基座第一闭环明细任务ID")
    fact_page_by_key = index_unique(fact_page_rows, "页码版面键")

    gate_rows = []
    for index, fact in enumerate(fact_rows, start=1):
        fact_id = clean(fact.get("第一闭环事实范围缺口公开账本ID"))
        task_id = clean(fact.get("稳定基座第一闭环明细任务ID"))
        field_name = clean(fact.get("字段类别"))
        field_status = field_by_task_field.get((task_id, field_name), {})
        result = result_by_task.get(task_id, {})
        bridge = bridge_by_fact.get(fact_id, {})
        backlink = backlink_by_fact.get(fact_id, {})
        confirmation = confirmation_by_task.get(task_id, {})
        task_review = task_review_by_task.get(task_id, {})
        gate = gate_level(fact, bridge, backlink)
        w0b0_hit = "W1-W0B0核心事实命中" if bridge else "W0-非W0B0核心事实"
        double_check = clean(bridge.get("高校源可作double_check提示")) if bridge else "false"
        pdf_hubei_first = "true" if bridge and clean(bridge.get("高校源可作double_check提示")) != "true" else "false"
        row = {
            "第一闭环事实准入门禁ID": stable_id("FCFACTGATE", [SOURCE_PDF_SHA256, fact_id]),
            "来源第一闭环事实进度公开账本": source_path(FACT_PROGRESS),
            "来源第一闭环字段级公开状态": source_path(FIELD_STATUS),
            "来源第一闭环核验结果看板": source_path(VERIFICATION_RESULT),
            "来源W0B0高校源桥接账本": source_path(W0_B0_BRIDGE),
            "来源W0B0高校源字段回接队列": source_path(FIELD_BACKLINK),
            "来源第一闭环字段确认公开账本": source_path(FIELD_CONFIRMATION),
            "来源第一闭环任务复核公开账本": source_path(TASK_REVIEW),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环事实范围缺口×准入门禁",
            "任务粒度": "事实范围缺口×PDF原页×湖北官方侧×高校源提示×冲突/双人复核状态",
            **{field: "false" for field in FALSE_FIELDS},
            "准入序号": index,
            "第一闭环事实进度公开账本ID": fact.get("第一闭环事实进度公开账本ID", ""),
            "第一闭环事实范围缺口公开账本ID": fact_id,
            "第一闭环字段核验状态ID": field_status.get("第一闭环字段核验状态ID", ""),
            "第一闭环核验结果ID": result.get("第一闭环核验结果ID", ""),
            "W0B0高校源桥接ID": bridge.get("W0B0高校源桥接ID", ""),
            "高校源字段回接队列ID": backlink.get("高校源字段回接队列ID", ""),
            "第一闭环字段确认公开账本ID": confirmation.get("第一闭环字段确认公开账本ID", ""),
            "稳定基座第一闭环任务复核公开账本ID": task_review.get("稳定基座第一闭环任务复核公开账本ID", ""),
            "稳定基座第一闭环明细任务ID": task_id,
            "稳定基座第一闭环页列包ID": fact.get("稳定基座第一闭环页列包ID", ""),
            "页码版面键": fact.get("页码版面键", ""),
            "来源页码": fact.get("来源页码", ""),
            "版面列": fact.get("版面列", ""),
            "专业行ID": fact.get("专业行ID", ""),
            "专业组出现ID": fact.get("专业组出现ID", ""),
            "院校代码": fact.get("院校代码", ""),
            "事实域": fact.get("事实域", ""),
            "事实类型": fact.get("事实类型", ""),
            "事实粒度": fact.get("事实粒度", ""),
            "字段类别": fact.get("字段类别", ""),
            "执行泳道": fact.get("执行泳道", "") or result.get("执行泳道", ""),
            "核验动作层级": atomic_action_level(fact, result),
            "页列主阻断": fact.get("页列主阻断", ""),
            "第一闭环页列优先级": result.get("第一闭环页列优先级", "") or task_review.get("第一闭环页列优先级", ""),
            "事实缺口桶": fact.get("事实缺口桶", ""),
            "准入总状态": "blocked_not_ready_for_next_stage",
            "准入阻断等级": gate,
            "PDF原页准入状态": pdf_gate(fact, task_review),
            "湖北官方侧准入状态": hubei_gate(fact),
            "高校源准入状态": school_gate(fact, bridge, backlink),
            "冲突处理准入状态": conflict_gate(fact, bridge),
            "双人复核准入状态": double_review_gate(fact, confirmation),
            "三方闭环准入状态": three_way_gate(fact, confirmation),
            "写回评审准入状态": writeback_gate(fact, confirmation),
            "PDF原页进度桶": fact.get("PDF原页进度桶", ""),
            "OCR提示进度桶": fact.get("OCR提示进度桶", ""),
            "机器坐标进度桶": fact.get("机器坐标进度桶", ""),
            "高校官网辅证进度桶": fact.get("高校官网辅证进度桶", ""),
            "冲突进度桶": fact.get("冲突进度桶", ""),
            "湖北官方侧进度桶": fact.get("湖北官方侧进度桶", ""),
            "双人复核进度桶": fact.get("双人复核进度桶", ""),
            "三方闭环状态": fact.get("三方闭环状态", ""),
            "字段事实写回状态": fact.get("字段事实写回状态", ""),
            "字段映射状态": fact.get("字段映射状态", ""),
            "字段事实状态": fact.get("字段事实状态", ""),
            "字段核验优先级": fact.get("字段核验优先级", ""),
            "字段事实阻断等级": fact.get("字段事实阻断等级", ""),
            "PDFOCR候选审阅桶": fact.get("PDFOCR候选审阅桶", ""),
            "PDFOCR与高校辅证关系桶": fact.get("PDFOCR与高校辅证关系桶", ""),
            "机器坐标候选审阅桶": fact.get("机器坐标候选审阅桶", ""),
            "B0冲突闭环状态": fact.get("B0冲突闭环状态", ""),
            "B0冲突优先级判定": fact.get("B0冲突优先级判定", ""),
            "W0B0命中状态": w0b0_hit,
            "W0B0事实类型": bridge.get("事实类型", ""),
            "高校源桥接桶": bridge.get("高校源桥接桶", ""),
            "高校源可作double_check提示": double_check,
            "高校源字段回接状态": "field_backlink_queue_ready" if backlink else "not_in_field_backlink_queue",
            "高校源字段回接泳道": backlink.get("回接泳道", ""),
            "结构化接入候选数": bridge.get("结构化接入候选数", "0") if bridge else "0",
            "是否PDF湖北官方先行": pdf_hubei_first,
            "是否需要人工直接看图": yes_no(needs_manual_image(fact)),
            "是否需要双人复核": yes_no(needs_double_review(fact, bridge, confirmation)),
            "是否存在PDFOCR与高校冲突": yes_no(has_pdf_ocr_school_conflict(fact, bridge, result)),
            "PDF原页私有记录状态": confirmation.get("PDF原页私有记录状态", ""),
            "湖北官方私有记录状态": confirmation.get("湖北官方私有记录状态", ""),
            "高校辅证私有记录状态": confirmation.get("高校辅证私有记录状态", ""),
            "双人复核公开状态": confirmation.get("双人复核公开状态", ""),
            "三方字段一致性公开状态": confirmation.get("三方字段一致性公开状态", ""),
            "字段事实写回评估状态": confirmation.get("字段事实写回评估状态", ""),
            "任务级复核状态": task_review.get("任务级复核状态", ""),
            "任务级阻断原因": task_review.get("任务级阻断原因", ""),
            "PDF原页是否必核": task_review.get("PDF原页是否必核", ""),
            "湖北官方侧是否必核": task_review.get("湖北官方侧是否必核", ""),
            "高校辅证是否需要复核": task_review.get("高校辅证是否需要复核", ""),
            "自动辅证是否可作为核页提示": task_review.get("自动辅证是否可作为核页提示", ""),
            "自动辅证是否可替代湖北官方计划": task_review.get("自动辅证是否可替代湖北官方计划", ""),
            "官方公开计划页可定稿": task_review.get("官方公开计划页可定稿", "false") or "false",
            "数智平台可定稿": task_review.get("数智平台可定稿", "false") or "false",
            "私有页图证据编号": fact.get("私有页图证据编号", ""),
            "私有页图SHA256": fact.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": fact.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": fact.get("私有OCR文本SHA256", ""),
            "私有页列CSV证据编号": fact.get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": fact.get("私有页列CSV_SHA256", ""),
            "私有页列HTML证据编号": fact.get("私有页列HTML证据编号", ""),
            "私有页列HTML_SHA256": fact.get("私有页列HTML_SHA256", ""),
            "最佳官网来源文件SHA256": fact.get("最佳官网来源文件SHA256", "") or task_review.get("最佳官网来源文件SHA256", ""),
            "裁图证据编号": fact.get("裁图证据编号", "") or task_review.get("裁图证据编号", ""),
            "裁图文件SHA256": fact.get("裁图文件SHA256", "") or task_review.get("裁图文件SHA256", ""),
            "证据集合SHA16": evidence_sha(fact),
            "当前准入阻断原因": "PDF原页、湖北官方侧、冲突/双人复核或三方闭环至少一项未完成；禁止升级为字段事实。",
            "下一步准入动作": "先补齐PDF原页私有记录和湖北官方侧记录；高校源仅作double check提示，完成后再评估三方闭环。",
            "公开安全策略": public_policy(),
        }
        gate_rows.append(row)

    rows_by_page = group_by(gate_rows, "页码版面键")
    rows_by_task = group_by([row for row in gate_rows if clean(row.get("稳定基座第一闭环明细任务ID"))], "稳定基座第一闭环明细任务ID")

    def page_sort_key(page_key):
        return (as_int(page_key.split("-", 1)[0]), page_key)

    page_rows = []
    for index, page_key in enumerate(sorted(rows_by_page, key=page_sort_key), start=1):
        rows = rows_by_page[page_key]
        first = rows[0]
        source_page = fact_page_by_key.get(page_key, {})
        page_rows.append({
            "第一闭环事实准入页列汇总ID": stable_id("FCFACTGATEPAGE", [SOURCE_PDF_SHA256, page_key]),
            "来源第一闭环事实准入门禁账本": source_path(OUTPUT),
            "来源第一闭环事实进度页列汇总": source_path(FACT_PROGRESS_PAGE),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环事实准入页列汇总",
            "任务粒度": "PDF页码×版面列×事实范围缺口",
            **{field: "false" for field in FALSE_FIELDS},
            "页列汇总序号": index,
            "页码版面键": page_key,
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "事实范围数": len(rows),
            "字段事实数": aggregate(rows, "事实域", "字段事实"),
            "专业名归属事实数": aggregate(rows, "事实域", "专业名归属"),
            "专业组边界事实数": aggregate(rows, "事实域", "专业组边界"),
            "涉及任务数": len({row["稳定基座第一闭环明细任务ID"] for row in rows if row["稳定基座第一闭环明细任务ID"]}),
            "涉及院校代码数": len({row["院校代码"] for row in rows if row["院校代码"]}),
            "事实类型分布": counter_text(rows, "事实类型"),
            "准入阻断等级分布": counter_text(rows, "准入阻断等级"),
            "核验动作层级分布": counter_text(rows, "核验动作层级"),
            "执行泳道分布": counter_text(rows, "执行泳道"),
            "W0B0命中事实数": sum(row["W0B0命中状态"].startswith("W1-") for row in rows),
            "高校源double_check事实数": aggregate(rows, "高校源可作double_check提示", "true"),
            "PDF湖北官方先行事实数": aggregate(rows, "是否PDF湖北官方先行", "true"),
            "B0冲突事实数": sum(clean(row["B0冲突闭环状态"]).startswith("R0-") for row in rows),
            "需要双人复核事实数": aggregate(rows, "是否需要双人复核", "true"),
            "需要人工看图事实数": aggregate(rows, "是否需要人工直接看图", "true"),
            "结构化接入候选事实数": sum(as_int(row["结构化接入候选数"]) > 0 for row in rows),
            "PDF待核事实数": len(rows),
            "湖北官方待核事实数": len(rows),
            "准入总状态分布": counter_text(rows, "准入总状态"),
            "事实集合SHA16": sha16(row["第一闭环事实范围缺口公开账本ID"] for row in rows),
            "任务集合SHA16": sha16(row["稳定基座第一闭环明细任务ID"] for row in rows),
            "院校代码集合SHA16": sha16(row["院校代码"] for row in rows),
            "证据集合SHA16": sha16(row["证据集合SHA16"] for row in rows),
            "页列准入动作": "按页列补齐PDF原页和湖北官方侧记录；高校源只作提示，不允许字段事实写回。",
            "公开安全策略": public_policy(),
        })
        if source_page and as_int(source_page.get("事实范围数")) != len(rows):
            raise SystemExit(f"page summary mismatch for {page_key}")

    task_rows = []
    for index, task_id in enumerate(sorted(rows_by_task), start=1):
        rows = rows_by_task[task_id]
        first = rows[0]
        result = result_by_task.get(task_id, {})
        task_review = task_review_by_task.get(task_id, {})
        task_rows.append({
            "第一闭环事实准入任务汇总ID": stable_id("FCFACTGATETASK", [SOURCE_PDF_SHA256, task_id]),
            "来源第一闭环事实准入门禁账本": source_path(OUTPUT),
            "来源第一闭环核验结果看板": source_path(VERIFICATION_RESULT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环事实准入任务汇总",
            "任务粒度": "稳定基座第一闭环明细任务ID×事实范围缺口",
            **{field: "false" for field in FALSE_FIELDS},
            "任务汇总序号": index,
            "稳定基座第一闭环明细任务ID": task_id,
            "第一闭环核验结果ID": result.get("第一闭环核验结果ID", ""),
            "稳定基座第一闭环任务复核公开账本ID": task_review.get("稳定基座第一闭环任务复核公开账本ID", ""),
            "稳定基座第一闭环页列包ID": first.get("稳定基座第一闭环页列包ID", ""),
            "页码版面键": first.get("页码版面键", ""),
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "专业行ID": first.get("专业行ID", ""),
            "专业组出现ID": first.get("专业组出现ID", ""),
            "院校代码": first.get("院校代码", ""),
            "字段名": result.get("字段名", ""),
            "执行泳道": result.get("执行泳道", "") or first.get("执行泳道", ""),
            "第一闭环页列优先级": result.get("第一闭环页列优先级", "") or task_review.get("第一闭环页列优先级", ""),
            "核验动作层级": result.get("核验动作层级", "") or first.get("核验动作层级", ""),
            "事实范围数": len(rows),
            "字段事实数": aggregate(rows, "事实域", "字段事实"),
            "专业名归属事实数": aggregate(rows, "事实域", "专业名归属"),
            "专业组边界事实数": aggregate(rows, "事实域", "专业组边界"),
            "准入阻断等级分布": counter_text(rows, "准入阻断等级"),
            "事实类型分布": counter_text(rows, "事实类型"),
            "W0B0命中事实数": sum(row["W0B0命中状态"].startswith("W1-") for row in rows),
            "高校源double_check事实数": aggregate(rows, "高校源可作double_check提示", "true"),
            "PDF湖北官方先行事实数": aggregate(rows, "是否PDF湖北官方先行", "true"),
            "B0冲突事实数": sum(clean(row["B0冲突闭环状态"]).startswith("R0-") for row in rows),
            "需要双人复核事实数": aggregate(rows, "是否需要双人复核", "true"),
            "需要人工看图事实数": aggregate(rows, "是否需要人工直接看图", "true"),
            "结构化接入候选事实数": sum(as_int(row["结构化接入候选数"]) > 0 for row in rows),
            "PDF待核事实数": len(rows),
            "湖北官方待核事实数": len(rows),
            "任务级复核状态": task_review.get("任务级复核状态", ""),
            "任务级阻断原因": task_review.get("任务级阻断原因", ""),
            "PDF原页是否必核": task_review.get("PDF原页是否必核", ""),
            "湖北官方侧是否必核": task_review.get("湖北官方侧是否必核", ""),
            "高校辅证是否需要复核": task_review.get("高校辅证是否需要复核", ""),
            "自动辅证是否可作为核页提示": task_review.get("自动辅证是否可作为核页提示", ""),
            "自动辅证是否可替代湖北官方计划": task_review.get("自动辅证是否可替代湖北官方计划", ""),
            "官方公开计划页可定稿": task_review.get("官方公开计划页可定稿", "false") or "false",
            "数智平台可定稿": task_review.get("数智平台可定稿", "false") or "false",
            "事实集合SHA16": sha16(row["第一闭环事实范围缺口公开账本ID"] for row in rows),
            "证据集合SHA16": sha16(row["证据集合SHA16"] for row in rows),
            "任务准入动作": "任务内事实仍需PDF原页和湖北官方侧闭环；不得据高校源或OCR直接写回。",
            "公开安全策略": public_policy(),
        })

    assert_public_safe(gate_rows, "fact_gate")
    assert_public_safe(page_rows, "fact_gate_page")
    assert_public_safe(task_rows, "fact_gate_task")

    write_csv(OUTPUT, gate_rows, GATE_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)
    write_csv(TASK_OUTPUT, task_rows, TASK_FIELDS)

    summary = {
        "status": "issue19_first_closure_fact_gate_ready_not_final",
        "generated_by": "build_issue19_first_closure_fact_gate_public_ledger.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output": source_path(OUTPUT),
        "page_output": source_path(PAGE_OUTPUT),
        "task_output": source_path(TASK_OUTPUT),
        "fact_gate_row_count": len(gate_rows),
        "page_summary_row_count": len(page_rows),
        "task_summary_row_count": len(task_rows),
        "task_summary_fact_count": sum(as_int(row["事实范围数"]) for row in task_rows),
        "unique_fact_scope_count": len({row["第一闭环事实范围缺口公开账本ID"] for row in gate_rows}),
        "unique_page_side_count": len({row["页码版面键"] for row in gate_rows}),
        "unique_task_count": len({row["稳定基座第一闭环明细任务ID"] for row in gate_rows if row["稳定基座第一闭环明细任务ID"]}),
        "task_absent_fact_count": sum(not bool(row["稳定基座第一闭环明细任务ID"]) for row in gate_rows),
        "fact_domain_counts": dict(Counter(row["事实域"] for row in gate_rows)),
        "fact_type_counts": dict(Counter(row["事实类型"] for row in gate_rows)),
        "field_category_counts": dict(Counter(
            row["字段类别"]
            for row in gate_rows
            if row["事实域"] == "字段事实" and row["字段类别"]
        )),
        "gate_level_counts": dict(Counter(row["准入阻断等级"] for row in gate_rows)),
        "gate_status_counts": dict(Counter(row["准入总状态"] for row in gate_rows)),
        "w0_b0_fact_count": sum(row["W0B0命中状态"].startswith("W1-") for row in gate_rows),
        "w0_b0_double_check_fact_count": sum(row["高校源可作double_check提示"] == "true" for row in gate_rows),
        "w0_b0_pdf_hubei_first_fact_count": sum(row["是否PDF湖北官方先行"] == "true" for row in gate_rows),
        "field_backlink_fact_count": sum(row["高校源字段回接状态"] == "field_backlink_queue_ready" for row in gate_rows),
        "structured_candidate_fact_count": sum(as_int(row["结构化接入候选数"]) > 0 for row in gate_rows),
        "b0_conflict_fact_count": sum(clean(row["B0冲突闭环状态"]).startswith("R0-") for row in gate_rows),
        "double_review_required_fact_count": sum(row["是否需要双人复核"] == "true" for row in gate_rows),
        "manual_image_required_fact_count": sum(row["是否需要人工直接看图"] == "true" for row in gate_rows),
        "pdf_pending_count": len(gate_rows),
        "hubei_official_pending_count": len(gate_rows),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "policy": "本账本只做第一闭环事实准入门禁，不公开字段值，不确认事实，不替代湖北官方计划，不进入推荐。",
    }
    write_json(SUMMARY_OUTPUT, summary)

    public_text = (
        OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + PAGE_OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + TASK_OUTPUT.read_text(encoding="utf-8", errors="ignore")
        + SUMMARY_OUTPUT.read_text(encoding="utf-8", errors="ignore")
    )
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if hits:
        raise SystemExit(f"public output contains forbidden tokens: {hits[:8]}")

    print(f"wrote {OUTPUT}")
    print(f"wrote {PAGE_OUTPUT}")
    print(f"wrote {TASK_OUTPUT}")
    print(f"wrote {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
