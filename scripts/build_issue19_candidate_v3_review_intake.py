#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import as_int, input_snapshot


ROOT = Path(__file__).resolve().parents[1]
ISSUE19_SOURCE = ROOT / "data/working/issue19-pdf-source.json"
BASELINE = ROOT / "candidate-baseline.json"
FAMILY_FIT_GROUPS = ROOT / "data/working/issue19-family-fit-group-screen.csv"
CANDIDATE_V2_GROUPS = ROOT / "data/working/issue19-candidate-v2-group-review-seed.csv"
CANDIDATE_V2_MAJORS = ROOT / "data/working/issue19-candidate-v2-major-review-seed.csv"
CANDIDATE_COVERAGE = ROOT / "data/working/issue19-full-admission-plan-candidate-coverage.csv"
PAGE_CODE_AUDIT = ROOT / "data/working/issue19-candidate-page-code-audit.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
HISTORICAL_LINES = {
    "2023": ROOT / "data/derived/hubei-2023-physics-toudang-parsed.csv",
    "2024": ROOT / "data/derived/hubei-2024-physics-toudang-parsed.csv",
    "2025": ROOT / "data/derived/hubei-2025-physics-toudang-parsed.csv",
}

INTAKE_OUTPUT = ROOT / "data/working/issue19-candidate-v3-review-intake.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v3-review-intake-summary.json"

