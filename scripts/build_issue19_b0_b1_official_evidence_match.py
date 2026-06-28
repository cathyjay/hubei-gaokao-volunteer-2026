#!/usr/bin/env python3
import csv
import html
import json
import re
import zipfile
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SEEDS = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-source-seeds.csv"
ADMISSION_DETAIL = ROOT / "data/working/issue19-candidate-v3-b0-b1-admission-detail-official-crosscheck.csv"
EXTERNAL_DIR = ROOT / "data/external/issue19-b0-b1-official-sources"
SAMPLE_OFFICIAL_DIR = ROOT / "data/external/issue19-sample-school-official"

NORMALIZED_OUTPUT = ROOT / "data/working/issue19-b0-b1-retained-official-plan-normalized.csv"
MATCH_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-evidence-match.csv"
DETAIL_LEDGER_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-admission-detail-evidence-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-candidate-v3-b0-b1-official-evidence-match-summary.json"


SOURCE_FILES_BY_SCHOOL = {
    "中国传媒大学": ["cuc-2026-hubei-physics-normal-zsjh.json"],
    "山东大学": ["sdu-2026-hubei-physics-normal-zsjh.json"],
    "兰州大学": ["lzu-2026-hubei-physics-normal-zsjh.json"],
    "西北民族大学": ["xbmu-2026-hubei-physics-normal-zsjh.json"],
    "成都信息工程大学": ["cuit-2026-undergraduate-plan.html"],
    "江汉大学": ["jhun-2026-hubei-physics-normal-lqxx2.json"],
    "天津外国语大学": ["tjfsu-2026-hubei-physics-normal-zsjh.json"],
    "西安财经大学": ["xaufe-2026-hubei-physics-normal.json"],
    "西安医学院": ["xiyi-2026-hubei-physics-normal.json"],
    "西安邮电大学": [
        "xupt-2026-hubei-physics-normal.json",
        "xupt-2026-hubei-physics-sino.json",
    ],
    "喀什大学": ["ksu-2026-undergraduate-plan.xlsx"],
    "杭州电子科技大学": ["hdu-2026-hubei-plan.xlsx"],
    "忻州师范学院": ["xztu-2026-hubei-physics-plan-extracted.csv"],
    "山东工商学院": ["sdtbu-2026-hubei-physics-plan-extracted.csv"],
    "江苏理工学院": ["jsut-2026-hubei-physics-plan-extracted.csv"],
    "南宁学院": ["unn-2026-undergraduate-plan-page.html"],
    "浙江工业大学": ["zjut-2026-hubei-physics-plan-extracted.csv"],
}

NORMALIZED_FIELDS = [
    "学校名称",
    "官方来源文件",
    "证据类型",
    "年份",
    "省份",
    "科类",
    "批次",
    "类别",
    "专业组",
    "专业代号",
    "专业代码",
    "专业名称",
    "专业备注",
    "计划数",
    "学制",
    "学费",
    "校区",
    "选科",
    "可核字段",
    "局限性",
    "年份证据说明",
]

MATCH_FIELDS = [
    "招生明细主表行ID",
    "主表粒度",
    "是否真实招生明细",
    "是否0明细占位",
    "来源页码",
    "复核批次",
    "入口类型",
    "院校代码",
    "院校名称OCR",
    "2026院校专业组代码",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR",
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "学费OCR候选",
    "专业偏好方向",
    "专业风险类型",
    "机器专业接受度初判",
    "调剂影响初判",
    "官网来源状态",
    "官网证据匹配状态",
    "官网证据覆盖结论",
    "最佳官网来源文件",
    "最佳官网专业名称",
    "最佳官网计划数",
    "最佳官网专业组",
    "最佳官网专业代号",
    "最佳官网学费",
    "最佳官网选科",
    "专业名称匹配方式",
    "专业名称匹配分",
    "计划数核验状态",
    "仍需核验",
]

DETAIL_LEDGER_FIELDS = [
    "招生明细主表行ID",
    "主表粒度",
    "是否真实招生明细",
    "是否0明细占位",
    "来源页码",
    "复核批次",
    "入口类型",
    "院校代码",
    "院校名称OCR",
    "2026院校专业组代码",
    "专业组内专业序号",
    "专业代号OCR",
    "专业名称及备注OCR",
    "再选科目OCR候选",
    "专业计划数OCR候选",
    "学费OCR候选",
    "专业偏好方向",
    "专业风险类型",
    "机器专业接受度初判",
    "调剂影响初判",
    "官网来源状态",
    "官网证据匹配状态",
    "官网证据覆盖结论",
    "最佳官网来源文件",
    "最佳官网专业名称",
    "最佳官网计划数",
    "最佳官网专业组",
    "最佳官网专业代号",
    "最佳官网学费",
    "最佳官网选科",
    "专业名称匹配方式",
    "专业名称匹配分",
    "计划数核验状态",
    "保真处理状态",
    "保真说明",
    "仍需核验",
    "可进入最终专业列表",
    "可进入下一阶段",
]


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._table_depth = 0
        self._current_table = None
        self._current_row = None
        self._current_cell = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self._table_depth += 1
            self._current_table = []
            self.tables.append(self._current_table)
        elif tag == "tr" and self._table_depth:
            self._current_row = []
        elif tag in {"td", "th"} and self._table_depth and self._current_row is not None:
            self._current_cell = []
        elif tag == "br" and self._current_cell is not None:
            self._current_cell.append(" ")

    def handle_data(self, data):
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"td", "th"} and self._current_cell is not None:
            text = html.unescape("".join(self._current_cell))
            self._current_row.append(" ".join(text.split()))
            self._current_cell = None
        elif tag == "tr" and self._table_depth and self._current_row is not None:
            if self._current_row:
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag == "table" and self._table_depth:
            self._table_depth -= 1


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_int(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("［", "").replace("[", "")
    match = re.search(r"\d+", text)
    if not match:
        return None
    return int(match.group(0))


def normalize_major_name(value):
    text = str(value or "")
    text = re.sub(r"[A-Z]\d{3}\s*[\u4e00-\u9fff（）()]+$", "", text)
    text = text.replace("院校专业组及专业代号", "")
    text = text.replace("英（", "英语（")
    replacements = {
        "菩英": "菁英",
        "入工智能": "人工智能",
        "百动化": "自动化",
        "直动化": "自动化",
        "生木": "土木",
        "士木": "土木",
        "工得": "工程",
        "浓车": "汽车",
        "汔车": "汽车",
        "项自": "项目",
        "南务": "商务",
        "國译": "翻译",
        "国译": "翻译",
        "葵语": "英语",
        "语盲": "语言",
        "华学": "化学",
        "顶测": "预测",
        "准碩": "准确",
        "益计": "会计",
        "〉": ")",
        "〈": "(",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"（含.*?）", "", text)
    text = re.sub(r"\(含.*?\)", "", text)
    text = re.sub(r"（办学地点.*?）", "", text)
    text = re.sub(r"\(办学地点.*?\)", "", text)
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text).lower()


