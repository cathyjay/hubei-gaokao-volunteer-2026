# 2026 湖北高考志愿数据底座与核验项目

这个项目用于持续记录、复核和讨论 2026 年湖北普通类首选物理考生的招生计划数据底座、证据链和志愿填报决策过程。
当前公开仓库只保存 OCR/结构化复核底座和核验工作台，不构成最终志愿方案或可填报清单。
当前阶段说“底座数据坐稳”，主要指《湖北招生考试》第 19 期等湖北 2026 招生计划原始数据被准确结构化、可回溯、可复验；不是目标院校、目标专业或志愿方案已经确定。考生分数、位次和家庭底线是固定输入，城市、学校和专业方向仍是后续分析维度，早期提到的城市和专业偏好只作为初始参考。
项目核心目标仍是在 2026-06-30 前形成可执行的学校/专业组/专业排序最终方案。2026-07-02
12:00 前只保留应急修改缓冲；官方本科普通批集中填报截止时间仍为 2026-07-02 17:00。

## 项目规则

- 不保存考生姓名、身份证号、准考证号、报名号等直接身份信息。
- 官方网页、PDF、图片原件是第一证据；OCR/CSV 只是便于筛选的派生数据。
- 证据层级固定为：第 19 期 PDF 原页或纸质原页是省招办原件底座；湖北官方系统在可得时用于官方系统核验和最终代码确认；高校官网、招生章程、官网 API、XLSX、PDF 或图片计划只作为高校侧辅证和差异发现；第三方平台和 OCR 只作为线索。
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
- `docs/EXPANDED_BUDGET_COOP_AND_SPECIAL_TRACKS.md`：7 万预算、中外合作/高收费和军事院校专项讨论入口。
- `docs/2026_ADMISSION_PLAN_ACQUISITION.md`：2026 招生计划获取来源、接口状态和下一步动作。
- `docs/HUBEI_ADMISSION_MAGAZINE_SEARCH.md`：《湖北招生考试》第 16/19 期专项检索记录。
- `docs/OCR_WORKFLOW.md`：第 19 期纸质版照片 OCR、批量处理和人工复核流程。
- `docs/ISSUE19_PDF_EXTRACTION_PLAN.md`：第 19 期 PDF 私有留存、OCR 提取和数据保存方案。
- `docs/ISSUE19_SAMPLE_DOUBLE_CHECK.md`：第 19 期 OCR 样本学校与学校官网 double check 方案。
- `docs/ISSUE19_FULL_ADMISSION_PLAN_DRAFT.md`：第 19 期全量招生计划 OCR 底座、候选复核工作台和保真机制。
- `docs/STABLE_FOUNDATION_V0_STATUS.md`：稳定数据基座 V0 状态，明确“可用于候选发现、不可用于定稿依据”的收口口径。
- `docs/DATA_FOUNDATION_CURRENT_STATUS.md`：数据基座当前推进状态、剩余阻断、我可继续推进的事项和需要家庭配合的事项。
- `docs/DATA_BROWSER_AND_VERIFICATION.md`：结构化数据浏览入口、Excel 工作簿、快速核验抽样和升级规则。
- `docs/CLOSURE_AND_SHORTLIST_V1.md`：字段闭环与重点核验 V1，把第一闭环 37 个页列、206 条任务、80 个高校官网辅证动作、Round4 55 个重点核验组和完整组内专业合到一个入口。
- `docs/NEXT_CLOSURE_AND_FAMILY_REVIEW_V1.md`：下一轮闭环与家庭讨论入口，把第一闭环拆成 64 个小核验包，并把 55 个重点组展开成 458 条完整组内专业明细。
- `docs/DATA_FOUNDATION_NEXT_EXECUTION_V1.md`：数据基座下一批执行工作台，聚焦 P0 冲突 10 包、官网辅证 next20 和 55 组调剂风险。
- `docs/ROUND1_CANDIDATE_SELECTION.md`：第一轮历史候选专业组选择、精选 80、历史优先城市观察和家庭讨论动作。
- `docs/PERSONAL_FIT_CANDIDATES_V1.md`：结合 515 分、91723 位次、家庭偏好和 7 万专项口径生成的个人适配候选讨论池。
- `docs/ROUND2_UPDATED_PREFERENCES.md`：纳入最新体检摘要、护理/动物医学/兽医暂不纳入、医技/康复低优先级专项了解和新增专业方向后的第二轮候选池。
- `docs/ROUND3_UNRESTRICTED_REGION_CANDIDATES.md`：城市和地区不参与筛选、加分或名额分配后的第三轮不限地区候选池。
- `docs/ROUND4_CITY_GRADIENT_CANDIDATES.md`：直接从稳定底座重建、按城市和冲稳保展示的第四轮主讨论候选池。
- `docs/ROUND4_50K_COOP_CITY_GRADIENT_CANDIDATES.md`：Round4 平行专项版，年学费 50000 元以内中外合作/高收费候选池。
- `docs/VOLUNTEER_TABLE_V1_REVIEW_PLAN.md`：本科普通批 45 个院校专业组草表 V1 的分批讨论和二次核验计划。
- `docs/CANDIDATE_POOL_V1.md`：第一版可讨论候选池，全部待 2026 计划核验。
- `docs/SCHOOL_CROSSCHECK_SOURCES.md`：高校官网招生计划交叉校验来源。
- `docs/DECISIONS.md`：每天的决策日志。

## 数据目录

- `data/official/`：官方网页、PDF、图片原件。
- `data/derived/`：OCR 文本、解析 CSV、等位分 JSON 和筛选池。
- `data/external/`：第三方辅助数据源本地留存，只用于发现和交叉校验。
- `data/working/`：当前偏好、招生计划导入模板和阶段性工作数据。
- `data/exports/`：面向浏览、筛选和人工核验的导出层，不替代 `data/working/` 原始结构化底座。
- `scripts/`：可重复运行的核验和筛选脚本。
- `CHECKSUMS.sha256`：项目文件哈希清单。

## 当前浏览入口

