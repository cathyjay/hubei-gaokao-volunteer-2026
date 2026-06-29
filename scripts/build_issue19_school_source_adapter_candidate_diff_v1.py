#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

PARSE_AUDIT = WORKING / "issue19-school-source-adapter-parse-audit-v1-public-ledger.csv"
ADAPTER_WORKBENCH = WORKING / "issue19-school-source-adapter-diff-execution-workbench-v1-public-ledger.csv"
INGESTION = WORKING / "issue19-school-source-structured-ingestion-candidates-public-ledger.csv"
ADMISSION_DETAIL = WORKING / "issue19-admission-detail-master-workbench.csv"
MATCH_SCRIPT = ROOT / "scripts/build_issue19_b0_b1_official_evidence_match.py"
PARSE_AUDIT_SCRIPT = ROOT / "scripts/build_issue19_school_source_adapter_parse_audit_v1.py"

PUBLIC_OUTPUT = WORKING / "issue19-school-source-adapter-candidate-diff-v1-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-adapter-candidate-diff-v1-summary.json"
PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-school-source-adapter-candidate-diff-v1"
PRIVATE_NORMALIZED_OUTPUT = PRIVATE_OUTPUT_DIR / "school-source-adapter-normalized-private-rows.csv"
PRIVATE_DETAIL_OUTPUT = PRIVATE_OUTPUT_DIR / "school-source-adapter-candidate-diff-private-detail.csv"
PRIVATE_INDEX_OUTPUT = PRIVATE_OUTPUT_DIR / "school-source-adapter-candidate-diff-private-index.csv"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_adapter_candidate_diff_v1"
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

PUBLIC_FIELDS = [
    "高校源Adapter候选diff公开ID",
    "来源Adapter解析审计账本",
    "来源AdapterDiff执行工作台",
    "来源逐专业招生明细总工作台",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "审计序号",
    "院校代码",
    "学校键SHA16",
    "高校源Adapter解析审计ID",
    "高校源AdapterDiff执行ID",
    "来源文件类型",
    "解析器族",
    "解析湖北物理类行数",
    "解析湖北物理类计划数合计",
    "第19期同校招生明细数",
    "第19期同校专业组数",
    "私有normalized行数",
    "私有diff明细数",
    "专业名匹配明细数",
    "疑似匹配明细数",
    "未匹配明细数",
    "无结构化高校源明细数",
    "计划数一致候选数",
    "官网可补OCR计划数候选数",
    "计划数冲突候选数",
    "计划数未覆盖数",
    "可生成候选diff明细数",
    "Adapter候选diff优先级",
    "最小人工核验集合",
    "本地未公开normalizedCSV证据编号",
    "本地未公开normalizedCSV_SHA256",
    "本地未公开normalized行数",
    "本地未公开diff明细CSV证据编号",
    "本地未公开diff明细CSV_SHA256",
    "本地未公开diff明细行数",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_NORMALIZED_FIELDS = [
    "高校源AdapterNormalized私有ID",
    "高校源Adapter解析审计ID",
    "高校源AdapterDiff执行ID",
    "院校代码",
    "学校名称",
    "来源文件类型",
    "解析器族",
    "Normalized行序号",
    "官方来源文件",
    "证据类型",
    "年份",
    "省份",
    "科类",
    "批次",
    "类别",
    "专业组",
    "专业代号",
    "专业代码",
    "专业名称",
    "专业备注",
    "计划数",
    "学制",
    "学费",
    "校区",
    "选科",
    "可核字段",
    "局限性",
    "年份证据说明",
]

PRIVATE_DETAIL_FIELDS = [
    "高校源Adapter候选diff私有明细ID",
    "高校源Adapter候选diff公开ID",
    "高校源Adapter解析审计ID",
    "院校代码",
    "院校名称OCR",
    "招生明细总工作台ID",
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
    "本轮高校源匹配状态",
    "本轮专业名称匹配方式",
    "本轮专业名称匹配分",
    "本轮计划数核验状态",
    "本轮高校源覆盖结论",
    "最佳高校源文件",
    "最佳高校源证据类型",
    "最佳高校源专业名称",
    "最佳高校源计划数",
    "最佳高校源专业组",
    "最佳高校源专业代号",
    "最佳高校源学费",
    "最佳高校源选科",
    "保真处理状态",
    "仍需核验",
    *FALSE_FIELDS,
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
    "复核备注",
]

PRIVATE_INDEX_FIELDS = [
    "高校源Adapter候选diff公开ID",
    "院校代码",
    "学校名称",
    "高校源Adapter解析审计ID",
    "私有normalized行数",
    "私有diff明细行数",
    "专业名匹配明细数",
    "疑似匹配明细数",
    "计划数一致候选数",
    "计划数冲突候选数",
    "Adapter候选diff优先级",
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
    "学校名称",
    "专业名称",
    "专业代号",
    "院校专业组代码",
    "字段值",
    "字段读数",
    "人工读数",
    "候选值",
    "OCR正文",
    "OCR行文本",
    "截图路径",
    "复核备注",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
    "data/external/",
]


def clean(value):
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: clean(row.get(field, "")) for field in fields} for row in rows])


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_path(path):
    return str(path.relative_to(ROOT))


