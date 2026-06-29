#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FACT_GATE = WORKING / "issue19-first-closure-fact-gate-public-ledger.csv"
FACT_SCOPE = WORKING / "issue19-stable-foundation-first-closure-fact-scope-gap-public-ledger.csv"
FIELD_FACT = WORKING / "issue19-stable-foundation-first-closure-field-fact-public-ledger.csv"
VERIFICATION_RESULT = WORKING / "issue19-first-closure-verification-result-public-ledger.csv"
EVIDENCE_STATUS = WORKING / "issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv"
NEXT_ACTION = WORKING / "issue19-stable-foundation-first-closure-next-action-matrix.csv"
P0_THREE_WAY = WORKING / "issue19-p0-immediate-three-way-closure-public-ledger.csv"
SCHOOL_RECONCILIATION = WORKING / "issue19-school-source-latest-reconciliation-public-ledger.csv"
FIELD_BACKLINK = WORKING / "issue19-w0-b0-school-source-field-backlink-queue-public-ledger.csv"
OFFICIAL_PUBLIC_STATUS = WORKING / "issue19-official-public-entry-status.json"

OUTPUT = WORKING / "issue19-first-closure-fact-resolution-gate-v1-public-ledger.csv"
PAGE_OUTPUT = WORKING / "issue19-first-closure-fact-resolution-gate-v1-page-summary.csv"
TASK_OUTPUT = WORKING / "issue19-first-closure-fact-resolution-gate-v1-task-summary.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-fact-resolution-gate-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_first_closure_fact_resolution_gate_v1"
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

LEDGER_FIELDS = [
    "事实准出门禁ID",
    "来源第一闭环事实准入门禁账本",
    "来源第一闭环事实范围缺口账本",
    "来源第一闭环字段事实公开账本",
    "来源第一闭环核验结果看板",
    "来源第一闭环证据状态账本",
    "来源第一闭环下一步动作矩阵",
    "来源P0即时三方闭环公开账本",
    "来源高校源最新对齐账本",
    "来源W0B0高校源字段回接队列",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "准出序号",
    "第一闭环事实准入门禁ID",
    "第一闭环事实范围缺口公开账本ID",
    "第一闭环字段事实公开账本ID",
    "第一闭环核验结果ID",
    "第一闭环证据状态公开账本ID",
    "第一闭环下一步动作ID",
    "P0即时三方闭环公开账本ID",
    "高校源字段回接队列ID",
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
    "第一闭环页列优先级",
    "事实准出状态",
    "事实准出阻断等级",
    "事实准出主阻断",
    "事实准出缺口清单",
    "事实准出完成条件",
    "PDF原页证据状态",
    "湖北官方侧证据状态",
    "高校辅证证据状态",
    "冲突处理状态",
    "双人复核状态",
    "三方闭环状态",
    "字段写回评审状态",
    "专业名归属状态",
    "专业组边界状态",
    "高校源字段回接状态",
    "同校高校源最新对齐记录数",
    "同校高校源最高证据层级",
    "P0三方闭环状态",
    "官方公开计划页可定稿",
    "数智平台可定稿",
    "湖北官方公开入口状态",
    "是否PDF原页已核",
    "是否湖北官方侧已核",
    "是否高校辅证必要且已核",
    "是否冲突已闭环",
    "是否双人复核已完成",
    "是否三方闭环完成",
    "是否字段写回评审完成",
    "是否可进入私有写回评审",
    "是否仍需PDF原页",
    "是否仍需湖北官方侧",
    "是否仍需高校辅证",
    "是否仍需冲突处理",
    "是否仍需双人复核",
    "是否仍需三方闭环",
    "是否仍需专业名归属",
    "是否仍需专业组边界",
    "下一步事实准出动作",
    "公开安全策略",
]

PAGE_FIELDS = [
    "事实准出页列汇总ID",
    "来源事实准出门禁账本",
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
    "事实准出状态分布",
    "事实准出阻断等级分布",
    "事实类型分布",
    "PDF待补事实数",
    "湖北官方待补事实数",
    "高校辅证待补事实数",
    "冲突待处理事实数",
    "双人复核待完成事实数",
    "三方闭环待完成事实数",
    "专业名归属待闭环事实数",
    "专业组边界待闭环事实数",
    "可进入私有写回评审事实数",
    "事实集合SHA16",
    "任务集合SHA16",
    "院校代码集合SHA16",
    "页列准出动作",
    "公开安全策略",
]

