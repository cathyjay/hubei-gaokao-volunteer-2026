# 目标与决策框架

最后更新：2026-06-28

## 一、项目目标

在 2026-06-30 前，为湖北 2026 普通类首选物理考生形成最终志愿方案。考生总分 515，累计位次 91723，位次区间 90895-91723。

核心目标有两个：

1. 保证录取成功率，避免滑档、退档，避免被明显不能接受的专业锁定。
2. 尽量用足 515 分和 91723 位次，不因为不了解学校和专业而过度保守。

2026-07-02 12:00 前只保留应急修改缓冲；官方本科普通批集中填报截止时间是 2026-07-02 17:00。

当前阶段的直接目标是先把 2026 湖北招生计划原始数据底座坐稳。这里的“坐稳”指《湖北招生考试》第 19 期和湖北官方计划相关原始数据被准确结构化、可回到原页或官方入口复验、可按 `专业行ID` 重复使用；不是目标院校、目标专业或志愿方案已经确定。考生分数、位次、选科和家庭底线是固定输入，城市、学校和专业方向仍会随着后续证据和家庭讨论继续扩展。前面提到的成都、西安、武汉、北京，以及数字媒体技术、计算机类、师范类，只是初始参考维度。

当前新增的原始数据审计和下沉门禁分别处理“链路不漂”“源头可回”和“风险可复用”：原始逐专业明细血缘审计要求 13736 条 OCR 专业行全部能一一回连到下游主表，且核心 OCR 字段漂移为 0；原始逐专业明细源证据审计要求 13736 条专业明细全部按 `来源页码+版面列+专业起始行号` 回连到私有 OCR 起始行、页级 manifest、私有窗口 JSONL 和公开原页锚点，且哈希与计数一致；逐专业源证据风险侧账再把源证据风险、底座稳定性、闭环缺口和 P0 复核任务下沉到同一条 `专业行ID`。这些属于“原始数据准确结构化”的证明，不属于“院校/专业已经可推荐”的证明。

## 二、数据策略

不能只看 2025 年，也不能用裸分直觉判断。每个候选院校专业组都要尽量看 2023、2024、2025 三年数据，并转换到 2026 位次语境下比较。

当前等位参照：

| 年份 | 等位分 | 等位位次区间 | 用途 |
| --- | ---: | --- | --- |
| 2025 | 494 | 90979-91841 | 最近一年主要参照 |
| 2024 | 497 | 91113-91965 | 第二年稳定性校验 |
| 2023 | 481 | 91236-91884 | 第三年趋势校验 |

候选项必须核验：

- 近三年投档线和位次趋势。
- 专业组代码是否变化，组内专业组成是否变化。
- 是否属于普通类、中外合作、预科、民族班、国家专项、地方专项、护理类、校企合作、联合培养等特殊类别。
- 2026 湖北招生计划、选科要求、专业备注和招生章程。

