#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

ACTION_PACKETS = WORKING / "issue19-first-closure-fact-action-packets-v1-public-ledger.csv"
FACT_RESOLUTION = WORKING / "issue19-first-closure-fact-resolution-gate-v1-public-ledger.csv"
FACT_CHANNEL = WORKING / "issue19-first-closure-fact-evidence-channel-workbench-v1-public-ledger.csv"

OUTPUT = WORKING / "issue19-first-closure-fact-action-packet-resolution-gate-v1-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-fact-action-packet-resolution-gate-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_fact_action_packet_resolution_gate_v1"

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
    "是否可以自动闭环",
]

GATE_FIELDS = [
    "第一闭环事实动作包准出门禁ID",
    "来源第一闭环事实动作包",
    "来源第一闭环事实准出门禁账本",
    "来源第一闭环事实证据通道工作台",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "准出门禁序号",
    "事实动作包ID",
    "事实动作包序号",
    "页码版面键",
    "来源页码",
    "版面列",
    "准出闭环波次",
    "执行泳道",
    "第一闭环页列优先级",
    "事实核验动作组",
    "动作组排序",
    "包执行优先级",
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
    "PDF原页待补事实数",
    "湖北官方侧待补事实数",
    "高校辅证待补事实数",
    "冲突待处理事实数",
    "双人复核待完成事实数",
    "三方闭环待完成事实数",
    "专业名归属待闭环事实数",
    "专业组边界待闭环事实数",
    "可进入私有写回评审事实数",
    "动作包准出状态",
    "动作包主缺口桶",
    "动作包准出阻断等级",
    "事实准出状态分布",
    "事实准出阻断等级分布",
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
    "事实集合SHA16",
    "任务集合SHA16",
    "字段状态集合SHA16",
    "院校代码集合SHA16",
    "准出完成条件",
    "下一步动作包准出动作",
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


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def true_count(rows, field):
    return sum(1 for row in rows if clean(row.get(field)) == "true")


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


def packet_status(row):
    missing_fields = [
        "PDF原页待补事实数",
        "湖北官方侧待补事实数",
        "高校辅证待补事实数",
        "冲突待处理事实数",
        "双人复核待完成事实数",
        "三方闭环待完成事实数",
        "专业名归属待闭环事实数",
        "专业组边界待闭环事实数",
    ]
    if any(as_int(row.get(field)) for field in missing_fields):
        return "blocked_missing_required_evidence"
    if as_int(row.get("可进入私有写回评审事实数")) != as_int(row.get("动作包事实数")):
        return "blocked_not_all_facts_ready_for_private_writeback_review"
    return "ready_for_private_writeback_review"


def blocker_bucket(row):
    checks = [
        ("冲突待处理事实数", "G0-冲突待处理"),
        ("双人复核待完成事实数", "G1-双人复核待完成"),
        ("专业名归属待闭环事实数", "G2-专业名归属待闭环"),
        ("专业组边界待闭环事实数", "G3-专业组边界待闭环"),
        ("高校辅证待补事实数", "G4-高校辅证待补"),
        ("PDF原页待补事实数", "G5-PDF湖北官方待闭环"),
        ("湖北官方侧待补事实数", "G5-PDF湖北官方待闭环"),
        ("三方闭环待完成事实数", "G6-三方闭环待完成"),
    ]
    for field, bucket in checks:
        if as_int(row.get(field)):
            return bucket
    return "G9-可进入私有写回评审"


def blocker_level(action_group):
    if action_group == "A0-W0B0冲突事实先核":
        return "R0-W0B0冲突阻断"
    if action_group in {"A1-专业名归属事实先核", "A2-专业组边界事实随页先核"}:
        return "R1-结构事实阻断"
    if action_group == "A3-双人复核事实先核":
        return "R2-双人复核阻断"
    if action_group == "A4-无稳定OCR人工看图":
        return "R3-人工看图阻断"
    if action_group == "A6-高校辅证提示回接":
        return "R4-高校辅证回接阻断"
    return "R5-常规PDF湖北官方阻断"


def next_step(row):
    bucket = clean(row.get("动作包主缺口桶"))
    if bucket == "G0-冲突待处理":
        return "先核 PDF 原页和湖北官方侧；冲突字段或结构事实必须双人复核后才能进入写回评审。"
    if bucket == "G1-双人复核待完成":
        return "先完成双人复核，再回补 PDF 原页、湖北官方侧和三方闭环状态。"
    if bucket == "G2-专业名归属待闭环":
        return "先核专业名、备注和限定词归属，防止后续字段写到错误专业行。"
    if bucket == "G3-专业组边界待闭环":
        return "先核页列和专业组边界，再继续组内字段闭环。"
    if bucket == "G4-高校辅证待补":
        return "先把高校官网辅证接入核验材料，但不得替代湖北官方计划定稿。"
    if bucket == "G5-PDF湖北官方待闭环":
        return "按 PDF 原页和湖北官方侧逐项核验；完成前不得写回字段事实或作为推荐依据。"
    if bucket == "G6-三方闭环待完成":
        return "补齐 PDF 原页、湖北官方侧和必要高校辅证的一致性证据后再评审。"
    return "进入私有写回评审前仍需人工复核门禁。"


def require_same(action_packet, gate_row, packet_facts):
    if as_int(gate_row["动作包事实数"]) != len(packet_facts):
        raise SystemExit(f"packet fact count mismatch: {action_packet.get('事实动作包ID')}")
    for old_field, new_field in {
        "仍需PDF原页事实数": "PDF原页待补事实数",
        "仍需湖北官方侧事实数": "湖北官方侧待补事实数",
        "仍需高校辅证事实数": "高校辅证待补事实数",
        "仍需冲突处理事实数": "冲突待处理事实数",
        "仍需双人复核事实数": "双人复核待完成事实数",
        "仍需三方闭环事实数": "三方闭环待完成事实数",
        "仍需专业名归属事实数": "专业名归属待闭环事实数",
        "仍需专业组边界事实数": "专业组边界待闭环事实数",
    }.items():
        if as_int(action_packet.get(old_field)) != as_int(gate_row.get(new_field)):
            raise SystemExit(f"packet missing count mismatch {old_field}->{new_field}: {action_packet.get('事实动作包ID')}")


def build_rows():
    packet_rows = read_csv(ACTION_PACKETS)
    resolution_rows = read_csv(FACT_RESOLUTION)
    channel_rows = read_csv(FACT_CHANNEL)

    resolution_by_id = index_unique(resolution_rows, "事实准出门禁ID")
    channel_by_packet = defaultdict(list)
    for row in channel_rows:
        key = (clean(row.get("页码版面键")), clean(row.get("事实核验动作组")))
        if not key[0] or not key[1]:
            raise SystemExit("missing page key or action group in fact channel")
        channel_by_packet[key].append(row)

    rows = []
    for packet in packet_rows:
        page_key = clean(packet.get("页码版面键"))
        action_group = clean(packet.get("事实核验动作组"))
        packet_facts = channel_by_packet.get((page_key, action_group), [])
        if not packet_facts:
            raise SystemExit(f"missing facts for packet: {packet.get('事实动作包ID')}")

        resolution_facts = []
        for fact in packet_facts:
            resolution_id = clean(fact.get("事实准出门禁ID"))
            resolution = resolution_by_id.get(resolution_id)
            if not resolution:
                raise SystemExit(f"missing resolution fact: {resolution_id}")
            resolution_facts.append(resolution)

        gate_row = {
            "第一闭环事实动作包准出门禁ID": stable_id(
                "FCFACTPACKGATE",
                [SOURCE_PDF_SHA256, packet.get("事实动作包ID")],
            ),
            "来源第一闭环事实动作包": source_path(ACTION_PACKETS),
            "来源第一闭环事实准出门禁账本": source_path(FACT_RESOLUTION),
            "来源第一闭环事实证据通道工作台": source_path(FACT_CHANNEL),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "第一闭环事实动作包×动作包准出门禁",
            "任务粒度": "页列动作包×PDF原页×湖北官方侧×高校辅证×冲突/复核/三方闭环",
            **false_gate_values(),
            "准出门禁序号": 0,
            "事实动作包ID": clean(packet.get("事实动作包ID")),
            "事实动作包序号": clean(packet.get("事实动作包序号")),
            "页码版面键": page_key,
            "来源页码": clean(packet.get("来源页码")),
            "版面列": clean(packet.get("版面列")),
            "准出闭环波次": clean(packet.get("准出闭环波次")),
            "执行泳道": clean(packet.get("执行泳道")),
            "第一闭环页列优先级": clean(packet.get("第一闭环页列优先级")),
            "事实核验动作组": action_group,
            "动作组排序": clean(packet.get("动作组排序")),
            "包执行优先级": clean(packet.get("包执行优先级")),
            "动作包事实数": clean(packet.get("动作包事实数")),
            "动作包字段事实数": clean(packet.get("动作包字段事实数")),
            "动作包专业名归属事实数": clean(packet.get("动作包专业名归属事实数")),
            "动作包专业组边界事实数": clean(packet.get("动作包专业组边界事实数")),
            "专业计划数字段事实数": clean(packet.get("专业计划数字段事实数")),
            "学费字段事实数": clean(packet.get("学费字段事实数")),
            "再选科目字段事实数": clean(packet.get("再选科目字段事实数")),
            "待人工判定字段事实数": clean(packet.get("待人工判定字段事实数")),
            "涉及任务数": clean(packet.get("涉及任务数")),
            "涉及字段状态数": clean(packet.get("涉及字段状态数")),
            "涉及专业行数": clean(packet.get("涉及专业行数")),
            "涉及专业组出现数": clean(packet.get("涉及专业组出现数")),
            "涉及院校代码数": clean(packet.get("涉及院校代码数")),
            "PDF原页待补事实数": true_count(resolution_facts, "是否仍需PDF原页"),
            "湖北官方侧待补事实数": true_count(resolution_facts, "是否仍需湖北官方侧"),
            "高校辅证待补事实数": true_count(resolution_facts, "是否仍需高校辅证"),
            "冲突待处理事实数": true_count(resolution_facts, "是否仍需冲突处理"),
            "双人复核待完成事实数": true_count(resolution_facts, "是否仍需双人复核"),
            "三方闭环待完成事实数": true_count(resolution_facts, "是否仍需三方闭环"),
            "专业名归属待闭环事实数": true_count(resolution_facts, "是否仍需专业名归属"),
            "专业组边界待闭环事实数": true_count(resolution_facts, "是否仍需专业组边界"),
            "可进入私有写回评审事实数": true_count(resolution_facts, "是否可进入私有写回评审"),
            "动作包准出状态": "",
            "动作包主缺口桶": "",
            "动作包准出阻断等级": blocker_level(action_group),
            "事实准出状态分布": counter_text(row.get("事实准出状态") for row in resolution_facts),
            "事实准出阻断等级分布": counter_text(row.get("事实准出阻断等级") for row in resolution_facts),
            "PDF原页通道状态分布": clean(packet.get("PDF原页通道状态分布")),
            "OCR提示通道状态分布": clean(packet.get("OCR提示通道状态分布")),
            "机器坐标通道状态分布": clean(packet.get("机器坐标通道状态分布")),
            "高校官网辅证通道状态分布": clean(packet.get("高校官网辅证通道状态分布")),
            "湖北官方侧通道状态分布": clean(packet.get("湖北官方侧通道状态分布")),
            "冲突处理通道状态分布": clean(packet.get("冲突处理通道状态分布")),
            "双人复核通道状态分布": clean(packet.get("双人复核通道状态分布")),
            "三方闭环通道状态分布": clean(packet.get("三方闭环通道状态分布")),
            "专业名归属通道状态分布": clean(packet.get("专业名归属通道状态分布")),
            "专业组边界通道状态分布": clean(packet.get("专业组边界通道状态分布")),
            "事实集合SHA16": clean(packet.get("事实集合SHA16")),
            "任务集合SHA16": clean(packet.get("任务集合SHA16")),
            "字段状态集合SHA16": clean(packet.get("字段状态集合SHA16")),
            "院校代码集合SHA16": clean(packet.get("院校代码集合SHA16")),
            "准出完成条件": counter_text(row.get("事实准出完成条件") for row in resolution_facts),
            "下一步动作包准出动作": "",
            "公开安全策略": "not_final；action_packet_gate_only；no_field_values；no_school_names；no_major_names；no_private_paths；no_ocr_text；no_recommendation；hubei_official_required",
        }
        gate_row["动作包准出状态"] = packet_status(gate_row)
        gate_row["动作包主缺口桶"] = blocker_bucket(gate_row)
        gate_row["下一步动作包准出动作"] = next_step(gate_row)
        for field in FALSE_FIELDS:
            if gate_row[field] != "false":
                raise SystemExit(f"non false gate {field}: {gate_row[field]}")
        require_same(packet, gate_row, packet_facts)
        rows.append(gate_row)

    rows.sort(
        key=lambda row: (
            as_int(row["事实动作包序号"]),
            as_int(row["动作组排序"]),
            row["页码版面键"],
        )
    )
    for index, row in enumerate(rows, 1):
        row["准出门禁序号"] = index

    return rows, packet_rows, resolution_rows, channel_rows


def build_summary(rows, packet_rows, resolution_rows, channel_rows):
    return {
        "status": "issue19_first_closure_fact_action_packet_resolution_gate_v1_not_final",
        "generated_by": "build_issue19_first_closure_fact_action_packet_resolution_gate_v1.py",
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_action_packets": source_path(ACTION_PACKETS),
        "source_action_packets_sha256": file_sha256(ACTION_PACKETS),
        "source_fact_resolution": source_path(FACT_RESOLUTION),
        "source_fact_resolution_sha256": file_sha256(FACT_RESOLUTION),
        "source_fact_channel": source_path(FACT_CHANNEL),
        "source_fact_channel_sha256": file_sha256(FACT_CHANNEL),
        "output_table": source_path(OUTPUT),
        "row_count": len(rows),
        "source_action_packet_row_count": len(packet_rows),
        "source_fact_resolution_row_count": len(resolution_rows),
        "source_fact_channel_row_count": len(channel_rows),
        "unique_page_side_count": len({row.get("页码版面键", "") for row in rows}),
        "unique_action_group_count": len({row.get("事实核验动作组", "") for row in rows}),
        "fact_count": sum(as_int(row.get("动作包事实数")) for row in rows),
        "field_fact_count": sum(as_int(row.get("动作包字段事实数")) for row in rows),
        "major_assignment_fact_count": sum(as_int(row.get("动作包专业名归属事实数")) for row in rows),
        "group_boundary_fact_count": sum(as_int(row.get("动作包专业组边界事实数")) for row in rows),
        "task_ref_count": sum(as_int(row.get("涉及任务数")) for row in rows),
        "field_status_ref_count": sum(as_int(row.get("涉及字段状态数")) for row in rows),
        "action_packet_counts": dict(Counter(row.get("事实核验动作组", "") for row in rows)),
        "action_fact_counts": dict(
            sorted(
                {
                    action: sum(as_int(row.get("动作包事实数")) for row in rows if row.get("事实核验动作组") == action)
                    for action in {row.get("事实核验动作组", "") for row in rows}
                }.items()
            )
        ),
        "field_category_counts": {
            "专业计划数": sum(as_int(row.get("专业计划数字段事实数")) for row in rows),
            "学费": sum(as_int(row.get("学费字段事实数")) for row in rows),
            "再选科目": sum(as_int(row.get("再选科目字段事实数")) for row in rows),
            "待人工判定字段": sum(as_int(row.get("待人工判定字段事实数")) for row in rows),
        },
        "missing_pdf_count": sum(as_int(row.get("PDF原页待补事实数")) for row in rows),
        "missing_hubei_official_count": sum(as_int(row.get("湖北官方侧待补事实数")) for row in rows),
        "missing_school_source_count": sum(as_int(row.get("高校辅证待补事实数")) for row in rows),
        "missing_conflict_count": sum(as_int(row.get("冲突待处理事实数")) for row in rows),
        "missing_double_review_count": sum(as_int(row.get("双人复核待完成事实数")) for row in rows),
        "missing_three_way_count": sum(as_int(row.get("三方闭环待完成事实数")) for row in rows),
        "missing_major_assignment_count": sum(as_int(row.get("专业名归属待闭环事实数")) for row in rows),
        "missing_group_boundary_count": sum(as_int(row.get("专业组边界待闭环事实数")) for row in rows),
        "private_writeback_review_ready_count": sum(as_int(row.get("可进入私有写回评审事实数")) for row in rows),
        "gate_status_counts": dict(Counter(row.get("动作包准出状态", "") for row in rows)),
        "blocker_bucket_counts": dict(Counter(row.get("动作包主缺口桶", "") for row in rows)),
        "blocker_level_counts": dict(Counter(row.get("动作包准出阻断等级", "") for row in rows)),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "auto_closure_allowed_count": 0,
        "note": "该表是第一闭环动作包准出门禁，只说明每个动作包的证据缺口和阻断桶；不保存字段值、学校名、专业名或 OCR 原文，不允许生成推荐。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"fact action packet gate contains forbidden public tokens: {hits[:10]}")


def main():
    rows, packet_rows, resolution_rows, channel_rows = build_rows()
    summary = build_summary(rows, packet_rows, resolution_rows, channel_rows)
    assert_public_safe(rows, summary)
    write_csv(OUTPUT, rows, GATE_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")


if __name__ == "__main__":
    main()
