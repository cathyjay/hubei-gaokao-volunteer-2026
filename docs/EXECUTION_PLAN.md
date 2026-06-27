# 推进计划：从数据底座到最终志愿方案

最后更新：2026-06-27

当前公开仓库不是最终志愿方案，而是招生计划数据底座、证据链和核验工作台。只有 PDF 原页、湖北官方系统或省招办计划、高校官网/章程、家庭接受度和同组调剂结论全部闭环后，才能从底座进入最终志愿排序。

## 一、项目最终目标和当前阶段边界

本项目的最终目标不是“尽可能整理更多数据”，而是在 2026-06-30 前形成一套可执行、可解释、可核验的湖北 2026 本科普通批志愿方案。

当前阶段的核心不是先锁定学校或专业，而是把 2026 湖北招生计划原始数据准确结构化。也就是说，底座数据坐稳的标准是：每条招生专业明细都能回到第 19 期原页、湖北官方计划入口、必要的高校官网/章程辅证和项目内稳定 `专业行ID`；后续再根据分数、位次、家庭预算、不能接受专业、城市和专业兴趣做筛选决策。此前给出的城市和专业方向只是初步参考，不代表目标院校或专业已经确定。

最终方案必须回答清楚：

- 填哪些院校专业组。
- 每个院校专业组内填哪 6 个专业，顺序是什么。
- 是否服从调剂，以及为什么可以服从或不能服从。
- 每个志愿项属于冲、稳、保哪一类。
- 为什么这个方案既能保证录取成功率，又尽量用足 515 分、91723 位次。

2026-07-02 12:00 前只保留应急修改缓冲；不再做方向性大改。

## 二、整体决策链路

用户当前理解的流程基本正确，可以整理为：

```text
个人考试成绩和位次
-> 2023/2024/2025 三年历史投档数据
-> 2026 年湖北招生计划
-> 家庭偏好和底线
-> 平行志愿和院校专业组规则
-> 冲稳保志愿方案
-> 最终填报核对
```

其中有几个需要修正或补充的点：

1. 不能直接知道“同位次学生具体都报了什么志愿”。公开可靠数据通常只能看到院校专业组投档线、投档位次、招生计划和专业组信息，不能看到每个学生的个人志愿选择。
2. 不能用 2026 裸分 515 直接和往年 515 对比，必须优先使用位次和等位分。当前等位参照是 2025 年 494 分、2024 年 497 分、2023 年 481 分。
3. 历史投档线只能判断录取概率，不能替代 2026 招生计划。最终能不能报、能不能服从调剂，必须看 2026 年院校专业组和组内全部专业。
4. 平行志愿的填报对象是“院校专业组”，不是单独学校，也不是单独专业。一个院校专业组下最多填 6 个专业，专业之间有顺序，但服从调剂发生在同一个院校专业组内的其他可调剂专业范围。
5. 2026 招生计划明细底座按湖北本科普通批首选物理在鄂招生计划全量保留；复核和排序可以分优先级推进，但公开明细不只保留 20 个候选。

## 三、我们当前处于哪一步

当前处于：

```text
2026 招生计划全量 OCR 明细底座已生成，候选V2逐专业明细复核种子、全量质量分层队列、逐专业明细质量工作台、全量逐专业字段保真总账、全量逐专业核验批次表、优先整组逐专业核验包、优先逐专业证据执行工作台、全量逐专业证据执行工作台、全量逐专业证据闭环任务队列、P0 证据执行包、P0 逐专业复核工作清单、字段缺口逐专业修复矩阵、湖北官方系统逐专业核验包、B0/B1 逐专业官网差异账、统一逐专业底座发布表、底座闭环逐专业明细执行主表、专业行原页证据锚点表、逐专业闭环缺口看板、底座机器审计表、候选V2证据总账、240 页公开页级 manifest、按页保真复核队列、家庭底线筛选表、候选V3复核入口索引、候选V3全量逐专业招生明细主表、候选V3全量逐专业复核队列、D0 原页核验工作台、D0 原页 OCR 证据表、B0/B1 原页核验包、B0/B1 逐专业招生明细主表/官方交叉校验工作台、候选V3全量逐专业字段保真总账、逐专业源证据风险侧账、字段事实闭环总账、字段事实核验任务队列、全量字段页列核验队列、页列底座综合风险登记表、页列底座核验批次表、P0 字段原页重读工作清单、P0 字段机器坐标候选表、P0 字段闭环推进工作台、P0 字段语义与多源线索审计表、P0 字段三方核验执行工作台、P0 字段即时复核包、P0 即时字段确认公开账本、P0 即时按页核页包、P0 即时页列核页执行队列和 P0 即时页列执行进度公开账本已生成
```

新增 P0 即时页列核页执行队列：`data/working/issue19-p0-immediate-page-execution-queue.csv` 把 148 个 `PDF页码×版面列` 包按候选冲突、无稳定候选、候选一致待官方闭环和常规人工确认重新排序，覆盖同一批 319 条字段任务。该队列只服务于 PDF 原页和湖北官方核验顺序，不保存候选读数、OCR 行文本、图片路径或最终建议。

新增全量字段页列核验队列：`data/working/issue19-field-fact-page-side-verification-queue.csv` 把 41208 条字段事实核验任务聚合为 462 个 `PDF页码×版面列` 执行单元，覆盖 231 个招生计划明细页和全部 13736 条专业明细。它是全量底座保真的页列层入口，当前 450 个页列为 V0 无候选阻断页列先核、12 个为 V1 有候选待人工核验页列，全部仍需要 PDF 原页和湖北官方侧核验。

新增页列底座综合风险登记表：`data/working/issue19-page-side-foundation-risk-register.csv` 继续保持 462 个 `PDF页码×版面列` 执行单元，把全量字段页列队列、单一逐专业招生明细总工作台、结构保真登记、结构风险、版面连续性、专业代号顺序、湖北官方查询键碰撞、教育部未匹配校名、B0/B1 官网差异、决策闸门和源证据风险侧账汇总到同一页列。当前 460 个页列为 Z0、2 个页列为 Z1；该表用于决定人工核页先后和避免结构/字段/官方消歧割裂，不保存学校专业明细或字段候选值，也不进入推荐或排序。

新增页列底座核验批次表：`data/working/issue19-page-side-foundation-verification-batches.csv` 把上述 462 个页列按风险顺序切成 19 个可执行批次，前 18 批各 25 个页列、最后 1 批 12 个页列。它用于把“全量底座做准”拆成可追踪的逐批核页任务：每批先核 PDF 原页、湖北官方系统或省招办计划、必要高校官网/章程辅证、结构归属和官方查询键消歧；全部批次当前仍为 R0，字段写回、下一阶段、志愿推荐和学校专业建议均为 0。

新增 P0 即时页列执行进度公开账本：`data/working/issue19-p0-immediate-page-execution-progress-public-ledger.csv` 把 148 个 P0 即时页列执行包接到私有字段确认工作台，只公开完成计数、状态分布、任务集合 SHA 和非最终门禁。当前 148 个页列包全部 R0，319 条 PDF 原页记录、319 条湖北官方侧记录、75 条高校辅证记录、290 条双人复核均未完成；这说明“任务已排好”，但“字段事实尚未核准”。

