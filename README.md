# 2026 湖北高考志愿数据底座与核验项目

这个项目用于持续记录、复核和讨论 2026 年湖北普通类首选物理考生的招生计划数据底座、证据链和志愿填报决策过程。
当前公开仓库只保存 OCR/结构化复核底座和核验工作台，不构成最终志愿方案或可填报清单。
当前阶段说“底座数据坐稳”，主要指《湖北招生考试》第 19 期等湖北 2026 招生计划原始数据被准确结构化、可回溯、可复验；不是目标院校、目标专业或志愿方案已经确定。考生分数、位次和家庭底线是固定输入，城市、学校和专业方向仍是后续分析维度，早期提到的城市和专业偏好只作为初始参考。
项目核心目标仍是在 2026-06-30 前形成可执行的学校/专业组/专业排序最终方案。2026-07-02
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
python3 scripts/build_issue19_full_major_field_fidelity_ledger.py
python3 scripts/build_issue19_full_major_verification_batches.py
python3 scripts/build_issue19_priority_group_major_review_pack.py
python3 scripts/build_issue19_priority_major_evidence_workbench.py
python3 scripts/build_issue19_full_major_evidence_workbench.py
python3 scripts/build_issue19_full_major_evidence_closure_tasks.py
python3 scripts/build_issue19_p0_evidence_execution_packets.py
python3 scripts/build_issue19_p0_evidence_review_worklist.py
python3 scripts/build_issue19_major_level_evidence_worktables.py
python3 scripts/build_issue19_major_detail_foundation_release.py
python3 scripts/build_issue19_foundation_closure_batches.py
python3 scripts/build_issue19_field_gap_repair_candidates.py
python3 scripts/build_issue19_b0_b1_official_evidence_sidecar.py
python3 scripts/build_issue19_major_line_pdf_evidence_anchors.py
python3 scripts/build_issue19_foundation_closure_gap_scorecard.py
python3 scripts/build_issue19_major_line_historical_toudang_sidecar.py
python3 scripts/build_issue19_admission_detail_master_workbench.py
python3 scripts/build_issue19_admission_detail_structural_fidelity_register.py
python3 scripts/build_issue19_candidate_filter_prep_major_detail.py
python3 scripts/build_issue19_major_decision_readiness_gates.py
python3 scripts/build_issue19_moe_school_attribute_major_detail.py
python3 scripts/build_issue19_hubei_official_query_key_collision_ledger.py
python3 scripts/build_issue19_foundation_stability_dashboard.py
python3 scripts/build_issue19_foundation_stabilization_major_detail_tasks.py
python3 scripts/build_issue19_official_public_entry_status_snapshot.py
python3 scripts/build_issue19_raw_major_lineage_consistency_audit.py
python3 scripts/build_issue19_raw_major_source_evidence_audit.py
python3 scripts/build_issue19_major_source_evidence_risk_sidecar.py
python3 scripts/build_issue19_field_fact_closure_ledger.py
python3 scripts/build_issue19_field_fact_verification_tasks.py
python3 scripts/build_issue19_field_fact_p0_reread_worklist.py
python3 scripts/build_issue19_major_line_layout_continuity_risk_ledger.py
python3 scripts/build_issue19_major_code_order_risk_ledger.py
python3 scripts/build_issue19_foundation_audit.py
python3 scripts/build_issue19_candidate_evidence_ledgers.py
python3 scripts/build_issue19_page_manifest.py
python3 scripts/build_issue19_page_fidelity_review_queue.py
python3 scripts/build_issue19_family_fit_screen.py
python3 scripts/build_issue19_candidate_v3_review_intake.py
python3 scripts/build_issue19_candidate_v3_admission_detail.py
python3 scripts/build_issue19_candidate_v3_admission_detail_review_queue.py
python3 scripts/build_issue19_candidate_v3_d0_resolution_workbench.py
python3 scripts/build_issue19_candidate_v3_d0_pdf_page_evidence.py
python3 scripts/build_issue19_candidate_v3_b0_b1_review_pack.py
python3 scripts/build_issue19_candidate_v3_b0_b1_official_crosscheck_queue.py
python3 scripts/extract_jsut_official_image_plan.py
python3 scripts/build_issue19_b0_b1_official_evidence_match.py
python3 scripts/build_issue19_b0_b1_fidelity_review_queues.py
python3 scripts/build_issue19_candidate_v3_major_field_fidelity_ledger.py
python3 scripts/fetch_hubei_plan_platform.py --dry-run-contract
python3 scripts/filter_toudang.py --year 2023 2024 2025 --keywords 武汉 湖北 成都 西安 北京 --min-score 470 --max-score 535
```

源证据风险下沉表：`data/working/issue19-major-source-evidence-risk-sidecar.csv` 是当前新增城市、学校或专业方向时的默认逐专业侧账之一，13736 行一行一个招生专业明细，把 `issue19-raw-major-source-evidence-audit.csv` 的源证据覆盖结论、R2/R3/R4 风险、起始行 QC、窗口哈希、底座稳定性、闭环缺口和 P0 复核任务汇到同一条 `专业行ID`。它只说明原始证据定位和核页优先级，不能生成学校或专业建议。

字段事实闭环总账：`data/working/issue19-field-fact-closure-ledger.csv` 是当前核再选科目、专业计划数、学费三项关键字段的默认逐专业入口，13736 行一行一个招生专业明细。它把总工作台、源证据风险、字段缺口候选、湖北官方核验包、B0/B1 官网辅证和决策闸门连到同一条 `专业行ID`，明确哪些字段缺候选、哪些字段有候选待核、哪些行 OCR 三字段齐全但还没有 PDF 原页和湖北官方系统闭环。该表全部 `最终可用=false`，只用于补证和复核，不用于推荐或排序。

字段事实核验任务队列：`data/working/issue19-field-fact-verification-tasks.csv` 把字段事实闭环总账按三项关键字段拆成 41208 条任务，即 13736 条招生专业明细 × 再选科目、专业计划数、学费。它保留 `专业行ID`、字段状态、字段候选、页级证据编号和 SHA，用于按页、按字段、按学校排补证顺序；全部 `最终可用=false`，不自动写回主表，也不用于学校或专业建议。

P0 字段原页重读工作清单：`data/working/issue19-field-fact-p0-reread-worklist.csv` 从字段事实核验任务队列中严格抽取 11444 条 K0 无候选字段任务，覆盖 8536 条招生专业明细、231 个 PDF 明细页和 967 所学校。它把每个 `专业行ID × 字段名` 回连到字段任务、原始源证据审计、PDF 原页锚点和页级保真队列，用于优先回看专业计划数、再选科目、学费三项原始字段；全部 `最终可用=false`、`可进入下一阶段=false`，不得自动写回主表，也不得生成学校或专业建议。

注意：`build_issue19_*` 生成的是 OCR 初稿、招生明细、质量审计、复核队列、统一逐专业底座入口和闭环执行批次，`机器初判`、质量分层、逐专业 P0/P1 优先级、逐专业核验批次、优先整组逐专业核验包、全量逐专业证据执行工作台、证据闭环任务队列、P0 证据执行包、P0 逐专业复核工作清单、统一逐专业底座发布表、底座闭环批次、字段缺口候选修复表、字段事实闭环总账、B0/B1 官网证据旁挂表、专业行原页证据锚点表、逐专业闭环缺口看板、逐专业三年投档线索旁挂表、单一逐专业招生明细总工作台、逐专业结构保真登记表、候选筛选准备表、决策闸门表、教育部学校属性逐专业核验表、湖北官方查询键碰撞清单、底座稳定性总看板、逐专业稳定化任务表、原始专业行血缘审计表、原始专业行源证据审计表、逐专业源证据风险侧账、教育部未匹配校名逐专业解析表、版面连续性风险清单、专业代号顺序风险清单、页级保真复核队列、候选 V3 批次、候选 V3 全量逐专业复核队列、B0/B1 核验包、官方交叉校验表、逐专业证据合并表和字段保真总账只用于安排复核与补证，不是最终报考建议。新增城市、学校或专业方向时，默认先查 `data/working/issue19-field-fact-closure-ledger.csv`、`data/working/issue19-raw-major-source-evidence-audit.csv`、`data/working/issue19-raw-major-lineage-consistency-audit.csv`、`data/working/issue19-major-source-evidence-risk-sidecar.csv`、`data/working/issue19-foundation-stability-dashboard.csv`、`data/working/issue19-foundation-stabilization-major-detail-tasks.csv`、`data/working/issue19-candidate-filter-prep-major-detail.csv`、`data/working/issue19-moe-school-attribute-major-detail.csv` 和 `data/working/issue19-admission-detail-master-workbench.csv`；这些表都保持一行一个招生专业明细。原始专业行血缘审计表确认 13736 条 OCR 专业行全部按 `专业明细源行号=原始CSV数据行号+1` 回连到质量工作台、统一底座、总工作台、结构保真、稳定性看板、PDF 原页锚点、三年投档旁挂和闭环缺口看板，核心字段漂移为 0；源证据审计表进一步确认 13736 条专业明细全部按 `来源页码+版面列+专业起始行号` 精确回连到私有 OCR 起始行、公开页级 manifest、私有窗口 JSONL 和公开原页锚点，起始行哈希、窗口哈希、页级 manifest 均满匹配。它们只能证明“原始数据准确结构化且可追溯”，不能证明字段已是官方最终事实。底座稳定性总看板把每条专业明细分成 B0=2663、B1=4370、B2=5962、B3=542、B4=199，只说明先核什么，不生成填报建议或录取概率；逐专业稳定化任务表进一步把 B0/B1/B2 的 12995 条明细拆成可执行核验任务，仍全部 `最终可用=false`、`可进入下一阶段=false`、`是否允许作为志愿推荐依据=false`。教育部学校属性表只能证明学校登记名单线索：精确命中 13161 条、父校/校区类保守命中 190 条、未匹配待核 385 条；民办线索 2230 条、合作办学线索 34 条、职业本科名称线索 241 条都必须继续阻断或单独讨论。候选是否能进入讨论看 `data/working/issue19-major-decision-readiness-gates.csv` 的阻断闸门；教育部未匹配校名逐专业解析看 `data/working/issue19-moe-unmatched-school-resolution-major-detail.csv`，385 行全部 `机器能否自动替换校名=false`。官方系统回填消歧看 `data/working/issue19-hubei-official-query-key-collision-ledger.csv`。结构风险看 `data/working/issue19-admission-detail-structural-fidelity-register.csv`、`data/working/issue19-structural-risk-major-line-ledger.csv`、`data/working/issue19-major-line-layout-continuity-risk-ledger.csv` 和 `data/working/issue19-major-code-order-risk-ledger.csv`，0 明细专业组看 `data/working/issue19-zero-detail-group-placeholder-workbench.csv`。要安排实际核验顺序时，继续看 `data/working/issue19-foundation-closure-gap-scorecard.csv` 的 S0-S8 动作桶；三年投档只看 `data/working/issue19-major-line-historical-toudang-sidecar.csv` 的同代码线索，不得直接当录取概率。官方公开入口状态看 `data/working/issue19-official-public-entry-status.json`：2026-06-27 计划页仍含“持续更新中/敬请期待”，平台无登录探针仍是 401。底层闭环批次仍是 `data/working/issue19-foundation-closure-major-batches.csv`，C0=5310、C1=7608、C2 主批次=0、C3=609、C4=209，全部仍 `最终可用=false`。C2 主批次为 0 不代表没有官网任务，含官网辅证任务 854 条、B0B1 官网差异任务 854 条已按动作维度单独统计；字段缺口候选修复表有 7621 条非空候选线索，字段事实闭环总账把再选科目、专业计划数和学费拆成 K0/K1/K2 待核状态，B0/B1 官网证据旁挂表有 61 条强辅证、55 条计划数补缺候选和 18 条冲突核页，专业行原页证据锚点覆盖 13736 条明细，但全部不得自动写回最终表。页级索引 231 行、学校索引 1100 行，只作核页顺序和补源入口，不能替代逐专业主表。