KEY_MAJOR_QUALIFIERS = [
    "面向武汉",
    "面向武",
    "中外合作",
    "英才班",
    "卓越班",
    "实验班",
    "智能与软件实验",
    "游戏科学",
    "师范",
]


def missing_key_qualifiers(target, official_name):
    return [
        qualifier
        for qualifier in KEY_MAJOR_QUALIFIERS
        if qualifier in target and qualifier not in official_name
    ]


def compact_for_similarity(value):
    text = re.sub(r"(要求|高考|外语|单科|成绩|不得|低于|满分|语种|英语|法语)", "", value)
    text = re.sub(r"(办学地点|校区|色弱|色盲|不予录取|各种颜色|导线|按键|信号灯|几何图形)", "", text)
    text = re.sub(r"(国际注册|课程培训费|学费|转入|其他专业)", "", text)
    return text


def similarity_score(target, official_name):
    target_compact = compact_for_similarity(target)
    official_compact = compact_for_similarity(official_name)
    if len(target_compact) < 4 or len(official_compact) < 4:
        return 0
    ratio = SequenceMatcher(None, target_compact, official_compact).ratio()
    if ratio >= 0.92:
        return 82
    if ratio >= 0.86 and (target_compact[:2] == official_compact[:2]):
        return 72
    return 0


def has_next_school_noise(text):
    return bool(re.search(r"[A-Z]\d{3,4}\s*[\u4e00-\u9fff]{2,}", str(text or "")))


def clean_cell(row, index):
    if index >= len(row):
        return ""
    return str(row[index]).strip()


def parse_table_html(path, school_name):
    parser = TableParser()
    parser.feed(path.read_text(encoding="utf-8-sig", errors="ignore"))
    rows = []
    for table in parser.tables:
        if not table:
            continue
        header_index = None
        for index, row in enumerate(table[:5]):
            if any("专业" in cell for cell in row) and any("湖北" == cell for cell in row):
                header_index = index
                break
        if header_index is None:
            continue
        header = table[header_index]
        major_index = next((i for i, cell in enumerate(header) if cell in {"专业", "专业名称"}), None)
        hubei_index = next((i for i, cell in enumerate(header) if cell == "湖北"), None)
        if major_index is None or hubei_index is None:
            continue
        code_index = next((i for i, cell in enumerate(header) if cell == "专业代码"), None)
        subject_index = next((i for i, cell in enumerate(header) if "选考" in cell), None)
        fee_index = next((i for i, cell in enumerate(header) if cell == "学费"), None)
        college_index = next((i for i, cell in enumerate(header) if cell == "学院"), None)
        campus_index = next((i for i, cell in enumerate(header) if cell == "校区"), None)
        total_index = next((i for i, cell in enumerate(header) if cell == "合计"), None)
        for raw in table[header_index + 1 :]:
            major = clean_cell(raw, major_index)
            if not major or major in {"专业", "专业名称"}:
                continue
            hubei_plan = clean_cell(raw, hubei_index)
            if not as_int(hubei_plan):
                continue
            # Some tables keep a province total row immediately after the header.
            if major == "" or major.isdigit():
                continue
            rows.append(
                {
                    "学校名称": school_name,
                    "官方来源文件": str(path.relative_to(ROOT)),
                    "证据类型": "official_static_html_table",
                    "年份": "2026",
                    "省份": "湖北",
                    "科类": "",
                    "批次": "",
                    "类别": "",
                    "专业组": "",
                    "专业代号": "",
                    "专业代码": clean_cell(raw, code_index) if code_index is not None else "",
                    "专业名称": major,
                    "专业备注": "",
                    "计划数": str(as_int(hubei_plan)),
                    "学制": "",
                    "学费": clean_cell(raw, fee_index) if fee_index is not None else "",
                    "校区": clean_cell(raw, campus_index) if campus_index is not None else "",
                    "选科": clean_cell(raw, subject_index) if subject_index is not None else "",
                    "可核字段": "专业名称；湖北计划数；学费；校区；选科" if fee_index is not None else "专业名称；湖北计划数",
                    "局限性": "HTML大表未直接给出湖北院校专业组代码和组内调剂边界；需与第19期原页及湖北官方系统对齐。",
                    "年份证据说明": "来源页为高校招生官网留存页；若页面自身年份标记不完整，仍需以官网发布时间、湖北计划字段和省招办计划交叉确认。",
                }
            )
    return rows


