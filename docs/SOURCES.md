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
   - 2026-06-27 本地首页：`data/official/hubei-2026-admission-plan-platform/index-live-20260627.html`
   - 本地前端资源：`data/official/hubei-2026-admission-plan-platform/assets/*.js`
   - 已发现接口：`/prod-api/planQuery/plan/nfs`、`/prod-api/planQuery/plan/yxList`、`/prod-api/planQuery/plan/group` 等。
   - 无登录探测留存：`data/official/hubei-2026-admission-plan-platform/api-probes/*.json`
   - 当前状态：无登录请求返回 `{"code":401,"msg":"令牌不能为空"}`。
   - 2026-06-27 当前资源 SHA：`index-Cut-ZwER.js=191ac7517cf0c9ea22cb82d98c381664ba439ffe485936b600405b92593e4de4`、`planQuery-DaPwtzYm.js=1013eb61f6f142b97d439269397b4674d778cf2c00483120462d83748cfd90ee`、`index-BjY7ltef.js=63e980b0c2d033d8cfcc5e46c21690abd9f2b776d940a1f02be7d75d67358522`。
   - 用途：登录后查询或导出 2026 招生计划；未登录状态不能作为完整数据来源。接口结构化时一行一个招生专业，院校专业组只作索引。

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
   - 私有证据编号：`issue19-pdf-local-copy`，具体本地路径不写入公开仓库。
   - PDF 元数据：`data/working/issue19-pdf-source.json`
   - 提取方案：`docs/ISSUE19_PDF_EXTRACTION_PLAN.md`
   - SHA256：`ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d`
   - 当前判断：240 页，无可抽取文本层，需要渲染为图片后 OCR。
   - 限制：原始 PDF、渲染页图片、整页 OCR 文本和全量抽取结果默认只做本地私有留存，不提交公开仓库。

8. 第 19 期样本学校官网交叉校验源
   - 来源状态表：`data/working/issue19-sample-school-official-sources.csv`
   - 高优先级摘要：`data/working/issue19-high-priority-double-check-summary.csv`
   - 本地留存目录：`data/external/issue19-sample-school-official/`
   - 第一批结构化试跑主证据：武汉科技大学、湖北大学、湖北理工学院。
   - 第一批字段补充源：武汉商学院。
   - 第二批附件 OCR 后加入：湖北科技学院。
   - 补充证据：湖北工程学院、荆楚理工学院。
   - 限制：高校官网只能交叉校验专业组、专业、人数、学费、选科或备注等字段；最终仍以湖北省招办材料、湖北官方平台或志愿系统为准。