截至 2026-06-27，当前最重要的新增执行入口是 `data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv`、`data/working/issue19-p0-immediate-page-review-packets.csv`、`data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv`、`data/working/issue19-field-fact-p0-immediate-review-packet.csv`、`data/working/issue19-field-fact-p0-triage-execution-workbench.csv`、`data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv`、`data/working/issue19-field-fact-p0-closure-action-workbench.csv`、`data/working/issue19-field-fact-p0-reread-machine-candidates.csv`、`data/working/issue19-field-fact-p0-reread-worklist.csv`、`data/working/issue19-field-fact-verification-tasks.csv`、`data/working/issue19-field-fact-closure-ledger.csv`、`data/working/issue19-foundation-stabilization-major-detail-tasks.csv` 和 `data/working/issue19-major-source-evidence-risk-sidecar.csv`。字段事实闭环总账覆盖全部 13736 条招生专业明细，逐行标出再选科目、专业计划数、学费三项关键字段的 K0/K1/K2 状态：字段候选任务 19065 条、非空候选 7621 条，PDF 原页和湖北官方字段核验仍全部待核。字段事实核验任务队列进一步把这 13736 条明细拆成 41208 条逐字段任务：K0 无候选原页重读 11444 条、K1 有候选待核 7621 条、K2 OCR 候选待三方闭环 22143 条，并全部回连页级保真队列。P0 字段原页重读工作清单把 11444 条 K0 无候选任务单独排成执行清单，覆盖 8536 条招生专业明细、231 个 PDF 明细页和 967 所学校，当前先按专业计划数 5739 条、再选科目 4674 条、学费 1031 条回看原页。P0 字段机器坐标候选表进一步在这 11444 条任务上生成 4840 条非空坐标候选，其中专业计划数 2175 条、再选科目 1994 条、学费 671 条；6386 条仍无候选，218 条多值冲突。P0 字段闭环推进工作台把这些任务分成 A1/A1R 快速候选核页 4840 条、A2 多值冲突核页 218 条、A3 无候选重读 6386 条，并预留 PDF 人工读数、湖北官方字段值、高校官网或章程字段值和三方一致性状态；当前确认计数均为 0，只安排核验动作，不写回字段、不进入推荐或排序。P0 字段语义与多源线索审计表继续保持 11444 条字段任务，标出语义异常 15 条、计划数偏大需重点核页 11 条、高校字段线索 75 条，其中机器候选与高校辅证一致 22 条、冲突 1 条、官网有规范字段但机器无候选 52 条；它只用于重新安排核页优先级。P0 字段三方核验执行工作台把同一批字段任务排成稳定执行顺序：冲突异常立即核页 16 条、计划数偏大重点核页 11 条、高校辅证线索三方核验 74 条、多值坐标冲突核页 218 条、常规机器候选核页 4791 条、无候选原页重读 6334 条，其中 245 条要求双人复核；它只做派单和证据回链，所有字段写回和推荐门禁仍为 0。P0 字段即时复核包再从该工作台严格切出 `EXEC-01/02/03/04` 共 319 条最高优先级任务，覆盖 319 条招生专业明细、114 个 PDF 页、202 个院校代码和 222 个执行包，只用于优先核字段；P0 即时字段确认公开账本再把同一批任务转成私有人工记录状态机，当前 319 条 PDF 原页和湖北官方私有记录均待完成、75 条需高校辅证私有记录、290 条需双人复核，字段写回评估可进入数为 0；P0 即时按页核页包把这 319 条任务按 `PDF页码×版面列` 聚合成 148 个执行包，覆盖 114 页，公开层只保存证据编号、SHA、bbox、状态和门禁，私有 HTML/CSV 用于人工逐页逐列核 PDF 原件；P0 即时 PDF 原页读数候选公开审计把同一批 319 条任务上的私有候选降格为公开状态，当前 253 条有私有候选线索、66 条无稳定候选需人工看图、99 条需直接图像复核、290 条需双人复核，所有候选都不得自动写入人工读数。稳定化任务表把底座稳定性总看板中的 B0/B1/B2 共 12995 条招生专业明细全部拆成逐专业稳定化任务；源证据风险侧账覆盖全部 13736 条招生专业明细，把源证据覆盖结论、R2/R3/R4 风险、起始行 QC、窗口哈希、底座稳定性、闭环缺口和 P0 复核任务下沉到同一条 `专业行ID`。这些表全部保持 `最终可用=false`、`可进入下一阶段=false`、`是否允许作为志愿推荐依据=false`。同时新增两张原始数据保真审计表：`data/working/issue19-raw-major-lineage-consistency-audit.csv` 把 13736 条原始 OCR 专业行逐行回连到质量工作台、统一底座、总工作台、结构保真、稳定性看板、PDF 原页锚点、三年投档旁挂和闭环缺口看板，确认全链路核心字段漂移为 0；`data/working/issue19-raw-major-source-evidence-audit.csv` 进一步按 `来源页码+版面列+专业起始行号` 把 13736 条专业明细全部回连到私有 OCR 起始行、页级 manifest、私有窗口 JSONL 和公开锚点，起始行哈希、窗口哈希和页级 manifest 均满匹配。官方公开入口状态快照为 `data/working/issue19-official-public-entry-status.json`：湖北教育考试网 2026 计划页在 2026-06-27 公开 HTTP 复核可访问，但正文仍含“持续更新中/敬请期待”；湖北招生数智平台无登录探针仍返回 401。

已经完成：

