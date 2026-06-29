#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

AUTO_BATCHES = WORKING / "issue19-school-source-auto-execution-batches-public-ledger.csv"
LATEST_RECONCILIATION = WORKING / "issue19-school-source-latest-reconciliation-public-ledger.csv"
C4C6_PACKETS = WORKING / "issue19-c4-c6-school-source-refresh-execution-packets.csv"

OUTPUT = WORKING / "issue19-school-source-progress-board-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-progress-board-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_progress_board"
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
]

FIELDS = [
    "高校源进度看板ID",
    "来源高校官网辅证自动执行批次",
    "来源高校源最新对齐账本",
    "来源C4C6高校源刷新执行包",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "看板序号",
    "高校官网辅证自动执行批次ID",
    "高校源最新对齐ID",
    "高校官网辅证状态快照ID",
    "院校代码",
    "院校名称公开",
    "自动执行泳道",
    "原官网来源状态",
    "原结构化输出状态桶",
    "原候选diff状态桶",
    "原补源状态桶",
    "最新高校侧证据层级",
    "相对原自动账本推进状态",
    "最新证据来源族",
    "最新公开证据集合SHA16",
    "来源类型桶",
    "建议来源形态",
    "来源留存状态",
    "涉及招生明细数",
    "涉及专业组数",
    "原涉及PDF页数",
    "next20结构化湖北物理行数合计",
    "next20结构化计划数合计",
    "live补源记录数",
    "live结构化输出记录数",
    "C4C6复用包数",
    "C4C6结构化diff包数",
    "C4C6补源尝试记录数",
    "C4C6综合结构化官网证据行数",
    "C4C6可生成候选diff明细数",
    "C4C6计划数一致候选数",
    "C4C6官网可补OCR计划数候选数",
    "C4C6计划数冲突候选数",
    "需补结构化明细数",
    "需继续补源明细数",
    "计划数冲突行数",
    "官网补缺候选行数",
    "官网未匹配行数",
    "下一批推进优先级",
    "下一批推进动作",
    "所需源类型",
    "人工最小核验动作",
    "仍需补源或解析原因",
    "完成条件",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
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
    "OCR行文本",
    "字段确认值",
    "人工读数",
    "候选值",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def source_kind(auto_row, latest_row):
    kinds = set()
    for value in [
        auto_row.get("来源文件类型集合", ""),
        latest_row.get("next20官网源类型集合", ""),
        latest_row.get("最新证据来源族", ""),
    ]:
        text = value.lower()
        if "json" in text or "api" in text:
            kinds.add("API/JSON")
        if "xlsx" in text or "excel" in text:
            kinds.add("XLSX")
        if "pdf" in text:
            kinds.add("PDF")
        if "html" in text or "入口" in value or "探针" in value:
            kinds.add("HTML/招生系统入口")
        if "章程" in value or "规则" in value:
            kinds.add("章程/规则")
    if not kinds:
        if latest_row.get("最新高校侧证据层级", "").startswith("L0"):
            return "待搜索高校官网计划源"
        return "公开来源待判定"
    return "；".join(sorted(kinds))


def source_family(latest_row):
    level = latest_row.get("最新高校侧证据层级", "")
    if level.startswith("L3"):
        return "F0-已有结构化或候选diff线索"
    if level.startswith("L1"):
        return "F1-有入口或探针但缺湖北物理结构化明细"
    return "F2-暂无可复用高校侧计划源"


def retention_state(auto_row, latest_row):
    if as_int(auto_row.get("公开来源文件数量")) or as_int(auto_row.get("公开来源URL数量")):
        return "R0-已有公开来源文件或URL留存"
    if as_int(latest_row.get("next20任务数")) or as_int(latest_row.get("live补源记录数")):
        return "R1-已有探针或live补源记录"
    if latest_row.get("最新高校侧证据层级", "").startswith("L0"):
        return "R3-暂无公开留存源"
    return "R2-已有账本线索但需补结构化留存"


def next_priority(auto_row, latest_row):
    action = auto_row.get("官网辅证自动动作", "")
    level = latest_row.get("最新高校侧证据层级", "")
    if action.startswith("C0-") or as_int(latest_row.get("C4C6计划数冲突候选数")):
        return "P0-冲突优先回PDF原页和湖北官方侧"
    if action.startswith("C1-") or as_int(latest_row.get("C4C6官网可补OCR计划数候选数")):
        return "P1-官网补缺线索回页"
    if action.startswith("C7-"):
        return "P2-专业名匹配和组边界确认"
    if level.startswith("L1") or action.startswith("C4-"):
        return "P3-补结构化湖北物理明细"
    if level.startswith("L0") or action.startswith("C6-"):
        return "P4-继续搜索高校官网计划网源"
    if action.startswith("C5-"):
        return "P5-仅章程规则限制核验"
    return "P6-保留线索等待PDF和湖北官方闭环"


def next_action(auto_row, latest_row):
    priority = next_priority(auto_row, latest_row)
    if priority.startswith("P0"):
        return "整理计划数冲突线索，回第19期PDF原页和湖北官方侧逐项核验。"
    if priority.startswith("P1"):
        return "把高校补缺线索作为定位提示，回PDF原页补候选，再核湖北官方侧。"
    if priority.startswith("P2"):
        return "补专业名匹配规则，核同页上下文、专业组边界和备注归属。"
    if priority.startswith("P3"):
        return "复用已有入口或来源，抽取湖北物理普通本科逐专业结构化明细。"
    if priority.startswith("P4"):
        return "继续搜索招生网、招生计划查询系统、附件、PDF、XLSX或API。"
    if priority.startswith("P5"):
        return "只核章程中的体检、语种、单科、收费、校区、调剂和录取规则。"
    return latest_row.get("最新自动建议动作", "") or auto_row.get("建议下一步动作", "")


def build_rows():
    auto_rows = read_csv(AUTO_BATCHES)
    latest_rows = read_csv(LATEST_RECONCILIATION)
    packet_rows = read_csv(C4C6_PACKETS)

    latest_by_auto = {
        row.get("原自动执行批次ID", ""): row
        for row in latest_rows
        if row.get("原自动执行批次ID", "")
    }
    packets_by_school = {}
    for row in packet_rows:
        packets_by_school.setdefault(row.get("院校代码", ""), []).append(row)

    rows = []
    for auto in auto_rows:
        latest = latest_by_auto.get(auto.get("高校官网辅证自动执行批次ID", ""), {})
        packets = packets_by_school.get(auto.get("院校代码", ""), [])
        priority = next_priority(auto, latest)
        rows.append({
            "高校源进度看板ID": stable_id(
                "SOURCESPROGRESS",
                [auto.get("高校官网辅证自动执行批次ID", ""), latest.get("高校源最新对齐ID", ""), SOURCE_PDF_SHA256],
            ),
            "来源高校官网辅证自动执行批次": "data/working/issue19-school-source-auto-execution-batches-public-ledger.csv",
            "来源高校源最新对齐账本": "data/working/issue19-school-source-latest-reconciliation-public-ledger.csv",
            "来源C4C6高校源刷新执行包": "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校×高校侧辅证自动执行任务",
            "任务粒度": "80个高校侧辅证任务×最新证据层级×下一批动作",
            **{field: "false" for field in FALSE_FIELDS},
            "看板序号": "",
            "高校官网辅证自动执行批次ID": auto.get("高校官网辅证自动执行批次ID", ""),
            "高校源最新对齐ID": latest.get("高校源最新对齐ID", ""),
            "高校官网辅证状态快照ID": auto.get("高校官网辅证状态快照ID", ""),
            "院校代码": auto.get("院校代码", ""),
            "院校名称公开": auto.get("院校名称公开", ""),
            "自动执行泳道": auto.get("自动执行泳道", ""),
            "原官网来源状态": latest.get("原官网来源状态", auto.get("官网来源状态", "")),
            "原结构化输出状态桶": latest.get("原结构化输出状态桶", auto.get("结构化输出状态桶", "")),
            "原候选diff状态桶": latest.get("原候选diff状态桶", auto.get("候选diff状态桶", "")),
            "原补源状态桶": latest.get("原补源状态桶", auto.get("补源状态桶", "")),
            "最新高校侧证据层级": latest.get("最新高校侧证据层级", ""),
            "相对原自动账本推进状态": latest.get("相对原自动账本推进状态", ""),
            "最新证据来源族": latest.get("最新证据来源族", ""),
            "最新公开证据集合SHA16": latest.get("最新公开证据集合SHA16", ""),
            "来源类型桶": source_family(latest),
            "建议来源形态": source_kind(auto, latest),
            "来源留存状态": retention_state(auto, latest),
            "涉及招生明细数": auto.get("涉及招生明细数", latest.get("原涉及招生明细数", "")),
            "涉及专业组数": auto.get("涉及专业组数", latest.get("原涉及专业组数", "")),
            "原涉及PDF页数": auto.get("涉及PDF页数", ""),
            "next20结构化湖北物理行数合计": latest.get("next20结构化湖北物理行数合计", "0"),
            "next20结构化计划数合计": latest.get("next20结构化计划数合计", "0"),
            "live补源记录数": latest.get("live补源记录数", "0"),
            "live结构化输出记录数": latest.get("live结构化输出记录数", "0"),
            "C4C6复用包数": latest.get("C4C6复用包数", "0"),
            "C4C6结构化diff包数": latest.get("C4C6结构化diff包数", "0"),
            "C4C6补源尝试记录数": latest.get("C4C6补源尝试记录数", "0"),
            "C4C6综合结构化官网证据行数": latest.get("C4C6综合结构化官网证据行数", "0"),
            "C4C6可生成候选diff明细数": latest.get("C4C6可生成候选diff明细数", "0"),
            "C4C6计划数一致候选数": latest.get("C4C6计划数一致候选数", "0"),
            "C4C6官网可补OCR计划数候选数": latest.get("C4C6官网可补OCR计划数候选数", "0"),
            "C4C6计划数冲突候选数": latest.get("C4C6计划数冲突候选数", "0"),
            "需补结构化明细数": str(sum(as_int(packet.get("需补结构化明细数")) for packet in packets)),
            "需继续补源明细数": str(sum(as_int(packet.get("需继续补源明细数")) for packet in packets)),
            "计划数冲突行数": auto.get("计划数冲突行数", "0"),
            "官网补缺候选行数": auto.get("官网补缺候选行数", "0"),
            "官网未匹配行数": auto.get("官网未匹配行数", "0"),
            "下一批推进优先级": priority,
            "下一批推进动作": next_action(auto, latest),
            "所需源类型": source_kind(auto, latest),
            "人工最小核验动作": latest.get("人工最小核验动作", auto.get("人工最小核验动作", "")),
            "仍需补源或解析原因": latest.get("仍需补源或解析原因", ""),
            "完成条件": auto.get("完成条件", ""),
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "公开安全策略": "公开看板只保存任务状态、计数、来源类型、ID和SHA；高校官网仅作辅证，不替代湖北官方计划，不保存字段读数、OCR正文、私有路径或登录态。",
        })

    rows.sort(
        key=lambda row: (
            row.get("下一批推进优先级", ""),
            -as_int(row.get("涉及招生明细数")),
            row.get("院校代码", ""),
            row.get("高校官网辅证自动执行批次ID", ""),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["看板序号"] = str(index)
    return rows, auto_rows, latest_rows, packet_rows


def ensure_public_safe(paths):
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    return [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]


def main():
    rows, auto_rows, latest_rows, packet_rows = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    unsafe_tokens = ensure_public_safe([OUTPUT])
    if unsafe_tokens:
        raise SystemExit(f"公开产物包含禁止词：{unsafe_tokens[:5]}")

    summary = {
        "status": "issue19_school_source_progress_board_not_final",
        "generated_by": "build_issue19_school_source_progress_board.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_auto_batches": "data/working/issue19-school-source-auto-execution-batches-public-ledger.csv",
        "source_latest_reconciliation": "data/working/issue19-school-source-latest-reconciliation-public-ledger.csv",
        "source_c4c6_packets": "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv",
        "output_table": "data/working/issue19-school-source-progress-board-public-ledger.csv",
        "row_count": len(rows),
        "unique_school_count": len({row["院校代码"] for row in rows if row["院校代码"]}),
        "source_auto_row_count": len(auto_rows),
        "source_latest_row_count": len(latest_rows),
        "source_c4c6_packet_count": len(packet_rows),
        "latest_evidence_level_counts": dict(Counter(row["最新高校侧证据层级"] for row in rows)),
        "next_priority_counts": dict(Counter(row["下一批推进优先级"] for row in rows)),
        "source_family_counts": dict(Counter(row["来源类型桶"] for row in rows)),
        "source_shape_counts": dict(Counter(row["建议来源形态"] for row in rows)),
        "retention_state_counts": dict(Counter(row["来源留存状态"] for row in rows)),
        "total_involved_major_detail_count": sum(as_int(row["涉及招生明细数"]) for row in rows),
        "row_attached_need_structure_count": sum(as_int(row["需补结构化明细数"]) for row in rows),
        "row_attached_need_source_count": sum(as_int(row["需继续补源明细数"]) for row in rows),
        "c4c6_unique_need_structure_count": sum(as_int(row.get("需补结构化明细数")) for row in packet_rows),
        "c4c6_unique_need_source_count": sum(as_int(row.get("需继续补源明细数")) for row in packet_rows),
        "total_candidate_diff_count": sum(as_int(row["C4C6可生成候选diff明细数"]) for row in rows),
        "total_conflict_count": sum(as_int(row["C4C6计划数冲突候选数"]) for row in rows),
        "total_fill_candidate_count": sum(as_int(row["C4C6官网可补OCR计划数候选数"]) for row in rows),
        "pdf_pending_count": sum(row["PDF原页核页状态"] == "pending_pdf_page_review" for row in rows),
        "hubei_official_pending_count": sum(
            row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_plan_review"
            for row in rows
        ),
        "field_writeback_ready_count": sum(
            row["字段事实写回状态"] != "blocked_until_pdf_hubei_school_three_way_closure"
            for row in rows
        ),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "official_plan_replacement_allowed_count": sum(row["是否允许官网证据替代湖北官方计划"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "public_boundary": "该看板只安排高校官网辅证继续推进和double check；官网证据不能替代湖北官方招生计划，不能自动写回字段事实或生成志愿建议。",
    }
    write_json(SUMMARY_OUTPUT, summary)


if __name__ == "__main__":
    main()