- 稳定数据基座浏览：`data/exports/issue19-stable-foundation-browser.xlsx`。用于看第 19 期全量结构化底座、专业组、逐专业明细、观察池和快速核验抽样。
- 7 万预算中外合作专项：`data/exports/issue19-expanded-budget-coop-scenario.xlsx`。用于讨论中外合作/高收费项目是否值得作为花钱换机会的专项线；当前覆盖 853 个专业组、2330 条专业明细，其中预算内中外合作/高收费可讨论 1706 条、预算内高学费可讨论 259 条、费用待核 234 条、超过 70000 元预算 131 条。
- 个人适配候选 V1：`data/exports/issue19-personal-fit-v1.xlsx`。用于结合考生分数、位次、家庭偏好、普通主线和 7 万专项口径看本轮适合继续讨论的院校专业组；当前 45 个专业组、267 条完整组内专业明细，其中 34 个进入或谨慎进入讨论。
- 第二轮更新偏好候选：`data/exports/issue19-round2-updated-preferences.xlsx`。用于纳入最新体检摘要、护理/动物医学/兽医暂不纳入、医技/康复低优先级专项了解和新增专业方向；当前主线精选 100 个专业组、专项精选 80 个专业组、点名观察 15 条记录，全部仍为讨论池。
- 第三轮不限地区候选：`data/exports/issue19-round3-unrestricted-region.xlsx`。用于在不设置城市/地区限制、不按武汉/成都/西安/北京加分、不分配优先城市名额的口径下重新筛选；当前主线精选 120 个专业组、优先讨论 60 个专业组、低优先级专项 25 个专业组，全部仍为讨论池。
- 第四轮城市冲稳保候选：`data/exports/issue19-round4-city-gradient.xlsx`。当前优先入口，直接从稳定底座、教育部学校属性表和三年投档线旁挂表重建；主表 328 个 H1-H4 专业组，优先讨论 120 组，H0 历史待补和 H5 高冲暂缓均单列附录。
- Round4 重点核验55组：`data/exports/issue19-round4-priority-focus55.xlsx`。把 Round4 优先 120 组压缩为 55 组重点核验入口、65 组暂缓，并展开 458 条完整组内专业；用于先看压缩理由、核验成本、调剂风险和家庭最小动作，全部仍为 `not_final`。
- 第四轮 5 万内中外合作/高收费专项：`data/exports/issue19-round4-50k-coop-city-gradient.xlsx`。Round4 平行专项入口，允许公办中外合作/国际合作/高收费项目单独讨论；主表 21 个 H1-H4 专业组，H0 38 组、H5 51 组、费用待核或超 5 万 165 组均单列附录。
- 字段闭环与重点核验 V1：`data/exports/issue19-closure-and-shortlist-v1.xlsx`。当前新增推进入口，把第一闭环 37 个页列、206 条逐任务、36 所学校 80 个高校官网辅证动作、2026-06-29 live 补源尝试、Round4 55 个重点核验组和 458 条完整组内专业明细放在同一工作簿；全部仍为核验入口，不作为定稿依据。
- 下一轮闭环与家庭讨论 V1：`data/exports/issue19-next-closure-family-review-v1.xlsx`。当前推进数据基座的优先执行入口，把 37 个页列继续拆成 64 个小核验包，并把 55 个重点专业组按家庭讨论、先核页、先核限制、先核费用分层；`05_重点组完整专业` 已增加家庭可选项、6 专业讨论候选和服从调剂影响列，全部仍为 `not_final`，字段写回、推荐依据和最终可用计数均为 0。
- 数据基座下一批执行 V1：`data/exports/issue19-data-foundation-next-execution-v1.xlsx`。当前新增执行入口，聚焦 P0 冲突 10 包/26 任务、高校官网辅证 next20 和 55 组调剂风险；用于继续推进字段事实闭环，不确认字段事实，不作为最终志愿方案。
- P0 top3 私有复核包公开台账：`data/working/issue19-p0-top3-review-packet-public-ledger.csv`、`data/working/issue19-p0-top3-field-review-public-ledger.csv` 和 `data/working/issue19-p0-top3-review-packet-summary.json`。把 `135-left`、`199-left`、`209-right` 这 3 个最高优先 P0 冲突包落成 15 条本地私有核验任务，并拆成 36 个逐字段核验单元；公开层只保存计数、状态、关系桶和 SHA，原页图、OCR 文本、候选值和人工读数留在 Git 忽略目录。
- 第一闭环 B0 冲突页列核验状态：`data/working/issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-b0-conflict-status-summary.json`。把 10 个 B0 页列、132 条同页任务和 26 条明确 PDFOCR 与高校辅证冲突任务单独抽出，标记 P0/P1/P3 核验优先级、字段类型、同页 B0/B1 计划数冲突专项口径和三方待核门禁；全部仍为 `not_final`，不得作为字段事实或志愿推荐依据。
- 第一闭环证据状态报告：`data/working/issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv`、`data/working/issue19-stable-foundation-first-closure-evidence-status-page-side-summary.csv` 和 `data/working/issue19-stable-foundation-first-closure-evidence-status-summary.json`。把 206 条第一闭环任务和 37 个页列按 PDF 原页、OCR 提示、机器坐标、高校辅证、冲突状态和写回门禁合成同一公开状态层；全部仍为待核状态，不保存字段值或人工读数。
- 第一闭环公开证据地图：`data/working/issue19-stable-foundation-first-closure-public-evidence-map.csv` 和 `data/working/issue19-stable-foundation-first-closure-public-evidence-map-summary.json`。把 37 个页列压缩成更适合沟通的一张表，逐页列展示 PDF 原页、PDFOCR、机器坐标、高校辅证、湖北官方侧、冲突和双人复核计数；不展示学校专业明细、字段读数或私有材料。
- 第一闭环下一步动作矩阵：`data/working/issue19-stable-foundation-first-closure-next-action-matrix.csv`、`data/working/issue19-stable-foundation-first-closure-next-action-page-summary.csv` 和 `data/working/issue19-stable-foundation-first-closure-next-action-summary.json`。把 206 条任务、37 个页列和同校高校源最新证据对齐，明确 N0-N5 下一步核验动作；全部仍不确认字段事实。
- 第一闭环字段事实公开账本：`data/working/issue19-stable-foundation-first-closure-field-fact-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-field-fact-summary.json`。把 206 条任务展开成 354 个字段原子：计划数 170、学费 105、再选科目 77、待人工判定字段 2；只公开字段闭环状态和 SHA，不公开字段明细值，不允许写回或推荐。
- 第一闭环事实范围缺口账本：`data/working/issue19-stable-foundation-first-closure-fact-scope-gap-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-fact-scope-gap-summary.json`。把第一闭环扩成 439 个待闭环事实范围：字段事实 354、专业名归属 48、专业组边界 37；用于明确底座差什么，不公开学校专业明细或字段值，不允许写回或推荐。
- 第一闭环事实核验包：`data/working/issue19-stable-foundation-first-closure-fact-verification-packets-public-ledger.csv`、`data/working/issue19-stable-foundation-first-closure-fact-verification-items-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-fact-verification-packets-summary.json`。把 439 个事实缺口压成 37 个页列核验包，分为 B0 冲突优先 10 包、专业名归属优先 9 包、缺候选人工看图 2 包、机器坐标辅助 16 包；只用于排核验顺序，不确认字段事实。
- 第一闭环 W0/B0 最小人工复核清单：`data/working/issue19-stable-foundation-first-closure-w0-b0-minimal-manual-packets-public-ledger.csv`、`data/working/issue19-stable-foundation-first-closure-w0-b0-minimal-manual-items-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-w0-b0-minimal-manual-summary.json`。把 B0 冲突优先的 275 个同页待核事实先压成 87 个核心事实、10 个页列、35 个任务：专业组边界 10、明确冲突字段 68、专业名归属 9；用于先核最容易导致串组、字段冲突或归属错位的事实，剩余 188 个同页伴生事实继续待闭环。
- 第一闭环 W0/B0 执行预填审计：`data/working/issue19-stable-foundation-first-closure-w0-b0-execution-prefill-packets-public-audit.csv`、`data/working/issue19-stable-foundation-first-closure-w0-b0-execution-prefill-items-public-audit.csv` 和 `data/working/issue19-stable-foundation-first-closure-w0-b0-execution-prefill-summary.json`。把 10 个页列、87 个核心事实接到 Git 忽略的私有预填 CSV、页图和 OCR 文本哈希；公开层只保存 ID、状态、计数和 SHA，不公开读数，不确认字段事实。
- 数据基座状态快照：`data/working/issue19-data-foundation-status-snapshot.csv` 和 `data/working/issue19-data-foundation-status-snapshot.json`。由 `scripts/build_issue19_data_foundation_status_snapshot.py` 生成，用于快速查看全量结构化、第一闭环、官网辅证、候选压缩和最终门禁状态；它只说明推进状态，不确认字段事实。
- 高校官网辅证状态快照：`data/working/issue19-school-source-status-snapshot-public-ledger.csv` 和 `data/working/issue19-school-source-status-snapshot-summary.json`。由 `scripts/build_issue19_school_source_status_snapshot.py` 生成，把 36 所学校、80 条高校侧辅证机会任务、C4/C6 补结构化/补源包、live 补源记录和最终门禁放到同一张公开状态账本；它只用于安排自动补源、生成 diff、压缩人工核验范围，不能作为字段事实、学校专业建议或志愿推荐依据。
- 高校官网辅证自动执行批次：`data/working/issue19-school-source-auto-execution-batches-public-ledger.csv` 和 `data/working/issue19-school-source-auto-execution-batches-summary.json`。由 `scripts/build_issue19_school_source_auto_execution_batches.py` 生成，在状态快照基础上把 80 条任务拆成 7 条推进泳道：冲突回页 17、补缺回页 8、专业名归属 12、补结构化 18、继续补计划网源 8、章程规则 16、留存观察 1；全部仍禁止字段写回、推荐和最终使用。
- 高校官网 next20 官方源探测：`data/working/issue19-school-source-next20-official-probe-public-ledger.csv` 和 `data/working/issue19-school-source-next20-official-probe-summary.json`。由 `scripts/build_issue19_school_source_next20_probe_ledger.py` 生成，把 next20 的 20 个任务、18 所学校汇总到官方 API/PDF/XLSX/HTML/入口探测状态；当前 15 个任务行已有结构化高校侧辅证，仍只作 double check。
- 高校官网最新证据对齐：`data/working/issue19-school-source-latest-reconciliation-public-ledger.csv` 和 `data/working/issue19-school-source-latest-reconciliation-summary.json`。由 `scripts/build_issue19_school_source_latest_reconciliation.py` 生成，把 80 条高校侧辅证自动执行任务与 next20、live 补源、C4/C6 复用、C4/C6 结构化 diff 和补源尝试对齐；当前 60 条已有湖北物理结构化或候选 diff 线索，12 条只有入口或探针记录，8 条暂无可复用高校侧计划源；A4 继续补源任务中 4 条已经推进到结构化或 diff 线索、4 条仍需补源。它只回答“高校侧辅证推进到哪一步”，不确认字段事实、不允许写回、不作为志愿推荐依据。
- 高校源缺口优先级清单：`data/working/issue19-school-source-gap-priority-public-ledger.csv` 和 `data/working/issue19-school-source-gap-priority-summary.json`。由 `scripts/build_issue19_school_source_gap_priority_ledger.py` 从最新证据对齐账本派生 80 条任务级缺口排序：37 条先人工回页，26 条自动补结构化或补源，17 条规则抽检或留存；所有行仍需 PDF 原页和湖北官方侧核验，不确认字段事实。
- 本科普通批志愿草表 V1：`data/exports/issue19-volunteer-table-v1-draft.xlsx`。基于第二轮更新偏好候选生成，用于把 45 个院校专业组、460 条专业选择明细拆成冲刺、稳冲、稳妥和保底、高费专项批次，逐组讨论 6 个专业草案、完整组内调剂、原页核验和章程核验；全部行仍为讨论草案，不作为定稿依据。

