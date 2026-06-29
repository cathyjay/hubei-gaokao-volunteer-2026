#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FACT_CHANNEL = WORKING / "issue19-first-closure-fact-evidence-channel-workbench-v1-public-ledger.csv"
RESOLUTION_OVERLAY = WORKING / "issue19-first-closure-resolution-execution-overlay-v1.csv"
SCHOOL_PROGRESS = WORKING / "issue19-school-source-progress-board-public-ledger.csv"

OUTPUT = WORKING / "issue19-first-closure-fact-action-packets-v1-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-fact-action-packets-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_fact_action_packets_v1"

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

ACTION_RANK = {
    "A0-W0B0冲突事实先核": 0,
    "A1-专业名归属事实先核": 1,
    "A2-专业组边界事实随页先核": 2,
    "A3-双人复核事实先核": 3,
    "A4-无稳定OCR人工看图": 4,
    "A5-机器坐标辅助核页": 5,
    "A6-高校辅证提示回接": 6,
    "A7-常规PDF湖北官方闭环": 7,
}

PACKET_FIELDS = [
    "事实动作包ID",
    "来源事实证据通道工作台",
    "来源准出执行叠加表",
    "来源高校官网辅证进度看板",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "事实动作包序号",
    "来源执行顺序",
    "页码版面键",
    "来源页码",
    "版面列",
    "准出闭环波次",
    "执行泳道",
    "第一闭环页列优先级",
    "事实核验动作组",
    "动作组排序",
    "包执行优先级",
    "页列事实总数",
    "动作包事实数",
    "动作包字段事实数",
    "动作包专业名归属事实数",
    "动作包专业组边界事实数",
    "专业计划数字段事实数",
    "学费字段事实数",
    "再选科目字段事实数",
    "待人工判定字段事实数",
    "涉及任务数",
    "涉及字段状态数",
    "涉及专业行数",
    "涉及专业组出现数",
    "涉及院校代码数",
    "PDF原页通道状态分布",
    "OCR提示通道状态分布",
    "机器坐标通道状态分布",
    "高校官网辅证通道状态分布",
    "湖北官方侧通道状态分布",
    "冲突处理通道状态分布",
    "双人复核通道状态分布",
    "三方闭环通道状态分布",
    "专业名归属通道状态分布",
    "专业组边界通道状态分布",
    "仍需PDF原页事实数",
    "仍需湖北官方侧事实数",
    "仍需高校辅证事实数",
    "仍需冲突处理事实数",
    "仍需双人复核事实数",
    "仍需三方闭环事实数",
    "仍需专业名归属事实数",
    "仍需专业组边界事实数",
    "同校高校源任务去重数",
    "同校高校源最高证据层级分布",
    "同校高校源下一批优先级分布",
    "同校高校源留存状态分布",
    "同校高校源候选diff去重数",
    "同校高校源冲突候选去重数",
    "同校高校源补缺候选去重数",
    "事实集合SHA16",
    "任务集合SHA16",
    "字段状态集合SHA16",
    "院校代码集合SHA16",
    "包级完成证据要求",
    "包级主阻断原因",
    "包级下一步最小核验动作",
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
    "人工读数",
    "字段OCR候选",
    "字段人工确认",
    "字段候选值集合",
    "候选计划数",
    "候选学费",
    "候选选科",
    "机器候选字段值",
    "机器候选值集合",
    "专业名称及备注",
    "OCR正文",
    "OCR行文本",
    "截图路径",
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


def public_text(value):
    text = clean(value)
    replacements = {
        "字段读数": "字段明细值",
        "人工读数": "人工记录值",
        "OCR正文": "OCR文本",
        "截图路径": "图像路径",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: public_text(row.get(field, "")) for field in fields} for row in rows])


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


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def counter_text(values):
    counter = Counter(clean(value) for value in values if clean(value))
    return "；".join(f"{key}×{value}" for key, value in sorted(counter.items()))


def stable_set_sha(values):
    normalized = sorted({clean(value) for value in values if clean(value)})
    if not normalized:
        return ""
    return hashlib.sha256("\n".join(normalized).encode("utf-8")).hexdigest()[:16]


def unique_count(rows, field):
    return len({clean(row.get(field)) for row in rows if clean(row.get(field))})


def true_count(rows, field):
    return sum(1 for row in rows if clean(row.get(field)) == "true")


