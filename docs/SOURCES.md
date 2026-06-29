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
   - 活体复查账本：`data/working/issue19-official-public-entry-live-recheck.json`
   - SHA256：索引页 `804a6e806629cc772677360c074fd5760796682ab0c88108be7ddfae773eaf50`，2026 页面 `5c56b9582418af6e1cfbd40431920a0fee28807492c6be30b972d118251e8776`。
   - 当前状态：2026-06-28 公开 HTTP 复核返回 200；活体复查 SHA 与留存副本一致；2026 页面已公开，但正文显示“持续更新中，敬请期待”。`can_finalize=false`，只能作为官方公开入口证据，不能作为结构化招生计划明细。
   - 用途：等待官方公开完整 2026 招生计划。

9. 湖北省招生数智综合平台
   - URL：https://zspt.hubzs.com.cn
   - 本地首页：`data/official/hubei-2026-admission-plan-platform/index.html`
   - 2026-06-27 本地首页：`data/official/hubei-2026-admission-plan-platform/index-live-20260627.html`
   - 2026-06-28 本地首页：`data/official/hubei-2026-admission-plan-platform/index-live-20260628.html`
   - 本地前端资源：`data/official/hubei-2026-admission-plan-platform/assets/*.js`
   - 已发现接口：`/prod-api/planQuery/plan/nfs`、`/prod-api/planQuery/plan/yxList`、`/prod-api/planQuery/plan/group` 等。
   - 无登录探测留存：`data/official/hubei-2026-admission-plan-platform/api-probes/*.json`
   - 活体复查账本：`data/working/issue19-official-public-entry-live-recheck.json`
   - 当前状态：无登录请求返回 `{"code":401,"msg":"令牌不能为空"}`；活体复查覆盖 `nfs`、`yxList`、`group`、`student` 和 `dict/pcdm`，均保持受阻。
   - 2026-06-28 首页 SHA：`6dade2ef84ab249dd9d700a24e98c63f40f8305bba2bb6250acbf8cf10fcaba3`。该变化只说明平台首页前端可访问并有新快照，不说明无登录可取得结构化招生计划。
   - 2026-06-27 当前资源 SHA：`index-Cut-ZwER.js=191ac7517cf0c9ea22cb82d98c381664ba439ffe485936b600405b92593e4de4`、`planQuery-DaPwtzYm.js=1013eb61f6f142b97d439269397b4674d778cf2c00483120462d83748cfd90ee`、`index-BjY7ltef.js=63e980b0c2d033d8cfcc5e46c21690abd9f2b776d940a1f02be7d75d67358522`。
   - 用途：登录后查询或导出 2026 招生计划；未登录状态不能作为完整数据来源。接口结构化时一行一个招生专业，院校专业组只作索引。

10. 教育部，全国高等学校名单
   - 页面 URL：https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202506/t20250627_1195683.html
   - 普通高校名单附件 URL：https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202506/W020250729615142156867.xls
   - 本地网页：`data/official/moe-2025-national-higher-school-list/source-page.html`
   - 本地 XLS：`data/official/moe-2025-national-higher-school-list/national-regular-higher-schools-2025.xls`
   - SHA256：网页 `6e262bdd12284183d55f5979d212e7ca2f476fb27cb3df102e3eecb4facea48f`，XLS `af6f0192c29fb412b441fb55a13311479d08f861d68257960c5edb2e4dfb55af`。
   - 用途：核验学校名称、学校标识码、主管部门、所在地、办学层次和教育部备注；辅助识别民办、合作办学、职业本科和校名 OCR 风险。
   - 限制：该名单截至 2025-06-20，不包含港澳台地区高等学校；`所在地` 是学校登记地线索，不等于 2026 招生专业实际就读校区；`备注` 为空不能直接等于公办最终结论；最终仍需湖北 2026 招生计划和招生章程闭环。

11. 湖北招生考试网，关于做好 2026 年军队院校招收普通高中毕业生工作的通知
   - URL：https://www.hbksw.com/tools/6/2281.html
   - 本地网页：`data/external/hubei-2026-military-academy/hbksw-2026-military-academy-admission.html`
   - 页面发布日期：2026-06-18 14:04。
   - 通知落款：湖北省军区动员局、湖北省军区政治工作局、湖北省教育厅。
   - 用途：军事院校本科提前批专项讨论的政策线索；页面包含 2026 在鄂军校计划总量、女生计划总量、填报时间、政审、军检、面试、体检合格类别和投档录取规则。
   - 重要边界：该来源不替代具体院校专业组计划、个人政审、军检和面试结论；军校不与本科普通批普通志愿混排，必须单独建专项核验表。

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
   - 官方系统不可得时的角色：优先自动抓取高校官网/API/XLSX/PDF/图片计划，用于批量 double check 第 19 期 PDF 抽取结果；若高校官网也没有湖北院校专业组边界，只能核专业、计划、学费、选科、校区或备注，不能单独证明调剂范围。

6. 官方系统不可得时的辅助数据源分层
   - `L1-省招办闭环`：第 19 期 PDF 原页、湖北官方平台或志愿系统、学校章程/官网三方一致。
   - `L2-省招办原件加高校辅证`：第 19 期 PDF 原页已核，高校官网/章程可复核关键字段，但湖北官方平台暂不可得。
   - `L3-高校辅证加第三方提示`：高校官网或第三方平台能提示方向，但未完成第 19 期原页核验。
   - `L4-OCR或单源线索`：只来自 OCR、第三方、单个网页或未闭环接口。
   - 限制：`L2` 可以进入候选讨论和人工抽检，不能自动定稿；`L3/L4` 只能用于发现候选和安排核验顺序。
   - 官方结构化计划暂不可得时的替代保真策略：第 19 期 PDF 原页仍是省招办原件层，高校官网/API/XLSX/PDF/图片只做自动 double check；最终候选、冲稳保边界、B0/B1 组、计划数冲突、官网未匹配、字段空缺但进入候选的专业必须 100% 回看原页并尽量核湖北官方系统。低风险辅证只做分层抽检，抽检出现结构错误、计划数冲突、关键限定词丢失、物理/历史未拆分、官网不是 2026 湖北物理普通本科、同组有家庭不能接受专业等情况时，升级同页列、同校或同组 100% 人工核验。
   - 自动核验优先级：优先抓高校官网的 API/JSON/XLSX，其次 HTML 表格，再其次 PDF 或图片计划；所有自动结果只作为字段候选、冲突提示或抽检样本，不能直接生成最终字段事实。
   - 人工核验降载方式：家庭或人工只集中签认最终候选完整专业组、冲稳保边界、红色冲突项和抽检失败升级项；不把 41208 个字段全部摊给人工逐项核对。
   - C4/C6 高校源刷新执行包：`data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv`，把 36 个 C4/C6 学校侧任务单独拆成公开执行包，并在 Git 忽略目录生成 601 条私有逐专业补源/补结构化明细；公开层只保存包级计数、泳道、集合 SHA 和私有 CSV SHA。
   - 高校官网辅证自动执行批次：`data/working/issue19-school-source-auto-execution-batches-public-ledger.csv`，从高校官网辅证状态快照生成 80 条公开执行批次，拆成冲突回页、补缺回页、专业名归属、补结构化、继续补源、章程规则和留存观察 7 条泳道；公开层只保存学校级任务、计数、SHA、状态桶和门禁。
   - 抽样门禁表：`data/working/issue19-official-unavailable-sampling-gates.csv`，用于在湖北官方结构化计划暂不可得时，把 80 条高校侧任务和 25 条 P3 低风险抽样明细变成可执行的 100% 核验、自动 diff、分层抽检和失败升级规则。
   - 抽样执行明细表：`data/working/issue19-official-unavailable-sampling-execution-detail.csv`，把抽样门禁下沉到 155 条逐专业明细，作为高风险 100% 核验、C2 强辅证抽样和 P3 低风险抽样的逐行执行入口。
   - 抽样复核 Overlay 公开账本：`data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv`，把 155 条执行明细接到本地私有复核表；公开层只保存 SHA、状态和计数，不保存学校专业明细、字段读数或人工备注。
   - 抽样页列核验包公开账本：`data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv`，把 155 条抽样复核明细压缩成 46 个 `PDF页码×版面列` 私有核页包；公开层只保存页列计数、证据编号、SHA 和非最终状态，不保存页图、OCR 行、学校专业明细或人工记录。
   - 抽样页列执行队列：`data/working/issue19-official-unavailable-sampling-review-execution-queue.csv`，把 46 个页列核验包按 E0-E4 风险泳道排序，公开层只保存页列顺序、计数、证据编号、SHA、升级规则和非最终门禁。
   - 抽样私有预填公开审计：`data/working/issue19-official-unavailable-sampling-triage-prefill-public-audit.csv`，把 46 个页列执行队列接到 Git 忽略的私有预填工作台；私有层预填 155 条明细的高校官网、OCR 和字段线索，公开层只保存页列计数、17 个高校来源文件聚合计数、私有 CSV SHA 和非最终门禁。

7. 《湖北招生考试》第 16/19 期专项检索
   - 检索记录：`docs/HUBEI_ADMISSION_MAGAZINE_SEARCH.md`
   - 湖北招生考试网产品手册：https://www.hbksw.com/product/
   - 本地产品手册：`data/external/hbksw-product-brochure/`
   - 学校片段样例：`data/external/hubei-admission-magazine-search/whhxit-2026-c211-codes.html`
   - 当前结论：未找到 2026 第 16/19 期完整公开电子版；第 19 期是本项目首选物理招生计划核心材料。
   - 限制：学校片段和第三方 Excel 线索不能替代官方杂志或平台。

8. 《湖北招生考试》2026 年第 19 期 PDF
   - 私有证据编号：`issue19-pdf-local-copy`，具体本地路径不写入公开仓库。
   - PDF 元数据：`data/working/issue19-pdf-source.json`
   - 提取方案：`docs/ISSUE19_PDF_EXTRACTION_PLAN.md`
   - SHA256：`ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d`
   - 当前判断：240 页，无可抽取文本层，需要渲染为图片后 OCR。
   - 限制：原始 PDF、渲染页图片、整页 OCR 文本和全量抽取结果默认只做本地私有留存，不提交公开仓库。

9. 第 19 期样本学校官网交叉校验源
   - 来源状态表：`data/working/issue19-sample-school-official-sources.csv`
   - 高优先级摘要：`data/working/issue19-high-priority-double-check-summary.csv`
   - 本地留存目录：`data/external/issue19-sample-school-official/`
   - 第一批结构化试跑主证据：武汉科技大学、湖北大学、湖北理工学院。
   - 第一批字段补充源：武汉商学院。
   - 第二批附件 OCR 后加入：湖北科技学院。
   - 补充证据：湖北工程学院、荆楚理工学院。
   - 限制：高校官网只能交叉校验专业组、专业、人数、学费、选科或备注等字段；最终仍以湖北省招办材料、湖北官方平台或志愿系统为准。

10. 候选 V3 B0/B1 官网/API 交叉校验源
   - 来源状态种子：`data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv`
   - 本地留存目录：`data/external/issue19-b0-b1-official-sources/`
   - 已留存来源：成都信息工程大学静态招生计划页，江汉大学、西安邮电大学、西安财经大学、西安医学院、中国传媒大学、山东大学、兰州大学、西北民族大学、天津外国语大学等官网/API 返回，杭州电子科技大学 XLSX，浙江工业大学 PDF 原件及抽取表，忻州师范学院、山东工商学院 PDF 原件及抽取表，江苏理工学院官方计划图和转录表，南宁学院官网静态计划表，武汉商学院分省分专业来源计划表和本科专业招生计划一览表，喀什大学 XLSX，以及若干仅能作为入口或章程线索的页面。
   - 当前状态：7 所学校为可复用高校官网湖北计划源，16 所为部分可核线索，8 所仍需继续补高校官网计划或章程来源，5 所目前只有章程/规则或不可用计划线索。
   - 已结构化到逐专业证据匹配表的来源类型：官网 AJAX/API JSON、官网静态 HTML 表、官网 XLSX、PDF 表格抽取留存 CSV、官方计划图转录 CSV、官网双表联合抽取。
   - 限制：高校官网/API/计划图只作为交叉校验证据；没有湖北院校专业组边界的来源只能核专业、计划、学费、校区或备注，不能单独证明调剂范围。武汉商学院官网“湖北”列遇到“历史或物理”等未拆分科类时，只用于核专业名、学费和选科，不作为物理类计划数。山东工商学院 PDF 的专业名列不是 PDF 文本，已用渲染图 OCR 专业名和 PDF 网格数字列双通道抽取，并保留审计表；仍需第 19 期原页和湖北官方系统闭环。

11. 2026-06-29 高校官网 live 补源尝试
   - 补源账本：`data/working/issue19-school-source-live-20260629-ledger.csv`
   - 补源账本摘要：`data/working/issue19-school-source-live-20260629-ledger-summary.json`
   - 本地留存目录：`data/external/issue19-school-source-live-20260629/`
   - 生成脚本：`scripts/build_issue19_school_source_live_20260629_ledger.py`
   - 有效新增源：西安航空学院官网 `2026年西安航空学院本科招生计划` 页面和高清 PDF。
   - 西安航空学院页面：`data/external/issue19-school-source-live-20260629/xaau-2026-undergraduate-plan-page.html`
   - 西安航空学院 PDF：`data/external/issue19-school-source-live-20260629/xaau-2026-province-major-plan.pdf`
   - 西安航空学院湖北物理/理工类抽取：`data/external/issue19-school-source-live-20260629/xaau-2026-hubei-physics-plan-extracted.csv`
   - 西安航空学院第 19 期对照：`data/working/issue19-school-source-live-20260629-xaau-crosscheck.csv`
   - 当前结论：西安航空学院官网 PDF 抽取到湖北物理/理工类 6 条、合计 15 人；第 19 期 K487 也有 6 条，但 OCR 计划数字段存在缺失或串读线索，特别是 K48704 自动化行疑似串入 K488 西安医学院。该源只能作为高校侧补缺候选，必须回看第 19 期原页和湖北官方侧后才能写回。
   - 未取得湖北物理专业加人数明细的尝试：长春工业大学官网招生计划栏目当前 2026 计划页仅见吉林省计划；武汉轻工大学官网入口、招生计划入口和湖北考生提示入口均为前端应用壳；湖北师范大学招生网普通抓取返回跳转登出页，信息公开网仅取得 2026 本科招生章程；浙江传媒学院留存招生网首页和信息公开网招考信息页，未见 2026 湖北物理计划明细；成都师范学院留存招生工作入口，未见 2026 湖北物理计划明细；韶关学院招生域名 HTTPS 访问失败；江苏理工学院招生网可见官方 2026 省外计划微信文章入口，但当前环境未能读取微信正文。
   - 新增入口留存：`cuz-zsw-home-20260629.html`、`cuz-xxgk-zkxx-20260629.html`、`cdnu-zsgz-entry-20260629.html`、`whpu-2026-plan-entry-shell.html`、`whpu-2026-hubei-fill-suggestion-shell.html`、`hbnu-2026-undergraduate-charter.html`、`jstu-zs-news-list-20260629.html`。
   - 限制：live 补源尝试只扩大 double check 覆盖，不替代湖北第 19 期、省招办计划或湖北官方系统。

12. 下一轮闭环与家庭讨论入口 V1
   - 生成脚本：`scripts/build_issue19_next_closure_family_review_v1.py`
   - 工作簿：`data/exports/issue19-next-closure-family-review-v1.xlsx`
   - 摘要：`data/exports/issue19-next-closure-family-review-v1-summary.json`
   - 页列核验包：`data/exports/issue19-next-closure-family-review-v1-first-closure-page-pack.csv`
   - 64 个小核验包：`data/exports/issue19-next-closure-family-review-v1-first-closure-action-pack.csv`
   - 206 条任务状态：`data/exports/issue19-next-closure-family-review-v1-first-closure-task-status.csv`
   - 55 个重点组讨论入口：`data/exports/issue19-next-closure-family-review-v1-priority55-group-review.csv`
   - 458 条完整组内专业明细：`data/exports/issue19-next-closure-family-review-v1-priority55-major-review.csv`
   - 输入来源：字段闭环与重点核验 V1 的第一闭环页列、第一闭环逐任务、第一闭环字段确认公开账本、55 个重点专业组和完整组内专业明细。
   - 当前结论：37 个第一闭环页列被拆成 64 个小核验包；55 个重点专业组被分成优先家庭讨论、先核限制、先核页、先看调剂和先核费用；458 条专业明细只作家庭接受度和调剂风险讨论入口，其中 147 条机器建议进入 6 专业讨论，44 个专业组可讨论服从调剂，11 个专业组需先核限制/字段后再判断调剂。
   - 限制：该入口不新增官方事实，不保存私有读数，不确认计划数、学费、选科或组边界；所有字段写回、推荐依据和最终可用计数仍为 0。