- 固定个人基线：湖北 2026 普通类首选物理，总分 515，累计位次 91723，位次区间 90895-91723。
- 建立 2023/2024/2025 三年历史投档数据参照。
- 形成第一版 20 条可讨论候选池，但全部仍是待核验状态。
- 明确家庭底线：公办、正常学费、不学医和护理，专业优先级暂定为数字媒体技术、计算机类、师范类。
- 获取并 OCR 处理《湖北招生考试》2026 年第 19 期 PDF。
- 对第 19 期做了 20 校样本定位和 7 校高优先级 double check。
- 第一批 4 校已经生成 OCR 初稿：武汉科技大学、湖北大学、湖北理工学院、武汉商学院，共 44 个院校专业组、220 条专业行。
- 第 19 期全量 OCR 招生明细底座初稿已生成，覆盖 1103 所院校、3329 个院校专业组、13736 条专业行。
- 第一版 20 条历史候选中，17 条已在全量 OCR 初稿中命中，3 条需要核对组号变化、OCR 漏识别或历史组调整。
- 已生成 20 条历史候选的候选组级复核工作台：`data/working/issue19-candidate-plan-review-summary.csv`。
- 已生成已命中候选组内专业明细：`data/working/issue19-candidate-plan-review-major-detail.csv`，共 77 条专业行。
- 已生成全量偏好专业检索队列：`data/working/issue19-preference-major-search.csv`，共 2499 条专业行。
- 已生成全量硬风险专业组队列：`data/working/issue19-hard-risk-group-review-queue.csv`，共 2962 个专业组。
- 已生成候选池页面复核包公开元数据：`data/working/issue19-candidate-review-page-packet.csv` 和 `data/working/issue19-candidate-review-group-page-map.csv`，覆盖 10 个需要回看的第 19 期 PDF 页。
- 已生成完整性审计队列：`data/working/issue19-candidate-page-code-audit.csv` 和 `data/working/issue19-ocr-structure-anomaly-queue.csv`，用于发现漏拆、串校、串组、页眉串入、数字错位和低置信度问题。
- 已生成候选 V2 逐专业明细复核种子：23 个专业组、82 条专业明细；其中 `C10704` 为页图可见但结构化漏拆补种，`K15114` 为成都理工同校偏好专业补充组，`K15123` 仍是 0 条明细的历史组号待核问题。
- 已生成候选 V2 升级工作台：23 个专业组、82 条专业明细，全部保持 `pending_verification`，用于逐项补齐原页、官方系统、章程、家庭接受度、调剂结论和三年投档稳定性证据。
- 已生成全量专业组质量分层和复核队列：3329 条专业组行、13736 条专业明细参与校验，3300 条进入复核队列，其中 3295 条为 P0；3 个规范化专业组代码重复、共 6 行，已显式标记，不做去重。
- 已生成全量逐专业明细质量工作台：13736 条专业行全部保留并生成唯一 `专业行ID`，5129 条结构异常全部匹配到专业行，13705 条进入逐专业复核队列，其中 13700 条为 P0。
- 已生成全量逐专业字段保真总账：`data/working/issue19-full-major-field-fidelity-ledger.csv` 覆盖 13736 条招生专业行，其中 13486 条为高风险保真行、250 条暂未触发机器高风险；总账把逐专业质量、家庭底线、组内调剂风险、字段完整性和结构异常合并到一行一专业证据视图，所有行仍 `最终可用=false`。
- 已生成全量逐专业核验批次表：`data/working/issue19-full-major-verification-batches.csv` 覆盖 13736 条招生专业行，把全量总账与页级保真队列合并成 A0-A9 执行批次；A0 阻断级结构先核 3998 行，A2 偏好专业逐专业先核 1672 行，A5 计划数字段先核 3248 行，全部仍 `最终可用=false`。
- 已生成优先整组逐专业核验包：`data/working/issue19-priority-group-major-review-pack.csv` 覆盖 1043 个优先专业组内的 7537 条招生专业明细；一行一个专业，专业组字段只作为调剂上下文，避免只核偏好专业或 6 个拟填专业而漏掉同组不可接受专业。
- 已生成优先逐专业证据执行工作台：`data/working/issue19-priority-major-evidence-workbench.csv` 覆盖同一批 7537 条招生专业明细；E0 PDF 原页/组边界阻断 1362 行，E1 历史候选/样本三方证据 450 行，E2 数字媒体技术三方证据 405 行。下一步优先按 E0/E1/E2 核 PDF 原页、湖北官方系统、高校官网/章程、家庭接受度、调剂结论和三年投档稳定性。
- 已生成全量逐专业证据执行工作台：`data/working/issue19-full-major-evidence-workbench.csv` 覆盖第 19 期全部 13736 条招生专业明细，其中 7537 条来自优先整组包、6199 条为非优先包但仍保留在同一张逐专业执行视图；非优先包按 F0-F4 继续推进 PDF 原页、官网辅证、计划/学费/选科补证、家庭底线和调剂风险核验。全部仍 `最终可用=false`、`是否可进入最终专业列表=false`、`可进入下一阶段=false`。
- 已生成全量逐专业证据闭环任务队列：`data/working/issue19-full-major-evidence-closure-tasks.csv` 覆盖 13736 条招生专业明细并拆成 94935 条证据任务；其中 82416 条为 6 类基础证据任务，12473 条为字段完整性补证任务，46 条为 B0/B1 官网冲突或未匹配复核任务。任务队列只安排执行，不生成最终方案。
- 已生成 P0 证据执行包：`data/working/issue19-p0-evidence-execution-packets.csv` 严格抽取闭环任务队列中的 6619 条 P0 任务，覆盖 5310 条招生专业明细、2282 个执行包、231 个 PDF 页和 1056 所学校；P0A PDF 原页结构阻断 4047 条、P0B 三方证据闭环 2526 条、P0C B0/B1 差异复核 46 条。执行包只用于把今晚优先任务按页/学校/类型组织起来，不改变逐专业明细粒度。
- 已生成 P0 逐专业复核工作清单：`data/working/issue19-p0-evidence-review-worklist.csv` 覆盖同一批 6619 条 P0 任务；每行仍对应一个招生专业明细和一个 P0 证据项，同时带出页图/OCR 文本证据编号与 SHA、全量证据工作台字段、页级风险和人工核验闸口。该表是今晚人工核验的逐专业执行清单，不是最终志愿表。
- 已生成字段缺口逐专业修复矩阵：`data/working/issue19-p1-field-gap-evidence-repair-matrix.csv` 共 19065 行，把再选科目、专业计划数、学费缺口逐字段拆开，避免一个专业多字段缺口被合并成粗任务。
- 已生成湖北官方系统逐专业核验包：`data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv` 覆盖全部 13736 条招生专业明细，每行预留官方系统证据编号、字段差异和公开原始行 SHA。
- 已生成 B0/B1 逐专业官网差异账：`data/working/issue19-b0-b1-public-official-diff-ledger.csv` 共 854 行，记录高校官网/API/PDF/图片辅证与 OCR 字段之间的匹配、冲突和缺口；该表不能替代湖北官方系统或省招办计划。
- 已生成第 19 期招生计划底座审计表：9 类机器阻断检查全部通过，0 个自动阻断项；8 类人工复核风险被保留，包括 1838 条唯一组码回退归属、31 个专业组内 116 条专业代号重复行、候选池 3 条未命中和字段/学费/选科等 OCR 风险。
- 已生成候选 V2 逐字段复核总账和三方证据矩阵：23 个候选/补充专业组、82 条专业明细拆成 840 个字段任务，其中 494 个为 P0；23 个专业组证据矩阵全部保持 `可进入最终候选=false`。
- 已生成第 19 期公开页级 manifest：覆盖 PDF 1-240 页，240 页均有页图哈希和 OCR 文本哈希；第 10-240 页共 231 页均有结构化专业组和专业明细记录。
- 已生成第 19 期按页保真复核队列：`data/working/issue19-page-fidelity-review-queue.csv` 覆盖第 10-240 页 231 个招生计划明细页，汇总 13736 条逐专业明细和 3329 个专业组的页级风险；该表只排核页顺序，候选讨论仍必须回到逐专业明细总账。
- 已生成第 19 期家庭底线筛选表：覆盖 3329 个院校专业组和 13736 条专业明细；其中 590 个专业组为“有偏好专业且未触发自动阻断”的优先复核对象，1467 个专业组因医学护理或高收费/超预算默认不进主方案，801 个专业组可进入人工调剂接受度判断；按标签拆分后，含数字媒体技术的专业组 78 个、计算机类相关 1032 个、师范类相关 391 个。
- 已生成候选 V3 复核入口表：1327 个院校专业组，每行都带完整组内招生明细、页码证据编号、页图/OCR 哈希、家庭筛选初判、候选批次、历史同组投档线线索和升级缺口；其中 23 行使用候选 V2 逐专业明细，1304 行使用家庭底线全量 OCR 明细；全部保持 `候选闸门状态=pending_verification`、`最终可用=false`、`可进入最终候选=false`。
- 已生成候选 V3 全量逐专业招生明细主表：`data/working/issue19-candidate-v3-admission-detail.csv`，覆盖 1327 个入口专业组并展开为 8412 行；其中 8410 条是真实招生专业，`K15123`、`C10702` 各保留 1 条 0 明细占位。后续 V3 候选讨论默认使用这张逐专业主表；`issue19-candidate-v3-review-intake.csv` 只作为院校专业组索引、历史线索和调剂范围承载。
- 已生成候选 V3 全量逐专业复核队列：`data/working/issue19-candidate-v3-admission-detail-review-queue.csv`，覆盖同一批 8412 行；其中 8410 条真实招生专业全部预留 PDF 原页、湖北官方系统、高校官网/章程、院校名称、专业组边界、专业字段、校区、特殊限制、家庭接受度和调剂影响核验字段，2 条 0 明细占位只用于补齐专业组明细，不能进入专业接受度或最终排序。
- 已生成 D0 原页核验工作台：`data/working/issue19-candidate-v3-d0-resolution-workbench.csv`，覆盖 58 条 D0 任务和 17 个专业组；其中 55 条院校名疑似截断任务可从专业组标题 OCR 提取完整院校名建议，5 条存在代码冲突或 F/O/P/0 字符混淆，2 条 0 明细占位仍需确认 2026 组号是否变化或取消。该表不自动写回主表。
- 已生成 D0 原页 OCR 证据表：`data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv`，按 17 个专业组聚合；13 个组为标题行精确命中，`P01202/F01203` 为 `0/O` 规范化命中，`C10702/K15123` 在原页 OCR 和结构化组表均未命中并保持 0 明细阻断。该表只作核页证据索引。
- 候选 V3 批次分布：B0 历史候选和组号问题优先核页 20 个，B1 数字媒体技术优先核页 29 个，B2 偏好专业未自动阻断核页 763 个，B3 偏好专业硬风险先核风险 514 个，B4 同页边界风险组核页 1 个。
- 已生成候选 V3 B0/B1 原页核验包：覆盖 49 个优先专业组和 324 个逐专业核验任务，涉及 32 个第 19 期 PDF 页；其中 B0 20 个组、B1 29 个组，0 明细占位任务仅限 `C10702` 和 `K15123`。
- B0/B1 逐专业核验包不从 `组内招生明细` 长文本切分，而是回到结构化来源：81 条来自候选 V2 逐专业种子，241 条来自家庭底线逐专业表，2 条为 0 明细占位任务。
- 已生成 B0/B1 官方交叉校验工作台：学校官方来源队列覆盖 36 所学校，组级索引覆盖 49 个专业组，逐专业招生明细主表覆盖 324 个专业任务；后续候选讨论默认使用 `data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv`，组级表只作投档、调剂、历史线和补源索引，不作为候选讨论主表。
- 已补充 B0/B1 官网/API/PDF/图片交叉核验源：7 所学校为可复用高校官网湖北计划源，16 所为部分可核线索，8 所仍需继续补官网计划或章程来源，5 所目前只有章程/规则或不可用计划线索。
- 已生成 `data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv`：覆盖 324 条逐专业招生明细，已标准化留存官网/API/HTML/XLSX/PDF/图片/双表联合抽取证据 434 条；当前 152 条专业名匹配，61 条计划数与 OCR 一致，55 条为 OCR 缺失但官网可补，18 条计划数存在差异。山东工商学院 PDF 已以渲染图 OCR 专业名 + PDF 网格数字列双通道抽取 24 条湖北物理类明细，并保留 42 行审计表。
- 已生成 B0/B1 保真复核队列：18 条计划数冲突、32 条专业未匹配、19 所学校补源缺口；其中 8 所是 P0 待补官方计划源，11 所是已有官网线索但尚未结构化到逐专业证据；“面向武汉、实验班、英才班、中外合作”等关键限定词未被官网证据覆盖时，不用泛化专业计划数替代；高校官网省份总计划未拆首选物理/历史时，不硬比物理类计划数；OCR 专业名疑似串入下一院校时直接降级为未匹配待核。
- 已生成候选 V3 全量逐专业字段保真总账：`data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv` 覆盖 8412 条招生明细，其中 8234 条为高风险保真行、178 条暂未触发机器高风险；总账把 D0 原页风险、B0/B1 18 条计划数冲突、32 条官网未匹配、字段完整性、结构异常、费用底线、家庭底线和调剂风险全部落到逐专业明细行上，所有行仍保持 `最终可用=false`。
- 已生成底座闭环逐专业明细执行主表：`data/working/issue19-foundation-closure-major-batches.csv` 覆盖第 19 期全部 13736 条招生专业明细，一行一个专业；C0-P0证据闭环先核 5310 行、C1-字段缺口先补 7608 行、C2 官网辅证主批次 0 行、C3-常规三方证据闭环 609 行、C4-低风险抽检但非最终 209 行，`最终可用=0`。C2 主批次为 0 是因为 854 条含官网辅证任务的专业明细已被 C0/C1 更高优先级覆盖，B0/B1 官网差异任务仍为 854 条。配套页级索引 231 行、学校索引 1100 行只用于核页顺序和补源入口，不替代逐专业主表。
- 已生成字段缺口候选修复线索表：`data/working/issue19-field-gap-repair-candidates.csv` 覆盖 19065 个字段缺口任务，其中 7621 条有非空候选线索；候选来源包括组级 OCR 上下文 6782 条、当前 OCR 单元格 817 条、高校官网辅证 22 条。所有候选均 `候选可自动写回主表=false`，只能安排原页和官方系统核验。
- 已生成 B0/B1 官网证据逐专业旁挂表：`data/working/issue19-b0-b1-official-evidence-by-major-line.csv` 覆盖 854 条已有官网线索的专业明细，其中 61 条 strong_support、55 条 fill_candidate、18 条 conflict_review；另有 `issue19-b0-b1-official-plan-fill-candidates.csv` 和 `issue19-b0-b1-official-conflict-review.csv` 用于直接下钻计划数补缺候选和冲突核页。所有行 `能否替代湖北官方计划=false`。
- 已生成专业行原页证据锚点表：`data/working/issue19-major-line-pdf-evidence-anchors.csv` 覆盖全部 13736 条专业明细，全部精确回连专业起始 OCR 行；12596 条已生成专业行级 OCR 锚点，1127 条缺少组标题上下文，13 条专业窗口需重点回看。公开表只保存行号范围、坐标摘要和哈希，OCR 窗口原文仅留在 `private/`。
- 已生成原始专业行源证据审计表：`data/working/issue19-raw-major-source-evidence-audit.csv` 覆盖全部 13736 条专业明细，全部按 `来源页码+版面列+专业起始行号` 精确回连私有 OCR 起始行，并与页级 manifest、公开原页锚点、私有窗口 JSONL、原始血缘审计表闭合；S0 源证据满回连 13736 条，但 R2/R3 仍有 13118 条需要优先或阻断级人工核页，R4 未触发起始行 QC 风险 618 条。
- 已生成逐专业源证据风险侧账：`data/working/issue19-major-source-evidence-risk-sidecar.csv` 覆盖全部 13736 条专业明细，一行一个招生专业；把源证据审计的 R2/R3/R4 风险和底座稳定性、闭环缺口、P0 复核任务合并到同一行。当前 X1 专业窗口 P0 先核 13 条、X2 起始行 P0_QC 先核 6086 条、X3 源证据优先复核 7019 条、X4 低风险抽检 618 条；源证据优先核页合计 13118 条。
- 已生成逐专业闭环缺口看板：`data/working/issue19-foundation-closure-gap-scorecard.csv` 覆盖全部 13736 条专业明细，把 C0-C4、字段候选、B0/B1 官网旁证、原页锚点、家庭/调剂/湖北官方门禁合并成 S0-S8 执行动作桶；其中 S0 冲突优先 18 条、S1 P0+官网辅证 116 条、S2 P0 原页 5176 条、S3 字段有候选 4248 条、S4 字段无候选 3360 条。
- 已生成逐专业三年投档线索旁挂表：`data/working/issue19-major-line-historical-toudang-sidecar.csv` 覆盖全部 13736 条专业明细；同代码 3 年命中 5836 条、2 年命中 3946 条、1 年命中 1940 条、0 年命中 2014 条。该表只作后续冲稳保筛选前置线索，不能替代 2026 招生计划核验。
- 已生成单一逐专业招生明细总工作台：`data/working/issue19-admission-detail-master-workbench.csv` 覆盖全部 13736 条专业明细；一行一个招生专业，把统一底座、闭环缺口看板、PDF 原页锚点和三年投档线索合并到同一行。后续新增城市、学校或专业方向时默认先看这张表；学校、专业组、页码只作索引和调剂上下文。
- 已生成逐专业结构保真登记和风险事件派单表：`data/working/issue19-admission-detail-structural-fidelity-register.csv` 覆盖全部 13736 条专业明细，`data/working/issue19-structural-risk-major-line-ledger.csv` 拆出 3108 条结构风险事件；其中唯一组码回退归属 1838 条、组内专业代号重复 116 条、重复组码 14 条、原页窗口 P0 13 条、原页窗口 P1 1127 条。另有 `data/working/issue19-zero-detail-group-placeholder-workbench.csv` 保留 40 个无明细组占位。
- 已生成逐专业候选筛选准备表：`data/working/issue19-candidate-filter-prep-major-detail.csv` 覆盖全部 13736 条专业明细；城市偏好关键词命中 1723 条、学费超预算机器线索 1862 条、学费字段待核 1262 条、办学属性待核 13736 条。该表只用于机器预筛和核验排序，不生成候选方案。
- 已生成逐专业决策闸门表：`data/working/issue19-major-decision-readiness-gates.csv` 覆盖全部 13736 条专业明细；G0 结构或归属未闭环 4459 条、G1 家庭底线风险 2342 条、G2 字段缺口 6218 条、G3 可作机器预筛线索但不可定案 350 条、G4 常规留存 367 条。所有行仍需 PDF 原页、湖北官方系统、办学属性、家庭接受度和同组调剂闭环。
- 已生成教育部学校属性逐专业核验表：`data/working/issue19-moe-school-attribute-major-detail.csv` 覆盖全部 13736 条专业明细；教育部精确匹配 13161 条，父校/校区/医学部等保守匹配 190 条，未匹配待核 385 条、涉及 49 个院校代码+校名。民办线索 2230 条、合作办学线索 34 条、职业本科名称线索 241 条已下沉到逐专业行；这些只是学校登记信息和风险线索，不能替代 2026 湖北招生计划、招生章程和实际校区核验。
- 已生成湖北官方查询键碰撞清单：`data/working/issue19-hubei-official-query-key-collision-ledger.csv` 覆盖 59 个非唯一官方查询三元组、118 条专业明细；后续官方系统回填不得只按院校代码、专业组代码和专业代号合并。
- 已生成逐专业版面连续性和专业代号顺序风险侧账：`data/working/issue19-major-line-layout-continuity-risk-ledger.csv` 拆出 1934 条版面风险事件，`data/working/issue19-major-code-order-risk-ledger.csv` 拆出 355 条专业代号顺序风险事件；两张表只安排核页和消歧，不自动修正 OCR，也不产生候选结论。
- 优先专业队列已经合并本专业行风险和所在专业组风险；`机器初判`、`综合风险等级` 只用于安排复核，不是最终报考建议。

