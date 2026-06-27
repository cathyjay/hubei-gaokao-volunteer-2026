#!/usr/bin/env python3
import csv
import hashlib
import html
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SCHOOL_REFRESH_LEDGER = (
    ROOT / "data/working/issue19-stable-foundation-school-source-refresh-public-ledger.csv"
)
AUTO_WORKBENCH = (
    ROOT / "data/working/issue19-stable-foundation-auto-official-crosscheck-workbench.csv"
)
SOURCE_SEEDS = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv"
OFFICIAL_LIVE_RECHECK = ROOT / "data/working/issue19-official-public-entry-live-recheck.json"

PUBLIC_OUTPUT = ROOT / "data/working/issue19-c4-c6-school-source-refresh-execution-packets.csv"
SUMMARY_OUTPUT = (
    ROOT / "data/working/issue19-c4-c6-school-source-refresh-execution-packets-summary.json"
)

PRIVATE_OUTPUT_DIR = (
    ROOT / "private/review-assets/issue19-c4-c6-school-source-refresh-execution-packets"
)
PRIVATE_PACKET_DIR = PRIVATE_OUTPUT_DIR / "packets"
PRIVATE_MASTER_CSV = PRIVATE_OUTPUT_DIR / "c4-c6-source-refresh-private-detail-workbench.csv"
PRIVATE_INDEX_CSV = PRIVATE_OUTPUT_DIR / "c4-c6-source-refresh-private-index.csv"
PRIVATE_INDEX_HTML = PRIVATE_OUTPUT_DIR / "index.html"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_c4_c6_school_source_refresh_execution_packets"

C4_ACTION = "C4-已有部分来源需补结构化或补湖北行"
C6_ACTION = "C6-继续搜索高校官网2026湖北计划源"
TARGET_ACTIONS = {C4_ACTION, C6_ACTION}

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
    "C4C6高校源刷新执行包ID",
    "来源高校侧辅证刷新公开账本",
    "来源稳定基座自动交叉核验工作台",
    "来源高校官网补源种子表",
    "来源湖北官方活体复查",
    "来源本地私有执行包",
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
    "执行总序",
    "执行泳道",
    "执行优先级",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "高校侧刷新批次",
    "高校侧刷新任务类型",
    "来源文件类型集合",
    "种子官网URL数量",
    "种子本地留存路径状态",
    "涉及招生明细数",
    "涉及专业组数",
    "涉及PDF页数",
    "涉及页列数",
    "专业行ID集合SHA256",
    "专业组ID集合SHA256",
    "页列集合SHA256",
    "需补结构化明细数",
    "需继续补源明细数",
    "私有明细CSV证据编号",
    "私有明细CSV_SHA256",
    "私有明细行数",
    "自动补源目标",
    "结构化验收字段",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源刷新状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_DETAIL_FIELDS = [
    "C4C6私有明细任务ID",
    "来源C4C6执行包ID",
    "来源高校侧辅证刷新公开账本ID",
    "来源稳定基座自动交叉核验任务ID",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "执行泳道",
    "执行优先级",
    "专业行ID",
    "专业组出现ID",
    "院校专业组代码OCR规范化",
    "来源页码",
    "版面列",
    "页码版面键",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注短摘",
    "OCR专业计划数候选",
    "OCR学费候选",
    "OCR再选科目候选",
    "官网证据强度",
    "官网来源状态",
    "官网证据匹配状态",
    "计划数核验状态",
    "最佳官网来源文件",
    "最佳官网专业名称",
    "最佳官网专业代号",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "种子官网URL集合",
    "种子本地留存路径集合",
    "建议自动补源动作",
    "结构化验收字段",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源刷新状态",
    "字段事实写回状态",
    "本轮是否已补源或结构化",
    "本轮补源或结构化结果文件",
    "本轮结果SHA256",
    "PDF原页人工核验结论",
    "湖北官方侧核验结论",
    "高校官网源复跑结论",
    "抽检或升级结论",
    "复核备注",
]

