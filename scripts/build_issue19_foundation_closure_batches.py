#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FOUNDATION_RELEASE = ROOT / "data/working/issue19-major-detail-foundation-release.csv"

MAJOR_BATCH_OUTPUT = ROOT / "data/working/issue19-foundation-closure-major-batches.csv"
PAGE_INDEX_OUTPUT = ROOT / "data/working/issue19-foundation-closure-page-index.csv"
SCHOOL_INDEX_OUTPUT = ROOT / "data/working/issue19-foundation-closure-school-index.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-foundation-closure-batches-summary.json"

DATA_STAGE = "issue19_foundation_closure_batches"


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def split_items(value):
    return [part for part in str(value or "").split("；") if part]


def join_unique(values):
    seen = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.append(text)
    return "；".join(seen)


def has_school_source(row):
    status = row.get("高校官网来源状态", "")
    return bool(status) and status != "not_yet_school_source_searched_in_full_workbench"


def has_historical_line(row):
    status = row.get("三年投档稳定性状态", "")
    return bool(status) and "未命中" not in status


def has_b0_b1_diff(row):
    return as_int(row.get("B0B1官网差异任务数")) > 0


def has_official_auxiliary_task(row):
    return has_b0_b1_diff(row) or has_school_source(row)


def primary_batch(row):
    if as_int(row.get("P0复核任务数")) > 0:
        return "C0-P0证据闭环先核"
    if as_int(row.get("字段缺口数")) > 0:
        return "C1-字段缺口先补"
    if has_official_auxiliary_task(row):
        return "C2-官网辅证交叉核验"
    if row.get("底座保真门禁", "").startswith("G4"):
        return "C4-低风险抽检但非最终"
    return "C3-常规三方证据闭环"


def action_flags(row):
    actions = ["湖北官方系统/省招办计划核验", "家庭接受度核验", "同组调剂结论核验"]
    if as_int(row.get("P0复核任务数")) > 0:
        actions.insert(0, "P0-PDF原页或三方证据先核")
    else:
        actions.insert(0, "PDF原页常规核验")
    if as_int(row.get("字段缺口数")) > 0:
        actions.append("P1-字段缺口补证")
    if has_official_auxiliary_task(row):
        actions.append("高校官网/章程辅证交叉")
    if has_historical_line(row):
        actions.append("三年投档稳定性复核")
    return join_unique(actions)


def primary_action(row):
    batch = primary_batch(row)
    if batch.startswith("C0"):
        return "回看PDF原页并同步补湖北官方系统/高校官网证据"
    if batch.startswith("C1"):
        return f"补字段缺口：{row.get('字段缺口字段') or '待识别字段'}"
    if batch.startswith("C2"):
        return "用高校官网/章程辅证和湖北官方系统逐字段交叉"
    if batch.startswith("C4"):
        return "抽检PDF原页和湖北官方系统，确认低风险行没有漏判"
    return "完成PDF原页、湖北官方系统、高校官网/章程、家庭接受度和调剂结论闭环"


def priority_score(row):
    base_by_batch = {
        "C0-P0证据闭环先核": 100000,
        "C1-字段缺口先补": 200000,
        "C2-官网辅证交叉核验": 300000,
        "C3-常规三方证据闭环": 400000,
        "C4-低风险抽检但非最终": 500000,
    }
    score = base_by_batch[primary_batch(row)]
    page_priority = row.get("页级复核优先级", "")
    if page_priority.startswith("P0"):
        score -= 5000
    elif page_priority.startswith("P1"):
        score -= 2500
    preference = row.get("专业偏好方向", "")
    if "数字媒体技术" in preference:
        score -= 900
    if "计算机类相关" in preference:
        score -= 700
    if "师范类相关" in preference:
        score -= 500
    if has_school_source(row):
        score -= 250
    if has_historical_line(row):
        score -= 100
    score += as_int(row.get("来源页码"))
    score += min(as_int(row.get("专业组内专业序号")), 99)
    return score


