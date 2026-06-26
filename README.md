# 2026 湖北高考志愿项目

这个项目用于持续记录、复核和讨论 2026 年湖北普通类首选物理考生的高考志愿填报方案。
核心目标是在 2026-06-30 前形成可执行的学校/专业组/专业排序最终方案。2026-07-02
12:00 前只保留应急修改缓冲；官方本科普通批集中填报截止时间仍为 2026-07-02 17:00。

## 项目规则

- 不保存考生姓名、身份证号、准考证号、报名号等直接身份信息。
- 官方网页、PDF、图片原件是第一证据；OCR/CSV 只是便于筛选的派生数据。
- 最终志愿只允许使用已经回看官方原件、招生计划和招生章程复核过的逐专业招生明细及其所在院校专业组。
- 以位次和等位分为主，不用裸分直觉做判断。
- 所有候选必须展开到招生专业明细，记录“为什么选、有什么风险、是否能接受调剂”。
- 对外讨论和候选方案不再只给学校/院校专业组两层摘要；默认一行一个招生专业明细，院校专业组只作为投档、调剂范围和证据索引字段。

## 固定考生基线

- 省份：湖北
- 年份：2026
- 类别：普通类，本科普通批优先
- 首选科目：物理
- 再选科目：化学、地理
- 总分：515
- 2026 位次区间：90895-91723
- 2026 累计位次：91723
- 2025 等位分：494
- 2024 等位分：497
- 2023 等位分：481

结构化记录见 `candidate-baseline.json`。

## 关键文档

- `docs/BACKGROUND_REQUIREMENTS_AND_PLAN.md`：背景、目标、缺口、6 月 30 日前计划。
- `docs/EXECUTION_PLAN.md`：从数据底座到最终志愿方案的推进计划和当前阶段。
- `docs/SOURCES.md`：所有数据源、年份、文件路径和用途。
- `docs/VERIFICATION.md`：复核方法和不可省略的人工核验点。
- `docs/GOAL_AND_FRAMEWORK.md`：冲稳保和学校/专业分析框架。
- `docs/VOLUNTEER_FILLING_GUIDE.md`：志愿填报阶段、专业名词和注意事项。
- `docs/MAJOR_DIRECTIONS.md`：当前可能专业方向和后续调研问题。
- `docs/FAMILY_PREFERENCES_AND_CONSTRAINTS.md`：家庭偏好、预算、体检和筛选硬底线。
- `docs/2026_ADMISSION_PLAN_ACQUISITION.md`：2026 招生计划获取来源、接口状态和下一步动作。
- `docs/HUBEI_ADMISSION_MAGAZINE_SEARCH.md`：《湖北招生考试》第 16/19 期专项检索记录。
- `docs/OCR_WORKFLOW.md`：第 19 期纸质版照片 OCR、批量处理和人工复核流程。
- `docs/ISSUE19_PDF_EXTRACTION_PLAN.md`：第 19 期 PDF 私有留存、OCR 提取和数据保存方案。
- `docs/ISSUE19_SAMPLE_DOUBLE_CHECK.md`：第 19 期 OCR 样本学校与学校官网 double check 方案。
- `docs/ISSUE19_FULL_ADMISSION_PLAN_DRAFT.md`：第 19 期全量招生计划 OCR 底座、候选复核工作台和保真机制。
- `docs/CANDIDATE_POOL_V1.md`：第一版可讨论候选池，全部待 2026 计划核验。
- `docs/SCHOOL_CROSSCHECK_SOURCES.md`：高校官网招生计划交叉校验来源。
- `docs/DECISIONS.md`：每天的决策日志。

## 数据目录

- `data/official/`：官方网页、PDF、图片原件。
- `data/derived/`：OCR 文本、解析 CSV、等位分 JSON 和筛选池。
- `data/external/`：第三方辅助数据源本地留存，只用于发现和交叉校验。
- `data/working/`：当前偏好、招生计划导入模板和阶段性工作数据。
- `scripts/`：可重复运行的核验和筛选脚本。
- `CHECKSUMS.sha256`：项目文件哈希清单。

## 快速命令

```bash
python3 scripts/update_checksums.py
python3 scripts/verify_baseline.py
python3 scripts/ocr_magazine_pages.py --input "<第19期照片目录本地私有副本>"
python3 scripts/ocr_pdf_pages.py --pdf "<第19期PDF本地私有副本>" --pages 1-20
python3 scripts/build_issue19_full_admission_plan_ocr_draft.py
python3 scripts/build_issue19_candidate_review_workbench.py
python3 scripts/build_issue19_priority_review_queues.py
python3 scripts/build_issue19_candidate_review_page_packet.py
python3 scripts/build_issue19_integrity_audit_queues.py
python3 scripts/build_issue19_candidate_v2_review_seed.py
python3 scripts/build_issue19_candidate_v2_verification_workbench.py
python3 scripts/build_issue19_full_quality_tiers.py
python3 scripts/build_issue19_major_detail_quality_workbench.py
python3 scripts/build_issue19_foundation_audit.py
python3 scripts/build_issue19_candidate_evidence_ledgers.py
python3 scripts/build_issue19_page_manifest.py
python3 scripts/build_issue19_family_fit_screen.py
python3 scripts/build_issue19_candidate_v3_review_intake.py
python3 scripts/build_issue19_candidate_v3_admission_detail.py
python3 scripts/build_issue19_candidate_v3_admission_detail_review_queue.py
python3 scripts/build_issue19_candidate_v3_d0_resolution_workbench.py
python3 scripts/build_issue19_candidate_v3_b0_b1_review_pack.py
python3 scripts/build_issue19_candidate_v3_b0_b1_official_crosscheck_queue.py
python3 scripts/extract_jsut_official_image_plan.py
python3 scripts/build_issue19_b0_b1_official_evidence_match.py
python3 scripts/build_issue19_b0_b1_fidelity_review_queues.py
python3 scripts/fetch_hubei_plan_platform.py --dry-run-contract
python3 scripts/filter_toudang.py --year 2023 2024 2025 --keywords 武汉 湖北 成都 西安 北京 --min-score 470 --max-score 535
```

注意：`build_issue19_*` 生成的是 OCR 初稿、招生明细、质量审计和复核队列，`机器初判`、质量分层、逐专业 P0/P1 优先级、候选 V3 批次、候选 V3 全量逐专业复核队列、B0/B1 核验包、官方交叉校验表、逐专业证据合并表和保真复核队列只用于安排复核与补证，不是最终报考建议。候选讨论默认使用逐专业招生明细表，组级/学校级表只作索引、投档线、调剂范围和补源入口。
