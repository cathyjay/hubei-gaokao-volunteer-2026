#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MACHINE_CANDIDATES = ROOT / "data/working/issue19-field-fact-p0-reread-machine-candidates.csv"
P0_REREAD_WORKLIST = ROOT / "data/working/issue19-field-fact-p0-reread-worklist.csv"
FIELD_FACT_LEDGER = ROOT / "data/working/issue19-field-fact-closure-ledger.csv"
OUTPUT = ROOT / "data/working/issue19-field-fact-p0-closure-action-workbench.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-field-fact-p0-closure-action-workbench-summary.json"

DATA_STAGE = "issue19_field_fact_p0_closure_action_workbench"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"


FIELDS = [
    "P0字段闭环推进任务ID",
    "来源P0字段机器候选表",
    "来源P0字段原页重读工作清单",
    "来源字段事实闭环总账",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动回填候选",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许写回字段",
    "机器是否已解决字段事实",
    "候选是否可作为人工核页线索",
    "仍需PDF原页核验",
    "仍需湖北官方系统或省招办计划核验",
    "仍需高校官网或招生章程辅证",
    "字段闭环阶段",
    "字段事实状态Before",
    "字段事实状态After建议",
    "PDF原页核页状态",
    "PDF原页人工读数",
    "PDF原页人工核验人",
    "PDF原页人工核验时间",
    "PDF原页证据编号",
    "PDF原页证据SHA256",
    "PDF核页差异类型",
    "湖北官方系统或省招办计划核验状态",
    "湖北官方字段值",
    "湖北官方证据编号",
    "湖北官方证据SHA256",
    "高校官网或招生章程辅证状态",
    "高校官网或招生章程字段值",
    "高校官网或招生章程证据编号",
    "高校官网或招生章程证据SHA256",
    "三方字段一致性状态",
    "P0闭环动作桶",
    "P0闭环执行优先级",
    "P0闭环批次",
    "P0字段机器候选任务ID",
    "来源P0字段原页重读任务ID",
    "来源字段事实核验任务ID",
    "字段事实闭环ID",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "来源页码",
    "版面列",
    "字段名",
    "字段事实状态",
    "字段事实闭环等级",
    "字段事实阻断等级",
    "字段事实缺口类型",
    "底座稳定性等级",
    "看板动作桶",
    "风险阻断等级",
    "候选初筛闸门状态",
    "机器候选状态",
    "机器候选置信等级",
    "机器候选规则ID",
    "机器候选字段值",
    "机器候选值集合",
    "机器候选去重值数",
    "机器候选原始命中数",
    "候选证据行号集合",
    "候选证据x集合",
    "候选证据y集合",
    "候选证据置信度集合",
    "候选证据来源范围",
    "页级保真队列ID",
    "原始专业行源证据审计ID",
    "专业行原页证据锚点ID",
    "窗口文本SHA256",
    "私有窗口证据编号",
    "闭环推进说明",
    "不得进入原因",
    "下一步",
]


FIELD_ORDER = {
    "专业计划数": 1,
    "再选科目": 2,
    "学费": 3,
}

ACTION_BY_STATUS = {
    "P0C1-单一坐标候选待人工核验": (
        "A1-单一坐标候选先核PDF原页",
        "10",
        "BATCH-A1-快速候选核页",
        "true",
    ),
    "P0C1-重复同值坐标候选待人工核验": (
        "A1R-重复同值坐标候选先核PDF原页",
        "20",
        "BATCH-A1-快速候选核页",
        "true",
    ),
    "P0C2-多值坐标候选冲突待人工核页": (
        "A2-多值坐标冲突先核PDF原页",
        "30",
        "BATCH-A2-冲突候选核页",
        "false",
    ),
    "P0C0-未找到坐标候选仍需人工原页重读": (
        "A3-无坐标候选需人工重读或高分辨率OCR",
        "40",
        "BATCH-A3-无候选重读",
        "false",
    ),
}


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value, default=0):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return default


def action_for(row):
    status = row.get("机器候选状态", "")
    if status not in ACTION_BY_STATUS:
        return ("A9-未知机器候选状态需人工排查", "90", "BATCH-A9-状态异常排查", "false")
    return ACTION_BY_STATUS[status]