def build_major_batches(release_rows):
    rows = []
    for row in release_rows:
        batch = primary_batch(row)
        rows.append({
            "底座闭环批次ID": stable_id("CLOSEMAJOR", [row.get("专业行ID", "")]),
            "来源统一逐专业底座入口": "data/working/issue19-major-detail-foundation-release.csv",
            "来源底座发布明细ID": row.get("底座发布明细ID", ""),
            "来源期号": row.get("来源期号", ""),
            "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "是否可进入最终专业列表": "false",
            "可进入下一阶段": "false",
            "闭环任务状态": "pending_foundation_closure",
            "闭环执行批次": batch,
            "闭环执行动作集合": action_flags(row),
            "首要核验动作": primary_action(row),
            "闭环执行排序分": str(priority_score(row)),
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "专业组内专业序号": row.get("专业组内专业序号", ""),
            "专业代号OCR": row.get("专业代号OCR", ""),
            "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
            "再选科目OCR候选": row.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": row.get("专业计划数OCR候选", ""),
            "学费OCR候选": row.get("学费OCR候选", ""),
            "字段缺口数": row.get("字段缺口数", ""),
            "字段缺口字段": row.get("字段缺口字段", ""),
            "P0复核任务数": row.get("P0复核任务数", ""),
            "P0证据项": row.get("P0证据项", ""),
            "湖北官方平台字段核验状态": row.get("湖北官方平台字段核验状态", ""),
            "高校官网来源状态": row.get("高校官网来源状态", ""),
            "高校官网证据匹配状态": row.get("高校官网证据匹配状态", ""),
            "高校官网计划数核验状态": row.get("高校官网计划数核验状态", ""),
            "高校官网差异字段集合": row.get("高校官网差异字段集合", ""),
            "B0B1官网差异任务数": row.get("B0B1官网差异任务数", ""),
            "页级保真队列ID": row.get("页级保真队列ID", ""),
            "页级复核优先级": row.get("页级复核优先级", ""),
            "页级阻断等级": row.get("页级阻断等级", ""),
            "私有页图证据编号": row.get("私有页图证据编号", ""),
            "私有页图SHA256": row.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": row.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": row.get("私有OCR文本SHA256", ""),
            "家庭接受度结论": row.get("家庭接受度结论", ""),
            "同组调剂结论": row.get("同组调剂结论", ""),
            "机器专业接受度初判": row.get("机器专业接受度初判", ""),
            "调剂影响等级": row.get("调剂影响等级", ""),
            "同组真实招生明细数": row.get("同组真实招生明细数", ""),
            "同组医学护理排除专业数": row.get("同组医学护理排除专业数", ""),
            "同组高收费或超预算专业数": row.get("同组高收费或超预算专业数", ""),
            "同组特殊限制待核专业数": row.get("同组特殊限制待核专业数", ""),
            "专业偏好方向": row.get("专业偏好方向", ""),
            "风险阻断等级": row.get("风险阻断等级", ""),
            "三年投档稳定性状态": row.get("三年投档稳定性状态", ""),
            "不得进入原因": row.get("不得进入原因", ""),
            "下一步": row.get("下一步", ""),
        })

    rows.sort(key=lambda row: (
        as_int(row["闭环执行排序分"]),
        as_int(row["来源页码"]),
        row["院校代码"],
        row["院校专业组代码OCR规范化"],
        as_int(row["专业组内专业序号"]),
        row["专业行ID"],
    ))
    for index, row in enumerate(rows, start=1):
        row["闭环执行总序"] = str(index)
    return rows


