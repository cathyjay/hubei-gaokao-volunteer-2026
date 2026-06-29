#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "data/working"

CANDIDATE_DIFF_PUBLIC = WORKING / "issue19-school-source-adapter-candidate-diff-v1-public-ledger.csv"
CANDIDATE_DIFF_SUMMARY = WORKING / "issue19-school-source-adapter-candidate-diff-v1-summary.json"
CANDIDATE_DIFF_PRIVATE_DETAIL = (
    ROOT
    / "private/review-assets/issue19-school-source-adapter-candidate-diff-v1"
    / "school-source-adapter-candidate-diff-private-detail.csv"
)

PUBLIC_OUTPUT = WORKING / "issue19-school-source-adapter-d0-d1-manual-review-packets-v1-public-ledger.csv"
SUMMARY_OUTPUT = WORKING / "issue19-school-source-adapter-d0-d1-manual-review-packets-v1-summary.json"
PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-school-source-adapter-d0-d1-manual-review-packets-v1"
PRIVATE_REVIEW_ITEMS = PRIVATE_OUTPUT_DIR / "school-source-adapter-d0-d1-private-review-items.csv"
PRIVATE_INDEX = PRIVATE_OUTPUT_DIR / "school-source-adapter-d0-d1-private-index.csv"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_school_source_adapter_d0_d1_manual_review_packets_v1"
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
    "高校源AdapterD0D1人工核验包ID",
    "来源Adapter候选diff公开账本",
    "来源Adapter候选diff摘要",
    "来源期号",
    "来源PDF_SHA256",
    "生成日期",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    *FALSE_FIELDS,
    "执行序号",
    "院校代码",
    "学校键SHA16",
    "高校源Adapter候选diff公开ID",
    "高校源Adapter解析审计ID",
    "Adapter候选diff优先级",
    "私有diff明细行数",
    "计划数冲突候选数",
    "OCR计划数可补候选数",
    "疑似匹配候选数",
    "计划数一致抽检候选数",
    "本包私有核验项数",
    "私有核验项优先级分布",
    "最小人工核验动作",
    "本地未公开核验项CSV证据编号",
    "本地未公开核验项CSV_SHA256",
    "本地未公开核验项行数",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_REVIEW_FIELDS = [
    "高校源AdapterD0D1人工核验项ID",
    "高校源AdapterD0D1人工核验包ID",
    "高校源Adapter候选diff公开ID",
    "高校源Adapter候选diff私有明细ID",
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
    "人工核验优先级",
    "人工核验原因",
    "建议核验动作",
    *FALSE_FIELDS,
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网结构化源状态",
    "字段事实写回状态",
    "复核备注",
]

