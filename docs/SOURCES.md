# 数据源

## 官方主来源

1. 湖北省教育考试院，2026 普通高考总分一分一段统计表
   - URL: https://www.hbea.edu.cn/html/2026-06/15962.html
   - 本地网页：`data/official/hubei-2026-one-score-one-rank-physics/source-page.html`
   - 本地图片：`data/official/hubei-2026-one-score-one-rank-physics/*.png`
   - 用途：确认 515 分同分人数、累计位次和位次区间。

2. 湖北省教育考试院，2026 普通高校招生录取控制分数线
   - URL: https://www.hbea.edu.cn/html/2026-06/15961.html
   - 本地网页：`data/official/hubei-2026-control-lines/source-page.html`
   - 本地图片：`data/official/hubei-2026-control-lines/control-lines.webp.png`
   - 用途：确认 2026 物理本科线、特殊招生线。

3. 湖北省教育厅，2025 本科普通批录取院校（首选物理）平行志愿投档分数线
   - URL: https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/zszy/zsfw/202507/t20250721_5727304.shtml
   - 本地网页：`data/official/hubei-2025-physics-toudang/source-page.html`
   - 本地图片：`data/official/hubei-2025-physics-toudang/raw-images/*.jpg`
   - 用途：最近一年核心参照；已保存 71 张官方图片。

4. 湖北省教育厅，2024 本科普通批录取院校（首选物理）平行志愿投档线
   - URL: https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/zszy/zsfw/202407/t20240721_5274253.shtml
   - 本地网页：`data/official/hubei-2024-physics-toudang/source-page.html`
   - 本地 PDF：`data/official/hubei-2024-physics-toudang/hubei-2024-physics-toudang.pdf`
   - 用途：第二年稳定性校验。

5. 湖北省 2023 本科普通批录取院校（首选物理）平行志愿投档线 PDF
   - URL: https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/xxgs/202307/P020250627347122820023.pdf
   - 本地 PDF：`data/official/hubei-2023-physics-toudang/hubei-2023-physics-toudang.pdf`
   - 用途：第三年趋势校验。

6. 湖北教育考试网 / 湖北招生数智综合平台，2026 志愿填报通知与政策问答
   - 志愿填报时间页面：http://www.hbccks.cn/html/gkzytb/2026-06/142885.html
   - 政策问答页面：http://gaokao.hbccks.cn/zkzc/2026-06/143020.html
   - 政策问答页面：http://gaokao.hbccks.cn/zkzc/2026-06/143021.html
   - 政策问答页面：http://gaokao.hbccks.cn/zkzc/2026-06/143022.html
   - 政策问答页面：http://gaokao.hbccks.cn/zkzc/2026-06/143040.html
   - 本地网页：`data/official/hubei-2026-volunteer-policy/*.html`
   - 用途：确认 2026 湖北志愿结构、填报时间、平行志愿规则、保存确认要求和操作风险。
   - 备注：本地留存使用 HTTP 地址抓取；同路径 HTTPS 抓取时曾返回 404 或证书域名不匹配。

7. 教育部 / 阳光高考，普通高等学校本科专业目录（2026 年）
   - 页面 URL：https://gaokao.chsi.com.cn/gkxx/zcdh/202604/20260428/2293468784.html
   - 本地网页：`data/official/moe-major-catalog/2026-major-catalog-page.html`
   - 本地 PDF：`data/official/moe-major-catalog/2026-major-catalog.pdf`
   - 用途：核验专业名称、专业代码、专业类归属，避免第三方平台专业分类误导。

8. 湖北教育考试网，2026 普通高等学校招生计划专题
   - 招生计划索引：http://www.hbccks.cn/html/gkgzzt/gkzsjh/
   - 2026 招生计划页面：http://www.hbccks.cn/html/gkzsjh/2026-05/142888.html
   - 本地网页：`data/official/hubei-2026-admission-plan-platform/hbccks-plan-index.html`
   - 本地网页：`data/official/hubei-2026-admission-plan-platform/hbccks-2026-plan-page.html`
   - 当前状态：2026 页面已公开，但正文显示“持续更新中，敬请期待”。
   - 用途：等待官方公开完整 2026 招生计划。

