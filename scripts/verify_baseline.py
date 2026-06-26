#!/usr/bin/env python3
import csv
import hashlib
import json
import re
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
