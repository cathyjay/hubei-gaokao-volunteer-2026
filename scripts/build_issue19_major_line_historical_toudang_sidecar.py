#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BASELINE = ROOT / "candidate-baseline.json"
FOUNDATION_RELEASE = ROOT / "data/working/issue19-major-detail-foundation-release.csv"
TOUDANG_2023 = ROOT / "data/derived/hubei-2023-physics-toudang-parsed.csv"
TOUDANG_2024 = ROOT / "data/derived/hubei-2024-physics-toudang-parsed.csv"
TOUDANG_2025 = ROOT / "data/derived/hubei-2025-physics-toudang-parsed.csv"

OUTPUT = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar-summary.json"

DATA_STAGE = "issue19_major_line_historical_toudang_sidecar"
YEARS = [2023, 2024, 2025]


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


def sha256_text(value):
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return None


def sort_int(value):
    number = as_int(value)
    return number if number is not None else 0


def short_text(value, limit=100):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def join_unique(values):
    seen = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.append(text)
    return "；".join(seen)


def normalize_name(value):
    return re.sub(r"[\s（）()【】\\[\\]第组]", "", str(value or "")).lower()


def normalize_req(value):
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("个限", "不限")
    text = re.sub(r"^[招北厅]+", "", text)
    if "不限" in text:
        return "不限"
    subjects = []
    for raw, normalized in [
        ("化", "化学"),
        ("生", "生物"),
        ("政", "政治"),
        ("地", "地理"),
    ]:
        if raw in text and normalized not in subjects:
            subjects.append(normalized)
    if not subjects:
        return text
    joiner = "和" if "和" in text else ("或" if "或" in text else "、")
    return joiner.join(subjects)


def historical_sources():
    return {
        2023: TOUDANG_2023,
        2024: TOUDANG_2024,
        2025: TOUDANG_2025,
    }


def build_historical_indexes():
    indexes = {}
    duplicate_codes = {}
    source_counts = {}
    for year, path in historical_sources().items():
        rows = read_csv(path)
        by_code = defaultdict(list)
        for row in rows:
            by_code[row.get("code", "")].append(row)
        indexes[year] = by_code
        duplicate_codes[year] = sorted(code for code, items in by_code.items() if len(items) > 1)
        source_counts[year] = len(rows)
    return indexes, duplicate_codes, source_counts


def year_values(items, field):
    return join_unique(row.get(field, "") for row in items)


def year_scores(items):
    scores = []
    for row in items:
        score = as_int(row.get("score"))
        if score is not None:
            scores.append(score)
    return scores


def year_delta_text(year, scores, equivalent_scores):
    equivalent = equivalent_scores.get(str(year))
    if equivalent is None or not scores:
        return ""
    return "；".join(f"{score}-{equivalent}={score - equivalent:+d}" for score in sorted(set(scores)))


def row_hashes(items):
    return join_unique(sha256_text(row.get("row", "")) for row in items)


def score_range(all_scores):
    if not all_scores:
        return ""
    if min(all_scores) == max(all_scores):
        return str(min(all_scores))
    return f"{min(all_scores)}-{max(all_scores)}"


def stability_layer(hit_count, duplicate_flag, req_changed, current_duplicate):
    if hit_count == 0:
        return "H0-三年同代码未命中或组号变化"
    if duplicate_flag:
        return f"H{hit_count}-同代码命中但历史投档代码重复"
    if current_duplicate:
        return f"H{hit_count}-同代码命中但2026组代码重复出现"
    if req_changed:
        return f"H{hit_count}-同代码命中但再选要求变化"
    if hit_count == 3:
        return "H3-三年同代码命中"
    if hit_count == 2:
        return "H2-两年同代码命中"
    return "H1-一年同代码命中"