2026 招生计划明细底座的默认粒度是一行一个招生专业明细，院校专业组只是投档和调剂范围字段。只有当原始招生专业明细准确结构化之后，后续才适合叠加家庭偏好、专业研究、城市地区展示字段、近三年投档稳定性和冲稳保排序。Round3 生成候选时不按城市加分或设名额。
当前第 19 期底座数据坐稳的直接入口是 `data/working/issue19-p0-immediate-page-execution-queue.csv`、`data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv`、`data/working/issue19-p0-immediate-page-review-packets.csv`、`data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv`、`data/working/issue19-p0-immediate-crop-ocr-public-audit.csv`、`data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv`、`data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv`、`data/working/issue19-field-fact-p0-immediate-review-packet.csv`、`data/working/issue19-field-fact-closure-ledger.csv`、`data/working/issue19-field-fact-verification-tasks.csv`、`data/working/issue19-field-fact-p0-reread-worklist.csv`、`data/working/issue19-field-fact-p0-reread-machine-candidates.csv`、`data/working/issue19-field-fact-p0-closure-action-workbench.csv`、`data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv` 和 `data/working/issue19-field-fact-p0-triage-execution-workbench.csv`：它们不替代湖北官方计划，只负责把再选科目、专业计划数、学费三项关键字段的缺口、候选、语义风险、PDF 原页待核状态、高校官网/章程辅证线索和湖北官方待核状态逐专业、逐字段结构化。P0 字段原页重读清单专门处理 K0 无候选字段，机器坐标候选表只给人工回页提供候选值和坐标线索，闭环推进工作台再把 PDF 原页、湖北官方系统或省招办计划、高校官网或章程三方待核状态分列，语义多源审计表把明显 OCR 噪声、候选偏大、官网补缺线索和多源冲突提前标出，三方核验执行工作台把 11444 条字段任务排成稳定执行顺序并逐行回连 PDF 原页锚点、湖北官方待核包和高校辅证线索，即时复核包再从中切出 319 条最高优先级字段任务，裁图证据索引再为这 319 条任务提供本地原页裁图的公开证据编号、哈希和 bbox，P0 即时三方闭环公开账本再把 PDF 原页、湖北官方系统或省招办计划、高校官网或章程三列状态分离，裁图 OCR 公开审计再用第二套 OCR 对 319 张私有裁图做状态级复读，字段确认公开账本再把私有人工记录是否完成、是否需要双人复核、是否存在三方冲突和是否可进入字段写回评估转成公开状态机，按页核页包再把 319 条任务按 `PDF页码×版面列` 分成 148 个执行包，PDF 原页读数候选公开审计再把私有候选读数降格为“有候选/无候选/冲突/需双人复核”的公开状态，页列核页执行队列再把 148 个页列包按候选冲突、无稳定候选、候选一致待官方和常规候选四档排序，方便人工逐页逐列看原件并防止左右列串读。所有这些表都避免把高校线索或单一 OCR 候选越权当事实，保证后续家庭偏好和专业分析不会建立在含混字段上。

本轮新增的 `data/working/issue19-field-fact-page-side-verification-queue.csv`、`data/working/issue19-page-side-foundation-risk-register.csv`、`data/working/issue19-page-side-foundation-verification-batches.csv`、`data/working/issue19-page-side-foundation-batch-execution-packets.csv`、`data/working/issue19-page-side-foundation-review-progress-public-ledger.csv`、`data/working/issue19-page-side-foundation-field-clue-public-audit.csv`、`data/working/issue19-page-side-foundation-human-review-overlay-public-ledger.csv`、`data/working/issue19-page-side-foundation-all-batch-review-public-ledger.csv` 和 `data/working/issue19-p0-immediate-page-execution-progress-public-ledger.csv` 继续服务于同一个目标：第一张表把全量 41208 条字段任务聚合到 462 个 `PDF页码×版面列` 执行单元，确保后续新增城市、学校或专业方向时仍能回到全量原始字段任务；第二张表在同一页列粒度上叠加结构、源证据、官方消歧、官网差异、决策闸门等风险，形成 460 个 Z0、2 个 Z1 的全量页列核验入口；第三张表把这 462 个页列按风险顺序切成 19 个可执行核验批次，前 18 批各 25 个页列、最后 1 批 12 个页列；第四张表进一步为 19 批生成批次级执行包，并在本地私有目录生成每批 HTML/CSV 核页材料，公开层只保留私有材料 SHA、批次计数和非最终门禁；第五张表把 19 批私有核页材料的填写状态公开成 462 行进度账本；第六张表把 41208 个字段任务重新聚合到 462 个页列，只公开字段分布、状态桶、线索缺失/冲突计数和私有模板 SHA，明确当前仍无任何字段事实可写回；第七张表在不可变字段线索模板之上建立私有人工复核 Overlay，公开层只同步 Overlay 记录数、已填计数、私有 CSV SHA 和非最终门禁，防止后续人工读数覆盖机器线索或误公开字段值；第八张表把第 1 批样板扩展为全 19 批公开复核账本，证明 462 个页列、13736 条专业明细和 41208 个字段任务都已经进入可复核流水线，但人工填写、字段确认、推荐依据和最终可用仍全部为 0；第九张表把 P0 即时 148 个页列包的私有核验进度公开成计数和门禁，明确当前全部仍为 R0，不能因为已经有执行队列就误判为字段已核准。官方入口状态已刷新到 2026-06-28：湖北教育考试网计划页和索引页公开可访问，但计划页仍含“持续更新中/敬请期待”；湖北招生数智平台首页可访问但无登录探针仍返回 401。目标院校、目标专业和城市范围仍未锁定，这些表只让原始招生计划数据更准确、更可复用。