尚未完成：

- 全量 OCR 初稿还没有完成分层人工复核。
- 组内全部专业、计划数、学费、选科、备注还没有逐字段确认。
- 还没有把每条招生专业按家庭偏好标成“可接受、勉强接受、不能接受”，也还没有形成对应专业组的调剂结论。
- 还没有形成可进入最终志愿表的逐专业明细或对应院校专业组。
- 还没有把全量质量队列中的 P0 项逐页人工确认。
- B0/B1 官方交叉校验工作台尚未完成闭环确认；当前官网来源状态和官网证据匹配只是补源线索，不能理解为“官方核验已完成”。
- 全量逐专业字段保真总账仍是复核工作台，不是最终志愿表；`P6-暂未触发机器高风险` 也必须完成 PDF 原页、湖北官方系统、高校官网/章程、家庭接受度和调剂结论闭环后才能升级。

所以现在还不能给最终志愿方案；当前数据只能用于生成复核任务和缩小候选范围。

## 四、2026 招生计划数据底座怎么才算做准

2026 招生计划数据底座有两个层级，不能混在一起：

1. **原始数据准确结构化**：先把第 19 期招生专业明细逐条拆准、字段标准化、主键稳定、证据可回溯。这是当前阶段的“底座坐稳”。
2. **可用于志愿决策**：在原始数据准确结构化之后，再叠加湖北官方系统/省招办计划、高校官网/章程、家庭接受度、调剂结论和近三年投档稳定性闭环。