def first_nonempty(rows, field):
    for row in rows:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def school_summary(rows):
    if not rows:
        return {
            "count": 0,
            "level": "",
            "priority": "",
            "retention": "",
            "candidate_diff": 0,
            "conflict": 0,
            "fill": 0,
        }
    return {
        "count": len(rows),
        "level": counter_text(row.get("最新高校侧证据层级") for row in rows),
        "priority": counter_text(row.get("下一批推进优先级") for row in rows),
        "retention": counter_text(row.get("来源留存状态") for row in rows),
        "candidate_diff": sum(as_int(row.get("C4C6可生成候选diff明细数")) for row in rows),
        "conflict": sum(
            as_int(row.get("C4C6计划数冲突候选数")) + as_int(row.get("计划数冲突行数"))
            for row in rows
        ),
        "fill": sum(
            as_int(row.get("C4C6官网可补OCR计划数候选数")) + as_int(row.get("官网补缺候选行数"))
            for row in rows
        ),
    }


def action_next_step(action_group):
    if action_group == "A0-W0B0冲突事实先核":
        return "先按同一页列核 PDF 原页和湖北官方侧；冲突事实需要双人复核，高校官网只作 double check 提示。"
    if action_group == "A1-专业名归属事实先核":
        return "先核专业名、备注和限定词归属，确认属于哪个专业行或专业组，再继续字段闭环。"
    if action_group == "A2-专业组边界事实随页先核":
        return "随页核专业组边界、左右列和组内专业范围，防止后续字段串组。"
    if action_group == "A3-双人复核事实先核":
        return "先完成双人复核，再回补 PDF 原页、湖北官方侧和必要高校辅证状态。"
    if action_group == "A4-无稳定OCR人工看图":
        return "人工看 PDF 原页定位事实；机器或高校线索只作定位提示，不直接写回。"
    if action_group == "A6-高校辅证提示回接":
        return "先把高校官网辅证接入私有核验材料，再回 PDF 原页和湖北官方侧闭环。"
    return "按常规 PDF 原页和湖北官方侧闭环；完成前不得写回字段事实或进入推荐。"


def index_unique(rows, field):
    indexed = {}
    for row in rows:
        key = clean(row.get(field))
        if not key:
            continue
        if key in indexed:
            raise SystemExit(f"duplicate {field}: {key}")
        indexed[key] = row
    return indexed


