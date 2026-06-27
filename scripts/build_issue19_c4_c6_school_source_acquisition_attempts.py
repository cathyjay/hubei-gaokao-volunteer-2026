#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

C4_C6_DIFF = ROOT / "data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv"
C4_C6_PACKETS = ROOT / "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv"
SOURCE_SEEDS = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv"
PUBLIC_OUTPUT = ROOT / "data/working/issue19-c4-c6-school-source-acquisition-attempts-public-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-c4-c6-school-source-acquisition-attempts-summary.json"

SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"

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

PUBLIC_FIELDS = [
    "C4C6高校官网补源尝试ID",
    "来源C4C6结构化候选diff公开账本",
    "来源C4C6执行包表",
    "来源高校官网补源种子表",
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
    "院校代码",
    "院校名称OCR",
    "涉及C4C6执行包数",
    "涉及私有明细数",
    "涉及C4明细数",
    "涉及C6明细数",
    "当前结构化候选diff优先级集合",
    "当前可生成候选diff明细数",
    "当前计划数冲突候选数",
    "当前无结构化官网源明细数",
    "种子官网URL",
    "种子本地留存路径",
    "本地入口证据状态",
    "最新自动探针状态",
    "最新自动探针摘要",
    "自动补源建议",
    "人工最小核验动作",
    "保真边界",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网补源状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]


SOURCE_PROBE_OBSERVATIONS = {
    "北京林业大学": {
        "probe_status": "entry_timeout_api_timeout_previous_forbidden",
        "probe_summary": "2026-06-28 http/https 入口和 f/ajax_zsjh 探针均超时；既有留存入口 HTML 存在，既有 API 探针返回 state=0/msg=禁止访问。",
        "auto_action": "保留入口和禁止访问证据；后续可用浏览器正常交互方式复核 XHR，但不得绕过访问限制。",
        "manual_action": "若进入最终候选，100% 回第19期原页/官方系统核专业组和逐专业计划；高校官网只作辅助。",
        "local_evidence": [
            "data/external/issue19-b0-b1-official-sources/bjfu-zsjh-entry.html",
            "data/external/issue19-b0-b1-official-sources/bjfu-ajax-hubei-2026-physics-forbidden.json",
        ],
    },
    "北京语言大学": {
        "probe_status": "structured_source_retained_parser_or_match_rule_needed",
        "probe_summary": "已留存北京语言大学招生系统 API 原始 JSON；C4 包命中 9 条，C6 单条仍未匹配，需核专业名或规则。",
        "auto_action": "补专业名限定词/中外合作等匹配规则，并回看第19期原页确认未匹配行。",
        "manual_action": "人工只核 C6 未匹配行、计划数冲突行和新增源命中抽检。",
        "local_evidence": [
            "data/external/issue19-c4-c6-official-sources/blcu-2026-hubei-physics-normal.json",
        ],
    },
    "山东财经大学": {
        "probe_status": "tls_handshake_failure_entry_and_api",
        "probe_summary": "2026-06-28 http/https 入口和 f/ajax_zsjh 探针均出现 SSL/TLS handshake failure；既有留存入口 HTML 存在。",
        "auto_action": "保留 TLS 失败证据；后续尝试浏览器正常访问或寻找学校发布的 XLS/PDF/HTML 计划页。",
        "manual_action": "若进入最终候选，100% 回第19期原页/官方系统核逐专业字段。",
        "local_evidence": [
            "data/external/issue19-b0-b1-official-sources/sdufe-zsjh-entry.html",
        ],
    },
    "成都理工大学": {
        "probe_status": "http_412_precondition_failed",
        "probe_summary": "2026-06-28 zsdata.cdut.edu.cn 入口和 lqxx/getList API 探针均返回 HTTP 412 Precondition Failed。",
        "auto_action": "保留 412 边界；后续找招生网静态计划页、附件或浏览器可访问的公开查询结果。",
        "manual_action": "最终候选前核第19期原页/官方系统；高校源不可得时不得用旧数据补计划数。",
        "local_evidence": [],
    },
    "云南大学": {
        "probe_status": "entry_200_api_403_forbidden",
        "probe_summary": "2026-06-28 入口页 http/https 均 200，f/ajax_zsjh 探针均 403；既有留存入口 HTML 和禁止访问 JSON 存在。",
        "auto_action": "保留 403 边界；后续仅用公开浏览器交互或学校静态附件，不绕过接口限制。",
        "manual_action": "若进入最终候选，100% 回第19期原页/官方系统核专业组边界和计划数。",
        "local_evidence": [
            "data/external/issue19-b0-b1-official-sources/ynu-zsjh-entry.html",
            "data/external/issue19-b0-b1-official-sources/ynu-ajax-hubei-2026-physics-forbidden.json",
        ],
    },
    "西安建筑科技大学": {
        "probe_status": "official_api_retained_structured_diff_available",
        "probe_summary": "2026-06-28 已留存西安建筑科技大学招生系统 API 原始 JSON；返回 2026 湖北物理普通类 20 条逐专业计划，合计 80。",
        "auto_action": "已接入 C4/C6 结构化候选 diff；后续优先核计划数冲突、OCR 缺失和新增源命中抽检。",
        "manual_action": "最终候选前仍需核第19期原页/官方系统；API 未给湖北院校专业组代码、学费和专业代号。",
        "local_evidence": [
            "data/external/issue19-c4-c6-official-sources/xauat-2026-hubei-physics-normal.json",
            "data/working/issue19-c4-c6-xauat-official-source-fetch-public-ledger.csv",
        ],
    },
}

