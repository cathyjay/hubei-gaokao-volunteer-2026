# 数据基座下一批执行工作台 V1

更新时间：2026-06-29

## 当前定位

这份工作台用于继续推进字段事实闭环，不是最终志愿方案，也不是已核准字段表。

它把当前最该推进的三件事放到同一个入口：

- 第一闭环 P0 冲突包：10 个包、26 条任务。
- 高校官网辅证 next20：从 80 个高校侧辅证任务里挑出下一批 20 个优先处理任务。
- 55 个重点专业组调剂风险：继续判断哪些组值得进入下一轮重点核验。

所有行仍保持非最终门禁：不确认字段事实，不允许字段写回，不允许作为志愿推荐依据。

## 直接打开哪个文件

优先打开：

- `data/exports/issue19-data-foundation-next-execution-v1.xlsx`

对应 CSV：

- `data/exports/issue19-data-foundation-next-execution-v1-p0-conflict-packages.csv`
- `data/exports/issue19-data-foundation-next-execution-v1-p0-conflict-tasks.csv`
- `data/exports/issue19-data-foundation-next-execution-v1-school-source-next20.csv`
- `data/exports/issue19-data-foundation-next-execution-v1-priority55-transfer-risk.csv`
- `data/exports/issue19-data-foundation-next-execution-v1-summary.json`

生成脚本：

- `scripts/build_issue19_data_foundation_next_execution_v1.py`

## 工作簿怎么看

1. `00_摘要`：本轮执行工作台的规模、输出和非最终门禁。
2. `01_P0冲突包`：10 个冲突包，按页码版面聚合，显示为什么先核、怎么核、还缺哪些证据。
3. `02_P0冲突逐任务`：26 条逐任务，保留院校、专业组、专业代号、字段范围和状态，用于安排原页核验。
4. `03_官网辅证next20`：下一批 20 个高校官网辅证任务，标记自动补源、结构化、人工最小核验动作和 live 补源状态。
5. `04_55组调剂风险`：55 个重点组的调剂风险层级和是否建议进入下一轮重点核验。

## 当前数量

| 项目 | 数量 |
| --- | ---: |
| P0 冲突包 | 10 |
| P0 冲突任务 | 26 |
| P0 需双人复核任务 | 19 |
| P0 有高校辅证线索任务 | 26 |
| P0 PDF 原页已完成 | 0 |
| P0 湖北官方侧已完成 | 0 |
| P0 字段写回 ready | 0 |
| 高校官网辅证 next20 | 20 |
| next20 覆盖学校 | 18 |
| live 已有结构化可复用 | 1 |
| 55 组建议进入下一轮重点核验 | 29 |

## P0 冲突包优先顺序

当前 P0 包共 10 个：

| 页码版面 | 任务数 | 重点 |
| --- | ---: | --- |
| 135-left | 10 | 江苏理工学院，最大冲突包，10 条均需双人复核 |
| 199-left | 3 | 南宁学院，三字段冲突，均需双人复核 |
| 209-right | 2 | 成都信息工程大学，小包双人复核样本 |
| 169-right | 1 | 山东工商学院，单任务双人复核 |
| 018-left | 4 | 中国传媒大学，跨两个专业组，复核强度混合 |
| 037-left | 1 | 山东大学，单任务双人复核 |
| 137-right | 1 | 浙江工业大学，单任务双人复核 |
| 056-left | 1 | 兰州大学，P0 但非双人复核，需要确认原因 |
| 226-left | 1 | 西安邮电大学，P0 但非双人复核 |
| 226-right | 2 | 西安医学院，P0 但非双人复核，需关注 K487/K488 边界 |

推进原则：先核 `135-left` 打样，再核 `199-left` 和 `209-right` 验证小包流程；P0 但非双人复核的包要补一个“不需双人复核原因确认”，不能默默通过。

## P0 top3 私有复核包

已把最优先的 `135-left`、`199-left`、`209-right` 单独落成第一批私有复核材料：

- 生成脚本：`scripts/build_issue19_p0_top3_review_packet.py`
- 公开台账：`data/working/issue19-p0-top3-review-packet-public-ledger.csv`
- 逐字段公开台账：`data/working/issue19-p0-top3-field-review-public-ledger.csv`
- 公开摘要：`data/working/issue19-p0-top3-review-packet-summary.json`
- 私有材料：`private/review-assets/issue19-p0-top3-review-packet/`，不提交公开仓库。

这批材料覆盖 3 个 P0 冲突包、15 条任务，15 条全部需要双人复核、PDF 原页读数、湖北官方侧记录和高校辅证记录。公开台账只保存包级计数、状态、证据编号和 SHA；页图、OCR 文本、字段候选值、人工读数、复核人和备注只留在私有材料。

逐字段层已进一步拆成 36 个字段核验单元：计划数 15 个、学费 15 个、再选科目 6 个。其中候选关系为 `R0-候选冲突` 16 个、`R3-仅高校辅证候选` 13 个、`R1-候选一致` 6 个、`R2-仅PDFOCR候选` 1 个。关系桶只用于安排核验优先级，不确认字段事实。

