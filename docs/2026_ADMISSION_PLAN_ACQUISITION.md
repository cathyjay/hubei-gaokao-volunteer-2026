# 2026 招生计划获取状态

最后更新：2026-06-28

## 一、为什么必须获取 2026 招生计划

历年投档线只能判断大致位次风险，不能替代 2026 年实际招生计划。最终每个院校专业组必须核验：

- 2026 院校专业组代码。
- 组内全部专业。
- 每个专业计划人数。
- 选科要求。
- 学费、学制、校区。
- 中外合作、定向、专项、预科、民族班、地方限制、体检或单科等备注。

只有拿到这些信息，才能判断一个专业组是否能服从调剂。

## 二、官方来源状态

| 来源 | URL 或位置 | 当前状态 | 用途 |
| --- | --- | --- | --- |
| 湖北省教育厅高校招生专题 | https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/ | 2026-06-28 复核：官方专题页列出“湖北省招生数智综合平台”入口 | 证明平台入口属于官方招生服务链路 |
| 湖北教育考试网招生计划专题 | http://www.hbccks.cn/html/gkgzzt/gkzsjh/ | 已留存索引页；2026-06-28 公开 HTTP 复核返回 200，SHA 与 2026-06-27 留存一致 | 官方公开入口 |
| 2026 年普通高等学校招生计划页面 | http://www.hbccks.cn/html/gkzsjh/2026-05/142888.html | 2026-06-28 公开 HTTP 复核返回 200，但页面仍显示“持续更新中，敬请期待”；`can_finalize=false` | 等待官方公开完整计划 |
| 湖北招生数智综合平台 | https://zspt.hubzs.com.cn | 2026-06-28 首页已留存，公开 HTTPS 返回 200；首页只证明平台入口可访问 | 官方志愿系统和智能参考系统 |
| 平台计划查询接口 | `/prod-api/planQuery/plan/*` | 无登录请求返回 `401 令牌不能为空`；活体复查覆盖 `nfs`、`yxList`、`group`、`student`、`dict/pcdm`；已写可复跑抓取脚本 | 需要考生登录态或平台权限 |
| 湖北招生考试网 2026 填报时间安排 | https://www.hbksw.com/info/6/2270.html | 2026-06-28 复核：说明考生可通过数智平台的“志愿填报智能参考系统”查询招生计划、章程和近 2 年投档最低分 | 官方平台用途说明 |
| 湖北招生考试网 2025 辅助工具提醒 | https://www.hbksw.com/info/15/1846.html | 2026-06-28 复核：提醒正式填报的院校专业组代号、包含专业、选科要求等以高校当年确定、《湖北招生考试》杂志公布的当年招生计划为准 | 明确第三方/辅助工具不能替代当年计划 |
| 《湖北招生考试》杂志 | 第 13、16、19、22 期 | 需人工获取 | 官方纸质/电子招生计划来源 |
| 第 16/19 期专项检索 | `docs/HUBEI_ADMISSION_MAGAZINE_SEARCH.md` | 未找到公开完整电子版 | 获取路径和线索记录 |
| 高校官网招生计划 | 学校本科招生网 | 已发现部分高校发布 2026 计划 | 只能作为交叉校验 |

本地证据：

- `data/official/hubei-2026-admission-plan-platform/hbccks-plan-index.html`
- `data/official/hubei-2026-admission-plan-platform/hbccks-2026-plan-page.html`
- `data/official/hubei-2026-admission-plan-platform/index.html`
- `data/official/hubei-2026-admission-plan-platform/index-live-20260627.html`
- `data/official/hubei-2026-admission-plan-platform/index-live-20260628.html`
- `data/official/hubei-2026-admission-plan-platform/assets/`
- `data/official/hubei-2026-admission-plan-platform/api-probes/`
- `data/working/issue19-official-public-entry-status.json`
- `data/working/issue19-official-public-entry-live-recheck.json`
- `data/working/issue19-official-unavailable-sampling-gates.csv`
- `data/working/issue19-official-unavailable-sampling-gates-summary.json`
- `data/working/issue19-official-unavailable-sampling-execution-detail.csv`
- `data/working/issue19-official-unavailable-sampling-execution-detail-summary.json`
- `data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv`
- `data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger-summary.json`
- `data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv`
- `data/working/issue19-official-unavailable-sampling-review-packets-public-ledger-summary.json`
- `data/working/issue19-official-unavailable-sampling-review-execution-queue.csv`
- `data/working/issue19-official-unavailable-sampling-review-execution-queue-summary.json`
- `data/working/issue19-official-unavailable-sampling-triage-prefill-public-audit.csv`
- `data/working/issue19-official-unavailable-sampling-triage-prefill-summary.json`
- `data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv`
- `data/working/issue19-c4-c6-school-source-refresh-execution-packets-summary.json`
- `data/official/hubei-2026-volunteer-policy/143022-policy.html`
- `data/external/school-plan-crosschecks/`

