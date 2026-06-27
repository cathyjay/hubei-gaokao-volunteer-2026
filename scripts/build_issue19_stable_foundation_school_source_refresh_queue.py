#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from issue19_review_rules import input_snapshot


ROOT = Path(__file__).resolve().parents[1]

AUTO_WORKBENCH = ROOT / "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv"
SOURCE_SEEDS = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv"
OFFICIAL_STATUS = ROOT / "data/working/issue19-official-public-entry-status.json"

OUTPUT = ROOT / "data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv"
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-stable-foundation-school-source-refresh-public-ledger-summary.json"
)
PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-stable-foundation-school-source-refresh"
PRIVATE_OUTPUT = PRIVATE_OUTPUT_DIR / "school-source-refresh-private-workbench.csv"

DATA_STAGE = "issue19_stable_foundation_school_source_refresh_public_ledger"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
]

PUBLIC_FIELDS = [
    "高校侧辅证刷新公开账本ID",
    "来源稳定基座自动交叉核验工作台",
    "来源高校官网补源种子表",
    "来源湖北官方公开入口状态快照",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "执行顺序",
    "高校侧刷新批次",
    "高校侧刷新任务类型",
    "高校侧刷新优先级",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "闭环优先级",
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态集合",
    "计划数核验状态集合",
    "差异字段集合",
    "来源文件类型集合",
    "公开来源文件数量",
    "公开来源文件集合SHA256",
    "公开来源URL数量",
    "公开来源URL集合SHA256",
    "涉及招生明细数",
    "涉及专业组数",
    "涉及PDF页数",
    "涉及页列数",
    "专业行ID集合SHA256",
    "专业组ID集合SHA256",
    "页列集合SHA256",
    "计划数冲突行数",
    "官网补缺候选行数",
    "强辅证抽检行数",
    "部分来源待结构化行数",
    "继续补源行数",
    "仅章程规则行数",
    "官网未匹配行数",
    "字段辅证行数",
    "疑似学费读作计划数行数",
    "需要PDF原页100%核验行数",
    "建议抽检行数",
    "建议补结构化行数",
    "建议继续补源行数",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源刷新状态",
    "高校官网或招生章程辅证状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_EXTRA_FIELDS = [
    "私有工作台用途",
    "涉及专业行ID集合",
    "涉及专业组ID集合",
    "页列集合",
    "公开来源文件集合",
    "公开来源URL集合",
    "官网来源检索提示",
    "建议自动复跑命令或动作",
    "本轮是否已复跑",
    "本轮复跑结果文件",
    "本轮复跑结果SHA256",
    "PDF原页人工核验结论",
    "湖北官方系统或省招办计划核验结论",
    "高校官网源复跑结论",
    "抽检结论",
    "升级范围",
    "复核人",
    "复核时间",
    "复核备注",
]

PRIVATE_FIELDS = PUBLIC_FIELDS + PRIVATE_EXTRA_FIELDS

PRIVATE_MANUAL_FIELDS = [
    "本轮是否已复跑",
    "本轮复跑结果文件",
    "本轮复跑结果SHA256",
    "PDF原页人工核验结论",
    "湖北官方系统或省招办计划核验结论",
    "高校官网源复跑结论",
    "抽检结论",
    "升级范围",
    "复核人",
    "复核时间",
    "复核备注",
]

