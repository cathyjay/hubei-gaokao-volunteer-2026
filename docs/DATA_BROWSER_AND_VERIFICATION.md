# 结构化数据浏览与快速核验说明

更新时间：2026-06-29

## 现在怎么直接看

最方便的入口是：

- `data/exports/issue19-round4-city-gradient.xlsx`
- `data/exports/issue19-round4-priority-focus55.xlsx`
- `data/exports/issue19-closure-and-shortlist-v1.xlsx`
- `data/exports/issue19-round4-50k-coop-city-gradient.xlsx`
- `data/exports/issue19-round2-updated-preferences.xlsx`
- `data/exports/issue19-round3-unrestricted-region.xlsx`
- `data/exports/issue19-personal-fit-v1.xlsx`
- `data/exports/issue19-stable-foundation-browser.xlsx`

`issue19-round4-city-gradient.xlsx` 是当前优先入口：它不引用 Round3 输出，直接从稳定底座、教育部学校属性表和三年投档线旁挂表重建候选，主表保留 H1-H4 共 328 个“主要可能够得着”的院校专业组，按城市和冲稳保展示；H0 历史待补、H5 高冲暂缓均单列附录。详细说明见 `docs/ROUND4_CITY_GRADIENT_CANDIDATES.md`。

`issue19-round4-priority-focus55.xlsx` 是 Round4 压缩入口：它把优先 120 组压缩为 55 个重点核验组，并把 65 组暂缓；55 组展开为 458 条完整组内专业，适合先做家庭调剂接受度判断和下一批核验排序。它仍是核验入口，不是定稿表。

`issue19-closure-and-shortlist-v1.xlsx` 是当前字段闭环和重点核验入口：它把第一闭环 37 个页列、206 条最高优先级逐任务、36 所学校 80 个高校官网辅证动作、2026-06-29 live 补源尝试、Round4 55 个重点核验专业组和 458 条完整组内专业明细放在一起。它适合今天继续推进“哪些字段先核、哪些官网源能 double check、哪些专业组优先让家庭看完整组内专业”。详细说明见 `docs/CLOSURE_AND_SHORTLIST_V1.md`。

`issue19-round4-50k-coop-city-gradient.xlsx` 是 Round4 的 5 万内中外合作/高收费平行专项入口：它保留 Round4 的公办、专业排除、H0/H5 单列和城市展示口径，只放费用相对清楚的 50000 元内中外合作/国际合作/高收费项目；主表 21 个专业组，费用待核、出国费用、非人民币币种和超过 50000 元的组单列附录。详细说明见 `docs/ROUND4_50K_COOP_CITY_GRADIENT_CANDIDATES.md`。

`issue19-round3-unrestricted-region.xlsx` 是第三轮历史入口：它在最新家庭偏好基础上取消城市和地区筛选、加分和名额分配，保留优先讨论 60 组和主线 120 组，用于回溯旧口径。详细说明见 `docs/ROUND3_UNRESTRICTED_REGION_CANDIDATES.md`。

`issue19-round2-updated-preferences.xlsx` 是第二轮历史入口：它吸收了最新体检摘要和家庭偏好，把护理、动物医学/兽医设为本轮暂不纳入，把医技/康复保留为专项了解，同时新增机械自动化、电子信息/网络、计算机/AI/软件、环境、农业、工商旅游管理等研究方向。该批次保留了优先城市观察表，用于复现旧口径，不作为 Round3 城市限制。详细说明见 `docs/ROUND2_UPDATED_PREFERENCES.md`。

`issue19-personal-fit-v1.xlsx` 是上一版个人适配候选：它把 515 分、91723 位次、旧家庭偏好、公办普通主线和 7 万中外合作专项口径合在一起，压缩成 45 个院校专业组、267 条完整组内专业明细。该文件仍可回溯，但不是最新偏好入口。详细说明见 `docs/PERSONAL_FIT_CANDIDATES_V1.md`。

`issue19-stable-foundation-browser.xlsx` 是从稳定数据基座 V0 生成的全量浏览版，不改动原始 CSV。它适合追溯全量底座、筛选新城市/新专业、检查某个专业组为什么进入或没有进入讨论池。

如果这次专门看“年学费 70000 元以内、中外合作或高收费是否值得讨论”，打开：

- `data/exports/issue19-expanded-budget-coop-scenario.xlsx`

这份工作簿是新增的专项覆盖层，不改动 V0 底座。详细说明见 `docs/EXPANDED_BUDGET_COOP_AND_SPECIAL_TRACKS.md`。

工作簿里主要看这几张表：

