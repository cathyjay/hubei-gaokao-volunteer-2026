#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]

SCHOOL_REFRESH = ROOT / "data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv"
SOURCE_GAP = ROOT / "data/working/issue19-b0-b1-official-source-gap-priority.csv"
C4C6_PACKETS = ROOT / "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv"
C4C6_DIFF = ROOT / "data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv"
C4C6_ATTEMPTS = ROOT / "data/working/issue19-c4-c6-school-source-acquisition-attempts-public-ledger.csv"
SEEDS = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv"
OFFICIAL_LIVE = ROOT / "data/working/issue19-official-public-entry-live-recheck.json"

OUTPUT = ROOT / "data/working/issue19-school-source-opportunity-queue.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-school-source-opportunity-queue-summary.json"

DATA_STAGE = "issue19_school_source_opportunity_queue"

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
    "高校官网辅证机会ID",
    "来源高校侧辅证刷新公开账本",
    "来源B0B1官方源缺口优先表",
    "来源C4C6高校源刷新执行包",
    "来源C4C6结构化候选diff公开账本",
    "来源C4C6高校官网补源尝试账本",
    "来源高校官网补源种子表",
    "来源湖北官方公开入口活体复查",
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
    "执行建议序号",
    "机会优先级",
    "机会类型",
    "自动收益分",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "高校侧刷新批次",
    "高校侧刷新任务类型",
    "闭环优先级",
    "官网证据强度",
    "官网来源状态",
    "来源文件类型集合",
    "公开来源文件数量",
    "公开来源URL数量",
    "涉及招生明细数",
    "涉及专业组数",
    "涉及PDF页数",
    "计划数冲突行数",
    "官网补缺候选行数",
    "强辅证抽检行数",
    "部分来源待结构化行数",
    "继续补源行数",
    "仅章程规则行数",
    "官网未匹配行数",
    "字段辅证行数",
    "B0B1缺口优先级",
    "B0B1缺口类型",
    "B0B1逐专业核验任务数",
    "C4C6执行包数量",
    "C4C6执行泳道集合",
    "C4C6执行优先级集合",
    "C4C6需补结构化明细数",
    "C4C6需继续补源明细数",
    "C4C6结构化diff优先级集合",
    "C4C6综合结构化官网证据行数",
    "C4C6专业名匹配明细数",
    "C4C6未匹配明细数",
    "C4C6无结构化官网源明细数",
    "C4C6计划数一致候选数",
    "C4C6官网可补OCR计划数候选数",
    "C4C6计划数冲突候选数",
    "C4C6可生成候选diff明细数",
    "最新自动探针状态",
    "最新自动探针摘要",
    "候选官网URL数量",
    "候选官网URL集合SHA256",
    "种子官网URL数量",
    "种子官网URL集合SHA256",
    "本地公开来源文件集合SHA256",
    "来源质量判断",
    "自动化下一步",
    "人工最小核验动作",
    "保真边界",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源刷新状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

FORBIDDEN_PUBLIC_TOKENS = [
    "/Users/",
    "/private/",
    "private/",
    "private\\",
    "ocr-runs",
    "rendered-pages",
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
    "身份证",
    "准考证",
    "报名号",
    "序列号",
    "已确认",
    "已核准",
    "最终推荐",
]


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


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def sha_list(values):
    normalized = "；".join(sorted({value for value in values if value}))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""


def join_limited(values, limit=8):
    result = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    if len(seen) > limit:
        result = result[:limit] + [f"另{len(seen) - limit}项"]
    return "；".join(result)


def split_values(value):
    if not value:
        return []
    return [part.strip() for part in str(value).replace("；", ";").split(";") if part.strip()]


def score_for(row, gap, packets, diffs, attempts):
    detail_count = as_int(row.get("涉及招生明细数")) or 0
    score = detail_count
    score += 35 * (as_int(row.get("计划数冲突行数")) or 0)
    score += 28 * (as_int(row.get("官网补缺候选行数")) or 0)
    score += 18 * (as_int(row.get("官网未匹配行数")) or 0)
    score += 12 * (as_int(row.get("部分来源待结构化行数")) or 0)
    score += 14 * (as_int(row.get("继续补源行数")) or 0)
    score += 10 * (as_int(row.get("字段辅证行数")) or 0)
    score += 8 * (as_int(row.get("强辅证抽检行数")) or 0)
    score += sum(as_int(packet.get("涉及招生明细数")) or 0 for packet in packets)
    score += 12 * sum(as_int(diff.get("无结构化官网源明细数")) or 0 for diff in diffs)
    score += 10 * sum(as_int(diff.get("官网可补OCR计划数候选数")) or 0 for diff in diffs)
    score += 20 * sum(as_int(diff.get("计划数冲突候选数")) or 0 for diff in diffs)
    score += 8 * sum(as_int(diff.get("可生成候选diff明细数")) or 0 for diff in diffs)
    score += 25 * len(attempts)
    if gap and gap.get("补源优先级", "").startswith("P0"):
        score += 120
    return score