9. 湖北省招生数智综合平台
   - URL：https://zspt.hubzs.com.cn
   - 本地首页：`data/official/hubei-2026-admission-plan-platform/index.html`
   - 本地前端资源：`data/official/hubei-2026-admission-plan-platform/assets/*.js`
   - 已发现接口：`/prod-api/planQuery/plan/nfs`、`/prod-api/planQuery/plan/yxList`、`/prod-api/planQuery/plan/group` 等。
   - 无登录探测留存：`data/official/hubei-2026-admission-plan-platform/api-probes/*.json`
   - 当前状态：无登录请求返回 `{"code":401,"msg":"令牌不能为空"}`。
   - 用途：登录后查询或导出 2026 招生计划；未登录状态不能作为完整数据来源。

## 交叉校验来源

1. static-data.gaokao.cn 一分一段 JSON
   - URL: https://static-data.gaokao.cn/www/2.0/section2021/2026/42/2073/3/lists.json
   - 本地副本：`data/derived/hubei-2026-physics-section-static-gaokao-cn.json`
   - 用途：复核 515 位次区间和 2025/2024/2023 等位分。

2. 用户提供的成绩截图
   - 用途：确认各科成绩和总分。
   - 处理方式：不复制进项目，因为截图包含直接个人身份信息。

3. 阳光高考招生章程入口
   - URL：https://gaokao.chsi.com.cn/zsgs/zhangcheng/
   - 本地网页：`data/external/chsi/admission-regulations-index.html`
   - 用途：后续逐校核验招生章程、专业录取规则、体检限报、语种、单科要求、收费和校区。

4. 千问高考
   - 首页 URL：https://p.qianwen.com/gaokaopc/index
   - 本地首页：`data/external/qianwen-gaokao/index.html`
   - 本地前端资源：`data/external/qianwen-gaokao/assets/*.js`
   - 可复现公开接口：`https://gk.qianwen.com/api/gaokaoChoice/v1/getUserFilters?need=major`
   - 本地接口副本：`data/external/qianwen-gaokao/api/getUserFilters-need-major.json`
   - 当前可用内容：专业分类和专业代码；已看到 `计算机类 0809`、`计算机科学与技术 080901`、`软件工程 080902`、`数字媒体技术 080906`、`教育学类 0401` 等。
   - 已发现但暂不能直接稳定使用的接口：`api/scorerank/pc/data`、`api/gaokaoChoice/pc/getFilters`、`api/userPage/pc/index`、`api/user/pc/setUserInfoV3` 等。
   - 复现命令：`curl -L 'https://gk.qianwen.com/api/gaokaoChoice/v1/getUserFilters?need=major' -o data/external/qianwen-gaokao/api/getUserFilters-need-major.json`
   - 限制：部分接口需要签名、客户端场景参数或登录态；直接请求会返回参数错误或验签失败。千问高考只能作为“发现候选项、理解专业分类、辅助交叉校验”的第三方数据源，不能覆盖湖北官方投档线、2026 招生计划和高校招生章程。

5. 高校官网招生计划交叉校验
   - 说明文档：`docs/SCHOOL_CROSSCHECK_SOURCES.md`
   - 本地样例：`data/external/school-plan-crosschecks/`
   - 当前样例：武汉科技大学 2026 湖北院校专业组及招生计划、2026 各专业招生计划及学费标准。
   - 用途：辅助核验学校官网公布的专业、计划、学费、选科和专业组线索。
   - 限制：高校官网不能替代湖北省招办 2026 招生计划；若高校官网与省招办计划不一致，以省招办渠道为准。