新增的 `data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv` 和 `data/working/issue19-stable-foundation-minimal-manual-closure-workbench.csv` 是当前“湖北官方公开结构化源暂不可得”时的下一步闭环入口：前者把 854 条高校官网辅证分成自动复跑、冲突、补缺、补结构化和补源动作，后者把 319 条 P0 即时字段任务压缩成最小人工核页包。它们只能决定核验顺序和工作量压缩方式，不能把高校官网、裁图 OCR 或人工派单当作最终招生计划事实。

新增的 `data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv` 是高校侧辅证刷新账本：把 854 条 B0/B1 高校官网辅证按 `高校×高校侧辅证动作` 聚合成 80 条任务，覆盖 36 所学校。它用于自动复跑或补结构化高校官网/API/XLSX/PDF/图片来源，并把 C0/C1/C7 必核项、C2 抽检项、C4/C6 补结构化和补源项分开；抽检失败时升级同页列、同校或同专业组人工核验。该账本仍只是 double check 和低人工量派单层，不替代湖北官方侧和第 19 期原页。

新增的 `data/working/issue19-school-source-status-snapshot-public-ledger.csv` 是高校官网辅证状态快照：它把 80 条高校侧辅证机会任务、36 所学校、C4/C6 补结构化/补源包、已有结构化高校源、live 补源记录和最终门禁统一到一张公开状态账本。当前 44 条 P0 立即处理、18 条 P1 高收益自动补源、13 条 P2 常规自动补源或抽检、5 条 P3 留存；所有 80 条仍同时阻断 PDF 原页核验、湖北官方侧核验和字段写回。它只告诉我们“哪些学校和任务下一步可以自动推进或需要人工核 PDF 原页”，不能把高校官网线索、API 线索或 live 探针结果当成最终招生计划事实。

新增的 `data/working/issue19-school-source-adapter-diff-execution-workbench-v1-public-ledger.csv` 和 `data/working/issue19-school-source-adapter-diff-execution-workbench-v1-summary.json` 是高校源 Adapter/Diff 执行层：它把 12 个已有公开结构化或半结构化源的候选学校接到 adapter、parser、normalized bridge 和候选 diff 动作上，用于继续自动 double check、发现冲突和压缩人工核验范围。它仍不确认计划数、学费、选科、专业名或专业组边界，不允许字段写回，也不能替代湖北官方计划。

新增的 `data/working/issue19-school-source-adapter-parse-audit-v1-public-ledger.csv` 和 `data/working/issue19-school-source-adapter-parse-audit-v1-summary.json` 是高校源 Adapter 解析审计层：它对 12 个来源实际跑 parser，确认这些来源能解析出 326 条湖北物理类计划行，并记录计划数、学费、选科、组内代码和校内组线索覆盖情况。它只证明“机器能解析出线索”，不证明这些线索已经可写回或可用于最终志愿。

新增的 `data/working/issue19-school-source-adapter-candidate-diff-v1-public-ledger.csv` 和 `data/working/issue19-school-source-adapter-candidate-diff-v1-summary.json` 是高校源 Adapter 候选 diff 层：它把 326 条私有 normalized 高校源和 344 条同校招生明细做自动匹配，公开层只保留计数、SHA 和非最终门禁。它的价值是压缩人工核验范围，尤其是计划数冲突、OCR 缺失但高校源可补、疑似匹配和一致候选抽检；它不能替代第 19 期 PDF 原页、湖北官方侧或家庭调剂判断。