def build_page_index(major_rows):
    by_page = defaultdict(list)
    for row in major_rows:
        by_page[row["来源页码"]].append(row)

    rows = []
    for page, page_rows in by_page.items():
        batch_counts = Counter(row["闭环执行批次"] for row in page_rows)
        field_counts = Counter()
        for row in page_rows:
            field_counts.update(split_items(row.get("字段缺口字段")))
        first = min(page_rows, key=lambda row: as_int(row["闭环执行总序"]))
        rows.append({
            "页级闭环索引ID": stable_id("CLOSEPAGE", [page]),
            "来源逐专业闭环批次表": "data/working/issue19-foundation-closure-major-batches.csv",
            "来源期号": first.get("来源期号", ""),
            "来源PDF_SHA256": first.get("来源PDF_SHA256", ""),
            "数据阶段": "issue19_foundation_closure_page_index",
            "索引粒度": "PDF页码",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "PDF页码": page,
            "页级执行总序": min(as_int(row["闭环执行总序"]) for row in page_rows),
            "页面专业明细数": len(page_rows),
            "涉及院校数": len({row["院校代码"] for row in page_rows}),
            "涉及专业组数": len({row["专业组出现ID"] for row in page_rows}),
            "C0_P0主批次专业明细数": batch_counts.get("C0-P0证据闭环先核", 0),
            "C1字段缺口主批次专业明细数": batch_counts.get("C1-字段缺口先补", 0),
            "C2官网辅证主批次专业明细数": batch_counts.get("C2-官网辅证交叉核验", 0),
            "C3常规三方主批次专业明细数": batch_counts.get("C3-常规三方证据闭环", 0),
            "C4低风险抽检主批次专业明细数": batch_counts.get("C4-低风险抽检但非最终", 0),
            "含官网辅证任务专业明细数": sum(has_official_auxiliary_task(row) for row in page_rows),
            "B0B1官网差异专业明细数": sum(has_b0_b1_diff(row) for row in page_rows),
            "有高校官网来源线索专业明细数": sum(has_school_source(row) for row in page_rows),
            "偏好专业明细数": sum(bool(row.get("专业偏好方向")) for row in page_rows),
            "数字媒体技术专业明细数": sum("数字媒体技术" in row.get("专业偏好方向", "") for row in page_rows),
            "计算机类相关专业明细数": sum("计算机类相关" in row.get("专业偏好方向", "") for row in page_rows),
            "师范类相关专业明细数": sum("师范类相关" in row.get("专业偏好方向", "") for row in page_rows),
            "字段缺口字段Top": join_unique(field for field, _count in field_counts.most_common()),
            "首个专业行ID": first.get("专业行ID", ""),
            "首个院校代码": first.get("院校代码", ""),
            "首个院校名称OCR": first.get("院校名称OCR", ""),
            "首要核验动作": first.get("首要核验动作", ""),
            "下一步": "按页批量回看PDF原页，完成页内逐专业字段和组边界核验；页级索引不得替代逐专业明细。",
        })
    rows.sort(key=lambda row: (as_int(row["页级执行总序"]), as_int(row["PDF页码"])))
    return rows


def build_school_index(major_rows):
    by_school = defaultdict(list)
    for row in major_rows:
        by_school[row["院校代码"]].append(row)

    rows = []
    for school_code, school_rows in by_school.items():
        batch_counts = Counter(row["闭环执行批次"] for row in school_rows)
        source_status_counts = Counter(row.get("高校官网来源状态", "") for row in school_rows)
        first = min(school_rows, key=lambda row: as_int(row["闭环执行总序"]))
        rows.append({
            "学校闭环索引ID": stable_id("CLOSESCHOOL", [school_code]),
            "来源逐专业闭环批次表": "data/working/issue19-foundation-closure-major-batches.csv",
            "来源期号": first.get("来源期号", ""),
            "来源PDF_SHA256": first.get("来源PDF_SHA256", ""),
            "数据阶段": "issue19_foundation_closure_school_index",
            "索引粒度": "院校",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "院校代码": school_code,
            "院校名称OCR": first.get("院校名称OCR", ""),
            "学校执行总序": min(as_int(row["闭环执行总序"]) for row in school_rows),
            "专业明细数": len(school_rows),
            "涉及PDF页数": len({row["来源页码"] for row in school_rows}),
            "涉及专业组数": len({row["专业组出现ID"] for row in school_rows}),
            "C0_P0主批次专业明细数": batch_counts.get("C0-P0证据闭环先核", 0),
            "C1字段缺口主批次专业明细数": batch_counts.get("C1-字段缺口先补", 0),
            "C2官网辅证主批次专业明细数": batch_counts.get("C2-官网辅证交叉核验", 0),
            "C3常规三方主批次专业明细数": batch_counts.get("C3-常规三方证据闭环", 0),
            "C4低风险抽检主批次专业明细数": batch_counts.get("C4-低风险抽检但非最终", 0),
            "含官网辅证任务专业明细数": sum(has_official_auxiliary_task(row) for row in school_rows),
            "B0B1官网差异专业明细数": sum(has_b0_b1_diff(row) for row in school_rows),
            "有高校官网来源线索专业明细数": sum(has_school_source(row) for row in school_rows),
            "偏好专业明细数": sum(bool(row.get("专业偏好方向")) for row in school_rows),
            "高校官网来源状态分布": "；".join(
                f"{status}:{count}" for status, count in source_status_counts.items() if status
            ),
            "首个PDF页码": first.get("来源页码", ""),
            "首个专业行ID": first.get("专业行ID", ""),
            "首要核验动作": first.get("首要核验动作", ""),
            "下一步": "按学校补湖北官方系统和高校官网/章程来源，再回到逐专业闭环批次表逐行核字段、家庭接受度和调剂范围。",
        })
    rows.sort(key=lambda row: (as_int(row["学校执行总序"]), row["院校代码"]))
    return rows