注意：同一页列里可能还有其他任务，所以这批 top3 不是按页列从全量公开账本直接抓取，而是以 `data/exports/issue19-data-foundation-next-execution-v1-p0-conflict-tasks.csv` 的 `第一闭环任务ID` 为准，再回连私有工作台。

## 第一闭环字段状态看板

新增页列级执行视图：

- 生成脚本：`scripts/build_issue19_first_closure_field_status_dashboard.py`
- 公开看板：`data/working/issue19-stable-foundation-first-closure-field-status-dashboard.csv`
- 公开摘要：`data/working/issue19-stable-foundation-first-closure-field-status-dashboard-summary.json`

这张表不是新增事实源，而是把第一闭环 206 条字段确认任务重新压缩到 37 个 `PDF页码×版面列`，方便下一步按页列核 PDF 原页。当前主阻断为：10 个页列先核 PDFOCR 与高校辅证冲突，4 个页列缺候选需人工看图，17 个页列可用机器坐标辅助核页，6 个页列按 PDFOCR 候选人工确认。

它只公开页列状态、计数、集合 SHA 和门禁，不保存字段明细、候选明细、院校专业明细或私有路径。字段写回、推荐依据、学校专业建议和最终可用仍全部为 0。

## 第一闭环证据状态报告

新增第一闭环证据状态公开报告：

- 生成脚本：`scripts/build_issue19_first_closure_evidence_status_report.py`
- 任务级公开账本：`data/working/issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv`
- 页列级公开汇总：`data/working/issue19-stable-foundation-first-closure-evidence-status-page-side-summary.csv`
- 公开摘要：`data/working/issue19-stable-foundation-first-closure-evidence-status-summary.json`

这张报告把 206 条第一闭环任务按 `PDF原页证据状态 / OCR提示状态 / 机器坐标提示状态 / 高校辅证证据状态 / 湖北官方侧状态 / 冲突状态 / 三方闭环状态 / 字段写回门禁` 并排展示。当前 PDFOCR 提示 103 条、机器坐标提示 49 条、高校辅证线索 74 条、PDFOCR 与高校辅证冲突 26 条、PDFOCR 无候选 103 条，其中真正无候选需人工看图 54 条；直接看图 80 条、双人复核 91 条。

它是“下一步怎么核”的状态报告，不是“字段已经核准”的结果表。公开层只保存状态桶、计数、ID、SHA 和下一步动作，不保存字段值、OCR 原文、学校专业明细、人工记录或私有路径；字段写回、推荐依据、学校专业建议和最终可用仍全部为 0。

## 第一闭环 B0 冲突页列核验状态

新增 B0 冲突页列公开账本：

- 生成脚本：`scripts/build_issue19_first_closure_b0_conflict_status.py`
- 公开账本：`data/working/issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv`
- 公开摘要：`data/working/issue19-stable-foundation-first-closure-b0-conflict-status-summary.json`

这张表专门处理字段状态看板中 `B0-PDFOCR与高校辅证冲突` 的 10 个页列。当前 10 个页列覆盖 132 条同页任务，其中 26 条是明确 PDFOCR 与高校辅证冲突，106 条是同页伴生待闭环任务。B0 冲突字段类型为计划数 26、学费 26、再选科目 16；需要人工直接看图 56 条，需要双人复核 46 条。

统计口径单独保留两层：全局 B0/B1 计划数冲突专项共 19 条，其中疑似学费错位 13 条、计划数不一致 6 条；落在这 10 个 B0 页列内的是 18 条，其中疑似学费错位 13 条、计划数不一致 5 条。这样后续不会把“全局专项冲突”和“B0 页列内冲突”混成一个数。

该表只公开页列级计数、字段类型、证据编号、状态桶和集合 SHA；不公开学校专业明细、字段候选值、OCR 原文、人工读数或私有路径。字段写回、推荐依据、学校专业建议和最终可用仍全部为 0。

## 第一闭环事实证据通道工作台

新增事实级执行视图：

- 生成脚本：`scripts/build_issue19_first_closure_fact_evidence_channel_workbench_v1.py`
- 公开工作台：`data/working/issue19-first-closure-fact-evidence-channel-workbench-v1-public-ledger.csv`
- 公开摘要：`data/working/issue19-first-closure-fact-evidence-channel-workbench-v1-summary.json`

这张表把第一闭环 439 个事实范围逐项接到 PDF 原页、OCR、机器坐标、高校官网辅证、湖北官方侧、冲突处理、双人复核、三方闭环、专业名归属和专业组边界通道。当前事实域为字段事实 354、专业名归属 48、专业组边界 37；动作组用于安排 A0 冲突先核、A1 专业名归属先核、A2 专业组边界随页先核、A3 双人复核先核、A4 人工看图、A6 高校辅证提示回接和 A7 常规 PDF/湖北官方闭环。

这张表只用于排下一步最小核验动作，不确认计划数、学费、选科、专业名或专业组边界，不写回主表，也不生成学校/专业建议或志愿推荐。公开层不保存学校名、专业名、字段值、OCR 原文、图片路径、人工记录或登录态。`同校高校源*` 字段是随事实行重复的同校上下文，不能跨行求和。