TASK_FIELDS = [
    "事实准出任务汇总ID",
    "来源事实准出门禁账本",
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
    "第一闭环证据状态公开账本ID",
    "第一闭环下一步动作ID",
    "稳定基座第一闭环页列包ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "字段名",
    "执行泳道",
    "核验动作层级",
    "第一闭环页列优先级",
    "事实范围数",
    "字段事实数",
    "专业名归属事实数",
    "专业组边界事实数",
    "事实准出状态分布",
    "事实准出阻断等级分布",
    "事实类型分布",
    "PDF待补事实数",
    "湖北官方待补事实数",
    "高校辅证待补事实数",
    "冲突待处理事实数",
    "双人复核待完成事实数",
    "三方闭环待完成事实数",
    "可进入私有写回评审事实数",
    "事实集合SHA16",
    "任务准出动作",
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


def yes_no(value):
    return "true" if value else "false"


def index_unique(rows, key):
    indexed = {}
    for row in rows:
        value = clean(row.get(key))
        if value:
            indexed[value] = row
    return indexed


def index_by_task(rows):
    return index_unique(rows, "稳定基座第一闭环明细任务ID")


def index_by_task_field(rows, field_col):
    indexed = {}
    for row in rows:
        task_id = clean(row.get("稳定基座第一闭环明细任务ID"))
        field_name = clean(row.get(field_col))
        if task_id and field_name:
            indexed[(task_id, field_name)] = row
    return indexed


def group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[clean(row.get(key))].append(row)
    return grouped


def counter_text(rows, field):
    counter = Counter(clean(row.get(field)) for row in rows if clean(row.get(field)))
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()))


def aggregate(rows, field, value="true"):
    return sum(clean(row.get(field)) == value for row in rows)


def public_policy():
    return "not_final；resolution_gate_only；no_field_values；no_school_names；no_major_names；no_private_paths；no_ocr_text；no_recommendation"


def completed(value):
    text = clean(value).lower()
    if not text:
        return False
    blocked_markers = ["pending", "blocked", "待", "未", "not_", "缺", "不能", "不允许"]
    if any(marker in text for marker in blocked_markers):
        return False
    ready_markers = ["ready", "closed", "complete", "完成", "已核", "一致"]
    return any(marker in text for marker in ready_markers)


def needs_school(fact_gate, field_backlink, next_action):
    return (
        clean(fact_gate.get("高校源可作double_check提示")) == "true"
        or bool(field_backlink)
        or clean(next_action.get("是否有高校辅证线索")) == "true"
    )


def gate_status(fact_gate):
    level = clean(fact_gate.get("准入阻断等级"))
    if level.startswith("G0-"):
        return "blocked_w0_b0_core_pdf_hubei"
    if level.startswith("G1-"):
        return "blocked_b0_companion_pdf_hubei"
    if level.startswith("G2-"):
        return "blocked_structure_pdf_hubei"
    if level.startswith("G3-"):
        return "blocked_double_review_pdf_hubei"
    if level.startswith("G4-"):
        return "blocked_manual_image_pdf_hubei"
    if level.startswith("G5-"):
        return "blocked_school_backlink_pdf_hubei"
    return "blocked_regular_pdf_hubei"


def main_blocker(row):
    status = clean(row.get("事实准出状态"))
    if status == "ready_for_private_writeback_review":
        return "no_blocker_private_writeback_review_ready"
    if "w0_b0" in status:
        return "W0/B0核心事实仍缺PDF原页与湖北官方侧闭环"
    if "b0_companion" in status:
        return "B0同页伴生事实仍缺冲突处理、PDF原页与湖北官方侧闭环"
    if "structure" in status:
        return "结构事实仍缺PDF原页与湖北官方侧闭环"
    if "double_review" in status:
        return "双人复核事实仍缺复核、PDF原页与湖北官方侧闭环"
    if "manual_image" in status:
        return "人工看图事实仍缺PDF原页与湖北官方侧闭环"
    if "school_backlink" in status:
        return "高校源回接事实仍缺湖北官方侧闭环"
    return "常规事实仍缺PDF原页与湖北官方侧闭环"