新增的 `data/working/issue19-school-source-adapter-d0-d1-manual-review-packets-v1-public-ledger.csv` 和 `data/working/issue19-school-source-adapter-d0-d1-manual-review-packets-v1-summary.json` 是高校源 Adapter 的最小人工核验入口：它把 344 条私有 diff 明细压缩成 146 条需要优先人工看的私有核验项，公开层只保留包级计数和 SHA。这个入口用于“少量人工换较高保真”，不是最终志愿建议。

新增的 `data/working/issue19-school-source-auto-execution-batches-public-ledger.csv` 是该状态快照的执行层：它不新增字段事实，只把 80 条任务拆成冲突回页、官网补缺回页、专业名归属、补结构化、继续补源、章程规则和留存观察 7 条泳道。当前它用于继续落实基础数据基座，把“我可以自动推进什么”和“哪些必须人工/官方闭环”分清楚。

新增的 `data/working/issue19-stable-foundation-first-closure-detail-packet.csv` 和 `data/working/issue19-stable-foundation-first-closure-page-side-packet.csv` 是第一批执行入口：把最高优先级的 206 条明细任务集中到 37 个页列，先核冲突、补缺、官网未匹配和高校辅证字段线索。它只压缩人工工作量和安排核验顺序，不改变“湖北官方计划和 PDF 原页闭环前不得定案”的原则。

配套的 `data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-review-summary.json` 已把这 37 个页列接入私有复核页面和公开状态机。公开层只同步任务数、私有材料 SHA、回链和门禁；当前 37 个页列全部还是 `R0-Overlay已生成未填写`，所以它只是第一闭环的执行承接材料，不是字段核准表或志愿建议表。

进一步的 `data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-task-review-summary.json` 把 206 条任务逐条回连到页列材料、PDF 原页、湖北官方侧、高校辅证线索和公共来源文件 SHA。它让后续人工核页可以按任务推进，但所有推荐、写回、最终可用门禁仍为 0。

新增的 `data/working/issue19-stable-foundation-first-closure-triage-prefill-public-audit.csv` 和 `data/working/issue19-stable-foundation-first-closure-triage-prefill-summary.json` 只公开第一闭环私有预填的页列级审计：37 个页列、206 条任务、74 条高校侧辅证候选线索已经进入私有核页提示层，但公开层不保存候选值。它的作用是减少人工打开高校官网和逐行查找成本，不改变“PDF 原页、省招办/湖北官方侧、必要高校侧辅证和双人复核闭环前不得定案”的原则。

新增的 `data/working/issue19-stable-foundation-first-closure-execution-queue.csv` 和 `data/working/issue19-stable-foundation-first-closure-execution-queue-summary.json` 把这 37 个页列排成第一闭环核验顺序：E0 冲突异常双人优先核验 18 个、E1 计划数补缺或偏大优先核验 11 个、E2 官网未匹配专业名归属核验 8 个。它只公开页列顺序、计数、证据编号、SHA、完成条件和阻断原因，不公开学校专业明细、候选值、人工读数、识别正文或私有路径；它是“先核什么”的工作台，不是“已经核准”的事实表。

新增的 `data/working/issue19-first-closure-resolution-execution-overlay-v1.csv` 和 `data/working/issue19-first-closure-resolution-execution-overlay-v1-summary.json` 是第一闭环的准出执行叠加入口：它把执行队列、439 个事实准出缺口、核验结果页列汇总和公开证据地图压到 37 个页列上，明确每个页列离“可进入私有写回评审”还差什么。当前 37 个页列分为 R0 冲突事实先闭环 10 个、R1 专业名归属先闭环 9 个、R2 双人复核先闭环 18 个；所有字段写回、推荐依据、学校专业建议和最终可用仍为 0。