当前第一个层级已经新增十五个结构化保障点：`issue19-raw-major-lineage-consistency-audit.csv` 要求 13736 条 raw 专业行全部能回到下游主表，且核心 OCR 字段传递漂移为 0；`issue19-raw-major-source-evidence-audit.csv` 要求 13736 条专业明细全部能回到源头 OCR 起始行、页级 manifest、私有窗口 JSONL 和公开锚点，且哈希和页级计数一致；`issue19-field-fact-closure-ledger.csv` 要求每条专业明细的再选科目、专业计划数、学费都以 K0/K1/K2 状态明确缺口、候选和待核来源；`issue19-field-fact-verification-tasks.csv` 要求每条专业明细刚好拆成三项字段核验任务，并回连字段总账和页级保真队列；`issue19-field-fact-page-side-verification-queue.csv` 要求 41208 条字段任务全部能聚合到 462 个页列执行单元，且每个页列只公开计数、任务集合 SHA 和证据索引；`issue19-page-side-foundation-risk-register.csv` 要求同一批 462 个页列继续叠加结构、源证据、官方消歧、官网差异、决策闸门等风险，形成全量页列核验入口；`issue19-page-side-foundation-verification-batches.csv` 再把 462 个页列按风险顺序切成 19 个批次，方便逐批核页和记录完成度；`issue19-field-fact-p0-reread-worklist.csv` 要求 11444 条 K0 无候选字段全部回连到字段任务、源证据审计、PDF 锚点和页级保真队列；`issue19-field-fact-p0-reread-machine-candidates.csv` 在这些 K0 字段中生成 4840 条机器坐标候选和 6604 条仍需重读或冲突核页任务，只作为人工核页入口，不允许自动写回；`issue19-field-fact-p0-closure-action-workbench.csv` 再把同一批任务拆成 PDF 原页、湖北官方系统或省招办计划、高校官网或章程三方闭环动作，所有人工和官方确认字段仍为空；`issue19-field-fact-p0-semantic-crosssource-audit.csv` 在同一任务集合上标出语义异常、计划数偏大、官网补缺线索和机器/高校辅证冲突，防止明显 OCR 噪声进入普通核页队列；`issue19-field-fact-p0-immediate-review-packet.csv` 从三方核验执行工作台中严格切出 319 条最高优先级字段任务，方便先核最可能影响字段事实的冲突和异常；`issue19-p0-immediate-page-review-packets.csv` 再把这 319 条任务按 148 个 `PDF页码×版面列` 包组织，方便人工回看原件并避免左右列串读；`issue19-p0-immediate-pdf-reading-candidate-public-audit.csv` 再把私有 OCR 候选降格为公开候选状态和人工审阅桶，253 条有候选、66 条无稳定候选、99 条需直接图像复核、290 条需双人复核，但自动写入人工读数和字段写回仍均为 0；`issue19-p0-immediate-page-execution-progress-public-ledger.csv` 再把 148 个页列包的私有核验完成度公开成计数和状态，当前全部 R0，防止误把排队完成当成字段核准。第二个层级尚未完成，所以仍不能输出最终志愿方案。

