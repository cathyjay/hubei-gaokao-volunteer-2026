# 第 19 期全量招生计划 OCR 底座初稿

最后更新：2026-06-27

## 一、数据范围

本底座对应湖北省 2026 本科普通批首选物理在鄂招生计划，来源为《湖北招生考试》2026 年第 19 期。

注意：这里的“湖北招生计划”不是只看湖北省内高校，而是所有在湖北投放本科普通批首选物理计划的省内外院校。

## 二、当前产物

全量招生明细和复核队列已经输出到公开工作数据目录：

| 文件 | 粒度 | 用途 |
| --- | --- | --- |
| `data/working/issue19-full-admission-plan-school-ocr-draft.csv` | 院校 | 看每所院校识别到多少专业组、多少专业行 |
| `data/working/issue19-full-admission-plan-group-ocr-draft.csv` | 院校专业组 | 看专业组代码、页码、组内专业行数、风险标签 |
| `data/working/issue19-full-admission-plan-major-ocr-draft.csv` | 专业行 | 看专业代号、专业名称及备注 OCR、计划数候选、学费候选、选科候选 |
| `data/working/issue19-full-admission-plan-candidate-coverage.csv` | 候选池命中 | 看第一版 20 条历史候选在第 19 期全量 OCR 初稿中是否命中 |
| `data/working/issue19-full-admission-plan-ocr-draft-summary.json` | 摘要 | 看总量、质量状态、字段覆盖、风险标签统计 |
| `data/working/issue19-candidate-plan-review-summary.csv` | 候选院校专业组 | 看 20 条历史候选的 2026 OCR 命中、组内专业数、费用/医学等风险和复核优先级 |
| `data/working/issue19-candidate-plan-review-major-detail.csv` | 候选组内专业明细 | 展开 20 条历史候选已命中专业组的全部 OCR 专业行 |
| `data/working/issue19-candidate-plan-review-summary.json` | 候选工作台摘要 | 看候选数、命中数、机器初判分布和输出文件 |
| `data/working/issue19-priority-review-queue.csv` | 候选复核队列 | 按待定位、默认排除、高风险、可复核等机器初判排序 |
| `data/working/issue19-preference-major-search.csv` | 全量优先专业检索 | 搜索全量 OCR 中命中的数字媒体技术、计算机相关、师范相关专业行 |
| `data/working/issue19-hard-risk-group-review-queue.csv` | 全量硬风险专业组 | 集中查看医学/护理、高收费、中外合作、体检限制、语种单科、专项预科等风险组 |
| `data/working/issue19-priority-review-queues-summary.json` | 优先/风险队列摘要 | 看偏好专业命中量、风险等级分布和硬风险专业组数量 |
| `data/working/issue19-candidate-review-page-packet.csv` | 页面复核包页码 | 看候选池需要回看的 10 个 PDF 页码、页图哈希、页面 OCR 文本哈希和本页专业组 |
| `data/working/issue19-candidate-review-group-page-map.csv` | 候选组页码映射 | 看 20 条历史候选对应第 19 期页码、同校 OCR 专业组和同校页码 |
| `data/working/issue19-candidate-review-page-packet-summary.json` | 页面复核包摘要 | 看页面复核包范围、页码清单和输入文件 SHA |
| `data/working/issue19-candidate-page-code-audit.csv` | 候选组号审计 | 看 20 条历史候选在页面 OCR 和全量结构化表中的命中是否一致 |
| `data/working/issue19-ocr-structure-anomaly-queue.csv` | 专业明细结构异常 | 看全量专业行中疑似串校、串组、页眉串入、代号异常、数字字段错位、低置信度的复核队列 |
| `data/working/issue19-integrity-audit-summary.json` | 完整性审计摘要 | 看候选页码组号审计和结构异常队列的类型分布 |
| `data/working/issue19-candidate-v2-group-review-seed.csv` | 候选 V2 专业组种子 | 在 20 条历史候选基础上补入页图重切组、同页相邻风险组和同校偏好专业补充组 |
| `data/working/issue19-candidate-v2-major-review-seed.csv` | 候选 V2 逐专业明细种子 | 直接列出候选 V2 每个院校专业组下的招生专业明细，用于后续判断调剂是否可接受 |
| `data/working/issue19-candidate-v2-review-seed-summary.json` | 候选 V2 摘要 | 看候选 V2 的行数、证据来源、重点发现和待复核状态 |
| `data/working/issue19-candidate-v2-verification-group-workbench.csv` | 候选 V2 组级升级工作台 | 看每个候选专业组距离“可讨论/可排序”还缺哪些原页、官方系统、章程、家庭接受度和调剂证据 |
| `data/working/issue19-candidate-v2-verification-major-workbench.csv` | 候选 V2 专业明细升级工作台 | 给每个专业记录机器接受度初判、阻断原因、字段核验状态和升级缺口 |
| `data/working/issue19-candidate-v2-verification-workbench-summary.json` | 候选 V2 升级摘要 | 看升级闸门状态、0 明细组、专业接受度分布和待补证据 |
| `data/working/issue19-full-quality-group-tiers.csv` | 全量专业组质量索引 | 给 3329 条专业组行标记 OCR 质量层级、P0/P1/P3 复核优先级、重复组码和字段异常 |
| `data/working/issue19-full-quality-review-queue.csv` | 全量质量复核队列 | 按优先级列出需要优先回看原页的 3300 条专业组行 |
| `data/working/issue19-full-quality-tier-summary.json` | 全量质量摘要 | 看质量层级分布、P0 队列规模、无专业明细组和重复规范化组码 |
| `data/working/issue19-full-major-detail-quality-workbench.csv` | 全量逐专业明细质量工作台 | 一行一个专业，带 `专业行ID`、`专业组出现ID`、组级质量、专业行异常、偏好/风险和字段完整性 |
| `data/working/issue19-full-major-detail-review-queue.csv` | 全量逐专业明细复核队列 | 按逐专业 P0/P1/P3 排序，后续候选讨论必须从这里展开完整专业明细 |
| `data/working/issue19-full-major-detail-quality-summary.json` | 逐专业质量摘要 | 看 13736 条专业行的 ID 唯一性、异常闭环、候选/样本命中和字段缺失统计 |
| `data/working/issue19-full-major-field-fidelity-ledger.csv` | 全量逐专业字段保真总账 | 覆盖 13736 条招生专业行，是新增城市、学校或专业方向时的全量底座入口 |
| `data/working/issue19-full-major-field-fidelity-ledger-summary.json` | 全量保真总账摘要 | 看高风险保真行、暂未触发机器高风险行、主键唯一性和风险计数 |
| `data/working/issue19-full-major-verification-batches.csv` | 全量逐专业核验批次表 | 覆盖 13736 条招生专业行；一行一个专业，把全量保真总账和页级队列合成 A0-A9 人工核验批次 |
| `data/working/issue19-full-major-verification-batches-summary.json` | 全量核验批次摘要 | 看 A0-A9 分布、231 页覆盖、候选/样本/偏好命中和非最终门禁 |
| `data/working/issue19-priority-group-major-review-pack.csv` | 优先整组逐专业核验包 | 覆盖 1043 个优先专业组内的 7537 条招生专业明细；一行一个专业，同时携带整组入选原因、调剂机器风险和组内完整专业数 |
| `data/working/issue19-priority-group-major-review-pack-summary.json` | 优先整组逐专业核验包摘要 | 看 W0-W3 优先级、A0-A9 分布、T1/T2/T3 调剂风险和全部非最终门禁 |
| `data/working/issue19-priority-major-evidence-workbench.csv` | 优先逐专业证据执行工作台 | 覆盖同一批 7537 条招生专业明细；一行一个专业，带全量核验状态、家庭底线、页级风险、B0/B1 官网辅证、D0 原页证据和三年投档线索 |
| `data/working/issue19-priority-major-evidence-workbench-summary.json` | 优先逐专业证据执行摘要 | 看 E0-E6 执行优先级、辅证命中、字段缺口、历史线索和非最终门禁 |
| `data/working/issue19-full-major-evidence-workbench.csv` | 全量逐专业证据执行工作台 | 覆盖第 19 期全部 13736 条招生专业明细；把优先包和非优先包统一为一行一个专业的证据执行视图 |
| `data/working/issue19-full-major-evidence-workbench-summary.json` | 全量逐专业证据执行摘要 | 看 E0-E6 与 F0-F4 优先级、7537 条优先包明细、6199 条非优先包明细、辅证命中、字段缺口和非最终门禁 |
| `data/working/issue19-full-major-evidence-closure-tasks.csv` | 全量逐专业证据闭环任务队列 | 覆盖 13736 条招生专业明细并拆成 94935 条证据任务；一行一个专业行和一个证据项 |
| `data/working/issue19-full-major-evidence-closure-tasks-summary.json` | 证据闭环任务摘要 | 看 PDF、湖北官方系统、高校官网/章程、家庭接受度、调剂、三年投档、字段补证和 B0/B1 差异任务分布 |
| `data/working/issue19-p0-evidence-execution-packets.csv` | P0 证据执行包 | 从闭环任务中抽取 6619 条 P0 任务；按页、学校、专业组和任务类型组织核验 |
| `data/working/issue19-p0-evidence-review-worklist.csv` | P0 逐专业复核工作清单 | 一行一个招生专业明细和一个 P0 证据项，带页图/OCR 哈希、全量证据字段和人工核验闸口 |
| `data/working/issue19-p1-field-gap-evidence-repair-matrix.csv` | 字段缺口逐专业修复矩阵 | 一行一个招生专业明细和一个字段缺口，拆分再选科目、专业计划数、学费缺口 |
| `data/working/issue19-field-gap-repair-candidates.csv` | 字段缺口候选修复线索 | 19065 个字段缺口候选任务；给出同组 OCR、当前 OCR 单元格或官网辅证候选值，但全部不可自动写回主表 |
| `data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv` | 湖北官方系统逐专业核验包 | 一行一个招生专业明细和一个湖北官方系统/省招办计划核验任务 |
| `data/working/issue19-b0-b1-public-official-diff-ledger.csv` | B0/B1 逐专业官网差异账 | 一行一个已有高校官网/章程辅证线索的招生专业明细，记录匹配、冲突和仍需核验项 |
| `data/working/issue19-b0-b1-official-evidence-by-major-line.csv` | B0/B1 官网证据逐专业旁挂表 | 覆盖 854 条已有官网线索的专业明细；按 `专业行ID` 标注强辅证、补缺候选、冲突核页、未匹配和待补源 |
| `data/working/issue19-b0-b1-official-plan-fill-candidates.csv` | B0/B1 官网计划数补缺候选 | 55 条 OCR 计划数缺失但官网有计划数的候选；不能替代湖北官方系统 |
| `data/working/issue19-b0-b1-official-conflict-review.csv` | B0/B1 官网计划数冲突核页表 | 18 条计划数冲突，优先核 PDF 原页计划数列、学费列和湖北官方系统 |
| `data/working/issue19-major-line-pdf-evidence-anchors.csv` | 专业行原页证据锚点表 | 覆盖全部 13736 条专业明细；公开表保存行号范围、坐标摘要和哈希，私有 JSONL 保存 OCR 窗口原文 |
| `data/working/issue19-major-detail-foundation-release.csv` | 统一逐专业底座入口 | 覆盖全部 13736 条招生专业明细；一行一个专业，聚合 P0/P1、湖北官方待核、官网差异、页级证据、家庭底线、调剂风险和三年投档线索；只用于检索、复核、补证和筛选预处理 |
| `data/working/issue19-major-line-historical-toudang-sidecar.csv` | 逐专业三年投档线索旁挂表 | 覆盖全部 13736 条专业明细；按同院校专业组代码挂接 2023/2024/2025 投档线和等位分差，仅作冲稳保前置线索 |
| `data/working/issue19-admission-detail-master-workbench.csv` | 单一逐专业招生明细总工作台 | 覆盖全部 13736 条招生专业明细；一行一个专业，把统一底座、闭环缺口看板、PDF 原页锚点和三年投档线索合并到同一行，后续讨论默认从这里开始 |
| `data/working/issue19-admission-detail-structural-fidelity-register.csv` | 逐专业结构保真登记表 | 覆盖全部 13736 条专业明细；显式标记专业组归属方式、回退归属、重复组码、重复专业代号、结构异常和原页锚点状态 |
| `data/working/issue19-structural-risk-major-line-ledger.csv` | 逐专业结构风险事件派单表 | 3108 条风险事件；把回退归属、重复专业代号、重复组码、原页窗口 P0/P1 拆成可派单核验项 |
| `data/working/issue19-zero-detail-group-placeholder-workbench.csv` | 0 明细专业组占位表 | 40 个专业组占位；只用于补齐真实招生专业明细，不作为招生专业行 |
| `data/working/issue19-candidate-filter-prep-major-detail.csv` | 逐专业候选筛选准备表 | 覆盖全部 13736 条专业明细；合并家庭偏好、城市关键词候选、学费数字线索、结构保真和调剂上下文，所有待官方/章程/人工确认字段保持 pending |
| `data/working/issue19-major-decision-readiness-gates.csv` | 逐专业决策闸门表 | 覆盖全部 13736 条专业明细；显式记录 PDF 原页、湖北官方系统、办学属性、城市/校区、家庭接受度、同组调剂和字段缺口阻断闸门 |
| `data/working/issue19-moe-school-attribute-major-detail.csv` | 教育部学校属性逐专业核验表 | 覆盖全部 13736 条专业明细；把教育部学校名称、标识码、主管部门、所在地、层次、备注、民办/合作办学/职业本科线索下沉到每条专业行 |
| `data/working/issue19-moe-school-attribute-unmatched-schools.csv` | 教育部未匹配学校支持清单 | 49 个院校代码+校名待核，只用于核 OCR 校名、特殊院校和职业本科风险，不替代逐专业主表 |
| `data/working/issue19-hubei-official-query-key-collision-ledger.csv` | 湖北官方查询键碰撞清单 | 118 条碰撞专业明细；防止后续按非唯一的院校代码+专业组代码+专业代号回填官方系统结果 |
| `data/working/issue19-foundation-stabilization-major-detail-tasks.csv` | 逐专业稳定化任务表 | 从 B0/B1/B2 抽取 12995 条招生专业明细；一行一个专业，保留第一核验动作、保真证据链、双重佐证字段和阻断原因 |
| `data/working/issue19-foundation-stabilization-major-detail-tasks-summary.json` | 逐专业稳定化任务摘要 | 看 B0/B1/B2 任务分布、字段候选、官网差异、结构风险、官方查询键碰撞和未匹配校名解析计数 |
| `data/working/issue19-official-public-entry-status.json` | 官方公开入口状态快照 | 记录 2026-06-27 湖北教育考试网公开入口 SHA 和平台无登录 401 探针；说明当前公开入口尚不能替代逐专业核验 |
| `data/working/issue19-raw-major-lineage-consistency-audit.csv` | 原始专业行血缘审计表 | 覆盖全部 13736 条 OCR 专业行；逐行核对原始 CSV、质量工作台、统一底座、总工作台、结构保真、稳定性看板、PDF 原页锚点、三年投档旁挂和闭环缺口看板是否一一回连且核心字段无漂移 |
| `data/working/issue19-raw-major-lineage-consistency-audit-summary.json` | 原始专业行血缘审计摘要 | 看全链路回连计数、核心字段漂移计数、稳定性等级分布、字段候选/结构风险/官方查询键碰撞聚合和全部不可推荐门禁 |
| `data/working/issue19-raw-major-source-evidence-audit.csv` | 原始专业行源证据审计表 | 覆盖全部 13736 条招生专业明细；按 `来源页码+版面列+专业起始行号` 回连私有 OCR 起始行，并与页级 manifest、公开原页锚点、私有窗口 JSONL 和原始血缘审计表闭合 |
| `data/working/issue19-raw-major-source-evidence-audit-summary.json` | 原始专业行源证据审计摘要 | 看源头 OCR 行、页级 manifest、窗口哈希、QC 计数、锚点状态和不可推荐门禁 |
| `data/working/issue19-major-source-evidence-risk-sidecar.csv` | 逐专业源证据风险侧账 | 覆盖全部 13736 条招生专业明细；把源证据风险、底座稳定性、闭环缺口和 P0 复核任务合并到同一条 `专业行ID` |
| `data/working/issue19-major-source-evidence-risk-sidecar-summary.json` | 逐专业源证据风险侧账摘要 | 看 X1/X2/X3/X4 源证据下沉分层、优先核页数量、P0 工作清单覆盖和不可推荐门禁 |
| `data/working/issue19-field-fact-closure-ledger.csv` | 字段事实闭环总账 | 覆盖全部 13736 条招生专业明细；把再选科目、专业计划数、学费三项关键字段的 OCR 候选、字段缺口候选、PDF 原页待核、湖北官方待核和下一步补证入口合到同一条 `专业行ID` |
| `data/working/issue19-field-fact-closure-ledger-summary.json` | 字段事实闭环摘要 | 看 L0-L4 字段闭环等级、Q0-Q2 阻断等级、K0/K1/K2 三字段状态、字段候选任务 19065 条和非空候选 7621 条 |
| `data/working/issue19-field-fact-verification-tasks.csv` | 字段事实核验任务队列 | 覆盖 41208 条逐字段任务；每条招生专业明细拆成再选科目、专业计划数、学费三项任务，回连字段总账和页级保真队列 |
| `data/working/issue19-field-fact-verification-tasks-summary.json` | 字段事实核验任务摘要 | 看 K0 无候选原页重读 11444 条、K1 有候选待核 7621 条、K2 OCR 候选待三方闭环 22143 条；全部仍非最终 |
| `data/working/issue19-field-fact-p0-reread-worklist.csv` | P0 字段原页重读工作清单 | 覆盖 11444 条 K0 无候选字段任务；一行一个 `专业行ID × 字段名`，回连字段任务、原始源证据审计、PDF 锚点和页级保真队列 |
| `data/working/issue19-field-fact-p0-reread-worklist-summary.json` | P0 字段原页重读摘要 | 看专业计划数、再选科目、学费三类 K0 字段的原页重读规模、覆盖页码、学校数和四路证据命中 |
| `data/working/issue19-major-line-layout-continuity-risk-ledger.csv` | 专业行版面连续性风险清单 | 1934 条风险事件；只用公开原页锚点字段检查行号和坐标连续性 |
| `data/working/issue19-major-code-order-risk-ledger.csv` | 专业代号顺序风险清单 | 355 条风险事件；检查专业代号无法解析、相邻不递增和大跳变 |
| `data/working/issue19-major-detail-foundation-release-summary.json` | 统一逐专业底座摘要 | 看 G0-G4 底座保真门禁、字段缺口、P0 专业明细、湖北官方待核、B0/B1 差异和全部非最终边界 |
| `data/working/issue19-foundation-closure-major-batches.csv` | 底座闭环逐专业执行批次 | 覆盖全部 13736 条招生专业明细；一行一个专业，把统一底座入口转成 C0-C4 执行批次和首要核验动作 |
| `data/working/issue19-foundation-closure-gap-scorecard.csv` | 逐专业闭环缺口看板 | 覆盖全部 13736 条专业明细；把 C0-C4、字段候选、官网旁证、原页锚点、家庭/调剂/官方门禁合并成核验顺序入口 |
| `data/working/issue19-foundation-closure-page-index.csv` | 底座闭环页级执行索引 | 覆盖 231 个招生计划 PDF 明细页；只用于安排核页顺序，不能替代逐专业明细 |
| `data/working/issue19-foundation-closure-school-index.csv` | 底座闭环学校执行索引 | 覆盖 1100 所院校；只用于安排补源和学校级核验顺序，不能替代逐专业明细 |
| `data/working/issue19-foundation-audit-summary.json` | 底座审计摘要 | 看机器阻断项是否通过、人工复核风险、页码覆盖、回退归属和重复专业代号 |
| `data/working/issue19-foundation-audit-findings.csv` | 底座审计发现 | 区分机器阻断检查和人工复核风险，避免把 OCR 风险误当最终事实 |
| `data/working/issue19-foundation-page-audit.csv` | 按页审计表 | 覆盖第 10-240 页，记录每页专业组、专业明细、结构异常、候选命中和复核优先级 |
| `data/working/issue19-candidate-v2-field-review-ledger.csv` | 候选 V2 字段复核总账 | 把 23 个候选/补充专业组和 82 条专业明细拆成 840 个字段核验任务 |
| `data/working/issue19-candidate-v2-triangulation-matrix.csv` | 候选 V2 证据矩阵 | 一行一个候选专业组，记录 PDF、官方系统、高校章程、家庭接受度、调剂和历史线证据状态 |
| `data/working/issue19-candidate-v2-evidence-ledger-summary.json` | 候选 V2 证据总账摘要 | 看字段任务数、P0/P1/P2/P3 分布、专业行 ID 匹配和升级边界 |
| `data/working/issue19-page-manifest.csv` | 公开页级 manifest | 覆盖 PDF 1-240 页，记录每页页图/OCR 文本哈希、OCR 统计、结构化明细和候选任务数 |
| `data/working/issue19-page-manifest-summary.json` | 页级 manifest 摘要 | 看 240 页渲染/OCR 完整性、10-240 页结构化覆盖和候选字段任务页码归属 |
| `data/working/issue19-page-fidelity-review-queue.csv` | 按页保真复核队列 | 覆盖 PDF 第 10-240 页 231 个招生计划明细页；逐页汇总 13736 条专业明细和 3329 个专业组的风险计数，只用于排核页顺序 |
| `data/working/issue19-page-fidelity-review-queue-summary.json` | 按页保真摘要 | 看页码连续性、F0/F1/F2/F3、P0-P6、证据哈希和非最终门禁 |
| `data/working/issue19-family-fit-group-screen.csv` | 家庭底线专业组筛选表 | 覆盖 3329 个院校专业组；每行展开完整组内招生明细，并给出医学护理、超预算、偏好方向和调剂初判 |
| `data/working/issue19-family-fit-major-detail.csv` | 家庭底线逐专业筛选表 | 覆盖 13736 条专业明细；一行一个专业，记录机器接受度初判、阻断或待核原因和家庭接受度待确认状态 |
| `data/working/issue19-family-fit-screen-summary.json` | 家庭底线筛选摘要 | 看机器家庭匹配、调剂初判和下一轮复核优先级分布 |
| `data/working/issue19-candidate-v3-review-intake.csv` | 候选 V3 复核入口 | 覆盖 1327 个候选专业组；每行都展开完整组内招生明细、页码证据、历史同组投档线线索和升级缺口 |
| `data/working/issue19-candidate-v3-review-intake-summary.json` | 候选 V3 摘要 | 看批次分布、专业明细来源、历史线命中分布和最终可用边界 |
| `data/working/issue19-candidate-v3-b0-b1-group-review-pack.csv` | B0/B1 组级核验包 | 覆盖 49 个优先专业组；逐组列出核页重点、页码证据、历史线口径和升级闸门 |
| `data/working/issue19-candidate-v3-b0-b1-major-review-pack.csv` | B0/B1 逐专业核验包 | 覆盖 324 个逐专业任务；用于回填 PDF、官方系统、章程、家庭接受度和调剂结论 |
| `data/working/issue19-candidate-v3-b0-b1-review-pack-summary.json` | B0/B1 核验包摘要 | 看 B0/B1 组数、逐专业任务数、0 明细占位任务和页码覆盖 |
| `data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv` | B0/B1 学校官方来源队列 | 覆盖 36 所学校；记录官网来源状态、补源优先级、检索式和逐专业任务数 |
| `data/working/issue19-candidate-v3-b0-b1-admission-detail-official-crosscheck.csv` | B0/B1 逐专业招生明细主表 | 覆盖 324 个逐专业任务；把组级投档、调剂、历史线和补源字段下沉到每条专业行 |
| `data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv` | B0/B1 逐专业招生明细证据合并表 | 覆盖 324 个逐专业任务；后续候选讨论默认使用这张表，一行一个招生专业或 0 明细占位，同时带出官网证据匹配和保真状态 |
| `data/working/issue19-candidate-v3-b0-b1-official-crosscheck-queue.csv` | B0/B1 组级官方交叉校验索引 | 覆盖 49 个优先专业组；逐组记录 PDF、湖北官方系统、高校官网/章程、家庭接受度和调剂结论待核状态，只作索引 |
| `data/working/issue19-candidate-v3-b0-b1-major-official-crosscheck-queue.csv` | B0/B1 原逐专业官方交叉校验队列 | 覆盖 324 个逐专业任务；一行一个专业或 0 明细占位任务，逐专业保留计划数、学费、风险和字段待核状态 |
| `data/working/issue19-candidate-v3-b0-b1-official-crosscheck-summary.json` | B0/B1 官方交叉校验摘要 | 看 36 校、49 组、324 个逐专业任务、官网来源状态分布和最终可用边界 |
| `data/working/issue19-candidate-v3-b0-b1-official-evidence-match.csv` | B0/B1 逐专业官网证据匹配表 | 覆盖 324 条招生明细；一行一个专业，记录官网/API/HTML/XLSX/PDF/计划图抽取匹配状态、官网计划数和仍需核验项 |
| `data/working/issue19-b0-b1-retained-official-plan-normalized.csv` | B0/B1 留存官网证据标准化表 | 覆盖 434 条官网/API/HTML/XLSX/PDF/计划图/双表联合抽取证据；只作交叉校验来源，不是最终事实表 |
| `data/working/issue19-b0-b1-plan-conflict-review-queue.csv` | B0/B1 计划数冲突复核队列 | 覆盖 18 条计划数冲突；带保真诊断和计划数候选引用方式，用于优先核 PDF 原页计划数列、学费列和湖北官方系统 |
| `data/working/issue19-b0-b1-unmatched-major-review-queue.csv` | B0/B1 官网未匹配专业复核队列 | 覆盖 32 条官网证据未匹配专业；区分 OCR 噪声、串校串行、普通未匹配和关键限定词未覆盖问题 |
| `data/working/issue19-b0-b1-official-source-gap-priority.csv` | B0/B1 学校补源缺口优先表 | 覆盖 19 所学校；区分 P0 待补官方计划源和 P1 已有线索待结构化 |