6. 《湖北招生考试》第 16/19 期专项检索
   - 检索记录：`docs/HUBEI_ADMISSION_MAGAZINE_SEARCH.md`
   - 湖北招生考试网产品手册：https://www.hbksw.com/product/
   - 本地产品手册：`data/external/hbksw-product-brochure/`
   - 学校片段样例：`data/external/hubei-admission-magazine-search/whhxit-2026-c211-codes.html`
   - 当前结论：未找到 2026 第 16/19 期完整公开电子版；第 19 期是本项目首选物理招生计划核心材料。
   - 限制：学校片段和第三方 Excel 线索不能替代官方杂志或平台。

7. 《湖北招生考试》2026 年第 19 期 PDF
   - 本地私有路径：`private/raw/hubei-admission-magazine-2026-issue-19/issue19.pdf`
   - PDF 元数据：`data/working/issue19-pdf-source.json`
   - 提取方案：`docs/ISSUE19_PDF_EXTRACTION_PLAN.md`
   - SHA256：`ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d`
   - 当前判断：240 页，无可抽取文本层，需要渲染为图片后 OCR。
   - 限制：原始 PDF、渲染页图片、整页 OCR 文本和全量抽取结果默认只保存在 `private/`，不提交公开仓库。

8. 第 19 期样本学校官网交叉校验源
   - 来源状态表：`data/working/issue19-sample-school-official-sources.csv`
   - 高优先级摘要：`data/working/issue19-high-priority-double-check-summary.csv`
   - 本地留存目录：`data/external/issue19-sample-school-official/`
   - 第一批结构化试跑主证据：武汉科技大学、湖北大学、湖北理工学院。
   - 第一批字段补充源：武汉商学院。
   - 第二批附件 OCR 后加入：湖北科技学院。
   - 补充证据：湖北工程学院、荆楚理工学院。
   - 限制：高校官网只能交叉校验专业组、专业、人数、学费、选科或备注等字段；最终仍以湖北省招办材料、湖北官方平台或志愿系统为准。

## 派生数据说明