PRIVATE_INDEX_FIELDS = [
    "C4C6高校源刷新执行包ID",
    "执行总序",
    "执行泳道",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "私有明细CSV相对路径",
    "私有明细CSV_SHA256",
    "私有明细行数",
    "种子官网URL数量",
    "种子本地留存路径状态",
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
    "专业名称及备注短摘",
    "OCR专业计划数候选",
    "OCR学费候选",
    "OCR再选科目候选",
    "最佳官网专业名称",
    "最佳官网计划数",
    "最佳官网学费",
    "最佳官网选科",
    "人工核验结论",
    "湖北官方侧核验结论",
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
    return "；".join(sorted({str(item).strip() for item in items if str(item).strip()}))


def set_sha(items):
    return sha256_text("\n".join(sorted({str(item).strip() for item in items if str(item).strip()})))


def as_int(value):
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


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


def seed_by_school(rows):
    mapping = defaultdict(list)
    for row in rows:
        mapping[row.get("学校名称", "")].append(row)
    return mapping


def seed_urls(seed_rows):
    return sorted({row.get("官网URL", "").strip() for row in seed_rows if row.get("官网URL", "").strip()})


def seed_local_paths(seed_rows):
    return sorted({row.get("本地留存路径", "").strip() for row in seed_rows if row.get("本地留存路径", "").strip()})


def seed_path_status(paths):
    if not paths:
        return "S0-无本地留存路径"
    normalized = [path for path in paths if path and path != "未留存"]
    if not normalized:
        return "S1-种子记录未留存"
    return "S2-种子有本地留存路径"


def source_lane(row):
    action = row.get("官网辅证自动动作", "")
    source_type = row.get("来源文件类型集合", "")
    url_count = as_int(row.get("公开来源URL数量", "0"))
    if action == C6_ACTION and url_count == 0:
        return "X0-C6无官网计划入口需搜索"
    if action == C6_ACTION:
        return "X1-C6有入口待获取湖北计划"
    if action == C4_ACTION and "未留存来源文件" in source_type:
        return "X2-C4有入口但未留存结果"
    return "X3-C4已有部分来源待结构化"


def lane_priority(lane):
    order = {
        "X0-C6无官网计划入口需搜索": "00-P0补源",
        "X1-C6有入口待获取湖北计划": "01-P0取数",
        "X2-C4有入口但未留存结果": "02-P1抓取",
        "X3-C4已有部分来源待结构化": "03-P1结构化",
    }
    return order.get(lane, "09-P3留存")


def source_goal(lane):
    if lane == "X0-C6无官网计划入口需搜索":
        return "查找高校招生网、招生计划查询 API、招生公众号或附件，补 2026 湖北物理普通本科计划源。"
    if lane == "X1-C6有入口待获取湖北计划":
        return "用已知官网入口获取或截图 2026 湖北物理普通本科计划结果，并保存来源证据。"
    if lane == "X2-C4有入口但未留存结果":
        return "复现官网入口查询并留存湖北 2026 物理普通本科结果，再抽取逐专业结构化行。"
    return "复跑或转录已有部分来源，抽取湖北物理普通本科逐专业行，生成字段级 diff。"


def detail_action(lane):
    if lane.startswith("X0"):
        return "先补官网计划源；若仍不可得，记录检索证据和不可得原因。"
    if lane.startswith("X1") or lane.startswith("X2"):
        return "抓取或人工导出官网湖北计划结果，结构化为逐专业行。"
    return "补结构化现有来源中的湖北物理普通本科逐专业行。"


def source_file_name(packet_id, order, school_code, action):
    action_label = "c4" if action == C4_ACTION else "c6"
    safe_school = "".join(ch for ch in school_code.lower() if ch.isalnum()) or "school"
    return f"{order:02d}-{safe_school}-{action_label}-{packet_id[-8:]}.csv"


def private_manual_defaults():
    return {
        "本轮是否已补源或结构化": "false",
        "本轮补源或结构化结果文件": "",
        "本轮结果SHA256": "",
        "PDF原页人工核验结论": "",
        "湖北官方侧核验结论": "",
        "高校官网源复跑结论": "",
        "抽检或升级结论": "",
        "复核备注": "",
    }


def generate_html(index_rows):
    lines = [
        "<!doctype html>",
        '<meta charset="utf-8">',
        "<title>C4/C6 高校源刷新执行包</title>",
        "<h1>C4/C6 高校源刷新执行包</h1>",
        "<p>本页只索引 Git 忽略目录下的私有执行 CSV。字段事实仍需 PDF 原页、湖北官方侧和必要高校辅证闭环。</p>",
        "<table border=\"1\" cellspacing=\"0\" cellpadding=\"4\">",
        "<thead><tr>"
        + "".join(f"<th>{html.escape(field)}</th>" for field in PRIVATE_INDEX_FIELDS)
        + "</tr></thead>",
        "<tbody>",
    ]
    for row in index_rows:
        lines.append(
            "<tr>"
            + "".join(f"<td>{html.escape(str(row.get(field, '')))}</td>" for field in PRIVATE_INDEX_FIELDS)
            + "</tr>"
        )
    lines.extend(["</tbody></table>"])
    return "\n".join(lines)


def main():
    school_rows = [
        row for row in read_csv(SCHOOL_REFRESH_LEDGER) if row.get("官网辅证自动动作") in TARGET_ACTIONS
    ]
    auto_rows = [row for row in read_csv(AUTO_WORKBENCH) if row.get("官网辅证自动动作") in TARGET_ACTIONS]
    seeds = seed_by_school(read_csv(SOURCE_SEEDS))
    live_recheck = json.loads(OFFICIAL_LIVE_RECHECK.read_text(encoding="utf-8"))

    auto_by_key = defaultdict(list)
    for row in auto_rows:
        auto_by_key[(row.get("院校代码", ""), row.get("院校名称OCR", ""), row.get("官网辅证自动动作", ""))].append(row)

    PRIVATE_PACKET_DIR.mkdir(parents=True, exist_ok=True)
    for old in PRIVATE_PACKET_DIR.glob("*.csv"):
        old.unlink()

    public_rows = []
    private_detail_rows = []
    private_index_rows = []

    for order, row in enumerate(sorted(school_rows, key=lambda item: as_int(item.get("执行顺序"))), 1):
        key = (row.get("院校代码", ""), row.get("院校名称OCR", ""), row.get("官网辅证自动动作", ""))
        details = auto_by_key.get(key, [])
        seed_rows = seeds.get(row.get("院校名称OCR", ""), [])
        urls = seed_urls(seed_rows)
        local_paths = seed_local_paths(seed_rows)
        lane = source_lane(row)
        packet_id = stable_id("C4C6PACKET", [*key])
        packet_name = source_file_name(packet_id, order, row.get("院校代码", ""), row.get("官网辅证自动动作", ""))
        packet_path = PRIVATE_PACKET_DIR / packet_name
        packet_rel = packet_path.relative_to(PRIVATE_OUTPUT_DIR)

        detail_rows = []
        for idx, detail in enumerate(details, 1):
            detail_row = {
                "C4C6私有明细任务ID": stable_id(
                    "C4C6DETAIL", [packet_id, detail.get("稳定基座自动交叉核验任务ID", ""), idx]
                ),
                "来源C4C6执行包ID": packet_id,
                "来源高校侧辅证刷新公开账本ID": row.get("高校侧辅证刷新公开账本ID", ""),
                "来源稳定基座自动交叉核验任务ID": detail.get("稳定基座自动交叉核验任务ID", ""),
                "院校代码": detail.get("院校代码", ""),
                "院校名称OCR": detail.get("院校名称OCR", ""),
                "官网辅证自动动作": detail.get("官网辅证自动动作", ""),
                "执行泳道": lane,
                "执行优先级": lane_priority(lane),
                "专业行ID": detail.get("专业行ID", ""),
                "专业组出现ID": detail.get("专业组出现ID", ""),
                "院校专业组代码OCR规范化": detail.get("院校专业组代码OCR规范化", ""),
                "来源页码": detail.get("来源页码", ""),
                "版面列": detail.get("版面列", ""),
                "页码版面键": page_side_key(detail),
                "专业组内专业序号": detail.get("专业组内专业序号", ""),
                "专业代号OCR": detail.get("专业代号OCR", ""),
                "专业名称及备注短摘": detail.get("专业名称及备注短摘", ""),
                "OCR专业计划数候选": detail.get("OCR专业计划数候选", ""),
                "OCR学费候选": detail.get("OCR学费候选", ""),
                "OCR再选科目候选": detail.get("OCR再选科目候选", ""),
                "官网证据强度": detail.get("官网证据强度", ""),
                "官网来源状态": detail.get("官网来源状态", ""),
                "官网证据匹配状态": detail.get("官网证据匹配状态", ""),
                "计划数核验状态": detail.get("计划数核验状态", ""),
                "最佳官网来源文件": detail.get("最佳官网来源文件", ""),
                "最佳官网专业名称": detail.get("最佳官网专业名称", ""),
                "最佳官网专业代号": detail.get("最佳官网专业代号", ""),
                "最佳官网计划数": detail.get("最佳官网计划数", ""),
                "最佳官网学费": detail.get("最佳官网学费", ""),
                "最佳官网选科": detail.get("最佳官网选科", ""),
                "种子官网URL集合": compact_join(urls),
                "种子本地留存路径集合": compact_join(local_paths),
                "建议自动补源动作": detail_action(lane),
                "结构化验收字段": "专业名称；专业代号或专业代码；计划数；学费；选科；学制；校区；备注限制；来源URL或文件SHA",
                "PDF原页核页状态": "pending_manual_pdf_review",
                "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
                "高校官网源刷新状态": "pending_school_source_refresh_or_structure",
                "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
                **private_manual_defaults(),
            }
            detail_rows.append(detail_row)

        write_csv(packet_path, detail_rows, PRIVATE_DETAIL_FIELDS)
        packet_sha = sha256_file(packet_path)
        private_detail_rows.extend(detail_rows)

        public = {
            "C4C6高校源刷新执行包ID": packet_id,
            "来源高校侧辅证刷新公开账本": str(SCHOOL_REFRESH_LEDGER.relative_to(ROOT)),
            "来源稳定基座自动交叉核验工作台": str(AUTO_WORKBENCH.relative_to(ROOT)),
            "来源高校官网补源种子表": str(SOURCE_SEEDS.relative_to(ROOT)),
            "来源湖北官方活体复查": str(OFFICIAL_LIVE_RECHECK.relative_to(ROOT)),
            "来源本地私有执行包": "local_c4_c6_school_source_refresh_packet_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "高校×C4C6来源刷新执行包",
            "任务粒度": "高校×动作×逐专业私有执行明细",
            **false_gate_values(),
            "执行总序": str(order),
            "执行泳道": lane,
            "执行优先级": lane_priority(lane),
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "官网辅证自动动作": row.get("官网辅证自动动作", ""),
            "高校侧刷新批次": row.get("高校侧刷新批次", ""),
            "高校侧刷新任务类型": row.get("高校侧刷新任务类型", ""),
            "来源文件类型集合": row.get("来源文件类型集合", ""),
            "种子官网URL数量": str(len(urls)),
            "种子本地留存路径状态": seed_path_status(local_paths),
            "涉及招生明细数": row.get("涉及招生明细数", ""),
            "涉及专业组数": row.get("涉及专业组数", ""),
            "涉及PDF页数": row.get("涉及PDF页数", ""),
            "涉及页列数": row.get("涉及页列数", ""),
            "专业行ID集合SHA256": row.get("专业行ID集合SHA256", ""),
            "专业组ID集合SHA256": row.get("专业组ID集合SHA256", ""),
            "页列集合SHA256": row.get("页列集合SHA256", ""),
            "需补结构化明细数": row.get("建议补结构化行数", "0"),
            "需继续补源明细数": row.get("建议继续补源行数", "0"),
            "私有明细CSV证据编号": f"c4-c6-packet-{order:02d}",
            "私有明细CSV_SHA256": packet_sha,
            "私有明细行数": str(len(detail_rows)),
            "自动补源目标": source_goal(lane),
            "结构化验收字段": "专业名称；专业代号或专业代码；计划数；学费；选科；学制；校区；备注限制；来源URL或文件SHA",
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "高校官网源刷新状态": "pending_school_source_refresh_or_structure",
            "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
            "公开安全策略": "公开层只保存高校包、计数、集合SHA和私有包SHA；不保存专业明细字段值、OCR原文、登录态、人工核验记录或最终建议。",
            "下一步": source_goal(lane) + " 完成后只生成 diff 或候选线索，仍需 PDF 原页和湖北官方侧闭环。",
        }
        public_rows.append(public)
        private_index_rows.append(
            {
                "C4C6高校源刷新执行包ID": packet_id,
                "执行总序": str(order),
                "执行泳道": lane,
                "院校代码": row.get("院校代码", ""),
                "院校名称OCR": row.get("院校名称OCR", ""),
                "官网辅证自动动作": row.get("官网辅证自动动作", ""),
                "私有明细CSV相对路径": str(packet_rel),
                "私有明细CSV_SHA256": packet_sha,
                "私有明细行数": str(len(detail_rows)),
                "种子官网URL数量": str(len(urls)),
                "种子本地留存路径状态": seed_path_status(local_paths),
            }
        )

    write_csv(PUBLIC_OUTPUT, public_rows, PUBLIC_FIELDS)
    write_csv(PRIVATE_MASTER_CSV, private_detail_rows, PRIVATE_DETAIL_FIELDS)
    write_csv(PRIVATE_INDEX_CSV, private_index_rows, PRIVATE_INDEX_FIELDS)
    PRIVATE_INDEX_HTML.write_text(generate_html(private_index_rows), encoding="utf-8")

    lane_counts = Counter(row["执行泳道"] for row in public_rows)
    lane_detail_counts = Counter()
    for row in public_rows:
        lane_detail_counts[row["执行泳道"]] += as_int(row["私有明细行数"])

    summary = {
        "status": "issue19_c4_c6_school_source_refresh_execution_packets_not_final",
        "generated_by": "build_issue19_c4_c6_school_source_refresh_execution_packets.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_school_refresh_ledger": str(SCHOOL_REFRESH_LEDGER.relative_to(ROOT)),
        "source_auto_workbench": str(AUTO_WORKBENCH.relative_to(ROOT)),
        "source_school_seed_table": str(SOURCE_SEEDS.relative_to(ROOT)),
        "source_official_live_recheck": str(OFFICIAL_LIVE_RECHECK.relative_to(ROOT)),
        "official_can_finalize": bool(
            live_recheck.get("current_conclusion", {}).get("can_finalize_admission_plan_from_public_entry")
        ),
        "official_without_login_structured_plan_available": bool(
            live_recheck.get("current_conclusion", {}).get("can_get_official_structured_plan_without_login")
        ),
        "output_public_table": str(PUBLIC_OUTPUT.relative_to(ROOT)),
        "public_packet_count": len(public_rows),
        "private_detail_row_count": len(private_detail_rows),
        "private_index_row_count": len(private_index_rows),
        "unique_school_count": len({row["院校代码"] for row in public_rows}),
        "unique_school_action_count": len({(row["院校代码"], row["官网辅证自动动作"]) for row in public_rows}),
        "c4_packet_count": sum(1 for row in public_rows if row["官网辅证自动动作"] == C4_ACTION),
        "c6_packet_count": sum(1 for row in public_rows if row["官网辅证自动动作"] == C6_ACTION),
        "c4_detail_count": sum(as_int(row["需补结构化明细数"]) for row in public_rows),
        "c6_detail_count": sum(as_int(row["需继续补源明细数"]) for row in public_rows),
        "lane_packet_counts": dict(lane_counts),
        "lane_detail_counts": dict(lane_detail_counts),
        "seed_url_packet_count": sum(1 for row in public_rows if as_int(row["种子官网URL数量"]) > 0),
        "seed_without_url_packet_count": sum(1 for row in public_rows if as_int(row["种子官网URL数量"]) == 0),
        "seed_local_path_status_counts": dict(Counter(row["种子本地留存路径状态"] for row in public_rows)),
        "private_master_csv_sha256": sha256_file(PRIVATE_MASTER_CSV),
        "private_index_csv_sha256": sha256_file(PRIVATE_INDEX_CSV),
        "private_index_html_sha256": sha256_file(PRIVATE_INDEX_HTML),
        "private_packet_csv_count": len(list(PRIVATE_PACKET_DIR.glob("*.csv"))),
        "field_writeback_allowed_count": 0,
        "recommendation_basis_allowed_count": 0,
        "school_major_suggestion_allowed_count": 0,
        "official_plan_replacement_allowed_count": 0,
        "final_available_count": 0,
        "next_stage_available_count": 0,
        "policy": {
            "goal": "把 C4/C6 最大自动补源缺口拆成可并行执行包，减少后续人工核验前的查找和结构化成本。",
            "boundary": "本包只产生高校官网补源、结构化 diff 和核验入口；字段事实仍需第19期 PDF 原页、湖北官方侧和必要高校辅证闭环。",
            "privacy": "公开层不保存逐专业字段值、OCR 原文、私有路径、登录态或人工记录。",
        },
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not public_text_safe([PUBLIC_OUTPUT, SUMMARY_OUTPUT]):
        raise SystemExit("公开 C4/C6 执行包包含禁止公开内容")

    print(f"写出 {PUBLIC_OUTPUT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"写出私有 C4/C6 执行材料：{PRIVATE_OUTPUT_DIR.relative_to(ROOT)}")


def public_text_safe(paths):
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    return all(token not in text for token in FORBIDDEN_PUBLIC_TOKENS)


if __name__ == "__main__":
    main()