def parse_json_plan(path, school_name):
    obj = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj, dict) and isinstance(obj.get("data"), dict) and isinstance(obj["data"].get("zsjhList"), list):
        return parse_zsjh_list_json(path, school_name, obj)
    if isinstance(obj, dict) and isinstance(obj.get("dataList"), list):
        return parse_tjfsu_json(path, school_name, obj)
    plan_rows = obj.get("list", [])
    rows = []
    for item in plan_rows:
        subject_parts = [item.get("sxkm", ""), item.get("xkkm", ""), item.get("xkyq", "")]
        subject = "；".join(part for part in subject_parts if str(part).strip())
        rows.append(
            {
                "学校名称": school_name,
                "官方来源文件": str(path.relative_to(ROOT)),
                "证据类型": "official_dynamic_api_json",
                "年份": str(item.get("nf", "")),
                "省份": str(item.get("sf", "")),
                "科类": str(item.get("klmc", "")),
                "批次": str(item.get("pcmc", "")),
                "类别": str(item.get("zslb", "")),
                "专业组": str(item.get("zygroup", "")),
                "专业代号": str(item.get("zydh", "")),
                "专业代码": str(item.get("zydm", "")),
                "专业名称": str(item.get("zymc", "")),
                "专业备注": str(item.get("zybz", "")),
                "计划数": str(item.get("jhrs", "")),
                "学制": str(item.get("xzmc", "")),
                "学费": str(item.get("zyxf", "")),
                "校区": str(item.get("xqlx", "")),
                "选科": subject,
                "可核字段": "专业名称；专业代码；专业代号；计划数；学制；学费；校区；选科；专业组",
                "局限性": "以高校招生系统字段为准；若未给出专业组或字段为空，专业组边界仍需回到第19期原页及湖北官方系统核验。",
                "年份证据说明": "官方招生系统API返回 nf=2026 且 sf=湖北。",
            }
        )
    return rows


def parse_zsjh_list_json(path, school_name, obj):
    rows = []
    for item in obj.get("data", {}).get("zsjhList", []):
        rows.append(
            {
                "学校名称": school_name,
                "官方来源文件": str(path.relative_to(ROOT)),
                "证据类型": "official_dynamic_ajax_json",
                "年份": str(item.get("nf", "")),
                "省份": str(item.get("ssmc", "")),
                "科类": str(item.get("klmc", "")),
                "批次": str(item.get("zycc", "")),
                "类别": str(item.get("zslx") or item.get("zylx", "")),
                "专业组": str(item.get("zyzname") or item.get("zyz") or item.get("kskmyqmc", "")),
                "专业代号": str(item.get("zydh", "")),
                "专业代码": str(item.get("zydm", "")),
                "专业名称": str(item.get("zymc") or item.get("zydhmc", "")),
                "专业备注": str(item.get("remarks") or item.get("bhzy") or item.get("zkfx", "")),
                "计划数": str(item.get("zsjhs", "")),
                "学制": str(item.get("xz") or item.get("zyxz", "")),
                "学费": str(item.get("xf") or item.get("zyxf", "")),
                "校区": str(item.get("jdxq") or item.get("campus", "")),
                "选科": str(item.get("xkkm") or item.get("kskmyqmc") or item.get("sxkmyqzw", "")),
                "可核字段": "专业名称；专业代码；专业代号；计划数；学制；学费；校区；选科；专业组名称",
                "局限性": "高校招生系统API未直接给出湖北院校专业组代码；专业组边界需同第19期原页和湖北官方系统对齐。",
                "年份证据说明": "官方招生系统API返回 nf=2026 且 ssmc=湖北。",
            }
        )
    return rows


def parse_tjfsu_json(path, school_name, obj):
    rows = []
    for item in obj.get("dataList", []):
        school = item.get("school") or {}
        rows.append(
            {
                "学校名称": school_name,
                "官方来源文件": str(path.relative_to(ROOT)),
                "证据类型": "official_dynamic_api_json",
                "年份": str(item.get("year", "")),
                "省份": str(item.get("enrollmentUnit", "")),
                "科类": str(item.get("kelei", "")),
                "批次": str(item.get("enrollOrder", "")),
                "类别": "",
                "专业组": "",
                "专业代号": "",
                "专业代码": "",
                "专业名称": str(item.get("specialty", "")),
                "专业备注": str(school.get("specialtyWithBrackets", "")),
                "计划数": str(item.get("amount", "")),
                "学制": "",
                "学费": "",
                "校区": "",
                "选科": "",
                "可核字段": "专业名称；计划数；年份；省份；批次；科类",
                "局限性": "官方系统返回字段较少，不含学费、学制、选科、校区、专业代号、院校专业组代码。",
                "年份证据说明": "官方招生系统API返回 year=2026 且 enrollmentUnit=湖北。",
            }
        )
    return rows


