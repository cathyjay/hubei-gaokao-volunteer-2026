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

## 交叉校验来源

1. static-data.gaokao.cn 一分一段 JSON
   - URL: https://static-data.gaokao.cn/www/2.0/section2021/2026/42/2073/3/lists.json
   - 本地副本：`data/derived/hubei-2026-physics-section-static-gaokao-cn.json`
   - 用途：复核 515 位次区间和 2025/2024/2023 等位分。

2. 用户提供的成绩截图
   - 用途：确认各科成绩和总分。
   - 处理方式：不复制进项目，因为截图包含直接个人身份信息。

3. 湖北教育考试网 / 湖北招生数智综合平台相关通知
   - 志愿填报时间页面：https://www.hbccks.cn/html/gkzytb/2026-06/142885.html
   - 志愿填报政策问答：https://gaokao.hbccks.cn/zkzc/2026-06/143021.html
   - 用途：确认填报时间、平台入口、平行志愿规则和操作风险。

## 派生数据说明

- `data/derived/hubei-2025-physics-toudang-ocr.txt`：由 2025 官方图片 OCR 生成。
- `data/derived/hubei-2025-physics-toudang-parsed.csv`：2025 投档线解析行，3147 条数据。
- `data/derived/hubei-2024-physics-toudang-parsed.csv`：2024 投档线解析行，2800 条数据。
- `data/derived/hubei-2023-physics-toudang-parsed.csv`：2023 投档线解析行，2874 条数据。
- `data/derived/initial-city-pool-2023-2025.tsv`：按初始城市关键词生成的初筛池，不是最终志愿表。