FORBIDDEN_PUBLIC_TOKENS = [
    "/Users/",
    "/home/",
    "/var/folders/",
    "/private/",
    "private/",
    "private\\",
    "ocr-runs",
    "rendered-pages",
    "file://",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".heic",
    "Authorization",
    "Bearer ",
    "Cookie",
    "Set-Cookie",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "api_key",
    "身份证",
    "准考证",
    "报名号",
    "序列号",
    "手机号",
    "候选值",
    "人工读数",
    "湖北官方字段值",
    "字段确认值",
    "已确认",
    "已核准",
    "最终推荐",
    "最终方案",
    "可填报",
    "可排序",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    return f"{prefix}-{hashlib.sha1('|'.join(str(p) for p in parts).encode('utf-8')).hexdigest()[:16]}"


def false_gate_values():
    return {field: "false" for field in FALSE_FIELDS}


def split_items(value):
    if not value:
        return []
    return [item.strip() for item in str(value).replace("；", ";").split(";") if item.strip()]


def compact_join(items):
    return "；".join(sorted({item for item in items if item}))


def set_sha(items):
    return sha256_text("\n".join(sorted({item for item in items if item})))


def page_side_key(row):
    page = str(row.get("来源页码", "")).strip()
    side = str(row.get("版面列", "")).strip()
    if not page or not side:
        return ""
    try:
        page = f"{int(page):03d}"
    except ValueError:
        pass
    return f"{page}-{side}"


def source_files(row):
    return split_items(row.get("最佳官网来源文件", ""))


def source_file_types(files, source_status):
    if not files:
        if source_status == "needs_official_plan_source_search":
            return ["待补官网2026湖北计划源"]
        if source_status == "charter_or_rules_only_no_plan":
            return ["章程或规则线索"]
        if source_status == "has_partial_source_needs_followup":
            return ["部分来源待结构化"]
        return ["未留存来源文件"]
    result = []
    for file in files:
        lower = file.lower()
        if lower.endswith(".json"):
            result.append("API/JSON")
        elif lower.endswith(".xlsx") or lower.endswith(".xls"):
            result.append("XLS/XLSX")
        elif lower.endswith(".csv"):
            result.append("结构化CSV")
        elif lower.endswith(".pdf"):
            result.append("PDF")
        elif lower.endswith(".html") or lower.endswith(".htm"):
            result.append("HTML")
        else:
            result.append("其他公开来源")
    return sorted(set(result))


def seed_by_school(rows):
    mapping = defaultdict(list)
    for row in rows:
        mapping[row.get("学校名称", "")].append(row)
    return mapping


def urls_for_school(school, seed_mapping):
    urls = []
    for row in seed_mapping.get(school, []):
        url = row.get("官网URL", "").strip()
        if url:
            urls.append(url)
    return sorted(set(urls))


def refresh_batch(action):
    if action in {
        "C0-冲突先核PDF原页和湖北官方系统",
        "C1-官网补缺候选但禁止自动写回",
    }:
        return "S0-PDF原页与湖北官方优先闭环"
    if action == "C7-官网源未匹配专业需人工确认专业名":
        return "S1-专业名匹配人工确认"
    if action in {
        "C4-已有部分来源需补结构化或补湖北行",
        "C3-字段辅证补充结构化后核原页",
    }:
        return "S2-高校官网来源结构化刷新"
    if action == "C2-强辅证抽检并等待湖北官方闭环":
        return "S3-强辅证分层抽检"
    if action == "C6-继续搜索高校官网2026湖北计划源":
        return "S4-继续补高校官网计划源"
    if action == "C5-仅章程规则核特殊要求不能核计划数":
        return "S5-章程规则核特殊限制"
    return "S6-留存等待"


def refresh_task_type(action):
    if action == "C0-冲突先核PDF原页和湖北官方系统":
        return "计划数冲突回页核验"
    if action == "C1-官网补缺候选但禁止自动写回":
        return "官网补缺候选回页核验"
    if action == "C7-官网源未匹配专业需人工确认专业名":
        return "官网专业名未匹配人工确认"
    if action == "C4-已有部分来源需补结构化或补湖北行":
        return "已有来源补结构化或补湖北物理行"
    if action == "C3-字段辅证补充结构化后核原页":
        return "字段辅证补结构化"
    if action == "C2-强辅证抽检并等待湖北官方闭环":
        return "强辅证分层抽检"
    if action == "C6-继续搜索高校官网2026湖北计划源":
        return "继续搜索高校官网2026湖北计划"
    if action == "C5-仅章程规则核特殊要求不能核计划数":
        return "招生章程规则核验"
    return "留存等待湖北官方闭环"


def refresh_priority(action):
    order = {
        "C0-冲突先核PDF原页和湖北官方系统": "00-P0冲突",
        "C1-官网补缺候选但禁止自动写回": "01-P0补缺",
        "C7-官网源未匹配专业需人工确认专业名": "02-P1未匹配",
        "C4-已有部分来源需补结构化或补湖北行": "03-P1补结构化",
        "C3-字段辅证补充结构化后核原页": "04-P1字段辅证",
        "C2-强辅证抽检并等待湖北官方闭环": "05-P1抽检",
        "C6-继续搜索高校官网2026湖北计划源": "06-P2补源",
        "C5-仅章程规则核特殊要求不能核计划数": "07-P2规则",
    }
    return order.get(action, "08-P3留存")


def recommended_action(action, files, urls):
    if action == "C0-冲突先核PDF原页和湖北官方系统":
        return "回看第19期PDF原页和湖北官方侧，逐字段判定冲突来源；高校源只作差异提示。"
    if action == "C1-官网补缺候选但禁止自动写回":
        return "用高校源定位缺口字段，再回PDF原页和湖北官方侧确认；确认前不得写回。"
    if action == "C7-官网源未匹配专业需人工确认专业名":
        return "人工比对专业名称限定词、专业代码和同页上下文，再回PDF原页和湖北官方侧确认是否同一专业。"
    if action in {
        "C4-已有部分来源需补结构化或补湖北行",
        "C3-字段辅证补充结构化后核原页",
    }:
        if files:
            return "复跑或补结构化现有高校来源文件，只输出diff和任务桶；字段事实仍回PDF原页和湖北官方侧。"
        return "先从高校官网入口补湖北2026物理普通批来源，再回PDF原页和湖北官方侧确认。"
    if action == "C2-强辅证抽检并等待湖北官方闭环":
        return "按学校、页列、专业组分层抽检；抽检失败即升级同页列、同校或同组100%核验，并回湖北官方侧确认。"
    if action == "C6-继续搜索高校官网2026湖北计划源":
        return "优先查高校招生网/API/XLSX/PDF/图片计划；无法取得时记录补源失败和搜索证据，最终仍等湖北官方侧。"
    if action == "C5-仅章程规则核特殊要求不能核计划数":
        return "只核录取规则、体检、语种、单科、校区和调剂规则；计划数仍等湖北官方侧或省招办来源。"
    if urls:
        return "复查高校官网入口并补结构化结果，字段事实仍回湖北官方侧确认。"
    return "留存等待湖北官方系统或省招办计划。"


def source_group_key(row):
    action = row.get("官网辅证自动动作", "")
    return (
        row.get("院校代码", ""),
        row.get("院校名称OCR", ""),
        action,
    )


def read_existing_private_rows(path):
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return {row.get("高校侧辅证刷新公开账本ID", ""): row for row in rows}


def build_public_rows(auto_rows, source_seed_rows):
    seed_mapping = seed_by_school(source_seed_rows)
    grouped = defaultdict(list)
    for row in auto_rows:
        grouped[source_group_key(row)].append(row)

    rows = []
    for key, group_rows in grouped.items():
        school_code, school_name, action = key
        source_status_values = [row.get("官网来源状态", "") for row in group_rows]
        strength_values = [row.get("官网证据强度", "") for row in group_rows]
        match_values = [row.get("官网证据匹配状态", "") for row in group_rows]
        plan_values = [row.get("计划数核验状态", "") for row in group_rows]
        diff_values = []
        source_file_values = []
        for row in group_rows:
            diff_values.extend(split_items(row.get("差异字段集合", "")))
            source_file_values.extend(source_files(row))
        source_file_values = sorted(set(source_file_values))
        source_url_values = urls_for_school(school_name, seed_mapping)
        major_ids = [row.get("专业行ID", "") for row in group_rows]
        group_ids = [row.get("专业组出现ID", "") for row in group_rows]
        page_sides = [page_side_key(row) for row in group_rows]
        pages = [row.get("来源页码", "") for row in group_rows]
        action_counter = Counter(row.get("官网辅证自动动作", "") for row in group_rows)
        batch = refresh_batch(action)
        row = {
            "高校侧辅证刷新公开账本ID": stable_id("SCHOOLREFRESH", [school_code, school_name, action]),
            "来源稳定基座自动交叉核验工作台": str(AUTO_WORKBENCH.relative_to(ROOT)),
            "来源高校官网补源种子表": str(SOURCE_SEEDS.relative_to(ROOT)),
            "来源湖北官方公开入口状态快照": str(OFFICIAL_STATUS.relative_to(ROOT)),
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校×高校侧辅证动作",
            "任务粒度": "高校×来源刷新任务",
            **false_gate_values(),
            "执行顺序": "",
            "高校侧刷新批次": batch,
            "高校侧刷新任务类型": refresh_task_type(action),
            "高校侧刷新优先级": refresh_priority(action),
            "院校代码": school_code,
            "院校名称OCR": school_name,
            "官网辅证自动动作": action,
            "闭环优先级": group_rows[0].get("闭环优先级", ""),
            "官网证据强度": compact_join(strength_values),
            "官网来源状态": compact_join(source_status_values),
            "官网证据匹配状态集合": compact_join(match_values),
            "计划数核验状态集合": compact_join(plan_values),
            "差异字段集合": compact_join(diff_values),
            "来源文件类型集合": compact_join(source_file_types(source_file_values, group_rows[0].get("官网来源状态", ""))),
            "公开来源文件数量": str(len(source_file_values)),
            "公开来源文件集合SHA256": set_sha(source_file_values),
            "公开来源URL数量": str(len(source_url_values)),
            "公开来源URL集合SHA256": set_sha(source_url_values),
            "涉及招生明细数": str(len(group_rows)),
            "涉及专业组数": str(len(set(group_ids))),
            "涉及PDF页数": str(len({page for page in pages if page})),
            "涉及页列数": str(len({item for item in page_sides if item})),
            "专业行ID集合SHA256": set_sha(major_ids),
            "专业组ID集合SHA256": set_sha(group_ids),
            "页列集合SHA256": set_sha(page_sides),
            "计划数冲突行数": str(action_counter["C0-冲突先核PDF原页和湖北官方系统"]),
            "官网补缺候选行数": str(action_counter["C1-官网补缺候选但禁止自动写回"]),
            "强辅证抽检行数": str(action_counter["C2-强辅证抽检并等待湖北官方闭环"]),
            "部分来源待结构化行数": str(action_counter["C4-已有部分来源需补结构化或补湖北行"]),
            "继续补源行数": str(action_counter["C6-继续搜索高校官网2026湖北计划源"]),
            "仅章程规则行数": str(action_counter["C5-仅章程规则核特殊要求不能核计划数"]),
            "官网未匹配行数": str(action_counter["C7-官网源未匹配专业需人工确认专业名"]),
            "字段辅证行数": str(action_counter["C3-字段辅证补充结构化后核原页"]),
            "疑似学费读作计划数行数": str(
                sum(1 for item in group_rows if item.get("疑似OCR把学费读入计划数") == "true")
            ),
            "需要PDF原页100%核验行数": str(
                len(group_rows)
                if action
                in {
                    "C0-冲突先核PDF原页和湖北官方系统",
                    "C1-官网补缺候选但禁止自动写回",
                    "C7-官网源未匹配专业需人工确认专业名",
                }
                else 0
            ),
            "建议抽检行数": str(
                len(group_rows) if action == "C2-强辅证抽检并等待湖北官方闭环" else 0
            ),
            "建议补结构化行数": str(
                len(group_rows)
                if action
                in {
                    "C4-已有部分来源需补结构化或补湖北行",
                    "C3-字段辅证补充结构化后核原页",
                }
                else 0
            ),
            "建议继续补源行数": str(
                len(group_rows) if action == "C6-继续搜索高校官网2026湖北计划源" else 0
            ),
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "高校官网源刷新状态": "pending_school_source_refresh",
            "高校官网或招生章程辅证状态": "pending_school_evidence_refresh_or_review",
            "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
            "公开安全策略": "公开表只保存学校级动作、计数、集合SHA和公开来源相对路径数量；不保存人工字段记录、登录态、截图路径或最终结论。",
            "下一步": recommended_action(action, source_file_values, source_url_values),
        }
        rows.append(row)

    rows.sort(key=lambda r: (r["高校侧刷新优先级"], r["院校代码"], r["官网辅证自动动作"]))
    for idx, row in enumerate(rows, 1):
        row["执行顺序"] = str(idx)
    return rows


def private_rows_from_public(public_rows, auto_rows, source_seed_rows, existing_private):
    seed_mapping = seed_by_school(source_seed_rows)
    auto_by_key = defaultdict(list)
    for row in auto_rows:
        auto_by_key[source_group_key(row)].append(row)

    result = []
    for public in public_rows:
        key = (
            public.get("院校代码", ""),
            public.get("院校名称OCR", ""),
            public.get("官网辅证自动动作", ""),
        )
        group_rows = auto_by_key.get(key, [])
        source_file_values = sorted({file for row in group_rows for file in source_files(row)})
        source_url_values = urls_for_school(public.get("院校名称OCR", ""), seed_mapping)
        existing = existing_private.get(public["高校侧辅证刷新公开账本ID"], {})
        private = {field: public.get(field, "") for field in PUBLIC_FIELDS}
        private.update(
            {
                "私有工作台用途": "记录高校官网源复跑、PDF原页核验、湖北官方侧核验和抽检升级结论；不提交公开仓库。",
                "涉及专业行ID集合": compact_join(row.get("专业行ID", "") for row in group_rows),
                "涉及专业组ID集合": compact_join(row.get("专业组出现ID", "") for row in group_rows),
                "页列集合": compact_join(page_side_key(row) for row in group_rows),
                "公开来源文件集合": compact_join(source_file_values),
                "公开来源URL集合": compact_join(source_url_values),
                "官网来源检索提示": compact_join(row.get("下一步", "") for row in source_seed_rows if row.get("学校名称") == key[1]),
                "建议自动复跑命令或动作": recommended_action(public.get("官网辅证自动动作", ""), source_file_values, source_url_values),
            }
        )
        for field in PRIVATE_MANUAL_FIELDS:
            private[field] = existing.get(field, "")
        result.append(private)
    return result


def public_text_safe(paths):
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    return all(token not in text for token in FORBIDDEN_PUBLIC_TOKENS)


def main():
    auto_rows = read_csv(AUTO_WORKBENCH)
    source_seed_rows = read_csv(SOURCE_SEEDS)
    official_status = json.loads(OFFICIAL_STATUS.read_text(encoding="utf-8"))

    public_rows = build_public_rows(auto_rows, source_seed_rows)
    existing_private = read_existing_private_rows(PRIVATE_OUTPUT)
    private_rows = private_rows_from_public(public_rows, auto_rows, source_seed_rows, existing_private)

    write_csv(PRIVATE_OUTPUT, private_rows, PRIVATE_FIELDS)
    write_csv(OUTPUT, public_rows, PUBLIC_FIELDS)

    public_action_row_counts = Counter(row.get("官网辅证自动动作") for row in public_rows)
    public_batch_counts = Counter(row.get("高校侧刷新批次") for row in public_rows)
    public_task_type_counts = Counter(row.get("高校侧刷新任务类型") for row in public_rows)
    public_file_type_counts = Counter(row.get("来源文件类型集合") for row in public_rows)
    major_action_counts = Counter(row.get("官网辅证自动动作") for row in auto_rows)
    source_status_major_counts = Counter(row.get("官网来源状态") for row in auto_rows)

    summary = {
        "status": "issue19_stable_foundation_school_source_refresh_public_ledger_not_final",
        "generated_by": "build_issue19_stable_foundation_school_source_refresh_queue.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_auto_workbench": str(AUTO_WORKBENCH.relative_to(ROOT)),
        "source_school_seed_table": str(SOURCE_SEEDS.relative_to(ROOT)),
        "source_official_public_status": str(OFFICIAL_STATUS.relative_to(ROOT)),
        "official_public_plan_page_can_finalize": bool(
            official_status.get("official_plan_page", {}).get("can_finalize")
        ),
        "zspt_platform_can_finalize": bool(official_status.get("zspt_platform", {}).get("can_finalize")),
        "input_files": input_snapshot(ROOT, [AUTO_WORKBENCH, SOURCE_SEEDS, OFFICIAL_STATUS]),
        "output_table": str(OUTPUT.relative_to(ROOT)),
        "private_workbench_generated": True,
        "private_workbench_sha256": sha256_file(PRIVATE_OUTPUT),
        "row_grain": "高校×高校侧辅证动作",
        "public_row_count": len(public_rows),
        "private_row_count": len(private_rows),
        "source_auto_workbench_row_count": len(auto_rows),
        "unique_public_ledger_id_count": len({row.get("高校侧辅证刷新公开账本ID") for row in public_rows}),
        "unique_school_count": len({row.get("院校代码") for row in public_rows}),
        "unique_school_action_count": len(
            {
                (row.get("院校代码"), row.get("官网辅证自动动作"))
                for row in public_rows
            }
        ),
        "public_action_row_counts": dict(public_action_row_counts),
        "public_batch_counts": dict(public_batch_counts),
        "public_task_type_counts": dict(public_task_type_counts),
        "public_file_type_counts": dict(public_file_type_counts),
        "major_action_counts": dict(major_action_counts),
        "source_status_major_counts": dict(source_status_major_counts),
        "source_file_available_public_row_count": sum(
            1 for row in public_rows if int(row.get("公开来源文件数量", "0") or 0) > 0
        ),
        "source_url_available_public_row_count": sum(
            1 for row in public_rows if int(row.get("公开来源URL数量", "0") or 0) > 0
        ),
        "immediate_pdf_review_major_count": sum(
            int(row.get("需要PDF原页100%核验行数", "0") or 0) for row in public_rows
        ),
        "sample_review_major_count": sum(
            int(row.get("建议抽检行数", "0") or 0) for row in public_rows
        ),
        "structure_refresh_major_count": sum(
            int(row.get("建议补结构化行数", "0") or 0) for row in public_rows
        ),
        "source_search_major_count": sum(
            int(row.get("建议继续补源行数", "0") or 0) for row in public_rows
        ),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "policy": {
            "official_boundary": "高校官网刷新队列只能扩大double-check覆盖，不能替代湖北官方系统或省招办计划。",
            "manual_boundary": "C0/C1/C7必须回PDF原页和湖北官方侧；C2抽检失败升级同页列、同校或同组100%核验。",
            "privacy_boundary": "复跑结果、人工核验结论和备注只写入Git忽略的私有工作台。",
        },
        "next_steps": [
            "优先处理S0和S1：计划数冲突、官网补缺、官网未匹配专业名。",
            "并行处理S2和S4：已有来源补结构化、缺源学校继续搜索高校官网2026湖北计划。",
            "S3强辅证只做分层抽检，抽检失败立即升级。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not public_text_safe([OUTPUT, SUMMARY_OUTPUT]):
        raise SystemExit("公开输出命中禁止公开 token")

    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {PRIVATE_OUTPUT.relative_to(ROOT)}：{len(private_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