def parse_extracted_pdf_csv(path, school_name):
    rows = []
    for item in read_csv(path):
        source_note_parts = []
        if item.get("原始PDF"):
            source_note_parts.append(f"原始PDF：{item.get('原始PDF', '')}")
        if item.get("页码"):
            source_note_parts.append(f"页码：{item.get('页码', '')}")
        if item.get("PDF表格行号"):
            source_note_parts.append(f"PDF表格行号：{item.get('PDF表格行号', '')}")
        if item.get("专业代码OCR"):
            source_note_parts.append(f"专业代码OCR：{item.get('专业代码OCR', '')}")
        if item.get("湖北格bbox_px"):
            source_note_parts.append(f"湖北格bbox_px：{item.get('湖北格bbox_px', '')}")
        if item.get("系"):
            source_note_parts.append(f"系：{item.get('系', '')}")
        if item.get("总计划数"):
            source_note_parts.append(f"总计划数：{item.get('总计划数', '')}")
        if item.get("专业名称OCR") and item.get("专业名称OCR") != item.get("专业名称"):
            source_note_parts.append(f"专业名称OCR：{item.get('专业名称OCR', '')}")
        if item.get("专业名称校正说明"):
            source_note_parts.append(f"专业名校正：{item.get('专业名称校正说明', '')}")
        if item.get("原始图片"):
            source_note_parts.append("原始图片：官方计划图已本地留存")
        if item.get("官网入口页"):
            source_note_parts.append("官网入口页：已本地留存")
        if item.get("类别"):
            source_note_parts.append(f"类别：{item.get('类别', '')}")
        evidence_type = "official_pdf_table_extracted_csv" if item.get("原始PDF") else "official_image_table_extracted_csv"
        if evidence_type == "official_pdf_table_extracted_csv":
            verifiable_fields = "专业名称；湖北物理类计划数；学制；学费；校区；PDF页码"
            year_note = "高校官网2026年分省分专业招生计划PDF经表格抽取留存。"
            default_limitation = "由高校官网PDF抽取，未给湖北院校专业组代码和专业代号，需与第19期原页及湖北官方系统对齐。"
        else:
            verifiable_fields = "专业名称；湖北物理类计划数；学制；学费；官方计划图"
            year_note = "高校官网入口指向的官方计划图经人工转录并用OCR辅助检查后留存。"
            default_limitation = "由高校官网入口指向的官方计划图转录，未给湖北院校专业组代码和专业代号，需与第19期原页及湖北官方系统对齐。"
        rows.append(
            {
                "学校名称": school_name,
                "官方来源文件": str(path.relative_to(ROOT)),
                "证据类型": evidence_type,
                "年份": "2026",
                "省份": "湖北",
                "科类": "物理类" if item.get("科类") in {"物理", "理工类"} else item.get("科类", ""),
                "批次": "",
                "类别": "",
                "专业组": "",
                "专业代号": "",
                "专业代码": "",
                "专业名称": item.get("专业名称", ""),
                "专业备注": "；".join(source_note_parts),
                "计划数": item.get("湖北计划数", ""),
                "学制": item.get("学制", ""),
                "学费": item.get("学费", ""),
                "校区": item.get("校区", ""),
                "选科": "",
                "可核字段": verifiable_fields,
                "局限性": item.get(
                    "提取局限性",
                    default_limitation,
                ),
                "年份证据说明": year_note,
            }
        )
    return rows


def parse_unn_html(path, school_name):
    parser = TableParser()
    parser.feed(path.read_text(encoding="utf-8-sig", errors="ignore"))
    header = None
    rows = []
    for table in parser.tables:
        if not table:
            continue
        first = table[0]
        if "年份" in first and "招生专业" in first and "湖北" in first:
            header = first
            data_rows = table[1:]
        elif header and first and first[0] == "2026" and len(first) == len(header):
            data_rows = table
        else:
            continue
        index_by_name = {name: index for index, name in enumerate(header) if name}
        def cell(raw, name):
            index = index_by_name.get(name)
            return clean_cell(raw, index) if index is not None else ""

        for raw in data_rows:
            year = cell(raw, "年份")
            province_plan = as_int(cell(raw, "湖北"))
            subject = cell(raw, "选考科目")
            batch = cell(raw, "批次")
            major = cell(raw, "招生专业")
            if year != "2026" or batch != "普通本科批" or not subject.startswith("物理") or province_plan is None:
                continue
            rows.append(
                {
                    "学校名称": school_name,
                    "官方来源文件": str(path.relative_to(ROOT)),
                    "证据类型": "official_static_html_table",
                    "年份": year,
                    "省份": "湖北",
                    "科类": "物理类",
                    "批次": batch,
                    "类别": "",
                    "专业组": cell(raw, "专业组编号"),
                    "专业代号": "",
                    "专业代码": "",
                    "专业名称": major,
                    "专业备注": f"学院：{cell(raw, '学院')}；全省计划数：{cell(raw, '计划数')}",
                    "计划数": str(province_plan),
                    "学制": "",
                    "学费": cell(raw, "学费（元/生·学年）"),
                    "校区": "",
                    "选科": subject,
                    "可核字段": "专业名称；湖北计划数；学费；选科；批次；学院；页面专业组编号",
                    "局限性": "页面专业组编号不是湖北志愿系统院校专业组代码；未给专业代号和湖北专业组边界，需与第19期原页及湖北官方系统对齐。",
                    "年份证据说明": "南宁学院招生计划网静态表包含2026年、湖北列和普通本科批字段。",
                }
            )
    return rows


def html_table_rows(path):
    parser = TableParser()
    parser.feed(path.read_text(encoding="utf-8-sig", errors="ignore"))
    return parser.tables[0] if parser.tables else []