补充说明：湖北教育考试网招生计划页面当前使用 HTTP 地址留存；同路径 HTTPS 抓取存在证书主机名不匹配问题，不能因此判断页面不存在。
`issue19-official-public-entry-status.json` 只记录公开入口状态和无登录探针结果；`issue19-official-public-entry-live-recheck.json` 用当前网络重新核对入口 SHA 和无登录接口状态。两者能说明现阶段官方公开入口尚不足以直接定稿，不能替代第 19 期逐专业招生明细和湖北官方系统字段核验。
若湖北官方系统在决策窗口内仍无法无登录自动取得，项目不绕过登录、不把高校侧来源当作省招办计划替代品；对应状态必须标记为 `official_system_unavailable` 或同等不可得状态，继续回到第 19 期 PDF 原页或纸质原页双人复核，并在湖北官方系统可得时补核。
2026-06-28 外部证据复核结论：截至本次复核，没有发现无需登录即可公开批量获取“2026 湖北本科普通批首选物理逐专业招生计划明细”的湖北官方网页、PDF、Excel 或开放接口；官方平台能查计划，但需要考生登录/验证，适合作为人工取证或导出截图的来源，不适合作为公开自动化抓取源。

## 三、已发现的平台接口

从湖北招生数智综合平台 2026-06-27 前端资源中发现以下只读计划查询接口；2026-06-28 首页已重新留存，但无登录探测边界不变：

- `/prod-api/planQuery/plan/nfs`
- `/prod-api/planQuery/plan/yxList?nf=2026&keyword=...&limit=...`
- `/prod-api/planQuery/plan/group`
- `/prod-api/planQuery/plan/student`
- `/prod-api/planQuery/plan/jzjt`
- `/prod-api/planQuery/dict/...`

本次留存的当前前端资源和 SHA256：

| 文件 | SHA256 | 用途 |
| --- | --- | --- |
| `data/official/hubei-2026-admission-plan-platform/index-live-20260627.html` | `253e6dd5c05c99af0ca9f52ee72182fcdcb70f188eae1bd88df456009dc6298d` | 当日平台首页快照 |
| `data/official/hubei-2026-admission-plan-platform/index-live-20260628.html` | `6dade2ef84ab249dd9d700a24e98c63f40f8305bba2bb6250acbf8cf10fcaba3` | 2026-06-28 平台首页快照；不能证明结构化计划可无登录取得 |
| `data/official/hubei-2026-admission-plan-platform/assets/index-Cut-ZwER.js` | `191ac7517cf0c9ea22cb82d98c381664ba439ffe485936b600405b92593e4de4` | 当前主入口资源，含请求封装 |
| `data/official/hubei-2026-admission-plan-platform/assets/planQuery-DaPwtzYm.js` | `1013eb61f6f142b97d439269397b4674d778cf2c00483120462d83748cfd90ee` | 当前计划查询接口定义 |
| `data/official/hubei-2026-admission-plan-platform/assets/planQueryDicts-CJncJeD8.js` | `3ba9e346cea6e9f44f4a5f2c6b00f4a021678006a6cc8a295ddddc2d439d09f4` | 当前计划查询字典辅助 |
| `data/official/hubei-2026-admission-plan-platform/assets/index-BjY7ltef.js` | `63e980b0c2d033d8cfcc5e46c21690abd9f2b776d940a1f02be7d75d67358522` | 当前计划查询页面实现 |
| `data/official/hubei-2026-admission-plan-platform/assets/jhcxtc-DB-omj6U.js` | `0f645c97ba0a7baacb61a7dae38dbb40bb51b4014080ee60e92dfb82b3f6c3cf` | 志愿参考/体检等弹窗资源 |
| `data/official/hubei-2026-admission-plan-platform/assets/jhcxsc-q90d6UCp.js` | `6f032912cd9d0c128c7df2bb5408c1d6372d98d30b27079d0428904407985298` | 收藏页资源 |