新增事实动作包执行视图：

- 生成脚本：`scripts/build_issue19_first_closure_fact_action_packets_v1.py`
- 公开工作台：`data/working/issue19-first-closure-fact-action-packets-v1-public-ledger.csv`
- 公开摘要：`data/working/issue19-first-closure-fact-action-packets-v1-summary.json`

这张表把事实证据通道工作台压成 79 个 `页列×事实核验动作组` 包，避免直接在 439 条事实行里安排执行。每个包保留事实数、字段事实数、专业名归属、专业组边界、证据通道分布、缺口计数、集合 SHA 和下一步最小动作；`同校高校源*` 字段按高校源进度看板 ID 去重后只作同校上下文。它仍不确认任何招生字段，不写回主表，也不生成学校专业建议。

新增高校源 Adapter/Diff 执行视图：

- 生成脚本：`scripts/build_issue19_school_source_adapter_diff_execution_workbench_v1.py`
- 公开工作台：`data/working/issue19-school-source-adapter-diff-execution-workbench-v1-public-ledger.csv`
- 公开摘要：`data/working/issue19-school-source-adapter-diff-execution-workbench-v1-summary.json`

这张表把 12 个高校官网结构化接入候选推进到 adapter、parser、normalized bridge 和候选 diff 的执行层。当前 4 行需要新建 adapter 或 bridge，8 行已有结构化线索需统一 normalized 输出；8 行属于优先生成冲突或高明细 diff，3 行生成补缺或常规 diff，1 行先做来源边界防串校验。它只服务高校源 double check 和人工核验压缩，不替代 PDF 原页、湖北官方计划或家庭决策。

## 高校官网 next20

下一批官网辅证任务按高风险和高收益混排：

- 高收益缺源：武汉轻工大学、长春工业大学、湖北师范大学、浙江传媒学院、成都师范学院、西安航空学院、韶关学院。
- 冲突优先回页：江汉大学、西北民族大学、南宁学院、西安建筑科技大学、喀什大学、山东工商学院、北京语言大学、江苏理工学院、杭州电子科技大学。
- 官网补缺：西安邮电大学、山东工商学院、中国传媒大学。
- 专业名未匹配：江汉大学。

新增 `data/working/issue19-school-source-next20-official-probe-public-ledger.csv` 后，next20 的官网源状态已经更清楚：

- 20 个任务行、18 所学校。
- 15 个任务行已有结构化高校侧辅证，覆盖 13 所学校。
- 已有结构化源包括武汉轻工大学、湖北师范大学、江汉大学、西北民族大学、西安邮电大学、南宁学院、西安建筑科技大学、山东工商学院、北京语言大学、江苏理工学院、西安航空学院、中国传媒大学、杭州电子科技大学等不同类型的官方 API/PDF/XLSX/HTML/图片转录源。
- 喀什大学已有官方 XLSX 湖北列，但科类边界仍要再核。
- 长春工业大学、浙江传媒学院、成都师范学院、韶关学院仍属于继续补源或入口失败状态。

这些高校侧来源只能用于 double check、冲突发现、补缺提示和人工核验排序；不能替代第 19 期原页、湖北官方系统或省招办计划。

配套的 `data/working/issue19-school-source-status-snapshot-public-ledger.csv` 已把 80 个官网辅证机会任务扩展成完整状态快照，覆盖 36 所学校。它把机会优先级、官网来源状态、C4/C6 补结构化或补源包、live 记录、候选 diff、PDF 原页待核、湖北官方侧待核和写回门禁放在一起看：P0 44 条、P1 18 条、P2 13 条、P3 5 条；36 条任务属于高风险冲突或补缺需先核 PDF 原页和湖北官方侧，17 条已有高校侧结构化线索但不得写回，1 条 live 已有结构化线索但仍需 PDF 和湖北官方闭环，21 条仍需补结构化、补规则或继续找计划网源，5 条只核章程规则限制。该快照用于安排下一轮自动补源和人工最小核验，不新增字段事实。

`data/working/issue19-school-source-auto-execution-batches-public-ledger.csv` 在上述状态快照基础上新增执行批次层，继续保持 80 条任务粒度。当前可直接推进的自动/半自动泳道为：A0 冲突回页 17 条、A1 官网补缺回页 8 条、A2 专业名归属 12 条、A3 补结构化 18 条、A4 继续找高校计划网源 8 条、A5 章程规则 16 条、A7 留存观察 1 条。该表是后续继续推进高校官网 double check 的总控入口，不作为字段事实或志愿方案依据。

## 完成条件

一个 P0 包从“排队”推进到“可评估写回”，至少需要：

1. 完成第 19 期 PDF 原页人工读数。
2. 完成湖北官方系统或省招办计划核验。
3. 完成高校官网或招生章程辅证记录。
4. 需要双人复核的任务完成第二人复核；P0 但未标双人的任务记录原因。
5. 三方一致性状态明确，不再是 pending。

即便完成这些，也只是进入“字段写回评估”，不能自动成为最终志愿依据。最终志愿还要继续核招生章程、完整专业组、调剂风险、投档线和家庭接受度。