def normalize_wbu_plan_key(value):
    return normalize_major_name(str(value or "").replace("(", "（").replace(")", "）"))


def parse_wbu_undergraduate_info(path):
    rows = html_table_rows(path)
    info_by_major = {}
    for raw in rows[1:]:
        if not raw or raw[0] == "总计":
            continue
        if len(raw) == 7:
            major = clean_cell(raw, 1)
            subject = clean_cell(raw, 2)
            requirement = clean_cell(raw, 3)
            fee = clean_cell(raw, 4)
            total_plan = clean_cell(raw, 5)
            college = clean_cell(raw, 0)
        elif len(raw) == 6:
            major = clean_cell(raw, 0)
            subject = clean_cell(raw, 1)
            requirement = clean_cell(raw, 2)
            fee = clean_cell(raw, 3)
            total_plan = clean_cell(raw, 4)
            college = ""
        else:
            continue
        key = normalize_wbu_plan_key(major)
        if key:
            info_by_major[key] = {
                "学院": college,
                "科类": subject,
                "考试科目要求": requirement,
                "学费": fee,
                "总计划数": total_plan,
                "专业名称": major,
            }
    return info_by_major


def parse_wbu_plan():
    source_plan_path = SAMPLE_OFFICIAL_DIR / "wbu-2026-source-plan.html"
    undergraduate_path = SAMPLE_OFFICIAL_DIR / "wbu-2026-undergraduate-plan.html"
    if not source_plan_path.exists() or not undergraduate_path.exists():
        return []

    info_by_major = parse_wbu_undergraduate_info(undergraduate_path)
    rows = html_table_rows(source_plan_path)
    if not rows:
        return []

    header = rows[0]
    if "专业及招考方向" not in header or "湖北" not in header or "计划数" not in header:
        return []
    major_index = header.index("专业及招考方向")
    hubei_index = header.index("湖北")
    total_index = header.index("计划数")

    normalized = []
    for raw in rows[1:]:
        major = clean_cell(raw, major_index)
        if not major or major == "总计":
            continue
        hubei_plan = as_int(clean_cell(raw, hubei_index))
        if hubei_plan is None:
            continue

        info = info_by_major.get(normalize_wbu_plan_key(major), {})
        subject = info.get("科类", "")
        is_physics_only = subject == "物理"
        comparable_plan = str(hubei_plan) if is_physics_only else ""
        if is_physics_only:
            verifiable_fields = "专业名称；湖北物理类计划数候选；学费；科类；选科；全校总计划数"
            limitation = "官网分省表湖北列与本科计划表科类均支持物理类逐专业计划候选；仍未给湖北院校专业组代码和专业代号，需与第19期原页及湖北官方系统对齐。"
        else:
            verifiable_fields = "专业名称；湖北总计划线索；学费；科类；选科；全校总计划数"
            limitation = "官网分省表湖北列未拆首选物理/历史，不能直接作为物理类计划数；本行只用于核专业名、学费、科类和选科线索；仍未给湖北院校专业组代码和专业代号，需与第19期原页及湖北官方系统对齐。"

        notes = [f"湖北来源计划={hubei_plan}", f"全校计划={clean_cell(raw, total_index)}"]
        for label, value in [("学院", info.get("学院", "")), ("本科计划表科类", subject)]:
            if value:
                notes.append(f"{label}={value}")

        normalized.append(
            {
                "学校名称": "武汉商学院",
                "官方来源文件": "；".join(
                    [
                        str(source_plan_path.relative_to(ROOT)),
                        str(undergraduate_path.relative_to(ROOT)),
                    ]
                ),
                "证据类型": "official_static_html_joined_tables",
                "年份": "2026",
                "省份": "湖北",
                "科类": "物理类" if is_physics_only else subject,
                "批次": "",
                "类别": "",
                "专业组": "",
                "专业代号": "",
                "专业代码": "",
                "专业名称": info.get("专业名称", major),
                "专业备注": "；".join(notes),
                "计划数": comparable_plan,
                "学制": "",
                "学费": info.get("学费", ""),
                "校区": "",
                "选科": info.get("考试科目要求", ""),
                "可核字段": verifiable_fields,
                "局限性": limitation,
                "年份证据说明": "武汉商学院招生网2026年分省分专业来源计划表和本科专业招生计划一览表联合留存。",
            }
        )
    return normalized


def xlsx_shared_strings(zf):
    path = "xl/sharedStrings.xml"
    if path not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(path))
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = []
    for si in root.findall("x:si", ns):
        parts = [node.text or "" for node in si.findall(".//x:t", ns)]
        strings.append("".join(parts))
    return strings


def xlsx_cell_value(cell, shared_strings):
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    value = cell.find("x:v", ns)
    if value is None:
        inline = cell.find("x:is", ns)
        if inline is not None:
            parts = [node.text or "" for node in inline.findall(".//x:t", ns)]
            return "".join(parts)
        return ""
    text = value.text or ""
    if cell.get("t") == "s":
        index = int(text)
        return shared_strings[index] if index < len(shared_strings) else ""
    return text


def xlsx_column_index(cell_ref):
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    result = 0
    for char in letters:
        result = result * 26 + ord(char) - ord("A") + 1
    return result - 1


def read_xlsx_rows(path):
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        shared_strings = xlsx_shared_strings(zf)
        sheet_name = "xl/worksheets/sheet1.xml"
        root = ET.fromstring(zf.read(sheet_name))
        rows = []
        for row in root.findall(".//x:sheetData/x:row", ns):
            values = []
            for cell in row.findall("x:c", ns):
                index = xlsx_column_index(cell.get("r", "A1"))
                while len(values) <= index:
                    values.append("")
                values[index] = xlsx_cell_value(cell, shared_strings)
            rows.append([" ".join(str(value).split()) for value in values])
    return rows


