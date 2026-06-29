#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

ACTION_PACKET_GATE = WORKING / "issue19-first-closure-fact-action-packet-resolution-gate-v1-public-ledger.csv"
MIN_PACKETS = WORKING / "issue19-stable-foundation-first-closure-w0-b0-minimal-manual-packets-public-ledger.csv"
PREFILL_PACKETS = WORKING / "issue19-stable-foundation-first-closure-w0-b0-execution-prefill-packets-public-audit.csv"
B0_CONFLICT_STATUS = WORKING / "issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv"
SCHOOL_BRIDGE_PAGE = WORKING / "issue19-w0-b0-school-source-bridge-page-summary.csv"
FIELD_BACKLINK_PAGE = WORKING / "issue19-w0-b0-school-source-field-backlink-page-summary.csv"
RESOLUTION_OVERLAY = WORKING / "issue19-first-closure-resolution-execution-overlay-v1.csv"

OUTPUT = WORKING / "issue19-first-closure-g0-conflict-package-closure-workbench-v1-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-first-closure-g0-conflict-package-closure-workbench-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
GENERATED_AT = "2026-06-29"
DATA_STAGE = "issue19_first_closure_g0_conflict_package_closure_workbench_v1"

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

FIELDS = [
    "G0冲突动作包闭环工作台ID",
    "来源动作包准出门禁",
    "来源W0B0最小人工复核包",
    "来源W0B0执行预填审计",
    "来源B0冲突页列状态",
    "来源W0B0高校源桥接页列汇总",
    "来源W0B0高校源字段回接页列汇总",
    "来源第一闭环准出执行叠加表",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "G0闭环工作台序号",
    "第一闭环事实动作包准出门禁ID",
    "事实动作包ID",
    "W0B0最小人工复核包ID",
    "W0B0执行预填包公开审计ID",
    "B0冲突页列核验状态ID",
    "W0B0高校源桥接页列汇总ID",
    "高校源字段回接页列汇总ID",
    "第一闭环准出执行叠加ID",
    "页码版面键",
    "来源页码",
    "版面列",
    "准出闭环波次",
    "执行泳道",
    "第一闭环页列优先级",
    "事实核验动作组",
    "动作包准出状态",
    "动作包主缺口桶",
    "动作包准出阻断等级",
    "动作包事实数",
    "动作包字段事实数",
    "动作包专业名归属事实数",
    "动作包专业组边界事实数",
    "专业计划数字段事实数",
    "学费字段事实数",
    "再选科目字段事实数",
    "PDF原页待补事实数",
    "湖北官方侧待补事实数",
    "高校辅证待补事实数",
    "冲突待处理事实数",
    "双人复核待完成事实数",
    "三方闭环待完成事实数",
    "专业名归属待闭环事实数",
    "专业组边界待闭环事实数",
    "W0事实范围总数",
    "最小人工复核事实数",
    "同页伴生待核事实数",
    "专业组边界先核事实数",
    "明确冲突字段事实数",
    "专业名归属先核事实数",
    "专业计划数冲突字段事实数",
    "学费冲突字段事实数",
    "再选科目冲突字段事实数",
    "涉及第一闭环任务数",
    "涉及冲突任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "需双人复核事实数",
    "需人工看图事实数",
    "PDFOCR提示事实数",
    "机器坐标提示事实数",
    "高校辅证线索事实数",
    "PDFOCR与高校冲突事实数",
    "私有页图存在",
    "私有OCR文本存在",
    "私有页列CSV证据编号",
    "私有页列CSV_SHA256",
    "私有页图_SHA256",
    "私有OCR文本_SHA256",
    "可作double_check提示事实数",
    "仍需补源或解析事实数",
    "结构化接入候选事实数",
    "高校源进度任务数合计",
    "高校源字段回接事实数",
    "字段回接需双人复核字段数",
    "字段回接需人工看图字段数",
    "字段回接存在PDFOCR与高校冲突字段数",
    "字段回接结构化接入候选字段数",
    "B0冲突闭环状态",
    "B0冲突优先级判定",
    "任务级人工动作桶摘要",
    "候选关系桶摘要",
    "人工核页材料状态",
    "G0包闭环状态",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "事实集合SHA16",
    "任务集合SHA16",
    "字段状态集合SHA16",
    "院校代码集合SHA16",
    "最小人工复核事实集合SHA256",
    "同页W0事实集合SHA256",
    "G0包下一步闭环动作",
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


def material_status(prefill):
    if (
        clean(prefill.get("私有页列CSV_SHA256"))
        and clean(prefill.get("私有页图_SHA256"))
        and clean(prefill.get("私有OCR文本_SHA256"))
        and clean(prefill.get("私有页图存在")) == "true"
        and clean(prefill.get("私有OCR文本存在")) == "true"
    ):
        return "M0-私有核页材料已生成_公开层仅保留SHA"
    return "M1-私有核页材料待补"


def next_action(row):
    page_key = row["页码版面键"]
    core = as_int(row.get("最小人工复核事实数"))
    conflict_fields = as_int(row.get("明确冲突字段事实数"))
    companion = as_int(row.get("同页伴生待核事实数"))
    return (
        f"按页列 {page_key} 打开私有预填材料；先核 {core} 个核心事实，"
        f"其中 {conflict_fields} 个明确冲突字段需对照 PDF 原页、湖北官方侧和高校辅证；"
        f"核心事实闭环后再处理 {companion} 个同页伴生事实。"
    )


def build_rows():
    gate_rows = read_csv(ACTION_PACKET_GATE)
    min_packets = read_csv(MIN_PACKETS)
    prefill_packets = read_csv(PREFILL_PACKETS)
    b0_rows = read_csv(B0_CONFLICT_STATUS)
    bridge_pages = read_csv(SCHOOL_BRIDGE_PAGE)
    backlink_pages = read_csv(FIELD_BACKLINK_PAGE)
    overlay_rows = read_csv(RESOLUTION_OVERLAY)

    min_by_page = index_unique(min_packets, "页码版面键")
    prefill_by_page = index_unique(prefill_packets, "页码版面键")
    b0_by_page = index_unique(b0_rows, "页码版面键")
    bridge_by_page = index_unique(bridge_pages, "页码版面键")
    backlink_by_page = index_unique(backlink_pages, "页码版面键")
    overlay_by_page = index_unique(overlay_rows, "页码版面键")

    g0_rows = [
        row for row in gate_rows
        if clean(row.get("动作包主缺口桶")) == "G0-冲突待处理"
    ]
    if len(g0_rows) != 10:
        raise SystemExit(f"expected 10 G0 rows, got {len(g0_rows)}")

    page_sets = [
        {clean(row.get("页码版面键")) for row in g0_rows},
        set(min_by_page),
        set(prefill_by_page),
        set(b0_by_page),
        set(bridge_by_page),
        set(backlink_by_page),
    ]
    if not all(page_set == page_sets[0] for page_set in page_sets[1:]):
        raise SystemExit("G0 page key mismatch across source ledgers")

    rows = []
    for gate in g0_rows:
        page_key = clean(gate.get("页码版面键"))
        minimal = min_by_page[page_key]
        prefill = prefill_by_page[page_key]
        b0 = b0_by_page[page_key]
        bridge = bridge_by_page[page_key]
        backlink = backlink_by_page[page_key]
        overlay = overlay_by_page.get(page_key, {})

        if clean(gate.get("事实核验动作组")) != "A0-W0B0冲突事实先核":
            raise SystemExit(f"unexpected G0 action group for {page_key}")
        if as_int(gate.get("动作包事实数")) != as_int(minimal.get("W0事实范围总数")):
            raise SystemExit(f"W0 fact count mismatch for {page_key}")
        if as_int(minimal.get("最小人工复核事实数")) + as_int(minimal.get("同页伴生待核事实数")) != as_int(minimal.get("W0事实范围总数")):
            raise SystemExit(f"minimal plus companion mismatch for {page_key}")
        if as_int(prefill.get("执行预填明细数")) != as_int(minimal.get("最小人工复核事实数")):
            raise SystemExit(f"prefill count mismatch for {page_key}")
        if as_int(bridge.get("事实数")) != as_int(minimal.get("最小人工复核事实数")):
            raise SystemExit(f"bridge fact count mismatch for {page_key}")
        if as_int(backlink.get("字段事实数")) != as_int(bridge.get("可作double_check提示事实数")):
            raise SystemExit(f"backlink field count mismatch for {page_key}")

        row = {
            "G0冲突动作包闭环工作台ID": stable_id("FCG0PKGCLOSE", [SOURCE_PDF_SHA256, gate.get("事实动作包ID")]),
            "来源动作包准出门禁": source_path(ACTION_PACKET_GATE),
            "来源W0B0最小人工复核包": source_path(MIN_PACKETS),
            "来源W0B0执行预填审计": source_path(PREFILL_PACKETS),
            "来源B0冲突页列状态": source_path(B0_CONFLICT_STATUS),
            "来源W0B0高校源桥接页列汇总": source_path(SCHOOL_BRIDGE_PAGE),
            "来源W0B0高校源字段回接页列汇总": source_path(FIELD_BACKLINK_PAGE),
            "来源第一闭环准出执行叠加表": source_path(RESOLUTION_OVERLAY),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "G0冲突动作包×闭环执行工作台",
            "任务粒度": "页列动作包×W0B0最小核验×预填材料×高校源double_check",
            **false_gate_values(),
            "G0闭环工作台序号": 0,
            "第一闭环事实动作包准出门禁ID": clean(gate.get("第一闭环事实动作包准出门禁ID")),
            "事实动作包ID": clean(gate.get("事实动作包ID")),
            "W0B0最小人工复核包ID": clean(minimal.get("W0B0最小人工复核包ID")),
            "W0B0执行预填包公开审计ID": clean(prefill.get("W0B0执行预填包公开审计ID")),
            "B0冲突页列核验状态ID": clean(b0.get("B0冲突页列核验状态ID")),
            "W0B0高校源桥接页列汇总ID": clean(bridge.get("W0B0高校源桥接页列汇总ID")),
            "高校源字段回接页列汇总ID": clean(backlink.get("高校源字段回接页列汇总ID")),
            "第一闭环准出执行叠加ID": clean(overlay.get("第一闭环准出执行叠加ID")),
            "页码版面键": page_key,
            "来源页码": clean(gate.get("来源页码")),
            "版面列": clean(gate.get("版面列")),
            "准出闭环波次": clean(gate.get("准出闭环波次")),
            "执行泳道": clean(gate.get("执行泳道")),
            "第一闭环页列优先级": clean(gate.get("第一闭环页列优先级")),
            "事实核验动作组": clean(gate.get("事实核验动作组")),
            "动作包准出状态": clean(gate.get("动作包准出状态")),
            "动作包主缺口桶": clean(gate.get("动作包主缺口桶")),
            "动作包准出阻断等级": clean(gate.get("动作包准出阻断等级")),
            "动作包事实数": clean(gate.get("动作包事实数")),
            "动作包字段事实数": clean(gate.get("动作包字段事实数")),
            "动作包专业名归属事实数": clean(gate.get("动作包专业名归属事实数")),
            "动作包专业组边界事实数": clean(gate.get("动作包专业组边界事实数")),
            "专业计划数字段事实数": clean(gate.get("专业计划数字段事实数")),
            "学费字段事实数": clean(gate.get("学费字段事实数")),
            "再选科目字段事实数": clean(gate.get("再选科目字段事实数")),
            "PDF原页待补事实数": clean(gate.get("PDF原页待补事实数")),
            "湖北官方侧待补事实数": clean(gate.get("湖北官方侧待补事实数")),
            "高校辅证待补事实数": clean(gate.get("高校辅证待补事实数")),
            "冲突待处理事实数": clean(gate.get("冲突待处理事实数")),
            "双人复核待完成事实数": clean(gate.get("双人复核待完成事实数")),
            "三方闭环待完成事实数": clean(gate.get("三方闭环待完成事实数")),
            "专业名归属待闭环事实数": clean(gate.get("专业名归属待闭环事实数")),
            "专业组边界待闭环事实数": clean(gate.get("专业组边界待闭环事实数")),
            "W0事实范围总数": clean(minimal.get("W0事实范围总数")),
            "最小人工复核事实数": clean(minimal.get("最小人工复核事实数")),
            "同页伴生待核事实数": clean(minimal.get("同页伴生待核事实数")),
            "专业组边界先核事实数": clean(minimal.get("专业组边界先核事实数")),
            "明确冲突字段事实数": clean(minimal.get("明确冲突字段事实数")),
            "专业名归属先核事实数": clean(minimal.get("专业名归属事实数")),
            "专业计划数冲突字段事实数": clean(minimal.get("专业计划数冲突字段事实数")),
            "学费冲突字段事实数": clean(minimal.get("学费冲突字段事实数")),
            "再选科目冲突字段事实数": clean(minimal.get("再选科目冲突字段事实数")),
            "涉及第一闭环任务数": clean(minimal.get("涉及第一闭环任务数")),
            "涉及冲突任务数": clean(minimal.get("涉及冲突任务数")),
            "涉及专业行数": clean(minimal.get("涉及专业行数")),
            "涉及院校代码数": clean(minimal.get("涉及院校代码数")),
            "需双人复核事实数": clean(minimal.get("需双人复核事实数")),
            "需人工看图事实数": clean(minimal.get("需人工看图事实数")),
            "PDFOCR提示事实数": clean(prefill.get("PDFOCR提示事实数")),
            "机器坐标提示事实数": clean(prefill.get("机器坐标提示事实数")),
            "高校辅证线索事实数": clean(prefill.get("高校辅证线索事实数")),
            "PDFOCR与高校冲突事实数": clean(prefill.get("PDFOCR与高校冲突事实数")),
            "私有页图存在": clean(prefill.get("私有页图存在")),
            "私有OCR文本存在": clean(prefill.get("私有OCR文本存在")),
            "私有页列CSV证据编号": clean(prefill.get("私有页列CSV证据编号")),
            "私有页列CSV_SHA256": clean(prefill.get("私有页列CSV_SHA256")),
            "私有页图_SHA256": clean(prefill.get("私有页图_SHA256")),
            "私有OCR文本_SHA256": clean(prefill.get("私有OCR文本_SHA256")),
            "可作double_check提示事实数": clean(bridge.get("可作double_check提示事实数")),
            "仍需补源或解析事实数": clean(bridge.get("仍需补源或解析事实数")),
            "结构化接入候选事实数": clean(bridge.get("结构化接入候选事实数")),
            "高校源进度任务数合计": clean(bridge.get("高校源进度任务数合计")),
            "高校源字段回接事实数": clean(backlink.get("字段事实数")),
            "字段回接需双人复核字段数": clean(backlink.get("需要双人复核字段数")),
            "字段回接需人工看图字段数": clean(backlink.get("需要人工看图字段数")),
            "字段回接存在PDFOCR与高校冲突字段数": clean(backlink.get("存在PDFOCR与高校冲突字段数")),
            "字段回接结构化接入候选字段数": clean(backlink.get("结构化接入候选字段数")),
            "B0冲突闭环状态": clean(b0.get("B0冲突闭环状态")),
            "B0冲突优先级判定": clean(b0.get("B0冲突优先级判定")),
            "任务级人工动作桶摘要": clean(b0.get("任务级人工动作桶摘要")),
            "候选关系桶摘要": clean(b0.get("候选关系桶摘要")),
            "人工核页材料状态": material_status(prefill),
            "G0包闭环状态": "blocked_pending_pdf_hubei_conflict_double_review",
            "PDF原页核页状态": clean(gate.get("PDF原页通道状态分布")) or clean(minimal.get("PDF原页核页状态")),
            "湖北官方系统或省招办计划核验状态": clean(minimal.get("湖北官方系统或省招办计划核验状态")),
            "高校官网源状态": clean(minimal.get("高校官网源状态")),
            "字段事实写回状态": clean(minimal.get("字段事实写回状态")),
            "事实集合SHA16": clean(gate.get("事实集合SHA16")),
            "任务集合SHA16": clean(gate.get("任务集合SHA16")),
            "字段状态集合SHA16": clean(gate.get("字段状态集合SHA16")),
            "院校代码集合SHA16": clean(gate.get("院校代码集合SHA16")),
            "最小人工复核事实集合SHA256": clean(minimal.get("最小人工复核事实集合SHA256")),
            "同页W0事实集合SHA256": clean(minimal.get("同页W0事实集合SHA256")),
            "G0包下一步闭环动作": "",
            "公开安全策略": "not_final；g0_conflict_package_workbench_only；no_field_values；no_school_names；no_major_names；no_private_paths；no_ocr_text；no_recommendation；hubei_official_required",
        }
        row["G0包下一步闭环动作"] = next_action(row)
        rows.append(row)

    rows.sort(key=lambda row: as_int(row.get("涉及冲突任务数")) * -1 or as_int(row.get("G0闭环工作台序号")))
    # Keep the existing action-packet order stable when conflict task counts tie.
    order_by_packet = {clean(row.get("事实动作包ID")): index for index, row in enumerate(g0_rows, 1)}
    rows.sort(key=lambda row: order_by_packet.get(row.get("事实动作包ID", ""), 999))
    for index, row in enumerate(rows, 1):
        row["G0闭环工作台序号"] = index
    return rows, {
        "action_packet_gate_rows": gate_rows,
        "minimal_rows": min_packets,
        "prefill_rows": prefill_packets,
        "b0_rows": b0_rows,
        "bridge_rows": bridge_pages,
        "backlink_rows": backlink_pages,
        "overlay_rows": overlay_rows,
    }


def build_summary(rows, sources):
    return {
        "status": "issue19_first_closure_g0_conflict_package_closure_workbench_v1_not_final",
        "generated_by": "build_issue19_first_closure_g0_conflict_package_closure_workbench_v1.py",
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_action_packet_gate": source_path(ACTION_PACKET_GATE),
        "source_action_packet_gate_sha256": file_sha256(ACTION_PACKET_GATE),
        "source_w0_b0_minimal_packets": source_path(MIN_PACKETS),
        "source_w0_b0_minimal_packets_sha256": file_sha256(MIN_PACKETS),
        "source_w0_b0_execution_prefill": source_path(PREFILL_PACKETS),
        "source_w0_b0_execution_prefill_sha256": file_sha256(PREFILL_PACKETS),
        "source_b0_conflict_status": source_path(B0_CONFLICT_STATUS),
        "source_b0_conflict_status_sha256": file_sha256(B0_CONFLICT_STATUS),
        "source_w0_b0_school_bridge_page": source_path(SCHOOL_BRIDGE_PAGE),
        "source_w0_b0_school_bridge_page_sha256": file_sha256(SCHOOL_BRIDGE_PAGE),
        "source_w0_b0_field_backlink_page": source_path(FIELD_BACKLINK_PAGE),
        "source_w0_b0_field_backlink_page_sha256": file_sha256(FIELD_BACKLINK_PAGE),
        "source_resolution_overlay": source_path(RESOLUTION_OVERLAY),
        "source_resolution_overlay_sha256": file_sha256(RESOLUTION_OVERLAY),
        "output_table": source_path(OUTPUT),
        "row_count": len(rows),
        "source_action_packet_gate_row_count": len(sources["action_packet_gate_rows"]),
        "source_w0_b0_minimal_packet_row_count": len(sources["minimal_rows"]),
        "source_w0_b0_execution_prefill_packet_row_count": len(sources["prefill_rows"]),
        "source_b0_conflict_status_row_count": len(sources["b0_rows"]),
        "source_w0_b0_school_bridge_page_row_count": len(sources["bridge_rows"]),
        "source_w0_b0_field_backlink_page_row_count": len(sources["backlink_rows"]),
        "unique_page_side_count": len({row.get("页码版面键", "") for row in rows}),
        "action_package_fact_count": sum(as_int(row.get("动作包事实数")) for row in rows),
        "action_package_field_fact_count": sum(as_int(row.get("动作包字段事实数")) for row in rows),
        "action_package_major_assignment_fact_count": sum(as_int(row.get("动作包专业名归属事实数")) for row in rows),
        "action_package_group_boundary_fact_count": sum(as_int(row.get("动作包专业组边界事实数")) for row in rows),
        "missing_pdf_count": sum(as_int(row.get("PDF原页待补事实数")) for row in rows),
        "missing_hubei_official_count": sum(as_int(row.get("湖北官方侧待补事实数")) for row in rows),
        "missing_school_source_count": sum(as_int(row.get("高校辅证待补事实数")) for row in rows),
        "missing_conflict_count": sum(as_int(row.get("冲突待处理事实数")) for row in rows),
        "minimal_review_fact_count": sum(as_int(row.get("最小人工复核事实数")) for row in rows),
        "companion_pending_fact_count": sum(as_int(row.get("同页伴生待核事实数")) for row in rows),
        "core_conflict_field_fact_count": sum(as_int(row.get("明确冲突字段事实数")) for row in rows),
        "core_group_boundary_fact_count": sum(as_int(row.get("专业组边界先核事实数")) for row in rows),
        "core_major_assignment_fact_count": sum(as_int(row.get("专业名归属先核事实数")) for row in rows),
        "core_plan_conflict_field_count": sum(as_int(row.get("专业计划数冲突字段事实数")) for row in rows),
        "core_tuition_conflict_field_count": sum(as_int(row.get("学费冲突字段事实数")) for row in rows),
        "core_elective_conflict_field_count": sum(as_int(row.get("再选科目冲突字段事实数")) for row in rows),
        "involved_task_count": sum(as_int(row.get("涉及第一闭环任务数")) for row in rows),
        "involved_conflict_task_count": sum(as_int(row.get("涉及冲突任务数")) for row in rows),
        "pdf_ocr_hint_fact_count": sum(as_int(row.get("PDFOCR提示事实数")) for row in rows),
        "machine_hint_fact_count": sum(as_int(row.get("机器坐标提示事实数")) for row in rows),
        "school_source_hint_fact_count": sum(as_int(row.get("高校辅证线索事实数")) for row in rows),
        "pdf_ocr_school_conflict_fact_count": sum(as_int(row.get("PDFOCR与高校冲突事实数")) for row in rows),
        "double_review_required_fact_count": sum(as_int(row.get("需双人复核事实数")) for row in rows),
        "manual_image_required_fact_count": sum(as_int(row.get("需人工看图事实数")) for row in rows),
        "school_source_double_check_fact_count": sum(as_int(row.get("可作double_check提示事实数")) for row in rows),
        "school_source_need_source_or_parse_fact_count": sum(as_int(row.get("仍需补源或解析事实数")) for row in rows),
        "structured_candidate_fact_count": sum(as_int(row.get("结构化接入候选事实数")) for row in rows),
        "field_backlink_fact_count": sum(as_int(row.get("高校源字段回接事实数")) for row in rows),
        "field_backlink_pdf_ocr_school_conflict_count": sum(as_int(row.get("字段回接存在PDFOCR与高校冲突字段数")) for row in rows),
        "private_material_ready_count": sum(
            1 for row in rows
            if row.get("人工核页材料状态") == "M0-私有核页材料已生成_公开层仅保留SHA"
        ),
        "g0_closure_status_counts": dict(Counter(row.get("G0包闭环状态", "") for row in rows)),
        "material_status_counts": dict(Counter(row.get("人工核页材料状态", "") for row in rows)),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "next_stage_allowed_count": 0,
        "final_available_count": 0,
        "auto_closure_allowed_count": 0,
        "note": "该表只把 G0 冲突动作包接到核页材料和高校源 double check 线索，仍不确认字段事实，不允许写回或推荐。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"G0 conflict package workbench contains forbidden public tokens: {hits[:10]}")


def main():
    rows, sources = build_rows()
    summary = build_summary(rows, sources)
    assert_public_safe(rows, summary)
    write_csv(OUTPUT, rows, FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")


if __name__ == "__main__":
    main()