这些工作簿都不是最终志愿方案。进入家庭讨论或最终排序前，仍必须核第 19 期原页、湖北官方系统或省招办计划、高校官网/章程、完整专业组和调剂风险。

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
python3 scripts/build_issue19_school_source_live_20260629_ledger.py
python3 scripts/build_issue19_data_foundation_status_snapshot.py
python3 scripts/build_issue19_official_public_entry_status_snapshot.py
python3 scripts/build_issue19_official_public_entry_live_recheck.py
python3 scripts/build_issue19_official_unavailable_sampling_gates.py
python3 scripts/build_issue19_official_unavailable_sampling_execution_detail.py
python3 scripts/build_issue19_official_unavailable_sampling_review_overlay.py
python3 scripts/build_issue19_official_unavailable_sampling_review_packets.py
python3 scripts/build_issue19_official_unavailable_sampling_review_execution_queue.py
python3 scripts/build_issue19_official_unavailable_sampling_triage_prefill.py
python3 scripts/build_issue19_raw_major_lineage_consistency_audit.py
python3 scripts/build_issue19_raw_major_source_evidence_audit.py
python3 scripts/build_issue19_major_source_evidence_risk_sidecar.py
python3 scripts/build_issue19_field_fact_closure_ledger.py
python3 scripts/build_issue19_field_fact_verification_tasks.py
python3 scripts/build_issue19_field_fact_page_side_verification_queue.py
python3 scripts/build_issue19_page_side_foundation_risk_register.py
python3 scripts/build_issue19_page_side_foundation_verification_batches.py
python3 scripts/build_issue19_page_side_foundation_batch_execution_packets.py
python3 scripts/build_issue19_field_fact_p0_reread_worklist.py
python3 scripts/build_issue19_field_fact_p0_reread_machine_candidates.py
python3 scripts/build_issue19_field_fact_p0_closure_action_workbench.py
python3 scripts/build_issue19_field_fact_p0_semantic_crosssource_audit.py
python3 scripts/build_issue19_field_fact_p0_triage_execution_workbench.py
python3 scripts/build_issue19_field_fact_p0_immediate_review_packet.py
python3 scripts/build_issue19_p0_immediate_pdf_crop_evidence_index.py
python3 scripts/build_issue19_p0_immediate_three_way_closure_ledger.py
python3 scripts/build_issue19_p0_immediate_crop_ocr_audit.py
python3 scripts/build_issue19_p0_immediate_field_confirmation_workbench.py
python3 scripts/build_issue19_p0_immediate_page_review_packets.py
python3 scripts/build_issue19_p0_immediate_pdf_reading_candidates.py
python3 scripts/build_issue19_p0_immediate_page_execution_queue.py
python3 scripts/build_issue19_p0_immediate_page_execution_progress_ledger.py
python3 scripts/build_issue19_major_evidence_level_routing.py
python3 scripts/build_issue19_stable_foundation_screening_views.py
python3 scripts/build_issue19_stable_foundation_group_readiness_bridge.py
python3 scripts/build_issue19_stable_foundation_v0_status.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/export_issue19_stable_foundation_browser.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/export_issue19_expanded_budget_coop_scenario.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_round1_candidate_selection.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_personal_fit_v1.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_round2_updated_preferences.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_round3_unrestricted_region_candidates.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_round4_city_gradient_candidates.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_round4_50k_coop_city_gradient_candidates.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_volunteer_table_v1_draft.py
python3 scripts/build_issue19_stable_foundation_next_closure_workbench.py
python3 scripts/build_issue19_stable_foundation_school_source_refresh_queue.py
python3 scripts/build_issue19_school_source_opportunity_queue.py
python3 scripts/build_issue19_c4_c6_school_source_refresh_execution_packets.py
python3 scripts/build_issue19_c4_c6_retained_source_reuse_audit.py
python3 scripts/fetch_issue19_c4_c6_blcu_official_source.py
python3 scripts/fetch_issue19_c4_c6_xauat_official_source.py
python3 scripts/build_issue19_c4_c6_structured_candidate_diff.py
python3 scripts/build_issue19_c4_c6_school_source_acquisition_attempts.py
python3 scripts/build_issue19_school_source_status_snapshot.py
python3 scripts/build_issue19_school_source_latest_reconciliation.py
python3 scripts/build_issue19_stable_foundation_first_closure_packet.py
python3 scripts/build_issue19_first_closure_review_materials.py
python3 scripts/build_issue19_first_closure_task_review_ledger.py
python3 scripts/build_issue19_first_closure_private_triage_prefill.py
python3 scripts/build_issue19_first_closure_execution_queue.py
python3 scripts/build_issue19_first_closure_pdf_ocr_candidate_audit.py
python3 scripts/build_issue19_first_closure_page_side_candidate_dashboard.py
python3 scripts/build_issue19_first_closure_machine_coordinate_candidate_audit.py
python3 scripts/build_issue19_first_closure_field_confirmation_workbench.py
python3 scripts/build_issue19_first_closure_field_status_dashboard.py
python3 scripts/build_issue19_first_closure_evidence_status_report.py
python3 scripts/build_issue19_first_closure_public_evidence_map.py
python3 scripts/build_issue19_first_closure_next_action_matrix.py
python3 scripts/build_issue19_first_closure_field_fact_public_ledger.py
python3 scripts/build_issue19_first_closure_b0_conflict_status.py
python3 scripts/build_issue19_next_closure_family_review_v1.py
python3 scripts/build_issue19_p0_top3_review_packet.py
python3 scripts/build_issue19_data_foundation_next_execution_v1.py
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

官方公开入口活体复查：`data/working/issue19-official-public-entry-live-recheck.json` 是对湖北教育考试网招生计划页、招生计划索引和湖北招生数智综合平台无登录接口的可复跑检查。它只保存状态码、SHA、标题和 401 探针结果，用来证明当前能自动取得的是官方入口状态，不是可逐字段定稿的官方结构化计划。

C4/C6 高校官网补源尝试账本：`data/working/issue19-c4-c6-school-source-acquisition-attempts-public-ledger.csv` 覆盖当前 C4/C6 剩余补源缺口中的 12 所学校、312 条相关私有明细；公开层只记录学校级 URL、自动探针状态、不可得边界、人工最小核验动作和门禁。它用于回答“湖北官方结构化计划不可直接自动取得时，哪些高校源还能自动 double check，哪些需要人工核验”，不能替代第 19 期原页、湖北官方系统或省招办计划。