1. `00_怎么看`：工作簿使用说明。
2. `01_V0状态`：底座当前状态和边界。
3. `02_专业组浏览`：一行一个院校专业组，适合先筛学校、城市、调剂风险和完整组。
4. `03_逐专业浏览`：一行一个招生专业明细，适合看专业、计划数、学费、选科、历史线索和核验优先级。
5. `04_观察池专业组`：从 3329 个专业组里筛出的机器观察池。
6. `05_初筛专业`：当前机器初筛线索专业。
7. `06_快速核验抽样`：用于快速验证 OCR/结构化质量的分层样本。
8. `07_候选讨论模板`：偏好专业线索组，预留家庭讨论字段。

如果不想打开 Excel，也可以直接看这些 CSV：

- `data/exports/issue19-stable-foundation-group-browser.csv`
- `data/exports/issue19-stable-foundation-major-browser.csv`
- `data/exports/issue19-stable-foundation-observation-groups.csv`
- `data/exports/issue19-stable-foundation-machine-signal-majors.csv`
- `data/exports/issue19-stable-foundation-quick-verification-sample.csv`
- `data/exports/issue19-stable-foundation-candidate-discussion-template.csv`

7 万预算中外合作专项 CSV：

- `data/exports/issue19-expanded-budget-coop-groups.csv`
- `data/exports/issue19-expanded-budget-coop-majors.csv`
- `data/exports/issue19-expanded-budget-coop-scenario-summary.json`

个人适配候选 V1：

- `data/exports/issue19-personal-fit-v1-groups.csv`
- `data/exports/issue19-personal-fit-v1-major-details.csv`
- `data/exports/issue19-personal-fit-v1-summary.json`

第二轮更新偏好候选：

- `data/exports/issue19-round2-updated-preferences-main-shortlist-groups.csv`
- `data/exports/issue19-round2-updated-preferences-health-agri-special-groups.csv`
- `data/exports/issue19-round2-updated-preferences-specific-watchlist.csv`
- `data/exports/issue19-round2-updated-preferences-priority-city-watchlist.csv`
- `data/exports/issue19-round2-updated-preferences-main-shortlist-majors.csv`
- `data/exports/issue19-round2-updated-preferences-special-majors.csv`
- `data/exports/issue19-round2-updated-preferences-summary.json`

第三轮不限地区候选：

- `data/exports/issue19-round3-unrestricted-region-discussion-priority-groups.csv`
- `data/exports/issue19-round3-unrestricted-region-main-shortlist-groups.csv`
- `data/exports/issue19-round3-unrestricted-region-main-shortlist-majors.csv`
- `data/exports/issue19-round3-unrestricted-region-special-low-priority-groups.csv`
- `data/exports/issue19-round3-unrestricted-region-special-majors.csv`
- `data/exports/issue19-round3-unrestricted-region-city-distribution.csv`
- `data/exports/issue19-round3-unrestricted-region-summary.json`

第四轮按城市和冲稳保候选：

- `data/exports/issue19-round4-city-gradient-candidate-groups.csv`
- `data/exports/issue19-round4-city-gradient-priority120-groups.csv`
- `data/exports/issue19-round4-city-gradient-major-details.csv`
- `data/exports/issue19-round4-city-gradient-city-summary.csv`
- `data/exports/issue19-round4-city-gradient-history-missing-groups.csv`
- `data/exports/issue19-round4-city-gradient-high-rush-paused-groups.csv`
- `data/exports/issue19-round4-city-gradient-summary.json`

字段闭环与重点核验 V1：

- `data/exports/issue19-closure-and-shortlist-v1-first-closure-page-sides.csv`
- `data/exports/issue19-closure-and-shortlist-v1-first-closure-detail-tasks.csv`
- `data/exports/issue19-closure-and-shortlist-v1-school-source-tasks.csv`
- `data/exports/issue19-closure-and-shortlist-v1-priority55-groups.csv`
- `data/exports/issue19-closure-and-shortlist-v1-priority55-major-details.csv`
- `data/exports/issue19-closure-and-shortlist-v1-paused65-groups.csv`
- `data/exports/issue19-closure-and-shortlist-v1-summary.json`

高校源 Adapter D0/D1 页列人工核验包：

- `data/working/issue19-school-source-adapter-d0-d1-page-side-packets-v1-public-ledger.csv`
- `data/working/issue19-school-source-adapter-d0-d1-page-side-packets-v1-summary.json`

高校源 Adapter D0/D1 页列核验进度公开账本：

- `data/working/issue19-school-source-adapter-d0-d1-page-side-progress-v1-public-ledger.csv`
- `data/working/issue19-school-source-adapter-d0-d1-page-side-progress-v1-summary.json`

