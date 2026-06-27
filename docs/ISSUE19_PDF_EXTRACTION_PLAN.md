# 《湖北招生考试》2026 年第 19 期 PDF 提取方案

最后更新：2026-06-26

## 一、当前材料

用户已提供第 19 期 PDF，公开仓库只记录私有证据编号和文件哈希，不记录用户本机原始路径。

该文件已复制到本地私有目录：

```text
private/raw/hubei-admission-magazine-2026-issue-19/issue19.pdf
```

公开仓库只保存文件元数据和抽取方法，不提交原始 PDF、整页截图或整页 OCR 文本。

## 二、已确认 PDF 元数据

| 字段 | 值 |
| --- | --- |
| 标题 | 湖北招生考试2026年19期·本科普通批（下） |
| 页数 | 240 |
| 文件大小 | 144095796 字节 |
| 页面尺寸 | 1000 x 1475 pt |
| SHA256 | `ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d` |
| 文本层 | 未发现可抽取文本层 |
| 处理路线 | PDF 渲染成图片后 OCR |

## 三、全量 OCR 运行摘要

已完成一次私有全量 OCR：

| 字段 | 值 |
| --- | --- |
| run id | `issue19-full-120dpi` |
| 私有输出目录 | `private/ocr-runs/issue19-full-120dpi` |
| 渲染 DPI | 120 |
| OCR 引擎 | Apple Vision |
| OCR 行数 | 65512 |
| QC 问题数 | 37127 |
| P0 问题数 | 19189 |
| P1 问题数 | 17938 |
| 低置信度页 | 61、117、129、166、192、215 |

摘要记录见 `data/working/issue19-ocr-run-summary.json`。整页 OCR 文本、渲染图片和 QC 明细只保存在 `private/`。

## 四、提取目标

本项目只服务湖北 2026 普通类、首选物理、本科普通批志愿决策。需要从第 19 期中提取：

- 院校代码和院校名称
- 院校专业组代码
- 首选科目和再选科目要求
- 专业代号和专业名称
- 招生计划数
- 学费、学制、校区
- 备注和特殊要求
- 来源页码、OCR 状态、人工核验状态

## 五、推荐处理流程

### 1. 小样本定位

先处理少量页，定位正文招生计划表从哪里开始：

```bash
python3 scripts/ocr_pdf_pages.py \
  --pdf private/raw/hubei-admission-magazine-2026-issue-19/issue19.pdf \
  --pages 1-20 \
  --output-dir private/ocr-runs/issue19-probe-001
```

查看：

```text
private/ocr-runs/issue19-probe-001/text/
private/ocr-runs/issue19-probe-001/suspected_plan_lines.csv
```

探测结果：第 10 页已经进入“本科普通批·首选科目物理·部委属院校”招生计划表。

### 2. 按页段分批 OCR

确认招生计划页段后，按 20-40 页一批处理，避免一次性生成过多图片和临时文件：

```bash
python3 scripts/ocr_pdf_pages.py \
  --pdf private/raw/hubei-admission-magazine-2026-issue-19/issue19.pdf \
  --pages 21-60 \
  --output-dir private/ocr-runs/issue19-pages-021-060
```

如需保留表格左右栏、坐标和行类型，继续生成行级 CSV：

```bash
python3 scripts/ocr_jsonl_to_line_csv.py \
  --jsonl private/ocr-runs/issue19-pages-021-060/ocr.jsonl \
  --output private/ocr-runs/issue19-pages-021-060/ocr-lines.csv
```

再生成 OCR 质量问题清单：

```bash
python3 scripts/ocr_qc_report.py \
  --lines private/ocr-runs/issue19-pages-021-060/ocr-lines.csv \
  --output private/ocr-runs/issue19-pages-021-060/qc_issues.csv
```

### 3. 人工复核结构化

OCR 输出只用于辅助录入。结构化数据先写入私有目录，逐条人工回看 PDF 页码后再标记核验状态：

