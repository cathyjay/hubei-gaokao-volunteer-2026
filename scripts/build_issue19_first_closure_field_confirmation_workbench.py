#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIRST_TASK_REVIEW = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv"
)
FIRST_PDF_OCR_PUBLIC = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv"
)
FIRST_PDF_OCR_PRIVATE = (
    ROOT
    / "private/review-assets/issue19-stable-foundation-first-closure-pdf-ocr-candidates/first-closure-pdf-ocr-candidates-private.csv"
)
FIRST_MACHINE_PUBLIC = (
    ROOT
    / "data/working/issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit.csv"
)
FIRST_MACHINE_PRIVATE = (
    ROOT
    / "private/review-assets/issue19-stable-foundation-first-closure-machine-coordinate-candidates/first-closure-machine-coordinate-candidates-private.csv"
)
FIRST_PAGE_DASHBOARD = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-page-side-candidate-dashboard.csv"
)
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

OUTPUT = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv"
)
SUMMARY_OUTPUT = (
    ROOT
    / "data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger-summary.json"
)

PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-stable-foundation-first-closure-field-confirmation"
)
PRIVATE_OUTPUT = PRIVATE_OUTPUT_DIR / "first-closure-field-confirmation-private-workbench.csv"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_field_confirmation_public_ledger"

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