官方不可得抽样门禁：`data/working/issue19-official-unavailable-sampling-gates.csv` 在湖北官方结构化计划暂不可无登录取得时，把高校官网 double check 和低风险抽检机械化：C0/C1/C7 共 105 条明细必须 100% 回看第 19 期原页，C2 强辅证抽检最低覆盖 25 条，P3 低风险池抽 25 条；抽检失败按同页列、同校或同组升级 100% 核验。该表仍不允许字段写回、志愿推荐或最终可用。

官方不可得抽样执行明细：`data/working/issue19-official-unavailable-sampling-execution-detail.csv` 把上述门禁继续下沉到 155 条逐专业招生明细：105 条高风险 100% 核验、25 条 C2 强辅证抽样、25 条 P3 低风险抽样。它是后续人工核 PDF 原页、核湖北官方侧和记录抽检结果的逐专业入口，仍不确认字段事实。

官方不可得抽样复核 Overlay 公开账本：`data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv` 把这 155 条执行明细接到 Git 忽略的本地复核表。公开账本只同步记录 SHA、PDF 原页/湖北官方侧/高校辅证已填计数、抽检失败和升级状态，当前 155 条全部为 `R0-Overlay已生成未填写`；学校专业明细、字段读数、复核记录和备注正文只留在本地 Overlay。它解决的是“官方不可得时如何少量人工核验且可追溯”，不是字段核准或志愿推荐。

官方不可得抽样页列核验包公开账本：`data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv` 把上述 155 条抽样复核明细压缩成 46 个 `PDF页码×版面列` 私有核页包，覆盖 40 个 PDF 页。公开账本只保留页列计数、证据编号、SHA 和 R0 状态；私有 HTML/CSV 才展示页图、OCR 行、学校专业线索和人工填写栏。它用于降低人工核验定位成本，不改变抽样范围，也不确认字段事实。

官方不可得抽样页列执行队列：`data/working/issue19-official-unavailable-sampling-review-execution-queue.csv` 把 46 个页列核验包排成 E0-E4 五条执行泳道：E0 冲突/错位先核 7 个、E1 官网未匹配专业名归属 11 个、E2 官网补缺候选核页 3 个、E3 C2 强辅证抽检 2 个、E4 P3 低风险抽检 23 个。公开队列只保存页列顺序、计数、证据编号、SHA、升级规则和非最终门禁，仍不公开学校专业明细、字段读数或人工记录。

官方不可得抽样私有预填公开审计：`data/working/issue19-official-unavailable-sampling-triage-prefill-public-audit.csv` 把 46 个页列执行队列接到 Git 忽略的私有预填工作台。私有层预填 155 条明细的高校官网专业名、计划数、学费、选科和 OCR 线索；公开层只保留页列计数、17 个高校来源文件的聚合计数、私有 CSV SHA 和非最终门禁。它减少人工核页查找成本，但不确认字段事实、不替代湖北官方计划。

全量字段页列核验队列：`data/working/issue19-field-fact-page-side-verification-queue.csv` 把 41208 条逐字段任务按 `PDF页码×版面列` 聚合成 462 个页列执行单元，覆盖 231 个招生计划明细页、13736 条专业明细。当前 450 个页列为 V0 无候选阻断页列先核，12 个为 V1 有候选待人工核验页列；所有任务都仍需要 PDF 原页和湖北官方侧核验，字段写回、推荐依据和最终可用计数均为 0。该表只回答“全量字段应该按哪些页列核”，不代替一行一个专业的明细表。

页列底座综合风险登记表：`data/working/issue19-page-side-foundation-risk-register.csv` 在全量字段页列核验队列基础上，继续合并总工作台、结构保真登记、结构风险、版面连续性、专业代号顺序、湖北官方查询键碰撞、教育部未匹配校名、B0/B1 官网差异、决策闸门和源证据风险侧账，仍保持 462 个 `PDF页码×版面列` 执行单元。当前 460 个页列为 Z0、2 个页列为 Z1；该表只公开风险计数、分布、证据集合 SHA 和非最终门禁，不公开院校名、专业名、专业代号、专业组代码、候选值、人工读数、OCR 原文或私有路径。

页列底座核验批次表：`data/working/issue19-page-side-foundation-verification-batches.csv` 把上述 462 个 `PDF页码×版面列` 执行单元按风险顺序切成 19 个可执行批次，前 18 批各 25 个页列、最后 1 批 12 个页列。该表继续只公开批次、页列、风险计数、集合 SHA 和非最终门禁，当前 462 行全部为 R0 未开始，字段事实写回、下一阶段、志愿推荐和学校专业建议计数均为 0。

页列底座批次执行包：`data/working/issue19-page-side-foundation-batch-execution-packets.csv` 把 19 个页列底座核验批次提升为批次级执行入口，并在本地私有目录生成每批 HTML/CSV 核页材料。公开表只保存 19 行批次计数、私有材料证据编号和 SHA、状态和非最终门禁，不公开识别行内容、页图路径、学校专业明细、字段读数或人工记录；当前 19 批全部仍为 R0，PDF 原页、湖北官方侧、结构/官方消歧和高校辅证完成页列数均为 0。

页列底座公开核页进度账本：`data/working/issue19-page-side-foundation-review-progress-public-ledger.csv` 把 19 批私有核页材料的填写状态同步为 462 个 `PDF页码×版面列` 的公开状态机，覆盖 231 页、13736 条专业明细、41208 个字段任务。当前 462 个页列全部为 `R0-未开始私有核页记录`，PDF 原页、湖北官方侧、结构/官方消歧、高校辅证、升级条件、推荐依据和最终可用计数全部为 0；公开表只保存页列状态、计数、证据编号和 SHA，不公开识别行内容、页图路径、学校专业明细、字段值、核页记录内容或补充记录内容。

页列底座字段线索公开审计：`data/working/issue19-page-side-foundation-field-clue-public-audit.csv` 在公开进度账本之后，把 41208 个逐字段任务重新聚合到 462 个页列，硬校验每个页列的字段任务回链、字段名分布、P/K/Q 状态桶、线索缺失、冲突线索、PDF/湖北官方待核状态和私有字段线索模板 SHA。当前 29764 个字段任务已有某种线索、11444 个字段任务缺线索、1137 个字段任务存在多值/冲突/疑似信号，但 41208 个字段任务仍全部待 PDF 原页和湖北官方侧核验；推荐依据、学校专业建议、下一阶段和最终可用计数均为 0。公开表只保存计数、状态桶和 SHA，不公开院校名、专业名、专业代号、专业组代码、字段候选值、人工读数、OCR 原文或私有路径。

页列底座人工复核 Overlay 公开账本：`data/working/issue19-page-side-foundation-human-review-overlay-public-ledger.csv` 在字段线索模板之上新增一层可填写的人工复核记录层。机器生成的字段线索模板保持不可变，后续 PDF 原页人工读数、湖北官方字段值、高校官网或章程辅证值、字段确认值和双人复核记录只写入 Git 忽略的私有 Overlay；公开账本只同步 462 个页列的 Overlay 记录数、私有 CSV SHA、已填字段计数、三方一致性可评估计数和非最终门禁。当前私有 Overlay 已覆盖 19 批、41208 个字段任务，缺失 0；人工填写、字段确认、推荐依据和最终可用计数仍全部为 0。它解决的是“后续怎么安全复核、复核记录不覆盖原始线索”，不是“字段已经核准”。

第 1 批样板复核公开审计：`data/working/issue19-page-side-foundation-batch-01-sample-public-audit.csv` 用第 1 批 25 个页列先验证流程，覆盖 23 个 PDF 页、717 条招生专业明细、2151 个字段任务。公开表只保留页列级分布、候选数量、动作桶、私有样板详表 SHA 和非最终门禁；私有样板详表才保留学校/专业/字段候选和回页线索。当前样板显示 Q0 无候选 831 个字段、Q1 带候选待核 1071 个字段、Q2 OCR 齐全但待 PDF/湖北官方闭环 249 个字段；正式 Overlay 写回、推荐依据和最终可用仍全部为 0。