当前自动识别结果：

| 指标 | 数量 |
| --- | ---: |
| OCR 院校数 | 1103 |
| OCR 院校专业组数 | 3329 |
| OCR 专业行数 | 13736 |
| 无专业行专业组数 | 40 |
| 第一版候选池命中 | 17/20 |
| 候选池已命中专业明细 | 77 |
| 全量优先专业关键词命中 | 2499 |
| 全量硬风险专业组 | 2962 |
| 优先专业所在专业组带风险 | 2139 |
| 候选池页面复核包页数 | 10 |
| 候选组号审计行数 | 20 |
| 全量专业明细结构异常行数 | 5129 |
| 候选 V2 专业组种子 | 23 |
| 候选 V2 逐专业明细种子 | 82 |
| 候选 V2 升级工作台专业组 | 23 |
| 候选 V2 升级工作台专业明细 | 82 |
| 候选 V2 字段复核任务 | 840 |
| 候选 V2 字段 P0 任务 | 494 |
| 候选 V2 证据矩阵 | 23 |
| 候选 V2 精确匹配全量专业行 | 75 |
| 候选 V2 页图补种/重切专业行 | 7 |
| 全量质量分层专业组行 | 3329 |
| 全量质量复核队列 | 3300 |
| P0 必须优先核页 | 3295 |
| 无专业明细专业组 | 40 |
| 重复规范化专业组代码 | 3 个代码、6 行 |
| 逐专业质量工作台专业行 | 13736 |
| 逐专业复核队列 | 13705 |
| 逐专业 P0 必须核页 | 13700 |
| 家庭底线筛选专业组 | 3329 |
| 家庭底线筛选专业明细 | 13736 |
| 有偏好专业且未自动阻断专业组 | 590 |
| 默认不进主方案专业组 | 1467 |
| 可进入人工调剂接受度判断专业组 | 801 |
| 候选 V3 复核入口专业组 | 1327 |
| 候选 V3：B0 历史候选和组号问题优先核页 | 20 |
| 候选 V3：B1 数字媒体技术优先核页 | 29 |
| 候选 V3：B2 偏好专业未自动阻断核页 | 763 |
| 候选 V3：B3 偏好专业硬风险先核风险 | 514 |
| 候选 V3：B4 同页边界风险组核页 | 1 |
| 候选 V3 使用候选 V2 明细 | 23 |
| 候选 V3 使用家庭筛选 OCR 明细 | 1304 |
| 候选 V3 同组历史投档线三年命中 | 468 |
| 候选 V3 B0/B1 核验包专业组 | 49 |
| 候选 V3 B0/B1 逐专业核验任务 | 324 |
| 候选 V3 B0/B1 覆盖 PDF 页 | 32 |
| 候选 V3 B0/B1 0 明细占位任务 | 2 |
| B0/B1 逐专业来源：候选 V2 种子 | 81 |
| B0/B1 逐专业来源：家庭底线逐专业表 | 241 |
| B0/B1 官方交叉校验学校 | 36 |
| B0/B1 官方交叉校验专业组 | 49 |
| B0/B1 逐专业招生明细主表 | 324 |
| B0/B1 官方交叉校验逐专业任务 | 324 |
| B0/B1 逐专业真实专业行 | 322 |
| B0/B1 逐专业 0 明细占位任务 | 2 |
| B0/B1 可复用高校官网湖北计划源学校 | 7 |
| B0/B1 部分官网线索待跟进学校 | 16 |
| B0/B1 待补高校官网计划源学校 | 8 |
| B0/B1 仅章程/规则或不可用计划线索学校 | 5 |
| B0/B1 留存官网/API/HTML/XLSX/PDF/计划图/双表联合抽取证据标准化行 | 434 |
| B0/B1 逐专业官网证据专业名匹配 | 152 |
| B0/B1 逐专业计划数与 OCR 一致 | 61 |
| B0/B1 逐专业 OCR 缺失但官网可补计划数 | 55 |
| B0/B1 逐专业计划数存在差异 | 18 |
| B0/B1 计划数冲突复核队列 | 18 |
| B0/B1 官网未匹配专业复核队列 | 32 |
| B0/B1 学校补源缺口优先表 | 19 |
| B0/B1 P0 待补官方计划源学校 | 8 |
| B0/B1 官方交叉校验最终可用 | 0 |
| 专业行ID唯一数 | 13736 |
| 结构异常全量匹配 | 5129/5129 |
| 底座机器阻断项 | 0 |
| 底座人工复核风险项 | 8 |
| 页级审计覆盖 | 231 页，第 10-240 页 |
| 公开页级 manifest | 240 页，第 1-240 页 |
| 已渲染页图哈希 | 240 |
| 已 OCR 文本哈希 | 240 |
| 结构化招生计划页 | 231 |
| OCR 行数 | 65512 |
| OCR QC 问题数 | 37127 |
| 低平均置信度页 | 6 页：61、117、129、166、192、215 |
| 精确专业组归属专业行 | 11898 |
| 唯一组码回退归属专业行 | 1838 |
| 回退归属涉及专业组 | 334 |
| 候选池命中回退专业行 | 18 |
| 组内专业代号重复 | 31 个专业组、116 条专业行 |
| 候选池专业行命中 | 77 |
| 样本学校专业行命中 | 560 |
| 重复组码关联专业行 | 14 |
| 优先整组逐专业核验包专业明细 | 7537 |
| 优先整组逐专业核验包覆盖专业组 | 1043 |
| 优先整组逐专业核验包覆盖 PDF 页 | 230 |
| 优先逐专业证据执行工作台专业明细 | 7537 |
| 优先执行 E0 PDF 原页/组边界阻断 | 1362 |
| 优先执行 E1 历史候选/样本三方证据 | 450 |
| 优先执行 E2 数字媒体技术三方证据 | 405 |
| 全量逐专业证据执行工作台专业明细 | 13736 |
| 全量证据工作台内优先包专业明细 | 7537 |
| 全量证据工作台内非优先包专业明细 | 6199 |
| 非优先 F0 PDF 原页/结构阻断 | 2685 |
| 非优先 F2 计划学费选科字段补证 | 2920 |
| 全量证据闭环任务 | 94935 |
| 基础证据任务 | 82416 |
| 字段完整性补证任务 | 12473 |
| B0/B1 官网冲突或未匹配任务 | 46 |
| 字段缺口候选修复任务 | 19065 |
| 字段缺口非空候选线索 | 7621 |
| 字段缺口自动写回 | 0 |
| 字段候选来源：组级 OCR 上下文 | 6782 |
| 字段候选来源：OCR 单元格 | 817 |
| 字段候选来源：高校官网辅证 | 22 |
| 字段候选无候选 | 11444 |
| B0/B1 官网证据旁挂专业明细 | 854 |
| B0/B1 官网强辅证 | 61 |
| B0/B1 官网计划数补缺候选 | 55 |
| B0/B1 官网计划数冲突核页 | 18 |
| B0/B1 疑似 OCR 把学费读入计划数 | 13 |
| 专业行原页证据锚点 | 13736 |
| 已生成专业行级 OCR 锚点 | 12596 |
| 原页锚点缺少组标题上下文 | 1127 |
| 原页锚点需重点回看专业窗口 | 13 |
| 逐专业闭环缺口看板 | 13736 |
| 看板 S0：B0/B1 冲突+P0原页优先 | 18 |
| 看板 S1：P0原页+官网辅证同步核 | 116 |
| 看板 S2：P0原页结构和字段先核 | 5176 |
| 看板 S3：字段缺口有候选先核 | 4248 |
| 看板 S4：字段缺口无候选需原页重读 | 3360 |
| 逐专业三年投档线索旁挂 | 13736 |
| 单一逐专业招生明细总工作台 | 13736 |
| 逐专业结构保真登记 | 13736 |
| 原始专业行血缘审计 | 13736 |
| 血缘审计全链路核心字段漂移 | 0 |
| 血缘审计 A0 全链路回连且核心 OCR 字段一致 | 13736 |
| 原始专业行源证据审计 | 13736 |
| 源证据 S0 满回连专业明细 | 13736 |
| 源证据 R2/R3 需优先或阻断级核页 | 13118 |
| 源证据 R4 未触发起始行 QC 风险 | 618 |
| 源证据风险侧账逐专业明细 | 13736 |
| 源证据风险侧账优先核页明细 | 13118 |
| 结构风险事件派单 | 3108 |
| 唯一组码回退归属专业明细 | 1838 |
| 组内专业代号重复专业明细 | 116 |
| 0 明细专业组占位 | 40 |
| 逐专业候选筛选准备表 | 13736 |
| 逐专业决策闸门表 | 13736 |
| 教育部名单精确匹配专业明细 | 13161 |
| 教育部父校/校区类保守匹配专业明细 | 190 |
| 教育部名单未匹配待核专业明细 | 385 |
| 教育部名单未匹配院校代码+校名 | 49 |
| 教育部备注民办线索专业明细 | 2230 |
| 教育部备注合作办学线索专业明细 | 34 |
| 职业本科名称线索专业明细 | 241 |
| 湖北官方查询键碰撞清单 | 59 个键、118 行 |
| 底座稳定性总看板 | 13736 |
| B0 校名/结构/官方查询键强阻断 | 2663 |
| B1 P0 原页或官网冲突优先 | 4370 |
| B2 字段缺口补证优先 | 5962 |
| B3 三方官方闭环待核 | 542 |
| B4 低风险抽检但仍非最终 | 199 |
| 逐专业稳定化任务表 | 12995 |
| 稳定化任务 P0 强阻断 | 2663 |
| 稳定化任务 P0 原页或官网冲突 | 4370 |
| 稳定化任务 P1 字段缺口补证 | 5962 |
| 稳定化任务字段候选任务 | 19065 |
| 稳定化任务非空字段候选 | 7621 |
| 稳定化任务最终可用 | 0 |
| 教育部未匹配校名逐专业解析表 | 385 |
| 未匹配校名历史同代码候选 | 281 |
| 未匹配校名教育部相似候选 | 232 |
| 未匹配校名 OCR 规则候选 | 90 |
| 未匹配校名机器自动替换 | 0 |
| 版面连续性风险事件 | 1934 |
| 专业代号顺序风险事件 | 355 |
| 城市偏好关键词命中专业明细 | 1723 |
| 办学属性待核专业明细 | 13736 |
| 三年同代码命中 | 5836 |
| 两年同代码命中 | 3946 |
| 一年同代码命中 | 1940 |
| 三年同代码未命中或组号变化 | 2014 |
| 历史线再选要求跨年变化风险 | 5645 |
| 2026 同代码专业组重复出现专业明细 | 14 |
| 底座闭环逐专业明细执行主表 | 13736 |
| 底座闭环页级索引 | 231 |
| 底座闭环学校索引 | 1100 |
| C0-P0证据闭环先核 | 5310 |
| C1-字段缺口先补 | 7608 |
| C2-官网辅证主批次 | 0 |
| C3-常规三方证据闭环 | 609 |
| C4-低风险抽检但非最终 | 209 |
| 含官网辅证任务专业明细 | 854 |
| B0/B1 官网差异专业明细 | 854 |
| 有高校官网来源线索专业明细 | 854 |
| 底座闭环最终可用 | 0 |