NO_SEED_DEFAULT = {
    "probe_status": "no_seed_need_official_source_search",
    "probe_summary": "当前 C4/C6 包无高校官网计划入口种子；需优先搜索学校本科招生网 2026 湖北物理普通本科计划源。",
    "auto_action": "先搜索官方招生网 API/HTML/XLSX/PDF，再按来源类型接入解析器。",
    "manual_action": "若学校进入最终候选而官网源未取得，必须回第19期原页/官方系统人工核验。",
    "local_evidence": [],
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


def as_int(value):
    text = str(value or "").strip()
    return int(text) if text.isdigit() else 0


def join_unique(values):
    seen = []
    seen_set = set()
    for value in values:
        if value and value not in seen_set:
            seen.append(value)
            seen_set.add(value)
    return "；".join(seen)


def seed_by_school():
    seeds = {}
    for row in read_csv(SOURCE_SEEDS):
        seeds[row["学校名称"]] = row
    return seeds


def local_evidence_status(paths):
    if not paths:
        return "no_local_source_evidence_yet"
    statuses = []
    for rel in paths:
        path = ROOT / rel
        if path.exists() and path.stat().st_size > 0:
            statuses.append(f"{rel}:exists")
        else:
            statuses.append(f"{rel}:missing")
    return "；".join(statuses)


def acquisition_bucket(priority):
    if priority.startswith("D4"):
        return "needs_parser_or_match_rule"
    if priority.startswith("D5"):
        return "known_entry_but_not_structured"
    if priority.startswith("D6"):
        return "no_entry_need_search"
    return "not_in_acquisition_gap"


def main():
    diff_rows = read_csv(C4_C6_DIFF)
    packets = read_csv(C4_C6_PACKETS)
    seeds = seed_by_school()
    packets_by_school = defaultdict(list)
    for row in diff_rows:
        if acquisition_bucket(row["结构化候选diff优先级"]) != "not_in_acquisition_gap":
            packets_by_school[row["院校名称OCR"]].append(row)

    output_rows = []
    for school in sorted(packets_by_school):
        rows = packets_by_school[school]
        first = rows[0]
        seed = seeds.get(school, {})
        observation = SOURCE_PROBE_OBSERVATIONS.get(school, NO_SEED_DEFAULT)
        local_evidence = observation.get("local_evidence", [])
        priorities = join_unique(row["结构化候选diff优先级"] for row in rows)
        actions = join_unique(row["官网辅证自动动作"] for row in rows)
        row = {
            "C4C6高校官网补源尝试ID": stable_id(
                "C4C6SOURCEATTEMPT", [first["院校代码"], school, priorities]
            ),
            "来源C4C6结构化候选diff公开账本": "data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv",
            "来源C4C6执行包表": "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv",
            "来源高校官网补源种子表": "data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": "issue19_c4_c6_school_source_acquisition_attempts",
            "主表粒度": "C4/C6高校×官网补源尝试",
            "任务粒度": "公开学校级补源状态；不保存逐专业字段值或登录态",
            **{field: "false" for field in FALSE_FIELDS},
            "院校代码": first["院校代码"],
            "院校名称OCR": school,
            "涉及C4C6执行包数": str(len(rows)),
            "涉及私有明细数": str(sum(as_int(row["涉及私有明细数"]) for row in rows)),
            "涉及C4明细数": str(
                sum(as_int(row["涉及私有明细数"]) for row in rows if "C4-" in row["官网辅证自动动作"])
            ),
            "涉及C6明细数": str(
                sum(as_int(row["涉及私有明细数"]) for row in rows if "C6-" in row["官网辅证自动动作"])
            ),
            "当前结构化候选diff优先级集合": priorities,
            "当前可生成候选diff明细数": str(sum(as_int(row["可生成候选diff明细数"]) for row in rows)),
            "当前计划数冲突候选数": str(sum(as_int(row["计划数冲突候选数"]) for row in rows)),
            "当前无结构化官网源明细数": str(sum(as_int(row["无结构化官网源明细数"]) for row in rows)),
            "种子官网URL": seed.get("官网URL", ""),
            "种子本地留存路径": seed.get("本地留存路径", ""),
            "本地入口证据状态": local_evidence_status(local_evidence),
            "最新自动探针状态": observation["probe_status"],
            "最新自动探针摘要": observation["probe_summary"],
            "自动补源建议": observation["auto_action"],
            "人工最小核验动作": observation["manual_action"],
            "保真边界": "高校官网源只作 double check 和差异发现，不能替代第19期原页、湖北官方系统或省招办计划。",
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "高校官网补源状态": acquisition_bucket(priorities),
            "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
            "公开安全策略": "公开层只保存学校级URL、状态、计数和不可得原因；不保存登录态、逐专业字段值、逐专业候选值或人工记录。",
            "下一步": f"{actions}：{observation['auto_action']}",
        }
        output_rows.append(row)

    write_csv(PUBLIC_OUTPUT, output_rows, PUBLIC_FIELDS)

    status_counts = Counter(row["最新自动探针状态"] for row in output_rows)
    bucket_counts = Counter(row["高校官网补源状态"] for row in output_rows)
    summary = {
        "status": "issue19_c4_c6_school_source_acquisition_attempts_not_final",
        "generated_by": "build_issue19_c4_c6_school_source_acquisition_attempts.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_c4_c6_structured_candidate_diff": "data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv",
        "source_c4_c6_packets": "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv",
        "source_school_seed_table": "data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv",
        "output_public_table": "data/working/issue19-c4-c6-school-source-acquisition-attempts-public-ledger.csv",
        "row_count": len(output_rows),
        "school_count": len({row["院校名称OCR"] for row in output_rows}),
        "total_private_detail_count": sum(as_int(row["涉及私有明细数"]) for row in output_rows),
        "total_c4_detail_count": sum(as_int(row["涉及C4明细数"]) for row in output_rows),
        "total_c6_detail_count": sum(as_int(row["涉及C6明细数"]) for row in output_rows),
        "total_no_structured_source_detail_count": sum(as_int(row["当前无结构化官网源明细数"]) for row in output_rows),
        "status_counts": dict(status_counts),
        "bucket_counts": dict(bucket_counts),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "policy": {
            "goal": "记录 C4/C6 D4/D5/D6 学校的官网补源尝试和不可得边界，指导下一轮自动源扩展。",
            "boundary": "本账本不保存招生计划字段事实，不确认任何专业或计划数；只说明补源状态和下一步。",
        },
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public_text = PUBLIC_OUTPUT.read_text(encoding="utf-8", errors="ignore") + SUMMARY_OUTPUT.read_text(
        encoding="utf-8", errors="ignore"
    )
    forbidden = ["/Users/", "private/", "Authorization", "Bearer ", "Cookie", "最终推荐", "最终方案", "可填报"]
    if any(token in public_text for token in forbidden):
        raise SystemExit("公开 C4/C6 官网补源尝试账本包含禁止公开内容")
    print(f"写出 C4/C6 官网补源尝试公开账本：{PUBLIC_OUTPUT.relative_to(ROOT)}")
    print(f"写出 C4/C6 官网补源尝试摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"学校数：{summary['school_count']}")
    print(f"探针状态：{dict(status_counts)}")


if __name__ == "__main__":
    main()