配套的 `issue19-p0-immediate-page-execution-queue.csv` 不增加字段事实，只把 148 个页列包按 Q0/Q1/Q2/Q3 排成执行顺序，其中 Q0 候选冲突 11 个页列包、Q1 无稳定候选 34 个页列包、Q2 候选一致仍需官方闭环 11 个页列包、Q3 常规候选 92 个页列包；它覆盖同一批 319 条字段任务，继续保持字段写回、推荐依据和最终可用均为 0。

一个招生专业及其所在院校专业组只有同时完成以下核验，才算“可用于志愿决策”：

| 核验项 | 要求 |
| --- | --- |
| 省招办计划 | 回看第 19 期 PDF 原页或湖北官方平台，确认院校代码、专业组代码、组内全部招生专业 |
| 字段核对 | 确认专业代号、专业名称、计划数、学费、学制、校区、选科、备注 |
| 官网交叉校验 | 使用高校官网或招生章程核对专业、学费、选科、校区、特殊限制 |
| 家庭接受度 | 标记每条招生专业为可接受、勉强接受、不能接受 |
| 调剂判断 | 判断如果服从调剂，是否可能进入不能接受专业 |
| 历史稳定性 | 对比 2023/2024/2025 投档线、位次、计划变化和波动 |
| 风险标签 | 标记医学/护理、高收费、中外合作、体检、语种、单科、小计划等风险 |

做到这个程度后，才可以进入冲稳保排序。

## 五、下一步具体做什么

下一步是在全量底座上做逐字段保真复核：先处理 P0/K0 无候选字段和原页结构问题，再处理 K1 有候选待核字段，最后处理 K2 OCR 齐全但尚未三方闭环的字段。目标院校、目标专业和城市偏好仍然可以继续调整；新增方向只改变筛选和补证优先级，不改变原始数据底座。

当前优先从 `data/working/issue19-p0-immediate-page-execution-queue.csv` 安排人工核页顺序：先核 Q0 候选冲突页列，再核 Q1 无稳定候选页列，再核 Q2 候选一致但仍需官方闭环页列，最后核 Q3 常规候选页列。这个入口只负责把原始数据核准工作排得更稳，不代表目标学校或专业已经确定。

全量推进时同步看 `data/working/issue19-field-fact-page-side-verification-queue.csv`：它覆盖全部 41208 条字段任务，可以避免我们只盯着 P0 即时 319 条而漏掉后续城市、学校或专业方向需要的全量字段核验。P0 现场进度则看 `data/working/issue19-p0-immediate-page-execution-progress-public-ledger.csv`，只有当 PDF 原页记录、湖北官方侧记录、必要高校辅证、双人复核和字段确认记录逐步完成后，才允许把对应字段推进到下一层。

