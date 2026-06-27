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
| 湖北教育考试网招生计划专题 | http://www.hbccks.cn/html/gkgzzt/gkzsjh/ | 已留存索引页；2026-06-28 公开 HTTP 复核返回 200，SHA 与 2026-06-27 留存一致 | 官方公开入口 |
| 2026 年普通高等学校招生计划页面 | http://www.hbccks.cn/html/gkzsjh/2026-05/142888.html | 2026-06-28 公开 HTTP 复核返回 200，但页面仍显示“持续更新中，敬请期待”；`can_finalize=false` | 等待官方公开完整计划 |
| 湖北招生数智综合平台 | https://zspt.hubzs.com.cn | 2026-06-28 首页已留存，公开 HTTPS 返回 200；首页只证明平台入口可访问 | 官方志愿系统和智能参考系统 |
| 平台计划查询接口 | `/prod-api/planQuery/plan/*` | 无登录请求返回 `401 令牌不能为空`；已写可复跑抓取脚本 | 需要考生登录态或平台权限 |
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
- `data/official/hubei-2026-volunteer-policy/143022-policy.html`
- `data/external/school-plan-crosschecks/`

补充说明：湖北教育考试网招生计划页面当前使用 HTTP 地址留存；同路径 HTTPS 抓取存在证书主机名不匹配问题，不能因此判断页面不存在。
`issue19-official-public-entry-status.json` 只记录公开入口状态和无登录探针结果；它能说明现阶段官方公开入口尚不足以直接定稿，不能替代第 19 期逐专业招生明细和湖北官方系统字段核验。

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

- 第 19 期 PDF 原页或纸质原页仍作为省招办原件层，优先核最终候选、冲稳保边界、B0/B1 优先组、计划数冲突、官网未匹配、补源缺口和字段空缺但进入候选的专业。
- 高校官网/API/XLSX/PDF/图片只用于自动 double check 专业名、计划数、学费、选科、校区、学制和章程限制；专业组边界、调剂范围和最终志愿系统代码仍必须回到湖北省招办渠道。
- `strong_support`、计划数一致或官网字段齐全的行只能进入分层抽检，不能自动定稿。抽样出现结构错误、关键限定词丢失、计划数冲突、OCR 把学费读成计划数、物理/历史未拆分、官网来源不是 2026 湖北物理普通本科，或同组存在家庭不能接受专业时，同页列、同校或同组升级 100% 人工核验。
- 家庭人工只签认最终候选完整专业组、红色冲突项和抽检失败升级项；脚本负责把 41208 个字段任务全量排序和分流，避免把全量字段核验压力摊给家庭。

## 五、官方平台抓取脚手架

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

## 六、下一步获取方案

优先级从高到低：

1. 使用考生账号登录湖北招生数智综合平台，在“志愿填报智能参考系统”中查询并导出或截图关注院校专业组。
2. 获取《湖北招生考试》杂志第 19 期。湖北招生考试网产品手册显示第 19 期对应本科普通批首选物理科目各院校在鄂招生计划。
3. 等待湖北教育考试网招生计划专题页面更新完整计划。
4. 对目标学校官网或招生公众号逐校查 2026 湖北招生计划，作为辅助来源，最终仍以湖北官方计划为准。

湖北官方政策问答已明确：考生填报的志愿代号必须以 2026 年省招办通过《湖北招生考试》杂志第 13、16、19、22 期公布的招生计划为准，不能使用往年资料上的代号。第 16 期对应历史类计划，若后续做历史类对照或家庭扩展需求再获取；当前考生首选物理，核心是第 19 期。

## 七、需要导出的字段

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