- `data/derived/hubei-2025-physics-toudang-ocr.txt`：由 2025 官方图片 OCR 生成。
- `data/derived/hubei-2025-physics-toudang-parsed.csv`：2025 投档线解析行，3147 条数据。
- `data/derived/hubei-2024-physics-toudang-parsed.csv`：2024 投档线解析行，2800 条数据。
- `data/derived/hubei-2023-physics-toudang-parsed.csv`：2023 投档线解析行，2874 条数据。
- `data/derived/initial-city-pool-2023-2025.tsv`：按初始城市关键词生成的初筛池，不是最终志愿表。
- `data/working/family-preferences.json`：当前家庭偏好和筛选底线。
- `data/working/2026-admission-plan-source-status.json`：2026 招生计划来源状态。
- `data/working/2026-admission-plan-template.csv`：后续导入 2026 招生计划的字段模板。
- `data/working/issue19-pdf-source.json`：第 19 期 PDF 元数据和私有留存边界。
- `data/working/issue19-admission-plan-template.csv`：第 19 期结构化计划录入模板。
- `data/working/issue19-sample-schools-20.csv`：第 19 期 OCR + 学校官网 double check 的 20 所样本学校清单。
- `data/working/issue19-sample-school-official-sources.csv`：20 所样本学校官网来源状态和本地留存路径。
- `data/working/issue19-high-priority-double-check-summary.csv`：第 19 期高优先级 7 校 OCR 定位和官网来源摘要，只保留统计指标与复核状态，不含整页 OCR 原文。
- `data/working/issue19-first-batch-review-seed-summary.json`：第一批 4 校私有逐组复核种子表的公开摘要，不含 OCR 原文。
- `data/working/issue19-first-batch-group-major-draft-summary.json`：第一批 4 校专业组/专业 OCR 初稿公开摘要，不含专业明细 OCR 原文。
- `data/working/issue19-full-admission-plan-school-ocr-draft.csv`：第 19 期全量 OCR 院校汇总初稿，公开招生明细底座的一部分，仍需人工复核。
- `data/working/issue19-full-admission-plan-group-ocr-draft.csv`：第 19 期全量 OCR 院校专业组汇总初稿，公开招生明细底座的一部分，仍需人工复核。
- `data/working/issue19-full-admission-plan-major-ocr-draft.csv`：第 19 期全量 OCR 专业行明细初稿，公开招生明细底座的一部分，所有行 `最终可用=false`。
- `data/working/issue19-full-admission-plan-candidate-coverage.csv`：第一版 20 条历史候选在第 19 期全量 OCR 初稿中的命中情况。
- `data/working/issue19-full-admission-plan-ocr-draft-summary.json`：第 19 期全量 OCR 招生明细公开摘要、质量状态和保真闸门。
- `data/working/issue19-candidate-plan-review-summary.csv`：第一版 20 条历史候选接入第 19 期 OCR 初稿后的候选组级复核表，含来源 SHA、机器初判、硬风险类型、费用和字段缺失情况。
- `data/working/issue19-candidate-plan-review-major-detail.csv`：第一版历史候选中已命中专业组的组内专业明细，77 条，所有行仍为 OCR 初稿。
- `data/working/issue19-candidate-plan-review-summary.json`：候选复核工作台摘要，记录输入文件 SHA、输出行数、机器初判分布和候选风险类型分布。
- `data/working/issue19-priority-review-queue.csv`：第一版 20 条历史候选的复核优先队列，先处理待定位、默认排除和高风险项。
- `data/working/issue19-preference-major-search.csv`：全量 OCR 中命中数字媒体技术、计算机相关、师范相关的专业行检索队列，含本专业风险、专业组风险和综合风险等级。
- `data/working/issue19-hard-risk-group-review-queue.csv`：全量 OCR 中命中医学/护理、高收费、中外合作、体检、语种单科、专项预科等风险标签的专业组队列。
- `data/working/issue19-priority-review-queues-summary.json`：全量优先专业和硬风险队列摘要，记录输入文件 SHA、输出行数、偏好方向命中量和综合风险分布。
- `data/working/issue19-candidate-review-page-packet.csv`：第一版 20 条历史候选所需回看的第 19 期 PDF 页码、页图哈希、页面 OCR 文本哈希和本页专业组清单；只保留公开元数据。
- `data/working/issue19-candidate-review-group-page-map.csv`：第一版 20 条历史候选到第 19 期 PDF 复核页码、同校 2026 OCR 专业组和同校页码的映射。
- `data/working/issue19-candidate-review-page-packet-summary.json`：候选池页面复核包公开摘要；私有页图和整页 OCR 文本只在本地生成，不提交。
- `data/working/issue19-candidate-page-code-audit.csv`：20 条历史候选的页码组号审计，记录候选组号在页面 OCR、全量专业组表和同校组号中的命中关系。
- `data/working/issue19-ocr-structure-anomaly-queue.csv`：全量专业明细结构异常队列，记录疑似串入下一院校、串入专业组代码、页眉串入、专业代号异常、数字字段错位和低置信度等风险。
- `data/working/issue19-integrity-audit-summary.json`：第 19 期完整性审计摘要，记录候选页码组号审计和结构异常队列的行数、类型分布和输入 SHA。
- `data/working/issue19-candidate-v2-group-review-seed.csv`：候选 V2 专业组复核种子，含 20 条历史候选、同页相邻风险组和同校偏好专业补充组，全部待人工复核。
- `data/working/issue19-candidate-v2-major-review-seed.csv`：候选 V2 逐专业招生明细复核种子，含 82 条专业明细，用于后续判断专业接受度和组内调剂风险。
- `data/working/issue19-candidate-v2-review-seed-summary.json`：候选 V2 摘要，记录输入文件 SHA、输出行数、证据来源和重点发现。
- `data/working/issue19-candidate-v2-verification-group-workbench.csv`：候选 V2 专业组升级工作台，记录原页核验、官方系统/省招办计划、高校章程、家庭接受度、调剂结论、历史线使用和升级缺口。
- `data/working/issue19-candidate-v2-verification-major-workbench.csv`：候选 V2 专业明细升级工作台，记录逐专业机器接受度初判、人工接受度待确认、字段核验状态、阻断原因和升级缺口。
- `data/working/issue19-candidate-v2-verification-workbench-summary.json`：候选 V2 升级工作台摘要，记录行数、默认闸门状态、0 明细组和专业接受度分布。
- `data/working/issue19-full-quality-group-tiers.csv`：第 19 期全量专业组质量索引，覆盖 3329 条专业组行，记录质量层级、复核优先级、字段异常、结构异常、重复规范化组码和风险命中。
- `data/working/issue19-full-quality-review-queue.csv`：第 19 期全量质量复核队列，列出 3300 条需要优先回看原页的专业组行，其中 P0 规则包括候选命中、偏好命中、硬风险、无明细、重复组码和字段异常等。
- `data/working/issue19-full-quality-tier-summary.json`：第 19 期全量质量分层摘要，记录 3329 个专业组行、13736 条专业明细、P0/P1/P3 数量、无明细组和重复规范化组码。
- `data/working/issue19-full-major-detail-quality-workbench.csv`：第 19 期全量逐专业明细质量工作台，覆盖 13736 条专业行，记录 `专业行ID`、`专业组出现ID`、组级质量、专业行异常、字段完整性、偏好/风险和复核优先级。
- `data/working/issue19-full-major-detail-review-queue.csv`：第 19 期全量逐专业明细复核队列，列出 13705 条需要优先回看原页的专业行。
- `data/working/issue19-full-major-detail-quality-summary.json`：逐专业质量摘要，记录 ID 唯一性、异常匹配、候选池/样本学校命中、字段缺失和逐专业 P0/P1/P3 数量。
- `data/working/issue19-foundation-audit-summary.json`：第 19 期招生计划底座审计摘要，记录机器阻断项、人工复核项、页码覆盖、回退归属、重复专业代号和候选覆盖状态。
- `data/working/issue19-foundation-audit-findings.csv`：第 19 期招生计划底座审计发现表，区分“阻断检查通过”和“需人工复核”的 OCR、选科、学费、调剂、候选池和专业组归属风险。
- `data/working/issue19-foundation-page-audit.csv`：第 19 期按页审计表，覆盖 PDF 第 10-240 页，记录每页专业组数、专业明细数、结构异常、候选命中和页级复核优先级。
- `data/working/issue19-candidate-v2-field-review-ledger.csv`：候选 V2 逐字段人工复核总账，覆盖 23 个候选/补充专业组和 82 条专业明细，拆成 840 个字段核验任务。
- `data/working/issue19-candidate-v2-triangulation-matrix.csv`：候选 V2 三方证据矩阵，一行一个候选专业组，记录 PDF 原页、湖北官方系统、省招办计划、高校官网/章程、家庭接受度、调剂结论和历史线证据状态。
- `data/working/issue19-candidate-v2-evidence-ledger-summary.json`：候选 V2 证据总账摘要，记录字段任务数、P0/P1/P2/P3 分布、专业行 ID 匹配和当前不可进入最终候选状态。
- `docs/ISSUE19_SAMPLE_DOUBLE_CHECK.md`：20 所样本学校 OCR 与学校官网交叉核验说明。
- `docs/ISSUE19_DOUBLE_CHECK_RESULTS_V1.md`：第 19 期高优先级 7 校样本核验 V1 结论和全量结构化前质量门槛。
- `docs/ISSUE19_FULL_ADMISSION_PLAN_DRAFT.md`：第 19 期全量招生计划 OCR 底座初稿说明和保真机制。
- `scripts/build_issue19_double_check_summary.py`：根据私有 OCR 定位和公开官网来源表生成高优先级 7 校摘要。
- `scripts/build_issue19_first_batch_review_seed.py`：根据私有 OCR 定位生成第一批 4 校逐组复核种子表，公开仓库只保留摘要 JSON。
- `scripts/build_issue19_first_batch_group_major_draft.py`：根据全量 OCR 行级数据生成第一批 4 校专业组/专业 OCR 初稿，专业明细只写入 `private/`。
- `scripts/build_issue19_full_admission_plan_ocr_draft.py`：根据全量 OCR 行级数据生成第 19 期全量公开招生明细初稿和候选池命中表。
- `scripts/build_issue19_candidate_review_workbench.py`：根据全量 OCR 底座和家庭偏好生成 20 条历史候选的候选组级复核工作台。
- `scripts/build_issue19_priority_review_queues.py`：根据全量 OCR 底座生成偏好专业检索队列和硬风险专业组队列。
- `scripts/build_issue19_candidate_review_page_packet.py`：根据候选复核工作台和全量 OCR 底座生成候选池页面复核包，公开保存页码和哈希，私有保存页图和页面 OCR 文本。
- `scripts/build_issue19_integrity_audit_queues.py`：根据候选页面复核包和全量 OCR 底座生成候选页码组号审计和全量专业明细结构异常队列。
- `scripts/build_issue19_candidate_v2_review_seed.py`：根据候选复核工作台、页码审计、页面复核包和人工页图复核结果生成候选 V2 专业组与逐专业明细复核种子。
- `scripts/build_issue19_candidate_v2_verification_workbench.py`：根据候选 V2 种子生成升级闸门工作台，明确进入排序前必须补齐的原页、官方系统、章程、家庭接受度和调剂证据。
- `scripts/build_issue19_full_quality_tiers.py`：根据全量专业组、专业明细和结构异常队列生成质量分层索引与复核队列；质量层级只用于安排核页优先级，不代表可填报。
- `scripts/build_issue19_major_detail_quality_workbench.py`：根据全量专业明细、专业组质量索引和结构异常队列生成逐专业明细质量工作台；后续候选讨论必须使用该表展开完整专业明细。
- `scripts/build_issue19_foundation_audit.py`：根据全量 OCR 初稿、质量分层、逐专业工作台、结构异常和候选覆盖生成底座审计表；用于证明机器层面的行数、页码、主键、异常和发布边界闭环。
- `scripts/build_issue19_candidate_evidence_ledgers.py`：根据候选 V2 升级工作台、全量逐专业工作台和底座审计生成字段复核总账与三方证据矩阵；用于后续人工回填和候选升级。
- `scripts/issue19_review_rules.py`：第 19 期候选工作台和复核队列共用的风险标签、风险等级、SHA 和行数记录规则。
- `data/working/historical-preferred-city-pool-2023-2025.tsv`：按成都、西安、武汉、北京生成的三年历史投档候选池，只用于发现候选；进入最终表前必须回看官方原件、2026 招生计划和招生章程。
- `data/working/candidate-pool-v1.csv`：第一版可讨论候选池，20 条，全部为 `needs_2026_plan_verification`。

## 使用优先级

1. 最终录取判断：湖北官方投档线、2026 湖北招生计划、高校招生章程。
2. 分数位次换算：湖北官方一分一段为主，static-data.gaokao.cn 作为交叉校验。
3. 专业名称和代码：教育部 2026 本科专业目录为准。
4. 候选发现和辅助理解：千问高考、阳光高考页面、其他第三方工具。

第三方工具的推荐概率、预测分和默认排序均不得直接进入最终方案，除非已用官方原件和招生章程复核。
