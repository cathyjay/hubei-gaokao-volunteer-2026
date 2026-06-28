#!/usr/bin/env python3
"""Build public verification packets for first-closure fact gaps.

This script groups the 439 first-closure fact-scope gaps into 37 page-side
verification packets and keeps a packet-item table for every fact. It is an
execution aid only: no field values, school names, major names, OCR text, image
paths, or private review notes are published.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

FACT_SCOPE = WORKING / "issue19-stable-foundation-first-closure-fact-scope-gap-public-ledger.csv"
NEXT_ACTION = WORKING / "issue19-stable-foundation-first-closure-next-action-matrix.csv"
NEXT_ACTION_PAGE = WORKING / "issue19-stable-foundation-first-closure-next-action-page-summary.csv"
EVIDENCE_MAP = WORKING / "issue19-stable-foundation-first-closure-public-evidence-map.csv"
EVIDENCE_PAGE = WORKING / "issue19-stable-foundation-first-closure-evidence-status-page-side-summary.csv"

PACKET_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-fact-verification-packets-public-ledger.csv"
ITEM_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-fact-verification-items-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-stable-foundation-first-closure-fact-verification-packets-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_stable_foundation_first_closure_fact_verification_packets"
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

PACKET_FIELDS = [
    "第一闭环事实核验包ID",
    "来源第一闭环事实范围缺口账本",
    "来源第一闭环下一步动作矩阵",
    "来源第一闭环页列下一步动作汇总",
    "来源第一闭环公开证据地图",
    "来源第一闭环页列证据汇总",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "核验包序号",
    "核验波次",
    "核验泳道",
    "稳定基座第一闭环页列包ID",
    "第一闭环页列下一步动作ID",
    "第一闭环公开证据地图ID",
    "第一闭环页列证据状态汇总ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "页列主阻断",
    "执行泳道",
    "页列优先级",
    "事实范围总数",
    "字段事实数",
    "专业名归属事实数",
    "专业组边界事实数",
    "专业计划数字段事实数",
    "学费字段事实数",
    "再选科目字段事实数",
    "待人工判定字段事实数",
    "第一闭环任务数",
    "涉及专业行数",
    "涉及院校代码数",
    "N0冲突双人核页任务数",
    "N1高校补缺回页任务数",
    "N2机器坐标辅助核页任务数",
    "N3无候选人工看图任务数",
    "N4PDFOCR候选确认任务数",
    "N5多源一致待官核任务数",
    "PDFOCR提示任务数",
    "PDFOCR无候选任务数",
    "机器坐标提示任务数",
    "高校辅证线索任务数",
    "PDFOCR与高校辅证冲突任务数",
    "需要人工直接看图任务数",
    "需要双人复核任务数",
    "事实需人工看图数",
    "事实需双人复核数",
    "事实缺口桶分布",
    "事实类型分布",
    "核验动作层级分布",
    "高校源可用性分布",
    "页列建议下一步动作",
    "人工最小核验动作",
    "包完成条件",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "事实范围集合SHA256",
    "任务ID集合SHA256",
    "专业行ID集合SHA256",
    "院校代码集合SHA256",
    "公开安全策略",
]

ITEM_FIELDS = [
    "第一闭环事实核验包明细ID",
    "第一闭环事实核验包ID",
    "来源第一闭环事实范围缺口账本",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "包内事实序号",
    "核验包序号",
    "核验波次",
    "核验泳道",
    "第一闭环事实范围缺口公开账本ID",
    "事实域",
    "事实类型",
    "事实粒度",
    "事实闭环状态",
    "稳定基座第一闭环明细任务ID",
    "第一闭环字段事实公开账本ID",
    "第一闭环下一步动作ID",
    "第一闭环证据状态公开账本ID",
    "稳定基座第一闭环页列包ID",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "任务来源类型",
    "字段名",
    "执行泳道",
    "核验动作层级",
    "页列主阻断",
    "事实缺口桶",
    "是否需要人工看图",
    "是否需要双人复核",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "事实对象集合SHA256",
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
    "院校专业组",
    "OCR行文本",
    "OCR原文",
    "候选值",
    "人工读数",
    "字段确认值",
    "PDF原页人工读数",
    "湖北官方字段值",
    "高校官网或招生章程字段值",
    "复核备注",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def stable_id(prefix: str, parts: list[str]) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def sha256_values(values: list[str]) -> str:
    clean = sorted({str(value or "").strip() for value in values if str(value or "").strip()})
    return hashlib.sha256("|".join(clean).encode("utf-8")).hexdigest() if clean else ""


def to_int(value: str | int | None) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def compact_counter(values: list[str]) -> str:
    counter = Counter(value for value in values if value)
    return "；".join(f"{key}×{count}" for key, count in sorted(counter.items())) if counter else ""


def wave_for_page(page_row: dict[str, str], fact_rows: list[dict[str, str]]) -> tuple[int, str, str]:
    block = page_row.get("页列主阻断", "")
    major_name_count = sum(row.get("事实域") == "专业名归属" for row in fact_rows)
    if block.startswith("B0"):
        return (0, "W0-B0冲突优先", "先双人核PDF原页冲突，再核湖北官方侧和高校辅证差异。")
    if major_name_count:
        return (1, "W1-专业名归属优先", "先核专业行归属和专业组边界，再进入字段事实判断。")
    if block.startswith("B1"):
        return (2, "W2-缺候选人工看图", "先人工看PDF原页补定位，再决定字段事实是否可进入三方闭环。")
    if block.startswith("B2"):
        return (3, "W3-机器坐标辅助核页", "按机器坐标定位字段，但以PDF原页和湖北官方侧为准。")
    if block.startswith("B3"):
        return (4, "W4-PDFOCR候选确认", "回看PDF原页确认PDFOCR候选，并等待湖北官方侧闭环。")
    return (9, "W9-留存待排", "留存待后续批次统一处理。")


def packet_sort_key(packet: dict[str, str]) -> tuple[int, int, int, str]:
    wave_rank = int(packet.pop("_wave_rank"))
    double_count = to_int(packet.get("事实需双人复核数"))
    fact_count = to_int(packet.get("事实范围总数"))
    return (wave_rank, -double_count, -fact_count, packet.get("页码版面键", ""))


def add_false_fields(row: dict[str, str]) -> None:
    for field in FALSE_FIELDS:
        row[field] = "false"


def build_packet(
    page_key: str,
    fact_rows: list[dict[str, str]],
    page_row: dict[str, str],
    map_row: dict[str, str],
    evidence_page_row: dict[str, str],
) -> dict[str, str]:
    wave_rank, wave_name, lane = wave_for_page(page_row, fact_rows)
    fact_type_counter = Counter(row.get("事实类型", "") for row in fact_rows)
    fact_gap_counter = Counter(row.get("事实缺口桶", "") for row in fact_rows)
    packet_id = stable_id(
        "FIRSTFACTPKT",
        [
            page_key,
            page_row.get("稳定基座第一闭环页列包ID", ""),
            sha256_values([row.get("第一闭环事实范围缺口公开账本ID", "") for row in fact_rows]),
        ],
    )
    row = {
        "第一闭环事实核验包ID": packet_id,
        "来源第一闭环事实范围缺口账本": source_path(FACT_SCOPE),
        "来源第一闭环下一步动作矩阵": source_path(NEXT_ACTION),
        "来源第一闭环页列下一步动作汇总": source_path(NEXT_ACTION_PAGE),
        "来源第一闭环公开证据地图": source_path(EVIDENCE_MAP),
        "来源第一闭环页列证据汇总": source_path(EVIDENCE_PAGE),
        "来源期号": SOURCE_ISSUE,
        "来源PDF_SHA256": SOURCE_PDF_SHA256,
        "生成日期": GENERATED_AT,
        "数据阶段": DATA_STAGE,
        "主表粒度": "第一闭环页列事实核验包",
        "任务粒度": "PDF页码×版面列×事实范围核验包",
        "核验波次": wave_name,
        "核验泳道": lane,
        "_wave_rank": str(wave_rank),
        "稳定基座第一闭环页列包ID": page_row.get("稳定基座第一闭环页列包ID", ""),
        "第一闭环页列下一步动作ID": page_row.get("第一闭环页列下一步动作ID", ""),
        "第一闭环公开证据地图ID": map_row.get("第一闭环公开证据地图ID", ""),
        "第一闭环页列证据状态汇总ID": evidence_page_row.get("第一闭环页列证据状态汇总ID", ""),
        "来源页码": page_row.get("来源页码", ""),
        "版面列": page_row.get("版面列", ""),
        "页码版面键": page_key,
        "页列主阻断": page_row.get("页列主阻断", ""),
        "执行泳道": page_row.get("执行泳道", ""),
        "页列优先级": page_row.get("第一闭环页列优先级", ""),
        "事实范围总数": str(len(fact_rows)),
        "字段事实数": str(sum(row.get("事实域") == "字段事实" for row in fact_rows)),
        "专业名归属事实数": str(sum(row.get("事实域") == "专业名归属" for row in fact_rows)),
        "专业组边界事实数": str(sum(row.get("事实域") == "专业组边界" for row in fact_rows)),
        "专业计划数字段事实数": str(fact_type_counter.get("字段事实-专业计划数", 0)),
        "学费字段事实数": str(fact_type_counter.get("字段事实-学费", 0)),
        "再选科目字段事实数": str(fact_type_counter.get("字段事实-再选科目", 0)),
        "待人工判定字段事实数": str(fact_type_counter.get("字段事实-待人工判定字段", 0)),
        "第一闭环任务数": page_row.get("页列任务数", ""),
        "涉及专业行数": page_row.get("涉及专业行数", ""),
        "涉及院校代码数": page_row.get("涉及院校代码数", ""),
        "N0冲突双人核页任务数": page_row.get("N0冲突双人核页任务数", ""),
        "N1高校补缺回页任务数": page_row.get("N1高校补缺回页任务数", ""),
        "N2机器坐标辅助核页任务数": page_row.get("N2机器坐标辅助核页任务数", ""),
        "N3无候选人工看图任务数": page_row.get("N3无候选人工看图任务数", ""),
        "N4PDFOCR候选确认任务数": page_row.get("N4PDFOCR候选确认任务数", ""),
        "N5多源一致待官核任务数": page_row.get("N5多源一致仍待官核任务数", page_row.get("N5多源一致待官核任务数", "")),
        "PDFOCR提示任务数": map_row.get("PDFOCR提示任务数", evidence_page_row.get("PDFOCR提示任务数", "")),
        "PDFOCR无候选任务数": map_row.get("PDFOCR无候选任务数", evidence_page_row.get("PDFOCR无候选任务数", "")),
        "机器坐标提示任务数": map_row.get("机器坐标提示任务数", evidence_page_row.get("机器坐标提示任务数", "")),
        "高校辅证线索任务数": map_row.get("高校辅证线索任务数", evidence_page_row.get("高校辅证线索任务数", "")),
        "PDFOCR与高校辅证冲突任务数": map_row.get("PDFOCR与高校辅证冲突任务数", evidence_page_row.get("PDFOCR与高校辅证冲突任务数", "")),
        "需要人工直接看图任务数": map_row.get("需要人工直接看图任务数", evidence_page_row.get("需要人工直接看图任务数", "")),
        "需要双人复核任务数": map_row.get("需要双人复核任务数", evidence_page_row.get("需要双人复核任务数", "")),
        "事实需人工看图数": str(sum(row.get("是否需要人工看图") == "true" for row in fact_rows)),
        "事实需双人复核数": str(sum(row.get("是否需要双人复核") == "true" for row in fact_rows)),
        "事实缺口桶分布": compact_counter([row.get("事实缺口桶", "") for row in fact_rows]),
        "事实类型分布": compact_counter([row.get("事实类型", "") for row in fact_rows]),
        "核验动作层级分布": page_row.get("核验动作层级分布", ""),
        "高校源可用性分布": page_row.get("高校源可用性分布", ""),
        "页列建议下一步动作": page_row.get("页列建议下一步动作", ""),
        "人工最小核验动作": lane,
        "包完成条件": "包内事实逐项完成PDF原页、湖北官方侧、必要高校辅证和双人复核记录后，仍需保持非自动写回，等待最终候选闭环。",
        "PDF原页核页状态": "pending_pdf_page_review",
        "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
        "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
        "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
        "事实范围集合SHA256": sha256_values([row.get("第一闭环事实范围缺口公开账本ID", "") for row in fact_rows]),
        "任务ID集合SHA256": evidence_page_row.get("第一闭环任务ID集合SHA256", ""),
        "专业行ID集合SHA256": evidence_page_row.get("专业行ID集合SHA256", ""),
        "院校代码集合SHA256": evidence_page_row.get("院校代码集合SHA256", ""),
        "公开安全策略": "公开层只保存页列、计数、状态桶、ID和SHA；不保存学校专业明细、字段明细值、识别正文或私有材料。",
    }
    add_false_fields(row)
    return row


def build_item(
    packet: dict[str, str],
    fact_row: dict[str, str],
    packet_seq: int,
    item_seq: int,
) -> dict[str, str]:
    row = {
        "第一闭环事实核验包明细ID": stable_id(
            "FIRSTFACTITEM",
            [
                packet.get("第一闭环事实核验包ID", ""),
                fact_row.get("第一闭环事实范围缺口公开账本ID", ""),
            ],
        ),
        "第一闭环事实核验包ID": packet.get("第一闭环事实核验包ID", ""),
        "来源第一闭环事实范围缺口账本": source_path(FACT_SCOPE),
        "来源期号": SOURCE_ISSUE,
        "来源PDF_SHA256": SOURCE_PDF_SHA256,
        "生成日期": GENERATED_AT,
        "数据阶段": DATA_STAGE + "_items",
        "主表粒度": "第一闭环页列事实核验包明细",
        "任务粒度": "核验包×事实范围",
        "包内事实序号": str(item_seq),
        "核验包序号": str(packet_seq),
        "核验波次": packet.get("核验波次", ""),
        "核验泳道": packet.get("核验泳道", ""),
        "第一闭环事实范围缺口公开账本ID": fact_row.get("第一闭环事实范围缺口公开账本ID", ""),
        "事实域": fact_row.get("事实域", ""),
        "事实类型": fact_row.get("事实类型", ""),
        "事实粒度": fact_row.get("事实粒度", ""),
        "事实闭环状态": fact_row.get("事实闭环状态", ""),
        "稳定基座第一闭环明细任务ID": fact_row.get("稳定基座第一闭环明细任务ID", ""),
        "第一闭环字段事实公开账本ID": fact_row.get("第一闭环字段事实公开账本ID", ""),
        "第一闭环下一步动作ID": fact_row.get("第一闭环下一步动作ID", ""),
        "第一闭环证据状态公开账本ID": fact_row.get("第一闭环证据状态公开账本ID", ""),
        "稳定基座第一闭环页列包ID": fact_row.get("稳定基座第一闭环页列包ID", ""),
        "来源页码": fact_row.get("来源页码", ""),
        "版面列": fact_row.get("版面列", ""),
        "页码版面键": fact_row.get("页码版面键", ""),
        "专业行ID": fact_row.get("专业行ID", ""),
        "专业组出现ID": fact_row.get("专业组出现ID", ""),
        "院校代码": fact_row.get("院校代码", ""),
        "任务来源类型": fact_row.get("任务来源类型", ""),
        "字段名": fact_row.get("字段名", ""),
        "执行泳道": fact_row.get("执行泳道", ""),
        "核验动作层级": fact_row.get("核验动作层级", ""),
        "页列主阻断": fact_row.get("页列主阻断", ""),
        "事实缺口桶": fact_row.get("事实缺口桶", ""),
        "是否需要人工看图": fact_row.get("是否需要人工看图", ""),
        "是否需要双人复核": fact_row.get("是否需要双人复核", ""),
        "PDF原页核页状态": "pending_pdf_page_review",
        "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
        "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
        "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
        "事实对象集合SHA256": fact_row.get("事实对象集合SHA256", ""),
        "公开安全策略": "公开层只保存事实范围ID、页列、状态桶和SHA；不保存字段明细值、识别正文或私有材料。",
    }
    add_false_fields(row)
    return row


def main() -> None:
    fact_rows = read_csv(FACT_SCOPE)
    next_page_rows = read_csv(NEXT_ACTION_PAGE)
    map_rows = read_csv(EVIDENCE_MAP)
    evidence_page_rows = read_csv(EVIDENCE_PAGE)

    facts_by_page = defaultdict(list)
    for row in fact_rows:
        facts_by_page[row.get("页码版面键", "")].append(row)

    next_page_by_key = {row.get("页码版面键", ""): row for row in next_page_rows}
    map_by_key = {row.get("页码版面键", ""): row for row in map_rows}
    evidence_page_by_key = {row.get("页码版面键", ""): row for row in evidence_page_rows}

    packet_rows = []
    for page_key, grouped_facts in facts_by_page.items():
        packet_rows.append(
            build_packet(
                page_key,
                grouped_facts,
                next_page_by_key.get(page_key, {}),
                map_by_key.get(page_key, {}),
                evidence_page_by_key.get(page_key, {}),
            )
        )

    packet_rows = sorted(packet_rows, key=packet_sort_key)
    item_rows = []
    packet_by_page = {}
    for packet_seq, packet in enumerate(packet_rows, start=1):
        packet["核验包序号"] = str(packet_seq)
        packet_by_page[packet.get("页码版面键", "")] = packet
        for field in PACKET_FIELDS:
            packet.setdefault(field, "")

    for packet in packet_rows:
        page_key = packet.get("页码版面键", "")
        sorted_facts = sorted(
            facts_by_page[page_key],
            key=lambda row: (
                row.get("事实域", ""),
                row.get("核验动作层级", ""),
                row.get("字段名", ""),
                row.get("第一闭环事实范围缺口公开账本ID", ""),
            ),
        )
        for item_seq, fact_row in enumerate(sorted_facts, start=1):
            item_rows.append(build_item(packet, fact_row, int(packet["核验包序号"]), item_seq))

    write_csv(PACKET_OUTPUT, packet_rows, PACKET_FIELDS)
    write_csv(ITEM_OUTPUT, item_rows, ITEM_FIELDS)

    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [PACKET_OUTPUT, ITEM_OUTPUT]
    )
    forbidden_hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if forbidden_hits:
        raise SystemExit(f"公开输出包含禁止内容：{forbidden_hits[:5]}")

    wave_counts = Counter(row.get("核验波次", "") for row in packet_rows)
    fact_domain_counts = Counter(row.get("事实域", "") for row in item_rows)
    fact_type_counts = Counter(row.get("事实类型", "") for row in item_rows)
    summary = {
        "status": "issue19_stable_foundation_first_closure_fact_verification_packets_ready_not_final",
        "generated_by": "build_issue19_first_closure_fact_verification_packets.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_first_closure_fact_scope_gap_ledger": source_path(FACT_SCOPE),
        "source_first_closure_next_action_matrix": source_path(NEXT_ACTION),
        "source_first_closure_next_action_page_summary": source_path(NEXT_ACTION_PAGE),
        "source_first_closure_public_evidence_map": source_path(EVIDENCE_MAP),
        "source_first_closure_evidence_page_summary": source_path(EVIDENCE_PAGE),
        "packet_output_table": source_path(PACKET_OUTPUT),
        "item_output_table": source_path(ITEM_OUTPUT),
        "packet_row_count": len(packet_rows),
        "item_row_count": len(item_rows),
        "unique_page_side_count": len({row.get("页码版面键", "") for row in packet_rows}),
        "unique_fact_scope_count": len({row.get("第一闭环事实范围缺口公开账本ID", "") for row in item_rows}),
        "wave_counts": dict(wave_counts),
        "fact_domain_counts": dict(fact_domain_counts),
        "fact_type_counts": dict(fact_type_counts),
        "total_fact_scope_count": sum(to_int(row.get("事实范围总数")) for row in packet_rows),
        "field_fact_count": sum(to_int(row.get("字段事实数")) for row in packet_rows),
        "major_name_assignment_fact_count": sum(to_int(row.get("专业名归属事实数")) for row in packet_rows),
        "group_boundary_fact_count": sum(to_int(row.get("专业组边界事实数")) for row in packet_rows),
        "double_review_required_fact_count": sum(to_int(row.get("事实需双人复核数")) for row in packet_rows),
        "manual_image_required_fact_count": sum(to_int(row.get("事实需人工看图数")) for row in packet_rows),
        "pdf_pending_packet_count": sum(row.get("PDF原页核页状态") == "pending_pdf_page_review" for row in packet_rows),
        "hubei_official_pending_packet_count": sum(
            row.get("湖北官方系统或省招办计划核验状态") == "pending_hubei_official_plan_review"
            for row in packet_rows
        ),
        "field_writeback_ready_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "该公开账本只把事实缺口排成页列核验包，不公开字段明细值，不确认字段事实，不生成志愿排序。",
    }
    write_json(SUMMARY_OUTPUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