def parse_xlsx_plan(path, school_name):
    rows = read_xlsx_rows(path)
    normalized = []
    rowwise_header_index = None
    for index, row in enumerate(rows[:10]):
        if "生源省市" in row and "招生专业（类）" in row and "招生计划数" in row:
            rowwise_header_index = index
            break
    if rowwise_header_index is not None:
        return parse_rowwise_xlsx_plan(path, school_name, rows, rowwise_header_index)

    header_index = None
    for index, row in enumerate(rows[:10]):
        if "专业名称" in row and "湖北" in row:
            header_index = index
            break
    if header_index is None:
        return normalized
    header = rows[header_index]
    major_index = header.index("专业名称")
    hubei_index = header.index("湖北")
    college_index = header.index("学院") if "学院" in header else None
    for raw in rows[header_index + 1 :]:
        major = clean_cell(raw, major_index)
        plan = as_int(clean_cell(raw, hubei_index))
        if not major or major in {"总计", "专业名称"} or plan is None:
            continue
        normalized.append(
            {
                "学校名称": school_name,
                "官方来源文件": str(path.relative_to(ROOT)),
                "证据类型": "official_attachment_xlsx_province_table",
                "年份": "2026",
                "省份": "湖北",
                "科类": "",
                "批次": "",
                "类别": "",
                "专业组": "",
                "专业代号": "",
                "专业代码": "",
                "专业名称": major,
                "专业备注": clean_cell(raw, college_index) if college_index is not None else "",
                "计划数": str(plan),
                "学制": "",
                "学费": "",
                "校区": "",
                "选科": "",
                "可核字段": "专业名称；湖北计划数；学院",
                "局限性": "附件按省份列计划，未拆湖北物理/历史/艺术类别，未给学费、学制、选科、校区、专业代号、院校专业组边界。",
                "年份证据说明": "官网页面标题和附件文件名均为2026年普通本科招生专业与计划。",
            }
        )
    return normalized


def parse_rowwise_xlsx_plan(path, school_name, rows, header_index):
    header = rows[header_index]
    index_by_name = {name: index for index, name in enumerate(header) if name}

    def get(raw, name):
        index = index_by_name.get(name)
        return clean_cell(raw, index) if index is not None else ""

    normalized = []
    for raw in rows[header_index + 1 :]:
        province = get(raw, "生源省市")
        subject = get(raw, "科类")
        major = get(raw, "招生专业（类）")
        plan = as_int(get(raw, "招生计划数"))
        if province != "湖北" or subject != "物理类" or not major or plan is None:
            continue

        direction = get(raw, "招考方向")
        included = get(raw, "类内所含专业")
        remarks = []
        if direction:
            remarks.append(f"招考方向：{direction}")
        if included:
            remarks.append(f"类内所含专业：{included}")
        category_parts = []
        for name in ["计划类别", "招考类型", "计划性质"]:
            value = get(raw, name)
            if value and value not in category_parts:
                category_parts.append(value)

        normalized.append(
            {
                "学校名称": school_name,
                "官方来源文件": str(path.relative_to(ROOT)),
                "证据类型": "official_attachment_xlsx_row_plan",
                "年份": "2026",
                "省份": province,
                "科类": subject,
                "批次": get(raw, "批次"),
                "类别": "；".join(category_parts),
                "专业组": "",
                "专业代号": "",
                "专业代码": "",
                "专业名称": major,
                "专业备注": "；".join(remarks),
                "计划数": str(plan),
                "学制": get(raw, "学制"),
                "学费": "",
                "校区": get(raw, "就学地点"),
                "选科": get(raw, "选考科目要求"),
                "可核字段": "专业名称；科类；批次；选考科目；湖北物理类计划数；学制；就学地点",
                "局限性": "官网XLSX按逐专业计划列出湖北物理类字段，但未给湖北院校专业组代码、专业代号和组内调剂边界。",
                "年份证据说明": "官网页面标题为2026年湖北招生计划，附件逐行给出湖北物理类本科普通批计划。",
            }
        )
    return normalized


def build_normalized_rows():
    rows = []
    for school_name, files in SOURCE_FILES_BY_SCHOOL.items():
        for filename in files:
            path = EXTERNAL_DIR / filename
            if not path.exists():
                continue
            if path.suffix == ".json":
                rows.extend(parse_json_plan(path, school_name))
            elif path.suffix == ".csv":
                rows.extend(parse_extracted_pdf_csv(path, school_name))
            elif path.suffix == ".xlsx":
                rows.extend(parse_xlsx_plan(path, school_name))
            elif path.suffix in {".html", ".htm"}:
                if school_name == "南宁学院":
                    rows.extend(parse_unn_html(path, school_name))
                else:
                    rows.extend(parse_table_html(path, school_name))
    rows.extend(parse_wbu_plan())
    return rows


