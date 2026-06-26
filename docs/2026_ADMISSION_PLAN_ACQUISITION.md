# 2026 招生计划获取状态

最后更新：2026-06-26

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
| 湖北教育考试网招生计划专题 | http://www.hbccks.cn/html/gkgzzt/gkzsjh/ | 已留存索引页 | 官方公开入口 |
| 2026 年普通高等学校招生计划页面 | http://www.hbccks.cn/html/gkzsjh/2026-05/142888.html | 页面显示“持续更新中，敬请期待” | 等待官方公开完整计划 |
| 湖北招生数智综合平台 | https://zspt.hubzs.com.cn | 首页和前端资源已留存 | 官方志愿系统和智能参考系统 |
| 平台计划查询接口 | `/prod-api/planQuery/plan/*` | 无登录请求返回 `401 令牌不能为空` | 需要考生登录态或平台权限 |
| 《湖北招生考试》杂志 | 第 13、16、19、22 期 | 需人工获取 | 官方纸质/电子招生计划来源 |
| 第 16/19 期专项检索 | `docs/HUBEI_ADMISSION_MAGAZINE_SEARCH.md` | 未找到公开完整电子版 | 获取路径和线索记录 |
| 高校官网招生计划 | 学校本科招生网 | 已发现部分高校发布 2026 计划 | 只能作为交叉校验 |

本地证据：

- `data/official/hubei-2026-admission-plan-platform/hbccks-plan-index.html`
- `data/official/hubei-2026-admission-plan-platform/hbccks-2026-plan-page.html`
- `data/official/hubei-2026-admission-plan-platform/index.html`
- `data/official/hubei-2026-admission-plan-platform/assets/`
- `data/official/hubei-2026-admission-plan-platform/api-probes/`
- `data/official/hubei-2026-volunteer-policy/143022-policy.html`
- `data/external/school-plan-crosschecks/`

补充说明：湖北教育考试网招生计划页面当前使用 HTTP 地址留存；同路径 HTTPS 抓取存在证书主机名不匹配问题，不能因此判断页面不存在。

## 三、已发现的平台接口

从湖北招生数智综合平台前端资源中发现以下只读计划查询接口：

- `/prod-api/planQuery/plan/nfs`
- `/prod-api/planQuery/plan/yxList?nf=2026&keyword=...&limit=...`
- `/prod-api/planQuery/plan/group`
- `/prod-api/planQuery/plan/student`
- `/prod-api/planQuery/plan/jzjt`
- `/prod-api/planQuery/dict/...`

直接无登录请求会返回：

```json
{"code":401,"msg":"令牌不能为空"}
```

结论：平台计划查询目前需要登录态，不能在项目里直接公开抓取完整 2026 计划。

无登录探测结果已留存在：

- `data/official/hubei-2026-admission-plan-platform/api-probes/planQuery-plan-nfs-no-token.json`
- `data/official/hubei-2026-admission-plan-platform/api-probes/planQuery-plan-yxList-2026-wuhan-no-token.json`

## 四、下一步获取方案

优先级从高到低：

1. 使用考生账号登录湖北招生数智综合平台，在“志愿填报智能参考系统”中查询并导出或截图关注院校专业组。
2. 获取《湖北招生考试》杂志第 19 期。湖北招生考试网产品手册显示第 19 期对应本科普通批首选物理科目各院校在鄂招生计划。
3. 等待湖北教育考试网招生计划专题页面更新完整计划。
4. 对目标学校官网或招生公众号逐校查 2026 湖北招生计划，作为辅助来源，最终仍以湖北官方计划为准。

湖北官方政策问答已明确：考生填报的志愿代号必须以 2026 年省招办通过《湖北招生考试》杂志第 13、16、19、22 期公布的招生计划为准，不能使用往年资料上的代号。第 16 期对应历史类计划，若后续做历史类对照或家庭扩展需求再获取；当前考生首选物理，核心是第 19 期。

## 五、需要导出的字段

整理 2026 计划时，每条院校专业组至少记录：

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
```

## 六、当前可先推进的工作

在完整 2026 计划拿到前，可以先做：

- 按 2023-2025 投档线筛出历史候选院校专业组。
- 按家庭底线剔除明显不合适项。
- 按城市和专业方向列出待查学校清单。
- 从学校官网或公众号补充 2026 湖北计划线索。

但这些只能作为候选池，不能进入最终志愿表。

当前已生成过渡候选池：

- `data/working/historical-preferred-city-pool-2023-2025.tsv`
- `data/working/candidate-pool-v1.csv`
- `docs/CANDIDATE_POOL_V1.md`

这些文件来自历年投档线解析结果，可能包含 OCR 噪声、历史专业组变化、预科/专项/民办/高收费等不符合当前家庭底线的项目，只能用于提示“下一步查哪些学校”，不能直接用于志愿排序。