全 19 批复核公开账本：`data/working/issue19-page-side-foundation-all-batch-review-public-ledger.csv` 已把上述样板扩展到 462 个页列、231 个 PDF 页、13736 条招生专业明细和 41208 个字段任务；公开表只保存计数、状态分布、私有详表 SHA 和非最终门禁，不公开学校专业明细、字段候选、OCR 原文或人工读数。当前 Q0=15813、Q1=21606、Q2=3789；人工填写、字段确认、推荐依据和最终可用仍全部为 0。

逐专业证据等级与核验路由表：`data/working/issue19-major-evidence-level-routing.csv` 是官方结构化计划暂不可公开自动取得时的逐专业核验导航，13736 行一行一个招生专业明细。当前 L3 高校辅证加第三方提示 854 条，L4 OCR 或单源线索 12882 条；P0 100% 人工核验 5043 条，P1 页列集中核验 7952 条，P2 自动官网核验后人工确认 557 条，P3 低风险抽检 184 条。它只决定先核什么、怎么 double check、什么时候升级人工，不确认字段值，也不生成学校专业建议。

稳定基座筛选视图：`data/working/issue19-stable-foundation-major-screening-view.csv` 和 `data/working/issue19-stable-foundation-group-screening-view.csv` 是后续筛学校、专业和专业组的当前统一入口。逐专业视图覆盖 13736 条招生明细，专业组视图覆盖 3329 个院校专业组并保留完整组内专业索引；当前 678 条逐专业明细可作为机器初筛线索但不可定案，1666 个专业组进入机器初筛观察池，所有最终门禁仍为 0。它们只用于把家庭底线、教育部学校属性、字段缺口、证据路由、三年投档线索和整组调剂风险放到同一处看，不替代 PDF 原页、湖北官方系统或省招办计划。

稳定基座专业组就绪桥接表：`data/working/issue19-stable-foundation-group-readiness-bridge.csv` 把 3329 个专业组按“离候选讨论还差什么证据”重新分层，并把第一闭环、高校侧辅证刷新和完整专业组底线接到同一处。当前 41 个专业组已进入第一闭环，1287 个专业组主要卡在字段事实缺口，1665 个专业组卡在结构或归属未闭环；该表只用于复核排队和候选讨论准备，不确认字段事实、不生成志愿排序。

稳定基座下一步闭环工作台：`data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv` 和 `data/working/issue19-stable-foundation-minimal-manual-closure-workbench.csv` 把“官方公开结构化源暂不可得”的替代保真路线落成两张可执行表。前者覆盖 854 条 B0/B1 高校官网辅证，分成 19 条冲突先核、55 条官网补缺候选、66 条强辅证抽检、411 条部分来源补结构化、190 条继续补源等动作；后者覆盖 319 条 P0 即时字段任务，按 148 个页列集中人工核 PDF 原页和湖北官方侧。两张表全部保持 `最终可用=false`、`是否允许作为志愿推荐依据=false`、`是否允许官网证据替代湖北官方计划=false`。

高校侧辅证刷新公开账本：`data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv` 把上述 854 条 B0/B1 高校辅证任务按 `高校×高校侧辅证动作` 聚合成 80 条公开刷新任务，覆盖 36 所学校。它用于自动复跑高校官网/API/XLSX/PDF/图片来源、补结构化、继续补源和分层抽检；公开层只保存任务桶、计数、集合 SHA、公开来源数量和非最终门禁，私有工作台才记录复跑结果和人工核验结论。当前 S0 PDF 原页与湖北官方优先闭环 15 条、S1 专业名匹配人工确认 12 条、S2 高校官网来源结构化刷新 23 条、S3 强辅证分层抽检 11 条、S4 继续补高校官网计划源 14 条、S5 章程规则核特殊限制 5 条；它能减少人工打开学校官网的工作量，但不能替代第 19 期 PDF 原页和湖北官方侧。

高校官网自动辅证机会队列：`data/working/issue19-school-source-opportunity-queue.csv` 在 80 条高校侧刷新任务上增加自动收益分和执行建议序号，优先处理冲突、补缺、官网专业名未匹配和高收益缺源学校。当前前 10 个自动补源/复核对象为武汉轻工大学、长春工业大学、湖北师范大学、江汉大学、浙江传媒学院、西北民族大学、西安邮电大学、南宁学院、西安建筑科技大学、喀什大学；该队列仍只生成候选 diff、补源证据或抽检任务，所有推荐和写回门禁为 0。

高校官网辅证状态快照：`data/working/issue19-school-source-status-snapshot-public-ledger.csv` 和 `data/working/issue19-school-source-status-snapshot-summary.json` 把 80 条官网辅证机会任务继续汇总为可追踪状态层，覆盖 36 所学校。当前 P0 立即处理 44 条、P1 高收益自动补源 18 条、P2 常规自动补源或抽检 13 条、P3 低收益留存 5 条；36 条任务结论为高风险冲突或补缺需先核 PDF 原页和湖北官方侧，17 条已有高校侧结构化线索但不得写回，21 条需补结构化、匹配规则或继续找 2026 湖北物理类计划网源，5 条只核章程规则限制。该快照公开层只保存学校、任务桶、来源数量、集合 SHA、状态桶和非最终门禁，不保存 URL 正文、字段值、OCR 原文、人工记录或登录态。

高校官网辅证自动执行批次：`data/working/issue19-school-source-auto-execution-batches-public-ledger.csv` 和 `data/working/issue19-school-source-auto-execution-batches-summary.json` 把上述 80 条任务进一步落成可执行推进泳道，覆盖 36 所学校。当前 A0 冲突回页 17 条、A1 官网补缺回页 8 条、A2 专业名归属 12 条、A3 补结构化 18 条、A4 继续搜索高校计划网源 8 条、A5 章程规则 16 条、A7 留存观察 1 条；同时记录结构化状态、候选 diff 状态、补源状态和闭环阻断状态。该账本只安排自动补源、补结构化、候选 diff 和人工最小核验，仍不能替代第 19 期 PDF 原页、湖北官方系统或省招办计划。

C4/C6 高校源刷新执行包：`data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv` 把上述学校刷新账本里最大的自动化缺口单独拆出，覆盖 36 个高校源刷新包、30 所学校和 601 条私有逐专业执行明细。其中 C4 22 个包、411 条明细需要补湖北物理行结构化，C6 14 个包、190 条明细需要继续找或获取高校官网 2026 湖北计划源。公开层只保存包级计数、泳道、集合 SHA 和私有 CSV SHA，不保存专业字段值、OCR 原文或人工记录；它只用于并行补源和生成后续 diff，不能替代湖北官方计划。

C4/C6 已留存官网源复用审计：`data/working/issue19-c4-c6-retained-source-reuse-public-ledger.csv` 把 36 个 C4/C6 执行包同 446 条已留存高校官网标准化证据做保守匹配，公开层只保留包级计数和私有明细 SHA。当前 17 个包已有可复用官网源，601 条私有明细中 206 条有专业名匹配、85 条出现计划数一致候选、104 条可提示 OCR 计划数漏识、19 条存在计划数冲突；这些只生成候选 diff 和核验优先级，不写回字段事实。

北京语言大学 C6 官方 API 原始源：`data/external/issue19-c4-c6-official-sources/blcu-2026-hubei-physics-normal.json` 已从北京语言大学招生系统无登录 API 留存，公开账本为 `data/working/issue19-c4-c6-blcu-official-source-fetch-public-ledger.csv`。该源返回 2026 湖北物理类普通类 14 条逐专业计划、计划数合计 34；它是高校侧辅证，仍不能替代第 19 期 PDF 原页和湖北官方侧。

西安建筑科技大学 C4/C6 官方 API 原始源：`data/external/issue19-c4-c6-official-sources/xauat-2026-hubei-physics-normal.json` 已从西安建筑科技大学招生系统无登录 API 留存，公开账本为 `data/working/issue19-c4-c6-xauat-official-source-fetch-public-ledger.csv`。该源返回 2026 湖北物理类普通类 20 条逐专业计划、计划数合计 80；它缺湖北院校专业组代码、学费和专业代号，只能作高校侧辅证。