质量分层口径：

| 层级或优先级 | 含义 |
| --- | --- |
| `Q0-无专业明细` | 专业组下没有识别出专业行，必须先回看原页补齐 |
| `Q1-高风险结构异常` | 出现串校、串组、数字字段错位等高严重度结构异常 |
| `Q2-重点候选字段待核` | 命中候选或偏好方向，同时存在字段或结构待核问题 |
| `Q3-字段待核` | 字段完整性或纯数字识别存在问题 |
| `Q4-结构相对完整待抽检` | 结构相对完整，但仍未完成原页核验 |
| `P0-必须优先核页` | 命中候选、偏好、硬风险、异常学费、缺关键字段、重复组码、行数不一致或结构高风险 |
| `P1-高优先核页` | 有字段待核，但暂未触发 P0 |
| `P3-相对完整但仍需核页` | 相对完整的抽检队列，仍不能直接用于填报 |

特别注意：`issue19-full-quality-group-tiers.csv` 是专业组复核索引，不是志愿建议表。后续讨论任何候选院校专业组时，必须从 `issue19-full-major-detail-quality-workbench.csv` 或候选 V2 逐专业明细中展开全部专业行；不能只给学校和专业组两层结论。

逐专业工作台保真口径：

| 字段或规则 | 用途 |
| --- | --- |
| `专业行ID` | 每条专业明细的稳定 ID，当前 13736 条全部唯一 |
| `专业组出现ID` | 专业组“出现行”的稳定 ID，防止 `F01403`、`F77804`、`F79104` 这类重复组码互相覆盖 |
| `组质量匹配方式` | 记录逐专业行如何匹配到组级质量索引 |
| `专业行异常规则ID列表` | 从结构异常队列逐行聚合，当前 5129 条异常全部匹配到专业行 |
| `专业偏好方向` / `专业风险类型` | 把关键词召回和风险标签下沉到专业行，便于后续判断每个组内专业是否能接受 |
| `逐专业复核优先级` | 只安排核页顺序，不表示该专业可报 |