BASE_PRIORITIES = {
    "R0-历史候选优先复核",
    "R1-偏好专业且未自动阻断",
    "R2-偏好专业但有硬风险先核风险",
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def split_labels(value):
    if not value:
        return set()
    return {part.strip() for part in str(value).replace(";", "；").split("；") if part.strip()}


def compact_v2_majors(majors):
    pieces = []
    for row in sorted(majors, key=lambda item: as_int(item.get("组内序号")) or 999):
        pieces.append(
            "{seq}. {code} {name}｜计划:{plan}｜学费:{tuition}｜选科:{subject}｜偏好:{pref}｜风险:{risk}".format(
                seq=row.get("组内序号", ""),
                code=row.get("专业代号", ""),
                name=row.get("专业名称及备注", ""),
                plan=row.get("专业计划数候选", ""),
                tuition=row.get("学费候选", ""),
                subject=row.get("再选科目候选", ""),
                pref=row.get("偏好方向", "") or "无",
                risk=row.get("风险类型", "") or "无",
            )
        )
    return "；".join(pieces)


def history_summary(rows, equivalent_score):
    if not rows:
        return "", ""
    parts = []
    deltas = []
    for row in rows:
        score = as_int(row.get("score"))
        req = row.get("req", "")
        remark = row.get("备注", "")
        score_text = row.get("score", "")
        parts.append(f"{score_text}({req}{'，' + remark if remark else ''})")
        if score is not None and equivalent_score is not None:
            delta = score - equivalent_score
            deltas.append(f"{delta:+d}")
    return "；".join(parts), "；".join(deltas)


def page_manifest_join(page_text, page_manifest_by_page, field):
    pages = [part.strip() for part in str(page_text or "").replace(";", "；").split("；") if part.strip()]
    values = []
    for page in pages:
        value = page_manifest_by_page.get(page, {}).get(field, "")
        if value:
            values.append(value)
    return "；".join(values)


def review_batch(*, family_row, v2_row):
    relation = v2_row.get("关联类型", "") if v2_row else ""
    if "同页相邻风险组" in relation:
        return "B4-同页边界风险组核页"
    if "历史候选" in relation or family_row.get("下一轮复核优先级") == "R0-历史候选优先复核":
        return "B0-历史候选和组号问题优先核页"
    priority = family_row.get("下一轮复核优先级", "")
    if priority == "R1-偏好专业且未自动阻断":
        if as_int(family_row.get("数字媒体技术专业数")):
            return "B1-数字媒体技术优先核页"
        return "B2-偏好专业未自动阻断核页"
    if priority == "R2-偏好专业但有硬风险先核风险":
        return "B3-偏好专业硬风险先核风险"
    if relation:
        return "B5-候选V2补充线索核页"
    return "B6-其他扩展线索"


def review_gaps(row):
    gaps = [
        "PDF原页核验",
        "湖北官方系统/省招办计划核验",
        "高校章程/官网核验",
        "家庭逐专业接受度确认",
        "调剂结论确认",
        "三年历史线使用口径核验",
    ]
    if row.get("办学属性核验状态") == "pending_school_attribute_review":
        gaps.append("办学属性核验")
    if row.get("专业明细来源") == "candidate_v2_review_seed" and row.get("专业明细行数") == "0":
        gaps.append("2026组号变化或旧组号问题")
    return "；".join(gaps)


def main():
    issue19_source = json.loads(ISSUE19_SOURCE.read_text())
    baseline = json.loads(BASELINE.read_text())
    source_issue = issue19_source["source"]["title"]
    source_pdf_sha256 = issue19_source["source"]["sha256"]
    equivalent_scores = {
        year: data["score"]
        for year, data in baseline["equivalent_scores"].items()
        if year in {"2023", "2024", "2025"}
    }

    family_rows = read_csv(FAMILY_FIT_GROUPS)
    v2_group_rows = read_csv(CANDIDATE_V2_GROUPS)
    v2_major_rows = read_csv(CANDIDATE_V2_MAJORS)
    coverage_rows = read_csv(CANDIDATE_COVERAGE)
    page_audit_rows = read_csv(PAGE_CODE_AUDIT)
    page_manifest_rows = read_csv(PAGE_MANIFEST)

    family_by_code = defaultdict(list)
    for row in family_rows:
        family_by_code[row["院校专业组代码OCR规范化"]].append(row)

    v2_code_counts = Counter(row["2026院校专业组代码"] for row in v2_group_rows)
    duplicate_v2_codes = [code for code, count in v2_code_counts.items() if count > 1]
    if duplicate_v2_codes:
        raise ValueError(f"候选V2专业组代码重复，需先人工拆分再生成V3：{duplicate_v2_codes}")

    v2_by_code = {row["2026院校专业组代码"]: row for row in v2_group_rows}
    v2_majors_by_code = defaultdict(list)
    for row in v2_major_rows:
        v2_majors_by_code[row["2026院校专业组代码"]].append(row)

    coverage_by_code = {row["候选专业组代码OCR规范化"]: row for row in coverage_rows}
    page_audit_by_code = {row["候选专业组代码"]: row for row in page_audit_rows}
    page_manifest_by_page = {row["PDF页码"]: row for row in page_manifest_rows}

    historical_by_year_code = {}
    for year, path in HISTORICAL_LINES.items():
        rows_by_code = defaultdict(list)
        for row in read_csv(path):
            rows_by_code[row["code"]].append(row)
        historical_by_year_code[year] = rows_by_code

    selected_family_rows = [
        row for row in family_rows if row.get("下一轮复核优先级") in BASE_PRIORITIES
    ]
    selected_keys = {(row["专业组出现ID"], row["院校专业组代码OCR规范化"]) for row in selected_family_rows}

    intake_rows = []
    for family_row in selected_family_rows:
        code = family_row["院校专业组代码OCR规范化"]
        v2_row = v2_by_code.get(code, {})
        intake_rows.append((family_row, v2_row))

    for code, v2_row in v2_by_code.items():
        if any(item_code == code for _, item_code in selected_keys):
            continue
        family_candidates = family_by_code.get(code)
        if family_candidates:
            for family_row in family_candidates:
                intake_rows.append((family_row, v2_row))
        else:
            synthetic_family_row = {
                "院校代码": v2_row.get("院校代码", ""),
                "院校名称OCR": v2_row.get("院校名称", ""),
                "院校专业组代码OCR规范化": code,
                "专业组号OCR": code[-2:] if len(code) >= 2 else "",
                "专业组出现ID": "",
                "来源页码": v2_row.get("来源页码", ""),
                "版面列": "",
                "专业组标题OCR原文": v2_row.get("院校名称", ""),
                "办学属性核验状态": "pending_school_attribute_review",
                "专业明细行数": v2_row.get("专业明细行数", "0"),
                "组内招生明细OCR": "",
                "偏好专业数": "0",
                "数字媒体技术专业数": "0",
                "计算机类相关专业数": "0",
                "师范类相关专业数": "0",
                "医学护理排除专业数": "0",
                "高收费或超预算专业数": "0",
                "特殊限制待核专业数": "0",
                "组质量层级": "",
                "组复核优先级": "",
                "组结构异常数": v2_row.get("结构异常行数", "0"),
                "组高严重结构异常数": "",
                "候选池V1命中": "是" if v2_row.get("关联类型") == "历史候选" else "否",
                "样本学校命中": "",
                "机器家庭匹配初判": "候选V2补充线索-需先核页",
                "调剂初判": "不可判断-需先确认2026专业组和明细",
                "下一轮复核优先级": "R0-历史候选优先复核"
                if v2_row.get("关联类型") == "历史候选"
                else "R2-偏好专业但有硬风险先核风险",
            }
            intake_rows.append((synthetic_family_row, v2_row))

    output_rows = []
    for family_row, v2_row in intake_rows:
        code = family_row["院校专业组代码OCR规范化"]
        page = family_row.get("来源页码") or v2_row.get("来源页码", "")
        coverage = coverage_by_code.get(code, {})
        page_audit = page_audit_by_code.get(code, {})
        v2_majors = v2_majors_by_code.get(code, [])
        if v2_row:
            major_source = "candidate_v2_review_seed"
            major_detail = compact_v2_majors(v2_majors)
            major_count = v2_row.get("专业明细行数", str(len(v2_majors)))
            relation_type = v2_row.get("关联类型", "")
            relation_source = v2_row.get("关联原候选", "")
        else:
            major_source = "family_fit_full_ocr"
            major_detail = family_row.get("组内招生明细OCR", "")
            major_count = family_row.get("专业明细行数", "0")
            relation_type = "家庭筛选扩展"
            relation_source = family_row.get("下一轮复核优先级", "")

        exact_history = {}
        score_delta = {}
        history_hit_count = 0
        for year in ["2023", "2024", "2025"]:
            history_rows = historical_by_year_code[year].get(code, [])
            if history_rows:
                history_hit_count += 1
            exact_history[year], score_delta[year] = history_summary(
                history_rows,
                equivalent_scores.get(year),
            )

        history_policy = "仅作同组代码历史线索，不能直接证明2026组内专业和投档位次可沿用。"
        if v2_row.get("证据来源") in {"page_visual_review_seed", "page_code_audit_only"}:
            history_policy = "2026组号或结构化存在变化/补种问题，历史线不得直接沿用。"
        elif not history_hit_count:
            history_policy = "未命中同组代码历史投档线，需另找同校相邻组或新组参照。"

        row = {
            "来源期号": source_issue,
            "来源PDF_SHA256": source_pdf_sha256,
            "数据阶段": "issue19_candidate_v3_review_intake",
            "最终可用": "false",
            "核验状态": "pending_v3_manual_review",
            "候选V3入口ID": stable_id(
                "V3",
                [
                    source_pdf_sha256,
                    family_row.get("专业组出现ID", ""),
                    code,
                    relation_type,
                    relation_source,
                ],
            ),
            "入口类型": relation_type,
            "入口来源说明": relation_source,
            "复核批次": review_batch(family_row=family_row, v2_row=v2_row),
            "候选闸门状态": "pending_verification",
            "可进入最终候选": "false",
            "院校代码": family_row.get("院校代码", ""),
            "院校名称OCR": family_row.get("院校名称OCR", ""),
            "2026院校专业组代码": code,
            "专业组出现ID": family_row.get("专业组出现ID", ""),
            "来源页码": page,
            "私有页图证据编号": page_manifest_join(page, page_manifest_by_page, "私有页图证据编号"),
            "私有页图SHA256": page_manifest_join(page, page_manifest_by_page, "私有页图SHA256"),
            "私有OCR文本证据编号": page_manifest_join(page, page_manifest_by_page, "私有OCR文本证据编号"),
            "办学属性核验状态": family_row.get("办学属性核验状态", "pending_school_attribute_review"),
            "专业明细来源": major_source,
            "专业明细行数": major_count,
            "组内招生明细": major_detail,
            "偏好专业数": family_row.get("偏好专业数", "0"),
            "数字媒体技术专业数": family_row.get("数字媒体技术专业数", "0"),
            "计算机类相关专业数": family_row.get("计算机类相关专业数", "0"),
            "师范类相关专业数": family_row.get("师范类相关专业数", "0"),
            "医学护理排除专业数": family_row.get("医学护理排除专业数", "0"),
            "高收费或超预算专业数": family_row.get("高收费或超预算专业数", "0"),
            "特殊限制待核专业数": family_row.get("特殊限制待核专业数", "0"),
            "机器家庭匹配初判": family_row.get("机器家庭匹配初判", ""),
            "调剂初判": family_row.get("调剂初判", ""),
            "下一轮复核优先级": family_row.get("下一轮复核优先级", ""),
            "组质量层级": family_row.get("组质量层级", ""),
            "组复核优先级": family_row.get("组复核优先级", ""),
            "组结构异常数": family_row.get("组结构异常数", ""),
            "组高严重结构异常数": family_row.get("组高严重结构异常数", ""),
            "历史候选匹配": "是" if coverage or v2_row.get("关联类型") == "历史候选" else "否",
            "候选池原始项": coverage.get("候选池学校专业组", v2_row.get("关联原候选", "")),
            "候选城市": coverage.get("城市", ""),
            "候选年份覆盖": coverage.get("年份覆盖", ""),
            "候选2023最低分": coverage.get("2023最低分", ""),
            "候选2024最低分": coverage.get("2024最低分", ""),
            "候选2025最低分": coverage.get("2025最低分", ""),
            "候选历史风险初判": coverage.get("历史风险初判", ""),
            "页面组号审计": page_audit.get("异常类型", v2_row.get("页面组号审计", "")),
            "页面组号证据": page_audit.get("页面OCR证据", v2_row.get("页面组号证据", "")),
            "2023同组投档线": exact_history["2023"],
            "2024同组投档线": exact_history["2024"],
            "2025同组投档线": exact_history["2025"],
            "三年同组命中数": str(history_hit_count),
            "等位分差摘要": "；".join(
                f"{year}:{score_delta[year]}" for year in ["2023", "2024", "2025"] if score_delta[year]
            ),
            "历史线使用口径": history_policy,
            "PDF原页核验状态": "pending_original_pdf_page_review",
            "湖北官方系统核验状态": "pending_hubei_official_plan_review",
            "高校官网章程核验状态": "pending_school_charter_review",
            "家庭接受度核验状态": "pending_family_acceptance_review",
            "调剂结论状态": "pending_transfer_decision",
            "历史线核验状态": "pending_history_line_review",
            "核验缺口": "",
            "下一步": "按复核批次回看第19期原PDF页；再核湖北官方系统/省招办计划、高校官网或章程、家庭接受度、调剂结论和历史线使用口径。",
        }
        row["核验缺口"] = review_gaps(row)
        output_rows.append(row)

    batch_order = {
        "B0-历史候选和组号问题优先核页": 0,
        "B1-数字媒体技术优先核页": 1,
        "B2-偏好专业未自动阻断核页": 2,
        "B3-偏好专业硬风险先核风险": 3,
        "B4-同页边界风险组核页": 4,
        "B5-候选V2补充线索核页": 5,
        "B6-其他扩展线索": 6,
    }
    output_rows.sort(
        key=lambda row: (
            batch_order.get(row["复核批次"], 99),
            row["来源页码"],
            row["院校代码"],
            row["2026院校专业组代码"],
            row["专业组出现ID"],
        )
    )

    fields = [
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "候选V3入口ID",
        "入口类型",
        "入口来源说明",
        "复核批次",
        "候选闸门状态",
        "可进入最终候选",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业组出现ID",
        "来源页码",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "办学属性核验状态",
        "专业明细来源",
        "专业明细行数",
        "组内招生明细",
        "偏好专业数",
        "数字媒体技术专业数",
        "计算机类相关专业数",
        "师范类相关专业数",
        "医学护理排除专业数",
        "高收费或超预算专业数",
        "特殊限制待核专业数",
        "机器家庭匹配初判",
        "调剂初判",
        "下一轮复核优先级",
        "组质量层级",
        "组复核优先级",
        "组结构异常数",
        "组高严重结构异常数",
        "历史候选匹配",
        "候选池原始项",
        "候选城市",
        "候选年份覆盖",
        "候选2023最低分",
        "候选2024最低分",
        "候选2025最低分",
        "候选历史风险初判",
        "页面组号审计",
        "页面组号证据",
        "2023同组投档线",
        "2024同组投档线",
        "2025同组投档线",
        "三年同组命中数",
        "等位分差摘要",
        "历史线使用口径",
        "PDF原页核验状态",
        "湖北官方系统核验状态",
        "高校官网章程核验状态",
        "家庭接受度核验状态",
        "调剂结论状态",
        "历史线核验状态",
        "核验缺口",
        "下一步",
    ]
    write_csv(INTAKE_OUTPUT, output_rows, fields)

    batch_counts = Counter(row["复核批次"] for row in output_rows)
    relation_counts = Counter(row["入口类型"] for row in output_rows)
    major_source_counts = Counter(row["专业明细来源"] for row in output_rows)
    history_hit_counts = Counter(row["三年同组命中数"] for row in output_rows)
    summary = {
        "status": "issue19_candidate_v3_review_intake_pending_manual_review",
        "source_issue": source_issue,
        "source_pdf_sha256": source_pdf_sha256,
        "data_stage": "issue19_candidate_v3_review_intake",
        "generated_by": "scripts/build_issue19_candidate_v3_review_intake.py",
        "inputs": input_snapshot(
            ROOT,
            [
                ISSUE19_SOURCE,
                BASELINE,
                FAMILY_FIT_GROUPS,
                CANDIDATE_V2_GROUPS,
                CANDIDATE_V2_MAJORS,
                CANDIDATE_COVERAGE,
                PAGE_CODE_AUDIT,
                PAGE_MANIFEST,
                *HISTORICAL_LINES.values(),
            ],
        ),
        "intake_count": len(output_rows),
        "batch_counts": dict(sorted(batch_counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "major_source_counts": dict(sorted(major_source_counts.items())),
        "history_exact_code_hit_count_distribution": dict(sorted(history_hit_counts.items())),
        "historical_candidate_count": sum(row["历史候选匹配"] == "是" for row in output_rows),
        "r0_r1_r2_family_fit_source_count": len(selected_family_rows),
        "candidate_v2_group_count": len(v2_group_rows),
        "candidate_v2_group_not_in_family_fit_priority_count": len(output_rows) - len(selected_family_rows),
        "final_available_count": sum(row["可进入最终候选"] == "true" for row in output_rows),
        "notes": [
            "本表是候选V3人工复核入口，不是最终志愿建议。",
            "R0/R1/R2 来自家庭底线筛选表，另补入候选V2的未定位、页图补种和同页边界组。",
            "候选V2有页图重切或补种证据时，专业明细优先使用 candidate_v2_review_seed。",
            "历史投档线按同组代码精确匹配，仅作线索；2026组号变化、专业组变化或组内专业变化时不得直接沿用。",
            "所有行保持可进入最终候选=false，必须完成PDF原页、湖北官方系统、高校章程、家庭接受度和调剂结论核验后才能升级。",
        ],
        "outputs": [str(INTAKE_OUTPUT.relative_to(ROOT))],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"写出候选V3复核入口表：{INTAKE_OUTPUT}")
    print(f"写出候选V3复核入口摘要：{SUMMARY_OUTPUT}")
    print(f"入口行数：{len(output_rows)}")


if __name__ == "__main__":
    main()
