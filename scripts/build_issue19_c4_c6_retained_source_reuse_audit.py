#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

C4_C6_PACKETS = ROOT / "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv"
C4_C6_PACKETS_SUMMARY = (
    ROOT / "data/working/issue19-c4-c6-school-source-refresh-execution-packets-summary.json"
)
C4_C6_PRIVATE_DETAIL = (
    ROOT
    / "private/review-assets/issue19-c4-c6-school-source-refresh-execution-packets"
    / "c4-c6-source-refresh-private-detail-workbench.csv"
)
RETAINED_OFFICIAL = ROOT / "data/working/issue19-b0-b1-retained-official-plan-normalized.csv"
FIELD_FIDELITY = ROOT / "data/working/issue19-full-major-field-fidelity-ledger.csv"
MATCH_SCRIPT = ROOT / "scripts/build_issue19_b0_b1_official_evidence_match.py"

PUBLIC_OUTPUT = ROOT / "data/working/issue19-c4-c6-retained-source-reuse-public-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-c4-c6-retained-source-reuse-summary.json"
PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-c4-c6-retained-source-reuse"
PRIVATE_DETAIL_OUTPUT = PRIVATE_OUTPUT_DIR / "c4-c6-retained-source-reuse-private-detail.csv"
PRIVATE_INDEX_OUTPUT = PRIVATE_OUTPUT_DIR / "c4-c6-retained-source-reuse-private-index.csv"

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
    "C4C6官网源复用审计ID",
    "来源C4C6执行包表",
    "来源C4C6执行包摘要",
    "来源官网标准化证据表",
    "来源全量字段保真总账",
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
    "C4C6高校源刷新执行包ID",
    "执行总序",
    "执行泳道",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "涉及私有明细数",
    "已有标准化官网证据行数",
    "已有标准化官网来源文件数",
    "已有标准化官网证据类型集合",
    "本轮官网专业名匹配明细数",
    "本轮官网疑似匹配明细数",
    "本轮官网未匹配明细数",
    "本轮无留存结构化官网源明细数",
    "计划数一致候选数",
    "官网可补OCR计划数候选数",
    "计划数冲突候选数",
    "计划数未覆盖数",
    "已有源可生成候选diff明细数",
    "结构化复用优先级",
    "建议下一步自动动作",
    "本地未公开明细CSV证据编号",
    "本地未公开明细CSV_SHA256",
    "本地未公开明细行数",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源复用状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]


PRIVATE_DETAIL_FIELDS = [
    "C4C6官网源复用私有明细ID",
    "来源C4C6执行包ID",
    "来源C4C6私有明细任务ID",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "执行泳道",
    "专业行ID",
    "专业组出现ID",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR",
    "OCR专业计划数候选",
    "OCR学费候选",
    "OCR再选科目候选",
    "本轮官网证据匹配状态",
    "本轮专业名称匹配方式",
    "本轮专业名称匹配分",
    "本轮计划数核验状态",
    "本轮官网证据覆盖结论",
    "最佳官网来源文件",
    "最佳官网证据类型",
    "最佳官网专业名称",
    "最佳官网计划数",
    "最佳官网专业组",
    "最佳官网专业代号",
    "最佳官网学费",
    "最佳官网选科",
    "保真处理状态",
    "仍需核验",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源复用状态",
    "字段事实写回状态",
    "复核备注",
]


PRIVATE_INDEX_FIELDS = [
    "C4C6官网源复用审计ID",
    "C4C6高校源刷新执行包ID",
    "执行总序",
    "执行泳道",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "私有明细行数",
    "本轮官网专业名匹配明细数",
    "计划数一致候选数",
    "结构化复用优先级",
]