C4/C6 结构化候选 diff：`data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv` 把既有 446 条高校官网标准化证据与北京语言大学、西安建筑科技大学新增 API 源合并成 480 条综合结构化高校源，再对 36 个 C4/C6 执行包、601 条私有逐专业明细做自动 double check。当前 21 个包已有结构化源、20 个包可生成候选 diff；专业名匹配 232 条、计划数一致候选 97 条、OCR 计划数缺失但官网可补 113 条、计划数冲突 25 条。公开层只保留包级计数和私有 SHA，逐专业 OCR、官网字段和冲突正文留在本地私有明细；该表用于缩小人工核验范围，不确认字段事实。

第一闭环批次包：`data/working/issue19-stable-foundation-first-closure-detail-packet.csv` 和 `data/working/issue19-stable-foundation-first-closure-page-side-packet.csv` 把最高优先级的 C0/C1/C7 官网辅证任务和 EXEC-01/02/03 P0 字段任务合并成第一批可执行核验包。当前 206 条明细任务被压缩到 37 个 `PDF页码×版面列`、32 个 PDF 页；其中 29 个页列含计划数冲突或补缺，30 个页列需要双人复核。该包只决定“先核哪些页列、哪些字段和哪些官网线索”，仍不确认字段事实，不替代湖北官方计划，不生成学校专业建议。

第一闭环复核材料公开账本：`data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-review-summary.json` 把上述 37 个页列接到 Git 忽略的私有 HTML/CSV 复核材料。公开层只保存页列、任务计数、优先级、私有材料 SHA、回链状态和非最终门禁；私有层才展示页图、OCR 行和待填写字段。当前 37 个页列全部为 `R0-Overlay已生成未填写`，206 条任务中自动官网辅证 105 条、人工字段核页 101 条，完成计数、推荐依据、字段写回、学校专业建议和最终可用仍全部为 0。

第一闭环任务级复核公开账本：`data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-task-review-summary.json` 把同一批 206 条任务逐条回连到 37 个页列材料、PDF 原页待核、湖北官方侧待核、高校辅证线索、双人复核要求和公共高校来源文件 SHA。它只回答“每条任务卡在哪条证据链、下一步怎么核”，不公开字段读数、不确认字段事实、不进入学校专业建议。

第一闭环私有预填公开审计：`data/working/issue19-stable-foundation-first-closure-triage-prefill-public-audit.csv` 和 `data/working/issue19-stable-foundation-first-closure-triage-prefill-summary.json` 把 206 条第一闭环任务的高校侧辅证候选只预填到 Git 忽略的私有工作台，公开层只保留 37 个页列的任务计数、私有 CSV SHA 和非最终门禁。当前 74 条任务有公共高校来源文件线索，35 条含学费线索，48 条含选科线索；这些都只是核页提示，不替代第 19 期 PDF 原页、湖北官方侧核验或字段确认。

第一闭环核验执行队列：`data/working/issue19-stable-foundation-first-closure-execution-queue.csv` 和 `data/working/issue19-stable-foundation-first-closure-execution-queue-summary.json` 把上述 37 个页列排成公开可执行顺序：E0 冲突异常双人优先核验 18 个、E1 计划数补缺或偏大优先核验 11 个、E2 官网未匹配专业名归属核验 8 个。该队列只公开页列顺序、计数、证据编号、SHA、完成条件和门禁，不公开学校专业明细、候选值、人工读数、识别正文或私有路径；当前 PDF 原页、湖北官方侧、高校辅证、字段写回和最终可用完成数全部为 0。

第一闭环 PDF OCR 候选公开审计：`data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv` 和 `data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit-summary.json` 覆盖同一批 206 条第一闭环任务，把私有复核材料里的 PDF OCR 候选和高校辅证线索转成公开状态桶。当前 103 条任务已有 PDF OCR 候选，103 条仍需人工看图，26 条存在 PDF OCR 与高校辅证冲突，13 条存在一致字段但仍需官方闭环；公开层只保存候选存在性、关系桶、计数、证据编号和门禁，不保存候选值、学校专业明细、识别正文或私有路径。

第一闭环页列候选看板：`data/working/issue19-stable-foundation-first-closure-page-side-candidate-dashboard.csv` 和 `data/working/issue19-stable-foundation-first-closure-page-side-candidate-dashboard-summary.json` 把上述 206 条任务聚合回 37 个 `PDF页码×版面列`。当前 10 个页列先核 PDF OCR 与高校辅证冲突，21 个页列先人工看图补 PDF 原页读数，6 个页列按 PDF OCR 候选逐条人工确认；公开层只保存页列状态桶、计数、证据编号、SHA 和门禁，不保存候选明细、学校专业明细、识别正文或私有路径。

第一闭环机器坐标候选公开审计：`data/working/issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit.csv` 和 `data/working/issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit-summary.json` 复用 P0 字段机器坐标候选表，专门处理 103 条原本缺 PDF OCR 候选的第一闭环任务。当前 49 条任务从“无 PDF OCR 候选”提升为“有机器坐标候选待人工核页”，其中专业计划数 44 条、学费 5 条；仍有 54 条需要人工看图或人工判定字段。机器坐标候选只在私有工作台保存字段明细，公开层只保存状态桶和计数，全部 `最终可用=false`、`可进入下一阶段=false`、`是否允许作为志愿推荐依据=false`、`机器坐标是否允许自动写回主表=false`。

第一闭环字段确认公开账本：`data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger-summary.json` 把同一批 206 条任务从“候选提示层”推进到“私有人工记录状态机”。公开层只保存 PDF OCR、机器坐标、高校辅证三类提示是否存在、人工核验泳道、PDF 原页/湖北官方/高校辅证私有记录状态、双人复核状态和门禁；候选值、人工读数、湖北官方字段值、学校辅证字段值和复核备注只写入 Git 忽略的私有工作台。当前 26 条任务为 PDFOCR 与高校辅证冲突双人核页、49 条为机器坐标候选辅助核页、77 条为 PDFOCR 候选人工确认、54 条为无候选人工看图；206 条 PDF 原页和湖北官方侧记录均待完成，91 条需要双人复核，字段写回、推荐依据、学校专业建议和最终可用计数仍全部为 0。

第一闭环字段状态看板：`data/working/issue19-stable-foundation-first-closure-field-status-dashboard.csv` 和 `data/working/issue19-stable-foundation-first-closure-field-status-dashboard-summary.json` 把上述 206 条字段确认任务重新压缩到 37 个 `PDF页码×版面列`。当前主阻断为：10 个页列先核 PDFOCR 与高校辅证冲突，4 个页列缺 PDFOCR 候选需人工看图，17 个页列可用机器坐标辅助核页，6 个页列按 PDFOCR 候选人工确认；拆字段计数为专业计划数 170、学费 105、再选科目 77、待人工判定字段 2。该看板只公开页列级状态、计数、集合 SHA 和门禁，不保存字段明细、候选明细、院校专业明细或私有路径；字段写回、推荐依据、学校专业建议和最终可用仍全部为 0。

第一闭环证据状态报告：`data/working/issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv`、`data/working/issue19-stable-foundation-first-closure-evidence-status-page-side-summary.csv` 和 `data/working/issue19-stable-foundation-first-closure-evidence-status-summary.json` 把 206 条任务级状态和 37 个页列级状态并排合成一个公开入口。当前 PDFOCR 提示 103 条、机器坐标提示 49 条、高校辅证线索 74 条、PDFOCR 与高校辅证冲突 26 条、PDFOCR 无候选 103 条，其中真正无候选需人工看图 54 条；直接看图 80 条、双人复核 91 条。该报告只公开状态桶、计数、ID、SHA 和下一步动作，不公开字段值、OCR 原文、学校专业明细、人工记录或私有路径；PDF 原页、湖北官方侧、高校辅证和三方闭环全部完成前，字段写回、推荐依据、学校专业建议和最终可用仍全部为 0。

第一闭环公开证据地图：`data/working/issue19-stable-foundation-first-closure-public-evidence-map.csv` 是更适合快速沟通的页列级视图，一行一个 `来源页码×版面列`。它保留 37 行、206 条任务、32 个 PDF 页的守恒关系，并显示 26 条 PDFOCR 与高校辅证冲突、103 条 PDFOCR 提示、103 条无 PDFOCR 候选、49 条机器坐标提示、74 条高校辅证线索和 91 条双人复核任务；仍不确认任何字段事实。