当前接口契约：

- 请求前缀为 `/prod-api`。
- 登录 token 来源为 `Admin-Token`，请求头为 `Authorization: Bearer <Admin-Token>`。
- 计划主查询页调用 `/planQuery/plan/group`，页面参数包括 `nf`、`pcdm`、`kldm`、`pageNum`、`pageSize`、`yxglzc`、`yxzyzdh`、`zyglzc1-4`、`ssdmlb`、`bxxzdmlb`、`sfsyl`、`sxzylblb`、`sxjhlblb`、`xkkmglfs`、`xkkmdmlb`，有权限时还会带 `verifyCode`。
- 返回列表按层级组织，`type=YX` 为院校行，`type=ZYZ` 为院校专业组行，`type=ZY` 为招生专业行。后续结构化时只把 `type=ZY` 作为真实招生明细，专业组无专业行时只输出 0 明细占位。

直接无登录请求会返回：

```json
{"code":401,"msg":"令牌不能为空"}
```

结论：平台计划查询目前需要登录态，不能在项目里直接公开抓取完整 2026 计划。

无登录探测结果已留存在：

- `data/official/hubei-2026-admission-plan-platform/api-probes/planQuery-plan-nfs-no-token.json`
- `data/official/hubei-2026-admission-plan-platform/api-probes/planQuery-plan-yxList-2026-wuhan-no-token.json`
- `data/official/hubei-2026-admission-plan-platform/api-probes/planQuery-plan-group-current-no-token.json`
- `data/official/hubei-2026-admission-plan-platform/api-probes/planQuery-dict-pcdm-2026-no-token.json`
- `data/official/hubei-2026-admission-plan-platform/api-probes/planQuery-plan-student-no-token.json`

上述无登录探测 JSON 的 SHA256 均为 `02f44fe53c8befdb83267ceb719f3d697cfa51d39ffa6995a726f017f8425b8f`，内容均为 `{"code":401,"msg":"令牌不能为空"}`。

## 四、官方结构化计划暂不可得时的保真办法

当前能自动取得的是官方入口证据，不是可定稿的官方逐专业结构化明细。若决策窗口内仍无法直接取得湖北官方系统导出的结构化计划，底座按降级闭环推进：

