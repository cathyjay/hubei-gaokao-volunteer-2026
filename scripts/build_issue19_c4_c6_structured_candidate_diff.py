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

PUBLIC_OUTPUT = ROOT / "data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-c4-c6-structured-candidate-diff-summary.json"
PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-c4-c6-structured-candidate-diff"
PRIVATE_DETAIL_OUTPUT = PRIVATE_OUTPUT_DIR / "c4-c6-structured-candidate-diff-private-detail.csv"
PRIVATE_INDEX_OUTPUT = PRIVATE_OUTPUT_DIR / "c4-c6-structured-candidate-diff-private-index.csv"

SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"

EXTRA_SCHOOL_SOURCES = [
    {
        "学校名称": "北京语言大学",
        "本地留存文件": "data/external/issue19-c4-c6-official-sources/blcu-2026-hubei-physics-normal.json",
        "来源层级": "新增C4C6高校官网API源",
        "来源说明": "北京语言大学招生系统API，参数为湖北、2026、物理类、普通类。",
    },
    {
        "学校名称": "西安建筑科技大学",
        "本地留存文件": "data/external/issue19-c4-c6-official-sources/xauat-2026-hubei-physics-normal.json",
        "来源层级": "新增C4C6高校官网API源",
        "来源说明": "西安建筑科技大学招生系统API，参数为湖北、2026、物理类、普通类。",
    },
]

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
    "C4C6结构化候选diff公开ID",
    "来源C4C6执行包表",
    "来源C4C6执行包摘要",
    "来源既有官网标准化证据表",
    "来源新增高校官网源清单",
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
    "既有官网标准化证据行数",
    "新增高校官网源标准化行数",
    "综合结构化官网证据行数",
    "综合结构化官网来源文件数",
    "综合结构化官网证据类型集合",
    "专业名匹配明细数",
    "疑似匹配明细数",
    "未匹配明细数",
    "无结构化官网源明细数",
    "计划数一致候选数",
    "官网可补OCR计划数候选数",
    "计划数冲突候选数",
    "计划数未覆盖数",
    "新增高校源命中明细数",
    "新增高校源计划数一致候选数",
    "新增高校源计划数冲突候选数",
    "可生成候选diff明细数",
    "结构化候选diff优先级",
    "官方不可得时替代核验动作",
    "人工复核最小集合说明",
    "本地未公开明细CSV证据编号",
    "本地未公开明细CSV_SHA256",
    "本地未公开明细行数",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_DETAIL_FIELDS = [
    "C4C6结构化候选diff私有明细ID",
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
    "官网证据来源层级",
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
    "高校官网结构化源状态",
    "字段事实写回状态",
    "复核备注",
]