def missing_list(pdf_done, hubei_done, school_done, conflict_done, double_done, three_way_done, major_done, group_done):
    missing = []
    if not pdf_done:
        missing.append("PDF原页")
    if not hubei_done:
        missing.append("湖北官方侧")
    if not school_done:
        missing.append("高校辅证")
    if not conflict_done:
        missing.append("冲突处理")
    if not double_done:
        missing.append("双人复核")
    if not three_way_done:
        missing.append("三方闭环")
    if not major_done:
        missing.append("专业名归属")
    if not group_done:
        missing.append("专业组边界")
    return "；".join(missing)


def assert_public_safe(rows, label):
    text = json.dumps(rows, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"{label} contains forbidden public tokens: {hits[:8]}")


def official_can_finalize(snapshot, key):
    section = snapshot.get(key, {})
    return bool(section.get("can_finalize"))


def sort_page_key(page_key):
    first = page_key.split("-", 1)[0]
    return (as_int(first), page_key)


def build_rows():
    fact_gate_rows = read_csv(FACT_GATE)
    fact_scope_rows = read_csv(FACT_SCOPE)
    field_fact_rows = read_csv(FIELD_FACT)
    result_rows = read_csv(VERIFICATION_RESULT)
    evidence_rows = read_csv(EVIDENCE_STATUS)
    next_action_rows = read_csv(NEXT_ACTION)
    p0_rows = read_csv(P0_THREE_WAY)
    school_rows = read_csv(SCHOOL_RECONCILIATION)
    backlink_rows = read_csv(FIELD_BACKLINK)
    official_snapshot = json.loads(OFFICIAL_PUBLIC_STATUS.read_text(encoding="utf-8"))

    scope_by_fact = index_unique(fact_scope_rows, "第一闭环事实范围缺口公开账本ID")
    field_fact_by_task_field = index_by_task_field(field_fact_rows, "字段名")
    result_by_task = index_by_task(result_rows)
    evidence_by_task = index_by_task(evidence_rows)
    next_by_task = index_by_task(next_action_rows)
    p0_by_task_field = index_by_task_field(p0_rows, "字段名")
    backlink_by_fact = index_unique(backlink_rows, "第一闭环事实范围缺口公开账本ID")
    school_by_code = group_by(school_rows, "院校代码")

    official_page_can_finalize = official_can_finalize(official_snapshot, "official_plan_page")
    platform_can_finalize = official_can_finalize(official_snapshot, "zspt_platform")
    official_status = clean(official_snapshot.get("status"))

    rows = []
    for index, gate in enumerate(fact_gate_rows, start=1):
        fact_id = clean(gate.get("第一闭环事实范围缺口公开账本ID"))
        task_id = clean(gate.get("稳定基座第一闭环明细任务ID"))
        field_name = clean(gate.get("字段类别"))
        domain = clean(gate.get("事实域"))
        fact_scope = scope_by_fact.get(fact_id, {})
        field_fact = field_fact_by_task_field.get((task_id, field_name), {}) if domain == "字段事实" else {}
        result = result_by_task.get(task_id, {})
        evidence = evidence_by_task.get(task_id, {})
        next_action = next_by_task.get(task_id, {})
        p0 = p0_by_task_field.get((task_id, field_name), {}) if domain == "字段事实" else {}
        backlink = backlink_by_fact.get(fact_id, {})
        school_matches = school_by_code.get(clean(gate.get("院校代码")), [])
        status = gate_status(gate)

        pdf_state = (
            clean(evidence.get("PDF原页证据状态"))
            or clean(result.get("PDF原页证据状态"))
            or clean(gate.get("PDF原页准入状态"))
        )
        hubei_state = (
            clean(evidence.get("湖北官方侧状态"))
            or clean(result.get("湖北官方侧状态"))
            or clean(gate.get("湖北官方侧准入状态"))
        )
        school_state = (
            clean(evidence.get("高校辅证证据状态"))
            or clean(result.get("高校辅证证据状态"))
            or clean(gate.get("高校源准入状态"))
        )
        conflict_state = (
            clean(evidence.get("冲突状态"))
            or clean(result.get("冲突状态"))
            or clean(gate.get("冲突处理准入状态"))
        )
        double_state = clean(gate.get("双人复核准入状态"))
        three_way_state = (
            clean(evidence.get("三方闭环状态"))
            or clean(result.get("三方闭环状态"))
            or clean(gate.get("三方闭环准入状态"))
        )
        writeback_state = (
            clean(field_fact.get("字段写回评估门禁"))
            or clean(evidence.get("字段写回门禁"))
            or clean(gate.get("写回评审准入状态"))
        )
        p0_three_state = clean(p0.get("三方字段一致性状态")) or "not_in_p0_three_way_scope"

        pdf_done = completed(pdf_state)
        hubei_done = completed(hubei_state) and official_page_can_finalize and platform_can_finalize
        school_required = needs_school(gate, backlink, next_action)
        school_done = True if not school_required else completed(school_state)
        conflict_required = (
            clean(gate.get("是否存在PDFOCR与高校冲突")) == "true"
            or clean(evidence.get("是否存在PDFOCR与高校冲突")) == "true"
            or clean(gate.get("B0冲突闭环状态")).startswith("R0-")
        )
        conflict_done = True if not conflict_required else completed(conflict_state)
        double_required = (
            clean(gate.get("是否需要双人复核")) == "true"
            or clean(evidence.get("是否需要双人复核")) == "true"
        )
        double_done = True if not double_required else completed(double_state)
        three_way_done = completed(three_way_state)
        writeback_done = completed(writeback_state)
        major_done = domain != "专业名归属" or (pdf_done and hubei_done)
        group_done = domain != "专业组边界" or (pdf_done and hubei_done)
        ready_private = (
            pdf_done
            and hubei_done
            and school_done
            and conflict_done
            and double_done
            and three_way_done
            and major_done
            and group_done
        )
        if ready_private:
            status = "ready_for_private_writeback_review"

        gaps = missing_list(
            pdf_done,
            hubei_done,
            school_done,
            conflict_done,
            double_done,
            three_way_done,
            major_done,
            group_done,
        )
        row = {
            "事实准出门禁ID": stable_id("FCFACTRESGATE", [SOURCE_PDF_SHA256, fact_id]),
            "来源第一闭环事实准入门禁账本": source_path(FACT_GATE),
            "来源第一闭环事实范围缺口账本": source_path(FACT_SCOPE),
            "来源第一闭环字段事实公开账本": source_path(FIELD_FACT),
            "来源第一闭环核验结果看板": source_path(VERIFICATION_RESULT),
            "来源第一闭环证据状态账本": source_path(EVIDENCE_STATUS),
            "来源第一闭环下一步动作矩阵": source_path(NEXT_ACTION),
            "来源P0即时三方闭环公开账本": source_path(P0_THREE_WAY),
            "来源高校源最新对齐账本": source_path(SCHOOL_RECONCILIATION),
            "来源W0B0高校源字段回接队列": source_path(FIELD_BACKLINK),
            "来源湖北官方公开入口状态快照": source_path(OFFICIAL_PUBLIC_STATUS),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环事实范围缺口×事实准出门禁",
            "任务粒度": "事实范围缺口×PDF原页×湖北官方侧×高校辅证×冲突/复核/三方闭环",
            **{field: "false" for field in FALSE_FIELDS},
            "准出序号": index,
            "第一闭环事实准入门禁ID": gate.get("第一闭环事实准入门禁ID", ""),
            "第一闭环事实范围缺口公开账本ID": fact_id,
            "第一闭环字段事实公开账本ID": field_fact.get("第一闭环字段事实公开账本ID", ""),
            "第一闭环核验结果ID": result.get("第一闭环核验结果ID", gate.get("第一闭环核验结果ID", "")),
            "第一闭环证据状态公开账本ID": evidence.get("第一闭环证据状态公开账本ID", ""),
            "第一闭环下一步动作ID": next_action.get("第一闭环下一步动作ID", ""),
            "P0即时三方闭环公开账本ID": p0.get("P0即时三方闭环公开账本ID", ""),
            "高校源字段回接队列ID": backlink.get("高校源字段回接队列ID", ""),
            "稳定基座第一闭环明细任务ID": task_id,
            "稳定基座第一闭环页列包ID": gate.get("稳定基座第一闭环页列包ID", ""),
            "页码版面键": gate.get("页码版面键", ""),
            "来源页码": gate.get("来源页码", ""),
            "版面列": gate.get("版面列", ""),
            "专业行ID": gate.get("专业行ID", ""),
            "专业组出现ID": gate.get("专业组出现ID", ""),
            "院校代码": gate.get("院校代码", ""),
            "事实域": domain,
            "事实类型": gate.get("事实类型", ""),
            "事实粒度": clean(fact_scope.get("事实粒度")) or gate.get("事实粒度", ""),
            "字段类别": field_name,
            "执行泳道": clean(evidence.get("执行泳道")) or gate.get("执行泳道", ""),
            "核验动作层级": clean(gate.get("核验动作层级")) or clean(result.get("核验动作层级")),
            "第一闭环页列优先级": clean(result.get("第一闭环页列优先级")) or gate.get("第一闭环页列优先级", ""),
            "事实准出状态": status,
            "事实准出阻断等级": gate.get("准入阻断等级", ""),
            "事实准出主阻断": "",
            "事实准出缺口清单": gaps,
            "事实准出完成条件": "PDF原页、湖北官方侧、必要高校辅证、冲突处理、双人复核、三方闭环均完成后，仅可进入私有写回评审；仍不得直接用于推荐。",
            "PDF原页证据状态": pdf_state,
            "湖北官方侧证据状态": hubei_state,
            "高校辅证证据状态": school_state,
            "冲突处理状态": conflict_state,
            "双人复核状态": double_state,
            "三方闭环状态": three_way_state,
            "字段写回评审状态": writeback_state,
            "专业名归属状态": "pending_pdf_hubei_closure" if domain == "专业名归属" else "not_applicable",
            "专业组边界状态": "pending_pdf_hubei_closure" if domain == "专业组边界" else "not_applicable",
            "高校源字段回接状态": "field_backlink_queue_ready" if backlink else "not_in_field_backlink_queue",
            "同校高校源最新对齐记录数": len(school_matches),
            "同校高校源最高证据层级": clean(next_action.get("同校高校源最高证据层级")),
            "P0三方闭环状态": p0_three_state,
            "官方公开计划页可定稿": yes_no(official_page_can_finalize),
            "数智平台可定稿": yes_no(platform_can_finalize),
            "湖北官方公开入口状态": official_status,
            "是否PDF原页已核": yes_no(pdf_done),
            "是否湖北官方侧已核": yes_no(hubei_done),
            "是否高校辅证必要且已核": yes_no(school_done),
            "是否冲突已闭环": yes_no(conflict_done),
            "是否双人复核已完成": yes_no(double_done),
            "是否三方闭环完成": yes_no(three_way_done),
            "是否字段写回评审完成": yes_no(writeback_done),
            "是否可进入私有写回评审": yes_no(ready_private),
            "是否仍需PDF原页": yes_no(not pdf_done),
            "是否仍需湖北官方侧": yes_no(not hubei_done),
            "是否仍需高校辅证": yes_no(not school_done),
            "是否仍需冲突处理": yes_no(not conflict_done),
            "是否仍需双人复核": yes_no(not double_done),
            "是否仍需三方闭环": yes_no(not three_way_done),
            "是否仍需专业名归属": yes_no(not major_done),
            "是否仍需专业组边界": yes_no(not group_done),
            "下一步事实准出动作": "先补PDF原页和湖北官方侧记录；高校源只作double check提示；完成后再做私有写回评审。",
            "公开安全策略": public_policy(),
        }
        row["事实准出主阻断"] = main_blocker(row)
        rows.append(row)

    return rows