- 已新增 `data/working/issue19-major-evidence-level-routing.csv` 作为官方不可得时的逐专业核验导航。它覆盖全部 13736 条招生专业明细，当前 L3 高校辅证 854 条、L4 OCR 或单源线索 12882 条；P0 100% 人工核验 5043 条、P1 页列集中核验 7952 条、P2 自动官网核验后人工确认 557 条、P3 低风险抽检 184 条。该表只安排证据等级、自动 double check 和人工核验顺序，不确认字段值。
- 已新增 `data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv` 作为高校官网自动核验和低人工量派单账本。它把 854 条 B0/B1 高校辅证聚合成 78 条学校级动作，按冲突、补缺、未匹配、补结构化、强辅证抽检、继续补源和章程规则分桶；自动脚本负责查找、复跑和结构化高校官网来源，人工只处理 C0/C1/C7、抽检失败升级项和最终候选完整专业组。
- 已新增 `data/working/issue19-official-unavailable-sampling-gates.csv` 作为官方结构化计划暂不可得时的抽样和升级门禁。它保留 78 条高校侧任务，并从 184 条 P3 低风险池中抽出 25 条专业明细；C0/C1/C7 共 104 条明细必须 100% 回看第 19 期原页，C2 强辅证抽检最低覆盖 20 条以上，P3 低风险样本用于验证底座稳定性。抽检失败即升级同页列 100%，同校出现 2 个失败升级同校 100%，同专业组失败升级整组 100%。
- 已新增 `data/working/issue19-official-unavailable-sampling-execution-detail.csv` 作为逐专业执行明细。它把 C0/C1/C7 直接展开到 104 条必核专业明细，把 C2 强辅证池抽出 24 条明细，把 P3 低风险池抽出 25 条明细，合计 153 条；人工执行时优先从这张表回看 PDF 原页、核湖北官方侧、核高校官网或章程辅证并记录三方一致性。
- 已新增 `data/working/issue19-official-unavailable-sampling-review-overlay-public-ledger.csv` 作为上述 153 条执行明细的公开进度账本，并在 Git 忽略的本地目录生成可填写复核表。公开层只同步记录 SHA、PDF 原页/湖北官方侧/高校辅证填写计数、抽检失败和升级状态；字段读数、学校专业明细、复核记录和备注正文不进入公开仓库。该账本只证明人工复核入口已建立，不证明字段事实闭环。
- 已新增 `data/working/issue19-official-unavailable-sampling-review-packets-public-ledger.csv` 作为上述复核 Overlay 的页列核验包账本。它把 153 条逐专业复核明细压缩成 46 个 `PDF页码×版面列` 私有核页包，覆盖 40 个 PDF 页；公开层只保留页列计数、证据编号、SHA 和 R0 状态，私有 HTML/CSV 才展示页图、OCR 行、学校专业线索和人工填写栏。该账本只降低人工定位成本，不改变抽样门禁，也不替代湖北官方计划。
- 已新增 `data/working/issue19-official-unavailable-sampling-review-execution-queue.csv` 作为 46 个页列核验包的公开执行顺序。它把任务分为 E0 冲突/错位先核 6 个、E1 官网未匹配专业名归属 11 个、E2 官网补缺候选核页 3 个、E3 C2 强辅证抽检 2 个、E4 P3 低风险抽检 24 个；人工可以按队列打开私有 HTML/CSV 和原页核验，但字段写回、推荐依据和最终可用仍全部关闭。
- 已新增 `data/working/issue19-official-unavailable-sampling-triage-prefill-public-audit.csv` 作为 46 个页列执行队列的私有预填公开审计。它在 Git 忽略目录生成 153 条私有预填明细，把 97 条高校官网辅证线索、16 个高校来源文件、OCR 计划数/学费/选科线索先放到人工核页入口；公开层只保留页列计数、来源文件聚合计数、私有 CSV SHA 和非最终门禁。该表减少人工逐校查找成本，但不确认字段事实，不替代第 19 期原页和湖北官方侧核验。
- 已新增 `data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv` 作为 C4/C6 高校源刷新执行包。它把 36 个学校侧 C4/C6 任务拆成 4 条泳道：X0 无官网计划入口需搜索 8 包、X1 有入口待获取湖北计划 6 包、X2 有入口但未留存结果 6 包、X3 已有部分来源待结构化 16 包；私有层承接 607 条逐专业补源/补结构化明细。该表只安排自动抓取、结构化和后续 diff，不能把高校官网结果直接写成湖北官方计划事实。
- 已新增 `data/working/issue19-c4-c6-retained-source-reuse-public-ledger.csv` 作为 C4/C6 已留存高校官网源复用审计。它把 36 个 C4/C6 包接到 434 条已留存官网/API/PDF/XLSX/HTML 标准化证据，公开层只保留包级匹配计数和私有明细 SHA；当前 16 个包已有可复用官网源，83 条私有明细出现计划数一致候选、104 条可提示 OCR 计划数漏识、18 条存在计划数冲突。该审计只决定后续 diff 和核验优先级。
- 已新增北京语言大学官方 API 原始源：`data/external/issue19-c4-c6-official-sources/blcu-2026-hubei-physics-normal.json`，公开账本为 `data/working/issue19-c4-c6-blcu-official-source-fetch-public-ledger.csv`。该源来自北京语言大学招生系统，参数为湖北、2026、物理类、普通类，返回 14 条逐专业计划、计划数合计 34；它仍只是高校侧辅证，不能替代湖北省招办计划。
- 已新增 `data/working/issue19-c4-c6-structured-candidate-diff-public-ledger.csv` 作为 C4/C6 结构化候选 diff。它把北京语言大学新增 API 源并入综合结构化高校源后，对 607 条私有明细自动 double check：专业名匹配 212 条、计划数一致候选 85 条、OCR 计划数补缺候选 106 条、计划数冲突候选 23 条。该表用于把人工核验压缩到冲突、OCR 缺失、疑似匹配和新增源命中抽检，仍不能字段写回或推荐。
- 第 19 期 PDF 原页或纸质原页仍作为省招办原件层，优先核最终候选、冲稳保边界、B0/B1 优先组、计划数冲突、官网未匹配、补源缺口和字段空缺但进入候选的专业。
- 高校官网/API/XLSX/PDF/图片只用于自动 double check 专业名、计划数、学费、选科、校区、学制和章程限制；专业组边界、调剂范围和最终志愿系统代码仍必须回到湖北省招办渠道。
- `strong_support`、计划数一致或官网字段齐全的行只能进入分层抽检，不能自动定稿。抽样出现结构错误、关键限定词丢失、计划数冲突、OCR 把学费读成计划数、物理/历史未拆分、官网来源不是 2026 湖北物理普通本科，或同组存在家庭不能接受专业时，同页列、同校或同组升级 100% 人工核验。
- 家庭人工只签认最终候选完整专业组、红色冲突项和抽检失败升级项；脚本负责把 41208 个字段任务全量排序和分流，避免把全量字段核验压力摊给家庭。

