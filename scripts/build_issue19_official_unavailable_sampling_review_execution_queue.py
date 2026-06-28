#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PACKETS = (
    ROOT / "data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv"
)
OVERLAY = (
    ROOT / "data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv"
)
PRIVATE_OVERLAY = (
    ROOT / "private/review-assets/issue19-official-unavailable-sampling-review-overlay/sampling-review-overlay.csv"
)

OUTPUT = (
    ROOT / "data/working/issue19-official-unavailable-sampling-review-execution-queue.csv"
)
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-official-unavailable-sampling-review-execution-queue-summary.json"
)

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_official_unavailable_sampling_review_execution_queue"

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许写回字段事实",
]

FIELDS = [
    "官方不可得抽样页列执行队列ID",
    "来源抽样页列包公开账本",
    "来源抽样复核Overlay公开账本",
    "来源本地抽样复核Overlay",
    "来源本地抽样页列核验包",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许写回字段事实",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列包排序",
    "执行队列总序",
    "执行泳道",
    "执行优先级",
    "人工核验方式",
    "人工最小动作",
    "抽检失败升级规则",
    "页列抽样明细数",
    "涉及专业行数",
    "涉及专业组数",
    "高风险100%核验明细数",
    "C0冲突明细数",
    "C1官网补缺明细数",
    "C7官网未匹配明细数",
    "C2强辅证抽样明细数",
    "P3低风险抽样明细数",
    "R4阻断明细数",
    "R3高风险明细数",
    "R1低风险明细数",
    "R0观察明细数",
    "双人复核明细数",
    "PDF原页必核明细数",
    "湖北官方侧必核明细数",
    "高校辅证必核明细数",
    "高校辅证待补源明细数",
    "PDF原页已填字段数",
    "湖北官方侧已填字段数",
    "高校辅证已填字段数",
    "三方一致性可评估明细数",
    "抽检失败明细数",
    "升级要求明细数",
    "首轮复核完成明细数",
    "次轮复核完成明细数",
    "页列完成状态",
    "字段事实写回状态",
    "私有页图证据编号",
    "私有页图SHA256",
    "私有OCR摘要证据编号",
    "私有OCR摘要SHA256",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页列HTML证据编号",
    "私有页列HTML_SHA256",
    "公开安全策略",
    "下一步",
]

LANE_META = {
    "E0": {
        "label": "E0-冲突/错位先核",
        "priority": "00-先核PDF原页和湖北官方侧冲突",
        "mode": "双人优先",
        "action": "逐条核 PDF 原页、湖北官方侧和必要高校辅证；冲突未消除前不得写回字段。",
    },
    "E1": {
        "label": "E1-官网未匹配专业名归属",
        "priority": "01-先确认专业名和归属",
        "mode": "双人优先",
        "action": "先确认 PDF 原页专业名、组内位置和湖北官方侧，再用高校辅证确认是否同一专业。",
    },
    "E2": {
        "label": "E2-官网补缺候选核页",
        "priority": "02-核PDF原页缺口和湖北官方侧",
        "mode": "单人初核加抽检",
        "action": "用高校辅证作为提示，回看 PDF 原页和湖北官方侧补齐缺口字段。",
    },
    "E3": {
        "label": "E3-C2强辅证抽检",
        "priority": "03-强辅证样本抽检",
        "mode": "单人初核加抽检",
        "action": "核 PDF 原页和湖北官方侧；若样本失败，按同页列、同校或同组升级。",
    },
    "E4": {
        "label": "E4-P3低风险抽检",
        "priority": "04-低风险样本验收",
        "mode": "单人抽检",
        "action": "抽检 PDF 原页和湖北官方侧；失败即升级，不得因为低风险直接定稿。",
    },
}


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


def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def page_side_key(row):
    return (str(row.get("来源页码", "")).strip(), str(row.get("版面列", "")).strip())


def false_values():
    return {field: "false" for field in FALSE_FIELDS}


def choose_lane(row):
    if as_int(row.get("C0冲突明细数")):
        return "E0"
    if as_int(row.get("C7官网未匹配明细数")):
        return "E1"
    if as_int(row.get("C1官网补缺明细数")):
        return "E2"
    if as_int(row.get("C2强辅证抽样明细数")):
        return "E3"
    if as_int(row.get("P3低风险抽样明细数")):
        return "E4"
    return "E4"


def completion_status(row):
    detail_count = as_int(row.get("页列抽样明细数"))
    pdf_done = as_int(row.get("PDF原页已填字段数"))
    hubei_done = as_int(row.get("湖北官方侧已填字段数"))
    tri_done = as_int(row.get("三方一致性可评估明细数"))
    if pdf_done == 0 and hubei_done == 0 and tri_done == 0:
        return "R0-未开始私有核验记录"
    if pdf_done < detail_count or hubei_done < detail_count:
        return "R1-PDF原页或湖北官方侧未填完"
    if tri_done < detail_count:
        return "R2-等待三方一致性和抽检升级判断"
    return "R3-可进入字段写回复查但仍非最终"