PUBLIC_FIELDS = [
    "第一闭环字段确认公开账本ID",
    "来源第一闭环任务复核公开账本",
    "来源第一闭环PDFOCR候选公开审计",
    "来源第一闭环机器坐标候选公开审计",
    "来源第一闭环页列候选看板",
    "来源私有字段确认工作台",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "字段确认公开账本总序",
    "第一闭环执行顺序",
    "执行泳道",
    "第一闭环页列优先级",
    "人工核验优先级数值",
    "人工核验泳道",
    "人工核验方式",
    "人工核验动作",
    "必须完成证据步骤",
    "公开升级阻断原因",
    "字段名",
    "字段审计范围",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "来源页码",
    "版面列",
    "页码版面键",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环任务复核公开账本ID",
    "稳定基座第一闭环页列包ID",
    "稳定基座第一闭环复核公开账本ID",
    "第一闭环PDFOCR候选公开审计ID",
    "第一闭环机器坐标候选公开审计ID",
    "第一闭环页列候选看板ID",
    "任务来源类型",
    "PDFOCR提示记录状态",
    "PDFOCR提示审阅桶",
    "PDFOCR与高校辅证关系桶",
    "PDFOCR提示字段数",
    "高校辅证提示字段数",
    "PDFOCR与高校辅证冲突字段数",
    "PDFOCR与高校辅证一致字段数",
    "机器坐标提示记录状态",
    "机器坐标提示审阅桶",
    "机器坐标提示关系桶",
    "机器坐标是否可辅助核页",
    "机器坐标提示字段数",
    "候选提示综合桶",
    "是否有PDFOCR提示",
    "是否有机器坐标提示",
    "是否有高校辅证线索",
    "是否存在PDFOCR与高校冲突",
    "是否需要人工直接看图",
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

PRIVATE_EXTRA_FIELDS = [
    "私有工作台用途",
    "PDFOCR计划数候选值",
    "PDFOCR学费候选值",
    "PDFOCR选科候选值",
    "机器坐标候选字段值",
    "机器坐标候选值集合",
    "高校辅证计划数候选值",
    "高校辅证学费候选值",
    "高校辅证选科候选值",
    "OCR行文本",
    "私有页图相对路径",
    "私有OCR文本相对路径",
    "机器坐标证据行号集合",
    "机器坐标证据x集合",
    "机器坐标证据y集合",
    "机器坐标证据置信度集合",
    "机器坐标窗口文本SHA256",
    "机器坐标私有窗口证据编号",
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

PRIVATE_FIELDS = PUBLIC_FIELDS + PRIVATE_EXTRA_FIELDS

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
    "候选值",
    "候选计划数",
    "候选学费",
    "候选选科",
    "OCR行文本",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "字段确认值",
    "人工读数",
    "一审记录",
    "二审记录",
    "复核结论",
    "复核备注",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
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


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def bool_text(value):
    return "true" if str(value).strip().lower() == "true" else "false"


def nonempty(value):
    return bool(str(value or "").strip())


def read_optional_private_rows(path, key_field):
    if not path.exists():
        return {}
    return {row.get(key_field, ""): row for row in read_csv(path)}


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


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


def confirmation_state(field_name, task, pdf_public, machine_public, private_row):
    pdf_value = private_row.get("PDF原页人工读数", "")
    hubei_value = private_row.get("湖北官方字段值", "")
    school_value = private_row.get("高校官网或招生章程字段值", "")
    reviewer_a = private_row.get("PDF核页复核人A", "")
    reviewer_b = private_row.get("PDF核页复核人B", "")

    school_required = task.get("高校辅证是否需要复核") == "true"
    double_required = task.get("是否需要双人复核") == "true"
    has_pdf = nonempty(pdf_value)
    has_hubei = nonempty(hubei_value)
    has_school = nonempty(school_value)
    double_done = (
        not double_required
        or (nonempty(reviewer_a) and nonempty(reviewer_b) and reviewer_a != reviewer_b)
    )

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

    direct_image = (
        pdf_public.get("是否需要人工直接看图") == "true"
        and machine_public.get("是否机器坐标可补候选") != "true"
    )
    return {
        "PDF原页私有记录状态": pdf_status,
        "湖北官方私有记录状态": hubei_status,
        "高校辅证私有记录状态": school_status,
        "双人复核公开状态": double_status,
        "三方字段一致性公开状态": consistency,
        "字段事实写回评估状态": writeback,
        "公开升级阻断原因": "；".join(reasons),
        "has_required_values": has_required_values,
        "direct_image": direct_image,
    }


def review_priority(task, pdf_public, machine_public):
    if pdf_public.get("是否存在PDFOCR与高校冲突") == "true":
        return 10, "F0-PDFOCR与高校辅证冲突双人核页", "双人复核", "先核PDF原页，再核湖北官方侧，最后对照高校辅证"
    if machine_public.get("是否机器坐标可补候选") == "true":
        return 20, "F1-机器坐标候选辅助核页", "单人初核加抽检", "按机器坐标提示回看PDF原页，再核湖北官方侧"
    if pdf_public.get("PDFOCR候选字段数") != "0":
        return 30, "F2-PDFOCR候选人工确认", "单人初核加抽检", "按PDFOCR候选回看PDF原页，再核湖北官方侧"
    if as_int(pdf_public.get("高校辅证候选字段数")) > 0:
        return 40, "F3-高校辅证线索辅助找行", "三方线索优先核验", "用高校辅证线索辅助定位，仍以PDF原页和湖北官方侧为准"
    return 50, "F4-无候选人工看图", "人工看图", "直接回看PDF原页和页列上下文"


def required_steps(task):
    steps = ["PDF原页人工核页", "湖北官方系统或省招办计划核验"]
    if task.get("高校辅证是否需要复核") == "true":
        steps.append("高校官网或招生章程辅证对照")
    if task.get("是否需要双人复核") == "true":
        steps.append("双人复核")
    return "；".join(steps)


def combined_hint_bucket(pdf_public, machine_public):
    if pdf_public.get("是否存在PDFOCR与高校冲突") == "true":
        return "H0-PDFOCR与高校辅证冲突"
    if machine_public.get("是否机器坐标可补候选") == "true":
        return "H1-原缺PDFOCR但有机器坐标候选"
    if as_int(pdf_public.get("PDFOCR候选字段数")):
        return "H2-已有PDFOCR候选"
    if pdf_public.get("高校辅证候选字段数") != "0":
        return "H3-仅高校辅证线索"
    return "H4-无候选需人工看图"


def private_seed(pdf_private, machine_private, existing_private):
    row = {
        "私有工作台用途": "仅供本地人工记录第一闭环字段读数和证据位置；不得提交公开仓库。",
        "PDFOCR计划数候选值": pdf_private.get("PDFOCR计划数候选值", ""),
        "PDFOCR学费候选值": pdf_private.get("PDFOCR学费候选值", ""),
        "PDFOCR选科候选值": pdf_private.get("PDFOCR选科候选值", ""),
        "机器坐标候选字段值": machine_private.get("机器坐标候选字段值", ""),
        "机器坐标候选值集合": machine_private.get("机器坐标候选值集合", ""),
        "高校辅证计划数候选值": pdf_private.get("高校辅证计划数候选值", ""),
        "高校辅证学费候选值": pdf_private.get("高校辅证学费候选值", ""),
        "高校辅证选科候选值": pdf_private.get("高校辅证选科候选值", ""),
        "OCR行文本": pdf_private.get("OCR行文本", ""),
        "私有页图相对路径": pdf_private.get("私有页图相对路径", ""),
        "私有OCR文本相对路径": pdf_private.get("私有OCR文本相对路径", ""),
        "机器坐标证据行号集合": machine_private.get("候选证据行号集合", ""),
        "机器坐标证据x集合": machine_private.get("候选证据x集合", ""),
        "机器坐标证据y集合": machine_private.get("候选证据y集合", ""),
        "机器坐标证据置信度集合": machine_private.get("候选证据置信度集合", ""),
        "机器坐标窗口文本SHA256": machine_private.get("窗口文本SHA256", ""),
        "机器坐标私有窗口证据编号": machine_private.get("私有窗口证据编号", ""),
    }
    for field in PRIVATE_MANUAL_FIELDS:
        row[field] = existing_private.get(field, "")
    return row


def page_side_key(row):
    return (row.get("来源页码", ""), row.get("版面列", ""))


def build_rows():
    task_rows = read_csv(FIRST_TASK_REVIEW)
    pdf_public_rows = read_csv(FIRST_PDF_OCR_PUBLIC)
    pdf_private_rows = read_csv(FIRST_PDF_OCR_PRIVATE)
    machine_public_rows = read_csv(FIRST_MACHINE_PUBLIC)
    machine_private_rows = read_csv(FIRST_MACHINE_PRIVATE)
    page_rows = read_csv(FIRST_PAGE_DASHBOARD)

    pdf_public_by_task = {row["稳定基座第一闭环明细任务ID"]: row for row in pdf_public_rows}
    pdf_private_by_task = {row["稳定基座第一闭环明细任务ID"]: row for row in pdf_private_rows}
    machine_public_by_task = {row["稳定基座第一闭环明细任务ID"]: row for row in machine_public_rows}
    machine_private_by_task = {row["稳定基座第一闭环明细任务ID"]: row for row in machine_private_rows}
    page_by_key = {page_side_key(row): row for row in page_rows}
    existing_private_by_public_id = read_optional_private_rows(
        PRIVATE_OUTPUT, "第一闭环字段确认公开账本ID"
    )

    sortable = []
    for task in task_rows:
        task_id = task["稳定基座第一闭环明细任务ID"]
        pdf_public = pdf_public_by_task.get(task_id)
        machine_public = machine_public_by_task.get(task_id)
        page = page_by_key.get(page_side_key(task))
        if not pdf_public or not machine_public or not page:
            raise ValueError(f"第一闭环任务缺少候选或页列看板证据链: {task_id}")
        priority, lane, mode, action = review_priority(task, pdf_public, machine_public)
        sortable.append(
            (
                as_int(pdf_public.get("第一闭环执行顺序")),
                priority,
                task_id,
                task,
                pdf_public,
                machine_public,
                page,
                lane,
                mode,
                action,
            )
        )

    public_rows = []
    private_rows = []
    for queue_index, item in enumerate(sorted(sortable), start=1):
        _, priority, task_id, task, pdf_public, machine_public, page, lane, mode, action = item
        public_id = stable_id("FIRSTFCONF", [task_id])
        pdf_private = pdf_private_by_task.get(task_id, {})
        machine_private = machine_private_by_task.get(task_id, {})
        existing_private = existing_private_by_public_id.get(public_id, {})
        private_extra = private_seed(pdf_private, machine_private, existing_private)
        state = confirmation_state(
            task.get("字段名") or pdf_private.get("字段名") or pdf_public.get("字段审计范围"),
            task,
            pdf_public,
            machine_public,
            private_extra,
        )
        writeback_allowed = (
            state["字段事实写回评估状态"] == "ready_for_manual_field_writeback_review"
        )
        has_pdf_hint = as_int(pdf_public.get("PDFOCR候选字段数")) > 0
        has_machine_hint = machine_public.get("是否机器坐标可补候选") == "true"
        has_school_hint = as_int(pdf_public.get("高校辅证候选字段数")) > 0
        public_row = {
            "第一闭环字段确认公开账本ID": public_id,
            "来源第一闭环任务复核公开账本": str(FIRST_TASK_REVIEW.relative_to(ROOT)),
            "来源第一闭环PDFOCR候选公开审计": str(FIRST_PDF_OCR_PUBLIC.relative_to(ROOT)),
            "来源第一闭环机器坐标候选公开审计": str(FIRST_MACHINE_PUBLIC.relative_to(ROOT)),
            "来源第一闭环页列候选看板": str(FIRST_PAGE_DASHBOARD.relative_to(ROOT)),
            "来源私有字段确认工作台": "first_closure_field_confirmation_private_workbench_not_public",
            "来源湖北官方公开入口状态快照": str(OFFICIAL_STATUS.relative_to(ROOT)),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细×第一闭环任务",
            "任务粒度": "逐任务×第一闭环字段确认公开状态",
            **false_gate_values(),
            "字段确认公开账本总序": str(queue_index),
            "第一闭环执行顺序": pdf_public.get("第一闭环执行顺序", ""),
            "执行泳道": pdf_public.get("执行泳道", ""),
            "第一闭环页列优先级": pdf_public.get("第一闭环页列优先级", ""),
            "人工核验优先级数值": str(priority),
            "人工核验泳道": lane,
            "人工核验方式": mode,
            "人工核验动作": action,
            "必须完成证据步骤": required_steps(task),
            "公开升级阻断原因": state["公开升级阻断原因"],
            "字段名": task.get("字段名") or pdf_private.get("字段名") or pdf_public.get("字段审计范围", ""),
            "字段审计范围": pdf_public.get("字段审计范围", ""),
            "专业行ID": task.get("专业行ID", ""),
            "专业组出现ID": task.get("专业组出现ID", ""),
            "院校代码": task.get("院校代码", ""),
            "来源页码": task.get("来源页码", ""),
            "版面列": task.get("版面列", ""),
            "页码版面键": task.get("页码版面键", ""),
            "稳定基座第一闭环明细任务ID": task_id,
            "稳定基座第一闭环任务复核公开账本ID": task.get("稳定基座第一闭环任务复核公开账本ID", ""),
            "稳定基座第一闭环页列包ID": task.get("稳定基座第一闭环页列包ID", ""),
            "稳定基座第一闭环复核公开账本ID": task.get("稳定基座第一闭环复核公开账本ID", ""),
            "第一闭环PDFOCR候选公开审计ID": pdf_public.get("第一闭环PDFOCR候选公开审计ID", ""),
            "第一闭环机器坐标候选公开审计ID": machine_public.get("第一闭环机器坐标候选公开审计ID", ""),
            "第一闭环页列候选看板ID": page.get("第一闭环页列候选看板ID", ""),
            "任务来源类型": task.get("任务来源类型", ""),
            "PDFOCR提示记录状态": pdf_public.get("PDFOCR候选记录状态", ""),
            "PDFOCR提示审阅桶": pdf_public.get("PDFOCR候选审阅桶", ""),
            "PDFOCR与高校辅证关系桶": pdf_public.get("PDFOCR与高校辅证关系桶", ""),
            "PDFOCR提示字段数": pdf_public.get("PDFOCR候选字段数", "0"),
            "高校辅证提示字段数": pdf_public.get("高校辅证候选字段数", "0"),
            "PDFOCR与高校辅证冲突字段数": pdf_public.get("冲突字段数", "0"),
            "PDFOCR与高校辅证一致字段数": pdf_public.get("一致字段数", "0"),
            "机器坐标提示记录状态": machine_public.get("机器坐标候选记录状态", ""),
            "机器坐标提示审阅桶": machine_public.get("机器坐标候选审阅桶", ""),
            "机器坐标提示关系桶": machine_public.get("机器坐标候选关系桶", ""),
            "机器坐标是否可辅助核页": machine_public.get("是否机器坐标可补候选", "false"),
            "机器坐标提示字段数": machine_public.get("机器坐标候选字段数", "0"),
            "候选提示综合桶": combined_hint_bucket(pdf_public, machine_public),
            "是否有PDFOCR提示": "true" if has_pdf_hint else "false",
            "是否有机器坐标提示": "true" if has_machine_hint else "false",
            "是否有高校辅证线索": "true" if has_school_hint else "false",
            "是否存在PDFOCR与高校冲突": pdf_public.get("是否存在PDFOCR与高校冲突", "false"),
            "是否需要人工直接看图": "true" if state["direct_image"] else "false",
            "是否需要双人复核": task.get("是否需要双人复核", "false"),
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
            "私有字段确认工作台状态": "private_first_closure_field_confirmation_workbench_generated",
            "公开安全策略": "公开表只保存字段确认状态、证据编号、SHA、关系状态和门禁；不保存字段读数明细、候选明细、识别文本、私有路径、院校名或专业名。",
            "下一步": "在私有第一闭环字段确认工作台补齐PDF原页、湖北官方系统或省招办计划、高校官网或章程的私有记录；公开账本只同步状态，不同步记录值。",
        }
        public_row["是否允许写回字段事实"] = "true" if writeback_allowed else "false"
        public_rows.append(public_row)
        private_rows.append({**public_row, **private_extra})

    return public_rows, private_rows


def build_summary(public_rows):
    return {
        "status": "issue19_stable_foundation_first_closure_field_confirmation_public_ledger_not_final",
        "generated_by": Path(__file__).name,
        "source_first_closure_task_review_public_ledger": str(FIRST_TASK_REVIEW.relative_to(ROOT)),
        "source_first_closure_pdf_ocr_candidate_public_audit": str(FIRST_PDF_OCR_PUBLIC.relative_to(ROOT)),
        "source_first_closure_machine_coordinate_candidate_public_audit": str(FIRST_MACHINE_PUBLIC.relative_to(ROOT)),
        "source_first_closure_page_side_candidate_dashboard": str(FIRST_PAGE_DASHBOARD.relative_to(ROOT)),
        "source_private_field_confirmation_workbench": "first_closure_field_confirmation_private_workbench_not_public",
        "source_official_public_status": str(OFFICIAL_STATUS.relative_to(ROOT)),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": str(OUTPUT.relative_to(ROOT)),
        "row_grain": "逐任务×第一闭环字段确认公开状态",
        "row_count": len(public_rows),
        "private_field_confirmation_workbench_generated": True,
        "private_field_confirmation_workbench_sha256": sha256(PRIVATE_OUTPUT),
        "unique_public_ledger_id_count": len({row["第一闭环字段确认公开账本ID"] for row in public_rows}),
        "unique_first_closure_task_id_count": len({row["稳定基座第一闭环明细任务ID"] for row in public_rows}),
        "unique_pdf_ocr_audit_id_count": len({row["第一闭环PDFOCR候选公开审计ID"] for row in public_rows}),
        "unique_machine_coordinate_audit_id_count": len({row["第一闭环机器坐标候选公开审计ID"] for row in public_rows}),
        "unique_page_side_count": len({row["页码版面键"] for row in public_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in public_rows}),
        "field_counts": dict(Counter(row["字段名"] or row["字段审计范围"] for row in public_rows)),
        "task_source_type_counts": dict(Counter(row["任务来源类型"] for row in public_rows)),
        "manual_review_lane_counts": dict(Counter(row["人工核验泳道"] for row in public_rows)),
        "manual_review_mode_counts": dict(Counter(row["人工核验方式"] for row in public_rows)),
        "combined_hint_bucket_counts": dict(Counter(row["候选提示综合桶"] for row in public_rows)),
        "pdf_hint_record_status_counts": dict(Counter(row["PDFOCR提示记录状态"] for row in public_rows)),
        "machine_hint_record_status_counts": dict(Counter(row["机器坐标提示记录状态"] for row in public_rows)),
        "pdf_private_record_status_counts": dict(Counter(row["PDF原页私有记录状态"] for row in public_rows)),
        "hubei_private_record_status_counts": dict(Counter(row["湖北官方私有记录状态"] for row in public_rows)),
        "school_private_record_status_counts": dict(Counter(row["高校辅证私有记录状态"] for row in public_rows)),
        "double_review_status_counts": dict(Counter(row["双人复核公开状态"] for row in public_rows)),
        "three_way_public_status_counts": dict(Counter(row["三方字段一致性公开状态"] for row in public_rows)),
        "field_writeback_review_status_counts": dict(Counter(row["字段事实写回评估状态"] for row in public_rows)),
        "pdf_ocr_hint_task_count": sum(row["是否有PDFOCR提示"] == "true" for row in public_rows),
        "machine_coordinate_hint_task_count": sum(row["是否有机器坐标提示"] == "true" for row in public_rows),
        "school_hint_task_count": sum(row["是否有高校辅证线索"] == "true" for row in public_rows),
        "direct_image_review_required_count": sum(row["是否需要人工直接看图"] == "true" for row in public_rows),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in public_rows),
        "pdf_manual_review_pending_count": sum(row["PDF原页核页状态"] == "pending_manual_pdf_review" for row in public_rows),
        "hubei_official_review_pending_count": sum(row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_review" for row in public_rows),
        "three_way_closure_pending_count": sum(row["三方字段一致性状态"] == "pending_private_three_way_field_confirmation" for row in public_rows),
        "field_writeback_ready_count": sum(row["字段事实写回评估状态"] == "ready_for_manual_field_writeback_review" for row in public_rows),
        "field_conflict_blocked_count": sum(row["字段事实写回评估状态"] == "blocked_conflict_needs_manual_resolution" for row in public_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in public_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in public_rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段事实"] == "true" for row in public_rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in public_rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in public_rows),
        "official_plan_replacement_allowed_count": sum(row["是否允许官网证据替代湖北官方计划"] == "true" for row in public_rows),
        "public_safety_note": "公开字段确认账本只保存状态、证据编号、SHA、关系状态和门禁；不保存字段读数明细、候选明细、识别文本、私有路径、院校名或专业名。",
    }


def ensure_public_safe(rows, summary):
    text = json.dumps(summary, ensure_ascii=False) + "\n" + "\n".join(
        ",".join(row.get(field, "") for field in PUBLIC_FIELDS) for row in rows
    )
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise RuntimeError(f"第一闭环字段确认公开账本含禁止公开内容: {hits[:10]}")


def main():
    public_rows, private_rows = build_rows()
    write_csv(PRIVATE_OUTPUT, private_rows, PRIVATE_FIELDS)
    summary = build_summary(public_rows)
    ensure_public_safe(public_rows, summary)
    write_csv(OUTPUT, public_rows, PUBLIC_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {PRIVATE_OUTPUT.relative_to(ROOT)}：{len(private_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