新增的 `data/working/issue19-first-closure-fact-evidence-channel-workbench-v1-public-ledger.csv` 和 `data/working/issue19-first-closure-fact-evidence-channel-workbench-v1-summary.json` 是事实级证据通道工作台：它把同一批 439 个事实范围逐条接到 PDF 原页、OCR、机器坐标、高校官网辅证、湖北官方侧、冲突处理、双人复核、三方闭环、专业名归属和专业组边界通道。它只回答“下一步最小核验动作是什么”，不确认字段事实，不写回主表，不生成学校专业建议或志愿推荐；其中 `同校高校源*` 字段只是随事实行重复展示的同校上下文，不能跨行求和。

新增的 `data/working/issue19-first-closure-fact-action-packets-v1-public-ledger.csv` 和 `data/working/issue19-first-closure-fact-action-packets-v1-summary.json` 是事实动作包执行层：它把 439 个事实范围压成 79 个页列动作包，用于按 A0/A1/A2/A3/A4/A6/A7 批量推进 PDF 原页、湖北官方侧、高校辅证、冲突处理、双人复核、专业名归属和专业组边界核验。它只安排执行，不确认计划数、学费、选科、专业名或专业组边界，也不进入学校专业推荐。

新增的 `data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv` 和 `data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit-summary.json` 是第一闭环 PDF OCR 候选提示层：覆盖 206 条任务，103 条已有 PDF OCR 候选，103 条需人工看图，26 条存在 PDF OCR 与高校辅证冲突，13 条存在一致字段但仍需官方闭环。它把私有候选值留在 Git 忽略目录，公开层只同步状态桶和计数，用于减少人工找行成本，不能自动写入人工记录或字段事实。

新增的 `data/working/issue19-stable-foundation-first-closure-page-side-candidate-dashboard.csv` 和 `data/working/issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit.csv` 继续压缩第一闭环人工工作量：前者把 206 条任务按 37 个页列给出核验动作，后者把 103 条原缺 PDF OCR 候选任务中的 49 条提升为机器坐标候选待人工核页。机器坐标候选只用于提示人工回看 PDF 原页，仍必须核湖北官方侧，不得自动写回字段事实或进入志愿推荐。

新增的 `data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv` 是第一闭环的字段确认桥：它不公开候选值和人工读数，只把 206 条任务的 PDF 原页私有记录、湖北官方侧私有记录、高校辅证私有记录、双人复核和三方一致性状态同步为公开状态机。当前它显示 206 条任务仍全部卡在 PDF 原页和湖北官方侧待核阶段，字段写回、推荐依据、学校专业建议和最终可用全部为 0；这正是后续人工或登录官方系统核验的执行入口，而不是最终招生计划事实表。

新增的 `data/working/issue19-stable-foundation-first-closure-field-status-dashboard.csv` 把这 206 条字段确认任务再压缩到 37 个页列，直接给出每个页列的主阻断和下一步动作：10 个页列先核 PDFOCR 与高校辅证冲突，4 个页列缺候选需人工看图，17 个页列可用机器坐标辅助核页，6 个页列按 PDFOCR 候选人工确认。它让后续核页可以按页列执行，但仍只保存状态、计数、集合 SHA 和门禁，不确认字段事实。

新增的 `data/working/issue19-stable-foundation-first-closure-evidence-status-public-ledger.csv` 和 `data/working/issue19-stable-foundation-first-closure-evidence-status-page-side-summary.csv` 是第一闭环证据状态报告：把 206 条任务的 PDF 原页待核、OCR 提示、机器坐标提示、高校辅证、冲突状态、湖北官方侧待核和写回门禁并排放到一个公开状态层。它解决的是“哪些任务下一步怎么核、哪些只是提示、哪些必须双人复核”的可读性问题，不新增字段事实；当前字段写回、推荐依据、学校专业建议和最终可用仍全部为 0。

