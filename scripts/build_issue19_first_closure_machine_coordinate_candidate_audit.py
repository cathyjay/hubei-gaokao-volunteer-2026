#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIRST_PDF_OCR_AUDIT = (
    ROOT / "data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv"
)
FIRST_PDF_OCR_SUMMARY = (
    ROOT
    / "data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit-summary.json"
)
FIRST_PDF_OCR_PRIVATE = (
    ROOT
    / "private/review-assets/issue19-stable-foundation-first-closure-pdf-ocr-candidates/first-closure-pdf-ocr-candidates-private.csv"
)
P0_MACHINE_CANDIDATES = ROOT / "data/working/issue19-field-fact-p0-reread-machine-candidates.csv"
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

PRIVATE_OUTPUT_DIR = (
    ROOT
    / "private/review-assets/issue19-stable-foundation-first-closure-machine-coordinate-candidates"
)
PRIVATE_OUTPUT = PRIVATE_OUTPUT_DIR / "first-closure-machine-coordinate-candidates-private.csv"

PUBLIC_OUTPUT = (
    ROOT
    / "data/working/issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit.csv"
)
SUMMARY_OUTPUT = (
    ROOT
    / "data/working/issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_machine_coordinate_candidate_public_audit"

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
    "第一闭环机器坐标候选公开审计ID",
    "来源第一闭环PDFOCR候选公开审计",
    "来源第一闭环PDFOCR候选摘要",
    "来源第一闭环PDFOCR候选私有工作台",
    "来源P0字段机器坐标候选表",
    "来源第一闭环机器坐标候选私有工作台",
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
    "第一闭环执行顺序",
    "执行泳道",
    "第一闭环页列优先级",
    "稳定基座第一闭环明细任务ID",
    "稳定基座第一闭环任务复核公开账本ID",
    "稳定基座第一闭环页列包ID",
    "稳定基座第一闭环复核公开账本ID",
    "第一闭环PDFOCR候选公开审计ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "任务来源类型",
    "字段审计范围",
    "原PDFOCR候选记录状态",
    "原PDFOCR候选审阅桶",
    "原PDFOCR与高校辅证关系桶",
    "机器坐标候选记录状态",
    "机器坐标候选审阅桶",
    "机器坐标候选关系桶",
    "是否原缺PDFOCR",
    "是否机器坐标可补候选",
    "是否从缺PDFOCR提升为机器坐标待核",
    "匹配P0机器坐标记录数",
    "单一机器坐标候选记录数",
    "无机器坐标候选记录数",
    "机器坐标冲突或多值记录数",
    "机器坐标候选字段数",
    "机器坐标候选字段类别",
    "机器坐标候选置信等级",
    "机器坐标候选规则ID",
    "P0字段机器候选任务ID",
    "来源P0字段原页重读任务ID",
    "来源字段事实核验任务ID",
    "页级保真队列ID",
    "专业行原页证据锚点ID",
    "候选证据行号数量",
    "候选证据坐标数量",
    "私有字段明细状态",
    "PDF原页是否必核",
    "湖北官方侧是否必核",
    "高校辅证是否需要复核",
    "是否需要人工直接看图",
    "是否需要双人复核",
    "是否可自动写入私有记录值",
    "机器坐标是否允许自动写回主表",
    "机器坐标是否允许自动回填候选",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_EXTRA_FIELDS = [
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "字段名",
    "机器坐标候选字段值",
    "机器坐标候选值集合",
    "候选证据行号集合",
    "候选证据x集合",
    "候选证据y集合",
    "候选证据置信度集合",
    "候选证据来源范围",
    "窗口文本SHA256",
    "私有窗口证据编号",
    "机器候选说明",
    "不得进入原因",
    "候选不得自动写回声明",
]

PRIVATE_FIELDS = PUBLIC_FIELDS + PRIVATE_EXTRA_FIELDS

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
    "机器候选字段值",
    "机器候选值集合",
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


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def load_official_status():
    data = json.loads(OFFICIAL_STATUS.read_text(encoding="utf-8"))
    return {
        "official_public_plan_page_can_finalize": bool(
            data.get("hubei_admission_plan_page", {}).get("can_finalize")
        ),
        "zspt_platform_can_finalize": bool(
            data.get("hubei_zspt_platform", {}).get("can_finalize")
        ),
    }


def machine_join_key(private_row, public_row):
    field = private_row.get("字段名") or public_row.get("字段审计范围", "")
    return (
        private_row.get("专业行ID", ""),
        field,
        public_row.get("来源页码", ""),
        public_row.get("版面列", ""),
    )


def is_single_machine_candidate(row):
    return (
        row.get("机器候选状态") == "P0C1-单一坐标候选待人工核验"
        and bool(row.get("机器候选字段值", "").strip())
        and row.get("机器候选去重值数") == "1"
    )


def count_split(value):
    text = str(value or "").strip()
    if not text:
        return 0
    return len([part for part in text.split(";") if part.strip()])


def relation_status(public_row, machine_row, matches):
    original_missing = (
        public_row.get("PDFOCR候选记录状态")
        == "private_pdf_ocr_candidate_unavailable_needs_manual_image_review"
    )
    if not original_missing:
        return "M2-原已有PDFOCR候选不启用机器坐标补候选"
    if machine_row:
        return "M0-机器坐标单一候选可作为人工核页提示"
    if matches:
        return "M1-机器坐标仍无候选需人工看图"
    return "M3-未匹配到P0机器坐标任务需人工判定"


def review_bucket(public_row, machine_row, matches):
    original_missing = (
        public_row.get("PDFOCR候选记录状态")
        == "private_pdf_ocr_candidate_unavailable_needs_manual_image_review"
    )
    if not original_missing:
        return "MC2-原已有PDFOCR候选按原流程人工核页"
    if machine_row:
        return "MC0-机器坐标候选可辅助PDF原页核页"
    if matches:
        return "MC1-机器坐标仍缺候选继续人工看图"
    return "MC3-无P0机器坐标记录需人工判定字段"


def build_rows():
    public_rows = read_csv(FIRST_PDF_OCR_AUDIT)
    private_rows = read_csv(FIRST_PDF_OCR_PRIVATE)
    machine_rows = read_csv(P0_MACHINE_CANDIDATES)
    official = load_official_status()

    private_by_task = {
        row.get("稳定基座第一闭环明细任务ID", ""): row for row in private_rows
    }
    machine_by_key = {}
    for row in machine_rows:
        key = (
            row.get("专业行ID", ""),
            row.get("字段名", ""),
            row.get("来源页码", ""),
            row.get("版面列", ""),
        )
        machine_by_key.setdefault(key, []).append(row)

    public_out = []
    private_out = []
    for public in public_rows:
        task_id = public.get("稳定基座第一闭环明细任务ID", "")
        private = private_by_task.get(task_id, {})
        key = machine_join_key(private, public)
        matches = machine_by_key.get(key, [])
        single_candidates = [row for row in matches if is_single_machine_candidate(row)]
        machine = single_candidates[0] if len(single_candidates) == 1 else {}
        original_missing = (
            public.get("PDFOCR候选记录状态")
            == "private_pdf_ocr_candidate_unavailable_needs_manual_image_review"
        )
        can_help = bool(original_missing and machine)
        status = relation_status(public, machine, matches)
        bucket = review_bucket(public, machine, matches)
        relation = (
            "MR0-缺PDFOCR但机器坐标可补候选"
            if can_help
            else (
                "MR1-缺PDFOCR且机器坐标仍缺候选"
                if original_missing
                else "MR2-原PDFOCR已有候选无需坐标补候选"
            )
        )
        field = private.get("字段名") or public.get("字段审计范围", "")
        base = {
            "第一闭环机器坐标候选公开审计ID": stable_id("FIRSTMCOORD", [task_id]),
            "来源第一闭环PDFOCR候选公开审计": str(FIRST_PDF_OCR_AUDIT.relative_to(ROOT)),
            "来源第一闭环PDFOCR候选摘要": str(FIRST_PDF_OCR_SUMMARY.relative_to(ROOT)),
            "来源第一闭环PDFOCR候选私有工作台": "first_closure_pdf_ocr_candidate_private_workbench_not_public",
            "来源P0字段机器坐标候选表": str(P0_MACHINE_CANDIDATES.relative_to(ROOT)),
            "来源第一闭环机器坐标候选私有工作台": "first_closure_machine_coordinate_candidate_private_workbench_not_public",
            "来源湖北官方公开入口状态快照": str(OFFICIAL_STATUS.relative_to(ROOT)),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细×第一闭环任务",
            "任务粒度": "逐任务×机器坐标候选公开状态",
            **false_gate_values(),
            "第一闭环执行顺序": public.get("第一闭环执行顺序", ""),
            "执行泳道": public.get("执行泳道", ""),
            "第一闭环页列优先级": public.get("第一闭环页列优先级", ""),
            "稳定基座第一闭环明细任务ID": task_id,
            "稳定基座第一闭环任务复核公开账本ID": public.get("稳定基座第一闭环任务复核公开账本ID", ""),
            "稳定基座第一闭环页列包ID": public.get("稳定基座第一闭环页列包ID", ""),
            "稳定基座第一闭环复核公开账本ID": public.get("稳定基座第一闭环复核公开账本ID", ""),
            "第一闭环PDFOCR候选公开审计ID": public.get("第一闭环PDFOCR候选公开审计ID", ""),
            "来源页码": public.get("来源页码", ""),
            "版面列": public.get("版面列", ""),
            "页码版面键": public.get("页码版面键", ""),
            "任务来源类型": public.get("任务来源类型", ""),
            "字段审计范围": public.get("字段审计范围", ""),
            "原PDFOCR候选记录状态": public.get("PDFOCR候选记录状态", ""),
            "原PDFOCR候选审阅桶": public.get("PDFOCR候选审阅桶", ""),
            "原PDFOCR与高校辅证关系桶": public.get("PDFOCR与高校辅证关系桶", ""),
            "机器坐标候选记录状态": status,
            "机器坐标候选审阅桶": bucket,
            "机器坐标候选关系桶": relation,
            "是否原缺PDFOCR": "true" if original_missing else "false",
            "是否机器坐标可补候选": "true" if can_help else "false",
            "是否从缺PDFOCR提升为机器坐标待核": "true" if can_help else "false",
            "匹配P0机器坐标记录数": str(len(matches)),
            "单一机器坐标候选记录数": str(len(single_candidates)),
            "无机器坐标候选记录数": str(
                sum(row.get("机器候选状态") == "P0C0-未找到坐标候选仍需人工原页重读" for row in matches)
            ),
            "机器坐标冲突或多值记录数": str(
                sum(
                    row.get("机器候选状态") not in [
                        "P0C0-未找到坐标候选仍需人工原页重读",
                        "P0C1-单一坐标候选待人工核验",
                    ]
                    for row in matches
                )
            ),
            "机器坐标候选字段数": "1" if can_help else "0",
            "机器坐标候选字段类别": field if can_help else "",
            "机器坐标候选置信等级": machine.get("机器候选置信等级", "") if can_help else "",
            "机器坐标候选规则ID": machine.get("机器候选规则ID", "") if can_help else "",
            "P0字段机器候选任务ID": machine.get("P0字段机器候选任务ID", "") if machine else "",
            "来源P0字段原页重读任务ID": machine.get("来源P0字段原页重读任务ID", "") if machine else "",
            "来源字段事实核验任务ID": machine.get("来源字段事实核验任务ID", "") if machine else "",
            "页级保真队列ID": machine.get("页级保真队列ID", "") if machine else "",
            "专业行原页证据锚点ID": machine.get("专业行原页证据锚点ID", "") if machine else "",
            "候选证据行号数量": str(count_split(machine.get("候选证据行号集合", ""))) if machine else "0",
            "候选证据坐标数量": str(count_split(machine.get("候选证据x集合", ""))) if machine else "0",
            "私有字段明细状态": "private_machine_coordinate_candidate_seeded" if can_help else "no_private_machine_coordinate_candidate",
            "PDF原页是否必核": public.get("PDF原页是否必核", ""),
            "湖北官方侧是否必核": public.get("湖北官方侧是否必核", ""),
            "高校辅证是否需要复核": public.get("高校辅证是否需要复核", ""),
            "是否需要人工直接看图": "false" if can_help else public.get("是否需要人工直接看图", ""),
            "是否需要双人复核": public.get("是否需要双人复核", ""),
            "是否可自动写入私有记录值": "false",
            "机器坐标是否允许自动写回主表": "false",
            "机器坐标是否允许自动回填候选": "false",
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "高校官网或招生章程辅证状态": public.get("高校官网或招生章程辅证状态", ""),
            "三方字段一致性状态": "pending_three_way_closure",
            "字段事实写回状态": "blocked_until_private_pdf_hubei_review_confirms_values",
            "公开安全策略": "公开层只保存机器坐标候选存在性、状态桶、计数、证据编号和门禁；不公开字段明细、学校专业明细、识别正文或私有路径",
            "下一步": (
                "用机器坐标候选辅助人工核PDF原页；再核湖北官方侧；仍不得自动写回字段事实"
                if can_help
                else "继续按原PDFOCR候选审计状态人工核PDF原页和湖北官方侧"
            ),
        }
        private_row = {
            **base,
            "专业行ID": private.get("专业行ID", ""),
            "专业组出现ID": private.get("专业组出现ID", ""),
            "院校代码": private.get("院校代码", ""),
            "字段名": field,
            "机器坐标候选字段值": machine.get("机器候选字段值", "") if can_help else "",
            "机器坐标候选值集合": machine.get("机器候选值集合", "") if can_help else "",
            "候选证据行号集合": machine.get("候选证据行号集合", "") if can_help else "",
            "候选证据x集合": machine.get("候选证据x集合", "") if can_help else "",
            "候选证据y集合": machine.get("候选证据y集合", "") if can_help else "",
            "候选证据置信度集合": machine.get("候选证据置信度集合", "") if can_help else "",
            "候选证据来源范围": machine.get("候选证据来源范围", "") if can_help else "",
            "窗口文本SHA256": machine.get("窗口文本SHA256", "") if machine else "",
            "私有窗口证据编号": machine.get("私有窗口证据编号", "") if machine else "",
            "机器候选说明": machine.get("机器候选说明", "") if machine else "",
            "不得进入原因": machine.get("不得进入原因", "") if machine else "",
            "候选不得自动写回声明": "机器坐标候选只用于人工核页提示，不能自动写回人工记录、字段事实或志愿方案。",
        }
        public_out.append(base)
        private_out.append(private_row)

    return public_out, private_out


def ensure_public_safe(rows):
    text = "\n".join(",".join(row.get(field, "") for field in PUBLIC_FIELDS) for row in rows)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise RuntimeError(f"第一闭环机器坐标候选公开审计含禁止内容: {hits[:10]}")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    public_rows, private_rows = build_rows()
    ensure_public_safe(public_rows)
    write_csv(PUBLIC_OUTPUT, public_rows, PUBLIC_FIELDS)
    write_csv(PRIVATE_OUTPUT, private_rows, PRIVATE_FIELDS)

    summary = {
        "status": "issue19_stable_foundation_first_closure_machine_coordinate_candidate_public_audit_not_final",
        "generated_by": "build_issue19_first_closure_machine_coordinate_candidate_audit.py",
        "source_first_closure_pdf_ocr_candidate_public_audit": str(FIRST_PDF_OCR_AUDIT.relative_to(ROOT)),
        "source_first_closure_pdf_ocr_candidate_summary": str(FIRST_PDF_OCR_SUMMARY.relative_to(ROOT)),
        "source_private_pdf_ocr_candidate_workbench": "first_closure_pdf_ocr_candidate_private_workbench_not_public",
        "source_p0_machine_candidates": str(P0_MACHINE_CANDIDATES.relative_to(ROOT)),
        "source_private_machine_coordinate_candidate_workbench": "first_closure_machine_coordinate_candidate_private_workbench_not_public",
        "source_official_public_status": str(OFFICIAL_STATUS.relative_to(ROOT)),
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "output_table": str(PUBLIC_OUTPUT.relative_to(ROOT)),
        "public_row_count": len(public_rows),
        "private_row_count": len(private_rows),
        "unique_task_count": len({row["稳定基座第一闭环明细任务ID"] for row in public_rows}),
        "unique_page_side_count": len({row["页码版面键"] for row in public_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in public_rows}),
        "original_missing_pdf_ocr_task_count": sum(row["是否原缺PDFOCR"] == "true" for row in public_rows),
        "machine_coordinate_candidate_task_count": sum(row["是否机器坐标可补候选"] == "true" for row in public_rows),
        "upgraded_from_missing_to_machine_candidate_count": sum(
            row["是否从缺PDFOCR提升为机器坐标待核"] == "true" for row in public_rows
        ),
        "remaining_missing_after_machine_coordinate_count": sum(
            row["是否原缺PDFOCR"] == "true" and row["是否机器坐标可补候选"] == "false"
            for row in public_rows
        ),
        "machine_candidate_field_counts": dict(
            Counter(row["机器坐标候选字段类别"] for row in public_rows if row["机器坐标候选字段类别"])
        ),
        "machine_candidate_record_status_counts": dict(
            Counter(row["机器坐标候选记录状态"] for row in public_rows)
        ),
        "machine_candidate_review_bucket_counts": dict(
            Counter(row["机器坐标候选审阅桶"] for row in public_rows)
        ),
        "machine_candidate_relation_bucket_counts": dict(
            Counter(row["机器坐标候选关系桶"] for row in public_rows)
        ),
        "execution_lane_counts": dict(Counter(row["执行泳道"] for row in public_rows)),
        "page_side_priority_counts": dict(Counter(row["第一闭环页列优先级"] for row in public_rows)),
        "direct_image_review_remaining_count": sum(row["是否需要人工直接看图"] == "true" for row in public_rows),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in public_rows),
        "pdf_required_count": sum(row["PDF原页是否必核"] == "true" for row in public_rows),
        "hubei_official_required_count": sum(row["湖北官方侧是否必核"] == "true" for row in public_rows),
        "auto_private_record_write_allowed_count": 0,
        "machine_auto_writeback_allowed_count": 0,
        "machine_auto_prefill_allowed_count": 0,
        "field_writeback_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "private_machine_coordinate_candidate_workbench_sha256": sha256(PRIVATE_OUTPUT),
        "public_boundary": "公开表只保存机器坐标候选存在性、状态桶、计数、证据编号和门禁；候选明细只在私有工作台。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(f"写出 {PUBLIC_OUTPUT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {PRIVATE_OUTPUT.relative_to(ROOT)}：{len(private_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