PRIVATE_INDEX_FIELDS = [
    "高校源AdapterD0D1人工核验包ID",
    "高校源Adapter候选diff公开ID",
    "院校代码",
    "院校名称OCR",
    "私有核验项数",
    "计划数冲突项数",
    "OCR计划数可补项数",
    "疑似匹配项数",
    "计划数一致抽检项数",
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
    "专业名称及备注OCR",
    "专业代号",
    "院校专业组代码",
    "官方来源文件",
    "最佳高校源专业名称",
    "最佳高校源计划数",
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


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def priority_for(detail, match_sample_rank):
    plan_status = detail.get("本轮计划数核验状态", "")
    match_status = detail.get("本轮高校源匹配状态", "")
    if plan_status == "mismatch":
        return "R0-计划数冲突优先核PDF原页", "高校源与OCR计划数冲突"
    if plan_status == "ocr_plan_missing_official_available":
        return "R1-OCR计划数缺失但高校源可补", "OCR计划数字段缺失，高校源有计划数线索"
    if match_status == "possible_match":
        return "R2-疑似匹配专业名人工确认", "专业名疑似匹配，需人工确认是否同一专业"
    if plan_status == "match" and match_sample_rank <= 2:
        return "R3-计划数一致候选抽检", "计划数一致候选，每包抽检最多2条"
    return "", ""


def action_for(priority):
    if priority.startswith("R0"):
        return "回看第19期PDF原页，核同一专业行计划数；再核湖北官方侧。"
    if priority.startswith("R1"):
        return "回看第19期PDF原页补读计划数；高校源只作提示。"
    if priority.startswith("R2"):
        return "人工确认专业名、限定词和所属专业组边界。"
    if priority.startswith("R3"):
        return "抽检PDF原页与湖北官方侧，确认一致口径可靠。"
    return ""


def build_rows():
    public_rows = read_csv(CANDIDATE_DIFF_PUBLIC)
    private_details = read_csv(CANDIDATE_DIFF_PRIVATE_DETAIL)
    details_by_public = defaultdict(list)
    for detail in private_details:
        details_by_public[detail["高校源Adapter候选diff公开ID"]].append(detail)

    private_review_rows = []
    private_index_rows = []
    packet_rows = []
    for public in public_rows:
        public_id = public["高校源Adapter候选diff公开ID"]
        packet_id = stable_id("SSREVIEW", [SOURCE_PDF_SHA256, public_id, public["院校代码"]])
        details = details_by_public.get(public_id, [])
        match_sample_rank = 0
        selected = []
        for detail in details:
            if detail.get("本轮计划数核验状态") == "match":
                match_sample_rank += 1
            priority, reason = priority_for(detail, match_sample_rank)
            if not priority:
                continue
            row = {
                "高校源AdapterD0D1人工核验项ID": stable_id(
                    "SSREVIEWITEM",
                    [packet_id, detail["高校源Adapter候选diff私有明细ID"], priority],
                ),
                "高校源AdapterD0D1人工核验包ID": packet_id,
                "人工核验优先级": priority,
                "人工核验原因": reason,
                "建议核验动作": action_for(priority),
                **detail,
            }
            private_review_rows.append(row)
            selected.append(row)

        priority_counts = Counter(row["人工核验优先级"] for row in selected)
        private_index_rows.append({
            "高校源AdapterD0D1人工核验包ID": packet_id,
            "高校源Adapter候选diff公开ID": public_id,
            "院校代码": public["院校代码"],
            "院校名称OCR": selected[0].get("院校名称OCR", "") if selected else "",
            "私有核验项数": len(selected),
            "计划数冲突项数": priority_counts.get("R0-计划数冲突优先核PDF原页", 0),
            "OCR计划数可补项数": priority_counts.get("R1-OCR计划数缺失但高校源可补", 0),
            "疑似匹配项数": priority_counts.get("R2-疑似匹配专业名人工确认", 0),
            "计划数一致抽检项数": priority_counts.get("R3-计划数一致候选抽检", 0),
        })
        packet_rows.append({
            "高校源AdapterD0D1人工核验包ID": packet_id,
            "来源Adapter候选diff公开账本": source_path(CANDIDATE_DIFF_PUBLIC),
            "来源Adapter候选diff摘要": source_path(CANDIDATE_DIFF_SUMMARY),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "生成日期": GENERATED_AT,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校源Adapter候选diff包×D0/D1最小人工核验项",
            "任务粒度": "公开包级计数；逐专业核验项仅保存在本地未公开CSV",
            **false_gate_values(),
            "执行序号": public["审计序号"],
            "院校代码": public["院校代码"],
            "学校键SHA16": public["学校键SHA16"],
            "高校源Adapter候选diff公开ID": public_id,
            "高校源Adapter解析审计ID": public["高校源Adapter解析审计ID"],
            "Adapter候选diff优先级": public["Adapter候选diff优先级"],
            "私有diff明细行数": public["私有diff明细数"],
            "计划数冲突候选数": public["计划数冲突候选数"],
            "OCR计划数可补候选数": public["官网可补OCR计划数候选数"],
            "疑似匹配候选数": public["疑似匹配明细数"],
            "计划数一致抽检候选数": priority_counts.get("R3-计划数一致候选抽检", 0),
            "本包私有核验项数": len(selected),
            "私有核验项优先级分布": "；".join(
                f"{key}:{value}" for key, value in sorted(priority_counts.items())
            ),
            "最小人工核验动作": "先核计划数冲突、OCR计划数缺失但高校源可补、疑似匹配；每包最多抽检2条计划数一致候选。",
            "本地未公开核验项CSV证据编号": "local_school_source_adapter_d0_d1_review_items_csv_not_public",
            "本地未公开核验项CSV_SHA256": "filled_after_write",
            "本地未公开核验项行数": len(selected),
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_plan_review",
            "高校官网结构化源状态": "structured_school_source_candidate_not_verified",
            "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
            "公开安全策略": "公开层只保留包级计数和SHA；学校名、专业名、OCR字段、高校源字段、人工备注不公开。",
            "下一步": "在私有核验项表中按R0/R1/R2/R3顺序回看PDF原页，并尽量核湖北官方侧；核验前不得写回字段事实。",
        })
    return packet_rows, private_review_rows, private_index_rows


def counter_dict(rows, field):
    return dict(sorted(Counter(row[field] for row in rows).items()))


def build_summary(packet_rows, private_review_rows, private_index_rows):
    priority_counts = Counter(row["人工核验优先级"] for row in private_review_rows)
    return {
        "status": "issue19_school_source_adapter_d0_d1_manual_review_packets_v1_not_final",
        "generated_by": "build_issue19_school_source_adapter_d0_d1_manual_review_packets_v1.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "generated_at": GENERATED_AT,
        "source_candidate_diff_public": source_path(CANDIDATE_DIFF_PUBLIC),
        "source_candidate_diff_summary": source_path(CANDIDATE_DIFF_SUMMARY),
        "output_public_table": source_path(PUBLIC_OUTPUT),
        "row_count": len(packet_rows),
        "unique_school_count": len({row["院校代码"] for row in packet_rows}),
        "private_review_item_count": len(private_review_rows),
        "private_index_row_count": len(private_index_rows),
        "candidate_priority_counts": counter_dict(packet_rows, "Adapter候选diff优先级"),
        "review_priority_counts": dict(sorted(priority_counts.items())),
        "plan_conflict_review_item_count": priority_counts.get("R0-计划数冲突优先核PDF原页", 0),
        "ocr_plan_missing_review_item_count": priority_counts.get("R1-OCR计划数缺失但高校源可补", 0),
        "possible_match_review_item_count": priority_counts.get("R2-疑似匹配专业名人工确认", 0),
        "plan_match_sample_review_item_count": priority_counts.get("R3-计划数一致候选抽检", 0),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "final_available_count": 0,
        "private_review_items_csv_sha256": "",
        "private_index_csv_sha256": "",
        "public_boundary": "公开表只保存包级计数、私有CSV SHA和非最终门禁；逐专业核验项留在Git忽略私有目录。",
    }


def assert_public_safe(rows, summary):
    text = json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in text]
    if hits:
        raise SystemExit(f"adapter d0 d1 manual packets contains forbidden public tokens: {hits[:10]}")


def main():
    packet_rows, private_review_rows, private_index_rows = build_rows()
    write_csv(PRIVATE_REVIEW_ITEMS, private_review_rows, PRIVATE_REVIEW_FIELDS)
    write_csv(PRIVATE_INDEX, private_index_rows, PRIVATE_INDEX_FIELDS)
    review_sha = sha256(PRIVATE_REVIEW_ITEMS)
    index_sha = sha256(PRIVATE_INDEX)
    for row in packet_rows:
        row["本地未公开核验项CSV_SHA256"] = review_sha
    summary = build_summary(packet_rows, private_review_rows, private_index_rows)
    summary["private_review_items_csv_sha256"] = review_sha
    summary["private_index_csv_sha256"] = index_sha
    assert_public_safe(packet_rows, summary)
    write_csv(PUBLIC_OUTPUT, packet_rows, PUBLIC_FIELDS)
    write_json(SUMMARY_OUTPUT, summary)
    print(f"wrote {source_path(PUBLIC_OUTPUT)}")
    print(f"wrote {source_path(SUMMARY_OUTPUT)}")
    print(f"private review items: {len(private_review_rows)}")


if __name__ == "__main__":
    main()
