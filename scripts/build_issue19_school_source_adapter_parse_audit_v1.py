#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

ADAPTER_WORKBENCH = WORKING / "issue19-school-source-adapter-diff-execution-workbench-v1-public-ledger.csv"
INGESTION = WORKING / "issue19-school-source-structured-ingestion-candidates-public-ledger.csv"
MATCH_SCRIPT = ROOT / "scripts/build_issue19_b0_b1_official_evidence_match.py"

OUTPUT = WORKING / "issue19-school-source-adapter-parse-audit-v1-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-adapter-parse-audit-v1-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_adapter_parse_audit_v1"
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
    "高校源Adapter解析审计ID",
    "来源AdapterDiff执行工作台",
    "来源结构化接入候选账本",
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
    "高校源AdapterDiff执行ID",
    "高校源结构化接入候选ID",
    "接入批次",
    "来源文件类型",
    "Parser状态桶",
    "Normalized桥接状态",
    "Diff执行桶",
    "公开证据集合SHA16",
    "证据文件数量",
    "可解析证据文件数量",
    "不可解析证据文件数量",
    "非计划规则侧证数量",
    "解析器族",
    "解析结果状态",
    "NormalizedSchema版本",
    "解析湖北物理类行数",
    "解析湖北物理类计划数合计",
    "可核字段覆盖数量",
    "可核字段覆盖集合",
    "缺失关键字段集合",
    "是否具备计划数线索",
    "是否具备学费线索",
    "是否具备选科线索",
    "是否具备组内代码线索",
    "是否具备专业组线索",
    "是否可进入候选diff",
    "候选diff前置缺口",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源状态",
    "字段事实写回状态",
    "下一步自动动作",
    "最小人工核验动作",
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

SCHOOL_NAMES_BY_CODE = {
    "A195": "兰州大学",
    "C125": "武汉轻工大学",
    "C133": "湖北师范大学",
    "K465": "西安建筑科技大学",
    "A032": "北京语言大学",
    "F099": "天津外国语大学",
    "F305": "忻州师范学院",
    "K487": "西安航空学院",
    "C108": "江汉大学",
    "K753": "喀什大学",
    "H450": "山东工商学院",
    "H001": "杭州电子科技大学",
}

KEY_FIELDS = ["专业名称", "计划数", "学费", "选科", "专业代号", "专业组"]
PUBLIC_FIELD_LABELS = {
    "专业名称": "专业名线索",
    "计划数": "计划数",
    "学费": "学费",
    "选科": "选科",
    "专业代号": "组内代码线索",
    "专业组": "校内组线索",
}


def clean(value):
    return "" if value is None else str(value).replace("\r", " ").replace("\n", " ").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: clean(row.get(field, "")) for field in fields} for row in rows])


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(path):
    return str(path.relative_to(ROOT))


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