第一闭环 B0 冲突页列核验状态：`data/working/issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-b0-conflict-status-summary.json` 把字段状态看板中的 10 个 B0 页列进一步单独抽出。当前 10 个页列覆盖 132 条同页任务，其中 26 条是明确 PDFOCR 与高校辅证冲突，106 条是同页伴生待闭环任务；B0 冲突字段类型为计划数 26、学费 26、再选科目 16。该表同时区分全局 B0/B1 计划数冲突专项 19 条和落在 B0 页列内的 18 条，防止把统计口径混用。公开层只保存页列级计数、字段类型、证据编号、状态桶和集合 SHA，不保存学校专业明细、字段候选值、OCR 原文、人工读数或私有路径；字段写回、推荐依据、学校专业建议和最终可用仍全部为 0。

第一闭环 W0/B0 最小人工复核清单：`data/working/issue19-stable-foundation-first-closure-w0-b0-minimal-manual-packets-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-w0-b0-minimal-manual-items-public-ledger.csv` 从 B0 冲突优先包中抽取最小先核集合。当前 10 个页列的 W0 待核事实共 275 个，先核 87 个核心事实：10 个专业组边界、68 个明确冲突字段、9 个专业名归属；字段类型为计划数 26、学费 26、再选科目 16。该清单只安排人工最小复核顺序，便于先处理串组、字段冲突和归属错位，不确认字段事实；PDF 原页、湖北官方侧、字段写回、推荐依据、学校专业建议和最终可用仍全部为 0。

第一闭环 W0/B0 执行预填审计：`data/working/issue19-stable-foundation-first-closure-w0-b0-execution-prefill-packets-public-audit.csv` 和 `data/working/issue19-stable-foundation-first-closure-w0-b0-execution-prefill-items-public-audit.csv` 是上述 87 个核心事实的执行层。它已经生成 10 个页列私有预填 CSV，并对页列 CSV、原页图、OCR 文本和逐条私有预填记录保存 SHA256，方便后续人工打开私有材料逐条核 PDF 原页；公开表仍只保存回链、状态、计数和哈希，不公开学校专业明细、OCR 正文、字段读数或人工记录，不确认任何字段事实。

P0 字段原页重读工作清单：`data/working/issue19-field-fact-p0-reread-worklist.csv` 从字段事实核验任务队列中严格抽取 11444 条 K0 无候选字段任务，覆盖 8536 条招生专业明细、231 个 PDF 明细页和 967 所学校。它把每个 `专业行ID × 字段名` 回连到字段任务、原始源证据审计、PDF 原页锚点和页级保真队列，用于优先回看专业计划数、再选科目、学费三项原始字段；全部 `最终可用=false`、`可进入下一阶段=false`，不得自动写回主表，也不得生成学校或专业建议。

P0 字段机器坐标候选表：`data/working/issue19-field-fact-p0-reread-machine-candidates.csv` 在 P0 原页重读工作清单的 11444 条 K0 字段任务上，使用私有 OCR 窗口坐标和保守字段规则生成机器候选，仍是一行一个 `专业行ID × 字段名`。当前非空候选 4840 条，其中专业计划数 2175 条、再选科目 1994 条、学费 671 条；6386 条仍未找到坐标候选，218 条为多值冲突。该表只把部分 K0 字段推进到“有候选待人工核页”，公开输出仅保留候选值、坐标摘要、必要来源 ID、页码/版面列、字段名、证据编号、哈希和非最终门禁，不保存 OCR 窗口原文、院校名、专业名、专业代号或专业组代码，全部 `最终可用=false`、`可进入下一阶段=false`、`机器是否允许自动写回主表=false`、`机器是否允许自动回填候选=false`，不得生成学校或专业建议。

P0 字段闭环推进工作台：`data/working/issue19-field-fact-p0-closure-action-workbench.csv` 继续保持 11444 条 `专业行ID × 字段名` 粒度，把机器候选表、P0 原页重读清单和字段事实闭环总账合成可执行核页台账。当前 A1/A1R 快速候选核页 4840 条、A2 多值冲突核页 218 条、A3 无候选重读 6386 条；PDF 原页人工读数、湖北官方字段值、高校官网或章程字段值和三方闭环计数均为 0。该表只安排 PDF 原页、湖北官方系统或省招办计划、高校官网或章程三方核验动作，不把机器候选写成事实。

P0 字段语义与多源线索审计表：`data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv` 继续保持 11444 条 `专业行ID × 字段名` 粒度，把机器候选做语义范围检查，并把已有 B0/B1 高校官网/章程辅证字段值、湖北官方核验包待核状态并列到同一条任务。当前机器候选语义异常 15 条、计划数偏大需重点核页 11 条；高校侧字段线索 75 条，其中机器候选与高校辅证一致 22 条、冲突 1 条、官网有规范字段但机器无候选 52 条。该表只排核页优先级，PDF 原页人工读数、湖北官方字段值和三方闭环仍全部为空，不写回字段、不生成学校专业建议。

P0 字段三方核验执行工作台：`data/working/issue19-field-fact-p0-triage-execution-workbench.csv` 把同一批 11444 条字段任务转成稳定执行顺序，并逐行并上 PDF 原页锚点、机器候选、B0/B1 高校官网/章程字段线索和湖北官方待核包。当前执行批次为冲突异常立即核页 16 条、计划数偏大重点核页 11 条、高校辅证线索三方核验 74 条、多值坐标冲突核页 218 条、常规机器候选核页 4791 条、无候选原页重读 6334 条；245 条要求双人复核。该表仍只是核验派单表，所有 PDF 人工读数、湖北官方字段值、高校官网或章程字段值为空，写回、推荐、下一阶段和最终可用门禁全部为 0。

P0 字段即时复核包：`data/working/issue19-field-fact-p0-immediate-review-packet.csv` 是从 P0 字段三方核验执行工作台严格切出的 319 条最高优先级任务，范围只包含冲突异常立即核页 16 条、计划数偏大重点核页 11 条、高校辅证线索三方核验 74 条、多值坐标冲突核页 218 条；覆盖 319 条招生专业明细、114 个 PDF 页、202 个院校代码和 222 个执行包。该包只是先核哪 319 个字段的派单入口，仍是一行一个 `专业行ID × 字段名`，不聚合学校或专业组，不写回字段，不生成学校或专业建议。

P0 即时复核裁图证据索引：`data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv` 对上述 319 条任务逐条生成本地 PDF 原页裁图，并在公开表只保存裁图证据编号、裁图文件 SHA256、裁图规格 SHA256、页码、版面列、bbox、页图/窗口哈希和非最终门禁；覆盖 114 个 PDF 页、148 个页码×版面列组合。它只证明每条字段任务可定位、可回看、可复验，不保存字段读数、院校名、专业名、专业代号、专业组代码或图片路径，也不写回字段、不生成学校或专业建议。

P0 即时三方闭环公开账本：`data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv` 把同一批 319 条即时复核任务继续下沉到“PDF 原页、湖北官方系统或省招办计划、高校官网或招生章程”三条证据链的独立状态；公开表只保存任务 ID、证据编号、SHA、bbox、状态和门禁，不保存具体字段读数、本地裁图路径、复核备注或最终确认值。当前高校字段线索 75 条，其中机器/高校可比对 23 条，22 条一致、1 条冲突，另有 52 条高校补缺线索；这些只决定优先核验顺序，全部仍为 pending/blocked/false。

P0 即时裁图 OCR 公开审计：`data/working/issue19-p0-immediate-crop-ocr-public-audit.csv` 把 319 张私有裁图再跑一次 Apple Vision OCR，并只公开识别状态、候选关系、SHA 和门禁。当前 319 张均有识别行，253 条有可比 OCR 候选，50 条进入“裁图 OCR 提示冲突优先人工核页”，35 条与既有线索一致但仍待三方核验，66 条未能稳定补读需人工看图；具体识别文本、候选读数和图片路径只在本地私有文件，不能写回字段事实。

P0 即时字段确认公开账本：`data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv` 把同一批 319 条即时复核任务继续转成“私有人工记录 -> 公开状态机”的桥。公开表只保存字段确认状态、证据编号、SHA、bbox、关系状态和门禁，不保存字段记录值、候选值、识别文本或图片路径；当前 319 条 PDF 原页和湖北官方私有记录均待完成，75 条需要高校辅证私有记录，290 条需要双人复核，全部仍阻断在字段写回评估前。