def best_match(detail, official_rows_by_school):
    school_rows = official_rows_by_school.get(detail["院校名称OCR"], [])
    if not school_rows:
        return None, "no_retained_official_plan_for_school", 0
    if has_next_school_noise(detail.get("专业名称及备注OCR", "")):
        return None, "unmatched_embedded_other_school_marker", 0
    target = normalize_major_name(detail["专业名称及备注OCR"])
    if not target:
        return None, "ocr_major_name_empty", 0
    best = None
    best_score = 0
    best_method = "unmatched"
    blocked_best_score = 0
    for official in school_rows:
        official_name = normalize_major_name(official["专业名称"])
        if not official_name:
            continue
        if missing_key_qualifiers(target, official_name):
            if official_name in target:
                blocked_best_score = max(blocked_best_score, 55)
            continue
        if official_name == target:
            score, method = 100, "exact_after_normalization"
        elif target in official_name:
            score, method = 92, "ocr_prefix_of_official_name"
        elif official_name in target:
            score, method = 85, "contains_after_normalization"
        elif len(official_name) >= 4 and official_name[:4] in target:
            score, method = 65, "prefix_possible_match"
        elif len(target) >= 4 and target[:4] in official_name:
            score, method = 65, "prefix_possible_match"
        else:
            fuzzy_score = similarity_score(target, official_name)
            if fuzzy_score >= 80:
                score, method = fuzzy_score, "fuzzy_ocr_similarity_match"
            elif fuzzy_score >= 60:
                score, method = fuzzy_score, "fuzzy_ocr_similarity_possible_match"
            else:
                score, method = 0, "unmatched"
        if score > best_score or (score == best_score and best and len(official_name) > len(normalize_major_name(best["专业名称"]))):
            best = official
            best_score = score
            best_method = method
    if best_score >= 80:
        return best, best_method, best_score
    if best_score >= 60:
        return best, "possible_" + best_method, best_score
    if blocked_best_score:
        return None, "unmatched_missing_key_qualifier", blocked_best_score
    return None, "unmatched", best_score


def plan_status(detail, official):
    if not official:
        return "not_covered"
    ocr_plan = as_int(detail.get("专业计划数OCR候选"))
    official_plan = as_int(official.get("计划数"))
    if official_plan is None:
        return "official_plan_missing"
    if ocr_plan is None:
        return "ocr_plan_missing_official_available"
    if ocr_plan == official_plan:
        return "match"
    return "mismatch"


def coverage_conclusion(match_status, plan_check):
    if match_status == "matched" and plan_check == "match":
        return "官网已覆盖专业名称和计划数，仍需核专业组边界、PDF原页和湖北官方系统"
    if match_status == "matched" and plan_check == "ocr_plan_missing_official_available":
        return "官网可补计划数OCR缺口，需回看PDF原页确认OCR漏识"
    if match_status == "matched":
        return "官网已覆盖专业名称，计划数字段仍需人工复核"
    if match_status == "possible_match":
        return "官网存在疑似专业名匹配，需人工确认OCR或专业名称差异"
    if match_status == "no_school_source":
        return "该校尚无可匹配的结构化官网计划证据"
    return "官网留存证据未匹配到该专业"


def remaining_requirements(match_status, plan_check, source_status):
    needs = ["PDF原页", "湖北官方系统"]
    if source_status != "has_reusable_2026_hubei_plan_source":
        needs.append("高校官网/章程补强")
    if match_status != "matched":
        needs.append("专业名人工复核")
    if plan_check != "match":
        needs.append("计划数人工复核")
    needs.extend(["专业组边界", "调剂范围", "家庭接受度"])
    return "；".join(dict.fromkeys(needs))


def build_match_rows(normalized_rows, detail_rows):
    by_school = defaultdict(list)
    for row in normalized_rows:
        by_school[row["学校名称"]].append(row)

    match_rows = []
    for detail in detail_rows:
        best, method, score = best_match(detail, by_school)
        if best is None and method == "no_retained_official_plan_for_school":
            match_status = "no_school_source"
        elif best is None:
            match_status = "unmatched"
        elif method.startswith("possible_"):
            match_status = "possible_match"
        else:
            match_status = "matched"
        plan_check = plan_status(detail, best)
        source_status = (
            "has_reusable_2026_hubei_plan_source"
            if best
            else detail["官网来源状态"]
        )
        match_rows.append(
            {
                "招生明细主表行ID": detail["招生明细主表行ID"],
                "主表粒度": detail["主表粒度"],
                "是否真实招生明细": detail["是否真实招生明细"],
                "是否0明细占位": detail["是否0明细占位"],
                "来源页码": detail["来源页码"],
                "复核批次": detail["复核批次"],
                "入口类型": detail["入口类型"],
                "院校代码": detail["院校代码"],
                "院校名称OCR": detail["院校名称OCR"],
                "2026院校专业组代码": detail["2026院校专业组代码"],
                "专业组内专业序号": detail["专业组内专业序号"],
                "专业代号OCR": detail["专业代号OCR"],
                "专业名称及备注OCR": detail["专业名称及备注OCR"],
                "再选科目OCR候选": detail["再选科目OCR候选"],
                "专业计划数OCR候选": detail["专业计划数OCR候选"],
                "学费OCR候选": detail["学费OCR候选"],
                "专业偏好方向": detail["专业偏好方向"],
                "专业风险类型": detail["专业风险类型"],
                "机器专业接受度初判": detail["机器专业接受度初判"],
                "调剂影响初判": detail["调剂影响初判"],
                "官网来源状态": source_status,
                "官网证据匹配状态": match_status,
                "官网证据覆盖结论": coverage_conclusion(match_status, plan_check),
                "最佳官网来源文件": best["官方来源文件"] if best else "",
                "最佳官网专业名称": best["专业名称"] if best else "",
                "最佳官网计划数": best["计划数"] if best else "",
                "最佳官网专业组": best["专业组"] if best else "",
                "最佳官网专业代号": best["专业代号"] if best else "",
                "最佳官网学费": best["学费"] if best else "",
                "最佳官网选科": best["选科"] if best else "",
                "专业名称匹配方式": method,
                "专业名称匹配分": str(score),
                "计划数核验状态": plan_check,
                "仍需核验": remaining_requirements(match_status, plan_check, source_status),
            }
        )
    return match_rows


