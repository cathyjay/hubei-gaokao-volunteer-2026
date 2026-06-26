#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]
V3_ADMISSION_DETAIL = ROOT / "data/working/issue19-candidate-v3-admission-detail.csv"
OUTPUT = ROOT / "data/working/issue19-candidate-v3-admission-detail-review-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v3-admission-detail-review-queue-summary.json"

DATA_STAGE = "issue19_candidate_v3_admission_detail_review_queue"

PRIORITY_ORDER = {
    "D0-0明细或边界问题先补齐": 0,
    "D1-历史候选逐专业核页": 1,
    "D2-数字媒体技术逐专业核页": 2,
    "D3-偏好专业可接受性核验": 3,
    "D4-硬风险专业排除或调剂风险核验": 4,
    "D5-特殊限制专业核验": 5,
    "D6-组内调剂接受度核验": 6,
}

REQUIRED_FIELDS = [
    "PDF原页",
    "湖北官方系统/省招办计划",
    "高校官网/招生章程",
    "院校代码和院校名称",
    "院校专业组代码和完整专业组边界",
    "专业代号",
    "专业名称及备注",
    "专业计划数",
    "学费",
    "再选科目",
    "校区/办学地点",
    "体检/语种/单科/专项限制",
    "家庭接受度",
    "调剂影响",
]

