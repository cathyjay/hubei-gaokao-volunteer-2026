#!/usr/bin/env python3
import csv
import ast
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
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


def script_list_constant(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"{name} not found in {path}")


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
    issue19_source_public_text = (ROOT / "data/working/issue19-pdf-source.json").read_text(encoding="utf-8")
    checks.append(ok(
        "第 19 期 PDF 元数据公开文件不含用户本机绝对路径",
        "/Users/" not in issue19_source_public_text
        and "original_user_path\"" not in issue19_source_public_text,
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

    full_major_fidelity_summary_path = ROOT / "data/working/issue19-full-major-field-fidelity-ledger-summary.json"
    full_major_fidelity_csv = ROOT / "data/working/issue19-full-major-field-fidelity-ledger.csv"
    full_major_fidelity_summary = json.loads(full_major_fidelity_summary_path.read_text())
    with full_major_fidelity_csv.open(newline="", encoding="utf-8-sig") as f:
        full_major_fidelity_reader = csv.DictReader(f)
        full_major_fidelity_rows = list(full_major_fidelity_reader)
        full_major_fidelity_fields = set(full_major_fidelity_reader.fieldnames or [])
    required_full_major_fidelity_fields = {
        "全量保真总账ID",
        "来源主表",
        "来源家庭底线逐专业表",
        "来源家庭底线专业组表",
        "专业行ID",
        "专业组出现ID",
        "主表粒度",
        "全量保真复核优先级",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "是否高风险保真行",
        "风险阻断等级",
        "高风险字段集合",
        "风险触发规则",
        "阻断原因",
        "调剂影响等级",
        "必须核验字段",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组号OCR",
        "专业组标题OCR原文",
        "来源页码",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "专业计划数是否纯数字",
        "学费OCR候选",
        "学费OCR数字候选",
        "学费是否纯数字",
        "专业偏好方向",
        "专业风险类型",
        "专业字段完整性标记",
        "专业行结构异常数",
        "专业行高严重结构异常数",
        "结构异常规则ID列表",
        "逐专业复核优先级",
        "机器专业接受度初判",
        "同组真实招生明细数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "是否可进入最终专业列表",
        "可进入下一阶段",
    }
    def split_cn_semicolon(value):
        return [part for part in str(value or "").split("；") if part]
    full_major_fidelity_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [full_major_fidelity_summary_path, full_major_fidelity_csv]
    )
    full_major_fidelity_ids = {row.get("专业行ID") for row in full_major_fidelity_rows}
    full_major_quality_ids = {row.get("专业行ID") for row in major_quality_rows}
    full_major_fidelity_priority_counts = Counter(
        row.get("全量保真复核优先级") for row in full_major_fidelity_rows
    )
    full_major_fidelity_block_counts = Counter(row.get("风险阻断等级") for row in full_major_fidelity_rows)
    full_major_fidelity_category_counts = Counter()
    full_major_fidelity_rule_counts = Counter()
    for row in full_major_fidelity_rows:
        full_major_fidelity_category_counts.update(split_cn_semicolon(row.get("高风险字段集合")))
        full_major_fidelity_rule_counts.update(split_cn_semicolon(row.get("风险触发规则")))
    full_major_required_core_tokens = [
        "PDF原页",
        "湖北官方系统",
        "高校官网/章程",
        "专业组边界",
        "调剂范围",
        "家庭接受度",
    ]
    checks.append(ok(
        "第 19 期全量逐专业字段保真总账摘要和行数正确",
        full_major_fidelity_summary.get("status") == "issue19_full_major_field_fidelity_ledger_not_final"
        and full_major_fidelity_summary.get("source_major_quality_table")
        == "data/working/issue19-full-major-detail-quality-workbench.csv"
        and full_major_fidelity_summary.get("source_family_major_table")
        == "data/working/issue19-family-fit-major-detail.csv"
        and full_major_fidelity_summary.get("source_family_group_table")
        == "data/working/issue19-family-fit-group-screen.csv"
        and full_major_fidelity_summary.get("output_table")
        == "data/working/issue19-full-major-field-fidelity-ledger.csv"
        and full_major_fidelity_summary.get("major_quality_row_count") == 13736
        and full_major_fidelity_summary.get("family_major_row_count") == 13736
        and full_major_fidelity_summary.get("family_group_row_count") == 3329
        and full_major_fidelity_summary.get("ledger_row_count") == 13736
        and full_major_fidelity_summary.get("unique_major_line_id_count") == 13736
        and full_major_fidelity_summary.get("unique_group_occurrence_id_count") == 3289
        and full_major_fidelity_summary.get("high_risk_row_count") == 13486
        and full_major_fidelity_summary.get("low_risk_row_count") == 250
        and full_major_fidelity_summary.get("empty_major_name_row_count") == 2
        and full_major_fidelity_summary.get("high_structure_anomaly_row_count") == 2862
        and full_major_fidelity_summary.get("plan_count_untrusted_row_count") == 6347
        and full_major_fidelity_summary.get("tuition_untrusted_row_count") == 1262
        and full_major_fidelity_summary.get("family_bottom_line_row_count") == 3516
        and full_major_fidelity_summary.get("preference_major_candidate_row_count") == 1726
        and full_major_fidelity_summary.get("auto_final_list_allowed_count") == 0
        and full_major_fidelity_summary.get("next_stage_allowed_count") == 0
        and len(full_major_fidelity_rows) == 13736,
        f"{len(full_major_fidelity_rows)} full major rows",
    ))
    checks.append(ok(
        "第 19 期全量逐专业字段保真总账字段、主键和粒度正确",
        required_full_major_fidelity_fields.issubset(full_major_fidelity_fields)
        and len({row.get("全量保真总账ID") for row in full_major_fidelity_rows})
        == len(full_major_fidelity_rows)
        and len(full_major_fidelity_ids) == len(full_major_fidelity_rows)
        and full_major_fidelity_ids == full_major_quality_ids
        and all(
            row.get("主表粒度") == "逐专业招生明细"
            and row.get("来源主表") == "data/working/issue19-full-major-detail-quality-workbench.csv"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("数据阶段") == "issue19_full_major_field_fidelity_ledger"
            and row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_full_major_field_fidelity_review"
            and row.get("PDF字段核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/章程字段核验状态") == "pending_school_plan_or_charter_review"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and all(token in row.get("必须核验字段", "") for token in full_major_required_core_tokens)
            for row in full_major_fidelity_rows
        ),
    ))
    checks.append(ok(
        "第 19 期全量逐专业字段保真总账优先级和风险计数闭环正确",
        full_major_fidelity_priority_counts == Counter(full_major_fidelity_summary.get("priority_counts", {}))
        and full_major_fidelity_block_counts == Counter(full_major_fidelity_summary.get("block_level_counts", {}))
        and full_major_fidelity_category_counts == Counter(full_major_fidelity_summary.get("category_counts", {}))
        and full_major_fidelity_summary.get("priority_counts") == {
            "P0-结构/空专业名/串校串行": 2864,
            "P1-计划数保真": 7272,
            "P2-家庭底线与费用": 1183,
            "P3-选科与特殊限制": 1951,
            "P4-调剂风险": 70,
            "P5-偏好专业待研究": 81,
            "P5-普通待核": 65,
            "P6-暂未触发机器高风险": 250,
        }
        and full_major_fidelity_summary.get("block_level_counts") == {
            "F0-阻断级：不得进入候选排序": 3998,
            "F1-高优先：必须逐字段核验": 8240,
            "F2-待补证：字段需核验": 1248,
            "F3-暂未触发机器高风险但仍非最终": 250,
        }
        and full_major_fidelity_rule_counts.get("empty_major_name") == 2
        and full_major_fidelity_rule_counts.get("high_structure_anomaly") == 2862
        and full_major_fidelity_rule_counts.get("missing_subject_candidate") == 11456
        and full_major_fidelity_rule_counts.get("group_has_plan_count_untrusted") == 9259
        and full_major_fidelity_rule_counts.get("preference_major_candidate") == 1726,
    ))
    checks.append(ok(
        "第 19 期全量逐专业字段保真总账高低风险边界和非最终状态正确",
        all(
            row.get("是否高风险保真行") == "true"
            and row.get("高风险字段集合")
            and row.get("风险触发规则")
            for row in full_major_fidelity_rows
            if row.get("全量保真复核优先级") != "P6-暂未触发机器高风险"
        )
        and all(
            row.get("是否高风险保真行") == "false"
            and row.get("风险阻断等级") == "F3-暂未触发机器高风险但仍非最终"
            and row.get("高风险字段集合") == ""
            and row.get("风险触发规则") == ""
            and "仍需按最终志愿门禁" in row.get("阻断原因", "")
            for row in full_major_fidelity_rows
            if row.get("全量保真复核优先级") == "P6-暂未触发机器高风险"
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            for row in full_major_fidelity_rows
        ),
    ))
    checks.append(ok(
        "第 19 期全量逐专业字段保真总账公开文件不含本地路径、图片扩展名、身份信息和最终可用结论",
        "private/" not in full_major_fidelity_public_text
        and "/Users/" not in full_major_fidelity_public_text
        and "ocr-runs" not in full_major_fidelity_public_text
        and "rendered-pages" not in full_major_fidelity_public_text
        and ".png" not in full_major_fidelity_public_text
        and ".jpg" not in full_major_fidelity_public_text
        and ".jpeg" not in full_major_fidelity_public_text
        and "final_allowed" not in full_major_fidelity_public_text
        and "ready_for_discussion" not in full_major_fidelity_public_text
        and "已确认" not in full_major_fidelity_public_text
        and "最终推荐" not in full_major_fidelity_public_text
        and "最终方案" not in full_major_fidelity_public_text
        and not any(token in full_major_fidelity_public_text for token in ["身份证", "准考证", "报名号", "姓名"]),
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

    candidate_v3_detail_summary_path = ROOT / "data/working/issue19-candidate-v3-admission-detail-summary.json"
    candidate_v3_detail_csv = ROOT / "data/working/issue19-candidate-v3-admission-detail.csv"
    candidate_v3_detail_summary = json.loads(candidate_v3_detail_summary_path.read_text())
    with candidate_v3_detail_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v3_detail_reader = csv.DictReader(f)
        candidate_v3_detail_rows = list(candidate_v3_detail_reader)
        candidate_v3_detail_fields = set(candidate_v3_detail_reader.fieldnames or [])
    required_candidate_v3_detail_fields = {
        "招生明细主表行ID",
        "主表粒度",
        "是否真实招生明细",
        "是否0明细占位",
        "组级索引文件",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "候选V3入口ID",
        "复核批次",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业组出现ID",
        "专业行来源",
        "专业行ID",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业偏好方向",
        "专业风险类型",
        "机器专业接受度初判",
        "调剂影响初判",
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
    candidate_v3_detail_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [candidate_v3_detail_summary_path, candidate_v3_detail_csv]
    )
    candidate_v3_detail_source_counts = Counter(row.get("专业行来源") for row in candidate_v3_detail_rows)
    candidate_v3_detail_batch_counts = Counter(row.get("复核批次") for row in candidate_v3_detail_rows)
    candidate_v3_detail_by_entry = Counter(row.get("候选V3入口ID") for row in candidate_v3_detail_rows)
    candidate_v3_detail_zero_codes = {
        row.get("2026院校专业组代码")
        for row in candidate_v3_detail_rows
        if row.get("是否0明细占位") == "true"
    }
    candidate_v3_detail_entry_counts_match = all(
        candidate_v3_detail_by_entry.get(row.get("候选V3入口ID"), 0)
        == ((as_int(row.get("专业明细行数")) or 0) or 1)
        for row in candidate_v3_rows
    )
    checks.append(ok(
        "第 19 期候选V3逐专业招生明细主表摘要、行数和闭环正确",
        candidate_v3_detail_summary.get("status") == "issue19_candidate_v3_admission_detail_not_final"
        and candidate_v3_detail_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and candidate_v3_detail_summary.get("default_discussion_table")
        == "data/working/issue19-candidate-v3-admission-detail.csv"
        and candidate_v3_detail_summary.get("group_index_table")
        == "data/working/issue19-candidate-v3-review-intake.csv"
        and candidate_v3_detail_summary.get("group_index_count") == 1327
        and candidate_v3_detail_summary.get("expected_real_detail_count_from_group_index") == 8410
        and candidate_v3_detail_summary.get("admission_detail_row_count") == 8412
        and candidate_v3_detail_summary.get("real_admission_detail_count") == 8410
        and candidate_v3_detail_summary.get("zero_detail_placeholder_count") == 2
        and candidate_v3_detail_summary.get("row_source_counts") == {
            "candidate_v2_major_review_seed": 82,
            "family_fit_major_detail": 8328,
            "zero_detail_group_placeholder": 2,
        }
        and candidate_v3_detail_summary.get("batch_counts") == {
            "B0-历史候选和组号问题优先核页": 79,
            "B1-数字媒体技术优先核页": 245,
            "B2-偏好专业未自动阻断核页": 4313,
            "B3-偏好专业硬风险先核风险": 3774,
            "B4-同页边界风险组核页": 1,
        }
        and candidate_v3_detail_summary.get("missing_detail_group_count") == 0
        and candidate_v3_detail_summary.get("detail_count_mismatch_group_count") == 0
        and candidate_v3_detail_summary.get("unique_admission_detail_id_count") == 8412
        and candidate_v3_detail_summary.get("final_available_count") == 0
        and candidate_v3_detail_summary.get("major_final_available_count") == 0
        and len(candidate_v3_detail_rows) == 8412,
        f"{len(candidate_v3_detail_rows)} detail rows",
    ))
    checks.append(ok(
        "第 19 期候选V3逐专业招生明细字段、主键和默认闸门正确",
        required_candidate_v3_detail_fields.issubset(candidate_v3_detail_fields)
        and len({row.get("招生明细主表行ID") for row in candidate_v3_detail_rows})
        == len(candidate_v3_detail_rows)
        and candidate_v3_detail_source_counts
        == Counter(candidate_v3_detail_summary.get("row_source_counts", {}))
        and candidate_v3_detail_batch_counts
        == Counter(candidate_v3_detail_summary.get("batch_counts", {}))
        and candidate_v3_detail_entry_counts_match
        and candidate_v3_detail_zero_codes == {"C10702", "K15123"}
        and all(
            row.get("主表粒度") == "逐专业招生明细"
            and row.get("组级索引文件") == "data/working/issue19-candidate-v3-review-intake.csv"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("数据阶段") == "issue19_candidate_v3_admission_detail"
            and row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_v3_detail_manual_review"
            and row.get("PDF字段核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/章程字段核验状态") == "pending_school_plan_or_charter_review"
            and row.get("家庭接受度人工结论状态") == "pending_family_acceptance_review"
            and row.get("调剂影响人工结论状态") == "pending_transfer_decision"
            and row.get("字段核验状态") == "pending"
            and row.get("是否阻断组升级") == "是"
            and row.get("可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            for row in candidate_v3_detail_rows
        )
        and all(
            row.get("是否真实招生明细") == ("false" if row.get("专业行来源") == "zero_detail_group_placeholder" else "true")
            and row.get("是否0明细占位") == ("true" if row.get("专业行来源") == "zero_detail_group_placeholder" else "false")
            for row in candidate_v3_detail_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3逐专业招生明细公开文件不含本地路径、身份信息和最终可用结论",
        "final_allowed" not in candidate_v3_detail_public_text
        and "ready_for_discussion" not in candidate_v3_detail_public_text
        and "已确认" not in candidate_v3_detail_public_text
        and "最终推荐" not in candidate_v3_detail_public_text
        and "最终方案" not in candidate_v3_detail_public_text
        and not any(token in candidate_v3_detail_public_text for token in shared_forbidden_tokens),
    ))

    candidate_v3_detail_queue_summary_path = (
        ROOT / "data/working/issue19-candidate-v3-admission-detail-review-queue-summary.json"
    )
    candidate_v3_detail_queue_csv = (
        ROOT / "data/working/issue19-candidate-v3-admission-detail-review-queue.csv"
    )
    candidate_v3_detail_queue_summary = json.loads(candidate_v3_detail_queue_summary_path.read_text())
    with candidate_v3_detail_queue_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v3_detail_queue_reader = csv.DictReader(f)
        candidate_v3_detail_queue_rows = list(candidate_v3_detail_queue_reader)
        candidate_v3_detail_queue_fields = set(candidate_v3_detail_queue_reader.fieldnames or [])
    required_candidate_v3_detail_queue_fields = {
        "逐专业复核队列ID",
        "来源主表",
        "招生明细主表行ID",
        "核验优先级",
        "核验优先级序号",
        "复核原因",
        "必须核验字段",
        "同组调剂机器风险",
        "同组真实招生明细数",
        "同组0明细占位数",
        "同组默认不能接受专业数",
        "同组暂缓判断专业数",
        "同组偏好专业数",
        "同组数字媒体技术专业数",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "候选V3入口ID",
        "复核批次",
        "入口类型",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "来源页码",
        "私有页图证据编号",
        "专业行来源",
        "是否真实招生明细",
        "是否0明细占位",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业偏好方向",
        "专业风险类型",
        "机器专业接受度初判",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "校区/办学地点字段核验状态",
        "体检/语种/单科/专项限制核验状态",
        "家庭接受度人工结论状态",
        "调剂影响人工结论状态",
        "字段核验状态",
        "专业组完整性人工结论状态",
        "湖北官方系统证据编号",
        "湖北官方系统证据SHA256",
        "高校官网/章程证据编号",
        "高校官网/章程证据SHA256",
        "人工核验人",
        "人工核验时间",
        "人工核验备注",
        "可进入最终专业列表",
        "可进入下一阶段",
        "下一步",
    }
    candidate_v3_detail_queue_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [candidate_v3_detail_queue_summary_path, candidate_v3_detail_queue_csv]
    )
    candidate_v3_detail_queue_priority_counts = Counter(
        row.get("核验优先级") for row in candidate_v3_detail_queue_rows
    )
    candidate_v3_detail_queue_transfer_counts = Counter(
        row.get("同组调剂机器风险") for row in candidate_v3_detail_queue_rows
    )
    candidate_v3_detail_queue_batch_counts = Counter(
        row.get("复核批次") for row in candidate_v3_detail_queue_rows
    )
    candidate_v3_detail_queue_zero_codes = {
        row.get("2026院校专业组代码")
        for row in candidate_v3_detail_queue_rows
        if row.get("是否0明细占位") == "true"
    }
    candidate_v3_detail_queue_suspicious_school_names = {"湖北", "湖南", "上海", "北京"}
    required_candidate_v3_detail_queue_review_tokens = [
        "PDF原页",
        "湖北官方系统/省招办计划",
        "高校官网/招生章程",
        "院校代码和院校名称",
        "院校专业组代码和完整专业组边界",
        "专业代号",
        "专业名称及备注",
        "专业计划数",
        "学费",
        "再选科目",
        "校区/办学地点",
        "体检/语种/单科/专项限制",
        "家庭接受度",
        "调剂影响",
    ]
    candidate_v3_detail_ids = {row.get("招生明细主表行ID") for row in candidate_v3_detail_rows}
    candidate_v3_detail_queue_ids = {
        row.get("招生明细主表行ID") for row in candidate_v3_detail_queue_rows
    }
    checks.append(ok(
        "第 19 期候选V3逐专业复核队列摘要、行数和来源闭环正确",
        candidate_v3_detail_queue_summary.get("status")
        == "issue19_candidate_v3_admission_detail_review_queue_not_final"
        and candidate_v3_detail_queue_summary.get("source_table")
        == "data/working/issue19-candidate-v3-admission-detail.csv"
        and candidate_v3_detail_queue_summary.get("output_table")
        == "data/working/issue19-candidate-v3-admission-detail-review-queue.csv"
        and candidate_v3_detail_queue_summary.get("row_count") == 8412
        and candidate_v3_detail_queue_summary.get("real_admission_detail_count") == 8410
        and candidate_v3_detail_queue_summary.get("zero_detail_placeholder_count") == 2
        and candidate_v3_detail_queue_summary.get("unique_queue_id_count") == 8412
        and candidate_v3_detail_queue_summary.get("final_available_count") == 0
        and candidate_v3_detail_queue_summary.get("major_final_available_count") == 0
        and candidate_v3_detail_queue_summary.get("priority_counts") == {
            "D0-0明细或边界问题先补齐": 58,
            "D1-历史候选逐专业核页": 77,
            "D2-数字媒体技术逐专业核页": 78,
            "D3-偏好专业可接受性核验": 1652,
            "D4-硬风险专业排除或调剂风险核验": 1604,
            "D5-特殊限制专业核验": 639,
            "D6-组内调剂接受度核验": 4304,
        }
        and candidate_v3_detail_queue_summary.get("transfer_risk_counts") == {
            "T0-不可判断：专业明细缺失": 2,
            "T1-高：同组存在默认不能接受专业": 3817,
            "T2-中：同组存在特殊限制待核专业": 1391,
            "T3-待家庭确认：机器未见自动阻断": 3202,
        }
        and len(candidate_v3_detail_queue_rows) == 8412,
        f"{len(candidate_v3_detail_queue_rows)} detail queue rows",
    ))
    checks.append(ok(
        "第 19 期候选V3逐专业复核队列字段、主键、门禁和占位行正确",
        required_candidate_v3_detail_queue_fields.issubset(candidate_v3_detail_queue_fields)
        and len({row.get("逐专业复核队列ID") for row in candidate_v3_detail_queue_rows})
        == len(candidate_v3_detail_queue_rows)
        and candidate_v3_detail_queue_ids == candidate_v3_detail_ids
        and candidate_v3_detail_queue_priority_counts
        == Counter(candidate_v3_detail_queue_summary.get("priority_counts", {}))
        and candidate_v3_detail_queue_transfer_counts
        == Counter(candidate_v3_detail_queue_summary.get("transfer_risk_counts", {}))
        and candidate_v3_detail_queue_batch_counts
        == Counter(candidate_v3_detail_queue_summary.get("batch_counts", {}))
        and candidate_v3_detail_queue_zero_codes == {"C10702", "K15123"}
        and all(
            row.get("来源主表") == "data/working/issue19-candidate-v3-admission-detail.csv"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("数据阶段") == "issue19_candidate_v3_admission_detail_review_queue"
            and row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_v3_detail_review_queue"
            and row.get("校区/办学地点字段核验状态") == "pending_location_review"
            and row.get("体检/语种/单科/专项限制核验状态") == "pending_special_requirement_review"
            and row.get("专业组完整性人工结论状态") == "pending_group_completeness_review"
            and row.get("湖北官方系统证据编号") == ""
            and row.get("湖北官方系统证据SHA256") == ""
            and row.get("高校官网/章程证据编号") == ""
            and row.get("高校官网/章程证据SHA256") == ""
            and row.get("人工核验时间") == ""
            and row.get("可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            for row in candidate_v3_detail_queue_rows
        )
        and all(
            row.get("院校代码")
            and row.get("院校名称OCR")
            and row.get("2026院校专业组代码")
            and row.get("来源页码")
            and row.get("私有页图证据编号")
            and row.get("专业代号OCR")
            and row.get("专业名称及备注OCR")
            and all(token in row.get("必须核验字段", "") for token in required_candidate_v3_detail_queue_review_tokens)
            and (
                row.get("专业计划数OCR候选")
                or row.get("专业字段完整性标记")
            )
            and (
                row.get("学费OCR候选")
                or row.get("专业字段完整性标记")
            )
            and (
                row.get("再选科目OCR候选")
                or row.get("专业字段完整性标记")
            )
            for row in candidate_v3_detail_queue_rows
            if row.get("是否真实招生明细") == "true"
        )
        and all(
            row.get("同组调剂机器风险") == "T0-不可判断：专业明细缺失"
            and row.get("是否真实招生明细") == "false"
            and row.get("专业行来源") == "zero_detail_group_placeholder"
            and not row.get("专业代号OCR")
            and not row.get("专业名称及备注OCR")
            and not row.get("专业计划数OCR候选")
            and not row.get("学费OCR候选")
            and row.get("同组真实招生明细数") == "0"
            and "补齐专业组内全部招生明细" in row.get("必须核验字段", "")
            for row in candidate_v3_detail_queue_rows
            if row.get("是否0明细占位") == "true"
        )
        and all(
            row.get("核验优先级") == "D0-0明细或边界问题先补齐"
            and "院校名称 OCR 疑似截断" in row.get("复核原因", "")
            for row in candidate_v3_detail_queue_rows
            if row.get("院校名称OCR") in candidate_v3_detail_queue_suspicious_school_names
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3逐专业复核队列公开文件不含本地路径、身份信息和最终可用结论",
        "final_allowed" not in candidate_v3_detail_queue_public_text
        and "ready_for_discussion" not in candidate_v3_detail_queue_public_text
        and "已确认" not in candidate_v3_detail_queue_public_text
        and "最终推荐" not in candidate_v3_detail_queue_public_text
        and "最终方案" not in candidate_v3_detail_queue_public_text
        and not any(token in candidate_v3_detail_queue_public_text for token in shared_forbidden_tokens),
    ))

    candidate_v3_d0_summary_path = ROOT / "data/working/issue19-candidate-v3-d0-resolution-workbench-summary.json"
    candidate_v3_d0_csv = ROOT / "data/working/issue19-candidate-v3-d0-resolution-workbench.csv"
    candidate_v3_d0_summary = json.loads(candidate_v3_d0_summary_path.read_text())
    with candidate_v3_d0_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v3_d0_reader = csv.DictReader(f)
        candidate_v3_d0_rows = list(candidate_v3_d0_reader)
        candidate_v3_d0_fields = set(candidate_v3_d0_reader.fieldnames or [])
    required_candidate_v3_d0_fields = {
        "D0工作台ID",
        "来源逐专业复核队列ID",
        "招生明细主表行ID",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "D0问题类型",
        "核验结论状态",
        "院校代码",
        "院校名称OCR",
        "建议完整院校名称",
        "建议来源",
        "建议证据强度",
        "同代码专业组标题建议名称一致性",
        "历年投档线命中年份",
        "历年投档线院校名线索",
        "历年投档线样例",
        "是否需要历年代码校名佐证",
        "代码冲突标记",
        "疑似字符混淆",
        "修正建议状态",
        "2026院校专业组代码",
        "专业组标题OCR原文",
        "来源页码",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "页面OCR是否出现候选组号",
        "同校第19期OCR专业组",
        "同校第19期OCR页码",
        "页面组号异常类型",
        "专业行来源",
        "是否真实招生明细",
        "是否0明细占位",
        "专业代号OCR",
        "专业名称及备注OCR",
        "同组调剂机器风险",
        "是否可自动写回主表",
        "可进入下一阶段",
        "下一步",
    }
    candidate_v3_d0_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [candidate_v3_d0_summary_path, candidate_v3_d0_csv]
    )
    candidate_v3_d0_issue_counts = Counter()
    for row in candidate_v3_d0_rows:
        for item in row.get("D0问题类型", "").split("；"):
            if item:
                candidate_v3_d0_issue_counts[item] += 1
    candidate_v3_d0_by_code = {
        row.get("2026院校专业组代码"): row for row in candidate_v3_d0_rows
    }
    candidate_v3_d0_zero_codes = {
        row.get("2026院校专业组代码")
        for row in candidate_v3_d0_rows
        if row.get("是否0明细占位") == "true"
    }
    checks.append(ok(
        "第 19 期候选V3 D0修正/核验工作台摘要和行数正确",
        candidate_v3_d0_summary.get("status") == "issue19_candidate_v3_d0_resolution_workbench_not_final"
        and candidate_v3_d0_summary.get("source_queue")
        == "data/working/issue19-candidate-v3-admission-detail-review-queue.csv"
        and candidate_v3_d0_summary.get("output_table")
        == "data/working/issue19-candidate-v3-d0-resolution-workbench.csv"
        and candidate_v3_d0_summary.get("row_count") == 58
        and candidate_v3_d0_summary.get("unique_group_count") == 17
        and candidate_v3_d0_summary.get("issue_counts") == {
            "0明细占位": 2,
            "专业组边界或明细缺失": 58,
            "院校名称OCR疑似截断": 55,
        }
        and candidate_v3_d0_summary.get("school_ocr_counts") == {
            "武汉体育学院": 2,
            "湖北": 22,
            "北京": 5,
            "上海": 9,
            "山东": 2,
            "湖南": 17,
            "成都理工大学": 1,
        }
        and candidate_v3_d0_summary.get("extracted_full_school_name_count") == 56
        and candidate_v3_d0_summary.get("name_correction_needed_count") == 55
        and candidate_v3_d0_summary.get("zero_detail_placeholder_count") == 2
        and candidate_v3_d0_summary.get("history_supported_name_count") == 55
        and candidate_v3_d0_summary.get("code_conflict_count") == 5
        and candidate_v3_d0_summary.get("auto_writeback_allowed_count") == 0
        and candidate_v3_d0_summary.get("next_stage_allowed_count") == 0
        and len(candidate_v3_d0_rows) == 58,
        f"{len(candidate_v3_d0_rows)} D0 rows",
    ))
    checks.append(ok(
        "第 19 期候选V3 D0工作台字段、建议和闸门正确",
        required_candidate_v3_d0_fields.issubset(candidate_v3_d0_fields)
        and len({row.get("D0工作台ID") for row in candidate_v3_d0_rows}) == len(candidate_v3_d0_rows)
        and candidate_v3_d0_issue_counts == Counter(candidate_v3_d0_summary.get("issue_counts", {}))
        and candidate_v3_d0_zero_codes == {"C10702", "K15123"}
        and all(
            row.get("数据阶段") == "issue19_candidate_v3_d0_resolution_workbench"
            and row.get("最终可用") == "false"
            and row.get("核验结论状态") == "pending_d0_manual_review"
            and row.get("是否可自动写回主表") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            for row in candidate_v3_d0_rows
        )
        and all(
            row.get("建议完整院校名称")
            and "仍需PDF原页和官方系统核验" in row.get("修正建议状态", "")
            for row in candidate_v3_d0_rows
            if "院校名称OCR疑似截断" in row.get("D0问题类型", "")
        )
        and candidate_v3_d0_by_code.get("C13709", {}).get("建议完整院校名称") == "湖北第二师范学院"
        and candidate_v3_d0_by_code.get("F79701", {}).get("建议完整院校名称") == "上海第二工业大学"
        and candidate_v3_d0_by_code.get("H68602", {}).get("建议完整院校名称") == "湖南第一师范学院"
        and candidate_v3_d0_by_code.get("H42516", {}).get("建议完整院校名称") == "山东第一医科大学"
        and candidate_v3_d0_by_code.get("F01203", {}).get("建议完整院校名称") == "北京第二外国语学院"
        and candidate_v3_d0_by_code.get("P01202", {}).get("建议完整院校名称") == "北京第二外国语学院"
        and candidate_v3_d0_by_code.get("C13709", {}).get("历年投档线院校名线索") == "湖北第二师范学院"
        and candidate_v3_d0_by_code.get("F79701", {}).get("历年投档线院校名线索") == "上海第二工业大学"
        and candidate_v3_d0_by_code.get("H68602", {}).get("历年投档线院校名线索") == "湖南第一师范学院"
        and candidate_v3_d0_by_code.get("H42516", {}).get("历年投档线院校名线索") == "山东第一医科大学"
        and candidate_v3_d0_by_code.get("P01202", {}).get("历年投档线命中年份") == ""
        and "禁止自动修正" in candidate_v3_d0_by_code.get("P01202", {}).get("代码冲突标记", "")
        and candidate_v3_d0_by_code.get("P01202", {}).get("疑似字符混淆") == "是"
        and "OCR含F/O/P/0易混字符" in candidate_v3_d0_by_code.get("F01203", {}).get("代码冲突标记", "")
        and all(
            row.get("页面OCR是否出现候选组号") == "否"
            and row.get("修正建议状态") == "未在全量结构化专业组表/页面OCR命中-需核2026组号是否变化或取消"
            and "不得进入最终候选" in row.get("下一步", "")
            for row in candidate_v3_d0_rows
            if row.get("是否0明细占位") == "true"
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3 D0工作台公开文件不含本地路径、身份信息和最终可用结论",
        "private/" not in candidate_v3_d0_public_text
        and "final_allowed" not in candidate_v3_d0_public_text
        and "ready_for_discussion" not in candidate_v3_d0_public_text
        and "已确认" not in candidate_v3_d0_public_text
        and "最终推荐" not in candidate_v3_d0_public_text
        and "最终方案" not in candidate_v3_d0_public_text
        and not any(token in candidate_v3_d0_public_text for token in shared_forbidden_tokens),
    ))

    candidate_v3_d0_pdf_summary_path = ROOT / "data/working/issue19-candidate-v3-d0-pdf-page-evidence-summary.json"
    candidate_v3_d0_pdf_csv = ROOT / "data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv"
    candidate_v3_d0_pdf_summary = json.loads(candidate_v3_d0_pdf_summary_path.read_text())
    with candidate_v3_d0_pdf_csv.open(newline="", encoding="utf-8-sig") as f:
        candidate_v3_d0_pdf_reader = csv.DictReader(f)
        candidate_v3_d0_pdf_rows = list(candidate_v3_d0_pdf_reader)
        candidate_v3_d0_pdf_fields = set(candidate_v3_d0_pdf_reader.fieldnames or [])
    required_candidate_v3_d0_pdf_fields = {
        "D0原页证据ID",
        "来源D0工作台文件",
        "来源D0任务数",
        "真实招生明细行数",
        "0明细占位行数",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "院校代码",
        "院校名称OCR",
        "建议完整院校名称",
        "2026院校专业组代码",
        "是否0明细占位组",
        "PDF证据页码",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "OCR引擎",
        "渲染DPI",
        "OCR语言",
        "页面OCR匹配方式",
        "OCR标题命中状态",
        "OCR命中变体",
        "标题代码与2026组代码关系",
        "OCR标题行号",
        "OCR标题行置信度",
        "OCR标题行SHA256",
        "OCR标题行原文",
        "结构化组表是否出现",
        "结构化专业明细数",
        "结构异常规则ID",
        "保守等级",
        "是否可写回D0建议",
        "可进入下一阶段",
    }
    candidate_v3_d0_pdf_by_code = {
        row.get("2026院校专业组代码"): row for row in candidate_v3_d0_pdf_rows
    }
    candidate_v3_d0_pdf_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [candidate_v3_d0_pdf_summary_path, candidate_v3_d0_pdf_csv]
    )
    def split_semicolon(value):
        return [part for part in str(value or "").split("；") if part]
    def all_private_ids_and_hashes_ok(row):
        page_ids = split_semicolon(row.get("私有页图证据编号"))
        text_ids = split_semicolon(row.get("私有OCR文本证据编号"))
        page_hashes = split_semicolon(row.get("私有页图SHA256"))
        text_hashes = split_semicolon(row.get("私有OCR文本SHA256"))
        return (
            page_ids
            and text_ids
            and all(re.fullmatch(r"page-\d{3}", item) for item in page_ids)
            and all(re.fullmatch(r"\d{3}_page-\d{3}", item) for item in text_ids)
            and all(re.fullmatch(r"[0-9a-f]{64}", item) for item in page_hashes)
            and all(re.fullmatch(r"[0-9a-f]{64}", item) for item in text_hashes)
        )
    checks.append(ok(
        "第 19 期候选V3 D0原页OCR证据摘要和行数正确",
        candidate_v3_d0_pdf_summary.get("status") == "issue19_candidate_v3_d0_pdf_page_evidence_not_final"
        and candidate_v3_d0_pdf_summary.get("source_d0_workbench")
        == "data/working/issue19-candidate-v3-d0-resolution-workbench.csv"
        and candidate_v3_d0_pdf_summary.get("output_table")
        == "data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv"
        and candidate_v3_d0_pdf_summary.get("row_count") == 17
        and candidate_v3_d0_pdf_summary.get("source_d0_task_count") == 58
        and candidate_v3_d0_pdf_summary.get("match_method_counts") == {
            "exact_match": 13,
            "missing_in_page_and_structured": 2,
            "normalized_o0_match": 2,
        }
        and candidate_v3_d0_pdf_summary.get("exact_title_hit_count") == 13
        and candidate_v3_d0_pdf_summary.get("confusable_title_hit_count") == 2
        and candidate_v3_d0_pdf_summary.get("no_title_hit_count") == 2
        and candidate_v3_d0_pdf_summary.get("zero_detail_group_count") == 2
        and candidate_v3_d0_pdf_summary.get("structured_group_hit_count") == 15
        and candidate_v3_d0_pdf_summary.get("structured_group_missing_count") == 2
        and candidate_v3_d0_pdf_summary.get("auto_writeback_allowed_count") == 0
        and candidate_v3_d0_pdf_summary.get("next_stage_allowed_count") == 0
        and len(candidate_v3_d0_pdf_rows) == 17,
        f"{len(candidate_v3_d0_pdf_rows)} groups",
    ))
    checks.append(ok(
        "第 19 期候选V3 D0原页OCR证据字段、组集合和闸门正确",
        required_candidate_v3_d0_pdf_fields.issubset(candidate_v3_d0_pdf_fields)
        and set(candidate_v3_d0_pdf_by_code) == set(candidate_v3_d0_by_code)
        and len({row.get("D0原页证据ID") for row in candidate_v3_d0_pdf_rows}) == len(candidate_v3_d0_pdf_rows)
        and sum(as_int(row.get("来源D0任务数")) or 0 for row in candidate_v3_d0_pdf_rows) == 58
        and sum(as_int(row.get("真实招生明细行数")) or 0 for row in candidate_v3_d0_pdf_rows) == 56
        and sum(as_int(row.get("0明细占位行数")) or 0 for row in candidate_v3_d0_pdf_rows) == 2
        and all(
            row.get("数据阶段") == "issue19_candidate_v3_d0_pdf_page_evidence"
            and row.get("最终可用") == "false"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("是否可写回D0建议") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("渲染DPI") == "120"
            and all_private_ids_and_hashes_ok(row)
            and all(1 <= (as_int(page) or 0) <= 240 for page in split_semicolon(row.get("PDF证据页码")))
            for row in candidate_v3_d0_pdf_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3 D0原页OCR证据关键风险组保持保守",
        candidate_v3_d0_pdf_by_code.get("C10702", {}).get("页面OCR匹配方式") == "missing_in_page_and_structured"
        and candidate_v3_d0_pdf_by_code.get("C10702", {}).get("0明细占位行数") == "1"
        and candidate_v3_d0_pdf_by_code.get("C10702", {}).get("真实招生明细行数") == "0"
        and candidate_v3_d0_pdf_by_code.get("C10702", {}).get("结构化组表是否出现") == "否"
        and candidate_v3_d0_pdf_by_code.get("C10702", {}).get("保守等级") == "P0-必须人工原页核验"
        and candidate_v3_d0_pdf_by_code.get("K15123", {}).get("页面OCR匹配方式") == "missing_in_page_and_structured"
        and candidate_v3_d0_pdf_by_code.get("K15123", {}).get("0明细占位行数") == "1"
        and candidate_v3_d0_pdf_by_code.get("K15123", {}).get("真实招生明细行数") == "0"
        and candidate_v3_d0_pdf_by_code.get("K15123", {}).get("结构化组表是否出现") == "否"
        and candidate_v3_d0_pdf_by_code.get("K15123", {}).get("保守等级") == "P0-必须人工原页核验"
        and candidate_v3_d0_pdf_by_code.get("P01202", {}).get("页面OCR匹配方式") == "normalized_o0_match"
        and candidate_v3_d0_pdf_by_code.get("P01202", {}).get("OCR命中变体") == "PO1202"
        and candidate_v3_d0_pdf_by_code.get("P01202", {}).get("标题代码与2026组代码关系") == "字符混淆命中-禁止自动写回"
        and candidate_v3_d0_pdf_by_code.get("F01203", {}).get("页面OCR匹配方式") == "normalized_o0_match"
        and candidate_v3_d0_pdf_by_code.get("F01203", {}).get("OCR命中变体") == "FO1203"
        and candidate_v3_d0_pdf_by_code.get("F01203", {}).get("标题代码与2026组代码关系") == "字符混淆命中-禁止自动写回"
        and candidate_v3_d0_pdf_by_code.get("C10705", {}).get("页面OCR匹配方式") == "exact_match"
        and "major_text_embeds_other_school_marker" in candidate_v3_d0_pdf_by_code.get("C10705", {}).get("结构异常规则ID", "")
        and "plan_count_number_ge_1000" in candidate_v3_d0_pdf_by_code.get("C10705", {}).get("结构异常规则ID", "")
        and candidate_v3_d0_pdf_by_code.get("C10705", {}).get("保守等级") == "P0-必须人工原页核验",
    ))
    checks.append(ok(
        "第 19 期候选V3 D0原页OCR证据公开文件不含私有路径、整页文本、图片路径和最终可用结论",
        "private/" not in candidate_v3_d0_pdf_public_text
        and "/Users/" not in candidate_v3_d0_pdf_public_text
        and "ocr-runs" not in candidate_v3_d0_pdf_public_text
        and "rendered-pages" not in candidate_v3_d0_pdf_public_text
        and ".png" not in candidate_v3_d0_pdf_public_text
        and ".jpg" not in candidate_v3_d0_pdf_public_text
        and ".jpeg" not in candidate_v3_d0_pdf_public_text
        and "final_allowed" not in candidate_v3_d0_pdf_public_text
        and "ready_for_discussion" not in candidate_v3_d0_pdf_public_text
        and "已确认" not in candidate_v3_d0_pdf_public_text
        and "最终推荐" not in candidate_v3_d0_pdf_public_text
        and "最终方案" not in candidate_v3_d0_pdf_public_text
        and not any(token in candidate_v3_d0_pdf_public_text for token in ["身份证", "准考证", "报名号", "姓名"]),
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
    b0_b1_plan_conflict_csv = ROOT / "data/working/issue19-b0-b1-plan-conflict-review-queue.csv"
    b0_b1_unmatched_major_csv = ROOT / "data/working/issue19-b0-b1-unmatched-major-review-queue.csv"
    b0_b1_source_gap_csv = ROOT / "data/working/issue19-b0-b1-official-source-gap-priority.csv"
    b0_b1_fidelity_summary_path = ROOT / "data/working/issue19-b0-b1-fidelity-review-summary.json"
    xztu_extracted_csv = ROOT / "data/external/issue19-b0-b1-official-sources/xztu-2026-hubei-physics-plan-extracted.csv"
    sdtbu_extracted_csv = ROOT / "data/external/issue19-b0-b1-official-sources/sdtbu-2026-hubei-physics-plan-extracted.csv"
    sdtbu_audit_csv = ROOT / "data/external/issue19-b0-b1-official-sources/sdtbu-2026-pdf-ocr-grid-audit.csv"
    jsut_extracted_csv = ROOT / "data/external/issue19-b0-b1-official-sources/jsut-2026-hubei-physics-plan-extracted.csv"
    b0_b1_official_summary = json.loads(b0_b1_official_summary_path.read_text())
    b0_b1_official_evidence_match_summary = json.loads(b0_b1_official_evidence_match_summary_path.read_text())
    b0_b1_fidelity_summary = json.loads(b0_b1_fidelity_summary_path.read_text())
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
    with b0_b1_plan_conflict_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_plan_conflict_reader = csv.DictReader(f)
        b0_b1_plan_conflict_rows = list(b0_b1_plan_conflict_reader)
        b0_b1_plan_conflict_fields = set(b0_b1_plan_conflict_reader.fieldnames or [])
    with b0_b1_unmatched_major_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_unmatched_major_reader = csv.DictReader(f)
        b0_b1_unmatched_major_rows = list(b0_b1_unmatched_major_reader)
        b0_b1_unmatched_major_fields = set(b0_b1_unmatched_major_reader.fieldnames or [])
    with b0_b1_source_gap_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_source_gap_reader = csv.DictReader(f)
        b0_b1_source_gap_rows = list(b0_b1_source_gap_reader)
        b0_b1_source_gap_fields = set(b0_b1_source_gap_reader.fieldnames or [])
    with xztu_extracted_csv.open(newline="", encoding="utf-8-sig") as f:
        xztu_extracted_rows = list(csv.DictReader(f))
    with sdtbu_extracted_csv.open(newline="", encoding="utf-8-sig") as f:
        sdtbu_extracted_rows = list(csv.DictReader(f))
    with sdtbu_audit_csv.open(newline="", encoding="utf-8-sig") as f:
        sdtbu_audit_rows = list(csv.DictReader(f))
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
    b0_b1_plan_conflict_type_counts = Counter(row.get("冲突类型") for row in b0_b1_plan_conflict_rows)
    b0_b1_plan_conflict_school_counts = Counter(row.get("院校名称") for row in b0_b1_plan_conflict_rows)
    b0_b1_unmatched_major_type_counts = Counter(row.get("未匹配类型") for row in b0_b1_unmatched_major_rows)
    b0_b1_source_gap_type_counts = Counter(row.get("结构化证据缺口类型") for row in b0_b1_source_gap_rows)
    b0_b1_source_gap_priority_counts = Counter(row.get("补源优先级") for row in b0_b1_source_gap_rows)
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
    b0_b1_detail_ledger_by_detail_id = {
        row.get("招生明细主表行ID"): row for row in b0_b1_detail_evidence_ledger_rows
    }
    xztu_extracted_plan_by_major = {
        row.get("专业名称"): row.get("湖北计划数") for row in xztu_extracted_rows
    }
    sdtbu_extracted_plan_by_major = {
        row.get("专业名称"): row.get("湖北计划数") for row in sdtbu_extracted_rows
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
    required_b0_b1_plan_conflict_fields = {
        "复核优先级",
        "冲突类型",
        "招生明细主表行ID",
        "来源页码",
        "院校代码",
        "院校名称",
        "2026院校专业组代码",
        "专业代号OCR",
        "专业名称及备注OCR",
        "OCR计划数候选",
        "官网专业名称",
        "官网计划数",
        "官网学费",
        "官网来源文件",
        "保真处理状态",
        "保真诊断",
        "计划数候选引用方式",
        "核页重点",
        "下一步",
    }
    required_b0_b1_unmatched_major_fields = {
        "复核优先级",
        "未匹配类型",
        "招生明细主表行ID",
        "来源页码",
        "院校代码",
        "院校名称",
        "2026院校专业组代码",
        "专业代号OCR",
        "专业名称及备注OCR",
        "OCR计划数候选",
        "官网来源状态",
        "官网证据覆盖结论",
        "专业名称匹配方式",
        "仍需核验",
        "核页重点",
        "下一步",
    }
    required_b0_b1_source_gap_fields = {
        "补源优先级",
        "结构化证据缺口类型",
        "院校代码",
        "院校名称",
        "官网来源状态",
        "B0B1专业组数",
        "逐专业核验任务数",
        "涉及专业组代码",
        "官网URL",
        "本地留存状态",
        "是否可核湖北2026",
        "可核字段",
        "局限性",
        "官方源缺口",
        "下一步",
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
            b0_b1_plan_conflict_csv,
            b0_b1_unmatched_major_csv,
            b0_b1_source_gap_csv,
            b0_b1_fidelity_summary_path,
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
        and b0_b1_official_evidence_match_summary.get("normalized_official_row_count") == 434
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
            "山东工商学院",
            "忻州师范学院",
            "成都信息工程大学",
            "杭州电子科技大学",
            "武汉商学院",
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
            "official_pdf_table_extracted_csv": 39,
            "official_image_table_extracted_csv": 15,
            "official_static_html_joined_tables": 43,
        }
        and b0_b1_official_evidence_match_summary.get("match_status_counts") == {
            "no_school_source": 140,
            "unmatched": 31,
            "matched": 152,
            "possible_match": 1,
        }
        and b0_b1_official_evidence_match_summary.get("plan_check_status_counts") == {
            "not_covered": 171,
            "ocr_plan_missing_official_available": 55,
            "official_plan_missing": 19,
            "match": 61,
            "mismatch": 18,
        }
        and b0_b1_official_evidence_match_summary.get("fidelity_status_counts") == {
            "有官网线索但未结构化匹配": 29,
            "占位行-不是真实招生明细": 2,
            "仅章程规则线索-无结构化计划证据": 43,
            "待补高校官网计划源": 66,
            "官网未匹配-专业名或OCR待核": 31,
            "官网可补OCR计划数-优先核页": 55,
            "待人工复核": 18,
            "官网专业名和计划数一致-仍待湖北官方系统和PDF原页复核": 61,
            "疑似匹配-人工确认": 1,
            "官网专业名匹配但计划数冲突-优先核页": 18,
        }
        and b0_b1_official_evidence_match_summary.get("matched_school_counts") == {
            "西安医学院": 2,
            "武汉商学院": 32,
            "忻州师范学院": 4,
            "江苏理工学院": 12,
            "杭州电子科技大学": 10,
            "山东工商学院": 15,
            "中国传媒大学": 9,
            "南宁学院": 4,
            "成都信息工程大学": 19,
            "西安邮电大学": 19,
            "喀什大学": 6,
            "山东大学": 3,
            "兰州大学": 7,
            "西北民族大学": 3,
            "江汉大学": 7,
        }
        and required_b0_b1_retained_official_fields.issubset(b0_b1_retained_official_fields)
        and required_b0_b1_evidence_match_fields.issubset(b0_b1_official_evidence_match_fields)
        and required_b0_b1_detail_evidence_ledger_fields.issubset(b0_b1_detail_evidence_ledger_fields)
        and len(b0_b1_retained_official_rows) == 434
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
        "山东工商学院官网PDF抽取表保留湖北物理类逐专业明细和OCR网格审计表",
        len(sdtbu_extracted_rows) == 24
        and len(sdtbu_audit_rows) == 42
        and all(row.get("学校名称") == "山东工商学院" for row in sdtbu_extracted_rows)
        and all(row.get("科类") == "物理" for row in sdtbu_extracted_rows)
        and sdtbu_extracted_plan_by_major.get("人工智能") == "3"
        and sdtbu_extracted_plan_by_major.get("数字媒体技术") == "2"
        and sdtbu_extracted_plan_by_major.get("计算机科学与技术") == "3"
        and sdtbu_extracted_plan_by_major.get("通信工程") == "1"
        and sdtbu_extracted_plan_by_major.get("数据科学与大数据技术") == "1"
        and sdtbu_extracted_plan_by_major.get("信息管理与信息系统") == "4"
        and any(
            row.get("专业名称OCR") == "信息箵理与信息系统"
            and row.get("专业名称") == "信息管理与信息系统"
            and "人工复核校正" in row.get("专业名称校正说明", "")
            for row in sdtbu_extracted_rows
        )
        and all(
            row.get("原始PDF") == "data/external/issue19-b0-b1-official-sources/sdtbu-2026-province-major-plan.pdf"
            and row.get("湖北列索引") == "13"
            and row.get("提取方法") == "pdf_grid_numbers_plus_apple_vision_ocr_major_column"
            and "湖北院校专业组代码" in row.get("提取局限性", "")
            for row in sdtbu_extracted_rows
        )
        and any(
            row.get("专业名称") == "信用风险管理与法律防控"
            and row.get("纳入湖北物理类匹配表") == "否"
            and "人工复核校正" in row.get("专业名称校正说明", "")
            for row in sdtbu_audit_rows
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
        "武汉商学院官网双表已标准化为逐专业明细且保留物理类计划数边界",
        sum(row.get("学校名称") == "武汉商学院" for row in b0_b1_retained_official_rows) == 43
        and sum(
            1
            for row in b0_b1_retained_official_rows
            if row.get("学校名称") == "武汉商学院" and row.get("计划数")
        )
        == 14
        and sum(
            1
            for row in b0_b1_retained_official_rows
            if row.get("学校名称") == "武汉商学院" and not row.get("计划数")
        )
        == 29
        and retained_official_by_school_major.get(("武汉商学院", "软件工程"), {}).get("计划数") == "58"
        and retained_official_by_school_major.get(("武汉商学院", "物联网工程(智能系统方向)"), {}).get("计划数") == "60"
        and retained_official_by_school_major.get(("武汉商学院", "数据科学与大数据技术"), {}).get("计划数") == "67"
        and retained_official_by_school_major.get(("武汉商学院", "数字经济"), {}).get("计划数") == "63"
        and retained_official_by_school_major.get(("武汉商学院", "烹饪与营养教育"), {}).get("计划数") == "70"
        and retained_official_by_school_major.get(("武汉商学院", "零售业管理（智慧运营方向）"), {}).get("计划数") == ""
        and retained_official_by_school_major.get(("武汉商学院", "经济与金融"), {}).get("计划数") == ""
        and all(
            row.get("证据类型") == "official_static_html_joined_tables"
            and row.get("年份") == "2026"
            and row.get("省份") == "湖北"
            and "第19期原页及湖北官方系统" in row.get("局限性", "")
            for row in b0_b1_retained_official_rows
            if row.get("学校名称") == "武汉商学院"
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
        "B0/B1保真复核队列摘要、行数和类型分布正确",
        b0_b1_fidelity_summary.get("status") == "b0_b1_fidelity_review_queues_not_final"
        and b0_b1_fidelity_summary.get("plan_conflict_row_count") == 18
        and b0_b1_fidelity_summary.get("unmatched_major_row_count") == 32
        and b0_b1_fidelity_summary.get("source_gap_school_count") == 19
        and b0_b1_fidelity_summary.get("plan_conflict_type_counts") == {
            "OCR计划数疑似误取学费": 13,
            "OCR计划数与官网计划数不一致": 5,
        }
        and b0_b1_fidelity_summary.get("plan_conflict_school_counts") == {
            "江苏理工学院": 10,
            "山东工商学院": 1,
            "中国传媒大学": 1,
            "南宁学院": 3,
            "成都信息工程大学": 2,
            "山东大学": 1,
        }
        and b0_b1_fidelity_summary.get("unmatched_major_type_counts") == {
            "官网留存证据未覆盖关键限定词专业": 17,
            "官网留存证据未匹配该专业": 8,
            "专业代号非数字疑似OCR噪声": 3,
            "OCR专业名疑似串入下一院校": 4,
        }
        and b0_b1_fidelity_summary.get("source_gap_type_counts") == {
            "需继续寻找高校官网湖北2026计划": 8,
            "有官网线索但尚未结构化到逐专业证据": 11,
        }
        and b0_b1_fidelity_summary.get("source_gap_priority_counts") == {
            "P0-待补官方计划源": 8,
            "P1-已有线索待结构化": 11,
        }
        and required_b0_b1_plan_conflict_fields.issubset(b0_b1_plan_conflict_fields)
        and required_b0_b1_unmatched_major_fields.issubset(b0_b1_unmatched_major_fields)
        and required_b0_b1_source_gap_fields.issubset(b0_b1_source_gap_fields)
        and len(b0_b1_plan_conflict_rows) == 18
        and len(b0_b1_unmatched_major_rows) == 32
        and len(b0_b1_source_gap_rows) == 19
        and b0_b1_plan_conflict_type_counts == Counter(
            b0_b1_fidelity_summary.get("plan_conflict_type_counts", {})
        )
        and b0_b1_plan_conflict_school_counts == Counter(
            b0_b1_fidelity_summary.get("plan_conflict_school_counts", {})
        )
        and b0_b1_unmatched_major_type_counts == Counter(
            b0_b1_fidelity_summary.get("unmatched_major_type_counts", {})
        )
        and b0_b1_source_gap_type_counts == Counter(
            b0_b1_fidelity_summary.get("source_gap_type_counts", {})
        )
        and b0_b1_source_gap_priority_counts == Counter(
            b0_b1_fidelity_summary.get("source_gap_priority_counts", {})
        ),
    ))
    checks.append(ok(
        "B0/B1保真复核队列与逐专业证据合并表精确对应",
        {row.get("招生明细主表行ID") for row in b0_b1_plan_conflict_rows}
        == {
            row.get("招生明细主表行ID")
            for row in b0_b1_detail_evidence_ledger_rows
            if row.get("计划数核验状态") == "mismatch"
        }
        and {row.get("招生明细主表行ID") for row in b0_b1_unmatched_major_rows}
        == {
            row.get("招生明细主表行ID")
            for row in b0_b1_detail_evidence_ledger_rows
            if row.get("官网证据匹配状态") in {"unmatched", "possible_match"}
        }
        and all(
            b0_b1_detail_ledger_by_detail_id.get(row.get("招生明细主表行ID"), {}).get("计划数核验状态")
            == "mismatch"
            and row.get("核页重点")
            and row.get("下一步")
            for row in b0_b1_plan_conflict_rows
        )
        and all(
            b0_b1_detail_ledger_by_detail_id.get(row.get("招生明细主表行ID"), {}).get("官网证据匹配状态")
            in {"unmatched", "possible_match"}
            and row.get("核页重点")
            and row.get("下一步")
            for row in b0_b1_unmatched_major_rows
        )
        and {
            row.get("院校名称")
            for row in b0_b1_source_gap_rows
            if row.get("补源优先级") == "P0-待补官方计划源"
        }
        == {
            "武汉轻工大学",
            "湖北师范大学",
            "长春工业大学",
            "浙江传媒学院",
            "浙江工业大学",
            "西安航空学院",
            "成都师范学院",
            "韶关学院",
        }
        and all(row.get("下一步") and row.get("官方源缺口") for row in b0_b1_source_gap_rows),
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

    v3_fidelity_ledger_summary_path = (
        ROOT / "data/working/issue19-candidate-v3-major-field-fidelity-ledger-summary.json"
    )
    v3_fidelity_ledger_csv = ROOT / "data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv"
    v3_fidelity_ledger_summary = json.loads(v3_fidelity_ledger_summary_path.read_text())
    with v3_fidelity_ledger_csv.open(newline="", encoding="utf-8-sig") as f:
        v3_fidelity_ledger_reader = csv.DictReader(f)
        v3_fidelity_ledger_rows = list(v3_fidelity_ledger_reader)
        v3_fidelity_ledger_fields = set(v3_fidelity_ledger_reader.fieldnames or [])
    required_v3_fidelity_ledger_fields = {
        "保真总账ID",
        "来源主表",
        "来源复核队列",
        "招生明细主表行ID",
        "主表粒度",
        "逐专业复核队列ID",
        "复核优先级序号",
        "保真复核优先级",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "候选V3入口ID",
        "复核批次",
        "最终可用",
        "核验状态",
        "是否高风险保真行",
        "风险阻断等级",
        "高风险字段集合",
        "风险触发规则",
        "异常类型列表",
        "阻断原因",
        "调剂影响等级",
        "必须核验字段",
        "院校代码",
        "院校名称OCR",
        "2026院校专业组代码",
        "专业组出现ID",
        "来源页码",
        "专业行来源",
        "是否真实招生明细",
        "是否0明细占位",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业偏好方向",
        "专业风险类型",
        "同组调剂机器风险",
        "同组真实招生明细数",
        "同组0明细占位数",
        "同组默认不能接受专业数",
        "同组暂缓判断专业数",
        "官网证据匹配状态",
        "官网证据覆盖结论",
        "B0B1计划冲突来源明细ID",
        "B0B1计划冲突类型",
        "B0B1未匹配专业来源明细ID",
        "B0B1未匹配类型",
        "最佳官网专业名称",
        "最佳官网计划数",
        "最佳官网学费",
        "计划数核验状态",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "D0原页匹配方式",
        "D0保守等级",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "下一步",
    }
    v3_fidelity_ledger_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [v3_fidelity_ledger_summary_path, v3_fidelity_ledger_csv]
    )
    v3_fidelity_ledger_ids = {row.get("招生明细主表行ID") for row in v3_fidelity_ledger_rows}
    v3_fidelity_ledger_priority_counts = Counter(
        row.get("保真复核优先级") for row in v3_fidelity_ledger_rows
    )
    v3_fidelity_ledger_block_counts = Counter(row.get("风险阻断等级") for row in v3_fidelity_ledger_rows)
    v3_fidelity_ledger_category_counts = Counter()
    v3_fidelity_ledger_rule_counts = Counter()
    for row in v3_fidelity_ledger_rows:
        v3_fidelity_ledger_category_counts.update(split_semicolon(row.get("高风险字段集合")))
        v3_fidelity_ledger_rule_counts.update(split_semicolon(row.get("风险触发规则")))
    v3_fidelity_ledger_by_code = {}
    for row in v3_fidelity_ledger_rows:
        v3_fidelity_ledger_by_code.setdefault(row.get("2026院校专业组代码"), []).append(row)
    v3_fidelity_ledger_plan_conflict_source_ids = {
        row.get("B0B1计划冲突来源明细ID")
        for row in v3_fidelity_ledger_rows
        if row.get("B0B1计划冲突来源明细ID")
    }
    v3_fidelity_ledger_unmatched_source_ids = {
        row.get("B0B1未匹配专业来源明细ID")
        for row in v3_fidelity_ledger_rows
        if row.get("B0B1未匹配专业来源明细ID")
    }
    b0_b1_plan_conflict_source_ids = {row.get("招生明细主表行ID") for row in b0_b1_plan_conflict_rows}
    b0_b1_unmatched_major_source_ids = {row.get("招生明细主表行ID") for row in b0_b1_unmatched_major_rows}
    v3_fidelity_required_core_tokens = [
        "PDF原页",
        "湖北官方系统",
        "高校官网/章程",
        "专业组边界",
        "调剂范围",
        "家庭接受度",
    ]
    checks.append(ok(
        "第 19 期候选V3全量逐专业字段保真总账摘要和行数正确",
        v3_fidelity_ledger_summary.get("status")
        == "issue19_candidate_v3_major_field_fidelity_ledger_not_final"
        and v3_fidelity_ledger_summary.get("source_detail_table")
        == "data/working/issue19-candidate-v3-admission-detail.csv"
        and v3_fidelity_ledger_summary.get("source_review_queue")
        == "data/working/issue19-candidate-v3-admission-detail-review-queue.csv"
        and v3_fidelity_ledger_summary.get("output_table")
        == "data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv"
        and v3_fidelity_ledger_summary.get("candidate_detail_row_count") == 8412
        and v3_fidelity_ledger_summary.get("candidate_real_detail_count") == 8410
        and v3_fidelity_ledger_summary.get("candidate_zero_detail_count") == 2
        and v3_fidelity_ledger_summary.get("ledger_row_count") == 8412
        and v3_fidelity_ledger_summary.get("high_risk_row_count") == 8234
        and v3_fidelity_ledger_summary.get("low_risk_row_count") == 178
        and v3_fidelity_ledger_summary.get("unique_group_count") == 1327
        and v3_fidelity_ledger_summary.get("zero_detail_row_count") == 2
        and v3_fidelity_ledger_summary.get("b0_b1_plan_conflict_covered_count") == 18
        and v3_fidelity_ledger_summary.get("b0_b1_unmatched_major_covered_count") == 32
        and v3_fidelity_ledger_summary.get("b0_b1_plan_conflict_source_id_count") == 18
        and v3_fidelity_ledger_summary.get("b0_b1_unmatched_major_source_id_count") == 32
        and v3_fidelity_ledger_summary.get("auto_final_list_allowed_count") == 0
        and v3_fidelity_ledger_summary.get("next_stage_allowed_count") == 0
        and len(v3_fidelity_ledger_rows) == 8412,
        f"{len(v3_fidelity_ledger_rows)} detail rows",
    ))
    checks.append(ok(
        "第 19 期候选V3全量逐专业字段保真总账字段、主键和粒度正确",
        required_v3_fidelity_ledger_fields.issubset(v3_fidelity_ledger_fields)
        and len({row.get("保真总账ID") for row in v3_fidelity_ledger_rows})
        == len(v3_fidelity_ledger_rows)
        and len(v3_fidelity_ledger_ids) == len(v3_fidelity_ledger_rows)
        and v3_fidelity_ledger_ids == candidate_v3_detail_ids
        and all(
            row.get("主表粒度") == "逐专业招生明细"
            and row.get("来源主表") == "data/working/issue19-candidate-v3-admission-detail.csv"
            and row.get("来源复核队列")
            == "data/working/issue19-candidate-v3-admission-detail-review-queue.csv"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("数据阶段") == "issue19_candidate_v3_major_field_fidelity_ledger"
            and row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_major_field_fidelity_review"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and all(token in row.get("必须核验字段", "") for token in v3_fidelity_required_core_tokens)
            for row in v3_fidelity_ledger_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3全量逐专业字段保真总账优先级和风险计数闭环正确",
        v3_fidelity_ledger_priority_counts == Counter(v3_fidelity_ledger_summary.get("priority_counts", {}))
        and v3_fidelity_ledger_block_counts == Counter(v3_fidelity_ledger_summary.get("block_level_counts", {}))
        and v3_fidelity_ledger_category_counts == Counter(v3_fidelity_ledger_summary.get("category_counts", {}))
        and v3_fidelity_ledger_summary.get("priority_counts") == {
            "P0-组边界/0明细/串校串行": 1810,
            "P1-计划数保真": 2494,
            "P2-关键限定词和官网未覆盖": 13,
            "P3-费用与高收费": 1011,
            "P4-限制条件": 2754,
            "P5-调剂接受度": 152,
            "P6-暂未触发机器高风险": 178,
        }
        and v3_fidelity_ledger_summary.get("block_level_counts") == {
            "F0-阻断级：不得进入候选排序": 2121,
            "F1-高优先：必须逐字段核验": 4617,
            "F2-待补证：字段需核验": 1496,
            "F3-暂未触发机器高风险但仍非最终": 178,
        }
        and v3_fidelity_ledger_rule_counts.get("b0_b1_plan_conflict") == 18
        and v3_fidelity_ledger_rule_counts.get("b0_b1_unmatched_major") == 32
        and v3_fidelity_ledger_rule_counts.get("d0_pdf_page_structure_anomaly") == 46,
    ))
    checks.append(ok(
        "第 19 期候选V3全量逐专业字段保真总账覆盖B0/B1和D0硬风险",
        v3_fidelity_ledger_plan_conflict_source_ids == b0_b1_plan_conflict_source_ids
        and v3_fidelity_ledger_unmatched_source_ids == b0_b1_unmatched_major_source_ids
        and all(
            row.get("B0B1计划冲突类型")
            and "b0_b1_plan_conflict" in row.get("风险触发规则", "")
            and "PDF原页" in row.get("必须核验字段", "")
            for row in v3_fidelity_ledger_rows
            if row.get("B0B1计划冲突来源明细ID")
        )
        and all(
            row.get("B0B1未匹配类型")
            and "b0_b1_unmatched_major" in row.get("风险触发规则", "")
            and "高校官网/章程" in row.get("必须核验字段", "")
            for row in v3_fidelity_ledger_rows
            if row.get("B0B1未匹配专业来源明细ID")
        )
        and {
            row.get("2026院校专业组代码")
            for row in v3_fidelity_ledger_rows
            if row.get("是否0明细占位") == "true"
        } == {"C10702", "K15123"}
        and all(
            len(v3_fidelity_ledger_by_code.get(code, [])) == 1
            and v3_fidelity_ledger_by_code[code][0].get("保真复核优先级")
            == "P0-组边界/0明细/串校串行"
            and v3_fidelity_ledger_by_code[code][0].get("风险阻断等级")
            == "F0-阻断级：不得进入候选排序"
            and "zero_detail_group_placeholder" in v3_fidelity_ledger_by_code[code][0].get("风险触发规则", "")
            and "d0_missing_in_page_and_structured" in v3_fidelity_ledger_by_code[code][0].get("风险触发规则", "")
            and not v3_fidelity_ledger_by_code[code][0].get("专业名称及备注OCR")
            for code in ["C10702", "K15123"]
        )
        and all(
            "d0_normalized_o0_match" in row.get("风险触发规则", "")
            and row.get("D0原页匹配方式") == "normalized_o0_match"
            for code in ["P01202", "F01203"]
            for row in v3_fidelity_ledger_by_code.get(code, [])
        )
        and "d0_major_text_embeds_other_school_marker"
        in v3_fidelity_ledger_by_code.get("C10705", [{}])[0].get("风险触发规则", "")
        and "d0_plan_count_number_ge_1000"
        in v3_fidelity_ledger_by_code.get("C10705", [{}])[0].get("风险触发规则", ""),
    ))
    checks.append(ok(
        "第 19 期候选V3全量逐专业字段保真总账非最终状态和低风险行边界正确",
        all(
            row.get("是否高风险保真行") == "true"
            and row.get("高风险字段集合")
            and row.get("风险触发规则")
            for row in v3_fidelity_ledger_rows
            if row.get("保真复核优先级") != "P6-暂未触发机器高风险"
        )
        and all(
            row.get("是否高风险保真行") == "false"
            and row.get("风险阻断等级") == "F3-暂未触发机器高风险但仍非最终"
            and row.get("高风险字段集合") == ""
            and row.get("风险触发规则") == ""
            and "仍需按最终志愿门禁" in row.get("阻断原因", "")
            for row in v3_fidelity_ledger_rows
            if row.get("保真复核优先级") == "P6-暂未触发机器高风险"
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            for row in v3_fidelity_ledger_rows
        ),
    ))
    checks.append(ok(
        "第 19 期候选V3全量逐专业字段保真总账公开文件不含本地路径、图片扩展名、身份信息和最终可用结论",
        "private/" not in v3_fidelity_ledger_public_text
        and "/Users/" not in v3_fidelity_ledger_public_text
        and "ocr-runs" not in v3_fidelity_ledger_public_text
        and "rendered-pages" not in v3_fidelity_ledger_public_text
        and ".png" not in v3_fidelity_ledger_public_text
        and ".jpg" not in v3_fidelity_ledger_public_text
        and ".jpeg" not in v3_fidelity_ledger_public_text
        and "final_allowed" not in v3_fidelity_ledger_public_text
        and "ready_for_discussion" not in v3_fidelity_ledger_public_text
        and "已确认" not in v3_fidelity_ledger_public_text
        and "最终推荐" not in v3_fidelity_ledger_public_text
        and "最终方案" not in v3_fidelity_ledger_public_text
        and not any(token in v3_fidelity_ledger_public_text for token in ["身份证", "准考证", "报名号", "姓名"]),
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

    page_fidelity_summary_path = ROOT / "data/working/issue19-page-fidelity-review-queue-summary.json"
    page_fidelity_csv = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"
    page_fidelity_summary = json.loads(page_fidelity_summary_path.read_text())
    with page_fidelity_csv.open(newline="", encoding="utf-8-sig") as f:
        page_fidelity_reader = csv.DictReader(f)
        page_fidelity_rows = list(page_fidelity_reader)
        page_fidelity_fields = set(page_fidelity_reader.fieldnames or [])
    required_page_fidelity_fields = {
        "页级保真队列ID",
        "来源页级manifest",
        "来源底座按页审计",
        "来源全量逐专业保真总账",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "PDF页码",
        "页码范围角色",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "OCR识别行数",
        "OCR_QC_P0数",
        "OCR_QC_P1数",
        "页面复核优先级",
        "页面阻断等级",
        "页面审计状态",
        "页面专业组数",
        "页面专业明细数",
        "页面结构异常数",
        "页面高严重结构异常数",
        "高风险保真行数",
        "低风险行数",
        "F0阻断行数",
        "F1高优先行数",
        "F2待补证行数",
        "F3低风险非最终行数",
        "P0结构串行行数",
        "P1计划数保真行数",
        "P2家庭费用行数",
        "P3选科限制行数",
        "P4调剂风险行数",
        "P5偏好或普通待核行数",
        "P6暂未触发机器高风险行数",
        "空专业名行数",
        "高严重结构异常专业行数",
        "结构异常专业行数",
        "计划数字段风险行数",
        "学费字段风险行数",
        "再选科目字段风险行数",
        "家庭底线风险行数",
        "偏好专业行数",
        "风险字段Top",
        "风险规则Top",
        "必须核验字段",
        "是否可进入最终页级结论",
        "可进入下一阶段",
        "下一步",
    }
    page_fidelity_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [page_fidelity_summary_path, page_fidelity_csv]
    )
    page_fidelity_priority_counts = Counter(row.get("页面复核优先级") for row in page_fidelity_rows)
    page_fidelity_block_counts = Counter(row.get("页面阻断等级") for row in page_fidelity_rows)
    page_manifest_by_page = {as_int(row.get("PDF页码")): row for row in page_manifest_rows}
    page_fidelity_by_page = {as_int(row.get("PDF页码")): row for row in page_fidelity_rows}
    fidelity_major_count_by_page = Counter()
    fidelity_high_risk_by_page = Counter()
    fidelity_low_risk_by_page = Counter()
    fidelity_f0_by_page = Counter()
    fidelity_f1_by_page = Counter()
    fidelity_f2_by_page = Counter()
    fidelity_f3_by_page = Counter()
    fidelity_p0_by_page = Counter()
    fidelity_p1_by_page = Counter()
    fidelity_p2_by_page = Counter()
    fidelity_p3_by_page = Counter()
    fidelity_p4_by_page = Counter()
    fidelity_p5_by_page = Counter()
    fidelity_p6_by_page = Counter()
    fidelity_empty_major_by_page = Counter()
    fidelity_high_structure_by_page = Counter()
    fidelity_structure_by_page = Counter()
    fidelity_plan_risk_by_page = Counter()
    fidelity_tuition_risk_by_page = Counter()
    fidelity_subject_risk_by_page = Counter()
    fidelity_family_by_page = Counter()
    fidelity_preference_by_page = Counter()
    for row in full_major_fidelity_rows:
        page = as_int(row.get("来源页码"))
        if page is None:
            continue
        fidelity_major_count_by_page[page] += 1
        fidelity_high_risk_by_page[page] += row.get("是否高风险保真行") == "true"
        fidelity_low_risk_by_page[page] += row.get("是否高风险保真行") == "false"
        block_level = row.get("风险阻断等级", "")
        fidelity_f0_by_page[page] += block_level.startswith("F0")
        fidelity_f1_by_page[page] += block_level.startswith("F1")
        fidelity_f2_by_page[page] += block_level.startswith("F2")
        fidelity_f3_by_page[page] += block_level.startswith("F3")
        priority = row.get("全量保真复核优先级", "")
        fidelity_p0_by_page[page] += priority.startswith("P0")
        fidelity_p1_by_page[page] += priority.startswith("P1")
        fidelity_p2_by_page[page] += priority.startswith("P2")
        fidelity_p3_by_page[page] += priority.startswith("P3")
        fidelity_p4_by_page[page] += priority.startswith("P4")
        fidelity_p5_by_page[page] += priority.startswith("P5")
        fidelity_p6_by_page[page] += priority.startswith("P6")
        categories = set(split_cn_semicolon(row.get("高风险字段集合")))
        rules = set(split_cn_semicolon(row.get("风险触发规则")))
        fidelity_empty_major_by_page[page] += "empty_major_name" in rules
        fidelity_high_structure_by_page[page] += as_int(row.get("专业行高严重结构异常数")) > 0
        fidelity_structure_by_page[page] += as_int(row.get("专业行结构异常数")) > 0
        fidelity_plan_risk_by_page[page] += "计划数字段" in categories
        fidelity_tuition_risk_by_page[page] += "学费字段" in categories
        fidelity_subject_risk_by_page[page] += "再选科目字段" in categories
        fidelity_family_by_page[page] += "家庭底线" in categories
        fidelity_preference_by_page[page] += "偏好专业" in categories
    page_fidelity_distribution_ok = True
    for page in range(10, 241):
        row = page_fidelity_by_page.get(page)
        manifest_row = page_manifest_by_page.get(page)
        foundation_row = foundation_page_by_page.get(page)
        page_fidelity_distribution_ok = page_fidelity_distribution_ok and bool(row) and bool(manifest_row) and bool(foundation_row)
        if not row or not manifest_row or not foundation_row:
            continue
        page_fidelity_distribution_ok = page_fidelity_distribution_ok and (
            row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("页码范围角色") == "招生计划明细页"
            and row.get("页码范围角色") == manifest_row.get("页码范围角色")
            and row.get("页面审计状态") == foundation_row.get("页面审计状态")
            and row.get("私有页图证据编号") == manifest_row.get("私有页图证据编号")
            and row.get("私有OCR文本证据编号") == manifest_row.get("私有OCR文本证据编号")
            and re.fullmatch(r"[0-9a-f]{64}", row.get("私有页图SHA256", "")) is not None
            and re.fullmatch(r"[0-9a-f]{64}", row.get("私有OCR文本SHA256", "")) is not None
            and row.get("私有页图SHA256") == manifest_row.get("私有页图SHA256")
            and row.get("私有OCR文本SHA256") == manifest_row.get("私有OCR文本SHA256")
            and as_int(row.get("OCR识别行数")) == as_int(manifest_row.get("OCR识别行数"))
            and as_int(row.get("OCR_QC_P0数")) == as_int(manifest_row.get("OCR_QC_P0数"))
            and as_int(row.get("OCR_QC_P1数")) == as_int(manifest_row.get("OCR_QC_P1数"))
            and as_int(row.get("页面专业组数")) == as_int(foundation_row.get("页面专业组数"))
            and as_int(row.get("页面专业明细数")) == as_int(foundation_row.get("页面专业明细数"))
            and as_int(row.get("页面专业明细数")) == fidelity_major_count_by_page.get(page, 0)
            and as_int(row.get("页面结构异常数")) == as_int(foundation_row.get("页面结构异常数"))
            and as_int(row.get("页面高严重结构异常数")) == as_int(foundation_row.get("页面高严重结构异常数"))
            and as_int(row.get("高风险保真行数")) == fidelity_high_risk_by_page.get(page, 0)
            and as_int(row.get("低风险行数")) == fidelity_low_risk_by_page.get(page, 0)
            and as_int(row.get("F0阻断行数")) == fidelity_f0_by_page.get(page, 0)
            and as_int(row.get("F1高优先行数")) == fidelity_f1_by_page.get(page, 0)
            and as_int(row.get("F2待补证行数")) == fidelity_f2_by_page.get(page, 0)
            and as_int(row.get("F3低风险非最终行数")) == fidelity_f3_by_page.get(page, 0)
            and as_int(row.get("P0结构串行行数")) == fidelity_p0_by_page.get(page, 0)
            and as_int(row.get("P1计划数保真行数")) == fidelity_p1_by_page.get(page, 0)
            and as_int(row.get("P2家庭费用行数")) == fidelity_p2_by_page.get(page, 0)
            and as_int(row.get("P3选科限制行数")) == fidelity_p3_by_page.get(page, 0)
            and as_int(row.get("P4调剂风险行数")) == fidelity_p4_by_page.get(page, 0)
            and as_int(row.get("P5偏好或普通待核行数")) == fidelity_p5_by_page.get(page, 0)
            and as_int(row.get("P6暂未触发机器高风险行数")) == fidelity_p6_by_page.get(page, 0)
            and as_int(row.get("空专业名行数")) == fidelity_empty_major_by_page.get(page, 0)
            and as_int(row.get("高严重结构异常专业行数")) == fidelity_high_structure_by_page.get(page, 0)
            and as_int(row.get("结构异常专业行数")) == fidelity_structure_by_page.get(page, 0)
            and as_int(row.get("计划数字段风险行数")) == fidelity_plan_risk_by_page.get(page, 0)
            and as_int(row.get("学费字段风险行数")) == fidelity_tuition_risk_by_page.get(page, 0)
            and as_int(row.get("再选科目字段风险行数")) == fidelity_subject_risk_by_page.get(page, 0)
            and as_int(row.get("家庭底线风险行数")) == fidelity_family_by_page.get(page, 0)
            and as_int(row.get("偏好专业行数")) == fidelity_preference_by_page.get(page, 0)
        )
    checks.append(ok(
        "第 19 期页级保真复核队列摘要和行数正确",
        page_fidelity_summary.get("status") == "issue19_page_fidelity_review_queue_not_final"
        and page_fidelity_summary.get("generated_by") == "build_issue19_page_fidelity_review_queue.py"
        and page_fidelity_summary.get("source_page_manifest") == "data/working/issue19-page-manifest.csv"
        and page_fidelity_summary.get("source_foundation_page_audit")
        == "data/working/issue19-foundation-page-audit.csv"
        and page_fidelity_summary.get("source_full_major_fidelity_ledger")
        == "data/working/issue19-full-major-field-fidelity-ledger.csv"
        and page_fidelity_summary.get("output_table")
        == "data/working/issue19-page-fidelity-review-queue.csv"
        and page_fidelity_summary.get("page_range") == [10, 240]
        and page_fidelity_summary.get("page_count") == 231
        and page_fidelity_summary.get("total_major_detail_count") == 13736
        and page_fidelity_summary.get("total_group_count") == 3329
        and page_fidelity_summary.get("total_high_risk_fidelity_rows") == 13486
        and page_fidelity_summary.get("total_low_risk_rows") == 250
        and page_fidelity_summary.get("total_f0_rows") == 3998
        and page_fidelity_summary.get("total_f1_rows") == 8240
        and page_fidelity_summary.get("total_f2_rows") == 1248
        and page_fidelity_summary.get("total_f3_rows") == 250
        and page_fidelity_summary.get("total_p0_rows") == 2864
        and page_fidelity_summary.get("total_p1_rows") == 7272
        and page_fidelity_summary.get("total_p2_rows") == 1183
        and page_fidelity_summary.get("total_p3_rows") == 1951
        and page_fidelity_summary.get("total_p4_rows") == 70
        and page_fidelity_summary.get("total_p5_rows") == 146
        and page_fidelity_summary.get("total_p6_rows") == 250
        and page_fidelity_summary.get("total_empty_major_name_rows") == 2
        and page_fidelity_summary.get("total_high_structure_anomaly_major_rows") == 2862
        and page_fidelity_summary.get("total_plan_count_risk_rows") == 6347
        and page_fidelity_summary.get("total_tuition_risk_rows") == 1262
        and page_fidelity_summary.get("total_preference_major_rows") == 1726
        and page_fidelity_summary.get("total_family_bottom_line_rows") == 3516
        and page_fidelity_summary.get("auto_final_page_allowed_count") == 0
        and page_fidelity_summary.get("next_stage_allowed_count") == 0
        and len(page_fidelity_rows) == 231,
        f"{len(page_fidelity_rows)} page rows",
    ))
    checks.append(ok(
        "第 19 期页级保真复核队列字段、主键和门禁正确",
        required_page_fidelity_fields.issubset(page_fidelity_fields)
        and len({row.get("页级保真队列ID") for row in page_fidelity_rows}) == len(page_fidelity_rows)
        and len(page_fidelity_by_page) == 231
        and [as_int(row.get("PDF页码")) for row in page_fidelity_rows] == list(range(10, 241))
        and page_fidelity_priority_counts == Counter(page_fidelity_summary.get("priority_counts", {}))
        and page_fidelity_block_counts == Counter(page_fidelity_summary.get("block_level_counts", {}))
        and page_fidelity_summary.get("priority_counts") == {"P0-必须优先核页": 230, "P1-字段高风险核页": 1}
        and page_fidelity_summary.get("block_level_counts")
        == {"F0-本页存在阻断级专业行": 230, "F1-本页存在高优先字段风险": 1}
        and all(
            row.get("来源页级manifest") == "data/working/issue19-page-manifest.csv"
            and row.get("来源底座按页审计") == "data/working/issue19-foundation-page-audit.csv"
            and row.get("来源全量逐专业保真总账")
            == "data/working/issue19-full-major-field-fidelity-ledger.csv"
            and row.get("数据阶段") == "issue19_page_fidelity_review_queue"
            and row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_page_fidelity_review"
            and row.get("是否可进入最终页级结论") == "false"
            and row.get("可进入下一阶段") == "false"
            and all(
                token in row.get("必须核验字段", "")
                for token in ["PDF原页", "专业组边界", "湖北官方系统", "高校官网/章程"]
            )
            for row in page_fidelity_rows
        ),
    ))
    checks.append(ok(
        "第 19 期页级保真复核队列逐页回推到manifest、页级审计和全量明细总账",
        page_fidelity_distribution_ok
        and sum(as_int(row.get("页面专业明细数")) for row in page_fidelity_rows) == 13736
        and sum(as_int(row.get("页面专业组数")) for row in page_fidelity_rows) == 3329
        and sum(as_int(row.get("高风险保真行数")) for row in page_fidelity_rows) == 13486
        and sum(as_int(row.get("低风险行数")) for row in page_fidelity_rows) == 250
        and sum(as_int(row.get("F0阻断行数")) for row in page_fidelity_rows) == 3998
        and sum(as_int(row.get("F1高优先行数")) for row in page_fidelity_rows) == 8240
        and sum(as_int(row.get("F2待补证行数")) for row in page_fidelity_rows) == 1248
        and sum(as_int(row.get("F3低风险非最终行数")) for row in page_fidelity_rows) == 250
        and sum(as_int(row.get("P0结构串行行数")) for row in page_fidelity_rows) == 2864
        and sum(as_int(row.get("P1计划数保真行数")) for row in page_fidelity_rows) == 7272
        and sum(as_int(row.get("P2家庭费用行数")) for row in page_fidelity_rows) == 1183
        and sum(as_int(row.get("P3选科限制行数")) for row in page_fidelity_rows) == 1951
        and sum(as_int(row.get("P4调剂风险行数")) for row in page_fidelity_rows) == 70
        and sum(as_int(row.get("P5偏好或普通待核行数")) for row in page_fidelity_rows) == 146
        and sum(as_int(row.get("P6暂未触发机器高风险行数")) for row in page_fidelity_rows) == 250,
    ))
    checks.append(ok(
        "第 19 期页级保真复核队列公开文件不含本地路径、私有文件路径、图片扩展名、身份信息和最终可用结论",
        "private/" not in page_fidelity_public_text
        and "/Users/" not in page_fidelity_public_text
        and "ocr-runs" not in page_fidelity_public_text
        and "rendered-pages" not in page_fidelity_public_text
        and ".png" not in page_fidelity_public_text
        and ".jpg" not in page_fidelity_public_text
        and ".jpeg" not in page_fidelity_public_text
        and "final_allowed" not in page_fidelity_public_text
        and "ready_for_discussion" not in page_fidelity_public_text
        and "已确认" not in page_fidelity_public_text
        and "最终推荐" not in page_fidelity_public_text
        and "最终方案" not in page_fidelity_public_text
        and not any(token in page_fidelity_public_text for token in shared_forbidden_tokens),
    ))

    full_major_verification_batches_summary_path = (
        ROOT / "data/working/issue19-full-major-verification-batches-summary.json"
    )
    full_major_verification_batches_csv = (
        ROOT / "data/working/issue19-full-major-verification-batches.csv"
    )
    full_major_verification_batches_summary = json.loads(
        full_major_verification_batches_summary_path.read_text()
    )
    with full_major_verification_batches_csv.open(newline="", encoding="utf-8-sig") as f:
        full_major_verification_batches_reader = csv.DictReader(f)
        full_major_verification_batches_rows = list(full_major_verification_batches_reader)
        full_major_verification_batches_fields = set(
            full_major_verification_batches_reader.fieldnames or []
        )
    required_full_major_verification_batches_fields = {
        "逐专业核验批次ID",
        "来源全量逐专业保真总账",
        "来源页级保真复核队列",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "最终可用",
        "核验状态",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "专业代号OCR",
        "专业名称及备注OCR",
        "页级保真队列ID",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "页级复核优先级",
        "页级阻断等级",
        "全量保真复核优先级",
        "风险阻断等级",
        "批次排序",
        "逐专业核验批次",
        "批次触发原因",
        "核验动作",
        "必须核验字段",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "家庭接受度核验状态",
        "调剂影响等级",
        "机器专业接受度初判",
        "专业偏好方向",
        "候选池V1命中",
        "样本学校命中",
        "下一步",
    }
    full_major_verification_batches_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            full_major_verification_batches_summary_path,
            full_major_verification_batches_csv,
        ]
    )
    full_major_verification_batch_counts = Counter(
        row.get("逐专业核验批次") for row in full_major_verification_batches_rows
    )
    full_major_verification_block_counts = Counter(
        row.get("风险阻断等级") for row in full_major_verification_batches_rows
    )
    full_major_verification_page_priority_counts = Counter(
        row.get("页级复核优先级") for row in full_major_verification_batches_rows
    )
    full_major_verification_ids = {
        row.get("专业行ID") for row in full_major_verification_batches_rows
    }
    full_major_verification_by_major_id = {
        row.get("专业行ID"): row for row in full_major_verification_batches_rows
    }
    full_major_fidelity_by_major_id = {row.get("专业行ID"): row for row in full_major_fidelity_rows}
    full_major_verification_distribution_ok = True
    for row in full_major_verification_batches_rows:
        fidelity_row = full_major_fidelity_by_major_id.get(row.get("专业行ID"))
        page_row = page_fidelity_by_page.get(as_int(row.get("来源页码")))
        full_major_verification_distribution_ok = (
            full_major_verification_distribution_ok
            and bool(fidelity_row)
            and bool(page_row)
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("专业组出现ID") == fidelity_row.get("专业组出现ID")
            and row.get("全量保真复核优先级") == fidelity_row.get("全量保真复核优先级")
            and row.get("风险阻断等级") == fidelity_row.get("风险阻断等级")
            and row.get("专业名称及备注OCR") == fidelity_row.get("专业名称及备注OCR")
            and row.get("专业计划数OCR候选") == fidelity_row.get("专业计划数OCR候选")
            and row.get("学费OCR候选") == fidelity_row.get("学费OCR候选")
            and row.get("页级保真队列ID") == page_row.get("页级保真队列ID")
            and row.get("私有页图证据编号") == page_row.get("私有页图证据编号")
            and row.get("私有OCR文本证据编号") == page_row.get("私有OCR文本证据编号")
            and row.get("页级复核优先级") == page_row.get("页面复核优先级")
            and row.get("页级阻断等级") == page_row.get("页面阻断等级")
        )
    checks.append(ok(
        "第 19 期全量逐专业核验批次表摘要和行数正确",
        full_major_verification_batches_summary.get("status")
        == "issue19_full_major_verification_batches_not_final"
        and full_major_verification_batches_summary.get("generated_by")
        == "build_issue19_full_major_verification_batches.py"
        and full_major_verification_batches_summary.get("source_full_major_fidelity_ledger")
        == "data/working/issue19-full-major-field-fidelity-ledger.csv"
        and full_major_verification_batches_summary.get("source_page_fidelity_review_queue")
        == "data/working/issue19-page-fidelity-review-queue.csv"
        and full_major_verification_batches_summary.get("output_table")
        == "data/working/issue19-full-major-verification-batches.csv"
        and full_major_verification_batches_summary.get("row_count") == 13736
        and full_major_verification_batches_summary.get("source_full_major_row_count") == 13736
        and full_major_verification_batches_summary.get("source_page_count") == 231
        and full_major_verification_batches_summary.get("unique_major_line_id_count") == 13736
        and full_major_verification_batches_summary.get("unique_group_occurrence_id_count") == 3289
        and full_major_verification_batches_summary.get("unique_pdf_page_count") == 231
        and full_major_verification_batches_summary.get("candidate_v1_hit_count") == 77
        and full_major_verification_batches_summary.get("sample_school_hit_count") == 560
        and full_major_verification_batches_summary.get("preference_major_row_count") == 2499
        and full_major_verification_batches_summary.get("auto_final_list_allowed_count") == 0
        and full_major_verification_batches_summary.get("next_stage_allowed_count") == 0
        and len(full_major_verification_batches_rows) == 13736,
        f"{len(full_major_verification_batches_rows)} major verification rows",
    ))
    checks.append(ok(
        "第 19 期全量逐专业核验批次表字段、主键和门禁正确",
        required_full_major_verification_batches_fields.issubset(
            full_major_verification_batches_fields
        )
        and len({row.get("逐专业核验批次ID") for row in full_major_verification_batches_rows})
        == len(full_major_verification_batches_rows)
        and len(full_major_verification_ids) == len(full_major_verification_batches_rows)
        and full_major_verification_ids == full_major_fidelity_ids
        and all(
            row.get("来源全量逐专业保真总账")
            == "data/working/issue19-full-major-field-fidelity-ledger.csv"
            and row.get("来源页级保真复核队列")
            == "data/working/issue19-page-fidelity-review-queue.csv"
            and row.get("数据阶段") == "issue19_full_major_verification_batches"
            and row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_full_major_manual_verification_batch"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("PDF字段核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/章程字段核验状态") == "pending_school_plan_or_charter_review"
            and row.get("家庭接受度核验状态") == "pending_family_acceptance_review"
            and all(
                token in row.get("必须核验字段", "")
                for token in ["PDF原页", "湖北官方系统", "高校官网/章程", "专业组边界"]
            )
            for row in full_major_verification_batches_rows
        ),
    ))
    checks.append(ok(
        "第 19 期全量逐专业核验批次表批次分布和上游闭环正确",
        full_major_verification_batch_counts
        == Counter(full_major_verification_batches_summary.get("batch_counts", {}))
        and full_major_verification_block_counts
        == Counter(full_major_verification_batches_summary.get("block_level_counts", {}))
        and full_major_verification_page_priority_counts
        == Counter(full_major_verification_batches_summary.get("page_priority_counts", {}))
        and full_major_verification_batches_summary.get("batch_counts") == {
            "A0-阻断级结构先核": 3998,
            "A1-历史候选和样本先核": 472,
            "A2-偏好专业逐专业先核": 1672,
            "A3-家庭底线和费用先核": 1129,
            "A4-调剂风险先核": 1811,
            "A5-计划数字段先核": 3248,
            "A6-选科和特殊限制先核": 1083,
            "A7-学费字段先核": 14,
            "A8-待补证字段核验": 18,
            "A9-低风险抽检但非最终": 291,
        }
        and full_major_verification_batches_summary.get("block_level_counts")
        == full_major_fidelity_summary.get("block_level_counts")
        and full_major_verification_distribution_ok,
    ))
    checks.append(ok(
        "第 19 期全量逐专业核验批次表公开文件不含本地路径、图片扩展名、身份信息和最终可用结论",
        "private/" not in full_major_verification_batches_public_text
        and "/Users/" not in full_major_verification_batches_public_text
        and "ocr-runs" not in full_major_verification_batches_public_text
        and "rendered-pages" not in full_major_verification_batches_public_text
        and ".png" not in full_major_verification_batches_public_text
        and ".jpg" not in full_major_verification_batches_public_text
        and ".jpeg" not in full_major_verification_batches_public_text
        and "final_allowed" not in full_major_verification_batches_public_text
        and "ready_for_discussion" not in full_major_verification_batches_public_text
        and "已确认" not in full_major_verification_batches_public_text
        and "最终推荐" not in full_major_verification_batches_public_text
        and "最终方案" not in full_major_verification_batches_public_text
        and not any(token in full_major_verification_batches_public_text for token in shared_forbidden_tokens),
    ))

    priority_group_major_pack_summary_path = (
        ROOT / "data/working/issue19-priority-group-major-review-pack-summary.json"
    )
    priority_group_major_pack_csv = (
        ROOT / "data/working/issue19-priority-group-major-review-pack.csv"
    )
    priority_group_major_pack_summary = json.loads(
        priority_group_major_pack_summary_path.read_text()
    )
    with priority_group_major_pack_csv.open(newline="", encoding="utf-8-sig") as f:
        priority_group_major_pack_reader = csv.DictReader(f)
        priority_group_major_pack_rows = list(priority_group_major_pack_reader)
        priority_group_major_pack_fields = set(
            priority_group_major_pack_reader.fieldnames or []
        )
    required_priority_group_major_pack_fields = {
        "优先整组核验包ID",
        "优先整组核验明细ID",
        "来源全量逐专业核验批次表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "核验状态",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "专业组信息用途",
        "整组核验优先级",
        "整组核验排序",
        "整组入选原因",
        "整组调剂机器风险",
        "整组招生明细数",
        "整组种子专业数",
        "整组偏好专业数",
        "整组默认不能接受专业数",
        "整组特殊限制待核专业数",
        "整组批次分布",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "页级保真队列ID",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "逐专业核验批次",
        "批次触发原因",
        "全量保真复核优先级",
        "风险阻断等级",
        "高风险字段集合",
        "风险触发规则",
        "专业偏好方向",
        "专业风险类型",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "调剂影响等级",
        "候选池V1命中",
        "样本学校命中",
        "必须核验字段",
        "核验动作",
        "下一步",
    }
    priority_group_major_pack_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            priority_group_major_pack_summary_path,
            priority_group_major_pack_csv,
        ]
    )
    priority_group_major_pack_priority_counts = Counter(
        row.get("整组核验优先级") for row in priority_group_major_pack_rows
    )
    priority_group_major_pack_batch_counts = Counter(
        row.get("逐专业核验批次") for row in priority_group_major_pack_rows
    )
    priority_group_major_pack_adjustment_counts = Counter(
        row.get("整组调剂机器风险") for row in priority_group_major_pack_rows
    )
    seed_batches = {
        "A1-历史候选和样本先核",
        "A2-偏好专业逐专业先核",
        "A8-待补证字段核验",
    }
    source_groups_by_id = {}
    seed_group_ids = set()
    source_rows_by_major_id = {}
    for row in full_major_verification_batches_rows:
        group_id = row.get("专业组出现ID")
        source_groups_by_id.setdefault(group_id, []).append(row)
        source_rows_by_major_id[row.get("专业行ID")] = row
        if row.get("逐专业核验批次") in seed_batches:
            seed_group_ids.add(group_id)
    pack_groups_by_id = {}
    pack_major_ids = set()
    priority_group_major_pack_distribution_ok = True
    for row in priority_group_major_pack_rows:
        group_id = row.get("专业组出现ID")
        source_row = source_rows_by_major_id.get(row.get("专业行ID"))
        pack_groups_by_id.setdefault(group_id, []).append(row)
        pack_major_ids.add(row.get("专业行ID"))
        priority_group_major_pack_distribution_ok = (
            priority_group_major_pack_distribution_ok
            and bool(source_row)
            and row.get("专业组出现ID") == source_row.get("专业组出现ID")
            and row.get("院校代码") == source_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == source_row.get("院校专业组代码OCR规范化")
            and row.get("专业代号OCR") == source_row.get("专业代号OCR")
            and row.get("专业名称及备注OCR") == source_row.get("专业名称及备注OCR")
            and row.get("逐专业核验批次") == source_row.get("逐专业核验批次")
            and row.get("风险阻断等级") == source_row.get("风险阻断等级")
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
        )
    priority_group_major_pack_group_completeness_ok = True
    for group_id, pack_rows in pack_groups_by_id.items():
        source_group_rows = source_groups_by_id.get(group_id, [])
        source_group_major_ids = {row.get("专业行ID") for row in source_group_rows}
        pack_group_major_ids = {row.get("专业行ID") for row in pack_rows}
        seed_count = sum(
            row.get("逐专业核验批次") in seed_batches
            for row in source_group_rows
        )
        preference_count = sum(bool(row.get("专业偏好方向")) for row in source_group_rows)
        default_no_count = sum(
            row.get("机器专业接受度初判", "").startswith("默认不能接受")
            for row in source_group_rows
        )
        special_count = sum(
            row.get("机器专业接受度初判", "").startswith("暂缓判断")
            for row in source_group_rows
        )
        if default_no_count:
            expected_risk = "T1-同组存在默认不能接受专业，调剂高风险"
        elif special_count:
            expected_risk = "T2-同组存在特殊限制待核专业，调剂中风险"
        else:
            expected_risk = "T3-未见机器默认不能接受专业，仍需家庭逐专业确认"
        priority_group_major_pack_group_completeness_ok = (
            priority_group_major_pack_group_completeness_ok
            and group_id in seed_group_ids
            and len(pack_rows) == len(source_group_rows)
            and pack_group_major_ids == source_group_major_ids
            and all(
                as_int(row.get("整组招生明细数")) == len(source_group_rows)
                and as_int(row.get("整组种子专业数")) == seed_count
                and as_int(row.get("整组偏好专业数")) == preference_count
                and as_int(row.get("整组默认不能接受专业数")) == default_no_count
                and as_int(row.get("整组特殊限制待核专业数")) == special_count
                and row.get("整组调剂机器风险") == expected_risk
                for row in pack_rows
            )
        )
    priority_group_major_required_core_tokens = [
        "PDF原页",
        "湖北官方系统",
        "高校官网/章程",
        "专业组边界",
        "调剂范围",
        "家庭接受度",
    ]
    checks.append(ok(
        "第 19 期优先整组逐专业核验包摘要和行数正确",
        priority_group_major_pack_summary.get("status")
        == "issue19_priority_group_major_review_pack_not_final"
        and priority_group_major_pack_summary.get("generated_by")
        == "build_issue19_priority_group_major_review_pack.py"
        and priority_group_major_pack_summary.get("source_full_major_verification_batches")
        == "data/working/issue19-full-major-verification-batches.csv"
        and priority_group_major_pack_summary.get("output_table")
        == "data/working/issue19-priority-group-major-review-pack.csv"
        and priority_group_major_pack_summary.get("row_count") == 7537
        and priority_group_major_pack_summary.get("source_row_count") == 13736
        and priority_group_major_pack_summary.get("seed_group_count") == 1043
        and priority_group_major_pack_summary.get("unique_group_occurrence_id_count") == 1043
        and priority_group_major_pack_summary.get("unique_major_line_id_count") == 7537
        and priority_group_major_pack_summary.get("unique_school_count") == 631
        and priority_group_major_pack_summary.get("unique_pdf_page_count") == 230
        and priority_group_major_pack_summary.get("candidate_v1_hit_row_count") == 70
        and priority_group_major_pack_summary.get("sample_school_hit_row_count") == 514
        and priority_group_major_pack_summary.get("preference_major_row_count") == 2097
        and priority_group_major_pack_summary.get("auto_final_list_allowed_count") == 0
        and priority_group_major_pack_summary.get("next_stage_allowed_count") == 0
        and len(priority_group_major_pack_rows) == 7537,
        f"{len(priority_group_major_pack_rows)} priority group major rows",
    ))
    checks.append(ok(
        "第 19 期优先整组逐专业核验包字段、主键和非最终门禁正确",
        required_priority_group_major_pack_fields.issubset(priority_group_major_pack_fields)
        and len({row.get("优先整组核验明细ID") for row in priority_group_major_pack_rows})
        == len(priority_group_major_pack_rows)
        and len(pack_major_ids) == len(priority_group_major_pack_rows)
        and pack_major_ids.issubset(full_major_verification_ids)
        and all(
            row.get("来源全量逐专业核验批次表")
            == "data/working/issue19-full-major-verification-batches.csv"
            and row.get("数据阶段") == "issue19_priority_group_major_review_pack"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("专业组信息用途")
            == "本行携带院校专业组上下文用于判断调剂范围；不得把本表降格为学校/专业组两层摘要。"
            and row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_priority_group_major_review"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and all(
                token in row.get("必须核验字段", "")
                for token in priority_group_major_required_core_tokens
            )
            for row in priority_group_major_pack_rows
        ),
    ))
    checks.append(ok(
        "第 19 期优先整组逐专业核验包批次、调剂风险和整组完整性正确",
        priority_group_major_pack_priority_counts
        == Counter(priority_group_major_pack_summary.get("priority_counts", {}))
        and priority_group_major_pack_batch_counts
        == Counter(priority_group_major_pack_summary.get("batch_counts", {}))
        and priority_group_major_pack_adjustment_counts
        == Counter(priority_group_major_pack_summary.get("adjustment_risk_counts", {}))
        and priority_group_major_pack_summary.get("priority_counts") == {
            "W0-历史候选/样本整组先核": 515,
            "W1-数字媒体技术整组先核": 468,
            "W2-其他偏好专业整组先核": 6476,
            "W3-待补证整组先核": 78,
        }
        and priority_group_major_pack_summary.get("batch_counts") == {
            "A0-阻断级结构先核": 1313,
            "A1-历史候选和样本先核": 472,
            "A2-偏好专业逐专业先核": 1672,
            "A3-家庭底线和费用先核": 517,
            "A4-调剂风险先核": 1220,
            "A5-计划数字段先核": 1750,
            "A6-选科和特殊限制先核": 506,
            "A7-学费字段先核": 3,
            "A8-待补证字段核验": 18,
            "A9-低风险抽检但非最终": 66,
        }
        and priority_group_major_pack_summary.get("adjustment_risk_counts") == {
            "T1-同组存在默认不能接受专业，调剂高风险": 3308,
            "T2-同组存在特殊限制待核专业，调剂中风险": 1329,
            "T3-未见机器默认不能接受专业，仍需家庭逐专业确认": 2900,
        }
        and set(pack_groups_by_id) == seed_group_ids
        and len(pack_groups_by_id) == 1043
        and priority_group_major_pack_distribution_ok
        and priority_group_major_pack_group_completeness_ok,
    ))
    checks.append(ok(
        "第 19 期优先整组逐专业核验包公开文件不含本地路径、图片扩展名、身份信息和最终可用结论",
        "private/" not in priority_group_major_pack_public_text
        and "/Users/" not in priority_group_major_pack_public_text
        and "ocr-runs" not in priority_group_major_pack_public_text
        and "rendered-pages" not in priority_group_major_pack_public_text
        and ".png" not in priority_group_major_pack_public_text
        and ".jpg" not in priority_group_major_pack_public_text
        and ".jpeg" not in priority_group_major_pack_public_text
        and "final_allowed" not in priority_group_major_pack_public_text
        and "ready_for_discussion" not in priority_group_major_pack_public_text
        and "已确认" not in priority_group_major_pack_public_text
        and "最终推荐" not in priority_group_major_pack_public_text
        and "最终方案" not in priority_group_major_pack_public_text
        and not any(token in priority_group_major_pack_public_text for token in shared_forbidden_tokens),
    ))

    priority_major_evidence_summary_path = (
        ROOT / "data/working/issue19-priority-major-evidence-workbench-summary.json"
    )
    priority_major_evidence_csv = (
        ROOT / "data/working/issue19-priority-major-evidence-workbench.csv"
    )
    priority_major_evidence_summary = json.loads(
        priority_major_evidence_summary_path.read_text()
    )
    with priority_major_evidence_csv.open(newline="", encoding="utf-8-sig") as f:
        priority_major_evidence_reader = csv.DictReader(f)
        priority_major_evidence_rows = list(priority_major_evidence_reader)
        priority_major_evidence_fields = set(priority_major_evidence_reader.fieldnames or [])
    required_priority_major_evidence_fields = {
        "证据执行工作台ID",
        "来源优先整组核验明细ID",
        "来源优先整组核验包",
        "来源全量逐专业核验批次表",
        "来源全量逐专业保真总账",
        "来源家庭底线逐专业表",
        "来源页级保真复核队列",
        "来源候选V3保真总账",
        "来源B0B1学校官网来源队列",
        "来源D0原页OCR证据表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "核验状态",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "证据执行优先级",
        "证据执行排序",
        "已有辅证标记",
        "证据缺口",
        "执行必须核验字段",
        "PDF原页证据状态",
        "D0原页OCR证据状态",
        "湖北官方系统证据状态",
        "高校官网/章程辅证状态",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "家庭接受度核验状态",
        "调剂影响初判",
        "组机器家庭匹配初判",
        "组调剂初判",
        "页级复核优先级",
        "页级阻断等级",
        "页级OCR平均置信度",
        "页级OCR_QC_P0数",
        "页级OCR_QC_P1数",
        "三年投档线索",
        "三年投档稳定性状态",
        "高校官网URL",
        "高校官网可核字段",
        "高校官网局限性",
        "B0B1计划冲突来源明细ID",
        "B0B1未匹配专业来源明细ID",
        "最佳官网专业名称",
        "最佳官网计划数",
        "最佳官网学费",
        "计划数核验状态",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "页级保真队列ID",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "整组核验优先级",
        "整组入选原因",
        "整组调剂机器风险",
        "整组招生明细数",
        "整组默认不能接受专业数",
        "整组特殊限制待核专业数",
        "逐专业核验批次",
        "全量保真复核优先级",
        "风险阻断等级",
        "高风险字段集合",
        "风险触发规则",
        "专业偏好方向",
        "专业风险类型",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "必须核验字段",
        "下一步",
    }
    family_major_detail_csv = ROOT / "data/working/issue19-family-fit-major-detail.csv"
    with family_major_detail_csv.open(newline="", encoding="utf-8-sig") as f:
        family_major_detail_rows = list(csv.DictReader(f))
    family_major_detail_by_major_id = {
        row.get("专业行ID"): row for row in family_major_detail_rows
    }
    page_fidelity_by_queue_id = {
        row.get("页级保真队列ID"): row for row in page_fidelity_rows
    }
    v3_fidelity_by_major_line_id = {
        row.get("专业行ID"): row
        for row in v3_fidelity_ledger_rows
        if row.get("专业行ID")
    }
    b0_b1_school_source_by_code = {
        row.get("院校代码"): row for row in b0_b1_school_source_rows
    }
    toudang_by_year = {}
    for year in ["2023", "2024", "2025"]:
        toudang_path = ROOT / f"data/derived/hubei-{year}-physics-toudang-parsed.csv"
        with toudang_path.open(newline="", encoding="utf-8-sig") as f:
            toudang_by_year[year] = {
                row.get("code"): row for row in csv.DictReader(f)
            }
    def historical_status_for_code(code):
        hit_years = [year for year, rows in toudang_by_year.items() if code in rows]
        if len(hit_years) >= 2:
            return f"同代码{len(hit_years)}年命中，仅作稳定性线索"
        if len(hit_years) == 1:
            return "同代码1年命中，需重点核组号变化"
        return "同代码三年未命中或组号变化，需人工判断历史参照"
    priority_major_evidence_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [priority_major_evidence_summary_path, priority_major_evidence_csv]
    )
    priority_major_evidence_priority_counts = Counter(
        row.get("证据执行优先级") for row in priority_major_evidence_rows
    )
    priority_major_evidence_source_counts = Counter(
        row.get("高校官网/章程辅证状态") for row in priority_major_evidence_rows
    )
    priority_major_evidence_marker_counts = Counter()
    for row in priority_major_evidence_rows:
        priority_major_evidence_marker_counts.update(
            split_cn_semicolon(row.get("已有辅证标记"))
        )
    priority_major_evidence_ids = {
        row.get("专业行ID") for row in priority_major_evidence_rows
    }
    priority_pack_by_major_id = {
        row.get("专业行ID"): row for row in priority_group_major_pack_rows
    }
    priority_major_evidence_distribution_ok = True
    for row in priority_major_evidence_rows:
        major_id = row.get("专业行ID")
        pack_row = priority_pack_by_major_id.get(major_id)
        verification_row = full_major_verification_by_major_id.get(major_id)
        fidelity_row = full_major_fidelity_by_major_id.get(major_id)
        family_row = family_major_detail_by_major_id.get(major_id)
        page_row = page_fidelity_by_queue_id.get(row.get("页级保真队列ID"))
        v3_row = v3_fidelity_by_major_line_id.get(major_id, {})
        school_row = b0_b1_school_source_by_code.get(row.get("院校代码"), {})
        d0_row = candidate_v3_d0_pdf_by_code.get(row.get("院校专业组代码OCR规范化"), {})
        expected_school_status = (
            v3_row.get("官网证据匹配状态")
            or school_row.get("官网来源状态")
            or "priority_pack_not_yet_school_source_searched"
        )
        priority_major_evidence_distribution_ok = (
            priority_major_evidence_distribution_ok
            and bool(pack_row)
            and bool(verification_row)
            and bool(fidelity_row)
            and bool(family_row)
            and bool(page_row)
            and row.get("来源优先整组核验明细ID")
            == pack_row.get("优先整组核验明细ID")
            and row.get("专业组出现ID") == pack_row.get("专业组出现ID")
            and row.get("院校代码") == pack_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == pack_row.get("院校专业组代码OCR规范化")
            and row.get("专业名称及备注OCR") == pack_row.get("专业名称及备注OCR")
            and row.get("逐专业核验批次") == pack_row.get("逐专业核验批次")
            and row.get("PDF字段核验状态") == verification_row.get("PDF字段核验状态")
            and row.get("湖北官方系统字段核验状态")
            == verification_row.get("湖北官方系统字段核验状态")
            and row.get("高校官网/章程字段核验状态")
            == verification_row.get("高校官网/章程字段核验状态")
            and row.get("家庭接受度核验状态") == family_row.get("家庭接受度核验状态")
            and row.get("页级复核优先级") == page_row.get("页面复核优先级")
            and row.get("页级阻断等级") == page_row.get("页面阻断等级")
            and row.get("高校官网/章程辅证状态") == expected_school_status
            and row.get("D0原页OCR证据状态")
            == d0_row.get("PDF原页OCR核验结论", "not_d0_group")
            and row.get("三年投档稳定性状态")
            == historical_status_for_code(row.get("院校专业组代码OCR规范化"))
        )
    priority_major_required_tokens = [
        "PDF原页",
        "湖北官方系统/省招办计划",
        "高校官网/章程",
        "专业组边界",
        "调剂范围",
        "家庭接受度",
        "三年投档稳定性",
    ]
    priority_major_gap_tokens = [
        "PDF原页人工核验",
        "湖北官方系统/省招办计划",
        "高校官网/招生章程",
        "家庭逐专业接受度",
        "同组调剂结论",
        "三年投档稳定性",
    ]
    checks.append(ok(
        "第 19 期优先逐专业证据执行工作台摘要和行数正确",
        priority_major_evidence_summary.get("status")
        == "issue19_priority_major_evidence_workbench_not_final"
        and priority_major_evidence_summary.get("generated_by")
        == "build_issue19_priority_major_evidence_workbench.py"
        and priority_major_evidence_summary.get("source_priority_group_major_review_pack")
        == "data/working/issue19-priority-group-major-review-pack.csv"
        and priority_major_evidence_summary.get("source_full_major_verification_batches")
        == "data/working/issue19-full-major-verification-batches.csv"
        and priority_major_evidence_summary.get("source_full_major_fidelity_ledger")
        == "data/working/issue19-full-major-field-fidelity-ledger.csv"
        and priority_major_evidence_summary.get("source_family_major_detail")
        == "data/working/issue19-family-fit-major-detail.csv"
        and priority_major_evidence_summary.get("source_page_fidelity_review_queue")
        == "data/working/issue19-page-fidelity-review-queue.csv"
        and priority_major_evidence_summary.get("output_table")
        == "data/working/issue19-priority-major-evidence-workbench.csv"
        and priority_major_evidence_summary.get("row_count") == 7537
        and priority_major_evidence_summary.get("unique_major_line_id_count") == 7537
        and priority_major_evidence_summary.get("unique_group_occurrence_id_count") == 1043
        and priority_major_evidence_summary.get("unique_school_count") == 631
        and priority_major_evidence_summary.get("unique_pdf_page_count") == 230
        and priority_major_evidence_summary.get("full_major_verification_hit_row_count") == 7537
        and priority_major_evidence_summary.get("full_major_fidelity_hit_row_count") == 7537
        and priority_major_evidence_summary.get("family_major_hit_row_count") == 7537
        and priority_major_evidence_summary.get("page_fidelity_hit_row_count") == 7537
        and priority_major_evidence_summary.get("candidate_v3_fidelity_hit_row_count") == 7199
        and priority_major_evidence_summary.get("b0_b1_school_source_hit_row_count") == 464
        and priority_major_evidence_summary.get("d0_pdf_evidence_hit_row_count") == 54
        and priority_major_evidence_summary.get("b0_b1_plan_conflict_row_count") == 8
        and priority_major_evidence_summary.get("b0_b1_unmatched_major_row_count") == 24
        and priority_major_evidence_summary.get("missing_plan_count_row_count") == 2831
        and priority_major_evidence_summary.get("missing_tuition_row_count") == 450
        and priority_major_evidence_summary.get("missing_subject_row_count") == 6733
        and priority_major_evidence_summary.get("historical_exact_group_hit_row_count") == 6496
        and priority_major_evidence_summary.get("auto_final_list_allowed_count") == 0
        and priority_major_evidence_summary.get("next_stage_allowed_count") == 0
        and len(priority_major_evidence_rows) == 7537,
        f"{len(priority_major_evidence_rows)} evidence rows",
    ))
    checks.append(ok(
        "第 19 期优先逐专业证据执行工作台字段、主键和非最终门禁正确",
        required_priority_major_evidence_fields.issubset(priority_major_evidence_fields)
        and len({row.get("证据执行工作台ID") for row in priority_major_evidence_rows})
        == len(priority_major_evidence_rows)
        and len(priority_major_evidence_ids) == len(priority_major_evidence_rows)
        and priority_major_evidence_ids == pack_major_ids
        and all(
            row.get("来源优先整组核验包")
            == "data/working/issue19-priority-group-major-review-pack.csv"
            and row.get("来源全量逐专业核验批次表")
            == "data/working/issue19-full-major-verification-batches.csv"
            and row.get("来源全量逐专业保真总账")
            == "data/working/issue19-full-major-field-fidelity-ledger.csv"
            and row.get("来源家庭底线逐专业表")
            == "data/working/issue19-family-fit-major-detail.csv"
            and row.get("来源页级保真复核队列")
            == "data/working/issue19-page-fidelity-review-queue.csv"
            and row.get("数据阶段") == "issue19_priority_major_evidence_workbench"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_priority_major_evidence_execution"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("PDF原页证据状态") == "has_page_hash_pending_manual_pdf_review"
            and row.get("湖北官方系统证据状态")
            == "pending_hubei_official_plan_or_platform_review"
            and row.get("PDF字段核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/章程字段核验状态") == "pending_school_plan_or_charter_review"
            and row.get("家庭接受度核验状态") == "pending_family_acceptance_review"
            and all(token in row.get("执行必须核验字段", "") for token in priority_major_required_tokens)
            and all(token in row.get("证据缺口", "") for token in priority_major_gap_tokens)
            for row in priority_major_evidence_rows
        ),
    ))
    checks.append(ok(
        "第 19 期优先逐专业证据执行工作台执行优先级、辅证和来源闭环正确",
        priority_major_evidence_priority_counts
        == Counter(priority_major_evidence_summary.get("priority_counts", {}))
        and priority_major_evidence_source_counts
        == Counter(priority_major_evidence_summary.get("official_source_status_counts", {}))
        and priority_major_evidence_marker_counts
        == Counter(priority_major_evidence_summary.get("evidence_marker_counts", {}))
        and priority_major_evidence_summary.get("priority_counts") == {
            "E0-PDF原页/组边界阻断先核": 1362,
            "E1-历史候选/样本三方证据先核": 450,
            "E2-数字媒体技术三方证据先核": 405,
            "E3-已有高校官网辅证先交叉": 148,
            "E4-计划学费选科字段先补证": 4878,
            "E5-同组调剂风险先核": 173,
            "E6-其他偏好整组按页推进": 121,
        }
        and priority_major_evidence_summary.get("official_source_status_counts") == {
            "charter_or_rules_only_no_plan": 41,
            "has_partial_source_needs_followup": 203,
            "has_reusable_2026_hubei_plan_source": 104,
            "needs_official_plan_source_search": 108,
            "priority_pack_not_yet_school_source_searched": 7073,
            "官网专业名匹配但计划数冲突-优先核页": 8,
        }
        and priority_major_evidence_summary.get("evidence_marker_counts") == {
            "B0/B1官网未匹配专业": 24,
            "B0/B1计划数冲突": 8,
            "命中B0/B1学校官网来源队列": 464,
            "命中D0原页OCR证据": 54,
            "命中候选V3保真总账": 7199,
            "暂无可复用辅证": 256,
        }
        and priority_major_evidence_distribution_ok,
    ))
    checks.append(ok(
        "第 19 期优先逐专业证据执行工作台公开文件不含本地路径、图片扩展名、身份信息、登录态和最终建议结论",
        "private/" not in priority_major_evidence_public_text
        and "private\\" not in priority_major_evidence_public_text
        and "/Users/" not in priority_major_evidence_public_text
        and "ocr-runs" not in priority_major_evidence_public_text
        and "rendered-pages" not in priority_major_evidence_public_text
        and ".png" not in priority_major_evidence_public_text
        and ".jpg" not in priority_major_evidence_public_text
        and ".jpeg" not in priority_major_evidence_public_text
        and "Authorization" not in priority_major_evidence_public_text
        and "Bearer " not in priority_major_evidence_public_text
        and "Cookie" not in priority_major_evidence_public_text
        and "final_allowed" not in priority_major_evidence_public_text
        and "ready_for_discussion" not in priority_major_evidence_public_text
        and "已确认" not in priority_major_evidence_public_text
        and "已核准" not in priority_major_evidence_public_text
        and "最终推荐" not in priority_major_evidence_public_text
        and "最终方案" not in priority_major_evidence_public_text
        and "可报" not in priority_major_evidence_public_text
        and "可填报" not in priority_major_evidence_public_text
        and "可排序" not in priority_major_evidence_public_text
        and not any(token in priority_major_evidence_public_text for token in shared_forbidden_tokens),
    ))

    full_major_evidence_summary_path = (
        ROOT / "data/working/issue19-full-major-evidence-workbench-summary.json"
    )
    full_major_evidence_csv = (
        ROOT / "data/working/issue19-full-major-evidence-workbench.csv"
    )
    full_major_evidence_summary = json.loads(
        full_major_evidence_summary_path.read_text()
    )
    with full_major_evidence_csv.open(newline="", encoding="utf-8-sig") as f:
        full_major_evidence_reader = csv.DictReader(f)
        full_major_evidence_rows = list(full_major_evidence_reader)
        full_major_evidence_fields = set(full_major_evidence_reader.fieldnames or [])
    required_full_major_evidence_fields = {
        "全量证据工作台ID",
        "来源全量逐专业核验批次表",
        "来源全量逐专业保真总账",
        "来源家庭底线逐专业表",
        "来源页级保真复核队列",
        "来源优先整组核验包",
        "来源优先逐专业证据工作台",
        "来源候选V3保真总账",
        "来源B0B1学校官网来源队列",
        "来源D0原页OCR证据表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "核验状态",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "是否在优先整组核验包",
        "来源优先整组核验明细ID",
        "来源优先证据工作台ID",
        "全量证据执行优先级",
        "全量证据执行排序",
        "已有辅证标记",
        "证据缺口",
        "执行必须核验字段",
        "PDF原页证据状态",
        "D0原页OCR证据状态",
        "湖北官方系统证据状态",
        "高校官网/章程辅证状态",
        "PDF字段核验状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程字段核验状态",
        "家庭接受度核验状态",
        "调剂影响初判",
        "调剂影响等级",
        "组机器家庭匹配初判",
        "组调剂初判",
        "页级保真队列ID",
        "页级复核优先级",
        "页级阻断等级",
        "页级OCR平均置信度",
        "页级OCR_QC_P0数",
        "页级OCR_QC_P1数",
        "三年投档线索",
        "三年投档稳定性状态",
        "高校官网URL",
        "高校官网可核字段",
        "高校官网局限性",
        "B0B1计划冲突来源明细ID",
        "B0B1未匹配专业来源明细ID",
        "最佳官网专业名称",
        "最佳官网计划数",
        "最佳官网学费",
        "计划数核验状态",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "整组核验优先级",
        "整组入选原因",
        "整组调剂机器风险",
        "同组真实招生明细数",
        "同组偏好专业数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "逐专业核验批次",
        "批次触发原因",
        "全量保真复核优先级",
        "风险阻断等级",
        "高风险字段集合",
        "风险触发规则",
        "专业偏好方向",
        "专业风险类型",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "必须核验字段",
        "下一步",
    }
    full_major_evidence_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [full_major_evidence_summary_path, full_major_evidence_csv]
    )
    full_major_evidence_priority_counts = Counter(
        row.get("全量证据执行优先级") for row in full_major_evidence_rows
    )
    full_major_evidence_source_counts = Counter(
        row.get("高校官网/章程辅证状态") for row in full_major_evidence_rows
    )
    full_major_evidence_historical_counts = Counter(
        row.get("三年投档稳定性状态") for row in full_major_evidence_rows
    )
    full_major_evidence_marker_counts = Counter()
    for row in full_major_evidence_rows:
        full_major_evidence_marker_counts.update(
            split_cn_semicolon(row.get("已有辅证标记"))
        )
    full_major_evidence_ids = {
        row.get("专业行ID") for row in full_major_evidence_rows
    }
    priority_major_evidence_by_major_id = {
        row.get("专业行ID"): row for row in priority_major_evidence_rows
    }
    full_major_evidence_distribution_ok = True
    for row in full_major_evidence_rows:
        major_id = row.get("专业行ID")
        verification_row = full_major_verification_by_major_id.get(major_id)
        fidelity_row = full_major_fidelity_by_major_id.get(major_id)
        family_row = family_major_detail_by_major_id.get(major_id)
        priority_pack_row = priority_pack_by_major_id.get(major_id, {})
        priority_evidence_row = priority_major_evidence_by_major_id.get(major_id, {})
        page_row = page_fidelity_by_queue_id.get(row.get("页级保真队列ID"))
        v3_row = v3_fidelity_by_major_line_id.get(major_id, {})
        school_row = b0_b1_school_source_by_code.get(row.get("院校代码"), {})
        d0_row = candidate_v3_d0_pdf_by_code.get(row.get("院校专业组代码OCR规范化"), {})
        expected_school_status = (
            v3_row.get("官网证据匹配状态")
            or school_row.get("官网来源状态")
            or "not_yet_school_source_searched_in_full_workbench"
        )
        full_major_evidence_distribution_ok = (
            full_major_evidence_distribution_ok
            and bool(verification_row)
            and bool(fidelity_row)
            and bool(family_row)
            and bool(page_row)
            and row.get("专业组出现ID") == verification_row.get("专业组出现ID")
            and row.get("院校代码") == verification_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == verification_row.get("院校专业组代码OCR规范化")
            and row.get("专业名称及备注OCR") == verification_row.get("专业名称及备注OCR")
            and row.get("逐专业核验批次") == verification_row.get("逐专业核验批次")
            and row.get("全量保真复核优先级") == verification_row.get("全量保真复核优先级")
            and row.get("风险阻断等级") == verification_row.get("风险阻断等级")
            and row.get("PDF字段核验状态") == verification_row.get("PDF字段核验状态")
            and row.get("湖北官方系统字段核验状态")
            == verification_row.get("湖北官方系统字段核验状态")
            and row.get("高校官网/章程字段核验状态")
            == verification_row.get("高校官网/章程字段核验状态")
            and row.get("家庭接受度核验状态")
            == verification_row.get("家庭接受度核验状态")
            and row.get("页级复核优先级") == page_row.get("页面复核优先级")
            and row.get("页级阻断等级") == page_row.get("页面阻断等级")
            and row.get("高校官网/章程辅证状态") == expected_school_status
            and row.get("D0原页OCR证据状态")
            == d0_row.get("PDF原页OCR核验结论", "not_d0_group")
            and row.get("三年投档稳定性状态")
            == historical_status_for_code(row.get("院校专业组代码OCR规范化"))
            and (
                (
                    row.get("是否在优先整组核验包") == "true"
                    and bool(priority_pack_row)
                    and bool(priority_evidence_row)
                    and row.get("来源优先整组核验明细ID")
                    == priority_pack_row.get("优先整组核验明细ID")
                    and row.get("来源优先证据工作台ID")
                    == priority_evidence_row.get("证据执行工作台ID")
                    and row.get("全量证据执行优先级")
                    == priority_evidence_row.get("证据执行优先级")
                )
                or (
                    row.get("是否在优先整组核验包") == "false"
                    and not priority_pack_row
                    and not priority_evidence_row
                    and not row.get("来源优先整组核验明细ID")
                    and not row.get("来源优先证据工作台ID")
                )
            )
        )
    checks.append(ok(
        "第 19 期全量逐专业证据执行工作台摘要和行数正确",
        full_major_evidence_summary.get("status")
        == "issue19_full_major_evidence_workbench_not_final"
        and full_major_evidence_summary.get("generated_by")
        == "build_issue19_full_major_evidence_workbench.py"
        and full_major_evidence_summary.get("source_full_major_verification_batches")
        == "data/working/issue19-full-major-verification-batches.csv"
        and full_major_evidence_summary.get("source_full_major_fidelity_ledger")
        == "data/working/issue19-full-major-field-fidelity-ledger.csv"
        and full_major_evidence_summary.get("source_family_major_detail")
        == "data/working/issue19-family-fit-major-detail.csv"
        and full_major_evidence_summary.get("source_page_fidelity_review_queue")
        == "data/working/issue19-page-fidelity-review-queue.csv"
        and full_major_evidence_summary.get("source_priority_group_major_review_pack")
        == "data/working/issue19-priority-group-major-review-pack.csv"
        and full_major_evidence_summary.get("source_priority_major_evidence_workbench")
        == "data/working/issue19-priority-major-evidence-workbench.csv"
        and full_major_evidence_summary.get("output_table")
        == "data/working/issue19-full-major-evidence-workbench.csv"
        and full_major_evidence_summary.get("row_count") == 13736
        and full_major_evidence_summary.get("unique_major_line_id_count") == 13736
        and full_major_evidence_summary.get("unique_group_occurrence_id_count") == 3289
        and full_major_evidence_summary.get("unique_school_count") == 1100
        and full_major_evidence_summary.get("unique_pdf_page_count") == 231
        and full_major_evidence_summary.get("priority_pack_row_count") == 7537
        and full_major_evidence_summary.get("non_priority_row_count") == 6199
        and full_major_evidence_summary.get("candidate_v3_fidelity_hit_row_count") == 8328
        and full_major_evidence_summary.get("b0_b1_school_source_hit_row_count") == 854
        and full_major_evidence_summary.get("d0_pdf_evidence_hit_row_count") == 56
        and full_major_evidence_summary.get("b0_b1_plan_conflict_row_count") == 18
        and full_major_evidence_summary.get("b0_b1_unmatched_major_row_count") == 28
        and full_major_evidence_summary.get("missing_plan_count_row_count") == 5739
        and full_major_evidence_summary.get("missing_tuition_row_count") == 1040
        and full_major_evidence_summary.get("missing_subject_row_count") == 11456
        and full_major_evidence_summary.get("historical_exact_group_hit_row_count") == 11722
        and full_major_evidence_summary.get("auto_final_list_allowed_count") == 0
        and full_major_evidence_summary.get("next_stage_allowed_count") == 0
        and len(full_major_evidence_rows) == 13736,
        f"{len(full_major_evidence_rows)} full evidence rows",
    ))
    checks.append(ok(
        "第 19 期全量逐专业证据执行工作台字段、主键和非最终门禁正确",
        required_full_major_evidence_fields.issubset(full_major_evidence_fields)
        and len({row.get("全量证据工作台ID") for row in full_major_evidence_rows})
        == len(full_major_evidence_rows)
        and len(full_major_evidence_ids) == len(full_major_evidence_rows)
        and full_major_evidence_ids == full_major_verification_ids
        and sum(row.get("是否在优先整组核验包") == "true" for row in full_major_evidence_rows) == 7537
        and sum(row.get("是否在优先整组核验包") == "false" for row in full_major_evidence_rows) == 6199
        and all(
            row.get("来源全量逐专业核验批次表")
            == "data/working/issue19-full-major-verification-batches.csv"
            and row.get("来源全量逐专业保真总账")
            == "data/working/issue19-full-major-field-fidelity-ledger.csv"
            and row.get("来源家庭底线逐专业表")
            == "data/working/issue19-family-fit-major-detail.csv"
            and row.get("来源页级保真复核队列")
            == "data/working/issue19-page-fidelity-review-queue.csv"
            and row.get("来源优先整组核验包")
            == "data/working/issue19-priority-group-major-review-pack.csv"
            and row.get("来源优先逐专业证据工作台")
            == "data/working/issue19-priority-major-evidence-workbench.csv"
            and row.get("数据阶段") == "issue19_full_major_evidence_workbench"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("核验状态") == "pending_full_major_evidence_execution"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("PDF原页证据状态") == "has_page_hash_pending_manual_pdf_review"
            and row.get("湖北官方系统证据状态")
            == "pending_hubei_official_plan_or_platform_review"
            and row.get("PDF字段核验状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/章程字段核验状态") == "pending_school_plan_or_charter_review"
            and row.get("家庭接受度核验状态") == "pending_family_acceptance_review"
            and all(token in row.get("执行必须核验字段", "") for token in priority_major_required_tokens)
            and all(token in row.get("证据缺口", "") for token in priority_major_gap_tokens)
            for row in full_major_evidence_rows
        ),
    ))
    checks.append(ok(
        "第 19 期全量逐专业证据执行工作台执行优先级、辅证和来源闭环正确",
        full_major_evidence_priority_counts
        == Counter(full_major_evidence_summary.get("priority_counts", {}))
        and full_major_evidence_source_counts
        == Counter(full_major_evidence_summary.get("official_source_status_counts", {}))
        and full_major_evidence_historical_counts
        == Counter(full_major_evidence_summary.get("historical_status_counts", {}))
        and full_major_evidence_marker_counts
        == Counter(full_major_evidence_summary.get("evidence_marker_counts", {}))
        and full_major_evidence_summary.get("priority_counts") == {
            "E0-PDF原页/组边界阻断先核": 1362,
            "E1-历史候选/样本三方证据先核": 450,
            "E2-数字媒体技术三方证据先核": 405,
            "E3-已有高校官网辅证先交叉": 148,
            "E4-计划学费选科字段先补证": 4878,
            "E5-同组调剂风险先核": 173,
            "E6-其他偏好整组按页推进": 121,
            "F0-非优先包PDF原页/结构阻断先核": 2685,
            "F1-非优先包已有官网辅证先交叉": 260,
            "F2-非优先包计划学费选科字段补证": 2920,
            "F3-非优先包家庭底线/调剂风险先核": 125,
            "F4-非优先包低风险抽检但非最终": 209,
        }
        and full_major_evidence_summary.get("official_source_status_counts") == {
            "charter_or_rules_only_no_plan": 63,
            "has_partial_source_needs_followup": 412,
            "has_reusable_2026_hubei_plan_source": 194,
            "needs_official_plan_source_search": 167,
            "not_yet_school_source_searched_in_full_workbench": 12882,
            "官网专业名匹配但计划数冲突-优先核页": 18,
        }
        and full_major_evidence_summary.get("historical_status_counts") == {
            "同代码1年命中，需重点核组号变化": 1940,
            "同代码2年命中，仅作稳定性线索": 3946,
            "同代码3年命中，仅作稳定性线索": 5836,
            "同代码三年未命中或组号变化，需人工判断历史参照": 2014,
        }
        and full_major_evidence_summary.get("evidence_marker_counts") == {
            "B0/B1官网未匹配专业": 28,
            "B0/B1计划数冲突": 18,
            "命中B0/B1学校官网来源队列": 854,
            "命中D0原页OCR证据": 56,
            "命中候选V3保真总账": 8328,
            "已纳入优先整组逐专业证据工作台": 7537,
            "暂无可复用辅证": 4738,
        }
        and full_major_evidence_distribution_ok,
    ))
    checks.append(ok(
        "第 19 期全量逐专业证据执行工作台公开文件不含本地路径、图片扩展名、身份信息、登录态和最终建议结论",
        "private/" not in full_major_evidence_public_text
        and "private\\" not in full_major_evidence_public_text
        and "/Users/" not in full_major_evidence_public_text
        and "ocr-runs" not in full_major_evidence_public_text
        and "rendered-pages" not in full_major_evidence_public_text
        and ".png" not in full_major_evidence_public_text
        and ".jpg" not in full_major_evidence_public_text
        and ".jpeg" not in full_major_evidence_public_text
        and "Authorization" not in full_major_evidence_public_text
        and "Bearer " not in full_major_evidence_public_text
        and "Cookie" not in full_major_evidence_public_text
        and "final_allowed" not in full_major_evidence_public_text
        and "ready_for_discussion" not in full_major_evidence_public_text
        and "已确认" not in full_major_evidence_public_text
        and "已核准" not in full_major_evidence_public_text
        and "最终推荐" not in full_major_evidence_public_text
        and "最终方案" not in full_major_evidence_public_text
        and "可填报" not in full_major_evidence_public_text
        and "可排序" not in full_major_evidence_public_text
        and not any(token in full_major_evidence_public_text for token in shared_forbidden_tokens),
    ))

    full_major_closure_summary_path = (
        ROOT / "data/working/issue19-full-major-evidence-closure-tasks-summary.json"
    )
    full_major_closure_csv = (
        ROOT / "data/working/issue19-full-major-evidence-closure-tasks.csv"
    )
    full_major_closure_summary = json.loads(
        full_major_closure_summary_path.read_text()
    )
    with full_major_closure_csv.open(newline="", encoding="utf-8-sig") as f:
        full_major_closure_reader = csv.DictReader(f)
        full_major_closure_rows = list(full_major_closure_reader)
        full_major_closure_fields = set(full_major_closure_reader.fieldnames or [])
    required_full_major_closure_fields = {
        "证据闭环任务ID",
        "来源全量证据工作台ID",
        "最终可用",
        "是否可升级",
        "任务状态",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "全量证据执行优先级",
        "证据项排序",
        "证据项",
        "证据任务优先级",
        "证据任务状态",
        "需要核验字段",
        "执行动作代码",
        "阻断或待核原因",
    }
    full_major_evidence_by_workbench_id = {
        row.get("全量证据工作台ID"): row for row in full_major_evidence_rows
    }
    full_major_closure_ids = {
        row.get("证据闭环任务ID") for row in full_major_closure_rows
    }
    full_major_closure_major_ids = {
        row.get("专业行ID") for row in full_major_closure_rows
    }
    full_major_closure_item_counts = Counter(
        row.get("证据项") for row in full_major_closure_rows
    )
    full_major_closure_priority_counts = Counter(
        row.get("证据任务优先级") for row in full_major_closure_rows
    )
    full_major_closure_status_counts = Counter(
        row.get("证据任务状态") for row in full_major_closure_rows
    )
    full_major_closure_execution_counts = Counter(
        row.get("全量证据执行优先级") for row in full_major_closure_rows
    )
    full_major_closure_base_items = {
        "PDF原页核验",
        "湖北官方系统/省招办计划核验",
        "高校官网/章程辅证",
        "家庭接受度核验",
        "同组调剂结论核验",
        "三年投档稳定性核验",
    }
    full_major_closure_items_by_major = {}
    full_major_closure_task_count_by_major = Counter()
    for row in full_major_closure_rows:
        major_id = row.get("专业行ID")
        full_major_closure_items_by_major.setdefault(major_id, Counter())[row.get("证据项")] += 1
        full_major_closure_task_count_by_major[major_id] += 1
    full_major_closure_task_count_distribution = Counter(full_major_closure_task_count_by_major.values())
    full_major_closure_distribution_ok = True
    for row in full_major_closure_rows:
        source_row = full_major_evidence_by_workbench_id.get(
            row.get("来源全量证据工作台ID")
        )
        full_major_closure_distribution_ok = (
            full_major_closure_distribution_ok
            and bool(source_row)
            and row.get("专业行ID") == source_row.get("专业行ID")
            and row.get("专业组出现ID") == source_row.get("专业组出现ID")
            and row.get("院校代码") == source_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == source_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == source_row.get("来源页码")
            and row.get("全量证据执行优先级")
            == source_row.get("全量证据执行优先级")
        )
    full_major_closure_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [full_major_closure_summary_path, full_major_closure_csv]
    )
    checks.append(ok(
        "第 19 期全量逐专业证据闭环任务队列摘要和行数正确",
        full_major_closure_summary.get("status")
        == "issue19_full_major_evidence_closure_tasks_not_final"
        and full_major_closure_summary.get("generated_by")
        == "build_issue19_full_major_evidence_closure_tasks.py"
        and full_major_closure_summary.get("source_full_major_evidence_workbench")
        == "data/working/issue19-full-major-evidence-workbench.csv"
        and full_major_closure_summary.get("output_table")
        == "data/working/issue19-full-major-evidence-closure-tasks.csv"
        and full_major_closure_summary.get("source_major_row_count") == 13736
        and full_major_closure_summary.get("task_row_count") == 94935
        and full_major_closure_summary.get("unique_task_id_count") == 94935
        and full_major_closure_summary.get("unique_major_line_id_count") == 13736
        and full_major_closure_summary.get("base_task_count") == 82416
        and full_major_closure_summary.get("conditional_field_gap_task_count") == 12473
        and full_major_closure_summary.get("conditional_b0_b1_task_count") == 46
        and full_major_closure_summary.get("auto_upgrade_allowed_count") == 0
        and full_major_closure_summary.get("final_available_count") == 0
        and len(full_major_closure_rows) == 94935,
        f"{len(full_major_closure_rows)} closure tasks",
    ))
    checks.append(ok(
        "第 19 期全量逐专业证据闭环任务队列字段、主键和非最终门禁正确",
        required_full_major_closure_fields.issubset(full_major_closure_fields)
        and len(full_major_closure_ids) == len(full_major_closure_rows)
        and full_major_closure_major_ids == full_major_evidence_ids
        and full_major_closure_task_count_distribution == Counter({7: 12433, 6: 1260, 8: 43})
        and all(
            full_major_closure_items_by_major.get(major_id, Counter()).get(item) == 1
            for major_id in full_major_evidence_ids
            for item in full_major_closure_base_items
        )
        and all(
            row.get("最终可用") == "false"
            and row.get("是否可升级") == "false"
            and row.get("任务状态") == "pending_evidence_closure"
            and row.get("来源全量证据工作台ID") in full_major_evidence_by_workbench_id
            and row.get("证据项")
            in {
                "PDF原页核验",
                "湖北官方系统/省招办计划核验",
                "高校官网/章程辅证",
                "家庭接受度核验",
                "同组调剂结论核验",
                "三年投档稳定性核验",
                "字段完整性补证",
                "B0/B1官网冲突或未匹配复核",
            }
            for row in full_major_closure_rows
        ),
    ))
    checks.append(ok(
        "第 19 期全量逐专业证据闭环任务队列任务分布和来源闭环正确",
        full_major_closure_item_counts
        == Counter(full_major_closure_summary.get("evidence_item_counts", {}))
        and full_major_closure_priority_counts
        == Counter(full_major_closure_summary.get("task_priority_counts", {}))
        and full_major_closure_status_counts
        == Counter(full_major_closure_summary.get("task_status_counts", {}))
        and full_major_closure_execution_counts
        == Counter(full_major_closure_summary.get("execution_priority_counts", {}))
        and full_major_closure_summary.get("evidence_item_counts") == {
            "PDF原页核验": 13736,
            "湖北官方系统/省招办计划核验": 13736,
            "高校官网/章程辅证": 13736,
            "家庭接受度核验": 13736,
            "同组调剂结论核验": 13736,
            "三年投档稳定性核验": 13736,
            "字段完整性补证": 12473,
            "B0/B1官网冲突或未匹配复核": 46,
        }
        and full_major_closure_summary.get("task_priority_counts") == {
            "P0-B0B1冲突/未匹配先核": 46,
            "P0-三方证据闭环先核": 2526,
            "P0-先核PDF结构阻断": 4047,
            "P1-字段补证": 59261,
            "P1-家庭底线和调剂风险": 6594,
            "P2-常规证据闭环": 22461,
        }
        and full_major_closure_summary.get("task_status_counts") == {
            "has_charter_or_rules_but_no_plan_detail": 63,
            "has_d0_page_ocr_evidence_pending_original_pdf_review": 56,
            "has_historical_line_pending_stability_review": 11722,
            "has_partial_school_source_pending_followup": 412,
            "has_school_plan_source_pending_crosscheck": 194,
            "pending_b0_b1_plan_conflict_review": 18,
            "pending_b0_b1_unmatched_major_review": 28,
            "pending_family_acceptance_review": 13736,
            "pending_field_gap_review": 12473,
            "pending_full_group_adjustment_review": 13736,
            "pending_group_code_change_or_missing_history_review": 2014,
            "pending_hubei_official_plan_review": 13736,
            "pending_original_pdf_page_review": 13680,
            "pending_school_plan_or_charter_review": 12882,
            "pending_school_plan_source_search": 167,
            "school_source_conflict_pending_pdf_and_hubei_review": 18,
        }
        and full_major_closure_distribution_ok,
    ))
    checks.append(ok(
        "第 19 期全量逐专业证据闭环任务队列公开文件不含本地路径、图片扩展名、身份信息、登录态和最终建议结论",
        "private/" not in full_major_closure_public_text
        and "private\\" not in full_major_closure_public_text
        and "/Users/" not in full_major_closure_public_text
        and "ocr-runs" not in full_major_closure_public_text
        and "rendered-pages" not in full_major_closure_public_text
        and ".png" not in full_major_closure_public_text
        and ".jpg" not in full_major_closure_public_text
        and ".jpeg" not in full_major_closure_public_text
        and "Authorization" not in full_major_closure_public_text
        and "Bearer " not in full_major_closure_public_text
        and "Cookie" not in full_major_closure_public_text
        and "final_allowed" not in full_major_closure_public_text
        and "ready_for_discussion" not in full_major_closure_public_text
        and "已确认" not in full_major_closure_public_text
        and "已核准" not in full_major_closure_public_text
        and "最终推荐" not in full_major_closure_public_text
        and "最终方案" not in full_major_closure_public_text
        and "可填报" not in full_major_closure_public_text
        and "可排序" not in full_major_closure_public_text
        and not any(token in full_major_closure_public_text for token in shared_forbidden_tokens),
    ))

    p0_execution_summary_path = (
        ROOT / "data/working/issue19-p0-evidence-execution-packets-summary.json"
    )
    p0_execution_csv = ROOT / "data/working/issue19-p0-evidence-execution-packets.csv"
    p0_execution_summary = json.loads(p0_execution_summary_path.read_text())
    with p0_execution_csv.open(newline="", encoding="utf-8-sig") as f:
        p0_execution_reader = csv.DictReader(f)
        p0_execution_rows = list(p0_execution_reader)
        p0_execution_fields = set(p0_execution_reader.fieldnames or [])
    required_p0_execution_fields = {
        "P0执行包任务ID",
        "P0执行包ID",
        "来源证据闭环任务队列",
        "来源证据闭环任务ID",
        "来源全量证据工作台ID",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "是否可升级",
        "执行包状态",
        "P0执行包类型",
        "P0页码优先序",
        "P0学校优先序",
        "P0页内任务数",
        "P0学校任务数",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "全量证据执行优先级",
        "证据项",
        "证据任务优先级",
        "证据任务状态",
        "需要核验字段",
        "执行动作代码",
        "阻断或待核原因",
    }
    p0_priority_to_packet_type = {
        "P0-先核PDF结构阻断": "P0A-PDF原页结构阻断",
        "P0-三方证据闭环先核": "P0B-三方证据闭环",
        "P0-B0B1冲突/未匹配先核": "P0C-B0B1差异复核",
    }
    p0_source_closure_rows = [
        row for row in full_major_closure_rows if row.get("证据任务优先级", "").startswith("P0-")
    ]
    p0_source_by_task_id = {
        row.get("证据闭环任务ID"): row for row in p0_source_closure_rows
    }
    p0_execution_task_ids = {row.get("P0执行包任务ID") for row in p0_execution_rows}
    p0_execution_source_task_ids = {
        row.get("来源证据闭环任务ID") for row in p0_execution_rows
    }
    p0_execution_major_ids = {row.get("专业行ID") for row in p0_execution_rows}
    p0_source_major_ids = {row.get("专业行ID") for row in p0_source_closure_rows}
    p0_execution_packet_ids = {row.get("P0执行包ID") for row in p0_execution_rows}
    p0_execution_packet_type_counts = Counter(row.get("P0执行包类型") for row in p0_execution_rows)
    p0_execution_status_counts = Counter(row.get("证据任务状态") for row in p0_execution_rows)
    p0_execution_item_counts = Counter(row.get("证据项") for row in p0_execution_rows)
    p0_source_page_counts = Counter(row.get("来源页码") for row in p0_source_closure_rows)
    p0_source_school_counts = Counter(
        (row.get("院校代码"), row.get("院校名称OCR")) for row in p0_source_closure_rows
    )
    p0_source_packet_groups = {
        stable_id(
            "P0PACK",
            [
                row.get("来源页码", ""),
                row.get("院校代码", ""),
                row.get("院校专业组代码OCR规范化", ""),
                p0_priority_to_packet_type.get(row.get("证据任务优先级", ""), ""),
            ],
        )
        for row in p0_source_closure_rows
    }
    p0_execution_distribution_ok = True
    for row in p0_execution_rows:
        source_row = p0_source_by_task_id.get(row.get("来源证据闭环任务ID"))
        expected_packet_type = p0_priority_to_packet_type.get(row.get("证据任务优先级", ""))
        expected_packet_id = stable_id(
            "P0PACK",
            [
                row.get("来源页码", ""),
                row.get("院校代码", ""),
                row.get("院校专业组代码OCR规范化", ""),
                row.get("P0执行包类型", ""),
            ],
        )
        p0_execution_distribution_ok = (
            p0_execution_distribution_ok
            and bool(source_row)
            and row.get("P0执行包ID") == expected_packet_id
            and row.get("P0执行包任务ID")
            == stable_id("P0TASK", [row.get("P0执行包ID", ""), row.get("来源证据闭环任务ID", "")])
            and row.get("P0执行包类型") == expected_packet_type
            and row.get("来源全量证据工作台ID") == source_row.get("来源全量证据工作台ID")
            and row.get("专业行ID") == source_row.get("专业行ID")
            and row.get("专业组出现ID") == source_row.get("专业组出现ID")
            and row.get("院校代码") == source_row.get("院校代码")
            and row.get("院校名称OCR") == source_row.get("院校名称OCR")
            and row.get("院校专业组代码OCR规范化") == source_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == source_row.get("来源页码")
            and row.get("专业组内专业序号") == source_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == source_row.get("专业代号OCR")
            and row.get("专业名称及备注OCR短摘") == source_row.get("专业名称及备注OCR短摘")
            and row.get("全量证据执行优先级") == source_row.get("全量证据执行优先级")
            and row.get("证据项") == source_row.get("证据项")
            and row.get("证据任务优先级") == source_row.get("证据任务优先级")
            and row.get("证据任务状态") == source_row.get("证据任务状态")
            and row.get("执行动作代码") == source_row.get("执行动作代码")
            and as_int(row.get("P0页内任务数")) == p0_source_page_counts[row.get("来源页码")]
            and as_int(row.get("P0学校任务数"))
            == p0_source_school_counts[(row.get("院校代码"), row.get("院校名称OCR"))]
        )
    p0_execution_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [p0_execution_summary_path, p0_execution_csv]
    )
    checks.append(ok(
        "第 19 期 P0 证据执行包摘要和行数正确",
        p0_execution_summary.get("status") == "issue19_p0_evidence_execution_packets_not_final"
        and p0_execution_summary.get("generated_by") == "build_issue19_p0_evidence_execution_packets.py"
        and p0_execution_summary.get("source_closure_tasks")
        == "data/working/issue19-full-major-evidence-closure-tasks.csv"
        and p0_execution_summary.get("output_table")
        == "data/working/issue19-p0-evidence-execution-packets.csv"
        and p0_execution_summary.get("source_closure_task_count") == 94935
        and p0_execution_summary.get("p0_task_row_count") == 6619
        and p0_execution_summary.get("unique_p0_task_id_count") == 6619
        and p0_execution_summary.get("unique_source_closure_task_id_count") == 6619
        and p0_execution_summary.get("unique_major_line_id_count") == 5310
        and p0_execution_summary.get("unique_packet_id_count") == 2282
        and p0_execution_summary.get("unique_pdf_page_count") == 231
        and p0_execution_summary.get("unique_school_count") == 1056
        and p0_execution_summary.get("auto_upgrade_allowed_count") == 0
        and p0_execution_summary.get("final_available_count") == 0
        and len(p0_execution_rows) == 6619,
        f"{len(p0_execution_rows)} P0 tasks",
    ))
    checks.append(ok(
        "第 19 期 P0 证据执行包字段、主键和逐专业粒度正确",
        required_p0_execution_fields.issubset(p0_execution_fields)
        and len(p0_execution_task_ids) == len(p0_execution_rows)
        and p0_execution_source_task_ids == set(p0_source_by_task_id)
        and p0_execution_major_ids == p0_source_major_ids
        and p0_execution_packet_ids == p0_source_packet_groups
        and all(
            row.get("来源证据闭环任务队列")
            == "data/working/issue19-full-major-evidence-closure-tasks.csv"
            and row.get("数据阶段") == "issue19_p0_evidence_execution_packets"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("任务粒度") == "逐专业招生明细×P0证据项"
            and row.get("最终可用") == "false"
            and row.get("是否可升级") == "false"
            and row.get("执行包状态") == "pending_p0_evidence_execution"
            and row.get("专业行ID")
            and row.get("来源全量证据工作台ID")
            for row in p0_execution_rows
        ),
    ))
    checks.append(ok(
        "第 19 期 P0 证据执行包任务分布和闭环来源正确",
        p0_execution_packet_type_counts == Counter(p0_execution_summary.get("packet_type_counts", {}))
        and p0_execution_status_counts == Counter(p0_execution_summary.get("task_status_counts", {}))
        and p0_execution_item_counts == Counter(p0_execution_summary.get("evidence_item_counts", {}))
        and p0_execution_summary.get("packet_type_counts") == {
            "P0A-PDF原页结构阻断": 4047,
            "P0B-三方证据闭环": 2526,
            "P0C-B0B1差异复核": 46,
        }
        and p0_execution_summary.get("evidence_item_counts") == {
            "PDF原页核验": 4047,
            "湖北官方系统/省招办计划核验": 1263,
            "高校官网/章程辅证": 1263,
            "B0/B1官网冲突或未匹配复核": 46,
        }
        and p0_execution_summary.get("task_status_counts") == {
            "pending_original_pdf_page_review": 3991,
            "pending_hubei_official_plan_review": 1263,
            "pending_school_plan_source_search": 148,
            "pending_school_plan_or_charter_review": 581,
            "has_school_plan_source_pending_crosscheck": 143,
            "has_d0_page_ocr_evidence_pending_original_pdf_review": 56,
            "has_partial_school_source_pending_followup": 346,
            "pending_b0_b1_unmatched_major_review": 28,
            "school_source_conflict_pending_pdf_and_hubei_review": 4,
            "pending_b0_b1_plan_conflict_review": 18,
            "has_charter_or_rules_but_no_plan_detail": 41,
        }
        and p0_execution_distribution_ok,
    ))
    checks.append(ok(
        "第 19 期 P0 证据执行包公开文件不含本地路径、图片扩展名、身份信息、登录态和最终建议结论",
        "private/" not in p0_execution_public_text
        and "private\\" not in p0_execution_public_text
        and "/Users/" not in p0_execution_public_text
        and "ocr-runs" not in p0_execution_public_text
        and "rendered-pages" not in p0_execution_public_text
        and ".png" not in p0_execution_public_text
        and ".jpg" not in p0_execution_public_text
        and ".jpeg" not in p0_execution_public_text
        and "Authorization" not in p0_execution_public_text
        and "Bearer " not in p0_execution_public_text
        and "Cookie" not in p0_execution_public_text
        and "final_allowed" not in p0_execution_public_text
        and "ready_for_discussion" not in p0_execution_public_text
        and "已确认" not in p0_execution_public_text
        and "已核准" not in p0_execution_public_text
        and "最终推荐" not in p0_execution_public_text
        and "最终方案" not in p0_execution_public_text
        and "可填报" not in p0_execution_public_text
        and "可排序" not in p0_execution_public_text
        and not any(token in p0_execution_public_text for token in shared_forbidden_tokens),
    ))

    p0_review_summary_path = (
        ROOT / "data/working/issue19-p0-evidence-review-worklist-summary.json"
    )
    p0_review_csv = ROOT / "data/working/issue19-p0-evidence-review-worklist.csv"
    p0_review_summary = json.loads(p0_review_summary_path.read_text())
    with p0_review_csv.open(newline="", encoding="utf-8-sig") as f:
        p0_review_reader = csv.DictReader(f)
        p0_review_rows = list(p0_review_reader)
        p0_review_fields = set(p0_review_reader.fieldnames or [])
    required_p0_review_fields = {
        "P0复核工作清单ID",
        "来源P0执行包表",
        "来源P0执行包任务ID",
        "来源P0执行包ID",
        "来源证据闭环任务ID",
        "来源全量证据工作台ID",
        "来源全量证据工作台",
        "来源页级manifest",
        "来源页级保真复核队列",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "是否可升级",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "P0复核结论状态",
        "P0执行包类型",
        "P0页码优先序",
        "P0学校优先序",
        "P0页内任务数",
        "P0学校任务数",
        "证据项",
        "证据任务优先级",
        "证据任务状态",
        "需要核验字段",
        "执行动作代码",
        "阻断或待核原因",
        "PDF页码",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "页面复核优先级",
        "页面阻断等级",
        "页面专业明细数",
        "页面结构异常数",
        "页面高严重结构异常数",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "高校官网/章程辅证状态",
        "计划数核验状态",
        "证据缺口",
        "PDF原页人工核验结论状态",
        "湖北官方系统证据状态",
        "湖北官方系统人工核验结论状态",
        "高校官网/章程人工核验结论状态",
        "家庭接受度人工结论状态",
        "同组调剂人工结论状态",
        "湖北官方系统证据编号",
        "湖北官方系统证据SHA256",
        "高校官网/章程证据编号",
        "高校官网/章程证据SHA256",
        "人工核验人",
        "人工核验时间",
        "人工核验备注",
        "下一步",
    }
    p0_execution_by_task_id = {
        row.get("P0执行包任务ID"): row for row in p0_execution_rows
    }
    p0_review_ids = {row.get("P0复核工作清单ID") for row in p0_review_rows}
    p0_review_source_task_ids = {
        row.get("来源P0执行包任务ID") for row in p0_review_rows
    }
    p0_review_source_closure_ids = {
        row.get("来源证据闭环任务ID") for row in p0_review_rows
    }
    p0_review_major_ids = {row.get("专业行ID") for row in p0_review_rows}
    p0_review_packet_ids = {row.get("来源P0执行包ID") for row in p0_review_rows}
    p0_review_packet_type_counts = Counter(row.get("P0执行包类型") for row in p0_review_rows)
    p0_review_status_counts = Counter(row.get("证据任务状态") for row in p0_review_rows)
    p0_review_item_counts = Counter(row.get("证据项") for row in p0_review_rows)
    p0_review_school_source_counts = Counter(row.get("高校官网/章程辅证状态") for row in p0_review_rows)
    p0_review_gate_counts = {
        "P0复核结论状态": Counter(row.get("P0复核结论状态") for row in p0_review_rows),
        "PDF原页人工核验结论状态": Counter(row.get("PDF原页人工核验结论状态") for row in p0_review_rows),
        "湖北官方系统人工核验结论状态": Counter(row.get("湖北官方系统人工核验结论状态") for row in p0_review_rows),
        "高校官网/章程人工核验结论状态": Counter(row.get("高校官网/章程人工核验结论状态") for row in p0_review_rows),
        "家庭接受度人工结论状态": Counter(row.get("家庭接受度人工结论状态") for row in p0_review_rows),
        "同组调剂人工结论状态": Counter(row.get("同组调剂人工结论状态") for row in p0_review_rows),
    }
    p0_review_join_ok = True
    for row in p0_review_rows:
        p0_row = p0_execution_by_task_id.get(row.get("来源P0执行包任务ID"))
        full_row = full_major_evidence_by_workbench_id.get(row.get("来源全量证据工作台ID"))
        manifest_row = page_manifest_by_page.get(as_int(row.get("PDF页码")))
        page_row = page_fidelity_by_page.get(as_int(row.get("PDF页码")))
        p0_review_join_ok = (
            p0_review_join_ok
            and bool(p0_row)
            and bool(full_row)
            and bool(manifest_row)
            and bool(page_row)
            and row.get("P0复核工作清单ID")
            == stable_id(
                "P0REVIEW",
                [
                    row.get("来源P0执行包任务ID", ""),
                    row.get("来源全量证据工作台ID", ""),
                ],
            )
            and row.get("来源P0执行包ID") == p0_row.get("P0执行包ID")
            and row.get("来源证据闭环任务ID") == p0_row.get("来源证据闭环任务ID")
            and row.get("P0执行包类型") == p0_row.get("P0执行包类型")
            and row.get("P0页码优先序") == p0_row.get("P0页码优先序")
            and row.get("P0学校优先序") == p0_row.get("P0学校优先序")
            and row.get("P0页内任务数") == p0_row.get("P0页内任务数")
            and row.get("P0学校任务数") == p0_row.get("P0学校任务数")
            and row.get("证据项") == p0_row.get("证据项")
            and row.get("证据任务优先级") == p0_row.get("证据任务优先级")
            and row.get("证据任务状态") == p0_row.get("证据任务状态")
            and row.get("需要核验字段") == p0_row.get("需要核验字段")
            and row.get("执行动作代码") == p0_row.get("执行动作代码")
            and row.get("阻断或待核原因") == p0_row.get("阻断或待核原因")
            and row.get("PDF页码") == p0_row.get("来源页码")
            and row.get("专业行ID") == p0_row.get("专业行ID")
            and row.get("专业组出现ID") == p0_row.get("专业组出现ID")
            and row.get("院校代码") == p0_row.get("院校代码")
            and row.get("院校名称OCR") == p0_row.get("院校名称OCR")
            and row.get("院校专业组代码OCR规范化")
            == p0_row.get("院校专业组代码OCR规范化")
            and row.get("专业组内专业序号") == p0_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == p0_row.get("专业代号OCR")
            and row.get("来源期号") == full_row.get("来源期号")
            and row.get("来源PDF_SHA256") == full_row.get("来源PDF_SHA256")
            and row.get("专业名称及备注OCR") == full_row.get("专业名称及备注OCR")
            and row.get("再选科目OCR候选") == full_row.get("再选科目OCR候选")
            and row.get("专业计划数OCR候选") == full_row.get("专业计划数OCR候选")
            and row.get("学费OCR候选") == full_row.get("学费OCR候选")
            and row.get("高校官网/章程辅证状态") == full_row.get("高校官网/章程辅证状态")
            and row.get("计划数核验状态") == full_row.get("计划数核验状态")
            and row.get("证据缺口") == full_row.get("证据缺口")
            and row.get("湖北官方系统证据状态") == full_row.get("湖北官方系统证据状态")
            and row.get("私有页图证据编号") == manifest_row.get("私有页图证据编号")
            and row.get("私有OCR文本证据编号") == manifest_row.get("私有OCR文本证据编号")
            and row.get("私有页图SHA256") == manifest_row.get("私有页图SHA256")
            and row.get("私有OCR文本SHA256") == manifest_row.get("私有OCR文本SHA256")
            and row.get("OCR平均置信度") == manifest_row.get("OCR平均置信度")
            and row.get("OCR_QC_P0数") == manifest_row.get("OCR_QC_P0数")
            and row.get("OCR_QC_P1数") == manifest_row.get("OCR_QC_P1数")
            and row.get("页面复核优先级") == page_row.get("页面复核优先级")
            and row.get("页面阻断等级") == page_row.get("页面阻断等级")
            and row.get("页面专业明细数") == page_row.get("页面专业明细数")
            and row.get("页面结构异常数") == page_row.get("页面结构异常数")
            and row.get("页面高严重结构异常数") == page_row.get("页面高严重结构异常数")
            and row.get("风险字段Top") == page_row.get("风险字段Top")
            and row.get("风险规则Top") == page_row.get("风险规则Top")
            and re.fullmatch(r"page-\d{3}", row.get("私有页图证据编号", "")) is not None
            and re.fullmatch(r"\d{3}_page-\d{3}", row.get("私有OCR文本证据编号", "")) is not None
            and re.fullmatch(r"[0-9a-f]{64}", row.get("私有页图SHA256", "")) is not None
            and re.fullmatch(r"[0-9a-f]{64}", row.get("私有OCR文本SHA256", "")) is not None
        )
    p0_review_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [p0_review_summary_path, p0_review_csv]
    )
    checks.append(ok(
        "第 19 期 P0 逐专业复核工作清单摘要和行数正确",
        p0_review_summary.get("status") == "issue19_p0_evidence_review_worklist_not_final"
        and p0_review_summary.get("generated_by") == "build_issue19_p0_evidence_review_worklist.py"
        and p0_review_summary.get("source_p0_execution_packets")
        == "data/working/issue19-p0-evidence-execution-packets.csv"
        and p0_review_summary.get("source_full_major_evidence_workbench")
        == "data/working/issue19-full-major-evidence-workbench.csv"
        and p0_review_summary.get("source_page_manifest")
        == "data/working/issue19-page-manifest.csv"
        and p0_review_summary.get("source_page_fidelity_review_queue")
        == "data/working/issue19-page-fidelity-review-queue.csv"
        and p0_review_summary.get("output_table")
        == "data/working/issue19-p0-evidence-review-worklist.csv"
        and p0_review_summary.get("source_p0_task_row_count") == 6619
        and p0_review_summary.get("worklist_row_count") == 6619
        and p0_review_summary.get("unique_worklist_id_count") == 6619
        and p0_review_summary.get("unique_source_p0_task_id_count") == 6619
        and p0_review_summary.get("unique_source_closure_task_id_count") == 6619
        and p0_review_summary.get("unique_major_line_id_count") == 5310
        and p0_review_summary.get("unique_packet_id_count") == 2282
        and p0_review_summary.get("unique_pdf_page_count") == 231
        and p0_review_summary.get("unique_school_count") == 1056
        and p0_review_summary.get("full_evidence_hit_count") == 6619
        and p0_review_summary.get("page_manifest_hit_count") == 6619
        and p0_review_summary.get("page_fidelity_hit_count") == 6619
        and len(p0_review_rows) == 6619,
        f"{len(p0_review_rows)} P0 review rows",
    ))
    checks.append(ok(
        "第 19 期 P0 逐专业复核工作清单字段、主键和门禁正确",
        required_p0_review_fields.issubset(p0_review_fields)
        and len(p0_review_ids) == len(p0_review_rows)
        and p0_review_source_task_ids == p0_execution_task_ids
        and p0_review_source_closure_ids == p0_execution_source_task_ids
        and p0_review_major_ids == p0_execution_major_ids
        and p0_review_packet_ids == p0_execution_packet_ids
        and p0_review_summary.get("final_available_count") == 0
        and p0_review_summary.get("auto_upgrade_allowed_count") == 0
        and p0_review_summary.get("next_stage_allowed_count") == 0
        and p0_review_summary.get("final_major_list_candidate_count") == 0
        and all(
            row.get("来源P0执行包表")
            == "data/working/issue19-p0-evidence-execution-packets.csv"
            and row.get("来源全量证据工作台")
            == "data/working/issue19-full-major-evidence-workbench.csv"
            and row.get("来源页级manifest")
            == "data/working/issue19-page-manifest.csv"
            and row.get("来源页级保真复核队列")
            == "data/working/issue19-page-fidelity-review-queue.csv"
            and row.get("数据阶段") == "issue19_p0_evidence_review_worklist"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("任务粒度") == "逐专业招生明细×P0证据项"
            and row.get("最终可用") == "false"
            and row.get("是否可升级") == "false"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("P0复核结论状态") == "pending_p0_manual_review"
            and row.get("PDF原页人工核验结论状态") == "pending_original_pdf_page_review"
            and row.get("湖北官方系统人工核验结论状态") == "pending_hubei_official_plan_review"
            and row.get("高校官网/章程人工核验结论状态") == "pending_school_plan_or_charter_review"
            and row.get("家庭接受度人工结论状态") == "pending_family_acceptance_review"
            and row.get("同组调剂人工结论状态") == "pending_transfer_decision"
            and not row.get("湖北官方系统证据编号")
            and not row.get("湖北官方系统证据SHA256")
            and not row.get("高校官网/章程证据编号")
            and not row.get("高校官网/章程证据SHA256")
            and not row.get("人工核验人")
            and not row.get("人工核验时间")
            for row in p0_review_rows
        ),
    ))
    checks.append(ok(
        "第 19 期 P0 逐专业复核工作清单与执行包、专业明细、页级证据逐行闭环",
        p0_review_packet_type_counts == Counter(p0_review_summary.get("packet_type_counts", {}))
        and p0_review_status_counts == Counter(p0_review_summary.get("task_status_counts", {}))
        and p0_review_item_counts == Counter(p0_review_summary.get("evidence_item_counts", {}))
        and p0_review_school_source_counts == Counter(p0_review_summary.get("school_source_status_counts", {}))
        and {
            key: dict(value) for key, value in p0_review_gate_counts.items()
        } == p0_review_summary.get("manual_gate_status_counts")
        and p0_review_summary.get("packet_type_counts") == {
            "P0A-PDF原页结构阻断": 4047,
            "P0B-三方证据闭环": 2526,
            "P0C-B0B1差异复核": 46,
        }
        and p0_review_summary.get("evidence_item_counts") == {
            "PDF原页核验": 4047,
            "湖北官方系统/省招办计划核验": 1263,
            "高校官网/章程辅证": 1263,
            "B0/B1官网冲突或未匹配复核": 46,
        }
        and p0_review_summary.get("task_status_counts") == {
            "pending_original_pdf_page_review": 3991,
            "pending_hubei_official_plan_review": 1263,
            "pending_school_plan_source_search": 148,
            "pending_school_plan_or_charter_review": 581,
            "has_school_plan_source_pending_crosscheck": 143,
            "has_d0_page_ocr_evidence_pending_original_pdf_review": 56,
            "has_partial_school_source_pending_followup": 346,
            "pending_b0_b1_unmatched_major_review": 28,
            "school_source_conflict_pending_pdf_and_hubei_review": 4,
            "pending_b0_b1_plan_conflict_review": 18,
            "has_charter_or_rules_but_no_plan_detail": 41,
        }
        and p0_review_summary.get("school_source_status_counts") == {
            "needs_official_plan_source_search": 315,
            "not_yet_school_source_searched_in_full_workbench": 5037,
            "has_reusable_2026_hubei_plan_source": 343,
            "has_partial_source_needs_followup": 780,
            "官网专业名匹配但计划数冲突-优先核页": 40,
            "charter_or_rules_only_no_plan": 104,
        }
        and p0_review_join_ok,
    ))
    checks.append(ok(
        "第 19 期 P0 逐专业复核工作清单公开文件不含本地路径、图片扩展名、身份信息、登录态和最终建议结论",
        "private/" not in p0_review_public_text
        and "private\\" not in p0_review_public_text
        and "/Users/" not in p0_review_public_text
        and "ocr-runs" not in p0_review_public_text
        and "rendered-pages" not in p0_review_public_text
        and ".png" not in p0_review_public_text
        and ".jpg" not in p0_review_public_text
        and ".jpeg" not in p0_review_public_text
        and "Authorization" not in p0_review_public_text
        and "Bearer " not in p0_review_public_text
        and "Cookie" not in p0_review_public_text
        and "final_allowed" not in p0_review_public_text
        and "ready_for_discussion" not in p0_review_public_text
        and "已确认" not in p0_review_public_text
        and "已核准" not in p0_review_public_text
        and "最终推荐" not in p0_review_public_text
        and "最终方案" not in p0_review_public_text
        and "可填报" not in p0_review_public_text
        and "可排序" not in p0_review_public_text
        and not any(token in p0_review_public_text for token in shared_forbidden_tokens),
    ))

    field_gap_summary_path = ROOT / "data/working/issue19-p1-field-gap-evidence-repair-matrix-summary.json"
    field_gap_csv = ROOT / "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv"
    hubei_official_summary_path = (
        ROOT / "data/working/issue19-hubei-official-plan-major-crosscheck-packets-summary.json"
    )
    hubei_official_csv = (
        ROOT / "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"
    )
    b0_b1_diff_summary_path = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger-summary.json"
    b0_b1_diff_csv = ROOT / "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
    field_gap_summary = json.loads(field_gap_summary_path.read_text())
    hubei_official_summary = json.loads(hubei_official_summary_path.read_text())
    b0_b1_diff_summary = json.loads(b0_b1_diff_summary_path.read_text())
    with field_gap_csv.open(newline="", encoding="utf-8-sig") as f:
        field_gap_reader = csv.DictReader(f)
        field_gap_rows = list(field_gap_reader)
        field_gap_fields = set(field_gap_reader.fieldnames or [])
    with hubei_official_csv.open(newline="", encoding="utf-8-sig") as f:
        hubei_official_reader = csv.DictReader(f)
        hubei_official_rows = list(hubei_official_reader)
        hubei_official_fields = set(hubei_official_reader.fieldnames or [])
    with b0_b1_diff_csv.open(newline="", encoding="utf-8-sig") as f:
        b0_b1_diff_reader = csv.DictReader(f)
        b0_b1_diff_rows = list(b0_b1_diff_reader)
        b0_b1_diff_fields = set(b0_b1_diff_reader.fieldnames or [])
    required_field_gap_fields = {
        "字段补证任务ID",
        "来源字段保真总账ID",
        "来源全量证据工作台ID",
        "来源证据闭环任务ID",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "可进入下一阶段",
        "证据状态",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "字段名",
        "OCR候选值",
        "OCR数字候选",
        "字段问题类型",
        "高风险字段集合",
        "风险触发规则",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "核验动作代码",
        "人工核验结论状态",
    }
    required_hubei_official_fields = {
        "湖北官方核验包任务ID",
        "来源证据闭环任务ID",
        "来源全量证据工作台ID",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "是否可升级",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "OCR再选科目",
        "OCR专业计划数",
        "OCR学费",
        "平台查询院校代码",
        "平台查询专业组代码",
        "平台查询专业代号",
        "平台匹配状态",
        "平台字段核验状态",
        "字段差异集合",
        "官方系统证据编号",
        "官方系统证据SHA256",
        "原始接口响应保存位置",
        "公开原始行SHA256",
    }
    required_b0_b1_diff_fields = {
        "公开官网差异账ID",
        "来源全量证据工作台ID",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "可进入下一阶段",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "OCR计划数",
        "OCR学费",
        "OCR再选科目",
        "高校官网/章程辅证状态",
        "官网来源状态",
        "官网证据匹配状态",
        "最佳官网来源文件",
        "最佳官网专业名称",
        "最佳官网计划数",
        "最佳官网学费",
        "计划数核验状态",
        "差异字段集合",
        "仍需核验",
    }
    full_major_field_gap_task_by_major_id = {
        row.get("专业行ID"): row
        for row in full_major_closure_rows
        if row.get("证据项") == "字段完整性补证"
    }
    full_major_hubei_task_by_major_id = {
        row.get("专业行ID"): row
        for row in full_major_closure_rows
        if row.get("证据项") == "湖北官方系统/省招办计划核验"
    }
    field_gap_name_to_risk_field = {
        "再选科目": "再选科目字段",
        "专业计划数": "计划数字段",
        "学费": "学费字段",
    }
    field_gap_name_to_source_field = {
        "再选科目": "再选科目OCR候选",
        "专业计划数": "专业计划数OCR候选",
        "学费": "学费OCR候选",
    }
    field_gap_join_ok = True
    for row in field_gap_rows:
        fidelity_row = full_major_fidelity_by_major_id.get(row.get("专业行ID"))
        full_row = full_major_evidence_by_workbench_id.get(row.get("来源全量证据工作台ID"))
        task_row = full_major_field_gap_task_by_major_id.get(row.get("专业行ID"))
        manifest_row = page_manifest_by_page.get(as_int(row.get("来源页码")))
        page_row = page_fidelity_by_page.get(as_int(row.get("来源页码")))
        field_name = row.get("字段名")
        field_gap_join_ok = (
            field_gap_join_ok
            and bool(fidelity_row)
            and bool(full_row)
            and bool(task_row)
            and bool(manifest_row)
            and bool(page_row)
            and row.get("字段补证任务ID")
            == stable_id("FIELDGAP", [row.get("专业行ID", ""), field_name])
            and row.get("来源字段保真总账ID") == fidelity_row.get("全量保真总账ID")
            and row.get("来源证据闭环任务ID") == task_row.get("证据闭环任务ID")
            and row.get("数据阶段") == "issue19_p1_field_gap_evidence_repair_matrix"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("任务粒度") == "逐专业招生明细×字段缺口"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("证据状态") == "pending_field_gap_review"
            and field_gap_name_to_risk_field.get(field_name) in split_cn_semicolon(fidelity_row.get("高风险字段集合"))
            and row.get("OCR候选值") == fidelity_row.get(field_gap_name_to_source_field.get(field_name, ""), "")
            and row.get("专业组出现ID") == fidelity_row.get("专业组出现ID") == full_row.get("专业组出现ID")
            and row.get("院校代码") == fidelity_row.get("院校代码") == full_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == fidelity_row.get("院校专业组代码OCR规范化")
            == full_row.get("院校专业组代码OCR规范化")
            and row.get("专业代号OCR") == fidelity_row.get("专业代号OCR") == full_row.get("专业代号OCR")
            and row.get("私有页图证据编号") == manifest_row.get("私有页图证据编号")
            and row.get("私有OCR文本证据编号") == manifest_row.get("私有OCR文本证据编号")
            and row.get("私有页图SHA256") == manifest_row.get("私有页图SHA256")
            and row.get("私有OCR文本SHA256") == manifest_row.get("私有OCR文本SHA256")
            and row.get("页面复核优先级") == page_row.get("页面复核优先级")
            and row.get("页面阻断等级") == page_row.get("页面阻断等级")
            and re.fullmatch(r"page-\d{3}", row.get("私有页图证据编号", "")) is not None
            and re.fullmatch(r"\d{3}_page-\d{3}", row.get("私有OCR文本证据编号", "")) is not None
            and re.fullmatch(r"[0-9a-f]{64}", row.get("私有页图SHA256", "")) is not None
            and re.fullmatch(r"[0-9a-f]{64}", row.get("私有OCR文本SHA256", "")) is not None
            and row.get("人工核验结论状态") == "pending_manual_field_review"
            and not row.get("人工确认值")
            and not row.get("人工证据编号")
            and not row.get("人工证据SHA256")
        )
    hubei_official_join_ok = True
    for row in hubei_official_rows:
        full_row = full_major_evidence_by_workbench_id.get(row.get("来源全量证据工作台ID"))
        task_row = full_major_hubei_task_by_major_id.get(row.get("专业行ID"))
        hubei_official_join_ok = (
            hubei_official_join_ok
            and bool(full_row)
            and bool(task_row)
            and row.get("湖北官方核验包任务ID")
            == stable_id("HBPLAN", [row.get("专业行ID", ""), row.get("来源证据闭环任务ID", "")])
            and row.get("来源证据闭环任务ID") == task_row.get("证据闭环任务ID")
            and row.get("数据阶段") == "issue19_hubei_official_plan_major_crosscheck_packets"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("任务粒度") == "逐专业招生明细×湖北官方系统核验"
            and row.get("最终可用") == "false"
            and row.get("是否可升级") == "false"
            and row.get("专业组出现ID") == full_row.get("专业组出现ID")
            and row.get("院校代码") == full_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化") == full_row.get("院校专业组代码OCR规范化")
            and row.get("专业代号OCR") == full_row.get("专业代号OCR")
            and row.get("OCR再选科目") == full_row.get("再选科目OCR候选")
            and row.get("OCR专业计划数") == full_row.get("专业计划数OCR候选")
            and row.get("OCR学费") == full_row.get("学费OCR候选")
            and row.get("平台查询院校代码") == full_row.get("院校代码")
            and row.get("平台查询专业组代码") == full_row.get("院校专业组代码OCR规范化")
            and row.get("平台查询专业代号") == full_row.get("专业代号OCR")
            and row.get("平台匹配状态") == "pending_hubei_official_platform_query"
            and row.get("平台字段核验状态") == "pending_hubei_official_plan_review"
            and not row.get("字段差异集合")
            and not row.get("官方系统证据编号")
            and not row.get("官方系统证据SHA256")
            and not row.get("公开原始行SHA256")
        )
    b0_b1_diff_join_ok = True
    for row in b0_b1_diff_rows:
        full_row = full_major_evidence_by_workbench_id.get(row.get("来源全量证据工作台ID"))
        b0_b1_diff_join_ok = (
            b0_b1_diff_join_ok
            and bool(full_row)
            and row.get("公开官网差异账ID") == stable_id("B0B1DIFF", [row.get("专业行ID", "")])
            and row.get("数据阶段") == "issue19_b0_b1_public_official_diff_ledger"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("专业行ID") == full_row.get("专业行ID")
            and row.get("专业组出现ID") == full_row.get("专业组出现ID")
            and row.get("院校代码") == full_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化") == full_row.get("院校专业组代码OCR规范化")
            and row.get("专业代号OCR") == full_row.get("专业代号OCR")
            and row.get("OCR计划数") == full_row.get("专业计划数OCR候选")
            and row.get("OCR学费") == full_row.get("学费OCR候选")
            and row.get("OCR再选科目") == full_row.get("再选科目OCR候选")
            and row.get("高校官网/章程辅证状态") == full_row.get("高校官网/章程辅证状态")
            and row.get("高校官网/章程辅证状态")
            != "not_yet_school_source_searched_in_full_workbench"
        )
    new_major_worktable_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            field_gap_summary_path,
            field_gap_csv,
            hubei_official_summary_path,
            hubei_official_csv,
            b0_b1_diff_summary_path,
            b0_b1_diff_csv,
        ]
    )
    checks.append(ok(
        "第 19 期字段缺口逐专业修复矩阵摘要、字段分布和行数正确",
        field_gap_summary.get("status") == "issue19_p1_field_gap_evidence_repair_matrix_not_final"
        and field_gap_summary.get("generated_by") == "build_issue19_major_level_evidence_worktables.py"
        and field_gap_summary.get("source_full_major_field_fidelity_ledger")
        == "data/working/issue19-full-major-field-fidelity-ledger.csv"
        and field_gap_summary.get("output_table")
        == "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv"
        and field_gap_summary.get("row_count") == 19065
        and field_gap_summary.get("unique_task_id_count") == 19065
        and field_gap_summary.get("unique_major_line_id_count") == 12473
        and field_gap_summary.get("unique_pdf_page_count") == 231
        and field_gap_summary.get("field_counts") == {
            "再选科目": 11456,
            "专业计划数": 6347,
            "学费": 1262,
        }
        and field_gap_summary.get("final_available_count") == 0
        and field_gap_summary.get("next_stage_allowed_count") == 0
        and len(field_gap_rows) == 19065,
        f"{len(field_gap_rows)} field gap rows",
    ))
    checks.append(ok(
        "第 19 期字段缺口逐专业修复矩阵字段、主键和来源闭环正确",
        required_field_gap_fields.issubset(field_gap_fields)
        and len({row.get("字段补证任务ID") for row in field_gap_rows}) == len(field_gap_rows)
        and Counter(row.get("字段名") for row in field_gap_rows)
        == Counter(field_gap_summary.get("field_counts", {}))
        and {row.get("专业行ID") for row in field_gap_rows}.issubset(full_major_evidence_ids)
        and field_gap_join_ok,
    ))
    checks.append(ok(
        "第 19 期湖北官方计划逐专业核验包摘要、字段和来源闭环正确",
        hubei_official_summary.get("status") == "issue19_hubei_official_plan_major_crosscheck_packets_not_final"
        and hubei_official_summary.get("generated_by") == "build_issue19_major_level_evidence_worktables.py"
        and hubei_official_summary.get("output_table")
        == "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"
        and hubei_official_summary.get("row_count") == 13736
        and hubei_official_summary.get("unique_task_id_count") == 13736
        and hubei_official_summary.get("unique_major_line_id_count") == 13736
        and hubei_official_summary.get("unique_source_closure_task_id_count") == 13736
        and hubei_official_summary.get("platform_status_counts")
        == {"pending_hubei_official_plan_review": 13736}
        and hubei_official_summary.get("final_available_count") == 0
        and hubei_official_summary.get("auto_upgrade_allowed_count") == 0
        and required_hubei_official_fields.issubset(hubei_official_fields)
        and len({row.get("湖北官方核验包任务ID") for row in hubei_official_rows})
        == len(hubei_official_rows)
        and {row.get("专业行ID") for row in hubei_official_rows} == full_major_evidence_ids
        and hubei_official_join_ok
        and len(hubei_official_rows) == 13736,
        f"{len(hubei_official_rows)} hubei official rows",
    ))
    checks.append(ok(
        "第 19 期 B0/B1 逐专业官网差异账摘要、字段和来源闭环正确",
        b0_b1_diff_summary.get("status") == "issue19_b0_b1_public_official_diff_ledger_not_final"
        and b0_b1_diff_summary.get("generated_by") == "build_issue19_major_level_evidence_worktables.py"
        and b0_b1_diff_summary.get("output_table")
        == "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
        and b0_b1_diff_summary.get("row_count") == 854
        and b0_b1_diff_summary.get("unique_diff_id_count") == 854
        and b0_b1_diff_summary.get("unique_major_line_id_count") == 854
        and b0_b1_diff_summary.get("school_source_status_counts") == {
            "has_partial_source_needs_followup": 412,
            "has_reusable_2026_hubei_plan_source": 194,
            "官网专业名匹配但计划数冲突-优先核页": 18,
            "charter_or_rules_only_no_plan": 63,
            "needs_official_plan_source_search": 167,
        }
        and b0_b1_diff_summary.get("match_status_counts") == {
            "": 533,
            "no_school_source": 137,
            "matched": 152,
            "unmatched": 31,
            "possible_match": 1,
        }
        and b0_b1_diff_summary.get("plan_conflict_count") == 18
        and b0_b1_diff_summary.get("unmatched_major_count") == 28
        and b0_b1_diff_summary.get("source_match_hit_count") == 153
        and b0_b1_diff_summary.get("final_available_count") == 0
        and b0_b1_diff_summary.get("next_stage_allowed_count") == 0
        and required_b0_b1_diff_fields.issubset(b0_b1_diff_fields)
        and len({row.get("公开官网差异账ID") for row in b0_b1_diff_rows}) == len(b0_b1_diff_rows)
        and Counter(row.get("高校官网/章程辅证状态") for row in b0_b1_diff_rows)
        == Counter(b0_b1_diff_summary.get("school_source_status_counts", {}))
        and b0_b1_diff_join_ok
        and len(b0_b1_diff_rows) == 854,
        f"{len(b0_b1_diff_rows)} b0/b1 diff rows",
    ))
    checks.append(ok(
        "第 19 期新增逐专业保真工作表公开文件不含本地路径、图片扩展名、身份信息、登录态和最终建议结论",
        "private/" not in new_major_worktable_public_text
        and "private\\" not in new_major_worktable_public_text
        and "/Users/" not in new_major_worktable_public_text
        and "ocr-runs" not in new_major_worktable_public_text
        and "rendered-pages" not in new_major_worktable_public_text
        and ".png" not in new_major_worktable_public_text
        and ".jpg" not in new_major_worktable_public_text
        and ".jpeg" not in new_major_worktable_public_text
        and "Authorization" not in new_major_worktable_public_text
        and "Bearer " not in new_major_worktable_public_text
        and "Cookie" not in new_major_worktable_public_text
        and "Admin-Token" not in new_major_worktable_public_text
        and "HUBEI_PLAN_TOKEN" not in new_major_worktable_public_text
        and "final_allowed" not in new_major_worktable_public_text
        and "ready_for_discussion" not in new_major_worktable_public_text
        and "已确认" not in new_major_worktable_public_text
        and "已核准" not in new_major_worktable_public_text
        and "最终推荐" not in new_major_worktable_public_text
        and "最终方案" not in new_major_worktable_public_text
        and "可填报" not in new_major_worktable_public_text
        and "可排序" not in new_major_worktable_public_text
        and not any(token in new_major_worktable_public_text for token in shared_forbidden_tokens),
    ))

    foundation_release_summary_path = (
        ROOT / "data/working/issue19-major-detail-foundation-release-summary.json"
    )
    foundation_release_csv = ROOT / "data/working/issue19-major-detail-foundation-release.csv"
    foundation_release_summary = json.loads(foundation_release_summary_path.read_text())
    with foundation_release_csv.open(newline="", encoding="utf-8-sig") as f:
        foundation_release_reader = csv.DictReader(f)
        foundation_release_rows = list(foundation_release_reader)
        foundation_release_fields = set(foundation_release_reader.fieldnames or [])
    required_foundation_release_fields = {
        "底座发布明细ID",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "底座发布状态",
        "核验状态",
        "最终可用",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "最终志愿排序门禁",
        "不得进入原因",
        "底座使用边界",
        "底座保真门禁",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业名称及备注短摘",
        "是否真实招生明细",
        "是否0明细占位",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "再选科目人工确认",
        "专业计划数人工确认",
        "学费人工确认",
        "字段缺口数",
        "字段缺口字段",
        "再选科目字段缺口",
        "专业计划数字段缺口",
        "学费字段缺口",
        "P0复核任务数",
        "P0证据项",
        "湖北官方核验包任务ID",
        "湖北官方平台匹配状态",
        "湖北官方平台字段核验状态",
        "湖北官方字段差异集合",
        "湖北官方系统证据状态",
        "湖北官方系统字段核验状态",
        "高校官网/章程辅证状态",
        "高校官网来源状态",
        "高校官网证据匹配状态",
        "高校官网计划数核验状态",
        "高校官网差异字段集合",
        "B0B1官网差异任务数",
        "PDF原页证据状态",
        "PDF字段核验状态",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "页级保真队列ID",
        "页级复核优先级",
        "页级阻断等级",
        "页级OCR平均置信度",
        "页级OCR_QC_P0数",
        "页级OCR_QC_P1数",
        "家庭接受度核验状态",
        "家庭接受度结论",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "调剂影响初判",
        "调剂影响等级",
        "同组调剂结论",
        "组机器家庭匹配初判",
        "组调剂初判",
        "同组真实招生明细数",
        "同组偏好专业数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "专业偏好方向",
        "专业风险类型",
        "全量证据执行优先级",
        "全量保真复核优先级",
        "风险阻断等级",
        "高风险字段集合",
        "风险触发规则",
        "证据缺口",
        "执行必须核验字段",
        "三年投档线索",
        "三年投档稳定性状态",
        "下一步",
    }
    full_major_evidence_by_major_id = {
        row.get("专业行ID"): row for row in full_major_evidence_rows
    }
    hubei_official_by_major_id = {
        row.get("专业行ID"): row for row in hubei_official_rows
    }
    p0_review_by_major_id = defaultdict(list)
    for row in p0_review_rows:
        p0_review_by_major_id[row.get("专业行ID")].append(row)
    field_gap_by_major_id = defaultdict(list)
    for row in field_gap_rows:
        field_gap_by_major_id[row.get("专业行ID")].append(row)
    b0_b1_diff_by_major_id = defaultdict(list)
    for row in b0_b1_diff_rows:
        b0_b1_diff_by_major_id[row.get("专业行ID")].append(row)
    foundation_release_join_ok = True
    for row in foundation_release_rows:
        major_id = row.get("专业行ID")
        full_row = full_major_evidence_by_major_id.get(major_id, {})
        hubei_row = hubei_official_by_major_id.get(major_id, {})
        p0_rows = p0_review_by_major_id.get(major_id, [])
        gap_rows = field_gap_by_major_id.get(major_id, [])
        diff_rows = b0_b1_diff_by_major_id.get(major_id, [])
        manifest_row = page_manifest_by_page.get(as_int(row.get("来源页码")))
        page_row = page_fidelity_by_page.get(as_int(row.get("来源页码")))
        gap_fields = {gap_row.get("字段名") for gap_row in gap_rows if gap_row.get("字段名")}
        p0_items = {p0_row.get("证据项") for p0_row in p0_rows if p0_row.get("证据项")}
        diff_source_statuses = {
            diff_row.get("官网来源状态") for diff_row in diff_rows if diff_row.get("官网来源状态")
        }
        diff_match_statuses = {
            diff_row.get("官网证据匹配状态") for diff_row in diff_rows if diff_row.get("官网证据匹配状态")
        }
        diff_plan_statuses = {
            diff_row.get("计划数核验状态") for diff_row in diff_rows if diff_row.get("计划数核验状态")
        }
        diff_fields = {
            diff_row.get("差异字段集合") for diff_row in diff_rows if diff_row.get("差异字段集合")
        }
        diff_fields_text = "；".join(dict.fromkeys(
            diff_row.get("差异字段集合")
            for diff_row in diff_rows
            if diff_row.get("差异字段集合")
        ))
        foundation_release_join_ok = (
            foundation_release_join_ok
            and bool(full_row)
            and bool(hubei_row)
            and bool(manifest_row)
            and bool(page_row)
            and row.get("底座发布明细ID") == stable_id("BASEMAJOR", [major_id])
            and row.get("数据阶段") == "issue19_major_detail_foundation_release"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("底座发布状态") == "公开底座待核验"
            and row.get("核验状态") == "pending_foundation_release_verification"
            and row.get("最终可用") == "false"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("最终志愿排序门禁") == "阻断-待证据闭环"
            and "湖北官方平台字段核验状态仍为pending_hubei_official_plan_review"
            in row.get("不得进入原因", "")
            and row.get("专业组出现ID") == full_row.get("专业组出现ID")
            and row.get("院校代码") == full_row.get("院校代码")
            and row.get("院校名称OCR") == full_row.get("院校名称OCR")
            and row.get("院校专业组代码OCR规范化")
            == full_row.get("院校专业组代码OCR规范化")
            and row.get("专业代号OCR") == full_row.get("专业代号OCR")
            and row.get("专业名称及备注OCR") == full_row.get("专业名称及备注OCR")
            and row.get("再选科目OCR候选") == full_row.get("再选科目OCR候选")
            and row.get("专业计划数OCR候选") == full_row.get("专业计划数OCR候选")
            and row.get("学费OCR候选") == full_row.get("学费OCR候选")
            and row.get("是否真实招生明细")
            == ("true" if full_row.get("专业名称及备注OCR", "").strip() else "false")
            and row.get("是否0明细占位") == "false"
            and not row.get("再选科目人工确认")
            and not row.get("专业计划数人工确认")
            and not row.get("学费人工确认")
            and row.get("字段缺口数") == str(len(gap_rows))
            and set(split_cn_semicolon(row.get("字段缺口字段"))) == gap_fields
            and row.get("再选科目字段缺口") == ("true" if "再选科目" in gap_fields else "false")
            and row.get("专业计划数字段缺口") == ("true" if "专业计划数" in gap_fields else "false")
            and row.get("学费字段缺口") == ("true" if "学费" in gap_fields else "false")
            and row.get("P0复核任务数") == str(len(p0_rows))
            and set(split_cn_semicolon(row.get("P0证据项"))) == p0_items
            and row.get("湖北官方核验包任务ID") == hubei_row.get("湖北官方核验包任务ID")
            and row.get("湖北官方平台匹配状态") == hubei_row.get("平台匹配状态")
            and row.get("湖北官方平台字段核验状态") == hubei_row.get("平台字段核验状态")
            and row.get("湖北官方平台字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("湖北官方系统证据状态") == full_row.get("湖北官方系统证据状态")
            and row.get("湖北官方系统字段核验状态") == full_row.get("湖北官方系统字段核验状态")
            and row.get("高校官网/章程辅证状态") == full_row.get("高校官网/章程辅证状态")
            and (
                set(split_cn_semicolon(row.get("高校官网来源状态"))) == diff_source_statuses
                or row.get("高校官网来源状态") == full_row.get("高校官网/章程辅证状态")
            )
            and set(split_cn_semicolon(row.get("高校官网证据匹配状态"))) == diff_match_statuses
            and (
                set(split_cn_semicolon(row.get("高校官网计划数核验状态"))) == diff_plan_statuses
                or row.get("高校官网计划数核验状态") == full_row.get("计划数核验状态")
            )
            and row.get("高校官网差异字段集合") == diff_fields_text
            and row.get("B0B1官网差异任务数") == str(len(diff_rows))
            and row.get("PDF原页证据状态") == full_row.get("PDF原页证据状态")
            and row.get("PDF字段核验状态") == full_row.get("PDF字段核验状态")
            and row.get("私有页图证据编号") == manifest_row.get("私有页图证据编号")
            and row.get("私有页图SHA256") == manifest_row.get("私有页图SHA256")
            and row.get("私有OCR文本证据编号") == manifest_row.get("私有OCR文本证据编号")
            and row.get("私有OCR文本SHA256") == manifest_row.get("私有OCR文本SHA256")
            and row.get("页级保真队列ID") == full_row.get("页级保真队列ID")
            and row.get("页级复核优先级") == full_row.get("页级复核优先级")
            and row.get("页级阻断等级") == full_row.get("页级阻断等级")
            and row.get("家庭接受度核验状态") == full_row.get("家庭接受度核验状态")
            and row.get("家庭接受度结论") == "pending_family_acceptance_review"
            and row.get("同组调剂结论") == "pending_transfer_decision"
            and row.get("全量证据执行优先级") == full_row.get("全量证据执行优先级")
            and row.get("全量保真复核优先级") == full_row.get("全量保真复核优先级")
            and row.get("风险阻断等级") == full_row.get("风险阻断等级")
            and row.get("证据缺口") == full_row.get("证据缺口")
            and row.get("执行必须核验字段") == full_row.get("执行必须核验字段")
        )
    foundation_release_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [foundation_release_summary_path, foundation_release_csv]
    )
    foundation_release_sensitive_re = re.compile(
        r"/Users/|C:\\Users\\|C:/Users/|/private/|/var/folders/|private/|private\\|"
        r"ocr-runs|rendered-pages|"
        r"\.(?:png|jpg|jpeg|webp|gif|heic|tiff|bmp)\b|"
        r"Authorization|Bearer\s|Cookie|Set-Cookie|Admin-Token|"
        r"HUBEI_PLAN_TOKEN|HUBEI_PLAN_AUTH_TOKEN|token=|"
        r"身份证|准考证|报名号|序列号|手机号|联系电话|通知书地址|"
        r"考生姓名|姓名[:：,，\t ]|微信号|WeChat ID|wxid_[A-Za-z0-9_-]+|"
        r"考生号|账号密码|登录密码",
        re.IGNORECASE,
    )
    checks.append(ok(
        "第 19 期统一逐专业底座发布表摘要、行数和门禁统计正确",
        foundation_release_summary.get("status") == "issue19_major_detail_foundation_release_not_final"
        and foundation_release_summary.get("generated_by")
        == "build_issue19_major_detail_foundation_release.py"
        and foundation_release_summary.get("source_full_major_evidence_workbench")
        == "data/working/issue19-full-major-evidence-workbench.csv"
        and foundation_release_summary.get("output_table")
        == "data/working/issue19-major-detail-foundation-release.csv"
        and foundation_release_summary.get("row_count") == 13736
        and foundation_release_summary.get("unique_release_id_count") == 13736
        and foundation_release_summary.get("unique_major_line_id_count") == 13736
        and foundation_release_summary.get("unique_group_occurrence_id_count") == 3289
        and foundation_release_summary.get("unique_school_count") == 1100
        and foundation_release_summary.get("unique_pdf_page_count") == 231
        and foundation_release_summary.get("p0_task_row_count") == 6619
        and foundation_release_summary.get("p0_major_line_count") == 5310
        and foundation_release_summary.get("field_gap_task_row_count") == 19065
        and foundation_release_summary.get("field_gap_major_line_count") == 12473
        and foundation_release_summary.get("field_gap_field_counts") == {
            "再选科目": 11456,
            "专业计划数": 6347,
            "学费": 1262,
        }
        and foundation_release_summary.get("hubei_official_packet_row_count") == 13736
        and foundation_release_summary.get("hubei_official_major_line_count") == 13736
        and foundation_release_summary.get("b0_b1_diff_row_count") == 854
        and foundation_release_summary.get("b0_b1_diff_major_line_count") == 854
        and foundation_release_summary.get("release_gate_counts") == {
            "G0-P0证据先核": 5310,
            "G1-字段缺口先补": 7608,
            "G3-常规三方证据闭环": 609,
            "G4-低风险抽检仍待三方核验": 209,
        }
        and foundation_release_summary.get("official_platform_status_counts")
        == {"pending_hubei_official_plan_review": 13736}
        and foundation_release_summary.get("missing_subject_count") == 11456
        and foundation_release_summary.get("missing_plan_count") == 5739
        and foundation_release_summary.get("missing_tuition_count") == 1040
        and foundation_release_summary.get("real_major_detail_count") == 13734
        and foundation_release_summary.get("zero_detail_placeholder_count") == 0
        and foundation_release_summary.get("final_available_count") == 0
        and foundation_release_summary.get("final_major_list_candidate_count") == 0
        and foundation_release_summary.get("next_stage_allowed_count") == 0
        and foundation_release_summary.get("final_sort_gate_open_count") == 0
        and len(foundation_release_rows) == 13736,
        f"{len(foundation_release_rows)} foundation release rows",
    ))
    checks.append(ok(
        "第 19 期统一逐专业底座发布表字段、主键和来源闭环正确",
        required_foundation_release_fields.issubset(foundation_release_fields)
        and len(foundation_release_fields) == 90
        and len({row.get("底座发布明细ID") for row in foundation_release_rows})
        == len(foundation_release_rows)
        and {row.get("专业行ID") for row in foundation_release_rows} == full_major_evidence_ids
        and Counter(row.get("底座保真门禁") for row in foundation_release_rows)
        == Counter(foundation_release_summary.get("release_gate_counts", {}))
        and Counter(row.get("湖北官方平台字段核验状态") for row in foundation_release_rows)
        == Counter(foundation_release_summary.get("official_platform_status_counts", {}))
        and sum(not row.get("再选科目OCR候选") for row in foundation_release_rows) == 11456
        and sum(not row.get("专业计划数OCR候选") for row in foundation_release_rows) == 5739
        and sum(not row.get("学费OCR候选") for row in foundation_release_rows) == 1040
        and foundation_release_join_ok,
    ))
    checks.append(ok(
        "第 19 期统一逐专业底座发布表公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(foundation_release_public_text) is None
        and "final_allowed" not in foundation_release_public_text
        and "ready_for_discussion" not in foundation_release_public_text
        and "已确认" not in foundation_release_public_text
        and "已核准" not in foundation_release_public_text
        and "最终推荐" not in foundation_release_public_text
        and "最终方案" not in foundation_release_public_text
        and "可填报" not in foundation_release_public_text
        and "可排序" not in foundation_release_public_text,
    ))

    closure_summary_path = ROOT / "data/working/issue19-foundation-closure-batches-summary.json"
    closure_major_csv = ROOT / "data/working/issue19-foundation-closure-major-batches.csv"
    closure_page_csv = ROOT / "data/working/issue19-foundation-closure-page-index.csv"
    closure_school_csv = ROOT / "data/working/issue19-foundation-closure-school-index.csv"
    closure_summary = json.loads(closure_summary_path.read_text())
    with closure_major_csv.open(newline="", encoding="utf-8-sig") as f:
        closure_major_reader = csv.DictReader(f)
        closure_major_rows = list(closure_major_reader)
        closure_major_fields = closure_major_reader.fieldnames or []
    with closure_page_csv.open(newline="", encoding="utf-8-sig") as f:
        closure_page_reader = csv.DictReader(f)
        closure_page_rows = list(closure_page_reader)
        closure_page_fields = closure_page_reader.fieldnames or []
    with closure_school_csv.open(newline="", encoding="utf-8-sig") as f:
        closure_school_reader = csv.DictReader(f)
        closure_school_rows = list(closure_school_reader)
        closure_school_fields = closure_school_reader.fieldnames or []
    expected_closure_major_fields = [
        "底座闭环批次ID",
        "来源统一逐专业底座入口",
        "来源底座发布明细ID",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "闭环任务状态",
        "闭环执行总序",
        "闭环执行批次",
        "闭环执行动作集合",
        "首要核验动作",
        "闭环执行排序分",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "字段缺口数",
        "字段缺口字段",
        "P0复核任务数",
        "P0证据项",
        "湖北官方平台字段核验状态",
        "高校官网来源状态",
        "高校官网证据匹配状态",
        "高校官网计划数核验状态",
        "高校官网差异字段集合",
        "B0B1官网差异任务数",
        "页级保真队列ID",
        "页级复核优先级",
        "页级阻断等级",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "家庭接受度结论",
        "同组调剂结论",
        "机器专业接受度初判",
        "调剂影响等级",
        "同组真实招生明细数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "专业偏好方向",
        "风险阻断等级",
        "三年投档稳定性状态",
        "不得进入原因",
        "下一步",
    ]
    expected_closure_page_fields = [
        "页级闭环索引ID",
        "来源逐专业闭环批次表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "索引粒度",
        "最终可用",
        "可进入下一阶段",
        "PDF页码",
        "页级执行总序",
        "页面专业明细数",
        "涉及院校数",
        "涉及专业组数",
        "C0_P0主批次专业明细数",
        "C1字段缺口主批次专业明细数",
        "C2官网辅证主批次专业明细数",
        "C3常规三方主批次专业明细数",
        "C4低风险抽检主批次专业明细数",
        "含官网辅证任务专业明细数",
        "B0B1官网差异专业明细数",
        "有高校官网来源线索专业明细数",
        "偏好专业明细数",
        "数字媒体技术专业明细数",
        "计算机类相关专业明细数",
        "师范类相关专业明细数",
        "字段缺口字段Top",
        "首个专业行ID",
        "首个院校代码",
        "首个院校名称OCR",
        "首要核验动作",
        "下一步",
    ]
    expected_closure_school_fields = [
        "学校闭环索引ID",
        "来源逐专业闭环批次表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "索引粒度",
        "最终可用",
        "可进入下一阶段",
        "院校代码",
        "院校名称OCR",
        "学校执行总序",
        "专业明细数",
        "涉及PDF页数",
        "涉及专业组数",
        "C0_P0主批次专业明细数",
        "C1字段缺口主批次专业明细数",
        "C2官网辅证主批次专业明细数",
        "C3常规三方主批次专业明细数",
        "C4低风险抽检主批次专业明细数",
        "含官网辅证任务专业明细数",
        "B0B1官网差异专业明细数",
        "有高校官网来源线索专业明细数",
        "偏好专业明细数",
        "高校官网来源状态分布",
        "首个PDF页码",
        "首个专业行ID",
        "首要核验动作",
        "下一步",
    ]
    foundation_release_by_major_id = {
        row.get("专业行ID"): row for row in foundation_release_rows
    }

    def int0(value):
        return as_int(value) or 0

    def closure_has_school_source(release_row):
        status = release_row.get("高校官网来源状态", "")
        return bool(status) and status != "not_yet_school_source_searched_in_full_workbench"

    def closure_has_historical_line(release_row):
        status = release_row.get("三年投档稳定性状态", "")
        return bool(status) and "未命中" not in status

    def closure_has_b0_b1_diff(release_row):
        return int0(release_row.get("B0B1官网差异任务数")) > 0

    def closure_has_official_auxiliary_task(release_row):
        return closure_has_b0_b1_diff(release_row) or closure_has_school_source(release_row)

    def closure_join_unique(values):
        seen = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in seen:
                seen.append(text)
        return "；".join(seen)

    def expected_closure_batch(release_row):
        if int0(release_row.get("P0复核任务数")) > 0:
            return "C0-P0证据闭环先核"
        if int0(release_row.get("字段缺口数")) > 0:
            return "C1-字段缺口先补"
        if closure_has_official_auxiliary_task(release_row):
            return "C2-官网辅证交叉核验"
        if release_row.get("底座保真门禁", "").startswith("G4"):
            return "C4-低风险抽检但非最终"
        return "C3-常规三方证据闭环"

    def expected_closure_actions(release_row):
        actions = ["湖北官方系统/省招办计划核验", "家庭接受度核验", "同组调剂结论核验"]
        if int0(release_row.get("P0复核任务数")) > 0:
            actions.insert(0, "P0-PDF原页或三方证据先核")
        else:
            actions.insert(0, "PDF原页常规核验")
        if int0(release_row.get("字段缺口数")) > 0:
            actions.append("P1-字段缺口补证")
        if closure_has_official_auxiliary_task(release_row):
            actions.append("高校官网/章程辅证交叉")
        if closure_has_historical_line(release_row):
            actions.append("三年投档稳定性复核")
        return closure_join_unique(actions)

    def expected_closure_primary_action(release_row):
        batch = expected_closure_batch(release_row)
        if batch.startswith("C0"):
            return "回看PDF原页并同步补湖北官方系统/高校官网证据"
        if batch.startswith("C1"):
            return f"补字段缺口：{release_row.get('字段缺口字段') or '待识别字段'}"
        if batch.startswith("C2"):
            return "用高校官网/章程辅证和湖北官方系统逐字段交叉"
        if batch.startswith("C4"):
            return "抽检PDF原页和湖北官方系统，确认低风险行没有漏判"
        return "完成PDF原页、湖北官方系统、高校官网/章程、家庭接受度和调剂结论闭环"

    def expected_closure_priority_score(release_row):
        base_by_batch = {
            "C0-P0证据闭环先核": 100000,
            "C1-字段缺口先补": 200000,
            "C2-官网辅证交叉核验": 300000,
            "C3-常规三方证据闭环": 400000,
            "C4-低风险抽检但非最终": 500000,
        }
        score = base_by_batch[expected_closure_batch(release_row)]
        page_priority = release_row.get("页级复核优先级", "")
        if page_priority.startswith("P0"):
            score -= 5000
        elif page_priority.startswith("P1"):
            score -= 2500
        preference = release_row.get("专业偏好方向", "")
        if "数字媒体技术" in preference:
            score -= 900
        if "计算机类相关" in preference:
            score -= 700
        if "师范类相关" in preference:
            score -= 500
        if closure_has_school_source(release_row):
            score -= 250
        if closure_has_historical_line(release_row):
            score -= 100
        score += int0(release_row.get("来源页码"))
        score += min(int0(release_row.get("专业组内专业序号")), 99)
        return score

    def expected_closure_sort_key(release_row):
        return (
            expected_closure_priority_score(release_row),
            int0(release_row.get("来源页码")),
            release_row.get("院校代码", ""),
            release_row.get("院校专业组代码OCR规范化", ""),
            int0(release_row.get("专业组内专业序号")),
            release_row.get("专业行ID", ""),
        )

    expected_sorted_release_rows = sorted(foundation_release_rows, key=expected_closure_sort_key)
    direct_release_fields = [
        "来源期号",
        "来源PDF_SHA256",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "字段缺口数",
        "字段缺口字段",
        "P0复核任务数",
        "P0证据项",
        "湖北官方平台字段核验状态",
        "高校官网来源状态",
        "高校官网证据匹配状态",
        "高校官网计划数核验状态",
        "高校官网差异字段集合",
        "B0B1官网差异任务数",
        "页级保真队列ID",
        "页级复核优先级",
        "页级阻断等级",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "家庭接受度结论",
        "同组调剂结论",
        "机器专业接受度初判",
        "调剂影响等级",
        "同组真实招生明细数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "专业偏好方向",
        "风险阻断等级",
        "三年投档稳定性状态",
        "不得进入原因",
        "下一步",
    ]
    closure_major_join_ok = True
    for index, row in enumerate(closure_major_rows, start=1):
        release_row = foundation_release_by_major_id.get(row.get("专业行ID"), {})
        expected_release_row = (
            expected_sorted_release_rows[index - 1]
            if index <= len(expected_sorted_release_rows)
            else {}
        )
        order = int0(row.get("闭环执行总序"))
        score = int0(row.get("闭环执行排序分"))
        expected_score = expected_closure_priority_score(release_row) if release_row else -1
        direct_release_fields_ok = all(
            row.get(field) == release_row.get(field) for field in direct_release_fields
        )
        closure_major_join_ok = (
            closure_major_join_ok
            and bool(release_row)
            and bool(expected_release_row)
            and row.get("专业行ID") == expected_release_row.get("专业行ID")
            and row.get("底座闭环批次ID") == stable_id("CLOSEMAJOR", [row.get("专业行ID", "")])
            and row.get("来源统一逐专业底座入口")
            == "data/working/issue19-major-detail-foundation-release.csv"
            and row.get("来源底座发布明细ID") == release_row.get("底座发布明细ID")
            and row.get("数据阶段") == "issue19_foundation_closure_batches"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("是否可进入最终专业列表") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("闭环任务状态") == "pending_foundation_closure"
            and order == index
            and score == expected_score
            and row.get("闭环执行批次") == expected_closure_batch(release_row)
            and row.get("闭环执行动作集合") == expected_closure_actions(release_row)
            and row.get("首要核验动作") == expected_closure_primary_action(release_row)
            and row.get("湖北官方平台字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("家庭接受度结论") == "pending_family_acceptance_review"
            and row.get("同组调剂结论") == "pending_transfer_decision"
            and direct_release_fields_ok
        )
    closure_by_page = defaultdict(list)
    closure_by_school = defaultdict(list)
    for row in closure_major_rows:
        closure_by_page[row.get("来源页码")].append(row)
        closure_by_school[row.get("院校代码")].append(row)

    def count_batch(rows, batch):
        return sum(row.get("闭环执行批次") == batch for row in rows)

    closure_page_index_ok = True
    for row in closure_page_rows:
        rows = closure_by_page.get(row.get("PDF页码"), [])
        first = min(rows, key=lambda item: as_int(item.get("闭环执行总序"))) if rows else {}
        closure_page_index_ok = (
            closure_page_index_ok
            and bool(rows)
            and row.get("页级闭环索引ID") == stable_id("CLOSEPAGE", [row.get("PDF页码", "")])
            and row.get("来源逐专业闭环批次表")
            == "data/working/issue19-foundation-closure-major-batches.csv"
            and row.get("数据阶段") == "issue19_foundation_closure_page_index"
            and row.get("索引粒度") == "PDF页码"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and int0(row.get("页级执行总序")) == min(int0(item.get("闭环执行总序")) for item in rows)
            and int0(row.get("页面专业明细数")) == len(rows)
            and int0(row.get("涉及院校数")) == len({item.get("院校代码") for item in rows})
            and int0(row.get("涉及专业组数")) == len({item.get("专业组出现ID") for item in rows})
            and int0(row.get("C0_P0主批次专业明细数")) == count_batch(rows, "C0-P0证据闭环先核")
            and int0(row.get("C1字段缺口主批次专业明细数")) == count_batch(rows, "C1-字段缺口先补")
            and int0(row.get("C2官网辅证主批次专业明细数")) == count_batch(rows, "C2-官网辅证交叉核验")
            and int0(row.get("C3常规三方主批次专业明细数")) == count_batch(rows, "C3-常规三方证据闭环")
            and int0(row.get("C4低风险抽检主批次专业明细数")) == count_batch(rows, "C4-低风险抽检但非最终")
            and int0(row.get("含官网辅证任务专业明细数"))
            == sum(closure_has_official_auxiliary_task(item) for item in rows)
            and int0(row.get("B0B1官网差异专业明细数"))
            == sum(closure_has_b0_b1_diff(item) for item in rows)
            and int0(row.get("有高校官网来源线索专业明细数"))
            == sum(closure_has_school_source(item) for item in rows)
            and int0(row.get("偏好专业明细数")) == sum(bool(item.get("专业偏好方向")) for item in rows)
            and int0(row.get("数字媒体技术专业明细数"))
            == sum("数字媒体技术" in item.get("专业偏好方向", "") for item in rows)
            and int0(row.get("计算机类相关专业明细数"))
            == sum("计算机类相关" in item.get("专业偏好方向", "") for item in rows)
            and int0(row.get("师范类相关专业明细数"))
            == sum("师范类相关" in item.get("专业偏好方向", "") for item in rows)
            and row.get("首个专业行ID") == first.get("专业行ID")
            and row.get("首个院校代码") == first.get("院校代码")
            and row.get("首个院校名称OCR") == first.get("院校名称OCR")
            and row.get("首要核验动作") == first.get("首要核验动作")
            and "不得替代逐专业明细" in row.get("下一步", "")
        )

    closure_school_index_ok = True
    for row in closure_school_rows:
        rows = closure_by_school.get(row.get("院校代码"), [])
        first = min(rows, key=lambda item: as_int(item.get("闭环执行总序"))) if rows else {}
        closure_school_index_ok = (
            closure_school_index_ok
            and bool(rows)
            and row.get("学校闭环索引ID") == stable_id("CLOSESCHOOL", [row.get("院校代码", "")])
            and row.get("来源逐专业闭环批次表")
            == "data/working/issue19-foundation-closure-major-batches.csv"
            and row.get("数据阶段") == "issue19_foundation_closure_school_index"
            and row.get("索引粒度") == "院校"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and int0(row.get("学校执行总序")) == min(int0(item.get("闭环执行总序")) for item in rows)
            and int0(row.get("专业明细数")) == len(rows)
            and int0(row.get("涉及PDF页数")) == len({item.get("来源页码") for item in rows})
            and int0(row.get("涉及专业组数")) == len({item.get("专业组出现ID") for item in rows})
            and int0(row.get("C0_P0主批次专业明细数")) == count_batch(rows, "C0-P0证据闭环先核")
            and int0(row.get("C1字段缺口主批次专业明细数")) == count_batch(rows, "C1-字段缺口先补")
            and int0(row.get("C2官网辅证主批次专业明细数")) == count_batch(rows, "C2-官网辅证交叉核验")
            and int0(row.get("C3常规三方主批次专业明细数")) == count_batch(rows, "C3-常规三方证据闭环")
            and int0(row.get("C4低风险抽检主批次专业明细数")) == count_batch(rows, "C4-低风险抽检但非最终")
            and int0(row.get("含官网辅证任务专业明细数"))
            == sum(closure_has_official_auxiliary_task(item) for item in rows)
            and int0(row.get("B0B1官网差异专业明细数"))
            == sum(closure_has_b0_b1_diff(item) for item in rows)
            and int0(row.get("有高校官网来源线索专业明细数"))
            == sum(closure_has_school_source(item) for item in rows)
            and int0(row.get("偏好专业明细数")) == sum(bool(item.get("专业偏好方向")) for item in rows)
            and row.get("首个专业行ID") == first.get("专业行ID")
            and row.get("首要核验动作") == first.get("首要核验动作")
            and "回到逐专业闭环批次表逐行核" in row.get("下一步", "")
        )

    closure_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [closure_summary_path, closure_major_csv, closure_page_csv, closure_school_csv]
    )
    checks.append(ok(
        "第 19 期底座闭环批次摘要和行数正确",
        closure_summary.get("status") == "issue19_foundation_closure_batches_not_final"
        and closure_summary.get("generated_by") == "build_issue19_foundation_closure_batches.py"
        and closure_summary.get("source_foundation_release")
        == "data/working/issue19-major-detail-foundation-release.csv"
        and closure_summary.get("output_major_batches")
        == "data/working/issue19-foundation-closure-major-batches.csv"
        and closure_summary.get("output_page_index")
        == "data/working/issue19-foundation-closure-page-index.csv"
        and closure_summary.get("output_school_index")
        == "data/working/issue19-foundation-closure-school-index.csv"
        and closure_summary.get("major_row_count") == 13736
        and closure_summary.get("unique_major_line_id_count") == 13736
        and closure_summary.get("unique_batch_id_count") == 13736
        and closure_summary.get("page_index_row_count") == 231
        and closure_summary.get("school_index_row_count") == 1100
        and closure_summary.get("closure_batch_counts") == {
            "C0-P0证据闭环先核": 5310,
            "C1-字段缺口先补": 7608,
            "C2-官网辅证交叉核验": 0,
            "C3-常规三方证据闭环": 609,
            "C4-低风险抽检但非最终": 209,
        }
        and closure_summary.get("field_gap_field_counts") == {
            "再选科目": 11456,
            "专业计划数": 6347,
            "学费": 1262,
        }
        and closure_summary.get("p0_major_line_count") == 5310
        and closure_summary.get("field_gap_major_line_count") == 12473
        and closure_summary.get("b0_b1_diff_major_line_count") == 854
        and closure_summary.get("school_source_major_line_count") == 854
        and closure_summary.get("official_auxiliary_task_major_line_count") == 854
        and closure_summary.get("preference_major_line_count") == 2499
        and closure_summary.get("digital_media_major_line_count") == 78
        and closure_summary.get("computer_major_line_count") == 1867
        and closure_summary.get("teacher_major_line_count") == 601
        and closure_summary.get("final_available_count") == 0
        and closure_summary.get("final_major_list_candidate_count") == 0
        and closure_summary.get("next_stage_allowed_count") == 0,
        f"{len(closure_major_rows)} major rows, {len(closure_page_rows)} page rows, {len(closure_school_rows)} school rows",
    ))
    checks.append(ok(
        "第 19 期底座闭环批次主表字段、主键和统一底座来源闭环正确",
        closure_major_fields == expected_closure_major_fields
        and len(closure_major_rows) == 13736
        and len({row.get("底座闭环批次ID") for row in closure_major_rows}) == 13736
        and {row.get("专业行ID") for row in closure_major_rows} == full_major_evidence_ids
        and Counter(row.get("闭环执行批次") for row in closure_major_rows)
        == Counter(closure_summary.get("closure_batch_counts", {}))
        and closure_major_join_ok,
    ))
    checks.append(ok(
        "第 19 期底座闭环页级和学校索引由逐专业主表重算一致",
        closure_page_fields == expected_closure_page_fields
        and closure_school_fields == expected_closure_school_fields
        and len(closure_page_rows) == 231
        and len(closure_school_rows) == 1100
        and closure_page_index_ok
        and closure_school_index_ok,
    ))
    checks.append(ok(
        "第 19 期底座闭环批次公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(closure_public_text) is None
        and "final_allowed" not in closure_public_text
        and "ready_for_discussion" not in closure_public_text
        and "已确认" not in closure_public_text
        and "已核准" not in closure_public_text
        and "最终推荐" not in closure_public_text
        and "最终方案" not in closure_public_text
        and "可填报" not in closure_public_text
        and "可排序" not in closure_public_text,
    ))

    field_gap_candidates_summary_path = ROOT / "data/working/issue19-field-gap-repair-candidates-summary.json"
    field_gap_candidates_csv = ROOT / "data/working/issue19-field-gap-repair-candidates.csv"
    field_gap_candidates_summary = json.loads(field_gap_candidates_summary_path.read_text())
    with field_gap_candidates_csv.open(newline="", encoding="utf-8-sig") as f:
        field_gap_candidates_reader = csv.DictReader(f)
        field_gap_candidate_rows = list(field_gap_candidates_reader)
        field_gap_candidate_fields = field_gap_candidates_reader.fieldnames or []
    expected_field_gap_candidate_fields = [
        "字段候选任务ID",
        "来源字段补证任务ID",
        "来源底座闭环批次ID",
        "来源统一逐专业底座入口",
        "来源字段缺口矩阵",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "候选可自动写回主表",
        "候选状态",
        "候选置信等级",
        "候选来源类型",
        "候选值",
        "候选证据说明",
        "必须人工核验原因",
        "闭环执行总序",
        "闭环执行批次",
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
        "字段名",
        "当前OCR候选值",
        "当前OCR数字候选",
        "字段问题类型",
        "组级OCR回连状态",
        "组级再选科目OCR候选",
        "组级再选科目规范候选",
        "高校官网计划数候选",
        "高校官网学费候选",
        "高校官网辅证状态",
        "计划数核验状态",
        "页级保真队列ID",
        "页面复核优先级",
        "页面阻断等级",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "下一步",
    ]
    field_gap_by_task_id = {
        row.get("字段补证任务ID"): row for row in field_gap_rows
    }
    closure_by_major_id = {
        row.get("专业行ID"): row for row in closure_major_rows
    }
    field_gap_candidate_join_ok = True
    for row in field_gap_candidate_rows:
        gap_row = field_gap_by_task_id.get(row.get("来源字段补证任务ID"), {})
        closure_row = closure_by_major_id.get(row.get("专业行ID"), {})
        field_gap_candidate_join_ok = (
            field_gap_candidate_join_ok
            and bool(gap_row)
            and bool(closure_row)
            and row.get("字段候选任务ID")
            == stable_id("GAPCAND", [row.get("来源字段补证任务ID", ""), row.get("字段名", "")])
            and row.get("来源底座闭环批次ID") == closure_row.get("底座闭环批次ID")
            and row.get("来源统一逐专业底座入口")
            == "data/working/issue19-foundation-closure-major-batches.csv"
            and row.get("来源字段缺口矩阵")
            == "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv"
            and row.get("数据阶段") == "issue19_field_gap_repair_candidates"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("任务粒度") == "逐专业招生明细×字段缺口×候选修复"
            and row.get("最终可用") == "false"
            and row.get("候选可自动写回主表") == "false"
            and row.get("专业行ID") == gap_row.get("专业行ID")
            and row.get("专业组出现ID") == gap_row.get("专业组出现ID")
            and row.get("院校代码") == gap_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化") == gap_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == gap_row.get("来源页码")
            and row.get("版面列") == gap_row.get("版面列")
            and row.get("专业组内专业序号") == gap_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == gap_row.get("专业代号OCR")
            and row.get("字段名") == gap_row.get("字段名")
            and row.get("当前OCR候选值") == gap_row.get("OCR候选值")
            and row.get("字段问题类型") == gap_row.get("字段问题类型")
            and row.get("闭环执行总序") == closure_row.get("闭环执行总序")
            and row.get("闭环执行批次") == closure_row.get("闭环执行批次")
            and row.get("候选置信等级") in {"none", "low", "medium"}
            and "不得写回最终志愿表" in row.get("下一步", "")
        )
    field_gap_candidates_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [field_gap_candidates_summary_path, field_gap_candidates_csv]
    )
    checks.append(ok(
        "第 19 期字段缺口候选修复表摘要、行数和候选分布正确",
        field_gap_candidates_summary.get("status") == "issue19_field_gap_repair_candidates_not_final"
        and field_gap_candidates_summary.get("generated_by") == "build_issue19_field_gap_repair_candidates.py"
        and field_gap_candidates_summary.get("source_field_gap_matrix")
        == "data/working/issue19-p1-field-gap-evidence-repair-matrix.csv"
        and field_gap_candidates_summary.get("source_foundation_closure")
        == "data/working/issue19-foundation-closure-major-batches.csv"
        and field_gap_candidates_summary.get("output_table")
        == "data/working/issue19-field-gap-repair-candidates.csv"
        and field_gap_candidates_summary.get("row_count") == 19065
        and field_gap_candidates_summary.get("unique_candidate_task_id_count") == 19065
        and field_gap_candidates_summary.get("unique_field_gap_task_id_count") == 19065
        and field_gap_candidates_summary.get("unique_major_line_id_count") == 12473
        and field_gap_candidates_summary.get("field_counts") == {
            "再选科目": 11456,
            "专业计划数": 6347,
            "学费": 1262,
        }
        and field_gap_candidates_summary.get("candidate_source_type_counts") == {
            "none": 11444,
            "group_ocr_context": 6782,
            "ocr_cell_candidate": 817,
            "school_official_auxiliary": 22,
        }
        and field_gap_candidates_summary.get("non_empty_candidate_value_count") == 7621
        and field_gap_candidates_summary.get("auto_write_allowed_count") == 0
        and field_gap_candidates_summary.get("final_available_count") == 0,
        f"{len(field_gap_candidate_rows)} candidate rows",
    ))
    checks.append(ok(
        "第 19 期字段缺口候选修复表字段、主键和来源闭环正确",
        field_gap_candidate_fields == expected_field_gap_candidate_fields
        and len(field_gap_candidate_rows) == 19065
        and len({row.get("字段候选任务ID") for row in field_gap_candidate_rows}) == 19065
        and {row.get("来源字段补证任务ID") for row in field_gap_candidate_rows}
        == {row.get("字段补证任务ID") for row in field_gap_rows}
        and field_gap_candidate_join_ok,
    ))
    checks.append(ok(
        "第 19 期字段缺口候选修复表公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(field_gap_candidates_public_text) is None
        and "final_allowed" not in field_gap_candidates_public_text
        and "ready_for_discussion" not in field_gap_candidates_public_text
        and "已确认" not in field_gap_candidates_public_text
        and "已核准" not in field_gap_candidates_public_text
        and "最终推荐" not in field_gap_candidates_public_text
        and "最终方案" not in field_gap_candidates_public_text
        and "可填报" not in field_gap_candidates_public_text
        and "可排序" not in field_gap_candidates_public_text,
    ))

    official_sidecar_summary_path = ROOT / "data/working/issue19-b0-b1-official-evidence-sidecar-summary.json"
    official_sidecar_csv = ROOT / "data/working/issue19-b0-b1-official-evidence-by-major-line.csv"
    official_fill_csv = ROOT / "data/working/issue19-b0-b1-official-plan-fill-candidates.csv"
    official_conflict_csv = ROOT / "data/working/issue19-b0-b1-official-conflict-review.csv"
    official_sidecar_summary = json.loads(official_sidecar_summary_path.read_text())
    with official_sidecar_csv.open(newline="", encoding="utf-8-sig") as f:
        official_sidecar_reader = csv.DictReader(f)
        official_sidecar_rows = list(official_sidecar_reader)
        official_sidecar_fields = official_sidecar_reader.fieldnames or []
    with official_fill_csv.open(newline="", encoding="utf-8-sig") as f:
        official_fill_reader = csv.DictReader(f)
        official_fill_rows = list(official_fill_reader)
        official_fill_fields = official_fill_reader.fieldnames or []
    with official_conflict_csv.open(newline="", encoding="utf-8-sig") as f:
        official_conflict_reader = csv.DictReader(f)
        official_conflict_rows = list(official_conflict_reader)
        official_conflict_fields = official_conflict_reader.fieldnames or []
    expected_official_sidecar_fields = [
        "官网证据旁挂ID",
        "来源招生明细主表行ID",
        "来源公开官网差异账ID",
        "来源底座闭环批次ID",
        "来源逐专业闭环主表",
        "来源公开官网差异账",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "可进入下一阶段",
        "能否替代湖北官方计划",
        "官网证据强度",
        "官网证据说明",
        "建议动作",
        "闭环执行总序",
        "闭环执行批次",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "来源页码",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR短摘",
        "OCR计划数",
        "OCR学费",
        "OCR再选科目",
        "官网来源状态",
        "官网证据匹配状态",
        "最佳官网来源文件",
        "最佳官网专业名称",
        "最佳官网专业代号",
        "最佳官网计划数",
        "最佳官网学费",
        "最佳官网选科",
        "专业名称匹配方式",
        "专业名称匹配分",
        "计划数核验状态",
        "差异字段集合",
        "疑似OCR把学费读入计划数",
        "仍需核验",
        "下一步",
    ]
    official_sidecar_join_ok = True
    for row in official_sidecar_rows:
        closure_row = closure_by_major_id.get(row.get("专业行ID"), {})
        official_sidecar_join_ok = (
            official_sidecar_join_ok
            and bool(closure_row)
            and row.get("官网证据旁挂ID") == stable_id("B0B1SIDE", [row.get("专业行ID", "")])
            and row.get("来源底座闭环批次ID") == closure_row.get("底座闭环批次ID")
            and row.get("来源逐专业闭环主表")
            == "data/working/issue19-foundation-closure-major-batches.csv"
            and row.get("数据阶段") == "issue19_b0_b1_official_evidence_sidecar"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("能否替代湖北官方计划") == "false"
            and row.get("闭环执行总序") == closure_row.get("闭环执行总序")
            and row.get("闭环执行批次") == closure_row.get("闭环执行批次")
            and row.get("专业组出现ID") == closure_row.get("专业组出现ID")
            and row.get("院校代码") == closure_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == closure_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == closure_row.get("来源页码")
            and row.get("专业组内专业序号") == closure_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == closure_row.get("专业代号OCR")
            and "必须回到 PDF 原页" in row.get("下一步", "")
        )
    official_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [official_sidecar_summary_path, official_sidecar_csv, official_fill_csv, official_conflict_csv]
    )
    checks.append(ok(
        "第 19 期 B0/B1 官网证据旁挂表摘要、行数和分层正确",
        official_sidecar_summary.get("status") == "issue19_b0_b1_official_evidence_sidecar_not_final"
        and official_sidecar_summary.get("generated_by")
        == "build_issue19_b0_b1_official_evidence_sidecar.py"
        and official_sidecar_summary.get("source_public_official_diff_ledger")
        == "data/working/issue19-b0-b1-public-official-diff-ledger.csv"
        and official_sidecar_summary.get("source_foundation_closure")
        == "data/working/issue19-foundation-closure-major-batches.csv"
        and official_sidecar_summary.get("sidecar_row_count") == 854
        and official_sidecar_summary.get("unique_major_line_id_count") == 854
        and official_sidecar_summary.get("unique_school_count") == 36
        and official_sidecar_summary.get("evidence_strength_counts") == {
            "needs_source": 196,
            "unmatched": 31,
            "fill_candidate": 55,
            "strong_support": 61,
            "rules_only": 63,
            "partial_source": 411,
            "conflict_review": 18,
            "field_support": 19,
        }
        and official_sidecar_summary.get("fill_candidate_row_count") == 55
        and official_sidecar_summary.get("conflict_review_row_count") == 18
        and official_sidecar_summary.get("suspected_plan_fee_misread_count") == 13
        and official_sidecar_summary.get("final_available_count") == 0
        and official_sidecar_summary.get("official_plan_replacement_allowed_count") == 0,
        f"{len(official_sidecar_rows)} sidecar rows",
    ))
    checks.append(ok(
        "第 19 期 B0/B1 官网证据旁挂表字段、主键和闭环主表来源正确",
        official_sidecar_fields == expected_official_sidecar_fields
        and official_fill_fields == expected_official_sidecar_fields
        and official_conflict_fields == expected_official_sidecar_fields
        and len(official_sidecar_rows) == 854
        and len({row.get("官网证据旁挂ID") for row in official_sidecar_rows}) == 854
        and len({row.get("专业行ID") for row in official_sidecar_rows}) == 854
        and len(official_fill_rows) == 55
        and all(row.get("官网证据强度") == "fill_candidate" for row in official_fill_rows)
        and len(official_conflict_rows) == 18
        and all(row.get("官网证据强度") == "conflict_review" for row in official_conflict_rows)
        and official_sidecar_join_ok,
    ))
    checks.append(ok(
        "第 19 期 B0/B1 官网证据旁挂表公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(official_public_text) is None
        and "final_allowed" not in official_public_text
        and "ready_for_discussion" not in official_public_text
        and "已确认" not in official_public_text
        and "已核准" not in official_public_text
        and "最终推荐" not in official_public_text
        and "最终方案" not in official_public_text
        and "可填报" not in official_public_text
        and "可排序" not in official_public_text,
    ))

    pdf_anchor_summary_path = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors-summary.json"
    pdf_anchor_csv = ROOT / "data/working/issue19-major-line-pdf-evidence-anchors.csv"
    pdf_anchor_summary = json.loads(pdf_anchor_summary_path.read_text())
    with pdf_anchor_csv.open(newline="", encoding="utf-8-sig") as f:
        pdf_anchor_reader = csv.DictReader(f)
        pdf_anchor_rows = list(pdf_anchor_reader)
        pdf_anchor_fields = pdf_anchor_reader.fieldnames or []
    expected_pdf_anchor_fields = [
        "专业行原页证据锚点ID",
        "来源逐专业质量工作台",
        "来源私有OCR行级CSV",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "可进入下一阶段",
        "证据锚点状态",
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
        "专业组标题行号",
        "专业组标题y",
        "专业起始行号",
        "专业起始y",
        "OCR窗口y上界",
        "OCR窗口y下界",
        "组标题上下文行号范围",
        "专业窗口行号范围",
        "合并证据窗口行号范围",
        "组标题上下文行数",
        "专业窗口行数",
        "合并证据窗口行数",
        "窗口平均置信度",
        "窗口最低置信度",
        "窗口坐标摘要",
        "窗口文本SHA256",
        "起始行回连状态",
        "起始行文本SHA256",
        "起始行专业代号匹配",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "私有窗口证据编号",
        "公开安全策略",
        "下一步",
    ]
    anchor_join_ok = True
    for row in pdf_anchor_rows:
        closure_row = closure_by_major_id.get(row.get("专业行ID"), {})
        anchor_join_ok = (
            anchor_join_ok
            and bool(closure_row)
            and row.get("专业行原页证据锚点ID")
            == stable_id("PDFANCHOR", [row.get("专业行ID", ""), row.get("专业起始行号", "")])
            and row.get("来源逐专业质量工作台")
            == "data/working/issue19-full-major-detail-quality-workbench.csv"
            and row.get("来源私有OCR行级CSV") == "private_ocr_lines_not_public"
            and row.get("数据阶段") == "issue19_major_line_pdf_evidence_anchors"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("专业组出现ID") == closure_row.get("专业组出现ID")
            and row.get("院校代码") == closure_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == closure_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == closure_row.get("来源页码")
            and row.get("版面列") == closure_row.get("版面列")
            and row.get("专业组内专业序号") == closure_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == closure_row.get("专业代号OCR")
            and row.get("起始行回连状态") == "exact_start_line_hit"
            and row.get("起始行专业代号匹配") == "true"
            and bool(row.get("窗口文本SHA256"))
            and "确认前不得作为最终志愿事实" in row.get("下一步", "")
        )
    pdf_anchor_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [pdf_anchor_summary_path, pdf_anchor_csv]
    )
    checks.append(ok(
        "第 19 期专业行原页证据锚点表摘要、行数和锚点分层正确",
        pdf_anchor_summary.get("status") == "issue19_major_line_pdf_evidence_anchors_not_final"
        and pdf_anchor_summary.get("generated_by")
        == "build_issue19_major_line_pdf_evidence_anchors.py"
        and pdf_anchor_summary.get("source_major_quality_workbench")
        == "data/working/issue19-full-major-detail-quality-workbench.csv"
        and pdf_anchor_summary.get("source_private_ocr_lines") == "private_ocr_lines_not_public"
        and pdf_anchor_summary.get("output_table")
        == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
        and pdf_anchor_summary.get("row_count") == 13736
        and pdf_anchor_summary.get("unique_anchor_id_count") == 13736
        and pdf_anchor_summary.get("unique_major_line_id_count") == 13736
        and pdf_anchor_summary.get("status_counts") == {
            "P2-已生成专业行级OCR证据锚点": 12596,
            "P1-缺少组标题上下文": 1127,
            "P0-专业窗口为空": 13,
        }
        and pdf_anchor_summary.get("exact_start_line_hit_count") == 13736
        and pdf_anchor_summary.get("start_line_major_code_match_count") == 13736
        and pdf_anchor_summary.get("non_empty_window_count") == 13736
        and pdf_anchor_summary.get("window_sha_non_empty_count") == 13736
        and pdf_anchor_summary.get("final_available_count") == 0
        and pdf_anchor_summary.get("next_stage_available_count") == 0,
        f"{len(pdf_anchor_rows)} anchor rows",
    ))
    checks.append(ok(
        "第 19 期专业行原页证据锚点表字段、主键和闭环主表来源正确",
        pdf_anchor_fields == expected_pdf_anchor_fields
        and len(pdf_anchor_rows) == 13736
        and len({row.get("专业行原页证据锚点ID") for row in pdf_anchor_rows}) == 13736
        and {row.get("专业行ID") for row in pdf_anchor_rows}
        == {row.get("专业行ID") for row in closure_major_rows}
        and anchor_join_ok,
    ))
    checks.append(ok(
        "第 19 期专业行原页证据锚点表公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(pdf_anchor_public_text) is None
        and "private/" not in pdf_anchor_public_text
        and "final_allowed" not in pdf_anchor_public_text
        and "ready_for_discussion" not in pdf_anchor_public_text
        and "已确认" not in pdf_anchor_public_text
        and "已核准" not in pdf_anchor_public_text
        and "最终推荐" not in pdf_anchor_public_text
        and "最终方案" not in pdf_anchor_public_text
        and "可填报" not in pdf_anchor_public_text
        and "可排序" not in pdf_anchor_public_text,
    ))

    gap_scorecard_summary_path = ROOT / "data/working/issue19-foundation-closure-gap-scorecard-summary.json"
    gap_scorecard_csv = ROOT / "data/working/issue19-foundation-closure-gap-scorecard.csv"
    gap_scorecard_summary = json.loads(gap_scorecard_summary_path.read_text())
    with gap_scorecard_csv.open(newline="", encoding="utf-8-sig") as f:
        gap_scorecard_reader = csv.DictReader(f)
        gap_scorecard_rows = list(gap_scorecard_reader)
        gap_scorecard_fields = gap_scorecard_reader.fieldnames or []
    expected_gap_scorecard_fields = [
        "闭环缺口看板ID",
        "来源逐专业闭环主表",
        "来源统一逐专业底座入口",
        "来源字段候选表",
        "来源B0B1官网旁挂表",
        "来源专业行原页证据锚点表",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "最终可用",
        "可进入下一阶段",
        "最终志愿排序门禁",
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
        "闭环执行总序",
        "看板执行总序",
        "闭环执行批次",
        "首要核验动作",
        "闭环执行动作集合",
        "看板动作桶",
        "看板排序分",
        "机器可辅助线索",
        "必须人工核PDF原页",
        "必须湖北官方系统或省招办计划核验",
        "必须家庭接受度确认",
        "必须同组调剂结论确认",
        "字段缺口字段",
        "字段缺口数",
        "字段候选任务数",
        "非空字段候选数",
        "中置信字段候选数",
        "低置信字段候选数",
        "有候选字段",
        "字段候选状态分布",
        "字段候选来源分布",
        "B0B1官网证据任务数",
        "B0B1官网证据强度",
        "B0B1计划数状态",
        "B0B1官网建议动作",
        "官网证据能否替代湖北官方计划",
        "专业行原页证据锚点ID",
        "原页证据锚点状态",
        "专业窗口行号范围",
        "合并证据窗口行数",
        "窗口文本SHA256",
        "起始行专业代号匹配",
        "页级复核优先级",
        "页级阻断等级",
        "P0复核任务数",
        "P0证据项",
        "湖北官方平台字段核验状态",
        "家庭接受度结论",
        "同组调剂结论",
        "机器专业接受度初判",
        "调剂影响等级",
        "专业偏好方向",
        "风险阻断等级",
        "三年投档稳定性状态",
        "不得进入原因",
        "下一步",
    ]
    field_candidate_major_counts = Counter(row.get("专业行ID") for row in field_gap_candidate_rows if row.get("候选值"))
    sidecar_major_counts = Counter(row.get("专业行ID") for row in official_sidecar_rows)
    anchor_by_major_id = {row.get("专业行ID"): row for row in pdf_anchor_rows}
    gap_scorecard_join_ok = True
    for row in gap_scorecard_rows:
        closure_row = closure_by_major_id.get(row.get("专业行ID"), {})
        anchor_row = anchor_by_major_id.get(row.get("专业行ID"), {})
        gap_scorecard_join_ok = (
            gap_scorecard_join_ok
            and bool(closure_row)
            and bool(anchor_row)
            and row.get("闭环缺口看板ID") == stable_id("GAPSCORE", [row.get("专业行ID", "")])
            and row.get("来源逐专业闭环主表")
            == "data/working/issue19-foundation-closure-major-batches.csv"
            and row.get("来源统一逐专业底座入口")
            == "data/working/issue19-major-detail-foundation-release.csv"
            and row.get("来源字段候选表")
            == "data/working/issue19-field-gap-repair-candidates.csv"
            and row.get("来源B0B1官网旁挂表")
            == "data/working/issue19-b0-b1-official-evidence-by-major-line.csv"
            and row.get("来源专业行原页证据锚点表")
            == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
            and row.get("数据阶段") == "issue19_foundation_closure_gap_scorecard"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("最终志愿排序门禁") == "阻断-待证据闭环"
            and row.get("专业组出现ID") == closure_row.get("专业组出现ID")
            and row.get("院校代码") == closure_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == closure_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == closure_row.get("来源页码")
            and row.get("版面列") == closure_row.get("版面列")
            and row.get("专业组内专业序号") == closure_row.get("专业组内专业序号")
            and row.get("闭环执行总序") == closure_row.get("闭环执行总序")
            and row.get("闭环执行批次") == closure_row.get("闭环执行批次")
            and row.get("必须人工核PDF原页") == "true"
            and row.get("必须湖北官方系统或省招办计划核验") == "true"
            and row.get("必须家庭接受度确认") == "true"
            and row.get("必须同组调剂结论确认") == "true"
            and row.get("官网证据能否替代湖北官方计划") == "false"
            and as_int(row.get("非空字段候选数")) == field_candidate_major_counts.get(row.get("专业行ID"), 0)
            and as_int(row.get("B0B1官网证据任务数")) == sidecar_major_counts.get(row.get("专业行ID"), 0)
            and row.get("专业行原页证据锚点ID") == anchor_row.get("专业行原页证据锚点ID")
            and row.get("窗口文本SHA256") == anchor_row.get("窗口文本SHA256")
            and "确认前不得进入最终志愿排序" in row.get("下一步", "")
        )
    gap_scorecard_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [gap_scorecard_summary_path, gap_scorecard_csv]
    )
    checks.append(ok(
        "第 19 期逐专业闭环缺口看板摘要、行数和动作桶正确",
        gap_scorecard_summary.get("status") == "issue19_foundation_closure_gap_scorecard_not_final"
        and gap_scorecard_summary.get("generated_by")
        == "build_issue19_foundation_closure_gap_scorecard.py"
        and gap_scorecard_summary.get("output_table")
        == "data/working/issue19-foundation-closure-gap-scorecard.csv"
        and gap_scorecard_summary.get("source_foundation_closure")
        == "data/working/issue19-foundation-closure-major-batches.csv"
        and gap_scorecard_summary.get("source_field_candidates")
        == "data/working/issue19-field-gap-repair-candidates.csv"
        and gap_scorecard_summary.get("source_b0_b1_sidecar")
        == "data/working/issue19-b0-b1-official-evidence-by-major-line.csv"
        and gap_scorecard_summary.get("source_pdf_anchors")
        == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
        and gap_scorecard_summary.get("row_count") == 13736
        and gap_scorecard_summary.get("unique_scorecard_id_count") == 13736
        and gap_scorecard_summary.get("unique_major_line_id_count") == 13736
        and gap_scorecard_summary.get("batch_counts") == {
            "C0-P0证据闭环先核": 5310,
            "C1-字段缺口先补": 7608,
            "C3-常规三方证据闭环": 609,
            "C4-低风险抽检但非最终": 209,
        }
        and gap_scorecard_summary.get("action_bucket_counts") == {
            "S0-B0B1冲突+P0原页优先": 18,
            "S1-P0原页+官网辅证同步核": 116,
            "S2-P0原页结构和字段先核": 5176,
            "S3-字段缺口有候选先核": 4248,
            "S4-字段缺口无候选需原页重读": 3360,
            "S6-常规三方闭环": 609,
            "S7-低风险但证据锚点异常抽检": 2,
            "S8-低风险抽检": 207,
        }
        and gap_scorecard_summary.get("non_empty_field_candidate_major_count") == 7202
        and gap_scorecard_summary.get("b0_b1_sidecar_major_count") == 854
        and gap_scorecard_summary.get("pdf_anchor_major_count") == 13736
        and gap_scorecard_summary.get("official_replace_allowed_count") == 0
        and gap_scorecard_summary.get("final_available_count") == 0
        and gap_scorecard_summary.get("next_stage_available_count") == 0,
        f"{len(gap_scorecard_rows)} scorecard rows",
    ))
    checks.append(ok(
        "第 19 期逐专业闭环缺口看板字段、主键和三类证据来源闭环正确",
        gap_scorecard_fields == expected_gap_scorecard_fields
        and len(gap_scorecard_rows) == 13736
        and len({row.get("闭环缺口看板ID") for row in gap_scorecard_rows}) == 13736
        and {row.get("专业行ID") for row in gap_scorecard_rows}
        == {row.get("专业行ID") for row in closure_major_rows}
        and gap_scorecard_join_ok,
    ))
    checks.append(ok(
        "第 19 期逐专业闭环缺口看板公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(gap_scorecard_public_text) is None
        and "private/" not in gap_scorecard_public_text
        and "final_allowed" not in gap_scorecard_public_text
        and "ready_for_discussion" not in gap_scorecard_public_text
        and "已确认" not in gap_scorecard_public_text
        and "已核准" not in gap_scorecard_public_text
        and "最终推荐" not in gap_scorecard_public_text
        and "最终方案" not in gap_scorecard_public_text
        and "可填报" not in gap_scorecard_public_text
        and "可排序" not in gap_scorecard_public_text,
    ))

    historical_sidecar_summary_path = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar-summary.json"
    historical_sidecar_csv = ROOT / "data/working/issue19-major-line-historical-toudang-sidecar.csv"
    historical_sidecar_summary = json.loads(historical_sidecar_summary_path.read_text())
    with historical_sidecar_csv.open(newline="", encoding="utf-8-sig") as f:
        historical_sidecar_reader = csv.DictReader(f)
        historical_sidecar_rows = list(historical_sidecar_reader)
        historical_sidecar_fields = historical_sidecar_reader.fieldnames or []
    expected_historical_sidecar_fields = [
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
    historical_sidecar_join_ok = True
    for row in historical_sidecar_rows:
        release_row = foundation_release_by_major_id.get(row.get("专业行ID"), {})
        hit_count = sum(row.get(f"{year}同代码命中") == "true" for year in [2023, 2024, 2025])
        historical_sidecar_join_ok = (
            historical_sidecar_join_ok
            and bool(release_row)
            and row.get("三年投档旁挂ID") == stable_id("HISTLINE", [row.get("专业行ID", "")])
            and row.get("来源统一逐专业底座入口")
            == "data/working/issue19-major-detail-foundation-release.csv"
            and row.get("来源2023投档线") == "data/derived/hubei-2023-physics-toudang-parsed.csv"
            and row.get("来源2024投档线") == "data/derived/hubei-2024-physics-toudang-parsed.csv"
            and row.get("来源2025投档线") == "data/derived/hubei-2025-physics-toudang-parsed.csv"
            and row.get("数据阶段") == "issue19_major_line_historical_toudang_sidecar"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("仅供冲稳保筛选线索") == "true"
            and row.get("专业组出现ID") == release_row.get("专业组出现ID")
            and row.get("院校代码") == release_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == release_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == release_row.get("来源页码")
            and row.get("版面列") == release_row.get("版面列")
            and row.get("专业组内专业序号") == release_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == release_row.get("专业代号OCR")
            and as_int(row.get("同代码命中年份数")) == hit_count
            and row.get("院校专业组代码OCR规范化", "").startswith(row.get("院校代码", ""))
            and "不能证明2026专业组存在" in row.get("历史线使用口径", "")
            and "不得单独据此下最终结论" in row.get("下一步", "")
        )
    historical_sidecar_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [historical_sidecar_summary_path, historical_sidecar_csv]
    )
    checks.append(ok(
        "第 19 期逐专业三年投档线索旁挂表摘要、行数和命中分布正确",
        historical_sidecar_summary.get("status") == "issue19_major_line_historical_toudang_sidecar_not_final"
        and historical_sidecar_summary.get("generated_by")
        == "build_issue19_major_line_historical_toudang_sidecar.py"
        and historical_sidecar_summary.get("output_table")
        == "data/working/issue19-major-line-historical-toudang-sidecar.csv"
        and historical_sidecar_summary.get("source_foundation_release")
        == "data/working/issue19-major-detail-foundation-release.csv"
        and historical_sidecar_summary.get("source_toudang_counts") == {
            "2023": 2874,
            "2024": 2800,
            "2025": 3147,
        }
        and historical_sidecar_summary.get("historical_duplicate_codes") == {
            "2023": [],
            "2024": [],
            "2025": ["H51001"],
        }
        and historical_sidecar_summary.get("row_count") == 13736
        and historical_sidecar_summary.get("unique_sidecar_id_count") == 13736
        and historical_sidecar_summary.get("unique_major_line_id_count") == 13736
        and historical_sidecar_summary.get("hit_year_count_distribution") == {
            "1": 1940,
            "0": 2014,
            "3": 5836,
            "2": 3946,
        }
        and historical_sidecar_summary.get("stability_layer_counts") == {
            "H1-一年同代码命中": 1940,
            "H0-三年同代码未命中或组号变化": 2014,
            "H3-三年同代码命中": 2126,
            "H3-同代码命中但再选要求变化": 3696,
            "H2-两年同代码命中": 2011,
            "H2-同代码命中但再选要求变化": 1935,
            "H3-同代码命中但2026组代码重复出现": 14,
        }
        and historical_sidecar_summary.get("historical_duplicate_major_line_count") == 0
        and historical_sidecar_summary.get("current_duplicate_group_major_line_count") == 14
        and historical_sidecar_summary.get("req_changed_major_line_count") == 5645
        and historical_sidecar_summary.get("screening_clue_count") == 13736
        and historical_sidecar_summary.get("final_available_count") == 0
        and historical_sidecar_summary.get("next_stage_available_count") == 0,
        f"{len(historical_sidecar_rows)} historical sidecar rows",
    ))
    checks.append(ok(
        "第 19 期逐专业三年投档线索旁挂表字段、主键和统一底座来源闭环正确",
        historical_sidecar_fields == expected_historical_sidecar_fields
        and len(historical_sidecar_rows) == 13736
        and len({row.get("三年投档旁挂ID") for row in historical_sidecar_rows}) == 13736
        and {row.get("专业行ID") for row in historical_sidecar_rows}
        == {row.get("专业行ID") for row in foundation_release_rows}
        and historical_sidecar_join_ok,
    ))
    checks.append(ok(
        "第 19 期逐专业三年投档线索旁挂表公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(historical_sidecar_public_text) is None
        and "private/" not in historical_sidecar_public_text
        and "final_allowed" not in historical_sidecar_public_text
        and "ready_for_discussion" not in historical_sidecar_public_text
        and "已确认" not in historical_sidecar_public_text
        and "已核准" not in historical_sidecar_public_text
        and "最终推荐" not in historical_sidecar_public_text
        and "最终方案" not in historical_sidecar_public_text
        and "可填报" not in historical_sidecar_public_text
        and "可排序" not in historical_sidecar_public_text,
    ))

    admission_master_summary_path = ROOT / "data/working/issue19-admission-detail-master-workbench-summary.json"
    admission_master_csv = ROOT / "data/working/issue19-admission-detail-master-workbench.csv"
    admission_master_summary = json.loads(admission_master_summary_path.read_text())
    with admission_master_csv.open(newline="", encoding="utf-8-sig") as f:
        admission_master_reader = csv.DictReader(f)
        admission_master_rows = list(admission_master_reader)
        admission_master_fields = admission_master_reader.fieldnames or []
    expected_admission_master_fields = script_list_constant(
        ROOT / "scripts/build_issue19_admission_detail_master_workbench.py",
        "FIELDS",
    )
    required_admission_master_fields = {
        "招生明细总工作台ID",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "专业代号OCR",
        "专业名称及备注OCR",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业行原页证据锚点ID",
        "窗口文本SHA256",
        "起始行专业代号匹配",
        "闭环执行批次",
        "看板动作桶",
        "必须人工核PDF原页",
        "必须湖北官方系统或省招办计划核验",
        "必须家庭接受度确认",
        "必须同组调剂结论确认",
        "同代码命中年份数",
        "稳定性分层",
        "历史线使用口径",
        "最终可用",
        "可进入下一阶段",
    }
    gap_scorecard_by_major_id = {row.get("专业行ID"): row for row in gap_scorecard_rows}
    historical_sidecar_by_major_id = {row.get("专业行ID"): row for row in historical_sidecar_rows}
    admission_master_by_major_id = {row.get("专业行ID"): row for row in admission_master_rows}
    admission_master_join_ok = True
    for row in admission_master_rows:
        major_id = row.get("专业行ID")
        release_row = foundation_release_by_major_id.get(major_id, {})
        gap_row = gap_scorecard_by_major_id.get(major_id, {})
        anchor_row = anchor_by_major_id.get(major_id, {})
        history_row = historical_sidecar_by_major_id.get(major_id, {})
        admission_master_join_ok = (
            admission_master_join_ok
            and bool(release_row)
            and bool(gap_row)
            and bool(anchor_row)
            and bool(history_row)
            and row.get("招生明细总工作台ID") == stable_id("ADMISSIONDETAIL", [major_id])
            and row.get("来源统一逐专业底座入口")
            == "data/working/issue19-major-detail-foundation-release.csv"
            and row.get("来源逐专业闭环缺口看板")
            == "data/working/issue19-foundation-closure-gap-scorecard.csv"
            and row.get("来源专业行原页证据锚点表")
            == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
            and row.get("来源三年投档线索旁挂表")
            == "data/working/issue19-major-line-historical-toudang-sidecar.csv"
            and row.get("数据阶段") == "issue19_admission_detail_master_workbench"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("专业组出现ID") == release_row.get("专业组出现ID")
            and row.get("院校代码") == release_row.get("院校代码")
            and row.get("院校专业组代码OCR规范化")
            == release_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == release_row.get("来源页码")
            and row.get("版面列") == release_row.get("版面列")
            and row.get("专业组内专业序号") == release_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == release_row.get("专业代号OCR")
            and row.get("专业名称及备注OCR") == release_row.get("专业名称及备注OCR")
            and row.get("专业行原页证据锚点ID") == anchor_row.get("专业行原页证据锚点ID")
            and row.get("窗口文本SHA256") == anchor_row.get("窗口文本SHA256")
            and row.get("起始行专业代号匹配") == anchor_row.get("起始行专业代号匹配")
            and row.get("闭环执行批次") == gap_row.get("闭环执行批次")
            and row.get("看板动作桶") == gap_row.get("看板动作桶")
            and row.get("必须人工核PDF原页") == "true"
            and row.get("必须湖北官方系统或省招办计划核验") == "true"
            and row.get("必须家庭接受度确认") == "true"
            and row.get("必须同组调剂结论确认") == "true"
            and row.get("官网证据能否替代湖北官方计划") == "false"
            and row.get("同代码命中年份数") == history_row.get("同代码命中年份数")
            and row.get("稳定性分层") == history_row.get("稳定性分层")
            and "不能证明2026专业组存在" in row.get("历史线使用口径", "")
            and "不得进入最终志愿排序" in row.get("下一步", "")
        )
    admission_master_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [admission_master_summary_path, admission_master_csv]
    )
    checks.append(ok(
        "第 19 期单一逐专业招生明细总工作台摘要、行数和全量 join 正确",
        admission_master_summary.get("status") == "issue19_admission_detail_master_workbench_not_final"
        and admission_master_summary.get("generated_by")
        == "build_issue19_admission_detail_master_workbench.py"
        and admission_master_summary.get("output_table")
        == "data/working/issue19-admission-detail-master-workbench.csv"
        and admission_master_summary.get("source_foundation_release")
        == "data/working/issue19-major-detail-foundation-release.csv"
        and admission_master_summary.get("source_gap_scorecard")
        == "data/working/issue19-foundation-closure-gap-scorecard.csv"
        and admission_master_summary.get("source_pdf_anchors")
        == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
        and admission_master_summary.get("source_historical_sidecar")
        == "data/working/issue19-major-line-historical-toudang-sidecar.csv"
        and admission_master_summary.get("row_grain_contract")
        == "one_row_per_admission_major_detail"
        and admission_master_summary.get("row_count") == 13736
        and admission_master_summary.get("unique_workbench_id_count") == 13736
        and admission_master_summary.get("unique_major_line_id_count") == 13736
        and admission_master_summary.get("missing_join_counts") == {}
        and admission_master_summary.get("gap_scorecard_join_count") == 13736
        and admission_master_summary.get("pdf_anchor_join_count") == 13736
        and admission_master_summary.get("historical_sidecar_join_count") == 13736
        and admission_master_summary.get("final_available_count") == 0
        and admission_master_summary.get("next_stage_available_count") == 0
        and admission_master_summary.get("official_replace_allowed_count") == 0
        and admission_master_summary.get("field_candidate_major_count") == 7202
        and admission_master_summary.get("b0_b1_evidence_major_count") == 854
        and admission_master_summary.get("must_pdf_review_count") == 13736
        and admission_master_summary.get("must_hubei_official_review_count") == 13736
        and admission_master_summary.get("must_family_review_count") == 13736
        and admission_master_summary.get("must_transfer_review_count") == 13736,
        f"{len(admission_master_rows)} admission detail rows",
    ))
    checks.append(ok(
        "第 19 期单一逐专业招生明细总工作台字段、主键和来源闭环正确",
        admission_master_fields == expected_admission_master_fields
        and required_admission_master_fields.issubset(set(admission_master_fields))
        and len(admission_master_rows) == 13736
        and len({row.get("招生明细总工作台ID") for row in admission_master_rows}) == 13736
        and {row.get("专业行ID") for row in admission_master_rows}
        == {row.get("专业行ID") for row in foundation_release_rows}
        and admission_master_join_ok,
    ))
    checks.append(ok(
        "第 19 期单一逐专业招生明细总工作台公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(admission_master_public_text) is None
        and "private/" not in admission_master_public_text
        and "final_allowed" not in admission_master_public_text
        and "ready_for_discussion" not in admission_master_public_text
        and "已确认" not in admission_master_public_text
        and "已核准" not in admission_master_public_text
        and "最终推荐" not in admission_master_public_text
        and "最终方案" not in admission_master_public_text
        and "可填报" not in admission_master_public_text
        and "可排序" not in admission_master_public_text,
    ))

    structural_summary_path = ROOT / "data/working/issue19-admission-detail-structural-fidelity-summary.json"
    structural_register_csv = ROOT / "data/working/issue19-admission-detail-structural-fidelity-register.csv"
    structural_event_csv = ROOT / "data/working/issue19-structural-risk-major-line-ledger.csv"
    zero_detail_csv = ROOT / "data/working/issue19-zero-detail-group-placeholder-workbench.csv"
    structural_summary = json.loads(structural_summary_path.read_text())
    with structural_register_csv.open(newline="", encoding="utf-8-sig") as f:
        structural_register_reader = csv.DictReader(f)
        structural_register_rows = list(structural_register_reader)
        structural_register_fields = structural_register_reader.fieldnames or []
    with structural_event_csv.open(newline="", encoding="utf-8-sig") as f:
        structural_event_reader = csv.DictReader(f)
        structural_event_rows = list(structural_event_reader)
        structural_event_fields = structural_event_reader.fieldnames or []
    with zero_detail_csv.open(newline="", encoding="utf-8-sig") as f:
        zero_detail_reader = csv.DictReader(f)
        zero_detail_rows = list(zero_detail_reader)
        zero_detail_fields = zero_detail_reader.fieldnames or []
    expected_structural_register_fields = script_list_constant(
        ROOT / "scripts/build_issue19_admission_detail_structural_fidelity_register.py",
        "REGISTER_FIELDS",
    )
    expected_structural_event_fields = script_list_constant(
        ROOT / "scripts/build_issue19_admission_detail_structural_fidelity_register.py",
        "RISK_EVENT_FIELDS",
    )
    expected_zero_detail_fields = script_list_constant(
        ROOT / "scripts/build_issue19_admission_detail_structural_fidelity_register.py",
        "ZERO_DETAIL_FIELDS",
    )
    structural_by_major_id = {row.get("专业行ID"): row for row in structural_register_rows}
    structural_event_join_ok = True
    for row in structural_event_rows:
        register_row = structural_by_major_id.get(row.get("专业行ID"), {})
        structural_event_join_ok = (
            structural_event_join_ok
            and bool(register_row)
            and row.get("结构风险事件ID")
            == stable_id("STRUCTEVENT", [row.get("专业行ID", ""), row.get("结构风险类型", "")])
            and row.get("来源结构保真登记表")
            == "data/working/issue19-admission-detail-structural-fidelity-register.csv"
            and row.get("来源单一逐专业招生明细总工作台")
            == "data/working/issue19-admission-detail-master-workbench.csv"
            and row.get("数据阶段") == "issue19_structural_risk_major_line_ledger"
            and row.get("主表粒度") == "逐专业招生明细×结构风险事件"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器能否自动修复") == "false"
            and row.get("专业组出现ID") == register_row.get("专业组出现ID")
            and row.get("院校专业组代码OCR规范化")
            == register_row.get("院校专业组代码OCR规范化")
            and "确认前不得进入最终志愿排序" in row.get("不得进入原因", "")
        )
    structural_register_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [structural_summary_path, structural_register_csv, structural_event_csv, zero_detail_csv]
    )
    checks.append(ok(
        "第 19 期逐专业结构保真登记摘要、风险事件和0明细占位正确",
        structural_summary.get("status") == "issue19_admission_detail_structural_fidelity_not_final"
        and structural_summary.get("generated_by")
        == "build_issue19_admission_detail_structural_fidelity_register.py"
        and structural_summary.get("output_table")
        == "data/working/issue19-admission-detail-structural-fidelity-register.csv"
        and structural_summary.get("risk_event_output_table")
        == "data/working/issue19-structural-risk-major-line-ledger.csv"
        and structural_summary.get("zero_detail_output_table")
        == "data/working/issue19-zero-detail-group-placeholder-workbench.csv"
        and structural_summary.get("source_master_workbench")
        == "data/working/issue19-admission-detail-master-workbench.csv"
        and structural_summary.get("row_count") == 13736
        and structural_summary.get("unique_register_id_count") == 13736
        and structural_summary.get("unique_major_line_id_count") == 13736
        and structural_summary.get("assignment_method_counts") == {
            "exact_group_header_match": 11898,
            "fallback_unique_group_code": 1838,
        }
        and structural_summary.get("fallback_unique_group_code_major_count") == 1838
        and structural_summary.get("duplicate_normalized_group_code_major_count") == 14
        and structural_summary.get("duplicate_major_code_row_count") == 116
        and structural_summary.get("duplicate_major_code_group_count") == 31
        and structural_summary.get("anchor_status_counts") == {
            "P2-已生成专业行级OCR证据锚点": 12596,
            "P1-缺少组标题上下文": 1127,
            "P0-专业窗口为空": 13,
        }
        and structural_summary.get("risk_event_count") == 3108
        and structural_summary.get("risk_event_type_counts") == {
            "唯一组码回退归属": 1838,
            "原页缺少组标题上下文": 1127,
            "组内专业代号重复": 116,
            "原页专业窗口为空": 13,
            "2026规范化专业组代码重复": 14,
        }
        and structural_summary.get("zero_detail_group_count") == 40
        and structural_summary.get("final_available_count") == 0
        and structural_summary.get("next_stage_available_count") == 0
        and structural_summary.get("machine_auto_fix_count") == 0,
        f"{len(structural_register_rows)} structural rows, {len(structural_event_rows)} events, {len(zero_detail_rows)} zero-detail groups",
    ))
    checks.append(ok(
        "第 19 期逐专业结构保真登记字段、主键和来源闭环正确",
        structural_register_fields == expected_structural_register_fields
        and structural_event_fields == expected_structural_event_fields
        and zero_detail_fields == expected_zero_detail_fields
        and len(structural_register_rows) == 13736
        and len(structural_event_rows) == 3108
        and len(zero_detail_rows) == 40
        and len({row.get("结构保真登记ID") for row in structural_register_rows}) == 13736
        and len({row.get("结构风险事件ID") for row in structural_event_rows}) == 3108
        and len({row.get("0明细占位ID") for row in zero_detail_rows}) == 40
        and {row.get("专业行ID") for row in structural_register_rows}
        == {row.get("专业行ID") for row in admission_master_rows}
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("必须人工核PDF原页") == "true"
            and row.get("必须湖北官方系统或省招办计划核验") == "true"
            and row.get("机器能否自动修复") == "false"
            for row in structural_register_rows
        )
        and sum(row.get("是否唯一组码回退归属") == "true" for row in structural_register_rows) == 1838
        and sum(row.get("是否组内专业代号重复") == "true" for row in structural_register_rows) == 116
        and sum(row.get("规范化专业组代码是否重复") == "是" for row in structural_register_rows) == 14
        and sum(row.get("原页证据锚点状态") == "P0-专业窗口为空" for row in structural_register_rows) == 13
        and sum(row.get("原页证据锚点状态") == "P1-缺少组标题上下文" for row in structural_register_rows) == 1127
        and structural_event_join_ok
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("是否真实招生明细") == "false"
            and row.get("是否0明细占位") == "true"
            and row.get("是否可作为招生明细行") == "false"
            for row in zero_detail_rows
        ),
    ))
    checks.append(ok(
        "第 19 期逐专业结构保真登记公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(structural_register_public_text) is None
        and "private/" not in structural_register_public_text
        and "final_allowed" not in structural_register_public_text
        and "ready_for_discussion" not in structural_register_public_text
        and "已确认" not in structural_register_public_text
        and "已核准" not in structural_register_public_text
        and "最终推荐" not in structural_register_public_text
        and "最终方案" not in structural_register_public_text
        and "可填报" not in structural_register_public_text
        and "可排序" not in structural_register_public_text,
    ))

    filter_prep_summary_path = ROOT / "data/working/issue19-candidate-filter-prep-summary.json"
    filter_prep_csv = ROOT / "data/working/issue19-candidate-filter-prep-major-detail.csv"
    filter_prep_summary = json.loads(filter_prep_summary_path.read_text())
    with filter_prep_csv.open(newline="", encoding="utf-8-sig") as f:
        filter_prep_reader = csv.DictReader(f)
        filter_prep_rows = list(filter_prep_reader)
        filter_prep_fields = filter_prep_reader.fieldnames or []
    expected_filter_prep_fields = script_list_constant(
        ROOT / "scripts/build_issue19_candidate_filter_prep_major_detail.py",
        "FIELDS",
    )
    filter_prep_join_ok = True
    for row in filter_prep_rows:
        master_row = admission_master_by_major_id.get(row.get("专业行ID"), {})
        structure_row = structural_by_major_id.get(row.get("专业行ID"), {})
        filter_prep_join_ok = (
            filter_prep_join_ok
            and bool(master_row)
            and bool(structure_row)
            and row.get("候选筛选准备ID") == stable_id("FILTERPREP", [row.get("专业行ID", "")])
            and row.get("来源单一逐专业招生明细总工作台")
            == "data/working/issue19-admission-detail-master-workbench.csv"
            and row.get("来源家庭底线逐专业筛选表")
            == "data/working/issue19-family-fit-major-detail.csv"
            and row.get("来源结构保真登记表")
            == "data/working/issue19-admission-detail-structural-fidelity-register.csv"
            and row.get("数据阶段") == "issue19_candidate_filter_prep_major_detail"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("候选筛选可用状态")
            == "pending_pdf_official_attribute_family_transfer_review"
            and row.get("办学属性核验状态") == "pending_school_attribute_review"
            and row.get("公办民办初判") == "pending_school_attribute_review"
            and row.get("专业组出现ID") == master_row.get("专业组出现ID")
            and row.get("院校专业组代码OCR规范化")
            == master_row.get("院校专业组代码OCR规范化")
            and row.get("专业代号OCR") == master_row.get("专业代号OCR")
            and row.get("结构保真优先级") == structure_row.get("结构保真优先级")
            and row.get("PDF字段核验状态") == master_row.get("PDF原页证据状态")
            and row.get("湖北官方系统字段核验状态") == master_row.get("湖北官方平台字段核验状态")
            and row.get("高校官网/章程字段核验状态") == master_row.get("高校官网/章程辅证状态")
            and "不得进入最终志愿排序" in row.get("不得进入原因", "")
        )
    filter_prep_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [filter_prep_summary_path, filter_prep_csv]
    )
    checks.append(ok(
        "第 19 期逐专业候选筛选准备表摘要、行数和 pending 边界正确",
        filter_prep_summary.get("status") == "issue19_candidate_filter_prep_not_final"
        and filter_prep_summary.get("generated_by")
        == "build_issue19_candidate_filter_prep_major_detail.py"
        and filter_prep_summary.get("output_table")
        == "data/working/issue19-candidate-filter-prep-major-detail.csv"
        and filter_prep_summary.get("source_master_workbench")
        == "data/working/issue19-admission-detail-master-workbench.csv"
        and filter_prep_summary.get("source_family_fit_major")
        == "data/working/issue19-family-fit-major-detail.csv"
        and filter_prep_summary.get("source_structural_register")
        == "data/working/issue19-admission-detail-structural-fidelity-register.csv"
        and filter_prep_summary.get("row_count") == 13736
        and filter_prep_summary.get("unique_filter_prep_id_count") == 13736
        and filter_prep_summary.get("unique_major_line_id_count") == 13736
        and filter_prep_summary.get("missing_join_counts") == {}
        and filter_prep_summary.get("city_hit_counts") == {
            "北京": 456,
            "未命中当前城市偏好": 12013,
            "武汉": 835,
            "西安": 273,
            "成都": 159,
        }
        and filter_prep_summary.get("city_status_counts") == {
            "machine_school_name_keyword_unverified": 1723,
            "pending_school_location_review": 12013,
        }
        and filter_prep_summary.get("school_attribute_status_counts")
        == {"pending_school_attribute_review": 13736}
        and filter_prep_summary.get("tuition_over_budget_machine_counts") == {
            "false": 10612,
            "true": 1862,
            "pending_tuition_field_review": 1262,
        }
        and filter_prep_summary.get("campus_status_counts") == {
            "pending_campus_or_location_review": 8545,
            "machine_ocr_remark_candidate_unverified": 5191,
        }
        and filter_prep_summary.get("pdf_field_review_status_counts") == {
            "has_page_hash_pending_manual_pdf_review": 13736,
        }
        and filter_prep_summary.get("hubei_official_field_review_status_counts") == {
            "pending_hubei_official_plan_review": 13736,
        }
        and filter_prep_summary.get("school_source_review_status_counts") == {
            "not_yet_school_source_searched_in_full_workbench": 12882,
            "has_partial_source_needs_followup": 412,
            "has_reusable_2026_hubei_plan_source": 194,
            "官网专业名匹配但计划数冲突-优先核页": 18,
            "charter_or_rules_only_no_plan": 63,
            "needs_official_plan_source_search": 167,
        }
        and filter_prep_summary.get("final_available_count") == 0
        and filter_prep_summary.get("next_stage_available_count") == 0
        and filter_prep_summary.get("pending_school_attribute_review_count") == 13736,
        f"{len(filter_prep_rows)} filter prep rows",
    ))
    checks.append(ok(
        "第 19 期逐专业候选筛选准备表字段、主键和来源闭环正确",
        filter_prep_fields == expected_filter_prep_fields
        and len(filter_prep_rows) == 13736
        and len({row.get("候选筛选准备ID") for row in filter_prep_rows}) == 13736
        and {row.get("专业行ID") for row in filter_prep_rows}
        == {row.get("专业行ID") for row in admission_master_rows}
        and all(row.get("办学属性核验状态") == "pending_school_attribute_review" for row in filter_prep_rows)
        and all(row.get("PDF字段核验状态") == "has_page_hash_pending_manual_pdf_review" for row in filter_prep_rows)
        and all(row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review" for row in filter_prep_rows)
        and all(row.get("最终可用") == "false" and row.get("可进入下一阶段") == "false" for row in filter_prep_rows)
        and filter_prep_join_ok,
    ))
    checks.append(ok(
        "第 19 期逐专业候选筛选准备表公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(filter_prep_public_text) is None
        and "private/" not in filter_prep_public_text
        and "final_allowed" not in filter_prep_public_text
        and "ready_for_discussion" not in filter_prep_public_text
        and "已确认" not in filter_prep_public_text
        and "已核准" not in filter_prep_public_text
        and "最终推荐" not in filter_prep_public_text
        and "最终方案" not in filter_prep_public_text
        and "可填报" not in filter_prep_public_text
        and "可排序" not in filter_prep_public_text,
    ))

    decision_gates_summary_path = ROOT / "data/working/issue19-major-decision-readiness-gates-summary.json"
    decision_gates_csv = ROOT / "data/working/issue19-major-decision-readiness-gates.csv"
    decision_gates_summary = json.loads(decision_gates_summary_path.read_text())
    with decision_gates_csv.open(newline="", encoding="utf-8-sig") as f:
        decision_gates_reader = csv.DictReader(f)
        decision_gates_rows = list(decision_gates_reader)
        decision_gates_fields = decision_gates_reader.fieldnames or []
    expected_decision_gates_fields = script_list_constant(
        ROOT / "scripts/build_issue19_major_decision_readiness_gates.py",
        "FIELDS",
    )
    filter_prep_by_major_id = {row.get("专业行ID"): row for row in filter_prep_rows}
    decision_gates_join_ok = True
    for row in decision_gates_rows:
        major_id = row.get("专业行ID", "")
        filter_row = filter_prep_by_major_id.get(major_id, {})
        master_row = admission_master_by_major_id.get(major_id, {})
        structure_row = structural_by_major_id.get(major_id, {})
        decision_gates_join_ok = (
            decision_gates_join_ok
            and bool(filter_row)
            and bool(master_row)
            and bool(structure_row)
            and row.get("决策闸门ID") == stable_id("DECISIONGATE", [major_id])
            and row.get("来源候选筛选准备表")
            == "data/working/issue19-candidate-filter-prep-major-detail.csv"
            and row.get("来源单一逐专业招生明细总工作台")
            == "data/working/issue19-admission-detail-master-workbench.csv"
            and row.get("来源结构保真登记表")
            == "data/working/issue19-admission-detail-structural-fidelity-register.csv"
            and row.get("数据阶段") == "issue19_major_decision_readiness_gates"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("专业组出现ID") == master_row.get("专业组出现ID")
            and row.get("城市字段状态") == filter_row.get("城市字段状态")
            and row.get("办学属性核验状态") == "pending_school_attribute_review"
            and row.get("PDF字段核验状态") == "has_page_hash_pending_manual_pdf_review"
            and row.get("湖北官方系统字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("家庭接受度核验状态") == "pending_family_acceptance_review"
            and row.get("同组调剂结论") == "pending_transfer_decision"
            and row.get("结构保真优先级") == structure_row.get("结构保真优先级")
            and "不得进入志愿排序" in row.get("不得进入原因", "")
        )
    decision_gates_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [decision_gates_summary_path, decision_gates_csv]
    )
    checks.append(ok(
        "第 19 期逐专业决策闸门表摘要、行数和阻断门禁正确",
        decision_gates_summary.get("status") == "issue19_major_decision_readiness_gates_not_final"
        and decision_gates_summary.get("generated_by")
        == "build_issue19_major_decision_readiness_gates.py"
        and decision_gates_summary.get("output_table")
        == "data/working/issue19-major-decision-readiness-gates.csv"
        and decision_gates_summary.get("row_count") == 13736
        and decision_gates_summary.get("unique_gate_id_count") == 13736
        and decision_gates_summary.get("unique_major_line_id_count") == 13736
        and decision_gates_summary.get("missing_join_counts") == {}
        and decision_gates_summary.get("readiness_status_counts") == {
            "G2-字段缺口未闭环": 6218,
            "G1-家庭底线风险待确认": 2342,
            "G0-结构或归属未闭环": 4459,
            "G3-可作机器预筛线索但不可定案": 350,
            "G4-常规留存但不可定案": 367,
        }
        and decision_gates_summary.get("action_bucket_counts") == {
            "D2-计划学费选科字段先补": 6218,
            "D1-家庭底线风险先确认": 2342,
            "D0-结构归属和PDF原页先核": 4459,
            "D3-偏好专业线索优先核": 125,
            "D6-常规留存待了解": 367,
            "D4-城市偏好线索待位置核": 48,
            "D5-调剂风险先核": 177,
        }
        and decision_gates_summary.get("blocking_gate_counts", {}).get("PDF原页待核") == 13736
        and decision_gates_summary.get("blocking_gate_counts", {}).get("湖北官方系统待核") == 13736
        and decision_gates_summary.get("blocking_gate_counts", {}).get("办学属性待核") == 13736
        and decision_gates_summary.get("blocking_gate_counts", {}).get("家庭接受度待核") == 13736
        and decision_gates_summary.get("blocking_gate_counts", {}).get("同组调剂结论待核") == 13736
        and decision_gates_summary.get("pdf_field_review_status_counts") == {
            "has_page_hash_pending_manual_pdf_review": 13736,
        }
        and decision_gates_summary.get("hubei_official_field_review_status_counts") == {
            "pending_hubei_official_plan_review": 13736,
        }
        and decision_gates_summary.get("school_attribute_gate_counts") == {
            "pending_school_attribute_review": 13736,
        }
        and decision_gates_summary.get("family_acceptance_status_counts") == {
            "pending_family_acceptance_review": 13736,
        }
        and decision_gates_summary.get("transfer_decision_status_counts") == {
            "pending_transfer_decision": 13736,
        }
        and decision_gates_summary.get("final_available_count") == 0
        and decision_gates_summary.get("next_stage_available_count") == 0
        and decision_gates_summary.get("candidate_decision_allowed_count") == 0,
        f"{len(decision_gates_rows)} decision gate rows",
    ))
    checks.append(ok(
        "第 19 期逐专业决策闸门表字段、主键和来源闭环正确",
        decision_gates_fields == expected_decision_gates_fields
        and len(decision_gates_rows) == 13736
        and len({row.get("决策闸门ID") for row in decision_gates_rows}) == 13736
        and {row.get("专业行ID") for row in decision_gates_rows}
        == {row.get("专业行ID") for row in admission_master_rows}
        and all(row.get("最终可用") == "false" and row.get("可进入下一阶段") == "false" for row in decision_gates_rows)
        and decision_gates_join_ok,
    ))
    checks.append(ok(
        "第 19 期逐专业决策闸门表公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(decision_gates_public_text) is None
        and "private/" not in decision_gates_public_text
        and "final_allowed" not in decision_gates_public_text
        and "ready_for_discussion" not in decision_gates_public_text
        and "已确认" not in decision_gates_public_text
        and "已核准" not in decision_gates_public_text
        and "最终推荐" not in decision_gates_public_text
        and "最终方案" not in decision_gates_public_text
        and "可填报" not in decision_gates_public_text
        and "可排序" not in decision_gates_public_text,
    ))

    moe_source_page = ROOT / "data/official/moe-2025-national-higher-school-list/source-page.html"
    moe_xls = ROOT / "data/official/moe-2025-national-higher-school-list/national-regular-higher-schools-2025.xls"
    moe_normalized_summary_path = ROOT / "data/working/moe-2025-regular-higher-schools-summary.json"
    moe_normalized_csv = ROOT / "data/working/moe-2025-regular-higher-schools-normalized.csv"
    moe_attribute_summary_path = ROOT / "data/working/issue19-moe-school-attribute-major-detail-summary.json"
    moe_attribute_csv = ROOT / "data/working/issue19-moe-school-attribute-major-detail.csv"
    moe_unmatched_csv = ROOT / "data/working/issue19-moe-school-attribute-unmatched-schools.csv"
    moe_source_text = moe_source_page.read_text(encoding="utf-8", errors="ignore")
    moe_normalized_summary = json.loads(moe_normalized_summary_path.read_text())
    moe_attribute_summary = json.loads(moe_attribute_summary_path.read_text())
    with moe_normalized_csv.open(newline="", encoding="utf-8-sig") as f:
        moe_normalized_reader = csv.DictReader(f)
        moe_normalized_rows = list(moe_normalized_reader)
        moe_normalized_fields = moe_normalized_reader.fieldnames or []
    with moe_attribute_csv.open(newline="", encoding="utf-8-sig") as f:
        moe_attribute_reader = csv.DictReader(f)
        moe_attribute_rows = list(moe_attribute_reader)
        moe_attribute_fields = moe_attribute_reader.fieldnames or []
    with moe_unmatched_csv.open(newline="", encoding="utf-8-sig") as f:
        moe_unmatched_reader = csv.DictReader(f)
        moe_unmatched_rows = list(moe_unmatched_reader)
        moe_unmatched_fields = moe_unmatched_reader.fieldnames or []
    expected_moe_normalized_fields = script_list_constant(
        ROOT / "scripts/build_issue19_moe_school_attribute_major_detail.py",
        "NORMALIZED_FIELDS",
    )
    expected_moe_attribute_fields = script_list_constant(
        ROOT / "scripts/build_issue19_moe_school_attribute_major_detail.py",
        "MAJOR_FIELDS",
    )
    expected_moe_unmatched_fields = script_list_constant(
        ROOT / "scripts/build_issue19_moe_school_attribute_major_detail.py",
        "UNMATCHED_FIELDS",
    )
    moe_attribute_by_major_id = {row.get("专业行ID"): row for row in moe_attribute_rows}
    moe_attribute_join_ok = True
    for row in moe_attribute_rows:
        major_id = row.get("专业行ID", "")
        master_row = admission_master_by_major_id.get(major_id, {})
        filter_row = filter_prep_by_major_id.get(major_id, {})
        moe_attribute_join_ok = (
            moe_attribute_join_ok
            and bool(master_row)
            and bool(filter_row)
            and row.get("学校属性核验ID") == stable_id("MOEATTR", [major_id])
            and row.get("来源候选筛选准备表")
            == "data/working/issue19-candidate-filter-prep-major-detail.csv"
            and row.get("来源单一逐专业招生明细总工作台")
            == "data/working/issue19-admission-detail-master-workbench.csv"
            and row.get("来源教育部全国普通高等学校名单")
            == "data/official/moe-2025-national-higher-school-list/national-regular-higher-schools-2025.xls"
            and row.get("数据阶段") == "issue19_moe_school_attribute_major_detail"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("专业组出现ID") == master_row.get("专业组出现ID")
            and row.get("院校专业组代码OCR规范化")
            == master_row.get("院校专业组代码OCR规范化")
            and row.get("专业代号OCR") == master_row.get("专业代号OCR")
            and row.get("城市字段状态") == filter_row.get("城市字段状态")
            and row.get("校区字段状态") == filter_row.get("校区字段状态")
            and row.get("同组调剂结论") == "pending_transfer_decision"
            and "不能替代2026湖北招生计划" in row.get("不得进入原因", "")
        )
    moe_attribute_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            moe_normalized_summary_path,
            moe_normalized_csv,
            moe_attribute_summary_path,
            moe_attribute_csv,
            moe_unmatched_csv,
        ]
    )
    checks.append(ok(
        "教育部 2025 全国普通高等学校名单官方源已留存且计数正确",
        moe_source_page.exists()
        and moe_xls.exists()
        and sha256(moe_source_page)
        == "6e262bdd12284183d55f5979d212e7ca2f476fb27cb3df102e3eecb4facea48f"
        and sha256(moe_xls)
        == "af6f0192c29fb412b441fb55a13311479d08f861d68257960c5edb2e4dfb55af"
        and "截至2025年6月20日" in moe_source_text
        and "普通高等学校2919所" in moe_source_text
        and "本科学校1365所" in moe_source_text
        and "高职（专科）学校1554所" in moe_source_text
        and moe_normalized_summary.get("row_count") == 2919
        and moe_normalized_summary.get("undergraduate_count") == 1365
        and moe_normalized_summary.get("junior_college_count") == 1554
        and moe_normalized_summary.get("remark_counts", {}).get("民办") == 829
        and moe_normalized_summary.get("remark_counts", {}).get("中外合作办学及内地与港澳合作办学") == 14
        and len(moe_normalized_rows) == 2919,
        f"{len(moe_normalized_rows)} MOE rows",
    ))
    checks.append(ok(
        "教育部普通高校名单标准化表字段和主键正确",
        moe_normalized_fields == expected_moe_normalized_fields
        and len({row.get("教育部名单行ID") for row in moe_normalized_rows}) == 2919
        and len({row.get("学校名称") for row in moe_normalized_rows}) == 2919
        and len({row.get("学校标识码") for row in moe_normalized_rows}) == 2919
        and sum(row.get("办学层次") == "本科" for row in moe_normalized_rows) == 1365
        and sum(row.get("备注") == "民办" for row in moe_normalized_rows) == 829
        and any(
            row.get("学校名称") == "武汉东湖学院"
            and row.get("备注") == "民办"
            and row.get("省份分组") == "湖北省"
            for row in moe_normalized_rows
        ),
    ))
    checks.append(ok(
        "第 19 期逐专业教育部学校属性核验表摘要、行数和保守边界正确",
        moe_attribute_summary.get("status") == "issue19_moe_school_attribute_major_detail_not_final"
        and moe_attribute_summary.get("generated_by")
        == "build_issue19_moe_school_attribute_major_detail.py"
        and moe_attribute_summary.get("output_table")
        == "data/working/issue19-moe-school-attribute-major-detail.csv"
        and moe_attribute_summary.get("source_master_workbench")
        == "data/working/issue19-admission-detail-master-workbench.csv"
        and moe_attribute_summary.get("source_filter_prep")
        == "data/working/issue19-candidate-filter-prep-major-detail.csv"
        and moe_attribute_summary.get("source_moe_normalized")
        == "data/working/moe-2025-regular-higher-schools-normalized.csv"
        and moe_attribute_summary.get("row_count") == 13736
        and moe_attribute_summary.get("unique_attribute_id_count") == 13736
        and moe_attribute_summary.get("unique_major_line_id_count") == 13736
        and moe_attribute_summary.get("unique_school_code_name_count") == 1100
        and moe_attribute_summary.get("match_status_counts") == {
            "exact_school_name_match": 13161,
            "parent_school_name_match_location_not_campus": 190,
            "unmatched_needs_school_name_or_special_school_review": 385,
        }
        and moe_attribute_summary.get("matched_school_count_by_status") == {
            "exact_school_name_match": 1034,
            "parent_school_name_match_location_not_campus": 17,
            "unmatched_needs_school_name_or_special_school_review": 49,
        }
        and moe_attribute_summary.get("public_private_machine_signal_counts") == {
            "非民办线索-教育部名单未备注民办": 11087,
            "未匹配-待核": 385,
            "民办-教育部备注民办": 2230,
            "中外合作或港澳合作办学线索-教育部备注": 34,
        }
        and moe_attribute_summary.get("vocational_name_signal_count") == 241
        and moe_attribute_summary.get("unmatched_school_count") == 49
        and moe_attribute_summary.get("unmatched_major_line_count") == 385
        and moe_attribute_summary.get("final_available_count") == 0
        and moe_attribute_summary.get("next_stage_available_count") == 0
        and "备注为空" in moe_attribute_summary.get("public_private_boundary", ""),
        f"{len(moe_attribute_rows)} MOE attribute rows",
    ))
    checks.append(ok(
        "第 19 期逐专业教育部学校属性核验表字段、主键和逐专业来源闭环正确",
        moe_attribute_fields == expected_moe_attribute_fields
        and len(moe_attribute_rows) == 13736
        and len({row.get("学校属性核验ID") for row in moe_attribute_rows}) == 13736
        and {row.get("专业行ID") for row in moe_attribute_rows}
        == {row.get("专业行ID") for row in admission_master_rows}
        and all(row.get("最终可用") == "false" and row.get("可进入下一阶段") == "false" for row in moe_attribute_rows)
        and sum(row.get("教育部匹配状态") == "parent_school_name_match_location_not_campus" for row in moe_attribute_rows) == 190
        and all(
            "父校登记地线索" in row.get("所在地使用边界", "")
            for row in moe_attribute_rows
            if row.get("教育部匹配状态") == "parent_school_name_match_location_not_campus"
        )
        and all(
            row.get("家庭底线属性动作") == "默认不进主方案-民办线索"
            for row in moe_attribute_rows
            if row.get("公办民办机器线索") == "民办-教育部备注民办"
        )
        and all(
            row.get("办学属性核验状态") == "pending_school_name_or_special_school_review"
            for row in moe_attribute_rows
            if row.get("教育部匹配状态") == "unmatched_needs_school_name_or_special_school_review"
        )
        and any(
            row.get("院校名称OCR") == "电子科技大学（沙河校区）"
            and row.get("教育部匹配学校名称") == "电子科技大学"
            and row.get("教育部匹配状态") == "parent_school_name_match_location_not_campus"
            for row in moe_attribute_rows
        )
        and any(
            row.get("院校名称OCR") == "武汉东湖学院"
            and row.get("公办民办机器线索") == "民办-教育部备注民办"
            for row in moe_attribute_rows
        )
        and moe_attribute_join_ok,
    ))
    checks.append(ok(
        "第 19 期教育部未匹配学校支持清单字段、行数和待核边界正确",
        moe_unmatched_fields == expected_moe_unmatched_fields
        and len(moe_unmatched_rows) == 49
        and {
            (row.get("院校代码"), row.get("院校名称OCR"))
            for row in moe_unmatched_rows
        } == {
            (row.get("院校代码"), row.get("院校名称OCR"))
            for row in moe_attribute_rows
            if row.get("教育部匹配状态")
            == "unmatched_needs_school_name_or_special_school_review"
        }
        and any(row.get("院校名称OCR") == "复且大学医学院" for row in moe_unmatched_rows)
        and any(row.get("院校名称OCR") == "北师香港浸会大学" for row in moe_unmatched_rows)
        and any("职业本科" in row.get("疑似风险类型", "") for row in moe_unmatched_rows),
    ))
    checks.append(ok(
        "第 19 期教育部学校属性公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(moe_attribute_public_text) is None
        and "private/" not in moe_attribute_public_text
        and "final_allowed" not in moe_attribute_public_text
        and "ready_for_discussion" not in moe_attribute_public_text
        and "已确认" not in moe_attribute_public_text
        and "已核准" not in moe_attribute_public_text
        and "最终推荐" not in moe_attribute_public_text
        and "最终方案" not in moe_attribute_public_text
        and "可填报" not in moe_attribute_public_text
        and "可排序" not in moe_attribute_public_text,
    ))

    official_collision_summary_path = ROOT / "data/working/issue19-hubei-official-query-key-collision-summary.json"
    official_collision_csv = ROOT / "data/working/issue19-hubei-official-query-key-collision-ledger.csv"
    official_collision_summary = json.loads(official_collision_summary_path.read_text())
    with official_collision_csv.open(newline="", encoding="utf-8-sig") as f:
        official_collision_reader = csv.DictReader(f)
        official_collision_rows = list(official_collision_reader)
        official_collision_fields = official_collision_reader.fieldnames or []
    expected_official_collision_fields = script_list_constant(
        ROOT / "scripts/build_issue19_hubei_official_query_key_collision_ledger.py",
        "FIELDS",
    )
    hubei_official_by_major_id = {row.get("专业行ID"): row for row in hubei_official_rows}
    official_collision_join_ok = True
    for row in official_collision_rows:
        major_id = row.get("专业行ID", "")
        official_row = hubei_official_by_major_id.get(major_id, {})
        official_collision_join_ok = (
            official_collision_join_ok
            and bool(official_row)
            and row.get("官方查询键碰撞ID")
            == stable_id("OFFICIALKEYCOLLISION", [row.get("碰撞键", ""), major_id])
            and row.get("来源湖北官方系统逐专业核验包")
            == "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"
            and row.get("数据阶段") == "issue19_hubei_official_query_key_collision_ledger"
            and row.get("主表粒度") == "逐专业招生明细×官方查询键碰撞"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("平台字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("专业组出现ID") == official_row.get("专业组出现ID")
            and row.get("平台查询院校代码") == official_row.get("平台查询院校代码")
            and row.get("平台查询专业组代码") == official_row.get("平台查询专业组代码")
            and row.get("平台查询专业代号") == official_row.get("平台查询专业代号")
            and "不得只按院校代码+专业组代码+专业代号合并" in row.get("消歧要求", "")
        )
    official_collision_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [official_collision_summary_path, official_collision_csv]
    )
    checks.append(ok(
        "第 19 期湖北官方查询键碰撞清单摘要和行数正确",
        official_collision_summary.get("status") == "issue19_hubei_official_query_key_collision_not_final"
        and official_collision_summary.get("generated_by")
        == "build_issue19_hubei_official_query_key_collision_ledger.py"
        and official_collision_summary.get("output_table")
        == "data/working/issue19-hubei-official-query-key-collision-ledger.csv"
        and official_collision_summary.get("source_hubei_official_packets")
        == "data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv"
        and official_collision_summary.get("source_row_count") == 13736
        and official_collision_summary.get("collision_key_count") == 59
        and official_collision_summary.get("collision_row_count") == 118
        and official_collision_summary.get("unique_collision_id_count") == 118
        and official_collision_summary.get("unique_major_line_id_count") == 118
        and official_collision_summary.get("collision_size_counts") == {"2": 59}
        and official_collision_summary.get("platform_field_review_status_counts") == {
            "pending_hubei_official_plan_review": 118,
        }
        and official_collision_summary.get("final_available_count") == 0
        and official_collision_summary.get("next_stage_available_count") == 0,
        f"{len(official_collision_rows)} collision rows",
    ))
    checks.append(ok(
        "第 19 期湖北官方查询键碰撞清单字段、主键和消歧门禁正确",
        official_collision_fields == expected_official_collision_fields
        and len(official_collision_rows) == 118
        and len({row.get("官方查询键碰撞ID") for row in official_collision_rows}) == 118
        and len({row.get("碰撞键") for row in official_collision_rows}) == 59
        and all(row.get("最终可用") == "false" and row.get("可进入下一阶段") == "false" for row in official_collision_rows)
        and official_collision_join_ok,
    ))
    checks.append(ok(
        "第 19 期湖北官方查询键碰撞清单公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(official_collision_public_text) is None
        and "private/" not in official_collision_public_text
        and "final_allowed" not in official_collision_public_text
        and "ready_for_discussion" not in official_collision_public_text
        and "已确认" not in official_collision_public_text
        and "已核准" not in official_collision_public_text
        and "最终推荐" not in official_collision_public_text
        and "最终方案" not in official_collision_public_text
        and "可填报" not in official_collision_public_text
        and "可排序" not in official_collision_public_text,
    ))

    stability_dashboard_summary_path = ROOT / "data/working/issue19-foundation-stability-dashboard-summary.json"
    stability_dashboard_csv = ROOT / "data/working/issue19-foundation-stability-dashboard.csv"
    unmatched_resolution_summary_path = ROOT / "data/working/issue19-moe-unmatched-school-resolution-summary.json"
    unmatched_resolution_csv = ROOT / "data/working/issue19-moe-unmatched-school-resolution-major-detail.csv"
    stability_dashboard_summary = json.loads(stability_dashboard_summary_path.read_text())
    unmatched_resolution_summary = json.loads(unmatched_resolution_summary_path.read_text())
    with stability_dashboard_csv.open(newline="", encoding="utf-8-sig") as f:
        stability_dashboard_reader = csv.DictReader(f)
        stability_dashboard_rows = list(stability_dashboard_reader)
        stability_dashboard_fields = stability_dashboard_reader.fieldnames or []
    with unmatched_resolution_csv.open(newline="", encoding="utf-8-sig") as f:
        unmatched_resolution_reader = csv.DictReader(f)
        unmatched_resolution_rows = list(unmatched_resolution_reader)
        unmatched_resolution_fields = unmatched_resolution_reader.fieldnames or []
    expected_stability_dashboard_fields = script_list_constant(
        ROOT / "scripts/build_issue19_foundation_stability_dashboard.py",
        "STABILITY_FIELDS",
    )
    expected_unmatched_resolution_fields = script_list_constant(
        ROOT / "scripts/build_issue19_foundation_stability_dashboard.py",
        "UNMATCHED_RESOLUTION_FIELDS",
    )

    decision_gates_by_major_id = {row.get("专业行ID"): row for row in decision_gates_rows}
    b0_b1_diff_by_major_id_for_stability = {
        row.get("专业行ID"): row for row in b0_b1_diff_rows
    }
    field_candidate_rows_by_major_id = defaultdict(list)
    for row in field_gap_candidate_rows:
        field_candidate_rows_by_major_id[row.get("专业行ID")].append(row)
    structural_event_rows_by_major_id = defaultdict(list)
    for row in structural_event_rows:
        structural_event_rows_by_major_id[row.get("专业行ID")].append(row)
    official_collision_rows_by_major_id = defaultdict(list)
    for row in official_collision_rows:
        official_collision_rows_by_major_id[row.get("专业行ID")].append(row)

    stability_join_ok = True
    for row in stability_dashboard_rows:
        major_id = row.get("专业行ID", "")
        master_row = admission_master_by_major_id.get(major_id, {})
        release_row = foundation_release_by_major_id.get(major_id, {})
        decision_row = decision_gates_by_major_id.get(major_id, {})
        gap_row = gap_scorecard_by_major_id.get(major_id, {})
        moe_row = moe_attribute_by_major_id.get(major_id, {})
        official_row = hubei_official_by_major_id.get(major_id, {})
        anchor_row = anchor_by_major_id.get(major_id, {})
        history_row = historical_sidecar_by_major_id.get(major_id, {})
        field_rows = field_candidate_rows_by_major_id.get(major_id, [])
        structural_events = structural_event_rows_by_major_id.get(major_id, [])
        official_collisions = official_collision_rows_by_major_id.get(major_id, [])
        stability_join_ok = (
            stability_join_ok
            and bool(master_row)
            and bool(release_row)
            and bool(decision_row)
            and bool(gap_row)
            and bool(moe_row)
            and bool(official_row)
            and bool(anchor_row)
            and bool(history_row)
            and row.get("底座稳定性看板ID") == stable_id("STABILITY", [major_id])
            and row.get("数据阶段") == "issue19_foundation_stability_dashboard"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("专业组出现ID") == master_row.get("专业组出现ID")
            and row.get("院校专业组代码OCR规范化")
            == master_row.get("院校专业组代码OCR规范化")
            and row.get("PDF原页锚点状态") == anchor_row.get("证据锚点状态")
            and row.get("湖北官方平台字段核验状态") == official_row.get("平台字段核验状态")
            and row.get("教育部匹配状态") == moe_row.get("教育部匹配状态")
            and row.get("教育部属性闸门等级") == moe_row.get("属性闸门等级")
            and row.get("候选初筛闸门状态") == decision_row.get("候选初筛闸门状态")
            and row.get("闭环执行批次") == gap_row.get("闭环执行批次")
            and row.get("看板动作桶") == gap_row.get("看板动作桶")
            and row.get("三年投档稳定性状态") == release_row.get("三年投档稳定性状态")
            and row.get("家庭接受度结论") == "pending_family_acceptance_review"
            and row.get("同组调剂结论") == "pending_transfer_decision"
            and row.get("湖北官方查询键是否碰撞") == ("true" if official_collisions else "false")
            and as_int(row.get("字段候选任务数")) == len(field_rows)
            and as_int(row.get("非空字段候选数"))
            == sum(1 for field_row in field_rows if field_row.get("候选值"))
            and as_int(row.get("结构风险事件数")) == len(structural_events)
            and row.get("B0B1官网差异任务数")
            == release_row.get("B0B1官网差异任务数")
        )
    stability_dashboard_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            stability_dashboard_summary_path,
            stability_dashboard_csv,
            unmatched_resolution_summary_path,
            unmatched_resolution_csv,
        ]
    )
    checks.append(ok(
        "第 19 期底座稳定性总看板摘要、行数和分布正确",
        stability_dashboard_summary.get("status")
        == "issue19_foundation_stability_dashboard_not_final"
        and stability_dashboard_summary.get("generated_by")
        == "build_issue19_foundation_stability_dashboard.py"
        and stability_dashboard_summary.get("output_table")
        == "data/working/issue19-foundation-stability-dashboard.csv"
        and stability_dashboard_summary.get("row_count") == 13736
        and stability_dashboard_summary.get("unique_stability_id_count") == 13736
        and stability_dashboard_summary.get("unique_major_line_id_count") == 13736
        and stability_dashboard_summary.get("unique_group_occurrence_id_count") == 3289
        and stability_dashboard_summary.get("unique_school_code_name_count") == 1100
        and stability_dashboard_summary.get("stability_level_counts") == {
            "B2-字段缺口补证优先": 5962,
            "B1-P0原页或官网冲突优先": 4370,
            "B3-三方官方闭环待核": 542,
            "B0-校名/结构/官方查询键强阻断": 2663,
            "B4-低风险抽检但仍非最终": 199,
        }
        and stability_dashboard_summary.get("foundation_batch_counts") == {
            "C1-字段缺口先补": 7608,
            "C0-P0证据闭环先核": 5310,
            "C3-常规三方证据闭环": 609,
            "C4-低风险抽检但非最终": 209,
        }
        and stability_dashboard_summary.get("scorecard_action_bucket_counts") == {
            "S4-字段缺口无候选需原页重读": 3360,
            "S2-P0原页结构和字段先核": 5176,
            "S3-字段缺口有候选先核": 4248,
            "S6-常规三方闭环": 609,
            "S1-P0原页+官网辅证同步核": 116,
            "S0-B0B1冲突+P0原页优先": 18,
            "S8-低风险抽检": 207,
            "S7-低风险但证据锚点异常抽检": 2,
        }
        and stability_dashboard_summary.get("moe_match_status_counts") == {
            "exact_school_name_match": 13161,
            "parent_school_name_match_location_not_campus": 190,
            "unmatched_needs_school_name_or_special_school_review": 385,
        }
        and stability_dashboard_summary.get("official_status_counts") == {
            "pending_hubei_official_plan_review": 13736,
        }
        and stability_dashboard_summary.get("structural_risk_major_line_count") == 2334
        and stability_dashboard_summary.get("official_query_collision_major_line_count") == 118
        and stability_dashboard_summary.get("unmatched_moe_major_line_count") == 385
        and stability_dashboard_summary.get("b0_b1_diff_major_line_count") == 854
        and stability_dashboard_summary.get("final_available_count") == 0
        and stability_dashboard_summary.get("next_stage_available_count") == 0
        and len(stability_dashboard_rows) == 13736,
        f"{len(stability_dashboard_rows)} stability rows",
    ))
    checks.append(ok(
        "第 19 期底座稳定性总看板字段、主键和逐专业来源闭环正确",
        stability_dashboard_fields == expected_stability_dashboard_fields
        and len({row.get("底座稳定性看板ID") for row in stability_dashboard_rows}) == 13736
        and {row.get("专业行ID") for row in stability_dashboard_rows}
        == {row.get("专业行ID") for row in admission_master_rows}
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("湖北官方平台字段核验状态") == "pending_hubei_official_plan_review"
            and row.get("家庭接受度结论") == "pending_family_acceptance_review"
            and row.get("同组调剂结论") == "pending_transfer_decision"
            for row in stability_dashboard_rows
        )
        and Counter(row.get("底座稳定性等级") for row in stability_dashboard_rows)
        == Counter(stability_dashboard_summary.get("stability_level_counts", {}))
        and sum(as_int(row.get("字段候选任务数")) for row in stability_dashboard_rows) == 19065
        and sum(as_int(row.get("非空字段候选数")) for row in stability_dashboard_rows) == 7621
        and stability_join_ok,
    ))

    unmatched_resolution_join_ok = True
    for row in unmatched_resolution_rows:
        major_id = row.get("专业行ID", "")
        moe_row = moe_attribute_by_major_id.get(major_id, {})
        history_row = historical_sidecar_by_major_id.get(major_id, {})
        unmatched_resolution_join_ok = (
            unmatched_resolution_join_ok
            and bool(moe_row)
            and bool(history_row)
            and moe_row.get("教育部匹配状态")
            == "unmatched_needs_school_name_or_special_school_review"
            and row.get("未匹配校名解析ID") == stable_id("UNMATCHEDSCHOOL", [major_id])
            and row.get("数据阶段")
            == "issue19_moe_unmatched_school_resolution_major_detail"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器能否自动替换校名") == "false"
            and row.get("专业组出现ID") == moe_row.get("专业组出现ID")
            and row.get("院校代码") == moe_row.get("院校代码")
            and row.get("院校名称OCR") == moe_row.get("院校名称OCR")
            and "不能自动替换2026招生计划校名" in row.get("不得进入原因", "")
        )
    checks.append(ok(
        "第 19 期教育部未匹配校名逐专业解析表摘要、行数和 pending 边界正确",
        unmatched_resolution_summary.get("status")
        == "issue19_moe_unmatched_school_resolution_major_detail_not_final"
        and unmatched_resolution_summary.get("generated_by")
        == "build_issue19_foundation_stability_dashboard.py"
        and unmatched_resolution_summary.get("output_table")
        == "data/working/issue19-moe-unmatched-school-resolution-major-detail.csv"
        and unmatched_resolution_summary.get("row_count") == 385
        and unmatched_resolution_summary.get("unique_resolution_id_count") == 385
        and unmatched_resolution_summary.get("unique_major_line_id_count") == 385
        and unmatched_resolution_summary.get("unique_school_code_name_count") == 49
        and unmatched_resolution_summary.get("candidate_level_counts") == {
            "R2-有历史同代码校名候选，需核2026是否更名或组号沿用": 80,
            "R4-暂无可靠机器候选，必须回看PDF原页和官方系统": 4,
            "R2-历史同代码候选与教育部相似候选交叉命中": 97,
            "R0-特殊院校或港澳台主体，教育部普通高校名单可能不覆盖": 28,
            "R1-校名截断，优先用历史同代码候选和PDF原页核名": 110,
            "R1-职业本科/职业大学线索，必须核2026计划和招生章程": 28,
            "R3-仅有教育部相似校名候选，需人工核OCR": 38,
        }
        and unmatched_resolution_summary.get("historical_candidate_major_line_count") == 281
        and unmatched_resolution_summary.get("similar_moe_candidate_major_line_count") == 232
        and unmatched_resolution_summary.get("ocr_rule_candidate_major_line_count") == 90
        and unmatched_resolution_summary.get("auto_replace_allowed_count") == 0
        and unmatched_resolution_summary.get("final_available_count") == 0
        and unmatched_resolution_summary.get("next_stage_available_count") == 0
        and len(unmatched_resolution_rows) == 385,
        f"{len(unmatched_resolution_rows)} unmatched resolution rows",
    ))
    checks.append(ok(
        "第 19 期教育部未匹配校名逐专业解析表字段、主键和核名线索边界正确",
        unmatched_resolution_fields == expected_unmatched_resolution_fields
        and len({row.get("未匹配校名解析ID") for row in unmatched_resolution_rows}) == 385
        and {row.get("专业行ID") for row in unmatched_resolution_rows}
        == {
            row.get("专业行ID")
            for row in moe_attribute_rows
            if row.get("教育部匹配状态")
            == "unmatched_needs_school_name_or_special_school_review"
        }
        and all(row.get("机器能否自动替换校名") == "false" for row in unmatched_resolution_rows)
        and any(
            row.get("院校代码") == "A201"
            and row.get("院校名称OCR") == "应急管理大学"
            and "华北科技学院" in row.get("历史同代码校名候选", "")
            for row in unmatched_resolution_rows
        )
        and any(
            row.get("院校代码") == "F487"
            and row.get("院校名称OCR") == "东北財经大学"
            and "东北财经大学" in row.get("OCR规则修正候选", "")
            for row in unmatched_resolution_rows
        )
        and any(
            row.get("院校代码") == "H857"
            and row.get("院校名称OCR") == "北师香港浸会大学"
            and row.get("候选综合等级")
            == "R0-特殊院校或港澳台主体，教育部普通高校名单可能不覆盖"
            for row in unmatched_resolution_rows
        )
        and unmatched_resolution_join_ok,
    ))
    checks.append(ok(
        "第 19 期底座稳定性新增公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(stability_dashboard_public_text) is None
        and "private/" not in stability_dashboard_public_text
        and "final_allowed" not in stability_dashboard_public_text
        and "ready_for_discussion" not in stability_dashboard_public_text
        and "已确认" not in stability_dashboard_public_text
        and "已核准" not in stability_dashboard_public_text
        and "最终推荐" not in stability_dashboard_public_text
        and "最终方案" not in stability_dashboard_public_text
        and "可填报" not in stability_dashboard_public_text
        and "可排序" not in stability_dashboard_public_text,
    ))

    stabilization_tasks_summary_path = ROOT / "data/working/issue19-foundation-stabilization-major-detail-tasks-summary.json"
    stabilization_tasks_csv = ROOT / "data/working/issue19-foundation-stabilization-major-detail-tasks.csv"
    official_public_entry_status_path = ROOT / "data/working/issue19-official-public-entry-status.json"
    admission_plan_source_status_path = ROOT / "data/working/2026-admission-plan-source-status.json"
    stabilization_tasks_summary = json.loads(stabilization_tasks_summary_path.read_text())
    official_public_entry_status = json.loads(official_public_entry_status_path.read_text())
    admission_plan_source_status = json.loads(admission_plan_source_status_path.read_text())
    with stabilization_tasks_csv.open(newline="", encoding="utf-8-sig") as f:
        stabilization_tasks_reader = csv.DictReader(f)
        stabilization_tasks_rows = list(stabilization_tasks_reader)
        stabilization_tasks_fields = stabilization_tasks_reader.fieldnames or []
    expected_stabilization_tasks_fields = script_list_constant(
        ROOT / "scripts/build_issue19_foundation_stabilization_major_detail_tasks.py",
        "FIELDS",
    )
    stability_dashboard_by_major_id = {row.get("专业行ID"): row for row in stability_dashboard_rows}
    stabilization_target_major_ids = {
        row.get("专业行ID")
        for row in stability_dashboard_rows
        if row.get("底座稳定性等级")
        in {
            "B0-校名/结构/官方查询键强阻断",
            "B1-P0原页或官网冲突优先",
            "B2-字段缺口补证优先",
        }
    }
    stabilization_join_ok = True
    for row in stabilization_tasks_rows:
        major_id = row.get("专业行ID", "")
        stability_row = stability_dashboard_by_major_id.get(major_id, {})
        gap_row = gap_scorecard_by_major_id.get(major_id, {})
        anchor_row = anchor_by_major_id.get(major_id, {})
        history_row = historical_sidecar_by_major_id.get(major_id, {})
        field_rows = field_candidate_rows_by_major_id.get(major_id, [])
        diff_rows = b0_b1_diff_by_major_id_for_stability.get(major_id)
        structural_events = structural_event_rows_by_major_id.get(major_id, [])
        official_collisions = official_collision_rows_by_major_id.get(major_id, [])
        stabilization_join_ok = (
            stabilization_join_ok
            and bool(stability_row)
            and bool(gap_row)
            and bool(anchor_row)
            and bool(history_row)
            and row.get("稳定化逐专业任务ID") == stable_id("STABILIZEMAJOR", [major_id])
            and row.get("底座稳定性看板ID") == stability_row.get("底座稳定性看板ID")
            and row.get("闭环缺口看板ID") == gap_row.get("闭环缺口看板ID")
            and row.get("专业行原页证据锚点ID") == anchor_row.get("专业行原页证据锚点ID")
            and row.get("三年投档旁挂ID") == history_row.get("三年投档旁挂ID")
            and row.get("数据阶段") == "issue19_foundation_stabilization_major_detail_tasks"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("任务粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("湖北官方平台字段核验状态")
            == "pending_hubei_official_plan_review"
            and row.get("家庭接受度结论") == "pending_family_acceptance_review"
            and row.get("同组调剂结论") == "pending_transfer_decision"
            and as_int(row.get("字段候选任务数")) == len(field_rows)
            and as_int(row.get("非空字段候选数"))
            == sum(1 for field_row in field_rows if field_row.get("候选值"))
            and as_int(row.get("B0B1官网差异任务数")) == (1 if diff_rows else 0)
            and as_int(row.get("结构风险事件数")) == len(structural_events)
            and row.get("湖北官方查询键是否碰撞") == ("true" if official_collisions else "false")
            and "未闭环前不得用于志愿推荐" in row.get("保真校验规则集合", "")
        )
    stabilization_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            stabilization_tasks_summary_path,
            stabilization_tasks_csv,
            official_public_entry_status_path,
            admission_plan_source_status_path,
        ]
    )
    checks.append(ok(
        "第 19 期逐专业稳定化任务表摘要、行数和分布正确",
        stabilization_tasks_summary.get("status")
        == "issue19_foundation_stabilization_major_detail_tasks_not_final"
        and stabilization_tasks_summary.get("generated_by")
        == "build_issue19_foundation_stabilization_major_detail_tasks.py"
        and stabilization_tasks_summary.get("output_table")
        == "data/working/issue19-foundation-stabilization-major-detail-tasks.csv"
        and stabilization_tasks_summary.get("row_grain") == "逐专业招生明细"
        and stabilization_tasks_summary.get("task_grain") == "逐专业招生明细"
        and stabilization_tasks_summary.get("row_count") == 12995
        and stabilization_tasks_summary.get("unique_task_id_count") == 12995
        and stabilization_tasks_summary.get("unique_major_line_id_count") == 12995
        and stabilization_tasks_summary.get("unique_group_occurrence_id_count") == 3081
        and stabilization_tasks_summary.get("unique_school_code_name_count") == 1098
        and stabilization_tasks_summary.get("stability_level_counts") == {
            "B2-字段缺口补证优先": 5962,
            "B1-P0原页或官网冲突优先": 4370,
            "B0-校名/结构/官方查询键强阻断": 2663,
        }
        and stabilization_tasks_summary.get("task_priority_counts") == {
            "P1-字段缺口逐专业补证": 5962,
            "P0-原页或官网冲突逐专业核验": 4370,
            "P0-强阻断逐专业核验": 2663,
        }
        and stabilization_tasks_summary.get("scorecard_action_bucket_counts") == {
            "S4-字段缺口无候选需原页重读": 3360,
            "S2-P0原页结构和字段先核": 5176,
            "S3-字段缺口有候选先核": 4248,
            "S6-常规三方闭环": 67,
            "S1-P0原页+官网辅证同步核": 116,
            "S0-B0B1冲突+P0原页优先": 18,
            "S8-低风险抽检": 8,
            "S7-低风险但证据锚点异常抽检": 2,
        }
        and stabilization_tasks_summary.get("field_gap_major_line_count") == 12473
        and stabilization_tasks_summary.get("field_candidate_task_count") == 19065
        and stabilization_tasks_summary.get("non_empty_field_candidate_count") == 7621
        and stabilization_tasks_summary.get("b0_b1_official_diff_major_line_count") == 854
        and stabilization_tasks_summary.get("structural_risk_major_line_count") == 2334
        and stabilization_tasks_summary.get("official_query_collision_major_line_count") == 118
        and stabilization_tasks_summary.get("unmatched_school_resolution_major_line_count") == 385
        and stabilization_tasks_summary.get("auto_writeback_allowed_count") == 0
        and stabilization_tasks_summary.get("recommendation_basis_allowed_count") == 0
        and stabilization_tasks_summary.get("final_available_count") == 0
        and stabilization_tasks_summary.get("next_stage_available_count") == 0
        and len(stabilization_tasks_rows) == 12995,
        f"{len(stabilization_tasks_rows)} stabilization rows",
    ))
    checks.append(ok(
        "第 19 期逐专业稳定化任务表字段、主键和保真边界正确",
        stabilization_tasks_fields == expected_stabilization_tasks_fields
        and len({row.get("稳定化逐专业任务ID") for row in stabilization_tasks_rows}) == 12995
        and {row.get("专业行ID") for row in stabilization_tasks_rows}
        == stabilization_target_major_ids
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            for row in stabilization_tasks_rows
        )
        and Counter(row.get("底座稳定性等级") for row in stabilization_tasks_rows)
        == Counter(stabilization_tasks_summary.get("stability_level_counts", {}))
        and sum(as_int(row.get("字段候选任务数")) or 0 for row in stabilization_tasks_rows) == 19065
        and sum(as_int(row.get("非空字段候选数")) or 0 for row in stabilization_tasks_rows) == 7621
        and sum(1 for row in stabilization_tasks_rows if row.get("专业行原页证据锚点ID")) == 12995
        and sum(1 for row in stabilization_tasks_rows if row.get("三年投档旁挂ID")) == 12995
        and stabilization_join_ok,
    ))
    checks.append(ok(
        "第 19 期官方公开入口状态快照边界正确",
        official_public_entry_status.get("status")
        == "issue19_official_public_entry_status_not_final"
        and official_public_entry_status.get("generated_by")
        == "build_issue19_official_public_entry_status_snapshot.py"
        and official_public_entry_status.get("checked_at") == "2026-06-27"
        and official_public_entry_status.get("official_plan_page", {}).get("sha256")
        == "5c56b9582418af6e1cfbd40431920a0fee28807492c6be30b972d118251e8776"
        and official_public_entry_status.get("official_plan_page", {}).get("contains_waiting_notice") is True
        and official_public_entry_status.get("official_plan_index", {}).get("sha256")
        == "804a6e806629cc772677360c074fd5760796682ab0c88108be7ddfae773eaf50"
        and official_public_entry_status.get("official_plan_index", {}).get("contains_2026_plan_link") is True
        and all(
            probe.get("is_unauthenticated_blocked") is True
            for probe in official_public_entry_status.get("zspt_platform", {}).get("unauthenticated_probe_results", [])
        )
        and admission_plan_source_status.get("last_updated") == "2026-06-27"
        and admission_plan_source_status.get("zspt_platform", {}).get("status_snapshot")
        == "data/working/issue19-official-public-entry-status.json",
    ))
    checks.append(ok(
        "第 19 期逐专业稳定化和官方入口新增公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(stabilization_public_text) is None
        and "private/" not in stabilization_public_text
        and "/Users/" not in stabilization_public_text
        and "final_allowed" not in stabilization_public_text
        and "ready_for_discussion" not in stabilization_public_text
        and "已确认" not in stabilization_public_text
        and "已核准" not in stabilization_public_text
        and "最终推荐" not in stabilization_public_text
        and "最终方案" not in stabilization_public_text
        and "可填报" not in stabilization_public_text
        and "可排序" not in stabilization_public_text,
    ))

    raw_lineage_summary_path = ROOT / "data/working/issue19-raw-major-lineage-consistency-audit-summary.json"
    raw_lineage_csv = ROOT / "data/working/issue19-raw-major-lineage-consistency-audit.csv"
    raw_lineage_summary = json.loads(raw_lineage_summary_path.read_text())
    with raw_lineage_csv.open(newline="", encoding="utf-8-sig") as f:
        raw_lineage_reader = csv.DictReader(f)
        raw_lineage_rows = list(raw_lineage_reader)
        raw_lineage_fields = raw_lineage_reader.fieldnames or []
    expected_raw_lineage_fields = script_list_constant(
        ROOT / "scripts/build_issue19_raw_major_lineage_consistency_audit.py",
        "FIELDS",
    )
    raw_lineage_by_major_id = {row.get("专业行ID"): row for row in raw_lineage_rows}
    quality_by_raw_line = {
        as_int(row.get("专业明细源行号")) - 1: row
        for row in major_quality_rows
        if as_int(row.get("专业明细源行号")) is not None
    }
    raw_lineage_join_ok = True
    for raw_index, raw_row in enumerate(full_major_rows, start=1):
        quality_row = quality_by_raw_line.get(raw_index, {})
        major_id = quality_row.get("专业行ID", "")
        lineage_row = raw_lineage_by_major_id.get(major_id, {})
        release_row = foundation_release_by_major_id.get(major_id, {})
        master_row = admission_master_by_major_id.get(major_id, {})
        structural_row = structural_by_major_id.get(major_id, {})
        stability_row = stability_dashboard_by_major_id.get(major_id, {})
        anchor_row = anchor_by_major_id.get(major_id, {})
        history_row = historical_sidecar_by_major_id.get(major_id, {})
        gap_row = gap_scorecard_by_major_id.get(major_id, {})
        field_rows = field_candidate_rows_by_major_id.get(major_id, [])
        structural_events = structural_event_rows_by_major_id.get(major_id, [])
        official_collisions = official_collision_rows_by_major_id.get(major_id, [])
        raw_lineage_join_ok = (
            raw_lineage_join_ok
            and bool(lineage_row)
            and bool(quality_row)
            and bool(release_row)
            and bool(master_row)
            and bool(structural_row)
            and bool(stability_row)
            and bool(anchor_row)
            and bool(history_row)
            and bool(gap_row)
            and lineage_row.get("原始专业行血缘审计ID")
            == stable_id("RAWLINEAGE", [major_id, issue19_source["source"]["sha256"]])
            and lineage_row.get("数据阶段") == "issue19_raw_major_lineage_consistency_audit"
            and lineage_row.get("主表粒度") == "逐专业招生明细"
            and lineage_row.get("最终可用") == "false"
            and lineage_row.get("可进入下一阶段") == "false"
            and lineage_row.get("机器是否允许自动写回主表") == "false"
            and lineage_row.get("是否允许作为志愿推荐依据") == "false"
            and lineage_row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and lineage_row.get("原始CSV数据行号") == str(raw_index)
            and lineage_row.get("专业明细源行号") == str(raw_index + 1)
            and lineage_row.get("专业行ID") == major_id
            and lineage_row.get("专业组出现ID") == quality_row.get("专业组出现ID")
            and lineage_row.get("院校代码") == raw_row.get("院校代码")
            and lineage_row.get("院校名称OCR") == raw_row.get("院校名称OCR")
            and lineage_row.get("院校专业组代码OCR规范化")
            == raw_row.get("院校专业组代码OCR规范化")
            and lineage_row.get("专业组号OCR") == raw_row.get("专业组号OCR")
            and lineage_row.get("专业组标题OCR原文") == raw_row.get("专业组标题OCR原文")
            and lineage_row.get("来源页码") == raw_row.get("来源页码")
            and lineage_row.get("版面列") == raw_row.get("版面列")
            and lineage_row.get("专业组标题行号") == raw_row.get("专业组标题行号")
            and lineage_row.get("专业组标题y") == raw_row.get("专业组标题y")
            and lineage_row.get("专业起始行号") == raw_row.get("专业起始行号")
            and lineage_row.get("专业起始y") == raw_row.get("专业起始y")
            and lineage_row.get("专业代号OCR") == raw_row.get("专业代号OCR")
            and lineage_row.get("专业名称及备注OCR") == raw_row.get("专业名称及备注OCR")
            and lineage_row.get("再选科目OCR候选") == raw_row.get("再选科目OCR候选")
            and lineage_row.get("专业计划数OCR候选") == raw_row.get("专业计划数OCR候选")
            and lineage_row.get("专业计划数OCR数字候选") == raw_row.get("专业计划数OCR数字候选")
            and lineage_row.get("专业计划数是否纯数字") == raw_row.get("专业计划数是否纯数字")
            and lineage_row.get("学费OCR候选") == raw_row.get("学费OCR候选")
            and lineage_row.get("学费OCR数字候选") == raw_row.get("学费OCR数字候选")
            and lineage_row.get("学费是否纯数字") == raw_row.get("学费是否纯数字")
            and lineage_row.get("OCR置信度") == raw_row.get("OCR置信度")
            and lineage_row.get("原始字段完整性标记") == raw_row.get("字段完整性标记")
            and lineage_row.get("原始核验状态") == raw_row.get("核验状态")
            and lineage_row.get("质量到统一底座匹配状态") == "已回连"
            and lineage_row.get("统一底座到总工作台匹配状态") == "已回连"
            and lineage_row.get("总工作台到结构保真匹配状态") == "已回连"
            and lineage_row.get("总工作台到底座稳定性匹配状态") == "已回连"
            and lineage_row.get("质量到原页锚点匹配状态") == "已回连"
            and lineage_row.get("统一底座到三年投档旁挂匹配状态") == "已回连"
            and lineage_row.get("闭环缺口看板匹配状态") == "已回连"
            and lineage_row.get("全链路核心字段漂移数") == "0"
            and not lineage_row.get("全链路核心字段漂移字段")
            and lineage_row.get("字段缺口数") == stability_row.get("字段缺口数")
            and lineage_row.get("字段缺口字段") == stability_row.get("字段缺口字段")
            and as_int(lineage_row.get("字段候选任务数")) == len(field_rows)
            and as_int(lineage_row.get("非空字段候选数"))
            == sum(1 for field_row in field_rows if field_row.get("候选值"))
            and as_int(lineage_row.get("结构风险事件数")) == len(structural_events)
            and lineage_row.get("结构保真风险标签") == structural_row.get("结构保真风险标签")
            and lineage_row.get("底座稳定性等级") == stability_row.get("底座稳定性等级")
            and lineage_row.get("看板动作桶") == stability_row.get("看板动作桶")
            and lineage_row.get("湖北官方查询键是否碰撞") == ("true" if official_collisions else "false")
            and as_int(lineage_row.get("官方查询键碰撞事件数")) == len(official_collisions)
            and lineage_row.get("专业行原页证据锚点ID") == anchor_row.get("专业行原页证据锚点ID")
            and lineage_row.get("三年投档旁挂ID") == history_row.get("三年投档旁挂ID")
            and lineage_row.get("血缘审计结论") == "A0-全链路一一回连且核心OCR字段一致"
            and "未闭环前不得用于志愿推荐" in lineage_row.get("不得进入原因", "")
        )
    raw_lineage_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [raw_lineage_summary_path, raw_lineage_csv]
    )
    checks.append(ok(
        "第 19 期原始逐专业明细血缘审计表摘要、行数和链路计数正确",
        raw_lineage_summary.get("status") == "issue19_raw_major_lineage_consistency_audit_not_final"
        and raw_lineage_summary.get("generated_by")
        == "build_issue19_raw_major_lineage_consistency_audit.py"
        and raw_lineage_summary.get("output_table")
        == "data/working/issue19-raw-major-lineage-consistency-audit.csv"
        and raw_lineage_summary.get("row_grain") == "逐专业招生明细"
        and raw_lineage_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and raw_lineage_summary.get("row_count") == 13736
        and raw_lineage_summary.get("unique_audit_id_count") == 13736
        and raw_lineage_summary.get("unique_major_line_id_count") == 13736
        and raw_lineage_summary.get("unique_group_occurrence_id_count") == 3289
        and raw_lineage_summary.get("unique_raw_csv_data_line_count") == 13736
        and raw_lineage_summary.get("quality_match_count") == 13736
        and raw_lineage_summary.get("foundation_match_count") == 13736
        and raw_lineage_summary.get("master_match_count") == 13736
        and raw_lineage_summary.get("structural_match_count") == 13736
        and raw_lineage_summary.get("stability_match_count") == 13736
        and raw_lineage_summary.get("pdf_anchor_match_count") == 13736
        and raw_lineage_summary.get("historical_sidecar_match_count") == 13736
        and raw_lineage_summary.get("gap_scorecard_match_count") == 13736
        and raw_lineage_summary.get("source_counts") == {
            "raw_major_draft_row_count": 13736,
            "quality_workbench_row_count": 13736,
            "foundation_release_row_count": 13736,
            "master_workbench_row_count": 13736,
            "structural_register_row_count": 13736,
            "stability_dashboard_row_count": 13736,
            "pdf_anchor_row_count": 13736,
            "historical_sidecar_row_count": 13736,
            "gap_scorecard_row_count": 13736,
            "field_candidate_task_row_count": 19065,
            "structural_risk_event_row_count": 3108,
            "official_query_collision_row_count": 118,
        }
        and len(raw_lineage_rows) == 13736,
        f"{len(raw_lineage_rows)} raw lineage rows",
    ))
    checks.append(ok(
        "第 19 期原始逐专业明细血缘审计字段、主键、漂移和门禁正确",
        raw_lineage_fields == expected_raw_lineage_fields
        and len({row.get("原始专业行血缘审计ID") for row in raw_lineage_rows}) == 13736
        and {row.get("专业行ID") for row in raw_lineage_rows}
        == {row.get("专业行ID") for row in admission_master_rows}
        and {as_int(row.get("原始CSV数据行号")) for row in raw_lineage_rows} == set(range(1, 13737))
        and {as_int(row.get("专业明细源行号")) for row in raw_lineage_rows} == set(range(2, 13738))
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("原始到质量工作台匹配状态") == "已按原始CSV数据行号+专业明细源行号回连"
            and row.get("质量到统一底座匹配状态") == "已回连"
            and row.get("统一底座到总工作台匹配状态") == "已回连"
            and row.get("总工作台到结构保真匹配状态") == "已回连"
            and row.get("总工作台到底座稳定性匹配状态") == "已回连"
            and row.get("质量到原页锚点匹配状态") == "已回连"
            and row.get("统一底座到三年投档旁挂匹配状态") == "已回连"
            and row.get("闭环缺口看板匹配状态") == "已回连"
            and row.get("全链路核心字段漂移数") == "0"
            and row.get("血缘审计结论") == "A0-全链路一一回连且核心OCR字段一致"
            for row in raw_lineage_rows
        )
        and Counter(row.get("底座稳定性等级") for row in raw_lineage_rows)
        == Counter(raw_lineage_summary.get("stability_level_counts", {}))
        and sum(as_int(row.get("字段候选任务数")) or 0 for row in raw_lineage_rows) == 19065
        and sum(as_int(row.get("非空字段候选数")) or 0 for row in raw_lineage_rows) == 7621
        and sum(as_int(row.get("结构风险事件数")) or 0 for row in raw_lineage_rows) == 3108
        and sum(row.get("湖北官方查询键是否碰撞") == "true" for row in raw_lineage_rows) == 118
        and raw_lineage_join_ok,
    ))
    checks.append(ok(
        "第 19 期原始逐专业明细血缘审计摘要漂移、稳定性分布和不可推荐门禁正确",
        raw_lineage_summary.get("core_field_drift_row_count") == 0
        and raw_lineage_summary.get("core_field_drift_total_count") == 0
        and raw_lineage_summary.get("raw_to_quality_drift_row_count") == 0
        and raw_lineage_summary.get("quality_to_foundation_drift_row_count") == 0
        and raw_lineage_summary.get("foundation_to_master_drift_row_count") == 0
        and raw_lineage_summary.get("quality_to_anchor_drift_row_count") == 0
        and raw_lineage_summary.get("master_to_stability_drift_row_count") == 0
        and raw_lineage_summary.get("foundation_to_history_drift_row_count") == 0
        and raw_lineage_summary.get("lineage_conclusion_counts")
        == {"A0-全链路一一回连且核心OCR字段一致": 13736}
        and raw_lineage_summary.get("stability_level_counts") == {
            "B0-校名/结构/官方查询键强阻断": 2663,
            "B1-P0原页或官网冲突优先": 4370,
            "B2-字段缺口补证优先": 5962,
            "B3-三方官方闭环待核": 542,
            "B4-低风险抽检但仍非最终": 199,
        }
        and raw_lineage_summary.get("field_candidate_task_count") == 19065
        and raw_lineage_summary.get("non_empty_field_candidate_count") == 7621
        and raw_lineage_summary.get("structural_risk_event_count") == 3108
        and raw_lineage_summary.get("official_query_collision_major_line_count") == 118
        and raw_lineage_summary.get("official_query_collision_event_count") == 118
        and raw_lineage_summary.get("final_available_count") == 0
        and raw_lineage_summary.get("next_stage_available_count") == 0
        and raw_lineage_summary.get("auto_writeback_allowed_count") == 0
        and raw_lineage_summary.get("recommendation_basis_allowed_count") == 0,
    ))
    checks.append(ok(
        "第 19 期原始逐专业明细血缘审计公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(raw_lineage_public_text) is None
        and "private/" not in raw_lineage_public_text
        and "/Users/" not in raw_lineage_public_text
        and "final_allowed" not in raw_lineage_public_text
        and "ready_for_discussion" not in raw_lineage_public_text
        and "已确认" not in raw_lineage_public_text
        and "已核准" not in raw_lineage_public_text
        and "最终推荐" not in raw_lineage_public_text
        and "最终方案" not in raw_lineage_public_text
        and "可填报" not in raw_lineage_public_text
        and "可排序" not in raw_lineage_public_text,
    ))

    raw_source_summary_path = ROOT / "data/working/issue19-raw-major-source-evidence-audit-summary.json"
    raw_source_csv = ROOT / "data/working/issue19-raw-major-source-evidence-audit.csv"
    raw_source_summary = json.loads(raw_source_summary_path.read_text())
    with raw_source_csv.open(newline="", encoding="utf-8-sig") as f:
        raw_source_reader = csv.DictReader(f)
        raw_source_rows = list(raw_source_reader)
        raw_source_fields = raw_source_reader.fieldnames or []
    expected_raw_source_fields = script_list_constant(
        ROOT / "scripts/build_issue19_raw_major_source_evidence_audit.py",
        "FIELDS",
    )
    raw_source_by_major_id = {row.get("专业行ID"): row for row in raw_source_rows}
    raw_source_join_ok = True
    for raw_index, raw_row in enumerate(full_major_rows, start=1):
        quality_row = quality_by_raw_line.get(raw_index, {})
        major_id = quality_row.get("专业行ID", "")
        source_row = raw_source_by_major_id.get(major_id, {})
        anchor_row = anchor_by_major_id.get(major_id, {})
        lineage_row = raw_lineage_by_major_id.get(major_id, {})
        manifest_row = page_manifest_by_page.get(as_int(raw_row.get("来源页码")), {})
        raw_source_join_ok = (
            raw_source_join_ok
            and bool(source_row)
            and bool(quality_row)
            and bool(anchor_row)
            and bool(lineage_row)
            and bool(manifest_row)
            and source_row.get("原始专业行源证据审计ID")
            == stable_id("RAWSOURCE", [major_id, issue19_source["source"]["sha256"]])
            and source_row.get("数据阶段") == "issue19_raw_major_source_evidence_audit"
            and source_row.get("主表粒度") == "逐专业招生明细"
            and source_row.get("最终可用") == "false"
            and source_row.get("可进入下一阶段") == "false"
            and source_row.get("机器是否允许自动写回主表") == "false"
            and source_row.get("是否允许作为志愿推荐依据") == "false"
            and source_row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and source_row.get("原始CSV数据行号") == str(raw_index)
            and source_row.get("专业明细源行号") == str(raw_index + 1)
            and source_row.get("专业行ID") == major_id
            and source_row.get("专业组出现ID") == quality_row.get("专业组出现ID")
            and source_row.get("院校代码") == raw_row.get("院校代码")
            and source_row.get("院校名称OCR") == raw_row.get("院校名称OCR")
            and source_row.get("院校专业组代码OCR规范化")
            == raw_row.get("院校专业组代码OCR规范化")
            and source_row.get("来源页码") == raw_row.get("来源页码")
            and source_row.get("版面列") == raw_row.get("版面列")
            and source_row.get("专业起始行号") == raw_row.get("专业起始行号")
            and source_row.get("专业起始y") == raw_row.get("专业起始y")
            and source_row.get("OCR置信度") == raw_row.get("OCR置信度")
            and source_row.get("私有OCR起始行匹配状态") == "exact_private_ocr_start_line_hit"
            and source_row.get("私有OCR起始行页码一致") == "true"
            and source_row.get("私有OCR起始行栏位一致") == "true"
            and source_row.get("私有OCR起始行行号一致") == "true"
            and source_row.get("私有OCR起始行y一致") == "true"
            and source_row.get("私有OCR起始行置信度一致") == "true"
            and source_row.get("私有OCR起始行哈希与公开锚点一致") == "true"
            and source_row.get("私有OCR起始行专业代号匹配") == "true"
            and source_row.get("公开页级manifest匹配状态") == "matched_public_page_manifest"
            and source_row.get("私有页级manifest匹配状态") == "matched_private_page_manifest"
            and source_row.get("私有页图SHA256") == manifest_row.get("私有页图SHA256")
            and source_row.get("私有页图SHA256一致") == "true"
            and source_row.get("私有OCR文本SHA256") == manifest_row.get("私有OCR文本SHA256")
            and source_row.get("私有OCR行数一致") == "true"
            and source_row.get("私有OCR平均置信度一致") == "true"
            and source_row.get("公开锚点匹配状态") == "matched_public_pdf_anchor"
            and source_row.get("专业行原页证据锚点ID") == anchor_row.get("专业行原页证据锚点ID")
            and source_row.get("窗口文本SHA256") == anchor_row.get("窗口文本SHA256")
            and source_row.get("私有窗口JSONL匹配状态") == "matched_private_window_jsonl"
            and source_row.get("私有窗口SHA一致") == "true"
            and source_row.get("私有窗口页码一致") == "true"
            and source_row.get("私有窗口栏位一致") == "true"
            and source_row.get("私有窗口专业代号一致") == "true"
            and source_row.get("私有窗口状态一致") == "true"
            and source_row.get("原始血缘审计匹配状态") == "matched_raw_lineage_audit"
            and source_row.get("原始血缘审计结论") == lineage_row.get("血缘审计结论")
            and source_row.get("源证据覆盖结论")
            == "S0-私有OCR起始行、页级manifest、窗口证据和公开锚点均已回连"
            and "不得用于志愿推荐" in source_row.get("不得进入原因", "")
        )
    raw_source_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [raw_source_summary_path, raw_source_csv]
    )
    checks.append(ok(
        "第 19 期原始逐专业明细源证据审计摘要、行数和源头覆盖计数正确",
        raw_source_summary.get("status") == "issue19_raw_major_source_evidence_audit_not_final"
        and raw_source_summary.get("generated_by")
        == "build_issue19_raw_major_source_evidence_audit.py"
        and raw_source_summary.get("output_table")
        == "data/working/issue19-raw-major-source-evidence-audit.csv"
        and raw_source_summary.get("row_grain") == "逐专业招生明细"
        and raw_source_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and raw_source_summary.get("row_count") == 13736
        and raw_source_summary.get("unique_audit_id_count") == 13736
        and raw_source_summary.get("unique_major_line_id_count") == 13736
        and raw_source_summary.get("unique_raw_csv_data_line_count") == 13736
        and raw_source_summary.get("source_counts") == {
            "raw_major_draft_row_count": 13736,
            "quality_workbench_row_count": 13736,
            "public_page_manifest_row_count": 240,
            "pdf_anchor_row_count": 13736,
            "raw_lineage_audit_row_count": 13736,
            "private_ocr_line_row_count": 65512,
            "private_page_manifest_row_count": 240,
            "private_qc_issue_row_count": 37127,
            "private_window_jsonl_row_count": 13736,
        }
        and raw_source_summary.get("private_ocr_start_line_match_count") == 13736
        and raw_source_summary.get("private_ocr_start_line_hash_match_count") == 13736
        and raw_source_summary.get("private_ocr_start_line_major_code_match_count") == 13736
        and raw_source_summary.get("public_page_manifest_match_count") == 13736
        and raw_source_summary.get("private_page_manifest_match_count") == 13736
        and raw_source_summary.get("private_page_sha_match_count") == 13736
        and raw_source_summary.get("private_ocr_line_count_match_count") == 13736
        and raw_source_summary.get("private_ocr_confidence_match_count") == 13736
        and raw_source_summary.get("public_anchor_match_count") == 13736
        and raw_source_summary.get("private_window_jsonl_match_count") == 13736
        and raw_source_summary.get("private_window_sha_match_count") == 13736
        and raw_source_summary.get("raw_lineage_audit_match_count") == 13736
        and len(raw_source_rows) == 13736,
        f"{len(raw_source_rows)} raw source rows",
    ))
    checks.append(ok(
        "第 19 期原始逐专业明细源证据审计字段、主键和物理源头回连正确",
        raw_source_fields == expected_raw_source_fields
        and len({row.get("原始专业行源证据审计ID") for row in raw_source_rows}) == 13736
        and {row.get("专业行ID") for row in raw_source_rows}
        == {row.get("专业行ID") for row in admission_master_rows}
        and {as_int(row.get("原始CSV数据行号")) for row in raw_source_rows} == set(range(1, 13737))
        and {as_int(row.get("专业明细源行号")) for row in raw_source_rows} == set(range(2, 13738))
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("私有OCR起始行匹配状态") == "exact_private_ocr_start_line_hit"
            and row.get("私有OCR起始行哈希与公开锚点一致") == "true"
            and row.get("私有OCR起始行专业代号匹配") == "true"
            and row.get("公开锚点匹配状态") == "matched_public_pdf_anchor"
            and row.get("私有窗口SHA一致") == "true"
            and row.get("源证据覆盖结论")
            == "S0-私有OCR起始行、页级manifest、窗口证据和公开锚点均已回连"
            for row in raw_source_rows
        )
        and raw_source_join_ok,
    ))
    checks.append(ok(
        "第 19 期原始逐专业明细源证据审计风险分层和不可推荐门禁正确",
        raw_source_summary.get("coverage_conclusion_counts")
        == {"S0-私有OCR起始行、页级manifest、窗口证据和公开锚点均已回连": 13736}
        and raw_source_summary.get("source_risk_level_counts") == {
            "R2-起始行P0_QC待人工核页": 6086,
            "R2-锚点窗口阻断待人工核页": 13,
            "R3-源证据已回连但需优先复核": 7019,
            "R4-源证据已回连且未触发起始行QC风险": 618,
        }
        and raw_source_summary.get("anchor_status_counts") == {
            "P2-已生成专业行级OCR证据锚点": 12596,
            "P1-缺少组标题上下文": 1127,
            "P0-专业窗口为空": 13,
        }
        and raw_source_summary.get("start_line_qc_p0_row_count") == 6092
        and raw_source_summary.get("start_line_qc_p1_row_count") == 6966
        and raw_source_summary.get("start_line_qc_p0_total_count") == 6092
        and raw_source_summary.get("start_line_qc_p1_total_count") == 6966
        and raw_source_summary.get("low_confidence_page_major_line_count") == 291
        and raw_source_summary.get("final_available_count") == 0
        and raw_source_summary.get("next_stage_available_count") == 0
        and raw_source_summary.get("auto_writeback_allowed_count") == 0
        and raw_source_summary.get("recommendation_basis_allowed_count") == 0,
    ))
    checks.append(ok(
        "第 19 期原始逐专业明细源证据审计公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(raw_source_public_text) is None
        and "private/" not in raw_source_public_text
        and "/Users/" not in raw_source_public_text
        and "final_allowed" not in raw_source_public_text
        and "ready_for_discussion" not in raw_source_public_text
        and "已确认" not in raw_source_public_text
        and "已核准" not in raw_source_public_text
        and "最终推荐" not in raw_source_public_text
        and "最终方案" not in raw_source_public_text
        and "可填报" not in raw_source_public_text
        and "可排序" not in raw_source_public_text,
    ))

    source_risk_sidecar_summary_path = ROOT / "data/working/issue19-major-source-evidence-risk-sidecar-summary.json"
    source_risk_sidecar_csv = ROOT / "data/working/issue19-major-source-evidence-risk-sidecar.csv"
    source_risk_sidecar_summary = json.loads(source_risk_sidecar_summary_path.read_text())
    with source_risk_sidecar_csv.open(newline="", encoding="utf-8-sig") as f:
        source_risk_sidecar_reader = csv.DictReader(f)
        source_risk_sidecar_rows = list(source_risk_sidecar_reader)
        source_risk_sidecar_fields = source_risk_sidecar_reader.fieldnames or []
    expected_source_risk_sidecar_fields = script_list_constant(
        ROOT / "scripts/build_issue19_major_source_evidence_risk_sidecar.py",
        "FIELDS",
    )
    p0_review_rows_by_major_id = defaultdict(list)
    for row in p0_review_rows:
        p0_review_rows_by_major_id[row.get("专业行ID")].append(row)
    source_risk_join_ok = True
    for row in source_risk_sidecar_rows:
        major_id = row.get("专业行ID", "")
        raw_row = raw_source_by_major_id.get(major_id, {})
        stability_row = stability_dashboard_by_major_id.get(major_id, {})
        gap_row = gap_scorecard_by_major_id.get(major_id, {})
        master_row = admission_master_by_major_id.get(major_id, {})
        p0_rows_for_major = p0_review_rows_by_major_id.get(major_id, [])
        expected_layer = (
            "X1-专业窗口P0先核"
            if raw_row.get("源证据风险等级", "").startswith("R2-锚点窗口阻断")
            else "X2-起始行P0_QC先核"
            if raw_row.get("源证据风险等级", "").startswith("R2-起始行P0_QC")
            else "X3-源证据优先复核"
            if raw_row.get("源证据风险等级", "").startswith("R3-")
            else "X4-源证据低风险抽检但仍需三方闭环"
        )
        source_risk_join_ok = (
            source_risk_join_ok
            and bool(raw_row)
            and bool(stability_row)
            and bool(gap_row)
            and bool(master_row)
            and row.get("源证据风险侧账ID")
            == stable_id("SOURCERISK", [major_id, issue19_source["source"]["sha256"]])
            and row.get("原始专业行源证据审计ID") == raw_row.get("原始专业行源证据审计ID")
            and row.get("底座稳定性看板ID") == stability_row.get("底座稳定性看板ID")
            and row.get("闭环缺口看板ID") == gap_row.get("闭环缺口看板ID")
            and row.get("招生明细总工作台ID") == master_row.get("招生明细总工作台ID")
            and row.get("数据阶段") == "issue19_major_source_evidence_risk_sidecar"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("是否允许生成学校专业建议") == "false"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("专业组出现ID") == raw_row.get("专业组出现ID")
            and row.get("院校代码") == raw_row.get("院校代码")
            and row.get("院校名称OCR") == raw_row.get("院校名称OCR")
            and row.get("院校专业组代码OCR规范化")
            == raw_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == raw_row.get("来源页码")
            and row.get("版面列") == raw_row.get("版面列")
            and row.get("专业组内专业序号") == raw_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == raw_row.get("专业代号OCR")
            and row.get("专业起始行号") == raw_row.get("专业起始行号")
            and row.get("专业起始y") == raw_row.get("专业起始y")
            and row.get("OCR置信度") == raw_row.get("OCR置信度")
            and row.get("源证据覆盖结论") == raw_row.get("源证据覆盖结论")
            and row.get("源证据风险等级") == raw_row.get("源证据风险等级")
            and row.get("源证据风险标签") == raw_row.get("源证据风险标签")
            and row.get("源证据下沉分层") == expected_layer
            and row.get("是否进入源证据优先核页清单")
            == ("false" if expected_layer.startswith("X4-") else "true")
            and row.get("私有OCR起始行匹配状态") == raw_row.get("私有OCR起始行匹配状态")
            and row.get("私有OCR起始行哈希与公开锚点一致")
            == raw_row.get("私有OCR起始行哈希与公开锚点一致")
            and row.get("私有OCR起始行专业代号匹配")
            == raw_row.get("私有OCR起始行专业代号匹配")
            and row.get("起始行QC_P0数") == raw_row.get("起始行QC_P0数")
            and row.get("起始行QC_P1数") == raw_row.get("起始行QC_P1数")
            and row.get("公开页级manifest匹配状态")
            == raw_row.get("公开页级manifest匹配状态")
            and row.get("私有页级manifest匹配状态")
            == raw_row.get("私有页级manifest匹配状态")
            and row.get("公开锚点匹配状态") == raw_row.get("公开锚点匹配状态")
            and row.get("专业行原页证据锚点ID") == raw_row.get("专业行原页证据锚点ID")
            and row.get("证据锚点状态") == raw_row.get("证据锚点状态")
            and row.get("窗口文本SHA256") == raw_row.get("窗口文本SHA256")
            and row.get("私有窗口JSONL匹配状态") == raw_row.get("私有窗口JSONL匹配状态")
            and row.get("私有窗口证据编号") == raw_row.get("私有窗口证据编号")
            and row.get("私有窗口SHA一致") == raw_row.get("私有窗口SHA一致")
            and row.get("底座稳定性等级") == stability_row.get("底座稳定性等级")
            and row.get("闭环执行批次") == gap_row.get("闭环执行批次")
            and row.get("看板动作桶") == gap_row.get("看板动作桶")
            and row.get("风险阻断等级") == gap_row.get("风险阻断等级")
            and row.get("PDF原页锚点状态") == stability_row.get("PDF原页锚点状态")
            and row.get("湖北官方平台字段核验状态")
            == stability_row.get("湖北官方平台字段核验状态")
            and row.get("字段缺口数") == gap_row.get("字段缺口数")
            and row.get("字段缺口字段") == gap_row.get("字段缺口字段")
            and row.get("字段候选任务数") == gap_row.get("字段候选任务数")
            and row.get("非空字段候选数") == gap_row.get("非空字段候选数")
            and row.get("家庭接受度结论") == gap_row.get("家庭接受度结论")
            and row.get("同组调剂结论") == gap_row.get("同组调剂结论")
            and row.get("调剂影响等级") == gap_row.get("调剂影响等级")
            and row.get("首要核验动作") == gap_row.get("首要核验动作")
            and row.get("闭环执行动作集合") == gap_row.get("闭环执行动作集合")
            and row.get("P0复核任务数") == gap_row.get("P0复核任务数")
            and row.get("P0证据项") == gap_row.get("P0证据项")
            and as_int(row.get("P0复核工作清单任务数")) == len(p0_rows_for_major)
            and "issue19-raw-major-source-evidence-audit.csv" in row.get("建议下钻入口", "")
            and "源证据风险已下沉" in row.get("源证据下沉结论", "")
            and "不得直接用于志愿推荐" in row.get("不得进入原因", "")
        )
    source_risk_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [source_risk_sidecar_summary_path, source_risk_sidecar_csv]
    )
    checks.append(ok(
        "第 19 期逐专业源证据风险侧账摘要、行数和分布正确",
        source_risk_sidecar_summary.get("status")
        == "issue19_major_source_evidence_risk_sidecar_not_final"
        and source_risk_sidecar_summary.get("generated_by")
        == "build_issue19_major_source_evidence_risk_sidecar.py"
        and source_risk_sidecar_summary.get("output_table")
        == "data/working/issue19-major-source-evidence-risk-sidecar.csv"
        and source_risk_sidecar_summary.get("row_grain") == "逐专业招生明细"
        and source_risk_sidecar_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and source_risk_sidecar_summary.get("row_count") == 13736
        and source_risk_sidecar_summary.get("unique_sidecar_id_count") == 13736
        and source_risk_sidecar_summary.get("unique_major_line_id_count") == 13736
        and source_risk_sidecar_summary.get("source_counts") == {
            "raw_source_audit_row_count": 13736,
            "stability_dashboard_row_count": 13736,
            "gap_scorecard_row_count": 13736,
            "master_workbench_row_count": 13736,
            "p0_review_worklist_row_count": 6619,
            "p0_review_worklist_major_line_count": 5310,
        }
        and source_risk_sidecar_summary.get("join_match_counts") == {
            "raw_source_audit_match_count": 13736,
            "stability_dashboard_match_count": 13736,
            "gap_scorecard_match_count": 13736,
            "master_workbench_match_count": 13736,
            "p0_review_worklist_major_line_count": 5310,
        }
        and source_risk_sidecar_summary.get("source_bridge_layer_counts") == {
            "X3-源证据优先复核": 7019,
            "X4-源证据低风险抽检但仍需三方闭环": 618,
            "X2-起始行P0_QC先核": 6086,
            "X1-专业窗口P0先核": 13,
        }
        and source_risk_sidecar_summary.get("source_review_priority_counts") == {
            "P1-源证据优先复核": 7019,
            "P3-低风险抽检但仍待三方闭环": 618,
            "P0-起始行QC先核": 6086,
            "P0-专业窗口或锚点阻断先核": 13,
        }
        and source_risk_sidecar_summary.get("source_priority_review_major_line_count") == 13118
        and source_risk_sidecar_summary.get("source_low_risk_sample_major_line_count") == 618
        and source_risk_sidecar_summary.get("anchor_status_counts") == {
            "P2-已生成专业行级OCR证据锚点": 12596,
            "P1-缺少组标题上下文": 1127,
            "P0-专业窗口为空": 13,
        }
        and source_risk_sidecar_summary.get("start_line_qc_p0_row_count") == 6092
        and source_risk_sidecar_summary.get("start_line_qc_p1_row_count") == 6966
        and source_risk_sidecar_summary.get("start_line_qc_p0_total_count") == 6092
        and source_risk_sidecar_summary.get("start_line_qc_p1_total_count") == 6966
        and source_risk_sidecar_summary.get("low_confidence_page_major_line_count") == 291
        and source_risk_sidecar_summary.get("p0_review_worklist_task_total_count") == 6619
        and source_risk_sidecar_summary.get("p0_review_worklist_major_line_count") == 5310
        and source_risk_sidecar_summary.get("final_available_count") == 0
        and source_risk_sidecar_summary.get("next_stage_available_count") == 0
        and source_risk_sidecar_summary.get("auto_writeback_allowed_count") == 0
        and source_risk_sidecar_summary.get("recommendation_basis_allowed_count") == 0
        and source_risk_sidecar_summary.get("school_major_suggestion_allowed_count") == 0
        and len(source_risk_sidecar_rows) == 13736,
        f"{len(source_risk_sidecar_rows)} source risk rows",
    ))
    checks.append(ok(
        "第 19 期逐专业源证据风险侧账字段、主键和下游回链正确",
        source_risk_sidecar_fields == expected_source_risk_sidecar_fields
        and len({row.get("源证据风险侧账ID") for row in source_risk_sidecar_rows}) == 13736
        and {row.get("专业行ID") for row in source_risk_sidecar_rows}
        == {row.get("专业行ID") for row in admission_master_rows}
        == {row.get("专业行ID") for row in raw_source_rows}
        == {row.get("专业行ID") for row in stability_dashboard_rows}
        == {row.get("专业行ID") for row in gap_scorecard_rows}
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("是否允许生成学校专业建议") == "false"
            and row.get("私有OCR起始行匹配状态") == "exact_private_ocr_start_line_hit"
            and row.get("私有OCR起始行哈希与公开锚点一致") == "true"
            and row.get("私有OCR起始行专业代号匹配") == "true"
            and row.get("源证据覆盖结论")
            == "S0-私有OCR起始行、页级manifest、窗口证据和公开锚点均已回连"
            for row in source_risk_sidecar_rows
        )
        and source_risk_join_ok,
    ))
    checks.append(ok(
        "第 19 期逐专业源证据风险侧账公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(source_risk_public_text) is None
        and "private/" not in source_risk_public_text
        and "/Users/" not in source_risk_public_text
        and "final_allowed" not in source_risk_public_text
        and "ready_for_discussion" not in source_risk_public_text
        and "已确认" not in source_risk_public_text
        and "已核准" not in source_risk_public_text
        and "最终推荐" not in source_risk_public_text
        and "最终方案" not in source_risk_public_text
        and "可填报" not in source_risk_public_text
        and "可排序" not in source_risk_public_text,
    ))

    field_fact_summary_path = ROOT / "data/working/issue19-field-fact-closure-ledger-summary.json"
    field_fact_csv = ROOT / "data/working/issue19-field-fact-closure-ledger.csv"
    field_fact_summary = json.loads(field_fact_summary_path.read_text())
    with field_fact_csv.open(newline="", encoding="utf-8-sig") as f:
        field_fact_reader = csv.DictReader(f)
        field_fact_rows = list(field_fact_reader)
        field_fact_fields = field_fact_reader.fieldnames or []
    expected_field_fact_fields = script_list_constant(
        ROOT / "scripts/build_issue19_field_fact_closure_ledger.py",
        "FIELDS",
    )
    source_risk_sidecar_by_major_id = {
        row.get("专业行ID"): row for row in source_risk_sidecar_rows
    }
    official_sidecar_by_major_id = {
        row.get("专业行ID"): row for row in official_sidecar_rows
    }
    field_candidate_rows_by_major_field = defaultdict(list)
    for candidate_row in field_gap_candidate_rows:
        field_candidate_rows_by_major_field[
            (candidate_row.get("专业行ID", ""), candidate_row.get("字段名", ""))
        ].append(candidate_row)

    def verify_counter(counter, summary_key):
        return counter == Counter(field_fact_summary.get(summary_key, {}))

    def verify_ordered_join(values):
        seen = set()
        result = []
        for value in values:
            cleaned = str(value or "").strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return "；".join(result)

    def verify_gap_field_set(value):
        text = str(value or "").strip()
        if not text:
            return set()
        return {part.strip() for part in text.split("；") if part.strip()}

    def verify_field_status(master_row, field_name, candidate_rows):
        if master_row.get(f"{field_name}人工确认", ""):
            return "K9-人工确认存在但仍需最终门禁复核"
        has_gap = field_name in verify_gap_field_set(master_row.get("字段缺口字段"))
        ocr_value = master_row.get(f"{field_name}OCR候选", "")
        non_empty_candidates = sum(1 for candidate_row in candidate_rows if candidate_row.get("候选值", "").strip())
        if has_gap and non_empty_candidates:
            return "K1-字段缺口有候选待PDF原页和官方核验"
        if has_gap:
            return "K0-字段缺口无候选需原页重读"
        if ocr_value:
            return "K2-OCR候选存在但三方核验未闭环"
        return "K0-字段空值需原页重读"

    def verify_field_fact_level(master_row):
        gap_count = as_int(master_row.get("字段缺口数")) or 0
        non_empty = as_int(master_row.get("非空字段候选数")) or 0
        if gap_count >= 3:
            return "L0-三字段缺口优先阻断"
        if gap_count == 2:
            return "L1-两字段缺口优先补证"
        if gap_count == 1 and non_empty > 0:
            return "L2-单字段缺口有候选待核"
        if gap_count == 1:
            return "L3-单字段缺口无候选需重读"
        return "L4-三字段OCR齐全但待三方闭环"

    def verify_field_blocking_level(master_row):
        gap_count = as_int(master_row.get("字段缺口数")) or 0
        non_empty = as_int(master_row.get("非空字段候选数")) or 0
        if gap_count and non_empty == 0:
            return "Q0-字段缺口无候选阻断"
        if gap_count:
            return "Q1-字段缺口有候选待人工核验"
        return "Q2-OCR字段齐全但PDF和官方未闭环"

    def verify_three_field_completeness(master_row):
        present = [
            bool(master_row.get("再选科目OCR候选", "").strip()),
            bool(master_row.get("专业计划数OCR候选", "").strip()),
            bool(master_row.get("学费OCR候选", "").strip()),
        ]
        if all(present):
            return "三字段OCR候选齐全"
        return f"三字段OCR候选缺{3 - sum(present)}项"

    field_fact_join_ok = True
    for row in field_fact_rows:
        major_id = row.get("专业行ID", "")
        master_row = admission_master_by_major_id.get(major_id, {})
        source_row = source_risk_sidecar_by_major_id.get(major_id, {})
        official_row = hubei_official_by_major_id.get(major_id, {})
        evidence_row = official_sidecar_by_major_id.get(major_id, {})
        decision_row = decision_gates_by_major_id.get(major_id, {})
        candidate_rows_for_major = field_candidate_rows_by_major_id.get(major_id, [])
        field_fact_join_ok = (
            field_fact_join_ok
            and bool(master_row)
            and bool(source_row)
            and bool(official_row)
            and bool(decision_row)
            and row.get("字段事实闭环ID")
            == stable_id("FIELDFACT", [major_id, issue19_source["source"]["sha256"]])
            and row.get("数据阶段") == "issue19_field_fact_closure_ledger"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("是否允许生成学校专业建议") == "false"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("专业组出现ID") == master_row.get("专业组出现ID")
            and row.get("院校代码") == master_row.get("院校代码")
            and row.get("院校名称OCR") == master_row.get("院校名称OCR")
            and row.get("院校专业组代码OCR规范化")
            == master_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == master_row.get("来源页码")
            and row.get("版面列") == master_row.get("版面列")
            and row.get("专业组内专业序号") == master_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == master_row.get("专业代号OCR")
            and row.get("专业名称及备注短摘") == master_row.get("专业名称及备注短摘")
            and row.get("再选科目OCR候选") == master_row.get("再选科目OCR候选")
            and row.get("专业计划数OCR候选") == master_row.get("专业计划数OCR候选")
            and row.get("学费OCR候选") == master_row.get("学费OCR候选")
            and row.get("再选科目人工确认") == master_row.get("再选科目人工确认")
            and row.get("专业计划数人工确认") == master_row.get("专业计划数人工确认")
            and row.get("学费人工确认") == master_row.get("学费人工确认")
            and row.get("字段缺口数") == master_row.get("字段缺口数")
            and row.get("字段缺口字段") == master_row.get("字段缺口字段")
            and row.get("字段候选任务数") == master_row.get("字段候选任务数")
            and row.get("非空字段候选数") == master_row.get("非空字段候选数")
            and row.get("三字段OCR完整状态") == verify_three_field_completeness(master_row)
            and row.get("字段事实闭环等级") == verify_field_fact_level(master_row)
            and row.get("字段事实阻断等级") == verify_field_blocking_level(master_row)
            and row.get("字段事实缺口类型")
            == (master_row.get("字段缺口字段") or "无机器字段缺口")
            and row.get("字段事实可机器修复") == "false"
            and row.get("字段事实可进入候选筛选") == "false"
            and row.get("PDF字段核验状态") == master_row.get("PDF原页证据状态")
            and row.get("湖北官方平台字段核验状态")
            == master_row.get("湖北官方平台字段核验状态")
            and row.get("湖北官方核验包任务ID")
            == (master_row.get("湖北官方核验包任务ID") or official_row.get("湖北官方核验包任务ID"))
            and row.get("高校官网证据匹配状态") == master_row.get("高校官网证据匹配状态")
            and row.get("B0B1官网证据任务数") == master_row.get("B0B1官网证据任务数")
            and row.get("官网证据能否替代湖北官方计划")
            == (master_row.get("官网证据能否替代湖北官方计划") or evidence_row.get("能否替代湖北官方计划", ""))
            and row.get("源证据下沉分层") == source_row.get("源证据下沉分层")
            and row.get("源证据核页优先级") == source_row.get("源证据核页优先级")
            and row.get("底座稳定性等级") == source_row.get("底座稳定性等级")
            and row.get("看板动作桶") == (master_row.get("看板动作桶") or source_row.get("看板动作桶"))
            and row.get("风险阻断等级") == (master_row.get("风险阻断等级") or source_row.get("风险阻断等级"))
            and row.get("候选初筛闸门状态") == decision_row.get("候选初筛闸门状态")
            and row.get("初筛动作桶") == decision_row.get("初筛动作桶")
            and len(candidate_rows_for_major) == (as_int(row.get("字段候选任务数")) or 0)
            and sum(1 for candidate_row in candidate_rows_for_major if candidate_row.get("候选值", "").strip())
            == (as_int(row.get("非空字段候选数")) or 0)
            and "issue19-field-fact-closure-ledger.csv" in row.get("建议下钻入口", "")
            and "issue19-admission-detail-master-workbench.csv" in row.get("建议下钻入口", "")
            and "不得用于志愿推荐" in row.get("不得进入原因", "")
        )
        for field_name in ["再选科目", "专业计划数", "学费"]:
            rows_for_field = field_candidate_rows_by_major_field.get((major_id, field_name), [])
            field_fact_join_ok = (
                field_fact_join_ok
                and row.get(f"{field_name}字段事实状态")
                == verify_field_status(master_row, field_name, rows_for_field)
                and (as_int(row.get(f"{field_name}候选任务数")) or 0) == len(rows_for_field)
                and (as_int(row.get(f"{field_name}非空候选数")) or 0)
                == sum(1 for candidate_row in rows_for_field if candidate_row.get("候选值", "").strip())
                and row.get(f"{field_name}候选值集合")
                == verify_ordered_join(candidate_row.get("候选值", "") for candidate_row in rows_for_field)
                and row.get(f"{field_name}候选来源类型集合")
                == verify_ordered_join(candidate_row.get("候选来源类型", "") for candidate_row in rows_for_field)
                and row.get(f"{field_name}候选置信等级集合")
                == verify_ordered_join(candidate_row.get("候选置信等级", "") for candidate_row in rows_for_field)
                and row.get(f"{field_name}候选状态集合")
                == verify_ordered_join(candidate_row.get("候选状态", "") for candidate_row in rows_for_field)
                and row.get(f"{field_name}官方核验状态") == official_row.get("平台字段核验状态")
                and row.get(f"{field_name}PDF核验状态") == master_row.get("PDF原页证据状态")
            )

    field_fact_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [field_fact_summary_path, field_fact_csv]
    )
    checks.append(ok(
        "第 19 期字段事实闭环总账摘要、行数和分布正确",
        field_fact_summary.get("status") == "issue19_field_fact_closure_ledger_not_final"
        and field_fact_summary.get("generated_by") == "build_issue19_field_fact_closure_ledger.py"
        and field_fact_summary.get("output_table")
        == "data/working/issue19-field-fact-closure-ledger.csv"
        and field_fact_summary.get("row_grain") == "逐专业招生明细"
        and field_fact_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and field_fact_summary.get("row_count") == 13736
        and field_fact_summary.get("unique_ledger_id_count") == 13736
        and field_fact_summary.get("unique_major_line_id_count") == 13736
        and field_fact_summary.get("source_counts") == {
            "master_workbench_row_count": 13736,
            "source_risk_sidecar_row_count": 13736,
            "field_gap_candidate_row_count": 19065,
            "hubei_official_packet_row_count": 13736,
            "b0_b1_official_evidence_row_count": 854,
            "decision_gate_row_count": 13736,
        }
        and field_fact_summary.get("field_fact_closure_level_counts") == {
            "L3-单字段缺口无候选需重读": 2771,
            "L2-单字段缺口有候选待核": 3803,
            "L1-两字段缺口优先补证": 5206,
            "L4-三字段OCR齐全但待三方闭环": 1263,
            "L0-三字段缺口优先阻断": 693,
        }
        and field_fact_summary.get("field_fact_blocking_level_counts") == {
            "Q0-字段缺口无候选阻断": 5271,
            "Q1-字段缺口有候选待人工核验": 7202,
            "Q2-OCR字段齐全但PDF和官方未闭环": 1263,
        }
        and field_fact_summary.get("three_field_ocr_completeness_counts") == {
            "三字段OCR候选缺1项": 6838,
            "三字段OCR候选缺2项": 5418,
            "三字段OCR候选齐全": 1293,
            "三字段OCR候选缺3项": 187,
        }
        and field_fact_summary.get("field_gap_count_distribution") == {
            "1": 6574,
            "2": 5206,
            "0": 1263,
            "3": 693,
        }
        and field_fact_summary.get("field_gap_field_distribution") == {
            "专业计划数": 777,
            "再选科目": 5715,
            "再选科目；专业计划数": 4719,
            "": 1263,
            "再选科目；专业计划数；学费": 693,
            "专业计划数；学费": 158,
            "学费": 82,
            "再选科目；学费": 329,
        }
        and field_fact_summary.get("reselect_field_status_counts") == {
            "K2-OCR候选存在但三方核验未闭环": 2280,
            "K1-字段缺口有候选待PDF原页和官方核验": 6782,
            "K0-字段缺口无候选需原页重读": 4674,
        }
        and field_fact_summary.get("plan_count_field_status_counts") == {
            "K0-字段缺口无候选需原页重读": 5739,
            "K2-OCR候选存在但三方核验未闭环": 7389,
            "K1-字段缺口有候选待PDF原页和官方核验": 608,
        }
        and field_fact_summary.get("tuition_field_status_counts") == {
            "K2-OCR候选存在但三方核验未闭环": 12474,
            "K0-字段缺口无候选需原页重读": 1031,
            "K1-字段缺口有候选待PDF原页和官方核验": 231,
        }
        and field_fact_summary.get("field_candidate_task_total_count") == 19065
        and field_fact_summary.get("field_candidate_non_empty_total_count") == 7621
        and field_fact_summary.get("manual_confirmed_field_count") == 0
        and field_fact_summary.get("pdf_review_pending_count") == 13736
        and field_fact_summary.get("hubei_official_review_pending_count") == 13736
        and field_fact_summary.get("final_available_count") == 0
        and field_fact_summary.get("next_stage_available_count") == 0
        and field_fact_summary.get("auto_writeback_allowed_count") == 0
        and field_fact_summary.get("recommendation_basis_allowed_count") == 0
        and field_fact_summary.get("school_major_suggestion_allowed_count") == 0
        and len(field_fact_rows) == 13736,
        f"{len(field_fact_rows)} field fact rows",
    ))
    checks.append(ok(
        "第 19 期字段事实闭环总账字段、主键和逐专业来源闭环正确",
        field_fact_fields == expected_field_fact_fields
        and len({row.get("字段事实闭环ID") for row in field_fact_rows}) == 13736
        and {row.get("专业行ID") for row in field_fact_rows}
        == {row.get("专业行ID") for row in admission_master_rows}
        == {row.get("专业行ID") for row in source_risk_sidecar_rows}
        == {row.get("专业行ID") for row in hubei_official_rows}
        == {row.get("专业行ID") for row in decision_gates_rows}
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("是否允许生成学校专业建议") == "false"
            and row.get("PDF字段核验状态") == "has_page_hash_pending_manual_pdf_review"
            and row.get("湖北官方平台字段核验状态") == "pending_hubei_official_plan_review"
            for row in field_fact_rows
        )
        and verify_counter(Counter(row.get("字段事实闭环等级") for row in field_fact_rows), "field_fact_closure_level_counts")
        and verify_counter(Counter(row.get("字段事实阻断等级") for row in field_fact_rows), "field_fact_blocking_level_counts")
        and verify_counter(Counter(row.get("三字段OCR完整状态") for row in field_fact_rows), "three_field_ocr_completeness_counts")
        and verify_counter(Counter(row.get("字段缺口数") for row in field_fact_rows), "field_gap_count_distribution")
        and verify_counter(Counter(row.get("字段缺口字段") for row in field_fact_rows), "field_gap_field_distribution")
        and verify_counter(Counter(row.get("再选科目字段事实状态") for row in field_fact_rows), "reselect_field_status_counts")
        and verify_counter(Counter(row.get("专业计划数字段事实状态") for row in field_fact_rows), "plan_count_field_status_counts")
        and verify_counter(Counter(row.get("学费字段事实状态") for row in field_fact_rows), "tuition_field_status_counts")
        and sum(as_int(row.get("再选科目候选任务数")) or 0 for row in field_fact_rows) == 11456
        and sum(as_int(row.get("专业计划数候选任务数")) or 0 for row in field_fact_rows) == 6347
        and sum(as_int(row.get("学费候选任务数")) or 0 for row in field_fact_rows) == 1262
        and sum(
            (as_int(row.get("再选科目非空候选数")) or 0)
            + (as_int(row.get("专业计划数非空候选数")) or 0)
            + (as_int(row.get("学费非空候选数")) or 0)
            for row in field_fact_rows
        ) == 7621
        and field_fact_join_ok,
    ))
    checks.append(ok(
        "第 19 期字段事实闭环总账公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(field_fact_public_text) is None
        and "private/" not in field_fact_public_text
        and "private\\" not in field_fact_public_text
        and "/Users/" not in field_fact_public_text
        and "ocr-runs" not in field_fact_public_text
        and "rendered-pages" not in field_fact_public_text
        and ".png" not in field_fact_public_text
        and ".jpg" not in field_fact_public_text
        and ".jpeg" not in field_fact_public_text
        and "Authorization" not in field_fact_public_text
        and "Bearer " not in field_fact_public_text
        and "Cookie" not in field_fact_public_text
        and "final_allowed" not in field_fact_public_text
        and "ready_for_discussion" not in field_fact_public_text
        and "已确认" not in field_fact_public_text
        and "已核准" not in field_fact_public_text
        and "最终推荐" not in field_fact_public_text
        and "最终方案" not in field_fact_public_text
        and "可填报" not in field_fact_public_text
        and "可排序" not in field_fact_public_text
        and not any(token in field_fact_public_text for token in shared_forbidden_tokens),
    ))

    field_fact_tasks_summary_path = ROOT / "data/working/issue19-field-fact-verification-tasks-summary.json"
    field_fact_tasks_csv = ROOT / "data/working/issue19-field-fact-verification-tasks.csv"
    field_fact_tasks_summary = json.loads(field_fact_tasks_summary_path.read_text())
    with field_fact_tasks_csv.open(newline="", encoding="utf-8-sig") as f:
        field_fact_tasks_reader = csv.DictReader(f)
        field_fact_tasks_rows = list(field_fact_tasks_reader)
        field_fact_tasks_fields = field_fact_tasks_reader.fieldnames or []
    expected_field_fact_tasks_fields = script_list_constant(
        ROOT / "scripts/build_issue19_field_fact_verification_tasks.py",
        "FIELDS",
    )
    field_fact_by_major_id = {row.get("专业行ID"): row for row in field_fact_rows}
    field_fact_task_fields_by_major_id = defaultdict(set)
    for row in field_fact_tasks_rows:
        field_fact_task_fields_by_major_id[row.get("专业行ID", "")].add(row.get("字段名", ""))

    def verify_field_task_priority(status):
        if status.startswith("K0-"):
            return "P0-字段无候选原页重读"
        if status.startswith("K1-"):
            return "P1-字段有候选回看原页和官方"
        if status.startswith("K2-"):
            return "P3-OCR齐全字段三方闭环"
        return "P4-人工确认或异常字段最终门禁复核"

    field_fact_task_page_counts = Counter(row.get("来源页码") for row in field_fact_tasks_rows)
    field_fact_task_page_k0_counts = Counter(
        row.get("来源页码")
        for row in field_fact_tasks_rows
        if row.get("字段事实状态", "").startswith("K0-")
    )
    field_fact_task_page_k1_counts = Counter(
        row.get("来源页码")
        for row in field_fact_tasks_rows
        if row.get("字段事实状态", "").startswith("K1-")
    )
    field_fact_task_page_k2_counts = Counter(
        row.get("来源页码")
        for row in field_fact_tasks_rows
        if row.get("字段事实状态", "").startswith("K2-")
    )
    field_fact_task_page_sequence = Counter()
    field_fact_task_join_ok = True
    for index, row in enumerate(field_fact_tasks_rows, start=1):
        major_id = row.get("专业行ID", "")
        field_name = row.get("字段名", "")
        fact_row = field_fact_by_major_id.get(major_id, {})
        page_row = page_fidelity_by_page.get(as_int(row.get("来源页码")))
        field_fact_task_page_sequence[row.get("来源页码", "")] += 1
        field_fact_task_join_ok = (
            field_fact_task_join_ok
            and bool(fact_row)
            and bool(page_row)
            and field_name in {"再选科目", "专业计划数", "学费"}
            and row.get("字段事实核验任务ID")
            == stable_id("FIELDVERIFY", [major_id, field_name, issue19_source["source"]["sha256"]])
            and row.get("来源字段事实闭环总账")
            == "data/working/issue19-field-fact-closure-ledger.csv"
            and row.get("来源页级保真复核队列")
            == "data/working/issue19-page-fidelity-review-queue.csv"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("数据阶段") == "issue19_field_fact_verification_tasks"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("任务粒度") == "逐专业招生明细×关键字段"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("是否允许生成学校专业建议") == "false"
            and row.get("任务状态") == "pending_field_fact_verification"
            and row.get("字段核验优先级") == verify_field_task_priority(row.get("字段事实状态", ""))
            and as_int(row.get("字段核验优先序")) == index
            and as_int(row.get("页内字段任务序")) == field_fact_task_page_sequence[row.get("来源页码", "")]
            and as_int(row.get("页内字段任务数")) == field_fact_task_page_counts[row.get("来源页码")]
            and as_int(row.get("页内阻断字段任务数")) == field_fact_task_page_k0_counts[row.get("来源页码")]
            and as_int(row.get("页内无候选字段任务数")) == field_fact_task_page_k0_counts[row.get("来源页码")]
            and as_int(row.get("页内有候选字段任务数")) == field_fact_task_page_k1_counts[row.get("来源页码")]
            and as_int(row.get("页内OCR齐全待核字段任务数")) == field_fact_task_page_k2_counts[row.get("来源页码")]
            and row.get("字段事实闭环ID") == fact_row.get("字段事实闭环ID")
            and row.get("专业组出现ID") == fact_row.get("专业组出现ID")
            and row.get("院校代码") == fact_row.get("院校代码")
            and row.get("院校名称OCR") == fact_row.get("院校名称OCR")
            and row.get("院校专业组代码OCR规范化")
            == fact_row.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == fact_row.get("来源页码")
            and row.get("版面列") == fact_row.get("版面列")
            and row.get("专业组内专业序号") == fact_row.get("专业组内专业序号")
            and row.get("专业代号OCR") == fact_row.get("专业代号OCR")
            and row.get("专业名称及备注短摘") == fact_row.get("专业名称及备注短摘")
            and row.get("字段OCR候选") == fact_row.get(f"{field_name}OCR候选")
            and row.get("字段人工确认") == fact_row.get(f"{field_name}人工确认")
            and row.get("字段事实状态") == fact_row.get(f"{field_name}字段事实状态")
            and row.get("字段候选任务数") == fact_row.get(f"{field_name}候选任务数")
            and row.get("字段非空候选数") == fact_row.get(f"{field_name}非空候选数")
            and row.get("字段候选值集合") == fact_row.get(f"{field_name}候选值集合")
            and row.get("字段候选来源类型集合") == fact_row.get(f"{field_name}候选来源类型集合")
            and row.get("字段候选置信等级集合") == fact_row.get(f"{field_name}候选置信等级集合")
            and row.get("字段候选状态集合") == fact_row.get(f"{field_name}候选状态集合")
            and row.get("字段PDF核验状态") == fact_row.get(f"{field_name}PDF核验状态")
            and row.get("字段湖北官方核验状态") == fact_row.get(f"{field_name}官方核验状态")
            and row.get("字段下一步") == fact_row.get(f"{field_name}下一步")
            and row.get("字段事实闭环等级") == fact_row.get("字段事实闭环等级")
            and row.get("字段事实阻断等级") == fact_row.get("字段事实阻断等级")
            and row.get("字段事实缺口类型") == fact_row.get("字段事实缺口类型")
            and row.get("字段缺口数") == fact_row.get("字段缺口数")
            and row.get("字段缺口字段") == fact_row.get("字段缺口字段")
            and row.get("三字段OCR完整状态") == fact_row.get("三字段OCR完整状态")
            and row.get("源证据下沉分层") == fact_row.get("源证据下沉分层")
            and row.get("源证据核页优先级") == fact_row.get("源证据核页优先级")
            and row.get("底座稳定性等级") == fact_row.get("底座稳定性等级")
            and row.get("看板动作桶") == fact_row.get("看板动作桶")
            and row.get("风险阻断等级") == fact_row.get("风险阻断等级")
            and row.get("候选初筛闸门状态") == fact_row.get("候选初筛闸门状态")
            and row.get("初筛动作桶") == fact_row.get("初筛动作桶")
            and row.get("湖北官方核验包任务ID") == fact_row.get("湖北官方核验包任务ID")
            and row.get("高校官网证据匹配状态") == fact_row.get("高校官网证据匹配状态")
            and row.get("B0B1官网证据任务数") == fact_row.get("B0B1官网证据任务数")
            and row.get("官网证据能否替代湖北官方计划")
            == fact_row.get("官网证据能否替代湖北官方计划")
            and row.get("页级保真队列ID") == page_row.get("页级保真队列ID")
            and row.get("页面复核优先级") == page_row.get("页面复核优先级")
            and row.get("页面阻断等级") == page_row.get("页面阻断等级")
            and row.get("私有页图证据编号") == page_row.get("私有页图证据编号")
            and row.get("私有页图SHA256") == page_row.get("私有页图SHA256")
            and row.get("私有OCR文本证据编号") == page_row.get("私有OCR文本证据编号")
            and row.get("私有OCR文本SHA256") == page_row.get("私有OCR文本SHA256")
            and row.get("OCR平均置信度") == page_row.get("OCR平均置信度")
            and row.get("OCR_QC_P0数") == page_row.get("OCR_QC_P0数")
            and row.get("OCR_QC_P1数") == page_row.get("OCR_QC_P1数")
            and row.get("页面专业明细数") == page_row.get("页面专业明细数")
            and row.get("页面结构异常数") == page_row.get("页面结构异常数")
            and row.get("页面高严重结构异常数") == page_row.get("页面高严重结构异常数")
            and "不得用于志愿推荐" in row.get("不得进入原因", "")
        )
    field_fact_tasks_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [field_fact_tasks_summary_path, field_fact_tasks_csv]
    )
    checks.append(ok(
        "第 19 期字段事实核验任务队列摘要、行数和分布正确",
        field_fact_tasks_summary.get("status") == "issue19_field_fact_verification_tasks_not_final"
        and field_fact_tasks_summary.get("generated_by")
        == "build_issue19_field_fact_verification_tasks.py"
        and field_fact_tasks_summary.get("output_table")
        == "data/working/issue19-field-fact-verification-tasks.csv"
        and field_fact_tasks_summary.get("row_grain") == "逐专业招生明细×关键字段"
        and field_fact_tasks_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and field_fact_tasks_summary.get("row_count") == 41208
        and field_fact_tasks_summary.get("unique_task_id_count") == 41208
        and field_fact_tasks_summary.get("unique_major_line_id_count") == 13736
        and field_fact_tasks_summary.get("unique_pdf_page_count") == 231
        and field_fact_tasks_summary.get("source_counts") == {
            "field_fact_ledger_row_count": 13736,
            "page_fidelity_queue_row_count": 231,
        }
        and field_fact_tasks_summary.get("field_counts") == {
            "专业计划数": 13736,
            "再选科目": 13736,
            "学费": 13736,
        }
        and field_fact_tasks_summary.get("field_status_counts") == {
            "K0-字段缺口无候选需原页重读": 11444,
            "K1-字段缺口有候选待PDF原页和官方核验": 7621,
            "K2-OCR候选存在但三方核验未闭环": 22143,
        }
        and field_fact_tasks_summary.get("field_priority_counts") == {
            "P0-字段无候选原页重读": 11444,
            "P1-字段有候选回看原页和官方": 7621,
            "P3-OCR齐全字段三方闭环": 22143,
        }
        and field_fact_tasks_summary.get("field_candidate_task_total_count") == 19065
        and field_fact_tasks_summary.get("field_candidate_non_empty_total_count") == 7621
        and field_fact_tasks_summary.get("page_fidelity_hit_task_count") == 41208
        and field_fact_tasks_summary.get("final_available_count") == 0
        and field_fact_tasks_summary.get("next_stage_available_count") == 0
        and field_fact_tasks_summary.get("auto_writeback_allowed_count") == 0
        and field_fact_tasks_summary.get("recommendation_basis_allowed_count") == 0
        and field_fact_tasks_summary.get("school_major_suggestion_allowed_count") == 0
        and len(field_fact_tasks_rows) == 41208,
        f"{len(field_fact_tasks_rows)} field verification tasks",
    ))
    checks.append(ok(
        "第 19 期字段事实核验任务队列字段、主键和逐字段来源闭环正确",
        field_fact_tasks_fields == expected_field_fact_tasks_fields
        and len({row.get("字段事实核验任务ID") for row in field_fact_tasks_rows}) == 41208
        and {row.get("专业行ID") for row in field_fact_tasks_rows}
        == {row.get("专业行ID") for row in field_fact_rows}
        and all(
            fields == {"再选科目", "专业计划数", "学费"}
            for fields in field_fact_task_fields_by_major_id.values()
        )
        and len(field_fact_task_fields_by_major_id) == 13736
        and Counter(row.get("字段名") for row in field_fact_tasks_rows)
        == Counter(field_fact_tasks_summary.get("field_counts", {}))
        and Counter(row.get("字段事实状态") for row in field_fact_tasks_rows)
        == Counter(field_fact_tasks_summary.get("field_status_counts", {}))
        and Counter(row.get("字段核验优先级") for row in field_fact_tasks_rows)
        == Counter(field_fact_tasks_summary.get("field_priority_counts", {}))
        and dict(field_fact_task_page_counts.most_common(30))
        == field_fact_tasks_summary.get("page_task_count_top30")
        and dict(field_fact_task_page_k0_counts.most_common(30))
        == field_fact_tasks_summary.get("page_blocking_field_task_count_top30")
        and sum(as_int(row.get("字段候选任务数")) or 0 for row in field_fact_tasks_rows) == 19065
        and sum(as_int(row.get("字段非空候选数")) or 0 for row in field_fact_tasks_rows) == 7621
        and sum(1 for row in field_fact_tasks_rows if row.get("页级保真队列ID")) == 41208
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("是否允许生成学校专业建议") == "false"
            and row.get("字段PDF核验状态") == "has_page_hash_pending_manual_pdf_review"
            and row.get("字段湖北官方核验状态") == "pending_hubei_official_plan_review"
            for row in field_fact_tasks_rows
        )
        and field_fact_task_join_ok,
    ))
    checks.append(ok(
        "第 19 期字段事实核验任务队列公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(field_fact_tasks_public_text) is None
        and "private/" not in field_fact_tasks_public_text
        and "private\\" not in field_fact_tasks_public_text
        and "/Users/" not in field_fact_tasks_public_text
        and "ocr-runs" not in field_fact_tasks_public_text
        and "rendered-pages" not in field_fact_tasks_public_text
        and ".png" not in field_fact_tasks_public_text
        and ".jpg" not in field_fact_tasks_public_text
        and ".jpeg" not in field_fact_tasks_public_text
        and "Authorization" not in field_fact_tasks_public_text
        and "Bearer " not in field_fact_tasks_public_text
        and "Cookie" not in field_fact_tasks_public_text
        and "final_allowed" not in field_fact_tasks_public_text
        and "ready_for_discussion" not in field_fact_tasks_public_text
        and "已确认" not in field_fact_tasks_public_text
        and "已核准" not in field_fact_tasks_public_text
        and "最终推荐" not in field_fact_tasks_public_text
        and "最终方案" not in field_fact_tasks_public_text
        and "可填报" not in field_fact_tasks_public_text
        and "可排序" not in field_fact_tasks_public_text
        and not any(token in field_fact_tasks_public_text for token in shared_forbidden_tokens),
    ))

    field_p0_reread_summary_path = ROOT / "data/working/issue19-field-fact-p0-reread-worklist-summary.json"
    field_p0_reread_csv = ROOT / "data/working/issue19-field-fact-p0-reread-worklist.csv"
    field_p0_reread_summary = json.loads(field_p0_reread_summary_path.read_text())
    with field_p0_reread_csv.open(newline="", encoding="utf-8-sig") as f:
        field_p0_reread_reader = csv.DictReader(f)
        field_p0_reread_rows = list(field_p0_reread_reader)
        field_p0_reread_fields = field_p0_reread_reader.fieldnames or []
    expected_field_p0_reread_fields = script_list_constant(
        ROOT / "scripts/build_issue19_field_fact_p0_reread_worklist.py",
        "FIELDS",
    )
    source_p0_field_tasks = [
        row for row in field_fact_tasks_rows
        if row.get("字段核验优先级") == "P0-字段无候选原页重读"
        and row.get("字段事实状态", "").startswith("K0-")
    ]
    source_p0_field_task_by_id = {
        row.get("字段事实核验任务ID"): row
        for row in source_p0_field_tasks
    }
    field_p0_reread_page_counts = Counter(row.get("来源页码") for row in field_p0_reread_rows)
    field_p0_reread_school_counts = Counter(
        f"{row.get('院校代码', '')}|{row.get('院校名称OCR', '')}"
        for row in field_p0_reread_rows
    )
    field_p0_reread_major_counts = Counter(row.get("专业行ID") for row in field_p0_reread_rows)
    field_p0_reread_page_sequence = Counter()
    field_p0_reread_join_ok = True
    for index, row in enumerate(field_p0_reread_rows, start=1):
        major_id = row.get("专业行ID", "")
        field_name = row.get("字段名", "")
        source_task_id = row.get("来源字段事实核验任务ID", "")
        source_task = source_p0_field_task_by_id.get(source_task_id, {})
        raw_source_row = raw_source_by_major_id.get(major_id, {})
        anchor_row = anchor_by_major_id.get(major_id, {})
        page_row = page_fidelity_by_page.get(as_int(row.get("来源页码")))
        page_key = row.get("来源页码", "")
        school_key = f"{row.get('院校代码', '')}|{row.get('院校名称OCR', '')}"
        field_p0_reread_page_sequence[page_key] += 1
        action_text = row.get("P0原页重读动作", "")
        field_action_ok = (
            (field_name == "专业计划数" and "计划数列" in action_text and "误读" in action_text)
            or (field_name == "再选科目" and "再选科目列" in action_text and "不限选科" in action_text)
            or (field_name == "学费" and "学费列" in action_text and "误读" in action_text)
        )
        field_p0_reread_join_ok = (
            field_p0_reread_join_ok
            and bool(source_task)
            and bool(raw_source_row)
            and bool(anchor_row)
            and bool(page_row)
            and field_name in {"再选科目", "专业计划数", "学费"}
            and row.get("P0字段原页重读任务ID")
            == stable_id("FIELDP0REREAD", [source_task_id, major_id, field_name, issue19_source["source"]["sha256"]])
            and row.get("来源字段事实核验任务队列")
            == "data/working/issue19-field-fact-verification-tasks.csv"
            and row.get("来源原始逐专业明细源证据审计")
            == "data/working/issue19-raw-major-source-evidence-audit.csv"
            and row.get("来源专业行原页证据锚点表")
            == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
            and row.get("来源页级保真复核队列")
            == "data/working/issue19-page-fidelity-review-queue.csv"
            and row.get("来源PDF_SHA256") == issue19_source["source"]["sha256"]
            and row.get("数据阶段") == "issue19_field_fact_p0_reread_worklist"
            and row.get("主表粒度") == "逐专业招生明细"
            and row.get("任务粒度") == "逐专业招生明细×K0字段原页重读"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("机器是否允许自动回填候选") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("是否允许生成学校专业建议") == "false"
            and row.get("P0原页重读状态") == "pending_original_page_reread"
            and as_int(row.get("P0原页重读优先序")) == index
            and as_int(row.get("页内P0字段任务序")) == field_p0_reread_page_sequence[page_key]
            and as_int(row.get("页内P0字段任务数")) == field_p0_reread_page_counts[page_key]
            and as_int(row.get("学校P0字段任务数")) == field_p0_reread_school_counts[school_key]
            and as_int(row.get("专业行P0字段任务数")) == field_p0_reread_major_counts[major_id]
            and source_task.get("字段核验优先级") == "P0-字段无候选原页重读"
            and source_task.get("字段事实状态", "").startswith("K0-")
            and row.get("专业行ID") == source_task.get("专业行ID")
            and row.get("字段事实闭环ID") == source_task.get("字段事实闭环ID")
            and row.get("专业组出现ID") == source_task.get("专业组出现ID")
            and row.get("院校代码") == source_task.get("院校代码")
            and row.get("院校名称OCR") == source_task.get("院校名称OCR")
            and row.get("院校专业组代码OCR规范化")
            == source_task.get("院校专业组代码OCR规范化")
            and row.get("来源页码") == source_task.get("来源页码")
            and row.get("版面列") == source_task.get("版面列")
            and row.get("专业组内专业序号") == source_task.get("专业组内专业序号")
            and row.get("专业代号OCR") == source_task.get("专业代号OCR")
            and row.get("专业名称及备注短摘") == source_task.get("专业名称及备注短摘")
            and row.get("字段名") == source_task.get("字段名")
            and row.get("字段OCR候选") == ""
            and row.get("字段人工确认") == ""
            and row.get("字段事实状态") == "K0-字段缺口无候选需原页重读"
            and row.get("字段候选任务数") == source_task.get("字段候选任务数")
            and row.get("字段非空候选数") == "0"
            and row.get("字段候选值集合") == ""
            and row.get("字段候选状态集合") == source_task.get("字段候选状态集合")
            and row.get("字段PDF核验状态") == "has_page_hash_pending_manual_pdf_review"
            and row.get("字段湖北官方核验状态") == "pending_hubei_official_plan_review"
            and row.get("字段事实闭环等级") == source_task.get("字段事实闭环等级")
            and row.get("字段事实阻断等级") == source_task.get("字段事实阻断等级")
            and row.get("字段事实缺口类型") == source_task.get("字段事实缺口类型")
            and row.get("字段缺口数") == source_task.get("字段缺口数")
            and row.get("字段缺口字段") == source_task.get("字段缺口字段")
            and row.get("三字段OCR完整状态") == source_task.get("三字段OCR完整状态")
            and row.get("页级保真队列ID") == page_row.get("页级保真队列ID")
            and row.get("页面复核优先级") == page_row.get("页面复核优先级")
            and row.get("页面阻断等级") == page_row.get("页面阻断等级")
            and row.get("私有页图证据编号") == page_row.get("私有页图证据编号")
            and row.get("私有页图SHA256") == page_row.get("私有页图SHA256")
            and row.get("私有OCR文本证据编号") == page_row.get("私有OCR文本证据编号")
            and row.get("私有OCR文本SHA256") == page_row.get("私有OCR文本SHA256")
            and row.get("OCR平均置信度") == page_row.get("OCR平均置信度")
            and row.get("OCR_QC_P0数") == page_row.get("OCR_QC_P0数")
            and row.get("OCR_QC_P1数") == page_row.get("OCR_QC_P1数")
            and row.get("页面专业明细数") == page_row.get("页面专业明细数")
            and row.get("页面结构异常数") == page_row.get("页面结构异常数")
            and row.get("页面高严重结构异常数") == page_row.get("页面高严重结构异常数")
            and row.get("原始专业行源证据审计ID") == raw_source_row.get("原始专业行源证据审计ID")
            and row.get("私有OCR起始行匹配状态") == raw_source_row.get("私有OCR起始行匹配状态")
            and row.get("专业起始行号") == raw_source_row.get("专业起始行号")
            and row.get("专业起始y") == raw_source_row.get("专业起始y")
            and row.get("起始行QC_P0数") == raw_source_row.get("起始行QC_P0数")
            and row.get("起始行QC_P1数") == raw_source_row.get("起始行QC_P1数")
            and row.get("起始行QC规则ID集合") == raw_source_row.get("起始行QC规则ID集合")
            and row.get("私有OCR起始行文本SHA256") == raw_source_row.get("私有OCR起始行文本SHA256")
            and row.get("源证据覆盖结论") == raw_source_row.get("源证据覆盖结论")
            and row.get("源证据风险等级") == raw_source_row.get("源证据风险等级")
            and row.get("源证据风险标签") == raw_source_row.get("源证据风险标签")
            and row.get("专业行原页证据锚点ID") == anchor_row.get("专业行原页证据锚点ID")
            and row.get("证据锚点状态") == anchor_row.get("证据锚点状态")
            and row.get("专业组标题行号") == anchor_row.get("专业组标题行号")
            and row.get("专业组标题y") == anchor_row.get("专业组标题y")
            and row.get("OCR窗口y上界") == anchor_row.get("OCR窗口y上界")
            and row.get("OCR窗口y下界") == anchor_row.get("OCR窗口y下界")
            and row.get("专业窗口行号范围") == anchor_row.get("专业窗口行号范围")
            and row.get("合并证据窗口行号范围") == anchor_row.get("合并证据窗口行号范围")
            and row.get("专业窗口行数") == anchor_row.get("专业窗口行数")
            and row.get("合并证据窗口行数") == anchor_row.get("合并证据窗口行数")
            and row.get("窗口文本SHA256") == anchor_row.get("窗口文本SHA256")
            and row.get("窗口平均置信度") == anchor_row.get("窗口平均置信度")
            and row.get("窗口最低置信度") == anchor_row.get("窗口最低置信度")
            and row.get("私有窗口证据编号") == anchor_row.get("私有窗口证据编号")
            and field_action_ok
            and "不得写回字段" in row.get("不得进入原因", "")
            and "推荐学校专业" in row.get("不得进入原因", "")
            and "志愿排序" in row.get("不得进入原因", "")
            and "补出字段候选" in row.get("下一步", "")
        )
    field_p0_reread_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [field_p0_reread_summary_path, field_p0_reread_csv]
    )
    checks.append(ok(
        "第 19 期 P0 字段原页重读工作清单摘要、行数和分布正确",
        field_p0_reread_summary.get("status") == "issue19_field_fact_p0_reread_worklist_not_final"
        and field_p0_reread_summary.get("generated_by")
        == "build_issue19_field_fact_p0_reread_worklist.py"
        and field_p0_reread_summary.get("output_table")
        == "data/working/issue19-field-fact-p0-reread-worklist.csv"
        and field_p0_reread_summary.get("row_grain") == "逐专业招生明细×K0字段原页重读"
        and field_p0_reread_summary.get("source_pdf_sha256") == issue19_source["source"]["sha256"]
        and field_p0_reread_summary.get("row_count") == 11444
        and field_p0_reread_summary.get("unique_task_id_count") == 11444
        and field_p0_reread_summary.get("unique_source_field_task_id_count") == 11444
        and field_p0_reread_summary.get("unique_major_line_id_count") == 8536
        and field_p0_reread_summary.get("unique_pdf_page_count") == 231
        and field_p0_reread_summary.get("unique_school_code_name_count") == 967
        and field_p0_reread_summary.get("source_counts") == {
            "field_fact_verification_task_row_count": 41208,
            "raw_source_audit_row_count": 13736,
            "pdf_evidence_anchor_row_count": 13736,
            "page_fidelity_queue_row_count": 231,
        }
        and field_p0_reread_summary.get("field_counts") == {
            "专业计划数": 5739,
            "再选科目": 4674,
            "学费": 1031,
        }
        and field_p0_reread_summary.get("field_status_counts") == {
            "K0-字段缺口无候选需原页重读": 11444,
        }
        and field_p0_reread_summary.get("field_fact_closure_level_counts") == {
            "L1-两字段缺口优先补证": 7438,
            "L3-单字段缺口无候选需重读": 2771,
            "L0-三字段缺口优先阻断": 1235,
        }
        and field_p0_reread_summary.get("source_risk_level_counts") == {
            "R2-起始行P0_QC待人工核页": 5179,
            "R3-源证据已回连但需优先复核": 5770,
            "R4-源证据已回连且未触发起始行QC风险": 478,
            "R2-锚点窗口阻断待人工核页": 17,
        }
        and field_p0_reread_summary.get("anchor_status_counts") == {
            "P2-已生成专业行级OCR证据锚点": 9765,
            "P1-缺少组标题上下文": 1662,
            "P0-专业窗口为空": 17,
        }
        and field_p0_reread_summary.get("field_candidate_task_total_count") == 11444
        and field_p0_reread_summary.get("field_candidate_non_empty_total_count") == 0
        and field_p0_reread_summary.get("raw_source_hit_count") == 11444
        and field_p0_reread_summary.get("pdf_anchor_hit_count") == 11444
        and field_p0_reread_summary.get("page_fidelity_hit_count") == 11444
        and field_p0_reread_summary.get("final_available_count") == 0
        and field_p0_reread_summary.get("next_stage_available_count") == 0
        and field_p0_reread_summary.get("auto_writeback_allowed_count") == 0
        and field_p0_reread_summary.get("auto_candidate_fill_allowed_count") == 0
        and field_p0_reread_summary.get("recommendation_basis_allowed_count") == 0
        and field_p0_reread_summary.get("school_major_suggestion_allowed_count") == 0
        and len(field_p0_reread_rows) == 11444
        and len(source_p0_field_tasks) == 11444,
        f"{len(field_p0_reread_rows)} p0 field reread rows",
    ))
    checks.append(ok(
        "第 19 期 P0 字段原页重读工作清单字段、主键和四路证据回连正确",
        field_p0_reread_fields == expected_field_p0_reread_fields
        and len({row.get("P0字段原页重读任务ID") for row in field_p0_reread_rows}) == 11444
        and {row.get("来源字段事实核验任务ID") for row in field_p0_reread_rows}
        == set(source_p0_field_task_by_id)
        and Counter(row.get("字段名") for row in field_p0_reread_rows)
        == Counter(field_p0_reread_summary.get("field_counts", {}))
        and Counter(row.get("字段事实状态") for row in field_p0_reread_rows)
        == Counter(field_p0_reread_summary.get("field_status_counts", {}))
        and Counter(row.get("字段事实闭环等级") for row in field_p0_reread_rows)
        == Counter(field_p0_reread_summary.get("field_fact_closure_level_counts", {}))
        and Counter(row.get("源证据风险等级") for row in field_p0_reread_rows)
        == Counter(field_p0_reread_summary.get("source_risk_level_counts", {}))
        and Counter(row.get("证据锚点状态") for row in field_p0_reread_rows)
        == Counter(field_p0_reread_summary.get("anchor_status_counts", {}))
        and dict(field_p0_reread_page_counts.most_common(30))
        == field_p0_reread_summary.get("page_task_count_top30")
        and dict(field_p0_reread_school_counts.most_common(30))
        == field_p0_reread_summary.get("school_task_count_top30")
        and sum(as_int(row.get("字段候选任务数")) or 0 for row in field_p0_reread_rows) == 11444
        and sum(as_int(row.get("字段非空候选数")) or 0 for row in field_p0_reread_rows) == 0
        and sum(1 for row in field_p0_reread_rows if row.get("原始专业行源证据审计ID")) == 11444
        and sum(1 for row in field_p0_reread_rows if row.get("专业行原页证据锚点ID")) == 11444
        and sum(1 for row in field_p0_reread_rows if row.get("页级保真队列ID")) == 11444
        and all(
            row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器是否允许自动写回主表") == "false"
            and row.get("机器是否允许自动回填候选") == "false"
            and row.get("是否允许作为志愿推荐依据") == "false"
            and row.get("是否允许生成学校专业建议") == "false"
            and row.get("P0原页重读状态") == "pending_original_page_reread"
            and row.get("字段OCR候选") == ""
            and row.get("字段人工确认") == ""
            and row.get("字段候选值集合") == ""
            and row.get("字段非空候选数") == "0"
            for row in field_p0_reread_rows
        )
        and field_p0_reread_join_ok,
    ))
    checks.append(ok(
        "第 19 期 P0 字段原页重读工作清单公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(field_p0_reread_public_text) is None
        and "private/" not in field_p0_reread_public_text
        and "private\\" not in field_p0_reread_public_text
        and "/Users/" not in field_p0_reread_public_text
        and "ocr-runs" not in field_p0_reread_public_text
        and "rendered-pages" not in field_p0_reread_public_text
        and ".png" not in field_p0_reread_public_text
        and ".jpg" not in field_p0_reread_public_text
        and ".jpeg" not in field_p0_reread_public_text
        and "Authorization" not in field_p0_reread_public_text
        and "Bearer " not in field_p0_reread_public_text
        and "Cookie" not in field_p0_reread_public_text
        and "final_allowed" not in field_p0_reread_public_text
        and "ready_for_discussion" not in field_p0_reread_public_text
        and "已确认" not in field_p0_reread_public_text
        and "已核准" not in field_p0_reread_public_text
        and "最终推荐" not in field_p0_reread_public_text
        and "最终方案" not in field_p0_reread_public_text
        and "可填报" not in field_p0_reread_public_text
        and "可排序" not in field_p0_reread_public_text
        and not any(token in field_p0_reread_public_text for token in shared_forbidden_tokens),
    ))

    layout_risk_summary_path = ROOT / "data/working/issue19-major-line-layout-continuity-risk-summary.json"
    layout_risk_csv = ROOT / "data/working/issue19-major-line-layout-continuity-risk-ledger.csv"
    layout_risk_summary = json.loads(layout_risk_summary_path.read_text())
    with layout_risk_csv.open(newline="", encoding="utf-8-sig") as f:
        layout_risk_reader = csv.DictReader(f)
        layout_risk_rows = list(layout_risk_reader)
        layout_risk_fields = layout_risk_reader.fieldnames or []
    expected_layout_risk_fields = script_list_constant(
        ROOT / "scripts/build_issue19_major_line_layout_continuity_risk_ledger.py",
        "FIELDS",
    )
    pdf_anchor_by_major_id = {row.get("专业行ID"): row for row in pdf_anchor_rows}
    layout_involved_major_ids = set()
    layout_risk_join_ok = True
    for row in layout_risk_rows:
        anchor_row = pdf_anchor_by_major_id.get(row.get("专业行ID"), {})
        layout_involved_major_ids.add(row.get("专业行ID", ""))
        if row.get("相邻前一专业行ID"):
            layout_involved_major_ids.add(row.get("相邻前一专业行ID", ""))
        layout_risk_join_ok = (
            layout_risk_join_ok
            and bool(anchor_row)
            and row.get("版面连续性风险ID")
            == stable_id(
                "LAYOUTRISK",
                [row.get("风险规则ID", ""), row.get("专业行ID", ""), row.get("相邻前一专业行ID", "")],
            )
            and row.get("来源专业行原页证据锚点表")
            == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
            and row.get("数据阶段") == "issue19_major_line_layout_continuity_risk_ledger"
            and row.get("主表粒度") == "逐专业招生明细×版面连续性风险事件"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器能否自动修复") == "false"
            and row.get("专业组出现ID") == anchor_row.get("专业组出现ID")
            and row.get("来源页码") == anchor_row.get("来源页码")
            and row.get("版面列") == anchor_row.get("版面列")
        )
    layout_risk_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [layout_risk_summary_path, layout_risk_csv]
    )
    checks.append(ok(
        "第 19 期专业行版面连续性风险清单摘要和计数正确",
        layout_risk_summary.get("status") == "issue19_major_line_layout_continuity_risk_not_final"
        and layout_risk_summary.get("generated_by")
        == "build_issue19_major_line_layout_continuity_risk_ledger.py"
        and layout_risk_summary.get("output_table")
        == "data/working/issue19-major-line-layout-continuity-risk-ledger.csv"
        and layout_risk_summary.get("source_anchor_table")
        == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
        and layout_risk_summary.get("source_row_count") == 13736
        and layout_risk_summary.get("risk_event_count") == 1934
        and layout_risk_summary.get("unique_risk_id_count") == 1934
        and layout_risk_summary.get("unique_major_line_id_count") == 1541
        and layout_risk_summary.get("unique_group_occurrence_id_count") == 351
        and layout_risk_summary.get("risk_rule_counts") == {
            "L01_START_LINE_NOT_AFTER_GROUP_TITLE": 950,
            "L02_ADJACENT_Y_DIRECTION_REVERSED": 280,
            "L04_ADJACENT_Y_LARGE_DELTA": 364,
            "L06_ADJACENT_LINE_GAP_GT_12": 195,
            "L05_ADJACENT_LINE_NOT_INCREASING": 138,
            "L03_ADJACENT_Y_ZERO_DELTA": 7,
        }
        and layout_risk_summary.get("final_available_count") == 0
        and layout_risk_summary.get("next_stage_available_count") == 0
        and layout_risk_summary.get("machine_auto_fix_count") == 0,
        f"{len(layout_risk_rows)} layout risk rows",
    ))
    checks.append(ok(
        "第 19 期专业行版面连续性风险清单字段、主键和锚点回链正确",
        layout_risk_fields == expected_layout_risk_fields
        and len(layout_risk_rows) == 1934
        and len({row.get("版面连续性风险ID") for row in layout_risk_rows}) == 1934
        and len(layout_involved_major_ids - {""}) == 1541
        and all(row.get("最终可用") == "false" and row.get("可进入下一阶段") == "false" for row in layout_risk_rows)
        and all(row.get("机器能否自动修复") == "false" for row in layout_risk_rows)
        and layout_risk_join_ok,
    ))
    checks.append(ok(
        "第 19 期专业行版面连续性风险清单公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(layout_risk_public_text) is None
        and "private/" not in layout_risk_public_text
        and "final_allowed" not in layout_risk_public_text
        and "ready_for_discussion" not in layout_risk_public_text
        and "已确认" not in layout_risk_public_text
        and "已核准" not in layout_risk_public_text
        and "最终推荐" not in layout_risk_public_text
        and "最终方案" not in layout_risk_public_text
        and "可填报" not in layout_risk_public_text
        and "可排序" not in layout_risk_public_text,
    ))

    code_order_summary_path = ROOT / "data/working/issue19-major-code-order-risk-summary.json"
    code_order_csv = ROOT / "data/working/issue19-major-code-order-risk-ledger.csv"
    code_order_summary = json.loads(code_order_summary_path.read_text())
    with code_order_csv.open(newline="", encoding="utf-8-sig") as f:
        code_order_reader = csv.DictReader(f)
        code_order_rows = list(code_order_reader)
        code_order_fields = code_order_reader.fieldnames or []
    expected_code_order_fields = script_list_constant(
        ROOT / "scripts/build_issue19_major_code_order_risk_ledger.py",
        "FIELDS",
    )
    code_involved_major_ids = set()
    code_order_join_ok = True
    for row in code_order_rows:
        anchor_row = pdf_anchor_by_major_id.get(row.get("专业行ID"), {})
        code_involved_major_ids.add(row.get("专业行ID", ""))
        if row.get("相邻前一专业行ID"):
            code_involved_major_ids.add(row.get("相邻前一专业行ID", ""))
        code_order_join_ok = (
            code_order_join_ok
            and bool(anchor_row)
            and row.get("专业代号顺序风险ID")
            == stable_id(
                "CODERISK",
                [row.get("风险规则ID", ""), row.get("专业行ID", ""), row.get("相邻前一专业行ID", "")],
            )
            and row.get("来源专业行原页证据锚点表")
            == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
            and row.get("数据阶段") == "issue19_major_code_order_risk_ledger"
            and row.get("主表粒度") == "逐专业招生明细×专业代号顺序风险事件"
            and row.get("最终可用") == "false"
            and row.get("可进入下一阶段") == "false"
            and row.get("机器能否自动修复") == "false"
            and row.get("专业组出现ID") == anchor_row.get("专业组出现ID")
            and row.get("专业代号OCR") == anchor_row.get("专业代号OCR")
        )
    code_order_public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [code_order_summary_path, code_order_csv]
    )
    checks.append(ok(
        "第 19 期专业代号顺序风险清单摘要和计数正确",
        code_order_summary.get("status") == "issue19_major_code_order_risk_not_final"
        and code_order_summary.get("generated_by")
        == "build_issue19_major_code_order_risk_ledger.py"
        and code_order_summary.get("output_table")
        == "data/working/issue19-major-code-order-risk-ledger.csv"
        and code_order_summary.get("source_anchor_table")
        == "data/working/issue19-major-line-pdf-evidence-anchors.csv"
        and code_order_summary.get("source_row_count") == 13736
        and code_order_summary.get("risk_event_count") == 355
        and code_order_summary.get("unique_risk_id_count") == 355
        and code_order_summary.get("unique_major_line_id_count") == 574
        and code_order_summary.get("unique_group_occurrence_id_count") == 220
        and code_order_summary.get("risk_rule_counts") == {
            "C01_MAJOR_CODE_UNPARSEABLE": 29,
            "C02_MAJOR_CODE_NOT_INCREASING": 170,
            "C03_MAJOR_CODE_JUMP_GT_5": 156,
        }
        and code_order_summary.get("final_available_count") == 0
        and code_order_summary.get("next_stage_available_count") == 0
        and code_order_summary.get("machine_auto_fix_count") == 0,
        f"{len(code_order_rows)} code order risk rows",
    ))
    checks.append(ok(
        "第 19 期专业代号顺序风险清单字段、主键和锚点回链正确",
        code_order_fields == expected_code_order_fields
        and len(code_order_rows) == 355
        and len({row.get("专业代号顺序风险ID") for row in code_order_rows}) == 355
        and len(code_involved_major_ids - {""}) == 574
        and all(row.get("最终可用") == "false" and row.get("可进入下一阶段") == "false" for row in code_order_rows)
        and all(row.get("机器能否自动修复") == "false" for row in code_order_rows)
        and code_order_join_ok,
    ))
    checks.append(ok(
        "第 19 期专业代号顺序风险清单公开文件不含私有路径、登录态、身份信息和最终误导结论",
        foundation_release_sensitive_re.search(code_order_public_text) is None
        and "private/" not in code_order_public_text
        and "final_allowed" not in code_order_public_text
        and "ready_for_discussion" not in code_order_public_text
        and "已确认" not in code_order_public_text
        and "已核准" not in code_order_public_text
        and "最终推荐" not in code_order_public_text
        and "最终方案" not in code_order_public_text
        and "可填报" not in code_order_public_text
        and "可排序" not in code_order_public_text,
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

    group_index_files = [
        ROOT / "data/working/issue19-candidate-v3-review-intake.csv",
        ROOT / "data/working/issue19-family-fit-group-screen.csv",
        ROOT / "data/working/issue19-full-admission-plan-group-ocr-draft.csv",
        ROOT / "data/working/issue19-full-quality-group-tiers.csv",
        ROOT / "data/working/issue19-candidate-v3-b0-b1-group-review-pack.csv",
        ROOT / "data/working/issue19-candidate-v3-b0-b1-official-crosscheck-queue.csv",
        ROOT / "data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv",
    ]
    group_index_misuse_ok = True
    for path in group_index_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        group_index_misuse_ok = group_index_misuse_ok and (
            "候选讨论主表" not in text and "默认讨论表" not in text
        )
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                group_index_misuse_ok = group_index_misuse_ok and all(
                    row.get(field, "false") != "true"
                    for field in ["最终可用", "可进入最终候选", "可进入下一阶段"]
                    if field in (reader.fieldnames or [])
                )
    checks.append(ok(
        "第 19 期组级索引/队列表不得冒充逐专业候选讨论主表",
        group_index_misuse_ok,
    ))

    if (ROOT / ".git").exists():
        tracked_pyc_result = subprocess.run(
            ["git", "ls-files", "*.pyc"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        tracked_pyc_files = [
            line for line in tracked_pyc_result.stdout.splitlines() if line.strip()
        ]
        checks.append(ok(
            "公开仓库未跟踪 Python 编译缓存",
            tracked_pyc_result.returncode == 0 and not tracked_pyc_files,
            "；".join(tracked_pyc_files[:5]),
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
