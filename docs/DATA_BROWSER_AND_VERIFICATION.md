# 结构化数据浏览与快速核验说明

更新时间：2026-06-28

## 现在怎么直接看

最方便的入口是：

- `data/exports/issue19-stable-foundation-browser.xlsx`

这个 Excel 工作簿是从稳定数据基座 V0 生成的浏览版，不改动原始 CSV。它适合家庭一起看、筛选和做第一轮讨论。

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
2. `城市候选`：先看武汉、成都、西安、北京，也可以后续扩展城市。
3. `偏好专业数`、`数字媒体技术专业数`、`计算机类相关专业数`、`师范类相关专业数`：找偏好专业组。
4. `调剂初判`：重点看完整专业组里有没有医学护理、高收费、特殊限制等不能接受项。
5. `历史线索分层`、`历史最高等位分差`、`历史最低等位分差`：粗看冲稳保线索。
6. `人工核验下一步`：看这个组下一步需要核什么。

进入某个专业组后，再到 `03_逐专业浏览` 用 `院校专业组代码OCR规范化` 过滤，查看完整组内专业，不只看想填的 6 个专业。

## 怎么快速验证这批数据

快速验证不应该让家里人手工核 13,736 条明细。合理方案是三层：

1. 机器一致性验收：用 `python3 scripts/verify_baseline.py` 和 `CHECKSUMS.sha256` 保证结构化表、血缘表、页列证据、风险表没有漂移。
2. 分层抽样核验：先核 `06_快速核验抽样` 的 190 条样本，覆盖偏好专业、优先城市、P0/P1 风险、官网辅证、低风险抽检和历史线索接近项。
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

## 重新生成浏览工作簿

```bash
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/export_issue19_stable_foundation_browser.py
/Users/cathy07/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/export_issue19_expanded_budget_coop_scenario.py
python3 scripts/update_checksums.py
python3 scripts/verify_baseline.py
```

这三个命令都通过后，才说明浏览层、核验抽样层和公开校验层是一致的。