SUSPICIOUS_SCHOOL_NAMES = {
    "北京",
    "上海",
    "天津",
    "重庆",
    "河北",
    "山西",
    "辽宁",
    "吉林",
    "黑龙江",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "海南",
    "四川",
    "贵州",
    "云南",
    "陕西",
    "甘肃",
    "青海",
    "台湾",
    "内蒙古",
    "广西",
    "西藏",
    "宁夏",
    "新疆",
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def split_labels(value):
    if not value:
        return set()
    return {part.strip() for part in str(value).replace(";", "；").split("；") if part.strip()}


def contains_any(value, words):
    return any(word in str(value or "") for word in words)


def is_default_rejected(row):
    return str(row.get("机器专业接受度初判", "")).startswith("默认不能接受")


def is_special_pause(row):
    return str(row.get("机器专业接受度初判", "")).startswith("暂缓判断")


def is_preference(row):
    return bool(row.get("专业偏好方向", "").strip())


def is_digital_media(row):
    text = "；".join([row.get("专业偏好方向", ""), row.get("专业名称及备注OCR", "")])
    return "数字媒体技术" in text


def has_suspicious_school_name(row):
    name = row.get("院校名称OCR", "").strip()
    return name in SUSPICIOUS_SCHOOL_NAMES or (name and len(name) <= 2 and "大学" not in name and "学院" not in name)


def review_priority(row):
    batch = row.get("复核批次", "")
    if row.get("是否0明细占位") == "true" or "同页边界风险" in batch or has_suspicious_school_name(row):
        return "D0-0明细或边界问题先补齐"
    if "历史候选" in batch:
        return "D1-历史候选逐专业核页"
    if is_digital_media(row):
        return "D2-数字媒体技术逐专业核页"
    if is_preference(row) and not is_default_rejected(row) and not is_special_pause(row):
        return "D3-偏好专业可接受性核验"
    if is_default_rejected(row):
        return "D4-硬风险专业排除或调剂风险核验"
    if is_special_pause(row):
        return "D5-特殊限制专业核验"
    return "D6-组内调剂接受度核验"


def review_reason(row, group_stats):
    pieces = []
    priority = row.get("核验优先级", "")
    if priority.startswith("D0"):
        pieces.append("专业组边界或明细缺失会直接影响调剂范围，先补齐原始招生明细")
    if has_suspicious_school_name(row):
        pieces.append("院校名称 OCR 疑似截断，必须先核院校代码和完整院校名称")
    if priority.startswith("D1"):
        pieces.append("历史候选涉及既有冲稳保判断，需优先确认 2026 专业变化")
    if priority.startswith("D2"):
        pieces.append("命中当前第一优先专业方向：数字媒体技术")
    if priority.startswith("D3"):
        pieces.append("命中当前偏好专业且未触发机器自动排除")
    if priority.startswith("D4"):
        pieces.append("机器初判为默认不能接受，需确认是否排除该专业或整个专业组")
    if priority.startswith("D5"):
        pieces.append("存在体检、语种、单科、专项等限制线索")
    if priority.startswith("D6"):
        pieces.append("该专业关系到是否可以接受组内调剂")
    if group_stats["默认不能接受专业数"]:
        pieces.append(f"同组有 {group_stats['默认不能接受专业数']} 条默认不能接受专业")
    if group_stats["暂缓判断专业数"]:
        pieces.append(f"同组有 {group_stats['暂缓判断专业数']} 条特殊限制待核专业")
    if row.get("专业字段完整性标记"):
        pieces.append(f"字段完整性待核：{row['专业字段完整性标记']}")
    if as_int(row.get("专业行高严重结构异常数")):
        pieces.append("专业行存在高严重结构异常")
    return "；".join(dict.fromkeys(pieces))


def fidelity_tasks(row):
    tasks = list(REQUIRED_FIELDS)
    if row.get("是否0明细占位") == "true":
        return "补齐专业组内全部招生明细；" + "；".join(tasks[:3])
    if row.get("专业偏好方向"):
        tasks.append("专业方向课程和就业出口")
    return "；".join(tasks)


def group_transfer_risk(group_rows):
    default_rejected = sum(is_default_rejected(row) for row in group_rows)
    special_pause = sum(is_special_pause(row) for row in group_rows)
    placeholder = sum(row.get("是否0明细占位") == "true" for row in group_rows)
    if placeholder:
        return "T0-不可判断：专业明细缺失"
    if default_rejected:
        return "T1-高：同组存在默认不能接受专业"
    if special_pause:
        return "T2-中：同组存在特殊限制待核专业"
    return "T3-待家庭确认：机器未见自动阻断"


def next_step(row, transfer_risk):
    if row.get("是否0明细占位") == "true":
        return "先回看第19期原页或湖北官方系统，补齐该专业组全部招生专业后再判断。"
    if transfer_risk.startswith("T1"):
        return "先核该行字段和同组默认不能接受专业；若不能接受专业确认存在，谨慎服从调剂或剔除该组。"
    if row.get("核验优先级", "").startswith(("D1", "D2", "D3")):
        return "先核 PDF 原页、湖北官方系统和高校章程，再让家庭确认该专业接受度。"
    if row.get("核验优先级", "").startswith("D4"):
        return "先核风险字段是否真实；若风险确认，记录为排除或调剂风险。"
    if row.get("核验优先级", "").startswith("D5"):
        return "先核体检、语种、单科、专项等限制是否影响报考资格和调剂。"
    return "作为同组调剂接受度判断材料，随该专业组一起核页。"


def sort_key(row):
    return (
        PRIORITY_ORDER.get(row["核验优先级"], 99),
        row.get("院校代码", ""),
        row.get("2026院校专业组代码", ""),
        as_int(row.get("专业组内专业序号")) or 9999,
        row.get("专业代号OCR", ""),
        row.get("招生明细主表行ID", ""),
    )


def main():
    detail_rows = read_csv(V3_ADMISSION_DETAIL)
    rows_by_entry = defaultdict(list)
    for row in detail_rows:
        rows_by_entry[row["候选V3入口ID"]].append(row)

    group_stats_by_entry = {}
    for entry_id, rows in rows_by_entry.items():
        group_stats_by_entry[entry_id] = {
            "同组真实招生明细数": sum(row.get("是否真实招生明细") == "true" for row in rows),
            "同组0明细占位数": sum(row.get("是否0明细占位") == "true" for row in rows),
            "同组默认不能接受专业数": sum(is_default_rejected(row) for row in rows),
            "同组暂缓判断专业数": sum(is_special_pause(row) for row in rows),
            "同组偏好专业数": sum(is_preference(row) for row in rows),
            "同组数字媒体技术专业数": sum(is_digital_media(row) for row in rows),
            "同组调剂机器风险": group_transfer_risk(rows),
        }

    output_rows = []
    for row in detail_rows:
        stats = group_stats_by_entry[row["候选V3入口ID"]]
        priority = review_priority(row)
        output = {
            "逐专业复核队列ID": stable_id("V3Q", [row["招生明细主表行ID"], priority]),
            "来源主表": "data/working/issue19-candidate-v3-admission-detail.csv",
            "招生明细主表行ID": row["招生明细主表行ID"],
            "核验优先级": priority,
            "核验优先级序号": str(PRIORITY_ORDER.get(priority, 99)),
            "复核原因": "",
            "必须核验字段": "",
            "同组调剂机器风险": stats["同组调剂机器风险"],
            "同组真实招生明细数": str(stats["同组真实招生明细数"]),
            "同组0明细占位数": str(stats["同组0明细占位数"]),
            "同组默认不能接受专业数": str(stats["同组默认不能接受专业数"]),
            "同组暂缓判断专业数": str(stats["同组暂缓判断专业数"]),
            "同组偏好专业数": str(stats["同组偏好专业数"]),
            "同组数字媒体技术专业数": str(stats["同组数字媒体技术专业数"]),
            "来源期号": row.get("来源期号", ""),
            "来源PDF_SHA256": row.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "最终可用": "false",
            "核验状态": "pending_v3_detail_review_queue",
            "候选V3入口ID": row.get("候选V3入口ID", ""),
            "复核批次": row.get("复核批次", ""),
            "入口类型": row.get("入口类型", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "2026院校专业组代码": row.get("2026院校专业组代码", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "来源页码": row.get("来源页码", ""),
            "私有页图证据编号": row.get("私有页图证据编号", ""),
            "私有页图SHA256": row.get("私有页图SHA256", ""),
            "专业行来源": row.get("专业行来源", ""),
            "专业行ID": row.get("专业行ID", ""),
            "是否真实招生明细": row.get("是否真实招生明细", ""),
            "是否0明细占位": row.get("是否0明细占位", ""),
            "专业组内专业序号": row.get("专业组内专业序号", ""),
            "专业代号OCR": row.get("专业代号OCR", ""),
            "专业名称及备注OCR": row.get("专业名称及备注OCR", ""),
            "再选科目OCR候选": row.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": row.get("专业计划数OCR候选", ""),
            "专业计划数是否纯数字": row.get("专业计划数是否纯数字", ""),
            "学费OCR候选": row.get("学费OCR候选", ""),
            "学费OCR数字候选": row.get("学费OCR数字候选", ""),
            "学费是否纯数字": row.get("学费是否纯数字", ""),
            "专业偏好方向": row.get("专业偏好方向", ""),
            "专业风险类型": row.get("专业风险类型", ""),
            "专业字段完整性标记": row.get("专业字段完整性标记", ""),
            "专业行结构异常数": row.get("专业行结构异常数", ""),
            "专业行高严重结构异常数": row.get("专业行高严重结构异常数", ""),
            "机器专业接受度初判": row.get("机器专业接受度初判", ""),
            "机器阻断或待核原因": row.get("机器阻断或待核原因", ""),
            "调剂影响初判": row.get("调剂影响初判", ""),
            "PDF字段核验状态": row.get("PDF字段核验状态", ""),
            "湖北官方系统字段核验状态": row.get("湖北官方系统字段核验状态", ""),
            "高校官网/章程字段核验状态": row.get("高校官网/章程字段核验状态", ""),
            "校区/办学地点字段核验状态": "pending_location_review",
            "体检/语种/单科/专项限制核验状态": "pending_special_requirement_review",
            "家庭接受度人工结论状态": row.get("家庭接受度人工结论状态", ""),
            "调剂影响人工结论状态": row.get("调剂影响人工结论状态", ""),
            "字段核验状态": row.get("字段核验状态", ""),
            "专业组完整性人工结论状态": "pending_group_completeness_review",
            "湖北官方系统证据编号": "",
            "湖北官方系统证据SHA256": "",
            "高校官网/章程证据编号": "",
            "高校官网/章程证据SHA256": "",
            "人工核验人": "",
            "人工核验时间": "",
            "人工核验备注": "",
            "可进入最终专业列表": "false",
            "可进入下一阶段": "false",
            "下一步": "",
        }
        output["复核原因"] = review_reason(output, {
            "默认不能接受专业数": stats["同组默认不能接受专业数"],
            "暂缓判断专业数": stats["同组暂缓判断专业数"],
        })
        output["必须核验字段"] = fidelity_tasks(row)
        output["下一步"] = next_step(output, output["同组调剂机器风险"])
        output_rows.append(output)

    output_rows.sort(key=sort_key)
    write_csv(OUTPUT, output_rows, list(output_rows[0].keys()))

    priority_counts = Counter(row["核验优先级"] for row in output_rows)
    transfer_risk_counts = Counter(row["同组调剂机器风险"] for row in output_rows)
    batch_counts = Counter(row["复核批次"] for row in output_rows)
    school_priority_counts = Counter()
    for row in output_rows:
        if row["核验优先级"] in {
            "D0-0明细或边界问题先补齐",
            "D1-历史候选逐专业核页",
            "D2-数字媒体技术逐专业核页",
            "D3-偏好专业可接受性核验",
        }:
            school_priority_counts[row["院校名称OCR"]] += 1

    summary = {
        "status": "issue19_candidate_v3_admission_detail_review_queue_not_final",
        "generated_by": Path(__file__).name,
        "source_table": str(V3_ADMISSION_DETAIL.relative_to(ROOT)),
        "output_table": str(OUTPUT.relative_to(ROOT)),
        "row_count": len(output_rows),
        "real_admission_detail_count": sum(row["是否真实招生明细"] == "true" for row in output_rows),
        "zero_detail_placeholder_count": sum(row["是否0明细占位"] == "true" for row in output_rows),
        "unique_queue_id_count": len({row["逐专业复核队列ID"] for row in output_rows}),
        "priority_counts": dict(priority_counts),
        "transfer_risk_counts": dict(transfer_risk_counts),
        "batch_counts": dict(batch_counts),
        "top_priority_school_counts": dict(school_priority_counts.most_common(30)),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "major_final_available_count": sum(row["可进入最终专业列表"] == "true" for row in output_rows),
        "fidelity_note": "该队列一行对应一个招生专业或0明细占位，用于安排 PDF 原页、湖北官方系统、高校官网/章程、家庭接受度和调剂影响核验顺序，不是填报建议。",
        "review_schema_note": "官方系统、高校官网/章程、校区/办学地点、特殊限制、专业组完整性、核验人和核验时间字段为后续人工核验落点；为空代表尚未核验，不得升级。",
        "inputs": input_snapshot(ROOT, [V3_ADMISSION_DETAIL]),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(output_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