def load_match_module():
    spec = importlib.util.spec_from_file_location("official_evidence_match", MATCH_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_next20_json(path, school_name):
    obj = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for item in obj.get("data", []) if isinstance(obj, dict) else []:
        rows.append({
            "学校名称": school_name,
            "官方来源文件": source_path(path),
            "证据类型": "official_zhinengdayi_json",
            "年份": str(item.get("year", "")),
            "省份": str(item.get("cityName", "")),
            "科类": "物理类",
            "批次": str(item.get("batch", "")),
            "类别": str(item.get("enrollType", "")),
            "专业组": "",
            "专业代号": "",
            "专业代码": "",
            "专业名称": str(item.get("majorName", "")),
            "专业备注": "",
            "计划数": str(item.get("enrollNum", "")),
            "学制": "",
            "学费": "",
            "校区": "",
            "选科": "",
            "可核字段": "专业名称；湖北计划数；年份；省份；批次；类别",
            "局限性": "智能答疑JSON未给湖北院校专业组代码、专业代号、学费和选科，仍需第19期原页和湖北官方侧核验。",
            "年份证据说明": "智能答疑JSON返回 year=2026 且 cityName=湖北。",
        })
    return rows


def parse_live_pdf_csv(path, school_name):
    rows = []
    for item in read_csv(path):
        rows.append({
            "学校名称": school_name,
            "官方来源文件": source_path(path),
            "证据类型": "official_live_pdf_extracted_csv",
            "年份": "2026",
            "省份": "湖北",
            "科类": clean(item.get("科类")) or "物理类",
            "批次": "",
            "类别": "",
            "专业组": "",
            "专业代号": clean(item.get("专业代号")),
            "专业代码": "",
            "专业名称": clean(item.get("专业名称")),
            "专业备注": "",
            "计划数": clean(item.get("湖北计划数")),
            "学制": "",
            "学费": "",
            "校区": "",
            "选科": "",
            "可核字段": "专业名称；专业代号；湖北计划数；科类",
            "局限性": "live PDF抽取源未给湖北院校专业组代码、学费和选科，需第19期原页和湖北官方侧核验。",
            "年份证据说明": "高校官网2026本科招生计划PDF经抽取留存。",
        })
    return rows


def parse_source(match_module, path, code):
    school_name = SCHOOL_NAMES_BY_CODE[code]
    if path.suffix == ".json":
        if "issue19-next20-official-sources" in str(path):
            return parse_next20_json(path, school_name)
        return match_module.parse_json_plan(path, school_name)
    if path.suffix == ".csv":
        if "issue19-school-source-live-20260629" in str(path):
            return parse_live_pdf_csv(path, school_name)
        return match_module.parse_extracted_pdf_csv(path, school_name)
    if path.suffix == ".xlsx":
        return match_module.parse_xlsx_plan(path, school_name)
    return []


def field_coverage(rows):
    covered = []
    for field in KEY_FIELDS:
        if any(clean(row.get(field)) for row in rows):
            covered.append(field)
    missing = [field for field in KEY_FIELDS if field not in covered]
    return covered, missing


def public_field_list(fields):
    return "；".join(PUBLIC_FIELD_LABELS[field] for field in fields)


def parser_family(source_type):
    if source_type == "API/JSON；章程HTML":
        return "JSON计划源解析；章程规则旁路"
    if source_type == "API/JSON":
        return "JSON计划源解析"
    if source_type == "PDF抽取CSV":
        return "PDF_CSV抽取源解析"
    if source_type == "XLSX":
        return "XLSX附件解析"
    return "来源类型待判定"


def diff_ready(rows, missing_fields):
    if not rows:
        return "false", "未解析出湖北物理类计划行"
    if "专业名称" in missing_fields or "计划数" in missing_fields:
        return "false", "缺专业名称或计划数线索"
    return "true", "可生成候选diff提示；仍需PDF原页和湖北官方侧闭环"


def build_rows():
    match_module = load_match_module()
    adapter_rows = read_csv(ADAPTER_WORKBENCH)
    ingestion_by_id = {
        row["高校源结构化接入候选ID"]: row for row in read_csv(INGESTION)
    }
    rows = []
    for adapter in adapter_rows:
        source = ingestion_by_id[adapter["高校源结构化接入候选ID"]]
        code = adapter["院校代码"]
        evidence_files = [
            clean(part)
            for part in source.get("本地公开证据文件集合", "").split("；")
            if clean(part)
        ]
        parsed_rows = []
        parseable_count = 0
        non_plan_count = 0
        for rel_path in evidence_files:
            path = ROOT / rel_path
            if not path.exists():
                continue
            if rel_path.startswith("data/working/") or "crosscheck" in path.name.lower():
                non_plan_count += 1
                continue
            if "charter" in path.name.lower() or path.suffix.lower() in {".html", ".htm"} and "章程" in adapter.get("来源文件类型", ""):
                non_plan_count += 1
                continue
            parsed = parse_source(match_module, path, code)
            if parsed:
                parseable_count += 1
                parsed_rows.extend(parsed)
        covered, missing = field_coverage(parsed_rows)
        plan_sum = sum(as_int(row.get("计划数")) for row in parsed_rows)
        can_diff, gap = diff_ready(parsed_rows, missing)
        row = {
            "高校源Adapter解析审计ID": stable_id("SSPARSE", [SOURCE_PDF_SHA256, code, adapter["高校源AdapterDiff执行ID"]]),
            "来源AdapterDiff执行工作台": source_path(ADAPTER_WORKBENCH),
            "来源结构化接入候选账本": source_path(INGESTION),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校官网结构化源Adapter解析审计",
            "任务粒度": "院校代码×证据集合×normalized解析状态",
            **false_gate_values(),
            "审计序号": adapter["执行序号"],
            "院校代码": code,
            "学校键SHA16": adapter["学校键SHA16"],
            "高校源AdapterDiff执行ID": adapter["高校源AdapterDiff执行ID"],
            "高校源结构化接入候选ID": adapter["高校源结构化接入候选ID"],
            "接入批次": adapter["接入批次"],
            "来源文件类型": adapter["来源文件类型"],
            "Parser状态桶": adapter["Parser状态桶"],
            "Normalized桥接状态": adapter["Normalized桥接状态"],
            "Diff执行桶": adapter["Diff执行桶"],
            "公开证据集合SHA16": adapter["公开证据集合SHA16"],
            "证据文件数量": len(evidence_files),
            "可解析证据文件数量": parseable_count,
            "不可解析证据文件数量": len(evidence_files) - parseable_count - non_plan_count,
            "非计划规则侧证数量": non_plan_count,
            "解析器族": parser_family(adapter["来源文件类型"]),
            "解析结果状态": "parsed_has_rows" if parsed_rows else "parsed_no_rows",
            "NormalizedSchema版本": "school_source_normalized_v1_audit_only",
            "解析湖北物理类行数": len(parsed_rows),
            "解析湖北物理类计划数合计": plan_sum,
            "可核字段覆盖数量": len(covered),
            "可核字段覆盖集合": public_field_list(covered),
            "缺失关键字段集合": public_field_list(missing),
            "是否具备计划数线索": "true" if "计划数" in covered else "false",
            "是否具备学费线索": "true" if "学费" in covered else "false",
            "是否具备选科线索": "true" if "选科" in covered else "false",
            "是否具备组内代码线索": "true" if "专业代号" in covered else "false",
            "是否具备专业组线索": "true" if "专业组" in covered else "false",
            "是否可进入候选diff": can_diff,
            "候选diff前置缺口": gap,
            "PDF原页核页状态": "pending_pdf_page_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网源状态": "for_double_check_only_not_official_plan_replacement",
            "字段事实写回状态": "blocked_until_pdf_hubei_school_three_way_closure",
            "下一步自动动作": "生成normalized私有明细和候选diff提示；公开层只保留计数和SHA。",
            "最小人工核验动作": "diff命中项仍需回看PDF原页，并核湖北官方侧或省招办计划。",
            "公开安全策略": "not_final；parse_audit_only；no_school_names；no_major_names；no_field_values；no_evidence_paths；no_private_paths；no_login_state；no_recommendation",
        }
        rows.append(row)
    rows.sort(key=lambda row: as_int(row["审计序号"]))
    return rows, adapter_rows


def counter_dict(rows, field):
    return dict(sorted(Counter(row[field] for row in rows).items()))


def build_summary(rows, adapter_rows):
    return {
        "status": "issue19_school_source_adapter_parse_audit_v1_not_final",
        "generated_by": "build_issue19_school_source_adapter_parse_audit_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_adapter_workbench": source_path(ADAPTER_WORKBENCH),
        "source_structured_ingestion": source_path(INGESTION),
        "output_table": source_path(OUTPUT),
        "row_count": len(rows),
        "unique_school_count": len({row["院校代码"] for row in rows}),
        "source_adapter_row_count": len(adapter_rows),
        "source_type_counts": counter_dict(rows, "来源文件类型"),
        "parser_family_counts": counter_dict(rows, "解析器族"),
        "parse_result_counts": counter_dict(rows, "解析结果状态"),
        "diff_ready_counts": counter_dict(rows, "是否可进入候选diff"),
        "plan_hint_count": sum(1 for row in rows if row["是否具备计划数线索"] == "true"),
        "fee_hint_count": sum(1 for row in rows if row["是否具备学费线索"] == "true"),
        "subject_hint_count": sum(1 for row in rows if row["是否具备选科线索"] == "true"),
        "major_code_hint_count": sum(1 for row in rows if row["是否具备组内代码线索"] == "true"),
        "group_hint_count": sum(1 for row in rows if row["是否具备专业组线索"] == "true"),
        "evidence_file_count": sum(as_int(row["证据文件数量"]) for row in rows),
        "parseable_evidence_file_count": sum(as_int(row["可解析证据文件数量"]) for row in rows),
        "non_plan_rule_sidecar_count": sum(as_int(row["非计划规则侧证数量"]) for row in rows),
        "parsed_hubei_physics_row_count": sum(as_int(row["解析湖北物理类行数"]) for row in rows),
        "parsed_hubei_physics_plan_sum": sum(as_int(row["解析湖北物理类计划数合计"]) for row in rows),
        "pdf_pending_count": len(rows),
        "hubei_official_pending_count": len(rows),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "final_available_count": 0,
        "public_boundary": "本表只审计高校源adapter解析能力和字段覆盖，不保存学校名、专业名、字段明细或证据路径，不替代第19期PDF原页和湖北官方计划。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"adapter parse audit contains forbidden public tokens: {hits[:10]}")


def main():
    rows, adapter_rows = build_rows()
    summary = build_summary(rows, adapter_rows)
    assert_public_safe(rows, summary)
    write_csv(OUTPUT, rows, FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")


if __name__ == "__main__":
    main()