def opportunity_type(row, gap, diffs, attempts):
    action = row.get("官网辅证自动动作", "")
    diff_priorities = {diff.get("结构化候选diff优先级", "") for diff in diffs}
    if action.startswith("C0") or "D0-存在计划数冲突需优先核PDF原页" in diff_priorities:
        return "O0-冲突优先回页核验"
    if action.startswith("C1"):
        return "O1-官网补缺候选回页核验"
    if action.startswith("C7"):
        return "O2-官网专业名未匹配先补规则"
    if gap and gap.get("补源优先级", "").startswith("P0"):
        return "O3-高收益缺源学校优先补源"
    if any(diff.get("无结构化官网源明细数", "0") not in {"", "0"} for diff in diffs):
        return "O4-有入口但缺结构化源"
    if action.startswith(("C4", "C3")):
        return "O5-已有来源补结构化"
    if action.startswith("C6") or attempts:
        return "O6-继续搜索高校官网计划源"
    if action.startswith("C2"):
        return "O7-强辅证抽检"
    if action.startswith("C5"):
        return "O8-章程规则源只核限制"
    return "O9-普通留存"


def priority_from_type(kind, score):
    if kind.startswith(("O0", "O1", "O2", "O3")):
        return "P0-立即处理"
    if kind.startswith(("O4", "O5", "O6")) and score >= 80:
        return "P1-高收益自动补源"
    if kind.startswith(("O4", "O5", "O6", "O7")):
        return "P2-常规自动补源或抽检"
    return "P3-低收益留存"


def quality_label(row, gap, packets, diffs, attempts):
    if any(diff.get("计划数冲突候选数", "0") not in {"", "0"} for diff in diffs):
        return "Q0-有结构化源但存在计划数冲突"
    if any(diff.get("计划数一致候选数", "0") not in {"", "0"} for diff in diffs):
        return "Q1-有结构化源且存在计划数一致候选"
    if packets and any(packet.get("种子本地留存路径状态", "").startswith("S2") for packet in packets):
        return "Q2-有入口或本地种子可复跑"
    if attempts:
        return "Q3-已有自动探针边界记录"
    if gap:
        return "Q4-缺源待搜索"
    if row.get("来源文件类型集合", "") in {"章程或规则线索", "仅章程规则"}:
        return "Q5-规则源不核计划数"
    return "Q6-来源质量待补充"


def next_action(kind, quality, row, attempts):
    if kind.startswith("O0"):
        return "先回第19期PDF原页和湖北官方侧核计划数冲突，再用高校源解释差异。"
    if kind.startswith("O1"):
        return "先回第19期PDF原页补计划数缺口，高校源只作候选读数线索。"
    if kind.startswith("O2"):
        return "先补专业名匹配规则或人工确认专业名，再判断计划数字段。"
    if kind.startswith("O3"):
        return "优先全网检索高校官网2026湖北物理本科普通批计划；若无计划页，至少留存章程规则。"
    if kind.startswith(("O4", "O5")):
        return "复跑已有入口或转录已留存来源，抽取湖北物理普通本科逐专业结构化行。"
    if kind.startswith("O6"):
        if attempts:
            return "沿用自动探针边界，只走公开浏览器交互或静态附件，不绕过访问限制。"
        return "继续搜索高校官网2026湖北计划源，优先可下载附件、公开API和静态表。"
    if kind.startswith("O7"):
        return "按分层抽检规则抽检强辅证行，抽检失败升级同页列/同校/同组。"
    if kind.startswith("O8"):
        return "只核体检、语种、单科、录取规则、调剂和收费限制，不核计划数。"
    return row.get("下一步", "保留为高校侧辅证线索。")