当前全量优先专业关键词命中：

| 方向 | 专业行数 |
| --- | ---: |
| 数字媒体技术 | 78 |
| 计算机类相关 | 1867 |
| 师范类相关 | 601 |

优先专业队列的风险口径：

| 风险口径 | 含义 |
| --- | --- |
| 本专业OCR风险等级 | 只看这一条专业行自身的 OCR 风险标签 |
| 专业组风险类型 | 看所在院校专业组内全部专业合并后的风险标签 |
| 综合风险等级 | 合并本专业行风险和专业组风险，防止忽略调剂范围内的风险 |

未命中的第一版候选专业组：

- `C10702`
- `C10704`
- `K15123`

这三项不能直接视为不存在。下一步需要核对是否为 OCR 漏识别、2026 组号变化、历史组取消或候选池历史 OCR 噪声。

候选页码组号审计进一步区分了三类情况：

- `C10704`：页面 OCR 出现候选组号，但全量结构化专业组表未拆出，属于高优先级切组漏拆复核。
- `C10702`：候选页未见该组号，结构化也未命中，更可能是 2026 组号变化、历史组取消或历史候选旧组号。
- `K15123`：候选页 208/209 未见该组号，同校第 19 期 OCR 仅见 `K15107` 至 `K15118`，更可能是 2026 组号变化或历史候选旧组号。