def build_rows():
    machine_rows = read_csv(MACHINE_CANDIDATES)
    reread_by_task = {row.get("P0字段原页重读任务ID", ""): row for row in read_csv(P0_REREAD_WORKLIST)}
    ledger_by_id = {row.get("字段事实闭环ID", ""): row for row in read_csv(FIELD_FACT_LEDGER)}

    rows = []
    for source in machine_rows:
        reread_row = reread_by_task.get(source.get("来源P0字段原页重读任务ID", ""), {})
        ledger_row = ledger_by_id.get(source.get("字段事实闭环ID", ""), {})
        action_bucket, priority, batch, has_machine_candidate = action_for(source)
        row = {
            "P0字段闭环推进任务ID": stable_id(
                "P0FIELDACTION",
                [
                    source.get("P0字段机器候选任务ID", ""),
                    source.get("来源P0字段原页重读任务ID", ""),
                    source.get("字段名", ""),
                    SOURCE_PDF_SHA256,
                ],
            ),
            "来源P0字段机器候选表": "data/working/issue19-field-fact-p0-reread-machine-candidates.csv",
            "来源P0字段原页重读工作清单": "data/working/issue19-field-fact-p0-reread-worklist.csv",
            "来源字段事实闭环总账": "data/working/issue19-field-fact-closure-ledger.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×K0字段×P0闭环推进动作",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "是否允许写回字段": "false",
            "机器是否已解决字段事实": "false",
            "候选是否可作为人工核页线索": has_machine_candidate,
            "仍需PDF原页核验": "true",
            "仍需湖北官方系统或省招办计划核验": "true",
            "仍需高校官网或招生章程辅证": "true",
            "字段闭环阶段": "P0-待PDF原页人工核页和官方闭环",
            "字段事实状态Before": source.get("字段事实状态", ""),
            "字段事实状态After建议": "保持K0，待PDF原页、湖北官方系统或省招办计划、高校官网或招生章程闭环后人工判定",
            "PDF原页核页状态": "pending_pdf_manual_review",
            "PDF原页人工读数": "",
            "PDF原页人工核验人": "",
            "PDF原页人工核验时间": "",
            "PDF原页证据编号": "",
            "PDF原页证据SHA256": "",
            "PDF核页差异类型": "",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "湖北官方字段值": "",
            "湖北官方证据编号": "",
            "湖北官方证据SHA256": "",
            "高校官网或招生章程辅证状态": "pending_school_official_or_charter_review",
            "高校官网或招生章程字段值": "",
            "高校官网或招生章程证据编号": "",
            "高校官网或招生章程证据SHA256": "",
            "三方字段一致性状态": "pending_three_way_closure",
            "P0闭环动作桶": action_bucket,
            "P0闭环执行优先级": priority,
            "P0闭环批次": batch,
            "闭环推进说明": (
                "本表把 P0/K0 无候选字段转成核页动作；机器候选只缩短人工定位路径，"
                "不能自动改写字段事实。"
            ),
            "不得进入原因": (
                "P0 字段仍未完成 PDF 原页、湖北官方系统或省招办计划、高校官网/章程闭环；"
                "不得写回主表、回填候选、推荐学校专业或进入志愿排序。"
            ),
            "下一步": next_step(action_bucket),
        }
        for field in [
            "P0字段机器候选任务ID",
            "来源P0字段原页重读任务ID",
            "来源字段事实核验任务ID",
            "字段事实闭环ID",
            "专业行ID",
            "专业组出现ID",
            "院校代码",
            "来源页码",
            "版面列",
            "字段名",
            "字段事实状态",
            "机器候选状态",
            "机器候选置信等级",
            "机器候选规则ID",
            "机器候选字段值",
            "机器候选值集合",
            "机器候选去重值数",
            "机器候选原始命中数",
            "候选证据行号集合",
            "候选证据x集合",
            "候选证据y集合",
            "候选证据置信度集合",
            "候选证据来源范围",
            "页级保真队列ID",
            "原始专业行源证据审计ID",
            "专业行原页证据锚点ID",
            "窗口文本SHA256",
            "私有窗口证据编号",
        ]:
            row[field] = source.get(field, "")
        for field in [
            "字段事实闭环等级",
            "字段事实阻断等级",
            "字段事实缺口类型",
            "底座稳定性等级",
            "看板动作桶",
            "风险阻断等级",
            "候选初筛闸门状态",
        ]:
            row[field] = ledger_row.get(field, reread_row.get(field, ""))
        rows.append(row)

    rows.sort(key=lambda row: (
        as_int(row.get("P0闭环执行优先级")),
        as_int(row.get("来源页码")),
        row.get("版面列", ""),
        row.get("院校代码", ""),
        row.get("专业组出现ID", ""),
        row.get("专业行ID", ""),
        FIELD_ORDER.get(row.get("字段名", ""), 9),
        row.get("P0字段闭环推进任务ID", ""),
    ))
    return rows


def next_step(action_bucket):
    if action_bucket.startswith("A1-"):
        return "按候选证据行号、x/y 坐标回看 PDF 原页；若原页一致，只进入人工 K1 候选回看，不自动写回。"
    if action_bucket.startswith("A1R-"):
        return "核对重复同值候选是否来自同一字段列；若原页一致，只进入人工 K1 候选回看，不自动写回。"
    if action_bucket.startswith("A2-"):
        return "逐个候选值回看 PDF 原页，确认字段列和专业行边界；冲突未消除前保持 K0/P0 阻断。"
    if action_bucket.startswith("A3-"):
        return "人工重读 PDF 原页对应专业行、同组上下文和字段列；必要时使用更高分辨率 OCR 后再生成候选。"
    return "人工排查未知状态，并回到 P0 原页重读工作清单确认来源。"


