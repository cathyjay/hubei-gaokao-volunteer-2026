#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_HASH_EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "candidate-screenshots",
    "private",
    "scratch",
    "tmp",
    "user-provided",
}
PUBLIC_HASH_EXCLUDED_SUFFIXES = {".pyc"}


def ok(label, condition, detail=""):
    status = "通过" if condition else "失败"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return condition


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def issue19_group_match_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        row.get("来源页码", ""),
        row.get("版面列", ""),
        row.get("专业组标题行号", ""),
        row.get("专业组标题OCR原文", ""),
    )


def issue19_major_match_key(row):
    return (
        row.get("院校代码", ""),
        row.get("院校专业组代码OCR规范化", ""),
        row.get("专业代号OCR", ""),
        row.get("专业名称及备注OCR", ""),
        row.get("来源页码", ""),
        row.get("版面列", ""),
        row.get("专业计划数OCR候选", ""),
        row.get("学费OCR候选", ""),
    )


def issue19_major_line_id(row, index, source_pdf_sha256):
    return stable_id(
        "M",
        [
            source_pdf_sha256,
            index,
            row.get("院校代码", ""),
            row.get("院校专业组代码OCR规范化", ""),
            row.get("来源页码", ""),
            row.get("版面列", ""),
            row.get("专业起始行号", ""),
            row.get("专业起始y", ""),
            row.get("专业代号OCR", ""),
            row.get("专业名称及备注OCR", ""),
        ],
    )


def issue19_assign_group_occurrence_ids(group_rows, major_rows, source_pdf_sha256):
    group_ids_by_key = {}
    groups_by_code = {}
    group_id_by_row_index = {}
    for index, row in enumerate(group_rows, start=1):
        group_id = stable_id(
            "G",
            [
                source_pdf_sha256,
                index,
                row.get("院校代码", ""),
                row.get("院校专业组代码OCR规范化", ""),
                row.get("来源页码", ""),
                row.get("版面列", ""),
                row.get("专业组标题行号", ""),
                row.get("专业组标题OCR原文", ""),
            ],
        )
        group_id_by_row_index[index] = group_id
        group_ids_by_key[issue19_group_match_key(row)] = group_id
        groups_by_code.setdefault(row.get("院校专业组代码OCR规范化"), []).append((group_id, row))

    major_group_ids = {}
    unmatched_major_count = 0
    fallback_unique_group_code_count = 0
    for index, row in enumerate(major_rows, start=1):
        exact_group_id = group_ids_by_key.get(issue19_group_match_key(row))
        if exact_group_id:
            major_group_ids[index] = exact_group_id
            continue
        code_groups = groups_by_code.get(row.get("院校专业组代码OCR规范化"), [])
        if len(code_groups) == 1:
            major_group_ids[index] = code_groups[0][0]
            fallback_unique_group_code_count += 1
            continue
        unmatched_major_count += 1
    return group_id_by_row_index, major_group_ids, unmatched_major_count, fallback_unique_group_code_count


def manifest_files():
    ignored = {ROOT / "CHECKSUMS.sha256"}
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(ROOT).parts
        if any(part in PUBLIC_HASH_EXCLUDED_DIRS for part in rel_parts):
            continue
        if path.suffix in PUBLIC_HASH_EXCLUDED_SUFFIXES:
            continue
        if path in ignored:
            continue
        files.append(path.relative_to(ROOT).as_posix())
    return set(files)