def summarize_page(rows):
    rows_by_page = group_by(rows, "页码版面键")
    page_rows = []
    for index, page_key in enumerate(sorted(rows_by_page, key=sort_page_key), start=1):
        items = rows_by_page[page_key]
        first = items[0]
        page_rows.append({
            "事实准出页列汇总ID": stable_id("FCFACTRESPAGE", [SOURCE_PDF_SHA256, page_key]),
            "来源事实准出门禁账本": source_path(OUTPUT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环事实准出页列汇总",
            "任务粒度": "PDF页码×版面列×事实准出门禁",
            **{field: "false" for field in FALSE_FIELDS},
            "页列汇总序号": index,
            "页码版面键": page_key,
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "事实范围数": len(items),
            "字段事实数": aggregate(items, "事实域", "字段事实"),
            "专业名归属事实数": aggregate(items, "事实域", "专业名归属"),
            "专业组边界事实数": aggregate(items, "事实域", "专业组边界"),
            "涉及任务数": len({row["稳定基座第一闭环明细任务ID"] for row in items if row["稳定基座第一闭环明细任务ID"]}),
            "涉及院校代码数": len({row["院校代码"] for row in items if row["院校代码"]}),
            "事实准出状态分布": counter_text(items, "事实准出状态"),
            "事实准出阻断等级分布": counter_text(items, "事实准出阻断等级"),
            "事实类型分布": counter_text(items, "事实类型"),
            "PDF待补事实数": aggregate(items, "是否仍需PDF原页", "true"),
            "湖北官方待补事实数": aggregate(items, "是否仍需湖北官方侧", "true"),
            "高校辅证待补事实数": aggregate(items, "是否仍需高校辅证", "true"),
            "冲突待处理事实数": aggregate(items, "是否仍需冲突处理", "true"),
            "双人复核待完成事实数": aggregate(items, "是否仍需双人复核", "true"),
            "三方闭环待完成事实数": aggregate(items, "是否仍需三方闭环", "true"),
            "专业名归属待闭环事实数": aggregate(items, "是否仍需专业名归属", "true"),
            "专业组边界待闭环事实数": aggregate(items, "是否仍需专业组边界", "true"),
            "可进入私有写回评审事实数": aggregate(items, "是否可进入私有写回评审", "true"),
            "事实集合SHA16": sha16(row["第一闭环事实范围缺口公开账本ID"] for row in items),
            "任务集合SHA16": sha16(row["稳定基座第一闭环明细任务ID"] for row in items),
            "院校代码集合SHA16": sha16(row["院校代码"] for row in items),
            "页列准出动作": "页列内事实仍缺PDF原页和湖北官方侧闭环；不得写回字段事实或生成推荐。",
            "公开安全策略": public_policy(),
        })
    return page_rows


def summarize_task(rows):
    rows_by_task = group_by([row for row in rows if clean(row.get("稳定基座第一闭环明细任务ID"))], "稳定基座第一闭环明细任务ID")
    task_rows = []
    for index, task_id in enumerate(sorted(rows_by_task), start=1):
        items = rows_by_task[task_id]
        first = items[0]
        task_rows.append({
            "事实准出任务汇总ID": stable_id("FCFACTRESTASK", [SOURCE_PDF_SHA256, task_id]),
            "来源事实准出门禁账本": source_path(OUTPUT),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环事实准出任务汇总",
            "任务粒度": "稳定基座第一闭环明细任务ID×事实准出门禁",
            **{field: "false" for field in FALSE_FIELDS},
            "任务汇总序号": index,
            "稳定基座第一闭环明细任务ID": task_id,
            "第一闭环核验结果ID": first.get("第一闭环核验结果ID", ""),
            "第一闭环证据状态公开账本ID": first.get("第一闭环证据状态公开账本ID", ""),
            "第一闭环下一步动作ID": first.get("第一闭环下一步动作ID", ""),
            "稳定基座第一闭环页列包ID": first.get("稳定基座第一闭环页列包ID", ""),
            "页码版面键": first.get("页码版面键", ""),
            "来源页码": first.get("来源页码", ""),
            "版面列": first.get("版面列", ""),
            "专业行ID": first.get("专业行ID", ""),
            "专业组出现ID": first.get("专业组出现ID", ""),
            "院校代码": first.get("院校代码", ""),
            "字段名": first.get("字段类别", ""),
            "执行泳道": first.get("执行泳道", ""),
            "核验动作层级": first.get("核验动作层级", ""),
            "第一闭环页列优先级": first.get("第一闭环页列优先级", ""),
            "事实范围数": len(items),
            "字段事实数": aggregate(items, "事实域", "字段事实"),
            "专业名归属事实数": aggregate(items, "事实域", "专业名归属"),
            "专业组边界事实数": aggregate(items, "事实域", "专业组边界"),
            "事实准出状态分布": counter_text(items, "事实准出状态"),
            "事实准出阻断等级分布": counter_text(items, "事实准出阻断等级"),
            "事实类型分布": counter_text(items, "事实类型"),
            "PDF待补事实数": aggregate(items, "是否仍需PDF原页", "true"),
            "湖北官方待补事实数": aggregate(items, "是否仍需湖北官方侧", "true"),
            "高校辅证待补事实数": aggregate(items, "是否仍需高校辅证", "true"),
            "冲突待处理事实数": aggregate(items, "是否仍需冲突处理", "true"),
            "双人复核待完成事实数": aggregate(items, "是否仍需双人复核", "true"),
            "三方闭环待完成事实数": aggregate(items, "是否仍需三方闭环", "true"),
            "可进入私有写回评审事实数": aggregate(items, "是否可进入私有写回评审", "true"),
            "事实集合SHA16": sha16(row["第一闭环事实范围缺口公开账本ID"] for row in items),
            "任务准出动作": "任务内事实仍缺PDF原页和湖北官方侧闭环；不得写回字段事实或生成推荐。",
            "公开安全策略": public_policy(),
        })
    return task_rows


def main():
    rows = build_rows()
    page_rows = summarize_page(rows)
    task_rows = summarize_task(rows)

    assert_public_safe(rows, "fact_resolution_gate")
    assert_public_safe(page_rows, "fact_resolution_gate_page")
    assert_public_safe(task_rows, "fact_resolution_gate_task")

    write_csv(OUTPUT, rows, LEDGER_FIELDS)
    write_csv(PAGE_OUTPUT, page_rows, PAGE_FIELDS)
    write_csv(TASK_OUTPUT, task_rows, TASK_FIELDS)

    summary = {
        "status": "issue19_first_closure_fact_resolution_gate_v1_ready_not_final",
        "generated_by": "build_issue19_first_closure_fact_resolution_gate_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_fact_gate": source_path(FACT_GATE),
        "source_fact_scope": source_path(FACT_SCOPE),
        "source_field_fact": source_path(FIELD_FACT),
        "source_verification_result": source_path(VERIFICATION_RESULT),
        "source_evidence_status": source_path(EVIDENCE_STATUS),
        "source_next_action": source_path(NEXT_ACTION),
        "source_p0_three_way": source_path(P0_THREE_WAY),
        "source_school_reconciliation": source_path(SCHOOL_RECONCILIATION),
        "source_field_backlink": source_path(FIELD_BACKLINK),
        "source_official_public_status": source_path(OFFICIAL_PUBLIC_STATUS),
        "output": source_path(OUTPUT),
        "page_output": source_path(PAGE_OUTPUT),
        "task_output": source_path(TASK_OUTPUT),
        "fact_resolution_row_count": len(rows),
        "page_summary_row_count": len(page_rows),
        "task_summary_row_count": len(task_rows),
        "task_summary_fact_count": sum(as_int(row["事实范围数"]) for row in task_rows),
        "task_absent_fact_count": sum(not bool(row["稳定基座第一闭环明细任务ID"]) for row in rows),
        "unique_fact_scope_count": len({row["第一闭环事实范围缺口公开账本ID"] for row in rows}),
        "unique_page_side_count": len({row["页码版面键"] for row in rows}),
        "unique_task_count": len({row["稳定基座第一闭环明细任务ID"] for row in rows if row["稳定基座第一闭环明细任务ID"]}),
        "fact_domain_counts": dict(Counter(row["事实域"] for row in rows)),
        "fact_type_counts": dict(Counter(row["事实类型"] for row in rows)),
        "field_category_counts": dict(Counter(
            row["字段类别"]
            for row in rows
            if row["事实域"] == "字段事实" and row["字段类别"]
        )),
        "resolution_status_counts": dict(Counter(row["事实准出状态"] for row in rows)),
        "resolution_blocker_counts": dict(Counter(row["事实准出阻断等级"] for row in rows)),
        "missing_pdf_count": sum(row["是否仍需PDF原页"] == "true" for row in rows),
        "missing_hubei_official_count": sum(row["是否仍需湖北官方侧"] == "true" for row in rows),
        "missing_school_source_count": sum(row["是否仍需高校辅证"] == "true" for row in rows),
        "missing_conflict_count": sum(row["是否仍需冲突处理"] == "true" for row in rows),
        "missing_double_review_count": sum(row["是否仍需双人复核"] == "true" for row in rows),
        "missing_three_way_count": sum(row["是否仍需三方闭环"] == "true" for row in rows),
        "missing_major_assignment_count": sum(row["是否仍需专业名归属"] == "true" for row in rows),
        "missing_group_boundary_count": sum(row["是否仍需专业组边界"] == "true" for row in rows),
        "private_writeback_review_ready_count": sum(row["是否可进入私有写回评审"] == "true" for row in rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段事实"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "official_plan_replacement_allowed_count": sum(row["是否允许官网证据替代湖北官方计划"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "policy": "本账本只做第一闭环事实准出门禁，不公开字段值，不确认事实，不替代湖北官方计划，不进入推荐。",
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