候选 V2 逐专业明细种子进一步处理了“只看专业组还不够”的问题：

- `C10703`：全量 OCR 曾把 `C10704` 的 3 个专业吞入 `C10703`；V2 种子按页图重切为 7 个专业。
- `C10704`：页图和页面 OCR 可见，但全量结构化表漏拆；V2 种子先按页图补出 3 个专业，仍需人工逐字段复核。
- `C10705`：同页相邻风险组，含康复治疗学中外合作办学，学费候选 48000，用于边界和风险复核，不进入主方案。
- `K15123`：第 208/209 页未见，V2 中保留为 0 条明细的历史候选定位问题，不能沿用为 2026 可报组。
- `K15114`：同校补充关注组，含数字媒体技术、智能科学与技术、电子信息工程；只能作为 2026 新候选线索，不能继承 `K15123` 历史投档线。
- `K17905`：同校补充关注组，命中数字媒体技术，但仍带 OCR 页眉串入异常，必须回看原页。

特别注意：`最高学费候选` 只适用于学费字段 OCR 为清晰纯数字的情况。遇到 `10万`、`6`、`［50000` 这类非纯数字或疑似截断字段时，预算判断必须回看原页和学校章程，不能直接用数字候选值。

候选 V2 升级工作台把“是否能进冲稳保排序”拆成硬闸门：