13. 数据基座下一批执行工作台 V1
   - 生成脚本：`scripts/build_issue19_data_foundation_next_execution_v1.py`
   - 工作簿：`data/exports/issue19-data-foundation-next-execution-v1.xlsx`
   - 摘要：`data/exports/issue19-data-foundation-next-execution-v1-summary.json`
   - P0 冲突包：`data/exports/issue19-data-foundation-next-execution-v1-p0-conflict-packages.csv`
   - P0 冲突逐任务：`data/exports/issue19-data-foundation-next-execution-v1-p0-conflict-tasks.csv`
   - 官网辅证 next20：`data/exports/issue19-data-foundation-next-execution-v1-school-source-next20.csv`
   - 55 组调剂风险：`data/exports/issue19-data-foundation-next-execution-v1-priority55-transfer-risk.csv`
   - 输入来源：下一轮闭环与家庭讨论 V1、第一闭环字段确认公开账本、高校官网辅证机会队列、2026-06-29 live 补源账本、55 组讨论入口和完整组内专业明细。
   - 当前结论：P0 冲突包 10 个、26 条任务，其中 19 条需双人复核、26 条均有高校辅证线索；官网辅证 next20 覆盖 18 所学校；55 个重点组中 29 组建议进入下一轮重点核验。
   - 限制：该入口只安排下一批核验和补源，不确认字段事实，不允许字段写回，不作为最终志愿方案。

14. 第一闭环事实进度公开账本
   - 生成脚本：`scripts/build_issue19_first_closure_fact_progress_public_ledger.py`
   - 事实进度账本：`data/working/issue19-first-closure-fact-progress-public-ledger.csv`
   - 页列汇总：`data/working/issue19-first-closure-fact-progress-page-summary.csv`
   - 公开摘要：`data/working/issue19-first-closure-fact-progress-summary.json`
   - 输入来源：第一闭环事实范围缺口账本、第一闭环核验结果看板、第一闭环字段级公开状态、公开证据地图、复核材料账本、任务复核账本、PDFOCR 候选审计、机器坐标候选审计和 B0 冲突页列状态。
   - 当前结论：覆盖 439 个待闭环事实范围、37 个页列和 206 条任务；事实域为字段事实 354、专业名归属 48、专业组边界 37；当前 PDF 原页和湖北官方侧均待闭环 439 个事实范围，字段写回、推荐依据、最终可用均为 0。
   - 限制：该账本只公开核验进度、状态桶、计数和 SHA，不公开字段值、OCR 正文、私有材料路径或最终结论；高校官网辅证仍只作 double check，不替代湖北官方计划。

15. 第一闭环事实准入门禁账本
   - 生成脚本：`scripts/build_issue19_first_closure_fact_gate_public_ledger.py`
   - 事实门禁账本：`data/working/issue19-first-closure-fact-gate-public-ledger.csv`
   - 页列汇总：`data/working/issue19-first-closure-fact-gate-page-summary.csv`
   - 任务汇总：`data/working/issue19-first-closure-fact-gate-task-summary.csv`
   - 公开摘要：`data/working/issue19-first-closure-fact-gate-summary.json`
   - 输入来源：第一闭环事实进度公开账本、第一闭环字段级公开状态、第一闭环核验结果看板、W0/B0 高校源桥接账本、W0/B0 高校源字段回接队列、第一闭环字段确认公开账本和任务复核公开账本。
   - 当前结论：覆盖 439 个事实范围、37 个页列和 206 条任务；所有事实均为 `blocked_not_ready_for_next_stage`，其中 W0/B0 核心事实 87、可高校源 double check 字段事实 68、PDF/湖北官方先行事实 19、B0 冲突事实 275、双人复核 146、人工看图 373。
   - 限制：该账本是公开阻断总账，只判断能否进入下一阶段；不确认字段事实、不公开字段值、不替代湖北官方计划、不生成学校专业建议或最终志愿方案。

16. 第一闭环事实准出门禁账本
   - 生成脚本：`scripts/build_issue19_first_closure_fact_resolution_gate_v1.py`
   - 准出门禁账本：`data/working/issue19-first-closure-fact-resolution-gate-v1-public-ledger.csv`
   - 页列汇总：`data/working/issue19-first-closure-fact-resolution-gate-v1-page-summary.csv`
   - 任务汇总：`data/working/issue19-first-closure-fact-resolution-gate-v1-task-summary.csv`
   - 公开摘要：`data/working/issue19-first-closure-fact-resolution-gate-v1-summary.json`
   - 输入来源：第一闭环事实准入门禁账本、事实范围缺口账本、字段事实公开账本、核验结果看板、证据状态账本、下一步动作矩阵、P0 即时三方闭环账本、高校源最新对齐账本、W0/B0 高校源字段回接队列和湖北官方公开入口状态快照。
   - 当前结论：覆盖同一批 439 个事实范围、37 个页列和 206 条任务；当前 PDF 原页待补 439、湖北官方侧待补 439、三方闭环待补 439、高校辅证待补 201、冲突待处理 275、双人复核待完成 146、专业名归属待闭环 48、专业组边界待闭环 37；可进入私有写回评审、字段写回、推荐依据、官网替代湖北官方计划和最终可用全部为 0。
   - 限制：该账本只做事实准出门禁和缺口说明，不公开字段值、学校名称、专业名称、OCR 原文、私有路径或最终结论；不能作为志愿推荐依据。

17. 第一闭环准出执行叠加表
   - 生成脚本：`scripts/build_issue19_first_closure_resolution_execution_overlay_v1.py`
   - 执行叠加表：`data/working/issue19-first-closure-resolution-execution-overlay-v1.csv`
   - 公开摘要：`data/working/issue19-first-closure-resolution-execution-overlay-v1-summary.json`
   - 输入来源：第一闭环执行队列、事实准出门禁账本、事实准出页列汇总、核验结果页列汇总和公开证据地图。
   - 当前结论：覆盖同一批 37 个页列、206 条任务和 439 个事实范围；R0 W0/B0 冲突事实先闭环 10 个页列、R1 专业名归属事实先闭环 9 个页列、R2 双人复核事实先闭环 18 个页列；PDF 原页、湖北官方侧和三方闭环待补事实均为 439，字段写回、推荐依据、官网替代湖北官方计划和最终可用全部为 0。
   - 限制：该表只把准出缺口叠加到执行顺序上，不确认字段事实、不公开字段值或学校专业明细、不替代湖北官方计划、不生成学校专业建议或最终志愿方案。

18. W0/B0 高校源桥接账本
   - 生成脚本：`scripts/build_issue19_w0_b0_school_source_bridge.py`
   - 公开账本：`data/working/issue19-w0-b0-school-source-bridge-public-ledger.csv`
   - 页列汇总：`data/working/issue19-w0-b0-school-source-bridge-page-summary.csv`
   - 公开摘要：`data/working/issue19-w0-b0-school-source-bridge-summary.json`
   - 输入来源：W0/B0 执行预填公开审计、高校源进度看板、高校源最新证据对齐账本和高校源结构化接入候选账本。
   - 当前结论：覆盖 87 个 W0/B0 核心事实、10 个页列、35 条任务、11 个院校代码；68 条字段事实已有高校源可作 double check 提示，19 条专业名归属或专业组边界必须先核 PDF 原页和湖北官方侧；7 条事实所在学校已有结构化接入候选。
   - 限制：该账本只公开高校源桥接状态、计数和 SHA，不公开字段值、人工记录、私有材料路径或最终结论；高校源只能作为定位、补缺或冲突提示，不替代第 19 期 PDF 原页和湖北官方计划。

19. W0/B0 高校源字段回接队列
   - 生成脚本：`scripts/build_issue19_w0_b0_school_source_field_backlink_queue.py`
   - 公开队列：`data/working/issue19-w0-b0-school-source-field-backlink-queue-public-ledger.csv`
   - 页列汇总：`data/working/issue19-w0-b0-school-source-field-backlink-page-summary.csv`
   - 院校汇总：`data/working/issue19-w0-b0-school-source-field-backlink-school-summary.csv`
   - 公开摘要：`data/working/issue19-w0-b0-school-source-field-backlink-summary.json`
   - 输入来源：W0/B0 高校源桥接账本、第一闭环字段级公开状态、第一闭环事实进度公开账本、第一闭环核验结果看板、高校源进度看板、高校源最新证据对齐账本和结构化接入候选账本。
   - 当前结论：覆盖 68 条可 double check 的 W0/B0 字段事实、10 个页列、10 个院校代码、26 条任务；字段为专业计划数 26、学费 26、再选科目 16；回接泳道为 B1 结构化候选优先 5、B2 双人核页前回接 45、B2 普通冲突提示 18。
   - 限制：该队列只用于把高校源提示接入私有核验材料，不公开字段值、OCR 正文、人工记录或私有路径；所有行仍待 PDF 原页和湖北官方侧闭环，不允许字段写回、推荐或替代湖北官方计划。

20. 高校官网 next20 官方源探测账本
   - 生成脚本：`scripts/build_issue19_school_source_next20_probe_ledger.py`
   - 智能答疑 API 留存脚本：`scripts/fetch_issue19_next20_zhinengdayi_official_sources.py`
   - 公开账本：`data/working/issue19-school-source-next20-official-probe-public-ledger.csv`
   - 公开摘要：`data/working/issue19-school-source-next20-official-probe-summary.json`
   - 智能答疑 API 公开账本：`data/working/issue19-next20-zhinengdayi-official-source-fetch-public-ledger.csv`
   - 智能答疑 API 摘要：`data/working/issue19-next20-zhinengdayi-official-source-fetch-summary.json`
   - 输入来源：数据基座下一批执行工作台 V1 的官网辅证 next20、2026-06-29 live 补源账本、C4/C6 已留存官网源复用审计、本地公开官方 JSON/PDF/XLSX/HTML/图片抽取源。
   - 当前结论：next20 共 20 个任务行、18 所学校；15 个任务行已有结构化高校侧辅证，覆盖 13 所学校；4 所学校仍需继续找 2026 湖北物理类分省分专业计划源或解析入口。
   - 限制：该账本只汇总高校侧官方源探测状态和公开计数，不公开逐专业字段值，不确认计划数、学费、选科或组边界，不允许字段写回。

21. 高校官网最新证据对齐账本
   - 生成脚本：`scripts/build_issue19_school_source_latest_reconciliation.py`
   - 公开账本：`data/working/issue19-school-source-latest-reconciliation-public-ledger.csv`
   - 公开摘要：`data/working/issue19-school-source-latest-reconciliation-summary.json`
   - 输入来源：高校官网辅证自动执行批次、官网辅证状态快照、next20 官方源探测账本、2026-06-29 live 补源账本、C4/C6 复用审计、C4/C6 结构化候选 diff 和 C4/C6 补源尝试账本。
   - 当前结论：覆盖 80 条高校侧辅证自动执行任务、36 所学校；60 条已有湖北物理结构化或候选 diff 线索，12 条只有入口或探针记录，8 条暂无可复用高校侧计划源；A4 继续补源任务中 4 条已经推进到结构化或 diff 线索、4 条仍需补源。
   - 限制：该账本只做高校侧公开证据状态对齐，不能替代第 19 期 PDF 原页、湖北官方系统或省招办计划；不确认逐专业字段事实，不允许字段写回，不作为志愿推荐依据。

22. 高校源缺口优先级清单
   - 生成脚本：`scripts/build_issue19_school_source_gap_priority_ledger.py`
   - 公开账本：`data/working/issue19-school-source-gap-priority-public-ledger.csv`
   - 公开摘要：`data/working/issue19-school-source-gap-priority-summary.json`
   - 输入来源：高校官网最新证据对齐账本、官网辅证状态快照、官网辅证自动执行批次、C4/C6 结构化候选 diff 和 C4/C6 补源尝试账本。
   - 当前结论：覆盖 80 条任务、36 所学校；按任务泳道分为冲突回页 17、OCR 补缺回页 8、专业名归属 12、补结构化 18、继续补源 8、章程规则 16、留存观察 1；执行优先级为先人工回页 37、自动补结构化或补源 26、规则抽检或留存 17。
   - 限制：该清单只排补源、结构化、核页和规则核验顺序；所有行仍需第 19 期 PDF 原页和湖北官方侧核验，不确认字段事实，不允许字段写回，不作为志愿推荐依据。

23. 高校源 E0 人工回页桥接队列
   - 生成脚本：`scripts/build_issue19_school_source_e0_manual_page_review_queue.py`
   - 公开账本：`data/working/issue19-school-source-e0-manual-page-review-queue-public-ledger.csv`
   - 公开摘要：`data/working/issue19-school-source-e0-manual-page-review-queue-summary.json`
   - 输入来源：高校源缺口优先级清单、第一闭环下一步动作矩阵。
   - 当前结论：覆盖 37 条 E0 人工先核回页任务、20 个院校代码；其中 35 条有同校第一闭环页列提示，2 条暂无同校页列提示；同校桥接提示合计关联 182 条第一闭环任务、17 个 PDF 页、22 个页列。
   - 限制：该队列只把 E0 高校侧任务接到同校页列提示，不能据此确认计划数、学费、选科、专业归属或专业组边界；所有行仍需第 19 期 PDF 原页和湖北官方侧核验。

24. Round4 重点核验55组独立入口
   - 生成脚本：`scripts/build_issue19_round4_priority_focus55.py`
   - 工作簿：`data/exports/issue19-round4-priority-focus55.xlsx`
   - 摘要：`data/exports/issue19-round4-priority-focus55-summary.json`
   - 重点核验组：`data/exports/issue19-round4-priority-focus55-groups.csv`
   - 完整组内专业明细：`data/exports/issue19-round4-priority-focus55-major-details.csv`
   - 暂缓组：`data/exports/issue19-round4-priority-focus55-paused65-groups.csv`
   - 输入来源：Round4 优先 120 组、Round4 完整组内专业、稳定基座专业组就绪桥接表和 Closure V1 重点 55 组。
   - 当前结论：从 Round4 优先 120 组压缩出 55 个重点核验组，另 65 组暂缓；55 组覆盖 48 所学校、458 条完整组内专业。
   - 限制：该入口只说明优先核验顺序、压缩理由、核验成本和调剂风险；不确认字段事实，不允许字段写回，不作为志愿推荐依据。

25. P0 top3 私有复核包公开台账
   - 生成脚本：`scripts/build_issue19_p0_top3_review_packet.py`
   - 公开台账：`data/working/issue19-p0-top3-review-packet-public-ledger.csv`
   - 逐字段公开台账：`data/working/issue19-p0-top3-field-review-public-ledger.csv`
   - 公开摘要：`data/working/issue19-p0-top3-review-packet-summary.json`
   - 私有材料证据编号：`p0_top3_private_review_packet_not_public`
   - 输入来源：数据基座下一批执行工作台 V1 的 P0 冲突包表和 P0 冲突逐任务表、第一闭环字段确认公开账本，以及 Git 忽略目录中的第一闭环私有工作台、页图和 OCR 文本。
   - 当前结论：已为 `135-left`、`199-left`、`209-right` 生成 3 个包、15 条任务的本地私有复核入口，并拆成 36 个字段核验单元：计划数 15 个、学费 15 个、再选科目 6 个。
   - 字段候选关系：`R0-候选冲突` 16 个、`R3-仅高校辅证候选` 13 个、`R1-候选一致` 6 个、`R2-仅PDFOCR候选` 1 个。该关系只用于安排核验优先级，不确认字段事实。
   - 限制：公开台账只保存状态、计数、关系桶、证据编号、集合 SHA 和私有材料 SHA；不保存页图路径、OCR 文本、字段候选值、人工读数、核验人或备注；不确认字段事实，不允许字段写回，不作为志愿推荐依据。

## 派生数据说明