高校源 Adapter D0/D1 页列 PDF 视觉核验审计：

- `data/working/issue19-school-source-adapter-d0-d1-page-side-pdf-visual-audit-v1-public-ledger.csv`
- `data/working/issue19-school-source-adapter-d0-d1-page-side-pdf-visual-audit-v1-summary.json`

高校源 Adapter D0/D1 逐项证据路由：

- `data/working/issue19-school-source-adapter-d0-d1-item-evidence-route-v1-public-ledger.csv`
- `data/working/issue19-school-source-adapter-d0-d1-item-evidence-route-v1-summary.json`

高校源 Adapter D0/D1 逐项准出门禁：

- `data/working/issue19-school-source-adapter-d0-d1-item-resolution-gate-v1-public-ledger.csv`
- `data/working/issue19-school-source-adapter-d0-d1-item-resolution-gate-v1-summary.json`

第四轮 5 万内中外合作/高收费专项：

- `data/exports/issue19-round4-50k-coop-city-gradient-candidate-groups.csv`
- `data/exports/issue19-round4-50k-coop-city-gradient-priority-groups.csv`
- `data/exports/issue19-round4-50k-coop-city-gradient-major-details.csv`
- `data/exports/issue19-round4-50k-coop-city-gradient-city-summary.csv`
- `data/exports/issue19-round4-50k-coop-city-gradient-history-missing-groups.csv`
- `data/exports/issue19-round4-50k-coop-city-gradient-high-rush-paused-groups.csv`
- `data/exports/issue19-round4-50k-coop-city-gradient-fee-pending-or-over-budget-groups.csv`
- `data/exports/issue19-round4-50k-coop-city-gradient-summary.json`

## 原始结构化数据在哪

原始 OCR 结构化底稿仍然保留在 `data/working`：

- `data/working/issue19-full-admission-plan-school-ocr-draft.csv`：一行一所院校。
- `data/working/issue19-full-admission-plan-group-ocr-draft.csv`：一行一个院校专业组。
- `data/working/issue19-full-admission-plan-major-ocr-draft.csv`：一行一个招生专业明细。

后续筛选优先使用稳定基座视图：

- `data/working/issue19-stable-foundation-group-screening-view.csv`
- `data/working/issue19-stable-foundation-major-screening-view.csv`
- `data/working/issue19-stable-foundation-group-readiness-bridge.csv`

## 怎么筛候选

先从 `02_专业组浏览` 开始，不要先陷入单个专业。

建议筛选顺序：

1. `公办民办机器线索` 和 `家庭底线属性动作`：先排除明显不符合“公办、正常学费”的组。
2. `城市` / `教育部所在地`：只作为展示字段；Round4 不按城市筛选、加分或分配名额，城市后续用于生活成本、交通、就业资源和家庭接受度讨论，实际校区仍需看第 19 期原页和招生章程。
3. `偏好专业数`、`数字媒体技术专业数`、`计算机类相关专业数`、`师范类相关专业数`：找偏好专业组。
4. `调剂初判`：重点看完整专业组里有没有医学护理、高收费、特殊限制等不能接受项。
5. `历史线索分层`、`历史最高等位分差`、`历史最低等位分差`：粗看冲稳保线索。
6. `人工核验下一步`：看这个组下一步需要核什么。

进入某个专业组后，再到 `03_逐专业浏览` 用 `院校专业组代码OCR规范化` 过滤，查看完整组内专业，不只看想填的 6 个专业。

## D0/D1 页列人工核验包怎么用

`issue19-school-source-adapter-d0-d1-page-side-packets-v1-public-ledger.csv` 是高校侧辅证 diff 之后的最小人工入口之一。它把 146 条私有 D0/D1 核验项压成 18 个 `PDF页码 × 版面列` 包：9 个 E0 计划数冲突页列、7 个 E1 OCR 计划数缺失可补页列、2 个 E2 疑似匹配页列。

使用顺序：

1. 先看公开账本的页码、版面列、优先级、R0/R1/R2/R3 计数和私有材料 SHA。
2. 到本地 Git 忽略的私有材料中打开对应页列 CSV/HTML，对照第 19 期 PDF 原页逐项核。
3. 能进入最终候选的组，再核湖北官方系统或省招办计划；高校官网、API、PDF、XLSX 只作 double check 和差异解释。
4. 未完成 PDF 原页、湖北官方侧和必要高校辅证闭环前，不得写回字段事实，不得生成学校专业建议，也不得把它理解成可填报结论。