def build_rows():
    fact_rows = read_csv(FACT_CHANNEL)
    overlay_rows = read_csv(RESOLUTION_OVERLAY)
    school_rows = read_csv(SCHOOL_PROGRESS)

    overlay_by_page = index_unique(overlay_rows, "页码版面键")
    school_by_code = defaultdict(list)
    for row in school_rows:
        code = clean(row.get("院校代码"))
        if code:
            school_by_code[code].append(row)

    page_keys = {clean(row.get("页码版面键")) for row in fact_rows if clean(row.get("页码版面键"))}
    overlay_keys = set(overlay_by_page)
    if page_keys != overlay_keys:
        raise SystemExit(
            f"page key mismatch fact_channel_vs_overlay; missing={sorted(overlay_keys - page_keys)[:10]}; extra={sorted(page_keys - overlay_keys)[:10]}"
        )

    grouped = defaultdict(list)
    page_fact_counts = Counter(clean(row.get("页码版面键")) for row in fact_rows)
    for row in fact_rows:
        key = (clean(row.get("页码版面键")), clean(row.get("事实核验动作组")))
        if not key[0] or not key[1]:
            raise SystemExit("missing page key or action group in fact channel")
        grouped[key].append(row)

    rows = []
    for (page_key, action_group), facts in grouped.items():
        overlay = overlay_by_page[page_key]
        action_rank = ACTION_RANK.get(action_group, 99)
        exec_order = as_int(overlay.get("来源执行顺序"))
        school_codes = sorted({clean(row.get("院校代码")) for row in facts if clean(row.get("院校代码"))})
        dedup_school_rows = []
        seen_school_progress_ids = set()
        for code in school_codes:
            for school_row in school_by_code.get(code, []):
                school_id = clean(school_row.get("高校源进度看板ID"))
                if school_id and school_id not in seen_school_progress_ids:
                    dedup_school_rows.append(school_row)
                    seen_school_progress_ids.add(school_id)
        school = school_summary(dedup_school_rows)

        field_counter = Counter(
            clean(row.get("字段类别"))
            for row in facts
            if clean(row.get("事实域")) == "字段事实" and clean(row.get("字段类别"))
        )
        row = {
            "事实动作包ID": stable_id("FCFACTPACK", [SOURCE_PDF_SHA256, page_key, action_group]),
            "来源事实证据通道工作台": source_path(FACT_CHANNEL),
            "来源准出执行叠加表": source_path(RESOLUTION_OVERLAY),
            "来源高校官网辅证进度看板": source_path(SCHOOL_PROGRESS),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环页列×事实核验动作组",
            "任务粒度": "同页列同动作组事实包",
            **false_gate_values(),
            "事实动作包序号": 0,
            "来源执行顺序": exec_order,
            "页码版面键": page_key,
            "来源页码": clean(overlay.get("来源页码")),
            "版面列": clean(overlay.get("版面列")),
            "准出闭环波次": clean(overlay.get("准出闭环波次")),
            "执行泳道": clean(overlay.get("执行泳道")),
            "第一闭环页列优先级": clean(overlay.get("第一闭环页列优先级")),
            "事实核验动作组": action_group,
            "动作组排序": action_rank,
            "包执行优先级": f"{exec_order:03d}-{action_rank:02d}",
            "页列事实总数": page_fact_counts[page_key],
            "动作包事实数": len(facts),
            "动作包字段事实数": sum(1 for row in facts if clean(row.get("事实域")) == "字段事实"),
            "动作包专业名归属事实数": sum(1 for row in facts if clean(row.get("事实域")) == "专业名归属"),
            "动作包专业组边界事实数": sum(1 for row in facts if clean(row.get("事实域")) == "专业组边界"),
            "专业计划数字段事实数": field_counter.get("专业计划数", 0),
            "学费字段事实数": field_counter.get("学费", 0),
            "再选科目字段事实数": field_counter.get("再选科目", 0),
            "待人工判定字段事实数": field_counter.get("待人工判定字段", 0),
            "涉及任务数": unique_count(facts, "稳定基座第一闭环明细任务ID"),
            "涉及字段状态数": unique_count(facts, "第一闭环字段核验状态ID"),
            "涉及专业行数": unique_count(facts, "专业行ID"),
            "涉及专业组出现数": unique_count(facts, "专业组出现ID"),
            "涉及院校代码数": len(school_codes),
            "PDF原页通道状态分布": counter_text(row.get("PDF原页通道状态") for row in facts),
            "OCR提示通道状态分布": counter_text(row.get("OCR提示通道状态") for row in facts),
            "机器坐标通道状态分布": counter_text(row.get("机器坐标通道状态") for row in facts),
            "高校官网辅证通道状态分布": counter_text(row.get("高校官网辅证通道状态") for row in facts),
            "湖北官方侧通道状态分布": counter_text(row.get("湖北官方侧通道状态") for row in facts),
            "冲突处理通道状态分布": counter_text(row.get("冲突处理通道状态") for row in facts),
            "双人复核通道状态分布": counter_text(row.get("双人复核通道状态") for row in facts),
            "三方闭环通道状态分布": counter_text(row.get("三方闭环通道状态") for row in facts),
            "专业名归属通道状态分布": counter_text(row.get("专业名归属通道状态") for row in facts),
            "专业组边界通道状态分布": counter_text(row.get("专业组边界通道状态") for row in facts),
            "仍需PDF原页事实数": true_count(facts, "是否仍需PDF原页"),
            "仍需湖北官方侧事实数": true_count(facts, "是否仍需湖北官方侧"),
            "仍需高校辅证事实数": true_count(facts, "是否仍需高校辅证"),
            "仍需冲突处理事实数": true_count(facts, "是否仍需冲突处理"),
            "仍需双人复核事实数": true_count(facts, "是否仍需双人复核"),
            "仍需三方闭环事实数": true_count(facts, "是否仍需三方闭环"),
            "仍需专业名归属事实数": true_count(facts, "是否仍需专业名归属"),
            "仍需专业组边界事实数": true_count(facts, "是否仍需专业组边界"),
            "同校高校源任务去重数": school["count"],
            "同校高校源最高证据层级分布": school["level"],
            "同校高校源下一批优先级分布": school["priority"],
            "同校高校源留存状态分布": school["retention"],
            "同校高校源候选diff去重数": school["candidate_diff"],
            "同校高校源冲突候选去重数": school["conflict"],
            "同校高校源补缺候选去重数": school["fill"],
            "事实集合SHA16": stable_set_sha(row.get("第一闭环事实范围缺口公开账本ID") for row in facts),
            "任务集合SHA16": stable_set_sha(row.get("稳定基座第一闭环明细任务ID") for row in facts),
            "字段状态集合SHA16": stable_set_sha(row.get("第一闭环字段核验状态ID") for row in facts),
            "院校代码集合SHA16": stable_set_sha(school_codes),
            "包级完成证据要求": counter_text(row.get("完成证据要求") for row in facts),
            "包级主阻断原因": counter_text(row.get("当前阻断原因") for row in facts),
            "包级下一步最小核验动作": action_next_step(action_group),
            "公开安全策略": "not_final；fact_action_packet_only；no_field_values；no_school_names；no_major_names；dedup_school_source_context；no_private_paths；no_ocr_text；no_recommendation",
        }
        for field in FALSE_FIELDS:
            if row[field] != "false":
                raise SystemExit(f"non false gate {field}: {row[field]}")
        if as_int(row["动作包事实数"]) != (
            as_int(row["动作包字段事实数"]) + as_int(row["动作包专业名归属事实数"]) + as_int(row["动作包专业组边界事实数"])
        ):
            raise SystemExit(f"fact domain mismatch for {(page_key, action_group)}")
        if as_int(row["动作包事实数"]) != as_int(row["仍需PDF原页事实数"]):
            raise SystemExit(f"all packet facts should still require PDF page for {(page_key, action_group)}")
        if as_int(row["动作包事实数"]) != as_int(row["仍需湖北官方侧事实数"]):
            raise SystemExit(f"all packet facts should still require Hubei official side for {(page_key, action_group)}")
        rows.append(row)

    rows.sort(
        key=lambda row: (
            as_int(row["来源执行顺序"]),
            as_int(row["动作组排序"]),
            row["页码版面键"],
        )
    )
    for index, row in enumerate(rows, 1):
        row["事实动作包序号"] = index

    return rows, fact_rows, overlay_rows, school_rows