- `data/derived/hubei-2025-physics-toudang-ocr.txt`：由 2025 官方图片 OCR 生成。
- `data/derived/hubei-2025-physics-toudang-parsed.csv`：2025 投档线解析行，3147 条数据。
- `data/derived/hubei-2024-physics-toudang-parsed.csv`：2024 投档线解析行，2800 条数据。
- `data/derived/hubei-2023-physics-toudang-parsed.csv`：2023 投档线解析行，2874 条数据。
- `data/derived/initial-city-pool-2023-2025.tsv`：按早期城市关键词生成的历史初筛池，不是当前 Round3 限制，也不是最终志愿表。
- `data/working/family-preferences.json`：历史 V0 家庭偏好和筛选底线，用于复现早期家庭底线筛选表；当前口径不要覆盖该文件。
- `data/working/family-preferences-current.json`：2026-06-28 后的当前家庭偏好、体检公开摘要、护理/动物医学/兽医暂不纳入、医技/康复专项了解口径、点名项目待核清单和 Round3 不限地区口径。
- `data/working/family-preferences-expanded-2026-06-28.json`：7 万预算、中外合作和特殊专项讨论口径；已同步当前护理/动物医学/兽医暂不纳入、医技/康复专项了解和城市地区不加分线索。
- `data/exports/issue19-round2-updated-preferences.xlsx`：第二轮更新偏好候选工作簿，含主线精选、医技/康复/农业/环境低优先级专项、点名学校观察、历史优先城市观察和组内明细。
- `data/exports/issue19-round2-updated-preferences-main-shortlist-groups.csv`：第二轮主线精选 100 个专业组；公办普通学费线索，临床/口腔/中医等暂缓方向不进主线，护理/动物医学/兽医暂不纳入，医技/康复不混入主线。
- `data/exports/issue19-round2-updated-preferences-health-agri-special-groups.csv`：第二轮医技/康复、农业、环境相关专项了解专业组；护理和动物医学/兽医不进入本轮专项候选。
- `data/exports/issue19-round2-updated-preferences-specific-watchlist.csv`：第二轮点名学校观察清单，包含西安建筑科技大学、贵州大学、北京农学院、厦门大学嘉庚学院、辽宁工程技术大学等待核线索。
- `data/exports/issue19-round2-updated-preferences-summary.json`：第二轮更新偏好候选池摘要、规模、方向统计和非定稿边界。
- `scripts/build_issue19_round2_updated_preferences.py`：根据稳定底座和当前家庭偏好生成第二轮候选池；只做讨论池和核验队列，不生成定稿志愿。
- `data/exports/issue19-round3-unrestricted-region.xlsx`：第三轮不限地区候选工作簿，城市和地区不参与筛选、加分或名额分配；含主线 120 组、优先讨论 60 组、低优先级专项和组内专业明细。
- `data/exports/issue19-round3-unrestricted-region-discussion-priority-groups.csv`：第三轮先讨论的 60 个专业组，只用于家庭讨论和入围核验。
- `data/exports/issue19-round3-unrestricted-region-main-shortlist-groups.csv`：第三轮不限地区主线精选 120 个专业组。
- `data/exports/issue19-round3-unrestricted-region-main-shortlist-majors.csv`：第三轮主线精选完整组内招生专业明细。
- `data/exports/issue19-round3-unrestricted-region-special-low-priority-groups.csv`：第三轮低优先级专项了解专业组，护理/助产、动物医学/兽医/动物科学仍不纳入。
- `data/exports/issue19-round3-unrestricted-region-summary.json`：第三轮不限地区候选池摘要、规模、方向统计和非定稿边界。
- `scripts/build_issue19_round3_unrestricted_region_candidates.py`：根据稳定底座和当前家庭偏好生成第三轮不限地区候选池；城市字段只展示，不参与排序加分。
- `data/working/2026-admission-plan-source-status.json`：2026 招生计划来源状态。
- `data/working/issue19-official-public-entry-status.json`：第 19 期底座相关官方公开入口状态快照，记录湖北教育考试网计划页/索引页 SHA、平台无登录 401 探针和当前不能直接定稿的边界。
- `data/working/issue19-official-public-entry-live-recheck.json`：第 19 期底座相关官方公开入口活体复查结果，记录当前公开入口 SHA 是否与留存一致、无登录接口是否仍返回 401，以及当前不能自动取得湖北官方结构化计划的边界。
- `data/working/issue19-official-unavailable-sampling-gates.csv`：湖北官方结构化计划暂不可得时的高校侧 double check 和分层抽样门禁表；高风险 100% 人工核验，低风险抽检失败后升级同页列、同校或同组。
- `data/working/issue19-official-unavailable-sampling-gates-summary.json`：上述抽样门禁摘要，记录 105 行门禁、C0/C1/C7 100% 核验明细数、C2 最低抽检明细数、P3 抽样数和全部非最终门禁。
- `data/working/issue19-official-unavailable-sampling-execution-detail.csv`：官方不可得时的逐专业抽样执行明细，覆盖 105 条高风险 100% 核验明细、25 条 C2 强辅证抽样明细和 25 条 P3 低风险抽样明细。
- `data/working/issue19-official-unavailable-sampling-execution-detail-summary.json`：上述执行明细摘要，记录 155 行逐专业明细、动作分布、风险分布、双人复核数和全部非最终门禁。
- `data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv`：官方不可得时的 155 条抽样执行明细复核 Overlay 公开账本；只保存本地复核表记录 SHA、三类证据填写计数、抽检失败/升级状态和非最终门禁。
- `data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger-summary.json`：上述公开账本摘要，记录 155 条 Overlay 记录、105/25/25 分层、50 条双人复核要求、初始 R0 状态和全部不可写回/不可推荐门禁。
- `data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv`：官方不可得时的抽样页列核验包公开账本，46 行；把 155 条抽样复核明细按 `PDF页码×版面列` 聚合，覆盖 40 个 PDF 页，只公开页列计数、证据编号、私有 CSV/HTML SHA、OCR 行数和非最终门禁。
- `data/working/issue19-official-unavailable-sampling-review-packets-public-ledger-summary.json`：上述页列包摘要，记录 46 个页列包、155 条抽样明细、105 条高风险 100% 核验、25 条 C2 抽样、25 条 P3 抽样、50 条双人复核和全部 R0 未填写状态。
- `data/working/issue19-official-unavailable-sampling-review-execution-queue.csv`：官方不可得时的抽样页列核验执行队列，46 行；按页列包生成 E0-E4 执行泳道和总序，人工优先核冲突/错位、官网未匹配、官网补缺候选，再核强辅证和低风险抽检。
- `data/working/issue19-official-unavailable-sampling-review-execution-queue-summary.json`：上述执行队列摘要，记录 46 个页列包、155 条抽样明细、105 条高风险 100% 核验、130 条需高校辅证、25 条待补源，以及 E0/E1/E2/E3/E4 为 7/11/3/2/23。
- `data/working/issue19-official-unavailable-sampling-triage-prefill-public-audit.csv`：官方不可得时的抽样私有预填公开审计，46 行；把页列执行队列接到私有预填工作台，公开层只保存页列级计数、17 个高校来源文件聚合计数、私有 CSV SHA 和全部非最终门禁。
- `data/working/issue19-official-unavailable-sampling-triage-prefill-summary.json`：上述预填公开审计摘要，记录 155 条私有预填明细、99 条高校辅证线索、17 个高校来源文件、130 条需高校辅证复核、25 条待补源，以及字段写回/推荐/下一阶段/最终可用计数均为 0。
- `data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv`：C4/C6 高校源刷新执行包，36 行；把 411 条 C4 补结构化明细和 190 条 C6 继续补源明细拆成可并行执行的学校包，公开层只保存计数、泳道、集合 SHA、私有 CSV SHA 和非最终门禁。
- `data/working/issue19-c4-c6-school-source-refresh-execution-packets-summary.json`：上述执行包摘要，记录 30 所学校、36 个包、601 条私有逐专业明细、X0/X1/X2/X3 泳道分布，以及所有字段写回/推荐/下一阶段/最终可用计数均为 0。
- `data/working/issue19-c4-c6-retained-source-reuse-public-ledger.csv`：C4/C6 已留存官网源复用公开审计，36 行；把 C4/C6 执行包同已留存官网标准化证据做保守匹配，公开层只保存包级计数、优先级和私有明细 SHA。
- `data/working/issue19-c4-c6-retained-source-reuse-summary.json`：上述复用审计摘要，记录 601 条私有明细中 206 条专业名匹配、85 条计划数一致候选、104 条 OCR 计划数补缺候选、19 条计划数冲突候选，全部不得写回或推荐。
- `data/external/issue19-c4-c6-official-sources/blcu-2026-hubei-physics-normal.json`：北京语言大学招生系统 API 原始留存，参数为湖北、2026、物理类、普通类；返回 14 条逐专业计划和 1 条汇总行，仅作高校侧辅证。
- `data/working/issue19-c4-c6-blcu-official-source-fetch-public-ledger.csv`：北京语言大学 C6 官方 API 抓取公开账本，1 行；只记录来源、请求参数摘要、本地 SHA、行数合计和非最终门禁。
- `data/external/issue19-c4-c6-official-sources/xauat-2026-hubei-physics-normal.json`：西安建筑科技大学招生系统 API 原始留存，参数为湖北、2026、物理类、普通类；返回 20 条逐专业计划和 1 条汇总行，仅作高校侧辅证。
- `data/working/issue19-c4-c6-xauat-official-source-fetch-public-ledger.csv`：西安建筑科技大学 C4/C6 官方 API 抓取公开账本，1 行；只记录来源、请求参数摘要、本地 SHA、行数合计、字段局限和非最终门禁。
- `data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv`：C4/C6 结构化候选 diff 公开账本，36 行；把既有官网标准化证据和新增高校官网源合并后，对 601 条私有明细生成包级匹配、计划数状态、人工最小核验集合和非最终门禁。
- `data/working/issue19-c4-c6-structured-candidate-diff-summary.json`：上述结构化候选 diff 摘要，记录综合结构化高校源 480 行、21 个有源包、20 个可生成候选 diff 包、97 条计划数一致候选、113 条 OCR 计划数补缺候选、25 条计划数冲突候选；只用于压缩人工核验范围。
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
- `data/working/issue19-p0-evidence-execution-packets.csv`：第 19 期 P0 证据执行包，严格从证据闭环任务队列中抽取 `P0-` 任务，当前 6619 条任务、5310 条招生专业明细、2282 个执行包、231 个 PDF 页、1056 所学校；一行对应一个专业行和一个 P0 证据项，`P0执行包ID` 只用于按页/学校/类型批量执行。
- `data/working/issue19-p0-evidence-execution-packets-summary.json`：P0 证据执行包摘要；记录 P0A PDF 原页结构阻断 4047 条、P0B 三方证据闭环 2526 条、P0C B0/B1 差异复核 46 条，以及全部不可升级、不可最终可用的门禁。
- `data/working/issue19-p0-evidence-review-worklist.csv`：第 19 期 P0 逐专业复核工作清单，覆盖同一批 6619 条 P0 任务；一行仍是一个招生专业明细和一个 P0 证据项，但额外带出全量证据工作台字段、页级 manifest 证据编号和 SHA、页级保真风险、人工核验闸口。该表用于人工逐行核验，不是最终志愿表。
- `data/working/issue19-p0-evidence-review-worklist-summary.json`：P0 逐专业复核工作清单摘要；记录 5310 条唯一招生专业明细、2282 个执行包、231 个 PDF 页、1056 所学校、6619/6619 上游回链命中，以及全部 `pending` 和不可升级门禁。
- `data/working/issue19-p1-field-gap-evidence-repair-matrix.csv`：字段缺口逐专业修复矩阵，19065 行；一行对应一个招生专业明细和一个字段缺口，其中再选科目 11456、专业计划数 6347、学费 1262。用于逐字段补证，不把空值解释为不限、无计划或无学费。
- `data/working/issue19-p1-field-gap-evidence-repair-matrix-summary.json`：字段缺口矩阵摘要；记录字段分布、12473 个唯一专业行、231 个 PDF 页和全部非最终门禁。
- `data/working/issue19-field-gap-repair-candidates.csv`：字段缺口候选修复线索表，19065 行；一行对应一个字段缺口候选，记录同组 OCR、当前 OCR 单元格或高校官网辅证产生的候选值、置信等级和禁止自动写回原因。非空候选 7621 条，全部 `候选可自动写回主表=false`。
- `data/working/issue19-field-gap-repair-candidates-summary.json`：字段缺口候选修复摘要；记录候选来源分布：组级 OCR 上下文 6782 条、OCR 单元格候选 817 条、高校官网辅证 22 条、无候选 11444 条。
- `data/working/issue19-hubei-official-plan-major-crosscheck-packets.csv`：湖北官方系统逐专业核验包，13736 行；一行对应一个招生专业明细和一个湖北官方系统/省招办计划核验任务，预留官方系统证据编号、字段差异和公开原始行 SHA。
- `data/working/issue19-hubei-official-plan-major-crosscheck-packets-summary.json`：湖北官方系统核验包摘要；记录 13736 个唯一专业行和 13736 个官方核验任务，当前全部 `pending_hubei_official_plan_review`。
- `data/working/issue19-b0-b1-public-official-diff-ledger.csv`：B0/B1 逐专业官网差异账，854 行；只覆盖已有高校官网/章程辅证线索的招生专业明细，记录官网匹配字段、计划数冲突、官网未匹配和仍需核验项。
- `data/working/issue19-b0-b1-public-official-diff-ledger-summary.json`：B0/B1 逐专业官网差异账摘要；记录 19 条计划数冲突、28 条官网未匹配、159 条已有最佳官网来源命中，以及全部非最终门禁。
- `data/working/issue19-b0-b1-official-evidence-by-major-line.csv`：B0/B1 官网证据逐专业旁挂表，854 行；一行一个 `专业行ID`，按官网证据强度分为 strong_support、fill_candidate、conflict_review、field_support、partial_source、needs_source、rules_only、unmatched。该表不替代湖北官方计划。
- `data/working/issue19-b0-b1-official-plan-fill-candidates.csv`：B0/B1 官网计划数补缺候选表，55 行；只收 OCR 计划数缺失但官网有计划数的专业明细，必须回到 PDF 原页和湖北官方系统确认后才能使用。
- `data/working/issue19-b0-b1-official-conflict-review.csv`：B0/B1 官网计划数冲突复核表，19 行；其中 13 行疑似 OCR 把学费读入计划数字段，优先回看原页计划数列和学费列。
- `data/working/issue19-b0-b1-official-evidence-sidecar-summary.json`：B0/B1 官网证据旁挂摘要；记录 66 条强辅证、55 条计划数补缺候选、19 条冲突核页、13 条疑似计划数学费错读和全部非最终门禁。
- `data/working/issue19-major-line-pdf-evidence-anchors.csv`：专业行原页证据锚点表，13736 行；一行一个招生专业明细，记录专业起始 OCR 行、专业窗口行号范围、坐标摘要、窗口文本 SHA256、页图/OCR 文本证据编号。公开表不保存 OCR 窗口原文，窗口原文只在 `private/`。
- `data/working/issue19-major-line-pdf-evidence-anchors-summary.json`：专业行原页证据锚点摘要；记录 13736 条专业行全部精确回连起始 OCR 行，其中 12596 条已生成专业行级 OCR 锚点，1127 条缺少组标题上下文，13 条专业窗口需重点回看。
- `data/working/issue19-major-detail-foundation-release.csv`：第 19 期统一逐专业底座入口，13736 行；一行一个招生专业明细，以 `专业行ID` 为主键，聚合 P0 复核任务、P1 字段缺口、湖北官方系统核验包、B0/B1 官网差异、页级证据编号、家庭底线、调剂风险和三年投档线索。该表用于检索、复核、补证和后续筛选预处理，不是最终志愿表。
- `data/working/issue19-major-detail-foundation-release-summary.json`：统一逐专业底座入口摘要；记录 13736 个唯一专业行、5310 条 P0 专业明细、12473 条字段缺口专业明细、13736 条湖北官方待核专业明细、854 条 B0/B1 官网差异专业明细和全部非最终门禁。
- `data/working/issue19-foundation-closure-major-batches.csv`：底座闭环逐专业执行批次主表，13736 行；一行一个招生专业明细，把统一底座入口转成 C0-C4 执行批次、首要核验动作、PDF/湖北官方/官网/家庭/调剂动作集合和执行总序。
- `data/working/issue19-foundation-closure-page-index.csv`：底座闭环页级执行索引，231 行；由逐专业执行批次主表按 PDF 页码重算，只用于安排核页顺序，不替代逐专业明细。
- `data/working/issue19-foundation-closure-school-index.csv`：底座闭环学校执行索引，1100 行；由逐专业执行批次主表按院校重算，只用于安排补源和学校级核验顺序，不替代逐专业明细。
- `data/working/issue19-foundation-closure-batches-summary.json`：底座闭环批次摘要；记录 C0 P0 先核 5310 条、C1 字段缺口先补 7608 条、C2 官网辅证主批次 0 条、C3 常规三方闭环 609 条、C4 低风险抽检 209 条、含官网辅证任务 854 条、B0/B1 官网差异任务 854 条和全部非最终门禁。
- `data/working/issue19-foundation-closure-gap-scorecard.csv`：逐专业闭环缺口看板，13736 行；一行一个招生专业明细，把闭环批次、字段候选、B0/B1 官网旁证、专业行原页证据锚点、家庭/调剂/湖北官方门禁合并成执行优先级。该表是当前核验顺序入口，不是最终报考方案。
- `data/working/issue19-foundation-closure-gap-scorecard-summary.json`：逐专业闭环缺口看板摘要；记录 S0 B0/B1 冲突 18 条、S1 P0+官网辅证 116 条、S2 P0 原页 5176 条、S3 字段缺口有候选 4248 条、S4 字段缺口无候选 3360 条、S6 常规三方 609 条、S7/S8 低风险抽检 209 条。
- `data/working/issue19-major-line-historical-toudang-sidecar.csv`：逐专业三年投档线索旁挂表，13736 行；一行一个招生专业明细，按 2026 院校专业组代码挂接 2023/2024/2025 同代码投档线、等位分差、再选要求规范集合、历史重复 code 和当前重复组代码风险。该表只作冲稳保筛选前置线索。
- `data/working/issue19-major-line-historical-toudang-sidecar-summary.json`：逐专业三年投档线索摘要；记录同代码 3 年命中 5836 条、2 年命中 3946 条、1 年命中 1940 条、0 年命中 2014 条；2025 历史投档表存在重复 code `H51001`，当前 2026 底座无对应专业明细行。
- `data/working/issue19-admission-detail-master-workbench.csv`：单一逐专业招生明细总工作台，13736 行；一行一个招生专业明细，把统一逐专业底座入口、逐专业闭环缺口看板、专业行原页证据锚点和三年投档线索旁挂表合并到同一行。后续新增城市、学校、专业方向或家庭讨论时默认先看这张表；院校、专业组、页码字段只是索引和调剂上下文。
- `data/working/issue19-admission-detail-master-workbench-summary.json`：单一逐专业招生明细总工作台摘要；记录四张来源表全部 13736 行 join 成功、`最终可用=0`、`可进入下一阶段=0`、官网证据不可替代湖北官方计划、PDF/湖北官方/家庭/调剂四类核验均为 13736 条必核。
- `data/working/issue19-admission-detail-structural-fidelity-register.csv`：逐专业结构保真登记表，13736 行；一行一个招生专业明细，显式标记专业组归属方式、唯一组码回退归属、重复组码、组内专业代号重复、结构异常和原页锚点状态。
- `data/working/issue19-structural-risk-major-line-ledger.csv`：逐专业结构风险事件派单表，3108 行；按风险事件展开，包含 1838 条唯一组码回退归属、116 条组内专业代号重复、14 条 2026 规范化专业组代码重复、13 条原页专业窗口为空和 1127 条缺少组标题上下文。
- `data/working/issue19-zero-detail-group-placeholder-workbench.csv`：0 明细专业组占位表，40 行；只保留专业组占位和补明细任务，不伪造专业代号或专业名称，不能作为招生专业明细参与候选筛选。
- `data/working/issue19-candidate-filter-prep-major-detail.csv`：逐专业候选筛选准备表，13736 行；一行一个招生专业明细，合并家庭偏好、城市关键词候选、学费数字线索、结构保真、调剂上下文和证据门禁。城市、办学属性、公办民办、校区均保持机器候选或 pending，不是确认事实。
- `data/working/issue19-candidate-filter-prep-summary.json`：候选筛选准备摘要；记录当前城市关键词命中 1723 条、办学属性待核 13736 条、学费超预算机器线索 1862 条、学费字段待核 1262 条，以及全部非最终门禁。
- `data/working/issue19-major-decision-readiness-gates.csv`：逐专业决策闸门表，13736 行；一行一个招生专业明细，显式列出 PDF 原页、湖北官方系统、办学属性、城市/校区、家庭接受度、同组调剂、字段缺口等阻断闸门。该表只用于机器预筛和核验排序，不是候选方案。
- `data/working/issue19-major-decision-readiness-gates-summary.json`：逐专业决策闸门摘要；记录 G0 结构或归属未闭环 4459 条、G1 家庭底线风险 2342 条、G2 字段缺口 6218 条、G3 可作机器预筛线索 350 条、G4 常规留存 367 条，全部不可进入下一阶段。
- `data/working/moe-2025-regular-higher-schools-normalized.csv`：教育部 2025 全国普通高等学校名单标准化表，2919 行；其中本科 1365 所、专科 1554 所，备注为民办 829 所、合作办学 14 所。该表只作学校登记信息官方基准。
- `data/working/moe-2025-regular-higher-schools-summary.json`：教育部普通高校名单标准化摘要，记录来源网页/XLS SHA、发布日期 2025-06-27、截至日期 2025-06-20、行数、层次和备注分布。
- `data/working/issue19-moe-school-attribute-major-detail.csv`：第 19 期逐专业教育部学校属性核验表，13736 行；一行一个招生专业明细，把教育部学校名称、标识码、主管部门、所在地、办学层次、备注、民办/合作办学/职业本科机器线索、父校/校区匹配边界下沉到每条专业行。
- `data/working/issue19-moe-school-attribute-major-detail-summary.json`：逐专业教育部学校属性核验摘要；记录精确匹配 13161 条、父校/校区类保守匹配 190 条、未匹配待核 385 条、未匹配学校 49 个、民办线索 2230 条、合作办学线索 34 条、职业本科名称线索 241 条，全部保持 `最终可用=false`。
- `data/working/issue19-moe-school-attribute-unmatched-schools.csv`：教育部名单未匹配学校支持清单，49 行；只用于回看 PDF 原页、湖北官方系统、学校官网或招生章程核校名和特殊院校性质，不能替代逐专业主表。
- `data/working/issue19-foundation-stability-dashboard.csv`：第 19 期底座稳定性总看板，13736 行；一行一个招生专业明细，把统一底座、决策闸门、教育部属性、湖北官方待核、官网差异、字段缺口、结构风险、官方查询键碰撞、三年投档线索和 PDF 锚点合并到同一行；只用于安排核验顺序和解释缺口。
- `data/working/issue19-foundation-stability-dashboard-summary.json`：底座稳定性总看板摘要；记录 B0 校名/结构/官方查询键强阻断 2663 条、B1 P0 原页或官网冲突优先 4370 条、B2 字段缺口补证优先 5962 条、B3 三方官方闭环待核 542 条、B4 低风险抽检但仍非最终 199 条，最终可用和可进入下一阶段均为 0。
- `data/working/issue19-foundation-stabilization-major-detail-tasks.csv`：第 19 期逐专业稳定化任务表，12995 行；从 B0/B1/B2 抽取一行一个招生专业明细，逐行列出第一核验动作、保真证据链、需双重佐证字段、字段候选、官网差异、结构风险、官方查询键碰撞和阻断原因；全部不得自动写回或作为志愿推荐依据。
- `data/working/issue19-foundation-stabilization-major-detail-tasks-summary.json`：逐专业稳定化任务摘要；记录 B0=2663、B1=4370、B2=5962，字段候选任务 19065，非空候选 7621，官网差异 854，结构风险专业明细 2334，官方查询键碰撞 118，未匹配校名解析 385，最终可用和可进入下一阶段均为 0。
- `data/working/issue19-raw-major-lineage-consistency-audit.csv`：第 19 期原始逐专业明细血缘审计表，13736 行；一行一个原始 OCR 专业行，固定 `原始CSV数据行号` 与 `专业明细源行号=原始CSV数据行号+1` 的映射，并按 `专业行ID` 回连到逐专业质量工作台、统一逐专业底座入口、单一逐专业招生明细总工作台、结构保真登记、底座稳定性看板、PDF 原页证据锚点、三年投档线索旁挂和闭环缺口看板。当前全链路核心字段漂移为 0，所有行仍 `最终可用=false`、`可进入下一阶段=false`、`是否允许作为志愿推荐依据=false`。
- `data/working/issue19-raw-major-lineage-consistency-audit-summary.json`：原始逐专业明细血缘审计摘要；记录 13736 条原始 OCR 专业行、13736 个唯一 `专业行ID`、3289 个专业组出现 ID、8 张核心下游表全部 13736 行回连、核心字段漂移行数 0、A0 全链路回连且核心 OCR 字段一致 13736 条。该摘要只证明原始数据结构化血缘和字段传递稳定，不证明 OCR 字段已经等于官方最终事实。
- `data/working/issue19-raw-major-source-evidence-audit.csv`：第 19 期原始逐专业明细源证据审计表，13736 行；一行一个招生专业明细，使用 `来源页码+版面列+专业起始行号` 回连私有 OCR 起始行，再按 `专业行ID` 回连公开页级 manifest、专业行原页证据锚点、私有窗口 JSONL 和原始血缘审计表。公开表只保存页码、行号、置信度、证据编号、哈希、QC 计数和状态，不保存 OCR 窗口原文、页图路径或登录态。
- `data/working/issue19-raw-major-source-evidence-audit-summary.json`：原始逐专业明细源证据审计摘要；记录 13736 条专业明细全部 S0 回连到私有 OCR 起始行、页级 manifest、窗口证据和公开锚点，起始行哈希、窗口哈希、页图 SHA、OCR 行数和页均置信度均满匹配。风险分层为 R2 起始行 P0_QC 6086 条、R2 锚点窗口阻断 13 条、R3 需优先复核 7019 条、R4 未触发起始行 QC 风险 618 条；这些风险只安排核页顺序，不生成志愿建议。
- `data/working/issue19-major-source-evidence-risk-sidecar.csv`：第 19 期逐专业源证据风险侧账，13736 行；一行一个招生专业明细，把源证据覆盖结论、风险等级、起始行 QC、窗口哈希、底座稳定性、闭环缺口和 P0 复核任务下沉到同一条 `专业行ID`。该表是新增城市、学校或专业方向时的源证据默认下钻入口之一。
- `data/working/issue19-major-source-evidence-risk-sidecar-summary.json`：逐专业源证据风险侧账摘要；记录 X1 专业窗口 P0 先核 13 条、X2 起始行 P0_QC 先核 6086 条、X3 源证据优先复核 7019 条、X4 低风险抽检 618 条，源证据优先核页合计 13118 条；所有行仍禁止自动写回和禁止作为志愿推荐依据。
- `data/working/issue19-field-fact-closure-ledger.csv`：第 19 期字段事实闭环总账，13736 行；一行一个招生专业明细，把单一逐专业招生明细总工作台、源证据风险侧账、字段缺口候选表、湖北官方系统核验包、B0/B1 官网证据旁挂表和逐专业决策闸门合到同一条 `专业行ID`。当前只核再选科目、专业计划数、学费三项关键字段的事实状态、候选任务、官方/PDF 待核状态和下一步补证入口，不生成志愿推荐。
- `data/working/issue19-field-fact-closure-ledger-summary.json`：字段事实闭环总账摘要；记录 L0 三字段缺口 693 条、L1 两字段缺口 5206 条、L2 单字段缺口有候选 3803 条、L3 单字段缺口无候选 2771 条、L4 三字段 OCR 齐全但待三方闭环 1263 条；字段候选任务 19065 条、非空候选 7621 条，PDF 原页和湖北官方字段核验仍全部待核。
- `data/working/issue19-field-fact-verification-tasks.csv`：第 19 期字段事实核验任务队列，41208 行；一行对应一个招生专业明细和一个关键字段，即 13736 条专业明细 × 再选科目、专业计划数、学费。用于逐字段安排原页重读、候选值回看、湖北官方系统核验和高校官网/章程辅证，全部不自动写回、不生成学校或专业建议。
- `data/working/issue19-field-fact-verification-tasks-summary.json`：字段事实核验任务摘要；记录三字段各 13736 条任务，K0 无候选原页重读 11444 条、K1 有候选待核 7621 条、K2 OCR 候选待三方闭环 22143 条，页级保真队列命中 41208 条。
- `data/working/issue19-field-fact-page-side-verification-queue.csv`：第 19 期全量字段页列核验队列，462 行；把 41208 条字段任务按 `PDF页码×版面列` 聚合，覆盖 231 个招生计划明细页、13736 条专业明细。公开表只保存页列计数、字段任务集合 SHA、证据编号和非最终门禁，不保存候选读数、院校名、专业名、专业代号或专业组代码。
- `data/working/issue19-field-fact-page-side-verification-queue-summary.json`：全量字段页列核验队列摘要；记录 450 个 V0 无候选阻断页列、12 个 V1 有候选待人工核验页列，41208 条任务均仍需 PDF 原页和湖北官方侧核验，字段写回、推荐依据和最终可用计数均为 0。
- `data/working/issue19-page-side-foundation-risk-register.csv`：第 19 期页列底座综合风险登记表，462 行；在全量字段页列核验队列基础上，按 `专业行ID -> PDF页码×版面列` 汇总总工作台、结构保真、结构风险、版面连续性、专业代号顺序、官方查询键碰撞、教育部未匹配校名、B0/B1 官网差异、决策闸门和源证据风险侧账。公开表只保存页列风险计数、风险等级分布、集合 SHA 和非最终门禁，不保存学校/专业明细、字段候选值、人工记录值、OCR 原文或私有路径。
- `data/working/issue19-page-side-foundation-risk-register-summary.json`：页列底座综合风险登记摘要；记录 231 个招生计划明细页、462 个页列、13736 条专业明细、41208 条字段任务，其中 460 个页列为 Z0 结构/源证据/官方消歧阻断先核，2 个页列为 Z1 字段缺口和结构风险并行核页；推荐依据、生成学校专业建议、下一阶段和最终可用计数均为 0。
- `data/working/issue19-page-side-foundation-verification-batches.csv`：第 19 期页列底座核验批次表，462 行；把页列底座综合风险登记表按风险顺序切成 19 个可执行核验批次，前 18 批各 25 个页列、最后 1 批 12 个页列。公开表只保存批次、页列、风险计数、集合 SHA、状态和非最终门禁。
- `data/working/issue19-page-side-foundation-verification-batches-summary.json`：页列底座核验批次摘要；记录 19 批、231 个招生计划明细页、462 个页列、13736 条专业明细、41208 条字段任务，其中 460 个页列为 Z0、2 个页列为 Z1，全部 R0 未开始，推荐依据、生成学校专业建议、下一阶段和最终可用计数均为 0。
- `data/working/issue19-page-side-foundation-batch-execution-packets.csv`：第 19 期页列底座批次执行包，19 行；把页列底座核验批次提升为批次级执行入口，并为每批生成本地私有 HTML/CSV 核页材料。公开表只保存批次计数、私有材料证据编号和 SHA、状态和非最终门禁，不保存识别行内容、页图路径、学校专业明细、字段读数或人工记录。
- `data/working/issue19-page-side-foundation-batch-execution-packets-summary.json`：页列底座批次执行包摘要；记录 19 批、462 个页列、13736 条专业明细、41208 条字段任务和 19 份私有批次核页材料；PDF 原页、湖北官方侧、下一阶段、推荐依据和最终可用计数均为 0。
- `data/working/issue19-page-side-foundation-review-progress-public-ledger.csv`：第 19 期页列底座公开核页进度账本，462 行；把 19 批私有核页材料的填写状态同步为公开页列状态机。公开表只保存页列状态、计数、私有材料证据编号和 SHA，不保存核页记录内容、字段值、识别行内容或页图路径。
- `data/working/issue19-page-side-foundation-review-progress-public-ledger-summary.json`：页列底座公开核页进度摘要；记录 19 批、462 个页列、231 个 PDF 页、13736 条专业明细、41208 个字段任务和 1441 个私有必填记录槽位；当前已填记录数 0，推荐依据、生成学校专业建议、下一阶段和最终可用计数均为 0。
- `data/working/issue19-page-side-foundation-field-clue-public-audit.csv`：第 19 期页列底座字段线索公开审计，462 行；把 41208 条字段事实核验任务按页列重新对账，只公开字段任务回链数、字段分布、P/K/Q 状态桶、线索缺失/冲突计数、PDF/湖北官方待核计数和私有字段线索模板 SHA。
- `data/working/issue19-page-side-foundation-field-clue-public-audit-summary.json`：页列底座字段线索公开审计摘要；记录 41208 条字段任务中 29764 条已有线索、11444 条缺线索、1137 条有冲突/多值/疑似信号，PDF 原页待核和湖北官方待核均为 41208，推荐依据、生成学校专业建议、下一阶段和最终可用计数均为 0。
- `data/working/issue19-page-side-foundation-human-review-overlay-public-ledger.csv`：第 19 期页列底座人工复核 Overlay 公开账本，462 行；在私有字段线索模板之上同步人工复核 Overlay 的页列级进度，只公开 Overlay 记录数、私有 CSV SHA、已填字段计数、三方一致性可评估计数和非最终门禁，不公开字段读数、官方值、院校专业明细或人工备注。
- `data/working/issue19-page-side-foundation-human-review-overlay-public-ledger-summary.json`：页列底座人工复核 Overlay 摘要；记录 19 批、462 个页列、231 个 PDF 页、41208 个字段任务、私有 Overlay 记录缺失 0、人工填写 0、字段确认 0、推荐依据和最终可用计数均为 0。
- `data/working/issue19-page-side-foundation-batch-01-sample-public-audit.csv`：第 19 期页列底座第 1 批样板复核公开审计，25 行；用于先验证 19 批并行前的批次级流程，只公开页列级字段任务分布、候选计数、动作桶、私有样板详表 SHA 和非最终门禁。
- `data/working/issue19-page-side-foundation-batch-01-sample-public-audit-summary.json`：第 1 批样板复核摘要；记录 25 个页列、23 个 PDF 页、717 条招生专业明细、2151 个字段任务，其中 Q0 831、Q1 1071、Q2 249，正式 Overlay 自动写回、推荐依据和最终可用计数均为 0。
- `data/working/issue19-page-side-foundation-all-batch-review-public-ledger.csv`：第 19 期页列底座全 19 批公开复核账本，462 行；覆盖 231 个 PDF 明细页、13736 条招生专业明细和 41208 个字段任务，只公开批次计数、字段状态分布、私有明细 SHA 和非最终门禁，不公开院校专业明细、字段候选值、OCR 原文、人工读数或私有路径。
- `data/working/issue19-page-side-foundation-all-batch-review-public-ledger-summary.json`：全 19 批复核摘要；记录 19 批、462 个页列、41208 个字段任务，Q0=15813、Q1=21606、Q2=3789，K0=11444、K1=7621、K2=22143；私有 Overlay 记录存在 41208 条但人工填写、自动写回、推荐依据和最终可用均为 0。
- `data/working/issue19-major-evidence-level-routing.csv`：第 19 期逐专业证据等级与核验路由表，13736 行；在湖北官方结构化计划暂不可公开自动取得时，把每条招生专业明细标为 L3/L4 证据等级、A0-A5 自动高校官网核验可执行性、P0-P3 人工核验优先级、H0-H4 人工强度和升级触发器。当前 L3 高校辅证加第三方提示 854 条，L4 OCR 或单源线索 12882 条；P0 100% 人工核验 5043 条，P1 页列集中核验 7952 条，P2 自动官网核验后人工确认 557 条，P3 低风险抽检 184 条。该表只用于保真路由、double check 和人工工作量压缩，不确认字段值、不替代湖北官方系统、不生成学校专业建议。
- `data/working/issue19-major-evidence-level-routing-summary.json`：逐专业证据等级与核验路由摘要；记录 13,736 条专业明细、854 条高校辅证命中、624 条可复用高校官网自动核验目标、13,736 条 PDF 原页和湖北官方待核门禁，以及最终可用、下一阶段、推荐依据和学校专业建议计数全部为 0。
- `data/working/issue19-stable-foundation-major-screening-view.csv`：稳定基座逐专业筛选视图，13736 行；一行一个招生专业明细，把单一逐专业总工作台、候选筛选准备表、字段事实闭环、证据路由、教育部学校属性、三年投档线索合到同一个 `专业行ID`。该表允许做机器初筛和核验排队，但全部 `最终可用=false`、`可进入下一阶段=false`、`是否允许作为志愿推荐依据=false`。
- `data/working/issue19-stable-foundation-group-screening-view.csv`：稳定基座院校专业组筛选视图，3329 行；按 `专业组出现ID` 聚合逐专业视图，保留整组专业清单索引、P0/P1/P2/P3 人工核验数量、字段缺口、学校属性、家庭底线、调剂风险和历史线索。该表只用于判断整组是否值得继续核验，不能作为最终专业组方案。
- `data/working/issue19-stable-foundation-screening-summary.json`：稳定基座筛选视图摘要；记录 13736 条逐专业明细、3329 个专业组、40 个 0 明细专业组、678 条机器初筛线索、1666 个机器观察池专业组、1816 个 P0 整组先核专业组，以及全部非最终门禁。
- `data/working/issue19-field-fact-p0-reread-worklist.csv`：第 19 期 P0 字段原页重读工作清单，11444 行；从字段事实核验任务队列中只抽取 K0 无候选字段，一行对应一个 `专业行ID × 字段名`，回连字段任务、原始源证据审计、PDF 原页证据锚点和页级保真队列，用于优先回看专业计划数、再选科目和学费的原页字段。
- `data/working/issue19-field-fact-p0-reread-worklist-summary.json`：P0 字段原页重读摘要；记录专业计划数 5739 条、再选科目 4674 条、学费 1031 条，覆盖 8536 条招生专业明细、231 个 PDF 明细页和 967 所学校；原始源证据、PDF 锚点和页级保真队列均 11444/11444 命中，全部仍为非最终状态。
- `data/working/issue19-field-fact-p0-reread-machine-candidates.csv`：第 19 期 P0 字段机器坐标候选表，11444 行；在 P0 字段原页重读工作清单的 K0 无候选字段上，用私有 OCR 窗口坐标和保守规则抽取候选值。公开输出只保存候选值、坐标摘要、必要来源 ID、页码/版面列、字段名、证据编号、哈希和非最终门禁，不保存 OCR 窗口原文、院校名、专业名、专业代号或专业组代码等上下文字段。当前非空候选 4840 条，其中专业计划数 2175 条、再选科目 1994 条、学费 671 条；6386 条仍需人工原页重读，218 条多值冲突需核页。
- `data/working/issue19-field-fact-p0-reread-machine-candidates-summary.json`：P0 字段机器坐标候选摘要；记录候选状态分布、坐标规则分布、页码/院校代码候选数量前 30 和全部非最终门禁。该表只把部分 K0 字段推进到“机器候选待人工核验”，不允许自动写回字段或生成学校专业建议。
- `data/working/issue19-field-fact-p0-closure-action-workbench.csv`：第 19 期 P0 字段闭环推进工作台，11444 行；严格继承 P0 字段原页重读任务粒度，把机器候选、PDF 原页核页、湖北官方系统或省招办计划核验、高校官网或招生章程辅证分成不同列。当前 A1/A1R 快速候选核页 4840 条、A2 多值冲突核页 218 条、A3 无候选重读 6386 条；人工读数和官方字段值均为空。
- `data/working/issue19-field-fact-p0-closure-action-workbench-summary.json`：P0 字段闭环推进摘要；记录动作桶、批次、三方待核状态、人工/官方/高校字段确认计数和全部非最终门禁。该表不产生字段事实，只安排核页和闭环动作。
- `data/working/issue19-field-fact-p0-semantic-crosssource-audit.csv`：第 19 期 P0 字段语义与多源线索审计表，11444 行；严格继承 P0 字段闭环推进工作台任务粒度，把机器候选语义风险、B0/B1 高校官网/章程字段线索和湖北官方待核状态并列。当前机器候选语义异常 15 条、计划数偏大需重点核页 11 条；机器候选与高校辅证一致 22 条、冲突 1 条、官网有规范字段但机器无候选 52 条。
- `data/working/issue19-field-fact-p0-semantic-crosssource-audit-summary.json`：P0 字段语义与多源线索摘要；记录语义状态、跨源关系、语义多源优先桶、湖北官方待核状态和全部非最终门禁。该表不产生字段事实，只用于防止机器候选噪声进入普通核页队列。
- `data/working/issue19-field-fact-p0-triage-execution-workbench.csv`：第 19 期 P0 字段三方核验执行工作台，11444 行；严格继承 P0 字段语义与多源线索审计表任务粒度，把执行总序、执行批次、执行方式、PDF 原页锚点、机器候选、高校官网/章程字段线索和湖北官方待核包合到同一条字段任务。当前冲突异常立即核页 16 条、计划数偏大重点核页 11 条、高校辅证线索三方核验 74 条、多值坐标冲突核页 218 条、常规机器候选核页 4791 条、无候选原页重读 6334 条；245 条要求双人复核。
- `data/working/issue19-field-fact-p0-triage-execution-workbench-summary.json`：P0 字段三方核验执行摘要；记录执行批次、执行方式、语义优先桶、原页锚点命中、湖北官方核验包命中、高校辅证字段线索和全部非最终门禁。该表只做核验派单，PDF 原页人工读数、湖北官方字段值和高校官网/章程字段值仍为空。
- `data/working/issue19-field-fact-p0-immediate-review-packet.csv`：第 19 期 P0 字段即时复核包，319 行；这是从 P0 字段三方核验执行工作台中按 `EXEC-01/02/03/04` 严格切出的派单包，覆盖冲突异常、计划数偏大、高校辅证线索和多值坐标冲突四类优先任务。该包仍是一行一个 `专业行ID × 字段名`，不保存院校名、专业名、专业代号或专业组代码，不写回字段事实。
- `data/working/issue19-field-fact-p0-immediate-review-packet-summary.json`：P0 字段即时复核包摘要；记录父表 11444 行、切片 319 行、执行包 222 个、PDF 页 114 个、院校代码 202 个、双人复核 245 条和全部非最终门禁。该摘要只说明先核哪些字段，不能作为推荐或排序依据。
- `data/working/issue19-p0-immediate-pdf-crop-evidence-index.csv`：第 19 期 P0 即时复核裁图证据索引，319 行；一行对应一个 `专业行ID × 字段名 × 即时复核任务ID`，公开表只保存裁图证据编号、裁图文件 SHA256、裁图规格 SHA256、页码、版面列、bbox、页图/窗口哈希和非最终门禁。裁图图片和本地裁图索引只在本地私有留存，不写入公开仓库。
- `data/working/issue19-p0-immediate-pdf-crop-evidence-index-summary.json`：P0 即时复核裁图证据索引摘要；记录 319 条本地裁图证据、114 个 PDF 页、148 个页码×版面列组合、字段分布、执行批次分布、哈希计数和全部非最终门禁。该摘要只证明证据可定位、可回看、可复验，不提供字段读数。
- `data/working/issue19-p0-immediate-three-way-closure-public-ledger.csv`：第 19 期 P0 即时三方闭环公开账本，319 行；一行对应一个 `专业行ID × 字段名 × 即时复核任务ID`，把 PDF 原页、湖北官方系统或省招办计划、高校官网或招生章程三条证据链的私有核验状态分列。公开表只保存任务 ID、证据编号、SHA、bbox、状态和门禁，不保存具体字段读数、本地裁图路径、复核备注或最终确认值。
- `data/working/issue19-p0-immediate-three-way-closure-public-ledger-summary.json`：P0 即时三方闭环公开账本摘要；记录 319 条闭环任务、75 条高校字段线索、23 条机器/高校可比对线索、22 条一致、1 条冲突、52 条高校补缺线索，以及全部非最终门禁。该摘要只说明三方核验顺序和阻断状态，不能作为推荐或排序依据。
- `data/working/issue19-p0-immediate-crop-ocr-public-audit.csv`：第 19 期 P0 即时裁图 OCR 公开审计表，319 行；一行对应一个 `专业行ID × 字段名 × 即时复核任务ID`，把私有裁图 Apple Vision OCR 的可比候选状态、与机器候选/高校辅证的关系和人工优先桶公开化。公开表只保存状态、关系、SHA 和门禁，不保存识别文本、候选读数或图片路径。
- `data/working/issue19-p0-immediate-crop-ocr-public-audit-summary.json`：P0 即时裁图 OCR 公开审计摘要；记录 319 张裁图均有识别行、253 条有可比 OCR 候选、50 条冲突优先人工核页、35 条与既有线索一致但仍待三方核验、66 条未能稳定补读需人工看图。该摘要只用于安排人工核页顺序，不生成字段事实。
- `data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv`：第 19 期 P0 即时字段确认公开账本，319 行；一行对应一个 `专业行ID × 字段名 × 即时复核任务ID`，把私有字段确认工作台中的 PDF 原页、湖北官方、高校辅证和双人复核完成情况转成公开状态机。公开表只保存状态、证据编号、SHA、bbox、关系状态和门禁，不保存字段记录值、候选值、识别文本或图片路径。
- `data/working/issue19-p0-immediate-field-confirmation-public-ledger-summary.json`：P0 即时字段确认公开账本摘要；记录 319 条字段确认任务、75 条需要高校辅证私有记录、290 条需要双人复核、319 条仍待 PDF 原页和湖北官方私有记录、字段写回评估可进入数 0。该摘要只说明人工闭环状态，不生成字段事实或推荐依据。
- `data/working/issue19-p0-immediate-page-review-packets.csv`：第 19 期 P0 即时按页核页包，148 行；把 319 条字段确认任务按 `PDF页码×版面列` 聚合，覆盖 114 个 PDF 页。公开表只保存页列包 ID、任务数、字段分布、证据编号集合、SHA、bbox 摘要、状态和门禁，不保存本地 HTML、裁图图片、候选读数、识别文本、院校名、专业名、专业代号或专业组代码。
- `data/working/issue19-p0-immediate-page-review-packets-summary.json`：P0 即时按页核页包摘要；记录 148 个页列包、319 条字段任务、319 个裁图证据、290 条双人复核任务、75 条高校辅证私有记录待完成、PDF 原页和湖北官方私有记录待完成各 319 条。该摘要只用于安排人工逐页逐列核 PDF 原页，不能作为推荐或排序依据。
- `data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit.csv`：第 19 期 P0 即时 PDF 原页读数候选公开审计表，319 行；一行对应一个 `专业行ID × 字段名 × 即时复核任务ID`，把私有裁图 OCR 候选、字段确认账本和按页核页包合并成公开状态。公开表只保存候选存在状态、候选关系、审阅桶、证据编号、SHA、bbox 和非最终门禁，不保存候选读数、OCR 行文本、图片路径或人工字段值。
- `data/working/issue19-p0-immediate-pdf-reading-candidate-public-audit-summary.json`：P0 即时 PDF 原页读数候选摘要；记录 319 条字段任务中 253 条有私有候选线索、66 条无稳定候选需人工看图、33 条候选冲突优先核图、43 条候选与既有线索一致但仍需核官方、177 条有候选但需人工确认、99 条需直接图像复核、290 条需双人复核、自动写入人工读数 0。该摘要只用于排人工核页顺序，不生成字段事实或推荐依据。
- `data/working/issue19-p0-immediate-page-execution-queue.csv`：第 19 期 P0 即时页列核页执行队列，148 行；一行对应一个 `PDF页码×版面列`，把按页核页包和 PDF 原页读数候选审计合并后重新排序。公开表只保存执行顺序、页列优先级、任务数量、证据编号、SHA、bbox 和非最终门禁，不保存候选读数、OCR 行文本、图片路径、院校名、专业名、专业代号或专业组代码。
- `data/working/issue19-p0-immediate-page-execution-queue-summary.json`：P0 即时页列核页执行摘要；记录 148 个页列包覆盖 114 页和 319 条字段任务，其中 11 个页列包为候选冲突先核、34 个为无稳定候选先看图、11 个为候选一致仍需官方闭环、92 个为常规候选人工确认。该摘要只用于组织核 PDF 原页和湖北官方核验顺序，不生成字段事实或推荐依据。
- `data/working/issue19-p0-immediate-page-execution-progress-public-ledger.csv`：第 19 期 P0 即时页列执行进度公开账本，148 行；把 P0 即时页列核页执行队列接到私有字段确认工作台，公开层只保存完成计数、状态分布、任务集合 SHA 和非最终门禁，不保存私有记录值、候选值、识别文本、图片路径、院校名、专业名、专业代号或专业组代码。
- `data/working/issue19-p0-immediate-page-execution-progress-public-ledger-summary.json`：P0 即时页列执行进度摘要；记录 148 个页列包全部为 R0，319 条 PDF 原页记录、319 条湖北官方侧记录、75 条高校辅证记录、290 条双人复核均未完成；三方一致性可评估数、字段写回复查数、推荐依据数和最终可用数全部为 0。
- `data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv`：稳定基座自动官网辅证交叉核验工作台，854 行；一行对应一条 B0/B1 高校官网辅证旁挂，把官网强辅证、补缺候选、冲突复核、章程规则、部分来源和待补源拆成可复跑动作。高校官网仍只能 double check 和定位冲突，不能替代湖北官方计划。
- `data/working/issue19-stable-foundation-minimal-manual-closure-workbench.csv`：稳定基座最小人工闭环工作台，319 行；一行对应一个 P0 即时字段核验任务，把页列进度、裁图证据、官网辅证动作、双人复核和人工必做步骤接到同一张表。该表只安排 PDF 原页和湖北官方侧核验，不保存人工读数或最终字段事实。
- `data/working/issue19-stable-foundation-next-closure-workbench-summary.json`：稳定基座下一步闭环摘要；记录自动工作台 854 行、人工工作台 319 行、官网辅证动作分布、P0 字段分布、官方公开入口仍不可定稿和所有最终门禁为 0。
- `data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv`：稳定基座高校侧辅证刷新公开账本，80 行；一行对应一个 `高校×高校侧辅证动作`，把 854 条 B0/B1 高校官网辅证压缩为可自动复跑、补结构化、继续补源、分层抽检和人工确认的学校级任务。公开表只保存动作、计数、集合 SHA、公开来源数量和非最终门禁，不保存复跑结果、人工核验结论或字段读数。
- `data/working/issue19-stable-foundation-school-source-refresh-public-ledger-summary.json`：高校侧辅证刷新摘要；记录 80 条公开任务、36 所学校、S0/S1/S2/S3/S4/S5 分布 15/12/23/11/14/5，源头 854 条 B0/B1 高校辅证任务，以及字段写回、推荐依据、学校专业建议、官网替代湖北官方计划和最终可用计数全部为 0。私有工作台 SHA 保存在摘要中，具体复跑和人工核验结果只在 Git 忽略目录。
- `data/working/issue19-school-source-auto-execution-batches-public-ledger.csv`：高校官网辅证自动执行批次公开账本，80 行；从高校官网辅证状态快照派生，覆盖 36 所学校和 7 条执行泳道，用于安排自动补源、补结构化、候选 diff 和人工最小核验。
- `data/working/issue19-school-source-auto-execution-batches-summary.json`：上述执行批次摘要；记录 17 条冲突回页、8 条官网补缺回页、12 条专业名归属、18 条补结构化、8 条继续找高校计划网源、16 条章程规则和 1 条留存观察，所有字段写回、推荐依据、学校专业建议、官网替代湖北官方计划和最终可用计数为 0。
- `data/working/issue19-school-source-latest-reconciliation-public-ledger.csv`：高校官网最新证据对齐公开账本，80 行；一行对应一条高校侧辅证自动执行任务，把 next20、live、C4/C6 复用、C4/C6 结构化 diff 和补源尝试的最新公开证据对齐到同一任务上，只保存计数、状态桶、证据来源族和非最终门禁。
- `data/working/issue19-school-source-latest-reconciliation-summary.json`：高校官网最新证据对齐摘要；记录 36 所学校、80 条任务、60 条已有湖北物理结构化或候选 diff 线索、12 条只有入口或探针记录、8 条暂无可复用高校侧计划源，以及 A4 继续补源任务中 4 条已推进、4 条仍需补源。字段写回、推荐依据、学校专业建议、官网替代湖北官方计划和最终可用计数全部为 0。
- `data/working/issue19-school-source-gap-priority-public-ledger.csv`：高校源缺口优先级公开清单，80 行；一行对应一条高校侧辅证自动执行任务，把冲突回页、OCR 补缺、专业名归属、补结构化、继续补源、章程规则和留存观察统一排成下一步执行顺序。
- `data/working/issue19-school-source-gap-priority-summary.json`：高校源缺口优先级摘要；记录 37 条人工先核回页、26 条自动补结构化或补源、17 条规则抽检或留存，以及 PDF 原页和湖北官方侧仍均需核验的非最终门禁。
- `data/working/issue19-school-source-e0-manual-page-review-queue-public-ledger.csv`：高校源 E0 人工回页桥接队列，37 行；从高校源缺口优先级清单筛出 E0 人工先核任务，并按院校代码旁挂同校第一闭环页列提示计数。
- `data/working/issue19-school-source-e0-manual-page-review-queue-summary.json`：上述 E0 队列摘要；记录 37 条 E0 任务、20 个院校代码、35 条有同校页列提示、2 条暂无同校页列提示、182 条同校第一闭环任务提示，以及全部非最终门禁。
- `data/working/issue19-c4-c6-school-source-acquisition-attempts-public-ledger.csv`：C4/C6 高校官网补源尝试公开账本，12 行；覆盖 12 所 C4/C6 D4/D5/D6 剩余补源缺口学校和 312 条相关私有明细。公开层只保存学校级 URL、既有入口证据、自动探针状态、补源建议、人工最小核验动作和非最终门禁，不保存逐专业候选值或登录态。
- `data/working/issue19-c4-c6-school-source-acquisition-attempts-summary.json`：C4/C6 高校官网补源尝试摘要；记录 12 所学校中 4 所有入口但尚未结构化、1 所需补 parser/匹配规则、7 所仍需继续找官方招生计划源，全部字段写回、推荐依据、学校专业建议、官网替代湖北官方计划和最终可用计数为 0。
- `data/working/issue19-stable-foundation-first-closure-detail-packet.csv`：稳定基座第一闭环明细包，206 行；只纳入 C0/C1/C7 官网辅证任务和 EXEC-01/02/03 P0 字段任务，用于先核最高风险冲突、补缺、未匹配和高校辅证线索。
- `data/working/issue19-stable-foundation-first-closure-page-side-packet.csv`：稳定基座第一闭环页列包，37 行；把 206 条明细任务聚合到 37 个 `PDF页码×版面列`，用于集中人工核 PDF 原页、湖北官方侧和高校官网辅证。
- `data/working/issue19-stable-foundation-first-closure-packet-summary.json`：第一闭环批次包摘要；记录 206 条明细、37 个页列、32 个 PDF 页、29 个计划数冲突或补缺页列、30 个双人复核页列，以及所有最终门禁为 0。
- `data/working/issue19-stable-foundation-first-closure-review-public-ledger.csv`：第一闭环复核材料公开账本，37 行；把第一闭环页列包接到 Git 忽略的私有 HTML/CSV 核页材料和 Overlay 状态机。公开表只保存页列计数、任务分布、材料 SHA、回链状态和非最终门禁，不保存页图路径、OCR 原文、人工读数或字段记录值。
- `data/working/issue19-stable-foundation-first-closure-review-summary.json`：第一闭环复核材料摘要；记录 37 个页列、32 个 PDF 页、206 条任务、105 条自动官网辅证任务、101 条人工字段任务、Q0/Q1/Q2 分布、私有材料 SHA、官方公开入口不可定稿和所有最终门禁为 0。
- `data/working/issue19-stable-foundation-first-closure-task-review-public-ledger.csv`：第一闭环任务级复核公开账本，206 行；一行对应一条第一闭环明细任务，把任务回连到页列复核材料、PDF 原页待核、湖北官方侧待核、高校辅证待核、公共高校来源文件 SHA、双人复核要求和人工最小动作。公开表不保存字段读数、页图路径、OCR 原文、私有 HTML/CSV 路径或人工复核记录。
- `data/working/issue19-stable-foundation-first-closure-task-review-summary.json`：第一闭环任务级复核摘要；记录 206 条任务、37 个页列、32 个 PDF 页、105 条自动官网辅证、101 条 P0 人工字段、74 条可作为核页提示的公共高校来源文件线索、91 条双人复核任务、206 条 PDF 原页和湖北官方侧必核任务，以及所有最终门禁为 0。
- `data/working/issue19-stable-foundation-first-closure-triage-prefill-public-audit.csv`：第一闭环私有预填公开审计，37 行；一行对应一个 `PDF页码×版面列`，只保存任务计数、高校侧辅证线索计数、私有页列 CSV SHA 和非最终门禁。候选计划数、学费、选科、OCR 候选、人工读数和复核结论只留在 Git 忽略的私有工作台。
- `data/working/issue19-stable-foundation-first-closure-triage-prefill-summary.json`：第一闭环私有预填摘要；记录 206 条私有任务行、37 个页列、74 条高校侧辅证候选线索、12 个公共高校来源文件和全部非最终门禁。该摘要只证明私有提示材料已生成，不确认字段事实。
- `data/working/issue19-stable-foundation-first-closure-execution-queue.csv`：第一闭环核验执行队列，37 行；把页列按 E0 冲突异常双人优先、E1 计划数补缺或偏大、E2 官网未匹配专业名归属排序，只保存页列顺序、计数、证据编号、SHA、完成条件和阻断原因。
- `data/working/issue19-stable-foundation-first-closure-execution-queue-summary.json`：第一闭环核验执行队列摘要；记录 37 个页列、206 条任务、E0/E1/E2 分布、Q0/Q1/Q2 分布、74 条公共高校来源文件任务、91 条双人复核任务和所有最终门禁为 0。该摘要不确认字段事实，不公开学校专业明细、候选值、人工读数、识别正文或私有路径。
- `data/working/issue19-first-closure-resolution-execution-overlay-v1.csv`：第一闭环准出执行叠加表，37 行；按第一闭环执行顺序，把事实准出页列汇总、核验结果页列汇总和公开证据地图合并，展示每个页列仍缺的 PDF 原页、湖北官方侧、高校辅证、冲突处理、双人复核、三方闭环、专业名归属和专业组边界事实数。
- `data/working/issue19-first-closure-resolution-execution-overlay-v1-summary.json`：第一闭环准出执行叠加摘要；记录 37 个页列、206 条任务、439 个事实范围，R0/R1/R2 波次为 10/9/18，所有自动闭环、字段写回、推荐依据、官网替代湖北官方计划、学校专业建议和最终可用门禁均为 0。
- `data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit.csv`：第一闭环 PDF OCR 候选公开审计，206 行；一行对应一条第一闭环任务，只公开 PDF OCR 候选是否存在、与高校辅证的关系桶、候选字段计数、冲突计数、证据编号和非最终门禁，不公开候选值、学校专业明细、识别正文或私有路径。
- `data/working/issue19-stable-foundation-first-closure-pdf-ocr-candidate-public-audit-summary.json`：第一闭环 PDF OCR 候选摘要；记录 103 条任务已有 PDF OCR 候选、103 条需人工看图、26 条 PDF OCR 与高校辅证冲突、13 条存在一致字段但仍需官方闭环、自动写入私有记录 0 和全部非最终门禁。私有候选工作台 SHA 保存在摘要中，候选明细只在 Git 忽略目录。
- `data/working/issue19-stable-foundation-first-closure-page-side-candidate-dashboard.csv`：第一闭环页列候选看板，37 行；把 206 条第一闭环任务聚合为 37 个 `PDF页码×版面列`，公开每个页列的 PDF OCR 候选、缺候选、冲突、一致、直接看图、双人复核和下一步动作计数。
- `data/working/issue19-stable-foundation-first-closure-page-side-candidate-dashboard-summary.json`：第一闭环页列候选看板摘要；记录 37 个页列、206 条任务、10 个先核冲突页列、21 个先人工看图页列、6 个按 PDF OCR 候选确认页列，以及全部非最终门禁。
- `data/working/issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit.csv`：第一闭环机器坐标候选公开审计，206 行；读取 P0 字段机器坐标候选表和第一闭环 PDF OCR 候选私有工作台，把 103 条原缺 PDF OCR 候选任务中的 49 条标为机器坐标候选待人工核页，公开层只保存状态桶、计数、证据编号和门禁。
- `data/working/issue19-stable-foundation-first-closure-machine-coordinate-candidate-public-audit-summary.json`：第一闭环机器坐标候选摘要；记录原缺 PDF OCR 候选 103 条、机器坐标可补候选 49 条、剩余缺候选 54 条、字段分布为专业计划数 44 条和学费 5 条。私有机器坐标候选工作台 SHA 保存在摘要中，字段明细只在 Git 忽略目录。
- `data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger.csv`：第一闭环字段确认公开账本，206 行；一行对应一条第一闭环任务，把任务级复核账本、PDF OCR 候选、机器坐标候选、页列候选看板和私有字段确认工作台接到同一个公开状态机。公开层只保存核验泳道、候选提示状态、PDF 原页/湖北官方/高校辅证私有记录状态、双人复核状态、三方一致性公开状态和非最终门禁，不保存任何候选值或人工字段值。
- `data/working/issue19-stable-foundation-first-closure-field-confirmation-public-ledger-summary.json`：第一闭环字段确认摘要；记录 206 条任务、37 个页列、32 个 PDF 页、PDF OCR 提示 103 条、机器坐标提示 49 条、高校辅证线索 74 条、直接看图 80 条、双人复核 91 条，以及 PDF 原页和湖北官方侧记录均待完成。字段写回、推荐依据、学校专业建议和最终可用仍全部为 0；私有字段确认工作台 SHA 保存在摘要中，具体读数只在 Git 忽略目录。
- `data/working/issue19-stable-foundation-first-closure-public-evidence-map.csv`：第一闭环公开证据地图，37 行；一行对应一个第一闭环 `PDF页码×版面列`，把 206 条任务压缩成页列级证据状态，公开显示 PDF/PDFOCR、机器坐标、高校辅证、湖北官方侧、冲突、直接看图、双人复核和阻断类型计数。该表不公开学校专业明细、候选值、人工读数、识别正文、私有路径或最终结论，只用于向家庭说明当前卡点在哪里。
- `data/working/issue19-stable-foundation-first-closure-public-evidence-map-summary.json`：第一闭环公开证据地图摘要；记录 37 个页列、206 条任务、32 个 PDF 页，E0/E1/E2 分布 18/11/8，PDFOCR 提示 103 条、无 PDFOCR 候选 103 条、机器坐标提示 49 条、高校侧公共来源任务 74 条、冲突 26 条、直接看图 80 条、双人复核 91 条，以及字段写回、推荐依据、学校专业建议和最终可用全部为 0。
- `data/working/issue19-stable-foundation-first-closure-next-action-matrix.csv`：第一闭环下一步动作矩阵，206 行；一行对应一条第一闭环任务，把证据状态、64 个小核验包和同校高校源最新证据合并为 N0-N5 核验动作层级，用于安排先双人核冲突、补缺回页、机器坐标辅助核页、人工看图、PDFOCR 候选确认或等待湖北官方侧。
- `data/working/issue19-stable-foundation-first-closure-next-action-page-summary.csv`：第一闭环下一步动作页列摘要，37 行；把 206 条动作矩阵任务压缩回 37 个 `PDF页码×版面列`，保留 N0-N5 分布、同校高校源可用性、关联 64 小包、页列主阻断和完成条件。
- `data/working/issue19-stable-foundation-first-closure-next-action-summary.json`：第一闭环下一步动作摘要；记录 N0 26 条、N1 35 条、N2 49 条、N3 54 条、N4 29 条、N5 13 条，PDF 原页和湖北官方侧待核均为 206，字段写回、推荐依据、学校专业建议和最终可用全部为 0。
- `data/working/issue19-stable-foundation-first-closure-field-fact-public-ledger.csv`：第一闭环字段事实公开账本，354 行；一行对应一个 `第一闭环任务ID×字段名`，把 206 条任务展开为专业计划数 170、学费 105、再选科目 77、待人工判定字段 2。公开层只保存字段名、状态、关系桶、ID 和 SHA，不保存字段明细值或人工记录。
- `data/working/issue19-stable-foundation-first-closure-field-fact-summary.json`：第一闭环字段事实摘要；记录 354 个字段原子全部为 `F0-字段记录未填写`，P0 top3 重点字段 36 个、B0 冲突页列字段 256 个、双人复核字段 119 个、人工看图字段 122 个；字段写回、推荐依据、学校专业建议、官网替代湖北官方计划和最终可用全部为 0。
- `data/working/issue19-stable-foundation-first-closure-fact-scope-gap-public-ledger.csv`：第一闭环事实范围缺口账本，439 行；一行对应一个待闭环事实范围，把字段事实 354、专业名归属 48、专业组边界 37 放在同一公开状态层。公开层只保存 ID、页列、状态桶、计数和 SHA，不保存学校专业明细、字段明细值、识别正文或私有材料。
- `data/working/issue19-stable-foundation-first-closure-fact-scope-gap-summary.json`：第一闭环事实范围缺口摘要；记录 439 个事实范围全部为 `F0-待原页与湖北官方侧闭环`，PDF 原页待核 439、湖北官方侧待核 439、双人复核事实 146、人工看图事实 152；字段写回、推荐依据、学校专业建议、官网替代湖北官方计划和最终可用全部为 0。
- `data/working/issue19-first-closure-fact-gate-public-ledger.csv`：第一闭环事实准入门禁账本，439 行；一行对应一个待闭环事实范围，公开展示其是否允许进入下一阶段。当前全部为 `blocked_not_ready_for_next_stage`，不公开字段值、不确认事实。
- `data/working/issue19-first-closure-fact-resolution-gate-v1-public-ledger.csv`：第一闭环事实准出门禁账本，439 行；一行对应一个待闭环事实范围，公开展示进入私有写回评审前仍缺的 PDF 原页、湖北官方侧、高校辅证、冲突处理、双人复核、三方闭环、专业名归属和专业组边界证据。当前准出、写回、推荐和最终可用计数均为 0。
- `data/working/issue19-first-closure-fact-resolution-gate-v1-page-summary.csv`：第一闭环事实准出页列汇总，37 行；按页列统计 439 个事实准出缺口，为准出执行叠加表提供页列级缺口来源。
- `data/working/issue19-first-closure-fact-resolution-gate-v1-task-summary.csv`：第一闭环事实准出任务汇总，206 行；按第一闭环任务统计 402 个带任务事实，另有 37 个专业组边界事实只保留在事实主表和页列汇总中。
- `data/working/issue19-first-closure-fact-resolution-gate-v1-summary.json`：第一闭环事实准出摘要；记录 439 个事实、37 个页列、206 个任务及 PDF 原页、湖北官方侧、三方闭环、冲突、双人复核、专业名归属和专业组边界待补计数。
- `data/working/issue19-first-closure-fact-gate-page-summary.csv`：第一闭环事实准入页列汇总，37 行；按 `PDF页码×版面列` 守恒统计事实范围、W0/B0、B0 冲突、双人复核、人工看图和 PDF/湖北官方待核数量。
- `data/working/issue19-first-closure-fact-gate-task-summary.csv`：第一闭环事实准入任务汇总，206 行；按第一闭环任务 ID 统计 402 个带任务事实，另有 37 个专业组边界事实在主表中无任务 ID。
- `data/working/issue19-first-closure-fact-gate-summary.json`：第一闭环事实准入摘要；记录 439 个事实、37 个页列、206 个任务，W0/B0 87、可高校源 double check 68、B0 冲突 275、双人复核 146、人工看图 373；所有推荐、写回、官网替代湖北官方计划和最终门禁均为 0。
- `data/working/issue19-stable-foundation-first-closure-fact-verification-packets-public-ledger.csv`：第一闭环事实核验包，37 行；一行对应一个 `PDF页码×版面列` 核验包，把 439 个事实缺口压缩为 B0 冲突优先、专业名归属优先、缺候选人工看图、机器坐标辅助四类波次。
- `data/working/issue19-stable-foundation-first-closure-fact-verification-items-public-ledger.csv`：第一闭环事实核验包明细，439 行；一行对应一个包内事实范围，逐项回链到事实范围缺口账本，并继承包序号、波次、页列主阻断和非最终门禁。
- `data/working/issue19-stable-foundation-first-closure-fact-verification-packets-summary.json`：第一闭环事实核验包摘要；记录 37 个核验包、439 个包内事实，波次分布为 B0 冲突优先 10、专业名归属优先 9、缺候选人工看图 2、机器坐标辅助 16；字段写回、推荐依据、学校专业建议、官网替代湖北官方计划和最终可用全部为 0。
- `data/working/issue19-stable-foundation-first-closure-w0-b0-minimal-manual-packets-public-ledger.csv`：第一闭环 W0/B0 最小人工复核包，10 行；一行对应一个 B0 冲突优先 `PDF页码×版面列`，把同页 275 个待核事实先压成 87 个核心事实的包级执行入口。
- `data/working/issue19-stable-foundation-first-closure-w0-b0-minimal-manual-items-public-ledger.csv`：第一闭环 W0/B0 最小人工复核明细，87 行；覆盖专业组边界 10、明确冲突字段 68、专业名归属 9，并逐项回链到第一闭环事实核验包明细。
- `data/working/issue19-stable-foundation-first-closure-w0-b0-minimal-manual-summary.json`：W0/B0 最小人工复核摘要；记录 10 个包、87 个核心事实、188 个同页伴生待核事实、35 个涉及任务，PDF 原页和湖北官方侧仍全部待核，字段写回和最终门禁全部为 0。
- `data/working/issue19-stable-foundation-first-closure-w0-b0-execution-prefill-packets-public-audit.csv`：第一闭环 W0/B0 执行预填包公开审计，10 行；把 10 个页列包接到私有页列 CSV、页图、OCR 文本和核心事实集合 SHA，公开层只保存状态、计数和哈希。
- `data/working/issue19-stable-foundation-first-closure-w0-b0-execution-prefill-items-public-audit.csv`：第一闭环 W0/B0 执行预填明细公开审计，87 行；一行对应一个核心事实，回链到最小人工复核明细、下一步动作矩阵、字段确认账本、PDFOCR 候选和机器坐标候选，并保存私有预填记录 SHA。
- `data/working/issue19-stable-foundation-first-closure-w0-b0-execution-prefill-summary.json`：W0/B0 执行预填审计摘要；记录 10 个页列私有 CSV、87 条私有预填记录、PDFOCR/机器坐标/高校辅证线索计数，字段写回、推荐依据、学校专业建议、官网替代湖北官方计划和最终可用全部为 0。
- `data/working/issue19-moe-unmatched-school-resolution-major-detail.csv`：教育部未匹配校名逐专业解析表，385 行；把 49 个未匹配院校代码+校名下沉到受影响的专业明细，提供历史同代码校名候选、教育部相似校名候选和 OCR 规则修正候选。所有行 `机器能否自动替换校名=false`。
- `data/working/issue19-moe-unmatched-school-resolution-summary.json`：未匹配校名解析摘要；记录历史同代码候选 281 条、教育部相似候选 232 条、OCR 规则修正候选 90 条、自动替换 0 条。该表只作核名派单，不写回最终校名。
- `data/working/issue19-hubei-official-query-key-collision-ledger.csv`：湖北官方查询键碰撞清单，118 行；记录 59 个 `院校代码+专业组代码+专业代号` 不唯一的官方查询三元组，防止未来按非唯一键回填官方系统结果。
- `data/working/issue19-hubei-official-query-key-collision-summary.json`：官方查询键碰撞摘要；记录碰撞键 59 个、碰撞行 118 条，所有行均需用 `专业行ID`、原页位置和官方返回行证据消歧。
- `data/working/issue19-major-line-layout-continuity-risk-ledger.csv`：专业行版面连续性风险清单，1934 条风险事件；只用公开原页锚点字段生成，检查专业起始行号、相邻 y 坐标、相邻行号递增和大跨度异常。
- `data/working/issue19-major-line-layout-continuity-risk-summary.json`：版面连续性风险摘要；记录 1541 条专业明细、351 个专业组涉及版面连续性风险，所有事件仅用于核页派单。
- `data/working/issue19-major-code-order-risk-ledger.csv`：专业代号顺序风险清单，355 条风险事件；用保守解析规则检查专业代号无法解析、相邻代号不递增和大跳变。
- `data/working/issue19-major-code-order-risk-summary.json`：专业代号顺序风险摘要；记录 574 条专业明细、220 个专业组涉及专业代号顺序风险。该表不判定 OCR 一定错误，只要求回看原页和湖北官方系统确认。
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
- `data/working/issue19-b0-b1-retained-official-plan-normalized.csv`：B0/B1 已留存官网/API/HTML/XLSX/PDF/图片/双表联合抽取证据标准化表，当前 446 条；字段包括学校、来源文件、证据类型、年份、省份、科类、专业、计划数、学费、校区、选科和来源局限。
- `data/working/issue19-candidate-v3-b0-b1-official-evidence-match.csv`：B0/B1 逐专业官网证据匹配表，覆盖 324 条招生明细；一行一个招生专业，带出页码、专业组、专业代号、OCR 专业名、OCR 计划数、官网匹配专业、官网计划数、匹配状态、计划数核验状态和仍需核验项。
- `data/working/issue19-candidate-v3-b0-b1-official-evidence-match-summary.json`：B0/B1 逐专业官网证据匹配摘要；当前 158 条专业名匹配，其中 66 条计划数与 OCR 一致，55 条为 OCR 缺失但官网可补，19 条官网未给可比计划数，19 条计划数存在差异，全部保持非最终结论。
- `data/working/issue19-b0-b1-plan-conflict-review-queue.csv`：B0/B1 计划数冲突复核队列，19 条；按 OCR 疑似误取学费、计划数不一致等类型安排核页顺序，并记录保真诊断和计划数候选引用方式。
- `data/working/issue19-b0-b1-unmatched-major-review-queue.csv`：B0/B1 官网证据未匹配专业复核队列，32 条；用于定位 OCR 噪声、串行、官网表未覆盖和关键限定词未覆盖问题。
- `data/working/issue19-b0-b1-official-source-gap-priority.csv`：B0/B1 学校补源缺口优先表，18 所；区分 7 所 P0 待补官方计划源、6 所已有官网线索但尚未结构化到逐专业证据的学校、5 所仅章程规则线索学校。
- `data/working/issue19-b0-b1-fidelity-review-summary.json`：B0/B1 保真复核队列摘要；只用于安排核页/补源，不是最终候选或填报方案。
- `data/working/issue19-candidate-v3-major-field-fidelity-ledger.csv`：候选 V3 全量逐专业字段保真总账，覆盖 8412 条招生明细；一行对应一个招生专业或 0 明细占位，合并 D0 原页证据、B0/B1 计划数冲突、官网未匹配、字段完整性、结构异常、费用底线、调剂风险和家庭底线，所有行均保持 `最终可用=false`。
- `data/working/issue19-candidate-v3-major-field-fidelity-ledger-summary.json`：全量逐专业字段保真总账摘要；记录 8412 行总账、8234 条高风险保真行、178 条暂未触发机器高风险行、18 条 B0/B1 计划冲突覆盖和 32 条 B0/B1 官网未匹配覆盖。
- `data/external/issue19-b0-b1-official-sources/xztu-2026-hubei-physics-plan-extracted.csv`：忻州师范学院官网 PDF 宽表抽取出的湖北物理类逐专业证据，15 条；作为 PDF 原件的可复跑抽取结果，不替代第 19 期原页和湖北官方系统。
- `data/external/issue19-b0-b1-official-sources/sdtbu-2026-hubei-physics-plan-extracted.csv`：山东工商学院官网 PDF 抽取出的湖北物理类逐专业证据，24 条；专业名来自 PDF 渲染图 Apple Vision OCR 并带 OCR 原文、置信度和校正说明，湖北计划数来自 PDF 网格数字列，不替代第 19 期原页和湖北官方系统。
- `data/external/issue19-b0-b1-official-sources/sdtbu-2026-pdf-ocr-grid-audit.csv`：山东工商学院官网 PDF 网格 OCR 审计表，42 条；保留每个有湖北计划数行的 PDF 表格行号、OCR 原文、校正说明、是否纳入湖北物理类匹配表。
- `data/external/issue19-b0-b1-official-sources/zjut-2026-province-major-plan.pdf`：浙江工业大学官网 2026 年分省分专业招生计划 PDF 原件；仅作高校侧辅证，不替代第 19 期原页和湖北官方系统。
- `data/external/issue19-b0-b1-official-sources/zjut-2026-hubei-physics-plan-extracted.csv`：浙江工业大学官网 PDF 抽取出的湖北物理类逐专业证据，12 条，计划数合计 48；另有 `zjut-2026-pdf-grid-audit.csv` 保留 PDF 网格审计记录。
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
- `scripts/build_issue19_p0_evidence_execution_packets.py`：从全量逐专业证据闭环任务队列抽取 P0 任务，按页码、学校、专业组和 P0 类型生成执行包；包 ID 只用于组织核验工作，不改变一行一个招生专业明细和一个证据项的任务粒度。
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
- `scripts/build_issue19_moe_school_attribute_major_detail.py`：读取教育部 2025 全国普通高等学校名单 XLS，生成教育部名单标准化表、逐专业学校属性核验表和未匹配学校支持清单；所有属性线索都下沉到 `专业行ID`，不生成学校级候选结论。
- `scripts/build_issue19_foundation_stability_dashboard.py`：生成底座稳定性总看板和教育部未匹配校名逐专业解析表；所有输出保持逐专业粒度、非最终门禁和 pending 边界。
- `scripts/build_issue19_foundation_stabilization_major_detail_tasks.py`：生成 B0/B1/B2 逐专业稳定化任务表；用于把底座保真任务落到招生专业明细，不生成学校/专业组层推荐。
- `scripts/build_issue19_official_public_entry_status_snapshot.py`：生成官方公开入口状态快照；只记录公开页面 `GET/200`、SHA、字节数、标题、入口角色、`can_finalize=false` 和无登录探针边界，不保存登录态。
- `scripts/build_issue19_official_unavailable_sampling_review_overlay.py`：读取官方不可得抽样执行明细，生成 155 条本地私有抽样复核 Overlay 和公开进度账本；公开层只保存 SHA、状态、计数和非最终门禁，人工读数和备注只进入 Git 忽略的本地表。
- `scripts/build_issue19_official_unavailable_sampling_review_packets.py`：读取官方不可得抽样复核 Overlay，把 155 条逐专业明细按 `PDF页码×版面列` 生成 46 个本地私有 HTML/CSV 核页包和公开页列包账本；公开层只保存计数、SHA 和状态，私有层承接页图、OCR 行、学校专业线索和人工填写栏。
- `scripts/build_issue19_official_unavailable_sampling_review_execution_queue.py`：读取抽样页列核验包、公开 Overlay 和本地私有 Overlay，生成 46 行页列执行队列和摘要；用于在官方结构化计划暂不可得时把自动高校辅证和最小人工核验排成可复跑顺序。
- `scripts/build_issue19_official_unavailable_sampling_triage_prefill.py`：读取官方不可得抽样页列执行队列、本地私有 Overlay 和官方入口活体复查，生成 46 行公开审计和 Git 忽略的 155 行私有预填工作台；高校官网与 OCR 线索只能作为人工核页提示，不确认字段事实。
- `scripts/build_issue19_major_source_evidence_risk_sidecar.py`：生成逐专业源证据风险侧账，把原始源证据风险、底座稳定性、闭环缺口和 P0 复核任务下沉到 `专业行ID`。
- `scripts/build_issue19_field_fact_closure_ledger.py`：生成字段事实闭环总账，逐专业汇总再选科目、专业计划数、学费的 OCR 候选、字段缺口候选、PDF/湖北官方待核状态和禁止写回边界。
- `scripts/build_issue19_field_fact_verification_tasks.py`：生成字段事实核验任务队列，把每条招生专业明细拆成再选科目、专业计划数、学费三项字段任务，并回连字段事实总账和页级保真队列。
- `scripts/build_issue19_field_fact_page_side_verification_queue.py`：生成全量字段页列核验队列，把 41208 条逐字段任务按 `PDF页码×版面列` 聚合成 462 个执行单元，用于全量核页排程和字段任务集合保真校验。
- `scripts/build_issue19_page_side_foundation_risk_register.py`：生成页列底座综合风险登记表，把字段页列队列和逐专业风险侧账汇总到 462 个 `PDF页码×版面列`，用于人工核页时同时看到字段、结构、源证据、官方消歧和决策闸门风险；公开输出只保留计数、分布、集合 SHA 和非最终门禁。
- `scripts/build_issue19_page_side_foundation_verification_batches.py`：生成页列底座核验批次表，把 462 个 `PDF页码×版面列` 风险登记单元按 25 个一批切成 19 批，保留批次聚合计数、风险登记集合 SHA 和全部非最终门禁，作为后续逐批核页和记录完成度的公开执行入口。
- `scripts/build_issue19_page_side_foundation_batch_execution_packets.py`：生成页列底座批次执行包，并在本地私有目录生成 19 份批次 HTML/CSV 核页材料；公开输出只保留私有材料证据编号、SHA、批次计数、状态和非最终门禁。
- `scripts/build_issue19_page_side_foundation_review_progress_ledger.py`：读取页列底座批次执行包和 Git 忽略的私有批次任务 CSV，生成 462 行页列底座公开核页进度账本；公开输出只保存填写状态、计数、证据编号和 SHA，不保存核页记录内容、字段值、识别行内容或页图路径。
- `scripts/build_issue19_page_side_foundation_field_clue_audit.py`：读取页列底座公开核页进度账本、字段事实核验任务队列和单一逐专业招生明细总工作台，生成 462 行页列字段线索公开审计，并在 Git 忽略的 `private/` 目录生成 19 份逐字段线索模板。公开输出只保存计数、状态桶和私有模板 SHA，不保存字段候选值、院校专业明细、OCR 原文或人工填写内容。
- `scripts/build_issue19_page_side_foundation_human_review_overlay.py`：读取页列字段线索公开审计和 Git 忽略的私有逐字段线索模板，生成 19 份私有人工复核 Overlay 和 462 行公开进度账本；机器线索模板保持不可变，人工读数、官方值、字段确认值和复核记录只进入私有 Overlay，公开层只保留计数、SHA 和非最终门禁。
- `scripts/build_issue19_page_side_foundation_batch_sample_review.py`：读取指定批次的私有字段线索模板和私有人工复核 Overlay，生成第 1 批样板复核公开审计和私有样板详表；样板只验证流程、分流和工作量，不自动写入正式 Overlay，不生成最终事实或志愿建议。
- `scripts/build_issue19_page_side_foundation_all_batch_review.py`：读取全 19 批私有字段线索模板和私有人工复核 Overlay，生成 462 行全批次公开复核账本和 19 份私有详表；公开层只保存计数、状态分布、SHA 和非最终门禁，用于证明全量字段任务已进入可复核流水线，不证明字段事实已核准。
- `scripts/build_issue19_major_evidence_level_routing.py`：读取单一逐专业招生明细总工作台、底座稳定性看板、决策闸门、字段事实闭环总账、B0/B1 高校官网差异账和三年投档旁挂表，生成 13736 行逐专业证据等级与核验路由表；用于在官方结构化计划不可得时自动分流高校官网 double check、P0/P1/P2/P3 人工核验和低风险抽检，不允许自动写回字段或生成志愿建议。
- `scripts/build_issue19_stable_foundation_screening_views.py`：读取单一逐专业总工作台、候选筛选准备表、字段事实闭环、证据路由、教育部学校属性、三年投档旁挂和家庭专业组筛选表，生成稳定基座逐专业/专业组筛选视图；用于后续筛学校、专业和专业组时统一查看家庭底线、字段缺口、学校属性、历史线索和整组调剂风险，不打开最终门禁，不替代湖北官方系统或省招办计划。
- `scripts/build_issue19_stable_foundation_next_closure_workbench.py`：读取稳定基座筛选视图、逐专业证据路由、B0/B1 高校官网证据旁挂、P0 字段确认账本、P0 页列进度和湖北官方公开入口状态，生成 854 行自动官网辅证交叉核验工作台、319 行最小人工闭环工作台和摘要；用于把官方公开结构化源暂不可得时的 double check 与人工核页路径落成可复跑任务表。
- `scripts/build_issue19_stable_foundation_school_source_refresh_queue.py`：读取稳定基座自动官网辅证交叉核验工作台、B0/B1 高校官网补源种子表和湖北官方公开入口状态，生成 78 行高校侧辅证刷新公开账本，并在 Git 忽略目录生成私有复跑/人工核验工作台；用于把学校官网 double check 自动化、抽检和补源任务降到学校级，不确认字段事实。
- `scripts/build_issue19_c4_c6_school_source_refresh_execution_packets.py`：读取高校侧辅证刷新公开账本、稳定基座自动交叉核验工作台和高校官网补源种子表，把 C4/C6 最大补源缺口拆成 36 个公开执行包和 Git 忽略的 601 条私有逐专业明细；用于并行补源、补结构化和生成后续 diff，不写回字段事实。
- `scripts/build_issue19_c4_c6_retained_source_reuse_audit.py`：读取 C4/C6 执行包、私有逐专业明细、已留存官网标准化证据和全量字段保真总账，生成 C4/C6 已留存官网源复用公开审计和 Git 忽略的逐专业候选明细；用于确定哪些包可直接生成候选 diff，仍不写回字段事实。
- `scripts/fetch_issue19_c4_c6_blcu_official_source.py`：抓取北京语言大学招生系统 2026 湖北物理类普通类计划 API，留存原始 JSON 并生成公开抓取账本；该源只作高校侧辅证，不替代湖北省招办计划。
- `scripts/fetch_issue19_c4_c6_xauat_official_source.py`：抓取西安建筑科技大学招生系统 2026 湖北物理类普通类计划 API，留存原始 JSON 并生成公开抓取账本；该源只作高校侧辅证，不替代湖北省招办计划。
- `scripts/build_issue19_c4_c6_structured_candidate_diff.py`：读取 C4/C6 执行包、私有逐专业明细、既有官网标准化证据、新增高校官网源和全量字段保真总账，生成结构化候选 diff 公开账本与 Git 忽略的逐专业候选明细；用于官方不可得时自动 double check 并最小化人工核验。
- `scripts/build_issue19_c4_c6_school_source_acquisition_attempts.py`：读取 C4/C6 结构化候选 diff、C4/C6 执行包和高校官网补源种子表，生成学校级补源尝试公开账本；记录自动探针状态、既有入口证据、自动补源建议和人工最小核验动作，不确认逐专业字段事实。
- `scripts/build_issue19_school_source_latest_reconciliation.py`：读取高校官网辅证自动执行批次、next20 探测、live 补源、C4/C6 复用审计、结构化候选 diff 和补源尝试账本，生成 80 行高校官网最新证据对齐账本；用于识别哪些高校侧任务已经推进、哪些仍需补源或解析，不确认字段事实。
- `scripts/build_issue19_school_source_gap_priority_ledger.py`：读取高校官网最新证据对齐账本、状态快照、自动执行批次、C4/C6 结构化候选 diff 和补源尝试账本，生成 80 行高校源缺口优先级清单；用于固定下一步人工回页、自动补结构化、继续补源和章程规则核验顺序，不确认字段事实。
- `scripts/build_issue19_school_source_e0_manual_page_review_queue.py`：读取高校源缺口优先级清单和第一闭环下一步动作矩阵，生成 37 行 E0 人工回页桥接队列；用于固定人工先核任务和同校页列提示，不确认字段事实。
- `scripts/build_issue19_school_source_adapter_diff_execution_workbench_v1.py`：读取高校官网结构化接入候选、进度看板、最新对齐账本和自动执行批次，生成 12 行 Adapter/Diff 执行工作台；用于安排 adapter、parser、normalized bridge 和候选 diff，不公开学校名、专业名、字段明细或证据路径。
- `scripts/build_issue19_school_source_adapter_parse_audit_v1.py`：读取高校源 Adapter/Diff 执行工作台、结构化接入候选账本和既有 parser，对 12 个高校侧来源实际跑 JSON/PDF_CSV/XLSX 解析审计；公开层只保存解析计数、字段覆盖、证据 SHA、非计划规则侧证计数和非最终门禁，不公开学校名、专业名、字段明细或证据路径。
- `scripts/build_issue19_school_source_adapter_candidate_diff_v1.py`：读取 Adapter 解析审计账本、结构化接入候选、单一逐专业招生明细总工作台和既有匹配函数，生成 12 行公开候选 diff 账本，并在 Git 忽略私有目录写出 326 行 normalized 高校源和 344 行逐专业 diff 明细；公开层只保存计数、SHA 和非最终门禁。
- `scripts/build_issue19_first_closure_verification_result_board.py`：读取第一闭环下一步动作矩阵、页列下一步汇总、证据状态账本、字段事实核验任务和 E0 人工回页队列，生成 206 行任务级核验结果看板和 37 行页列汇总；用于统一展示 PDF/OCR/机器坐标/高校官网/湖北官方/冲突状态，不确认字段事实。
- `scripts/build_issue19_first_closure_field_verification_status.py`：读取第一闭环下一步动作矩阵、字段事实核验任务和 E0 人工回页队列，把 206 条组合任务拆成 354 个字段级公开状态；只保存状态、ID、计数和动作，不保存字段读数或候选文本。
- `scripts/build_issue19_school_source_progress_board.py`：读取高校官网辅证自动执行批次、高校源最新对齐账本和 C4/C6 执行包，生成 80 行高校官网辅证进度看板；用于按 L3/L1/L0、来源形态、留存状态和下一批动作继续推进 double check。
- `scripts/build_issue19_round4_family_explanation_board.py`：读取 Round4 重点 55 组、暂缓 65 组和优先 120 组，生成家庭阅读说明表和工作簿；用于解释为什么入选、为什么暂缓、完整组内专业接受度和调剂风险，不作为定稿依据。
- `data/working/issue19-first-closure-verification-result-public-ledger.csv`：第一闭环 206 条最高风险明细的任务级核验结果看板。
- `data/working/issue19-first-closure-verification-result-page-summary.csv`：第一闭环 37 个页列的核验结果页列汇总和建议人工小包。
- `data/working/issue19-first-closure-field-verification-status-public-ledger.csv`：第一闭环 354 个字段级待核状态，拆分专业计划数、学费、再选科目和待人工判定字段。
- `data/working/issue19-school-source-progress-board-public-ledger.csv`：80 个高校官网辅证任务的最新进度看板。
- `data/exports/issue19-round4-family-explanation-board.xlsx`、`data/exports/issue19-round4-family-explanation-board.csv`、`data/exports/issue19-round4-family-explanation-focus55.csv`、`data/exports/issue19-round4-family-explanation-paused65.csv`：Round4 120 组家庭阅读说明表，重点 55 与暂缓 65 分开保存。
- `scripts/build_issue19_stable_foundation_first_closure_packet.py`：读取稳定基座下一步闭环工作台，把最高优先级 C0/C1/C7 官网辅证任务和 EXEC-01/02/03 P0 字段任务合并成 206 条明细任务和 37 个页列执行包。
- `scripts/build_issue19_first_closure_review_materials.py`：读取第一闭环明细包、页列包、页列底座公开进度账本、字段线索审计、人工复核 Overlay、官方入口状态和私有 OCR 证据，生成第一闭环公开复核账本，并在 Git 忽略的 `private/` 目录生成 37 份页列 HTML/CSV 核页材料。
- `scripts/build_issue19_first_closure_task_review_ledger.py`：读取第一闭环明细包、页列包、第一闭环复核公开账本和官方入口状态，生成 206 行任务级公开复核账本；公共高校来源文件只公开相对路径和 SHA，字段读数、OCR 原文、页图路径和人工记录继续留在私有复核材料。
- `scripts/build_issue19_first_closure_private_triage_prefill.py`：读取第一闭环明细包、任务级复核公开账本、页列复核公开账本和官方入口状态，生成 37 行公开审计和 Git 忽略的私有预填工作台；高校侧候选值只能作为私有核页提示，不写入公开字段事实或最终门禁。
- `scripts/build_issue19_first_closure_execution_queue.py`：读取第一闭环页列包、页列复核公开账本、任务级复核公开账本、私有预填公开审计和官方入口状态，生成 37 行公开执行队列；用于压缩人工核验路径和固定执行顺序，不能替代 PDF 原页、湖北官方侧或高校官网/章程闭环。
- `scripts/build_issue19_first_closure_pdf_ocr_candidate_audit.py`：读取第一闭环执行队列、任务级复核公开账本、私有复核材料和私有预填工作台，生成 206 行 PDF OCR 候选公开审计和 Git 忽略的私有候选工作台；公开输出只保存状态桶和计数，候选明细不能自动写回人工记录。
- `scripts/build_issue19_first_closure_page_side_candidate_dashboard.py`：读取第一闭环执行队列和 PDF OCR 候选公开审计，生成 37 行页列候选看板；用于把任务级候选状态聚合成页列级核验动作，不确认字段事实。
- `scripts/build_issue19_first_closure_machine_coordinate_candidate_audit.py`：读取第一闭环 PDF OCR 候选公开/私有工作台和 P0 字段机器坐标候选表，生成 206 行机器坐标候选公开审计和 Git 忽略的私有候选工作台；用于把部分缺 PDF OCR 候选任务转成机器坐标候选待人工核页，不能自动写回字段或替代湖北官方计划。
- `scripts/build_issue19_first_closure_public_evidence_map.py`：读取第一闭环页列证据状态汇总、任务复核公开账本、私有预填公开审计和官方入口状态，生成 37 行页列级公开证据地图；用于说明每个页列卡在 PDF/PDFOCR、机器坐标、高校辅证、湖北官方侧、冲突或双人复核哪一步，不确认字段事实。
- `scripts/build_issue19_first_closure_next_action_matrix.py`：读取第一闭环证据状态报告、页列汇总、高校源最新证据对齐账本和 64 个小核验包，生成 206 行下一步动作矩阵和 37 行页列摘要；用于把字段核验动作排成 N0-N5，不确认字段事实。
- `scripts/build_issue19_first_closure_field_fact_public_ledger.py`：读取第一闭环字段确认公开账本、证据状态、下一步动作矩阵、P0 top3 字段账本、B0 冲突页列账本和 Git 忽略的私有字段工作台，生成 354 行字段原子公开账本；公开层只同步状态和 SHA，不公开字段明细值。
- `scripts/build_issue19_first_closure_fact_scope_gap_ledger.py`：读取第一闭环字段事实账本、下一步动作矩阵、页列动作汇总和证据状态报告，生成 439 行事实范围缺口账本；用于把字段事实、专业名归属和专业组边界三类待闭环事实放到同一个公开状态层，不确认字段事实。
- `scripts/build_issue19_first_closure_resolution_execution_overlay_v1.py`：读取第一闭环执行队列、事实准出门禁账本、事实准出页列汇总、核验结果页列汇总和公开证据地图，生成 37 行准出执行叠加表；用于把 439 个事实准出缺口压回页列执行顺序，安排下一轮补证闭环，不确认字段事实。
- `scripts/build_issue19_first_closure_fact_evidence_channel_workbench_v1.py`：读取第一闭环事实准出门禁、准出执行叠加表、核验结果看板、字段级公开状态和高校官网辅证进度看板，生成 439 行事实证据通道工作台；用于把每个事实范围接到 PDF/OCR/机器坐标/高校官网/湖北官方/冲突/双人复核/三方闭环通道并安排下一步最小核验动作，不确认字段事实。
- `scripts/build_issue19_first_closure_fact_verification_packets.py`：读取事实范围缺口账本、下一步动作矩阵、页列动作汇总、公开证据地图和页列证据汇总，生成 37 个页列核验包和 439 个包内事实项；用于安排人工核页、双人复核和并行处理顺序，不确认字段事实。
- `scripts/build_issue19_first_closure_w0_b0_minimal_manual_checklist.py`：读取第一闭环事实核验包、包内事实明细和 B0 冲突页列核验状态，生成 10 个 W0/B0 最小人工复核包和 87 个核心事实项；用于先核专业组边界、明确冲突字段和专业名归属，不确认字段事实。
- `scripts/build_issue19_first_closure_w0_b0_execution_prefill_audit.py`：读取 W0/B0 最小人工复核包、B0 冲突页列状态、公开证据地图、下一步动作矩阵、字段确认账本、PDFOCR/机器坐标候选和 Git 忽略的私有工作台，生成 10 行执行预填包审计、87 行执行预填明细审计和本地私有页列 CSV；用于人工打开私有材料核 PDF 原页，不确认字段事实。
- `scripts/build_issue19_field_fact_p0_reread_worklist.py`：生成 P0 字段原页重读工作清单，只抽取 K0 无候选字段任务，并补齐原始源证据、PDF 锚点和页级保真证据回连。
- `scripts/build_issue19_field_fact_p0_reread_machine_candidates.py`：生成 P0 字段机器坐标候选表，从私有 OCR 窗口中按字段坐标规则抽取专业计划数、再选科目和学费候选；公开输出不包含私有路径、页图或 OCR 原文，所有候选仍必须人工核 PDF 原页并用湖北官方系统或省招办计划确认。
- `scripts/build_issue19_field_fact_p0_closure_action_workbench.py`：生成 P0 字段闭环推进工作台，把机器候选分成快速候选核页、冲突候选核页和无候选重读批次，并预留 PDF 人工读数、湖北官方字段值和高校官网/章程辅证字段值。
- `scripts/build_issue19_field_fact_p0_semantic_crosssource_audit.py`：生成 P0 字段语义与多源线索审计表，把机器候选语义异常、计划数偏大、高校官网/章程字段补缺线索和机器/高校辅证冲突标到同一条字段任务；公开输出仍不写回字段事实。
- `scripts/build_issue19_field_fact_p0_triage_execution_workbench.py`：生成 P0 字段三方核验执行工作台，把 11444 条 P0 字段任务排成稳定执行顺序，并逐行回连 PDF 原页锚点、湖北官方待核包和高校辅证线索；公开输出仍不写回字段事实。
- `scripts/build_issue19_field_fact_p0_immediate_review_packet.py`：从 P0 字段三方核验执行工作台中严格切出 `EXEC-01/02/03/04` 的 319 条即时复核任务，保留父表来源 ID、证据编号、机器候选、高校辅证和湖北官方待核状态，并继续锁定全部非最终门禁。
- `scripts/build_issue19_p0_immediate_pdf_crop_evidence_index.py`：为 P0 字段即时复核包的 319 条任务生成本地 PDF 原页裁图，并写出公开裁图证据索引；脚本会校验页图 SHA、页级 manifest、专业行原页证据锚点和裁图 bbox，只公开证据编号、哈希和坐标摘要。
- `scripts/build_issue19_p0_immediate_three_way_closure_ledger.py`：把 P0 字段即时复核包、裁图证据索引和 B0/B1 高校官网辅证旁挂表合成 319 行 P0 即时三方闭环公开账本，同时生成本地私有三方读数模板；公开输出只保存证据编号、哈希、bbox、状态和门禁，不保存字段读数或复核备注。
- `scripts/build_issue19_p0_immediate_crop_ocr_audit.py`：读取 319 张私有裁图的 Apple Vision OCR 结果，生成公开裁图 OCR 审计表和本地私有读数候选表；公开输出只保存 OCR 状态、关系、SHA 和门禁，不保存识别文本、候选读数或图片路径。
- `scripts/build_issue19_p0_immediate_field_confirmation_workbench.py`：生成 P0 即时字段确认公开账本和本地私有字段确认工作台；私有表承接 PDF 原页、湖北官方、高校辅证和双人复核记录，公开表只同步状态机和门禁，不同步字段记录值。
- `scripts/build_issue19_p0_immediate_page_review_packets.py`：读取 P0 即时字段确认公开账本、本地私有裁图索引和私有字段确认工作台，生成 148 个 `PDF页码×版面列` 核页执行包；公开输出只保存聚合状态和证据哈希，私有目录生成本地 HTML/CSV 审阅材料。
- `scripts/build_issue19_p0_immediate_page_execution_queue.py`：读取 P0 即时按页核页包和 P0 即时 PDF 原页读数候选公开审计，把 148 个 `PDF页码×版面列` 包按候选冲突、无稳定候选、候选一致待官方闭环和常规人工确认重新排序；公开输出只保存执行顺序、任务数、证据编号、SHA、bbox 和非最终门禁。
- `scripts/build_issue19_p0_immediate_page_execution_progress_ledger.py`：读取 P0 即时页列核页执行队列、公开字段确认账本和 Git 忽略的私有字段确认工作台，生成不含私有值的页列进度公开账本。
- `scripts/issue19_review_rules.py`：第 19 期候选工作台和复核队列共用的风险标签、风险等级、SHA 和行数记录规则。
- `data/working/historical-preferred-city-pool-2023-2025.tsv`：按早期提到的成都、西安、武汉、北京生成的三年历史投档候选池，只用于复现历史候选发现；Round3 当前不按城市加分或设名额，进入后续讨论前必须回看官方原件、2026 招生计划和招生章程。
- `data/working/candidate-pool-v1.csv`：第一版可讨论候选池，20 条，全部为 `needs_2026_plan_verification`。