- 当前 23 个专业组全部为 `候选闸门状态=pending_verification`，`可进入最终候选=false`。
- 当前 82 条专业明细全部为 `专业闸门状态=pending_verification`，`是否允许进入最终专业列表=false`。
- `C10702`、`K15123` 是 0 明细组，`零明细原因=group_not_found_or_code_changed`，不得进入排序。
- `K15114`、`K17905` 等同校补充组默认 `历史投档线可沿用=false`，必须重新找 2026 组证据和历史参照。
- `C10704` 虽然页图可见，但仍要求原页、湖北官方系统/省招办计划、高校章程、家庭接受度和调剂结论全部补齐后，才可能进入讨论。

## 三、当前可信度

当前状态统一为：

```text
full_ocr_draft_needs_manual_pdf_review
candidate_review_workbench_needs_manual_pdf_review
priority_review_queues_need_manual_pdf_review
candidate_v2_review_seed_needs_manual_pdf_review
candidate_v2_verification_workbench_pending_review
candidate_v2_evidence_ledgers_pending_manual_review
full_quality_tiers_need_manual_pdf_review
full_major_detail_quality_need_manual_pdf_review
issue19_foundation_machine_checks_passed_need_pdf_official_review
issue19_foundation_stabilization_major_detail_tasks_not_final
issue19_official_public_entry_status_not_final
```

所有明细行的 `最终可用` 均为：

```text
false
```

也就是说，本底座现在可以用于：

- 搜索学校、专业组和专业关键词。
- 查看全量湖北 2026 本科普通批首选物理在鄂招生专业明细 OCR 初稿。
- 批量发现数字媒体技术、计算机类、师范类等方向。
- 批量发现医学/护理、中外合作、高收费、体检限制、语种单科等风险。
- 对第一版候选池做 2026 专业组定位。
- 按 P0/P1/P3 队列安排原页人工复核。
- 逐专业展开候选专业组内全部招生明细。
- 生成下一步人工复核任务。

但现在不能用于：

- 直接填报志愿。
- 直接判断某个专业组一定可报。
- 直接判断某个专业组可以服从调剂。
- 直接生成最终冲稳保志愿表。
- 把 `机器初判` 当成报考建议。
- 把关键词命中当成精确专业分类。
- 把质量分层或 P0/P1/P3 当成可报结论。

当前底座数据“坐稳”的阶段性含义是：原始招生计划明细正在被准确结构化、逐专业回链和保真排队；它不代表目标院校、目标专业、冲稳保顺序或服从调剂结论已经确定。固定输入是考生成绩、位次、选科和家庭底线，目标院校与专业方向后续会根据完整底座、家庭讨论和专业研究继续调整。

特别注意：

```text
命中不等于可报。
未命中不等于不存在。
机器初判不等于最终建议。
OCR 字段不等于最终事实。
```

## 四、保真机制

为了避免 OCR 错误被误当真值，本项目采用以下保真机制：