def top_counts(counter, limit=30):
    return dict(counter.most_common(limit))


def nested_field_action_counts(rows):
    counts = defaultdict(Counter)
    for row in rows:
        counts[row["字段名"]][row["P0闭环动作桶"]] += 1
    return {field: dict(counter) for field, counter in counts.items()}


def write_summary(rows):
    action_counts = Counter(row["P0闭环动作桶"] for row in rows)
    batch_counts = Counter(row["P0闭环批次"] for row in rows)
    field_counts = Counter(row["字段名"] for row in rows)
    non_empty_rows = [row for row in rows if row["机器候选字段值"]]
    summary = {
        "status": "issue19_field_fact_p0_closure_action_workbench_not_final",
        "generated_by": "build_issue19_field_fact_p0_closure_action_workbench.py",
        "source_machine_candidates": "data/working/issue19-field-fact-p0-reread-machine-candidates.csv",
        "source_p0_reread_worklist": "data/working/issue19-field-fact-p0-reread-worklist.csv",
        "source_field_fact_ledger": "data/working/issue19-field-fact-closure-ledger.csv",
        "output_table": "data/working/issue19-field-fact-p0-closure-action-workbench.csv",
        "row_grain": "逐专业招生明细×K0字段×P0闭环推进动作",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "unique_action_task_id_count": len({row["P0字段闭环推进任务ID"] for row in rows}),
        "unique_machine_candidate_task_id_count": len({row["P0字段机器候选任务ID"] for row in rows}),
        "unique_source_p0_reread_task_id_count": len({row["来源P0字段原页重读任务ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in rows}),
        "unique_school_code_count": len({row["院校代码"] for row in rows}),
        "field_counts": dict(field_counts),
        "machine_candidate_status_counts": dict(Counter(row["机器候选状态"] for row in rows)),
        "action_bucket_counts": dict(action_counts),
        "action_batch_counts": dict(batch_counts),
        "field_action_bucket_counts": nested_field_action_counts(rows),
        "manual_pdf_check_with_machine_candidate_count": sum(row["候选是否可作为人工核页线索"] == "true" for row in rows),
        "machine_candidate_non_empty_value_count": len(non_empty_rows),
        "multi_value_conflict_action_count": action_counts.get("A2-多值坐标冲突先核PDF原页", 0),
        "no_coordinate_action_count": action_counts.get("A3-无坐标候选需人工重读或高分辨率OCR", 0),
        "page_action_count_top30": top_counts(Counter(row["来源页码"] for row in rows)),
        "page_machine_candidate_count_top30": top_counts(Counter(row["来源页码"] for row in non_empty_rows)),
        "manual_pdf_required_count": sum(row["仍需PDF原页核验"] == "true" for row in rows),
        "hubei_official_required_count": sum(row["仍需湖北官方系统或省招办计划核验"] == "true" for row in rows),
        "school_official_required_count": sum(row["仍需高校官网或招生章程辅证"] == "true" for row in rows),
        "pdf_manual_review_pending_count": sum(row["PDF原页核页状态"] == "pending_pdf_manual_review" for row in rows),
        "hubei_official_review_pending_count": sum(row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_plan_review" for row in rows),
        "school_official_review_pending_count": sum(row["高校官网或招生章程辅证状态"] == "pending_school_official_or_charter_review" for row in rows),
        "three_way_closure_pending_count": sum(row["三方字段一致性状态"] == "pending_three_way_closure" for row in rows),
        "pdf_confirmed_count": sum(bool(row["PDF原页人工读数"]) for row in rows),
        "official_confirmed_count": sum(bool(row["湖北官方字段值"]) for row in rows),
        "school_official_confirmed_count": sum(bool(row["高校官网或招生章程字段值"]) for row in rows),
        "three_way_closed_count": sum(row["字段闭环阶段"] == "T3-三方字段闭环待人工写回" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "auto_writeback_allowed_count": sum(row["机器是否允许自动写回主表"] == "true" for row in rows),
        "auto_candidate_fill_allowed_count": sum(row["机器是否允许自动回填候选"] == "true" for row in rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段"] == "true" for row in rows),
        "machine_solved_field_fact_count": sum(row["机器是否已解决字段事实"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "public_safety_note": "本产物只保存动作桶、候选值、坐标摘要、必要来源ID、页码/版面列、字段名、证据编号、哈希和非最终门禁；不保存私有OCR窗口原文、院校名、专业名、专业代号、专业组代码、图片路径、登录态或个人身份信息。",
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    write_summary(rows)
    print(f"写出P0字段闭环推进工作台：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