`issue19-school-source-adapter-d0-d1-page-side-progress-v1-public-ledger.csv` 是上述页列包的公开状态机/进度账本，不是新的事实源。它只同步每个页列私有 CSV 中 PDF 原页记录、湖北官方计划记录、高校源差异解释、最终字段处理建议、双人复核和字段写回门禁的填写状态，以及是否可进入字段写回评审；不含学校名、专业名、字段值、OCR 正文、人工读数或私有路径。当前仍是 `not_final`，字段事实、推荐依据、最终可用、学校专业建议均为 0 或 `false`，只能回答“私有核验项有没有填、能否进入字段写回评审”。

`issue19-school-source-adapter-d0-d1-page-side-pdf-visual-audit-v1-public-ledger.csv` 是同一批页列的视觉核验入口。公开层只显示 18 个页列的源页图 SHA、栏图 SHA、HTML SHA、尺寸、页码和状态；实际栏图、整页图、学校专业线索和人工填写栏只在本地私有 HTML/CSV。它用于人工快速打开对应 PDF 原页和左右栏，不确认计划数、学费、选科、专业名或专业组边界。

`issue19-school-source-adapter-d0-d1-item-evidence-route-v1-public-ledger.csv` 是同一批 146 条私有核验项的一行一项公开路由。它逐条回链页列包、页列进度和 PDF 视觉审计，只公开状态桶、证据编号和 SHA，不公开学校、专业、代码、OCR 线索、字段读数或人工记录。它适合用来检查“每一项到底还缺 PDF 原页、湖北官方侧、高校源辅证还是双人复核”，但仍不能作为字段事实、学校专业建议或最终志愿依据。

`issue19-school-source-adapter-d0-d1-item-resolution-gate-v1-public-ledger.csv` 是逐项证据路由之后的准出门禁表。它不新增事实，只把每条核验项拆成 PDF 原页、湖北官方侧、高校辅证、冲突处理、双人复核、三方闭环和字段写回缺口；当前 146 条全部为 `blocked_missing_required_evidence`，其中 29 条还需要冲突处理和双人复核。它用于判断哪些项补证后才可进入私有写回评审。

## 怎么快速验证这批数据

快速验证不应该让家里人手工核 13,736 条明细。合理方案是三层：

1. 机器一致性验收：用 `python3 scripts/verify_baseline.py` 和 `CHECKSUMS.sha256` 保证结构化表、血缘表、页列证据、风险表没有漂移。
2. 分层抽样核验：先核 `06_快速核验抽样` 的 190 条样本，覆盖偏好专业、城市字段、P0/P1 风险、官网辅证、低风险抽检和历史线索接近项。
3. 入围组 100% 核验：只要一个院校专业组进入家庭讨论或志愿梯度，就必须核完整组，不只核想填的专业。

`06_快速核验抽样` 每一行都带：

- PDF 页码和版面列。
- 院校、专业组、专业代号、专业名称。
- OCR 读到的计划数、学费、选科。
- 抽样理由。
- 预留的原页、湖北官方、高校辅证核验结果和备注字段。

核验时先回看第 19 期 PDF 原页，确认专业名称、代号、计划数、学费、选科、备注限制和专业组边界。能进入定稿讨论的专业组，再尽量核湖北官方系统；高校官网只做 double check 和冲突发现。

## 抽样失败怎么处理

如果抽样发现以下情况，不能只改单行，要升级核验范围：

- 专业组边界错位。
- 左右栏串读。
- 计划数或学费读错。
- 专业名称关键限定词丢失，例如师范、中外合作、实验班、面向地区。
- 同一页列出现多处结构错误。
- 同一院校多个专业出现类似 OCR 错误。
- 组内出现家庭不能接受专业但调剂风险未标出。

升级规则：

- 单字段错误：先核同一专业组。
- 页列错位：核同一 `PDF页码 × 版面列`。
- 学校规则或官网冲突：核同一院校相关专业组。
- 调剂风险漏标：核完整专业组，并重新判断是否服从调剂。
- D0/D1 页列包中任一 R0 冲突或 R2 疑似匹配核不准：同页列先升级 100% 核验；同校重复出现问题时，再升级到同校相关专业组。

## 重新生成浏览工作簿

```bash
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/export_issue19_stable_foundation_browser.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/export_issue19_expanded_budget_coop_scenario.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_personal_fit_v1.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_round2_updated_preferences.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_round4_city_gradient_candidates.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_issue19_round4_50k_coop_city_gradient_candidates.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/update_checksums.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/verify_baseline.py
```

这些命令都通过后，才说明浏览层、核验抽样层、个人候选层、Round2 更新偏好层、Round4 普通主线、Round4 5 万专项和公开校验层是一致的。
