#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

IMMEDIATE_PACKET = ROOT / "data/working/issue19-field-fact-p0-immediate-review-packet.csv"
CROP_INDEX = ROOT / "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv"
THREE_WAY_LEDGER = ROOT / "data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv"
PRIVATE_CROP_OCR_JSONL = ROOT / "private/ocr-runs/p0-immediate-crops-vision-ocr/ocr.jsonl"
PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-p0-immediate-crop-ocr-audit"
PRIVATE_OUTPUT = PRIVATE_OUTPUT_DIR / "crop-ocr-readings-private.csv"

OUTPUT = ROOT / "data/working/issue19-p0-immediate-crop-ocr-public-audit.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-p0-immediate-crop-ocr-public-audit-summary.json"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_p0_immediate_crop_ocr_public_audit"
PRIVATE_OCR_RUN_EVIDENCE_ID = "CROPOCRRUN-p0-immediate-vision-ocr"


FIELDS = [
    "P0即时裁图OCR公开审计ID",
    "来源P0即时三方闭环公开账本",
    "来源P0字段即时复核包",
    "来源P0裁图证据索引",
    "来源私有裁图OCR运行",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动回填候选",
    "是否允许写回字段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "裁图OCR公开审计总序",
    "闭环公开账本总序",
    "即时复核总序",
    "执行总序",
    "执行批次",
    "即时复核阶段",
    "语义多源优先桶",
    "字段名",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "来源页码",
    "版面列",
    "P0字段即时复核任务ID",
    "P0即时三方闭环公开账本ID",
    "P0即时复核裁图证据索引ID",
    "裁图证据编号",
    "裁图文件SHA256",
    "裁图规格SHA256",
    "裁图bbox归一化",
    "裁图bbox像素",
    "私有裁图OCR运行证据编号",
    "私有裁图OCR结果SHA256",
    "裁图OCR行数",
    "裁图OCR平均置信度区间",
    "裁图OCR候选状态",
    "裁图OCR候选置信等级",
    "裁图OCR目标行定位状态",
    "裁图OCR与机器候选关系",
    "裁图OCR与高校辅证关系",
    "裁图OCR三方辅助桶",
    "是否有机器规范候选",
    "是否有高校字段线索",
    "是否裁图OCR有可比候选",
    "是否裁图OCR与机器候选一致",
    "是否裁图OCR与机器候选冲突",
    "是否裁图OCR与高校辅证一致",
    "是否裁图OCR与高校辅证冲突",
    "是否建议人工优先核页",
    "是否需要双人复核",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_FIELDS = [
    *FIELDS,
    "裁图OCR候选字段值",
    "裁图OCR候选规范值",
    "裁图OCR候选行文本",
    "裁图OCR候选行序号",
    "裁图OCR候选x中心",
    "裁图OCR候选y中心",
    "裁图OCR候选置信度",
    "裁图OCR候选距目标行y",
    "裁图OCR全部候选短摘",
    "机器候选规范值",
    "高校官网字段规范值",
    "私有OCR图片本地路径",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_digits(value):
    return "".join(re.findall(r"\d+", str(value or "")))


def normalize_subject(value):
    text = re.sub(r"[\s\[\]【】（）()「」『』；:：、,，。·/|\\-]", "", str(value or ""))
    if "不限" in text:
        return "不限"
    if "化学" in text:
        return "化学"
    if "生物" in text:
        return "生物"
    if "地理" in text:
        return "地理"
    if "政治" in text or "思想政治" in text:
        return "政治"
    return ""


def as_float(value, default=None):
    try:
        return float(str(value or "").strip())
    except ValueError:
        return default


def as_int(value, default=0):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return default


def parse_y_range(value):
    match = re.search(r"y_bottom_origin=([0-9.]+)-([0-9.]+)", value or "")
    if not match:
        return None
    low = float(match.group(1))
    high = float(match.group(2))
    if high <= low:
        return None
    return low, high


def parse_float_values(value):
    values = []
    for part in re.split(r"[;,，；| ]+", str(value or "")):
        number = as_float(part)
        if number is not None:
            values.append(number)
    return values


def map_original_y_to_crop_y(original_y, crop_y_range):
    if original_y is None or not crop_y_range:
        return None
    low, high = crop_y_range
    mapped = (original_y - low) / (high - low)
    return max(0.0, min(1.0, mapped))


def load_crop_ocr(path):
    result = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            image = Path(item.get("image", ""))
            result[image.stem] = item
    return result


def confidence_bucket(value):
    if value is None:
        return "C0-无置信度"
    if value >= 0.85:
        return "C4-高置信"
    if value >= 0.75:
        return "C3-中高置信"
    if value >= 0.65:
        return "C2-中置信"
    return "C1-低置信"


def target_y_from_row(row, crop_row):
    candidate_ys = parse_float_values(row.get("候选证据y集合", ""))
    if candidate_ys:
        original_y = sum(candidate_ys) / len(candidate_ys)
    else:
        upper = as_float(row.get("OCR窗口y上界"))
        lower = as_float(row.get("OCR窗口y下界"))
        if upper is not None and lower is not None:
            original_y = (upper + lower) / 2
        else:
            original_y = None
    return map_original_y_to_crop_y(original_y, parse_y_range(crop_row.get("裁图bbox归一化", "")))


def line_center(line):
    box = line.get("boundingBox") or {}
    x = as_float(box.get("x"), 0.0) + as_float(box.get("width"), 0.0) / 2
    y = as_float(box.get("y"), 0.0) + as_float(box.get("height"), 0.0) / 2
    return x, y


def ocr_line_candidates(ocr_result, field_name):
    candidates = []
    for index, line in enumerate(ocr_result.get("lines", []), start=1):
        text = str(line.get("text", "")).strip()
        x, y = line_center(line)
        confidence = as_float(line.get("confidence"), 0.0)
        value = ""
        if field_name == "专业计划数":
            digits = normalize_digits(text)
            if digits and text.replace(" ", "").isdigit() and 1 <= len(digits) <= 3 and 0.72 <= x <= 0.88:
                value = digits
        elif field_name == "学费":
            digits = normalize_digits(text)
            if digits and text.replace(" ", "").isdigit() and 4 <= len(digits) <= 6 and 0.82 <= x <= 0.98:
                value = digits
        elif field_name == "再选科目":
            subject = normalize_subject(text)
            if subject and 0.58 <= x <= 0.82:
                value = subject
        if not value:
            continue
        candidates.append({
            "value": value,
            "text": text,
            "line_index": str(index),
            "x": f"{x:.6f}",
            "y": f"{y:.6f}",
            "confidence": f"{confidence:.4f}",
            "confidence_float": confidence,
        })
    return candidates


def choose_candidate(candidates, target_y):
    if not candidates:
        return None, "O0-未识别可比候选", "low", "target_y_unmatched"
    if target_y is None:
        return None, "O1-有候选但缺目标行定位", "low", "target_y_missing"
    ranked = sorted(
        candidates,
        key=lambda item: (abs(float(item["y"]) - target_y), -item["confidence_float"]),
    )
    best = ranked[0]
    distance = abs(float(best["y"]) - target_y)
    close = [item for item in ranked if abs(float(item["y"]) - target_y) <= max(0.035, distance + 0.005)]
    close_values = sorted({item["value"] for item in close})
    if len(close_values) > 1:
        return best, "O3-目标行附近多值候选冲突", "low", f"target_y={target_y:.6f};distance={distance:.6f}"
    if distance <= 0.045:
        confidence = "high" if best["confidence_float"] >= 0.75 else "medium"
        return best, "O4-目标行单一候选", confidence, f"target_y={target_y:.6f};distance={distance:.6f}"
    if distance <= 0.095:
        return best, "O2-候选距目标行偏远需人工确认", "low", f"target_y={target_y:.6f};distance={distance:.6f}"
    return None, "O1-有候选但未能贴合目标行", "low", f"target_y={target_y:.6f};nearest_distance={distance:.6f}"


def compare_values(candidate_value, reference_value, no_reference_label):
    if not reference_value:
        return no_reference_label
    if not candidate_value:
        return "crop_ocr_no_comparable_candidate"
    if candidate_value == reference_value:
        return "crop_ocr_matches_reference"
    return "crop_ocr_conflicts_reference"


def helper_bucket(machine_relation, school_relation, candidate_status):
    if "冲突" in candidate_status or machine_relation.endswith("conflicts_reference") or school_relation.endswith("conflicts_reference"):
        return "A0-裁图OCR提示冲突优先人工核页"
    if candidate_status == "O4-目标行单一候选" and (
        machine_relation.endswith("matches_reference") or school_relation.endswith("matches_reference")
    ):
        return "A1-裁图OCR与既有线索一致但仍待三方核验"
    if candidate_status.startswith("O0") or candidate_status.startswith("O1"):
        return "A3-裁图OCR未能稳定补读需人工看图"
    return "A2-裁图OCR有候选但需人工确认"


def brief_candidates(candidates):
    parts = []
    for item in candidates[:12]:
        parts.append(
            f"{item['value']}@line{item['line_index']}:x{item['x']}:y{item['y']}:c{item['confidence']}"
        )
    return "；".join(parts)


def build_rows():
    immediate_by_id = {row["P0字段即时复核任务ID"]: row for row in read_csv(IMMEDIATE_PACKET)}
    crop_by_id = {row["来源P0字段即时复核任务ID"]: row for row in read_csv(CROP_INDEX)}
    three_way_rows = read_csv(THREE_WAY_LEDGER)
    ocr_by_stem = load_crop_ocr(PRIVATE_CROP_OCR_JSONL)
    ocr_jsonl_sha = sha256(PRIVATE_CROP_OCR_JSONL)

    public_rows = []
    private_rows = []
    for index, closure in enumerate(three_way_rows, start=1):
        task_id = closure["P0字段即时复核任务ID"]
        immediate = immediate_by_id[task_id]
        crop = crop_by_id[task_id]
        crop_evidence_id = crop["裁图证据编号"]
        ocr_result = ocr_by_stem.get(crop_evidence_id, {})
        field_name = closure["字段名"]
        candidates = ocr_line_candidates(ocr_result, field_name)
        target_y = target_y_from_row(immediate, crop)
        selected, candidate_status, candidate_confidence, target_status = choose_candidate(candidates, target_y)
        candidate_value = selected["value"] if selected else ""
        machine_value = immediate.get("机器候选规范值", "")
        school_value = immediate.get("高校官网字段规范值", "")
        machine_relation = compare_values(candidate_value, machine_value, "no_machine_reference")
        school_relation = compare_values(candidate_value, school_value, "no_school_reference")
        bucket = helper_bucket(machine_relation, school_relation, candidate_status)
        public_row = {
            "P0即时裁图OCR公开审计ID": stable_id("P0CROPOCRAUDIT", [task_id, crop_evidence_id, field_name]),
            "来源P0即时三方闭环公开账本": "data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv",
            "来源P0字段即时复核包": "data/working/issue19-field-fact-p0-immediate-review-packet.csv",
            "来源P0裁图证据索引": "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv",
            "来源私有裁图OCR运行": "private_crop_ocr_run_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0字段×裁图OCR辅助审计",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "裁图OCR公开审计总序": str(index),
            "闭环公开账本总序": closure["闭环公开账本总序"],
            "即时复核总序": closure["即时复核总序"],
            "执行总序": closure["执行总序"],
            "执行批次": closure["执行批次"],
            "即时复核阶段": closure["即时复核阶段"],
            "语义多源优先桶": closure["语义多源优先桶"],
            "字段名": field_name,
            "专业行ID": closure["专业行ID"],
            "专业组出现ID": closure["专业组出现ID"],
            "院校代码": closure["院校代码"],
            "来源页码": closure["来源页码"],
            "版面列": closure["版面列"],
            "P0字段即时复核任务ID": task_id,
            "P0即时三方闭环公开账本ID": closure["P0即时三方闭环公开账本ID"],
            "P0即时复核裁图证据索引ID": crop["P0即时复核裁图证据索引ID"],
            "裁图证据编号": crop_evidence_id,
            "裁图文件SHA256": crop["裁图文件SHA256"],
            "裁图规格SHA256": crop["裁图规格SHA256"],
            "裁图bbox归一化": crop["裁图bbox归一化"],
            "裁图bbox像素": crop["裁图bbox像素"],
            "私有裁图OCR运行证据编号": PRIVATE_OCR_RUN_EVIDENCE_ID,
            "私有裁图OCR结果SHA256": ocr_jsonl_sha,
            "裁图OCR行数": str(ocr_result.get("lineCount", 0)),
            "裁图OCR平均置信度区间": confidence_bucket(ocr_result.get("averageConfidence")),
            "裁图OCR候选状态": candidate_status,
            "裁图OCR候选置信等级": candidate_confidence,
            "裁图OCR目标行定位状态": target_status,
            "裁图OCR与机器候选关系": machine_relation,
            "裁图OCR与高校辅证关系": school_relation,
            "裁图OCR三方辅助桶": bucket,
            "是否有机器规范候选": "true" if machine_value else "false",
            "是否有高校字段线索": "true" if school_value else "false",
            "是否裁图OCR有可比候选": "true" if candidate_value else "false",
            "是否裁图OCR与机器候选一致": "true" if machine_relation == "crop_ocr_matches_reference" else "false",
            "是否裁图OCR与机器候选冲突": "true" if machine_relation == "crop_ocr_conflicts_reference" else "false",
            "是否裁图OCR与高校辅证一致": "true" if school_relation == "crop_ocr_matches_reference" else "false",
            "是否裁图OCR与高校辅证冲突": "true" if school_relation == "crop_ocr_conflicts_reference" else "false",
            "是否建议人工优先核页": "true" if bucket.startswith("A0") or closure["是否需要双人复核"] == "true" else "false",
            "是否需要双人复核": closure["是否需要双人复核"],
            "PDF原页核页状态": closure["PDF原页核页状态"],
            "湖北官方系统或省招办计划核验状态": closure["湖北官方系统或省招办计划核验状态"],
            "高校官网或招生章程辅证状态": closure["高校官网或招生章程辅证状态"],
            "三方字段一致性状态": closure["三方字段一致性状态"],
            "字段事实写回状态": closure["字段事实写回状态"],
            "公开安全策略": "公开审计只保存裁图OCR状态、关系、SHA和门禁；具体识别文本、候选读数和图片路径只在本地私有文件。",
            "下一步": "按裁图OCR辅助桶排序人工回看裁图和PDF原页；再核湖北官方系统或省招办计划，不能自动写回字段。",
        }
        private_row = {
            **public_row,
            "裁图OCR候选字段值": candidate_value,
            "裁图OCR候选规范值": candidate_value,
            "裁图OCR候选行文本": selected["text"] if selected else "",
            "裁图OCR候选行序号": selected["line_index"] if selected else "",
            "裁图OCR候选x中心": selected["x"] if selected else "",
            "裁图OCR候选y中心": selected["y"] if selected else "",
            "裁图OCR候选置信度": selected["confidence"] if selected else "",
            "裁图OCR候选距目标行y": target_status,
            "裁图OCR全部候选短摘": brief_candidates(candidates),
            "机器候选规范值": machine_value,
            "高校官网字段规范值": school_value,
            "私有OCR图片本地路径": ocr_result.get("image", ""),
        }
        public_rows.append(public_row)
        private_rows.append(private_row)
    return public_rows, private_rows


def write_summary(rows):
    field_counts = Counter(row["字段名"] for row in rows)
    status_counts = Counter(row["裁图OCR候选状态"] for row in rows)
    bucket_counts = Counter(row["裁图OCR三方辅助桶"] for row in rows)
    machine_relation_counts = Counter(row["裁图OCR与机器候选关系"] for row in rows)
    school_relation_counts = Counter(row["裁图OCR与高校辅证关系"] for row in rows)
    confidence_counts = Counter(row["裁图OCR平均置信度区间"] for row in rows)
    summary = {
        "status": "issue19_p0_immediate_crop_ocr_public_audit_not_final",
        "generated_by": "build_issue19_p0_immediate_crop_ocr_audit.py",
        "source_three_way_ledger": "data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv",
        "source_immediate_packet": "data/working/issue19-field-fact-p0-immediate-review-packet.csv",
        "source_crop_evidence_index": "data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv",
        "source_private_crop_ocr_run": "private_crop_ocr_run_not_public",
        "output_table": "data/working/issue19-p0-immediate-crop-ocr-public-audit.csv",
        "row_grain": "逐专业招生明细×P0字段×裁图OCR辅助审计",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(rows),
        "private_reading_candidate_file_generated": True,
        "unique_public_audit_id_count": len({row["P0即时裁图OCR公开审计ID"] for row in rows}),
        "unique_immediate_task_id_count": len({row["P0字段即时复核任务ID"] for row in rows}),
        "unique_three_way_ledger_id_count": len({row["P0即时三方闭环公开账本ID"] for row in rows}),
        "unique_crop_index_id_count": len({row["P0即时复核裁图证据索引ID"] for row in rows}),
        "unique_crop_evidence_id_count": len({row["裁图证据编号"] for row in rows}),
        "unique_major_field_pair_count": len({(row["专业行ID"], row["字段名"]) for row in rows}),
        "field_counts": dict(field_counts),
        "ocr_line_zero_count": sum(as_int(row["裁图OCR行数"]) == 0 for row in rows),
        "ocr_candidate_available_count": sum(row["是否裁图OCR有可比候选"] == "true" for row in rows),
        "ocr_candidate_unavailable_count": sum(row["是否裁图OCR有可比候选"] == "false" for row in rows),
        "ocr_machine_agree_count": sum(row["是否裁图OCR与机器候选一致"] == "true" for row in rows),
        "ocr_machine_conflict_count": sum(row["是否裁图OCR与机器候选冲突"] == "true" for row in rows),
        "ocr_school_agree_count": sum(row["是否裁图OCR与高校辅证一致"] == "true" for row in rows),
        "ocr_school_conflict_count": sum(row["是否裁图OCR与高校辅证冲突"] == "true" for row in rows),
        "manual_priority_count": sum(row["是否建议人工优先核页"] == "true" for row in rows),
        "double_review_required_count": sum(row["是否需要双人复核"] == "true" for row in rows),
        "candidate_status_counts": dict(status_counts),
        "helper_bucket_counts": dict(bucket_counts),
        "machine_relation_counts": dict(machine_relation_counts),
        "school_relation_counts": dict(school_relation_counts),
        "ocr_confidence_bucket_counts": dict(confidence_counts),
        "pdf_manual_review_pending_count": sum(row["PDF原页核页状态"] == "pending_pdf_manual_review" for row in rows),
        "hubei_official_review_pending_count": sum(
            row["湖北官方系统或省招办计划核验状态"] == "pending_hubei_official_plan_review" for row in rows
        ),
        "three_way_closure_pending_count": sum(row["三方字段一致性状态"] == "pending_three_way_closure" for row in rows),
        "field_writeback_ready_count": sum(
            row["字段事实写回状态"] != "blocked_until_pdf_hubei_school_three_way_closure" for row in rows
        ),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段"] == "true" for row in rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in rows),
        "public_safety_note": "公开审计只保存裁图OCR状态、关系、SHA和门禁；不保存具体识别文本、候选读数、图片路径、院校名、专业名、专业代号或专业组代码。",
    }
    write_json(SUMMARY_OUTPUT, summary)


def main():
    if not PRIVATE_CROP_OCR_JSONL.exists():
        raise SystemExit(f"缺少私有裁图 OCR 结果：{PRIVATE_CROP_OCR_JSONL}")
    public_rows, private_rows = build_rows()
    write_csv(OUTPUT, public_rows, FIELDS)
    write_csv(PRIVATE_OUTPUT, private_rows, PRIVATE_FIELDS)
    write_summary(public_rows)
    print(f"写出P0即时裁图OCR公开审计：{OUTPUT.relative_to(ROOT)}，{len(public_rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"本地私有裁图OCR读数候选已生成：{PRIVATE_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