def build_rows():
    baseline = json.loads(BASELINE.read_text())
    equivalent_scores = {
        str(year): baseline["equivalent_scores"][str(year)]["score"]
        for year in YEARS
    }
    release_rows = read_csv(FOUNDATION_RELEASE)
    historical_indexes, duplicate_codes, source_counts = build_historical_indexes()

    group_occurrences = defaultdict(set)
    for row in release_rows:
        group_occurrences[row.get("院校专业组代码OCR规范化", "")].add(row.get("专业组出现ID", ""))

    rows = []
    for release in release_rows:
        group_code = release.get("院校专业组代码OCR规范化", "")
        year_items = {year: historical_indexes[year].get(group_code, []) for year in YEARS}
        hit_years = [year for year in YEARS if year_items[year]]
        all_scores = []
        for year in YEARS:
            all_scores.extend(year_scores(year_items[year]))

        req_values = [
            normalize_req(item.get("req"))
            for year in YEARS
            for item in year_items[year]
            if normalize_req(item.get("req"))
        ]
        req_norm_set = join_unique(req_values)
        req_changed = len(set(req_values)) > 1
        duplicate_years = [str(year) for year in YEARS if group_code in duplicate_codes[year]]
        current_duplicate = len(group_occurrences[group_code]) > 1
        historical_names = [name for year in YEARS for name in [year_values(year_items[year], "name")] if name]
        current_school_norm = normalize_name(release.get("院校名称OCR", ""))
        school_name_mismatch = (
            bool(historical_names)
            and current_school_norm
            and not any(current_school_norm in normalize_name(name) for name in historical_names)
        )

        deltas = [
            year_delta_text(year, year_scores(year_items[year]), equivalent_scores)
            for year in YEARS
        ]
        deltas = [delta for delta in deltas if delta]
        hit_count = len(hit_years)
        duplicate_flag = bool(duplicate_years)
        layer = stability_layer(hit_count, duplicate_flag, req_changed, current_duplicate)
        rows.append({
            "三年投档旁挂ID": stable_id("HISTLINE", [release.get("专业行ID", "")]),
            "来源统一逐专业底座入口": "data/working/issue19-major-detail-foundation-release.csv",
            "来源2023投档线": "data/derived/hubei-2023-physics-toudang-parsed.csv",
            "来源2024投档线": "data/derived/hubei-2024-physics-toudang-parsed.csv",
            "来源2025投档线": "data/derived/hubei-2025-physics-toudang-parsed.csv",
            "来源期号": release.get("来源期号", ""),
            "来源PDF_SHA256": release.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "仅供冲稳保筛选线索": "true",
            "专业行ID": release.get("专业行ID", ""),
            "专业组出现ID": release.get("专业组出现ID", ""),
            "院校代码": release.get("院校代码", ""),
            "院校名称OCR": release.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": group_code,
            "来源页码": release.get("来源页码", ""),
            "版面列": release.get("版面列", ""),
            "专业组内专业序号": release.get("专业组内专业序号", ""),
            "专业代号OCR": release.get("专业代号OCR", ""),
            "专业名称及备注OCR短摘": short_text(release.get("专业名称及备注OCR")),
            "2023同代码命中": "true" if year_items[2023] else "false",
            "2023投档分": year_values(year_items[2023], "score"),
            "2023等位分差": year_delta_text(2023, year_scores(year_items[2023]), equivalent_scores),
            "2023再选要求": year_values(year_items[2023], "req"),
            "2023院校专业组名称": year_values(year_items[2023], "name"),
            "2023页码": year_values(year_items[2023], "page"),
            "2023备注": year_values(year_items[2023], "备注"),
            "2023原始行SHA256": row_hashes(year_items[2023]),
            "2024同代码命中": "true" if year_items[2024] else "false",
            "2024投档分": year_values(year_items[2024], "score"),
            "2024等位分差": year_delta_text(2024, year_scores(year_items[2024]), equivalent_scores),
            "2024再选要求": year_values(year_items[2024], "req"),
            "2024院校专业组名称": year_values(year_items[2024], "name"),
            "2024页码": year_values(year_items[2024], "page"),
            "2024备注": year_values(year_items[2024], "备注"),
            "2024原始行SHA256": row_hashes(year_items[2024]),
            "2025同代码命中": "true" if year_items[2025] else "false",
            "2025投档分": year_values(year_items[2025], "score"),
            "2025等位分差": year_delta_text(2025, year_scores(year_items[2025]), equivalent_scores),
            "2025再选要求": year_values(year_items[2025], "req"),
            "2025院校专业组名称": year_values(year_items[2025], "name"),
            "2025页码": "",
            "2025备注": "",
            "2025原始行SHA256": row_hashes(year_items[2025]),
            "同代码命中年份数": str(hit_count),
            "同代码命中年份": "；".join(str(year) for year in hit_years),
            "三年投档分范围": score_range(all_scores),
            "等位分差摘要": "；".join(deltas),
            "三年再选要求规范集合": req_norm_set,
            "再选要求是否跨年变化": "true" if req_changed else "false",
            "历史院校专业组名称是否疑似不一致": "true" if school_name_mismatch else "false",
            "历史投档代码重复年份": "；".join(duplicate_years),
            "历史投档代码是否重复": "true" if duplicate_flag else "false",
            "2026同代码专业组出现次数": str(len(group_occurrences[group_code])),
            "2026同代码专业组是否重复出现": "true" if current_duplicate else "false",
            "稳定性分层": layer,
            "历史线使用口径": "按院校专业组代码同代码旁挂，仅作冲稳保筛选前置线索；不能证明2026专业组存在、组内专业不变、计划数准确或投档位次可沿用。",
            "下一步": "先完成2026招生计划 PDF 原页、湖北官方系统/省招办计划和专业组内完整明细核验，再把三年同代码线索用于冲稳保排序；不得单独据此下最终结论。",
        })

    rows.sort(key=lambda row: (
        sort_int(row.get("来源页码")),
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        sort_int(row.get("专业组内专业序号")),
        row.get("专业行ID", ""),
    ))
    return rows, source_counts, duplicate_codes