def load_match_module():
    spec = importlib.util.spec_from_file_location("official_evidence_match", MATCH_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def join_unique(values):
    seen = []
    seen_set = set()
    for value in values:
        if value and value not in seen_set:
            seen.append(value)
            seen_set.add(value)
    return "；".join(seen)


def as_int(value):
    text = str(value or "").strip()
    return int(text) if text.isdigit() else 0


def detail_text(private_row, fidelity_row, field_name, fallback_name):
    return fidelity_row.get(field_name, "") or private_row.get(fallback_name, "")


def match_status(module, detail, official_rows_by_school):
    best, method, score = module.best_match(detail, official_rows_by_school)
    if best is None and method == "no_retained_official_plan_for_school":
        status = "no_school_source"
    elif best is None:
        status = "unmatched"
    elif method.startswith("possible_"):
        status = "possible_match"
    else:
        status = "matched"
    plan_check = module.plan_status(detail, best)
    return best, method, score, status, plan_check


def fidelity_status(status, plan_check):
    if status == "no_school_source":
        return "无留存结构化官网源-先补源或补parser"
    if status == "matched" and plan_check == "match":
        return "官网专业名和计划数一致-仍待PDF原页与湖北官方侧复核"
    if status == "matched" and plan_check == "mismatch":
        return "官网专业名匹配但计划数冲突-优先核PDF原页"
    if status == "matched" and plan_check == "ocr_plan_missing_official_available":
        return "官网可补OCR计划数候选-需回PDF原页确认OCR漏识"
    if status == "possible_match":
        return "疑似匹配-需人工确认专业名"
    if status == "unmatched":
        return "有留存官网源但未匹配-需补结构化规则或人工确认"
    return "待复核"


def priority_for(row_count, match_count, possible_count, plan_match_count, seed_url_count):
    if plan_match_count > 0:
        return "R0-已有官网源且存在计划数一致候选"
    if match_count > 0 or possible_count > 0:
        return "R1-已有官网源但计划数需核页或OCR补缺"
    if row_count > 0:
        return "R2-已有官网源但未匹配需补规则"
    if seed_url_count > 0:
        return "R3-无留存标准化源但有入口需抓取或补parser"
    return "R4-无入口需搜索高校官网计划源"


def next_action(priority):
    if priority == "R0-已有官网源且存在计划数一致候选":
        return "生成候选diff并优先回看PDF原页与湖北官方侧，不写回主表。"
    if priority == "R1-已有官网源但计划数需核页或OCR补缺":
        return "保留官网候选值，优先核PDF原页计划数和OCR漏识。"
    if priority == "R2-已有官网源但未匹配需补规则":
        return "检查专业名限定词、批次科类筛选和parser字段映射。"
    if priority == "R3-无留存标准化源但有入口需抓取或补parser":
        return "先抓取入口指向的2026湖北物理普通本科计划源，再结构化。"
    return "先搜索高校招生官网2026湖北招生计划，找到官方PDF/XLSX/HTML/API后再入库。"


def assert_public_safe(paths):
    forbidden = [
        "/Users/",
        "/home/",
        "/var/folders/",
        "/private/",
        "private/",
        "private\\",
        "专业名称及备注OCR",
        "OCR专业计划数候选",
        "OCR学费候选",
        "OCR再选科目候选",
        "最佳官网专业名称",
        "最佳官网计划数",
        "人工读数",
        "已确认",
        "已核准",
        "最终推荐",
        "最终方案",
        "可填报",
        "可排序",
        "Authorization",
        "Bearer ",
        "Cookie",
        "access_token",
        "password",
        "secret",
    ]
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    if any(token in text for token in forbidden):
        raise SystemExit("公开 C4/C6 官网源复用审计包含禁止公开内容")


def main():
    match_module = load_match_module()
    packets = read_csv(C4_C6_PACKETS)
    details = read_csv(C4_C6_PRIVATE_DETAIL)
    retained_rows = read_csv(RETAINED_OFFICIAL)
    fidelity_rows = {row["专业行ID"]: row for row in read_csv(FIELD_FIDELITY)}

    retained_by_school = defaultdict(list)
    for row in retained_rows:
        retained_by_school[row["学校名称"]].append(row)

    details_by_packet = defaultdict(list)
    for row in details:
        details_by_packet[row["来源C4C6执行包ID"]].append(row)

    private_detail_rows = []
    private_index_rows = []
    public_rows = []

    for packet in packets:
        packet_id = packet["C4C6高校源刷新执行包ID"]
        packet_details = details_by_packet.get(packet_id, [])
        packet_private_rows = []
        for detail in packet_details:
            fidelity = fidelity_rows.get(detail["专业行ID"], {})
            matching_detail = {
                "院校名称OCR": detail["院校名称OCR"],
                "专业名称及备注OCR": detail_text(
                    detail, fidelity, "专业名称及备注OCR", "专业名称及备注短摘"
                ),
                "专业计划数OCR候选": detail_text(
                    detail, fidelity, "专业计划数OCR候选", "OCR专业计划数候选"
                ),
                "官网来源状态": detail.get("官网来源状态", ""),
            }
            best, method, score, status, plan_check = match_status(
                match_module, matching_detail, retained_by_school
            )
            coverage = match_module.coverage_conclusion(status, plan_check)
            remaining = match_module.remaining_requirements(
                status, plan_check, detail.get("官网来源状态", "")
            )
            row = {
                "C4C6官网源复用私有明细ID": stable_id(
                    "C4C6REUSEDETAIL",
                    [packet_id, detail["C4C6私有明细任务ID"], status, plan_check],
                ),
                "来源C4C6执行包ID": packet_id,
                "来源C4C6私有明细任务ID": detail["C4C6私有明细任务ID"],
                "院校代码": detail["院校代码"],
                "院校名称OCR": detail["院校名称OCR"],
                "官网辅证自动动作": detail["官网辅证自动动作"],
                "执行泳道": detail["执行泳道"],
                "专业行ID": detail["专业行ID"],
                "专业组出现ID": detail["专业组出现ID"],
                "院校专业组代码OCR规范化": detail["院校专业组代码OCR规范化"],
                "来源页码": detail["来源页码"],
                "版面列": detail["版面列"],
                "专业组内专业序号": detail["专业组内专业序号"],
                "专业代号OCR": detail["专业代号OCR"],
                "专业名称及备注OCR": matching_detail["专业名称及备注OCR"],
                "OCR专业计划数候选": matching_detail["专业计划数OCR候选"],
                "OCR学费候选": detail_text(detail, fidelity, "学费OCR候选", "OCR学费候选"),
                "OCR再选科目候选": detail_text(
                    detail, fidelity, "再选科目OCR候选", "OCR再选科目候选"
                ),
                "本轮官网证据匹配状态": status,
                "本轮专业名称匹配方式": method,
                "本轮专业名称匹配分": str(score),
                "本轮计划数核验状态": plan_check,
                "本轮官网证据覆盖结论": coverage,
                "最佳官网来源文件": best.get("官方来源文件", "") if best else "",
                "最佳官网证据类型": best.get("证据类型", "") if best else "",
                "最佳官网专业名称": best.get("专业名称", "") if best else "",
                "最佳官网计划数": best.get("计划数", "") if best else "",
                "最佳官网专业组": best.get("专业组", "") if best else "",
                "最佳官网专业代号": best.get("专业代号", "") if best else "",
                "最佳官网学费": best.get("学费", "") if best else "",
                "最佳官网选科": best.get("选科", "") if best else "",
                "保真处理状态": fidelity_status(status, plan_check),
                "仍需核验": remaining,
                **{field: "false" for field in FALSE_FIELDS},
                "PDF原页核页状态": "pending_manual_pdf_review",
                "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
                "高校官网源复用状态": "retained_source_reuse_candidate_not_verified",
                "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
                "复核备注": "",
            }
            private_detail_rows.append(row)
            packet_private_rows.append(row)

        retained_school_rows = retained_by_school.get(packet["院校名称OCR"], [])
        match_counts = Counter(row["本轮官网证据匹配状态"] for row in packet_private_rows)
        plan_counts = Counter(row["本轮计划数核验状态"] for row in packet_private_rows)
        source_files = {row["官方来源文件"] for row in retained_school_rows if row.get("官方来源文件")}
        source_types = {row["证据类型"] for row in retained_school_rows if row.get("证据类型")}
        priority = priority_for(
            len(retained_school_rows),
            match_counts.get("matched", 0),
            match_counts.get("possible_match", 0),
            plan_counts.get("match", 0),
            as_int(packet.get("种子官网URL数量")),
        )
        public_id = stable_id("C4C6REUSE", [packet_id, packet["院校代码"], packet["官网辅证自动动作"]])
        private_index_rows.append(
            {
                "C4C6官网源复用审计ID": public_id,
                "C4C6高校源刷新执行包ID": packet_id,
                "执行总序": packet["执行总序"],
                "执行泳道": packet["执行泳道"],
                "院校代码": packet["院校代码"],
                "院校名称OCR": packet["院校名称OCR"],
                "官网辅证自动动作": packet["官网辅证自动动作"],
                "私有明细行数": str(len(packet_private_rows)),
                "本轮官网专业名匹配明细数": str(match_counts.get("matched", 0)),
                "计划数一致候选数": str(plan_counts.get("match", 0)),
                "结构化复用优先级": priority,
            }
        )
        public_rows.append(
            {
                "C4C6官网源复用审计ID": public_id,
                "来源C4C6执行包表": "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv",
                "来源C4C6执行包摘要": "data/working/issue19-c4-c6-school-source-refresh-execution-packets-summary.json",
                "来源官网标准化证据表": "data/working/issue19-b0-b1-retained-official-plan-normalized.csv",
                "来源全量字段保真总账": "data/working/issue19-full-major-field-fidelity-ledger.csv",
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "数据阶段": "issue19_c4_c6_retained_source_reuse_audit",
                "主表粒度": "C4/C6高校源刷新执行包×已留存官网标准化证据复用",
                "任务粒度": "公开包级审计；逐专业匹配候选仅保存在本地未公开明细",
                **{field: "false" for field in FALSE_FIELDS},
                "C4C6高校源刷新执行包ID": packet_id,
                "执行总序": packet["执行总序"],
                "执行泳道": packet["执行泳道"],
                "院校代码": packet["院校代码"],
                "院校名称OCR": packet["院校名称OCR"],
                "官网辅证自动动作": packet["官网辅证自动动作"],
                "涉及私有明细数": str(len(packet_private_rows)),
                "已有标准化官网证据行数": str(len(retained_school_rows)),
                "已有标准化官网来源文件数": str(len(source_files)),
                "已有标准化官网证据类型集合": join_unique(sorted(source_types)),
                "本轮官网专业名匹配明细数": str(match_counts.get("matched", 0)),
                "本轮官网疑似匹配明细数": str(match_counts.get("possible_match", 0)),
                "本轮官网未匹配明细数": str(match_counts.get("unmatched", 0)),
                "本轮无留存结构化官网源明细数": str(match_counts.get("no_school_source", 0)),
                "计划数一致候选数": str(plan_counts.get("match", 0)),
                "官网可补OCR计划数候选数": str(plan_counts.get("ocr_plan_missing_official_available", 0)),
                "计划数冲突候选数": str(plan_counts.get("mismatch", 0)),
                "计划数未覆盖数": str(plan_counts.get("not_covered", 0)),
                "已有源可生成候选diff明细数": str(
                    match_counts.get("matched", 0) + match_counts.get("possible_match", 0)
                ),
                "结构化复用优先级": priority,
                "建议下一步自动动作": next_action(priority),
                "本地未公开明细CSV证据编号": "local_c4_c6_retained_source_reuse_detail_csv_not_public",
                "本地未公开明细CSV_SHA256": "filled_after_write",
                "本地未公开明细行数": str(len(packet_private_rows)),
                "PDF原页核页状态": "pending_manual_pdf_review",
                "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
                "高校官网源复用状态": "retained_source_reuse_audit_not_verified",
                "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
                "公开安全策略": "公开层只保留包级计数、优先级和SHA；逐专业字段值、官网候选值和复核正文不公开。",
                "下一步": "用本地未公开明细生成候选diff；所有字段仍需PDF原页、湖北官方侧和必要高校辅证闭环。",
            }
        )

    write_csv(PRIVATE_DETAIL_OUTPUT, private_detail_rows, PRIVATE_DETAIL_FIELDS)
    write_csv(PRIVATE_INDEX_OUTPUT, private_index_rows, PRIVATE_INDEX_FIELDS)
    private_detail_sha = sha256(PRIVATE_DETAIL_OUTPUT)
    private_index_sha = sha256(PRIVATE_INDEX_OUTPUT)
    for row in public_rows:
        row["本地未公开明细CSV_SHA256"] = private_detail_sha
    write_csv(PUBLIC_OUTPUT, public_rows, PUBLIC_FIELDS)

    public_match_counts = Counter()
    public_plan_counts = Counter()
    for row in private_detail_rows:
        public_match_counts[row["本轮官网证据匹配状态"]] += 1
        public_plan_counts[row["本轮计划数核验状态"]] += 1

    priority_counts = Counter(row["结构化复用优先级"] for row in public_rows)
    lane_priority_counts = Counter(
        f"{row['执行泳道']}|{row['结构化复用优先级']}" for row in public_rows
    )
    summary = {
        "status": "issue19_c4_c6_retained_source_reuse_audit_not_final",
        "generated_by": "build_issue19_c4_c6_retained_source_reuse_audit.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_c4_c6_packets": "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv",
        "source_c4_c6_packets_summary": "data/working/issue19-c4-c6-school-source-refresh-execution-packets-summary.json",
        "source_retained_official_plan": "data/working/issue19-b0-b1-retained-official-plan-normalized.csv",
        "source_field_fidelity_ledger": "data/working/issue19-full-major-field-fidelity-ledger.csv",
        "official_can_finalize": False,
        "official_without_login_structured_plan_available": False,
        "output_public_table": "data/working/issue19-c4-c6-retained-source-reuse-public-ledger.csv",
        "public_packet_count": len(public_rows),
        "private_detail_row_count": len(private_detail_rows),
        "private_index_row_count": len(private_index_rows),
        "retained_official_row_count": len(retained_rows),
        "retained_official_school_count": len(retained_by_school),
        "packet_with_retained_source_count": sum(
            1 for row in public_rows if as_int(row["已有标准化官网证据行数"])
        ),
        "packet_with_reuse_candidate_count": sum(
            1 for row in public_rows if as_int(row["已有源可生成候选diff明细数"])
        ),
        "detail_match_status_counts": dict(public_match_counts),
        "detail_plan_check_counts": dict(public_plan_counts),
        "priority_counts": dict(priority_counts),
        "lane_priority_counts": dict(lane_priority_counts),
        "plan_match_candidate_count": public_plan_counts.get("match", 0),
        "ocr_plan_missing_official_available_count": public_plan_counts.get(
            "ocr_plan_missing_official_available", 0
        ),
        "plan_mismatch_candidate_count": public_plan_counts.get("mismatch", 0),
        "no_retained_source_detail_count": public_match_counts.get("no_school_source", 0),
        "private_detail_csv_sha256": private_detail_sha,
        "private_index_csv_sha256": private_index_sha,
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "policy": {
            "goal": "复用已留存高校官网标准化证据，给C4/C6执行包生成候选diff优先级。",
            "boundary": "本审计只证明哪些包已有可复用官网源和候选匹配，不证明字段事实完成核验。",
            "required_closure": "字段事实仍必须回到第19期PDF原页、湖北官方系统或省招办计划、必要高校辅证和人工复核闭环。",
        },
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert_public_safe([PUBLIC_OUTPUT, SUMMARY_OUTPUT])
    print(f"写出 C4/C6 官网源复用公开审计：{PUBLIC_OUTPUT.relative_to(ROOT)}")
    print(f"写出 C4/C6 官网源复用摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出本地未公开逐专业复用明细：{PRIVATE_DETAIL_OUTPUT.relative_to(ROOT)}")
    print(f"公开包数：{len(public_rows)}")
    print(f"私有明细行数：{len(private_detail_rows)}")
    print(f"专业名匹配计数：{dict(public_match_counts)}")
    print(f"计划数核验计数：{dict(public_plan_counts)}")


if __name__ == "__main__":
    main()
