#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

IMMEDIATE_PACKET = ROOT / "data/working/issue19-field-fact-p0-immediate-review-packet.csv"
CROP_INDEX = ROOT / "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv"
THREE_WAY_LEDGER = ROOT / "data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv"
CROP_OCR_AUDIT = ROOT / "data/working/issue19-p0-immediate-crop-ocr-public-audit.csv"
PRIVATE_CROP_OCR_READING = (
    ROOT
    / "private/review-assets/issue19-p0-immediate-crop-ocr-audit/crop-ocr-readings-private.csv"
)

OUTPUT = ROOT / "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-p0-immediate-field-confirmation-public-ledger-summary.json"

PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-p0-immediate-field-confirmation"
PRIVATE_OUTPUT = PRIVATE_OUTPUT_DIR / "field-confirmation-private-workbench.csv"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_p0_immediate_field_confirmation_public_ledger"


FIELDS = [
    "P0即时字段确认公开账本ID",
    "来源P0字段即时复核包",
    "来源P0裁图证据索引",
    "来源P0即时三方闭环公开账本",
    "来源P0即时裁图OCR公开审计",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动回填候选",
    "是否允许写回字段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "字段确认公开账本总序",
    "人工核验优先级数值",
    "人工核验泳道",
    "人工核验方式",
    "人工核验动作",
    "必须完成证据步骤",
    "公开升级阻断原因",
    "字段名",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "来源页码",
    "版面列",
    "P0字段即时复核任务ID",
    "P0即时复核裁图证据索引ID",
    "P0即时三方闭环公开账本ID",
    "P0即时裁图OCR公开审计ID",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图规格SHA256",
    "裁图bbox归一化",
    "裁图bbox像素",
    "执行批次",
    "即时复核阶段",
    "语义多源优先桶",
    "裁图OCR三方辅助桶",
    "裁图OCR候选状态",
    "裁图OCR候选置信等级",
    "裁图OCR平均置信度区间",
    "裁图OCR目标行定位状态",
    "裁图OCR与机器候选关系",
    "裁图OCR与高校辅证关系",
    "机器候选状态",
    "机器候选置信等级",
    "机器候选与高校辅证关系",
    "高校官网辅证覆盖状态",
    "高校官网证据强度",
    "高校官网证据匹配状态",
    "高校官网来源状态",
    "高校官网是否可替代湖北官方计划",
    "是否有机器规范候选",
    "是否有高校字段线索",
    "是否裁图OCR有可比候选",
    "是否裁图OCR与机器候选冲突",
    "是否裁图OCR与高校辅证冲突",
    "是否机器高校冲突",
    "是否高校补缺线索",
    "是否需要双人复核",
    "PDF原页私有记录状态",
    "湖北官方私有记录状态",
    "高校辅证私有记录状态",
    "双人复核公开状态",
    "三方字段一致性公开状态",
    "字段事实写回评估状态",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "私有字段确认工作台状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_FIELDS = FIELDS + [
    "私有工作台用途",
    "机器候选字段值",
    "机器候选规范值",
    "高校官网字段候选值",
    "高校官网字段规范值",
    "裁图OCR候选字段值",
    "裁图OCR候选规范值",
    "裁图OCR候选行文本",
    "裁图OCR候选行序号",
    "裁图OCR候选置信度",
    "私有OCR图片本地路径",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "PDF核页复核人A",
    "PDF核页复核人B",
    "湖北官方核验人",
    "高校辅证核验人",
    "人工复核备注",
]