def stable_id(prefix, parts):
    text = "|".join(clean(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    text = clean(value)
    return int(text) if text.isdigit() else 0


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence_files_for(source):
    return [
        clean(part)
        for part in source.get("本地公开证据文件集合", "").split("；")
        if clean(part)
    ]


def is_plan_source(rel_path, adapter):
    path = ROOT / rel_path
    if rel_path.startswith("data/working/") or "crosscheck" in path.name.lower():
        return False
    if "charter" in path.name.lower():
        return False
    if path.suffix.lower() in {".html", ".htm"} and "章程" in adapter.get("来源文件类型", ""):
        return False
    return True


def build_normalized_rows(match_module, parse_module, audit_rows, adapter_by_id, ingestion_by_id):
    rows = []
    for audit in audit_rows:
        adapter = adapter_by_id[audit["高校源AdapterDiff执行ID"]]
        source = ingestion_by_id[audit["高校源结构化接入候选ID"]]
        code = audit["院校代码"]
        school_name = parse_module.SCHOOL_NAMES_BY_CODE[code]
        parsed_rows = []
        for rel_path in evidence_files_for(source):
            if not is_plan_source(rel_path, adapter):
                continue
            parsed_rows.extend(parse_module.parse_source(match_module, ROOT / rel_path, code))
        for index, parsed in enumerate(parsed_rows, 1):
            rows.append({
                "高校源AdapterNormalized私有ID": stable_id(
                    "SSNORM",
                    [
                        audit["高校源Adapter解析审计ID"],
                        index,
                        parsed.get("官方来源文件", ""),
                        parsed.get("专业名称", ""),
                        parsed.get("计划数", ""),
                    ],
                ),
                "高校源Adapter解析审计ID": audit["高校源Adapter解析审计ID"],
                "高校源AdapterDiff执行ID": audit["高校源AdapterDiff执行ID"],
                "院校代码": code,
                "学校名称": school_name,
                "来源文件类型": audit["来源文件类型"],
                "解析器族": audit["解析器族"],
                "Normalized行序号": index,
                **{field: parsed.get(field, "") for field in PRIVATE_NORMALIZED_FIELDS if field not in {
                    "高校源AdapterNormalized私有ID",
                    "高校源Adapter解析审计ID",
                    "高校源AdapterDiff执行ID",
                    "院校代码",
                    "学校名称",
                    "来源文件类型",
                    "解析器族",
                    "Normalized行序号",
                }},
            })
    return rows


def match_status(module, detail, source_rows):
    by_school = defaultdict(list)
    by_school[detail["院校名称OCR"]] = source_rows
    best, method, score = module.best_match(detail, by_school)
    if best is None and method == "no_retained_official_plan_for_school":
        status = "no_school_source"
    elif best is None:
        status = "unmatched"
    elif method.startswith("possible_"):
        status = "possible_match"
    else:
        status = "matched"
    return best, method, score, status, module.plan_status(detail, best)


def fidelity_status(status, plan_check):
    if status == "no_school_source":
        return "无结构化高校源-需回到补源或parser"
    if status == "matched" and plan_check == "match":
        return "高校源专业名和计划数一致-仍待PDF原页与湖北官方侧复核"
    if status == "matched" and plan_check == "mismatch":
        return "高校源专业名匹配但计划数冲突-优先核PDF原页"
    if status == "matched" and plan_check == "ocr_plan_missing_official_available":
        return "高校源可补OCR计划数候选-需回PDF原页确认OCR漏识"
    if status == "possible_match":
        return "高校源疑似匹配-需人工确认专业名"
    if status == "unmatched":
        return "有结构化高校源但未匹配-需补规则或人工确认"
    return "待复核"


def priority_for(match_counts, plan_counts):
    if plan_counts.get("mismatch", 0) > 0:
        return "D0-存在计划数冲突需优先核PDF原页"
    if plan_counts.get("ocr_plan_missing_official_available", 0) > 0:
        return "D1-高校源可补OCR计划数缺口需核页"
    if plan_counts.get("match", 0) > 0:
        return "D2-已有计划数一致候选需抽检核页"
    if match_counts.get("matched", 0) or match_counts.get("possible_match", 0):
        return "D3-有专业名命中但计划数未闭合"
    return "D4-结构化源未命中需补规则或人工确认"


def manual_minimum(match_counts, plan_counts):
    parts = []
    if plan_counts.get("mismatch", 0):
        parts.append("计划数冲突行")
    if plan_counts.get("ocr_plan_missing_official_available", 0):
        parts.append("OCR计划数缺失但高校源可补行")
    if match_counts.get("possible_match", 0):
        parts.append("疑似匹配专业名")
    if plan_counts.get("match", 0):
        parts.append("计划数一致候选抽检")
    if not parts:
        parts.append("补parser或人工确认专业名，不做逐行写回")
    return "；".join(parts)


def build_diff_rows(match_module, parse_module, audit_rows, normalized_rows, admission_rows):
    source_rows_by_audit = defaultdict(list)
    for row in normalized_rows:
        source_rows_by_audit[row["高校源Adapter解析审计ID"]].append(row)

    admission_by_code = defaultdict(list)
    for row in admission_rows:
        if row.get("是否真实招生明细") == "true":
            admission_by_code[row["院校代码"]].append(row)

    private_detail_rows = []
    private_index_rows = []
    public_rows = []

    for audit in audit_rows:
        code = audit["院校代码"]
        school_name = parse_module.SCHOOL_NAMES_BY_CODE[code]
        public_id = stable_id("SSDIFF", [SOURCE_PDF_SHA256, audit["高校源Adapter解析审计ID"], code])
        school_source_rows = source_rows_by_audit[audit["高校源Adapter解析审计ID"]]
        details = admission_by_code.get(code, [])
        packet_private_rows = []
        for detail in details:
            matching_detail = {
                "院校名称OCR": school_name,
                "专业名称及备注OCR": detail.get("专业名称及备注OCR", ""),
                "专业计划数OCR候选": detail.get("专业计划数OCR候选", ""),
                "官网来源状态": "has_structured_school_source_adapter_rows",
            }
            best, method, score, status, plan_check = match_status(
                match_module, matching_detail, school_source_rows
            )
            row = {
                "高校源Adapter候选diff私有明细ID": stable_id(
                    "SSDIFFDETAIL",
                    [public_id, detail["专业行ID"], status, plan_check, method],
                ),
                "高校源Adapter候选diff公开ID": public_id,
                "高校源Adapter解析审计ID": audit["高校源Adapter解析审计ID"],
                "院校代码": code,
                "院校名称OCR": detail.get("院校名称OCR", ""),
                "招生明细总工作台ID": detail.get("招生明细总工作台ID", ""),
                "专业行ID": detail.get("专业行ID", ""),
                "专业组出现ID": detail.get("专业组出现ID", ""),
                "院校专业组代码OCR规范化": detail.get("院校专业组代码OCR规范化", ""),
                "来源页码": detail.get("来源页码", ""),
                "版面列": detail.get("版面列", ""),
                "专业组内专业序号": detail.get("专业组内专业序号", ""),
                "专业代号OCR": detail.get("专业代号OCR", ""),
                "专业名称及备注OCR": detail.get("专业名称及备注OCR", ""),
                "OCR专业计划数候选": detail.get("专业计划数OCR候选", ""),
                "OCR学费候选": detail.get("学费OCR候选", ""),
                "OCR再选科目候选": detail.get("再选科目OCR候选", ""),
                "本轮高校源匹配状态": status,
                "本轮专业名称匹配方式": method,
                "本轮专业名称匹配分": score,
                "本轮计划数核验状态": plan_check,
                "本轮高校源覆盖结论": match_module.coverage_conclusion(status, plan_check),
                "最佳高校源文件": best.get("官方来源文件", "") if best else "",
                "最佳高校源证据类型": best.get("证据类型", "") if best else "",
                "最佳高校源专业名称": best.get("专业名称", "") if best else "",
                "最佳高校源计划数": best.get("计划数", "") if best else "",
                "最佳高校源专业组": best.get("专业组", "") if best else "",
                "最佳高校源专业代号": best.get("专业代号", "") if best else "",
                "最佳高校源学费": best.get("学费", "") if best else "",
                "最佳高校源选科": best.get("选科", "") if best else "",
                "保真处理状态": fidelity_status(status, plan_check),
                "仍需核验": match_module.remaining_requirements(status, plan_check, "has_reusable_2026_hubei_plan_source"),
                **false_gate_values(),
                "PDF原页核页状态": "pending_manual_pdf_review",
                "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
                "高校官网结构化源状态": "structured_school_source_candidate_not_verified",
                "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
                "复核备注": "",
            }
            private_detail_rows.append(row)
            packet_private_rows.append(row)

        match_counts = Counter(row["本轮高校源匹配状态"] for row in packet_private_rows)
        plan_counts = Counter(row["本轮计划数核验状态"] for row in packet_private_rows)
        group_count = len({row.get("专业组出现ID", "") for row in details if row.get("专业组出现ID")})
        public_row = {
            "高校源Adapter候选diff公开ID": public_id,
            "来源Adapter解析审计账本": source_path(PARSE_AUDIT),
            "来源AdapterDiff执行工作台": source_path(ADAPTER_WORKBENCH),
            "来源逐专业招生明细总工作台": source_path(ADMISSION_DETAIL),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校源Adapter解析审计×第19期同校逐专业明细候选diff",
            "任务粒度": "公开学校代码级计数；逐专业OCR与高校源匹配明细仅保存在本地未公开CSV",
            **false_gate_values(),
            "审计序号": audit["审计序号"],
            "院校代码": code,
            "学校键SHA16": audit["学校键SHA16"],
            "高校源Adapter解析审计ID": audit["高校源Adapter解析审计ID"],
            "高校源AdapterDiff执行ID": audit["高校源AdapterDiff执行ID"],
            "来源文件类型": audit["来源文件类型"],
            "解析器族": audit["解析器族"],
            "解析湖北物理类行数": audit["解析湖北物理类行数"],
            "解析湖北物理类计划数合计": audit["解析湖北物理类计划数合计"],
            "第19期同校招生明细数": len(details),
            "第19期同校专业组数": group_count,
            "私有normalized行数": len(school_source_rows),
            "私有diff明细数": len(packet_private_rows),
            "专业名匹配明细数": match_counts.get("matched", 0),
            "疑似匹配明细数": match_counts.get("possible_match", 0),
            "未匹配明细数": match_counts.get("unmatched", 0),
            "无结构化高校源明细数": match_counts.get("no_school_source", 0),
            "计划数一致候选数": plan_counts.get("match", 0),
            "官网可补OCR计划数候选数": plan_counts.get("ocr_plan_missing_official_available", 0),
            "计划数冲突候选数": plan_counts.get("mismatch", 0),
            "计划数未覆盖数": plan_counts.get("not_covered", 0),
            "可生成候选diff明细数": match_counts.get("matched", 0) + match_counts.get("possible_match", 0),
            "Adapter候选diff优先级": priority_for(match_counts, plan_counts),
            "最小人工核验集合": manual_minimum(match_counts, plan_counts),
            "本地未公开normalizedCSV证据编号": "local_school_source_adapter_normalized_rows_csv_not_public",
            "本地未公开normalizedCSV_SHA256": "filled_after_write",
            "本地未公开normalized行数": len(school_source_rows),
            "本地未公开diff明细CSV证据编号": "local_school_source_adapter_candidate_diff_detail_csv_not_public",
            "本地未公开diff明细CSV_SHA256": "filled_after_write",
            "本地未公开diff明细行数": len(packet_private_rows),
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网结构化源状态": "structured_school_source_candidate_not_verified",
            "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
            "公开安全策略": "公开层只保留院校代码级计数和SHA；学校名、专业名、OCR字段、高校源字段、冲突正文和人工结论不公开。",
            "下一步": "用私有diff明细优先核计划数冲突、OCR缺失但高校源可补、疑似匹配和一致候选抽检；仍不得替代第19期PDF原页和湖北官方侧。",
        }
        private_index_rows.append({
            "高校源Adapter候选diff公开ID": public_id,
            "院校代码": code,
            "学校名称": school_name,
            "高校源Adapter解析审计ID": audit["高校源Adapter解析审计ID"],
            "私有normalized行数": len(school_source_rows),
            "私有diff明细行数": len(packet_private_rows),
            "专业名匹配明细数": match_counts.get("matched", 0),
            "疑似匹配明细数": match_counts.get("possible_match", 0),
            "计划数一致候选数": plan_counts.get("match", 0),
            "计划数冲突候选数": plan_counts.get("mismatch", 0),
            "Adapter候选diff优先级": public_row["Adapter候选diff优先级"],
        })
        public_rows.append(public_row)

    return public_rows, private_detail_rows, private_index_rows


def counter_dict(rows, field):
    return dict(sorted(Counter(row[field] for row in rows).items()))


def build_summary(public_rows, private_normalized_rows, private_detail_rows, private_index_rows):
    match_counts = Counter(row["本轮高校源匹配状态"] for row in private_detail_rows)
    plan_counts = Counter(row["本轮计划数核验状态"] for row in private_detail_rows)
    return {
        "status": "issue19_school_source_adapter_candidate_diff_v1_not_final",
        "generated_by": "build_issue19_school_source_adapter_candidate_diff_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_parse_audit": source_path(PARSE_AUDIT),
        "source_adapter_workbench": source_path(ADAPTER_WORKBENCH),
        "source_admission_detail": source_path(ADMISSION_DETAIL),
        "output_public_table": source_path(PUBLIC_OUTPUT),
        "row_count": len(public_rows),
        "unique_school_count": len({row["院校代码"] for row in public_rows}),
        "private_normalized_row_count": len(private_normalized_rows),
        "private_diff_detail_row_count": len(private_detail_rows),
        "private_index_row_count": len(private_index_rows),
        "parsed_hubei_physics_row_count": sum(as_int(row["解析湖北物理类行数"]) for row in public_rows),
        "parsed_hubei_physics_plan_sum": sum(as_int(row["解析湖北物理类计划数合计"]) for row in public_rows),
        "admission_detail_row_count": sum(as_int(row["第19期同校招生明细数"]) for row in public_rows),
        "school_group_count": sum(as_int(row["第19期同校专业组数"]) for row in public_rows),
        "source_type_counts": counter_dict(public_rows, "来源文件类型"),
        "parser_family_counts": counter_dict(public_rows, "解析器族"),
        "candidate_priority_counts": counter_dict(public_rows, "Adapter候选diff优先级"),
        "match_status_counts": dict(sorted(match_counts.items())),
        "plan_check_status_counts": dict(sorted(plan_counts.items())),
        "match_candidate_count": match_counts.get("matched", 0) + match_counts.get("possible_match", 0),
        "plan_match_candidate_count": plan_counts.get("match", 0),
        "ocr_plan_missing_official_available_count": plan_counts.get("ocr_plan_missing_official_available", 0),
        "plan_mismatch_candidate_count": plan_counts.get("mismatch", 0),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "final_available_count": 0,
        "private_normalized_csv_sha256": "",
        "private_detail_csv_sha256": "",
        "private_index_csv_sha256": "",
        "public_boundary": "公开表只保存院校代码级计数、私有CSV SHA和非最终门禁；学校名、专业名、OCR字段、高校源字段和人工记录留在Git忽略的私有目录。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"adapter candidate diff contains forbidden public tokens: {hits[:10]}")


def main():
    match_module = load_module(MATCH_SCRIPT, "official_evidence_match")
    parse_module = load_module(PARSE_AUDIT_SCRIPT, "adapter_parse_audit")
    audit_rows = read_csv(PARSE_AUDIT)
    adapter_by_id = {row["高校源AdapterDiff执行ID"]: row for row in read_csv(ADAPTER_WORKBENCH)}
    ingestion_by_id = {row["高校源结构化接入候选ID"]: row for row in read_csv(INGESTION)}
    admission_rows = read_csv(ADMISSION_DETAIL)

    private_normalized_rows = build_normalized_rows(
        match_module, parse_module, audit_rows, adapter_by_id, ingestion_by_id
    )
    public_rows, private_detail_rows, private_index_rows = build_diff_rows(
        match_module, parse_module, audit_rows, private_normalized_rows, admission_rows
    )

    write_csv(PRIVATE_NORMALIZED_OUTPUT, private_normalized_rows, PRIVATE_NORMALIZED_FIELDS)
    write_csv(PRIVATE_DETAIL_OUTPUT, private_detail_rows, PRIVATE_DETAIL_FIELDS)
    write_csv(PRIVATE_INDEX_OUTPUT, private_index_rows, PRIVATE_INDEX_FIELDS)
    normalized_sha = sha256(PRIVATE_NORMALIZED_OUTPUT)
    detail_sha = sha256(PRIVATE_DETAIL_OUTPUT)
    index_sha = sha256(PRIVATE_INDEX_OUTPUT)

    for row in public_rows:
        row["本地未公开normalizedCSV_SHA256"] = normalized_sha
        row["本地未公开diff明细CSV_SHA256"] = detail_sha
    summary = build_summary(public_rows, private_normalized_rows, private_detail_rows, private_index_rows)
    summary["private_normalized_csv_sha256"] = normalized_sha
    summary["private_detail_csv_sha256"] = detail_sha
    summary["private_index_csv_sha256"] = index_sha

    assert_public_safe(public_rows, summary)
    write_csv(PUBLIC_OUTPUT, public_rows, PUBLIC_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(PUBLIC_OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")
    print(f"private normalized rows: {len(private_normalized_rows)}")
    print(f"private diff detail rows: {len(private_detail_rows)}")


if __name__ == "__main__":
    main()