def main():
    baseline = json.loads((ROOT / "candidate-baseline.json").read_text())
    section = json.loads(
        (ROOT / "data/derived/hubei-2026-physics-section-static-gaokao-cn.json").read_text()
    )
    row_515 = section["data"]["search"]["515"]

    checks = []
    scores = baseline["scores"]
    checks.append(ok("各科成绩合计等于总分", sum(v for k, v in scores.items() if k != "总分") == scores["总分"]))
    checks.append(ok("总分为 515", scores["总分"] == 515))
    checks.append(ok("一分一段 JSON 中 515 分累计位次为 91723", row_515["total"] == "91723", row_515["total"]))
    checks.append(ok("一分一段 JSON 中 515 分位次区间为 90895-91723", row_515["rank_range"] == "90895-91723", row_515["rank_range"]))

    appositive = {str(x["year"]): x for x in row_515["appositive_fraction"]}
    checks.append(ok("2025 等位分为 494", appositive["2025"]["score"] == "494", appositive["2025"]["score"]))
    checks.append(ok("2024 等位分为 497", appositive["2024"]["score"] == "497", appositive["2024"]["score"]))
    checks.append(ok("2023 等位分为 481", appositive["2023"]["score"] == "481", appositive["2023"]["score"]))

    raw_images = list((ROOT / "data/official/hubei-2025-physics-toudang/raw-images").glob("*.jpg"))
    checks.append(ok("2025 官方投档线原始图片数量为 71", len(raw_images) == 71, str(len(raw_images))))

    parsed_path = ROOT / "data/derived/hubei-2025-physics-toudang-parsed.csv"
    with parsed_path.open(newline="") as f:
        parsed_count = sum(1 for _ in csv.DictReader(f))
    checks.append(ok("2025 投档线解析行数不少于 3000", parsed_count >= 3000, str(parsed_count)))

    for year, minimum in [("2024", 2700), ("2023", 2800)]:
        pdf = ROOT / f"data/official/hubei-{year}-physics-toudang/hubei-{year}-physics-toudang.pdf"
        checks.append(ok(f"{year} 官方投档线 PDF 已留存", pdf.exists() and pdf.stat().st_size > 1000))
        parsed = ROOT / f"data/derived/hubei-{year}-physics-toudang-parsed.csv"
        with parsed.open(newline="") as f:
            count = sum(1 for _ in csv.DictReader(f))
        checks.append(ok(f"{year} 投档线解析行数不少于 {minimum}", count >= minimum, str(count)))

    policy_files = [
        ROOT / "data/official/hubei-2026-volunteer-policy/142885-volunteer-time.html",
        ROOT / "data/official/hubei-2026-volunteer-policy/143020-policy.html",
        ROOT / "data/official/hubei-2026-volunteer-policy/143021-policy.html",
        ROOT / "data/official/hubei-2026-volunteer-policy/143022-policy.html",
        ROOT / "data/official/hubei-2026-volunteer-policy/143040-policy.html",
    ]
    checks.append(ok("2026 湖北志愿填报政策页均已留存", all(p.exists() and p.stat().st_size > 1000 for p in policy_files)))

    major_catalog_pdf = ROOT / "data/official/moe-major-catalog/2026-major-catalog.pdf"
    checks.append(ok("教育部 2026 本科专业目录 PDF 已留存", major_catalog_pdf.exists() and major_catalog_pdf.stat().st_size > 1000))

    qianwen_path = ROOT / "data/external/qianwen-gaokao/api/getUserFilters-need-major.json"
    qianwen = json.loads(qianwen_path.read_text())
    qianwen_text = json.dumps(qianwen, ensure_ascii=False)
    checks.append(ok("千问高考专业分类接口返回成功", qianwen.get("status") == 0 and qianwen.get("code") == "00000"))
    checks.append(ok("千问高考专业分类包含数字媒体技术 080906", "数字媒体技术" in qianwen_text and "080906" in qianwen_text))
    checks.append(ok("千问高考专业分类包含教育学类 0401", "教育学类" in qianwen_text and "0401" in qianwen_text))

    candidate_pool_path = ROOT / "data/working/candidate-pool-v1.csv"
    with candidate_pool_path.open(newline="") as f:
        candidate_rows = list(csv.DictReader(f))
    checks.append(ok("第一版候选池共 20 条", len(candidate_rows) == 20, str(len(candidate_rows))))
    checks.append(ok(
        "第一版候选池主方案项待核验且医学项已排除",
        all(
            "needs_2026_plan_verification" in row.get("复核状态", "")
            or "excluded_medical" in row.get("复核状态", "")
            for row in candidate_rows
        )
        and sum("excluded_medical" in row.get("复核状态", "") for row in candidate_rows) == 4,
    ))

    family_preferences = json.loads((ROOT / "data/working/family-preferences.json").read_text())
    major_preference = family_preferences["major_preference"]
    budget_preference = family_preferences["budget"]
    checks.append(ok(
        "家庭偏好已记录不学医",
        {"医学类", "护理类"}.issubset(set(major_preference.get("rejected_directions", []))),
    ))
    checks.append(ok(
        "家庭专业优先级已记录",
        major_preference.get("priority_order") == ["数字媒体技术", "计算机类相关专业", "师范类专业"],
    ))
    checks.append(ok(
        "家庭费用上限已记录为 15000 元/年",
        budget_preference.get("annual_upper_limit_yuan") == 15000,
    ))

    school_crosscheck_files = [
        ROOT / "data/external/school-plan-crosschecks/wust-2026-hubei-major-groups.html",
        ROOT / "data/external/school-plan-crosschecks/wust-2026-major-plan-fees.html",
    ]
    checks.append(ok("高校官网交叉校验样例已留存", all(p.exists() and p.stat().st_size > 1000 for p in school_crosscheck_files)))

    magazine_search_files = [
        ROOT / "docs/HUBEI_ADMISSION_MAGAZINE_SEARCH.md",
        ROOT / "data/external/hbksw-product-brochure/index.html",
        ROOT / "data/external/hbksw-product-brochure/1029-06.jpg",
        ROOT / "data/external/hubei-admission-magazine-search/whhxit-2026-c211-codes.html",
    ]
    checks.append(ok("第 16/19 期专项检索证据已留存", all(p.exists() and p.stat().st_size > 1000 for p in magazine_search_files)))

    ocr_workflow_files = [
        ROOT / "docs/OCR_WORKFLOW.md",
        ROOT / "scripts/ocr_magazine_pages.py",
        ROOT / "scripts/vision_ocr.swift",
        ROOT / "scripts/ocr_pdf_pages.py",
        ROOT / "scripts/ocr_jsonl_to_line_csv.py",
        ROOT / "scripts/ocr_qc_report.py",
    ]
    checks.append(ok("第 19 期照片 OCR 工作流已就绪", all(p.exists() and p.stat().st_size > 1000 for p in ocr_workflow_files)))

    issue19_source = json.loads((ROOT / "data/working/issue19-pdf-source.json").read_text())
    checks.append(ok(
        "第 19 期 PDF 元数据已记录",
        issue19_source["source"]["sha256"] == "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
        and issue19_source["source"]["pages"] == 240
        and issue19_source["source"]["text_layer"] == "none_detected",
    ))

    issue19_template = ROOT / "data/working/issue19-admission-plan-template.csv"
    template_header = issue19_template.read_text(encoding="utf-8").splitlines()[0]
    required_template_fields = [
        "来源页码",
        "来源PDF_SHA256",
        "核验状态",
        "院校代码",
        "院校名称",
        "院校专业组代码",
        "专业代号",
        "专业名称",
        "专业计划数",
        "组内调剂可接受性",
    ]
    checks.append(ok(
        "第 19 期招生计划中文结构化模板字段完整",
        all(re.search(rf"(^|,){field}(,|$)", template_header) for field in required_template_fields),
    ))

    sample_schools_path = ROOT / "data/working/issue19-sample-schools-20.csv"
    with sample_schools_path.open(newline="", encoding="utf-8-sig") as f:
        sample_schools = list(csv.DictReader(f))
    checks.append(ok(
        "第 19 期 OCR double check 样本学校为 20 所",
        len(sample_schools) == 20 and all(row.get("官网核验状态") for row in sample_schools),
        str(len(sample_schools)),
    ))

    official_sources_path = ROOT / "data/working/issue19-sample-school-official-sources.csv"
    with official_sources_path.open(newline="", encoding="utf-8-sig") as f:
        official_sources = list(csv.DictReader(f))
    saved_official_pages = list((ROOT / "data/external/issue19-sample-school-official").glob("*"))
    checks.append(ok(
        "第 19 期样本学校官网来源状态已记录",
        len(official_sources) == 20 and len(saved_official_pages) >= 8,
        f"{len(official_sources)} sources, {len(saved_official_pages)} local files",
    ))

    high_priority_summary_path = ROOT / "data/working/issue19-high-priority-double-check-summary.csv"
    with high_priority_summary_path.open(newline="", encoding="utf-8-sig") as f:
        high_priority_summary = list(csv.DictReader(f))
    checks.append(ok(
        "第 19 期高优先级 7 校 double check 摘要已生成",
        len(high_priority_summary) == 7
        and all(row.get("证据集分层") for row in high_priority_summary)
        and any(row.get("学校名称") == "湖北理工学院" and "主证据" in row.get("证据集分层", "") for row in high_priority_summary),
        str(len(high_priority_summary)),
    ))

    first_batch_seed = json.loads((ROOT / "data/working/issue19-first-batch-review-seed-summary.json").read_text())
    checks.append(ok(
        "第 19 期第一批 4 校逐组复核种子摘要已生成",
        first_batch_seed.get("status") == "review_seed_only_not_final"
        and len(first_batch_seed.get("schools", [])) == 4
        and sum(row.get("专业组标题候选数", 0) for row in first_batch_seed.get("schools", [])) >= 40,
        str(sum(row.get("专业组标题候选数", 0) for row in first_batch_seed.get("schools", []))),
    ))

    first_batch_draft_path = ROOT / "data/working/issue19-first-batch-group-major-draft-summary.json"
    first_batch_draft_text = first_batch_draft_path.read_text()
    first_batch_draft = json.loads(first_batch_draft_text)
    draft_group_count = sum(row.get("OCR专业组数", 0) for row in first_batch_draft.get("schools", []))
    draft_major_count = sum(row.get("OCR专业行数", 0) for row in first_batch_draft.get("schools", []))
    draft_tags = {
        tag
        for row in first_batch_draft.get("schools", [])
        for tag in row.get("偏好和风险标签", [])
    }
    expected_first_batch_schools = {
        "C102": "武汉科技大学",
        "C103": "湖北大学",
        "C138": "湖北理工学院",
        "C150": "武汉商学院",
    }
    allowed_first_batch_summary_keys = {"status", "schools", "notes"}
    allowed_first_batch_school_keys = {
        "学校名称",
        "院校代码",
        "OCR专业组数",
        "OCR专业行数",
        "PDF OCR页码",
        "偏好和风险标签",
        "状态",
    }
    first_batch_public_forbidden_tokens = [
        "private/",
        "private\\",
        "private_outputs",
        "\"source\"",
        "ocr-runs",
        "rendered-pages",
        "derived/",
        ".jpg",
        ".jpeg",
        ".png",
        "专业名称及备注OCR",
        "专业代号OCR",
        "专业组标题OCR原文",
        "专业起始行号",
        "身份证",
        "准考证",
        "报名号",
        "姓名",
        "序列号",
    ]
    first_batch_public_schools = first_batch_draft.get("schools", [])
    checks.append(ok(
        "第 19 期第一批 4 校专业组/专业 OCR 初稿公开摘要不含私有路径和敏感明细",
        set(first_batch_draft.keys()) <= allowed_first_batch_summary_keys
        and not any(token in first_batch_draft_text for token in first_batch_public_forbidden_tokens),
    ))
    checks.append(ok(
        "第 19 期第一批 4 校专业组/专业 OCR 初稿公开摘要字段和学校范围正确",
        len(first_batch_public_schools) == 4
        and all(set(row.keys()) <= allowed_first_batch_school_keys for row in first_batch_public_schools)
        and {
            row.get("院校代码"): row.get("学校名称")
            for row in first_batch_public_schools
        } == expected_first_batch_schools
        and all(row.get("状态") == "ocr_group_major_draft_needs_manual_pdf_review" for row in first_batch_public_schools)
        and all(
            isinstance(page, int) and 1 <= page <= 240
            for row in first_batch_public_schools
            for page in row.get("PDF OCR页码", [])
        ),
    ))
    checks.append(ok(
        "第 19 期第一批 4 校专业组/专业 OCR 初稿摘要已生成",
        first_batch_draft.get("status") == "ocr_group_major_draft_needs_manual_pdf_review"
        and draft_group_count == 44
        and draft_major_count >= 200
        and "rejected_medical" in draft_tags
        and "priority_2_computer" in draft_tags,
        f"{draft_group_count} groups, {draft_major_count} majors",
    ))

    full_draft_summary_path = ROOT / "data/working/issue19-full-admission-plan-ocr-draft-summary.json"
    full_draft_summary = json.loads(full_draft_summary_path.read_text())
    full_school_path = ROOT / "data/working/issue19-full-admission-plan-school-ocr-draft.csv"
    full_group_path = ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv"
    full_major_path = ROOT / "data/working/issue19-full-admission-plan-major-ocr-draft.csv"
    full_candidate_coverage_path = ROOT / "data/working/issue19-full-admission-plan-candidate-coverage.csv"
    with full_school_path.open(newline="", encoding="utf-8-sig") as f:
        full_school_rows = list(csv.DictReader(f))
    with full_group_path.open(newline="", encoding="utf-8-sig") as f:
        full_group_reader = csv.DictReader(f)
        full_group_rows = list(full_group_reader)
        full_group_fields = full_group_reader.fieldnames or []
    with full_major_path.open(newline="", encoding="utf-8-sig") as f:
        full_major_reader = csv.DictReader(f)
        full_major_rows = list(full_major_reader)
        full_major_fields = full_major_reader.fieldnames or []
    with full_candidate_coverage_path.open(newline="", encoding="utf-8-sig") as f:
        full_candidate_coverage_rows = list(csv.DictReader(f))

    full_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            full_draft_summary_path,
            full_school_path,
            full_group_path,
            full_major_path,
            full_candidate_coverage_path,
        ]
    )
    full_public_forbidden_tokens = [
        "/Users/",
        "private/",
        "private\\",
        "ocr-runs",
        "rendered-pages",
        ".jpg",
        ".jpeg",
        ".png",
        "身份证",
        "准考证",
        "报名号",
        "序列号",
    ]
    required_full_major_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业代号OCR",
        "专业名称及备注OCR",
        "来源页码",
        "专业计划数OCR候选",
        "学费OCR候选",
        "字段完整性标记",
        "核验状态",
    }
    required_full_group_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "OCR专业行数",
        "偏好和风险标签",
        "字段完整性标记",
        "核验状态",
    }
    checks.append(ok(
        "第 19 期全量招生明细 OCR 初稿摘要和范围正确",
        full_draft_summary.get("status") == "full_ocr_draft_needs_manual_pdf_review"
        and "湖北省 2026 本科普通批首选物理在鄂招生计划" in full_draft_summary.get("scope", "")
        and full_draft_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and full_draft_summary.get("counts", {}).get("OCR院校数") == 1103
        and full_draft_summary.get("counts", {}).get("OCR院校专业组数") == 3329
        and full_draft_summary.get("counts", {}).get("OCR专业行数") == 13736
        and full_draft_summary.get("major_field_completeness", {}).get("最终可用true专业行数") == 0,
    ))
    checks.append(ok(
        "第 19 期全量招生明细 OCR 初稿风险标签统计正确",
        full_draft_summary.get("risk_and_preference_tag_counts", {}).get("rejected_medical") == 769
        and full_draft_summary.get("risk_and_preference_tag_counts", {}).get("priority_2_computer") == 1032
        and full_draft_summary.get("risk_and_preference_tag_counts", {}).get("priority_3_teacher") == 515,
    ))
    checks.append(ok(
        "第 19 期全量招生明细 OCR 初稿公开 CSV 行数正确",
        len(full_school_rows) == 1103
        and len(full_group_rows) == 3329
        and len(full_major_rows) == 13736
        and len(full_candidate_coverage_rows) == 20,
        f"{len(full_school_rows)} schools, {len(full_group_rows)} groups, {len(full_major_rows)} majors",
    ))
    checks.append(ok(
        "第 19 期全量招生明细 OCR 初稿公开 CSV 字段完整",
        required_full_major_fields.issubset(set(full_major_fields))
        and required_full_group_fields.issubset(set(full_group_fields)),
    ))
    checks.append(ok(
        "第 19 期全量招生明细 OCR 初稿状态保持待人工复核",
        all(row.get("最终可用") == "false" and row.get("核验状态") == "needs_manual_pdf_review" for row in full_major_rows)
        and all(row.get("最终可用") == "false" and row.get("核验状态") == "needs_manual_pdf_review" for row in full_group_rows),
    ))
    medical_boundary_keywords = [
        "中医骨伤科学",
        "康复治疗学",
        "健康服务与管理",
        "食品卫生与营养学",
        "公共卫生",
    ]
    checks.append(ok(
        "第 19 期医学相关边界专业已进入风险标签",
        all(
            all(
                "rejected_medical" in row.get("偏好和风险标签", "")
                for row in full_major_rows
                if keyword in row.get("专业名称及备注OCR", "")
            )
            for keyword in medical_boundary_keywords
        ),
    ))
    checks.append(ok(
        "第 19 期全量招生明细 OCR 初稿候选池覆盖已记录",
        full_draft_summary.get("candidate_pool_v1_coverage", {}).get("候选专业组数") == 20
        and full_draft_summary.get("candidate_pool_v1_coverage", {}).get("全量OCR命中候选专业组数") == 17
        and set(full_draft_summary.get("candidate_pool_v1_coverage", {}).get("未命中候选专业组", [])) == {"C10702", "C10704", "K15123"},
    ))
    checks.append(ok(
        "第 19 期全量招生明细 OCR 初稿公开文件不含本地路径和身份信息",
        not any(token in full_public_text for token in full_public_forbidden_tokens),
    ))

    candidate_review_summary_path = ROOT / "data/working/issue19-candidate-plan-review-summary.json"
    candidate_review_summary_csv = ROOT / "data/working/issue19-candidate-plan-review-summary.csv"
    candidate_review_detail_csv = ROOT / "data/working/issue19-candidate-plan-review-major-detail.csv"
    candidate_review_queue_csv = ROOT / "data/working/issue19-priority-review-queue.csv"
    priority_review_summary_path = ROOT / "data/working/issue19-priority-review-queues-summary.json"
    preference_search_csv = ROOT / "data/working/issue19-preference-major-search.csv"
    hard_risk_queue_csv = ROOT / "data/working/issue19-hard-risk-group-review-queue.csv"
    with candidate_review_summary_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_review_reader = csv.DictReader(f)
        candidate_review_rows = list(candidate_review_reader)
        candidate_review_fields = set(candidate_review_reader.fieldnames or [])
    with candidate_review_detail_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_detail_reader = csv.DictReader(f)
        candidate_detail_rows = list(candidate_detail_reader)
        candidate_detail_fields = set(candidate_detail_reader.fieldnames or [])
    with candidate_review_queue_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_queue_reader = csv.DictReader(f)
        candidate_queue_rows = list(candidate_queue_reader)
        candidate_queue_fields = set(candidate_queue_reader.fieldnames or [])
    with preference_search_csv.open(newline="", encoding="utf-8-sig") as f:
        preference_reader = csv.DictReader(f)
        preference_rows = list(preference_reader)
        preference_fields = set(preference_reader.fieldnames or [])
    with hard_risk_queue_csv.open(newline="", encoding="utf-8-sig") as f:
        hard_risk_reader = csv.DictReader(f)
        hard_risk_rows = list(hard_risk_reader)
        hard_risk_fields = set(hard_risk_reader.fieldnames or [])

    candidate_review_summary = json.loads(candidate_review_summary_path.read_text())
    priority_review_summary = json.loads(priority_review_summary_path.read_text())
    required_candidate_summary_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "候选池学校专业组",
        "候选专业组代码",
        "硬风险专业行数",
        "硬风险标签命中数",
        "硬风险类型",
        "机器初判",
        "核验状态",
    }
    required_candidate_detail_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "候选池学校专业组",
        "候选专业组代码",
        "专业名称及备注OCR",
        "偏好和风险标签",
        "核验状态",
        "最终可用",
    }
    required_candidate_queue_fields = {
        "复核优先级",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "候选池学校专业组",
        "候选专业组代码",
        "机器初判",
        "初判原因",
        "硬风险类型",
        "第19期全量OCR命中",
    }
    required_preference_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "优先方向",
        "综合风险等级",
        "本专业OCR风险等级",
        "本专业风险类型",
        "专业组风险类型",
        "院校专业组代码",
        "专业名称及备注OCR",
        "最终可用",
    }
    required_hard_risk_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "综合风险等级",
        "风险类型",
        "院校专业组代码",
        "核验状态",
        "最终可用",
    }
    shared_forbidden_tokens = [
        "/Users/",
        "private/",
        "private\\",
        "ocr-runs",
        "rendered-pages",
        ".jpg",
        ".jpeg",
        ".png",
        "身份证",
        "准考证",
        "报名号",
        "序列号",
    ]
    review_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            candidate_review_summary_path,
            candidate_review_summary_csv,
            candidate_review_detail_csv,
            candidate_review_queue_csv,
            priority_review_summary_path,
            preference_search_csv,
            hard_risk_queue_csv,
        ]
    )
    checks.append(ok(
        "第 19 期候选复核工作台摘要和行数正确",
        candidate_review_summary.get("status") == "candidate_review_workbench_needs_manual_pdf_review"
        and candidate_review_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and candidate_review_summary.get("candidate_count") == 20
        and candidate_review_summary.get("matched_candidate_count") == 17
        and candidate_review_summary.get("unmatched_candidate_count") == 3
        and candidate_review_summary.get("candidate_major_detail_count") == 77
        and candidate_review_summary.get("machine_decision_counts") == {
            "默认排除": 10,
            "可复核但字段不完整": 3,
            "高风险暂缓": 3,
            "待定位": 3,
            "可人工复核": 1,
        }
        and len(candidate_review_rows) == 20
        and len(candidate_detail_rows) == 77
        and len(candidate_queue_rows) == 20,
    ))
    checks.append(ok(
        "第 19 期候选复核工作台字段和风险口径正确",
        required_candidate_summary_fields.issubset(candidate_review_fields)
        and required_candidate_detail_fields.issubset(candidate_detail_fields)
        and required_candidate_queue_fields.issubset(candidate_queue_fields)
        and "硬风险命中数" not in candidate_review_fields
        and any(
            row.get("候选专业组代码") == "C15003"
            and row.get("机器初判") == "高风险暂缓"
            and "语种或单科限制" in row.get("硬风险类型", "")
            for row in candidate_review_rows
        )
        and any(
            row.get("候选专业组代码") == "C10703"
            and row.get("机器初判") == "高风险暂缓"
            and "医学/护理等排除方向" in row.get("硬风险类型", "")
            for row in candidate_review_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选复核工作台状态保持待人工复核",
        all(row.get("最终可用") == "false" and row.get("核验状态") == "needs_manual_pdf_review" for row in candidate_detail_rows)
        and all(row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"] for row in candidate_review_rows + candidate_detail_rows + candidate_queue_rows),
    ))

    checks.append(ok(
        "第 19 期全量优先专业和硬风险队列摘要正确",
        priority_review_summary.get("status") == "priority_review_queues_need_manual_pdf_review"
        and priority_review_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and priority_review_summary.get("preference_major_count") == 2499
        and priority_review_summary.get("preference_counts") == {
            "数字媒体技术": 78,
            "计算机类相关": 1867,
            "师范类相关": 601,
        }
        and priority_review_summary.get("preference_comprehensive_risk_level_counts") == {
            "未触发硬风险": 360,
            "限制风险": 133,
            "硬风险": 2006,
        }
        and priority_review_summary.get("preference_major_only_risk_level_counts") == {
            "未触发硬风险": 1699,
            "限制风险": 194,
            "硬风险": 606,
        }
        and priority_review_summary.get("preference_rows_with_group_risk_count") == 2139
        and priority_review_summary.get("hard_risk_group_count") == 2962
        and len(preference_rows) == 2499
        and len(hard_risk_rows) == 2962,
    ))
    checks.append(ok(
        "第 19 期全量优先专业和硬风险队列字段与状态正确",
        required_preference_fields.issubset(preference_fields)
        and required_hard_risk_fields.issubset(hard_risk_fields)
        and all(row.get("最终可用") == "false" and row.get("核验状态") == "needs_manual_pdf_review" for row in preference_rows + hard_risk_rows)
        and all(row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"] for row in preference_rows + hard_risk_rows)
        and not any(
            row.get("综合风险等级") == "未触发硬风险" and row.get("专业组风险类型")
            for row in preference_rows
        ),
    ))
    checks.append(ok(
        "第 19 期新增公开复核文件不含本地路径和身份信息",
        not any(token in review_public_text for token in shared_forbidden_tokens),
    ))

    page_packet_summary_path = ROOT / "data/working/issue19-candidate-review-page-packet-summary.json"
    page_packet_csv = ROOT / "data/working/issue19-candidate-review-page-packet.csv"
    group_page_map_csv = ROOT / "data/working/issue19-candidate-review-group-page-map.csv"
    with page_packet_csv.open(newline="", encoding="utf-8-sig") as f:
        page_packet_reader = csv.DictReader(f)
        page_packet_rows = list(page_packet_reader)
        page_packet_fields = set(page_packet_reader.fieldnames or [])
    with group_page_map_csv.open(newline="", encoding="utf-8-sig") as f:
        group_page_map_reader = csv.DictReader(f)
        group_page_map_rows = list(group_page_map_reader)
        group_page_map_fields = set(group_page_map_reader.fieldnames or [])
    page_packet_summary = json.loads(page_packet_summary_path.read_text())
    required_page_packet_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "页码",
        "页图文件名",
        "页图SHA256",
        "页面OCR文本文件名",
        "页面OCR文本SHA256",
        "关联候选专业组",
        "本页OCR专业组",
        "核验状态",
    }
    required_group_page_map_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "候选池学校专业组",
        "候选专业组代码",
        "第19期全量OCR命中",
        "候选复核页码",
        "同校第19期OCR专业组",
        "同校第19期OCR页码",
        "机器初判",
        "核验状态",
    }
    page_packet_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [page_packet_summary_path, page_packet_csv, group_page_map_csv]
    )
    page_packet_forbidden_tokens = [
        token
        for token in shared_forbidden_tokens
        if token not in {".png"}
    ]
    checks.append(ok(
        "第 19 期候选池页面复核包公开摘要正确",
        page_packet_summary.get("status") == "candidate_review_page_packet_ready_private_assets_not_committed"
        and page_packet_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and page_packet_summary.get("candidate_count") == 20
        and page_packet_summary.get("review_page_count") == 10
        and set(page_packet_summary.get("review_pages", [])) == {17, 69, 74, 80, 81, 208, 209, 212, 223, 226}
        and page_packet_summary.get("group_map_row_count") == 20
        and page_packet_summary.get("private_assets_generated_locally") is True
        and len(page_packet_rows) == 10
        and len(group_page_map_rows) == 20,
    ))
    checks.append(ok(
        "第 19 期候选池页面复核包字段和定位正确",
        required_page_packet_fields.issubset(page_packet_fields)
        and required_group_page_map_fields.issubset(group_page_map_fields)
        and all(row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"] for row in page_packet_rows + group_page_map_rows)
        and all(row.get("核验状态") == "needs_manual_pdf_review" for row in page_packet_rows)
        and all("/" not in row.get("页图文件名", "") and "/" not in row.get("页面OCR文本文件名", "") for row in page_packet_rows)
        and any(
            row.get("候选专业组代码") == "C10702" and row.get("候选复核页码") == "69"
            for row in group_page_map_rows
        )
        and any(
            row.get("候选专业组代码") == "K15123" and row.get("候选复核页码") == "208；209"
            for row in group_page_map_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选池页面复核包公开文件不含本地路径和身份信息",
        not any(token in page_packet_public_text for token in page_packet_forbidden_tokens),
    ))

    integrity_summary_path = ROOT / "data/working/issue19-integrity-audit-summary.json"
    candidate_page_code_audit_csv = ROOT / "data/working/issue19-candidate-page-code-audit.csv"
    structure_anomaly_queue_csv = ROOT / "data/working/issue19-ocr-structure-anomaly-queue.csv"
    integrity_summary = json.loads(integrity_summary_path.read_text())
    with candidate_page_code_audit_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_page_code_reader = csv.DictReader(f)
        candidate_page_code_rows = list(candidate_page_code_reader)
        candidate_page_code_fields = set(candidate_page_code_reader.fieldnames or [])
    with structure_anomaly_queue_csv.open(newline="", encoding="utf-8-sig") as f:
        structure_anomaly_reader = csv.DictReader(f)
        structure_anomaly_rows = list(structure_anomaly_reader)
        structure_anomaly_fields = set(structure_anomaly_reader.fieldnames or [])
    required_candidate_code_audit_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "候选池学校专业组",
        "候选专业组代码",
        "页面OCR是否出现候选组号",
        "全量专业组表是否出现",
        "异常规则ID",
        "异常类型",
        "严重程度",
        "核验状态",
    }
    required_structure_anomaly_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "源文件",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "字段完整性标记",
        "异常规则ID",
        "异常类型",
        "严重程度",
        "核验状态",
    }
    integrity_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [integrity_summary_path, candidate_page_code_audit_csv, structure_anomaly_queue_csv]
    )
    checks.append(ok(
        "第 19 期完整性审计摘要和行数正确",
        integrity_summary.get("status") == "issue19_integrity_audit_queues_need_manual_pdf_review"
        and integrity_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and integrity_summary.get("candidate_page_code_audit_count") == 20
        and integrity_summary.get("structure_anomaly_count") == 5129
        and integrity_summary.get("candidate_page_code_anomaly_counts") == {
            "页面与结构化均命中": 16,
            "结构化命中但页面OCR未检出组号": 1,
            "复核页未见候选组号且结构化未命中": 2,
            "页面有组号但结构化未拆出": 1,
        }
        and integrity_summary.get("structure_anomaly_rule_counts") == {
            "major_text_embeds_other_school_marker": 1022,
            "tuition_number_le_500": 1241,
            "tuition_not_plain_number": 222,
            "major_text_embeds_group_code": 32,
            "plan_count_number_ge_1000": 585,
            "plan_count_not_plain_number": 40,
            "low_ocr_confidence": 1717,
            "major_text_embeds_page_header": 170,
            "major_code_not_two_chars": 100,
        }
        and len(candidate_page_code_rows) == 20
        and len(structure_anomaly_rows) == 5129,
    ))
    checks.append(ok(
        "第 19 期完整性审计字段和关键异常正确",
        required_candidate_code_audit_fields.issubset(candidate_page_code_fields)
        and required_structure_anomaly_fields.issubset(structure_anomaly_fields)
        and all(row.get("最终可用") == "false" and row.get("核验状态") == "needs_manual_pdf_review" for row in candidate_page_code_rows + structure_anomaly_rows)
        and any(
            row.get("候选专业组代码") == "C10704"
            and row.get("异常规则ID") == "candidate_group_page_hit_structured_miss"
            and row.get("页面OCR命中页码") == "69"
            and row.get("严重程度") == "高"
            for row in candidate_page_code_rows
        )
        and any(
            row.get("候选专业组代码") == "K15123"
            and row.get("异常规则ID") == "candidate_group_missing_in_page_and_structured"
            for row in candidate_page_code_rows
        )
        and any(
            row.get("院校专业组代码OCR规范化") == "C10705"
            and row.get("专业代号OCR") == "15"
            and row.get("异常规则ID") == "major_text_embeds_other_school_marker"
            and "C108" in row.get("异常证据", "")
            for row in structure_anomaly_rows
        ),
    ))
    checks.append(ok(
        "第 19 期完整性审计公开文件不含本地路径和身份信息",
        not any(token in integrity_public_text for token in shared_forbidden_tokens),
    ))

    candidate_v2_summary_path = ROOT / "data/working/issue19-candidate-v2-review-seed-summary.json"
    candidate_v2_group_csv = ROOT / "data/working/issue19-candidate-v2-group-review-seed.csv"
    candidate_v2_major_csv = ROOT / "data/working/issue19-candidate-v2-major-review-seed.csv"
    candidate_v2_summary = json.loads(candidate_v2_summary_path.read_text())
    with candidate_v2_group_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v2_group_reader = csv.DictReader(f)
        candidate_v2_group_rows = list(candidate_v2_group_reader)
        candidate_v2_group_fields = set(candidate_v2_group_reader.fieldnames or [])
    with candidate_v2_major_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v2_major_reader = csv.DictReader(f)
        candidate_v2_major_rows = list(candidate_v2_major_reader)
        candidate_v2_major_fields = set(candidate_v2_major_reader.fieldnames or [])
    required_candidate_v2_group_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "关联类型",
        "关联原候选",
        "2026院校专业组代码",
        "院校名称",
        "来源页码",
        "证据来源",
        "专业明细行数",
        "V2定位结论",
        "核验状态",
    }
    required_candidate_v2_major_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "关联类型",
        "关联原候选",
        "2026院校专业组代码",
        "专业代号",
        "专业名称及备注",
        "专业计划数候选",
        "学费候选",
        "偏好方向",
        "风险类型",
        "核验状态",
    }
    candidate_v2_groups_by_code = {
        row.get("2026院校专业组代码"): row for row in candidate_v2_group_rows
    }
    candidate_v2_majors_by_group = {}
    for row in candidate_v2_major_rows:
        candidate_v2_majors_by_group.setdefault(row.get("2026院校专业组代码"), []).append(row)
    candidate_v2_major_codes_by_group = {
        code: [row.get("专业代号") for row in rows]
        for code, rows in candidate_v2_majors_by_group.items()
    }
    candidate_v2_zero_detail_groups = {
        row.get("2026院校专业组代码")
        for row in candidate_v2_group_rows
        if row.get("专业明细行数") == "0"
    }
    candidate_v2_suspicious_tuition_rows = [
        row
        for row in candidate_v2_major_rows
        if (
            not row.get("学费候选", "").isdigit()
            or "tuition_not_plain_number" in row.get("字段完整性标记", "")
            or "tuition_not_plain_number" in row.get("结构异常规则ID", "")
            or "tuition_number_le_500" in row.get("结构异常规则ID", "")
        )
    ]
    candidate_v2_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [candidate_v2_summary_path, candidate_v2_group_csv, candidate_v2_major_csv]
    )
    candidate_v2_forbidden_tokens = [
        token
        for token in shared_forbidden_tokens
        if token not in {".png"}
    ]
    candidate_v2_forbidden_tokens.append("/tmp/")
    checks.append(ok(
        "第 19 期候选V2逐专业明细种子摘要和行数正确",
        candidate_v2_summary.get("status") == "candidate_v2_review_seed_needs_manual_pdf_review"
        and candidate_v2_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and candidate_v2_summary.get("group_seed_count") == 23
        and candidate_v2_summary.get("major_seed_count") == 82
        and candidate_v2_summary.get("relation_type_counts") == {
            "历史候选": 20,
            "同页相邻风险组": 1,
            "同校偏好专业补充组": 2,
        }
        and candidate_v2_summary.get("evidence_source_counts") == {
            "full_ocr_draft": 68,
            "page_visual_review_seed": 14,
        }
        and len(candidate_v2_group_rows) == 23
        and len(candidate_v2_major_rows) == 82,
        f"{len(candidate_v2_group_rows)} groups, {len(candidate_v2_major_rows)} majors",
    ))
    checks.append(ok(
        "第 19 期候选V2逐专业明细种子字段和待复核状态正确",
        required_candidate_v2_group_fields.issubset(candidate_v2_group_fields)
        and required_candidate_v2_major_fields.issubset(candidate_v2_major_fields)
        and all(
            row.get("最终可用") == "false" and row.get("核验状态") == "needs_manual_pdf_review"
            for row in candidate_v2_group_rows + candidate_v2_major_rows
        )
        and all(
            row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            for row in candidate_v2_group_rows + candidate_v2_major_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V2专业组行数与逐专业明细一致",
        all(
            as_int(row.get("专业明细行数"))
            == len(candidate_v2_majors_by_group.get(row.get("2026院校专业组代码"), []))
            for row in candidate_v2_group_rows
        )
        and candidate_v2_zero_detail_groups == {"C10702", "K15123"}
        and all(
            "需回看页图逐字段确认" in row.get("页面证据", "")
            for row in candidate_v2_major_rows
            if row.get("证据来源") == "full_ocr_draft"
        ),
    ))
    checks.append(ok(
        "第 19 期候选V2关键定位结论保持保守",
        candidate_v2_groups_by_code.get("C10702", {}).get("V2定位结论")
        == "第19期候选页未见该组号，按2026组号变化/旧组号处理"
        and candidate_v2_groups_by_code.get("C10704", {}).get("证据来源") == "page_visual_review_seed"
        and candidate_v2_groups_by_code.get("C10704", {}).get("结构化命中") == "否"
        and candidate_v2_groups_by_code.get("C10704", {}).get("专业明细行数") == "3"
        and "结构化漏拆" in candidate_v2_groups_by_code.get("C10704", {}).get("V2定位结论", "")
        and candidate_v2_groups_by_code.get("K15123", {}).get("专业明细行数") == "0"
        and "2026组号变化/旧组号" in candidate_v2_groups_by_code.get("K15123", {}).get("V2定位结论", "")
        and candidate_v2_groups_by_code.get("K15114", {}).get("关联类型") == "同校偏好专业补充组"
        and candidate_v2_groups_by_code.get("K15114", {}).get("关联原候选") == "成都理工大学 K15123 第23组"
        and "数字媒体技术" in candidate_v2_groups_by_code.get("K15114", {}).get("偏好方向", "")
        and candidate_v2_groups_by_code.get("K17905", {}).get("关联类型") == "同校偏好专业补充组"
        and candidate_v2_groups_by_code.get("K17905", {}).get("关联原候选") == "成都师范学院 K17903 第03组",
    ))
    checks.append(ok(
        "第 19 期候选V2关键专业明细保持逐专业和风险可追溯",
        candidate_v2_major_codes_by_group.get("C10703") == ["05", "06", "07", "08", "09", "10", "11"]
        and candidate_v2_major_codes_by_group.get("C10704") == ["12", "13", "14"]
        and candidate_v2_major_codes_by_group.get("C10705") == ["15"]
        and candidate_v2_major_codes_by_group.get("K15114") == ["53", "54", "55"]
        and candidate_v2_major_codes_by_group.get("K15123") is None
        and any(
            row.get("专业代号") == "14"
            and row.get("专业名称及备注") == "数据科学与大数据技术"
            and row.get("专业计划数候选") == "7"
            and row.get("学费候选") == "4000"
            and row.get("偏好方向") == "计算机类相关"
            for row in candidate_v2_majors_by_group.get("C10704", [])
        )
        and any(
            row.get("专业代号") == "15"
            and row.get("学费候选") == "48000"
            and "中外合作或高收费" in row.get("风险类型", "")
            and "学费超过当前上限" in row.get("风险类型", "")
            for row in candidate_v2_majors_by_group.get("C10705", [])
        )
        and any(
            row.get("专业代号") == "53"
            and "数字媒体技术" in row.get("专业名称及备注", "")
            and row.get("专业计划数候选") == "2"
            and row.get("学费候选") == "6240"
            and "体检或色觉限制" in row.get("风险类型", "")
            for row in candidate_v2_majors_by_group.get("K15114", [])
        )
        and any(
            row.get("专业代号") == "54"
            and row.get("专业名称及备注") == "智能科学与技术（宜宾校区）"
            and row.get("专业计划数候选") == "4"
            and row.get("学费候选") == "6240"
            for row in candidate_v2_majors_by_group.get("K15114", [])
        )
        and any(
            row.get("2026院校专业组代码") == "K17905"
            and "数字媒体技术" in row.get("专业名称及备注", "")
            and row.get("证据来源") == "full_ocr_draft"
            and "major_text_embeds_page_header" in row.get("结构异常规则ID", "")
            for row in candidate_v2_major_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V2异常学费字段仍保持待复核",
        {
            row.get("2026院校专业组代码")
            for row in candidate_v2_suspicious_tuition_rows
        }.issuperset({"A03208", "K48504", "K48704"})
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "needs_manual_pdf_review"
            and row.get("结构异常规则ID")
            for row in candidate_v2_suspicious_tuition_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V2公开文件不含本地路径和身份信息",
        not any(token in candidate_v2_public_text for token in candidate_v2_forbidden_tokens),
    ))

    candidate_v2_verification_summary_path = ROOT / "data/working/issue19-candidate-v2-verification-workbench-summary.json"
    candidate_v2_verification_group_csv = ROOT / "data/working/issue19-candidate-v2-verification-group-workbench.csv"
    candidate_v2_verification_major_csv = ROOT / "data/working/issue19-candidate-v2-verification-major-workbench.csv"
    candidate_v2_verification_summary = json.loads(candidate_v2_verification_summary_path.read_text())
    with candidate_v2_verification_group_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v2_verification_group_reader = csv.DictReader(f)
        candidate_v2_verification_group_rows = list(candidate_v2_verification_group_reader)
        candidate_v2_verification_group_fields = set(candidate_v2_verification_group_reader.fieldnames or [])
    with candidate_v2_verification_major_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v2_verification_major_reader = csv.DictReader(f)
        candidate_v2_verification_major_rows = list(candidate_v2_verification_major_reader)
        candidate_v2_verification_major_fields = set(candidate_v2_verification_major_reader.fieldnames or [])
    required_candidate_v2_verification_group_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "2026院校专业组代码",
        "专业明细行数",
        "零明细原因",
        "历史投档线可沿用",
        "历史线基准来源",
        "原PDF页人工核验状态",
        "湖北官方系统/省招办计划核验状态",
        "高校官网/招生章程核验状态",
        "家庭接受度核验状态",
        "调剂结论状态",
        "全部专业已复核",
        "候选闸门状态",
        "可进入最终候选",
        "升级缺口",
    }
    required_candidate_v2_verification_major_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "2026院校专业组代码",
        "专业代号",
        "专业名称及备注",
        "专业接受度机器初判",
        "专业接受度人工确认",
        "专业闸门状态",
        "专业字段复核状态",
        "专业代号核验状态",
        "专业名称核验状态",
        "计划数核验状态",
        "学费核验状态",
        "选科核验状态",
        "备注核验状态",
        "是否允许进入最终专业列表",
        "升级缺口",
    }
    candidate_v2_verification_groups_by_code = {
        row.get("2026院校专业组代码"): row for row in candidate_v2_verification_group_rows
    }
    candidate_v2_verification_majors_by_group = {}
    for row in candidate_v2_verification_major_rows:
        candidate_v2_verification_majors_by_group.setdefault(row.get("2026院校专业组代码"), []).append(row)
    candidate_v2_verification_zero_detail_groups = {
        row.get("2026院校专业组代码")
        for row in candidate_v2_verification_group_rows
        if row.get("专业明细行数") == "0"
    }
    candidate_v2_verification_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            candidate_v2_verification_summary_path,
            candidate_v2_verification_group_csv,
            candidate_v2_verification_major_csv,
        ]
    )
    checks.append(ok(
        "第 19 期候选V2升级工作台摘要和行数正确",
        candidate_v2_verification_summary.get("status") == "candidate_v2_verification_workbench_pending_review"
        and candidate_v2_verification_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and candidate_v2_verification_summary.get("group_count") == 23
        and candidate_v2_verification_summary.get("major_count") == 82
        and candidate_v2_verification_summary.get("group_can_enter_final_count") == 0
        and candidate_v2_verification_summary.get("major_can_enter_final_count") == 0
        and set(candidate_v2_verification_summary.get("zero_detail_groups", [])) == {"C10702", "K15123"}
        and candidate_v2_verification_summary.get("group_gate_status_counts") == {"pending_verification": 23}
        and candidate_v2_verification_summary.get("major_gate_status_counts") == {"pending_verification": 82}
        and len(candidate_v2_verification_group_rows) == 23
        and len(candidate_v2_verification_major_rows) == 82,
        f"{len(candidate_v2_verification_group_rows)} groups, {len(candidate_v2_verification_major_rows)} majors",
    ))
    checks.append(ok(
        "第 19 期候选V2升级工作台字段和默认闸门状态正确",
        required_candidate_v2_verification_group_fields.issubset(candidate_v2_verification_group_fields)
        and required_candidate_v2_verification_major_fields.issubset(candidate_v2_verification_major_fields)
        and all(
            row.get("最终可用") == "false"
            and row.get("候选闸门状态") == "pending_verification"
            and row.get("可进入最终候选") == "false"
            and row.get("全部专业已复核") == "false"
            and row.get("原PDF页人工核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统/省招办计划核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/招生章程核验状态") == "pending_school_charter_review"
            and row.get("家庭接受度核验状态") == "pending_family_acceptance_review"
            and row.get("调剂结论状态") == "pending_transfer_decision"
            for row in candidate_v2_verification_group_rows
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("专业闸门状态") == "pending_verification"
            and row.get("是否允许进入最终专业列表") == "false"
            and row.get("专业接受度人工确认") == "pending_family_acceptance_review"
            and row.get("原PDF页字段核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校章程字段核验状态") == "pending_school_charter_review"
            for row in candidate_v2_verification_major_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V2升级工作台专业组明细一致且零明细组不可升级",
        all(
            as_int(row.get("专业明细行数"))
            == len(candidate_v2_verification_majors_by_group.get(row.get("2026院校专业组代码"), []))
            for row in candidate_v2_verification_group_rows
        )
        and candidate_v2_verification_zero_detail_groups == {"C10702", "K15123"}
        and all(
            row.get("零明细原因") == "group_not_found_or_code_changed"
            and row.get("历史投档线可沿用") == "false"
            and row.get("可进入最终候选") == "false"
            for row in candidate_v2_verification_group_rows
            if row.get("2026院校专业组代码") in {"C10702", "K15123"}
        ),
    ))
    checks.append(ok(
        "第 19 期候选V2升级工作台重点组闸门正确",
        candidate_v2_verification_groups_by_code.get("C10704", {}).get("证据来源") == "page_visual_review_seed"
        and candidate_v2_verification_groups_by_code.get("C10704", {}).get("结构化命中") == "否"
        and candidate_v2_verification_groups_by_code.get("C10704", {}).get("历史线基准来源") == "pending_structured_group_repair"
        and candidate_v2_verification_groups_by_code.get("K15114", {}).get("历史投档线可沿用") == "false"
        and candidate_v2_verification_groups_by_code.get("K15114", {}).get("历史线基准来源") == "pending_new_group_evidence"
        and candidate_v2_verification_groups_by_code.get("K17905", {}).get("历史投档线可沿用") == "false"
        and candidate_v2_verification_groups_by_code.get("K17905", {}).get("字段异常专业数") == "1"
        and candidate_v2_verification_groups_by_code.get("K17905", {}).get("候选闸门状态") == "pending_verification"
        and any(
            row.get("2026院校专业组代码") == "K17905"
            and row.get("专业闸门状态") == "pending_verification"
            and row.get("专业接受度机器初判") == "字段异常待核验"
            and "major_text_embeds_page_header" in row.get("结构异常规则ID", "")
            for row in candidate_v2_verification_major_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V2升级工作台专业接受度阻断原因完整",
        all(row.get("专业接受度机器初判") for row in candidate_v2_verification_major_rows)
        and all(
            row.get("阻断原因")
            for row in candidate_v2_verification_major_rows
            if row.get("专业接受度机器初判") in {"默认不能接受", "默认不进主方案"}
        )
        and all(
            row.get("风险说明")
            for row in candidate_v2_verification_major_rows
            if row.get("专业接受度机器初判") == "限制风险待核验"
        ),
    ))
    checks.append(ok(
        "第 19 期候选V2升级工作台公开文件不含本地路径、身份信息和 final_allowed",
        "final_allowed" not in candidate_v2_verification_public_text
        and not any(token in candidate_v2_verification_public_text for token in candidate_v2_forbidden_tokens),
    ))

    candidate_v2_evidence_summary_path = ROOT / "data/working/issue19-candidate-v2-evidence-ledger-summary.json"
    candidate_v2_field_ledger_csv = ROOT / "data/working/issue19-candidate-v2-field-review-ledger.csv"
    candidate_v2_triangulation_csv = ROOT / "data/working/issue19-candidate-v2-triangulation-matrix.csv"
    candidate_v2_evidence_summary = json.loads(candidate_v2_evidence_summary_path.read_text())
    with candidate_v2_field_ledger_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v2_field_ledger_reader = csv.DictReader(f)
        candidate_v2_field_ledger_rows = list(candidate_v2_field_ledger_reader)
        candidate_v2_field_ledger_fields = set(candidate_v2_field_ledger_reader.fieldnames or [])
    with candidate_v2_triangulation_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v2_triangulation_reader = csv.DictReader(f)
        candidate_v2_triangulation_rows = list(candidate_v2_triangulation_reader)
        candidate_v2_triangulation_fields = set(candidate_v2_triangulation_reader.fieldnames or [])

    required_candidate_v2_field_ledger_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "复核状态",
        "复核任务ID",
        "复核对象类型",
        "字段类别",
        "字段名称",
        "关联类型",
        "关联原候选",
        "院校代码",
        "院校名称",
        "2026院校专业组代码",
        "专业组出现ID",
        "专业行ID",
        "组内序号",
        "专业代号",
        "专业名称及备注",
        "来源页码",
        "证据来源",
        "OCR原值",
        "OCR风险提示",
        "原PDF人工确认值",
        "湖北官方系统确认值",
        "高校官网/章程确认值",
        "家庭确认值",
        "私有证据编号",
        "字段核验状态",
        "是否阻断候选升级",
        "复核优先级",
    }
    required_candidate_v2_triangulation_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "证据矩阵ID",
        "关联类型",
        "关联原候选",
        "院校代码",
        "院校名称",
        "2026院校专业组代码",
        "来源页码",
        "专业明细行数",
        "字段复核任务数",
        "字段P0任务数",
        "原PDF页证据状态",
        "湖北官方系统证据状态",
        "高校官网/章程证据状态",
        "家庭接受度证据状态",
        "调剂结论状态",
        "三年历史线证据状态",
        "第19期PDF底座状态",
        "组内调剂机器初判",
        "历史投档线可沿用",
        "候选闸门状态",
        "可进入最终候选",
        "升级缺口",
    }
    candidate_v2_field_rows_by_group = {}
    candidate_v2_p0_field_rows_by_group = {}
    for row in candidate_v2_field_ledger_rows:
        group_code = row.get("2026院校专业组代码")
        candidate_v2_field_rows_by_group[group_code] = candidate_v2_field_rows_by_group.get(group_code, 0) + 1
        if row.get("复核优先级") == "P0-字段必须优先核":
            candidate_v2_p0_field_rows_by_group[group_code] = (
                candidate_v2_p0_field_rows_by_group.get(group_code, 0) + 1
            )
    candidate_v2_triangulation_by_code = {
        row.get("2026院校专业组代码"): row for row in candidate_v2_triangulation_rows
    }
    candidate_v2_evidence_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            candidate_v2_evidence_summary_path,
            candidate_v2_field_ledger_csv,
            candidate_v2_triangulation_csv,
        ]
    )
    checks.append(ok(
        "第 19 期候选V2证据总账摘要和行数正确",
        candidate_v2_evidence_summary.get("status")
        == "candidate_v2_evidence_ledgers_pending_manual_review"
        and candidate_v2_evidence_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and candidate_v2_evidence_summary.get("group_count") == 23
        and candidate_v2_evidence_summary.get("major_count") == 82
        and candidate_v2_evidence_summary.get("field_review_task_count") == 840
        and candidate_v2_evidence_summary.get("group_field_review_task_count") == 184
        and candidate_v2_evidence_summary.get("major_field_review_task_count") == 656
        and candidate_v2_evidence_summary.get("triangulation_matrix_count") == 23
        and candidate_v2_evidence_summary.get("field_review_status_counts") == {"pending": 840}
        and candidate_v2_evidence_summary.get("field_review_priority_counts") == {
            "P0-字段必须优先核": 494,
            "P1-字段高优先核": 296,
            "P2-字段常规核": 42,
            "P3-字段常规核": 8,
        }
        and candidate_v2_evidence_summary.get("major_full_workbench_match_status_counts") == {
            "exact_full_major_match": 75,
            "not_in_full_major_workbench": 7,
        }
        and candidate_v2_evidence_summary.get("final_available_count") == 0
        and candidate_v2_evidence_summary.get("candidate_can_enter_final_count") == 0
        and len(candidate_v2_field_ledger_rows) == 840
        and len(candidate_v2_triangulation_rows) == 23,
        f"{len(candidate_v2_field_ledger_rows)} field tasks, {len(candidate_v2_triangulation_rows)} matrix rows",
    ))
    checks.append(ok(
        "第 19 期候选V2证据总账字段、主键和待核状态正确",
        required_candidate_v2_field_ledger_fields.issubset(candidate_v2_field_ledger_fields)
        and required_candidate_v2_triangulation_fields.issubset(candidate_v2_triangulation_fields)
        and len({row.get("复核任务ID") for row in candidate_v2_field_ledger_rows})
        == len(candidate_v2_field_ledger_rows)
        and len({row.get("证据矩阵ID") for row in candidate_v2_triangulation_rows})
        == len(candidate_v2_triangulation_rows)
        and all(
            row.get("最终可用") == "false"
            and row.get("字段核验状态") == "pending"
            and row.get("是否阻断候选升级") == "是"
            and row.get("私有证据编号") == ""
            for row in candidate_v2_field_ledger_rows
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("候选闸门状态") == "pending_verification"
            and row.get("可进入最终候选") == "false"
            and row.get("原PDF页证据状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统证据状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/章程证据状态") == "pending_school_charter_review"
            and row.get("家庭接受度证据状态") == "pending_family_acceptance_review"
            and row.get("调剂结论状态") == "pending_transfer_decision"
            for row in candidate_v2_triangulation_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V2证据矩阵与字段总账聚合一致",
        all(
            as_int(row.get("字段复核任务数"))
            == candidate_v2_field_rows_by_group.get(row.get("2026院校专业组代码"), 0)
            and as_int(row.get("字段P0任务数"))
            == candidate_v2_p0_field_rows_by_group.get(row.get("2026院校专业组代码"), 0)
            for row in candidate_v2_triangulation_rows
        )
        and candidate_v2_triangulation_by_code.get("C10702", {}).get("字段复核任务数") == "8"
        and candidate_v2_triangulation_by_code.get("K15123", {}).get("字段复核任务数") == "8"
        and candidate_v2_triangulation_by_code.get("C10704", {}).get("专业明细行数") == "3"
        and candidate_v2_triangulation_by_code.get("K15114", {}).get("三年历史线证据状态")
        == "pending_new_group_evidence",
    ))
    checks.append(ok(
        "第 19 期候选V2证据总账专业行ID匹配口径正确",
        sum(
            row.get("复核对象类型") == "专业字段"
            and "exact_full_major_match" in row.get("证据来源", "")
            and bool(row.get("专业行ID"))
            for row in candidate_v2_field_ledger_rows
        )
        == 75 * 8
        and sum(
            row.get("复核对象类型") == "专业字段"
            and "not_in_full_major_workbench" in row.get("证据来源", "")
            and not row.get("专业行ID")
            for row in candidate_v2_field_ledger_rows
        )
        == 7 * 8,
    ))
    checks.append(ok(
        "第 19 期候选V2证据总账公开文件不含本地路径、身份信息和最终可用结论",
        "final_allowed" not in candidate_v2_evidence_public_text
        and "ready_for_discussion" not in candidate_v2_evidence_public_text
        and "已确认" not in candidate_v2_evidence_public_text
        and not any(token in candidate_v2_evidence_public_text for token in candidate_v2_forbidden_tokens),
    ))

    full_quality_summary_path = ROOT / "data/working/issue19-full-quality-tier-summary.json"
    full_quality_group_csv = ROOT / "data/working/issue19-full-quality-group-tiers.csv"
    full_quality_queue_csv = ROOT / "data/working/issue19-full-quality-review-queue.csv"
    full_quality_summary = json.loads(full_quality_summary_path.read_text())
    with full_quality_group_csv.open(newline="", encoding="utf-8-sig") as f:
        full_quality_group_reader = csv.DictReader(f)
        full_quality_group_rows = list(full_quality_group_reader)
        full_quality_group_fields = set(full_quality_group_reader.fieldnames or [])
    with full_quality_queue_csv.open(newline="", encoding="utf-8-sig") as f:
        full_quality_queue_reader = csv.DictReader(f)
        full_quality_queue_rows = list(full_quality_queue_reader)
        full_quality_queue_fields = set(full_quality_queue_reader.fieldnames or [])
    (
        full_group_id_by_row_index,
        full_major_group_ids,
        full_unmatched_major_group_count,
        full_fallback_unique_group_code_major_count,
    ) = issue19_assign_group_occurrence_ids(
        full_group_rows, full_major_rows, issue19_source["source"]["sha256"]
    )
    full_quality_groups_by_code = {}
    for row in full_quality_group_rows:
        full_quality_groups_by_code.setdefault(row.get("院校专业组代码OCR规范化"), []).append(row)
    full_group_codes = {row.get("院校专业组代码OCR规范化") for row in full_group_rows}
    full_group_code_counts = Counter(row.get("院校专业组代码OCR规范化") for row in full_group_rows)
    full_quality_group_code_counts = Counter(
        row.get("院校专业组代码OCR规范化") for row in full_quality_group_rows
    )
    full_group_signatures = Counter(
        (
            row.get("院校代码"),
            row.get("院校专业组代码OCR规范化"),
            row.get("来源页码"),
            row.get("专业组标题行号"),
            row.get("OCR专业行数"),
            row.get("专业组标题OCR原文"),
        )
        for row in full_group_rows
    )
    full_quality_group_signatures = Counter(
        (
            row.get("院校代码"),
            row.get("院校专业组代码OCR规范化"),
            row.get("来源页码"),
            row.get("专业组标题行号"),
            row.get("OCR专业行数_组表"),
            row.get("专业组标题OCR原文"),
        )
        for row in full_quality_group_rows
    )
    full_quality_group_occurrence_ids = {
        row.get("专业组出现ID") for row in full_quality_group_rows
    }
    full_quality_major_count_by_group = Counter(
        full_major_group_ids[index]
        for index in range(1, len(full_major_rows) + 1)
        if index in full_major_group_ids
    )
    full_major_group_id_by_key = {
        issue19_major_match_key(row): full_major_group_ids[index]
        for index, row in enumerate(full_major_rows, start=1)
        if index in full_major_group_ids
    }
    full_quality_anomaly_count_by_group = Counter(
        full_major_group_id_by_key[issue19_major_match_key(row)]
        for row in structure_anomaly_rows
        if issue19_major_match_key(row) in full_major_group_id_by_key
    )
    full_quality_high_anomaly_count_by_group = Counter(
        full_major_group_id_by_key[issue19_major_match_key(row)]
        for row in structure_anomaly_rows
        if row.get("严重程度") == "高"
        and issue19_major_match_key(row) in full_major_group_id_by_key
    )
    required_full_quality_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "专业组出现ID",
        "专业组源行号",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组标题OCR原文",
        "来源页码",
        "版面列",
        "专业组标题行号",
        "OCR专业行数_组表",
        "专业明细行数_专业表",
        "专业行数是否一致",
        "规范化专业组代码是否重复",
        "规范化专业组代码重复行数",
        "相对质量层级",
        "复核优先级",
        "结构异常数",
        "高严重结构异常数",
        "偏好专业命中数",
        "偏好方向列表",
        "硬风险命中",
        "硬风险类型列表",
    }
    full_quality_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [full_quality_summary_path, full_quality_group_csv, full_quality_queue_csv]
    )
    checks.append(ok(
        "第 19 期全量专业组质量分层摘要和行数正确",
        full_quality_summary.get("status") == "full_quality_tiers_need_manual_pdf_review"
        and full_quality_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and full_quality_summary.get("group_count") == 3329
        and full_quality_summary.get("major_count") == 13736
        and full_quality_summary.get("review_queue_count") == 3300
        and full_quality_summary.get("quality_tier_counts") == {
            "Q1-高风险结构异常": 1552,
            "Q4-结构相对完整待抽检": 245,
            "Q0-无专业明细": 40,
            "Q3-字段待核": 998,
            "Q2-重点候选字段待核": 494,
        }
        and full_quality_summary.get("review_priority_counts") == {
            "P0-必须优先核页": 3295,
            "P3-相对完整但仍需核页": 29,
            "P1-高优先核页": 5,
        }
        and full_quality_summary.get("groups_with_any_structure_anomaly") == 2147
        and full_quality_summary.get("groups_with_high_structure_anomaly") == 1552
        and full_quality_summary.get("groups_with_no_major_detail") == 40
        and full_quality_summary.get("duplicate_normalized_group_code_count") == 3
        and full_quality_summary.get("duplicate_normalized_group_code_row_count") == 6
        and full_quality_summary.get("unmatched_major_group_occurrence_count") == 0
        and full_quality_summary.get("fallback_unique_group_code_major_count") == 1838
        and full_quality_summary.get("candidate_v1_hit_group_count") == 17
        and full_quality_summary.get("preference_hit_group_count") == 1312
        and full_quality_summary.get("risk_hit_group_count") == 2962
        and len(full_quality_group_rows) == 3329
        and len(full_quality_queue_rows) == 3300,
        f"{len(full_quality_group_rows)} groups, {len(full_quality_queue_rows)} queue rows",
    ))
    checks.append(ok(
        "第 19 期全量专业组质量分层字段、状态和覆盖正确",
        required_full_quality_fields.issubset(full_quality_group_fields)
        and required_full_quality_fields.issubset(full_quality_queue_fields)
        and len(full_quality_group_code_counts) == len(full_group_codes)
        and set(full_quality_groups_by_code) == full_group_codes
        and full_quality_group_code_counts == full_group_code_counts
        and full_quality_group_signatures == full_group_signatures
        and full_quality_group_occurrence_ids == set(full_group_id_by_row_index.values())
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "needs_manual_pdf_review"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("专业组出现ID")
            == full_group_id_by_row_index[as_int(row.get("专业组源行号")) - 1]
            and row.get("规范化专业组代码重复行数")
            == str(full_group_code_counts[row.get("院校专业组代码OCR规范化")])
            and (
                row.get("规范化专业组代码是否重复") == "是"
                if full_group_code_counts[row.get("院校专业组代码OCR规范化")] > 1
                else row.get("规范化专业组代码是否重复") == "否"
            )
            for row in full_quality_group_rows + full_quality_queue_rows
        ),
    ))
    checks.append(ok(
        "第 19 期全量专业组质量分层聚合与明细/异常队列一致",
        all(
            as_int(row.get("专业明细行数_专业表"))
            == full_quality_major_count_by_group[row.get("专业组出现ID")]
            and as_int(row.get("结构异常数"))
            == full_quality_anomaly_count_by_group[row.get("专业组出现ID")]
            and as_int(row.get("高严重结构异常数"))
            == full_quality_high_anomaly_count_by_group[row.get("专业组出现ID")]
            for row in full_quality_group_rows
        )
        and full_quality_summary.get("preference_hit_group_count")
        == sum(as_int(row.get("偏好专业命中数")) > 0 for row in full_quality_group_rows)
        and sum(
            bool(row.get("偏好方向列表")) and not (as_int(row.get("偏好专业命中数")) > 0)
            for row in full_quality_group_rows
        ) == 0
        and all(
            (
                row.get("专业行数是否一致") == "是"
                and row.get("OCR专业行数_组表") == row.get("专业明细行数_专业表")
            )
            or (
                row.get("专业行数是否一致") == "否"
                and row.get("OCR专业行数_组表") != row.get("专业明细行数_专业表")
                and "组表专业行数与明细表聚合不一致" in row.get("优先级原因说明", "")
            )
            for row in full_quality_group_rows
        ),
    ))
    checks.append(ok(
        "第 19 期全量专业组质量分层 P0 触发规则保持保守",
        all(
            row.get("复核优先级") == "P0-必须优先核页"
            for row in full_quality_group_rows
            if (
                as_int(row.get("专业明细行数_专业表")) == 0
                or as_int(row.get("高严重结构异常数")) > 0
                or row.get("候选池V1命中") == "是"
                or bool(row.get("偏好方向列表"))
                or row.get("硬风险命中") == "是"
                or as_int(row.get("异常学费专业数")) > 0
                or as_int(row.get("缺再选科目专业数")) > 0
                or as_int(row.get("缺计划数专业数")) > 0
                or row.get("规范化专业组代码是否重复") == "是"
                or row.get("专业行数是否一致") == "否"
            )
        )
        and full_quality_groups_by_code.get("C10703", [{}])[0].get("复核优先级") == "P0-必须优先核页"
        and full_quality_groups_by_code.get("C10705", [{}])[0].get("复核优先级") == "P0-必须优先核页"
        and full_quality_groups_by_code.get("K15114", [{}])[0].get("复核优先级") == "P0-必须优先核页"
        and full_quality_groups_by_code.get("K17905", [{}])[0].get("复核优先级") == "P0-必须优先核页",
    ))
    checks.append(ok(
        "第 19 期全量专业组质量分层公开文件不含本地路径、身份信息和最终可用结论",
        "final_allowed" not in full_quality_public_text
        and "ready_for_discussion" not in full_quality_public_text
        and "已确认" not in full_quality_public_text
        and not any(token in full_quality_public_text for token in shared_forbidden_tokens),
    ))

    major_quality_summary_path = ROOT / "data/working/issue19-full-major-detail-quality-summary.json"
    major_quality_workbench_csv = ROOT / "data/working/issue19-full-major-detail-quality-workbench.csv"
    major_quality_queue_csv = ROOT / "data/working/issue19-full-major-detail-review-queue.csv"
    major_quality_summary = json.loads(major_quality_summary_path.read_text())
    with major_quality_workbench_csv.open(newline="", encoding="utf-8-sig") as f:
        major_quality_reader = csv.DictReader(f)
        major_quality_rows = list(major_quality_reader)
        major_quality_fields = set(major_quality_reader.fieldnames or [])
    with major_quality_queue_csv.open(newline="", encoding="utf-8-sig") as f:
        major_quality_queue_reader = csv.DictReader(f)
        major_quality_queue_rows = list(major_quality_queue_reader)
        major_quality_queue_fields = set(major_quality_queue_reader.fieldnames or [])

    required_major_quality_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "专业行ID",
        "专业组出现ID",
        "专业明细源行号",
        "专业组内专业序号",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组标题OCR原文",
        "来源页码",
        "版面列",
        "专业组标题行号",
        "专业组标题y",
        "专业起始行号",
        "专业起始y",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "专业计划数OCR数字候选",
        "专业计划数是否纯数字",
        "学费OCR候选",
        "学费OCR数字候选",
        "学费是否纯数字",
        "OCR置信度",
        "专业偏好和风险标签原文",
        "专业偏好方向",
        "专业风险类型",
        "专业风险等级",
        "专业字段完整性标记",
        "专业字段完整性问题数",
        "专业行结构异常数",
        "专业行高严重结构异常数",
        "专业行异常规则ID列表",
        "专业行异常类型列表",
        "专业关注类型",
        "逐专业复核优先级",
        "逐专业复核原因说明",
        "组质量匹配方式",
        "组相对质量层级",
        "组复核优先级",
        "组优先级原因说明",
        "规范化专业组代码是否重复",
        "规范化专业组代码重复行数",
        "专业行候选池V1命中",
        "专业行样本学校命中",
        "下一步",
    }
    full_quality_by_occurrence_id = {
        row.get("专业组出现ID"): row for row in full_quality_group_rows
    }
    anomaly_count_by_major_key = Counter(issue19_major_match_key(row) for row in structure_anomaly_rows)
    high_anomaly_count_by_major_key = Counter(
        issue19_major_match_key(row)
        for row in structure_anomaly_rows
        if row.get("严重程度") == "高"
    )
    major_quality_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [major_quality_summary_path, major_quality_workbench_csv, major_quality_queue_csv]
    )
    checks.append(ok(
        "第 19 期逐专业明细质量工作台摘要和行数正确",
        major_quality_summary.get("status") == "full_major_detail_quality_need_manual_pdf_review"
        and major_quality_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and major_quality_summary.get("major_count") == 13736
        and major_quality_summary.get("review_queue_count") == 13705
        and major_quality_summary.get("matched_anomaly_count") == 5129
        and major_quality_summary.get("unmatched_anomaly_count") == 0
        and major_quality_summary.get("unmatched_group_quality_count") == 0
        and major_quality_summary.get("unmatched_major_group_occurrence_count") == 0
        and major_quality_summary.get("fallback_unique_group_code_major_count") == 1838
        and major_quality_summary.get("unique_major_line_id_count") == 13736
        and major_quality_summary.get("unique_group_occurrence_id_count") == 3289
        and major_quality_summary.get("major_review_priority_counts") == {
            "P0-逐专业必须核页": 13700,
            "P3-逐专业相对完整但仍需核页": 31,
            "P1-逐专业高优先核页": 5,
        }
        and major_quality_summary.get("major_attention_type_counts") == {
            "字段或结构异常待核验": 7678,
            "明确排除方向待人工确认": 1499,
            "偏好方向待研究": 2043,
            "普通明细待核页": 533,
            "费用或合作办学风险待确认": 702,
            "限制条件待确认": 1281,
        }
        and major_quality_summary.get("major_rows_with_structure_anomaly") == 4409
        and major_quality_summary.get("major_rows_with_high_structure_anomaly") == 2862
        and major_quality_summary.get("preference_major_row_count") == 2499
        and major_quality_summary.get("risk_major_row_count") == 3482
        and major_quality_summary.get("candidate_v1_major_row_count") == 77
        and major_quality_summary.get("duplicate_group_code_major_row_count") == 14
        and len(major_quality_rows) == 13736
        and len(major_quality_queue_rows) == 13705,
        f"{len(major_quality_rows)} majors, {len(major_quality_queue_rows)} queue rows",
    ))
    checks.append(ok(
        "第 19 期逐专业明细质量工作台字段、状态和主键正确",
        required_major_quality_fields.issubset(major_quality_fields)
        and required_major_quality_fields.issubset(major_quality_queue_fields)
        and len({row.get("专业行ID") for row in major_quality_rows}) == len(major_quality_rows)
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "needs_manual_pdf_review"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("专业行ID")
            == issue19_major_line_id(
                full_major_rows[as_int(row.get("专业明细源行号")) - 2],
                as_int(row.get("专业明细源行号")) - 1,
                issue19_source["source"]["sha256"],
            )
            and row.get("专业组出现ID")
            == full_major_group_ids[as_int(row.get("专业明细源行号")) - 1]
            for row in major_quality_rows + major_quality_queue_rows
        ),
    ))
    checks.append(ok(
        "第 19 期逐专业明细质量工作台原始明细、组质量和异常闭环正确",
        all(
            (
                row.get("院校代码"),
                row.get("院校专业组代码OCR规范化"),
                row.get("专业代号OCR"),
                row.get("专业名称及备注OCR"),
                row.get("来源页码"),
                row.get("版面列"),
                row.get("专业计划数OCR候选"),
                row.get("学费OCR候选"),
            )
            == issue19_major_match_key(full_major_rows[as_int(row.get("专业明细源行号")) - 2])
            and row.get("组复核优先级")
            == full_quality_by_occurrence_id[row.get("专业组出现ID")].get("复核优先级")
            and row.get("组相对质量层级")
            == full_quality_by_occurrence_id[row.get("专业组出现ID")].get("相对质量层级")
            and as_int(row.get("专业行结构异常数"))
            == anomaly_count_by_major_key[
                issue19_major_match_key(full_major_rows[as_int(row.get("专业明细源行号")) - 2])
            ]
            and as_int(row.get("专业行高严重结构异常数"))
            == high_anomaly_count_by_major_key[
                issue19_major_match_key(full_major_rows[as_int(row.get("专业明细源行号")) - 2])
            ]
            for row in major_quality_rows
        )
        and sum(as_int(row.get("专业行结构异常数")) for row in major_quality_rows) == 5129
        and sum(as_int(row.get("专业行高严重结构异常数")) for row in major_quality_rows)
        == sum(1 for row in structure_anomaly_rows if row.get("严重程度") == "高"),
    ))
    checks.append(ok(
        "第 19 期逐专业明细质量工作台字段完整性统计正确",
        sum(not row.get("专业名称及备注OCR") for row in major_quality_rows) == 2
        and sum(not row.get("再选科目OCR候选") for row in major_quality_rows) == 11456
        and sum(not row.get("专业计划数OCR候选") for row in major_quality_rows) == 5739
        and sum(not row.get("学费OCR候选") for row in major_quality_rows) == 1040
        and sum(row.get("专业计划数是否纯数字") == "否" for row in major_quality_rows) == 5779
        and sum(row.get("学费是否纯数字") == "否" for row in major_quality_rows) == 1262
        and sum(row.get("专业行候选池V1命中") == "是" for row in major_quality_rows) == 77
        and sum(row.get("专业行样本学校命中") == "是" for row in major_quality_rows) == 560,
    ))
    checks.append(ok(
        "第 19 期逐专业明细质量工作台 P0 触发规则保持保守",
        all(
            row.get("逐专业复核优先级") == "P0-逐专业必须核页"
            for row in major_quality_rows
            if (
                row.get("组复核优先级") == "P0-必须优先核页"
                or as_int(row.get("专业行高严重结构异常数")) > 0
                or bool(row.get("专业偏好方向"))
                or row.get("专业风险等级") != "未触发硬风险"
                or row.get("专业计划数是否纯数字") == "否"
                or row.get("学费是否纯数字") == "否"
                or "missing_subject_candidate" in row.get("专业字段完整性标记", "")
                or "missing_plan_count_candidate" in row.get("专业字段完整性标记", "")
                or "missing_tuition_candidate" in row.get("专业字段完整性标记", "")
            )
        ),
    ))
    checks.append(ok(
        "第 19 期逐专业明细质量工作台公开文件不含本地路径、身份信息和最终可用结论",
        "final_allowed" not in major_quality_public_text
        and "ready_for_discussion" not in major_quality_public_text
        and "已确认" not in major_quality_public_text
        and not any(token in major_quality_public_text for token in shared_forbidden_tokens),
    ))

    family_fit_summary_path = ROOT / "data/working/issue19-family-fit-screen-summary.json"
    family_fit_group_csv = ROOT / "data/working/issue19-family-fit-group-screen.csv"
    family_fit_major_csv = ROOT / "data/working/issue19-family-fit-major-detail.csv"
    family_fit_summary = json.loads(family_fit_summary_path.read_text())
    with family_fit_group_csv.open(newline="", encoding="utf-8-sig") as f:
        family_fit_group_reader = csv.DictReader(f)
        family_fit_group_rows = list(family_fit_group_reader)
        family_fit_group_fields = set(family_fit_group_reader.fieldnames or [])
    with family_fit_major_csv.open(newline="", encoding="utf-8-sig") as f:
        family_fit_major_reader = csv.DictReader(f)
        family_fit_major_rows = list(family_fit_major_reader)
        family_fit_major_fields = set(family_fit_major_reader.fieldnames or [])
    required_family_fit_group_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "家庭偏好版本",
        "预算上限元",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组出现ID",
        "办学属性核验状态",
        "专业明细行数",
        "组内招生明细OCR",
        "偏好专业数",
        "医学护理排除专业数",
        "高收费或超预算专业数",
        "机器家庭匹配初判",
        "调剂初判",
        "下一轮复核优先级",
    }
    required_family_fit_major_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "家庭偏好版本",
        "预算上限元",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业偏好方向",
        "专业风险类型",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "调剂影响初判",
        "家庭接受度核验状态",
    }
    family_fit_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [family_fit_summary_path, family_fit_group_csv, family_fit_major_csv]
    )
    family_fit_major_rows_by_group = Counter(row.get("专业组出现ID") for row in family_fit_major_rows)
    family_fit_preference_rows_by_group = Counter(
        row.get("专业组出现ID") for row in family_fit_major_rows if row.get("专业偏好方向")
    )
    family_fit_medical_rows_by_group = Counter(
        row.get("专业组出现ID")
        for row in family_fit_major_rows
        if row.get("机器专业接受度初判") == "默认不能接受-医学护理等排除方向"
    )
    family_fit_high_fee_rows_by_group = Counter(
        row.get("专业组出现ID")
        for row in family_fit_major_rows
        if row.get("机器专业接受度初判") == "默认不能接受-高收费或超预算"
    )
    family_fit_major_acceptance_counts = Counter(
        row.get("机器专业接受度初判") for row in family_fit_major_rows
    )
    family_fit_group_fit_counts = Counter(row.get("机器家庭匹配初判") for row in family_fit_group_rows)
    family_fit_transfer_counts = Counter(row.get("调剂初判") for row in family_fit_group_rows)
    family_fit_priority_counts = Counter(row.get("下一轮复核优先级") for row in family_fit_group_rows)
    checks.append(ok(
        "第 19 期家庭底线筛选表摘要和行数正确",
        family_fit_summary.get("status") == "issue19_family_fit_screen_ocr_draft_needs_manual_review"
        and family_fit_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and family_fit_summary.get("family_preference_version") == family_preferences.get("last_updated")
        and family_fit_summary.get("tuition_limit_yuan") == 15000
        and family_fit_summary.get("group_count") == 3329
        and family_fit_summary.get("major_count") == 13736
        and family_fit_summary.get("groups_with_preference_major_count") == 1312
        and family_fit_summary.get("groups_with_digital_media_count") == 78
        and family_fit_summary.get("groups_with_computer_count") == 1032
        and family_fit_summary.get("groups_with_teacher_count") == 391
        and family_fit_summary.get("groups_default_not_main_plan_count") == 1467
        and family_fit_summary.get("groups_priority_review_without_auto_block_count") == 590
        and family_fit_summary.get("group_fit_counts") == {
            "优先复核-有偏好专业且未触发自动阻断": 590,
            "普通备选待了解-未命中当前偏好且未触发自动阻断": 779,
            "暂不可判断-无专业明细": 40,
            "暂缓进入主方案-组内存在特殊限制待核专业": 453,
            "默认不进主方案-组内存在医学/护理等排除专业": 752,
            "默认不进主方案-组内存在高收费/超预算专业": 715,
        }
        and family_fit_summary.get("transfer_judgement_counts") == {
            "不可判断-无专业明细": 40,
            "可进入人工调剂接受度判断": 801,
            "暂不判断-特殊限制待核": 453,
            "暂不判断-组内存在学费字段待核": 37,
            "暂不判断-组内结构异常需先核页": 531,
            "调剂风险线索-组内存在默认不能接受专业": 1467,
        }
        and family_fit_summary.get("next_round_priority_counts") == {
            "R0-历史候选优先复核": 17,
            "R1-偏好专业且未自动阻断": 792,
            "R2-偏好专业但有硬风险先核风险": 514,
            "R3-普通备选或保底扩展待了解": 1064,
            "R4-默认不进主方案低优先": 942,
        }
        and family_fit_summary.get("major_acceptance_counts") == {
            "优先了解-命中当前偏好方向": 1726,
            "待了解-未命中当前偏好方向": 7279,
            "暂缓判断-特殊限制待核": 1215,
            "默认不能接受-医学护理等排除方向": 1499,
            "默认不能接受-高收费或超预算": 2017,
        }
        and len(family_fit_group_rows) == 3329
        and len(family_fit_major_rows) == 13736,
        f"{len(family_fit_group_rows)} groups, {len(family_fit_major_rows)} majors",
    ))
    checks.append(ok(
        "第 19 期家庭底线筛选表字段、状态和主键正确",
        required_family_fit_group_fields.issubset(family_fit_group_fields)
        and required_family_fit_major_fields.issubset(family_fit_major_fields)
        and {row.get("专业组出现ID") for row in family_fit_group_rows}
        == {row.get("专业组出现ID") for row in full_quality_group_rows}
        and {row.get("专业行ID") for row in family_fit_major_rows}
        == {row.get("专业行ID") for row in major_quality_rows}
        and len({row.get("专业行ID") for row in family_fit_major_rows}) == 13736
        and family_fit_major_acceptance_counts == Counter(
            family_fit_summary.get("major_acceptance_counts", {})
        )
        and family_fit_group_fit_counts == Counter(family_fit_summary.get("group_fit_counts", {}))
        and family_fit_transfer_counts == Counter(family_fit_summary.get("transfer_judgement_counts", {}))
        and family_fit_priority_counts == Counter(family_fit_summary.get("next_round_priority_counts", {}))
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "needs_manual_pdf_review"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("家庭偏好版本") == family_preferences.get("last_updated")
            and row.get("办学属性核验状态") == "pending_school_attribute_review"
            for row in family_fit_group_rows
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "needs_manual_pdf_review"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("家庭接受度核验状态") == "pending_family_acceptance_review"
            for row in family_fit_major_rows
        ),
    ))
    checks.append(ok(
        "第 19 期家庭底线筛选表聚合与逐专业明细一致",
        all(
            as_int(row.get("专业明细行数")) == family_fit_major_rows_by_group[row.get("专业组出现ID")]
            and as_int(row.get("偏好专业数")) == family_fit_preference_rows_by_group[row.get("专业组出现ID")]
            and as_int(row.get("医学护理排除专业数")) == family_fit_medical_rows_by_group[row.get("专业组出现ID")]
            and as_int(row.get("高收费或超预算专业数")) == family_fit_high_fee_rows_by_group[row.get("专业组出现ID")]
            and (
                (as_int(row.get("专业明细行数")) == 0 and not row.get("组内招生明细OCR"))
                or (as_int(row.get("专业明细行数")) > 0 and "专业行ID:" in row.get("组内招生明细OCR", ""))
            )
            for row in family_fit_group_rows
        )
        and sum(as_int(row.get("偏好专业数")) > 0 for row in family_fit_group_rows) == 1312,
    ))
    checks.append(ok(
        "第 19 期家庭底线筛选表公开文件不含本地路径、身份信息和最终可用结论",
        "final_allowed" not in family_fit_public_text
        and "ready_for_discussion" not in family_fit_public_text
        and "已确认" not in family_fit_public_text
        and not any(token in family_fit_public_text for token in shared_forbidden_tokens),
    ))

    candidate_v3_summary_path = ROOT / "data/working/issue19-candidate-v3-review-intake-summary.json"
    candidate_v3_csv = ROOT / "data/working/issue19-candidate-v3-review-intake.csv"
    candidate_v3_summary = json.loads(candidate_v3_summary_path.read_text())
    with candidate_v3_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v3_reader = csv.DictReader(f)
        candidate_v3_rows = list(candidate_v3_reader)
        candidate_v3_fields = set(candidate_v3_reader.fieldnames or [])
    required_candidate_v3_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "候选V3入口ID",
        "入口类型",
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
        "机器家庭匹配初判",
        "调剂初判",
        "历史候选匹配",
        "2023同组投档线",
        "2024同组投档线",
        "2025同组投档线",
        "三年同组命中数",
        "历史线使用口径",
        "PDF原页核验状态",
        "湖北官方系统核验状态",
        "高校官网章程核验状态",
        "家庭接受度核验状态",
        "调剂结论状态",
        "历史线核验状态",
        "核验缺口",
    }
    candidate_v3_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [candidate_v3_summary_path, candidate_v3_csv]
    )
    candidate_v3_batch_counts = Counter(row.get("复核批次") for row in candidate_v3_rows)
    candidate_v3_relation_counts = Counter(row.get("入口类型") for row in candidate_v3_rows)
    candidate_v3_major_source_counts = Counter(row.get("专业明细来源") for row in candidate_v3_rows)
    candidate_v3_history_hit_counts = Counter(row.get("三年同组命中数") for row in candidate_v3_rows)
    candidate_v2_group_codes = {row.get("2026院校专业组代码") for row in candidate_v2_group_rows}
    candidate_v3_v2_codes = {
        row.get("2026院校专业组代码")
        for row in candidate_v3_rows
        if row.get("专业明细来源") == "candidate_v2_review_seed"
    }
    candidate_v3_zero_detail_codes = {
        row.get("2026院校专业组代码")
        for row in candidate_v3_rows
        if as_int(row.get("专业明细行数")) == 0
    }
    candidate_v3_nonzero_blank_detail_count = sum(
        (as_int(row.get("专业明细行数")) or 0) > 0
        and not row.get("组内招生明细", "").strip()
        for row in candidate_v3_rows
    )

    def expected_candidate_v2_major_detail(group_code):
        pieces = []
        for item in sorted(
            candidate_v2_majors_by_group.get(group_code, []),
            key=lambda row: as_int(row.get("组内序号")) or 999,
        ):
            pieces.append(
                "{seq}. {code} {name}｜计划:{plan}｜学费:{tuition}｜选科:{subject}｜偏好:{pref}｜风险:{risk}".format(
                    seq=item.get("组内序号", ""),
                    code=item.get("专业代号", ""),
                    name=item.get("专业名称及备注", ""),
                    plan=item.get("专业计划数候选", ""),
                    tuition=item.get("学费候选", ""),
                    subject=item.get("再选科目候选", ""),
                    pref=item.get("偏好方向", "") or "无",
                    risk=item.get("风险类型", "") or "无",
                )
            )
        return "；".join(pieces)

    candidate_v3_v2_detail_matches = all(
        row.get("组内招生明细") == expected_candidate_v2_major_detail(row.get("2026院校专业组代码"))
        for row in candidate_v3_rows
        if row.get("专业明细来源") == "candidate_v2_review_seed"
    )
    checks.append(ok(
        "第 19 期候选V3复核入口摘要和行数正确",
        candidate_v3_summary.get("status") == "issue19_candidate_v3_review_intake_pending_manual_review"
        and candidate_v3_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and candidate_v3_summary.get("intake_count") == 1327
        and candidate_v3_summary.get("batch_counts") == {
            "B0-历史候选和组号问题优先核页": 20,
            "B1-数字媒体技术优先核页": 29,
            "B2-偏好专业未自动阻断核页": 763,
            "B3-偏好专业硬风险先核风险": 514,
            "B4-同页边界风险组核页": 1,
        }
        and candidate_v3_summary.get("relation_counts") == {
            "历史候选": 20,
            "同校偏好专业补充组": 2,
            "同页相邻风险组": 1,
            "家庭筛选扩展": 1304,
        }
        and candidate_v3_summary.get("major_source_counts") == {
            "candidate_v2_review_seed": 23,
            "family_fit_full_ocr": 1304,
        }
        and candidate_v3_summary.get("history_exact_code_hit_count_distribution") == {
            "0": 267,
            "1": 227,
            "2": 365,
            "3": 468,
        }
        and candidate_v3_summary.get("historical_candidate_count") == 20
        and candidate_v3_summary.get("r0_r1_r2_family_fit_source_count") == 1323
        and candidate_v3_summary.get("candidate_v2_group_count") == 23
        and candidate_v3_summary.get("candidate_v2_group_not_in_family_fit_priority_count") == 4
        and candidate_v3_summary.get("final_available_count") == 0
        and len(candidate_v3_rows) == 1327,
        f"{len(candidate_v3_rows)} intake rows",
    ))
    checks.append(ok(
        "第 19 期候选V3复核入口字段、状态和证据链正确",
        required_candidate_v3_fields.issubset(candidate_v3_fields)
        and len({row.get("候选V3入口ID") for row in candidate_v3_rows}) == len(candidate_v3_rows)
        and candidate_v3_batch_counts == Counter(candidate_v3_summary.get("batch_counts", {}))
        and candidate_v3_relation_counts == Counter(candidate_v3_summary.get("relation_counts", {}))
        and candidate_v3_major_source_counts == Counter(candidate_v3_summary.get("major_source_counts", {}))
        and candidate_v3_history_hit_counts
        == Counter(candidate_v3_summary.get("history_exact_code_hit_count_distribution", {}))
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_v3_manual_review"
            and row.get("候选闸门状态") == "pending_verification"
            and row.get("可进入最终候选") == "false"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("私有页图SHA256")
            and row.get("PDF原页核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网章程核验状态") == "pending_school_charter_review"
            and row.get("家庭接受度核验状态") == "pending_family_acceptance_review"
            and row.get("调剂结论状态") == "pending_transfer_decision"
            for row in candidate_v3_rows
        )
        and sum(row.get("专业明细来源") == "candidate_v2_review_seed" for row in candidate_v3_rows) == 23
        and sum(row.get("专业明细行数") == "0" for row in candidate_v3_rows) == 2
        and candidate_v3_zero_detail_codes == {"C10702", "K15123"}
        and candidate_v3_nonzero_blank_detail_count == 0
        and candidate_v3_v2_codes == candidate_v2_group_codes
        and candidate_v3_v2_detail_matches
        and any(
            row.get("2026院校专业组代码") == "K15123"
            and row.get("来源页码") == "208；209"
            and "page-208" in row.get("私有页图证据编号", "")
            and "page-209" in row.get("私有页图证据编号", "")
            and "历史线不得直接沿用" in row.get("历史线使用口径", "")
            for row in candidate_v3_rows
        )
        and any(
            row.get("2026院校专业组代码") == "C10704"
            and row.get("入口类型") == "历史候选"
            and row.get("专业明细来源") == "candidate_v2_review_seed"
            and row.get("专业明细行数") == "3"
            and "历史线不得直接沿用" in row.get("历史线使用口径", "")
            for row in candidate_v3_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3复核入口公开文件不含本地路径、图片扩展名、身份信息和最终可用结论",
        "final_allowed" not in candidate_v3_public_text
        and "ready_for_discussion" not in candidate_v3_public_text
        and "已确认" not in candidate_v3_public_text
        and "最终推荐" not in candidate_v3_public_text
        and "最终方案" not in candidate_v3_public_text
        and not any(token in candidate_v3_public_text for token in shared_forbidden_tokens),
    ))

    v3_b0_b1_summary_path = ROOT / "data/working/issue19-candidate-v3-b0-b1-review-pack-summary.json"
    v3_b0_b1_group_csv = ROOT / "data/working/issue19-candidate-v3-b0-b1-group-review-pack.csv"
    v3_b0_b1_major_csv = ROOT / "data/working/issue19-candidate-v3-b0-b1-major-review-pack.csv"
    v3_b0_b1_summary = json.loads(v3_b0_b1_summary_path.read_text())
    with v3_b0_b1_group_csv.open(newline="", encoding="utf-8-sig") as f:
        v3_b0_b1_group_reader = csv.DictReader(f)
        v3_b0_b1_group_rows = list(v3_b0_b1_group_reader)
        v3_b0_b1_group_fields = set(v3_b0_b1_group_reader.fieldnames or [])
    with v3_b0_b1_major_csv.open(newline="", encoding="utf-8-sig") as f:
        v3_b0_b1_major_reader = csv.DictReader(f)
        v3_b0_b1_major_rows = list(v3_b0_b1_major_reader)
        v3_b0_b1_major_fields = set(v3_b0_b1_major_reader.fieldnames or [])
    required_v3_b0_b1_group_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "组核验包ID",
        "候选V3入口ID",
        "复核批次",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "来源页码",
        "私有页图证据编号",
        "私有页图SHA256",
        "专业明细来源",
        "专业明细行数",
        "逐专业核验任务数",
        "组内招生明细",
        "核页重点",
        "PDF原页核验状态",
        "湖北官方系统核验状态",
        "高校官网章程核验状态",
        "家庭接受度核验状态",
        "调剂结论状态",
        "历史线核验状态",
        "升级判定状态",
        "可进入下一阶段",
    }
    required_v3_b0_b1_major_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "专业核验任务ID",
        "候选V3入口ID",
        "复核批次",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "来源页码",
        "私有页图证据编号",
        "专业明细来源",
        "专业行来源",
        "专业行ID",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业偏好方向",
        "专业风险类型",
        "机器专业接受度初判",
        "调剂影响初判",
        "字段核验状态",
        "是否阻断组升级",
        "可进入最终专业列表",
    }
    v3_b0_b1_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [v3_b0_b1_summary_path, v3_b0_b1_group_csv, v3_b0_b1_major_csv]
    )
    v3_b0_b1_group_batch_counts = Counter(row.get("复核批次") for row in v3_b0_b1_group_rows)
    v3_b0_b1_group_source_counts = Counter(row.get("专业明细来源") for row in v3_b0_b1_group_rows)
    v3_b0_b1_major_source_counts = Counter(row.get("专业行来源") for row in v3_b0_b1_major_rows)
    v3_b0_b1_major_tasks_by_entry = Counter(row.get("候选V3入口ID") for row in v3_b0_b1_major_rows)
    v3_b0_b1_intake_rows = [row for row in candidate_v3_rows if row.get("复核批次") in {
        "B0-历史候选和组号问题优先核页",
        "B1-数字媒体技术优先核页",
    }]
    v3_b0_b1_intake_by_id = {row.get("候选V3入口ID"): row for row in v3_b0_b1_intake_rows}
    v3_b0_b1_group_by_id = {row.get("候选V3入口ID"): row for row in v3_b0_b1_group_rows}
    v3_b0_b1_zero_detail_codes = {
        row.get("2026院校专业组代码")
        for row in v3_b0_b1_group_rows
        if as_int(row.get("专业明细行数")) == 0
    }
    v3_b0_b1_placeholder_codes = {
        row.get("2026院校专业组代码")
        for row in v3_b0_b1_major_rows
        if row.get("专业行来源") == "zero_detail_group_placeholder"
    }
    checks.append(ok(
        "第 19 期候选V3 B0/B1核验包摘要和行数正确",
        v3_b0_b1_summary.get("status") == "issue19_candidate_v3_b0_b1_review_pack_pending_manual_review"
        and v3_b0_b1_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and v3_b0_b1_summary.get("group_count") == 49
        and v3_b0_b1_summary.get("major_review_task_count") == 324
        and v3_b0_b1_summary.get("placeholder_major_task_count") == 2
        and v3_b0_b1_summary.get("batch_counts") == {
            "B0-历史候选和组号问题优先核页": 20,
            "B1-数字媒体技术优先核页": 29,
        }
        and v3_b0_b1_summary.get("group_major_source_counts") == {
            "candidate_v2_review_seed": 22,
            "family_fit_full_ocr": 27,
        }
        and v3_b0_b1_summary.get("major_row_source_counts") == {
            "candidate_v2_major_review_seed": 81,
            "family_fit_major_detail": 241,
            "zero_detail_group_placeholder": 2,
        }
        and v3_b0_b1_summary.get("zero_detail_group_codes") == ["C10702", "K15123"]
        and v3_b0_b1_summary.get("selected_page_count") == 32
        and v3_b0_b1_summary.get("missing_page_hash_groups") == []
        and v3_b0_b1_summary.get("final_available_count") == 0
        and len(v3_b0_b1_group_rows) == 49
        and len(v3_b0_b1_major_rows) == 324,
        f"{len(v3_b0_b1_group_rows)} groups, {len(v3_b0_b1_major_rows)} major tasks",
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1核验包字段、状态和任务闭环正确",
        required_v3_b0_b1_group_fields.issubset(v3_b0_b1_group_fields)
        and required_v3_b0_b1_major_fields.issubset(v3_b0_b1_major_fields)
        and len({row.get("组核验包ID") for row in v3_b0_b1_group_rows}) == len(v3_b0_b1_group_rows)
        and len({row.get("专业核验任务ID") for row in v3_b0_b1_major_rows}) == len(v3_b0_b1_major_rows)
        and v3_b0_b1_group_batch_counts == Counter(v3_b0_b1_summary.get("batch_counts", {}))
        and v3_b0_b1_group_source_counts == Counter(v3_b0_b1_summary.get("group_major_source_counts", {}))
        and v3_b0_b1_major_source_counts == Counter(v3_b0_b1_summary.get("major_row_source_counts", {}))
        and set(v3_b0_b1_group_by_id) == set(v3_b0_b1_intake_by_id)
        and all(
            v3_b0_b1_group_by_id[entry_id].get("复核批次") == intake_row.get("复核批次")
            and v3_b0_b1_group_by_id[entry_id].get("2026院校专业组代码") == intake_row.get("2026院校专业组代码")
            and v3_b0_b1_group_by_id[entry_id].get("专业明细来源") == intake_row.get("专业明细来源")
            and v3_b0_b1_group_by_id[entry_id].get("专业明细行数") == intake_row.get("专业明细行数")
            and v3_b0_b1_group_by_id[entry_id].get("来源页码") == intake_row.get("来源页码")
            and v3_b0_b1_group_by_id[entry_id].get("组内招生明细") == intake_row.get("组内招生明细")
            for entry_id, intake_row in v3_b0_b1_intake_by_id.items()
        )
        and v3_b0_b1_zero_detail_codes == {"C10702", "K15123"}
        and v3_b0_b1_placeholder_codes == {"C10702", "K15123"}
        and all(
            row.get("逐专业核验任务数") == str(v3_b0_b1_major_tasks_by_entry.get(row.get("候选V3入口ID"), 0))
            for row in v3_b0_b1_group_rows
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_b0_b1_original_page_review"
            and row.get("可进入下一阶段") == "false"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("私有页图SHA256")
            for row in v3_b0_b1_group_rows
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_b0_b1_major_review"
            and row.get("字段核验状态") == "pending"
            and row.get("是否阻断组升级") == "是"
            and row.get("可进入最终专业列表") == "false"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            for row in v3_b0_b1_major_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1核验包公开文件不含本地路径、图片扩展名、身份信息和最终可用结论",
        "final_allowed" not in v3_b0_b1_public_text
        and "ready_for_discussion" not in v3_b0_b1_public_text
        and "已确认" not in v3_b0_b1_public_text
        and "最终推荐" not in v3_b0_b1_public_text
        and "最终方案" not in v3_b0_b1_public_text
        and not any(token in v3_b0_b1_public_text for token in shared_forbidden_tokens),
    ))

    b0_b1_official_summary_path = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-crosscheck-summary.json"
    b0_b1_school_source_csv = ROOT / "data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv"
    b0_b1_group_official_csv = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-crosscheck-queue.csv"
    b0_b1_admission_detail_csv = ROOT / "data/working/issue19-candidate-v3-b0-b1-admission-detail-official-crosscheck.csv"
    b0_b1_major_official_csv = ROOT / "data/working/issue19-candidate-v3-b0-b1-major-official-crosscheck-queue.csv"
    b0_b1_official_seed_csv = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv"
    b0_b1_source_search_log_csv = ROOT / "data/working/issue19-b0-b1-official-source-search-log.csv"
    b0_b1_retained_official_csv = ROOT / "data/working/issue19-b0-b1-retained-official-plan-normalized.csv"
    b0_b1_official_evidence_match_csv = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-evidence-match.csv"
    b0_b1_detail_evidence_ledger_csv = ROOT / "data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv"
    b0_b1_official_evidence_match_summary_path = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-evidence-match-summary.json"
    xztu_extracted_csv = ROOT / "data/external/issue19-b0-b1-official-sources/xztu-2026-hubei-physics-plan-extracted.csv"
    jsut_extracted_csv = ROOT / "data/external/issue19-b0-b1-official-sources/jsut-2026-hubei-physics-plan-extracted.csv"
    b0_b1_official_summary = json.loads(b0_b1_official_summary_path.read_text())
    b0_b1_official_evidence_match_summary = json.loads(b0_b1_official_evidence_match_summary_path.read_text())
    with b0_b1_school_source_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_school_source_reader = csv.DictReader(f)
        b0_b1_school_source_rows = list(b0_b1_school_source_reader)
        b0_b1_school_source_fields = set(b0_b1_school_source_reader.fieldnames or [])
    with b0_b1_group_official_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_group_official_reader = csv.DictReader(f)
        b0_b1_group_official_rows = list(b0_b1_group_official_reader)
        b0_b1_group_official_fields = set(b0_b1_group_official_reader.fieldnames or [])
    with b0_b1_admission_detail_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_admission_detail_reader = csv.DictReader(f)
        b0_b1_admission_detail_rows = list(b0_b1_admission_detail_reader)
        b0_b1_admission_detail_fields = set(b0_b1_admission_detail_reader.fieldnames or [])
    with b0_b1_major_official_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_major_official_reader = csv.DictReader(f)
        b0_b1_major_official_rows = list(b0_b1_major_official_reader)
        b0_b1_major_official_fields = set(b0_b1_major_official_reader.fieldnames or [])
    with b0_b1_official_seed_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_official_seed_rows = list(csv.DictReader(f))
    with b0_b1_retained_official_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_retained_official_reader = csv.DictReader(f)
        b0_b1_retained_official_rows = list(b0_b1_retained_official_reader)
        b0_b1_retained_official_fields = set(b0_b1_retained_official_reader.fieldnames or [])
    with b0_b1_official_evidence_match_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_official_evidence_match_reader = csv.DictReader(f)
        b0_b1_official_evidence_match_rows = list(b0_b1_official_evidence_match_reader)
        b0_b1_official_evidence_match_fields = set(b0_b1_official_evidence_match_reader.fieldnames or [])
    with b0_b1_detail_evidence_ledger_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_detail_evidence_ledger_reader = csv.DictReader(f)
        b0_b1_detail_evidence_ledger_rows = list(b0_b1_detail_evidence_ledger_reader)
        b0_b1_detail_evidence_ledger_fields = set(b0_b1_detail_evidence_ledger_reader.fieldnames or [])
    with xztu_extracted_csv.open(newline="", encoding="utf-8-sig") as f:
        xztu_extracted_rows = list(csv.DictReader(f))
    with jsut_extracted_csv.open(newline="", encoding="utf-8-sig") as f:
        jsut_extracted_rows = list(csv.DictReader(f))
    with b0_b1_source_search_log_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_source_search_log_rows = list(csv.DictReader(f))

    required_b0_b1_school_source_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "学校官方来源队列ID",
        "院校代码",
        "院校名称OCR",
        "B0B1专业组数",
        "逐专业核验任务数",
        "涉及专业组代码",
        "官网来源状态",
        "官网URL",
        "本地留存状态",
        "官方源缺口",
        "补源优先级",
        "高校官网计划检索式",
        "招生章程检索式",
    }
    required_b0_b1_group_official_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "官方交叉校验任务ID",
        "候选V3入口ID",
        "复核批次",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "逐专业核验任务数",
        "官网来源状态",
        "官网URL",
        "官方源缺口",
        "必须核验字段",
        "湖北官方系统核验状态",
        "高校官网计划核验状态",
        "招生章程核验状态",
        "PDF原页核验状态",
        "家庭接受度核验状态",
        "调剂结论状态",
        "交叉校验结论",
        "可进入下一阶段",
    }
    required_b0_b1_admission_detail_fields = {
        "招生明细主表行ID",
        "主表粒度",
        "是否真实招生明细",
        "是否0明细占位",
        "组级索引文件",
        "学校补源文件",
        "原逐专业核验队列文件",
        "组级风险线索",
        "历史线使用口径",
        "专业明细行数",
        "逐专业核验任务数",
        "必须核验字段",
        "组级湖北官方系统核验状态",
        "组级高校官网计划核验状态",
        "组级招生章程核验状态",
        "组级PDF原页核验状态",
        "组级家庭接受度核验状态",
        "组级调剂结论状态",
        "组级交叉校验结论",
        "组级可进入下一阶段",
        "官方逐专业校验任务ID",
        "官方交叉校验任务ID",
        "专业核验任务ID",
        "候选V3入口ID",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业行来源",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "官网来源状态",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "家庭接受度人工结论状态",
        "调剂影响人工结论状态",
        "字段核验状态",
        "是否阻断组升级",
        "可进入最终专业列表",
        "可进入下一阶段",
    }
    required_b0_b1_major_official_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "官方逐专业校验任务ID",
        "官方交叉校验任务ID",
        "专业核验任务ID",
        "候选V3入口ID",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业风险类型",
        "机器专业接受度初判",
        "官网来源状态",
        "官方源缺口",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "家庭接受度人工结论状态",
        "调剂影响人工结论状态",
        "字段核验状态",
        "是否阻断组升级",
        "可进入最终专业列表",
        "可进入下一阶段",
    }
    b0_b1_school_source_counts = Counter(row.get("官网来源状态") for row in b0_b1_school_source_rows)
    b0_b1_group_official_source_counts = Counter(row.get("官网来源状态") for row in b0_b1_group_official_rows)
    b0_b1_admission_detail_source_counts = Counter(row.get("官网来源状态") for row in b0_b1_admission_detail_rows)
    b0_b1_major_official_source_counts = Counter(row.get("官网来源状态") for row in b0_b1_major_official_rows)
    b0_b1_major_official_source_row_counts = Counter(row.get("专业行来源") for row in b0_b1_major_official_rows)
    b0_b1_school_priority_counts = Counter(row.get("补源优先级") for row in b0_b1_school_source_rows)
    b0_b1_retained_official_evidence_counts = Counter(row.get("证据类型") for row in b0_b1_retained_official_rows)
    b0_b1_evidence_match_status_counts = Counter(row.get("官网证据匹配状态") for row in b0_b1_official_evidence_match_rows)
    b0_b1_evidence_plan_status_counts = Counter(row.get("计划数核验状态") for row in b0_b1_official_evidence_match_rows)
    b0_b1_detail_ledger_fidelity_counts = Counter(row.get("保真处理状态") for row in b0_b1_detail_evidence_ledger_rows)
    b0_b1_evidence_matched_school_counts = Counter(
        row.get("院校名称OCR")
        for row in b0_b1_official_evidence_match_rows
        if row.get("官网证据匹配状态") == "matched"
    )
    b0_b1_group_count_by_school = Counter(
        (row.get("院校代码"), row.get("院校名称OCR")) for row in b0_b1_group_official_rows
    )
    b0_b1_major_count_by_school = Counter(
        (row.get("院校代码"), row.get("院校名称OCR")) for row in b0_b1_major_official_rows
    )
    b0_b1_group_batch_count_by_school = Counter(
        (row.get("院校代码"), row.get("院校名称OCR"), row.get("复核批次"))
        for row in b0_b1_group_official_rows
    )
    b0_b1_school_status_by_name = {
        row.get("院校名称OCR"): row.get("官网来源状态") for row in b0_b1_school_source_rows
    }
    b0_b1_group_official_by_entry = {
        row.get("候选V3入口ID"): row for row in b0_b1_group_official_rows
    }
    b0_b1_major_official_by_task = {
        row.get("专业核验任务ID"): row for row in b0_b1_major_official_rows
    }
    b0_b1_admission_detail_by_task = {
        row.get("专业核验任务ID"): row for row in b0_b1_admission_detail_rows
    }
    b0_b1_major_review_by_task = {
        row.get("专业核验任务ID"): row for row in v3_b0_b1_major_rows
    }
    b0_b1_major_official_tasks_by_entry = Counter(
        row.get("候选V3入口ID") for row in b0_b1_major_official_rows
    )
    b0_b1_school_source_by_name = {
        row.get("院校名称OCR"): row for row in b0_b1_school_source_rows
    }
    b0_b1_evidence_match_by_detail_id = {
        row.get("招生明细主表行ID"): row for row in b0_b1_official_evidence_match_rows
    }
    xztu_extracted_plan_by_major = {
        row.get("专业名称"): row.get("湖北计划数") for row in xztu_extracted_rows
    }
    jsut_extracted_plan_by_major = {
        row.get("专业名称"): row.get("湖北计划数") for row in jsut_extracted_rows
    }
    retained_official_by_school_major = {
        (row.get("学校名称"), row.get("专业名称")): row for row in b0_b1_retained_official_rows
    }
    b0_b1_official_seed_school_names = {row.get("学校名称") for row in b0_b1_official_seed_rows}
    allowed_b0_b1_official_source_statuses = {
        "charter_or_rules_only_no_plan",
        "has_partial_source_needs_followup",
        "has_reusable_2026_hubei_plan_source",
        "needs_official_plan_source_search",
    }
    required_b0_b1_crosscheck_field_names = {
        "院校代码",
        "院校名称",
        "院校专业组代码",
        "专业组边界和组内全部专业",
        "专业代号",
        "专业名称及备注",
        "专业计划数",
        "学费",
        "学制",
        "校区",
        "再选科目",
        "特殊备注",
        "招生章程录取规则",
        "体检/语种/单科限制",
        "办学性质和高收费/中外合作",
    }
    required_b0_b1_retained_official_fields = {
        "学校名称",
        "官方来源文件",
        "证据类型",
        "年份",
        "省份",
        "科类",
        "专业名称",
        "计划数",
        "可核字段",
        "局限性",
    }
    required_b0_b1_evidence_match_fields = {
        "招生明细主表行ID",
        "主表粒度",
        "是否真实招生明细",
        "来源页码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业组内专业序号",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业偏好方向",
        "机器专业接受度初判",
        "调剂影响初判",
        "官网证据匹配状态",
        "官网证据覆盖结论",
        "最佳官网来源文件",
        "最佳官网专业名称",
        "最佳官网计划数",
        "计划数核验状态",
        "仍需核验",
    }
    required_b0_b1_detail_evidence_ledger_fields = {
        "招生明细主表行ID",
        "主表粒度",
        "是否真实招生明细",
        "是否0明细占位",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "官网证据匹配状态",
        "最佳官网专业名称",
        "最佳官网计划数",
        "最佳官网学费",
        "计划数核验状态",
        "保真处理状态",
        "仍需核验",
        "可进入最终专业列表",
        "可进入下一阶段",
    }
    b0_b1_major_official_placeholder_rows = [
        row
        for row in b0_b1_major_official_rows
        if row.get("专业行来源") == "zero_detail_group_placeholder"
    ]
    b0_b1_major_official_real_rows = [
        row
        for row in b0_b1_major_official_rows
        if row.get("专业行来源") != "zero_detail_group_placeholder"
    ]
    b0_b1_official_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            b0_b1_official_summary_path,
            b0_b1_school_source_csv,
            b0_b1_group_official_csv,
            b0_b1_admission_detail_csv,
            b0_b1_major_official_csv,
            b0_b1_official_seed_csv,
            b0_b1_source_search_log_csv,
            b0_b1_retained_official_csv,
            b0_b1_official_evidence_match_csv,
            b0_b1_detail_evidence_ledger_csv,
            b0_b1_official_evidence_match_summary_path,
            xztu_extracted_csv,
        ]
    )
    checks.append(ok(
        "第 19 期候选V3 B0/B1官方交叉校验队列摘要和行数正确",
        b0_b1_official_summary.get("status") == "issue19_candidate_v3_b0_b1_official_crosscheck_pending"
        and b0_b1_official_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and b0_b1_official_summary.get("school_count") == 36
        and b0_b1_official_summary.get("group_count") == 49
        and b0_b1_official_summary.get("major_review_task_count") == 324
        and b0_b1_official_summary.get("admission_detail_main_row_count") == 324
        and b0_b1_official_summary.get("major_official_crosscheck_task_count") == 324
        and b0_b1_official_summary.get("school_source_status_counts") == {
            "charter_or_rules_only_no_plan": 5,
            "has_partial_source_needs_followup": 16,
            "has_reusable_2026_hubei_plan_source": 7,
            "needs_official_plan_source_search": 8,
        }
        and b0_b1_official_summary.get("group_source_status_counts") == {
            "charter_or_rules_only_no_plan": 8,
            "has_partial_source_needs_followup": 19,
            "has_reusable_2026_hubei_plan_source": 12,
            "needs_official_plan_source_search": 10,
        }
        and b0_b1_official_summary.get("admission_detail_source_status_counts") == {
            "charter_or_rules_only_no_plan": 44,
            "has_partial_source_needs_followup": 132,
            "has_reusable_2026_hubei_plan_source": 82,
            "needs_official_plan_source_search": 66,
        }
        and b0_b1_official_summary.get("major_source_status_counts") == {
            "charter_or_rules_only_no_plan": 44,
            "has_partial_source_needs_followup": 132,
            "has_reusable_2026_hubei_plan_source": 82,
            "needs_official_plan_source_search": 66,
        }
        and b0_b1_official_summary.get("major_row_source_counts") == {
            "candidate_v2_major_review_seed": 81,
            "family_fit_major_detail": 241,
            "zero_detail_group_placeholder": 2,
        }
        and b0_b1_official_summary.get("source_priority_counts") == {
            "S0-B0历史候选学校优先补源": 11,
            "S1-已有官网计划源先做字段对照": 6,
            "S2-多组学校优先补源": 1,
            "S3-B1单组学校按页码推进": 18,
        }
        and b0_b1_official_summary.get("schools_with_reusable_2026_hubei_plan_source") == [
            "中国传媒大学",
            "兰州大学",
            "天津外国语大学",
            "山东大学",
            "武汉商学院",
            "西北民族大学",
            "西安邮电大学",
        ]
        and b0_b1_official_summary.get("schools_needing_official_plan_source_search") == [
            "成都师范学院",
            "武汉轻工大学",
            "浙江传媒学院",
            "浙江工业大学",
            "湖北师范大学",
            "西安航空学院",
            "长春工业大学",
            "韶关学院",
        ]
        and b0_b1_official_summary.get("admission_detail_real_row_count") == 322
        and b0_b1_official_summary.get("admission_detail_placeholder_row_count") == 2
        and b0_b1_official_summary.get("final_available_count") == 0
        and b0_b1_official_summary.get("major_final_available_count") == 0
        and len(b0_b1_school_source_rows) == 36
        and len(b0_b1_group_official_rows) == 49
        and len(b0_b1_admission_detail_rows) == 324
        and len(b0_b1_major_official_rows) == 324
        and len(b0_b1_official_seed_rows) == 25,
        f"{len(b0_b1_school_source_rows)} schools, {len(b0_b1_group_official_rows)} groups, {len(b0_b1_admission_detail_rows)} details, {len(b0_b1_major_official_rows)} majors",
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1官方交叉校验字段、主键和来源状态正确",
        required_b0_b1_school_source_fields.issubset(b0_b1_school_source_fields)
        and required_b0_b1_group_official_fields.issubset(b0_b1_group_official_fields)
        and required_b0_b1_admission_detail_fields.issubset(b0_b1_admission_detail_fields)
        and required_b0_b1_major_official_fields.issubset(b0_b1_major_official_fields)
        and len({row.get("学校官方来源队列ID") for row in b0_b1_school_source_rows}) == len(b0_b1_school_source_rows)
        and len({row.get("官方交叉校验任务ID") for row in b0_b1_group_official_rows}) == len(b0_b1_group_official_rows)
        and len({row.get("招生明细主表行ID") for row in b0_b1_admission_detail_rows}) == len(b0_b1_admission_detail_rows)
        and len({row.get("官方逐专业校验任务ID") for row in b0_b1_major_official_rows}) == len(b0_b1_major_official_rows)
        and b0_b1_school_source_counts == Counter(b0_b1_official_summary.get("school_source_status_counts", {}))
        and b0_b1_group_official_source_counts == Counter(b0_b1_official_summary.get("group_source_status_counts", {}))
        and b0_b1_admission_detail_source_counts == Counter(b0_b1_official_summary.get("admission_detail_source_status_counts", {}))
        and b0_b1_major_official_source_counts == Counter(b0_b1_official_summary.get("major_source_status_counts", {}))
        and b0_b1_major_official_source_row_counts == Counter(b0_b1_official_summary.get("major_row_source_counts", {}))
        and b0_b1_school_priority_counts == Counter(b0_b1_official_summary.get("source_priority_counts", {}))
        and b0_b1_official_seed_school_names == {
            "北京语言大学",
            "北京林业大学",
            "中国传媒大学",
            "成都理工大学",
            "成都信息工程大学",
            "江汉大学",
            "山东大学",
            "山东财经大学",
            "山东工商学院",
            "江苏理工学院",
            "忻州师范学院",
            "杭州电子科技大学",
            "兰州大学",
            "天津外国语大学",
            "西北民族大学",
            "西安建筑科技大学",
            "西安财经大学",
            "西安工商学院",
            "西安医学院",
            "西安邮电大学",
            "北方工业大学",
            "云南大学",
            "喀什大学",
            "南宁学院",
            "新疆天山职业技术大学",
        }
        and all(
            b0_b1_school_source_by_name.get(name, {}).get("官网来源状态") == expected_status
            for name, expected_status in {
                "北京语言大学": "has_partial_source_needs_followup",
                "北京林业大学": "has_partial_source_needs_followup",
                "中国传媒大学": "has_reusable_2026_hubei_plan_source",
                "成都理工大学": "has_partial_source_needs_followup",
                "成都信息工程大学": "has_partial_source_needs_followup",
                "江汉大学": "has_partial_source_needs_followup",
                "山东大学": "has_reusable_2026_hubei_plan_source",
                "山东财经大学": "has_partial_source_needs_followup",
                "山东工商学院": "has_partial_source_needs_followup",
                "江苏理工学院": "has_partial_source_needs_followup",
                "忻州师范学院": "has_partial_source_needs_followup",
                "杭州电子科技大学": "has_partial_source_needs_followup",
                "兰州大学": "has_reusable_2026_hubei_plan_source",
                "天津外国语大学": "has_reusable_2026_hubei_plan_source",
                "西北民族大学": "has_reusable_2026_hubei_plan_source",
                "西安建筑科技大学": "has_partial_source_needs_followup",
                "西安财经大学": "has_partial_source_needs_followup",
                "西安医学院": "has_partial_source_needs_followup",
                "西安邮电大学": "has_reusable_2026_hubei_plan_source",
                "北方工业大学": "charter_or_rules_only_no_plan",
                "云南大学": "has_partial_source_needs_followup",
                "喀什大学": "has_partial_source_needs_followup",
                "南宁学院": "has_partial_source_needs_followup",
                "西安工商学院": "charter_or_rules_only_no_plan",
                "新疆天山职业技术大学": "charter_or_rules_only_no_plan",
            }.items()
        )
        and all(
            row.get("官网来源状态") in allowed_b0_b1_official_source_statuses
            for row in b0_b1_school_source_rows + b0_b1_group_official_rows + b0_b1_admission_detail_rows + b0_b1_major_official_rows
        )
        and all(
            row.get("数据阶段") == "issue19_candidate_v3_b0_b1_official_crosscheck_queue"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            for row in b0_b1_school_source_rows + b0_b1_group_official_rows + b0_b1_admission_detail_rows + b0_b1_major_official_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1官方交叉校验逐专业招生明细与核验包一一对应",
        set(b0_b1_major_official_by_task) == set(b0_b1_major_review_by_task)
        and set(b0_b1_admission_detail_by_task) == set(b0_b1_major_review_by_task)
        and all(
            b0_b1_major_official_by_task[task_id].get("候选V3入口ID") == review_row.get("候选V3入口ID")
            and b0_b1_major_official_by_task[task_id].get("2026院校专业组代码") == review_row.get("2026院校专业组代码")
            and b0_b1_major_official_by_task[task_id].get("专业代号OCR") == review_row.get("专业代号OCR")
            and b0_b1_major_official_by_task[task_id].get("专业名称及备注OCR") == review_row.get("专业名称及备注OCR")
            and b0_b1_major_official_by_task[task_id].get("专业计划数OCR候选") == review_row.get("专业计划数OCR候选")
            and b0_b1_major_official_by_task[task_id].get("学费OCR候选") == review_row.get("学费OCR候选")
            and b0_b1_major_official_by_task[task_id].get("机器专业接受度初判") == review_row.get("机器专业接受度初判")
            for task_id, review_row in b0_b1_major_review_by_task.items()
        )
        and all(
            b0_b1_admission_detail_by_task[task_id].get("主表粒度") == "逐专业招生明细"
            and b0_b1_admission_detail_by_task[task_id].get("专业名称及备注OCR") == review_row.get("专业名称及备注OCR")
            and b0_b1_admission_detail_by_task[task_id].get("专业计划数OCR候选") == review_row.get("专业计划数OCR候选")
            and b0_b1_admission_detail_by_task[task_id].get("组级风险线索")
            == b0_b1_group_official_by_entry.get(review_row.get("候选V3入口ID"), {}).get("风险线索")
            for task_id, review_row in b0_b1_major_review_by_task.items()
        )
        and all(
            row.get("逐专业核验任务数") == str(b0_b1_major_official_tasks_by_entry.get(row.get("候选V3入口ID"), 0))
            and b0_b1_group_official_by_entry.get(row.get("候选V3入口ID"), {}).get("官方交叉校验任务ID")
            for row in b0_b1_group_official_rows
        )
        and all(
            row.get("官方交叉校验任务ID")
            == b0_b1_group_official_by_entry.get(row.get("候选V3入口ID"), {}).get("官方交叉校验任务ID")
            for row in b0_b1_major_official_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1官方交叉校验学校聚合和来源状态传递一致",
        all(
            as_int(row.get("B0B1专业组数"))
            == b0_b1_group_count_by_school[(row.get("院校代码"), row.get("院校名称OCR"))]
            and as_int(row.get("逐专业核验任务数"))
            == b0_b1_major_count_by_school[(row.get("院校代码"), row.get("院校名称OCR"))]
            and as_int(row.get("B0组数"))
            == b0_b1_group_batch_count_by_school[
                (row.get("院校代码"), row.get("院校名称OCR"), "B0-历史候选和组号问题优先核页")
            ]
            and as_int(row.get("B1组数"))
            == b0_b1_group_batch_count_by_school[
                (row.get("院校代码"), row.get("院校名称OCR"), "B1-数字媒体技术优先核页")
            ]
            for row in b0_b1_school_source_rows
        )
        and all(
            row.get("官网来源状态") == b0_b1_school_status_by_name.get(row.get("院校名称OCR"))
            for row in b0_b1_group_official_rows
        )
        and all(
            row.get("官网来源状态")
            == b0_b1_group_official_by_entry.get(row.get("候选V3入口ID"), {}).get("官网来源状态")
            for row in b0_b1_admission_detail_rows + b0_b1_major_official_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1官方交叉校验0明细占位不可冒充真实招生明细",
        len(b0_b1_major_official_placeholder_rows) == 2
        and len(b0_b1_major_official_real_rows) == 322
        and {
            row.get("2026院校专业组代码")
            for row in b0_b1_major_official_placeholder_rows
        } == {"C10702", "K15123"}
        and all(
            row.get("是否阻断组升级") == "是"
            and row.get("可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("专业名称及备注OCR") == ""
            for row in b0_b1_major_official_placeholder_rows
        )
        and all(row.get("专业行来源") != "zero_detail_group_placeholder" for row in b0_b1_major_official_real_rows)
        and all(
            required_b0_b1_crosscheck_field_names.issubset(
                set(row.get("必须核验字段", "").split("；"))
            )
            for row in b0_b1_group_official_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1逐专业招生明细主表为默认候选粒度",
        all(row.get("主表粒度") == "逐专业招生明细" for row in b0_b1_admission_detail_rows)
        and all(
            row.get("是否真实招生明细") == ("false" if row.get("专业行来源") == "zero_detail_group_placeholder" else "true")
            and row.get("是否0明细占位") == ("true" if row.get("专业行来源") == "zero_detail_group_placeholder" else "false")
            and row.get("组级索引文件") == "data/working/issue19-candidate-v3-b0-b1-official-crosscheck-queue.csv"
            and row.get("学校补源文件") == "data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv"
            and row.get("原逐专业核验队列文件") == "data/working/issue19-candidate-v3-b0-b1-major-official-crosscheck-queue.csv"
            and row.get("组级可进入下一阶段") == "false"
            for row in b0_b1_admission_detail_rows
        )
        and sum(row.get("是否真实招生明细") == "true" for row in b0_b1_admission_detail_rows) == 322
        and sum(row.get("是否0明细占位") == "true" for row in b0_b1_admission_detail_rows) == 2,
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1官方交叉校验默认闸门保持不可升级",
        all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_school_official_source_review"
            for row in b0_b1_school_source_rows
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_group_official_crosscheck"
            and row.get("湖北官方系统核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网计划核验状态") == "pending_school_plan_review"
            and row.get("招生章程核验状态") == "pending_school_charter_review"
            and row.get("PDF原页核验状态") == "pending_original_pdf_page_review"
            and row.get("家庭接受度核验状态") == "pending_family_acceptance_review"
            and row.get("调剂结论状态") == "pending_transfer_decision"
            and row.get("交叉校验结论") == "pending"
            and row.get("可进入下一阶段") == "false"
            for row in b0_b1_group_official_rows
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_major_official_crosscheck"
            and row.get("PDF字段核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/章程字段核验状态") == "pending_school_plan_or_charter_review"
            and row.get("家庭接受度人工结论状态") == "pending_family_acceptance_review"
            and row.get("调剂影响人工结论状态") == "pending_transfer_decision"
            and row.get("字段核验状态") == "pending"
            and row.get("是否阻断组升级") == "是"
            and row.get("可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            for row in b0_b1_admission_detail_rows
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_major_official_crosscheck"
            and row.get("PDF字段核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/章程字段核验状态") == "pending_school_plan_or_charter_review"
            and row.get("家庭接受度人工结论状态") == "pending_family_acceptance_review"
            and row.get("调剂影响人工结论状态") == "pending_transfer_decision"
            and row.get("字段核验状态") == "pending"
            and row.get("是否阻断组升级") == "是"
            and row.get("可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            for row in b0_b1_major_official_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1官网/API留存证据匹配表为逐专业明细且不是最终方案",
        b0_b1_official_evidence_match_summary.get("status") == "official_evidence_match_not_final"
        and b0_b1_official_evidence_match_summary.get("normalized_official_row_count") == 367
        and b0_b1_official_evidence_match_summary.get("admission_detail_row_count") == 324
        and b0_b1_official_evidence_match_summary.get("admission_detail_evidence_ledger_row_count") == 324
        and b0_b1_official_evidence_match_summary.get("default_discussion_table")
        == "data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv"
        and b0_b1_official_evidence_match_summary.get("retained_official_schools") == [
            "中国传媒大学",
            "兰州大学",
            "南宁学院",
            "喀什大学",
            "天津外国语大学",
            "山东大学",
            "忻州师范学院",
            "成都信息工程大学",
            "杭州电子科技大学",
            "江汉大学",
            "江苏理工学院",
            "西北民族大学",
            "西安医学院",
            "西安财经大学",
            "西安邮电大学",
        ]
        and b0_b1_official_evidence_match_summary.get("evidence_type_counts") == {
            "official_dynamic_ajax_json": 38,
            "official_dynamic_api_json": 189,
            "official_static_html_table": 58,
            "official_attachment_xlsx_province_table": 31,
            "official_attachment_xlsx_row_plan": 21,
            "official_pdf_table_extracted_csv": 15,
            "official_image_table_extracted_csv": 15,
        }
        and b0_b1_official_evidence_match_summary.get("match_status_counts") == {
            "no_school_source": 191,
            "matched": 124,
            "unmatched": 9,
        }
        and b0_b1_official_evidence_match_summary.get("plan_check_status_counts") == {
            "not_covered": 200,
            "ocr_plan_missing_official_available": 52,
            "mismatch": 25,
            "match": 47,
        }
        and b0_b1_official_evidence_match_summary.get("fidelity_status_counts") == {
            "待补高校官网计划源": 189,
            "占位行-不是真实招生明细": 2,
            "官网可补OCR计划数-优先核页": 52,
            "官网专业名匹配但计划数冲突-优先核页": 25,
            "官网未匹配-专业名或OCR待核": 9,
            "官网专业名和计划数一致-仍待湖北官方系统和PDF原页复核": 47,
        }
        and b0_b1_official_evidence_match_summary.get("matched_school_counts") == {
            "西安财经大学": 1,
            "西安医学院": 2,
            "忻州师范学院": 4,
            "江苏理工学院": 13,
            "杭州电子科技大学": 10,
            "中国传媒大学": 9,
            "南宁学院": 5,
            "成都信息工程大学": 19,
            "西安邮电大学": 19,
            "喀什大学": 7,
            "山东大学": 6,
            "兰州大学": 7,
            "西北民族大学": 3,
            "江汉大学": 18,
            "天津外国语大学": 1,
        }
        and required_b0_b1_retained_official_fields.issubset(b0_b1_retained_official_fields)
        and required_b0_b1_evidence_match_fields.issubset(b0_b1_official_evidence_match_fields)
        and required_b0_b1_detail_evidence_ledger_fields.issubset(b0_b1_detail_evidence_ledger_fields)
        and len(b0_b1_retained_official_rows) == 367
        and len(b0_b1_official_evidence_match_rows) == 324
        and len(b0_b1_detail_evidence_ledger_rows) == 324
        and set(b0_b1_evidence_match_by_detail_id) == {row.get("招生明细主表行ID") for row in b0_b1_admission_detail_rows}
        and {row.get("招生明细主表行ID") for row in b0_b1_detail_evidence_ledger_rows}
        == {row.get("招生明细主表行ID") for row in b0_b1_admission_detail_rows}
        and b0_b1_retained_official_evidence_counts == Counter(
            b0_b1_official_evidence_match_summary.get("evidence_type_counts", {})
        )
        and b0_b1_evidence_match_status_counts == Counter(
            b0_b1_official_evidence_match_summary.get("match_status_counts", {})
        )
        and b0_b1_evidence_plan_status_counts == Counter(
            b0_b1_official_evidence_match_summary.get("plan_check_status_counts", {})
        )
        and b0_b1_evidence_matched_school_counts == Counter(
            b0_b1_official_evidence_match_summary.get("matched_school_counts", {})
        )
        and b0_b1_detail_ledger_fidelity_counts == Counter(
            b0_b1_official_evidence_match_summary.get("fidelity_status_counts", {})
        )
        and all(row.get("主表粒度") == "逐专业招生明细" for row in b0_b1_official_evidence_match_rows)
        and all(row.get("主表粒度") == "逐专业招生明细" for row in b0_b1_detail_evidence_ledger_rows)
        and all(
            row.get("可进入最终专业列表") == "false" and row.get("可进入下一阶段") == "false"
            for row in b0_b1_detail_evidence_ledger_rows
        )
        and all(
            all(token in row.get("仍需核验", "") for token in ["PDF原页", "湖北官方系统", "专业组边界", "调剂范围", "家庭接受度"])
            for row in b0_b1_official_evidence_match_rows
        ),
    ))
    checks.append(ok(
        "忻州师范学院官网PDF抽取表保留湖北物理类逐专业明细且可复核",
        len(xztu_extracted_rows) == 15
        and all(row.get("学校名称") == "忻州师范学院" for row in xztu_extracted_rows)
        and all(row.get("科类") == "物理" for row in xztu_extracted_rows)
        and xztu_extracted_plan_by_major.get("应用化学") == "1"
        and xztu_extracted_plan_by_major.get("数字媒体技术") == "1"
        and xztu_extracted_plan_by_major.get("数据科学与大数据技术") == "1"
        and xztu_extracted_plan_by_major.get("计算机科学与技术(师范)") == "2"
        and all(
            row.get("原始PDF") == "data/external/issue19-b0-b1-official-sources/xztu-2026-province-major-plan.pdf"
            and row.get("提取方法") == "pdfplumber_extract_tables_header_hubei_column"
            and "湖北院校专业组代码" in row.get("提取局限性", "")
            for row in xztu_extracted_rows
        ),
    ))
    checks.append(ok(
        "江苏理工学院官方计划图转录表保留湖北物理类逐专业明细且可复核",
        len(jsut_extracted_rows) == 15
        and all(row.get("学校名称") == "江苏理工学院" for row in jsut_extracted_rows)
        and all(row.get("科类") == "物理类" for row in jsut_extracted_rows)
        and jsut_extracted_plan_by_major.get("会计学") == "1"
        and jsut_extracted_plan_by_major.get("电气工程及其自动化") == "2"
        and jsut_extracted_plan_by_major.get("数据科学与大数据技术") == "1"
        and jsut_extracted_plan_by_major.get("数字媒体技术") == "2"
        and all(
            row.get("原始图片") == "data/external/issue19-b0-b1-official-sources/jsut-2026-hubei-plan.jpg"
            and row.get("官网入口页") == "data/external/issue19-b0-b1-official-sources/jsut-zs-home-2026-plan-links.html"
            and row.get("提取方法") == "official_image_visual_transcription_with_apple_vision_ocr_check"
            and "湖北院校专业组代码" in row.get("提取局限性", "")
            for row in jsut_extracted_rows
        ),
    ))
    checks.append(ok(
        "南宁学院官网静态表已标准化为湖北物理类逐专业证据",
        sum(row.get("学校名称") == "南宁学院" for row in b0_b1_retained_official_rows) == 20
        and retained_official_by_school_major.get(("南宁学院", "计算机科学与技术"), {}).get("计划数") == "2"
        and retained_official_by_school_major.get(("南宁学院", "物联网工程"), {}).get("计划数") == "2"
        and retained_official_by_school_major.get(("南宁学院", "智能科学与技术"), {}).get("计划数") == "2"
        and retained_official_by_school_major.get(("南宁学院", "数据科学与大数据技术"), {}).get("计划数") == "2"
        and retained_official_by_school_major.get(("南宁学院", "数字媒体技术"), {}).get("计划数") == "3"
        and all(
            row.get("证据类型") == "official_static_html_table"
            and row.get("年份") == "2026"
            and row.get("省份") == "湖北"
            and row.get("科类") == "物理类"
            and "页面专业组编号不是湖北志愿系统院校专业组代码" in row.get("局限性", "")
            for row in b0_b1_retained_official_rows
            if row.get("学校名称") == "南宁学院"
        ),
    ))
    checks.append(ok(
        "B0/B1剩余官方来源并发检索日志已记录",
        len(b0_b1_source_search_log_rows) == 10
        and {
            row.get("学校名称"): row.get("是否可核湖北2026")
            for row in b0_b1_source_search_log_rows
        }
        == {
            "武汉轻工大学": "未见",
            "湖北师范大学": "未见",
            "长春工业大学": "未见",
            "江苏理工学院": "部分",
            "浙江工业大学": "可能",
            "浙江传媒学院": "未见",
            "韶关学院": "未见",
            "南宁学院": "部分",
            "成都师范学院": "未见",
            "西安航空学院": "未见",
        }
        and all(row.get("局限性") and row.get("下一步") for row in b0_b1_source_search_log_rows),
    ))
    checks.append(ok(
        "第 19 期候选V3 B0/B1官方交叉校验公开文件不含本地路径、图片扩展名、身份信息和最终可用结论",
        "final_allowed" not in b0_b1_official_public_text
        and "ready_for_discussion" not in b0_b1_official_public_text
        and "已确认" not in b0_b1_official_public_text
        and "最终推荐" not in b0_b1_official_public_text
        and "最终方案" not in b0_b1_official_public_text
        and not any(token in b0_b1_official_public_text for token in shared_forbidden_tokens),
    ))

    foundation_audit_summary_path = ROOT / "data/working/issue19-foundation-audit-summary.json"
    foundation_audit_findings_csv = ROOT / "data/working/issue19-foundation-audit-findings.csv"
    foundation_page_audit_csv = ROOT / "data/working/issue19-foundation-page-audit.csv"
    foundation_audit_summary = json.loads(foundation_audit_summary_path.read_text())
    with foundation_audit_findings_csv.open(newline="", encoding="utf-8-sig") as f:
        foundation_findings_reader = csv.DictReader(f)
        foundation_finding_rows = list(foundation_findings_reader)
        foundation_finding_fields = set(foundation_findings_reader.fieldnames or [])
    with foundation_page_audit_csv.open(newline="", encoding="utf-8-sig") as f:
        foundation_page_reader = csv.DictReader(f)
        foundation_page_rows = list(foundation_page_reader)
        foundation_page_fields = set(foundation_page_reader.fieldnames or [])

    foundation_required_finding_fields = {
        "审计编号",
        "审计域",
        "审计项",
        "审计状态",
        "严重程度",
        "自动阻断",
        "计数",
        "证据摘要",
        "下一步",
    }
    foundation_required_page_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "来源页码",
        "页面专业组数",
        "页面专业明细数",
        "页面院校数",
        "页面结构异常数",
        "页面高严重结构异常数",
        "页面偏好专业明细数",
        "页面风险专业明细数",
        "页面候选池V1专业明细数",
        "页面复核优先级",
        "页面审计状态",
        "下一步",
    }
    foundation_findings_by_id = {row.get("审计编号"): row for row in foundation_finding_rows}
    foundation_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [foundation_audit_summary_path, foundation_audit_findings_csv, foundation_page_audit_csv]
    )
    checks.append(ok(
        "第 19 期底座审计摘要、发现和页级表正确",
        foundation_audit_summary.get("status")
        == "issue19_foundation_machine_checks_passed_need_pdf_official_review"
        and foundation_audit_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and foundation_audit_summary.get("page_count") == 231
        and foundation_audit_summary.get("missing_page_count") == 0
        and foundation_audit_summary.get("outside_page_row_count") == 0
        and foundation_audit_summary.get("school_count") == 1103
        and foundation_audit_summary.get("group_count") == 3329
        and foundation_audit_summary.get("major_count") == 13736
        and foundation_audit_summary.get("major_workbench_count") == 13736
        and foundation_audit_summary.get("major_review_queue_count") == 13705
        and foundation_audit_summary.get("structure_anomaly_count") == 5129
        and foundation_audit_summary.get("matched_structure_anomaly_count") == 5129
        and foundation_audit_summary.get("automatic_blocking_findings_count") == 0
        and foundation_audit_summary.get("manual_review_findings_count") == 8
        and foundation_audit_summary.get("finding_status_counts") == {"通过": 10, "需人工复核": 8}
        and len(foundation_finding_rows) == 18
        and len(foundation_page_rows) == 231
        and foundation_required_finding_fields.issubset(foundation_finding_fields)
        and foundation_required_page_fields.issubset(foundation_page_fields),
        f"{len(foundation_finding_rows)} findings, {len(foundation_page_rows)} pages",
    ))
    checks.append(ok(
        "第 19 期底座审计机器阻断项全部通过",
        all(
            row.get("审计状态") == "通过" and row.get("自动阻断") == "否"
            for row in foundation_finding_rows
            if row.get("严重程度") == "阻断"
        )
        and foundation_findings_by_id["F002"].get("计数") == "0"
        and foundation_findings_by_id["F004"].get("证据摘要") == "专业组ID=3329/3329；专业行ID=13736/13736"
        and foundation_findings_by_id["F007"].get("证据摘要") == "异常队列=5129；工作台聚合=5129"
        and foundation_findings_by_id["F009"].get("计数") == "0",
    ))
    checks.append(ok(
        "第 19 期底座审计关键人工复核风险已显式记录",
        foundation_audit_summary.get("duplicate_group_code_count") == 3
        and foundation_audit_summary.get("duplicate_group_code_row_count") == 6
        and foundation_audit_summary.get("duplicate_group_code_major_row_count") == 14
        and foundation_audit_summary.get("exact_group_occurrence_major_count") == 11898
        and foundation_audit_summary.get("fallback_unique_group_code_major_count") == 1838
        and foundation_audit_summary.get("fallback_unique_group_code_group_count") == 334
        and foundation_audit_summary.get("fallback_candidate_major_count") == 18
        and foundation_audit_summary.get("fallback_sample_major_count") == 52
        and foundation_audit_summary.get("unmatched_major_group_occurrence_count") == 0
        and foundation_audit_summary.get("duplicate_major_code_group_count") == 31
        and foundation_audit_summary.get("duplicate_major_code_pair_count") == 58
        and foundation_audit_summary.get("duplicate_major_code_row_count") == 116
        and foundation_audit_summary.get("candidate_coverage_status_counts") == {"命中": 17, "未命中": 3}
        and foundation_findings_by_id["R008"].get("审计状态") == "需人工复核"
        and foundation_findings_by_id["R008"].get("计数") == "1838"
        and foundation_findings_by_id["R009"].get("审计状态") == "需人工复核"
        and foundation_findings_by_id["R009"].get("计数") == "116",
    ))
    checks.append(ok(
        "第 19 期底座页级审计覆盖 10-240 页且无缺结构化记录页",
        [as_int(row.get("来源页码")) for row in foundation_page_rows] == list(range(10, 241))
        and sum(as_int(row.get("页面专业组数")) for row in foundation_page_rows) == 3329
        and sum(as_int(row.get("页面专业明细数")) for row in foundation_page_rows) == 13736
        and sum(as_int(row.get("页面结构异常数")) for row in foundation_page_rows) == 5129
        and sum(as_int(row.get("页面高严重结构异常数")) for row in foundation_page_rows)
        == sum(1 for row in structure_anomaly_rows if row.get("严重程度") == "高")
        and all(row.get("页面审计状态") == "有结构化记录待核页" for row in foundation_page_rows),
    ))
    checks.append(ok(
        "第 19 期底座审计公开文件不含本地路径、身份信息和最终可用结论",
        "final_allowed" not in foundation_public_text
        and "ready_for_discussion" not in foundation_public_text
        and "已确认" not in foundation_public_text
        and not any(token in foundation_public_text for token in shared_forbidden_tokens),
    ))

    page_manifest_summary_path = ROOT / "data/working/issue19-page-manifest-summary.json"
    page_manifest_csv = ROOT / "data/working/issue19-page-manifest.csv"
    page_manifest_summary = json.loads(page_manifest_summary_path.read_text())
    with page_manifest_csv.open(newline="", encoding="utf-8-sig") as f:
        page_manifest_reader = csv.DictReader(f)
        page_manifest_rows = list(page_manifest_reader)
        page_manifest_fields = set(page_manifest_reader.fieldnames or [])
    required_page_manifest_fields = {
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "PDF页码",
        "页码范围角色",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "OCR引擎",
        "识别语言",
        "OCR识别行数",
        "OCR平均置信度",
        "OCR_QC_P0数",
        "OCR_QC_P1数",
        "疑似招生计划行数",
        "结构化状态",
        "结构化院校数",
        "结构化专业组数",
        "结构化专业明细数",
        "结构异常数",
        "高严重结构异常数",
        "候选V2字段任务数",
        "候选V2字段P0任务数",
        "核验状态",
    }
    page_manifest_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [page_manifest_summary_path, page_manifest_csv]
    )
    checks.append(ok(
        "第 19 期公开页级 manifest 摘要和行数正确",
        page_manifest_summary.get("status") == "issue19_page_manifest_public_metadata_ready"
        and page_manifest_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and page_manifest_summary.get("page_count") == 240
        and page_manifest_summary.get("rendered_page_count") == 240
        and page_manifest_summary.get("ocr_text_page_count") == 240
        and page_manifest_summary.get("structured_plan_page_range") == [10, 240]
        and page_manifest_summary.get("structured_plan_page_count") == 231
        and page_manifest_summary.get("structured_plan_pages_with_group_and_major_count") == 231
        and page_manifest_summary.get("structured_group_count") == 3329
        and page_manifest_summary.get("structured_major_count") == 13736
        and page_manifest_summary.get("structure_anomaly_count") == 5129
        and page_manifest_summary.get("high_structure_anomaly_count") == 3142
        and page_manifest_summary.get("candidate_v2_field_task_count") == 840
        and page_manifest_summary.get("candidate_v2_field_task_on_single_page_count") == 832
        and page_manifest_summary.get("candidate_v2_field_task_without_single_page_count") == 8
        and page_manifest_summary.get("candidate_v2_p0_field_task_count") == 494
        and page_manifest_summary.get("candidate_v2_p0_field_task_on_single_page_count") == 486
        and page_manifest_summary.get("candidate_v2_p0_field_task_without_single_page_count") == 8
        and page_manifest_summary.get("low_confidence_page_count_below_0_65") == 6
        and page_manifest_summary.get("low_confidence_pages_below_0_65")
        == [61, 117, 129, 166, 192, 215]
        and page_manifest_summary.get("private_inputs", {}).get("page_manifest_row_count") == 240
        and page_manifest_summary.get("private_inputs", {}).get("ocr_line_count") == 65512
        and page_manifest_summary.get("private_inputs", {}).get("qc_issue_count") == 37127
        and page_manifest_summary.get("private_inputs", {}).get("suspected_plan_line_count") == 3837
        and len(page_manifest_rows) == 240,
        f"{len(page_manifest_rows)} pages",
    ))
    checks.append(ok(
        "第 19 期公开页级 manifest 字段、状态和页码范围正确",
        required_page_manifest_fields.issubset(page_manifest_fields)
        and [as_int(row.get("PDF页码")) for row in page_manifest_rows] == list(range(1, 241))
        and all(
            row.get("最终可用") == "false"
            and row.get("核验状态") == "needs_manual_pdf_review"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("私有页图SHA256")
            and row.get("私有OCR文本SHA256")
            and row.get("OCR引擎") == "apple_vision"
            for row in page_manifest_rows
        )
        and all(row.get("页码范围角色") == "前置说明页" for row in page_manifest_rows[:9])
        and all(row.get("页码范围角色") == "招生计划明细页" for row in page_manifest_rows[9:])
        and all(
            row.get("结构化状态") == "结构化招生计划页"
            and as_int(row.get("结构化专业组数")) > 0
            and as_int(row.get("结构化专业明细数")) > 0
            for row in page_manifest_rows[9:]
        ),
    ))
    checks.append(ok(
        "第 19 期公开页级 manifest 与 OCR/结构化/候选任务聚合一致",
        sum(as_int(row.get("OCR识别行数")) for row in page_manifest_rows) == 65512
        and sum(as_int(row.get("OCR_QC_P0数")) for row in page_manifest_rows) == 19189
        and sum(as_int(row.get("OCR_QC_P1数")) for row in page_manifest_rows) == 17938
        and sum(as_int(row.get("疑似招生计划行数")) for row in page_manifest_rows) == 3837
        and sum(as_int(row.get("结构化专业组数")) for row in page_manifest_rows) == 3329
        and sum(as_int(row.get("结构化专业明细数")) for row in page_manifest_rows) == 13736
        and sum(as_int(row.get("结构异常数")) for row in page_manifest_rows) == 5129
        and sum(as_int(row.get("高严重结构异常数")) for row in page_manifest_rows) == 3142
        and sum(as_int(row.get("候选V2字段任务数")) for row in page_manifest_rows) == 832
        and sum(as_int(row.get("候选V2字段P0任务数")) for row in page_manifest_rows) == 486,
    ))
    group_count_by_page = Counter()
    school_codes_by_page = {}
    for row in full_group_rows:
        page = as_int(row.get("来源页码"))
        if page is None:
            continue
        group_count_by_page[page] += 1
        if row.get("院校代码"):
            school_codes_by_page.setdefault(page, set()).add(row.get("院校代码"))
    major_count_by_page = Counter()
    for row in full_major_rows:
        page = as_int(row.get("来源页码"))
        if page is not None:
            major_count_by_page[page] += 1
    anomaly_count_by_page = Counter()
    high_anomaly_count_by_page = Counter()
    for row in structure_anomaly_rows:
        page = as_int(row.get("来源页码"))
        if page is None:
            continue
        anomaly_count_by_page[page] += 1
        high_anomaly_count_by_page[page] += row.get("严重程度") == "高"
    candidate_task_count_by_page = Counter()
    candidate_p0_task_count_by_page = Counter()
    for row in candidate_v2_field_ledger_rows:
        page = as_int(row.get("来源页码"))
        if page is None:
            continue
        candidate_task_count_by_page[page] += 1
        candidate_p0_task_count_by_page[page] += row.get("复核优先级") == "P0-字段必须优先核"
    foundation_page_by_page = {
        as_int(row.get("来源页码")): row
        for row in foundation_page_rows
    }
    manifest_page_distribution_ok = True
    for row in page_manifest_rows:
        page = as_int(row.get("PDF页码"))
        foundation_row = foundation_page_by_page.get(page)
        manifest_page_distribution_ok = manifest_page_distribution_ok and (
            as_int(row.get("结构化院校数")) == len(school_codes_by_page.get(page, set()))
            and as_int(row.get("结构化专业组数")) == group_count_by_page.get(page, 0)
            and as_int(row.get("结构化专业明细数")) == major_count_by_page.get(page, 0)
            and as_int(row.get("结构异常数")) == anomaly_count_by_page.get(page, 0)
            and as_int(row.get("高严重结构异常数")) == high_anomaly_count_by_page.get(page, 0)
            and as_int(row.get("候选V2字段任务数")) == candidate_task_count_by_page.get(page, 0)
            and as_int(row.get("候选V2字段P0任务数")) == candidate_p0_task_count_by_page.get(page, 0)
        )
        if 10 <= page <= 240:
            manifest_page_distribution_ok = manifest_page_distribution_ok and bool(foundation_row) and (
                as_int(row.get("结构化专业组数"))
                == as_int(foundation_row.get("页面专业组数"))
                and as_int(row.get("结构化专业明细数"))
                == as_int(foundation_row.get("页面专业明细数"))
                and as_int(row.get("结构异常数"))
                == as_int(foundation_row.get("页面结构异常数"))
                and as_int(row.get("高严重结构异常数"))
                == as_int(foundation_row.get("页面高严重结构异常数"))
                and row.get("底座页级复核优先级") == foundation_row.get("页面复核优先级")
                and row.get("底座页级审计状态") == foundation_row.get("页面审计状态")
            )
        else:
            manifest_page_distribution_ok = manifest_page_distribution_ok and not foundation_row
    checks.append(ok(
        "第 19 期公开页级 manifest 逐页回推到结构化底座和候选总账",
        manifest_page_distribution_ok,
    ))
    checks.append(ok(
        "第 19 期公开页级 manifest 不含本地路径、私有文件路径、图片扩展名和最终可用结论",
        "final_allowed" not in page_manifest_public_text
        and "ready_for_discussion" not in page_manifest_public_text
        and "已确认" not in page_manifest_public_text
        and not any(token in page_manifest_public_text for token in shared_forbidden_tokens),
    ))

    issue19_ocr_summary = json.loads((ROOT / "data/working/issue19-ocr-run-summary.json").read_text())
    checks.append(ok(
        "第 19 期全量 OCR 摘要已记录",
        issue19_ocr_summary["page_count"] == 240
        and issue19_ocr_summary["summary"]["ocr_line_count"] >= 60000
        and issue19_ocr_summary["summary"]["qc_issue_count"] >= 30000
        and issue19_ocr_summary["source_pdf_sha256"] == issue19_source["source"]["sha256"],
    ))

    checksum_path = ROOT / "CHECKSUMS.sha256"
    if checksum_path.exists():
        manifest_ok = True
        manifest_rel_paths = set()
        for line in checksum_path.read_text().splitlines():
            expected, rel = line.split(maxsplit=1)
            manifest_rel_paths.add(rel)
            actual = sha256(ROOT / rel)
            if actual != expected:
                print(f"[失败] 文件哈希不一致 - {rel}")
                manifest_ok = False
        expected_rel_paths = manifest_files()
        missing = sorted(expected_rel_paths - manifest_rel_paths)
        extra = sorted(manifest_rel_paths - expected_rel_paths)
        for rel in missing:
            print(f"[失败] 哈希清单缺少文件 - {rel}")
            manifest_ok = False
        for rel in extra:
            print(f"[失败] 哈希清单包含多余文件 - {rel}")
            manifest_ok = False
        checks.append(ok("哈希清单完整且一致", manifest_ok))
    else:
        checks.append(ok("哈希清单存在", False))

    if not all(checks):
        raise SystemExit(1)
    print("所有基线校验通过。")


if __name__ == "__main__":
    main()