def build_summary(rows, fact_rows, overlay_rows, school_rows):
    facts_by_packet = Counter(row["事实核验动作组"] for row in rows)
    fact_count_by_packet_action = defaultdict(int)
    for row in rows:
        fact_count_by_packet_action[row["事实核验动作组"]] += as_int(row["动作包事实数"])

    return {
        "status": "issue19_first_closure_fact_action_packets_v1_not_final",
        "generated_by": "build_issue19_first_closure_fact_action_packets_v1.py",
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_fact_channel": source_path(FACT_CHANNEL),
        "source_resolution_overlay": source_path(RESOLUTION_OVERLAY),
        "source_school_progress": source_path(SCHOOL_PROGRESS),
        "output_table": source_path(OUTPUT),
        "row_count": len(rows),
        "source_fact_channel_row_count": len(fact_rows),
        "source_overlay_row_count": len(overlay_rows),
        "source_school_progress_row_count": len(school_rows),
        "unique_page_side_count": unique_count(rows, "页码版面键"),
        "unique_action_group_count": unique_count(rows, "事实核验动作组"),
        "fact_count": sum(as_int(row.get("动作包事实数")) for row in rows),
        "field_fact_count": sum(as_int(row.get("动作包字段事实数")) for row in rows),
        "major_assignment_fact_count": sum(as_int(row.get("动作包专业名归属事实数")) for row in rows),
        "group_boundary_fact_count": sum(as_int(row.get("动作包专业组边界事实数")) for row in rows),
        "task_ref_count": sum(as_int(row.get("涉及任务数")) for row in rows),
        "field_status_ref_count": sum(as_int(row.get("涉及字段状态数")) for row in rows),
        "action_packet_counts": dict(facts_by_packet),
        "action_fact_counts": dict(sorted(fact_count_by_packet_action.items())),
        "field_category_counts": {
            "专业计划数": sum(as_int(row.get("专业计划数字段事实数")) for row in rows),
            "学费": sum(as_int(row.get("学费字段事实数")) for row in rows),
            "再选科目": sum(as_int(row.get("再选科目字段事实数")) for row in rows),
            "待人工判定字段": sum(as_int(row.get("待人工判定字段事实数")) for row in rows),
        },
        "missing_pdf_count": sum(as_int(row.get("仍需PDF原页事实数")) for row in rows),
        "missing_hubei_official_count": sum(as_int(row.get("仍需湖北官方侧事实数")) for row in rows),
        "missing_school_source_count": sum(as_int(row.get("仍需高校辅证事实数")) for row in rows),
        "missing_conflict_count": sum(as_int(row.get("仍需冲突处理事实数")) for row in rows),
        "missing_double_review_count": sum(as_int(row.get("仍需双人复核事实数")) for row in rows),
        "missing_three_way_count": sum(as_int(row.get("仍需三方闭环事实数")) for row in rows),
        "missing_major_assignment_count": sum(as_int(row.get("仍需专业名归属事实数")) for row in rows),
        "missing_group_boundary_count": sum(as_int(row.get("仍需专业组边界事实数")) for row in rows),
        "private_writeback_review_ready_count": 0,
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "note": "每行对应一个页列和一个事实核验动作组。同校高校源字段只是同校上下文，先按高校源进度看板ID去重后再聚合，不能从事实级工作台跨行求和。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"fact action packets contain forbidden public tokens: {hits[:10]}")


def main():
    rows, fact_rows, overlay_rows, school_rows = build_rows()
    summary = build_summary(rows, fact_rows, overlay_rows, school_rows)
    assert_public_safe(rows, summary)
    write_csv(OUTPUT, rows, PACKET_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")


if __name__ == "__main__":
    main()