def write_summary(major_rows, page_rows, school_rows):
    raw_batch_counts = Counter(row["闭环执行批次"] for row in major_rows)
    batch_counts = {
        "C0-P0证据闭环先核": raw_batch_counts.get("C0-P0证据闭环先核", 0),
        "C1-字段缺口先补": raw_batch_counts.get("C1-字段缺口先补", 0),
        "C2-官网辅证交叉核验": raw_batch_counts.get("C2-官网辅证交叉核验", 0),
        "C3-常规三方证据闭环": raw_batch_counts.get("C3-常规三方证据闭环", 0),
        "C4-低风险抽检但非最终": raw_batch_counts.get("C4-低风险抽检但非最终", 0),
    }
    field_counts = Counter()
    for row in major_rows:
        field_counts.update(split_items(row.get("字段缺口字段")))
    summary = {
        "status": "issue19_foundation_closure_batches_not_final",
        "generated_by": "build_issue19_foundation_closure_batches.py",
        "source_foundation_release": "data/working/issue19-major-detail-foundation-release.csv",
        "output_major_batches": "data/working/issue19-foundation-closure-major-batches.csv",
        "output_page_index": "data/working/issue19-foundation-closure-page-index.csv",
        "output_school_index": "data/working/issue19-foundation-closure-school-index.csv",
        "major_row_count": len(major_rows),
        "unique_major_line_id_count": len({row["专业行ID"] for row in major_rows}),
        "unique_batch_id_count": len({row["底座闭环批次ID"] for row in major_rows}),
        "page_index_row_count": len(page_rows),
        "school_index_row_count": len(school_rows),
        "closure_batch_counts": batch_counts,
        "field_gap_field_counts": dict(field_counts),
        "p0_major_line_count": sum(as_int(row.get("P0复核任务数")) > 0 for row in major_rows),
        "field_gap_major_line_count": sum(as_int(row.get("字段缺口数")) > 0 for row in major_rows),
        "b0_b1_diff_major_line_count": sum(as_int(row.get("B0B1官网差异任务数")) > 0 for row in major_rows),
        "school_source_major_line_count": sum(has_school_source(row) for row in major_rows),
        "official_auxiliary_task_major_line_count": sum(
            has_official_auxiliary_task(row) for row in major_rows
        ),
        "preference_major_line_count": sum(bool(row.get("专业偏好方向")) for row in major_rows),
        "digital_media_major_line_count": sum("数字媒体技术" in row.get("专业偏好方向", "") for row in major_rows),
        "computer_major_line_count": sum("计算机类相关" in row.get("专业偏好方向", "") for row in major_rows),
        "teacher_major_line_count": sum("师范类相关" in row.get("专业偏好方向", "") for row in major_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in major_rows),
        "final_major_list_candidate_count": sum(row["是否可进入最终专业列表"] == "true" for row in major_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in major_rows),
        "notes": [
            "主表仍是一行一个招生专业明细，页级/学校级索引只用于安排执行顺序。",
            "所有行仍保持非最终门禁；闭环批次只说明先核什么，不产生志愿排序结论。",
            "C2 主批次可能被 C0/C1 覆盖；含官网辅证任务专业明细数和 B0B1 官网差异专业明细数按动作维度单独统计。",
            "C0/C1 是当前数据底座阶段优先处理对象，湖北官方系统核验仍需登录态或最终志愿系统证据。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    release_rows = read_csv(FOUNDATION_RELEASE)
    major_rows = build_major_batches(release_rows)
    major_fields = [
        "底座闭环批次ID",
        "来源统一逐专业底座入口",
        "来源底座发布明细ID",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "闭环任务状态",
        "闭环执行总序",
        "闭环执行批次",
        "闭环执行动作集合",
        "首要核验动作",
        "闭环执行排序分",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "字段缺口数",
        "字段缺口字段",
        "P0复核任务数",
        "P0证据项",
        "湖北官方平台字段核验状态",
        "高校官网来源状态",
        "高校官网证据匹配状态",
        "高校官网计划数核验状态",
        "高校官网差异字段集合",
        "B0B1官网差异任务数",
        "页级保真队列ID",
        "页级复核优先级",
        "页级阻断等级",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "家庭接受度结论",
        "同组调剂结论",
        "机器专业接受度初判",
        "调剂影响等级",
        "同组真实招生明细数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "专业偏好方向",
        "风险阻断等级",
        "三年投档稳定性状态",
        "不得进入原因",
        "下一步",
    ]
    page_rows = build_page_index(major_rows)
    page_fields = [
        "页级闭环索引ID",
        "来源逐专业闭环批次表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "索引粒度",
        "最终可用",
        "可进入下一阶段",
        "PDF页码",
        "页级执行总序",
        "页面专业明细数",
        "涉及院校数",
        "涉及专业组数",
        "C0_P0主批次专业明细数",
        "C1字段缺口主批次专业明细数",
        "C2官网辅证主批次专业明细数",
        "C3常规三方主批次专业明细数",
        "C4低风险抽检主批次专业明细数",
        "含官网辅证任务专业明细数",
        "B0B1官网差异专业明细数",
        "有高校官网来源线索专业明细数",
        "偏好专业明细数",
        "数字媒体技术专业明细数",
        "计算机类相关专业明细数",
        "师范类相关专业明细数",
        "字段缺口字段Top",
        "首个专业行ID",
        "首个院校代码",
        "首个院校名称OCR",
        "首要核验动作",
        "下一步",
    ]
    school_rows = build_school_index(major_rows)
    school_fields = [
        "学校闭环索引ID",
        "来源逐专业闭环批次表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "索引粒度",
        "最终可用",
        "可进入下一阶段",
        "院校代码",
        "院校名称OCR",
        "学校执行总序",
        "专业明细数",
        "涉及PDF页数",
        "涉及专业组数",
        "C0_P0主批次专业明细数",
        "C1字段缺口主批次专业明细数",
        "C2官网辅证主批次专业明细数",
        "C3常规三方主批次专业明细数",
        "C4低风险抽检主批次专业明细数",
        "含官网辅证任务专业明细数",
        "B0B1官网差异专业明细数",
        "有高校官网来源线索专业明细数",
        "偏好专业明细数",
        "高校官网来源状态分布",
        "首个PDF页码",
        "首个专业行ID",
        "首要核验动作",
        "下一步",
    ]
    write_csv(MAJOR_BATCH_OUTPUT, major_rows, major_fields)
    write_csv(PAGE_INDEX_OUTPUT, page_rows, page_fields)
    write_csv(SCHOOL_INDEX_OUTPUT, school_rows, school_fields)
    write_summary(major_rows, page_rows, school_rows)
    print(f"写入 {MAJOR_BATCH_OUTPUT.relative_to(ROOT)}：{len(major_rows)} 行")
    print(f"写入 {PAGE_INDEX_OUTPUT.relative_to(ROOT)}：{len(page_rows)} 行")
    print(f"写入 {SCHOOL_INDEX_OUTPUT.relative_to(ROOT)}：{len(school_rows)} 行")
    print(f"写入 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