## 五、高校官网自动核验适配器候选

湖北官方结构化计划暂不可无登录取得时，高校官网只做 double check 和差异发现。当前优先把高校来源按三类适配器推进，所有未接入脚本的线索都标为“待脚本复核”，不得直接写回字段事实。

| 适配器 | 代表学校和来源 | 当前本地证据 | 自动化价值 | 边界 |
| --- | --- | --- | --- | --- |
| `ajax_zsjh_form` | 北京语言大学 `http://lqcx.blcu.edu.cn/f/ajax_zsjh`；中国传媒大学 `https://zszx.cuc.edu.cn/f/ajax_zsjh` | 已留存 `blcu-2026-hubei-physics-normal.json`、`cuc-2026-hubei-physics-normal-zsjh.json` | JSON 字段稳定，适合批量核专业名、计划数、学费、学制、校区、选科 | 多数不给湖北省编院校专业组代码，不能替代省招办专业组边界 |
| `zsdata_lqxx_json` | 西安邮电大学、江汉大学、西安财经大学、西安医学院、兰州大学等 `zsdata/lqxx` 同构接口 | 已留存 `xupt-*`、`jhun-*`、`xaufe-*`、`xiyi-*`、`lzu-*` 原始 JSON 或入口文件 | 适合自动抓 2026 湖北物理普通类逐专业计划，学校间可复用 parser | 不同学校参数名、科类口径、批次口径可能不同，需逐校网络可达性和字段映射复核 |
| `html_table_plan` | 成都信息工程大学 HTML 表；武汉科技大学专业组页 + 专业计划学费页 | 已留存 `cuit-2026-undergraduate-plan.html`、`wust-2026-hubei-major-groups.html`、`wust-2026-major-plan-fees.html` | 适合解析静态表格，或多页 join 核计划、学费、校区、专业组线索 | HTML 表结构漂移风险较高；多页 join 不能自动定稿，必须回第 19 期原页和湖北官方侧 |
| `image_or_pdf_ocr` | 湖北大学图片主体计划页、学校 PDF/图片计划 | 部分学校已有 PDF/图片/OCR 抽取链路 | 适合作为人工核页入口和 OCR 二次校验 | 不作为主自动源；关键字段必须人工看原图/PDF 并留 SHA |

自动化优先级：JSON API 高于 HTML 表格，高于 PDF/OCR/截图。人工最小核验集合优先包含：计划数冲突行、OCR 计划数缺失但官网可补行、疑似匹配专业名、新增高校源命中抽检，以及每个最终候选院校专业组的完整组内专业核验。

## 六、官方平台抓取脚手架

已新增脚本：

```bash
python3 scripts/fetch_hubei_plan_platform.py --dry-run-contract
```

拿到登录态后，脚本运行方式为：

```bash
HUBEI_PLAN_TOKEN='<Admin-Token>' \
python3 scripts/fetch_hubei_plan_platform.py \
  --year 2026 \
  --batch-label-contains 本科普通批 \
  --subject-label-contains 物理 \
  --page-size 200
```

脚本保真规则：