PRIVATE_MANUAL_FIELDS = [
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "PDF核页复核人A",
    "PDF核页复核人B",
    "湖北官方核验人",
    "高校辅证核验人",
    "人工复核备注",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def bool_text(value):
    return "true" if str(value).strip().lower() == "true" else "false"


def nonempty(value):
    return bool(str(value or "").strip())


def read_optional_private_rows(path, key_field):
    if not path.exists():
        return {}
    return {row.get(key_field, ""): row for row in read_csv(path)}


def normalize_value(field_name, value):
    text = str(value or "").strip()
    if not text:
        return ""
    if field_name in {"专业计划数", "学费"}:
        return "".join(re.findall(r"\d+", text))
    compact = re.sub(r"[\s\[\]【】（）()「」『』；:：、,，。·/|\\-]", "", text)
    if "不限" in compact:
        return "不限"
    for subject in ["化学", "生物", "地理"]:
        if subject in compact:
            return subject
    if "思想政治" in compact or "政治" in compact:
        return "政治"
    return compact


def review_priority(immediate, ledger, crop_ocr):
    crop_machine_conflict = crop_ocr.get("是否裁图OCR与机器候选冲突") == "true"
    crop_school_conflict = crop_ocr.get("是否裁图OCR与高校辅证冲突") == "true"
    machine_school_conflict = ledger.get("是否机器高校冲突") == "true"
    no_crop_candidate = crop_ocr.get("是否裁图OCR有可比候选") != "true"
    crop_helper = crop_ocr.get("裁图OCR三方辅助桶", "")

    if crop_machine_conflict or crop_school_conflict or machine_school_conflict:
        return 10, "M0-冲突优先双人核页", "双人复核", "先核PDF原页，再核湖北官方，最后对照高校辅证"
    if immediate.get("执行批次") == "EXEC-02-计划数偏大重点核页":
        return 20, "M1-计划数偏大重点核页", "双人复核", "先核PDF原页计划数列，再核湖北官方计划数"
    if no_crop_candidate:
        return 30, "M2-裁图OCR未稳定补读人工看图", "双人复核", "直接回看PDF原页裁图和整页上下文"
    if crop_helper == "A1-裁图OCR与既有线索一致但仍待三方核验":
        return 40, "M3-多源一致快速三方核验", "三方线索优先核验", "核PDF原页和湖北官方，确认高校辅证只能作辅助"
    if ledger.get("是否高校补缺线索") == "true":
        return 50, "M4-高校补缺线索核PDF", "三方线索优先核验", "先用高校线索定位字段，再回PDF原页和湖北官方"
    if immediate.get("是否需要双人复核") == "true":
        return 60, "M5-多值或双人复核常规核页", "双人复核", "核PDF原页，必要时对照裁图OCR候选位置"
    return 70, "M6-常规人工核页", "单人初核加抽检", "核PDF原页后等待湖北官方复核"


def required_steps(ledger, crop_ocr):
    steps = ["PDF原页人工核页", "湖北官方系统或省招办计划核验"]
    if ledger.get("是否有高校字段线索") == "true" or crop_ocr.get("是否有高校字段线索") == "true":
        steps.append("高校官网或招生章程辅证对照")
    if ledger.get("是否需要双人复核") == "true" or crop_ocr.get("是否需要双人复核") == "true":
        steps.append("双人复核")
    return "；".join(steps)


def private_seed_row(public_id, immediate, crop_ocr, existing_private, private_crop_ocr):
    row = {
        "私有工作台用途": "仅供本地人工记录字段读数和证据位置；不得提交公开仓库。",
        "机器候选字段值": immediate.get("机器候选字段值", ""),
        "机器候选规范值": immediate.get("机器候选规范值", ""),
        "高校官网字段候选值": immediate.get("高校官网字段候选值", ""),
        "高校官网字段规范值": immediate.get("高校官网字段规范值", ""),
        "裁图OCR候选字段值": private_crop_ocr.get("裁图OCR候选字段值", ""),
        "裁图OCR候选规范值": private_crop_ocr.get("裁图OCR候选规范值", ""),
        "裁图OCR候选行文本": private_crop_ocr.get("裁图OCR候选行文本", ""),
        "裁图OCR候选行序号": private_crop_ocr.get("裁图OCR候选行序号", ""),
        "裁图OCR候选置信度": private_crop_ocr.get("裁图OCR候选置信度", ""),
        "私有OCR图片本地路径": private_crop_ocr.get("私有OCR图片本地路径", ""),
    }
    for field in PRIVATE_MANUAL_FIELDS:
        row[field] = existing_private.get(field, "")
    return row


def confirmation_state(field_name, ledger, crop_ocr, private_row, force_double_review=False):
    pdf_value = private_row.get("PDF原页人工读数", "")
    hubei_value = private_row.get("湖北官方字段值", "")
    school_value = private_row.get("高校官网或招生章程字段值", "")
    reviewer_a = private_row.get("PDF核页复核人A", "")
    reviewer_b = private_row.get("PDF核页复核人B", "")

    school_required = ledger.get("是否有高校字段线索") == "true" or crop_ocr.get("是否有高校字段线索") == "true"
    double_required = (
        force_double_review
        or ledger.get("是否需要双人复核") == "true"
        or crop_ocr.get("是否需要双人复核") == "true"
    )
    has_pdf = nonempty(pdf_value)
    has_hubei = nonempty(hubei_value)
    has_school = nonempty(school_value)
    double_done = (not double_required) or (nonempty(reviewer_a) and nonempty(reviewer_b) and reviewer_a != reviewer_b)

    pdf_status = "private_pdf_reading_recorded" if has_pdf else "pending_private_pdf_reading"
    hubei_status = "private_hubei_reading_recorded" if has_hubei else "pending_private_hubei_reading"
    if school_required:
        school_status = "private_school_reading_recorded" if has_school else "pending_private_school_reading"
    else:
        school_status = "not_applicable_no_school_field_clue"
    double_status = (
        "double_review_not_required"
        if not double_required
        else ("double_review_recorded" if double_done else "pending_double_review")
    )

    values = [normalize_value(field_name, pdf_value), normalize_value(field_name, hubei_value)]
    if school_required:
        values.append(normalize_value(field_name, school_value))
    comparable_values = [value for value in values if value]
    has_required_values = has_pdf and has_hubei and (has_school if school_required else True)
    conflict = len(set(comparable_values)) > 1 if has_required_values else False

    if conflict:
        consistency = "blocked_conflict_needs_manual_resolution"
        writeback = "blocked_conflict_needs_manual_resolution"
    elif has_required_values and double_done:
        consistency = "private_readings_consistent_pending_field_writeback_review"
        writeback = "ready_for_manual_field_writeback_review"
    else:
        consistency = "pending_private_three_way_field_confirmation"
        writeback = "blocked_until_required_private_readings_complete"

    reasons = []
    if not has_pdf:
        reasons.append("PDF原页私有记录未完成")
    if not has_hubei:
        reasons.append("湖北官方私有记录未完成")
    if school_required and not has_school:
        reasons.append("高校辅证私有记录未完成")
    if double_required and not double_done:
        reasons.append("双人复核未完成")
    if conflict:
        reasons.append("三方或双方读数冲突待人工裁决")
    if not reasons:
        reasons.append("等待读写回前人工复查")

    return {
        "PDF原页私有记录状态": pdf_status,
        "湖北官方私有记录状态": hubei_status,
        "高校辅证私有记录状态": school_status,
        "双人复核公开状态": double_status,
        "三方字段一致性公开状态": consistency,
        "字段事实写回评估状态": writeback,
        "公开升级阻断原因": "；".join(reasons),
        "has_required_values": has_required_values,
        "double_done": double_done,
        "conflict": conflict,
    }


def build_rows():
    immediate_rows = read_csv(IMMEDIATE_PACKET)
    crop_by_task = {row["来源P0字段即时复核任务ID"]: row for row in read_csv(CROP_INDEX)}
    ledger_by_task = {row["P0字段即时复核任务ID"]: row for row in read_csv(THREE_WAY_LEDGER)}
    crop_ocr_by_task = {row["P0字段即时复核任务ID"]: row for row in read_csv(CROP_OCR_AUDIT)}
    private_crop_ocr_by_id = read_optional_private_rows(PRIVATE_CROP_OCR_READING, "P0即时裁图OCR公开审计ID")
    existing_private_by_public_id = read_optional_private_rows(PRIVATE_OUTPUT, "P0即时字段确认公开账本ID")

    sortable = []
    for index, immediate in enumerate(immediate_rows, start=1):
        task_id = immediate["P0字段即时复核任务ID"]
        crop = crop_by_task.get(task_id)
        ledger = ledger_by_task.get(task_id)
        crop_ocr = crop_ocr_by_task.get(task_id)
        if not crop or not ledger or not crop_ocr:
            raise ValueError(f"P0即时任务缺少下游证据链: {task_id}")
        for source_name, source_row in [("裁图索引", crop), ("三方账本", ledger), ("裁图OCR审计", crop_ocr)]:
            if source_row.get("专业行ID") != immediate.get("专业行ID") or source_row.get("字段名") != immediate.get("字段名"):
                raise ValueError(f"{source_name} 与即时任务主键不一致: {task_id}")
        priority, lane, mode, action = review_priority(immediate, ledger, crop_ocr)
        sortable.append((priority, int(immediate.get("执行总序", index)), task_id, immediate, crop, ledger, crop_ocr, lane, mode, action))

    public_rows = []
    private_rows = []
    for queue_index, item in enumerate(sorted(sortable), start=1):
        priority, _, _, immediate, crop, ledger, crop_ocr, lane, mode, action = item
        public_id = stable_id(
            "P0FCONF",
            [
                immediate.get("P0字段即时复核任务ID", ""),
                immediate.get("专业行ID", ""),
                immediate.get("字段名", ""),
            ],
        )
        private_crop_ocr = private_crop_ocr_by_id.get(crop_ocr.get("P0即时裁图OCR公开审计ID", ""), {})
        existing_private = existing_private_by_public_id.get(public_id, {})
        private_extra = private_seed_row(public_id, immediate, crop_ocr, existing_private, private_crop_ocr)
        force_double_review = "双人" in mode
        state = confirmation_state(
            immediate.get("字段名", ""),
            ledger,
            crop_ocr,
            private_extra,
            force_double_review=force_double_review,
        )
        writeback_allowed = state["字段事实写回评估状态"] == "ready_for_manual_field_writeback_review"
        public_row = {
            "P0即时字段确认公开账本ID": public_id,
            "来源P0字段即时复核包": "data/working/issue19-field-fact-p0-immediate-review-packet.csv",
            "来源P0裁图证据索引": "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv",
            "来源P0即时三方闭环公开账本": "data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv",
            "来源P0即时裁图OCR公开审计": "data/working/issue19-p0-immediate-crop-ocr-public-audit.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0字段×字段确认公开状态",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "true" if writeback_allowed else "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "字段确认公开账本总序": str(queue_index),
            "人工核验优先级数值": str(priority),
            "人工核验泳道": lane,
            "人工核验方式": mode,
            "人工核验动作": action,
            "必须完成证据步骤": required_steps(ledger, crop_ocr),
            "公开升级阻断原因": state["公开升级阻断原因"],
            "字段名": immediate.get("字段名", ""),
            "专业行ID": immediate.get("专业行ID", ""),
            "专业组出现ID": immediate.get("专业组出现ID", ""),
            "院校代码": immediate.get("院校代码", ""),
            "来源页码": immediate.get("来源页码", ""),
            "版面列": immediate.get("版面列", ""),
            "P0字段即时复核任务ID": immediate.get("P0字段即时复核任务ID", ""),
            "P0即时复核裁图证据索引ID": crop.get("P0即时复核裁图证据索引ID", ""),
            "P0即时三方闭环公开账本ID": ledger.get("P0即时三方闭环公开账本ID", ""),
            "P0即时裁图OCR公开审计ID": crop_ocr.get("P0即时裁图OCR公开审计ID", ""),
            "裁图证据编号": crop.get("裁图证据编号", ""),
            "裁图文件SHA256": crop.get("裁图文件SHA256", ""),
            "裁图规格SHA256": crop.get("裁图规格SHA256", ""),
            "裁图bbox归一化": crop.get("裁图bbox归一化", ""),
            "裁图bbox像素": crop.get("裁图bbox像素", ""),
            "执行批次": immediate.get("执行批次", ""),
            "即时复核阶段": immediate.get("即时复核阶段", ""),
            "语义多源优先桶": immediate.get("语义多源优先桶", ""),
            "裁图OCR三方辅助桶": crop_ocr.get("裁图OCR三方辅助桶", ""),
            "裁图OCR候选状态": crop_ocr.get("裁图OCR候选状态", ""),
            "裁图OCR候选置信等级": crop_ocr.get("裁图OCR候选置信等级", ""),
            "裁图OCR平均置信度区间": crop_ocr.get("裁图OCR平均置信度区间", ""),
            "裁图OCR目标行定位状态": crop_ocr.get("裁图OCR目标行定位状态", ""),
            "裁图OCR与机器候选关系": crop_ocr.get("裁图OCR与机器候选关系", ""),
            "裁图OCR与高校辅证关系": crop_ocr.get("裁图OCR与高校辅证关系", ""),
            "机器候选状态": ledger.get("机器候选状态", ""),
            "机器候选置信等级": ledger.get("机器候选置信等级", ""),
            "机器候选与高校辅证关系": ledger.get("机器候选与高校辅证关系", ""),
            "高校官网辅证覆盖状态": ledger.get("高校官网辅证覆盖状态", ""),
            "高校官网证据强度": ledger.get("高校官网证据强度", ""),
            "高校官网证据匹配状态": ledger.get("高校官网证据匹配状态", ""),
            "高校官网来源状态": ledger.get("高校官网来源状态", ""),
            "高校官网是否可替代湖北官方计划": ledger.get("高校官网是否可替代湖北官方计划", ""),
            "是否有机器规范候选": bool_text(ledger.get("是否有机器规范候选", "")),
            "是否有高校字段线索": bool_text(ledger.get("是否有高校字段线索", "")),
            "是否裁图OCR有可比候选": bool_text(crop_ocr.get("是否裁图OCR有可比候选", "")),
            "是否裁图OCR与机器候选冲突": bool_text(crop_ocr.get("是否裁图OCR与机器候选冲突", "")),
            "是否裁图OCR与高校辅证冲突": bool_text(crop_ocr.get("是否裁图OCR与高校辅证冲突", "")),
            "是否机器高校冲突": bool_text(ledger.get("是否机器高校冲突", "")),
            "是否高校补缺线索": bool_text(ledger.get("是否高校补缺线索", "")),
            "是否需要双人复核": (
                "true"
                if ledger.get("是否需要双人复核") == "true"
                or crop_ocr.get("是否需要双人复核") == "true"
                or "双人" in mode
                else "false"
            ),
            "PDF原页私有记录状态": state["PDF原页私有记录状态"],
            "湖北官方私有记录状态": state["湖北官方私有记录状态"],
            "高校辅证私有记录状态": state["高校辅证私有记录状态"],
            "双人复核公开状态": state["双人复核公开状态"],
            "三方字段一致性公开状态": state["三方字段一致性公开状态"],
            "字段事实写回评估状态": state["字段事实写回评估状态"],
            "PDF原页核页状态": "pending_manual_pdf_review" if not state["has_required_values"] else "private_pdf_reading_recorded",
            "湖北官方系统或省招办计划核验状态": (
                "pending_hubei_official_review"
                if not nonempty(private_extra.get("湖北官方字段值"))
                else "private_hubei_reading_recorded"
            ),
            "高校官网或招生章程辅证状态": state["高校辅证私有记录状态"],
            "三方字段一致性状态": state["三方字段一致性公开状态"],
            "字段事实写回状态": state["字段事实写回评估状态"],
            "私有字段确认工作台状态": "private_field_confirmation_workbench_generated",
            "公开安全策略": "公开表只保存字段确认状态、证据编号、SHA、bbox、关系状态和门禁；不保存字段记录值、候选值、识别文本、图片路径、院校名、专业名、专业代号或专业组代码。",
            "下一步": "在私有字段确认工作台补齐PDF原页、湖北官方系统或省招办计划、高校官网或章程的私有字段记录；公开账本只同步状态，不同步记录值。",
        }
        public_rows.append(public_row)
        private_rows.append({**public_row, **private_extra})

    return public_rows, private_rows


def build_summary(public_rows):
    return {
        "status": "issue19_p0_immediate_field_confirmation_public_ledger_not_final",
        "generated_by": Path(__file__).name,
        "source_immediate_packet": "data/working/issue19-field-fact-p0-immediate-review-packet.csv",
        "source_crop_evidence_index": "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv",
        "source_three_way_ledger": "data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv",
        "source_crop_ocr_audit": "data/working/issue19-p0-immediate-crop-ocr-public-audit.csv",
        "output_table": "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv",
        "row_grain": "逐专业招生明细×P0字段×字段确认公开状态",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(public_rows),
        "private_field_confirmation_workbench_generated": True,
        "unique_public_ledger_id_count": len({row["P0即时字段确认公开账本ID"] for row in public_rows}),
        "unique_immediate_task_id_count": len({row["P0字段即时复核任务ID"] for row in public_rows}),
        "unique_crop_index_id_count": len({row["P0即时复核裁图证据索引ID"] for row in public_rows}),
        "unique_three_way_ledger_id_count": len({row["P0即时三方闭环公开账本ID"] for row in public_rows}),
        "unique_crop_ocr_audit_id_count": len({row["P0即时裁图OCR公开审计ID"] for row in public_rows}),
        "unique_major_field_pair_count": len({(row["专业行ID"], row["字段名"]) for row in public_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in public_rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in public_rows}),
        "field_counts": dict(Counter(row["字段名"] for row in public_rows)),
        "manual_review_lane_counts": dict(Counter(row["人工核验泳道"] for row in public_rows)),
        "manual_review_mode_counts": dict(Counter(row["人工核验方式"] for row in public_rows)),
        "execution_batch_counts": dict(Counter(row["执行批次"] for row in public_rows)),
        "crop_helper_bucket_counts": dict(Counter(row["裁图OCR三方辅助桶"] for row in public_rows)),
        "machine_school_relation_counts": dict(Counter(row["机器候选与高校辅证关系"] for row in public_rows)),
        "pdf_private_record_status_counts": dict(Counter(row["PDF原页私有记录状态"] for row in public_rows)),
        "hubei_private_record_status_counts": dict(Counter(row["湖北官方私有记录状态"] for row in public_rows)),
        "school_private_record_status_counts": dict(Counter(row["高校辅证私有记录状态"] for row in public_rows)),
        "double_review_status_counts": dict(Counter(row["双人复核公开状态"] for row in public_rows)),
        "three_way_public_status_counts": dict(Counter(row["三方字段一致性公开状态"] for row in public_rows)),
        "field_writeback_review_status_counts": dict(Counter(row["字段事实写回评估状态"] for row in public_rows)),
        "crop_machine_conflict_count": sum(row["是否裁图OCR与机器候选冲突"] == "true" for row in public_rows),
        "crop_school_conflict_count": sum(row["是否裁图OCR与高校辅证冲突"] == "true" for row in public_rows),
        "machine_school_conflict_count": sum(row["是否机器高校冲突"] == "true" for row in public_rows),
        "school_fill_clue_count": sum(row["是否高校补缺线索"] == "true" for row in public_rows),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in public_rows),
        "pdf_manual_review_pending_count": sum(row["PDF原页核页状态"] == "pending_manual_pdf_review" for row in public_rows),
        "hubei_official_review_pending_count": sum(row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_review" for row in public_rows),
        "three_way_closure_pending_count": sum(row["三方字段一致性状态"] == "pending_private_three_way_field_confirmation" for row in public_rows),
        "field_writeback_ready_count": sum(row["字段事实写回评估状态"] == "ready_for_manual_field_writeback_review" for row in public_rows),
        "field_conflict_blocked_count": sum(row["字段事实写回评估状态"] == "blocked_conflict_needs_manual_resolution" for row in public_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in public_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in public_rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段"] == "true" for row in public_rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in public_rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in public_rows),
        "public_safety_note": "公开字段确认账本只保存状态、证据编号、SHA、bbox、关系状态和门禁；不保存字段记录值、候选值、识别文本、图片路径、院校名、专业名、专业代号或专业组代码。",
    }


def main():
    public_rows, private_rows = build_rows()
    write_csv(OUTPUT, public_rows, FIELDS)
    write_csv(PRIVATE_OUTPUT, private_rows, PRIVATE_FIELDS)
    write_json(SUMMARY_OUTPUT, build_summary(public_rows))
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {PRIVATE_OUTPUT.relative_to(ROOT)}：{len(private_rows)} 行")


if __name__ == "__main__":
    main()