1. **来源绑定**：每条公开明细都记录来源期号、PDF SHA256、PDF OCR 页码和 OCR 行号，后续可以回到第 19 期原页复核。
2. **状态锁定**：所有全量 OCR 明细默认 `needs_manual_pdf_review`，且 `最终可用=false`。
3. **字段标记**：对缺少选科、缺少计划数、缺少学费、计划数非纯数字、学费非纯数字、低置信度等情况写入 `字段完整性标记`。
4. **风险标签**：自动标记医学/护理、中外合作/高收费、体检限制、语种单科、专项预科、学费超过 15000 元等风险。
5. **候选覆盖**：单独生成候选池命中表，未命中的候选不直接删除，而是进入组号变化或漏识别复核。
6. **公开安全检查**：公开文件不得包含本地路径、private 路径、图片路径或个人身份信息。
7. **复核队列**：候选池、优先专业、硬风险专业组分别生成复核队列，避免只凭印象挑学校。
8. **页面复核包**：候选池生成 10 页私有页图和页面 OCR 文本，公开仓库只保留页码、文件名和哈希。
9. **完整性审计**：额外生成候选页码组号审计和全量专业明细结构异常队列，专门捕捉页面有组号但结构化漏拆、专业行串到下一院校、页眉串入、专业代号异常、计划数/学费错位等问题。
10. **逐专业种子**：候选 V2 同时保留专业组级定位和逐专业明细，避免只看学校/专业组两层汇总就判断是否能服从调剂。
11. **升级闸门**：候选 V2 升级工作台把原页核验、湖北官方系统/省招办计划、高校章程、家庭接受度、调剂结论、三年投档稳定性拆开记录；默认全部 pending，不能直接进入排序。
12. **质量分层**：全量专业组质量索引把无专业明细、高严重结构异常、重复规范化组码、字段缺失、异常学费、行数不一致、候选命中、逐专业偏好命中和硬风险统一纳入 P0/P1/P3 复核优先级；偏好方向必须来自专业明细，不再把院校名或组标题当作专业偏好。
13. **逐专业工作台**：全量逐专业明细质量工作台为每条专业行生成 `专业行ID`，并附带 `专业组出现ID`、组级质量、专业行异常、字段完整性、偏好/风险标签和复核优先级。
14. **重复保护**：对 `F01403`、`F77804`、`F79104` 这类规范化组码重复行不做去重，保留原行并标记为 P0；逐专业表用 `专业组出现ID` 防止疑似串校内容被同组码覆盖。
15. **底座审计**：新增底座审计摘要、发现表和页级审计表，把 PDF 指纹、页码覆盖、行数闭环、主键唯一、异常闭环、回退归属、重复专业代号和发布边界显式记录。
16. **证据总账**：候选 V2 逐字段复核总账把专业代号、专业名称、选科、计划数、学费、备注、家庭接受度和调剂影响拆成字段任务，并预留原 PDF、湖北官方系统、高校章程、家庭确认值和私有证据编号。
17. **页级 manifest**：公开页级 manifest 覆盖第 1-240 页，只保存页图/OCR 文本哈希、OCR/QC 统计和结构化计数，不公开私有页图、整页 OCR 文本或本机路径。
18. **按页保真复核队列**：按页队列覆盖第 10-240 页 231 个招生计划明细页，逐页对齐 manifest、底座按页审计和全量逐专业字段保真总账；该表只用于排核页顺序和抓页级风险，不替代一行一个招生专业的明细总账。
19. **全量逐专业核验批次**：全量核验批次表覆盖 13736 条招生专业行，把每个专业落到 A0-A9 执行批次，带出 PDF 页证据编号、页级风险、字段风险、家庭底线、偏好方向和核验动作；它是人工核验入口，不是可填报清单。
20. **家庭底线筛选**：家庭底线筛选表把 3329 个专业组按完整组内专业展开，给出医学护理、超预算、特殊限制、偏好方向和调剂初判；办学属性没有权威字段时一律保持 `pending_school_attribute_review`。
21. **候选 V3 复核入口**：V3 不再只保留 20 个历史候选，而是把家庭筛选 R0/R1/R2、候选 V2、同页边界风险和偏好专业线索合并为 1327 个复核入口；每行都展开招生明细，但全部锁定为 `pending_verification` 和 `最终可用=false`。
22. **历史线克制**：候选 V3 只把 2023/2024/2025 同院校专业组代码投档线作为线索；组号变化、0 明细、同校补充组和页图补种组均标记“历史线不得直接沿用”。
23. **B0/B1 核验包**：对 20 个历史候选/组号问题和 29 个数字媒体技术优先组生成组级与逐专业核验包；逐专业任务来自结构化来源，不从长文本拆分，0 明细组只保留占位任务。
24. **官方交叉校验明细主表**：B0/B1 拆成学校官方来源、组级索引、逐专业招生明细主表、原逐专业核验队列、逐专业官网证据匹配表和逐专业证据合并表；候选讨论默认看逐专业证据合并表，组级索引只用于投档、调剂、历史线和补源。高校官网只作辅助补证，若与湖北官方系统、省招办计划或志愿系统不一致，以湖北省招办渠道为准；高校官网省份总计划未拆首选物理/历史时，只核专业名、学费、选科等线索，不硬算物理类计划数。山东工商学院 PDF 已用渲染图 OCR 专业名和 PDF 网格数字列双通道抽取，并保留网格审计表；这仍只是交叉校验证据。
25. **0 明细占位保护**：`C10702`、`K15123` 只有 0 明细占位任务，占位任务只防止专业组丢失，不能冒充真实招生明细；真实逐专业任务当前为 322 条。
26. **机器校验**：`scripts/verify_baseline.py` 会检查全量明细行数、来源 SHA、候选命中数、候选工作台、优先/风险队列、页面复核包、完整性审计、候选 V2 逐专业明细、候选 V2 升级工作台、候选 V2 证据总账、全量质量分层、逐专业质量工作台、全量逐专业核验批次表、优先整组逐专业核验包、优先逐专业证据执行工作台、全量逐专业证据执行工作台、证据闭环任务队列、P0 证据执行包、P0 逐专业复核工作清单、家庭底线筛选表、候选 V3 复核入口、候选 V3 B0/B1 核验包、B0/B1 逐专业招生明细主表、官方交叉校验工作台、逐专业官网证据匹配表、逐专业证据合并表、保真复核队列、底座审计、页级 manifest、按页保真复核队列、专业行原页证据锚点、逐专业闭环缺口看板、逐专业三年投档线索旁挂、单一逐专业招生明细总工作台、字段事实闭环总账、字段事实核验任务队列、P0 字段原页重读工作清单、`最终可用=false`、核验状态、0 明细占位、敏感路径和哈希清单。
27. **P0 证据执行包**：`data/working/issue19-p0-evidence-execution-packets.csv` 从 94935 条闭环任务中抽取 6619 条 P0 任务，覆盖 5310 条招生专业明细、2282 个执行包、231 个 PDF 页和 1056 所学校。`P0执行包ID` 只用于按页、学校、专业组和任务类型组织人工核验，不能作为最终志愿粒度；最终仍必须回到 `专业行ID`、完整组内招生明细和证据闭环状态。
28. **P0 逐专业复核工作清单**：`data/working/issue19-p0-evidence-review-worklist.csv` 把 P0 执行包、全量证据工作台、页级 manifest 和按页保真复核队列合并到一行一专业的复核视图；公开仓库只保存证据编号、SHA、字段候选和 pending 闸口，不保存私有页图、整页 OCR 文本、登录态或最终结论。
29. **逐专业补证表**：新增字段缺口矩阵、湖北官方系统核验包和 B0/B1 官网差异账；三张表均保持一行一个招生专业明细或一行一个招生专业明细×证据项，全部 `最终可用=false`，只用于补证和核验顺序。
30. **统一逐专业底座入口**：`data/working/issue19-major-detail-foundation-release.csv` 是后续新增城市、学校或专业方向时的默认检索入口；它不拆成学校/专业组两层，而是把每个招生专业明细的字段缺口、P0/P1、湖北官方待核、官网差异、家庭底线、调剂风险和下一步动作放在同一行。
31. **底座闭环执行批次**：`data/working/issue19-foundation-closure-major-batches.csv` 保留 C0/C1/C3/C4 主批次；C2 主批次当前为 0，是因为官网辅证任务被 C0/C1 更高优先级覆盖。页级和学校级索引只服务核页与补源，不产生可报结论。
32. **专业行原页证据锚点**：`data/working/issue19-major-line-pdf-evidence-anchors.csv` 给每条招生专业明细生成原页 OCR 行号范围、坐标摘要和窗口哈希；公开表不保存 OCR 窗口原文，私有 JSONL 仅用于人工回看。
33. **原始专业行源证据审计**：`data/working/issue19-raw-major-source-evidence-audit.csv` 用 `来源页码+版面列+专业起始行号` 回连私有 OCR 起始行，再对齐页级 manifest、公开锚点、私有窗口 JSONL 和血缘审计。当前 S0 满回连 13736 条，但 R2/R3 仍需按原页或 QC 风险人工核页；它证明源证据闭合，不证明字段已是最终事实。
34. **逐专业源证据风险侧账**：`data/working/issue19-major-source-evidence-risk-sidecar.csv` 把源证据风险下沉到默认入口，避免只在审计表里看到 R2/R3 风险。当前 X1 13 条、X2 6086 条、X3 7019 条、X4 618 条；它用于核页优先级和证据解释，不生成学校或专业建议。
35. **逐专业闭环缺口看板**：`data/working/issue19-foundation-closure-gap-scorecard.csv` 是今晚实际推进入口；它仍是一行一个招生专业明细，把字段候选、B0/B1 官网旁证、原页锚点和官方/家庭/调剂门禁合并到同一行，方便按 S0-S8 动作桶推进。
36. **三年投档线索旁挂**：`data/working/issue19-major-line-historical-toudang-sidecar.csv` 把 2023/2024/2025 同代码投档线下沉到逐专业明细，但只作冲稳保筛选线索；同代码命中不能证明 2026 专业组、计划数、选科、备注或组内专业保持不变。
37. **单一招生明细总工作台**：`data/working/issue19-admission-detail-master-workbench.csv` 是后续讨论的默认入口；它不是学校/专业组两层摘要，而是 13736 行逐专业招生明细，并把 PDF 原页锚点、字段缺口、官网旁证、家庭/调剂门禁和三年投档线索放在同一行。
38. **结构保真显式化**：`data/working/issue19-admission-detail-structural-fidelity-register.csv` 和 `data/working/issue19-structural-risk-major-line-ledger.csv` 把 1838 条唯一组码回退归属、116 条组内专业代号重复、14 条重复组码、13 条原页窗口 P0 和 1127 条原页窗口 P1 显式下沉到逐专业明细或风险事件，避免只停留在 summary 统计。
39. **0 明细占位保护**：`data/working/issue19-zero-detail-group-placeholder-workbench.csv` 保留 40 个无专业明细专业组，但它们不是招生专业行，不能参与专业接受度、调剂结论或候选排序。
40. **候选筛选准备**：`data/working/issue19-candidate-filter-prep-major-detail.csv` 只支持机器预筛和核验排序；城市只是院校名关键词候选，公办/民办、办学属性、校区、实际办学地点全部保持 pending。
41. **决策闸门显式化**：`data/working/issue19-major-decision-readiness-gates.csv` 把 PDF 原页、湖北官方系统、办学属性、公办民办、城市/校区、家庭接受度、同组调剂、字段缺口全部列成逐专业阻断闸门；G3 也只表示“可作机器预筛线索”，不能定案。
42. **官方回填消歧**：`data/working/issue19-hubei-official-query-key-collision-ledger.csv` 记录 59 个非唯一官方查询三元组、118 条专业明细；后续回填官方系统结果必须按 `专业行ID`、原页位置和官方返回行证据消歧。
43. **教育部学校属性逐专业核验**：`data/working/issue19-moe-school-attribute-major-detail.csv` 覆盖 13736 条招生专业明细；教育部精确匹配 13161 条、父校/校区类保守匹配 190 条、未匹配待核 385 条。民办线索 2230 条、合作办学线索 34 条、职业本科名称线索 241 条都下沉到逐专业行。教育部所在地只作登记地线索，备注为空不能等于公办最终结论，所有行仍需 2026 湖北招生计划和招生章程闭环。
44. **未匹配校名风险账本**：`data/working/issue19-moe-school-attribute-unmatched-schools.csv` 保留 49 个未匹配院校代码+校名，覆盖 OCR 错字、省名截断、特殊院校、港澳台/境外主体、新设/更名学校和职业本科线索；该清单只安排核名和补证，不生成候选结论。
45. **底座稳定性总看板**：`data/working/issue19-foundation-stability-dashboard.csv` 覆盖 13736 条招生专业明细，把 PDF 锚点、教育部属性、湖北官方待核、官网差异、字段缺口、结构风险、官方查询键碰撞、三年投档线索、家庭接受度和同组调剂门禁合并到同一行。B0=2663、B1=4370、B2=5962、B3=542、B4=199；这些等级只说明先核什么，不生成填报建议或录取概率。
46. **逐专业稳定化任务**：`data/working/issue19-foundation-stabilization-major-detail-tasks.csv` 覆盖 B0/B1/B2 共 12995 条招生专业明细；它不是学校/专业组层派单，而是一行一个专业，记录第一核验动作、保真证据链、需双重佐证字段、字段候选、官网差异、结构风险、官方查询键碰撞和阻断原因。所有行 `机器是否允许自动写回主表=false`、`是否允许作为志愿推荐依据=false`。
47. **官方公开入口状态快照**：`data/working/issue19-official-public-entry-status.json` 记录 2026-06-27 湖北教育考试网招生计划页面和索引页公开 HTTP 复核状态，计划页 SHA 为 `5c56b9582418af6e1cfbd40431920a0fee28807492c6be30b972d118251e8776` 且仍含“持续更新中/敬请期待”；湖北招生数智平台无登录探针仍为 401。该快照只说明当前官方公开入口边界，不能替代第 19 期逐专业明细、湖北官方系统字段核验和高校章程交叉核验。
48. **未匹配校名逐专业解析**：`data/working/issue19-moe-unmatched-school-resolution-major-detail.csv` 把教育部未匹配的 385 条专业明细展开为核名工作台；历史同代码候选 281 条、教育部相似候选 232 条、OCR 规则候选 90 条，但 `机器能否自动替换校名=false` 全量保持，任何校名修正必须回看 PDF 原页、湖北官方系统和学校官网/章程。
49. **版面和代号侧账**：`data/working/issue19-major-line-layout-continuity-risk-ledger.csv` 和 `data/working/issue19-major-code-order-risk-ledger.csv` 分别记录版面连续性和专业代号顺序风险，只用于核页派单和消歧，不自动修正 OCR。
50. **字段事实核验任务**：`data/working/issue19-field-fact-verification-tasks.csv` 把 13736 条招生专业明细拆成 41208 条逐字段核验任务，一行一个 `专业行ID × 字段名`。它只安排再选科目、专业计划数、学费的原页重读、候选值回看和湖北官方核验顺序，不写回主表，不生成学校或专业建议。
51. **P0 字段原页重读清单**：`data/working/issue19-field-fact-p0-reread-worklist.csv` 只抽取 11444 条 K0 无候选字段任务，覆盖 8536 条招生专业明细、231 个 PDF 明细页和 967 所学校。该表把每个字段回连到字段任务、源证据审计、PDF 锚点和页级保真队列，只能用于按优先序回看原页和补字段候选。
52. **规则克制**：偏好专业标签只做关键词召回，不做最终专业分类；例如“师范相关”必须回看原 PDF 和专业目录确认。
53. **人工闸门**：进入最终志愿表前，必须回看第 19 期原 PDF 页，并与湖北官方平台或志愿系统、高校官网/招生章程交叉核验。