def fidelity_status(row):
    if row.get("是否0明细占位") == "true":
        return "占位行-不是真实招生明细"
    match_status = row.get("官网证据匹配状态")
    plan_check = row.get("计划数核验状态")
    if match_status == "no_school_source":
        source_status = row.get("官网来源状态")
        if source_status == "needs_official_plan_source_search":
            return "待补高校官网计划源"
        if source_status == "charter_or_rules_only_no_plan":
            return "仅章程规则线索-无结构化计划证据"
        return "有官网线索但未结构化匹配"
    if match_status == "matched" and plan_check == "match":
        return "官网专业名和计划数一致-仍待湖北官方系统和PDF原页复核"
    if match_status == "matched" and plan_check == "mismatch":
        return "官网专业名匹配但计划数冲突-优先核页"
    if match_status == "matched" and plan_check == "ocr_plan_missing_official_available":
        return "官网可补OCR计划数-优先核页"
    if match_status == "possible_match":
        return "疑似匹配-人工确认"
    if match_status == "unmatched":
        return "官网未匹配-专业名或OCR待核"
    return "待人工复核"


def build_detail_ledger_rows(detail_rows, match_rows):
    matches_by_id = {row["招生明细主表行ID"]: row for row in match_rows}
    ledger_rows = []
    for detail in detail_rows:
        match = matches_by_id.get(detail["招生明细主表行ID"], {})
        merged = {}
        for field in DETAIL_LEDGER_FIELDS:
            if field == "保真处理状态":
                merged[field] = fidelity_status({**detail, **match})
            elif field == "保真说明":
                merged[field] = (
                    "本表一行对应一个招生专业或0明细占位；学校和专业组只作索引。"
                    "全部行仍保持不可进入最终表，必须继续核PDF原页、湖北官方系统、"
                    "高校官网/章程、调剂范围和家庭接受度。"
                )
            else:
                merged[field] = match.get(field, detail.get(field, ""))
        ledger_rows.append(merged)
    return ledger_rows


def main():
    normalized_rows = build_normalized_rows()
    detail_rows = read_csv(ADMISSION_DETAIL)
    match_rows = build_match_rows(normalized_rows, detail_rows)
    detail_ledger_rows = build_detail_ledger_rows(detail_rows, match_rows)
    write_csv(NORMALIZED_OUTPUT, normalized_rows, NORMALIZED_FIELDS)
    write_csv(MATCH_OUTPUT, match_rows, MATCH_FIELDS)
    write_csv(DETAIL_LEDGER_OUTPUT, detail_ledger_rows, DETAIL_LEDGER_FIELDS)

    summary = {
        "status": "official_evidence_match_not_final",
        "generated_by": "scripts/build_issue19_b0_b1_official_evidence_match.py",
        "normalized_official_row_count": len(normalized_rows),
        "admission_detail_row_count": len(match_rows),
        "admission_detail_evidence_ledger_row_count": len(detail_ledger_rows),
        "default_discussion_table": str(DETAIL_LEDGER_OUTPUT.relative_to(ROOT)),
        "retained_official_schools": sorted({row["学校名称"] for row in normalized_rows}),
        "evidence_type_counts": dict(Counter(row["证据类型"] for row in normalized_rows)),
        "match_status_counts": dict(Counter(row["官网证据匹配状态"] for row in match_rows)),
        "plan_check_status_counts": dict(Counter(row["计划数核验状态"] for row in match_rows)),
        "fidelity_status_counts": dict(Counter(row["保真处理状态"] for row in detail_ledger_rows)),
        "matched_school_counts": dict(Counter(row["院校名称OCR"] for row in match_rows if row["官网证据匹配状态"] == "matched")),
        "notes": [
            "本结果只是高校官网/API对第19期OCR底座的交叉校验证据，不是最终志愿方案。",
            "默认讨论表是一行一个招生明细的合并表；学校和专业组表只作为索引、调剂和补源辅助。",
            "计划数只有在OCR数字和官网数字一致时才记为match；OCR空缺但官网有数时只用于补缺提示。",
            "专业名称含面向武汉、实验班、英才班、中外合作等关键限定词时，不用泛化专业名的官网计划数替代。",
            "所有可用结论仍必须回到PDF原页、湖北官方系统、招生章程、专业组边界、调剂范围和家庭接受度。",
        ],
        "outputs": [
            str(NORMALIZED_OUTPUT.relative_to(ROOT)),
            str(MATCH_OUTPUT.relative_to(ROOT)),
            str(DETAIL_LEDGER_OUTPUT.relative_to(ROOT)),
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出官网/API标准化证据：{NORMALIZED_OUTPUT}")
    print(f"写出逐专业官网证据匹配：{MATCH_OUTPUT}")
    print(f"写出逐专业招生明细证据合并表：{DETAIL_LEDGER_OUTPUT}")
    print(f"写出摘要：{SUMMARY_OUTPUT}")
    print(f"官网/API标准化行数：{len(normalized_rows)}")
    print(f"逐专业匹配行数：{len(match_rows)}")
    print(f"逐专业招生明细证据合并行数：{len(detail_ledger_rows)}")


if __name__ == "__main__":
    main()