- token 只从 `HUBEI_PLAN_TOKEN` 或 `HUBEI_PLAN_AUTH_TOKEN` 读取，不打印、不写入公开仓库。
- 可选考生号只从 `--ksh` 或 `HUBEI_PLAN_KSH` 读取；公开摘要只记录 redacted 标识。
- 原始分页 JSON 默认写入 `private/hubei-plan-platform/raw/`，该目录被 Git 忽略。
- 公开输出默认为 `data/working/hubei-2026-official-platform-admission-detail.csv`，一行一个招生专业；专业组无专业行时只输出 0 明细占位。
- 公开 CSV 默认保存原始行 SHA，不保存完整原始行 JSON；如确需字段级审计，可显式加 `--include-raw-json-in-csv`，但提交前必须做隐私和敏感字段扫描。
- 平台数据进入最终方案前，仍要和第 19 期 PDF 原页、高校官网/章程、家庭接受度和调剂结论闭环。

## 七、下一步获取方案

优先级从高到低：

1. 使用考生账号登录湖北招生数智综合平台，在“志愿填报智能参考系统”中查询并导出或截图关注院校专业组。
2. 获取《湖北招生考试》杂志第 19 期。湖北招生考试网产品手册显示第 19 期对应本科普通批首选物理科目各院校在鄂招生计划。
3. 等待湖北教育考试网招生计划专题页面更新完整计划。
4. 对目标学校官网或招生公众号逐校查 2026 湖北招生计划，作为辅助来源，最终仍以湖北官方计划为准。

湖北官方政策问答已明确：考生填报的志愿代号必须以 2026 年省招办通过《湖北招生考试》杂志第 13、16、19、22 期公布的招生计划为准，不能使用往年资料上的代号。第 16 期对应历史类计划，若后续做历史类对照或家庭扩展需求再获取；当前考生首选物理，核心是第 19 期。

## 八、需要导出的字段

整理 2026 计划时，默认按“招生明细”记录，一行一个专业；院校专业组只作为索引和调剂范围。每条招生明细至少记录：

```text
学校名称
院校代码
院校专业组代码
批次
首选科目
再选科目要求
城市
校区
学校属性
组内全部专业名称
专业代码
每个专业计划人数
学费
学制
备注
是否中外合作/高收费/民办/定向/专项/预科/民族班
是否有体检、单科、语种等限制
来源页码或平台截图编号
原始行SHA256
私有原始响应编号
```

## 八、当前可先推进的工作

在完整 2026 计划拿到前，可以先做：

- 按 2023-2025 投档线筛出历史候选院校专业组。
- 按家庭底线剔除明显不合适项。
- 按城市和专业方向列出待查学校清单。
- 从学校官网或公众号补充 2026 湖北计划线索。
- 把第 19 期 OCR 明细逐专业结构化并保真核验，优先处理 B0/B1/B2 的 12995 条稳定化任务。
- 使用 `data/working/issue19-raw-major-lineage-consistency-audit.csv` 持续确认 13736 条原始 OCR 专业行没有丢行、错连或核心字段漂移；使用 `data/working/issue19-raw-major-source-evidence-audit.csv` 持续确认每条专业明细都能按 `来源页码+版面列+专业起始行号` 回到私有 OCR 起始行、页级 manifest、私有窗口 JSONL 和公开原页锚点；再用 `data/working/issue19-major-source-evidence-risk-sidecar.csv` 把源证据风险、底座稳定性、闭环缺口和 P0 复核任务下沉到同一条 `专业行ID`，用 `data/working/issue19-field-fact-closure-ledger.csv` 把再选科目、专业计划数、学费三项关键字段的缺口、候选和待核状态下沉到同一条 `专业行ID`。这些表只证明原始结构化链路、源证据闭合、字段事实状态和核页优先级，不能替代湖北官方系统或省招办计划字段核验。

但这些只能作为候选池，不能进入最终志愿表。

当前已生成过渡候选池：

- `data/working/historical-preferred-city-pool-2023-2025.tsv`
- `data/working/candidate-pool-v1.csv`
- `docs/CANDIDATE_POOL_V1.md`

这些文件来自历年投档线解析结果，可能包含 OCR 噪声、历史专业组变化、预科/专项/民办/高收费等不符合当前家庭底线的项目，只能用于提示“下一步查哪些学校”，不能直接用于志愿排序。