实际操作时，新增城市、学校或专业方向先从 `data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv`、`data/working/issue19-p0-immediate-page-review-packets.csv`、`data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv`、`data/working/issue19-field-fact-p0-immediate-review-packet.csv`、`data/working/issue19-field-fact-p0-triage-execution-workbench.csv`、`data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv`、`data/working/issue19-field-fact-p0-closure-action-workbench.csv`、`data/working/issue19-field-fact-p0-reread-machine-candidates.csv`、`data/working/issue19-field-fact-p0-reread-worklist.csv`、`data/working/issue19-field-fact-verification-tasks.csv`、`data/working/issue19-field-fact-closure-ledger.csv`、`data/working/issue19-major-source-evidence-risk-sidecar.csv`、`data/working/issue19-foundation-stabilization-major-detail-tasks.csv`、`data/working/issue19-candidate-filter-prep-major-detail.csv`、`data/working/issue19-moe-school-attribute-major-detail.csv` 和 `data/working/issue19-admission-detail-master-workbench.csv` 查；是否能进入候选讨论先看 `data/working/issue19-major-decision-readiness-gates.csv` 的阻断闸门。学校属性、公办民办、合作办学、职业本科和未匹配校名先看教育部学校属性表，但它只给登记信息线索，不能替代湖北官方计划和招生章程。结构风险看 `data/working/issue19-structural-risk-major-line-ledger.csv`、`data/working/issue19-major-line-layout-continuity-risk-ledger.csv`、`data/working/issue19-major-code-order-risk-ledger.csv` 和 `data/working/issue19-zero-detail-group-placeholder-workbench.csv`；官方系统回填消歧看 `data/working/issue19-hubei-official-query-key-collision-ledger.csv`。安排核验顺序时，以 P0 即时 PDF 原页读数候选公开审计、P0 即时按页核页包、P0 即时字段确认公开账本、P0 字段即时复核包、P0 字段三方核验执行工作台、P0 字段语义与多源线索审计表、P0 字段闭环推进工作台、P0 字段机器坐标候选表、P0 字段原页重读清单、字段事实核验任务队列、字段事实闭环总账、源证据风险侧账、逐专业稳定化任务表和逐专业闭环缺口看板作为当前入口，再下钻到 P0/P1、官方平台、官网辅证和专业行原页证据锚点。
执行上先按 `data/working/issue19-field-fact-p0-reread-machine-candidates.csv` 的坐标候选状态、`data/working/issue19-field-fact-p0-reread-worklist.csv` 的 P0 原页重读优先序、`data/working/issue19-field-fact-verification-tasks.csv` 的 P0/P1/P3 字段任务、`data/working/issue19-field-fact-closure-ledger.csv` 的字段事实阻断等级和 `data/working/issue19-foundation-closure-gap-scorecard.csv` 的 S0-S8 动作桶推进：先处理 K0/Q0 无候选缺口、L0/L1 多字段缺口和 S0/S2 原页结构问题，再处理 K1/Q1 有候选待核和 S3/S4 字段补证，最后对 K2/Q2 OCR 齐全行做 PDF 原页与湖北官方系统闭环。下钻时仍保留 C0/C1/C3/C4 主批次：C0 下钻 `data/working/issue19-p0-evidence-review-worklist.csv`，C1 下钻 `data/working/issue19-field-gap-repair-candidates.csv`、`data/working/issue19-field-fact-closure-ledger.csv`、`data/working/issue19-field-fact-verification-tasks.csv`、`data/working/issue19-field-fact-p0-reread-machine-candidates.csv`、`data/working/issue19-field-fact-p0-reread-worklist.csv` 和 `data/working/issue19-p1-field-gap-evidence-repair-matrix.csv`，官方平台核验看 `data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv`，官网辅证差异看 `data/working/issue19-b0-b1-official-evidence-by-major-line.csv`、`data/working/issue19-b0-b1-official-plan-fill-candidates.csv` 和 `data/working/issue19-b0-b1-official-conflict-review.csv`，原页定位先看 `data/working/issue19-raw-major-source-evidence-audit.csv` 和 `data/working/issue19-major-line-pdf-evidence-anchors.csv`，三年投档参考看 `data/working/issue19-major-line-historical-toudang-sidecar.csv`。每一步都必须回链到 `专业行ID`、全量证据工作台和页级证据哈希，不能只按页级、学校级或执行包 ID 得出结论。

注意：

```text
命中不等于可报。
未命中不等于不存在。
机器初判不等于最终建议。
OCR 字段不等于最终事实。
```

### 第一步：候选池命中项和未命中项复核

对象：

- 第一版 20 条历史候选中已命中的 17 条。
- 未命中的 `C10702`、`C10704`、`K15123`。

动作：

- 对已命中项，回看第 19 期 PDF 原页确认专业组边界和组内全部专业。
- 对所有候选项，输出时必须使用逐专业招生明细主表；专业组只作为索引、投档线和调剂范围，不能只给学校/专业组两层结论。
- 对未命中项，先看 `issue19-candidate-page-code-audit.csv`：`C10704` 属于页面有组号但结构化漏拆，`C10702`、`K15123` 更偏 2026 组号变化、历史组取消或候选池历史 OCR 噪声。
- 优先打开候选池页面复核包的 10 页私有页图和页面 OCR 文本，先核候选专业组及同校相邻专业组。
- 同步使用 `issue19-full-quality-review-queue.csv`，优先处理 P0 中的候选池、偏好专业、硬风险、无专业明细、重复组码和行数不一致项。
- 同步使用 `issue19-full-major-detail-quality-workbench.csv` 和 `issue19-full-major-detail-review-queue.csv`，保证候选讨论时直接展开每条专业明细。
- 同步使用 `issue19-candidate-v3-admission-detail.csv`，保证 V3 候选讨论时一行对应一个招生专业或 0 明细占位。
- 同步使用 `issue19-candidate-v3-admission-detail-review-queue.csv`，按逐专业核验优先级处理 0 明细、疑似截断院校名、历史候选、数字媒体技术、偏好专业、硬风险专业、特殊限制和调剂接受度任务。
- D0 先使用 `issue19-candidate-v3-d0-resolution-workbench.csv`：核 `C10702/K15123` 是否仍存在，核 `湖北/湖南/上海/北京/山东` 等截断院校名的完整校名，尤其核 `P012/F012` 代码冲突。
- 同步查看 `issue19-ocr-structure-anomaly-queue.csv`，命中串校、串组、页眉串入、计划数/学费错位的专业行不得直接用于判断调剂可接受。
- 核对专业代号、专业名称、计划数、学费、选科、备注。
- 标记风险：医学/护理、高收费、中外合作、体检限制、语种/单科、小计划、学费超过 15000 元。
- 标记家庭接受度：可接受、勉强接受、不能接受。

产物：

```text
候选池 2026 计划复核表：
data/working/issue19-candidate-plan-review-summary.csv
data/working/issue19-candidate-plan-review-major-detail.csv
data/working/issue19-candidate-page-code-audit.csv
data/working/issue19-ocr-structure-anomaly-queue.csv
data/working/issue19-candidate-v2-group-review-seed.csv
data/working/issue19-candidate-v2-major-review-seed.csv
data/working/issue19-candidate-v2-verification-group-workbench.csv
data/working/issue19-candidate-v2-verification-major-workbench.csv
data/working/issue19-full-quality-group-tiers.csv
data/working/issue19-full-quality-review-queue.csv
data/working/issue19-full-major-detail-quality-workbench.csv
data/working/issue19-full-major-detail-review-queue.csv
data/working/issue19-foundation-audit-findings.csv
data/working/issue19-foundation-page-audit.csv
data/working/issue19-candidate-v2-field-review-ledger.csv
data/working/issue19-candidate-v2-triangulation-matrix.csv
data/working/issue19-page-manifest.csv
data/working/issue19-family-fit-group-screen.csv
data/working/issue19-family-fit-major-detail.csv
data/working/issue19-candidate-v3-review-intake.csv
data/working/issue19-candidate-v3-admission-detail.csv
data/working/issue19-candidate-v3-admission-detail-review-queue.csv
data/working/issue19-candidate-v3-d0-resolution-workbench.csv
data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv
data/working/issue19-candidate-v3-b0-b1-group-review-pack.csv
data/working/issue19-candidate-v3-b0-b1-major-review-pack.csv
data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv
data/working/issue19-candidate-v3-b0-b1-admission-detail-official-crosscheck.csv
data/working/issue19-candidate-v3-b0-b1-official-crosscheck-queue.csv
data/working/issue19-candidate-v3-b0-b1-major-official-crosscheck-queue.csv
```