def school_support_required_count(rows):
    count = 0
    pending_source_count = 0
    for row in rows:
        status = row.get("高校官网或招生章程辅证状态", "")
        action = row.get("官网辅证自动动作", "")
        if status == "not_yet_school_source_searched_in_full_workbench":
            pending_source_count += 1
            continue
        if action.startswith(("C0-", "C1-", "C2-", "C7-")):
            count += 1
    return count, pending_source_count


def build():
    packet_rows = read_csv(PACKETS)
    overlay_rows = read_csv(OVERLAY)
    private_rows = read_csv(PRIVATE_OVERLAY)
    overlay_by_page_side = defaultdict(list)
    for row in overlay_rows:
        overlay_by_page_side[page_side_key(row)].append(row)
    private_by_page_side = defaultdict(list)
    for row in private_rows:
        private_by_page_side[page_side_key(row)].append(row)

    sorted_packets = sorted(
        packet_rows,
        key=lambda row: (
            choose_lane(row),
            -as_int(row.get("双人复核明细数")),
            -as_int(row.get("页列抽样明细数")),
            as_int(row.get("页列包排序")),
        ),
    )
    queue_rows = []
    for order, row in enumerate(sorted_packets, start=1):
        lane = choose_lane(row)
        meta = LANE_META[lane]
        key = page_side_key(row)
        detail_rows = overlay_by_page_side.get(key, [])
        private_detail_rows = private_by_page_side.get(key, [])
        school_required, school_pending = school_support_required_count(private_detail_rows)
        detail_count = as_int(row.get("页列抽样明细数"))
        queue_rows.append({
            "官方不可得抽样页列执行队列ID": stable_id(
                "SAMPLINGEXECQ",
                [row.get("页码版面键", ""), SOURCE_PDF_SHA256, DATA_STAGE],
            ),
            "来源抽样页列包公开账本": (
                "data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv"
            ),
            "来源抽样复核Overlay公开账本": (
                "data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv"
            ),
            "来源本地抽样复核Overlay": "local_sampling_review_overlay_not_public",
            "来源本地抽样页列核验包": "local_sampling_review_packet_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "官方不可得抽样页列核验执行队列",
            **false_values(),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "页码版面键": row.get("页码版面键", ""),
            "页列包排序": row.get("页列包排序", ""),
            "执行队列总序": str(order),
            "执行泳道": meta["label"],
            "执行优先级": meta["priority"],
            "人工核验方式": meta["mode"],
            "人工最小动作": meta["action"],
            "抽检失败升级规则": "同页列100%；同校出现2个失败则同校100%；同专业组失败则整组100%。",
            "页列抽样明细数": row.get("页列抽样明细数", ""),
            "涉及专业行数": row.get("涉及专业行数", ""),
            "涉及专业组数": row.get("涉及专业组数", ""),
            "高风险100%核验明细数": row.get("高风险100%核验明细数", ""),
            "C0冲突明细数": row.get("C0冲突明细数", ""),
            "C1官网补缺明细数": row.get("C1官网补缺明细数", ""),
            "C7官网未匹配明细数": row.get("C7官网未匹配明细数", ""),
            "C2强辅证抽样明细数": row.get("C2强辅证抽样明细数", ""),
            "P3低风险抽样明细数": row.get("P3低风险抽样明细数", ""),
            "R4阻断明细数": row.get("R4阻断明细数", ""),
            "R3高风险明细数": row.get("R3高风险明细数", ""),
            "R1低风险明细数": row.get("R1低风险明细数", ""),
            "R0观察明细数": row.get("R0观察明细数", ""),
            "双人复核明细数": row.get("双人复核明细数", ""),
            "PDF原页必核明细数": str(detail_count),
            "湖北官方侧必核明细数": str(detail_count),
            "高校辅证必核明细数": str(school_required),
            "高校辅证待补源明细数": str(school_pending),
            "PDF原页已填字段数": row.get("PDF原页已填字段数", ""),
            "湖北官方侧已填字段数": row.get("湖北官方侧已填字段数", ""),
            "高校辅证已填字段数": row.get("高校辅证已填字段数", ""),
            "三方一致性可评估明细数": row.get("三方一致性可评估明细数", ""),
            "抽检失败明细数": row.get("抽检失败明细数", ""),
            "升级要求明细数": row.get("升级要求明细数", ""),
            "首轮复核完成明细数": row.get("首轮复核完成明细数", ""),
            "次轮复核完成明细数": row.get("次轮复核完成明细数", ""),
            "页列完成状态": completion_status(row),
            "字段事实写回状态": row.get("字段事实写回状态", ""),
            "私有页图证据编号": row.get("私有页图证据编号", ""),
            "私有页图SHA256": row.get("私有页图SHA256", ""),
            "私有OCR摘要证据编号": row.get("私有OCR摘要证据编号", ""),
            "私有OCR摘要SHA256": row.get("私有OCR摘要SHA256", ""),
            "私有页列CSV证据编号": row.get("私有页列CSV证据编号", ""),
            "私有页列CSV_SHA256": row.get("私有页列CSV_SHA256", ""),
            "私有页列HTML证据编号": row.get("私有页列HTML证据编号", ""),
            "私有页列HTML_SHA256": row.get("私有页列HTML_SHA256", ""),
            "公开安全策略": (
                "公开队列只保存页列计数、执行状态、证据编号和SHA；"
                "学校专业明细、字段记录、OCR明细和人工记录只留在本地私有包。"
            ),
            "下一步": (
                "按执行队列总序打开本地页列HTML/CSV；把PDF原页、湖北官方侧、"
                "高校辅证和双人复核结论写回本地抽样复核Overlay。"
            ),
        })
        if not detail_rows:
            raise ValueError(f"missing overlay rows for page side {key}")

    write_csv(OUTPUT, queue_rows, FIELDS)
    summary = {
        "status": "issue19_official_unavailable_sampling_review_execution_queue_not_final",
        "generated_by": "build_issue19_official_unavailable_sampling_review_execution_queue.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_packets": (
            "data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv"
        ),
        "source_overlay": (
            "data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv"
        ),
        "output_table": (
            "data/working/issue19-official-unavailable-sampling-review-execution-queue.csv"
        ),
        "row_grain": "PDF页码×版面列",
        "row_count": len(queue_rows),
        "unique_page_side_count": len({row["页码版面键"] for row in queue_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in queue_rows}),
        "sampling_detail_count": sum(as_int(row["页列抽样明细数"]) for row in queue_rows),
        "high_risk_100pct_detail_count": sum(as_int(row["高风险100%核验明细数"]) for row in queue_rows),
        "c0_conflict_detail_count": sum(as_int(row["C0冲突明细数"]) for row in queue_rows),
        "c1_fill_candidate_detail_count": sum(as_int(row["C1官网补缺明细数"]) for row in queue_rows),
        "c7_unmatched_detail_count": sum(as_int(row["C7官网未匹配明细数"]) for row in queue_rows),
        "c2_sample_detail_count": sum(as_int(row["C2强辅证抽样明细数"]) for row in queue_rows),
        "p3_sample_detail_count": sum(as_int(row["P3低风险抽样明细数"]) for row in queue_rows),
        "double_review_required_count": sum(as_int(row["双人复核明细数"]) for row in queue_rows),
        "pdf_required_detail_count": sum(as_int(row["PDF原页必核明细数"]) for row in queue_rows),
        "hubei_official_required_detail_count": sum(as_int(row["湖北官方侧必核明细数"]) for row in queue_rows),
        "school_support_required_detail_count": sum(as_int(row["高校辅证必核明细数"]) for row in queue_rows),
        "school_support_pending_source_detail_count": sum(as_int(row["高校辅证待补源明细数"]) for row in queue_rows),
        "pdf_page_filled_field_count": sum(as_int(row["PDF原页已填字段数"]) for row in queue_rows),
        "hubei_official_filled_field_count": sum(as_int(row["湖北官方侧已填字段数"]) for row in queue_rows),
        "school_support_filled_field_count": sum(as_int(row["高校辅证已填字段数"]) for row in queue_rows),
        "tri_consistency_assessable_count": sum(as_int(row["三方一致性可评估明细数"]) for row in queue_rows),
        "sampling_failure_count": sum(as_int(row["抽检失败明细数"]) for row in queue_rows),
        "escalation_required_count": sum(as_int(row["升级要求明细数"]) for row in queue_rows),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "execution_lane_counts": dict(Counter(row["执行泳道"] for row in queue_rows)),
        "completion_status_counts": dict(Counter(row["页列完成状态"] for row in queue_rows)),
        "policy": {
            "boundary": "本队列只安排人工核验顺序和状态同步，不确认字段、不写回、不生成学校专业建议或志愿推荐。",
            "minimum_manual_scope": f"{len(queue_rows)}个页列包；{sum(as_int(row['页列抽样明细数']) for row in queue_rows)}条抽样明细；PDF原页和湖北官方侧均需闭环。",
        },
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    build()
    print(f"写出 {OUTPUT.relative_to(ROOT)}")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