```text
private/derived/issue19-admission-plan/issue19-admission-plan.csv
```

公开仓库保留空模板：

```text
data/working/issue19-admission-plan-template.csv
```

结构化 CSV 使用中文表头，方便家庭成员共同审阅。字段模板见 `data/working/issue19-admission-plan-template.csv`。

### 4. 20 所学校样本 double check

在全量结构化之前，先抽 20 所学校做 OCR + 官网双重核验：

```text
data/working/issue19-sample-schools-20.csv
```

样本核验说明见 `docs/ISSUE19_SAMPLE_DOUBLE_CHECK.md`。

私有 OCR 定位输出：

```bash
python3 scripts/extract_issue19_school_samples.py
```

输出到：

```text
private/derived/issue19-sample-school-ocr/样本学校OCR定位.csv
```

样本验证目标：

- OCR 能否正确定位学校、院校代码、院校专业组代码。
- OCR 能否识别组内全部专业，而不是只识别想看的专业。
- 学校官网能否找到 2026 湖北招生计划、专业组、专业代号、计划数、学费、选科或至少部分字段。
- 记录 OCR 与学校官网的冲突类型，再决定是否进入全量结构化。

## 六、数据保存边界

| 数据 | 保存位置 | 是否提交公开仓库 | 说明 |
| --- | --- | --- | --- |
| 原始 PDF | `private/raw/.../issue19.pdf` | 否 | 版权敏感，且文件很大 |
| 渲染页图片 | `private/ocr-runs/.../rendered-pages/` | 否 | 派生自原始 PDF |
| 整页 OCR 文本 | `private/ocr-runs/.../text/` | 否 | 派生自原始 PDF |
| OCR 运行 manifest | `private/ocr-runs/.../pdf_manifest.json` | 否 | 含本地路径和页图哈希 |
| 结构化全量计划 | `private/derived/issue19-admission-plan/` | 否，默认私有 | 可用于筛选，但仍需人工核验 |
| 空模板和 schema | `data/working/`、`docs/` | 是 | 不含整本内容，可复用 |
| 最终候选志愿分析 | `docs/`、`data/working/` | 是，谨慎 | 只记录必要字段、来源页码和复核状态 |

## 七、核验状态

每条专业计划至少使用以下状态：

- `ocr_raw`：仅 OCR 初稿，未看原图。
- `needs_manual_review`：需要人工回看 PDF 页。
- `manual_verified`：已人工核对页码和原图。
- `cross_checked_school_site`：已用高校官网计划交叉核验。
- `cross_checked_system`：已用湖北官方平台或志愿系统交叉核验。
- `rejected_unclear`：OCR 或原图不清，不能采用。

进入最终志愿表前，至少需要达到 `manual_verified`，关键候选应尽量达到 `cross_checked_system`。

技术闸门：`ocr_raw -> parsed_unverified -> manual_checked -> official_system_verified -> final_allowed`。任何应急使用项也必须完成 PDF 原页或纸质原页双人复核；湖北官方系统可得时必须补核，不可得时必须记录不可得状态和风险标签。没有完成这些步骤前，不得进入最终方案。

## 八、下一步

1. 对 `docs/ISSUE19_DOUBLE_CHECK_RESULTS_V1.md` 中的高优先级 7 校做 100% 原 PDF 页人工复核。
2. 先输出私有“逐组复核表”，确认院校代码、专业组代码、组边界、组内全部专业、计划数、学费、选科和备注。
3. 用学校官网、湖北官方平台或志愿系统做字段级交叉核验。
4. 样本校验通过后，再从 `ocr-lines.csv` 按左右栏、页码和坐标建立全量“院校专业组 -> 组内全部专业”的结构化表。
5. 对第一版候选池和新增候选学校优先回看对应页，完成院校专业组级核验。
6. 对可进入最终表的院校专业组，再查高校官网和官方平台做交叉核验。