def write_summary(rows, source_counts, duplicate_codes):
    summary = {
        "status": "issue19_major_line_historical_toudang_sidecar_not_final",
        "generated_by": "build_issue19_major_line_historical_toudang_sidecar.py",
        "output_table": "data/working/issue19-major-line-historical-toudang-sidecar.csv",
        "source_foundation_release": "data/working/issue19-major-detail-foundation-release.csv",
        "source_toudang_counts": {str(year): source_counts[year] for year in YEARS},
        "historical_duplicate_codes": {str(year): duplicate_codes[year] for year in YEARS},
        "row_count": len(rows),
        "unique_sidecar_id_count": len({row["三年投档旁挂ID"] for row in rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in rows}),
        "hit_year_count_distribution": dict(Counter(row["同代码命中年份数"] for row in rows)),
        "stability_layer_counts": dict(Counter(row["稳定性分层"] for row in rows)),
        "historical_duplicate_major_line_count": sum(row["历史投档代码是否重复"] == "true" for row in rows),
        "current_duplicate_group_major_line_count": sum(row["2026同代码专业组是否重复出现"] == "true" for row in rows),
        "req_changed_major_line_count": sum(row["再选要求是否跨年变化"] == "true" for row in rows),
        "school_name_mismatch_major_line_count": sum(row["历史院校专业组名称是否疑似不一致"] == "true" for row in rows),
        "screening_clue_count": sum(row["仅供冲稳保筛选线索"] == "true" for row in rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in rows),
        "notes": [
            "本表是同院校专业组代码的三年投档线索旁挂表，不是录取概率结论。",
            "同代码命中不能证明2026年专业组、计划数、选科、备注和组内专业保持不变。",
            "2025 H51001 等历史投档代码重复会显式标记，禁止压扁为单一事实。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


FIELDS = [
    "三年投档旁挂ID",
    "来源统一逐专业底座入口",
    "来源2023投档线",
    "来源2024投档线",
    "来源2025投档线",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "最终可用",
    "可进入下一阶段",
    "仅供冲稳保筛选线索",
    "专业行ID",
    "专业组出现ID",
    "院校代码",
    "院校名称OCR",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR短摘",
    "2023同代码命中",
    "2023投档分",
    "2023等位分差",
    "2023再选要求",
    "2023院校专业组名称",
    "2023页码",
    "2023备注",
    "2023原始行SHA256",
    "2024同代码命中",
    "2024投档分",
    "2024等位分差",
    "2024再选要求",
    "2024院校专业组名称",
    "2024页码",
    "2024备注",
    "2024原始行SHA256",
    "2025同代码命中",
    "2025投档分",
    "2025等位分差",
    "2025再选要求",
    "2025院校专业组名称",
    "2025页码",
    "2025备注",
    "2025原始行SHA256",
    "同代码命中年份数",
    "同代码命中年份",
    "三年投档分范围",
    "等位分差摘要",
    "三年再选要求规范集合",
    "再选要求是否跨年变化",
    "历史院校专业组名称是否疑似不一致",
    "历史投档代码重复年份",
    "历史投档代码是否重复",
    "2026同代码专业组出现次数",
    "2026同代码专业组是否重复出现",
    "稳定性分层",
    "历史线使用口径",
    "下一步",
]


def main():
    rows, source_counts, duplicate_codes = build_rows()
    write_csv(OUTPUT, rows, FIELDS)
    write_summary(rows, source_counts, duplicate_codes)
    print(f"写出逐专业三年投档线索旁挂表：{OUTPUT.relative_to(ROOT)}，{len(rows)} 行")
    print(f"写出摘要：{SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