PRIVATE_INDEX_FIELDS = [
    "C4C6结构化候选diff公开ID",
    "C4C6高校源刷新执行包ID",
    "执行总序",
    "执行泳道",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "私有明细行数",
    "新增高校源标准化行数",
    "专业名匹配明细数",
    "新增高校源命中明细数",
    "计划数一致候选数",
    "计划数冲突候选数",
    "结构化候选diff优先级",
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


def normalize_extra_sources(match_module):
    rows = []
    source_meta_by_file = {}
    for source in EXTRA_SCHOOL_SOURCES:
        rel_path = source["本地留存文件"]
        path = ROOT / rel_path
        source_meta_by_file[rel_path] = {
            **source,
            "sha256": sha256(path),
        }
        if path.suffix == ".json":
            parsed = match_module.parse_json_plan(path, source["学校名称"])
        else:
            raise SystemExit(f"暂不支持的新增高校官网源类型：{rel_path}")
        for row in parsed:
            row["来源层级"] = source["来源层级"]
            row["来源说明"] = source["来源说明"]
        rows.extend(parsed)
    return rows, source_meta_by_file


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


def source_layer(best, extra_source_files):
    if not best:
        return "无匹配结构化官网源"
    if best.get("官方来源文件") in extra_source_files:
        return "新增C4C6高校官网源"
    return "既有B0B1留存官网源"


def fidelity_status(status, plan_check, layer):
    if status == "no_school_source":
        return "无结构化官网源-继续自动找源或补parser"
    if status == "matched" and plan_check == "match":
        return f"{layer}专业名和计划数一致-仍待PDF原页与湖北官方侧复核"
    if status == "matched" and plan_check == "mismatch":
        return f"{layer}专业名匹配但计划数冲突-优先核PDF原页"
    if status == "matched" and plan_check == "ocr_plan_missing_official_available":
        return f"{layer}可补OCR计划数候选-需回PDF原页确认OCR漏识"
    if status == "possible_match":
        return f"{layer}疑似匹配-需人工确认专业名"
    if status == "unmatched":
        return "有结构化官网源但未匹配-需补结构化规则或人工确认"
    return "待复核"


def priority_for(match_counts, plan_counts, extra_match_count, extra_source_rows, seed_url_count):
    if plan_counts.get("mismatch", 0) > 0:
        return "D0-存在计划数冲突需优先核PDF原页"
    if extra_match_count > 0:
        return "D1-新增高校官网源已命中需抽检核页"
    if plan_counts.get("match", 0) > 0:
        return "D2-已有结构化源计划数一致候选"
    if match_counts.get("matched", 0) or match_counts.get("possible_match", 0):
        return "D3-已有结构化源但计划数未闭合"
    if extra_source_rows > 0:
        return "D4-新增高校官网源未命中需补规则或核专业名"
    if seed_url_count > 0:
        return "D5-有入口但仍缺结构化计划源"
    return "D6-无入口需继续搜索高校官网计划源"


def alternative_action(priority):
    if priority.startswith("D0"):
        return "自动保留冲突包，人工只优先核计划数冲突行、对应PDF原页和高校源，不逐行全量核。"
    if priority.startswith("D1"):
        return "自动保留新增高校源命中行，人工抽检计划数一致行并核OCR缺失行。"
    if priority.startswith("D2"):
        return "自动生成既有官网源diff，人工抽检计划数一致行并优先核OCR缺失。"
    if priority.startswith("D3"):
        return "自动保留专业名命中线索，人工集中核计划数字段和疑似匹配专业名。"
    if priority.startswith("D4"):
        return "自动检查parser和专业名限定词，必要时人工只看该校新增源和PDF原页。"
    if priority.startswith("D5"):
        return "继续自动抓高校官网入口指向的2026湖北物理计划源，暂不安排大规模人工。"
    return "继续自动搜索高校官网招生计划/API/PDF/XLSX，找不到时再列入少量人工核验。"


def manual_minimum(match_counts, plan_counts, extra_match_count):
    parts = []
    if plan_counts.get("mismatch", 0):
        parts.append("计划数冲突行")
    if plan_counts.get("ocr_plan_missing_official_available", 0):
        parts.append("OCR计划数缺失但官网可补行")
    if match_counts.get("possible_match", 0):
        parts.append("疑似匹配专业名")
    if extra_match_count:
        parts.append("新增高校源命中行抽检")
    if not parts:
        parts.append("继续自动补源，暂不人工逐行核验")
    return "；".join(parts)


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
        "候选值",
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
        raise SystemExit("公开 C4/C6 结构化候选diff包含禁止公开内容")


def main():
    match_module = load_match_module()
    packets = read_csv(C4_C6_PACKETS)
    details = read_csv(C4_C6_PRIVATE_DETAIL)
    retained_rows = read_csv(RETAINED_OFFICIAL)
    fidelity_rows = {row["专业行ID"]: row for row in read_csv(FIELD_FIDELITY)}
    extra_rows, extra_source_meta = normalize_extra_sources(match_module)
    extra_source_files = set(extra_source_meta)

    combined_rows = []
    for row in retained_rows:
        row = dict(row)
        row["来源层级"] = "既有B0B1留存官网源"
        row["来源说明"] = "既有高校官网/API/PDF/XLSX/HTML标准化留存。"
        combined_rows.append(row)
    combined_rows.extend(extra_rows)

    combined_by_school = defaultdict(list)
    retained_by_school = defaultdict(list)
    extra_by_school = defaultdict(list)
    for row in combined_rows:
        combined_by_school[row["学校名称"]].append(row)
    for row in retained_rows:
        retained_by_school[row["学校名称"]].append(row)
    for row in extra_rows:
        extra_by_school[row["学校名称"]].append(row)

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
                match_module, matching_detail, combined_by_school
            )
            coverage = match_module.coverage_conclusion(status, plan_check)
            remaining = match_module.remaining_requirements(
                status, plan_check, detail.get("官网来源状态", "")
            )
            layer = source_layer(best, extra_source_files)
            row = {
                "C4C6结构化候选diff私有明细ID": stable_id(
                    "C4C6DIFFDETAIL",
                    [packet_id, detail["C4C6私有明细任务ID"], status, plan_check, layer],
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
                "官网证据来源层级": layer,
                "最佳官网来源文件": best.get("官方来源文件", "") if best else "",
                "最佳官网证据类型": best.get("证据类型", "") if best else "",
                "最佳官网专业名称": best.get("专业名称", "") if best else "",
                "最佳官网计划数": best.get("计划数", "") if best else "",
                "最佳官网专业组": best.get("专业组", "") if best else "",
                "最佳官网专业代号": best.get("专业代号", "") if best else "",
                "最佳官网学费": best.get("学费", "") if best else "",
                "最佳官网选科": best.get("选科", "") if best else "",
                "保真处理状态": fidelity_status(status, plan_check, layer),
                "仍需核验": remaining,
                **{field: "false" for field in FALSE_FIELDS},
                "PDF原页核页状态": "pending_manual_pdf_review",
                "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
                "高校官网结构化源状态": "structured_school_source_candidate_not_verified",
                "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
                "复核备注": "",
            }
            private_detail_rows.append(row)
            packet_private_rows.append(row)

        school = packet["院校名称OCR"]
        retained_school_rows = retained_by_school.get(school, [])
        extra_school_rows = extra_by_school.get(school, [])
        combined_school_rows = combined_by_school.get(school, [])
        match_counts = Counter(row["本轮官网证据匹配状态"] for row in packet_private_rows)
        plan_counts = Counter(row["本轮计划数核验状态"] for row in packet_private_rows)
        source_layer_counts = Counter(row["官网证据来源层级"] for row in packet_private_rows)
        extra_matched = source_layer_counts.get("新增C4C6高校官网源", 0)
        extra_plan_match = sum(
            1
            for row in packet_private_rows
            if row["官网证据来源层级"] == "新增C4C6高校官网源"
            and row["本轮计划数核验状态"] == "match"
        )
        extra_plan_mismatch = sum(
            1
            for row in packet_private_rows
            if row["官网证据来源层级"] == "新增C4C6高校官网源"
            and row["本轮计划数核验状态"] == "mismatch"
        )
        source_files = {
            row["官方来源文件"] for row in combined_school_rows if row.get("官方来源文件")
        }
        source_types = {row["证据类型"] for row in combined_school_rows if row.get("证据类型")}
        priority = priority_for(
            match_counts,
            plan_counts,
            extra_matched,
            len(extra_school_rows),
            as_int(packet.get("种子官网URL数量")),
        )
        public_id = stable_id("C4C6DIFF", [packet_id, packet["院校代码"], packet["官网辅证自动动作"]])
        private_index_rows.append(
            {
                "C4C6结构化候选diff公开ID": public_id,
                "C4C6高校源刷新执行包ID": packet_id,
                "执行总序": packet["执行总序"],
                "执行泳道": packet["执行泳道"],
                "院校代码": packet["院校代码"],
                "院校名称OCR": school,
                "官网辅证自动动作": packet["官网辅证自动动作"],
                "私有明细行数": str(len(packet_private_rows)),
                "新增高校源标准化行数": str(len(extra_school_rows)),
                "专业名匹配明细数": str(match_counts.get("matched", 0)),
                "新增高校源命中明细数": str(extra_matched),
                "计划数一致候选数": str(plan_counts.get("match", 0)),
                "计划数冲突候选数": str(plan_counts.get("mismatch", 0)),
                "结构化候选diff优先级": priority,
            }
        )
        public_rows.append(
            {
                "C4C6结构化候选diff公开ID": public_id,
                "来源C4C6执行包表": "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv",
                "来源C4C6执行包摘要": "data/working/issue19-c4-c6-school-source-refresh-execution-packets-summary.json",
                "来源既有官网标准化证据表": "data/working/issue19-b0-b1-retained-official-plan-normalized.csv",
                "来源新增高校官网源清单": "data/external/issue19-c4-c6-official-sources",
                "来源全量字段保真总账": "data/working/issue19-full-major-field-fidelity-ledger.csv",
                "来源期号": SOURCE_ISSUE,
                "来源PDF_SHA256": SOURCE_PDF_SHA256,
                "数据阶段": "issue19_c4_c6_structured_candidate_diff",
                "主表粒度": "C4/C6高校源刷新执行包×综合结构化高校官网源候选diff",
                "任务粒度": "公开包级计数；逐专业候选diff和官网字段值仅保存在本地未公开明细",
                **{field: "false" for field in FALSE_FIELDS},
                "C4C6高校源刷新执行包ID": packet_id,
                "执行总序": packet["执行总序"],
                "执行泳道": packet["执行泳道"],
                "院校代码": packet["院校代码"],
                "院校名称OCR": school,
                "官网辅证自动动作": packet["官网辅证自动动作"],
                "涉及私有明细数": str(len(packet_private_rows)),
                "既有官网标准化证据行数": str(len(retained_school_rows)),
                "新增高校官网源标准化行数": str(len(extra_school_rows)),
                "综合结构化官网证据行数": str(len(combined_school_rows)),
                "综合结构化官网来源文件数": str(len(source_files)),
                "综合结构化官网证据类型集合": join_unique(sorted(source_types)),
                "专业名匹配明细数": str(match_counts.get("matched", 0)),
                "疑似匹配明细数": str(match_counts.get("possible_match", 0)),
                "未匹配明细数": str(match_counts.get("unmatched", 0)),
                "无结构化官网源明细数": str(match_counts.get("no_school_source", 0)),
                "计划数一致候选数": str(plan_counts.get("match", 0)),
                "官网可补OCR计划数候选数": str(plan_counts.get("ocr_plan_missing_official_available", 0)),
                "计划数冲突候选数": str(plan_counts.get("mismatch", 0)),
                "计划数未覆盖数": str(plan_counts.get("not_covered", 0)),
                "新增高校源命中明细数": str(extra_matched),
                "新增高校源计划数一致候选数": str(extra_plan_match),
                "新增高校源计划数冲突候选数": str(extra_plan_mismatch),
                "可生成候选diff明细数": str(
                    match_counts.get("matched", 0) + match_counts.get("possible_match", 0)
                ),
                "结构化候选diff优先级": priority,
                "官方不可得时替代核验动作": alternative_action(priority),
                "人工复核最小集合说明": manual_minimum(match_counts, plan_counts, extra_matched),
                "本地未公开明细CSV证据编号": "local_c4_c6_structured_candidate_diff_detail_csv_not_public",
                "本地未公开明细CSV_SHA256": "filled_after_write",
                "本地未公开明细行数": str(len(packet_private_rows)),
                "PDF原页核页状态": "pending_manual_pdf_review",
                "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
                "高校官网结构化源状态": "structured_school_source_candidate_not_verified",
                "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
                "公开安全策略": "公开层只保留包级计数、优先级和SHA；逐专业OCR、官网匹配字段、冲突正文和人工结论不公开。",
                "下一步": "优先核冲突、OCR缺失和新增源命中行；若湖北官方侧不可自动获取，则用高校官网源自动double check加少量PDF原页人工核验闭环。",
            }
        )

    write_csv(PRIVATE_DETAIL_OUTPUT, private_detail_rows, PRIVATE_DETAIL_FIELDS)
    write_csv(PRIVATE_INDEX_OUTPUT, private_index_rows, PRIVATE_INDEX_FIELDS)
    private_detail_sha = sha256(PRIVATE_DETAIL_OUTPUT)
    private_index_sha = sha256(PRIVATE_INDEX_OUTPUT)
    for row in public_rows:
        row["本地未公开明细CSV_SHA256"] = private_detail_sha
    write_csv(PUBLIC_OUTPUT, public_rows, PUBLIC_FIELDS)

    detail_match_counts = Counter(row["本轮官网证据匹配状态"] for row in private_detail_rows)
    detail_plan_counts = Counter(row["本轮计划数核验状态"] for row in private_detail_rows)
    source_layer_counts = Counter(row["官网证据来源层级"] for row in private_detail_rows)
    priority_counts = Counter(row["结构化候选diff优先级"] for row in public_rows)
    lane_priority_counts = Counter(
        f"{row['执行泳道']}|{row['结构化候选diff优先级']}" for row in public_rows
    )
    extra_source_sha = {
        rel_path: meta["sha256"] for rel_path, meta in sorted(extra_source_meta.items())
    }
    summary = {
        "status": "issue19_c4_c6_structured_candidate_diff_not_final",
        "generated_by": "build_issue19_c4_c6_structured_candidate_diff.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_c4_c6_packets": "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv",
        "source_c4_c6_packets_summary": "data/working/issue19-c4-c6-school-source-refresh-execution-packets-summary.json",
        "source_retained_official_plan": "data/working/issue19-b0-b1-retained-official-plan-normalized.csv",
        "source_extra_school_sources": [source["本地留存文件"] for source in EXTRA_SCHOOL_SOURCES],
        "source_extra_school_source_sha256": extra_source_sha,
        "source_field_fidelity_ledger": "data/working/issue19-full-major-field-fidelity-ledger.csv",
        "hubei_official_can_finalize": False,
        "hubei_official_without_login_structured_plan_available": False,
        "school_official_sources_are_substitute_evidence_only": True,
        "output_public_table": "data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv",
        "public_packet_count": len(public_rows),
        "private_detail_row_count": len(private_detail_rows),
        "private_index_row_count": len(private_index_rows),
        "retained_official_row_count": len(retained_rows),
        "retained_official_school_count": len(retained_by_school),
        "extra_school_source_row_count": len(extra_rows),
        "extra_school_source_school_count": len(extra_by_school),
        "combined_structured_source_row_count": len(combined_rows),
        "combined_structured_source_school_count": len(combined_by_school),
        "packet_with_structured_source_count": sum(
            1 for row in public_rows if as_int(row["综合结构化官网证据行数"])
        ),
        "packet_with_candidate_diff_count": sum(
            1 for row in public_rows if as_int(row["可生成候选diff明细数"])
        ),
        "detail_match_status_counts": dict(detail_match_counts),
        "detail_plan_check_counts": dict(detail_plan_counts),
        "source_layer_counts": dict(source_layer_counts),
        "priority_counts": dict(priority_counts),
        "lane_priority_counts": dict(lane_priority_counts),
        "plan_match_candidate_count": detail_plan_counts.get("match", 0),
        "ocr_plan_missing_official_available_count": detail_plan_counts.get(
            "ocr_plan_missing_official_available", 0
        ),
        "plan_mismatch_candidate_count": detail_plan_counts.get("mismatch", 0),
        "no_structured_source_detail_count": detail_match_counts.get("no_school_source", 0),
        "extra_source_matched_detail_count": source_layer_counts.get("新增C4C6高校官网源", 0),
        "extra_source_plan_match_count": sum(
            1
            for row in private_detail_rows
            if row["官网证据来源层级"] == "新增C4C6高校官网源"
            and row["本轮计划数核验状态"] == "match"
        ),
        "extra_source_plan_mismatch_count": sum(
            1
            for row in private_detail_rows
            if row["官网证据来源层级"] == "新增C4C6高校官网源"
            and row["本轮计划数核验状态"] == "mismatch"
        ),
        "private_detail_csv_sha256": private_detail_sha,
        "private_index_csv_sha256": private_index_sha,
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "policy": {
            "goal": "在湖北官方侧计划证据不可自动获取时，用高校官网/API/PDF/XLSX结构化源自动double check，压缩人工核验范围。",
            "boundary": "高校官网源只能作辅证和差异发现，不替代第19期PDF原页、湖北官方系统或省招办计划。",
            "manual_minimization": "人工优先核计划数冲突、OCR计划数缺失但官网可补、疑似匹配和新增源命中抽检，不逐行全量核。",
        },
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert_public_safe([PUBLIC_OUTPUT, SUMMARY_OUTPUT])
    print(f"写出 C4/C6 结构化候选diff公开账本：{PUBLIC_OUTPUT.relative_to(ROOT)}")
    print(f"写出 C4/C6 结构化候选diff摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出本地未公开逐专业候选diff明细：{PRIVATE_DETAIL_OUTPUT.relative_to(ROOT)}")
    print(f"公开包数：{len(public_rows)}")
    print(f"私有明细行数：{len(private_detail_rows)}")
    print(f"专业名匹配计数：{dict(detail_match_counts)}")
    print(f"计划数核验计数：{dict(detail_plan_counts)}")
    print(f"来源层级计数：{dict(source_layer_counts)}")


if __name__ == "__main__":
    main()