新增的 `data/working/issue19-stable-foundation-first-closure-b0-conflict-status-public-ledger.csv` 则把上述 10 个 B0 冲突页列单独抽出，形成更小的优先核验入口：10 个页列覆盖 132 条同页任务，其中 26 条为明确 PDFOCR 与高校辅证冲突，106 条为同页伴生待闭环任务。它同时记录全局 B0/B1 计划数冲突专项 19 条和 B0 页列内 18 条两个口径，防止后续把专项统计和页列统计混用。该表仍只安排 PDF 原页、湖北官方侧、高校辅证和双人复核顺序，不确认字段事实。

## 三、学校分析维度

- 城市和校区：当前不限制城市或地区；城市用于生活成本、交通、就业资源、实习机会和家庭接受度讨论，不参与 Round3 机器筛选加分。
- 属性：公办、民办、独立学院、职业本科、中外合作要分开看。
- 平台：硕士点、博士点、优势学科、行业资源、实习机会。
- 校区：实际就读校区、交通、生活成本、是否异地校区或联合培养。
- 费用：学费、住宿费、中外合作费用、民办费用。
- 稳定性：招生计划人数、历史波动、是否小计划专业组。
- 风险：退档、调剂、体检限报、单科要求、专业备注。

## 四、专业分析维度

当前先记录三个可能方向：

- 数字媒体技术
- 计算机类相关专业
- 师范类专业

当前优先级为：数字媒体技术 > 计算机/软件/人工智能/网络/电子信息 > 机械自动化/机器人工程 > 师范类 > 环境/农业/工商旅游管理等待了解方向。师范类可以了解，但需要继续确认是否愿意从教、是否接受考编压力和就业地区约束。临床医学、口腔医学、中医等医学主线暂缓；护理、动物医学/兽医本轮暂不纳入；医技/康复只进入专项了解，不自动进入普通主方案。

这些仍不是最终结论。后续每个专业都要按以下维度判断：

- 课程难度：数学、物理、编程、设计、表达、实习强度。
- 与成绩匹配：数学 88、物理 50 提示对强理论、强硬件、强物理方向要谨慎；英语 122 是明显优势。
- 就业出口：本科就业、考研必要性、考编考证、地域依赖、行业周期。
- 转换空间：能否转向数据、教育、运营、产品、考公、考编或考研。
- 调剂后果：同一专业组里是否有明显不能接受的专业。
- 家庭和考生偏好：兴趣、禁忌、城市地区接受度、费用承受度。

## 五、冲稳保定义

冲、稳、保不是按感觉分，而是按位次、专业组风险和可接受度共同判断。

| 风险桶 | 定义 | 使用原则 |
| --- | --- | --- |
| 冲 | 历史等位分或位次略高于当前水平，但专业组可接受，退档和调剂风险可控 | 数量不能过多，不能放不能接受的组 |
| 稳 | 历史等位分和当前水平接近，学校/专业/城市综合可接受 | 志愿表中部主力 |
| 保 | 历史等位分明显低于当前水平，录取概率更高，且能接受专业组内调剂 | 必须足够可靠，不能只保学校不保专业 |

最终表中每个候选院校专业组都必须记录：

- 年份数据：2023、2024、2025 投档线和位次。
- 2026 计划：专业组代码、专业、人数、选科、备注。
- 可接受专业、勉强接受专业、不能接受专业；范围必须覆盖整个院校专业组，不只覆盖主动填报的 6 个专业。
- 是否服从调剂，以及服从调剂的前提；前提是组内所有可能调剂专业都能接受且符合录取要求。
- 风险桶：冲、稳、保。
- 入选理由或排除理由。
- 复核状态：CSV 核、原件核、2026 计划核、章程核、最终核。

## 六、最终决策原则

1. 官方来源优先，第三方平台只用于发现和交叉校验。
2. 位次优先于裸分，等位分优先于跨年直接比分数。
3. 不把不能接受的院校专业组放进志愿表。
4. 服从调剂前必须默认接受组内所有可能被调剂到的专业。
5. 保底项必须同时保学校属性、专业可接受度和录取概率。
6. 投档不等于录取；投档线只能说明进入院校专业组的门槛，不能说明组内每个专业都能录取。
7. 任何临时修改都要记录原因、来源和影响范围。