def main():
    refresh_rows = read_csv(SCHOOL_REFRESH)
    gap_rows = read_csv(SOURCE_GAP)
    packet_rows = read_csv(C4C6_PACKETS)
    diff_rows = read_csv(C4C6_DIFF)
    attempt_rows = read_csv(C4C6_ATTEMPTS)
    seed_rows = read_csv(SEEDS)
    official_live = json.loads(OFFICIAL_LIVE.read_text())

    gap_by_school = {row.get("院校代码", ""): row for row in gap_rows}
    packets_by_school_action = defaultdict(list)
    packet_by_id = {}
    for row in packet_rows:
        key = (row.get("院校代码", ""), row.get("官网辅证自动动作", ""))
        packets_by_school_action[key].append(row)
        packet_by_id[row.get("C4C6高校源刷新执行包ID", "")] = row

    diffs_by_school_action = defaultdict(list)
    for row in diff_rows:
        packet = packet_by_id.get(row.get("C4C6高校源刷新执行包ID", ""), {})
        key = (row.get("院校代码", ""), row.get("官网辅证自动动作", "") or packet.get("官网辅证自动动作", ""))
        diffs_by_school_action[key].append(row)

    attempts_by_school = defaultdict(list)
    for row in attempt_rows:
        attempts_by_school[row.get("院校代码", "")].append(row)

    seeds_by_school_name = defaultdict(list)
    for row in seed_rows:
        seeds_by_school_name[row.get("学校名称", "")].append(row)

    source_pdf_sha256 = refresh_rows[0].get("来源PDF_SHA256", "") if refresh_rows else ""
    issue = refresh_rows[0].get("来源期号", "") if refresh_rows else "湖北招生考试2026年19期·本科普通批（下）"

    output_rows = []
    for refresh in refresh_rows:
        school_code = refresh.get("院校代码", "")
        school_name = refresh.get("院校名称OCR", "")
        action = refresh.get("官网辅证自动动作", "")
        key = (school_code, action)
        gap = gap_by_school.get(school_code, {})
        packets = packets_by_school_action.get(key, [])
        diffs = diffs_by_school_action.get(key, [])
        attempts = attempts_by_school.get(school_code, [])
        seeds = seeds_by_school_name.get(school_name, [])
        score = score_for(refresh, gap, packets, diffs, attempts)
        kind = opportunity_type(refresh, gap, diffs, attempts)
        priority = priority_from_type(kind, score)
        quality = quality_label(refresh, gap, packets, diffs, attempts)
        candidate_urls = [
            gap.get("官网URL", ""),
            *(attempt.get("种子官网URL", "") for attempt in attempts),
        ]
        seed_urls = [seed.get("官网URL", "") for seed in seeds]
        local_source_hashes = [
            refresh.get("公开来源文件集合SHA256", ""),
            *(packet.get("私有明细CSV_SHA256", "") for packet in packets),
            *(diff.get("本地未公开明细CSV_SHA256", "") for diff in diffs),
        ]

        output_rows.append({
            "高校官网辅证机会ID": stable_id("SCHOOLOPP", [school_code, action]),
            "来源高校侧辅证刷新公开账本": str(SCHOOL_REFRESH.relative_to(ROOT)),
            "来源B0B1官方源缺口优先表": str(SOURCE_GAP.relative_to(ROOT)),
            "来源C4C6高校源刷新执行包": str(C4C6_PACKETS.relative_to(ROOT)),
            "来源C4C6结构化候选diff公开账本": str(C4C6_DIFF.relative_to(ROOT)),
            "来源C4C6高校官网补源尝试账本": str(C4C6_ATTEMPTS.relative_to(ROOT)),
            "来源高校官网补源种子表": str(SEEDS.relative_to(ROOT)),
            "来源湖北官方公开入口活体复查": str(OFFICIAL_LIVE.relative_to(ROOT)),
            "来源期号": issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校×高校侧辅证动作",
            "任务粒度": "自动辅证机会",
            **false_gate_values(),
            "执行建议序号": "",
            "机会优先级": priority,
            "机会类型": kind,
            "自动收益分": str(score),
            "院校代码": school_code,
            "院校名称OCR": school_name,
            "官网辅证自动动作": action,
            "高校侧刷新批次": refresh.get("高校侧刷新批次", ""),
            "高校侧刷新任务类型": refresh.get("高校侧刷新任务类型", ""),
            "闭环优先级": refresh.get("闭环优先级", ""),
            "官网证据强度": refresh.get("官网证据强度", ""),
            "官网来源状态": refresh.get("官网来源状态", ""),
            "来源文件类型集合": refresh.get("来源文件类型集合", ""),
            "公开来源文件数量": refresh.get("公开来源文件数量", "0"),
            "公开来源URL数量": refresh.get("公开来源URL数量", "0"),
            "涉及招生明细数": refresh.get("涉及招生明细数", "0"),
            "涉及专业组数": refresh.get("涉及专业组数", "0"),
            "涉及PDF页数": refresh.get("涉及PDF页数", "0"),
            "计划数冲突行数": refresh.get("计划数冲突行数", "0"),
            "官网补缺候选行数": refresh.get("官网补缺候选行数", "0"),
            "强辅证抽检行数": refresh.get("强辅证抽检行数", "0"),
            "部分来源待结构化行数": refresh.get("部分来源待结构化行数", "0"),
            "继续补源行数": refresh.get("继续补源行数", "0"),
            "仅章程规则行数": refresh.get("仅章程规则行数", "0"),
            "官网未匹配行数": refresh.get("官网未匹配行数", "0"),
            "字段辅证行数": refresh.get("字段辅证行数", "0"),
            "B0B1缺口优先级": gap.get("补源优先级", ""),
            "B0B1缺口类型": gap.get("结构化证据缺口类型", ""),
            "B0B1逐专业核验任务数": gap.get("逐专业核验任务数", "0") if gap else "0",
            "C4C6执行包数量": str(len(packets)),
            "C4C6执行泳道集合": join_limited(packet.get("执行泳道", "") for packet in packets),
            "C4C6执行优先级集合": join_limited(packet.get("执行优先级", "") for packet in packets),
            "C4C6需补结构化明细数": str(sum(as_int(packet.get("需补结构化明细数")) or 0 for packet in packets)),
            "C4C6需继续补源明细数": str(sum(as_int(packet.get("需继续补源明细数")) or 0 for packet in packets)),
            "C4C6结构化diff优先级集合": join_limited(diff.get("结构化候选diff优先级", "") for diff in diffs),
            "C4C6综合结构化官网证据行数": str(sum(as_int(diff.get("综合结构化官网证据行数")) or 0 for diff in diffs)),
            "C4C6专业名匹配明细数": str(sum(as_int(diff.get("专业名匹配明细数")) or 0 for diff in diffs)),
            "C4C6未匹配明细数": str(sum(as_int(diff.get("未匹配明细数")) or 0 for diff in diffs)),
            "C4C6无结构化官网源明细数": str(sum(as_int(diff.get("无结构化官网源明细数")) or 0 for diff in diffs)),
            "C4C6计划数一致候选数": str(sum(as_int(diff.get("计划数一致候选数")) or 0 for diff in diffs)),
            "C4C6官网可补OCR计划数候选数": str(sum(as_int(diff.get("官网可补OCR计划数候选数")) or 0 for diff in diffs)),
            "C4C6计划数冲突候选数": str(sum(as_int(diff.get("计划数冲突候选数")) or 0 for diff in diffs)),
            "C4C6可生成候选diff明细数": str(sum(as_int(diff.get("可生成候选diff明细数")) or 0 for diff in diffs)),
            "最新自动探针状态": join_limited(attempt.get("最新自动探针状态", "") for attempt in attempts),
            "最新自动探针摘要": join_limited((attempt.get("最新自动探针摘要", "") for attempt in attempts), limit=3),
            "候选官网URL数量": str(len({url for url in candidate_urls if url})),
            "候选官网URL集合SHA256": sha_list(candidate_urls),
            "种子官网URL数量": str(len({url for url in seed_urls if url})),
            "种子官网URL集合SHA256": sha_list(seed_urls),
            "本地公开来源文件集合SHA256": sha_list(local_source_hashes),
            "来源质量判断": quality,
            "自动化下一步": next_action(kind, quality, refresh, attempts),
            "人工最小核验动作": join_limited(
                [
                    *(attempt.get("人工最小核验动作", "") for attempt in attempts),
                    refresh.get("下一步", ""),
                ],
                limit=4,
            ),
            "保真边界": "高校官网/API/PDF/XLSX/章程只作double-check、补缺候选、冲突发现和规则核验，不能替代第19期原页、湖北官方系统或省招办计划。",
            "PDF原页核页状态": refresh.get("PDF原页核页状态", ""),
            "湖北官方系统或省招办计划核验状态": refresh.get("湖北官方系统或省招办计划核验状态", ""),
            "高校官网源刷新状态": refresh.get("高校官网源刷新状态", ""),
            "字段事实写回状态": refresh.get("字段事实写回状态", ""),
            "公开安全策略": "公开层只保存学校级计数、URL集合SHA、来源SHA和自动化状态；不保存逐专业字段读数、OCR原文、人工记录或登录态。",
            "下一步": next_action(kind, quality, refresh, attempts),
        })

    output_rows.sort(
        key=lambda row: (
            {"P0-立即处理": 0, "P1-高收益自动补源": 1, "P2-常规自动补源或抽检": 2, "P3-低收益留存": 3}.get(row["机会优先级"], 9),
            -as_int(row["自动收益分"]),
            row["院校代码"],
            row["官网辅证自动动作"],
        )
    )
    for index, row in enumerate(output_rows, start=1):
        row["执行建议序号"] = str(index)

    write_csv(OUTPUT, output_rows, FIELDS)

    public_text = OUTPUT.read_text(encoding="utf-8-sig")
    forbidden_hits = sorted(token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text)
    if forbidden_hits:
        raise SystemExit(f"公开自动辅证机会队列含禁止内容：{forbidden_hits}")

    priority_counts = Counter(row["机会优先级"] for row in output_rows)
    type_counts = Counter(row["机会类型"] for row in output_rows)
    quality_counts = Counter(row["来源质量判断"] for row in output_rows)
    summary = {
        "status": "issue19_school_source_opportunity_queue_not_final",
        "generated_by": "build_issue19_school_source_opportunity_queue.py",
        "output_table": str(OUTPUT.relative_to(ROOT)),
        "source_issue": issue,
        "source_pdf_sha256": source_pdf_sha256,
        "official_live_recheck_source": str(OFFICIAL_LIVE.relative_to(ROOT)),
        "official_public_plan_can_finalize": bool(official_live.get("official_plan_page", {}).get("can_finalize_plan")),
        "zspt_platform_can_finalize": bool(official_live.get("zspt_platform", {}).get("can_finalize_plan")),
        "input_files": input_snapshot(ROOT, [SCHOOL_REFRESH, SOURCE_GAP, C4C6_PACKETS, C4C6_DIFF, C4C6_ATTEMPTS, SEEDS, OFFICIAL_LIVE]),
        "row_count": len(output_rows),
        "unique_school_count": len({row["院校代码"] for row in output_rows if row["院校代码"]}),
        "priority_counts": dict(priority_counts),
        "opportunity_type_counts": dict(type_counts),
        "source_quality_counts": dict(quality_counts),
        "top_10_school_codes_by_execution_order": [row["院校代码"] for row in output_rows[:10]],
        "top_10_school_names_by_execution_order": [row["院校名称OCR"] for row in output_rows[:10]],
        "total_involved_major_detail_count": sum(as_int(row["涉及招生明细数"]) or 0 for row in output_rows),
        "total_c4c6_no_structured_source_detail_count": sum(as_int(row["C4C6无结构化官网源明细数"]) or 0 for row in output_rows),
        "total_c4c6_candidate_diff_detail_count": sum(as_int(row["C4C6可生成候选diff明细数"]) or 0 for row in output_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in output_rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in output_rows),
        "official_plan_replacement_allowed_count": sum(row["是否允许官网证据替代湖北官方计划"] == "true" for row in output_rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段事实"] == "true" for row in output_rows),
        "policy": {
            "usage": "本表用于安排高校官网/API/PDF/XLSX/章程辅证自动化顺序，优先吃掉高收益且可公开复现的来源。",
            "non_final_gate": "所有行均不得作为推荐依据、不得生成学校专业建议、不得替代湖北官方计划、不得自动写回字段事实。",
            "official_boundary": "高校侧来源只能double-check、补缺候选和发现冲突；字段事实仍需第19期原页、湖北官方系统或省招办计划闭环。",
            "automation_boundary": "自动探针只使用公开入口、公开附件和正常浏览器/API行为；不绕过登录、验证码、403、412、TLS或访问限制。"
        },
        "next_steps": [
            "按执行建议序号优先处理P0：冲突、补缺、未匹配和高收益缺源学校。",
            "P1/P2优先复跑已有入口和已留存来源，生成结构化diff，不直接写回主表。",
            "补源失败时只记录公开边界，转入第一闭环人工页列核验。"
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_text = SUMMARY_OUTPUT.read_text(encoding="utf-8")
    forbidden_summary_hits = sorted(token for token in FORBIDDEN_PUBLIC_TOKENS if token in summary_text)
    if forbidden_summary_hits:
        raise SystemExit(f"公开自动辅证机会摘要含禁止内容：{forbidden_summary_hits}")

    print(f"写出高校官网自动辅证机会队列：{OUTPUT.relative_to(ROOT)}")
    print(f"机会行数：{len(output_rows)}")
    print(f"学校数：{summary['unique_school_count']}")


if __name__ == "__main__":
    main()