该表的目的不是马上定志愿，而是先把最可能进入方案的院校专业组从全量 OCR 初稿提升到可讨论状态。
B0/B1 核验包和官方交叉校验工作台都是复核工具，不是可填报清单；后续候选讨论默认看逐专业招生明细表。全 V3 默认表是 `data/working/issue19-candidate-v3-admission-detail.csv`，全 V3 核验顺序看 `data/working/issue19-candidate-v3-admission-detail-review-queue.csv`，B0/B1 已补官网证据时默认表是 `data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv`。包内所有组和专业仍必须保持不可进入最终表，直到原页、官方系统、章程、家庭接受度和调剂结论全部补齐。

### 第二步：把 20 条候选池接入 2026 招生计划

对象：

- `data/working/candidate-pool-v1.csv` 中的 20 条候选。
- 必要时补充省内公办保底项和其他城市候选。

动作：

- 对每条历史候选找到 2026 对应院校专业组。
- 如果 2026 专业组代码、组内专业变化较大，不能机械沿用历史投档线。
- 如果 2026 已无该组或组内出现不可接受专业，移出主方案。

产物：

```text
候选池 V2：已接入 2026 招生计划
```

候选池 V2 必须新增或确认以下字段：

- PDF 原页人工核验状态。
- 湖北官方平台或志愿系统核验状态。
- 学校官网/章程核验状态。
- 组内每个专业的家庭接受度。
- 是否可服从调剂。
- 不可接受专业数量。
- 三年投档稳定性结论。

### 第三步：做专业和调剂判断

每个候选院校专业组都要回答：

- 主动填的 6 个专业分别是什么。
- 这些专业之间怎么排序。
- 除了这 6 个，组内还有哪些专业。
- 如果服从调剂，是否会被调到不能接受专业。
- 是否因为体检、单科、语种、学费、校区、专项资格等原因存在退档或不适合风险。

产物：

```text
专业组接受度表
```

### 第四步：冲稳保排序

排序依据：

- 2026 位次 91723。
- 2025/2024/2023 等位分和投档位次。
- 2026 计划人数和组内专业变化。
- 家庭偏好和底线。
- 调剂可接受性。

产物：

```text
冲稳保候选表
```

### 第五步：形成最终志愿方案

最终方案至少要包含：

- 45 个院校专业组排序。
- 每个院校专业组的 6 个专业排序。
- 是否服从调剂。
- 每项的冲稳保定位。
- 每项的复核状态和风险说明。
- 最终提交检查清单。

## 六、时间倒排

| 时间 | 目标 | 产物 |
| --- | --- | --- |
| 2026-06-27 | 完成全量 OCR 明细底座、候选复核工作台、偏好专业和硬风险队列、候选V2逐专业明细种子、升级工作台、全量质量分层、逐专业质量工作台、全量逐专业核验批次表、优先整组逐专业核验包、优先逐专业证据执行工作台、全量逐专业证据执行工作台、全量逐专业证据闭环任务队列、P0/P1逐专业复核与补证表、湖北官方逐专业核验包、B0/B1逐专业官网差异账、统一逐专业底座入口、底座闭环逐专业执行批次、底座机器审计、候选证据总账、页级 manifest、按页保真复核队列、家庭底线筛选表、候选V3复核入口索引、候选V3全量逐专业招生明细主表、候选V3全量逐专业复核队列、D0 原页核验工作台、D0 原页 OCR 证据表、B0/B1 原页核验包、B0/B1 逐专业招生明细主表、官方交叉校验工作台、山东工商学院 PDF 网格 OCR 抽取、逐专业证据合并表和保真复核队列；默认讨论入口收敛为逐专业招生明细表；启动重点组人工复核 | 全量 OCR 招生明细、候选池复核工作台、优先复核队列、候选V2逐专业明细、升级闸门表、质量分层队列、逐专业明细质量工作台、全量逐专业核验批次表、优先整组逐专业核验包、优先逐专业证据执行工作台、全量逐专业证据执行工作台、证据闭环任务队列、P0逐专业复核清单、字段缺口矩阵、湖北官方逐专业核验包、B0/B1逐专业官网差异账、统一逐专业底座入口、底座闭环逐专业执行批次、底座闭环页级/学校索引、底座审计表、候选字段复核总账、三方证据矩阵、页级 manifest、按页保真复核队列、家庭底线筛选表、候选V3复核入口索引、候选V3逐专业招生明细主表、候选V3逐专业复核队列、D0 工作台、D0 原页证据表、B0/B1 核验包、B0/B1 学校补源队列、组级索引、逐专业招生明细主表、山东工商学院 PDF 抽取表和审计表、逐专业证据合并表、保真复核队列 |
| 2026-06-28 | 对 20 条候选池和必要保底项做 PDF 原页、官网/章程、家庭接受度复核 | 候选池 V2 |
| 2026-06-29 | 完成专业接受度、调剂判断、冲稳保分层 | 冲稳保候选表 |
| 2026-06-30 | 形成最终志愿方案 | 最终志愿表、风险审查表 |
| 2026-07-01 | 家庭复核和填报系统演练 | 最终复查记录 |
| 2026-07-02 12:00 前 | 只处理应急修改 | 应急变更记录 |

## 七、当前最重要的判断

现在最重要的不是继续扩大数据量，而是先回答：

```text
某个院校专业组，组内所有专业我们是否都能接受？
```

如果答案是否定的，那么即使学校不错、城市不错、历史分数合适，也不能轻易服从调剂，甚至不能进入最终志愿表。

如果答案是肯定的，再去看这个组应该放在冲、稳、保哪个位置。

因此，下一步的工作重点是：

```text
底座稳定性总看板 -> B0/B1/B2 先核 -> P0 核 PDF 原页/三方证据/B0B1差异 -> P1 补字段和家庭调剂底线 -> 标记专业接受度 -> 判断是否可服从调剂
```

当前 2026 招生计划数据底座阶段的默认入口是 `data/working/issue19-foundation-stability-dashboard.csv` 和 `data/working/issue19-foundation-stabilization-major-detail-tasks.csv`。前者覆盖全部 13736 条招生专业明细：B0 校名/结构/官方查询键强阻断 2663 条，B1 P0 原页或官网冲突优先 4370 条，B2 字段缺口补证优先 5962 条，B3 三方官方闭环待核 542 条，B4 低风险抽检但仍非最终 199 条；后者只抽取 B0/B1/B2 共 12995 条，逐专业列出第一核验动作、保真证据链、双重佐证字段和阻断原因。今晚后续推进不等用户补材料，优先自动收敛 B0/B1/B2：核 385 条教育部未匹配校名逐专业解析任务、118 条湖北官方查询键碰撞、3108 条结构风险事件、854 条官网差异线索和 19065 个字段候选任务；但所有自动结果只进入 pending 核验队列，不能写成最终志愿方案。