P0 即时按页核页包：`data/working/issue19-p0-immediate-page-review-packets.csv` 把上述 319 条字段确认任务按 `PDF页码×版面列` 聚合成 148 个执行包，覆盖 114 个 PDF 页，公开表只保存页列任务数、证据编号集合、SHA、bbox 摘要、状态和门禁；本地私有 HTML 才显示裁图和候选线索。这个表用于人工逐页逐列核 PDF 原页，防止左右列串读，不生成字段事实、学校专业建议或最终方案。

P0 即时 PDF 原页读数候选公开审计：`data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv` 把字段确认账本、裁图 OCR 审计和按页核页包接到同一批 319 条任务上。公开表只保存候选存在状态、候选关系、审阅桶、证据编号、SHA、bbox 和门禁；具体候选读数、OCR 行文本和图片路径只在 Git 忽略的私有表里。当前 253 条有私有 PDF 原页读数候选，66 条需要人工直接看图，99 条需要直接图像复核，290 条需要双人复核，所有行 `是否可自动写入人工读数=false`、`最终可用=false`。

P0 即时页列核页执行队列：`data/working/issue19-p0-immediate-page-execution-queue.csv` 把 148 个 `PDF页码×版面列` 包按新候选层重新排序。当前 11 个页列包为候选冲突先核，34 个为无稳定候选先看图，11 个为候选一致但仍需官方闭环，92 个为常规候选人工确认；队列覆盖同一批 319 条字段任务，仍不保存候选读数、OCR 行文本或图片路径。

P0 即时页列执行进度公开账本：`data/working/issue19-p0-immediate-page-execution-progress-public-ledger.csv` 把同一批 148 个页列执行包接到私有字段确认工作台，只公开完成计数、状态分布、任务集合哈希和非最终门禁。当前全部 148 个页列包仍为 R0，319 条 PDF 原页记录、319 条湖北官方侧记录、75 条高校辅证记录、290 条双人复核均未完成；三方一致性可评估数、字段写回复查数、推荐依据数和最终可用数全部为 0。它的作用是防止把“已经排队”误读成“已经核准”。

注意：`build_issue19_*` 生成的是 OCR 初稿、招生明细、质量审计、复核队列、统一逐专业底座入口和闭环执行批次，`机器初判`、质量分层、逐专业 P0/P1 优先级、逐专业核验批次、优先整组逐专业核验包、全量逐专业证据执行工作台、证据闭环任务队列、P0 证据执行包、P0 逐专业复核工作清单、统一逐专业底座发布表、底座闭环批次、字段缺口候选修复表、字段事实闭环总账、B0/B1 官网证据旁挂表、专业行原页证据锚点表、逐专业闭环缺口看板、逐专业三年投档线索旁挂表、单一逐专业招生明细总工作台、逐专业结构保真登记表、候选筛选准备表、决策闸门表、教育部学校属性逐专业核验表、湖北官方查询键碰撞清单、底座稳定性总看板、逐专业稳定化任务表、原始专业行血缘审计表、原始专业行源证据审计表、逐专业源证据风险侧账、教育部未匹配校名逐专业解析表、版面连续性风险清单、专业代号顺序风险清单、页级保真复核队列、候选 V3 批次、候选 V3 全量逐专业复核队列、B0/B1 核验包、官方交叉校验表、逐专业证据合并表、字段保真总账、P0 即时字段确认公开账本、P0 即时 PDF 原页读数候选公开审计和 P0 即时页列核页执行队列只用于安排复核与补证，不是最终报考建议。新增城市、学校或专业方向时，默认先查 `data/working/issue19-p0-immediate-page-execution-queue.csv`、`data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv`、`data/working/issue19-p0-immediate-page-review-packets.csv`、`data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv`、`data/working/issue19-p0-immediate-crop-ocr-public-audit.csv`、`data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv`、`data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv`、`data/working/issue19-field-fact-p0-immediate-review-packet.csv`、`data/working/issue19-field-fact-p0-triage-execution-workbench.csv`、`data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv`、`data/working/issue19-field-fact-closure-ledger.csv`、`data/working/issue19-raw-major-source-evidence-audit.csv`、`data/working/issue19-raw-major-lineage-consistency-audit.csv`、`data/working/issue19-major-source-evidence-risk-sidecar.csv`、`data/working/issue19-foundation-stability-dashboard.csv`、`data/working/issue19-foundation-stabilization-major-detail-tasks.csv`、`data/working/issue19-candidate-filter-prep-major-detail.csv`、`data/working/issue19-moe-school-attribute-major-detail.csv` 和 `data/working/issue19-admission-detail-master-workbench.csv`；这些表都保持一行一个招生专业明细、一行一个字段任务或一行一个页列核页执行包。原始专业行血缘审计表确认 13736 条 OCR 专业行全部按 `专业明细源行号=原始CSV数据行号+1` 回连到质量工作台、统一底座、总工作台、结构保真、稳定性看板、PDF 原页锚点、三年投档旁挂和闭环缺口看板，核心字段漂移为 0；源证据审计表进一步确认 13736 条专业明细全部按 `来源页码+版面列+专业起始行号` 精确回连到私有 OCR 起始行、公开页级 manifest、私有窗口 JSONL 和公开原页锚点，起始行哈希、窗口哈希、页级 manifest 均满匹配。它们只能证明“原始数据准确结构化且可追溯”，不能证明字段已是官方最终事实。底座稳定性总看板把每条专业明细分成 B0=2663、B1=4370、B2=5962、B3=542、B4=199，只说明先核什么，不生成填报建议或录取概率；逐专业稳定化任务表进一步把 B0/B1/B2 的 12995 条明细拆成可执行核验任务，仍全部 `最终可用=false`、`可进入下一阶段=false`、`是否允许作为志愿推荐依据=false`。教育部学校属性表只能证明学校登记名单线索：精确命中 13161 条、父校/校区类保守命中 190 条、未匹配待核 385 条；民办线索 2230 条、合作办学线索 34 条、职业本科名称线索 241 条都必须继续阻断或单独讨论。候选是否能进入讨论看 `data/working/issue19-major-decision-readiness-gates.csv` 的阻断闸门；教育部未匹配校名逐专业解析看 `data/working/issue19-moe-unmatched-school-resolution-major-detail.csv`，385 行全部 `机器能否自动替换校名=false`。官方系统回填消歧看 `data/working/issue19-hubei-official-query-key-collision-ledger.csv`。结构风险看 `data/working/issue19-admission-detail-structural-fidelity-register.csv`、`data/working/issue19-structural-risk-major-line-ledger.csv`、`data/working/issue19-major-line-layout-continuity-risk-ledger.csv` 和 `data/working/issue19-major-code-order-risk-ledger.csv`，0 明细专业组看 `data/working/issue19-zero-detail-group-placeholder-workbench.csv`。要安排实际核验顺序时，继续看 `data/working/issue19-foundation-closure-gap-scorecard.csv` 的 S0-S8 动作桶；三年投档只看 `data/working/issue19-major-line-historical-toudang-sidecar.csv` 的同代码线索，不得直接当录取概率。官方公开入口状态看 `data/working/issue19-official-public-entry-status.json`：2026-06-28 计划页仍含“持续更新中/敬请期待”，平台首页可访问但无登录探针仍是 401。底层闭环批次仍是 `data/working/issue19-foundation-closure-major-batches.csv`，C0=5310、C1=7608、C2 主批次=0、C3=609、C4=209，全部仍 `最终可用=false`。C2 主批次为 0 不代表没有官网任务，含官网辅证任务 854 条、B0B1 官网差异任务 854 条已按动作维度单独统计；字段缺口候选修复表有 7621 条非空候选线索，字段事实闭环总账把再选科目、专业计划数和学费拆成 K0/K1/K2 待核状态，B0/B1 官网证据旁挂表有 66 条强辅证、55 条计划数补缺候选和 19 条冲突核页，专业行原页证据锚点覆盖 13736 条明细，但全部不得自动写回最终表。页级索引 231 行、学校索引 1100 行，只作核页顺序和补源入口，不能替代逐专业主表。
