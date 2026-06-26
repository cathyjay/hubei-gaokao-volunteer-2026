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