## 2026-06-29 新增执行与接入产物

- `scripts/build_issue19_first_closure_manual_verification_workbook.py`：生成 `data/exports/issue19-first-closure-manual-verification-workbook.xlsx`、37 行页列核验包、206 行任务核验项和 354 行字段核验项；用于把第一闭环人工核验拆成可执行清单，公开层不保存具体核验内容、OCR 原文、截图路径或最终结论。
- `scripts/build_issue19_priority55_family_major_decision_workbook.py`：生成 `data/exports/issue19-priority55-family-major-decision-workbook.xlsx`、55 行组汇总和 458 行逐专业家庭标注表；用于家庭先标“可接受/勉强接受/不能接受/待了解”和服从调剂态度，不确认招生计划字段。
- `scripts/build_issue19_school_source_structured_ingestion_candidates.py`：生成 `data/working/issue19-school-source-structured-ingestion-candidates-public-ledger.csv`、summary 和 Excel；优先列出兰州大学、武汉轻工大学、湖北师范大学、西安建筑科技大学、北京语言大学、天津外国语大学、忻州师范学院、西安航空学院、江汉大学、喀什大学、山东工商学院、杭州电子科技大学 12 所已有公开结构化/半结构化源的下一步接入动作。
- `scripts/build_issue19_first_closure_fact_evidence_channel_workbench_v1.py`：生成 `data/working/issue19-first-closure-fact-evidence-channel-workbench-v1-public-ledger.csv` 和 summary，将 439 个事实范围按事实级证据通道展开；公开层不保存学校名、专业名、字段值、OCR 原文、图片路径、人工记录或登录态，`同校高校源*` 仅是同校上下文计数，不能跨事实行求和。
- `scripts/build_issue19_first_closure_fact_action_packets_v1.py`：生成 `data/working/issue19-first-closure-fact-action-packets-v1-public-ledger.csv` 和 summary，将 439 个事实范围压成 79 个 `页列×事实核验动作组` 执行包；公开层只保存状态、计数、集合 SHA 和下一步动作，不保存学校名、专业名、字段值、OCR 原文、图片路径、人工记录或登录态。
- 上述产物均继承第 19 期 PDF SHA `ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d`，并保持字段写回、推荐依据、学校专业建议、官网替代湖北官方计划和最终可用门禁为 `false` 或 0。

## 使用优先级

1. 最终录取判断：湖北官方投档线、2026 湖北招生计划、高校招生章程。
2. 分数位次换算：湖北官方一分一段为主，static-data.gaokao.cn 作为交叉校验。
3. 专业名称和代码：教育部 2026 本科专业目录为准。
4. 候选发现和辅助理解：千问高考、阳光高考页面、其他第三方工具。

第三方工具的推荐概率、预测分和默认排序均不得直接进入最终方案，除非已用官方原件和招生章程复核。