## 五、下一步复核优先级

第一优先级：

- 从 `issue19-foundation-stability-dashboard.csv` 的 B0/B1/B2 开始排核：B0 先处理校名/结构/官方查询键强阻断，B1 处理 P0 原页或官网冲突，B2 处理字段缺口补证。
- 第一版候选池已命中的 17 个专业组。
- 未命中的 `C10702`、`C10704`、`K15123`，其中 `C10704` 已标记为页面有组号但结构化漏拆。
- 候选 V3 复核入口表中 B0/B1/B2 批次：先核 20 个历史候选/组号问题、29 个数字媒体技术优先组、763 个偏好专业且未自动阻断组。
- B0/B1 逐专业招生明细证据合并表中的 36 所学校、49 个专业组和 324 个逐专业任务；继续补 8 所 `needs_official_plan_source_search` 学校的官网计划或章程来源，同时不能把 `has_reusable_2026_hubei_plan_source` 理解为最终通过。
- 教育部未匹配学校支持清单中的 49 个院校代码+校名，以及 `issue19-moe-unmatched-school-resolution-major-detail.csv` 中的 385 条逐专业核名任务；历史同代码和教育部相似候选只能作为回看原页的线索。
- 页面复核包覆盖的 10 页：17、69、74、80、81、208、209、212、223、226。
- 全量质量复核队列中 `P0-必须优先核页` 的专业组行，尤其是候选池、偏好专业命中、硬风险命中、重复组码、无专业明细和行数不一致项。
- 逐专业明细复核队列中 `P0-逐专业必须核页` 的专业行，尤其是候选池 77 条专业明细、样本学校 560 条专业明细、结构异常和字段缺失项。
- 底座审计发现表中 8 类人工复核项，尤其是 1838 条唯一组码回退归属、候选池命中回退行、31 个组内专业代号重复的专业组。
- 候选 V2 字段复核总账中 494 个 P0 字段任务，尤其是计划数、学费、再选科目、专业接受度和调剂影响。
- 完整性审计中严重程度为“高”的结构异常，尤其是候选学校和优先专业方向所在页。
- 风险标签命中的专业组：医学/护理、中外合作、高收费、体检限制、语种单科、专项预科、学费超过 15000 元。

第二优先级：

- 湖北省内公办保稳样本。
- 师范方向样本。
- 数字媒体技术、计算机类相关专业组。
- 小计划、跨页、无专业行、字段缺失较多的专业组。

第三优先级：

- 明显高冲、当前位次大概率够不到的院校专业组。
- 医学/护理方向已经明确排除的学校，只保留为风险样本。

## 六、升级标准

一条专业组从 OCR 初稿进入候选志愿表，至少要完成：

```text
OCR 初稿/最终可用=false
-> 原 PDF 页人工复核
-> 湖北官方平台或志愿系统核验
-> 学校官网/章程交叉核验
-> 家庭接受度和调剂判断
-> 三年投档稳定性判断
-> 冲稳保排序
```

候选池 V2 的输入是：

- `data/working/issue19-candidate-plan-review-summary.csv`
- `data/working/issue19-candidate-plan-review-major-detail.csv`
- `data/working/issue19-preference-major-search.csv`
- `data/working/issue19-hard-risk-group-review-queue.csv`
- `data/working/issue19-candidate-v2-group-review-seed.csv`
- `data/working/issue19-candidate-v2-major-review-seed.csv`
- `data/working/issue19-candidate-v2-verification-group-workbench.csv`
- `data/working/issue19-candidate-v2-verification-major-workbench.csv`
- `data/working/issue19-full-major-detail-quality-workbench.csv`
- `data/working/issue19-full-major-detail-review-queue.csv`

这些文件只负责把“要复核什么”列清楚。只有完成 PDF 原页、湖北官方平台或志愿系统、学校官网/章程、家庭接受度、调剂风险、三年投档稳定性核验后，才允许从 `needs_manual_pdf_review` 升级为可进入冲稳保排序。

只有同时满足以下条件，才能考虑进入最终志愿表：

- 2026 专业组代码确认无误。
- 组内全部专业确认完整。
- 专业代号、专业名称、计划数、学费、选科、备注确认无误。
- 组内不能接受专业为 0，或明确不服从调剂且风险可控。
- 学费不超过当前家庭上限 15000 元，或经过家庭单独确认。
- 不含医学/护理等明确排除方向。
- 不违反体检、语种、单科、校区、专项资格等要求。
- 近三年投档位次和 2026 计划变化支持其冲稳保定位。