9. 候选 V3 B0/B1 官网/API 交叉校验源
   - 来源状态种子：`data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv`
   - 本地留存目录：`data/external/issue19-b0-b1-official-sources/`
   - 已留存来源：成都信息工程大学静态招生计划页，江汉大学、西安邮电大学、西安财经大学、西安医学院、中国传媒大学、山东大学、兰州大学、西北民族大学、天津外国语大学等官网/API 返回，杭州电子科技大学 XLSX，忻州师范学院、山东工商学院 PDF 原件及抽取表，江苏理工学院官方计划图和转录表，南宁学院官网静态计划表，武汉商学院分省分专业来源计划表和本科专业招生计划一览表，喀什大学 XLSX，以及若干仅能作为入口或章程线索的页面。
   - 当前状态：7 所学校为可复用高校官网湖北计划源，16 所为部分可核线索，8 所仍需继续补高校官网计划或章程来源，5 所目前只有章程/规则或不可用计划线索。
   - 已结构化到逐专业证据匹配表的来源类型：官网 AJAX/API JSON、官网静态 HTML 表、官网 XLSX、PDF 表格抽取留存 CSV、官方计划图转录 CSV、官网双表联合抽取。
   - 限制：高校官网/API/计划图只作为交叉校验证据；没有湖北院校专业组边界的来源只能核专业、计划、学费、校区或备注，不能单独证明调剂范围。武汉商学院官网“湖北”列遇到“历史或物理”等未拆分科类时，只用于核专业名、学费和选科，不作为物理类计划数。山东工商学院 PDF 的专业名列不是 PDF 文本，已用渲染图 OCR 专业名和 PDF 网格数字列双通道抽取，并保留审计表；仍需第 19 期原页和湖北官方系统闭环。

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
- `data/working/issue19-full-major-field-fidelity-ledger.csv`：第 19 期全量逐专业字段保真总账，覆盖 13736 条招生专业行；一行对应一个招生专业，合并逐专业质量、家庭底线、组内调剂风险、字段完整性和结构异常，所有行均保持 `最终可用=false`。
- `data/working/issue19-full-major-field-fidelity-ledger-summary.json`：全量逐专业字段保真总账摘要；记录 13736 行总账、13486 条高风险保真行、250 条暂未触发机器高风险行、主键唯一性和风险计数。
- `data/working/issue19-full-major-verification-batches.csv`：第 19 期全量逐专业核验批次表，覆盖 13736 条招生专业行；一行对应一个专业，合并全量字段保真总账和页级保真队列，给出 A0-A9 人工核验批次、触发原因和核验动作。
- `data/working/issue19-full-major-verification-batches-summary.json`：全量逐专业核验批次摘要；记录 13736 行、231 个 PDF 页、A0-A9 分布和全部不可进入最终专业列表的门禁。
- `data/working/issue19-priority-group-major-review-pack.csv`：第 19 期优先整组逐专业核验包，覆盖 1043 个优先专业组内的 7537 条招生专业明细；一行对应一个专业，专业组字段只作为投档和调剂范围上下文。
- `data/working/issue19-priority-group-major-review-pack-summary.json`：优先整组逐专业核验包摘要；记录 W0-W3、A0-A9、T1/T2/T3 分布和全部不可进入最终专业列表的门禁。
- `data/working/issue19-priority-major-evidence-workbench.csv`：第 19 期优先逐专业证据执行工作台，覆盖同一批 7537 条招生专业明细；把全量核验批次、全量保真总账、家庭逐专业表、页级保真队列、V3 保真总账、B0/B1 官网来源、D0 原页证据和三年投档线索下沉到每条专业行。
- `data/working/issue19-priority-major-evidence-workbench-summary.json`：优先逐专业证据执行摘要；记录 E0-E6 执行优先级、辅证命中、字段缺口、三年投档线索和全部不可进入最终专业列表的门禁。
- `data/working/issue19-full-major-evidence-workbench.csv`：第 19 期全量逐专业证据执行工作台，覆盖 13736 条招生专业明细；一行一个专业，把全量核验批次、全量保真总账、家庭底线、页级保真、优先整组包、B0/B1 官网辅证、D0 原页证据和三年投档线索统一到同一张执行视图。
- `data/working/issue19-full-major-evidence-workbench-summary.json`：全量逐专业证据执行摘要；记录 7537 条优先包明细、6199 条非优先包明细、F0-F4 非优先包补证优先级、辅证命中、字段缺口、历史线索和全部不可进入最终专业列表的门禁。
- `data/working/issue19-full-major-evidence-closure-tasks.csv`：第 19 期全量逐专业证据闭环任务队列，覆盖 13736 条招生专业明细并拆成 94935 条证据任务；一行对应一个专业行和一个证据项，只保留紧凑执行索引，完整 OCR 原文回链到全量证据工作台。
- `data/working/issue19-full-major-evidence-closure-tasks-summary.json`：证据闭环任务摘要；记录 82416 条基础任务、12473 条字段完整性补证任务、46 条 B0/B1 官网冲突或未匹配任务、P0/P1/P2 优先级和全部非最终门禁。
- `data/working/issue19-foundation-audit-summary.json`：第 19 期招生计划底座审计摘要，记录机器阻断项、人工复核项、页码覆盖、回退归属、重复专业代号和候选覆盖状态。
- `data/working/issue19-foundation-audit-findings.csv`：第 19 期招生计划底座审计发现表，区分“阻断检查通过”和“需人工复核”的 OCR、选科、学费、调剂、候选池和专业组归属风险。
- `data/working/issue19-foundation-page-audit.csv`：第 19 期按页审计表，覆盖 PDF 第 10-240 页，记录每页专业组数、专业明细数、结构异常、候选命中和页级复核优先级。
- `data/working/issue19-candidate-v2-field-review-ledger.csv`：候选 V2 逐字段人工复核总账，覆盖 23 个候选/补充专业组和 82 条专业明细，拆成 840 个字段核验任务。
- `data/working/issue19-candidate-v2-triangulation-matrix.csv`：候选 V2 三方证据矩阵，一行一个候选专业组，记录 PDF 原页、湖北官方系统、省招办计划、高校官网/章程、家庭接受度、调剂结论和历史线证据状态。
- `data/working/issue19-candidate-v2-evidence-ledger-summary.json`：候选 V2 证据总账摘要，记录字段任务数、P0/P1/P2/P3 分布、专业行 ID 匹配和当前不可进入最终候选状态。
- `data/working/issue19-page-manifest.csv`：第 19 期公开页级 manifest，覆盖 PDF 1-240 页，记录私有页图/文本证据编号、哈希、OCR 行数、QC 数、结构化专业组/专业明细和候选字段任务数。
- `data/working/issue19-page-manifest-summary.json`：第 19 期页级 manifest 摘要，记录 240 页渲染/OCR 完整性、10-240 页结构化覆盖、OCR/QC 总量和候选字段任务页码归属。
- `data/working/issue19-page-fidelity-review-queue.csv`：第 19 期按页保真复核队列，覆盖 PDF 第 10-240 页 231 个招生计划明细页；逐页对齐 manifest、底座页级审计和全量逐专业字段保真总账，只安排核页顺序，不替代逐专业明细。
- `data/working/issue19-page-fidelity-review-queue-summary.json`：按页保真复核队列摘要；记录 13736 条专业明细、3329 个专业组、F0/F1/F2/F3 和 P0-P6 汇总，以及全部不可进入最终结论的门禁。
- `data/working/issue19-family-fit-group-screen.csv`：第 19 期家庭底线专业组筛选表，覆盖 3329 个院校专业组；每行展开组内全部招生明细，并给出医学护理、超预算、偏好方向和调剂初判。
- `data/working/issue19-family-fit-major-detail.csv`：第 19 期家庭底线逐专业筛选表，覆盖 13736 条专业明细；一行一个专业，记录机器接受度初判、阻断或待核原因和家庭接受度待确认状态。
- `data/working/issue19-family-fit-screen-summary.json`：家庭底线筛选摘要，记录专业组/专业行数、机器家庭匹配分布、调剂初判分布和下一轮复核优先级分布。
- `data/working/issue19-candidate-v3-review-intake.csv`：候选 V3 复核入口表，覆盖家庭筛选 R0/R1/R2 与候选 V2 补充组，每行都带完整组内招生明细、页码哈希、候选批次、历史同组投档线线索和升级缺口；全部 `最终可用=false`。
- `data/working/issue19-candidate-v3-review-intake-summary.json`：候选 V3 摘要，记录 1327 条复核入口、批次分布、历史线命中分布、专业明细来源和最终可用边界。
- `data/working/issue19-candidate-v3-admission-detail.csv`：候选 V3 全量逐专业招生明细主表，覆盖 8412 行；其中 8410 条是真实招生专业，2 条为 0 明细占位。后续 V3 候选讨论默认使用该表，组级入口只作索引。
- `data/working/issue19-candidate-v3-admission-detail-summary.json`：候选 V3 逐专业主表摘要，记录 1327 个组级入口、8410 条真实招生明细、2 条占位、来源行数闭环、主键唯一性和最终可用边界。
- `data/working/issue19-candidate-v3-admission-detail-review-queue.csv`：候选 V3 全量逐专业复核队列，覆盖 8412 行；一行一个招生专业或 0 明细占位，记录核验优先级、必须核验字段、同组调剂机器风险、官方系统/高校官网证据落点和人工核验状态。
- `data/working/issue19-candidate-v3-admission-detail-review-queue-summary.json`：候选 V3 全量逐专业复核队列摘要，记录 8410 条真实明细、2 条 0 明细占位、D0-D6 核验优先级分布、T0-T3 调剂机器风险分布和最终可用边界。
- `data/working/issue19-candidate-v3-d0-resolution-workbench.csv`：候选 V3 D0 修正/核验工作台，覆盖 58 条 D0 任务；记录院校名称恢复建议、专业组标题 OCR 证据、历年投档线代码-校名佐证、代码冲突标记、疑似字符混淆和 0 明细占位处理口径。
- `data/working/issue19-candidate-v3-d0-resolution-workbench-summary.json`：D0 工作台摘要，记录 17 个专业组、55 条院校名疑似截断、2 条 0 明细占位、5 条代码冲突/字符混淆风险和所有行不可自动写回的边界。
- `data/working/issue19-candidate-v3-d0-pdf-page-evidence.csv`：D0 原页 OCR 证据表，按 17 个专业组聚合 58 条 D0 任务；记录页码、页图/OCR 文本哈希、标题行短摘录、匹配方式、结构化是否出现、结构异常、保守等级和不可自动写回边界。
- `data/working/issue19-candidate-v3-d0-pdf-page-evidence-summary.json`：D0 原页 OCR 证据摘要，记录 13 个精确标题命中、2 个 `0/O` 规范化匹配、2 个原页和结构化均未命中的 0 明细组，以及全部不可升级边界。
- `data/working/issue19-candidate-v3-b0-b1-group-review-pack.csv`：候选 V3 B0/B1 组级核验包，覆盖 49 个优先专业组，逐组列出页码证据、组内招生明细、历史线口径、核页重点和升级闸门；这是复核工作台，不是可填报清单。
- `data/working/issue19-candidate-v3-b0-b1-major-review-pack.csv`：候选 V3 B0/B1 逐专业核验包，覆盖 324 个逐专业核验任务；一行一个专业或 0 明细占位任务，用于回填 PDF、官方系统、章程、家庭接受度和调剂结论；这是复核工作台，不是可填报清单。
- `data/working/issue19-candidate-v3-b0-b1-review-pack-summary.json`：候选 V3 B0/B1 核验包摘要，记录组数、专业任务数、页码覆盖、0 明细组和发布边界。
- `data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv`：B0/B1 官方来源补充线索种子，记录已发现的高校官网入口、动态接口、静态计划页和官方计划图转录；只作补源和交叉校验线索。
- `data/working/issue19-b0-b1-official-source-search-log.csv`：B0/B1 追加官方来源检索日志，记录武汉轻工大学、湖北师范大学、长春工业大学、浙江工业大学、浙江传媒学院、韶关学院、江苏理工学院、南宁学院、成都师范学院、西安航空学院的官网来源状态、局限性和下一步。
- `data/working/issue19-candidate-v3-b0-b1-school-official-source-queue.csv`：B0/B1 学校官方来源队列，覆盖 36 所学校，记录官网来源状态、补源优先级、检索式和逐专业任务数；这是补源工作台，不是学校已核准结论。
- `data/working/issue19-candidate-v3-b0-b1-admission-detail-official-crosscheck.csv`：B0/B1 逐专业招生明细主表，覆盖 324 个逐专业任务；组级信息只作索引字段下沉到每条专业行。
- `data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv`：B0/B1 逐专业招生明细证据合并表，覆盖 324 个任务；后续讨论默认使用这张表，一行一个招生专业或 0 明细占位，同时带出 OCR 字段、官网匹配字段、计划数核验状态、保真处理状态和仍需核验项。
- `data/working/issue19-candidate-v3-b0-b1-official-crosscheck-queue.csv`：B0/B1 组级官方交叉校验索引，覆盖 49 个优先专业组，逐组记录 PDF、湖北官方系统、高校官网/章程、家庭接受度和调剂结论待核状态；全部 `可进入下一阶段=false`。
- `data/working/issue19-candidate-v3-b0-b1-major-official-crosscheck-queue.csv`：B0/B1 原逐专业官方交叉校验队列，覆盖 324 个逐专业任务；一行一个专业或 0 明细占位任务，记录专业代号、专业名称、计划数、学费、风险、官网来源状态和各字段待核状态。
- `data/working/issue19-candidate-v3-b0-b1-official-crosscheck-summary.json`：B0/B1 官方交叉校验摘要，记录 36 校、49 组、324 个逐专业任务、逐专业招生明细主表行数、官网来源状态分布、`final_available_count=0` 和 `major_final_available_count=0`。
- `data/working/issue19-b0-b1-retained-official-plan-normalized.csv`：B0/B1 已留存官网/API/HTML/XLSX/PDF/图片/双表联合抽取证据标准化表，当前 434 条；字段包括学校、来源文件、证据类型、年份、省份、科类、专业、计划数、学费、校区、选科和来源局限。
- `data/working/issue19-candidate-v3-b0-b1-official-evidence-match.csv`：B0/B1 逐专业官网证据匹配表，覆盖 324 条招生明细；一行一个招生专业，带出页码、专业组、专业代号、OCR 专业名、OCR 计划数、官网匹配专业、官网计划数、匹配状态、计划数核验状态和仍需核验项。
- `data/working/issue19-candidate-v3-b0-b1-official-evidence-match-summary.json`：B0/B1 逐专业官网证据匹配摘要；当前 152 条专业名匹配，其中 61 条计划数与 OCR 一致，55 条为 OCR 缺失但官网可补，19 条官网未给可比计划数，18 条计划数存在差异，全部保持非最终结论。
- `data/working/issue19-b0-b1-plan-conflict-review-queue.csv`：B0/B1 计划数冲突复核队列，18 条；按 OCR 疑似误取学费、计划数不一致等类型安排核页顺序，并记录保真诊断和计划数候选引用方式。
- `data/working/issue19-b0-b1-unmatched-major-review-queue.csv`：B0/B1 官网证据未匹配专业复核队列，32 条；用于定位 OCR 噪声、串行、官网表未覆盖和关键限定词未覆盖问题。
- `data/working/issue19-b0-b1-official-source-gap-priority.csv`：B0/B1 学校补源缺口优先表，19 所；区分 8 所 P0 待补官方计划源和 11 所已有官网线索但尚未结构化到逐专业证据的学校。
- `data/working/issue19-b0-b1-fidelity-review-summary.json`：B0/B1 保真复核队列摘要；只用于安排核页/补源，不是最终候选或填报方案。
- `data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv`：候选 V3 全量逐专业字段保真总账，覆盖 8412 条招生明细；一行对应一个招生专业或 0 明细占位，合并 D0 原页证据、B0/B1 计划数冲突、官网未匹配、字段完整性、结构异常、费用底线、调剂风险和家庭底线，所有行均保持 `最终可用=false`。
- `data/working/issue19-candidate-v3-major-field-fidelity-ledger-summary.json`：全量逐专业字段保真总账摘要；记录 8412 行总账、8234 条高风险保真行、178 条暂未触发机器高风险行、18 条 B0/B1 计划冲突覆盖和 32 条 B0/B1 官网未匹配覆盖。
- `data/external/issue19-b0-b1-official-sources/xztu-2026-hubei-physics-plan-extracted.csv`：忻州师范学院官网 PDF 宽表抽取出的湖北物理类逐专业证据，15 条；作为 PDF 原件的可复跑抽取结果，不替代第 19 期原页和湖北官方系统。
- `data/external/issue19-b0-b1-official-sources/sdtbu-2026-hubei-physics-plan-extracted.csv`：山东工商学院官网 PDF 抽取出的湖北物理类逐专业证据，24 条；专业名来自 PDF 渲染图 Apple Vision OCR 并带 OCR 原文、置信度和校正说明，湖北计划数来自 PDF 网格数字列，不替代第 19 期原页和湖北官方系统。
- `data/external/issue19-b0-b1-official-sources/sdtbu-2026-pdf-ocr-grid-audit.csv`：山东工商学院官网 PDF 网格 OCR 审计表，42 条；保留每个有湖北计划数行的 PDF 表格行号、OCR 原文、校正说明、是否纳入湖北物理类匹配表。
- `data/external/issue19-b0-b1-official-sources/jsut-2026-hubei-physics-plan-extracted.csv`：江苏理工学院官方计划图转录出的湖北物理类普通类逐专业证据，15 条；作为官方计划图的结构化转录结果，不替代第 19 期原页和湖北官方系统。
- `docs/ISSUE19_SAMPLE_DOUBLE_CHECK.md`：20 所样本学校 OCR 与学校官网交叉核验说明。
- `docs/ISSUE19_DOUBLE_CHECK_RESULTS_V1.md`：第 19 期高优先级 7 校样本核验 V1 结论和全量结构化前质量门槛。
- `docs/ISSUE19_FULL_ADMISSION_PLAN_DRAFT.md`：第 19 期全量招生计划 OCR 底座初稿说明和保真机制。
- `scripts/build_issue19_double_check_summary.py`：根据私有 OCR 定位和公开官网来源表生成高优先级 7 校摘要。
- `scripts/build_issue19_first_batch_review_seed.py`：根据私有 OCR 定位生成第一批 4 校逐组复核种子表，公开仓库只保留摘要 JSON。
- `scripts/build_issue19_first_batch_group_major_draft.py`：根据全量 OCR 行级数据生成第一批 4 校专业组/专业 OCR 初稿，专业明细只写入本地私有留存区。
- `scripts/build_issue19_full_admission_plan_ocr_draft.py`：根据全量 OCR 行级数据生成第 19 期全量公开招生明细初稿和候选池命中表。
- `scripts/build_issue19_candidate_review_workbench.py`：根据全量 OCR 底座和家庭偏好生成 20 条历史候选的候选组级复核工作台。
- `scripts/build_issue19_priority_review_queues.py`：根据全量 OCR 底座生成偏好专业检索队列和硬风险专业组队列。
- `scripts/build_issue19_candidate_review_page_packet.py`：根据候选复核工作台和全量 OCR 底座生成候选池页面复核包，公开保存页码和哈希，私有保存页图和页面 OCR 文本。
- `scripts/build_issue19_integrity_audit_queues.py`：根据候选页面复核包和全量 OCR 底座生成候选页码组号审计和全量专业明细结构异常队列。
- `scripts/build_issue19_candidate_v2_review_seed.py`：根据候选复核工作台、页码审计、页面复核包和人工页图复核结果生成候选 V2 专业组与逐专业明细复核种子。
- `scripts/build_issue19_candidate_v2_verification_workbench.py`：根据候选 V2 种子生成升级闸门工作台，明确进入排序前必须补齐的原页、官方系统、章程、家庭接受度和调剂证据。
- `scripts/build_issue19_full_quality_tiers.py`：根据全量专业组、专业明细和结构异常队列生成质量分层索引与复核队列；质量层级只用于安排核页优先级，不代表可填报。
- `scripts/build_issue19_major_detail_quality_workbench.py`：根据全量专业明细、专业组质量索引和结构异常队列生成逐专业明细质量工作台；后续候选讨论必须使用该表展开完整专业明细。
- `scripts/build_issue19_full_major_field_fidelity_ledger.py`：根据第 19 期全量逐专业质量工作台、家庭底线逐专业表和家庭底线专业组表生成全量逐专业字段保真总账；这是全量底座默认逐专业证据视图，不生成可填报结论。
- `scripts/build_issue19_full_major_verification_batches.py`：根据全量逐专业字段保真总账和页级保真复核队列生成 A0-A9 全量逐专业核验批次表；只用于安排人工核验顺序，不生成可报结论。
- `scripts/build_issue19_priority_group_major_review_pack.py`：根据全量逐专业核验批次表，把有历史候选、样本学校、偏好专业或待补证字段种子的专业组完整展开为逐专业明细包；用于整组核页和调剂风险判断，不生成可报结论。
- `scripts/build_issue19_priority_major_evidence_workbench.py`：根据优先整组逐专业核验包和现有证据表生成逐专业证据执行工作台；用于安排 PDF 原页、湖北官方系统、高校官网/章程、家庭接受度、调剂结论和三年稳定性核验，不生成可报结论。
- `scripts/build_issue19_full_major_evidence_workbench.py`：根据全量逐专业核验批次表、优先逐专业证据工作台和现有辅证表生成 13736 行全量逐专业证据执行工作台；用于把全量底座和优先核验切片统一起来，不生成可报结论。
- `scripts/build_issue19_full_major_evidence_closure_tasks.py`：根据全量逐专业证据工作台生成证据闭环任务队列；每条招生专业至少拆成 PDF 原页、湖北官方系统/省招办计划、高校官网/章程、家庭接受度、同组调剂和三年投档稳定性 6 类任务，额外补字段完整性和 B0/B1 冲突任务，不生成可报结论。
- `scripts/build_issue19_foundation_audit.py`：根据全量 OCR 初稿、质量分层、逐专业工作台、结构异常和候选覆盖生成底座审计表；用于证明机器层面的行数、页码、主键、异常和发布边界闭环。
- `scripts/build_issue19_candidate_evidence_ledgers.py`：根据候选 V2 升级工作台、全量逐专业工作台和底座审计生成字段复核总账与三方证据矩阵；用于后续人工回填和候选升级。
- `scripts/build_issue19_page_manifest.py`：根据私有 OCR 运行目录和公开结构化表生成 240 页公开页级 manifest；只输出页级元数据和哈希，不输出私有页图、整页 OCR 文本或本机路径。
- `scripts/build_issue19_page_fidelity_review_queue.py`：根据页级 manifest、底座按页审计和全量逐专业字段保真总账生成 231 页按页保真复核队列；用于排核页顺序和逐页对账，不生成候选或可报结论。
- `scripts/build_issue19_family_fit_screen.py`：根据全量专业组质量索引、逐专业质量工作台和家庭偏好生成家庭底线筛选表；只做 OCR 草案初筛，办学属性、字段和家庭接受度仍全部待核。
- `scripts/build_issue19_candidate_v3_review_intake.py`：根据家庭底线筛选、候选 V2、页级 manifest、三年历史投档线和全量 OCR 覆盖表生成候选 V3 复核入口；用于下一轮逐组核页和补证，不产生最终建议。
- `scripts/build_issue19_candidate_v3_admission_detail.py`：把候选 V3 复核入口展开为全量逐专业招生明细主表；优先使用候选 V2 逐专业种子和家庭底线逐专业表，不从长文本硬切专业。
- `scripts/build_issue19_candidate_v3_admission_detail_review_queue.py`：根据候选 V3 逐专业招生明细主表生成全量逐专业复核队列；所有真实专业都必须核 PDF 原页、湖北官方系统、高校官网/章程、完整专业组边界、校区、特殊限制、家庭接受度和调剂影响，0 明细占位只用于补齐组内招生明细。
- `scripts/build_issue19_candidate_v3_d0_resolution_workbench.py`：从 V3 逐专业复核队列的 D0 任务生成原页核验工作台；可提取 `专业组标题OCR原文` 中的完整院校名和历年投档线代码-校名线索，但不自动写回主表。
- `scripts/build_issue19_candidate_v3_d0_pdf_page_evidence.py`：把 D0 工作台聚合到 17 个专业组，并用私有行级 OCR 与公开页级 manifest 生成可公开的原页 OCR 证据表；公开输出只保留短标题摘录、行号、证据编号和 SHA，不写入私有路径、整页 OCR 或图片。
- `scripts/build_issue19_candidate_v3_b0_b1_review_pack.py`：根据候选 V3 入口、家庭底线逐专业表、候选 V2 逐专业种子和页级 manifest 生成 B0/B1 组级和逐专业核验包；不从长文本拆专业，优先使用结构化来源。
- `scripts/build_issue19_candidate_v3_b0_b1_official_crosscheck_queue.py`：根据 B0/B1 核验包和高校官网来源表生成学校来源、组级索引、逐专业招生明细主表和原逐专业官方交叉校验队列；这些表只是补证工作台，不代表官方核验完成。
- `scripts/extract_xztu_official_pdf_plan.py`：使用 `pdfplumber` 从忻州师范学院官网 PDF 中抽取湖北物理类专业行，并写出可审计 CSV；需要使用 bundled Python 或本地安装 `pdfplumber`。
- `scripts/extract_sdtbu_official_pdf_plan.py`：将山东工商学院官网 PDF 渲染为图片，使用 Apple Vision OCR 识别专业名列，再用 PDF 表格网格抽湖北列计划数，输出湖北物理类抽取表和网格 OCR 审计表；需要使用 bundled Python 和 macOS Swift/Vision。
- `scripts/extract_jsut_official_image_plan.py`：把江苏理工学院官方计划图人工转录并写成逐专业 CSV，同时保留来源图片和官网入口校验条件。
- `scripts/build_issue19_b0_b1_official_evidence_match.py`：把已留存官网/API/HTML/XLSX/PDF/计划图抽取证据标准化，并与 B0/B1 逐专业招生明细主表逐条匹配；同时生成逐专业招生明细证据合并表，输出只用于保真交叉校验，不是最终志愿方案。
- `scripts/build_issue19_candidate_v3_major_field_fidelity_ledger.py`：根据候选 V3 全量逐专业招生明细主表、逐专业复核队列、全量逐专业质量工作台、D0 原页证据和 B0/B1 保真队列生成全量字段保真总账；总账是逐专业明细粒度，不产生最终推荐。
- `scripts/build_issue19_b0_b1_fidelity_review_queues.py`：从 B0/B1 逐专业证据合并表生成计划数冲突、专业未匹配和学校补源缺口三类保真复核队列；只安排人工核验顺序，不生成可填报结论。
- `scripts/fetch_hubei_plan_platform.py`：湖北招生数智综合平台逐专业计划抓取脚手架；token 只从环境变量读取，原始分页响应默认保存在 Git 忽略的 `private/hubei-plan-platform/raw/`，公开输出为逐专业规范化 CSV 和摘要。
- `scripts/issue19_review_rules.py`：第 19 期候选工作台和复核队列共用的风险标签、风险等级、SHA 和行数记录规则。
- `data/working/historical-preferred-city-pool-2023-2025.tsv`：按成都、西安、武汉、北京生成的三年历史投档候选池，只用于发现候选；进入最终表前必须回看官方原件、2026 招生计划和招生章程。
- `data/working/candidate-pool-v1.csv`：第一版可讨论候选池，20 条，全部为 `needs_2026_plan_verification`。

## 使用优先级

1. 最终录取判断：湖北官方投档线、2026 湖北招生计划、高校招生章程。
2. 分数位次换算：湖北官方一分一段为主，static-data.gaokao.cn 作为交叉校验。
3. 专业名称和代码：教育部 2026 本科专业目录为准。
4. 候选发现和辅助理解：千问高考、阳光高考页面、其他第三方工具。

第三方工具的推荐概率、预测分和默认排序均不得直接进入最终方案，除非已用官方原件和招生章程复核。
